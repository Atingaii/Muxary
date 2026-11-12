from __future__ import annotations

from pathlib import Path

from provider_pane_status.codex_pane import parse_codex_pane_status
from provider_pane_status.models import (
    PaneCompletionEvidence,
    ProviderPaneStatusSignal,
    SOURCE_STATUS_ERROR,
    SOURCE_STATUS_OK,
)


def test_codex_parser_direct_module_keeps_body_text_unknown() -> None:
    status = parse_codex_pane_status(
        "\n".join(
            [
                "› Explain this status text",
                "",
                "The UI can show • Working (9m 47s • esc to interrupt).",
                "",
                "› Use /skills to list available skills",
            ]
        )
    )

    assert status.state == "unknown"
    assert status.reason == "no_known_status_pattern"
    assert status.completion_evidence is None


def test_codex_parser_direct_module_exposes_worked_for_as_observation_only() -> None:
    status = parse_codex_pane_status("• Worked for 4s\n")
    record = status.to_record()

    assert status.state == "completed"
    assert status.terminal_outcome == "completed"
    assert isinstance(status.completion_evidence, PaneCompletionEvidence)
    assert status.completion_evidence.__not_a_job_terminator__() is None
    assert record["completion_evidence"] == {
        "outcome": "completed",
        "reason": "codex_worked_for_terminal_summary",
        "source": "codex_pane",
    }


def test_provider_signal_separates_capture_error_from_parse_unknown() -> None:
    parsed_unknown = ProviderPaneStatusSignal(
        provider="codex",
        source_status=SOURCE_STATUS_OK,
        parsed_state="unknown",
        reason="no_known_status_pattern",
    )
    source_error = ProviderPaneStatusSignal(
        provider="codex",
        source_status=SOURCE_STATUS_ERROR,
        parsed_state="unknown",
        reason="tmux_capture_failed",
    )

    assert parsed_unknown.to_record()["source_status"] == "ok"
    assert source_error.to_record()["source_status"] == "error"
    assert parsed_unknown.to_record()["parsed_state"] == "unknown"
    assert source_error.to_record()["parsed_state"] == "unknown"


def test_probe_script_imports_shared_parser_without_local_codex_regex() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "probe_codex_pane_status.py"
    source = script_path.read_text(encoding="utf-8")

    assert "from provider_pane_status.codex_pane import" in source
    assert "STATUS_MARKER_RE" not in source
    assert "CODEX_WORKING_LINE_RE" not in source
    assert "CODEX_RECONNECT_LINE_RE" not in source
    assert "CODEX_TOOL_LINE_RE" not in source
