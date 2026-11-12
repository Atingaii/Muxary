from __future__ import annotations

import json
from pathlib import Path

from provider_pane_status.codex_pane import PaneStatus
from provider_pane_status.codex_session import (
    compose_codex_runtime_status,
    read_codex_session_status,
)


def _write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _meta(cwd: Path) -> dict[str, object]:
    return {
        "type": "session_meta",
        "payload": {
            "cwd": str(cwd),
            "session_id": "sid-1",
        },
    }


def _event(payload_type: str) -> dict[str, object]:
    return {
        "type": "event_msg",
        "payload": {
            "type": payload_type,
            "turn_id": "turn-1",
        },
    }


def test_empty_session_root_is_free_without_prompt_floor(tmp_path: Path) -> None:
    root = tmp_path / "sessions"
    root.mkdir()

    status = read_codex_session_status(root, work_dir=tmp_path / "work")

    assert status.state == "free"
    assert status.reason == "no_codex_session_files"


def test_empty_session_root_is_unknown_after_prompt_floor(tmp_path: Path) -> None:
    root = tmp_path / "sessions"
    root.mkdir()

    status = read_codex_session_status(root, work_dir=tmp_path / "work", min_mtime_s=1.0)

    assert status.state == "unknown"
    assert status.reason == "no_recent_codex_session_files"


def test_no_matching_workdir_session_is_free_without_prompt_floor(tmp_path: Path) -> None:
    other_work_dir = tmp_path / "other"
    current_work_dir = tmp_path / "current"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(session, [_meta(other_work_dir), _event("task_complete")])

    status = read_codex_session_status(tmp_path / "sessions", work_dir=current_work_dir)
    after_prompt = read_codex_session_status(tmp_path / "sessions", work_dir=current_work_dir, min_mtime_s=1.0)

    assert status.state == "free"
    assert status.reason == "no_matching_codex_session_files"
    assert after_prompt.state == "unknown"
    assert after_prompt.reason == "no_recent_matching_codex_session_files"


def test_task_started_without_complete_is_working(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(session, [_meta(work_dir), _event("task_started")])

    status = read_codex_session_status(tmp_path / "sessions", work_dir=work_dir)

    assert status.state == "working"
    assert status.reason == "codex_session_task_started"


def test_task_complete_is_free(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(session, [_meta(work_dir), _event("task_started"), _event("task_complete")])

    status = read_codex_session_status(tmp_path / "sessions", work_dir=work_dir)

    assert status.state == "free"
    assert status.reason == "codex_session_task_complete"


def test_turn_aborted_after_task_started_is_interrupted(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(session, [_meta(work_dir), _event("task_started"), _event("turn_aborted")])

    status = read_codex_session_status(tmp_path / "sessions", work_dir=work_dir)

    assert status.state == "interrupted"
    assert status.reason == "codex_session_turn_aborted"
    assert status.matched_patterns == ("turn_aborted",)


def test_thread_rolled_back_after_task_started_is_interrupted(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(session, [_meta(work_dir), _event("task_started"), _event("thread_rolled_back")])

    status = read_codex_session_status(tmp_path / "sessions", work_dir=work_dir)

    assert status.state == "interrupted"
    assert status.reason == "codex_session_thread_rolled_back"
    assert status.matched_patterns == ("thread_rolled_back",)


def test_assistant_message_without_task_complete_stays_unknown(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(
        session,
        [
            _meta(work_dir),
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "done"}],
                },
            },
        ],
    )

    status = read_codex_session_status(tmp_path / "sessions", work_dir=work_dir)

    assert status.state == "unknown"
    assert status.reason == "no_session_task_boundary"
    assert "assistant_response_without_task_complete" in status.notes


def test_runtime_uses_session_free_only_when_pane_is_unknown(tmp_path: Path) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    session_status = read_codex_session_status(root)

    unknown = compose_codex_runtime_status(PaneStatus("unknown", "no_known_status_pattern"), session_status)
    working = compose_codex_runtime_status(PaneStatus("working", "codex_working_status_line"), session_status)

    assert unknown.state == "free"
    assert unknown.source == "session"
    assert working.state == "working"
    assert working.source == "pane"


def test_runtime_does_not_mark_empty_capture_free(tmp_path: Path) -> None:
    root = tmp_path / "sessions"
    root.mkdir()
    session_status = read_codex_session_status(root)

    runtime = compose_codex_runtime_status(PaneStatus("unknown", "empty_capture"), session_status)

    assert runtime.state == "unknown"
    assert runtime.reason == "empty_capture"


def test_runtime_uses_session_interrupted_when_pane_is_unknown(tmp_path: Path) -> None:
    work_dir = tmp_path / "work"
    session = tmp_path / "sessions" / "2026" / "06" / "29" / "rollout-demo.jsonl"
    _write_jsonl(session, [_meta(work_dir), _event("task_started"), _event("turn_aborted")])
    session_status = read_codex_session_status(tmp_path / "sessions", work_dir=work_dir)

    runtime = compose_codex_runtime_status(PaneStatus("unknown", "no_known_status_pattern"), session_status)

    assert runtime.state == "interrupted"
    assert runtime.reason == "codex_session_turn_aborted"
    assert runtime.source == "session"
