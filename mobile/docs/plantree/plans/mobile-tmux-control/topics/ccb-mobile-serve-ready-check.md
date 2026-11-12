# CCB Mobile Serve Ready-Check

Date: 2026-06-18
Status: Named-tunnel preflight landed; named/cellular smoke next

## Purpose

This ready-check answers the source-boundary questions from
[gateway-contract-checkpoint.md](gateway-contract-checkpoint.md) before adding
`ccb mobile serve` or mobile gateway code under
`/home/bfly/yunwei/ccb_source`.

The original outcome was deliberately narrow: it opened only the first
loopback, current-project gateway skeleton package. G2 has since added the
pairing/device-token foundation, authenticated focus routes,
terminal-open/token foundation, terminal WebSocket/PTy streaming foundation,
paired-gateway terminal UI wiring, isolated gateway terminal smoke, and
window-level terminal/focus UI. QR camera pairing has now landed on the app
side, gateway terminal reconnect/resume cursor support has landed, app-side
route diagnostics now exist, and the remaining developer SSH diagnostic
runtime has been removed after gateway-only smoke covered equivalent terminal
validation. Source public route metadata and tunnel-aware smoke tooling have
also landed. Live Cloudflare Tunnel smoke, content, notification, lifecycle,
and multi-project registry work remain later packages behind the same
boundary.

## Landed G1 Evidence

CCB source commit `bcee866e` landed the G1 loopback current-project gateway
skeleton in `/home/bfly/yunwei/ccb_source`.

Landed scope:

- normal phase2 CLI route for `ccb mobile serve`;
- loopback-only listen validation with default `127.0.0.1:8787`;
- current-project `GET /v1/health`, `GET /v1/projects`, and
  `GET /v1/projects/{project_id}/view`;
- `CcbdClient` backed health/project/view data;
- mobile state path properties under `PathLayout(project_root).ccbd_dir /
  "mobile"`;
- ProjectView gateway responses redact `namespace.socket_path` and
  `namespace.session_name`;
- focused source tests for gateway service, parser, render, router, and
  phase2 dispatch.

App-side Flutter HTTP transport and repository wiring landed in mobile commit
`aaec0ad`. G2 then moved to pairing/device-token source and app import work.

## Landed G2 Evidence

CCB source commit `55c26078` landed the first pairing/device-token foundation
in `/home/bfly/yunwei/ccb_source`. Mobile app commit `d01a338` landed the
matching claim-response import and secure host-profile storage.

Landed source scope:

- startup `ccb mobile serve` summary emits a short-lived pairing code;
- pairing codes are stored only as hashes in `.ccb/ccbd/mobile/pairing-tokens.jsonl`;
- claimed devices are stored in `.ccb/ccbd/mobile/devices.json` with device
  token hashes, scopes, route metadata, and revocation state;
- `POST /v1/pairing/claim` returns the one-time device token and host profile;
- bearer-token `GET /v1/devices/me` verifies stored device tokens;
- `POST /v1/devices/{device_id}/revoke` supports self-revoke;
- audit metadata is appended to `.ccb/ccbd/mobile/audit.jsonl` without token
  plaintext or terminal bytes.

Landed app scope:

- `GatewayPairingPayload` parses QR/manual pairing payloads;
- `GatewayPairingClient` claims a pairing code over HTTP;
- `GatewayHostProfileStore` persists the paired profile and device token
  through `flutter_secure_storage`;
- `HttpGatewayTransport` can inject the stored bearer token without putting it
  into `GatewayHostProfile`.

