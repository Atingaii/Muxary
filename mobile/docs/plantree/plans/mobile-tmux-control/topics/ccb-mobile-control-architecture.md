# CCB Mobile Control Architecture

Date: 2026-06-17

## Core Position

CCB mobile control should be an agent-first remote client for server-side CCB
sessions. The phone or iPad is a readable control surface for projects and
named agents already running on the server, with raw tmux/terminal control as
an explicit fallback, not an independent mobile agent app.

It should still be CCB-scoped, not a generic tmux browser. Generic tmux clients
organize around SSH hosts, tmux sessions, windows, and panes. CCB organizes
around projects, `ccbd` backends, configured agents, configured windows, Comms,
provider activity, and runtime reconciliation.

## Recommended Shape

```
native Flutter app on phone/iPad
  |
  | QR pairing, device profile, reconnect
  v
transport adapter
  |
  | GatewayTransport: HTTPS/WebSocket to ccb mobile gateway
  | SshTransport: SSH exec/PTY fallback for direct tmux mode
  v
server-side CCB
  |
  | control: ccbd project_view / focus / content / lifecycle
  | terminal: tmux -S <project_socket> attach/control/capture
  v
project tmux namespace and managed provider panes
```

The mobile gateway can be a new `ccb mobile serve` process or a `ccbd` sidecar.
The app may also keep an SSH direct transport for developer/fallback use. The
important boundary is that every normal product action is CCB-scoped and
project-aware, not an arbitrary host tmux session action.

## Project Discovery

The mobile home screen should list CCB projects. Opening a project should land
in an agent-first project workspace for that project.

Initial discovery options:

- explicit project registry written by `ccb mobile serve`;
- recent `.ccb` anchors known to the user account;
- manually paired project QR code from an active `ccb` foreground;
- later: multi-host registry with host health.

Avoid blind filesystem scans by default. A project entry should resolve to a
`.ccb` anchor, then to current `ccbd` lifecycle/socket/session facts.

## Project View As Main Data Model

`project_view` already exposes the shape mobile needs:

- project id, root, display name;
- `ccbd` generation, health, heartbeat, namespace epoch;
- tmux socket path, session name, active window, active pane id;
- configured windows and sidebar state;
- configured agents, provider, window, pane evidence, activity, queue depth,
  callback-waiting state, runtime health, and provider runtime details;
- Comms data.

Mobile should subscribe to this model or poll it initially. New mobile features
should extend this model instead of inventing a second authority source.

## Agent And Window Focus

Mobile taps should call existing focus endpoints:

- `project_focus_window`
- `project_focus_agent`

Those endpoints already validate namespace epoch, find panes using CCB tmux
user options, select the correct pane/window, and refresh project view/sidebar
state.

The phone should not call `tmux select-pane` or `select-window` directly.

## Ask And Composer

For this product direction, the primary mobile path is structured CCB control:

- select one agent in the project workspace;
- submit a request to an agent;
- submit a callback response;
- silence/background a task where appropriate;
- inspect queue depth and completion state;
- open Comms items and Markdown/content views.

Raw terminal remains an explicit control/debug path:

- type into CCB-managed panes;
- use mobile special keys;
- paste text or commands;
- switch/focus project windows and agent panes;
- reconnect without disturbing the server tmux session.

The app should not force all work through ask/composer, but it should also not
force reading and routine control through terminal scraping. Its main reason to
exist is CCB-aware mobile control of projects, agents, content, and terminal
fallback when needed.

## Pane Snapshots

The safest terminal MVP is pane snapshot viewing:

- capture selected pane history with text mode and ANSI mode;
- show pane title, agent slot, runtime generation, last update time, and
  whether the pane is alive;
- refresh on demand or at a low polling rate;
- deep-link from agent rows and Comms items to relevant pane snapshots.

CCB already has capture helpers that can be wrapped by a `ccbd` endpoint.

## Interactive Terminal

Interactive terminal mode should be a separate, explicit action.

Recommended constraints:

- issue a short-lived terminal token;
- bind the token to project id, namespace epoch, target slot/window, and current
  pane evidence;
- revalidate before accepting input;
- permit read-only terminals by default;
- require explicit permission for raw input;
- use a CCB-owned paste-buffer path for multiline text;
- keep destructive tmux operations behind CCB admin endpoints.

