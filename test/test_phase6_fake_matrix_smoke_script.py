from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "phase6_fake_matrix_smoke.py"
RUNTIME_RESIDUE_KEYS = {
    "dynamic_agents_absent",
    "config_dynamic_agents_absent",
    "observed_topology_residue_absent",
}


def _load_module():
    spec = importlib.util.spec_from_file_location("phase6_fake_matrix_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_manifest_declares_all_required_phase6_cases() -> None:
    module = _load_module()

    manifest = module.case_manifest()

    assert [case["case_id"] for case in manifest] == [
        "smoke-direct-execution-pass",
        "smoke-needs-detail-pass",
        "smoke-macro-adjustment",
        "smoke-blocked",
        "smoke-partial-completion",
        "smoke-reviewer-reject-rework",
        "smoke-reviewer-cannot-accept",
        "smoke-busy-release",
    ]
    assert [case["task_id"] for case in manifest] == [case["case_id"] for case in manifest]
    assert manifest[0]["runner"] == "workflow_closure_smoke.run_workflow_smoke"
    assert [case["runner"] for case in manifest[1:4]] == [
        "workflow_closure_smoke.run_phase6_route_smoke",
        "workflow_closure_smoke.run_phase6_route_smoke",
        "workflow_closure_smoke.run_phase6_route_smoke",
    ]
    assert [case["runner"] for case in manifest[4:7]] == [
        "workflow_closure_smoke.run_phase6_execution_case_smoke",
        "workflow_closure_smoke.run_phase6_execution_case_smoke",
        "workflow_closure_smoke.run_phase6_execution_case_smoke",
    ]
    assert manifest[7]["runner"] == "phase6_fake_matrix_smoke.run_busy_release_smoke"
    assert [case["implemented"] for case in manifest] == [True, True, True, True, True, True, True, True]


def test_report_marks_missing_cases_incomplete_not_pass() -> None:
    module = _load_module()

    report = module.build_matrix_report()

    assert report["phase6_fake_matrix_status"] == "incomplete"
    assert report["phase6a_pass"] is False
    assert report["summary"]["required_case_count"] == 8
    assert report["summary"]["observed_case_count"] == 0
    assert report["summary"]["implemented_case_count"] == 8
    assert report["summary"]["classification_counts"]["test_design_failure"] == 8
    assert report["summary"]["missing_case_ids"] == [row["case_id"] for row in report["rows"]]
    assert report["summary"]["not_implemented_case_ids"] == []

    direct_row = report["rows"][0]
    assert direct_row["case_id"] == "smoke-direct-execution-pass"
    assert direct_row["task_id"] == "smoke-direct-execution-pass"
    assert direct_row["implemented"] is True
    assert direct_row["case_status"] == "missing_evidence"
    assert direct_row["round_result"] == "not_run"
    assert direct_row["cleanup_result"] == "not_run"
    assert direct_row["runtime_residue"] == {
        "dynamic_agents_absent": None,
        "config_dynamic_agents_absent": None,
        "observed_topology_residue_absent": None,
    }
    assert direct_row["classification"] == "test_design_failure"
    assert [row["case_status"] for row in report["rows"]] == [
        "missing_evidence",
        "missing_evidence",
        "missing_evidence",
        "missing_evidence",
        "missing_evidence",
        "missing_evidence",
        "missing_evidence",
        "missing_evidence",
    ]
    for row in report["rows"]:
        assert {
            "task_id",
            "expected_route",
            "observed_route",
            "route_decision_correct",
            "round_result",
            "final_status",
            "cleanup_result",
            "runtime_residue",
            "classification",
        } <= set(row)


def test_direct_execution_evidence_can_pass_but_does_not_complete_matrix() -> None:
    module = _load_module()
    evidence = {
        "case_id": "smoke-direct-execution-pass",
        "task_id": "task-direct-001",
        "observed_route": "direct_execution",
        "round_result": "pass",
        "final_status": "done",
        "cleanup_status": "released",
        "artifact_paths": {"round_json": "/tmp/round.json"},
        "runtime_paths": {"project_root": "/tmp/phase6-direct"},
        "authority_checks": {
            "topology_dispatch_absent": True,
            "communication_edges_absent": True,
            "provider_reply_authority_parsing_absent": True,
        },
        "ask_reachability": True,
        "runtime_residue": {
            "dynamic_agents_absent": True,
            "config_dynamic_agents_absent": True,
            "observed_topology_residue_absent": True,
        },
    }

    report = module.build_matrix_report(direct_evidence=evidence)

    direct_row = report["rows"][0]
    assert direct_row["case_status"] == "observed"
    assert direct_row["task_id"] == "task-direct-001"
    assert direct_row["route_decision_correct"] is True
    assert direct_row["classification"] == "pass"
    assert direct_row["cleanup_result"] == "released"
    assert direct_row["ask_reachability"] is True
    assert direct_row["runtime_residue"]["dynamic_agents_absent"] is True
    _assert_runtime_residue_bools(direct_row)
    assert direct_row["artifact_paths"]["round_json"] == "/tmp/round.json"
    assert report["phase6_fake_matrix_status"] == "incomplete"
    assert report["phase6a_pass"] is False
    assert report["summary"]["observed_case_count"] == 1
    assert "smoke-direct-execution-pass" not in report["summary"]["missing_case_ids"]
    assert report["summary"]["classification_counts"]["pass"] == 1
    assert report["summary"]["classification_counts"]["test_design_failure"] == 7


def test_workflow_closure_payload_is_normalized_into_direct_execution_row(tmp_path: Path) -> None:
    module = _load_module()
    project_root = tmp_path / "phase6-direct"
    desired_path, observed_path = _write_runtime_residue_files(project_root, "lpdirect")
    payload = {
        "workflow_smoke_status": "ok",
        "task_id": "task-closure",
        "project_root": str(project_root),
        "summary": {
            "checks": {
                "route_direct_execution_imported": True,
                "topology_dispatch_absent": True,
                "release_status_released": True,
                "release_retained_zero": True,
                "ask_reachability": True,
                "dynamic_agents_absent_from_ps": True,
            },
            "round_path": "/tmp/phase6-direct/.ccb/runtime/loops/lp1/round.json",
            "round_result": "pass",
            "final_status": "done",
            "release": {
                "loop_topology_status": "released",
                "retained_count": 0,
            },
        },
        "results": [
            {
                "name": "runner_execute",
                "stdout": json.dumps(
                    {
                        "topology": {
                            "desired_path": str(desired_path),
                            "observed_path": str(observed_path),
                        }
                    }
                ),
            }
        ],
    }

    report = module.build_matrix_report(direct_evidence=payload)

    direct_row = report["rows"][0]
    assert direct_row["task_id"] == "task-closure"
    assert direct_row["observed_route"] == "direct_execution"
    assert direct_row["cleanup_status"] == "released"
    assert direct_row["cleanup_result"] == "released"
    assert direct_row["classification"] == "pass"
    assert direct_row["ask_reachability"] is True
    assert direct_row["runtime_paths"]["ccb_config"] == str(project_root / ".ccb" / "ccb.config")
    assert direct_row["runtime_residue"] == {
        "dynamic_agents_absent": True,
        "config_dynamic_agents_absent": True,
        "observed_topology_residue_absent": True,
    }
    assert direct_row["authority_checks"]["topology_dispatch_absent"] is True
    assert direct_row["authority_checks"]["provider_reply_authority_parsing_absent"] is True


def test_route_workflow_payloads_are_normalized_into_matrix_rows(tmp_path: Path) -> None:
    module = _load_module()
    desired_path, observed_path = _write_runtime_residue_files(tmp_path, "lproute")

    report = module.build_matrix_report(
        route_smoke_payloads={
            "smoke-needs-detail-pass": {
                "workflow_smoke_status": "ok",
                "phase6_case_id": "smoke-needs-detail-pass",
                "task_id": "smoke-needs-detail-pass",
                "project_root": str(tmp_path),
                "summary": {
                    "observed_route": "needs_detail",
                    "checks": {
                        "topology_dispatch_absent": True,
                        "communication_edges_absent": True,
                        "provider_reply_authority_parsing_absent": True,
                        "detail_step_files_imported": True,
                        "ask_reachability": True,
                        "dynamic_agents_absent_from_ps": True,
                    },
                    "round_path": str(tmp_path / "round.json"),
                    "round_result": "pass",
                    "round_result_source": "ask_first_round",
                    "final_status": "done",
                    "cleanup_status": "released",
                    "release": {"loop_topology_status": "released", "retained_count": 0},
                },
                "results": [
                    {
                        "name": "runner_execute",
                        "stdout": json.dumps(
                            {
                                "topology": {
                                    "desired_path": str(desired_path),
                                    "observed_path": str(observed_path),
                                }
                            }
                        ),
                    }
                ],
            },
            "smoke-macro-adjustment": {
                "workflow_smoke_status": "ok",
                "phase6_case_id": "smoke-macro-adjustment",
                "task_id": "smoke-macro-adjustment",
                "project_root": str(tmp_path),
                "summary": {
                    "observed_route": "macro_adjustment_request",
                    "checks": {
                        "topology_dispatch_absent": True,
                        "communication_edges_absent": True,
                        "provider_reply_authority_parsing_absent": True,
                        "adjustment_evidence_imported": True,
                        "execution_topology_absent": True,
                        "next_owner_planner": True,
                        "ask_reachability": False,
                        "dynamic_agents_absent_from_ps": True,
                    },
                    "round_result": "replan_required",
                    "round_result_source": "phase6_route_smoke_script",
                    "final_status": "replan_required",
                    "cleanup_status": "released",
                    "release": {"loop_topology_status": "released", "retained_count": 0},
                },
            },
            "smoke-blocked": {
                "workflow_smoke_status": "ok",
                "phase6_case_id": "smoke-blocked",
                "task_id": "smoke-blocked",
                "project_root": str(tmp_path),
                "summary": {
                    "observed_route": "blocked",
                    "checks": {
                        "topology_dispatch_absent": True,
                        "communication_edges_absent": True,
                        "provider_reply_authority_parsing_absent": True,
                        "blocker_evidence_imported": True,
                        "execution_topology_absent": True,
                        "next_owner_frontdesk_or_terminal": True,
                        "ask_reachability": False,
                        "dynamic_agents_absent_from_ps": True,
                    },
                    "round_result": "blocked",
                    "round_result_source": "phase6_route_smoke_script",
                    "final_status": "blocked",
                    "cleanup_status": "released",
                    "release": {"loop_topology_status": "released", "retained_count": 0},
                },
            },
        }
    )

    rows = {row["case_id"]: row for row in report["rows"]}
    assert rows["smoke-needs-detail-pass"]["classification"] == "pass"
    assert rows["smoke-needs-detail-pass"]["ask_reachability"] is True
    assert rows["smoke-needs-detail-pass"]["authority_checks"]["communication_edges_absent"] is True
    _assert_runtime_residue_bools(rows["smoke-needs-detail-pass"])
    assert rows["smoke-macro-adjustment"]["classification"] == "valid_non_success"
    assert rows["smoke-macro-adjustment"]["ask_reachability"] is False
    _assert_runtime_residue_bools(rows["smoke-macro-adjustment"])
    assert rows["smoke-blocked"]["classification"] == "valid_non_success"
    assert rows["smoke-blocked"]["final_status"] == "blocked"
    _assert_runtime_residue_bools(rows["smoke-blocked"])
    assert report["summary"]["observed_case_count"] == 3
    assert report["summary"]["classification_counts"]["pass"] == 1
    assert report["summary"]["classification_counts"]["valid_non_success"] == 2
    assert report["phase6_fake_matrix_status"] == "incomplete"


def test_execution_case_workflow_payloads_are_normalized_into_matrix_rows(tmp_path: Path) -> None:
    module = _load_module()
    desired_path, observed_path = _write_runtime_residue_files(tmp_path, "lpexec")

    report = module.build_matrix_report(
        route_smoke_payloads={
            "smoke-partial-completion": _case_payload(
                tmp_path,
                desired_path,
                observed_path,
                case_id="smoke-partial-completion",
                route="partial_completion",
                round_result="partial",
                final_status="partial",
            ),
            "smoke-reviewer-reject-rework": _case_payload(
                tmp_path,
                desired_path,
                observed_path,
                case_id="smoke-reviewer-reject-rework",
                route="direct_execution",
                round_result="pass",
                final_status="done",
            ),
            "smoke-reviewer-cannot-accept": _case_payload(
                tmp_path,
                desired_path,
                observed_path,
                case_id="smoke-reviewer-cannot-accept",
                route="direct_execution",
                round_result="replan_required",
                final_status="replan_required",
            ),
        }
    )

    rows = {row["case_id"]: row for row in report["rows"]}
    assert rows["smoke-partial-completion"]["classification"] == "valid_non_success"
    assert rows["smoke-partial-completion"]["final_status"] == "partial"
    _assert_runtime_residue_bools(rows["smoke-partial-completion"])
    assert rows["smoke-reviewer-reject-rework"]["classification"] == "pass"
    assert rows["smoke-reviewer-reject-rework"]["round_result"] == "pass"
    _assert_runtime_residue_bools(rows["smoke-reviewer-reject-rework"])
    assert rows["smoke-reviewer-cannot-accept"]["classification"] == "valid_non_success"
    assert rows["smoke-reviewer-cannot-accept"]["final_status"] == "replan_required"
    _assert_runtime_residue_bools(rows["smoke-reviewer-cannot-accept"])
    assert report["summary"]["observed_case_count"] == 3
    assert report["summary"]["classification_counts"]["pass"] == 1
    assert report["summary"]["classification_counts"]["valid_non_success"] == 2
    assert report["phase6_fake_matrix_status"] == "incomplete"


def test_mount_topology_desired_file_drives_communication_edges_check(tmp_path: Path) -> None:
    module = _load_module()
    desired_path = tmp_path / "agent_mount_topology.desired.json"
    desired_path.write_text(
        json.dumps(
            {
                "record_type": "ccb_loop_agent_mount_topology_desired",
                "nodes": [{"agent": "loop-lp1-coder-1"}],
            }
        ),
        encoding="utf-8",
    )
    evidence = {
        "case_id": "smoke-direct-execution-pass",
        "observed_route": "direct_execution",
        "round_result": "pass",
        "final_status": "done",
        "cleanup_result": "released",
        "runtime_paths": {"desired_path": str(desired_path)},
        "authority_checks": {"topology_dispatch_absent": True},
    }

    report = module.build_matrix_report(direct_evidence=evidence)

    direct_row = report["rows"][0]
    assert direct_row["authority_checks"]["topology_dispatch_absent"] is True
    assert direct_row["authority_checks"]["communication_edges_absent"] is True
    assert direct_row["classification"] == "pass"


def test_mount_topology_dispatch_fields_mark_authority_violation(tmp_path: Path) -> None:
    module = _load_module()
    desired_path = tmp_path / "agent_mount_topology.desired.json"
    desired_path.write_text(
        json.dumps(
            {
                "record_type": "ccb_loop_agent_mount_topology_desired",
                "nodes": [{"agent": "loop-lp1-coder-1"}],
                "edges": [{"from": "worker", "to": "reviewer"}],
            }
        ),
        encoding="utf-8",
    )
    evidence = {
        "case_id": "smoke-direct-execution-pass",
        "observed_route": "direct_execution",
        "round_result": "pass",
        "final_status": "done",
        "cleanup_result": "released",
        "runtime_paths": {"desired_path": str(desired_path)},
        "authority_checks": {"topology_dispatch_absent": True},
    }

    report = module.build_matrix_report(direct_evidence=evidence)

    direct_row = report["rows"][0]
    assert direct_row["authority_checks"]["topology_dispatch_absent"] is True
    assert direct_row["authority_checks"]["communication_edges_absent"] is False
    assert direct_row["classification"] == "system_failure"


def test_workflow_payload_reads_runner_topology_desired_path(tmp_path: Path) -> None:
    module = _load_module()
    desired_path = tmp_path / "agent_mount_topology.desired.json"
    desired_path.write_text(
        json.dumps({"record_type": "ccb_loop_agent_mount_topology_desired", "nodes": []}),
        encoding="utf-8",
    )
    payload = {
        "workflow_smoke_status": "ok",
        "project_root": str(tmp_path),
        "summary": {
            "checks": {
                "route_direct_execution_imported": True,
                "topology_dispatch_absent": True,
                "release_status_released": True,
            },
            "round_result": "pass",
            "final_status": "done",
            "release": {"loop_topology_status": "released", "retained_count": 0},
        },
        "results": [
            {
                "name": "runner_execute",
                "stdout": json.dumps(
                    {
                        "topology": {
                            "desired_path": str(desired_path),
                            "status": "ready",
                        }
                    }
                ),
            }
        ],
    }

    report = module.build_matrix_report(direct_smoke_payload=payload)

    direct_row = report["rows"][0]
    assert direct_row["runtime_paths"]["desired_path"] == str(desired_path)
    assert direct_row["authority_checks"]["communication_edges_absent"] is True
    assert direct_row["classification"] == "pass"


def test_valid_non_success_boundaries_are_not_pass_or_system_failure() -> None:
    module = _load_module()
    report = module.build_matrix_report(
        case_evidence={
            "smoke-macro-adjustment": {
                "observed_route": "macro_adjustment_request",
                "round_result": "replan_required",
                "final_status": "replan_required",
                "cleanup_result": "released",
            },
            "smoke-blocked": {
                "observed_route": "blocked",
                "round_result": "blocked",
                "final_status": "blocked",
                "cleanup_result": "released",
            },
            "smoke-partial-completion": {
                "observed_route": "partial_completion",
                "round_result": "partial",
                "final_status": "partial",
                "cleanup_result": "released",
            },
            "smoke-busy-release": {
                "observed_route": "direct_execution",
                "round_result": "busy",
                "final_status": "running",
                "cleanup_result": "retained_busy",
            },
        }
    )

    rows = {row["case_id"]: row for row in report["rows"]}
    for case_id in (
        "smoke-macro-adjustment",
        "smoke-blocked",
        "smoke-partial-completion",
        "smoke-busy-release",
    ):
        assert rows[case_id]["classification"] == "valid_non_success"
    assert report["phase6_fake_matrix_status"] == "incomplete"
    assert report["phase6a_pass"] is False


def test_release_incomplete_with_bounded_blockers_is_valid_non_success() -> None:
    module = _load_module()

    report = module.build_matrix_report(
        case_evidence={
            "smoke-macro-adjustment": {
                "observed_route": "macro_adjustment_request",
                "round_result": "replan_required",
                "final_status": "replan_required",
                "cleanup_result": "release_incomplete",
                "release_blockers": {
                    "p6bl0b-orchestrator": {
                        "desired_state": "absent",
                        "observed_state": "parked",
                        "lifecycle_state": "parked",
                        "reason": "parked_after_release",
                    }
                },
                "authority_checks": {
                    "topology_dispatch_absent": True,
                    "communication_edges_absent": True,
                    "provider_reply_authority_parsing_absent": True,
                },
                "runtime_residue": {
                    "dynamic_agents_absent": False,
                    "config_dynamic_agents_absent": False,
                    "observed_topology_residue_absent": False,
                },
            }
        }
    )

    row = {item["case_id"]: item for item in report["rows"]}["smoke-macro-adjustment"]
    assert row["cleanup_result"] == "release_incomplete"
    assert row["release_incomplete_agents"] == ["p6bl0b-orchestrator"]
    assert row["release_blockers"]["p6bl0b-orchestrator"]["reason"] == "parked_after_release"
    assert row["classification"] == "valid_non_success"
    assert report["summary"]["classification_counts"]["valid_non_success"] == 1
    assert "smoke-macro-adjustment" not in report["summary"]["hard_failure_case_ids"]
    assert report["phase6a_pass"] is False


def test_release_incomplete_without_bounded_blockers_is_system_failure() -> None:
    module = _load_module()

    report = module.build_matrix_report(
        direct_evidence={
            "case_id": "smoke-direct-execution-pass",
            "observed_route": "direct_execution",
            "round_result": "pass",
            "final_status": "done",
            "cleanup_result": "release_incomplete",
            "release_incomplete_agents": ["p6bl0b-orchestrator"],
            "release_blockers": {
                "p6bl0b-orchestrator": {
                    "profile": "ccb_orchestrator",
                    "reason": "unexpected_residue",
                }
            },
            "authority_checks": {
                "topology_dispatch_absent": True,
                "communication_edges_absent": True,
                "provider_reply_authority_parsing_absent": True,
            },
        }
    )

    direct_row = report["rows"][0]
    assert direct_row["cleanup_result"] == "release_incomplete"
    assert direct_row["classification"] == "system_failure"
    assert "smoke-direct-execution-pass" in report["summary"]["hard_failure_case_ids"]
    assert report["phase6a_pass"] is False


def test_busy_release_evidence_row_preserves_retained_busy_contract(tmp_path: Path) -> None:
    module = _load_module()
    desired_path = tmp_path / "agent_mount_topology.desired.json"
    desired_path.write_text(
        json.dumps({"record_type": "ccb_loop_agent_mount_topology_desired", "agents": []}),
        encoding="utf-8",
    )

    report = module.build_matrix_report(
        case_evidence={
            "smoke-busy-release": {
                "case_id": "smoke-busy-release",
                "task_id": "smoke-busy-release",
                "observed_route": "direct_execution",
                "round_result": "busy",
                "final_status": "running",
                "cleanup_result": "retained_busy",
                "runtime_paths": {"desired_path": str(desired_path), "project_root": str(tmp_path)},
                "authority_checks": {
                    "topology_dispatch_absent": True,
                    "provider_reply_authority_parsing_absent": True,
                },
                "ask_reachability": True,
                "runtime_residue": {
                    "dynamic_agents_absent": True,
                    "config_dynamic_agents_absent": True,
                    "observed_topology_residue_absent": True,
                },
                "retained_busy_evidence": {
                    "retained_agents": ["loop-p6busy-coder-1"],
                    "retain_reasons": {"loop-p6busy-coder-1": "runtime_state=busy"},
                },
            }
        }
    )

    row = {item["case_id"]: item for item in report["rows"]}["smoke-busy-release"]
    assert row["case_status"] == "observed"
    assert row["route_decision_correct"] is True
    assert row["round_result"] == "busy"
    assert row["final_status"] == "running"
    assert row["cleanup_result"] == "retained_busy"
    assert row["classification"] == "valid_non_success"
    assert row["authority_checks"] == {
        "topology_dispatch_absent": True,
        "communication_edges_absent": True,
        "provider_reply_authority_parsing_absent": True,
    }
    _assert_runtime_residue_bools(row)
    assert row["retained_busy_evidence"]["retain_reasons"] == {
        "loop-p6busy-coder-1": "runtime_state=busy"
    }


def test_busy_release_runner_builds_lifecycle_evidence(tmp_path: Path, monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setattr(module, "SOURCE_WRAPPER_ROOT", tmp_path)

    class FakeWorkflow:
        DEFAULT_PLAN = "workflow-smoke"

        def __init__(self) -> None:
            self.commands: list[str] = []
            self.command_argv: dict[str, list[str]] = {}

        def prepare_project(self, *, test_root, project_name, provider, ccb_test, reset):
            project_root = Path(test_root) / project_name
            (project_root / ".ccb").mkdir(parents=True, exist_ok=True)
            (project_root / ".ccb" / "ccb.config").write_text("frontdesk:fake\n", encoding="utf-8")
            role_store = project_root / "roles"
            role_store.mkdir(parents=True, exist_ok=True)
            return {"project_root": str(project_root), "role_store": str(role_store)}

        def _smoke_env(self, *, test_root, project_root, role_store):
            return {"HOME": str(Path(test_root) / "source_home")}

        def write_artifacts(self, *, project_root, task_id, route, scenario):
            drafts = Path(project_root) / "drafts"
            drafts.mkdir(parents=True, exist_ok=True)
            paths = {}
            for kind in ("task_packet", "execution_contract", "orchestration_notes"):
                path = drafts / f"{kind}.md"
                path.write_text(f"{kind}\nscenario: {scenario}\nroute: {route}\n", encoding="utf-8")
                paths[kind] = str(path)
            return paths

        def _append(self, results, name, command, *, cwd, env, timeout=60, allow_failure=False):
            self.commands.append(name)
            self.command_argv[name] = list(command)
            project_root = Path(command[command.index("--project") + 1]) if "--project" in command else Path(cwd)
            loop_dir = project_root / ".ccb" / "runtime" / "loops" / "p6busy"
            loop_dir.mkdir(parents=True, exist_ok=True)
            desired_path = loop_dir / "agent_mount_topology.desired.json"
            observed_path = loop_dir / "agent_mount_topology.observed.json"
            worker = "loop-p6busy-coder-1"
            reviewer = "loop-p6busy-code_reviewer-1"
            stdout = "{}"
            if name == "route_direct_execution":
                stdout = json.dumps({"artifact": {"orchestrator_route": "direct_execution"}})
            elif name == "busy_worker_ask":
                stdout = f"accepted job=job_busy123 target={worker}\n[CCB_ASYNC_SUBMITTED job=job_busy123 target={worker}]\n"
            elif name == "topology_release_busy":
                desired_path.write_text(json.dumps({"agents": [{"id": worker}]}), encoding="utf-8")
                observed_path.write_text(json.dumps({"agents": [{"id": worker}]}), encoding="utf-8")
                stdout = json.dumps(
                    {
                        "loop_topology_status": "retained_busy",
                        "desired_path": str(desired_path),
                        "observed_path": str(observed_path),
                        "retained_agents": [worker],
                        "retain_reasons": {worker: "runtime_state=busy"},
                        "released_agents": [reviewer],
                    }
                )
            elif name == "task_show_final":
                stdout = json.dumps({"task": {"status": "running", "current_loop": "p6busy"}})
            elif name == "post_retained_ps":
                stdout = f"{worker}\nfrontdesk\n"
            elif name.startswith("watch_"):
                stdout = "watch_status: terminal\n"
            elif name == "topology_release_idle":
                (project_root / ".ccb" / "ccb.config").write_text("frontdesk:fake\n", encoding="utf-8")
                desired_path.write_text(json.dumps({"agents": []}), encoding="utf-8")
                observed_path.write_text(json.dumps({"agents": []}), encoding="utf-8")
                stdout = json.dumps(
                    {
                        "loop_topology_status": "released",
                        "desired_path": str(desired_path),
                        "observed_path": str(observed_path),
                        "released_agents": [worker],
                        "retained_count": 0,
                        "released_count": 1,
                    }
                )
            elif name == "post_idle_ps":
                stdout = "frontdesk\nplanner\n"
            results.append({"name": name, "command": command, "returncode": 0, "stdout": stdout, "stderr": ""})

    fake = FakeWorkflow()
    monkeypatch.setattr(module, "_load_workflow_closure_smoke", lambda: fake)

    evidence = module.run_busy_release_smoke(
        test_root=tmp_path,
        project_name="phase6-busy",
        provider="fake",
        ccb_test=tmp_path / "ccb_test",
        timeout_s=1,
        reset=True,
        keep_running=False,
        busy_latency_ms=1000,
    )

    assert evidence["round_result"] == "busy"
    assert evidence["final_status"] == "running"
    assert evidence["cleanup_result"] == "retained_busy"
    assert evidence["ask_reachability"] is True
    assert evidence["authority_checks"]["topology_dispatch_absent"] is True
    assert evidence["authority_checks"]["communication_edges_absent"] is True
    assert evidence["runtime_residue"] == {
        "dynamic_agents_absent": True,
        "config_dynamic_agents_absent": True,
        "observed_topology_residue_absent": True,
    }
    assert evidence["retained_busy_evidence"]["retain_reasons"] == {
        "loop-p6busy-coder-1": "runtime_state=busy"
    }
    assert "topology_release_busy" in fake.commands
    assert "topology_release_idle" in fake.commands
    busy_ask_argv = fake.command_argv["busy_worker_ask"]
    task_id_index = busy_ask_argv.index("--task-id")
    assert busy_ask_argv[task_id_index + 2] == "loop-p6busy-coder-1"
    assert busy_ask_argv[task_id_index + 3 :] == ["phase6", "busy", "release", "smoke"]
    assert "from" not in busy_ask_argv


def test_route_decision_correct_is_computed_from_observed_route_not_evidence_flag() -> None:
    module = _load_module()
    evidence = {
        "case_id": "smoke-direct-execution-pass",
        "observed_route": "blocked",
        "route_decision_correct": True,
        "round_result": "pass",
        "final_status": "done",
        "cleanup_result": "released",
    }

    report = module.build_matrix_report(direct_evidence=evidence)

    direct_row = report["rows"][0]
    assert direct_row["route_decision_correct"] is False
    assert direct_row["classification"] == "system_failure"
    assert report["phase6_fake_matrix_status"] == "incomplete"


def test_direct_source_wrapper_run_rejects_non_external_test_root(tmp_path: Path) -> None:
    module = _load_module()

    try:
        module.run_direct_execution_smoke(
            test_root=tmp_path,
            project_name="phase6-direct",
            provider="fake",
            ccb_test=tmp_path / "ccb_test",
            timeout_s=1,
            reset=False,
            keep_running=False,
        )
    except ValueError as exc:
        assert "/home/bfly/yunwei/test_ccb2" in str(exc)
    else:
        raise AssertionError("expected non-external source-wrapper root to be rejected")


def test_cli_writes_json_report_and_jsonl_rows_while_returning_incomplete(tmp_path: Path, capsys) -> None:
    module = _load_module()
    evidence_path = tmp_path / "direct-evidence.json"
    evidence_path.write_text(
        json.dumps(
            {
                "case_id": "smoke-direct-execution-pass",
                "observed_route": "direct_execution",
                "round_result": "pass",
                "final_status": "done",
                "cleanup_status": "released",
                "authority_checks": {"topology_dispatch_absent": True},
            }
        ),
        encoding="utf-8",
    )

    rc = module.main(
        [
            "--direct-evidence",
            str(evidence_path),
            "--output-dir",
            str(tmp_path / "report"),
            "--history-report-path",
            str(tmp_path / "history.md"),
            "--json",
        ]
    )

    assert rc == 1
    printed = json.loads(capsys.readouterr().out)
    assert printed["phase6_fake_matrix_status"] == "incomplete"
    report_path = tmp_path / "report" / "phase6_fake_matrix_report.json"
    rows_path = tmp_path / "report" / "phase6_fake_matrix_rows.jsonl"
    history_path = tmp_path / "history.md"
    assert report_path.is_file()
    assert rows_path.is_file()
    assert history_path.is_file()
    persisted = json.loads(report_path.read_text(encoding="utf-8"))
    assert persisted["report_paths"]["report_json"] == str(report_path)
    assert persisted["report_paths"]["markdown_report"] == str(history_path)
    assert len(rows_path.read_text(encoding="utf-8").splitlines()) == 8
    history = history_path.read_text(encoding="utf-8")
    assert "# Phase 6 Fake-Provider Matrix Scaffold Report" in history
    assert "phase6_fake_matrix_status: `incomplete`" in history
    assert "Missing or not implemented cases remain" in history
    assert "smoke-needs-detail-pass" in history


def test_markdown_report_uses_pass_wording_for_observed_matrix() -> None:
    module = _load_module()
    report = module.build_matrix_report(case_evidence=_all_case_evidence())

    assert report["phase6_fake_matrix_status"] == "pass"
    assert report["phase6a_pass"] is True

    history = module._markdown_report(report)

    assert "# Phase 6 Fake-Provider Matrix Report" in history
    assert "Scaffold Report" not in history
    assert "phase6_fake_matrix_status: `pass`" in history
    assert "observed_case_count: `8`" in history
    assert "## Reviewer Audit Notes" in history
    assert "All eight required fake-provider matrix cases are observed" in history
    assert "final Phase 6A acceptance still requires reviewer/module-level sign-off" in history
    assert "Missing or not implemented cases remain" not in history


def test_busy_only_selected_matrix_does_not_require_unselected_rows() -> None:
    module = _load_module()
    evidence = _all_case_evidence()[module.BUSY_RELEASE_CASE_ID]

    report = module.build_matrix_report(
        case_evidence={module.BUSY_RELEASE_CASE_ID: evidence},
        selected_case_ids=[module.BUSY_RELEASE_CASE_ID],
    )

    assert report['phase6_fake_matrix_status'] == 'pass'
    assert report['summary']['required_case_count'] == 1
    assert report['summary']['observed_case_count'] == 1
    assert report['summary']['missing_case_ids'] == []
    assert [row['case_id'] for row in report['rows']] == [module.BUSY_RELEASE_CASE_ID]
    assert [row['case_id'] for row in report['manifest']] == [module.BUSY_RELEASE_CASE_ID]


def _case_payload(
    tmp_path: Path,
    desired_path: Path,
    observed_path: Path,
    *,
    case_id: str,
    route: str,
    round_result: str,
    final_status: str,
) -> dict[str, object]:
    return {
        "workflow_smoke_status": "ok",
        "phase6_case_id": case_id,
        "task_id": case_id,
        "project_root": str(tmp_path),
        "summary": {
            "observed_route": route,
            "checks": {
                "topology_dispatch_absent": True,
                "communication_edges_absent": True,
                "provider_reply_authority_parsing_absent": True,
                "ask_reachability": True,
                "dynamic_agents_absent_from_ps": True,
            },
            "round_path": str(tmp_path / f"{case_id}-round.json"),
            "round_result": round_result,
            "round_result_source": "round_reviewer_reply",
            "final_status": final_status,
            "cleanup_status": "released",
            "release": {"loop_topology_status": "released", "retained_count": 0},
        },
        "results": [
            {
                "name": "runner_execute",
                "stdout": json.dumps(
                    {
                        "topology": {
                            "desired_path": str(desired_path),
                            "observed_path": str(observed_path),
                        }
                    }
                ),
            }
        ],
    }


def _write_runtime_residue_files(project_root: Path, loop_id: str) -> tuple[Path, Path]:
    (project_root / ".ccb").mkdir(parents=True, exist_ok=True)
    (project_root / ".ccb" / "ccb.config").write_text(
        "frontdesk:fake; planner:fake; orchestrator:fake; ccb_round_reviewer:fake\n"
        "\n"
        "[loop.capacity]\n"
        'name_template = "loop-{loop_id}-{profile}-{index}"\n',
        encoding="utf-8",
    )
    loop_dir = project_root / ".ccb" / "runtime" / "loops" / loop_id
    loop_dir.mkdir(parents=True, exist_ok=True)
    desired_path = loop_dir / "agent_mount_topology.desired.json"
    observed_path = loop_dir / "agent_mount_topology.observed.json"
    desired_path.write_text(
        json.dumps(
            {
                "record_type": "ccb_loop_agent_mount_topology_desired",
                "loop_id": loop_id,
                "agents": [],
                "nodes": [],
            }
        ),
        encoding="utf-8",
    )
    observed_path.write_text(
        json.dumps(
            {
                "record_type": "ccb_loop_agent_mount_topology_observed",
                "loop_id": loop_id,
                "agents": [],
            }
        ),
        encoding="utf-8",
    )
    return desired_path, observed_path


def _assert_runtime_residue_bools(row: dict[str, object]) -> None:
    residue = row["runtime_residue"]
    assert isinstance(residue, dict)
    assert RUNTIME_RESIDUE_KEYS <= set(residue)
    assert all(isinstance(residue[key], bool) for key in RUNTIME_RESIDUE_KEYS)


def _all_case_evidence() -> dict[str, dict[str, object]]:
    return {
        "smoke-direct-execution-pass": {
            "observed_route": "direct_execution",
            "round_result": "pass",
            "final_status": "done",
            "cleanup_result": "released",
        },
        "smoke-needs-detail-pass": {
            "observed_route": "needs_detail",
            "round_result": "pass",
            "final_status": "done",
            "cleanup_result": "released",
        },
        "smoke-macro-adjustment": {
            "observed_route": "macro_adjustment_request",
            "round_result": "replan_required",
            "final_status": "replan_required",
            "cleanup_result": "released",
        },
        "smoke-blocked": {
            "observed_route": "blocked",
            "round_result": "blocked",
            "final_status": "blocked",
            "cleanup_result": "released",
        },
        "smoke-partial-completion": {
            "observed_route": "partial_completion",
            "round_result": "partial",
            "final_status": "partial",
            "cleanup_result": "released",
        },
        "smoke-reviewer-reject-rework": {
            "observed_route": "direct_execution",
            "round_result": "pass",
            "final_status": "done",
            "cleanup_result": "released",
        },
        "smoke-reviewer-cannot-accept": {
            "observed_route": "direct_execution",
            "round_result": "replan_required",
            "final_status": "replan_required",
            "cleanup_result": "released",
        },
        "smoke-busy-release": {
            "observed_route": "direct_execution",
            "round_result": "busy",
            "final_status": "running",
            "cleanup_result": "retained_busy",
        },
    }
