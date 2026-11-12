# Decision 017: Mobile Is An Optional CCB Source Bundle

Date: 2026-06-23
Status: Accepted for planning and implementation shaping

## Context

CCB Mobile needs host-side tooling beyond the core CCB runtime:

- mobile gateway serve/check/QR onboarding commands;
- optional Tailnet setup and diagnostics;
- optional Tailscale installation/login handoff;
- mobile app installation guidance or artifact handoff;
- route-provider smoke checks for HTTP, WebSocket, diagnostics, and revoke.

These requirements are materially different from normal CCB start/update
behavior. They may install or inspect VPN/network software, ask for OS package
manager privileges, open a browser for Tailscale login, and guide phone/iPad
installation. Making this part of normal `ccb update` would surprise users who
do not want mobile access.

CCB already has a precedent for optional source-owned tooling:
`ccb update rich` installs and refreshes the rich workbench bundle outside the
mandatory core update path.

## Decision

Host-side CCB Mobile tooling should live in `/home/bfly/yunwei/ccb_source` as
an independent optional bundle, installed or refreshed with:

```bash
ccb update mobile
```

Normal `ccb update` must not install the mobile bundle, Tailscale, phone app
artifacts, or other mobile-only dependencies by default.

The optional bundle should be shaped like the rich workbench pattern:

- explicit update target: `ccb update mobile`;
- explicit uninstall/disable target when needed, for example
  `ccb uninstall mobile`;
- CCB-owned install state under CCB's user data/cache locations;
- host-side commands and diagnostics in CCB source, not scattered across the
  standalone Flutter app repository;
- best-effort dependency install with clear prompts and non-interactive skip
  controls;
- no silent VPN/network software installation.

`ccb update mobile` may continue into a guided onboarding flow after the bundle
is ready:

```text
ensure mobile host bundle
ensure ccb mobile serve support
detect/install Tailscale with explicit confirmation
open or print Tailscale login when not authenticated
start loopback gateway
start tailscale serve for Tailnet route
print CCB Mobile QR and phone installation guidance
run route diagnostics and terminal smoke when possible
```

The mobile app source can still live in this standalone `ccb_mobile` workspace
while the host-side bundle lives in CCB source. If app artifacts are later
distributed through CCB, they should be downloaded/verified as optional mobile
bundle artifacts, not copied into the required CCB runtime path.

## Boundaries

- `ccb update mobile` may prompt to install Tailscale or platform packages; it
  must not silently install VPN/network software.
- CCB must not store Tailscale passwords, OAuth tokens, admin API tokens, or
  user-owned tailnet credentials.
- Tailscale login, phone VPN permission, App Store/TestFlight installation, and
  tailnet admin policy approval remain user-controlled external steps.
- The bundle should not make Tailnet the ordinary-user default route. CCB Relay
  remains the default not-on-LAN route per
  [Decision 011](011-relay-default-remote-route.md).
- The bundle must preserve `GatewayTransport` and `RouteProvider` boundaries:
  route-provider setup does not change project ids, ProjectView, terminal ids,
  terminal frame schemas, content ids, or CCB device-token authority.

## Consequences

- Core CCB users are not forced to install mobile dependencies.
- Mobile users get a short, memorable setup entrypoint:
  `ccb update mobile`.
- Tailnet setup can be mostly automated while still respecting OS, VPN, and
  Tailscale account consent boundaries.
- CCB source owns host-side mobile setup and diagnostics, making release,
  repair, and uninstall behavior consistent with other CCB optional bundles.
- The standalone Flutter mobile repository can remain focused on app code,
  app-side tests, and mobile UI/product work.

## Implementation Evidence

Lead accepted the first source-side implementation on 2026-06-23:

- Worktree: `/home/bfly/yunwei/ccb_source_mobile_update_tailnet`
- Branch: `worker1/mobile-update-tailnet`
- Commits:
  - `b6e148f2 feat: add mobile tailnet update onboarding`
  - `d73ae650 fix: align mobile tailnet serve port`
- Verification:
  - focused/relevant tests after follow-up: 147 passed;
  - worker full pytest before follow-up: 2993 passed, 2 skipped;
  - `python -m py_compile ...`: passed;
  - `git diff --check`: passed;
  - reviewer1 accepted the final stack.

The follow-up fixed generated route alignment so
`--public-url https://<host>:8787` matches
`tailscale serve --bg --https=8787 http://127.0.0.1:8787`.

## Validation

This decision is validated when:

1. `ccb update mobile` is accepted by the management parser as an optional
   target, analogous to `ccb update rich`;
2. normal `ccb update` leaves mobile/Tailscale dependencies untouched;
3. mobile bundle status/doctor output can explain installed, missing,
   partially configured, and blocked states;
4. logged-in Tailscale users can proceed directly to gateway/QR setup;
5. non-logged-in users get a browser or QR login handoff without CCB storing
   credentials;
6. `ccb uninstall mobile` or equivalent removes CCB-owned mobile bundle state
   without deleting CCB project runtime or Tailscale user configuration;
7. route diagnostics still prove Tailnet, LAN, relay, and Cloudflare use the
   same app-facing gateway contract.
