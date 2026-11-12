# Complete Workflow Design

Date: 2026-06-26

## Purpose

Define the full CCB-native agentic workflow loop: how user intent becomes a
planner task packet, how execution rounds run, how round evidence returns to
durable state, when planner is reactivated, and when the loop stops.

This document is the compact end-to-end reference. Detailed role and artifact
contracts remain in the linked topic files.

## Design Premise

The workflow should fuse program stability with agent flexibility.

Scripts and helpers are the stable kernel. They should stay small,
deterministic, idempotent, and recoverable. Their job is to enforce identity,
state transitions, locks, leases, indexes, path safety, artifact manifests,
required evidence, and stop conditions.

Agents are the semantic layer. Their job is to understand ambiguous intent,
write complex human-readable artifacts, plan, review, diagnose, explain
non-convergence, and recommend the next semantic outcome.

The boundary is:

```text
agents author semantic artifacts
scripts validate, index, commit, or reject them
loop_runner advances only from committed state
```

This avoids turning scripts into brittle Markdown-understanding systems while
also preventing agents from directly mutating hard authority.

## Core Model

There are two nested loops:

```text
workflow loop
  frontdesk intake
  planning
  planning review
  clarification
  ready
  execution round
  round checking
  evidence writeback
  stop or next planning cycle

execution round
  orchestrator
  topology commit/reconcile
  worker/checker node(s)
  round checker
  topology release/reconcile
```

Planner is inside the workflow loop. Planner is outside the execution round.

That distinction keeps planning automatic and state-driven without letting
planner inherit fast-changing worker, provider, and retry noise during
execution.

## Authority Rule

Agents do semantic work and produce artifacts. Scripts own hard authority.

```text
frontdesk / planner / checker / round_checker
  produce: requests, questions, reports, plans, evidence

ccb plan / ccb loop / ccb question scripts
  validate and write: status, phase, owner, index, current_loop, task packet imports

loop_runner
  reads: task and loop state
  decides: which role or script to activate next
```

No agent directly edits authoritative status, `tasks/index.json`, loop phase,
owner, current loop binding, or progress files.

## Durable State

Durable task packets live under plan-tree:

```text
docs/plantree/plans/<plan-slug>/tasks/<task-id>/
  README.md
  requirements.md
  acceptance-criteria.md
  verification-contract.md
  handoff.md
  review.md
  completion.md
  tasks/index.json
```

Runtime loop state lives under `.ccb/runtime/loops/<loop-id>/`:

```text
round.json
asks.jsonl
events.jsonl
breadcrumb.md
agent_topology.desired.json
agent_topology.observed.json
agent_topology.events.jsonl
topology_proposals/
artifacts/
nodes/
branches/
verification/
```

The durable packet carries stable task truth. Runtime loop state carries
high-frequency execution evidence.

## Workflow Phases

| Phase | Owner | Meaning |
| :--- | :--- | :--- |
| `intake` | `frontdesk` | User-facing macro task capture. |
| `planning` | planner group | Build or revise task packet artifacts. |
| `planning_review` | planner group | Check ambiguity, risks, and verification contract. |
| `clarification` | broker/frontdesk | Ask only stage-blocking user questions. |
| `ready` | loop runner | Task packet is execution-ready. |
| `orchestration` | orchestrator | Split task into bounded work items. |
| `topology_reconcile` | CCB scripts / reconciler | Commit desired runtime workflow graph and converge required agents, placement, and lifecycle. |
| `execution` | execution nodes | Worker/checker nodes perform and verify bounded work. |
| `round_checking` | round checker | Verify integrated round result. |
| `writeback` | scripts / planner stewardship mode | Import durable evidence and update task status. |
| `done` | terminal | Task is complete. |
| `blocked` | terminal or paused | External condition or decision blocks progress. |
| `needs_clarification` | paused | User answer required before continuing. |
| `partial` | planner reactivation | Completed branches preserved; remaining work replanned. |
| `replan_required` | planner reactivation | Requirements, split, acceptance, or risk model must change. |

`partial` and `replan_required` are not success states. They are durable
handoff states that reactivate planner unless limits or user decisions stop the
loop.

## Planner Activation Rules

Planner should be activated by loop runner when task or loop state says
planning is needed.

