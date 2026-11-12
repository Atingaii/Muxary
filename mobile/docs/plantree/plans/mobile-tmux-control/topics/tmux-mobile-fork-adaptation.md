# tmux-mobile Fork Adaptation

Date: 2026-06-18
Status: Superseded by Decision 005 for primary client base; retained as a
server-side gateway and tmux behavior reference.

## Purpose

Define how tmux-mobile can inform a CCB phone/iPad remote-control product.
Earlier analysis treated tmux-mobile as the preferred first implementation
base. Decision 005 moves the primary app base to native Flutter, while keeping
tmux-mobile useful for server-side WebSocket/PTY/tmux gateway design.

The goal is not to build an independent mobile agent app. The goal is to remote
control server-side CCB tmux panes with a mobile-optimized terminal, while CCB
metadata improves project selection, pane targeting, safety, Comms, and
Markdown reading.

## Why tmux-mobile Still Matters

tmux-mobile already matches the clarified product center:

- server-hosted web terminal;
- phone browser as a thin client;
- xterm.js-style terminal interaction;
- tmux socket/path configuration;
- session/window/pane listing;
- terminal attach, input, resize, and reconnect mechanics;
- common deployment path through LAN or tunnel.

That is still close to "remote into the server CCB tmux pane", but it is not
the best primary base for native Android, iOS, and iPadOS apps.

## Product Boundary

The adapted product should be "tmux-mobile for CCB", not "CCB rewritten as a
mobile app".

Keep:

- server-side process owns terminal access;
- mobile client renders and controls server tmux;
- CCB continues running on the server;
- CCB project tmux sessions remain the primary workspace;
- mobile/iPad UX optimizes remote terminal control.

Add:

- CCB project discovery;
- CCB project socket/session binding;
- CCB agent/window labels;
- CCB focus actions;
- CCB stale namespace/pane validation;
- CCB Comms and callback indicators;
- Markdown reader for CCB message/artifact content.

Avoid:

- arbitrary host tmux browsing by default;
- standalone mobile agent execution;
- mobile-created CCB projects;
- raw destructive tmux operations against CCB sessions;
- treating pane ids as stable deep-link identity.

## Adaptation Map

### Keep From tmux-mobile

- web terminal UI foundation;
- terminal WebSocket path;
- tmux attach/control plumbing;
- socket-name/socket-path configuration ideas;
- client reconnect behavior;
- mobile keyboard and terminal controls;
- deployment model suitable for LAN/tailnet/tunnel.

Source review note:

- tmux-mobile's tmux CLI executor supports `TMUX_MOBILE_SOCKET_NAME` and
  `TMUX_MOBILE_SOCKET_PATH`.
- Its PTY attach path currently does not pass that socket name/path into
  `tmux attach-session`.
- CCB adaptation must make terminal attach socket-aware before using project
  tmux sockets.

### Replace Or Wrap

- session list becomes CCB project list;
- raw tmux socket selection becomes CCB project socket selection;
- window/pane list is annotated and filtered by CCB project/agent metadata;
- select-window/select-pane should call CCB focus endpoints when targeting
  CCB-managed windows and agents;
- paste should use CCB/tmux-safe buffer strategy where possible;
- destructive pane/window/session operations should be removed from the normal
  UI or routed through explicit CCB admin endpoints.

### Add

- `ccb mobile serve` entrypoint or equivalent wrapper;
- project registry from `.ccb` anchors and `ccbd` lifecycle records;
- ProjectView side panel;
- agent quick switcher;
- Comms/callback attention badges;
- Markdown content drawer;
- QR/device pairing;
- permission scopes for view, terminal input, content, focus, and admin.

## CCB-Specific Runtime Rules

- Connect to the tmux socket path reported by CCB namespace state.
- Treat namespace epoch as a stale-view guard.
- Resolve panes by CCB user options where possible:
  `@ccb_project_id`, `@ccb_role`, `@ccb_slot`, `@ccb_window`,
  `@ccb_managed_by`.
- Use pane id only as current evidence.
- On pane recovery or project restart, refresh CCB metadata before accepting
  further input.
- Detaching a mobile terminal must not stop `ccbd`, tmux session, or provider
  panes.

## UI Shape

Primary screen:

- full-screen terminal attached to the selected CCB project;
- top or side project/agent switcher;
- special key bar;
- paste/composer drawer;
- project health and callback badges;
- read-only lock or input-enabled state.

Secondary screens:

- project picker;
- agent/window picker;
- Comms and callback list;
- Markdown reader;
- device/settings page.

On iPad, a split view is useful:

- terminal on the right;
- project/agent/Comms navigation on the left;
- Markdown drawer or overlay for reading long agent output.

On phone, keep terminal full-screen and use bottom sheets for navigation and
Markdown.

## Implementation Sequence

1. Fork or vendor tmux-mobile outside the CCB core runtime.
2. Add a CCB project registry endpoint that returns active project socket and
   session facts.
3. Replace generic session list with CCB project list.
4. Attach terminal stream to the selected CCB project's tmux session.
5. Add ProjectView side data.
6. Route agent/window switching through `project_focus_agent` and
   `project_focus_window`.
7. Add paste and input validation against current namespace/pane evidence.
8. Add Comms and Markdown drawers.
9. Lock down destructive tmux operations.

## Risks

- tmux-mobile's grouped-session model may create state CCB does not own.
- Phone resize may affect desktop tmux layout if attach behavior is not
  controlled.
- Generic session/pane operations may bypass CCB authority.
- CCB project discovery must not accidentally include source checkout runtime
  state or unrelated tmux sessions.
- Public tunnel exposure needs strong pairing, token, and permission defaults.

## Acceptance Criteria

- A phone/iPad can open one active CCB project and interact with its server
  tmux pane.
- Project switching uses CCB project identity, not raw tmux session names.
- Agent/window switching keeps CCB sidebar/project view coherent.
- Terminal input cannot continue against stale namespace/pane evidence after
  project restart or pane recovery.
- Destructive tmux operations are unavailable by default.
- Comms/Markdown features enhance the remote session without replacing it.
