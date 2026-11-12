# Decision 012: Agent-First Project Workspace

Date: 2026-06-20

## Status

Accepted.

Updates the default product surface from Decisions
[004](004-tmux-first-server-remote.md) and
[005](005-native-flutter-tmux-first-client.md) while preserving their
server-remote and CCB-authority boundaries.

## Context

Manual emulator testing showed that a terminal-first project view consumes the
phone viewport with project names, runtime ids, gateway URLs, pairing state,
and raw terminal details before the user can see the selected agent's work.

The user wants the top of the project page to work as an agent switcher, and
the whole page to show exactly one selected agent. Markdown and CCB-authored
content should be readable as content, not inferred from a tmux stream.

## Decision

The default project view is an agent-first workspace:

- top area shows the agent switcher;
- main body shows exactly one selected agent;
- selected-agent content includes state, current task, Comms/callbacks,
  Markdown/content, readable terminal history, and primary actions;
- project path, gateway URL, pairing code, runtime id, route diagnostics, and
  low-level terminal state move behind connection details or settings;
- tapping an agent switches the selected agent by default;
- focus and raw terminal entry are explicit actions;
- Open Terminal enters raw tmux/terminal control mode for the selected
  agent/window;
- raw terminal remains available for pane-level control, debugging, and
  operations not yet represented by CCB APIs;
- structured CCB content is the authoritative source for Markdown/math
  reading; readable terminal history from pane capture/tmux scrollback is a
  best-effort fallback or observability surface only.

Remote access direction is unchanged: CCB Relay is the default not-on-LAN route
from [Decision 011](011-relay-default-remote-route.md), while Cloudflare
Tunnel remains an advanced/self-hosted route provider.

## Consequences

- The next mobile app slice should reshape the first project viewport before
  adding more route-provider complexity.
- Widget tests should prove that agent taps switch the selected agent and do
  not open the terminal.
- Project/gateway/runtime diagnostics should be available but should not
  dominate the first viewport.
- Existing terminal transport, gateway terminal tokens, reconnect/resume, and
  tmux target validation remain required, but are no longer the default
  reading surface.
- If the app cannot render useful selected-agent content from current
  ProjectView/Comms data, the missing content contract should be recorded as a
  source-side API gap before inventing terminal scraping.
- If terminal history is needed for readability, the first source should be
  current pane plus retained tmux scrollback; project-lifetime history requires
  a separate recorder/journal and should not be implied by capture-pane alone.

## Validation

The decision is validated when:

1. opening a project shows a top agent switcher and one selected-agent
   workspace;
2. project path, gateway URL, pairing code, runtime id, and route diagnostics
   are hidden behind a details affordance;
3. tapping a different agent switches the selected agent without opening raw
   terminal;
4. Open Terminal explicitly enters the existing raw terminal control mode;
5. Markdown/content display uses structured CCB content when available and
   treats pane snapshots/readable terminal history as best-effort fallback.
