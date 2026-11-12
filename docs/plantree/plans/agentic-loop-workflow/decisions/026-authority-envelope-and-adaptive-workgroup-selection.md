# 026 Authority Envelope And Adaptive Workgroup Selection

Date: 2026-07-11
Status: Accepted for F1 implementation

## Context

Decision 025 makes one task with one to four reviewed workgroups the current
release gate. The first G1 foundation can import and validate a one-to-four
node orchestration bundle, but it intentionally pauses multi-node execution.
Several authority interfaces must be frozen before the runtime, Config V3,
and RolePack packages can proceed independently:

- task records do not yet expose a monotonic semantic revision;
- normalized bundles do not bind an effective capacity digest;
- provenance currently participates in the semantic bundle digest;
- a missing provider bundle is always synthesized as one node, which would
  silently collapse a Config V3 task that should have been decomposed;
- ask submission intent and parts of stage state remain scalar;
- complexity and cutability are not explicit evidence for selecting one to
  four workgroups.

## Decision

### Task Revision

Every task record has a positive integer `task_revision`.

- New tasks start at revision `1`.
- Existing task records without the field are read as revision `1` and are
  materialized under the task lock on their next authoritative mutation.
- The semantic input set is exactly `task_packet`, `execution_contract`,
  `detail_design`, `detail_summary`, `detail_packet`, and
  `orchestration_notes` for bundle V1.
- Importing a byte-identical semantic artifact is idempotent and does not
  increment the revision. Replacing one with a different digest increments
  the revision exactly once under the task lock.
- Bundle, node, integration, round, status, topology, and release evidence do
  not increment the task revision.
- Managed role-output imports carry the task revision captured at activation.
  A stale activation cannot mutate a newer task revision.
- Semantic input replacement while a task is bound to a running loop is
  rejected. Structural replan first ends or pauses the old execution
  authority, then imports revised inputs and creates a new bundle revision.

`task_revision` is an ordering/fencing value. `task_digest` remains the
canonical digest of the semantic artifact refs and hashes; neither replaces
the other.

### Effective Capacity Snapshot

Before bundle import, scripts compile
`ccb.loop.effective_capacity_snapshot.v1`. The canonical snapshot contains no
timestamps, host paths, secrets, pane ids, or provider session state. Its
digest is SHA-256 over sorted canonical JSON and binds:

- config version and workflow profile/mode;
- `max_workgroups`, `max_parallel_workgroups`, and
  `max_active_dynamic_agents`;
- node rework, workspace/integration, release, naming, and execution-window
  policies that can change bundle admissibility or execution behavior;
- required resident and dynamic logical profiles with effective RolePack id,
  provider, model, workspace mode, release policy, and `max_instances`;
- profile aliases that affect logical-role resolution.

Config V2 compiles a compatibility snapshot with
`max_workgroups = 1` and `max_parallel_workgroups = 1`; its existing physical
`loop.capacity.max_nodes` meaning is preserved. Config V3 exposes the explicit
semantic and physical limits from its workflow runtime config. A controller
must reject a bundle whose bound capacity digest no longer matches current
effective config. It does not silently reduce node count or serialize a graph
to fit drifted capacity.

### Candidate And Normalized Bundle

An explicit candidate remains provider evidence. Scripts bind current task and
capacity authority while normalizing it.

The candidate root adds one required `selection` object:

```json
{
  "workgroup_count": 1,
  "complexity": "atomic|bounded|complex|very_complex",
  "cutability": "none|limited|high",
  "execution_shape": "single_unit|parallel|serial|mixed_dag",
  "rationale": "short semantic reason for the chosen node count"
}
```

`workgroup_count` must be an integer from one to four and must equal the
candidate node count.

The normalized `ccb.loop.orchestration_bundle.v1` root is exactly:

```text
schema
task_id
task_revision
task_digest
capacity_digest
bundle_revision
selection
nodes
integration
policy
```

`source`, provider job id, source reply digest, actor, and import timestamp are
artifact provenance and do not participate in the semantic bundle digest. The
artifact record retains all of them, plus the capacity snapshot and its
digest. Re-importing identical semantics is idempotent even when provenance
differs. A different bundle for the same task and bundle revision conflicts.

`bundle_revision` is monotonic per task. Revision `1` is the first accepted
bundle. Structural replan requires the next revision and a fresh immaculate
orchestrator activation; stale or skipped revisions reject.

### Adaptive One-To-Four Selection

The immaculate orchestrator selects the node count from task semantics. The
controller validates; it never invents a decomposition or rewrites the count.

