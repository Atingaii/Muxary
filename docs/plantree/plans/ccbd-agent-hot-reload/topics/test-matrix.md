# Test Matrix

Date: 2026-05-29

## Automated Unit Tests

- Reload no-op:
  - old and new config identities match;
  - no namespace mutation;
  - no runtime authority writes;
  - project view cache is invalidated only if needed.
- Reload dry-run:
  - diff classes are returned;
  - no tmux commands are issued;
  - no graph is published;
  - no lifecycle or lease signature changes.
  - Phase 3 covered classes: `no_change`, `view_only_change`, `add_agent`,
    `add_window`, `remove_agent`, `replace_agent`, `move_agent`, `layout_change`,
    and `invalid_config`;
  - `ccb reload --dry-run` renders daemon payloads and returns non-zero for
    invalid-config dry-run results;
  - plain `ccb reload` is not a dry-run and is allowed only for the gated
    additive classes below.
  - Phase 4 dry-run payloads may include bounded `drain_intents` suggestions
    for `remove_agent` and `replace_agent`, but they remain no-mutation plans
    with `safe_to_apply=false`.
  - dry-run payloads surface active `reload_drains` from the bounded drain
    store when a prior busy unload is waiting, including retry guidance without
    mutating tmux/runtime/lifecycle/service graph.
  - Phase 5 dry-run payloads include `namespace_patch_plan` for view-only and
    additive classes; the plan is `apply_deferred=true` /
    `mutation_enabled=false` and does not call tmux or publish a graph.
- Namespace patch planning:
  - add-agent append plans one `create_agent_pane` step and reports existing
    agents as preservation-gate inputs, not as already-proven reused panes;
  - add-window plans `create_window`, optional `create_sidebar_pane`, and
    `create_agent_pane` steps for the new window only;
  - view-only plans only project-view/sidebar refresh intent, not tmux
    namespace mutation;
  - `remove_agent` plans `kill_agent_pane` steps for idle unload; replace,
    move, and arbitrary layout changes remain blocked for non-dry-run mutation;
  - additive planning requires verified project id, tmux socket, session,
    namespace epoch, window, role, slot key, and `managed_by=ccbd` proof before
    future apply;
  - planner tests monkeypatch app mutation paths and prove no tmux, namespace,
    runtime authority, service-graph publish, provider start/stop, heartbeat
    scan, or config watch is introduced.
- Phase 6a design contract:
  - document that `ensure_project_namespace(topology_plan=...)` is not the
    additive apply entrypoint because it may recreate the namespace;
  - document transaction order: namespace patch, new runtime mount,
    lease/lifecycle signature update, service graph publish, project view/sidebar
    refresh;
  - document that graph publish is forbidden after any failure before the publish
    step;
  - document the keeper config-signature race and require Phase 6b handoff
    tests before additive non-dry-run reload can publish;
  - document the before/after pane-id proof required for `preserved_agents`;
  - record the historical gate that non-dry-run reload stayed rejected until
    the narrow apply API had fake-backend tests.
- Phase 6b namespace additive patch API:
  - `add_window` fake-backend apply creates only the new window, optional
    sidebar pane, and new agent panes;
  - append-only `add_agent` fake-backend apply requires a layout proof that the
    last existing agent pane is expanded, then splits exactly one new agent pane
    from that anchor;
  - new pane identities include project id, role, slot key, window, namespace
    epoch, and `managed_by=ccbd`;
  - preserved-agent before/after snapshots are gate evidence only;
  - insert, reorder, move, replace, delete, and arbitrary layout mutations
    remain blocked;
  - patch-plan/topology mismatch is blocked before pane mutation;
  - failures before or during patch return diagnostics with graph/runtime/lease
    publish flags false.
