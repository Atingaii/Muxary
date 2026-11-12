# Planner Feedback And Task-Set Closure Plan

Date: 2026-07-12
Status: P0-P4 integrated; P5 direct acceptance active
Authority: [Decision 029](../decisions/029-planner-feedback-and-task-set-closure.md)

## Objective

Close the two missing Planner feedback loops without turning Controller code
back into a semantic message broker:

1. Task Detailer can return macro-impact findings to Planner after source
   investigation or user clarification.
2. A Planner-created task set produces one revision-fenced aggregate closure,
   Planner Roadmap backfill, and Frontdesk/user status report after all required
   child work reaches a stable outcome.

## Current Gaps

- `detail_summary` and `macro_adjustment_request` are durable evidence, but
  normal `detail_ready` proceeds to Orchestrator without a hard global-impact
  branch or direct Detailer-to-Planner capability.
- Planner task-set import marks the source intake done at decomposition time.
- Child tasks have independent `round_summary` records but no parent task-set
  lifecycle or final-child join.
- Per-task `pass` goes terminal without Planner rehydration.
- Mixed child results have no deterministic aggregate precedence.
- There is no exact-once Planner completion backfill or subsequent Frontdesk
  status notification.
- Existing tests prove per-task routing and task-set creation, not Roadmap-level
  closure.

## Target Flow

```text
Frontdesk --silence--> Planner
                         |
                         +-> task-set authority + child tasks
                                      |
                     Orchestrator -> optional Task Detailer
                                      |          |
                       local detail --+          +--silence--> Planner replan
                                      |
                               Worker/Reviewer rounds
                                      |
                             child round imports
                                      |
                          deterministic task-set join
                                      |
                       closure envelope --silence--> Planner
                                                       |
                                      Roadmap/Brief/TODO revision import
                                                       |
                                           --silence--> Frontdesk -> user
```

## Durable State

Add a versioned task-set authority surface under the owning plan, for example:

```text
docs/plantree/plans/<plan>/task-sets/<task-set-id>/
  task-set.json
  closure.json
  closure-summary.md
  planner-backfill.json
  frontdesk-status.json
```

`task-set.json` is script-owned and contains source request identity, Planner
job, plan revision, task-set revision, child membership, required/optional
flags, and current aggregate state. Human Roadmap prose remains Planner-owned.

Runtime intent belongs under:

```text
.ccb/runtime/task-sets/<task-set-id>/
  events.jsonl
  planner-feedback-intents.jsonl
  frontdesk-status-intents.jsonl
```

No runtime file is PlanTree semantic authority.

## Protocols

### Detailer feedback envelope

`ccb.detailer.replan_request.v1` requires:

- task id/revision and source Detailer job;
- current Planner packet and orchestration bundle digests;
- user clarification refs when user discussion changed intent;
- macro-impact categories;
- preserved facts and proposed changes;
- acceptance/dependency/Roadmap impacts;
- detail summary and macro-adjustment artifact digests.

The RolePack receives exactly one managed capability: silent inline ask to the
resident Planner with this schema. Generic shell/CCB access and arbitrary
targets remain denied.

### Task-set closure envelope

`ccb.plan.task_set_closure.v1` requires:

- task-set id/revision and source request;
- expected legacy PlanTree projection digest;
- ordered child ids and revisions;
- status, last-round result, artifact digest, cleanup/release state per child;
- aggregate result and deterministic reason;
- accepted output refs, incomplete scope, blockers, and replan inputs;
- closure evidence digest and exact-once intent id.

The envelope must not contain raw provider logs or exceed the normal inline
request limit. Large evidence remains behind immutable refs and digests.

### Planner backfill result

Planner returns a proposal containing:

- updated Brief summary;
- Roadmap/TODO node transitions;
- next milestone or explicit terminal state;
- decision/open-question/evidence link updates;
- whether user-visible reporting is required;
- compact Frontdesk status body.

Scripts validate the expected legacy PlanTree projection digest and allowed
Planner-owned paths before applying the proposal. This single-lane digest maps
to `legacy_projection_digest` under Decision 031; it is not a portfolio, plan,
or task revision and cannot replace a typed authority closure for multi-lane
writes.

## State Machine

Suggested task-set states:

```text
planning
  -> decomposed
  -> running
  -> closure_pending
  -> planner_backfill_pending
  -> frontdesk_notification_pending
  -> closed

exceptional:
  -> replan_required
  -> partial
  -> blocked
  -> system_failure
  -> cancelled
```

`decomposed` is not completion. `closed` requires child aggregation, Planner
backfill import, and either a persisted Frontdesk notification or an explicit
script-owned `notification_not_required` decision.

## Implementation Waves

### P0: Freeze schemas and invariants

- Add task-set, Detailer feedback, closure, Planner backfill, and Frontdesk
  status schemas/models.
- Define result precedence, required/optional child semantics, size limits,
  digest calculation, and revision rules.
- Add failing tests that demonstrate current premature source-task settlement
  and missing final-child closure.

Gate: no runtime behavior changes until schema and negative tests agree.

### P1: Task-set parent authority

- Persist task-set identity during Planner task-set import.
- Replace decomposition-as-completion with `decomposed/running` parent state.
- Bind every child to task-set id/revision and required/optional membership.
- Expose task-set show/status/effective-next-action diagnostics.

Gate: existing single-task behavior remains unchanged; V2 remains unchanged.

### P2: Detailer-to-Planner replan path

