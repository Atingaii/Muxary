# CCB Mobile Comprehensive Test Program

Date: 2026-06-26
Status: Detailed test program design
Read with:
[app-deep-test-compass-plan.md](app-deep-test-compass-plan.md),
[app-stress-and-performance-test-plan.md](app-stress-and-performance-test-plan.md),
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md),
[app-real-avd-stress-casebook.md](app-real-avd-stress-casebook.md),
and
[local-avd-real-project-test-runbook.md](local-avd-real-project-test-runbook.md).

## Purpose

This document is the top-level execution program for deep CCB Mobile testing.
It turns the current acceptance matrix into coherent worker-sized test
packages, required metrics, artifact schemas, and rejection rules.

For the operational lane-by-lane checklist, budgets, required artifact fields,
and the current prioritized missing runs, use
[app-deep-test-compass-plan.md](app-deep-test-compass-plan.md). This document
stays at package/program level; the compass is the detailed execution map.

The target is not a fake mobile demo. The target is a phone UI that can connect
to the real server-wide CCB mobile gateway, list every mounted CCB project on
the host, open disposable real projects under `/home/bfly/yunwei/test_ccb2`,
mirror the selected CCB agent pane, send ordinary input exactly like direct
pane typing, transfer files, download agent-generated artifacts, and remain
stable under realistic use.

## Test Authority

Use this authority order when evidence conflicts:

1. User-visible behavior on a real Android Emulator connected to the intended
   server-wide gateway.
2. Source-side CCB runtime evidence: project root, project id, namespace epoch,
   pane id, tmux socket/session/window, provider-native transcript, and gateway
   request logs.
3. App-side screenshots, UI dumps, logcat, frame/memory/power metrics, and
   integration-test output.
4. Unit/widget tests for isolated boundaries.

Fake/local repositories are allowed for unit and widget regressions only. They
cannot close P0/P1 real-backend gates.

## Global Invariants

Every P0/P1 run must prove these before it can count:

- app is installed from the app commit under test;
- app is connected to one known server-wide gateway, not a stale profile;
- gateway is loopback-only on the host and reachable through `adb reverse`;
- project list is server-wide and includes disposable `test_ccb2` projects;
- selected send/file/recovery targets are under `/home/bfly/yunwei/test_ccb2`;
- selected agent has real pane evidence, not a fake-only runtime;
- ordinary mobile send creates no `ccb ask` job, no `CCB_REQ_ID`, and no
  visible mobile device prefix;
- ordinary chat bubbles hide internal source labels such as
  `completion_snapshot`, `provider_native`, `jobs.jsonl`, `project_view`, job
  ids, and request ids;
- refresh is operation-driven and not an idle 3-second terminal-history poll;
- artifacts include clean pass/fail status and first failed gate.

## Test Packages

Workers should own packages, not tiny callbacks. Each package produces one
artifact root and one review packet.

| Package | Scope | Primary Owner | Required Reviewer Focus |
| :--- | :--- | :--- | :--- |
| T0 Environment Compass | gateway identity, app binding, project list, idle safety | mobile app engineer | fake/demo rejection, gateway/profile identity, no logcat fatal |
| T1 Pane Chat Correctness | selected pane identity, phone send, provider reply, desktop-origin sync | mobile app engineer | no ask/job path, no metadata injection, correct agent/project |
| T2 History Rendering | 200+ native turns, pagination, scroll preservation, Markdown/layout pressure | frontend engineer + mobile app engineer | no stale-history overwrite, frame/memory budgets, no visual jump |
| T3 File And Artifact Flow | image/document upload, backend artifact mapping/download, hash checks | mobile app engineer | authenticated ids, no host path leak, retry/error states |
| T4 Recovery And Security | `adb reverse`, gateway restart, ccbd restart, revoke/re-pair, background/resume | mobile app engineer | fail-closed behavior, no duplicate pane input replay |
| T5 Performance And Power | profile/release frame timing, CPU, PSS, wake locks, request rates, soak | mobile app engineer | sustained stability and no idle polling storm |
| T6 UX Manual Review | human walkthrough on a prepared emulator and real test project | lead + user | visible correctness, controls, discoverability, no hidden demo state |

