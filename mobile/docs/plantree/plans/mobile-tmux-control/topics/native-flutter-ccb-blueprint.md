# Native Flutter CCB Blueprint

Date: 2026-06-18
Status: Draft

## Product Boundary

The app is a remote controller for CCB already running on a server.

It should not run providers locally on the phone. It should not become a
generic server management app. Its default home is CCB projects, favorites,
agents, status, terminal, Comms, and readable Markdown content.

## Recommended Architecture

```
Flutter app: Android / iOS / iPadOS
  |
  | QR pairing, stored host profile, reconnect
  v
Transport adapter
  |
  | GatewayTransport: HTTPS/WebSocket to ccb mobile gateway
  | SshTransport: SSH exec/PTY fallback for direct tmux mode
  | RouteProvider: lan | tailnet | cloudflare_tunnel | relay
  v
Server-side CCB
  |
  | control: ccbd project_view / focus / submit / content / lifecycle
  | terminal: tmux -S <project_tmux_socket> attach/control/poll
  v
Project tmux namespace and managed CCB panes
```

The app should keep `GatewayTransport` and `SshTransport` separate from the UI.
This lets the first fork reuse ServerBox's SSH/terminal code while still
leaving room for a Paseo/tmux-mobile-style gateway protocol.

`RouteProvider` is a sub-layer of `GatewayTransport`, not a separate product
mode. LAN, tailnet, CCB Relay, and Cloudflare Tunnel should all expose the same
CCB project, agent, content, notification, and terminal-token API to the
Flutter app.

## Transport Modes

### Gateway Transport

Default product direction.

Server command:

```bash
ccb mobile serve
```

Phone pairing:

```text
scan QR -> host id + gateway URL + one-time pairing token
```

Gateway duties:

- device pairing and scoped tokens;
- project registry and favorites;
- calls to `ccbd` over project Unix sockets;
- terminal binding to `tmux -S <tmux_socket_path> attach -t <session>`;
- optional relay/tunnel integration later;
- Markdown/content and notification event aggregation.

Pros:

- easiest "scan and use" experience after server setup;
- phone does not need to store SSH private keys;
- CCB authority is centralized on the server;
- better fit for notification, relay, and future desktop/web clients.

Cons:

- more server code than direct SSH;
- needs pairing/scopes before exposed beyond LAN/tailnet.

### SSH Direct Transport

Developer/fallback mode and a useful first spike if forking ServerBox.

QR can provision:

- host, port, username, known-host fingerprint;
- CCB project id/root or a resolver command;
- optional gateway URL for side-channel data;
- never a long-lived private key in plain text.

Terminal:

```bash
tmux -S <project_tmux_socket> attach-session -t <tmux_session_name>
```

Control side channel options:

- call a narrow `ccb mobile inspect --json` wrapper over SSH;
- call `ccb mobile project-view --json <project>` over SSH;
- later replace with `GatewayTransport`.

Pros:

- fastest path from ServerBox/MuxPod to a working native terminal;
- no always-running HTTP gateway required;
- uses proven SSH keep-alive/reconnect code.

Cons:

- phone must manage SSH auth;
- polling ProjectView over SSH is clumsier than WebSocket events;
- push/completion reminders need more work;
- easier to drift into a generic SSH/tmux client if the UI is not CCB-first.

### Cloudflare Tunnel Route Provider

First not-on-LAN product route.

Server shape:

```bash
ccb mobile serve --listen 127.0.0.1:8787
cloudflared tunnel run ccb-mobile
```

Pairing QR includes:

- `transport: gateway`;
- `route_provider: cloudflare_tunnel`;
- `gateway_url`;
- `host_id`;
- one-time CCB pairing token;
- server fingerprint;
- capabilities such as `websocket_terminal` and `event_cursor`.

Rules:

- Cloudflare provides reachability only;
- CCB device tokens and scopes remain mandatory;
- terminal tokens remain short-lived and target-bound;
- Cloudflare Access can be optional defense-in-depth but must not replace CCB
  device identity;
- app UI must not branch on Cloudflare-specific logic.

### Relay Route Provider

Post-MVP research path.

Future relay should reuse the same `GatewayTransport` operations and terminal
frame schema:

```text
server gateway --outbound session--> relay
phone app      --outbound session--> relay
```