| Trigger | Activate Planner? | Reason |
| :--- | :--- | :--- |
| New macro task accepted by `frontdesk` | yes | Need requirements, acceptance, verification, handoff. |
| Task status is `draft` | yes | Task packet is incomplete. |
| Task status is `needs_clarification` and answers are normalized | yes | Planner must absorb answers. |
| Broker defaulted or deferred current-stage questions | yes | Planner must record assumptions and continue. |
| Round result is `partial` | yes | Preserve completed work and replan remaining branch. |
| Round result is `replan_required` | yes | Current plan or task split is invalid. |
| Blocker is resolved | yes | Re-evaluate readiness or next task. |
| User changes goal, scope, or risk tolerance | yes | Planning basis changed. |
| Checker result is `rework_node` | no | Stay inside execution round through orchestrator/worker. |
| Round checker result is `pass` | no | Scripts import completion and mark done. |
| Provider, ask, tmux, or pane failure | no by default | Monitor/recovery handles runtime failure first. |
| Pure status/index write is needed | no | Script-owned state update. |

Planner should rehydrate from files, not retained conversation memory. Its
minimum input set is:

- original task packet;
- imported completion, partial, blocker, or replan report;
- round checker report;
- orchestrator summary and dependency notes;
- referenced node/checker reports;
- normalized user answers when broker/frontdesk was involved.

## Round Completion And Writeback

Round completion is not direct planner activation.

```text
execution round ends
  -> round_checker writes semantic report
  -> ccb loop records round result
  -> ccb plan imports durable evidence
  -> loop_runner reads updated state
  -> loop_runner stops, pauses, or activates next role
```

Round checker decides semantic result. Scripts write the result. Loop runner
decides next activation.

### Writeback Consistency

The writeback chain is a consistency boundary. Loop runner must not activate
planner or start a new execution round from a half-written round result.

V1 should treat round writeback as one idempotent command sequence:

```text
bind task to loop
  -> run execution round
  -> import round result and report
  -> validate task status, current_loop, evidence refs, and counters
  -> clear current_loop or enter recovery/blocker state
```

If any step after round checker output fails, loop runner should record a
script/state validation failure and stop automatic progress for that task. It
should not infer success from the presence of a report file alone.

The first implementation does not need a full two-phase commit, but it does
need per-task locking, an idempotent `current_loop` binding, result import
validation, and a recovery/escalation state for repeated script failures.

## Result Routing

| Round Result | Script Writeback | Next Activation |
| :--- | :--- | :--- |
| `pass` | import completion, mark `done` | stop and notify `frontdesk` |
| `rework_node` | record node issue in runtime state | orchestrator/worker within limits |
| `partial` | import partial report, mark `partial` | planner unless limit/user decision stops |
| `replan_required` | import replan report, mark `replan_required` | planner unless limit/user decision stops |
| `global_blocker` | import blocker report, mark `blocked` or `needs_clarification` | frontdesk/broker/recovery |

`pass` is the only normal successful stop. `partial` preserves value but still
requires planning. `blocked` stops automatic progress until the blocker is
resolved or the user changes scope.

### Result Decision Rules

Use `rework_node` only when a bounded node can fix the problem under the
current task split, current acceptance criteria, current risk model, and
remaining rework budget.

Use `partial` when independent sibling work is proven useful and can be
preserved, but one or more branches need planner rehydration before they can
continue.

Use `replan_required` when the current plan, task split, acceptance criteria,
verification contract, or risk model is wrong or incomplete. If orchestrator
finds that a node cannot be repaired without changing the split or global
dependencies, it should escalate to `replan_required` instead of issuing
another `rework_node`.

Use `needs_clarification` only when a user answer is required before planner
can safely continue. If planner can make a bounded assumption, broker may
record that assumption and keep the task in planning rather than escalating to
the user.

Use `blocked` for external or unrecoverable conditions. Provider, ask, tmux,
or pane failures should first go through deterministic recovery; they become
`blocked` only when recovery limits are reached or an external action is
required.

## Stop Rules

The loop stops when loop runner sees a terminal or paused state.

Terminal states:

- `done`
- `cancelled`
- unrecoverable `blocked`

Paused states:

- `needs_clarification`
- `manual_pause`
- `blocked` awaiting user/environment action

Limit stops:

- maximum workflow iterations reached;
- maximum replan cycles reached;
- maximum node rework rounds reached;
- maximum same failure signature reached;
- maximum planner iterations without new artifact or decision evidence reached;
- maximum user scope changes per active loop reached;
- maximum recovery rounds reached;
- maximum wall-clock runtime reached;
- maximum dynamic node count reached;
- repeated script/state validation failure.

When a limit is reached, loop runner writes a blocked or escalation state
through scripts and sends a compact evidence package to `frontdesk`.

## Stop Decision Ownership

| Decision | Owner |
| :--- | :--- |
| Did this round satisfy the verification contract? | round checker |
| Can this branch be fixed without replanning? | checker / orchestrator / round checker |
| Does the remaining work require a new plan? | planner after rehydration |
| Is user input required? | planner or broker, surfaced through frontdesk |
| Has the workflow reached a terminal or paused state? | loop runner |
| Who writes terminal status? | `ccb plan` / `ccb loop` scripts |

