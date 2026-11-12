# CCB Mobile Deep Test Compass Plan

Date: 2026-06-27
Status: Detailed execution design
Read with:
[app-comprehensive-test-program.md](app-comprehensive-test-program.md),
[app-real-avd-stress-casebook.md](app-real-avd-stress-casebook.md),
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md),
and
[local-avd-real-project-test-runbook.md](local-avd-real-project-test-runbook.md).

## Purpose

This document is the single compass for deep CCB Mobile validation. It is more
operational than the broad stress plan: each lane states what to run on the
Android Emulator, what source-side evidence must be captured, which metrics
matter, and what condition rejects the run.

The goal is to prove the real product:

- the phone connects to one server-wide CCB mobile gateway;
- the first page lists all mounted/reachable CCB projects on the server;
- destructive or exploratory tests use disposable projects under
  `/home/bfly/yunwei/test_ccb2`;
- selected-agent chat mirrors the same server/desktop pane;
- phone input is pane-equivalent and never wraps `ccb ask`;
- user files and backend agent artifacts can be downloaded on the phone;
- refresh is operation-driven, not a blind fixed terminal-history poll;
- performance, power, and recovery behavior are good enough for a real app.

## Operating Rules

These rules are fail-fast. If any rule is broken, the evidence packet is not a
valid real-backend packet.

1. Use a real server-wide gateway, never app fake/demo, for P0/P1 evidence.
2. Use `adb reverse` to a loopback-only gateway. Do not expose the gateway on
   `0.0.0.0` and do not use Funnel as a substitute for local AVD validation.
3. Before sending or uploading, prove the selected project root is under
   `/home/bfly/yunwei/test_ccb2` and the selected agent has real pane evidence.
4. Ordinary phone send must appear in the selected pane exactly as typed:
   no `CCB_REQ_ID`, no `mobile_gateway`, no ask/job envelope, no hidden device
   prefix.
5. Ordinary chat bubbles must hide internal provenance labels:
   `completion_snapshot`, `provider_native`, `jobs.jsonl`, `project_view`,
   request ids, and job ids.
6. Do not submit the same evidence packet to several reviewers as independent
   evidence. One worker owns one packet and one reviewer audits that packet.
7. Stop on the first P0 failure. Collect evidence instead of continuing a
   pressure lane against a known-broken state.

## System Under Test

Every packet records the full topology:

| Layer | Required Record |
| :--- | :--- |
| App | commit, dirty status, build mode, package id, install time |
| Device | emulator id, Android API, `adb devices -l`, `adb reverse --list` |
| Gateway | URL, route provider, host id, state directory, process pid |
| Source | CCB source worktree path, commit, dirty status, provider |
| Projects | `/v1/projects` JSON, healthy/unreachable counts, selected roots |
| Agent | agent name, namespace epoch, tmux socket/session/window/pane id |
| Transcript | cursor/page metadata, source transcript path or provider evidence |
| Files | corpus manifest, uploaded ids, downloaded paths, SHA256 values |

## Execution Waves

Run the waves in order. Later waves require the earlier wave to be green in
the same environment or explicitly waived by the lead.

| Wave | Cadence | Build | Purpose | Blocks |
| :--- | :--- | :--- | :--- | :--- |
| W0 Compass | before every manual session | debug | prove gateway/app/project identity and no fatal instability | all |
| W1 Functional Smoke | after chat/source routing changes | debug | server-wide list, open project, send, reply, desktop-origin sync | file/history |
| W2 File Smoke | after file/artifact changes | debug | image/doc upload, backend artifact download, hash checks | file pressure |
| W3 Recovery Smoke | after gateway/auth/lifecycle changes | debug | reverse/gateway/ccbd/revoke/background recovery | soak |
| W4 Rendering Pressure | before release milestones | profile | 200+ history, Markdown, chips, scroll stability | release |
| W5 Power Soak | before release candidate | profile/release | 30-minute foreground idle/low-touch stability | user handoff |
| W6 Manual Handoff | after W0-W3 pass | current candidate | let the user test prepared real projects | product signoff |

