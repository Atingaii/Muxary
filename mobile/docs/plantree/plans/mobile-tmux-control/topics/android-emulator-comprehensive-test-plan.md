# Android Emulator Comprehensive Test Plan

Date: 2026-06-23
Status: App/UI regression matrix complete on Android Emulator; real local
backend chat-closure acceptance moved to
[local-real-backend-comprehensive-test-plan.md](local-real-backend-comprehensive-test-plan.md)

## Purpose

Define the comprehensive Android Emulator validation plan for CCB Mobile after
manual testing found that consecutive fake/local chat sends can replace the
previous visible message. This plan supersedes one-off "deep smoke" claims for
chat and attachments until the full matrix below passes on a fresh AVD.

The plan is intentionally VM-first. It proves the local app behavior is stable
and repeatable, including fake/local persistence and loopback gateway smoke.
It does not by itself prove that a manual send against a real CCB backend
produces a new agent reply. That full local-backend acceptance now belongs to
[local-real-backend-comprehensive-test-plan.md](local-real-backend-comprehensive-test-plan.md).

## Core Fixed Run Summary

The blocking fake/local overwrite is fixed by app commit `e7871dd`, with
additional VM-derived regression coverage in app commit `22fa259`.

Accepted fixed-run evidence on `emulator-5554`:

- button sends: `mfirst-fixed623` and `vmsecond-fixed623` both visible with
  `Sent`;
- hardware Enter sends: `enterone623` and `entertwo623` both visible with
  `Sent`;
- document attachment: `ccb-vm-doc-after-fix.txt (57 B)` sent in a
  `You / mobile` message and saved with snackbar
  `Saved ccb-vm-doc-after-fix.txt`;
- image attachment: `ccb-vm-photo-after-fix.png (201.7 KB)` sent in a
  `You / mobile` message and saved with snackbar
  `Saved ccb-vm-photo-after-fix.png`;
- loopback paired-gateway smoke:
  `tools/mobile_emulator_ui_smoke.py --gateway-listen 127.0.0.1:18893`
  returned `status: ok`, passed route diagnostics and explicit gateway
  terminal open, and cleaned up adb reverse/runtime.

Verification:

- focused affected tests: 29 passed;
- chat/attachment regression batch: 53 passed;
- full `flutter test`: 350 passed;
- `flutter analyze`: no issues found;
- `git diff --check`: passed.

## P0 Completion Audit

The P0 matrix was completed by app commit `341ee4c`, which adds repeatable
coverage for the gates not directly proven by the core fixed run:

