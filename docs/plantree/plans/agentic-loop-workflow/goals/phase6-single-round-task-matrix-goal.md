# Phase 6 Single-Round Task Matrix Goal

Date: 2026-07-03
Status: Planning

## Objective

Define the acceptance gate for Phase 6 as single-round workflow success across
different task types, not as a claim that the full long-running workflow is
already production-ready.

Phase 6 passes only when the current workflow kernel can complete one bounded
round for each supported task route, with script-owned state transitions and
safe dynamic agent cleanup.

The broader real-provider stress and capability assessment is tracked in
[phase6-real-capability-assessment-goal.md](phase6-real-capability-assessment-goal.md).
This file defines the minimum single-round matrix; the real assessment expands
it with complexity levels, abnormal-state injection, and post-run failure
analysis.

## Acceptance Boundary

Phase 6 proves:

- `frontdesk -> planner -> task artifacts -> orchestrator -> optional
  task_detailer -> worker/reviewer -> round_summary -> planner import` can
  close one round;
- the orchestrator chooses the correct route for different task types;
- task-local clarification can happen inside the same round when needed;
- worker/reviewer collaboration stays ask-first;
- planner only records compact macro outcomes after the round;
- dynamic execution agents release or retain safely after the round.

Phase 6 does not prove:

- long-running workflow daemons or autonomous continuous looping;
- multi-round convergence across partial or replan branches;
- default real-provider production readiness;
- rich/mobile/sidebar workflow UX;
- complex fanout graphs or arbitrary team-builder DSL behavior.

## Required Artifacts

Each Phase 6 test task must use the same stable anchors:

- `task_packet.md`: macro task and scope.
- `execution_contract.md`: round acceptance contract and verification rules.
- `orchestration_notes.md`: orchestrator route and mount decision evidence.
- `round_summary.md`: compact round result imported through scripts.

Route-scoped step policy:

- `direct_execution`: `steps/step-*.md` is optional. The planner remains
  macro-only; a sufficiently explicit `task_packet + execution_contract` is
  enough.
- `needs_detail`: `steps/step-*.md` is required after
  `ccb_task_detailer` refinement.
- `partial_completion`: `steps/step-*.md` is required so partial progress can
  be mapped to explicit unfinished steps.

This keeps Decision 018 intact: planner stays macro-only, task detailer owns
task-local detail expansion, and orchestrator does not become the default step
author.

## Task Matrix

Phase 6 should cover at least these single-round task types:

1. `direct_execution` task:
   planner output is already executable; orchestrator skips detailer and mounts
   one `worker + code_reviewer` pair.
2. `needs_detail` task:
   planner output is macro-only; orchestrator activates `ccb_task_detailer`,
   imports detailed packet/steps, then mounts execution.
3. `macro_adjustment_request` task:
   orchestrator detects macro inconsistency before execution, returns compact
   adjustment evidence to planner, and the round ends without mounting workers.
4. `blocked` task:
   orchestrator or detailer cannot proceed due to missing hard dependency or
   unresolved user input; task stays blocked by imported evidence, not by
   provider text guesswork.
5. `partial_completion` task:
   the round completes with only part of the bounded scope accepted; imported
   evidence records which steps passed and which remain open, and the task
   ends `partial` rather than being treated as a failed test.

The success target for Phase 6 is:

- the `direct_execution` and `needs_detail` tasks complete one round
  successfully;
- the `macro_adjustment_request` and `blocked` tasks terminate correctly with
  the expected non-success state and evidence;
- the `partial_completion` task terminates correctly with explicit `partial`
  evidence and unfinished-step traceability;
- no route silently falls back to another route.

## Happy-Path Test Flow

For `direct_execution` and `needs_detail`, the test flow is:

```text
frontdesk input
  -> planner writes task_packet + execution_contract
  -> task becomes ready_for_orchestration
  -> orchestrator triages the route
  -> optional task_detailer expands details and step files
  -> orchestrator imports orchestration_notes
  -> mount topology apply + ask reachability proof
  -> worker/code_reviewer execute one bounded round
  -> round_summary import
  -> planner imports compact stable summary
  -> dynamic release or safe retain
```