## Next Worker Packets

Use these packets for the next real-AVD work. Each packet is intentionally
larger than a micro-test and should be implemented, run, and reviewed as one
cohesive evidence unit.

### P-A Live Artifact Packet

Purpose: close the biggest file/download gap by proving the phone can download
files created by the selected provider during the same live run.

Scope:

- W0 preflight plus one disposable `test_ccb2` project with real pane
  evidence;
- prompt the selected agent to create a deterministic Markdown report and a
  deterministic small binary/image-like artifact when provider tooling allows;
- verify source-side artifact identity, artifact scope, and hash/content;
- refresh the phone timeline, download every new artifact, and verify Android
  saved files;
- restart the app and repeat the download from history.

Review focus:

- no seeded artifact is counted as provider-generated;
- no raw host filesystem path leaks into the phone UI or public URL;
- artifact ids are scoped to the selected project and agent;
- repeated download reuses the same artifact identity.

### P-B 200+ Mixed-History Profile Packet

Purpose: prove the timeline can render real product history without jump,
overwrite, or provenance leakage.

Scope:

- profile build, not debug-only;
- at least 200 turns with Markdown, code, duplicate short prompts, long
  paragraphs, image/document chips, and artifact links;
- newest open, upward pagination to oldest marker, refresh at top/middle/bottom,
  agent switch away/back, and expand/collapse while pages are loaded;
- `gfxinfo`, meminfo, screenshots, UI dumps, and source transcript cursor logs.

Review focus:

- older pages prepend and never replace newer content;
- scroll position and expanded/collapsed state are stable;
- ordinary chat hides `completion_snapshot`, `provider_native`, job/request ids,
  and provider cache names;
- frame p95 and PSS delta meet profile gates.

### P-C File Error, Retry, And Restart Packet

Purpose: make file transfer robust enough for real users.

Scope:

- upload image-only, text+document, multiple attachments, near-limit,
  oversized, unsupported, and canceled picker cases;
- remove `adb reverse` during one send and verify retry is explicit and
  non-duplicating;
- force-stop/relaunch the app and restart the gateway on the same state dir;
- redownload accepted files and verify hashes.

Review focus:

- failed attachments do not leave stuck composer state;
- accepted files remain usable from history after restart;
- file state does not leak across agents or projects;
- exact prompt and attachment retry reach the selected pane at most once.

### P-D Refresh And New-Message Packet

Purpose: prove the operation-driven refresh model under real reading behavior.

Scope:

- selected-agent idle audit with no touch;
- desktop-origin message while phone is pinned to newest;
- desktop-origin message while phone is scrolled away from newest;
- explicit refresh, scroll-boundary refresh, background/resume refresh, and
  home project-list refresh;
- request counters and screenshots before/after every refresh.

Review focus:

- no blind 3-second conversation/terminal-history loop;
- no visible card jumping or repeated expand/collapse;
- scrolled-away user gets a new-message affordance instead of a forced jump;
- home refresh and selected-agent refresh are distinct user-visible actions.

### P-E Profile Recovery And Soak Packet

Purpose: turn debug recovery smokes into release-readiness evidence.

Scope:

- profile or release build;
- repeat reverse loss, gateway restart, project ccbd restart, revoke/re-pair,
  background/resume during refresh, and background/resume during download;
- 30-minute foreground low-touch soak with one project-list refresh, one
  selected-agent refresh, one agent switch, one send, and one file download;
- collect request counts, meminfo, top, power, batterystats, gfxinfo, logcat,
  gateway tail, and source project tail.

Review focus:

- fail-closed behavior without reinstall or clear-data;
- no hidden input replay;
- no wake lock, ANR, OOM, request storm, or unbounded PSS growth;
- post-soak send and download still work.

## Case Lanes

### D0 Environment Binding

Goal: prove the app is bound to the intended real gateway.

Actions:

1. Start or select one server-wide gateway on `127.0.0.1:<port>`.
2. Set `adb reverse tcp:<port> tcp:<port>`.
3. Clear ambiguity from older profiles or record why the active profile is the
   intended one.
