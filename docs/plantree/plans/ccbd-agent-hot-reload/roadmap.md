# CCBD Agent Hot Reload Roadmap

Date: 2026-06-28

## Done

- Confirmed current daemon initialization loads `.ccb/ccb.config` once and
  injects the resulting object into registry, supervisor, supervision,
  completion tracking, dispatcher, project view, and project focus services.
- Confirmed the old keeper/CLI compatibility behavior treated config signature
  drift as a daemon restart trigger.
- Confirmed current namespace topology check escalates missing windows,
  changed agent pane membership, and missing sidebar panes into namespace
  recreation.
- Confirmed `[ui.sidebar.view]` is already a view-only hot-load precedent
  through `project_view`, but it does not cover agent/runtime topology.
- Recorded additive-first hot reload as the first supported target.
- Discussed the full dynamic load/unload/replace direction and recorded the
  main safety risks: handler lock contention, stale handler service captures,
  unbounded draining, unbounded pending replacement, and namespace patch drift.
- Established Phase 0 baseline diagnostics for control-plane handler latency,
  heartbeat steps, project-view work, process metrics, and reload placeholders.
- Introduced the Phase 1 config-bound service graph boundary used by startup,
  with graph version and created-at diagnostics.
- Added Phase 2 stable handler routing wrappers so request handlers resolve the
  current service graph at request time without a steady-state publish/read
  mutex.
- Added Phase 3 dry-run reload planning: `project_reload_config` accepts only
  `dry_run=true`, `ccb reload --dry-run` renders the no-mutation plan, and the
  classifier reports no-op, view-only, add, remove, replace, move/layout, and
  invalid-config cases without publishing a graph or touching tmux/runtime
  authority.
- Added Phase 4 bounded drain/retire state machinery: a pure drain queue model
  with timeout, pending-count, and age bounds, an explicit `reload-drain.json`
  store, injectable busy predicate transitions, retired terminal state, and
  dry-run drain intent suggestions for unload/replace plans. Phase 4 still does
  not publish a graph, patch namespace, mutate runtime authority, or execute
  tmux operations.
- Added Phase 5 namespace patch planning foundation: dry-run payloads now
  include a deferred namespace patch plan for view-only and additive
  add-agent/add-window classes, with required project/session/slot proofs,
  preserved-agent reporting, and explicit blocks for remove/replace/move/layout.
  Mutating apply, tmux writes, runtime authority writes, agent mounting, and
  service-graph publish remain deferred.
- Added Phase 6a additive apply design: documented the transaction order,
  rollback/diagnostic behavior, pane preservation proof, reusable existing APIs,
  and required narrow APIs before non-dry-run reload can be enabled.
- Added the Phase 6b first implementation step: a fake-backend-tested
  `add_window` namespace additive patch API that creates only new
  window/sidebar/agent pane evidence and remains disconnected from
  non-dry-run `ccb reload`.
- Added append-only `add_agent` namespace additive patch apply: it requires the
  new layout to expand the last existing agent pane, splits the new managed
  agent pane from that anchor, preserves old pane evidence, and remains
  disconnected from non-dry-run reload.
- Added the Phase 6b new-agent runtime mount helper: it calls the existing
  start-flow/runtime authority path only for namespace-patch-created agent
  panes, proves preserved runtime authority is unchanged, and remains
  disconnected from non-dry-run reload.
- Added the Phase 6b signature/publish transaction helper: after successful
  namespace patch and runtime mount results, it updates the current lease and
  mounted lifecycle config signature with holder/generation checks, then
  publishes the new service graph.
- Added the Phase 6b internal additive apply orchestrator: it builds the
  dry-run plan and target graph, accepts only `view_only_change`, append-only
  `add_agent`, and `add_window`, then runs namespace patch, runtime mount, and
  signature/publish transaction in order. Stage failures keep the old graph
  active and return pane/runtime residue diagnostics.
- Wired the Phase 6b additive apply orchestrator into the explicit user path:
  `project_reload_config(dry_run=false)` and plain `ccb reload` now attempt
  only `view_only_change`, append-only `add_agent`, and `add_window`.
  Non-additive classes still block at plan stage, CLI output includes stage,
  graph versions, diagnostics, and residue, and successful publish invalidates
  the project-view cache.
- Added the Phase 6b keeper handoff guard: plain `ccb reload` and accepted
  daemon-side non-dry-run additive apply with a changed config signature write a
  short-lived `reload-handoff.json` while disk config has the target signature
  but daemon ping may still report the old graph signature. Keeper accepts that
  mismatch only for the matching live daemon holder and stale or mismatched
  handoffs fail closed.
