# Pane Live Output And Smooth Conversation

Date: 2026-06-29
Status: Package A worktree progress with real-AVD timing, `/status`,
scroll-away, idle no-blind-polling, recovery timing, long-output shape,
200-line high-volume transcript reconciliation, and status-only terminal-stream
evidence; 1000-line/repeated high-volume packet still pending
Read with:
[agent-native-conversation-and-input-correction.md](agent-native-conversation-and-input-correction.md),
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md),
and
[local-avd-real-project-test-runbook.md](local-avd-real-project-test-runbook.md).

## Purpose

Make the selected-agent chat feel like a smooth mobile conversation while
remaining faithful to the real CCB pane.

The current product contract is correct: phone input is pane-backed, not an
ask job. The remaining smoothness problem is on the read side. A provider
native transcript is useful for final readable history, but it can lag or omit
interactive terminal output such as `/status`, progress text, and TUI-style
updates. Terminal history refresh can recover that text, but using it as a
periodic replacement source can cause visible jumping, stale blocks, and
multiple small "agent reply" cards for one long execution.

This topic defines the next cohesive package: use the selected pane's terminal
output stream as the low-latency activity/status source, then render readable
conversation content from the provider/native transcript and retained terminal
history when the turn settles.

## Product Contract

The selected-agent chat should behave like a readable wrapper over the same
desktop/server pane:

- Sending from the phone is equivalent to typing into the selected agent pane.
- While the agent is working, the phone shows `Working` or `Streaming` status
  near the composer quickly enough that the user knows the pane is alive.
- One long provider execution appears as one final readable turn after native
  transcript reconciliation, not as a sequence of terminal-output reply cards.
- Final readable history can come from the provider-native transcript when it
  is mapped to the selected pane/session.
- Terminal output remains the authority for in-progress activity status, but it
  is not rendered as a default chat bubble. Command results and `/status`-style
  provider UI output should appear through provider/native transcript or
  explicit manual refresh/backfill surfaces.
- Internal provenance labels such as `tmux output / live`,
  `completion_snapshot`, provider cache names, job ids, route names, and
  request ids are not shown in the default conversation surface.

## Source Priority

Use three sources with different roles instead of forcing one source to do
everything.

| Source | Role | UI Treatment |
| :--- | :--- | :--- |
| Terminal output stream | Realtime in-progress pane activity | Composer-adjacent `Working`/`Streaming` status only |
| Provider-native transcript | Final readable user/assistant history | Canonical conversation bubbles after reconciliation |
| Terminal history endpoint | Manual refresh/backfill/fallback | Best-effort retained pane output, not a blind polling loop |

The stream and history sources must be scoped to the same CCB-validated
project, namespace epoch, window, agent, and pane target as the composer.

Reference posture: Paseo remains useful as a daemon/client and streamed-agent
workflow reference, but CCB should not copy a separate mobile agent protocol for
ordinary chat. The CCB-specific path is selected-pane terminal frames for
activity state plus CCB/provider transcript reconciliation for readable
history.

## 2026-06-29 Latency Baseline

Manual AVD review reported that phone-to-visible-output can feel more than
one second behind desktop pane activity. Focused inspection and lightweight
measurements show that the first bottleneck is not the loopback gateway link:

| Probe | Observed |
| :--- | :--- |
| Host to gateway `/v1/health` | ~3 ms |
| Host to gateway `/v1/projects` | ~85 ms for the current multi-project registry |
| Android Emulator to gateway `/v1/health` through `adb reverse` | ~13 ms |
| Android Emulator to gateway `/v1/projects` through `adb reverse` | ~16 ms |
| Gateway terminal websocket read loop | `session.read(0.1)`, so ~100 ms polling granularity |

The visible one-second step comes from the app-side post-send conversation
refresh model:

- the user bubble is local and appears immediately;
- terminal websocket output can arrive quickly when the selected pane emits
  bytes;
