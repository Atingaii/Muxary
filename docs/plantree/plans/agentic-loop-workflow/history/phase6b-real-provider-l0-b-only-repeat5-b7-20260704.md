# Phase 6B Real-Provider L0 B7 Report

Status: valid_non_success

## Claim Boundary

This report covers Phase 6B L0 runtime sanity only. It does not approve Phase 6B, L1-L5, production/default enablement, or real capability beyond the observed L0 evidence.

## Evidence Provenance

The evidence row is generated from command logs and runtime artifacts. Provider reply text remains evidence only and does not write task or topology authority fields.

## Script Harness

Script path: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/run_l0.sh

Script sha256: c1c46371f9c56b265c32d7c6f8670d33416609c082ebf4ddb302f5c5d8b74f3e

## Evidence Row

```json
{
  "ask_evidence_errors": [],
  "ask_evidence_paths": [
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/ccbd/messages/messages.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/agents/p6bl0b-orchestrator/jobs.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/ccbd/mailboxes/p6bl0b-orchestrator/inbox.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/ccbd/snapshots/job_699a6c2997ad.json"
  ],
  "ask_reachability": true,
  "ask_reachability_by_variant": {
    "resident_planning_group": true
  },
  "ask_targets": {
    "resident_planning_group": "p6bl0b-orchestrator"
  },
  "ask_targets_logged": {
    "resident_planning_group": true
  },
  "authority_write_violations": [],
  "classification": "valid_non_success",
  "cleanup_result": "release_incomplete",
  "command_returncodes": {
    "ask_b_orchestrator_compact": 0,
    "config_validate_after_b": 0,
    "config_validate_initial": 0,
    "diagnose": 0,
    "ps_b_after_ask": 0,
    "ps_b_after_release": 0,
    "start_project": 0,
    "topology_b_commit_apply": 0,
    "topology_b_propose": 0,
    "topology_b_release": 0
  },
  "complexity_level": "L0",
  "detailer_activated_expected": false,
  "detailer_activated_observed": false,
  "expected_route": "runtime_sanity",
  "final_status": "valid_non_success",
  "human_diagnosis_summary": "L0 runtime sanity normalized from command logs, topology artifacts, ask log, and release residue evidence. Provider replies are evidence only and do not mutate authority fields.",
  "input_errors": [],
  "missing_artifacts": [],
  "missing_command_labels": [],
  "observed_route": "runtime_sanity",
  "provider_home_mode": "approved_inherited_current_real_provider_home",
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
  "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/run_l0.sh",
  "script_sha256": "c1c46371f9c56b265c32d7c6f8670d33416609c082ebf4ddb302f5c5d8b74f3e",
  "script_sha256_matches": true,
  "script_sha256_recorded": "c1c46371f9c56b265c32d7c6f8670d33416609c082ebf4ddb302f5c5d8b74f3e",
  "task_id": "phase6b-l0-runtime-sanity",
  "test_design_failures": [],
  "topology_variants": [
    "resident_planning_group"
  ],
  "variant_results": {
    "resident_planning_group": {
      "ask_returncode": 0,
      "ask_target": "p6bl0b-orchestrator",
      "config_dynamic_agents_absent_after_release": false,
      "desired_agent_ids": [
        "p6bl0b-detailer",
        "p6bl0b-frontdesk",
        "p6bl0b-orchestrator",
        "p6bl0b-planner"
      ],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
      "desired_profiles": [
        "ccb_frontdesk",
        "ccb_orchestrator",
        "ccb_planner",
        "ccb_task_detailer"
      ],
      "dynamic_agents_absent_after_release": false,
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
      "expected_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "missing_artifacts": [],
      "observed_agent_ids": [
        "p6bl0b-detailer",
        "p6bl0b-frontdesk",
        "p6bl0b-orchestrator",
        "p6bl0b-planner"
      ],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
      "observed_profiles": [
        "ccb_frontdesk",
        "ccb_orchestrator",
        "ccb_planner",
        "ccb_task_detailer"
      ],
      "observed_topology_residue_absent": false,
      "proposal_agent_ids": [
        "p6bl0b-detailer",
        "p6bl0b-frontdesk",
        "p6bl0b-orchestrator",
        "p6bl0b-planner"
      ],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
      "proposal_profiles": [
        "ccb_frontdesk",
        "ccb_orchestrator",
        "ccb_planner",
        "ccb_task_detailer"
      ],
      "release_blockers": {
        "p6bl0b-detailer": {
          "desired_state": "absent",
          "lifecycle_state": "parked",
          "observed_state": "parked",
          "profile": "ccb_task_detailer",
          "reason": "active_after_release"
        },
        "p6bl0b-frontdesk": {
          "desired_state": "absent",
          "lifecycle_state": "parked",
          "observed_state": "parked",
          "profile": "ccb_frontdesk",
          "reason": "active_after_release"
        },
        "p6bl0b-orchestrator": {
          "desired_state": "absent",
          "lifecycle_state": "parked",
          "observed_state": "parked",
          "profile": "ccb_orchestrator",
          "reason": "active_after_release"
        },
        "p6bl0b-planner": {
          "desired_state": "absent",
          "lifecycle_state": "parked",
          "observed_state": "parked",
          "profile": "ccb_planner",
          "reason": "active_after_release"
        }
      },
      "release_incomplete_agents": [
        "p6bl0b-detailer",
        "p6bl0b-frontdesk",
        "p6bl0b-orchestrator",
        "p6bl0b-planner"
      ],
      "release_loop_topology_status": "release_incomplete",
      "release_returncode": 0
    }
  },
  "worker_reviewer_ask_success": null
}
```

