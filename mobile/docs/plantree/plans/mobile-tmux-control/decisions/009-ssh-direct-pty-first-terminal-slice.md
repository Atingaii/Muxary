# Decision 009: SSH Direct PTY For First Terminal Slice

Date: 2026-06-18
Status: Accepted for the first real terminal slice
Depends on: [Decision 007](007-native-baseline-before-ccb-gateway.md),
[Decision 008](008-permissive-baseline-until-agpl-approval.md)

## Decision

Use SSH direct PTY as the first real mobile terminal transport after the
isolated harness proved that `project_view` exposes the required project tmux
socket, session, namespace epoch, and selected agent evidence.

The SSH direct slice must execute the socket-aware attach command derived from
`CcbTerminalTarget`:

```text
tmux -S <project_socket> attach-session -t <session>
```

This is a validation and implementation-sequence decision, not the long-term
remote-access product boundary. `GatewayTransport` remains the preferred path
for QR pairing, Cloudflare Tunnel, device scopes, content, notifications,
lifecycle actions, and relay compatibility.

## Evidence

On 2026-06-18, the harness was run against a started disposable CCB project at
`/tmp/ccb-mobile-terminal-run-20260618150322` using installed CCB
`v7.6.11`.

Observed evidence:

- `ccbd` socket: `.ccb/ccbd/ccbd.sock`
- tmux socket: `.ccb/ccbd/tmux.sock`
- namespace epoch: `1`
- tmux session: `ccb-ccb-mobile-terminal-run-20260618150322-e8852d0a`
- selected agent: `mobile_probe`
- selected pane evidence: `%2`
- generated attach command:
  `tmux -S /tmp/ccb-mobile-terminal-run-20260618150322/.ccb/ccbd/tmux.sock attach-session -t ccb-ccb-mobile-terminal-run-20260618150322-e8852d0a`
- cleanup: `ccb kill -f` returned `kill_status: ok`

The durable evidence summary is indexed in
[../history/evidence-index.md](../history/evidence-index.md).

## Rationale

SSH direct PTY is the shortest path to validate native terminal behavior while
the gateway contract remains separate:

- it can reuse permissive Flutter/Dart terminal dependencies already selected
  for Batch 1;
- it does not require CCB source edits before the first interactive terminal
  proof;
- it exercises the same socket/session authority that the future gateway must
  enforce;
- it keeps Cloudflare Tunnel and relay work behind `GatewayTransport` instead
  of leaking route-provider assumptions into UI identity.

## Consequences

- The next implementation package should add an `SshTerminalTransport` or
  equivalent adapter behind the existing terminal transport boundary.
- UI code still consumes `MobileCcbRepository` and `CcbTerminalTarget`, not raw
  SSH or tmux details.
- Default `tmux attach`, arbitrary session browsing, and generic tmux mutation
  remain disallowed in CCB mode.
- SSH credentials, host-key handling, and remote-device safety remain open
  product/security questions before this path can become user-facing outside
  developer validation.
- The gateway path is not deferred indefinitely; it remains required for
  Cloudflare Tunnel, pairing, tokens, content, notifications, lifecycle, and
  relay-compatible routing.

## Validation Path

This decision is validated when:

1. a fake or local SSH profile can open an `xterm` session through the terminal
   transport boundary;
2. the launched command is built only from `CcbTerminalTarget` socket/session
   evidence;
3. paste, resize, background/resume, reconnect, and close are covered by
   focused tests or emulator/device smoke evidence;
4. closing the mobile terminal does not stop `ccbd`, provider panes, or the
   project tmux session;
5. the plan tree records the next gateway contract checkpoint before remote
   Cloudflare work starts.