4. Query `/v1/health` and `/v1/projects`.
5. Open the app and capture screenshot/UI dump.

Metrics:

- `/v1/projects` p50/p95/max over five samples;
- cold app start to first route;
- project-list first render;
- logcat fatal/ANR/OOM count;
- app PSS at home.

Reject if:

- the phone shows fake/demo when a server profile should be active;
- the app cannot be tied to the gateway URL and host id;
- one stale project breaks the whole project list.

### D1 Server-Wide Project Discovery

Goal: prove the home page lists all mounted/reachable server projects.

Actions:

1. Use the home refresh button.
2. Compare visible projects with `/v1/projects`.
3. Open `test_ccb2_alpha`, go back, open `test_ccb2_beta`.
4. Include at least one stale/unreachable registry entry when practical.

Metrics:

- refresh p50/p95/max;
- open-project p50/p95;
- healthy and unreachable counts;
- UI visible row count and screenshot.

Reject if:

- only one current project is available;
- project ids are replaced by host ids or route-provider ids;
- a stale project prevents healthy projects from loading.

### D2 Selected-Agent Pane Identity

Goal: prove the app timeline is the selected pane, not stale job history.

Actions:

1. Open a disposable test project.
2. Select `mobile_probe` and record pane evidence.
3. Capture desktop pane tail and phone timeline screenshot.
4. Switch to `mobile_peer` and repeat.
5. Switch back and verify transcript/draft isolation.

Metrics:

- agent switch p50/p95;
- newest visible source marker age;
- count of forbidden provenance labels in UI dump.

Reject if:

- newest phone content does not correspond to the selected pane;
- agent switch leaks another agent's transcript;
- UI shows `completion_snapshot`, `provider_native`, job ids, or request ids
  in ordinary chat.

### D3 Pane-Equivalent Send And Reply

Goal: prove phone input equals direct pane typing and real provider output is
shown.

Actions:

1. Send `mobile-turn-a:<timestamp>` from the phone.
2. Inspect the desktop pane before waiting for reply.
3. Wait for provider reply through bounded active-send refresh or manual
   refresh.
4. Send duplicate text, such as `hi` twice.
5. Repeat in a second project or agent.

Metrics:

- tap to local user bubble;
- tap to desktop pane input visible;
- tap to first provider reply visible;
- duplicate-turn ordering and count;
- source jobs count for the marker.

Reject if:

- pane receives `CCB_REQ_ID`, `mobile_gateway`, or an ask wrapper;
- phone send creates a normal `ccb ask` job;
- duplicate text collapses into one turn;
- reply is a fake echo instead of provider/pane output.

### D4 Desktop-Origin Dynamic Sync

Goal: prove the phone can load desktop-entered pane conversation.

Actions:

1. Type `desktop-origin:<timestamp>` directly into the desktop pane.
2. Leave the phone untouched for 30 seconds.
3. Trigger explicit selected-agent refresh.
4. Repeat while scrolled away from newest.

Metrics:

- idle conversation/terminal request count;
- refresh to marker visible latency;
- scroll-position delta;
- new-message affordance count.

Reject if:

- the app needs project reopen to see desktop-origin content;
- idle shows a blind fixed request loop;
- timeline jumps while the user is reading older content.

### D5 Older History And Mixed Rendering

Goal: prove dynamic upward loading and heavy rendering remain stable.

Dataset:

- at least 200 turns;
- Markdown headings, lists, tables, links, code blocks, long paragraphs;
- duplicate short prompts;
- image/document chips;
- backend artifact links.

Actions:

1. Open newest page and record first render.
2. Scroll upward until the oldest marker appears.
3. Refresh at top, middle, and bottom positions.
4. Expand/collapse long items while pages are loaded.
5. Switch agents and return.

Metrics:

- newest page render p50/p95;
- older page load p50/p95;
- frame p50/p95 in profile mode;
- PSS delta after loading all pages;
- layout overflow count.

Reject if:

- older pages reorder or replace newer turns;
- scroll position is lost after prepend;
- app shows stale ask/job records as ordinary conversation;
- frame or memory budgets fail in profile mode.

### D6 User File Upload

Goal: prove user-selected images/documents flow through the selected-agent
route.

Corpus:

- `small.md`, `small.txt`, `document.pdf`, `image.png`, `image.jpg`;
- `near-limit.bin`;
- `oversized.bin`;
- `unsupported.xyz` when unsupported-type handling is enabled.

Actions:

1. Attach image with empty text and send.
2. Attach Markdown document with text and send.
3. Attach multiple files up to the product limit.
4. Test near-limit, oversized, unsupported, and cancel flows.
5. Restart the app and download accepted files from history.

Metrics:

- picker open latency;
- selected file to tray/chip visible;
- upload accepted latency;
- download saved latency;
- source/download SHA256;
- memory delta after image preview.

Reject if:

- host filesystem path leaks to the phone;
- failed attachment leaves composer stuck;
- file state leaks across agents/projects;
- downloaded hash differs from the uploaded/source object.

### D7 Backend Artifact Download

Goal: prove files generated by agents can be downloaded on the phone.

Actions:

1. Ask the agent to generate a deterministic Markdown report.
2. Ask for a deterministic image/binary artifact when tool support exists.
3. Refresh if needed and verify artifact chips/links in the correct turn.
4. Download, open, and hash saved files.
5. Restart app/gateway and download again from history.

Metrics:

- artifact generated to chip visible;
- download p50/p95;
- saved file size and SHA256;
- retry duration after transient failure.

Reject if:

- artifact belongs to another project/agent;
- raw server path is visible;
- artifact disappears after restart;
- failed download cannot be retried.

### D8 Recovery, Security, And Replay Guard

Goal: prove failures are visible, recoverable, and do not duplicate input.

Actions:

1. Remove/restore `adb reverse`.
2. Stop/restart server-wide gateway.
3. Stop/restart one project `ccbd`.
4. Revoke paired device, try protected routes, then re-pair.
5. Background/resume during refresh and file download.
6. Type a draft with attachment, fail send, restore network, retry once.

Metrics:

- time to visible failure;
- time to recovery after restore;
- protected-route success count after revoke;
- duplicate pane input replay count;
- preserved draft/file count.

Reject if:

- protected routes succeed after revoke;
- app needs reinstall/clear-data to recover from normal gateway restart;
- retry silently resends input without explicit user action;
- project A failure breaks project B.

### D9 Refresh, Idle, Power, And Performance

Goal: prove the app remains usable and quiet during idle and long sessions.

Actions:

1. Run 3-minute debug idle request audit.
2. Run 30-minute profile/release foreground soak.
3. During soak, perform low-frequency manual refresh, agent switch, and one
   file download.
4. Pull `meminfo`, `top`, `dumpsys power`, `batterystats`, `gfxinfo`, and
   logcat.

Metrics:

- idle requests/minute by endpoint;
- CPU idle and interaction windows;
- PSS baseline/mid/end/post-idle;
- wake-lock count;
- frame p50/p95 during list and chat scroll;
- logcat FATAL/ANR/OOM count.

Reject if:

- selected-agent page polls conversation/terminal history in a blind loop;
- app-held wake locks are nonzero at idle;
- PSS growth exceeds the budget and does not settle;
- frame p95 misses the release gate for two consecutive samples;
- UI visibly flickers, jumps, or repeatedly expands/collapses cards.

## Budgets

Initial budgets stay conservative until profile/release baselines are broader.

