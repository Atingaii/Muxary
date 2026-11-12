# Goal: Planner Role And Plan Update Scripts V1

Date: 2026-06-25

## Objective

Land the first planner-to-plan-tree authority path:

1. Define the V1 planner role boundary.
2. Define and implement the minimal `ccb plan` task packet command surface.
3. Prove planner-style draft artifacts can be imported into durable task
   packets without agents directly writing authoritative status or indexes.
4. Prove required artifacts and review evidence are enforced before `ready`.
5. Validate the full path in `/home/bfly/yunwei/test_ccb2` with
   `/home/bfly/yunwei/ccb_source/ccb_test`.

This goal is not complete until the source-test folder creates a ready task
packet through commands, not by hand-editing plan-tree status files.

## Scope

In scope:

- `agentroles.planner` design and internal `planner + plan_reviewer` shape.
- Minimal `ccb plan` command surface:
  - `task-create`
  - `task-artifact`
  - `task-status`
  - `task-show`
  - `task-list`
  - `breadcrumb`
- Durable task packet layout under
  `docs/plantree/plans/<plan-slug>/tasks/<task-id>/`.
- Machine-owned `tasks/index.json`.
- Artifact import metadata with digest and timestamp.
- Tests for validation, status edges, required artifacts, and path safety.

Out of scope for this goal:

- Full `ccb question` broker implementation.
- Full loop runner integration.
- Multi-plan task routing.
- Automatic plan sync from runtime loop completion.
- Rich sidebar UI for task state.

## Planned V1 Command Contract

```bash
ccb plan task-create --plan <plan-slug> --title "<title>" --json
ccb plan task-artifact --task <task-id> --kind <requirements|acceptance|verification|risk|handoff|review|completion> --file <path> --json
ccb plan task-status --task <task-id> --status <draft|needs_clarification|ready|running|partial|replan_required|done|blocked> --json
ccb plan task-show --task <task-id> --json
ccb plan task-list --plan <plan-slug> --json
ccb plan breadcrumb --task <task-id>
```

## Required Task Packet Files

Before `ready`:

- `requirements.md`
- `acceptance-criteria.md`
- `verification-contract.md`
- `handoff.md`
- `review.md`

Optional before ready:

- `risk-notes.md`

Terminal or partial states may require:

- `completion.md`
- blocker or replan evidence.

## Test Targets

Focused unit tests:

- task id creation;
- index write/read;
- artifact import and sha256 metadata;
- required-artifact enforcement for `ready`;
- valid and invalid status transitions;
- path traversal rejection;
- breadcrumb rendering;
- no writes under `.ccb/runtime` from `ccb plan`.

CLI tests:

- JSON output shape for every V1 command.
- Human breadcrumb output.
- Negative JSON for missing artifacts and invalid status transitions.

External smoke:

```bash
cd /home/bfly/yunwei/test_ccb2
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> plan task-create ...
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> plan task-artifact ...
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> plan task-status --status ready ...
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> plan task-show --json
```

The smoke must run from `/home/bfly/yunwei/test_ccb2`, not from the source
checkout, and it must use the source wrapper, not the installed release
`ccb`.

## Current Status

Implemented in the current worktree and externally smoke-tested.

Done:

- Planner role design documented in
  [../topics/planner-role-design.md](../topics/planner-role-design.md).
- Plan-update script landing shape documented in
  [../topics/plan-update-script-landing.md](../topics/plan-update-script-landing.md).
- Authority decision recorded in
  [../decisions/007-planner-proposes-scripts-write-plan-state.md](../decisions/007-planner-proposes-scripts-write-plan-state.md).
- `ccb plan` commands are mapped into the existing parser, phase2 dispatch,
  service, and render layers.
- Task packet files and machine-owned `tasks/index.json` are written under
  `docs/plantree/plans/<plan-slug>/tasks/`.
- `task-create`, `task-artifact`, `task-status`, `task-show`, `task-list`,
  and `breadcrumb` are implemented.
- `ready` rejects missing `requirements`, `acceptance`, `verification`,
  `handoff`, or `review` artifacts.
- `done` and `blocked` require a `completion` artifact.
- Artifact imports reject files outside the project root and record destination
  path, source path, byte count, sha256, and timestamp.
- `ccb plan` is excluded from bootstrap config creation and provider/daemon
  startup paths.

Validation:

- `python -m py_compile lib/cli/services/plan_tasks.py lib/cli/parser_runtime/commands.py lib/cli/phase2.py test/test_plan_tasks_cli.py`
- `python -m pytest test/test_plan_tasks_cli.py -q` passed: 4 tests.
- `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py -q` passed: 112 tests.
- External smoke project:
  `/home/bfly/yunwei/test_ccb2/plan-task-smoke-v1`.
- External wrapper:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` from
  `/home/bfly/yunwei/test_ccb2`.
- External smoke result: `smoke-task-001` was created, imported
  requirements/acceptance/verification/handoff, rejected `ready` before
  review, imported review, transitioned to `ready`, and returned valid
  `task-show`, `task-list`, and `breadcrumb` output.
- `.ccb` in the smoke project remained an anchor only; no `ccbd` or provider
  runtime directory was created.
- Extended smoke with loop execution:
  `/home/bfly/yunwei/test_ccb2/agentic-loop-full-smoke-v1`.
- Extended smoke result: `full-smoke-task-001` reached `ready`; mounted fake
  providers ran `loopfull2` through worker, reviewer, orchestrator, and
  `round_checker`; dynamic worker/reviewer agents were released; round checker
  evidence was imported as `completion`; task status advanced through
  `running` to `done`.

Remaining:

1. Remove the manual bridge between ready task packet and `ccb loop run-once`;
   the loop runner should read task packet refs and update `current_loop`.
2. Add actor/job-id metadata when plan commands are called from managed agent
   jobs.
3. Add the later broker/question command surface for staged clarification.
