# Phase 6B Repeat8 Direct-Execution Failure Note

Date: 2026-07-05
Status: SUPERVISOR NOTE / NO LAUNCH APPROVAL / PHASE 6B UNCLAIMED

## Scope

This note records the supervisor diagnosis from the consumed L1-L4 repeat8
run. It is input for the next source repair and reviewer gate. It is not a
runtime approval request and does not change the repeat8 B7 result.

Repeat8 evidence:

- Runtime root:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`
- B7 report:
  [../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md)
- B7 status: `not_claimable`
- Cleanup: post-B7 `kill` returned `kill_status: ok`, `state: unmounted`

## Finding

L1 and L2 direct-execution work succeeded only inside loop-owned copy
workspaces. The main lab project remained unchanged:

- `lab_docs/l1_release_note.md` still has `status: draft` and `summary: TBD`.
- `lab_code/calculator.py` still returns `a - b`.
- The supervisor L2 test resolution ran from the lab project root, resolved
  lab-local `tests/test_calculator.py`, and failed with `AssertionError: -1 !=
  5`.

The provider evidence confirms the split:

- L1 `ccb_round_reviewer-reply.md` says the worker workspace has the correct
  file and explicitly notes the main lab seed file remains unchanged.
- L1 round reviewer states: "In the CCB workspace model, this is expected -
  workspaces are isolated and the workspace artifact is authoritative for the
  loop. No contract clause requires the worker to sync back to the seed
  directory."
- L2 worker/reviewer evidence similarly verifies success inside
  `.ccb/workspaces/loop-...-coder-1`, not in the lab project root.

## Acceptance Implication

The next repair cannot be only a B7 normalizer tweak. It must settle and
enforce the direct-execution landing semantics:

1. If Phase 6B requires direct execution to change the task project, the
   ask-first runner must apply or promote accepted worker workspace changes to
   the project before importing `round_summary:pass`, and it must verify the
   expected files/tests from the project root.
2. If the intended authority is instead the worker copy workspace artifact, the
   launch packet, B7 schema, task contracts, and final acceptance goal must say
   that explicitly. The current repeat8 packet did not say that, and its
   supervisor-side L2 project-root test failed.

For the current Phase 6B goal, treat repeat8 L1/L2 as blocking until reviewer2
accepts a source repair or an explicit owner-approved semantic change.

## Repair Acceptance Checklist

Before requesting another L1-L4 real-provider run, the repair package should
prove all of the following without consuming a launch approval:

- A direct-execution pass cannot be imported when the expected project-root
  file effects are absent.
- For copy-workspace workers, accepted changes are either applied to the
  project root through a script-owned path or rejected as non-landed evidence.
- L2-style tests are run or checked from the authority location that the B7
  row claims. If the row claims project-root completion, the test must pass
  from the project root.
- Round reviewer/provider text remains evidence only; it cannot redefine
  authority from project-root evidence to workspace-artifact evidence.
- Failure cleanup still releases dynamic topology and does not strand
  `running/current_loop` tasks.
- Existing bounded non-success routes remain intact:
  `needs_detail`, `macro_adjustment_request`, and `blocked` must not be
  converted into fake direct-execution pass paths.

## Current Evidence Reuse

Repeat8 L3 and L4 rows remain useful bounded evidence:

- L3 `needs_detail` reached the detail checkpoint with no post-detail
  execution.
- L4 `macro_adjustment_request` and `blocked` produced script-owned terminal
  evidence.

They do not make the L1-L4 tranche claimable because L1/L2 direct-execution
rows failed.
