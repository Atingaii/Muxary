# Remote Access Roadmap

Date: 2026-06-19
Status: Relay-first default route selected; local Android emulator validation
available; source-side Tailnet onboarding landed in reviewed worktree;
Cloudflare named-tunnel path retained as advanced route

## Goal

Support phones and iPads outside the server's local network without requiring
ordinary users to buy a domain, configure Cloudflare, open router ports, or
have a public IP.

The product model remains:

```text
mobile app
  -> GatewayTransport
  -> route provider
  -> ccb mobile gateway
  -> ccbd + CCB project tmux socket
```

LAN, tailnet, Cloudflare Tunnel, and CCB Relay are route providers. They are
not separate product modes and must not leak into the project, agent, terminal,
content, or notification models.

## Default Route Decision

[Decision 011](../decisions/011-relay-default-remote-route.md) changes the default
not-on-LAN path from Cloudflare named tunnels to CCB Relay. Cloudflare named
tunnels remain valuable for advanced/self-hosted users, but they are no longer
the ordinary user's alpha gate because they require user-owned domains and DNS
configuration.

Reserved first relay endpoint:

```text
wss://relay.seemlab.top
```

Default route order:

1. LAN/manual URL for local development and same-network use.
2. CCB Relay for ordinary remote use and open-box mobile pairing.
3. Tailnet for private-network users with Tailscale already installed.
4. Cloudflare named tunnel for advanced domain/DNS users.
5. Development quick tunnel for smoke/demo only.

## Route Provider Contract

The app should model route provider as connection metadata:

```text
RouteProvider
  kind: lan | tailnet | cloudflare_tunnel | relay
  gatewayUrl
  websocketUrl
  hostFingerprint
  capabilities
  diagnostics
```

All route providers must expose the same `GatewayTransport` operations:

- pair device;
- list projects;
- fetch ProjectView;
- focus agent/window;
- open terminal token;
- stream terminal frames;
- send terminal input;
- fetch content;
- subscribe or poll events;
- request lifecycle action.

The server should keep the same HTTP/WebSocket API whether the request arrives
from LAN, tailnet, Cloudflare Tunnel, or relay.

## Phase R0: Route-Agnostic Gateway Contract

Purpose: prevent future rework before any external route is added.

Work:

- define `GatewayTransport` as the app's default remote transport;
- keep `SshTransport` only as developer fallback;
- define terminal frame schema independent of Cloudflare and relay;
- add gateway health and capability endpoints;
- include route metadata in QR pairing without changing the project model;
- add local fake route and LAN route fixtures for UI tests.

Acceptance:

- UI code does not branch on `cloudflare_tunnel` or `relay`;
- terminal token/open/input/close behavior is route-independent;
- app can switch a host profile from LAN URL to tunnel URL without recreating
  projects or favorites.

## Phase R1: Local Android And LAN Validation

Purpose: keep the phone app and gateway path testable without public relay or
Cloudflare infrastructure.

Available local setup:

- AVD `ccb_mobile_api35` exists at
  `/home/bfly/.android/avd/ccb_mobile_api35.avd`;
- Flutter 3.44.2 and Android SDK paths are exported by
  `tools/mobile_toolchain_env.sh`;
- prior Android `flutter run` smoke installed and started the app on
  `emulator-5554`;
- the host-side gateway terminal smoke already verifies pairing, route
  diagnostics, ProjectView/focus, terminal-open, WebSocket terminal
  output/input/paste/resize/close, reconnect, and cleanup.

Manual emulator validation shape:

```bash
source tools/mobile_toolchain_env.sh
emulator -avd ccb_mobile_api35 -no-window -gpu swiftshader_indirect -no-snapshot-load &
adb wait-for-device
adb reverse tcp:8787 tcp:8787

# In a CCB project, start the gateway on host loopback.
ccb mobile serve --listen 127.0.0.1:8787 --route-provider lan

# Then run the app on the emulator and pair to http://127.0.0.1:8787.
cd app
flutter run -d emulator-5554 --debug --target lib/main.dart
```

Acceptance:

- emulator can pair using the existing QR/manual paired-gateway flow;
- route diagnostics pass against host loopback via `adb reverse`;
- agent/window focus and terminal streaming work through the same app
  `GatewayTransport` used by relay and Cloudflare routes.

## Phase R2: CCB Relay Default Route Spike

Purpose: validate the RustDesk/Paseo-style remote route for ordinary users.

Proposed shape:

```text
phone app  <->  CCB relay  <->  user's CCB host
```

Work:

- define relay session and frame envelopes;
- define host/app rendezvous keyed by relay host id/session id;
- add or adapt an E2EE handshake so relay forwards opaque frames;
- connect `ccb mobile serve` outbound to the relay while preserving loopback
  ownership of ccbd/tmux;
