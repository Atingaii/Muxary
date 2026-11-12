# Local AVD Real-Project Test Runbook

Date: 2026-06-26
Status: Detailed execution runbook
Read with:
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md),
[app-stress-and-performance-test-plan.md](app-stress-and-performance-test-plan.md),
and
[agent-native-conversation-and-input-correction.md](agent-native-conversation-and-input-correction.md).

## Purpose

This runbook is the operator-facing test script for CCB Mobile local Android
Emulator validation. It exists to prevent ambiguous "it works on the phone"
evidence. A valid run must prove that the app is connected to the same
server-side CCB projects and agent panes that the desktop is using.

The phone is not an independent chatbot and the test target is not the fake
demo repository. The phone must:

- list all mounted/reachable server CCB projects;
- open a disposable real project under `/home/bfly/yunwei/test_ccb2`;
- render the selected agent's pane-equivalent conversation;
- send ordinary text as direct pane input, not as a CCB ask job;
- upload/download files through authenticated gateway routes;
- remain stable without blind fixed-interval terminal-history polling.

## Run Modes

Use these modes to make evidence comparable.

| Mode | Purpose | May Send? | May Upload? | Acceptance Weight |
| :--- | :--- | :--- | :--- | :--- |
| Compass | Safe health snapshot before touching the app | No | No | Environment only |
| Manual Smoke | Human-visible app validation with screenshots | One marker only | One small file only | P0 UX smoke |
| Functional Stress | Pane chat, files, project switching, recovery | Yes | Yes | P0/P1 correctness |
| Performance | Profile/release timing, scrolling, memory, CPU | Limited | Limited | Release readiness |
| Soak | Long idle/active stability and battery risk | Low-frequency | Optional final smoke | Release readiness |

Do not mix modes in one report. A failed compass run should stop before manual
or stress actions.

## Non-Negotiable Preflight

Before any tap, type, upload, or send, collect and record:

```text
app_commit=<git sha in /home/bfly/yunwei/ccb_source/mobile>
source_commit=<git sha in the source worktree under test>
app_dirty=<git status --short>
source_dirty=<git status --short>
adb_device=<adb devices -l>
gateway_url=http://127.0.0.1:<port>
adb_reverse=<adb reverse --list>
gateway_health=<GET /v1/health>
projects_count=<GET /v1/projects count>
selected_project_root=<absolute test_ccb2 root>
selected_agent=<agent name>
selected_agent_runtime=<provider, pane_id, tmux window, namespace epoch>
```

Fail the run immediately if:

- the app is using the fake/local demo repository for P0/P1 chat;
- the selected project is not under `/home/bfly/yunwei/test_ccb2`;
- the selected agent has no active pane evidence;
- `pane_id` is null or the runtime is fake-only for a real-reply gate;
- `/v1/projects` is current-project-only instead of server-wide;
- multiple gateways are running and the app's paired profile cannot be tied to
  the intended gateway URL and host id.

## Real Project Fixture Gate

Each functional run must use at least two disposable projects:

```text
/home/bfly/yunwei/test_ccb2/<run-id>/test_ccb2_alpha
/home/bfly/yunwei/test_ccb2/<run-id>/test_ccb2_beta
```

Each project must have:

- `mobile_probe`: primary selected-agent chat target;
- `mobile_peer`: secondary isolation target;
- a valid CCB `ProjectView`;
- a valid tmux pane per test agent;
- provider/runtime evidence that can accept direct pane input;
- enough retained transcript or scrollback for older-history tests.

The setup is invalid if it only has static fixtures, fake local UI replies, or
agents whose runtime records show `pane_id: null`.

### Provider Tiers

Use the strongest available tier for each gate:

| Tier | Use | Allowed For |
| :--- | :--- | :--- |
| Real provider pane | Codex or another real provider agent with active pane/session | P0 chat, real reply, transcript, performance |
| Deterministic pane-backed test provider | Source-side provider stub running in a real CCB pane | Harness mechanics, file/artifact determinism |
| App fake/demo repository | Flutter unit/widget support only | Never P0/P1 real-backend acceptance |

