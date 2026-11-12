# Source Research: Mobile And Tmux Remote Control

Date: 2026-06-17

## ChatMux

Project: <https://github.com/binjie09/ChatMux>
License: MIT

ChatMux is the closest reference for a self-hosted web/gateway tmux workspace.
It uses a Go gateway, React/TypeScript UI, xterm.js terminal rendering, SQLite,
Tauri, and Capacitor. The browser/mobile client does not SSH directly; it talks
to the gateway, and the gateway opens SSH/tmux sessions.

Useful patterns:

- gateway as the trust boundary;
- bearer-token API and one-time terminal WebSocket tokens;
- xterm.js terminal stream over WebSocket;
- tmux session/window listing through tmux format strings;
- `tmux attach-session` construction for terminal WebSocket sessions;
- command/composer policy separate from raw terminal input.

CCB fit:

- Good reference if CCB wants additional gateway/auth, packaging, or
  WebSocket-token patterns.
- Its generic SSH/tmux session model must be replaced with CCB project
  registry, `project_view`, `project_focus_*`, and CCB ask/composer APIs.
- It is less direct than tmux-mobile for a product whose main job is remote
  control of an existing server-side CCB tmux workspace.

Risk:

- Treating tmux sessions as the product identity would drift from CCB. In CCB,
  `.ccb` anchor, `ccbd`, namespace epoch, configured windows, and runtime
  records own identity; tmux session names and pane ids are evidence.

## tmux-mobile

Project: <https://github.com/DagsHub/tmux-mobile>
License: MIT

tmux-mobile is a small Node/web mobile client for local tmux, commonly exposed
with a Cloudflare tunnel. It supports tmux socket selection, password/token
access, xterm.js terminal attach, session/window/pane listing, and mobile
client cleanup. A notable pattern is creating per-client grouped sessions so
mobile clients have isolated focus.

Useful patterns:

- quick local web terminal proof of concept;
- `TMUX_MOBILE_SOCKET_NAME` and `TMUX_MOBILE_SOCKET_PATH` configuration;
- per-mobile-client session lifecycle;
- xterm.js backed `tmux attach-session`;
- practical tmux CLI wrappers for sessions, windows, panes, capture, and
  selection.

CCB fit:

- Best MIT reference for a server-hosted WebSocket/xterm/tmux gateway.
- The grouped-session idea is attractive for mobile focus isolation.
- Generic operations like split, kill, select, and create session should not be
  exposed directly in CCB.
- No longer the preferred mobile app base after the native Android/iOS
  requirement was clarified.

Risk:

- Grouped sessions can change focus semantics and create extra session state
  that CCB does not know about. They should only be used after `ccbd` gains an
  explicit mobile-view-client concept with recorded ownership and cleanup.
- Its PTY attach path must be made socket-aware before it can safely connect to
  CCB project tmux sockets.

## ServerBox

Project: <https://github.com/lollipopkit/flutter_server_box>
License: AGPL-3.0

Research checkout:

- path: `/tmp/ccb-mobile-research/serverbox`
- commit: `d845a6b`
- commit date: 2026-06-18
- commit subject: `Fix backup and restore format exception (#1196)`

ServerBox is a mature Flutter app for server management with iOS, Android,
desktop, SSH terminal, SFTP, process/systemd/docker features, foreground
service, and platform notification hooks. It uses `dartssh2` and a bundled/path
`xterm` package.

Useful patterns:

- native Flutter app structure and multi-platform packaging;
- SSH terminal with PTY execution;
- tmux attach/list/window-switch command builder;
- session/tab restore;
- Android foreground service and iOS Live Activity session tracking;
- virtual keys and mobile terminal UI patterns.

CCB fit:

- Preferred native fork candidate if an AGPL mobile component is acceptable.
- Much closer to "native phone/iPad app" than tmux-mobile or ttyd.
- Needs a CCB-first product model layered over or replacing its generic server
  dashboard.

Risk:

- Generic server-management scope is broader than CCB needs.
- Current tmux command builder does not support `tmux -S <project_socket>`.
- Existing generic tmux create/kill/window operations must be removed or
  gated in CCB mode.
- AGPL license should be accepted intentionally for the mobile app component.

## MuxPod

