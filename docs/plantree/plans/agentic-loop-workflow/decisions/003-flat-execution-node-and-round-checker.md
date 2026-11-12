# Decision 003: Flat Execution Nodes And Round Checker

Date: 2026-06-24

Status: Accepted

## Context

Loop execution needs strong quality control without recreating a hidden
hierarchy inside every work item. A default master-worker structure inside each
execution node would duplicate orchestrator responsibility, increase context
load, and create another place where scope or quality could drift.

At the same time, a simple worker-only model is not enough. The system needs a
separate quality gate that can design verification, audit for hidden fallback or
degradation, and reject partial work that is incorrectly reported as done.

Parallel work also needs partial semantics. A non-converged node should not
automatically cancel unrelated sibling nodes, but it also must not be silently
downgraded to success.

## Decision

Use flat execution nodes for v1:

```text
execution_node = worker + checker
```

The checker is a peer quality gate. It derives node-level verification, reviews
worker output, runs focused tests, audits fallback/degradation behavior, and
returns `pass`, `rework`, `blocked`, or `non_converged`.

Do not add a default node-internal master role. Add a temporary
`node_coordinator` only in a later complex-node mode when orchestrator cannot
safely split the work item.

Add a separate round checker after node work drains. Planner defines the
verification contract before execution; round checker designs and executes the
concrete round verification plan after it sees actual node reports, changed
surfaces, dependency graph, and partial branches.

If a node does not converge after bounded rework, freeze that node and its
dependent branch, drain unrelated sibling work when safe, and return a partial
package to planner. Scope reduction or degradation must leave execution and be
approved through planner/frontdesk flow when needed.

## Consequences

- Execution nodes stay small and short-lived.
- Checker remains independent from worker and cannot become a hidden executor.
- Orchestrator stays responsible for task splitting and dependency graph
  aggregation.
- Round checker verifies whole-round correctness rather than trusting local
  node pass states.
- Partial work can be preserved without claiming degraded completion.
- The state machine needs explicit node, branch, and round statuses.

## Non-Goals

- This does not implement complex node-internal teams in v1.
- This does not let checker lower acceptance criteria.
- This does not let round checker change product scope.
- This does not let loop runner mark partial work as done.
