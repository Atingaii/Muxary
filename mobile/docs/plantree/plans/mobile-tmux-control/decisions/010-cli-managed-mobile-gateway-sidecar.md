# Decision 010: CLI-Managed Mobile Gateway Sidecar First

Date: 2026-06-18
Status: Accepted for the first `ccb mobile serve` package
Depends on: [Decision 006](006-cloudflare-tunnel-before-custom-relay.md),
[Decision 007](007-native-baseline-before-ccb-gateway.md),
[Decision 009](009-ssh-direct-pty-first-terminal-slice.md)

Route priority note: [Decision 011](011-relay-default-remote-route.md)
supersedes Decision 006's Cloudflare-first ordering. This decision still owns
the first `ccb mobile serve` sidecar boundary.

## Decision

Implement the first `ccb mobile serve` package as a CLI-managed gateway
sidecar process for the current CCB project.

The gateway must run outside `ccbd`, bind loopback by default, talk to the
project ccbd over its existing Unix socket through `CcbdClient`, and preserve
`ccbd` as the authority for project state, namespace epoch, focus, Comms,
lifecycle, and tmux socket/session facts.

Do not mount the HTTP/WebSocket server inside `ccbd` for the first package.
Do not make `ccbd` supervise the mobile gateway in the first package.

## Rationale

- The mobile gateway owns route-provider HTTP/WebSocket concerns, pairing
  envelopes, device tokens, terminal stream clients, and remote diagnostics.
- `ccbd` already owns project reconciliation, dispatcher state, provider
  runtime records, namespace lifecycle, and the project tmux session.
- A separate gateway can fail, restart, or be exposed through Cloudflare
  Tunnel without stopping server-side CCB.
- Current CCB source already has the ccbd RPC surface needed for the first
  read-only gateway slice: `ping`, `project_view`, `project_focus_agent`, and
  `project_focus_window`.
- The app-side `GatewayTransport` and `RouteProvider` boundary already keeps
  Cloudflare/LAN/relay routing out of CCB project identity and terminal frame
  semantics.

## Required Boundary

First package:

```text
Flutter app
  -> GatewayTransport
  -> RouteProvider: lan | tailnet | cloudflare_tunnel | relay
  -> ccb mobile serve process
  -> CcbdClient over project ccbd Unix socket
  -> ccbd project authority
  -> project tmux socket/session
```

The gateway may internally read namespace socket/session facts from
`project_view` or `ping('ccbd')`, but the remote app must not receive tmux
socket paths or session names.

## Storage Boundary

First mobile-specific state belongs under:

```text
PathLayout(project_root).ccbd_dir / "mobile"
```

The gateway owns mobile device records, pairing-token hashes, terminal-token
hashes, and mobile audit events there. `ccbd` runtime records remain reserved
for project and agent authority.

## Consequences

- The first CCB source package can start with loopback-only health, current
  project list, and ProjectView endpoints.
- The first sidecar stays route-agnostic. Decision 011 now makes CCB Relay the
  default not-on-LAN route and keeps Cloudflare Tunnel as an advanced route.
- QR pairing, persistent device auth, terminal WebSocket streaming, content,
  notifications, lifecycle, and multi-project registry work become later
  packages rather than prerequisites for G1.
- A future decision may move supervision into `ccbd` or add a host-level
  registry after the sidecar contract proves stable.

## Validation Path

This decision is validated when:

1. `ccb mobile serve` is routed through the normal phase2 CLI parser and
   dispatch path;
2. the default listener is loopback;
3. current-project health/list/view responses are backed by `CcbdClient`;
4. route-provider fields remain absent from project ids, terminal ids,
   ProjectView payloads, and terminal frame schemas;
5. stopping the gateway does not stop `ccbd`, provider panes, or the project
   tmux session;
6. the plan tree links the source ready-check and names the first source files
   to inspect/change before production edits begin.
