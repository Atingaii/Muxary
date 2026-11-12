# Dynamic Window And Pane Agent Maintenance

Date: 2026-06-26

## Purpose

Define how CCB should maintain dynamic tmux windows and panes when the default
visible workspace starts with only one user-facing frontend, while dialog,
planning, orchestration, execution, monitoring, and recovery agents are loaded
and released on demand.

This document is a visual/runtime layout plan. It does not move authority from
scripts, task packets, runtime state, or loop runner into tmux panes. Windows
and panes are presentation and process containers, not workflow truth.

Agent lifecycle policy is specified separately in
[dynamic-agent-lifecycle-and-skills.md](dynamic-agent-lifecycle-and-skills.md).
This document describes where panes go; it does not decide durable authority.
For the current V1 workflow surface, the default presentation policy is visible
window placement rather than hidden background agents. Lifecycle still decides
when an agent is released, retained busy, or unloaded after evidence import.

## Design Principle

CCB needs a runtime layout manager:

```text
semantic roles request capacity
runtime layout manager maps agents to windows and panes
ccbd/tmux owns process placement
workflow state remains in task/loop files
```

This follows the simple-kernel/flexible-agent principle:

- Agent roles decide semantic need: dialog, planning, orchestration, node work,
  review, recovery.
- Program code deterministically maintains windows, panes, ownership, limits,
  lifecycle, and cleanup.

## Window Classes

Prefer named windows over relying on tmux numeric indexes. Numeric ordering is
for usability only.

| Logical Order | Window Class | Default Name | Contents | Max Panes |
| :--- | :--- | :--- | :--- | :--- |
| 1 | user interaction | `ccb-user` | resident `ccb_frontdesk`, on-demand immaculate `ccb_task_detailer`, future user-summoned dialog experts | 6 |
| 2 | planning and orchestration | `ccb-plan` | resident `ccb_planner`, per-task immaculate `ccb_orchestrator`, per-round immaculate `ccb_round_reviewer` | 6 |
| 3+ | execution workgroups | `ccb-exec`, `ccb-exec-2`, ... | `coder + code_reviewer` work units, packed three pairs per window | 6 |
| later | runtime diagnostics | `runtime` | loop runner, ccbd logs, capacity, ask/job queue, monitor, recovery | 6 |
| later | archived evidence | `archive-<loop-id>` | frozen panes or summaries retained for inspection | 6 |

When a class exceeds its pane limit:

- `ccb-user` creates `ccb-user-2`, then `-3` for future dialog expert overflow.
- `ccb-plan` creates `ccb-plan-2`, then `-3` if planning-side panes exceed six.
- Execution workgroups pack into `ccb-exec`; the seventh active execution
  pane creates `ccb-exec-2`.

## Window 1: `ccb-user`

Purpose: visible user discussion space.

Resident pane:

```text
ccb_frontdesk
```

Rules:

- `ccb_frontdesk` is the default user-facing boundary.
- `ccb_task_detailer` is created visibly in Window 1 only after a task route
  requests detail work. Its reply is imported, then its task-scoped provider
  session and pane are unloaded after the idle/evidence gate.
- Dialog-facing roles do not own task status, loop status, runtime lifecycle,
  or execution authority.
- Any task-affecting conversation should return through explicit artifacts or
  summaries before release.

Example:

```text
ccb-user
  ccb_frontdesk
  ccb_task_detailer  # only while a detail route is active
```

## Window 2: `ccb-plan`

Purpose: planning, review, clarification, orchestration, and round-level
verification workspace.

Resident pane:

```text
ccb_planner
```

Rules:

- V1 keeps only `ccb_planner` resident in Window 2. `ccb_orchestrator` is
  mounted visibly for one task/round and then unloaded.
- `ccb_planner` owns macro plan/task state recommendations and plan-tree
  artifacts through script authority.
- `ccb_orchestrator` lives here while active because it semantically decomposes
  work and proposes desired topology; it does not directly create tmux windows
  or panes.
- `ccb_round_reviewer` is mounted in `ccb-plan` only for round-end verification.
  It is part of the same round topology and release transaction as the
  execution agents.
- Scripts and loop runner remain authority; these panes produce artifacts and
  recommendations.

Phase examples:

| Phase | Expected Panes |
| :--- | :--- |
| planning | `ccb_planner`; add `ccb_orchestrator` when task orchestration starts |
| ready/execution start | `ccb_planner`, active `ccb_orchestrator` |
| round end | `ccb_planner`, active `ccb_orchestrator`, active `ccb_round_reviewer` |

## Window 3+: `ccb-exec` Execution Windows

Purpose: isolate bounded execution work while keeping panes dense enough for
repeated observation and review.

Default work-unit pattern:

```text
ccb-exec
  coder
  code_reviewer
  coder
  code_reviewer
  coder
  code_reviewer
```

Overflow pattern:

```text
ccb-exec-2
  coder
  code_reviewer
  ...
```

Rules:

- A recommended work unit is `coder + code_reviewer`.
- One window holds at most six panes, so one page holds at most three
  coder/reviewer work units.
- Desired active execution agents are assigned in desired order; 1-6 go to
  `ccb-exec`, 7-12 to `ccb-exec-2`, and so on.
- When a work unit is released or parked out of active execution, later
  execution agents move back into the earliest available execution window and
  the empty overflow window is removed by namespace patch/reflow.
- Busy execution agents are retained and reported as `retained_busy`; they are
  not killed to satisfy compaction.

## Runtime Window

Purpose: diagnostics and operations, normally hidden or not focused.

Panes:

```text
loop_runner
ccbd logs
capacity status
ask/job queue
monitor
recovery
```

Open this window for:

- ask/callback stalls;
- provider auth or startup failures;
- stale leases;
- busy release;
- pane death;
- capacity mismatch;
- dispatcher or message-bureau diagnostics.

The runtime window can show program logs and state renderings, but it does not
replace structured runtime files.

## Agent Placement Rules

Placement should be deterministic:

```text
profile ccb_frontdesk or ccb_task_detailer
  -> ccb-user

profile ccb_planner, ccb_orchestrator, or ccb_round_reviewer
  -> ccb-plan

profile coder or code_reviewer
  -> ccb-exec page by desired-order chunks of six active execution agents

agent kind monitor/recovery/system
  -> runtime
```

Profiles outside that built-in set must provide explicit `window_name` or
`window_class`; the topology reconciler should not silently reinterpret custom
roles as old worker/checker compatibility.

The pane limit is a readability constraint, not a workflow authority rule.

Current V1 default: do not hide workflow roles merely to reduce pane count.
Instead, keep active roles visible in the correct logical window and page
execution workgroups across `ccb-exec`, `ccb-exec-2`, and later windows. Hidden
or parked placement remains a lower-level lifecycle capability for explicit
operator action or later product modes, not the default agentic-loop layout.

