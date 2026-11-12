# Mount Topology And Ask-First Orchestration

Date: 2026-07-03

## Purpose

Define the simplified landing direction for CCB's agentic workflow:

```text
few authority documents
  + mount-only topology
  + normal ask collaboration
  + script-owned state transitions
```

The goal is to avoid turning topology into a full communication DSL. Topology
should answer "what agents are mounted where, with what lifecycle policy?"
Normal `ask` should answer "who talks to whom to complete this semantic work?"

Decision 022 further separates semantic publication intent from its physical
side effect. Orchestrator may define logical role assignments and complete ask
packets in one orchestration bundle, but controller code binds concrete mounted
agents and submits those asks exactly once. This refinement does not put
communication edges back into mount topology.

Decision 024 fixes future multi-lane topology ownership: each lane keeps
separate desired/observed topology and immaculate orchestrator activations,
while one project-level deterministic Topology Controller arbitrates shared
capacity, identities, windows, panes, workspaces, reconcile, and release. This
is design-only until the single-lane production gate is closed.

## Layer Model

| Layer | What It Owns | What It Must Not Own |
| :--- | :--- | :--- |
| Plan/task documents | Durable goal, scope, acceptance, constraints, final evidence. | High-frequency chat logs, every intermediate thought, tmux state. |
| Mount topology | Agent/window/pane/provider/lifecycle desired and observed state. | Worker/reviewer conversation flow, detailed semantic decision making. |
| Ask collaboration | Agent-to-agent task execution, review, detail clarification, and result exchange. | Authoritative task status, topology mutation, release decisions. |
| CCB scripts | Status transitions, artifact import, topology apply/release, locks, validation. | Product reasoning, implementation strategy, semantic tradeoff resolution. |

## Document Layout

Durable plan/task documents live under plan-tree:

```text
docs/plantree/plans/<plan-slug>/tasks/<task-id>/
  README.md
  task_packet.md
  execution_contract.md
  orchestration_notes.md
  orchestration_bundle.json
  round_summary.md
  artifacts/
    detail_packet.manifest.json
    detail_summary.md
    macro_adjustment_request.md
    node-<n>-worker-result.md
    node-<n>-review.md
    round-review.md
```

Runtime mount state stays under `.ccb/runtime`:

```text
.ccb/runtime/loops/<loop-id>/
  agent_mount_topology.desired.json
  agent_mount_topology.observed.json
  agent_mount_topology.events.jsonl
  agent_mount_topology.lock
  topology_proposals/
    <proposal-id>.json
```

V1 may keep the current `agent_topology.*` filenames while implementation is
being split. New design and tests should treat these files as mount topology,
not as the preferred communication graph.

## Authority Documents

### `task_packet.md`

Planner-facing durable macro task.

Required content:

- task id, plan slug, status, current loop binding;
- goal, scope, non-goals, assumptions;
- acceptance criteria;
- verification contract;
- risk notes and known blockers;
- source links and related plan-tree links;
- next owner hint: `orchestrator`, `planner`, `frontdesk`, or terminal.

Activation:

- `draft` or `replan_required` activates planner;
- `ready_for_orchestration` activates orchestrator;
- `blocked` or unresolved user scope activates frontdesk through a curated
  question artifact;
- `done` stops the loop.

### `execution_contract.md`

Round-level hard constraints that every task ask should reference.

Required content:

- no hidden fallback or silent scope reduction;
- what counts as acceptable test evidence;
- what must be escalated instead of patched over;
- maximum node count and rework budget;
- artifact paths that final work must update or cite;
- release policy for ephemeral agents after evidence import.

Activation:

- Orchestrator reads it before deciding direct execution versus detail pass.
- Worker/reviewer asks must include a link or compact quote from it.
- Round summary must state whether it was satisfied.

### `orchestration_notes.md`

Orchestrator-owned lightweight execution plan.

Allowed content:

- selected route: `direct_execution`, `needs_detail`,
  `macro_adjustment_request`, or `blocked`;
