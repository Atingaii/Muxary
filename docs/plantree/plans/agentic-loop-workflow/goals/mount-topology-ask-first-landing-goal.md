# Mount Topology Ask-First Landing Goal

Date: 2026-07-03
Status: In Progress

## Goal

Land the simplified workflow contract from Decision 020 in small, reviewable
phases:

```text
task documents activate workflow state
  -> orchestrator decides route
  -> CCB applies mount topology
  -> agents collaborate through ask
  -> scripts import stable evidence
  -> dynamic agents release or retain safely
```

The landing target is not a general workflow DSL. The program kernel remains
simple and stable; semantic flexibility stays with roles and `ask`.

## Current Phase Status

- Phase 0 contract freeze: complete in plan-tree.
- Phase 1 mount topology schema split: passed local worktree gate on
  2026-07-03. The current worktree writes
  `agent_mount_topology.desired.json`, accepts
  `ccb.loop.agent_mount_topology.v1`, keeps legacy `agent_topology.*` reads,
  rejects `edges`, `gates`, and `artifacts` by default, and requires explicit
  legacy compatibility for graph dispatch tests.
- Phase 2 document anchors and activation state: accepted in the current
  worktree after independent review.
- Phase 3A orchestrator triage: accepted in the current worktree after
  reviewer audit and source-wrapper smoke.
- Phase 4A direct-execution ask-first round: accepted in the current worktree
  after reviewer audit and source-wrapper smoke. The accepted path applies
  mount topology for `coder + code_reviewer`, uses ordinary CCB `ask` for
  collaboration, imports `round_summary`, releases the dynamic pair, writes no
  `topology_dispatch.json`, and keeps source/normalized/desired/observed
  topology free of absent `edges`, `gates`, and `artifacts`.
- Next target: Phase 5 release, retain, park, and reflow hardening.

## Non-Goals

- Do not add a background watcher in V1.
- Do not broaden topology dispatch into a DAG scheduler.
- Do not require every worker/reviewer exchange to be encoded as topology
  edges.
- Do not make planner, frontdesk, worker, or reviewer write authority files
  directly.
- Do not make real-provider credentials mandatory for source CI.

## Phase 0: Contract Freeze

### Landing Scope

- Treat [Decision 020](../decisions/020-mount-topology-and-ask-first-orchestration.md)
  as the current design authority.
- Keep [runtime-workflow-graph-and-reconciler.md](../topics/runtime-workflow-graph-and-reconciler.md)
  as landed topology-controller evidence, not the current communication-flow
  target.
- Freeze the V1 anchor names:
  `task_packet`, `execution_contract`, `agent_mount_topology`,
  `orchestration_notes`, and `round_summary`.

### Test Gate

- `git diff --check -- docs/plantree/README.md docs/plantree/plans/agentic-loop-workflow`
- Link check by `rg`:
  - Decision 020 appears in README, roadmap, status, and runtime graph topic.
  - No active status item says topology dispatch should be broadened as the
    mainline workflow DSL.

### Review Gate

- Reviewer agrees that topology owns only runtime mounting/lifecycle state.
- Reviewer agrees that `ask` is the default collaboration mechanism.
- Reviewer confirms every authority change has a script-owned import path.

## Phase 1: Mount Topology Schema Split

### Landing Scope

- Keep existing `ccb loop topology` command names for operator continuity.
- Add or alias schema semantics for `ccb.loop.agent_mount_topology.v1`.
- Prefer runtime filenames:

```text
.ccb/runtime/loops/<loop-id>/
  agent_mount_topology.desired.json
  agent_mount_topology.observed.json
  agent_mount_topology.events.jsonl
```

- Preserve backward-compatible reads of current `agent_topology.*` during the
  transition.
- Validate mount topology fields:
  - windows and pane order;
  - agents, role ids, profiles, provider/model/thinking snapshot;
  - lifecycle and release policy;
  - desired state and observed readiness/drift.
- Reject communication-flow-only fields in the mount schema unless an explicit
  legacy dispatch compatibility mode is selected.

### Test Gate

- Unit tests:
  - mount schema accepts windows, pane order, profiles, lifecycle, release
    policy, and provider snapshot;
  - mount schema rejects unsupported communication edges and call-order-only
    proposals;
  - legacy `agent_topology.*` files can still be read for migration;
  - stale revision and base revision conflicts still reject.
- Existing topology/layout regression tests still pass.
- `py_compile` covers touched topology services.

### Review Gate

- No test depends on semantic success/failure stored in topology.
- No mount validator accepts arbitrary dispatch DSL by default.
- Backward compatibility is explicit and bounded.

## Phase 2: Document Anchor And Activation State

### Landing Scope

- Add first-class task artifacts or generated views for:
  - `task_packet.md`;
  - `execution_contract.md`;
  - `orchestration_notes.md`;
  - `round_summary.md`.
