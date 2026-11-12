# Agent Terminal Mode Remote Pane Control

Date: 2026-07-04
Status: Ready for implementation

## Scope

Land a first-class Terminal mode for each selected CCB agent inside the mobile
project workspace. When the user opens an agent's Terminal mode, the app should
show the raw tmux pane stream for that agent through the existing terminal
emulator and allow direct pane input/control.

This is not a replacement for the chat-first agent workspace. Normal project
use still defaults to chat. Terminal mode is an explicit per-agent control
mode for inspection, debugging, and direct pane operation.

## Current Source Facts

Existing source already provides most of the transport base:

- `lib/mobile_gateway/service.py` exposes `POST /v1/projects/<id>/terminals`
  and `/v1/terminals/<id>` WebSocket handling behind `terminal_input` scope.
- `lib/mobile_gateway/terminal.py` creates a server-side PTY running
  `tmux -S <socket> attach-session -t <pane-or-session>` and streams output.
- `mobile/app/lib/transport/gateway_terminal_transport.dart` already opens
  terminal handles, writes bytes, pastes text, resizes, reconnects, and renews
  expired handles.
- `mobile/app/lib/features/terminal/fake_terminal_screen.dart` already uses
  `package:xterm/xterm.dart` and `TerminalView` for both fake and live gateway
  terminal surfaces.
- `mobile/app/lib/features/project_home/project_home_screen.dart` already has
  an agent terminal route entry through `_openAgentTerminal`.

The main work is therefore not to introduce a terminal dependency from
scratch. The work is to promote the existing live terminal route into a
polished per-agent Terminal mode, tighten pane-control input coverage, and
prove the behavior on a real Android Emulator.

## Product Semantics

Interpret "no rendering" as:

- no chat bubbles, Markdown, provider transcript parsing, terminal-history
  block splitting, or semantic output decoration inside Terminal mode;
- still use a terminal emulator (`xterm`/`TerminalView`) to interpret ANSI,
  cursor movement, alternate screen, colors, erase sequences, and terminal
  resize behavior.

Interpret "all pane streams" as:

- initial current screen repaint from tmux attach;
- subsequent live output bytes from the attached pane/session stream;
- input echo and prompt changes as observed through tmux;
- alternate-screen applications such as `top`, pagers, and editors must render
  as terminal state, not as appended text blocks.

Scrollback beyond what the terminal emulator retains can remain bounded in the
first implementation. The selected-agent conversation timeline and readable
terminal history remain separate surfaces.

## Non-Goals

- Do not make raw terminal the default project page.
- Do not add arbitrary tmux split/kill/new/rename operations.
- Do not bypass CCB focus, namespace epoch, target validation, or device
  `terminal_input` scope.
- Do not implement this in the retired `ccb_mobile` checkout.
- Do not test by sending exploratory prompts into active user work projects.

## Implementation Packages

### Package A: Agent Workspace Mode Switch

Goal: expose Terminal mode from the selected-agent workspace rather than only
as a separate fallback route.

Expected source areas:

- `mobile/app/lib/features/project_home/project_chat_header.dart`
- `mobile/app/lib/features/project_home/project_home_scaffold_host.dart`
- `mobile/app/lib/features/project_home/project_home_screen.dart`
- `mobile/app/lib/features/terminal/fake_terminal_screen.dart`
- new or extracted terminal widget files under
  `mobile/app/lib/features/terminal/`

Requirements:

- Add a compact `Chat / Terminal` mode switch for the selected agent.
- Keep Chat as the default mode when entering a project or changing agents.
- Terminal mode must receive the current `project_id`, `agent_name`,
  `MobileCcbRepository`, and `TerminalTransport`.
- Reuse `CcbProjectView.terminalTargetForAgent(agentName)` as the target
  resolver.
- Dispose or pause the terminal session when leaving Terminal mode, changing
  agent, closing project, or unmounting the widget.
- Keep the older explicit Open Terminal route only if useful as a compatibility
  route; it must share the same terminal pane component instead of duplicating
  behavior.

Acceptance:

- Widget tests prove switching Chat -> Terminal -> Chat does not remove the
  normal composer or timeline state.
- Widget tests prove changing selected agent opens a terminal target for the
  new agent, not the old agent.
- Fake mode remains supported without gateway transport.

### Package B: Direct Terminal Surface

Goal: make Terminal mode feel like direct pane control, not a form-based input
panel.

Expected source areas:

- `mobile/app/lib/features/terminal/fake_terminal_screen.dart`
- new terminal toolbar/controller files under
  `mobile/app/lib/features/terminal/`
- focused tests under `mobile/app/test/`

Requirements:

- Use `TerminalView` as the primary surface.
- Remove or demote the current command `TextField` from the main live control
  path; user typing in `TerminalView` should write to `TerminalSession`.
- Add a compact terminal toolbar for soft-keyboard users:
  `Esc`, `Tab`, `Ctrl`, arrows, paste, size sync, reconnect, and a small
  overflow for less common keys.
- Preserve hardware keyboard behavior while Terminal mode has focus.
- Provide visible connection state without covering terminal content.
- Keep text sizes, toolbar buttons, and status text stable on phone and wide
  layouts.

Acceptance:

- Widget tests cover toolbar actions and ensure labels/buttons do not overflow
  on a phone viewport.
- App-side tests verify toolbar actions call `writeBytes`, `paste`, `resize`,
  and `reconnect` with the expected commands/bytes.