- Use one workgroup when the task is atomic, tightly coupled, or cannot expose
  independently reviewable scopes and acceptance checks.
- Use two to four workgroups only when each node has a complete work packet,
  bounded allowed paths, independent review evidence, and explicit
  dependencies where scopes or outputs interact.
- Choose the smallest count that preserves useful concurrency and ownership.
  Do not split work merely to fill configured capacity.
- Independent nodes require disjoint scopes. Coupled scopes require a DAG
  dependency and run from accepted predecessor integration state.
- Capacity is a ceiling, not a requested count.

Config V2 may omit a candidate only on the legacy route-only direct-execution
surface. Scripts then create one explicit
`v2_single_workgroup_compatibility` bundle using the same normalized node
kernel. Config V3 always requires an explicit candidate, including one-node
tasks. Missing, malformed, over-capacity, or semantically invalid V3 bundles
block before loop bind; they never fall back to one group.

Real acceptance prompts describe ordinary implementation work and never name
the desired workgroup count. The observed count must come from the imported
orchestrator candidate and its selection evidence.

### Node State And Exact-Once Intent

The sole round authority is
`ccb.loop.workgroup_round_state.v1`, keyed by canonical node id. Scalar
worker/reviewer fields may remain as read-only compatibility projections for
one-node output during migration, but they are never transition authority.

Node statuses are:

```text
created
worker_intent
worker_submission_unknown
worker_pending
worker_failed
worker_complete
reviewer_intent
reviewer_submission_unknown
reviewer_pending
reviewer_rework
review_failed
review_passed
integration_ready
integrated
blocked
released
```

Round/controller statuses are:

```text
bundle_pending
topology_pending
executing
integration_pending
project_verification_pending
round_review_pending
pass
partial
replan_required
blocked
```

Submission intents are append-only records in the task/loop namespace. Their
identity is exactly `(bundle_revision, node_id, purpose, attempt)`, where
purpose is one of `worker`, `reviewer`, `worker_rework`, `reviewer_recheck`, or
`round_reviewer`; round review uses reserved node id `round`. Intent lifecycle
is `prepared -> accepted -> terminal -> consumed`, with `unknown` as a
non-retriable diagnostic state until authoritative job evidence resolves it.
Job id binds once. Duplicate or stale callbacks are idempotent and cannot move
a newer attempt.

### Result Mapping And Ownership

- `pass`: every required node is reviewed and integrated, integration and
  project-root checks pass, round review passes, and script authority imports
  the result.
- `partial`: at least one reviewed node result is preserved as evidence, but
  the full required set cannot complete and the contract permits a useful
  partial outcome. No partial delta remains promoted as completed project-root
  work.
- `blocked`: the graph is structurally valid but an external or execution
  blocker prevents a safe deliverable.
- `replan_required`: task semantics, bundle structure, scope, capacity,
  dependency, or integration conflict requires a new task/bundle decision.
- submission-unknown and provider-pending states remain pending; elapsed
  business time is not a result.
- controller/runtime failures remain explicit system failures and cannot be
  normalized to a task pass.

The orchestrator owns one semantic candidate per bundle revision. The
deterministic controller owns concrete agents, asks, state, Git integration,
promotion, rollback, result import, and release. The normal worker-complete
path never asks an orchestrator again. Only structural replan creates a fresh
orchestrator activation.

## F1 Rejection And Compatibility Gate

F1 implementation is complete only when tests prove:

- task revision increments, idempotence, stale activation rejection, and
  running-loop mutation rejection;
- capacity snapshot/digest stability and drift rejection for V2 and V3;
- provenance changes do not change bundle digest;
- explicit candidates support exactly one to four nodes and selection count
  equals node count;
- V2 route-only omission produces one compatibility node, while V3 omission
  blocks;
- node-map state is transition authority and intent identity is node/purpose/
  attempt scoped;
- one-node behavior remains compatible without a separate scalar engine;
- normal pass has no post-worker orchestrator activation.

## Consequences

- Wave 1 packages can share stable task, capacity, bundle, state, and intent
  interfaces without copying private helpers.
- Config V3 can advertise four workgroups only after the runtime and visible
  real-provider gates prove four.
- Adaptive fanout is inspectable semantic evidence, not a controller heuristic
  and not a test-script parameter.
- Existing Config V2 static users retain one-group workflow behavior.

## Related

- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [025-single-lane-multi-workgroup-release-gate.md](025-single-lane-multi-workgroup-release-gate.md)
- [../goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md)
- [../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md)
- [../topics/config-v3-dynamic-workflow.md](../topics/config-v3-dynamic-workflow.md)