- Wired sidebar's refresh control and `r` shortcut to the same explicit
  non-dry-run reload path, then refresh project view after the response. This
  lets edited configs materialize new tmux panes/windows without adding a
  background config watcher.
- Enabled the first Phase 7 idle unload path for explicit `ccb reload`:
  deleting an agent from `[windows]` plans `remove_agent`, blocks before tmux
  mutation when that agent is busy or has outstanding dispatcher work, kills
  only the target managed pane, stops that agent runtime authority/helper, then
  publishes the new service graph through the existing lease/lifecycle
  transaction. Replacement, moves, arbitrary layout reshapes, and background
  config watching remain deferred.
- Changed keeper and CLI daemon compatibility checks so modern
  config-signature drift is treated as a reload-pending state instead of a
  restart trigger. Saving `.ccb/ccb.config` no longer interrupts the mounted
  daemon; explicit `ccb reload` or sidebar reload owns materializing the new
  panes/windows.
- Added the dynamic agent overlay command surface on top of the explicit reload
  transaction: `ccb agent add ... --window/--window-class/--loop-id/--node-id`
  writes runtime lifecycle records without rewriting `.ccb/ccb.config`, then
  uses guarded reload to append a pane or create a managed window when the
  daemon is mounted.
- Added safe dynamic agent release on top of the idle `remove_agent` reload
  path: `ccb agent remove ... --policy unload --idle-only` and
  `ccb agent release ... --policy auto|hide|park|unload` retain busy agents,
  unload idle dynamic runtime authority, close only the target pane, clear the
  active `pane_id` while preserving `last_pane_id`, and remove empty dynamic
  windows.
- Verified controlled mounted tmux dynamic lifecycle smokes from
  `/home/bfly/yunwei/test_ccb2`: existing-window add/remove with busy retain,
  new-window add/remove with empty-window cleanup, and a same-window
  `1->6->1` dynamic agent cycle that preserved `%1:main` and returned
  `known_agents` to `['main']`.
- Added long-lived dynamic role parking semantics: `ccb agent hide`,
  `ccb agent park`, and `ccb agent resume` now update dynamic lifecycle state;
  `park` projects `dispatch_disabled=true`, publishes a config-only
  `view_only_change`, preserves the existing pane/runtime context, rejects
  direct dispatch, and `resume` re-enables dispatch without tmux mutation.
- Verified the dispatch-disabled slice with `150 passed` across
  `test/test_agent_lifecycle_cli.py`, `test/test_v2_config_loader.py`, and
  `test/test_v2_ccbd_dispatcher.py`; reload-related focused tests passed with
  `70 passed`. External source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-smoke-1782474327` proved existing-window
  add, ask, park rejection, resume ask, new-window add, ask, idle release,
  empty-window cleanup, and return to `known_agents: ['main']`.
- Closed the startup-to-hotload pane identity bridge for compact configs and
  structured/fake providers: legacy startup now stamps the logical default
  window on tmux pane identity, and non-stale namespace-assigned panes are
  written back to runtime authority even when the provider has no session
  binding. Source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-real-1782476922` proved startup
  `@ccb_window=main`, existing-window `add_agent`, new-window `add_window`,
  and ask submission without manual pane seeding. Source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-unload-1782477435` proved explicit
  `remove --policy unload --force` removes the dynamic pane, stops runtime
  authority, removes empty dynamic windows, and returns the project to only
  `main`.
- Verified the no-manual-seeding same-window cycle after the compact startup
  bridge fix in `/home/bfly/yunwei/test_ccb2/hotload-cycle-auto-1782482877`:
  dynamic panes grew from `%1:main` to
  `%1:main,%2:dyn1,%3:dyn2,%4:dyn3,%5:dyn4,%6:dyn5`, each dynamic agent
  accepted ask submission, then `remove --policy unload --force` shrank the
  window back to only `%1:main` with runtime authority showing only `main`.
- Added and verified batch dynamic lifecycle release coverage:
  `ccb agent release --agents ...` can release a group of idle dynamic agents
  through one guarded reload transaction, including namespace/runtime cleanup
  evidence in the default fake-provider dynamic layout CI bundle
  (`231e30b8`).
- Added and verified batch move placement by window class: `ccb agent move
  --agents ... --window-class review|loop|node` can place a group of existing
  panes into class-derived target windows without rewriting static
  `.ccb/ccb.config`, and the smoke flow proves source-window cleanup plus ask
  reachability after the move (`ec9d488d`).
- Added and verified execution-node batch move smoke: `ccb agent move
  --agents worker,checker --loop-id round1 --node-id node1 --json` moves an
  existing worker/checker pair into `node-round1-node1`, removes the evacuated
  source window, preserves pane identity, and keeps ask submission reachable
  after the transaction (`24bbad5f`).
- Added and verified mixed move-plus-add explicit `[windows]` reload: one
  `ccb reload` transaction can create a new target window, move existing panes
  into it, append a newly-created agent pane after the moved anchors, remove
  the evacuated source window, mount the new agent runtime authority, update
  moved-agent runtime authority, and keep ask submission reachable for moved
  and new agents. Unit coverage includes existing-target and new-target
  namespace plans/apply plus combined moved-and-mounted runtime updates; source
  wrapper smoke
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-mixed-move-add-latest.json`
  passed for `mixed-move-add`.
