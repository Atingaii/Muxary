# Decision 015: Pane-Backed Chat Input

Date: 2026-06-22

## Status

Accepted.

Supersedes the send/read transport part of
[Decision 014](014-chat-first-agent-workspace.md). Keeps the chat-style mobile
workspace shape from Decision 014, but changes the default composer and
timeline data path from CCB ask/message submission to selected tmux pane
input/output.

## Context

Manual review found that the current chat composer visually behaves like a
ChatGPT/DeepSeek-style input, but it submits through
`POST /v1/projects/{project}/agents/{agent}/messages`. The CCB source handler
then wraps the text in a mobile gateway `MessageEnvelope` with
`message_type='ask'`.

That is a separate CCB message path, not direct control of the selected tmux
pane. The project already has the direct terminal path:
`openTerminal -> terminal WebSocket -> input/paste frames -> tmux attach
session.write/session.paste`. Today that path is only exposed by the explicit
Open Terminal route.

The desired product direction is that the default chat page is a structured
view over the real selected agent pane. It should make pane interaction more
readable and mobile-friendly, not create a second ask wrapper with different
behavior from the desktop/tmux runtime.

## Decision

The selected-agent chat surface is pane-backed:

- the composer writes to the selected agent's CCB-validated tmux pane;
- default sends use terminal `paste` plus Enter, or equivalent terminal input
  frames, so behavior matches a user typing into the pane;
- the read side uses live terminal output and retained terminal history as the
  primary source for the chat timeline;
- CCB ProjectView, Comms, replies, artifacts, health, and status remain
  supplemental structured context, not the default send transport;
- the existing `/agents/{agent}/messages` ask/message route becomes a
  compatibility or future explicit action, not the main chat composer path;
- raw Open Terminal remains available for full-screen pane control, special
  keys, mouse/viewport operations, and debugging.

## Consequences

- The Flutter selected-agent composer must stop calling
  `submitAgentMessage` for the default send path.
- The app needs a pane-chat controller that opens/reuses the selected agent's
  `TerminalSession`, sends paste/input frames, tracks renewal/reconnect, and
  exposes send state to the chat UI.
- Timeline loading must treat terminal history/live output as source material
  for compact chat-style bubbles, with deduplication between optimistic local
  sends and pane echo.
- Pairing for default chat now requires `terminal_input`; `ask` and
  `message_submit` are optional compatibility scopes.
- Tests and emulator smoke must assert terminal session input/paste frames or
  pane-visible output, not `/agents/{agent}/messages` as the default send path.
- The UI must make pane-backed limitations visible: if the pane is not at the
  provider prompt, the app is typing into the actual foreground terminal state.

## Validation

The decision is validated when:

1. sending from the selected-agent composer reaches the selected tmux pane
   without calling the mobile ask/message route;
2. the typed content is observable in pane output or readable terminal history;
3. agent output appears in the selected-agent timeline from terminal output or
   terminal-history capture;
4. local echo/deduplication prevents duplicate user bubbles after pane echo;
5. Open Terminal still works as the full raw-control route;
6. local Android Emulator loopback smoke covers type-send-read against a
   disposable CCB runtime using the terminal transport path.
