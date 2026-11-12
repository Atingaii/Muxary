# Parallel Roadmap Lanes And Planner Authority

Date: 2026-07-15
Status: Design accepted; implementation not started

## Purpose

Define how Plan Tree, planner, runtime lanes, worktrees, and integration gates
manage serial and parallel project work without creating multiple competing
plan authorities.

The central rule is:

> Parallelism belongs to the roadmap and lane model first. Planner instance
> count is a later scaling choice.

## Current Baseline

Current source already provides useful lower-level pieces:

- per-task file locks;
- one loop lease per running task;
- dynamic role profiles and bounded instance counts;
- generated loop/agent identities;
- worker Git-worktree support;
- mount topology and dynamic release.

Current source remains serial at project scope:

- `loop_runner_auto` holds one project-wide `auto-runner.lock`;
- `find_first_actionable_task` returns one selected task;
- the planner role design assumes one macro planner;
- isolated worker changes are promoted toward one shared project root;
- no lane registry, ready-frontier scheduler, scope-claim authority, or merge
  queue exists.

These constraints must be treated as implementation gaps, not hidden by
raising planner or worker `max_instances`.

## Three Planning And Execution Graphs

### Roadmap Graph

Durable macro graph under Plan Tree:

```text
goal
  -> milestone-1
      -> feature-a-1 -> feature-a-2 --+
      -> feature-b-1 -> feature-b-2 --+-> integration-ab -> milestone-2
```

It owns:

- macro goals and milestones;
- serial dependencies;
- parallel branch eligibility;
- priority and pause/resume intent;
- semantic scope claims and cross-lane conflicts;
- join nodes and integration acceptance;
- mapping from roadmap node to plan/task refs.

### Orchestration Graph

One accepted macro task may contain a smaller worker DAG. Decision 022 keeps
that graph in one orchestration bundle. It cannot add, remove, or reorder
Roadmap Graph nodes without a planner-owned graph change.

### Git/Worktree Graph

Controller projection of executable roadmap branches into concrete branches,
worktrees, base commits, integration order, and merge evidence. Plan Tree
describes semantic parallelism; controller decides safe physical materialization.

## Durable Representation

Keep human semantics and machine scheduling separate:

```text
docs/plantree/plans/<plan>/
  roadmap.md              # human goals, rationale, phases, tradeoffs
  roadmap.graph.json      # script-owned scheduling graph
  brief.md
  tasks/
```

Suggested graph node:

```json
{
  "id": "feature-a",
  "type": "workstream",
  "status": "ready",
  "priority": 50,
  "depends_on": [],
  "parallel_group": "milestone-1",
  "scope_claim_refs": ["scope-claims/feature-a.json"],
  "join_at": "integration-ab",
  "workspace_policy": "isolated",
  "acceptance_refs": ["acceptance.md#feature-a"],
  "plan_ref": "../feature-a/README.md"
}
```

Initial join semantics should stay simple: all required predecessor nodes must
complete. More general `any` or quorum joins are deferred until a real use case
requires them.

## Workflow Lane

A lane is a runtime binding for one active Roadmap Graph branch:

```text
.ccb/runtime/lanes/<lane-id>/
  lane.json
  planner-lease.json
  scope-claims.json
  dependencies.json
  capacity.json
  integration-contract.json
  runner.lock
```

Minimum identity carried by every ask, callback, import, and evidence record:

```text
project_id
plan_id
lane_id
roadmap_node_id
task_id
loop_id
round_id
activation_id
plan_revision
task_revision
base_commit
lease_fence
```

Missing or mismatched identity rejects the write. A late provider reply cannot
mutate a reassigned lane after its fencing token changes.

## Ready Frontier

The project scheduler computes executable nodes without semantic inference:

```text
ready_frontier = nodes where
  status is ready
  and all dependencies are complete
  and no active scope claim conflicts
  and required capacity is available
  and the lane is not paused
```

The scheduler may start all safe frontier nodes concurrently. It does not
rewrite dependencies, lower acceptance, shrink scope, or serialize a declared
parallel branch silently. Capacity or conflict prevents admission and produces
an explicit waiting reason.

## Project-Unique Topology Controller

Semantic orchestration is lane-scoped; physical topology authority is
project-scoped.

```text
Lane A orchestrator -> bundle A -> topology intent A --+
                                                    +-> project Topology Controller
Lane B orchestrator -> bundle B -> topology intent B --+
```