- Extend `ccb plan` task metadata with a small activation surface:

```text
status: draft | ready_for_orchestration | running | partial | replan_required | done | blocked
next_owner: planner | orchestrator | frontdesk | terminal
current_loop: <loop-id|none>
activation_reason: <short reason>
```

- `ccb loop runner --once` reads task status and `next_owner`; it does not
  infer workflow state from agent conversation memory.
- Default policy: `execution_contract.md` is mandatory before
  `ready_for_orchestration`. A synthesized low-risk contract is allowed only
  behind an explicit flag and must record provenance.
- `orchestration_notes.md` is imported as task evidence, not stored only as
  loop-local runtime state, so planner/frontdesk can review semantic routing
  without reading `.ccb/runtime`.

### Machine Contract

Phase 2 must define machine-checkable fields before runner behavior expands.

| Contract | Required Values |
| :--- | :--- |
| Anchor artifact kinds | `task_packet`, `execution_contract`, `orchestration_notes`, `round_summary`. |
| Task status enum | `draft`, `ready_for_orchestration`, `running`, `partial`, `replan_required`, `done`, `blocked`. |
| `next_owner` enum | `planner`, `orchestrator`, `frontdesk`, `terminal`. |
| Orchestrator route enum | `direct_execution`, `needs_detail`, `macro_adjustment_request`, `blocked`. |
| Round result enum | `pass`, `partial`, `replan_required`, `blocked`. |
| Round result mapping | `pass -> done`, `partial -> partial`, `replan_required -> replan_required`, `blocked -> blocked`. |
| Metadata fields | `task_id`, `status`, `next_owner`, `current_loop`, `activation_reason`, `artifact_kind`, `artifact_path`, `sha256`, `actor`, `job_id`, `imported_at`. |

Phase 2 must not introduce Markdown guessing. If a field affects state,
scripts must read it from command arguments, metadata, or a structured sidecar
that is imported through `ccb plan`.

### Test Gate

- `ccb plan` unit tests:
  - cannot mark ready for orchestration without required task packet fields;
  - cannot run without execution contract unless the test explicitly uses a
    low-risk synthesized contract path;
  - imports `orchestration_notes` without changing authority state;
  - imports `round_summary` and maps `pass`, `partial`, `replan_required`,
    and `blocked` to task state through scripts.
  - rejects unknown `next_owner`, route, and round result values.
  - duplicate `round_summary` import is idempotent for the same digest and
    rejected or versioned for conflicting content.
- Source-wrapper fake smoke creates a task in `/home/bfly/yunwei/test_ccb2`
  using `/home/bfly/yunwei/ccb_source/ccb_test`.

### Review Gate

- Planner remains macro-only: no detailed implementation body maintenance.
- Orchestration notes are non-authority and cannot mark work done.
- Round summary is compact enough for planner rehydration.
- `task_detailer` may be installed and optionally visible by project topology,
  but collection membership or installation never makes it part of the
  planning chain; orchestrator route decides activation.

## Phase 3: Orchestrator Triage Without Detailer By Default

### Landing Scope

- Runner activates `ccb_orchestrator` for `ready_for_orchestration`.
- Orchestrator returns one of:
  - `direct_execution`;
  - `needs_detail`;
  - `macro_adjustment_request`;
  - `blocked`.
- Direct execution path does not call `ccb_task_detailer`.
- `needs_detail` calls `ccb_task_detailer`, then returns to orchestrator.
- Macro adjustment goes back to planner through a compact artifact, not by
  editing roadmap or decisions directly.

### Test Gate

- Fake-provider route tests:
  - direct route mounts worker/reviewer and skips detailer;
  - needs-detail route asks detailer, imports detail packet, then continues;
  - macro-adjustment route does not mount workers;
  - blocked route stops with blocker evidence.
- All route tests verify that task status changes only through `ccb plan`
  commands.

### Review Gate

- Detailer is optional and on-demand, not a fixed planning-chain member.
- Orchestrator can request mount topology but cannot mutate runtime files
  directly.
- Planner only receives macro summaries and adjustment reasons.

## Phase 4: Ask-First Execution Round

### Landing Scope

- Orchestrator proposes mount topology for one or more execution pairs.
- CCB applies topology and proves targets are askable.
- Orchestrator sends task asks normally.
- Worker and `code_reviewer` may communicate directly through `ask`.
- Orchestrator imports the stable result into `round_summary.md`.

### Test Gate

Source-wrapper smoke from `/home/bfly/yunwei/test_ccb2`:

1. Isolated `HOME` and `CCB_SOURCE_HOME`.
2. Start with resident baseline:
   - `ccb_frontdesk + ccb_task_detailer` in `ccb-user`;
   - `ccb_planner + ccb_orchestrator` in `ccb-plan`.
