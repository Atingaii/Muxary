# Minimum Production Candidate Goal

Date: 2026-06-29

Status: Historical narrow candidate gate. Current active Phase 6 acceptance
target is
[phase6-single-round-task-matrix-goal.md](phase6-single-round-task-matrix-goal.md).
Historical naming note: older `checker` references map to the current
`code_reviewer` execution-review role.

## Objective

Define and verify the smallest agentic workflow slice that can be treated as a
production-candidate gate, without claiming that the full multi-agent workflow
is ready as a default production mode.

The candidate target is intentionally narrow:

```text
frontdesk-style macro task
  -> planner activation
  -> clarification pause and answer import
  -> planner reactivation
  -> plan reviewer gate
  -> ready task
  -> one execution round
  -> dynamic worker/checker capacity
  -> round result import
  -> auto release and layout cleanup
```

This gate proves the program kernel can advance one complete workflow through
script-owned state and release all short-lived execution capacity.

## Candidate Scope

In scope:

- deterministic `ccb plan`, `ccb question`, and `ccb loop runner --once`
  command chain;
- project-local workflow RolePacks for frontdesk, planner, broker,
  plan reviewer, orchestrator, worker, checker, and round checker;
- fake-provider execution as the default reproducible gate;
- one task, one runner activation chain, one execution round, and bounded
  dynamic `worker + checker` capacity;
- `release --policy auto` cleanup with no retained dynamic worker/checker
  agents;
- evidence that scripts do not infer semantic success from generic provider
  text.

Out of scope for this candidate:

- long-running workflow daemon;
- automatic production default enablement for new CCB projects;
- unbounded multi-round loops;
- fully dynamic multi-node fanout beyond the bounded smoke topology;
- user-facing rich/sidebar workflow dashboard;
- real-provider mandatory CI gates;
- automatic release publishing or destructive recovery.

## Acceptance Criteria

The candidate gate passes only when:

- `workflow_smoke_status` is `ok`;
- planner initial activation is recorded;
- clarification reaches `needs_clarification` and pauses for frontdesk;
- normalized answers return the task to `draft`;
- planner is reactivated after answers;
- `ready` is rejected before review and accepted after review import;
- runner executes one round;
- final task status is terminal or replan/blocked by explicit imported
  evidence;
- capacity release uses `policy=auto`;
- retained dynamic capacity count is zero;
- generated loop workers/checkers are absent from `ps` after release;
- final cleanup reaches `kill_status: ok`;
- all commands run through `/home/bfly/yunwei/ccb_source/ccb_test` from
  `/home/bfly/yunwei/test_ccb2` with isolated `HOME`, `CCB_SOURCE_HOME`, and
  `AGENT_ROLES_STORE`.

The fake-provider smoke may end in `blocked` when the round checker does not
emit a machine-readable pass marker. That remains acceptable for conservative
evidence gates, because scripts must not convert ambiguous semantic output into
success. The deterministic bridge smoke may also end in `done` when the fake
round checker emits an explicit `round result: pass` marker.

## Verification Command

Run from the external test root, not from the source checkout:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
python /home/bfly/yunwei/ccb_source/scripts/workflow_closure_smoke.py \
  --test-root /home/bfly/yunwei/test_ccb2 \
  --project-name workflow-min-prod-candidate-<stamp> \
  --ccb-test /home/bfly/yunwei/ccb_source/ccb_test \
  --reset --run --json
```

Recommended focused source regression before or after the smoke:

```bash
PYTHONPATH=lib python -m pytest -q \
  test/test_workflow_closure_smoke_script.py \
  test/test_question_cli.py \
  test/test_orchestrator_rolepack.py \
  test/test_loop_capacity_cli.py
