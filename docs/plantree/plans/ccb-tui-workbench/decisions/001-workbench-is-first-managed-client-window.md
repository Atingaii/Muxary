# Workbench Is The First Managed Client Window

Date: 2026-07-14

## Context

The user-facing conversation and workflow surface should be the first CCB
window, while provider Agent windows remain available behind it. Current
topology appends generic tool windows after Agent windows, and `entry_window`
selection alone does not change physical traversal order.

## Decision

An opted-in Agentic Loop project gets a built-in `ccb-workbench` window as the
first managed topology surface. It has topology kind `client`, is selected as
the entry window, contains no Agent or duplicate Sidebar, and precedes
`ccb-user`, `ccb-plan`, and dynamic Agent windows.

This is initially a Config V3 opt-in. Config V2 and generic tool-window order
remain unchanged.

## Consequences

- Namespace topology requires an ordered client primitive rather than merely
  pointing `entry_window` at an appended tool window.
- Agent window identities remain stable but their relative tmux position moves
  behind the workbench when the feature is enabled.
- The workbench cannot become an ask target, provider runtime, or capacity
  slot.
- Layout and startup contracts must change with implementation.
