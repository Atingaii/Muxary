# App Architecture Refactor Plan

Date: 2026-06-22
Status: In Progress

## Purpose

Define a low-risk architecture cleanup path for the Flutter app after the
pane-backed chat direction landed. The immediate goal is not a visual redesign
or transport rewrite. The goal is to break the current mobile app giant files
into stable feature and controller boundaries so future chat, terminal,
diagnostics, relay, and iPad work can continue without repeatedly editing the
same 4k-line file.

## Progress

- 2026-06-22: A1 started. Gateway dependency factory typedefs/defaults moved
  from `main.dart` to `app/app_factories.dart`, runtime mode moved to
  `app/runtime_mode.dart`, and `ccb_mobile.dart` now exports both app-level
  modules. `CcbMobileApp` and `ProjectHomeScreen` remain in `main.dart` for
  the next A1 slice so behavior and test harnesses stay stable.
- 2026-06-22: A1 completed. `main.dart` is now a 10-line entrypoint plus
  compatibility exports, `CcbMobileApp` lives in `app/ccb_mobile_app.dart`,
  and the public `ProjectHomeScreen` wrapper plus existing project shell moved
  to `features/project_home/project_home_screen.dart`. The move preserves the
  existing UI behavior and keeps `package:ccb_mobile/main.dart` imports
  compatible for current integration tests.
- 2026-06-22: A3 started. `PaneChatController` now owns selected-agent
  terminal session reuse, paste-plus-Enter sends, output subscriptions,
  stream-error notice events, and close/dispose behavior. The
  `SelectedAgentWorkspace` still owns message ids, local message state,
  scrolling, and sent/failed transitions, so this is a controller extraction
  rather than a UI behavior change.
- 2026-06-22: A3 controller hardening started. `PaneChatController` now
  suppresses only exact terminal echoes, clears pending echo suppression after
  the first different output to avoid stale false positives, and drops broken
  sessions after stream error/done so the next send opens a fresh terminal
  session.
- 2026-06-22: A3 behavior stabilization continued before the next widget
  extraction. Pane-backed selected-agent sends now refresh readable
  `/terminal-history` after successful paste-plus-Enter, user sends always
  scroll to the sent message, and live `tmux output / live` frames are
  ANSI-stripped, capped, and merged into one compact bubble so real emulator
  chat does not get flooded by raw terminal frames. The AVD integration helper
  now prefers onstage taps and emits chat diagnostics on timeout.
- 2026-06-22: A3 leaf extraction resumed after the behavior stabilization
  passed emulator smoke. `AgentMessageComposer` moved to
  `features/agent_chat/agent_message_composer.dart`, and live terminal output
  compaction/merge behavior moved to
  `features/agent_chat/live_terminal_output.dart` with direct unit coverage.
  `project_home_screen.dart` is still the main risk, but it no longer owns
  those leaf agent-chat concerns.
- 2026-06-22: A3 retry behavior stabilization completed for partial pane
  sends. `PaneChatController` now reports send failure stage and whether input
  may have reached the pane; the chat UI maps possible partial input to a
  `Check pane` delivery state without a blind Retry action. This keeps retry
  semantics in the controller/chat boundary before timeline and bubble widgets
  move out of `project_home`.
- 2026-06-22: A3 chat presentation extraction continued. Decision 016 freezes
  the current compact composer primitive as terminal paste plus Enter for this
  refactor package, and `ConversationBubble`/conversation presentation helpers
  moved to `features/agent_chat/`. `project_home_screen.dart` still owns the
  selected-agent workspace, timeline assembly, content reader, and readable
  history panel, but no longer owns bubble, preview, Markdown/plain rendering
  selection, state-chip labels, or terminal-derived presentation helpers.
- 2026-06-22: A3 timeline/content/history extraction continued. Conversation
  timeline virtualization, structured content reading, readable terminal
  history loading/panel rendering, terminal-history presentation labels, and
  terminal-history-to-chat item mapping now live under `features/agent_chat/`.
  Shared copy snackbar feedback is isolated in `clipboard_feedback.dart`, so
  content and history widgets do not depend on each other.
  `project_home_screen.dart` still owns selected-agent workspace state,
  draft/scroll maps, local optimistic messages, pane-chat submission, and
  project/connection shell concerns, but no longer owns the selected-agent
  timeline widget or content/history leaf rendering.
- 2026-06-22: A3 workspace extraction moved the selected-agent workspace
  boundary itself to `features/agent_chat/selected_agent_workspace.dart`.
  `project_home_screen.dart` now mounts that feature entrypoint instead of
  owning selected-agent draft/scroll/local-message/pane-chat state directly.
  This is an intermediate split: `selected_agent_workspace.dart` is still over
  the feature-file budget and should be split next into a smaller widget plus
  `AgentChatController`/state helpers.
- 2026-06-22: A3 state-helper extraction started that follow-up split.
  Conversation signatures, stale namespace epoch detection, pane partial-send
  delivery mapping, and local optimistic-message pruning now live in
  `features/agent_chat/agent_chat_state_helpers.dart` with direct unit
  coverage. `selected_agent_workspace.dart` is down to about 843 lines, but it
  still owns controller-like draft, loading, scroll, and local-message maps.
- 2026-06-22: A3 controller extraction continued. `AgentChatController` now
  owns selected-agent local optimistic messages, remote conversations,
  refreshed terminal history cache, conversation errors, expanded item ids,
  loading/submitting flags, collapsed composer state, new-message flags, and
  local message ids. `SelectedAgentWorkspace` is down to about 762 lines and
  now primarily owns Flutter `TextEditingController`/`ScrollController`
  lifecycle, repository/pane side effects, timer scheduling, and widget
  assembly.
- 2026-06-22: A3 timeline assembly extraction continued the widget-shell
  split. `agent_chat_timeline_items.dart` now owns selected-agent timeline
  item ordering across remote conversations, terminal-history foreground
  evidence, ProjectView/content fallback, refresh errors, and local optimistic
  messages. `SelectedAgentWorkspace` is down to about 741 lines; the remaining
  high-risk responsibility is repository/pane side effects plus Flutter
  controller lifecycle.
- 2026-06-22: A3 repository-side-effect extraction continued.
  `AgentConversationLoader` now owns selected-agent conversation fetch,
  stale namespace epoch fail-closed handling, and one optional ProjectView
  refresh before retrying the fetch. `AgentTerminalHistoryLoader` now owns
  post-pane-send readable terminal-history refresh and keeps missing/failed
  history as supplemental evidence instead of a send failure.
  `SelectedAgentWorkspace` is down to about 707 lines; remaining high-risk
  responsibilities are pane-send/repository-submit side effects, scheduled
  post-submit refresh timers, live output item creation, and Flutter
  controller lifecycle.
- 2026-06-22: A3 repository-submit extraction continued.
  `AgentRepositoryMessageSubmitter` now owns the compatibility repository
  message submit path used when no terminal transport is injected. It maps
  namespace-missing, stale namespace epoch refresh/retry, remote conversation
  responses, replacement message responses, and failed submit errors into a
  small UI outcome object. `SelectedAgentWorkspace` is down to about 674
  lines and no longer calls `submitAgentMessage` directly. Remaining
  workspace responsibilities are pane-backed terminal send orchestration,
  scheduled post-submit refresh timers, live output item creation, Flutter
  text/scroll controller lifecycle, and widget assembly.
- 2026-06-22: A3 pane-submit extraction continued.
  `AgentPaneMessageSubmitter` now owns the pane-backed terminal send path,
  terminal transport readiness mapping, stale namespace epoch refresh/retry
  before pane input reaches the terminal, partial-input `Check pane` mapping,
  `PaneChatController` session lifecycle, and pane event subscription. It
  returns a small UI outcome so `SelectedAgentWorkspace` can update the local
  message and refresh terminal history without owning terminal send mechanics.
  `SelectedAgentWorkspace` is down to about 626 lines; remaining
  responsibilities are scheduled refresh timers, live output item creation,
  Flutter text/scroll controller lifecycle, and widget assembly.
- 2026-06-22: A3 live-output item extraction continued.
  `pane_chat_event_messages.dart` now owns conversion from `PaneChatEvent` to
  local conversation messages, including compact live tmux output bubbles,
  consecutive live-output merge behavior, terminal stream notices, and the
  "blank output does not consume ids" rule. `SelectedAgentWorkspace` is down
  to about 583 lines and no longer owns live output/notice bubble construction.
  Remaining responsibilities are scheduled refresh timers, Flutter text/scroll
  controller lifecycle, and widget assembly.
