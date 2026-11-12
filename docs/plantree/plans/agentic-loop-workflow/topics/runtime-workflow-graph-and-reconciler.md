# Runtime Workflow Graph And Reconciler

Date: 2026-06-30

## Scope Update

This document records the landed desired-state topology controller and the
earlier broader workflow-graph direction. Decision 020 narrows the preferred
future contract: topology should become **mount topology** for agents,
windows, panes, providers, and lifecycle. Normal communication flow should use
CCB `ask` plus small document anchors instead of expanding topology into a
general dispatch DSL.

Keep the implementation evidence in this document, but treat sections about
information-flow edges, call ordering, and release gates as legacy or
experimental runner-dispatch scope unless a later decision explicitly restores
them.

## Purpose

Replace direct orchestrator-driven agent load/release with a desired-state
runtime workflow graph.

The graph is more than an agent list. It records the planned agent topology,
runtime groups, information-flow order, calls, artifact handoffs, verification
gates, and lifecycle release rules for one loop or round.

The design keeps the established principle:

```text
program kernel stays simple and stable
semantic flexibility belongs to roles
scripts commit and reconcile authority state
```

## Core Idea

`orchestrator` proposes the graph. CCB scripts commit it. A reconciler applies
runtime changes.

```text
orchestrator
  writes semantic topology proposal
    ↓
ccb loop topology validate / commit
  writes desired topology revision
    ↓
topology reconciler
  compares desired vs observed
    ↓
agent lifecycle + layout + capacity + readiness
  converge runtime to desired state
```

This is closer to a desired-state controller than a manager role directly
running imperative commands.

## CCB Workflow Window Mapping

The reconciler maps the current workflow Role/profile names to deterministic
window names when a desired agent does not provide an explicit `window_name` or
`window_class`.

| Logical Window | Default Window | Profiles | Lifecycle Default |
| :--- | :--- | :--- | :--- |
| Window 1: user interaction | `ccb-user` | `ccb_frontdesk`, `ccb_task_detailer` | Visible; resident or on-demand, but context rules stay role-specific. |
| Window 2: planning and orchestration | `ccb-plan` | `ccb_planner`, `ccb_orchestrator`, `ccb_round_reviewer` | Visible; planner may retain compact context, immaculate roles clear per activation. |
| Window 3+: execution workgroups | `ccb-exec`, `ccb-exec-2`, ... | `coder`, `code_reviewer` | Visible while active; unload only after idle/evidence gates. |

`ccb_round_reviewer` belongs in Window 2 because it reviews whole-round
evidence and feeds planner/orchestrator decisions for the next loop. It is
round-scoped, but it is not part of a single coder/reviewer work unit, so
placing it in execution windows would blur the per-node evidence boundary.

Execution windows pack profiles in desired-order chunks of six panes. With the
recommended `coder + code_reviewer` work unit, one execution window holds up to
three work units. The seventh execution agent starts `ccb-exec-2`; after
release or park removes active execution agents, later agents are moved back
into the first available execution window during reconcile.

The current V1 product direction deliberately avoids hidden default placement
for workflow roles. Visibility is controlled by deterministic windows rather
than backgrounding the agent: `ccb-user` holds the user-facing boundary and
task-local detail surface, `ccb-plan` holds planning/orchestration/round
review, and `ccb-exec*` pages hold execution workgroups. Context freshness is
still enforced separately by the immaculate-role contract; visible residency is
not permission to reuse old conversation state.

## Runtime Files

Candidate loop-local layout:

```text
.ccb/runtime/loops/<loop-id>/
  agent_topology.desired.json
  agent_topology.observed.json
  agent_topology.events.jsonl
  agent_topology.lock
  topology_proposals/
    <proposal-id>.json
```

### `agent_topology.desired.json`

Authority target written only by `ccb loop topology commit`.

Minimum fields:

```json
{
  "schema": "ccb.loop.agent_topology.v1",
  "record_type": "ccb_loop_agent_topology_desired",
  "topology_status": "committed",
  "loop_id": "loop-123",
  "revision": 4,
  "base_revision": 3,
  "proposal_id": "proposal-001",
  "committed_at": "2026-07-02T00:00:00Z",
  "nodes": [],
  "edges": [],
  "artifacts": {},
  "gates": [],
  "release_policy": {"policy": "auto", "idle_only": true}
}
```

Minimum desired node/agent fields:

| Field | Meaning |
| :--- | :--- |
| `nodes[].id` | Stable topology grouping key for validation and evidence. |
| `nodes[].agents[].id` | Concrete CCB agent name; generated only when a loop id is available. |
| `nodes[].agents[].profile` | Required `loop.role_profiles` key. V1 built-in placement recognizes only `ccb_frontdesk`, `ccb_task_detailer`, `ccb_planner`, `ccb_orchestrator`, `ccb_round_reviewer`, `coder`, and `code_reviewer`. |
| `nodes[].agents[].desired_state` | `present`, `hidden`, `parked`, or `absent`. |
| `nodes[].agents[].window_name` | Optional explicit override. |
| `nodes[].agents[].window_class` | Optional placement intent for the lower-level dynamic placement resolver. |
| `nodes[].agents[].release_policy` | Optional `auto`, `hide`, `park`, or `unload`; otherwise inherited from topology `release_policy`. |

### `agent_topology.observed.json`

Observed runtime state written by the reconciler.

Minimum fields:

```json
{
  "schema": "ccb.loop.agent_topology.observed.v1",
  "record_type": "ccb_loop_agent_topology_observed",
  "loop_id": "loop-123",
  "desired_revision": 4,
  "last_reconcile_status": "reconciled",
  "agents": [],
  "edges": [],
  "actions": [],
  "retained": [],
  "retained_count": 0,
  "released_count": 0,
  "drift": {"mismatched_agents": []}
}
```

### `agent_topology.events.jsonl`

Append-only diagnostic events:

```json
{"event": "commit", "revision": 4, "proposal_id": "proposal-001"}
{"event": "ensure_agent", "agent": "wf-coder-1", "state": "ready"}
{"event": "release_requested", "agent": "wf-coder-1", "policy": "auto"}
{"event": "retained_busy", "agent": "wf-code-reviewer-1", "reason": "ask_running"}
```

## Legacy Dispatch Compatibility Appendix

The following graph, edge, artifact, and gate material is preserved as
historical compatibility context for already-landed tests and migration. It is
not the current mainline workflow contract. New work should prefer
mount-topology plus ask-first orchestration from Decision 020.

## Legacy Graph Shape

The graph has four layers:

| Layer | Purpose |
| :--- | :--- |
| `nodes` | Agent instances or group members, roles, profiles, lifetime, placement intent. |
| `groups` | Runtime topology teams such as planning groups and execution workgroups. These are Project Binding or runtime state, not Agent Roles source. |
| `edges` | Information-flow and call relationships between agents or artifacts. |
| `artifacts` | Input and output records referenced by edges and gates. |
| `gates` | Conditions for dispatch, rework, release, round check, and planner reactivation. |

Example:

