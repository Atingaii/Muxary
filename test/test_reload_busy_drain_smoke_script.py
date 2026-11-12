from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "reload_busy_drain_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("reload_busy_drain_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_busy_remove_config_removes_only_target_agent() -> None:
    module = _load_module()

    initial = module.build_busy_remove_config(provider="codex", include_agent2=True)
    target = module.build_busy_remove_config(provider="codex", include_agent2=False)

    assert 'main = "agent1:codex, agent2:codex"' in initial
    assert 'main = "agent1:codex"' in target
    assert "agent2" not in target


def test_prepare_busy_remove_project_writes_explicit_windows_config(tmp_path: Path) -> None:
    module = _load_module()

    prepared = module.prepare_busy_remove_project(
        test_root=tmp_path,
        project_name="busy-drain",
        provider="fake",
        reset=False,
    )

    project_root = Path(prepared["project_root"])
    role_store = Path(prepared["role_store"])
    config_text = (project_root / ".ccb" / "ccb.config").read_text(encoding="utf-8")
    assert 'entry_window = "main"' in config_text
    assert 'main = "agent1:fake, agent2:fake"' in config_text
    assert role_store.is_dir()


def test_build_busy_remove_config_can_widen_sidebar_for_visual_smoke() -> None:
    module = _load_module()

    text = module.build_busy_remove_config(provider="fake", include_agent2=True, sidebar_width="40%")

    assert "[ui.sidebar]" in text
    assert 'width = "40%"' in text


def test_real_provider_run_requires_explicit_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv(module.REAL_RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match=module.REAL_RUN_ENV):
        module.run_busy_remove_drain_smoke(
            test_root=tmp_path,
            project_name="real-provider",
            ccb_test=Path(__file__),
            provider="codex",
        )


def test_busy_remove_drain_flow_blocks_rejects_and_retries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module,
        "prepare_busy_remove_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )
    monkeypatch.setattr(
        module.layout_smoke,
        "preflight",
        lambda **kwargs: {"preflight_status": "ok", "checks": {"provider": kwargs["provider"]}},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "ask_agent2_busy":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_busy_agent2 target=agent2\n[CCB_ASYNC_SUBMITTED job=job_busy_agent2 target=agent2]\n",
                "stderr": "",
            }
        if name == "reload_remove_agent2_while_busy":
            return {
                "name": name,
                "returncode": 1,
                "stdout": "\n".join(
                    [
                        "reload_status: blocked",
                        "plan_class: remove_agent",
                        "reload_drain_active_count: 1",
                        "reload_drain_active: agent=agent2 intent_kind=unload phase=draining status=active",
                        "reload_drain_retry: ccb reload",
                    ]
                ),
                "stderr": "",
            }
        if name == "ask_agent2_during_reload_drain":
            return {
                "name": name,
                "returncode": 1,
                "stdout": "",
                "stderr": "error: agent agent2 is draining and rejects new work\n",
            }
        if name.startswith("watch_job_"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "watch_status: terminal\nstatus: completed\n",
                "stderr": "",
            }
        if name == "reload_remove_agent2_after_drain":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "reload_status: published\nplan_class: remove_agent\nreload_drain_active_count: 0\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_project_view(name, _project_root, *, timeout_s):
        del timeout_s
        if name == "project_view_after_blocked_reload":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "view": {
                        "reload_drains": {"active_count": 1, "retry_command": "ccb reload"},
                        "agents": [
                            {"name": "agent1", "dispatch_blocked_by_reload_drain": False},
                            {"name": "agent2", "dispatch_blocked_by_reload_drain": True},
                        ],
                        "windows": [{"name": "main", "agents": ["agent1", "agent2"]}],
                    }
                },
            }
        if name == "project_view_after_retry_reload":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "view": {
                        "reload_drains": {"active_count": 0},
                        "agents": [{"name": "agent1", "dispatch_blocked_by_reload_drain": False}],
                        "windows": [{"name": "main", "agents": ["agent1"]}],
                    }
                },
            }
        raise AssertionError(f"unexpected project view {name}")

    monkeypatch.setattr(module.layout_smoke, "_run", fake_run)
    monkeypatch.setattr(module, "_project_view_result", fake_project_view)

    payload = module.run_busy_remove_drain_smoke(
        test_root=tmp_path,
        project_name="busy-drain",
        ccb_test=Path("ccb_test"),
        provider="fake",
        command_timeout_s=1,
        reset=True,
        busy_latency_ms=1000,
    )

    assert payload["reload_busy_drain_smoke_status"] == "ok"
    checks = payload["checks"]
    assert checks["busy_ask_accepted"] is True
    assert checks["blocked_reload_reports_active_drain"] is True
    assert checks["project_view_records_active_drain"] is True
    assert checks["new_ask_rejected_while_draining"] is True
    assert checks["retry_reload_published"] is True
    assert checks["agent2_removed_from_view"] is True
    assert [name for name, _command in calls if name.startswith("reload_")] == [
        "reload_remove_agent2_while_busy",
        "reload_remove_agent2_after_drain",
    ]


