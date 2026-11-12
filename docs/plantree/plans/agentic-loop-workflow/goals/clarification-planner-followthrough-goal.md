# Goal: Clarification And Planner Follow-Through V1

Date: 2026-06-27

## Objective

Complete the next minimal workflow loop after the state-router landing:

```text
planner activation
  -> planner artifacts or candidate questions
  -> optional broker/frontdesk clarification
  -> normalized answers
  -> planner artifact import
  -> plan reviewer review
  -> script-owned ready transition
```

The goal is not to build a broad workflow engine. The goal is to give the
already-landed `ccb loop runner --once` planner activation a durable follow-up
path so a `draft`, `partial`, or `replan_required` task can move toward
`ready` through script-owned artifacts instead of stopping at a submitted
planner ask.

## Design Principle

Keep the kernel small and stable.

```text
program kernel owns hard constraints
roles own semantic judgment
scripts commit or reject role artifacts
```

The program owns identity, schema validation, path safety, provenance, task
state edges, artifact manifests, locks, leases, and one-step routing. It must
not parse complex Markdown to infer user intent, planning quality, or
readiness.

Roles own semantic flexibility:

- `planner` drafts task-packet artifacts, readiness recommendations, and
  candidate questions;
- `clarification_broker` filters, merges, defaults, defers, and normalizes
  questions;
- `frontdesk` presents curated user questions and returns user answers;
- `plan_reviewer` checks ambiguity, risk, acceptance, verification, and hidden
  fallback before `ready`.

## Current Baseline

Already landed:

- workflow RolePack drafts for `planner`, `plan_reviewer`,
  `clarification_broker`, `frontdesk`, `orchestrator`, `worker`, `checker`,
  and `round_checker`;
- `ccb plan task-*` task packet, artifact import, status, bind-loop,
  import-round, show/list, and breadcrumb surfaces;
- first `ccb loop runner --once` state router:
  - `ready` -> execution bridge;
  - `draft`, `partial`, `replan_required` -> planner activation packet and
    one planner ask;
  - `needs_clarification` -> paused/frontdesk;
  - `blocked`, `done`, terminal -> deterministic stop;
- artifact actor/job provenance on `ccb plan` imports;
- source-wrapper smokes in `/home/bfly/yunwei/test_ccb2` for draft planner
  activation, paused clarification stop, and ready execution bridge.

See
[../history/workflow-runner-state-router-2026-06-27.md](../history/workflow-runner-state-router-2026-06-27.md).

## Scope

In scope:

- define and implement a V1 `ccb question` command/artifact surface;
- store candidate questions, broker-filtered user questions, raw answers,
  normalized answers, defaults, deferrals, and planner wakeup refs;
- wire broker/frontdesk clarification into the durable task lifecycle;
- extend planner follow-through so planner artifacts are imported through
  `ccb plan`;
- activate `plan_reviewer` and import its review artifact;
- keep `ready` transition script-owned and review-backed;
- add focused tests and source-wrapper smokes from
  `/home/bfly/yunwei/test_ccb2`.

Out of scope:

- long-running runner daemon;
- recursive loop execution inside one command;
- arbitrary workflow-spec interpreter;
- multi-task scheduling;
- free-form Markdown semantic parsing inside scripts;
- direct planner-to-worker execution;
- high-frequency runtime log sync into plan-tree;
- broad dynamic-pane/layout changes.

## Proposed Command Surface

### Candidate Questions

```bash
ccb question candidate-import \
  --task <task-id> \
  --file <candidate-questions.jsonl> \
  --json
```

Purpose:

- import planner-generated candidate questions;
- validate JSONL shape and project-local file path;
- record provenance, byte count, sha256, source path, and imported path;
- keep task status unchanged unless a separate script transition is requested.

### Broker User Questions

```bash
ccb question user-batch-import \
  --task <task-id> \
  --file <user-questions.md|json> \
  --json
```

Purpose:

- import broker-filtered user-facing questions;
- record defaults and deferrals when present;
- allow the runner to pause the task at `needs_clarification` with question
  refs for frontdesk.

### Raw And Normalized Answers

```bash
ccb question answer-import \
  --task <task-id> \
  --file <raw-answer.md|json> \
  --json

ccb question normalized-import \
  --task <task-id> \
  --file <normalized-answers.jsonl> \
  --json
```

Purpose:

- store raw user answer separately from broker-normalized answers;
- preserve frontdesk context purity by linking to artifacts;
- wake planner with compact answer refs instead of pasted conversation logs.

