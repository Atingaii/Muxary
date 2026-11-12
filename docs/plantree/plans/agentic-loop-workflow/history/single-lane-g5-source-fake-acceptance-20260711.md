# Single-Lane G5 Source/Fake Acceptance Closure

Date: 2026-07-11
Status: Accepted source/fake runtime acceptance; no live-provider claim
Branch: `workflow/agentic-loop-topology`
Final commit before this record: `b42ec3b2`

## Scope

G5 proves the integrated single-lane scheduler through real source-wrapper
runtime paths with deterministic fake providers. It covers one to four
workgroups, reviewed node progression, R2 integration, root verification,
round review, release, restart replay, failure classification, rollback, and
strict normalized evidence.

This checkpoint is intentionally narrower than G6. It does not claim that
Codex or Claude live providers pass, that a visible opened project has passed,
that Config V3 opened-project behavior is production-ready, or that a packed
candidate installs outside the source checkout.

## Landed Commits

- `5163ad6f`: add the G5 source/fake runtime campaign harness, report schema,
  ten-scenario matrix, external B7/campaign aggregation, and source-wrapper
  coverage.
- `9fceb5de`: quarantine terminal failed workgroups, durably exclude failed
  nodes from R2 integration, restore failed worktrees, and prevent dirty
  terminal nodes from blocking release cleanup.
- `b42ec3b2`: recover valid spilled fake G5 contracts from project-bound ask
  artifacts while rejecting conflicting, unbound, size-drifted, or hash-drifted
  contracts.

## Direct Audit Findings And Repairs

`talk2` rejected an earlier false-clean path where all-failed or exhausted
rework cases left dirty node worktrees and release blockers. The repair records
each terminal failed node as script-owned R2 evidence, preserves any dirty
delta in quarantine, resets the worktree to the node base, marks it `excluded`,
and lets unrelated accepted siblings integrate deterministically.

`talk2` also reproduced a four-node all-failed activation where a large
orchestrator ask spilled into artifact storage and the first compact marker was
malformed. The repair accepts only normalized G5 contracts with the exact
schema, task id, count, shape, selected node, and restart latency fields; it
skips malformed compact text, rejects conflicting valid contracts, and validates
spilled ask artifacts against the explicit project id, project path, byte size,
and SHA256 digest before using them as fake-provider input.

## Campaign Evidence

Final direct campaign root:
`/home/bfly/yunwei/test_ccb2/talk2-g5-final-20260711130355`

Final normalized evidence directory:
`/home/bfly/yunwei/test_ccb2/talk2-g5-final-20260711130355-evidence`

Evidence digests:

- `campaign.json`:
  `4fc6a1eb71ab66004166f78a058bd82f684c74676f59566362ed502821b7dcb7`
- `evidence_rows.jsonl`:
  `66a6d17408a1e3bfaa0a8a3dc9c6ab45283922887bc6a4aca8a6e6dd629bab2d`
- `B7.md`:
  `b228c8a550580d4e1f0e2f72339aeb3972102f4efaeefb9313dd95e83f7ff806`

The campaign schema is `ccb.g5.source_fake_runtime_campaign.v1`, status
`pass`, execution mode `source_fake_runtime`, provider `fake`, row count `10`.
The B7 explicitly records no live or real provider coverage.

Accepted rows:

| Scenario | Classification | Task | Round | Count | Shape |
|---|---|---|---|---:|---|
| `pass` | `pass` | `done` | `pass` | 4 | `mixed_dag` |
| `restart_replay_pass` | `pass` | `done` | `pass` | 2 | `parallel` |
| `reviewer_rework_pass` | `pass` | `done` | `pass` | 1 | `parallel` |
| `reviewer_rework_exhausted_blocked` | `valid_non_success` | `blocked` | `blocked` | 1 | `parallel` |
| `worker_failure_partial` | `valid_non_success` | `partial` | `partial` | 2 | `parallel` |
| `all_workers_failed_blocked` | `valid_non_success` | `blocked` | `blocked` | 4 | `parallel` |
| `reviewer_provider_failure` | `valid_non_success` | `partial` | `partial` | 2 | `parallel` |
| `round_reviewer_blocked` | `valid_non_success` | `blocked` | `blocked` | 4 | `mixed_dag` |
| `integration_verification_failure` | `valid_non_success` | `replan_required` | `replan_required` | 4 | `mixed_dag` |
| `root_verification_failure` | `valid_non_success` | `replan_required` | `replan_required` | 4 | `mixed_dag` |

## Verification

Worker branch pre-integration checks:

- Changed-source `py_compile`: passed.
- Changed-source `pyflakes`: passed.
- `git diff --check e9d10dba..HEAD`: passed.
- `python -m pytest test/test_source_fake_runtime_campaign.py -q`:
  `4 passed`.

Integrated `workflow/agentic-loop-topology` checks after cherry-pick:

- Changed-source `py_compile`: passed.
- Changed-source `pyflakes`: passed.
- `git diff --check HEAD~3..HEAD`: passed.
- `python -m pytest test/test_single_lane_multi_workgroup_smoke.py -q`:
  `37 passed in 312.29s`.
- `python -m pytest test/test_source_fake_runtime_campaign.py test/test_multi_workgroup_scheduler.py test/test_workgroup_git_integration.py test/test_phase6_fake_matrix_smoke_script.py test/test_workflow_closure_smoke_script.py -q`:
  `126 passed in 17.13s`.
- Narrow socket scans under `/tmp/pytest-of-bfly` and
  `/home/bfly/yunwei/test_ccb2` for G5/talk2-G5 roots returned no socket
  residue.
- Process scan for G5/source-fake/single-lane prefixes returned only the scan
  commands themselves, not live G5 runtime processes.
- Full non-provider-blackbox gate after the G5 docs commit:
  `4263 passed, 2 skipped, 21 deselected in 569.98s`.
- Post-full-gate process scan found no current pytest-root runtime processes.
  Five socket files remained under `/tmp/pytest-of-bfly/pytest-6905`, all
  returned `ConnectionRefusedError` and were not connectable runtime services.

## Residual Gates

- G6 must run fresh visible opened projects with inherited real Codex/Claude
  provider configuration and a project-local role store.
- G6 must prove frontdesk-started one-, two-, three-, and four-workgroup
  visible real tasks, actual overlap where applicable, review-before-
  integration, deterministic root output, UI/sidebar evidence, restart/failure
  semantics, busy-retain, and zero final dynamic residue.
- G7 must freeze a packed candidate, install it outside the source checkout,
  run update/rollback smoke, and produce deployment-readiness evidence.
- Publication remains G8 and requires explicit user authorization.
