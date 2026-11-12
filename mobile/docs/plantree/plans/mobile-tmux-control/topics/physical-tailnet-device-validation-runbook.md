# Physical Tailnet Device Validation Runbook

Date: 2026-06-27
Status: Executable hardening lane; environment currently blocked
Read with:
[app-stress-and-performance-test-plan.md](app-stress-and-performance-test-plan.md),
[app-local-avd-full-acceptance-matrix.md](app-local-avd-full-acceptance-matrix.md),
[app-real-avd-stress-casebook.md](app-real-avd-stress-casebook.md), and
[tailscale-tailnet-stable-route.md](tailscale-tailnet-stable-route.md).

## Purpose

Define the physical Android phone + Tailnet validation lane for CCB Mobile.
The local AVD track proves the server-wide gateway, native pane conversation,
file transfer, recovery, and power behavior on loopback plus `adb reverse`.
This lane proves the same product behavior over a private Tailnet route on a
real Android phone.

This lane is not a replacement for the local AVD acceptance matrix. It is the
remaining remote-device hardening path before claiming the full remote-control
goal across physical networking conditions.

## Safety Boundary

The validation must preserve the same security boundary as the local gateway:

- `ccb mobile serve` or `ccb install mobile` keeps the CCB gateway
  loopback-only.
- Tailscale Serve exposes only the loopback gateway inside the Tailnet.
- Do not use Tailscale Funnel.
- Do not bind CCB Mobile gateway to `0.0.0.0`.
- Do not store Tailscale passwords, OAuth tokens, admin API tokens, or grants.
- Do not automatically change Tailnet ACLs/grants.
- Use disposable real CCB test projects under `/home/bfly/yunwei/test_ccb2`
  for send, upload, and destructive recovery actions.

## Preflight

Run the read-only preflight before any manual phone smoke:

```bash
PATH="/home/bfly/.local/share/android-sdk/platform-tools:$PATH" \
  tools/mobile_physical_tailnet_preflight.py \
  --gateway-url https://<ccb-host>.<tailnet>.ts.net:8787 \
  --json-out /tmp/ccb-mobile-physical-tailnet-preflight.json
```

Pass:

- `status` is `ok`;
- at least one online non-emulator Android device is attached;
- Android reports `sys.boot_completed=1`;
- host `tailscale status --json` reports `BackendState: Running`;
- `tailscale serve status` shows the same public HTTPS port as
  `--gateway-url` and a loopback origin such as `127.0.0.1`;
- `/v1/health` through the Tailnet HTTPS URL returns an ok response.

Current environment note:

- 2026-06-27 preflight is blocked by environment, not by app code:
  [../history/physical-tailnet-preflight-blocked-20260627.json](../history/physical-tailnet-preflight-blocked-20260627.json)
  records no online Android device and no `tailscale` binary on PATH.

## Required Evidence Packet

Initialize the artifact directory before the physical run:

```bash
tools/mobile_physical_tailnet_evidence_init.py \
  /tmp/ccb-mobile-physical-tailnet-<timestamp>/
```

This creates `summary.json` with T0-T6 marked `pending`, plus the screenshot
and UI dump directories. It does not create passing evidence; the audit still
fails until the real run fills the required files and each case result is
marked `ok`, `passed`, or `pass`.

Collect the read-only T0 environment and preflight evidence into that same
directory:

```bash
PATH="/home/bfly/.local/share/android-sdk/platform-tools:$PATH" \
  tools/mobile_physical_tailnet_environment_collect.py \
  /tmp/ccb-mobile-physical-tailnet-<timestamp>/ \
  --gateway-url https://<ccb-host>.<tailnet>.ts.net:8787
```

This writes `preflight.json` and `environment.json`, including app/source git
state plus `adb` and Tailscale command output. It is read-only; it does not
install Tailscale, run `tailscale up`, start Serve, or change gateway state.

After each case, record the case result with at least one evidence file:

```bash
tools/mobile_physical_tailnet_case_record.py \
  /tmp/ccb-mobile-physical-tailnet-<timestamp>/ \
  T0 \
  --status ok \
  --evidence preflight.json \
  --evidence environment.json
```

