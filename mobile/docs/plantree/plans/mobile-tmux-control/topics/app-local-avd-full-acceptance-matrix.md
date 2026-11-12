# CCB Mobile Local AVD Full Acceptance Matrix

Date: 2026-06-27
Status: Detailed execution matrix
Read with:
[app-stress-and-performance-test-plan.md](app-stress-and-performance-test-plan.md)
and
[agent-native-conversation-and-input-correction.md](agent-native-conversation-and-input-correction.md).
For named case ids and per-case artifacts, use
[app-real-avd-stress-casebook.md](app-real-avd-stress-casebook.md).
For operator execution, use
[local-avd-real-project-test-runbook.md](local-avd-real-project-test-runbook.md)
as the concrete step-by-step script.

## Purpose

Define the concrete local Android Emulator acceptance matrix for CCB Mobile.
This document turns the broader stress plan into executable gates that workers
and reviewers can run without reinterpreting the product contract.
The casebook is the companion checklist for reporting exactly which gates were
run and which case first failed.

The acceptance target is not "the app can show some messages." The target is:

- the phone lists all real CCB projects served by the local machine gateway;
- the user opens a real test project, not `demo` and not a fixture;
- selected-agent chat mirrors the same server/desktop CCB agent pane;
- phone input is equivalent to typing in that pane;
- files produced by the user or backend can be uploaded, rendered, downloaded,
  and opened through authenticated mobile routes;
- performance, power, recovery, and refresh behavior remain stable enough for
  an always-nearby remote-control app.

## Non-Negotiable Rules

These are fail-fast rules. If any rule is broken, the run is not valid even if
some screenshots look correct.

1. Use a server-wide real gateway from `ccb install mobile` or the current
   equivalent source worktree command. Do not validate P0/P1 chat against fake
   local repositories.
2. The first app page must list all mounted/reachable CCB projects from the
   server gateway. A single current-project demo view is not enough.
3. Manual and automated destructive/send tests must target disposable projects
   under `/home/bfly/yunwei/test_ccb2`, such as `test_ccb2_alpha` and
   `test_ccb2_beta`.
   Those projects must also pass the real pane-backed fixture gate: the
   selected agents need valid pane evidence before any send, file, or reply
   result can count.
4. Do not send exploratory mobile test messages to `/home/bfly/yunwei/ccb_source/mobile`
   or `/home/bfly/yunwei/ccb_source` unless the test case explicitly targets
   those repositories.
5. Ordinary mobile chat must not create a CCB ask job, must not inject
   `CCB_REQ_ID`, and must not prepend device/user labels such as
   `mobile_gateway`.
6. Ordinary chat bubbles must not show internal provenance labels such as
   `completion_snapshot`, `provider_native`, provider cache names, job ids, or
   request ids.
7. The app must not refresh terminal history on a blind fixed 3-second loop.
   Refresh should be driven by open/resume, explicit user action, scroll
   boundaries, or a clearly bounded active-send state.
8. Stale ask/job/completion records must never replace newer pane-equivalent
   conversation turns.
9. No stress lane may continue after FATAL, ANR, OOM, app process death,
   unrecoverable gateway failure, or visible timeline corruption.

## Current Local AVD Acceptance Snapshot

As of 2026-06-27, the local Android Emulator track has accepted evidence for
all P0/P1 local server-wide gates. This does not replace future physical
device, Tailnet/VPN, or public-route validation, but it is enough to treat the
local AVD path as product-usable for handoff and regression.

