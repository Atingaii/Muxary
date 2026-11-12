# Phase 6B Real-Provider L0 B7 Report

Status: test_design_failure

## Claim Boundary

This report covers Phase 6B L0 runtime sanity only. It does not approve Phase 6B, L1-L5, production/default enablement, or real capability beyond the observed L0 evidence.

## Evidence Provenance

The evidence row is generated from command logs and runtime artifacts. Provider reply text remains evidence only and does not write task or topology authority fields.

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
    "config_validate_initial": 0,
    "diagnose": 0,
    "start_project": 0,
    "topology_a_commit_apply": 0,
    "topology_a_propose": 0
  },
  "complexity_level": "L0",
  "detailer_activated_expected": false,
  "detailer_activated_observed": false,
  "expected_route": "runtime_sanity",
  "final_status": "valid_non_success",
  "human_diagnosis_summary": "L0 runtime sanity normalized from command logs, topology artifacts, ask log, and release residue evidence. Provider replies are evidence only and do not mutate authority fields.",
  "input_errors": [
    "missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/asks.jsonl"
  ],
  "missing_artifacts": [
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json"
  ],
  "missing_command_labels": [
    "ask_b_orchestrator_compact",
    "config_validate_after_a",
    "config_validate_after_b",
    "ps_a_after_ask",
    "ps_a_after_release",
    "ps_b_after_ask",
    "ps_b_after_release",
    "topology_a_release",
    "topology_b_commit_apply",
    "topology_b_propose",
    "topology_b_release"
  ],
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
  "required_artifacts_present": false,
  "reviewer_contract_citation": null,
  "role_boundary_violations": [],
  "round_result": "not_applicable",
  "route_decision_correct": true,
  "runtime_residue": {
    "config_dynamic_agents_absent": false,
    "dynamic_agents_absent": false,
    "observed_topology_residue_absent": false
  },
  "task_id": "phase6b-l0-runtime-sanity",
  "test_design_failures": [
    "Required command labels are missing: ask_b_orchestrator_compact, config_validate_after_a, config_validate_after_b, ps_a_after_ask, ps_a_after_release, ps_b_after_ask, ps_b_after_release, topology_a_release, topology_b_commit_apply, topology_b_propose, topology_b_release",
    "Required runtime artifacts are missing: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json, /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl, /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json, /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
    "resident_planning_group.proposal: missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
    "resident_planning_group.desired: missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
    "resident_planning_group.observed: missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
    "missing artifact: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/asks.jsonl"
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
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.desired.json",
      "desired_profiles": [
        "ccb_orchestrator"
      ],
      "dynamic_agents_absent_after_release": false,
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.events.jsonl",
      "expected_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "missing_artifacts": [],
      "observed_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.observed.json",
      "observed_profiles": [
        "ccb_orchestrator"
      ],
      "observed_topology_residue_absent": false,
      "proposal_agent_ids": [
        "phase6b-l0-ccb-orchestrator"
      ],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/topology_proposals/phase6b-l0-minimal-orchestrator.json",
      "proposal_profiles": [
        "ccb_orchestrator"
      ],
      "release_returncode": null
    },
    "resident_planning_group": {
      "ask_returncode": null,
      "ask_target": "p6bl0b-orchestrator",
      "config_dynamic_agents_absent_after_release": false,
      "desired_agent_ids": [],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
      "desired_profiles": [],
      "dynamic_agents_absent_after_release": false,
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
      "expected_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "missing_artifacts": [
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
        "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl"
      ],
      "observed_agent_ids": [],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
      "observed_profiles": [],
      "observed_topology_residue_absent": false,
      "proposal_agent_ids": [],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
      "proposal_profiles": [],
      "release_returncode": null
    }
  },
  "worker_reviewer_ask_success": null
}
```

## Command Log

/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/phase6b_l0_repeat_command_log.jsonl

## Talk2 Supervisor Note

This repeat run used reviewer2 approval
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f3adf3a31988-art_e0ad26e38f534e04.txt`.
The approved command block was executed once from `/home/bfly/yunwei/test_ccb2`.
It returned process status `0`, but the command log contains only six records:
`diagnose`, `config_validate_initial`, `start_project`, `topology_a_propose`,
`topology_a_commit_apply`, and `ask_a_orchestrator_compact`.

The variant A ask submitted successfully as `job_25a9c7e4a9b6` to
`phase6b-l0-ccb-orchestrator`. No `topology_a_release`, `config_validate_after_a`,
variant B, or release commands were logged before B7 normalization.

Supervisor diagnosis: the frozen command block was executed through stdin
piping into `bash`; `ccb_test ask` inherited stdin and consumed the remaining
script body. This is a repeat-launch execution-harness defect, not Phase 6B
readiness. The repeat approval is consumed and a further run requires fresh
correction and launch-specific approval.

Post-B7 external cleanup was run with the same lab-local role store and
returned `kill_status: ok`, `state: unmounted`.