- 2026-06-22: A3 timer lifecycle extraction continued.
  `conversation_refresh_scheduler.dart` now owns the delayed post-submit
  conversation refresh schedule, current-agent activity guard, timer creation,
  and cancel-all lifecycle with direct fake-timer tests.
  `SelectedAgentWorkspace` is down to about 573 lines and no longer owns raw
  `Timer` bookkeeping. Remaining responsibilities are Flutter text/scroll
  controller lifecycle and widget assembly.
- 2026-06-22: A3 Flutter controller lifecycle extraction continued.
  `agent_chat_ui_controller_store.dart` now owns per-agent
  `TextEditingController` and `ScrollController` lifetimes, the initial
  timeline scroll offset, near-end detection, and post-frame jump-to-latest
  retries with direct widget coverage. `SelectedAgentWorkspace` is down to
  about 549 lines and no longer owns draft/scroll controller maps or disposal.
  Remaining responsibility is widget assembly around the side-effect
  coordinator.
- 2026-06-22: A3 selected-agent view extraction continued.
  `selected_agent_workspace_view.dart` now owns the no-agent state and the
  selected-agent timeline/composer widget assembly, preserving existing keys
  and callbacks. `SelectedAgentWorkspace` is down to about 515 lines and now
  primarily coordinates repository/pane side effects, controller state, and
  view-model assembly for the extracted view.
- 2026-06-22: A3 selected-agent view-model extraction continued.
  `selected_agent_workspace_model.dart` now owns selected-agent content,
  readable terminal history, remote conversation, refresh error, local
  optimistic message, loading, unread, submitting, expansion, and composer
  collapse assembly for the extracted view. `SelectedAgentWorkspace` is down
  to about 485 lines and now mainly coordinates submit/load/refresh side
  effects around `AgentChatController`.
- 2026-06-22: A3 conversation-refresh side-effect extraction continued.
  `agent_conversation_refresh_coordinator.dart` now owns selected-agent
  conversation loading state, repository loader invocation, stale-refresh
  loader reuse, remote conversation application, conversation error capture,
  new-message flag behavior, and scroll-to-latest decisions.
  `SelectedAgentWorkspace` is down to about 457 lines; remaining side effects
  are submit/retry orchestration, pane-send replacement handling, terminal
  history refresh application, and pane live-event application.
- 2026-06-22: A3 pane live-event side-effect extraction continued.
  `agent_pane_event_coordinator.dart` now owns applying pane output/notice
  events to local conversation messages, new-message flag behavior, and
  scroll-to-latest decisions. `SelectedAgentWorkspace` is down to about 446
  lines; remaining side effects are submit/retry orchestration, pane-send
  replacement handling, and terminal-history refresh application.
- 2026-06-22: A3 terminal-history refresh side-effect extraction continued.
  `agent_terminal_history_refresh_coordinator.dart` now owns the post-pane-send
  readable terminal-history refresh, refreshed-history controller update,
  new-message flag behavior, and scroll-to-latest decision. `SelectedAgentWorkspace`
  stays about 446 lines because the new coordinator field offsets the removed
  method body, but remaining side effects are narrowed to submit/retry
  orchestration and pane-send replacement handling.
- 2026-06-22: A3 message-submit side-effect extraction continued.
  `agent_message_submit_coordinator.dart` now owns selected-agent send and
  retry orchestration, optimistic local message insertion, repository outcome
  application, pane-send replacement handling, post-send conversation refresh
  scheduling, and post-pane terminal-history refresh triggering.
  `SelectedAgentWorkspace` is down to about 306 lines and now mainly wires
  lifecycle callbacks, selected-agent conversation refresh, pane live events,
  terminal-history refresh, and the extracted workspace view.
- 2026-06-22: A3 widget-test support extraction started.
  `test/support/project_home_test_fakes.dart` now owns reusable project-home
  widget-test fakes: recording gateway repository, recording terminal
  transport/session, controlled/stale/Markdown/long-conversation repositories,
  demo ProjectView payload builders, rendered-text finder, and in-memory secure
  store. `widget_test.dart` is down to about 1522 lines, but it still owns all
  scenario bodies plus interaction helpers and remains above the architecture
  budget.
- 2026-06-22: A3 widget-test interaction-helper extraction continued.
  `test/support/project_home_test_driver.dart` now owns reusable project-home
  widget interaction helpers for opening the project/connection surfaces,
  activating stored paired profiles, setting test viewport/insets, selecting
  agent/window assertions, expanding tiles, tapping visible controls, and
  dragging virtualized timelines. `widget_test.dart` is down to about 1368
  lines; remaining test risk is now the concentration of all project-home
  scenario bodies in one file.
- 2026-06-22: A3/A5 widget-test scenario split started.
  `test/project_home_layout_widget_test.dart` now owns project-home first
  render, wide project/agent sidebars, phone agent switcher collapse, composer
  collapse with keyboard insets, and wide two-detent sidebar drag scenarios.
  `widget_test.dart` is down to about 1092 lines; remaining split candidates
  are chat timeline/composer scenarios, notifications, connection lifecycle,
  paired-gateway/terminal paths, and route diagnostics.
- 2026-06-22: A3/A5 widget-test scenario split reached the current budget
  target. `test/agent_chat_history_widget_test.dart` now owns readable
  terminal-history, tmux-history bubble, long-history virtualization,
  scroll-to-latest, and pane-output while reading older history coverage.
  `test/agent_chat_composer_widget_test.dart` now owns selected-agent terminal
  open, draft, pending/sent/failed/retry, markdown rendering, partial-pane
  `Check pane`, and stale-epoch retry coverage. `widget_test.dart` is down to
  about 493 lines; all project-home widget scenario/support files are now
  under the 500-line budget.
- 2026-06-22: A3 project-home shell extraction resumed.
  `features/project_home/project_lifecycle_panel.dart`,
  `features/project_home/gateway_pairing_panel.dart`, and
  `features/project_home/runtime_mode_panel.dart` now own lifecycle controls,
  gateway-pairing controls, runtime/profile selection, route diagnostics
  display, and shared gateway profile key/label helpers. `project_home_screen.dart`
  is down to about 2088 lines; next leaf candidates are project list, wide
  sidebars, project chat header, notification sheet, and the connection details
  wrapper before tackling profile/pairing orchestration state.
- 2026-06-22: A3 project-home shell leaf extraction continued.
  `features/project_home/notification_center_sheet.dart` now owns notification
  list rendering, severity/kind icons, target labels, and the notification-open
  message helper. `project_home_screen.dart` is down to about 1973 lines and
  still owns notification target selection side effects plus the remaining
  project list, wide sidebar, project chat header, connection details wrapper,
  and profile/pairing orchestration regions.
- 2026-06-22: A3 project-home shell widget extraction continued.
  The phone project list, wide project/agent columns, collapsed sidebar rail,
  two-detent drag handle, project chat header, mobile window/agent switcher,
  and shared ProjectView window/agent selection helpers now live in small
  `features/project_home/` leaves exported by `project_shell_widgets.dart`.
  `project_home_screen.dart` is down to about 1117 lines. The largest new
  project-home leaf is 159 lines, so this slice avoids replacing one giant
  file with another. Remaining project-home risk is concentrated in the
  connection details wrapper/panel and profile/pairing/runtime/diagnostics
  orchestration state.
- 2026-06-22: A3 project-home connection details extraction continued.
  `features/project_home/connection_details.dart` now owns the Diagnostics
  route wrapper and panel tree that mounts runtime/profile, lifecycle, and
  gateway-pairing panels. `project_home_screen.dart` is down to about 996
  lines and no longer owns connection details presentation. Remaining
  project-home risk is profile/pairing/runtime/diagnostics orchestration,
  repository/terminal activation, and route/lifecycle side-effect methods.
- 2026-06-22: A3 project-home profile/bootstrap extraction continued through
  the worker/reviewer gate. `features/project_home/project_home_gateway_profiles.dart`
  now owns profile key/label/sort/merge helpers, and
  `features/project_home/project_home_profile_bootstrapper.dart` owns
  secure-store load, debug profile seeding, initial selection, and debug
  auto-activate decisions. Follow-up `6203ce6` preserves the original
  `runtime_mode_panel.dart` helper import path and normal load store-order
  semantics. `project_home_screen.dart` is down to about 984 lines. Remaining
  project-home risk is pairing/runtime/diagnostics orchestration,
  repository/terminal activation, and route/lifecycle side-effect methods.
- 2026-06-23: A3 project-home pairing request extraction continued through
  the worker/reviewer gate. `features/project_home/project_home_pairing_request.dart`
  now owns manual gateway URL validation, pairing-code validation,
  device-name defaulting, manual claim endpoint construction, required scopes,
  and QR payload pass-through. `project_home_screen.dart` is down to about
  977 lines and no longer constructs manual pairing payloads inline. Remaining
  project-home risk is runtime/diagnostics orchestration,
  repository/terminal activation, route/lifecycle side-effect methods, claim
  outcome UI wiring, and callback wiring. Reviewer accepted the package with
  a follow-up for widget-level manual validation and QR scan glue tests.
