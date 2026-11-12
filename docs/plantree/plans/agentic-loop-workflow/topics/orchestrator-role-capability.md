# Orchestrator Role Capability

Date: 2026-06-24

## Purpose

`orchestrator` is the loop-internal semantic workgraph planner. It is activated
by `loop_runner` through `ask` only when a task cannot use the validated
single-unit execution template. It turns an execution-ready task packet into
one complete orchestration bundle: bounded work items, dependencies, logical
role assignments, complete task packets, review/integration intent, and
capacity intent.

It is not a daemon, not a permanent manager, and not the owner of runtime state.
It does not physically publish asks. CCB scripts validate the bundle, bind
logical roles to concrete mounted agents, submit asks exactly once, import
results, and reconcile topology and lifecycle.

The current boundary is governed by
[Decision 022](../decisions/022-semantic-orchestration-bundle-and-controller-execution.md)
and the
[semantic orchestration/controller topic](semantic-orchestration-and-controller-boundary.md).

## Context Purity

`orchestrator` is an immaculate (`无垢`) role. It is allowed to reason deeply
inside one task triage or execution-round dispatch, but the next activation must
start from durable task refs, loop refs, topology refs, and imported evidence,
not from the prior orchestration conversation.

This applies even when the orchestrator pane is visually resident in the
foreground. Pane visibility is an observability affordance; it is not permission
to retain semantic memory across tasks or rounds. The runtime should use a new
provider session, a unique activation identity, or a proven clear/reset step for
each orchestration activation and record enough evidence to audit freshness.

## Activation Model

```text
loop_runner
  -> ask orchestrator
      inputs: task packet, verification contract, loop state refs, node budget
      outputs: orchestration bundle containing work items, dependency graph,
               logical role assignments, task packet refs, review policy,
               integration points, capacity intent, and dispatchable nodes
```

`orchestrator` should receive references, not large copied context:

- Durable task packet path.
- Planner handoff path.
- Acceptance criteria path.
- Verification contract path.
- Current loop breadcrumb.
- Existing node/branch status refs.
- Read-only capacity envelope and current mount constraints.

`orchestrator` may read the referenced documents, reason semantically, and
produce draft artifacts. It must ask CCB scripts to record authoritative state.

## Core Capabilities

### 1. Task Complexity Assessment

Classify the current execution task before slicing:

| Class | Meaning | Default Node Count |
| :--- | :--- | :--- |
| `single` | One bounded implementation path, low cross-module risk | 1 |
| `split_serial` | Several dependent steps; parallelism would create rework | 1-2 |
| `split_parallel` | Independent work items can run safely in parallel | 2-4 |
| `replan_required` | Task is too vague, too broad, or acceptance criteria are not executable | 0 |

Complexity signals:

- Number of affected modules.
- Cross-module dependency risk.
- Need for domain specialization.
- Test surface breadth.
- Whether work items can be independently verified.
- Whether partial branch completion is useful.
- Whether shared files would create merge or semantic conflicts.

Hard limits:

- V1 node count must be between 1 and 4.
- Prefer 1 node unless parallelism clearly reduces risk or wall time.
- If more than 4 nodes seem necessary, return `replan_required` with a smaller
  task-splitting recommendation.

### 2. Work Item Slicing

Produce work items that are:

- Bounded.
- Testable.
- Independently reviewable.
- Traceable to acceptance criteria.
- Small enough for one `coder + checker` node.

Each work item should include:

```json
{
  "work_item_id": "wi-001",
  "title": "Implement config parser guard",
  "goal": "Make project config parsing fail visibly instead of falling back",
  "scope": ["lib/agents/config_loader_runtime"],
  "non_goals": ["rewrite config grammar"],
  "acceptance_refs": ["acceptance-criteria.md#config-visible-failure"],
  "verification_refs": ["verification-contract.md#real-cli-smoke"],
  "depends_on": [],
  "expected_artifacts": ["summary", "changed_files", "tests", "risk_notes"],
  "assigned_node": "node-001"
}
```

### 3. Dependency Graph And Branch Control

Build a small DAG:

```json
{
  "nodes": ["node-001", "node-002"],
  "edges": [["node-001", "node-002"]],
  "branches": [
    {"branch_id": "branch-config", "root_node": "node-001"}
  ]
}
```