If deterministic providers are used for file/artifact repeatability, the
report must say so and must still run at least one real-provider reply lane.

## Gateway And App Binding

The app must be bound to one intended server-wide gateway:

1. Start or select one loopback-only server-wide gateway.
2. Record the gateway process, port, host id, route provider, and source
   commit.
3. Set `adb reverse tcp:<port> tcp:<port>`.
4. Pair or debug-seed the app to that exact gateway.
5. In the app, refresh the project list and verify the first page matches the
   `/v1/projects` sample.

If older gateways are still running, the run report must list them and explain
how the tested app profile was pinned to the intended one. "The screen shows a
project" is not sufficient evidence.

## Stage A: Server-Wide Project List

Goal: prove the first page is server-wide.

Actions:

1. Start with the app foreground.
2. Navigate to the project list/home page.
3. Tap the visible refresh button.
4. Compare visible projects with `/v1/projects`.
5. Confirm `test_ccb2_alpha` and `test_ccb2_beta` are selectable.
6. Keep one stale/unreachable registry entry in the source list if available.

Pass:

- multiple mounted CCB projects are visible;
- stale/unreachable entries degrade but do not block healthy projects;
- refresh timing is recorded;
- no demo-only state appears.

Required evidence:

- screenshot of home list;
- `projects.json`;
- UI dump;
- refresh timing;
- gateway log tail.

## Stage B: Selected-Agent Pane Identity

Goal: prove the phone is looking at the same agent pane as the desktop.

Actions per selected agent:

1. Open `test_ccb2_beta`.
2. Select `mobile_probe`.
3. Record CCB source runtime evidence: agent runtime JSON, pane id, tmux
   socket/session/window, namespace epoch.
4. Capture desktop pane tail.
5. Capture phone timeline screenshot and UI dump.
6. Switch to `mobile_peer` and repeat.

Pass:

- newest phone content corresponds to the selected agent pane;
- the app does not show stale ask/job/completion records as newest chat;
- switching agents changes the transcript and draft state correctly;
- internal labels are not visible in ordinary bubbles.

Forbidden visible labels in default chat:

```text
CCB_REQ_ID
mobile_gateway
completion_snapshot
provider_native
jobs.jsonl
message_type=ask
project_view
```

## Stage C: Pane-Equivalent Send And Reply

Goal: prove phone input is equivalent to typing in the pane.

Actions:

1. Send `mobile-turn-a:<timestamp>` from the phone to `mobile_probe`.
2. Inspect the desktop pane before waiting for a provider reply.
3. Wait for the provider reply using the allowed active-send refresh/backoff.
4. Send `hi` twice to prove duplicate user text remains ordered.
5. Switch to `mobile_peer` and send `mobile-turn-b:<timestamp>`.

Pass:

- desktop pane receives exactly the typed text;
- no ask job or `CCB_REQ_ID` is created for ordinary chat;
- the phone shows the same user turn and the real provider reply in order;
- duplicate sends remain separate turns;
- failed sends do not replay terminal input silently.

Timing to record:

| Metric | Start | End |
| :--- | :--- | :--- |
| local send visible | send tap | user bubble stable |
| pane input visible | send tap | marker visible in desktop pane or pane log |
| first reply visible | send tap | first assistant reply visible in app |
| stable refresh | refresh action | unchanged list confirmed no jump |

## Stage D: Desktop-Origin Sync

Goal: prove the phone can dynamically load desktop-origin conversation.

Actions:

1. Type `desktop-origin:<timestamp>` directly into the desktop agent pane.
2. Do not touch the phone for 30 seconds.
3. Confirm no fixed polling storm and no visible timeline jumping.
4. Use the explicit conversation refresh action.
5. Repeat while the phone is scrolled away from newest.

Pass:

- desktop-origin text appears after allowed refresh;
- no project reopen is required;
- when not pinned to newest, the app uses a new-message affordance instead of
  jumping to bottom;
