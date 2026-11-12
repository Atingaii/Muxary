# Decision 013: Readable Terminal History

Date: 2026-06-20

## Status

Accepted.

Extends [Decision 012](012-agent-first-project-workspace.md) without changing
the structured-content authority boundary.

## Context

The user wants the selected-agent workspace to show more than a polished
current terminal screen. On phone, the user should be able to drag vertically
through agent history, read logs/code/diffs/test output, and still open raw
terminal only when direct control is needed.

Tmux can expose the current pane and retained scrollback immediately, but it
cannot reconstruct output older than the pane's history limit or overwritten by
full-screen/control-sequence behavior. Full project-lifetime terminal history
needs an explicit recorder/journal.

## Decision

Add a readable terminal history surface to the selected-agent workspace:

- default selected-agent body can show structured CCB content plus readable
  terminal history;
- MVP history source is current tmux pane capture plus retained scrollback;
- the UI must allow vertical scrolling through retained history;
- the renderer should clean ANSI/control noise and group command output, logs,
  code blocks, diffs, stack traces, and Markdown-looking text into readable
  blocks;
- terminal-derived content is labeled best-effort with freshness, pane,
  namespace, and stale-evidence warnings;
- raw terminal remains an explicit Open Terminal control/debug mode;
- structured CCB message/reply/artifact content remains authoritative for
  Markdown/math reading;
- complete project-lifetime history requires a future terminal journal and is
  not promised by tmux capture alone.

## Consequences

- The next app/content slice should include a scrollable readable history model
  or fixture, not only a single pane snapshot.
- Gateway/source work may need a safe `terminal_history_get` or equivalent route
  that captures pane scrollback through current CCB project identity and
  namespace evidence.
- The app should preserve scroll position while refreshing or appending newer
  output.
- Tests should cover long retained history, stale pane evidence labels, and the
  explicit raw-terminal fallback.
- Security rules for terminal-derived text remain conservative: no automatic
  link execution, no arbitrary local file reads, and raw source/fidelity remains
  available.

## Validation

The decision is validated when:

1. opening an agent shows a readable history surface that can scroll through
   retained tmux pane history;
2. code/log/diff/error blocks are more readable than raw terminal text;
3. refresh/new output does not unexpectedly jump the user's scroll position;
4. UI labels terminal-derived content as best-effort scrollback;
5. Open Terminal remains the path for raw tmux control.
