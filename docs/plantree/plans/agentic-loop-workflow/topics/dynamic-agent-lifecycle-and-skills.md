# Dynamic Agent Lifecycle And Skills

Date: 2026-06-26

## Purpose

Define how CCB should dynamically load, show, hide, park, resume, release, and
unload agents without turning tmux panes or `.ccb/ccb.config` into the runtime
truth.

This document sits between two existing topics:

- [dynamic-window-pane-agent-maintenance.md](dynamic-window-pane-agent-maintenance.md)
  defines where panes and windows appear.
- [role-profiles-and-capacity-skill.md](role-profiles-and-capacity-skill.md)
  defines how orchestrator requests bounded execution capacity.

The missing layer is lifecycle policy. `frontend`, planner, and orchestrator
style roles carry expensive, long-lived context. They should normally be hidden
or parked when not active, not unloaded. Short-lived execution roles can be
unloaded after their evidence has been imported and their work is idle.

Current workflow direction: loop execution agents should normally be created
and released by topology reconciliation, not by `orchestrator` directly calling
`ccb agent add/remove` or `ccb loop capacity ensure/release`. The lifecycle
commands in this document remain the lower-level mechanism for operators,
non-loop dynamic agents, and the topology reconciler.

## Role Classes

### Long-Lived Interactive Roles

Examples:

- primary `frontend` or `frontdesk` agents;
- dialog experts that are expected to continue a user conversation;
- planner coordinators;
- plan reviewers when they are assigned to an active task family;
- orchestrator;
- round checker when a round family is still open.

Default policy:

- `hide` when the role should remain alive but should not occupy the current
  visible workspace;
- `park` when the role should stop receiving new work but retain its provider
  session, runtime record, placement metadata, and resume path;
- hard `unload` only when explicit, idle, summarized, and not needed for an
  active task.

### Short-Lived Execution Roles

Examples:

- generated worker agents;
- generated checker or code reviewer agents;
- node-local helper agents.

Default policy:

- release after task or round evidence is imported;
- retain if ask/job state is busy;
- unload when idle and owned only by the current round;
- reuse only when the configured profile says reuse is allowed.

### Diagnostic And System Roles

Examples:

- loop monitor;
- recovery helper;
- runtime diagnostics pane;
- ask/job queue observer.

Default policy:

- hide or park while diagnostics remain relevant;
- unload after the diagnostic window or incident is closed;
- never make product or plan decisions by itself.

## Lifecycle States

The runtime lifecycle should be explicit enough for scripts, skills, and users
to reason about it.

| State | Meaning |
| :--- | :--- |
| `visible` | Agent is running and has a pane in the active logical view. |
| `hidden` | Agent is running, but its pane is outside the current view or in a hidden/runtime window. |
| `parked` | Agent is retained for later resume and receives no new normal work. Provider/session state should remain available when feasible. |
| `retained_busy` | A release was requested, but pending ask/job/provider state made release unsafe. |
| `sleeping` | Optional future state: provider process is stopped, but a resume reference and summary artifact are retained. |
| `unloaded` | Provider and pane are stopped; only runtime evidence, resume metadata, and artifacts remain. |
| `failed_resume` | CCB tried to resume the agent and could not prove readiness. |
| `failed_release` | CCB tried to release the agent and could not complete or prove cleanup. |

`hide` is a presentation action. `park` is a lifecycle action. `unload` is a
destructive runtime action and must be rarer.

## Runtime Records

Dynamic lifecycle state should be runtime state, not config state.

Candidate paths:

```text
.ccb/runtime/agents/index.json
.ccb/runtime/agents/<agent-name>/lifecycle.json
.ccb/runtime/layout/windows.json
.ccb/runtime/loops/<loop-id>/capacity.json
```

Candidate lifecycle record:

```json
{
  "agent": "orchestrator",
  "role": "agentroles.ccb_orchestrator",
  "profile": "orchestrator",
  "role_class": "long_lived_interactive",
  "lifecycle_state": "parked",
  "visibility_state": "hidden",
  "window_class": "plan-orchestrate",
  "pane_id": "%12",
  "provider": "codex",
  "session_ref": "provider-session-id-or-path",
  "workspace": "/project",
  "loop_id": "loop_123",
  "task_id": "task_123",
  "created_by": "loop_runner",
  "last_reason": "round drained; retain orchestrator context",
  "summary_artifact": ".ccb/runtime/artifacts/orchestrator-summary.md",
  "restore_policy": "prefer_provider_session_then_summary",
  "updated_at": "2026-06-26T00:00:00Z"
}
```

`.ccb/ccb.config` remains source policy. It may declare allowed profiles,
provider/model/thinking defaults, placement classes, limits, and lifecycle
defaults, but it should not store current dynamic instances.

## Command Surface

### Agent Specification Sources

Dynamic agent creation should support three input levels. The lower levels are
convenience syntax; the higher levels remain the safer workflow path.

#### Profile-Based

Use a predeclared profile from config. This is the safest path for autonomous
workflow roles.

```bash
ccb agent add reviewer --profile code_reviewer --hidden --lifetime current_loop --json
ccb agent add planner2 --profile planner --parked --json
```

Profile authority:

- profile names and defaults come from `.ccb/ccb.config`;
- provider, model, thinking, role, workspace, limits, and default lifecycle
  can be declared once and reused;
- autonomous roles should prefer this form because it prevents invented
  provider/model/role combinations.

#### Inline Role-Based

Use an explicit role plus provider when a profile does not exist yet.

```bash
ccb agent add architect:codex \
  --role agentroles.architect \
  --model gpt-5.5 \
  --thinking high \
  --visible \
  --window-class frontdesk-dialog \
  --lifetime session \
  --json
```

This form is useful for operator-driven experiments and user-visible dialog
experts. It should still be validated against installed roles, provider
support, model/thinking constraints, and project limits.

#### Minimal Shorthand

The compact example syntax is a shorthand, not the full authority model:

```bash
ccb agent add helper:codex --role agentroles.general --hidden --json
ccb agent remove helper --policy park --json
```

`name:provider` means:

- `name` is the dynamic agent name;
- `provider` is the provider id;
- role must still be resolved, either through `--role`, `--profile`, or a
  safe default such as `agentroles.general` only when the project explicitly
  allows that default.

V1 should avoid silent role defaults unless the default is visible in
diagnostics. A missing role should normally produce a validation error.

### Lifecycle Actions

Separate user intent from destructive process operations.

| Action | Meaning | Provider Process | Pane | Dispatch Eligibility |
| :--- | :--- | :--- | :--- | :--- |
| `show` | Make a running/parked agent visible. | kept | visible | enabled if not parked |
| `hide` | Remove from current visible workspace. | kept | hidden or moved | unchanged |
| `park` | Retain context but stop normal dispatch. | kept when feasible | hidden/parked | disabled until resume |
| `resume` | Return hidden/parked agent to usable state. | kept or restored | visible or hidden | enabled |
| `release` | Apply role policy. | depends on policy | depends | depends |
| `unload` | Graceful stop after idle/evidence gates. | stopped gracefully | closed/archived | disabled |
| `kill` | Force stop for broken or explicitly abandoned process. | killed | closed | disabled |

`remove` should be a policy-driven release request. It must not mean
unconditional process kill.

```bash
ccb agent remove helper --policy auto --idle-only --json
ccb agent remove helper --policy hide --json
ccb agent remove helper --policy park --json
ccb agent remove helper --policy unload --idle-only --summary required --json
ccb agent remove helper --policy kill --force --reason "operator reset" --json
```

Policy meaning:

- `auto`: use role class default. Long-lived roles park or hide; short-lived
  execution roles unload only after idle/evidence gates.
- `hide`: presentation-only removal from the visible workspace.
- `park`: retain role context, stop normal dispatch, keep restore metadata.
- `unload`: graceful provider stop after idle and summary/evidence rules.
- `kill`: force stop. Operator-grade only, never a normal skill action.

`kill` exists because real systems need a recovery escape hatch, but it should
be semantically loud, require `--force`, require `--reason`, and emit a
diagnostic event.

### User-Facing Commands

These commands should be stable and small.

