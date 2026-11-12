# Single-Lane Multi-Workgroup G1 Foundation Evidence

Date: 2026-07-10
Status: Foundation landed; G1 not complete
Commit: `34027943` (`feat(workflow): add orchestration bundle foundation`)

## Scope Landed

- Added strict candidate and normalized orchestration-bundle parsing for one
  to four workgroups.
- Added script-owned `plan task-artifact --kind orchestration_bundle` import,
  task locking, canonical work-packet materialization, provenance metadata,
  idempotent replay, and conflicting-import rejection.
- Validated task binding, imported artifact references, profiles, DAG shape,
  canonical node order, integration order, path safety, parallel scope
  overlap, work-packet digests, normalized bundle digest, and task-input
  digest.
- Added explicit orchestrator fenced-candidate import. A missing candidate on
  the legacy one-workgroup path creates an auditable compatibility bundle
  rather than an unrecorded scalar route.
- Added canonical `nodes.node-001` state alongside the temporary legacy scalar
  mirror in pending and final ask-first evidence.
- Added a hard runner boundary for bundles with more than one node: the runner
  pauses before task binding, ask submission, or execution until the
  multi-workgroup scheduler lands.

## Defects Exposed And Fixed

1. The fenced-section parser accepted a heading without a colon while the
   bundle detector required `orchestration_bundle:`. A valid provider bundle
   therefore could never be consumed. The parser now accepts the optional
   colon and has end-to-end completion-snapshot coverage.
2. A conflicting bundle candidate could write canonical work-packet files
   before conflict rejection. Conflict detection now happens under the task
   lock before packet writes; tests prove the accepted packet remains
   unchanged.
3. Load-time normalized-bundle validation was weaker than import-time
   validation. The loader now rechecks all canonical node fields, profiles,
   references, scopes, digests, order, integration, and policy.
4. Provider node order previously changed the normalized digest. Nodes and
   semantic lists are now normalized deterministically.

## Direct Verification

- `python -m py_compile` on all touched workflow services and tests: passed.
- Bundle/plan/loop/topology focused and adjacent suite: `209 passed`.
- Full repository run: `3988 passed, 2 skipped, 4 failed`. All four failures
  are existing Gemini restart-timing blackbox cases; they either completed
  before the test observed an intermediate running preview or reported
  `runtime_unavailable`. They do not call the changed workflow bundle path.
- Current release gate excluding Gemini, as required by the active provider
  policy: `3868 passed, 2 skipped, 124 deselected`.
- `git diff --check`: passed before commit.

## Deliberate Non-Claims

This checkpoint does not execute multiple workgroups and is not a release or
deployment-readiness claim. The following remain open:

- finish the complete V1 authority envelope, including task revision and
  effective capacity snapshot/digest binding;
- make the one-node path consume node-scoped work packets and node-keyed
  submission intents as its sole internal state, then remove the scalar mirror;
- remove the normal post-worker orchestrator call; allow a fresh orchestrator
  only for structural replan;
- implement clean-Git/node-worktree review and deterministic integration;
- implement ready-frontier fanout, per-node recovery/rework/results, generalized
  topology/capacity/release, Config V3, fake-provider 2/3/4 flows, and visible
  real-provider acceptance.

## Next Gate

Complete the remaining G1 one-node generalization before starting G2/G3. The
authoritative design and test matrix remain:

- [../goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md)
- [../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md)
- [../decisions/025-single-lane-multi-workgroup-release-gate.md](../decisions/025-single-lane-multi-workgroup-release-gate.md)