- 2026-06-23: A3 project-home pairing widget follow-up passed the
  worker/reviewer gate. `test/project_home_pairing_widget_test.dart` now owns
  focused widget coverage for manual invalid gateway URL, missing pairing code,
  and QR scan payload pass-through when manual fields are invalid. This keeps
  `test/widget_test.dart` under budget while closing the review-requested
  pairing UI glue coverage gap.
- 2026-06-23: A3 route diagnostics reached the formal-review gate after
  implementation commits `39139bc` and `37bc271` plus test follow-up
  `4e54bdd`, then gained late ordering coverage in `232ac4f`. The package
  extracts route-check outcome modeling and covers success snackbar,
  failure-after-success preservation, and pending-diagnostics duplicate-check
  suppression. Follow-up `23e11bf` moves those widget scenarios out of
  `test/widget_test.dart` into `test/project_home_route_diagnostics_widget_test.dart`,
  keeping the widget-test budget intact before supplemental reviewer
  acceptance. The next post-acceptance architecture slice is planned as
  lifecycle request outcome/coordinator extraction, because its boundary is
  smaller and more testable than activation/runtime switching, terminal
  navigation, or focus side effects.
- 2026-06-23: A3 route diagnostics was accepted by reviewer3
  `job_2673b5bcff9c` and reviewer2 `job_7f71564a658f`. The next worker package
  is lifecycle request outcome/coordinator extraction, keeping UI dialog,
  mounted/setState/notifier wiring, `_viewFuture`, and snackbar display in
  `project_home_screen.dart` while moving request outcome modeling and direct
  tests into a small lifecycle coordinator.
- 2026-06-23: A3 lifecycle request outcome/coordinator extraction landed as
  implementation commit `ef9aa02` plus coverage follow-up `ef7f285`. The
  package is ready for formal review after adding direct default-timeout
  coverage and focused widget coverage for stop cancel and failure-after-success
  lifecycle detail preservation.
- 2026-06-23: A3 lifecycle request outcome/coordinator extraction was accepted
  by reviewer1 `job_396e14f00467` and reviewer2 `job_a296084cd7b9`. The next
  candidate slice under precheck is notification target selection helper
  extraction, keeping modal/sheet navigation, `setState`, selected-agent state,
  and snackbar display in `project_home_screen.dart`.
- 2026-06-23: reviewer3 precheck `job_9c091e3df2ca` approved notification
  target selection helper extraction as the next worker package. The package
  should keep sheet UI/callback shape and screen-owned side effects stable,
  move only selected-agent resolution plus notification snack text into a
  UI-free helper, preserve agent-priority/window-fallback behavior, and add
  direct resolver tests plus focused notification widget coverage.
- 2026-06-23: notification target helper extraction landed as worker commit
  `3d20d2e` and was accepted by reviewer3 `job_32835c5b0692` and reviewer2
  `job_c2ce410da688`. The package adds a UI-free resolver, keeps
  `notificationOpenMessage` available through the sheet file as a compatibility
  wrapper, moves notification widget coverage into
  `test/project_home_notification_widget_test.dart`, and keeps screen-owned
  sheet pop/state/snackbar side effects in `project_home_screen.dart`.
- 2026-06-23: reviewer1 follow-on precheck `job_dc5a961c22ed` selected claim
  outcome UI wiring / pairing claim completion coordinator as the safest next
  slice after notification helper. The proposed coordinator would model
  claim/store, profile-merge, and success/failure outcomes only; the screen
  must still own request validation, claiming state, mounted checks, profile
  assignment, pairing-code clear, activation, scanner/manual controllers, and
  snackbar display.
- 2026-06-23: lead dispatched worker2 `job_0ed4c5c7c816` to implement the
  pairing claim completion coordinator package. It should not move runtime/
  profile activation, repository/terminal activation, raw terminal navigation,
  focus side effects, shell selection, or callback cleanup.
- 2026-06-23: pairing claim completion coordinator landed as worker commit
  `9525da3` and was accepted by reviewer2 `job_7c91a53bce75` and reviewer3
  `job_43bdb54147c6`. The package adds a UI-free claim/merge outcome
  coordinator plus direct tests and pairing failure widget coverage while
  keeping request validation, claiming state, profile assignment, pairing-code
  clear, activation, and snackbar display in `project_home_screen.dart`.
- 2026-06-23: reviewer1 next-slice precheck `job_ea6f715fdf34` recommended
  project/window/agent shell selection helpers after pairing claim. Preferred
  direction is to extend existing `project_view_selection.dart` with pure
  selected-agent fallback and local window-selection helpers rather than
  adding a broader coordinator.
- 2026-06-23: lead dispatched worker1 `job_7089effebbce` to implement the
  project/window/agent shell selection helper package. It should replace only
  screen selection call sites and must not move paired-gateway focus,
  runtime/profile activation, terminal navigation, repository factories,
  scanner flow, or callback wiring.
- 2026-06-23: project/window/agent shell selection helper extraction landed as
  worker commit `6ad416f` and test follow-up `03b5ab0`, accepted by reviewer2
  `job_856fa5f15687` and reviewer3 `job_649c062f645a`. The package keeps
  `_selectedAgentName`, `setState`, paired-gateway focus, callbacks, and UI
  wiring in `project_home_screen.dart`, while selected-agent fallback and local
  window first-agent selection move into pure `project_view_selection.dart`
  helpers. Follow-up `03b5ab0` locks the current empty-string window fallback
  to the `main` window first agent.
- 2026-06-23: lead dispatched reviewer1 `job_08e57efca5d9` and reviewer2
  `job_470d6695c7d1` for read-only precheck of the next safe
  `project_home_screen.dart` extraction slice. Implementation waits for a
  bounded recommendation rather than jumping into activation, terminal,
  focus, or callback wiring changes without review gates.
- 2026-06-23: reviewer1 `job_08e57efca5d9` and reviewer2
  `job_470d6695c7d1` both recommended focus agent/window coordinator
  extraction as the next low-risk project-home slice. The package should move
  stale namespace checks, `focusAgent`/`focusWindow` repository calls,
  injectable 10s timeout, success/failure/stale outcomes, and focused-window
  selected-agent fallback into a UI-free helper while leaving `setState`,
  mounted guards, `_viewFuture`, snackbar display, fake/local window
  selection, paired terminal-open navigation, terminal transport checks, and
  runtime/profile/pairing state in `project_home_screen.dart`.
- 2026-06-23: lead dispatched worker1 `job_8ba59084166f` to implement the
  focus agent/window coordinator package with the reviewer1/reviewer2 gates
  above. Formal acceptance is held until worker1 returns a committed app
  package and reviewers check the focus behavior, terminal-open ordering,
  state ownership, and helper dependency boundary.
- 2026-06-23: focus agent/window coordinator extraction landed as worker
  commit `b24c4f7`, with stale-path/failure follow-up tests in `c216db4`.
  The package adds the UI-free coordinator plus direct/focused widget tests and
  is now in formal review handoff. Acceptance should verify stale/failure
  screen handling, paired terminal focus-before-navigation, fake/local no-focus
  behavior, and the coordinator dependency boundary before Last Landed
  advances.
- 2026-06-23: reviewer3 `job_2380f50e2f66` accepted the focus coordinator
  package with no blocking findings and one low-risk mounted-check follow-up
  note for stale outcomes after an awaited coordinator call. Reviewer2 review
  is still pending before Last Landed advances.
- 2026-06-23: reviewer2 `job_be784530ef4e` also accepted the focus coordinator
  package with no blocking findings and one minor test gap: the default 10s
  timeout is visible in code but not explicitly asserted. Lead will close the
  mounted-check and default-timeout notes through a small worker follow-up
  before advancing Last Landed.
- 2026-06-23: focus coordinator follow-up `9e13d21` closed the mounted-check
  and direct default-timeout notes, so the focus agent/window package advanced
  to the A3 Last Landed checkpoint at that point. Reviewer1 `job_3df0277eed9a`
  recommends scan flow / QR pairing UI coordinator as the next low-risk slice.
- 2026-06-23: A3 scan flow / QR pairing UI coordinator extraction was accepted
  by reviewer3 `job_bebc09d1ed8b` and reviewer2 `job_f83fc409bbd8` after
  implementation `46e583e`, pending-claim scan coverage `dc6d0f0`, live
  route-kind refresh fix `ce5d79e`, and no-reopen route assertion `5fc80aa`.
  `project_home_pairing_scan_coordinator.dart` is UI-free and models only
  scanner busy/cancel/success/failure outcomes. `project_home_screen.dart`
  keeps scanner `BuildContext`, controller writes, route-kind state, claim
  override, activation, and snackbar ownership, while `_pairingRouteKindNotifier`
  lets the already-open Connection Details route reflect QR route changes before
  claim completion. The remaining immediate hygiene issue is test structure:
  `project_home_pairing_widget_test.dart` is now about 537 lines and should be
  split into scan-specific widget coverage before more pairing scenarios land.
