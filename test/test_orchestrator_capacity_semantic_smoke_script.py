from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "orchestrator_capacity_semantic_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("orchestrator_capacity_semantic_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_config_declares_orchestrator_and_loop_profiles() -> None:
    module = _load_module()

    text = module.build_config(provider="codex", model="gpt-test")

    assert 'main = "orchestrator:codex"' in text
    assert '[agents.orchestrator]' in text
    assert 'role = "agentroles.ccb_orchestrator"' in text
    assert '[loop.capacity]' in text
    assert 'name_template = "l{loop_id}-{profile}-{index}"' in text
    assert '[loop.role_profiles.worker]' in text
    assert '[loop.role_profiles.code_reviewer]' in text
    assert 'provider = "codex"' in text
    assert 'model = "gpt-test"' in text
    assert 'max_nodes = 2' in text
    assert 'thinking =' not in text


def test_prepare_project_writes_config_and_role_store(tmp_path: Path) -> None:
    module = _load_module()
    test_root = tmp_path / "test_ccb2"
    ccb_test = tmp_path / "ccb_test"
    ccb_test.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    payload = module.prepare_project(
        test_root=test_root,
        project_name="orchestrator-capacity-real-provider-smoke",
        provider="codex",
        ccb_test=ccb_test,
        reset=False,
    )

    project_root = Path(payload["project_root"])
    role_store = Path(payload["role_store"])
    assert (project_root / ".ccb" / "ccb.config").is_file()
    assert (role_store / "installed" / "agentroles.ccb_orchestrator" / "current" / "role.toml").is_file()
    assert (role_store / "installed" / "agentroles.coder" / "current" / "role.toml").is_file()
    assert (role_store / "installed" / "agentroles.code_reviewer" / "current" / "role.toml").is_file()
    assert (project_root / "bin" / "ccb").is_file()
    assert (project_root / "bin" / "ask").is_file()
    assert str(ccb_test.resolve(strict=False)) in (project_root / "bin" / "ccb").read_text(encoding="utf-8")


def test_preflight_reports_ok_when_required_files_exist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    test_root = tmp_path / "test_ccb2"
    (test_root / "source_home").mkdir(parents=True)
    ccb_test = tmp_path / "ccb_test"
    ccb_test.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    monkeypatch.setattr(module.shutil, "which", lambda name: f"/usr/bin/{name}")

    payload = module.preflight(
        test_root=test_root,
        project_name="orchestrator-capacity-real-provider-smoke",
        provider="codex",
        ccb_test=ccb_test,
    )

    assert payload["preflight_status"] == "ok"
    assert payload["checks"]["provider_executable"] == "codex"
    assert payload["checks"]["provider_executable_path"] == "/usr/bin/codex"
    assert payload["checks"]["source_home_provider_auth_exists"] is False
    assert "real_home_provider_auth_exists" in payload["checks"]
    assert payload["checks"]["default_loop_id"] == "rp1"
    assert payload["checks"]["default_worker_name"] == "lrp1-worker-1"
    assert payload["checks"]["default_reviewer_name"] == "lrp1-code_reviewer-1"
    assert payload["checks"]["default_generated_names_valid"] is True
    assert payload["checks"]["real_run_opt_in"] is False


def test_fake_provider_prepare_preflight_does_not_require_provider_binary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    test_root = tmp_path / "test_ccb2"
    ccb_test = tmp_path / "ccb_test"
    ccb_test.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    monkeypatch.setattr(module.shutil, "which", lambda _name: None)

    prepared = module.prepare_project(
        test_root=test_root,
        project_name="orchestrator-capacity-fake-prepare",
        provider="fake",
        ccb_test=ccb_test,
        reset=False,
    )
    payload = module.preflight(
        test_root=test_root,
        project_name="orchestrator-capacity-fake-prepare",
        provider="fake",
        ccb_test=ccb_test,
    )

    assert Path(prepared["source_home"]).is_dir()
    assert payload["preflight_status"] == "ok"
    assert payload["checks"]["provider_executable"] == "fake"
    assert payload["checks"]["provider_executable_path"] is None
    assert payload["checks"]["provider_executable_found"] is True
    assert payload["checks"]["source_home_exists"] is True


