from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from jsonschema import Draft202012Validator
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
HARNESS = SCRIPTS / "single_lane_evidence_harness.py"
SCHEMA = SCRIPTS / "schemas" / "single_lane_evidence.v1.schema.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import single_lane_evidence_fixtures as fixtures  # noqa: E402
import single_lane_evidence_harness as harness  # noqa: E402


EXPECTED_CLASSIFICATIONS = {
    "one-group-pass": "pass",
    "two-group-parallel-pass": "pass",
    "three-group-serial-pass": "pass",
    "four-group-mixed-dag-pass": "pass",
    "reviewer-rework-pass": "pass",
    "worker-failure-partial": "valid_non_success",
    "reviewer-failure-replan": "valid_non_success",
    "round-failure-blocked": "valid_non_success",
    "unknown-submission-restart-replay": "pass",
    "merge-conflict-replan": "valid_non_success",
    "root-test-failure-rollback": "valid_non_success",
    "release-busy-bounded": "valid_non_success",
    "release-persistent-failure": "system_failure",
    "missing-node-evidence": "test_design_failure",
    "provider-fake-success": "system_failure",
    "duplicate-ask": "system_failure",
    "duplicate-integration": "system_failure",
    "process-runtime-leak": "system_failure",
    "artifact-digest-mismatch": "system_failure",
}


def _report(manifest: dict | None = None) -> dict:
    return harness.normalize_manifest(
        manifest or fixtures.build_fixture_manifest(),
        source_commit=fixtures.FIXTURE_SOURCE_COMMIT,
    )


def _rows(report: dict) -> dict[str, dict]:
    return {row["case_id"]: row for row in report["rows"]}


def _case(manifest: dict, case_id: str) -> dict:
    return next(case for case in manifest["cases"] if case["case_id"] == case_id)


def _schema_validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_fixture_matrix_is_deterministic_and_covers_required_shapes() -> None:
    first = fixtures.build_fixture_manifest()
    second = fixtures.build_fixture_manifest()

    assert harness.canonical_json(first) == harness.canonical_json(second)
    assert first["required_case_ids"] == list(harness.REQUIRED_CASE_IDS)
    assert first["execution_mode"] == "deterministic_fixture"
    assert len(first["cases"]) == 19

    report = _report(first)
    rows = _rows(report)
    assert {case_id: row["classification"] for case_id, row in rows.items()} == EXPECTED_CLASSIFICATIONS
    assert report["classification"] == "pass"
    assert report["pass"] is True
    assert report["complete"] is True
    assert report["summary"]["classification_mismatch_case_ids"] == []
    assert all(row["classification_matches_expected"] for row in rows.values())
    assert rows["one-group-pass"]["bundle"]["adaptive_selection"]["workgroup_count"] == 1
    assert rows["two-group-parallel-pass"]["bundle"]["adaptive_selection"]["execution_shape"] == "parallel"
    assert rows["three-group-serial-pass"]["bundle"]["adaptive_selection"]["execution_shape"] == "serial"
    assert rows["four-group-mixed-dag-pass"]["bundle"]["adaptive_selection"] == {
        "workgroup_count": 4,
        "complexity": "very_complex",
        "cutability": "high",
        "execution_shape": "mixed_dag",
        "rationale": "deterministic mixed_dag fixture with 4 reviewed workgroup(s)",
    }


def test_every_negative_fixture_is_prevented_from_passing() -> None:
    rows = _rows(_report())
    negative_ids = set(EXPECTED_CLASSIFICATIONS) - {
        "one-group-pass",
        "two-group-parallel-pass",
        "three-group-serial-pass",
        "four-group-mixed-dag-pass",
        "reviewer-rework-pass",
        "unknown-submission-restart-replay",
    }

    assert all(rows[case_id]["classification"] != "pass" for case_id in negative_ids)
    assert rows["worker-failure-partial"]["round"]["result"] == "partial"
    assert rows["reviewer-failure-replan"]["round"]["result"] == "replan_required"
    assert rows["round-failure-blocked"]["round"]["result"] == "blocked"
    assert rows["merge-conflict-replan"]["integration"]["status"] == "conflict"
    assert rows["root-test-failure-rollback"]["root"]["rollback_digest"] == rows["root-test-failure-rollback"]["root"]["pre_digest"]


