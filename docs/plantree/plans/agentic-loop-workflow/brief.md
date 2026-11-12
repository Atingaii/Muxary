# Agentic Loop Workflow Brief

Date: 2026-07-02
Status: planning

## Purpose

Build an opt-in CCB agentic loop that keeps program authority small and stable
while model roles handle semantic planning, detail refinement, review,
orchestration, execution, and verification through explicit artifacts.

## Current Phase

V1 source implementation is validating the planning bridge:
`agentroles.planner` maintains a compact brief and macro task packet, while
`task_detailer` owns task-scoped detail docs only when orchestrator triage
requests detailed refinement.

## Macro Objective

Support a bounded workflow path from macro task intake to reviewed task packet,
task detail refinement, explicit runtime topology or loop execution, review,
round result import, and release without giving model roles direct authority
over status indexes, runtime state, tmux, provider processes, or role
collection runtime launch.

## Active Roadmap Item

- Item: V1 planner brief plus task detailer detail docs import bridge
- Ref: [roadmap](roadmap.md)
- Owner: planner

## Accepted Constraints And Non-Goals

- Program code stays limited to schema checks, artifact import, state
  transition validation, and explicit runtime reconciliation.
- Planner maintains macro brief and links, not detail design bodies.
- `task_detailer` maintains task-scoped detail docs and stable summaries, not
  authoritative roadmap or task status.
- Role Collections install/list/update/profiles only; runtime agents must be
  declared explicitly by roles, members, edges, and gates.

## Decision Summary

- Planner uses a compact brief and `task_detailer` owns task detail docs only
  after orchestrator asks for detail
  ([decision 018](decisions/018-planner-uses-plan-brief.md),
  [decision 019](decisions/019-orchestrator-triage-before-task-detailer.md)).

## Open Question Summary

- Decide when the role-output consumption bridge graduates from focused smoke
  to default fake-provider workflow closure coverage
  ([open questions](open-questions.md)).

## Detail Links

- Planner/detail boundary: [brief and detail docs](topics/planner-plan-tree-brief-and-detail-boundary.md)
- Planner role boundary: [planner role design](topics/planner-role-design.md)
- Task detailer boundary: [task detailer role design](topics/task-detailer-role-design.md)

## Current Task And Detail Packet

- Macro task: V1 minimal implementation slice for planner brief plus
  task_detailer detail docs.
- Detail packet: not yet durable; this slice adds import support for
  `detail_design` and `detail_summary` task artifacts.
- Detail readiness: planning

## Readiness State

The minimal import bridge is test-backed. Broader real-provider behavior and
topology-driven execution remain opt-in follow-up work.

## Verification Summary

Focused source tests cover plan brief import, task detail doc import,
task_detailer bundle consumption, and planner bundle rejection for detail
bodies.

## Next Owner / Handoff

Next owner is planner for deciding whether to expand fake workflow closure
smoke to include `--consume-role-output` plus orchestrator-demanded
task_detailer refinement.

## Last Stable Evidence

- 2026-07-02: focused tests `test/test_plan_tasks_cli.py` and
  `test/test_loop_capacity_cli.py` passed after this slice.