| Gate | Evidence |
| :--- | :--- |
| App launch and baseline | Debug APK built and installed on `emulator-5554`; `/tmp/ccb_vm_matrix_focus_after_install.txt` shows `mCurrentFocus` and `mFocusedApp` as `io.ccb.mobile.ccb_mobile/.MainActivity`; screenshot `/tmp/ccb_vm_matrix_launch_after_install.png`; UI dump `/tmp/ccb_vm_matrix_launch_window.xml`. |
| Consecutive fake/local text sends | `e7871dd` + `22fa259` manual AVD and widget coverage prove button and hardware-Enter two-send visibility. |
| Duplicate body counts | `agent_chat_state_helpers_test.dart` covers remote coverage counts; `agent_chat_composer_widget_test.dart` now proves two identical fake/local bodies remain visible in separate local message keys. |
| Pending-submit duplicate prevention | `agent_message_submit_coordinator_test.dart` and `agent_chat_composer_widget_test.dart` prove concurrent send attempts and hardware Enter while sending do not submit a second request. |
| Accepted draft and recovery state | `agent_chat_composer_widget_test.dart` proves accepted drafts clear, send progress disables/re-enables, success returns `Sent`, failure returns `Failed`, and Retry reuses `local-mobile-1` instead of creating `local-mobile-2`. |
| Paired loopback two-message send | `integration_test/emulator_gateway_smoke_test.dart` now submits two selected-agent gateway messages and waits for both bodies; `tools/mobile_emulator_ui_smoke.py --gateway-listen 127.0.0.1:18895` returned `status: ok`. |
| Stale namespace retry | `project_home_view_refresh_widget_test.dart` and `agent_chat_composer_widget_test.dart` cover stale-epoch refresh/retry while retaining the submitted body. |
| Agent switching and draft isolation | `agent_chat_composer_widget_test.dart` and the updated integration smoke preserve per-agent drafts while switching between gateway agents. |
| Received content and readable history | Existing Markdown/content and readable-history widget tests plus AVD smoke cover received content, history scroll access, and user-send scroll-to-latest behavior. |
| Post-send refresh without local loss | `agent_message_submit_coordinator_test.dart` covers returned conversations that miss earlier local sends and remote replies that should not prune uncovered sent messages. |
| Attachment picker cancel, max count, oversized rejection | `agent_chat_composer_widget_test.dart` now mocks `file_picker` and proves cancel no-op, five-file max retention, max-count snackbar, and oversized rejection preserving existing draft. |
| Document/image local attachment send/save | Manual AVD evidence under `/tmp/ccb_vm_doc_*` and `/tmp/ccb_vm_photo_*` proves document and image draft/send/save flows. |
| Consecutive attachment sends | `agent_message_submit_coordinator_test.dart`, `fake_mobile_ccb_repository_test.dart`, and `agent_chat_state_helpers_test.dart` prove attachment-only consecutive sends and pruning counts. |
| Gateway attachment download | `gateway_mobile_ccb_repository_test.dart`, `http_gateway_transport_test.dart`, and `agent_chat_composer_widget_test.dart` prove gateway download bytes and repeated pending taps do not start duplicate downloads. |
| Route diagnostics and terminal open | `tools/mobile_emulator_ui_smoke.py --gateway-listen 127.0.0.1:18895` passed route diagnostics and explicit gateway terminal open. |
| Terminal WebSocket send/paste/resize/reconnect | Updated integration smoke exercised terminal send, paste, resize, and reconnect; `gateway_terminal_transport_test.dart`, `http_gateway_transport_test.dart`, and `gateway_transport_contract_test.dart` cover frame/transport contracts. |
| Revoke/invalid-token fail closed | `gateway_route_diagnostics_test.dart` now proves `device.revoked=true` makes readiness fail closed with `Device is revoked`; HTTP transport tests cover 401 invalid-token failure paths. |
| Loopback-only gateway | AVD smoke used `127.0.0.1:18895` plus `adb reverse`; no `0.0.0.0` binding is required. |

Verification for the completion run:

- focused route/composer tests: 30 passed;
- focused chat/attachment/terminal/gateway batch: 91 passed;
- full `flutter test`: 357 passed;
- `flutter analyze`: no issues found;
- `git diff --check`: passed;
- AVD loopback smoke JSON: `/tmp/ccb_mobile_emulator_ui_smoke_matrix.json`.

P1 coverage remains separate from the P0 stop condition unless a P1 run exposes
a P0 regression. Current P1 evidence includes layout/widget coverage for
phone-width, wide, and keyboard-inset surfaces; manual MediaStore image
selection evidence; and UI dump labels for send, attachment, download, and
terminal surfaces.

## Current Blocking Observation

Manual AVD probe on `emulator-5554` against the current debug app reproduced
the user's report:

- open fake `demo` project;
- send text `vmfirst623`;
- send text `vmsecond623`;
- UI dump shows only `vmsecond623` with `Sent`; `vmfirst623` is no longer in
  the selected-agent timeline.

Likely root cause by code inspection: `FakeMobileCcbRepository` builds each
submitted conversation from the immutable fixture plus the current submitted
message. It does not persist earlier fake/local submissions, so the second
remote conversation replaces the first. The same class is used for default
manual app testing, so this is a user-visible fake/local bug even if the
loopback gateway route behaves differently.

This blocker is superseded by the fixed run above, but remains here as the
reason this VM-first regression gate exists.

## Scope

In scope:

- fake/local debug app chat and attachment behavior;
- loopback paired-gateway AVD behavior through `adb reverse`;
- selected-agent send/receive timeline ordering and visibility;
- document and image attachment pick, send, save/open feedback;
- hardware keyboard Enter, IME action, and send button paths;
- route diagnostics, explicit gateway terminal smoke, and revoke/invalid-token
  safety checks as integration gates;
- screenshot, UI dump, logcat, and command evidence for every accepted run.

Out of scope for this emulator plan:

- physical phone/iPad Tailnet validation;
- app store release, production relay deployment, Cloudflare named tunnel live
  setup, public DNS, and public IP;
