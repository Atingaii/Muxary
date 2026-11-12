from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dynamic_agent_lifecycle_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dynamic_agent_lifecycle_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_lifecycle_config_declares_explicit_windows() -> None:
    module = _load_module()

    text = module.build_lifecycle_config(provider="codex")

    assert 'entry_window = "main"' in text
    assert "[windows]" in text
    assert 'main = "frontdesk:codex"' in text
    assert 'plan-orchestrate = "planner:codex"' in text


def test_prepare_lifecycle_project_writes_roles_and_config(tmp_path: Path) -> None:
    module = _load_module()

    prepared = module.prepare_lifecycle_project(
        test_root=tmp_path,
        project_name="lifecycle",
        provider="fake",
        reset=False,
    )

    project_root = Path(prepared["project_root"])
    role_store = Path(prepared["role_store"])
    config_text = (project_root / ".ccb" / "ccb.config").read_text(encoding="utf-8")
    assert 'main = "frontdesk:fake"' in config_text
    assert 'plan-orchestrate = "planner:fake"' in config_text
    assert (role_store / "installed" / "agentroles.ccb_planner" / "current" / "role.toml").is_file()
    assert (role_store / "installed" / "agentroles.code_reviewer" / "current" / "role.toml").is_file()


def test_real_provider_run_requires_explicit_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv(module.REAL_RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match=module.REAL_RUN_ENV):
        module.run_lifecycle_policy_smoke(
            test_root=tmp_path,
            project_name="real-provider",
            ccb_test=Path(__file__),
            provider="codex",
        )


def test_lifecycle_policy_flow_parks_long_lived_and_unloads_short_lived(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module,
        "prepare_lifecycle_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )
    monkeypatch.setattr(
        module.layout_smoke,
        "preflight",
        lambda **kwargs: {"preflight_status": "ok", "checks": {"provider": kwargs["provider"]}},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("ask_planner_helper_while_parked"):
            return {
                "name": name,
                "returncode": 1,
                "stdout": "",
                "stderr": "error: agent planner_helper is parked or dispatch disabled\n",
            }
        if name.startswith("ask_"):
            target = name.removeprefix("ask_")
            job = f"job_{target}"
            return {
                "name": name,
                "returncode": 0,
                "stdout": f"accepted job={job} target={target}\n[CCB_ASYNC_SUBMITTED job={job} target={target}]\n",
                "stderr": "",
            }
        if name.startswith("watch_job_"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "watch_status: terminal\nstatus: completed\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_run_json(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "add_planner_helper":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "role_class": "long_lived_interactive",
                    "lifecycle_state": "hidden",
                    "pane_id": "%3",
                    "apply": {"plan_class": "add_agent"},
                },
            }
        if name == "show_planner_helper_after_add":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"lifecycle_state": "hidden", "pane_id": "%3", "dispatch_disabled": False},
            }
        if name == "release_planner_helper_auto":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "requested_policy": "auto",
                    "resolved_policy": "park",
                    "lifecycle_state": "parked",
                    "dispatch_disabled": True,
                    "pane_id": "%3",
                    "apply": {"plan_class": "view_only_change"},
                },
            }
        if name == "show_planner_helper_after_park":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"lifecycle_state": "parked", "pane_id": "%3", "dispatch_disabled": True},
            }
        if name == "resume_planner_helper_hidden":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "lifecycle_state": "hidden",
                    "dispatch_disabled": False,
                    "pane_id": "%3",
                    "apply": {"plan_class": "view_only_change"},
                },
            }
        if name == "show_planner_helper_after_resume":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"lifecycle_state": "hidden", "pane_id": "%3", "dispatch_disabled": False},
            }
        if name == "add_reviewer_helper":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "role_class": "short_lived_execution",
                    "lifecycle_state": "hidden",
                    "pane_id": "%4",
                    "apply": {"plan_class": "add_agent"},
                },
            }
        if name == "release_reviewer_helper_auto":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "requested_policy": "auto",
                    "resolved_policy": "unload",
                    "lifecycle_state": "unloaded",
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_agents": {"reviewer_helper": "%4"},
                    },
                },
            }
        if name == "layout_after_reviewer_release":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 1,
                    "windows": [
                        {"name": "main", "agent_names": ["frontdesk"], "agents": [{"agent": "frontdesk", "pane_id": "%1"}]},
                        {
                            "name": "plan-orchestrate",
                            "agent_names": ["planner", "planner_helper"],
                            "agents": [
                                {"agent": "planner", "pane_id": "%2"},
                                {"agent": "planner_helper", "pane_id": "%3"},
                            ],
                        },
                    ],
                },
            }
        if name == "cleanup_planner_helper_unload":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "resolved_policy": "unload",
                    "lifecycle_state": "unloaded",
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_agents": {"planner_helper": "%3"},
                    },
                },
            }
        if name == "layout_after_cleanup":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 0,
                    "windows": [
                        {"name": "main", "agent_names": ["frontdesk"], "agents": [{"agent": "frontdesk", "pane_id": "%1"}]},
                        {
                            "name": "plan-orchestrate",
                            "agent_names": ["planner"],
                            "agents": [{"agent": "planner", "pane_id": "%2"}],
                        },
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module.layout_smoke, "_run", fake_run)
    monkeypatch.setattr(module.layout_smoke, "_run_json", fake_run_json)

    payload = module.run_lifecycle_policy_smoke(
        test_root=tmp_path,
        project_name="lifecycle",
        ccb_test=Path("ccb_test"),
        provider="fake",
        command_timeout_s=1,
        reset=True,
    )

    assert payload["dynamic_agent_lifecycle_smoke_status"] == "ok"
    assert payload["checks"]["planner_auto_policy_park"] is True
    assert payload["checks"]["parked_ask_rejected"] is True
    assert payload["checks"]["planner_resume_hidden"] is True
    assert payload["checks"]["reviewer_auto_policy_unload"] is True
    assert payload["checks"]["layout_clean_after_cleanup"] is True
    assert [name for name, _command in calls if name.startswith("release_")] == [
        "release_planner_helper_auto",
        "release_reviewer_helper_auto",
    ]


