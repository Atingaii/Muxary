# Sidebar Provider Activity Roadmap

Date: 2026-05-27

## Done

- Diagnosed that current sidebar activity mostly uses CCB job state, runtime
  health, pane liveness, and pane text heuristics.
- Confirmed Claude CCB-managed jobs can already terminalize some API errors
  through session event log handling, but manual pane activity is not wired into
  sidebar status.
- Inspected `tmux-agent-status` and recorded the useful hook-status pattern:
  provider hooks write small scoped status files and UI reads aggregated state.
- Decided not to import `tmux-agent-status` as a tmux plugin or global scanner.
- Drafted the Codex activity topic and shared validation matrix under this
  plan-tree root.
- Documented current `ccbd` Comms status, message-bureau lineage, automatic
  retry, manual retry, and recovery behavior in
  [topics/current-ccbd-comms-and-retry.md](topics/current-ccbd-comms-and-retry.md).
- Added a dedicated mailbox-internal design reference index in
  [topics/mailbox-internal-design-references.md](topics/mailbox-internal-design-references.md)
  so future status work does not confuse sidebar Comms rows with mailbox-kernel
  policy.
- Recorded that provider-native activity is the execution-state authority, while
  CCB job/Comms state remains workflow metadata.
- Recorded that provider `failed` should remain sticky until the next provider
  turn or runtime ownership change.

## In Progress

- Define and implement the phase-1 provider status bridge in
  [topics/phase-1-provider-status-to-sidebar.md](topics/phase-1-provider-status-to-sidebar.md):
  provider hook/session facts -> agent runtime activity artifact ->
  `project_view` agent row -> sidebar symbol.
- Shape the broader Agent Runtime Status v1 path in
  [topics/agent-runtime-status-v1.md](topics/agent-runtime-status-v1.md):
  generic source-side evidence merging first, then Codex and Claude
  provider-specific status adapters, then mobile gateway consumption.
- Define the independent Codex pane-status probe in
  [topics/codex-pane-status-probe-spike.md](topics/codex-pane-status-probe-spike.md):
  run Codex in a disposable tmux pane under `/home/bfly/yunwei/test_ccb2`,
  measure `pipe-pane`/`capture-pane`/pane facts, and produce explicit-evidence
  fixtures before production parser work.
- Added the first standalone pane-only demo probe at
  `scripts/probe_codex_pane_status.py` with parser/turn-timing unit tests in
  `test/test_codex_pane_status_probe.py`.
- Extended the Codex pane probe with direct pane stimulus, adaptive sampling,
  and authenticated
  `/home/bfly/yunwei/test_ccb2` evidence for startup/auth baseline,
  quick-turn `unknown -> working -> unknown`, long text,
  long tool `working -> tool_running`, historical interrupt recovery, pane
  death, and network-proxy failure.
- Added pane-derived turn timing based on the probe submit clock:
  first-active latency, last-active elapsed time, terminal elapsed time, and
  terminal outcome/reason.
- Split auth/API/config failures out of generic waiting/failed states in the
  Codex pane probe. Isolated no-login runs now classify as `auth_required`, and
  run-local bad provider config runs classify request-route failures as
  `api_error`.
- Added pane-probe stability/overhead metrics and transition-only event output.
  The 2026-06-29 stress pass covered startup, short turn, long streaming text,
  long/short tool use, API route failure, no-login auth, ESC during tool work,
  and pane death with zero 1 s flicker transitions in the recorded runs.
- Removed visible Codex input prompt and pane quiet as completed-turn signals.
  Without `Worked for ...` or another hard marker, pane-only status remains
  non-terminal.
- Removed prompt-derived idle, low-confidence `streaming_answer`, `stalled`,
  queued hard-state parsing, Codex UI timer fields, reconnect retry fields, and
  `status-elapsed` interrupt triggering from the minimal pane parser.
- Removed `confidence`, `last_output_age_s`, `Conversation interrupted` as a
  current state, and `pane_quiet_after_active` completion from parser/runtime
  output.
- Removed built-in `scenario`, fault injection, ESC injection, and pane-death
  action branches from the main probe; those lanes now require external/manual
  stimulus while the probe observes.
- Added Codex `Worked for ...` terminal-summary parsing as a sufficient
  completed-turn signal for the pane probe.
- Classified `Reconnecting... n/m (... esc to interrupt)` as an active,
  recoverable Codex state that wins over nearby stream-disconnected error text;
  the retry count and visible seconds are not lifecycle signals.
- Hardened active-state parsing so `working`, `tool_running`, and
  `reconnecting` require Codex status-line shaped rows; conversation text or
  indented examples containing the same keywords remain `unknown`.
- Removed post-send Enter retry from the prompt stimulus path. The probe now
  sends at most one prompt and one submit key, then only observes.