```bash
ccb agent status [--json]
ccb agent show <agent> [--json]
ccb agent add <name[:provider]> [--profile <profile>] [--role <role>] [--visible|--hidden|--parked] [--json]
ccb agent load <agent> [--visible|--hidden] [--json]
ccb agent hide <agent> [--json]
ccb agent park <agent> [--json]
ccb agent resume <agent> [--visible|--hidden] [--json]
ccb agent remove <agent> [--policy auto|hide|park|unload|kill] [--idle-only] [--json]
ccb agent release <agent> --idle-only [--json]
```

Semantics:

- `add` creates a dynamic runtime definition and starts or ensures the agent.
- `load` resumes an existing dynamic lifecycle record or starts a configured
  static agent; it should not silently create a new unrelated agent.
- `hide` keeps the provider running and changes only presentation.
- `park` keeps the role retained but stops normal dispatch to it.
- `resume` returns a hidden or parked role to usable state.
- `remove` applies an explicit release policy. With no policy, it should use
  `auto`.
- `release` applies policy. For long-lived roles, `release` normally parks.
  For short-lived round-owned roles, `release` may unload after idle/evidence
  checks.

Hard unload should be advanced and explicit:

```bash
ccb agent unload <agent> --idle-only --reason <text> [--json]
ccb agent unload <agent> --force --reason <text> [--json]
ccb agent kill <agent> --force --reason <text> [--json]
```

`--force` should remain operator-grade, not something a role skill uses during
normal workflow.

### Add Parameters

Core parameters:

| Parameter | Meaning |
| :--- | :--- |
| `<name[:provider]>` | Agent name, optionally with provider shorthand. |
| `--profile <profile>` | Load from declared dynamic profile. |
| `--role <role-id>` | RolePack id, for example `agentroles.coder`. |
| `--provider <provider>` | Provider id when not supplied through `name:provider` or profile. |
| `--model <model>` | Optional provider model override when allowed. |
| `--thinking <level>` | Optional reasoning intensity when supported. |
| `--workspace-mode <mode>` | Workspace policy, using existing CCB semantics. |
| `--window <name>` | Exact logical tmux window name. Existing windows are appended to; missing windows may be created by the guarded reload path. |
| `--window-class <class>` | Placement class such as `frontdesk-dialog`, `plan-orchestrate`, `runtime`, or node window. |
| `--loop-id <id>` / `--node-id <id>` | Execution-node placement hint. Together they map worker/checker-style agents to `node-<loop-id>-<node-id>`. |
| `--lifetime <lifetime>` | `session`, `current_loop`, `current_round`, or `manual`. |
| `--visible` | Start visible in its target layout class. |
| `--hidden` | Start running but hidden from the current view. |
| `--parked` | Create or retain lifecycle record but do not dispatch normal work until resumed. |
| `--json` | Return machine-readable result. |

Validation rules:

- `--profile` may supply role/provider/model/thinking defaults.
- `name:provider` and `--provider` must not conflict.
- `--role` and profile role must not conflict unless an explicit override
  policy exists.
- `--visible`, `--hidden`, and `--parked` are mutually exclusive.
- Short-lived execution lifetimes require a loop or task owner before
  automatic release can be safe.
- Long-lived roles default to `--hidden` or `--parked` when added by a
  non-user-facing workflow role.

### Remove Parameters

Core parameters:

| Parameter | Meaning |
| :--- | :--- |
| `<agent>` | Existing dynamic or configured agent name. |
| `--policy auto` | Use role class default. |
| `--policy hide` | Hide pane only. |
| `--policy park` | Retain session/context and disable dispatch. |
| `--policy unload` | Gracefully stop provider and close/archive pane. |
| `--policy kill` | Force stop; requires `--force` and `--reason`. |
| `--idle-only` | Refuse destructive release while ask/job/provider state is busy. |
| `--summary required|best-effort|none` | Summary/evidence requirement before unload or kill. |
| `--reason <text>` | Human-readable audit reason. Required for kill and recommended for unload. |
| `--json` | Return machine-readable result. |

`remove --policy auto` should resolve through role class:

| Role Class | Auto Policy |
| :--- | :--- |
| `long_lived_interactive` | `park`, or `hide` when it is still expected to receive user-visible attention. |
| `short_lived_execution` | `unload` after idle/evidence gates. |
| `diagnostic` | `park` while incident is open, otherwise `unload` after idle. |
| unknown | `park` unless operator explicitly chooses unload or kill. |

Workflow lifetime mapping is semantic, not a statement about which window is
visible. `ccb_frontdesk` and `ccb_planner` are `long_lived_interactive`.
`ccb_task_detailer`, `ccb_orchestrator`, `ccb_round_reviewer`, coder, and code
reviewer are immaculate task/round roles and use `short_lived_execution`, so
automatic release unloads their provider session and pane instead of parking
their context for reuse.

The command output should always report the resolved policy. Example:

```json
{
  "agent_lifecycle_status": "ok",
  "agent": "planner2",
  "requested_action": "remove",
  "requested_policy": "auto",
  "resolved_policy": "park",
  "previous_state": "visible",
  "next_state": "parked",
  "ask_target": "planner2",
  "retained_busy": false
}
```

### Status And Show Output

`status` is list-oriented. `show` is detail-oriented.

```bash
ccb agent status --json
ccb agent status --class planning --json
ccb agent show planner2 --json
```

Minimum status fields:

- name;
- static or dynamic source;
- role;
- provider;
- role class;
- lifecycle state;
- visibility state;
- ask reachability;
- pane id and window class when known;
- current owner: user, task, loop, or manual;
- release policy and blockers.

This read-only inventory should land before mutation commands because it is
the safety and diagnostics surface for all later lifecycle work.

### Loop And Orchestrator Commands

`ccb loop topology` should become the orchestrator-facing execution-node
interface:

```bash
ccb loop topology propose --loop-id <loop-id> --from <file> --json
ccb loop topology commit --loop-id <loop-id> --proposal <id> --apply --json
ccb loop topology reconcile --loop-id <loop-id> --json
ccb loop topology status --loop-id <loop-id> --json
ccb loop topology release --loop-id <loop-id> --policy auto --json
```

`ccb loop capacity` remains the lower-level substrate that the reconciler may
use:

```bash
ccb loop capacity ensure \
  --loop-id <loop-id> \
  --profile coder=2 \
  --profile checker=2 \
  --lifetime current_round \
  --json

ccb loop capacity status --loop-id <loop-id> --json

ccb loop capacity release \
  --loop-id <loop-id> \
  --idle-only \
  --policy auto \
  --json
```

Planned extensions:

- `--policy auto|hide|park|unload`;
- `--role-class long_lived_interactive|short_lived_execution|diagnostic`;
- `--visibility visible|hidden|parked`;
- structured `retained_busy` output when release is unsafe.

The orchestrator may request execution capacity only as topology intent. It
should not choose tmux operations or provider process operations. After
topology commands exist, the normal orchestrator path should be topology
proposal, not direct capacity ensure or release.

### Layout Commands

Layout commands remain presentation-level:

```bash
ccb layout status --json
ccb layout arrange --window <window-name> --json
ccb layout compact --window <window-name> --json
```

They should consume lifecycle and placement records instead of inventing agent
state.

## Skill Design

### `dynamic-agent-lifecycle`

Purpose: allow trusted workflow roles to request lifecycle actions without raw
tmux, config edits, reload, kill, or provider process control.

Inputs:

- lifecycle intent: `add`, `load`, `hide`, `park`, `resume`, `remove`,
  `release`, `status`;
- target profile or target agent;
- role id and provider only when the caller is allowed to use inline specs;
- role class;
- requested visibility;
- lifetime: `current_round`, `current_loop`, `session`, or `manual`;
- task id and loop id when applicable;
- reason string;
- evidence or summary artifact reference when release may lose context.

Allowed commands:

- `ccb agent status --json`;
- `ccb agent show <agent> --json`;
- `ccb layout resolve <agent> ... --json`;
- `ccb agent add ... --json`;
- `ccb agent load ... --json`;
- `ccb agent hide ... --json`;
- `ccb agent park ... --json`;
- `ccb agent resume ... --json`;
- `ccb agent remove ... --idle-only --json`;
- `ccb agent release ... --idle-only --json`;
- `ccb loop topology propose/status/commit --json` when the caller is
  orchestrator and the target is execution capacity;