- 2026-06-23: A3 pairing scan widget coverage split landed as `390469b` and
  was accepted by reviewer3 `job_81419217e21d`. Scan cancel, failure,
  pending-claim success, and busy/claiming scan scenarios now live in
  `test/project_home_pairing_scan_widget_test.dart`; non-scan pairing
  validation and claim failure coverage remain in
  `test/project_home_pairing_widget_test.dart`. Both focused files are now
  under the 500-line budget.
- 2026-06-23: reviewer2 precheck `job_2aecc2933b77` agreed that
  runtime/profile activation outcome helper is the next production slice, with
  the narrower boundary that the helper should not import `AppRuntimeMode` or
  any Flutter/repository/terminal/factory/screen dependencies. Worker1 package
  `job_44861a231e67` is dispatched against reviewer1/reviewer2 gates.
- 2026-06-23: runtime/profile activation outcome helper extraction landed as
  `1f68890` and was accepted by reviewer2 `job_4f5e37263212`, reviewer1
  `job_3ec84d7520de`, and reviewer3 `job_91768c2f0949`. The new
  `project_home_runtime_activation.dart` helper stays UI-free and models only
  paired-profile selection, no-profile snack outcome, gateway URL/route-kind/
  active project id activation data, and fake-mode reset intent. The screen
  still owns `AppRuntimeMode`, `setState`, controller and route-kind notifier
  writes, repository/terminal factories, `_viewFuture`, activation side
  effects, lifecycle reset, and snackbar display. The next slice should be
  prechecked around the remaining repository/terminal activation or raw
  terminal navigation glue before another worker package is dispatched.
- 2026-06-23: raw terminal navigation outcome/spec helper extraction landed
  as `4446406` and was accepted by reviewer1 `job_c5ec2faeb205` and reviewer2
  `job_e78d4b579f6d`. The new `project_home_terminal_navigation.dart` helper
  stays UI-free and models fake terminal specs, paired post-focus terminal
  specs, no-navigation, and the defensive no-transport snack outcome. The
  screen still owns `_mode`, `_focusAgent`, mounted checks, real
  `_terminalTransport`, `_activeRepository`, `_showSnack`, `Navigator`,
  `MaterialPageRoute`, and `FakeTerminalScreen` construction. Follow-up
  `2775863` widened the exported `GatewayTerminalTransportFactory` typedef to
  nullable for widget coverage; reviewer2 rejected that public API drift,
  reviewer1 considered it acceptable, and `09921f2` reverted it so the final
  accepted state keeps the public factory type non-null.
- 2026-06-23: reviewer2 `job_17b9dceb2eb3` and reviewer1
  `job_b2e4c228d3e3` selected active-view refresh outcome/coordinator
  extraction as the next A3 package. Lead dispatched worker1
  `job_4fb2ee108bbe` to move only the `getProjectView` refresh call,
  injectable 10s timeout, success/failure outcome, and next selected-agent
  calculation into a UI-free `project_home_view_refresh.dart` helper. The
  screen must still own `_activeRepository`, `_activeProjectId`, mounted
  checks, `setState`, `_viewFuture`, `_selectedAgentName`, snackbar display,
  and `SelectedAgentWorkspace(onRefreshView: _refreshActiveView)` wiring.
- 2026-06-23: active-view refresh outcome/coordinator extraction landed as
  `8962e45` and was accepted by reviewer2 `job_992256a4274c`, reviewer1
  `job_6d331e644728`, and reviewer3 `job_d8df7e67dca7` with one P2 follow-up.
  `project_home_view_refresh.dart` is UI-free and handles the active view
  refresh call, default 10s timeout, success/failure outcome, and selected-agent
  preserve/clear calculation. Focused direct/widget tests cover exact project
  id, same refreshed view, selected-agent preserve/clear, repository error,
  timeout, stale namespace retry, missing-agent cleanup, and refresh-failure
  preservation. The P2 follow-up is to restore non-null public constructor
  invariants in existing runtime activation and terminal navigation outcome
  helpers after analyzer cleanup widened nullable variant fields.
- 2026-06-23: P2 invariant follow-up `7fac3ec` was accepted by reviewer3
  `job_6912bf683dea` and reviewer2 `job_72e3edd0687a`. Reviewer3
  `job_1cee5bac7ab4`, reviewer2 `job_5b6e97fa0558`, and reviewer1
  `job_766409cfa87e` recommend the next A3 package as a deliberately narrow
  connection-details panel host/wiring
  extraction: keep `_openConnectionDetails` route navigation and
  `ConnectionDetailsScreen` construction in `project_home_screen.dart`, and
  move only the `ValueListenableBuilder<RouteProviderKind>` plus
  `ConnectionDetailsPanel` parameter wiring into a small host widget. The
  critical invariant is that route-kind live updates continue to refresh the
  already-open Pair Gateway panel after manual selection, profile activation,
  or QR scan success.
- 2026-06-23: connection-details panel host/wiring extraction landed as
  `459912d` and entered formal review with reviewer1 `job_00922abd2262`,
  reviewer2 `job_4931ec64bf05`, and reviewer3 `job_e78a09d560af`. Reviewer2
  and reviewer3 accepted the package with no blocking findings; reviewer1
  also accepted it with no blocking findings in `job_00922abd2262`. The
  package adds `project_home_connection_details_panel_host.dart` as a thin
  `ValueListenableBuilder<RouteProviderKind>` plus `ConnectionDetailsPanel`
  host; `_openConnectionDetails` still owns `Navigator`, `MaterialPageRoute`,
  and `ConnectionDetailsScreen` construction.
- 2026-06-23: lead dispatched read-only next-slice prechecks to reviewer1
  `job_6f6c5d4aa474`, reviewer2 `job_9ee1d5167796`, and reviewer3
  `job_9b147137345e` after inspecting the residual `project_home_screen.dart`
  surface. Candidate regions include simple shell UI state, profile
  bootstrap/load state application, runtime/profile activation side effects,
  pairing state application, notification modal/snackbar glue, and remaining
  route shells; implementation waits for a bounded recommendation before a
  worker package is dispatched.
- 2026-06-23: lead local residual audit confirms `project_home_screen.dart`
  is now less about UI leaf extraction and more about screen-owned state
  application. Remaining responsibilities cluster around wide/mobile shell
  state mutations, profile bootstrap/load loading flags, runtime/profile
  activation side effects, pairing scan/claim controller writes and claiming
  flags, route/lifecycle/focus/refresh snackbar/state application, notification
  modal glue, and raw terminal/details route shells. The next package should
  be selected by reviewer precheck rather than by line-count reduction alone.
- 2026-06-23: next-slice prechecks started converging on local shell state.
  Reviewer3 `job_9b147137345e` recommends a pure local shell state reducer,
  but reviewer1 `job_6f6c5d4aa474` recommends narrowing the package to only
  wide-sidebar state transitions because that boundary is smallest and already
  has `wide_sidebar_state.dart` as the natural home. The selected next package
  should therefore move wide sidebar collapse/expand/toggle and drag transition
  pure logic into `wide_sidebar_state.dart` while leaving mobile collapse,
  project open/close, agent/window selection, routes, runtime, pairing,
  terminal, notification, focus, and refresh untouched. Reviewer2
  `job_9ee1d5167796` recommends notification-open outcome extraction instead;
  record it as the next alternate candidate rather than mixing it into the
  wide-sidebar package.
- 2026-06-23: after the user requested more cohesive packages and one review
  lane per package, subsequent ProjectHome A3 packages moved larger bounded
  responsibilities instead of one-method helpers. The accepted sequence now
  includes notification-open outcome (`c1cf0bd`), runtime session activation
  (`e261c99`), local shell state (`65020f6`), profile loading (`3631f29` plus
  test follow-up `81a385d`), scaffold host (`eca07e3`), route actions
  (`88a529a`), pairing form controller (`a31238d`), and pairing flow
  coordinator (`c3d422b`). The current screen is about 839 lines and should be
  reduced further only by cohesive packages that keep screen-owned state
  application explicit.
- 2026-06-23: reviewer2 `job_1c9b5e9a92b9` recommends stopping production
  `ProjectHomeScreen` extraction for now. The remaining screen code is mostly
  the composition root for state fields, `setState`, mounted guards, snackbar
  display, callback closures, active repository/project/transport assignment,
  and notifier updates. A new state applier/controller would likely hide
  screen-owned semantics. Future work should resume Phase 5 relay-first
  package selection unless a new cohesive product-driven ProjectHome package
  appears.