```

## Latest Verification

2026-07-02 source-wrapper planner-output import bridge smoke:

```text
project_root: /home/bfly/yunwei/test_ccb2/planner-bridge-smoke-20260702
provider: fake
task_id: task-bridge
runner_planner: imported_planner_output
planner_imported_artifacts: requirements, acceptance, verification, handoff
next_activation_after_planner: activate_plan_reviewer
runner_plan_reviewer: imported_plan_reviewer_output
reviewer_imported_artifacts: review
task_status_after_review: ready
next_activation_after_review: execute
loop_id: lpdb912e
execution: ran_one_round
round_result: pass
round_result_source: round_checker_reply
final_task_status: done
final_artifacts: requirements, acceptance, verification, handoff, review, round_pass
dynamic_agents: loop-lpdb912e-worker-1, loop-lpdb912e-code_reviewer-1
release_status: released
released_count: 2
retained_count: 0
dynamic_agents_still_in_ps: false
cleanup: kill_status ok
```

Interpretation:

- `ccb loop runner --once --consume-role-output` now consumes explicit
  machine-readable planner and plan-reviewer bundles from ask/watch replies;
- planner output is committed through existing `ccb plan task-artifact`
  authority, not by direct agent mutation of task indexes or status;
- plan-reviewer output imports the review artifact and commits `ready` only
  through the existing `ccb plan task-status` validation path;
- the subsequent runner activation enters the existing orchestrator execution
  bridge, creates dynamic worker/reviewer capacity, records a round pass, and
  releases all short-lived dynamic agents.

2026-07-01 source-wrapper planner-task/orchestrator smoke:

Historical note: this smoke used deprecated `agentroles.planner_task`
material. Current mainline design uses `agentroles.planner` and routes task
detailing through orchestrator triage.

```text
project_root: /home/bfly/yunwei/test_ccb2/planner-task-orchestrator-real-20260701
planner role: agentroles.planner_task (historical/deprecated)
orchestrator role: agentroles.orchestrator
provider: fake
task_id: planner-e2e-001
planner activation: job_d6ad68d3cd55 completed
planner artifact auto-import: not implemented; task remained draft with no artifacts
manual script-owned artifact import: requirements, acceptance, verification, handoff
plan reviewer activation: job_ae46f904a0f8 accepted
ready before review: rejected
ready after review: accepted
loop_id: lp6227c7
dynamic agents: loop-lp6227c7-worker-1, loop-lp6227c7-code_reviewer-1
worker/reviewer/orchestrator/round_checker ask status: completed
round import: round_blocker
final task status: blocked
release_policy: auto
release_status: released
released_count: 2
retained_count: 0
dynamic_agent_count after release: 0
cleanup: kill_status ok
```

Interpretation:

- the historical/deprecated host-neutral `planner_task` role was mountable in
  a CCB source test project and activated by `loop runner --once`;
- the current workflow runner is still submit-only for planner activation and
  does not yet consume planner replies or auto-import planner-authored
  artifacts;
- once planner artifacts are committed through `ccb plan` commands, the
  ready-task to orchestrator execution path works: the runner binds the task,
  creates dynamic worker/reviewer capacity, dispatches the round, imports round
  evidence, and releases both short-lived dynamic agents;
- the final `blocked` status is expected with fake-provider output because no
  machine-readable round-checker pass marker was present.

2026-06-29 source verification:

```text
python -m pytest -q \
  test/test_workflow_closure_smoke_script.py \
  test/test_question_cli.py \
  test/test_orchestrator_rolepack.py \
  test/test_loop_capacity_cli.py

40 passed
```

2026-06-29 source-wrapper candidate smoke:

```text
project_root: /home/bfly/yunwei/test_ccb2/workflow-min-prod-candidate-20260629-110507
provider: fake
workflow_smoke_status: ok
task_id: task-closure
loop_id: lp76bbd9
final_status: blocked
round_result: blocked
round_result_source: missing_round_checker_result
release_policy: auto
release_status: released
released_count: 2
retained_count: 0
dynamic_agents_absent_from_ps: true
namespace_reflowed_windows: main
removed_dynamic_agents: loop-lp76bbd9-worker-1, loop-lp76bbd9-code_reviewer-1
```

Interpretation:

- the minimum scripted workflow candidate gate passed;
- the `blocked` terminal status is expected for fake-provider evidence because
  no machine-readable round-checker pass marker was present;
- auto-release removed both generated loop agents and preserved all long-lived
  workflow panes;
- this evidence supports controlled beta use of the scripted one-shot workflow
  kernel, not default production enablement.

## Production Readiness Boundary

Passing this gate means:

- the minimum scripted workflow closure is healthy;
- dynamic execution capacity can be created, used, and cleaned up;
- the role and artifact chain is coherent enough for controlled beta use.

It does not mean:

- the workflow should be enabled by default;
- long-running autonomous multi-round execution is safe;
- all real-provider edge cases are covered;
- planner, broker, monitor, and recovery roles are production-complete.

Promotion beyond this candidate requires a second gate with opt-in real
Codex/Claude provider lanes and a third gate for multi-round partial/replan
behavior.