- `ccb loop capacity ensure/status/release --json` only when the caller is the
  topology reconciler, operator diagnostics, or a legacy compatibility flow.

For `add`, the intended sequence is:

```text
layout resolve
  -> agent add
  -> agent show/status
  -> layout status
```

`layout resolve` is read-only preflight evidence. It should catch unexpected
entry-window placement, existing-agent conflicts, unexpected overflow windows,
or accidental execution-node placement before any provider or tmux mutation.

Forbidden actions:

- edit `.ccb/ccb.config`;
- call raw `ccb reload`;
- call raw `ccb kill`;
- call raw `tmux`;
- kill provider processes;
- hard unload long-lived roles without explicit operator instruction;
- use `remove --policy kill`;
- convert a failed release into success;
- silently reduce requested node count unless planner policy explicitly allows
  serial fallback.

Outputs:

- requested action;
- actual lifecycle state;
- agent names and ask targets;
- retained-busy list with reasons;
- blocker artifact path when action is not possible;
- next recommended action.

### Permission Profiles

| Caller Role | Allowed Lifecycle Actions | Boundary |
| :--- | :--- | :--- |
| `frontdesk` / `frontend` | load visible dialog expert, hide dialog expert, resume parked dialog expert, status | No worker fanout, no hard unload, no plan/runtime authority writes. |
| planner group | add/load/resume planner helper/reviewer/broker by profile, park planner helpers, status | No execution-node capacity and no direct user question bypass. |
| orchestrator | propose/inspect/commit topology through `ccb loop topology`, park/resume itself, status | Max 1-4 nodes, no direct capacity ensure/release in the normal path, no raw tmux, no config edits, no provider kill, no `kill` policy. |
| round checker | status, request temporary diagnostic helper, park self after result import | No implementation fixes and no task status writes. |
| monitor/recovery | status, report retained/failed lifecycle, suggest operator actions | No force unload unless explicitly escalated. |

`orchestrator-capacity` can remain as a legacy/debugging skill while
`orchestrator-topology` becomes the normal workflow skill. Both may share the
same underlying runtime command surface through the topology reconciler.

## Safety Rules

1. Runtime instances are not written into `.ccb/ccb.config`.
2. Long-lived roles default to `hide` or `park`, not `unload`.
3. Short-lived execution roles unload only after idle and evidence-import
   checks.
4. Busy release returns `retained_busy`.
5. Layout compaction must not kill or respawn surviving provider panes.
6. Resume failure should produce `failed_resume` and a blocker, not silently
   create a new blank role with the same name.
7. Skills call CCB commands. They do not call raw tmux or provider binaries.
8. Every lifecycle mutation should emit structured JSON and append a runtime
   event for diagnostics.
9. `remove` must report the resolved policy. It must not conceal a kill,
   unload, or failed retain behind a generic success line.
10. `kill` requires explicit operator intent, `--force`, `--reason`, and a
    diagnostic event.

## Implementation Phases

1. Read-only inventory:
   - `ccb agent status --json`;
   - lifecycle index discovery from config, runtime records, ccbd state, and
     tmux pane metadata.
2. General dynamic add validation:
   - parse `name:provider` shorthand;
   - support profile-based and inline role-based specs;
   - reject missing or conflicting role/provider/model/thinking inputs;
   - write runtime lifecycle records without changing `.ccb/ccb.config`.
3. Presentation-only lifecycle:
   - `hide`, `resume`, and layout-state updates for fake-agent panes.
4. Park semantics:
   - `park` long-lived roles without unloading providers;
   - prove parked roles are omitted from normal dispatch unless explicitly
     resumed.
5. Policy-based remove/release:
   - `remove --policy auto|hide|park|unload|kill`;
   - prove `remove --policy auto` resolves by role class;
   - prove `kill` requires `--force` and `--reason`.
6. Short-lived release:
   - `release --idle-only` for generated worker/checker nodes;
   - import evidence before unload;
   - retain busy agents.
