# Phase 1-6 Active Supervision Board

Date: 2026-07-04
Status: FINAL AGGREGATION CLOSED / PHASE 6B CLAIMED FOR BOUNDED SCOPE

## Purpose

This board records the active and completed `talk2` supervision lanes for the
[Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md). It is a
handoff aid. The acceptance verdict is recorded separately in
[../history/phase1-6-acceptance-report-20260705.md](../history/phase1-6-acceptance-report-20260705.md).

## Current Claim State

- Phase 6A is claimable only for the accepted fake-provider, single-round,
  source-wrapper program-matrix scope.
- Phase 6B is claimable for initial real-provider, single-round capability
  after `talk2` final aggregation on 2026-07-05. The accepted evidence set is
  L0 repeat6, L1-L4 repeat12, and L5 partial repeat4.
- A separate post-acceptance deployment-readiness lane is now active at
  [phase1-6-deployment-readiness-supervision-20260707.md](phase1-6-deployment-readiness-supervision-20260707.md).
  It does not retract the bounded Phase 6B claim; it tracks the stricter
  operator-facing standard requested on 2026-07-07: frontdesk-started real
  tasks, L1-L4 regression after later source changes, dynamic release under
  pressure, UI/sidebar visibility, and observer behavior.
- That deployment-readiness lane is currently blocked. reviewer2
  `job_7c18b7d9e333` requires independent deployment audit ownership, and
  reviewer1 `job_50c72bc31578` requires stronger frontdesk route mix,
  module-level, UI/sidebar, busy-retain, and final-report evidence before any
  deployment-ready verdict.
- Current partial deployment evidence: worker1 `job_ec6a6a8b2ef8` passes only
  the Frontdesk real entry E2E lane. worker2 `job_cd6b21bc5896` provides useful
  raw L1-L4/sequence13 regression evidence, but it is not deployment-ready
  evidence because it did not start from frontdesk intake and does not use the
  fixed row schema. worker3 `job_153786148bfd` provides useful raw
  UI/sidebar, observer, resident-reachability, and dynamic-unload evidence, but
  it is not deployment-ready evidence because task authority was
  script-created/imported after frontdesk asks, fixed evidence rows are
  missing, and positive busy-retain evidence is still absent. As of the
  2026-07-07T11:50:57+08:00 local state check, worker1
  `job_e6cffc269af4` is completed and passes the Frontdesk=Codex
  direct-execution retest lane with fixed rows for one L2 task reaching
  `done/pass` and clean dynamic release. It does not cover L1-L4 route mix,
  UI/sidebar, or positive busy-retain. worker2 `job_a8d5fddd2a67` is completed
  and is `BLOCKER / not_claimable` for the stricter L1-L4 lane. Fresh root
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence15-worker2-20260707113648`
  proves the frontdesk/planner entry path, inherited provider home, explicit
  positive timeout diagnostic, default watch beyond the old 10 second window,
  and dynamic release for the frontdesk-created combined task. Formal L1 then
  stopped after worker/reviewer success because final round orchestrator
  provider delivery failed with `codex_prompt_delivery_failed /
  delivery_anchor_missing`; L2-L4 were not reached. worker2 applied a focused
  retry-policy source repair in
  `lib/ccbd/services/dispatcher_runtime/finalization_retry_runtime/policy.py`
  so `decision.diagnostics.delivery_retryable=true` can trigger automatic
  retry without overriding non-retryable API failures. Talk2 re-ran
  `test/test_ccbd_retry_failure_detail.py` (`4 passed`),
  `test/test_stability_regressions.py::test_codex_delivery_guard_times_out_after_anchor_never_appears`
  (`1 passed`), and py_compile for the touched retry files. A new fresh L1-L4
  frontdesk-started retest after this repair was assigned to worker2 as
  `job_93f0288df5f7`; sequence15 is consumed failure evidence and must not be
  reused. A separate frontdesk auto-runner role-output issue was already
  repaired: an earlier failed planner job `job_ce2490255a5a` had been logged
  repeatedly as `role_output_import_blocked`, then a later auto-runner for
  successful planner job `job_03c5c271f243` stopped on the old failed job
  instead of consuming the requested wait job. The source bug was that blocked
  role-output imports were not treated as settled for future auto-runner scans.
  A focused source repair was assigned to worker1 as `job_9e95855157d1`;
  completion artifact
  `job_9e95855157d1-art_2036e8fd9d6d4770.txt` is accepted for that focused
  repair. The scanner path now treats prior `role_output_import_blocked`
  records as settled while leaving explicit consume `ok`-only, so blocked
  evidence is not rewritten as pass. Talk2 re-ran `py_compile`, the new
  regression, the focused `loop_runner_auto or role_output_import` selection
  (`9 passed`), and the full `test/test_loop_capacity_cli.py` file
  (`109 passed`). The older queued worker2 ask `job_ac5fef15fa2a` failed with
  an empty artifact and is not evidence; the active post-repair retest is
  worker2 `job_93f0288df5f7`. Later worker3 ask `job_731bc4142333` also failed
  with an empty artifact and is not evidence.
- Worker2 `job_93f0288df5f7` completed the fresh sequence16 retest after
  worker1's explicit-project ask repair. The frontdesk target blocker is
  cleared, but sequence16 is still `not_claimable`: L1 reached
  `direct_execution -> done/pass`; L3 reached `needs_detail -> detail_ready`;
  L4 macro reached `macro_adjustment_request -> replan_required`; L4 blocked
  reached `blocked -> blocked`; L2 reached `direct_execution` but became
  terminally `blocked` before worker/reviewer execution because rolepack/bootstrap
  setup failed. Logs show `roles_install_all.stderr` reporting `role source not
  found` for all required CCB route roles, and the generated B7 missed
  task-show/round evidence for direct rows while preserving stale dynamic
  residue despite post-B7 cleanup returning `state: unmounted`. This is a
  sequence driver/B7 evidence blocker, not an accepted L1-L4 result. worker3
  `job_553ecdfb89ca` returned
  `BLOCKER / not deployment-ready`: positive rows cover busy-retain,
  UI/sidebar switching, and observer timeout behavior, but direct execution can
  leave dynamic release residue after auto-release timeout, `needs_detail` can
  repeatedly reactivate task_detailer instead of settling to `detail_ready`, and
  provider delivery failures prevented the full route mix. Focused repair
  `job_fb4475224824` is accepted as source repair: task_detailer output imports
  detail artifacts once and settles `detail_ready`, and release reconcile now
  performs one bounded non-busy residue retry. The real-provider stress harness
  still needs a fresh rerun before deployment readiness. These are triage
  observations only, not acceptance evidence.
- Worker1 `job_df3c9451c8b5` is accepted as source repair for the sequence16
  rolepack/bootstrap and B7 evidence blocker. Source-test role installation now
  discovers source-checkout draft RolePacks, required draft manifests use
  installer-valid `catalog.level = "experimental"`, the maintained sequence
  packet seeds roles via `ccb_test roles install --skip-tools`, duplicate task
  creation is handled by observing/reusing existing task authority, and B7 can
  read round evidence from task-show artifact paths while keeping stale topology
  residue failing unless authoritative cleanup evidence says `kill_status: ok`
  and `state: unmounted`. Talk2 verified the targeted 94-test bundle,
  py_compile, invalid-level scan, and a source-wrapper role-seed smoke for all
  seven required roles from `/home/bfly/yunwei/test_ccb2`. This is source
  repair evidence only; a fresh sequence17 real-provider L1-L4 retest is
  required.
- Worker2 `job_6437d7ef41ea` consumed sequence17 from fresh root
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence17-worker2-20260707-131428`.
  It is `not_claimable`. Role seeding and final cleanup were fixed, but the
  harness split into two task flows: frontdesk created the meta task
  `fresh-sequence17-real-provider-deploymen-20260707052218`, which blocked on
  `isolated_workspace_deletions_unsupported`, while the supervisor then created
  manual L1 task `phase6b-l1-doc-direct-execution` and killed the project while
  that worker job was still incomplete, producing `ask_job_incomplete`. The
  B7/equivalent report also read stale pre-terminal task-show evidence. This is
  a harness/controller blocker, not a provider-task pass or a valid L1 failure.
- Talk2 audited worker1 `job_08f4c86e3973` as the sequence17
  harness/controller source repair and added one stricter guard before any
  fresh provider run: live ask-first pending authority in `round.pending.json`
  or `ask_first_stage_state.json` now stops progress/cleanup with rc 78, and
  provider-running `loop runner --once` paths in the sequence12 driver no
  longer pass explicit timeout values or use shell timeout wrapping. Verified:
  sequence12 doc tests (`30 passed`), rolepack tests (`66 passed`), and focused
  pending/timeout loop regressions (`78 passed, 128 deselected`). Fresh
  real-provider asks are in flight as worker2 `job_a1edbee23686` for
  frontdesk-started L1-L4 sequence18 and worker3 `job_89215d1865e5` for
  single-round dynamic-node unload stress.