## Read-Only Placement Resolution

Workflow roles and skills should be able to ask CCB where a dynamic agent would
land before they request lifecycle changes. The command surface is read-only:

```bash
ccb layout resolve <agent> --window ccb-plan --json
ccb layout resolve <agent> --window ccb-exec --json
```

The resolver uses the same effective config and placement precedence as
dynamic agent overlays:

```text
--window
  -> exact window name

--loop-id/--node-id
  -> lower-level explicit execution-node placement only when requested

--window-class
  -> first matching class window with fewer than six panes, else class-N

no explicit placement
  -> topology profile mapping when reconciled from desired topology;
     otherwise entry window for explicit [windows], else default layout surface
```

It must not write `.ccb/ccb.config`, create runtime lifecycle records, start a
provider, or mutate tmux. Its output is evidence for scripts and agents, not
workflow authority.

## Lifecycle Rules

These rules are layout effects of lifecycle decisions. The policy authority is
the lifecycle layer.

### Ensure

```text
request agent capacity
  -> topology reconciler or runtime layout manager resolves window placement
  -> ensure window
  -> ensure pane
  -> start provider session
  -> record placement
```

### Release

```text
release request
  -> check pending ask/job
  -> if busy: mark retained
  -> if idle: request summary artifact when needed
  -> record final placement state
  -> close pane
  -> compact window
  -> remove empty overflow window when no retained pane remains
```

Release must never be a blind `tmux kill-pane`. It should go through CCB
runtime state so busy agents are retained and cleanup is auditable.

### Move

Moving panes is allowed for visual cleanup, but it must update placement state.
Moving a pane must not change role authority, task ownership, or loop state.

Move should land in two phases:

```text
move-plan
  -> read effective config plus dynamic/loop overlays
  -> find the agent's current logical window
  -> resolve the requested target window/class/node
  -> verify ownership: dynamic session agents can move, static config agents cannot
  -> report source/target order, created-window need, and blockers
  -> perform no runtime mutation

move-apply
  -> consume or recompute a valid move plan
  -> drain/idle-check the target agent if required
  -> move the existing pane without restarting the provider
  -> update lifecycle placement evidence
  -> reflow source and target windows
  -> publish runtime authority after tmux and state agree
```

The first command surface is intentionally read-only:

```bash
ccb layout move-plan <agent> --window <target-window> --json
ccb layout move-plan <agent> --window-class <class> --json
ccb layout move-plan <agent> --loop-id <loop-id> --node-id <node-id> --json
```

It should block cross-window movement for `source=configured` agents because
configured panes belong to `.ccb/ccb.config`; moving them is a config-edit and
reload problem, not a runtime dynamic-agent operation. Same-window resolution is
a no-op regardless of ownership because it requires no mutation.

### Archive

Completed node windows can be removed after evidence import. For debugging,
they may be converted into an `archive-<loop-id>` window or summarized into
runtime artifacts.

## Runtime Layout State

CCB should maintain deterministic layout state. Candidate shape:

```json
{
  "windows": {
    "ccb-user": {
      "class": "user_interaction",
      "max_panes": 6,
      "agents": ["ccb_frontdesk", "ccb_task_detailer"]
    },
    "ccb-plan": {
      "class": "planning_orchestration",
      "max_panes": 6,
      "agents": ["ccb_planner", "ccb_orchestrator", "ccb_round_reviewer"]
    },
    "ccb-exec": {
      "class": "execution",
      "max_panes": 6,
      "agents": ["coder_1", "code_reviewer_1", "coder_2", "code_reviewer_2"]
    }
  }
}
```

The exact path can be decided during implementation. Likely options:

- project-level `.ccb/runtime/layout/windows.json`;
- loop-level `.ccb/runtime/loops/<loop-id>/layout.json`;
- both, with project layout indexing loop-local placements.

## True Hot-Load Design

True hot load means an operator, script, or orchestrator can add a dynamic
agent while CCB is already mounted, without restarting the project and without
interrupting preserved agents.

Acceptance criteria:

- `ccb agent add ...` writes a dynamic lifecycle record and immediately applies
  it when the project daemon is mounted;
- a new tmux pane or window is created by ccbd, not by the agent role;
- only the new agent runtime is started;
- preserved agents keep their pane ids, runtime authority, queues, and jobs;
- `ccb ps` shows the new agent after the transaction publishes;
- `ccb ask <new-agent> ...` is accepted after the command returns;
- failure rolls back or marks the dynamic record as failed without publishing a
  partial service graph.

The existing `ccb reload` path is the right transaction kernel. It already has:

- additive `add_agent` for appending a pane to an existing managed window;
- additive `add_window` for creating a new managed window and materializing its
  panes;
- runtime mount for only the newly materialized agent panes;
- graph/lease/lifecycle publish as a single transaction after namespace and
  runtime stages pass.

The missing layer is not another raw tmux command. The missing layer is a
dynamic placement overlay that can produce the same config/topology delta that
`ccb reload` already knows how to apply.

### Dynamic Add Transaction

```text
ccb agent add ccb_round_reviewer:codex --role agentroles.ccb_round_reviewer --window ccb-plan
  -> validate role/provider/profile/lifecycle policy
  -> choose placement target
  -> write .ccb/runtime/agents/ccb_round_reviewer/lifecycle.json as pending/applied intent
  -> dynamic config overlay materializes target window/layout
  -> if unmounted: defer until startup
  -> if mounted: call reload transaction
       -> dry-run/plan class must be add_agent or add_window
       -> namespace patch creates pane/window and stamps @ccb identity
       -> runtime mount starts only ccb_round_reviewer
       -> publish graph/signatures
  -> update lifecycle record with pane/window evidence
  -> return apply details
```

The dynamic record should carry placement intent and evidence:

```json
{
  "agent": "ccb_round_reviewer",
  "provider": "codex",
  "role": "agentroles.ccb_round_reviewer",
  "lifecycle_state": "hidden",
  "placement": {
    "mode": "window",
    "window_class": null,
    "window_name": "ccb-plan",
    "layout_policy": "append-only",
    "loop_id": null,
    "node_id": null
  },
  "applied": {
    "status": "applied",
    "plan_class": "add_agent",
    "window_name": "ccb-plan",
    "pane_id": "%12",
    "published_graph_version": 4
  }
}
```

### Existing Window Pane Add

V1 should support append-only pane creation first.

Requirements:

- target window exists in current topology;
- target window has at least one preserved agent pane when appending;
- new agent is added at the end of that window's agent order;
- layout delta remains compatible with the current additive patch planner.

This maps cleanly to existing `add_agent`.

Startup compatibility requirement:

- compact legacy configs still normalize to the logical `main` window even
  when they are not written with explicit `[windows]`;