def test_autonomous_cleanup_contract_requires_capacity_release_and_layout_cleanup() -> None:
    module = _load_module()

    payload = module.autonomous_cleanup_contract()

    assert payload["autonomous_cleanup_contract_status"] == "ok"
    assert payload["canonical_pass"] is True
    assert "capacity.retained_count=0" in payload["required_final_checks"]
    assert "layout.loop_agent_count=0" in payload["required_final_checks"]
    assert payload["rejections"]["capacity_not_released"] is True
    assert payload["rejections"]["capacity_retained_agents"] is True
    assert payload["rejections"]["missing_layout_payload"] is True
    assert payload["rejections"]["layout_retains_loop_agents"] is True


def test_run_smoke_requires_explicit_real_provider_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv(module.REAL_RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match="real provider smoke requires"):
        module.run_smoke(
            test_root=tmp_path,
            project_name="orchestrator-capacity-real-provider-smoke",
            provider="codex",
            ccb_test=tmp_path / "ccb_test",
            loop_id="real-provider-smoke",
            task="smoke",
            provider_home_mode="source-home",
            timeout_s=1,
        )


def test_run_smoke_keeps_run_once_payload_when_command_returns_nonzero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    monkeypatch.setenv(module.REAL_RUN_ENV, "1")
    calls: list[list[str]] = []
    run_once_stdout = '{"loop_run_status":"failed","failure":{"error":"watch timed out"}}\n'
    round_path = (
        tmp_path
        / "orchestrator-capacity-real-provider-smoke"
        / ".ccb"
        / "runtime"
        / "loops"
        / "rp1"
        / "round.json"
    )
    round_path.parent.mkdir(parents=True)
    round_path.write_text(
        '{"agents":{"worker":"lrp1-worker-1","reviewer":"lrp1-code_reviewer-1","orchestrator":"orchestrator"}}',
        encoding="utf-8",
    )

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        name = command[-1]
        if name == "-f":
            return subprocess.CompletedProcess(command, 0, stdout="kill_status: ok\n", stderr="")
        if "run-once" in command:
            return subprocess.CompletedProcess(command, 1, stdout=run_once_stdout, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    payload = module.run_smoke(
        test_root=tmp_path,
        project_name="orchestrator-capacity-real-provider-smoke",
        provider="codex",
        ccb_test=tmp_path / "ccb_test",
        loop_id="rp1",
        task="smoke",
        provider_home_mode="source-home",
        timeout_s=1,
    )

    assert payload["smoke_status"] == "failed"
    assert payload["run_once_payload"] == {
        "loop_run_status": "failed",
        "failure": {"error": "watch timed out"},
    }
    names = [item["name"] for item in payload["results"]]
    assert "post_failure_ps" in names
    assert "post_failure_config_validate" in names
    assert "post_failure_pend_lrp1-worker-1" in names
    assert "post_failure_pend_lrp1-code_reviewer-1" in names
    assert "post_failure_pend_orchestrator" in names
    assert calls[-1][-2:] == ["kill", "-f"]


def test_run_autonomous_smoke_reports_success_from_parent_watch_and_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    monkeypatch.setenv(module.REAL_RUN_ENV, "1")
    project_root = tmp_path / "orchestrator-capacity-autonomous-smoke"
    (project_root / "roles").mkdir(parents=True)
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(list(command))
        if command[-2:] == ["kill", "-f"]:
            return subprocess.CompletedProcess(command, 0, stdout="kill_status: ok\n", stderr="")
        if "ask" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="accepted job=job_parent target=orchestrator\n[CCB_ASYNC_SUBMITTED job=job_parent target=orchestrator]\n",
                stderr="",
            )
        if "watch" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "watch_status: terminal\n"
                    "job_id: job_parent\n"
                    "agent_name: orchestrator\n"
                    "target_name: orchestrator\n"
                    "status: completed\n"
                    "reply: AUTONOMOUS_LOOP_STATUS: pass release_status: released released_count: 2 retained_count: 0\n"
                ),
                stderr="",
            )
        if "capacity" in command and "status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"loop_capacity_status":"released","retained_count":0}\n',
                stderr="",
            )
        if "layout" in command and "status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"layout_status":"ok","loop_agent_count":0,"windows":[{"name":"main","agent_names":["orchestrator"]}]}\n',
                stderr="",
            )
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    payload = module.run_autonomous_smoke(
        test_root=tmp_path,
        project_name="orchestrator-capacity-autonomous-smoke",
        provider="codex",
        ccb_test=tmp_path / "ccb_test",
        loop_id="auto1",
        task="smoke",
        provider_home_mode="real-home",
        timeout_s=1,
    )

    assert payload["autonomous_status"] == "ok"
    assert payload["parent_job_id"] == "job_parent"
    assert payload["watch_status"] == "completed"
    assert payload["capacity_payload"] == {"loop_capacity_status": "released", "retained_count": 0}
    assert payload["layout_payload"]["layout_status"] == "ok"
    assert payload["layout_payload"]["loop_agent_count"] == 0
    assert payload["repeat_count"] == 1
    assert len(payload["rounds"]) == 1
    assert payload["rounds"][0]["round_status"] == "ok"
    assert any("ask" in command for command in calls)
    assert any("watch" in command for command in calls)
    assert any("layout" in command and "status" in command for command in calls)


