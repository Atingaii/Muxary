# Planner Role Design

Date: 2026-06-25

## Purpose

The long-lived planner turns macro user intent into stable plan-tree
direction, macro task refs, and readiness recommendations. It owns
semantic understanding, requirement shaping, risk surfacing, and durable
plan-tree hygiene, but it does not own detailed implementation planning or
authoritative state writes.

Planner should be designed together with the plan-tree structure it maintains.
It is responsible for keeping roadmap, decisions, open questions, evidence
indexes, a compact plan brief, and macro task refs coherent. It is not
responsible for turning a macro task into a code-level or operation-level
execution plan; that work belongs to `task_detailer` in V1.

This keeps `frontdesk` light and keeps durable plan-tree state from becoming a
free-form model scratchpad.

Detailed implementation refinement is an orchestrator-demanded path. When
orchestrator triage returns `needs_detail`, it may activate `task_detailer`.
See
[task-detailer-role-design.md](task-detailer-role-design.md) and
[../decisions/015-task-detailer-owns-task-refinement-and-clarification.md](../decisions/015-task-detailer-owns-task-refinement-and-clarification.md).
Planner's primary plan-tree work surface is the plan brief. See
[planner-plan-tree-brief-and-detail-boundary.md](planner-plan-tree-brief-and-detail-boundary.md)
and
[../decisions/018-planner-uses-plan-brief.md](../decisions/018-planner-uses-plan-brief.md).
The orchestrator triage boundary is recorded in
[../decisions/019-orchestrator-triage-before-task-detailer.md](../decisions/019-orchestrator-triage-before-task-detailer.md).

## Role Boundary

### Planner Owns

- Understanding the macro task and identifying missing requirements.
- Maintaining durable plan-tree context: roadmap state, open questions,
  decisions, evidence indexes, implementation-status handoff, and macro task
  publication.
- Maintaining the plan brief: macro objective, current phase, active roadmap
  item, constraints, decision summary, open-question summary, detail links,
  task/detail-packet links, readiness summary, verification summary, next
  owner, and last stable evidence.
- Reading relevant plan-tree and durable prior evidence.
- Producing macro requirements, constraints, non-goals, high-level acceptance,
  plan refs, risk flags, and handoff to orchestrator triage.
- Selecting or confirming the roadmap item that is currently ready for
  execution triage.
- Reviewing `macro-adjustment-request` artifacts from `task_detailer` and
  deciding whether one bounded roadmap, decision, open-question, or macro task
  patch is needed.
- Emitting stage-batched candidate questions when macro planning user input is
  genuinely needed.
- Running internal review before marking a task ready.
- Returning `ready`, `needs_clarification`, `blocked`, or `not_ready` as a
  semantic recommendation.

### Planner Does Not Own

- Direct user conversation. User-facing questions go through broker and
  `frontdesk`.
- Maintaining detailed design bodies under `topics/*`; in V1,
  `task_detailer` owns task-scoped detail docs and returns stable summary
  backfill plus links.
- Detailed implementation packet maintenance. `task_detailer` owns source/code
  research, detail packet construction, and task-local clarification.
- Editing detailed task packets, detail evidence maps, worker handoffs, or
  task-local clarification summaries as if they were planner-owned state.
- Authoritative task status, task index, phase, owner, or loop state writes.
- Runtime agent load/unload, `ask` scheduling, worker selection, or loop
  capacity.
- Direct `task_detailer` activation. Orchestrator decides whether a macro task
  can proceed directly or needs detail refinement.
- Final code correctness approval. It defines what must be proven; checker and
  round checker evaluate actual work.
- Silent fallback from unclear requirements to reduced scope.

## Internal Shape

V1 starts with a single macro planner plus optional review modes:

```text
planner
  -> maintains plan brief, macro task refs, and stable plan-tree state
optional plan_reviewer
  -> checks macro/task detail ambiguity, acceptance criteria, risks, and verification contract
orchestrator triage
  -> direct_execution
  -> needs_detail -> task_detailer -> orchestrator
  -> macro_adjustment_request -> planner
```

`plan_steward` is a historical term for planner stewardship work mode or the
deterministic `ccb plan` authority surface. It is not a separate required
mainline Role. `task_detailer` is not a fixed downstream planning member; it is
activated only when orchestrator triage needs task-local detail refinement.

The accepted post-V1 parallel direction keeps one global planner by default
and adds a Roadmap Graph plus Workflow Lanes. One planner may create several
serial or parallel roadmap branches and remain idle while controller code
advances the safe ready frontier. Multiple planner instances are only a later
throughput optimization across disjoint plan roots or explicit lane scopes;
the same plan scope never has multiple active planner writers. See
[parallel-roadmap-lanes-and-planner-authority.md](parallel-roadmap-lanes-and-planner-authority.md)
and
[Decision 023](../decisions/023-roadmap-graph-and-workflow-lanes.md).

