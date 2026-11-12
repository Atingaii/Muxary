# Phase 6B Real-Provider L0 Repeat2 B7 Report

Date: 2026-07-04
Status: test_design_failure

## Claim Boundary

This report covers one approved Phase 6B L0 repeat2 runtime-sanity attempt only. It does not approve Phase 6B, L1-L5, production/default enablement, or real-provider workflow capability.

## Launch Approval

- Approval artifact: `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_041526ab5f10-art_5fb0add0afc141b7.txt`
- Approved scope: exactly one repeat2 L0 run from `/home/bfly/yunwei/test_ccb2` using `/home/bfly/yunwei/ccb_source/ccb_test`.
- Lab root: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704`
- Project root: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity`
- Provider map: `ccb_round_reviewer -> claude`; all other six mapped roles -> `codex`.
- Provider home mode: approved inherited current real provider home; observed process env used lab-local `HOME`/`CCB_SOURCE_HOME` with inherited provider-profile semantics.

## Result Summary

Repeat2 did not pass. It is classified as `test_design_failure`.

- The approved stdin harness fix worked: the script continued after variant A compact ask and reached variant B.
- Variant A compact ask submitted successfully to `phase6b-l0-ccb-orchestrator` as `job_40835bfeed99`.
- Variant A release returned `0`, but post-release `ps` still listed `phase6b-l0-ccb-orchestrator` as `busy` with queue `1`; release output also reported `released_count=0`.
- Variant B topology proposal succeeded, but commit/apply failed with `agent profile ccb_orchestrator exceeds max_instances=1` before B ask/release could run.
- The approved B7 normalizer code failed before writing evidence because it called `hashlib.sha256` without importing `hashlib`; this report is a talk2 supervisor fallback from command logs and runtime artifacts.

## Evidence Row