- final provider-native transcript still arrives through HTTP
  `/conversation` refresh;
- the pre-optimization active-send refresh scheduler started at `1s`, then
  backed off to `2s`, `5s`, `10s`, `20s`, `40s`, and `60s`;
- provider-native transcript can also lag until Codex/Claude writes the
  relevant rollout/session record.

Optimization should therefore first reduce active-send follow-up latency and
instrument the end-to-end path before changing gateway protocols.

## 2026-06-29 Worktree Evidence

Current worktree progress implements the first optimization slice:

- active-send follow-up delays now start at `250 ms`, then back off through
  `750 ms`, `1500 ms`, `3 s`, `5 s`, `10 s`, `20 s`, `40 s`, `80 s`,
  `160 s`, `320 s`, `640 s`, and `900 s`;
- pane-backed sends mark the selected agent as `Working` in the same state
  update that accepts the optimistic local user bubble;
- `Working` now has status-label priority over `Refreshing` while a
  pane-backed send is awaiting the selected agent response;
- if the pane path fails before scheduling a follow-up refresh, `Working` is
  cleared so the UI does not get stuck;
- terminal lifecycle notices remain out of normal conversation bubbles.
- the strict AVD harness can run repeated native-pane timing cases with
  `--native-pane-repeat N` and emits p50/p95 timing summaries, first-feedback
  kind counts, and missing-Working counts.

Focused verification:

- Flutter focused batch: `81` tests passed across scheduler, pane event,
  pane controller, submit coordinator, composer widget, and timeline model
  tests.
- Python harness tests: `38` tests passed.
- `git diff --check`: passed.

After repeat-harness work, Python harness tests now pass `41/41`; the added
coverage proves multi-marker timing extraction, nearest-rank p50/p95 summary
generation, and native-pane repeat argument parsing.

Earlier single-run real-AVD evidence, now superseded by the repeat run below:

- Device: `emulator-5554`.
- App: current worktree debug APK
  `app/build/app/outputs/flutter-apk/app-debug.apk`,
  `sha256 4786d3e9717ba7200e17b681b0e7809e627d8af2a5752f8c746c2af9b86d09cc`.
- Source gateway: clean
  `/home/bfly/yunwei/ccb_source_mobile_agent_native` at `7e436f7e`.
- Gateway: server-wide real gateway at `127.0.0.1:19255` with `adb reverse`
  `tcp:19255 tcp:19255`.
- Project: disposable real
  `/home/bfly/yunwei/test_ccb2/.../test_ccb2_alpha`.
- Final passing timing JSON:
  `send_to_local_bubble_ms=227`,
  `send_to_working_ms=null`,
  `send_to_first_feedback_ms=1044`,
  `first_feedback_kind=expected_reply`,
  `send_to_expected_reply_ms=5247`.
- Source-side native evidence:
  `prompt_contains_ccb_req_id=false`,
  `prompt_contains_mobile_gateway=false`,
  `jobs_matches=[]`,
  `user_match_count=1`,
  `reply_match_count=1`.

This evidence proved the native-pane send/reply path and timing
instrumentation, but did not close the full optimization goal. It also exposed
that the real AVD path did not capture a visible `Working` frame before final
feedback; the repeat run below closes that specific status-visibility gap.
Remaining strict gates at this checkpoint: `/status`, long-running output,
scroll-away behavior, idle 180-second zero request count, gateway recovery,
logcat/device memory/CPU/gfx/wakelock summaries, and screenshot/UI dump
evidence.

Repeat real-AVD timing evidence now exists for the same path:
[history/local-avd-native-pane-repeat-timing-20260629.json](../history/local-avd-native-pane-repeat-timing-20260629.json).
That run used `--native-pane-repeat 2` against `emulator-5554`,
server-wide gateway `127.0.0.1:19302`, source head `7e436f7e`, and debug APK
`sha256 34915a1825c9024a7089044fbabbb32bf4dd831182893d5cd0e359848063af2c`.
It produced machine-readable p50/p95:

| Metric | p50 | p95 | Missing |
| :--- | ---: | ---: | ---: |
| Send tap -> local bubble | `133 ms` | `186 ms` | `0/2` |
| Send tap -> Working | `138 ms` | `188 ms` | `0/2` |
| Send tap -> first visible feedback | `138 ms` | `188 ms` | `0/2` |
| Send tap -> final expected reply | `3206 ms` | `3224 ms` | `0/2` |

The repeated run confirms the native pane contract, timing collection, and
real-path `Working` visibility. It does not close the broader streaming goal by
itself: long-running output, scroll-away behavior, idle request counts,
recovery, and device metrics still needed strict AVD evidence at that
checkpoint.

Provider-command visibility is now covered by
[history/local-avd-native-status-command-20260629.json](../history/local-avd-native-status-command-20260629.json).
That run sent `/status` into the real selected Codex pane on `emulator-5554`
through server-wide gateway `127.0.0.1:19303`; the selected-agent timeline
rendered non-local marker `Weekly limit:` in `562 ms`.

Scroll-away refresh behavior is now covered by
[history/local-avd-scroll-away-desktop-origin-20260629.json](../history/local-avd-scroll-away-desktop-origin-20260629.json).
That run seeded `56` native-history turns, moved the selected-agent timeline
away from newest content, verified a desktop-origin pane marker was not pulled
in during a `2 s` idle window, then used explicit refresh plus `New messages`
to render the marker without forced jump-to-bottom while away from latest.

Idle no-blind-polling behavior is now covered by
[history/local-avd-idle-request-20260629.json](../history/local-avd-idle-request-20260629.json).
That run opened `test_ccb2_alpha/mobile_probe` through server-wide gateway
`127.0.0.1:19306` on `emulator-5554` and held the selected-agent page idle for
`180 s`; the reset audit window observed `0` total requests, `0` conversation
requests, `0` terminal-history requests, and `0.0` conversation/history
requests per minute. Device sampling reported PSS delta `-582 KB`, wake locks
`size=0`, `mWakeLockSummary=0x0`, no FATAL/ANR/OOM marker, and no skipped-frame
storm.

Recovery timing is now covered by
[history/local-avd-reverse-recovery-timing-20260629.json](../history/local-avd-reverse-recovery-timing-20260629.json).
That run removed and restored `adb reverse` while exercising the server-wide
project list and an already-open selected-agent conversation through gateway
`127.0.0.1:19309`. Project-list retry recovered in `1234 ms`; opened
conversation retry recovered in `1099 ms`; the composer stayed present after
recovery; and the selected-agent surface showed no `CCB_REQ_ID`,
`mobile_gateway`, or `completion_snapshot` labels.

Long-output shape is now covered by
[history/local-avd-native-long-output-live-turn-20260629.json](../history/local-avd-native-long-output-live-turn-20260629.json).
That run sent a 40-line native Codex pane prompt through gateway
`127.0.0.1:19310`; the final marker appeared inside exactly one live
terminal-output conversation item, `Working` appeared in `155 ms`, and internal
labels were absent. This remains a shape smoke; it does not replace the future
long-duration/high-volume plus device-health gate.

Longer-output command evidence is now covered by
[history/local-avd-native-long-output-120-device-metrics-20260629.json](../history/local-avd-native-long-output-120-device-metrics-20260629.json).
That run sent a 120-line native Codex pane prompt through gateway
`127.0.0.1:19313` and collected device metrics from the ready-to-send marker.
It reported local bubble `273 ms`, `Working` `281 ms`, first feedback
`281 ms`, final marker `1056 ms`, one final expected-reply item, one live
terminal-output item, screenshot/UI dump artifact paths, no FATAL/ANR/OOM, and
no skipped-frame storm. This is still not enough to close the final gate:
`live_terminal_output_expected_item_count` was `0`, the device window had only
one valid memory sample, and global wake-lock warnings require longer-scenario
interpretation.