Do not submit the same review packet to multiple reviewers as independent
evidence. Assign one reviewer to a packet unless the user explicitly asks for
parallel review.

## Expanded Execution Detail

The remaining validation should be run as larger, product-shaped packets. A
packet should start by proving identity, then perform the user workflow, then
collect correlation and metrics before any cleanup. Do not split the packet
into one task per tap, and do not let a worker continue a pressure run after a
P0 gate has already failed.

| Packet | Required End-To-End Story | Must Include | Reject Immediately If |
| :--- | :--- | :--- | :--- |
| E1 Real Gateway And Project List | fresh app install or known profile opens the server-wide gateway and refreshes all mounted projects | `/v1/projects` samples, home screenshot, project-list refresh timing, stale-entry degradation | app shows fake/demo, only one current project appears, or selected profile cannot be tied to the gateway |
| E2 Native Pane Conversation | user opens `test_ccb2_alpha` and `test_ccb2_beta`, sends to two agents, sees provider replies, and desktop-origin input syncs back | pane evidence, source transcript excerpts, no jobs match, screenshots before/after refresh | `CCB_REQ_ID`, `mobile_gateway`, stale job history, wrong project, or wrong agent appears |
| E3 Refresh Semantics | app idles quietly, then explicit refresh, scroll-boundary refresh, and resume refresh update the timeline without jumps | endpoint request counters, before/after screenshots, scroll-position deltas, CPU/PSS/wake-lock samples | blind 3-second polling, card flicker, stale records replacing newer turns, or visible expand/collapse loops |
| E4 File And Artifact Flow | user uploads image/document, downloads accepted files, then downloads provider-generated artifacts from history | file corpus manifest, opaque ids, Android saved paths, SHA256 before/after, retry screenshots | raw host path leak, hash mismatch, stuck upload/download state, or artifact crosses project/agent |
| E5 Long History Rendering | profile build opens 200+ mixed turns, loads older pages upward, renders Markdown/chips/artifacts, and preserves reading position | page timings, frame/gfxinfo, memory samples, UI dumps, overflow scan, oldest/newest markers | older pages reorder, scroll position is lost, internal labels appear, or frame/memory gate fails |
| E6 Recovery And Security | reverse/gateway/ccbd/revoke/background failures are induced and recovered without reinstall or hidden replay | failure markers, retry screenshots, old-token 401 evidence, duplicate-send counts, preserved draft/file proof | protected route succeeds after revoke, input replays silently, app needs clear-data, or project A failure breaks project B |
| E7 Power And Soak | profile/release app stays open for 30 minutes with low-touch actions and ends with send/download sanity | request counts, top/meminfo/power/batterystats/gfxinfo/logcat, post-soak screenshot | wake lock, FATAL/ANR/OOM, request storm, unbounded PSS growth, or post-soak send/download failure |

### Sampling Cadence

Use the same cadence across packets so results can be compared:

- record gateway request counters at packet start, after every intentional
  user action, and at packet end;
- sample `adb shell dumpsys meminfo io.ccb.mobile.ccb_mobile` and
  `adb shell top -b -n 1` at baseline, midpoint, end, and post-idle recovery;
- collect `adb shell dumpsys power` at baseline and end for every packet that
  waits more than 60 seconds;
- collect `adb shell dumpsys gfxinfo io.ccb.mobile.ccb_mobile framestats`
  before and after scripted scroll or long-history rendering;
- capture screenshots and UI dumps for the home page, selected project,
  selected agent before action, after action, and first failure;
- write source-side correlation immediately after the phone action, before a
  provider reply can obscure whether the pane received exact input.

### Response-Speed Measurements

Every E1-E5 packet must record p50/p95/max where the action repeats at least
five times, otherwise record single-run latency with the build mode:

- project list refresh;
- open project;
- switch agent;
- selected-agent explicit refresh with no changes;
- selected-agent explicit refresh with new desktop-origin content;
- phone send tap to local bubble;
- phone send tap to source pane input visible;
- phone send tap to first provider reply visible;
- file picker open to preview tray visible;
- accepted file/artifact tap to Android saved path visible;
- older-history page request to first visible older marker.