- Ran the first real-account live provider smokes for dynamic pane movement
  and same-window growth/shrink:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-move-agent-latest.json`
  passed for `codex` with `move-agent`;
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-same-window-continuous-latest.json`
  passed for `codex` with `same-window-continuous` (`1->6->1`);
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-move-agent-latest.json`
  passed for `claude` with `move-agent`;
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-same-window-continuous-latest.json`
  passed for `claude` with `same-window-continuous` (`1->6->1`). Together
  these prove pane-backed managed Codex and Claude agents can remain
  ask-reachable after move transactions, and both providers can survive
  same-window dynamic add/reflow/unload cycles while preserving the original
  main pane.
- Extended live-provider evidence to multi-window batch release:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-batch-release-latest.json`
  passed for `codex` with `batch-release`;
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-batch-release-latest.json`
  passed for `claude` with `batch-release`. Together these prove a real
  provider session can add a survivor helper to an existing window, add two
  helpers into new windows, batch-unload two dynamic helpers, remove the empty
  dynamic windows, preserve the survivor pane, and keep survivor/main asks
  reachable after the release transaction.
- Extended live-provider evidence to higher-stress explicit `[windows]` flows:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-window-class-continuous-latest.json`
  and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-window-class-continuous-latest.json`
  passed `window-class-continuous` (`1->8->1` across `plan-orchestrate` and
  `plan-orchestrate-2`);
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-mixed-move-add-latest.json`
  and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-mixed-move-add-latest.json`
  passed `mixed-move-add`; and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-batch-move-window-class-latest.json`
  plus
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-batch-move-window-class-latest.json`
  passed `batch-move-window-class`. Together these prove real Codex and Claude
  sessions can grow a window-class to a second window and shrink it back, mix
  pane moves with newly-mounted agents in one reload transaction, batch-move
  dynamic agents into class-derived target windows, preserve moved pane ids,
  remove evacuated dynamic windows, and keep moved/new agents ask-reachable.
- Extended live-provider evidence to explicit arrange/reflow recovery:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-arrange-window-latest.json`
  and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-arrange-window-latest.json`
  passed `arrange-window`. These prove real Codex and Claude sessions can
  survive an intentionally disturbed `plan-orchestrate` pane layout, restore the
  fixed-column target geometry with `ccb agent arrange`, preserve pane ids and
  agent order, keep a helper ask-reachable after arrange, then unload helpers
  back to the static `frontdesk` plus `planner` topology.
- Extended live-provider evidence to the shared-source move edge case:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-move-shared-source-latest.json`
  and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-move-shared-source-latest.json`
  passed `move-shared-source`. These prove real Codex and Claude sessions can
  move one dynamic helper out of a source window that still contains another
  helper, keep the source window alive, preserve both moved and staying pane ids,
  keep both helpers ask-reachable after the move, move the helper back, and only
  remove the source window after the final helper is released.
- Extended live-provider evidence to resolve/preflight and loop capacity:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-resolve-preflight-latest.json`
  and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-resolve-preflight-latest.json`
  passed `resolve-preflight` with real dynamic providers and fake static filler
  panes. These prove window-class overflow resolution predicts
  `plan-orchestrate-2`, the subsequent real provider `agent add` matches the
  resolved target, release removes the overflow window, execution-node
  resolution predicts `node-round3-node1`, `loop capacity ensure` creates the
  real worker/reviewer node window, and `loop capacity release` removes it.