## Command Log

/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/phase6b_l0_b_only_repeat5_command_log.jsonl

## Talk2 Supervisor Note

Reviewer2 approved exactly one B-only repeat5 run in
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_2953f5e7ab7e-art_44ef33571b3d4e09.txt`
with verdict `APPROVED_TO_RUN_L0_B_ONLY_REPEAT5`. Talk2 executed the approved
command block once from `/home/bfly/yunwei/test_ccb2` against fresh root
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704`.

The run reached the intended B-only resident planning group path and normalized
as auditable non-success:

- `diagnose`, config validation, project start, topology B propose/apply, B
  compact ask, B `ps`, B release, B post-release `ps`, and B post-release
  config validation all returned `0`.
- B compact ask submitted `job_699a6c2997ad` to `p6bl0b-orchestrator`.
- The evidence row has `classification=valid_non_success`,
  `ask_reachability=true`, `required_artifacts_present=true`,
  `script_sha256_matches=true`, no missing labels, no missing artifacts, no
  input errors, no test-design failures, and no authority-write violations.
- `topology_b_release` returned `0` but reported
  `loop_topology_status=release_incomplete` with all four resident planning
  group agents still parked/active after release:
  `p6bl0b-frontdesk`, `p6bl0b-detailer`, `p6bl0b-planner`, and
  `p6bl0b-orchestrator`.

Provider-home evidence observed from the approved runner:

- `HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/source_home`
- `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/source_home`
- `AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/roles`
- mounted resident planning group provider profiles recorded `mode=inherit`,
  `home=null`, and inherit flags enabled in `topology_b_release.stdout`.

## Post-B7 External Cleanup

After B7 evidence was captured, `talk2` ran external-project cleanup with the
same lab-local role store:

```text
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/source_home
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/source_home
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/roles
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/l0-runtime-sanity kill
```

Cleanup result:

```text
kill_status: ok
project_id: eeead7606c13b6accfe91c6b5993ebe7319dec07842d2d3be5c1b68e234caca9
state: unmounted
socket_path: /run/user/1000/ccb-runtime/ccbd-eeead7606c13.sock
forced: false
```

Logs:

- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/logs/post_b7_kill_with_roles.stdout`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/logs/post_b7_kill_with_roles.stderr`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/logs/post_b7_kill_with_roles.rc`

This post-run cleanup does not turn the L0 run into Phase 6B readiness. The
attempt remains a bounded `valid_non_success` L0 runtime-sanity result.
