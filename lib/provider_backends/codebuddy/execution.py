from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from ccbd.api_models import JobRecord
from completion.models import (
    CompletionConfidence, CompletionDecision, CompletionItemKind,
    CompletionSourceKind, CompletionStatus,
)
from provider_core.protocol import is_done_text, request_anchor_for_job
from provider_execution.active import ensure_active_pane_alive, prepare_active_start
from provider_execution.base import ProviderPollResult, ProviderRuntimeContext, ProviderSubmission
from provider_execution.common import (
    build_item, error_submission, interrupt_and_clear_runtime_target,
    no_wrap_requested, send_prompt_to_runtime_target,
)
from provider_backends.native_cli_support.prompt import clean_native_reply
from terminal_runtime import get_backend_for_session

from .native_log import CodebuddyNativeLogReader
from .hooks import read_native_binding
from .protocol_runtime import wrap_codebuddy_prompt
from .session import load_project_session


_MODE = "codebuddy_native_log"


class CodebuddyProviderAdapter:
    provider = "codebuddy"

    def restore_diagnostics(self) -> dict[str, object]:
        return {
            "resume_supported": False,
            "restore_mode": "resubmit_required",
            "restore_reason": "provider_resume_unsupported",
            "restore_detail": "CodeBuddy conversations can resume; interrupted CCB jobs must be resubmitted",
        }

    def start(self, job: JobRecord, *, context: ProviderRuntimeContext | None, now: str) -> ProviderSubmission:
        # Native message status=completed also appears on pre-tool commentary.
        # Without the request/done protocol there is no authoritative turn end.
        if no_wrap_requested(getattr(job, "provider_options", None)):
            return error_submission(
                job, provider=self.provider, now=now,
                source_kind=CompletionSourceKind.SESSION_EVENT_LOG,
                reason="codebuddy_no_wrap_unsupported",
                error="CodeBuddy requires request/done markers for exact turn completion",
            )
        prepared = prepare_active_start(
            job, context=context, provider=self.provider,
            source_kind=CompletionSourceKind.SESSION_EVENT_LOG, now=now,
            missing_session_reason="missing_codebuddy_session",
            load_session_fn=_load_session, backend_for_session_fn=get_backend_for_session,
        )
        if isinstance(prepared, ProviderSubmission):
            return prepared
        path = str(prepared.session.data.get("codebuddy_session_path") or "").strip()
        launch_id = str(prepared.session.data.get("codebuddy_launch_id") or "")
        if launch_id:
            binding = read_native_binding(
                Path(str(prepared.session.data.get("state_dir") or "")),
                launch_id=launch_id, work_dir=prepared.work_dir,
                config_dir=Path(str(prepared.session.data.get("codebuddy_config_dir") or "")),
            )
            if binding is None:
                return error_submission(
                    job, provider=self.provider, now=now,
                    source_kind=CompletionSourceKind.SESSION_EVENT_LOG,
                    reason="runtime_unavailable", error="codebuddy_native_binding_missing",
                )
            path = binding["session_path"]
        if not path:
            return error_submission(
                job, provider=self.provider, now=now,
                source_kind=CompletionSourceKind.SESSION_EVENT_LOG,
                reason="runtime_unavailable", error="codebuddy_session_path_missing",
            )
        reader = CodebuddyNativeLogReader(work_dir=prepared.work_dir, session_path=Path(path))
        anchor = request_anchor_for_job(job.job_id)
        try:
            state = reader.capture_state()
            send_prompt_to_runtime_target(
                prepared.backend, prepared.pane_id, wrap_codebuddy_prompt(job.request.body, anchor),
            )
        except Exception as exc:
            return error_submission(
                job, provider=self.provider, now=now,
                source_kind=CompletionSourceKind.SESSION_EVENT_LOG,
                reason="codebuddy_send_failed", error=f"{type(exc).__name__}: {exc}",
            )
        return ProviderSubmission(
            job_id=job.job_id, agent_name=job.agent_name, provider=self.provider,
            accepted_at=now, ready_at=now,
            source_kind=CompletionSourceKind.SESSION_EVENT_LOG, reply="",
            diagnostics={"provider": self.provider, "mode": _MODE, "session_path": path},
            runtime_state={
                "mode": _MODE, "reader": reader, "state": state,
                "backend": prepared.backend, "pane_id": prepared.pane_id,
                "request_anchor": anchor, "anchor_seen": False,
                "session_path": path, "next_seq": 1, "reply_buffer": "",
                "started_at": now, "run_timeout_s": _timeout(),
            },
        )

    def poll(self, submission: ProviderSubmission, *, now: str) -> ProviderPollResult | None:
        if submission.runtime_state.get("mode") != _MODE:
            return None
        state = dict(submission.runtime_state)
        backend, pane_id = state.get("backend"), str(state.get("pane_id") or "")
        if backend is None or not pane_id or state.get("reader") is None:
            return _terminal(submission, state, now, CompletionStatus.FAILED, "codebuddy_runtime_state_invalid")
        dead = ensure_active_pane_alive(submission, backend=backend, pane_id=pane_id, now=now)
        if dead is not None:
            return dead
        try:
            events, cursor = state["reader"].try_get_events(dict(state.get("state") or {}))
        except (OSError, ValueError) as exc:
            return _terminal(
                submission, state, now, CompletionStatus.FAILED,
                f"codebuddy_log_read_failed:{type(exc).__name__}",
            )
        state["state"] = cursor
        items = []
        if cursor.get("reset_reason"):
            # Replaying an older prefix after replacement/truncation must not
            # manufacture a fresh user anchor and a successful old answer.
            return _terminal(submission, state, now, CompletionStatus.INCOMPLETE, "codebuddy_log_reset")
        anchor = str(state.get("request_anchor") or "")
        for role, text in events:
            if role == "user":
                matches = text.splitlines()[0].rstrip(" \t") == f"CCB_REQ_ID: {anchor}" if text else False
                if matches:
                    if not state["anchor_seen"]:
                        items.append(_item(submission, state, now, CompletionItemKind.ANCHOR_SEEN, {"text": text}))
                    state["anchor_seen"] = True
                elif state["anchor_seen"]:
                    return _terminal(submission, state, now, CompletionStatus.INCOMPLETE, "codebuddy_turn_interrupted", items)
                continue
            if not state["anchor_seen"]:
                continue
            if role == "error":
                return _terminal(submission, state, now, CompletionStatus.FAILED, f"codebuddy_native_error:{text}", items)
            if role != "assistant":
                continue
            # Only native completed assistant output reaches this branch. User,
            # reasoning, terminal echo and tool output never own completion.
            done = is_done_text(text, anchor)
            reply = clean_native_reply(text, anchor)
            if done:
                state["reply_buffer"] = reply
                items.append(_item(submission, state, now, CompletionItemKind.ASSISTANT_FINAL, {"text": reply, "final_answer": reply}))
                items.append(_item(submission, state, now, CompletionItemKind.TURN_BOUNDARY, {"finish_reason": "ccb_done", "turn_id": anchor}))
                return _terminal(submission, state, now, CompletionStatus.COMPLETED, "codebuddy_done_marker", items)
            # Retain progress for incomplete/error diagnostics, not as a final.
            if reply:
                state["reply_buffer"] = reply
                items.append(_item(submission, state, now, CompletionItemKind.ASSISTANT_CHUNK, {"text": reply}))
        if _elapsed(str(state.get("started_at") or ""), now) >= float(state["run_timeout_s"]):
            return _terminal(submission, state, now, CompletionStatus.INCOMPLETE, "codebuddy_run_timeout", items)
        updated = replace(submission, reply=str(state.get("reply_buffer") or ""), runtime_state=state)
        if items or state != submission.runtime_state:
            return ProviderPollResult(submission=updated, items=tuple(items))
        return None

    def cancel(self, submission: ProviderSubmission) -> None:
        backend = submission.runtime_state.get("backend")
        pane_id = str(submission.runtime_state.get("pane_id") or "")
        if backend is not None and pane_id:
            interrupt_and_clear_runtime_target(backend, pane_id)


