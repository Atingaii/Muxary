from __future__ import annotations

import json
from pathlib import Path

from provider_backends.codex.comm import CodexLogReader
from provider_backends.codex.comm_runtime import extract_cwd_from_log_file, extract_session_id, is_codex_subagent_log


def test_extract_cwd_from_log_file_reads_session_meta(tmp_path: Path) -> None:
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "cwd": f"  {tmp_path / 'repo'}  ",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert extract_cwd_from_log_file(log_path) == str(tmp_path / "repo")


def test_extract_session_id_reads_nested_payload_when_filename_has_no_uuid(tmp_path: Path) -> None:
    session_id = "123e4567-e89b-12d3-a456-426614174321"
    log_path = tmp_path / "session.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "session": {
                        "id": session_id,
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert extract_session_id(log_path) == session_id


def test_codex_subagent_log_is_identified_from_session_meta(tmp_path: Path) -> None:
    log_path = tmp_path / "subagent.jsonl"
    log_path.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "cwd": str(tmp_path),
                    "thread_source": "subagent",
                    "source": {"subagent": {"thread_spawn": {"parent_thread_id": "parent-1"}}},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert is_codex_subagent_log(log_path) is True


def test_codex_log_scan_ignores_newer_subagent_with_same_work_dir(tmp_path: Path) -> None:
    work_dir = tmp_path / "repo"
    session_root = tmp_path / "sessions"
    work_dir.mkdir()
    session_root.mkdir()
    parent = session_root / "rollout-parent.jsonl"
    child = session_root / "rollout-child.jsonl"
    parent.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {"cwd": str(work_dir), "thread_source": "user", "source": "cli"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    child.write_text(
        json.dumps(
            {
                "type": "session_meta",
                "payload": {
                    "cwd": str(work_dir),
                    "thread_source": "subagent",
                    "source": {"subagent": {"thread_spawn": {"parent_thread_id": "parent"}}},
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    parent.touch()
    child.touch()

    reader = CodexLogReader(root=session_root, work_dir=work_dir, follow_workspace_sessions=True)

    assert reader.current_log_path() == parent
