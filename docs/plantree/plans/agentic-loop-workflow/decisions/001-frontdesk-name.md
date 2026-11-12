# Decision 001: Use `frontdesk` For The User-Facing Boundary

Date: 2026-06-24

## Status

Accepted.

## Context

Earlier discussion used `main` for the user-facing role. That name is
misleading in this workflow. It implies central authority, strongest reasoning,
or primary execution responsibility, while the intended role is only an intake,
handoff, reporting, and escalation boundary.

The workflow's control plane should be the scripted state machine and loop
runner. Planning authority belongs to planner and script-owned stewardship
surfaces.
Execution belongs to orchestrator-selected execution nodes. Runtime health
belongs to monitor layers. The user-facing role should not be encouraged by
name to take over those responsibilities.

## Decision

Use `frontdesk` for the user-facing non-executing role.

`frontdesk` means:

- Receives user input.
- Captures macro intent.
- Passes structured intake to planner group.
- Presents clarification, escalation, and final summaries to the user.
- Does not own implementation, plan-tree mutation, loop state mutation,
  worker scheduling, or done decisions.

## Consequences

- Future role prompts, team specs, config examples, and UI labels should use
  `frontdesk` rather than `main`.
- If a stronger human-boundary role is later needed for risk escalation, it
  should be named explicitly, such as `frontdesk_supervisor`, rather than
  overloading `frontdesk`.
- Trellis comparison text may still refer to a "main session" when describing
  Trellis itself, because that is an external design concept.

## Non-Goals

- This decision does not define the full role prompt.
- This decision does not grant `frontdesk` write authority.
- This decision does not decide whether `frontdesk` is one agent or a small
  group in the final team spec.
