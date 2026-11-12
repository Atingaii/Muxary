# Decision 006: Cloudflare Tunnel Before Custom Relay

Date: 2026-06-18
Status: Superseded by
[Decision 011](011-relay-default-remote-route.md) for default route ordering

## Supersession Note

This decision's route boundary remains useful, and the Cloudflare named-tunnel
work remains an advanced route provider. Its "Cloudflare before relay" priority
is superseded because ordinary CCB Mobile users should not need to own a
domain, configure DNS, or manage Cloudflare credentials.

## Decision

The mobile remote-access roadmap should use Cloudflare Tunnel as the first
out-of-LAN route and defer a self-hosted/open relay until the CCB mobile API,
gateway, terminal token, reconnect, and device-scope model are stable.

Cloudflare Tunnel must be treated as a route provider, not as the product
protocol. The app should still talk to `GatewayTransport`; the gateway should
still expose the same CCB-shaped HTTP/WebSocket API; CCB should still own
project, agent, lifecycle, content, and terminal authority.

## Rationale

- Cloudflare Tunnel solves the immediate "phone is not on the same LAN"
  problem without requiring a public server IP or router port forwarding.
- It lets the first public remote mode stay scan-first: configure tunnel on
  the server, print QR, scan on phone, connect.
- It avoids building a custom relay before the terminal stream, pairing,
  ProjectView, notifications, Markdown, and lifecycle behaviors are proven.
- A route-provider boundary keeps future relay migration contained to the
  connection layer.

## Required Boundary

The app architecture must keep these layers separate:

```text
Flutter UI
  -> MobileCcbRepository
  -> GatewayTransport
  -> RouteProvider: lan | tailnet | cloudflare_tunnel | relay
  -> ccb mobile gateway
  -> ccbd + project tmux socket
```

`RouteProvider` may change URL discovery, WebSocket establishment, heartbeat,
and diagnostics. It must not change:

- project list schema;
- ProjectView schema;
- focus/lifecycle/content endpoints;
- terminal token semantics;
- terminal frame format;
- device scopes;
- stale namespace checks;
- tmux socket binding rules.

## Cloudflare First Shape

Server:

```bash
ccb mobile serve --listen 127.0.0.1:8787
cloudflared tunnel run ccb-mobile
```

QR payload:

```json
{
  "scheme": "ccb-mobile",
  "transport": "gateway",
  "route_provider": "cloudflare_tunnel",
  "gateway_url": "https://ccb-mobile.example.com",
  "host_id": "host_...",
  "pairing_token": "short-lived",
  "server_fingerprint": "sha256:...",
  "capabilities": ["http_json", "websocket_terminal", "event_cursor"]
}
```

The phone pairs with CCB's gateway token. Cloudflare Access can be an optional
outer protection layer, but it must not replace CCB device identity, scopes,
revocation, or terminal tokens.

## Relay-Later Shape

Future relay should use the same app/gateway protocol:

```text
server gateway --outbound encrypted session--> relay
phone app      --outbound encrypted session--> relay
relay forwards frames, but does not own CCB actions
```

The relay may help with NAT, reconnect, and multi-device routing. It must not
become the authority for CCB projects, tmux targets, or lifecycle operations.

## Consequences

- `GatewayTransport` becomes the primary product transport earlier than
  SSH-direct mode for real remote use.
- `SshTransport` remains useful for developer fallback and isolated terminal
  validation, but it is not the main not-on-LAN story.
- `ccb mobile serve` needs route-agnostic pairing, terminal frames, event
  cursors, diagnostics, and revocation from the start.
- Relay design can be researched after the MVP without forcing a mobile app
  rewrite.

## Validation

This decision is validated when:

- the same mobile app profile can connect through localhost/LAN and Cloudflare
  Tunnel without UI changes;
- terminal reconnect works after app backgrounding and transient network loss;
- revoking a CCB device token blocks project list and terminal opening even if
  the Cloudflare URL is still reachable;
- terminal frame and event schemas do not include Cloudflare-specific fields;
- a relay spike can reuse the same API and frame contracts.
