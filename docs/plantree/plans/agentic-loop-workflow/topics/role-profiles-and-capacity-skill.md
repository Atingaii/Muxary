# Role Profiles And Capacity Skill

Date: 2026-06-24

## Purpose

Define the profile and capacity substrate for dynamic execution nodes:

1. `loop.role_profiles` in `.ccb/ccb.config`, where users declare which
   role/provider/model/thinking/workspace combinations are allowed.
2. A `ccb loop capacity` script protocol that can ensure, inspect, and release
   concrete node capacity by profile name and count.

This document originally described an `orchestrator-capacity` skill. The
current preferred design is topology-driven:

```text
orchestrator proposes topology
  -> ccb loop topology commits desired state
  -> topology reconciler uses role profiles, capacity, lifecycle, and layout
```

The goal is no longer to let `orchestrator` directly request dynamic capacity.
The goal is to keep provider/model/thinking/profile policy declarative while
the topology reconciler safely loads and releases execution agents.

For the broader lifecycle policy shared by frontend, planner, orchestrator,
and execution roles, see
[dynamic-agent-lifecycle-and-skills.md](dynamic-agent-lifecycle-and-skills.md).
This document remains focused on orchestrator execution capacity.

## Design Principle

Separate source policy from runtime instances.

```text
.ccb/ccb.config
  declares allowed loop capacity profiles

orchestrator-topology skill
  proposes graph nodes, edges, artifacts, and release gates

ccb loop topology commit/reconcile
  validates graph intent and commits desired topology

ccb loop capacity ensure/release/status
  remains a lower-level substrate for creating or releasing concrete profile
  instances when the reconciler needs it

runtime layout manager / ccbd / guarded reload
  performs window, pane, provider, service-graph, and runtime-authority mutation
```

`orchestrator` may submit topology intent only through the narrow topology
surface. Capacity and lifecycle surfaces are permission boundaries for scripts
and operators, not the normal orchestrator path.

## Config Shape

Proposed rich TOML shape:

```toml
[loop.capacity]
enabled = true
max_nodes = 4
default_lifetime = "current_round"
name_template = "loop-{loop_id}-{profile}-{index}"
reuse = "prefer_idle"

[loop.role_profiles.coder]
role = "agentroles.coder"
provider = "codex"
model = "gpt-5.5"
thinking = "high"
workspace_mode = "git-worktree"
max_instances = 4
reuse = "prefer_idle"

[loop.role_profiles.checker]
role = "agentroles.checker"
provider = "codex"
model = "gpt-5.5"
thinking = "medium"
workspace_mode = "git-worktree"
max_instances = 4
reuse = "prefer_idle"

[loop.role_profiles.round_checker]
role = "agentroles.round_checker"
provider = "claude"
model = "opus"
thinking = "high"
workspace_mode = "inplace"
max_instances = 1
reuse = "prefer_idle"
```

### `loop.capacity`

Fields:

| Field | Meaning |
| :--- | :--- |
| `enabled` | Whether script-driven loop capacity is allowed. |
| `max_nodes` | Project-wide maximum dynamic execution nodes per loop. Default should be `4`. |
| `default_lifetime` | Default lifetime for generated agents, usually `current_round`. |
| `name_template` | Deterministic generated-agent name pattern. |
| `reuse` | Default reuse policy for idle matching agents. |

Allowed lifetime values:

- `current_round`
- `current_loop`
- `manual_release`

Allowed reuse values:

- `prefer_idle`: reuse idle matching agents before creating new ones.
- `always_new`: create fresh agents unless max capacity blocks it.
- `pinned`: use an existing configured long-lived agent matching the profile.

### `loop.role_profiles.<profile>`

Fields:

| Field | Meaning |
| :--- | :--- |
| `role` | RolePack id, for example `agentroles.coder`. |
| `provider` | CCB provider id. |
| `model` | Optional provider model shortcut, following current agent model rules. |
| `thinking` | Provider-neutral reasoning intensity request. |
| `workspace_mode` | Same semantics as agent workspace mode. |
| `workspace_group` | Optional group/template for shared git-worktree behavior. |
| `startup_args` | Optional advanced provider args; must not conflict with `model` or `thinking`. |
| `provider_profile` | Optional provider profile overlay, same boundary as agent overlays. |
| `max_instances` | Per-profile maximum active generated agents. |
| `reuse` | Optional per-profile override. |

`role`, `provider`, and `max_instances` should be required. `model`,
`thinking`, workspace, startup args, and provider profile fields are optional.

`thinking` is a source-level intent field. Runtime implementation must map it
through provider adapters. If a provider does not support a requested thinking
level, validation should fail visibly instead of silently ignoring it.

## Command Surface

The capacity substrate should expose only three command families. These may be
called by topology reconciliation, by operator diagnostics, or by legacy
compatibility flows.

### Ensure

```bash
ccb loop capacity ensure \
  --loop-id loop_123 \
  --profile coder=2 \
  --profile checker=2 \
  --lifetime current_round \
  --json
```

Responsibilities:

- Parse requested profile counts.
- Validate `loop.capacity.enabled`.
- Validate profile names exist in config.
- Enforce project and per-profile max counts.
- Reuse idle matching agents when allowed.
- Create missing agents through CCB-owned runtime mutation.
- Return ready ask targets or structured blockers.
- Return placement evidence such as `node_id`, `window_name`, or `placement`
  when available; these fields are CCB-owned evidence, not orchestrator input.
- Record capacity ownership under runtime loop state.

Example output:

