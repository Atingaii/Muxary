# Decision 009: Loop Runner Activates Planner And Owns Stop Decisions

Date: 2026-06-26

Status: Accepted

## Context

The design originally described planner as a pre-execution group, which made it
look like planning happened outside the loop. Later discussion clarified that
the loop should be a dynamic script/helper that reads document state and
activates the right role automatically.

Planner must therefore be inside the workflow loop. At the same time, planner
should not stay inside the noisy execution round.

The design also needs a clear stopping authority. Documents hold state, but
documents do not decide. Agents can recommend, but agents must not directly
write terminal authority.

## Decision

Define two nested loops:

- workflow loop: includes intake, planner, broker, ready state, execution
  round, round check, writeback, and stop/next-cycle decisions;
- execution round: includes orchestrator, execution nodes, checker, round
  checker, monitor, and capacity release.

Planner is a workflow-loop phase and is activated by loop runner when task
state requires planning: `draft`, resolved clarification, `partial`,
`replan_required`, resolved blocker, or changed user scope.

Planner is not active inside the execution round unless the round exits through
`partial` or `replan_required`.

Loop runner owns activation and stopping decisions by reading authoritative
state and limits. Scripts write authoritative status. Agents produce reports
and recommendations.

## Consequences

- Planner is automatic and state-driven, not a manual pre-step.
- Execution noise stays out of planner until it becomes durable round evidence.
- The loop stops on terminal states, paused states, or configured limits.
- `round_checker=pass` goes to script writeback and stop; `partial` and
  `replan_required` reactivate planner through durable state.
- `needs_clarification` pauses automatic progression until user answers are
  normalized.

## Non-Goals

- This does not implement the full loop runner command surface.
- This does not let documents mutate themselves.
- This does not let planner write task status or runtime phase directly.
- This does not let round checker create the next plan.