The relay forwards or brokers encrypted app/server sessions. It should not
own project state, tmux sockets, terminal targets, provider logs, or lifecycle
actions.

## Flutter App Modules

### Host And Pairing

Responsibilities:

- scan QR;
- create/update host profile;
- store device token or SSH profile securely;
- show host/gateway connectivity;
- support re-pair and revocation UI.

ServerBox reuse:

- secure storage and platform packaging patterns.

Paseo reference:

- connection offer, server id, public key, relay fields, pairing link paste.

### Project Home

Responsibilities:

- list CCB projects;
- favorites and recent projects;
- project health, running/offline, active agents, waiting callbacks,
  unread Comms, last activity;
- wake/open/close/stop actions through CCB authority.

Rules:

- do not list unrelated tmux sessions;
- do not use pane id as durable project identity.

### Terminal Surface

Responsibilities:

- high-fidelity terminal attach view;
- socket-aware target: project tmux socket + session;
- special keys, keyboard, paste composer, copy mode;
- reconnect indicator and input queue policy;
- optional capture-poll fallback.

ServerBox reuse:

- xterm terminal page and PTY session flow.

MuxPod reuse/reference:

- special key bar;
- pane breadcrumb;
- adaptive capture fallback;
- `load-buffer` + `paste-buffer -p` multiline paste;
- deep-link target restoration.

CCB-specific constraints:

- terminal target is selected by project/window/agent, not arbitrary session;
- terminal input requires `terminal_input` scope;
- multiline paste should be CCB/tmux paste-buffer based;
- destructive tmux operations are absent in normal CCB mode.

### ProjectView Side Panel

Responsibilities:

- named agents with provider and status;
- windows and current focus;
- queue/callback/completion state;
- Comms attention;
- health/degraded state.

Data source:

- `project_view` polling first;
- event stream or cursor later.

### Markdown Content Surface

Responsibilities:

- render ask/comms/reply/artifact content;
- GFM tables and task lists;
- fenced code copy;
- inline/block math;
- raw source toggle;
- safe link handling;
- persistent reading position per content item.

Renderer candidates:

- `flutter_markdown` or existing ServerBox Markdown wrapper for GFM basics;
- `flutter_math_fork` or a KaTeX-compatible renderer for formulas;
- raw HTML disabled by default.

Terminal capture should not be the authoritative Markdown source. Use CCB
content ids and artifact validation.

### Notifications

Responsibilities:

- completed/failed/blocked/callback waiting;
- project offline/unhealthy;
- terminal disconnected/reconnected;
- deep link to project + agent/window/content.

Sources:

- ProjectView deltas first;
- Comms/callback data;
- later: CCB event cursor.

Native hooks:

- Android foreground service/notifications from ServerBox or MuxPod patterns;
- iOS Live Activity patterns from ServerBox;
- full push service deferred until gateway/event model is stable.

## Server-Side CCB Additions

### `ccb mobile serve`

Purpose:

- print QR pairing;
- run gateway on LAN/tailnet by default;
- expose paired-device API;
- never stop project daemons when the gateway exits.

Initial endpoints:

- `GET /api/projects`;
- `GET /api/projects/:id/view`;
- `POST /api/projects/:id/focus-agent`;
- `POST /api/projects/:id/focus-window`;
- `POST /api/projects/:id/terminal-token`;
- `WS /terminal`;
- `GET /api/content/:id`;
- `GET /api/events` or polling-compatible delta endpoint later.

### CCB CLI JSON Wrappers

Useful for SSH direct transport and tests:

- `ccb mobile projects --json`;
- `ccb mobile project-view --project <id> --json`;
- `ccb mobile project-info --project <id> --json`;
- `ccb mobile focus-agent --project <id> --agent <name> --json`.

These wrappers should call the same internal code as the gateway. They are not
a separate authority model.

### Content Endpoint

Needed for high-quality Markdown/math.

Requirements:

- resolve ask, reply, Comms, and text artifact ids;
- return text and render hints;
- refuse arbitrary file paths;
- keep ProjectView compact by returning previews/ids rather than full bodies.

## Implementation Sequence

### Package N1: Native Repo Baseline

Goal: create a separate `ccb-mobile` Flutter workspace.