Project: <https://github.com/moezakura/mux-pod>
License: Apache-2.0

MuxPod is a mobile-first tmux client built with Flutter. It connects directly
over SSH, stores keys in Android Keystore, renders terminal output with xterm,
and offers a phone-optimized control surface.

Useful patterns:

- session/window/pane breadcrumb navigation;
- visual pane selector;
- special key bar and hold/swipe arrow-key gestures;
- pinch zoom and terminal font scaling;
- reconnect and input queue behavior;
- deep links into server/session/window/pane targets;
- multiline paste through tmux `load-buffer` and `paste-buffer`.

Research checkout:

- path: `/tmp/ccb-mobile-research/mux-pod`
- commit: `d3b400d`
- commit date: 2026-05-21
- commit subject: `fix(terminal): use load-buffer + paste-buffer for multi-line text (#51)`

CCB fit:

- Strongest tmux-specific UX reference for a native mobile client.
- Useful even if ServerBox is the actual fork base.
- Its command layer should be made CCB/socket-aware and wrapped by CCB project
  identity rather than direct arbitrary SSH/tmux mutations.

Risk:

- Direct SSH/tmux operations bypass `ccbd` authority. CCB should not expose
  mobile `kill-pane`, `split-window`, `kill-server`, or session mutation as raw
  client actions.
- The project is Android-first in its public README even though Flutter iOS
  project files exist.
- Its terminal surface relies heavily on command/capture polling rather than
  continuous `tmux attach`, which is useful as fallback but not enough by
  itself for all full-screen TUI workloads.

## Paseo

Project: <https://github.com/getpaseo/paseo>
License: AGPL-3.0-or-later

Paseo is not primarily a tmux remote client. It is a full open-source agent
daemon, protocol, app, relay, and SDK for controlling coding agents across
mobile, desktop, web, and CLI. It supports Claude Code, Codex, Copilot,
OpenCode, Pi, voice, pairing, relay/E2EE, and terminal streams.

Useful patterns:

- protocol-first daemon/client split;
- mobile and desktop apps on one protocol;
- terminal stream multiplexing with binary frames;
- terminal key encoding for complex key combinations;
- QR/pairing offer structure;
- notifications/attention-required events;
- timeline-style mobile agent UX.

CCB fit:

- Good architecture inspiration for pairing, terminal multiplexing, relay, and
  mobile agent workflows.
- Not a tmux-specific fork base for CCB.
- Stronger as the QR/gateway/relay reference than as the terminal/tmux code
  base.

Risk:

- AGPL code reuse is a product/licensing decision. For a permissive CCB mobile
  component, use Paseo as a reference unless adopting AGPL-compatible
  distribution intentionally.

## Termux App

Project: <https://github.com/termux/termux-app>
License: GPLv3-only for the app, with library/code exceptions noted in the
repository license.

Research checkout:

- path: `/tmp/ccb-mobile-research/termux-app`
- commit: `401bbe54b8f4e68302b1ff70678015a24628fb1d`
- commit date: 2026-06-05
- commit subject: ``Fixed: Do not add `BigTextStyle` to notification if big text is null``

Termux is a mature Android terminal application and local Linux environment.
It has strong terminal emulator, terminal view, extra keys, foreground service,
wake/wifi lock, notification, Android intent, and local shell session patterns.

Useful patterns:

- native Android terminal rendering and input handling;
- terminal extra keys and soft-keyboard handling;
- foreground service to keep sessions alive;
- notification and wake/wifi lock patterns;
- Android intent/plugin model for command execution;
- Markwon-based Markdown support in parts of the app/shared library.

CCB fit:

- Good reference or possible base for a future Android-native CCB client.
- Useful if CCB wants a phone app that feels more like a native terminal and
  less like a browser PWA.
- Better as a native client over a CCB gateway protocol than as a replacement
  for the server gateway itself.

Risks:

- Termux is Android-only, so it does not solve iPad.
- Its `TerminalSession` is built around a local subprocess and PTY file
  descriptor; remote CCB streams need a new remote terminal session abstraction.
- Forking the whole app pulls in GPLv3-only app licensing and Termux package
  ecosystem constraints.
