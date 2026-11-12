# Cloudflare Alpha Hardening

Date: 2026-06-18
Status: Source/app/harness route guards landed; config/credentials pending

## Purpose

Turn the accepted quick-tunnel smoke into a safer Cloudflare alpha route for
normal users without changing the `GatewayTransport` contract or exposing a
public gateway listener.

## Official References

- Quick tunnels are for testing/development, not production:
  <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/>.
- Locally-managed tunnels use `cloudflared tunnel create <NAME>`, local
  configuration, DNS routing, and `cloudflared tunnel run`:
  <https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/>.
- Cloudflare Tunnel routes traffic from Cloudflare to services behind
  `cloudflared` after a public hostname is mapped to a local service:
  <https://developers.cloudflare.com/tunnel/routing/>.
- Cloudflare WebSockets must remain enabled for terminal streaming:
  <https://developers.cloudflare.com/network/websockets/>.

## Named-Tunnel Setup Shape

The CCB gateway remains loopback-bound. Cloudflare owns the public route,
while CCB owns device identity, pairing, terminal tokens, and audit.

Server setup shape:

```bash
cloudflared tunnel login
cloudflared tunnel create ccb-mobile
cloudflared tunnel route dns ccb-mobile mobile.example.com
```

Example `~/.cloudflared/config.yml`:

```yaml
tunnel: <tunnel-uuid>
credentials-file: /home/<user>/.cloudflared/<tunnel-uuid>.json

ingress:
  - hostname: mobile.example.com
    service: http://127.0.0.1:8787
  - service: http_status:404
```

Runtime shape:

```bash
ccb mobile serve \
  --listen 127.0.0.1:8787 \
  --public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel

cloudflared tunnel run ccb-mobile
```

Validation shape:

```bash
tools/mobile_gateway_terminal_smoke.py \
  --cloudflared-named-tunnel \
  --gateway-listen 127.0.0.1:8787 \
  --gateway-public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

The named tunnel or an equivalent cellular run is the next required public
route gate. Quick-tunnel evidence proves the route shape; named/cellular
evidence proves a stable user setup path.

Current local blocker: this host now has user-local `cloudflared` at
`/home/bfly/.local/bin/cloudflared`, but still has no
`/home/bfly/.cloudflared/config.yml`, `/home/bfly/.cloudflared/cert.pem`, or
Cloudflare account/domain credentials. A 2026-06-18 recheck found no
`/home/bfly/.cloudflared` directory and zero local credentials JSON files, so
the named-tunnel gate cannot be executed from this environment yet.

## Named-Tunnel Preflight

Mobile commit `4f41391` added a preflight mode that checks the local
`cloudflared` binary, config, credentials file, public URL, route provider, and
loopback origin without starting a disposable CCB runtime. Mobile commit
`6f26591` made that preflight hostname-aware for multi-ingress configs and
added local self-tests for both blocked and ok paths:

```bash
tools/mobile_gateway_terminal_smoke.py \
  --cloudflared-named-tunnel-preflight \
  --gateway-listen 127.0.0.1:8787 \
  --gateway-public-url https://mobile.example.com \
  --route-provider cloudflare_tunnel