Provider response speed is recorded but is not an app performance failure by
itself. The packet must separate provider latency from app transport/render
latency.

### Data Quality Gates

Each packet must state whether it used live provider behavior, seeded native
transcript data, or app fake data. Only live provider or controlled native
transcript fixtures can close real-backend gates; app fake data can only close
unit/widget regressions. For file/artifact work, mark each item as:

- `user_upload`: selected on Android and sent by the app;
- `source_seeded`: inserted by the harness for deterministic smoke coverage;
- `provider_generated`: created by the selected provider/agent during the run.

Release acceptance for backend artifacts requires at least one
`provider_generated` text artifact and one binary/image-like artifact when the
provider/tooling can create it. If the provider cannot create a binary artifact
in the environment, the packet must record a provider/environment block rather
than count seeded data as live proof.

## Capability Definition Of Done

Each capability is accepted only when it has both user-visible proof and
source-side correlation. A passing widget or unit test is not enough for these
capabilities.

| Capability | Minimum Real-AVD Proof | Required Correlation | Release-Level Proof |
| :--- | :--- | :--- | :--- |
| Server-wide project discovery | home page lists multiple mounted projects, refresh works, stale entries degrade | `/v1/projects` sample, gateway log, project roots | profile startup/open timings and 50+ project budget |
| Selected-agent identity | app timeline matches selected pane for two agents | pane id, tmux target, namespace epoch, provider/session marker | agent switching under long-history pressure |
| Phone send | desktop pane receives exact text and app shows provider reply | pane tail before reply, no jobs match, no `CCB_REQ_ID` | 20+ turns across two projects, duplicate text preserved |
| Desktop-origin sync | direct pane input appears after explicit refresh | host input marker and app UI dump | scrolled-away new-message affordance and no jump |
| Older history | upward loading reaches old markers | transcript cursor/page logs | 200+ mixed turns with profile frame/memory metrics |
| User file upload | image/document attach, send, chip, download/hash | gateway file ids and SHA256 | near-limit, oversized, unsupported, restart persistence |
| Backend artifact download | agent-created artifact appears and saves locally | artifact id, source file hash, downloaded hash | live provider-generated text/image artifacts plus retry |
| Recovery | reverse/gateway/ccbd/revoke/background recover or fail closed | host event markers, gateway logs, app errors | no duplicate input replay and draft/file preservation |
| Idle/power | 3-minute no-touch window has no visible jumping | endpoint request counts, CPU, PSS, wake locks | 30-minute profile/release soak |

## Worker Evidence Packet

Every worker-owned package must return one evidence packet, not scattered
screenshots:

```text
result/
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
  logcat.txt
  gateway.log.tail
  source-project.log.tail
  screenshots/
  ui/
  source-correlation/
  files/
```

`summary.md` should answer these in order:

1. What app/source commits were tested and were the worktrees clean?
2. Which gateway URL, host id, state dir, and route provider were used?
3. Which disposable project roots and agents were touched?
4. Which cases passed, warned, blocked, or failed?
5. What was the first failed gate and likely owner?
6. Which screenshots, logs, and source-side records prove the result?
7. What residual risks remain?

`summary.json` is the machine-readable authority for dashboards and must include
at least:

```json
{
  "status": "ok|warn|blocked|fail",
  "package": "T2 Pane Chat Correctness",
  "case_ids": ["C2.1", "C3.1"],
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

Reviewers should inspect `summary.json` first. If it says `fake_or_demo_used:
true` for a P0/P1 case, reject the packet before reading screenshots.

## Execution Board

Use this board to keep work cohesive. Move one package at a time through
`Ready -> Running -> Review -> Accepted`; do not fork identical review packets
to multiple reviewers.

| Package | Current Status | Next Evidence Needed | Blocks |
| :--- | :--- | :--- | :--- |
| T0 Environment Compass | smoke evidence exists | keep as preflight before every run | all later packages |
| T1 Pane Chat Correctness | smoke evidence exists | longer multi-turn, duplicate-text, scrolled-away sync | T2/T3 correctness claims |
| T2 History Rendering | partial | 200+ mixed-content profile run | release rendering gate |
| T3 File And Artifact Flow | partial | live provider artifacts, retry/error, restart persistence | file release gate |
| T4 Recovery And Security | smoke evidence exists | profile/release recovery pressure | auth/reliability gate |
| T5 Performance And Power | partial; debug idle request-rate accepted | profile 30-minute soak with CPU, memory, wake locks, request counts, and frames | release readiness |
| T6 UX Manual Review | pending | prepared emulator plus accepted T0-T4 smoke evidence | user handoff |

The next useful work is whichever earliest package can produce missing evidence
without relying on a known failing prerequisite. For example, do not run file
pressure if selected-agent identity or pane-equivalent send is failing in the
same environment.

## Execution Ladder

Run stages in order. A failed stage blocks later pressure stages until fixed or
explicitly waived as out of scope.

### Stage 0: Preflight And Binding

Goal: prove the app is bound to the intended gateway.

Actions:

- record app and source commits plus dirty status;
- record emulator id, Android API, package version, and build mode;
- start one server-wide gateway on `127.0.0.1:<port>`;
- set `adb reverse tcp:<port> tcp:<port>`;
- query `/v1/health` and `/v1/projects`;
- open the app and verify the same gateway/profile is active;
- capture screenshot and UI dump.

Metrics:

- `/v1/projects` p50/p95/max for five samples;
- app foreground startup to first visible route;
- project-list refresh latency;
- logcat fatal/ANR/OOM count.

Reject if:

- app shows only demo/fake project state;
- multiple gateways exist and the selected profile cannot be tied to the test
  gateway;
- any stale project makes the whole project list fail.

### Stage 1: Server-Wide Navigation

Goal: prove the phone can discover and open real projects.

Actions:

- use the home refresh button;
- compare visible projects to `/v1/projects`;
- open `test_ccb2_alpha`, return, open `test_ccb2_beta`;
- switch between `mobile_probe` and `mobile_peer`;
- capture timings and screenshots.

Metrics:

- refresh p50/p95;
- open-project p50/p95;
- agent switch p50/p95;
- healthy/unreachable project counts.

Reject if:

- project ids drift to host ids or route-provider ids;
- selected project root is outside `/home/bfly/yunwei/test_ccb2` for send/file
  tests;
- agent switch leaks another agent's transcript.

### Stage 2: Pane-Equivalent Conversation

Goal: prove the mobile chat surface is the selected pane renderer and input.

Actions:

- record selected agent pane evidence before send;
- send deterministic text from the phone;
- inspect the desktop pane before waiting for provider reply;
- wait for provider reply through allowed active-send refresh/backoff;
- type a desktop-origin marker directly in the pane and refresh the app;
- repeat across two projects and two agents;
- send duplicate text such as `hi` twice.

Metrics:

- send tap to local user bubble;
- send tap to desktop pane marker;
- send tap to first provider reply visible;
- explicit refresh to desktop-origin marker visible;
- duplicate-turn ordering correctness.

Reject if:

- pane receives `CCB_REQ_ID`, a mobile device label, or an ask prompt wrapper;
- phone bubble displays internal provenance labels;
- `jobs.jsonl` or stale completion records replace newer native transcript;
- duplicate sends collapse into one turn.

### Stage 3: Refresh Semantics

Goal: prove refresh is user/operation driven and visually stable.

Actions:

- idle on selected-agent page for 3 minutes with no touch;
- record gateway endpoint counts during idle;
- scroll away from newest, then create a desktop-origin turn;
- trigger explicit refresh and verify new-message behavior;
- refresh at bottom, middle, and top positions;
- background/resume the app and refresh.

Metrics:

- idle requests/minute by endpoint;
- CPU and PSS during idle;
- wake-lock state;
- refresh p50/p95;
- scroll-position delta after unchanged refresh;
- number of visible expand/collapse flips during idle.

Reject if:

- terminal-history or conversation endpoints are called on an idle fixed
  3-second loop;
- visible timeline jumps while idle;
- refresh prepends/appends duplicate blocks or stale blocks.

### Stage 4: Older History And Rendering Pressure

Goal: prove long provider-native conversation history renders and paginates.

Dataset:

- at least 200 turns;
- Markdown headings, lists, tables, code blocks, links, math-like text, and
  long paragraphs;
- duplicate short prompts;
- image/document attachment chips;
- backend artifact links;
- mixed user/assistant turns for at least two agents.

Actions:

- open newest page and measure first render;
- scroll upward until oldest marker appears;
- refresh while at top, middle, and bottom;
- expand/collapse long items while pages are loading;
- switch agents and return.

Metrics:

- newest page API and UI render latency;
- older page API and UI render latency;
- total time and drag count to oldest marker;
- frame p50/p95 in profile mode;
- PSS delta after all pages loaded;
- Markdown/layout overflow count.

Reject if:

- older pages reorder or replace current newest turns;
- scroll position is not preserved after prepend;
- internal source labels become visible in ordinary chat;
- frame p95 or memory growth misses the release budget.

### Stage 5: User File Upload

Goal: prove images and documents can be sent through the selected-agent path.

Corpus:

- `small.md` and `small.txt`, <= 20 KB;
- `document.pdf`, 1-5 MB;
- `image.png` and `image.jpg`, 1-5 MB;
- `near-limit.bin`, just below the accepted size limit;
- `oversized.bin`, above the accepted limit;
- `unsupported.xyz`, if unsupported-type handling is exposed.

Actions:

- attach image with empty text and send;
- attach Markdown document with text and send;
- attach multiple files up to the per-message limit;
- test near-limit, oversized, and unsupported files;
- switch agent/project and verify draft/file isolation;
- download each accepted attachment from history.

Metrics:

- picker open latency;
- file selected to preview visible;
- upload accepted latency;
- conversation chip visible latency;
- download saved latency;
- SHA256 before upload and after download;
- memory delta after image preview.

Reject if:

- accepted file exposes a host-local path;
- upload/download uses unauthenticated public paths;
- failed attachment leaves composer stuck;
- file state leaks across agents or projects.

### Stage 6: Backend Artifact Download

Goal: prove files generated by CCB agents can be downloaded to the phone.

Actions:

- seed or generate a deterministic text artifact and image artifact from the
  selected agent;
- verify artifact link/chip appears in the correct turn;
- download the artifact;
- open or hash the saved file;
- restart the app and download from history again;
- switch project and confirm artifact isolation.

Metrics:

- artifact visible latency;
- download p50/p95;
- saved file size and SHA256;
- failed-open snackbar/error path;
- retry duration after transient gateway failure.

Reject if:

- artifact belongs to another project or agent;
- phone receives raw server filesystem paths;
- artifact disappears after app restart;
- failed download cannot be retried.

### Stage 7: Recovery And Security

Goal: prove gateway/network/auth failures are recoverable and fail closed.

Actions:

- remove `adb reverse`, then refresh project list and conversation;
- restore `adb reverse`;
- restart mobile gateway;
- restart one project `ccbd`;
- revoke paired device;
- try list, view, send, terminal, upload, and download after revoke;
- re-pair and reopen the same test project;
- background/resume during conversation refresh and file download.

Metrics:

- time to visible error;
- time to recovery after reverse/gateway restore;
- stale credential rejection count;
- duplicate terminal input replay count;
- preserved draft/attachment count.

Current evidence:

- 2026-06-26 `58c5f00` passed a real Android Emulator project-list and
  selected-agent reverse-loss/recovery smoke through gateway
  `127.0.0.1:19047`; the harness removed `adb reverse`, verified
  `Could not load projects`, restored the mapping, retried the project list,
  then repeated removal/restoration for selected-agent refresh and verified
  `Conversation refresh failed` cleared after explicit refresh. See
  [../history/local-avd-reverse-recovery-smoke-20260626.json](../history/local-avd-reverse-recovery-smoke-20260626.json).
- 2026-06-26 `b584d74` passed a real Android Emulator gateway-process
  restart smoke through gateway `127.0.0.1:19049`; the harness stopped and
  restarted the server-wide mobile gateway twice on the same listener/state
  directory, then verified project-list Retry and selected-agent explicit
  refresh recovery without clearing app data. See
  [../history/local-avd-gateway-restart-smoke-20260626.json](../history/local-avd-gateway-restart-smoke-20260626.json).
- 2026-06-26 `6372afb` passed a real Android Emulator project-ccbd restart
  smoke through gateway `127.0.0.1:19054`; the harness stopped and restarted
  only `test_ccb2_alpha`'s ccbd, then verified selected-agent explicit refresh
  retry recovered on the same open project without clearing app data. See
  [../history/local-avd-ccbd-restart-smoke-20260626.json](../history/local-avd-ccbd-restart-smoke-20260626.json).
- 2026-06-27 `952f2b2` passed a real Android Emulator replay-guard smoke
  through gateway `127.0.0.1:19070`; the harness removed `adb reverse` before
  a selected-agent send with an attachment, verified a retryable failed
  message preserved the prompt and file name, restored the reverse mapping,
  tapped Retry once, and verified source-side native transcript counts showed
  one user prompt and one provider reply with no jobs/ask metadata. See
  [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json).
- 2026-06-27 `a57fc92` passed a real Android Emulator revoke/re-pair smoke
  through gateway `127.0.0.1:19072`; the harness revoked the current paired
  device, verified the old token failed closed with HTTP `401`, then the app
  claimed a replacement pairing through Connection Details and recovered
  selected-agent refresh without clearing app data. See
  [../history/local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json).
- Stage 7 remains open for longer profile/release recovery pressure.

Reject if:

- protected routes succeed after revoke;
- send input is replayed silently after reconnect;
- app requires reinstall/clear-data to recover from normal gateway restart;
- project A failure breaks project B.

### Stage 8: Performance And Power Soak

Goal: prove the app can stay open without battery or stability issues.

Actions:

- run debug 10-minute soak after functional smoke;
- run profile 30-minute soak before release candidate;
- optionally run 2-hour extended soak;
- perform low-frequency manual project refresh, agent switch, and conversation
  refresh;
- end with one text send and one file download smoke.

Metrics:

- PSS/RSS baseline, midpoint, end, and post-idle recovery;
- CPU percent idle and during interactions;
- wake-lock count;
- request counts/minute by endpoint;
- logcat FATAL/ANR/OOM;
- `dumpsys gfxinfo` frame p50/p95 during scripted scroll;
- battery stats excerpt for the app package.

Reject if:

- app-held wake locks are nonzero while idle;
- idle endpoint requests exceed the budget without active send/refresh;
- memory grows beyond budget and does not settle;
- any ANR/OOM/FATAL appears.

## Evidence Schema

Every package writes:

```text
/tmp/ccb-mobile-avd-case-<timestamp>/
  summary.json
  environment.json
  gateway-health.json
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