### Question Status

```bash
ccb question status --task <task-id> --json
```

Purpose:

- report question batch state, unresolved blocking questions, defaults,
  deferred questions, answer refs, normalized-answer refs, and next owner.

## Artifact Schemas

V1 should keep schemas simple and explicit.

Candidate JSONL line:

```json
{"id":"q1","stage":"planning","question":"...","why_blocking":"...","default_if_unanswered":"","defer_allowed":true}
```

User question batch:

```json
{
  "schema": "ccb.workflow.user_questions/v1",
  "task_id": "task-123",
  "batch_id": "qbatch-123",
  "questions": [
    {"id": "q1", "text": "...", "why": "...", "required": true}
  ],
  "defaults": [],
  "deferred": []
}
```

Normalized answer JSONL line:

```json
{"question_id":"q1","answer":"...","source":"user|default|deferred","planner_note":"..."}
```

Scripts validate shape, required fields, local paths, digest, and known task
identity. Scripts do not judge whether an answer is semantically sufficient.

## State Routing

The existing runner behavior remains one activation per invocation.

New V1 routing expectation:

| State / Artifact Condition | Runner Action |
| :--- | :--- |
| `draft` with no candidate questions | activate planner |
| planner imports candidate questions | activate broker or pause for broker path |
| broker imports user-facing questions | set/keep `needs_clarification` and stop for frontdesk |
| raw + normalized answers imported | reactivate planner with answer refs |
| planner imports required task artifacts | activate `plan_reviewer` |
| review artifact imported and requirements met | allow `task-status ready` |
| `ready` | execution bridge |

The runner should stop after each activation and return `next_action` rather
than chaining recursively.

## Planner Follow-Through

Planner artifacts should continue to use `ccb plan task-artifact`:

- `requirements`
- `acceptance`
- `verification`
- `risk`
- `handoff`
- readiness recommendation artifact if needed later

`plan_reviewer` produces `review.md`. `ready` remains blocked unless required
artifacts are present. The script may require `review` for V1, matching the
current `ccb plan` ready guard.

## Acceptance Criteria

- A `draft` task can be routed to planner, then receive candidate questions
  through `ccb question candidate-import`.
- Broker can import a user-facing question batch and move or keep the task in
  `needs_clarification`.
- Frontdesk/user answers can be imported as raw and normalized answer
  artifacts.
- Runner can reactivate planner with answer refs.
- Planner artifacts can be imported through `ccb plan task-artifact`.
- `plan_reviewer` can be activated and its review imported.
- `task-status ready` succeeds only after required artifacts and review are
  present.
- `runner --once` then routes the ready task to the existing execution bridge.
- Every imported artifact records provenance.
- Scripts never infer readiness from free-form Markdown.

## Goal Slices

This goal should be landed in narrow slices. Each slice must keep the program
kernel deterministic and leave semantic judgment in role artifacts.

### Slice 1: Question Artifact Surface

Deliver:

- parser/model/handler support for `ccb question`;
- candidate, user-batch, raw-answer, normalized-answer, and status actions;
- task-local artifact storage with digest, byte count, source path, imported
  path, timestamp, actor, and job/request provenance;
- JSON/JSONL shape validation and project-local path safety;
- focused parser/service tests.

Stop after this slice if the command surface is not stable. Do not wire
planner/broker automation around a weak artifact contract.

### Slice 2: Runner Question Awareness

Deliver:

- `needs_clarification` runner stop responses include question artifact refs;
- normalized answers can wake planner through compact answer refs;
- runner still performs at most one activation per `--once`;
- no provider is activated during pure question import.

### Slice 3: Planner Follow-Through

Deliver:

- planner imports requirements, acceptance, verification, risk, handoff, and
  readiness recommendation artifacts through `ccb plan`;
- planner activation packets include question/answer refs when present;
- task status changes remain script-owned.

### Slice 4: Plan Reviewer Gate

Deliver:

- activate `plan_reviewer` after required planner artifacts exist;
- import reviewer output as the existing `review` artifact;
- allow `task-status ready` only when required artifacts and review are
  present;
- route the ready task to the existing execution bridge.

## Test Targets

Focused tests:

- parser tests for `ccb question` subcommands;
- question import rejects invalid JSON/JSONL, unknown task, external file
  paths, duplicate conflicting question ids, and malformed required fields;