Authenticated focus-agent/window routes landed in source commit `88f0b568`,
and the Flutter app transport/repository wiring landed in mobile commit
`ba2d51e`. Flutter pairing/profile UI and explicit runtime-mode selection
landed in mobile commit `6359df1`. Terminal-open/token foundation landed in
source commit `dfcb7af7`, and app terminal-open handle parsing landed in
mobile commit `faa3039`. Terminal WebSocket/PTy streaming foundation landed in
source commit `8ce445f1`, and app terminal frame transport landed in mobile
commit `f3e2d78`. Paired-gateway terminal UI wiring landed in mobile commit
`5b3c985`. Isolated gateway terminal smoke landed in mobile commit `03c6925`
after source focus fix `0ac903f4`. Window-level terminal/focus UI landed in
mobile commit `92312e0`. QR camera pairing landed in mobile commit `b3f03ab`.
Release builds hid developer SSH in mobile commit `2590a97`; mobile commit
`4b43a4f` later removed that diagnostic runtime entirely after gateway-only
terminal smoke covered the validation use case. Gateway terminal resume cursor
support landed in source commit `300f1f80` and mobile commit `3bebca4`.
App-side route diagnostics landed in mobile commit `b9555a9`.
Source public route metadata landed in source commit `a222446c`, and the
tunnel-aware mobile smoke harness landed in mobile commit `08eed72`. The next
source hardening package added host-side device list/revoke in source commit
`8a264cae`. Source commit `c3c7fd1b` then added user-facing Cloudflare Alpha
setup docs and README entry links. Mobile commit `4f41391` added a
named-tunnel preflight, and source commit `44ba9edd` documented it. Mobile
commit `6f26591` then made preflight hostname-aware with local self-tests, and
source commit `973a2707` documented multi-ingress matching. Mobile commit
`1c2d4de` added automated named-tunnel smoke startup, and source commit
`444b648c` documented it. Mobile commit `eadcece` added blocked-preflight
`next_actions`, and source commit `9ce07104` documented that checklist.
Mobile commit `de79cde` added a side-effect-free `config_template` draft to
the same preflight JSON, source commit `a2ac6f1e` documented it, and mobile
commit `2ff36a9` added round-trip self-test coverage for the generated draft;
mobile commit `11bae28` and source commit `69891f03` then made
`--cloudflared-tunnel-name <name>` consistent across setup guidance and
automated smoke handoff; mobile commit `e1e14a2` and source commit `867300d7`
then made fixed loopback `--gateway-listen` a named-tunnel preflight
requirement; mobile commit `3f0a0b5` and source commit `8e047913` then added
copyable `named_tunnel_smoke_command` handoff; mobile commit `434ed01` and
source commit `93c0de50` added manual cloudflared and already-running tunnel
smoke command handoff;
named-tunnel or cellular validation remains required before broad public or
other non-loopback exposure.

## Landed Cloudflare Smoke Harness Evidence

CCB source commit `a222446c` added the route metadata required for Cloudflare
Tunnel pairing:

- `ccb mobile serve --public-url <http-or-https-url>`;
- `ccb mobile serve --route-provider lan|tailnet|cloudflare_tunnel|relay`;
- CLI summary output for `gateway_url` and `route_provider`;
- validation that `--public-url` is an absolute HTTP(S) URL;
- loopback listen validation remains the network exposure boundary.

Mobile app commit `08eed72` added the matching repeatable smoke path:

- named tunnel mode passes `--gateway-public-url` and
  `--route-provider cloudflare_tunnel`;
- development mode can start `cloudflared tunnel --url
  http://127.0.0.1:<port>` and use the generated `*.trycloudflare.com` URL;
- the Dart smoke asserts the claimed route provider, runs
  `GatewayRouteDiagnostics`, then proves terminal output/input/paste/resize,
  close, and reconnect through the same gateway terminal transport.

Local verification has covered the loopback path and a live quick-tunnel
terminal smoke. App commit `a8eeec0` added a smoke-only public DNS override for
generated quick-tunnel hostnames, then proved Cloudflare public `/v1/health`,
route diagnostics, terminal output/input/paste/resize/close/reconnect, and
cleanup through the tunnel. This host's system resolver still returns NXDOMAIN
for generated `*.trycloudflare.com` names, so the next public-route gate is
Cloudflare alpha hardening plus named-tunnel or cellular validation.

Source commit `8a264cae` added the first Cloudflare alpha revoke hardening:

- `ccb mobile devices` lists paired devices from local mobile state;
- `ccb mobile revoke <device_id>` revokes lost devices locally without adding
  a public HTTP admin route;
- device revoke cascades to still-open terminal handles;
- terminal token auth checks owning-device revocation;
- focused source tests and the mobile loopback gateway smoke passed against
  the updated source.

Source commit `c3c7fd1b` added the initial Cloudflare Alpha setup docs:

- English and Chinese guides under `docs/mobile-cloudflare-alpha*.md`;
- README entry links;
- named-tunnel setup shape, loopback gateway command, pairing instructions,
  local device list/revoke commands, safety notes, and official Cloudflare
  documentation links.

The setup path is now documented outside plan-tree. The remaining alpha gate
is evidence from a named tunnel or equivalent cellular run.

Mobile commit `4f41391` added a named-tunnel preflight to the smoke harness:

- checks the `cloudflared` binary and version;
- checks `~/.cloudflared/config.yml`;
- checks configured tunnel and credentials-file presence;
- checks the requested public URL, `cloudflare_tunnel` route provider, and
  loopback origin/listen port match;
- exits before starting disposable CCB runtime.

Source commit `44ba9edd` documented that preflight command in both setup
guides. Mobile commit `6f26591` made the preflight select the ingress
`hostname` matching `--gateway-public-url` and added self-tests for missing
config, matching hostname, wrong origin port, and missing hostname. Source
commit `973a2707` documented that multi-ingress behavior. This local
environment still lacks `/home/bfly/.cloudflared/config.yml`,
`/home/bfly/.cloudflared/cert.pem`, and Cloudflare account/domain credentials.

Mobile commit `1c2d4de` then added `--cloudflared-named-tunnel` so the same
smoke harness can run preflight, start `cloudflared tunnel run`, wait for a
registered tunnel connection, run public health/route diagnostics/terminal
streaming, and clean up owned processes. Source commit `444b648c` documents
the automated path in both setup guides.

Mobile commit `eadcece` added `next_actions` to preflight output, and source
commit `9ce07104` documents it. Mobile commit `de79cde` added
`config_template`, source commit `a2ac6f1e` documents it, and mobile commit
`2ff36a9` tests that the generated draft can round-trip to an ok local
preflight. Mobile commit `11bae28` makes the same preflight honor
`--cloudflared-tunnel-name <name>` in setup commands and success handoff.
Mobile commit `e1e14a2` blocks dynamic or non-loopback gateway listen values
before they can produce invalid named-tunnel ingress guidance. Mobile commit
`3f0a0b5` adds the exact `named_tunnel_smoke_command` to run after those setup
fixes. Mobile commit `434ed01` adds the matching `cloudflared_run_command`
and `existing_tunnel_smoke_command` for operators who manage `cloudflared`
outside the harness. This turns the current local missing Cloudflare config
state into a concrete command/config checklist plus a copy-ready config draft
that still requires real tunnel and credentials values.

## Landed Authenticated Focus Evidence

Landed source scope:

- `POST /v1/projects/{project_id}/focus-agent`
- `POST /v1/projects/{project_id}/focus-window`
- both routes require a bearer device token with `focus` scope;
- both routes call existing ccbd `project_focus_agent` /
  `project_focus_window` through `CcbdClient`;
- both routes refresh ProjectView after focus and redact tmux socket/session
  evidence before returning it to the app.

Landed app scope:

- `HttpGatewayTransport.focusAgent` and `focusWindow` call the new POST
  routes;
- the stored device token is injected only as an Authorization header;
- `GatewayMobileCcbRepository` now delegates focus through the gateway
  transport and receives refreshed redacted ProjectView.

## Landed App Runtime Mode Evidence

Mobile app commit `6359df1` landed the first pairing/profile UI and explicit
runtime mode switch:

- manual gateway URL + pairing code form uses `GatewayPairingClient` and
  `GatewayHostProfileStore`;
- stored paired profiles can activate a `GatewayMobileCcbRepository`;
- runtime modes are explicit: fake and paired gateway;
- paired gateway mode uses agent taps for authenticated focus and does not try
  to open terminal PTY before gateway terminal routes exist.