Strict live-marker command evidence is now covered by
[history/local-avd-native-long-output-strict-80-live-device-metrics-20260629.json](../history/local-avd-native-long-output-strict-80-live-device-metrics-20260629.json).
That run used a marker that was not present verbatim in the user prompt, then
required the marker inside the live `Terminal output` item before timing
evidence was emitted. It reported local bubble `259 ms`, `Working` `263 ms`,
first feedback `263 ms`, final marker `205237 ms`, one final expected-reply
item, one live terminal-output item containing the marker, `88` metric samples,
PSS delta `-1481 KB`, wake locks `size=0`, `mWakeLockSummary=0x0`, no
FATAL/ANR/OOM, no skipped-frame storm, and no warnings. This is the current
strongest long-output evidence, but it is still below the original `1000`-line
and repeated p50/p95 target.

High-volume transcript reconciliation is now covered by
[history/local-avd-native-high-volume-200-device-metrics-20260629.json](../history/local-avd-native-high-volume-200-device-metrics-20260629.json).
That run sent a 200-line native Codex pane prompt through gateway
`127.0.0.1:19318` after extending the active-send follow-up refresh schedule
through `80 s`, `160 s`, and `320 s`. The selected-agent model contained all
`200` prefixed lines, local bubble appeared in `162 ms`, `Working` in
`167 ms`, first feedback in `167 ms`, final transcript reconciliation in
`80313 ms`, and the UI model stayed compact with `3` non-local conversation
items against an `8` item cap. Device metrics had `35` samples, PSS delta
`11060 KB`, wake locks `size=0`, `mWakeLockSummary=0x0`, no FATAL/ANR/OOM
marker, no skipped-frame storm, and no warnings. This closes the intermediate
200-line reconciliation proof, but it is still below the original `1000`-line
and repeated high-volume p50/p95 target.

Status-only terminal-stream behavior is now covered by
[history/local-avd-status-only-transcript-200-20260629.json](../history/local-avd-status-only-transcript-200-20260629.json).
That run repeated the 200-line native Codex pane prompt through gateway
`127.0.0.1:19323` after changing `PaneChatEventKind.output` to update only
selected-agent activity state. The selected-agent model contained all `200`
prefixed lines, local bubble appeared in `238 ms`, `Working` in `244 ms`,
first feedback in `244 ms`, final transcript reconciliation in `80336 ms`, and
`live_terminal_output_item_count=0`. This is the current product-shape
evidence: tmux/terminal stream drives `Working`, while provider/native
transcript supplies the readable conversation items.

Release recovery device-health evidence is now covered by
[history/local-avd-release-reverse-recovery-current-20260629.json](../history/local-avd-release-reverse-recovery-current-20260629.json).
That run installed release APK
`app/build/app/outputs/flutter-apk/app-release.apk`, opened the real
server-wide disposable project `test_ccb2_alpha/mobile_probe` through gateway
`127.0.0.1:19316`, removed `adb reverse`, observed the selected-agent
conversation failure, restored `adb reverse`, and rendered
`Native reverse recovery restored 1782719941` after explicit refresh. Recovery
elapsed `14230.173 ms`; device metrics had `7` samples, PSS delta `-3448 KB`,
wake locks `size=0`, `mWakeLockSummary=0x0`, no FATAL/ANR/OOM marker, no
skipped-frame storm, and no warnings. This closes the local release
recovery-device-health proof for this goal, while physical Tailnet/VPN
recovery remains separate.

## Proposed Architecture

### 1. Live Pane Output Session

Use the existing gateway terminal transport and `TerminalSession.output` as the
active-turn stream. Do not add a separate ask route and do not depend on
provider session files for the first visible feedback.

App-side responsibilities:

- open or reuse the selected agent terminal session when the user sends,
  requests live follow, or opens a selected-agent workspace that is in an
  active response state;
