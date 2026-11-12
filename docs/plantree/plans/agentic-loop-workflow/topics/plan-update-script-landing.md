# Plan Update Script Landing

Date: 2026-06-25

## Goal

Land the first script-owned plan-update surface so planner agents can create
and advance durable task packets without directly editing authoritative
plan-tree status or runtime loop records.

The first slice should prove the state-authority rule:

```text
agents draft content; CCB scripts write authority.
```

## V1 Minimum Command Surface

Start smaller than the full proposed command set.

```bash
ccb plan task-create --plan <plan-slug> --title "<title>" --json
ccb plan task-artifact --task <task-id> --kind <requirements|acceptance|verification|risk|handoff|review|completion> --file <path> --json
ccb plan task-status --task <task-id> --status <draft|needs_clarification|ready|running|partial|replan_required|done|blocked> --json
ccb plan task-show --task <task-id> --json
ccb plan task-list --plan <plan-slug> --json
ccb plan breadcrumb --task <task-id>
```

Defer for later:

- `ccb question ...` broker commands;
- `ccb plan sync` full plan-tree summary automation;
- `ccb loop create/start` integration beyond a ready-task handoff;
- multi-plan cross-index updates.

## Follow-Up Slice: Ready Task To One Round

The next narrow slice should connect an execution-ready task packet to one
`ccb loop run-once` invocation without introducing a daemon.

Minimum commands:

```bash
ccb plan task-bind-loop --task <task-id> --loop <loop-id> --json
ccb plan task-import-round --task <task-id> --loop <loop-id> \
  --result <pass|partial|replan_required|blocked> --report <path> --json
ccb loop run-once --task-id <task-id> --json
ccb loop runner --once --json
```

`task-bind-loop` writes `current_loop`, moves `ready` to `running` when needed,
and is idempotent for the same task/loop pair. It rejects terminal tasks and
rejects rebinding a running task to a different loop.

`task-import-round` writes first-class round evidence, maps the round result
to task status, clears `current_loop`, and updates limit counters:

| Round result | Artifact kind | Task status |
| :--- | :--- | :--- |
| `pass` | `round_pass` | `done` |
| `partial` | `round_partial` | `partial` |
| `replan_required` | `round_replan` | `replan_required` |
| `blocked` | `round_blocker` | `blocked` |

`loop runner --once` should scan for one `ready` task, bind it, run the round,
import the round checker result, and exit. If no ready task exists, it should
return an `idle` JSON result. Automatic planner activation, clarification
routing, long-running daemon ownership, and multi-task concurrency remain
deferred.

## Durable Task Layout

Scripts write under the target plan root:

```text
docs/plantree/plans/<plan-slug>/tasks/
  index.json
  <task-id>/
    README.md
    requirements.md
    acceptance-criteria.md
    verification-contract.md
    risk-notes.md
    handoff.md
    review.md
    completion.md
    artifacts/
```

`index.json` is machine-owned. Markdown files are durable task artifacts.

`README.md` should remain compact:

```text
Task: <title>
Task ID: <task-id>
Plan Root: <plan-slug>
Status: <status>
Current Loop: <loop-id|none>
Owner: <planner|loop_runner|frontdesk>
Created: <timestamp>
Updated: <timestamp>
```

## Authority Rules

`ccb plan` scripts own:

- task id allocation;
- task status;
- task index;
- current loop binding;
- status transition timestamps;
- imported artifact path and digest records.

Planner agents may create draft files outside the authoritative task packet,
then call `task-artifact` to import them. The import should record:

- source path;
- kind;
- destination path;
- byte count;
- sha256 digest;
- actor/job id when available;
- timestamp.

Scripts must reject:

- unknown plan slugs;
- path traversal outside the project;
- unknown artifact kinds;
- status transitions that skip required artifacts;
- `ready` without requirements, acceptance, verification, handoff, and review;
- terminal status changes without completion or blocker evidence;
- direct writes into `.ccb/runtime` through `ccb plan`.

## Status Edges

V1 task status graph:

```text
draft -> needs_clarification
needs_clarification -> draft
draft -> ready
ready -> running
running -> partial
running -> replan_required
running -> done
running -> blocked
partial -> replan_required
partial -> done
replan_required -> draft
blocked -> draft
```

Terminal for a single task packet:

- `done`
- `blocked`

`partial` and `replan_required` are durable loop results but not final product
completion.

## Planner Handoff Contract

Before `task-status --status ready` succeeds, the task packet must include:

- `requirements.md`
- `acceptance-criteria.md`
- `verification-contract.md`
- `handoff.md`
- `review.md`

`review.md` should come from `plan_reviewer` or an equivalent reviewer role.
It must state:

- remaining ambiguity;
- risk flags;
- acceptance/test adequacy;
- whether user clarification is still needed;
- readiness recommendation.

## Test Plan

Unit tests:

- create task id deterministically enough for tests while remaining collision
  safe;
- write task packet files and `tasks/index.json`;
- import artifact kinds to the correct destination;
- record source digest metadata;
- reject missing required artifacts on `ready`;
- reject invalid status edges;
- reject path traversal and unknown artifact kind;
- render breadcrumb from task state.

CLI contract tests:

- `ccb plan task-create --json`;
- `ccb plan task-artifact --json`;
- `ccb plan task-status --json`;
- `ccb plan task-show --json`;
- `ccb plan task-list --json`;
- `ccb plan breadcrumb`.

Integration smoke in `/home/bfly/yunwei/test_ccb2`:

1. create a temporary plan root;
2. create a task;
3. import planner draft artifacts;
4. attempt invalid `ready` before review and expect rejection;
5. import review;
6. mark ready;
7. show/list/breadcrumb;
8. optionally hand the ready task to the existing `loop run-once` or
   orchestrator capacity smoke in a later slice.

Regression guard:

- plan scripts must not start providers;
- plan scripts must not mutate `.ccb/runtime/loops`;
- plan scripts must not require installed global `ccb` during source tests;
- source validation must use `/home/bfly/yunwei/ccb_source/ccb_test` from
  `/home/bfly/yunwei/test_ccb2`.

## Acceptance Criteria

The slice is done when:

- planner role design is documented;
- `ccb plan` V1 command surface is implemented;
- focused unit and CLI tests pass;
- an external `/home/bfly/yunwei/test_ccb2` smoke creates a ready task packet;
- plan-tree is updated with evidence and remaining open questions;
- no high-frequency runtime event logs are committed to plan-tree.

## Landing Evidence

Current worktree implementation evidence:

- `ccb plan task-create/task-artifact/task-status/task-show/task-list/breadcrumb`
  is implemented through parser, phase2 dispatch, service, and render layers.
- Focused tests live in `test/test_plan_tasks_cli.py`.
- External smoke project:
  `/home/bfly/yunwei/test_ccb2/plan-task-smoke-v1`.
- Smoke result: `smoke-task-001` reached `ready` only after review was
  imported; `breadcrumb` produced the compact runtime handoff text.
- The smoke used `/home/bfly/yunwei/ccb_source/ccb_test` from
  `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME`.