- startup panes must be stamped with `@ccb_window=main` so later dynamic
  overlays can use the same namespace patch proof as explicit-window configs;
- structured/fake providers that do not expose a provider session binding
  still need namespace pane evidence written into runtime authority, otherwise
  `ccb ps`, cleanup, and hot-load planning can disagree about the active pane.

### New Window Add

New-window hot load should be first-class, not a workaround.

When placement chooses a missing window, the dynamic overlay should add a
`WindowSpec` to the loaded config:

```text
ccb-plan
  ccb_round_reviewer

ccb-exec
  coder_1
  code_reviewer_1
```

This maps to existing `add_window`:

- namespace patch creates the tmux window;
- if sidebar policy applies, it creates a sidebar pane;
- it materializes all agent panes in the new window;
- runtime mount starts only those new agents;
- publish updates graph/signatures.

New-window add does not need a preserved pane anchor inside that new window,
but it still requires a live project tmux namespace and publishable reload
transaction.

### Placement Selection

V1 placement should be deterministic:

```text
explicit --window NAME
  -> use NAME; create it if allowed

explicit --window-class CLASS
  -> first existing CLASS window with room
  -> else create CLASS-N

explicit --loop-id/--node-id
  -> lower-level execution-node override for non-topology callers

desired topology without placement flags
  -> profile mapping: ccb-user, ccb-plan, or packed ccb-exec pages

standalone agent add without placement flags
  -> fallback to entry window append
```

Suggested command examples:

```bash
ccb agent add ccb_task_detailer:codex --role agentroles.ccb_task_detailer --window ccb-user --json
ccb agent add ccb_round_reviewer:codex --role agentroles.ccb_round_reviewer --window ccb-plan --json
ccb agent add coder1:codex --profile coder --window ccb-exec --json
ccb agent add code_reviewer1:codex --profile code_reviewer --window ccb-exec --json
```

### Append-Only First, Reflow Later

The current safe reload planner supports appending and creating new windows. It
does not yet support arbitrary live reflow of existing panes.

Therefore:

- V1 true hot load should be append-only for existing windows and full
  materialization for new windows.
- V1 should not rearrange existing live panes into the 1->6 visual pattern.
- V2 can add a controlled reflow transaction after pane movement and placement
  evidence are modeled as first-class runtime state.

This keeps the first hot-load slice safe: adding an agent must not unexpectedly
move or resize active agents that are mid-conversation or mid-job.

### Current Landed Hot-Load Slice

Current worktree implementation now covers the first safe hot-load placement
slice:

- `ccb agent add ... --window NAME` appends to an existing managed window when
  `NAME` exists, or creates a new managed window when it does not.
- `ccb agent add ... --window-class CLASS` chooses the first class window with
  room, or creates a class window when none is available.
- `ccb agent add ... --loop-id LOOP --node-id NODE` maps to
  `node-<loop-id>-<node-id>` for execution-node placement.
- Dynamic overlays produce explicit `WindowSpec` data for placement and reuse
  the existing guarded reload transaction instead of issuing raw tmux commands.
- Lifecycle records are updated with placement intent and apply evidence:
  `window_name`, `pane_id`, `plan_class`, `runtime_mount_status`, and published
  graph version.
- Existing windows use append-only layout, preserving current panes. New
  windows use the deterministic pane-growth layout for their initial contents.
- `remove --policy unload --idle-only` applies the guarded `remove_agent`
  reload path after idle checks, closes only the released dynamic pane, unloads
  runtime authority, records `last_pane_id`, and removes empty dynamic windows.
- `agent release --policy unload --idle-only` exposes the same safe non-kill
  release path for workflow roles and scripts.
- Busy dynamic agents are retained instead of being killed or removed.
- `ccb agent move <agent> --window NAME` now covers the first true
  cross-window movement slice for dynamic session agents when the target
  managed window already exists. The reload plan uses `move_agent`, applies a
  tmux `move-pane`, restamps the pane's `@ccb_window`, reflows source and target
  windows, and updates runtime authority without provider restart.
- Dynamic move records write a separate `placement_sequence`, so moving an
  older agent into a target window appends after existing target agents instead
  of reusing the original creation order and accidentally becoming a
  non-additive reorder.
- `ccb layout status` and `ccb layout status --json` expose the effective
  runtime layout view for explicit `[windows]`: configured/static vs dynamic
  agents, lifecycle state, dispatch state, runtime state, pane ids, namespace
  state, and best-effort tmux pane observations. Unmounted projects with stale
  namespace state skip tmux observation instead of reporting a false failure.
- Dynamic lifecycle records now store `created_sequence` and
  `resolved_window_name`. The config overlay uses creation order for active
  dynamic agents, so a second agent in the same execution node appends after
  the existing worker instead of being alphabetically reordered into a
  non-additive `layout_change`.
- Loop capacity records now use the same placement model. Generated capacity
  agents carry `loop_id`, `node_id`, `created_sequence`, and
  `placement.window_name`, and explicit `[windows]` overlays place worker /
  checker capacity in `node-<loop-id>-<node-id>` windows. `layout status`
  reports these records as `source=loop`, separate from configured and generic
  dynamic agents.

Evidence:

- Parser and dry-run plan tests cover explicit window, window class, and
  loop/node placement in `test/test_agent_lifecycle_cli.py`.
- Agent move tests cover unmounted `move_agent` planning, mounted apply
  evidence, namespace `move-pane` application, runtime authority window
  mutation, and move-aware append/remove exclusion.
- Reload apply tests cover both `add_agent` and `add_window` dynamic overlays:
  `test_additive_reload_apply_dynamic_agent_overlay_materializes_tmux_pane_before_mount`
  and
  `test_additive_reload_apply_dynamic_agent_overlay_materializes_new_window_before_mount`.
- Controlled mounted tmux smoke passed for existing-window append in
  `/home/bfly/yunwei/test_ccb2/agent-hot-pane-ident.otr4SM`; the new `helper`
  pane was mounted and reachable by `ask`.
- Controlled mounted tmux smoke passed for new-window creation in
  `/home/bfly/yunwei/test_ccb2/agent-hot-window-ident.Xj9dR6`; the `review`
  window was created, `helper` was mounted, and `ask helper` completed.
- Controlled mounted tmux smoke passed for existing-window add plus release in
  `/home/bfly/yunwei/test_ccb2/agent-hot-remove-pty.2FIiGo`; an unload request
  while `helper` was busy returned `retained_busy`, and the retry after `ask`
  completion closed only the `helper` pane and removed it from `ps`.
- Controlled mounted tmux smoke passed for new-window add plus release in
  `/home/bfly/yunwei/test_ccb2/agent-hot-window-remove-pty.RqWVcE`; the
  `review` window was created for `helper`, then removed after idle unload.
