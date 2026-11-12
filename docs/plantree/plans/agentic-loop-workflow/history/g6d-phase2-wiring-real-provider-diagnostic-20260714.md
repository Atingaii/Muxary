# G6D Phase2 Wiring And Real-Provider Diagnostic

Date: 2026-07-14
Status: repair and broadened regression gate accepted
Repair commit: `62753d63791f8b644ee6f5f5433fe57070fb2c84`

## Admission Baseline

The visible lanes started from clean source `c725b56f`, using the absolute
source wrapper `/home/bfly/yunwei/ccb_source/ccb_test`, external projects under
`/home/bfly/yunwei/test_ccb2`, Config V3, project-local Role stores, inherited
real provider state, and no `CCB_SOURCE_RUNTIME_OK` override.

The accepted deterministic callback fixture was:

`/home/bfly/yunwei/test_ccb2/source-callback-fixture-c725-20260714T110602Z`

It covered exact active-job anchors after session rotation, changed cwd,
partial/subagent/duplicate rejection, two managed roots, the 181-second
delivery guard, non-empty completion artifacts, and zero cleanup residue.

## Rejected C1 Codex Lane

Evidence root:

`/home/bfly/yunwei/test_ccb2/real-provider-visible-c1-codex-20260714T112158Z`

- Real provider/model: Codex `gpt-5.4`, inherited profile, high thinking.
- Frontdesk `job_a0fe8d5aa05b` completed and performed the silent Planner
  handoff.
- Planner `job_823bbc80e411` completed with a 12,344-byte artifact.
- The source-owned auto-runner stopped before Orchestrator activation with:

  `AttributeError: 'types.SimpleNamespace' object has no attribute 'loop_runner_auto'`

No manual `--once` fallback, retry, task import, dynamic activation, or
authority mutation was used after the hard stop.

## Rejected C3 Claude Lane

Evidence root:

`/home/bfly/yunwei/test_ccb2/real-visible-c3-claude-20260714T112344Z`

- Real provider CLI/model: Claude Code `2.1.206`, exact runtime model
  `DeepSeek-V4-pro`, inherited profile.
- Frontdesk `job_8494c5669f17` completed with a 724-byte artifact and performed
  the silent Planner handoff.
- Planner `job_f1c394cdaccd` completed with a 4,943-byte artifact.
- The auto-runner stopped at the same missing production service field before
  any dynamic Role was activated.

The lane proves real Claude Frontdesk/Planner projection and handoff only. It
does not prove the seven-Role C3 matrix.

## Root Cause And Repair

`handle_loop_runner(auto=True)` called `services.loop_runner_auto`, but
`phase2.py::_dispatch_services()` and
`phase2_services.py::build_phase2_dispatch_services()` registered only
`loop_runner_once`.

The same audit found a second production assembly defect in Frontdesk dispatch:
the handler used an eager `getattr` default that evaluated the absent legacy
`frontdesk_intake` field even when `frontdesk_intake_command` was present.

Commit `62753d63` makes both production builders explicitly register:

- `loop_runner_auto`;
- `frontdesk_intake_command`.

The Frontdesk handler now calls the command service directly. That service is
the mounted-project daemon proxy and already owns the no-socket fallback to
the internal intake service.

## Regression Evidence

Implementation evidence root:

`/home/bfly/yunwei/test_ccb2/auto-runner-wiring-job_acf28692264d`

- New wiring tests before the repair: `3 failed`.
- Phase2 wiring and neighboring entrypoints after the repair: `5 passed`.
- Nearby loop-runner/Frontdesk service tests: `16 passed`.
- Multi-workgroup auto-runner tests: `5 passed`.
- Public `loop runner --auto --max-steps 1 --json`: exit `0`, bounded `idle`,
  `auto_runner_finished`, and no `AttributeError`.

The first broadened Phase2 run at
`/home/bfly/yunwei/test_ccb2/phase2-wiring-gate-62753d63-20260714T114127Z`
is retained as rejected evidence. Its 19 pane/adapter failures used a long
`XDG_RUNTIME_DIR`; the log contains repeated `AF_UNIX path too long` failures.
The full loop-capacity, multi-workgroup, task-set, and public auto-runner rows
in that run passed. The short-path rerun at
`/home/bfly/yunwei/test_ccb2/phase2-short-gate-62753d63-20260714T115135Z`
then passed all 83 Phase2 tests; it was retained as non-final because `main`
advanced during execution.

The immutable rerun pinned detached HEAD `123ee43c` at
`/home/bfly/yunwei/ccb_worktrees/phase2-gate-123ee43c-job_2bc8203d0954`.
Only PlanTree files differ between `62753d63` and `123ee43c`. Its evidence root
`/home/bfly/yunwei/test_ccb2/phase2-pinned-gate-123ee43c-20260714T115921Z`
records `83 passed in 246.93s`, exit zero, fixed HEAD before and after, short
isolated HOME/XDG/basetemp paths, and zero test-owned residue. This accepts the
Phase2 wiring regression surface when combined with the same-code loop
capacity `256 passed`, scheduler `92 passed`, task-set `17 passed`, and public
auto-runner exit-zero/idle evidence.

## Cleanup

Both rejected real-provider projects were inspected while open. Each had only
Frontdesk and Planner resident, no dynamic agent, no node worktree, and no live
auto-runner. Each was then force-unmounted with its project-local Role store
and source `ccb_test`.

Post-cleanup audits found zero project-owned keeper, ccbd, provider, bridge,
sidebar, tmux, listener, socket, auto-runner, and active mount residue. Raw
audit evidence remains under each lane's `evidence/talk2-audit` directory.

## Claim Boundary

This checkpoint accepts the root cause, minimal repair, broadened Phase2 gate,
and rejected-lane cleanup. It does not accept Planner provider permission
enforcement, fresh C1/C2/C3, weak-model repeatability, installed-candidate
behavior, publication, or tagging. The next blocker is recorded in the G6E
Planner readless diagnostic.
