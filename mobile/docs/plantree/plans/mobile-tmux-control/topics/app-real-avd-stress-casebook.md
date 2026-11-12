# CCB Mobile Real AVD Stress Casebook

Date: 2026-06-27
Status: Detailed test case inventory
Read with:
[app-stress-and-performance-test-plan.md](app-stress-and-performance-test-plan.md),
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md),
and
[local-avd-real-project-test-runbook.md](local-avd-real-project-test-runbook.md).

## Purpose

This casebook turns the local Android Emulator acceptance matrix into
named, repeatable test cases. It is the checklist for workers, reviewers, and
manual operators when the goal is to prove that CCB Mobile works against the
real local server-wide CCB backend.

The cases are intentionally broader than unit tests. A case is accepted only
when it records:

- the CCB Mobile app commit and dirty status;
- the CCB source worktree commit and dirty status;
- the server-wide gateway URL, host id, route provider, and state directory;
- the Android device id and `adb reverse --list`;
- the selected `/home/bfly/yunwei/test_ccb2` project root;
- the selected agent pane evidence;
- screenshots, UI dumps, logs, timings, memory, request counts, and power
  evidence appropriate to the case.

## Global Validity Rules

These rules apply to every P0/P1 case.

1. The app must be connected to a server-wide mobile gateway. A fake/local demo
   repository is never accepted as real-backend evidence.
2. Send, upload, and destructive tests must use disposable projects under
   `/home/bfly/yunwei/test_ccb2`.
3. The selected test agent must have real CCB pane evidence before any
   chat/file/reply result counts.
4. Ordinary phone input must be equivalent to direct pane typing: no ask-job
   envelope, no `CCB_REQ_ID`, no `mobile_gateway`, no visible provider/cache
   provenance labels in ordinary chat bubbles.
5. Home refresh, selected-agent refresh, older-history loading, and active-send
   refresh must be operation-driven. Blind 3-second terminal-history polling is
   a failure for idle/stability cases.
6. Do not submit the same review packet to several reviewers as if it were
   independent evidence. Assign one reviewer per evidence packet unless the
   user explicitly asks for parallel review.

## Current Accepted Coverage

The local Android Emulator track has accepted evidence for every P0/P1 case in
this casebook as of 2026-06-27. Treat this as the local AVD baseline for
manual handoff and regression. Do not use it to claim physical-device,
Tailnet/VPN, or public-route recovery; those remain separate hardening lanes.
The physical Android phone + Tailnet hardening lane is now tracked separately
in
[physical-tailnet-device-validation-runbook.md](physical-tailnet-device-validation-runbook.md)
with T0-T6 cases for preflight, server-wide pairing, pane-equivalent
conversation, dynamic sync/history, files/artifacts, Tailnet recovery, and
physical-device power/performance soak.