## Current Inventory

Largest Dart files:

| File | Lines | Current role |
| :--- | ---: | :--- |
| `app/lib/features/project_home/project_home_screen.dart` | 839 | Stop-condition composition root after A1/A3 extraction: owns state fields, `setState`, mounted guards, snackbar display, callback closures, active repository/project/transport assignment, notifier updates, and application of accepted helper/coordinator outcomes. Profile helper/bootstrap and profile loading outcomes, manual pairing request construction, pairing form controller ownership, pairing flow request/scan/claim composition, route diagnostics, lifecycle, notification target/open outcomes, shell selection, wide-sidebar state transitions, focus coordination, runtime/profile activation/session modeling, raw terminal navigation outcome/spec decisions, route/modal shell actions, active-view refresh outcome modeling, connection-details panel host wiring, and scaffold host composition are now extracted. |
| `app/test/http_gateway_transport_test.dart` | 856 | HTTP gateway contract tests. |
| `app/integration_test/emulator_gateway_smoke_test.dart` | 722 | End-to-end emulator UI smoke with fake, pairing, diagnostics, lifecycle, chat, terminal, and timeout diagnostics. |
| `app/test/gateway_route_diagnostics_test.dart` | 616 | Route diagnostics tests. |
| `app/lib/transport/gateway_transport.dart` | 539 | Gateway interface plus DTOs/frame models. |
| `app/test/widget_test.dart` | 393 | Remaining project-home widget smoke coverage for notifications, lifecycle, window switching, runtime mode, pairing, and paired gateway terminal after layout/chat/route-diagnostics/notification scenario extraction. |
| `app/test/project_home_pairing_scan_widget_test.dart` | 329 | Focused scan-flow widget coverage for scan cancel, scan failure with route unchanged, pending scan claim route updates, and busy/claiming no-scanner behavior. |
| `app/test/project_home_pairing_widget_test.dart` | 326 | Focused project-home pairing widget coverage for manual validation negative paths, QR invalid-manual pass-through, manual claim failure/no activation, and manual claim success code-only clear plus activation. |
| `app/test/project_home_scaffold_host_test.dart` | 283 | Focused ProjectHome scaffold-host coverage for mobile host keys/callback forwarding, terminal disabled state with no selected agent, and wide sidebar surfaces across `WideSidebarState`. |
| `app/test/project_home_route_actions_widget_test.dart` | 213 | Focused ProjectHome route-action widget coverage for terminal route push, connection-details route push, notification sheet pop-before-callback behavior, and stop confirmation dialog results. |
| `app/test/project_home_pairing_form_controller_test.dart` | 197 | Direct pairing form controller coverage for defaults, route-kind notifier updates, manual request validation/defaulting, QR override pass-through, scan form application, activation form application, and code-only clearing. |
| `app/test/project_home_pairing_flow_test.dart` | 237 | Direct pairing flow coordinator coverage for request build outcome mapping, scan busy/cancel/failure/success, exact QR payload pass-through, claim success delegation, and claim/merge failure mapping. |
| `app/test/project_home_route_diagnostics_widget_test.dart` | 182 | Focused route diagnostics widget coverage for success snackbar/report rendering, failure-after-success report preservation, and pending-diagnostics duplicate-check suppression. |
| `app/test/project_home_view_refresh_widget_test.dart` | 175 | Focused active-view refresh widget coverage for stale namespace retry, selected-agent cleanup when refreshed view drops an agent, and refresh failure preservation. |
| `app/test/project_home_connection_details_panel_host_test.dart` | 94 | Focused connection-details panel host coverage for route-kind listenable live updates and route-kind callback forwarding. |
| `app/test/support/project_home_test_fakes.dart` | 469 | Reusable project-home widget-test fakes and fixtures: recording repository/terminal transport, controlled submit/stale/Markdown/long conversation repositories, demo payload builders, rendered text finder, and memory secure store. |
| `app/lib/features/terminal/fake_terminal_screen.dart` | 452 | Raw terminal screen and control bar. |
| `app/lib/transport/http_gateway_transport.dart` | 433 | HTTP/WebSocket gateway implementation. |
| `app/lib/pairing/gateway_pairing.dart` | 422 | Pairing/profile DTOs, client, secure store. |
| `app/test/agent_chat_composer_widget_test.dart` | 343 | Focused selected-agent composer widget coverage for terminal open, per-agent drafts, send/retry states, markdown rendering, partial-pane sends, and stale-epoch retry. |
| `app/test/agent_message_submit_coordinator_test.dart` | 323 | Direct selected-agent message submit coordinator coverage for repository sends, remote conversation application, and blank-send guards. |
| `app/lib/features/agent_chat/selected_agent_workspace.dart` | 306 | Extracted selected-agent workspace feature entrypoint after controller/state, timeline assembly, loaders, submitters, side-effect coordinators, refresh scheduler, UI-controller store, view, and view-model extraction. Remaining role is lifecycle/callback wiring around the extracted workspace pieces. |
| `app/test/project_home_runtime_activation_widget_test.dart` | 340 | Focused project-home runtime activation widget coverage for no-profile paired mode, profile-load failure UI recovery, selected/first profile activation, route-kind live refresh, dropdown activation, and fake reset terminal path. |
| `app/test/pane_chat_controller_test.dart` | 291 | Direct pane-chat controller coverage for paste-plus-Enter, output events, error notice events, echo deduplication, stream recovery, session reuse, and staged send failures outside a widget tree. |
| `app/test/project_home_layout_widget_test.dart` | 284 | Focused project-home layout/widget-shell coverage for project list, wide sidebars, mobile agent/composer collapse, keyboard insets, and two-detent sidebar drag. |
| `app/test/agent_chat_history_widget_test.dart` | 276 | Focused selected-agent history/timeline widget coverage for readable terminal history, tmux-history compact bubbles, virtualization, scroll-to-latest, and background pane output. |
| `app/lib/features/agent_chat/pane_chat_controller.dart` | 274 | Extracted pane-chat controller for selected-agent terminal session reuse, paste-plus-Enter sends, stream output, echo dedupe, recovery, and staged send failures. |
| `app/lib/features/agent_chat/agent_message_submit_coordinator.dart` | 266 | Extracted selected-agent send/retry orchestration, optimistic-message state transitions, repository outcome application, pane-send replacement handling, and post-send refresh scheduling. |
| `app/lib/models/ccb_conversation_item.dart` | 242 | Conversation item and delivery-state model, including the local `unconfirmed`/`Check pane` state. |
| `app/lib/features/agent_chat/readable_terminal_history_panel.dart` | 235 | Extracted readable terminal history loader, panel, block list, block copy controls, stale/epoch/source chips. |
| `app/lib/features/agent_chat/agent_chat_controller.dart` | 222 | Extracted selected-agent chat state controller for local messages, remote conversations, refreshed history, loading/submitting flags, expanded/collapsed/new-message state, and message ids. |
| `app/lib/features/agent_chat/conversation_item_presentation.dart` | 167 | Extracted conversation preview/body/rendering policy helpers, state labels, terminal-derived detection, and blocked-link snackbar. |
| `app/lib/features/project_home/project_lifecycle_panel.dart` | 159 | Extracted project lifecycle controls and status/detail rendering. |
| `app/test/support/project_home_test_driver.dart` | 159 | Reusable project-home widget interaction helpers for opening surfaces, switching modes, viewport/inset setup, selected agent/window assertions, visible taps, and timeline drag-until-visible flows. |
| `app/lib/features/project_home/runtime_mode_panel.dart` | 149 | Extracted runtime/profile selector, route diagnostics status, and re-exported shared gateway profile key/label helpers. |
| `app/test/project_home_gateway_profiles_test.dart` | 155 | Focused gateway profile helper/bootstrapper coverage for helper API compatibility, merge replacement/sort, store-order load, debug seed, and auto-activate decisions. |
| `app/test/project_home_profile_loading_test.dart` | 186 | Direct profile-loading coordinator coverage for no-debug load intent, debug success with auto-activate, bootstrap failure fallback intent, load failure preservation, and store-order selection. |
| `app/lib/features/agent_chat/conversation_timeline.dart` | 151 | Extracted virtualized selected-agent timeline and item routing to conversation, content, and readable-history bodies. |
| `app/lib/features/project_home/project_list.dart` | 141 | Extracted phone project list screen and shared project list tile. |
| `app/lib/features/project_home/mobile_agent_switcher.dart` | 137 | Extracted phone window/agent switcher collapse/expand panel. |
| `app/lib/features/project_home/gateway_pairing_panel.dart` | 134 | Extracted gateway URL/code/device/route inputs plus QR scan and claim controls. |
| `app/lib/features/project_home/connection_details.dart` | 132 | Extracted Diagnostics route wrapper and connection details panel mounting runtime, lifecycle, and gateway-pairing leaves. |
| `app/lib/features/project_home/project_home_scaffold_host.dart` | 255 | Extracted presentational ProjectHome scaffold hosts for project list, mobile opened-project chat scaffold, and wide project scaffold; forwards callbacks without owning route/modal/snackbar/state behavior. |
| `app/lib/features/project_home/project_home_route_actions.dart` | 96 | Extracted ProjectHome route/modal shell actions for terminal route push, connection-details route push, notification center sheet, and stop confirmation dialog. |
| `app/lib/features/project_home/project_home_pairing_flow.dart` | 174 | Extracted pairing flow coordinator that composes request-build, scan, and claim outcomes around existing pairing request/scan/claim boundaries without owning UI state. |
| `app/lib/features/project_home/project_home_pairing_form_controller.dart` | 71 | Extracted pairing form controller for gateway URL/code/device text controllers, route-kind value/listenable, manual/QR request building, scan/activation form writes, code clearing, and disposal. |
| `app/lib/features/project_home/project_home_connection_details_panel_host.dart` | 91 | Extracted connection-details panel host that listens to route-kind changes and forwards the existing `ConnectionDetailsPanel` wiring. |
| `app/lib/features/project_home/notification_center_sheet.dart` | 120 | Extracted notification center bottom sheet, icons, target labels, and notification-open message helper. |
| `app/lib/features/project_home/wide_agent_column.dart` | 116 | Extracted wide window-grouped agent sidebar. |
| `app/lib/features/project_home/agent_window_switchers.dart` | 108 | Extracted shared horizontal agent/window chip switchers. |
| `app/test/project_home_pairing_request_test.dart` | 119 | Focused pairing request helper coverage for manual validation, default device names, exact claim endpoint/scopes, and QR payload pass-through. |
| `app/test/project_home_view_refresh_test.dart` | 126 | Direct active-view refresh helper coverage for exact project id, same refreshed view, selected-agent preserve/clear/null behavior, repository failure, and timeout. |
| `app/test/project_home_runtime_activation_test.dart` | 105 | Direct runtime activation helper coverage for no-profile, selected-vs-first profile selection, store-order preservation, project id fallback, URL/route kind activation data, and fake reset data. |
| `app/lib/features/project_home/project_view_selection.dart` | 103 | Extracted ProjectView window/agent ordering, filtering, selected-window, and first-agent helpers. |
| `app/test/project_home_terminal_navigation_widget_test.dart` | 281 | Focused raw terminal navigation widget coverage for paired focused project id, paired stale/failure no-navigation, and fake no-focus terminal open. |
| `app/test/project_home_terminal_navigation_test.dart` | 84 | Direct raw terminal navigation helper coverage for fake specs, null focused view, no-transport snack outcome, focused project id, and bool-only transport readiness modeling. |
| `app/lib/features/project_home/project_home_pairing_request.dart` | 78 | Extracted manual gateway pairing request validation, defaulting, payload construction, and QR override pass-through helper. |
| `app/lib/features/project_home/project_home_runtime_activation.dart` | 82 | Extracted UI-free runtime/profile activation outcome helper for paired profile selection, no-profile snack outcome, gateway activation data, and fake reset data. |
| `app/lib/features/project_home/project_home_terminal_navigation.dart` | 76 | Extracted UI-free raw terminal navigation outcome/spec helper for fake specs, paired post-focus specs, no-navigation, and no-transport snack outcome. |
| `app/lib/features/project_home/project_home_view_refresh.dart` | 64 | Extracted UI-free active-view refresh coordinator for active repository `getProjectView`, timeout, success/failure outcome, and selected-agent preserve/clear calculation. |
| `app/test/project_home_pairing_scan_coordinator_test.dart` | 79 | Direct pairing scan coordinator coverage for busy, cancel, exact-payload success, and failure snackbar text. |
| `app/lib/features/project_home/project_home_pairing_scan_coordinator.dart` | 54 | Extracted UI-free pairing scan outcome helper for busy/cancel/success/failure scanner results. |
| `app/lib/features/project_home/project_home_profile_bootstrapper.dart` | 56 | Extracted gateway profile secure-store load, debug profile seeding, initial selection, and auto-activate decision helper. |
| `app/lib/features/project_home/project_home_profile_loading.dart` | 77 | Extracted UI-free profile loading coordinator around profile bootstrap/load outcomes and debug-bootstrap fallback intent. |
| `app/lib/features/project_home/project_home_gateway_profiles.dart` | 32 | Extracted gateway profile key, label, sort, and merge helpers shared by runtime UI and profile bootstrap/claim paths. |
| `app/lib/features/project_home/wide_project_column.dart` | 74 | Extracted wide project column shell. |
| `app/lib/features/project_home/wide_collapsed_sidebar_rail.dart` | 72 | Extracted wide collapsed sidebar rail actions. |
| `app/lib/features/project_home/wide_sidebar_drag_handle.dart` | 70 | Extracted wide sidebar drag/tap handle presentation. |
| `app/lib/features/project_home/project_chat_header.dart` | 65 | Extracted project chat header actions. |
| `app/lib/features/project_home/wide_sidebar_state.dart` | 42 | Extracted wide sidebar detent constants, state enum, and drag target helper. |
| `app/lib/features/project_home/project_shell_widgets.dart` | 10 | Barrel export for project-home shell leaves. |
| `app/lib/features/agent_chat/agent_message_composer.dart` | 135 | Extracted selected-agent composer leaf widget. |
| `app/lib/features/agent_chat/conversation_bubble.dart` | 131 | Extracted conversation bubble shell preserving keys, compact preview, state chip, Retry, and expand/collapse behavior. |
| `app/lib/features/agent_chat/agent_pane_message_submitter.dart` | 116 | Extracted pane-backed selected-agent message submit path, stale retry, partial-input mapping, and pane event subscription lifecycle. |
| `app/lib/features/agent_chat/content_reader.dart` | 112 | Extracted structured content reader, Markdown body rendering, raw-source expansion, and copy controls. |
| `app/lib/features/agent_chat/selected_agent_workspace_view.dart` | 110 | Extracted no-agent and selected-agent timeline/composer widget assembly. |
| `app/lib/features/agent_chat/terminal_history_conversation_items.dart` | 110 | Extracted terminal history command/output to compact foreground conversation item mapping. |
| `app/lib/features/agent_chat/agent_repository_message_submitter.dart` | 99 | Extracted selected-agent compatibility repository message submit path and UI outcome mapping. |
| `app/lib/features/agent_chat/agent_conversation_refresh_coordinator.dart` | 94 | Extracted selected-agent conversation load/apply/error/new-message/scroll side-effect coordination. |
| `app/lib/features/agent_chat/pane_chat_event_messages.dart` | 89 | Extracted pane event to local conversation message mapping for live output and terminal notices. |
| `app/lib/features/agent_chat/agent_chat_state_helpers.dart` | 78 | Extracted pure selected-agent chat state helpers for conversation signatures, stale epoch detection, partial-send delivery state, and local optimistic-message pruning. |
| `app/lib/features/agent_chat/agent_chat_ui_controller_store.dart` | 71 | Extracted per-agent draft and timeline scroll controller lifecycle, near-end checks, and post-frame jump-to-latest retries. |
| `app/lib/features/agent_chat/live_terminal_output.dart` | 68 | Extracted live terminal output compaction and merge helpers. |
| `app/lib/features/agent_chat/selected_agent_workspace_model.dart` | 63 | Extracted selected-agent workspace view-model assembly for the extracted view. |
| `app/lib/features/agent_chat/agent_terminal_history_refresh_coordinator.dart` | 57 | Extracted post-pane-send readable terminal-history refresh application, new-message flag, and scroll side-effect coordination. |
| `app/lib/features/agent_chat/agent_conversation_loader.dart` | 57 | Extracted selected-agent conversation repository fetch plus stale epoch refresh handling. |
| `app/lib/features/agent_chat/agent_chat_timeline_items.dart` | 57 | Extracted selected-agent timeline item ordering across remote conversation, terminal-history foreground evidence, ProjectView/content fallback, refresh errors, and local messages. |
| `app/lib/features/agent_chat/agent_pane_event_coordinator.dart` | 56 | Extracted pane output/notice event application, new-message flag, and scroll side-effect coordination. |
| `app/lib/features/agent_chat/conversation_refresh_scheduler.dart` | 54 | Extracted post-submit delayed conversation refresh timer scheduling and cancellation. |
| `app/lib/features/agent_chat/terminal_history_presentation.dart` | 46 | Extracted terminal-history labels, block text, icons, and colors. |
| `app/lib/features/agent_chat/agent_terminal_history_loader.dart` | 32 | Extracted post-pane-send readable terminal-history refresh and supplemental-error swallowing. |
| `app/lib/features/agent_chat/clipboard_feedback.dart` | 9 | Shared copy-to-clipboard snackbar helper for content and readable-history leaves. |