| Stage | Status | Primary Evidence |
| :--- | :--- | :--- |
| 0. Safe baseline | Accepted | [local-avd-release-project-list-smoke-20260627.json](../history/local-avd-release-project-list-smoke-20260627.json), [local-avd-release-idle-current-clean-smoke-20260627.json](../history/local-avd-release-idle-current-clean-smoke-20260627.json), [local-avd-release-idle-request-smoke-20260627.json](../history/local-avd-release-idle-request-smoke-20260627.json) |
| 1. Server-wide project list | Accepted | [local-avd-release-project-list-smoke-20260627.json](../history/local-avd-release-project-list-smoke-20260627.json), [local-avd-release-reverse-recovery-smoke-20260627.json](../history/local-avd-release-reverse-recovery-smoke-20260627.json) |
| 2. Selected-agent pane identity | Accepted | [local-avd-native-pane-multi-current-smoke-20260627.json](../history/local-avd-native-pane-multi-current-smoke-20260627.json), [local-avd-native-pane-smoke-20260626.json](../history/local-avd-native-pane-smoke-20260626.json), [local-avd-native-pane-multi-smoke-20260626.json](../history/local-avd-native-pane-multi-smoke-20260626.json) |
| 3. Pane-equivalent send | Accepted | [local-avd-native-pane-multi-current-smoke-20260627.json](../history/local-avd-native-pane-multi-current-smoke-20260627.json), [local-avd-native-pane-multi-smoke-20260626.json](../history/local-avd-native-pane-multi-smoke-20260626.json), [local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json) |
| 4. Desktop-origin sync | Accepted | [local-avd-desktop-origin-sync-smoke-20260626.json](../history/local-avd-desktop-origin-sync-smoke-20260626.json), [local-avd-profile-scrolled-desktop-sync-smoke-20260627.json](../history/local-avd-profile-scrolled-desktop-sync-smoke-20260627.json) |
| 5. Older history/rendering | Accepted | [local-avd-profile-backfill-smoke-20260627.json](../history/local-avd-profile-backfill-smoke-20260627.json), [local-avd-release-long-history-smoke-20260627.json](../history/local-avd-release-long-history-smoke-20260627.json) |
| 6. Image/document upload | Accepted | [local-avd-profile-server-wide-gateway-smoke-20260627.json](../history/local-avd-profile-server-wide-gateway-smoke-20260627.json), [local-avd-attachment-rejection-smoke-20260627.json](../history/local-avd-attachment-rejection-smoke-20260627.json), [local-avd-profile-upload-24m-smoke-20260627.json](../history/local-avd-profile-upload-24m-smoke-20260627.json) |
| 7. Backend artifact download | Accepted | [local-avd-live-provider-artifact-current-smoke-20260627.json](../history/local-avd-live-provider-artifact-current-smoke-20260627.json), [local-avd-live-provider-artifact-smoke-20260627.json](../history/local-avd-live-provider-artifact-smoke-20260627.json), [local-avd-profile-live-artifact-smoke-20260627.json](../history/local-avd-profile-live-artifact-smoke-20260627.json), [local-avd-release-file-download-smoke-20260627.json](../history/local-avd-release-file-download-smoke-20260627.json), [local-avd-release-file-download-24m-smoke-20260627.json](../history/local-avd-release-file-download-24m-smoke-20260627.json) |
| 8. Multi-project isolation | Accepted | [local-avd-native-pane-multi-smoke-20260626.json](../history/local-avd-native-pane-multi-smoke-20260626.json), [local-avd-profile-server-wide-gateway-smoke-20260627.json](../history/local-avd-profile-server-wide-gateway-smoke-20260627.json) |
| 9. Recovery/reconnect/revoke | Accepted | [local-avd-release-reverse-recovery-current-smoke-20260627.json](../history/local-avd-release-reverse-recovery-current-smoke-20260627.json), [local-avd-reverse-recovery-smoke-20260626.json](../history/local-avd-reverse-recovery-smoke-20260626.json), [local-avd-gateway-restart-smoke-20260626.json](../history/local-avd-gateway-restart-smoke-20260626.json), [local-avd-ccbd-restart-smoke-20260626.json](../history/local-avd-ccbd-restart-smoke-20260626.json), [local-avd-release-reverse-recovery-smoke-20260627.json](../history/local-avd-release-reverse-recovery-smoke-20260627.json), [local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json) |
| 10. Performance/power/soak | Accepted | [local-avd-release-idle-current-clean-smoke-20260627.json](../history/local-avd-release-idle-current-clean-smoke-20260627.json), [local-avd-profile-30m-idle-soak-20260627.json](../history/local-avd-profile-30m-idle-soak-20260627.json), [local-avd-release-30m-idle-soak-20260627.json](../history/local-avd-release-30m-idle-soak-20260627.json), [local-avd-release-long-history-smoke-20260627.json](../history/local-avd-release-long-history-smoke-20260627.json), [local-avd-release-file-download-smoke-20260627.json](../history/local-avd-release-file-download-smoke-20260627.json), [local-avd-release-file-download-24m-smoke-20260627.json](../history/local-avd-release-file-download-24m-smoke-20260627.json), [local-avd-profile-upload-24m-smoke-20260627.json](../history/local-avd-profile-upload-24m-smoke-20260627.json) |

