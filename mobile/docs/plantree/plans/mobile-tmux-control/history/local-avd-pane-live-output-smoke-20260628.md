# Local AVD Pane Live-Output Smoke 2026-06-28

Status: Partial pass with source fixture blocker.

## Scope

Validate the first smooth-conversation app package on a real Android Emulator
connected to a server-wide mobile gateway, not fake/demo mode.

## Environment

- App: current `ccb_mobile` worktree debug APK built and installed on
  `emulator-5554`.
- Gateway: `/home/bfly/yunwei/ccb_source_mobile_update_simple/ccb_test install mobile`
  from `/home/bfly/yunwei/test_ccb2`.
- Gateway URL: `http://127.0.0.1:18999`.
- ADB route: `adb reverse tcp:18999 tcp:18999`.
- Gateway mode: `loopback_server_registry`.
- Project list: real server-wide projects, including `ccb_mobile`,
  `ccb_source`, `test_ccb2`, `test_ccb2_alpha`, and `test_ccb2_beta`.

## Passing Evidence

- The app opened the real server-wide project list after debug-profile pairing.
- `test_ccb2` opened from the server-wide list and rendered real project
  windows/agents and retained conversation history.
- Phone send used the pane-backed path: the sent text appeared as the exact
  user input without adding a new `CCB_REQ_ID`, `mobile_gateway`, or ask-job
  wrapper.
- The app rendered terminal output from the selected pane after send.
- The app rendered a short `Working` state after send and, after the follow-up
  app fix, cleared that state once the first pane output or terminal notice was
  received. A later dump showed no stuck `Working`/`Refreshing` status.
- The app still exposes explicit `Refresh conversation` and `Send Tab` controls
  on the selected-agent page.

Volatile local artifacts from the run:

- `/tmp/ccb_after_reinstall.png`
- `/tmp/ccb_testroot_open.png`
- `/tmp/ccb_new_probe_after_send.png`
- `/tmp/ccb_new_probe_after_wait.png`
- `/tmp/ccb_new_probe_after_wait.xml`

## Source Fixture Blocker

The controlled send reached the selected pane path, but the current source
fixture/gateway returned:

```text
open terminal failed: terminal does not support clear
```

This happened for both `test_ccb2_alpha` and the `test_ccb2` root project. It
blocks claiming a complete provider-reply or `/status` acceptance pass from
this run. The app-side behavior is improved and observable, but final
conversation acceptance still needs a source-side pane-backed fixture that can
open a real provider terminal session cleanly.

## Verification

- App focused tests:
  `flutter test test/project_home_server_projects_widget_test.dart
  test/agent_pane_event_coordinator_test.dart
  test/conversation_refresh_scheduler_test.dart`
  passed.
- App full tests: `flutter test` passed `403` tests.
- `git diff --check` passed.

## Follow-Up

- Fix or replace the source-side real-project fixture so selected-agent
  terminal open succeeds without `terminal does not support clear`.
- Re-run real AVD cases for `/status`, provider reply, and long-running output
  after the source fixture passes the Real Project Fixture Gate.
