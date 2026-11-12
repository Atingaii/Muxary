# Android push and foreground-mode contract

## Decisions

Android push is an opt-in, feature-flagged delivery hint. The app uses the
official FlutterFire `firebase_core` and `firebase_messaging` packages only
when `CCB_MOBILE_PUSH_ENABLED=true`; the default build neither initializes
Firebase nor registers an FCM token. Firebase auto-initialization is disabled
in the Android manifest, so a token is never generated before the paired
profile has opted in.

Firebase configuration is deployment-owned and is intentionally absent from
this repository: no `google-services.json`, generated `firebase_options.dart`,
service-account credential, or sender credential is committed. If private
Android configuration is absent or Firebase initialization fails, push stays
disabled for that process. Pairing, terminal, snapshots, and foreground UI
continue normally.

The client requests notification permission only after it has a paired host
with the existing `notify` scope. A denial is a normal result: it disables
push registration and does not affect foreground notification reconciliation.
Once allowed, the FCM token and every refresh are registered at
`PUT /v1/devices/me/push-token` with the bearer token from that exact paired
host. The gateway derives device identity exclusively from that bearer; it
never accepts a caller-supplied device identity. Re-pairing creates a new
binding; the app does not revoke or mutate an old binding automatically.

The registration protocol is deliberately small:

```json
{"token":"fcm-token"}
```

The gateway stores the FCM token in owner-only private state. Sender data
payloads are exactly `id`, `kind`, `project_id`, `project_short_name`,
`agent`, `completed_at`, `dedupe_key`, `host_id`, and `device_id`. The final
two fields bind the route to the paired profile selected by the gateway; they
must not include prompts, terminal output, paths, errors, credentials, or a
device token. For Android
background and terminated delivery, the deployment-owned FCM sender must wrap
those route fields in a real FCM notification+data message; data-only messages
are not accepted as production evidence for background user-visible delivery.
FCM is not an authorization channel: opening a route always uses the stored
paired profile and normal gateway authorization.

On a foreground/background notification click, the app first restores its
stored paired profile, records the push `dedupe_key` in the same seen store
used by the foreground SSE notification stream, and resumes the existing
cursor-based notification catch-up, then loads the requested project and
selects its agent. Invalid, unpaired, stale, or cross-profile routes stop at
the project list. Legacy identity-free push routes remain accepted only when
the stored profile is unambiguous. Handling a push never submits a prompt, replays
terminal input, retries a mutation, or writes project files. The notification
route is a view-selection request only.

Foreground FCM receipt does not write the persistent SSE dedupe store. It uses
a bounded in-memory trigger dedupe and asks the cursor stream to catch up; the
SSE event remains authoritative for unread markers, local notification policy,
and durable completion dedupe.

Only the device whose visible target exactly matches the event's project and
agent may be suppressed. Visibility is sent to the gateway as paired-device
presence; it is not a global notification acknowledgement and does not
suppress other devices. Push does not start or retain background SSE/polling.
The current foreground SSE remains a foreground reconciliation aid and is
stopped on backgrounding.

## Threat and dependency review

`firebase_messaging 16.4.1` (Firebase/FlutterFire, BSD-3-Clause) is the
official FCM Flutter client and brings `firebase_core`; `firebase_core
4.11.0` is declared directly so initialization is explicit. Versions are
pinned through `pubspec.lock`. Firebase's Flutter setup requires a
deployment-specific configuration file, while the FCM guide specifies
`getToken`, `onTokenRefresh`, and Android auto-init controls. Those facts are
why configuration and sender credentials stay outside source control and why
the app enables token generation only after paired opt-in.

Dependency audit note: pub.dev listed `firebase_messaging 16.4.2` and
`firebase_core 4.12.0` as current on 2026-07-14, but that pair failed this
project's compile gate because `firebase_messaging` could not resolve
`FirebasePlugin` / `pluginConstants`. The integration therefore keeps the
latest build-passing official FlutterFire pins above until the upstream package
pair is buildable with this Flutter SDK.

## Deployment configuration

Android Firebase configuration is injected at build time:

```bash
CCB_MOBILE_FIREBASE_ANDROID_CONFIG=/secure/operator/google-services.json \
  flutter build apk --debug --dart-define=CCB_MOBILE_PUSH_ENABLED=true
```

The source file must be deployment-owned and must match
`io.ccb.mobile.ccb_mobile`. Gradle copies it to the ignored
`android/app/google-services.json` only for the local build. If the variable is
absent and no ignored local file exists, the Google Services plugin is not
applied and Push remains fail-closed. Do not commit `google-services.json`,
`firebase_options.dart`, service-account JSON, OAuth tokens, signing secrets,
or release credentials.

The gateway FCM sender is enabled only from operator-owned credentials:

```bash
export CCB_MOBILE_FCM_PROJECT_ID=firebase-project-id
export CCB_MOBILE_FCM_CREDENTIALS_FILE=/secure/operator/fcm-service-account.json
# Or use Application Default Credentials:
# export GOOGLE_APPLICATION_CREDENTIALS=/secure/operator/application-default.json

ccb install mobile
```

Supported sender tuning is optional:

```bash
export CCB_MOBILE_FCM_TIMEOUT_SECONDS=2
export CCB_MOBILE_FCM_MAX_RETRIES=2
export CCB_MOBILE_FCM_MAX_WORKERS=4
export CCB_MOBILE_FCM_RETRY_BACKOFF_SECONDS=0.25
```

The sender uses Google's OAuth client libraries with the
`https://www.googleapis.com/auth/firebase.messaging` scope and sends FCM HTTP
v1 notification+data messages. It does not parse service-account JWTs itself.
If credentials, project id, or the optional `google-auth` runtime dependency
are missing, `ccb mobile serve` and `ccb install mobile` still start with
`push_sender.configured/ready` diagnostics set to false; ordinary pairing,
terminal, files, project view, and foreground SSE continue to work.

Diagnostics are intentionally low sensitivity. CLI output and
`GET /v1/mobile/push/audit` report provider, configured/ready state, worker
limits, counters, and broad failure reasons. They do not include FCM tokens,
credential paths, service-account contents, request bodies beyond the approved
route payload, or bearer tokens.

## Real-device acceptance

Production evidence requires the same APK SHA/signing certificate/version,
server-wide gateway audit, app logcat, and a dedicated real CCB test project.
With legal Firebase configuration and sender credentials present, validate:
foreground notification handling, Android HOME/background, lock screen,
process kill/relaunch, notification tap route selection, Push+SSE dedupe,
permission denial, invalid-token cleanup, multi-device isolation, and visible
target suppression.

If a legal Firebase Android app config, FCM sender credential, Google Play
emulator, or physical Android device is unavailable, real delivery remains an
external blocker. Fake senders and local notifications may cover code paths,
but they must not be reported as real FCM background or terminated delivery.

## Foreground service decision

No Android foreground service is implemented in this change. The app has no
single native owner for an active terminal or large transfer connection, so a
notification-only service would be misleading and would not make SSE/polling a
valid background delivery mechanism. A future service may be considered only
behind a feature flag after it owns a user-visible active terminal or transfer,
declares an Android-supported service type, has stop/cancel semantics, and is
covered by emulator/device tests. It must not be used for push, idle polling,
or mutation replay.