Each lane keeps independently attributable desired/observed topology state.
One project Topology Controller validates the combined physical resource view,
binds logical roles to concrete agents, creates fresh immaculate activations,
places them in role-class windows, reconciles mount state, and releases only
matching lane-owned agents.

The controller is deterministic program code, not an Agent. It cannot split
tasks, write worker prompts, change roadmap priority, rewrite bundles, judge
quality, or import semantic success. Dispatch remains a separate controller
responsibility after topology returns concrete ready bindings.

Project-wide uniqueness prevents capacity, agent-name, tmux, sidebar,
workspace, and release races. It must use short reconcile transactions rather
than one project lock held while providers work. See
[Decision 024](../decisions/024-project-topology-controller-and-single-lane-first.md).

## Serial And Parallel Semantics

| Condition | Scheduling result |
| :--- | :--- |
| `depends_on` predecessor incomplete | Serial wait |
| Independent scope and sufficient capacity | Parallel admission |
| Read/read scope overlap | Parallel admission |
| Read/write overlap | Admit only with pinned revision and stale-read policy |
| Write/write overlap | Serialize, combine, or request planner decision |
| Shared schema, public interface, release metadata, or migration | Exclusive claim or global review |
| Required join predecessors complete | Enter integration gate |

File-path comparison is insufficient. Claims should cover files, modules,
interfaces, schemas, commands, generated outputs, test resources, ports,
databases, and release surfaces.

## Planner Model

### Default: one global planner

One planner can maintain many roadmap branches because it is not active during
normal execution. It creates or revises graph nodes, then controller code
advances them.

Planner activates only for:

- new macro intake;
- branch creation, cancellation, or reprioritization;
- semantic scope conflict;
- partial or replan result;
- global-impact request;
- failed integration gate;
- next-milestone decision.

Normal child worker/reviewer success and dynamic release update script-owned
projections without another Planner call. The final required child transition
is different: Decision 029 adds one task-set join and one revision-fenced
Planner closure backfill so a completed macro request can update Roadmap,
Brief, TODO, and next-milestone authority exactly once.

### Optional: scoped lane planners

Multiple planner instances are justified only when planning queue latency,
independent domains, multiple users, or long-running research become measured
bottlenecks.

Rules:

- one active planner writer per plan root or explicit lane scope;
- one global planner writer for portfolio and shared architecture;
- lane planners write only their own plan root;
- global changes use `portfolio-change-request` artifacts;
- planner conversations remain lane-scoped even when they share one RolePack;
- no planner holds a file lock while a provider is reasoning.

The same `agentroles.ccb_planner` RolePack may support `portfolio` and `lane`
activation modes. A new required role id is not needed until behavior or
permissions prove materially different.

## Global Plan Tree Control Prerequisite

Decision 031 owns global Plan Tree consistency. Planner reasoning runs without
a lock and returns a proposal. One repository control holder validates typed
authority refs, revisions, closure digest, generation/fence, and writer scope
before the registered control workspace can publish the target ref. A lane's
local `docs/plantree` checkout is a snapshot, not another writer.

Locator election, holder handoff/takeover, task-store migration, proposal
transactions, external contract refs, freshness, and integration recovery are
defined only in
[global-plan-tree-authority-and-cross-worktree-control.md](global-plan-tree-authority-and-cross-worktree-control.md).
The legacy storage/projection cutover is isolated in
[global-plan-tree-storage-and-projection-migration.md](global-plan-tree-storage-and-projection-migration.md).

Global roadmap and architecture retain one semantic writer by default. Lane
status dashboards are derived from lane authority rather than rewritten by
every planner.

## Code Worktrees

Planner instances do not need code worktrees merely to reason. Executable
Roadmap nodes use isolated workspaces:

Executable lanes use code worktrees:

| Roadmap node | Workspace policy |
| :--- | :--- |
| Planning/document authority only | No code worktree |
| Serial implementation in one lane | Reuse lane worktree when safe |
| Independent concurrent implementation | Separate lane worktree |
| Exclusive shared surface | Serialize or create a joint lane |
| Integration join | Dedicated integration worktree |

Workers receive an immutable execution snapshot containing plan/task revision,
base commit, task envelope, acceptance refs, and digests. A moving global plan
cannot silently alter an active execution round.