| Case | Status | Evidence |
| :--- | :--- | :--- |
| C0.1 Environment/Gateway Identity | Accepted | [../history/local-avd-release-project-list-smoke-20260627.json](../history/local-avd-release-project-list-smoke-20260627.json), [../history/local-avd-release-idle-current-clean-smoke-20260627.json](../history/local-avd-release-idle-current-clean-smoke-20260627.json), [../history/local-avd-release-idle-request-smoke-20260627.json](../history/local-avd-release-idle-request-smoke-20260627.json) |
| C1.1 Server-Wide Project Refresh | Accepted | [../history/local-avd-release-project-list-smoke-20260627.json](../history/local-avd-release-project-list-smoke-20260627.json), [../history/local-avd-release-reverse-recovery-smoke-20260627.json](../history/local-avd-release-reverse-recovery-smoke-20260627.json) |
| C2.1 Selected-Agent Pane Identity | Accepted | [../history/local-avd-native-pane-multi-current-smoke-20260627.json](../history/local-avd-native-pane-multi-current-smoke-20260627.json), [../history/local-avd-native-pane-smoke-20260626.json](../history/local-avd-native-pane-smoke-20260626.json), [../history/local-avd-native-pane-multi-smoke-20260626.json](../history/local-avd-native-pane-multi-smoke-20260626.json) |
| C3.1/C3.2 Phone Send And Provider Reply | Accepted | [../history/local-avd-native-pane-multi-current-smoke-20260627.json](../history/local-avd-native-pane-multi-current-smoke-20260627.json), [../history/local-avd-native-pane-multi-smoke-20260626.json](../history/local-avd-native-pane-multi-smoke-20260626.json), [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json) |
| C4.1/C4.2/C4.3 Dynamic Sync And No Idle Polling | Accepted | [../history/local-avd-desktop-origin-sync-smoke-20260626.json](../history/local-avd-desktop-origin-sync-smoke-20260626.json), [../history/local-avd-profile-scrolled-desktop-sync-smoke-20260627.json](../history/local-avd-profile-scrolled-desktop-sync-smoke-20260627.json), [../history/local-avd-release-idle-current-clean-smoke-20260627.json](../history/local-avd-release-idle-current-clean-smoke-20260627.json), [../history/local-avd-release-30m-idle-soak-20260627.json](../history/local-avd-release-30m-idle-soak-20260627.json) |
| C5.1 Older History Pagination | Accepted | [../history/local-avd-profile-backfill-smoke-20260627.json](../history/local-avd-profile-backfill-smoke-20260627.json), [../history/local-avd-release-long-history-smoke-20260627.json](../history/local-avd-release-long-history-smoke-20260627.json) |
| C6.1-C6.4 Image/Document Upload And Rejection | Accepted | [../history/local-avd-profile-server-wide-gateway-smoke-20260627.json](../history/local-avd-profile-server-wide-gateway-smoke-20260627.json), [../history/local-avd-attachment-rejection-smoke-20260627.json](../history/local-avd-attachment-rejection-smoke-20260627.json), [../history/local-avd-file-restart-smoke-20260627.json](../history/local-avd-file-restart-smoke-20260627.json), [../history/local-avd-profile-upload-24m-smoke-20260627.json](../history/local-avd-profile-upload-24m-smoke-20260627.json), [../history/local-avd-release-upload-24m-smoke-20260627.json](../history/local-avd-release-upload-24m-smoke-20260627.json) |
| C7.1/C7.2 Backend Artifact Download | Accepted | [../history/local-avd-live-provider-artifact-current-smoke-20260627.json](../history/local-avd-live-provider-artifact-current-smoke-20260627.json), [../history/local-avd-live-provider-artifact-smoke-20260627.json](../history/local-avd-live-provider-artifact-smoke-20260627.json), [../history/local-avd-profile-live-artifact-smoke-20260627.json](../history/local-avd-profile-live-artifact-smoke-20260627.json), [../history/local-avd-release-file-download-smoke-20260627.json](../history/local-avd-release-file-download-smoke-20260627.json), [../history/local-avd-release-file-download-24m-smoke-20260627.json](../history/local-avd-release-file-download-24m-smoke-20260627.json) |
| C8.1 Multi-Project Isolation | Accepted | [../history/local-avd-native-pane-multi-smoke-20260626.json](../history/local-avd-native-pane-multi-smoke-20260626.json), [../history/local-avd-profile-server-wide-gateway-smoke-20260627.json](../history/local-avd-profile-server-wide-gateway-smoke-20260627.json) |
| C9.1-C9.4 Recovery/Revoke/Replay Guard | Accepted | [../history/local-avd-release-reverse-recovery-current-smoke-20260627.json](../history/local-avd-release-reverse-recovery-current-smoke-20260627.json), [../history/local-avd-reverse-recovery-smoke-20260626.json](../history/local-avd-reverse-recovery-smoke-20260626.json), [../history/local-avd-gateway-restart-smoke-20260626.json](../history/local-avd-gateway-restart-smoke-20260626.json), [../history/local-avd-ccbd-restart-smoke-20260626.json](../history/local-avd-ccbd-restart-smoke-20260626.json), [../history/local-avd-release-reverse-recovery-smoke-20260627.json](../history/local-avd-release-reverse-recovery-smoke-20260627.json), [../history/local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json), [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json) |
| C10.1/C10.2 Idle/Frame/Memory Pressure | Accepted | [../history/local-avd-release-idle-current-clean-smoke-20260627.json](../history/local-avd-release-idle-current-clean-smoke-20260627.json), [../history/local-avd-profile-30m-idle-soak-20260627.json](../history/local-avd-profile-30m-idle-soak-20260627.json), [../history/local-avd-release-30m-idle-soak-20260627.json](../history/local-avd-release-30m-idle-soak-20260627.json), [../history/local-avd-release-long-history-smoke-20260627.json](../history/local-avd-release-long-history-smoke-20260627.json), [../history/local-avd-release-file-download-smoke-20260627.json](../history/local-avd-release-file-download-smoke-20260627.json), [../history/local-avd-release-file-download-24m-smoke-20260627.json](../history/local-avd-release-file-download-24m-smoke-20260627.json), [../history/local-avd-profile-upload-24m-smoke-20260627.json](../history/local-avd-profile-upload-24m-smoke-20260627.json), [../history/local-avd-release-upload-24m-smoke-20260627.json](../history/local-avd-release-upload-24m-smoke-20260627.json) |

