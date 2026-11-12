# Semantic Orchestration And Controller Boundary

Date: 2026-07-10
Status: Design accepted; implementation not started

## Purpose

Define a coherent boundary across global planning, task detail, semantic
orchestration, physical dispatch, topology, review, and lifecycle. The design
must preserve global structure without making every logical responsibility a
serial provider call.

The central rule is:

> Keep work slicing, dependency design, logical assignment, and publication
> intent together. Separate only deterministic runtime side effects.

## Planning Scales

| Scale | Owner | Durable Output |
| :--- | :--- | :--- |
| Global plan and architecture | Long-lived planner | Plan brief, architecture map, invariants, cross-task dependencies, macro acceptance, integration milestones |
| Task-local source detail | Immaculate task detailer, only when needed | Detail packet, source evidence, local acceptance, global-impact result |
| Execution workgraph | Immaculate orchestrator, only when needed | Complete orchestration bundle |
| Concrete runtime placement | Controller and topology services | Agent binding, mount topology, observed readiness, lifecycle evidence |
| Implementation and verification | Immaculate workers and reviewers | Worker result, review result, tests, integration evidence |
| Global result rehydration | Scripts plus planner on trigger | Plan delta summary, coverage update, macro adjustment or milestone completion |

The planner must remain compact, but it cannot be only a roadmap or TODO
keeper. It owns the global structure against which local task success is
judged.

## Global Consistency Loop

Every macro task should carry a bounded task envelope:

```json
{
  "task_id": "task-123",
  "goal_refs": ["brief.md#goal-a"],
  "architecture_refs": ["architecture-map.md#storage-boundary"],
  "dependency_refs": ["task-087"],
  "invariants": ["no-provider-reply-authority"],
  "integration_checkpoint": "checkpoint-cli-storage",
  "acceptance_refs": ["acceptance-coverage.json#task-123"]
}
```

When detail is required, the task detailer produces local implementation
evidence plus a mandatory global-impact result:

```json
{
  "task_id": "task-123",
  "impact": "none | bounded | macro",
  "interfaces_touched": [],
  "dependencies_changed": [],
  "invariants_touched": [],
  "assumptions_invalidated": [],
  "acceptance_changes": [],
  "evidence_refs": []
}
```

The controller applies this gate:

- `none`: validate required fields and continue without another planner call;
- `bounded`: import a compact plan-delta summary and activate an integration
  review only when the touched surface requires it;
- `macro`: stop execution and reactivate planner to accept or reject the plan
  change.

`detail_ready` should be interpreted as local readiness. Execution requires a
separate global-consistency result. Implementation may represent these as
fields rather than adding many task statuses:

```text
local_readiness=ready
global_consistency=passed
execution_readiness=ready
```

## Orchestration Bundle

The orchestrator receives the accepted task envelope, execution contract,
detail packet when present, and a read-only capacity envelope. It returns one
bundle in one provider activation.

Minimum shape:

```json
{
  "schema": "ccb.loop.orchestration_bundle.v1",
  "task_id": "task-123",
  "revision": 1,
  "nodes": [
    {
      "id": "implement-storage",
      "role_profile": "coder",
      "packet_ref": "work-units/implement-storage.md",
      "depends_on": [],
      "acceptance_refs": [],
      "verification_refs": [],
      "review_role_profile": "code_reviewer",
      "completion_contract": "tests and review pass"
    }
  ],
  "integration_points": [],
  "dispatchable_nodes": ["implement-storage"],
  "rework_policy": {"max_rounds": 1},
  "capacity_intent": {"coder": 1, "code_reviewer": 1}
}
```

The bundle is the single semantic source for:

- task slicing;
- graph dependencies and parallelism;
- logical role assignment;
- worker and reviewer packets;
- integration and merge points;
- bounded rework and partial behavior.

No later component may repeat these decisions.

## Controller Contract

The runtime controller consumes the bundle as an execution instruction. It is
not a semantic agent.

Allowed controller actions:

1. Validate bundle schema, task revision, authority refs, and capacity intent.
2. Bind logical profiles to concrete allowed agent instances.
3. Commit and reconcile mount-only topology.
4. Wait for explicit mounted-agent readiness events.
5. Submit exactly one `ask` for every newly dispatchable node.
6. Persist submission intent, concrete target, job id, and callback state.
7. Resume from callback or persisted provider-job evidence without polling for
   semantic completion.
8. Import reviewed artifacts through script-owned commands.
9. Release eligible immaculate agents and record residue or busy retain.

Forbidden controller actions:

- re-slice a task;
- rewrite worker packets or acceptance criteria;
- replace a requested logical role with a different role;
- infer success from provider prose;
- silently serialize a parallel graph because capacity is missing;
- reduce scope or skip a blocked node;
- synthesize a pass when submission state is unknown.

## Physical Publication

The orchestrator owns publication intent. The controller owns the physical
side effect:

```text
bundle node role_profile=coder
  -> topology binding loop-coder-1
  -> controller submits ask once
  -> runtime ledger records job_id
```

This boundary is required for crash recovery, idempotence, project-path
validation, callback resume, and authority safety. It is not a second planning
step.

## Capacity Envelope

