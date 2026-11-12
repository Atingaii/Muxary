# Decision 008: Separate Round Checker, Rehydrate Planner For Next Loop

Date: 2026-06-25

Status: Accepted

## Context

Planner defines what must be built and verified before execution. Round checker
judges what actually happened after a loop round. If they are merged, one role
becomes both the author of acceptance criteria and the judge of whether the
criteria were satisfied, which weakens drift resistance.

At the same time, a later loop round still needs planner to understand the
previous round. The design must avoid keeping planner's long conversation
context alive just to remember runtime details.

## Decision

Keep `round_checker` as a separate role identity from planner.

After each round, `round_checker` produces a compact round review report with
result, verification evidence, failed criteria, hidden-degradation findings,
and recommended next owner. CCB scripts or planner stewardship mode import
durable completion, partial, blocker, or replan evidence into the task packet.

When another loop is needed, planner is rehydrated from the task packet and
round evidence refs. Planner creates the next task or revised plan from files,
not from retained conversation memory.

## Consequences

- Planner context remains clean across long-running work.
- Round checker can independently challenge execution results.
- Next-loop planning still has full evidence through task packet and round
  report files.
- `pass` can go directly to planner / `ccb plan`; `partial` and
  `replan_required` return to planner; `global_blocker` reaches frontdesk only
  when a user decision is needed.
- V1 can keep `plan_reviewer` inside planner group while preserving
  `round_checker` as a separate role.

## Non-Goals

- This does not make round checker a final product-scope authority.
- This does not require planner to stay resident across rounds.
- This does not require raw runtime logs to enter durable plan-tree files.
- This does not implement the full multi-round loop runner state machine.