## Artifact Root

Every run writes a directory:

```text
/tmp/ccb-mobile-avd-case-<timestamp>/
  summary.json
  environment.json
  projects.json
  selected-agent-runtime.json
  timings.json
  request-counts.json
  memory.json
  power.txt
  gfxinfo.txt
  logcat.txt
  gateway.log.tail
  source-project.log.tail
  screenshots/
  ui/
  files/
```

`summary.json` must include a single first failed case and owner when the run
is not green:

```json
{
  "status": "ok|warn|blocked|fail",
  "case_id": "C3.2",
  "first_failed_gate": "exact pane input visible",
  "owner": "app-ui|app-transport|source-gateway|source-runtime|provider|environment|null",
  "fake_or_demo_used": false,
  "real_pane_verified": true,
  "ccb_req_id_seen": false,
  "blind_polling_seen": false
}
```

## P0 Cases: Must Pass Before Manual Product Acceptance

### C0.1 Environment And Gateway Identity

Goal: prove the app is talking to the intended server-wide gateway.

Setup:

- one loopback-only mobile gateway;
- one `adb reverse` entry for that gateway port;
- app foreground on Android Emulator;
- no ambiguous older gateway profile selected in the app.

Actions:

1. Record `git status --short` for app and source worktrees.
2. Record `adb devices -l` and `adb reverse --list`.
3. Call `/v1/health` and `/v1/projects` from the host.
4. Capture the foreground app screenshot and UI dump.

Pass:

- `/v1/projects` returns a server-wide list, not a single current project;
- the app home page or selected project corresponds to that same gateway;
- no `demo` fallback appears when a server profile is active;
- no FATAL/ANR/OOM appears in logcat.

### C1.1 Server-Wide Project Refresh

Goal: prove the first page can refresh all mounted/reachable projects.

Actions:

1. Navigate to the project list.
2. Tap the visible refresh button.
3. Compare visible project names with `projects.json`.
4. Open `test_ccb2_alpha`, return, then open `test_ccb2_beta`.

Metrics:

- refresh duration;
- open-project duration;
- healthy/unreachable project counts.

Pass:

- both `test_ccb2_*` projects are visible and selectable;
- one stale/unreachable entry cannot fail the whole project list;
- refresh p95 stays within the budget in the stress plan.

### C2.1 Selected-Agent Pane Identity

Goal: prove the phone is rendering the selected desktop/server agent pane.

Actions for `mobile_probe` and `mobile_peer`:

1. Select the agent in the app.
2. Record `pane_id`, tmux session/window, namespace epoch, provider/session
   evidence, and desktop pane tail.
3. Capture phone timeline screenshot and UI dump.

Pass:

- newest phone timeline content corresponds to the selected agent pane;
- switching agents changes the transcript and does not leak the other agent;
- ordinary bubbles do not show `completion_snapshot`, `provider_native`,
  `jobs.jsonl`, `project_view`, request ids, or job ids.

### C3.1 Phone Send Is Pane Input

Goal: prove phone send is equivalent to direct typing into the selected pane.

Actions:

1. Send `mobile-turn-a:<timestamp>` to `mobile_probe`.
2. Inspect the desktop pane before waiting for a provider reply.
3. Inspect source logs for ask/job creation.
4. Repeat with `mobile_peer`.

Pass:

- the desktop pane receives exactly the typed text;
- no `CCB_REQ_ID` appears anywhere in the pane, phone bubble, or source logs;
- no `mobile_gateway` or device label is prepended;
- no ask-job entry is created for ordinary chat.

