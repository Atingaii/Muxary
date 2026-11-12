# 021 Immaculate Role Context Lifecycle

Date: 2026-07-09
Status: Accepted for planning

## Context

The workflow originally separates durable planning memory from noisy execution
memory. Recent real-project testing made the distinction more important:
visible panes and mounted agents are useful for observation, but visible
residency must not imply that every role can accumulate long-term conversation
state.

The system needs a clear contract for roles that should start clean on every
task, round, or detail pass while still reading durable artifacts from the plan
and runtime authority surfaces.

## Decision

CCB defines an immaculate (`无垢`) role class.

An immaculate role is activation-scoped. It may be mounted, visible, or have
archived provider-state for audit, but it must not use old conversation history
as working context for a new task, round, branch, retry, or clarification
continuation.

The initial immaculate roles are:

- `ccb_orchestrator`
- `ccb_task_detailer`
- loop execution workers such as `coder`
- loop reviewers such as `code_reviewer`
- `ccb_round_reviewer`

The long-lived context exceptions are:

- `ccb_frontdesk`, which retains user-facing dialogue, preferences, macro
  intake, confirmations, and escalation breadcrumbs.
- `ccb_planner`, which retains macro plan-tree state, compact brief, roadmap or
  TODO state, decisions, open questions, accepted constraints, and stable
  evidence links.

`ccb_planner` and `ccb_frontdesk` stay useful because they do not own
implementation detail. `ccb_orchestrator`, `ccb_task_detailer`, workers,
reviewers, and round reviewers stay reliable because each activation is
rehydrated from explicit artifacts instead of prior chat memory.

## Runtime Contract

The runtime/controller owns freshness. A valid implementation must provide one
of these mechanisms before an immaculate role receives a new activation:

- create a new provider session;
- use a unique dynamic agent identity for the activation;
- run and record a proven clear/reset step.

Prompt wording alone is not sufficient. The evidence for a workflow run should
record the activation id, freshness mechanism, role identity, and durable refs
used to rehydrate the role.

## Consequences

- UI/sidebar visibility and pane residency are observability features, not
  permissions to reuse context.
- Old provider-state may be preserved for audit, but it is not semantic input
  unless explicitly summarized into an artifact and passed by the controller.
- `task_detailer` clarification returns to the same task/detail packet, not
  necessarily the same provider conversation.
- `orchestrator` can coordinate one task or round deeply, but each later task
  or round starts from task, loop, topology, and evidence refs.
- Workers and reviewers should be released, cleared, or replaced after their
  work item and review evidence are imported.
- Deployment-readiness tests must include freshness evidence for immaculate
  roles, especially after multi-round and repeated frontdesk-originated tasks.

## Non-Goals

- Do not clear `frontdesk` after every user message.
- Do not clear `planner` after every task; keep its macro brief compact instead.
- Do not make hidden script-only execution the acceptance path. The live project
  should still expose mounted roles and evidence for observation.
- Do not treat conversation logs as task authority. Script-owned task, topology,
  and round artifacts remain the authority boundary.

## Related

- [../topics/context-purity.md](../topics/context-purity.md)
- [../topics/orchestrator-role-capability.md](../topics/orchestrator-role-capability.md)
- [../topics/task-detailer-role-design.md](../topics/task-detailer-role-design.md)
- [../topics/planner-plan-tree-brief-and-detail-boundary.md](../topics/planner-plan-tree-brief-and-detail-boundary.md)
