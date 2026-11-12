# Decision 004: Script-Owned Plan And Runtime Lists

Date: 2026-06-24

Status: Accepted

## Context

The workflow design borrows Trellis' core idea that long-running AI work should
not rely on one model conversation as the source of truth. Plans, active work,
progress, and breadcrumbs should live in files and be advanced by scripts.

CCB adds visible agents, `ask` jobs, callback state, panes, node status,
branch status, and round verification. This makes ad hoc agent edits to state
files especially risky: two agents could race, lower quality gates, or turn
runtime evidence into durable truth without validation.

## Decision

Use two separate state layers:

- Durable plan packets under `docs/plantree/plans/<plan-slug>/tasks/<task-id>/`.
- Machine-owned runtime loop lists under `.ccb/runtime/loops/`.

Agents may write draft artifacts and semantic content, but authoritative
status, indexes, phase, owner, node, branch, ask, and round state must be
written through CCB-owned scripts.

The first command namespaces are:

- `ccb plan` for durable task packet creation, artifact registration, status,
  and sync.
- `ccb loop` for runtime list, loop state, node/branch status, ask records,
  events, breadcrumbs, and round results.
- `ccb question` for staged clarification artifacts.

## Consequences

- `frontdesk` and long-lived roles can rehydrate from compact breadcrumbs
  instead of carrying the full loop in conversation context.
- Planner output remains durable and reviewable without absorbing high-frequency
  runtime noise.
- Runtime state can support visible CCB agents, ask/callback refs, partial
  branches, and round verification.
- Script validation can reject illegal phase edges, missing artifacts,
  over-limit retries, and unauthorized state writers.
- The first implementation can use fixed configured agents before dynamic
  hot-load/hot-unload is introduced.

## Non-Goals

- This does not require dynamic agent creation in v1.
- This does not make `docs/plantree` an event log.
- This does not allow agents to directly mutate `.ccb/runtime/loops` authority
  files.
- This does not decide final CLI names; it fixes the authority split and file
  structure first.
