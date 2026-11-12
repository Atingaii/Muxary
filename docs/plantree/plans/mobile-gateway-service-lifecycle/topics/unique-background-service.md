# Unique Background Mobile Gateway Service

Date: 2026-07-01

## Current Behavior

Relevant current code paths:

- `lib/cli/management_runtime/commands_runtime/update.py`
  - `ccb update mobile` calls `run_mobile_update_onboarding()`.
  - It does not start, stop, or replace a gateway process.
- `lib/cli/services/mobile_update.py`
  - prints Tailscale/mobile setup guidance and a suggested
    `ccb mobile serve --listen 127.0.0.1:8787 ...` command.
- `lib/cli/services/mobile.py`
  - `prepare_mobile_gateway()` builds a foreground current-project gateway.
  - `prepare_server_mobile_gateway()` builds a foreground server-wide gateway.
- `lib/cli/management_runtime/commands_runtime/install.py`
  - `ccb install mobile` calls `prepare_server_mobile_gateway()` and then
    blocks in `serve_forever()`.

Observed failure:

- If a previous gateway still listens on `127.0.0.1:8787`, the next gateway
  creation fails at bind time with `OSError [Errno 98] Address already in use`.
- On 2026-07-01 the local blocker was a development gateway:
  `/tmp/ccb-mobile-real-project-emulator/notifications-testccb2/gateway_runner.py`.
  Killing that process released `127.0.0.1:8787`, while Tailscale-side listeners
  on tailnet addresses remained separate from the loopback gateway.

## Target Contract

`ccb update mobile` should become the primary host-owned startup/update command:

1. Acquire a host mobile service lock.
2. Load the current mobile service state.
3. If a prior CCB-managed mobile gateway is alive, stop it and wait for the
   loopback port to release.
4. If the state is stale, clear it.
5. If the requested loopback port is owned by a non-CCB process, fail with a
   clear diagnostic and do not kill it.
6. Spawn one background CCB-managed mobile gateway.
7. Wait until the gateway responds to `/v1/health`.
8. Write fresh service state and print the active gateway/pairing summary.

The command should be repeatable. A second `ccb update mobile` should refresh
or replace the existing managed service, not report address-in-use.

## State Layout

Use `mobile_host_state_dir()` as the host authority root.

Files:

- `service.lock`
  - acquired before inspecting or replacing the service;
  - stale locks are cleared only after confirming the owner pid is gone or the
    lock age exceeds a conservative timeout.
- `service.json`
  - CCB-owned service authority, not a user config file.
- `service.log`
  - stdout/stderr for the background gateway process.

Proposed `service.json` fields:

```json
{
  "schema_version": 1,
  "record_type": "ccb_mobile_host_service",
  "pid": 12345,
  "process_group_id": 12345,
  "generation": 7,
  "host_id": "host-...",
  "listen": "127.0.0.1:8787",
  "local_gateway_url": "http://127.0.0.1:8787",
  "gateway_url": "https://host.tailnet.ts.net:8787",
  "route_provider": "tailnet",
  "state_dir": "/home/user/.local/state/ccb/mobile",
  "started_at": "2026-07-01T00:00:00Z",
  "command_kind": "ccb_mobile_host_serve",
  "entrypoint": "/home/user/.local/bin/ccb"
}
```

Ownership validation must not trust pid alone. A live pid is managed only when
state and process evidence agree, for example:

- pid exists;
- process command line contains the CCB internal mobile-host serve command;
- state dir or listen argument matches the state record;
- optional generation/host id arguments match.

## Command Shape

Add an internal command, not a public workflow command:

```bash
ccb __mobile-host-serve \
  --listen 127.0.0.1:8787 \
  --public-url https://host.tailnet.ts.net:8787 \
  --route-provider tailnet \
  --state-dir ~/.local/state/ccb/mobile \
  --generation 7 \
  --host-id host-...
```

This command owns `prepare_server_mobile_gateway()` and `serve_forever()`.
It should write startup state only after the server socket is bound and pairing
metadata exists. If it exits, the manager can classify the state as stale on the
next `ccb update mobile`.

Public command behavior:

- `ccb update mobile`
  - performs setup guidance plus managed background service refresh;
  - prints active gateway URL, local URL, route provider, state dir, pid, and
    pairing summary.
- `ccb install mobile`
  - should call the same manager or become a compatibility alias for
    `ccb update mobile`;
  - should not create a second independent foreground server-wide gateway.
- `ccb mobile serve`
  - remains a foreground project-scoped/debug command;
  - if it fails with address-in-use, it should point users to
    `ccb update mobile` for the managed host service.

## Port And Route Boundaries

CCB owns only the loopback gateway process.

- Tailscale Serve and Cloudflare Tunnel are route layers and are not killed by
  the first slice.
- A tailnet or Cloudflare listener can keep exposing the same port after the
  loopback gateway is replaced.
- If the loopback port is occupied by an external process, CCB reports the pid
  and command line and asks the user to stop it or choose a different port.

## Implementation Slices

1. Service state helpers:
   - read/write/remove `service.json`;
   - detect live managed pid with cmdline validation;
   - detect loopback port owner for diagnostics.
2. Replacement manager:
   - lock;
   - stop managed old pid/process group;
   - wait for port release;
   - refuse external owners;
   - spawn internal command;
   - wait for `/v1/health`.
3. Internal command:
   - run server-wide gateway forever;
   - write state and logs;
   - close server cleanly on SIGTERM.
4. CLI integration:
   - wire `ccb update mobile`;
   - route `ccb install mobile` through the same manager;
   - update render output.
5. Docs:
   - update Cloudflare/Tailscale setup docs only after behavior is implemented.

## Tests

Unit tests:

- stale `service.json` with dead pid is cleared and startup proceeds;
- live managed pid is terminated before replacement;
- external port owner is reported and not killed;
- macOS/non-Linux-style port detection uses `lsof` when `ss` is unavailable;
- a connectable loopback listener with unknown pid is refused, not ignored;
- truncated managed command evidence is accepted only when `state_dir` matches;
- service lock prevents concurrent replacements;
- health wait failure terminates the newly spawned process;
- internal serve removes its own current `service.json` when it exits;
- internal serve reports state-write failures before entering `serve_forever()`;
- logged-in `ccb update mobile` onboarding injects a managed service refresh
  instead of only printing the foreground `ccb mobile serve` instruction;
- logged-in onboarding reports invalid service-summary results as explicit
  gateway update failures;
- internal command routing occurs before normal project discovery.

Covered by the first local implementation slice:

- `test/test_mobile_host_service.py`
- `test/test_cli_services_mobile_update.py`
- `test/test_cli_management_update.py`
- `test/test_v2_cli_router.py`

Integration/smoke tests:

- from `/home/bfly/yunwei/test_ccb2`, run source `ccb_test update mobile`
  twice and assert the second run replaces or refreshes the managed service
  without `Address already in use`;
- verify `/v1/health` on `127.0.0.1:8787`;
- verify paired/mobile route metadata remains loopback-safe and redacted.

## Open Questions

- Should `ccb update mobile` always create a new pairing code, or should it
  optionally keep the current service running when configuration is unchanged?
- Should there be a public `ccb mobile status` or `ccb mobile stop` command in
  the same slice, or should update/install remain the only service controls for
  now?