Accepted case statuses require evidence paths. The tool keeps the overall
`summary.json` status `pending` until every T0-T6 case is accepted; a blocked
or failed case keeps the packet non-acceptable for the final audit. Evidence
paths must be relative to the artifact directory and must already exist there;
absolute paths or `..` escapes are rejected. Empty files and empty directories
do not count as case evidence.

Each run writes a directory such as:

```text
/tmp/ccb-mobile-physical-tailnet-<timestamp>/
  summary.json
  preflight.json
  environment.json
  projects.json
  phone-screenshots/
  phone-ui/
  gateway-health.json
  route-diagnostics.json
  timings.json
  request-counts.json
  memory.json
  power.txt
  logcat.txt
  gateway.log.tail
  source-project.log.tail
  transfer-hashes.json
  recovery-events.json
```

After collecting the packet, run:

```bash
tools/mobile_physical_tailnet_evidence_audit.py \
  /tmp/ccb-mobile-physical-tailnet-<timestamp>/ \
  --json-out /tmp/ccb-mobile-physical-tailnet-<timestamp>/audit.json
```

The audit must return `status: ok` before this physical Tailnet lane can be
accepted. It checks required files/directories, JSON parseability, preflight
success, `summary.json` T0-T6 case coverage, Tailnet route provider evidence,
non-emulator device evidence, file hash matches, recovery replay markers, and
obvious failure strings such as `CCB_REQ_ID`. Accepted T0-T6 case evidence
paths are also checked for safety, existence, and non-empty content inside the
artifact directory. T5/T6 are semantic gates, not only file-presence gates:
`timings.json` must include at least five turns with own-message latency,
provider-reply latency, and direct/DERP/relay path evidence; `request-counts.json`
must explicitly prove `blind_polling_seen: false`; `memory.json` must include at
least two samples and stay within the debug stress budget; `recovery-events.json`
must include multiple recovery events and `input_replayed: false`; `power.txt`
must show idle wake-lock zero evidence.

When that audit passes, copy or commit the final audit JSON into the plan-tree
history as:

```text
docs/plantree/plans/mobile-tmux-control/history/physical-tailnet-final-audit.json
```

The final audit must be generated by the current physical stress evidence
auditor and include `requirements_version: physical-tailnet-stress-v2`; older
`status: ok` audit files are intentionally rejected by the acceptance evidence
audit because they may not include the T5/T6 semantic checks above.

`tools/mobile_acceptance_evidence_audit.py` treats this file as the physical
Tailnet closure evidence. If it is absent, the overall audit remains blocked by
the preflight lane. If it is present but not clean `status: ok`, the overall
audit fails.

Minimum environment fields:

- app commit, dirty state, build mode, APK path;
- source worktree path, commit, dirty state;
- Tailnet hostname and route provider;
- `tailscale status`, `tailscale ping <phone>`, and `tailscale netcheck`;
- gateway listen URL and public Tailnet URL;
- attached Android serial, model, API level, and VPN state evidence;
- selected `/home/bfly/yunwei/test_ccb2` project roots and agent pane
  evidence.

## Cases

### T0. Physical Device And Tailnet Readiness

Goal: prove the test host and phone are ready for a real remote route.

Actions:

1. Run the preflight above.
2. Record `adb devices -l`.
3. Record `tailscale status --json`.
4. Record `tailscale ping <phone-or-ipad-name>`.
5. Record `tailscale netcheck`.

Pass:

- preflight `status: ok`;
- phone is not an emulator;
- phone and host are in the same Tailnet;
- connection path is recorded as direct or DERP/relay;
- gateway `/v1/health` succeeds through the Tailnet URL.

### T1. Server-Wide Pairing And Project List

Goal: prove the phone reaches the server-wide mobile gateway over Tailnet.

Actions:

1. Start `ccb install mobile` or the current server-wide gateway flow.
2. Publish the loopback gateway with
   `tailscale serve --bg --https=8787 http://127.0.0.1:8787`.
3. Pair the phone through the Tailnet QR/profile.
4. Open the app project list and use the refresh button.
5. Compare the phone list with `/v1/projects`.

Pass:

- profile route provider is `tailnet`;
- all mounted healthy server projects appear;
- stale/unreachable projects degrade without blocking the list;
- no `demo`/fake fallback is visible while paired to the server gateway.

### T2. Pane-Equivalent Conversation

Goal: prove physical phone input is still equivalent to direct pane typing.

Actions:

1. Open a disposable test project under `/home/bfly/yunwei/test_ccb2`.
2. Select `mobile_probe`.
3. Send a deterministic prompt from the phone.
4. Inspect the desktop pane and source logs.
5. Wait for the provider reply and refresh only through allowed active-send or
   explicit refresh behavior.

Pass:

- desktop pane receives exactly the typed text;
- no `CCB_REQ_ID`, ask-job envelope, `mobile_gateway`, or device prefix is
  present;
- the provider reply appears in the selected phone timeline;
- ordinary bubbles do not show internal provenance labels such as
  `completion_snapshot` or provider cache names.

### T3. Desktop-Origin Sync And History

Goal: prove the phone is a renderer for the same agent pane, not only a send
client.

Actions:

1. Type a marker directly into the desktop agent pane.
2. Leave the phone untouched for 30 seconds and record request counts.
3. Trigger explicit selected-agent refresh.
4. Scroll upward to load older history.
5. While scrolled away, add a desktop-origin turn and refresh again.

Pass:

- desktop-origin content appears only after an allowed refresh trigger;
- idle request counts do not show blind polling;
- older history prepends in chronological order;
- scrolled-away refresh does not jump unexpectedly or replace current turns
  with stale ask/job records.

### T4. Files And Backend Artifacts

Goal: prove user-origin and agent-origin files work over Tailnet.

Actions:

1. Upload a small Markdown file and a small image from the phone.
2. Upload or reject a near-limit file according to the product limit.
3. Ask the agent to create a deterministic artifact in the test project.
4. Download every visible file/artifact to the phone.
5. Record source-side and phone-side SHA256 values.

Pass:

- upload progress does not get stuck;
- rejected files show a reason and do not poison later sends;
- artifact links use authenticated opaque ids, not host filesystem paths;
- downloaded bytes match the source artifact or stored upload;
- repeated downloads do not create duplicate source artifacts.

### T5. Tailnet Recovery

Goal: prove remote connection loss and restore are safe.

Actions:

1. Turn off the phone Tailscale VPN.
2. Refresh project list and selected-agent conversation.
3. Turn VPN back on.
4. Refresh again.
5. Stop and restart `tailscale serve`.
6. Restart the mobile gateway on the same state directory.
7. Revoke and re-pair the device.

Pass:

- failures are visible and recoverable;
- drafts are preserved;
- no input is replayed after reconnect;
- selected project and profile recover without app reinstall;
- revoked credentials fail closed until re-pair.

### T6. Performance, Power, And Soak

Goal: prove the physical route is stable enough for daily remote-control use.

Actions:

1. Run a 10-minute selected-agent idle soak.
2. Run a 30-minute idle soak if the 10-minute gate is clean.
3. During active conversation, record prompt-to-visible-own-message and
   prompt-to-provider-reply timings for at least five turns.
4. Record memory, CPU/top, wake locks, and logcat before and after.

Pass:

- idle request rate remains operation-driven, not timer-driven;
- no app-held wake locks remain during idle;
- no FATAL/ANR/OOM appears;
- memory growth stays within the stress-plan budget;
- latency records include whether Tailscale was direct or DERP/relay.

## Stop Conditions

Stop and collect evidence if any of these occur:

- phone falls back to fake/demo mode;
- a send appears in the wrong project or wrong agent pane;
- `CCB_REQ_ID`, ask metadata, or `mobile_gateway` appears in ordinary chat;
- timeline visibly jumps, flickers, or alternates stale/current histories;
- upload/download is permanently stuck;
- Tailnet recovery replays a previous input;
- app process dies, ANR/OOM appears, or wake locks remain after idle.

## Completion Rule

This lane is complete only when T0-T6 pass on an attached physical Android
phone through a Tailnet route, with artifacts linked from
[../history/evidence-index.md](../history/evidence-index.md). Local AVD,
Cloudflare, or loopback evidence cannot close this lane.