def test_busy_remove_drain_flow_can_capture_sidebar_render(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"

    monkeypatch.setattr(
        module,
        "prepare_busy_remove_project",
        lambda **kwargs: {
            "project_root": str(project_root),
            "role_store": str(role_store),
            "sidebar_width": str(kwargs.get("sidebar_width") or ""),
        },
    )
    monkeypatch.setattr(
        module.layout_smoke,
        "preflight",
        lambda **kwargs: {"preflight_status": "ok", "checks": {"provider": kwargs["provider"]}},
    )

    def fake_run(name, command, **_kwargs):
        if name == "ask_agent2_busy":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_busy_agent2 target=agent2\n[CCB_ASYNC_SUBMITTED job=job_busy_agent2 target=agent2]\n",
                "stderr": "",
            }
        if name == "reload_remove_agent2_while_busy":
            return {
                "name": name,
                "returncode": 1,
                "stdout": "\n".join(
                    [
                        "reload_status: blocked",
                        "plan_class: remove_agent",
                        "reload_drain_active_count: 1",
                        "reload_drain_active: agent=agent2 intent_kind=unload phase=draining status=active",
                        "reload_drain_retry: ccb reload",
                    ]
                ),
                "stderr": "",
            }
        if name.startswith("sidebar_render_after_blocked_reload_attempt_"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "  ◐  agent2 [fake] drain:waiting\n",
                "stderr": "",
            }
        if name == "ask_agent2_during_reload_drain":
            return {"name": name, "returncode": 1, "stdout": "", "stderr": "agent2 is draining\n"}
        if name.startswith("watch_job_"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "watch_status: terminal\nstatus: completed\n",
                "stderr": "",
            }
        if name == "reload_remove_agent2_after_drain":
            return {"name": name, "returncode": 0, "stdout": "reload_status: published\n", "stderr": ""}
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_project_view(name, _project_root, *, timeout_s):
        del timeout_s
        if name == "project_view_after_blocked_reload":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "view": {
                        "namespace": {"socket_path": "/tmp/ccb.sock", "session_name": "ccb-test"},
                        "reload_drains": {"active_count": 1, "retry_command": "ccb reload"},
                        "agents": [
                            {"name": "agent1", "dispatch_blocked_by_reload_drain": False},
                            {"name": "agent2", "dispatch_blocked_by_reload_drain": True},
                        ],
                        "windows": [
                            {"name": "main", "agents": ["agent1", "agent2"], "sidebar_pane_id": "%1"}
                        ],
                    }
                },
            }
        if name == "project_view_after_retry_reload":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "view": {
                        "reload_drains": {"active_count": 0},
                        "agents": [{"name": "agent1", "dispatch_blocked_by_reload_drain": False}],
                        "windows": [{"name": "main", "agents": ["agent1"], "sidebar_pane_id": "%1"}],
                    }
                },
            }
        raise AssertionError(f"unexpected project view {name}")

    monkeypatch.setattr(module.layout_smoke, "_run", fake_run)
    monkeypatch.setattr(module, "_project_view_result", fake_project_view)

    payload = module.run_busy_remove_drain_smoke(
        test_root=tmp_path,
        project_name="busy-drain",
        ccb_test=Path("ccb_test"),
        provider="fake",
        command_timeout_s=1,
        reset=True,
        busy_latency_ms=1000,
        check_sidebar_render=True,
    )

    assert payload["reload_busy_drain_smoke_status"] == "ok"
    assert payload["check_sidebar_render"] is True
    assert payload["checks"]["sidebar_renders_active_drain"] is True
    assert any(command["name"] == "sidebar_render_after_blocked_reload" for command in payload["commands"])


def test_sidebar_capture_scope_requires_socket_session_and_sidebar_pane() -> None:
    module = _load_module()
    payload = {
        "view": {
            "namespace": {"socket_path": "/tmp/ccb.sock", "session_name": "ccb-test"},
            "windows": [{"name": "main", "sidebar_pane_id": "%7"}],
        }
    }

    assert module._sidebar_capture_scope(payload, window_name="main") == (
        "/tmp/ccb.sock",
        "ccb-test",
        "%7",
    )
    assert module._sidebar_capture_scope({"view": {"namespace": {}, "windows": []}}, window_name="main") is None


def test_main_passes_arguments_to_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return {"reload_busy_drain_smoke_status": "ok", "commands": [], "checks": {}}

    monkeypatch.setattr(module, "run_busy_remove_drain_smoke", fake_runner)

    assert (
        module.main(
            [
                "--provider",
                "fake",
                "--command-timeout",
                "77",
                "--project-name",
                "drain",
                "--auto-retry",
                "--check-sidebar-render",
            ]
        )
        == 0
    )
    assert captured["provider"] == "fake"
    assert captured["project_name"] == "drain"
    assert captured["command_timeout_s"] == 77
    assert captured["auto_retry"] is True
    assert captured["check_sidebar_render"] is True


def test_tests_workflow_runs_reload_busy_drain_fake_smoke() -> None:
    text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "Guard reload busy drain smoke" in text
    assert "scripts/reload_busy_drain_smoke.py" in text
    assert "ci-reload-busy-drain" in text
    assert "matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'" in text
    assert "--provider fake" in text
    assert "--busy-latency-ms 5000" in text
    assert "--auto-retry" in text
    assert 'payload["reload_busy_drain_smoke_status"] == "ok"' in text
    assert 'checks["blocked_reload_reports_active_drain"] is True' in text
    assert 'checks["project_view_records_active_drain"] is True' in text
    assert 'checks["new_ask_rejected_while_draining"] is True' in text
    assert 'checks["auto_retry_published"] is True' in text
    assert 'checks["agent2_removed_from_view"] is True' in text
