# Mobile UX Flows

Date: 2026-06-17
Status: Draft

## Design Bias

The mobile UI should feel like a CCB-aware remote control for server-side CCB
projects, not a marketing app, not a generic SSH launcher, not a tmux-first
terminal clone, and not an independent mobile agent runtime.

The primary job is to answer:

- Can I open a server-side CCB project from phone/iPad?
- Can I switch CCB projects, windows, and agents quickly?
- Can I see exactly one selected agent clearly?
- Can I read and continue the selected agent conversation like a mobile chat?
- Can I keep a short list of common projects and wake/close them remotely?
- Which CCB projects are alive?
- Which agents need attention?
- What is each agent doing?
- Did my agent finish, fail, block, or ask for a callback?
- Can I read Comms/Markdown context without parsing a terminal stream?
- Can I enter raw terminal mode when I explicitly need pane-level control?

## Home

Default home: project-centric list grouped by host.

Each project row should show:

- favorite/pinned state;
- project display name;
- root path or short path;
- host name;
- health: online, starting, degraded, offline, stale;
- lifecycle: stopped, starting, running, stopping, failed, unknown;
- active agent count;
- waiting callback count;
- unread or unresolved Comms count;
- last completion/attention event;
- last activity time;
- quick action to wake/open or close/stop project.

Host health should be visible but not dominate the main workflow unless the
user has many hosts.

## Project Lifecycle Flow

Frequent projects should be one tap away:

1. User pins a project from the project list or current project view.
2. Home shows the pinned project with lifecycle and health.
3. If stopped, the primary action is wake/open.
4. If running, the primary action is open the project workspace.
5. Stop/close actions are available but separated:
   close mobile view is lightweight; stop project uses CCB shutdown behavior.
6. Lifecycle changes produce notifications and update the row state.

## Project Remote View

Opening a project should land in an agent-first workspace, not a terminal
stream or a status dashboard. The first viewport should prioritize an agent
switcher, one selected agent, a conversation timeline, and a persistent
composer:

- top window/agent switcher: a compact window row scopes the agent row below
  it, so CCB windows behave as task/workspace groups rather than connection
  details;
- agent switcher: configured agents for the selected window with compact
  state, callback, and attention indicators;
- main body: exactly one selected agent chat timeline with user messages,
  agent replies, callbacks, Comms, Markdown/content, status events, and
  readable terminal-history evidence where useful;
- bottom composer: multiline input, send action, pending/sent/failed state,
  retry, and per-agent draft preservation;
- project and route details: project path, runtime id, gateway URL, pairing,
  namespace/epoch diagnostics, and route health behind a details affordance;
- explicit terminal action: Open Terminal enters raw terminal control mode for
  the selected agent/window;
- diagnostics/details: pairing, route health, lifecycle, runtime id, and other
  technical state stay behind the Diagnostics affordance; windows should not
  be listed there as connection configuration;
- actions: ask, focus, refresh, restart agent, reload config, admin menu.

Agent taps should switch the selected agent first. Focus requests and terminal
entry should be visible explicit actions, followed by ProjectView refresh to
confirm the active CCB state.

Mobile interaction polish recorded 2026-06-30:

- the full agent list should not be revealed by an upward swipe from the
  conversation. Use an explicit pull-out/drawer button, and leave vertical
  drags/overscroll to timeline scrolling and refresh behavior;
- expanding a collapsed conversation bubble must not make "scroll to bottom"
  unstable or snap the viewport back to the top. Treat this as a gesture,
  scroll-controller, and refresh/rebuild stability regression, especially if
  the current agent-list reveal gesture competes with the timeline;
- pane-backed task completion should be eligible for a phone reminder no
  matter which project is currently open. The app already has in-app
  ProjectView-derived notification models; system-level or cross-project
  delivery still needs a concrete event source and permission/background
  strategy.

User feedback backlog recorded 2026-06-30:

1. Agent list reveal should be explicit: remove upward-swipe reveal from the
   conversation area and open the list through a pull-out/drawer button.
2. Expanded conversation bubbles must keep bottom scrolling stable and must not
   snap back to the top after expansion.
3. Pane-backed task completion should be able to notify the phone across all
   paired projects, not only the currently open project.
4. Remote files, artifacts, and attachments need a long-press action sheet with
   Download and Open; Open should use a confirmed external-app handoff after
   downloading or reusing a local cached copy.
5. URLs in readable app content should be openable through the OS browser/app
   chooser after confirmation; local host paths stay blocked unless resolved by
   the gateway into validated CCB content.
6. App install/upgrade continuity needs fixing: the app should support in-app
   upgrade eventually, or at minimum a newly supplied APK should install over
   the existing app without signature conflict or forced uninstall.

Implementation evidence recorded 2026-06-30:

- Real emulator validation used `emulator-5554`, server-wide gateway
  `http://127.0.0.1:8791`, and the dedicated real project
  `test_ccb2 / main3 / agy1`.
- Evidence is under
  `/tmp/ccb-mobile-real-project-emulator-download-review/`, including
  `current-screen.png`, `test-ccb2-screen.png`,
  `attachment-selected-current.png`, `upload-after-send-current.png`,
  `attachment-longpress-current.png`,
  `open-attachment-confirm-current.png`, and
  `open-attachment-after-confirm.png`.
- The app listed real server-wide projects, selected a file through Android
  DocumentsUI, sent `ccb-mobile-upload-smoke.txt` through the live project
  path, rendered the uploaded attachment in the conversation, showed the
  long-press `Download attachment` / `Open attachment` action sheet, confirmed
  before opening, and reached the Android `Open with` chooser.
- URL opening has widget coverage and a confirmation UI, but the same real
  emulator pass did not produce a reliable coordinate-based URL confirmation
  screenshot. Treat URL external-open as needing one more targeted real-device
  evidence pass or a more explicit URL action affordance.
- OS-level task completion notification is not implemented yet. Current
  completion feedback is in-app status/snackbar only. The next coherent package
  is an app-lifetime local notification layer with Android 13+
  `POST_NOTIFICATIONS` handling, deduplication by project/agent/completion
  event, terse completion copy, default platform notification behavior, and
  notification payloads that deep-link back to the project/agent.
  Cross-project or killed-app background delivery remains a larger follow-up.

## Agent Detail

Agent detail is the main conversation and control surface for one selected
agent:

- agent name and provider;
- current state and last activity;
- completion state and last finished/failed/blocked event;
- current queue or task summary when available;
- chat timeline with user asks, agent replies, callback prompts, Comms,
  status events, and artifact cards;
- persistent composer;
- Markdown-rendered request/reply content inside timeline cards;
- focus action and explicit open-terminal action for that agent pane.

The agent workspace is the default compact pane-backed chat surface. Composer
and Markdown views should cover normal mobile usage. Raw terminal mode remains
available for full pane-level control, debugging, special keys, mouse/viewport
operations, and operations that are not comfortable in the compact chat shell.

## Ask And Callback Flow

Suggested flow:

1. User opens project.
2. User taps an agent in the top switcher.
3. The selected-agent timeline and composer are already visible.
4. User types a multiline message and sends it.
5. Mobile shows pending, queued/sent, and failed/retry states in the timeline.
6. Gateway writes the text to the selected agent's CCB-validated tmux pane
   through terminal paste/input frames.
7. If callback is required, notification and Comms detail deep-link back to the
   same thread.

This keeps the user's mobile input aligned with the real provider CLI pane
while letting the app render the pane interaction as a readable chat surface.

## Markdown Reading Flow

Markdown should be the default display mode for CCB-authored and
agent-authored content:

