# Task Completion Notification Lifecycle

Date: 2026-07-01
Status: Planning

## Problem

The P0 task-completion notification package landed the first OS notification
path, but the lifecycle is not yet complete. Reported behavior:

- after app install or first subscription, the phone immediately notifies many
  old completion events;
- later newly completed work may not notify;
- the app has no persistent in-app unread marker on the server-wide project
  list, project window switcher, or agent switcher;
- the project list does not show a project-level running indicator when an
  agent is actively working.

This topic refines [Decision 019](../decisions/019-app-lifetime-task-completion-notifications.md).
The reliability scope remains app-lifetime local notification only.

## Current Code Inventory

App-side notification code is concentrated in
`app/lib/notifications/task_completion_notifications.dart`.

Current behavior:

- `TaskCompletionNotificationController.start()` subscribes to
  `/v1/mobile/notifications`;
- every `task_completed` event is passed to `_handleEvent`;
- `_handleEvent` calls `TaskCompletionSeenDedupeStore.markSeenIfNew`;
- fresh events immediately show an OS notification if permission is granted;
- stream errors are swallowed and there is no explicit reconnect/on-done loop;
- there is no separate in-app unread store or baseline state.

Nearby UI:

- `ProjectHomeServerProjectListHost` renders server-wide project rows from
  `List<CcbProject>` only;
- `ProjectListTile` renders the currently opened project from
  `CcbProjectView`;
- `AgentSwitcher` and `WideAgentColumn` already draw a working border from
  `agentHasSourceWorkingActivity(agent)`;
- `WindowSwitcher` has no unread or working aggregation yet;
- `CcbAgent.activityState/activitySource/activityReason` is the app-side
  source for working/exception state, not conversation text.

## Required State Split

The fix must split three concepts that are currently easy to conflate:

1. OS notification dedupe.
   - Purpose: avoid repeated Android notifications for the same
     `dedupe_key`.
   - Storage: bounded persistent set, currently `seen_dedupe_keys`.
   - It must not decide whether a project has unread app-internal work.

2. Subscription baseline.
   - Purpose: mark retained/replayed old events as already known on first
     subscribe or reconnect.
   - Old retained events should be persisted as seen, but must not create OS
     notifications or unread stars.
   - Preferred source contract: retained events carry replay metadata or the
     stream sends a `stream_ready`/`snapshot_end` marker before live events.
   - App fallback if the source cannot be changed immediately: suppress events
     whose `completed_at` is clearly before the subscription start time, then
     migrate to explicit stream readiness for acceptance.

3. In-app unread completion state.
   - Purpose: show red star markers in the app until the user opens the
     corresponding agent conversation.
   - Key: at minimum `project_id + agent + dedupe_key`.
   - Window is derived from the current `CcbProjectView.agentByName(agent)` when
     the project is open; the notification payload may remain low-sensitive and
     does not need to include a window if the view can resolve it.
   - Clearing rule: opening/selecting the target agent conversation clears that
     agent's unread completion markers. Opening the project alone should not
     clear other agents.

## Event Lifecycle

Startup/subscription:

- load paired profile;
- request notification permission only after pairing/subscription as already
  decided;
- start the server-wide notification stream;
- consume retained replay as baseline: mark dedupe keys seen, do not notify,
  do not set unread;
- after source `stream_ready` or equivalent live boundary, transition to live
  mode.

Live completion:

- if event kind is not `task_completed`, ignore for this feature;
- if `dedupe_key` is already seen, ignore for OS notification and unread;
- mark the key seen;
- add/update unread state for `project_id/agent`;
- if app process is alive and permission is granted, show the OS notification
  when the app is backgrounded or outside the target conversation;
- if the target agent conversation is currently open, the unread marker may be
  cleared immediately after the event is applied, but the UI should not flash a
  stale red star.

Reconnect:

- if the stream errors or ends while a notify-scoped profile is active, restart
  with bounded backoff;
- retained replay after reconnect must not duplicate OS notifications because
  dedupe keys are already seen;
- new events created while disconnected should still be delivered if the source
  retention window covers them.

Tap/open:

- OS notification tap opens the target project/agent as today;
- opening/selecting the same target agent clears unread markers for that agent;
- if target project/agent no longer exists, fall back to project list and keep
  no invalid unread marker.

## UI Rules

Project list:

- show a small red star on a project row if any unread completion belongs to
  that `project_id`;
- show a colored running ring around the project avatar/card when any known
  agent in that project is actively working;
- do not use red alone as the only signal for running; reserve red for unread
  completion attention.

Project window switcher:

- show a red star on a window if it contains one or more unread agents;
- if the user is already inside that window, show the star on the specific
  agent chip instead of only the window chip.

Agent switcher:

- show a red star on an unread agent chip;
- keep the existing working border/color for actively running agents;
- unread and working can coexist: running border plus unread star.

Current agent conversation:

- selecting/opening the target agent conversation clears unread state for that
  agent after the selection is applied;
- clearing unread must not clear the OS dedupe store.

## Source/App Contract Needs

For a stable fix, the source notification stream should expose one of:

- `event: stream_ready` after retained replay, followed only by live events;
- a per-event replay/live flag, such as `replay: true`;
- a `since=now` or equivalent subscribe mode for clients that do not want
  retained old events.

The app should continue treating payload content as low-sensitive:

- keep: `id`, `kind`, `project_id`, `project_short_name`, `agent`,
  `completed_at`, `dedupe_key`;
- optional: `window` only if source can provide it without weakening privacy;
- forbid: prompt, reply, terminal output, file paths, provider transcript,
  error detail.

## Implementation Packages

Package A: notification stream lifecycle.

- add explicit baseline/live handling in `TaskCompletionNotificationController`;
- add stream reconnect/backoff while the paired notify profile is active;
- add tests for old retained events not notifying, live post-baseline event
  notifying, replay after reconnect not duplicating, stream end reconnect, and
  permission-denied consuming live events without OS notification.

Package B: app-internal unread completion state.

- add a small persistent unread completion store keyed by project/agent/dedupe;
- wire notification live events into project-home state;
- clear unread when target agent is selected/opened;
- add project, window, and agent badge widget tests.

Package C: project-level running indicator.

- use `CcbAgent.activityState` from loaded project views for opened projects;
- if server-wide project rows need running status without opening every
  project, add a source-side low-cost project summary field rather than
  parsing conversation or pane text;
- add focused widget tests for running ring and for running+unread coexistence.

## Acceptance

Real Android Emulator acceptance must use the server-wide gateway and a
dedicated test project/worktree.

Required proof:

1. Fresh install/subscription with retained old completion events creates no
   OS notifications and no unread red stars for old events.
2. A later live completion creates exactly one OS notification.
3. Restart/reconnect does not re-notify the same `dedupe_key`.
4. A later live completion after reconnect still notifies.
5. Project list shows a red star on the project with unread completion.
6. Project window/agent switchers show unread at the correct granularity.
7. Opening the target agent conversation clears only that agent's unread marker.
8. Running agents create a project-level running ring and agent-level working
   border without being mistaken for unread.
9. Notification payload/log evidence remains low-sensitive.

## Open Questions

- Should foreground app use OS notifications, or only app-internal markers,
  when the user is not currently inside the target agent conversation?
- Should an event for the currently visible agent clear immediately, or briefly
  show a marker until the next user interaction?
- Can the source stream add an explicit `stream_ready` marker, or does the
  first fix need an app-only completed-at baseline fallback?
- Does the server-wide project list already have or need a low-cost activity
  summary so running rings can work for unopened projects?