Optional later roles:

- `risk_reviewer`: only for destructive, release, migration, security,
  payment, credential, or broad-runtime changes.
- `domain_researcher`: only when planner lacks source-backed domain knowledge.
- `spec_checker`: only when the task changes public contracts or Role specs.

The group should remain small. If a task needs many specialists, planner should
produce a clearer brief and macro task packet, then let orchestrator handle
triage, optional detail expansion, and execution splitting. An independent
detail-design role is deferred until task-scoped detail work proves too broad
for `task_detailer`.

## Inputs

Planner receives a macro packet from `frontdesk`:

```text
macro_task
user_goal
constraints
known_non_goals
risk_tolerance
target_plan_root
source_refs
prior_decisions
```

Planner may load:

- the target plan root README, roadmap, open questions, and active topics;
- the plan brief;
- task detail links and stable summary backfill from `task_detailer`;
- relevant source files or tests only when needed for macro feasibility;
  detailed source/code research belongs to `task_detailer`;
- prior user answers from normalized clarification artifacts;
- accepted decisions and evidence indexes.

Planner should not load runtime loop logs or large task detail docs unless they
are referenced as durable evidence, blocker material,
`macro-adjustment-request` evidence, or stable summary import candidates.

## Outputs

Planner writes macro draft artifacts, then asks `ccb plan` scripts to import
them as authoritative task packet files. Orchestrator may later request a
detailed execution packet from `task_detailer` before dispatch.

Draft outputs:

```text
brief.md
requirements.md
acceptance-criteria.md
verification-contract.md
risk-notes.md
handoff.md
candidate-questions.jsonl
macro-adjustment-review.md
plan-update-request.json
planner-review.md
readiness.json
```

Task-detailer outputs are separate and short-lived until accepted:

```text
detail-brief.md
source-evidence-map.md
execution-spec.md
acceptance-detail.md
verification-detail.md
worker-handoff.md
detail-readiness.json
clarification-needed.md
clarification-summary.md
macro-adjustment-request.json
```

Task-detailer detail docs remain linked detail material until planner accepts a
stable summary back into the brief or task document:

```text
topics/<detail-design>.md
source-evidence-summary.md
brief-update-summary.json
macro-adjustment-request.json
```

## Plan Brief Work Surface

Planner should update the brief before expanding durable task state. The brief
is the single macro summary surface for the current planning phase. It should
stay short and link to detail design docs instead of absorbing them.

Planner may update:

- purpose and macro objective;
- current phase and active roadmap item;
- accepted constraints and non-goals;
- decision and open-question summaries with links;
- task detail links;
- current macro task and detail packet links;
- readiness and verification summaries;
- next owner or handoff;
- last stable evidence.

Planner must not use the brief as a scratchpad for local technical research,
detailed design alternatives, source evidence maps, task-local clarification,
or worker handoff detail. Those belong to `task_detailer` in V1.

## Macro Adjustment Requests

`task_detailer` may discover that the selected roadmap task cannot be safely
detailed without changing a macro assumption. In that case, detailer does not
edit roadmap, decisions, or task status. It emits a `macro-adjustment-request`
artifact for planner review.

Planner handling rules:

- read the request, cited evidence, affected macro task, and proposed single
  adjustment;
- decide whether the finding is blocking, non-blocking, obsolete, already
  covered, or needs user-facing macro clarification;
- if accepted, produce a narrow `plan-update-request.json` for `ccb plan` or
  the future plan adapter to commit;
- if rejected, record a short reason and return the detailer to the current
  macro scope;
- never treat a detailer's request as an accepted decision before script-owned
  commit.

Suggested request shape:

```json
{
  "schema": "agentroles.macro_adjustment_request.v1",
  "task_id": "task-001",
  "macro_task_ref": "docs/plantree/plans/example/tasks/task-001/README.md",
  "detail_packet_ref": ".ccb/runtime/loops/loop-001/tasks/task-001/detailer/detail-packet.manifest.json",
  "requested_change_type": "roadmap",
  "reason": "Source evidence contradicts a macro assumption.",
  "evidence_refs": ["src/example.py", "docs/plantree/plans/example/decisions/001.md"],
  "impact": "Worker handoff cannot be made safe until acceptance is narrowed.",
  "single_recommended_adjustment": "Add explicit non-goal for provider replacement.",
  "urgency": "blocking",
  "next_owner": "planner"
}
```