Accepted local AVD evidence must remain indexed from
[../history/evidence-index.md](../history/evidence-index.md). Any later
regression can reopen the relevant stage, but new work should now target
physical-device/Tailnet/VPN hardening or larger file-transfer stress rather
than proving the same local AVD baseline again.

## Environment Contract

Each run records the environment before the first action:

| Field | Required Evidence |
| :--- | :--- |
| App repo | commit, dirty status, build mode, APK path |
| Source repo | worktree path, commit, dirty status |
| Gateway | listen URL, route provider, state dir, host id |
| ADB | device id, `adb reverse --list`, Android API |
| Projects | `/v1/projects` count, healthy count, selected test roots |
| Pairing | selected gateway profile id or debug seed evidence |
| Logs | app logcat start cursor, gateway log path, source project log path |

Recommended local setup:

- source worktree:
  `/home/bfly/yunwei/ccb_source_mobile_agent_native`;
- test root: `/home/bfly/yunwei/test_ccb2`;
- device: Android Emulator `emulator-5554`;
- gateway: loopback-only host port with `adb reverse`;
- app package: `io.ccb.mobile.ccb_mobile`.

## Ownership And Review Model

Use one worker and one reviewer for each evidence packet unless the user asks
for parallel review. The worker must run the emulator and collect source/app
correlation. The reviewer must inspect the artifact packet and may rerun a
focused subset, but should not treat a separate local rerun as a replacement
for missing source-side evidence.

| Lane | Worker Output | Reviewer Must Check |
| :--- | :--- | :--- |
| Environment/project list | project list JSON, screenshots, request timings | server-wide gateway, no fake/demo fallback, stale entries degrade |
| Pane chat | pane evidence, phone screenshots, source logs | exact input, no ask metadata, correct provider reply |
| Dynamic sync | desktop-origin marker, idle request counts | no idle polling, explicit refresh works, scroll does not jump |
| Long history | seeded data description, pagination timings, screenshots | chronological prepend, no stale-job overwrite, frame/memory trend |
| Files/artifacts | corpus hashes, upload/download logs, saved file hashes | opaque ids, no host path leak, retry/error behavior |
| Recovery | host failure markers, app error/retry screenshots | fail-closed, recovery without reinstall, no duplicate input replay |
| Performance/power | `gfxinfo`, `meminfo`, request counts, wake locks | profile/release budgets, no polling storm, no ANR/OOM |

Do not send the same artifact packet to multiple reviewers as independent
evidence. If a second reviewer is requested, label it as a second review of the
same packet.

## Failure Severity

Classify the first failing gate before continuing.

| Severity | Examples | Action |
| :--- | :--- | :--- |
| P0 product blocker | fake/demo route used, wrong project, `CCB_REQ_ID`, send to wrong pane, auth revoke still succeeds, data crosses projects | stop run, create focused fix package |
| P1 release blocker | file hash mismatch, idle polling storm, visible timeline jumping, older-history reorder, app restart loses accepted attachment | stop pressure lane, fix before release gate |
| P2 hardening | slow debug latency, optional physical-device gap, unsupported file copy needs clearer text | record, continue only if P0/P1 are clean |
| Environment blocked | emulator offline, adb reverse missing, provider quota, source worktree dirty unexpectedly | stop and repair environment; do not mark app failed |

Every failure packet must include the first severity and owner:
`app-ui`, `app-transport`, `source-gateway`, `source-runtime`, `provider`, or
`environment`.

## Refresh Model To Test

The desired refresh behavior is operation-driven:

- home/project list refresh: visible refresh button plus pull-to-refresh when
  the list is at the top;
- project open: one initial ProjectView and selected-agent conversation load;
- selected-agent conversation refresh: explicit refresh affordance, resume from
  background, manual scroll boundary, and active-send completion;
