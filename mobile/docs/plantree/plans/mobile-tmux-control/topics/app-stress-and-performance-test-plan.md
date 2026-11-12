# CCB Mobile App Stress And Performance Test Plan

Date: 2026-06-27
Status: Expanded execution design; automation in progress
Read when: validating CCB Mobile stability, response speed, memory, rendering,
file transfer, multi-project behavior, or release readiness.

Detailed execution matrix:
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md)
defines the local Android Emulator gate sequence, manual tester script,
refresh-model requirements, worker package boundaries, and reviewer rejection
checklist for this plan.
Use `tools/mobile_acceptance_evidence_audit.py` to verify that accepted matrix
and casebook evidence links still resolve, parse as JSON, and do not carry
obvious failure markers before claiming or handing off the current test state.

Detailed execution compass:
[app-deep-test-compass-plan.md](app-deep-test-compass-plan.md)
maps the same work into concrete real-AVD actions, metrics, evidence packet
fields, budgets, rejection gates, automation targets, and next missing runs.

Comprehensive execution program:
[app-comprehensive-test-program.md](app-comprehensive-test-program.md)
groups the stress work into worker-sized packages, required evidence schemas,
metric collection, reviewer gates, and the recommended next execution order.

Named case inventory:
[app-real-avd-stress-casebook.md](app-real-avd-stress-casebook.md)
assigns repeatable case ids for the real AVD gates, including environment
identity, server-wide project refresh, selected-pane identity, phone send,
desktop-origin sync, file/image upload, backend artifact download, recovery,
idle power, and rendering pressure.

Physical remote-device lane:
[physical-tailnet-device-validation-runbook.md](physical-tailnet-device-validation-runbook.md)
defines the remaining Android phone + Tailnet validation path. It starts with
the read-only `tools/mobile_physical_tailnet_preflight.py` gate, then verifies
server-wide pairing, pane-equivalent conversation, file/artifact transfer,
Tailnet recovery, and physical-device power/performance soak.
Use `tools/mobile_physical_tailnet_evidence_audit.py` on the collected
physical run artifact directory before accepting that lane.

Operator runbook:
[local-avd-real-project-test-runbook.md](local-avd-real-project-test-runbook.md)
defines the exact preflight, real pane-backed fixture gate, stage actions,
artifact layout, refresh/power checks, and reviewer rejection rules for each
local emulator run.

## Purpose

Define a complete pressure-test plan for CCB Mobile that starts gently and
ramps up only after the app, emulator, and local gateway are stable. The plan
must validate the real server-wide mobile path, not the fake/demo repository.

The app must remain usable during testing. Stress tests are not allowed to hide
bugs by constantly reinstalling the app, clearing state, or using fake
fixtures. Every accepted run records the selected gateway, project roots,
source/app commits, screenshots, logs, timing metrics, and stop conditions.

## Test Rule

All P0/P1 runs use a real server-wide gateway and real local CCB projects:

- start from `ccb install mobile` or the current equivalent server-wide local
  gateway;
- pair or debug-seed a real paired gateway profile;
- list all mounted/reachable server projects on the phone first page;
- open a test project under `/home/bfly/yunwei/test_ccb2`;
- do not validate against the fake `demo` project;
- do not send exploratory test messages into `/home/bfly/yunwei/ccb_source/mobile`
  unless the test explicitly targets the mobile repo itself.
- before any send/file test, verify the selected test agent has a real CCB
  pane target (`pane_id`, tmux session/window, namespace epoch, and non-fake
  or explicitly pane-backed provider evidence). A server-wide project list is
  not enough if the selected project is fake-only or has no valid agent pane.

Fake/local fixtures remain useful for unit and widget regressions, but they do
not satisfy this stress plan.

Operational refresh rule:

- the app must not rely on blind fixed 3-second terminal-history polling for
  ordinary idle chat sync;
- home/project list refresh must be explicit and visible;
- selected-agent conversation refresh should be triggered by open/resume,
  explicit refresh, scroll boundary, or bounded active-send state;
- idle evidence must record request rate, CPU, wake locks, and absence of
  visible timeline jumping.

## Current Compass Baseline

The first low-disruption compass run on 2026-06-26 used the current emulator,
real server-wide gateway `127.0.0.1:19011`, and real project
`test_ccb2_beta`. It intentionally avoided bulk sends, uploads, reinstall, and
batterystats reset.

Evidence:

- baseline artifact: `/tmp/ccb-mobile-stress-20260626155408/summary.json`;
- light UI artifact: `/tmp/ccb-mobile-stress-ui-20260626155648/summary.json`;
- 3-minute idle soak artifact: `/tmp/ccb-mobile-soak-20260626155755/summary.json`;
- controlled send artifact: `/tmp/ccb-mobile-send-20260626160154/summary.json`.