- Controlled mounted tmux cycle smoke passed in
  `/home/bfly/yunwei/test_ccb2/agent-hot-cycle-pty.Tu9DCH`; panes grew from
  `%1:main` to `%1:main,%2:dyn1,%3:dyn2,%4:dyn3,%5:dyn4,%6:dyn5`, then
  released back to `%1:main` with `known_agents: ['main']`.
- Source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-real-1782476922` proved compact startup
  now stamps `@ccb_window=main`, existing-window `add_agent` creates `%2`,
  new-window `add_window` creates `review/%4`, and `ask` submission is accepted
  for both dynamic agents without manual tmux option seeding.
- Source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-unload-1782477435` proved explicit
  `remove --policy unload --force` removes the dynamic reviewer pane `%4`,
  removes the empty `review` window, removes the helper pane `%2`, stops
  dynamic runtime authority, and leaves only `main/%1`.
- Source-wrapper cycle smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-cycle-auto-1782482877` proved single
  window continuous growth and shrink without manual pane seeding:
  `main/%1 -> dyn1/%2 -> dyn2/%3 -> dyn3/%4 -> dyn4/%5 -> dyn5/%6`, followed
  by forced unload in reverse order back to only `main/%1`.
- Source-wrapper status smoke in
  `/home/bfly/yunwei/test_ccb2/layout-status-real-1782553123` proved
  `layout status --json` on an explicit-window project before mount, after
  mount, after same-window hot add/release, after new-window add/release with
  empty-window removal, and after forced kill with stale namespace state.
- Source-wrapper placement smoke in
  `/home/bfly/yunwei/test_ccb2/layout-placement-real-1782555` proved
  `--window-class plan-orchestrate` overflows from a full 6-pane
  `plan-orchestrate` window into `plan-orchestrate-2`, the loop/node placement
  flags create `node-round1-node1`, a second same-node agent appends as
  `worker1; checker1` with reload `plan_class=add_agent`, `ask checker1` is
  accepted, and reverse unload removes the checker pane, removes the empty node
  window after worker unload, removes the empty overflow window, and returns
  layout status to the two configured windows with `dynamic_agent_count=0`.
- Source-wrapper continuous window-class smoke now proves the page transition
  under repeated dynamic agent add/remove, not only a single overflow helper:
  `/home/bfly/yunwei/test_ccb2/window-class-continuous-smoke.json` fills
  `plan-orchestrate` to six agents, creates and appends to
  `plan-orchestrate-2`, verifies fixed columns on both pages, accepts an ask to
  the overflow helper, unloads seven helpers in reverse order, removes the
  empty overflow page, and returns to static `frontdesk` plus `planner`.
- The CI fake-provider dynamic layout gate now runs
  `same-window-continuous` and `window-class-continuous` together, so both
  single-page fixed reflow and class overflow cleanup are guarded on Ubuntu
  py3.11.
- Focused regression after the placement-order fix passed with `185 passed`
  across agent lifecycle, layout status, pane growth, layout runtime, reload
  patch/runtime mount, config loader, and loop capacity tests.
- Source-wrapper loop-capacity layout smoke in
  `/home/bfly/yunwei/test_ccb2/loop-capacity-layout-real-1782557` proved
  mounted loop capacity ensure for `worker=1` and `code_reviewer=1` creates
  `node-round1-node1`, status reports `loop_agent_count=2` with both agents as
  `source=loop`, the node panes are alive, and idle loop-capacity release
  removes the node window and returns to `loop_agent_count=0`.
- Repeatable dynamic layout smoke script
  `scripts/dynamic_layout_smoke.py` now covers the two high-risk mounted
  source-wrapper flows. In
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-smoke-1782565-multi-node`,
  `loop capacity ensure --profile worker=2 --profile code_reviewer=2`
  created `node-round2-node1` and `node-round2-node2`, accepted asks to worker
  and reviewer targets, waited for terminal fake jobs, released four loop
  agents, and returned to only the `main` window with `orchestrator`. In
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-smoke-1782565-same-window`,
  `agent add` grew `main` to `main, helper1, helper2, helper3`, removing the
  middle `helper2` used `plan_class=remove_agent`, preserved `helper1` and
  `helper3` pane ids, accepted asks to both survivors, and cleaned up with
  `kill_status: ok`.
- Real `remove_agent` namespace patch apply now performs best-effort visual
  reflow after same-window pane removal and then reapplies configured sidebar
  widths. For fully managed one-to-six agent windows, the reflow targets the
  fixed visual order `p1,p3,p5` left and `p2,p4,p6` right; unsupported shapes
  fall back to tmux even compaction. `NamespacePatchApplyResult` records
  `reflowed_windows` and
  `reflow_errors`, and `agent remove --json` exposes them as
  `namespace_reflowed_windows` / `namespace_reflow_errors`. Focused tests cover
  reflow after pane-only removal and sidebar width restoration. The
  source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-reflow-1782570-same-window`
  proved `main, helper1, helper2, helper3 -> main, helper1, helper3` reports
  `namespace_reflowed_windows=["main"]`, preserves survivor panes, accepts
  asks to both survivors, and cleans up with `kill_status: ok`.
- The orchestrator autonomous smoke harness now treats layout residue as a
  failure even when capacity release succeeds. After each autonomous parent
  callback chain it runs `layout status --json` and requires
  `loop_agent_count=0`; script tests cover both clean release and residual
  loop-agent failure. The source-wrapper fake workflow closure smoke in
  `/home/bfly/yunwei/test_ccb2/workflow-closure-layout-1782571` also proved
  generated loop agents release from layout and `ps` state with
  `dynamic_agents_absent_from_ps=true`.