- Phase 6b additive runtime mount helper:
  - fake `run_start_flow` receives only `patch_result.agent_panes` new agents
    and explicit `namespace_agent_panes`;
  - `cleanup_tmux_orphans=false`, no config watch, and no full namespace
    ensure/recreate/reflow/kill path;
  - preserved runtime authority records are unchanged before/after helper
    execution;
  - successful helper writes runtime authority only for new agents through the
    existing `RuntimeService` path;
  - start-flow failure does not publish a graph or update lease/lifecycle
    signature;
  - partial start-flow failure may leave new-agent authority residue, but
    diagnostics must mark graph and lease/lifecycle publish false.
- Phase 6b signature/publish transaction helper:
  - successful transaction updates lease config signature, mounted lifecycle
    config signature, namespace epoch, then publishes the new service graph;
  - app-visible graph version, config identity, registry, and ping config
    signature come from the new graph only after publish;
  - namespace patch failure blocks before signature writes and publish;
  - runtime mount failure, including partial new-agent runtime residue, blocks
    before signature writes and publish;
  - lease/lifecycle signature failure keeps the current graph/config visible and
    rolls back any signature write that already happened;
  - stale lease holder, daemon instance, or generation blocks signature handoff;
  - graph publish failure after signature writes rolls signatures back and keeps
    graph old.
- Phase 6b additive apply orchestrator:
  - view-only apply publishes the target graph without real namespace mutation
    or new runtime authority writes;
  - append-only `add_agent` and `add_window` success paths run namespace patch,
    mount only new agents, then publish the target graph;
  - plan-blocked, namespace-patch-failed, runtime-mount-failed, and
    publish-transaction-failed paths stop at the failing stage and keep the old
    graph/config visible;
  - failed namespace patch diagnostics report created window/pane residue;
  - failed runtime mount diagnostics report new-agent runtime authority residue;
  - successful publish leaves app graph/config, lease signature, and lifecycle
    signature consistent.
- Phase 6b user path gate:
  - `project_reload_config(dry_run=false)` and plain `ccb reload` invoke the
    additive apply orchestrator;
  - non-dry-run `view_only_change`, append-only `add_agent`, and `add_window`
    succeed in focused tests;
  - `no_change` returns noop without graph publish; `replace_agent`,
    `move_agent`, and arbitrary `layout_change` are rejected or blocked without
    graph publish;
  - idle `remove_agent` kills only the removed agent pane, stops that runtime
    authority/helper, and publishes the new graph;
  - busy or outstanding `remove_agent` blocks before namespace mutation;
  - namespace patch, runtime mount, and publish transaction failures return
    stage-specific diagnostics and residue while keeping the old graph/config
    visible;
  - CLI render/exit-code tests cover non-dry-run success and failed residue
    output;
  - plain CLI reload writes a bounded `reload-handoff.json` before RPC submit,
    and changed-signature daemon apply overwrites it during the transaction;
    both clear it after success or failure;
  - after successful non-dry-run publish, `ping('ccbd')` and `project_view`
    read the new graph/config signature.
- Bounded drain/retire state:
  - idle intent transitions immediately to `idle_ready` / `retiring`;
  - busy intent remains `waiting` / `draining` until timeout;
  - `timeout_s`, `max_age_s`, and `max_pending` reject or terminate bounded
    records;
  - unload and replace intents share the queue bound without unbounded growth;
  - non-dry-run idle `replace_agent` executes same-slot runtime replacement,
    while busy replace persists a bounded replace drain before returning
    blocked diagnostics;
  - `retired` is terminal;
  - busy/idle predicate is injectable;
  - state-machine and store tests do not call tmux, publish a service graph,
    patch namespace, mutate runtime authority, or start/stop providers.
  - non-dry-run busy `remove_agent` persists an unload drain before returning
    blocked, dispatcher rejects active-drain targets, and a later successful
    idle retry retires the record.
  - daemon heartbeat auto-retry handles ready active unload drains only when
    the current disk config still plans `remove_agent`; busy records remain
    waiting, and stale ready drains are retired if the removal is no longer in
    the current plan.
  - `project_reload_config` and CLI reload rendering expose active drain count,
    agent, phase/status, busy state, bounded deadlines, and `ccb reload` as the
    explicit retry path.
  - `project_view` exposes the same active drain summary and marks affected
    agent rows with `reload_drain` and
    `dispatch_blocked_by_reload_drain=true`; project-view cache reuse is
    invalidated when `reload-drain.json` appears or changes.
  - the Rust sidebar helper parses those row-level drain fields and renders a
    compact `drain:<status>` marker so a user can see why a draining agent is
    temporarily dispatch-blocked;
  - `scripts/reload_busy_drain_smoke.py --check-sidebar-render` captures the
    live tmux sidebar pane during the blocked reload and requires
    `drain:waiting`, proving the marker is visible outside Rust unit tests.