7. Skill packaging:
   - `dynamic-agent-lifecycle` skill has landed in the orchestrator CCB
     adapter for non-loop dynamic agents;
   - the skill now requires `ccb layout resolve ... --json` before
     `ccb agent add ... --json`, and checks `addable`,
     `placement_mode`, `resolved_window_name`, and `will_create_window`;
  - `orchestrator-capacity` is retained as a legacy loop-capacity substrate;
    the next skill direction is `orchestrator-topology`, with reconciliation
    using lifecycle and capacity mechanisms underneath.
8. Real workflow smoke:
   - start with one visible frontend;
   - dynamically load planner and orchestrator;
   - park planner/orchestrator;
   - run one worker/checker node;
   - release worker/checker;
   - resume planner/orchestrator;
   - verify ask reachability and lifecycle records throughout.

## Test Targets

- Unit tests for lifecycle state transitions and invalid transitions.
- Unit tests proving `.ccb/ccb.config` is not rewritten by dynamic lifecycle
  actions.
- Parser tests for `ccb agent add helper:codex --role ...`,
  profile-based add, invalid conflicting provider, and invalid missing role.
- Parser and behavior tests for `remove --policy auto|hide|park|unload|kill`.
- Fake tmux smoke for `visible -> hidden -> visible`.
- Fake tmux smoke for `visible -> parked -> visible`.
- Dynamic role smoke for:
  `add reviewer:codex --role agentroles.code_reviewer --hidden`,
  `show reviewer`,
  `remove reviewer --policy park`,
  `resume reviewer`,
  `remove reviewer --policy unload --idle-only`.
- Fake execution smoke for `1->4` worker/checker capacity and
  `4->0` idle release.
- Busy release smoke proving retained agents are not killed.
- Negative smoke proving `remove --policy kill` fails without both `--force`
  and `--reason`.
- Restart smoke proving parked long-lived roles are discoverable and resumable.
- Negative skill tests proving roles refuse raw tmux, raw reload, raw kill,
  and hard unload of long-lived roles.

## Current Landed Slice

Current worktree slice:

- `ccb agent status --json`;
- `ccb agent show <agent> --json`;
- `ccb agent add <name[:provider]> --profile <profile> ... --json`;
- `ccb agent add <name[:provider]> --role <role> ... --json`;
- `ccb agent hide <agent> --json`;
- `ccb agent park <agent> --json`;
- `ccb agent resume <agent> [--visible|--hidden] --json`;
- `ccb agent remove <agent> --policy auto|hide|park|unload|kill ... --json`;
- `ccb agent release <agent> --policy auto|hide|park|unload ... --json`;
- dynamic lifecycle state under `.ccb/runtime/agents/<agent>/lifecycle.json`;
- dynamic config overlay that places active dynamic agents through explicit
  `--window`, `--window-class`, or `--loop-id/--node-id` intent without
  rewriting `.ccb/ccb.config`;
- append-only hot add into an existing managed window and hot creation of a
  new managed window through the guarded `ccb reload` transaction;
- idle `remove --policy unload --idle-only` now applies the guarded
  `remove_agent` reload path, closes only the target dynamic pane, unloads its
  runtime authority, and removes the dynamic overlay from the projected config;
- `release` is the non-kill command surface for role-policy release. It defaults
  to `auto`, unloads short-lived execution roles, and parks unknown/long-lived
  roles unless an explicit non-kill policy is supplied;
- `scripts/dynamic_agent_lifecycle_smoke.py` now provides a repeatable
  source-wrapper policy smoke for explicit `[windows]`: long-lived planner
  helpers must park on `release --policy auto`, reject normal `ask` while
  parked, resume without pane replacement, and regain ask reachability;
  short-lived reviewer helpers must unload on `release --policy auto` and
  disappear from layout/runtime state.
- `park` now means "keep runtime/pane context but disable dispatch":
  lifecycle state `parked` projects `dispatch_disabled=true` into the active
  config, the reload planner treats that as a config-only `view_only_change`,
  direct `ask` rejects the parked agent, and broadcast dispatch skips it;
- `resume` clears the dispatch-disabled projection without changing pane
  ownership or restarting the provider;
- busy dynamic agents are retained with `retained_busy` instead of being killed
  or silently removed;
