# Relay Route Provider Spike

Date: 2026-06-21
Status: In Progress

## Purpose

Define the first CCB Relay route-provider slice that can be implemented and
verified with only local tests, Android Emulator, fake transports, and
source-backed loopback harnesses.

This spike does not deploy `relay.seemlab.top` and does not require public
network reachability. It prepares the app/source contract so a later relay
adapter can be added without changing the CCB project, agent, terminal,
content, notification, or lifecycle models.

## Design Position

Relay remains a route provider:

```text
mobile app
  -> GatewayTransport
  -> RouteProvider.relay
  -> relay adapter
  -> ccb mobile gateway
  -> ccbd + project tmux socket
```

It is not a new product mode. The app must not branch CCB project behavior on
`relay`; only the connection adapter, pairing metadata, and route diagnostics
may care about the provider.

## Reuse Check

Reuse existing local code before adding relay-specific machinery:

- `RouteProviderKind.relay` already exists in the app route model.
- `GatewayTransport` already owns route-agnostic operations for health,
  projects, ProjectView, focus, readable history, lifecycle, terminal open, and
  terminal frames.
- `GatewayPairingPayload` and `GatewayPairedHost` already preserve
  `gateway_url`, optional `websocket_url`, capabilities, diagnostics, scopes,
  server fingerprint, and secure profile storage.
- `GatewayRouteDiagnostics` already validates route metadata, device auth,
  provider scope, gateway health, project reachability, and ProjectView
  redaction.
- Source `ccb mobile serve --route-provider relay` is already accepted as
  pairing metadata, but source does not yet implement an outbound relay
  adapter.

Do not hand-roll terminal, WebSocket, pairing, reconnect, lifecycle, Markdown,
or storage behavior for relay. The first relay code should adapt the existing
transport and pairing contracts.

## Current Local Contract

Until a production relay adapter exists, local fake tests define the metadata
contract:

- `route_provider`: `relay`
- `gateway_url`: HTTPS origin used as the relay control origin, for example
  `https://relay.seemlab.top`
- `websocket_url`: WSS origin used for the relay socket, for example
  `wss://relay.seemlab.top`
- `server_fingerprint`: host authority fingerprint, still owned by the CCB
  host, not by the relay
- `capabilities`: includes normal gateway capabilities plus relay-specific
  adapter hints such as `relay_tunnel`
- `diagnostics`: may include non-secret relay placement/rendezvous hints such
  as region and host id

The relay URL checks are intentionally stricter than LAN checks:

- `gateway_url` must be HTTPS origin-only;
- `websocket_url` must be WSS origin-only;
- `/v1/devices/me` route metadata must report the same relay origin as the
  stored profile;
- route-provider metadata must not appear in ProjectView identity, terminal
  ids, terminal-open payloads, lifecycle payloads, or WebSocket frames.
- app `RelayGatewayTransport` local tests may wrap an existing relay-profile
  `GatewayTransport`, but the recorded envelope JSON must expose only envelope
  metadata and opaque payload fields, never CCB project ids, agent/window
  names, terminal ids/tokens, paste text, route-provider metadata, or relay
  URLs.

## Landed Local Adapter Slice

App commit `f8c5a25` adds the first fake/local relay adapter contract:

- `RelayGatewayTransport` requires `RouteProviderKind.relay` and rejects LAN
  profiles;
- all existing `GatewayTransport` operations are delegated without changing
  project, focus, lifecycle, readable-history, terminal-open, terminal-frame,
  or input semantics;
- `RelayGatewayEnvelope` validates sequence numbers and base64 opaque fields;
- local tests assert operation ordering, sequence increments, and plaintext
  avoidance in the envelope JSON surface;
- this remains a contract test double and does not implement production
  encryption, relay rendezvous, host outbound connections, or public relay
  deployment.

## Landed App Protocol Slice

App commit `3bd2ca1` adds the first app-side relay protocol contract:

- `RelayFrame` models `client_hello`, `host_hello`, `gateway_envelope`, `ack`,
  and `close` frame kinds;