### C3.2 Provider Reply Round Trip

Goal: prove the phone can show the real backend/provider reply.

Actions:

1. Run C3.1.
2. Wait for the provider reply.
3. Use only allowed active-send refresh/backoff or manual refresh.
4. Compare the phone reply with the provider transcript or pane output.

Pass:

- first reply appears in the correct agent timeline;
- the reply is not a fake/local echo;
- local user message and provider reply are ordered correctly;
- a duplicate text send such as `hi`, `hi` remains two distinct turns.

### C4.1 Desktop-Origin Dynamic Sync

Goal: prove the phone is a shared pane renderer, not only a mobile send client.

Actions:

1. Type `desktop-origin:<timestamp>` directly into the desktop agent pane.
2. Leave the phone untouched for 30 seconds.
3. Record gateway request counts during that idle window.
4. Trigger the explicit selected-agent refresh.

Pass:

- desktop-origin content appears after refresh without reopening the project;
- idle request rate does not show blind terminal-history polling;
- if the phone is scrolled away from newest, the app shows a new-message
  affordance instead of jumping.

### C4.2 Scrolled-Away New-Message Stability

Goal: prove explicit refresh does not destroy the user's reading position.

Actions:

1. Open a selected-agent page with at least 40 visible/native turns.
2. Scroll upward until the newest turn is off screen.
3. Type `desktop-scrolled-origin:<timestamp>` directly in the desktop pane.
4. Trigger the phone's selected-agent refresh.
5. Tap the new-message affordance if one appears.

Pass:

- the timeline does not jump to bottom during refresh while the user is reading
  older content;
- exactly one new-message affordance appears;
- tapping the affordance scrolls to the new turn;
- expanded/collapsed state of visible cards is preserved;
- no stale ask/job/completion records are inserted around the new turn.

### C4.3 No-Idle-Polling Request Audit

Goal: prove the app is not silently polling conversation or terminal history on
a fixed idle interval.

Actions:

1. Open a selected-agent page and wait until any active send/reply state has
   settled.
2. Reset or mark gateway request counters.
3. Leave the emulator untouched for 180 seconds.
4. Collect gateway endpoint counts, app CPU, PSS, wake locks, logcat, and a
   before/after screenshot.

Pass:

- selected-agent conversation/terminal endpoints stay within the idle request
  budget in the stress plan;
- no visible timeline expansion/collapse or scroll jump occurs;
- app-held wake locks are zero;
- no background refresh spinner is visible after settle.

Accepted evidence:

- 2026-06-26 `09962f6` covers the debug request-rate and device-metrics
  portion on a real server-wide Android Emulator path: `180` seconds on an
  open selected-agent page produced `0` total gateway requests,
  `0` conversation/terminal requests, seven device metric samples, PSS delta
  `-508 KB`, `Wake Locks: size=0`, `mWakeLockSummary=0x0`, and no
  FATAL/ANR/OOM before a post-window explicit refresh:
  [../history/local-avd-idle-metrics-smoke-20260626.json](../history/local-avd-idle-metrics-smoke-20260626.json).

## P1 Cases: File, History, Recovery, And Release Readiness

### C5.1 Older History Pagination

Goal: prove old native transcript pages load upward without replacing new
content.

Dataset:

- at least 200 native turns;
- mixed Markdown, code blocks, tables, links, image/document chips, and one
  backend artifact link.

Pass:

- older pages prepend in chronological order;
- visible scroll position is preserved after prepend;
- unchanged refresh preserves expanded/collapsed states;
- no stale ask/job/completion records replace current pane history.

### C6.1 Image Upload

Goal: prove image send works through the real selected-agent path.

Actions:

1. Select `image.png`.
2. Send with empty text.
3. Observe thumbnail, upload state, conversation chip, and agent access.
4. Download/open the resulting attachment if the UI exposes it.

Pass:

- preview appears within budget;
- upload state is visible and does not get stuck;
- the accepted file uses an authenticated opaque id;
- no raw host path is exposed to the phone.

### C6.2 Document Upload

Goal: prove documents work and remain readable to the receiving agent.

Actions:

1. Send `small.md` with text.
2. Send `document.pdf`.
3. Record SHA256 before upload and after download.
4. Ask the agent to reference the uploaded file by content, not just metadata.

