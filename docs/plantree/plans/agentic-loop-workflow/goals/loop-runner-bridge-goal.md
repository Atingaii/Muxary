# Goal: Loop Runner Bridge V1

Date: 2026-06-26

## Objective

Remove the remaining manual bridge between a ready durable task packet and one
completed execution round.

The V1 goal is a narrow one-shot bridge:

```text
ready task packet
  -> bind task to loop
  -> run one execution round
  -> import round result
  -> advance task status
  -> stop, pause, or leave planner-reactivation state
```

This goal is complete only when `/home/bfly/yunwei/test_ccb2` can create a
ready task packet, run `ccb loop runner --once`, and see the task transition
through script-owned state without hand-editing task files or runtime loop
state.

## Design Principle

This goal follows
[Decision 010: Simple Kernel, Flexible Agents](../decisions/010-simple-kernel-flexible-agents.md).

The program kernel must stay minimal, deterministic, idempotent, and easy to
recover. It owns only hard constraints:

- task-loop identity binding;
- per-task lock and lease checks;
- legal status edges;
- required artifact kinds;
- digest and metadata recording;
- round result import;
- bounded stop, pause, and retry decisions.

Model roles own semantic flexibility:

- planner writes requirements, acceptance criteria, verification contracts,
  risk notes, and replan/partial interpretations;
- orchestrator decomposes ready work and aggregates execution evidence;
- worker/checker roles execute bounded tasks and produce node evidence;
- round checker decides whether the integrated round passes, is partial,
  requires replanning, or is blocked.

The bridge must not encode semantic judgment into scripts. When semantics are
needed, an agent writes an artifact and the script commits or rejects it.

## Scope

In scope:

- `ccb plan task-bind-loop --task <task-id> --loop <loop-id> --json`
- `ccb plan task-import-round --task <task-id> --loop <loop-id> --result <pass|partial|replan_required|blocked> --report <path> --json`
- `ccb loop run-once --task-id <task-id> --json`
- `ccb loop runner --once --json`
- per-task lock or lease metadata sufficient to prevent duplicate one-shot
  runner execution for the same ready task;
- idempotent retry behavior when bind or import is repeated with the same
  task, loop, result, and report digest;
- first-class round artifact kinds:
  `round_pass`, `round_partial`, `round_replan`, and `round_blocker`;
- focused unit tests and one external source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2`.

Out of scope:

- long-running loop runner daemon;
- automatic background file watching;
- fully dynamic multi-round planning and execution;
- broker/question command surface;
- automatic planner activation for every planning state;
- arbitrary multi-task scheduling;
- complex semantic parsing of planner, orchestrator, or checker Markdown;
- pane layout reflow, provider replacement, or cross-window movement.

## Planned Command Contract

### Bind Ready Task To Loop

```bash
ccb plan task-bind-loop --task <task-id> --loop <loop-id> --json
```

Rules:

- task must exist and be `ready`;
- task must not already have an active different loop;
- command writes a machine-owned current-loop binding and lease metadata;
- repeating the same bind is idempotent if the existing binding is compatible;
- incompatible bind attempts fail without mutating state.

### Run One Round From Task

```bash
ccb loop run-once --task-id <task-id> --json
```

Rules:

- reads task breadcrumb/handoff instead of free-form CLI task text;
- creates or uses the bound loop id;
- calls the existing bounded `run-once` execution path;
- writes runtime artifacts under `.ccb/runtime/loops/<loop-id>/`;
- does not mark the task terminal by itself.

### Import Round Result

```bash
ccb plan task-import-round \
  --task <task-id> \
  --loop <loop-id> \
  --result <pass|partial|replan_required|blocked> \
  --report <path> \
  --json
```

Rules:

- report path must be inside the project and must match the loop result;
- script records byte count, sha256, source path, imported path, result,
  loop id, and timestamp;
- `pass` imports `round_pass` and advances task to `done`;
- `partial` imports `round_partial` and advances task to `partial`;
- `replan_required` imports `round_replan` and advances task to
  `replan_required`;
- `blocked` imports `round_blocker` and advances task to `blocked` or
  `needs_clarification` only when the report declares user input is required;
- repeated import with the same digest is idempotent;
- conflicting result or digest fails closed.

### One-Shot Runner

```bash
ccb loop runner --once --json
```

Rules:

- selects at most one ready task;
- binds it to a loop if needed;
- runs one execution round;
- imports the round result through `ccb plan task-import-round`;
- stops after one task and one round;
- returns a structured result with task id, loop id, action, status, and
  next activation recommendation.

## Acceptance Criteria

- A ready task can be consumed without manual copy/paste from breadcrumb to
  `loop run-once --task`.
- Duplicate `runner --once` invocations cannot both run the same task.
- Round result import is idempotent for identical reports and rejects
  conflicting reports.
- The script layer only commits structured state and metadata; semantic
  pass/partial/replan/blocker judgment comes from round checker artifacts.
- `partial` and `replan_required` do not claim success; they leave durable
  planner-reactivation states.
- Terminal or paused status is visible through `ccb plan task-show --json`.
- Runtime loop noise stays under `.ccb/runtime/loops`; plan-tree receives only
  imported durable evidence.

## Test Targets

Focused unit tests:

- task bind requires `ready`;
- compatible bind retry is idempotent;
- incompatible bind fails without mutation;
- per-task lock rejects duplicate active runners;
- `task-import-round` maps each result to the correct artifact kind and task
  status;
- import rejects path traversal, missing report, conflicting digest, and
  incompatible loop id;
- `loop run-once --task-id` reads task packet handoff/breadcrumb and writes
  loop artifacts;
- `loop runner --once` stops after one task and one round.

External smoke:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> plan task-create ...

HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> loop runner --once --json
```