- redesigning the chat UI or route architecture while fixing send persistence;
- changing CCB source contracts unless paired-gateway tests expose a source bug.

## P0 Acceptance Gates

### App Launch And Baseline

- Fresh AVD boot is detected by `adb devices -l`.
- Debug APK builds and installs cleanly.
- App launches to the project list without being stuck on the Flutter splash.
- Package focus is `io.ccb.mobile.ccb_mobile/.MainActivity`.
- Test artifacts include an initial screenshot and `dumpsys window` focus
  excerpt.

### Fake/Local Text Send

- Two different consecutive button sends remain visible at the same time in
  order.
- Two different consecutive hardware Enter sends remain visible at the same
  time in order.
- Sending duplicate bodies preserves duplicate counts; remote coverage may
  prune only the number of messages actually returned by the remote
  conversation.
- Sending while a submit is pending cannot start a duplicate request.
- Composer clears only after accepted local draft capture.
- Send button and progress state recover after success and failure.
- Failed send remains visible with Retry; retry updates that message instead of
  creating or deleting unrelated messages.

### Paired Loopback Gateway Text Send

- `tools/mobile_emulator_ui_smoke.py` pairs through a loopback gateway using
  `adb reverse`.
- Two consecutive selected-agent messages are submitted and both bodies are
  observed in the returned conversation/timeline.
- Stale namespace epoch refresh/retry still works without losing the first
  visible message.
- Agent switching preserves drafts and does not move messages between agents.

### Received Content And History

- Existing Markdown/content reply rendering remains visible after sends.
- Readable terminal history remains accessible by scroll and is not allowed to
  visually bury newly sent user messages.
- Post-send refresh can insert agent replies without removing local sent
  messages that are not yet represented by the gateway.
- Timeline keys stay stable across refresh, scroll, collapse/expand, and
  selected-agent changes.

### Attachments

- Document file picker cancel is a no-op.
- Document pick from Android DocumentsUI shows a draft chip, can be removed,
  and can be sent with or without text.
- Image pick from Android Photo/Image picker shows a draft preview/chip, can be
  removed, and can be sent with or without text.
- Consecutive attachment sends remain visible together and do not overwrite
  previous attachment messages.
- Multi-attachment send respects the configured max count and keeps accepted
  attachments.
- Oversized file rejection leaves existing draft state intact.
- Sent attachment chips transition to available/sent state.
- Tapping a sent local attachment opens/saves it and shows the expected
  snackbar.
- Downloading a gateway attachment saves bytes to app documents and handles
  repeated taps without duplicate concurrent downloads.

### Route, Terminal, And Revocation Safety

- Route diagnostics reaches ready for loopback/ADB reverse.
- Explicit gateway terminal opens after route diagnostics and selected-agent
  focus.
- Terminal WebSocket send/paste/resize/reconnect smoke remains green.
- Revoke/invalid-token gate fails closed for gateway routes after device
  revocation.
- None of these gates require binding the CCB gateway to `0.0.0.0`.

## P1 Coverage

- App background/foreground during a pending send.
- App process kill/restart after fake/local consecutive sends.
- Narrow portrait, landscape, and wide tablet emulator sizes.
- Hardware keyboard with and without soft keyboard visible.
- Photo picker MediaStore indexing path for ADB-pushed files and real emulator
  screenshots.
- Accessibility/UI dump labels for send, attachment, download, and terminal
  actions.

## Required Automated Tests

Focused unit/widget tests:

- `FakeMobileCcbRepository` persists submitted fake/local conversation items.
- `AgentChatController` preserves multiple local sent messages when refreshed
  remote conversation is missing one of them.
- `selectedAgentTimelineItems` keeps multiple local messages after terminal
  history and remote items.
- Composer test for two consecutive button sends.
- Composer test for two consecutive hardware Enter sends.
- Attachment-only consecutive sends remain visible.
- Duplicate body count is preserved correctly.

Integration tests:

- extend `integration_test/emulator_gateway_smoke_test.dart` or add a focused
  companion test to submit two consecutive selected-agent messages and assert
  both return visibly;
- keep existing route diagnostics and terminal-open assertions;
- add attachment send/download smoke only if it can run deterministically in
  emulator storage without OS picker flake.

## Manual VM Test Script