`app/lib/main.dart` is no longer the main architecture risk. The remaining
giant file is `app/lib/features/project_home/project_home_screen.dart`, which
contains roughly these regions:

- lines 1-82: imports, public `ProjectHomeScreen` wrapper, and
  project-home view shell setup;
- lines 84-837: `ProjectHomeScreen` state, repository/terminal activation,
  pairing flow state application, runtime switching, raw terminal navigation,
  callback wiring, and mounting of extracted project shell widgets;
- lines 838-839: lifecycle snackbar helper.

## Problems

1. One file owns unrelated reasons to change.

   `main.dart` currently changes for project shell layout, terminal transport,
   pairing, route diagnostics, lifecycle, chat timeline rendering, Markdown,
   history display, and test affordances. Small changes increase merge and
   regression risk.

2. Stateful logic and UI are interleaved.

   `_ProjectHomeViewState` owns profile activation, route checks, lifecycle,
   selected agent/window state, navigation, and selected-agent terminal
   transport. `_SelectedAgentWorkspaceState` owns draft/scroll maps, remote
   conversations, local optimistic items, pane sessions, terminal live output,
   and UI composition.

3. Controller boundaries are implicit.

   The app already has clean lower-level seams (`MobileCcbRepository`,
   `GatewayTransport`, `TerminalTransport`), but the UI layer does not have
   explicit controllers for:

   - active host/profile/runtime mode;
   - project shell selection and focus;
   - selected-agent chat timeline and drafts;
   - pane-backed chat sessions;
   - connection details/diagnostics/lifecycle actions.