- `scripts/dynamic_layout_smoke.py` now includes an explicit workflow-window
  flow for `--window-class plan-orchestrate`. The source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-window-class-1782560319-window-class`
  proved `main=[frontdesk]` and
  `plan-orchestrate=[planner, planner_helper1, planner_helper2,
  planner_helper3]`, removed middle `planner_helper2` with
  `plan_class=remove_agent`, reported
  `namespace_reflowed_windows=["plan-orchestrate"]`, preserved
  `planner_helper1` and `planner_helper3` pane ids, kept `main` unchanged, and
  accepted asks to both surviving helpers.
- The same smoke harness is now ready for guarded real-provider probes:
  `--provider` rewrites the generated config and dynamic `agent add` provider,
  `--flow` can isolate one scenario such as `window-class`,
  `--provider-home-mode` separates isolated source-home from real user auth,
  and non-fake runs require `CCB_DYNAMIC_LAYOUT_SMOKE_RUN_REAL=1`.
  Verification covered the unchanged default fake run, a selected
  `--flow window-class` fake run, and Codex `--prepare-only` preflight with
  real-home auth discovery under `/home/bfly`.
- After merging remote `v7.7.0` runtime-accelerator/theme work, the dynamic
  layout smoke still passed all fake-provider flows in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-merged-1782561461-*`. A guarded
  Codex real-provider `window-class` run then passed in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-codex-window-1782561840-window-class`:
  three Codex helpers hot-loaded into `plan-orchestrate`, middle
  `planner_helper2` unloaded with `plan_class=remove_agent`, reflow reported
  `namespace_reflowed_windows=["plan-orchestrate"]`, surviving panes stayed in
  place, and asks to `planner_helper1` and `planner_helper3` were accepted.
- The matching guarded Claude real-provider `window-class` run passed in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-claude-window-1782563057-window-class`:
  `frontdesk` and `planner` started as explicit Claude panes, three Claude
  helpers hot-loaded into `plan-orchestrate`, middle `planner_helper2` removed
  with `plan_class=remove_agent`, reflow reported
  `namespace_reflowed_windows=["plan-orchestrate"]`, surviving helper pane ids
  were preserved, asks to `planner_helper1` and `planner_helper3` were
  accepted, and cleanup returned `state: unmounted`.
- `layout status --json` now includes script-facing ownership and apply
  diagnostics on each agent record: `agent_kind`, `ownership_class`,
  `dispatch_state`, `pane_identity_source`, `apply_status`,
  `apply_plan_class`, `apply_stage`, `failed_apply`, and `retained_busy`.
  Focused tests cover static configured agents, dynamic session helpers, loop
  capacity agents, parked dispatch-disabled helpers, and failed apply records;
  the fake explicit-window smoke remained green after adding the fields.
- `agent status --json` and `agent show --json` now mirror the same
  ownership/apply vocabulary for configured and dynamic lifecycle records, so
  orchestrator scripts can query either the layout view or the lifecycle view
  without switching field names. Focused tests cover static configured agents,
  active dynamic agents, parked dispatch-disabled agents, deferred apply
  records, and failed-apply detection.
- Non-interactive `ccb` start output now carries a compact layout identity
  summary generated from the same `layout status` source. The startup view
  reports explicit-window state, window/pane counts, observed pane count, and
  per-agent `ownership_class`, `dispatch_state`, `pane_id`,
  `pane_identity_source`, runtime state, and apply status. If that diagnostic
  probe fails, start still reports success but surfaces
  `layout_summary_status: unavailable` with the error type and message.
- The orchestrator draft RolePack now includes `dynamic-agent-lifecycle` for
  non-loop dynamic agents. The current loop-agent direction is
  `orchestrator-topology`: orchestrator proposes graph intent, while topology
  reconciliation uses capacity, lifecycle, and layout mechanisms to apply
  safe load/release/move behavior. The older `orchestrator-capacity` path is
  retained as a legacy/debugging substrate rather than the preferred
  orchestrator-facing contract.
- `scripts/dynamic_layout_smoke.py` now supports repeated `--provider` values
  for a guarded provider matrix. The real Codex+Claude matrix passed in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-matrix-real-1782567263-*` for
  `--flow window-class`, with both providers proving hot add, middle unload,
  explicit-window reflow, survivor pane preservation, ask reachability, and
  cleanup.
- `scripts/guarded_dynamic_layout_provider_smoke.py` now provides a fixed
  guarded entrypoint for future release/CI wiring. It defaults to prepare-only
  Codex+Claude `window-class`, `move-agent`, and `resolve-preflight`, requires
  `--run` plus
  `CCB_DYNAMIC_LAYOUT_SMOKE_RUN_REAL=1` for live provider execution, and passed
  both prepare-only and real guarded source-wrapper runs in
  `/home/bfly/yunwei/test_ccb2/guarded-dynamic-layout-prepare-1782568181-*`
  and `/home/bfly/yunwei/test_ccb2/guarded-dynamic-layout-real-1782568215-*`.
- The default `Tests` workflow now runs that wrapper as a prepare-only Ubuntu
  py3.11 gate, without `--run`, and asserts that the Codex+Claude
  `window-class`, `move-agent`, and `resolve-preflight` provider matrix reaches
  `prepared`. This keeps real provider execution behind explicit local/release
  opt-in while making wrapper drift a normal CI failure.
- Dynamic reload apply reports now carry pane identity diagnostics. The shared
  `pane_identity_report` appears under mounted `ccb agent add/remove --json`,
  topology reconciliation, and lower-level
  `ccb loop capacity ensure/release --json` apply payloads, summarizing
  added and removed agent panes, preserved before/after panes, created/removed
  panes, removed windows, reflowed windows, reflow errors, mounted agents, and
  unloaded agents from the same namespace patch/runtime mount transaction.
- `ccb layout arrange --window NAME --json` now exposes the first manual
  topology-preserving rearrangement command. It is mounted-only, reads the
  effective `[windows]` layout plus current namespace state, reuses the same
  fixed-layout-first/even-layout fallback helper as dynamic add/remove, and
  returns `arrange_status`, `reflowed_windows`, `reflow_errors`, namespace
  data, and latest layout status. It does not create panes, remove panes, move
  agents across windows, rewrite `.ccb/ccb.config`, or restart provider
  sessions. The source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/layout-arrange-smoke.json` proved a disturbed
  horizontal `plan-orchestrate` window returns to the managed two-column
  layout while preserving agent order.
- `scripts/dynamic_layout_smoke.py` now supports `--output <path>` for direct
  JSON evidence artifacts. The latest source-wrapper fake-provider closure in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-output-latest.json` passed
  `same-window-continuous`, `multi-window-continuous`, and
  `window-class-continuous`: a single window grew `1->6->1`, separate dynamic
  review windows were created and removed back to `main`, and
  `plan-orchestrate` overflowed into `plan-orchestrate-2` before reverse
  unload removed the empty overflow page.
- `scripts/dynamic_layout_smoke.py --flow arrange-window` now makes the manual
  arrange proof repeatable. It hot-loads helpers into `plan-orchestrate`,
  uses tmux only to disturb the window into a non-managed horizontal shape,
  restores the window through `ccb layout arrange`, proves fixed columns,
  preserves agent order and pane ids, verifies a post-arrange ask, and unloads
  dynamic helpers back to static `frontdesk` plus `planner`. The latest
  source-wrapper artifact is
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-arrange-latest.json`.
- The default Ubuntu py3.11 fake-provider dynamic layout CI gate now runs
  `arrange-window` together with `same-window-continuous` and
  `window-class-continuous`; the CI-equivalent source-wrapper artifact
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-ci-arrange-latest.json` passed
  all three flows.
- Opt-in real-provider `arrange-window` smokes now pass for Codex and Claude.
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-arrange-codex-real-latest.json`
  and
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-arrange-claude-real-latest.json`
  both prove the same disturbance/arrange/ask/unload chain with real provider
  panes while preserving pane ids and agent order.
- `ccb layout move-plan <agent> ... --json` now exposes the first read-only
  cross-window move planner. It reads the effective layout with dynamic
  overlays, reports source window, resolved target window, source/target
  would-be agent order, created-window need, ownership class, and explicit
  `read_only=true` / `mutation_performed=false`. It plans movement for dynamic
  session agents, reports same-window requests as `noop`, and blocks
  cross-window movement for static configured agents. Focused tests pass in
  `test/test_layout_cli.py`, `test/test_layout_status_cli.py`, and
  `test/test_agent_lifecycle_cli.py`; source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/move-plan-smoke` proved `helper1` can be
  planned from `plan-orchestrate` to a new `review` window while `frontdesk`
  is blocked from cross-window runtime movement.