## Integration Gate

Lane-local pass means `implementation_done`, not global `done`.

```text
lane A reviewed --+
                  +-> hidden candidate -> combined tests -> target promotion
lane B reviewed --+                                    -> published
```

Integration is intentionally serialized for a shared target branch. Lane-local
pass is not global completion. The gate records one integration id, hidden
candidate, conflict handling, combined verification, target promotion, Plan
Tree transition, publication, and unresolved global impact. Dependent nodes
wait for `published`; exact saga and recovery semantics live in the global
control protocol.

## Project Scheduler And Locks

Replace one long project-wide runner lock with:

- a short project scheduler transaction lock;
- one runner lock per lane;
- existing task locks and loop leases;
- short topology/capacity transactions;
- one integration lock per target branch.

Provider calls never hold the project scheduler lock. One lane may plan while
another executes, reviews, waits for integration, or releases agents.

## UI Projection

Keep role-class windows, but label every dynamic pane and sidebar item with its
lane:

```text
[A] planner
[A] orchestrator
[A] coder-1
[B] planner
[B] coder-1
```

Window 1 remains frontdesk/detail interaction, Window 2 holds planner and
planning-stage immaculate roles, and Window 3+ holds execution roles. Existing
six-pane overflow rules can create additional role-class windows. The sidebar
should group or filter by lane so visibility does not become cross-lane
ambiguity.

## Implementation Sequence

0. Close and freeze the current single-lane real-provider workflow baseline;
   do not start multi-lane source changes before its visible end-to-end,
   recovery, freshness, authority, release, and repeatability gates pass.
1. Complete the global control protocol's identity/election, fail-closed lock,
   task-store migration, typed authority, transaction, and freshness slices;
   pass acceptance-matrix sections A, B, and E.
2. Add Roadmap Graph schema, cycle validation, and deterministic ready-frontier
   input projection.
3. Add the shared lane registry, immutable snapshots, identity propagation,
   scope claims, and deterministic conflict admission.
4. Replace first-actionable selection with ready-frontier scheduling and split
   the project runner lock into short scheduler and per-lane locks.
5. Add hidden integration candidates, combined verification, target promotion,
   publication recovery, and dependent-admission fences.
6. Add lane-aware topology names, UI/sidebar projection, and capacity fairness.
7. Pass all fake and real rows in the cross-worktree acceptance matrix.
8. Measure planner/control queue latency before enabling scoped semantic
   planners; keep one physical authority commit stream.

## Acceptance Criteria

- Two disjoint ready branches execute concurrently while one lane failure does
  not stop the other.
- Same-scope writes cannot run concurrently without explicit conflict
  resolution, and dependency edges cannot admit before predecessor publication.
- No ask, callback, artifact, worktree change, topology record, integration, or
  cleanup action crosses lane identity.
- Stale authority, holder, task, provider, and integration writes fail closed.
- Global completion requires the exact hidden candidate, combined verification,
  target promotion, Plan Tree transition, event publication, and cleanup policy.

The falsifiable case-by-case gate is
[global-plan-tree-cross-worktree-acceptance-matrix.md](global-plan-tree-cross-worktree-acceptance-matrix.md);
this summary cannot waive one of its forbidden states.

## Related

- [../decisions/023-roadmap-graph-and-workflow-lanes.md](../decisions/023-roadmap-graph-and-workflow-lanes.md)
- [../decisions/024-project-topology-controller-and-single-lane-first.md](../decisions/024-project-topology-controller-and-single-lane-first.md)
- [../decisions/031-global-plan-tree-authority-across-worktrees.md](../decisions/031-global-plan-tree-authority-across-worktrees.md)
- [global-plan-tree-authority-and-cross-worktree-control.md](global-plan-tree-authority-and-cross-worktree-control.md)
- [global-plan-tree-storage-and-projection-migration.md](global-plan-tree-storage-and-projection-migration.md)
- [global-plan-tree-cross-worktree-acceptance-matrix.md](global-plan-tree-cross-worktree-acceptance-matrix.md)
- [planner-role-design.md](planner-role-design.md)
- [state-and-script-contract.md](state-and-script-contract.md)
- [plan-and-runtime-list-structure.md](plan-and-runtime-list-structure.md)
- [semantic-orchestration-and-controller-boundary.md](semantic-orchestration-and-controller-boundary.md)