The controller snapshots allowed runtime capacity before semantic
orchestration:

```json
{
  "allowed_role_profiles": {
    "coder": {"max_instances": 3},
    "code_reviewer": {"max_instances": 2}
  },
  "max_dynamic_agents": 6,
  "window_capacity": 6,
  "provider_constraints": {},
  "lifecycle_policy": "immaculate-per-activation"
}
```

The orchestrator designs once against this envelope. A changed or unavailable
capacity state produces `capacity_conflict`; it does not authorize automatic
graph degradation.

## Activation Paths

### Single-unit fast path

```text
frontdesk -> planner task envelope
  -> deterministic direct-template eligibility gate
  -> controller mounts one worker/reviewer pair
  -> worker -> reviewer -> import -> release
```

The fast path is allowed only when the planner packet explicitly selects the
predefined single-unit template and deterministic validation proves bounded
scope, executable acceptance, known verification, no unresolved detail, and no
cross-task integration change.

### Orchestrated path

```text
frontdesk -> planner task envelope
  -> orchestrator emits complete bundle once
  -> controller dispatches all DAG-ready workers in parallel
  -> reviewers and integration gate
  -> import -> global delta -> release
```

### Detail path

```text
planner task envelope
  -> detailer emits detail packet + global impact
  -> global consistency gate
  -> orchestrator emits complete bundle
  -> controller executes
```

Detail and orchestration are serial only when the task has a real information
dependency. The detailer returns facts and constraints; it must not create a
competing task split that the orchestrator then repeats.

## Serial Depth Budget

Provider latency is governed by the longest dependency chain, not the number
of logical modules.

| Task shape | Target serial provider depth |
| :--- | :--- |
| Frontdesk-only answer | 1 |
| Validated single-unit project task | 4: frontdesk, planner, worker, reviewer |
| Multi-unit task with orchestration | 5: add one orchestrator activation |
| Task requiring source-backed detail | 6: add one detailer activation |
| Macro-impact task | 7 only when a second planner decision is required |

Workers on independent graph branches run in parallel. Topology, dispatch,
state import, and release add no provider calls. A future implementation should
record per-stage timings so a claimed optimization is based on the actual
critical path.

## Review And Completion

Independent review remains mandatory. Round-level or integration review may be
policy-triggered for multi-node, cross-module, partial, rework, migration,
security, or public-interface tasks. Whether the single-unit path may combine
node and round review into one independent review activation remains an
implementation-readiness question; latency alone cannot waive required
evidence.

After a round, scripts produce a compact global delta:

```json
{
  "task_id": "task-123",
  "result": "pass | partial | replan_required | blocked",
  "architecture_changes": [],
  "dependencies_completed": [],
  "invariants_verified": [],
  "acceptance_coverage_changes": [],
  "planner_activation_required": false
}
```

Local node pass cannot complete a macro milestone unless its required
acceptance coverage and integration checkpoint are satisfied.

## Failure Rules

- Unknown ask submission state pauses; it does not resubmit or pass.
- Capacity drift stops with `capacity_conflict`; it does not shrink the graph.
- Missing global-impact evidence stops a detail path before execution.
- A reviewer may request bounded node rework, but structural graph changes
  require a new immaculate orchestrator activation.
- Macro drift returns to planner; neither detailer nor orchestrator edits
  global plan authority directly.
- Dynamic agents release only after evidence import and idle checks.

## Implementation Delta

This document is a target design, not a statement of current runtime support.
The current source has proven orchestrator triage, ask-first direct execution,
task-detail import, mount-only topology, script-owned result import, dynamic
release, and visible immaculate-role activation. Future implementation still
needs:

- an authoritative orchestration-bundle schema and validator;
- a controller path that executes the bundle without semantic reinterpretation;
- a planner-selected, deterministic single-unit fast path;
- mandatory detail global-impact evidence and global-consistency gate;
- capacity-envelope snapshot and explicit conflict handling;
- global delta and acceptance-coverage import;
- real opened-project latency and multi-worker acceptance evidence.

## Acceptance Criteria For A Future Landing

- One orchestrator activation produces all semantic work units and logical
  assignments for a complex round.
- Controller tests prove no task re-slicing, packet rewriting, or silent role
  substitution.
- Crash-window tests prove exact-once physical publication and callback resume.
- Real opened-project evidence proves independent workers dispatch in parallel.
- Capacity drift produces explicit non-success without graph degradation.
- Detail paths cannot execute without global-impact evidence.
- Planner reactivation occurs only on declared global triggers, not every
  local pass.
- Dynamic immaculate roles release cleanly while frontdesk and planner remain
  resident and visible.

## Related

- [../decisions/022-semantic-orchestration-bundle-and-controller-execution.md](../decisions/022-semantic-orchestration-bundle-and-controller-execution.md)
- [planner-plan-tree-brief-and-detail-boundary.md](planner-plan-tree-brief-and-detail-boundary.md)
- [task-detailer-role-design.md](task-detailer-role-design.md)
- [orchestrator-role-capability.md](orchestrator-role-capability.md)
- [mount-topology-and-ask-first-orchestration.md](mount-topology-and-ask-first-orchestration.md)
- [state-and-script-contract.md](state-and-script-contract.md)