- make the app consume `RouteProvider.relay` pairing payloads without UI
  branching;
- deploy a first relay candidate at `relay.seemlab.top` or an equivalent local
  test endpoint.

Hosted deployment and admission details:

- [public-relay-invitation-and-aliyun-deployment.md](public-relay-invitation-and-aliyun-deployment.md)
  defines the accountless but authenticated public service, one-time applicant
  invitations, host key binding, end-to-end encryption, no-business-payload
  storage, quotas, and Alibaba Cloud staging profile;
- [public-relay-android-emulator-acceptance.md](public-relay-android-emulator-acceptance.md)
  is the required public WSS gate. Local harness results cannot substitute for
  that same-build real Emulator evidence.

Local spike evidence:

- mobile app commit `28dc384` added fake/local relay metadata guards:
  diagnostics require HTTPS origin-only relay `gateway_url`, WSS origin-only
  relay `websocket_url`, and matching `/v1/devices/me` route metadata; pairing
  tests prove relay `websocket_url`, capabilities, diagnostics, fingerprint,
  scopes, and secure-store roundtrip are preserved without storing the
  one-time pairing code.
- mobile app commit `f8c5a25` added fake/local relay transport envelope
  coverage: `RelayGatewayTransport` wraps the route-agnostic
  `GatewayTransport` contract for relay profiles, records opaque local
  envelopes for gateway operations, and tests that project ids, terminal ids,
  terminal tokens, paste text, route metadata, and relay URLs do not leak into
  the envelope JSON surface.
- mobile app commit `3bd2ca1` added the app-side relay protocol contract:
  `RelayFrame` covers local client hello, host hello, opaque gateway envelope,
  ack, and close frames; `RelayHandshakeTranscript` validates local handshake
  agreement; and `RelayHostRegistration` defines the host-outbound
  registration payload without local gateway URLs, pairing codes, device
  tokens, terminal tokens, project ids, terminal ids, or paste text.
- source commit `1b438505` added the source-side local relay harness:
  `mobile_gateway.relay` validates the same frame/handshake/registration
  shape, `MobileGatewayRelayOutboundClient` registers a host into an in-memory
  `LocalRelayServerHarness`, and `ccb mobile serve --route-provider relay`
  reports local `relay_outbound` registration status without opening a public
  listener.
- [relay-route-provider-spike.md](relay-route-provider-spike.md) records the
  first relay contract, reuse boundary, emulator-only acceptance gates, and
  follow-up packages before any public relay deployment.

Acceptance:

- user host and phone both connect outbound to the relay;
- relay cannot control CCB lifecycle and should not see terminal content in
  cleartext;
- same project list, ProjectView, focus, terminal token, terminal frame,
  content, and event semantics as LAN/Cloudflare;
- relay disconnect does not stop server-side CCB projects.
- each applicant invitation can activate at most one host credential, including
  concurrent claims, and cannot be reused after successful activation;
- the relay stores only anonymous admission/security metadata and never
  persists forwarded CCB payloads.

## Phase R3: Tailscale Tailnet Stable Private Route

Purpose: give private-network users and developer dogfood a stable route that
does not require public DNS, Cloudflare credentials, router port forwarding, or
public CCB relay availability.

Detailed plan:

- [tailscale-tailnet-stable-route.md](tailscale-tailnet-stable-route.md)

Route shape:

```bash
ccb mobile serve \
  --listen 127.0.0.1:8787 \
  --public-url https://ccb-host.<tailnet>.ts.net:8787 \
  --route-provider tailnet

tailscale serve --bg --https=8787 http://127.0.0.1:8787
```

Requirements:

- host-side Mobile setup is packaged as an explicit optional CCB source bundle
  installed with `ccb update mobile`, not as part of mandatory `ccb update`;
- computer and phone/iPad are logged in to the same tailnet;
- MagicDNS and tailnet HTTPS are enabled;
- CCB gateway remains loopback-only;
- Tailscale Serve publishes only the loopback gateway inside the tailnet;
- Tailnet identity and grants are an outer network-access boundary, while CCB
  pairing, device token, scopes, revocation, terminal tokens, namespace epoch,
  and target validation remain CCB-owned;
- Tailscale Funnel is not used for this route.

Source-side landed evidence:

- source worktree `/home/bfly/yunwei/ccb_source_mobile_update_tailnet`, branch
  `worker1/mobile-update-tailnet`;
- commits `b6e148f2` and `d73ae650` add reviewed `ccb update mobile` Tailnet
  onboarding and align the public Tailnet HTTPS port with the gateway listen
  port;
