# Workflow Role Output Import Bridge

Date: 2026-07-02

## Summary

The missing bridge between planner/task_detailer/plan-reviewer role output and
script-owned task packets has landed in the current source tree.

`ccb loop runner --once --consume-role-output` now performs one bounded
role-output consumption step:

- submit the planner, task_detailer, or plan-reviewer ask;
- watch the returned job once;
- accept only an explicit JSON bundle with the expected schema;
- write bundle text into the activation import area;
- import allowed artifacts through `ccb plan task-artifact`;
- for task_detailer only, request `detail_ready` through
  `ccb plan task-status` after the required detail packet is imported;
- for plan reviewer only, request `ready` through `ccb plan task-status`.

The default runner path remains submit-only unless `--consume-role-output` is
set.

Task detailer output is now bounded to task-scoped artifacts:

- `detail_design`
- `detail_summary`
- `detail_packet`
- optional `macro_adjustment_request`

The `detail_ready` status requires `detail_design`, `detail_summary`, and
`detail_packet`. A macro adjustment request is saved for planner or plan
steward review but does not directly mutate roadmap, brief, decisions, or task
status.

## Verification

Focused source tests:

```text
python -m pytest \
  test/test_loop_capacity_cli.py \
  test/test_plan_tasks_cli.py \
  test/test_workflow_closure_smoke_script.py -q

39 passed
```

Source-wrapper bridge smoke:

```text
project_root: /home/bfly/yunwei/test_ccb2/agentic-loop-v1-smoke-20260702162851
provider: fake
task_id: task-closure
runner_planner: activated_planner
runner_task_detailer: imported_task_detailer_output
task_detailer_detail_ready: true
runner_plan_reviewer: activated_plan_reviewer
review_import: manual smoke artifact
task_status_after_review: ready
execution: ran_one_round
round_result: pass
final_task_status: done
dynamic_agents: loop-lpb589b2-worker-1, loop-lpb589b2-code_reviewer-1
release_status: released
released_count: 2
retained_count: 0
dynamic_agents_still_in_ps: false
cleanup: kill_status ok
```

## Consequences

- The workflow kernel can now close a deterministic fake-provider task from
  draft to done with an explicit task_detailer stage and script-owned detail
  readiness gate.
- The bridge preserves the simple-kernel/flexible-agent principle: agents
  propose artifacts; scripts validate and commit.
- Ambiguous planner text remains non-authoritative. There is no free-form
  Markdown parsing or status inference.
- The next workflow-runtime gap is topology-driven dispatch from committed
  runtime workflow graphs and formal RolePack alignment, not planner/detailer
  artifact import.
