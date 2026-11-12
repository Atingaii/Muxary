# Local Real-Backend Comprehensive Test Plan

Date: 2026-06-24
Status: Reopened for agent-native chat correction on 2026-06-25. Earlier
source loopback and AVD lanes remain useful evidence for gateway routing,
server-wide project listing, file upload/download, backend-generated artifact
download, revoke fail-closed, reconnect, and latency measurement. They do not
close the default chat gate because the ordinary mobile composer still uses
`/agents/{agent}/messages`, which the source gateway submits as
`message_type='ask'`, and the conversation route still backfills primarily
from CCB job records. The active P0 is now native selected-pane input plus
provider-native transcript loading, verified on a real local CCB project.

## Purpose

Define the full local validation plan for CCB Mobile when "local" means an
Android Emulator connected to a real host-side CCB test backend through a
loopback-only mobile gateway and `adb reverse`.

This plan exists because manual testing exposed an acceptance mismatch:
opening the default fake `demo` project can show `You / Sent`, and the
message-submit route can show an ask/job completion snapshot, but neither
proves that the phone is behaving like direct input to the selected agent.
Fake/local fixtures and ask/message-submit lanes remain useful for fast UI,
file, route, and compatibility regressions, but they cannot satisfy this
plan's P0 native chat, transcript, attachment, lifecycle, terminal, security,
or performance gates.

## Definition Of Local

For this plan, local means:

- host machine runs a disposable real CCB project through
  `/home/bfly/yunwei/ccb_source/ccb`;
- host machine runs `ccb mobile serve` bound only to loopback, for example
  `127.0.0.1:18897`;
- emulator reaches that gateway through `adb reverse tcp:<port> tcp:<port>`;
- app is installed from the current Flutter debug APK and paired into
  `AppRuntimeMode.pairedGateway`;
- all project, agent, message, attachment, terminal, lifecycle, and route
  behavior comes from the real CCB backend/gateway, not
  `FakeMobileCcbRepository`.

Evidence from the fake `demo` project is allowed only for auxiliary UI
regression. It must be labelled `fake/local auxiliary` and must not be used to
close the real-backend acceptance gates below.

## Required Backend Fixture

P0 should not depend on an external LLM provider or an open-ended Codex turn.
The local test backend needs a deterministic CCB project profile that can
produce bounded, verifiable outputs:

- primary agent: `mobile_probe`;
- secondary agent: `mobile_peer`;
- deterministic text echo path: receiving `ccb-local-echo:<id>` produces a
  visible agent reply containing `ccb-local-reply:<id>`;
- Markdown path: receiving `ccb-local-md:<id>` produces a Markdown reply with
  heading, list, code span, and link text;
- attachment path: receiving a message with one uploaded file produces a
  visible reply that references the file name and attachment metadata;
- generated artifact path: receiving `ccb-local-artifact:<id>` produces an
  agent reply with a downloadable backend-generated file, exposed through a
  gateway-authenticated opaque file or artifact id rather than a host-local
  path;
- terminal path: selected-agent pane can echo a sent command and accept paste,
  resize, reconnect, and token-renewal exercises;
- lifecycle path: wake/open/close work on the disposable project, and stop is
  tested only in a throwaway run.

If this deterministic backend fixture does not yet exist in CCB source, the
first implementation package for this plan is to add it to the local smoke
harness. Do not replace this requirement with app-side fake replies.

Current backend capability and AVD baseline:

- CCB source worktree:
  `/home/bfly/yunwei/ccb_source_mobile_local_backend_matrix`;
- source commit `99fa0544 feat: add mobile gateway file routes` adds
  gateway file upload/download routes and attachment-capable message submit
  for the local mobile gateway;
- source commit `7156431f fix: preserve mobile attachment metadata in
  conversation` carries mobile attachment metadata from source job
  `route_options` into ProjectView Comms and the gateway conversation route
  without exposing host-local file paths;
- source commit `9a6cd505 test: add deterministic mobile markdown fake reply`
  adds a `ccb-local-md:<id>` fake-provider fixture that returns Markdown with
  a title, reply marker, list item, code block, and link text through the real
  dispatcher;
