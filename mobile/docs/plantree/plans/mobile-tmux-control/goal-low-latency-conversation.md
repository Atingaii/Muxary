# CCB Mobile Low-Latency Conversation Goal

Date: 2026-06-29

## Purpose

Reusable goal prompt for optimizing CCB Mobile selected-agent conversation
latency and smoothness after pane-backed send and provider-native transcript
sync are available at smoke level.

The product goal is not to make CCB Mobile a separate agent client. The phone
remains a readable wrapper over the selected desktop/server CCB pane: it sends
ordinary input to the selected pane, shows low-latency in-progress feedback,
then reconciles into provider-native readable conversation history.

This goal is implementation-driving and requires strict local Android Emulator
validation. Fake/demo evidence cannot close this goal.

## Invocation

Use this prompt when assigning the next cohesive optimization run:

```text
读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-low-latency-conversation.md`
作为当前长期 goal。

目标：优化 CCB Mobile selected-agent 对话延迟和流畅度。手机发送后必须立即显示
本地 user turn 和 Working 状态；真实 pane 有输出时尽快显示；provider-native
transcript 到达后合并为最终可读历史。不能恢复 3 秒 blind polling，不能把
terminal lifecycle 噪声渲染成聊天气泡，不能走 CCB ask/message 路径，不能出现
CCB_REQ_ID、mobile_gateway、completion_snapshot、tmux source label 等普通用户
不可见来源标记。

启动前必须 resume plan tree：读取
`docs/plantree/README.md`、
`docs/plantree/plans/mobile-tmux-control/README.md`、
`implementation-status.md`、`roadmap.md`、
`decisions/015-pane-backed-chat-input.md`、
`decisions/016-pane-composer-send-primitive.md`、
`topics/agent-native-conversation-and-input-correction.md`、
`topics/pane-live-output-and-smooth-conversation.md`、
`topics/local-avd-real-project-test-runbook.md`，并检查 mobile/source 两个
worktree 的 dirty 状态。

当前已知延迟基线：
- Android Emulator 通过 adb reverse 到 gateway 的 `/v1/health` 约 13ms；
- `/v1/projects` 约 16ms；
- gateway terminal websocket read loop 约 100ms 粒度；
- 当前 app active-send refresh scheduler 首次刷新是 1s，这是主要体感延迟台阶。

实现边界：
- app 侧优先落地低延迟 active-send follow-loop：发送后首个 refresh attempt
  目标 <= 300ms，后续 bounded backoff，例如 250ms、750ms、1500ms、3s、5s、
  10s、20s、40s；
- 只在 active send / explicit refresh / overscroll / foreground resume /
  load older 等用户或状态驱动场景刷新；
- idle selected-agent 页面必须继续保持 0 conversation/history blind polling；
- 添加 timing instrumentation 或测试 harness 证据：send accepted、pane send
  complete、first terminal activity event、first conversation refresh complete、
  first timeline changed/rendered、follow loop stopped；
- live terminal output 只作为低延迟 activity/status source，不作为默认聊天
  气泡内容；最终 readable history 仍以 provider-native transcript 为主；
- 一次长执行应更新一个状态条和一个最终 readable turn，不产生许多零散
  Agent reply 或 Terminal output 卡片；
- terminal stream closed、server exited unexpectedly、transport lifecycle
  错误等不得作为普通聊天气泡出现；
- 如果 source 侧需要改变，只能围绕 mobile gateway selected-pane stream /
  conversation metadata / timing evidence 做最小改动，保持 route-provider 不进入
  project id、terminal id、ProjectView、terminal frame schema。

严格虚拟机验收：
- 必须使用本机 Android Emulator `emulator-5554` 或 `ccb_mobile_api35`；
- 必须先安装当前 worktree 构建出的 debug/profile APK，并记录 APK 路径、
  app commit、source commit、package version、安装命令和设备 id；
