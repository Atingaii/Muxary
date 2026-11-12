# Phase 6B Real-Provider L0 B7 Report

Status: pass

## Claim Boundary

This report covers Phase 6B L0 runtime sanity only. It does not approve Phase 6B, L1-L5, production/default enablement, or real capability beyond the observed L0 evidence.

## Evidence Provenance

The evidence row is generated from command logs and runtime artifacts. Provider reply text remains evidence only and does not write task or topology authority fields.

## Script Harness

Script path: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/run_l0.sh

Script sha256: a91587e9b48a0766df433f031ac9c936fe6fb4c621d175c5c57001907c6934b4

## Evidence Row

```json
{
  "ask_evidence_errors": [],
  "ask_evidence_paths": [
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccbd/messages/messages.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/agents/p6bl0b-orchestrator/jobs.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccbd/mailboxes/p6bl0b-orchestrator/inbox.jsonl",
    "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccbd/snapshots/job_4181721f9473.json"
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
  "classification": "pass",
  "cleanup_result": "released",
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
  "final_status": "ok",
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
    "observed_topology_residue_absent": true
  },
  "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/run_l0.sh",
  "script_sha256": "a91587e9b48a0766df433f031ac9c936fe6fb4c621d175c5c57001907c6934b4",
  "script_sha256_matches": true,
  "script_sha256_recorded": "a91587e9b48a0766df433f031ac9c936fe6fb4c621d175c5c57001907c6934b4",
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
      "desired_agent_ids": [],
      "desired_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
      "desired_profiles": [],
      "dynamic_agents_absent_after_release": false,
      "events_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
      "expected_agent_ids": [
        "p6bl0b-frontdesk",
        "p6bl0b-detailer",
        "p6bl0b-planner",
        "p6bl0b-orchestrator"
      ],
      "missing_artifacts": [],
      "observed_agent_ids": [],
      "observed_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
      "observed_profiles": [],
      "observed_topology_residue_absent": true,
      "proposal_agent_ids": [
        "p6bl0b-detailer",
        "p6bl0b-frontdesk",
        "p6bl0b-orchestrator",
        "p6bl0b-planner"
      ],
      "proposal_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
      "proposal_profiles": [
        "ccb_frontdesk",
        "ccb_orchestrator",
        "ccb_planner",
        "ccb_task_detailer"
      ],
      "release_blockers": {},
      "release_drained_agents": [
        "p6bl0b-detailer",
        "p6bl0b-frontdesk",
        "p6bl0b-orchestrator",
        "p6bl0b-planner"
      ],
      "release_drained_clean": true,
      "release_incomplete_agents": [],
      "release_loop_topology_status": "released",
      "release_returncode": 0
    }
  },
  "worker_reviewer_ask_success": null
}
```

## Command Log

/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_command_log.jsonl
