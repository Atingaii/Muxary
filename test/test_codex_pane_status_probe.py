from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "probe_codex_pane_status.py"
SPEC = importlib.util.spec_from_file_location("probe_codex_pane_status", SCRIPT_PATH)
probe = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
sys.modules[SPEC.name] = probe
SPEC.loader.exec_module(probe)


def test_parse_codex_working_line_without_ui_elapsed_or_confidence() -> None:
    status = probe.parse_codex_pane_status("• Working (28s • esc to interrupt)\n")

    assert status.state == "working"
    assert status.reason == "codex_working_status_line"
    assert "running_status_time" in status.matched_patterns
    record = status.to_record()
    assert "status_elapsed_s" not in record
    assert "confidence" not in record


def test_parse_codex_booting_mcp_status_line_without_space_after_bullet() -> None:
    status = probe.parse_codex_pane_status("•Booting MCP server: codex_apps(0s • esc to interrupt)\n")

    assert status.state == "working"
    assert status.reason == "codex_working_status_line"
    assert "running_status_time" in status.matched_patterns


def test_parse_codex_booting_mcp_status_line_with_hollow_bullet() -> None:
    status = probe.parse_codex_pane_status("◦ Booting MCP server: codex_apps (2s • esc to interrupt)\n")

    assert status.state == "working"
    assert status.reason == "codex_working_status_line"
    assert "running_status_time" in status.matched_patterns