Observed baseline:

- `/v1/projects` listed `38` projects with `38` healthy entries;
- project list API p50 was `80.9 ms`, max `438.3 ms`;
- 60-second baseline PSS did not grow (`-74 KB` delta);
- 3-minute idle soak PSS did not grow (`-40 KB` delta);
- power dump reported `Wake Locks: size=0` and `mWakeLockSummary=0x0`;
- logcat had no FATAL, ANR, or OOM markers;
- 180-second selected-agent idle metrics smoke recorded `0` total gateway
  requests, `0.0` conversation/terminal requests per minute, seven device
  metric samples, PSS delta `-508 KB`, `Wake Locks: size=0`,
  `mWakeLockSummary=0x0`, and no FATAL/ANR/OOM before a post-window manual
  refresh;
- light project navigation returned to list and reopened `test_ccb2_beta` in
  about `2.0 s` each in debug mode;
- controlled send showed the local message after about `5.4 s`, but did not
  prove a new backend reply and surfaced `open terminal failed: not a
  terminal`.

Status:

- Level 0, Level 1 light navigation, and short idle soak are green as
  diagnostic baselines.
- Level 2 native conversation smoke is now green for pane-backed phone send
  and desktop-origin explicit refresh on disposable `test_ccb2` projects; the
  remaining Level 2 work is longer multi-turn pressure, older-history
  pagination, and scrolled-away new-message behavior.
- File/image pressure has first native selected-agent smoke coverage on fresh
  disposable `test_ccb2` projects: text attachment send/download, image
  send/preview, seeded Codex native text/image artifact downloads, and
  on-device SHA256 verification for `9` saved files passed on app head
  `16e621e` and source head `7fece763`. Full C6/C7 acceptance still needs
  live provider-generated artifacts, retry/error paths, restart persistence,
  and profile/release metrics.

## Safety And Stop Conditions

Testing should avoid making the emulator or app unstable. Use staged load and
stop early when instability appears.

Stop the run and collect evidence if any of these occur:

- app process dies, Android ANR appears, or the screen freezes for more than
  10 seconds;
- memory PSS grows by more than 30 percent after a steady-state phase and does
  not fall after idle;
- two consecutive gateway requests fail without an intentional failure step;
- the project page returns to `demo` or loses the paired gateway profile;
- conversation refresh replaces visible newer turns with stale ask/job
  records;
- ordinary mobile send injects `CCB_REQ_ID` or a mobile-specific prefix;
- file upload/download leaves a permanently stuck busy state;
- frame timing p95 exceeds the gate for two consecutive samples in profile or
  release mode.
- any controlled native-send probe reports `open terminal failed: not a
  terminal`, no visible own message, or no backend reply marker within the
  configured timeout;
- idle power evidence shows nonzero app-held wake locks, repeated foreground
  service wakeups, or app CPU above the idle budget for two consecutive
  samples;
- a run uses the fake `demo` project or a non-test project while claiming real
  server-wide acceptance.

When a stop condition is hit, do not continue pressure actions. Save screenshot,
UI dump, logcat, gateway logs, memory snapshot, and the last user action.

## Build Modes

Use different gates for debug and profile/release:

- **Debug build**: developer stability and functional coverage only. Memory
  and startup values are diagnostic, not release acceptance.
- **Profile build**: primary performance mode for frame timing, cold/warm
  startup, scrolling, rendering, and memory trend.
- **Release build**: package size, install/start sanity, and final user-path
  smoke. Release cannot rely on debug-only paired-profile seeding.

Minimum report must state which mode was used.

## Environment Matrix

### Required Local Matrix

- Android Emulator `emulator-5554`, API 35 or newer.
- `adb reverse` to a loopback-only gateway.
- Source worktree containing the current mobile gateway source changes.
- Two fresh CCB test projects under `/home/bfly/yunwei/test_ccb2`, each with
  at least two agents.
- One long-lived server-wide gateway with project registry mode.
- One app install with paired gateway restored after app restart.
- At least one clean test project reserved for mobile pressure under
  `/home/bfly/yunwei/test_ccb2`; manual exploration should not target
  `/home/bfly/yunwei/ccb_source/mobile` unless the test explicitly validates the
  mobile repo itself.

### Optional Release Matrix

- Android physical device on LAN.
- Android physical device through Tailnet or relay route.
- iPad/iOS simulator after iOS build path is active.

## Test Data Sets