Pass:

- chips show filename/size without overflow;
- the agent can access the uploaded content through the gateway/source file
  route;
- downloaded file hash or visible content matches.

### C6.3 Rejection And Recovery

Goal: prove rejected files do not corrupt the composer.

Actions:

1. Try `oversized.bin`.
2. Try `unsupported.xyz`.
3. Remove the failed attachment.
4. Send a normal text message.

Pass:

- failure reason is visible;
- the composer remains usable;
- no later message reuses the rejected file.

### C6.4 Attachment Persistence Across Restart

Goal: prove successful attachments remain usable after app and gateway restart.

Actions:

1. Send `small.md` and `image.png` through the selected-agent path.
2. Download both from the visible conversation and record SHA256.
3. Force-stop and relaunch the app.
4. Restart the mobile gateway on the same state directory.
5. Reopen the same project/agent and download both attachments again.

Pass:

- attachment chips are restored from history without host-path leakage;
- both downloads succeed after restart;
- hashes match the original corpus or source-side stored object;
- no duplicate upload happens during restore.

### C7.1 Backend Artifact Download

Goal: prove agent-generated files can be downloaded to the phone.

Actions:

1. Ask the agent to generate a deterministic Markdown report.
2. Ask the agent to generate a deterministic PNG or binary artifact.
3. Wait for artifact chips/links in the timeline.
4. Download and open or hash the saved file.
5. Restart the app and download again from history.

Pass:

- artifact belongs to the current project and agent;
- artifact route uses authenticated opaque ids;
- saved content matches the backend artifact;
- failed open/download has retry feedback.

### C7.2 Live Provider-Generated Artifact

Goal: prove the app can handle artifacts created during the same live run, not
only seeded transcript fixtures.

Actions:

1. Send a prompt asking the selected agent to create a deterministic Markdown
   file named with the run timestamp.
2. Send a prompt asking the selected agent to create a deterministic image or
   binary artifact when the provider/tooling supports it.
3. Wait for the provider response and explicit refresh if needed.
4. Download every new artifact shown in that response.
5. Compare content/hash with the source-side artifact record.

Pass:

- artifact chips/links appear in the same agent turn that created them;
- artifact ids are opaque and scoped to the selected project/agent;
- the phone can download the artifact without a raw host filesystem path;
- a repeated download uses the same artifact identity and does not create a
  duplicate source artifact.

### C8.1 Multi-Project Isolation

Goal: prove server-wide routing does not mix projects.

Actions:

1. In alpha, send marker A and upload file A.
2. In beta, send marker B and upload file B.
3. Return to alpha.
4. Stop or degrade beta, then refresh alpha.

Pass:

- alpha and beta messages/files never cross;
- stopping beta does not break alpha;
- selected project ids remain project ids, not host ids or route-provider ids.

### C9.1 Disconnect And Retry

Goal: prove network loss and restore are safe.

Actions:

1. Remove `adb reverse`.
2. Refresh project list and selected-agent conversation.
3. Restore `adb reverse`.
4. Refresh again.
5. Restart the mobile gateway and retry.

Pass:

- errors are clear and recoverable;
- no stuck spinner remains;
- drafts are preserved;
- no terminal input is replayed after reconnect.

Smoke status:

- 2026-06-26 `58c5f00` covers the project-list and selected-agent refresh
  paths for `adb reverse` loss/restore on a real Android Emulator gateway:
  [../history/local-avd-reverse-recovery-smoke-20260626.json](../history/local-avd-reverse-recovery-smoke-20260626.json).
- 2026-06-26 `b584d74` covers the project-list and selected-agent refresh
  paths for real mobile gateway process stop/restart on the same loopback
  listener and state directory:
  [../history/local-avd-gateway-restart-smoke-20260626.json](../history/local-avd-gateway-restart-smoke-20260626.json).
- 2026-06-26 `6372afb` covers selected-agent explicit refresh recovery after
  the opened test project's real ccbd is stopped and restarted while the
  server-wide gateway stays up:
  [../history/local-avd-ccbd-restart-smoke-20260626.json](../history/local-avd-ccbd-restart-smoke-20260626.json).
