# Architecture And Reuse Plan

Date: 2026-06-18
Status: Execution design

## Purpose

This is the architecture and open-source reuse gate for CCB Mobile
implementation. It turns the broader native Flutter blueprint into the design
that must be satisfied before large-scale app coding.

The goal is not to write a new mobile terminal app from scratch. The goal is
to adapt proven open-source mobile terminal, tmux, pairing, gateway, Markdown,
and notification patterns into a CCB-scoped native app.

## Architecture Rules

- The phone/iPad is a controller for CCB already running on a server.
- The UI model is host -> project -> window/agent -> terminal/content, not
  server -> arbitrary tmux session -> pane.
- UI code depends on `MobileCcbRepository`, not directly on SSH, WebSocket,
  `tmux`, or CCB socket details.
- `GatewayTransport` and `SshTransport` are implementation details behind the
  repository boundary.
- `RouteProvider` is a sub-layer of `GatewayTransport`: LAN, tailnet, CCB
  Relay, and Cloudflare Tunnel must keep the same app-facing CCB schemas.
- `pane_id` is diagnostic evidence only. Terminal input targets must include
  stable project identity, namespace epoch, and target kind.
- Destructive tmux/session actions are absent from normal CCB mode unless a
  later CCB-owned admin endpoint explicitly permits them.

## App Module Map

Expected first layout under `app/lib/`:

```text
core/
  result/error models, clocks, ids, logging
models/
  ccb_host.dart
  ccb_project.dart
  ccb_window.dart
  ccb_agent.dart
  ccb_terminal_target.dart
  ccb_content_item.dart
  ccb_notification.dart
  ccb_scope.dart
repository/
  mobile_ccb_repository.dart
  fake_mobile_ccb_repository.dart
transport/
  gateway_transport.dart
  ssh_transport.dart
  route_provider.dart
  terminal_transport.dart
tmux/
  tmux_command_builder.dart
  tmux_paste_strategy.dart
features/
  host_pairing/
  project_home/
  project_detail/
  terminal/
  content_reader/
  notifications/
  lifecycle/
fixtures/
  project_view_fixture.dart
```

Initial implementation may use fewer files, but it must preserve these
ownership boundaries. Screens can change without rewriting transport code.

## CCB Data Model

Minimum app model:

- `CcbHost`: local host id, display name, transport mode, route provider,
  base URL or SSH profile reference, capabilities, health.
- `CcbProject`: project id, display name, root for diagnostics, favorite
  state, lifecycle, health, last activity summary.
- `CcbWindow`: window name, label, kind, order, active state, agent names,
  tmux window evidence.
- `CcbAgent`: agent name, provider, window, order, active state, queue depth,
  callback/completion state, runtime health, pane evidence.
- `CcbTerminalTarget`: project id, namespace epoch, tmux socket path/session
  evidence for direct mode, target kind, window/agent, current pane evidence,
  input scope.
- `CcbContentItem`: project id, content id, kind, preview, format,
  render hints, source safety.
- `CcbNotification`: host id, project id, event id, kind, severity, target
  deep link, acknowledgement state.
- `CcbScope`: `view`, `content`, `focus`, `terminal_input`, `notify`, `ask`,
  `lifecycle`, `admin`.

Mapping source for Batch 1 is fake fixture data shaped like real
`project_view`:

- `view.project`
- `view.ccbd`
- `view.namespace`
- `view.windows`
- `view.agents`
- `view.comms`

## Transport Boundary

`MobileCcbRepository` should expose:

```text
listProjects()
getProjectView(projectId)
focusAgent(projectId, agent, namespaceEpoch)
focusWindow(projectId, window, namespaceEpoch)
openTerminal(projectId, target, size)
getContent(projectId, contentId)
subscribeEvents(cursor)
requestLifecycle(projectId, action)
```

Batch 1 uses a fake repository for UI/model work and a command-builder-only
terminal harness. Live network calls wait until the fake model and tmux command
tests pass.

Transport implementations:

- `GatewayTransport`: default for QR pairing, CCB Relay, Cloudflare Tunnel,
  terminal tokens, content, and notifications.
- `SshTransport`: developer/fallback path for first vertical slice if the base
  app reuses ServerBox-style SSH PTY code.
- `RouteProvider`: `lan`, `tailnet`, `cloudflare_tunnel`, `relay`; route
  fields never appear in project ids, terminal ids, ProjectView payloads, or
  terminal frame semantics.
- `TerminalTransport`: terminal bytes/input/resize/reconnect abstraction
  independent of whether the backend is SSH PTY, gateway WebSocket, capture
  polling, or later tmux control mode.

## Open-Source Reuse Plan