- unchanged refresh preserves scroll and expanded states.

## Stage E: Older Transcript And Rendering

Goal: prove dynamic upward loading and rendering stability.

Dataset:

- at least 200 turns;
- Markdown headings, lists, code, links, tables, long paragraphs;
- image/document chips;
- at least one backend artifact link.

Actions:

1. Open newest page.
2. Scroll upward until older pages load.
3. Capture page cursors and first/last visible markers.
4. Expand/collapse long blocks during scrolling.
5. Refresh at top, middle, and bottom positions.

Pass:

- older pages prepend in order;
- visible position is preserved after prepend;
- no stale completion/job records replace current pane history;
- no text overflow or layout collision;
- profile-mode frame/memory budgets are met.

## Stage F: Image And Document Send

Goal: prove user-origin files work in the real chat path.

Corpus:

```text
small.md
small.txt
document.pdf
image.png
image.jpg
near-limit.bin
oversized.bin
unsupported.xyz
```

Actions:

1. Attach `image.png` without text and send.
2. Attach `small.md` with text and send.
3. Attach multiple files up to the configured message limit.
4. Try `near-limit.bin`.
5. Try `oversized.bin` and `unsupported.xyz`.
6. Switch agents and confirm drafts/attachments do not leak.

Pass:

- preview tray and chips are stable;
- upload progress/errors are visible;
- accepted files appear as authenticated attachment ids;
- rejected files leave the composer usable;
- no host-local path is exposed.

Metrics:

- select-to-preview latency;
- upload accepted latency;
- conversation attachment visible latency;
- memory delta after image preview;
- error recovery latency.

## Stage G: Backend Artifact Download

Goal: prove files generated by agents can be downloaded to the phone.

Actions:

1. Ask the test agent to generate a deterministic text report.
2. Ask the test agent to generate a deterministic image or binary artifact.
3. Wait for the artifact chip/link in the conversation.
4. Tap download.
5. Open or inspect saved file.
6. Restart app and repeat download from history.

Pass:

- artifact appears in the correct agent/project conversation;
- download uses authenticated opaque id;
- saved hash or visible content matches source artifact;
- failed download/open has retry feedback;
- artifact remains available after app restart and project switch.

## Stage H: Multi-Project Isolation

Goal: prove server-wide access does not mix state.

Actions:

1. Open alpha, send a marker, upload one small file.
2. Open beta, send a different marker, upload a different file.
3. Return to alpha.
4. Stop or degrade beta.
5. Refresh alpha.

Pass:

- alpha and beta messages/files never cross;
- stopping beta does not break alpha;
- selected project/agent state remains correct;
- host id, project id, and route-provider metadata remain separate.

## Stage I: Recovery And Reconnect

Goal: prove remote-control failure behavior is safe.

Actions:

1. Remove `adb reverse`.
2. Trigger project list refresh and selected-agent refresh.
3. Restore `adb reverse`.
4. Restart the mobile gateway.
5. Restart one test project `ccbd`.
6. Revoke the paired device.
7. Re-pair.
8. Background/resume during refresh, send wait, and download.

Pass:

- protected routes fail after revoke;
- reconnect does not replay stale input;
- drafts remain available after recoverable network failure;
- no spinner remains indefinitely;
- app recovers without reinstall or clearing data.

## Stage J: Performance, Power, And Soak

Goal: prove the app can stay open as a remote-control surface.

Minimum debug diagnostics:

- 3-minute foreground idle soak on selected project;
- one project-list refresh;
- one conversation refresh;
- one agent switch;
- no send unless selected pane is verified.

Release/profile gate:

- 30-minute foreground soak;
- one manual refresh and one agent switch every 5 minutes;
- one post-soak send and one post-soak download;
- frame timing during project list scroll, long chat scroll, Markdown
  expansion, and attachment chip scroll.

Pass budgets:

