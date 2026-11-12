from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dynamic_layout_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("dynamic_layout_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _observed_window(pane_ids: list[str], agent_names: list[str] | None = None) -> dict[str, object]:
    names = agent_names or [f"agent{index}" for index, _pane_id in enumerate(pane_ids, start=1)]
    return {
        "panes": [
            {
                "pane_id": pane_id,
                "ccb_agent": names[index],
                "pane_index": index,
                "pane_left": index * 81,
                "pane_top": 0,
                "pane_width": 80,
                "pane_height": 24,
            }
            for index, pane_id in enumerate(pane_ids)
        ]
    }


def _observed_fixed_columns(pane_ids: list[str], agent_names: list[str]) -> dict[str, object]:
    panes = []
    left_names = agent_names[0::2]
    right_names = agent_names[1::2]
    left_ids = pane_ids[0::2]
    right_ids = pane_ids[1::2]
    for row, (pane_id, agent) in enumerate(zip(left_ids, left_names)):
        panes.append(
            {
                "pane_id": pane_id,
                "ccb_agent": agent,
                "pane_index": len(panes),
                "pane_left": 25,
                "pane_top": row * 9,
                "pane_width": 47,
                "pane_height": 8,
            }
        )
    for row, (pane_id, agent) in enumerate(zip(right_ids, right_names)):
        panes.append(
            {
                "pane_id": pane_id,
                "ccb_agent": agent,
                "pane_index": len(panes),
                "pane_left": 73,
                "pane_top": row * 9,
                "pane_width": 47,
                "pane_height": 8,
            }
        )
    return {"panes": panes}


def test_build_multi_node_config_declares_explicit_windows_and_loop_profiles() -> None:
    module = _load_module()

    text = module.build_multi_node_config()

    assert 'entry_window = "main"' in text
    assert '[windows]' in text
    assert 'main = "orchestrator:fake"' in text
    assert '[loop.capacity]' in text
    assert 'max_nodes = 4' in text
    assert '[loop.role_profiles.worker]' in text
    assert 'role = "agentroles.coder"' in text
    assert '[loop.role_profiles.code_reviewer]' in text
    assert 'role = "agentroles.code_reviewer"' in text


def test_build_configs_accept_provider() -> None:
    module = _load_module()

    assert 'main = "orchestrator:codex"' in module.build_multi_node_config(provider="codex")
    assert 'provider = "codex"' in module.build_multi_node_config(provider="codex")
    assert 'main = "main:claude"' in module.build_same_window_config(provider="claude")
    assert 'main = "main:claude"' in module.build_single_agent_window_config(provider="claude")
    assert 'plan-orchestrate = "planner:gemini"' in module.build_window_class_config(provider="gemini")
    assert 'main = "frontdesk:qwen"' in module.build_resolve_preflight_config(provider="qwen")
    assert 'provider = "qwen"' in module.build_resolve_preflight_config(provider="qwen")


def test_build_resolve_preflight_config_can_use_static_filler_provider() -> None:
    module = _load_module()

    text = module.build_resolve_preflight_config(provider="codex", static_provider="fake")

    assert 'main = "frontdesk:fake"' in text
    assert 'plan-orchestrate = "p1:fake, p2:fake, p3:fake, p4:fake, p5:fake, p6:fake"' in text
    assert '[loop.role_profiles.worker]' in text
    assert 'provider = "codex"' in text


def test_build_window_class_config_declares_plan_orchestrate_window() -> None:
    module = _load_module()

    text = module.build_window_class_config()

    assert 'entry_window = "main"' in text
    assert '[windows]' in text
    assert 'main = "frontdesk:fake"' in text
    assert 'plan-orchestrate = "planner:fake"' in text


def test_build_resolve_preflight_config_declares_full_class_and_loop_profiles() -> None:
    module = _load_module()

    text = module.build_resolve_preflight_config()

    assert 'main = "frontdesk:fake"' in text
    assert 'plan-orchestrate = "p1:fake, p2:fake, p3:fake, p4:fake, p5:fake, p6:fake"' in text
    assert '[loop.capacity]' in text
    assert 'name_template = "loop-{loop_id}-{profile}-{index}"' in text
    assert '[loop.role_profiles.worker]' in text
    assert '[loop.role_profiles.code_reviewer]' in text
    assert 'thinking =' not in text


def test_prepare_projects_write_configs_and_roles(tmp_path: Path) -> None:
    module = _load_module()

    multi = module.prepare_multi_node_project(test_root=tmp_path, project_name="multi", reset=False)
    same = module.prepare_same_window_project(test_root=tmp_path, project_name="same", reset=False)
    single = module.prepare_single_agent_window_project(test_root=tmp_path, project_name="single", reset=False)
    window_class = module.prepare_window_class_project(test_root=tmp_path, project_name="window-class", reset=False)
    resolve = module.prepare_resolve_preflight_project(test_root=tmp_path, project_name="resolve", reset=False)

    multi_root = Path(multi["project_root"])
    same_root = Path(same["project_root"])
    single_root = Path(single["project_root"])
    window_class_root = Path(window_class["project_root"])
    resolve_root = Path(resolve["project_root"])
    assert (multi_root / ".ccb" / "ccb.config").read_text(encoding="utf-8").startswith("version = 2")
    assert (same_root / ".ccb" / "ccb.config").read_text(encoding="utf-8").startswith("version = 2")
    assert (single_root / ".ccb" / "ccb.config").read_text(encoding="utf-8").startswith("version = 2")
    assert 'plan-orchestrate = "planner:fake"' in (window_class_root / ".ccb" / "ccb.config").read_text(encoding="utf-8")
    assert 'plan-orchestrate = "p1:fake, p2:fake, p3:fake, p4:fake, p5:fake, p6:fake"' in (resolve_root / ".ccb" / "ccb.config").read_text(encoding="utf-8")
    assert (Path(multi["role_store"]) / "installed" / "agentroles.coder" / "current" / "role.toml").is_file()
    assert (Path(multi["role_store"]) / "installed" / "agentroles.code_reviewer" / "current" / "role.toml").is_file()
    assert (Path(same["role_store"]) / "installed" / "agentroles.general" / "current" / "role.toml").is_file()
    assert (Path(single["role_store"]) / "installed" / "agentroles.general" / "current" / "role.toml").is_file()
    assert (Path(window_class["role_store"]) / "installed" / "agentroles.general" / "current" / "role.toml").is_file()
    assert (Path(resolve["role_store"]) / "installed" / "agentroles.general" / "current" / "role.toml").is_file()
    assert (Path(resolve["role_store"]) / "installed" / "agentroles.coder" / "current" / "role.toml").is_file()
    assert (Path(resolve["role_store"]) / "installed" / "agentroles.code_reviewer" / "current" / "role.toml").is_file()


def test_prepare_only_can_generate_real_provider_window_class_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="real-provider-prepare",
        ccb_test=Path(__file__),
        provider="codex",
        flows=("window-class",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["window-class"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "frontdesk:codex"' in config.read_text(encoding="utf-8")
    assert payload["preflight"]["checks"]["provider"] == "codex"


def test_prepare_only_can_generate_resolve_preflight_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="resolve-prepare",
        ccb_test=Path(__file__),
        provider="claude",
        flows=("resolve-preflight",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["resolve-preflight"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'plan-orchestrate = "p1:claude, p2:claude, p3:claude, p4:claude, p5:claude, p6:claude"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_single_agent_window_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="single-window-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("single-agent-window",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["single-agent-window"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_move_agent_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="move-agent-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("move-agent",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["move-agent"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_move_shared_source_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="move-shared-source-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("move-shared-source",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["move-shared-source"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_arrange_window_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="arrange-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("arrange-window",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["arrange-window"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'plan-orchestrate = "planner:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_same_window_continuous_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="continuous-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("same-window-continuous",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["same-window-continuous"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_multi_window_continuous_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="multi-window-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("multi-window-continuous",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["multi-window-continuous"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_batch_release_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="batch-release-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("batch-release",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["batch-release"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_prepare_only_can_generate_batch_move_window_class_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="batch-move-window-class-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("batch-move-window-class",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["batch-move-window-class"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    text = config.read_text(encoding="utf-8")
    assert 'plan-orchestrate = "p1:fake, p2:fake, p3:fake, p4:fake, p5:fake"' in text


def test_prepare_only_can_generate_batch_move_execution_node_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="batch-move-execution-node-prepare",
        ccb_test=Path(__file__),
        provider="fake",
        flows=("batch-move-execution-node",),
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["flows"] == ["batch-move-execution-node"]
    assert len(payload["prepared"]) == 1
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    assert 'main = "main:fake"' in config.read_text(encoding="utf-8")


def test_same_window_continuous_flow_grows_to_six_and_shrinks_to_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    helper_panes = {f"helper{index}": f"%{index + 1}" for index in range(1, 6)}

    monkeypatch.setattr(
        module,
        "prepare_same_window_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("ask_helper3"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_helper3 target=helper3\n[CCB_ASYNC_SUBMITTED job=job_helper3 target=helper3]\n",
                "stderr": "",
            }
        if name.startswith("watch_job_"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "watch_status: terminal\nstatus: completed\n",
                "stderr": "",
            }
        if name.startswith("ask_main"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_main target=main\n[CCB_ASYNC_SUBMITTED job=job_main target=main]\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_run_json(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("add_helper"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_agent"}},
            }
        if name == "layout_after_grow_to_six":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 5,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main", *helper_panes],
                            "observed": _observed_fixed_columns(["%1", *helper_panes.values()], ["main", *helper_panes.keys()]),
                            "agents": [
                                {"agent": "main", "pane_id": "%1"},
                                *[
                                    {"agent": helper, "pane_id": pane}
                                    for helper, pane in helper_panes.items()
                                ],
                            ],
                        }
                    ],
                },
            }
        if name.startswith("remove_helper"):
            helper = name.removeprefix("remove_")
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_reflowed_windows": ["main"],
                        "namespace_removed_agents": {helper: helper_panes[helper]},
                    }
                },
            }
        if name == "layout_after_shrink_to_one":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 0,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window(["%1"], ["main"]),
                            "agents": [{"agent": "main", "pane_id": "%1"}],
                        }
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_same_window_continuous_flow(
        test_root=tmp_path,
        project_name="continuous",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["grew_to_six_order"] is True
    assert payload["checks"]["observed_grew_to_six_panes"] is True
    assert payload["checks"]["observed_grow_geometry"] is True
    assert payload["checks"]["observed_grow_indexes_contiguous"] is True
    assert payload["checks"]["observed_grow_min_width"] is True
    assert payload["checks"]["observed_grow_fixed_columns"] is True
    assert payload["checks"]["shrunk_to_one_order"] is True
    assert payload["checks"]["observed_shrunk_to_one_pane"] is True
    add_names = [name for name, _command in calls if name.startswith("add_helper")]
    remove_names = [name for name, _command in calls if name.startswith("remove_helper")]
    assert add_names == ["add_helper1", "add_helper2", "add_helper3", "add_helper4", "add_helper5"]
    assert remove_names == ["remove_helper5", "remove_helper4", "remove_helper3", "remove_helper2", "remove_helper1"]


def test_multi_window_continuous_flow_adds_and_removes_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    helpers = {"helper1": "%2", "helper2": "%3", "helper3": "%4"}

    monkeypatch.setattr(
        module,
        "prepare_same_window_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("ask_helper2"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_helper2 target=helper2\n[CCB_ASYNC_SUBMITTED job=job_helper2 target=helper2]\n",
                "stderr": "",
            }
        if name.startswith("watch_job_"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "watch_status: terminal\nstatus: completed\n",
                "stderr": "",
            }
        if name.startswith("ask_main"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_main target=main\n[CCB_ASYNC_SUBMITTED job=job_main target=main]\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_run_json(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("add_helper"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_window"}},
            }
        if name == "layout_after_add_windows":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 3,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window(["%1"], ["main"]),
                            "agents": [{"agent": "main", "pane_id": "%1"}],
                        },
                        *[
                            {
                                "name": f"review{index}",
                                "agent_names": [helper],
                                "observed": _observed_window([pane], [helper]),
                                "agents": [{"agent": helper, "pane_id": pane}],
                            }
                            for index, (helper, pane) in enumerate(helpers.items(), start=1)
                        ],
                    ],
                },
            }
        if name.startswith("remove_helper"):
            helper = name.removeprefix("remove_")
            window = f"review{helper[-1]}"
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_windows": [window],
                        "namespace_removed_agents": {helper: helpers[helper]},
                    }
                },
            }
        if name == "layout_after_remove_windows":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 0,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window(["%1"], ["main"]),
                            "agents": [{"agent": "main", "pane_id": "%1"}],
                        }
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_multi_window_continuous_flow(
        test_root=tmp_path,
        project_name="multi-window",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["grew_to_four_windows"] is True
    assert payload["checks"]["observed_grew_to_four_windows"] is True
    assert payload["checks"]["observed_window_geometry"] is True
    assert payload["checks"]["returned_to_main_window"] is True
    assert payload["checks"]["observed_returned_to_main_pane"] is True
    add_names = [name for name, _command in calls if name.startswith("add_helper")]
    remove_names = [name for name, _command in calls if name.startswith("remove_helper")]
    assert add_names == ["add_helper1_review1", "add_helper2_review2", "add_helper3_review3"]
    assert remove_names == ["remove_helper3", "remove_helper2", "remove_helper1"]


def test_batch_release_flow_removes_multiple_windows_in_one_transaction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    panes = {"main": "%1", "helper1": "%2", "helper2": "%3", "helper3": "%4"}

    monkeypatch.setattr(
        module,
        "prepare_same_window_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "ask_helper1_after_batch_release":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_helper1 target=helper1\n[CCB_ASYNC_SUBMITTED job=job_helper1 target=helper1]\n",
                "stderr": "",
            }
        if name == "ask_main_after_batch_release":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_main target=main\n[CCB_ASYNC_SUBMITTED job=job_main target=main]\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_run_json(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("add_helper"):
            plan_class = "add_agent" if name == "add_helper1_main" else "add_window"
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": plan_class}},
            }
        if name == "layout_before_batch_release":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 3,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main", "helper1"],
                            "observed": _observed_window([panes["main"], panes["helper1"]], ["main", "helper1"]),
                            "agents": [
                                {"agent": "main", "pane_id": panes["main"]},
                                {"agent": "helper1", "pane_id": panes["helper1"]},
                            ],
                        },
                        {
                            "name": "review2",
                            "agent_names": ["helper2"],
                            "observed": _observed_window([panes["helper2"]], ["helper2"]),
                            "agents": [{"agent": "helper2", "pane_id": panes["helper2"]}],
                        },
                        {
                            "name": "review3",
                            "agent_names": ["helper3"],
                            "observed": _observed_window([panes["helper3"]], ["helper3"]),
                            "agents": [{"agent": "helper3", "pane_id": panes["helper3"]}],
                        },
                    ],
                },
            }
        if name == "batch_remove_helper2_helper3":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "agent_lifecycle_status": "removed",
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_agents": {"helper2": panes["helper2"], "helper3": panes["helper3"]},
                        "namespace_removed_windows": ["review2", "review3"],
                    },
                },
            }
        if name == "layout_after_batch_release":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 1,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main", "helper1"],
                            "observed": _observed_window([panes["main"], panes["helper1"]], ["main", "helper1"]),
                            "agents": [
                                {"agent": "main", "pane_id": panes["main"]},
                                {"agent": "helper1", "pane_id": panes["helper1"]},
                            ],
                        }
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_batch_release_flow(
        test_root=tmp_path,
        project_name="batch-release",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["batch_remove_agent_plan"] is True
    assert payload["checks"]["batch_removed_windows"] is True
    assert payload["checks"]["survivor_panes_preserved"] is True
    assert payload["checks"]["survivor_ask_accepted"] is True
    batch_commands = [command for name, command in calls if name == "batch_remove_helper2_helper3"]
    assert batch_commands == [
        "ccb_test --project "
        f"{project_root} agent remove --agents helper2,helper3 --policy unload --idle-only --json"
    ]


def test_batch_move_window_class_flow_splits_targets_by_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    panes = {
        "frontdesk": "%1",
        "p1": "%2",
        "p2": "%3",
        "p3": "%4",
        "p4": "%5",
        "p5": "%6",
        "zeta": "%7",
        "alpha": "%8",
    }

    monkeypatch.setattr(
        module,
        "prepare_batch_move_window_class_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "ask_zeta_after_batch_move_window_class":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_zeta target=zeta\n[CCB_ASYNC_SUBMITTED job=job_zeta target=zeta]\n",
                "stderr": "",
            }
        if name == "ask_alpha_after_batch_move_window_class":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_alpha target=alpha\n[CCB_ASYNC_SUBMITTED job=job_alpha target=alpha]\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_run_json(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "add_zeta_to_review":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_window"}},
            }
        if name == "add_alpha_to_review":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_agent"}},
            }
        if name == "layout_before_batch_move_window_class":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 2,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["frontdesk"],
                            "observed": _observed_window([panes["frontdesk"]], ["frontdesk"]),
                            "agents": [{"agent": "frontdesk", "pane_id": panes["frontdesk"]}],
                        },
                        {
                            "name": "plan-orchestrate",
                            "agent_names": ["p1", "p2", "p3", "p4", "p5"],
                            "observed": _observed_window(
                                [panes["p1"], panes["p2"], panes["p3"], panes["p4"], panes["p5"]],
                                ["p1", "p2", "p3", "p4", "p5"],
                            ),
                            "agents": [
                                {"agent": agent, "pane_id": panes[agent]}
                                for agent in ("p1", "p2", "p3", "p4", "p5")
                            ],
                        },
                        {
                            "name": "review",
                            "agent_names": ["zeta", "alpha"],
                            "observed": _observed_window([panes["zeta"], panes["alpha"]], ["zeta", "alpha"]),
                            "agents": [
                                {"agent": "zeta", "pane_id": panes["zeta"]},
                                {"agent": "alpha", "pane_id": panes["alpha"]},
                            ],
                        },
                    ],
                },
            }
        if name == "move_zeta_alpha_to_window_class":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "agent_lifecycle_status": "active",
                    "target_window_names": ["plan-orchestrate", "plan-orchestrate-2"],
                    "apply": {
                        "plan_class": "move_agent",
                        "namespace_moved_agents": {"zeta": panes["zeta"], "alpha": panes["alpha"]},
                        "namespace_moved_agent_windows": {
                            "zeta": "plan-orchestrate",
                            "alpha": "plan-orchestrate-2",
                        },
                        "namespace_removed_windows": ["review"],
                    },
                },
            }
        if name == "layout_after_batch_move_window_class":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 2,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["frontdesk"],
                            "observed": _observed_window([panes["frontdesk"]], ["frontdesk"]),
                            "agents": [{"agent": "frontdesk", "pane_id": panes["frontdesk"]}],
                        },
                        {
                            "name": "plan-orchestrate",
                            "agent_names": ["p1", "p2", "p3", "p4", "p5", "zeta"],
                            "observed": _observed_window(
                                [panes["p1"], panes["p2"], panes["p3"], panes["p4"], panes["p5"], panes["zeta"]],
                                ["p1", "p2", "p3", "p4", "p5", "zeta"],
                            ),
                            "agents": [
                                {"agent": agent, "pane_id": panes[agent]}
                                for agent in ("p1", "p2", "p3", "p4", "p5", "zeta")
                            ],
                        },
                        {
                            "name": "plan-orchestrate-2",
                            "agent_names": ["alpha"],
                            "observed": _observed_window([panes["alpha"]], ["alpha"]),
                            "agents": [{"agent": "alpha", "pane_id": panes["alpha"]}],
                        },
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_batch_move_window_class_flow(
        test_root=tmp_path,
        project_name="batch-move-window-class",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["move_target_windows"] is True
    assert payload["checks"]["moved_agent_panes_match"] is True
    assert payload["checks"]["removed_review_window"] is True
    assert payload["checks"]["after_windows"] is True
    assert payload["checks"]["zeta_ask_accepted"] is True
    move_commands = [command for name, command in calls if name == "move_zeta_alpha_to_window_class"]
    assert move_commands == [
        "ccb_test --project "
        f"{project_root} agent move --agents zeta,alpha --window-class plan-orchestrate "
        "--reason dynamic layout batch window-class move smoke --json"
    ]


def test_batch_move_execution_node_flow_moves_pair_to_node_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    panes = {"main": "%1", "worker": "%2", "checker": "%3"}

    monkeypatch.setattr(
        module,
        "prepare_same_window_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "ask_worker_after_batch_move_execution_node":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_worker target=worker\n[CCB_ASYNC_SUBMITTED job=job_worker target=worker]\n",
                "stderr": "",
            }
        if name == "ask_checker_after_batch_move_execution_node":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_checker target=checker\n[CCB_ASYNC_SUBMITTED job=job_checker target=checker]\n",
                "stderr": "",
            }
        return {"name": name, "returncode": 0, "stdout": "ok\n", "stderr": ""}

    def fake_run_json(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "add_worker_to_review":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_window"}},
            }
        if name == "add_checker_to_review":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_agent"}},
            }
        if name == "layout_before_batch_move_execution_node":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 2,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window([panes["main"]], ["main"]),
                            "agents": [{"agent": "main", "pane_id": panes["main"]}],
                        },
                        {
                            "name": "review",
                            "agent_names": ["worker", "checker"],
                            "observed": _observed_window([panes["worker"], panes["checker"]], ["worker", "checker"]),
                            "agents": [
                                {"agent": "worker", "pane_id": panes["worker"]},
                                {"agent": "checker", "pane_id": panes["checker"]},
                            ],
                        },
                    ],
                },
            }
        if name == "move_worker_checker_to_execution_node":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "agent_lifecycle_status": "active",
                    "target_window_name": "node-round1-node1",
                    "target_window_names": ["node-round1-node1"],
                    "apply": {
                        "plan_class": "move_agent",
                        "namespace_moved_agents": {"worker": panes["worker"], "checker": panes["checker"]},
                        "namespace_moved_agent_windows": {
                            "worker": "node-round1-node1",
                            "checker": "node-round1-node1",
                        },
                        "namespace_removed_windows": ["review"],
                    },
                },
            }
        if name == "layout_after_batch_move_execution_node":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 2,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window([panes["main"]], ["main"]),
                            "agents": [{"agent": "main", "pane_id": panes["main"]}],
                        },
                        {
                            "name": "node-round1-node1",
                            "agent_names": ["worker", "checker"],
                            "observed": _observed_window([panes["worker"], panes["checker"]], ["worker", "checker"]),
                            "agents": [
                                {"agent": "worker", "pane_id": panes["worker"]},
                                {"agent": "checker", "pane_id": panes["checker"]},
                            ],
                        },
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_batch_move_execution_node_flow(
        test_root=tmp_path,
        project_name="batch-move-execution-node",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["move_target_window"] is True
    assert payload["checks"]["moved_agent_panes_match"] is True
    assert payload["checks"]["removed_review_window"] is True
    assert payload["checks"]["after_windows"] is True
    assert payload["checks"]["worker_ask_accepted"] is True
    move_commands = [command for name, command in calls if name == "move_worker_checker_to_execution_node"]
    assert move_commands == [
        "ccb_test --project "
        f"{project_root} agent move --agents worker,checker --loop-id round1 --node-id node1 "
        "--reason dynamic layout batch execution-node move smoke --json"
    ]


def test_move_agent_flow_moves_helper_to_new_window_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module,
        "prepare_same_window_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name == "ask_helper_before_move":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_before target=helper\n[CCB_ASYNC_SUBMITTED job=job_before target=helper]\n",
                "stderr": "",
            }
        if name == "ask_helper_after_move":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_after target=helper\n[CCB_ASYNC_SUBMITTED job=job_after target=helper]\n",
                "stderr": "",
            }
        if name == "ask_helper_after_return":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_return target=helper\n[CCB_ASYNC_SUBMITTED job=job_return target=helper]\n",
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
        if name == "add_move_helper_to_main":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_agent"}},
            }
        if name == "layout_before_move_agent":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 1,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main", "helper"],
                            "observed": _observed_window(["%1", "%2"], ["main", "helper"]),
                            "agents": [
                                {"agent": "main", "pane_id": "%1"},
                                {"agent": "helper", "pane_id": "%2"},
                            ],
                        }
                    ],
                },
            }
        if name == "move_helper_to_review_window":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "move_agent",
                        "apply_status": "applied",
                        "namespace_moved_agents": {"helper": "%2"},
                        "namespace_moved_agent_windows": {"helper": "review"},
                        "namespace_reflowed_windows": ["main", "review"],
                    }
                },
            }
        if name == "layout_after_move_agent":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 1,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window(["%1"], ["main"]),
                            "agents": [{"agent": "main", "pane_id": "%1"}],
                        },
                        {
                            "name": "review",
                            "agent_names": ["helper"],
                            "observed": _observed_window(["%2"], ["helper"]),
                            "agents": [{"agent": "helper", "pane_id": "%2"}],
                        },
                    ],
                },
            }
        if name == "move_helper_back_to_main":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "move_agent",
                        "apply_status": "applied",
                        "namespace_moved_agents": {"helper": "%2"},
                        "namespace_moved_agent_windows": {"helper": "main"},
                        "namespace_removed_windows": ["review"],
                        "namespace_reflowed_windows": ["main"],
                    }
                },
            }
        if name == "layout_after_move_agent_return":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 1,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main", "helper"],
                            "observed": _observed_window(["%1", "%2"], ["main", "helper"]),
                            "agents": [
                                {"agent": "main", "pane_id": "%1"},
                                {"agent": "helper", "pane_id": "%2"},
                            ],
                        }
                    ],
                },
            }
        if name == "remove_moved_helper":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_agents": {"helper": "%2"},
                        "namespace_removed_windows": [],
                    }
                },
            }
        if name == "layout_after_move_cleanup":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 0,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["main"],
                            "observed": _observed_window(["%1"], ["main"]),
                            "agents": [{"agent": "main", "pane_id": "%1"}],
                        }
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_move_agent_flow(
        test_root=tmp_path,
        project_name="move-agent",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["pre_move_ask_accepted"] is True
    assert payload["checks"]["post_move_ask_accepted"] is True
    assert payload["checks"]["move_preserved_helper_pane"] is True
    assert payload["checks"]["move_window_evidence"] is True
    assert payload["checks"]["return_ask_accepted"] is True
    assert payload["checks"]["return_preserved_helper_pane"] is True
    assert payload["checks"]["return_removed_review_window"] is True
    assert payload["checks"]["release_kept_main_window"] is True
    assert payload["checks"]["dynamic_agents_cleaned"] is True
    assert [name for name, _command in calls if name.startswith("watch_job_")] == [
        "watch_job_before",
        "watch_job_after",
        "watch_job_return",
    ]


def test_move_shared_source_flow_keeps_remaining_source_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module,
        "prepare_same_window_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def layout_payload(windows: list[tuple[str, list[tuple[str, str]]]], *, dynamic_count: int) -> dict[str, object]:
        return {
            "dynamic_agent_count": dynamic_count,
            "windows": [
                {
                    "name": name,
                    "agent_names": [agent for agent, _pane in agents],
                    "observed": _observed_window([pane for _agent, pane in agents], [agent for agent, _pane in agents]),
                    "agents": [{"agent": agent, "pane_id": pane} for agent, pane in agents],
                }
                for name, agents in windows
            ],
        }

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        jobs = {
            "ask_helper2_before_shared_source_move": "job_before",
            "ask_helper1_after_shared_source_move": "job_after_moved",
            "ask_helper2_after_shared_source_move": "job_after_stay",
            "ask_helper1_after_shared_source_return": "job_return",
        }
        if name in jobs:
            target = "helper1" if "helper1" in name else "helper2"
            job_id = jobs[name]
            return {
                "name": name,
                "returncode": 0,
                "stdout": f"accepted job={job_id} target={target}\n[CCB_ASYNC_SUBMITTED job={job_id} target={target}]\n",
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
        if name == "add_helper1_to_review":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_window"}},
            }
        if name == "add_helper2_to_review":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_agent"}},
            }
        if name == "layout_before_shared_source_move":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": layout_payload(
                    [("main", [("main", "%1")]), ("review", [("helper1", "%2"), ("helper2", "%3")])],
                    dynamic_count=2,
                ),
            }
        if name == "move_helper1_to_main_from_shared_source":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "move_agent",
                        "apply_status": "applied",
                        "namespace_moved_agents": {"helper1": "%2"},
                        "namespace_moved_agent_windows": {"helper1": "main"},
                        "namespace_reflowed_windows": ["main", "review"],
                        "namespace_removed_windows": [],
                    }
                },
            }
        if name == "layout_after_shared_source_move":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": layout_payload(
                    [("main", [("main", "%1"), ("helper1", "%2")]), ("review", [("helper2", "%3")])],
                    dynamic_count=2,
                ),
            }
        if name == "move_helper1_back_to_shared_source":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "move_agent",
                        "apply_status": "applied",
                        "namespace_moved_agents": {"helper1": "%2"},
                        "namespace_moved_agent_windows": {"helper1": "review"},
                        "namespace_reflowed_windows": ["main", "review"],
                        "namespace_removed_windows": [],
                    }
                },
            }
        if name == "layout_after_shared_source_return":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": layout_payload(
                    [("main", [("main", "%1")]), ("review", [("helper2", "%3"), ("helper1", "%2")])],
                    dynamic_count=2,
                ),
            }
        if name == "remove_shared_source_helper1":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_agents": {"helper1": "%2"},
                        "namespace_removed_windows": [],
                    }
                },
            }
        if name == "remove_shared_source_helper2":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "apply": {
                        "plan_class": "remove_agent",
                        "namespace_removed_agents": {"helper2": "%3"},
                        "namespace_removed_windows": ["review"],
                    }
                },
            }
        if name == "layout_after_shared_source_cleanup":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": layout_payload([("main", [("main", "%1")])], dynamic_count=0),
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_move_shared_source_flow(
        test_root=tmp_path,
        project_name="move-shared-source",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["before_move_order"] is True
    assert payload["checks"]["move_source_window_retained"] is True
    assert payload["checks"]["move_preserved_stay_pane"] is True
    assert payload["checks"]["after_move_order"] is True
    assert payload["checks"]["return_kept_review_window"] is True
    assert payload["checks"]["after_return_order"] is True
    assert payload["checks"]["final_release_removed_review_window"] is True
    assert payload["checks"]["dynamic_agents_cleaned"] is True
    assert [name for name, _command in calls if name.startswith("watch_job_")] == [
        "watch_job_before",
        "watch_job_after_moved",
        "watch_job_after_stay",
        "watch_job_return",
    ]


def test_arrange_window_flow_disturbs_and_restores_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    helpers = tuple(f"planner_helper{index}" for index in range(1, 5))
    plan_agents = ("planner", *helpers)
    pane_ids = ["%2", "%3", "%4", "%5", "%6"]
    pane_map = dict(zip(plan_agents, pane_ids))

    monkeypatch.setattr(
        module,
        "prepare_window_class_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def plan_window_payload(*, observed: dict[str, object]) -> dict[str, object]:
        return {
            "dynamic_agent_count": len(helpers),
            "namespace": {
                "tmux_socket_path": str(tmp_path / "tmux.sock"),
                "tmux_session_name": "ccb-test",
            },
            "windows": [
                {
                    "name": "main",
                    "agent_names": ["frontdesk"],
                    "observed": _observed_window(["%1"], ["frontdesk"]),
                    "agents": [{"agent": "frontdesk", "pane_id": "%1"}],
                },
                {
                    "name": "plan-orchestrate",
                    "agent_names": list(plan_agents),
                    "observed": observed,
                    "agents": [
                        {"agent": agent, "pane_id": pane_map[agent]}
                        for agent in plan_agents
                    ],
                },
            ],
        }

    fixed_plan = plan_window_payload(observed=_observed_fixed_columns(pane_ids, list(plan_agents)))
    horizontal_plan = plan_window_payload(observed=_observed_window(pane_ids, list(plan_agents)))

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("ask_planner_helper3"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_helper3 target=planner_helper3\n[CCB_ASYNC_SUBMITTED job=job_helper3 target=planner_helper3]\n",
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
        if name.startswith("add_planner_helper"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "add_agent"}},
            }
        if name == "layout_before_arrange_disturb":
            return {"name": name, "returncode": 0, "stdout": "{}\n", "stderr": "", "payload": fixed_plan}
        if name == "layout_after_arrange_disturb":
            return {"name": name, "returncode": 0, "stdout": "{}\n", "stderr": "", "payload": horizontal_plan}
        if name == "arrange_plan_orchestrate":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "arrange_status": "ok",
                    "layout_status": "ok",
                    "reflowed_windows": ["plan-orchestrate"],
                    "reflow_errors": {},
                    **fixed_plan,
                },
            }
        if name == "layout_after_arrange":
            return {"name": name, "returncode": 0, "stdout": "{}\n", "stderr": "", "payload": fixed_plan}
        if name.startswith("remove_planner_helper"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": "remove_agent"}},
            }
        if name == "layout_after_arrange_cleanup":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 0,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["frontdesk"],
                            "observed": _observed_window(["%1"], ["frontdesk"]),
                            "agents": [{"agent": "frontdesk", "pane_id": "%1"}],
                        },
                        {
                            "name": "plan-orchestrate",
                            "agent_names": ["planner"],
                            "observed": _observed_window(["%2"], ["planner"]),
                            "agents": [{"agent": "planner", "pane_id": "%2"}],
                        },
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_arrange_window_flow(
        test_root=tmp_path,
        project_name="arrange-window",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["disturb_made_non_fixed"] is True
    assert payload["checks"]["arrange_status_ok"] is True
    assert payload["checks"]["arrange_fixed_columns"] is True
    assert payload["checks"]["pane_ids_preserved"] is True
    assert payload["checks"]["after_release_static_windows"] is True
    assert ("disturb_plan_orchestrate_even_horizontal", f"tmux -S {tmp_path / 'tmux.sock'} select-layout -t ccb-test:plan-orchestrate even-horizontal") in calls
    assert [name for name, _command in calls if name.startswith("remove_planner_helper")] == [
        "remove_planner_helper4",
        "remove_planner_helper3",
        "remove_planner_helper2",
        "remove_planner_helper1",
    ]


def test_window_class_continuous_flow_grows_to_overflow_page_and_cleans_up(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    project_root = tmp_path / "project"
    role_store = tmp_path / "roles"
    calls: list[tuple[str, str]] = []
    helpers = tuple(f"planner_helper{index}" for index in range(1, 8))
    helper_panes = {helper: f"%{index + 2}" for index, helper in enumerate(helpers, start=1)}

    monkeypatch.setattr(
        module,
        "prepare_window_class_project",
        lambda **_kwargs: {"project_root": str(project_root), "role_store": str(role_store)},
    )

    def fake_run(name, command, **_kwargs):
        calls.append((name, " ".join(str(item) for item in command)))
        if name.startswith("ask_planner_helper7"):
            return {
                "name": name,
                "returncode": 0,
                "stdout": "accepted job=job_helper7 target=planner_helper7\n[CCB_ASYNC_SUBMITTED job=job_helper7 target=planner_helper7]\n",
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
        if name.startswith("add_planner_helper"):
            helper = name.removeprefix("add_")
            index = helpers.index(helper)
            plan_class = "add_window" if index == 5 else "add_agent"
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {"apply": {"plan_class": plan_class}},
            }
        if name == "layout_after_window_class_grow_to_eight":
            page1_agents = ["planner", *helpers[:5]]
            page2_agents = list(helpers[5:])
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 7,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["frontdesk"],
                            "observed": _observed_window(["%1"], ["frontdesk"]),
                            "agents": [{"agent": "frontdesk", "pane_id": "%1"}],
                        },
                        {
                            "name": "plan-orchestrate",
                            "agent_names": page1_agents,
                            "observed": _observed_fixed_columns(
                                ["%2", *[helper_panes[helper] for helper in helpers[:5]]],
                                page1_agents,
                            ),
                            "agents": [
                                {"agent": "planner", "pane_id": "%2"},
                                *[
                                    {"agent": helper, "pane_id": helper_panes[helper]}
                                    for helper in helpers[:5]
                                ],
                            ],
                        },
                        {
                            "name": "plan-orchestrate-2",
                            "agent_names": page2_agents,
                            "observed": _observed_fixed_columns(
                                [helper_panes[helper] for helper in helpers[5:]],
                                page2_agents,
                            ),
                            "agents": [
                                {"agent": helper, "pane_id": helper_panes[helper]}
                                for helper in helpers[5:]
                            ],
                        },
                    ],
                },
            }
        if name.startswith("remove_planner_helper"):
            helper = name.removeprefix("remove_")
            removed_windows = ["plan-orchestrate-2"] if helper == "planner_helper6" else []
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
                        "namespace_removed_windows": removed_windows,
                        "namespace_removed_agents": {helper: helper_panes[helper]},
                    },
                },
            }
        if name == "layout_after_window_class_shrink_to_planner":
            return {
                "name": name,
                "returncode": 0,
                "stdout": "{}\n",
                "stderr": "",
                "payload": {
                    "dynamic_agent_count": 0,
                    "windows": [
                        {
                            "name": "main",
                            "agent_names": ["frontdesk"],
                            "observed": _observed_window(["%1"], ["frontdesk"]),
                            "agents": [{"agent": "frontdesk", "pane_id": "%1"}],
                        },
                        {
                            "name": "plan-orchestrate",
                            "agent_names": ["planner"],
                            "observed": _observed_window(["%2"], ["planner"]),
                            "agents": [{"agent": "planner", "pane_id": "%2"}],
                        },
                    ],
                },
            }
        raise AssertionError(f"unexpected json command {name}")

    monkeypatch.setattr(module, "_run", fake_run)
    monkeypatch.setattr(module, "_run_json", fake_run_json)

    payload = module._run_window_class_continuous_flow(
        test_root=tmp_path,
        project_name="window-class-continuous",
        provider="fake",
        ccb_test=Path("ccb_test"),
        provider_home=tmp_path / "home",
        command_timeout_s=1,
        reset=True,
        keep_running=False,
    )

    assert payload["flow_status"] == "ok"
    assert payload["checks"]["add_plan_sequence"] is True
    assert payload["checks"]["page1_order"] is True
    assert payload["checks"]["page2_order"] is True
    assert payload["checks"]["page1_observed_fixed_columns"] is True
    assert payload["checks"]["page2_observed_fixed_columns"] is True
    assert payload["checks"]["page2_removed_when_empty"] is True
    assert payload["checks"]["after_page2_removed"] is True
    add_names = [name for name, _command in calls if name.startswith("add_planner_helper")]
    remove_names = [name for name, _command in calls if name.startswith("remove_planner_helper")]
    assert add_names == [f"add_{helper}" for helper in helpers]
    assert remove_names == [f"remove_{helper}" for helper in reversed(helpers)]


