# Phase 6B L1-L4 Repeat9 Supervisor Correction

Date: 2026-07-04
Status: SUPERVISOR OVERRIDE / NOT CLAIMABLE

## Summary

Reviewer1 fallback launch-gate approval `job_c4935017fc15` was consumed exactly
once from:

`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`

The run executed through L1 and L2 only, then talk2 stopped the sequence under
the approved stop-on-failure rule. Post-B7 cleanup returned `kill_status: ok`
and `state: unmounted`.

The generated B7 file
[phase6b-real-provider-l1-l4-repeat9-b7-20260704.md](phase6b-real-provider-l1-l4-repeat9-b7-20260704.md)
currently says `Status: pass`, but that status is rejected by supervisor
evidence and must not be used for a Phase 6B claim.
Phase 6B remains unclaimed.

## Evidence

- L1 completed as expected:
  - task `phase6b-l1-doc-direct-execution`
  - final status `done`
  - round result `pass`
  - project-root file `lab_docs/l1_release_note.md` was updated.
- L2 did not complete as expected:
  - task `phase6b-l2-code-test-direct-execution`
  - task-show final status `blocked`
  - round result `blocked`
  - `round_result_source=isolated_workspace_no_project_root_effect`
  - project-root `lab_code/calculator.py` was updated to `return a + b`
  - a supervisor-created project-root unittest resolution check later passed.
- L3 and both L4 tasks were not started in repeat9.
- The B7 normalizer misread task-show output. It looked for a `record` wrapper,
  but current `ccb_test plan task-show --json` emits top-level task fields and
  a nested `task` object. Missing or blocked task status therefore fell back to
  expected status, producing false `pass`/`valid_non_success` rows.
- The B7 normalizer also emitted rows for unrun L3/L4 tasks by filling expected
  statuses instead of classifying them as missing/not-run evidence.

## Required Repair

Before any future L1-L4 approval packet can be trusted:

- parse task-show JSON from the actual current shape (`status` / `task`) rather
  than only a nonexistent `record` wrapper;
- classify missing task-show evidence or unrun task rows as not claimable;
- never emit overall `Status: pass` unless every required row has observed,
  script-owned evidence for the expected route, status, result, and cleanup;
- add static tests reproducing the repeat9 false-pass shape;
- get reviewer acceptance before preparing any fresh repeat10 root.

Sequence9 is consumed and must not be reused.
