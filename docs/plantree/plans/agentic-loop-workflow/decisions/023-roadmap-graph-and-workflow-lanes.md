# 023 Roadmap Graph And Workflow Lanes

Date: 2026-07-10
Status: Accepted for planning

## Context

The current workflow V1 uses one macro planner, a project-wide auto-runner
lock, and first-actionable-task selection. Dynamic worker capacity and
per-task locks exist, but they do not provide project-level concurrent
workflows.

Parallel product work is not primarily a question of how many planner agents
are mounted. It requires a durable model for serial dependencies, parallel
branches, scope conflicts, integration joins, runtime lanes, and isolated code
workspaces. Cloning the planner without these boundaries would create multiple
writers for the same roadmap and plan authority.

## Decision

Plan Tree gains a durable Roadmap Graph capable of representing serial and
parallel macro work. The default architecture uses one global planner to edit
that graph and a deterministic project scheduler to advance its ready
frontier.

A first-class Workflow Lane is the unit of concurrent execution. Each lane has
one plan scope, one planner writer lease, its own runtime namespace, task/loop
identity, capacity allocation, code worktree when implementation is required,
and integration contract.

Parallel execution does not require parallel planner activations. One planner
may create several ready roadmap branches and then remain idle while lane
controllers execute them concurrently. Planner is reactivated only for new
macro intent, graph changes, semantic conflicts, partial/replan outcomes,
priority changes, or failed integration gates.

## Graph Separation

CCB keeps three graphs distinct:

- Roadmap Graph: durable macro goals, tasks, dependencies, branches, joins,
  priorities, and integration gates; owned by Plan Tree and planner proposals.
- Orchestration Graph: task-local worker units and review/integration intent;
  owned by one Decision 022 orchestration bundle.
- Git/Worktree Graph: concrete branches, worktrees, base commits, merge order,
  and integration checkout; owned by controller code.

The graphs reference each other by stable ids but do not share authority.

## Planner Scaling

V1 parallel roadmap support starts with one global planner.

Multiple planner instances are a later throughput optimization, allowed only
across disjoint plan roots or explicit lane scopes. The invariant is:

```text
one plan scope = one active planner writer
one global roadmap = one global planner writer
```

Lane planners may submit global change requests but cannot directly edit the
portfolio roadmap, shared architecture, or another lane's plan root.

## Plan And Worktree Boundary

Plan Tree is the durable control plane and does not need one code worktree per
planner. Planner instances write scoped documents through revision-checked
script commands.

Code worktrees are created only for executable roadmap nodes. Independent
parallel branches use separate worktrees. Serial tasks within one lane may
reuse a lane worktree. All branches join through an integration worktree and
combined verification before global completion.

Workers receive an immutable plan/task snapshot with plan revision, task
revision, base commit, and artifact digests. They do not execute against a
moving global roadmap.

## Consequences

- Plan Tree becomes a graph-backed portfolio and workflow authority, not only
  a linear Markdown roadmap.
- Human-readable roadmap narrative remains separate from script-owned graph
  projection and high-frequency lane status.
- Project-level parallelism is driven by the ready frontier, scope claims,
  capacity, and integration gates.
- A project scheduler uses short transactions; provider work runs under lane
  locks rather than one long project-wide auto-runner lock.
- Parallel code branches cannot promote directly into one shared project root.
- Integration is intentionally serialized at explicit join gates.
- Additional planner panes are optional and must not precede lane authority
  isolation.

## Non-Goals

- Do not let multiple planners edit one roadmap concurrently.
- Do not equate Plan Tree branches with Git branches or task-local workgraphs.
- Do not infer parallel safety from different file paths alone.
- Do not create worktrees for planning-only nodes.
- Do not claim concurrent workflow support until two real opened-project lanes
  execute, join, recover, and release without cross-lane contamination.

## Related

- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [024-project-topology-controller-and-single-lane-first.md](024-project-topology-controller-and-single-lane-first.md)
- [031-global-plan-tree-authority-across-worktrees.md](031-global-plan-tree-authority-across-worktrees.md)
- [../topics/parallel-roadmap-lanes-and-planner-authority.md](../topics/parallel-roadmap-lanes-and-planner-authority.md)
- [../topics/planner-role-design.md](../topics/planner-role-design.md)
- [../topics/state-and-script-contract.md](../topics/state-and-script-contract.md)