The smoke must prove:

- source wrapper is used, not the installed release `ccb`;
- the project lives under `/home/bfly/yunwei/test_ccb2`;
- task reaches `ready` through `ccb plan` commands;
- runner executes one round through fake providers first;
- generated worker/checker agents release after idle evidence import;
- final task status is `done`, `partial`, `replan_required`, or `blocked`
  based on imported round evidence;
- no provider runtime is created when only `ccb plan` commands are used before
  the runner phase.

## Implementation Sequence

1. Add the task-loop binding data model and command.
2. Add round artifact kinds and import rules.
3. Extend `loop run-once` to accept `--task-id`.
4. Add one-shot `loop runner --once` selection and stop behavior.
5. Add focused tests for idempotence, lock behavior, and result mapping.
6. Run external fake-provider smoke in `/home/bfly/yunwei/test_ccb2`.
7. Update roadmap and landed evidence only after the smoke passes.

## Risks

- If bind/import commands are too broad, they will turn into a second workflow
  engine. Keep them narrow.
- If scripts infer semantic meaning from Markdown, they will become brittle.
  Require explicit result arguments and round checker report artifacts.
- If locking is weak, duplicate runners can corrupt task status. Lock before
  running the round, not after.
- If runtime loop details are copied into plan-tree eagerly, context purity is
  lost. Import only durable reports and metadata.

## Current Status

Verified in the current worktree.

Landed command surface:

- `ccb plan task-bind-loop --task <task-id> --loop <loop-id> --json`
- `ccb plan task-import-round --task <task-id> --loop <loop-id> --result <pass|partial|replan_required|blocked> --report <path> --json`
- `ccb loop run-once --task-id <task-id> --json`
- `ccb loop runner --once --json`

Verification evidence from 2026-06-27:

- Focused tests:
  `PYTHONPATH=lib pytest -q test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py`
  passed with `21 passed`.
- CLI/router/render regression tests:
  `PYTHONPATH=lib pytest -q test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py`
  passed with `102 passed`.
- Compile check passed for the touched CLI service, model, parser, phase2, and
  render modules with `python -m py_compile`.
- External source-wrapper smoke passed from `/home/bfly/yunwei/test_ccb2`
  using `/home/bfly/yunwei/ccb_source/ccb_test` in project
  `/home/bfly/yunwei/test_ccb2/loop-runner-bridge-smoke-1782493619`.

Smoke proof points:

- `ccb_test --diagnose` reported source wrapper
  `/home/bfly/yunwei/ccb_source/ccb_test`, source CLI
  `/home/bfly/yunwei/ccb_source/ccb.py`, cwd `/home/bfly/yunwei/test_ccb2`,
  and `allowed_source_test_project: yes`.
- Plan commands created task `bridge-smoke`, imported required planner
  artifacts, and marked it `ready`; `.ccb/ccbd` did not exist before the
  runner/start phase.
- `ccb loop runner --once --timeout 20 --json` returned
  `loop_runner_status=ok`, `action=ran_one_round`, loop `lp494c05`, and
  imported the round through `task-import-round`.
- The fake `round_checker` did not emit a valid standalone machine result, so
  the runner deliberately imported `round_blocker` with
  `round_result_source=missing_round_checker_result` instead of inferring a
  false `pass` from `loop_run_status=ok`.
- `ccb plan task-show --task bridge-smoke --json` reported
  `status=blocked`, `current_loop=None`, an imported lease, and artifact kinds
  `acceptance,handoff,requirements,review,round_blocker,verification`.
- Runtime round evidence stayed under
  `.ccb/runtime/loops/lp494c05/`; `ps` after the round showed only static
  `orchestrator` and `round_checker`, while generated worker/reviewer capacity
  had `released_count=2` and `retained_count=0`.

The next selected goal is
[Workflow Runner State Router V1](workflow-runner-state-router-goal.md), which
should build on this bridge without turning the script layer into a semantic
planner.
