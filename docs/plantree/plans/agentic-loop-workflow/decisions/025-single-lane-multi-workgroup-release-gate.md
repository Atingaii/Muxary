# 025 Single-Lane Multi-Workgroup Release Gate

Date: 2026-07-10
Status: Accepted for current release target

## Context

The current direct-execution path has strong single-workgroup evidence, but its
runtime state is still centered on one generated `coder`, one
`code_reviewer`, one scalar worker result, one scalar reviewer result, and one
post-execution orchestrator summary. Existing multi-node evidence proves
capacity, placement, pane overflow, and release mechanics; it does not prove
that one real task can be split into several reviewed work units and integrated
without losing authority or recovery guarantees.

The next release must close this gap before multi-lane roadmap scheduling is
implemented. It must also introduce Config V3 as the opt-in dynamic workflow
control surface while preserving Config V2 as the static-layout contract.

## Decision

The next production and release gate is one Workflow Lane executing one macro
task through one semantic orchestration bundle containing between one and four
`Worker + Reviewer` workgroups.

- One immaculate orchestrator activation owns the complete bundle. There is
  not one orchestrator per workgroup and there is no second LLM task publisher.
- Every execution node is a paired workgroup: one worker writes in the
  node-scoped workspace and one reviewer evaluates that same node result.
- Independent nodes may run concurrently. `depends_on` defines deterministic
  execution waves for serial or mixed graphs.
- The deterministic controller validates the bundle, binds concrete agents,
  submits asks exactly once, resumes from durable terminal state, integrates
  reviewed node results, promotes the integrated delta, imports authority, and
  releases dynamic roles. It must not redesign the graph.
- The normal pass path does not reactivate an orchestrator after worker
  completion. A fresh orchestrator activation is allowed only for structural
  replan.
- A dedicated immaculate `ccb_round_reviewer` validates compact node-review,
  integration, project-root, and test evidence after script-owned integration.
- Mount topology remains physical mount/layout/lifecycle state only. Bundle
  dependencies and semantic task packets do not become topology dispatch
  edges, gates, or artifacts.

The one-workgroup path must use the same generalized bundle/state-machine
engine through a deterministic one-node bundle. The release must not retain a
second hard-coded execution engine.

## Workspace And Integration Boundary

Multi-workgroup execution in the first production release requires a Git
project and a clean declared execution scope.

- Each workgroup receives a node-scoped Git worktree and branch pinned to a
  recorded base commit.
- A worker and its reviewer share the node workspace identity; the reviewer is
  read/review-only by role contract.
- Parallel nodes in the first release must declare disjoint allowed-change
  paths. Overlap requires an explicit dependency or bundle validation fails.
- A controller-owned integration worktree merges reviewed node commits in
  deterministic topological and node-id order.
- Dependents begin from the accepted integration commit that contains all
  required predecessors.
- Merge conflicts, scope violations, dirty reviewed trees, and integration
  test failures are explicit failures. They are never hidden by automatic
  conflict resolution, silent serialization, or shared in-place writes.
- The integrated delta is promoted to the project root only after node review
  and integration verification. Project-root verification and round review
  follow. Any non-pass or unknown final result restores the pre-promotion
  snapshot.

Single-workgroup compatibility may keep the existing bounded workspace modes,
but it must still pass through the generalized node state and evidence model.

## Runtime And Recovery Boundary

- `ask` remains submit-once and callback/persisted-terminal driven. Provider
  completion has no business timeout that converts slow work into failure.
- Submission intent is keyed by `node_id`, purpose, and attempt. A crash before
  or after submission cannot silently duplicate an ask.
- Unknown submission state pauses as `ask_submission_unknown`; it cannot be
  converted to pass, resubmitted speculatively, or released as complete.
- Sibling work may continue when it is independent and its declared scope is
  safe. Dependents of a failed node remain frozen.
- Node rework is bounded by configuration. Structural changes return
  `replan_required` and require a new immaculate orchestration activation.
- Dynamic role release is ownership-scoped. Busy retain, partial release,
  retry, and final residue remain explicit evidence.

## Config And Release Boundary

- Config V2 remains the stable static-agent/static-window contract.
- Config V3 becomes the opt-in dynamic workflow contract.
- V3 requires resident `frontdesk` and `planner` role slots.
- V3 requires dynamic profiles for `task_detailer`, `orchestrator`, `coder`,
  `code_reviewer`, and `ccb_round_reviewer`, including provider/model/default
  resolution and installed RolePack validation.
- V3 uses unambiguous workgroup and dynamic-agent limits; it must not overload
  the existing `max_nodes` field to mean both semantic nodes and agent count.
- V3 and V2 static authority fields cannot be mixed.

No new package is published until the multi-workgroup engine, V3 config,
source/fake tests, visible real-provider opened-project tests, packaging,
fresh-install, upgrade, and rollback gates all pass from one clean release
commit. The final package version and npm publication command remain explicit
release-time decisions; no version is guessed or reused during implementation.

## Consequences

- The first production fanout target is within one task lane, not concurrent
  roadmap lanes.
- Capacity is measured in workgroups and physical dynamic agents separately.
- Project-root mutation becomes an integration result, not a side effect of
  each parallel worker.
- Existing single-pair behavior becomes a compatibility case of the new
  engine and remains regression protected.
- A release claim must state the largest real-provider workgroup count actually
  proven. Supporting four workgroups requires a visible real four-workgroup
  acceptance run; otherwise configuration must reject a larger value.
- Workers or reviewers may be delegated concrete source fixes, but `talk2`
  directly owns validation, raw-evidence audit, and release acceptance.

## Related

- [021-immaculate-role-context-lifecycle.md](021-immaculate-role-context-lifecycle.md)
- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [024-project-topology-controller-and-single-lane-first.md](024-project-topology-controller-and-single-lane-first.md)
- [../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md)
- [../topics/config-v3-dynamic-workflow.md](../topics/config-v3-dynamic-workflow.md)