1. User opens a Comms item, ask result, callback, or artifact-backed message.
2. Mobile shows a clean Markdown reading view.
3. Code blocks have copy buttons and wrap/scroll controls.
4. Tables can switch between fitted, horizontal scroll, and card/list mode.
5. Long sections can collapse without losing the raw text.
6. A raw source toggle remains available for debugging or copy fidelity.
7. Long-pressing a remote file, artifact, or attachment opens an action sheet
   with at least Download and Open. Download saves the file through the
   authenticated gateway path; Open downloads to app storage if needed and then
   hands the local file to the OS/app chooser. The app should confirm once
   before opening remote content in another app.
8. Web URLs in Markdown, terminal-derived readable content, Comms, and
   artifacts should be openable through the system browser or app chooser after
   a one-time confirmation. Local host paths remain blocked unless the gateway
   resolves them into validated CCB content/artifact references.

Pane snapshots stay terminal output, not Markdown. If a provider's latest reply
is available through CCB message/session evidence, mobile should prefer that
structured content over trying to infer Markdown from captured terminal text.

## Pane Snapshot Flow

Pane snapshots evolve into a readable terminal history flow for the selected
agent. This is still a fallback/observability surface, not the authoritative
Markdown reply source.

Suggested flow:

1. User taps an agent.
2. The selected-agent workspace shows a vertically scrollable readable history
   block or timeline section built from the current pane plus retained tmux
   scrollback.
3. Pull-to-refresh or periodic refresh appends/reconciles newer output without
   jumping away from the user's current scroll position.
4. Snapshot header shows agent/window, freshness, alive/dead, and stale-view
   warnings.
5. If stale, the UI asks the user to refresh ProjectView instead of sending
   input to old pane evidence.

Readable history mode should support copy text, copy block, collapse repeated
logs, wrap/scroll code, diff highlighting, and "open raw terminal" as a
deliberate upgrade path.

Readable history may detect Markdown-looking output for convenience, but it
should not become the authoritative reply view. The authoritative Markdown view
should come from CCB message/reply/artifact content when available.

The MVP can only show current tmux scrollback. A later terminal journal should
record output as it happens if the product needs complete project-lifetime
history beyond tmux `history-limit`.

## Interactive Terminal Flow

Interactive terminal is an explicit raw-control flow:

1. User opens a project from the project list.
2. User selects one agent or window in the agent-first workspace.
3. User taps Open Terminal.
4. Gateway resolves project id to current CCB tmux socket/session facts.
5. Terminal opens with special key controls and paste composer.
6. Side/bottom sheet shows target identity: project, window, agent, current
   pane evidence.
7. If stale target evidence is detected, input locks until refresh.
8. Closing terminal returns to the selected agent workspace and does not affect project
   lifecycle.

Phone terminal controls should include:

- Esc, Tab, Ctrl, Alt modifier toggles;
- arrows and function keys;
- paste as block;
- font size;
- reconnect status;
- read-only/input lock indicator;
- explicit close.

## Notifications

Useful notification classes:

- task completed;
- task failed, incomplete, or cancelled;
- callback waiting;
- direct Comms mention;
- agent unhealthy or pane missing;
- project backend offline;
- project wake/stop result;
- raw terminal session disconnected.

Notifications should deep-link by project id plus agent/window/Comms id. They
should not deep-link by pane id alone.

Completion reminders should cover all paired projects, not only the current
project page. If CCB/tmux already emits a reliable task-complete signal, the
mobile layer should subscribe or poll through the gateway and translate it into
deduplicated in-app and OS-level phone notifications.

P0 system task-complete notification design recorded 2026-06-30:

- scope is task completion only, not every activity/status update;
- trigger on an authoritative project/agent transition from working/running to
  completed/done for a pane-backed task;
- notification copy is terse and low sensitivity:
  `<project short name> / <agent> task completed`, with the same shape in
  localized UI strings;
- do not include prompts, replies, task details, file paths, terminal output,
  provider text, or exception detail;
- use the platform default notification channel behavior, including the
  system/default sound and vibration; do not design or bundle custom sounds in
  P0;