def test_prepare_only_can_generate_light_real_provider_resolve_preflight_project(tmp_path: Path) -> None:
    module = _load_module()

    payload = module.run_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="resolve-light",
        ccb_test=Path(__file__),
        provider="codex",
        flows=("resolve-preflight",),
        resolve_preflight_static_provider="fake",
        prepare_only=True,
        reset=True,
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert payload["resolve_preflight_static_provider"] == "fake"
    config = Path(payload["prepared"][0]["project_root"]) / ".ccb" / "ccb.config"
    text = config.read_text(encoding="utf-8")
    assert 'main = "frontdesk:fake"' in text
    assert 'plan-orchestrate = "p1:fake, p2:fake, p3:fake, p4:fake, p5:fake, p6:fake"' in text
    assert 'provider = "codex"' in text


def test_real_provider_run_requires_explicit_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv(module.REAL_RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match=module.REAL_RUN_ENV):
        module.run_dynamic_layout_smoke(
            test_root=tmp_path,
            project_prefix="real-provider-run",
            ccb_test=Path(__file__),
            provider="codex",
            flows=("window-class",),
        )


def test_real_home_mode_ignores_isolated_home_when_override_is_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    isolated_home = tmp_path / "source_home"
    real_home = tmp_path / "real_home"
    monkeypatch.setenv("HOME", str(isolated_home))
    monkeypatch.setenv("CCB_REAL_HOME", str(real_home))

    assert module._provider_home(test_root=tmp_path, mode="real-home") == real_home