- Handler graph routing:
  - after graph replacement, `submit`, `project_view`, `ping`, and focus
    handlers resolve the new graph;
  - wrapper dispatch does not reload `.ccb/ccb.config` or rebuild the graph per
    request;
  - old graph retention is bounded after in-flight requests finish once
    RCU-style retention exists in a later mutating phase.
- Invalid config:
  - parse/validation error returned;
  - old `app.config_identity` remains published;
  - keeper-compatible signature remains old;
  - no tmux calls.
- Add agent to existing window:
  - old agent pane ids unchanged;
  - new agent pane created with correct CCB tmux identity options;
  - registry knows the new agent;
  - supervision sees the new desired agent.
- Add new window:
  - existing window and pane ids unchanged;
  - new tmux window exists;
  - new sidebar pane exists when sidebar mode is `every_window`;
  - new agents in that window are mounted.
- Existing agent provider/workspace/model/key/url change:
  - pure same-agent replacement is planned as `replace_agent` with
    `reuse_agent_pane_for_replace`;
  - provider suffix changes inside `[windows]` are compared as provider-neutral
    layout so they do not create a false `layout_change`;
  - idle replace stops old runtime authority and respawns the new provider in
    the same pane before publishing;
  - busy replace records a bounded `replace` drain and leaves namespace,
    runtime authority, and graph publish untouched;
  - a later successful idle retry retires the active replace drain after
    publishing the same-slot replacement;
  - source-wrapper fake smoke covers actual daemon `fake-codex -> fake-claude`
    replacement, pane-id preservation, provider status update, and post-replace
    ask reachability.
- Existing agent removed from `[windows]`:
  - Phase 3 dry-run reports `remove_agent`;
  - idle unload retires runtime and removes only the target pane;
  - busy unload returns a stable rejection before pane kill, records an active
    bounded unload drain, and exposes the drain record in blocked diagnostics;
  - subsequent `ccb reload --dry-run` / `ccb reload` payloads show the active
    drain status until a successful idle retry clears it;
  - active unload drains reject new dispatcher work for the draining agent and
    remove draining agents from broadcast target resolution;
  - after the runtime becomes idle, either a manual retry or daemon heartbeat
    auto-retry uses the same `remove_agent` path and retires the drain record;
  - existing unrelated processes are not killed by reload.
- Existing agent provider/workspace/model/key/url change after automatic busy
  replace retry is enabled:
  - idle-ready replace drains should execute the same same-slot replacement
    path without requiring a manual `ccb reload`;
  - provider session continuity is not claimed without provider-specific proof.
- Existing agent moved to another managed window:
  - explicit dynamic move plans `move_agent`;
  - the target pane id is preserved while window ownership changes;
  - source and target windows are reflowed without killing unrelated panes;
  - ask remains reachable before move, after move, and after moving back;
  - evacuated dynamic windows are removed only when empty.
- Busy agent preservation:
  - fake runtime reports `BUSY`;
  - additive reload succeeds for unrelated new agent;
  - busy runtime authority is unchanged.
