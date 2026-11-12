# Open Questions

Date: 2026-05-27

## Codex

- Does the current Codex managed-home hook configuration require an explicit
  trust record, or is projected managed config sufficient?
- Which Codex failure event should map to `failed` versus recoverable
  `pending` when a turn is interrupted or blocked?
- Should Codex app-server be evaluated immediately after hook activity lands,
  or only after sidebar false-idle is fixed?
- Which Codex status-line details are stable enough to parse as structured
  `runtime_status` fields rather than plain display text?
- Which `capture-pane` flags best preserve current Codex status-line state
  without making parser input too noisy?
- Is `pipe-pane` sufficient as the low-latency output-freshness signal, or does
  Codex TUI repaint behavior require a current-screen capture after each
  important transition?
- When Codex exits during startup before `capture-pane` can read the current
  screen, should pipe-pane stderr/raw output become a separate explicit
  acquisition source for `source_status=error`, or should ProjectView report
  only `pane_dead` until a current-screen capture sees provider error text?
- Can approval-wait be forced safely in an isolated test Codex home, or does it
  require an opt-in real-account/manual lane?
- Which Codex pane-probe artifacts can be sanitized and committed as parser
  fixtures without leaking prompt, reply, credential, or account details?

## Claude

- Which Claude `Notification` payloads mean "waiting for user" rather than
  ordinary idle notification?
- Can Claude activity status be sourced entirely from hooks, or does sidebar
  failure detection also need a bounded session-log watcher?
- How long should `Stop` with running background tasks keep the agent active
  before freshness fallback takes over?
- Which Claude pane/status messages should be considered durable API for
  `waiting_for_user` versus provider-specific display copy?

## ProjectView Consumers

- Should `runtime_status.state` expose `stalled` separately from `reconnecting`
  in the first schema, or should both map to `pending` detail until live
  evidence proves the distinction is stable?
- Should mobile gateway conversation status events include the full redacted
  `runtime_status` object or only a compact summary plus the object on project
  agent rows?
- Which initial smoothing constants should ship after live validation:
  `working_min_hold_s`, `idle_confirm_s`, `reconnect_grace_s`,
  `stalled_after_s`, and `pane_capture_min_interval_s`?
- Does ProjectView need a small in-memory previous-status cache for smoothing,
  or can v1 derive stable transitions entirely from existing evidence
  timestamps?

## Testing

- Which local fault proxy should be the standard manual test tool for API
  disconnect and stream-cut scenarios?
- Should release automation allow a "manual fault lane evidence attached"
  marker when provider credentials cannot run in CI?
