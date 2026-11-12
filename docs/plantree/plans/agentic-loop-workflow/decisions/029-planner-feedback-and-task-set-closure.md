# 029 Planner Feedback And Task-Set Closure

Date: 2026-07-12
Status: Accepted; implementation integrated, P5 acceptance active

## Context

The current single-task loop imports a Round Reviewer result correctly, but a
successful task becomes `done/terminal` without rehydrating Planner. Planner
task-set intake also settles the source Frontdesk task as soon as decomposition
finishes, before the imported child tasks execute. There is no script-owned
task-set identity that can detect the final child transition, aggregate mixed
outcomes, or notify Planner exactly once.

Task Detailer has a related gap. It can produce local detail artifacts and can
discover macro drift, but the current normal path returns a ready detail packet
to Orchestrator. A Detailer that learns from source inspection or user
clarification that the Planner task is wrong needs a direct, bounded way to ask
Planner to replan without editing Planner-owned PlanTree surfaces itself.

## Decision

Add two Planner feedback paths with one shared rule:

> Roles author semantic feedback; scripts validate identity, revisions,
> exact-once delivery, authority imports, and recovery.

### Detailer replan feedback

Task Detailer classifies its result as exactly one of:

- `local_detail_ready`: local execution detail is complete and the accepted
  macro scope, dependencies, acceptance, and Roadmap remain valid;
- `planner_replan_required`: source evidence or user clarification changes
  macro scope, public interfaces, dependencies, ordering, acceptance, risk, or
  another Planner-owned surface;
- `needs_clarification`: user input is still required in the current Detailer
  conversation;
- `blocked`: an external condition prevents safe refinement.

For `planner_replan_required`, Detailer submits one direct silent Planner ask
using a restricted `ccb.detailer.replan_request.v1` envelope. It cannot target
another role, chain, wait, write Roadmap files, or launch execution. Controller
code validates and persists the handoff but does not reconstruct its semantic
body.

The accepted request increments task revision, marks the task
`replan_required`, invalidates the old orchestration bundle, and prevents
Worker dispatch. Planner rehydrates from the original task packet, detail
summary, macro-adjustment request, user clarification evidence, and revision
fence. A revised task returns through a fresh immaculate Orchestrator.

### Task-set and Roadmap closure feedback

Planner task-set decomposition creates a script-owned task-set record instead
of treating decomposition as macro completion. The record binds:

- task-set id and revision;
- source Frontdesk request and Planner job;
- plan and Roadmap projection revision;
- ordered child task ids and required/optional membership;
- child task revisions and terminal evidence digests;
- closure intent, Planner backfill job, and Frontdesk notification identity.

The source intake may record `decomposed`, but it must not represent the macro
request as execution-complete until the task-set closure is accepted.

When the last required child reaches a stable terminal or replan state, a
deterministic aggregator writes `ccb.plan.task_set_closure.v1` and creates one
durable closure intent. It does not ask Planner while any child is running,
needs clarification, has incomplete release/cleanup authority, or references
a newer task-set revision.

Outcome precedence is:

| Child outcomes | Aggregate | Next owner |
| :--- | :--- | :--- |
| all required children `pass` | `pass` | Planner completion backfill |
| one or more `replan_required` | `replan_required` | Planner replans once from one aggregate |
| any `partial`, with no replan | `partial` | Planner preserves accepted work and plans remainder |
| pass plus required blocked child | `partial` | Planner records landed scope and unresolved branch |
| all unfinished required children blocked | `blocked` | Planner/Frontdesk escalation |
| cleanup, authority, revision, or evidence failure | no semantic result | Controller-visible system failure |

Multiple replan children produce one aggregate Planner request, not one
Planner ask per child.

Planner receives the validated closure envelope through one silent ask,
updates Brief/Roadmap/TODO/decision and evidence links under an expected
PlanTree revision, selects the next milestone, and emits one compact
`ccb.planner.frontdesk_status.v1` status message to Frontdesk when user-visible
reporting is required. Frontdesk reports the result; it does not reinterpret
execution evidence or modify plan authority.