- 2026-06-27 `952f2b2` covers a failed selected-agent send with one
  attachment while `adb reverse` is removed, then explicit Retry after
  restore; source-side native transcript evidence shows one matching user
  prompt, one matching reply, no jobs matches, no `CCB_REQ_ID`, and no
  `mobile_gateway`:
  [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json).
- 2026-06-27 `a57fc92` covers paired-device revoke and re-pair recovery:
  [../history/local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json).
- C9.1 smoke-level recovery coverage is now broad enough for local AVD. The
  release path is covered by
  [../history/local-avd-release-reverse-recovery-smoke-20260627.json](../history/local-avd-release-reverse-recovery-smoke-20260627.json),
  which removes `adb reverse`, observes a visible connection failure, seeds a
  new provider-native backend marker while disconnected, restores reverse, and
  verifies that explicit refresh renders the new marker.

### C9.2 Revoke And Re-Pair

Goal: prove auth failure closes protected routes.

Actions:

1. Revoke the paired device from the host.
2. Try project list, conversation refresh, send, terminal open, upload, and
   download.
3. Re-pair the app to the same server.

Pass:

- protected routes fail after revoke;
- the app does not continue using stale credentials;
- re-pair restores the project list and selected project without clearing
  unrelated app state.

Smoke status:

- 2026-06-27 `a57fc92` covers this path on a real server-wide Android
  Emulator gateway:
  [../history/local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json).
  The harness revoked `avd_20260626165524`, verified the old token returned
  HTTP `401` with `device token revoked`, then the app claimed replacement
  pairing `pair_355f43918c137673` through Connection Details and recovered
  selected-agent refresh without clearing app data.

### C9.3 Background And Resume During Work

Goal: prove Android lifecycle transitions do not corrupt in-flight state.

Actions:

1. Start a selected-agent refresh and send the app to background.
2. Bring the app foreground and verify refresh result or visible retry state.
3. Start a file download and background the app.
4. Bring the app foreground and verify the download completes or can be
   retried.
5. Repeat while `adb reverse` is temporarily removed and restored.

Pass:

- no app process death, ANR, or stuck overlay;
- no duplicate pane input is sent after resume;
- draft text and unsent attachments are preserved;
- completed downloads are still openable after resume;
- failed work has a visible retry path.

Smoke status:

- 2026-06-26 `69bbe32` covers the selected-agent page background/resume
  subpath on a real Android Emulator gateway:
  [../history/local-avd-background-resume-smoke-20260626.json](../history/local-avd-background-resume-smoke-20260626.json).
  The harness opened `test_ccb2_alpha/mobile_probe`, sent the real Android
  HOME key event, waited `10` seconds, relaunched `MainActivity`, verified the
  selected-agent workspace/composer remained visible with no forbidden
  ask/provenance labels, and completed explicit conversation refresh.
- 2026-06-27 `da99280` covers the selected-agent reverse-loss while
  backgrounded subpath on a real Android Emulator gateway:
  [../history/local-avd-background-reverse-recovery-smoke-20260627.json](../history/local-avd-background-reverse-recovery-smoke-20260627.json).
  The harness opened `test_ccb2_alpha/mobile_probe`, sent Android HOME,
  removed `adb reverse tcp:19068`, waited `10` seconds, restored
  `adb reverse tcp:19068 tcp:19068`, relaunched `MainActivity`, verified the
  selected-agent workspace/composer remained visible with no forbidden
  ask/provenance labels, and completed explicit conversation refresh.
- 2026-06-27 `f598ee5` covers backend artifact file-download
  background/resume on a real Android Emulator gateway:
  [../history/local-avd-background-file-download-smoke-20260627.json](../history/local-avd-background-file-download-smoke-20260627.json).
  The harness opened `test_ccb2_alpha/mobile_probe`, tapped an `8 MiB`
  artifact download, sent Android HOME for `10` seconds, foregrounded the app,
  and verified the saved Android file SHA256.
- 2026-06-27 `952f2b2` covers draft/attachment preservation and explicit
  Retry replay-guard after gateway-path loss:
  [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json).
- C9.3 local AVD smoke-level lifecycle evidence is closed. Longer
  physical-device or Tailnet/VPN lifecycle pressure remains separate.

### C9.4 Pending Draft And Replay Guard

Goal: prove reconnect/retry never replays user input silently.