All reusable test data should be deterministic and safe to recreate.

### Projects

- `test_ccb2_alpha`: default navigation and multi-project source.
- `test_ccb2_beta`: default manual/AVD interactive project.
- `test_ccb2_stale_*`: registry entries that are intentionally stopped or
  unreachable for list degradation tests.
- `test_ccb2_large_history`: seeded transcript and Markdown rendering pressure.

Each project should have:

- `mobile_probe`: primary text/file/conversation agent;
- `mobile_peer`: secondary agent for isolation and switch tests;
- a known CCB window and pane target for each agent;
- a known expected provider/session id when provider-native transcript mapping
  is under test.

### Prompts

Use short deterministic markers so phone screenshots, source logs, and desktop
panes can be correlated:

- `mobile-compass-ping:<timestamp>` for single-send probes;
- `mobile-turn-a:<index>:<timestamp>` for multi-turn agent A;
- `mobile-turn-b:<index>:<timestamp>` for multi-turn agent B;
- `mobile-md:<timestamp>` for Markdown-heavy reply;
- `mobile-file:<timestamp>` for attachment acknowledgement;
- `mobile-artifact:<timestamp>` for backend-generated file links.

Ordinary mobile input must be sent exactly as typed. It must not be rewritten
with `CCB_REQ_ID`, `mobile_gateway`, a device prefix, or an ask-job envelope.

### File Corpus

Store generated local files under `/tmp/ccb-mobile-file-corpus-<timestamp>/`
for each run:

- `small.md`: Markdown <= 20 KB with heading, list, code, and link;
- `small.txt`: UTF-8 text <= 20 KB;
- `document.pdf`: 1-5 MB PDF or generated binary-backed PDF fixture;
- `image.png`: 1-5 MB generated PNG with visible marker text;
- `image.jpg`: 1-5 MB JPEG;
- `near-limit.bin`: just below the configured accepted file-size limit;
- `oversized.bin`: above the configured limit;
- `unsupported.xyz`: unsupported extension/type when the app exposes this
  error.

The report records file size, SHA256, selected MIME type, upload duration,
download duration, saved path, and whether the opened/saved file hash matches.

## Observability Requirements

Each run writes a single JSON summary and a folder of artifacts:

- app commit, source commit, build mode, APK path and size;
- gateway listen URL, route provider, host id, source state directory;
- ADB device id, emulator image/API, `adb reverse --list`;
- project list count, healthy count, and first visible projects;
- selected project id/root and selected agent names;
- p50/p95/max timings for each measured action;
- memory PSS/RSS before, during, and after load;
- CPU snapshot during idle and during stress;
- screenshots for home, project page, conversation after send, file chip, and
  download result;
- UI dumps for key states;
- logcat tail, gateway log tail, and source-side errors;
- explicit pass/fail and first failed gate.
- selected build mode and whether debug-only profile seeding was used;
- source/app git status summaries so dirty worktrees are visible;
- request counts by endpoint during idle and stress windows;
- native pane evidence for send/read tests: pane id, session/window, tmux
  target, transcript cursor, and the visible desktop-pane marker when
  available.

Recommended artifact root:

```text
/tmp/ccb-mobile-stress-<timestamp>/
```

## Metrics

### UX Timing Metrics

Measure from user action to the first visible stable UI state:

- cold app start to first route visible;
- cold app start to server project list visible;
- manual project-list refresh;
- open project to selected-agent page visible;
- agent switch to selected-agent timeline ready;
- conversation refresh to unchanged/no-jump state;
- mobile send tap to local pending/sent visible;
- mobile send tap to desktop pane/native transcript input visible;
- mobile send tap to first provider reply visible;
- older transcript page load after upward scroll;
- attachment selected to preview visible;
- attachment send to upload accepted;
- attachment chip tap to file saved/openable;
- backend-generated file link to file saved/openable.

### Rendering Metrics

Use profile/release mode for acceptance:

- frame p50/p95 while scrolling project list;
- frame p50/p95 while scrolling a long conversation;
- frame p50/p95 while expanding/collapsing long Markdown;
- frame p50/p95 while image thumbnails and document chips are visible;
- dropped/janky frame percentage for each interaction.

Debug `dumpsys gfxinfo` can be recorded, but it is not a release gate for
Flutter SurfaceView.

### Resource Metrics

- app PSS/RSS at idle home;
- app PSS/RSS after opening project;
- app PSS/RSS after 100 conversation turns;
- app PSS/RSS after image/document upload/download;
- app PSS/RSS after 30-minute soak;
- CPU idle percentage;
- CPU during list refresh, conversation refresh, file upload/download;
- network request counts per minute while idle.
- wake-lock state from `dumpsys power`;
- package-scoped `dumpsys batterystats --charged <package>` excerpt;
- GC/logcat warning rates during scroll and file operations.