`readiness.json` should be compact:

```json
{
  "status": "ready",
  "confidence": "high",
  "blocking_questions": [],
  "deferred_questions": [],
  "required_artifacts": [
    "requirements",
    "acceptance",
    "verification",
    "handoff"
  ],
  "risk_flags": []
}
```

## Clarification Handling

Macro planning clarification should still be stage-batched:

1. produce candidate questions with why-this-blocks evidence;
2. send them to broker, not directly to `frontdesk`;
3. wait for normalized answers or broker-recorded defaults;
4. update the draft plan packet;
5. only then request ready transition.

Planner should not ask every possible question up front. It should ask only
questions that block the current planning stage or create unacceptable risk if
defaulted.

Task-local implementation-detail clarification is different. If
`task_detailer` needs user input while refining a specific task, it creates a
clarification-needed artifact, frontend or `frontdesk` notifies the user to
enter that `task_detailer`, and the user clarifies with the same role instance.
`task_detailer` then records a clarification summary and continues refinement.

## Readiness Rules

A task is execution-ready only when:

- desired behavior is concrete enough for a worker;
- non-goals and forbidden degradations are explicit;
- acceptance criteria are testable;
- verification contract states what must be proven;
- risk notes identify irreversible or user-sensitive choices;
- required user clarifications are answered, defaulted with evidence, or
  deferred with a reason;
- either the macro handoff is concise enough for orchestrator to split into
  bounded workgroups, or orchestrator can return `needs_detail` with a
  constrained refinement request for `task_detailer`.

If these are missing, planner must return `not_ready` or
`needs_clarification`; it must not shrink scope to make the task executable.

## Script Authority And Plan Stewardship Mode

Planner proposes content. `ccb plan` scripts write authority. Plan stewardship
is a planner work mode or deterministic script surface for low-noise plan-tree
sync, not a separate required mainline Role.

Recommended sequence:

```text
frontdesk macro packet
  -> planner macro artifacts
  -> ccb plan task-create / task-artifact
  -> orchestrator triage
      -> direct_execution
      -> task_detailer when detailed refinement is needed
  -> macro-adjustment-request back to planner when macro drift is found
  -> optional plan_reviewer report
  -> detail packet linked to task document
  -> ccb plan task-status --status ready/detail_ready
  -> loop runner may activate orchestrator
  -> orchestrator proposes execution workgroups
```

The stewardship surface can be implemented as:

- deterministic command services for actual writes;
- an optional planner mode that audits plan-tree consistency and prepares sync
  summaries, without bypassing scripts.

## Next-Loop Rehydration

Planner is responsible for creating the next task when a round returns
`partial` or `replan_required`, but it should not rely on retained conversation
memory from the prior planning turn.

For next-loop planning, planner should reload:

- the original task packet;
- imported completion, partial, blocker, or replan evidence;
- round checker report;
- orchestrator summary and dependency notes;
- node/checker reports referenced by the round report;
- normalized user answers when broker/frontdesk was involved.

Planner should then produce a revised task packet or clarification batch. It
must not treat round checker evidence as permission to lower acceptance
criteria. See
[round-checker-and-planner-rehydration.md](round-checker-and-planner-rehydration.md).

## Planner Stop Conditions

Planner is a workflow-loop participant, so it also needs bounded progress.
Loop runner should stop or escalate planner cycling when one of these limits is
reached:

- Maximum planner iterations for the same task without a new artifact, answer,
  decision, or evidence ref.
- Maximum `partial` or `replan_required` cycles for the same failure
  signature.
- Maximum user scope changes inside one active loop.
- Repeated readiness recommendations that fail script validation for the same
  reason.
- Repeated clarification batches that broker marks as non-blocking,
  duplicate, obsolete, or defaultable.

When a planner stop condition is hit, planner should produce a compact
escalation package with the task id, current artifacts, repeated failure
signature, unresolved decision, and recommended next owner. Scripts then mark a
paused or blocked state; planner must not silently reduce scope to satisfy the
limit.

## Context-Purity Budget

Planner context should include stable planning material and current stage
drafts. It should exclude:

- raw ask logs;
- node heartbeats;
- pane/provider runtime noise;
- every worker retry;
- unrelated historical tasks;
- release logs unless the current task is a release task.

If execution detail becomes durable evidence, planner stewardship mode should
link it back into plan-tree at a boundary instead of dumping raw runtime logs
into the planner conversation.

`task_detailer` may hold short-lived code and detailed clarification context,
but it should summarize accepted findings into durable artifacts and then be
released or parked according to workflow policy.