`summary.json` must include:

```json
{
  "status": "ok|warn|blocked|fail",
  "package": "T3 File And Artifact Flow",
  "first_failed_gate": null,
  "owner": "app-ui|app-transport|source-gateway|source-runtime|provider|environment|null",
  "app_commit": "...",
  "source_commit": "...",
  "app_dirty": false,
  "source_dirty": false,
  "gateway_url": "http://127.0.0.1:19000",
  "fake_or_demo_used": false,
  "real_pane_verified": true,
  "ccb_req_id_seen": false,
  "blind_polling_seen": false
}
```

For file cases, add:

```json
{
  "files": [
    {
      "name": "small.md",
      "mime_type": "text/markdown",
      "size_bytes": 1234,
      "source_sha256": "...",
      "download_sha256": "...",
      "upload_ms": 123,
      "download_ms": 456,
      "result": "ok"
    }
  ]
}
```

For performance cases, add:

```json
{
  "performance": {
    "build_mode": "profile",
    "idle_requests_per_minute": 1.2,
    "chat_scroll_frame_p95_ms": 24.5,
    "pss_delta_percent": 4.1,
    "wake_locks": 0
  }
}
```

## Automation Targets

Keep automation incremental. Each target should be usable independently.

1. `mobile_app_compass_test`: environment, project list, logcat, memory,
   wake-lock, and request-count sampling.