### Correctness Metrics

- desktop pane contains the exact mobile prompt without injected metadata;
- phone timeline contains the same prompt and the corresponding provider
  reply in the same order;
- `CCB_REQ_ID`, `mobile_gateway`, `completion_snapshot`, provider source
  labels, and job ids are absent from ordinary chat bubbles;
- older transcript pages prepend without reordering or replacing visible new
  content;
- file attachment chips map to authenticated opaque ids, not host paths;
- backend-generated file links are downloadable on the phone.

## Budgets

Initial budgets are provisional until a profile-build baseline exists:

| Metric | Debug Diagnostic | Profile/Release Gate |
| :--- | :--- | :--- |
| cold start to first route | record only | p95 <= 2500 ms |
| cold start to project list | record only | p95 <= 3500 ms |
| project list refresh, <= 50 healthy projects | p95 <= 2000 ms | p95 <= 1000 ms |
| open project to agent page | p95 <= 3000 ms | p95 <= 1500 ms |
| agent switch ready | p95 <= 2000 ms | p95 <= 800 ms |
| unchanged conversation refresh | p95 <= 1500 ms | p95 <= 700 ms |
| older page load | p95 <= 2500 ms | p95 <= 1200 ms |
| local send visible | p95 <= 500 ms | p95 <= 250 ms |
| first provider reply visible | provider-dependent | record p50/p95 by provider |
| project-list scroll frame p95 | record only | <= 24 ms |
| chat scroll frame p95 | record only | <= 32 ms |
| idle CPU | <= 3 percent | <= 1 percent |
| idle memory growth over 30 min | <= 30 percent | <= 15 percent |
| app-held wake locks while idle | 0 expected | 0 required |
| idle gateway requests | record only | <= 2/minute when no manual refresh |
| file preview visible | p95 <= 1500 ms | p95 <= 800 ms |
| file upload accepted, <= 5 MB | p95 <= 5000 ms | p95 <= 3000 ms |
| file download saved, <= 5 MB | p95 <= 5000 ms | p95 <= 3000 ms |

Any budget failure should be classified as app UI, gateway, source backend,
provider latency, emulator/device, or test harness overhead.

## Sampling Method

Use consistent sampling so separate runs are comparable. Each sample should be
timestamped relative to the first app foreground frame.

| Signal | Debug Baseline | Profile/Release Gate | Notes |
| :--- | :--- | :--- | :--- |
| Gateway endpoints | count before/after each stage | per-minute counters during soak | separate `/v1/projects`, project view, conversation, terminal, file, artifact, pairing |
| UI timings | stopwatch or integration-test markers | integration-test markers required | record p50/p95/max over repeated actions |
| Frame stats | optional `dumpsys gfxinfo` | required before/after scripted scroll | reset frame stats before each scripted lane when possible |
| Memory | `dumpsys meminfo <package>` every 30-60s | baseline/mid/end/post-idle | use PSS as primary, RSS as diagnostic |
| CPU | `top -H` or `pidstat` equivalent | idle and interaction windows | record host load too when emulator is saturated |
| Power | `dumpsys power`, `dumpsys batterystats` | required for soak | app-held wake locks must be zero at idle |
| Logs | logcat cursor per run | logcat cursor per run | fail on FATAL/ANR/OOM; classify repeated warnings |
| Source proof | gateway log tail and project log tail | required | include selected pane id and project root |

Minimum ADB/host commands for an artifact packet:

```bash
adb devices -l
adb reverse --list
adb shell dumpsys window | sed -n '1,80p'
adb shell dumpsys meminfo io.ccb.mobile.ccb_mobile
adb shell dumpsys power
adb shell dumpsys gfxinfo io.ccb.mobile.ccb_mobile
adb logcat -d -v time
curl -sS "$GATEWAY_URL/v1/health"
curl -sS "$GATEWAY_URL/v1/projects"
```

For request counts, prefer gateway-side counters or structured logs. If only
raw logs are available, count by normalized route template, not by full URL, so
project ids and artifact ids do not split the same endpoint into many buckets.

## Stress Ramp

Run pressure in this order. Each lane starts from a known passing lower lane
and stops immediately on the first P0 failure.