- Worker2 `job_a1edbee23686` returned an invalid evidence report: the claimed
  sequence18 fresh root and its B7/rows/command-log paths do not exist on
  disk, and only the old sequence17 root is present. Worker3
  `job_89215d1865e5` exposed a separate harness blocker: the generated config
  mounted only `bootstrap:codex`, so `ccb_test ask frontdesk` failed with
  `unknown agent: frontdesk`; role profiles alone do not create ask targets.
  Worker1 follow-up job `job_a0fac3efdb4c` produced a parameterized,
  non-stale runner with inspectable manifest paths and no provider timeout, but
  talk2 audit found the worker3 resident-agent blocker still uncovered.
  Follow-up jobs `job_e19d3a0c25a5`, `job_c515d0f1736e`, and
  `job_83494eb661b7` require the runner to write resident-agent config before
  startup or reload it before use, and to validate mounted resident
  frontdesk/planner/orchestrator/task_detailer/ccb_round_reviewer
  `agent.json` authority before any further L1-L4 retest is accepted.
  Worker1 `job_e19d3a0c25a5` completed only the config/static portion; talk2
  rejected it as complete because it still did not check actual
  `.ccb/agents/<target>/agent.json` mounted authority. A stricter follow-up
  `job_7ebb314a7bcc` / `job_c515d0f1736e` added the negative
  `resident_agents_not_mounted` guard before `frontdesk-entry`. Worker1
  `job_83494eb661b7` completed the positive source/static coverage proving all
  resident `agent.json` files allow `frontdesk_entry` to reach the ask command
  path, but worker3 `job_89215d1865e5` then exposed the next readiness blocker:
  resident `agent.json` files can exist while `ps` reports every resident as
  `state=degraded`, and frontdesk delivery can fail with
  `codex_prompt_delivery_failed / delivery_anchor_missing` because the current
  provider log path points to an old donor root. Worker1 `job_c82254482242`
  plus talk2 local hardening now add the missing source/static resident
  readiness guard: the runner parses `ccb_test --project <project> ps`, and
  `init` / `frontdesk-entry` fail with `resident_agents_not_ready` unless all
  five resident roles are live and `state=idle`. `degraded`, `busy`, and
  missing ps entries now block before any `ask frontdesk`. Verified:
  `test/test_phase6b_l1_l4_frontdesk_runner.py` -> `13 passed` and py_compile
  for the runner/test. No fresh real-provider retest has consumed this repair.
- Fresh post-guard real-provider retests were submitted for the next evidence
  wave: worker1 `job_df0ee0c52429` for frontdesk=codex direct-execution smoke,
  worker2 `job_e8f28dbc52f5` for L1-L4 route-mix regression with the maintained
  runner, and worker3 `job_1c6a378536be` for UI/lifecycle pressure. These jobs
  are in flight only. Acceptance requires inspectable fresh roots under
  `/home/bfly/yunwei/test_ccb2`, inherited provider environment, no fake
  provider, live resident `ps` all idle before frontdesk ask, fixed evidence
  rows, script-owned authority imports, dynamic release/retention evidence,
  cleanup after B7, and no missing evidence paths.
- This claim does not approve production/default enablement, post-detail
  execution, reviewer-rework stability, long-running multi-round workflows, or
  arbitrary workflow authoring.
- Any further real-provider command requires a fresh root and a new explicit
  owner/supervisor launch decision.
- Reviewer2 granted final effective L1-L4 repeat8 approval-to-run in
  `job_05e6f1c57f3c`; talk2 consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`.
  The B7 report
  [../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md)
  is `Status: not_claimable`: L1/L2 are `test_design_failure`, while L3
  `needs_detail`, L4 `macro_adjustment_request`, and L4 `blocked` are bounded
  `valid_non_success` rows. Post-B7 cleanup succeeded with `kill_status: ok`,
  `state: unmounted`. Sequence8 is consumed/non-reusable. The repeat8 direct
  execution semantic split is recorded in
  [phase6b-repeat8-direct-execution-failure-note.md](phase6b-repeat8-direct-execution-failure-note.md):
  worker/reviewer success was verified in copy workspaces, but project-root
  evidence stayed unchanged. Reviewer2 `job_04b5c2faa2f2` blocks repeat8
  reapproval because the sequence8 root is now non-fresh.
- The dated Phase 6B L1-L4 launch request topic is now repeat8 historical
  record only, with no executable command block. Talk2 requested a separate
  active sequence9 approval packet:
  [phase6b-l1-l4-launch-request-sequence9-20260704.md](phase6b-l1-l4-launch-request-sequence9-20260704.md).
  Requested fresh root:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`;
  planned B7:
  `history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md`.
  Reviewer1 fallback launch-gate re-audit `job_c4935017fc15` granted exactly
  one sequence9 run. Talk2 consumed it once from the sequence9 root. L1 reached
  `done/pass`; L2 updated project-root `lab_code/calculator.py`, and a
  supervisor-created project-root unittest resolution check passed, but task
  authority remained `blocked` with
  `round_result_source=isolated_workspace_no_project_root_effect`. Talk2
  stopped the tranche under the approved stop-on-failure rule, so L3/L4 were
  not run. The generated repeat9 B7 says `Status: pass`, but that is rejected
  as a normalizer false-positive in
  [../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md](../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md).
  Cleanup returned `kill_status: ok`, `state: unmounted`. Sequence9 is
  consumed/non-reusable. The prior repeat9 draft hold is historical only, not
  an active approval/run state; later sequence12 evidence closes the L1-L4
  lane for the bounded Phase 6B claim.
- Worker1 `job_dd20a18926e1` prepared the fresh sequence10 repair/launch
  packet:
  [phase6b-l1-l4-launch-request-sequence10-20260704.md](phase6b-l1-l4-launch-request-sequence10-20260704.md).
  It uses root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence10-20260704`
  and planned B7 path
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md`.
  Reviewer2 audit `job_0d07e67ef312` remained queued, so reviewer1 fallback
  launch gate `job_bfe386ae7a9f` granted exactly one sequence10 run. Talk2
  consumed it once. L1 direct execution stopped with task authority `blocked`
  after the round reviewer found worker changes only in the copy workspace; the
  main project `lab_docs/l1_release_note.md` was still `status: draft` /
  `summary: TBD`. L2/L3/L4 were not run. Repeat10 B7
  [../history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md)
  is `Status: not_claimable`; cleanup returned `kill_status: ok`,
  `state: unmounted`. Sequence10 is consumed/non-reusable.
- Worker1 source repair `job_e2ff663087be` addresses the sequence10
  fake-success source bug for future runs: ask-first `direct_execution` now
  stages allowed copy-workspace deltas into the project root before
  code-reviewer and `ccb_round_reviewer` validation, includes project-root
  authority evidence in their prompts, and rolls staged changes back on
  non-pass/unknown/test-failure outcomes. This is source readiness only; no
  real-provider, B7, source-wrapper runtime, or cleanup command was run. Later
  sequence12 runtime evidence proves the repaired path for the bounded Phase 6B
  claim.
- Reviewer1 accepted the source repair in `job_a7e62fee5496`; talk2 local
  static verification after review passed `py_compile` for the repaired loop
  services and `python -m pytest test/test_loop_capacity_cli.py
  test/test_plan_tasks_cli.py test/test_loop_topology_cli.py
  test/test_loop_topology_dispatch_contract.py -q` with `89 passed`.
- Worker3 `job_1cfa66b23752` prepared the fresh L1-L4 sequence11 approval
  packet:
  [phase6b-l1-l4-launch-request-sequence11-20260704.md](phase6b-l1-l4-launch-request-sequence11-20260704.md).
  Reviewer1 `job_68063ec21783` granted exactly one run, and talk2 consumed it
  once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence11-20260704`
  with B7 path
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat11-b7-20260704.md`.
  L1 and L2 reached `done/pass` with project-root evidence, but B7 misclassified
  them because round/result authority parsing and persisted-topology residue
  semantics are wrong in the normalizer. L3 activated the detailer, then failed
  to import the detail packet because non-orchestration detail artifacts were
  submitted with `--route`; `detail_ready` transition was then rejected. Talk2
  stopped before L4, captured repeat11 B7 as `Status: not_claimable`, and
  cleanup returned `kill_status: ok`. Sequence11 is consumed/non-reusable.
  Worker1 `job_a218e823a78f` / `job_ad72d8bb8790` repaired the L3
  detail-authority path and reviewer1 accepted it in `job_f3982925275d`.
  Worker2 `job_f4ee3f0cc58e` / `job_dd89005df2ee` repaired the repeat11 B7
  normalizer and reviewer1 accepted it through callback continuation
  `cb_faab6bb2d057-art_f9e89c4d470a4c16.txt`.