- Keeper signature continuity:
  - successful reload updates daemon ping payload signature;
  - keeper `daemon_matches_project_config()` returns true after reload;
  - during apply, keeper tolerates the exact target-disk/old-daemon signature
    handoff only for a fresh matching live holder;
  - expired or wrong-holder handoff records do not bypass handoff trust;
  - saving `.ccb/ccb.config` before explicit reload does not make keeper or CLI
    compatibility restart a modern mounted daemon. The old daemon signature is
    a reload-pending state until `ccb reload` applies or rejects the change.
- Project view/sidebar:
  - successful reload invalidates cache;
  - next `project_view` includes new agents/windows;
  - active reload drains appear in `project_view.reload_drains` and on the
    affected agent row, including long-TTL cache invalidation when the drain
    file changes;
  - sidebar helper rendering includes row-level active drain status from
    `project_view`, currently covered by the sidebar crate unit test plus the
    external fake busy-drain smoke evidence, with `--check-sidebar-render`
    available for true tmux pane capture validation;
  - sidebar refresh control and `r` shortcut submit non-dry-run reload and then
    refresh project view;
  - daemon-pushed sidebar refresh remains deferred unless later manual
    validation proves it is needed.
- Performance gates:
  - no-op dry-run does not increase steady-state heartbeat work;
  - project-view cache hits remain cache hits;
  - handler graph read path does not use a contended global mutex.

## Integration Tests With Fake Tmux

- Add one agent to an existing two-agent window and assert only one `split-pane`
  is issued.
- Add a new window and assert existing windows receive no `kill-window`,
  `respawn-pane`, or recreation calls.
- Sidebar-enabled topology creates exactly one sidebar pane for each new window.
- Failure after validation but before publish leaves old bundle active.
- Failure during namespace patch leaves old config active and records a
  recoverable reload failure.
- Old service graph is retained only for in-flight requests and then released.
- Drain timeout and pending queue bounds prevent unbounded pending reload state.

## Manual `test_ccb2` Tests