Expected end state:

- route decision matches the test task type;
- smoke evidence records `route_decision_correct=true`;
- required artifacts exist and are imported through scripts;
- one round completes without hidden dispatch DSL;
- planner receives only compact stable outcome fields;
- dynamic worker/reviewer panes are released when idle.

## Negative And Branch Tests

Phase 6 should also prove these abnormal single-round outcomes:

1. Reviewer rejects worker output once:
   worker receives one bounded rework inside the same round, then the round
   still reaches imported `pass` evidence.
2. Reviewer cannot accept within the bounded round:
   round ends as `partial` or `replan_required`, not fake success.
3. Detailer needs user clarification:
   task transitions back through the frontdesk/user surface, resumes, and still
   completes a single round after clarification import.
4. Busy release:
   execution agent is marked `retained_busy`, not killed; later reconcile may
   release it after idle proof.
5. Ask failure or provider interruption:
   imported blocker evidence is recorded; no script infers success from missing
   or ambiguous output.

Bounded-round rule:

- a single round may contain at most one reviewer-driven rework cycle;
- if review still fails after that one rework, or if the round exceeds its
  explicit timeout budget, the round must end as `partial`,
  `replan_required`, or `blocked`;
- a Phase 6 smoke must never hide repeated retries inside one "successful"
  round.

## Pass Criteria

Phase 6 passes only when:

- all `direct_execution` tasks in the matrix end with imported `round_result:
  pass`;
- all `needs_detail` tasks in the matrix import a detail packet and then end
  with imported `round_result: pass`;
- all `partial_completion` tasks end with imported `round_result: partial`,
  explicit unfinished-step evidence, and task status not equal to `done`;
- `macro_adjustment_request` tasks do not mount worker/reviewer agents, import
  visible adjustment evidence, and end with planner ownership restored through
  `next_owner=planner` plus a non-terminal or replan state;
- `blocked` tasks preserve explicit blocker evidence and never become `done`;
- worker/reviewer direct ask works without topology communication edges;
- reviewer output must cite `execution_contract` verification rules; contract-
  free reviewer approval is rejected by the import path or the smoke fails;
- planner summary import remains macro-only and does not rewrite task detail
  docs;
- smoke evidence records `route_decision_correct=true` for every task;
- no dynamic execution agents remain mounted after idle auto-release cleanup;
- no tests rely on real-provider credentials.

## Verification Layers

Phase 6 verification should be split into three layers:

1. Focused unit/CLI tests:
   task artifact validation, route mapping, state transitions, round-result
   import, release/retain behavior, and mount-topology guards.
2. Source-wrapper fake-provider smokes:
   the minimum matrix should include:
   - `smoke-direct-execution-pass`;
   - `smoke-needs-detail-pass`;
   - `smoke-macro-adjustment`;
   - `smoke-blocked`;
   - `smoke-reviewer-reject-rework`;
   - `smoke-reviewer-cannot-accept`;
   one smoke per task type from `/home/bfly/yunwei/test_ccb2` using
   `/home/bfly/yunwei/ccb_source/ccb_test`. `smoke-busy-release` may be a
   separate seventh smoke or an explicit cleanup phase inside a direct-
   execution smoke.
3. Optional real-provider opt-in smoke:
   one tiny `direct_execution` task and one tiny `needs_detail` task. This is
   useful evidence, but not a CI blocker for Phase 6.

## Review Gate

Independent review should confirm:

- Phase 6 is still a single-round acceptance gate, not a hidden multi-round
  workflow claim;
- planner remains macro-only;
- `ccb_task_detailer` is route-activated, not part of every task by default;
- topology remains mount-only in mainline;
- `ask` is still the normal collaboration channel;
- scripts remain the only authority for task state transitions;
- reviewer can force non-success outcomes without the system downgrading the
  acceptance bar.

## Next Work If Phase 6 Passes

If this gate passes, the next gap is not more single-round coverage. The next
gaps are:

- multi-round convergence;
- long-running loop supervision and restart recovery;
- real-provider stability gates;
- long-term document governance;
- user-facing workflow observability.