- source commit `d0da183a feat: expose backend generated artifacts through
  mobile gateway (fake provider)` adds a deterministic
  `ccb-local-artifact:<id>` fixture that writes generated text and PNG
  artifacts into the mobile gateway file store, returns them as conversation
  attachments, and emits `ccb-artifact://<file_id>` Markdown links;
- source commit `50bf589f feat: expose mobile backend artifacts in
  conversations` makes that route executable against a real local gateway by
  passing the mobile file store into source fake-provider jobs, resolving
  `ccb-artifact://<file_id>` reply links back into conversation attachment
  metadata, and requiring bearer auth for ProjectView so revoked devices fail
  closed;
- app commit `eea9cac test: add local backend capability probe` plus
  `f1670db test: accept source pairing claim shape in mobile probe` provide
  the machine-readable source gateway probe;
- app commit `ac654ee test: cover emulator attachment upload download`
  extends the Android Emulator smoke runner with provider selection,
  terminal-lane skipping for deterministic fake-provider runs, and a real
  gateway file upload/download UI lane;
- app commit `7f9aeb7 test: cover emulator markdown reply smoke` adds a
  real-local AVD lane that expands the deterministic Markdown reply and waits
  for the title, marker, list item, code-block text, and link text;
- app commit `12cfa53 test: cover emulator image attachment smoke` adds a
  real-local AVD lane for generated PNG upload, conversation metadata, chip
  tap, download, and saved feedback;
- app commit `201d416 feat: implement backend-agent generated artifact
  download` maps `ccb-artifact://<file_id>` Markdown links back to matching
  conversation attachments, adds the `backend_artifact_route` capability
  probe gate, and adds latency budgets for backend-generated artifact
  download;
- app commit `b132f37 test: cover backend artifact downloads in emulator
  smoke` adds the Android Emulator route for backend-generated artifact text
  and image downloads and switches the capability probe default deterministic
  message to the Markdown fixture;
- probe artifact:
  [../history/local-real-backend-source-probe-20260623.json](../history/local-real-backend-source-probe-20260623.json);
- AVD smoke artifact:
  [../history/local-real-backend-avd-smoke-20260623.json](../history/local-real-backend-avd-smoke-20260623.json);
- latest raw run artifact:
  `/tmp/ccb-mobile-local-probe-source-file-route.json`;
- latest AVD terminal lane artifact:
  `/tmp/ccb-mobile-avd-terminal-smoke-source-worktree.json`;
- latest AVD attachment lane artifact:
  `/tmp/ccb-mobile-avd-real-local-attachment-smoke.json`.
- latest AVD attachment plus Markdown lane artifact:
  `/tmp/ccb-mobile-avd-real-local-attachment-markdown-smoke.json`.
- latest AVD media plus Markdown lane artifact:
  `/tmp/ccb-mobile-avd-real-local-media-markdown-smoke.json`.
- backend artifact + revoke source probe artifact:
  [../history/local-real-backend-source-probe-artifacts-revoke-20260623.json](../history/local-real-backend-source-probe-artifacts-revoke-20260623.json);
- latest combined AVD file/image/Markdown/backend-artifact lane artifact:
  [../history/local-real-backend-avd-file-md-artifact-smoke-20260623.json](../history/local-real-backend-avd-file-md-artifact-smoke-20260623.json);
- latest terminal/reconnect AVD lane artifact:
  [../history/local-real-backend-avd-terminal-smoke-20260623.json](../history/local-real-backend-avd-terminal-smoke-20260623.json);
- latest lifecycle stop AVD lane artifact:
  [../history/local-real-backend-avd-lifecycle-stop-smoke-20260623.json](../history/local-real-backend-avd-lifecycle-stop-smoke-20260623.json);
- latest multi-agent image/artifact AVD lane artifact:
  [../history/local-real-backend-avd-multi-agent-image-turns-smoke-20260623.json](../history/local-real-backend-avd-multi-agent-image-turns-smoke-20260623.json);
- five-run latency artifact:
  [../history/local-real-backend-latency-summary-20260623.json](../history/local-real-backend-latency-summary-20260623.json).
- live current-project backend reply and file evidence:
  [../history/local-real-backend-live-current-project-20260624.json](../history/local-real-backend-live-current-project-20260624.json).
