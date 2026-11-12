# Decision 007: Native Baseline Before CCB Gateway

Date: 2026-06-18
Status: Accepted
Depends on: [Decision 005](005-native-flutter-tmux-first-client.md),
[Decision 006](006-cloudflare-tunnel-before-custom-relay.md)

## Decision

Start implementation with the native Flutter app baseline, fake CCB transport,
CCB-shaped data model, socket-aware tmux command layer, and one terminal
vertical-slice harness before implementing `ccb mobile serve`.

The first real terminal validation may use manually configured project facts
from an isolated CCB test project:

- project id;
- namespace epoch;
- CCB tmux socket path;
- CCB tmux session name;
- selected window or agent target.

This is an implementation sequence decision, not a product transport change.
`GatewayTransport` remains the preferred product path for pairing,
Cloudflare Tunnel, device scopes, content, notifications, and relay
compatibility.

The first transport choice after this harness evidence is recorded separately
in [Decision 009](009-ssh-direct-pty-first-terminal-slice.md).

## Rationale

CCB source already provides the authority anchors needed by the mobile model:

- `project_view` returns project, namespace, window, agent, and Comms state;
- `project_focus_agent` and `project_focus_window` validate namespace epoch;
- tmux socket path and session name are project-owned facts;
- pane ids are already treated as evidence rather than durable identity.

The missing and riskiest mobile-side work is native terminal fit, mobile data
shape, socket-aware command generation, background/resume behavior, and
license-safe app setup. Those can be validated without adding a gateway first.

## Consequences

- Batch 1 can proceed without CCB source edits.
- The mobile app must still define `GatewayTransport` and `SshTransport`
  boundaries so SSH/direct validation does not leak into UI assumptions.
- Manual project facts are allowed only for fixtures and isolated validation.
- No generic tmux session picker should appear in CCB mode.
- `ccb mobile serve`, QR pairing, Cloudflare Tunnel, content endpoints,
  notifications, and lifecycle controls move to later packages.

## Validation Path

This decision is validated when:

1. the Flutter app starts on Android emulator with fake CCB project/agent data;
2. model tests reject terminal input targets based on `pane_id` alone;
3. tmux command tests prove `tmux -S <project_socket> attach-session -t
   <session>` is generated for CCB project terminals;
4. default `tmux attach` cannot be generated for a CCB project;
5. a terminal harness can open an isolated CCB project tmux session without
   stopping `ccbd`, provider panes, or the project tmux session when the app
   view closes.

The isolated started-project harness evidence was captured on 2026-06-18 and
indexed in [../history/evidence-index.md](../history/evidence-index.md).
