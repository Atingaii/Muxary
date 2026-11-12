# Mobile Gateway Service Lifecycle Roadmap

Date: 2026-07-01

## Done

- Reproduced the core local-port collision with two server-wide gateway
  preparations: the second bind to the same loopback port raises
  `OSError [Errno 98] Address already in use`.
- Confirmed current command split:
  - `ccb update mobile` prints onboarding guidance only;
  - `ccb mobile serve` runs a foreground current-project gateway;
  - `ccb install mobile` runs a foreground server-wide gateway;
  - no pid/state/health ownership layer exists for a unique background service.
- Released the immediate local `127.0.0.1:8787` blocker by terminating the
  stale development gateway process requested by the user.
- Landed the first local implementation slice:
  - `cli.services.mobile_host` manages host service state, lock files, stale
    state cleanup, managed pid replacement, external port-owner refusal,
    background spawn, health wait, and cleanup of failed spawns;
  - `ccb update mobile` now injects a managed service refresh into the
    logged-in Tailnet onboarding path;
  - the internal `ccb __mobile-host-serve` command is routed before normal CLI
    project discovery and owns the long-running server-wide gateway process.
- Addressed coworker review findings for the first slice:
  - loopback port owner detection now uses `ss`, then `lsof`, then a narrow
    "connectable but unknown owner" refusal instead of silently continuing;
  - managed pid fallback requires the recorded `state_dir` to match the
    current service state dir;
  - internal serve shutdown removes only its own current `service.json`;
  - state-write and onboarding service-summary failures are surfaced with
    explicit user-facing errors.
- Verified the first slice with:
  - `python -m pytest -q test/test_mobile_host_service.py
    test/test_cli_services_mobile_update.py test/test_mobile_cli_service.py
    test/test_v2_cli_router.py test/test_v2_cli_parser.py
    test/test_v2_cli_render.py test/test_cli_management_update.py
    test/test_mobile_gateway_service.py test/test_mobile_gateway_relay.py
    test/test_mobile_gateway_terminal.py`
    (`270 passed`);
  - `python -m py_compile` over the touched CLI/mobile files;
  - targeted `git diff --check`;
  - `HOME=/home/bfly/yunwei/test_ccb2/source_home
    CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home
    /home/bfly/yunwei/ccb_source/ccb_test --diagnose` from
    `/home/bfly/yunwei/test_ccb2`.

## In Progress

- Controlled source-runtime smoke from `/home/bfly/yunwei/test_ccb2`:
  run `ccb_test update mobile` only when starting/replacing the host mobile
  gateway is intended.

## Next

1. Reuse the same manager from `ccb install mobile` or make `install mobile`
   a compatibility alias for the managed background startup path.
2. Add an explicit status/stop command decision if operational testing shows
   users need it before release.
3. Update user-facing mobile setup docs after the command behavior is accepted.

## Deferred

- Route-provider process supervision for `tailscale serve --bg` or
  `cloudflared tunnel run`.
- Multi-profile host gateways on different ports.
- Systemd/user-service integration.

## Release Gate

This work is release-ready only when:

- repeated `ccb update mobile` on the same host is idempotent;
- managed old gateway processes are stopped before new ones bind the port;
- stale pid files do not block startup;
- external port owners are never killed implicitly;
- startup waits for a health check instead of reporting success after a blind
  spawn;
- tests cover process ownership, state files, lock behavior, and address-in-use
  failure handling.