The main technical choice is output transport:

- capture-polling is safest and easiest, but not fully interactive;
- pty-backed `tmux attach-session` is simple, but can resize or shift the
  canonical workspace if not carefully isolated;
- tmux control mode may better support per-pane streams without normal client
  attachment side effects, but needs a focused spike;
- per-client grouped sessions isolate focus, but should be deferred until
  `ccbd` explicitly owns mobile view-client state.

## Action Matrix

Safe default mobile actions:

- list projects;
- open project view;
- inspect agents/windows/Comms;
- focus agent/window through `ccbd`;
- submit ask/composer text;
- read pane snapshots;
- view logs/diagnostics summarized from CCB authority.

Permissioned actions:

- raw terminal input;
- paste multiline text into a pane;
- interrupt an agent pane;
- restart a managed agent;
- reload project config;
- restart project panes.

Admin-only actions:

- `ccb kill`;
- clear provider context;
- destructive pane/window operations;
- changing project registry or remote exposure settings.

Do not expose directly:

- `tmux kill-server`;
- raw `kill-pane`/`split-window`/`new-session` against project sessions;
- session/window renaming that bypasses `.ccb/ccb.config`;
- treating stale `pane_id` as durable identity.

## Security Model

The gateway is the trust boundary.

Minimum controls:

- QR pairing with short-lived bootstrap tokens;
- stable device tokens after pairing;
- permission scopes such as `view`, `ask`, `terminal-input`, and `admin`;
- TLS, trusted local network, tailnet, CCB Relay, or Cloudflare Tunnel for
  transport;
- terminal WebSocket tokens that are single-use and short-lived;
- audit events for ask, admin actions, focus changes, and raw-input session
  start/stop;
- no default storage of SSH credentials in a browser client.

Remote access tiers:

1. local host only for development;
2. LAN or Tailscale for local/trusted development;
3. CCB Relay for the default not-on-LAN release;
4. Cloudflare Tunnel and self-hosted relay as advanced routes.

## Multi-Project Implications

Each project has independent lifecycle, namespace, session, provider state, and
Comms. Mobile must not merge them into one tmux session list.

Recommended mobile home layout:

- host health and gateway status;
- project cards/rows with project name, root, health, active agents, waiting
  callbacks, unread Comms, and last activity;
- per-project detail with windows, agents, Comms, pane snapshots, and actions;
- deep links by project id plus target slot/window, not pane id alone.

## Multi-Agent Implications

Agent identity is the CCB slot/config identity, not the tmux pane number.

Mobile should show:

- agent name and provider;
- window membership/order;
- state: active, idle, waiting, unhealthy, restarting, missing, or unknown;
- queue depth and current task;
- callback/comms attention;
- pane evidence only as diagnostics.

This matches CCB's multi-agent value better than a raw terminal grid.

## Forking Guidance

Best native path for the clarified agent-first server-remote product:

- ServerBox as the preferred native Flutter fork candidate if AGPL is
  acceptable for the mobile app component;
- MuxPod as the primary tmux-specific mobile UX and command-strategy reference;
- tmux-mobile as a MIT reference for server-side WebSocket/xterm/tmux gateway
  behavior;
- Paseo as the strongest pairing, relay, daemon/client protocol, terminal
  frame, and agent workflow reference;
- Termux, Blink, ConnectBot, mosh, and ttyd as narrower reference points.

If the mobile app needs a permissive license, start a smaller Flutter app and
reimplement the needed MuxPod/ServerBox ideas rather than directly forking
AGPL code.

## First Prototype Shape

Prototype the smallest native CCB tmux remote flow:

1. create a dedicated Flutter app/fork baseline;
2. pair or manually configure one CCB host/project;
3. open one project's server-side tmux session using
   `tmux -S <tmux_socket_path> attach-session -t <tmux_session_name>`;
4. type, paste, resize, background, resume, and reconnect from phone/iPad;
5. list registered CCB projects and favorites through a fake then real CCB
   transport;
6. tap an agent/window and call `project_focus_agent` or
   `project_focus_window`;
7. show ProjectView status, Comms, and Markdown drawers around the terminal;
8. prevent unrelated tmux sessions and destructive operations by default.

That proves the CCB-specific value without turning the product into a separate
mobile agent runtime.