```json
{
  "status": "ok",
  "loop_id": "loop_123",
  "capacity_ref": ".ccb/runtime/loops/loop_123/capacity.json",
  "agents": [
    {
      "name": "loop-loop_123-coder-1",
      "profile": "coder",
      "role": "agentroles.coder",
      "provider": "codex",
      "lifetime": "current_round",
      "node_id": "node1",
      "placement": {"mode": "execution_node", "window_name": "node-loop_123-node1"},
      "source": "created",
      "state": "ready"
    }
  ],
  "rejected": []
}
```

### Status

```bash
ccb loop capacity status --loop-id loop_123 --json
```

Responsibilities:

- Report generated and reused agents for the loop.
- Report busy/idle/failed/readiness state.
- Report outstanding dispatcher work when known.
- Report why release is currently blocked.

### Release

```bash
ccb loop capacity release \
  --loop-id loop_123 \
  --idle-only \
  --lifetime current_round \
  --json
```

Responsibilities:

- Release only agents owned by the loop and matching the requested lifetime.
- Refuse to unload busy agents unless a later explicit force policy exists.
- Preserve long-lived pinned agents and only detach loop ownership.
- Return retained agents with reasons.
- Record final capacity release evidence in runtime loop state.

## Runtime Authority Model

`ccb loop capacity` owns all authoritative runtime writes. It may internally
reuse existing reload machinery, but that is an implementation detail.

Allowed implementation strategies:

1. Preferred target: daemon-side transient loop capacity overlay.
   `.ccb/ccb.config` declares profiles, while generated instances live under
   `.ccb/runtime/loops/<loop-id>/capacity.json` and the ccbd service graph.
2. Transitional implementation: CCB script renders generated config entries
   and calls the existing guarded reload transaction, but only inside a
   clearly marked CCB-generated block and with release cleanup.

`orchestrator` must not know which strategy is used.

The preferred target avoids turning short-lived execution nodes into durable
project config. The transitional strategy may be useful because current CCB
already has explicit `reload` support for append-only add-agent/add-window and
idle remove-agent.

For explicit `[windows]` layouts, the current runtime layout manager maps
loop-generated execution profiles into `node-<loop-id>-<node-id>` windows and
removes empty node windows after idle release. This placement behavior remains
an implementation contract of CCB, not an orchestrator choice.

## Topology Reconciler Contract

`ccb loop capacity` should be treated as a reconciler substrate. The
orchestrator-facing skill should become `orchestrator-topology`, which calls
`ccb loop topology` commands and receives status from desired/observed
topology state.

Reconciler triggers:

- After `ccb loop topology commit --apply`.
- Before dispatching work items when required topology targets may be missing.
- After round drain or partial completion when generated agents can be
  released.
- During recovery when observed topology drift needs a capacity explanation.

Inputs:

- loop id
- committed desired topology revision
- desired profiles and counts derived from graph nodes
- configured max node budget
- current capacity summary ref
- lifetime

Allowed actions:

- reconciler may call `ccb loop capacity ensure --json`
- reconciler may call `ccb loop capacity status --json`
- reconciler may call `ccb loop capacity release --json`
- reconciler writes observed topology and events
- loop runner or orchestrator may use committed/observed ready agent names as
  `ask` targets
- blockers are recorded in observed topology and may be included in
  partial/replan reports
- inspect `ccb layout status --json` only as a read-only diagnostic view for
  `source=loop`, `loop_id`, `node_id`, and pane evidence

Forbidden actions:

- normal orchestrator workflow calling `ccb loop capacity ensure/release`
  directly after topology commands exist
- edit `.ccb/ccb.config`
- call raw `ccb reload`
- call raw `ccb kill`
- call raw `ccb agent add --window` or `ccb agent add --window-class`
- kill tmux panes or provider processes
- hand-pick `node-<loop-id>-<node-id>` or any other execution window name
- invent provider/model/thinking values not present in `loop.role_profiles`
- exceed `max_nodes` or profile `max_instances`
- ignore failed validation and silently run fewer nodes as success

## Interaction With Work Slicing

Complexity assessment produces desired node counts:

```json
{
  "complexity_class": "split_parallel",
  "node_budget": 3,
  "profiles": {
    "coder": 3,
    "checker": 3
  }
}
```

Capacity ensure returns concrete agents:

```json
{
  "coder": ["loop-loop_123-coder-1", "loop-loop_123-coder-2"],
  "checker": ["loop-loop_123-checker-1", "loop-loop_123-checker-2"]
}
```

Only after this mapping exists should orchestrator generate final worker and
checker asks. If capacity cannot be satisfied, orchestrator should return
`replan_required`, `blocked`, or a reduced serial plan only when planner policy
explicitly allows serial fallback.

## Validation Gates

Config validation:

- Unknown profile fields fail.
- Unknown roles fail with the current role-store diagnostics.
- Profile provider/model/thinking conflicts fail.
- `max_nodes` and per-profile `max_instances` must be bounded.
- `name_template` must produce valid, collision-resistant agent names.

Command validation:

- Requests from non-loop contexts are rejected unless explicitly allowed.
- Requests can only reference declared profile names.
- Ensure is idempotent for the same loop/profile/count/lifetime.
- Release is idle-only by default.
- Busy release returns `retained`, not success.

Skill validation:

- Negative prompts prove the skill refuses raw reload/kill/config edits.
- Positive prompts prove it can request capacity by profile and consume returned
  ask targets.
- Blocked capacity must be surfaced as a structured blocker, not hidden by
  degradation.

## Open Implementation Choices

1. When to replace the transitional guarded-reload materialization with a
   daemon-side transient loop capacity overlay.
2. The exact provider adapter mapping for `thinking = "low|medium|high"`.
3. Whether `manual_release` lifetime should be allowed before cleanup and
   storage diagnostics are mature.