The transport envelope has exactly `schema`, `closure`, `closure_intent`, and
the script-owned `closure_ref`. Its canonical project-relative path is echoed
exactly in Planner and embedded Frontdesk evidence refs; provider prose cannot
infer or rewrite it. Retry transport authority, where runtime owns it, is
`source_job_id`, `effective_job_id`, and ordered `retry_lineage`; every lineage
edge has exactly `message_id`, `source_attempt_id`, `successor_attempt_id`,
`retry_source_job_id`, `retry_successor_job_id`, and `retry_index`, recomputed
from message/attempt authority rather than arbitrary provider options. This
RolePack/fake corpus is source/fake protocol evidence only, not combined
runtime acceptance.

## Exact-Once And Revision Rules

- Detail feedback identity is task id + task revision + detail digest.
- Closure identity is task-set id + task-set revision + ordered terminal
  evidence digest.
- Same identity and digest reuses the persisted job; conflicting reuse fails.
- Submit/persist/start crashes recover from durable intent without duplicate
  Planner or Frontdesk asks.
- Adding, removing, or revising a child increments task-set revision and makes
  every older open closure intent stale.
- Planner writes use the expected legacy PlanTree projection digest; a conflict
  causes a visible retry/replan, never last-writer-wins.
- Provider replies remain proposals/evidence. Scripts own task, task-set,
  revision, closure, notification, and delivery authority.
- Business asks have no elapsed-time timeout. Only terminal provider/job state
  or explicit cancellation closes them.

## Minimal Controller Boundary

Controller code may:

- validate envelopes, role/target/silence rules, ids, revisions, and digests;
- persist and recover exact-once intent;
- aggregate script-owned child outcomes;
- import Planner proposals under revision fencing;
- gate Orchestrator/Worker activation and final release;
- expose evidence and system failures.

Controller code may not:

- compose Detailer's explanation of plan drift;
- decide how Planner changes Roadmap semantics;
- summarize provider prose into a user report;
- submit one Planner ask per failed child;
- mark a task set complete from decomposition alone;
- downgrade mixed outcomes to pass.

## Compatibility

Config V2 static workflows keep their existing behavior. This contract is a
Config V3 agentic-loop feature. Existing per-task round artifacts remain valid;
task-set closure adds parent aggregation authority rather than replacing child
authority.

For the integrated single-lane path, `expected PlanTree revision` means the
digest of the selected Planner projection files. Under Decision 031 it maps to
`legacy_projection_digest` inside one plan-level proposal. It is not the future
`portfolio_revision`, `plan_revision`, `task_revision`, or typed authority
closure and cannot authorize a multi-lane write by itself. Migration must carry
both the legacy digest and full Decision 031 basis until the old importer is
retired.

## Acceptance

- Source tests cover all aggregate rows, exact-once recovery, revision races,
  stale closure rejection, restricted role capabilities, and no premature
  completion.
- Real opened-project tests cover local Detailer return, user clarification
  leading to Planner replan, all-pass task-set closure, mixed partial/blocked
  closure, multi-replan aggregation, Planner Roadmap update, Frontdesk report,
  restart recovery, and zero dynamic/process residue.
- The source intake, task-set record, children, Planner backfill, Roadmap
  revision, Frontdesk notification, and final user-visible summary agree.

## Related

- [015-task-detailer-owns-task-refinement-and-clarification.md](015-task-detailer-owns-task-refinement-and-clarification.md)
- [018-planner-uses-plan-brief.md](018-planner-uses-plan-brief.md)
- [019-orchestrator-triage-before-task-detailer.md](019-orchestrator-triage-before-task-detailer.md)
- [028-frontdesk-owned-planner-silence-handoff.md](028-frontdesk-owned-planner-silence-handoff.md)
- [031-global-plan-tree-authority-across-worktrees.md](031-global-plan-tree-authority-across-worktrees.md)
- [../topics/planner-feedback-and-task-set-closure-plan.md](../topics/planner-feedback-and-task-set-closure-plan.md)