- focused/relevant tests after follow-up: 147 passed;
- worker full pytest before follow-up: 2993 passed, 2 skipped;
- reviewer1 accepted the final stack.

Acceptance:

- one physical phone or iPad can pair through `route_provider: tailnet`;
- `/v1/health`, `/v1/devices/me`, project list, ProjectView, focus,
  terminal-open, WebSocket output/input/paste/resize/close, reconnect, and
  revoke all pass through the same `GatewayTransport` screens and schemas as
  LAN/relay/Cloudflare;
- smoke evidence records whether the connection is direct, peer-relay, or DERP
  relay.

## Phase R4: Cloudflare Tunnel Advanced Route

Purpose: keep a documented advanced route for users who already have a domain,
Cloudflare account, and named-tunnel setup.

Server setup:

```bash
ccb mobile serve \
  --listen 127.0.0.1:8787 \
  --public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
cloudflared tunnel run ccb-mobile
```

Gateway requirements:

- bind local listener to loopback by default when used with tunnel;
- generate QR with `route_provider: cloudflare_tunnel`;
- reject unpaired devices even if the tunnel URL is reachable;
- issue short-lived terminal tokens;
- support WebSocket terminal stream through the tunnel;
- provide diagnostics for tunnel URL, gateway health, and pairing status.

App requirements:

- scan Cloudflare-backed QR;
- store host profile and server fingerprint;
- run a route diagnostics gate that checks HTTPS/WSS route shape, gateway
  health/capabilities, paired-device auth, route-provider scope, project
  reachability, and ProjectView redaction before treating the route as ready;
- reconnect with exponential backoff;
- lock terminal input while route/gateway identity is stale;
- preserve favorites and last opened project when route URL changes.

Landed alpha evidence:

- mobile app commit `b9555a9` added `GatewayRouteDiagnostics`, the
  authenticated `/v1/devices/me` transport contract, and a runtime-panel route
  check that stays behind `GatewayTransport` instead of branching UI code on
  Cloudflare.
- source commit `a222446c` added `ccb mobile serve --public-url` and
  `--route-provider` metadata support while preserving loopback-only listen
  validation.
- mobile app commit `08eed72` added `tools/mobile_gateway_terminal_smoke.py`
  support for named Cloudflare Tunnel URLs and development quick tunnels via
  `cloudflared tunnel --url`; the Dart smoke now asserts route-provider
  metadata and runs `GatewayRouteDiagnostics` before terminal streaming.
- mobile app commit `f75f1ec` added a public `/v1/health` readiness wait
  before Dart pairing and preserved cloudflared/gateway summaries on failure.
- mobile app commit `a8eeec0` added smoke-only public DNS override support for
  generated quick-tunnel hostnames and passed a live Cloudflare quick-tunnel
  smoke through public HTTPS/WSS with route diagnostics and terminal
  output/input/paste/resize/close/reconnect.
- source commit `8a264cae` added host-local `ccb mobile devices` and
  `ccb mobile revoke <device_id>` so a server operator can revoke lost phones
  without adding a public HTTP admin route; revoke also invalidates still-open
  terminal handles.
- source commit `c3c7fd1b` added English and Chinese Cloudflare Alpha setup
  docs and README entry links for the documented named-tunnel path.
- mobile app commit `4f41391` added a named-tunnel preflight to the smoke
  harness so missing local Cloudflare config/credentials are reported before
  any disposable CCB runtime starts.
- source commit `44ba9edd` added the preflight command to the English and
  Chinese Cloudflare Alpha setup docs.
- mobile app commit `6f26591` made the preflight hostname-aware for
  multi-ingress configs and added local self-tests for missing config, matched
  hostname, wrong origin port, and missing hostname cases.
- source commit `973a2707` documented the multi-ingress hostname matching
  behavior.
- mobile app commit `1c2d4de` added `--cloudflared-named-tunnel` so the smoke
  harness can run preflight, start `cloudflared tunnel run`, wait for a
  registered tunnel connection, and then run the public health/terminal smoke
  path.
- source commit `444b648c` documented the automated named-tunnel smoke path.
- mobile app commit `eadcece` added `next_actions` to blocked preflight JSON,
  turning missing Cloudflare setup into a command/config checklist.
- source commit `9ce07104` documented the `next_actions` checklist.
- mobile app commit `de79cde` added `config_template` to blocked preflight
  JSON, turning the requested hostname and gateway listen origin into a
  side-effect-free `~/.cloudflared/config.yml` draft.
- source commit `a2ac6f1e` documented the `config_template` field.
- mobile app commit `2ff36a9` added round-trip self-test coverage for that
  generated config draft.