| Ramp | Duration / Size | Required Build | Purpose |
| :--- | :--- | :--- | :--- |
| R0 Safe compass | 3-5 minutes | debug | verify gateway binding, no fake/demo, no fatal logs |
| R1 Chat burst | 20 turns, two agents | debug | catch ask metadata, duplicate merge, agent isolation |
| R2 Mixed history | 200+ turns | profile preferred | catch pagination, layout, memory, source-label leaks |
| R3 File burst | 10 files, 2 projects | debug then profile | catch upload/download state, hashing, isolation |
| R4 Recovery | reverse, gateway, ccbd, revoke, resume | debug | catch retry/replay and stale auth |
| R5 Release soak | 30 minutes | profile/release | catch polling storm, wake locks, leaks |
| R6 Extended soak | 2 hours | profile/release | optional pre-release confidence |

Do not jump directly to R5. If R1 or R2 is failing, the soak will mostly
measure a broken app.

## Human-Visible Stability Checks

Automated metrics are not enough for the current product surface. Every deep
run should include screenshots or video clips for:

- first server-wide project list after refresh;
- selected project/agent with matching desktop pane marker;
- phone send and provider reply;
- desktop-origin turn before/after explicit refresh;
- scrolled-away new-message state;
- older-history top/middle/bottom;
- image/document attachment tray and conversation chips;
- backend artifact download result;
- recovery error and recovered state;
- final idle screen after the soak.

Reject runs where the app is technically alive but visibly flickers, repeatedly
expands/collapses cards, loses scroll position on unchanged refresh, or hides
the user's selected project/agent context.

## Execution Lanes

### Lane A: Compass Baseline

Purpose: quickly answer "is the current app safe to touch?"

Scope:

- Level 0 health snapshot;
- short project-list API latency;
- passive CPU/memory/power/log sampling;
- no send, upload, reinstall, gateway restart, or battery reset.

Cadence:

- before every manual real-backend session;
- after any app-side refresh or polling change;
- after any source gateway change that affects project list, conversation, or
  file routes.

### Lane B: Interactive Real-Project Smoke

Purpose: verify the visible phone app is mounted to the correct real projects.

Scope:

- project list visible and refreshable;
- open `test_ccb2_*`;
- switch agents;
- run one controlled send only if the selected pane target is valid;
- capture screenshots before and after.

Cadence:

- before handing the emulator to the user for manual review;
- after native conversation or route changes.

### Lane C: Native Conversation Stress

Purpose: verify pane-equivalent chat.

Scope:

- 20 mobile-originated turns across two agents;
- 5 desktop-pane-originated turns refreshed onto the phone;
- older-page loading;
- no ask/job metadata in the default chat surface.

Cadence:

- after every source/app package that touches send, conversation, transcript,
  timeline merge, refresh, or metadata hiding.

### Lane D: File And Artifact Stress

Purpose: validate user and backend file workflows.

Scope:

- image upload/download;
- document upload/download;
- near-limit and oversized behavior;
- backend-generated artifact link download;
- repeat after agent/project switch.

Cadence:

- after native conversation path is green;
- after every file-route, attachment UI, storage, permission, or download
  change.

### Lane E: Long-History And Rendering Stress

Purpose: verify performance and visual stability.

Scope:

- 200+ turns with mixed Markdown and attachments;
- upward pagination;
- manual refresh while scrolled near top/middle/bottom;
- expand/collapse long blocks.

Cadence:

- before release milestones;
- after timeline virtualization, Markdown rendering, refresh scheduler, or
  transcript cursor changes.

### Lane F: Recovery And Security Stress

Purpose: verify fail-closed behavior.

Scope:

- remove/restore `adb reverse`;
- restart gateway;
- restart one project `ccbd`;
- revoke paired device;
- re-pair;
- background/resume during refresh.

Cadence:

- before declaring source/app gateway contracts stable;
- after auth, token, route-provider, terminal, file, or lifecycle changes.

### Lane G: Soak

Purpose: detect slow leaks and polling storms.

Scope:

- 30-minute foreground soak for release gate;
- optional 2-hour extended soak;
- low-frequency manual refresh and agent switch;
- final send/file smoke only after idle metrics are stable.

Cadence:

- before release candidate;
- after changes to polling, refresh, networking, lifecycle, image decode, file
  storage, or transcript caching.

## Test Levels

### Level 0: Non-Disruptive Health Snapshot

Purpose: prove the current device is safe to touch.

Actions:

1. Verify emulator online and CCB Mobile in foreground.
2. Verify gateway listener and `adb reverse`.
3. Call `/v1/projects` three times with at least one second between samples.
4. Capture screenshot, UI dump, meminfo, top, and logcat tail.
5. Do not tap, type, send, upload, or reinstall.

Pass:

- app remains foreground;
- no demo project when paired gateway should be active;
- project list or current real project page is visible;
- idle CPU is low;
- no new error flood in logcat or gateway logs.

Failure triage:

- app not foreground: test harness/environment issue first;
- gateway unreachable: inspect `adb reverse`, listener, and source gateway log;
- project list contains only demo: app pairing/profile activation issue;
- high idle CPU or wake locks: refresh/polling or platform lifecycle issue.

### Level 1: Real Project Navigation Baseline

Purpose: validate project list and project-open performance.

Actions:

1. Start from paired gateway home.
2. Refresh projects once.
3. Open the first healthy `/home/bfly/yunwei/test_ccb2` project.
4. Switch between two agents once.
5. Return to project list and reopen the same project.

Pass:

- no fallback to fake demo;
- project list remains server-wide;
- selected project id is correct for all project routes;
- no stale/unreachable project blocks the list;
- timings stay within debug diagnostic or profile gate.

### Level 2: Native Conversation Functional Stress

Purpose: validate pane-equivalent chat under moderate use.

Prerequisite: the native pane send/read contract must be landed.

Actions:

1. Send 10 short prompts from the phone to agent A.
2. Send 10 short prompts from the phone to agent B.
3. Type 5 prompts directly in the desktop pane and refresh phone timeline.
4. Scroll up to load older transcript pages.
5. Switch agents repeatedly and verify each agent retains its own timeline and
   draft.

Pass:

- no `CCB_REQ_ID`, mobile prefix, or ask/job wrapper in pane/transcript;
- desktop pane and phone timeline agree on user turns and replies;
- stale job records do not overwrite latest native turns;
- duplicate prompts remain distinct;
- scroll position does not jump unexpectedly after unchanged refreshes.

Detailed cases:

| Case | Setup | Action | Expected |
| :--- | :--- | :--- | :--- |
| C2.1 single native send | agent A open | send `mobile-compass-ping:<id>` | desktop pane receives exact text; phone shows user turn; no `CCB_REQ_ID` |
| C2.2 provider reply | C2.1 green | wait for provider reply | phone shows same assistant reply as native transcript/pane |
| C2.3 desktop-origin turn | agent A pane focused on desktop | type marker directly in pane | phone refresh shows marker without reopening project |
| C2.4 duplicate text | agent A open | send `hi` twice | both turns remain distinct and ordered |
| C2.5 agent isolation | agents A/B available | send distinct markers to each | switching agents never shows other agent's turns |
| C2.6 stale history guard | old ask/job records exist | refresh timeline | stale records do not replace latest native transcript |
| C2.7 older page | seeded transcript exists | pull/load older page | older messages prepend and cursor remains stable |

### Level 3: File And Image Stress

Purpose: validate upload, preview, download, and backend-generated artifacts.

Test files:

- small text or Markdown file, <= 20 KB;
- PDF or document file, 1-5 MB;
- PNG/JPEG image, 1-5 MB;
- large accepted file near 20-25 MB;
- rejected oversized file above the configured limit;
- unsupported extension/type if the app exposes a clear error.

Actions:

1. Attach one image to an empty text message.
2. Attach one document to a text message.
3. Attach multiple files up to the per-message limit.
4. Download each app-uploaded attachment from the conversation.
5. Trigger or select a backend-generated file/artifact and download it.
6. Repeat after project/agent switch and app background/resume.

Pass:

- attachment tray remains responsive;
- thumbnails/chips do not overflow;
- upload progress and failure states are visible;
- downloaded files are saved/openable;
- raw host paths and unauthenticated URLs are not exposed;
- failed/rejected files do not corrupt the composer state.

Detailed cases:

| Case | Action | Expected |
| :--- | :--- | :--- |
| F3.1 image-only send | attach `image.png`, no text | tray renders thumbnail, send succeeds, reply references file or image chip |
| F3.2 document + text | attach `small.md` with text | chip shows name/size, send succeeds, download returns matching SHA256 |
| F3.3 multi-attachment | attach max allowed count | layout remains stable; all accepted files have independent chips |
| F3.4 near-limit file | attach `near-limit.bin` | progress remains visible, upload either succeeds within budget or gives clear retryable error |
| F3.5 oversized file | attach `oversized.bin` | blocked before or during upload with clear error, composer recovers |
| F3.6 backend artifact | ask deterministic artifact prompt | app downloads generated text/image through opaque ids |
| F3.7 project switch | upload in project A then B | files/artifacts do not cross project ids |

### Level 4: Rendering And History Pressure

Purpose: validate long timeline rendering.

Actions:

1. Seed at least 200 native transcript turns in one agent.
2. Seed mixed Markdown: headings, lists, code blocks, tables, links, and long
   text.
3. Seed image/document chips and backend artifact links.
4. Open project and measure initial visible page.
5. Scroll upward until all older pages are loaded.
6. Expand/collapse long blocks during scrolling.
7. Refresh while scrolled near middle and near top.

Pass:

- no visible jumping between old and new content;
- unchanged refresh does not re-render or reorder the list;
- older pages append/prepend in stable order;
- expanded state is stable for the current visible items;
- frame/memory budgets hold in profile mode.

Detailed cases:

| Case | Dataset | Action | Expected |
| :--- | :--- | :--- | :--- |
| R4.1 initial long open | 200+ turns | open project | newest page visible within budget |
| R4.2 upward pagination | 200+ turns | pull/load older until start | stable order; no duplicate visible keys |
| R4.3 unchanged refresh | scrolled middle | refresh | scroll position and expanded states remain stable |
| R4.4 Markdown blocks | mixed Markdown | expand/collapse code/table blocks | no overflow; frame budget holds |
| R4.5 media chips | image/doc chips visible | scroll repeatedly | thumbnails/chips do not trigger memory runaway |

### Level 5: Multi-Project Pressure

Purpose: validate server-wide project isolation and list scale.

Actions:

1. Start at least 10 mounted CCB projects, two of them active test projects.
2. Keep several stale/unreachable registry entries.
3. Refresh the server project list.
4. Open project A, send/read, upload/download.
5. Open project B, send/read, upload/download.
6. Return to project A and verify state isolation.

Pass:

- stale projects degrade but do not block reachable projects;
- messages/files/artifacts never cross project ids;
- project list refresh stays within budget;
- selected project and selected agent survive navigation correctly.

### Level 6: Recovery And Failure Pressure

Purpose: verify fail-closed recovery without hidden data loss.

Actions:

1. Drop `adb reverse` and verify recoverable gateway error.
2. Restore `adb reverse` and refresh.
3. Restart the mobile gateway without clearing app state.
4. Restart one test project's `ccbd`.
5. Revoke the paired device and verify protected routes fail.
6. Re-pair and verify state recovery.
7. Background and resume the app during conversation refresh.
8. Rotate or resize emulator if supported by the run.

Pass:

- no unsafe action succeeds after revoke;
- refresh recovers after gateway/ccbd restart;
- terminal handles do not replay stale input;
- no stuck loading spinner after recoverable failures;
- app does not clear local drafts unless the user sent them successfully.

Current evidence:

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
- 2026-06-27 `952f2b2` covers pending draft/attachment preservation and
  terminal input replay guard after `adb reverse` loss/restore plus explicit
  Retry:
  [../history/local-avd-replay-guard-smoke-20260627.json](../history/local-avd-replay-guard-smoke-20260627.json).
- 2026-06-27 `a57fc92` covers paired-device revoke fail-closed behavior and
  app UI re-pair recovery without clearing app data:
  [../history/local-avd-revoke-repair-smoke-20260627.json](../history/local-avd-revoke-repair-smoke-20260627.json).
- Remaining Level 6 stress work: longer profile/release recovery pressure.

### Level 7: Soak

Purpose: detect leaks, polling storms, and slow degradation.

Actions:

1. Open a real test project and leave the app foreground for 30 minutes.
2. Every 5 minutes, refresh conversation once and switch agent once.
3. After 30 minutes, run file download and a short native send.
4. Optional extended soak: 2 hours with the same low-frequency cadence.

Pass:

- memory growth remains within budget;
- idle CPU remains low;
- gateway request rate stays low while idle;
- no timeline drift or stale job overwrite appears after long idle.

Sub-gates:

- debug request-rate plus device-metrics smoke: accepted on 2026-06-26 with
  `0` selected-agent conversation/terminal-history requests over `180` idle
  seconds, PSS delta `-508 KB`, no wake locks, and no FATAL/ANR/OOM;
- 3-minute safe soak: developer preflight, must have no PSS growth, no wake
  locks, and no FATAL/ANR/OOM before heavier tests;
- 30-minute release soak: profile/release gate, memory growth <= 15 percent;
- 2-hour extended soak: optional regression for polling, image cache, and
  network reconnect work.

## Automation Plan

Add or extend tools in this order:

1. `tools/mobile_app_compass_test.py`
   - combined Level 0 collector and short soak runner;
   - default mode is non-disruptive: no install, no sends, no uploads, no
     batterystats reset;
   - optional explicit `--send-marker` performs one controlled real send and
     marks the run `warn` if no reply marker is visible.
