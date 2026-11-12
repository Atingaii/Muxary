# Round Checker And Planner Rehydration

Date: 2026-06-25

## Problem

If `round_checker` is separate from planner, the next loop still needs planner
to understand what happened in the previous round. That must not be solved by
keeping planner's conversation context alive forever.

The workflow should keep semantic responsibilities separate while letting
planner rebuild the next task from durable evidence.

## Boundary

`round_checker` owns post-round judgment:

- read planner's verification contract;
- read node/checker/orchestrator outputs;
- design or confirm concrete round verification;
- decide whether the round is `pass`, `rework_node`, `partial`,
  `replan_required`, or `global_blocker`;
- write a compact round review report.

`round_checker` does not:

- change product scope;
- lower acceptance criteria;
- implement fixes;
- write authoritative task status;
- create the next plan.

Planner owns next-round planning:

- read the original task packet;
- read the round review report and evidence refs;
- decide whether to preserve completed sibling work;
- re-split failed or partial branches;
- revise requirements, acceptance, or verification only when justified;
- send user-facing uncertainty through broker/frontdesk.

Planner does not need previous conversation memory. It rehydrates from files.

## Rehydration Inputs

When planner is asked to prepare the next loop, it should load:

```text
task packet
  requirements.md
  acceptance-criteria.md
  verification-contract.md
  handoff.md
  review.md
  completion.md or partial/replan report

runtime evidence refs
  round.json
  asks.jsonl
  worker/checker artifacts
  aggregate reply
  round_checker reply/report
```

It should not load raw logs or every runtime event unless the round report
points to them as blocker evidence.

## Handoff Results

Round checker result routing:

| Result | Next Owner | Meaning |
| :--- | :--- | :--- |
| `pass` | script-owned child/task-set projection | Import completion evidence and mark the child done; Planner rehydrates once at task-set or milestone closure. |
| `rework_node` | orchestrator | A bounded node can fix the issue within the current plan. |
| `partial` | planner | Preserve completed sibling work and replan remaining branch. |
| `replan_required` | planner | Requirements, split, acceptance, or risk model must change. |
| `global_blocker` | broker/frontdesk when user decision is needed | External input or environment change is required. |

## V1 Simplification

For V1:

- Keep `round_checker` as a distinct role identity.
- Keep `plan_reviewer` as part of planner group; it may be a separate role
  later, but can start as an internal planner stage.
- Let deterministic `ccb plan` commands write task status and imported
  completion artifacts.
- Let `ccb loop run-once` produce round checker evidence, not final plan
  mutations.

This gives an end-to-end chain without making planner, checker, and plan
steward one large context.

Decision 029 refines the V1 pass path: successful child tasks do not each wake
Planner. A deterministic task-set join aggregates terminal child evidence and
submits one revision-fenced Planner closure backfill. Partial and replan
results may still activate Planner before final closure when macro work cannot
safely continue.

Related:
[../decisions/029-planner-feedback-and-task-set-closure.md](../decisions/029-planner-feedback-and-task-set-closure.md).