def test_rework_and_restart_replay_preserve_exact_once_lineage() -> None:
    rows = _rows(_report())
    rework_jobs = rows["reviewer-rework-pass"]["nodes"][0]["jobs"]
    assert [(job["purpose"], job["attempt"], job["status"]) for job in rework_jobs] == [
        ("worker", 1, "completed"),
        ("reviewer", 1, "rework"),
        ("worker_rework", 1, "completed"),
        ("reviewer", 2, "completed"),
    ]

    replay = rows["unknown-submission-restart-replay"]
    assert replay["classification"] == "pass"
    assert replay["nodes"][0]["jobs"][0]["submission_history"] == ["unknown", "resolved_same_job"]
    assert replay["authority_checks"]["duplicate_asks_absent"] is True


def test_provider_prose_cannot_set_route_result_pass_or_authority() -> None:
    manifest = fixtures.build_fixture_manifest()
    passing = _case(manifest, "one-group-pass")
    passing["round"]["provider_prose"] = "route=blocked result=partial classification=system_failure"
    first = _rows(_report(manifest))["one-group-pass"]
    assert first["classification"] == "pass"
    assert first["round"]["result"] == "pass"

    fake = _rows(_report())["provider-fake-success"]
    assert fake["classification"] == "system_failure"
    assert fake["round"]["provider_prose"].startswith("Provider reports success")
    assert fake["authority_checks"]["provider_prose_is_evidence_only"] is False
    assert fake["authority_checks"]["fake_success_absent"] is False


def test_missing_case_and_missing_field_are_test_design_failures() -> None:
    manifest = fixtures.build_fixture_manifest()
    manifest["cases"] = [case for case in manifest["cases"] if case["case_id"] != "one-group-pass"]
    rows = _rows(_report(manifest))
    assert rows["one-group-pass"]["observed"] is False
    assert rows["one-group-pass"]["classification"] == "test_design_failure"

    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    del case["task"]["digest"]
    row = _rows(_report(manifest))["one-group-pass"]
    assert row["classification"] == "test_design_failure"
    assert {item["code"] for item in row["diagnostics"]} == {"missing_evidence"}


def test_duplicate_case_is_system_failure_and_non_object_extra_case_invalidates_manifest() -> None:
    manifest = fixtures.build_fixture_manifest()
    manifest["cases"].append(deepcopy(_case(manifest, "one-group-pass")))
    duplicate_report = _report(manifest)
    duplicate = _rows(duplicate_report)["one-group-pass"]
    assert duplicate["classification"] == "system_failure"
    assert duplicate_report["classification"] == "system_failure"

    manifest = fixtures.build_fixture_manifest()
    manifest["cases"].append("not-an-evidence-row")
    invalid_report = _report(manifest)
    assert invalid_report["classification"] == "test_design_failure"
    assert invalid_report["pass"] is False


def test_malformed_data_is_system_failure() -> None:
    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    case["task"]["revision"] = "1"

    row = _rows(_report(manifest))["one-group-pass"]
    assert row["classification"] == "system_failure"
    assert "malformed_evidence" in {item["code"] for item in row["diagnostics"]}


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("nodes", 0, "jobs"), None),
        (("nodes", 0, "dependencies"), "node-999"),
        (("nodes", 0, "base_commit"), "not-a-commit"),
        (("nodes", 0, "jobs", 0, "submission_history"), "unknown"),
        (("task", "digest"), "not-a-digest"),
        (("integration", "checks"), "passed"),
        (("integration", "checks", 0, "status"), "green"),
        (("dependency_readiness", "ready_node_ids"), [{"node_id": "node-001"}]),
        (("topology_release", "retained_count"), "0"),
        (("runtime_residue", "bounded_retained_busy"), []),
        (("runtime_residue", "processes"), [{"kind": "provider", "agent_id": [], "state": "running"}]),
        (("authority_log", "asks"), [{"intent_key": ["not", "hashable"]}]),
        (("immaculate_freshness", "activations"), [{"activation_id": {}, "immaculate": True}] * 4),
        (("ui_placement", "placements", 0, "pane"), None),
        (("round", "result"), []),
        (("artifacts",), None),
    ],
)
def test_malformed_nested_evidence_never_crashes_and_emits_schema_valid_failure(
    path: tuple,
    value: object,
) -> None:
    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    target = case
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    report = _report(manifest)
    row = _rows(report)["one-group-pass"]
    assert row["classification"] == "system_failure"
    assert row["classification_matches_expected"] is False
    assert "malformed_evidence" in {item["code"] for item in row["diagnostics"]}
    _schema_validator().validate(report)


