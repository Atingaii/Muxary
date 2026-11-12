# tmux-mobile Source Deep Dive

Date: 2026-06-18
Status: Draft

## Source Checkout

Repository: <https://github.com/DagsHub/tmux-mobile>

Local research checkout:

- path: `/tmp/ccb-mobile-research/tmux-mobile`
- commit: `493c404bc793d4599aa3f77c29c720adebed4d2e`
- commit date: 2026-02-19
- commit subject: `feat: make pane zoom sticky across pane switches (#59)`
- package version: `0.0.8`
- license: MIT

This checkout is read-only research input for the CCB mobile plan. It should
not become source validation state for `ccb_source`.

## Documents Read

- `README.md`
- `SECURITY.md`
- `SPEC.md`
- `AGENTS.md`
- `package.json`
- backend source under `src/backend/`
- frontend source under `src/frontend/`
- test harness and integration/smoke tests under `tests/`

## User-Facing Behavior

tmux-mobile is distributed as an npm package:

```bash
npx tmux-mobile
```

It starts a Node backend on `127.0.0.1:8767`, serves a React frontend, and can
start a Cloudflare quick tunnel. The CLI prints a local URL, tunnel URL when
enabled, token query parameter, QR code, and password when password auth is
enabled.

Important documented options:

- `--port`
- `--password`
- `--[no-]require-password`
- `--no-tunnel`
- `--session`
- `--scrollback`
- `--debug-log`

Important environment variables:

- `TMUX_MOBILE_SOCKET_NAME`
- `TMUX_MOBILE_SOCKET_PATH`
- `TMUX_MOBILE_DEBUG_LOG`
- `TMUX_MOBILE_FORCE_SCRIPT_PTY`
- `TMUX_MOBILE_TRACE_TMUX`

## Tech Stack

Backend:

- Node.js 20+
- Express
- `ws`
- `node-pty`
- yargs
- optional `cloudflared`

Frontend:

- React 19
- Vite
- xterm.js 6
- FitAddon

Tests:

- Vitest unit/integration tests
- Playwright e2e tests
- fake tmux and fake PTY harnesses
- optional real tmux smoke test

## Runtime Architecture

The app has two WebSocket channels:

- `/ws/control`: JSON control plane for auth, state, tmux mutations, scrollback,
  session selection, and compose send.
- `/ws/terminal`: terminal data plane for xterm.js input/output and resize.

The control client authenticates first. The server returns a `clientId`, and the
terminal socket must authenticate with the same token/password plus that
`clientId`. Terminal streams are therefore bound to a control client.

## Backend Modules

### `src/backend/cli.ts`

Responsibilities:

- parse CLI flags;
- create token/password;
- create runtime config;
- construct `TmuxCliExecutor`, `NodePtyFactory`, and server;
- optionally start Cloudflare quick tunnel;
- print URLs and QR code;
- handle shutdown.

CCB adaptation:

- add `ccb mobile serve` or a wrapper around this startup path;
- replace default generic tmux session with CCB project registry;
- support LAN/tailnet first, with tunnel as optional user-chosen transport;
- avoid auto-installing cloudflared by default in stricter environments.

### `src/backend/server.ts`

Responsibilities:

- serve frontend and `/api/config`;
- own control and terminal WebSocket servers;
- authenticate both sockets;
- create one control context per client;
- create one terminal runtime per control client;
- create a grouped tmux session per mobile client;
- route control mutations to `TmuxGateway`;
- broadcast tmux state monitor updates.

Important behavior:

- mobile sessions are named `tmux-mobile-client-<clientId>`;
- initial attach filters those mobile sessions out of the session picker;
- control-client close shuts down terminal clients and kills the grouped mobile
  session;
- state monitor still snapshots all sessions, including mobile sessions.

CCB adaptation:

- replace generic session picker with project picker;
- replace mobile session prefix with CCB-scoped mobile view-client identity;
- filter or annotate CCB mobile grouped sessions in state;
- route CCB agent/window selection through `project_focus_agent` and
  `project_focus_window`;
- remove or gate `new_session`, `new_window`, `split_pane`, `kill_window`, and
  `kill_pane` for normal users;
- add project lifecycle, favorite project, notification, content, and
  ProjectView messages.

### `src/backend/tmux/cli-executor.ts`

Responsibilities:

- run tmux with `execFile`;
- support `socketName` via `tmux -L`;
- support `socketPath` via `tmux -S`;
- list sessions, windows, panes;
- create sessions and grouped sessions;
- select, split, kill, zoom panes/windows;
- capture scrollback.

Positive fit:

- argument-array execution is a good safety base;
- socket path support is exactly what CCB project sockets need;
- format-string parsing is small and testable.

CCB adaptation:

- add CCB tmux format fields such as `@ccb_project_id`, `@ccb_role`,
  `@ccb_slot`, `@ccb_window`, and `@ccb_managed_by`;
