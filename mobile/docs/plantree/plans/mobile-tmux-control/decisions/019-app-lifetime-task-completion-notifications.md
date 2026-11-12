# Decision 019: App-Lifetime Task Completion Notifications

Date: 2026-06-30
Status: Accepted for the P0 system task-completion notification package

## Context

The user wants CCB Mobile to show a phone system notification when a
pane-backed agent task completes, regardless of which paired project is
currently open in the app. The notification should be low-sensitive and contain
only the project short name, agent name, and completion text. It must not
include prompt text, replies, terminal output, file paths, provider details, or
error detail. The notification should use the platform default sound and
vibration behavior, not custom notification audio.

The implementation has two possible reliability levels:

- an app-lifetime local notification layer that works while the app process and
  gateway notification subscription are alive, including ordinary background;
- a push or foreground-service architecture that targets killed-app, force-stop,
  or deep-Doze delivery.

The second path would add device tokens, cloud push or foreground-service
policy, battery compliance, and a wider privacy surface, so it is too broad for
the first package.

## Decision

P0 accepts app-lifetime local notifications only:

- foreground and ordinary background delivery are in scope while the app process
  and gateway subscription are alive;
- force-stop, killed-app state, deep Doze, FCM, APNs, foreground service, and
  WorkManager-style background polling are out of scope for P0.

The P0 app-facing contract is a server-wide gateway notification stream:

- implement `mobile_notifications_subscribe` as SSE or an equivalent
  long-lived stream;
- keep `GET /v1/notifications` available only for reconnect/catch-up if needed;
- do not use ProjectView deltas as the primary cross-project notification
  source;
- ProjectView deltas may remain a foreground/current-project fallback.

The source side must generate a low-sensitive task completion event and a stable
`dedupe_key`. The app must not infer completion or dedupe from notification
copy, terminal text, or time windows. The recommended source-generated key shape
is:

```text
project_id + namespace_epoch + agent + completion_sequence_or_activity_transition_id
```

The exact completion marker remains a source-side spike:

- Codex should first use the enhanced provider/agent activity state and emit a
  completion event from a stable `working -> idle/completed/exception`
  transition.
- Claude and generic tmux providers should use the unified CCB agent activity
  model where possible.
- If a provider does not expose a clear completion signal, P0 may cover Codex
  plus the generic idle transition and mark other providers best-effort.
- The source spike must define completion event generation, sequence stability,
  and whether recent events can be replayed after restart.

P0 notifies all paired phones/clients:

- do not suppress phone notifications because a desktop or another mobile
  client is active;
- do not introduce `device_active_hint` or active-client suppression in P0;
- each client performs local bounded dedupe so one device does not repeat the
  same completion notification.

The ordinary paired-device profile includes the `notify` scope by default. Old
profiles without `notify` should degrade cleanly, such as by showing
"re-pair to enable notifications" or silently omitting OS notifications. Do not
reuse `view`, `content`, or `terminal-input` as implicit notification scopes.

## Implementation Packages

Source package: server-wide mobile notification stream.

- owns `/v1/mobile/notifications` or the equivalent
  `mobile_notifications_subscribe` gateway stream;
- generates completion events and `dedupe_key`;
- enforces `notify` scope;
- fans out low-sensitive events to multiple paired clients;
- proves event generation, dedupe stability, scope denial, multi-project stream
  behavior, and absence of prompt/output/path leakage.

App package: local notification subscriber.

- subscribes to the server-wide notification stream;
- creates the Android `ccb_task_completion` notification channel;
- requests Android 13+ `POST_NOTIFICATIONS` after pairing or subscription, not
  at cold start;
- uses platform default channel sound/vibration;
- persists a bounded `seenDedupeKeys` set;
- derives a stable Android integer notification id from `dedupe_key`;
- routes notification taps to the target project/agent, falling back to the
  project list if the target cannot be resolved.

## Validation

Real Android Emulator acceptance must use the server-wide gateway and a
dedicated test project, not fake/demo mode and not `ccb_mobile` or other active
user projects.

Required evidence:

1. App foreground receives a completion event and posts one OS notification.
2. App backgrounded with Home, but not killed, receives a completion event and
   posts one OS notification.
3. Notification body contains only `<project_short_name> / <agent> task
   completed` or the localized equivalent.
4. Notification channel is `ccb_task_completion` and uses platform default
   sound/vibration behavior.
5. Replaying the same `dedupe_key` does not create duplicate notifications.
6. Tapping the notification opens the target project/agent; missing targets
   fall back to the project list.
7. Android 13+ notification permission denial does not crash and degrades to no
   OS notification.
8. Logs and captured event JSON prove the payload does not contain prompt,
   reply, path, terminal output, provider transcript, or error detail.

## Consequences

- P0 is useful for ordinary app-background use without expanding into push
  infrastructure.
- Users should not expect completion notifications after force-stop, process
  kill, or deep battery restriction until a later push/foreground-service design
  exists.
- The source completion marker is now the main remaining technical dependency
  before the app package can be fully validated.