```json
{
  "groups": [
    {
      "id": "workgroup-node1",
      "kind": "execution_group",
      "purpose": "bounded implementation node",
      "lifecycle": "ephemeral",
      "desired_state": "present",
      "artifact_root": ".ccb/runtime/loops/loop-123/groups/workgroup-node1",
      "activation_policy": "all_members_ready_before_dispatch",
      "release_policy": "auto_after_artifacts_imported_and_idle",
      "placement": {"window_name": "ccb-exec"},
      "members": [
        {
          "id": "coder_1",
          "role": "agentroles.coder",
          "profile": "coder",
          "lifecycle": "ephemeral",
          "desired_state": "present"
        },
        {
          "id": "code_reviewer_1",
          "role": "agentroles.code_reviewer",
          "profile": "code_reviewer",
          "lifecycle": "ephemeral",
          "desired_state": "present"
        }
      ]
    }
  ],
  "nodes": [],
  "edges": [
    {
      "id": "edge-worker-node1",
      "from": "ccb_orchestrator",
      "to": "coder_1",
      "type": "ask",
      "order": 10,
      "input_artifact": "node1.task.md",
      "output_artifact": "node1.worker-result.md"
    },
    {
      "id": "edge-review-node1",
      "from": "coder_1",
      "to": "code_reviewer_1",
      "type": "ask_after",
      "after": ["edge-worker-node1"],
      "order": 20,
      "input_artifact": "node1.worker-result.md",
      "output_artifact": "node1.review.md"
    }
  ],
  "gates": [
    {
      "id": "release-node1",
      "type": "release_when",
      "agents": ["coder_1", "code_reviewer_1"],
      "condition": "artifacts_imported && agents_idle",
      "policy": "auto"
    }
  ]
}
```

Runtime groups are topology records, not RolePacks and not Agent Roles source
objects. A group must declare concrete members, roles, profiles, placement,
edges, gates, lifecycle, and release behavior that CCB should reconcile.
Collection ids are not runtime selection keys.

Plan-tree brief documents, task-scoped detail docs, and task detail packets may
appear in topology artifacts or edge inputs only as explicit refs. They do not
imply role selection, runtime membership, or Collection-based mounting.

Role Collections relevant to installing common runtime roles:

| Collection | Install Use | Required Members | Runtime Boundary |
| :--- | :--- | :--- | :--- |
| `agentroles.collections.planning_group` | Install the CCB planner and optional planning-adjacent capabilities. | `agentroles.ccb_planner` | Does not imply shared conversation, task-detailer activation, or automatic mount. |
| `agentroles.collections.execution_workgroup` | Install default bounded implementation and review Roles together. | `agentroles.coder`, `agentroles.code_reviewer` | Runtime topology still selects concrete agents, edges, and release gates. |
| `agentroles.collections.agentic_loop_core` | Install the common CCB workflow Role set. | `agentroles.ccb_frontdesk`, `agentroles.ccb_planner`, `agentroles.ccb_orchestrator`, `agentroles.ccb_task_detailer`, `agentroles.ccb_round_reviewer`, `agentroles.coder`, `agentroles.code_reviewer` | Install bundle only; runtime topology remains explicit. |

The `planning_group` runtime shape does not imply that `ccb_planner` and
`ccb_task_detailer` share one conversation or that `ccb_task_detailer` is
always present. `ccb_planner` publishes a brief and macro task ref;
`ccb_orchestrator` triage decides whether direct execution is possible or
whether a short-lived detailer pass is needed. `ccb_task_detailer` maintains
task-scoped detail docs, returns its detail packet to `ccb_orchestrator`, and
submits task-scope macro adjustment requests for planner review through plan
authority.

## Legacy Edge Semantics

Edges are not decorative arrows. Each edge must have enough information for
scripts to validate ordering and for humans to audit the workflow.

Minimum edge fields:

| Field | Meaning |
| :--- | :--- |
| `from` | Source agent or artifact producer. |
| `to` | Target agent or artifact consumer. |
| `type` | V1 dispatch supports `ask` and `ask_after`. Other semantic edge types such as `artifact_read`, `handoff`, `status_report`, `group_ready`, `release_gate`, or `release_when` remain design candidates and must be rejected by the runner until implemented. |
| `order` | Stable ordering hint for deterministic display and simple dispatch. |
| `after` | Edge ids that must complete before this edge can run. |
| `input_artifact` | Artifact consumed by the edge. |
| `output_artifact` | Artifact expected from the edge. |
| `condition` | Optional condition for conditional handoff or release. |
| `timeout_policy` | How long the edge can wait before becoming stalled. |
| `failure_policy` | `retry`, `freeze_branch`, `replan_required`, or `escalate`. |