def test_main_passes_arguments_to_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return {"dynamic_agent_lifecycle_smoke_status": "ok", "commands": [], "checks": {}}

    monkeypatch.setattr(module, "run_lifecycle_policy_smoke", fake_runner)

    assert module.main(["--provider", "fake", "--command-timeout", "77", "--project-name", "life"]) == 0
    assert captured["provider"] == "fake"
    assert captured["project_name"] == "life"
    assert captured["command_timeout_s"] == 77


def test_tests_workflow_runs_dynamic_agent_lifecycle_fake_smoke() -> None:
    text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "Guard dynamic agent lifecycle smoke" in text
    assert "scripts/dynamic_agent_lifecycle_smoke.py" in text
    assert "ci-dynamic-agent-lifecycle" in text
    assert "matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'" in text
    assert "--provider fake" in text
    assert "--command-timeout 180" in text
    assert 'payload["dynamic_agent_lifecycle_smoke_status"] == "ok"' in text
    assert 'checks["planner_auto_policy_park"] is True' in text
    assert 'checks["planner_park_dispatch_disabled"] is True' in text
    assert 'checks["planner_park_view_only"] is True' in text
    assert 'checks["planner_pane_preserved_on_park"] is True' in text
    assert 'checks["parked_ask_rejected"] is True' in text
    assert 'checks["planner_resume_hidden"] is True' in text
    assert 'checks["planner_pane_preserved_on_resume"] is True' in text
    assert 'checks["planner_ask_after_resume_accepted"] is True' in text
    assert 'checks["reviewer_auto_policy_unload"] is True' in text
    assert 'checks["reviewer_remove_agent"] is True' in text
    assert 'checks["reviewer_pane_removed"] is True' in text
    assert 'checks["layout_clean_after_cleanup"] is True' in text
    assert 'checks["asks_terminal"] is True' in text