- Removed the obsolete `raw_status`/published-status dual track. Events,
  snapshots, and metrics now use the single pane parser status stream.
- Covered Codex hollow-bullet `◦ Booting MCP server: ...` active rows from the
  latest real pane artifact and removed duplicated working-line regex
  bookkeeping.
- Coworker review `job_b10ad02f41f4` scored the pane-only Codex status probe
  simplicity `9.5/10` and accuracy `9/10`, found no required remaining
  branch/fallback deletion, and approved marking demo v1 converged.
- Recorded a post-hardening quick-turn artifact under
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T080801Z-3478011/artifacts/run.json`:
  `unknown -> working -> unknown`, capture p95 1.6 ms, zero 1 s flicker
  transitions, and no terminal completion without `Worked for ...`.
- Drafted the production extraction plan in
  [topics/provider-pane-status-signal-module.md](topics/provider-pane-status-signal-module.md):
  first land `provider_pane_status.models` and `provider_pane_status.codex_pane`,
  keep pane observations separate from job lifecycle authority, and defer
  resolver/adapter abstraction until Claude or a second consumer needs it.
- Landed the PR1 extraction slice: `lib/provider_pane_status/models.py` and
  `lib/provider_pane_status/codex_pane.py` now own the strict Codex pane parser,
  while `scripts/probe_codex_pane_status.py` imports it and no longer carries
  local Codex regex duplicates.
- Verified PR1 with `python -m py_compile` for the probe and new package, plus
  `python -m pytest -q test/test_provider_pane_status_codex.py
  test/test_codex_pane_status_probe.py` (`32 passed`). The new module tests
  keep body-text `Working` as `unknown`, expose `Worked for ...` as observation
  only, and assert the script imports the shared parser.
- Ran live `/home/bfly/yunwei/test_ccb2` probe evidence after extraction:
  `run-20260629T133020Z-2455185` observed
  `unknown -> working -> unknown`, capture p95 1.6 ms, zero 1 s flicker
  transitions, and no terminal completion without `Worked for ...`;
  `run-20260629T133248Z-2540939` observed isolated no-login
  `unknown -> auth_required`, capture p95 1.5 ms, zero flicker transitions.
- Captured a startup bad-config boundary in
  `run-20260629T133335Z-2576972`: pipe output contained explicit
  `Error loading config.toml`, but the tmux pane/server died before
  `capture-pane` could read the text, so the strict status stream reported
  `pane_dead`. This remains an explicit follow-up source-acquisition question,
  not a parser fallback.
- Added the first explicit session-supplement slice: `codex_session.py` reads
  only the managed Codex session root, recognizes `task_started` as `working`
  and `task_complete` as runtime `free`, and keeps assistant text without a
  task boundary as `unknown`.
- The probe now records `status` as pane-only evidence plus
  `session_status` and `runtime_status` as separate fields. Runtime `free`
  does not rewrite pane `unknown`; it is a second-source conclusion.
- Verified session-supplement behavior with
  `python -m pytest -q test/test_provider_pane_status_codex.py
  test/test_provider_pane_status_codex_session.py
  test/test_codex_pane_status_probe.py` (`49 passed`) and live
  `/home/bfly/yunwei/test_ccb2` evidence:
  `run-20260629T141909Z-4154029` observed runtime
  `unknown -> working -> free` while pane evidence remained
  `unknown -> working -> unknown`; terminal timing closed at 2.285 s from
  `codex_session_task_complete`.
- Verified that explicit pane conditions still win over session-derived free:
  nonexistent pane observation stayed `pane_dead`, and a new untrusted workdir
  stayed `waiting_for_user` instead of becoming `free`.
- Added bounded runtime stabilization so display state no longer exposes
  short-lived soft jumps: startup session `free` is grace-held until the pane
  settles, recent active work is held over brief `free`/`unknown` gaps, and
  short empty captures reuse the prior stable active/free state. Raw runtime,
  pane, and session signals remain recorded separately in snapshots and metrics.
- Verified stabilization with live evidence:
  `run-20260629T143303Z-455718` collapsed the prior startup jump into stable
  `unknown -> working -> free` while raw state was recorded separately, and
  `run-20260629T143329Z-468685` delayed the final `free` transition by the
  active hold window so the task lane stayed `unknown -> working -> free`
  without `working -> free -> working` style oscillation.
- Tightened the post-review stabilizer implementation after coworker review
  `job_2578d60d2d46` timed out: runtime catalog no longer lists display-state
  `completed`, prompt submission is blocked for already-active panes, and
  `empty_capture` hold is bounded by a dedicated empty-capture start time.
- A smaller coworker follow-up, `job_c54b68ed7ac2`, returned upstream 429 after
  retries were exhausted and provided no review findings; the current
  acceptance evidence is local tests plus live pressure runs.
- User decision on 2026-06-29: do not block this slice on further coworker
  review; proceed with local verification and live pressure evidence.
- Re-ran live pressure checks after cleanup: `run-20260629T144549Z-901054`
  surfaced `waiting_for_user`; `run-20260629T144608Z-910979` and
  `run-20260629T144656Z-947753` both stayed `unknown -> working -> free`;
  high-frequency `run-20260629T144755Z-990498` sampled at 9.65/s with 242
  captures, p95 capture 1.7 ms, and zero flicker; isolated no-login
  `run-20260629T144836Z-1012045` surfaced `auth_required`.
- Added runtime `start` for the post-submit/pre-first-signal interval. It is a
  display stabilizer state only: raw pane/session/runtime evidence remains
  recorded separately and `start` does not mean `free` or real `working`.
- Final no-review smoke `run-20260629T152132Z-2210496` stayed
  `start -> working -> free` while raw runtime stayed
  `unknown -> working -> free`; it ended at runtime `free` from
  `codex_session_task_complete`, had zero flicker transitions, and measured
  p95 capture latency at 1.8 ms.
- Landed Codex ProjectView/sidebar coverage: ProjectView now publishes
  `provider_runtime_status` for Codex rows and explicit sidebar
  `activity_symbol`/`activity_color` overrides from the strict runtime state.
  Codex `start`, `working`, `tool_running`, `reconnecting`, `free`, known
  failures, and `unknown` now drive the agent row directly.
- Disabled legacy Codex pane keyword/prompt/error heuristics in the activity
  resolver. The generic prompt/keyword helpers remain available only for
  non-Codex providers until Claude receives a strict parser, and Codex prompt
  visibility no longer marks comms as recoverable stuck work.
- Verified the sidebar integration slice with
  `python -m py_compile lib/ccbd/project_view/activity.py
  lib/ccbd/project_view/service.py` and
  `python -m pytest -q test/test_ccbd_project_view.py` (`71 passed`).

## Next

- Capture a live reconnect/stream-disconnect lane matching the observed
  `Reconnecting... n/m (... esc to interrupt)` pane text; fixture coverage now
  treats it as recoverable active state.
- Add or capture an interruption lane with a current hard marker if Codex has
  one; visible `Conversation interrupted` copy alone is now treated as
  historical pane text.
- Add a real invalid-key `auth_failed` lane when it can be produced without
  mutating the user's persistent Codex home; fixture coverage exists, while
  current live auth coverage is `auth_required` and route-level `api_error`.
- Capture a live `Worked for ...` artifact from the Codex rendering mode that
  shows terminal summaries; current parser coverage is fixture-backed, while
  the latest quick-turn pane capture did not display that line.
- Decide whether fast-startup-exit stderr/pipe output is a separate
  `source_status=error` acquisition source for ProjectView, or whether strict
  current-screen `pane_dead` remains the only pane-death signal for ProjectView.
- Add Claude status parsing for scheduled tasks, shell/tool still running,
  permission/input waiting, API/auth/model errors, and Stop-with-background
  work.
- Update mobile gateway status summaries to derive from `activity_state` and
  `runtime_status`, not a coarse agent state fallback.
- Run the validation matrix in [topics/test-matrix.md](topics/test-matrix.md),
  including live `/home/bfly/yunwei/test_ccb2` stable and fault lanes.

## Deferred

- Codex app-server as a future transport backend.
- Process-tree polling fallback except as bounded diagnostics.
- Sidebar detail popups for provider reason text.
- Cross-project provider activity aggregation.
- Structured `AgentRuntimeStatus`, generic resolver tests, and
  smoothing/hysteresis until a second provider or second consumer creates a
  real composition need.

## Release Gate

This work is release-ready only when:

- manual Codex and Claude work no longer appears idle while active;
- ProjectView clients can show structured working/waiting/reconnecting/unknown
  detail without parsing provider pane text themselves;
- lifecycle/runtime ownership remains the hard guard, CCB job/Comms facts remain
  workflow metadata, and provider evidence owns execution-state labels;
- CCB job-only `running` without fresh provider progress cannot keep an agent
  `working` forever;
- API/auth/model failures surface as failed or recoverable pending states;
- no stale activity can keep an agent active forever;
- rapid `project_view` refreshes do not make visible status flicker between
  active and unknown/completed for the same unresolved provider state;
- `project_view` refresh CPU cost and pane capture frequency remain bounded;
- the Codex parser is backed by sanitized probe fixtures rather than guessed
  provider pane copy;
- live fault-lane tests have been recorded for disconnect, invalid auth, and
  unavailable model.