```

On this host the preflight returns `status: blocked` because
`/home/bfly/.cloudflared/config.yml` is missing. It also warns that
`/home/bfly/.cloudflared/cert.pem` is missing for `cloudflared login`,
`tunnel create`, and DNS route commands. Source commit `44ba9edd` documents
the preflight in the English and Chinese setup guides. Source commit
`973a2707` clarifies that multi-ingress configs are matched by `hostname`
against `--gateway-public-url`.

Mobile commit `1c2d4de` added `--cloudflared-named-tunnel`, which runs the
preflight before starting CCB runtime, starts `cloudflared tunnel run`, waits
for a registered tunnel connection, then uses the existing public health and
terminal smoke path. Source commit `444b648c` documents this automated smoke
command. Mobile commit `f4bb5e5` adds a CLI-level regression proving a failed
named-tunnel preflight exits before disposable project creation or CCB runtime
startup.

Mobile commit `eadcece` added `next_actions` to blocked preflight JSON, and
source commit `9ce07104` documents it. The output now tells the operator which
Cloudflare setup command or config edit is needed before the public smoke can
run. Mobile commit `de79cde` then added `config_template` to the same JSON,
and source commit `a2ac6f1e` documents it. The blocked output now includes a
side-effect-free `~/.cloudflared/config.yml` draft using the requested
hostname and gateway listen origin. Mobile commit `2ff36a9` added a
round-trip self-test proving that generated draft can become an ok local
preflight when the referenced credentials file exists. Mobile commit
`11bae28` and source commit `69891f03` added and documented
`--cloudflared-tunnel-name <name>` handoff, so non-default tunnel names stay
consistent across setup `next_actions`, preflight output, and automated smoke.
Mobile commit `e1e14a2` and source commit `867300d7` then made fixed loopback
`--gateway-listen` an explicit named-tunnel preflight gate, blocking the
default dynamic `127.0.0.1:0` port before it can become a Cloudflare ingress
origin. Mobile commit `3f0a0b5` and source commit `8e047913` added and
documented `named_tunnel_smoke_command`, so preflight JSON now includes the
copyable automated public smoke command after setup fixes. Mobile commit
`434ed01` and source commit `93c0de50` then added and documented
`cloudflared_run_command` plus `existing_tunnel_smoke_command` for manual
cloudflared startup or already-running tunnel validation. Mobile commit
`53a50dd` and source commit `9cd71bd8` made the public URL shape explicit:
named-tunnel preflight now blocks path, query, fragment, or credentials in
`--gateway-public-url`, emits `suggested_gateway_public_url`, and normalizes
the copyable smoke commands to the origin-only URL. Mobile commit `9396842`
mirrors that rule in app-side `GatewayRouteDiagnostics`, so a paired
Cloudflare profile with a non-origin gateway URL fails the runtime route check
before terminal WebSocket use. Mobile commit `1d4e28c` then added a
`device_gateway_url` diagnostics check so the server-reported device route
metadata must match the app profile route origin before the route is ready.
Source commit `a071e257` now makes `ccb mobile serve --public-url` reject
non-origin public URLs before pairing metadata is emitted.

## User-Facing Setup Docs

Source commit `c3c7fd1b` landed the initial public setup guides in
`/home/bfly/yunwei/ccb_source`:

- `docs/mobile-cloudflare-alpha.md`
- `docs/mobile-cloudflare-alpha.zh.md`
- README entry links from `README.md` and `README_zh.md`

These docs promote the setup path out of plan-tree notes, while still keeping
named-tunnel or cellular validation as a required alpha gate.

## Landed Security Posture

Source commit `8a264cae` landed host-local device management:

- `ccb mobile devices` lists paired devices from local
  `.ccb/ccbd/mobile/devices.json`;
- `ccb mobile revoke <device_id>` revokes a device locally without exposing a
  public HTTP admin route;
- device revoke cascades to still-open terminal handles for that device;
- terminal token authentication also checks whether the owning device has been
  revoked;
- audit records device and terminal revocation metadata without terminal bytes
  or plaintext tokens.

Already-landed gateway/token properties:

- pairing codes expire after 10 minutes by default;
- terminal tokens expire after 5 minutes by default;
- terminal input and paste require monotonic input sequence numbers;
- terminal reconnect requires the latest output resume cursor after a
  disconnect;
- ProjectView and terminal-open responses redact tmux socket/session evidence;
- `--public-url` changes pairing metadata only and does not change the
  loopback listener.

## Remaining Alpha Gates

1. Follow preflight `next_actions`, `config_template`, source/app/harness
   origin-only and device route consistency checks, and emitted smoke commands
   to provision Cloudflare named-tunnel config/credentials.
2. Run automated named-tunnel or cellular validation and record full smoke
   evidence.
3. Refine the user-facing setup docs after named/cellular validation evidence,
   especially any Cloudflare account, DNS, WebSocket, or cellular-network
   caveats found during the run.
4. Decide whether Cloudflare Access is optional defense-in-depth for alpha docs.
5. Add host-side device list/revoke UI or app-visible device status only after
   the CLI path and public smoke are stable.
6. Keep broad public/non-loopback gateway exposure blocked until the named or
   cellular gate passes.