Options:

- fork ServerBox directly if AGPL is accepted;
- start a smaller Flutter app and port only needed ideas if a permissive app
  license is required.

Acceptance:

- Android and iOS debug builds start;
- one terminal screen can be opened against a fake transport;
- upstream attribution and license notes are present.

### Package N2: CCB Project Data Model

Goal: replace server/session-first state with host/project/agent state.

Work:

- add `CcbHost`, `CcbProject`, `CcbAgent`, `CcbWindow`, `CcbTerminalTarget`;
- add local favorites/recent state;
- mock ProjectView fixtures for UI development.

Acceptance:

- home screen lists projects and favorites from fixture data;
- agent list is named and status-bearing;
- no generic tmux session picker is visible in CCB mode.

### Package N3: Socket-Aware Tmux Transport

Goal: terminal opens the CCB project tmux namespace.

Work:

- add socket path/name to tmux command builders;
- build `tmux -S <socket> attach-session -t <session>`;
- add capture and paste commands with the same socket prefix;
- add tests for quoting and socket placement.

Acceptance:

- direct SSH test attaches to an isolated tmux socket;
- default `tmux attach` is never used for a CCB project;
- closing terminal view does not stop CCB.

### Package N4: QR Pairing

Goal: scan once, then reconnect simply.

Work:

- define `ccb-mobile://pair?...` or HTTPS pairing link;
- implement QR scanner and paste-link fallback;
- store host profile securely;
- support local/LAN gateway profile for vertical-slice development;
- support CCB Relay gateway profile for the first not-on-LAN release and keep
  Cloudflare Tunnel as an advanced profile;
- optional SSH-direct profile second.

Acceptance:

- server prints QR;
- phone scans and creates a host profile;
- revocation/re-pair path is defined even if minimal.

### Package N5: ProjectView And Focus

Goal: named agent switching from CCB authority.

Work:

- gateway or SSH wrapper calls `project_view`;
- app displays windows/agents/status;
- focus agent/window calls CCB endpoint/wrapper;
- stale namespace epoch refreshes and locks unsafe actions.

Acceptance:

- tapping an agent does not call raw `tmux select-pane`;
- UI refreshes after focus;
- stale epoch path is visible and recoverable.

### Package N6: Markdown And Math

Goal: readable CCB content view.

Work:

- add `project_content_get` or gateway content route;
- add native Markdown renderer;
- add formula renderer and fallback;
- add code copy/table scroll/source toggle.

Acceptance:

- long reply/artifact content is readable on phone and iPad;
- math formulas render or degrade clearly;
- local host paths are not exposed as arbitrary links.

### Package N7: Completion Notifications

Goal: phone is useful away from the terminal.

Work:

- derive first notifications from ProjectView/Comms deltas;
- deep link to project + agent/content;
- use foreground/local notification primitives first;
- defer cloud push until event identity and pairing are stable.

Acceptance:

- duplicate deltas do not spam;
- notification opens the correct project target;
- acknowledgements persist locally or gateway-side.

### Package N8: Lifecycle Controls

Goal: wake and stop projects without raw tmux kills.

Work:

- add wake/open/close/stop through CCB-owned lifecycle behavior;
- require explicit scope and confirmation for stop;
- keep admin-only force stop separate.

Acceptance:

- close only closes mobile view;
- stop never runs raw `tmux kill-server`;
- project can be woken then opened.

## First Vertical Slice

The smallest useful native slice:

1. Flutter app baseline.
2. Manual host/project fixture.
3. Socket-aware tmux terminal attach to one CCB project.
4. ProjectView fixture side panel.
5. Agent focus through a fake CCB transport.

This proves native terminal fit before building the full pairing and gateway.

## Alpha

Alpha should add:

- QR pairing to local gateway and Cloudflare Tunnel route;
- real ProjectView polling;
- focus agent/window;
- favorites/recent projects;
- Markdown/math drawer;
- basic completion/attention notifications;
- reconnect after backgrounding.

## MVP

MVP should add:

- project wake/open/close/stop;
- content endpoint backed by CCB artifact validation;
- terminal input scopes;
- device revocation;
- stale epoch handling;
- phone and iPad UI test coverage;
- documented Cloudflare Tunnel setup for not-on-LAN access.