- lifecycle records now retain placement intent and applied evidence, including
  `window_name`, `pane_id`, `last_pane_id`, `plan_class`,
  `runtime_mount_status`, unloaded-agent lists, and published graph version;
- safety gate requiring `remove --policy kill --force --reason`.

Verification evidence:

- `PYTHONPATH=lib pytest -q test/test_agent_lifecycle_cli.py` passed with
  `15 passed`, including parser, dry-run plan coverage for `--window`,
  `--window-class`, `--loop-id/--node-id` placement, mounted unload apply
  evidence, and `agent release` auto-policy behavior.
- Targeted reload tests passed for both existing-window and new-window dynamic
  overlays:
  `test_additive_reload_apply_dynamic_agent_overlay_materializes_tmux_pane_before_mount`
  and
  `test_additive_reload_apply_dynamic_agent_overlay_materializes_new_window_before_mount`.
- Targeted focused suite passed with `35 passed`, covering agent lifecycle,
  loop capacity, layout planning/smoke surfaces, pane growth, and both dynamic
  reload apply tests.
- Broader focused suite passed with `43 passed`, covering agent lifecycle,
  loop capacity, layout planning/smoke surfaces, pane growth, plan tasks,
  orchestrator RolePack projection, and both dynamic reload apply tests.
- Focused dispatch-disabled suite passed with `150 passed`:
  `PYTHONPATH=lib pytest -q test/test_agent_lifecycle_cli.py
  test/test_v2_config_loader.py test/test_v2_ccbd_dispatcher.py`.
- Reload-focused suite passed with `70 passed`:
  `PYTHONPATH=lib pytest -q test/test_ccbd_reload_dry_run.py
  test/test_ccbd_reload_apply.py test/test_ccbd_reload_runtime_mount.py
  test/test_pane_growth_layout.py test/test_layout_cli.py`.
- External source-wrapper smoke passed in
  `/home/bfly/yunwei/test_ccb2/agent-lifecycle-real.o4yC4g`:
  add dynamic `helper:fake` while unmounted, validate projected config,
  start project with `main + helper`, ask `helper`, watch fake-provider reply,
  kill project, unload `helper`, and validate config returns to `main`.
- External mounted smoke in
  `/home/bfly/yunwei/test_ccb2/agent-hot-add.i5WEIQ` intentionally used
  `fake-codex`; it failed because `ps` exposed no preserved pane for `main`.
  The user-facing error now includes:
  `stage=namespace_patch`, `plan_class=add_agent`,
  `reason=namespace_patch_failed`, and
  `anchor pane missing for preserved agent 'main'`.
- Controlled mounted tmux smoke with seeded preserved pane identity passed for
  existing-window append in
  `/home/bfly/yunwei/test_ccb2/agent-hot-pane-ident.otr4SM`:
  `ccb_test agent add helper:fake-codex --role agentroles.general --window main --hidden --json`
  returned `apply_status=applied`, `plan_class=add_agent`, a new `pane_id`,
  `runtime_mount_status=mounted`, and `ask helper` completed.
- Controlled mounted tmux smoke with seeded preserved pane identity passed for
  new-window creation in
  `/home/bfly/yunwei/test_ccb2/agent-hot-window-ident.Xj9dR6`:
  `ccb_test agent add helper:fake-codex --role agentroles.general --window review --hidden --json`
  returned `apply_status=applied`, `plan_class=add_window`, `window_name=review`,
  a new `pane_id`, `runtime_mount_status=mounted`, and `ask helper` completed.
- Controlled mounted tmux smoke with seeded preserved pane identity passed for
  existing-window add, busy retain, idle unload, and post-unload `ps` cleanup in
  `/home/bfly/yunwei/test_ccb2/agent-hot-remove-pty.2FIiGo`:
  `agent add --window main` returned `add_agent`, `ask helper` completed,
  an early `remove --policy unload --idle-only` returned `retained_busy` while
  the job was busy, and the retry after completion returned `remove_agent`,
  `runtime_mount_status=unloaded`, `unloaded_agents=helper`, `pane_id=null`,
  `last_pane_id=%2`, and `ps` no longer listed `helper`.