- mobile app commit `11bae28` and source commit `69891f03` made non-default
  named tunnel handoff consistent through `--cloudflared-tunnel-name <name>`.
- mobile app commit `e1e14a2` and source commit `867300d7` made fixed
  loopback `--gateway-listen` a named-tunnel preflight requirement, preventing
  dynamic port `127.0.0.1:0` from becoming Cloudflare ingress guidance.
- mobile app commit `3f0a0b5` and source commit `8e047913` added a copyable
  `named_tunnel_smoke_command` to preflight JSON and setup docs.
- mobile app commit `434ed01` and source commit `93c0de50` added manual
  `cloudflared_run_command` and already-running tunnel smoke command handoff.

Acceptance:

- phone on cellular can pair and open one CCB project terminal;
- app background/foreground reconnect returns to the same target or fails
  closed with refresh;
- ProjectView, focus, Markdown content, notifications, and lifecycle use the
  same endpoint shapes as LAN;
- device revocation works without changing Cloudflare config.
- named-tunnel or cellular validation passes with the same route diagnostics
  and terminal smoke evidence as the accepted quick-tunnel run.

## Phase R5: Remote MVP Hardening

Purpose: make the default relay route and optional advanced routes safe enough
for normal open-source users.

Work:

- implement the one-time hosted-relay admission and key-binding contract from
  [Decision 023](../decisions/023-one-time-public-relay-admission.md);
- deploy the first staging endpoint and pass the complete public Android
  Emulator plan before inviting beta users;

- document relay setup, local emulator validation, Tailnet private setup, and
  advanced tunnel
  configuration; initial Cloudflare source docs landed in `c3c7fd1b`,
  preflight docs landed in `44ba9edd`, ingress-matching docs landed in
  `973a2707`, automated smoke docs landed in `444b648c`, blocked setup
  handoff docs landed in `9ce07104` and `a2ac6f1e`, and Cloudflare docs should
  be retained as advanced-route documentation;
- add pairing-token expiry and host-side device list/revocation; host-side
  CLI list/revoke landed in source `8a264cae`, setup docs landed in
  `c3c7fd1b`, and app-visible device UI remains later work;
- add per-device scopes and admin confirmation gates;
- add audit events without terminal keystroke logging;
- add event cursor/resume for notifications;
- add relay/tunnel health diagnostics in the app;
- define recommended Cloudflare Access posture as optional defense-in-depth for
  the advanced Cloudflare route.

Acceptance:

- a non-expert can run `ccb mobile pair`, scan QR, and connect from cellular
  without owning a domain;
- lost network does not replay input or lifecycle actions;
- stale namespace and terminal token expiry are visible and recoverable;
- exposing the gateway URL alone is not enough to control CCB.

## Phase R6: Self-Hosted Relay Option

Purpose: make the default CCB relay architecture self-hostable without
rewriting mobile UI or CCB gateway semantics.

Research questions:

- Can the relay forward the existing HTTP/WebSocket operation set, or should
  it use one bidirectional framed session?
- Should the app/server use message-level encryption over the relay so relay
  operators cannot inspect terminal frames?
- How should server availability, device routing, and reconnect cursors work?
- How should relay auth differ from CCB device auth?
- What minimum self-hosting story is acceptable?

Acceptance:

- same QR shape with `route_provider: relay`;
- same project list, ProjectView, terminal token, terminal frame, content, and
  event schemas;
- relay has no CCB lifecycle authority;
- relay can be stopped without stopping server-side CCB projects;
- switching a host profile from Cloudflare URL to relay route preserves
  favorites and project ids.

Non-goals:

- relay does not execute tmux;
- relay does not store provider logs;
- relay does not own project lifecycle;
- relay does not replace CCB device scopes.

## Design Rules To Avoid Rework

- Do not put Cloudflare-specific logic in Flutter screens.
- Do not let Cloudflare Access identity replace CCB device identity.
- Do not encode route-provider fields into project ids or terminal ids.
- Do not expose tmux sockets, pane ids, or raw SSH as the public remote API.
- Do not make terminal frames depend on WebSocket URL shape.
- Do not implement notifications by scraping terminal text.
- Do not assume the gateway URL is permanent; host identity and project ids are
  the durable keys.
- Do not let route disconnect imply project shutdown.

## Recommended Milestone Placement

- Vertical slice: LAN/manual URL is enough.
- Alpha: local Android emulator plus LAN paired-gateway validation.
- Remote alpha: CCB Relay default route spike.
- MVP: relay hardening, revocation, scopes, diagnostics, and docs.
- Advanced/self-hosted: Cloudflare named tunnel, tailnet, and self-hosted relay
  options after the default relay path is stable.