2. `tools/mobile_app_perf_smoke.py`
   - starts server-wide local gateway, installs profile/debug app with paired
     host, measures startup/list/open/agent-switch.
3. `tools/mobile_app_conversation_stress.py`
   - after native pane send lands, drives Level 2 and records pane/transcript
     evidence.
4. `tools/mobile_app_file_stress.py`
   - drives upload/download/image/document/backend artifact lanes.
5. `tools/mobile_app_soak.py`
   - long-running low-frequency stability run with periodic metrics.

Each tool should support:

- `--dry-run`;
- `--device-id`;
- `--gateway-url` or `--gateway-listen`;
- `--project-root`;
- `--artifact-dir`;
- `--no-send` for safe diagnostics;
- JSON summary to stdout and artifact directory.

Tool reports must use `ok`, `warn`, `blocked`, or `fail`:

- `ok`: all gates in the requested level passed;
- `warn`: safe diagnostics passed but a non-release gate, such as optional
  controlled send reply visibility, did not close;
- `blocked`: environment or prerequisite missing, such as app not foreground,
  no device, no gateway, or native send target invalid;
- `fail`: app/gateway correctness or stability gate failed.

## Triage Model

Every failure should be assigned one primary owner before new work starts:

- **app-ui**: rendering, scroll, composer, chips, route state, stale UI, or
  local state merge;
- **app-transport**: HTTP/WebSocket/file client, auth header, retry, timeout,
  or download storage;
- **source-gateway**: route contract, project registry, selected pane target,
  file/artifact route, revoke, or terminal handle;
- **source-runtime**: ccbd, tmux pane resolution, provider transcript mapping,
  lifecycle, or terminal attach;
- **provider**: model latency, provider-native transcript availability, or
  provider-specific streaming behavior;
- **environment**: emulator, ADB, reverse port, host CPU, network, or test
  harness issue.

Do not continue stress after a P0 blocker. Convert the blocker into a focused
source/app package, then restart from Lane A.

## Manual Review Checklist

Before accepting a stress run, inspect:

- current screen screenshot;
- first project list page;
- selected test project path;
- selected agents;
- one native send with no `CCB_REQ_ID`;
- one desktop-pane-only prompt appearing on the phone;
- one older transcript page loaded by upward scroll;
- one image chip and one document chip;
- one successful download snackbar or file-open path;
- memory trend chart or at least before/after PSS/RSS;
- all stop conditions.

## Runbook

### Safe Compass Run

```bash
cd /home/bfly/yunwei/ccb_source/mobile
source tools/mobile_toolchain_env.sh
python tools/mobile_app_compass_test.py \
  --gateway-url http://127.0.0.1:19011 \
  --duration-s 180 \
  --sample-interval-s 30
```

Expected outcome:

- `status` is `ok`;
- app is foreground;
- real project or project list is visible;
- project list API has no repeated failures;
- no wake locks, FATAL, ANR, or OOM;
- PSS does not grow materially.

### Controlled Send Probe

Only run this after confirming the selected project and agent are disposable
test targets:

```bash
python tools/mobile_app_compass_test.py \
  --gateway-url http://127.0.0.1:19011 \
  --duration-s 60 \
  --sample-interval-s 30 \
  --send-marker mobile-compass-ping-$(date +%H%M%S)
```

Expected outcome after native send is fixed:

- marker appears in the phone timeline;
- desktop pane receives exact marker text;
- reply marker appears or provider reply is visible;
- no `CCB_REQ_ID`, `mobile_gateway`, `completion_snapshot`, or fake/demo
  markers appear in ordinary chat.

If the run reports `warn` because the own message appears but the reply marker
does not, inspect screenshot and gateway/source logs before continuing.

## Release Gate

CCB Mobile is not release-ready until the following pass in profile or release
mode:

- Level 1 server-wide project navigation baseline;
- Level 2 native conversation functional stress;
- Level 3 file/image stress;
- Level 4 rendering/history pressure with at least 200 turns;
- Level 5 multi-project pressure with stale registry entries;
- Level 6 recovery/revoke smoke;
- Level 7 30-minute soak;
- package size and install/start sanity;
- no fake/demo acceptance evidence used for P0 chat or file gates.

## Open Questions

- What is the initial supported maximum transcript size per agent before the
  app should require search or archive mode?
- Should the project list API cache health status with a stale marker to keep
  refresh under budget when many registry entries are offline?
- What file size limit should ship for the first real app build: 25 MB, 50 MB,
  or configurable per host?
- Which physical Android devices should be the minimum release performance
  matrix?
