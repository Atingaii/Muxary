route: <direct_execution|needs_detail|macro_adjustment_request|blocked|partial_completion>
orchestration_notes: <compact rationale with supplied task and contract refs>

For Config V3 `direct_execution` or `partial_completion`, emit exactly one
candidate. Config V2 may omit it only for deterministic one-node
compatibility. Repeat the node object once per semantically justified
workgroup; do not use the displayed single object as a node-count preference.
Replace every angle-bracket placeholder before replying. Integer fields must
be JSON integers, not quoted placeholder strings.

Output the heading `orchestration_bundle:` exactly and immediately follow it
with a code fence whose language tag is literally `json`. The schema identifier
`ccb.loop.orchestration_bundle_candidate.v1` belongs only in the JSON object's
top-level `schema` field; never use it as the code-fence language. This format
is required for both one-node and multi-node bundles.

orchestration_bundle:
```json
{
  "schema": "ccb.loop.orchestration_bundle_candidate.v1",
  "task_id": "<task-id>",
  "bundle_revision": "<positive-integer-supplied-by-controller>",
  "selection": {
    "workgroup_count": "<integer-1-to-4-equal-to-node-count>",
    "complexity": "<atomic|bounded|complex|very_complex>",
    "cutability": "<none|limited|high>",
    "execution_shape": "<single_unit|parallel|serial|mixed_dag>",
    "rationale": "<one-line reason, at most 500 characters; target 300 or fewer>"
  },
  "nodes": [
    {
      "node_id": "<short-agent-name-safe-node-id-max-32-chars>",
      "workgroup_id": "<short-agent-name-safe-workgroup-id-max-32-chars>",
      "worker_profile": "coder",
      "reviewer_profile": "code_reviewer",
      "depends_on": ["<predecessor-node-id-if-any>"],
      "parallel_group": "<evidence-label-only>",
      "work_packet": "Goal: <bounded goal>\nDeclared refs: <task and contract refs>\nScope: <allowed work>\nNon-goals: <excluded work>\nDependencies: <accepted predecessor evidence or none>\nExpected evidence: <changed paths and checks>\nVerification: <bounded obligations>",
      "allowed_paths": ["<project-relative-path>"],
      "acceptance_refs": ["<known-artifact-ref>"],
      "verification_refs": ["<known-artifact-ref>"],
      "integration_order": "<unique-positive-integer>"
    }
  ],
  "integration": {
    "verification_refs": ["<known-artifact-ref>"],
    "project_root_verification_refs": ["<known-artifact-ref>"]
  },
  "policy": {
    "max_node_rework_rounds": "<non-negative-integer-within-policy>",
    "on_required_node_failure": "partial_or_blocked",
    "on_structural_failure": "replan_required"
  }
}
```

Candidate root fields are exactly the seven fields shown. Capacity is a
ceiling, not a target. Structural ambiguity is `replan_required`; never hide it
with serialization, node-count reduction, scope shrinkage, or fallback.
Disjoint independently testable units that rely only on already declared
interfaces belong in separate ready nodes. A shared API, package, final root
test, or product outcome is not enough reason to merge them. For a one-node
selection, the rationale must name the concrete path overlap or predecessor
evidence dependency that prevents independent review.
Verification refs must point to artifacts with `Verification:` or
`Verification Commands:` bullet entries that are direct argv commands executed
without a shell. Do not use `Verification Contract:` prose as executable
verification evidence.

Use the policy literal values exactly as shown: `on_required_node_failure` is
`partial_or_blocked` and `on_structural_failure` is `replan_required`. Do not
substitute semantic alternatives such as rework, retry, fail, or
return_failed_node_for_rework.
Both integration arrays must be non-empty. For one-node bundles, copy the
execution-contract artifact ref into both `verification_refs` and
`project_root_verification_refs`; never leave project-root verification empty.