- subscribe to terminal output frames for the selected agent only;
- close or pause the subscription on project switch, agent switch, app
  background, route dispose, explicit logout, or idle timeout;
- never keep a global stream or fixed timer alive while the user is idle.

Gateway/source responsibilities if changes are needed:

- keep terminal output frames scoped by validated terminal handle;
- preserve existing terminal token, project id, namespace epoch, and pane
  validation;
- avoid adding route-provider metadata into terminal frame schemas.

### 2. Live Turn Aggregator

Add a small app-side aggregator between `PaneChatController.events` and
`AgentChatController` local messages.

It should:

- strip ANSI/control sequences and normalize carriage-return updates;
- suppress pane echo for the just-sent user input;
- merge terminal chunks into a stable live turn id per agent turn;
- coalesce output with a short flush interval, for example 100-250 ms, so the
  UI is responsive but not rebuilt for every byte frame;
- cap retained live text by both lines and characters, with an expand affordance
  or "open terminal" action for full raw output;
- mark state as `working`, `streaming`, `stalled`, `complete`, or `error`;
- preserve scroll position when the user is not pinned near the newest turn;
- expose a "New output" affordance instead of jumping when the user has
  scrolled away.

The current `appendOrMergeLiveTerminalOutput` path is the right starting point,
but it needs a clearer turn lifecycle and stable in-place updates rather than
creating a fresh item id for every live chunk.

### 3. Transcript Reconciliation

After an active send, refresh the selected-agent conversation with bounded
backoff. When provider-native transcript catches up:

- match the optimistic user bubble and live assistant turn to the native
  transcript by selected agent, time window, normalized text, and source
  cursor when available;
- replace or mark the live turn complete without duplicating the same reply;
- keep terminal-only output visible when there is no equivalent native
  transcript record, such as `/status` output or a shell/tool progress line;
- avoid letting stale jobs/completion snapshots replace newer pane-derived
  output;
- keep Comms and system activity compact and inline rather than as fake agent
  replies.

### 4. Refresh Model

Do not reintroduce a blind 3-second terminal-history polling loop.

Allowed refresh triggers:

- project open and selected-agent open;
- explicit refresh button;
- pull-to-refresh or overscroll boundary;
- app foreground/resume;
- active send bounded follow-up until reply/idle timeout;
- manual "load older" pagination when the user scrolls near the oldest loaded
  item.

The active-send refresh loop must stop when:

- the live stream has gone idle and a transcript/history refresh confirms no
  newer output;
- a provider-native final reply reconciles the live turn;
- the user switches project/agent;
- a timeout budget is reached.

## Interaction Design

### Conversation Timeline

- Show the user's sent turn immediately.
- Show a compact `Working` status as soon as the terminal send reaches the
  selected pane or an active stream is opened.
- Update one assistant live bubble in place as output arrives.
- If the output is long, show the newest useful tail plus an expand/open
  terminal affordance; do not keep appending separate cards.
- Hide source/provenance labels in normal mode. Diagnostics can expose them
  behind a detail route or debug affordance.
- When not pinned at bottom, keep the scroll stable and show a new-output
  affordance.

### `/status` And Provider UI Commands

`/status` is not a CCB ask and may not appear in the provider-native transcript
as a normal assistant message. It should still be visible because it is terminal
output from the selected pane. This is a primary acceptance case for the live
stream path.

### Attachment And Artifact Continuity

File upload/download remains in the same conversation surface, but live stream
work should not change the file contract. Backend-generated artifact links are
rendered from authenticated gateway artifact ids when they appear in the
native transcript or supplemental content. Live terminal output may mention a
file path, but raw host paths must not become phone-download URLs.

## Package Plan

### Package A: Live Turn Aggregator

Likely app files:

- `app/lib/features/agent_chat/live_terminal_output.dart`
- `app/lib/features/agent_chat/pane_chat_event_messages.dart`
- `app/lib/features/agent_chat/agent_chat_controller.dart`
- `app/lib/features/agent_chat/selected_agent_workspace.dart`
- focused tests under `app/test/`

Scope:

- stable live turn ids;
- in-place merge/coalesce;
- state labels for working/streaming/stalled/complete;
- echo suppression and ANSI/carriage-return cleanup;
- no gateway/source contract changes.

Acceptance:

- a stream of many terminal chunks produces one assistant live item;
- live item updates in place and preserves user scroll when not near bottom;
- `/status` output is visible even if the native transcript does not change;
- idle app keeps zero conversation/history polling requests.

Current app-side status:

- pane stream output maps to terminal-output conversation items;
- consecutive live terminal chunks merge into one visible item;
- normal provenance labels are hidden in the default conversation surface;
- the selected-agent page renders `Working` after send and clears it after
  first pane output or terminal notice.

### Package B: Active Send Follow Loop

Likely app files:

- `conversation_refresh_scheduler.dart`
- `selected_agent_workspace.dart`
- `agent_conversation_refresh_coordinator.dart`
- `agent_terminal_history_refresh_coordinator.dart`

Scope:

- lower-latency bounded active-send refresh/backoff;
- stop conditions and cancellation on switch/dispose;
- visible `Working` state while waiting;
- manual refresh still available.

Acceptance:

- after phone send, the app shows working state immediately;
- first terminal output or transcript-visible update renders within the
  latency budget below;
- active follow stops after completion/idle timeout;
- no fixed 3-second background loop returns.

Current app-side status:

- explicit refresh and user scroll refresh are available;
- active send schedules bounded follow-up refresh instead of a blind fixed
  interval loop;
- real AVD smoke confirmed the visible state does not stay stuck after a
  terminal notice.

Current worktree slice:

- replace the first active-send refresh delays with a faster bounded sequence,
  now `250 ms`, `750 ms`, `1500 ms`, `3 s`, `5 s`, `10 s`, `20 s`, and
  `40 s`;
- keep idle selected-agent pages at zero blind conversation/history requests;
- keep manual refresh, overscroll refresh, and load-older behavior unchanged;
- add instrumentation hooks or test-only timing capture for:
  send accepted, pane send complete, first terminal output event, first
  conversation refresh completion, first changed timeline render, and follow
  loop stop;
- do not turn this into a global polling loop.

### Package C: Transcript/History Reconciliation

Likely app and source files:

- app timeline/model merge helpers;
- source conversation route only if native transcript metadata needs a better
  cursor or source marker;
- focused source tests if the gateway response shape changes.

Scope:

- dedupe live output versus provider-native final reply;
- keep terminal-only command output when no transcript equivalent exists;
- prevent stale job/completion records from becoming newest chat;
- keep older-history pagination stable.

Acceptance:

- one long provider response becomes one final readable reply, not duplicate
  live plus final cards;
- `/status` remains visible as terminal output;
- switching away and back does not resurrect stale live items;
- desktop-origin text appears after explicit refresh or active stream without
  overwriting newer phone turns.

### Package D: Real AVD Smoothness Gate

Use the server-wide real gateway and disposable projects under
`/home/bfly/yunwei/test_ccb2`. Do not use fake/demo for acceptance.

Required cases:

1. Open real project list, select a disposable test project and agent.
2. Send `hi` and verify pane input, live working state, and real reply.
3. Send `/status` and verify credits/status output appears from the pane.
4. Trigger a long provider response and verify it stays one live/final turn.
5. Type from desktop pane and verify phone refresh/stream displays it.
6. Scroll away, trigger output, and verify no jump plus new-output affordance.
7. Keep the page idle for 3 minutes and verify no blind polling requests.
8. Record p50/p95 timings and device metrics.

Current 2026-06-29 result:

- Case 1 partially passed: the app opened the real server-wide gateway and
  selected `/home/bfly/yunwei/test_ccb2`.
- Case 2 has repeat real-AVD evidence: phone input reached the pane-backed path
  without adding a new `CCB_REQ_ID`, `Working` was captured `2/2`, and the
  expected native reply rendered in the selected-agent timeline. Broader
  multi-action and long-output timing remain open.
- Case 3 now has dedicated real-AVD evidence: `/status` was sent as pane input
  and the selected-agent timeline rendered marker `Weekly limit:` in `562 ms`
  through the server-wide gateway. See
  [../history/local-avd-native-status-command-20260629.json](../history/local-avd-native-status-command-20260629.json).
- Case 6 now has dedicated real-AVD evidence for explicit-refresh behavior:
  after seeding `56` native-history turns, the test dragged away from the end,
  injected a desktop-origin pane marker, verified the idle window did not pick
  it up through blind polling, then explicit refresh surfaced `New messages`
  and tapping it rendered the marker. See
  [../history/local-avd-scroll-away-desktop-origin-20260629.json](../history/local-avd-scroll-away-desktop-origin-20260629.json).
- Case 7 now has dedicated real-AVD evidence: the selected-agent page stayed
  open and idle for `180 s` on `emulator-5554`, and the reset request-count
  window observed `0` conversation requests, `0` terminal-history requests,
  and `0.0` conversation/history requests per minute. Device sampling also
  reported no FATAL/ANR/OOM, no skipped-frame storm, and no wakelock. See
  [../history/local-avd-idle-request-20260629.json](../history/local-avd-idle-request-20260629.json).
- Recovery timing now has dedicated real-AVD evidence: after `adb reverse`
  removal/restoration, project-list retry recovered in `1234 ms` and
  selected-agent conversation retry recovered in `1099 ms` without reopening
  the app or showing internal labels. See
  [../history/local-avd-reverse-recovery-timing-20260629.json](../history/local-avd-reverse-recovery-timing-20260629.json).
- Long-output shape now has dedicated real-AVD evidence: a 40-line native
  Codex pane prompt rendered its final marker in exactly one live
  terminal-output item. See
  [../history/local-avd-native-long-output-live-turn-20260629.json](../history/local-avd-native-long-output-live-turn-20260629.json).
- Latency baseline shows emulator-to-gateway request latency is tens of
  milliseconds, while app-side active-send refresh has a one-second first
  scheduled refresh. The next optimization package should target this refresh
  schedule and add timing evidence before any source protocol expansion.
- Current worktree app-side follow-loop update lowers the default first
  explicit scheduled refresh to `250 ms` and locks that with
  `conversation_refresh_scheduler_test.dart`; it also proves scheduler
  construction does not arm timers before an explicit schedule call. Focused
  verification run:
  `flutter test test/conversation_refresh_scheduler_test.dart
  test/agent_chat_controller_test.dart test/pane_chat_event_messages_test.dart
  test/agent_pane_event_coordinator_test.dart test/pane_chat_controller_test.dart
  test/agent_pane_message_submitter_test.dart
  test/agent_message_submit_coordinator_test.dart` and
  `flutter test test/agent_chat_composer_widget_test.dart
  test/selected_agent_workspace_model_test.dart
  test/agent_chat_timeline_items_test.dart`.

Evidence:
[../history/local-avd-pane-live-output-smoke-20260628.md](../history/local-avd-pane-live-output-smoke-20260628.md),
[../history/local-avd-native-pane-repeat-timing-20260629.json](../history/local-avd-native-pane-repeat-timing-20260629.json),
[../history/local-avd-native-status-command-20260629.json](../history/local-avd-native-status-command-20260629.json),
[../history/local-avd-scroll-away-desktop-origin-20260629.json](../history/local-avd-scroll-away-desktop-origin-20260629.json),
[../history/local-avd-idle-request-20260629.json](../history/local-avd-idle-request-20260629.json),
[../history/local-avd-reverse-recovery-timing-20260629.json](../history/local-avd-reverse-recovery-timing-20260629.json),
and
[../history/local-avd-native-long-output-live-turn-20260629.json](../history/local-avd-native-long-output-live-turn-20260629.json).