## Landed Terminal-Open Token Evidence

CCB source commit `dfcb7af7` landed the first terminal-open/token foundation:

- `POST /v1/projects/{project_id}/terminals`;
- default pairing scopes now include `terminal_input`;
- the route requires a bearer device token with `terminal_input` scope;
- the gateway validates project id, namespace epoch, target kind, and
  agent/window identity through unredacted ProjectView before minting a token;
- terminal tokens are stored only as hashes under
  `.ccb/ccbd/mobile/terminal-tokens.jsonl`;
- terminal-open audit records metadata only and does not include token
  plaintext, terminal input bytes, pasted text, or output bytes;
- terminal-open responses include terminal id, short-lived token, expiry,
  WebSocket URL, target epoch, and target summary without exposing tmux
  socket/session paths.

Mobile app commit `faa3039` landed the matching app-side handle parser:

- `HttpGatewayTransport.openTerminal` POSTs the existing
  `GatewayTerminalOpenRequest` shape to the new source route;
- the stored device token is injected only as an Authorization header;
- the parser requires terminal id/token/expiry/WebSocket URL/target summary;
- at that checkpoint, `terminalFrames` and `sendTerminalFrame` remained
  fail-closed; source commit `8ce445f1` and app commit `f3e2d78` later landed
  frame streaming.

## Landed Terminal WebSocket/PTy Evidence

CCB source commit `8ce445f1` landed the first gateway-owned terminal
WebSocket/PTy streaming foundation:

- `GET /v1/terminals/{terminal_id}` upgrades to a route-agnostic WebSocket
  terminal stream;
- the first client frame must be `open` with terminal id and terminal token;
- terminal tokens are validated against hashed records before creating a tmux
  attach client;
- ProjectView namespace epoch and agent/window target identity are revalidated
  before attach;
- the gateway opens a server-side `tmux -S <socket> attach-session -t
  <session>` client and does not expose socket/session paths to the app;
- output/input/paste/resize/closed/error JSON frames are routed through the
  stream;
- input and paste frames require monotonic sequence numbers, preventing stale
  replay;
- close is client-scoped and closes only the mobile attach stream.

Mobile app commit `f3e2d78` landed the matching app-side WebSocket transport:

- `GatewayTerminalFrame.fromJson` parses gateway frames;
- `HttpGatewayTransport.terminalFrames` connects to the terminal WebSocket and
  emits the required `open` frame;
- `sendTerminalFrame` sends input/paste/resize/closed frames over the active
  socket;
- disconnected sends fail closed;
- local Dart WebSocket tests prove open/output/input/paste/resize/close frame
  behavior.

## Landed Paired Gateway Terminal UI Evidence

Mobile app commit `5b3c985` landed the first paired-gateway terminal UI
integration:

- paired gateway mode creates an injected `GatewayTerminalTransport` backed by
  `HttpGatewayTransport`;
- manual pairing requests `view`, `focus`, and `terminal_input` scopes;
- tapping an agent in paired gateway mode first calls authenticated focus, then
  opens the existing terminal screen with `TerminalOpenRequest.gateway`;
- `GatewayTerminalTransport` opens a terminal handle, subscribes to gateway
  frames, maps output bytes into `TerminalSession.output`, and sends input,
  paste, resize, and close frames through `sendTerminalFrame`;
- at that checkpoint, reconnect remained fail-closed until a resume cursor was
  designed;
- widget/transport coverage proves the app no longer tries to build direct
  tmux attach commands from redacted paired-gateway ProjectView data.

## Landed Isolated Gateway Terminal Smoke Evidence

Source commit `0ac903f4` fixed a real smoke blocker in
`/home/bfly/yunwei/ccb_source`: `project_focus_agent` now selects the pane
found by CCB pane options instead of first selecting a tmux window named after
the logical CCB window. This preserves the existing `focus-window` behavior
while allowing projects whose actual tmux window is still `ccb` and whose CCB
logical window is stored as `@ccb_window=main`.

