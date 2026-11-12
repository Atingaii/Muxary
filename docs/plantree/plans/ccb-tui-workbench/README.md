# CCB TUI Workbench Plan

Date: 2026-07-14
Status: Planning

## Purpose

Design a CCB-native terminal workbench that becomes the first visible tmux
window for an opted-in Agentic Loop project. The workbench keeps normal
Frontdesk conversation stable on the left and presents task queue, workflow
state, clarification, internal activity, verification, and collected results
on the right. Agent windows remain visible for inspection but move behind the
workbench in tmux traversal order.

The workbench is a client of `ccbd` and the scripted workflow state machine. It
must not become an Agent, a workflow runner, a second task-state authority, or
a replacement for `.ccb/ccb.config`.

## Current Source Findings

- `tools/ccb-agent-sidebar` already ships a Rust `ratatui`/`crossterm` client,
  local Unix-socket transport, mouse input, theme handling, and TestBackend
  coverage. The workbench should use the same deployed TUI stack.
- Namespace topology currently places all Agent windows before generic
  `tool_windows`. Pointing `entry_window` at a tool selects it after startup but
  does not make it the first physical tmux window.
- Config V3 currently compiles resident `frontdesk` and `planner` into
  `ccb-user` and `ccb-plan`, and fixes `entry_window` to `ccb-user`.
- `ccbd` already supports `from_actor=user` submission, job watch/cancel, and
  `project_view`, but it does not yet expose one authoritative conversation,
  workflow, interaction, queue, and result projection for a workbench.
- The current question service is artifact/import oriented. A TUI-safe answer
  command keyed by `task_id` and `question_id` is still required.

## Scope

In scope for V1:

- One managed `client` window named `ccb-workbench` at topology order zero.
- Agentic Loop Config V3 opt-in without changing Config V2 defaults.
- Left-side Frontdesk conversation and right-side conditional workflow panel.
- One active top-level workflow task with multiple FIFO queued tasks.
- Existing one-task internal Worker/Reviewer fanout remains governed by the
  Agentic Loop plan; serial V1 refers to top-level workflow lanes.
- Explicit clarification routing by `question_id`, never semantic target
  guessing from free-form input.
- Status and complete results on the right, with compact notices and explicit
  result/status references available to the left conversation.
- Reconnect and restore without cancelling backend work.
- Keyboard-first operation with mouse parity and narrow-terminal layouts.

Out of scope for V1:

- Multiple simultaneously active top-level workflow lanes.
- Browser GUI, remote multi-user UI, mobile UI, and rich media previews.
- Drag-and-drop workflow editing or arbitrary user-authored workflow graphs.
- Replacing provider panes or hiding Agent execution from operators.
- Letting the TUI directly edit PlanTree state or runtime artifact files.
- Making `ccb config` a workflow dashboard.

## Authority And Reading Order

1. Shipped runtime and layout contracts under `docs/` remain authoritative.
2. The Agentic Loop plan owns workflow semantics, task transitions, dynamic
   Agent lifecycle, and PlanTree writeback.
3. This plan owns the workbench client, its UI interaction model, projection
   API requirements, and first-window product behavior.
4. Implementation status and evidence will be added only after implementation
   starts.

Read in this order:

- [roadmap.md](roadmap.md)
- [topics/product-and-interaction-contract.md](topics/product-and-interaction-contract.md)
- [topics/topology-and-lifecycle-contract.md](topics/topology-and-lifecycle-contract.md)
- [topics/state-command-and-result-contract.md](topics/state-command-and-result-contract.md)
- [topics/implementation-and-test-plan.md](topics/implementation-and-test-plan.md)
- [open-questions.md](open-questions.md)

## Decisions

- [001-workbench-is-first-managed-client-window.md](decisions/001-workbench-is-first-managed-client-window.md)
- [002-conversation-left-workflow-right.md](decisions/002-conversation-left-workflow-right.md)
- [003-standalone-ratatui-client-and-ccbd-authority.md](decisions/003-standalone-ratatui-client-and-ccbd-authority.md)

## Related Sources

- [Agentic Loop Workflow](../agentic-loop-workflow/README.md)
- [Agentic Loop clarification flow](../agentic-loop-workflow/topics/clarification-flow.md)
- [Agentic Loop state and script contract](../agentic-loop-workflow/topics/state-and-script-contract.md)
- [Managed Tool Windows](../managed-tool-windows/README.md)
- [Config Designer UI](../config-designer-ui/README.md)
- [CCB config and layout contract](../../../ccb-config-layout-contract.md)
- [CCBD startup and supervision contract](../../../ccbd-startup-supervision-contract.md)
- [runtime flows baseline](../../baseline/runtime-flows.md)
- [storage and state baseline](../../baseline/storage-and-state.md)
