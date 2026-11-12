# 020 Mount Topology And Ask-First Orchestration

Date: 2026-07-03
Status: Accepted for planning

## Context

The first topology slice proved dynamic agent mounting, release, parking,
moving, and reflow. It also proved a minimal topology-dispatch path that can
execute `ask` / `ask_after` edges from a committed graph.

That broader graph direction is now too heavy for the workflow shape we want.
Most collaboration should stay inside CCB's existing `ask` primitive, because
worker/reviewer, detailer/orchestrator, and reviewer/orchestrator handoffs are
semantic conversations, not runtime layout facts.

The workflow still needs durable anchors, but only for hard authority:
task intent, execution constraints, mounted-agent topology, and final imported
results.

## Decision

CCB topology is narrowed to **mount topology**.

Topology authority owns:

- which agents should be mounted, parked, hidden, released, or retained;
- which window/page each mounted agent belongs to;
- pane ordering and reflow policy;
- provider/profile snapshot and dynamic ownership metadata;
- resident versus ephemeral lifecycle policy;
- observed drift, busy retention, and release evidence.

Topology authority does not own normal communication flow.

The default orchestration model is **ask-first**:

- `ccb_orchestrator` reads a task packet and execution contract;
- it decides whether the task needs direct execution, task-detailer refinement,
  or planner macro adjustment;
- it proposes or patches the mount topology needed for that round;
- after CCB applies topology, controller code binds accepted logical roles and
  submits normal `ask` jobs exactly once from the accepted orchestration
  intent;
- worker and `code_reviewer` replies remain semantic evidence, while follow-up
  asks and bounded rework are controller-owned physical side effects;
- important outcomes become authority only after they are imported into
  task/round artifacts through scripts.

## Required Document Anchors

The first production-oriented loop should use a small document set:

| Anchor | Owner | Authority |
| :--- | :--- | :--- |
| `task_packet` | planner plus `ccb plan` scripts | Goal, scope, non-goals, acceptance, verification, blockers, macro refs. |
| `execution_contract` | planner/orchestrator plus scripts | Hard constraints for this round: no hidden fallback, required tests, artifact refs, stop/escalation rules. |
| `agent_mount_topology` | CCB topology commands | Desired and observed agent/window/pane/lifecycle state. |
| `orchestration_notes` | orchestrator | Lightweight human-readable ask plan and work split. Not runtime authority. |
| `round_summary` | orchestrator/round reviewer plus scripts | Stable completion, partial, blocker, or replan evidence imported back into the task packet. |

Free-form ask replies are not durable workflow truth by themselves. If an ask
changes task state, scope, acceptance, verification, or completion status, the
result must be summarized into one of the document anchors and accepted by the
appropriate script-owned transition.

## Dynamic Activation Model

Document state activates the next process. The runner should not infer hidden
state from agent conversation memory.

```text
task_packet:draft
  -> planner/script imports required macro artifacts
  -> task_packet:ready_for_orchestration
  -> orchestrator triage
      -> direct_execution
      -> needs_detail -> task_detailer -> orchestrator
      -> macro_adjustment_request -> planner
      -> blocked
  -> agent_mount_topology:committed
  -> topology reconciler applies agents/windows/panes
  -> ask collaboration runs under execution_contract
  -> round_summary imported
  -> planner imports stable macro summary or stops on done/blocked
```

The program kernel should own status transitions, topology apply/release, and
artifact import. Agents own semantic proposals, detailed reasoning, and
human-readable summaries.

## Consequences

- Decision 014 remains valid as landed evidence for the topology controller,
  but its broad graph-dispatch scope is narrowed by this decision.
- Future implementation should rename or split runtime files toward
  `agent_mount_topology.*` and treat graph edges as legacy/experimental runner
  input, not the preferred orchestration contract.
- `orchestration_notes` may mention intended asks and review order, but CCB
  should not require a full dispatch DAG for ordinary worker/reviewer loops.
- `ask` remains the normal collaboration primitive. Decision 022 makes
  programmatic controller submission the preferred physical publication path
  for recoverable workflow execution; provider-side direct ask commands remain
  interactive or compatibility behavior, not the authority path.
- Tests must prove both sides: topology can change panes without losing
  running agents, and ask-first collaboration can complete a task with only
  the small document anchors.

## Non-Goals

- Do not turn mount topology into a general workflow DSL.
- Do not encode every worker/reviewer conversation as a required edge.
- Do not make planner or frontdesk responsible for runtime topology mutation.
- Do not let agents write authority files directly when a CCB command surface
  exists.
- Do not add a file watcher in V1; activation should be explicit through
  runner commands or later debounced ccbd support.

## Related

- [014-runtime-workflow-graph-reconciler.md](014-runtime-workflow-graph-reconciler.md)
- [019-orchestrator-triage-before-task-detailer.md](019-orchestrator-triage-before-task-detailer.md)
- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [../topics/mount-topology-and-ask-first-orchestration.md](../topics/mount-topology-and-ask-first-orchestration.md)
- [../topics/runtime-workflow-graph-and-reconciler.md](../topics/runtime-workflow-graph-and-reconciler.md)

Decision 022 preserves ask-first collaboration but refines physical ask
submission as a controller-owned side effect. The orchestrator owns semantic
publication intent, not provider-side execution of runtime commands.