Mobile app commit `03c6925` landed the matching repeatable smoke:

- `tools/mobile_gateway_terminal_smoke.py` creates a disposable project under
  `/home/bfly/yunwei/test_ccb2`, starts source CCB with `mobile_probe`, starts
  `ccb mobile serve --listen 127.0.0.1:0`, captures the pairing summary without
  logging the pairing code in sanitized output, runs the Dart smoke, and kills
  the disposable runtime unless `--keep-running` is requested;
- `app/tool/gateway_terminal_smoke.dart` claims pairing, builds
  `HttpGatewayTransport`, reads health/projects/ProjectView, focuses the
  selected agent, opens `GatewayTerminalTransport`, verifies the redacted
  gateway target has no direct tmux evidence, streams output, sends input,
  paste, and resize frames, closes the stream, and at that checkpoint asserted
  reconnect failed closed until a resume cursor contract existed;
- `GatewayPairingClient` and `HttpGatewayTransport` now set explicit
  `Content-Length` for JSON POST bodies because the current source gateway
  JSON reader depends on content length rather than chunked request bodies.

Latest smoke evidence:

- command: `tools/mobile_gateway_terminal_smoke.py`
- status: `ok`
- project root:
  `/home/bfly/yunwei/test_ccb2/ccb-mobile-gateway-smoke-20260618095356`
- selected agent/window: `mobile_probe` / `main`
- namespace epoch: `1`
- `target_has_direct_tmux_evidence: false`
- `output_bytes_seen: 5476`
- `input_sent: true`, `paste_sent: true`, `resize_sent: true`
- `close_completed: true`
- `reconnect_failed_closed: true`
- cleanup: gateway process terminated and `ccb kill -f` returned `kill_status:
  ok`

## Landed Window-Level Terminal UI Evidence

Mobile app commit `92312e0` landed the first window-level terminal/focus entry:

- `CcbProjectView.terminalTargetForWindow` maps configured windows to stable
  `window_active_pane` terminal targets with namespace epoch and optional
  active pane evidence;
- the gateway terminal-open request serializes the window target as
  `kind: window_active_pane`, `window`, and optional `pane_id`, while still
  omitting tmux socket/session evidence;
- `FakeTerminalScreen` now accepts exactly one terminal identity: agent or
  window;
- the project home screen renders windows separately from agents and uses a
  window tap surface instead of pretending a window is an agent;
- paired gateway mode calls authenticated `focusWindow`, refreshes the view,
  and then opens the existing gateway terminal transport for the selected
  window;
- fake and developer-SSH modes can open a window target through the existing
  terminal screen path.

## Landed QR Camera Pairing Evidence

Mobile app commit `b3f03ab` landed QR camera pairing for the existing
paired-gateway onboarding path:

- the app reuses `mobile_scanner` 7.2.0 for QR detection instead of building
  camera/barcode logic from scratch;
- Android declares `CAMERA`, and iOS declares `NSCameraUsageDescription`;
- `GatewayPairingPayload.fromQrText` parses the source gateway pairing JSON
  payload emitted by `create_pairing_payload`;
- the Pair Gateway panel opens a scanner, fills the scanned gateway URL/code
  for operator visibility, and auto-claims through the existing
  `GatewayPairingClient` / `GatewayHostProfileStore` path;
- focused tests cover source-shaped QR payload parsing, malformed QR rejection,
  and scan-to-claim profile storage.

## Landed Release Developer SSH Gate Evidence

Mobile app commit `2590a97` narrowed developer SSH to a non-release diagnostic
surface:

- `ProjectHomeScreen` defaults `allowDeveloperSsh` to `!kReleaseMode`;
- release builds omit the SSH runtime segment and Developer SSH profile panel;
- disabled SSH attempts fail closed with a snack instead of creating
  `SshTerminalTransport`;
- widget tests can still explicitly enable developer SSH to preserve isolated
  local validation coverage while paired-gateway QR onboarding remains the
  user-facing path.

