# 024 Project Topology Controller And Single-Lane First

Date: 2026-07-10
Status: Accepted for planning

## Context

Decision 023 introduces future concurrent Workflow Lanes. Each lane needs
isolated orchestration, runtime identity, topology intent, execution agents,
and lifecycle evidence. The physical resources remain project-wide: provider
limits, role-profile capacity, agent names, tmux windows and panes, sidebar
state, workspace names, and release operations.

Giving each lane an independent topology controller would create competing
capacity views, duplicate names, layout races, and cross-lane release risk.
Making one global orchestrator own every lane would instead serialize semantic
planning and mix lane context.

The current production priority also remains one complete single-lane workflow.
Parallel-lane design must not distract from closing that path.

## Decision

Each active lane or task round has its own immaculate orchestrator activation
and lane-scoped topology desired/observed state. The project has exactly one
deterministic Topology Controller authority.

The Topology Controller:

- consumes admitted lane capacity intent and allowed config profiles;
- validates project-wide role/provider/model and maximum-instance constraints;
- binds logical role profiles to concrete lane-owned agent identities;
- creates fresh or proven-cleared immaculate provider activations;
- compiles lane intent into mount-only agent/window/pane/workspace state;
- reconciles desired and observed runtime idempotently;
- returns concrete bindings and readiness to the dispatch controller;
- applies busy-retain, release, reflow, and residue evidence by lane ownership;
- recovers from partial mount/release without inferring semantic success.

It does not split tasks, write ask content, choose roadmap priority, rewrite an
orchestration bundle, judge implementation quality, or write plan/task success.

Project-wide uniqueness applies to physical reconcile transactions, not to a
long-running global lock. Lane topology state remains independently addressable
and the project controller uses short capacity/layout/lifecycle transactions.

## Lane And Integration Rules

- Independent lanes use independent orchestrator activations and bundles.
- One lane bundle may contain several parallel workers; it does not need one
  orchestrator per worker.
- Structural replan creates a fresh orchestrator activation for that lane.
- A complex roadmap join may create a separate integration lane and fresh
  integration orchestrator.
- Releasing one lane must match project, lane, loop, and activation ownership
  and cannot mutate another lane's active topology.

## Sequencing Gate

Roadmap Graph, multi-lane scheduling, and project-wide topology aggregation
remain design-only until the current single-lane path is production-ready:

```text
frontdesk
  -> planner
  -> optional detail/global-consistency gate
  -> optional orchestrator bundle
  -> controller mount and exact-once dispatch
  -> one or more worker/reviewer workgroups
  -> round/integration evidence
  -> script-owned completion
  -> clean immaculate-role release
```

The single-lane gate must prove visible opened-project operation, real provider
execution, recovery, authority isolation, context freshness, release, and
repeatability. Multi-lane source changes start only after that gate has a
stable baseline and explicit acceptance evidence.

## Consequences

- Orchestrator count follows active semantic lanes, not worker count.
- Topology state is lane-scoped while physical topology authority is project
  scoped.
- Project Scheduler, Topology Controller, and Dispatch Controller are separate
  deterministic responsibilities, though they may be modules in one runner
  process.
- No multi-lane implementation is authorized by this decision.
- Single-lane defects must be repaired at their source rather than hidden by
  parallel scheduling or additional agents.

## Related

- [020-mount-topology-and-ask-first-orchestration.md](020-mount-topology-and-ask-first-orchestration.md)
- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [023-roadmap-graph-and-workflow-lanes.md](023-roadmap-graph-and-workflow-lanes.md)
- [025-single-lane-multi-workgroup-release-gate.md](025-single-lane-multi-workgroup-release-gate.md)
- [031-global-plan-tree-authority-across-worktrees.md](031-global-plan-tree-authority-across-worktrees.md)
- [../topics/parallel-roadmap-lanes-and-planner-authority.md](../topics/parallel-roadmap-lanes-and-planner-authority.md)
