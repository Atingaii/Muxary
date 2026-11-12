# Terminal Transport Spike

Date: 2026-06-17
Status: Draft

## Problem

CCB needs mobile terminal visibility and input as the main product workflow,
but normal tmux remote approaches can conflict with CCB's managed project
layout.

Risks:

- a small phone terminal can resize or reflow the canonical desktop workspace;
- a generic attached client can change active window/pane focus unexpectedly;
- per-client grouped sessions can create tmux state outside `ccbd` authority;
- stale pane ids can accept input after pane recovery if not revalidated;
- terminal disconnect must not imply project shutdown.

The current product direction is a native Flutter client for Android,
iOS, and iPadOS. The terminal transport still belongs on the server side:
the app should connect to a CCB-approved transport, and that transport should
bind to the selected project tmux socket/session only after CCB target
validation.

## Candidate Transports

### Native SSH Direct Attach

Method: the app opens an SSH connection to the host, starts a PTY, and runs a
CCB-provided attach command such as `tmux -S <project_socket> attach-session`
or a `ccb mobile terminal attach --project ...` wrapper.

Pros:

- fastest native vertical slice if the user already has SSH access;
- no first-release gateway daemon is required;
- maps well to Flutter terminal libraries and ServerBox-style connection code;
- can be provisioned by QR code with host, user, port, project id, and attach
  command template.

Cons:

- raw SSH credentials and host-key UX become mobile product concerns;
- control-plane calls need CLI JSON wrappers or a separate local gateway;
- less friendly for non-technical pairing than a purpose-built gateway;
- reconnect/resume needs app-owned session logic.

Recommendation: use as a developer and first vertical-slice path, but expose
it through CCB-shaped QR pairing and command wrappers instead of a generic SSH
terminal UI.

### Capture Polling

Method: call CCB-mediated pane capture periodically or on demand.

Pros:

- safest;
- read-only;
- does not attach a tmux client;
- easy to bind to agent/window identity;
- enough for MVP monitoring and debugging.

Cons:

- not a true interactive terminal;
- inefficient if used at high frequency;
- requires ANSI/cell handling work for rich rendering.

Recommendation: keep as a supporting fallback and diagnostics mode, not the
primary product path.

### Gateway Pty-Backed `tmux attach-session`

Method: a server-side gateway opens a PTY running `tmux attach-session` to the
project session and streams it to the native app over WebSocket or another
binary stream.

Pros:

- common pattern in ChatMux, tmux-mobile, ttyd, and WeTTY-style clients;
- provides a real terminal quickly;
- easy to prototype.
- hides tmux socket paths and host shell details from the phone;
- pairs well with Paseo-style QR pairing and relay later.

Cons:

- attached client dimensions can affect tmux layout;
- focus and status line behavior are session-level, not CCB-agent-level;
- raw input is easy to send before identity checks are complete;
- closing or resizing clients needs careful handling.

Recommendation: use as the preferred product transport after the SSH-direct
vertical slice, because it gives CCB one place to enforce target validation,
token scopes, reconnect, and event delivery.

### Tmux Control Mode

Method: use tmux control mode to subscribe to output and send input in a more
structured way.

Pros:

- may avoid some full-client attach side effects;
- can expose structured pane events;
- better fit for a gateway that owns multiplexing.

Cons:

- needs careful tmux-specific parsing and lifecycle handling;
- may still need a size model;
- more implementation complexity than PTY attach.

Recommendation: run a focused spike as a possible hardening path if PTY attach
has unacceptable resize or focus side effects.

### Managed Grouped Sessions

Method: create per-device grouped sessions so each mobile client has isolated
focus while sharing windows.

Pros:

- strong focus isolation;
- used effectively by tmux-mobile-style approaches;
- can make multiple phone/browser clients less disruptive.

Cons:

- creates extra tmux sessions that CCB does not currently model;
- can confuse project/session authority unless `ccbd` owns them;
- cleanup and generation handling need first-class runtime records.