2. `mobile_server_wide_emulator_smoke`: server-wide gateway setup, disposable
   `test_ccb2` projects, app install/seed, and integration-test execution.
3. `native_pane_gateway_smoke_test`: pane-equivalent send/reply correctness.
4. `native_pane_desktop_sync_smoke_test`: desktop-origin explicit refresh and
   no-idle-refresh window.
5. `server_wide_gateway_smoke_test`: project list, file/artifact, and
   older-history backfill.
6. New profile harness: install profile/release APK, run scripted scroll, pull
   `gfxinfo`, `meminfo`, `batterystats`, request counts, and screenshots.
7. New artifact verifier: compare local corpus SHA256, uploaded metadata,
   downloaded phone file, and gateway file metadata.

## Reviewer Gates

Reviewers should reject evidence packets when:

- packet does not identify app/source commits and dirty status;
- test used fake/demo while claiming real backend acceptance;
- test target was not under `/home/bfly/yunwei/test_ccb2` for destructive
  sends/files;
- selected agent pane evidence is missing;
- only phone screenshots are provided without source/gateway correlation;
- ordinary chat shows request ids, job ids, `mobile_gateway`, or provenance
  labels;
- the packet omits first failed gate after a failure;
- performance packet uses debug mode as a release performance gate;
- multiple reviewers received the same packet as if independent.

