# Decision 011: Runtime Layout Manager Owns Dynamic Windows

Date: 2026-06-26

## Status

Accepted.

## Decision

CCB should grow a runtime layout manager for dynamic tmux window and pane
maintenance.

Default window classes:

- `frontdesk-dialog`: one primary frontend plus visible dialog/expert agents,
  at most six panes per window.
- `plan-orchestrate`: planner group, broker, planner stewardship mode,
  orchestrator, and round checker, at most six panes per window.
- `node-<loop-id>-<node-id>`: one execution node per window, normally
  worker + checker plus optional node status/artifact panes.
- `runtime`: loop runner, ccbd logs, capacity, ask/job queue, monitor, and
  recovery diagnostics.

Window and pane placement is a runtime presentation concern. It does not own
workflow authority.

## Rationale

The old fixed-pane model does not fit a workflow where most agents are loaded
and released on demand. Without a runtime layout manager, dynamic agents would
either clutter the primary user window or require ad hoc tmux commands that
are hard to recover and audit.

Separating visual placement from semantic orchestration keeps boundaries clear:

- frontend/dialog agents remain user-facing;
- planner/orchestrator agents remain planning and control workbench agents;
- worker/checker agents are isolated per execution node;
- runtime diagnostics are available without polluting user conversation panes.

## Consequences

- Orchestrator requests execution nodes semantically; it does not manage tmux.
- Runtime layout manager maps agent kind and loop/node ownership to windows
  and panes.
- Agent lifecycle policy is a separate layer. The layout manager places,
  hides, shows, and compacts panes according to lifecycle records, but it does
  not decide whether a long-lived role should be parked or a short-lived role
  should be unloaded.
- Release must check pending jobs and runtime state before closing panes.
- Busy agents are retained, not blindly killed.
- Pane movement or compaction must update placement state.
- Each execution node can be observed, retried, blocked, or archived
  independently.

## Open Implementation Questions

- Exact persisted layout state path:
  project-level `.ccb/runtime/layout/windows.json`, loop-level
  `.ccb/runtime/loops/<loop-id>/layout.json`, or both.
- Whether the first public surface should be `ccb layout ...`, `ccb view ...`,
  or hidden behind existing `ccb loop capacity` commands.
- How much exact tmux geometry should be restored across restarts in V1.