Recommendation: evaluate because tmux-mobile uses this style effectively, but
ship it only if `ccbd` explicitly owns mobile view-client state and cleanup.

## Spike A: Native SSH Direct Attach

Goal: prove the native app can safely control a server-side CCB tmux session
through a socket-aware attach command.

Scope:

- run against an isolated test CCB project, not the source checkout runtime;
- provision host/project/command through QR code or equivalent import;
- attach to the project session through the CCB project socket with
  `tmux -S <socket>`;
- open from phone-sized and iPad-sized app layouts;
- type, paste, resize, rotate, reconnect, and close;
- switch agents/windows through CCB CLI JSON wrappers or gateway endpoints;
- reject input after namespace epoch or pane evidence changes.

Pass conditions:

- terminal control feels like a normal mobile tmux remote;
- desktop layout is not corrupted by phone/iPad resize;
- closing the client does not stop `ccbd`, tmux session, or provider panes;
- stale target evidence fails closed;
- unrelated tmux sessions are not exposed.

## Spike B: Gateway Pty Attach

Goal: prove the same native terminal surface can use a CCB gateway transport
without changing the app's project/agent UX.

Scope:

- run `ccb mobile serve` or a prototype sidecar on the server;
- pair the app through a Paseo-style QR offer;
- open a terminal token for one project/agent target;
- stream terminal bytes over WebSocket binary frames;
- reconnect after app background/foreground and network changes;
- verify device scopes for view, focus, content, terminal input, and lifecycle.

Pass conditions:

- the app can switch between SSH direct and gateway transports behind one
  terminal interface;
- gateway validates project id, namespace epoch, selected agent/window, and
  current pane evidence before accepting input;
- disconnect leaves project/session/agents alive;
- pairing is simple enough for non-expert use.

## Spike C: Control Mode Feasibility

Goal: determine whether tmux control mode should replace or harden PTY attach.

Scope:

- run against an isolated test CCB project, not the source checkout runtime;
- open a control-mode client to the project socket/session;
- subscribe to one target pane;
- send text and special keys only after target revalidation;
- resize without changing canonical desktop layout, or document why impossible.

Pass conditions:

- mobile stream can follow the selected pane;
- desktop layout and focus do not drift unexpectedly;
- disconnect leaves project/session/agents alive;
- implementation complexity is acceptable compared with PTY attach.

## Spike D: Managed Grouped Session Feasibility

Goal: determine whether tmux-mobile-style grouped sessions can isolate mobile
focus without creating unmanaged CCB runtime state.

Scope:

- create a per-device grouped session for an isolated CCB test project;
- record it as explicit mobile view-client state;
- test multiple phones and a desktop client at the same time;
- verify focus, window selection, resize, reconnect, and cleanup behavior;
- verify project restart and `ccb kill` cleanup.

Pass conditions:

- grouped session state is visible to and owned by CCB;
- cleanup is deterministic;
- focus isolation is better than PTY attach;
- no stale grouped sessions survive project shutdown.

## Regression Cases

Any interactive transport needs tests for:

- namespace epoch changes after project restart;
- agent pane respawn changes pane id;
- sidebar window/pane exists alongside agent panes;
- multiple phones connected to same project;
- desktop tmux client attached at the same time;
- mobile rotation or terminal resize;
- network reconnect after token expiry;
- `ccb kill` while phone is connected;
- project offline while app is open.

## Current Recommendation

Phase 1 should ship an interactive native tmux remote for CCB project sessions.
Start with socket-aware SSH direct attach if it gets the native app to a real
CCB terminal fastest, then move the same app surface onto a CCB gateway
transport for QR pairing, scoped tokens, event delivery, and relay readiness.
Keep capture snapshots as fallback/diagnostics. Evaluate tmux control mode and
managed grouped sessions only after real resize, focus, and multi-client risks
are measured.