4. Test fixtures are too concentrated.

   `widget_test.dart` mixes all widget tests with recording transports, fake
   secure store, fake gateway repositories, controlled submit repos, stale
   epoch repos, Markdown repos, and long conversation fixtures.

5. Feature folders do not match product surfaces.

   `app/lib/features/terminal/` exists, but project shell, chat, connection,
   lifecycle, notifications, and pairing screens are still embedded in
   `main.dart`.

## Architecture Targets

### Package Shape

Keep the current lightweight Flutter app and existing model/transport/repository
seams. Add feature folders that mirror product surfaces:

```text
app/lib/
  app/
    ccb_mobile_app.dart
    app_factories.dart
    runtime_mode.dart
  features/
    project_home/
      project_home_screen.dart
      project_home_controller.dart
      project_list.dart
      project_chat_header.dart
      wide_project_shell.dart
      mobile_agent_switcher.dart
      notification_center_sheet.dart
    agent_chat/
      selected_agent_workspace.dart
      agent_chat_controller.dart
      agent_chat_ui_controller_store.dart
      agent_chat_state_helpers.dart
      agent_chat_timeline_items.dart
      agent_conversation_loader.dart
      agent_terminal_history_loader.dart
      agent_repository_message_submitter.dart
      agent_pane_message_submitter.dart
      agent_message_submit_coordinator.dart
      pane_chat_event_messages.dart
      conversation_refresh_scheduler.dart
      pane_chat_controller.dart
      selected_agent_workspace_model.dart
      selected_agent_workspace_view.dart
      agent_conversation_refresh_coordinator.dart
      agent_pane_event_coordinator.dart
      agent_terminal_history_refresh_coordinator.dart
      conversation_timeline.dart
      conversation_bubble.dart
      agent_message_composer.dart
      terminal_history_items.dart
    connection/
      connection_details_screen.dart
      runtime_mode_panel.dart
      gateway_pairing_panel.dart
      project_lifecycle_panel.dart
      route_diagnostics_panel.dart
    terminal/
      fake_terminal_screen.dart
  models/
  repository/
  transport/
  pairing/
  fixtures/
```

Use `main.dart` only as the entrypoint:

```dart
import 'app/ccb_mobile_app.dart';

void main() {
  runApp(const CcbMobileApp());
}
```

### State Ownership

Use the existing `flutter_riverpod` dependency for app-level and feature-level
controllers, but migrate incrementally. Do not rewrite every stateful widget in
one pass.

Target controllers:

- `AppRuntimeController`
  Owns active repository, active terminal transport, selected profile,
  runtime mode, profile bootstrap, debug profile seed, and profile activation.

- `ProjectShellController`
  Owns selected project id, opened project id, selected window/agent, wide
  sidebar detents, mobile agent-panel collapse, focus-agent/window calls, and
  ProjectView refresh.

- `AgentChatController`
  Owns per-agent drafts, scroll controllers or scroll intents, expanded item
  ids, local optimistic messages, conversation errors, loading state, and
  new-message flags.

- `PaneChatController`
  Owns selected-agent `TerminalSession` lifecycle, paste plus Enter sends,
  live output subscription, stream errors, retry constraints, echo
  deduplication, and terminal-history refresh triggers.

- `ConnectionController`
  Owns route diagnostics, lifecycle actions, pairing claim, scan flow, and
  details panel state.

### Dependency Direction

Keep strict one-way dependency flow:

```text
Widgets -> Controllers -> Repository/Transport -> Models
```

Rules:

- Feature widgets should not instantiate `HttpGatewayTransport` directly.
- Feature widgets should not know secure-store details.
- `agent_chat` may depend on `TerminalTransport` and `MobileCcbRepository`, but
  not on route-provider or pairing internals.
- `connection` may depend on pairing/profile/diagnostics/lifecycle, but not on
  conversation timeline internals.
- `transport` must not import feature widgets.
- `models` must not import Flutter UI packages.

## File Budgets

Use these budgets as guardrails, not hard failures:

| File type | Target max |
| :--- | ---: |
| Entrypoint file | 40 lines |
| Feature screen | 250 lines |
| Feature controller | 300 lines |
| Leaf widget | 220 lines |
| DTO/model file | 250 lines |
| Transport interface/DTO file | 350 lines |
| Transport implementation | 450 lines |
| Widget test file | 500 lines |
| Integration smoke | 700 lines, acceptable if high-level helper extraction continues |

`gateway_transport.dart` is allowed to remain larger temporarily because it is
the route-agnostic gateway contract. Split it only after app-shell extraction,
because moving DTOs too early will cause wide test churn.

## Migration Packages

### A0: Safety Baseline

Goal: make architecture moves mechanically safe.

Work:

- keep current passing checks as the safety gate:
  `flutter test`, `flutter test integration_test/emulator_gateway_smoke_test.dart`,
  and `tools/mobile_emulator_ui_smoke.py`;
- add a simple architecture inventory command to handoff notes:
  `find app/lib app/test app/integration_test -name '*.dart' -print0 | xargs -0 wc -l | sort -nr`;
- freeze public app behavior during extraction: no UI redesign, no protocol
  changes, no state semantics changes.

Acceptance:

- no code move starts without a passing baseline;
- every extraction package keeps tests green.

### A1: App Bootstrap And Factories Extraction

Goal: shrink the top of `main.dart` and isolate dependency construction.

Move:

- `CcbMobileApp`;
- `ProjectHomeScreen` public wrapper;
- gateway repository/terminal/diagnostics factory typedefs and default factory
  functions;
- `_AppRuntimeMode`;
- wide layout constants if only used by project shell after A2.

Target files:

- `app/lib/app/ccb_mobile_app.dart`
- `app/lib/app/app_factories.dart`
- `app/lib/app/runtime_mode.dart`

Acceptance:

- `main.dart` only calls `runApp`;
- public imports from `ccb_mobile.dart` stay stable;
- `flutter test test/widget_test.dart` passes.

### A2: Project Home Shell Extraction

Goal: isolate project list, mobile/wide shell, window/agent switching, and
notification center from chat and connection details.

Move:

- `_ProjectHomeView` and `_ProjectHomeViewState`;
- `_ProjectListTile`;
- `_WideProjectColumn`;
- `_WideAgentColumn`;
- `_WideAgentTile`;
- `_WideCollapsedSidebarRail`;
- `_WideSidebarDragHandle`;
- `_ProjectChatHeader`;
- `_AgentSwitcher`;
- `_MobileAgentSwitcherPanel`;
- `_WindowSwitcher`;
- `_NotificationCenterSheet`;
- project/window/agent ordering helpers.

Target files:

- `features/project_home/project_home_screen.dart`
- `features/project_home/project_home_controller.dart`
- `features/project_home/project_list.dart`
- `features/project_home/wide_project_shell.dart`
- `features/project_home/mobile_agent_switcher.dart`
- `features/project_home/notification_center_sheet.dart`