- deduplicate by project id, agent name, and stable completion event id or
  state-transition marker so refresh/resume does not repeat old notifications;
- tapping the notification opens the target project and selected agent when
  possible; if the app cannot resolve the target, open the project list;
- require notification permission and keep a later settings toggle available
  for users who want to disable completion reminders.

App engineering review recorded 2026-06-30:

- P0 is an app-lifetime local notification path. It can notify while the app
  process and notification subscription are alive, including ordinary
  background after the user presses Home, but it does not guarantee delivery
  after force-stop, killed-app state, or deep Doze. Reliable killed-app
  delivery would require a separate push or foreground-service design.
- Android should request `POST_NOTIFICATIONS` only after a useful user moment,
  such as first successful gateway pairing or first notification subscription,
  not during cold start. If permission is denied, keep app-internal completion
  state without posting an OS notification.
- A fixed Android channel such as `ccb_task_completion` should use platform
  default behavior. Start with default importance unless real validation shows
  that the completion reminder must be more prominent; do not ship custom
  audio assets.
- Suggested rendering is title `CCB Mobile` and body
  `<project_short_name> / <agent> task completed`, localized with the same
  low-sensitive shape such as `<project_short_name> / <agent> 任务完成`.
- Real validation must put the app in ordinary background, trigger a task
  completion from a dedicated test project through the server-wide gateway,
  confirm the notification, tap it back to the project/agent, and prove
  duplicate refresh/resume events do not repost the same completion.

Lead decision recorded in
[Decision 019](../decisions/019-app-lifetime-task-completion-notifications.md):

- P0 accepts app-lifetime local notifications and explicitly defers FCM/APNs,
  foreground services, and WorkManager/background polling.
- The app-facing source is a server-wide dedicated gateway notification stream;
  ProjectView deltas are only a foreground/current-project fallback.
- Every paired phone/client may notify for the same completion in P0. Do not add
  active-device suppression or `device_active_hint` yet.
- `notify` is part of the ordinary paired-device profile. Old profiles without
  it should degrade cleanly or ask the user to re-pair for notifications.
- The remaining source dependency is a stable CCB/tmux completion marker and
  source-generated `dedupe_key`.

## Multi-Agent Views

For CCB, a phone-specific "agent board" is more useful than a pane grid:

- rows are configured agents;
- columns or chips show provider, window, activity, queue, callback, and health;
- completion markers show done, failed, blocked, or waiting for user;
- one-tap focus changes the desktop tmux view through `ccbd`;
- one-tap ask opens composer;
- terminal snapshot is secondary detail.

This is the main product difference from generic tmux clients.

## Mobile Constraints

Avoid mobile layouts that require reading four panes side by side. Prefer:

- list-first navigation;
- one selected agent/window at a time;
- dense rows with status chips;
- terminal snapshot as scrollable content;
- raw terminal as full-screen mode;
- admin actions behind menus and confirmations.

## MVP Screens

Minimum screens:

1. Pairing screen.
2. Project list.
3. Project agent workspace with top agent switcher, selected-agent timeline,
   and persistent composer.
4. Explicit raw terminal mode for selected agent/window.
5. Project lifecycle confirmation sheet.
6. Markdown content detail for Comms, replies, formulas, and artifacts.
7. Comms/callback detail.
8. Notification center.
9. Settings/devices screen for permissions and revocation.

## Anti-Patterns

Avoid:

- starting from SSH host/session lists;
- showing every tmux pane as equal to a CCB agent;
- making raw terminal the default project page;
- making agent taps open terminal instead of switching selected agent;
- letting project path, gateway URL, pairing code, runtime id, or diagnostics
  consume the first viewport;
- exposing destructive tmux commands in the normal UI;
- depending on pane ids in deep links;
- treating captured terminal text as the only readable answer source;
- making the input composer a hidden secondary action instead of the default
  selected-agent control;
- sending normal user messages by typing into a provider/tmux pane;
- hiding stale namespace warnings.