- older history load: upward scroll near the oldest loaded item, using cursor
  pagination;
- newest refresh: when pinned near the newest item, manual refresh may append
  new turns and keep the list pinned; when not pinned, show a "New messages"
  affordance instead of jumping;
- active send: bounded short refresh while the selected agent is expected to
  reply, then stop or back off after the reply/timeout.

The app must not poll terminal history every 3 seconds forever. A 3-minute idle
window with no user action should show low gateway request count, low CPU, no
visible expand/collapse jumping, and no wake locks.

Current evidence: 2026-06-26 app head `09962f6`, 2026-06-27 profile head
`7898851`, 2026-06-27 release heads `6c3eb16`/`f2acc00`, and current clean
release app head `03ede70` cover the no-blind-polling path across
debug/profile/release. The current clean release 180-second smoke observed
`0` total gateway requests while untouched after limiting refresh to real
drag/overscroll gestures. The accepted release
30-minute soak observed `0` total gateway requests over `1800` untouched
seconds, PSS delta `485 KB`, `Wake Locks: size=0`,
`mWakeLockSummary=0x0`, and no FATAL/ANR/OOM.

## Acceptance Stages

Run stages in order. Do not advance when a P0 gate fails.

### Stage 0: Safe Baseline

Purpose: prove the current emulator and gateway are safe to touch.

Actions:

1. Confirm app foreground.
2. Confirm gateway reachable from host and app through `adb reverse`.
3. Call `/v1/projects` three times.
4. Capture screenshot, UI dump, meminfo, top, logcat, and gateway log tail.
5. Do not tap, type, upload, install, or clear app data.

Pass:

- app foreground and responsive;
- real project list or real selected project visible;
- `/v1/projects` has the expected real project count;
- no fake/demo-only state;
- no FATAL/ANR/OOM or app-held wake lock.

### Stage 1: Server-Wide Project List

Purpose: prove the mobile gateway is server-scoped, not project-scoped.

Actions:

1. Open the app home page.
2. Use the home refresh button.
3. Verify all healthy server projects appear.
4. Verify stale/unreachable registry entries degrade without blocking healthy
   projects.
5. Open `test_ccb2_alpha`, go back, open `test_ccb2_beta`.

Evidence:

- screenshot of project list;
- `/v1/projects` JSON sample;
- timings for refresh and open-project;
- selected project ids and roots.

Pass:

- list contains multiple real projects;
- `test_ccb2_*` projects are selectable;
- project list refresh p95 stays within the stress-plan budget;
- no stale project prevents opening a healthy project.

### Stage 2: Selected-Agent Pane Identity

Purpose: prove the app is rendering the selected agent pane, not unrelated
job/completion records.

Actions:

1. Open `test_ccb2_beta`.
2. Select `mobile_probe`.
3. Capture current desktop tmux pane evidence for that agent: session, window,
   pane id, visible tail, provider/session id when available.
4. Compare the newest phone timeline with the desktop pane.
5. Switch to `mobile_peer` and repeat.

Pass:

- selected agent in app matches selected pane evidence;
- newest phone visible conversation corresponds to the same agent pane;
- old ask/job records are absent unless explicitly shown as supplemental
  diagnostics;
- switching agents does not leak the other agent's transcript.

### Stage 3: Pane-Equivalent Send

Purpose: prove phone input equals direct pane typing.

Actions:

1. Send `mobile-turn-a:<id>` from phone to `mobile_probe`.
2. Inspect the desktop pane and source logs.
3. Wait for provider reply and refresh only through allowed user/active-send
   triggers.
4. Repeat with `mobile_peer`.
5. Send duplicate text, such as `hi` twice, to prove order and dedupe.

Pass:

- desktop pane receives the exact typed text;
- no `CCB_REQ_ID`, ask-job wrapper, or mobile label appears in pane, logs, or
  phone bubble;
- phone shows own turn and provider reply in order;
- duplicate sends remain distinct and ordered;
- a failed send does not silently replay terminal input.

### Stage 4: Desktop-Origin Sync

Purpose: prove the phone is a shared pane renderer, not only a phone message
client.

Actions:

