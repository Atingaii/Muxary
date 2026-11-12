# Decision 014: Chat-First Agent Workspace

Date: 2026-06-21

## Status

Accepted.

Extends [Decision 012](012-agent-first-project-workspace.md) and
[Decision 013](013-readable-terminal-history.md). Raw terminal control remains
available, but the default mobile workspace becomes conversation-first.
The UI shape remains accepted, but the send/read transport stance is superseded
by [Decision 015](015-pane-backed-chat-input.md): the composer must write to
the selected agent's tmux pane instead of wrapping the ask/message route.

## Context

Manual emulator testing showed that the agent-first page is more readable than
the older terminal/status surface, but it still behaves like a monitoring
dashboard. The user expects a ChatGPT/DeepSeek-style workbench: one selected
agent, a readable message timeline, and a persistent input composer.

The current app can show selected-agent state, Markdown blocks, readable tmux
history, and explicit terminal controls. It cannot yet submit a normal user
message from the main mobile surface because there is no first-class mobile
conversation/composer contract; typing into a raw terminal is the wrong default
interaction for CCB agents.

## Decision

The default selected-agent workspace is a chat-style conversation surface:

- top area shows project/agent switching only;
- the main body is a vertically scrollable timeline for the selected agent;
- timeline entries include user messages, agent replies, callbacks, Comms,
  status/tool events, artifact/content cards, and terminal-derived history
  blocks when useful;
- bottom area is a persistent multiline composer with send, disabled/error
  states, draft preservation, and keyboard-safe layout;
- sending a message uses the pane-backed path defined by
  [Decision 015](015-pane-backed-chat-input.md);
- structured CCB messages, replies, Comms, and artifacts are authoritative
  conversation content;
- readable terminal history remains a secondary evidence block in the
  conversation timeline, clearly labeled best-effort;
- Open Terminal remains an explicit advanced/debug action for pane-level
  control.

## Consequences

- The next landing phase should prioritize the chat surface as a structured
  tmux pane input/output layer before production relay work.
- The gateway/app should reuse the existing terminal-open, input, paste,
  output, and terminal-history contracts rather than creating a parallel ask
  wrapper for default chat sends.
- The Flutter home screen should be refactored from dashboard cards to:
  agent switcher, message timeline, and bottom composer.
- Connection details, route diagnostics, lifecycle controls, terminal state,
  runtime ids, and pairing remain behind secondary routes or menus.
- Widget and emulator tests must prove that a user can type and send from the
  main surface without opening raw terminal.

## Validation

The decision is validated when:

1. opening a paired project shows one selected-agent chat timeline;
2. the bottom composer accepts multiline input and remains usable with the
   Android soft keyboard;
3. sending writes through a CCB-validated selected-agent terminal session and
   creates visible pending/sent/failed-or-echoed state in the timeline;
4. agent replies or callback/comms events appear as readable Markdown cards;
5. raw terminal is reachable only through an explicit Open Terminal action;
6. the local Android Emulator loopback smoke covers type-send-read without any
   public route or physical device.
