from __future__ import annotations

import json
from pathlib import Path

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from completion.models import CompletionSourceKind
import provider_backends.kimi.hindsight as kimi_hindsight
from provider_backends.kimi.execution import KimiProviderAdapter
from provider_backends.kimi.hindsight import HindsightRecall, HindsightRetain
from provider_backends.kimi.native_log import KimiTurnObservation
from provider_execution.base import ProviderSubmission


class _Backend:
    def __init__(self, text: str = "") -> None:
        self._text = text
        self.sent: list[str] = []

    def get_pane_content(self, pane_id: str, *, lines: int) -> str:
        del pane_id, lines
        return self._text

    def send_text(self, pane_id: str, text: str) -> None:
        del pane_id
        self.sent.append(text)

    def send_keys(self, pane_id: str, *keys: str) -> None:
        del pane_id
        self.sent.extend(keys)


def _job(*, body: str = "do work", job_id: str = "job_native123", workspace_path: Path) -> JobRecord:
    return JobRecord(
        job_id=job_id,
        submission_id=None,
        agent_name="kimi1",
        provider="kimi",
        request=MessageEnvelope(
            project_id="proj",
            to_agent="kimi1",
            from_actor="user",
            body=body,
            task_id=None,
            reply_to=None,
            message_type="ask",
            delivery_scope=DeliveryScope.SINGLE,
        ),
        status=JobStatus.RUNNING,
        terminal_decision=None,
        cancel_requested_at=None,
        workspace_path=str(workspace_path),
        created_at="2026-06-13T00:00:00Z",
        updated_at="2026-06-13T00:00:00Z",
    )


def _submission(work_dir: Path, *, extra_state: dict[str, object] | None = None) -> ProviderSubmission:
    return ProviderSubmission(
        job_id="job_native123",
        agent_name="kimi1",
        provider="kimi",
        accepted_at="2026-06-13T00:00:00Z",
        ready_at="2026-06-13T00:00:00Z",
        source_kind=CompletionSourceKind.SESSION_EVENT_LOG,
        reply="",
        runtime_state={
            "mode": "native_turn_log",
            "backend": _Backend(),
            "pane_id": "%9",
            "req_id": "job_native123",
            "request_anchor": "job_native123",
            "work_dir": str(work_dir),
            "started_at": "2026-06-13T00:00:00Z",
            "last_poll_at": "2026-06-13T00:00:00Z",
            "prompt_sent": True,
            "next_seq": 1,
            "anchor_emitted": False,
            "reply_buffer": "",
            "last_reply_signature": "",
            "turn_boundary_ref": "",
            "session_path": "",
            **(extra_state or {}),
        },
    )


def test_kimi_start_injects_hindsight_recall_into_prompt(monkeypatch, tmp_path: Path) -> None:
    work_dir = tmp_path / "project"
    work_dir.mkdir()
    backend = _Backend("ready")
    session = type(
        "Session",
        (),
        {
            "session_id": "session-1",
            "pane_id": "%9",
            "data": {},
            "backend": lambda self: backend,
        },
    )()
    monkeypatch.setattr("provider_backends.kimi.execution.load_project_session", lambda *args, **kwargs: session)
    monkeypatch.setattr("provider_backends.kimi.execution._pane_ready_for_input", lambda content: True)
    monkeypatch.setattr(
        "provider_backends.kimi.execution.recall_hindsight_memories",
        lambda *args, **kwargs: HindsightRecall(
            context="<hindsight_memories>\n- remembered preference\n</hindsight_memories>",
            diagnostics={"status": "ok", "result_count": 1},
        ),
    )

    submission = KimiProviderAdapter().start(
        _job(body="please implement", workspace_path=work_dir),
        context=None,
        now="2026-06-13T00:00:00Z",
    )

    sent = "".join(backend.sent)
    assert submission.runtime_state["prompt_sent"] is True
    assert "remembered preference" in sent
    assert "please implement" in sent
    assert submission.diagnostics["hindsight_recall"]["status"] == "ok"
    assert submission.runtime_state["hindsight_user_prompt"] == "please implement"