- question import records provenance and digest metadata;
- question status reports candidate/user/raw/normalized refs;
- runner stops on `needs_clarification` with question refs;
- runner reactivates planner after normalized answers exist;
- planner review import allows ready transition only through existing
  `ccb plan` guard;
- no provider activation occurs during pure question import.

Existing tests to extend where practical:

```bash
PYTHONPATH=lib pytest -q \
  test/test_plan_tasks_cli.py \
  test/test_loop_capacity_cli.py \
  test/test_orchestrator_rolepack.py
```

New tests may live in:

```text
test/test_question_cli.py
```

## External Smoke

All source validation must run from `/home/bfly/yunwei/test_ccb2` with:

```bash
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> ...
```

Required smoke path:

1. create project with fake planner, broker, frontdesk, reviewer, orchestrator,
   worker/checker profiles as needed;
2. create `draft` task;
3. run `ccb loop runner --once --json` -> planner activation;
4. import candidate questions;
5. import broker-filtered user question batch;
6. verify runner returns `needs_clarification` / frontdesk stop;
7. import raw and normalized answers;
8. run runner -> planner activation with answer refs;
9. import planner task artifacts;
10. activate/import `plan_reviewer` review;
11. set task `ready`;
12. run runner -> execution bridge;
13. verify final status is `done`, `partial`, `replan_required`, or `blocked`
    based only on imported round evidence.

## Implementation Sequence

1. Add the `ccb question` parser/model/service skeleton.
2. Add durable question artifact layout under each task root.
3. Implement candidate/user-batch/raw-answer/normalized-answer imports.
4. Add question status output and provenance metadata.
5. Extend runner routing to include question refs in paused/planner activation
   responses.
6. Add broker/frontdesk handoff behavior without direct user conversation
   automation.
7. Add plan reviewer activation/import follow-through.
8. Run focused tests.
9. Run external source-wrapper smoke.
10. Update roadmap, open questions, and history evidence.

## Long-Running Goal Prompt

Use this prompt when handing the work to a future agent:

```text
You are continuing the CCB agentic-loop workflow landing.

Active goal:
docs/plantree/plans/agentic-loop-workflow/goals/clarification-planner-followthrough-goal.md

Implement the goal, not only the documentation. Preserve the core design rule:
the program kernel owns hard constraints and state transitions; roles own
semantic judgment through artifacts.

Start by reading the active goal, the workflow roadmap, and the existing
`ccb plan` / `ccb loop runner --once` implementation. Then land the next
narrow incomplete slice with tests:

1. Prefer the smallest deterministic script surface.
2. Store durable artifacts under the task packet, with provenance and digest.
3. Validate schemas, task identity, and project-local paths.
4. Do not parse free-form Markdown for readiness or semantic sufficiency.
5. Keep `runner --once` to one activation or one stop response per invocation.
6. Source validation must use
   `/home/bfly/yunwei/ccb_source/ccb_test` from
   `/home/bfly/yunwei/test_ccb2`, with isolated `HOME` and
   `CCB_SOURCE_HOME`.

Do not mark the goal complete until every acceptance criterion in the goal
document is proven by focused tests and an external source-wrapper smoke.
```

## Risks

- If `ccb question` becomes a semantic broker, scripts will become brittle.
  Keep scripts to schema/path/provenance/status constraints.
- If runner chains planner, broker, frontdesk, and reviewer in one invocation,
  recovery becomes opaque. Keep V1 one activation per `--once`.
- If frontdesk receives raw planner question floods, context pressure returns
  to the user-facing role. Broker must compact first.
- If normalized answers overwrite raw answers, auditability is lost. Store both.
- If reviewer is bypassed for `ready`, planner can silently lower quality gates.

## Current Status

In progress.

Landed in current worktree:

- `ccb question` parser/model/phase2/service/handler/dispatch surface;
- `candidate-import`, `user-batch-import`, `answer-import`,
  `normalized-import`, and `status` actions;
- task-local question artifact storage under
  `docs/plantree/plans/<plan>/tasks/<task>/questions/`;
- artifact index records with source path, imported path, byte count, sha256,
  timestamp, actor/job provenance, and import history;
- JSON/JSONL shape validation for candidate questions, user question batches,
  raw JSON answers, and normalized answers;
- project-local path safety checks;
- `user-batch-import` moves or keeps `draft` tasks at
  `needs_clarification`;
- `normalized-import` moves answered `needs_clarification` tasks back to
  `draft` so the one-shot runner can activate planner;
