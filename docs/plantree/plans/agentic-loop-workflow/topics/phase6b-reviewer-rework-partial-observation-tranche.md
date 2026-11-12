# Phase 6B Reviewer-Rework / Partial Observation Tranche

Date: 2026-07-04
Status: PLAN-ONLY REVIEW PACKET / NOT LAUNCH APPROVAL / PHASE 6B UNCLAIMED

## Purpose

This packet turns the remaining Phase 6B claim blocker, "observe at least one
reviewer rework or partial result and classify it correctly", into a future
reviewable L5 observation tranche. It is planning material only. It does not
approve a provider run, does not request launch approval, and does not claim
Phase 6B readiness.

References:

- [Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md)
- [Phase 6B task-pack catalog](phase6-real-provider-lab-task-packs.md)
- [Frozen L1-L4 launch request](phase6b-l1-l4-launch-request-20260704.md)
- [Phase 6B launch checklist](phase6b-real-provider-lab-launch-checklist.md)
- [Phase 6B claim coverage matrix](phase6b-real-provider-claim-coverage-matrix.md)
- Reviewer2 L1-L4 doc-only acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c0fac249749e-art_85be7618d4844d01.txt`

## Boundary

- This tranche is separate from the frozen L1-L4 request and must not be
  appended to it without a new launch-specific reviewer verdict.
- It does not touch the worker1 static normalizer hardening lane
  `job_4697fb66db4e`.
- Any future execution must use a fresh external lab root, exact command
  shape, inherited current system provider environment, lab-local
  `AGENT_ROLES_STORE`, and explicit approval-to-run.
- No source-wrapper, `ccb_test`, provider, L0-L5, or runtime command is
  authorized by this document.

## Candidate Tasks

The partial candidate is the recommended single-task tranche if a future launch
reviewer approves only one observation, because the acceptance goal requires
reviewer rework or partial, and partial can be bounded without relying on a
provider mistake. The reviewer-rework candidate remains a concrete alternate
or second task if the launch reviewer wants direct reviewer-rework evidence.

| Candidate | Task id | Expected route | Expected round result | Expected final status | Expected classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Partial budget/source-gap observation | `phase6b-l5-partial-budget-source-gap` | `direct_execution` | `partial` | `partial` | `valid_non_success` |
| Reviewer bounded-rework observation | `phase6b-l5-reviewer-bounded-rework-contract` | `direct_execution` | `pass` after one accepted rework, or `reviewer_cannot_accept` if not accepted | `done` after accepted rework, otherwise `partial`, `replan_required`, or `blocked` | `pass` after accepted rework with `rework_attempt_count=1`; otherwise `valid_non_success` with explicit blocker evidence |

### Partial Candidate

Concrete fixture shape:

- Present file:
  `lab_docs/l5_partial_existing_summary.md`.
- Intentionally absent dependency:
  `lab_docs/l5_partial_required_source.md`.
- Task packet asks the worker to update the existing summary from the required
  source file, but explicitly forbids inventing missing source content.
- Execution contract says that if the source is absent, the worker must update
  only the safe completed portion, return `partial`, list completed and
  unfinished steps, and cite the missing source as blocker evidence.

Expected observation:

- `observed_route=direct_execution`.
- `round_result=partial`.
- `final_status=partial`.
- `classification=valid_non_success`.
- `partial_completed_steps` contains the existing-summary inspection/update
  step.
- `partial_unfinished_steps` contains the missing-source synchronization step.
- `human_diagnosis_summary` states that partial is valid because the missing
  source was bounded and not invented.

### Reviewer-Rework Candidate

Concrete fixture shape:

- Present file:
  `lab_docs/l5_reviewer_contract_note.md`.
- Task packet requires three exact markers in that file:
  `scope_boundary`, `verification_evidence`, and `claim_boundary`.
- Execution contract requires the worker reply to cite both `task_packet` and
  `execution_contract`, report the exact changed file, and include focused
  verification evidence.
- Reviewer contract requires rejection if any marker, citation, or verification
  evidence is missing. One reviewer-requested rework cycle is allowed.

Expected observation:

- `observed_route=direct_execution`.
- `rework_attempt_count=1` if the reviewer requests rework.
- Accepted rework: `round_result=pass`, `final_status=done`,
  `classification=pass`, and `reviewer_rework_observed=true`.
- Not accepted after the bounded rework: `round_result=reviewer_cannot_accept`
  or `partial`, `final_status=partial`, `replan_required`, or `blocked`, and
  `classification=valid_non_success` only when blocker evidence is explicit.
- If the first worker pass is accepted with no rework, the row may be `pass`
  but it does not satisfy the reviewer-rework/partial claim requirement; the
  launch supervisor should proceed to the partial candidate if approved.

## Required Artifacts

Future launch approval must name the exact output root before execution. The
following paths are schematic and must be bound by that future request:

```text
$PHASE6B_L5_ROOT/command_log.jsonl
$PHASE6B_L5_ROOT/rows/phase6b_l5_reviewer_rework_partial_evidence_rows.jsonl
$PHASE6B_L5_ROOT/reports/phase6b_l5_reviewer_rework_partial_b7.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/task_packet.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/execution_contract.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/orchestration_notes.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/worker_reply.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/reviewer_verdict.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/round_summary.md
```

Reviewer-rework rows additionally require:

```text
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/reviewer_rework_request.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/rework_reply.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/reviewer_final_verdict.md
```

Partial rows additionally require:

```text
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/partial_evidence.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/completed_steps.md
$PHASE6B_L5_ROOT/supervisor_imports/<task_id>/unfinished_steps.md
```

## Required B7 Row Fields

Every row must include the shared task-pack fields:

```text
task_id
complexity_level
provider_mix
expected_route
observed_route
route_decision_correct
required_artifacts_present
ask_reachability
detailer_activated_expected
detailer_activated_observed
worker_reviewer_ask_success
reviewer_contract_citation
round_result
final_status
cleanup_result
runtime_residue
role_boundary_violations
authority_write_violations
classification
human_diagnosis_summary
```

These L5 fields are also required:

```text
observation_type
failure_domain
rework_attempt_count
rework_attempt_limit
reviewer_rework_observed
reviewer_rework_request_path
reviewer_final_verdict_path
partial_observed
partial_completed_steps
partial_unfinished_steps
partial_reason
provider_format_drift
busy_retain_observed
topology_dispatch_absent
topology_communication_dsl_absent
provider_reply_authority_parsing_absent
release_blockers
release_incomplete_agents
```

Classification rules:

- `partial` with explicit completed and unfinished steps is
  `valid_non_success`.
- Accepted reviewer rework with exactly one rework attempt is `pass`.
- Reviewer cannot accept after the bounded rework is `valid_non_success` only
  when the row includes a concrete blocker, final reviewer verdict, and cleanup
  evidence.
- Missing artifacts, vague partials, hidden retries, unbounded reviewer
  rejection loops, provider text treated as authority, or unbounded runtime
  residue are not valid non-success.

## Reviewer Contract

The reviewer must cite both `task_packet` and `execution_contract`. The
reviewer must reject hidden fallback, scope shrink, fake success, missing
verification evidence, missing contract markers, or invented missing source
content. The reviewer must not mark partial work `done`.

Bounded rework limit:

- Maximum reviewer-requested rework cycles: `1`.
- A second reviewer rejection stops the task and must be classified from the
  evidence; it must not trigger an automatic hidden retry.
- The B7 row must record `rework_attempt_count` even when it is `0`.

## Cleanup And Residue Expectations

- Dynamic `coder` and `code_reviewer` agents are released only after
  `round_summary` import and idle proof.
- Resident roles stay mounted.
- `cleanup_result=released` is expected for clean rows.
- `cleanup_result=release_incomplete` is allowed only with explicit bounded
  `release_blockers` / `release_incomplete_agents`, such as `parked`,
  `drained`, `retained_busy`, or inherited-provider-home safety evidence.
- No released dynamic agent may remain in `.ccb/ccb.config`, desired topology,
  observed topology, or process/status evidence without an explicit blocker.
- Mainline evidence must not contain topology communication DSL fields,
  `topology_dispatch.json`, or provider-reply authority parsing.

## Stop Conditions

Stop before the next task and classify from evidence if any of these occur:

- future approval-to-run does not name the exact root, task tranche, and command
  shape;
- source-wrapper root or provider-home isolation is invalid;
- route differs from the launch-approved expected route;
- required `task_packet`, `execution_contract`, reviewer verdict, or
  `round_summary` artifact is missing;
- reviewer omits the required contract citation;
- rework attempts exceed the `1` attempt limit;
- partial completed/unfinished steps are empty or vague;
- provider reply text mutates authority state;
- topology dispatch or topology communication DSL appears in mainline evidence;
- cleanup leaves unbounded runtime residue.

## Reviewable Normalizer Shape

Status: PLAN-ONLY NORMALIZER SKETCH / DO NOT RUN.

Future launch approval must bind the exact root. Proposed root for the first
L5 observation tranche:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-reviewer-rework-partial-20260704
```

