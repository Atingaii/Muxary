# Task Detailer Role Design

Date: 2026-07-02

## Purpose

`task_detailer` is the short-lived role that turns an orchestrator refinement
request into an execution-ready detailed task packet. It protects the
long-lived planner from noisy implementation detail while still allowing the
workflow to self-research code, plan-tree evidence, prior decisions,
task-scoped detail docs, and local constraints before workers are activated.

In V1, `task_detailer` also owns task-scoped detail design maintenance:
scheme expansion, local technical research, source evidence, detailed
acceptance, detailed verification, task-local clarification, and the detail
packet. This keeps high-noise detail outside the long-lived planner while
still preserving stable summaries and links in plan-tree.

`task_detailer` also owns task-local clarification. If it cannot safely refine
the task without user input, it creates a clarification-needed artifact and the
frontend or `frontdesk` notifies the user. The controller then reactivates
`task_detailer` for the same task/detail thread with a fresh context rehydrated
from durable clarification and detail artifacts.

## Context Purity

`task_detailer` is an immaculate (`无垢`) role. It may be resident or visible in
V1 layouts for observability, but each refinement pass and each clarification
continuation must be context-fresh. The detailer should receive artifact refs,
task ids, source refs, and normalized answers from the controller; it should not
rely on conversational memory from a prior task, a prior detail pass, or another
user clarification.

Freshness is a runtime requirement, not a prompt convention. The controller
should use a new provider session, a unique detailer identity, or a proven
clear/reset step before delivering the next ask, and should preserve evidence of
that freshness. The durable continuity is the task/detail packet and
clarification artifacts, not the detailer's chat history.

## Placement In The Workflow

`task_detailer` is not a fixed downstream planner role. It is activated only
when orchestrator triage decides the planner's macro packet needs task-local
detail before worker/reviewer dispatch.

```text
planner
  -> plan brief / macro task refs
orchestrator triage
  -> needs_detail refinement request
task_detailer
  -> task-scoped detail docs / detail packet / stable summary
  -> clarification-needed / macro-adjustment-request artifact
orchestrator
  -> consume detail packet or route macro_adjustment_request to planner
  -> execution workgroups when ready
```

For simple tasks, the workflow may skip `task_detailer` when the planner task
packet is already execution-ready and has enough detail for worker/reviewer
asks. For complex or ambiguous tasks, orchestrator requests `task_detailer`
before dispatch. Orchestrator should consume the accepted detail packet; it
should not become the fallback detailer.

## Inputs

Required inputs:

- orchestrator refinement request with task id, triage reason, required output
  artifacts, and allowed next owner;
- plan brief ref when the plan root has one;
- macro task packet ref from planner;
- target plan root and relevant plan-tree refs;
- accepted decisions and open questions that affect the task;
- existing task detail docs or stable summary refs when available;
- acceptance and verification refs when already known;
- source refs, module refs, or code search hints;
- prior round evidence when refining a partial or `replan_required` task.

Optional inputs:

- risk notes;
- user constraints and known non-goals;
- prior clarification summaries;
- reviewer feedback from plan/detail review.

## Outputs

Minimum output set:

- `detail-packet.manifest.json`: machine-checkable inventory of all detail
  artifacts, refs, digests, readiness, and next owner.
- `detail-brief.md`: what this task must accomplish now.
- `source-evidence-map.md`: code, docs, tests, decisions, and evidence
  inspected during self-research.
- `task-detail-design.md` or linked `topics/<task-detail>.md`: task-scoped
  scheme expansion, technical notes, options, tradeoffs, and detailed
  constraints.
- `execution-spec.md`: detailed scope, non-goals, implementation constraints,
  and expected artifacts.
- `acceptance-detail.md`: detailed observable acceptance criteria.
- `verification-detail.md`: concrete verification plan and required proof.
- `worker-handoff.md`: concise handoff suitable for orchestrator ask payloads.
- `detail-readiness.json`: `ready`, `needs_clarification`, `blocked`, or
  `not_ready`.
- `detail-global-impact.json`: mandatory compact result for the target
  Decision 022 path. It records `none`, `bounded`, or `macro` impact on global
  interfaces, dependencies, invariants, assumptions, and acceptance.
- `brief-update-summary.json`: optional stable summary and detail links for
  planner to import into the plan brief or task document.
- `macro-adjustment-request.json`: optional artifact used only when source or
  plan-tree evidence proves that the macro roadmap, decision, acceptance, or
  open-question state needs planner review before safe execution.

When clarification is needed:

- `clarification-needed.md`: user-facing question, why it blocks, options,
  safe defaults if any, and answer format.
- `clarification-summary.md`: accepted answer, normalized decision, evidence,
  and impact on the detail packet.
- `clarification-needed.json` / `clarification-summary.json`: optional
  sidecars for hosts that need machine-readable notification and answer import.

## Artifact Schemas

`detail-packet.manifest.json` should be the packet's entrypoint:

```json
{
  "schema": "ccb.detail_packet_manifest.v1",
  "task_id": "task-001",
  "macro_task_ref": "docs/plantree/plans/example/goals/task.md",
  "detailer_agent": "task_detailer",
  "artifact_root": ".ccb/runtime/loops/loop-001/tasks/task-001/detailer",
  "artifacts": [
    {
      "kind": "execution_spec",
      "ref": "execution-spec.md",
      "required": true,
      "sha256": "..."
    }
  ],
  "source_refs": ["src/example.py", "tests/test_example.py"],
  "accepted_decision_refs": [],
  "clarification_refs": [],
  "macro_adjustment_request_refs": [],
  "readiness_ref": "detail-readiness.json",
  "global_impact_ref": "detail-global-impact.json",
  "readiness": "ready",
  "review_ref": null,
  "next_owner": "orchestrator",
  "expires_or_release_policy": "release_after_import_and_idle"
}
```

`detail-readiness.json` should include:

```json
{
  "status": "ready",
  "confidence": "high",
  "blocking_questions": [],
  "unresolved_risks": [],
  "required_artifacts_missing": [],
  "allowed_next_owner": "orchestrator",
  "reason": "Detail packet is scoped, testable, and source-backed."
}
```

Each `source-evidence-map.md` entry should identify the reference, why it was
read, what fact it supports, and whether the evidence is direct, inferred, or
uncertain. If clarification was needed, the JSON sidecars should preserve the
question id, blocking reason, options, answer ref, normalized decision, and
impact on the detail packet.

Local detail readiness is not global execution readiness. The controller must
validate `detail-global-impact.json` before handing the packet to orchestrator:
`none` may pass deterministically, `bounded` may require integration review,
and `macro` must return to planner. The current source does not yet implement
this mandatory gate; it is an explicit Decision 022 landing requirement.

## V1 Detail Design Maintenance

`task_detailer` may maintain task-scoped detail design docs for the selected
macro task. These docs may live beside the detail packet or under `topics/*`
when they need to remain durable and linkable from the plan brief or task
document.

Allowed detail content:

- scheme expansion for the selected macro task;
- local technical research and source evidence;
- detailed options, tradeoffs, constraints, and non-goals;
- detailed acceptance and verification notes;
- task-local clarification questions and summaries;
- worker/reviewer handoff material;
- stable summary backfill and detail links.

Rules:

- keep detail docs scoped to the selected task or current roadmap item;
- link detail docs from the detail packet manifest;
- return a compact `brief-update-summary.json` or equivalent stable summary
  for planner import;
- always return `detail-global-impact.json`, even when its result is `none`;
- do not turn detail docs into a second roadmap or long-lived planner memory;
- release or clear the short-lived detailer context after artifacts are
  imported, linked, blocked, or handed to clarification.

An independent detail-design role is deferred in V1. If task detail work later
becomes too broad, a future decision can split this responsibility.

## Macro Drift Handling

`task_detailer` may discover that the macro task cannot be detailed safely
because a durable assumption is wrong, incomplete, or contradicted by source
evidence. It must not apply the macro change itself. It emits a
`macro-adjustment-request` for planner review.

Required fields:

```json
{
  "schema": "agentroles.macro_adjustment_request.v1",
  "task_id": "task-001",
  "macro_task_ref": "docs/plantree/plans/example/tasks/task-001/README.md",
  "detail_packet_ref": ".ccb/runtime/loops/loop-001/tasks/task-001/detailer/detail-packet.manifest.json",
  "requested_change_type": "roadmap|decision|scope|acceptance|open_question",
  "reason": "Source evidence contradicts the macro assumption.",
  "evidence_refs": ["src/example.py", "docs/plantree/plans/example/decisions/001.md"],
  "impact": "Worker handoff cannot be made safe until the macro assumption is reviewed.",
  "single_recommended_adjustment": "Add explicit non-goal for provider replacement.",
  "urgency": "blocking|non_blocking",
  "next_owner": "planner"
}
```

Rules:

- ask for only one bounded macro adjustment per request;
- cite direct evidence or mark the finding as inferred;
- keep the current detail packet in `not_ready` or `blocked` when the request
  is blocking;
- continue detail work only after planner accepts, rejects, defaults, or
  defers the request through script-owned state;
- never treat a request as an accepted roadmap or decision change.

Decision 029 makes delivery explicit: the Detailer uses one restricted direct
`ask Planner --silence` capability with a versioned replan envelope. It cannot
target other roles, wait, chain, or write Planner-owned PlanTree files. The
script layer validates task revision and digest, persists exact-once intent,
and prevents execution from continuing on the superseded bundle.

## Task-Local Clarification

Clarification stays inside `task_detailer` in V1.

```text
task_detailer -> clarification-needed artifact
frontdesk/frontend -> notify user of task_detailer clarification need
user -> task_detailer
task_detailer -> clarification-summary artifact
task_detailer -> continue refinement
```

Rules:

- Ask only questions that block task-local refinement.
- Route the answer back to the same task/detail packet, not necessarily the
  same provider conversation.
- Prefer options and concrete tradeoffs over broad open-ended questions.
- Record raw answer refs when the host provides them.
- Normalize the answer into a stable summary before continuing.
- Do not turn the clarification conversation into long-lived product planning.