Evidence row path: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/phase6b_l0_repeat2_evidence_row.json`

```json
{
  "approved_normalizer_failure": "approved B7 normalizer failed before writing row/report: NameError: name 'hashlib' is not defined",
  "approved_normalizer_path": "/home/bfly/yunwei/test_ccb2/phase6b_l0_repeat2_b7_normalizer.py",
  "ask_reachability": false,
  "ask_targets": {
    "minimal_orchestrator": "phase6b-l0-ccb-orchestrator",
    "resident_planning_group": "p6bl0b-orchestrator"
  },
  "ask_targets_logged": {
    "minimal_orchestrator": true,
    "resident_planning_group": false
  },
  "authority_write_violations": [],
  "classification": "test_design_failure",
  "cleanup_result": "release_incomplete",
  "command_returncodes": {
    "ask_a_orchestrator_compact": 0,
    "config_validate_after_a": 0,
    "config_validate_initial": 0,
    "diagnose": 0,
    "ps_a_after_ask": 0,
    "ps_a_after_release": 0,
    "start_project": 0,
    "topology_a_commit_apply": 0,
    "topology_a_propose": 0,
    "topology_a_release": 0,
    "topology_b_commit_apply": 1,
    "topology_b_propose": 0
  },
  "complexity_level": "L0",
  "detailer_activated_expected": false,
  "detailer_activated_observed": false,
  "expected_route": "runtime_sanity",
  "final_status": "valid_non_success",
  "human_diagnosis_summary": "Repeat2 fixed the ask-stdin harness and reached variant B. Variant A compact ask submitted successfully, but release did not free the busy dynamic orchestrator/profile slot. Variant B commit/apply then failed because ccb_orchestrator exceeded max_instances=1. Provider replies remain evidence only.",
  "input_errors": [],
  "launch_approval_artifact": "/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_041526ab5f10-art_5fb0add0afc141b7.txt",
  "missing_artifacts": [],
  "missing_command_labels": [
    "ask_b_orchestrator_compact",
    "ps_b_after_ask",
    "topology_b_release",
    "ps_b_after_release",
    "config_validate_after_b"
  ],
  "observed_route": "runtime_sanity",
  "provider_home_mode": "approved_inherited_current_real_provider_home",
  "provider_home_observed": {
    "AGENT_ROLES_STORE": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/roles",
    "CCB_SOURCE_HOME": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/source_home",
    "HOME": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/source_home"
  },
  "provider_mix": {
    "ccb_frontdesk": "codex",
    "ccb_orchestrator": "codex",
    "ccb_planner": "codex",
    "ccb_round_reviewer": "claude",
    "ccb_task_detailer": "codex",
    "code_reviewer": "codex",
    "coder": "codex"
  },
  "required_artifacts_present": true,
  "reviewer_contract_citation": null,
  "role_boundary_violations": [],
  "round_result": "not_applicable",
  "route_decision_correct": true,
  "runtime_residue": {
    "config_dynamic_agents_absent": false,
    "dynamic_agents_absent": false,
    "observed_topology_residue_absent": false
  },
  "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/run_l0.sh",
  "script_sha256": "4078f378851cdb6849814ccfd4c36f1552f90c854a9f5d5e8dfa2d24d39798fc",
  "script_sha256_matches": true,
  "script_sha256_recorded": "4078f378851cdb6849814ccfd4c36f1552f90c854a9f5d5e8dfa2d24d39798fc",
  "task_id": "phase6b-l0-runtime-sanity",
  "test_design_failures": [
    "Required command labels are missing: ask_b_orchestrator_compact, ps_b_after_ask, topology_b_release, ps_b_after_release, config_validate_after_b",
    "Variant B commit/apply failed: command_status: failed | error: agent profile ccb_orchestrator exceeds max_instances=1",
    "Variant A release returned 0 but dynamic orchestrator remained busy/bound in ps_a_after_release, preserving ccb_orchestrator profile pressure.",
    "approved B7 normalizer failed before writing row/report: NameError: name 'hashlib' is not defined"
  ],
  "topology_variants": [
    "minimal_orchestrator",
    "resident_planning_group"
  ],
  "variant_results": {
    "minimal_orchestrator": {
      "ask_job_ids": [
        "job_40835bfeed99"
      ],
      "ask_job_statuses": [
        "accepted",
        "running"
      ],
      "ask_returncode": 0,
      "ask_target": "phase6b-l0-ccb-orchestrator",
      "commit_apply_returncode": 0,
      "desired_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.desired.json",
      "desired_profiles": [
        "ccb_orchestrator"
      ],
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.events.jsonl",
      "observed_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.observed.json",
      "observed_profiles": [
        "ccb_orchestrator"
      ],
      "post_release_ps_contains_dynamic_agent": true,
      "proposal_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/topology_proposals/phase6b-l0-minimal-orchestrator.json",
      "proposal_profiles": [
        "ccb_orchestrator"
      ],
      "proposal_returncode": 0,
      "release_returncode": 0,
      "release_stdout_released_count": 0
    },
    "resident_planning_group": {
      "ask_returncode": null,
      "ask_target": "p6bl0b-orchestrator",
      "commit_apply_returncode": 1,
      "commit_apply_stderr": "command_status: failed\nerror: agent profile ccb_orchestrator exceeds max_instances=1",
      "desired_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
      "desired_profiles": [
        "ccb_frontdesk",
        "ccb_task_detailer",
        "ccb_planner",
        "ccb_orchestrator"
      ],
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
      "observed_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "observed_error": "agent profile ccb_orchestrator exceeds max_instances=1",
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
      "observed_profiles": [
        "ccb_frontdesk",
        "ccb_task_detailer",
        "ccb_planner",
        "ccb_orchestrator"
      ],
      "observed_reconcile_status": "failed",
      "proposal_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
      "proposal_profiles": [
        "ccb_frontdesk",
        "ccb_task_detailer",
        "ccb_planner",
        "ccb_orchestrator"
      ],
      "proposal_returncode": 0,
      "release_returncode": null
    }
  },
  "worker_reviewer_ask_success": null
}
```

## Command Log

Command log path: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/phase6b_l0_repeat2_command_log.jsonl`