- Worker3 `job_cf01392dc751` prepared the fresh L1-L4 sequence12 approval
  packet:
  [phase6b-l1-l4-launch-request-sequence12-20260705.md](phase6b-l1-l4-launch-request-sequence12-20260705.md).
  Requested root:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`;
  planned B7 path:
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md`.
  The packet carries forward the accepted L3 detail-authority and repeat11 B7
  normalizer repairs. It is not runtime approval; sequence12 may run only if
  talk2 grants launch-specific self-review approval and reconfirms the root is
  absent immediately before `init`. Talk2 submitted a self-contained reviewer2
  request `job_a047b32d275c`, but no completion artifact is visible; on
  2026-07-05 the user instructed talk2 to stop using reviewers for this gate.
- Owner decision on 2026-07-04: future real-provider lab launch packets must
  inherit the current system provider environment. Do not export lab-local
  `HOME` or `CCB_SOURCE_HOME` to a fresh `source_home` for real-provider runs;
  that isolation can trigger unnecessary Codex login churn. External test roots
  under `/home/bfly/yunwei/test_ccb2` and lab-local RolePack stores remain
  required unless a reviewer-approved packet says otherwise.
- Reviewer2 granted repaired L1-L4 checkpoint/resume approval-to-run in
  `job_7800c403f864`, superseding the held old monolithic approval
  `job_d44bf15c6cb1`. Talk2 consumed the repaired approval exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704`.
  Materialization and `init` succeeded, but the first L1 `start-task` stopped
  before provider ask activation because `plan task-create --plan
  phase6b-real-provider-l1-l4` required a project plan root that the driver had
  not materialized. B7 was captured as `not_claimable` /
  `test_design_failure`, then cleanup returned `state: unmounted`.
- Reviewer2 granted L1-L4 repeat2 approval-to-run in `job_0c8596e0895d`.
  Talk2 consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704`.
  The plan-root repair worked: `task-create`, anchor imports,
  `ready_for_orchestration`, and orchestrator activation all succeeded for L1.
  The run then stopped before direct execution because
  `plan task-artifact --kind orchestration_notes` rejected the supervisor file:
  it was outside the lab project root. B7 was captured as `not_claimable` /
  `test_design_failure`, then cleanup returned `state: unmounted`.
- Reviewer2 granted L5 partial-only approval-to-run in `job_4e3c051ef168`.
  Talk2 consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704`.
  Materialization and `init` succeeded, but `start-partial` stopped before
  provider ask activation because `plan task-create --plan
  phase6b-real-provider-l5` required a project plan root that the driver had
  not materialized. B7 was captured as `not_claimable` /
  `test_design_failure`, then cleanup returned `state: unmounted`.
- Reviewer2 granted L5 partial-only repeat2 approval-to-run in
  `job_af5f6fb64a7d` plus urgent addendum approval `job_663bad41c855`. Talk2
  consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704`.
  The plan-root and project-local supervisor import repairs worked through
  `direct_execution`; the round then imported `blocked` with
  `round_result_source=ask_submission_failed` because ask-first execution
  submitted plain `ask` from an active CCB task context. B7 was captured as
  `not_claimable` / `test_design_failure`, then cleanup returned
  `state: unmounted`. Worker1 source repair `job_19092d158390` was accepted by
  reviewer2 `job_56466011201a`: ask-first result-needed child asks now set
  `callback=True`, which maps to CCB chain routing. This closes the source
  blocker only; a fresh L5 launch-specific approval and supervised rerun are
  still required for partial/rework evidence.
- Reviewer2 granted L5 partial-only repeat3 approval-to-run in
  `job_de6263827473` from worker1 packet `job_657112c87bce`. Talk2 consumed
  it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704`.
  The run inherited the current system provider environment and reached
  `direct_execution`; the worker returned partial evidence, but reviewer ask
  submission failed before any reviewer verdict with
  `ask --chain requires an active parent job for the sender`. B7 was captured
  as `not_claimable` / `test_design_failure`, then cleanup returned
  `kill_status: ok`, `state: unmounted` after retrying cleanup with lab-local
  `AGENT_ROLES_STORE`.
- Worker1 source repair `job_52ec099f6427` was accepted by reviewer2
  `job_766050825b27`: ask-first watched child asks now submit from
  runner-owned `system` sender, with `callback=False`, `silence=False`, and
  immediate `watch_ask_job`. This repairs the repeat3 parent-job failure in
  source/tests only. No runtime rerun is approved.
- Current local worktree audit: repeat6 approval-to-run was granted once in
  reviewer2 `job_8c7b404ad63c` and consumed by one talk2-supervised run from
  `/home/bfly/yunwei/test_ccb2`. B7 evidence was captured before cleanup and
  post-B7 cleanup returned `state: unmounted`.
- Reviewer2 granted L1-L4 repeat6 approval-to-run in `job_bca6a4a854a3`.
  Talk2 consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence6-20260704`.
  The run stopped at L1 because the real orchestrator provider followed the
  activation prompt and imported `orchestration_notes` itself. This violates
  the launch contract: route authority must come from supervisor/script-owned
  imports, not provider-side `ccb plan task-artifact`. B7 is
  [../history/phase6b-real-provider-l1-l4-repeat6-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat6-b7-20260704.md)
  with `Status: not_claimable`; cleanup returned `kill_status: ok`,
  `state: unmounted`.
- Claim coverage matrix:
  [phase6b-real-provider-claim-coverage-matrix.md](phase6b-real-provider-claim-coverage-matrix.md).

## Active Lanes

| Lane | Owner | Job | Review Path | Scope | Exit Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Phase 6B L1-L4 historical-doc cleanup | worker3 -> reviewer2 | worker3 `job_5bc19f21a1d5`; reviewer1 re-audit `job_b4184497742b` | Dated launch request topic is repeat8 historical/non-runnable only. Sequence9 now lives in a separate active packet. | Historical cleanup remains doc-only; do not run from the dated repeat8 topic. |
| Phase 6B L1-L4 sequence9 runtime attempt | talk2 | reviewer1 fallback launch-gate `job_c4935017fc15` | [phase6b-l1-l4-launch-request-sequence9-20260704.md](phase6b-l1-l4-launch-request-sequence9-20260704.md) was consumed once from `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`. L1 passed; L2 project-root file/test evidence exists but task authority is `blocked`; L3/L4 were not run. | Repeat9 is not claimable. Generated B7 false-pass is rejected by [../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md](../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md). Cleanup returned `kill_status: ok`, `state: unmounted`. |
| Phase 6B L1-L4 sequence11 runtime attempt | talk2 | reviewer1 `job_68063ec21783` | [phase6b-l1-l4-launch-request-sequence11-20260704.md](phase6b-l1-l4-launch-request-sequence11-20260704.md) was consumed once from `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence11-20260704`. L1/L2 reached `done/pass`; L3 failed at detail packet import and `detail_ready`; L4 was not run. | Repeat11 B7 [../history/phase6b-real-provider-l1-l4-repeat11-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat11-b7-20260704.md) is `Status: not_claimable`; cleanup returned `kill_status: ok`. |
| Phase 6B L3 detail-authority repair | worker1 -> reviewer1 | worker1 `job_a218e823a78f` / `job_ad72d8bb8790`; reviewer1 `job_f3982925275d` | Repair the sequence11 `needs_detail -> detail_ready` path: non-orchestration detail artifacts do not use `--route`, `detail_ready` is gated by required artifacts, and command-status failure markers fail hard. | Accepted; no runtime command approved by this source/doc repair. |
| Phase 6B repeat11 B7 normalizer repair | worker2 -> reviewer1 | worker2 `job_f4ee3f0cc58e` / `job_dd89005df2ee`; reviewer callback `job_f1a981893030` | Repair B7 parsing/classification so L1/L2 `done/pass` rows use script-owned round/task evidence and persisted topology evidence is not treated as dynamic runtime residue. | Accepted; no runtime command approved by this docs/test repair. |
| Phase 6B L1-L4 sequence12 runtime attempt | talk2 | worker3 `job_cf01392dc751`; reviewer1 fallback `job_454bdb9b36f1`; reviewer2 request `job_a047b32d275c` has no artifact; user reassigned gate to talk2 | Talk2 self-reviewed [phase6b-l1-l4-launch-request-sequence12-20260705.md](phase6b-l1-l4-launch-request-sequence12-20260705.md), confirmed root/B7 absence, and consumed it once from `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`. B7 [../history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md](../history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md) is `Status: pass`: L1/L2 are `pass`; L3, L4 macro, and L4 blocked are `valid_non_success`; all rows are claimable. | Consumed/non-reusable. Cleanup returned `kill_status: ok`, `state: unmounted`. Final aggregation is recorded in [../history/phase1-6-acceptance-report-20260705.md](../history/phase1-6-acceptance-report-20260705.md). |

