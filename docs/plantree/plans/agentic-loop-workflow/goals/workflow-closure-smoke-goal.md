# Workflow Closure Smoke Goal

Date: 2026-06-27

## Objective

Turn the previously manual workflow-loop evidence into a repeatable
source-wrapper smoke:

```text
frontdesk/user macro task
  -> planner activation
  -> candidate questions
  -> broker/frontdesk clarification artifacts
  -> normalized answers
  -> planner artifact imports
  -> plan reviewer activation and review gate
  -> ready execution bridge
  -> dynamic worker + checker round
  -> round_checker evidence import
  -> release --policy auto cleanup
```

The smoke must keep the program kernel simple: scripts own schemas, path
safety, status transitions, locks, and capacity release; role intelligence is
represented by imported artifacts and fake-provider asks.

## Landed Slice

- Added `ccb loop capacity release --policy auto` while preserving legacy
  `--idle-only`.
- Updated `loop_run_once` to call release with `policy='auto'`.
- Preserved `release_policy` and `idle_only` in `round.json` capacity summaries
  so closure evidence can prove which release policy was used.
- Added `scripts/workflow_closure_smoke.py`, a deterministic fake-provider
  source-wrapper smoke that prepares an isolated project in
  `/home/bfly/yunwei/test_ccb2`, installs local workflow RolePacks into a
  project-local role store, drives `ccb plan`, `ccb question`, and
  `ccb loop runner --once`, then kills the project.
- Added `test/test_workflow_closure_smoke_script.py` for script config,
  project preparation, command sequence, review gate, and auto-release summary.
- Updated local and external `agentroles.ccb_orchestrator` guidance to use
  `ccb loop capacity release --loop-id <id> --policy auto --json`.

## Verification

Focused source tests:

```bash
PYTHONPATH=lib pytest -q \
  test/test_loop_capacity_cli.py \
  test/test_workflow_closure_smoke_script.py \
  test/test_orchestrator_rolepack.py \
  test/test_orchestrator_capacity_semantic_smoke_script.py
# 35 passed
```

Compile and whitespace checks:

```bash
PYTHONPATH=lib python -m py_compile \
  lib/cli/services/loop_capacity.py \
  lib/cli/services/loop_run_once.py \
  scripts/workflow_closure_smoke.py \
  test/test_workflow_closure_smoke_script.py \
  test/test_loop_capacity_cli.py
# passed

git diff --check
# passed
```

External Agent Roles spec focused tests after the orchestrator skill update:

```bash
cd /home/bfly/yunwei/agent-roles-spec
python -m pytest -q tests/test_ccb_orchestrator_role.py tests/test_ccb_workflow_roles.py
# 5 passed
```

Real source-wrapper smoke:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
python /home/bfly/yunwei/ccb_source/scripts/workflow_closure_smoke.py \
  --test-root /home/bfly/yunwei/test_ccb2 \
  --project-name workflow-closure-smoke-178255c \
  --ccb-test /home/bfly/yunwei/ccb_source/ccb_test \
  --reset --run --json
```

Result:

```text
workflow_smoke_status: ok
project: /home/bfly/yunwei/test_ccb2/workflow-closure-smoke-178255c
final_status: blocked
round_result: blocked
round_result_source: missing_round_checker_result
release_policy: auto
retained_count: 0
dynamic_agents_absent_from_ps: true
```

The terminal `blocked` status is intentional for the fake-provider smoke:
scripts must not infer `pass` from a generic fake `round_checker` reply when
no machine-readable `round result: pass` line exists.

Latest layout-cleanup rerun:

```text
project: /home/bfly/yunwei/test_ccb2/workflow-closure-layout-1782571
workflow_smoke_status: ok
release_policy: auto
release_status: released
retained_count: 0
dynamic_agents_absent_from_ps: true
```

This rerun adds evidence for the dynamic window/pane work: generated worker
and checker agents are removed from runtime layout and `ps` state after the
auto-release step, while the fake-provider terminal `blocked` result remains
the expected round-checker artifact guard.

## Implementation Finding

The first smoke draft used explicit `[windows]` topology with all workflow
roles in one window. That exposed a follow-up risk: current loop-capacity
generated agents are more reliable through compact layout overlays, while
explicit windows need additional runtime window-placement work before they
become the default workflow smoke topology. The closure smoke therefore uses
compact layout plus role overlays for this slice.

Follow-up belongs under
[../topics/dynamic-window-pane-agent-maintenance.md](../topics/dynamic-window-pane-agent-maintenance.md):
make loop-generated execution nodes work cleanly with explicit workflow
windows, especially `frontdesk-dialog`, `plan-orchestrate`, and per-node
execution windows.
