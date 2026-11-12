# 019 Orchestrator Triage Before Task Detailer

Date: 2026-07-02
Status: Accepted for planning

## Context

Earlier workflow notes treated `task_detailer` as part of the normal planning
chain after planner. That made the detailer look like a fixed downstream
member of `planning_group`, and it blurred the boundary between macro planning
and execution orchestration.

The new mainline keeps `agentroles.ccb_planner` as the only CCB macro planner.
The historical `plan_steward` term is a planner work mode or script-authority
surface, not a separate required Role. `agentroles.planner_task` is historical
or deprecated alias material and must not be used for new CCB workflow
topology.

## Decision

Orchestrator triages the planner's macro task before any task-detailer
activation.

The mainline flow is:

```text
frontdesk
  -> planner
  -> orchestrator triage
      -> direct worker/reviewer
      OR
      -> ccb_task_detailer -> orchestrator -> worker/reviewer
      OR
      -> macro_adjustment_request -> planner
  -> round_reviewer
  -> planner/frontdesk
```

Orchestrator classifies the next step as one of:

- `direct_execution`: the planner macro packet is concrete enough to dispatch
  bounded worker/reviewer asks.
- `needs_detail`: the task needs source-backed refinement before dispatch;
  orchestrator requests a short-lived `ccb_task_detailer`.
- `macro_adjustment_request`: the macro packet cannot safely proceed without a
  planner-owned roadmap, decision, scope, acceptance, or open-question update,
  so orchestrator or task_detailer emits a compact artifact for planner
  review.
- `blocked`: execution cannot proceed and needs a blocker artifact or user
  escalation.

`ccb_task_detailer` is an on-demand refinement role. It is called only for
`needs_detail`, receives an orchestrator refinement request plus planner macro
refs, and returns its detail packet to orchestrator. It must not call workers,
reviewers, or topology commands directly.

If detail work discovers macro drift, the detailer emits a
`macro_adjustment_request` addressed to planner. It must not edit roadmap,
decisions, open questions, task status, runtime topology, or global plan-tree
surfaces directly.

Decision 029 fixes the delivery boundary for that request: Task Detailer owns
one restricted direct silent Planner handoff carrying a versioned macro-impact
envelope. Controller code validates exact-once identity/revision authority but
does not reconstruct the semantic request.

## Consequences

- `agentroles.collections.planning_group` requires only
  `agentroles.ccb_planner`;
  optional planning members are plan review or clarification roles, not
  `ccb_task_detailer`. Detailer may be installed directly or through a broader
  workflow collection, but it is not a planning-group member.
- `agentroles.collections.agentic_loop_core` requires
  `agentroles.ccb_frontdesk`, `agentroles.ccb_planner`,
  `agentroles.ccb_orchestrator`, `agentroles.coder`,
  `agentroles.code_reviewer`, and `agentroles.ccb_round_reviewer`. Optional
  members include `agentroles.ccb_task_detailer` and future CCB review, risk,
  monitor, and recovery Roles.
- `agentroles.collections.execution_workgroup` requires coder and code
  reviewer.
- Role Collections remain install/update/remove/list/profile metadata. They do
  not inherit, authorize, mount, or select runtime topology.
- Planner owns macro plan-tree, brief, roadmap, decisions, open questions,
  macro task publication, and review of `detail_summary` or
  `macro_adjustment_request` artifacts. It does not directly schedule detailer,
  worker, reviewer, provider, tmux, or topology operations.

## Related

- [017-flat-roles-and-role-collections.md](017-flat-roles-and-role-collections.md)
- [018-planner-uses-plan-brief.md](018-planner-uses-plan-brief.md)
- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [029-planner-feedback-and-task-set-closure.md](029-planner-feedback-and-task-set-closure.md)
- [../topics/architecture.md](../topics/architecture.md)
- [../topics/task-detailer-role-design.md](../topics/task-detailer-role-design.md)

Decision 022 refines this V1 triage shape: a validated single-unit template may
eventually bypass an orchestrator provider activation, while a semantically
orchestrated task uses one complete orchestration bundle and controller-owned
physical dispatch.