- runner paused responses include compact question refs;
- planner activation packets include compact question/answer refs when present;
- draft tasks with requirements, acceptance, verification, and handoff
  artifacts now activate `plan_reviewer` when review is missing;
- plan reviewer activation packets include compact artifact refs and script
  write rules for importing `review` and only then requesting `ready`;
- full source-wrapper fake-provider smoke now reaches the ready execution
  bridge and imports round evidence back to the task packet.

Verification evidence:

```bash
PYTHONPATH=lib pytest -q test/test_question_cli.py
# 7 passed

PYTHONPATH=lib python -m py_compile \
  lib/cli/services/questions.py \
  lib/cli/models_start.py \
  lib/cli/models.py \
  lib/cli/parser_runtime/commands.py \
  lib/cli/parser_runtime/__init__.py \
  lib/cli/parser_runtime/constants.py \
  lib/cli/parser.py \
  lib/cli/phase2.py \
  lib/cli/phase2_services.py \
  lib/cli/phase2_runtime/context.py \
  lib/cli/phase2_runtime/handlers_ops.py \
  lib/cli/phase2_runtime/dispatch.py \
  lib/cli/services/plan_tasks.py \
  lib/cli/services/loop_runner.py \
  test/test_question_cli.py
# passed

PYTHONPATH=lib pytest -q \
  test/test_plan_tasks_cli.py \
  test/test_loop_capacity_cli.py \
  test/test_orchestrator_rolepack.py
# 34 passed

PYTHONPATH=lib pytest -q \
  test/test_question_cli.py \
  test/test_plan_tasks_cli.py \
  test/test_loop_capacity_cli.py \
  test/test_orchestrator_rolepack.py
# 41 passed

git diff --check
# passed
```

External source-wrapper smoke:

```text
project: /home/bfly/yunwei/test_ccb2/question-followthrough-smoke-1782531830
wrapper: /home/bfly/yunwei/ccb_source/ccb_test
result: question_smoke_status ok
covered: task-create, candidate-import, user-batch-import, runner paused
with question refs, raw answer import, normalized answer import, status
artifact_count: 4

project: /home/bfly/yunwei/test_ccb2/plan-review-guard-smoke-1782532093
wrapper: /home/bfly/yunwei/ccb_source/ccb_test
result: review_guard_status ok
covered: task-create, planner artifact imports, ready rejection before
review, review import, ready success after review

project: /home/bfly/yunwei/test_ccb2/question-followthrough-e2e-smoke-1782532792
wrapper: /home/bfly/yunwei/ccb_source/ccb_test
result: e2e_status ok
covered: config validate, mounted fake-provider start, draft planner
activation, candidate question import, user question import,
needs_clarification pause with question refs, raw answer import, normalized
answer import, planner reactivation with answer refs, planner artifact imports,
plan_reviewer activation, ready rejection before review, review import, ready
success after review, ready execution bridge, round evidence import
final_status: blocked
round_result: blocked
round_result_source: missing_round_checker_result
round_artifact: round_blocker
```

Completion audit:

- Draft routing to planner: proven by focused tests and e2e smoke
  `planner1_action=activated_planner`.
- Candidate question import: proven by focused tests and e2e smoke
  `candidate-import`.
- Broker/user question batch import and `needs_clarification`: proven by
  focused tests and e2e smoke `paused_status=paused`.
- Raw and normalized answer imports: proven by focused tests and e2e smoke.
- Planner reactivation with answer refs: proven by focused test activation
  packet assertion and e2e smoke `planner2_action=activated_planner`.
- Planner artifacts through `ccb plan task-artifact`: proven by review guard
  smoke and e2e smoke artifact imports.
- `plan_reviewer` activation and review import: proven by focused test,
  review guard smoke, and e2e smoke `reviewer_action=activated_plan_reviewer`.
- `ready` only after required artifacts plus review: proven by focused test,
  review guard smoke, and e2e smoke ready-before failure / ready-after success.
- Ready task routes to execution bridge: proven by e2e smoke
  `execute_action=ran_one_round`.
- Imported artifacts record provenance: proven by focused tests for question
  and plan artifact metadata.
- Scripts do not infer readiness from Markdown: code path validates schema,
  path, digest, artifact presence, and status edges; e2e final result is
  `blocked` with `round_result_source=missing_round_checker_result` rather
  than inferred pass from fake provider text.

Current goal status: complete in the current worktree.
