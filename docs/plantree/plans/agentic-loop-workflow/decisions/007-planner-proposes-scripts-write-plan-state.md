# Decision 007: Planner Proposes, Scripts Write Plan State

Date: 2026-06-25

## Status

Accepted for V1 design.

## Decision

Planner group owns semantic planning and readiness recommendations, but CCB
scripts own authoritative task packet creation, task status, task indexes,
current-loop binding, and durable plan-tree sync.

Planner agents may produce draft artifacts and review reports. They must use
`ccb plan` command surfaces to import artifacts and request state transitions.

## Rationale

- Keeps `frontdesk` light without turning planner into an unbounded hidden
  executor.
- Preserves context purity: planner handles stable requirements, while runtime
  detail stays in `.ccb/runtime`.
- Gives tests a deterministic authority surface.
- Prevents model conversation drift from silently changing task status.
- Matches the accepted Trellis-inspired principle that durable workflow truth
  lives outside model memory and is advanced through scripts.

## Consequences

- The first planner implementation must include plan-update scripts before
  autonomous planner-to-loop handoff is trusted.
- `ready` requires required artifacts and reviewer evidence.
- Plan steward can be a semantic helper, but cannot bypass script validation.
- Direct planner edits to task status or machine indexes are invalid.