- latest server-wide backend and AVD evidence:
  [../history/server-wide-backend-full-smoke-20260624.json](../history/server-wide-backend-full-smoke-20260624.json)
  and
  [../history/server-wide-avd-full-smoke-20260624.json](../history/server-wide-avd-full-smoke-20260624.json).

The source loopback probe passed health, pairing claim, authenticated
ProjectView, message submit, deterministic `agent_reply` marker, file upload,
and file download. This is the backend capability baseline only. It does not
close the AVD UI stop condition below.

The real-local AVD split lanes now also pass:

- terminal lane: Android Emulator `emulator-5554`, source provider `codex`,
  loopback gateway `127.0.0.1:18896`, `adb reverse tcp:18896 tcp:18896`,
  route diagnostics, paired profile activation, selected-agent focus,
  terminal WebSocket open/control, and post-smoke terminal target;
- attachment lane: Android Emulator `emulator-5554`, source provider `fake`
  only for deterministic backend reply text, loopback gateway
  `127.0.0.1:18897`, `adb reverse tcp:18897 tcp:18897`, real gateway file
  upload, conversation attachment metadata, deterministic agent reply, chip
  tap, gateway download, and `Saved <file>` feedback.
- attachment plus Markdown lane: Android Emulator `emulator-5554`, source
  provider `fake`, loopback gateway `127.0.0.1:18897`, real gateway message
  and file routes, deterministic Markdown reply, expanded reply rendering, and
  visible title, marker, list, code text, and link text.
- media plus Markdown lane: Android Emulator `emulator-5554`, source provider
  `fake`, loopback gateway `127.0.0.1:18897`, document upload/download,
  generated PNG upload/download, deterministic Markdown reply, and saved-file
  feedback in one real-local AVD run.

Fresh 2026-06-23 evidence now also proves:

- backend artifact source probe: real source gateway `status=ok`, deterministic
  Markdown reply marker, file upload/download, backend-generated artifact
  download, and revoke fail-closed over `/devices/me`, ProjectView, message
  submit, terminal open, and file download;
- combined fake-provider AVD lane: document upload/download, generated PNG
  upload/download, deterministic Markdown rendering, and backend-generated
  text + image artifact link downloads all return `status=ok` through
  `adb reverse`;
- terminal AVD lane: route diagnostics, paired profile activation,
  selected-agent focus, terminal WebSocket open/control, terminal reconnect
  button path, and post-smoke terminal target are green;
- lifecycle stop AVD lane: the destructive stop path is exercised only against
  a throwaway runtime and returns `status=ok`;
- five-run source/gateway latency summary: all five runs `ok`; p50/p95 pass
  for pairing, ProjectView, message submit, deterministic reply marker, file
  upload/download, backend artifact route, and revoke fail-closed.
- multi-agent AVD lane: Android Emulator `emulator-5554`, source provider
  `fake` for deterministic local backend replies, loopback gateway
  `127.0.0.1:18923`, and `adb reverse tcp:18923 tcp:18923` pass with two
  agents (`mobile_probe`, `mobile_peer`), per-agent draft isolation, two
  backend message-route turns per agent, per-agent PNG upload/download, and
  per-agent backend-generated text + PNG artifact link downloads.
- live current-project lane: Android Emulator `emulator-5554`, source
  worktree `/home/bfly/yunwei/ccb_source_mobile_local_backend_matrix`, real
  project `/home/bfly/yunwei/ccb_source/mobile`, loopback gateway
  `127.0.0.1:18931`, and `adb reverse tcp:18931 tcp:18931` pass with `lead`
  receiving two real backend message turns and the app displaying both
  `Agent reply / completion_snapshot` markers. The same gateway accepted text
  and PNG upload/download checks with decoded byte/hash verification.

The remaining local-matrix gaps are now specific follow-ups rather than the
core backend loop: app foreground/background timing, oversized-file rejection
timing, and later physical Tailnet/relay smoke.

## P0 Stop Condition

The plan is complete only when a fresh AVD run produces a machine-readable
summary with:

- current APK installed and focused;
- app paired to a real host-side CCB project;
- runtime mode confirmed as paired gateway;
- project id, agent names, namespace epoch, route provider, gateway URL, and
  adb reverse mapping recorded;
