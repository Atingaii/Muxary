# Phase 6B Real-Provider L0 B7 Report

Status: test_design_failure

## Claim Boundary

This report covers Phase 6B L0 runtime sanity only. It does not approve Phase 6B, L1-L5, production/default enablement, or real capability beyond the observed L0 evidence.

## Evidence Provenance

The evidence row is generated from command logs and runtime artifacts. Provider reply text remains evidence only and does not write task or topology authority fields.

## Script Harness

Script path: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/run_l0.sh

Script sha256: cb55ddd76cbd93322ebb9346967c002740f3b8986334df155aa28efc94f1cb00

## Evidence Row

```json
{
  "ask_reachability": false,
  "ask_targets": {
    "minimal_orchestrator": "phase6b-l0-ccb-orchestrator",
    "resident_planning_group": "p6bl0b-orchestrator"
  },
  "ask_targets_logged": {
    "minimal_orchestrator": false,
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
    "topology_a_release_clean_check": 66
  },
  "complexity_level": "L0",
  "detailer_activated_expected": false,
  "detailer_activated_observed": false,
  "expected_route": "runtime_sanity",
  "final_status": "valid_non_success",
  "human_diagnosis_summary": "L0 runtime sanity normalized from command logs, topology artifacts, ask log, and release residue evidence. Provider replies are evidence only and do not mutate authority fields.",
  "input_errors": [
    "missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/asks.jsonl"
  ],
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
  "release_gate": {
    "label": "topology_a_release_clean_check",
    "payload": {
      "loop_topology_status": "release_incomplete",
      "release_blockers": {
        "phase6b-l0-ccb-orchestrator": {
          "desired_state": "absent",
          "lifecycle_state": "parked",
          "observed_state": "parked",
          "profile": "ccb_orchestrator",
          "reason": "active_after_release"
        }
      },
      "release_gate_status": "blocked",
      "release_incomplete_agents": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "release_incomplete_profile_counts": {
        "ccb_orchestrator": 1
      }
    },
    "returncode": 66,
    "status": "blocked"
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
  "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/run_l0.sh",
  "script_sha256": "cb55ddd76cbd93322ebb9346967c002740f3b8986334df155aa28efc94f1cb00",
  "script_sha256_matches": true,
  "script_sha256_recorded": "cb55ddd76cbd93322ebb9346967c002740f3b8986334df155aa28efc94f1cb00",
  "task_id": "phase6b-l0-runtime-sanity",
  "test_design_failures": [
    "missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/asks.jsonl"
  ],
  "topology_variants": [
    "minimal_orchestrator",
    "resident_planning_group"
  ],
  "variant_results": {
    "minimal_orchestrator": {
      "ask_returncode": 0,
      "ask_target": "phase6b-l0-ccb-orchestrator",
      "config_dynamic_agents_absent_after_release": false,
      "desired_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.desired.json",
      "desired_profiles": [
        "ccb_orchestrator"
      ],
      "dynamic_agents_absent_after_release": false,
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.events.jsonl",
      "expected_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "missing_artifacts": [],
      "observed_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.observed.json",
      "observed_profiles": [
        "ccb_orchestrator"
      ],
      "observed_topology_residue_absent": false,
      "proposal_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/topology_proposals/phase6b-l0-minimal-orchestrator.json",
      "proposal_profiles": [
        "ccb_orchestrator"
      ],
      "release_blockers": {
        "phase6b-l0-ccb-orchestrator": {
          "desired_state": "absent",
          "lifecycle_state": "parked",
          "observed_state": "parked",
          "profile": "ccb_orchestrator",
          "reason": "active_after_release"
        }
      },
      "release_incomplete_agents": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "release_loop_topology_status": "release_incomplete",
      "release_returncode": 0
    },
    "resident_planning_group": {
      "ask_returncode": null,
      "ask_target": "p6bl0b-orchestrator",
      "config_dynamic_agents_absent_after_release": false,
      "desired_agent_ids": [],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
      "desired_profiles": [],
      "dynamic_agents_absent_after_release": false,
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
      "expected_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "missing_artifacts": [
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl"
      ],
      "observed_agent_ids": [],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
      "observed_profiles": [],
      "observed_topology_residue_absent": false,
      "proposal_agent_ids": [],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
      "proposal_profiles": [],
      "release_blockers": {},
      "release_incomplete_agents": [],
      "release_loop_topology_status": null,
      "release_returncode": null
    }
  },
  "worker_reviewer_ask_success": null
}
```

## Command Log

/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/phase6b_l0_repeat3_command_log.jsonl

## Talk2 Supervisor Note

Reviewer2 approved exactly one repeat3 run in
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_90cc9a80d7a0-art_4b939eb8ba814845.txt`
with verdict `APPROVED_TO_RUN_L0_REPEAT3`. Talk2 executed the approved launch
block once from `/home/bfly/yunwei/test_ccb2` against fresh root
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704`.

The run reached the intended repeat3 release gate:

- `diagnose`, config validation, project start, topology A propose/apply, A
  compact ask, A `ps`, A release, A post-release `ps`, and A post-release
  config validation all returned `0`.
- A compact ask submitted `job_b7a8ed0f671e` to
  `phase6b-l0-ccb-orchestrator`.
- `topology_a_release` returned `0` but reported
  `loop_topology_status=release_incomplete`, `released_count=0`, and
  `release_incomplete_agents=["phase6b-l0-ccb-orchestrator"]`.
- `topology_a_release_clean_check` returned `66` with
  `release_gate_status=blocked`, so variant B did not run. This prevented the
  repeat2 profile-capacity failure class from being re-entered.

The generated B7 row classifies the run as `test_design_failure` because the
normalizer still treats missing
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/runtime/asks.jsonl`
as an input error. Runtime ask evidence did exist under the actual CCB runtime
paths, including
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity/.ccb/agents/phase6b-l0-ccb-orchestrator/jobs.jsonl`.
That job later became `incomplete` with reason `project_shutdown` during
post-B7 cleanup. Provider reply text was not used as authority.

Provider-home evidence observed from the approved runner:

- `HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/source_home`
- `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/source_home`
- `AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/roles`
- mounted A orchestrator provider profile recorded `mode=inherit`,
  `home=null`, and inherit flags enabled in `topology_a_release.stdout`.

## Post-B7 External Cleanup

After B7 evidence was captured, `talk2` ran external-project cleanup with the
same lab-local role store:

```text
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/source_home
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/source_home
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/roles
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/l0-runtime-sanity kill
```

Cleanup result:

```text
kill_status: ok
project_id: f968ce8cb19a4fbcf18e07ae55615cf27800f02fc71a3d3834946e99cffe81b1
state: unmounted
socket_path: /run/user/1000/ccb-runtime/ccbd-f968ce8cb19a.sock
forced: false
```

Logs:

- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/logs/post_b7_kill_with_roles.stdout`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/logs/post_b7_kill_with_roles.stderr`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/logs/post_b7_kill_with_roles.rc`

This post-run cleanup does not change the L0 evidence classification above.
The attempted run remains non-passing and Phase 6B remains unclaimed.

## Follow-Up Required

Before any further real-provider L0 run, fix the B7 normalizer/runtime ask
evidence contract so the gated `release_incomplete` path can classify as the
intended auditable `valid_non_success` when command/runtime evidence is present.
The next request also needs fresh launch-specific approval; this repeat3
approval is consumed.