Acceptance:

- project shell imports `agent_chat` and `connection` as feature children;
- no connection details widgets remain in the project-home file;
- phone and wide widget tests still pass.

### A3: Agent Chat Feature Extraction

Goal: make pane-backed chat independently testable.

Move:

- `_SelectedAgentWorkspace`;
- `_ConversationTimeline`;
- `_ConversationTimelineItem`;
- `_ConversationBubble`;
- `_ConversationPreview`;
- `_ConversationBody`;
- `_ConversationStateChip`;
- `_AgentMessageComposer`;
- `_conversationItemsFor`;
- `_terminalHistoryConversationItems`;
- terminal-derived item helpers;
- `_AgentReadableHistoryLoader`;
- `_AgentContentReader`;
- `_ContentItemView`;
- `_ReadableTerminalHistoryPanel`;
- `_TerminalHistoryBlockView`;
- copy/link helpers if only used by chat/content.

Create:

- `AgentChatController` for drafts, expanded item ids, loading/errors, local
  optimistic messages, and new-message flags.
- `PaneChatController` for terminal sessions, paste plus Enter, output
  subscription, error notice items, stream close, and history refresh requests.

Target files:

- `features/agent_chat/selected_agent_workspace.dart`
- `features/agent_chat/selected_agent_workspace_model.dart`
- `features/agent_chat/selected_agent_workspace_view.dart`
- `features/agent_chat/agent_conversation_refresh_coordinator.dart`
- `features/agent_chat/agent_pane_event_coordinator.dart`
- `features/agent_chat/agent_terminal_history_refresh_coordinator.dart`
- `features/agent_chat/agent_chat_controller.dart`
- `features/agent_chat/agent_chat_ui_controller_store.dart`
- `features/agent_chat/agent_chat_state_helpers.dart`
- `features/agent_chat/agent_chat_timeline_items.dart`
- `features/agent_chat/conversation_refresh_scheduler.dart`
- `features/agent_chat/pane_chat_controller.dart`
- `features/agent_chat/conversation_timeline.dart`
- `features/agent_chat/conversation_bubble.dart`
- `features/agent_chat/agent_message_composer.dart`
- `features/agent_chat/readable_terminal_history_panel.dart`
- `features/agent_chat/content_reader.dart`

Acceptance:

- paired-gateway composer test proves no `submitAgentMessage` call for default
  sends;
- pane send test can instantiate `PaneChatController` without a widget tree;
- output stream and error handling tests do not require `ProjectHomeScreen`;
- `main.dart` contains no selected-agent chat classes.

### A4: Connection/Diagnostics/Lifecycle Extraction

Goal: remove secondary route panels from the project shell.

Move:

- `_ConnectionDetailsScreen`;
- `_ConnectionDetailsPanel`;
- `_RuntimeModePanel`;
- `_GatewayPairingPanel`;
- `_ProjectLifecyclePanel`;
- `_LifecycleButton`;
- route-provider, profile, lifecycle label helpers.

Target files:

- `features/connection/connection_details_screen.dart`
- `features/connection/runtime_mode_panel.dart`
- `features/connection/gateway_pairing_panel.dart`
- `features/connection/project_lifecycle_panel.dart`
- `features/connection/route_diagnostics_panel.dart`
- `features/connection/connection_controller.dart`

Acceptance:

- project shell calls one `ConnectionDetailsScreen` entrypoint;
- route diagnostics and lifecycle widget tests import connection feature
  helpers directly;
- connection code does not import chat widgets.

### A5: Test Harness Decomposition

Goal: keep tests readable as app features split.

Move from `widget_test.dart`:

- recording terminal transport and session into `test/support/recording_terminal.dart`;
- recording/fake gateway repositories into `test/support/fake_repositories.dart`;
- memory secure store into `test/support/memory_secure_store.dart`;
- widget interaction helpers into `test/support/widget_helpers.dart`;
- long conversation body/payload helpers into
  `test/support/conversation_fixtures.dart`.

Split tests:

- `test/project_home_widget_test.dart`
- `test/agent_chat_widget_test.dart`
- `test/connection_widget_test.dart`
- `test/notification_widget_test.dart`
- keep only cross-feature smoke-level assertions in one small shell test.

Acceptance:

- no widget test file over 500 lines;
- support fakes are reused by integration tests only when necessary;
- `flutter test` remains the main gate.

### A6: Transport Contract Cleanup

Goal: split large route/gateway DTO surfaces after UI extraction has reduced
churn.

Candidate split:

- `transport/gateway_transport.dart`
  stays the abstract interface;
- `transport/gateway_models.dart`
  health, device, project, lifecycle DTOs;
- `transport/gateway_terminal_models.dart`
  terminal handle, request, frames;
- `transport/gateway_message_models.dart`
  compatibility ask/message DTOs;
- `transport/gateway_route_models.dart`
  diagnostics/route-provider metadata if needed.

Acceptance:

- route-agnostic contract tests still prove route metadata does not leak into
  terminal/message schemas;
- message DTOs are clearly labeled compatibility, not default chat send.

## Recommended Sequence

1. A1 app bootstrap extraction.
2. A3 `PaneChatController` extraction first, even before full chat widget
   extraction, because current product risk is pane-backed chat correctness.
3. A3 remaining chat widget extraction.
4. A4 connection details extraction.
5. A2 project shell extraction.
6. A5 test decomposition.
7. A6 transport DTO cleanup.

Reasoning:

- Pane-backed chat is the newest and riskiest behavior; extracting its
  controller gives focused tests for send/retry/output without destabilizing
  shell layout.
- Project shell extraction touches the widest UI surface. It should happen
  after chat and connection leaf features have clear entrypoints.
- Transport DTO cleanup should wait until feature extraction reduces import
  churn.

## Implementation Rules

- One extraction package per commit.
- Lead does not directly land implementation packages by default. Lead owns
  package selection, worker dispatch, reviewer routing, plan-tree evidence,
  and acceptance.
- Workers own file edits, formatting, focused/full verification, and the
  implementation handoff for each package.
- Reviewers must review non-documentation implementation packages before
  acceptance, prioritizing bugs, behavioral regressions, missing tests, and
  architecture drift.
- No behavioral change in extraction commits unless explicitly marked.
- Move code first, then rename/refine.
- Preserve keys used by widget/integration tests.
- Preserve `ProjectHomeScreen` constructor shape until tests and debug profile
  seeding are migrated.
- Use `dart format` after each package.
- Run focused tests for touched feature plus full `flutter test`.
- Run AVD smoke after packages that touch:
  project shell, paired profile activation, selected-agent composer, raw
  terminal route, route diagnostics, lifecycle, or integration-test helpers.

## Verification Matrix

| Package | Minimum check | Full check |
| :--- | :--- | :--- |
| A1 | `flutter test test/widget_test.dart --plain-name "runtime modes expose only fake and paired gateway"` | `flutter test` |
| A2 | project shell/widget tests | `flutter test` + AVD smoke |
| A3 | agent chat widget tests + pane controller tests | `flutter test` + AVD smoke |
| A4 | connection/lifecycle/diagnostics widget tests | `flutter test` + AVD smoke if route/profile activation touched |
| A5 | split test files compile | `flutter test` |
| A6 | transport contract tests | `flutter test` + terminal smoke if terminal frame DTOs move |

## Risks

- Private widget extraction can create large import churn. Mitigation: move
  files under features with private names preserved first; rename after tests
  pass.
- Riverpod migration can become a rewrite. Mitigation: start controllers as
  plain Dart/ChangeNotifier-compatible classes, then wrap in providers only
  where it reduces constructor plumbing.
- Integration tests rely on stable `ValueKey`s. Mitigation: keys are part of
  the extraction contract.
- Pane chat session lifecycle can regress during extraction. Mitigation:
  create direct `PaneChatController` tests before moving more UI.
- Golden or screenshot tests are not present. Mitigation: keep AVD smoke as
  the UI regression gate for mobile and tablet paths.

## Acceptance Criteria For The Architecture Cleanup

- `app/lib/main.dart` is under 80 lines and contains only entrypoint-level
  wiring.
- No feature implementation file is over 500 lines without a written exception.
- Selected-agent pane-backed send path is covered outside a full
  `ProjectHomeScreen` widget test.
- Connection details/lifecycle/diagnostics can be tested without mounting the
  selected-agent timeline.
- Widget test files are split so no single file owns unrelated feature fakes.
- `flutter test` and local AVD smoke pass after the final package.

## Deferred

- Switching to a full Clean Architecture package stack.
- Replacing all `StatefulWidget` state with Riverpod in one pass.
- Splitting CCB source mobile gateway files.
- Reworking the relay protocol or terminal frame schemas.
- Introducing generated routes or code generation.