- ordinary text send -> selected-pane/native input -> real provider reply
  visible, with timing and no `CCB_REQ_ID`;
- Markdown reply visible and rendered;
- document and image upload -> backend conversation -> download/open feedback;
- backend-agent generated file -> conversation attachment/artifact link ->
  authenticated gateway download/open feedback with byte/hash verification;
- route diagnostics, lifecycle, raw terminal, focus, reconnect, and revoke
  gates passed;
- latency metrics collected for every operation listed in
  [Response Speed Budgets](#response-speed-budgets);
- screenshots, UI dumps, logcat, gateway stdout/stderr, and CCB project path
  stored under `/tmp` or a stable evidence directory;
- `flutter test`, focused local-backend tests, `flutter analyze`, and
  `git diff --check` passing.

## Test Environment Matrix

| Area | Required Local Configuration |
| :--- | :--- |
| Emulator | Fresh booted Android Emulator, default `emulator-5554` unless explicitly overridden. |
| App install | `flutter build apk --debug`, `adb install -r`, verified package `io.ccb.mobile.ccb_mobile`. |
| Backend | Disposable CCB project under `/home/bfly/yunwei/test_ccb2`, started through real CCB source CLI. |
| Gateway | `ccb mobile serve --listen 127.0.0.1:<fixed-port>`; no `0.0.0.0`, no Funnel, no public listener. |
| Bridge | `adb reverse tcp:<fixed-port> tcp:<fixed-port>` recorded before pairing and removed during cleanup unless a manual handoff requests keep-running. |
| Pairing | App claims the real gateway profile via QR/manual pairing payload; fake `demo` must not be the active project for P0. |
| Logs | Capture ADB logcat, UIAutomator XML, screenshots, gateway logs, CCB command stdout/stderr, and final JSON summary. |

## Response Speed Budgets

The local backend test should collect timing for every step. A single run must
meet the hard cap. A repeated run of at least five iterations should report
p50 and p95. These budgets are local-loopback budgets; future Tailnet/relay
budgets should be separate.

| Operation | Target | Hard Cap | Measurement |
| :--- | :--- | :--- | :--- |
| APK install + app launch to first usable screen | p50 <= 3s | 8s | `adb install` completion to focused `MainActivity` with project list visible. |
| Pairing claim and profile activation | p50 <= 1.5s | 5s | Claim button tap or QR result to paired runtime profile selected. |
| Project view load/refresh | p50 <= 500ms | 2s | Repository `getProjectView` call start to visible refreshed view. |
| Route diagnostics | p50 <= 1.5s | 5s | Check tap to `Route ready` or fail-closed result. |
| Focus agent/window | p50 <= 500ms | 2s | Tap agent/window to selected state and refreshed view. |
| Send tap to local visible user message | p50 <= 100ms | 300ms | Send button tap to `You` message visible with pending/sending/sent state. |
| Send tap to backend accepted | p50 <= 1s | 5s | Submit request start to accepted result from gateway. |
| Backend accepted to first agent reply visible | p50 <= 3s for deterministic backend | 15s | Accepted result to `Agent reply` containing expected marker. |
| Markdown reply render | p50 <= 500ms | 2s | Reply item returned to rendered Markdown body visible. |
| Small document upload, <= 1 MB | p50 <= 2s | 8s | Pick confirmation to uploaded attachment metadata in sent conversation. |
| Image upload, <= 5 MB | p50 <= 3s | 12s | Pick confirmation to uploaded image metadata and preview/chip visible. |
| Oversized rejection | p50 <= 100ms | 500ms | Pick result to visible rejection without draft loss. |
| Attachment download, <= 1 MB | p50 <= 2s | 8s | Download tap to saved/open feedback and bytes verified. |
| Backend-generated artifact download, <= 1 MB | p50 <= 2s | 8s | Agent-produced artifact chip/link tap to saved/open feedback and bytes/hash verified. |
| Terminal WebSocket open | p50 <= 1s | 5s | Open Terminal tap to live terminal view connected. |
| Terminal input echo | p50 <= 500ms | 3s | Send/paste action to expected terminal output visible. |
| Terminal reconnect | p50 <= 2s | 8s | Reconnect tap or dropped socket to usable terminal stream. |
| App background/foreground refresh | p50 <= 1s | 5s | Resume to current paired view and composer usable. |

If a budget fails because the deterministic backend fixture is missing or a
provider is non-deterministic, the run is blocked, not accepted.

## Functional Coverage

### 1. Install, Launch, Pairing, And Runtime Mode

- Build and install the current debug APK.
- Confirm package focus is `io.ccb.mobile.ccb_mobile/.MainActivity`.
- Start a real disposable CCB project and loopback gateway.
- Pair the app with the real gateway via QR/manual payload.
- Confirm active runtime is paired gateway.
- Confirm visible project id/agent set comes from the real CCB project, not
  `demo`.
- Restart the app and confirm the stored profile can reactivate the real
  gateway.
- Clear app data and confirm the profile is gone.

### 2. Project, Window, Agent, Focus, And Lifecycle

- Project list opens the real backend project.
- Window tabs match ProjectView windows.
- Agent switcher selects `mobile_probe` and `mobile_peer`.
- Focus calls use current namespace epoch and recover on stale epoch.
- Draft and scroll state are isolated per agent.
- Wake/open/close lifecycle actions run through backend and update status.
- Stop is confirmed in a separate throwaway run and never executed
  accidentally.

### 3. Native Text Chat Closure

P0 text chat is a full loop:

1. Enter unique body `native-mobile-echo:<id>` or a human prompt chosen for the
   real local agent.
2. Tap send.
3. UI immediately shows the user message as pending or sent.
4. Source/app evidence proves the default path did not call
   `/agents/{agent}/messages` and did not create an ask job.
5. The selected desktop pane or provider-native transcript shows exactly the
   user text, without `CCB_REQ_ID` or a mobile prefix.
6. The backend/provider produces a real reply in the same agent session.
7. App refreshes or streams the native conversation transcript.
8. UI shows the provider reply, not only a Comms compatibility card or
   completion snapshot.
9. The previous sent message remains visible.
10. Sending the same body twice preserves duplicate counts.
11. Retry after a forced failure never silently replays pane input.

This is the primary gate that was not proven by fake/local demo testing or by
the CCB ask/message-submit route.

### 4. Markdown, Content, History, And Artifacts

- Markdown reply renders heading, list, code span, link text, and plain text.
- Raw source or fallback body remains accessible.
- Existing content items remain readable after new sends.
- Terminal-history bubbles stay scrollable and do not bury newly sent content.
- Artifact/link metadata is visible when returned by backend.
- Backend-agent generated files are registered as mobile-downloadable
  resources with opaque ids, file names, MIME types, sizes, and optional
  hashes. The app must not require a raw host-local `file://` path or an
  unauthenticated public URL.
- Artifact links in Markdown or structured conversation payloads resolve to
  an in-app authenticated download action, not the generic blocked-link
  snackbar.
- Notification/deep-link opens the correct real agent/content target.

### 5. Attachments: Upload, Conversation, Download

- File picker cancel is no-op.
- Document upload: txt/md/pdf/doc-like file accepted, metadata returned by
  gateway, sent conversation shows attachment chip.
- Image upload: image file accepted, preview/chip visible, metadata returned.
- Attachment-only message can be sent and receives backend acknowledgement.
- Multi-attachment message respects max count and preserves accepted files.
- Oversized and unsupported files are rejected without losing existing draft.
- Backend reply can reference uploaded file metadata.
- Download from gateway saves exact bytes, shows feedback, and repeated taps
  during download do not start duplicate downloads.
- Open/download failure shows snackbar and leaves retry path visible.

### 5a. Backend-Agent Generated File Download

This lane covers the user's requirement that files produced by the backend CCB
agent can be downloaded to the phone from the conversation.

- Deterministic backend command `ccb-local-artifact:<id>` produces a small
  text or Markdown file and a small image or binary fixture owned by the
  selected agent.
- CCB source registers each generated artifact as a mobile-downloadable
  resource under the loopback gateway, with device-token authorization and
  project/agent scoping.
- The conversation route returns the generated file as either the existing
  attachment model or a structured artifact link that the app maps to the same
  download/open UX.
- The payload contains only opaque ids and metadata. It must not expose
  unrestricted host filesystem paths, workspace-relative paths that the phone
  cannot resolve, or unauthenticated public URLs.
- The app renders a visible chip/link for the generated file, downloads it
  through the authenticated gateway, saves it locally, shows success feedback,
  and verifies bytes or SHA-256 against source metadata.
- Revoked devices, invalid tokens, wrong project ids, wrong agent ids, and
  missing artifact ids fail closed with no partial file saved.

### 6. Raw Terminal And Pane-Backed Control

- Open Terminal is explicit, never opened by agent selection alone.
- Terminal token is minted by gateway after paired focus.
- WebSocket connects and renders live output.
- Send, paste, resize, reconnect, and token-renewal paths work.
- Terminal history resume cursor prevents replay gaps or duplicate stale input.
- Closing terminal returns to the chat workspace without losing draft or
  selected agent.

### 7. Route Diagnostics, Reconnect, And Failure Modes

- Health, device metadata, project view, focus, and terminal checks pass on
  loopback route.
- Removing `adb reverse` fails closed with actionable diagnostics.
- Killing gateway fails closed without fake success.
- Restarting gateway plus restoring reverse recovers after refresh/retry.
- Invalid token returns 401/permission error and no project data.
- Device revocation blocks project list, route diagnostics, terminal opening,
  message submit, file upload, and file download.
- Gateway remains loopback-only throughout the run.

### 8. UI, Keyboard, Layout, And Accessibility

- Phone portrait, phone landscape, and tablet/wide emulators render the same
  real backend state.
- Soft keyboard does not hide composer or send button.
- Hardware Enter behavior is explicit: configured send shortcut sends, newline
  behavior is documented and tested.
- Attachment button, send button, download button, terminal actions,
  diagnostics, profile, lifecycle, and notifications have stable semantics or
  keys for UIAutomator/test access.
- Long file names, long Markdown, and long terminal history do not overlap
  controls.

### 9. Persistence And App Lifecycle

- Background/foreground preserves paired profile, selected project, selected
  agent, draft, and pending attachment state.
- App process kill/restart reloads the stored profile and can refresh the real
  backend view.
- Pending sends either complete once or show a retryable failure; no duplicate
  backend submission from app resume.
- Downloaded files remain accessible from app documents/cache as designed.

## Test Automation Shape

Add or extend a runner such as:

```bash
tools/mobile_local_backend_comprehensive_smoke.py \
  --device-id emulator-5554 \
  --gateway-listen 127.0.0.1:18897 \
  --iterations 5 \
  --collect-artifacts /tmp/ccb-mobile-local-backend-<stamp>
```

The runner should:

1. create a disposable deterministic CCB project;
2. start CCB runtime;
3. start loopback-only `ccb mobile serve`;
4. install `adb reverse`;
5. build/install current debug APK;
6. clear app data for fresh-run tests;
7. pair and activate the real gateway profile;
8. execute P0 functional flows;
9. collect timing metrics and artifacts;
10. optionally leave the gateway alive only when `--keep-running` is passed;
11. always print a final JSON summary.

Repeated backend probe JSON can be aggregated with:

```bash
python tools/mobile_local_backend_latency_summary.py \
  /tmp/ccb-mobile-local-probe-run-*.json
```

This summary reports per-gate samples, p50, p95, max, and hard-cap status for
the backend capability probe. It is not a substitute for the AVD UI timing
lane, but it is the accepted format for the source/gateway response-speed
evidence.

### Landed Capability Preflight

The first executable preflight is:

```bash
python tools/mobile_local_backend_capability_probe.py \
  --gateway-url http://127.0.0.1:18897 \
  --pairing-code <pairing-code> \
  --agent mobile_probe \
  --reply-timeout 15 \
  --include-revoke-gate
```

This probe is not the full AVD matrix. It is the gate that prevents false
acceptance before the UI runner is expanded. It records pass/fail/blocked
status and timing for:

- gateway health;
- pairing claim;
- authenticated project view and namespace epoch;
- selected-agent message submit through the real gateway;
- deterministic `agent_reply` marker visibility in conversation;
- file upload route used by the mobile app;
- file download route and exact byte verification;
- optional device revoke fail-closed coverage: revoke the claimed device, then
  verify `/v1/devices/me`, ProjectView, message submit, terminal open, and
  downloaded file routes reject the old token;
- backend-agent generated artifact registration/download and exact byte or
  SHA-256 verification.

The probe must be run against a real loopback `ccb mobile serve` gateway. A
fake `demo` project or app-local repository cannot satisfy it.

Current implementation status:

- source file upload/download routes are present and have source unit coverage;
- source ProjectView/conversation now preserves mobile attachment metadata for
  the app download chip;
- source worktree `d0da183a` registers deterministic backend-agent generated
  text and PNG artifacts as mobile-downloadable resources and returns them as
  conversation attachments plus `ccb-artifact://<file_id>` links;
- deterministic backend reply is currently achieved by the source `fake`
  provider in the attachment lane, which is acceptable for repeatability
  because the app still pairs with and talks to the real source gateway;
- the deterministic Markdown fixture exists and has source dispatcher plus AVD
  UI evidence;
- document and image upload/download have real-local AVD evidence;
- backend-agent generated artifact download still needs real-local AVD
  click/download evidence; reconnect failure lanes, 5-run latency evidence,
  and AVD UI timing still need to be added before the matrix can be marked
  complete;
- the capability probe has an optional revoke fail-closed gate and the latency
  summary tool exists, but neither has yet been run as accepted five-run or AVD
  evidence against a fresh real-local matrix.

The JSON summary should include:

- commit hash and APK build timestamp;
- emulator id and Android API;
- project root, project id, agents, windows, namespace epoch;
- gateway URL, route provider, adb reverse mapping;
- pass/fail per gate;
- timing samples per operation;
- p50/p95/hard-cap status;
- artifact paths;
- cleanup status.

## Manual Handoff Mode

For user hand testing, the runner may support `--keep-running-manual`:

- leaves CCB runtime, gateway, and adb reverse alive;
- installs and launches the app;
- ensures the app is in paired gateway mode before returning;
- prints the gateway URL, project root, pairing status, expected test agent,
  and exact manual test checklist;
- verifies the gateway process is still alive after returning.

This mode must not claim automated completion; it is only a handoff state for
interactive debugging.

## Required Evidence Per Accepted Run

- Final JSON summary from the local-backend runner.
- Screenshot before send, after user message, and after agent reply.
- UIAutomator XML for those three states.
- Logcat excerpt around send/upload/download/terminal operations.
- Gateway stdout/stderr excerpt.
- CCB project path and `.ccb` socket path.
- Uploaded/downloaded test file hashes.
- Backend-generated artifact ids and hashes, plus downloaded local paths.
- Timing table with p50/p95/hard-cap pass/fail.
- Cleanup proof: adb reverse removed unless manual keep-running was requested;
  runtime killed/unmounted for normal automated runs.

## Relationship To Existing Plans

- [android-emulator-comprehensive-test-plan.md](android-emulator-comprehensive-test-plan.md)
  remains the accepted app/UI regression matrix and fake/local persistence
  guard.
- This plan is the new local real-backend authority for chat closure, response
  speed, mobile-uploaded attachment download, backend-agent generated artifact
  download, route diagnostics, lifecycle, terminal, reconnect, and revoke
  behavior.
- Physical phone/iPad Tailnet validation should not replace this plan; it
  should run after this local real-backend matrix is green and should reuse the
  same functional gates with Tailnet-specific latency budgets.

## Open Implementation Questions

- Should the source `fake` provider become the canonical deterministic local
  matrix fixture for text/Markdown/image lanes, or should a dedicated
  mobile-probe provider command be added?
- Should local chat closure use pane-backed terminal input only, the mobile
  message route, or both while Decision 015/016 are reconciled with current
  gateway behavior?
- For P0 attachment closure, should image upload/download be a separate lane
  with image MIME and preview assertions, or is document-plus-download enough
  for first alpha while image stays P1?
- Which exact hard caps should fail CI versus only warn in manual AVD runs?
- Where should persistent evidence live when `/tmp` is insufficient for longer
  repeated latency runs?