- `RelayHandshakeTranscript` validates session id, host id, accepted protocol
  version, and public key material agreement before marking a relay session
  ready;
- `RelayFrame.gatewayEnvelope` wraps `RelayGatewayEnvelope` as opaque relay
  payload instead of exposing project, terminal, route, or token metadata;
- `RelayHostRegistration` defines the host-outbound registration shape with
  host id, server fingerprint, public key, capabilities, and non-secret
  diagnostics;
- local tests reject cleartext gateway URLs, route-provider metadata, pairing
  codes, device tokens, terminal tokens, project ids, terminal ids, and paste
  text in relay cleartext payloads.

## Landed Source Local Harness Slice

Source commit `1b438505` adds the first source-side local relay harness:

- `mobile_gateway.relay` mirrors the app-defined relay registration, frame,
  handshake, and opaque gateway-envelope validation shape;
- `MobileGatewayRelayOutboundClient` registers a host into a
  `LocalRelayServerHarness` without opening a public listener;
- the local harness negotiates `client_hello`/`host_hello`, records an
  established session, forwards only opaque gateway envelopes from phone to
  host, and returns ack frames;
- disconnected and unknown host states are exposed through local diagnostics
  without stopping CCB runtime;
- `ccb mobile serve --route-provider relay` now includes a local
  `relay_outbound` summary for registered fake relay host state while keeping
  the gateway listener loopback-bound.

## Landed Relay Health Diagnostics Slice

Source commit `1112559d` and app commit `c10e4f1` add local relay health
diagnostics without public networking:

- source `LocalRelayServerHarness` reports unknown host, disconnected host,
  relay unreachable, stale device, and host-fingerprint mismatch states;
- `MobileGatewayRelayOutboundClient.diagnostics()` can pass local device and
  expected fingerprint context into the harness;
- app `GatewayRouteDiagnostics` accepts source-compatible `state` or
  `relay_state` metadata and maps blocking relay states into user-visible
  route-check failures;
- app route diagnostics compares source-compatible observed relay host
  fingerprint metadata against the stored profile fingerprint;
- these checks stay in the route/provider layer and do not add relay metadata
  to ProjectView, terminal handles, lifecycle requests, or relay envelopes.

## Future Relay Adapter Shape

The production adapter still needs a separate source/app package:

1. Relay server accepts outbound TLS WebSocket connections from CCB hosts and
   phones.
2. CCB host registers a relay host id and opens an outbound tunnel to the
   relay.
3. Phone pairs through an existing CCB-authorized claim path and stores a relay
   host profile.
4. Phone and host establish an end-to-end encrypted session; relay forwards
   opaque frames only.
5. The app presents the same `GatewayTransport` API as LAN/Cloudflare.
6. Relay disconnects affect route health only; they must not stop CCB runtime,
   revoke devices, mint terminal tokens, or control lifecycle actions.

## Emulator-Only Acceptance For This Spike

This spike is accepted only by local evidence:

- app route diagnostics accept a fake relay profile with HTTPS/WSS origins;
- app route diagnostics reject unsafe relay path/query/fragment/credential or
  non-WSS metadata;
- app route diagnostics explain unknown host, disconnected host, relay
  unreachable, stale device, and host-fingerprint mismatch states from local
  source-compatible metadata;
- source local relay diagnostics expose the same blocking states without
  stopping CCB runtime or opening a public listener;
- pairing and secure storage preserve relay metadata without storing the
  pairing code;
- existing route-boundary tests continue to keep route metadata below the
  transport boundary;
- full Flutter tests and debug APK build pass;
- no public DNS, Cloudflare, production relay, public IP, or physical phone is
  required.

## Follow-Up Packages

1. Fold relay health, lifecycle, notification/deep-link, readable-history, and
   terminal-control evidence into the emulator-only acceptance checklist.
2. Only after fake/local source/app relay diagnostics pass, deploy or smoke a real
   `relay.seemlab.top` endpoint.