Actions:

1. Type a draft with one attachment but do not send.
2. Remove `adb reverse` and tap send.
3. Restore `adb reverse`.
4. Retry explicitly once.
5. Inspect the desktop pane and gateway logs.

Pass:

- the failed send keeps the draft or a retryable failed message;
- desktop pane receives the text at most once;
- retry is user-triggered, not automatic hidden replay;
- attachment upload either succeeds once or remains explicitly retryable.

Smoke status:

- 2026-06-27 `952f2b2` covers this path on a real server-wide Android
  Emulator gateway:
  [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json).
  The harness attached `replay-guard-attachment.txt`, removed
  `adb reverse tcp:19070` before send, verified the failed message retained
  the prompt and attachment, restored `adb reverse tcp:19070 tcp:19070`,
  tapped `Retry` once, and verified source-side transcript counts
  `user_match_count == 1` and `reply_match_count == 1`.

### C10.1 Idle Power And Request Rate

Goal: prove the app does not burn power while idle.

Actions:

1. Open a selected-agent page.
2. Leave it untouched for 3 minutes in debug mode.
3. Repeat for 30 minutes in profile/release mode before release.
4. Capture request counts, CPU, memory, wake locks, and logcat.

Pass:

- idle gateway requests are <= 2/minute when no active send is pending;
- app-held wake locks are zero;
- debug idle CPU is <= 3 percent diagnostic target;
- profile/release idle CPU is <= 1 percent target;
- memory growth stays within the stress-plan budget;
- no visible timeline jumping occurs.

Accepted evidence:

- 2026-06-26 `09962f6` closes the request-rate and debug device-metrics
  subgate: `0.0` selected-agent conversation/terminal requests per minute
  over `180` idle seconds, seven samples, PSS delta `-508 KB`,
  `Wake Locks: size=0`, `mWakeLockSummary=0x0`, and no FATAL/ANR/OOM. It
  is supplemented by accepted profile and release 30-minute soaks:
  [../history/local-avd-profile-30m-idle-soak-20260627.json](../history/local-avd-profile-30m-idle-soak-20260627.json) and
  [../history/local-avd-release-30m-idle-soak-20260627.json](../history/local-avd-release-30m-idle-soak-20260627.json).
  Release long-history and file-download smokes cover active frame/memory
  pressure:
  [../history/local-avd-release-long-history-smoke-20260627.json](../history/local-avd-release-long-history-smoke-20260627.json) and
  [../history/local-avd-release-file-download-smoke-20260627.json](../history/local-avd-release-file-download-smoke-20260627.json).

### C10.2 Rendering Frame Pressure

Goal: prove long timelines and attachments remain smooth enough.

Actions:

1. Record `dumpsys gfxinfo` before interaction.
2. Scroll a long project list.
3. Scroll a 200+ turn conversation.
4. Expand/collapse Markdown, code, and tables.
5. Scroll image/document chips.

Pass:

- profile/release frame p95 stays within the stress-plan budget;
- no text overlap, chip overflow, or repeated rebuild jump is visible;
- memory returns toward baseline after idle.

## Execution Bundles

Keep implementation and validation bundles cohesive:

1. **Native chat bundle**: C2-C4 plus older-history C5 smoke.
2. **Refresh/power bundle**: C4, C9.1, C10.1, and request-rate evidence.
3. **File/artifact bundle**: C6-C7 plus C8 isolation.
4. **Release performance bundle**: C5, C10.1, C10.2 in profile/release mode.

Do not split every tap or callback into separate worker tasks. A worker owns a
bundle, produces one artifact directory, and one reviewer audits that artifact.

## Current Known Gaps

- No current P0/P1 local Android Emulator gap remains for the server-wide
  product baseline. C0-C10 have accepted real-project evidence indexed above
  and in [../history/evidence-index.md](../history/evidence-index.md).
- Physical-device and Tailnet/VPN recovery remain P2 hardening because local
  AVD recovery uses `adb reverse`.
- Release-mode user-origin upload with the real Android system picker is now
  covered for a `24 MiB` file on local AVD; remaining transfer hardening is
  physical-device/Tailnet rather than an emulator coverage gap.
- The exact native transcript source remains provider-specific; Codex is the
  accepted first provider implementation.
