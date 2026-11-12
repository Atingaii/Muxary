# Phase 6B Real-Provider Claim Coverage Matrix

Date: 2026-07-04
Status: FINAL AGGREGATION ACCEPTED / NOT PRODUCTION ENABLEMENT

## Purpose

This matrix maps the Phase 6B claim requirements from the
[Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md) to the
current evidence state. It is a `talk2` supervision aid, not permission to run
a provider command. As of 2026-07-05, it records the bounded Phase 6B final
aggregation verdict for initial real-provider, single-round capability.

## Current Boundary

- Phase 6A is accepted only for the fake-provider, single-round,
  source-wrapper program-matrix scope.
- Phase 6B is claimable for initial real-provider, single-round capability
  after `talk2` final aggregation on 2026-07-05, per the user's instruction to
  stop using reviewer gates for this final aggregation.
- L0 B-only repeat6 passed runtime sanity and consumed its one-run approval.
- L1-L4 repeat8 approval `job_05e6f1c57f3c` was consumed exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`.
  B7 is
  [phase6b-real-provider-l1-l4-repeat8-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md)
  with `Status: not_claimable`: L1/L2 classify as `test_design_failure`, L3
  and both L4 terminal routes classify as `valid_non_success`, and cleanup
  returned `kill_status: ok`, `state: unmounted`. Reviewer2
  `job_04b5c2faa2f2` blocks repeat8 reapproval because sequence8 is now
  non-fresh.
- Repeat8 direct-execution diagnosis is tracked in
  [phase6b-repeat8-direct-execution-failure-note.md](phase6b-repeat8-direct-execution-failure-note.md):
  L1/L2 providers validated copy-workspace changes, while project-root
  evidence stayed unchanged.
- Reviewer2 `job_311550b109ec` blocked repeat8 reapproval because sequence8 is
  non-fresh. The dated L1-L4 launch request topic is now repeat8 historical
  only, with no executable command block. Reviewer1 re-audit
  `job_b4184497742b` marked the source-level blockers accepted, and talk2
  requested a separate active sequence9 packet:
  [phase6b-l1-l4-launch-request-sequence9-20260704.md](phase6b-l1-l4-launch-request-sequence9-20260704.md).
  Reviewer1 fallback launch-gate re-audit `job_c4935017fc15` approved exactly
  one sequence9 run for
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`.
  Talk2 consumed that approval once. L1 reached `done/pass`; L2 reached a
  blocked round with `round_result_source=isolated_workspace_no_project_root_effect`
  even though the project-root file and a supervisor-created unittest
  resolution check later passed. L3/L4 were not run. Generated repeat9 B7
  [phase6b-real-provider-l1-l4-repeat9-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md)
  says `Status: pass`, but this is rejected as a normalizer false-positive by
  [phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md](../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md).
  Sequence9 is consumed/non-reusable and no repeat9 evidence is claimable.
  Worker1 `job_dd20a18926e1` prepared a fresh sequence10 repair/launch packet
  at
  [phase6b-l1-l4-launch-request-sequence10-20260704.md](phase6b-l1-l4-launch-request-sequence10-20260704.md)
  for root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence10-20260704`
  and planned B7 path
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md`.
  Reviewer1 fallback launch gate `job_bfe386ae7a9f` granted exactly one
  sequence10 run after reviewer2 `job_0d07e67ef312` remained queued. Talk2
  consumed sequence10 once: L1 direct execution stopped as `blocked` because the
  round reviewer found worker changes only in the loop copy workspace while the
  main project `lab_docs/l1_release_note.md` stayed draft/TBD. L2/L3/L4 were
  not run. Repeat10 B7
  [phase6b-real-provider-l1-l4-repeat10-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md)
  is `Status: not_claimable`; cleanup succeeded. At that point, the Phase 6B
  claim remained blocked.
  Worker1 source repair `job_e2ff663087be` now stages allowed isolated-worker
  deltas into the project root before direct-execution reviewer/final
  validation and rolls them back on non-pass/unknown/test-failure outcomes.
  This closes the sequence10 fake-success source path for future reviewer-gated
  runs only; no new real-provider or B7 evidence was generated. Reviewer1
  accepted the repair in `job_a7e62fee5496`, and talk2 local verification after
  review passed the focused `py_compile` plus `89 passed` pytest bundle.
  Worker3 `job_1cfa66b23752` prepared the L1-L4 sequence11 approval packet
  [phase6b-l1-l4-launch-request-sequence11-20260704.md](phase6b-l1-l4-launch-request-sequence11-20260704.md)
  for root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence11-20260704`
  and B7 path
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat11-b7-20260704.md`.
  Reviewer1 approved one run; talk2 consumed it once. Sequence11 is now
  historical/non-reusable. Worker3 `job_cf01392dc751` prepared the active next
  L1-L4 sequence12 packet at
  [phase6b-l1-l4-launch-request-sequence12-20260705.md](phase6b-l1-l4-launch-request-sequence12-20260705.md)
  for root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`
  and B7 path
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md`.
  Reviewer1 fallback `job_454bdb9b36f1` returned `APPROVAL BLOCKED` because
  reviewer1 was not an acceptable substitute launch gate for that packet; it
  confirmed the root and B7 path were absent. Talk2 submitted self-contained
  reviewer2 request `job_a047b32d275c`; no completion artifact is visible. On
  2026-07-05 the user instructed talk2 to stop using reviewers for this gate.
  Talk2 then self-reviewed the exact command shape, confirmed the root and B7
  path were absent, and consumed sequence12 exactly once. B7
  [phase6b-real-provider-l1-l4-repeat12-b7-20260705.md](../history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md)
  is `Status: pass`: L1/L2 are `pass`; L3 `needs_detail`, L4
  `macro_adjustment_request`, and L4 `blocked` are `valid_non_success`; all
  rows are claimable. Cleanup returned `kill_status: ok`, `state: unmounted`.