- 必须连接 server-wide real mobile gateway，不允许用 fake/demo 作为完成证据；
- 必须使用 `/home/bfly/yunwei/test_ccb2` 下 disposable real CCB projects；
- 不允许把探索测试发送到 `/home/bfly/yunwei/ccb_source/mobile` 当前工作项目；
- 必须证明首页列出真实 mounted/reachable CCB projects；
- 必须打开 test project 的至少两个 agents；
- 必须执行普通文本、`/status`、长执行输出、desktop-origin pane 输入、滚动离底、
  手动 refresh、idle 180s、gateway/reverse recovery；
- 必须记录 screenshot、UI dump、logcat、gateway log tail、request-count、
  timing JSON、device mem/cpu/gfx/wakelock 摘要；
- 必须记录 gateway 启动命令、`adb reverse` 状态、`/v1/health`、
  `/v1/projects`、被打开 project/agent 的 API 响应摘要；
- 必须记录每个测试动作的开始/结束时间戳，不能只用人工截图判断通过；
- 必须给出 p50/p95：send tap -> local bubble、send tap -> Working、
  send tap -> first visible output、first terminal byte -> rendered、
  transcript available -> rendered、refresh click -> visible change；
- 必须证明 idle 180s 期间 conversation/history request count 为 0；
- 必须证明无 FATAL/ANR/OOM、无明显 skipped-frame storm、无持续 wakelock。

验收指标：
- Send tap to local user bubble <= 100ms；
- Send tap to Working <= 150ms；
- First active-send refresh attempt <= 300ms；
- First terminal output frame to visible live update <= 250ms app-side；
- Transcript available 后 first conversation-changed render <= 500ms local AVD；
- Provider promptly writes 时 send tap to first visible output <= 500ms local AVD；
- Tailnet 物理路线可后续验证，不能替代本 goal 的本地 AVD gate；
- 一次 1000 行长输出不会产生 1000 个聊天卡片，不会强制跳到底部；
- 普通聊天 UI 不显示内部 source/provenance label。

工作方式：
- 不要把任务切成过碎 micro-helper；按 coherent packages 落地：
  1. active-send follow-loop + timing instrumentation；
  2. live turn aggregator/noise filtering/coalescing；
  3. transcript/live reconciliation；
  4. strict real-AVD smoke harness/evidence audit。
- 每包必须有文件范围、测试、真实 AVD 证据、风险和 reviewer gates。
- mobile repo 和 ccb_source repo 分开提交、分开验证。
- 不提交 `.ccb/agents`、`.ccb/ccbd`、secrets、tokens、logs、SDK 本地配置、
  emulator runtime state 或未要求的 APK/dist artifacts。

