# Decision 012: Long-Lived Roles Park Before Unload

Date: 2026-06-26

## Status

Accepted.

## Decision

Long-lived interactive roles should default to `hide` or `park`, not hard
`unload`.

This applies to:

- primary `frontend` or `frontdesk` agents;
- planner coordinators and plan reviewers while a task family is active;
- orchestrator;
- round checker when its round family may continue;
- dialog experts that are expected to preserve user-facing context.

Short-lived execution roles, such as generated workers and checkers, may be
unloaded after evidence has been imported and idle checks prove that no ask,
job, or provider work is pending.

## Rationale

The agentic loop design depends on context purity, but not all context should
be discarded at the same rate. Worker/checker context is fast-changing and
round-local, so it should be summarized and released. Planner and orchestrator
context is slower-moving control context. Dropping it aggressively would make
long-running work less stable and would increase rehydration cost.

`hide` and `park` let CCB keep the visible workspace small while preserving the
state needed for future planning, orchestration, clarification, or recovery.

## Consequences

- Dynamic lifecycle state belongs under `.ccb/runtime`, not in
  `.ccb/ccb.config`.
- `ccb agent release` should apply role policy. For long-lived roles, the
  default result is park or hide. For short-lived round-owned roles, the
  default result can be unload after idle/evidence gates pass.
- `ccb loop capacity release` remains optimized for generated worker/checker
  agents.
- Hard unload remains explicit, idle-gated, and operator-grade.
- `remove` is policy resolution, not a synonym for kill. It must report the
  resolved policy: hide, park, unload, or kill.
- `kill` remains an explicit emergency/operator action requiring force,
  reason, and diagnostics. It is not available to normal role skills.
- Skills used by `frontdesk`, planner, and orchestrator must not call raw
  `tmux`, raw `ccb reload`, raw `ccb kill`, or provider process kills.

## Follow-Up

Implement the lifecycle command and skill surface described in
[dynamic-agent-lifecycle-and-skills.md](../topics/dynamic-agent-lifecycle-and-skills.md)
before allowing autonomous roles to dynamically park or unload live provider
sessions.
