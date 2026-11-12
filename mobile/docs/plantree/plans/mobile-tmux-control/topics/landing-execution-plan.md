# Landing Execution Plan

Date: 2026-06-18
Status: Execution baseline

## Purpose

Convert the native agent-first, server-remote design into implementation
packages that can be landed incrementally.

The preferred path is a dedicated Flutter mobile repository with CCB-specific
project/agent UI. ServerBox is the preferred fork candidate if AGPL is
acceptable; MuxPod, tmux-mobile, and Paseo remain important references.

## Implementation Principles

- Keep the phone/iPad as a remote for server-side CCB.
- Default the project page to a top agent switcher plus one selected-agent
  workspace; raw terminal is an explicit fallback action.
- Connect terminal streams to CCB project tmux sockets, not the default tmux
  server.
- Let `ccbd` remain authority for project lifecycle, focus, ProjectView,
  namespace epoch, and agent/window identity.
- Keep terminal transport behind an interface so SSH direct and gateway
  transports can coexist.
- Keep route providers behind `GatewayTransport` so CCB Relay, Cloudflare
  Tunnel, and local routes do not alter UI, project, agent, terminal, content,
  or event schemas.
- Avoid raw pane/session mutations in the normal mobile UI.
- Use fake CCB transports and isolated real tmux sockets before touching live
  CCB projects.

## Source Reality Check

Checked against `/home/bfly/yunwei/ccb_source` version `7.6.11` on
2026-06-18.

Existing CCB anchors that the mobile landing can reuse:

- `lib/ccbd/socket_client.py` provides `CcbdClient` over line-delimited JSON
  RPC.
- `lib/ccbd/socket_client_runtime/endpoints.py` already exposes
  `project_view`, `project_focus_agent`, `project_focus_window`,
  `project_sidebar_click`, `submit`, `queue`, `watch`, `ack`, and lifecycle-ish
  daemon operations.
- `lib/ccbd/project_view/service.py` returns `project`, `ccbd`, `namespace`,
  `windows`, `agents`, and `comms`; `namespace` includes `epoch`,
  `socket_path`, `session_name`, `active_window`, and `active_pane_id`.
- `lib/ccbd/project_focus/service.py` validates namespace epoch and focuses
  agents/windows through CCB authority instead of pane id alone.
- `lib/storage/paths_ccbd.py` defines the CCB tmux socket and session naming
  source.
- `lib/terminal_runtime/tmux.py` already has socket-aware tmux base args, and
  `lib/terminal_runtime/tmux_send.py` has a paste-buffer path that the mobile
  command layer should mirror.

Implication: the first mobile batch should not invent a new CCB authority
model. It should model the existing `project_view` shape, keep pane ids as
evidence, and prove socket-aware tmux terminal behavior before adding a
gateway.

## Batch 1 Landing Scope

Write surface:

- mobile workspace files under this repository, expected first app path:
  `app/`;
- plan-tree status updates;
- no `ccb_source` edits for Batch 1 unless a later ready-check explicitly
  opens a CCB-source task.

Packages included:

1. N1 native repo baseline, with license-safe upstream handling.
2. N2 CCB mobile data model and fake transport.
3. N3 socket-aware tmux command layer.
4. N4 terminal vertical-slice harness for one manually configured isolated CCB
   project.

Packages excluded from Batch 1:

- `ccb mobile serve`;
- Cloudflare Tunnel pairing;
- live ProjectView polling through a gateway;
- content endpoint, notifications, lifecycle controls, and relay work.

Execution gates:

- If AGPL is accepted for the app component, ServerBox can be used as a fork
  candidate with attribution preserved.
- If AGPL is not accepted yet, start from a smaller Flutter baseline and port
  only compatible ideas; do not import ServerBox/Paseo code.
- Android emulator is the first required validation target. iOS/iPadOS remains
  planned but is not a blocker for the first Android terminal slice.
- The first real terminal target must use `tmux -S <project_socket>
  attach-session -t <session>` or an equivalent gateway PTY command generated
  from `CcbTerminalTarget`; default `tmux attach` is a failure.

## Repository Layout Decision

Initial implementation should live outside CCB core runtime. In this
standalone mobile workspace, the expected app path is `app/`:

```text
ccb_mobile/
  app/
    android/
    ios/
    lib/
    test/
  docs/plantree/
```

Server-side gateway or CLI integration can later live in CCB:

```text
ccb mobile serve
ccb mobile projects --json
ccb mobile project-view --json
```

Do not initially copy the mobile app into `ccb_source/lib/`. The app has a
different dependency graph, platform toolchain, release cadence, and license
surface.

## Package N1: Native Repo Baseline

Goal: create a working Flutter app baseline.

Options:

- fork ServerBox when AGPL is acceptable for the mobile app component;
- otherwise start a smaller Flutter app and reimplement/port only compatible
  ideas from MuxPod and MIT references.

Work:

- preserve upstream attribution and license notes;
- keep Android and iOS debug builds working;
- add a fake CCB transport;
- render a project/agent fixture home screen;
- keep one terminal screen reachable through fake data.

Acceptance:

- Android and iOS debug builds start;
- app opens to CCB project/favorite UI, not a generic server dashboard;
- no CCB source code changes.

## Package N2: CCB Mobile Data Model

Goal: define the app model before wiring real transports.

Flutter files:

- `lib/models/ccb_host.dart`
- `lib/models/ccb_project.dart`
- `lib/models/ccb_agent.dart`
- `lib/models/ccb_window.dart`
- `lib/models/ccb_terminal_target.dart`
- `lib/models/ccb_content_item.dart`
- `lib/models/ccb_notification.dart`
- transport interfaces under `lib/transport/`

Work:

- model stable CCB identity separately from tmux pane evidence;
- add local favorites/recent projects;
- add permission scopes;
- map fake ProjectView snapshots into UI state.

Acceptance:

- tests prove pane id alone cannot form a terminal input target;
- fixture ProjectView creates named project/window/agent rows;
- favorites and recent projects are independent of raw tmux session names.

## Package N3: Socket-Aware Tmux Command Layer

Goal: make every CCB tmux command target the project socket.

Work:

- add tmux socket path/name to command builders;
- generate `tmux -S <socket> attach-session -t <session>`;
- generate socket-aware list/capture/select/paste commands;
- add safe shell quoting tests;
- remove or gate generic kill/split/new/rename operations in CCB mode.

Acceptance:

- command tests cover socket path, session name, window/agent target, and
  multiline paste;
- default `tmux attach` cannot be produced for a CCB project;
- destructive tmux commands are absent from normal CCB UI routes.

## Package N4: Terminal Transport Vertical Slice

Goal: open one CCB project terminal from the native app.

Transport options:

- SSH direct: reuse ServerBox-style `SSHClient.execute(command, pty: ...)`;
- gateway: WebSocket terminal stream to a server-side PTY running tmux attach.

Work:

- bind terminal to `CcbTerminalTarget`;
- support keyboard, special keys, paste, resize, background/resume, reconnect;
- add a capture-poll fallback mode;
- test against isolated real tmux socket and fake transport.

Acceptance:

- the terminal attaches to `tmux_socket_path` and `tmux_session_name`;
- closing the app or terminal view does not stop project CCB state;
- app reconnect returns to the same project target or requires refresh;
- multiline paste uses tmux paste-buffer strategy where possible.

## Package N5: Pairing And Host Profile

Goal: make setup scan-first instead of manual configuration.

Server work:

- `ccb mobile serve` prints QR and local/tailnet URL;
- one-time pairing token creates device profile;
- gateway stores/revokes device tokens.
- pairing payload carries route provider metadata such as LAN, tailnet, or
  Cloudflare Tunnel.

App work:

- QR scanner and paste-link fallback;
- host profile storage;
- connection status and re-pair UI;
- optional SSH-direct profile fields.

Acceptance:

- phone scans QR and creates a host profile;
- reconnect works after app restart;
- revoked token cannot list projects;
- pairing payload does not expose long-lived private keys.

## Package N5.5: Cloudflare Tunnel Route Provider

Goal: support phones outside the server LAN without building a custom relay.

Server work:

- make `ccb mobile serve --listen 127.0.0.1:<port>` the safe tunnel default;
- generate QR with `route_provider: cloudflare_tunnel`;
- document `cloudflared tunnel run ccb-mobile`;
- expose `/v1/health` and `/v1/capabilities`;
- ensure CCB token revocation works independently of Cloudflare configuration.

App work:

- store route provider metadata on the host profile;
- connect through Cloudflare URL using the same `GatewayTransport`;
- show tunnel/gateway diagnostics;
- preserve projects/favorites if the route URL changes.

Acceptance:

- phone on cellular can pair and open a CCB terminal through Cloudflare Tunnel;
- LAN/tailnet and Cloudflare profiles use the same screens and endpoint
  schemas;
- revoked CCB device token blocks access even when the tunnel URL is reachable;
- terminal reconnect does not replay stale input.

## Package N6: Project Registry And ProjectView

Goal: replace fixtures with live CCB project data.

Server/gateway work:

- project registry with favorites/recent state;
- wrapper around `ccbd` line-delimited JSON RPC;
- ProjectView polling and delta detection.

App work:

- live project list;
- project detail with windows, agents, Comms, health, callbacks, and
  completion state;
- stale/offline/degraded UI states.

Acceptance:

- app lists CCB projects without listing unrelated tmux sessions;
- unavailable `ccbd` degrades safely;
- ProjectView updates do not reconnect the terminal;
- favorite ordering survives app restart.

## Package N7: Agent And Window Focus

Goal: make tapping named agents/windows use CCB authority.

Work:

- gateway or SSH wrapper calls `project_focus_agent`;
- gateway or SSH wrapper calls `project_focus_window`;
- refresh ProjectView after focus;
- handle stale namespace epoch.

Acceptance:

- focus calls include project id and namespace epoch;
- pane id alone is rejected;
- stale epoch returns a refresh-required state;
- UI never calls raw `tmux select-pane` for CCB agent focus.

## Package N8: Markdown And Math Content

Goal: render CCB content in a mobile reading surface.

CCB work:

- add or expose a content route that resolves ask/reply/Comms/text artifact ids;
- refuse arbitrary host file paths;
- return render hints and previews.

App work:

- Markdown renderer with GFM basics;
- inline/block math renderer;
- code copy, table scroll, raw source toggle;
- link policy for local file/image references.

Acceptance:

- content loads by id, not by raw path;
- formulas render or degrade clearly;
- long replies and artifacts are readable on phone and iPad;
- terminal capture is not the authoritative Markdown source.

## Package N9: Notifications And Deep Links

Goal: notify on completion and attention without terminal scraping.

Work:

- derive first events from ProjectView/Comms deltas;
- define local/gateway acknowledgement state;
- add deep links to project + agent/window/content;
- use local notifications first; cloud push is deferred.

Acceptance:

- duplicate deltas do not spam notifications;
- notification opens the correct project target;
- completion, failure, blocked, callback-waiting, and unhealthy events are
  distinguishable.

## Package N10: Lifecycle Controls

Goal: wake/open/close/stop projects through CCB-owned lifecycle.

Work:

- `wake`: start/open project backend if allowed;
- `open`: select project and terminal target;
- `close`: close mobile view only;
- `stop`: CCB shutdown semantics with confirmation;
- keep `force_stop` admin-only.

Acceptance:

- close never stops `ccbd`, project tmux session, or provider panes;
- stop never calls raw `tmux kill-server`;
- lifecycle actions require explicit scope;
- stopped project can be woken and then opened.

## CCB Core Work Packages

### CCB-A: Gateway Launcher

Purpose: expose local/tailnet/Cloudflare pairing and gateway transport.

Likely files:

- CLI command registration under `lib/cli/`;
- launcher/service module for `ccb mobile serve`;
- docs for LAN/Tailscale usage.

Acceptance:

- command prints URL and QR;
- stopping the gateway does not stop project daemons;
- Cloudflare route metadata can be included in QR without changing endpoint
  schemas;
- source runtime validation follows existing `ccb_test` isolation rules.

### CCB-B: Mobile JSON Wrappers

Purpose: support SSH direct transport and tests without a long-running gateway.

Commands:

- `ccb mobile projects --json`;
- `ccb mobile project-view --project <id> --json`;
- `ccb mobile project-info --project <id> --json`;
- `ccb mobile focus-agent --project <id> --agent <name> --json`.

Acceptance:

- wrappers call the same internal authority as the gateway;
- output includes tmux socket path, session name, namespace epoch, and
  ProjectView identity fields;
- wrappers do not expose arbitrary tmux sessions.

### CCB-C: Content Endpoint

Purpose: provide full Markdown/artifact text by id.

Likely files:

- `lib/ccbd/socket_client_runtime/endpoints.py`;
- content lookup service under `lib/ccbd/`;
- tests for artifact validation and path safety.

Acceptance:

- endpoint resolves ask/reply/Comms/text artifact ids;
- endpoint refuses arbitrary file paths;
- ProjectView remains compact.

### CCB-D: Event Cursor

Purpose: make mobile notifications more reliable than ProjectView diffing.

Initial alternative:

- keep gateway-side ProjectView delta detection for Alpha.

MVP endpoint:

- cursor-based event list or streaming subscription;
- stable event ids for reconnect and acknowledgement.

## First Vertical Slice Checklist

Implement only:

1. Package N1: native repo baseline.
2. Package N2: CCB data model with fixtures.
3. Package N3: socket-aware tmux command layer.
4. Package N4: terminal transport to one manually configured CCB project.

Manual validation:

1. start an isolated test CCB project outside `ccb_source`;
2. read project `tmux_socket_path` and `tmux_session_name`;
3. configure those facts in the app fixture/profile;
4. open terminal on Android emulator/device and iPad simulator/device;
5. type and paste into the terminal;
6. background/resume and reconnect;
7. verify CCB project, tmux session, and provider panes remain alive.

Pass/fail:

- pass if terminal is usable and close does not affect CCB;
- fail if the app connects to default tmux, exposes unrelated sessions, or
  corrupts the project layout.

## Alpha Checklist

Add:

1. Package N5: pairing/host profile.
2. Package N5.5: Cloudflare Tunnel route provider if remote alpha is required.
3. Package N6: live ProjectView.
4. Package N7: agent/window focus.
5. Package N8: Markdown/math drawer.
6. Basic notifications from ProjectView/Comms deltas.

Alpha acceptance:

- frequent projects list works;
- named agents are visible and switchable;
- stale namespace epoch locks or refreshes the UI;
- Markdown/code/table/math content is readable on phone and iPad;
- destructive tmux controls remain absent.

## MVP Checklist

Add:

1. Package N9: notification acknowledgement and deep links.
2. Package N10: lifecycle controls.
3. CCB-C: content endpoint if not already landed.
4. device revocation and scopes.
5. documented Cloudflare Tunnel setup for not-on-LAN access.

MVP acceptance:

- QR setup is simple enough for normal use;
- reconnect is stable across app backgrounding and network loss;
- completion and callback reminders do not depend on terminal scraping;
- wake/stop uses CCB lifecycle semantics;
- app is usable on phone and iPad layouts.