def test_run_autonomous_smoke_fails_when_layout_keeps_loop_agents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    monkeypatch.setenv(module.REAL_RUN_ENV, "1")
    project_root = tmp_path / "orchestrator-capacity-autonomous-layout-residue"
    (project_root / "roles").mkdir(parents=True)

    def fake_run(command, **_kwargs):
        if command[-2:] == ["kill", "-f"]:
            return subprocess.CompletedProcess(command, 0, stdout="kill_status: ok\n", stderr="")
        if "ask" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="accepted job=job_parent target=orchestrator\n[CCB_ASYNC_SUBMITTED job=job_parent target=orchestrator]\n",
                stderr="",
            )
        if "watch" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "watch_status: terminal\n"
                    "job_id: job_parent\n"
                    "agent_name: orchestrator\n"
                    "target_name: orchestrator\n"
                    "status: completed\n"
                    "reply: AUTONOMOUS_LOOP_STATUS: pass release_status: released released_count: 2 retained_count: 0\n"
                ),
                stderr="",
            )
        if "capacity" in command and "status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"loop_capacity_status":"released","retained_count":0}\n',
                stderr="",
            )
        if "layout" in command and "status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"layout_status":"ok","loop_agent_count":1}\n',
                stderr="",
            )
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    payload = module.run_autonomous_smoke(
        test_root=tmp_path,
        project_name="orchestrator-capacity-autonomous-layout-residue",
        provider="codex",
        ccb_test=tmp_path / "ccb_test",
        loop_id="auto1",
        task="smoke",
        provider_home_mode="real-home",
        timeout_s=1,
    )

    assert payload["autonomous_status"] == "failed"
    assert payload["rounds"][0]["round_status"] == "failed"
    assert payload["rounds"][0]["layout_payload"]["loop_agent_count"] == 1