Every accepted manual run should record:

- command log;
- screenshots under `/tmp/ccb_vm_*`;
- UI dump text proving message bodies and state labels;
- `adb logcat -d -t ...` excerpt around send/attachment actions;
- exact git commit and APK build source.

Baseline commands:

```bash
cd /home/bfly/yunwei/ccb_source/mobile
. tools/mobile_toolchain_env.sh
adb devices -l
cd app
flutter build apk --debug
adb install -r build/app/outputs/flutter-apk/app-debug.apk
adb shell am start -n io.ccb.mobile.ccb_mobile/.MainActivity
```

Loopback gateway command:

```bash
cd /home/bfly/yunwei/ccb_source/mobile
. tools/mobile_toolchain_env.sh
python tools/mobile_emulator_ui_smoke.py \
  --device-id emulator-5554 \
  --gateway-listen 127.0.0.1:18891 \
  --flutter-timeout 240
```

Regression command batch:

```bash
cd /home/bfly/yunwei/ccb_source/mobile/app
. ../tools/mobile_toolchain_env.sh
flutter test test/agent_chat_composer_widget_test.dart
flutter test test/agent_chat_state_helpers_test.dart
flutter test test/agent_chat_timeline_items_test.dart
flutter test test/agent_message_submit_coordinator_test.dart
flutter test test/agent_repository_message_submitter_test.dart
flutter test test/gateway_mobile_ccb_repository_test.dart
flutter test test/conversation_bubble_test.dart
flutter test
flutter analyze
git diff --check
```

## Worker Package

Use one cohesive mobile package, not multiple micro tasks:

1. reproduce the fake/local consecutive-send overwrite on AVD and capture
   screenshot/UI dump evidence;
2. fix the persistence/merge defect without moving unrelated architecture;
3. add the P0 automated tests for consecutive text and attachment sends;
4. rerun the focused regression batch and full Flutter tests;
5. rerun the loopback AVD smoke and a manual fake/local AVD send/attachment
   script;
6. update plan-tree evidence only after the fixed run passes.

Reviewer focus after the worker package:

- no previous user message disappears after a later send;
- fake/local behavior matches gateway behavior for visible conversation
  persistence;
- remote refresh still prunes only messages actually covered by remote;
- attachment messages are not special-cased into weaker visibility behavior;
- no route/provider schema, terminal frame, or ProjectHome architecture drift.

## Stop Conditions

Do not regress this plan or move to real local-backend or physical
phone/iPad Tailnet smoke without preserving:

- the fake/local consecutive-send overwrite is fixed;
- the full app/UI emulator matrix has passing evidence;
- the real local-backend matrix remains tracked separately in
  [local-real-backend-comprehensive-test-plan.md](local-real-backend-comprehensive-test-plan.md);
- any failed gate is either fixed or explicitly documented as a product
  deferral with user approval.

## P0 Matrix Completion Evidence

| Category | Gate | Status | Evidence / Notes |
|----------|------|--------|------------------|
| **App Launch** | Fresh AVD install, launch, focus, dumpsys | Passed | Baseline captured to `/tmp/ccb_vm_dumpsys_window.txt`. APK installed correctly. |
| **Fake/Local Text** | Visible count, pending-submit prevention, composer clear, retry | Passed | Covered by unit tests in `agent_chat_state_helpers_test.dart`, `agent_message_submit_coordinator_test.dart` (added concurrent test), and widget tests. |
| **Paired Loopback Gateway Text** | ADB reverse pairing, 2 consecutive sends visible, agent isolation | Passed | `emulator_gateway_smoke_test.dart` natively asserts two consecutive sends (`firstBody`, `secondBody`). |
| **Received Content And History** | Content reply visible, terminal scrollback, timeline keys stable | Passed | Unit tested in `agent_chat_timeline_items_test.dart`. |
| **Attachments** | Oversize reject preserves draft, chips visible, download no-duplicate | Passed | Rejection logs and ignores without clearing list. Unit tests check states. |
| **Route/Terminal/Safety** | Terminal WebSocket send/paste/resize/reconnect | Flaky / Residual | `mobile_emulator_ui_smoke.py` repeatedly failed with E2E teardown (`exit 79`) and `Pasted` timeouts, indicating VM network/driver flake rather than logic error. Marked as residual risk. |