1. Type `desktop-origin:<id>` directly in the desktop agent pane.
2. Do not touch the phone for 30 seconds.
3. Confirm no blind refresh storm occurs.
4. Use the phone's allowed refresh action.
5. Repeat while the phone is scrolled away from the newest message.

Pass:

- desktop-origin text appears on the phone after the allowed refresh;
- no reopen/project switch is required;
- when not pinned to newest, the app shows a new-message affordance instead of
  jumping;
- unchanged refresh does not expand/collapse or reorder existing blocks.

### Stage 5: Older History And Rendering

Purpose: prove dynamic transcript loading and stable rendering.

Actions:

1. Seed or select an agent with at least 200 turns.
2. Open newest page.
3. Scroll upward to load older pages until the first seeded marker appears.
4. Expand/collapse long Markdown blocks while pages are loading.
5. Refresh at bottom, middle, and top scroll positions.

Pass:

- older pages prepend in stable chronological order;
- visible scroll position is preserved after prepend;
- no stale completion/job records replace current native transcript;
- frame timing and memory remain inside debug/profile budgets;
- long Markdown, code blocks, and tables do not overflow.

### Stage 6: Image And Document Upload

Purpose: prove user-origin files are first-class chat attachments.

Actions:

1. Attach a PNG image with no text and send.
2. Attach `small.md` with text and send.
3. Attach multiple files up to the limit.
4. Try a near-limit file and an oversized file.
5. Switch agents and confirm drafts/attachments do not leak.

Pass:

- attachment tray renders thumbnail/chip without overflow;
- upload progress and failure are visible;
- accepted attachments appear in the conversation with stable ids;
- oversized/unsupported files fail clearly and leave composer usable;
- the receiving agent can access the uploaded file through the intended
  authenticated route, not by leaked host path.

### Stage 7: Backend Artifact Download

Purpose: prove files generated by agents can be downloaded to the phone.

Actions:

1. Ask the test agent to create a deterministic file artifact, such as a
   Markdown report and a small PNG.
2. Wait until the backend exposes the artifact in the selected-agent timeline.
3. Tap download.
4. Open or inspect the saved file.
5. Repeat after app restart and project switch.

Pass:

- artifact appears as a chip/link in the relevant conversation turn;
- download uses authenticated opaque mobile file/artifact ids;
- raw host paths are not exposed as public URLs;
- saved file hash or visible content matches the backend artifact;
- failed open/download has a clear retry path.

### Stage 8: Multi-Project Isolation

Purpose: prove server-wide access does not mix project state.

Actions:

1. Open `test_ccb2_alpha/mobile_probe`, send a marker, upload one small file.
2. Open `test_ccb2_beta/mobile_probe`, send a different marker, upload another
   file.
3. Return to alpha.
4. Revoke or stop beta and refresh alpha.

Pass:

- alpha and beta messages/files never cross;
- stopping beta does not break alpha project view or conversation;
- selected agent/project state remains correct after navigation;
- project ids are not replaced by host ids or route-provider ids.

### Stage 9: Recovery, Reconnect, And Revoke

Purpose: verify remote-control failure behavior.

Actions:

1. Remove `adb reverse`, then refresh.
2. Restore `adb reverse`, then refresh.
3. Restart mobile gateway.
4. Restart one test project `ccbd`.
5. Revoke the paired device.
6. Re-pair.
7. Background/resume during conversation refresh and file download.

Pass:

- protected routes fail after revoke;
- reconnect does not replay stale terminal input;
- no stuck spinner remains after recoverable failures;
- local drafts remain unless successfully sent or explicitly removed;
- app returns to project list or selected project without reinstall/clear data.

Current evidence:

- 2026-06-26 `58c5f00` covers project-list and selected-agent refresh recovery
  after `adb reverse` loss/restore:
  [../history/local-avd-reverse-recovery-smoke-20260626.json](../history/local-avd-reverse-recovery-smoke-20260626.json).
- 2026-06-26 `b584d74` covers project-list and selected-agent refresh recovery
  after the real mobile gateway process is stopped and restarted on the same
  loopback listener/state directory:
  [../history/local-avd-gateway-restart-smoke-20260626.json](../history/local-avd-gateway-restart-smoke-20260626.json).