### Package C: Pane Input Coverage

Goal: support the control keys needed for real remote pane operation.

Expected source areas:

- `lib/mobile_gateway/terminal.py`
- `test/test_mobile_gateway_terminal.py`
- possibly `mobile/app/lib/transport/gateway_transport.dart` if an explicit
  key frame is chosen.

Preferred first implementation:

- Extend byte-sequence handling in `_send_tmux_terminal_bytes()` for common
  ANSI sequences emitted by Flutter `TerminalView`:
  arrow keys, Home/End, Delete, PageUp/PageDown, and common Ctrl combinations.
- Keep text input and paste using the current literal paths.
- If byte decoding becomes ambiguous, add a small explicit key-command frame
  rather than trying to infer every terminal sequence from text.

Required safety:

- Every input frame continues to use terminal token authentication,
  monotonically increasing input sequence checks, and target revalidation.
- Input must continue targeting only the validated pane id/agent target for
  the handle.
- Unsupported bytes fail closed with an error instead of writing to a wrong
  pane or session.

Acceptance:

- Python tests assert tmux `send-keys` calls for Enter, Tab, Esc, Ctrl-C,
  Ctrl-D, Ctrl-U, Backspace, arrows, Home/End, Delete, PageUp/PageDown, and at
  least one unsupported-byte failure.
- Gateway tests prove stale namespace epoch and wrong terminal token still fail
  closed.

### Package D: Resize, Reconnect, And Lifecycle Hardening

Goal: make Terminal mode robust under mobile lifecycle changes.

Expected source areas:

- `mobile/app/lib/transport/gateway_terminal_transport.dart`
- `mobile/app/lib/features/terminal/`
- existing gateway terminal tests.

Requirements:

- Preserve existing terminal-token renewal and resume-cursor behavior.
- Trigger resize from TerminalView layout changes and orientation changes, but
  avoid excessive resize spam.
- On app resume, reconnect to the same validated target or surface a clear
  stale-target error requiring refresh.
- Closing Terminal mode must close/disconnect the handle without killing CCB,
  the project tmux session, or provider panes.

Acceptance:

- Flutter tests cover lifecycle reconnect and dispose.
- Python/gateway tests cover disconnect vs close semantics where applicable.

### Package E: Emulator Evidence Package

Goal: prove the feature on a real Android Emulator before review acceptance.

Required environment:

- Build and install from `/home/bfly/yunwei/ccb_source/mobile/app`.
- Pair through the server-wide mobile gateway.
- Use a dedicated disposable real CCB test project, preferably under
  `/home/bfly/yunwei/test_ccb2`.
- Do not send exploratory terminal input into `/home/bfly/yunwei/ccb_source`,
  `/home/bfly/yunwei/ccb_mobile`, or other active user work projects.

Minimum real-AVD scenarios:

1. Open server-wide project list and enter the disposable project.
2. Select an agent and switch to Terminal mode.
3. Verify the terminal shows the selected agent's pane stream, not a fake
   transcript or chat bubble.
4. Run a simple echo command and prove output appears in the terminal.
5. Run `top` or an equivalent alternate-screen/refreshing command and prove it
   updates in place instead of appending repeated text.
6. Send `Ctrl-C` from the toolbar and prove the running command stops.
7. Use arrow keys and Tab in a shell/provider prompt and prove the pane
   receives them.
8. Rotate the emulator or change layout and prove resize is sent without
   breaking the project session.
9. Temporarily break and restore `adb reverse` or the gateway route and prove
   reconnect either resumes or fails closed with a recoverable refresh path.
10. Switch back to Chat mode and prove the normal conversation timeline and
    composer still work.

Evidence packet:

- emulator screenshots for Chat mode, Terminal mode, refreshing terminal
  command, toolbar controls, and post-reconnect state;
- a short screen recording for live refresh and input control;
- gateway logs showing terminal open, input, resize, disconnect/reconnect, and
  no token/scope failures;
- test command output for focused Python and Flutter tests;
- APK path and sha256;
- source commit hash;
- explicit statement that `ccb_mobile` implementation files were not edited.

## Review Rejection Gates

Reject the implementation if any of these are true:

- code changes land under the retired `ccb_mobile` implementation tree;
- Terminal mode uses chat bubbles, Markdown, or terminal-history blocks for the
  live pane display;
- app text input only works through a separate command form and not the
  terminal surface/toolbar;
- special keys are not tested at the gateway boundary;
- pane identity relies on stale `pane_id` alone without CCB project/agent and
  namespace epoch validation;
- emulator evidence uses fake/demo project data as the main proof;
- the worker cannot provide real screenshots/recording of live terminal
  refresh and `Ctrl-C` behavior;
- closing the phone Terminal mode kills or restarts `ccbd`, provider panes, or
  the project tmux session.

## Open Edges

- The first package can use the existing gateway PTY attach. If emulator
  evidence shows phone resize damages desktop tmux layout, a follow-up tmux
  control-mode or managed grouped-session spike is required before widening
  release scope.
- Mouse mode, external keyboard function keys, and high-volume scrollback are
  useful but not P0 unless the emulator evidence reveals they are required for
  basic pane control.
- If `TerminalView` emits byte sequences that tmux `send-keys` cannot safely
  represent, prefer an explicit gateway key frame over broad lossy decoding.
