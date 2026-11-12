# Gateway Contract Checkpoint

Date: 2026-06-18
Status: Checkpoint with CCB source ready-check recorded

## Purpose

This checkpoint freezes the minimum route-agnostic gateway contract needed
before adding `ccb mobile serve`, Cloudflare Tunnel pairing, content,
notifications, or lifecycle work.

The app already has a validated SSH-direct terminal path. The gateway path must
reuse the same CCB identity and terminal target semantics instead of creating a
second product model.

## Current Evidence

Ready:

- Flutter app source, Android/iOS platform folders, and Android debug build.
- Fake CCB repository and ProjectView-shaped fixture.
- Socket-aware `CcbTerminalTarget` and `TmuxCommandBuilder`.
- SSH direct PTY adapter using `dartssh2`.
- Developer SSH profile entry point.
- Isolated CCB project harness evidence.
- SSH direct live smoke through temporary localhost sshd.
- Android API 35 emulator `flutter run` smoke.

Resolved before G1 gateway coding:

- [ccb-mobile-serve-ready-check.md](ccb-mobile-serve-ready-check.md) answers
  the source ownership questions for the first loopback current-project
  package;
- [Decision 010](../decisions/010-cli-managed-mobile-gateway-sidecar.md)
  selects a CLI-managed gateway sidecar rather than a ccbd-mounted HTTP server
  for the first package.

Remaining after G1:

- exact pairing token storage and revocation owner;
- exact terminal token lifetime and replay behavior;
- first content endpoint shape for Markdown/Comms/replies.

## Boundary Rules

- `GatewayTransport` is the product remote transport.
- `SshTerminalTransport` remains a developer/fallback validation path.
- `RouteProvider` is metadata below `GatewayTransport`.
- CCB Relay is the default not-on-LAN route provider per
  [Decision 011](../decisions/011-relay-default-remote-route.md).
- Cloudflare Tunnel remains an advanced route provider and must reuse the same
  app-facing schemas.
- Route-provider fields must not appear in project ids, terminal ids,
  ProjectView payloads, terminal frame semantics, or content ids.
- `pane_id` remains evidence only and must never authorize terminal input by
  itself.
- Gateway endpoints must validate project id, namespace epoch, target kind,
  agent/window identity, scope, and terminal token before accepting input.
- Closing a mobile terminal must close only the mobile stream/client, not
  `ccbd`, provider panes, or the project tmux session.

## App-Facing Interfaces

The Flutter app should keep UI code behind `MobileCcbRepository`:

```text
listProjects()
getProjectView(projectId)
focusAgent(projectId, agent, namespaceEpoch)
focusWindow(projectId, window, namespaceEpoch)
openTerminal(projectId, target, geometry)
getContent(projectId, contentId)
subscribeEvents(cursor)
requestLifecycle(projectId, action)
```

Transport implementations:

- `FakeMobileCcbRepository`: fixture and UI development.
- `SshTransport` / `SshTerminalTransport`: developer validation and fallback.
- `GatewayTransport`: HTTP/WebSocket product path.

## Pairing Envelope

QR/manual pairing should import a host profile shaped like:

```json
{
  "scheme": "ccb-mobile",
  "transport": "gateway",
  "route_provider": "cloudflare_tunnel",
  "gateway_url": "https://ccb-mobile.example.com",
  "host_id": "host_...",
  "pairing_token": "short-lived",
  "expires_at": "2026-06-18T12:00:00Z",
  "server_fingerprint": "sha256:...",
  "capabilities": [
    "http_json",
    "websocket_terminal",
    "event_cursor",
    "content_markdown"
  ]
}
```

LAN, tailnet, Cloudflare Tunnel, and relay change only route fields. Device
identity, scopes, project ids, terminal ids, event cursors, content ids, and
terminal frame schemas stay CCB-owned.

## Gateway HTTP Endpoints

Minimum route-agnostic endpoints:

```text
GET  /v1/health
POST /v1/pair/claim
GET  /v1/projects
GET  /v1/projects/{project_id}/view
POST /v1/projects/{project_id}/focus-agent
POST /v1/projects/{project_id}/focus-window
POST /v1/projects/{project_id}/terminals
GET  /v1/projects/{project_id}/content/{content_id}
GET  /v1/events?cursor=...
POST /v1/projects/{project_id}/lifecycle
POST /v1/devices/{device_id}/revoke
```

Every mutating request must include:

- device id;
- scope used for the action;
- namespace epoch where the action touches terminal/focus state;
- request id for replay defense;
- current terminal token when sending terminal input.

## Terminal Open

Request:

```json
{
  "schema_version": 1,
  "project_id": "project-id",
  "namespace_epoch": 1,
  "target": {
    "kind": "agent",
    "agent": "mobile_probe",
    "window": "main",
    "pane_id": "%2"
  },
  "geometry": {
    "columns": 100,
    "rows": 30,
    "pixel_width": 960,
    "pixel_height": 640
  }
}
```

Response:

```json
{
  "terminal_id": "term_...",
  "terminal_token": "short-lived",
  "expires_at": "2026-06-18T12:05:00Z",
  "websocket_url": "wss://gateway.example.com/v1/terminals/term_...",
  "target_epoch": 1,
  "target_summary": {
    "project_id": "project-id",
    "agent": "mobile_probe",
    "window": "main"
  }
}
```

The response must not expose tmux socket paths to remote clients. The gateway
may internally run `tmux -S <project_socket> attach-session -t <session>` only
after validating ProjectView identity and scopes.

## Terminal Frames

Initial binary frame model can stay simple:

```json
{ "type": "open", "terminal_id": "term_...", "token": "..." }
{ "type": "input", "seq": 1, "bytes_b64": "..." }
{ "type": "paste", "seq": 2, "text": "..." }
{ "type": "resize", "columns": 120, "rows": 36 }
{ "type": "output", "seq": 10, "bytes_b64": "..." }
{ "type": "closed", "reason": "client_closed" }
{ "type": "error", "code": "stale_namespace_epoch" }
```

Required behavior:

- input sequence numbers are monotonic per terminal token;
- reconnect cannot replay stale input without an explicit resume cursor;
- terminal output can be binary bytes;
- close is client-scoped only;
- token expiry locks input and asks the app to reopen/revalidate target;
- stale namespace epoch closes the stream fail-closed.

## CCB Source Ready-Check

Before editing `/home/bfly/yunwei/ccb_source`, answer:

1. Should `ccb mobile serve` be mounted inside `ccbd`, run as a sidecar, or be
   a CLI-managed gateway process?
2. Where will paired-device records, scopes, revocation, and audit events live?
3. Which current `ccbd` endpoints can be called directly, and which need a new
   mobile wrapper?
4. Should terminal PTY attach live in `ccbd` or the gateway process?
5. What is the first persistent project registry source for mobile home:
   current project only, recent `.ccb` anchors, or explicit registration?

Implementation must stay out of `ccb_source` until that ready-check is
recorded. That ready-check is now recorded in
[ccb-mobile-serve-ready-check.md](ccb-mobile-serve-ready-check.md); it opens
only the G1 loopback current-project gateway skeleton.

## Acceptance Gate For Gateway Package

The first gateway package is ready to start when:

- app-side `GatewayTransport` and `RouteProvider` interfaces exist;
- fake gateway fixtures prove route-provider fields stay outside CCB identity;
- terminal open/input/resize/close schemas have focused tests;
- plan tree records the CCB source ready-check outcome;
- the implementation package names the exact CCB source files to inspect or
  change.