- Promoted the fake-provider core dynamic layout smoke into the regular
  Ubuntu/Python 3.11 CI gate as `Guard core dynamic layout smoke`, backed by
  `scripts/guarded_core_dynamic_layout_smoke.py`. The guard covers
  `same-window-continuous`, `batch-release`, `move-agent`, `move-shared-source`,
  `window-class-continuous`, `arrange-window`, `mixed-move-add`,
  `batch-move-window-class`, and `resolve-preflight`, while keeping real
  Codex/Claude runs as guarded manual/release evidence. Guard script, workflow
  text coverage, and dynamic layout script tests passed with
  `pytest -q test/test_dynamic_layout_smoke_script.py
  test/test_guarded_dynamic_layout_provider_smoke_script.py
  test/test_guarded_core_dynamic_layout_smoke_script.py` (`49 passed`), and the
  source-wrapper guard fake smoke
  `/home/bfly/yunwei/test_ccb2/guarded-core-dynamic-layout-local-latest.json` passed
  all nine flows with `dynamic_layout_smoke_status: ok`.
- Verified dynamic lifecycle policy smoke for park/resume and auto release:
  `pytest -q test/test_dynamic_agent_lifecycle_smoke_script.py` passed with
  `5 passed`; source-wrapper fake smoke
  `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-fake-latest.json`
  passed; CI-gate-equivalent fake smoke
  `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-ci-gate-latest.json`
  passed; real-home Codex smoke
  `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-codex-latest.json`
  passed; real-home Claude smoke
  `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-claude-latest.json`
  passed. The lifecycle smoke proves long-lived planner helpers auto-park,
  reject dispatch while parked, preserve pane identity through resume, regain
  ask reachability after resume, while short-lived reviewer helpers auto-unload
  and clean layout/runtime state.
- Promoted the dynamic lifecycle smoke into the Ubuntu/Python 3.11 test
  workflow as `Guard dynamic agent lifecycle smoke`, with workflow text
  coverage in `test/test_dynamic_agent_lifecycle_smoke_script.py`. This makes
  fake-provider park/resume/auto-unload behavior part of the regular CI gate.
- Added the first bounded busy-unload bridge: non-dry-run `remove_agent` still
  blocks before namespace mutation when the target agent is busy or has
  outstanding work, but now records an active unload drain in
  `.ccb/ccbd/reload-drain.json`, exposes drain diagnostics in the blocked
  payload, rejects new dispatcher work for draining agents, and retires the
  drain record after a later idle retry successfully unloads the agent.
  Focused verification passed with
  `pytest -q test/test_ccbd_reload_drain.py test/test_ccbd_reload_apply.py test/test_v2_ccbd_dispatcher.py`
  (`78 passed`).
- Exposed active busy-unload drain status through `project_reload_config` /
  `ccb reload --dry-run` / `ccb reload`: reload payloads now include
  `reload_drains.active_records`, the CLI renders active drain count, agent,
  phase/status, bounded deadlines, and the explicit retry command (`ccb
  reload`). Focused verification passed with
  `pytest -q test/test_ccbd_reload_drain.py test/test_ccbd_reload_apply.py test/test_v2_cli_render.py`
  (`76 passed`) and
  `pytest -q test/test_ccbd_reload_dry_run.py test/test_ccbd_reload_patch.py`
  (`42 passed`).
- Re-ran an external source-wrapper fake provider lifecycle smoke from
  `/home/bfly/yunwei/test_ccb2` using current source `ccb_test`:
  `scripts/dynamic_agent_lifecycle_smoke.py --provider fake --project-name
  dynamic-agent-lifecycle-drain-status-smoke --reset` passed with
  `dynamic_agent_lifecycle_smoke_status: ok`, covering dynamic add, ask,
  park/reject, resume/ask, short-lived reviewer unload, planner cleanup,
  layout cleanup, and final `kill`.
- Exposed active reload drain state in `project_view` for sidebar/orchestrator
  consumers: the view now includes top-level `reload_drains`, affected agent
  rows carry `reload_drain` and `dispatch_blocked_by_reload_drain=true`, and
  the project-view cache key includes the `reload-drain.json` file revision so
  a long TTL cannot hide newly recorded or retired drains. Focused
  verification passed with `pytest -q test/test_ccbd_project_view.py`
  (`67 passed`) plus the reload/drain/dispatcher slice
  `pytest -q test/test_ccbd_reload_drain.py test/test_ccbd_reload_apply.py test/test_v2_cli_render.py test/test_v2_ccbd_dispatcher.py::test_dispatcher_rejects_targets_with_active_reload_drain`
  (`77 passed`).
