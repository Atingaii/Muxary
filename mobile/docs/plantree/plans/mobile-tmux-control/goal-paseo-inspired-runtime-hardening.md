# CCB Mobile Paseo-Inspired Runtime Hardening Goal

Date: 2026-07-13
Status: In Progress
Mode: Execute-ready

## Purpose

Harden the existing Flutter-based CCB Mobile application by adopting the
connection-runtime patterns proven in Paseo without forking Paseo or replacing
CCB's mobile gateway, project/window/agent model, tmux ownership, signing
identity, or release channel.

The goal is a mobile client that returns from Android background, network
changes, gateway restarts, and ordinary process recreation without asking the
user to reconnect or scan again while its stored device credential remains
valid. Reliable killed/background task-completion delivery must use push rather
than pretending an ordinary app WebSocket can remain alive indefinitely.

## Binding Product Decisions

1. `/home/bfly/yunwei/ccb_source/mobile/app` remains the authoritative Flutter
   app. The retired `/home/bfly/yunwei/ccb_mobile` repository is not an
   implementation surface.
2. The Python server-wide mobile gateway remains authoritative for projects,
   windows, agents, native conversations, files, notifications, and validated
   tmux pane control.
3. Paseo is a design and implementation reference. Reuse only compatible
   AGPL-attributed ideas or isolated code where a deliberate port is justified;
   do not import Paseo's daemon/agent lifecycle.
4. The current pairing handoff remains deliberately reusable without an
   automatic expiry or claim-count limit. The same pairing code/QR may claim
   any number of devices until the operator explicitly runs
   `ccb update mobile`, which rotates the handoff. Existing paired device
   tokens survive handoff rotation until individually revoked.
5. A temporary route outage, timeout, gateway restart, Android background, or
   process recreation must never erase a valid profile/device token. Only an
   authoritative `401`, `403`, or revoked-device response may require re-pair.
6. Background reliability has two modes:
   - default: cached UI + foreground catch-up + OS push notifications;
   - optional keep-connected mode: Android foreground service only while the
     user explicitly enables it or an interactive Terminal/large transfer is
     active.
7. Reconnect must never replay terminal input, message submission, lifecycle
   mutation, or file mutation automatically.

Decision detail: [Decision 021](decisions/021-reusable-pairing-until-manual-rotation.md).

## Target Runtime Shape

```text
Flutter UI
  -> MobileConnectionSupervisor
       -> persistent GatewayProfileStore
       -> route/liveness state machine
       -> HTTP repository
       -> invalidation + completion stream
       -> conversation/event cursor store
       -> Terminal session supervisor
       -> push registration
  -> cached project / view / conversation snapshots

CCB mobile gateway
  -> device + reusable pairing handoff registry
  -> bounded persistent event journal
  -> presence/focus records
  -> FCM-compatible push sender
  -> existing project/conversation/terminal/file authority
```

Pages consume one connection state instead of inventing independent status:

```text
offline -> connecting -> online
                     -> degraded -> reconnecting -> online
                     -> authenticationRequired
```

## Package A: Flutter Connection Supervisor And Resume

Scope:

- introduce one app-lifetime connection supervisor above project pages;
- restore the last valid profile, cached project list, selected project,
  window, agent, and conversation before waiting for network;
- validate `/v1/health` and `/v1/devices/me` using the stored token;
- converge ordinary HTTP, invalidation SSE, completion subscription, and
  Terminal connectivity into one connection state;
- reconnect using bounded exponential backoff with jitter;
- on Android resume, immediately reconnect and perform cursor-based catch-up;
- preserve cached UI while reconnecting and expose Retry/Diagnostics without
  replacing content with an empty/error page;
- keep sends fail-closed while offline; do not blindly retry mutations;
- preserve selected Terminal target identity and renew a handle only after the
  project/window/agent/pane epoch is revalidated.

Acceptance:

- HOME for 30 seconds and 5 minutes returns to visible cached content
  immediately and reaches online within 2 seconds on a healthy route;
- gateway restart recovers within 10 seconds without manual reconnect;
- profile/token survives timeout, DNS/Tailscale outage, and process restart;
- authoritative revoke enters `authenticationRequired` and offers Re-pair;
- no duplicated subscriptions, refresh storms, or terminal input replay.

## Package B: Gateway Journal, Presence, And Pairing Semantics

Scope:

- preserve the reusable pairing handoff until explicit manual rotation;
- make `ccb update mobile` rotate the handoff while preserving issued device
  records/tokens;
- persist pairing generation and claim audit without imposing expiry/count;
- expose a bounded monotonic event journal shared by project/activity,
  conversation, completion, and device-relevant invalidations;
- support `Last-Event-ID`/cursor resume and explicit `resync_required` when the
  requested cursor fell outside retention;
- add device presence containing app visibility, focused project/agent/
  terminal, and last real user activity;
- keep heartbeat updates separate from project activity ordering;
- preserve multi-device isolation, scopes, revocation, and audit redaction.

Acceptance:

- the same QR successfully pairs at least three clean device profiles before
  manual rotation;
- a fourth claim after prior claims still succeeds;
- running `ccb update mobile` changes pairing generation/code, makes the old
  handoff fail, and keeps existing device tokens valid;
- reconnect cursor returns every retained event once, with deterministic
  dedupe; stale cursor returns `resync_required`;
- presence never logs terminal input, prompt, reply, local path, or token.

## Package C: Push Notifications And Optional Foreground Mode

Scope:

- register a per-device Android FCM token through the paired device identity;
- store push tokens encrypted/permission-restricted and remove invalid tokens;
- send low-sensitive completion/permission/error notifications when no active
  client is visibly focused on the target;
- payload contains only stable route/dedupe identifiers and short display
  labels, never prompt/reply/path/terminal output;
- tap deep-links to the project/agent and performs normal foreground catch-up;
- retain current in-app unread markers and dedupe across SSE and Push;
- add an opt-in Android `remoteMessaging` foreground service for explicit
  keep-connected/active-Terminal/large-transfer use only;
- show a persistent notification while the service is active and stop it when
  the user disables the mode or the qualifying operation ends;
- do not make FCM credentials, signing secrets, or service-account material
  part of the repository.

Acceptance:

- background and ordinary process-killed app receives one completion
  notification and opens the correct target;
- visible target suppresses the OS notification but still reconciles state;
- duplicate completion from Push + SSE produces one unread event;
- notification permission denial does not break foreground operation;
- Android force-stop is documented as an OS boundary, not misreported as pass;
- optional foreground mode has explicit user control and measured power cost.

## Package D: Strict Real-Device Recovery And Power Gate

The integrated package is not accepted by unit/widget tests alone.

Environment:

- current signed debug/profile APK built from the exact tested commit;
- Android Emulator plus one physical Android phone;
- server-wide gateway with real mounted CCB projects;
- dedicated `/home/bfly/yunwei/test_ccb2` project/agent for mutations;
- no exploratory prompt to `ccb_mobile`, `ccb_source`, or another active user
  project.

Scenarios:

1. foreground idle and active conversation;
2. HOME 30 seconds, 5 minutes, and 30 minutes;
3. screen off/on and forced Doze maintenance cycle;
4. Wi-Fi/mobile network transition where available;
5. Tailscale stop/start and route recovery;
6. gateway kill/restart and host reboot simulation;
7. app process kill/relaunch and Android force-stop boundary;
8. three-device pairing with the same handoff, then manual rotation;
9. completion Push, deep link, unread marker, and dedupe;
10. active Terminal reconnect with zero input replay;
11. foreground-service opt-in/on/off and battery sampling;
12. revoke one device while other devices remain connected.

Evidence packet:

- APK path/SHA/version/commit and signing certificate digest;
- gateway URL/provider and pairing generation with secrets redacted;
- screenshots + UI XML for online/reconnecting/cached/auth-required states;
- logcat, gateway logs, event cursor dumps, presence summaries, push delivery
  evidence, HTTP request audit, meminfo/gfxinfo/battery/wakelock samples;
- exact recovery timings and PASS/FAIL per scenario.

Budgets:

- cached UI visible immediately on resume/relaunch;
- healthy foreground resume online in <= 2 seconds p95;
- gateway restart recovery <= 10 seconds p95;
- completion push normally visible <= 10 seconds;
- zero unexpected re-pair requests without authoritative auth failure;
- zero mutation/input replay after reconnect;
- no FATAL/ANR/OOM and no reconnect/request storm;
- no sustained background polling when push/default mode is selected.

## Implementation Discipline

- Use coherent packages, not micro-task fragmentation.
- Each implementation worker owns focused tests and a commit on a branch based
  on `main`; final merge happens only after lead/reviewer diff audit.
- Do not overwrite unrelated dirty workflow/release/provider files in the main
  working tree.
- Dependency additions require a source/version/license check and must not
  expose secrets.
- Prefer existing Flutter/gateway abstractions; split new runtime logic out of
  large screen/service files.
- Add protocol fields compatibly and version capability negotiation where
  older app/gateway combinations may coexist.
- Keep feature flags for Push and foreground service until physical-phone and
  release-mode evidence passes.

## Rollout And Rollback

Rollout order:

1. supervisor/cached foreground recovery;
2. persistent journal/cursor/presence;
3. Push registration and delivery;
4. optional foreground service;
5. physical-phone soak and release rollout.

Rollback:

- supervisor can fall back to the existing repository transports;
- event journal can force `resync_required` and full read-only refresh;
- Push and foreground service remain independently disableable;
- pairing rotation never revokes already-issued device tokens;
- retain the last accepted Release APK until the new release passes upgrade,
  reconnect, and notification gates.

## Completion Gate

Do not mark this goal complete until Packages A-D are integrated on `main`,
focused and relevant full test suites pass, a same-commit APK passes real
emulator and physical-phone evidence, reusable pairing behavior is proven
before and after manual rotation, and the plan-tree evidence/status is updated.

