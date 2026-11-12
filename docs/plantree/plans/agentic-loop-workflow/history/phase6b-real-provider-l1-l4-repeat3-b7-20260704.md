# Phase 6B L1-L4 B7 Report

Status: not_claimable

## Claim Boundary

This report covers only the approved L1-L4 real-provider launch sequence.
It does not approve L5, production/default enablement, or Phase 6B completion.

## Rows

```json
[
  {
    "ask_reachability": true,
    "authority_checks": {
      "communication_edges_absent": true,
      "no_source_checkout_edits": true,
      "provider_reply_authority_parsing_absent": true,
      "script_owned_round_imports": true,
      "script_owned_route_imports": true,
      "topology_dispatch_absent": true
    },
    "authority_write_violations": [],
    "blocker_evidence_imported": false,
    "changed_files": [],
    "classification": "test_design_failure",
    "cleanup_result": "unknown",
    "command_log_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/phase6b_l1_l4_command_log.jsonl",
    "complexity_level": "L1",
    "conflicting_decision_refs": [],
    "detail_design_path": null,
    "detail_packet_imported": false,
    "detail_packet_path": null,
    "detail_summary_path": null,
    "detailer_activated_expected": false,
    "detailer_activated_observed": false,
    "execution_after_detail_ready": false,
    "expected_route": "direct_execution",
    "final_status": "done",
    "hidden_fallback_detected": null,
    "human_diagnosis_summary": "normalizer did not find complete task evidence",
    "macro_adjustment_request_imported": false,
    "missing_dependency": null,
    "observed_route": "direct_execution",
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
    "reviewer_contract_citation": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/l1-l4-real-provider-lab/drafts/phase6b-l1-doc-direct-execution.execution_contract.md",
    "role_boundary_violations": [],
    "round_result": "pass",
    "round_summary_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/logs/phase6b-l1-doc-direct-execution__run_direct_execution_round.stdout",
    "route_decision_correct": true,
    "runtime_residue": {
      "config_dynamic_agents_absent": null,
      "dynamic_agents_absent": null,
      "observed_topology_residue_absent": null
    },
    "scope_shrink_detected": null,
    "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/run_l1_l4.sh",
    "script_sha256": "cd01a5da7ce5b27dfae3a1818b21d26f9f3b978870833b5feff3046a670e711d",
    "source_evidence_refs": [],
    "step_files_present": false,
    "task_id": "phase6b-l1-doc-direct-execution",
    "test_command": null,
    "test_result": "not_applicable",
    "worker_reviewer_ask_success": true
  },
  {
    "ask_reachability": true,
    "authority_checks": {
      "communication_edges_absent": true,
      "no_source_checkout_edits": true,
      "provider_reply_authority_parsing_absent": true,
      "script_owned_round_imports": true,
      "script_owned_route_imports": true,
      "topology_dispatch_absent": true
    },
    "authority_write_violations": [],
    "blocker_evidence_imported": false,
    "changed_files": [],
    "classification": "test_design_failure",
    "cleanup_result": "unknown",
    "command_log_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/phase6b_l1_l4_command_log.jsonl",
    "complexity_level": "L2",
    "conflicting_decision_refs": [],
    "detail_design_path": null,
    "detail_packet_imported": false,
    "detail_packet_path": null,
    "detail_summary_path": null,
    "detailer_activated_expected": false,
    "detailer_activated_observed": false,
    "execution_after_detail_ready": false,
    "expected_route": "direct_execution",
    "final_status": "done",
    "hidden_fallback_detected": null,
    "human_diagnosis_summary": "normalizer did not find complete task evidence",
    "macro_adjustment_request_imported": false,
    "missing_dependency": null,
    "observed_route": "direct_execution",
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
    "reviewer_contract_citation": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/l1-l4-real-provider-lab/drafts/phase6b-l2-code-test-direct-execution.execution_contract.md",
    "role_boundary_violations": [],
    "round_result": "pass",
    "round_summary_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/logs/phase6b-l2-code-test-direct-execution__run_direct_execution_round.stdout",
    "route_decision_correct": true,
    "runtime_residue": {
      "config_dynamic_agents_absent": null,
      "dynamic_agents_absent": null,
      "observed_topology_residue_absent": null
    },
    "scope_shrink_detected": null,
    "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/run_l1_l4.sh",
    "script_sha256": "cd01a5da7ce5b27dfae3a1818b21d26f9f3b978870833b5feff3046a670e711d",
    "source_evidence_refs": [],
    "step_files_present": false,
    "task_id": "phase6b-l2-code-test-direct-execution",
    "test_command": "python -m unittest tests/test_calculator.py",
    "test_result": "unknown",
    "worker_reviewer_ask_success": true
  },
  {
    "ask_reachability": true,
    "authority_checks": {
      "communication_edges_absent": true,
      "no_source_checkout_edits": true,
      "provider_reply_authority_parsing_absent": true,
      "script_owned_round_imports": true,
      "script_owned_route_imports": true,
      "topology_dispatch_absent": true
    },
    "authority_write_violations": [],
    "blocker_evidence_imported": false,
    "changed_files": [],
    "classification": "test_design_failure",
    "cleanup_result": "unknown",
    "command_log_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/phase6b_l1_l4_command_log.jsonl",
    "complexity_level": "L3",
    "conflicting_decision_refs": [],
    "detail_design_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/supervisor_imports/phase6b-l3-needs-detail-source-inspection/detail_design.md",
    "detail_packet_imported": true,
    "detail_packet_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/supervisor_imports/phase6b-l3-needs-detail-source-inspection/detail_packet.md",
    "detail_summary_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/supervisor_imports/phase6b-l3-needs-detail-source-inspection/detail_summary.md",
    "detailer_activated_expected": true,
    "detailer_activated_observed": true,
    "execution_after_detail_ready": false,
    "expected_route": "needs_detail",
    "final_status": "detail_ready",
    "hidden_fallback_detected": null,
    "human_diagnosis_summary": "normalizer did not find complete task evidence",
    "macro_adjustment_request_imported": false,
    "missing_dependency": null,
    "observed_route": "needs_detail",
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
    "reviewer_contract_citation": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/l1-l4-real-provider-lab/drafts/phase6b-l3-needs-detail-source-inspection.execution_contract.md",
    "role_boundary_violations": [],
    "round_result": "detail_ready",
    "round_summary_path": null,
    "route_decision_correct": true,
    "runtime_residue": {
      "config_dynamic_agents_absent": null,
      "dynamic_agents_absent": null,
      "observed_topology_residue_absent": null
    },
    "scope_shrink_detected": null,
    "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/run_l1_l4.sh",
    "script_sha256": "cd01a5da7ce5b27dfae3a1818b21d26f9f3b978870833b5feff3046a670e711d",
    "source_evidence_refs": [
      "lab_code/config_summary.py",
      "lab_docs/l3_config_rules.md"
    ],
    "step_files_present": true,
    "task_id": "phase6b-l3-needs-detail-source-inspection",
    "test_command": null,
    "test_result": "not_applicable",
    "worker_reviewer_ask_success": null
  },
  {
    "ask_reachability": true,
    "authority_checks": {
      "communication_edges_absent": true,
      "no_source_checkout_edits": true,
      "provider_reply_authority_parsing_absent": true,
      "script_owned_round_imports": true,
      "script_owned_route_imports": true,
      "topology_dispatch_absent": true
    },
    "authority_write_violations": [],
    "blocker_evidence_imported": false,
    "changed_files": [],
    "classification": "test_design_failure",
    "cleanup_result": "unknown",
    "command_log_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/phase6b_l1_l4_command_log.jsonl",
    "complexity_level": "L4",
    "conflicting_decision_refs": [
      "decisions/020-mount-topology-and-ask-first-orchestration.md"
    ],
    "detail_design_path": null,
    "detail_packet_imported": false,
    "detail_packet_path": null,
    "detail_summary_path": null,
    "detailer_activated_expected": false,
    "detailer_activated_observed": false,
    "execution_after_detail_ready": false,
    "expected_route": "macro_adjustment_request",
    "final_status": "replan_required",
    "hidden_fallback_detected": false,
    "human_diagnosis_summary": "normalizer did not find complete task evidence",
    "macro_adjustment_request_imported": true,
    "missing_dependency": null,
    "observed_route": "macro_adjustment_request",
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
    "reviewer_contract_citation": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/l1-l4-real-provider-lab/drafts/phase6b-l4-macro-adjustment-request.execution_contract.md",
    "role_boundary_violations": [],
    "round_result": "macro_adjustment_request",
    "round_summary_path": null,
    "route_decision_correct": true,
    "runtime_residue": {
      "config_dynamic_agents_absent": null,
      "dynamic_agents_absent": null,
      "observed_topology_residue_absent": null
    },
    "scope_shrink_detected": false,
    "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/run_l1_l4.sh",
    "script_sha256": "cd01a5da7ce5b27dfae3a1818b21d26f9f3b978870833b5feff3046a670e711d",
    "source_evidence_refs": [],
    "step_files_present": false,
    "task_id": "phase6b-l4-macro-adjustment-request",
    "test_command": null,
    "test_result": "not_applicable",
    "worker_reviewer_ask_success": null
  },
  {
    "ask_reachability": true,
    "authority_checks": {
      "communication_edges_absent": true,
      "no_source_checkout_edits": true,
      "provider_reply_authority_parsing_absent": true,
      "script_owned_round_imports": true,
      "script_owned_route_imports": true,
      "topology_dispatch_absent": true
    },
    "authority_write_violations": [],
    "blocker_evidence_imported": true,
    "changed_files": [],
    "classification": "test_design_failure",
    "cleanup_result": "unknown",
    "command_log_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/phase6b_l1_l4_command_log.jsonl",
    "complexity_level": "L4",
    "conflicting_decision_refs": [],
    "detail_design_path": null,
    "detail_packet_imported": false,
    "detail_packet_path": null,
    "detail_summary_path": null,
    "detailer_activated_expected": false,
    "detailer_activated_observed": false,
    "execution_after_detail_ready": false,
    "expected_route": "blocked",
    "final_status": "blocked",
    "hidden_fallback_detected": false,
    "human_diagnosis_summary": "normalizer did not find complete task evidence",
    "macro_adjustment_request_imported": false,
    "missing_dependency": "PHASE6B_LAB_PRIVATE_API_TOKEN",
    "observed_route": "blocked",
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
    "reviewer_contract_citation": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/l1-l4-real-provider-lab/drafts/phase6b-l4-blocked-missing-secret.execution_contract.md",
    "role_boundary_violations": [],
    "round_result": "blocked",
    "round_summary_path": null,
    "route_decision_correct": true,
    "runtime_residue": {
      "config_dynamic_agents_absent": null,
      "dynamic_agents_absent": null,
      "observed_topology_residue_absent": null
    },
    "scope_shrink_detected": false,
    "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/run_l1_l4.sh",
    "script_sha256": "cd01a5da7ce5b27dfae3a1818b21d26f9f3b978870833b5feff3046a670e711d",
    "source_evidence_refs": [],
    "step_files_present": false,
    "task_id": "phase6b-l4-blocked-missing-secret",
    "test_command": null,
    "test_result": "not_applicable",
    "worker_reviewer_ask_success": null
  }
]
```

## Authority Checks

```json
{
  "communication_edges_absent": true,
  "no_source_checkout_edits": true,
  "provider_reply_authority_parsing_absent": true,
  "script_owned_round_imports": true,
  "script_owned_route_imports": true,
  "topology_dispatch_absent": true
}
```

## Failure Taxonomy

```json
{
  "pass": 0,
  "provider_failure": 0,
  "role_failure": 0,
  "system_failure": 0,
  "test_design_failure": 5,
  "valid_non_success": 0
}
```

## Complexity Breakpoint

unknown_pending_reviewer_rework_partial
