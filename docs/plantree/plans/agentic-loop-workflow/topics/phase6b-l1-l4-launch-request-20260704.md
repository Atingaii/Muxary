# Phase 6B L1-L4 Launch Request Historical Record

Date: 2026-07-04
Status: REPEAT8 CONSUMED HISTORICAL RECORD / DO NOT RUN / NO ACTIVE L1-L4 LAUNCH REQUEST / PHASE 6B UNCLAIMED

## Purpose

This topic is now a non-runnable historical record for the consumed Phase 6B
L1-L4 repeat8 lane. It preserves the evidence trail and cleanup state, and it
records the gates that must close before any future sequence9 launch request can
be prepared.

This file is not an approval-to-run request. It intentionally contains no
executable command block, no B7 normalizer command, and no active repeat8 or
sequence9 runtime shape. Any future sequence9 request must be created in a
separate active request file after the source repair gate is accepted, for
example:

```text
docs/plantree/plans/agentic-loop-workflow/topics/phase6b-l1-l4-launch-request-sequence9-20260704.md
```

No source-wrapper, `ccb_test`, provider, L1-L4, L5, B7, cleanup, or runtime
command is authorized by this document.

## Evidence References

- Phase 1-6 acceptance goal:
  [../goals/phase1-6-acceptance-goal.zh.md](../goals/phase1-6-acceptance-goal.zh.md)
- Phase 6 real-provider task-pack catalog:
  [phase6-real-provider-lab-task-packs.md](phase6-real-provider-lab-task-packs.md)
- Phase 6B launch checklist:
  [phase6b-real-provider-lab-launch-checklist.md](phase6b-real-provider-lab-launch-checklist.md)
- L1-L4 planning package acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_b9eac0af0f9e-art_973372060e54411a.txt`
- Static hardening acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f20daf37898d-art_82078d731cc04aa7.txt`
- Repeat8 approval, now consumed:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_05e6f1c57f3c-art_ef78db3a28f64e07.txt`
- Repeat8 reapproval blocker:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_04b5c2faa2f2-art_3e18d57b3d08411a.txt`
- Effective repeat8 non-fresh-root blocker:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_311550b109ec-art_6729ef2967a04132.txt`
- Repeat8 B7 report:
  [../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md)
- Repeat8 direct-execution diagnosis:
  [phase6b-repeat8-direct-execution-failure-note.md](phase6b-repeat8-direct-execution-failure-note.md)
- Prior reviewer1 source authority blocker:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_1ebb25b249ba-art_5a1d3267af214108.txt`
- Reviewer1 source re-audit acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_b4184497742b-art_965b03f80b204538.txt`

## Historical Roots

Consumed, non-reusable L1-L4 roots:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence4-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence5-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence6-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence7-20260704
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704
```

Repeat8 used:

```text
root: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704
B7: docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md
Status: not_claimable
cleanup: complete, state=unmounted
```

Sequence8 must not be reapproved or reused.

## Repeat8 Result

Repeat8 was approved by reviewer2 in `job_05e6f1c57f3c` and consumed exactly
once by talk2 from the sequence8 root. The B7 report is `not_claimable`.

Observed result summary:

- L1 and L2 reached `done/pass` authority, but the lab project root did not
  contain the expected file changes.
- L2's lab-local unittest evidence resolved the intended test file but failed.
- Provider/reviewer evidence showed the worker changes existed only in copy
  workspaces.
- L3 `needs_detail`, L4 `macro_adjustment_request`, and L4 `blocked` produced
  bounded non-success evidence, but the overall tranche remains non-claimable
  because L1/L2 direct execution was not valid.
- Post-B7 cleanup completed and unmounted the project.

The diagnosis is recorded in
[phase6b-repeat8-direct-execution-failure-note.md](phase6b-repeat8-direct-execution-failure-note.md).

## Source Repair Status

Reviewer1 `job_1ebb25b249ba` previously blocked using the then-current source
as the basis for sequence9. Reviewer1 re-audit `job_b4184497742b` now marks the
source-level blockers accepted, including the missing copy-workspace binding
path and project-root test authority path.

Future direct-execution pass evidence must still preserve script-owned
project-root authority:

- valid copy-workspace binding, unless the worker ran in-place;
- promotion from copy workspace to project root;
- verified project-root file changes before importing pass;
- L2 project-root test evidence before importing pass;
- provider/reviewer replies remain evidence only and cannot write authority.

This historical file does not create a sequence9 approval-to-run request. A
future request requires a separate file after talk2 explicitly asks for it and
the source/doc gates are accepted for launch review.

## Future Sequence9 Requirements

After talk2 explicitly asks for a future sequence9 approval packet, a future
worker may create a separate request file for sequence9. That future file must
not reuse this historical topic as the active packet.

Required future request properties:

```text
file: docs/plantree/plans/agentic-loop-workflow/topics/phase6b-l1-l4-launch-request-sequence9-20260704.md
root: /home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704
B7: docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md
scope: L1 direct, L2 direct, L3 needs_detail -> detail_ready, L4 macro, L4 blocked
excluded: L5, reviewer-rework, Phase 6B completion claim
```

Future runtime policy:

```text
HOME: inherited from current system provider environment; do not export lab-local HOME
CCB_SOURCE_HOME: inherited from current system provider environment; do not export lab-local CCB_SOURCE_HOME
AGENT_ROLES_STORE: lab-local under the future sequence9 root
blocked route artifact kind: blocker_evidence
topology: mount-only, no topology_dispatch.json, no communication DSL
authority: script-owned route and round imports only; provider replies are evidence only
```

Before any approved future `init`, talk2 must reconfirm the sequence9 root is
absent.

## Static Cleanup Gate

This cleanup closes the document-side gate requested by reviewer1:

- repeat8 is historical/non-runnable only;
- there is no active repeat8 request shape;
- there is no active sequence9 request in this file;
- no executable repeat8 or sequence9 command block is retained here;
- future sequence9 approval requires a separate file after source/doc gate
  acceptance and a fresh talk2 request.

Reviewer2 may audit this cleanup as `DOC-ONLY ACCEPTED` or `BLOCKER`. Reviewer2
must not grant approval-to-run from this historical record.

## Remaining Gates

- Source/doc gate acceptance cited in the future sequence9 request.
- Future sequence9 active request file prepared only after talk2 explicitly
  asks for it.
- Reviewer2 launch-specific approval-to-run for that future file only.
- Fresh sequence9 root check immediately before any approved `init`.
- Reviewer-gated B7 aggregation before any Phase 6B claim.
