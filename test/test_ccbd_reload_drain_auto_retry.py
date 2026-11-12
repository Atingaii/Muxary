from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ccbd.app import CcbdApp
from ccbd.reload_drain import DrainIntent, DrainQueue, DrainQueueStore, plan_drain_transition
from ccbd.reload_drain_auto_retry import tick_reload_drain_auto_retry


BASE_CONFIG = """version = 2
entry_window = "main"

[windows]
main = "agent1:fake, agent2:fake"
"""

REMOVE_AGENT_CONFIG = """version = 2
entry_window = "main"

[windows]
main = "agent1:fake"
"""


def test_reload_drain_auto_retry_applies_ready_remove_agent(tmp_path: Path) -> None:
    app = _app_with_active_drain(tmp_path / "repo-auto-retry-apply", target_config=REMOVE_AGENT_CONFIG, busy=False)
    calls: list[dict[str, object]] = []

    def fake_apply(_app, new_config, **kwargs):
        calls.append(
            {
                "agents": tuple(new_config.agents),
                "current_namespace": kwargs.get("current_namespace"),
                "lock_already_held": kwargs.get("lock_already_held"),
            }
        )
        return SimpleNamespace(status="published", plan_class="remove_agent", reason="")

    payload = tick_reload_drain_auto_retry(app, run_apply_fn=fake_apply)

    assert payload["reload_drain_auto_retry_status"] == "applied"
    assert payload["retry_agents"] == ["agent2"]
    assert payload["apply_status"] == "published"
    assert calls == [
        {
            "agents": ("agent1",),
            "current_namespace": None,
            "lock_already_held": True,
        }
    ]
    queue = app.reload_drain_store.load()
    active = queue.active_records_for("agent2")
    assert len(active) == 1
    assert active[0].status == "idle_ready"


def test_reload_drain_auto_retry_waits_while_target_busy(tmp_path: Path) -> None:
    app = _app_with_active_drain(tmp_path / "repo-auto-retry-wait", target_config=REMOVE_AGENT_CONFIG, busy=True)

    def fail_apply(*_args, **_kwargs):
        raise AssertionError("busy drain must not apply")

    payload = tick_reload_drain_auto_retry(app, run_apply_fn=fail_apply)

    assert payload["reload_drain_auto_retry_status"] == "waiting"
    assert payload["ready_agents"] == []
    assert payload["waiting_agents"] == ["agent2"]
    queue = app.reload_drain_store.load()
    active = queue.active_records_for("agent2")
    assert len(active) == 1
    assert active[0].status == "waiting"
    assert active[0].busy is True


def test_reload_drain_auto_retry_retires_stale_ready_drain_when_config_restored(tmp_path: Path) -> None:
    app = _app_with_active_drain(tmp_path / "repo-auto-retry-stale", target_config=BASE_CONFIG, busy=False)

    def fail_apply(*_args, **_kwargs):
        raise AssertionError("stale drain must not apply")

    payload = tick_reload_drain_auto_retry(app, run_apply_fn=fail_apply)

    assert payload["reload_drain_auto_retry_status"] == "skipped"
    assert payload["reason"] == "no_ready_drain_matches_current_remove_plan"
    assert payload["ready_agents"] == ["agent2"]
    assert payload["retired_stale_agents"] == ["agent2"]
    queue = app.reload_drain_store.load()
    assert queue.active_records_for("agent2") == ()
    assert queue.records[-1].status == "retired"


def test_reload_drain_auto_retry_can_be_disabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    app = _app_with_active_drain(tmp_path / "repo-auto-retry-disabled", target_config=REMOVE_AGENT_CONFIG, busy=False)
    monkeypatch.setenv("CCB_CCBD_RELOAD_DRAIN_AUTO_RETRY", "0")

    def fail_apply(*_args, **_kwargs):
        raise AssertionError("disabled auto retry must not apply")

    payload = tick_reload_drain_auto_retry(app, run_apply_fn=fail_apply)

    assert payload == {
        "reload_drain_auto_retry_status": "noop",
        "reason": "reload_drain_auto_retry_disabled",
    }


def _app_with_active_drain(project_root: Path, *, target_config: str, busy: bool) -> CcbdApp:
    (project_root / ".ccb").mkdir(parents=True)
    (project_root / ".ccb" / "ccb.config").write_text(BASE_CONFIG, encoding="utf-8")
    app = CcbdApp(project_root, clock=lambda: "2026-06-28T00:00:00Z")
    app.reload_drain_clock_s = lambda: 2.0
    app.dispatcher._has_outstanding_work = lambda agent_name: bool(busy and agent_name == "agent2")
    _write_active_drain(app.reload_drain_store, busy=busy)
    (project_root / ".ccb" / "ccb.config").write_text(target_config, encoding="utf-8")
    return app


def _write_active_drain(store: DrainQueueStore, *, busy: bool) -> None:
    intent = DrainIntent(
        intent_id="drain-agent2",
        intent_kind="unload",
        agent_name="agent2",
        created_at_s=0.0,
        reason="test busy unload",
    )
    result = DrainQueue.empty().enqueue(intent, now_s=0.0)
    record = plan_drain_transition(result.record, now_s=1.0, is_busy=lambda _record: busy)
    store.save(result.queue.replace_record(record))
