# Single-Lane R1 Authority Runtime Closure

Date: 2026-07-11
Branch: `workflow/agentic-loop-topology`
Commit: `0c2f19ef`
Status: Accepted by direct `talk2` source review and validation

## Scope Closed

R1 closes the F1 source authority envelope and the generalized one-node G1
kernel. It does not execute multi-node bundles yet.

- Task records now carry a monotonic semantic `task_revision`; managed role
  output is fenced against stale semantic activations under the task lock.
- Effective capacity is canonicalized as
  `ccb.loop.effective_capacity_snapshot.v1` and bound into normalized bundle
  authority by digest.
- Bundle provenance is artifact metadata rather than semantic bundle content.
- Candidate selection records complexity, cutability, execution shape,
  rationale, and an adaptive one-to-four workgroup count.
- Config V2 retains deterministic one-node omission compatibility; its
  compatibility bundle revision is replay-safe and advances after semantic
  replan. Config V3 omission is rejected before semantic import.
- One-node execution now reads node-map authority and canonical work packets.
  Scalar fields remain compatibility projections only.
- Ask intent identity is `(bundle_revision, node_id, purpose, attempt)` with
  append-only `prepared -> accepted -> terminal -> consumed` evidence and an
  explicit non-retriable `unknown` state.
- Concurrent direct `runner --once` calls serialize the intent check and
  daemon submission, preventing duplicate node asks.
- Worker, reviewer, rework, and round-review activations require proven
  immaculate freshness. Orchestrator and task-detailer activation likewise
  stop before provider submission when clear evidence is not `cleared`.
- The normal pass path no longer asks an orchestrator after worker completion.
  Structural replan remains the only reason for a fresh orchestrator.

## Defects Exposed During Direct Review

The initial worker result passed its focused tests but was not accepted as-is.
Direct diff and failure-path review found and fixed:

1. provider-controlled `parallel_group` labels could bypass the real DAG
   parallel-capacity limit;
2. managed role imports checked revision before writes but did not carry CAS
   through every authoritative mutation;
3. Config V3 missing-candidate handling could import orchestration notes before
   blocking;
4. two concurrent `--once` callers could both pass the intent check and submit
   the same ask;
5. failed provider clear was recorded but execution continued with polluted
   immaculate context;
6. V2 structural replan regenerated bundle revision 1 and conflicted with the
   prior bundle;
7. the orchestrator activation prompt still described the pre-F1 schema and
   biased selection with a concrete one-group example;
8. byte-identical idempotence had accidentally expanded to non-semantic
   evidence artifacts, which would discard new actor/job/import traceability.

## Direct Verification

- `py_compile` for all nine touched source/test files: passed.
- Owned R1 suite: `195 passed`.
- Adjacent topology/frontdesk/workflow/ask/question suite: `117 passed`.
- Full repository run: `4000 passed, 2 skipped, 5 failed`.
  - Four failures are Gemini provider-blackbox restart timing cases. Gemini is
    explicitly outside this release gate.
  - The remaining failure is a stale Phase 6B history assertion requiring the
    consumed repeat8 root in active status docs. It reproduces unchanged on
    parent commit `ec01d53a` and is not caused by R1.
- `git diff --check` and the new-file whitespace check: passed.

## Remaining Gates

- Multi-node bundles still pause before bind and provider asks.
- Config V3 parsing/validation and the V3 capacity compiler are not landed.
- RolePack projections still need the final adaptive candidate contract.
- Git node worktrees, reviewed commits, deterministic integration, promotion,
  rollback, ready-frontier scheduling, per-node lifecycle, and B7 aggregation
  remain Wave 2/3 work.
- Physical peak capacity must include dynamic control-role overlap when T1
  freezes the concrete topology schedule.
- No real-provider one-to-four workgroup claim is made by this checkpoint.