def test_unexpected_negative_result_fails_the_campaign_even_when_evidence_is_complete() -> None:
    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    fixtures._round_failure(case)

    report = _report(manifest)
    row = _rows(report)["one-group-pass"]
    assert row["classification"] == "valid_non_success"
    assert row["expected_classification"] == "pass"
    assert row["classification_matches_expected"] is False
    assert report["classification"] == "system_failure"
    assert report["complete"] is True
    assert report["summary"]["classification_mismatch_case_ids"] == ["one-group-pass"]


def test_authority_drift_duplicate_actions_and_legacy_dispatch_are_system_failures() -> None:
    rows = _rows(_report())
    assert rows["duplicate-ask"]["authority_checks"]["duplicate_asks_absent"] is False
    assert rows["duplicate-integration"]["authority_checks"]["duplicate_integrations_absent"] is False

    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    case["authority_log"]["legacy_files"] = [".ccb/runtime/topology_dispatch.json"]
    row = _rows(_report(manifest))["one-group-pass"]
    assert row["classification"] == "system_failure"
    assert row["authority_checks"]["topology_dispatch_absent"] is False


def test_digest_mismatch_is_computed_from_content_not_claimed_boolean() -> None:
    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    case["task"]["semantic"]["request"] = "tampered after digest"

    row = _rows(_report(manifest))["one-group-pass"]
    assert row["task"]["digest_matches"] is False
    assert row["classification"] == "system_failure"
    assert "digest_mismatch" in {item["code"] for item in row["diagnostics"]}


def test_bounded_busy_is_valid_non_success_but_unbounded_residue_fails() -> None:
    rows = _rows(_report())
    busy = rows["release-busy-bounded"]
    assert busy["classification"] == "valid_non_success"
    assert busy["topology_release"]["released_count"] == 3
    assert busy["topology_release"]["retained_count"] == 1
    assert busy["runtime_residue"]["checks"]["bounded_busy_valid"] is True
    assert busy["topology_release"]["checks"]["drained_agents_match_released"] is True

    leak = rows["process-runtime-leak"]
    assert leak["classification"] == "system_failure"
    assert {item["kind"] for item in leak["runtime_residue"]["processes"]} == {"ccbd", "tmux", "provider"}
    assert leak["runtime_residue"]["checks"]["unexplained_residue_absent"] is False


def test_cleanup_capture_must_precede_cleanup() -> None:
    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "one-group-pass")
    case["runtime_residue"]["captured_before_cleanup"] = False

    row = _rows(_report(manifest))["one-group-pass"]
    assert row["classification"] == "system_failure"
    assert "cleanup_or_process_leak" in {item["code"] for item in row["diagnostics"]}


def test_report_and_b7_are_tied_to_source_and_artifact_digests() -> None:
    report = _report()
    markdown = harness.markdown_b7(report)
    rows_jsonl = "".join(harness.canonical_json(row) + "\n" for row in report["rows"])

    assert report["source_commit"] == fixtures.FIXTURE_SOURCE_COMMIT
    assert report["live_execution_claimed"] is False
    assert report["artifact_digests"]["input_sha256"] == harness.sha256_value(fixtures.build_fixture_manifest())
    assert report["artifact_digests"]["rows_jsonl_sha256"] == hashlib.sha256(rows_jsonl.encode()).hexdigest()
    assert fixtures.FIXTURE_SOURCE_COMMIT in markdown
    assert report["artifact_digests"]["input_sha256"] in markdown
    assert report["artifact_digests"]["rows_jsonl_sha256"] in markdown
    assert "Provider prose is retained as evidence only" in markdown


def test_json_jsonl_and_markdown_outputs_are_byte_stable(tmp_path: Path) -> None:
    report = _report()
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_paths = harness.write_outputs(report, first)
    second_paths = harness.write_outputs(report, second)

    for key in first_paths:
        assert Path(first_paths[key]).read_bytes() == Path(second_paths[key]).read_bytes()


def test_schema_declares_strict_versioned_row_and_report() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    row_schema = schema["$defs"]["row"]
    report_schema = schema["$defs"]["report"]
    row = _report()["rows"][0]

    assert row_schema["additionalProperties"] is False
    assert report_schema["additionalProperties"] is False
    assert set(row_schema["required"]) == set(row)
    assert row_schema["properties"]["schema"]["const"] == harness.ROW_SCHEMA
    assert report_schema["properties"]["schema"]["const"] == harness.REPORT_SCHEMA