| Label | Return Code | Stdout | Stderr |
| :--- | :--- | :--- | :--- |
| `diagnose` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/diagnose.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/diagnose.stderr` |
| `config_validate_initial` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/config_validate_initial.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/config_validate_initial.stderr` |
| `start_project` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/start_project.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/start_project.stderr` |
| `topology_a_propose` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_a_propose.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_a_propose.stderr` |
| `topology_a_commit_apply` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_a_commit_apply.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_a_commit_apply.stderr` |
| `ask_a_orchestrator_compact` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/ask_a_orchestrator_compact.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/ask_a_orchestrator_compact.stderr` |
| `ps_a_after_ask` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/ps_a_after_ask.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/ps_a_after_ask.stderr` |
| `topology_a_release` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_a_release.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_a_release.stderr` |
| `ps_a_after_release` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/ps_a_after_release.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/ps_a_after_release.stderr` |
| `config_validate_after_a` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/config_validate_after_a.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/config_validate_after_a.stderr` |
| `topology_b_propose` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_b_propose.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_b_propose.stderr` |
| `topology_b_commit_apply` | `1` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_b_commit_apply.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/topology_b_commit_apply.stderr` |

## Variant A: Minimal Orchestrator

- `topology_a_propose`: `0`
- `topology_a_commit_apply`: `0`
- `ask_a_orchestrator_compact`: `0`
- Ask job ids: `['job_40835bfeed99']`
- Ask job statuses: `['accepted', 'running']`
- `topology_a_release`: `0`
- Post-release `ps` still contains `phase6b-l0-ccb-orchestrator`: `True`

## Variant B: Resident Planning Group

- `topology_b_propose`: `0`
- `topology_b_commit_apply`: `1`
- Commit/apply failure: `command_status: failed
error: agent profile ccb_orchestrator exceeds max_instances=1`
- Observed topology status: `failed`
- Observed topology error: `agent profile ccb_orchestrator exceeds max_instances=1`
- Variant B did not reach compact ask, release, or post-release validation.

## Authority Audit

- Proposal/desired/observed topology files for A and B were checked for top-level `edges`, `gates`, and `artifacts` dispatch keys.
- Authority write violations: `[]`
- `topology_dispatch.json` files under project: `[]`
- Provider reply text did not mutate authority; B7 is generated from logs/runtime artifacts.

## Cleanup And Residue Audit

- A release command returned `0`, but release evidence is not clean because the dynamic A orchestrator remained listed after release.
- B did not mount any dynamic agents because commit/apply failed before ask/release.
- Runtime residue booleans are intentionally explicit and non-pass:

```json
{
  "config_dynamic_agents_absent": false,
  "dynamic_agents_absent": false,
  "observed_topology_residue_absent": false
}
```

## Post-B7 External Cleanup

After this B7 evidence was captured, `talk2` ran external-project cleanup with
the same lab-local role store:

```text
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/source_home
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/source_home
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/roles
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/l0-runtime-sanity kill
```

Cleanup result:

```text
kill_status: ok
project_id: 874f69fdc1da582f67c9aab58ff5ad8a796c2d3a94f48ec3c0ef62770acf4cbe
state: unmounted
socket_path: /run/user/1000/ccb-runtime/ccbd-874f69fdc1da.sock
forced: false
```

Logs:

- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/post_b7_kill_with_roles.stdout`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/post_b7_kill_with_roles.stderr`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/post_b7_kill_with_roles.rc`

This post-run cleanup does not change the L0 evidence classification above.
The attempted run remains `test_design_failure`.

## Follow-Up Required

Before any further real-provider L0 run, fix or explicitly account for the profile-capacity/release behavior where a submit-only busy dynamic orchestrator still occupies `ccb_orchestrator max_instances=1` after topology release. Also fix the B7 normalizer missing `hashlib` import before requesting another launch approval.