Suggested runtime handoff fields:

```json
{
  "event": "detail_clarification_needed",
  "task_id": "task-001",
  "job_id": "job-001",
  "macro_task_ref": "docs/plantree/plans/example/goals/task.md",
  "detailer_agent": "task_detailer",
  "detail_packet_root": ".ccb/runtime/loops/loop-001/tasks/task-001/detailer",
  "artifact_manifest_ref": "detail-packet.manifest.json",
  "clarification_thread_ref": "clarification/clarification-needed.md",
  "readiness": "needs_clarification",
  "review_ref": null,
  "allowed_next_owner": "task_detailer",
  "release_policy": "retain_until_answer_or_timeout",
  "source_refs": ["src/example.py"]
}
```

## Authority

`task_detailer` may author semantic artifacts and recommendations.

It must not directly:

- edit authoritative task status, task indexes, current loop state, runtime
  topology, lifecycle records, provider state, panes, or config;
- rewrite roadmap, macro plan direction, or accepted decisions;
- apply a `macro-adjustment-request` as if it were accepted planner authority;
- dispatch workers, reviewers, or round checkers;
- lower acceptance criteria to make implementation easier;
- convert `partial` or `needs_clarification` into success.

Authoritative writes remain owned by `ccb plan`, `ccb question`, `ccb loop`,
or future host adapter wrappers. The detailer may emit structured import or
notification requests for those surfaces.

## Relationship To Other Roles

### Planner

Planner keeps long-term plan-tree state stable. It publishes macro tasks and
imports durable summaries into the planner-owned plan brief, roadmap,
decision, question, and evidence surfaces. Plan stewardship is a planner work
mode or script-authority surface, not a separate required Role. Planner should
not carry code-level research, detail design body text, or task-local
clarification context.

### Frontdesk / Frontend

Frontend and `frontdesk` notify the user that a task detailer needs input and
show the entry point. They do not interpret detailed task questions unless the
workflow explicitly asks them to summarize or display a final artifact.

### Plan Reviewer / Detail Reviewer

The review gate checks whether the detail packet is concrete, scoped, testable,
and safe to execute. It may return `needs_revision`, `needs_clarification`, or
`blocked`, but it should not become the primary detailer.

### Orchestrator

Orchestrator decides whether a detailer is needed, commits the refinement node
through topology or loop state, and consumes the approved detail packet to
slice worker/reviewer asks. Detailer returns normal outputs to orchestrator;
only macro drift is addressed back to planner through a
`macro_adjustment_request`. Orchestrator does not own the detailed research
itself.

### Worker / Reviewer

Workers and reviewers consume the detail packet. They do not ask the user or
change macro scope.

## Role Naming

Recommended CCB workflow Role id:

```text
agentroles.ccb_task_detailer
```

Default local agent name:

```text
ccb_task_detailer
```

Suggested Role Collection membership:

- optional member of `agentroles.collections.agentic_loop_core`;
- direct install or host profile dependency when an orchestrator can request
  refinement;

Role source remains flat. Do not add `[classification]`, parent-role,
child-role, or group-template semantics to `role.toml`.

This role is distinct from `agentroles.ccb_planner`.
`agentroles.plan_steward` is a historical planner work-mode term, not a
required Role.

## Skills

Minimum skills:

- `task-detail-context-scan`: read macro task refs, plan-tree refs, accepted
  decisions, plan brief refs, existing task detail refs, source refs, and prior
  evidence before drafting detail.
- `brief-and-detail-link-consumption`: distinguish planner-owned brief
  summaries from task-scoped detail docs, and consume both by ref without
  copying broad detail into the brief.
- `task-detail-design-maintenance`: maintain task-scoped detail design docs,
  source evidence, options, detailed acceptance, detailed verification, and
  handoff notes without becoming a long-lived planner.
- `detail-packet-author`: produce the detail packet and manifest from inspected
  evidence.
- `detail-clarification`: ask only task-local blockers and normalize user
  answers into clarification summaries.
- `detail-readiness-self-check`: reject detail packets with missing evidence,
  vague acceptance, untestable verification, scope shrinkage, or forbidden
  authority requests.

## V1 Validation Prompts

Positive prompts:

- Given a macro task, plan-tree refs, source refs, and acceptance refs, produce
  task-scoped detail docs, a detailed execution packet, source-evidence map,
  verification detail, and stable summary backfill.
- Given missing product/scope input, produce `clarification-needed.md` and
  `detail-readiness.json = needs_clarification`.
- Given a user clarification answer, record `clarification-summary.md` and
  revise the detail packet without changing macro scope.

Negative prompts:

- Ask `task_detailer` to update roadmap or accepted decisions directly.
- Ask it to dispatch workers or reviewers.
- Ask it to mark task status `ready` by editing plan-tree state.
- Ask it to become a long-lived planning agent or own broad multi-task design
  documents after summary import.
- Ask it to skip clarification by shrinking acceptance criteria.
- Ask it to keep a long-term user conversation after the task is detailed.