def test_normalized_report_and_every_row_validate_against_draft_2020_12_schema() -> None:
    report = _report()
    validator = _schema_validator()

    validator.validate(report)
    for row in report["rows"]:
        validator.validate(row)


def test_dynamic_control_roles_are_in_topology_ui_freshness_and_release_evidence() -> None:
    manifest = fixtures.build_fixture_manifest()
    case = _case(manifest, "four-group-mixed-dag-pass")
    dynamic_agents = case["topology_release"]["desired"]["agents"]

    assert len(dynamic_agents) == 10
    assert dynamic_agents[0].endswith("-orchestrator")
    assert dynamic_agents[-1].endswith("-ccb-round-reviewer")
    assert set(case["ui_placement"]["sidebar_agents"]) == set(dynamic_agents)
    assert {item["agent_id"] for item in case["ui_placement"]["placements"]} == set(dynamic_agents)
    assert len(case["immaculate_freshness"]["activations"]) == len(dynamic_agents)
    assert case["topology_release"]["released_count"] == len(dynamic_agents)
    assert set(case["topology_release"]["drained_agents"]) == set(dynamic_agents)


def test_normalization_does_not_mutate_input_or_authority_files(tmp_path: Path) -> None:
    manifest = fixtures.build_fixture_manifest()
    original = deepcopy(manifest)
    project = tmp_path / "project"
    authority = project / ".ccb" / "runtime" / "tasks" / "task.json"
    authority.parent.mkdir(parents=True)
    authority.write_text('{"status":"ready"}\n', encoding="utf-8")
    before = hashlib.sha256(authority.read_bytes()).hexdigest()

    _report(manifest)

    assert manifest == original
    assert hashlib.sha256(authority.read_bytes()).hexdigest() == before


def test_cli_writes_passing_campaign_without_mutating_authority(tmp_path: Path) -> None:
    manifest_path = tmp_path / "matrix.json"
    fixtures.write_fixture(manifest_path)
    project = tmp_path / "project"
    authority = project / ".ccb" / "runtime" / "round.json"
    authority.parent.mkdir(parents=True)
    authority.write_text('{"result":"pending"}\n', encoding="utf-8")
    before = authority.read_bytes()
    output = tmp_path / "evidence"

    completed = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--input",
            str(manifest_path),
            "--output-dir",
            str(output),
            "--source-commit",
            fixtures.FIXTURE_SOURCE_COMMIT,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert authority.read_bytes() == before
    assert json.loads(completed.stdout)["classification"] == "pass"
    assert (output / "single_lane_evidence_report.v1.json").is_file()
    assert (output / "single_lane_evidence_rows.v1.jsonl").is_file()
    assert (output / "single_lane_evidence_b7.v1.md").is_file()
    report = json.loads((output / "single_lane_evidence_report.v1.json").read_text(encoding="utf-8"))
    assert report["pass"] is True
    assert report["complete"] is True
    assert report["summary"]["classification_mismatch_case_ids"] == []
    assert report["summary"]["missing_or_incomplete_case_ids"] == ["missing-node-evidence"]
    _schema_validator().validate(report)


def test_cli_refuses_to_write_inside_ccb_authority_state(tmp_path: Path) -> None:
    manifest_path = tmp_path / "matrix.json"
    fixtures.write_fixture(manifest_path)
    completed = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--input",
            str(manifest_path),
            "--output-dir",
            str(tmp_path / ".ccb" / "runtime" / "evidence"),
            "--source-commit",
            fixtures.FIXTURE_SOURCE_COMMIT,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode != 0
    assert "must not be inside .ccb" in completed.stderr
    assert not (tmp_path / ".ccb").exists()


def test_removing_required_case_keeps_cli_nonzero_and_report_incomplete(tmp_path: Path) -> None:
    manifest = fixtures.build_fixture_manifest()
    manifest["cases"] = [case for case in manifest["cases"] if case["case_id"] != "four-group-mixed-dag-pass"]
    manifest_path = tmp_path / "missing.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output = tmp_path / "output"

    completed = subprocess.run(
        [
            sys.executable,
            str(HARNESS),
            "--input",
            str(manifest_path),
            "--output-dir",
            str(output),
            "--source-commit",
            fixtures.FIXTURE_SOURCE_COMMIT,
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads((output / "single_lane_evidence_report.v1.json").read_text(encoding="utf-8"))

    assert completed.returncode != 0
    assert report["complete"] is False
    assert "four-group-mixed-dag-pass" in report["summary"]["missing_or_incomplete_case_ids"]