Talk2 static preflight for the current L5 repeat4 packet passed on
2026-07-04: L5 doc tests `7 passed`, L1-L4/L5 doc bundle `16 passed`,
`test/test_loop_capacity_cli.py` `37 passed`, py_compile/diff/whitespace/link
checks passed, and the repeat4 root was absent. Reviewer2 then granted
approval-to-run in `job_5dd131a6ea7e`; talk2 consumed it exactly once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704`.
The resulting B7 report
[../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md)
has `Status: valid_non_success` and
`reviewer_rework_or_partial_observed=true`; post-B7 cleanup returned
`state: unmounted`.

Current wait rule: do not run more L1-L4 real-provider/runtime commands from
sequence12. The sequence12 root is consumed/non-reusable; any further L1-L4
runtime work requires a fresh root and a new talk2 launch review.
Reviewer1 fallback `job_454bdb9b36f1` explicitly does not approve runtime and
requires an explicit reviewer2 approval artifact before execution.
The approvals
`job_7800c403f864`, `job_0c8596e0895d`,
`job_51a85fa2fc58`, `job_6ec85738acc6`, `job_bca6a4a854a3`,
`job_a9649f4a0e98`, and repeat8 approval `job_05e6f1c57f3c`, plus roots
`phase6-real-lab-l1-l4-sequence-20260704`,
`phase6-real-lab-l1-l4-sequence2-20260704`,
`phase6-real-lab-l1-l4-sequence3-20260704`, and
`phase6-real-lab-l1-l4-sequence4-20260704`, and
`phase6-real-lab-l1-l4-sequence8-20260704`,
`phase6-real-lab-l1-l4-sequence9-20260704`, and
`phase6-real-lab-l1-l4-sequence10-20260704`, and
`phase6-real-lab-l1-l4-sequence11-20260704`, are consumed by failed runs and
must not be reused. The sequence5 root was partially started by talk2 and then
stopped after reviewer2 blocker `job_f142f85effeb`; it is also historical and
must not be reused. The sequence6 root stopped at L1 provider-side authority
write and is historical/non-reusable. Do not run more L5 real-provider/runtime commands unless a
fresh owner/supervisor launch decision names a new root, task tranche, and
executable continuation shape. L5 repeat2
approvals `job_af5f6fb64a7d` and `job_663bad41c855`, L5 repeat3 approval
`job_de6263827473`, plus roots
`phase6-real-lab-l5-partial-only-repeat2-20260704` and
`phase6-real-lab-l5-partial-only-repeat3-20260704`, are consumed and must not
be reused. Repeat3 showed a source-level child ask submission blocker from
runner-owned context, not provider environment isolation; that source blocker
is accepted as repaired in worker1 `job_52ec099f6427` / reviewer2
`job_766050825b27`. L5 repeat4 approval-to-run was granted in
reviewer2 `job_5dd131a6ea7e` and consumed once by talk2 from
`phase6-real-lab-l5-partial-only-repeat4-20260704`; it does not approve
reviewer-rework, L1-L4, Phase 6B, or production enablement, and must not be
reused.

Talk2 static verification after reviewer2 accepted worker1's project-local
ask/cwd repair: `python -m pytest test/test_v2_ask_service.py
test/test_loop_capacity_cli.py test/test_plan_tasks_cli.py -q` -> `88
passed`; `python -m pytest test/test_phase6b_l1_l4_launch_request_doc.py
test/test_phase6b_l5_launch_request_doc.py
test/test_phase6b_l5_rework_partial_tranche_doc.py -q` -> `19 passed`;
`git diff --check` on the touched source/docs/tests was clean; the repeat8
root `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`
was absent. No runtime/provider/B7 command was run.
Reviewer1 read-only repeat8 gate audit `job_bb6fa188932d` returned
`COVERAGE OK`; it does not grant runtime approval and requires talk2 to verify
sequence8 root freshness immediately before any approved `init`.
Talk2 consumed repeat8 on 2026-07-05 after confirming the root was absent:
B7 is `not_claimable`, cleanup succeeded, and no Phase 6B claim is permitted.

L1-L4 repeat4 was consumed once from
`phase6-real-lab-l1-l4-sequence4-20260704`. It completed L1, then stopped at
L2 because the exact approved unittest command is not valid under the inherited
provider environment; B7 is `not_claimable`, and post-B7 cleanup returned
`state: unmounted`.

Worker3 static hardening `job_82d723ec0f89` returned with reviewer2
`job_f20daf37898d` acceptance: the current tree contains L1-L4
`authority_checks.*` normalizer output and an embedded L5 reviewer-rework/partial
normalizer shape. This is docs/tests readiness only, not launch approval.

## Callback Acceptance Gates

Use these gates when accepting the active worker/reviewer callbacks. If any
gate is missing, keep Phase 6B unclaimed and either request a repair addendum
or record the blocker.

### Worker1 `job_fcb789dab179` / `job_19092d158390` - Ask-First Child Ask Repair

Accepted by reviewer2 `job_56466011201a`. The callback and reviewer artifact
prove:

- ask-first direct execution submits needed-result child asks through CCB chain
  routing, not plain `ask`, when running from an active CCB task context;
- worker, reviewer, rework, orchestrator, and `ccb_round_reviewer` ask sites
  keep reply artifacts as evidence only and do not mutate task authority from
  provider text;
- submit/watch failures still import blocked evidence and release dynamic
  topology; no blocked/partial work is marked `done`;
- focused tests cover the old `ask_submission_failed` failure and the chain
  route option;
- any source-wrapper smoke is fake/isolated only; no L5 or L1-L4 real-provider
  approval-to-run is implied.
- any future real-provider launch packet after this repair inherits the current
  system provider environment and does not create a fresh provider home.

### Worker2 `job_855ab110681e` - L1-L4 Repeat4 Packet

Accept only if the callback and reviewer artifact prove:

- active command/request uses a fresh repeat4 root and B7 path, and marks
  `job_d44bf15c6cb1`, `job_7800c403f864`, `job_0c8596e0895d`,
  `job_51a85fa2fc58`, and roots sequence/sequence2/sequence3 consumed;
- blocked terminal evidence imports through an accepted artifact kind such as
  `blocker_evidence`, never `--kind blocked`;
- B7 classification computes route correctness before classification and does
  not classify otherwise complete L1/L2/L3/L4 macro rows as
  `test_design_failure` because of a later blocked-row issue;
- L3 remains route/detail-only at `detail_ready` unless a fresh reviewer
  approval explicitly expands it;
- L5 reviewer-rework/partial remains excluded from this historical L1-L4
  packet; the current bounded Phase 6B claim is based on L0 repeat6, L1-L4
  repeat12, L5 partial repeat4, and the 2026-07-05 final aggregation;
- real-provider command shape inherits the current system provider environment
  and does not export lab-local `HOME` or `CCB_SOURCE_HOME`;
- `python -m pytest test/test_phase6b_l1_l4_launch_request_doc.py -q` is green
  or any remaining static drift is explicitly accepted by reviewer2. The
  current local tree now passes this doc test, but worker2/reviewer2 callback
  remains the authority for accepting the L1-L4 packet;
- no runtime/source-wrapper/provider command was run during packet repair.

### Worker3 `job_2faf4fd57789` - L5 Partial-Only Repeat4 Packet

Accept only if the callback and reviewer artifact prove:

- reviewer2 verdict is explicit: approval-to-run for exactly one future
  supervised L5 partial-only repeat4 run, doc-only acceptance, or blocker;
- root is fresh:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704`;
- B7 path is fresh:
  `history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md`;
- task scope is only `phase6b-l5-partial-budget-source-gap`, expected
  `direct_execution` / `partial` / `partial` / `valid_non_success`; reviewer
  rework remains excluded unless reviewer2 explicitly expands scope;
- command shape materializes a script from `/home/bfly/yunwei/test_ccb2`, does
  not pipe through stdin, creates project-local plan roots, and stores every
  supervisor import file inside the lab project root;
- packet verifies the accepted source repair: `RUNNER_ASK_SENDER = 'system'`,
  no callback/chain for watched ask-first child asks, and no `silence=True` for
  needed-result asks;
- provider map is `ccb_round_reviewer -> claude`, all other required roles ->
  `codex`, and real-provider command shape inherits the current system provider
  environment with no lab-local `HOME` / `CCB_SOURCE_HOME` override;
- no source-wrapper, `ccb_test`, provider, L5, runtime, launch, or B7 command
  was run by worker3.

### Reviewer1 `job_e8459a2782cd` - Read-Only Coverage Audit

Treat `COVERAGE OK` as lane coverage only. It is not launch approval, runtime
evidence, or a Phase 6B claim. Any blocker/high finding must either become a
new active lane or be folded into one of the two existing repair lanes before
another real-provider run.