- Repeat6 B7 is [phase6b-real-provider-l1-l4-repeat6-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat6-b7-20260704.md);
  repeat6 B7 [phase6b-real-provider-l1-l4-repeat6-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat6-b7-20260704.md)
  remains historical and non-claimable.
- The L1-L4 frozen launch request was `DOC-ONLY ACCEPTED` by reviewer2
  `job_c0fac249749e`. A later launch-specific approval-to-run was granted by
  reviewer2 `job_d44bf15c6cb1`, but talk2 held execution before consuming it
  because the frozen script had no approved continuation path after the first
  supervisor checkpoint. Reviewer2 then granted repaired checkpoint/resume
  approval in `job_7800c403f864`; talk2 consumed it once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704`, and
  the run stopped before provider ask activation because the driver did not
  materialize `docs/plantree/plans/phase6b-real-provider-l1-l4` before
  `plan task-create`. That approval/root are historical and not runnable.
  Repeat2 approval `job_0c8596e0895d` was also consumed once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704`; it
  proved the plan-root repair through L1 orchestrator activation but failed
  before direct execution because an outer-root supervisor artifact was passed
  to `plan task-artifact --file`.
- Reviewer1 read-only audit `job_34d57ea11c3a` returned `COVERAGE OK`: no new
  immediate lane is needed.
- Worker1 callback `job_307d5f834a1a` closed the declared task-specific B7
  normalizer field drift; reviewer2 accepted it in `job_d023a883a62d`. The
  follow-up static hardening lane `job_82d723ec0f89` emits conservative
  `authority_checks.*` output in the embedded L1-L4 normalizer; reviewer2
  accepted it in `job_f20daf37898d` as static hardening only.
- Worker2 callback `job_e6456cf4a072` provided the L5
  reviewer-rework/partial observation tranche; reviewer2 accepted it in
  `job_3824dde8454e` as plan-only readiness, not launch approval. The follow-up
  static hardening lane adds a reviewable embedded L5 normalizer shape;
  reviewer2 accepted that shape in `job_f20daf37898d`.