def test_chat_text_with_working_keywords_does_not_trigger_working() -> None:
    text = "\n".join(
        [
            "› Explain this UI line",
            "",
            "The screen can show Working (9m 47s • esc to interrupt),",
            "but that sentence is part of the conversation body.",
            "",
            "› Use /skills to list available skills",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "unknown"
    assert status.reason == "no_known_status_pattern"


def test_indented_status_shaped_text_is_not_a_codex_status_line() -> None:
    text = "\n".join(
        [
            "› Explain this UI line",
            "",
            "  • Working (9m 47s • esc to interrupt)",
            "",
            "› Use /skills to list available skills",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "unknown"
    assert status.reason == "no_known_status_pattern"


def test_bullet_body_text_with_working_keyword_is_not_status_line() -> None:
    text = "\n".join(
        [
            "› Explain this UI line",
            "",
            "• The phrase Working (9m 47s • esc to interrupt) appears in docs.",
            "",
            "› Use /skills to list available skills",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "unknown"
    assert status.reason == "no_known_status_pattern"


def test_parse_codex_background_terminal_as_tool_running() -> None:
    status = probe.parse_codex_pane_status(
        "• Working (20s • esc to interrupt) · 1 background terminal running · /ps to view\n"
    )

    assert status.state == "tool_running"
    assert status.reason == "provider_tool_running"


def test_parse_prompt_only_is_unknown_not_idle() -> None:
    text = "\n".join(
        [
            "│ permissions: YOLO mode                               │",
            "⚠ `--dangerously-bypass-hook-trust` is enabled.",
            "",
            "› Improve documentation in @filename",
            "",
            "  gpt-5.5 default · /home/bfly/yunwei/test_ccb2",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "unknown"
    assert status.reason == "no_known_status_pattern"


def test_stale_working_marker_remains_working_without_explicit_terminal_signal() -> None:
    text = "\n".join(
        [
            "• Working (20s • esc to interrupt)",
            "",
            "› Run a task",
            "",
            "done",
            "",
            "› Use /skills to list available skills",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "working"
    assert status.reason == "codex_working_status_line"


def test_parse_trust_menu_as_waiting_for_user() -> None:
    text = "\n".join(
        [
            "Do you trust the contents of this directory?",
            "",
            "› 1. Yes, continue",
            "  2. No, quit",
            "",
            "  Press enter to continue",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "waiting_for_user"
    assert status.reason == "provider_waiting_for_user"


def test_parse_login_menu_as_auth_required() -> None:
    text = "\n".join(
        [
            "Sign in with ChatGPT to use Codex as part of your paid plan",
            "or connect an API key for usage-based billing",
            "",
            "> 1. Sign in with ChatGPT",
            "  2. Sign in with Device Code",
            "  3. Provide your own API key",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "auth_required"
    assert status.reason == "codex_auth_required"


def test_parse_error_text_as_api_error() -> None:
    status = probe.parse_codex_pane_status(
        "ERROR: stream disconnected before completion: error sending request for url\n"
    )

    assert status.state == "api_error"
    assert status.terminal_outcome == "failed"


def test_parse_auth_failed_text_as_auth_failed() -> None:
    status = probe.parse_codex_pane_status("Authentication failed: invalid API key\n")

    assert status.state == "auth_failed"
    assert status.reason == "provider_auth_failed"
    assert status.terminal_outcome == "failed"


def test_parse_config_error_text_as_config_error() -> None:
    status = probe.parse_codex_pane_status("Failed to parse config.toml: invalid configuration\n")

    assert status.state == "config_error"
    assert status.reason == "provider_config_error"
    assert status.terminal_outcome == "failed"


def test_parse_reconnecting_status_ignores_retry_count_and_ui_elapsed() -> None:
    text = "\n".join(
        [
            "• Reconnecting... 2/5 (16s • esc to interrupt)",
            "  └ Stream disconnected before completion: IO error: peer closed connection without sending TLS close_notify",
            "",
            "› Summarize recent commits",
        ]
    )

    status = probe.parse_codex_pane_status(text)
    record = status.to_record()

    assert status.state == "reconnecting"
    assert status.reason == "provider_reconnecting"
    assert "retry_attempt" not in record
    assert "retry_limit" not in record
    assert "status_elapsed_s" not in record
    assert status.terminal_outcome is None


def test_parse_pane_dead_as_pane_dead() -> None:
    status = probe.parse_codex_pane_status("› idle", pane_dead=True)

    assert status.state == "pane_dead"
    assert status.terminal_outcome == "pane_dead"


def test_conversation_interrupted_text_is_not_a_current_state() -> None:
    text = "\n".join(
        [
            "› Write a long answer",
            "",
            "■ Conversation interrupted - tell the model what to do differently.",
            "",
            "› Use /skills to list available skills",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "unknown"
    assert status.terminal_outcome is None


def test_parse_worked_for_summary_as_completed_without_ui_elapsed_field() -> None:
    text = "\n".join(
        [
            "› Reply with exactly: done",
            "",
            "done",
            "",
            "• Worked for 4s",
            "",
            "› Use /skills to list available skills",
        ]
    )

    status = probe.parse_codex_pane_status(text)
    record = status.to_record()

    assert status.state == "completed"
    assert status.reason == "codex_worked_for_terminal_summary"
    assert status.terminal_outcome == "completed"
    assert "terminal_elapsed_s" not in record


def test_worked_for_summary_after_working_text_wins() -> None:
    text = "\n".join(
        [
            "• Working (12s • esc to interrupt)",
            "",
            "• The answer is complete.",
            "",
            "• Worked for 6s",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "completed"
    assert status.terminal_outcome == "completed"


def test_working_text_after_worked_for_wins() -> None:
    text = "\n".join(
        [
            "• Worked for 6s",
            "",
            "• Working (12s • esc to interrupt)",
        ]
    )

    status = probe.parse_codex_pane_status(text)

    assert status.state == "working"
    assert status.terminal_outcome is None


def test_status_catalog_excludes_removed_fallback_states() -> None:
    for state in ("streaming_answer", "stalled", "queued", "idle"):
        assert state not in probe.STATUS_CATALOG
    assert "interrupted" in probe.STATUS_CATALOG
    for state in ("free", "start", "working", "reconnecting", "unknown"):
        assert state in probe.STATUS_CATALOG
    assert "completed" not in probe.STATUS_CATALOG
    assert "completed" in probe.PANE_STATUS_CATALOG


def test_prompt_send_blocking_uses_blocking_states_not_idle_prompt() -> None:
    assert probe.prompt_can_be_sent(probe.PaneStatus("unknown", "no_known_status_pattern")) is True
    assert probe.prompt_can_be_sent(probe.PaneStatus("working", "codex_working_status_line")) is False
    assert probe.prompt_can_be_sent(probe.PaneStatus("tool_running", "provider_tool_running")) is False
    assert probe.prompt_can_be_sent(probe.PaneStatus("reconnecting", "provider_reconnecting")) is False
    assert probe.prompt_can_be_sent(probe.PaneStatus("waiting_for_user", "provider_waiting_for_user")) is False
    assert probe.prompt_can_be_sent(probe.PaneStatus("auth_required", "codex_auth_required")) is False
    assert probe.prompt_can_be_sent(probe.PaneStatus("api_error", "provider_api_error")) is False
    assert probe.prompt_can_be_sent(probe.PaneStatus("pane_dead", "pane_dead")) is False


def test_next_sample_delay_uses_active_and_base_intervals() -> None:
    args = probe.parse_args([])
    unknown = probe.PaneStatus("unknown", "empty_capture")
    working = probe.PaneStatus("working", "codex_working_status_line")

    assert probe.next_sample_delay_s(args, status=unknown) == 0.5
    assert probe.next_sample_delay_s(args, status=working) == 0.25


def test_turn_timing_uses_probe_clock_for_active_display_elapsed() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    runtime.prompt_sent_at_s = 10.0
    working = probe.PaneStatus("working", "codex_working_status_line")

    active = probe.update_turn_timing(runtime, status=working, now_s=12.0)

    assert active["phase"] == "active"
    assert active["display_elapsed_s"] == 2
    assert active["display_elapsed_source"] == "probe_submit_clock"
    assert active["first_active_latency_s"] == 2


def test_turn_timing_terminalizes_worked_for_without_prior_active_sample() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    runtime.prompt_sent_at_s = 10.0
    completed = probe.PaneStatus(
        "completed",
        "codex_worked_for_terminal_summary",
        terminal_outcome="completed",
    )

    terminal = probe.update_turn_timing(runtime, status=completed, now_s=12.5)

    assert terminal["phase"] == "terminal"
    assert terminal["terminal_state"] == "completed"
    assert terminal["terminal_outcome"] == "completed"
    assert terminal["terminal_elapsed_s"] == 2.5
    assert runtime.first_active_at_s is None


def test_turn_timing_does_not_complete_unknown_after_active() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    runtime.prompt_sent_at_s = 10.0
    working = probe.PaneStatus("working", "codex_working_status_line")
    unknown = probe.PaneStatus("unknown", "no_known_status_pattern")

    probe.update_turn_timing(runtime, status=working, now_s=11.0)
    record = probe.update_turn_timing(runtime, status=unknown, now_s=12.2)

    assert record["phase"] == "unknown"
    assert "terminal_state" not in record
    assert runtime.turn_terminal_at_s is None


def test_turn_timing_terminalizes_session_task_complete_as_free() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    runtime.prompt_sent_at_s = 10.0
    pane_unknown = probe.PaneStatus("unknown", "no_known_status_pattern")
    runtime_status = probe.CodexRuntimeStatus(
        "free",
        "codex_session_task_complete",
        "session",
        "unknown",
        "no_known_status_pattern",
        "free",
        "codex_session_task_complete",
    )

    terminal = probe.update_turn_timing(runtime, status=pane_unknown, runtime_status=runtime_status, now_s=12.5)

    assert terminal["phase"] == "terminal"
    assert terminal["terminal_state"] == "free"
    assert terminal["terminal_outcome"] == "completed"


def _runtime_status(
    state: str,
    reason: str,
    *,
    pane_state: str = "unknown",
    pane_reason: str = "no_known_status_pattern",
    session_state: str | None = None,
    session_reason: str | None = None,
) -> probe.CodexRuntimeStatus:
    return probe.CodexRuntimeStatus(
        state,
        reason,
        "test",
        pane_state,
        pane_reason,
        session_state,
        session_reason,
    )


def test_stabilizer_suppresses_startup_session_free_before_pane_settles() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    raw_free = _runtime_status("free", "codex_session_task_complete", session_state="free")

    stable = probe.stabilize_runtime_status(runtime, raw_free, now_s=0.5)

    assert stable.state == "unknown"
    assert stable.source == "stabilizer"
    assert stable.reason == "startup_free_grace"
    assert "raw_state=free" in stable.notes


def test_stabilizer_marks_submitted_unknown_as_start() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    runtime.prompt_sent_at_s = 10.0
    raw_unknown = _runtime_status("unknown", "no_known_status_pattern")

    stable = probe.stabilize_runtime_status(runtime, raw_unknown, now_s=10.4)

    assert stable.state == "start"
    assert stable.source == "stabilizer"
    assert stable.reason == "prompt_submitted_waiting_for_first_signal"
    assert "raw_state=unknown" in stable.notes


def test_stabilizer_keeps_unknown_before_prompt_as_unknown() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    raw_unknown = _runtime_status("unknown", "no_known_status_pattern")

    stable = probe.stabilize_runtime_status(runtime, raw_unknown, now_s=3.0)

    assert stable.state == "unknown"
    assert stable.source == "test"


def test_stabilizer_does_not_hide_fast_session_complete_as_start() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    runtime.prompt_sent_at_s = 10.0
    raw_free = _runtime_status("free", "codex_session_task_complete", session_state="free")

    stable = probe.stabilize_runtime_status(runtime, raw_free, now_s=10.2)

    assert stable.state == "free"
    assert stable.reason == "codex_session_task_complete"


def test_stabilizer_holds_recent_working_over_soft_free() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    working = _runtime_status("working", "codex_working_status_line", pane_state="working", pane_reason="codex_working_status_line")
    free = _runtime_status("free", "codex_session_task_complete", session_state="free")

    assert probe.stabilize_runtime_status(runtime, working, now_s=1.0).state == "working"
    held = probe.stabilize_runtime_status(runtime, free, now_s=1.5)
    released = probe.stabilize_runtime_status(runtime, free, now_s=2.7)

    assert held.state == "working"
    assert held.reason == "active_hold_after_recent_work"
    assert released.state == "free"
    assert released.reason == "codex_session_task_complete"


def test_stabilizer_does_not_hold_working_over_hard_waiting_state() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    working = _runtime_status("working", "codex_working_status_line", pane_state="working", pane_reason="codex_working_status_line")
    waiting = _runtime_status(
        "waiting_for_user",
        "provider_waiting_for_user",
        pane_state="waiting_for_user",
        pane_reason="provider_waiting_for_user",
    )

    probe.stabilize_runtime_status(runtime, working, now_s=1.0)
    stable = probe.stabilize_runtime_status(runtime, waiting, now_s=1.2)

    assert stable.state == "waiting_for_user"
    assert stable.source == "test"


def test_stabilizer_holds_previous_free_over_short_empty_capture() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    free = _runtime_status("free", "codex_session_task_complete", session_state="free")
    empty = _runtime_status("unknown", "empty_capture", pane_reason="empty_capture", session_state="free")

    probe.stabilize_runtime_status(runtime, free, now_s=3.0)
    held = probe.stabilize_runtime_status(runtime, empty, now_s=3.5)

    assert held.state == "free"
    assert held.reason == "empty_capture_hold_previous"


def test_stabilizer_releases_long_empty_capture_hold() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.started_at_s = 0.0
    free = _runtime_status("free", "codex_session_task_complete", session_state="free")
    empty = _runtime_status("unknown", "empty_capture", pane_reason="empty_capture", session_state="free")

    probe.stabilize_runtime_status(runtime, free, now_s=3.0)
    held = probe.stabilize_runtime_status(runtime, empty, now_s=3.2)
    released = probe.stabilize_runtime_status(runtime, empty, now_s=5.3)

    assert held.state == "free"
    assert released.state == "unknown"
    assert released.reason == "empty_capture"


def test_transition_event_mode_ignores_removed_timer_fields() -> None:
    previous = {
        "state": "working",
        "reason": "codex_working_status_line",
        "terminal_outcome": None,
    }
    same_state = dict(previous)
    state_change = dict(previous)
    state_change["state"] = "unknown"
    state_change["reason"] = "no_known_status_pattern"

    assert probe.should_emit_status_event("all", previous, same_state) is True
    assert probe.should_emit_status_event("transitions", None, previous) is True
    assert probe.should_emit_status_event("transitions", previous, same_state) is False
    assert probe.should_emit_status_event("transitions", previous, state_change) is True


def test_build_metrics_includes_stability_and_overhead() -> None:
    runtime = probe.ProbeRuntime(paths=probe.build_paths(Path("/tmp/codex-pane-test")), session_name="")
    runtime.capture_count = 4
    runtime.capture_duration_s = [0.001, 0.002, 0.003, 0.010]
    records = [
        {
            "elapsed_s": 0.0,
            "state": "unknown",
            "reason": "no_known_status_pattern",
        },
        {
            "elapsed_s": 0.2,
            "state": "working",
            "reason": "codex_working_status_line",
        },
        {
            "elapsed_s": 0.4,
            "state": "unknown",
            "reason": "no_known_status_pattern",
        },
    ]

    metrics = probe.build_metrics(
        runtime,
        ["unknown", "working", "unknown"],
        state_records=records,
        flicker_window_s=1.0,
    )

    assert metrics["capture_duration_p95_s"] == 0.003
    assert metrics["sample_count"] == 3
    assert metrics["transition_count"] == 2
    assert "raw_transition_count" not in metrics
    assert metrics["flicker_transition_count"] == 1
    assert metrics["state_dwell_s"] == {"unknown": 0.2, "working": 0.2}