def _load_session(work_dir: Path, *, agent_name: str):
    return load_project_session(work_dir, instance=agent_name or None)


def _item(submission, state, now, kind, payload):
    seq = int(state.get("next_seq") or 1)
    state["next_seq"] = seq + 1
    return build_item(
        submission, kind=kind, timestamp=now, seq=seq, payload=payload,
        cursor_kwargs={"session_path": str(state.get("session_path") or "")},
    )


def _terminal(submission, state, now, status, reason, items=()):
    reply = str(state.get("reply_buffer") or "")
    confidence = CompletionConfidence.EXACT if status is CompletionStatus.COMPLETED else CompletionConfidence.DEGRADED
    updated = replace(submission, reply=reply, runtime_state=state, status=status, reason=reason, confidence=confidence)
    return ProviderPollResult(
        submission=updated, items=tuple(items),
        decision=CompletionDecision(
            terminal=True, status=status, reason=reason, confidence=confidence,
            reply=reply, anchor_seen=bool(state.get("anchor_seen")),
            reply_started=bool(reply), reply_stable=False,
            provider_turn_ref=str(state.get("request_anchor") or submission.job_id),
            source_cursor=None, finished_at=now,
            diagnostics={"mode": _MODE, "session_path": state.get("session_path")},
        ),
    )


def _timeout() -> float:
    try:
        value = float(os.environ.get("CCB_CODEBUDDY_RUN_TIMEOUT_S", "900"))
    except ValueError:
        return 900.0
    return value if 0 < value < float("inf") else 900.0


def _elapsed(start: str, end: str) -> float:
    return (datetime.fromisoformat(end.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds()


def build_execution_adapter() -> CodebuddyProviderAdapter:
    return CodebuddyProviderAdapter()


__all__ = ["CodebuddyProviderAdapter", "build_execution_adapter"]