3. Apply one execution pair in `ccb-exec`.
4. Prove `ask` reachability for orchestrator, worker, and reviewer.
5. Prove worker/reviewer direct ask succeeds without topology dispatch edges.
6. Import round summary.
7. Release dynamic execution agents.
8. Confirm resident panes remain mounted and askable.

Expected indicators:

- `mount_topology_status=ready`;
- `ask_reachability=ok`;
- `round_summary_imported=true`;
- `released_count` matches ephemeral execution agents;
- `retained_busy=0` in idle cleanup tests;
- final dynamic execution count is zero.

### Review Gate

- No hidden fallback, scope shrinkage, or fake success is accepted.
- Review evidence cites the original `execution_contract`.
- Worker/reviewer asks can be audited through CCB artifacts or message records,
  but the durable truth is `round_summary.md`.

## Phase 5: Release, Retain, Park, And Reflow Hardening

### Landing Scope

- Dynamic execution agents release after evidence import and idle proof.
- Busy agents become `retained_busy`, not killed.
- Long-lived roles default to hide/park, not unload.
- Reflow preserves surviving pane identity.
- Empty overflow windows are removed only after ownership proof.

### Test Gate

- Continuous add/remove:
  - `1 -> 6 -> 1` single-page grow/shrink;
  - `1 -> 8 -> 1` overflow page creation/removal;
  - middle execution pair release preserves survivor pane ids.
- Busy-retain:
  - active ask blocks unload;
  - later idle reconcile releases the retained agent.
- Park/resume:
  - planner/orchestrator park disables dispatch when appropriate;
  - resume preserves pane id and restores ask reachability.

### Review Gate

- No forced kill of busy provider sessions.
- No context-losing rebuild for surviving panes.
- Static or resident configured agents are not removed by loop cleanup.

## Phase 6: Single-Round Task Matrix Candidate

### Landing Scope

- One bounded single-round workflow per supported task route:

```text
frontdesk input
  -> planner task_packet + execution_contract
  -> orchestrator triage
      -> direct_execution
      -> needs_detail -> ccb_task_detailer -> execution
      -> macro_adjustment_request -> planner
      -> blocked
      -> partial_completion
  -> mount topology apply when execution is required
  -> worker/reviewer ask-first single round
  -> round summary import
  -> dynamic release or safe retain
```

- Phase 6 success is defined as single-round correctness across task types, not
  as proof of multi-round convergence or long-running workflow supervision.
- Detailed acceptance matrix lives in
  [phase6-single-round-task-matrix-goal.md](phase6-single-round-task-matrix-goal.md).

### Test Gate

- Focused pytest suite passes for plan tasks, topology, lifecycle, runner,
  fake provider, and workflow smoke.
- Source-wrapper fake-provider smokes pass with
  `/home/bfly/yunwei/ccb_source/ccb_test` from
  `/home/bfly/yunwei/test_ccb2`.
- The task matrix covers at least:
  - one `direct_execution` round that passes;
  - one `needs_detail` round that imports detail packet then passes;
  - one `macro_adjustment_request` task that returns to planner without
    mounting execution agents;
  - one `blocked` task that stays blocked by explicit evidence;
  - one `partial_completion` task that ends `partial` with explicit unfinished
    step evidence.
- `git diff --check` is clean.
- No tests require real Codex/Claude auth.

### Review Gate

- Independent reviewer confirms:
  - Phase 6 is a single-round acceptance gate only;
  - topology is mount-only in mainline;
  - ask-first collaboration works without hidden dispatch DSL;
  - planner/frontdesk context remains thin;
  - task_detailer does not become a long-lived omnipotent role;
  - scripts own authority transitions;
  - release/retain behavior is safe.

## Worker Package Order

Recommended work packages:

1. `mount-topology-schema`: schema split, validation, compatibility tests.
2. `task-anchor-artifacts`: task packet, execution contract, orchestration
   notes, round summary import tests.
3. `orchestrator-triage-router`: direct/detail/macro/block route handling.
4. `ask-first-round-smoke`: fake-provider ask-first worker/reviewer round.
5. `release-retain-reflow-hardening`: busy retain, park/resume, overflow
   cleanup.
6. `production-candidate-gate`: consolidated test command and source-wrapper
   smoke.

Each package should land with:

- focused unit tests;
- one source-wrapper smoke when runtime behavior changes;
- a short plan-tree status update;
- reviewer notes for boundary regressions.

## Failure Policy

- Schema ambiguity blocks implementation rather than adding fallback behavior.
- Repeated route failure returns `blocked` or `replan_required`; it must not
  silently downgrade the task.
- Busy release failure records `retained_busy` and retries later.
- Any agent-produced authority change must be rejected unless imported through
  a script command.
- Any test that only passes because fake provider skips the real authority path
  is not sufficient for the production candidate.