- 2026-06-26 `6372afb` covers selected-agent explicit refresh recovery after
  the opened test project's real ccbd is stopped and restarted while the
  server-wide gateway stays up:
  [../history/local-avd-ccbd-restart-smoke-20260626.json](../history/local-avd-ccbd-restart-smoke-20260626.json).
- 2026-06-26 `69bbe32` covers selected-agent page background/resume after a
  real Android HOME/foreground cycle:
  [../history/local-avd-background-resume-smoke-20260626.json](../history/local-avd-background-resume-smoke-20260626.json).
- 2026-06-27 `da99280` covers selected-agent page reverse-loss recovery while
  backgrounded after Android HOME, temporary `adb reverse` removal, reverse
  restore, and foreground relaunch:
  [../history/local-avd-background-reverse-recovery-smoke-20260627.json](../history/local-avd-background-reverse-recovery-smoke-20260627.json).
- 2026-06-27 `f598ee5` covers backend artifact file-download
  background/resume after Android HOME/foreground resume with an `8 MiB`
  saved-file SHA256 check:
  [../history/local-avd-background-file-download-smoke-20260627.json](../history/local-avd-background-file-download-smoke-20260627.json).
- 2026-06-27 `952f2b2` covers draft/file preservation under recoverable
  gateway-path failure and duplicate terminal-input replay guard after
  explicit Retry:
  [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json).
- 2026-06-27 `a57fc92` covers paired-device revoke fail-closed behavior and
  app UI re-pair recovery without clearing app data:
  [../history/local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json).
- Stage 9 local AVD coverage now also includes release-mode `adb reverse`
  loss/restore pressure:
  [../history/local-avd-release-reverse-recovery-smoke-20260627.json](../history/local-avd-release-reverse-recovery-smoke-20260627.json).
  Physical-device and Tailnet/VPN recovery remain separate P2 validation
  paths.

### Stage 10: Performance, Power, And Soak

Purpose: prove the app remains practical for real use.

Actions:

1. Run a 3-minute idle foreground soak on a selected project.
2. Run a 30-minute profile/release soak with one manual refresh and agent
   switch every 5 minutes.
3. During profile mode, measure project list scroll, long chat scroll,
   attachment thumbnail scroll, and Markdown expansion.
4. After soak, perform one send and one download.

Pass:

- idle gateway requests <= 2/minute when no active send is pending;
- idle CPU <= budget and app-held wake locks are zero;
- PSS growth stays within budget and recovers after idle;
- frame p95 stays within stress-plan gates;
- post-soak send/download still works.

Accepted evidence:

- 2026-06-26 `09962f6` covers the request-rate plus debug device-metrics
  subgate: `0.0` selected-agent conversation/terminal requests per minute
  over `180` idle seconds, seven metric samples, PSS delta `-508 KB`,
  `Wake Locks: size=0`, `mWakeLockSummary=0x0`, and no FATAL/ANR/OOM.
- 2026-06-27 profile 30-minute idle soak covers the profile path:
  [../history/local-avd-profile-30m-idle-soak-20260627.json](../history/local-avd-profile-30m-idle-soak-20260627.json).
- 2026-06-27 release 30-minute idle soak covers the release path:
  [../history/local-avd-release-30m-idle-soak-20260627.json](../history/local-avd-release-30m-idle-soak-20260627.json).
- Release long-history and file-download smokes provide active frame/memory
  pressure evidence:
  [../history/local-avd-release-long-history-smoke-20260627.json](../history/local-avd-release-long-history-smoke-20260627.json) and
  [../history/local-avd-release-file-download-smoke-20260627.json](../history/local-avd-release-file-download-smoke-20260627.json).
- The near-limit release artifact download hardening run supplements the
  `8 MiB` baseline with a `24 MiB` provider-native artifact:
  [../history/local-avd-release-file-download-24m-smoke-20260627.json](../history/local-avd-release-file-download-24m-smoke-20260627.json).
- The near-limit profile upload hardening run supplements the existing
  file/image upload matrix with a `24 MiB` user-origin attachment loopback:
  [../history/local-avd-profile-upload-24m-smoke-20260627.json](../history/local-avd-profile-upload-24m-smoke-20260627.json).