def test_run_autonomous_smoke_repeats_rounds_with_stable_loop_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    monkeypatch.setenv(module.REAL_RUN_ENV, "1")
    project_root = tmp_path / "orchestrator-capacity-autonomous-repeat-smoke"
    (project_root / "roles").mkdir(parents=True)
    calls: list[list[str]] = []
    ask_inputs: list[str] = []
    ask_count = 0

    def fake_run(command, **kwargs):
        nonlocal ask_count
        calls.append(list(command))
        if command[-2:] == ["kill", "-f"]:
            return subprocess.CompletedProcess(command, 0, stdout="kill_status: ok\n", stderr="")
        if "ask" in command:
            ask_count += 1
            ask_inputs.append(str(kwargs.get("input") or ""))
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    f"accepted job=job_parent_{ask_count} target=orchestrator\n"
                    f"[CCB_ASYNC_SUBMITTED job=job_parent_{ask_count} target=orchestrator]\n"
                ),
                stderr="",
            )
        if "watch" in command:
            job_id = command[-1]
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "watch_status: terminal\n"
                    f"job_id: {job_id}\n"
                    "agent_name: orchestrator\n"
                    "target_name: orchestrator\n"
                    "status: completed\n"
                    "reply: AUTONOMOUS_LOOP_STATUS: pass release_status: released released_count: 2 retained_count: 0\n"
                ),
                stderr="",
            )
        if "capacity" in command and "status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"loop_capacity_status":"released","retained_count":0}\n',
                stderr="",
            )
        if "layout" in command and "status" in command:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout='{"layout_status":"ok","loop_agent_count":0,"windows":[{"name":"main","agent_names":["orchestrator"]}]}\n',
                stderr="",
            )
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    payload = module.run_autonomous_smoke(
        test_root=tmp_path,
        project_name="orchestrator-capacity-autonomous-repeat-smoke",
        provider="codex",
        ccb_test=tmp_path / "ccb_test",
        loop_id="rep",
        task="smoke",
        provider_home_mode="real-home",
        timeout_s=1,
        repeat_count=2,
    )

    assert payload["autonomous_status"] == "ok"
    assert payload["repeat_count"] == 2
    assert [item["loop_id"] for item in payload["rounds"]] == ["rep", "rep"]
    assert [item["parent_job_id"] for item in payload["rounds"]] == ["job_parent_1", "job_parent_2"]
    assert [item["round_status"] for item in payload["rounds"]] == ["ok", "ok"]
    assert "Loop id: rep" in ask_inputs[0]
    assert "Loop id: rep" in ask_inputs[1]
    assert sum(1 for command in calls if "ask" in command) == 2
    assert sum(1 for command in calls if "watch" in command) == 2
    assert sum(1 for command in calls if "capacity" in command and "status" in command) == 2
    assert sum(1 for command in calls if "layout" in command and "status" in command) == 2


def test_main_passes_repeat_to_autonomous_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_module()
    seen: dict[str, int] = {}

    monkeypatch.setattr(
        module,
        "prepare_project",
        lambda **_kwargs: {"project_root": str(tmp_path), "role_store": str(tmp_path / "roles")},
    )
    monkeypatch.setattr(
        module,
        "preflight",
        lambda **_kwargs: {"preflight_status": "ok", "checks": {}},
    )

    def fake_run_autonomous_smoke(**kwargs):
        seen["repeat_count"] = kwargs["repeat_count"]
        return {"autonomous_status": "ok", "repeat_count": kwargs["repeat_count"], "rounds": []}

    monkeypatch.setattr(module, "run_autonomous_smoke", fake_run_autonomous_smoke)

    rc = module.main(
        [
            "--test-root",
            str(tmp_path),
            "--project-name",
            "repeat-project",
            "--ccb-test",
            str(tmp_path / "ccb_test"),
            "--run-autonomous",
            "--repeat",
            "3",
            "--json",
        ]
    )

    assert rc == 0
    assert seen["repeat_count"] == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["autonomous"]["repeat_count"] == 3


def test_tests_workflow_runs_prepare_only_orchestrator_autonomous_cleanup_contract() -> None:
    text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "Guard orchestrator autonomous cleanup contract" in text
    assert "scripts/orchestrator_capacity_semantic_smoke.py" in text
    assert "ci-orchestrator-autonomous-cleanup" in text
    assert "matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'" in text
    assert "--provider fake" in text
    assert "--prepare-only" in text
    assert 'preflight["preflight_status"] == "ok"' in text
    assert 'contract["autonomous_cleanup_contract_status"] == "ok"' in text
    assert 'all(contract["rejections"].values())' in text
    assert '"config", "validate"' in text
    step = text.split("Guard orchestrator autonomous cleanup contract", 1)[1].split("provider-blackbox:", 1)[0]
    assert "--run" not in step
    assert "--run-autonomous" not in step