- Controlled mounted tmux smoke passed for new-window add and unload in
  `/home/bfly/yunwei/test_ccb2/agent-hot-window-remove-pty.RqWVcE`:
  `agent add --window review` returned `add_window`, `ask helper` completed,
  `remove --policy unload --idle-only` returned `remove_agent` and
  `runtime_mount_status=unloaded`, and tmux `list-windows` showed the empty
  `review` window was removed while the main workspace remained.
- Controlled mounted tmux cycle smoke passed in
  `/home/bfly/yunwei/test_ccb2/agent-hot-cycle-pty.Tu9DCH`: starting from one
  `main` pane, five dynamic agents were hot-added into the same window to reach
  six panes, then released in reverse with
  `agent release --policy unload --idle-only`; final tmux panes returned to
  `%1:main`, and `ping ccbd` reported `known_agents: ['main']`.
- External mounted source-wrapper smoke passed in
  `/home/bfly/yunwei/test_ccb2/hotload-smoke-1782474327`: starting from
  `main:fake-codex`, seeded preserved pane identity for the fake provider,
  `agent add helper --window main` returned `add_agent` with pane `%2`,
  `ask helper` completed, `agent park helper` returned `view_only_change`,
  preserved `%2`, and direct `ask helper` failed with
  `agent helper is dispatch-disabled`; `agent resume helper --hidden` returned
  `view_only_change` and `ask helper` completed again. The same smoke then
  created a new `review` window with `reviewer` (`add_window`, pane `%4`),
  verified `ask reviewer`, released reviewer and helper through idle unload,
  removed the empty `review` window, and returned `known_agents` to `['main']`.
- External dynamic lifecycle policy smoke passed in
  `/home/bfly/yunwei/test_ccb2/lifecycle-policy-smoke.json`: explicit
  `[windows]` startup mounted `frontdesk` and `planner`; dynamic
  legacy `planner_helper:fake --role agentroles.ccb_planner --window-class
  plan-orchestrate --hidden` returned `role_class=long_lived_interactive` and
  `plan_class=add_agent`; `release planner_helper --idle-only` returned
  `resolved_policy=park`, `lifecycle_state=parked`,
  `plan_class=view_only_change`, and preserved the pane; direct `ask
  planner_helper` failed with `agent planner_helper is dispatch-disabled`;
  `resume planner_helper --hidden` restored ask reachability; dynamic
  `reviewer_helper:fake --role agentroles.code_reviewer --window-class
  plan-orchestrate --hidden` returned `role_class=short_lived_execution`;
  `release reviewer_helper --idle-only` returned `resolved_policy=unload`,
  `plan_class=remove_agent`, and removed the reviewer pane; cleanup returned
  layout status to only static `frontdesk` plus `planner` with
  `dynamic_agent_count=0`. Script unit tests passed with `5 passed`, adjacent
  lifecycle/layout script regression passed with `49 passed`, and
  `git diff --check` passed.

Known V1 gap:

- Running `agent add` against an already mounted project still requires
  preserved pane identity for existing managed panes. If the startup path or a
  test adapter does not stamp/expose that identity, CCB rejects the reload
  instead of risking active pane drift.
- Full live provider smoke with `codex`/`claude` remains separate from the
  controlled fake-provider tmux proof.
- Live reflow into the 1->6 visual pattern is now landed for fully managed
  agent windows with one to six effective agent panes. The implementation
  preserves pane IDs and provider sessions while arranging `p1,p3,p5` in the
  left column and `p2,p4,p6` in the right column; unsupported window shapes
  still fall back to tmux even compaction. Manual drag/drop and arbitrary
  cross-window movement remain deferred.

## Open Questions

1. Should `sleeping` be included in V1, or should V1 use only `parked` and
   `unloaded`?
2. Should inline `ccb agent add name:provider --role ...` be public in V1, or
   should dynamic creation remain behind profiles and role-specific commands
   until diagnostics are mature?
3. How much provider-native session restoration can be promised for each
   provider after unload?
4. Should parked panes live in a hidden tmux window, a runtime window, or a
   ccbd-only provider session with no visible pane?