- idle gateway requests <= 2/minute when no active send is pending;
- app-held wake locks: zero;
- profile/release idle CPU <= 1 percent target;
- debug idle CPU <= 3 percent diagnostic target;
- 30-minute profile/release PSS growth <= 15 percent;
- no FATAL/ANR/OOM;
- no visible timeline jumping while idle.

## Refresh-Specific Test Plan

The refresh model is a product gate, not just performance tuning.

Required refresh triggers:

- home project-list refresh button;
- pull-to-refresh or equivalent when list is at top;
- project open initial load;
- app resume;
- selected-agent explicit refresh button;
- scroll-near-oldest older-page load;
- scroll-near-newest refresh or append;
- bounded active-send backoff until reply or timeout.

Rejected refresh behavior:

- blind fixed 3-second terminal-history polling forever;
- refresh that replaces visible new turns with stale history;
- refresh that toggles expansion state or scroll position on unchanged data;
- refresh that continues at high request rate while idle.

Evidence:

- request count by endpoint during 3-minute idle;
- screenshot before and after unchanged refresh;
- UI dump proving no duplicate/stale items;
- logcat/gateway logs showing no periodic error flood.

## Automation Artifacts

Each run writes one directory:

```text
/tmp/ccb-mobile-avd-run-<timestamp>/
  summary.json
  environment.json
  projects.json
  selected-agent-runtime.json
  timings.json
  memory.json
  power.txt
  logcat.txt
  gateway.log.tail
  source-project.log.tail
  ui-home.xml
  ui-project.xml
  ui-post-send.xml
  screenshots/
  files/
```

`summary.json` must include:

```json
{
  "status": "ok|warn|blocked|fail",
  "first_failed_gate": "stage.case or null",
  "owner": "app-ui|app-transport|source-gateway|source-runtime|provider|environment|null",
  "app_commit": "...",
  "source_commit": "...",
  "gateway_url": "http://127.0.0.1:<port>",
  "project_root": "/home/bfly/yunwei/test_ccb2/...",
  "agent": "mobile_probe",
  "real_pane_verified": true,
  "fake_or_demo_used": false,
  "ccb_req_id_seen": false,
  "blind_polling_seen": false
}
```

## Reviewer Checklist

A reviewer should reject the run if any of these are true:

- evidence uses demo/fake for P0 real chat;
- selected agent has no verified pane id;
- the app sends through CCB ask/job semantics;
- `CCB_REQ_ID`, `mobile_gateway`, or `completion_snapshot` is visible in
  ordinary chat;
- the phone timeline differs from the desktop pane without a diagnostic
  failure;
- server-wide project list cannot be refreshed;
- files use raw host paths or unauthenticated URLs;
- performance report omits request rate, memory, or power evidence;
- the artifact does not identify source/app commits and selected project root.

## Execution Order For Workers

Keep worker packages cohesive:

1. **Environment and fixture package**: create verified real pane-backed
   `test_ccb2` projects, one intended gateway, profile seed/pairing, and
   compass artifact.
2. **Native chat package**: pane-equivalent send/read, metadata cleanup,
   desktop-origin sync, older-page loading.
3. **Refresh package**: remove or prove absence of blind polling, explicit
   refresh buttons, scroll/resume/active-send refresh, idle request metrics.
4. **File/artifact package**: image/document upload, backend artifact download,
   storage/open behavior, multi-agent/project isolation.
5. **Performance package**: profile/release frame timing, memory, CPU, power,
   30-minute soak, final summary and evidence index update.

Do not start Stage F or later if Stage C is blocked.

## Current Known Blocker From Latest Compass Evidence

The latest controlled send evidence against gateway `127.0.0.1:19011` opened a
real server-wide project list but selected a `test_ccb2_beta` fixture whose
agents were fake-only and had no valid agent pane. The UI showed the local
message, but the backend path returned `open terminal failed: not a terminal`.

That evidence is useful as a fixture-gate failure. It is not valid proof that
real selected-agent chat works or fails. The next valid run must first pass
the Real Project Fixture Gate above with a pane-backed agent.