| Source | License | Reuse posture | Planned use | Required CCB adaptation |
| :--- | :--- | :--- | :--- | :--- |
| ServerBox | AGPL-3.0 | Fork only if AGPL is accepted. Otherwise use as reference only. | Flutter shell, SSH PTY terminal, xterm view, secure storage, reconnect, notifications, iOS/Android packaging. | Replace server dashboard with CCB project home; add socket-aware tmux commands; remove/gate generic tmux mutations; add ProjectView/content layers. |
| MuxPod | Apache-2.0 | Reuse ideas/code where compatible after source inspection. | Tmux command strategy, special key bar, paste-buffer pattern, capture fallback, pane navigation UX. | Add `-S <project_socket>` everywhere; change identity to host/project/window/agent; remove generic destructive actions. |
| tmux-mobile | MIT | Reuse server/gateway patterns and tests, not native app base. | WebSocket terminal gateway, fake tmux/PTY tests, socket-aware CLI executor, grouped-session research. | Bind gateway PTY attach to CCB project socket/session; validate project id, namespace epoch, target, and scopes first. |
| Paseo | AGPL-3.0 | Protocol/pairing reference unless AGPL reuse is accepted. | QR pairing, daemon/client protocol, relay, terminal frames, reconnect concepts. | Replace daemon/workspace model with CCB `ccbd`, ProjectView, and tmux socket authority. |
| ConnectBot | Apache-2.0 | Android SSH reference only. | SSH UX and host-key handling ideas if needed. | Android-only; not CCB/tmux aware. |
| ttyd | MIT | Gateway diagnostic/reference only. | Minimal terminal server concepts. | Must wrap CCB identity/scopes; not a product UI. |
| mosh | GPLv3 plus waiver notes | Later transport-hardening reference only. | Roaming/reconnect concepts. | Adds server/client binaries and UDP; not MVP. |

Reuse gates before importing code:

1. Record license and attribution requirements in the plan tree or app docs.
2. Confirm platform fit for Android and iOS/iPadOS.
3. Identify exact source files/modules to import or fork.
4. Decide whether code is copied, vendored, forked, or only reimplemented as
   a pattern.
5. Add tests around each adapted boundary before wiring it to live CCB state.

## Batch 1 Implementation Shape

Batch 1 is architecture-first and fake-transport-first:

1. Select app base after license decision.
2. Keep the Batch 1 source scaffold under `app/`; generate platform folders
   after Flutter/Android tooling is available.
3. Add CCB models and fake ProjectView fixture mapper.
4. Add `MobileCcbRepository` plus fake implementation.
5. Add `TmuxCommandBuilder` with socket-aware attach/capture/paste commands.
6. Add tests proving:
   - `pane_id` alone cannot authorize terminal input;
   - default `tmux attach` cannot be generated for a CCB project;
   - multiline paste uses a socket-bound tmux buffer strategy;
   - route provider metadata stays outside project and terminal identity.

## Test Strategy

Required before live CCB terminal work:

- model tests for project, agent, window, terminal target, content, scopes;
- fixture mapping tests from realistic `project_view` JSON;
- tmux command tests for socket path, session name, attach, capture, paste,
  focus target evidence, and quoting;
- fake repository UI smoke test where feasible;
- Android emulator smoke test after toolchain setup.

Required for the first real terminal slice:

- isolated CCB test project outside `/home/bfly/yunwei/ccb_source` and outside
  this project's active runtime;
- attach to the exact project tmux socket/session;
- type, paste, resize, background/resume, reconnect, and close;
- verify `ccbd`, provider panes, and project tmux session remain alive.

## Commit And Plan-Tree Cadence

- Update `implementation-status.md` after every coherent work batch.
- Add or update a decision when architecture, license, base-app, or transport
  choices become stable.
- Commit plan-only work separately when it forms a usable checkpoint.
- Commit implementation work with the matching plan-tree evidence whenever a
  coherent package or passing test set lands.
- Never include `.ccb/agents`, `.ccb/ccbd`, logs, build output, tokens,
  private keys, or Android `local.properties` in commits.

## Current Readiness

Ready now:

- architecture and reuse design;
- fake CCB model design;
- tmux command-builder specification;
- permissive Batch 1 `app/` source scaffold for review;
- generated Android/iOS platform folders;
- Android debug APK build from the CCB fake-project scaffold;
- fake project agent tap opens a read-only `xterm` terminal screen backed by
  a `CcbTerminalTarget` and socket-aware attach command;
- isolated terminal validation harness script for reading `project_view` and
  printing socket-aware tmux attach evidence from a running isolated project.
- started-project harness evidence proving `project_view` provides the
  namespace epoch, tmux socket/session, and selected agent evidence needed for
  a mobile terminal target.
- `TerminalTransport` and `SshTerminalTransport` implementation that reuses
  `dartssh2`, opens only the socket-aware attach command generated from
  `CcbTerminalTarget`, and forwards paste, resize, reconnect, and output
  through an injectable live terminal session.
- developer SSH profile entry point that keeps credentials in memory, injects
  live transport for validation, and leaves the default fake terminal path
  intact.
- repeatable SSH direct PTY live smoke using temporary localhost sshd and a
  disposable CCB project.
- Android API 35 emulator `flutter run` smoke.
- route-agnostic gateway contract checkpoint.
- app-side `GatewayTransport` and `RouteProvider` interfaces with fake gateway
  contract tests.

Current next implementation package:

- record the CCB source ready-check for `ccb mobile serve`, including runtime
  ownership, paired-device storage, endpoint reuse, terminal PTY ownership,
  project registry, source files, and verification gates;
- keep `GatewayTransport` as the required product route for pairing,
  Cloudflare Tunnel, terminal tokens, content, notifications, lifecycle, and
  relay-compatible routing.

Blocked before emulator/device smoke and live terminal validation:

- no Android system image/AVD or attached Android device has been selected for
  a real `flutter run` smoke test;
- app license posture is not final, so direct AGPL source import remains
  disallowed.

Not blocked:

- plan-tree design updates;
- model and command-layer implementation around fake fixtures;
- permissive minimal Flutter baseline work while AGPL remains undecided;
- running the isolated CCB terminal harness against a started test project
  before live networking.