- Added a fake-provider external smoke for the explicit `[windows]`
  busy-remove path: `scripts/reload_busy_drain_smoke.py` starts a two-agent
  project, submits a long-running fake job to `agent2`, edits `.ccb/ccb.config`
  to remove `agent2`, proves `ccb reload` blocks and records an active drain,
  proves `project_view` exposes the same drain, proves new `ask agent2` work is
  rejected while draining, waits for the original job to finish, retries
  `ccb reload`, and proves `agent2` disappears from project view. The smoke is
  promoted to the Ubuntu/Python 3.11 CI gate as `Guard reload busy drain smoke`.
  The same slice fixed CLI `ask` target resolution so a target removed from the
  disk config but still present as an active reload drain is submitted to the
  mounted daemon and rejected with the precise draining diagnostic instead of
  the misleading local `unknown agent` error. Verification passed with
  `pytest -q test/test_v2_ask_service.py test/test_reload_busy_drain_smoke_script.py`
  (`36 passed`), the reload/project-view focused slice (`67 passed` +
  `77 passed`), and external source-wrapper fake smoke
  `scripts/reload_busy_drain_smoke.py --provider fake --project-name
  reload-busy-drain-smoke --reset` from `/home/bfly/yunwei/test_ccb2`.
- Added daemon heartbeat auto-retry for ready active unload drains: after
  completion polling shows the draining agent has no outstanding work, heartbeat
  reuses the guarded additive reload transaction for the current disk
  `remove_agent` plan and retires the drain through the existing unload path.
  Busy drains remain waiting, and stale ready drains are retired when the user
  restores the agent in `.ccb/ccb.config` before auto-retry. Verification
  passed with `pytest -q test/test_ccbd_reload_drain_auto_retry.py
  test/test_reload_busy_drain_smoke_script.py` (`9 passed`), the reload/drain
  focused slice (`80 passed`), project-view/heartbeat lock checks (`69
  passed`), `pytest -q test/test_v2_ask_service.py` (`30 passed`), and external
  source-wrapper fake smoke
  `scripts/reload_busy_drain_smoke.py --provider fake --auto-retry
  --project-name reload-busy-drain-auto-retry-smoke --reset` from
  `/home/bfly/yunwei/test_ccb2`.
- Closed the first sidebar drain visibility gap: the Rust sidebar helper now
  parses `reload_drain` and `dispatch_blocked_by_reload_drain` from
  `project_view` agent rows and renders draining agents with a warning-colored
  `drain:<status>` marker. Verification passed with `cargo fmt
  --manifest-path tools/ccb-agent-sidebar/Cargo.toml --check`,
  `cargo test --manifest-path tools/ccb-agent-sidebar/Cargo.toml` (`73
  passed`), and external source-wrapper fake smoke
  `scripts/reload_busy_drain_smoke.py --provider fake --project-name
  reload-busy-drain-sidebar-visibility --reset` from
  `/home/bfly/yunwei/test_ccb2`, which proved active drain recording, ask
  rejection while draining, retry publish, and final drain cleanup.
- Added a repeatable true tmux sidebar pane capture to the busy-drain smoke:
  `scripts/reload_busy_drain_smoke.py --check-sidebar-render` widens the test
  sidebar, waits for a blocked active drain, captures the live sidebar pane, and
  requires the rendered `drain:waiting` marker before allowing the smoke to
  pass. Verification passed with `pytest -q
  test/test_reload_busy_drain_smoke_script.py` (`9 passed`), `python -m
  py_compile scripts/reload_busy_drain_smoke.py`, `cargo build --release
  --manifest-path tools/ccb-agent-sidebar/Cargo.toml` so the source wrapper
  used the updated helper, and external source-wrapper fake smoke
  `scripts/reload_busy_drain_smoke.py --provider fake --project-name
  reload-busy-drain-sidebar-render --busy-latency-ms 15000
  --check-sidebar-render --reset` from `/home/bfly/yunwei/test_ccb2`, which
  passed all checks including `sidebar_renders_active_drain`.
- Added the first replace-agent apply boundary: non-dry-run `replace_agent`
  reloads now return a structured `replace_agent_deferred` plan-stage blocker
  instead of a generic unsupported-plan message. The payload includes affected
  `replace_agents`, planned replace drain intents, and a CLI-rendered
  `next_supported_action`, while still avoiding namespace patch, runtime
  mutation, service-graph publish, or persistent drain records. Verification
  passed with `pytest -q test/test_ccbd_reload_apply.py
  test/test_ccbd_reload_drain.py test/test_ccbd_reload_dry_run.py
  test/test_v2_cli_render.py` (`99 passed`) and `python -m py_compile
  lib/ccbd/reload_apply_plan.py lib/cli/render_runtime/reload_view.py`.