- Focused regression after landing existing-window `agent move` passed with
  `108 passed` across agent lifecycle, namespace patch apply, runtime move,
  runtime attach, reload patch/drain, and layout CLI tests. Source-wrapper CLI
  smoke in
  `/home/bfly/yunwei/test_ccb2/source-move-smoke-20260628034710` proved
  unmounted `agent add helper`, `agent add reviewer`, `agent move helper
  --window review`, `placement_sequence=3`, and valid projected config.
- Focused regression after connecting loop capacity to layout placement passed
  with `187 passed` across loop capacity, agent lifecycle, layout status, pane
  growth, layout runtime, reload patch/runtime mount, and config loader tests.
- Focused regression passed with `222 passed` across dynamic lifecycle,
  config-loader, dispatcher, start-runtime, start-flow, reload-apply,
  reload-runtime-mount, and tmux-start-layout tests.

## Command Surface Direction

User-facing commands should stay small:

```bash
ccb view
ccb view frontdesk
ccb view dialogs
ccb view plan
ccb view loop <loop-id>
ccb view node <node-id>
ccb view runtime
```

Internal or advanced commands can be added later:

```bash
ccb layout status --json
ccb layout arrange --window <window>
ccb layout ensure-window --class <class> --name <name>
ccb layout assign-agent --agent <agent> --window <window>
ccb layout release-agent --agent <agent> --idle-only
ccb layout compact --window <window>
ccb layout archive --window <window>
```

Avoid making users manually manage tmux panes for normal workflow operations.

## Relationship To Orchestrator

Orchestrator does semantic execution planning. It may request:

```text
need 3 execution nodes:
  node1: worker + checker
  node2: worker + checker
  node3: worker + checker
```

Runtime layout manager decides:

```text
create node-<loop-id>-node1 window
create node-<loop-id>-node2 window
create node-<loop-id>-node3 window
place worker/checker panes
record placement state
```

Therefore:

- orchestrator does not call raw tmux commands;
- orchestrator does not decide visual layout details;
- runtime layout manager does not decide semantic task decomposition;
- loop runner and scripts remain state authority.

## Configuration Direction

Candidate config:

```toml
[ui.windows.ccb_user]
name = "ccb-user"
class = "user_interaction"
max_panes = 6
profiles = ["ccb_frontdesk", "ccb_task_detailer"]

[ui.windows.ccb_plan]
name = "ccb-plan"
class = "planning_orchestration"
max_panes = 6
profiles = ["ccb_planner", "ccb_orchestrator", "ccb_round_reviewer"]

[ui.windows.ccb_exec]
name = "ccb-exec"
class = "execution"
mode = "packed_pages"
max_panes = 6
profiles = ["coder", "code_reviewer"]

[ui.windows.runtime]
class = "runtime"
focus_by_default = false
max_panes = 6
```

The initial implementation can hard-code these classes before exposing config.

## V1 Slice

V1 should implement enough to support the agentic loop without making tmux
layout a second workflow system:

1. Track logical window class and pane placement for dynamic agents.
2. Place V1 resident `ccb_frontdesk` and `ccb_task_detailer` in `ccb-user`.
3. Place V1 resident `ccb_planner` and `ccb_orchestrator` in `ccb-plan`;
   place `ccb_round_reviewer` there only when a round-review topology asks for
   it.
4. Pack active `coder + code_reviewer` work units into `ccb-exec` pages with
   six panes per page.
5. Reclaim empty execution overflow pages by moving surviving execution agents
   back into earlier pages during reconcile.
6. Retain busy agents and release idle agents through runtime state, not raw
   tmux kills.
7. Provide a read-only `ccb layout status --json` or equivalent diagnostic.

V1 acceptance for this layout requires source tests that prove:

- `ccb_frontdesk` and any active `ccb_task_detailer` land in `ccb-user`.
- `ccb_planner`, `ccb_orchestrator`, and active `ccb_round_reviewer` land in
  `ccb-plan`.
- `coder` and `code_reviewer` land in `ccb-exec` pages in desired order, with
  at most six panes per window.
- The seventh active execution agent creates `ccb-exec-2`.
- Releasing or parking enough execution agents compacts survivors back into
  the earliest `ccb-exec` page and removes empty overflow pages.
- Automatically assigned workflow roles remain `present`/visible by default;
  hidden/parked states must be explicit.

## Fixed Pane Growth Order

The first implementation slice should not attempt arbitrary placement. Within
one logical page, panes grow in a deterministic 1->6 pattern:

| Count | Intent | Layout spec |
| --- | --- | --- |
| 1 | full pane | `p1` |
| 2 | left/right | `p1; p2` |
| 3 | left stacked, right full | `(p1, p3); p2` |
| 4 | two columns, two rows | `(p1, p3); (p2, p4)` |
| 5 | left three rows, right two rows | `(p1, p3, p5); (p2, p4)` |
| 6 | two columns, three rows | `(p1, p3, p5); (p2, p4, p6)` |

This keeps early panes visually stable as new panes are appended:

- pane 1 remains the top-left anchor;
- pane 2 remains the top-right anchor after the second pane appears;
- odd-numbered additions extend the left column;
- even-numbered additions extend the right column.

Overflow creates another tmux window with the same local 1->6 rule. The layout
manager should treat the window name as a page, not as semantic workflow
authority.

Initial landing target:

- add a scriptable planning surface for 1->6 plus overflow;
- add an isolated tmux smoke surface for placeholder panes;
- add a dynamic smoke surface that continuously grows and shrinks fake-agent
  panes in one isolated tmux session;
- defer live agent movement and drag/drop editing until the deterministic
  growth model is verified.

## Fixed Pane Shrink Order

Dynamic release is the inverse operation of growth, but it is more sensitive
because some panes contain still-running providers. CCB must not rebuild the
whole window to compact after deletion.

Release flow:

```text
release dynamic agent
  -> resolve target pane by @ccb_project_id + @ccb_slot
  -> check ask/job/queue state
  -> if busy: retain and report
  -> if idle: unload target provider and close only that pane
  -> recompute growth-1-6 layout for remaining ordered agents
  -> compact remaining panes without respawning them
  -> remove empty overflow window if needed
  -> update layout state
```

The target layout is computed from the remaining logical order:

| Shrink | Remaining order | Target layout |
| --- | --- | --- |
| 6->5 | `p1 p2 p3 p4 p5` | `p1, p3, p5; p2, p4` |
| 5->4 | `p1 p2 p3 p4` | `p1, p3; p2, p4` |
| 4->3 | `p1 p2 p3` | `p1, p3; p2` |
| 3->2 | `p1 p2` | `p1; p2` |
| 2->1 | `p1` | `p1` |

For middle deletion, the same rule applies after removing the target from the
ordered list. Example:

```text
[p1, p2, p3, p4, p5, p6] - p3
=> [p1, p2, p4, p5, p6]
=> p1, p4, p6; p2, p5
```

Multi-window shrink:

- 8->7 keeps `ccb-exec-2` with one remaining execution pane when seven active
  execution agents remain.
- 7->6 moves the surviving overflow pane back to `ccb-exec` and removes
  `ccb-exec-2`.
- Empty execution overflow windows are removed after no retained panes remain.

Compaction can use tmux resize/swap/move operations on surviving panes, but it
must never kill or respawn surviving agent panes to make the visual layout
prettier.

Current evidence:

- isolated fake-agent dynamic smoke passed for `1->6->1`;
- isolated fake-agent dynamic smoke passed for `1->8->1`, including page add
  at 7 and page removal at 6;
- `ccb layout status --json` now provides a read-only effective topology and
  runtime pane diagnostic for explicit `[windows]`, including dynamic overlays
  and best-effort tmux observations;
- topology default placement now maps V1 resident
  `ccb_frontdesk`/`ccb_task_detailer` to `ccb-user`, V1 resident
  `ccb_planner`/`ccb_orchestrator` to `ccb-plan`, optional
  `ccb_round_reviewer` to `ccb-plan` when present, and
  `coder`/`code_reviewer` to packed `ccb-exec` pages;
- dynamic overlay-created runtime windows use append-compatible layout specs,
  so growing an existing `ccb-exec` page from one `coder + code_reviewer`
  group to two groups produces an additive namespace patch instead of
  reshaping and respawning existing panes;
- source tests prove four coder/reviewer work units create `ccb-exec` plus
  `ccb-exec-2`, then releasing one middle work unit moves the final work unit
  back into `ccb-exec` and removes `ccb-exec-2`;
- existing-window and new-window dynamic hot add are proven through guarded
  reload tests and controlled mounted tmux smoke;
- existing-window and new-window dynamic hot unload are proven through
  controlled mounted tmux smoke, including busy retain and empty-window removal;
- guarded dynamic movement now covers two bounded cases: moving a dynamic agent
  into an existing managed window, and moving one dynamic agent into a newly
  materialized target window. The new-window case is intentionally restricted
  to a target window that contains exactly the moved agent; the namespace patch
  creates the target window, moves the preserved pane, kills the placeholder
  pane, restamps window evidence, and reflows only the source/target windows;
- mounted movement is now proven by the repeatable fake-provider
  `move-agent` smoke: helper is reachable before movement, retains its pane id
  after moving from `main` to new `review`, remains reachable after movement,
  and unload removes the empty target window. This smoke also guards the
  transaction invariant that runtime `status=moved` is publish-ready, so tmux
  namespace movement and runtime authority publication do not split;
- bounded movement cycles are now proven for one dynamic agent in an otherwise
  empty dynamic source window: moving `helper` from `review` back to `main`
  removes the empty `review` window in the same guarded transaction, preserves
  the helper pane id, reflows `main`, keeps ask reachability after return, and
  leaves final unload as a normal same-window `remove_agent` operation;
- guarded provider movement coverage now includes the bounded move cycle:
  prepare-only Codex+Claude matrix projects cover `window-class`, `move-agent`,
  and `resolve-preflight`, while opt-in Codex and Claude real-provider
  `move-agent` runs prove `main -> review -> main -> unload` with terminal asks
  before move, after move, and after return. The smoke harness uses
  `ccb pend --watch` with an explicit watch timeout for these job observations;
- shared-source movement is now proven for moving one dynamic agent out of a
  source window that still contains another dynamic agent: `helper1` and
  `helper2` start in `review`, moving `helper1` to `main` preserves both pane
  ids, keeps `review` alive with `helper2`, keeps both helpers ask-reachable,
  and moving `helper1` back appends it after `helper2`; final unload removes
  `review` only after both helpers exit;
- same-transaction movement of multiple agents out of one shared source window
  is now proven at the reload/namespace patch layer. The planner preserves
  source-window order by subtracting the full moved-agent set, and namespace
  apply moves both existing panes into the target window while preserving pane
  ids, source-window survivorship, and target append order. This proof is
  intentionally below the CLI layer; a user-facing batch move command remains a
  separate product/API decision;
- full source-window evacuation is also proven at the reload/namespace patch
  layer: when every source-window agent is moved elsewhere, the patch plan
  emits the moved panes in new target topology order, then kills the emptied
  source window in the same transaction. This closes the low-level
  `6->1`/page-collapse style invariant for moved panes without respawning
  providers;
- `ccb agent move --agents a,b --window NAME --json` now exposes the first
  user-facing batch move command for dynamic session agents. It writes all
  selected lifecycle placement records, applies one reload transaction, and
  rolls back all touched lifecycle records if the transaction fails. The same
  implementation proves multiple moved panes can enter a newly materialized
  target window, with the placeholder pane cleaned only once and subsequent
  moved panes anchored after the prior moved pane. Source-wrapper fake-provider
  evidence is preserved in
  `/home/bfly/yunwei/test_ccb2/batch-move-*-latest.json`;
- `ccb agent remove --agents a,b --policy unload --idle-only --json` and
  `ccb agent release --agents a,b --idle-only --json` now expose the first
  user-facing batch release/unload command for dynamic session agents. The
  lifecycle layer validates all selected agents up front, treats idle retention
  as all-or-nothing, writes one batch of lifecycle state, applies one guarded
  reload transaction, and restores all touched lifecycle records on failure.
  Source-wrapper fake-provider evidence is preserved in
  `/home/bfly/yunwei/test_ccb2/batch-remove-smoke-evidence/summary.json`; it
  proves batch removal of `helper2,helper3` from
  `main=[main,helper1,helper2,helper3]`, `plan_class=remove_agent`,
  `namespace_reflowed_windows=["main"]`, survivor layout
  `main=[main,helper1]`, ask acceptance for `helper1`, and final
  `kill_status: ok`;