## Current Coverage And Remaining Gaps

Accepted evidence already covers early C0-C4 smoke and one C5 long-history
smoke:

- server-wide real gateway and project-list discovery have multiple accepted
  smoke records;
- pane-equivalent phone send/reply passed on disposable projects and agents;
- desktop-origin explicit refresh passed for a controlled marker;
- 56 provider-native Codex transcript turns loaded through the real gateway.
- profile scrolled-away desktop-origin sync passed on a real server-wide
  gateway: after loading mixed native backfill and scrolling away from bottom,
  explicit refresh surfaced a directly pane-injected marker through the
  new-message affordance, with source-side evidence showing no ask/job or
  `mobile_gateway` pollution.
- native selected-agent file/artifact smoke passed on a real server-wide
  gateway with `9` on-device SHA256-verified downloads, including text
  attachments, images, and seeded Codex native artifact links.
- debug idle metrics smoke passed on a real server-wide gateway:
  `180` seconds on an open selected-agent page produced `0`
  conversation/terminal-history requests before a post-window manual refresh,
  seven device metric samples, no PSS growth, no wake locks, and no
  FATAL/ANR/OOM.
- profile 30-minute idle soak passed on a real server-wide gateway:
  `1800` seconds on an open selected-agent page produced `0` total idle
  gateway requests, `0` conversation/terminal-history requests, `31` device
  metric samples, `0.52%` PSS growth, no wake locks, and no FATAL/ANR/OOM.

Still open before full product acceptance:

- 200+ mixed-content history pressure in profile/release mode;
- live provider-generated artifact creation during the run;
- oversized/unsupported file retry, app restart persistence, and
  profile/release file-performance metrics;
- release frame, memory, CPU, app-specific battery attribution, and release
  30-minute power soak.

## Next Execution Order

1. Finish the remaining T3 hardening cases: live provider-generated artifacts,
   oversized/unsupported retry, app restart persistence, and file-performance
   metrics.
2. Run T2 200+ mixed-history pressure in profile mode, because current C5
   evidence is only a 56-turn smoke.
3. Run T3/T8 multi-project isolation with files, because server-wide access is
   now the product default.
4. Run T4 recovery in profile/release mode, because debug smoke is broad but
   not release evidence.
5. Build the non-Flutter-Driver release harness, then rerun T5 as a release
   30-minute soak with request-count, frame, CPU, memory, and power evidence
   before any release candidate claim.

Do not keep expanding architecture extraction work until these test packages
have accepted evidence or a clear product blocker is found.