Mobile app commit `4b43a4f` then removed the diagnostic runtime after
gateway-only smoke covered equivalent terminal validation:

- runtime mode selection now exposes only fake and paired gateway;
- `SshTerminalTransport`, the SSH direct smoke tool, and SSH transport tests
  were deleted;
- `dartssh2` and SSH-only transitive dependencies were removed from the app
  lockfile;
- live terminal control remains on the paired-gateway WebSocket path.

## Landed Gateway Terminal Resume Cursor Evidence

Source commit `300f1f80` and mobile app commit `3bebca4` landed the first
gateway terminal reconnect/resume cursor package:

- terminal handles now store `last_output_seq` and disconnected state in the
  source gateway token record;
- transport disconnect marks the terminal as disconnected without closing the
  handle, while explicit close and protocol errors still close the handle;
- reconnect requires a matching `resume_cursor`, clears disconnected state on
  success, and rejects missing or stale cursors with explicit error codes;
- terminal open acks include `resume_cursor` and `last_input_seq`;
- the Flutter gateway terminal session tracks the latest output sequence,
  reconnects with that cursor, updates input sequence from open acks, and keeps
  output streams alive across transport reconnects;
- the repeatable gateway smoke now proves `reconnect_completed: true` through
  the real source-backed WebSocket/PTy path.

## Landed App Route Diagnostics Evidence

Mobile app commit `b9555a9` landed the first app-side route diagnostics gate:

- `GatewayTransport.device()` and `HttpGatewayTransport.device()` consume the
  existing `/v1/devices/me` source route to prove paired-device auth;
- `GatewayRouteDiagnostics` checks Cloudflare HTTPS/WSS route shape, gateway
  health/capabilities, paired-device auth, route-provider scope, project list
  reachability, and ProjectView redaction;
- the runtime panel exposes an injectable `Check Route` action without putting
  Cloudflare-specific branching into the UI;
- no source change was needed for this package because G2 already exposed
  device introspection.

Mobile app commit `c87c924` later added focused contract tests proving extra
route metadata is ignored below the route boundary and remains out of
ProjectView-derived terminal requests, terminal ids, terminal handle
summaries, and terminal frame schemas.

## Source Snapshot

Read-only inspection was done against `/home/bfly/yunwei/ccb_source` at CCB
source version `7.6.12`.

Relevant source facts:

- CLI entry is `ccb.py` via `bin/ccb.js` / `bin/ccb`; phase2 commands flow
  through `lib/cli/parser.py`, `lib/cli/parser_runtime/commands.py`,
  `lib/cli/phase2_runtime/dispatch.py`, and
  `lib/cli/phase2_services.py`.
- `CcbdClient` in `lib/ccbd/socket_client.py` talks to the project ccbd Unix
  socket and binds endpoint methods from
  `lib/ccbd/socket_client_runtime/endpoints.py`.
- Existing ccbd handlers include `ping`, `project_view`,
  `project_focus_agent`, `project_focus_window`,
  `project_view_dismiss_comms`, lifecycle/start/stop, mailbox, queue, trace,
  and recovery operations.
- `project_view` returns `view.project`, `view.ccbd`, `view.namespace`,
  `view.windows`, `view.agents`, and `view.comms`.
- `view.namespace` already includes `epoch`, `socket_path`, and
  `session_name`; those are server-side validation evidence and must not be
  exposed to the remote app.
- Focus handlers already reject stale namespace epochs through
  `ProjectFocusService`.
- `PathLayout(...).ccbd_dir` is the existing per-project runtime/state root,
  with socket paths, lifecycle JSON, state JSON, JSONL logs, snapshots,
  cursors, and artifacts under the same ownership boundary.
- Foreground terminal attach already treats tmux attach as a UI client:
  `lib/cli/services/start_foreground.py` waits for attachable namespace facts
  from `ping('ccbd')`, then runs
  `tmux -S <namespace_tmux_socket_path> attach-session -t
  <namespace_tmux_session_name>`.