The document stores the decision result. It does not decide on its own. Agents
recommend; loop runner evaluates state and limits; scripts write authority.

## Loop Runner Algorithm

V1 target behavior:

```text
while true:
  state = read_task_and_loop_state()

  if state is done/cancelled/manual_pause:
    stop

  if state is blocked and not recoverable:
    notify_frontdesk
    stop

  if state is needs_clarification:
    publish_questions_or_wait_for_answers
    stop_current_auto_loop

  if limits_exceeded(state):
    write_blocked_or_escalation()
    notify_frontdesk
    stop

  if state is draft/partial/replan_required/clarification_answered:
    activate_planner()
    continue

  if state is ready:
    bind_current_loop()
    ask_orchestrator_for_topology()
    commit_and_reconcile_topology()
    start_execution_round()
    continue

  if state is running:
    monitor_or_continue_round()
    continue

  if round_result is pass:
    reconcile_release_gates()
    import_completion_and_mark_done()
    notify_frontdesk
    stop

  if round_result is rework_node:
    activate_orchestrator_or_worker_within_limits()
    continue

  if round_result is partial/replan_required:
    import_round_evidence_and_mark_status()
    reconcile_release_or_park()
    continue
```

The loop runner is the automatic activator. It is a script/helper, not a
conversation agent.

## Role Set

Minimal V1 role set:

| Role | Required In V1 | Notes |
| :--- | :--- | :--- |
| `frontdesk` | yes | User-facing macro intake and final/escalation reports. |
| `planner` | yes | Activated in planning phases and after partial/replan. |
| `plan_reviewer` | optional/internal | Can start as planner stage; separate role later. |
| `clarification_broker` | later | Needed for staged user questions. |
| `orchestrator` | yes | Splits ready task into bounded execution work. |
| `worker` | yes | Performs bounded work. |
| `checker` / `code_reviewer` | yes | Node-level quality gate. |
| `round_checker` | yes | Whole-round verifier, separate from planner. |
| planner stewardship mode / `ccb plan` | script-first | Deterministic `ccb plan` commands are V1 authority; planner may audit/summarize without bypassing scripts. |
| `inner_monitor` | partial/later | Deterministic health checks first; semantic monitor later. |

## V1 Command Surface

Already landed or partially landed:

```bash
ccb plan task-create
ccb plan task-artifact
ccb plan task-status
ccb plan task-show
ccb plan task-list
ccb plan breadcrumb

ccb loop capacity ensure/status/release
ccb loop run-once --round-checker <agent>
```

Needed next:

```bash
ccb plan task-bind-loop --task <task-id> --loop <loop-id>
ccb plan task-import-round --task <task-id> --loop <loop-id> \
  --result <pass|partial|replan_required|blocked> --report <path>
ccb loop run-once --task-id <task-id>
ccb loop runner --once
ccb loop topology propose/validate/commit/reconcile/status/release
```

The immediate gap is removing the manual bridge between a ready task packet and
`ccb loop run-once`. The first runner should be a one-shot CLI, not a daemon.
Planner activation, clarification commands, and long-running runner ownership
remain later slices.

## Implementation Status

Current proven slice:

- `ccb plan` creates durable task packets and enforces readiness artifacts.
- `ccb loop run-once` runs worker, reviewer, orchestrator, and round checker.
- Topology-driven execution is the next design target: orchestrator should
  propose a runtime workflow graph, scripts should commit desired topology,
  and the reconciler should load/release execution agents by diffing desired
  and observed state.
- External fake-provider smoke reached:

```text
task draft -> ready -> running -> done
round worker -> reviewer -> orchestrator -> round_checker
dynamic worker/reviewer release
round checker evidence imported as completion
```

Smoke project:

```text
/home/bfly/yunwei/test_ccb2/agentic-loop-full-smoke-v1
```

Remaining implementation gap:

- loop runner should automatically read task status and activate planner or
  execution round;
- runtime workflow graph commands and reconciler should replace direct
  orchestrator capacity ensure/release in the normal execution path;
- task packet should track `current_loop`;
- round results need first-class artifact kinds beyond generic `completion`;
- task/loop binding needs per-task lock or lease protection before automatic
  runner activation;
- loop limits need durable counters and failure signatures;
- clarification broker command surface is not implemented.

## Design Consequences

- Planner is not an outside manual pre-step. It is an automatic workflow phase.
- Planner exits during execution rounds to protect context purity.
- Round ending does not directly wake planner; scripts first write durable
  state, then loop runner decides.
- Stopping is deterministic: terminal status, paused state, or limit rule.
- Agents remain replaceable because all durable truth is in task and loop
  files, not in agent memory.
