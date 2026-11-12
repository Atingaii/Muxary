# 015 Task Detailer Owns Task Refinement And Task-Local Clarification

Date: 2026-07-02
Status: Accepted for planning

## Decision

Do not make the long-lived planner maintain detailed implementation planning
or task-local clarification context.

Introduce a short-lived `task_detailer` role for execution-readiness
refinement. `task_detailer` reads a macro task, plan-tree refs, source refs,
prior decisions, and durable evidence, then produces a detailed execution
packet for orchestrator, worker, and reviewer roles.

Task-local clarification is part of `task_detailer`; do not introduce a
separate `task_clarifier` role in V1.

When user input is needed, `task_detailer` produces a clarification-needed
artifact and notifies `frontdesk` or the frontend. The user may then interact
with that same `task_detailer` instance. `frontdesk` only exposes the entry
point and reminder; it does not interpret the detailed task question by
default.

## Rationale

- Long-lived planner context should stay stable and macro-level.
- Detailed implementation research is short-lived, code-heavy, and likely to
  include noisy local evidence.
- Splitting `task_clarifier` from `task_detailer` would add handoff and
  synchronization cost before the workflow proves that separation is needed.
- Users should clarify task detail with the agent that already holds the
  task-local research context.

## Role Boundary

Long-lived planner owns:

- plan-tree roadmap, decisions, open questions, and durable evidence indexes;
- macro task publication and long-term plan hygiene;
- importing stable summaries from completed, partial, or blocked workflow
  rounds through script-owned plan state.

`task_detailer` owns:

- reading macro task refs and relevant plan-tree/source evidence;
- refining scope, non-goals, acceptance, verification, risk, and handoff;
- asking task-local clarification only when needed;
- recording clarification summaries and normalized answers;
- producing a detailed execution packet for review and orchestration.

`task_detailer` must not:

- own long-term plan-tree maintenance;
- rewrite roadmap or macro direction;
- dispatch workers or reviewers directly;
- mutate authoritative task status, indexes, runtime state, or provider state;
- become a permanent user-facing agent after the task-local clarification is
  resolved.

## V1 Flow

```text
frontdesk -> planner -> macro task refs
orchestrator triage -> task_detailer only when detail is needed
task_detailer -> self research over plan-tree/source refs
task_detailer -> clarification-needed artifact when needed
frontdesk/frontend -> notify user to talk to task_detailer
user -> task_detailer
task_detailer -> clarification summary + detailed execution packet
task_detailer -> orchestrator
optional plan_reviewer/detail_reviewer -> readiness gate
orchestrator -> worker + reviewer nodes
round_checker -> planner / ccb plan summary import
```

## Deferred Split

Only consider a separate `task_clarifier` later if:

- task-local user clarification commonly becomes long-running;
- multiple detailers must share one user clarification thread;
- clarification needs a strict UI/form/audit workflow;
- security boundaries require a clarifier that cannot read source while the
  detailer can.
