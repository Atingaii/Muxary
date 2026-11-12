# Native Flutter Base Source Analysis

Date: 2026-06-18
Status: Draft

## Purpose

Record the local source review behind the updated native Flutter
agent-first server-remote direction. The target product is still a phone/iPad
remote for server-side CCB projects and panes, not an independent mobile agent
runtime.

## Local Research Checkouts

All research checkouts are shallow clones under `/tmp/ccb-mobile-research`.

| Project | Local Path | Commit | License | Role |
| :--- | :--- | :--- | :--- | :--- |
| Paseo | `/tmp/ccb-mobile-research/paseo` | `127b138` / 2026-06-17 | AGPL-3.0 | Pairing, daemon/client protocol, relay, terminal frames, agent UX reference. |
| ServerBox | `/tmp/ccb-mobile-research/serverbox` | `d845a6b` / 2026-06-18 | AGPL-3.0 | Preferred native Flutter fork candidate if AGPL is acceptable. |
| MuxPod | `/tmp/ccb-mobile-research/mux-pod` | `d3b400d` / 2026-05-21 | Apache-2.0 | Best tmux-specific mobile UX and command reference. |
| tmux-mobile | `/tmp/ccb-mobile-research/tmux-mobile` | `493c404` / 2026-02-19 | MIT | Server WebSocket/xterm/tmux gateway reference. |
| Termux App | `/tmp/ccb-mobile-research/termux-app` | `401bbe5` / 2026-06-05 | GPLv3-only app | Android terminal reference only. |
| Blink Shell | `/tmp/ccb-mobile-research/blink` | `a90b442` / 2026-04-14 | GPLv3 | iOS SSH/Mosh terminal reference only. |
| ConnectBot | `/tmp/ccb-mobile-research/connectbot` | `58278c5` / 2026-06-17 | Apache-2.0 | Android SSH terminal reference only. |
| mosh | `/tmp/ccb-mobile-research/mosh` | `decd9b7` / 2026-03-22 | GPLv3, with iOS App Store waiver note | Reconnect/roaming reference only. |
| ttyd | `/tmp/ccb-mobile-research/ttyd` | `647d55a` / 2026-03-20 | MIT | Minimal web terminal server reference. |

## ServerBox

ServerBox is the strongest practical native base for a CCB mobile client if an
AGPL app component is acceptable.

Source anchors:

- `pubspec.yaml` uses Flutter, `dartssh2`, bundled/path `xterm`, `wakelock`,
  native notification/home-widget related packages, and platform folders for
  iOS, Android, macOS, Linux, and Windows.
- `lib/view/page/ssh/page/page.dart` owns the terminal page, xterm view,
  virtual keys, paste, focus, wake lock, and mobile layout behavior.
- `lib/view/page/ssh/page/init.dart` opens SSH foreground sessions with PTY,
  runs tmux attach commands via `SSHClient.execute(..., pty: ...)`, and has
  keep-alive/disconnect handling.
- `lib/data/ssh/tmux/tmux_command_builder.dart` builds attach/list/window
  switch commands, but currently targets the default tmux server only.
- `lib/view/widget/tmux_session_selector.dart` has a generic session/window
  picker plus destructive new/kill-window actions that must be removed or
  hidden for CCB.
- `lib/data/ssh/session_manager.dart` tracks active terminal sessions and
  updates Android foreground notifications and iOS Live Activity hooks.

Useful parts:

- mature Flutter app shell and platform packaging;
- real SSH PTY terminal, not only pane capture polling;
- tab/session restore and reconnect behavior;
- special-key and virtual-key controls;
- Android foreground service and iOS Live Activity patterns;
- existing tmux attach/list/switch command builder tests.

Required CCB changes to the fork:

- replace SSH host/server dashboard with CCB host/project home;
- add QR pairing and a CCB host profile;
- add socket-aware tmux command building: `tmux -S <project_socket>`;
- route project/window/agent status through CCB authority;
- remove or gate generic tmux new/kill/split/rename operations;
- add a ProjectView side panel and Markdown/math reading surface;
- separate raw terminal input scope from lifecycle/admin scope.

Main risks:

- AGPL licensing affects the mobile app component if code is reused directly;
- the existing product is broad server management, so UI simplification is a
  real code cleanup task;
- current tmux commands do not know CCB project sockets or namespace epochs;
- the terminal is SSH/PTY-first, while a future CCB gateway transport may use
  WebSocket frames.

## MuxPod

MuxPod is the strongest tmux-specific UX reference. It should not be ignored
even if ServerBox is the fork base.

Source anchors:

- `lib/services/tmux/tmux_commands.dart` builds detailed session/window/pane
  commands, `capture-pane`, `send-keys`, `load-buffer`, and `paste-buffer`.
- `lib/screens/terminal/terminal_screen.dart` implements pane polling,
  adaptive refresh, copy-mode detection, input queueing, reconnect hooks,
  special keys, pane navigation, and multiline paste.
- `lib/providers/ssh_provider.dart` implements network-aware reconnect with
  backoff and cached connection options.
- `lib/services/deep_link/deep_link_service.dart` parses deep links into
  server/session/window/pane targets.