Implementation status: landed as the `workflow/g6c-detailer-planner` package
with RolePack command-surface, managed Codex/Claude transports, dispatcher
intent recovery, task revision fencing, stale bundle rejection, and focused
source tests. Commit SHA is recorded in the package handoff.

- Add explicit Detailer result classification and macro-impact validation.
- Add the sole restricted silent Planner capability to Task Detailer.
- Persist exact-once intent before submit and recover all crash windows.
- Fence old bundle/activation and prevent Worker dispatch after accepted
  replan feedback.
- Import Planner revision and launch a fresh Orchestrator only after authority
  validation.

Gate: local detail still returns directly to Orchestrator; only global impact
activates Planner.

### P3: Task-set closure aggregator

- Observe child authority transitions, not provider replies.
- Refuse closure while children, cleanup, release, or evidence are incomplete.
- Compute deterministic mixed-result aggregate and closure digest.
- Create exactly one Planner closure intent on the final required transition.
- Recover submit/persist/start crashes without duplicate Planner asks.

Gate: all-pass, pass+blocked, pass+partial, multiple replan, all-blocked, stale
revision, and system-failure rows are deterministic.

### P4: Planner backfill and Frontdesk notification

- Add Planner closure mode and revision-fenced PlanTree proposal import.
- Update Brief/Roadmap/TODO/decision/open-question/evidence links.
- Select next milestone or terminal Roadmap state.
- Submit one restricted status message to Frontdesk when required.
- Keep Frontdesk read-only; it reports the imported Planner summary to the
  user without changing workflow authority.

Gate: a macro request is not `closed` before Planner backfill and notification
settlement.

### P5: Recovery, compatibility, and real acceptance

- Run full source/fake matrix and non-provider-blackbox suite.
- Run fresh visible real-provider projects for the scenario matrix below.
- Capture jobs, callback/intent records, task-set state, PlanTree revisions,
  UI/panes, topology/release, and shutdown residue.
- Preserve failed fresh roots as evidence; never reuse them after repair.

Gate: direct `talk2` evidence audit passes without hidden fallback or
controller-authored semantic messages.

## Test Matrix

### Detailer feedback

| Case | Expected behavior |
| :--- | :--- |
| local source-backed refinement | `detail_ready`; no Planner ask; fresh Orchestrator resumes |
| user clarification confirms original plan | same local path; no Planner ask |
| user changes scope or acceptance | one silent Planner replan ask; old bundle fenced |
| Detailer finds dependency/interface conflict | one Planner ask with macro-impact evidence |
| repeated identical feedback | persisted job reused; no duplicate |
| same identity, different digest | fail visibly |
| submit/append/start crash | recover one Planner job |
| Planner pending | remain pending without timeout or Worker dispatch |
| Planner revision conflict | reject proposal and retry from current revision |
| repeated Planner/Detailer cycle | bounded automatic cycles, then user escalation |

### Task-set closure

| Case | Aggregate and closure behavior |
| :--- | :--- |
| all pass | one `pass` closure, Planner backfill, Frontdesk completion |
| pass + blocked | `partial`, landed and unresolved scope preserved |
| pass + partial | `partial`, one Planner request |
| multiple replan-required | one `replan_required` aggregate, not N asks |
| all blocked | `blocked`, Planner/Frontdesk escalation |
| child still running/clarifying | no closure |
| release or cleanup incomplete | system failure; no semantic pass |
| final child transition replayed | closure intent reused |
| restart before Planner submit | one recovered Planner job |
| restart after Planner completion before import | import same result once |
| new child added during closure | old intent stale; new revision required |
| old child result arrives after revision | rejected as stale evidence |
| Planner backfill revision conflict | no Roadmap overwrite |
| Frontdesk notification crash | one recovered notification |

### Real opened-project acceptance

1. One local-detail task that returns directly to Orchestrator.
2. One user clarification that changes scope and visibly returns to Planner.
3. One all-pass three-task set that updates Roadmap and reports completion.
4. One mixed pass/blocked/partial task set with honest non-success summary.
5. One two-child replan case aggregated into one Planner activation.
6. One restart during closure and one revision-race injection.

Every project uses a fresh root under `/home/bfly/yunwei/test_ccb2`, explicit
worktree `ccb_test`, inherited requested provider environment, project-local
Role store, visible panes, and project-level shutdown immediately after
evidence capture.

## Rejection Conditions

- source intake marked macro-complete at decomposition;
- Controller writes semantic Planner or Frontdesk prose;
- Detailer edits Roadmap directly or targets a non-Planner role;
- multiple child failures generate multiple Planner asks;
- aggregate pass while any required child is incomplete/non-pass;
- closure before cleanup/release authority is clean;
- stale task-set, legacy projection digest, or Decision 031 authority closure
  accepted;
- duplicate Planner/Frontdesk notification after restart;
- Planner update silently overwrites newer user work;
- hidden timeout, fallback, scope shrink, or degraded success;
- final project leaves dynamic agent, worktree, branch, socket, or process
  residue.

## Dependencies And Boundaries

- Build on existing `submit_or_recover_ask_once`, task revision, callback,
  task-import-round, role-output import, PlanTree artifact, and release APIs.
- Do not add a generic workflow messaging bus or topology communication DSL.
- Do not implement multi-lane Roadmap scheduling as part of this package.
- Do not replace Worker-owned Reviewer chains or Frontdesk-owned intake.
- Packaging/publication remains behind the single-lane G6/G7 release gates.