## Metrics And Budgets

| Metric | Target |
| :--- | :--- |
| Send tap to local user bubble | <= 100 ms |
| Send tap to `Working` state | <= 150 ms |
| First terminal output frame to visible live update | <= 250 ms app-side |
| First active-send refresh attempt | <= 300 ms |
| First conversation-changed render after transcript is available | <= 500 ms local AVD |
| Send tap to first visible output on local AVD | <= 500 ms when provider writes promptly |
| Send tap to first visible output over Tailnet | <= 1000 ms when provider writes promptly |
| Live UI update frequency | <= 10 updates/sec after coalescing |
| Idle selected-agent page request count | 0 conversation/history requests over 180 seconds |
| Long output stability | 1000 lines do not create 1000 chat cards or visible jank |
| Memory trend | No unbounded live buffer growth; cap per active live turn |

## Verification Commands

App:

```bash
cd app
flutter test test/pane_chat_controller_test.dart
flutter test test/agent_chat_composer_widget_test.dart
flutter test test/conversation_refresh_scheduler_test.dart
flutter test test/selected_agent_workspace_model_test.dart
flutter test test/project_home_server_projects_widget_test.dart
flutter test
git diff --check
```

Source, only if gateway conversation or terminal frame contracts change:

```bash
PYTHONPATH=lib python -m pytest test/test_mobile_gateway_service.py
python -m py_compile lib/mobile_gateway/service.py
git diff --check
```

Real AVD:

- run against the server-wide gateway, not fake/demo;
- use disposable projects under `/home/bfly/yunwei/test_ccb2`;
- capture screenshot, UI dump, logcat, gateway log tail, request count, and
  timings for each case.

## Risks

- Terminal output is not structured. The live aggregator must avoid pretending
  terminal text is canonical final transcript.
- Provider TUIs can repaint lines with carriage returns or alternate-screen
  behavior. The MVP should normalize common output and leave raw terminal as
  the fallback for full fidelity.
- Direct pane input can execute in whatever foreground mode the agent pane is
  currently in. The UI must keep the existing `Check pane` honesty when send
  state is ambiguous.
- Streaming every frame into Flutter can cause jank or battery drain. Coalesced
  flushes, caps, and idle cancellation are mandatory.
- Reconciliation can hide useful terminal-only command output if it is too
  aggressive. `/status` must remain a regression gate.

## Open Questions

1. Should the live turn keep only a tail in the main timeline and offer a
   detail sheet for the full live buffer, or should it expand inline?
2. What exact idle timeout should mark a live turn `stalled` versus
   `complete` when no provider-native final reply appears?
3. Should terminal output streaming start only after phone sends, or also when
   the selected desktop pane is already visibly active on project open?
4. Is a source-side pane-output event stream needed later, or is the existing
   terminal WebSocket sufficient for the first smooth conversation package?
5. Should the faster active-send refresh sequence be fixed, adaptive based on
   first terminal bytes, or provider-specific once Codex/Claude working-state
   detection is reliable?

## Current Blocker

The app-side smoothness package is test-backed and installed into the current
AVD. Active-send `Working` visibility and `/status` provider-command visibility
now have strict real-AVD evidence, and the `180 s` idle no-blind-polling gate
also has strict real-AVD evidence. Recovery timing is now measured, but this is
not yet a completed real-provider conversation pass. A 40-line long-output
shape smoke now proves the marker can stay in one live terminal-output item.
Remaining blockers are the broader evidence packet: one long-duration or
high-volume provider execution must stay one live/final turn, and device health
metrics for long-output/recovery scenarios must show no FATAL/ANR/OOM or
sustained jank/power regression.