When a node is `non_converged`, orchestrator should:

- Freeze that node.
- Freeze dependent downstream nodes.
- Continue unrelated sibling work when safe.
- Return a partial package for planner when the round drains.

It must not downgrade the branch to success or silently remove it from scope.

### 4. Capacity Intent

Before activation, the controller supplies a read-only capacity envelope with
allowed role profiles, maximum instances, provider constraints, window
capacity, and lifecycle policy. The orchestrator designs against that envelope
and returns logical capacity intent as part of the bundle.

Allowed:

- request declared role profiles and counts;
- identify parallel branches and integration points;
- state the expected activation lifetime and evidence gates;
- return `replan_required` when the bounded capacity cannot safely execute the
  task.

Disallowed:

- choose concrete agent ids, windows, or panes;
- encode normal ask edges in mount topology;
- edit `.ccb/ccb.config` or runtime authority files;
- run reload, add, move, park, release, or kill commands;
- silently reduce parallelism after a capacity conflict.

The controller compiles accepted capacity intent into mount-only topology. If
capacity changes before dispatch, it returns `capacity_conflict`; it does not
rewrite the workgraph.

### 5. Logical Publication Intent

Each orchestration-bundle node includes everything needed for deterministic
physical publication:

- work item id and complete packet ref;
- required logical role profile;
- dependencies and dispatch readiness;
- scope, non-goals, acceptance, and verification refs;
- forbidden degradation rules;
- expected worker output and independent review contract;
- bounded rework and structural-escalation policy.

The orchestrator does not execute `ask`. The controller binds the logical role
to a concrete mounted instance, submits once, and records submission intent,
target, job id, and callback state. This preserves exact-once recovery without
introducing a second semantic task publisher.

### 6. Structural Replanning

Normal worker/reviewer success does not reactivate orchestrator. The controller
imports accepted evidence and advances according to the bundle.

An immaculate orchestrator is activated again only when semantic structure
must change, including:

- dependency graph invalidation;
- a new work unit or integration point;
- partial continuation requiring a new split;
- reviewer findings that exceed bounded node rework;
- changed capacity that cannot execute the accepted graph.

The new activation consumes durable node, review, and round evidence and emits
a new bundle revision. It does not rely on the previous provider conversation.

## Explicit Non-Authority

`orchestrator` must not:

- Modify durable plan-tree state directly.
- Modify runtime authority files directly.
- Start or stop providers directly.
- Submit worker or reviewer asks directly.
- Bind logical roles to concrete agent instances.
- Confirm user-facing scope changes.
- Lower acceptance criteria.
- Convert partial work into `done`.
- Override checker or round checker quality gates.
- Expand beyond the configured 1-4 node budget.

## V1 Cut

The target path is:

```text
planner -> loop_runner -> ask orchestrator
orchestrator -> orchestration bundle
loop_runner -> validate bundle and capacity intent
loop_runner/reconciler -> commit/reconcile mount topology
loop_runner -> submit asks to concrete ready targets exactly once
worker/reviewer -> return evidence through callback delivery
loop_runner -> import evidence and advance accepted graph
round/integration reviewer -> verify when policy requires
loop_runner/reconciler -> release/reconcile immaculate roles
planner/frontdesk -> receive partial/replan only when needed
```

The current source still implements earlier triage and ask-first paths. The
bundle path is a planning target and must not be described as landed until its
schema, controller, recovery, and real opened-project acceptance evidence exist.

## Role Pack Guidance

The `orchestrator` Role Pack should include:

- Role memory describing purpose, authorities, non-authorities, and V1 limits.
- A bundle skill for coupled work slicing, dependency design, logical role
  assignment, complete worker/reviewer packets, and capacity intent.
- No permission to run physical ask, topology, layout, lifecycle, reload, or
  provider-management commands.
- Templates for task envelopes, work items, dependency graphs, orchestration
  bundles, capacity intent, structural replan requests, and partial reports.
- References to:
  - `topics/plan-and-runtime-list-structure.md`
  - `topics/execution-node-and-round-verification.md`
  - `topics/state-and-script-contract.md`
  - `docs/plantree/plans/ccbd-agent-hot-reload/roadmap.md`
