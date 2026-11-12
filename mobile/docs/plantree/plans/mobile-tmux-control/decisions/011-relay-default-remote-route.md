# Decision 011: CCB Relay Is The Default Remote Route

Date: 2026-06-19

## Status

Accepted for planning and next implementation shaping.

## Context

Cloudflare named tunnels are useful for self-hosted and advanced setups, but
they require each user to own a domain, configure DNS, run `cloudflared login`,
create a named tunnel, and maintain local tunnel credentials. That is too much
setup for a default CCB Mobile experience.

The product goal is closer to RustDesk/Paseo-style onboarding:

```text
phone app  <->  public CCB relay  <->  user's CCB host
```

The user's CCB host should only need outbound network access. It should not
need a public IP, domain, router port forward, or Cloudflare account.

The user has `seemlab.top`; reserve `relay.seemlab.top` as the first planned
public CCB relay endpoint.

## Decision

CCB Mobile's default not-on-LAN route should be a CCB relay service, not
Cloudflare named tunnels.

Cloudflare named tunnels remain supported as an advanced/self-hosted route
provider. LAN and tailnet routes remain useful local/private options.

The default route order becomes:

1. LAN/manual URL for local development and same-network use.
2. CCB Relay for ordinary remote use and open-box mobile pairing.
3. Tailnet for private-network users.
4. Cloudflare named tunnel for advanced domain/DNS users.
5. Development quick tunnel for smoke/demo only.

## Required Shape

The relay route must preserve the existing `GatewayTransport` boundary:

- `RouteProvider.relay` is route metadata, not a product mode.
- Relay must not own CCB project lifecycle, device identity, terminal tokens,
  ProjectView authority, or tmux state.
- User host and phone both connect outbound to the relay over TLS WebSocket.
- Relay should forward opaque frames and should not see terminal bytes or CCB
  project content in cleartext.
- Pairing, device tokens, terminal tokens, revocation, audit, namespace epoch,
  and target validation remain owned by the user's CCB host.

The first public endpoint can be:

```text
wss://relay.seemlab.top
```

## Local Validation Path

Before a public relay exists, local phone/emulator validation remains possible:

- use the existing Android AVD `ccb_mobile_api35`;
- run the gateway on host loopback, usually `127.0.0.1:8787`;
- use `adb reverse tcp:8787 tcp:8787` so the Android emulator can reach the
  host loopback gateway as `http://127.0.0.1:8787`;
- pair through the current QR/manual gateway flow;
- keep the existing host-side smoke harness as the faster protocol regression
  gate.

This validates the current phone app, QR/manual pairing, secure profile import,
gateway route diagnostics, ProjectView/focus calls, terminal-open, and terminal
WebSocket behavior without requiring a domain or Cloudflare setup.

## Consequences

- The active remote-access plan should be reshaped from Cloudflare-first alpha
  to relay-first remote alpha.
- `seemlab.top` is useful for the project-level relay endpoint, but ordinary
  users should not need their own domain.
- Cloudflare named-tunnel blockers no longer block the product default route;
  they only block the advanced Cloudflare route's live named-tunnel evidence.
- Relay implementation needs a focused spike for framing, E2EE, host/app
  rendezvous, reconnect, abuse controls, and deployment.

## Open Follow-Ups

- Decide whether the first relay implementation is a simple VPS service or a
  Cloudflare Workers/Durable Objects service.
- Define the relay frame envelope and E2EE handshake.
- Decide how hosted relay authentication, quotas, and abuse controls work.
- Add public relay health and diagnostics without exposing CCB host authority.