def test_kimi_poll_retains_completed_turn_once(monkeypatch, tmp_path: Path) -> None:
    work_dir = tmp_path / "project"
    work_dir.mkdir()
    calls: list[dict[str, str]] = []

    def retain_stub(**kwargs) -> HindsightRetain:
        calls.append({key: str(value) for key, value in kwargs.items()})
        return HindsightRetain(retained=True, diagnostics={"status": "ok"})

    observation = KimiTurnObservation(
        request_seen=True,
        completed=True,
        reply="KIMI_RETAIN_OK",
        session_id="session-1",
        session_path="session-path",
        provider_turn_ref="turn-1",
        line_count=4,
        native_started_at=None,
        native_completed_at="2026-06-13T00:00:10Z",
    )
    monkeypatch.setattr("provider_backends.kimi.execution.observe_kimi_turn", lambda *args, **kwargs: observation)
    monkeypatch.setattr("provider_backends.kimi.execution._observe_kimi_pane_turn", lambda *args, **kwargs: None)
    monkeypatch.setattr("provider_backends.kimi.execution.retain_hindsight_turn", retain_stub)

    stable = KimiProviderAdapter().poll(
        _submission(work_dir, extra_state={"hindsight_user_prompt": "remember this task"}),
        now="2026-06-13T00:00:16Z",
    )

    assert stable is not None
    assert len(calls) == 1
    assert calls[0]["prompt"] == "remember this task"
    assert calls[0]["reply"] == "KIMI_RETAIN_OK"
    assert stable.submission.runtime_state["hindsight_retained"] is True
    assert stable.submission.runtime_state["hindsight_retain"]["status"] == "ok"

    KimiProviderAdapter().poll(stable.submission, now="2026-06-13T00:00:17Z")
    assert len(calls) == 1


def test_kimi_reuses_codex_hindsight_config_without_codex_retain_context(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    config_dir = home / ".hindsight"
    config_dir.mkdir(parents=True)
    (config_dir / "codex.json").write_text(
        json.dumps(
            {
                "hindsightApiUrl": "http://127.0.0.1:18888",
                "bankId": "local-ai-memory",
                "retainContext": "codex",
                "autoRetain": True,
            }
        ),
        encoding="utf-8",
    )
    requests: list[dict[str, object]] = []

    def request_stub(method: str, path: str, payload: object, **kwargs) -> object:
        requests.append({"method": method, "path": path, "payload": payload, **kwargs})
        return {}

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(kimi_hindsight, "_request", request_stub)

    retained = kimi_hindsight.retain_hindsight_turn(
        prompt="remember this",
        reply="done",
        session_id="session-1",
        job_id="job-1",
        agent_name="kimi1",
        workspace_path="/repo",
    )

    payload = requests[0]["payload"]
    assert retained.retained is True
    assert isinstance(payload, dict)
    assert payload["items"][0]["context"] == "kimi"


def test_kimi_can_render_visible_hindsight_hook_context(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    config_dir = home / ".hindsight"
    config_dir.mkdir(parents=True)
    (config_dir / "kimi.json").write_text(
        json.dumps(
            {
                "hindsightApiUrl": "http://127.0.0.1:18888",
                "bankId": "local-ai-memory",
                "showHookContext": True,
            }
        ),
        encoding="utf-8",
    )

    def request_stub(method: str, path: str, payload: object, **kwargs) -> object:
        del method, path, payload, kwargs
        return {"results": [{"content": "visible memory"}]}

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(kimi_hindsight, "_request", request_stub)

    recall = kimi_hindsight.recall_hindsight_memories(
        "please use memory",
        session_id="session-1",
        agent_name="kimi1",
        workspace_path="/repo",
    )

    assert "UserPromptSubmit hook (completed)" in recall.context
    assert "hook context:   <hindsight_memories>" in recall.context
    assert "visible memory" in recall.context
    assert recall.diagnostics["show_hook_context"] is True


def test_kimi_hindsight_accepts_api_key_or_token_env(monkeypatch, tmp_path: Path) -> None:
    home = tmp_path / "home"
    config_dir = home / ".hindsight"
    config_dir.mkdir(parents=True)
    (config_dir / "kimi.json").write_text(
        json.dumps(
            {
                "hindsightApiUrl": "http://127.0.0.1:18888",
                "bankId": "local-ai-memory",
            }
        ),
        encoding="utf-8",
    )
    seen_tokens: list[str] = []

    def request_stub(method: str, path: str, payload: object, **kwargs) -> object:
        del method, path, payload
        config = kwargs["config"]
        seen_tokens.append(config.api_token)
        return {"results": [{"content": "token memory"}]}

    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HINDSIGHT_API_KEY", "key-token")
    monkeypatch.setattr(kimi_hindsight, "_request", request_stub)

    recall = kimi_hindsight.recall_hindsight_memories(
        "please use memory",
        session_id="session-1",
        agent_name="kimi1",
        workspace_path="/repo",
    )

    assert "token memory" in recall.context
    assert seen_tokens == ["key-token"]