不要把 goal 标记 complete，直到：
- focused Flutter tests 和 full relevant regression 通过；
- 严格 real-AVD evidence packet 通过；
- 普通手机发送不走 ask/message，不产生 CCB_REQ_ID；
- `/status` 或同类 provider UI command 能被手机看到；
- 长执行稳定为一个 live/final turn；
- idle 页面没有 blind polling；
- plan-tree history/evidence 更新完成。
```

Short objective:

```text
降低 CCB Mobile selected-agent 对话延迟：发送后快速显示 Working 和真实 pane
输出，用 bounded active-send follow-loop 与 live turn 合并替代 1s 台阶和噪声卡片，
并用严格本地 Android Emulator + server-wide real CCB projects 证明性能、稳定性、
无 ask/CCB_REQ_ID、无 blind polling。
```

## Current Progress

Status on 2026-06-29: Package A is implemented at native-pane repeat-smoke
level, including real-path `Working` visibility, but the full strict evidence
packet is not complete.

Implemented in the current worktree:

- active-send follow-up scheduler begins at `250 ms` and now keeps a bounded
  long-tail through `80 s`, `160 s`, `320 s`, `640 s`, and `900 s` for long
  provider executions;
- selected-agent `Working` state appears immediately when a pane-backed send
  accepts the optimistic local user bubble;
- `Working` clears if pane send does not schedule a follow-up refresh;
- terminal lifecycle notices do not render as ordinary conversation bubbles;
- native-pane integration smoke emits `CCB_MOBILE_NATIVE_TIMING_JSON`.
- the server-wide AVD harness accepts `--native-pane-repeat N` and summarizes
  repeated native-pane timings into p50/p95 fields plus Working capture count.
- selected-agent status now prioritizes `Working` over `Refreshing` when a
  pane-backed send is awaiting an agent response while a conversation refresh is
  also in progress.

Current evidence:

- Focused Flutter batch: `81` tests passed.
- Python smoke harness unit tests: `38` tests passed.
- Earlier single-run AVD smoke on `emulator-5554` against disposable
  `test_ccb2_alpha/mobile_probe` through server-wide gateway
  `127.0.0.1:19255`: passed, but was superseded by the repeat evidence below.
- Timing: local bubble `227 ms`, `Working` not captured on the final real
  run, first visible feedback `1044 ms` as `expected_reply`, expected reply
  `5247 ms`.
- Source-side native evidence: no `CCB_REQ_ID`, no `mobile_gateway`, no jobs
  matches, one native user match, and one native reply match.
- Harness unit evidence: Python smoke helper tests cover multi-marker timing
  extraction and native timing p50/p95 summary generation.
- Repeat real-AVD timing evidence:
  [history/local-avd-native-pane-repeat-timing-20260629.json](history/local-avd-native-pane-repeat-timing-20260629.json)
  ran two native-pane sends through `emulator-5554` and server-wide gateway
  `127.0.0.1:19302`: local bubble p50 `133 ms` / p95 `186 ms`, `Working`
  p50 `138 ms` / p95 `188 ms`, first visible feedback p50 `138 ms` /
  p95 `188 ms`, final expected reply p50 `3206 ms` / p95 `3224 ms`,
  `Working` captured `2/2`.
- Provider-command real-AVD evidence:
  [history/local-avd-native-status-command-20260629.json](history/local-avd-native-status-command-20260629.json)
  sent `/status` through `emulator-5554` and server-wide gateway
  `127.0.0.1:19303` into disposable `test_ccb2_alpha/mobile_probe`; the
  selected-agent timeline showed non-local marker `Weekly limit:` in `562 ms`.
- Scroll-away real-AVD evidence:
  [history/local-avd-scroll-away-desktop-origin-20260629.json](history/local-avd-scroll-away-desktop-origin-20260629.json)
  opened disposable `test_ccb2_alpha/mobile_probe`, seeded `56` native-history
  turns, dragged the selected-agent timeline away from the end, waited during a
  `2 s` idle window without seeing the desktop marker, then explicit refresh
  surfaced `New messages`; tapping it returned to latest and rendered the
  desktop-origin pane marker.
- Idle no-blind-polling real-AVD evidence:
  [history/local-avd-idle-request-20260629.json](history/local-avd-idle-request-20260629.json)
  opened disposable `test_ccb2_alpha/mobile_probe` on `emulator-5554` through
  server-wide gateway `127.0.0.1:19306`, then held the selected-agent page
  idle for `180 s`. The reset audit window observed `0` total requests,
  `0` conversation requests, `0` terminal-history requests, and `0`
  conversation/history requests per minute. Device sampling also reported
  `7` memory samples, PSS delta `-582 KB`, wake locks `size=0`,
  `mWakeLockSummary=0x0`, no FATAL/ANR/OOM marker, and no skipped-frame storm.
- Recovery timing real-AVD evidence:
  [history/local-avd-reverse-recovery-timing-20260629.json](history/local-avd-reverse-recovery-timing-20260629.json)
  removed and restored `adb reverse` while exercising both the server-wide
  project list and an already-open selected-agent conversation through gateway
  `127.0.0.1:19309`; project-list retry recovered in `1234 ms`, opened
  conversation retry recovered in `1099 ms`, and the selected-agent composer
  remained present with no `CCB_REQ_ID`, `mobile_gateway`, or
  `completion_snapshot` labels.
- Long-output shape real-AVD evidence:
  [history/local-avd-native-long-output-live-turn-20260629.json](history/local-avd-native-long-output-live-turn-20260629.json)
  sent a 40-line native Codex pane prompt through gateway `127.0.0.1:19310`.
  The final marker rendered in exactly one live terminal-output conversation
  item (`live_terminal_output_expected_item_count=1`), with `Working` visible
  at `155 ms` and no internal labels. This is a shape smoke, not the final
  long-duration/1000-line/device-health gate.
- Longer-output real-AVD evidence:
  [history/local-avd-native-long-output-120-device-metrics-20260629.json](history/local-avd-native-long-output-120-device-metrics-20260629.json)
  sent a 120-line native Codex pane prompt through gateway `127.0.0.1:19313`
  and collected device metrics from the ready-to-send marker. It reported
  local bubble `273 ms`, `Working` `281 ms`, first feedback `281 ms`, final
  marker `1056 ms`, one final expected-reply item, one live terminal-output
  item, screenshot/UI dump artifact paths, no FATAL/ANR/OOM, and no
  skipped-frame storm. This is stronger than the 40-line shape smoke but still
  not the final completion gate because the marker was not inside the live
  terminal-output item, the device window had only one valid memory sample,
  and global wake-lock warnings need longer-scenario interpretation.
- Strict live-marker long-output real-AVD evidence:
  [history/local-avd-native-long-output-strict-80-live-device-metrics-20260629.json](history/local-avd-native-long-output-strict-80-live-device-metrics-20260629.json)
  sent an 80-line native Codex pane prompt through gateway `127.0.0.1:19315`
  with an expected marker that was not present verbatim in the user prompt,
  then required that marker to appear inside the live `Terminal output` item.
  It reported local bubble `259 ms`, `Working` `263 ms`, first feedback
  `263 ms`, final marker `205237 ms`, one final expected-reply item, one live
  terminal-output item containing the marker, `88` device-metric samples, PSS
  delta `-1481 KB`, wake locks `size=0`, `mWakeLockSummary=0x0`, no
  FATAL/ANR/OOM, no skipped-frame storm, and no warnings. This closes a
  stronger live-turn/device-health proof than the earlier 40-line smoke, but
  still does not close the original `1000`-line target or repeated
  long-output p50/p95 gate.
- High-volume transcript reconciliation real-AVD evidence:
  [history/local-avd-native-high-volume-200-device-metrics-20260629.json](history/local-avd-native-high-volume-200-device-metrics-20260629.json)
  sent a 200-line native Codex pane prompt through gateway `127.0.0.1:19318`
  after extending active-send follow-up refreshes through `80 s`, `160 s`,
  and `320 s`. The selected-agent model contained all `200` prefixed lines,
  local bubble appeared in `162 ms`, `Working` in `167 ms`, first feedback in
  `167 ms`, final transcript reconciliation in `80313 ms`, and only `3`
  non-local conversation items against an `8` item cap. Device metrics
  collected `35` samples, PSS delta `11060 KB`, wake locks `size=0`,
  `mWakeLockSummary=0x0`, no FATAL/ANR/OOM marker, no skipped-frame storm,
  and no warnings. This closes the intermediate 200-line native transcript
  reconciliation gate, but not the original `1000`-line or repeated
  high-volume p50/p95 gate.
- Status-only terminal-stream real-AVD evidence:
  [history/local-avd-status-only-transcript-200-20260629.json](history/local-avd-status-only-transcript-200-20260629.json)
  repeated the 200-line prompt through gateway `127.0.0.1:19323` after making
  terminal stream output status-only. The transcript model contained all `200`
  prefixed lines, `live_terminal_output_item_count=0`, local bubble appeared
  in `238 ms`, `Working` in `244 ms`, first feedback in `244 ms`, and final
  transcript reconciliation in `80336 ms`. This is the current evidence for
  the product rule: tmux stream indicates activity; provider/native transcript
  renders readable chat.
- Release reverse-recovery real-AVD evidence:
  [history/local-avd-release-reverse-recovery-current-20260629.json](history/local-avd-release-reverse-recovery-current-20260629.json)
  installed release APK `app/build/app/outputs/flutter-apk/app-release.apk`,
  opened disposable real project `test_ccb2_alpha/mobile_probe` through
  gateway `127.0.0.1:19316`, removed `adb reverse`, observed
  `Connection refused`, restored `adb reverse`, and rendered
  `Native reverse recovery restored 1782719941` after explicit refresh.
  Recovery elapsed `14230.173 ms`; device metrics reported `7` memory samples,
  PSS delta `-3448 KB`, wake locks `size=0`, `mWakeLockSummary=0x0`, no
  FATAL/ANR/OOM marker, no skipped-frame storm, and no warnings. This closes
  the local release recovery device-health proof, while physical Tailnet/VPN
  recovery remains separate.

Still required before this goal can be closed:

- broader real-AVD p50/p95 timing across multiple actions;
- streaming output visibility beyond the immediate `Working` status;
- long-duration or high-volume output acceptance at the original `1000`-line
  target, beyond the 40-line shape smoke, 120-line command smoke, strict
  80-line live-marker smoke, and 200-line native transcript reconciliation
  smoke;
- broader repeated-run p50/p95 and device mem/cpu/gfx/wakelock/logcat
  stability packet for high-volume long-output scenarios;
- screenshot/UI dump/gateway log/request-count artifacts.

## Scope

### In Scope

- App-side active-send follow-loop schedule and cancellation.
- App-side timing instrumentation or test harness evidence capture.
- Live terminal output coalescing and stable live turn behavior.
- Transcript/live-output reconciliation when provider-native history catches up.
- Strict local Android Emulator evidence under real server-wide gateway.
- Focused source changes only when selected-pane stream or transcript metadata
  blocks the app-side goal.
- Plan-tree status, roadmap, and evidence updates.

### Out Of Scope

- Replacing provider-native transcript as the final readable history source.
- Reintroducing fixed background polling.
- Validating against fake/demo as completion evidence.
- Sending exploratory prompts into active user work projects such as
  `/home/bfly/yunwei/ccb_source/mobile`.
- Physical phone/Tailnet as a P0 gate for this local optimization goal.
- Public release, Play Store, GitHub release, or APK publication.
- Broad redesign of project list, pairing, Tailscale onboarding, file transfer,
  route diagnostics, or terminal route actions unless a regression is found.

## Required Packages

### Package A: Active-Send Follow Loop And Timing Evidence

Goal: remove the fixed one-second first refresh step while preserving zero idle
polling.

Likely files:

- `app/lib/features/agent_chat/conversation_refresh_scheduler.dart`
- `app/lib/features/agent_chat/selected_agent_workspace.dart`
- `app/lib/features/agent_chat/agent_message_submit_coordinator.dart`
- focused tests under `app/test/`
- optional test/evidence helper under `tools/`

P0 gates:

- First active-send refresh attempt is scheduled within `300ms`.
- Follow-up refresh is active only after send/key input or explicit user/state
  trigger.
- Idle selected-agent page still makes zero conversation/history requests over
  180 seconds.
- Switching project/agent, dispose, app background, or completion cancels the
  follow loop.
- Working indicator is visible while awaiting output and does not remain stuck.

### Package B: Live Turn Aggregator And Noise Hygiene

Goal: make low-latency terminal output readable without polluting chat.

Likely files:

- `app/lib/features/agent_chat/live_terminal_output.dart`
- `app/lib/features/agent_chat/pane_chat_event_messages.dart`
- `app/lib/features/agent_chat/agent_chat_controller.dart`
- `app/lib/features/agent_chat/conversation_bubble.dart`
- focused tests under `app/test/`

P0 gates:

- Terminal lifecycle notices do not render as conversation bubbles.
- `server exited unexpectedly` and equivalent lifecycle sentinels are filtered
  unless attached to meaningful user-visible output.
- Many terminal chunks update one stable live turn.
- Live output is coalesced to avoid excessive rebuilds.
- Source/provenance labels remain hidden in normal conversation UI.

### Package C: Provider Transcript Reconciliation

Goal: keep provider-native transcript as final history without duplicating live
output.

Likely files:

- timeline merge helpers under `app/lib/features/agent_chat/`
- `app/lib/models/ccb_agent_conversation.dart` only if needed
- source `/conversation` metadata tests only if response shape changes

P0 gates:

- A provider final reply replaces or completes the matching live turn.
- Terminal-only output such as `/status` remains visible when absent from
  native transcript.
- Older history pagination remains stable.
- Desktop-origin pane input appears after refresh without overwriting newer
  phone turns.

### Package D: Strict Real-AVD Evidence Packet

Goal: make the optimization objectively reviewable.

Required environment:

- Android Emulator: `emulator-5554` or `ccb_mobile_api35`.
- Gateway: server-wide real mobile gateway through loopback and `adb reverse`.
- Projects: disposable real CCB projects under `/home/bfly/yunwei/test_ccb2`.
- App: debug/profile APK built from current worktree.

Required actions:

1. Open project list and capture mounted/reachable real projects.
2. Open disposable project A, agent 1; send `hi`; record timings and transcript.
3. Send `/status`; verify visible output without CCB_REQ_ID or ask job.
4. Trigger long output; verify one live/final turn and stable scroll.
5. Open project A, agent 2; repeat a short send.
6. Open project B; prove project isolation.
7. Type from desktop pane; verify phone explicit refresh or live follow shows it.
8. Scroll away, generate output, verify no jump plus new-output affordance.
9. Idle 180 seconds, verify zero blind requests and no wakelock.
10. Break and restore `adb reverse` or gateway, verify recovery without replay.

Required artifacts:

- `summary.json` with status, app/source heads, dirty flags, gateway URL,
  device id, route provider, project roots, and package version.
- `timings.json` with per-case p50/p95 and raw samples.
- `requests.json` with request counts by endpoint.
- `device_metrics.json` with mem/cpu/gfx/wakelock summary.
- `logcat.txt`, gateway log tail, source evidence tail.
- screenshots and UI dumps for key states.
- source-side checks proving no `CCB_REQ_ID`, no `mobile_gateway`, no ask job
  for ordinary sends.

## Reviewer Gates

Reviewers should reject completion claims if any of these are true:

- Evidence uses fake/demo or the active `ccb_mobile` work project for
  exploratory sends.
- First active-send refresh remains at one second.
- Idle selected-agent page makes background conversation/history requests.
- `/status` output is invisible on the phone.
- Long output produces many disconnected reply cards.
- Terminal lifecycle/status noise appears as ordinary chat bubbles.
- Ordinary phone sends create ask jobs or inject `CCB_REQ_ID`.
- Metrics are only described verbally without machine-readable timing/request
  evidence.
- App/source commits are mixed without clear repo-specific verification.
- The installed APK hash/version is missing, or the test cannot prove the
  emulator is running the build under review.
- The evidence cannot prove the app is connected to the server-wide real
  gateway and disposable `test_ccb2` projects.

## Verification Commands

App focused tests:

```bash
cd app
flutter test test/conversation_refresh_scheduler_test.dart
flutter test test/pane_chat_event_messages_test.dart
flutter test test/agent_pane_event_coordinator_test.dart
flutter test test/pane_chat_controller_test.dart
flutter test test/agent_chat_composer_widget_test.dart
flutter test test/selected_agent_workspace_model_test.dart
git diff --check
```

App broader regression:

```bash
cd app
flutter test test/project_home_server_projects_widget_test.dart
flutter test test/project_home_terminal_navigation_widget_test.dart
flutter test test/project_home_focus_widget_test.dart
flutter test
```

Source, only if touched:

```bash
cd /home/bfly/yunwei/ccb_source
PYTHONPATH=lib python -m pytest test/test_mobile_gateway_service.py
python -m py_compile lib/mobile_gateway/service.py
git diff --check
```

Real AVD:

Use the strict Package D evidence packet. Completion requires a passing
machine-readable packet, not a screenshot-only claim.

## Completion Rule

Do not mark this goal complete until the strict real-AVD packet proves both
latency and correctness:

- local send and working indicators are immediate;
- first active refresh is below `300ms`;
- visible output meets the local AVD latency budget when the provider writes
  promptly;
- ordinary sends are pane-equivalent and ask-free;
- `/status`, long execution, desktop-origin input, scroll stability, recovery,
  and idle request-count gates pass;
- plan-tree evidence links the commits, tests, artifacts, and remaining risks.