- L1-L4 repeat3 approval `job_51a85fa2fc58` was consumed once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704`. It
  proved project-root-local supervisor imports through L1/L2 direct execution,
  L3 `detail_ready`, and L4 macro evidence, then stopped on the final blocked
  task because the driver used unknown artifact kind `blocked`. The B7
  normalizer also classified otherwise useful rows as `test_design_failure`.
  Worker2 `job_855ab110681e` prepares the repeat4 packet to use
  `blocker_evidence`, compute route correctness before classification, and
  request a fresh reviewer2 verdict for
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence4-20260704`.
- L5 partial-only approval `job_4e3c051ef168` was consumed once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704`.
  The run failed before provider ask activation because the lab-local plan root
  `docs/plantree/plans/phase6b-real-provider-l5` was absent before
  `plan task-create`; B7 was captured as `not_claimable` /
  `test_design_failure`, and post-B7 cleanup returned `state: unmounted`. That
  approval/root are historical and not runnable.
- L5 partial-only repeat2 approval `job_af5f6fb64a7d` and urgent addendum
  approval `job_663bad41c855` were consumed once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704`.
  The plan-root and project-local supervisor import repairs worked through
  `direct_execution`, but the runner imported a blocked round with
  `round_result_source=ask_submission_failed`: plain child `ask` is rejected
  from an active CCB task when the child result is needed. Worker1 source
  repair `job_19092d158390` was accepted by reviewer2 `job_56466011201a`:
  result-needed ask-first child asks now set `callback=True` and use existing
  CCB chain routing.
- L5 partial-only repeat3 approval `job_de6263827473` was consumed once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704`.
  Current-system provider environment inheritance worked and the worker
  produced partial evidence, but reviewer ask submission failed before reviewer
  verdict with `ask --chain requires an active parent job for the sender`.
  The B7 report
  [phase6b-real-provider-l5-partial-repeat3-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat3-b7-20260704.md)
  is `not_claimable` / `test_design_failure`, and cleanup returned
  `state: unmounted`. Worker1 source repair `job_52ec099f6427` was accepted
  by reviewer2 `job_766050825b27`: watched ask-first child asks now submit
  from runner-owned `system` sender with no callback/chain and no silence.
  Worker3 `job_2faf4fd57789` prepared a fresh repeat4 launch packet, and
  reviewer2 granted approval-to-run in `job_5dd131a6ea7e`; talk2 consumed that
  approval once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704`.
  The B7 report
  [../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md)
  is `valid_non_success` with `reviewer_rework_or_partial_observed=true`.
- Reviewer1 refreshed coverage audit `job_ecea1e97fc6a` returned `COVERAGE OK`
  before repeat3/L5 repeat2 runtime consumption. Reviewer1 follow-up coverage
  audit `job_e8459a2782cd` also returned `COVERAGE OK`: L1-L4 needs
  blocked-kind/B7 classification repair via worker2 `job_855ab110681e` plus
  provider-env addendum `job_984364b1766c` and doc-test addendum
  `job_ce9ed763cc71`; L5 now needs a fresh repeat4 launch packet/run using
  the accepted `system` sender ask-first repair, assigned to worker3 as
  `job_2faf4fd57789`.
- Owner decision on 2026-07-04: future real-provider packets inherit the
  current system provider environment and must not export lab-local `HOME` or
  `CCB_SOURCE_HOME` to a fresh provider home.
- Any future real-provider command needs a fresh root and a new explicit
  owner/supervisor launch decision naming the exact task tranche and command
  shape.

## Claim Coverage

