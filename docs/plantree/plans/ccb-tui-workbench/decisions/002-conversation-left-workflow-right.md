# Conversation Left, Workflow Right

Date: 2026-07-14

## Context

Mixing normal user input, internal ask replies, progress logs, clarification,
and final task results in one transcript makes input intent ambiguous and
pollutes long-lived Agent context.

## Decision

The workbench keeps normal Frontdesk conversation on the left. Workflow state,
queue, internal activity, verification, and complete task results live on a
conditional right-side panel.

Status and results move into the left conversation only as explicit stable
references for discussion. A pending clarification may temporarily scope the
left composer to an exact `question_id`; resolving or leaving that interaction
restores normal Frontdesk mode and its draft.

## Consequences

- The left transcript remains readable and does not become a status feed.
- The right panel needs a durable backend projection and result store.
- Input routing is explicit and testable; Detail is not selected by semantic
  guessing.
- Narrow terminals use full-screen views without changing the routing model.