- 2026-06-28 live provider smoke evidence:
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-move-agent-latest.json`
    passed `codex` `move-agent`: add helper, ask before move, move to `review`,
    ask after move, move back to `main`, ask after return, unload helper, and
    return to only `main`;
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-same-window-continuous-latest.json`
    passed `codex` `same-window-continuous`: grow `main` from one managed
    agent pane to six, preserve the original main pane, verify geometry/fixed
    columns, ask a dynamic helper, unload helpers in reverse order, reflow back
    to one pane, and keep main ask-reachable;
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-move-agent-latest.json`
    passed `claude` `move-agent` with the same pane-preserving move/move-back
    and unload checks.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-same-window-continuous-latest.json`
    passed `claude` `same-window-continuous`: grow `main` from one managed
    agent pane to six, preserve the original main pane, verify geometry/fixed
    columns, ask a dynamic helper, unload helpers in reverse order, reflow back
    to one pane, and keep main ask-reachable.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-batch-release-latest.json`
    passed `codex` `batch-release`: add a survivor helper to an existing
    window, add two helpers into new windows, batch-unload the two new-window
    helpers, remove empty dynamic windows, preserve the survivor pane, and keep
    survivor/main asks reachable.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-batch-release-latest.json`
    passed the same real-home `batch-release` checks for `claude`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-window-class-continuous-latest.json`
    passed `codex` `window-class-continuous`: grow the
    `plan-orchestrate` window class from static planner to eight real provider
    panes across `plan-orchestrate` and `plan-orchestrate-2`, observe fixed
    columns, ask `planner_helper7`, unload helpers in reverse order, remove the
    empty second page, and return to only `frontdesk` plus `planner`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-window-class-continuous-latest.json`
    passed the same real-home `window-class-continuous` checks for `claude`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-mixed-move-add-latest.json`
    passed `codex` `mixed-move-add`: move existing `zeta`/`alpha` panes from
    `review` to `archive`, mount new `beta` in the same reload transaction,
    remove the evacuated `review` window, preserve moved pane ids, and keep all
    three agents ask-reachable.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-mixed-move-add-latest.json`
    passed the same real-home `mixed-move-add` checks for `claude`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-batch-move-window-class-latest.json`
    passed `codex` `batch-move-window-class`: add dynamic `zeta` and `alpha`
    into `review`, batch-move them into `plan-orchestrate` class windows, remove
    the evacuated `review` window, preserve moved pane ids, and keep both agents
    ask-reachable.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-batch-move-window-class-latest.json`
    passed the same real-home `batch-move-window-class` checks for `claude`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-arrange-window-latest.json`
    passed `codex` `arrange-window`: grow `plan-orchestrate` to five agent
    panes, intentionally disturb the window into a non-fixed horizontal layout,
    restore the fixed-column target geometry with `ccb agent arrange`, preserve
    pane ids and agent order, keep `planner_helper3` ask-reachable, then unload
    helpers back to the static `frontdesk` plus `planner` topology.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-arrange-window-latest.json`
    passed the same real-home `arrange-window` checks for `claude`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-move-shared-source-latest.json`
    passed `codex` `move-shared-source`: add two helpers to `review`, move one
    helper to `main` while keeping the source `review` window alive for the
    staying helper, preserve moved/staying pane ids, keep both helpers
    ask-reachable, move the helper back, and remove the source window only after
    both helpers are released.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-move-shared-source-latest.json`
    passed the same real-home `move-shared-source` checks for `claude`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-codex-resolve-preflight-latest.json`
    passed `codex` `resolve-preflight` with `fake` static filler panes: resolve
    window-class overflow to `plan-orchestrate-2`, add/release the real
    `review_helper1`, resolve execution-node placement to `node-round3-node1`,
    ensure real worker/reviewer loop capacity, then release the node cleanly.
  - `/home/bfly/yunwei/test_ccb2/dynamic-layout-live-claude-resolve-preflight-latest.json`
    passed the same real dynamic-provider `resolve-preflight` checks for
    `claude` with `fake` static filler panes.
- 2026-06-28 core fake-provider CI gate evidence:
  - `.github/workflows/test.yml` now runs `Guard core dynamic layout smoke` on
    Ubuntu/Python 3.11 with fake provider through
    `scripts/guarded_core_dynamic_layout_smoke.py`, covering
    `same-window-continuous`, `batch-release`, `move-agent`,
    `move-shared-source`, `window-class-continuous`, `arrange-window`,
    `mixed-move-add`, `batch-move-window-class`, and `resolve-preflight`.
  - The guard script asserts top-level flow checks plus critical per-flow
    invariants for pane preservation, fixed-column geometry, empty-window
    cleanup, moved/new agent ask reachability, shared-source window retention,
    mixed move-plus-add planning, batch window-class move, and
    resolve/preflight loop-capacity cleanup.
  - `pytest -q test/test_dynamic_layout_smoke_script.py
    test/test_guarded_dynamic_layout_provider_smoke_script.py
    test/test_guarded_core_dynamic_layout_smoke_script.py` passed with
    `49 passed`.
  - `/home/bfly/yunwei/test_ccb2/guarded-core-dynamic-layout-local-latest.json`
    passed the same nine-flow fake-provider guard from the external `test_ccb2`
    source-wrapper environment with
    `dynamic_layout_smoke_status: ok`.
- 2026-06-28 dynamic lifecycle smoke evidence:
  - `pytest -q test/test_dynamic_agent_lifecycle_smoke_script.py` passed with
    `5 passed` before workflow promotion; after adding the CI gate, targeted
    workflow/lifecycle tests passed with `8 passed`;
  - `.github/workflows/test.yml` now runs `Guard dynamic agent lifecycle smoke`
    on Ubuntu/Python 3.11 with fake provider, checking park/resume dispatch
    gates, pane preservation, reviewer unload, layout cleanup, and terminal
    asks;
  - `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-fake-latest.json`
    passed fake-provider lifecycle policy checks;
  - `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-ci-gate-latest.json`
    passed the same fake-provider lifecycle smoke using the CI-gate timeout and
    project shape;
  - `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-codex-latest.json`
    passed real-home `codex` lifecycle checks: long-lived planner helper
    auto-parks, dispatch is rejected while parked, pane identity is preserved
    through resume, ask works again after resume, short-lived reviewer helper
    auto-unloads, and final layout returns to static `frontdesk` plus
    `planner`.
  - `/home/bfly/yunwei/test_ccb2/dynamic-agent-lifecycle-claude-latest.json`
    passed the same real-home lifecycle checks for `claude`.
- Phase 3 dry-run checks:
  - start a mounted project and run `ccb reload --dry-run` with no config
    changes; expect `plan_class: no_change`;
  - edit `.ccb/ccb.config` to add one agent to an existing window; dry-run
    should report `add_agent` and no new pane should appear;
  - edit config to add a new window; dry-run should report `add_window` and no
    tmux window should appear;
  - edit config to remove an idle agent; dry-run should report `remove_agent`
    with a `kill_agent_pane` namespace step and no pane should disappear;
  - edit an existing agent provider/workspace/model/key/url; dry-run should
    report `replace_agent` and leave the running pane untouched;
  - delete or move an existing agent; dry-run should report `remove_agent` or
    `move_agent`/`layout_change` and leave panes untouched;
  - for delete or replace dry-run, inspect the payload for `drain_intents`
    suggestions only; no pending drain store entry, pane change, graph publish,
    or runtime authority write should occur from dry-run alone;
  - break TOML or config validation; dry-run should report `invalid_config`
    while `ccb ping ccbd` still shows the old config signature.
- Phase 5 dry-run namespace patch checks:
  - for add-agent/add-window dry-run, inspect `namespace_patch_plan`; it should
    show deferred additive steps and leave panes/runtime state untouched;
  - run `ccb reload --dry-run` before plain `ccb reload` and confirm the
    planned class is one of the gated additive classes before mutation.
- Phase 6+ mutating checks:
  - keep fake-backend tests for the enabled additive path and verify no
    `kill-server`, `kill-window`, `reflow_workspace`, or full
    `ensure_project_namespace` recreation path is called;
  - start a project with two windows and four agents;
  - start a long-running/manual task in `agent2`;
  - edit `.ccb/ccb.config` to add `agent5` to an existing window;
  - wait at least one keeper poll and verify generation/pane ids did not
    change before running reload;
  - run `ccb reload`;
  - verify via tmux screenshot that `agent2` remains in the same pane and
    continues running, `agent5` appears in a new managed pane, sidebar shows
    `agent5`, and no global refresh/restart occurred;
  - repeat by adding a new window with one new agent;
  - after the added agent is idle, remove it from `.ccb/ccb.config`, run
    `ccb reload`, and verify only that agent pane disappears, `ccb ping ccbd`
    no longer lists it, and old pane ids for the remaining agents are
    unchanged;
  - submit a real `ask` to a remaining agent after unload and confirm ccbd still
    routes through the same mounted daemon;
  - try changing `agent2` provider/workspace/model while it is running; reload
    must refuse without killing the pane;
  - try deleting a running agent; reload must refuse without killing the pane;
  - run `ccb reload --dry-run` before each mutating manual test and verify it
    reports the same planned operation that the mutating command later
    executes;
  - measure idle/sidebar-open CPU and RSS before and after the reload feature is
    installed.

## Release Gate

Hot reload is releasable only when:

- accepted additive reload preserves old pane ids in automated and manual
  tests;
- busy existing agents continue running through reload;
- unsafe diffs are rejected without side effects;
- keeper does not restart after successful reload;
- project view/sidebar reflect the new config immediately after reload;
- `ccb kill` and normal cold start behavior remain unchanged.
- steady-state CPU/RSS does not grow continuously after repeated dry-run and
  accepted reload operations;
- draining and pending replacement have tested timeout and bound behavior.