- expose CCB pane/window metadata to frontend;
- treat pane id as evidence only;
- stop exposing raw destructive tmux methods through the default control
  protocol.

### `src/backend/pty/node-pty-adapter.ts`

Responsibilities:

- spawn a PTY running `tmux attach-session -t <session>`;
- fall back to `script(1)` when node-pty is unavailable;
- strip inherited `TMUX`/`TMUX_PANE` env vars.

Critical CCB finding:

- `TmuxCliExecutor` supports socket path/name, but `NodePtyFactory` currently
  does not pass `-S` or `-L` to `tmux attach-session`.
- A CCB fork must make PTY attach socket-aware before connecting to project
  tmux sockets.

Required seam:

```ts
spawnTmuxAttach({
  socketPath,
  socketName,
  sessionName
})
```

The same socket prefix must be used for both CLI control commands and PTY
attach.

### `src/backend/pty/terminal-runtime.ts`

Responsibilities:

- manage one PTY process;
- attach to session;
- forward data/exit events;
- write terminal input;
- resize PTY.

CCB adaptation:

- bind runtime to project id, namespace epoch, session name, and socket path;
- reject or lock input when project namespace changes;
- distinguish mobile view close from CCB project stop.

### `src/backend/state/state-monitor.ts`

Responsibilities:

- poll `buildSnapshot()` periodically;
- serialize session state and publish only when changed;
- support forced publish after control mutations;
- drop stale concurrent forced snapshots.

CCB adaptation:

- poll `project_view` in addition to tmux state, or replace tmux snapshot as
  the primary side-data source;
- emit completion/attention notifications from ProjectView deltas;
- keep tmux polling focused on the selected project socket, not global tmux
  sessions.

### `src/backend/auth/auth-service.ts`

Responsibilities:

- generated token;
- optional password;
- in-memory verification.

Current posture:

- all-or-nothing access;
- no scopes, identities, lockout, or revocation except restart;
- password can be saved in browser localStorage.

CCB adaptation:

- introduce paired device identity;
- introduce scopes/profiles;
- make terminal input common for trusted devices but keep lifecycle/admin
  separate;
- add revocation without server restart.

## Frontend

`src/frontend/App.tsx` is currently a single large React component.

It owns:

- xterm.js instance and FitAddon;
- control WebSocket;
- terminal WebSocket;
- auth/password flow;
- session/window/pane snapshot state;
- drawer;
- toolbar and special keys;
- compose bar;
- scrollback overlay;
- theme picker;
- sticky zoom.

CCB adaptation should not rewrite it all at once. The useful first extraction
seams are:

- protocol client hook;
- terminal host component;
- toolbar component;
- project/agent drawer;
- scrollback/content drawer;
- auth/pairing flow.

## UI Features Worth Keeping

- xterm full-screen terminal as main surface;
- mobile special key toolbar;
- direct terminal input and compose mode;
- paste support;
- scrollback overlay using `capture-pane`;
- sticky zoom preference;
- theme persistence;
- session/window/pane drawer shape as a starting point;
- password overlay and QR startup flow.

## UI Features To Replace For CCB

- Sessions section becomes Projects/Favorites.
- Windows section becomes CCB windows plus tool windows.
- Panes section becomes named agents and active window panes.
- New Session/New Window/Split/Kill controls leave the normal UI.
- Session picker becomes project picker.
- Top title should show project/window/agent, not only window.
- Status indicator should show ProjectView health and notification state.

## Security Findings

The current security model is explicitly not multi-tenant or fine-grained.
Authenticated users can run commands as the OS user that launched
tmux-mobile.

Known gaps relevant to CCB:

- no scopes;
- no device identity or revocation;
- no origin allowlist;
- no rate limiting;
- token in URL;
- password in localStorage;
- all authenticated clients have full control;
- auto-install of cloudflared is not checksum-pinned.

CCB should treat tmux-mobile auth as a starting point only.

## Test Harness Value

tmux-mobile has a strong test base for adaptation:

- `FakeTmuxGateway` models sessions/windows/panes/grouped sessions;
- `FakePtyFactory` validates terminal stream binding;
- server integration tests cover auth, attach, grouped sessions, terminal I/O,
  scrollback, and sticky zoom;
- state monitor tests cover diffing and stale forced snapshots;
- real tmux smoke test uses isolated socket path.

CCB adaptation should preserve this test style and add fake CCB project and
ProjectView harnesses.

## Key Adaptation Risks

1. PTY attach must become socket-aware.
2. Grouped sessions must be recorded or bounded so CCB does not confuse them
   with project authority.
3. Mobile resize can affect tmux layout.
4. Generic destructive tmux commands must be removed or gated.
5. Project lifecycle wake/stop must call CCB semantics, not raw tmux kill.
6. Completion notifications need stable event semantics, not terminal scraping.
7. Markdown/math content should come from CCB message/artifact authority, not
   captured terminal text.