- `scripts/dynamic_layout_smoke.py --flow batch-release` makes the batch
  release proof repeatable across the source-wrapper harness. The flow creates
  `main=[main,helper1]`, `review2=[helper2]`, and `review3=[helper3]`, runs one
  `ccb agent remove --agents helper2,helper3 --policy unload --idle-only
  --json`, verifies `namespace_removed_agents` for both target panes,
  `namespace_removed_windows=["review2","review3"]`, survivor pane
  preservation for `main/helper1`, post-release layout
  `main=[main,helper1]`, and ask acceptance for both `helper1` and `main`.
  Latest evidence:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-batch-release-latest.json`;
- the default Ubuntu Python 3.11 fake-provider dynamic layout CI bundle now
  includes `--flow batch-release` and asserts the batch flow result, removed
  dynamic panes, removed single-agent windows, survivor pane preservation, and
  ask reachability for both `helper1` and `main`;
- `ccb agent move --agents a,b` now accepts the same dynamic target grammar as
  single-agent move instead of being limited to explicit `--window NAME`.
  The first landed target is `--window-class CLASS`: CCB writes the batch
  lifecycle placement in command order, resolves each agent through the
  effective `[windows]` capacity rules, reports `target_window_names` when a
  batch spans multiple resolved windows, and still applies one reload
  transaction with rollback on failure. Source-wrapper fake-provider evidence
  is preserved in
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-batch-move-window-class-latest.json`;
  it proves `review=[zeta,alpha]` moves to
  `plan-orchestrate=[p1,p2,p3,p4,p5,zeta]` and
  `plan-orchestrate-2=[alpha]`, preserves both moved pane ids, removes
  `review`, and accepts ask for both moved agents;
- `scripts/dynamic_layout_smoke.py --flow batch-move-execution-node` now
  covers the other dynamic target grammar for batch move. The flow creates
  `review=[worker,checker]`, runs one `ccb agent move --agents worker,checker
  --loop-id round1 --node-id node1 --json`, verifies `target_window_name` and
  `target_window_names` resolve to `node-round1-node1`, checks both moved pane
  ids are preserved in `node-round1-node1`, confirms `review` is removed, and
  accepts ask for both moved agents. Latest evidence:
  `/home/bfly/yunwei/test_ccb2/dynamic-layout-batch-move-execution-node-latest.json`;
- `ccb agent park --agents a,b --json` and
  `ccb agent resume --agents a,b --hidden|--visible --json` now expose the
  first user-facing batch transition command for long-lived dynamic agents.
  The lifecycle layer validates all selected agents up front, writes one batch
  of lifecycle state, applies one guarded config-only reload transaction, and
  restores all touched lifecycle records on failure. Source-wrapper
  fake-provider evidence is preserved in
  `/home/bfly/yunwei/test_ccb2/batch-park-resume-smoke-evidence/summary.json`;
  it proves batch `park` sets dispatch disabled for both helpers and rejects
  ask, batch `resume --hidden` re-enables dispatch without changing pane ids,
  and ask is accepted after resume;
- same-window middle dynamic release is proven: removing the middle helper pane
  deletes only the target pane, preserves the remaining dynamic pane ids, keeps
  their ask targets reachable, and avoids `layout_change`;
- same-window dynamic agent cycle smoke passed for `1->6->1` without changing
  the preserved `main` pane id;
- mounted source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/hotload-smoke-1782474327` proved a full
  runtime sequence across existing-window add, `park` config-only dispatch
  disable, `resume`, new-window `add_window`, ask reachability, idle release,
  empty-window removal, and return to one `main` pane;
- mounted source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/resolve-preflight-smoke-1782573894-resolve-preflight`
  proved the role-facing preflight chain on explicit `[windows]`: `layout
  resolve` predicted `plan-orchestrate-2`, `agent add` materialized it as
  `add_window`, `agent show` and `layout status` confirmed placement,
  `agent release --idle-only` unloaded the short-lived reviewer and removed the
  empty overflow window, then `layout resolve --loop-id/--node-id` predicted
  `node-round3-node1` before `ccb loop capacity` created and released the
  worker/checker execution-node window;
- guarded provider prepare-only now covers `window-class`, `move-agent`, and
  `resolve-preflight` for Codex+Claude, so CI validates the new project/config
  surface without requiring real provider auth;
- guarded `resolve-preflight` provider preparation can now keep static
  overflow filler panes on `fake` while reserving Codex/Claude for the dynamic
  reviewer and loop worker/checker profiles, reducing the future real-provider
  run from a large static pane startup to the actual dynamic add/release and
  loop-capacity surfaces that need real-provider proof;
- the first opt-in Codex real-provider run of this lighter
  `resolve-preflight` variant passed in `/home/bfly/yunwei/test_ccb2`, proving
  real dynamic reviewer add/release and real loop worker/checker
  create/release while static overflow panes remained `fake`;
- the matching opt-in Claude real-provider run of the lighter
  `resolve-preflight` variant also passed in `/home/bfly/yunwei/test_ccb2`,
  proving the same real dynamic reviewer and loop worker/checker lifecycle
  path for Claude;
- compact workspace release reflow now resolves entry-window reflow through
  namespace workspace id/name when logical `main` is not an actual tmux window
  name; the workflow closure source-wrapper smoke proved loop worker/checker
  release with `namespace_reflowed_windows=["main"]` and empty reflow errors;
- the fake-provider workflow closure layout-cleanup smoke is now part of the
  Ubuntu py3.11 CI gate, asserting workflow closure, auto release, zero
  retained loop agents, and empty namespace/pane reflow errors;
- live provider release remains gated on busy/idle checks.

## 2026-07-10 Real Project Evidence

The opened real-provider project recorded in
[visible-three-round-dynamic-window-e2e-20260710.md](../history/visible-three-round-dynamic-window-e2e-20260710.md)
validated the intended foreground layout across three sequential task loops.
Idle state retained only frontdesk and planner. Each direct-execution round
created `ccb-exec`, appended immaculate orchestration/round-review panes to
`ccb-plan`, then released all four dynamic agents and removed the empty
execution window. The final state returned to two windows and two resident
agent panes with zero retained loop agents.

The same run proved that provider context purity is a runtime requirement, not
only a RolePack prompt convention: every activation performed provider-native
clear, generated fresh pane/session evidence, and was unloaded after evidence
import. Claude session selection now permits same-agent, same-project rotation
after clear while preserving the initial exact binding and rejecting foreign
project sessions.

Deferred:

- interactive drag/drop layout management;
- visual rich panel for window topology;
- automatic screenshot/archive of completed node windows;
- cross-session restoration of exact pane geometry;
- transactions that mix moved panes with newly materialized panes in the same
  target window;
- user-defined arbitrary window classes.