## Ready-Check Answers

### 1. Runtime Ownership

First package: implement `ccb mobile serve` as a CLI-managed gateway sidecar
process for the current project.

Do not mount the HTTP/WebSocket gateway inside `ccbd` for the first package.
Do not make `ccbd` supervise the gateway in the first package.

Rationale:

- `ccbd` is already the project authority and Unix-socket RPC server.
- The mobile gateway needs HTTP/WebSocket routing, pairing envelopes, device
  tokens, route-provider metadata, and terminal stream lifecycle.
- Those concerns are not the same as ccbd's project reconciliation,
  dispatcher, provider runtime, or tmux namespace ownership.
- Keeping the gateway as a separate process lets it bind loopback by default,
  be tunneled by Cloudflare later, and fail without stopping CCB.

The gateway must use `CcbdClient(context.paths.ccbd_socket_path)` to read and
mutate CCB-owned state. It must not write directly to provider runtime records
or own the project tmux namespace.

### 2. Paired Device Storage

First package state should live under the current project's runtime root:

```text
PathLayout(project_root).ccbd_dir / "mobile"
```

Initial files:

```text
mobile/
  gateway.json
  devices.json
  pairing-tokens.jsonl
  terminal-tokens.jsonl
  audit.jsonl
```

Ownership:

- gateway owns mobile device records, token hashes, pairing attempts, terminal
  token metadata, and mobile audit events;
- ccbd remains the authority for project state, agent/window focus, namespace
  epoch, tmux socket/session, lifecycle, Comms, and jobs;
- mobile clients are gateway records in the first package, not ccbd runtime
  records.

Security minimum:

- store token hashes, not bearer token plaintext;
- keep pairing and terminal tokens short-lived;
- audit metadata only: device id, scope, project id, request id, action,
  result, timestamp, and denial reason;
- never log terminal input bytes, pasted text, or terminal output.

### 3. Endpoint Reuse

Use existing ccbd endpoints directly through `CcbdClient`:

- `ping('ccbd')` for health, namespace attachability, and diagnostics;
- `project_view(schema_version=1)` for current project model, namespace epoch,
  windows, agents, active focus, Comms preview, and tmux evidence;
- `project_focus_agent(agent, namespace_epoch=...)` for agent focus;
- `project_focus_window(window, namespace_epoch=...)` for window focus;
- `project_view_dismiss_comms(comms_id)` when mobile Comms dismissal is added.

Add gateway wrappers instead of ccbd handlers for:

- HTTP health shape and gateway capabilities;
- current-project project list;
- pairing claim, device listing, revocation, scopes, and audit;
- terminal open, terminal token minting, WebSocket stream ownership, input,
  paste, resize, close, and reconnect;
- route-provider diagnostics;
- first content/event/lifecycle APIs until their exact CCB source authority is
  selected.

The first gateway package originally exposed only loopback-safe read endpoints:

```text
GET /v1/health
GET /v1/projects
GET /v1/projects/{project_id}/view
```

Pairing, focus, terminal-open token routes, terminal WebSocket frame streaming,
and paired-gateway agent terminal UI have since landed with token/scope
checks. Content, event, lifecycle routes, window-specific terminal UI, isolated
gateway smoke, and remote-route diagnostics remain later packages.

### 4. Terminal PTY Ownership

First product gateway terminal stream should live in the gateway process, not
inside `ccbd`.

Open sequence:

1. gateway receives a terminal-open request containing project id,
   namespace epoch, target kind, agent/window identity, and geometry;
2. gateway calls `project_view` through `CcbdClient`;
3. gateway validates project id, namespace epoch, target kind, agent/window,
   and current available namespace facts;
4. gateway mints a short-lived terminal token;
5. gateway opens a PTY client running:

```text
tmux -S <server-side namespace socket> attach-session -t <server-side session>
```

6. gateway streams PTY bytes over the route-agnostic terminal WebSocket frame
   contract.

The remote app must receive only project id, terminal id, token, target
summary, and terminal frame data. It must not receive tmux socket paths or
session names.

