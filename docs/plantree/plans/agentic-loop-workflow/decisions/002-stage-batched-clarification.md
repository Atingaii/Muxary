# Decision 002: Stage-Batched Clarification Through Broker

Date: 2026-06-24

Status: Accepted

## Context

Planner group needs to understand user intent deeply enough to produce an
execution-ready plan. At the same time, `frontdesk` should not become a detailed
planning assistant or carry all low-level ambiguity in its conversation context.

Direct planner-to-user questioning would leak detailed planning state into the
user-facing channel. Asking all possible questions up front would overload the
user and create obsolete answers. Letting planner silently assume everything
would hide risk.

## Decision

Use a stage-batched clarification flow.

Planner group emits candidate questions for the current phase. A clarification
broker reviews the batch, merges duplicates, removes code-answerable or
plan-tree-answerable items, applies safe defaults, defers future-phase items,
marks obsolete questions, and publishes only true user-needed questions to
`frontdesk` as a compact display artifact reference.

`frontdesk` remains the only user-facing surface. It presents the curated
questions and records raw answers. Broker normalizes those answers and notifies
planner group to continue. Broker does not activate the execution loop.

The broker should not be a heavy long-lived semantic role by default. Persistent
state belongs in question artifacts and queue records. A semantic broker can be
launched with fresh context per phase batch and released after resolution.

## Consequences

- `frontdesk` context stays small and macro-level.
- Planner can still ask necessary clarifying questions without directly
  becoming user-facing.
- Most noisy ambiguity is handled in runtime-local artifacts instead of durable
  plan-tree Markdown.
- User interactions become shorter because broker filters, defaults, and
  defers before anything reaches the user.
- The design needs a `ccb question` command surface or equivalent helper to
  validate files, preserve raw answers, normalize answers, and wake planner.

## Non-Goals

- This does not make broker a product decision maker.
- This does not let broker start `loop runner` or execution nodes.
- This does not let `frontdesk` mutate planner artifacts directly.
- This does not require every phase to ask the user; phases with no
  `user_needed` questions can continue after broker records defaults or
  deferrals.