V1 now validates edge types and dependency acyclicity before commit. The runner
also performs a second guard at dispatch time, because runtime files may be
stale or hand-edited after commit.

Current V1 dispatch behavior is intentionally small:

- only `ask` and `ask_after` execute;
- observed topology must be `reconciled`, match the desired revision, and have
  no drift;
- each edge source and target must resolve to a ready observed agent, except
  pseudo-sources `user` and `system`;
- edges execute through a deterministic sequential executor ordered by
  `order`, then proposal order, with `after` dependencies required to have
  completed earlier in that sequence;
- unsupported edge types, missing endpoints, missing targets, stale observed
  revisions, drift, non-ready agents, missing dependencies, and cycles fail
  before ask submission;
- dispatch writes `topology_dispatch.json`,
  `topology_dispatch.events.jsonl`, per-edge reply artifacts, and a
  round-compatible `round.json`.

This is not a general DAG scheduler yet. Conditional branches, retries,
release gates, artifact import policy, and rework loops remain future slices.

## Reconciler Activation

V1 should avoid a background watcher. Reconciliation happens explicitly:

```bash
ccb loop topology commit --loop-id loop-123 --proposal proposal-001 --apply --json
ccb loop topology reconcile --loop-id loop-123 --json
```

`loop runner --once` should call reconcile at stable boundaries:

1. Before execution round start.
2. Before ask dispatch to required targets.
3. After node work drains.
4. After round check and writeback.
5. During release cleanup.

V2 may move this into ccbd:

```text
desired revision changes
  -> debounce
  -> loop-level lock
  -> reconcile
  -> observed/events update
```

## Diff Rules

Reconciler behavior:

| Desired vs Observed | Action |
| :--- | :--- |
| desired agent present, observed missing | load or ensure agent. |
| desired agent present, observed ready | keep. |
| desired agent present, observed failed | repair or mark blocker. |
| desired placement changed, same agent | move/reflow without provider restart when safe. |
| desired removed, observed idle ephemeral | unload after evidence gate. |
| desired removed, observed busy | mark `draining` / `retained_busy`; do not kill. |
| desired parked, observed visible | park/hide while preserving context. |
| desired absent, observed residue | cleanup only after ownership proof. |

The reconciler should not silently reduce node count, swap providers, or
downgrade acceptance criteria. If desired cannot be applied, it records drift
and returns a structured blocker.

### Responsibility Boundary

`ccb_orchestrator` may propose desired topology, including semantic nodes,
agent profiles, asks, artifacts, gates, and release preferences. It must not
run raw tmux commands, reload the namespace directly, kill panes, or mutate
runtime lifecycle files.

The CCB host/topology reconciler owns:

- validation against `loop.role_profiles`, profile capacity, edge references,
  and stale base revisions;
- committing the desired revision;
- comparing desired agents with observed dynamic lifecycle records;
- calling lifecycle operations for load, release, hide, park, resume, and move;
- calling layout arrange/reflow after agent placement changes;
- writing observed topology, drift, retained-busy records, and events.

### Lifecycle Operation Semantics

| Operation | Reconciler Meaning |
| :--- | :--- |
| `load` | Add a missing desired agent through dynamic lifecycle using the profile's role/provider/workspace policy. |
| `unload` | Remove an idle short-lived execution agent and its pane after ownership and idle gates pass. |
| `park` | Retain context, disable dispatch, and keep the lifecycle record for long-lived or busy-sensitive roles. |
| `hide` | Keep the agent running and dispatchable while removing it from active visual focus where supported. |
| `move` | Change placement metadata and reflow without restarting the provider session when the dynamic agent remains owned. |
| `reflow` | Recompute pane order/layout for affected windows after add, release, park/hide, move, or overflow compaction. |

### Reflow Rules

For one window with one to six panes, order is stable in the desired/effective
agent list. Growth appends panes and balances the tmux layout; shrink removes
only the released idle pane and reflows survivors. A 6->1 shrink keeps the
remaining pane identity/context instead of restarting the agent.

