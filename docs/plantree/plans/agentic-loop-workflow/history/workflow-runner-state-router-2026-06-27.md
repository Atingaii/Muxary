# Workflow Runner State Router Landing

Date: 2026-06-27

## Summary

Landed the first `ccb loop runner --once` state-router slice.

The router now selects one committed task state and performs exactly one
deterministic action:

- `ready` -> run the existing execution bridge;
- `draft`, `partial`, `replan_required` -> write a compact planner activation
  packet and submit one planner ask;
- `needs_clarification` -> stop paused for frontdesk;
- `blocked` -> stop blocked for frontdesk/recovery;
- `done` / `cancelled` -> stop terminal;
- no eligible task -> idle.

The script still does not interpret planner Markdown or infer semantic
success. It routes by committed status and lets roles produce artifacts.

## Artifact Metadata

`ccb plan task-artifact` and `ccb plan task-import-round` now record an
`actor` object on imported artifacts.

Fields:

- `source`: default `cli`, or explicit internal source such as `loop_runner`;
- `actor`: default `user`, or `CCB_CALLER_ACTOR` / runtime-derived actor /
  explicit internal actor;
- `role`: optional `CCB_ACTOR_ROLE` / explicit role;
- `job_id`: optional `CCB_JOB_ID`, `CCB_REQ_ID`, or explicit internal job id.

This gives planner, round checker, and future broker artifacts enough
provenance for audit and handoff without changing existing artifact paths or
digest semantics.

## Planner Activation Evidence

Planner activation writes compact JSON under:

```text
.ccb/runtime/loops/activations/<activation-id>.json
```

The packet is reference-first:

- task id and committed status;
- reason for activation;
- task packet root;
- artifact refs;
- round evidence refs for `partial` / `replan_required`;
- script write rules;
- stop limits;
- submitted planner ask job id.

## Verification

Focused tests:

```bash
PYTHONPATH=lib pytest -q test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
# 27 passed

PYTHONPATH=lib pytest -q test/test_orchestrator_rolepack.py test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
# 34 passed
```

Compile and whitespace checks:

```bash
PYTHONPATH=lib python -m py_compile \
  lib/cli/services/plan_tasks.py \
  lib/cli/services/loop_runner.py \
  lib/cli/services/loop_run_once.py \
  lib/cli/phase2_runtime/handlers_ops.py

git diff --check -- \
  lib/cli/services/plan_tasks.py \
  lib/cli/services/loop_runner.py \
  lib/cli/services/loop_run_once.py \
  lib/cli/phase2_runtime/handlers_ops.py \
  test/test_plan_tasks_cli.py \
  test/test_loop_capacity_cli.py \
  docs/plantree/plans/agentic-loop-workflow
```

External source-wrapper smokes from `/home/bfly/yunwei/test_ccb2`:

- `workflow-router-smoke-1782529622`: `draft` task activated planner only,
  returned `loop_runner_status=ok`, `action=activated_planner`, and wrote a
  planner activation packet with script rules.
- `workflow-router-paused-smoke-1782529659`: `needs_clarification` task stopped
  as `paused`, returned `next_owner=frontdesk`, and did not submit provider
  work.
- `workflow-router-ready-smoke-1782529767`: `ready` task ran the existing
  execution bridge with fake providers, imported a `blocked` round result
  because fake `round_checker` did not provide a machine-readable result line,
  and returned `round_result_source=missing_round_checker_result`.

## Remaining Work

- Add the V1 `ccb question` command/artifact surface for broker/frontdesk
  clarification.
- Extend planner follow-through: planner artifacts should be imported and
  reviewed through script-owned state before execution readiness.
- Add richer managed-job provenance when provider shells expose more explicit
  job/actor environment.
- Keep long-running daemon, recursive runner loops, and multi-task scheduling
  deferred.