- Landed the first idle `replace_agent` mutation slice: pure existing-agent
  provider/spec replacement now plans a same-slot runtime replacement, skips
  tmux namespace mutation, stops old runtime authority, respawns the new
  provider in the original pane, publishes the new service graph/signature, and
  reports `replaced_agents`. Busy replacement records a bounded `replace`
  drain and leaves namespace/runtime/publish untouched; a later manual idle
  retry reuses the same replacement path and retires the active replace drain.
  A real source-wrapper smoke in `/home/bfly/yunwei/test_ccb2` proved
  `fake-codex -> fake-claude` same-slot replacement publishes, preserves pane
  `%1`, updates layout status to the new provider, and keeps `ask` reachable.
  Verification passed with `PYTHONPATH=lib pytest -q test/test_ccbd_reload_apply.py
  test/test_ccbd_reload_patch.py test/test_ccbd_reload_drain.py
  test/test_ccbd_reload_dry_run.py test/test_ccbd_reload_runtime_mount.py
  test/test_ccbd_reload_transaction.py test/test_v2_cli_render.py
  test/test_v2_cli_router.py` (`212 passed`) and external source-wrapper smoke
  `scripts/guarded_core_dynamic_layout_smoke.py --test-root
  /home/bfly/yunwei/test_ccb2 --ccb-test
  /home/bfly/yunwei/ccb_source/ccb_test --provider fake --project-prefix
  core-dynamic-layout-replace-safety --reset`, which passed all guarded core
  dynamic layout checks.

## In Progress

- Phase 6/7 explicit mutating reload and dynamic lifecycle are in hardening:
  accepted user-path classes are implemented for view-only, append-only
  add-agent/add-window, idle remove-agent, runtime dynamic add, runtime dynamic
  release, busy retain, empty dynamic-window cleanup, config-only park/resume
  dispatch toggling, compact-startup pane identity preservation, bounded
  busy-unload drain recording/status surfacing in reload and project-view
  surfaces, heartbeat auto-retry for ready unload drains, batch release, batch
  move into explicit review/loop/node windows, and mixed move-plus-add explicit
  `[windows]` reload. Live `codex` and `claude` move, same-window `1->6->1`,
  lifecycle park/resume, multi-window batch-release, window-class-continuous,
  mixed move-plus-add, batch window-class move, arrange-window, and
  shared-source move, plus resolve/preflight loop-capacity smokes have passed;
  the core fake-provider dynamic layout bundle is now a CI gate. Sidebar helper
  now renders active drain status from `project_view`, and a true tmux pane
  capture smoke verifies the marker in a running sidebar. Pure idle
  replace-agent mutation is implemented for same-slot respawn and publish, and
  busy replace has bounded drain plus manual idle-retry cleanup. Automatic
  heartbeat retry for ready replace drains, daemon-pushed sidebar refresh,
  arbitrary layout reshapes, and background config watching remain deferred.

## Next

1. Watch the first remote CI run for the expanded `Guard core dynamic layout
   smoke` gate. If runtime or flake rate is too high, split the nine fake flows
   into a stable core gate and an edge-flow gate rather than weakening
   assertions.
2. Run or update the automatic and manual additive reload matrix in
   [topics/test-matrix.md](topics/test-matrix.md), including `test_ccb2`
   evidence for unchanged old panes, newly-mounted agents, released dynamic
   panes, moved panes, mixed move-plus-add transactions, and empty-window
   cleanup. The fake busy-remove drain path now has a dedicated CI smoke; the
   next matrix expansion should decide whether a guarded real-provider variant
   is useful or too slow for routine gates.
3. Extend the busy `replace_agent` drain path with heartbeat-driven retry
   execution, using the landed same-slot replacement path once the active
   replace drain becomes idle-ready.
4. Keep daemon-pushed sidebar refresh deferred unless a real tmux visual check
   shows project-view polling is too slow for drain/reload state changes.

## Deferred

- Pane-preserving arbitrary layout reshuffle.
- Background file watching of `.ccb/ccb.config`.
- General `ccbd` control-plane performance optimization.
- Automatic replace of indefinitely busy agents without user policy.
- Cross-window movement of busy panes.