| Metric | Debug Diagnostic | Profile/Release Gate |
| :--- | :--- | :--- |
| Project list refresh, <= 50 projects | p95 <= 2000 ms | p95 <= 1000 ms |
| Open project to selected-agent visible | p95 <= 3000 ms | p95 <= 1500 ms |
| Agent switch ready | p95 <= 2000 ms | p95 <= 800 ms |
| Manual conversation refresh unchanged | p95 <= 1500 ms | p95 <= 700 ms |
| Local send bubble visible | p95 <= 500 ms | p95 <= 250 ms |
| Pane input visible | p95 <= 1500 ms | p95 <= 800 ms |
| Older history page load | p95 <= 2500 ms | p95 <= 1200 ms |
| File tray/chip visible | p95 <= 1500 ms | p95 <= 800 ms |
| File upload accepted, <= 5 MB | p95 <= 5000 ms | p95 <= 3000 ms |
| File download saved, <= 5 MB | p95 <= 5000 ms | p95 <= 3000 ms |
| Chat scroll frame p95 | record only | <= 32 ms |
| Idle CPU | <= 3 percent | <= 1 percent |
| Idle app-held wake locks | 0 expected | 0 required |
| Idle conversation/terminal requests | 0 expected debug target | <= 2/minute max |
| 30-minute PSS growth | <= 30 percent | <= 15 percent |

Budget misses must identify the likely owner:
`app-ui`, `app-transport`, `source-gateway`, `source-runtime`, `provider`, or
`environment`.

## Evidence Packet Shape

Every deep packet writes one artifact root:

```text
/tmp/ccb-mobile-deep-<timestamp>/
  summary.md
  summary.json
  commands.txt
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
  source-correlation/
  files/
```

`summary.json` must include:

```json
{
  "status": "ok|warn|blocked|fail",
  "wave": "W1 Functional Smoke",
  "case_ids": ["D2", "D3"],
  "first_failed_gate": null,
  "owner": null,
  "app_commit": "...",
  "source_commit": "...",
  "app_dirty": false,
  "source_dirty": false,
  "device_id": "emulator-5554",
  "gateway_url": "http://127.0.0.1:19000",
  "project_roots": ["/home/bfly/yunwei/test_ccb2/..."],
  "fake_or_demo_used": false,
  "real_pane_verified": true,
  "ccb_req_id_seen": false,
  "mobile_prefix_seen": false,
  "provenance_label_seen": false,
  "blind_polling_seen": false,
  "logcat_fatal_anr_oom": false
}
```

Reviewers reject any P0/P1 packet where `fake_or_demo_used` is true,
`real_pane_verified` is false, or the selected project root is not under
`/home/bfly/yunwei/test_ccb2`.

## Automation Targets

The automation should grow in cohesive packages:

1. `mobile_app_compass_test`: D0/D1 metrics and app identity.
2. `mobile_server_wide_emulator_smoke`: fixture setup, gateway, adb reverse,
   install, debug profile seed, and integration-test orchestration.
3. Native conversation smoke: D2/D3 phone send/reply and no ask metadata.
4. Desktop-origin sync smoke: D4 plus no-idle-request audit.
5. File/artifact smoke: D6/D7 with on-device SHA256 checks.
6. Recovery smoke: D8 for reverse, gateway, ccbd, revoke, re-pair,
   background/resume, and replay guard.
7. Profile/release harness: D5/D9 frame, memory, CPU, wake-lock, and 30-minute
   soak.
8. Manual handoff script: opens prepared emulator on real `test_ccb2` projects
   with home refresh and selected-agent refresh ready for the user.

## Current Next Runs

Prioritize these missing packets:

1. **P-A live provider artifact packet**: ask the real provider to create
   deterministic files in a disposable project, surface them in the phone
   timeline, download them, and verify Android saved-file hashes.
2. **P-B 200+ mixed-history profile packet**: profile-mode page load, upward
   pagination, scroll stability, frame/memory, and label-hiding proof.
3. **P-C file error/retry/restart packet**: oversized/unsupported rejection,
   retry after gateway-path loss, restart persistence, and redownload hashes.
4. **P-D refresh/new-message packet**: idle no-poll audit, explicit refresh,
   scrolled-away new-message behavior, background/resume refresh, and home
   refresh.
5. **P-E profile recovery/soak packet**: profile or release recovery pass plus
   30-minute request-count, CPU, wake-lock, PSS, gfxinfo, and post-soak
   send/download sanity.

Do not run W4/W5 against a failing W1/W2 environment. Re-run W0 first if the
emulator, gateway, source worktree, app install, or paired profile changed.