- needed agents and work units;
- intended ask order and reviewer expectations;
- links to task packet, execution contract, detail packet, and topology
  proposal;
- assumptions that are local to this round.

Non-authority:

- It does not change task status.
- It does not mount agents by itself.
- It is not a required DAG scheduler input.
- It must not replace `round_summary.md`.

### `orchestration_bundle.json`

Decision 022 target artifact for complex semantic execution. One immaculate
orchestrator activation owns its work slicing, dependencies, logical role
assignments, task packet refs, review/integration policy, and capacity intent.

The current source does not yet treat this artifact as runtime authority. A
future controller may execute it only after schema, revision, capacity, and
task-envelope validation. It must not reinterpret the bundle or copy its graph
into mount topology communication edges.

### `agent_mount_topology.*`

CCB-owned runtime desired and observed state.

Minimum desired schema intent:

```json
{
  "schema": "ccb.loop.agent_mount_topology.v1",
  "loop_id": "loop-123",
  "revision": 4,
  "agents": [
    {
      "id": "wf-coder-1",
      "profile": "coder",
      "role": "agentroles.coder",
      "desired_state": "present",
      "window_name": "ccb-exec",
      "pane_order": 1,
      "lifecycle": "ephemeral",
      "release_policy": "auto"
    }
  ],
  "windows": [
    {
      "name": "ccb-exec",
      "class": "execution",
      "max_panes": 6,
      "layout_policy": "fixed-balanced"
    }
  ]
}
```

Allowed authority:

- agent ids and profiles;
- role ids and provider/profile snapshot;
- window names/classes and pane order;
- lifecycle class: resident, semi-resident, ephemeral;
- desired state: present, hidden, parked, absent;
- release policy: retain, hide, park, auto, unload;
- observed readiness, drift, busy retain, and release evidence.

Forbidden authority:

- normal worker/reviewer communication edges;
- arbitrary call-order DSL;
- user-facing requirements;
- acceptance criteria;
- semantic success/failure.

### `round_summary.md`

Round-level stable evidence.

Required content:

- result: `pass`, `partial`, `replan_required`, or `blocked`;
- completed work units and skipped work units;
- verification evidence and failing evidence;
- worker/reviewer findings that matter after context is cleared;
- unresolved blockers and owner;
- whether dynamic agents can be released or must be retained busy;
- compact planner import summary.

Activation:

- `pass` can move the task to `done` after script validation.
- `partial` can preserve sibling evidence and activate planner for next
  slicing.
- `replan_required` activates planner with a macro adjustment reason.
- `blocked` activates frontdesk or planner depending on blocker type.

## Dynamic Activation

V1 should use explicit runner calls, not a watcher:

```text
ccb loop runner --once
  reads task_packet status
  if ready_for_orchestration:
    validates the single-unit template or asks ccb_orchestrator once
    imports orchestration_notes and orchestration_bundle when required
    commits/applies mount topology when needed
    binds logical roles and submits newly dispatchable asks exactly once
    resumes from callbacks and imports reviewed evidence
    imports round_summary
    releases eligible ephemeral agents
  else:
    activates the owner implied by task status
```

Later ccbd support can watch committed status revisions with debounce, but the
same state machine should remain visible and testable through commands.

## Ask Collaboration Rules

Default logical flows:

- orchestrator -> worker;
- worker -> code_reviewer;
- code_reviewer -> worker for bounded rework;
- orchestrator -> ccb_task_detailer when triage returns `needs_detail`;
- ccb_task_detailer -> orchestrator with detail packet links;
- round reviewer -> orchestrator for missing evidence clarification.

These arrows describe semantic provenance, not permission for providers to run
arbitrary ask commands. In the Decision 022 target path, controller code
submits each physical ask from validated bundle state, records the job id, and
resumes from delivery evidence. Provider replies cannot create new workflow
authority or silently publish additional work.

Required discipline:

- Ask messages should include links to `task_packet.md` and
  `execution_contract.md`.
- Ask replies may contain reasoning, but authority changes require script
  import.
- If reviewer and worker converge, orchestrator still imports a compact
  `round_summary.md`.
- If they do not converge within budget, the unit reports `partial`,
  `replan_required`, or `blocked`; it must not silently degrade.

Controller-owned programmatic ask is the preferred physical dispatch mechanism
for recoverable bundle execution. Direct provider-side ask remains useful for
interactive collaboration and compatibility paths, but it cannot replace
submission intent, job-id persistence, callback recovery, or script-owned
artifact import.

## Landing Plan

The executable phase plan is tracked in
[../goals/mount-topology-ask-first-landing-goal.md](../goals/mount-topology-ask-first-landing-goal.md).
This section keeps the design-level sequence only. The goal file owns
execution phase numbers, gates, tests, and review indicators.

### Design Step A: Plan-tree contract

- Add Decision 020 and this topic as the preferred direction.
- Mark the old runtime workflow graph as landed substrate plus superseded broad
  communication scope.
- Define the exact artifact names and activation states used by the first
  source-wrapper smoke.

### Design Step B: Mount topology schema split

- Keep existing `ccb loop topology` commands.
- Add validation mode that treats topology as mount-only.
- Introduce `agent_mount_topology.*` aliases or schema name while preserving
  backward-compatible read of `agent_topology.*`.
- Reject new communication-only edges in mount topology unless an explicit
  legacy dispatch flag is used.

### Design Step C: Ask-first source smoke

Run from `/home/bfly/yunwei/test_ccb2` with source `ccb_test` and fake
providers:

1. Create a task packet and execution contract.
2. Ask `ccb_orchestrator` to triage.
3. Commit/apply a mount topology with resident `ccb_frontdesk`,
   `ccb_task_detailer`, `ccb_planner`, `ccb_orchestrator`, and one
   `coder + code_reviewer` pair.
4. Prove `ask` reachability to orchestrator, worker, and reviewer.
5. Let worker/reviewer coordinate through normal ask.
6. Import `round_summary.md`.
7. Release dynamic execution agents while preserving resident panes.

### Design Step D: Real-provider opt-in gate

- Repeat the ask-first smoke with one real Codex or Claude worker pair when
  credentials are available.
- Verify Chinese input/rich terminal behavior is unaffected by loop runtime.
- Verify busy retain prevents release while a provider job is active.

## Test Matrix

| Test | Purpose |
| :--- | :--- |
| mount schema rejects communication edges | Proves topology is not a hidden workflow DSL. |
| mount schema accepts windows/panes/provider/lifecycle | Proves topology still replaces ad hoc tmux mutation. |
| ready task activates orchestrator | Proves document status drives the next step. |
| orchestrator direct execution route | Proves detailer is optional. |
| orchestrator needs-detail route | Proves detailer can refine and return to orchestrator without becoming planner. |
| worker/reviewer direct ask | Proves normal collaboration does not require topology edges. |
| round summary import | Proves ask replies become authority only through artifacts. |
| release dynamic agents | Proves ephemeral cleanup and reflow after evidence import. |
| retain busy dynamic agent | Proves no forced unload during active provider work. |
| resident agent park/hide policy | Proves frontdesk/planner/orchestrator are not casually killed. |

## Open Design Points

- Whether `task_packet.md` should be generated from current `README.md` plus
  artifacts, or added as an explicit compact artifact beside it.
- Resolved V1 default: `execution_contract.md` is mandatory before
  `ready_for_orchestration`. A low-risk synthesized contract is allowed only
  behind an explicit flag and must write provenance.
- Resolved V1 preference: `orchestration_notes.md` should be imported through
  `ccb plan task-artifact` as task evidence, not stored only as loop-local
  runtime evidence, so semantic route choices remain reviewable from
  plan-tree.
- How long old `agent_topology.*` dispatch support remains available after the
  mount-topology split.
