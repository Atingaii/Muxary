# Topology And Lifecycle Contract

Date: 2026-07-14
Status: Proposed

## Required Topology

An opted-in Agentic Loop project materializes windows in this logical order:

```text
0  ccb-workbench  kind=client  entry=true   sidebar=false
1  ccb-user       kind=agents  frontdesk
2  ccb-plan       kind=agents  planner
3+ dynamic Agent windows created by workflow topology authority
```

The numeric index shown by tmux may honor a user's tmux `base-index`, so the
contract is relative order: workbench first, all Agent windows after it.

## Why This Is Not A Generic Tool Window

Generic `tool_windows` are arbitrary user commands, are currently appended
after Agent windows, and are intentionally outside workflow control. The
workbench is a built-in, versioned CCB client with a constrained socket command
surface and project lifecycle semantics. It therefore needs a distinct
`client` topology kind rather than special behavior inferred from a tool name.

The client kind:

- owns no Agent name, provider, mailbox, worktree, or rolepack;
- is not an ask target and is absent from Agent capacity;
- may read workbench/project projections and submit explicit user commands;
- receives no duplicate Sidebar because it already renders project/workflow
  navigation;
- is tracked in namespace/project view for focus, health, and diagnostics;
- cannot be configured with an arbitrary executable.

## Proposed Config V3 Surface

First implementation is explicit and Config V3 only:

```toml
[ui.workbench]
enabled = true
```

The Config V3 compiler, not the user, supplies the built-in client command,
window name, order, and entry selection. When disabled, current `ccb-user` and
`ccb-plan` compilation remains unchanged.

Config V2, legacy compact layouts, and generic `[tool_windows]` retain their
current ordering and startup behavior. Default-on adoption is a later product
decision after opt-in acceptance.

## Materialization Changes

Current namespace planning concatenates Agent windows followed by tool
windows. The implementation must introduce ordered built-in client surfaces
without globally sorting `entry_window` first and changing existing explicit
topologies.

Required behavior:

- client surface is prepended only when the compiled workflow config enables
  it;
- existing Agent `WindowSpec.order` values are offset in the namespace plan,
  not rewritten as user config;
- generic tool windows remain after Agent windows;
- `entry_window` resolves to `ccb-workbench` for the enabled workflow profile;
- dynamic mount/reflow never places an Agent pane in the client window;
- reload can add or remove the idle client surface without restarting
  unrelated Agents; busy workflow behavior must be explicitly tested;
- ProjectView reports `kind=client`, order, health, and active state.

The shipped config/layout and startup/supervision contracts must be updated in
the same implementation patch that changes these semantics.

## Process Lifecycle

- `ccbd` remains alive independently of the TUI process.
- TUI disconnect, terminal resize, process crash, or tmux detach cannot cancel
  a task or advance workflow state.
- Reconnecting rebuilds UI state from snapshot plus cursor, not from in-memory
  widget state.
- An unexpected client failure is visible and recoverable through bounded
  client-slot supervision.
- Project kill stops the client together with the namespace after workflow and
  Agent shutdown rules have run.
- Explicit task cancellation is a workflow command, not a consequence of
  closing the client.

The exact explicit quit/detach UX remains in
[../open-questions.md](../open-questions.md).
