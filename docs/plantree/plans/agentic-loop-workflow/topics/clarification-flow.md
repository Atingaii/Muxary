# Clarification Flow

Date: 2026-06-24

## Principle

Clarification should be stage-batched, artifact-first, and reference-driven,
but there are two different clarification surfaces:

- macro planning clarification, where planner emits candidate questions and a
  broker filters them before `frontdesk` presents them;
- task-local refinement clarification, where `task_detailer` already holds the
  relevant code and plan context and asks the user directly after `frontdesk`
  or frontend notifies the user where to answer.

Planner group may discover many uncertainties while shaping a plan, but it
should not stream all of them to `frontdesk` or to the user. It should emit a
candidate batch for the current phase. A broker then filters the batch into a
small set of user-facing questions, records defaults and deferrals, and returns
normalized answers to planner group.

`task_detailer` may discover narrower uncertainties while refining one macro
task into detailed execution artifacts. In that case, a separate broker or
`task_clarifier` role is not needed in V1. The detailer creates a
clarification-needed artifact, the frontend or `frontdesk` notifies the user,
the user answers inside the same `task_detailer` conversation, and the detailer
records a clarification summary before continuing.

The goal is to preserve context purity:

- `frontdesk` sees only the curated user-facing question artifact and answer
  status for macro planning, or a task-detailer clarification notification for
  task-local refinement.
- Planner group sees the broker review and normalized answers.
- `task_detailer` sees task-local answers and normalizes them into
  clarification summaries.
- Runtime artifacts hold raw candidates, raw answers, and fast-changing detail.
- Durable plan-tree files only receive accepted assumptions, decisions,
  blockers, or design consequences.

## Why Stage-Batched

Asking every question immediately creates too much context noise and forces
`frontdesk` into detailed planning. Asking every possible question up front
creates a long interrogation that may become obsolete once early answers or code
evidence change the plan.

Stage-batched clarification balances both risks:

- Ask only questions needed for the current phase.
- Let broker answer or default low-risk details from existing evidence.
- Defer later-phase uncertainty until it is actually needed.
- Keep one compact user interaction per phase when possible.

## Role Boundaries

| Role | Input | Output | Must Not Do |
| :--- | :--- | :--- | :--- |
| planner group | Macro task, plan-tree, code evidence | Candidate question batch | Directly ask the user |
| clarification broker | Candidate questions and evidence refs | User question artifact, assumptions, deferrals, normalized answers | Start execution loop |
| frontdesk | User question artifact ref | Raw user answer | Inspect all planning scratch by default |
| planner group after answer | Normalized answers and assumptions | Updated plan or execution-ready artifact | Re-ask broker-resolved details |
| task_detailer | Macro task refs, plan-tree/source evidence, detail packet draft | Clarification-needed artifact, clarification summary, detailed execution packet | Maintain long-term plan-tree, dispatch workers, or broaden macro scope |
| frontdesk/frontend for task detail | Clarification-needed notification ref | User routed to `task_detailer` | Interpret task-detail question by default |

## Broker Lifecycle

The persistent component is not a long-lived semantic agent. Persistent state is:

- Question queue.
- Candidate question batch.
- Broker review.
- User-facing question artifact.
- Raw answers.
- Normalized answers.
- Deferred and obsolete question records.

The semantic broker should normally be launched with fresh context for one phase
batch, then released. A deterministic router can remain as a CCB helper that
creates files, validates schemas, and wakes the next owner.

## Macro Runtime File Layout

```text
.ccb/runtime/loops/<loop-id>/clarification/<phase>/
  candidate_questions.jsonl
  broker_review.json
  user_questions.md
  assumptions.jsonl
  deferred_questions.jsonl
  obsolete_questions.jsonl
  raw_answers.jsonl
  normalized_answers.jsonl
```

Task-local detailer clarification uses a per-task detailer surface instead of
the macro broker queue:

```text
.ccb/runtime/loops/<loop-id>/tasks/<task-id>/detailer/
  detail-packet.manifest.json
  detail-readiness.json
  clarification/
    clarification-needed.md
    clarification-needed.json
    raw-answer-ref.json
    clarification-summary.md
    clarification-summary.json
```

The frontend or `frontdesk` should receive only a compact notification event:

```json
{
  "event": "detail_clarification_needed",
  "loop_id": "20260624-rich-workflow-001",
  "task_id": "task-001",
  "detailer_agent": "task_detailer",
  "question_ref": ".ccb/runtime/loops/20260624-rich-workflow-001/tasks/task-001/detailer/clarification/clarification-needed.md",
  "artifact_manifest_ref": ".ccb/runtime/loops/20260624-rich-workflow-001/tasks/task-001/detailer/detail-packet.manifest.json"
}
```

It should route the user to the indicated `task_detailer`; it should not expand
or reinterpret the question by default.

## Candidate Question Shape

```json
{
  "question_id": "q-001",
  "phase": "planning",
  "asked_by": "planner",
  "question": "Should rich workflow be enabled by default for new projects?",
  "why_needed": "Default behavior changes install and startup experience.",
  "decision_surface": "product_scope",
  "blocking": true,
  "options": ["default_on", "opt_in", "project_config"],
  "evidence_refs": [
    "docs/plantree/plans/agentic-loop-workflow/roadmap.md"
  ],
  "default_if_unanswered": null,
  "defer_until": null
}
```

## Broker Classification

| Class | Meaning | Action |
| :--- | :--- | :--- |
| `user_needed` | Current phase is blocked by user preference, scope, or risk tolerance | Include in `user_questions.md` |
| `answerable` | Code, plan-tree, or prior answer already resolves it | Record broker answer and evidence |
| `assumed` | Safe default is acceptable for current phase | Record in `assumptions.jsonl` |
| `deferred` | Real question, but not needed for this phase | Record in `deferred_questions.jsonl` |
| `obsolete` | Plan changed and the question no longer applies | Record in `obsolete_questions.jsonl` |
| `split` | One question contains several decision surfaces | Split before classification |

## User Question Budget

The default target should be one compact question set per phase, with a small
maximum such as three user-facing questions unless the workflow spec raises the
budget. If more questions remain after broker filtering, broker should prefer:

1. Ask questions that block current phase safety or scope.
2. Default low-risk implementation details.
3. Defer future-phase choices.
4. Escalate to `frontdesk` only with the curated display artifact reference.

## Reference-First Handoff

Broker should avoid sending large text payloads through agent messages. It
should send compact references:

```json
{
  "event": "questions_ready",
  "loop_id": "20260624-rich-workflow-001",
  "phase": "planning",
  "display_ref": ".ccb/runtime/loops/20260624-rich-workflow-001/clarification/planning/user_questions.md",
  "count": 2
}
```

`frontdesk` presents the display artifact to the user, records the raw answer,
and returns only the answer artifact reference:

```json
{
  "event": "user_answered",
  "loop_id": "20260624-rich-workflow-001",
  "phase": "planning",
  "raw_answer_ref": ".ccb/runtime/loops/20260624-rich-workflow-001/clarification/planning/raw_answers.jsonl"
}
```

Broker then normalizes the answer and notifies planner:

```json
{
  "event": "answers_normalized",
  "loop_id": "20260624-rich-workflow-001",
  "phase": "planning",
  "answers_ref": ".ccb/runtime/loops/20260624-rich-workflow-001/clarification/planning/normalized_answers.jsonl"
}
```

## Event Flow

```text
planner_group
  -> ccb question candidates
  -> clarification_broker
  -> ccb question broker-review
  -> ccb question publish
  -> frontdesk
  -> ccb question answer
  -> clarification_broker
  -> ccb question resolve
  -> planner_group
```

Broker resolution must not directly activate `loop runner` or execution nodes.
Planner group remains responsible for incorporating clarified answers into the
plan and marking the task ready through the normal planning review path.

Task-local refinement flow:

```text
orchestrator/loop_runner
  -> task_detailer
  -> clarification-needed artifact
  -> frontdesk/frontend notification
  -> user talks to task_detailer
  -> task_detailer clarification-summary
  -> task_detailer detail packet
  -> plan/detail review gate
  -> orchestrator
```

The task-local flow does not need `clarification_broker` unless later evidence
shows that detailer/user clarification becomes too long, too cross-cutting, or
requires a stricter UI/form/audit process.

## Answer Normalization

Raw answers should be preserved, but planner should consume normalized records:

```json
{
  "question_id": "q-001",
  "raw_answer_ref": "raw_answers.jsonl#1",
  "normalized_decision": "project_config",
  "confidence": "high",
  "planner_note": "Use opt-in project config for v1; do not make rich default.",
  "requires_followup": false
}
```

If confidence is low, broker may return a second focused question to
`frontdesk`. It should not expand the scope or introduce unrelated questions in
that follow-up.