def test_main_passes_command_timeout_to_runner(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return {"dynamic_layout_smoke_status": "prepared"}

    monkeypatch.setattr(module, "run_dynamic_layout_smoke", fake_runner)

    assert module.main(["--command-timeout", "123", "--prepare-only", "--resolve-preflight-static-provider", "fake"]) == 0
    assert captured["command_timeout_s"] == 123
    assert captured["resolve_preflight_static_provider"] == "fake"


def test_main_writes_output_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    output_path = tmp_path / "artifacts" / "dynamic-layout.json"

    def fake_runner(**_kwargs):
        return {
            "dynamic_layout_smoke_status": "ok",
            "checks": {"same_window_continuous_1_to_6_to_1": True},
            "results": [],
        }

    monkeypatch.setattr(module, "run_dynamic_layout_smoke", fake_runner)

    assert module.main(["--flow", "same-window-continuous", "--output", str(output_path)]) == 0
    assert output_path.is_file()
    assert '"dynamic_layout_smoke_status": "ok"' in output_path.read_text(encoding="utf-8")


def test_main_runs_repeated_providers_as_matrix(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    calls = []

    def fake_runner(**kwargs):
        calls.append(kwargs)
        return {
            "dynamic_layout_smoke_status": "ok",
            "provider": kwargs["provider"],
            "flows": list(kwargs["flows"]),
            "checks": {"window_class_middle_release": True},
            "results": [],
        }

    monkeypatch.setattr(module, "run_dynamic_layout_smoke", fake_runner)

    assert module.main(["--provider", "codex", "--provider", "claude", "--flow", "window-class"]) == 0
    assert [(call["provider"], call["project_prefix"]) for call in calls] == [
        ("codex", "dynamic-layout-smoke-codex"),
        ("claude", "dynamic-layout-smoke-claude"),
    ]
    assert calls[0]["flows"] == ("window-class",)


def test_provider_matrix_payload_compacts_provider_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()

    def fake_runner(**kwargs):
        return {
            "dynamic_layout_smoke_status": "ok",
            "provider": kwargs["provider"],
            "provider_home_mode": kwargs["provider_home_mode"],
            "flows": ["window-class"],
            "checks": {"window_class_middle_release": True},
            "results": [],
        }

    monkeypatch.setattr(module, "run_dynamic_layout_smoke", fake_runner)

    payload = module.run_dynamic_layout_provider_matrix(
        test_root=tmp_path,
        project_prefix="matrix",
        ccb_test=Path(__file__),
        providers=("codex", "claude", "codex"),
        flows=("window-class",),
    )
    compact = module.compact_smoke_payload(payload)

    assert payload["dynamic_layout_smoke_status"] == "ok"
    assert payload["providers"] == ["codex", "claude"]
    assert compact["provider_results"][0]["provider"] == "codex"
    assert compact["provider_results"][1]["provider"] == "claude"


def test_watch_submitted_jobs_uses_converged_watch_with_smoke_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    captured = {}

    def fake_run(name, command, **kwargs):
        captured.update({"name": name, "command": command, **kwargs})
        return {"name": name, "returncode": 0, "stdout": "watch_status: terminal\n", "stderr": ""}

    monkeypatch.setattr(module, "_run", fake_run)

    results = module._watch_submitted_jobs(
        ccb_test=Path("ccb_test"),
        project_root=tmp_path / "project",
        test_root=tmp_path,
        env={"CCB_WATCH_TIMEOUT_S": "10", "CCB_WATCH_POLL_INTERVAL_S": "0.1"},
        asks=({"stdout": "accepted job=job_slow target=helper\n"},),
        timeout=240,
    )

    assert len(results) == 1
    assert captured["name"] == "watch_job_slow"
    assert captured["command"] == [
        "ccb_test",
        "--project",
        str(tmp_path / "project"),
        "pend",
        "--watch",
        "job_slow",
    ]
    assert captured["env"]["CCB_WATCH_TIMEOUT_S"] == "240"
    assert captured["env"]["CCB_WATCH_POLL_INTERVAL_S"] == "0.1"
    assert captured["timeout"] == 245


def test_run_records_timeout_without_raising(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()

    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["ccb"], timeout=1, output="partial out", stderr="partial err")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module._run("slow", ["ccb"], cwd=tmp_path, env={}, timeout=1)

    assert result["returncode"] is None
    assert result["timeout"] is True
    assert result["stdout"] == "partial out"
    assert result["stderr"] == "partial err"
    compact = module._compact_command(result)
    assert compact["timeout"] is True


def test_payload_helpers_extract_window_agents_and_panes() -> None:
    module = _load_module()
    result = {
        "payload": {
            "windows": [
                {
                    "name": "main",
                    "agent_names": ["main", "helper1"],
                    "agents": [
                        {"agent": "main", "pane_id": "%1"},
                        {"agent": "helper1", "pane_id": "%2"},
                    ],
                }
            ]
        }
    }

    assert module._window_agents(result) == {"main": ["main", "helper1"]}
    assert module._agent_panes(result) == {"main": "%1", "helper1": "%2"}


def test_fixed_columns_accept_uneven_five_pane_rows() -> None:
    module = _load_module()
    result = {
        "payload": {
            "windows": [
                {
                    "name": "plan-orchestrate",
                    "agent_names": ["planner", "helper1", "helper2", "helper3", "helper4"],
                    "observed": {
                        "panes": [
                            {"pane_id": "%1", "ccb_agent": "planner", "pane_left": 25, "pane_top": 1, "pane_width": 66, "pane_height": 15},
                            {"pane_id": "%3", "ccb_agent": "helper2", "pane_left": 25, "pane_top": 17, "pane_width": 66, "pane_height": 15},
                            {"pane_id": "%5", "ccb_agent": "helper4", "pane_left": 25, "pane_top": 33, "pane_width": 66, "pane_height": 15},
                            {"pane_id": "%2", "ccb_agent": "helper1", "pane_left": 94, "pane_top": 1, "pane_width": 66, "pane_height": 23},
                            {"pane_id": "%4", "ccb_agent": "helper3", "pane_left": 94, "pane_top": 25, "pane_width": 66, "pane_height": 23},
                        ]
                    },
                }
            ]
        }
    }

    assert module._observed_panes_match_fixed_columns(
        result,
        "plan-orchestrate",
        ("planner", "helper1", "helper2", "helper3", "helper4"),
    )


def test_compact_payload_keeps_checks_and_window_summary_without_full_stdout() -> None:
    module = _load_module()
    payload = {
        "dynamic_layout_smoke_status": "ok",
        "checks": {"flow": True},
        "results": [
            {
                "flow": "flow",
                "flow_status": "ok",
                "checks": {"ok": True},
                "commands": [
                    {
                        "name": "layout",
                        "returncode": 0,
                        "stdout": "line1\nline2\nline3\nline4\n",
                        "payload": {
                            "action": "remove",
                            "layout_status": "ok",
                            "loop_agent_count": 2,
                            "resolved_window_name": "node-round1-node1",
                            "will_create_window": True,
                            "apply": {
                                "plan_class": "remove_agent",
                                "apply_status": "applied",
                                "namespace_removed_agents": {"helper": "%2"},
                                "namespace_removed_windows": ["review"],
                                "namespace_moved_agents": {"moved": "%3"},
                                "namespace_moved_agent_windows": {"moved": "review"},
                            },
                            "windows": [
                                {
                                    "name": "node-round1-node1",
                                    "agent_names": ["worker", "checker"],
                                    "pane_count": 2,
                                    "runtime_pane_count": 2,
                                    "observed": {
                                        "panes": [
                                            {"pane_id": "%1", "pane_index": 0, "pane_left": 0, "pane_top": 0, "pane_width": 80, "pane_height": 24},
                                            {"pane_id": "%2", "pane_index": 1, "pane_left": 81, "pane_top": 0, "pane_width": 80, "pane_height": 24},
                                        ],
                                    },
                                    "large": "ignored",
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }

    compact = module.compact_smoke_payload(payload)

    assert compact["dynamic_layout_smoke_status"] == "ok"
    command = compact["results"][0]["commands"][0]
    assert command["stdout_excerpt"] == ["line1", "line2", "line3"]
    assert command["payload"] == {
        "action": "remove",
        "layout_status": "ok",
        "loop_agent_count": 2,
        "resolved_window_name": "node-round1-node1",
        "will_create_window": True,
        "apply": {
            "plan_class": "remove_agent",
            "apply_status": "applied",
            "namespace_removed_agents": {"helper": "%2"},
            "namespace_removed_windows": ["review"],
            "namespace_moved_agents": {"moved": "%3"},
            "namespace_moved_agent_windows": {"moved": "review"},
        },
        "windows": [
            {
                "name": "node-round1-node1",
                "agents": ["worker", "checker"],
                "pane_count": 2,
                "runtime_pane_count": 2,
                "observed_panes": [
                    {"pane_id": "%1", "pane_index": 0, "pane_left": 0, "pane_top": 0, "pane_width": 80, "pane_height": 24},
                    {"pane_id": "%2", "pane_index": 1, "pane_left": 81, "pane_top": 0, "pane_width": 80, "pane_height": 24},
                ],
            }
        ],
    }


def test_tests_workflow_runs_core_dynamic_layout_fake_smoke() -> None:
    text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "Guard core dynamic layout smoke" in text
    assert "scripts/guarded_core_dynamic_layout_smoke.py" in text
    assert "ci-core-dynamic-layout" in text
    assert "matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'" in text
    assert "--provider fake" in text
    assert 'payload["dynamic_layout_smoke_status"] == "ok"' in text
    assert '"mixed-move-add",' in text
    assert '"batch-move-window-class",' in text
    assert '"resolve-preflight",' in text
    step = text.split("Guard core dynamic layout smoke", 1)[1].split("Guard dynamic agent lifecycle smoke", 1)[0]
    assert "--run" not in step
    assert "codex" not in step
    assert "claude" not in step
    assert 'payload["checks"]["mixed_move_add_explicit_windows"] is True' not in step