## Completed Runtime Lane

| Lane | Owner | Job | Review | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| B-only L0 repeat6 runtime sanity | talk2 | reviewer2 `job_8c7b404ad63c`; worker3 package `job_4e82bb56cb03` | reviewer2 approval-to-run granted; package approval also recorded in `job_c7ebe2d2dade` | Executed exactly once from `/home/bfly/yunwei/test_ccb2`; B7 `classification=pass`; compact ask submitted `job_4181721f9473`; release drained all four resident planning-group agents; cleanup `kill_status: ok`, `state: unmounted`. | [../history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md](../history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_evidence_row.json`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/logs/post_b7_kill_with_roles.stdout` |
| L1-L4 checkpoint/resume runtime attempt | talk2 | reviewer2 `job_7800c403f864`; worker1 package `job_745793b6341f` | reviewer2 approval-to-run granted and superseded old `job_d44bf15c6cb1`; consumed exactly once | `not_claimable` / `test_design_failure`. Materialization and `init` succeeded, then L1 `start-task` failed at `task_create` before provider ask activation: missing project plan root `docs/plantree/plans/phase6b-real-provider-l1-l4`. B7 was written before cleanup; cleanup returned `kill_status: ok`, `state: unmounted`. | [../history/phase6b-real-provider-l1-l4-b7-20260704.md](../history/phase6b-real-provider-l1-l4-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704/phase6b_l1_l4_command_log.jsonl`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704/logs/phase6b-l1-doc-direct-execution__task_create.stderr` |
| L1-L4 repeat2 runtime attempt | talk2 | reviewer2 `job_0c8596e0895d`; worker1 package `job_8d9cad74d6a0` | reviewer2 approval-to-run granted; consumed exactly once | `not_claimable` / `test_design_failure`. Plan-root repair succeeded through L1 `task-create`, task anchors, ready state, and orchestrator activation. `continue-route` then failed before direct execution because the supervisor `orchestration_notes.md` file was outside the lab project root and `plan task-artifact` rejected it. B7 was written before cleanup; cleanup returned `kill_status: ok`, `state: unmounted`. | [../history/phase6b-real-provider-l1-l4-repeat2-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat2-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704/phase6b_l1_l4_command_log.jsonl`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704/logs/phase6b-l1-doc-direct-execution__import_orchestration_notes_direct_execution.stderr`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704/cleanup/post_b7_cleanup.json` |
| L1-L4 repeat3 runtime attempt | talk2 | reviewer2 `job_51a85fa2fc58`; worker1 package `job_5397a044cc0c` | reviewer2 approval-to-run granted; consumed exactly once | `not_claimable` / `test_design_failure`. Plan-root and project-local supervisor imports succeeded through L1/L2 direct execution, L3 `detail_ready`, and L4 macro replan evidence. The final blocked task failed because the driver imported blocker evidence with unknown artifact kind `blocked`; accepted kinds include `blocker_evidence`. B7 was written before cleanup; cleanup returned `kill_status: ok`, `state: unmounted` after rerun with approved lab-local environment. | [../history/phase6b-real-provider-l1-l4-repeat3-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat3-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/phase6b_l1_l4_command_log.jsonl`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/logs/phase6b-l4-blocked-missing-secret__import_blocked.stderr`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704/cleanup/post_b7_cleanup.json` |
| L5 partial-only runtime attempt | talk2 | reviewer2 `job_4e3c051ef168`; worker2 package `job_eeb712e17794` | reviewer2 approval-to-run granted; consumed exactly once | `not_claimable` / `test_design_failure`. Materialization and `init` succeeded, then `start-partial` failed at `task_create` before provider ask activation: missing project plan root `docs/plantree/plans/phase6b-real-provider-l5`. B7 was written before cleanup; cleanup returned `kill_status: ok`, `state: unmounted`. | [../history/phase6b-real-provider-l5-partial-b7-20260704.md](../history/phase6b-real-provider-l5-partial-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704/phase6b_l5_partial_only_command_log.jsonl`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704/logs/phase6b-l5-partial-budget-source-gap__task_create.stderr`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704/cleanup/post_b7_cleanup.json` |
| L5 partial-only repeat2 runtime attempt | talk2 | reviewer2 `job_af5f6fb64a7d`; urgent addendum `job_663bad41c855`; worker2 package `job_e6c576d10c97` | reviewer2 approval-to-run granted; consumed exactly once | `not_claimable` / `test_design_failure`. Plan-root and project-local supervisor imports succeeded through `direct_execution`. The direct-execution round mounted and released dynamic agents, but imported `blocked` with `round_result_source=ask_submission_failed`: plain `ask` from an active CCB task requires `--chain` when the child result is needed, or `--silence` for independent fire-and-forget work. B7 was written before cleanup; cleanup returned `kill_status: ok`, `state: unmounted`. | [../history/phase6b-real-provider-l5-partial-repeat2-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat2-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704/phase6b_l5_partial_only_repeat2_command_log.jsonl`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704/l5-partial-real-provider-lab/.ccb/runtime/loops/lp7b3a34/round_summary.md`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704/cleanup/post_b7_cleanup.json` |
| L5 partial-only repeat3 runtime attempt | talk2 | reviewer2 `job_de6263827473`; worker1 package `job_657112c87bce` | reviewer2 approval-to-run granted; consumed exactly once | `not_claimable` / `test_design_failure`. Current-system provider environment inheritance worked and `direct_execution` ran. The worker ask completed with partial evidence, but reviewer ask submission failed before provider review: `ask --chain requires an active parent job for the sender`. B7 was written before cleanup; cleanup returned `kill_status: ok`, `state: unmounted` after retrying with lab-local `AGENT_ROLES_STORE`. | [../history/phase6b-real-provider-l5-partial-repeat3-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat3-b7-20260704.md); `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704/phase6b_l5_partial_only_repeat3_command_log.jsonl`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704/l5-partial-real-provider-lab/.ccb/runtime/loops/lp0ba040/round_summary.md`; `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704/cleanup/post_b7_cleanup.json` |

## Completed Repair Lane

| Lane | Owner | Job | Review | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| L0 release/drain semantics | worker1 | `job_d239b74ee4a6` | reviewer2 `job_50ce63ab373b` | Accepted. Parked resident agents may be pruned from loop topology authority as `drained_agents` while lifecycle records remain parked/dispatch-disabled; retained-busy priority and non-drained `release_incomplete` remain. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_50ce63ab373b-art_159c32ab43394689.txt`; no runtime/provider/L0 command run. |
| Ask-first child ask chain routing | worker1 | `job_fcb789dab179`; callback `job_19092d158390` | reviewer2 `job_56466011201a` | Accepted. `_submit_and_watch` sets `ParsedAskCommand(callback=True)`, which maps needed-result ask-first child asks to existing CCB chain routing. Authority, topology, submit/watch failure cleanup, partial, and bounded-rework semantics remain bounded by tests. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_56466011201a-art_21f1debeb5a44a6c.txt`; no source-wrapper, provider, L5/L1-L4, runtime, launch, or B7 command run. |
| Ask-first watched child ask runner sender | worker1 | `job_52ec099f6427` | reviewer2 `job_766050825b27` | Accepted. Watched ask-first child asks submit from runner-owned `system` sender with `callback=False`, `silence=False`, and immediate watch. This avoids both repeat3's missing active parent job error and the old plain nested ask rejection. Submit/watch failure cleanup and topology release remain covered. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_766050825b27-art_2c89fbbb8e0f4b4d.txt`; no source-wrapper, provider, L5/L1-L4/L0, runtime, launch, B7, or approval command run. |
| `release_incomplete` classification | worker2/reviewer1 | `job_692502f50c7d`, follow-up `job_3fd8ef33538c`; direct audit `job_ebe46ce6cd8b` | reviewer1 `job_ebe46ce6cd8b` | Accepted. `release_incomplete_agents` plus bounded `release_blockers` classifies as `valid_non_success`; missing, vague, or unbounded blocker evidence remains a hard failure. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ebe46ce6cd8b-art_c895cae3d4ac466f.txt`; no source-wrapper/provider/L0 command run. |

## Completed Planning Lane

| Lane | Owner | Job | Review | Result | Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Phase 6B L1-L4 launch prep | worker3 | `job_5c007d3bab56` | reviewer1 `job_b9eac0af0f9e` | Accepted as planning/readiness prep only; not launch approval. | [phase6b-l1-l4-launch-prep.md](phase6b-l1-l4-launch-prep.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_b9eac0af0f9e-art_973372060e54411a.txt` |
| Phase 6B L1-L4 acceptance checklist | reviewer1 | `job_cca7d14d2fdb` | read-only checklist | Accepted as checklist/readiness artifact only; not launch approval. No checklist blockers. High finding H1: reviewer rework/partial must be a first-class gate. Medium findings: L3 endpoint ambiguity and fixture materialization must be resolved before freezing. Missing goal items to make explicit: B7 reviewer gate, failure taxonomy/human diagnosis, and first stable complexity breakpoint. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_cca7d14d2fdb-art_cca61f8c4b4a46e2.txt`; addendum forwarded to worker3 as `job_6316087b161b`. |
| Phase 6B L1-L4 frozen launch request | worker3 | `job_4b8391dd3a11`; addenda `job_447b42f40abc`, `job_6316087b161b` | reviewer2 `job_c0fac249749e` | `DOC-ONLY ACCEPTED`. Frozen request is reviewable and complete for doc/readiness, but no approval-to-run is granted. Reviewer-rework/partial remains a Phase 6B claim blocker; L3 stops at `detail_ready`; task-specific normalizer fields are now covered by the later hardening lane. | [phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c0fac249749e-art_85be7618d4844d01.txt` |
| Phase 6B L1-L4 normalizer hardening | worker1 | `job_4697fb66db4e`; callback `job_307d5f834a1a` | reviewer2 `job_d023a883a62d` | Accepted as static doc/test hardening only; no launch approval. The embedded B7 normalizer now emits the declared shared and task-specific fields with conservative placeholders. Later worker3 `job_82d723ec0f89` closed the remaining `authority_checks.*` gap. | [phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_d023a883a62d-art_4cc0f39173fa4773.txt`; no runtime/provider command run. |
| Phase 6B L5 reviewer-rework/partial tranche | worker2 | `job_7d3f23d1ff2b`; callback `job_e6456cf4a072` | reviewer2 `job_3824dde8454e` | Accepted as plan-only readiness packet; no runtime and no launch approval. Defines bounded partial candidate `phase6b-l5-partial-budget-source-gap` and bounded reviewer-rework candidate `phase6b-l5-reviewer-bounded-rework-contract`, with artifacts, B7 fields, reviewer contract, stop conditions, and cleanup/residue rules. Later worker3 `job_82d723ec0f89` added an embedded L5 normalizer shape. Residual gaps before launch: exact frozen command/run script and launch-specific approval-to-run. | [phase6b-reviewer-rework-partial-observation-tranche.md](phase6b-reviewer-rework-partial-observation-tranche.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_3824dde8454e-art_f877efe2b9434c4f.txt`; no source-wrapper/provider/runtime command run. |
| Phase 6B static launch normalizer hardening | worker3 | `job_82d723ec0f89` | reviewer2 `job_f20daf37898d` | Accepted as static docs/tests readiness only; no launch approval. L1-L4 embedded normalizer emits conservative `authority_checks.*` booleans, and the L5 tranche has an embedded normalizer shape. Reviewer2 residual risks: L1-L4 checks are heuristics over local files/labels, and L5 still needs a frozen command shape or executable `run_l5.sh` before any approval-to-run. | [phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md); [phase6b-reviewer-rework-partial-observation-tranche.md](phase6b-reviewer-rework-partial-observation-tranche.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f20daf37898d-art_82078d731cc04aa7.txt`; no source-wrapper/provider/runtime command run. |
| Phase 6B active-lane coverage audit | reviewer1 | `job_34d57ea11c3a` | read-only audit | `COVERAGE OK`. No missing Phase 6B acceptance-goal requirement; no accidental launch-approval or runtime-permission wording; no new immediate lane needed. Medium notes: future approval requests must restate L3 is route/detail-only, and worker2 should return a concrete reviewer-rework/partial recommendation or blocker. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_34d57ea11c3a-art_6d7184feba4b4dce.txt` |
| Phase 6B refreshed active-lane coverage audit | reviewer1 | `job_ecea1e97fc6a` | read-only audit | `COVERAGE OK`. The worker1 L1-L4 checkpoint/resume repair lane and worker2 L5 launch-packet lane are sufficient to cover the remaining Phase 6B gates; no accidental runtime authorization, L5/L1-L4 merge, Phase 6B claim, or B7 softening was found. Medium note: the repaired L1-L4 packet must explicitly supersede or revoke held approval `job_d44bf15c6cb1`, not leave "preserve" ambiguous. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ecea1e97fc6a-art_d16242510c594408.txt`; no edits/runtime by reviewer. |
| Phase 6B post-repeat3/repeat2 coverage audit | reviewer1 | `job_e8459a2782cd` | read-only audit | `COVERAGE OK`. The remaining active repair lanes cover the current blockers. Medium notes: repeat3 per-task evidence remains non-claimable unless a reviewer explicitly accepts row separation from the failed tranche; L5 needs fake/unit evidence before any new approval; update the board so consumed roots are not reused. | `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_e8459a2782cd-art_05471952a50b4d6e.txt`; no edits/runtime by reviewer. |
| Phase 6B L1-L4 approval packet | worker1 | `job_0e204d68a674`; callback `job_745793b6341f` | reviewer2 `job_d44bf15c6cb1` | `APPROVAL-TO-RUN GRANTED` for exactly one future supervised L1-L4 run, but talk2 held execution during pre-run audit. The frozen script calls `activate_orchestrator_and_stop`, then immediately requires `supervisor_imports/<task>/route.txt`; the root freshness guard prevents pre-seeding checkpoint files and no resume entrypoint is defined. Approval remains unconsumed until repaired or superseded. | [phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_d44bf15c6cb1-art_d04f4c04780544c1.txt`; no runtime/provider command run. |
| Phase 6B L1-L4 checkpoint/resume approval packet | worker1 | `job_d21db63841cd`; callback `job_465b7a7b8425` | reviewer2 `job_7800c403f864` | `APPROVAL-TO-RUN GRANTED`; explicitly superseded and invalidated old `job_d44bf15c6cb1`. Talk2 consumed it once; see completed runtime lane. The packet repaired checkpoint/resume mechanics but missed project plan-root materialization before `task-create`. | [phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md); `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_7800c403f864-art_5c4ccc3dca374a7f.txt`; runtime evidence in [../history/phase6b-real-provider-l1-l4-b7-20260704.md](../history/phase6b-real-provider-l1-l4-b7-20260704.md). |

## L1-L4 Package Checklist

For any later L1-L4 packet revision or launch-specific approval-to-run audit,
accept the package only if it proves all of the following without running an
unapproved provider/runtime command:

- Status is unambiguously `DO NOT RUN` unless reviewer2 explicitly grants a
  launch-specific approval-to-run in the same artifact.
- The proposed root is fresh, external, under `/home/bfly/yunwei/test_ccb2`, and
  does not reuse the repeat6 L0 root.
- The task sequence is explicit: which L1, L2, L3 `needs_detail`, L4
  `macro_adjustment_request`, and L4 `blocked` candidates are included, and
  whether the approval request covers all tasks or a smaller tranche.
- The Phase 6B real-capability requirement to observe at least one reviewer
  rework or partial result is either covered by a concrete task/case with
  expected artifacts and B7 fields, or explicitly remains a blocker that
  prevents a Phase 6B claim.
- The L3 endpoint is not ambiguous: the package says whether L3 proceeds to
  full direct execution after detail readiness or stops at route-only
  `detail_ready` as valid non-success.
- Fixture generation/materialization is exact and lab-local, with paths and
  expected initial/final evidence surfaces.
- Command shape uses `/home/bfly/yunwei/ccb_source/ccb_test` from an external
  root, a materialized stdin-safe script, command logs, per-task evidence rows,
  and a B7 aggregation report path.
- Every supervisor artifact that the command passes to
  `plan task-artifact --file` lives inside the lab project root, not only the
  outer lab root. This includes route notes, detail summaries/design packets,
  macro-adjustment evidence, blocker evidence, terminal evidence, and round
  summaries.
- Static extraction tests prove the embedded driver cannot construct
  `plan task-artifact --file` paths outside the lab project root, and include a
  regression assertion for the observed error text
  `plan artifact file must be inside project root`.
- B7 schema covers route correctness, detailer activation, worker/reviewer ask
  evidence, reviewer contract citation, round result import, cleanup/residue
  classification, authority audit, and topology audit.
- B7 report path and independent reviewer gate are named before launch; B7 must
  include failure taxonomy, human diagnosis for every non-pass row, and first
  observed task-complexity breakpoint or `unknown` with evidence.
- Provider map and provider-environment policy are explicit: real-provider
  runs inherit the current system provider environment, do not export lab-local
  `HOME` or `CCB_SOURCE_HOME`, and keep lab-local `AGENT_ROLES_STORE` plus
  RolePack seeding unless reviewer-approved otherwise.
- The package states that repeat6 is L0-only pass evidence and that no L1-L4,
  L1-L5, Phase 6B completion, or production/default enablement is claimed.

## Worker2 L5 Callback Acceptance Checklist

When worker2 `job_7d3f23d1ff2b` returns, accept the callback only if the full
reply and reviewer artifact prove all of the following:

- Verdict is planning/readiness acceptance or a concrete blocker. It must not
  request or grant launch approval, and it must not report any source-wrapper,
  `ccb_test`, provider, L0-L5, or runtime command.
- The packet remains separate from the frozen L1-L4 request unless a later
  launch-specific reviewer verdict explicitly combines them.
- At least one concrete future observation path is present for the Phase 6B
  requirement "reviewer rework or partial": a bounded partial candidate, a
  bounded reviewer-rework candidate, or a reviewed blocker explaining why no
  valid observation can be planned yet.
- The packet defines expected route, round result, final status,
  classification, human diagnosis, artifacts, B7 row fields, cleanup/residue
  evidence, and stop conditions for the selected candidate or tranche.
- The launch driver creates or copies every supervisor route, round, partial,
  blocker, or terminal evidence file passed to `plan task-artifact --file`
  inside the lab project root, and static tests prove no import path points to
  only the outer lab root.
- The static test suite includes a regression assertion for
  `plan artifact file must be inside project root` so the L5 repeat cannot
  reproduce the L1-L4 repeat2 failure after plan-root initialization succeeds.
- The L5 embedded B7 normalizer emits `observed_route=direct_execution` for the
  partial fixture when route evidence exists in the approved project-root-local
  location; the current known regression is
  `test_phase6b_l5_b7_normalizer_emits_declared_schema_for_partial` producing
  `observed_route=unknown`.
- Partial cannot be marked `done`: completed and unfinished steps must be
  explicit, and missing-source or bounded-blocker evidence must be preserved.
- Reviewer rework cannot hide retries: rework attempt count and limit must be
  explicit, and a second rejection must stop and classify from evidence.
- B7 fields must cover reviewer-rework/partial-specific evidence plus the
  normal authority/topology audit surface, including `topology_dispatch`
  absence, communication-edge absence, provider-reply authority parsing
  absence, script-owned imports, runtime residue, and bounded release blockers.
- The callback must state that the packet is not accepted runtime evidence and
  does not satisfy Phase 6B until a future launch-specific run produces
  reviewer-gated B7 rows.

## Worker3 Normalizer Callback Acceptance Record

Worker3 `job_82d723ec0f89` returned with reviewer2 `job_f20daf37898d`
acceptance. The callback and reviewer2 artifact satisfy the intended checks:

- Verdict is static hardening acceptance or a concrete blocker. It must not
  request or grant launch approval, and it must not report any source-wrapper,
  `ccb_test`, provider, L0-L5, or runtime command.
- The L1-L4 embedded normalizer emits the declared `authority_checks.*`
  booleans:
  `topology_dispatch_absent`, `communication_edges_absent`,
  `provider_reply_authority_parsing_absent`, `script_owned_route_imports`,
  `script_owned_round_imports`, and `no_source_checkout_edits`.
- The L1-L4 normalizer keeps placeholders conservative and does not let
  `authority_checks.*` alone create pass evidence.
- The accepted L5 reviewer-rework/partial tranche has a reviewable executable
  normalizer or launch-packet normalizer shape that emits all shared and
  L5-specific B7 fields, including rework attempt counts, partial completed and
  unfinished steps, provider format drift, topology/authority booleans,
  release blockers, and release-incomplete agents.
- Static tests or extraction checks prove the documented schema and embedded
  normalizer output do not drift.
- Nearby status/index docs stated at that time that the work remained
  plan/doc/test readiness only. Current active status now points to the
  2026-07-05 final aggregation for the bounded Phase 6B claim and keeps future
  real-provider runs behind fresh root/launch decisions.

## Worker1 L1-L4 Approval-Packet Callback Checklist

When worker1 `job_0e204d68a674` returns, accept the callback only if the full
reply and reviewer2 artifact prove one of these outcomes:

- `APPROVAL-TO-RUN GRANTED` for the exact L1-L4 packet;
- `DOC-ONLY ACCEPTED` / readiness accepted without runtime approval;
- concrete blockers that stop approval.

For any approval-to-run verdict, do not execute immediately. First audit that
the reviewer2 artifact and packet name all of the following:

- exact fresh root under `/home/bfly/yunwei/test_ccb2`, not the consumed L0
  repeat6 root;
- exact command shape, materialized script path, script sha evidence path,
  command log path, evidence rows path, and B7 report path;
- exact task tranche, limited to L1, L2, L3 `needs_detail`, L4
  `macro_adjustment_request`, and L4 `blocked`;
- L3 endpoint remains route/detail-only `detail_ready`, with no post-detail
  execution claim;
- L5 reviewer-rework/partial remains outside this approval and still blocks a
  Phase 6B claim;
- provider map, current-system provider environment inheritance, no lab-local
  `HOME` / `CCB_SOURCE_HOME` override, lab-local `AGENT_ROLES_STORE`, and
  RolePack seeding are explicit;
- accepted `authority_checks.*` and B7 normalizer behavior from reviewer2
  `job_f20daf37898d` are preserved;
- stop conditions include source checkout misuse, topology communication DSL,
  provider-reply authority mutation, unbounded runtime residue, and any
  blocked/partial work marked `done`.

Reject or hold the callback if worker1 reports running source-wrapper,
`ccb_test`, provider, L0/L1-L4/L5, runtime, or launch commands. If approval is
granted, talk2 must perform a separate pre-run audit before executing anything.

## Worker1 Checkpoint/Resume Repair Callback Checklist

When worker1 `job_d21db63841cd` returns, accept the callback only if the full
reply and reviewer2 artifact prove one of these outcomes:

- `APPROVAL-TO-RUN GRANTED` for a repaired exact L1-L4 command shape;
- `DOC-ONLY ACCEPTED` / readiness accepted without runtime approval;
- concrete blockers that stop approval.

Before treating any approval as runnable, audit that the repaired packet:

- explicitly supersedes or revokes the held `job_d44bf15c6cb1` approval; do
  not accept wording that merely says the old approval might be preserved;
- defines an executable continuation path for every supervisor checkpoint,
  including route imports for L1/L2/L3/L4, L3 detail imports, and terminal L4
  macro/blocked imports;
- does not require pre-seeding checkpoint files into a non-empty root that the
  freshness guard would reject;
- keeps the materialized-script shape and avoids stdin piping;
- keeps the exact L1, L2, L3 `needs_detail` to `detail_ready`, L4
  `macro_adjustment_request`, and L4 `blocked` tranche; L5 remains excluded;
- preserves provider map, current-system provider environment inheritance,
  lab-local RolePack seeding, accepted `authority_checks.*`, script-owned
  imports, no topology dispatch, and no provider-reply authority mutation;
- includes static tests or extraction checks that would fail for the previous
  immediate-checkpoint-exit shape;
- reports no source-wrapper, `ccb_test`, provider, L0/L1-L4/L5, runtime, or
  launch command execution by worker1.

If approval is granted, talk2 must still run a separate pre-run audit against
the exact reviewer2 artifact, root freshness, command shape, and continuation
procedure before executing anything.

## Worker2 L5 Launch-Packet Callback Checklist

When worker2 `job_d11d3c062959` or addenda `job_2e0f6e9cec8a` /
`job_857205f05fb4` returns, accept the callback only if the full reply and
reviewer2 artifact prove one of these outcomes:

- `APPROVAL-TO-RUN GRANTED` for an exact L5 reviewer-rework/partial command
  shape;
- `DOC-ONLY ACCEPTED` / readiness accepted without runtime approval;
- concrete blockers that stop approval.

Before treating any approval as runnable, audit that the L5 packet:

- uses a fresh external root under `/home/bfly/yunwei/test_ccb2` and does not
  reuse L0 repeat6 or any L1-L4 root;
- names whether the approved tranche is partial-only, reviewer-rework-only, or
  an ordered bounded sequence, with exact stop conditions;
- keeps L1-L4 separate unless reviewer2 explicitly approves a combined future
  packet;
- includes a materialized stdin-safe script, command log, script sha path,
  supervisor import paths, row path, B7 path, cleanup path, and exact
  normalizer command shape;
- creates or copies every supervisor route, round, partial, blocker, or
  terminal evidence file passed to `plan task-artifact --file` inside the lab
  project root, with static checks that would fail for outer-root-only import
  paths;
- emits every shared B7 field and every L5-specific field from the accepted
  tranche, including rework attempt count/limit, partial completed and
  unfinished steps, topology/authority booleans, release blockers, and
  `release_incomplete_agents`;
- preserves provider policy: `ccb_round_reviewer` uses `claude`, the rest use
  `codex`, real-provider runs inherit the current system provider environment
  without lab-local `HOME` / `CCB_SOURCE_HOME` overrides, and RolePacks are
  seeded lab-locally;
- preserves script/supervisor-owned authority imports, no topology dispatch,
  no topology communication DSL, and no provider-reply authority parsing;
- reports no source-wrapper, `ccb_test`, provider, L0/L1-L4/L5, runtime, or
  launch command execution by worker2.

If approval is granted, talk2 must still run a separate pre-run audit against
the exact reviewer2 artifact, root freshness, command shape, task tranche, and
B7 normalization procedure before executing anything.

## Future Runtime Approval Preflight

Use this checklist only after a worker callback includes a fresh reviewer2
`APPROVAL-TO-RUN GRANTED` artifact. It does not authorize runtime by itself.

Before running any approved command, talk2 must verify:

- the full reviewer2 artifact was read and names the exact root, task tranche,
  command shape, script path, script sha path, command log path, evidence row
  path, B7 report path, cleanup path, and stop conditions;
- the root is still absent or empty immediately before execution and lives
  under `/home/bfly/yunwei/test_ccb2`;
- the command runs from `/home/bfly/yunwei/test_ccb2`, uses the absolute
  `/home/bfly/yunwei/ccb_source/ccb_test` wrapper, and materializes then runs a
  script with `bash "$SCRIPT"` rather than stdin piping;
- provider environment matches the owner decision and approval: no lab-local
  `HOME` or `CCB_SOURCE_HOME` override for real-provider runs, current system
  provider environment is inherited, and lab-local `AGENT_ROLES_STORE` remains
  explicit if the packet uses one;
- the approved task tranche matches the lane: L1-L4 repair approval must
  explicitly supersede or revoke held `job_d44bf15c6cb1`, while L5 approval
  must remain separate from L1-L4 unless reviewer2 explicitly approves a
  combined run;
- authority boundaries are preserved: script/supervisor-owned route, detail,
  blocker, macro, round, and status imports; provider replies are evidence
  only; no `--consume-role-output`, topology dispatch, or topology
  communication DSL;
- B7 rows cover the goal-required evidence for that tranche, including route
  correctness, reviewer contract citation, cleanup/residue, failure taxonomy,
  human diagnosis for non-pass rows, and the relevant L3/L4/L5-specific fields;
- B7 is written and reviewed before cleanup evidence is destroyed, then
  post-B7 cleanup is run and recorded;
- no Phase 6B claim is made after L1-L4 alone, after L5 alone, or before the
  claim coverage matrix shows all goal requirements have reviewer-gated
  evidence.

If any preflight item fails, do not run the command. Record the blocker and
request a repaired packet or reviewer clarification.

## Acceptance Gates

- Do not run L0 again without a fresh launch-specific reviewer approval. The
  repeat6 run proved the new drained-release path for L0 runtime sanity, but
  that one-run approval is consumed.
- Do not treat L1-L4 launch-request preparation as launch approval. The frozen
  request is doc-only accepted, but may not run unless reviewer2 explicitly
  grants launch-specific approval-to-run for a fresh root and exact command
  shape.
- L0 gates are resolved for runtime sanity, but L1-L4 still need reviewer gate
  acceptance. The frozen request now selects the first sequence, fixes the L3
  endpoint at `detail_ready`, and materializes fixture hashes/paths; it remains
  `DO NOT RUN` unless reviewer2 explicitly grants approval-to-run for the exact
  root and command shape.
- Do not claim Phase 6B until the real-provider lab meets the
  [Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md)
  requirements: L0-L4 evidence, L0/L1/L2 basic executable tasks, at least one
  L3 `needs_detail`, at least one blocked or macro-adjustment termination, at
  least one reviewer rework or partial observation, and reviewer-gated B7.

## Forbidden During Active Lanes

- No unapproved real-provider or L0-L4 runtime commands.
- No fake `released` state while agents remain active.
- No topology communication DSL, `topology_dispatch.json` mainline revival, or
  provider-reply authority parsing.
- No deletion of runtime evidence to hide residue.
- No broad implementation work in the supervision lane.

## Callback Handling

When a worker callback arrives, audit it against this board and the relevant
review artifact before updating claim state. If a worker reports only partial
progress, keep the lane open and record the narrowed blocker.

Reviewer2 `job_8c7b404ad63c` returned `APPROVAL-TO-RUN GRANTED`; talk2 read
the artifact, confirmed the repeat6 root and command shape, ran the one
approved B-only L0 sequence, generated B7 evidence before cleanup, then ran
post-B7 cleanup. Future callbacks should not reuse that approval.

Worker3 `job_4b8391dd3a11` has returned with reviewer2
`DOC-ONLY ACCEPTED` in `job_c0fac249749e`; no runtime approval was granted.
The next callback pattern to watch for is a separate launch-specific
approval-to-run audit. If such an approval arrives, first read the full
artifact and confirm it names the exact fresh root, task tranche, and command
shape before running anything.

Reviewer1 `job_cca7d14d2fdb` returned a checklist/readiness artifact only. It
does not approve runtime. Talk2 forwarded its findings to worker3 as addendum
`job_6316087b161b`; use that checklist to audit any later reviewer2
approval-to-run artifact before executing a real-provider command.

Worker3 addenda `job_447b42f40abc` and `job_6316087b161b` reported that the
checklist points were incorporated before reviewer2 review. Reviewer2
`job_c0fac249749e` then returned `DOC-ONLY ACCEPTED`: the launch packet is
reviewable, but no runtime is approved and Phase 6B remains blocked by missing
runtime evidence plus missing reviewer rework/partial observation.

Worker1 returned callback `job_307d5f834a1a` for the static L1-L4
normalizer/schema hardening lane, and reviewer2 accepted it in
`job_d023a883a62d`. This closes the declared task-specific field drift without
granting runtime approval. The follow-up worker3 lane `job_82d723ec0f89`
addresses the `authority_checks.*` boolean set noted by reviewer2, and
reviewer2 accepted it in `job_f20daf37898d` as static hardening only.

Worker2 returned callback `job_e6456cf4a072` for the reviewed
reviewer-rework/partial plan-only tranche. Reviewer2 accepted it in
`job_3824dde8454e`: the packet is sufficient planning readiness for a future
L5 observation tranche, but grants no runtime approval and includes no
executable command or B7 normalizer.

Reviewer1 returned `COVERAGE OK` for read-only audit `job_34d57ea11c3a`: all
Phase 6B acceptance-goal items are represented by current evidence, active
lanes, or explicit pending gates. Worker1's normalizer callback and worker2's
L5 planning callback are now accepted. Worker3's static
launch-packet/normalizer hardening callback is also accepted. Do not request
launch approval or run real-provider/runtime commands without a fresh reviewer
verdict.

Talk2 submitted worker1 `job_0e204d68a674` to prepare a launch-specific L1-L4
approval-to-run packet and have reviewer2 audit it. This active lane is
request preparation only: if approval is granted, the command must not be run
until talk2 reads the full reviewer artifact and confirms the exact approved
root, task tranche, and command shape.

## 2026-07-07 Current Effective Gate

The current deployment-readiness lane has moved past launch-packet approval
reviews and is blocked on real frontdesk-started behavior.

- Latest route-mix real run evidence is worker2 `job_e8f28dbc52f5`:
  `invalid_harness`. It proves resident-idle preflight, natural-language
  frontdesk entry, automatic planner handoff, and real planner activation, but
  planner returned one controller-owned validation meta task instead of the
  intended L1-L4 task set. No claimable B7/rows were produced.
- The source contract still asks planner for one `task-packet.md` plus one
  `readiness.json`; current code inspection shows no accepted `task-set`
  schema yet. This is a product contract blocker for multi-task/route-mix
  workflows, not a reporting issue.
- worker2 `job_d54ea15ed764` failed with `pane_dead` and a zero-byte artifact;
  it is invalid worker evidence. The follow-up source-only repair
  `job_d67e88548023` now passes the focused invalid-harness regression and
  hardens the runner/B7 path. A later retry request `job_fa7e24e69871`
  failed again with a zero-byte artifact and is not evidence.
- worker3 `job_4666f8642b59` completed file-only evidence audit and confirms
  none of the visible roots is deployment-readiness pass evidence. worker1 is
  blocked by missing plan root in the first observed handoff path, worker2 is
  non-claimable because the route matrix collapsed into a meta task, and
  worker3 is invalid due stale sequence37 root reuse. UI/sidebar evidence is
  still unproven.
- worker1 `job_8ee629a6634f` completed source repair and is accepted for the
  multi-task handoff contract only. The focused source tests pass, but this is
  not deployment readiness evidence.

Do not claim deployment readiness or run another broad real-provider stress
lane until the source contract and runner evidence hardening land, pass source
tests, and a fresh real-provider rerun proves frontdesk intake through planner
decomposition, route execution/review, dynamic-agent release, and B7 rows
before cleanup.