- The mature parts are terminal/local-shell infrastructure, not QR pairing,
  CCB project registry, ProjectView, agent switching, or remote relay protocol.
- Using Termux as a generic SSH/tmux client would bypass CCB authority unless
  it talks to a CCB gateway instead of directly mutating tmux.

## Blink Shell

Project: <https://github.com/blinksh/blink>
License: GPLv3

Research checkout:

- path: `/tmp/ccb-mobile-research/blink`
- commit: `a90b442`
- commit date: 2026-04-14
- commit subject: `Created Default style`

Blink is a mature iOS SSH/Mosh terminal. It is useful for iOS terminal UX,
Mosh, keyboard, and reconnect references.

CCB fit: reference only. It is iOS-only, GPLv3, and not CCB/tmux-project
specific.

## ConnectBot

Project: <https://github.com/connectbot/connectbot>
License: Apache-2.0

Research checkout:

- path: `/tmp/ccb-mobile-research/connectbot`
- commit: `58278c5`
- commit date: 2026-06-17
- commit subject: `chore(deps): bump io.nlopez.compose.rules:ktlint from 0.6.0 to 0.6.1`

ConnectBot is a mature Android SSH terminal client. It is useful for Android
SSH and terminal references, but Android-only and not CCB/tmux-project
specific.

## mosh

Project: <https://github.com/mobile-shell/mosh>
License: GPLv3, with an iOS App Store waiver note in the repository.

Research checkout:

- path: `/tmp/ccb-mobile-research/mosh`
- commit: `decd9b7`
- commit date: 2026-03-22
- commit subject: `Addressing last review comments`

mosh is the strongest reference for roaming and intermittent mobile
connectivity. It is not an MVP base because it requires a server-side
`mosh-server`, UDP reachability, and native client integration.

## Other Terminal Sharing Options

### ttyd

Project: <https://github.com/tsl0922/ttyd>
License: MIT

Research checkout:

- path: `/tmp/ccb-mobile-research/ttyd`
- commit: `647d55a`
- commit date: 2026-03-20
- commit subject: `remove dependabot conf`

ttyd exposes a command-line program as a web terminal using xterm.js and
libwebsockets. It can share `tmux attach` quickly, making it a strong demo or
diagnostics tool.

CCB fit: useful for a proof of concept, but it is not CCB-aware and should not
be the default control plane.

### GoTTY

Project: <https://github.com/yudai/gotty>

GoTTY turns CLI tools into web applications and can wrap tmux. It is useful as
prior art for "terminal over web", but it does not solve CCB authority,
multi-project discovery, mobile agent status, or safe input policy.

### WeTTY

Project: <https://github.com/butlerx/wetty>

WeTTY is an HTTP/HTTPS terminal using xterm.js and WebSockets. It is a useful
web-terminal reference, but not a CCB-specific product base by itself.

### tmate

Project: <https://github.com/tmate-io/tmate>

tmate is a tmux fork for instant terminal sharing. It is excellent for
temporary human support sessions, but not ideal as CCB's mobile control plane:
CCB needs project registry, agent state, Comms, safe ask submission, and
`ccbd`-mediated authority.

### xterm.js

Project: <https://github.com/xtermjs/xterm.js/>

xterm.js is the common browser terminal foundation used by several projects in
this space. It supports tmux/curses/mouse-style workloads and is the likely web
terminal rendering layer for a CCB web or hybrid mobile client.

## Practical Source Takeaways

1. A browser/mobile terminal is technically straightforward.
2. For the clarified product, remote tmux control is the main workflow.
3. The hard part for CCB is preserving project, agent, pane, and lifecycle
   authority while still feeling like a normal mobile tmux remote.
4. For native Android/iOS, ServerBox is the strongest direct fork candidate if
   AGPL is acceptable.
5. MuxPod is the strongest tmux-specific UX reference and should shape pane
   navigation, special keys, deep links, polling fallback, and multiline paste.
6. tmux-mobile is the best server-side WebSocket/xterm/tmux gateway reference,
   not the primary native app base.
7. Paseo is the best QR pairing, relay, daemon/client protocol, and agent UX
   reference.
8. CCB-specific ProjectView, Comms, Markdown, and ask controls should enhance
   the remote tmux session rather than replace it.
