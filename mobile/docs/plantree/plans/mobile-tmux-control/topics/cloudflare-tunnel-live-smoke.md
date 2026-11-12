# Cloudflare Tunnel Live Smoke

Date: 2026-06-18
Status: Quick tunnel live smoke accepted with smoke-only DNS override

## Purpose

Define the first repeatable not-on-LAN validation path for the mobile gateway
without changing the app or gateway protocol when moving later to a relay.

The smoke must prove:

- `ccb mobile serve` stays loopback-bound;
- pairing metadata uses `route_provider: cloudflare_tunnel` and an HTTPS
  public gateway URL;
- the app-side route diagnostics gate reports ready;
- ProjectView and terminal-open responses do not expose tmux socket/session
  evidence;
- terminal output, input, paste, resize, close, and resume-cursor reconnect
  still work through the public route.

## Official Setup References

- Cloudflare quick tunnels can expose a local web server for development with
  `cloudflared tunnel --url http://localhost:8080`; Cloudflare labels quick
  tunnels as testing-oriented, not production:
  <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/>.
- Cloudflare Tunnel uses `cloudflared` as the connector and creates outbound
  connections from the origin to Cloudflare, avoiding inbound firewall/public
  IP exposure: <https://developers.cloudflare.com/tunnel/>.
- Locally-managed named tunnels can publish a hostname through
  `cloudflared tunnel route dns <UUID-or-NAME> <hostname>` and run with
  `cloudflared tunnel run <UUID-or-NAME>`:
  <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/>.
- Cloudflare supports proxied WebSocket connections; terminal frame streaming
  must still be verified by the CCB smoke because CCB also depends on pairing,
  terminal tokens, and resume cursors:
  <https://developers.cloudflare.com/network/websockets/>.

## Prepared Harness

Mobile commit `08eed72` adds these harness modes, commit `f75f1ec` waits for
the public `/v1/health` endpoint before launching the Dart smoke, and commit
`a8eeec0` adds smoke-only public DNS override support for generated
quick-tunnel hostnames when the local system resolver cannot resolve them:

```bash
tools/mobile_gateway_terminal_smoke.py \
  --gateway-listen 127.0.0.1:8787 \
  --gateway-public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

Use this when a named Cloudflare Tunnel already routes
`https://mobile.example.com` to `http://127.0.0.1:8787`.

```bash
tools/mobile_gateway_terminal_smoke.py --cloudflared-quick-tunnel
```

Use this for a development quick tunnel. The harness allocates a loopback port,
starts `cloudflared tunnel --url http://127.0.0.1:<port>`, parses the generated
`*.trycloudflare.com` URL, starts `ccb mobile serve` on the same loopback port,
and injects that public URL plus `cloudflare_tunnel` into the pairing payload.
For quick tunnels, the harness may resolve the generated hostname with public
DNS and pass a process-local `host=ip` override into the Dart smoke; TLS SNI
and HTTP Host still use the original public hostname.

Both modes run the same Dart smoke path and set
`CCB_MOBILE_ROUTE_PROVIDER=cloudflare_tunnel`, so the app fails closed if the
claimed profile falls back to LAN metadata.

## Source Support

CCB source commit `a222446c` adds:

```bash
ccb mobile serve \
  --listen 127.0.0.1:8787 \
  --public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

`--public-url` changes pairing metadata only. It does not bind a public
listener; `parse_listen_address` still rejects non-loopback listen addresses.

## Local Verification

This environment verified the route-aware harness on loopback:

- source focused pytest: `144 passed`;
- app `tools/mobile_gateway_terminal_smoke.py`: returned `status: ok`;
- smoke route provider: `lan`;
- `route_diagnostics_ready: true`;
- terminal evidence: `input_sent: true`, `paste_sent: true`,
  `resize_sent: true`, `close_completed: true`, `close_timed_out: false`, and
  `reconnect_completed: true`;
- `target_has_direct_tmux_evidence: false`;
- app `flutter test`: 52 tests passed;
- app debug APK build succeeded.

This environment accepted the live quick-tunnel path:

- temporary `cloudflared` version: `2026.6.0`;
- quick tunnel URL:
  `https://dir-peter-measuring-wholesale.trycloudflare.com`;
- source gateway startup succeeded with `route_provider: cloudflare_tunnel`
  and local listener `127.0.0.1:58999`;
- public DNS override used `dig @1.1.1.1` and selected `104.16.231.132` for
  the generated hostname without changing system DNS;
- public `/v1/health` returned HTTP `200` after 12 attempts;
- Dart smoke returned `status: ok`, `route_provider: cloudflare_tunnel`,
  `route_diagnostics_ready: true`, `target_has_direct_tmux_evidence: false`,
  `input_sent: true`, `paste_sent: true`, `resize_sent: true`,
  `close_completed: true`, `close_timed_out: false`, and
  `reconnect_completed: true`;
- cleanup stopped cloudflared, the gateway process, and the disposable CCB
  runtime.

`flutter analyze` and `dart analyze lib test tool` reported no Dart issues but
returned Analysis Server watcher errors in this environment:
`OS Error: Too many open files, errno = 24`. This is recorded as an
environment verification limitation, not as an accepted app diagnostic pass.

## Acceptance

A live Cloudflare smoke is accepted when the JSON result contains:

- `status: ok`;
- `gateway.route_provider: cloudflare_tunnel`;
- `dart_smoke.route_provider: cloudflare_tunnel`;
- `dart_smoke.route_diagnostics_ready: true`;
- `dart_smoke.target_has_direct_tmux_evidence: false`;
- `dart_smoke.reconnect_completed: true`;
- cleanup with gateway and disposable CCB runtime stopped unless
  `--keep-running` was requested.

## Current Limitation

The generated quick-tunnel hostname still does not resolve through this host's
system resolver, but the smoke harness now records and uses a process-local
public DNS override for validation. Product hardening still needs named-tunnel
or cellular validation and user-facing setup docs before broad
public/non-loopback gateway exposure.

See [cloudflare-alpha-hardening.md](cloudflare-alpha-hardening.md) for the
named-tunnel setup shape and the host-side device revocation hardening that
landed after this quick-tunnel smoke.
