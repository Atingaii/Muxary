# G6C Root14 Orchestrator Fence Diagnostic

Date: 2026-07-13
Status: rejected real-provider acceptance; source blockers later closed
Phase: G6C / Decision 029 P5
Read when: reviewing the Orchestrator output contract or preparing root15

## Accepted Preconditions

- Source head included the bounded `detail_ready` terminal constraint,
  fail-closed importer settlement, Planner RolePack alignment, strict B7
  authority checks, restart/idempotence coverage, and the Gemini ccbd-restart
  repair.
- The current source suite passed `4792` tests with `2` skipped before launch.
- The fresh project used the source worktree's explicit `ccb_test`, inherited
  real provider environment, a root-local Role store, and five visible idle
  resident panes.
- The generated Frontdesk request contained all five route/terminal pairs,
  `git_repository=not_guaranteed`, repo-independent verification rules, and
  controller-owned B7 and cleanup boundaries.

## Preserved Root14 Evidence

Root:
`/home/bfly/yunwei/test_ccb2/deploy-g6c-real-talk2-20260713-14`

Frontdesk job `job_67533c6a7251` completed with exact Intake Evidence. Its
direct Planner handoff transaction committed with
`controller_rewrote_body=false`. Planner job `job_0499358eca35` returned and
imported exactly five required child tasks under task set
`ts-e9c056b28f8262225a56:r1`; no extra bounded child was created and all
verification commands were repo-independent.

L1 completed `done/pass` through a real dynamic Coder, Code Reviewer, and
Round Reviewer chain. Direct content verification passed, the only project
artifact was `docs/phase6b-l1-doc-direct-execution.md`, and the dynamic pair
was released.

L2 Orchestrator job `job_0d271968fceb` returned a semantically valid one-node
direct-execution bundle, but used
````text
```ccb.loop.orchestration_bundle_candidate.v1
```
````
as the code-fence language. The importer correctly rejected it with
`orchestrator_reply_bundle_requires_fenced_json`; the L2 task remained
`ready_for_orchestration` and no Worker was submitted.

## Root Cause And Repair Boundary

The Orchestrator template uses a literal `json` fence and the runner asks for
fenced JSON, but the RolePack memory describes a fenced
`ccb.loop.orchestration_bundle_candidate.v1`. The real model interpreted the
schema name as the fence language. The importer fail-closed boundary is
correct and must not gain a permissive parser or fallback.

The RolePack repair must state unambiguously that:

- the heading is exactly `orchestration_bundle:`;
- the following code-fence language is literally `json`;
- `ccb.loop.orchestration_bundle_candidate.v1` appears only as the JSON
  object's `schema` value, never as the fence language.

The run also exposed a harness recovery defect. A failed precondition can
consume a fixed read-only observation label; after the precondition is
repaired, replay collides with `evidence_integrity_duplicate_label`. Recovery
may make read-only observation idempotent, but mutating authority, provider
submission, B7, and cleanup labels must remain duplicate fail-closed.

## Root15 Gates

- Land the RolePack contract repair through `mother` with projection tests
  covering the literal `json` fence and rejecting schema-as-fence wording.
- Land the harness recovery repair with failure-then-replay coverage and no
  duplicate provider submission or relaxed mutating-label integrity.
- Pass focused RolePack, importer, harness, static, and current-source full
  gates before creating a fresh root15.
- Root15 must rerun the entire Frontdesk-to-closure workflow. Root14 L1
  evidence cannot be carried forward as a root15 pass.
- Root15 must prove the L3 terminal constraint and settlement, all five route
  terminals, task-set closure, Planner backfill, Frontdesk delivery, strict
  B7, dynamic release, auto-runner exit, shutdown, and zero runtime residue.

## Cleanup

The pending-authority guard passed. The rejected project was then unmounted
with `kill_status: ok`, all five resident agents reported `stopped`, and no
project process remained. Evidence was preserved; no false B7 pass was
generated.

## Post-Repair Source Gate

The literal-`json` RolePack repair, bounded read-only harness recovery, and
exact schema-as-fence controller regression landed through `3a4b41da`.
Focused RolePack, harness, document, and loop-controller gates passed.

Root15 was still forbidden at this checkpoint. Two complete
`test/test_single_lane_multi_workgroup_smoke.py` runs passed only `37/39` and
`38/39`. The unstable rows are the reviewer-rework scenarios; observed failed
checks include `rework_exactly_once` and, in one run, release, dynamic-agent,
and child-worktree residue. A targeted two-case rerun passed, which is evidence
of non-determinism rather than acceptance. The race or cross-scenario state
leak must be reproduced, repaired, and retested before the full source gate.

Persistent fresh-root evidence narrowed this to a scheduler authority error,
not cross-scenario contamination. The first Worker-owned Reviewer chain
returns `rework_required` and its callback continuation completes, but the
original Worker job is already terminal. The scheduler then tries a second
`ask --chain ... reviewer from worker`; CCB correctly rejects it because that
sender has no active parent job. On the failing path the round records
`rework_count=0`, no Worker-rework job, no Reviewer recheck, and
`review_chain_final_rework_required`. The runtime must create a fresh
Worker-rework parent job before the second Reviewer chain; the smoke harness
must not manufacture or bypass that authority.

## Later Closure

The authority and cleanup blockers were closed through `b14c66ef`. The final
source suite and external live-residue audit passed on 2026-07-14, admitting a
fresh root15 without reclassifying root14 itself as accepted evidence. See
[g6c-source-gate-and-root15-readiness-20260714.md](g6c-source-gate-and-root15-readiness-20260714.md).