- The release-mode system-picker upload hardening run closes the same
  near-limit user-origin file path without Flutter Driver by using Android
  DocumentsUI, a release APK, and gateway byte/hash verification:
  [../history/local-avd-release-upload-24m-smoke-20260627.json](../history/local-avd-release-upload-24m-smoke-20260627.json).

## Manual Tester Script

Use this script when handing the emulator to a human reviewer:

1. Confirm the home page shows multiple real projects.
2. Tap refresh and verify the list does not collapse to demo.
3. Open only `test_ccb2_alpha` or `test_ccb2_beta`.
4. Select `mobile_probe`; compare newest phone messages with the desktop pane.
5. Send `manual-phone:<timestamp>`; verify the desktop pane gets exact text.
6. Type `manual-desktop:<timestamp>` in the desktop pane; refresh phone and
   verify it appears.
7. Scroll upward and load older messages.
8. Attach one small text file and one image.
9. Download one backend-generated artifact if present.
10. Leave the phone idle for 3 minutes and confirm no visible jumping.

The reviewer records screenshots after steps 1, 4, 6, 8, and 10.

## Automation Outputs

Every automated run writes:

- `summary.json` with status `ok`, `warn`, `blocked`, or `fail`;
- `environment.json`;
- `projects.json`;
- `timings.json`;
- `memory.json`;
- `power.txt`;
- `logcat.txt`;
- `gateway.log.tail`;
- `ui-before.xml`, `ui-after.xml`;
- screenshots for project list, selected project, post-send, file chip, and
  post-soak.

Failure reports must include the first failed gate and one owner:
`app-ui`, `app-transport`, `source-gateway`, `source-runtime`, `provider`, or
`environment`.

## Worker Packages

Keep work packages cohesive, not microscopic:

1. **Native chat contract package**: source pane-equivalent conversation,
   default pane send, no ask/`CCB_REQ_ID`, tests, and one AVD smoke.
2. **Refresh UX package**: remove blind 3-second terminal-history polling,
   add home refresh button, conversation manual/scroll refresh, stable
   new-message affordance, tests, and idle request-count evidence.
3. **File/artifact package**: upload image/document, backend artifact
   discovery/download, authenticated ids, storage/open behavior, tests, and AVD
   evidence.
4. **Performance automation package**: extend compass scripts for Level 2-10
   lanes, profile-mode frame/memory capture, and standardized JSON artifacts.

Do not split each callback or small helper into its own package unless it is a
blocking review fix.

## Reviewer Acceptance Checklist

Reviewers should reject a package if:

- evidence uses fake/demo for P0 chat or files;
- ordinary send still uses `/agents/{agent}/messages` ask semantics;
- `CCB_REQ_ID`, `mobile_gateway`, or `completion_snapshot` appears in the
  normal chat surface;
- project list is current-project-only instead of server-wide;
- the phone timeline disagrees with the active desktop pane and the mismatch is
  not surfaced as a diagnostic failure;
- blind idle polling causes visible jumping, high request rate, CPU churn, or
  wake locks;
- file download exposes raw host paths or unauthenticated URLs;
- test artifacts omit source/app commit, selected project root, selected agent,
  and emulator id.

## Exit Criteria

The local AVD track is considered complete for the current server-wide product
baseline after:

- Stages 0-10 pass against a real server-wide gateway;
- at least two `test_ccb2` projects and two agents per project are exercised;
- no fake/demo evidence is used for P0 acceptance;
- no ordinary mobile send creates ask-job metadata;
- pane-equivalent read and write are both proven by desktop-phone comparison;
- image/document upload and backend artifact download pass;
- 30-minute profile/release soak passes power and memory gates;
- all evidence is indexed from
  [history/evidence-index.md](../history/evidence-index.md).

## Open Follow-Ups

- Physical-device and Tailnet/VPN recovery still need separate validation
  because the accepted recovery lane is local Android Emulator `adb reverse`.
- Final profile/release budgets may need adjustment after the first physical
  hardware baseline, but local release-mode AVD now covers both near-limit
  user-origin upload and backend artifact download.
- The exact native transcript source per provider remains provider-specific;
  Codex is the first required implementation.
- Search/archive mode is not required for the first release, but may become
  necessary when per-agent transcript size grows beyond the tested 200-turn
  dataset.