| Claim requirement | Required evidence | Current evidence | State | Next gate |
| :--- | :--- | :--- | :--- | :--- |
| Phase 6A prerequisite is accepted | Reviewer-accepted fake-provider matrix and claim boundary | [phase1-6-evidence-index.md](../history/phase1-6-evidence-index.md) records reviewer1 matrix acceptance and reviewer2 claim-boundary acceptance. | Closed for Phase 6A scope only | Do not expand this into a real-provider claim. |
| L0 real-provider runtime sanity | Approved L0 run, ask reachability, B7 row, clean release/cleanup | [phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md](../history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md) has `classification=pass`; cleanup returned `state: unmounted`. | Closed for L0 only | Do not rerun or reuse repeat6 approval. |
| L1 and L2 basic executable tasks | Real-provider execution rows for L1 and L2 with expected route/result, artifacts, and cleanup | Historical repeats 3-11 exposed and then repaired command, project-root, ask-routing, and normalizer failures. Sequence12 consumed talk2 self-review exactly once from `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`. B7 [phase6b-real-provider-l1-l4-repeat12-b7-20260705.md](../history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md) is `Status: pass`: L1 `phase6b-l1-doc-direct-execution` and L2 `phase6b-l2-code-test-direct-execution` both classify `pass`, include worker/reviewer/round evidence, project-root changed-file evidence, script-owned route/round checks, and L2 lab-local unittest resolution evidence. Cleanup returned `kill_status: ok`, `state: unmounted`. | Closed by repeat12 L1/L2 rows | Sequence12 is consumed/non-reusable. Do not rerun without a fresh root and new talk2 launch review. |
| At least one L3 `needs_detail` | Real-provider route/detailer evidence for L3; endpoint must be explicit | Sequence12 produced a claimable L3 row: `phase6b-l3-needs-detail-source-inspection` observed route `needs_detail`, final status `detail_ready`, round result `detail_ready`, classification `valid_non_success`, detailer activation observed, detail packet/step evidence present, and no post-detail execution. | Closed by repeat12 L3 row | Keep L3 bounded at `detail_ready`; post-detail execution remains a separate gate. |
| At least one blocked or macro-adjustment termination | Real-provider row for `blocked` or `macro_adjustment_request` with script-owned authority import | Sequence12 produced claimable L4 rows for both terminal routes: `phase6b-l4-macro-adjustment-request` observed `macro_adjustment_request -> replan_required` with `macro_adjustment_request` evidence, and `phase6b-l4-blocked-missing-secret` observed `blocked -> blocked` with `blocker_evidence` for missing `PHASE6B_LAB_PRIVATE_API_TOKEN`. Both classify `valid_non_success`; neither mounted worker/reviewer execution. | Closed by repeat12 L4 rows | Preserve script-owned terminal authority; sequence12 is consumed/non-reusable. |
| At least one reviewer rework or partial observation | Concrete real-provider task/case and evidence row, or explicit blocker preventing Phase 6B claim | [phase6b-reviewer-rework-partial-observation-tranche.md](phase6b-reviewer-rework-partial-observation-tranche.md) defines a bounded partial candidate and bounded reviewer-rework candidate; reviewer2 accepted it as plan-only readiness in `job_3824dde8454e`. Static hardening `job_82d723ec0f89` adds a reviewable embedded normalizer shape, accepted by reviewer2 in `job_f20daf37898d`. The first L5 partial-only approval stopped at missing plan-root setup. L5 repeat2 reached `direct_execution` but stopped with `ask_submission_failed` before worker/reviewer output. L5 repeat3 reached `direct_execution` and worker partial evidence, but reviewer ask submission failed before reviewer-gated verdict. The source fix is accepted in `job_766050825b27`; repeat4 approval-to-run was granted in `job_5dd131a6ea7e` and consumed once by talk2. The repeat4 B7 row is `direct_execution` / `partial` / `partial` / `valid_non_success`, with `reviewer_rework_or_partial_observed=true` and cleanup `state: unmounted`. | Closed for partial observation only | Do not rerun or reuse repeat4 approval. Reviewer-rework remains unobserved, but partial observation satisfies the acceptance goal's either/or requirement. |
| B7 aggregation and final gate | B7 report path, evidence rows, failure taxonomy, human diagnosis for every non-pass row, and final owner/supervisor aggregation gate | Historical setup-failure and repeat2-11 B7 reports remain non-claimable or corrected as documented above. Sequence12 B7 [phase6b-real-provider-l1-l4-repeat12-b7-20260705.md](../history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md) is `Status: pass` with all five L1-L4 rows claimable. L5 repeat4 B7 [phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md) is usable for the partial-observation lane. Final aggregation is recorded in [phase1-6-acceptance-report-20260705.md](../history/phase1-6-acceptance-report-20260705.md). | Closed by talk2 final aggregation on 2026-07-05 | Do not expand this into production/default enablement, post-detail execution, reviewer-rework stability, or multi-round workflow acceptance. |
| First stable complexity breakpoint | Observed breakpoint or `unknown` with evidence | L5 repeat4 produced a partial row for `phase6b-l5-partial-budget-source-gap`, with `classification=valid_non_success`. This establishes a partial-observation breakpoint at L5 for the current task pack. | Closed for L5 partial breakpoint | Reviewer-rework remains unobserved; open a separate goal if that branch needs direct evidence. |
| Evidence schema fidelity | Normalizer emits the fields it declares, including task-specific fields and authority audit fields | Worker1 callback `job_307d5f834a1a` made the embedded normalizer emit declared shared and task-specific fields; reviewer2 accepted the static hardening in `job_d023a883a62d`. Static hardening `job_82d723ec0f89` now emits conservative `authority_checks.*` booleans in the embedded L1-L4 normalizer; reviewer2 accepted it in `job_f20daf37898d`. | Static schema fidelity closed for launch-packet readiness; no runtime evidence | Future approval-to-run requests must preserve these checks and still produce B7 runtime evidence. |
| Cleanup, topology, and authority safety | Bounded cleanup/residue classification; no topology dispatch mainline; no provider-reply authority mutation | L0 repeat6 satisfied this for L0. Sequence12 B7 authority checks are true for topology dispatch absence, communication-edge absence, provider-reply authority parsing absence, script-owned route/round imports, dynamic-agent absence, config dynamic-agent absence, and observed topology residue absence; cleanup returned `kill_status: ok`, `state: unmounted`. | Closed for L1-L4 repeat12 evidence | Final aggregation must preserve these checks. |