- `lib/widgets/special_keys_bar.dart`, `lib/widgets/tmux_tiles.dart`, and
  `lib/widgets/session_tree.dart` are useful mobile tmux interaction patterns.

Useful parts:

- CCB-like project/agent fast switching can reuse the breadcrumb/pane-selector
  mental model;
- `load-buffer` + `paste-buffer -p` is the right direction for multiline CCB
  paste;
- adaptive `capture-pane` polling is useful as a low-risk mobile fallback mode;
- deep links map naturally to completion notifications.

Required CCB changes:

- add socket prefix support to every tmux command;
- change identity from `server/session/window/pane` to
  `host/project/window/agent/current pane evidence`;
- remove generic destructive pane/session operations from normal CCB mode;
- add ProjectView/ccbd side channel because tmux flags are not enough for CCB
  completion, callback, Comms, queue, or provider health.

Main risks:

- the README presents Android as the supported target, even though Flutter iOS
  project files exist;
- its terminal mode is mostly command/capture based rather than true
  `tmux attach`, which is mobile-friendly but less faithful for full-screen TUI
  workloads;
- no existing CCB/gateway/pairing model.

## Paseo

Paseo is the strongest product/protocol reference, not the best tmux-specific
fork base.

Source anchors:

- `README.md` maps the monorepo: `packages/server`, `packages/app`,
  `packages/cli`, `packages/desktop`, `packages/relay`.
- `docs/architecture.md` documents daemon/client/relay structure, WebSocket
  protocol, terminal binary frames, reconnect, and compatibility rules.
- `packages/protocol/src/binary-frames/terminal.ts` defines a compact terminal
  stream frame with opcodes for output, input, resize, snapshot, and restore.
- `packages/server/src/server/pairing-offer.ts` generates relay QR offers with
  server id, daemon public key, relay endpoint, and QR rendering.
- `packages/server/src/terminal/terminal.ts` and
  `terminal-manager.ts` manage local node-pty terminal sessions.

Useful parts:

- QR pairing flow and connection offer shape;
- stable host identity and daemon public key model;
- relay/E2EE concepts;
- terminal binary stream and snapshot/restore concepts;
- mobile/desktop/web client sharing one protocol;
- agent timeline and notification patterns.

Required CCB changes if used directly:

- replace Paseo's agent daemon model with CCB ProjectView and ccbd RPC;
- replace local node-pty terminal creation with CCB project tmux attach or
  control-mode binding;
- replace workspace model with CCB project/agent model.

Main risks:

- AGPL code reuse is a deliberate distribution decision;
- the product model overlaps CCB but does not align with CCB's existing tmux
  authority boundaries;
- not tmux-specific.

## tmux-mobile

tmux-mobile remains a useful MIT server-side reference.

Source anchors:

- `src/backend/tmux/cli-executor.ts` already passes `-S` or `-L` for tmux CLI
  list/mutation commands.
- `src/backend/pty/node-pty-adapter.ts` currently runs `tmux attach-session`
  without the socket prefix, which is the key bug/patch if it is adapted to
  CCB project sockets.
- `src/backend/server.ts` creates per-client grouped sessions and streams PTY
  bytes over `/ws/control` and `/ws/terminal`.
- tests include fake tmux, fake PTY, integration, e2e, and real tmux smoke.

Useful parts:

- minimal WebSocket terminal gateway;
- xterm.js terminal attach path;
- fake tmux/fake PTY test style;
- per-client grouped session idea for focus isolation.

Main risks:

- it is web-first, not native-first;
- generic tmux session/window/pane operations do not match CCB authority;
- grouped sessions need explicit CCB ownership before they can be a durable
  product behavior.

## Non-Bases

Termux is mature but Android-only and built around local subprocess PTYs. It is
useful for Android terminal UX, foreground service, and extra-key ideas, not as
the shared iOS/Android base.

Blink is a strong iOS SSH/Mosh reference, but iOS-only and GPLv3.

ConnectBot is a strong Android SSH reference, Apache-2.0, but Android-only and
not tmux/CCB-specific.

mosh is the best reconnect/roaming design reference, but using it directly
adds client/server binary and UDP deployment requirements. It is a later
transport hardening option, not an MVP requirement.

ttyd is a small MIT web terminal server and useful for diagnostics or a
fallback gateway recipe. It is not CCB-aware and not a native app base.

## Recommendation

Do not build the terminal, SSH reconnect, special-key UI, and native packaging
from scratch.

Recommended base sequence:

1. Create a dedicated `ccb-mobile` Flutter repository.
2. Start from ServerBox if AGPL is acceptable for the mobile app component.
3. Port or reimplement MuxPod's tmux-specific command/pane UX where ServerBox
   is too generic.
4. Keep tmux-mobile and ttyd as server-side terminal gateway references.
5. Keep Paseo as the pairing/relay/protocol reference.

If CCB mobile must remain permissive-license at the app level, use a smaller
new Flutter app and selectively reimplement MuxPod-style ideas under Apache/MIT
compatible dependencies instead of forking ServerBox or Paseo.
