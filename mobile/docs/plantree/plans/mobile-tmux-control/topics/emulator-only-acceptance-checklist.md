# Emulator-Only Acceptance Checklist

Date: 2026-06-21
Status: Accepted

## Purpose

This is the audit checklist for
[goal-emulator-only.md](../goal-emulator-only.md). It turns the broad
emulator-only goal into concrete local proof points so completion is judged by
current evidence, not intent.

Public DNS, Cloudflare, production relay, public IP, physical phones, and app
store release are outside this checklist. They remain route-provider or release
follow-up work.

## Latest Local Smoke

Normal AVD smoke on 2026-06-21:

```bash
tools/mobile_emulator_ui_smoke.py \
  --gateway-listen 127.0.0.1:18877 \
  --gateway-timeout 30 \
  --flutter-timeout 300 \
  --harness-timeout 10
```

Result: `status: ok`; AVD `emulator-5554` boot-complete; `adb_reverse.mapping:
tcp:18877 tcp:18877`; gateway loopback URL `http://127.0.0.1:18877`; pairing
code present; Flutter integration smoke installed the debug APK and passed two
tests; pre/post harness `mobile_terminal_target_ok: true` for selected agent
`mobile_probe` pane `%2`; cleanup removed adb reverse, stopped gateway, and
unmounted the disposable CCB runtime.

Throwaway stop smoke on 2026-06-21:

```bash
tools/mobile_emulator_ui_smoke.py \
  --gateway-listen 127.0.0.1:18879 \
  --gateway-timeout 30 \
  --flutter-timeout 300 \
  --harness-timeout 10 \
  --include-lifecycle-stop
```

Result: `status: ok`; AVD `emulator-5554` boot-complete; `adb_reverse.mapping:
tcp:18879 tcp:18879`; Flutter integration smoke passed two tests; stop was
confirmed through the app; `post_harness.skipped: true` with reason
`lifecycle stop was requested by the AVD smoke`; cleanup removed adb reverse,
stopped gateway, and unmounted the disposable CCB runtime.

Both smoke runs emitted the existing non-fatal `mobile_scanner` Kotlin Gradle
Plugin warning. The `app_data_clear_returncode: 1` value is non-blocking for
these runs because the app was installed by the subsequent Flutter test step
and both integration tests passed.

## Checklist

| Gate | Status | Current Evidence | Next Audit Command |
| :--- | :--- | :--- | :--- |
| Android emulator app launch | Accepted | 2026-06-21 normal and stop AVD smokes built, installed, and launched the debug APK on `emulator-5554`. | Normal AVD smoke command above. |
| Local loopback gateway and adb reverse | Accepted | Normal smoke used `127.0.0.1:18877`; stop smoke used `127.0.0.1:18879`; both reported matching `adb reverse` mappings and cleanup. | Normal AVD smoke command above. |
| Isolated CCB runtime | Accepted | Both smokes created disposable projects under `/home/bfly/yunwei/test_ccb2`, started CCB, and unmounted via cleanup. | Normal AVD smoke command above. |
| Local pairing/claim | Accepted | Both smokes reported `pairing_code_seen: true`; integration UI claimed the loopback gateway before paired route checks. | Normal AVD smoke command above. |
| Project and agent discovery | Accepted | Pre/post harness reported selected agent `mobile_probe`, selected window `main`, namespace epoch `1`, and attachable pane evidence. | Normal AVD smoke command above. |
| Agent-first switcher | Accepted | Integration test drives fake agent switching without terminal navigation; widget tests cover selected-agent default behavior. | `flutter test test/widget_test.dart` or normal AVD smoke. |
| Structured content reader | Accepted | AVD smoke drives `structured-content-reader`; widget tests cover Markdown body rendering through `flutter_markdown_plus`. | `flutter test test/widget_test.dart`. |
| Formula fallback | Accepted for emulator-only | Dedicated math renderer remains an open improvement, but every content item has a selectable Markdown body, copy action, and raw-source expansion for formulas or unsupported markup. | `flutter test test/widget_test.dart`; inspect `raw-source-*` UI. |
| Readable terminal history | Accepted | AVD smoke and widget tests drag `readable-terminal-history-scroll` until retained scrollback item `Checkpoint 09` is visible. Source/app gateway route evidence is in commits `d8c8cc17`, `26607d8`, and `be5f345`. | Normal AVD smoke command above. |
| Explicit raw terminal fallback | Accepted | Agent taps select agents; Open Terminal opens terminal view. Normal AVD smoke opens selected-agent gateway terminal. | Normal AVD smoke command above. |
| Terminal input/paste/resize/reconnect | Accepted | Normal AVD smoke exercises live terminal send, paste, size sync, and reconnect; app commit `5b72330` added the controls. | Normal AVD smoke command above. |
| Terminal token renewal | Accepted by local harness | App commit `6d2fab7` added `app/tool/terminal_token_renewal_smoke.dart`; latest plan evidence records renewal with resume cursor and post-renewal input/paste. | `cd app && dart run tool/terminal_token_renewal_smoke.dart`. |
| Route diagnostics for loopback/ADB | Accepted | Normal AVD smoke checks route diagnostics to `Route ready`; app route diagnostics also cover device gateway URL consistency. | Normal AVD smoke command above. |
| Relay route health diagnostics | Accepted by fake/local tests | Source `1112559d` and app `c10e4f1` cover unknown host, disconnected host, relay unreachable, stale device, and fingerprint mismatch without public relay. | Source relay tests and `flutter test test/gateway_route_diagnostics_test.dart`. |
| Simulated notifications/deep links | Accepted by widget/model tests | App `14e68a7` synthesizes notifications from ProjectView/Comms and widget tests deep-link to agent content and Comms. Platform push/local OS notifications remain outside emulator-only acceptance. | `flutter test test/project_view_fixture_test.dart test/widget_test.dart`. |
| Safe lifecycle controls | Accepted | Normal AVD smoke covers wake/open/close; stop smoke covers confirmed stop in a throwaway runtime; source/app commits `e1ace0b0`, `b8d9507`, and `f08754f` enforce CCB authority and no raw tmux kill. | Normal and stop AVD smoke commands above. |
| Source/app tests and debug build | Accepted | Latest relay-health batch: source mobile gateway tests `175 passed`; app `flutter test` `76 passed`; `flutter build apk --debug` succeeded. | Focused tests for changed package, then full app test/build before completion claim. |
| Plan-tree evidence and commits | Accepted | Source `1112559d`, app `c10e4f1`, plan `6767c45`, and this checklist are recorded in plan tree. | `git log --oneline`; inspect `history/evidence-index.md`. |
| Public remote access | Deferred by goal | Production relay, public DNS, public IP, Cloudflare, and physical devices are explicitly outside emulator-only completion. | Keep route-provider fake/local tests current. |

## Completion Audit Position

Final audit result on 2026-06-21: accepted.

Every completion gate in [goal-emulator-only.md](../goal-emulator-only.md) has
current local evidence in this checklist or an explicit goal-level deferral.
The accepted deferrals are public remote access, production relay deployment,
Cloudflare, public DNS/IP, physical devices, app stores, and high-quality
dedicated math rendering beyond the current Markdown/raw-source fallback.

No missing or contradictory emulator-only proof remains for this goal.