Exact normalization command shape for future reviewer approval:

```bash
# DO NOT RUN until an L5 launch-specific reviewer approves the exact root and tranche.
python - "$PHASE6B_L5_ROOT" \
  /home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l5-reviewer-rework-partial-b7-20260704.md <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
b7_path = Path(sys.argv[2])
command_log_path = root / "command_log.jsonl"
rows_path = root / "rows" / "phase6b_l5_reviewer_rework_partial_evidence_rows.jsonl"
supervisor_root = root / "supervisor_imports"

provider_mix = {
    "ccb_frontdesk": "codex",
    "ccb_planner": "codex",
    "ccb_orchestrator": "codex",
    "ccb_task_detailer": "codex",
    "ccb_round_reviewer": "claude",
    "coder": "codex",
    "code_reviewer": "codex",
}
candidate_defs = {
    "phase6b-l5-partial-budget-source-gap": {
        "observation_type": "partial",
        "failure_domain": "task_scope",
        "expected_route": "direct_execution",
    },
    "phase6b-l5-reviewer-bounded-rework-contract": {
        "observation_type": "reviewer_rework",
        "failure_domain": "reviewer_contract",
        "expected_route": "direct_execution",
    },
}
shared_fields = [
    "task_id",
    "complexity_level",
    "provider_mix",
    "expected_route",
    "observed_route",
    "route_decision_correct",
    "required_artifacts_present",
    "ask_reachability",
    "detailer_activated_expected",
    "detailer_activated_observed",
    "worker_reviewer_ask_success",
    "reviewer_contract_citation",
    "round_result",
    "final_status",
    "cleanup_result",
    "runtime_residue",
    "role_boundary_violations",
    "authority_write_violations",
    "classification",
    "human_diagnosis_summary",
]
l5_fields = [
    "observation_type",
    "failure_domain",
    "rework_attempt_count",
    "rework_attempt_limit",
    "reviewer_rework_observed",
    "reviewer_rework_request_path",
    "reviewer_final_verdict_path",
    "partial_observed",
    "partial_completed_steps",
    "partial_unfinished_steps",
    "partial_reason",
    "provider_format_drift",
    "busy_retain_observed",
    "topology_dispatch_absent",
    "topology_communication_dsl_absent",
    "provider_reply_authority_parsing_absent",
    "release_blockers",
    "release_incomplete_agents",
]

def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""

def read_lines(path):
    return [line.strip() for line in read_text(path).splitlines() if line.strip()]

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def load_jsonl(path):
    if not path.is_file():
        return [], [f"missing artifact: {path}"]
    records = []
    errors = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid jsonl: {path}:{line_number}: {exc}")
    return records, errors

def field_from_summary(text, field, default):
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.M)
    return match.group(1).strip() if match else default

def has_dispatch_keys(payload):
    if isinstance(payload, dict):
        if any(key in payload for key in ("edges", "gates", "artifacts")):
            return True
        return any(has_dispatch_keys(value) for value in payload.values())
    if isinstance(payload, list):
        return any(has_dispatch_keys(value) for value in payload)
    return False

def topology_json_paths():
    return [
        path
        for path in root.rglob("*.json")
        if path.name.startswith("agent_mount_topology") or path.parent.name == "topology_proposals"
    ]

def topology_communication_dsl_absent():
    paths = topology_json_paths()
    if not paths:
        return False
    return not any(has_dispatch_keys(load_json(path, {})) for path in paths)

def runtime_residue(task_dir):
    payload = load_json(task_dir / "runtime_residue.json", {})
    return {
        "dynamic_agents_absent": payload.get("dynamic_agents_absent"),
        "config_dynamic_agents_absent": payload.get("config_dynamic_agents_absent"),
        "observed_topology_residue_absent": payload.get("observed_topology_residue_absent"),
    }

def row_for(task_id, config, labels):
    task_dir = supervisor_root / task_id
    summary_text = read_text(task_dir / "round_summary.md")
    reviewer_text = read_text(task_dir / "reviewer_verdict.md")
    final_reviewer_path = task_dir / "reviewer_final_verdict.md"
    route = read_text(task_dir / "route.txt").strip() or "unknown"
    round_result = field_from_summary(summary_text, "round_result", "unknown")
    final_status = field_from_summary(summary_text, "final_status", "unknown")
    cleanup_result = field_from_summary(summary_text, "cleanup_result", "unknown")
    partial_completed = read_lines(task_dir / "completed_steps.md")
    partial_unfinished = read_lines(task_dir / "unfinished_steps.md")
    rework_request = task_dir / "reviewer_rework_request.md"
    release_payload = load_json(task_dir / "release.json", {})
    role_boundary = load_json(task_dir / "role_boundary_violations.json", [])
    authority_violations = load_json(task_dir / "authority_write_violations.json", [])
    required_artifacts = [
        "task_packet.md",
        "execution_contract.md",
        "orchestration_notes.md",
        "worker_reply.md",
        "reviewer_verdict.md",
        "round_summary.md",
    ]
    row = {
        "task_id": task_id,
        "complexity_level": "L5",
        "provider_mix": provider_mix,
        "expected_route": config["expected_route"],
        "observed_route": route,
        "route_decision_correct": route == config["expected_route"],
        "required_artifacts_present": all((task_dir / artifact).is_file() for artifact in required_artifacts),
        "ask_reachability": f"{task_id}__run_direct_execution_round" in labels,
        "detailer_activated_expected": False,
        "detailer_activated_observed": f"{task_id}__activate_detailer" in labels,
        "worker_reviewer_ask_success": (task_dir / "worker_reply.md").is_file() and (task_dir / "reviewer_verdict.md").is_file(),
        "reviewer_contract_citation": str(task_dir / "execution_contract.md")
        if "execution_contract" in reviewer_text
        else None,
        "round_result": round_result,
        "final_status": final_status,
        "cleanup_result": cleanup_result,
        "runtime_residue": runtime_residue(task_dir),
        "role_boundary_violations": role_boundary if isinstance(role_boundary, list) else ["invalid role boundary evidence"],
        "authority_write_violations": authority_violations if isinstance(authority_violations, list) else ["invalid authority evidence"],
        "classification": "test_design_failure",
        "human_diagnosis_summary": "missing or incomplete L5 observation evidence",
        "observation_type": config["observation_type"],
        "failure_domain": config["failure_domain"],
        "rework_attempt_count": 1 if rework_request.is_file() else 0,
        "rework_attempt_limit": 1,
        "reviewer_rework_observed": rework_request.is_file(),
        "reviewer_rework_request_path": str(rework_request) if rework_request.is_file() else None,
        "reviewer_final_verdict_path": str(final_reviewer_path) if final_reviewer_path.is_file() else None,
        "partial_observed": round_result == "partial" or final_status == "partial",
        "partial_completed_steps": partial_completed,
        "partial_unfinished_steps": partial_unfinished,
        "partial_reason": read_text(task_dir / "partial_evidence.md").strip() or None,
        "provider_format_drift": (task_dir / "provider_format_drift.md").is_file(),
        "busy_retain_observed": (task_dir / "busy_retain_observed.md").is_file(),
        "topology_dispatch_absent": not any(root.rglob("topology_dispatch.json")),
        "topology_communication_dsl_absent": topology_communication_dsl_absent(),
        "provider_reply_authority_parsing_absent": (task_dir / "round_summary.md").is_file()
        and not (task_dir / "provider_reply_authority_import.json").exists(),
        "release_blockers": release_payload.get("release_blockers", {}),
        "release_incomplete_agents": release_payload.get("release_incomplete_agents", []),
    }
    if row["authority_write_violations"] or row["role_boundary_violations"]:
        row["classification"] = "system_failure"
        return row
    if config["observation_type"] == "partial":
        if (
            row["route_decision_correct"]
            and row["required_artifacts_present"]
            and row["partial_observed"]
            and row["partial_completed_steps"]
            and row["partial_unfinished_steps"]
            and row["topology_dispatch_absent"]
            and row["topology_communication_dsl_absent"]
            and row["provider_reply_authority_parsing_absent"]
        ):
            row["classification"] = "valid_non_success"
            row["human_diagnosis_summary"] = "bounded partial observation with completed and unfinished step evidence"
    else:
        if row["reviewer_rework_observed"] and row["rework_attempt_count"] == 1 and round_result == "pass" and final_status == "done":
            row["classification"] = "pass"
            row["human_diagnosis_summary"] = "reviewer requested one bounded rework and accepted the final result"
        elif row["reviewer_rework_observed"] and final_status in {"partial", "replan_required", "blocked"} and final_reviewer_path.is_file():
            row["classification"] = "valid_non_success"
            row["human_diagnosis_summary"] = "bounded reviewer cannot-accept outcome after one rework"
    return row

command_records, input_errors = load_jsonl(command_log_path)
labels = {str(record.get("label")): record for record in command_records}
if supervisor_root.exists():
    task_ids = [path.name for path in supervisor_root.iterdir() if path.is_dir() and path.name in candidate_defs]
else:
    task_ids = []
if not task_ids:
    task_ids = list(candidate_defs)

rows = [row_for(task_id, candidate_defs[task_id], labels) for task_id in task_ids]
for row in rows:
    missing = [field for field in shared_fields + l5_fields if field not in row]
    if missing:
        row.setdefault("test_design_failures", []).append(f"missing row fields: {missing}")
        row["classification"] = "test_design_failure"

observation_requirement_met = any(
    (row.get("partial_observed") or row.get("reviewer_rework_observed"))
    and row.get("classification") in {"pass", "valid_non_success"}
    for row in rows
)
failure_taxonomy = {
    name: sum(1 for row in rows if row.get("classification") == name)
    for name in ["pass", "valid_non_success", "system_failure", "role_failure", "provider_failure", "test_design_failure"]
}
aggregate_status = "valid_non_success" if observation_requirement_met else "not_claimable"
if input_errors or any(row.get("classification") in {"system_failure", "role_failure", "provider_failure", "test_design_failure"} for row in rows):
    aggregate_status = "not_claimable"

rows_path.parent.mkdir(parents=True, exist_ok=True)
rows_path.write_text(
    "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
    encoding="utf-8",
)
b7_path.write_text(
    "\n".join(
        [
            "# Phase 6B L5 Reviewer-Rework / Partial B7 Report",
            "",
            f"Status: {aggregate_status}",
            "",
            "## Claim Boundary",
            "",
            "This report covers only the approved L5 reviewer-rework/partial observation tranche.",
            "It does not approve Phase 6B completion without reviewer acceptance.",
            "",
            "## Observation Requirement",
            "",
            f"reviewer_rework_or_partial_observed={str(observation_requirement_met).lower()}",
            "",
            "## Rows",
            "",
            "```json",
            json.dumps(rows, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Failure Taxonomy",
            "",
            "```json",
            json.dumps(failure_taxonomy, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    + "\n",
    encoding="utf-8",
)
PY
```

## Future Launch Boundary

This packet is ready to be reviewed as planning input only. A later launch
request must choose the exact candidate task or ordered tranche, bind concrete
paths, include the command and normalizer shape, and ask explicitly for
approval-to-run. Until that happens, Phase 6B remains unclaimed and no runtime
command is approved.