For execution overflow, active `coder` and `code_reviewer` agents are chunked
six per window:

```text
1..6   -> ccb-exec
7..12  -> ccb-exec-2
13..18 -> ccb-exec-3
```

When active execution count falls back below a page boundary, reconcile moves
survivors from later execution windows into earlier windows, reflows the target
window, and lets the namespace patch remove empty overflow windows.

## Lifecycle States

Desired states:

| State | Meaning |
| :--- | :--- |
| `present` | Agent should exist and be dispatchable when ready. |
| `parked` | Agent should retain context but not receive normal dispatch. |
| `hidden` | Agent should remain running but outside the active view. |
| `absent` | Agent should be released or no longer owned by this topology. |

Observed states:

| State | Meaning |
| :--- | :--- |
| `missing` | Required runtime agent is not present. |
| `starting` | Runtime is being created. |
| `ready` | Agent is mounted and askable. |
| `busy` | Ask/job/provider state is active. |
| `draining` | Release requested but busy state prevents unload. |
| `parked` | Agent retained but dispatch disabled. |
| `releasing` | Cleanup transaction in progress. |
| `released` | Runtime agent removed or ownership detached. |
| `failed` | Reconciler could not prove readiness or cleanup. |

## Command Surface

V1 topology commands:

```bash
ccb loop topology propose --loop-id <id> --from <file> --json
ccb loop topology validate --loop-id <id> --proposal <proposal-id> --json
ccb loop topology commit --loop-id <id> --proposal <proposal-id> --apply --json
ccb loop topology reconcile --loop-id <id> --json
ccb loop topology status --loop-id <id> --json
ccb loop topology release --loop-id <id> --policy auto --json
```

Possible later command:

```bash
ccb loop topology patch --loop-id <id> --from <file> --apply --json
```

## Validation Rules

Before commit:

- `base_revision` must match unless the caller explicitly rebases.
- Active topology agent count must stay within configured loop capacity.
- Every role/profile must be declared in allowed project policy.
- Concrete role ids for the current CCB workflow are
  `agentroles.ccb_frontdesk`, `agentroles.ccb_planner`,
  `agentroles.ccb_orchestrator`, `agentroles.ccb_task_detailer`,
  `agentroles.ccb_round_reviewer`, `agentroles.coder`, and
  `agentroles.code_reviewer`.
- Runtime groups must not be treated as Agent Roles source objects.
- Runtime groups must not use Collection ids as membership, permission, or
  automatic mount authority.
- Group members must resolve to concrete mounted or mountable roles and allowed
  profiles through Project Binding or topology policy.
- `execution_group` should include at least one `coder` and one
  `code_reviewer` unless the proposal explicitly marks a research-only or
  review-only exception.
- Agent ids must be unique within the loop.
- Edge graph must be acyclic.
- `after` references must point to existing edge ids.
- Artifacts referenced by required edges must be declared.
- Release gates must not target long-lived roles for hard unload by default.
- Busy release must resolve to `draining` or `retained_busy`, never forced
  unload.
- Window and pane placement is validated by CCB layout logic, not chosen
  freely by `orchestrator`.

## Relationship To Existing Capacity And Lifecycle Work

`loop.role_profiles` remains the source policy for provider, model, thinking,
workspace, role id, max instances, and reuse behavior.

`ccb loop capacity ensure/status/release` remains a useful lower-level
implementation substrate. It can be called by the reconciler or retained as a
compatibility/debugging surface.

`ccb agent add/remove/release/park/resume` remains useful for operator and
non-loop dynamic agents.

The preferred orchestrator-facing contract is now:

```text
orchestrator-topology skill
  -> ccb loop topology propose / status / commit
```

not:

```text
orchestrator-capacity skill
  -> ccb loop capacity ensure / release
```

## Failure Handling

Failure should be visible and durable:

- validation failure rejects the proposal before desired topology changes;
- reconcile failure records drift in observed state;
- retained busy agents stay owned until a later reconcile can release them;
- repeated same-signature reconcile failure escalates to monitor/recovery;
- runtime drift does not become semantic success;
- planner/frontdesk receive compact blockers only after deterministic recovery
  cannot progress.

## Implementation Status

V1 desired-state topology control is landed in the current worktree:

- `ccb loop topology propose/validate/commit/reconcile/status/release` is
  available as a scriptable JSON command surface;
- proposal validation covers role profile existence, profile capacity limits,
  duplicate node ids, duplicate agent ids, unknown edge dependencies, and edge
  dependency cycles;
- commit writes revisioned `agent_topology.desired.json`;
- reconcile writes `agent_topology.observed.json` and delegates runtime
  changes to existing dynamic agent lifecycle and layout services;
- default placement maps the current workflow profiles to `ccb-user`,
  `ccb-plan`, and packed `ccb-exec` windows;
- reconcile batches missing agent lifecycle records before mounted reload, and
  dynamic runtime windows render append-compatible layout specs so an existing
  execution page can grow without replacing surviving panes;
- `loop runner --once` can now consume a committed topology graph for a task
  already bound to that loop and dispatch supported `ask` / `ask_after` edges
  after observed topology is fresh and ready;
- topology dispatch writes per-edge status, job ids, replies, and artifact
  paths, then imports the resulting `round.json` through existing
  `plan task-import-round` authority;
- tested runtime actions include add, move, park, release, and reflow;
- post-review hardening covers release policy propagation, long-lived auto
  park semantics, partial reconcile failure recording and recovery, busy-agent
  retain, cross-loop isolation, stale base revision rejection, reactivation
  after release, duplicate node rejection, execution overflow, and overflow
  compaction.

Evidence:
[history/runtime-topology-reconciler-2026-06-30.md](../history/runtime-topology-reconciler-2026-06-30.md).

Remaining legacy-dispatch work is limited to compatibility guards and
migration safety. Do not broaden this runner path into release gates, typed
edge artifact scheduling, conditional/rework branches, or a general workflow
DAG unless a later decision explicitly reverses Decision 020.

## Implementation Slice

Initial slice status:

1. Done: read/write schemas and CLI validation for topology proposals.
2. Done: commit validated proposals as `agent_topology.desired.json`
   revisions.
3. Done: read-only topology status over desired/observed summaries.
4. Done: explicit V1 reconcile delegates to existing lifecycle and layout
   code.
5. Done: default CCB workflow role placement and packed execution-page
   compaction for Window 1/2/3+.
6. Done: `loop runner --once` consumes a committed topology graph for a bound
   loop and dispatches `ask` / `ask_after` edges in deterministic dependency
   order.
7. Done: fake-provider smoke proves committed topology drives ordered asks to
   `coder`, `code_reviewer`, and `ccb_round_reviewer`, writes edge evidence,
   and imports the round result.
8. Compatibility only: keep legacy graph dispatch tests explicit and guarded;
   do not add new mainline edge/gate features.

## Test Targets

- Proposal validation: duplicate agent ids, invalid profile, stale base
  revision, and mainline rejection of `edges`, `gates`, and `artifacts`.
- Legacy-dispatch compatibility validation: explicit legacy flag, invalid edge
  dependency, graph cycle, missing artifact, stale observed revision, drift,
  and not-ready target rejection.
- Commit: desired revision increments, proposal id and actor are recorded,
  events are appended.
- Reconcile load: desired present + observed missing creates ready agents.
- Reconcile keep: desired present + observed ready is idempotent.
- Reconcile release: desired absent + idle ephemeral unloads and reflows.
- Busy release: desired absent + busy records `retained_busy` and does not
  kill or remove the pane.
- Placement change: move/reflow preserves provider session when ownership is
  unchanged.
- Mainline loop runner smoke: no topology edges; mount topology makes agents
  askable, normal `ask` collaboration produces `round_summary`, scripts import
  the summary, and dynamic execution agents release.