## Phase 6B Claim Preconditions

The 2026-07-05 final aggregation found the bounded Phase 6B claim satisfied
because all of the following are true in current evidence:

- Phase 6A remains accepted for the fake-provider/source-wrapper program-matrix
  scope, without being expanded into a real-provider claim by implication.
- L0 evidence remains valid and its consumed approval is not reused.
- L1 and L2 have real-provider rows with expected route, expected final status,
  reviewer contract citation, changed-file/test evidence, cleanup evidence, and
  B7 classification.
- At least one L3 `needs_detail` row has real-provider route/detailer evidence,
  explicit endpoint semantics, detail packet/step/source evidence, and no
  hidden post-detail claim unless separately approved and evidenced.
- At least one L4 `blocked` or `macro_adjustment_request` row has
  real-provider terminal evidence, script-owned import authority, and no worker
  mount or fake fallback outside the approved route.
- At least one L5 reviewer-rework or partial observation has real-provider
  evidence and correct classification. A direct pass without rework does not
  satisfy this item.
- B7 aggregation is complete for the real-provider tranche(s), includes
  failure taxonomy and human diagnosis for every non-pass row, and has passed
  the `talk2` owner/supervisor final aggregation gate requested by the user.
- The first stable complexity breakpoint is either observed from the evidence
  or explicitly remains `unknown` with reviewer-accepted justification.
- Cleanup, topology, and authority audits show no unbounded runtime residue, no
  topology communication DSL, no `topology_dispatch.json` mainline, no
  provider-reply authority parsing, and no blocked/partial work marked `done`.
- The final acceptance report under `history/` states that Phase 6B is
  claimable for initial real-provider, single-round capability and links the
  exact evidence rows, B7 report(s), cleanup evidence, and remaining
  non-production blockers:
  [phase1-6-acceptance-report-20260705.md](../history/phase1-6-acceptance-report-20260705.md).

If future evidence contradicts any item, reopen the claim matrix and record the
contradiction as a new gate instead of reusing consumed roots.

## Decision Rules

- `DOC-ONLY ACCEPTED` means the package is reviewable; it is not launch
  approval.
- `COVERAGE OK` means the current supervision lanes cover the known gaps; it is
  not launch approval and not runtime evidence.
- `APPROVAL-TO-RUN GRANTED` historical entries were used for earlier lanes, but
  the final sequence12 launch and final aggregation used `talk2` self-review
  after the user explicitly stopped reviewer routing.
- A successful L1-L4 run without reviewer rework or partial observation would
  not complete Phase 6B. This claim uses L5 repeat4 partial observation to
  satisfy the either/or requirement.
- Any non-pass row must include bounded classification, failure taxonomy,
  human diagnosis, cleanup result, runtime residue, and authority/topology
  audit evidence before it can be treated as valid non-success.