### 5. First Project Registry

First package project registry is current project only.

`ccb mobile serve` should resolve the active project through the existing
`CliContext` and `PathLayout`, then return one project from
`GET /v1/projects`.

Do not scan recent `.ccb` anchors, source checkouts, home directories,
installed-release environments, tmux sessions, or arbitrary project roots in
the first package. A host-level multi-project registry can be designed later
after current-project gateway behavior and device token semantics are proven.

## First Source Package

Package name: G1 loopback current-project gateway skeleton.

Allowed behavior:

- add `ccb mobile serve` as a normal phase2 CLI command;
- bind loopback by default, for example `127.0.0.1:8787`;
- return JSON from `/v1/health`, `/v1/projects`, and
  `/v1/projects/{project_id}/view`;
- call existing ccbd through `CcbdClient`;
- create no long-lived tokens yet unless needed for internal health tests;
- keep Cloudflare setup external and not auto-managed.

Non-goals:

- no public network bind by default;
- no Cloudflare Tunnel automation;
- no QR pairing yet;
- no persistent mobile device auth yet;
- no terminal input/WebSocket route yet;
- no multi-project discovery yet;
- no ccbd lifecycle ownership changes.

## Candidate Source Files

Expected files to change or add in `/home/bfly/yunwei/ccb_source` for G1:

- `lib/cli/parser_runtime/constants.py`
- `lib/cli/parser_runtime/commands.py`
- `lib/cli/parser.py`
- `lib/cli/models_start.py` or a new `lib/cli/models_mobile.py`
- `lib/cli/models.py`
- `lib/cli/phase2_runtime/dispatch.py`
- `lib/cli/phase2_runtime/handlers_ops.py` or a new mobile handler module
- `lib/cli/phase2_services.py`
- `lib/cli/render.py` and `lib/cli/render_runtime/` only if CLI output needs
  a rendered status beyond JSON/plain lines
- `lib/storage/paths_ccbd.py` for `ccbd_mobile_dir` and concrete mobile state
  paths
- new `lib/mobile_gateway/` package for gateway models, storage, service,
  HTTP server, ccbd adapter, and later terminal streaming

Expected tests:

- new `test/test_mobile_gateway_*.py` files;
- focused additions to `test/test_v2_cli_parser.py`;
- focused additions to `test/test_v2_phase2_entrypoint.py`;
- focused additions or fixtures around `test/test_ccbd_project_view.py`;
- terminal package later: `test/test_terminal_runtime_tmux_attach.py` and
  gateway terminal frame tests.

## Verification Gates

G1 must prove:

- `ccb mobile serve --help` or equivalent usage is routed through the normal
  CLI path;
- parser rejects unsupported `mobile` actions;
- default listener is loopback;
- project discovery is current-project only;
- health/project/view endpoints call `CcbdClient` through a test double;
- response JSON omits tmux socket/session from app-facing project list;
- ProjectView route preserves CCB schema and route-provider independence;
- gateway process shutdown does not call `stop_all`, `shutdown`, raw
  `tmux kill-session`, or `tmux kill-server`;
- no `.ccb/agents`, `.ccb/ccbd` runtime state, token plaintext, logs, or build
  artifacts are committed.

After G1, later packages have added pairing/device-token storage, authenticated
focus routes, app runtime modes, terminal-open token minting, terminal
WebSocket/PTY streaming, paired-gateway terminal UI, isolated gateway smoke,
window-level terminal/focus UI, and QR camera pairing. The next package should
reduce or replace the developer-only SSH profile before any user-facing remote
release.

## Remaining Questions

- Should the future host-level registry be an explicit `ccb mobile register`
  list, a ccbd-discovered recent-project list, or a user-managed gateway
  config?
- Which library or adapted open-source implementation should own the terminal
  WebSocket server once G3 starts?
- Should mobile lifecycle actions call existing CLI flows, new ccbd handlers,
  or gateway-managed wrappers?
- Which CCB content store becomes the first authoritative Markdown endpoint?
