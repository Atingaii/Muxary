# Archived Agentic Loop Workflow Implementation Status

Archived: 2026-07-10
Superseded by: [../implementation-status.md](../implementation-status.md)

This file preserves the accumulated Phase 1-6, deployment-readiness,
real-provider, provider-backend, UI/lifecycle, and early G1 status log that
previously occupied the active handoff file. It is historical evidence, not
the current execution queue. The snapshot below is otherwise preserved.

Date: 2026-07-10

## Current Phase

The workflow kernel is now beyond pure planning. The current source tree has
accepted Phase 3A orchestrator triage and an accepted Phase 4A
direct-execution ask-first round for the narrow fake-provider path. Phase 5A
failure cleanup and Phase 5 lifecycle closure are accepted with residual risk.
The Phase 6A fake-provider, single-round program-matrix scope is accepted after
the residue-clean integrated source-wrapper matrix and module/claim-boundary
reviews. Phase 6B is now claimable for initial real-provider, single-round
capability after `talk2` final aggregation on 2026-07-05:
L0 repeat6 is `pass`, L1-L4 repeat12 is `Status: pass` with all five rows
claimable, and L5 partial repeat4 is `valid_non_success` with partial
observation. The final acceptance report is
[history/phase1-6-acceptance-report-20260705.md](phase1-6-acceptance-report-20260705.md).
Production/default enablement, post-detail execution, reviewer-rework
stability, long-running multi-round workflows, arbitrary workflow authoring,
and final source-control packaging remain outside that bounded Phase 6 claim.

The active post-baseline release target is now
[goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md).
It keeps one Workflow Lane but replaces the scalar single-pair engine with one
orchestration bundle driving one to four Git-isolated `Worker + Reviewer`
workgroups, deterministic reviewed integration, project-root verification and
rollback, exact-once recovery, and complete dynamic release. Config V3 is part
of the same release gate; Config V2 remains the static compatibility contract.
No multi-lane scheduler implementation or package publication starts before
this goal's source/fake/visible-real/package gates pass.

Post-acceptance deployment readiness is a separate active gate at
[topics/phase1-6-deployment-readiness-supervision-20260707.md](../topics/phase1-6-deployment-readiness-supervision-20260707.md).
Current operator-facing acceptance policy: final deployment-readiness testing
must be run from a real opened project under `/home/bfly/yunwei/test_ccb2`
using `/home/bfly/yunwei/ccb_source/ccb_test`, with inherited system provider
environment when testing real Codex/Claude behavior, a lab-local
`AGENT_ROLES_STORE`, visible UI/pane state for user or supervisor inspection,
and frontdesk-started handoff through planner/orchestrator. Scripted B7 rows
are required evidence, but they are not sufficient by themselves; if hidden
script output contradicts visible project state or raw task/loop authority,
the normalizer is the bug.

## 2026-07-10 G1 Orchestration Bundle Foundation

Commit `34027943` lands the first G1 implementation slice: strict
one-to-four-node orchestration-bundle validation, script-owned task artifact
import, canonical work packets and digests, deterministic ordering, explicit
orchestrator fenced-candidate import, a deterministic one-node compatibility
bundle, and canonical `nodes.node-001` pending/final evidence. Multi-node
bundles deliberately pause before loop binding or ask submission because the
ready-frontier scheduler and Git integration kernel are not landed.

Direct `talk2` verification passed the 209-test bundle/plan/loop/topology set
and the non-Gemini repository gate (`3868 passed, 2 skipped, 124 deselected`).
The unrestricted run had `3988 passed, 2 skipped, 4 failed`; all four failures
are existing Gemini restart-timing blackbox cases and remain recorded rather
than hidden. G1 is not complete: task-revision/capacity binding, sole
node-state execution, node-keyed exact-once intent, and removal of the normal
post-worker orchestrator call are still required. Evidence:
[history/single-lane-multi-workgroup-g1-foundation-20260710.md](single-lane-multi-workgroup-g1-foundation-20260710.md).

## 2026-07-10 Visible Multi-Round Checkpoint

`talk2` directly completed a three-task, three-loop real-provider run in the
opened project
`/home/bfly/yunwei/test_ccb2/workflow-window-e2e-talk2-20260710-093408`.
All tasks reached `done/pass`; every execution loop released four dynamic
roles with zero retained; `ccb-exec` was removed after each round; resident
frontdesk and planner panes remained visible. The run exposed and fixed static
route-target activation plus two Claude post-`/clear` session-selection bugs.
Current workflow-branch commits are `c845c8f2`, `7a134400`, and `df164fb1`.
Direct verification: provider/session suite `92 passed`, project suite
`12 passed`, config valid, final loop topologies empty. Evidence:
[history/visible-three-round-dynamic-window-e2e-20260710.md](visible-three-round-dynamic-window-e2e-20260710.md).
The project remains mounted for inspection; no release was published and
production/default enablement remains a separate decision.

## 2026-07-10 Five-Task Resilience Checkpoint

The same visible project later completed five additional planner tasks, each
`done/pass` with fresh coder, code reviewer, orchestrator, and round reviewer
capacity released `4/0`. Direct acceptance passed 32 product tests. A real
planner job survived an in-flight ccbd restart with the same job and pane PID,
and a separate dynamic Claude mount proved correct sidebar state, private
session persistence, and release `1/0`. The run exposed and repaired current
turn frontdesk request binding, seed-job authority, Codex readiness, same-live
runtime restore, bounded Claude result recovery, Claude sidebar false failure,
and provider-session file permissions. Evidence and remaining secure
credential-rehydration limits are recorded in
[history/visible-five-task-workflow-resilience-e2e-20260710.md](visible-five-task-workflow-resilience-e2e-20260710.md).
The project remains mounted; release publication and production/default
enablement remain separate gates.

2026-07-08 talk2 checkpoint: the latest source tree is locally test-clean
after the sequence29/frontdesk/detailer/B7 fixes and the phase2 provider
blackbox environment-isolation regression. Verified:
`python -m pytest -q` -> `3902 passed, 2 skipped`; focused provider blackbox
`test/test_v2_phase2_entrypoint.py -m provider_blackbox -q` -> `21 passed`;
full phase2 entrypoint -> `77 passed`; py_compile on touched source/tests
passed; `git diff --check` passed. reviewer1 `job_8657be7ac70f` independently
accepted source/doc readiness for the next real-provider validation lanes, with no
blocking source/doc repair required; it noted Phase 6B-specific role-output
import coupling as technical debt, not a blocker. This is source/local
verification only, not deployment readiness. The next supervised work must be
executed directly by `talk2` from the Phase 1-6 goal into fresh real-provider
opened-project validation lanes: L1-L4 frontdesk route-mix rerun,
dynamic unload/busy-retain/UI rerun, and raw evidence versus B7 audit. Per the
user's 2026-07-08 direction, workers/reviewers are no longer used for
validation; only concrete code-modification tasks should be delegated.
2026-07-08 talk2 self-run evidence: `talk2` directly executed the fresh
real-provider L1-L4 frontdesk route-mix lane from
`/home/bfly/yunwei/test_ccb2` with `/home/bfly/yunwei/ccb_source/ccb_test`,
inherited system provider environment, and lab-local `AGENT_ROLES_STORE`.
Fresh root:
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814`.
B7:
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/phase6b-real-provider-l1-l4-sequence38-talk2-selfrun-20260708124814-b7.md`
reports `Status: pass`: L1 and L2 reached `direct_execution -> done/pass`
with `released_count=2`, `retained_count=0`, `dynamic_unload_ok=true`, and
`runtime_residue=false`; L3 reached `needs_detail -> detail_ready`; L4 macro
reached `macro_adjustment_request -> replan_required`; L4 blocked reached
`blocked -> blocked`. Frontdesk automatically handed off to planner, planner
produced the five-task route mix, all rows are `claimable_row=true`, and
provider-reply authority parsing is absent. Post-B7 cleanup was run with the
same root-local role store; final `ps` shows `ccbd_state: unmounted` and all
resident roles stopped. This closes the L1-L4 route-mix validation lane for
the current source tree. Deployment readiness remains open for dynamic
lifecycle/busy-retain/UI/sidebar pressure evidence and final packaging.
Next production-target queue is tracked in
[topics/phase1-6-deployment-readiness-supervision-20260707.md](../topics/phase1-6-deployment-readiness-supervision-20260707.md):
P0 freeze current baseline and evidence paths; P1 run dynamic lifecycle,
busy-retain, sidebar/UI, observer-timeout validation from a fresh visible
project; P2 run frontdesk pressure across complexity levels and valid
non-success outcomes; P3 complete the six-module audit from the Phase 1-6 goal;
P4 produce the final deployment-readiness report; P5 run source hygiene,
worktree/branch packaging, and install/update smoke checks. Validation remains
`talk2` direct-owned; delegate only concrete source fixes discovered by those
lanes.
2026-07-08 config-v3 follow-up: user requested a new opt-in
`version = 3` dynamic workflow config while preserving `version = 2` static
layout for users who prefer manual agent/window placement. `ccb_self`
`job_a398feb91b6d` produced design input, now summarized in
[topics/config-v3-dynamic-workflow.md](../topics/config-v3-dynamic-workflow.md).
The next source lane should first implement schema/version dispatch and
`ccb config validate` support for v3, with v2 regression protection, required
workflow role checks, rolepack/provider/model validation, and migration
dry-run planning. 2026-07-08 update: the same lane now includes an enhanced
control-panel direction for config editing, but implementation should start
with shared CLI/control-plane JSON contracts, not a separate UI authority.
`odesign` reviewed the panel direction in `job_669f39f1971f`; the adopted
framing is a config preparation workflow with digest-aware Draft/Saved/
Validated/Dry-run/Reloaded states, locked required role/capacity rows, and an
MVP read-only-to-gated-edit rollout.
2026-07-08 v2 static panel follow-up: `odesign` produced a separate v2 static
layout control panel demo design in `job_f9100b2ffd30`, now captured in
[topics/config-v2-static-control-panel.md](../topics/config-v2-static-control-panel.md).
This v2 surface is a static `[windows]` layout preparation workflow with a
visual split builder, template picker, pane inspector, folded overlays, tool
window/sidebar secondary sections, compact layout preview, and the same
digest-aware validate/dry-run/apply gates.
This is a design/source lane, not deployment-readiness evidence by itself.
Runtime proof must still use a visible opened project under
`/home/bfly/yunwei/test_ccb2` after parser, validation, and control-contract
tests pass.
2026-07-08 P0 baseline freeze: talk2 recorded the deployment-readiness
baseline in
[history/phase1-6-deployment-readiness-p0-baseline-20260708.md](phase1-6-deployment-readiness-p0-baseline-20260708.md).
The baseline fixes the explicit source `ccb_test` path, test root, dirty
worktree state, global role-store exclusion, current sequence38 B7 anchor, and
fresh-root naming rules for P1/P2. This is setup evidence only; next production
target is P1 dynamic lifecycle/busy-retain/UI/sidebar real-project validation.
2026-07-08 P1 dynamic lifecycle pass: talk2 directly executed the P1 lane from
`/home/bfly/yunwei/test_ccb2` against fresh visible root
`/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320`
with `/home/bfly/yunwei/ccb_source/ccb_test`, inherited system provider
environment, and root-local `AGENT_ROLES_STORE`. B7:
`/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/p1-dynamic-lifecycle-b7.md`
returned `status: pass`. Evidence summary:
[history/phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md](phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md).
Three real direct-execution rounds, including L3 post-detail execution, reached
`done/pass` and each released dynamic coder/reviewer nodes with
`released_count=2`, `retained_count=0`, and observed topology `agents=[]`.
Positive busy-retain with a real Codex dynamic coder returned
`retained_busy` while active and `released` after idle. A real explicit
observer-timeout diagnostic returned `command_status: failed` /
`watch timed out`, then completed normally under a longer watch and released
cleanly. Resident frontdesk/planner/orchestrator/task_detailer/
`ccb_round_reviewer` panes remained visible in the fresh project. P1 is closed;
P2 frontdesk pressure is the next deployment-readiness lane.
2026-07-08 P2 frontdesk pressure pass: talk2 directly executed the P2
macro-intake pressure lane from `/home/bfly/yunwei/test_ccb2` against fresh
visible root
`/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920`
with `/home/bfly/yunwei/ccb_source/ccb_test`, inherited system provider
environment, and root-local `AGENT_ROLES_STORE`. B7:
`/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920/phase6b-real-provider-l1-l4-p2-frontdesk-pressure-talk2-20260708170920-b7.md`
returned `Status: pass`. Evidence summary:
[history/phase1-6-deployment-readiness-p2-frontdesk-pressure-20260708.md](phase1-6-deployment-readiness-p2-frontdesk-pressure-20260708.md).
One natural-language frontdesk macro-intake produced five route-mix tasks.
Frontdesk returned Intake Evidence only, exactly one handoff marker was
created, planner received one silence ask and returned a fenced
`task-set.json`, L1/L2 direct execution ended `done/pass` with
`released_count=2`, `retained_count=0`, and no active dynamic residue, while
L3/L4 valid non-success rows were classified as `valid_non_success`.
Post-B7 cleanup returned `ccbd_state: unmounted`. This closes the P2
macro-intake pressure lane; a five-independent-frontdesk-message P2-B remains
an optional stricter shape if later required. P3 module-level audit was
completed next and is recorded below.
2026-07-08 P3 module-level audit complete: talk2 directly audited the six
Phase 1-6 modules against current P0/P1/P2 evidence and recorded
`PASS_WITH_LIMITS` in
[history/phase1-6-deployment-readiness-p3-module-audit-20260708.md](phase1-6-deployment-readiness-p3-module-audit-20260708.md).
The audit verified current direct evidence for task artifact traceability,
route/outcome matching across direct/detail/macro/blocked, mount-only topology
without communication DSL keys, provider-reply authority parsing absence,
dynamic release/busy-retain/resident visibility/final cleanup, and row/B7
classification consistency. Limits carried to P4: current P1/P2 did not rerun
partial or reviewer-rework, did not inject every live ask submit/watch failure,
did not independently rerun every historical park/resume/reflow case, and did
not run five independent frontdesk user-message pressure cases. Historical L5
partial and Phase 6A reviewer-rework evidence are accepted only as bounded
supplement. P4 final report was completed next and is recorded below.
2026-07-08 P4 deployment-readiness report complete:
[history/phase1-6-deployment-readiness-report-20260708.md](phase1-6-deployment-readiness-report-20260708.md).
Verdict is now `REPORT_COMPLETE / P5_SOURCE_GATE_PASSED /
RELEASE_NOT_PUBLISHED / PRODUCTION_DEFAULT_NOT_ENABLED`. The report summarizes
sequence38, P1, P2, P3, P5, module verdicts, failure taxonomy, first stable L5
partial breakpoint, unresolved blockers, explicit non-goals, and package-owner
release priorities. Current source is ready for package-owner staging/release
decisions. Production/default enablement remains blocked until an explicit
release artifact/update smoke and deployment policy decision exist.
2026-07-08 P4 post-fix fullflow retest: talk2 directly reproduced and fixed a
real-provider L3 `needs_detail` stop-contract bug. The task_detailer returned
complete detail artifacts and `controller_expected_stop: detail_ready`, but
the importer previously blocked because the reply also used
`detail readiness recommendation: needs_clarification`. The source fix now
honors the controller-visible detail-ready stop contract only when the
activation explicitly carries `detail_ready_stop_contract.status=detail_ready`.
Fresh retest root:
`/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901`.
B7:
`/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901/phase6b-real-provider-l1-l4-deploy-fullflow-talk2-selfrun-20260708202901-b7.md`
reports `Status: pass`: L1/L2 direct rows reached `done/pass` with
`released_count=2`, `retained_count=0`, `dynamic_unload_ok=true`, and
`runtime_residue=false`; L3 reached `detail_ready`; L4 macro reached
`replan_required`; L4 blocked reached `blocked`; all five rows are claimable.
Post-B7 cleanup stopped the project-local ccbd/tmux/provider processes, and a
follow-up `ps` showed no target-project runtime residue. Verified after the
source repair: focused task-detailer/route tests `13 passed`, broad
`test_loop_capacity_cli.py test/test_plan_tasks_cli.py` `150 passed`,
py_compile passed, and `git diff --check` was clean for the touched
source/test files.
2026-07-08 P5 source packaging gate complete:
[history/phase1-6-deployment-readiness-p5-packaging-gate-20260708.md](phase1-6-deployment-readiness-p5-packaging-gate-20260708.md).
Verdict: `PASS_FOR_SOURCE_PACKAGING_GATE / RELEASE_NOT_PUBLISHED /
PRODUCTION_DEFAULT_NOT_ENABLED`. P5 exposed and fixed two blockers without
weakening production authority: deterministic `ccb_test` fake provider smoke
is allowed past frontdesk hard command-surface enforcement only under
`CCB_TEST_ENTRYPOINT=1`, and fake worker smoke now writes declared workspace
evidence so direct execution exercises script-owned project-root promotion
before pass. Verified: source-wrapper smoke `workflow_smoke_status=ok`,
final `done/pass`, `released_count=2`, `retained_count=0`; focused provider/
smoke tests `64 passed`; broad workflow source bundle `322 passed`; `npm pack
--dry-run` passed; corrected project install and global-prefix skip-download
npm install smoke under
`/home/bfly/yunwei/test_ccb2/p5-install-smoke-talk2-20260708205754` created
all `ccb`, `ask`, `autonew`, and `ctx-transfer` bin links; `git diff --check`
passed. P5 did not publish npm, install into the global/system CCB
environment, switch the main checkout, or enable production/default behavior.
Package-owner staging/release decisions remain separate.
2026-07-08 P5 post-gate automatic frontdesk stress pass: talk2 directly ran a
fresh real-provider opened-project route-mix lane from `/home/bfly/yunwei/test_ccb2`
with inherited provider environment and root-local role store. Fresh root:
`/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921`.
B7:
`/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/phase6b-real-provider-l1-l4-deploy-stress-talk2-selfrun-20260708205921-b7.md`
reports `Status: pass`: five claimable rows, L1/L2 direct rows
`done/pass` with `released_count=2`, `retained_count=0`,
`runtime_residue=false`, and `dynamic_unload_ok=true`; L3 `detail_ready`; L4
macro `replan_required`; L4 blocked `blocked`; post-B7 cleanup exited 0 and a
follow-up process scan found no target-project process residue. This run also
confirmed the preferred production-facing path: one frontdesk macro-intake
automatically handed off to planner, planner returned a five-task set, and the
frontdesk-spawned auto-runner completed the route mix without manual task
advancement. A manual checkpoint robustness bug found during this run was
fixed in `scripts/phase6b_l1_l4_frontdesk_runner.py`: already running or
terminal tasks are now observed before waiting for the auto-runner lock, while
new task creation/activation still waits to avoid duplicate authority.
2026-07-08 P5 repeatability and real-install update: talk2 ran another fresh
real-provider automatic route-mix lane from `/home/bfly/yunwei/test_ccb2`.
Root:
`/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126`.
B7:
`/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126/phase6b-real-provider-l1-l4-deploy-repeatability-talk2-202607082126-b7.md`
reports `Status: pass`, five claimable rows, two `pass` rows, three
`valid_non_success` rows, L1/L2 `released_count=2`, `retained_count=0`,
`dynamic_unload_ok=true`, `runtime_residue=false`, and no post-cleanup
target-project process residue. A separate real npm latest install smoke under
`/home/bfly/yunwei/test_ccb2/p5-real-npm-install-talk2-20260708212535`
installed public `@seemseam/ccb@8.0.19`, created all CLI bin links, downloaded
`.ccb-release/ccb-linux-x86_64`, and `ccb --print-version` returned `v8.0.19`.
This proves the published release install path, but not current dirty-source
publication: this checkout still has `package.json` version `8.0.14`, while
npm latest is `8.0.19`.
2026-07-08 P5 current-source preview release/install update: talk2 attempted a
local `build_linux_release.py --allow-dirty` preview build from the dirty
source tree and exposed a release-copy blocker: generated Flutter/Gradle
mobile output from `mobile/app/build`, `.dart_tool`, and related cache
directories entered the release stage, growing the stage to about `11G` and
the partial tarball to about `1.3G`. The build was interrupted during
`create_tarball()` and treated as a P5 packaging blocker. Fix:
`scripts/build_release.py` now excludes generated mobile/frontend output
directories (`build`, `.dart_tool`, `.gradle`, `.idea`, `node_modules`,
`dist-mobile`), with regression coverage in
`test/test_build_linux_release_script.py`. Rerun evidence:
`/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205`.
The fixed preview artifact
`dist/ccb-linux-x86_64.tar.gz` is `32M`, sha256
`4454560c3e846cbc475fa05ab289e47e0cd7417a19f5cb18f0151ebcdee4af23`, and
`current-source-release-install-result.json` reports `status=ok`,
`install_mode=release`, `source_kind=preview`, `version=8.0.14`,
`ccb --print-version -> v8.0.14`, all CLI bin links present, release helpers
present, and no forbidden mobile build entries. This still does not publish an
official GitHub/npm release or enable production/default behavior.
The installed-preview runtime closure gap is also covered: using the installed
artifact's own `scripts/workflow_closure_smoke.py` and `ccb_test`, talk2 ran a
fresh deterministic workflow closure smoke at
`/home/bfly/yunwei/test_ccb2/p5-installed-preview-smoke-talk2-202607082220`.
Result JSON:
`/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/installed-preview-workflow-smoke-result.json`.
It reports `workflow_smoke_status=ok`, final task `done`, round `pass`,
`round_result_source=round_reviewer_reply`, dynamic release `released_count=2`,
`retained_count=0`, kill return code 0, and no target-project process residue
in the follow-up process scan.
2026-07-08 delegated-worker dispatch result: the earlier worker lanes did not produce
valid workflow evidence. worker2 `job_b9c256184ba3`, worker3
`job_856bafb7d5f8`, and worker1 `job_17897f7f6452` all completed with
zero-byte artifacts and job snapshots showing `codex_prompt_delivery_failed`
with `delivery_failure_kind=delivery_anchor_missing`. Partial roots were
created at
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence30-worker2-20260708105306`,
`/home/bfly/yunwei/test_ccb2/deploy-runtime-ui-dynamic-lifecycle-worker3-fresh-20260708105425`,
and
`/home/bfly/yunwei/test_ccb2/deploy-frontdesk-bootstrap-pressure-worker1-20260708105432`,
but they are setup-only failure evidence: no complete B7 rows, no cleanup, and
no deployment-readiness claim. reviewer2 `job_433e016931e7` landed the strict
read-only gate at
[topics/phase1-6-deployment-readiness-acceptance-gate-20260708.md](../topics/phase1-6-deployment-readiness-acceptance-gate-20260708.md),
which classifies deployment readiness as `BLOCKED / NOT READY` until fresh
opened-project evidence satisfies the gate. A runtime refresh is also blocked:
`ccb restart worker1` failed with `role_digest_changed_fresh_restart_unsupported`,
and `ccb reload --dry-run` returned `plan_class: no_change` /
`reload_namespace_patch_status: no_op`, so worker reruns must wait for an
explicit CCB runtime rebuild/refresh decision or another proven way to restore
reliable worker prompt delivery. `ccb repair retry/resubmit` and extra worker
probes are intentionally held because they would mutate/re-enter the same
unreliable worker path, not provide dry-run recovery evidence.
As of 2026-07-07, that gate is blocked: reviewer2 `job_7c18b7d9e333`
requires independent deployment audit ownership instead of `talk2`
self-approval, and reviewer1 `job_50c72bc31578` requires stronger
frontdesk-started route mix, module-level integration, UI/sidebar,
busy-retain, and final-report evidence. No deployment-readiness verdict is
claimed.
Latest active deployment-readiness retests include worker3
`job_903e17b48e2c` for repeated single-round dynamic unload, positive
busy-retain, UI/sidebar, and frontdesk single-authority evidence. Worker2
`job_6f2180f706c5` returned a zero-byte artifact and left sequence25 stopped at
L1 with pending reviewer authority and duplicate command labels; it is
classified as `BLOCKER / runner_resume_and_evidence_integrity`, not route-mix
evidence. Worker1 `job_6d2dbb2d8a64` landed the maintained L1-L4 runner repair:
pending ask-first authority is now recorded as a non-claimable checkpoint, B7
and cleanup are blocked while pending authority remains, `resume-pending
<task_id>` is available after the persisted provider job becomes terminal, and
duplicate command evidence labels are rejected before stdout/stderr can be
overwritten. Talk2 verified `python -m py_compile
scripts/phase6b_l1_l4_frontdesk_runner.py
test/test_phase6b_l1_l4_frontdesk_runner.py` and `python -m pytest -q
test/test_phase6b_l1_l4_frontdesk_runner.py` -> `25 passed`; no real-provider
rerun has consumed the repair yet. A visible worker3 runtime root
`/home/bfly/yunwei/test_ccb2/deploy-runtime-ui-dynamic-lifecycle-worker3-20260707135051`
is also not claimable: worker3 `job_903e17b48e2c` returned `Verdict:
BLOCKER`, with resident preflight and UI/tmux pane switching positive but no
valid dynamic-round, busy-retain, B7, or cleanup evidence because frontdesk job
`job_2a29c4d4d4a1` directly created `docs/runtime-retest-a.md` instead of
handing the implementation request to planner/orchestrator/dynamic workers. A
focused frontdesk boundary repair is assigned to worker2 as
`job_634eaa1cfe61`. Worker2 completed that source repair: frontdesk RolePack
instructions now forbid direct project artifact implementation, frontdesk
Codex launch honors required command policy with `--ask-for-approval never
--sandbox read-only`, and dispatcher finalization rejects implementation-like
frontdesk `completed` replies without valid Intake/Blocked Evidence by writing
`.ccb/runtime/frontdesk-boundary/<job>.json` and marking the job failed with
`frontdesk_direct_implementation_boundary_violation`. Talk2 verified
`python3 -m py_compile` for the touched dispatcher/launcher/tests and focused
pytest for frontdesk dispatcher, loop capacity, runtime launch, rolepack, and
provider hook settings. No deployment-readiness claim is made until fresh
post-repair real-provider route-mix and dynamic/UI reruns produce valid rows,
B7, release, and cleanup evidence. Fresh post-repair reruns have been submitted:
worker2 `job_e96f29120464` for L1-L4 frontdesk route-mix, and worker3
`job_3b15e482acd5` for repeated direct-execution dynamic unload, UI/sidebar,
busy-retain, and frontdesk single-authority evidence. Both reruns failed before
creating a business test root: their artifacts are 0 bytes, no matching fresh
root exists under `/home/bfly/yunwei/test_ccb2`, and job diagnostics show
`codex_prompt_delivery_failed` with
`delivery_failure_kind=delivery_anchor_missing` in the `talk2_workers` group
workspace. This is classified as a provider prompt-delivery blocker, not
route-mix or lifecycle evidence. A focused delivery-layer repair has been
assigned to worker1 as `job_4b6c21ee38c5`; fresh real-provider reruns must wait
until that blocker is repaired and verified. That worker1 repair job also
failed before doing work: its completion artifact is 0 bytes and has the same
`codex_prompt_delivery_failed` / `delivery_anchor_missing` shape. Talk2 then
cleared worker1/worker2/worker3 provider contexts with `ccb clear` and submitted
a minimal delivery probe to worker1 as `job_f61106a0502b`. Full real-provider
route-mix and lifecycle reruns remain held until that probe proves worker prompt
delivery has recovered. The probe also failed with a 0-byte artifact, but local
tmux/session-log inspection proved the prompt did reach worker1 and worker1
replied `delivery_probe_ok`. The deeper bug was completion detection binding to
the stale group-workspace session log while the active Codex resume wrote a new
session under the same agent's legacy `.ccb/workspaces/worker1` cwd. A source
repair in `lib/provider_backends/codex/execution.py` now treats that exact
same-project legacy-agent workspace as a trusted fallback only when the log is
under the same agent session root and contains the current `CCB_REQ_ID`.
Regression coverage landed in `test/test_stability_regressions.py`; Talk2
verified the focused regression plus nearby Codex fallback/quarantine tests.
The live installed CCB worker panes still need a post-install/restart or
equivalent runtime refresh before full worker dispatch can be considered
restored.
Talk2 then ran a source-runtime real-provider route-mix probe directly from
`/home/bfly/yunwei/test_ccb2` using fresh root
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence20-talk2-20260707230547`
and `/home/bfly/yunwei/ccb_source/ccb_test`, inheriting the system provider
environment and using only a lab-local `AGENT_ROLES_STORE`. Positive evidence:
frontdesk/codex auto-forwarded to planner/codex with `silence=true`; planner
produced the required five-task route mix; L1 and L2 reached `done/pass`; both
direct-execution loops released dynamic coder/reviewer nodes with
`released_count=2`, `retained_count=0`; and L3 reached `detail_ready` after a
source parser repair for the real task_detailer markdown shape
(`## Readiness Recommendation` followed by `detail_ready`). Verification for
that repair: `test/test_loop_capacity_cli.py::test_loop_runner_imports_task_detailer_markdown_heading_sections`
passed, the focused task_detailer/needs-detail selection passed, and
`python -m pytest test/test_loop_capacity_cli.py test/test_plan_tasks_cli.py -q`
-> `135 passed`. Remaining deployment blocker: the same real run stopped at
`planner_status_transition_required` for the L4
`macro_adjustment_request` route, with the L4 `blocked` route still only at
route evidence. Deployment readiness still needs script-owned automatic
terminal evidence for `macro_adjustment_request -> replan_required` and
`blocked -> blocked` in the frontdesk-started lane.
Current partial evidence: worker1 supplemental `job_ec6a6a8b2ef8` passes the
Frontdesk real entry E2E lane only, with fixed JSON/JSONL rows for two
frontdesk-started direct-execution tasks. worker2 original `job_cd6b21bc5896`
is useful raw L1-L4/sequence13 regression evidence, but it is not a
deployment-readiness pass because it starts from supervisor/driver task
creation rather than frontdesk intake and lacks the fixed row schema. worker3
original `job_153786148bfd` is useful raw UI/sidebar, observer,
resident-reachability, and dynamic-unload evidence, but it is not a deployment
readiness pass because task authority was script-created/imported after
frontdesk asks, fixed evidence rows are missing, and positive busy-retain
release evidence is still absent. As of the 2026-07-07T11:50:57+08:00 local
ccbd state check, worker1 `job_e6cffc269af4` is completed and passes the
Frontdesk=Codex direct-execution retest lane. It has fixed evidence rows under
`/home/bfly/yunwei/test_ccb2/deploy-frontdesk-codex-e2e-worker1-20260707-114105`
showing one L2 frontdesk=codex direct-execution path reached `done/pass` with
clean dynamic release. It does not cover L1-L4 route mix, UI/sidebar, or
positive busy-retain. worker2 `job_a8d5fddd2a67` is completed and is
`BLOCKER / not_claimable` for the stricter L1-L4 lane. Fresh root
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence15-worker2-20260707113648`
proves the frontdesk/planner entry path, inherited provider home, explicit
positive timeout diagnostic, default watch beyond the old 10 second window, and
dynamic release for the frontdesk-created combined task. Formal L1 then stopped
after worker/reviewer success because final round orchestrator provider
delivery failed with `codex_prompt_delivery_failed / delivery_anchor_missing`;
L2-L4 were not reached. worker2 applied a focused retry-policy source repair in
`lib/ccbd/services/dispatcher_runtime/finalization_retry_runtime/policy.py` so
`decision.diagnostics.delivery_retryable=true` can trigger automatic retry
without overriding non-retryable API failures. Talk2 re-ran
`test/test_ccbd_retry_failure_detail.py` (`4 passed`),
`test/test_stability_regressions.py::test_codex_delivery_guard_times_out_after_anchor_never_appears`
(`1 passed`), and py_compile for the touched retry files. A new fresh L1-L4
frontdesk-started retest after this repair was assigned to worker2 as
`job_93f0288df5f7`; sequence15 is consumed failure evidence and must not be
reused. A separate frontdesk auto-runner role-output issue was already repaired:
an earlier failed planner job `job_ce2490255a5a` had been logged repeatedly as
`role_output_import_blocked`, then a later auto-runner for successful planner
job `job_03c5c271f243` stopped on the old failed job instead of consuming the
requested wait job. The source bug was that blocked role-output imports were
not treated as settled for future auto-runner scans. A focused source repair
was assigned to worker1 as
`job_9e95855157d1`; completion artifact
`job_9e95855157d1-art_2036e8fd9d6d4770.txt` is accepted for that focused
repair. The scanner path now treats prior `role_output_import_blocked` records
as settled while leaving explicit consume `ok`-only, so blocked evidence is not
rewritten as pass. Talk2 re-ran `py_compile`, the new regression, the focused
`loop_runner_auto or role_output_import` selection (`9 passed`), and the full
`test/test_loop_capacity_cli.py` file (`109 passed`). The older queued worker2
ask `job_ac5fef15fa2a` failed with an empty artifact and is not evidence; the
active post-repair retest is worker2 `job_93f0288df5f7`. Later worker3 ask
`job_731bc4142333` also failed with an empty artifact and is not evidence.

Worker2 `job_93f0288df5f7` completed the fresh sequence16 retest from
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence16-worker2-20260707120823`
after worker1's explicit-project ask repair. The frontdesk target blocker is
cleared, but sequence16 is still `not_claimable`: L1 reached
`direct_execution -> done/pass`; L3 reached `needs_detail -> detail_ready`; L4
macro reached `macro_adjustment_request -> replan_required`; L4 blocked reached
`blocked -> blocked`; L2 reached `direct_execution` but became terminally
`blocked` before worker/reviewer execution because rolepack/bootstrap setup
failed. Logs show `roles_install_all.stderr` reporting `role source not found`
for `agentroles.ccb_frontdesk`, `agentroles.ccb_planner`,
`agentroles.ccb_task_detailer`, `agentroles.ccb_orchestrator`,
`agentroles.ccb_round_reviewer`, and `agentroles.code_reviewer`; the generated
B7 also missed task-show/round evidence for direct rows and preserved stale
dynamic residue from `loop-lpa2c402-*` despite post-B7 cleanup returning
`state: unmounted`. This is a deployment blocker in the sequence driver/B7
evidence path, not an accepted L1-L4 result. worker3
`job_553ecdfb89ca` returned `BLOCKER / not deployment-ready`: positive rows
cover busy-retain, UI/sidebar switching, and observer timeout behavior, but
direct execution can leave dynamic release residue after auto-release timeout,
`needs_detail` can repeatedly reactivate task_detailer instead of settling to
`detail_ready`, and provider delivery failures prevented the full route mix. A
focused repair for those lifecycle blockers landed as worker3
`job_fb4475224824`: `role_output_import.py` now imports task_detailer
`detail_design`, `detail_summary`, and `detail_packet` once and settles the task
to `detail_ready`, while `loop_topology.py` performs one bounded retry after a
failed non-busy release reconcile with residue blockers. Talk2 re-ran the
focused task_detailer/release regressions plus nearby reply-only and
busy-retain guards. This is accepted as source repair only; the real-provider
stress harness still needs a fresh rerun before deployment readiness.
Worker1 `job_df3c9451c8b5` is accepted as a focused source repair for the
sequence16 rolepack/bootstrap and B7 evidence blocker. Source-test role
installation now discovers source-checkout CCB draft RolePacks, passes the
concrete role path to `agent-roles`, and the maintained sequence packet uses
`ccb_test roles install --skip-tools` plus `current/role.toml` and
`install.json` validation instead of manual copies. Required draft RolePacks now
use installer-valid `catalog.level = "experimental"`. The sequence driver also
observes/reuses existing task records, while B7 reads round evidence from
task-show artifact paths and only treats stale topology residue as released when
authoritative `cleanup_after_b7.stdout` reports `kill_status: ok` and
`state: unmounted`. Talk2 re-ran the targeted test bundle (`94 passed`),
py_compile, invalid catalog-level scan, and a source-wrapper role seed smoke
from `/home/bfly/yunwei/test_ccb2` that installed all seven required roles into
a fresh local `AGENT_ROLES_STORE`. This is source repair evidence only; a fresh
sequence17 real-provider L1-L4 retest is still required.
Worker2 `job_6437d7ef41ea` consumed the fresh sequence17 retest root
`/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence17-worker2-20260707-131428`.
It proves the rolepack/bootstrap blocker is repaired and cleanup can unmount
the project cleanly, but it is still `not_claimable`. The frontdesk natural
language request created a separate meta direct-execution task
`fresh-sequence17-real-provider-deploymen-20260707052218`; that task was
blocked by script-owned authority because the worker's isolated workspace
deleted or renamed project-root files, yielding
`round_result_source=isolated_workspace_deletions_unsupported`. The driver then
also started the manual L1 task `phase6b-l1-doc-direct-execution`, creating a
second loop `lp451adf`; cleanup happened while its worker job was still
incomplete, so its round summary is `blocked / ask_job_incomplete`. The B7 row
used stale pre-terminal task-show evidence and missed the round summaries. This
exposes a harness/controller bug: the frontdesk-started request and the
supervisor L1-L4 sequence are not yet a single authoritative task flow.
Deployment readiness remains blocked; the next repair must remove the meta/L1
double path, wait for terminal round authority before cleanup, and regenerate
B7 from final task-show plus round artifacts.

Historical Phase 6B attempts remain below for traceability. L1-L4 repeat4
consumed reviewer2 approval
`job_6ec85738acc6` exactly once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence4-20260704`.
It completed L1, then stopped at L2 because the exact approved command
`python -m unittest tests/test_calculator.py` resolves `tests` to an installed
site-packages package in the inherited provider environment. B7 is
[history/phase6b-real-provider-l1-l4-repeat4-b7-20260704.md](phase6b-real-provider-l1-l4-repeat4-b7-20260704.md)
with `Status: not_claimable`; post-B7 cleanup returned `state: unmounted`.
The L1-L4 repeat5 root was partially started by talk2 after an approval
callback, then stopped when reviewer2 later returned the non-fresh-root blocker
`job_f142f85effeb`; cleanup returned `state: unmounted`, and sequence5 is
historical/non-reusable. Reviewer2 approved L1-L4 repeat6 in
`job_bca6a4a854a3`, and talk2 consumed it exactly once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence6-20260704`.
Repeat6 stopped at L1 because the real orchestrator provider imported
`orchestration_notes` itself, violating the required supervisor/script-owned
route authority boundary. B7 is
[history/phase6b-real-provider-l1-l4-repeat6-b7-20260704.md](phase6b-real-provider-l1-l4-repeat6-b7-20260704.md)
with `Status: not_claimable`; cleanup returned `kill_status: ok`,
`state: unmounted`. Worker1 `job_18eb612e93b3` repaired the orchestrator
activation contract so providers reply only and do not receive route-authority
import instructions; reviewer2 accepted that source repair in
`job_dd92b30f6a59`. Reviewer2 approved L1-L4 repeat7 in
`job_a9649f4a0e98`, and talk2 consumed it exactly once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence7-20260704`.
Repeat7 stopped at L1 `activate_orchestrator`: `ccb_test loop runner --once`
failed before provider ask submission with `ask is project-local; workspace or
cwd resolved to another .ccb project`. B7 is
[history/phase6b-real-provider-l1-l4-repeat7-b7-20260704.md](phase6b-real-provider-l1-l4-repeat7-b7-20260704.md)
with `Status: not_claimable`; post-B7 cleanup returned `kill_status: ok`,
`state: unmounted`. Reviewer2 blocker `job_790f95da49fe` confirmed sequence7
is consumed/non-fresh. Worker1 repaired the project-local ask/cwd failure in
`job_17d3d3198d09` by allowing service-owned internal asks under explicit
project contexts while preserving direct user-facing cross-project rejection;
reviewer2 accepted the repair in `job_dfc8946339d0`. Repeat8 launch approval
`job_05e6f1c57f3c` was granted and talk2 consumed it exactly once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`.
The B7 report is
[history/phase6b-real-provider-l1-l4-repeat8-b7-20260704.md](phase6b-real-provider-l1-l4-repeat8-b7-20260704.md)
with `Status: not_claimable`: L1/L2 are `test_design_failure` because the
direct-execution authority reached `done/pass` without corresponding lab
changes and L2's lab-local unittest evidence failed; L3/L4 produced bounded
`valid_non_success` rows. Post-B7 cleanup first rejected unsupported
`kill --json`, then succeeded with `kill_status: ok`, `state: unmounted`.
Sequence8 is consumed/non-reusable. Reviewer2 `job_04b5c2faa2f2` blocks any
repeat8 reapproval because the root now exists and is non-fresh. The
supervisor diagnosis is recorded in
[topics/phase6b-repeat8-direct-execution-failure-note.md](../topics/phase6b-repeat8-direct-execution-failure-note.md):
the repeat8 provider/reviewer evidence validated copy-workspace changes, while
the lab project root remained unchanged.
Worker3 converted the dated L1-L4 launch request topic into a repeat8
historical record with no executable command block. Talk2 then requested a
separate active sequence9 packet:
[topics/phase6b-l1-l4-launch-request-sequence9-20260704.md](../topics/phase6b-l1-l4-launch-request-sequence9-20260704.md).
The requested fresh root is
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`, and the
planned B7 path is
`history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md`. Reviewer1
`job_1ebb25b249ba` previously found a source-level direct-execution
project-root authority blocker; reviewer1 re-audit `job_b4184497742b` now marks
the source-level blockers accepted. Reviewer1 fallback launch-gate re-audit
`job_c4935017fc15` granted exactly one sequence9 run, and talk2 consumed that
approval once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`.
Sequence9 reached L1 `done/pass`, then L2 direct execution produced a blocked
round with `round_result_source=isolated_workspace_no_project_root_effect`.
Although the project-root `calculator.py` was updated and a supervisor-created
project-root unittest resolution check passed after the block, the task
authority remained `blocked`, and L3/L4 were not run. The generated B7 file is
[history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md](phase6b-real-provider-l1-l4-repeat9-b7-20260704.md),
but its `Status: pass` is a false-positive normalizer result and is rejected by
the supervisor correction
[history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md](phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md).
Post-B7 cleanup returned `kill_status: ok`, `state: unmounted`. Sequence9 is
consumed/non-reusable, no repeat9 evidence is claimable, and Phase 6B remains
unclaimed.
Worker1 `job_dd20a18926e1` prepared the fresh sequence10 repair/launch packet
at
[topics/phase6b-l1-l4-launch-request-sequence10-20260704.md](../topics/phase6b-l1-l4-launch-request-sequence10-20260704.md)
for root
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence10-20260704` and B7
path
`history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md`. The embedded
B7 normalizer now parses current task-show JSON from top-level `status` and
nested `task.status`, treats missing task-show or unrun L3/L4 rows as
`test_design_failure`, preserves blocked task authority as blocked, and only
emits overall `Status: pass` when every required row has observed route,
status, round/result, and task-specific artifact/test evidence. Reviewer2 audit
`job_0d07e67ef312` remained queued, so talk2 used reviewer1 fallback launch
gate `job_bfe386ae7a9f`, which granted exactly one sequence10 run. Talk2
consumed it once from the sequence10 root. L1 reached direct execution, but the
round reviewer detected a fake-success shape: worker changes existed only in the
loop copy workspace, the main project `lab_docs/l1_release_note.md` remained
`status: draft` / `summary: TBD`, and script-owned task authority imported the
round as `blocked`. Talk2 stopped before L2/L3/L4, wrote
[history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md](phase6b-real-provider-l1-l4-repeat10-b7-20260704.md)
with `Status: not_claimable`, and cleanup returned `kill_status: ok`,
`state: unmounted`. Sequence10 is consumed/non-reusable; Phase 6B remains
unclaimed.
Worker1 source repair `job_e2ff663087be` updates ask-first `direct_execution`
authority after the sequence10 fake-success finding: when the worker runs in an
isolated copy workspace, script-owned allowed-path promotion now happens before
code-reviewer, orchestrator, and `ccb_round_reviewer` validation, so reviewers
audit project-root evidence rather than workspace-only evidence. Non-pass,
unknown, or project-root-test failure after staging rolls the project root back
and records explicit rollback evidence instead of importing success. Focused
verification added
`test_loop_runner_direct_execution_promotes_before_project_root_review` and
kept `rework_node`/unknown results non-success. No real-provider, B7,
source-wrapper runtime, or cleanup command was run for this source repair.
Reviewer1 accepted this source repair in `job_a7e62fee5496` with artifact
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_a7e62fee5496-art_d74161f1a0dd4d52.txt`.
Talk2 local verification after review passed `py_compile` for
`loop_ask_first.py`, `loop_runner.py`, `loop_topology.py`, and `plan_tasks.py`,
plus `python -m pytest test/test_loop_capacity_cli.py
test/test_plan_tasks_cli.py test/test_loop_topology_cli.py
test/test_loop_topology_dispatch_contract.py -q` with `89 passed`. Worker3
`job_1cfa66b23752` prepared the next fresh L1-L4 sequence11 approval packet at
[topics/phase6b-l1-l4-launch-request-sequence11-20260704.md](../topics/phase6b-l1-l4-launch-request-sequence11-20260704.md)
for root
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence11-20260704` and B7
path
`history/phase6b-real-provider-l1-l4-repeat11-b7-20260704.md`. Reviewer1
`job_68063ec21783` granted exactly one sequence11 approval-to-run, and talk2
consumed it once from the sequence11 root. L1 and L2 direct-execution rows
reached task authority `done/pass` with project-root changes and L2 lab-local
unittest evidence, but the generated B7
[history/phase6b-real-provider-l1-l4-repeat11-b7-20260704.md](phase6b-real-provider-l1-l4-repeat11-b7-20260704.md)
misclassified them as `test_design_failure` because the normalizer failed to
parse script-owned round/result evidence and treated persisted topology evidence
as residue. L3 reached `needs_detail` and activated the detailer, but the
detail imports failed because `detail_design`, `detail_summary`, and
`detail_packet` were submitted with `--route`, and the subsequent
`ready_for_orchestration -> detail_ready` status transition was rejected.
Talk2 stopped before L4, wrote repeat11 B7 with `Status: not_claimable`, and
post-B7 cleanup returned `kill_status: ok`. Sequence11 is consumed and
non-reusable. Talk2 dispatched worker1 `job_a218e823a78f` to repair the L3
detail-authority path and worker2 `job_f4ee3f0cc58e` to repair the B7
normalizer. Worker1 completed the L3 repair in `job_ad72d8bb8790`: the
source now allows `ready_for_orchestration -> detail_ready` while preserving
the required `detail_design`, `detail_summary`, and `detail_packet` gate; the
sequence11 driver no longer passes `--route` for detail, macro, or blocker
artifacts; `detail_ready` uses the default `next_owner=planner`; and
`run_required` fails hard on `command_status: failed` text or JSON markers.
Reviewer1 accepted that repair in `job_f3982925275d`. Worker2 completed the B7
normalizer repair in `job_dd89005df2ee`: the embedded sequence11 normalizer now
parses both `round_result:` and legacy `round result:` fields, reads
task-show `last_round.result`, and treats persisted observed topology as valid
when no dynamic `loop-*` agents remain retained or active. Reviewer1 accepted
the repair through callback continuation
`cb_faab6bb2d057-art_f9e89c4d470a4c16.txt`; historical repeat11 B7 remains
immutable evidence and was not regenerated. No further L1-L4 runtime command is
approved until a fresh sequence12-or-later launch packet is talk2-gated.
Worker3 `job_cf01392dc751` prepared the fresh sequence12 approval packet at
[topics/phase6b-l1-l4-launch-request-sequence12-20260705.md](../topics/phase6b-l1-l4-launch-request-sequence12-20260705.md)
for root
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705` and B7
path
`history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md`. The packet
carries forward the accepted L3 detail-authority and B7 normalizer repairs, is
static/docs/tests preparation only, and was not runtime approval until the user
changed the launch gate to talk2 self-review. Reviewer1 fallback audit
`job_454bdb9b36f1` returned `APPROVAL BLOCKED`: reviewer1 is not an acceptable
substitute because the packet designates reviewer2 as the required launch gate.
At that audit, the sequence12 root and B7 path were still absent. Talk2 then
submitted a self-contained reviewer2 launch-gate request `job_a047b32d275c`;
no completion artifact is visible. On 2026-07-05 the user instructed talk2 to
stop using reviewer approval and perform launch review directly. Talk2 ran the
launch-specific self-review, confirmed the root and B7 path were absent, then
consumed sequence12 exactly once from `/home/bfly/yunwei/test_ccb2`. The run
produced
`history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md` with
`Status: pass`: L1/L2 are `pass`, L3 `needs_detail` is
`valid_non_success`, L4 `macro_adjustment_request` is `valid_non_success`, and
L4 `blocked` is `valid_non_success`. Post-B7 cleanup returned
`kill_status: ok`, `state: unmounted`.
L5 repeat2 reached direct execution, but the worker ask submission failed
because ask-first execution used plain `ask` from an active CCB task context.
Worker1 repaired that first source blocker in
`job_19092d158390`, accepted by reviewer2 `job_56466011201a`. L5 repeat3 then
inherited the current system provider environment and reached direct execution:
the worker produced a partial signal, but reviewer submission failed with
`ask --chain requires an active parent job for the sender`. The repeat3 B7 is
`not_claimable`, cleanup is complete. Worker1 source repair
`job_52ec099f6427` is now accepted by reviewer2 `job_766050825b27`: ask-first
watched child asks submit from runner-owned `system` sender with
`callback=False` and `silence=False`. Worker3 prepared the fresh L5 repeat4
launch packet in `job_2faf4fd57789`, and reviewer2 granted approval-to-run in
`job_5dd131a6ea7e`. Talk2 consumed that approval once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704`.
The run produced
[history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](phase6b-real-provider-l5-partial-repeat4-b7-20260704.md)
with `Status: valid_non_success` and
`reviewer_rework_or_partial_observed=true`; post-B7 cleanup returned
`state: unmounted`. Reviewer-gated Phase 6B aggregation remains pending.

```text
draft task
  -> planner role activation and explicit bundle import
  -> ccb_task_detailer bundle import and detail_ready gate
  -> plan reviewer activation and review import
  -> script-validated ready
  -> one execution round
  -> dynamic worker + code_reviewer capacity
  -> round result import
  -> auto release
```

This is still an opt-in candidate path, not a default project workflow daemon.

Target next runtime shape:

```text
draft task
  -> planner role activation and explicit bundle import
  -> orchestrator triage
      -> direct execution -> ask-first execution round
      -> needs_detail -> ccb_task_detailer -> orchestrator
      -> macro_adjustment_request -> planner
      -> blocked -> blocker evidence
```

The topology-dispatch slice below is landed evidence, but it is no longer the
preferred direction to expand. The next design correction is to keep topology
as mount authority only and use normal CCB `ask` for most semantic
collaboration. See
[decisions/020-mount-topology-and-ask-first-orchestration.md](../decisions/020-mount-topology-and-ask-first-orchestration.md)
and
[topics/mount-topology-and-ask-first-orchestration.md](../topics/mount-topology-and-ask-first-orchestration.md).

## Fast Resume Summary

- Phase 6B is claimable for initial real-provider, single-round capability
  after the 2026-07-05 `talk2` final aggregation report:
  [history/phase1-6-acceptance-report-20260705.md](phase1-6-acceptance-report-20260705.md).
  Do not expand this into production/default enablement, post-detail execution,
  reviewer-rework stability, long-running multi-round workflows, or arbitrary
  workflow authoring. Do not run more provider/runtime commands without a fresh
  root and a new explicit owner/supervisor launch decision.
- Owner decision on 2026-07-04: future real-provider lab packets must inherit
  the current system provider environment and must not export lab-local `HOME`
  or `CCB_SOURCE_HOME` to a fresh `source_home`. The suspected repeated Codex
  login attempts are caused by isolated provider homes; fake/source-wrapper
  evidence that already used isolation remains historical evidence only.
- Repaired L1-L4 approval `job_7800c403f864` superseded old
  `job_d44bf15c6cb1` and was consumed exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704`.
  That run failed before provider ask activation because the lab project plan
  root was absent. L1-L4 repeat2 approval `job_0c8596e0895d` was then consumed
  exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704`.
  The plan-root repair succeeded through L1 `task-create`, anchor imports,
  `ready_for_orchestration`, and orchestrator activation. `continue-route`
  then failed before direct execution because the supervisor
  `orchestration_notes.md` file was outside the lab project root and
  `plan task-artifact --file` rejected it. B7 is
  [history/phase6b-real-provider-l1-l4-repeat2-b7-20260704.md](phase6b-real-provider-l1-l4-repeat2-b7-20260704.md)
  with status `not_claimable`; post-B7 cleanup returned `state: unmounted`.
  Worker1 `job_bc9e143601a3` then produced repeat3 approval
  `job_51a85fa2fc58`; talk2 consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704`.
  The project-local supervisor import repair worked for route notes, L3 detail
  files, and macro-adjustment evidence. The run stopped on the final blocked
  task because the driver imported `blocked.md` with artifact kind `blocked`,
  but the product accepts `blocker_evidence` and related legacy round kinds,
  not `blocked`. B7 is
  [history/phase6b-real-provider-l1-l4-repeat3-b7-20260704.md](phase6b-real-provider-l1-l4-repeat3-b7-20260704.md)
  with status `not_claimable`; post-B7 cleanup returned `state: unmounted`
  after rerunning cleanup with the approved lab-local environment variables.
  No L1-L4 rerun is approved until the blocked-artifact-kind and B7
  classification repair is accepted and reviewer2 grants a fresh verdict naming
  a new root and command shape.
- L5 partial-only approval `job_4e3c051ef168` was consumed exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704`.
  Materialization and `init` succeeded; `start-partial` failed at
  `plan task-create --plan phase6b-real-provider-l5` because the project plan
  root `docs/plantree/plans/phase6b-real-provider-l5` was absent. B7 is
  [history/phase6b-real-provider-l5-partial-b7-20260704.md](phase6b-real-provider-l5-partial-b7-20260704.md)
  with status `not_claimable`; post-B7 cleanup returned `state: unmounted`.
  Worker2 `job_d11d3c062959` prepared the static repeat2 packet for fresh
  root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704`
  and fresh B7 path
  `history/phase6b-real-provider-l5-partial-repeat2-b7-20260704.md`.
  Reviewer2 granted L5 repeat2 approval in `job_af5f6fb64a7d` and urgent
  regression addendum approval in `job_663bad41c855`. Talk2 consumed that
  approval exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704`.
  Plan-root and project-local supervisor import repairs worked through
  `direct_execution`; the direct-execution round then imported a blocked result
  with `round_result_source=ask_submission_failed` because the runner submitted
  a plain child `ask` while already inside an active CCB task. B7 is
  [history/phase6b-real-provider-l5-partial-repeat2-b7-20260704.md](phase6b-real-provider-l5-partial-repeat2-b7-20260704.md)
  with status `not_claimable`; post-B7 cleanup returned `state: unmounted`.
- Worker1 source repair `job_19092d158390` was accepted by reviewer2
  `job_56466011201a`: `_submit_and_watch` now sets
  `ParsedAskCommand(callback=True)`, mapping result-needed ask-first child asks
  to existing CCB chain routing. Tests cover success, partial, bounded rework,
  submit failure, watch failure, and route mapping. No source-wrapper,
  provider, L5/L1-L4, runtime, launch, or B7 command was run. This closes the
  first source blocker but not the real-provider L5 evidence gate.
- Worker1 L5 repeat3 packet `job_657112c87bce` was accepted by reviewer2
  `job_de6263827473` and consumed exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704`.
  The run used the current system provider environment, not lab-local
  `HOME`/`CCB_SOURCE_HOME` isolation. It reached `direct_execution`, the worker
  completed with a partial signal, and dynamic topology released cleanly. The
  reviewer ask then failed before provider review with
  `round_result_source=ask_submission_failed`, stage `reviewer_ask`, and error
  `ask --chain requires an active parent job for the sender`. B7 is
  [history/phase6b-real-provider-l5-partial-repeat3-b7-20260704.md](phase6b-real-provider-l5-partial-repeat3-b7-20260704.md)
  with status `not_claimable`; post-B7 cleanup returned `kill_status: ok`,
  `state: unmounted` after retrying with lab-local `AGENT_ROLES_STORE`.
- Active pending callbacks: L1-L4 needs a fresh worker repair for blocked
  evidence kind and B7 normalizer classification ordering; talk2 dispatched
  worker2 `job_855ab110681e` to prepare that repeat4 repair and chain
  reviewer2; that repair must preserve the new real-provider environment
  policy by inheriting the current system provider environment without
  lab-local `HOME` / `CCB_SOURCE_HOME` overrides; talk2 sent the provider-env
  addendum as `job_984364b1766c`. Talk2 also sent doc-test addendum
  `job_ce9ed763cc71`. Reviewer2 accepted the current gate in
  `job_6ec85738acc6`; talk2 consumed it once. Repeat4 completed L1, stopped at
  L2 on the exact unittest command/package-resolution blocker, produced
  [history/phase6b-real-provider-l1-l4-repeat4-b7-20260704.md](phase6b-real-provider-l1-l4-repeat4-b7-20260704.md)
  with `Status: not_claimable`, and cleanup is complete. L5 source repair
  `job_52ec099f6427` is accepted by
  reviewer2 `job_766050825b27`: watched ask-first child asks now use the
  runner-owned `system` sender, no callback/chain, no silence, and immediate
  watch. Talk2 dispatched worker3 `job_2faf4fd57789` for a fresh L5
  partial-only repeat4 launch packet; reviewer2 `job_5dd131a6ea7e` granted
  approval-to-run, and talk2 consumed it exactly once from
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704`.
  B7 is
  [history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](phase6b-real-provider-l5-partial-repeat4-b7-20260704.md)
  with `Status: valid_non_success`; cleanup is complete.
  Reviewer1 read-only coverage audit `job_e8459a2782cd` returned
  `COVERAGE OK`; reviewer-rework remains excluded until a new L5 packet covers
  it or records a blocker.

## Immediate Resume Handoff

- Current wait state: reviewer1 returned `COVERAGE OK` in read-only
  `job_34d57ea11c3a`, and worker1's L1-L4 normalizer hardening callback
  `job_307d5f834a1a` is accepted by reviewer2 `job_d023a883a62d`. Worker2's
  L5 reviewer-rework/partial planning callback `job_e6456cf4a072` is accepted
  by reviewer2 `job_3824dde8454e` as plan-only readiness. Worker3's static
  launch-packet/normalizer hardening lane `job_82d723ec0f89` is accepted by
  reviewer2 `job_f20daf37898d`: the L1-L4 embedded normalizer now emits
  conservative `authority_checks.*` fields, and the L5 reviewer-rework/partial
  tranche has an embedded normalizer shape. Worker1's repaired
  checkpoint/resume launch packet `job_d21db63841cd` received reviewer2
  `APPROVAL-TO-RUN GRANTED` in `job_7800c403f864`, explicitly superseding old
  `job_d44bf15c6cb1`; talk2 consumed it once. The run materialized and
  initialized the lab, then failed before provider ask activation at L1
  `task_create` because the project-local plan root was absent. Worker1's
  repeat2 repair received reviewer2 `APPROVAL-TO-RUN GRANTED` in
  `job_0c8596e0895d`; talk2 consumed it once. Repeat2 proved the plan-root
  repair through L1 `task-create`, anchor import, ready state, and
  orchestrator activation, then failed before direct execution because the
  supervisor `orchestration_notes.md` file was outside the lab project root and
  `plan task-artifact --file` rejected it. The resulting L1-L4 repeat2 B7 is
  `not_claimable`, cleanup is complete, and a fresh supervisor-artifact path
  repair plus fresh approval is required before rerun. Worker1 repeat3 later
  reached L1/L2 direct execution, L3 `detail_ready`, and L4 macro evidence, but
  stopped on the final blocked task because artifact kind `blocked` is not
  accepted; that B7 is also `not_claimable` and cleanup is complete. Worker2
  `job_c3741ad025da` produced L5 partial-only approval `job_4e3c051ef168`;
  talk2 consumed it once and the run failed before provider ask activation at
  L5 `task_create` because the project-local plan root was absent. Worker2
  repeat2 packet `job_e6c576d10c97` plus urgent approval
  `job_663bad41c855` was consumed exactly once. It reached direct execution,
  then imported `blocked` with `round_result_source=ask_submission_failed`
  because ask-first execution used plain `ask` from an active CCB task context.
  The L5 repeat2 B7 is `not_claimable` and cleanup is complete. Worker1 source
  repair `job_19092d158390` is accepted by reviewer2 `job_56466011201a`.
  Worker1 L5 repeat3 packet `job_657112c87bce` was accepted by reviewer2
  `job_de6263827473` and consumed exactly once. Repeat3 inherited the system
  provider environment and reached direct execution; the worker produced a
  partial signal, but reviewer ask submission failed with
  `ask --chain requires an active parent job for the sender`. The L5 repeat3
  B7 is `not_claimable` and cleanup is complete. Worker1 source repair
  `job_52ec099f6427` is accepted by reviewer2 `job_766050825b27`. Worker3
  `job_2faf4fd57789` prepared the fresh repeat4 launch packet, reviewer2
  `job_5dd131a6ea7e` granted approval-to-run, and talk2 consumed it once. The
  L5 repeat4 B7 is `valid_non_success` with partial observed. At that point,
  Phase 6B still needed L1-L4 repair and final aggregation; both are now closed
  for the bounded initial real-provider single-round claim by repeat12 and the
  2026-07-05 final report.
- Active supervision board:
  [topics/phase1-6-active-supervision-board-20260704.md](../topics/phase1-6-active-supervision-board-20260704.md).
  Use it as the compact lane tracker for pending worker/reviewer callbacks.
- Current wait state: reviewer1 accepted the residue-clean integrated
  eight-case fake-provider source-wrapper matrix in `job_712002b8f005`.
  Reviewer2 accepted the module/final-report evidence package and Phase 6A
  claim boundary in `job_a34e79ecfc00`. The accepted Phase 6A claim is limited
  to fake-provider, single-round, source-wrapper program-matrix evidence. It
  excludes Phase 6B, real-provider capability, production/default enablement,
  long-running multi-round workflows, and arbitrary workflow authoring.
- The Phase 6A closure runbook now records reviewer1's accepted single-case
  re-audit, the residue-clean integrated matrix run, reviewer1 matrix
  acceptance, and reviewer2 claim-boundary acceptance. Keep the runbook as
  evidence/rerun guidance, not as Phase 6B launch approval.
- Lifecycle worker artifact:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_72c2e45f44d4-art_36d80ca8458840dc.txt`.
  Reviewer1 acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_069b75debd58-art_35fb1de286b34146.txt`.
- The integrated matrix was run from `/home/bfly/yunwei/test_ccb2` with
  isolated `HOME` and `CCB_SOURCE_HOME`; use
  `/home/bfly/yunwei/test_ccb2/phase6-final-matrix-20260704-final-report/phase6_fake_matrix_report.json`
  as the current residue-clean JSON report, with rows JSONL beside it and
  Markdown at
  `/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6-real-capability-assessment-20260704.md`.
  Use these as the current reviewer-audit evidence package.
- Reviewer2 accepted the updated docs/handoff state after one stale lifecycle
  wording edit in `job_b45ba6df0d10`:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_b45ba6df0d10-art_eccfb8c67a104427.txt`.
  This is not a Phase 6A acceptance verdict.
- Final source-control packaging hygiene decisions from `worker2`
  `job_ac6140294b18` are present in the worktree in
  [topics/phase1-6-final-packaging-hygiene.md](../topics/phase1-6-final-packaging-hygiene.md):
  ignore `dist/` and `dist-mobile/`, include Satinoos Markdown/SVG plus
  selected PNG/PDF outputs, defer `claude_pane.py` and its test to managed-provider
  reliability, and include the reviewed shared README/topic edits as Phase 1-6
  / Decision 020 context. Completion evidence:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ac6140294b18-art_3982631569024f29.txt`.
  Worker2 refresh `job_20d089747749` confirmed that this visible worktree state
  is the completed packaging hygiene package:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_20d089747749-art_fd4b337941724d2a.txt`.
  Reviewer2 accepted this as final packaging hygiene guidance in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_08484caac091-art_1299c45369de43a4.txt`.
  Final slice-aware staging/package execution is still pending.
  Dry-run final staging manifest:
  [topics/phase1-6-final-staging-manifest-20260704.md](../topics/phase1-6-final-staging-manifest-20260704.md).
  It classifies the current `git status --short` inventory and provides
  review-only staging command shapes; it does not stage or commit files.
  Reviewer2 accepted it for human package-owner staging review in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_6e27efd2bf13-art_734269e45fd04a07.txt`.
  Worker3 tightened broad dry-run command paths in `job_cd066f5d6147`;
  reviewer2 accepted the tightened manifest for human package-owner final
  staging review in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_055a5e798708-art_2255afc4ca87434a.txt`.
  Final human staging/package execution is still pending.
- Phase 6B launch-readiness docs from `worker3` `job_a3d68dcac65d` are
  complete as planning/readiness cleanup, including
  [topics/phase6b-real-provider-lab-launch-checklist.md](../topics/phase6b-real-provider-lab-launch-checklist.md):
  Phase 6A/busy-release/task-pack blockers are marked closed, and remaining
  launch blockers are launch-review acceptance of the recorded provider map,
  inherited-provider-home risk, exact lab-local RolePack seeding, exact launch
  command/schema, B7 normalization procedure, and reviewer launch-gate
  approval. Completion evidence:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_a3d68dcac65d-art_b2de958d32e043a6.txt`
  and formalization
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_784116ffdc92-art_fbd45b71153b4746.txt`.
  Reviewer2 accepted this as planning/readiness cleanup only in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_af0277c593a5-art_fd27e853e98f4830.txt`;
  this is not L0 launch approval.
- L0-only launch-request draft from `worker3` `job_01dbb84db190` is present at
  [topics/phase6b-l0-launch-request-20260704.md](../topics/phase6b-l0-launch-request-20260704.md).
  It was approved for one bounded L0 run by reviewer2 `job_960ec614c477`, then
  executed once under `talk2` supervision. The result is recorded in
  [history/phase6b-real-provider-l0-b7-20260704.md](phase6b-real-provider-l0-b7-20260704.md)
  and classified as `test_design_failure`, not Phase 6B readiness: variant A
  used the wrong ask target (`ccb_orchestrator` instead of the mounted
  `phase6b-l0-ccb-orchestrator`), variant B used an invalid long proposal id,
  the approved normalizer failed on missing B runtime artifacts, and cleanup was
  not clean before the external project was killed successfully. Completion
  evidence for the original draft:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_01dbb84db190-art_dc9e90ae951147b6.txt`.
  Reviewer2 accepted it as planning/readiness state only in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_409627815844-art_8f98469016924af7.txt`;
  this is not launch approval.
- Keep Phase 6B unclaimed. The corrected repeat L0 launch request was approved
  once by reviewer2 in `job_f3adf3a31988` and executed once from
  `/home/bfly/yunwei/test_ccb2` under `talk2` supervision. That approval is
  consumed. The repeat result is
  [history/phase6b-real-provider-l0-repeat-b7-20260704.md](phase6b-real-provider-l0-repeat-b7-20260704.md)
  and is classified as `test_design_failure`, not Phase 6B readiness: the
  command log stopped after `ask_a_orchestrator_compact`, A release and all
  variant B commands were missing, and the supervisor diagnosis is that
  executing the frozen block through stdin piping allowed `ccb_test ask` to
  inherit/consume the remaining script body. Post-B7 external cleanup returned
  `kill_status: ok` and `state: unmounted`.
- Keep Phase 6B unclaimed after repeat2. Reviewer2 approved one repeat2 run in
  `job_041526ab5f10`; talk2 executed it once from
  `/home/bfly/yunwei/test_ccb2` using the fixed root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704`. That
  approval is consumed. The repeat2 result is
  [history/phase6b-real-provider-l0-repeat2-b7-20260704.md](phase6b-real-provider-l0-repeat2-b7-20260704.md)
  and is classified as `test_design_failure`, not Phase 6B readiness. The
  stdin harness fix worked and the script reached variant B: variant A compact
  ask submitted as `job_40835bfeed99` to
  `phase6b-l0-ccb-orchestrator`; `topology_a_release` returned `0` but left
  the dynamic orchestrator busy/bound with `released_count=0`; variant B then
  failed at commit/apply with `agent profile ccb_orchestrator exceeds
  max_instances=1`. The approved B7 normalizer also failed before writing
  evidence because it used `hashlib.sha256` without importing `hashlib`, so
  talk2 generated a supervisor fallback B7 from command logs and runtime
  artifacts. Post-B7 cleanup returned `kill_status: ok` and `state:
  unmounted`. The follow-up repair now makes active post-release dynamic
  topology residue explicit as `release_incomplete`, adds a repeat3 harness gate
  that stops before B when A release is not clean, fixes the B7 normalizer
  `hashlib` import, and uses fresh root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704`. That
  repeat3 approval/run is now historical and consumed; no Phase 6B readiness was
  claimed.
- Keep Phase 6B unclaimed after repeat3. Reviewer2 approved one repeat3 run in
  `job_90cc9a80d7a0`; talk2 executed it once from
  `/home/bfly/yunwei/test_ccb2` using the fixed root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704`. That
  approval is consumed. The repeat3 result is
  [history/phase6b-real-provider-l0-repeat3-b7-20260704.md](phase6b-real-provider-l0-repeat3-b7-20260704.md)
  and is classified as `test_design_failure`, not Phase 6B readiness. The
  release gate worked as designed: A compact ask submitted as
  `job_b7a8ed0f671e`, `topology_a_release` reported
  `loop_topology_status=release_incomplete`, and
  `topology_a_release_clean_check` returned `66` before variant B. Post-B7
  cleanup returned `kill_status: ok` and `state: unmounted`. The remaining
  blocker is the B7 normalizer/runtime ask-evidence contract: it still expects
  `.ccb/runtime/asks.jsonl`, while actual ask evidence for this run existed at
  `.ccb/agents/phase6b-l0-ccb-orchestrator/jobs.jsonl`. The follow-up repair now
  updates the launch-request B7 normalizer contract to discover dynamic-agent
  `jobs.jsonl` and ccbd job/message artifacts as ask evidence, with regression
  coverage for the release-gate-blocked path. No Phase 6B readiness is claimed.
- Keep Phase 6B unclaimed after repeat4. Reviewer2 approved exactly one
  repeat4 run in `job_46d3377feb21`; talk2 executed it once from
  `/home/bfly/yunwei/test_ccb2` using the fresh root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat4-20260704`. That
  approval is consumed. The repeat4 result is
  [history/phase6b-real-provider-l0-repeat4-b7-20260704.md](phase6b-real-provider-l0-repeat4-b7-20260704.md)
  and is classified as `valid_non_success`, not Phase 6B readiness. Variant A
  submitted ask job `job_0f9d5c50b756` to
  `phase6b-l0-ccb-orchestrator`; `topology_a_release` reported
  `loop_topology_status=release_incomplete`, and
  `topology_a_release_clean_check` returned `66` before variant B. The repaired
  B7 normalizer accepted dynamic-agent/ccbd ask evidence, found no missing
  command labels, no missing artifacts, no input errors, and no test-design
  failures. Post-B7 cleanup returned `kill_status: ok` and `state: unmounted`.
  User decision "方案 2：只跑 B，不跑 A" is now reflected in the B-only repeat5
  launch request. No Phase 6B readiness is claimed.
- Keep Phase 6B unclaimed after B-only repeat5. Reviewer2 approved exactly one
  B-only repeat5 run in `job_2953f5e7ab7e`; talk2 executed it once from
  `/home/bfly/yunwei/test_ccb2` using the fresh root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704`.
  That approval is consumed. The repeat5 result is
  [history/phase6b-real-provider-l0-b-only-repeat5-b7-20260704.md](phase6b-real-provider-l0-b-only-repeat5-b7-20260704.md)
  and is classified as `valid_non_success`, not Phase 6B readiness. The B-only
  command block mounted the resident planning group and submitted compact ask
  `job_699a6c2997ad` to `p6bl0b-orchestrator`; all command labels returned
  `0`, ask reachability was true, required artifacts were present, script
  sha256 matched, and no test-design failures or authority-write violations
  were recorded. The non-success reason is release residue:
  `topology_b_release` reported `release_incomplete` for `p6bl0b-frontdesk`,
  `p6bl0b-detailer`, `p6bl0b-planner`, and `p6bl0b-orchestrator`. Post-B7
  cleanup returned `kill_status: ok` and `state: unmounted`. Worker1
  `job_26e39b154740` then landed a source-side release/drain repair so future
  resident planning-group releases can report explicit `drained_agents` while
  preserving parked provider sessions. Any further L0 command still requires
  fresh launch-specific approval.
- Release/drain product repair lane: talk2 delegated the repair to worker1 in
  `job_26e39b154740`; reviewer2 accepted the implementation in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_50ce63ab373b-art_159c32ab43394689.txt`.
  The accepted behavior treats absent resident agents observed as parked as
  drained release agents, prunes them from loop topology authority, leaves their
  lifecycle records parked/dispatch-disabled, preserves retained-busy priority,
  and updates B7 normalization so parked provider sessions do not have to be
  killed for a clean resident release. This is not L0 launch approval and does
  not claim Phase 6B readiness. The read-only reviewer1 checklist request
  `job_8d1df3ab4b5a`
  completed at
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_8d1df3ab4b5a-art_e51879613e664273.txt`.
  It sets the pending fix's acceptance bar: no fake `released` state while
  agents remain active; active/busy/inherited-provider-home residue must be
  retained with explicit bounded reasons; no topology DSL or provider-reply
  authority parsing; any later L0 rerun requires fresh reviewer2 approval. It
  also flags one blocker for the matrix/report lane: `release_incomplete` with
  explicit blockers must classify as `valid_non_success` in matrix/report
  evidence, not as an unclassified cleanup string. Do not treat either job as L0
  launch approval, Phase 6B acceptance, or permission to rerun real-provider
  commands.
- Matrix/report classification lane: talk2 delegated reviewer1 B1 to worker2 in
  `job_692502f50c7d`, then submitted a narrower follow-up as
  `job_3fd8ef33538c` after the visible tree still had a classification gap.
  Reviewer1 accepted the visible fix in direct read-only audit
  `job_ebe46ce6cd8b`:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ebe46ce6cd8b-art_c895cae3d4ac466f.txt`.
  Accepted behavior: `release_incomplete_agents` plus bounded
  `release_blockers` classifies as `valid_non_success`; missing, vague, or
  unbounded blocker evidence remains a hard failure. Reviewer1 verified
  `py_compile`, `python -m pytest test/test_phase6_fake_matrix_smoke_script.py
  -q` with 18 passing tests, and direct probes. No source-wrapper, `ccb_test`,
  real-provider, L0, or L1-L4 commands were run. Residual risk:
  future B7 normalizers must emit blocker reason text matching the bounded
  marker vocabulary, or valid residue will still classify as `system_failure`.
- B-only repeat6 L0 runtime-sanity lane: talk2 delegated launch-request prep to
  worker3 as `job_4e82bb56cb03`; reviewer2 granted launch-specific
  approval-to-run in `job_8c7b404ad63c`, with package approval also recorded in
  `job_c7ebe2d2dade`. Talk2 executed exactly one approved run from
  `/home/bfly/yunwei/test_ccb2` using root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704`.
  The B7 report
  [history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md](phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md)
  classifies the row as `pass`: ask reachability was true for
  `job_4181721f9473`, all command labels returned `0`,
  `topology_b_release` reported `released`, all four resident planning-group
  agents appeared in `drained_agents` with `parked_after_release`, and post-B7
  cleanup returned `kill_status: ok` / `state: unmounted`. This consumes the
  repeat6 approval and remains L0-only evidence, not Phase 6B readiness.
- Phase 6B L1-L4 planning package is accepted as planning/readiness prep only.
  Worker3 completed it in `job_5c007d3bab56`; reviewer1 accepted it in
  `job_b9eac0af0f9e` with no blockers/high findings:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_b9eac0af0f9e-art_973372060e54411a.txt`.
  The package is
  [topics/phase6b-l1-l4-launch-prep.md](../topics/phase6b-l1-l4-launch-prep.md)
  and contains concrete L1, L2, L3 `needs_detail`, L4
  `macro_adjustment_request`, and L4 `blocked` task candidates with prompts,
  expected routes/statuses, evidence rows, cleanup expectations, B7 aggregation,
  and stop conditions. It does not approve runtime. L1-L4 remain blocked on
  fresh launch-specific approval. The frozen follow-up request
  [topics/phase6b-l1-l4-launch-request-20260704.md](../topics/phase6b-l1-l4-launch-request-20260704.md)
  prepares a fresh repeat3 root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704`,
  all five accepted candidate ids in sequence, L3 bounded at `detail_ready`,
  fixture materialization with hashes, static command/checkpoint shape, and B7
  aggregation schema. Reviewer2 accepted it as `DOC-ONLY ACCEPTED` in
  `job_c0fac249749e`:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c0fac249749e-art_85be7618d4844d01.txt`.
  No approval-to-run is granted. The later repeat2 launch approval
  `job_0c8596e0895d` was consumed once and showed the plan-root fix worked
  through L1 orchestrator activation, but exposed a new driver bug:
  supervisor import files were placed under the outer lab root instead of the
  lab project root, so `plan task-artifact --file` rejected them. Residual
  risks before any future approval-to-run: real-provider `loop runner --once`
  multi-task behavior is unproven, L3 post-detail execution remains deferred,
  and reviewer-rework/partial observation remains a Phase 6B claim blocker.
  Static hardening `job_82d723ec0f89` adds conservative `authority_checks.*`
  output in the L1-L4 embedded normalizer and an embedded L5
  reviewer-rework/partial normalizer shape; reviewer2 accepted it in
  `job_f20daf37898d` as docs/tests readiness only. It still grants no launch
  approval.

## Last Landed

- Phase 1 mount topology schema split is formally accepted in the current
  worktree, but is not yet committed or default-enabled:
  `ccb loop topology` now writes `agent_mount_topology.desired.json`, accepts
  `ccb.loop.agent_mount_topology.v1`, reads legacy `agent_topology.*` files
  when new files are absent, rejects `edges`, `gates`, and `artifacts` by
  default, and keeps legacy graph dispatch behind explicit compatibility
  markers. This is not committed yet.
- Phase 2 document anchors and activation state are landed in this worktree:
  `ccb plan task-artifact` accepts `task_packet`, `execution_contract`,
  and `orchestration_notes`; task records now carry
  machine-readable `status`, `next_owner`, `current_loop`, and
  `activation_reason`; `ready_for_orchestration` requires both
  `task_packet` and `execution_contract`; orchestration notes import as
  non-authority evidence; and `task-import-round` writes first-class
  `round_summary.md` while preserving legacy round aliases for migration.
- Phase 3A orchestrator triage router is accepted in this worktree after
  reviewer1 audit and source-wrapper smoke:
  `ready_for_orchestration + next_owner=orchestrator` with no imported route
  now activates `orchestrator` once and stops. The activation packet includes
  task packet, execution contract, existing orchestration notes refs/compact
  content, and the allowed routes `direct_execution`, `needs_detail`,
  `macro_adjustment_request`, and `blocked`; it instructs route import through
  `ccb plan task-artifact --kind orchestration_notes --route <route>`.
- Imported `orchestration_notes --route` now drives only the next runner
  decision: `needs_detail` activates `task_detailer` on demand and returns to
  orchestrator after detail packet artifacts exist; `direct_execution` runs the
  Phase 4A ask-first direct-execution round; macro-adjustment and blocked
  routes pause without mounting workers. Route notes still do not mark work
  done or blocked by themselves.
- Runner mainline remains topology-dispatch-free and does not parse provider
  reply text for route/status authority. Legacy `ready` records without
  activation metadata keep the bounded fixed bridge compatibility path.
- Phase 4A direct-execution ask-first path is accepted after reviewer1 audit
  and source-wrapper smoke: `direct_execution` applies a
  `coder + code_reviewer` mount proposal, coordinates asks through CCB `ask`,
  imports `round_summary`, releases the ephemeral pair, and writes no
  `topology_dispatch.json`. The ask-first source proposal, normalized
  proposal, committed desired topology, and observed topology no longer emit
  absent `edges`, `gates`, or `artifacts`; those remain legacy dispatch
  compatibility concepts, not mainline mount-topology fields.
- Phase 5A failure cleanup is accepted after reviewer1 audit: non-ready mount
  topology stops before worker/reviewer asks, submit/watch failures and
  missing/unknown round results import blocked round evidence, recoverable
  failures clear `running + current_loop`, and dynamic execution agents are
  released through the lifecycle path.
- V1 planner brief + task_detailer detail-packet import slice:
  `ccb plan task-artifact` now accepts `brief`, `detail_design`,
  `detail_summary`, `detail_packet`, and `macro_adjustment_request`; planner
  bundles may import compact `brief.md` and macro task-packet artifacts only;
  task_detailer bundles may import task-scoped detail docs, a detail packet
  manifest, and optional macro adjustment requests.
- `detail_ready` now requires the task_detailer three-piece packet:
  `detail_design`, `detail_summary`, and `detail_packet`. A
  `macro_adjustment_request` is preserved as an artifact/ref and does not apply
  planner authority or advance status by itself.
- Planner-side compact import policy is landed for `detail_summary`,
  `macro_adjustment_request`, and `round_summary`: compact artifacts carry
  `planner_compact_import` metadata listing macro-only allowed update
  surfaces and forbidden detail imports; `macro_adjustment_request` remains
  request-only; and generic `task-artifact --kind round_summary` is rejected so
  round results must use script-owned `task-import-round`.
- The previous `ccb loop runner --once --consume-role-output` bundle-consume
  path is legacy/disabled under Decision 020. Script-owned artifact imports and
  explicit `ccb plan task-status` transitions are the authority path.
- The fake provider now supports deterministic workflow replies for planner,
  ccb_task_detailer, plan-reviewer, and round-checker `round result: pass`
  smoke.
- `scripts/workflow_closure_smoke.py` now includes the current pre-triage
  ccb_task_detailer stage in the official fake-provider closure smoke.
- `ccb loop topology` now applies the CCB workflow window contract by default:
  V1 resident `ccb_frontdesk` and `ccb_task_detailer` land in `ccb-user`;
  V1 resident `ccb_planner` and `ccb_orchestrator` land in `ccb-plan`;
  on-demand `ccb_round_reviewer` also lands in `ccb-plan` when round-review
  topology needs it; active `coder + code_reviewer` agents pack six panes per
  `ccb-exec` page and compact overflow pages during reconcile.
- Topology reconcile stages missing desired agents as one lifecycle add batch
  before mounted reload, releases absent agents before compaction moves, and
  dynamic overlay-created runtime windows now use append-compatible layout
  specs so an existing `ccb-exec` page can grow from one work pair to two
  without forcing a context-losing pane rebuild.
- Follow-up audit fixed the shrink/compaction observed-state summary: when a
  later desired topology omits a previously mounted execution pair, reconcile
  now reports the removed agents through `released_count` and
  `released_agents` instead of only compacting the config.
- Worker2 dispatch-contract review identified topology-driven dispatch as a
  release blocker and added contract coverage. Follow-up validation now rejects
  unsupported topology edge types and legacy workflow profile aliases such as
  `worker`, `checker`, `round_checker`, `ccb_worker`, `ccb_checker`, and bare
  planner/orchestrator/detailer aliases before runtime reconciliation.
- The previous topology-dispatch experiment is no longer a runner mainline:
  `ccb loop runner --once` selects tasks only through task document state,
  does not consult topology-dispatch discovery, and does not execute committed
  topology `ask` / `ask_after` edges.
- Legacy `topology_dispatch.py` remains covered as bounded compatibility code,
  but mounted topology is now treated as mount/window/provider/lifecycle
  authority rather than a communication DSL.
- When a running task is already bound to a loop, the runner returns a paused
  `ask_first_execution_not_ready` payload with the bound `current_loop` and
  writes no topology dispatch runtime artifacts.

Evidence:

- Compact Phase 1-6 evidence index:
  [history/phase1-6-evidence-index.md](phase1-6-evidence-index.md).
  Use that file for accepted-review and checklist navigation; keep this status
  file focused on current handoff.
- Independent Phase 1 acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_901b6d77e156-art_7a7117480eab4689.txt`
  (reviewer2: Phase 1 accepted, no blocker/high findings). Medium notes are
  legacy compatibility fields in explicit legacy proposals, the updated
  observed pass count for the capacity/workflow-smoke bundle, and refreshing
  the external Phase 1 smoke artifact during final Phase 6 reporting.
- Independent Phase 3A acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c27531f0d6ac-art_135e832a12844b2c.txt`
  (reviewer1: acceptable, no high issues). Follow-up source-wrapper smoke from
  `/home/bfly/yunwei/test_ccb2/phase3a-triage-smoke-routes-YiiWhm` returned
  `phase3a_triage_smoke=ok`, covered `needs_detail`, `direct_execution`,
  `macro_adjustment_request`, and `blocked`, and confirmed no
  `topology_dispatch.json`.
- Independent Phase 4A acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_477271c7d115-art_fe93361dc9144451.txt`
  (reviewer1: Phase 4A acceptable, no blocker/high issues). The review
  independently reran a source-wrapper smoke after persistence hardening and
  recorded `workflow_smoke_status=ok`, `execution_mode=ask_first_direct_execution`,
  `dispatch_source=ask_first_mount_topology`, final status `done`,
  `round_summary_imported=true`, dynamic execution agents released, resident
  roles retained, and no `topology_dispatch.json`.
- Independent Phase 5A acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_a0c108e8b37a-art_8a672dcbb5404df0.txt`
  (reviewer1: Phase 5A accepted, no blockers). Residual medium notes are
  source-wrapper failure-mode smokes, partial-add release confidence, and
  `ccb_round_reviewer` naming alignment.
- Independent Phase 6A scaffold review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5b00939a7c0b-art_507140d2c6e14c58.txt`
  (reviewer2: accepted with residual notes as a scaffold only). The scaffold
  correctly reported incomplete and `phase6a_pass=false` while required matrix
  closure was incomplete. The later residue-clean integrated matrix is now
  accepted for the Phase 6A program-matrix scope.
- Phase 6 route-matrix runtime tranche checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c4a59d18bb49-art_48f7596bf35049a2.txt`
  (reviewer1: checklist only, not an acceptance verdict). The tranche scope is
  `needs_detail`, `macro_adjustment_request`, and `blocked`; `partial_completion`
  is deferred unless it lands without broad rewrites.
- Phase 6 route-matrix runtime tranche acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_240557da6f39-art_cafd3ad2ac1541c2.txt`
  (reviewer1: accepted). `needs_detail`, `macro_adjustment_request`, and
  `blocked` are accepted; Decision 020 invariants remain intact; the matrix
  correctly kept `phase6a_pass=false` while incomplete. The later
  non-lifecycle tranche accepted `partial_completion`, reviewer reject/rework,
  and reviewer cannot accept; the later `smoke-busy-release` single-case
  runner is accepted in `job_7fb1ad254939`; the residue-clean integrated
  matrix is accepted in `job_712002b8f005`.
- Remaining Phase 6 matrix tranche checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_10f4edb64910-art_42ad97f3a16d41eb.txt`
  (reviewer1: checklist only, not an acceptance verdict). It defines acceptance
  for `partial_completion`, reviewer reject/rework, reviewer cannot accept, and
  busy-release. The later runner/test package and integrated matrix have
  reviewer acceptance.
- Remaining non-lifecycle Phase 6 matrix tranche from worker1:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ee4475e034ec-art_dd0c1e75aa8a401c.txt`
  (worker evidence). Reviewer1 accepted the three non-lifecycle cases in
  `job_67657b4505b1`:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_67657b4505b1-art_bfe488836bb447f8.txt`.
  It covers `partial_completion`, reviewer reject/rework, and reviewer cannot
  accept; `smoke-busy-release` is later accepted in `job_7fb1ad254939`.
- Module-level and final-report acceptance checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_9cb0746fad98-art_25c9e57d83a840c1.txt`
  (reviewer2: checklist only, not an acceptance verdict). It defines the
  module-level gates, Phase 6A/6B claim gates, and required final report shape.
- Draft Phase 1-6 acceptance report skeleton:
  [history/phase1-6-acceptance-report-draft.md](phase1-6-acceptance-report-draft.md)
  from worker3 `job_71da7d32150a`
  (`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_71da7d32150a-art_c460458d607043ae.txt`).
  This was initially `DRAFT / INCOMPLETE`; it now records the accepted Phase
  6A program-matrix scope and still does not claim Phase 6B closure.
- Phase 6B real-provider lab readiness checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_723a4456a783-art_19fdabce655a4233.txt`
  (reviewer2: not ready). The original checklist required Phase 6A
  fake-provider matrix closure and Phase 5 lifecycle busy-retain closure; those
  are now accepted. Remaining Phase 6B launch prerequisites still include
  launch-review acceptance of inherited-provider-home risk, lab-local RolePack
  seeding commands, exact launch command/schema, frozen evidence schema, and
  B7 reviewer gate setup.
- Phase 6B L0-L5 real-provider task-pack draft:
  [topics/phase6-real-provider-lab-task-packs.md](../topics/phase6-real-provider-lab-task-packs.md)
  from worker3 `job_82bd13bd29b9`
  (`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_82bd13bd29b9-art_70525b7c7898481e.txt`).
  Reviewer2 accepted it as planning input in `job_5ce23d15f100`
  (`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5ce23d15f100-art_909fc6ba1eaa410b.txt`)
  with no blocker/high findings. It remains planning input only and is not a
  lab launch approval.
- Phase 6B launch-readiness checklist:
  [topics/phase6b-real-provider-lab-launch-checklist.md](../topics/phase6b-real-provider-lab-launch-checklist.md)
  separates prerequisites closed by Phase 6A from open L0 launch gates. It is
  not launch approval.
- Phase 6B L0-only launch request:
  [topics/phase6b-l0-launch-request-20260704.md](../topics/phase6b-l0-launch-request-20260704.md)
  records owner decisions for the L0 provider map, inherited-provider-home
  policy, seven-role seed scope, B-only resident-planning-group topology scope,
  compact ask schema, timeout, B-only repeat6 request shape, dynamic-agent
  ask-evidence normalization, and `talk2` normalization owner. Repeat6 has
  executed once and passed L0 runtime sanity; that approval is consumed and
  cannot authorize another run.
- Phase 6A fake-provider matrix closure runbook:
  [topics/phase6a-fake-provider-matrix-closure-runbook.md](../topics/phase6a-fake-provider-matrix-closure-runbook.md)
  from worker3 `job_30fb5b4a6ffc`
  (`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_30fb5b4a6ffc-art_5e90da8f2dcf4303.txt`).
  Reviewer2 accepted it as planning input in `job_78dfa7c30af0`
  (`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_78dfa7c30af0-art_ac73033fc697442c.txt`)
  with no blocker/high findings. It has since been updated to record the
  completed integrated matrix run and reviewer acceptance.
- Phase 6A closure sequencing audit:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_bee533da6307-art_9fd45895a47145be.txt`
  (reviewer1: sequencing audit, not an acceptance verdict). Active jobs are
  necessary but not sufficient; after worker/reviewer gates close, an
  integrated source-wrapper matrix run, module-level audit, and dated final
  acceptance report remain distinct integrator/reviewer tasks.
- Phase 6A scaffold hardening acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_953728534f32-art_1af95df6a0814a08.txt`
  (reviewer2: accepted; scaffold/report hardening only). Product route runners
  remain open.
- Formal RolePack package acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_0cab915b5071-art_0affd7907e51440d.txt`
  (reviewer2: accepted). This closes the missing-formal-RolePack portion of
  the Phase 6A blocker for `agentroles.ccb_task_detailer`,
  `agentroles.ccb_round_reviewer`, `agentroles.coder`, and
  `agentroles.code_reviewer`; runtime target and source-wrapper smoke
  migration remain open.
- Target-name/source-wrapper RolePack migration acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_be1921a3e3d8-art_f4d19138b1684864.txt`
  (reviewer2: accepted). Ask-first now targets `ccb_round_reviewer`;
  source-wrapper smoke uses the accepted RolePack ids; legacy `round_checker`
  remains compatibility-only.
- Planner compact-import policy checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ce8adccd030c-art_9b448c591b3e47cf.txt`
  (reviewer2: checklist only, not an acceptance verdict). It defines blockers
  for macro-only planner import of `detail_summary`,
  `macro_adjustment_request`, and `round_summary`.
- Planner compact-import policy acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_fbd5863fb80c-art_1928abb5b1284568.txt`
  (reviewer2: accepted). This closes the planner-side compact import policy
  TODO; remaining work is route runners, lifecycle closure, matrix scaffold
  wiring, and final Phase 6A source-wrapper matrix audit.
- Planner compact-import traceability follow-up from worker1
  `job_6fc415cce199`: test-only tightening proves compact imports do not move
  `status`, `next_owner`, or `current_loop` on `detail_summary` /
  `macro_adjustment_request`, and asserts `sha256`, `actor.job_id`, and
  `imported_at` traceability for compact imports and script-owned
  `round_summary`.
- Remaining Phase 5 lifecycle closure checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_a715b88063ad-art_1bd7d58cd0d14087.txt`
  (reviewer1: checklist only, not an acceptance verdict). It covers busy retain,
  resident preservation, reflow identity, overflow windows, park/resume,
  source-wrapper failure hooks, and runtime residue audits.
- RolePack/name inventory:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_987a48380278-art_0c4ce25a7e5f43ed.txt`
  (worker2: inventory only). It identifies missing formal RolePacks and active
  legacy `round_checker` target usage as must-migrate items before Phase 6A.
- Independent Phase 2 acceptance review:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f16656e84115-art_bc343f598772478a.txt`
  (reviewer2: no Phase 2 blockers remain).
- [history/workflow-role-output-import-2026-07-02.md](workflow-role-output-import-2026-07-02.md)
- [goals/minimum-production-candidate-goal.md](../goals/minimum-production-candidate-goal.md)

## Active TODO

1. Freeze the remaining F1 authority interfaces: task revision, capacity
   snapshot/digest, final bundle/node schemas, and node-keyed exact-once key.
2. Complete G1 so the one-group path uses node state exclusively and no normal
   post-worker orchestrator activation remains.
3. Run the goal's parallel R1/C1/P1 packages, integrate them one at a time,
   then start R2/T1/E1 only after the first wave gate passes.
4. Complete Git integration and exact-once 2-4 workgroup scheduling, including
   topology, busy-retain, rollback, restart, and residue evidence.
5. Implement Config V3 with two resident roles, five immaculate dynamic
   profiles, provider/model/RolePack validation, explicit semantic/physical
   capacity, then run direct `talk2` source/fake/visible-real/package gates.

## Next Gate

Complete F1 and the remaining G1 closure in
[goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md):
bind the final authority envelope, move the current one-workgroup route wholly
onto the generalized node engine, and remove the normal post-worker
orchestrator before starting Git integration or parallel workgroups.

## Blocked By

No external dependency blocks F1/G1. Source implementation is blocked only on
keeping the new bundle/controller boundary and Config V3 lifecycle contract
coherent. Multi-lane work, default enablement, and publication remain blocked
until the single-lane multi-workgroup goal passes. Exact release version and
registry state are intentionally resolved at the final clean release gate so a
published version is never guessed or reused.

## Last Verified

- Worker3 sequence12 packet static preflight: `python -m py_compile
  test/test_phase6b_l1_l4_launch_request_doc.py` passed; `python -m pytest
  test/test_phase6b_l1_l4_launch_request_doc.py -q` -> `26 passed`;
  `python -m pytest test/test_phase6b_l1_l4_launch_request_doc.py
  test/test_phase6b_l5_launch_request_doc.py
  test/test_phase6b_l5_rework_partial_tranche_doc.py -q` -> `33 passed`;
  `git diff --check` on touched docs/tests was clean; root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`
  was absent. No runtime/provider/source-wrapper/L1-L4/L5/B7/cleanup/launch
  command was run.
- Talk2 sequence12 self-review and runtime execution on 2026-07-05:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` from
  `/home/bfly/yunwei/test_ccb2` passed; root and B7 path were absent before
  materialization; `init`, L1/L2 direct execution, L3 `needs_detail ->
  detail_ready`, L4 `macro_adjustment_request -> replan_required`, and L4
  `blocked -> blocked` completed. The run exposed and talk2 repaired a source
  status-transition gap for `ready_for_orchestration -> replan_required` and
  `ready_for_orchestration -> blocked` using script-owned
  `macro_adjustment_request` / `blocker_evidence` artifacts. B7
  `history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md` reports
  `Status: pass`, all five rows `claimable_row=true`, and classifications
  `pass, pass, valid_non_success, valid_non_success, valid_non_success`.
  `cleanup-after-b7` returned `kill_status: ok`, `state: unmounted`.
- Talk2 final aggregation on 2026-07-05: created
  `history/phase1-6-acceptance-report-20260705.md`, updated the evidence
  index, claim coverage matrix, active supervision board, README, and static
  doc tests. No additional provider/runtime command was run for aggregation.
- Talk2 static preflight for the current L5 repeat4 packet: `python -m
  py_compile lib/cli/services/loop_ask_first.py test/test_loop_capacity_cli.py
  test/test_phase6b_l5_launch_request_doc.py
  test/test_phase6b_l5_rework_partial_tranche_doc.py` passed;
  `python -m pytest test/test_phase6b_l5_launch_request_doc.py
  test/test_phase6b_l5_rework_partial_tranche_doc.py -q` -> `7 passed`;
  `python -m pytest test/test_loop_capacity_cli.py -q` -> `37 passed`;
  L1-L4/L5 doc bundle -> `16 passed`; `git diff --check`,
  whitespace sanity, Markdown relative-link sanity passed; repeat4 root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704`
  was absent before execution.
- Talk2 consumed reviewer2 approval `job_5dd131a6ea7e` exactly once for L5
  partial-only repeat4. Runtime reached `direct_execution`, worker/reviewer/
  ccb_round_reviewer completed, task state became `partial`, dynamic topology
  released with no blockers, B7 normalized to `valid_non_success`, and
  post-B7 cleanup returned `state: unmounted`.
- Worker1 release/drain repair `job_26e39b154740`: `python -m py_compile
  /home/bfly/yunwei/ccb_source/lib/cli/services/loop_topology.py` passed, and
  targeted pytest passed with `45 passed` for `test_loop_topology_cli.py`,
  `test_loop_topology_dispatch_contract.py`,
  `test_phase6_fake_matrix_smoke_script.py`, and
  `test_phase6b_l0_launch_request_doc.py`. Reviewer2 accepted in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_50ce63ab373b-art_159c32ab43394689.txt`.
  No source-wrapper, CCB runtime, or real-provider/L0 launch command was run.
- B-only repeat6 L0 runtime sanity: reviewer2 approved one run in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_8c7b404ad63c-art_948e9db1551a4458.txt`;
  talk2 executed it once from `/home/bfly/yunwei/test_ccb2`, generated
  [history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md](phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md)
  with `classification=pass`, then ran post-B7 cleanup with `kill_status: ok`
  and `state: unmounted`.
- Draft Phase 1-6 acceptance report skeleton from worker3
  `job_71da7d32150a`: relative Markdown link sanity passed; draft/claim
  marker sanity originally confirmed `DRAFT / INCOMPLETE` and `not claimable`;
  later docs now record Phase 6A program-matrix acceptance. Targeted
  `git diff --check` for the report and status docs passed in that earlier
  review. No source runtime commands were run.
- Dated final report created:
  [history/phase1-6-acceptance-report-20260704.md](phase1-6-acceptance-report-20260704.md).
  It records Phase 6A program-matrix acceptance and keeps Phase 6B blocked.
- Phase 6B L0-L5 task-pack draft from worker3 `job_82bd13bd29b9`: relative
  Markdown link sanity for the new topic and README passed; marker sanity for
  `DRAFT / NOT READY TO RUN`, L0-L5, Phase 6A/6B, and isolation terms passed;
  targeted `git diff --check` passed. No source runtime or real-provider
  commands were run.
- Reviewer2 Phase 6B task-pack planning-gate review `job_5ce23d15f100`:
  accepted as planning input; no blocker/high findings; medium notes are
  unrelated README dirty edits and conditional clarification acceptance
  criteria. It explicitly does not approve running the real-provider lab.
- Worker1 remaining non-lifecycle Phase 6 matrix tranche `job_ee4475e034ec`:
  worker verification reports focused pytest `24 passed`, broader workflow
  bundle `104 passed`, source-wrapper smoke for the three new rows observed
  expected route/result/status/cleanup/classification, and overall incomplete
  status as expected because `smoke-busy-release` was not implemented in that
  tranche.
- Worker3 Phase 6A closure runbook `job_30fb5b4a6ffc`: markdown/link/marker
  sanity and targeted `git diff --check` passed; no source runtime commands
  were run.
- Reviewer2 Phase 6A runbook planning-gate review `job_78dfa7c30af0`: accepted
  as planning input; no blocker/high findings; medium notes are pre-existing
  README dirty edits, pending final eight-case command, and integrated run
  owner note. The runbook owner note was added after review.
- Reviewer1 Phase 6A closure sequencing audit `job_bee533da6307`: active jobs
  are necessary but not sufficient; remaining distinct tasks after active gates
  close are integrated full-matrix execution, module-level audit, and dated
  final acceptance report.
- Reviewer1 accepted worker1's remaining non-lifecycle Phase 6 matrix tranche
  in `job_67657b4505b1`: `smoke-partial-completion`,
  `smoke-reviewer-reject-rework`, and `smoke-reviewer-cannot-accept` all
  matched expected route/result/status/cleanup/classification evidence in
  isolated source-wrapper validation. `smoke-busy-release` remains correctly
  excluded until its runner is accepted using Phase 5 lifecycle closure
  evidence. The integrated
  eight-case matrix still must populate the full runtime residue fields before
  Phase 6A can be claimed.
- Reviewer1 single-case `smoke-busy-release` audit `job_d9820cc82c80` returned
  needs changes:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_d9820cc82c80-art_03a049a53f6f479e.txt`.
  Unit checks passed, but the source-wrapper run failed at `busy_worker_ask`
  with `error: unknown sender agent: phase6`. Worker2 follow-up
  `job_c690c97e0b8b` now provides the missing argv-level regression proof and
  single-case source-wrapper evidence. Reviewer1 accepted the single-case
  runner in `job_7fb1ad254939`: B1 is closed; `phase6a_pass=false` remains
  correct for the single-case report; integrated matrix still remains.
- Talk2 local re-validation after worker2 follow-up:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` from
  `/home/bfly/yunwei/test_ccb2` passed with isolated `HOME` and
  `CCB_SOURCE_HOME`; source-wrapper `--run-busy-release --json --timeout 120
  --reset` wrote
  `/home/bfly/yunwei/test_ccb2/phase6-busy-release-single-reaudit/phase6_fake_matrix_report.json`
  and returned incomplete status as expected for a single-case run. The busy
  row was observed with route `direct_execution`, `route_decision_correct=true`,
  `round_result=busy`, `final_status=running`, `cleanup_result=retained_busy`,
  classification `valid_non_success`, `ask_reachability=true`, runtime residue
  checks true, authority checks true, retained-busy evidence, and later idle
  release evidence. This is not reviewer acceptance.
- Earlier integrated source-wrapper matrix run from
  `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME`
  wrote
  `/home/bfly/yunwei/test_ccb2/phase6-final-matrix-20260704-talk2/phase6_fake_matrix_report.json`
  and returned `phase6_fake_matrix_status=pass`, `phase6a_pass=true`,
  `observed_case_count=8`, `implemented_case_count=8`, no missing cases, and
  no hard failures. It exposed the now-fixed audit gap: seven rows still had null
  `runtime_residue.config_dynamic_agents_absent` and
  `runtime_residue.observed_topology_residue_absent`, so worker3
  `job_9ee0c28fa49e` is assigned before module-level/final-report audit.
- Residue-clean integrated source-wrapper matrix run from
  `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME`
  wrote
  `/home/bfly/yunwei/test_ccb2/phase6-final-matrix-20260704-final-report/phase6_fake_matrix_report.json`,
  `/home/bfly/yunwei/test_ccb2/phase6-final-matrix-20260704-final-report/phase6_fake_matrix_rows.jsonl`,
  and
  `docs/plantree/plans/agentic-loop-workflow/history/phase6-real-capability-assessment-20260704.md`.
  It returned `phase6_fake_matrix_status=pass`, `phase6a_pass=true`,
  `observed_case_count=8`, `implemented_case_count=8`, no missing cases, no
  hard failures, and all three runtime residue booleans true for every row.
  Worker3 `job_9fff172b9685` then cleaned the generated Markdown wording:
  the report is titled "Phase 6 Fake-Provider Matrix Report", says 8/8 cases
  are observed, and no longer says missing/not-implemented cases remain.
- Reviewer2 accepted the updated Phase 6A handoff docs in
  `job_e36241800d67`: no blocker/high/medium findings; the evidence index,
  runbook, status, and draft report correctly separate accepted worker1 cases,
  open `smoke-busy-release`, later integrated matrix run, module-level audit,
  and final dated report.
- Worker3 completed source-control hygiene inventory in `job_cfb3cde1fe2c`.
  It recommends keeping Decision 020 / Phase 6A code, tests, RolePack drafts,
  matrix scripts, and acceptance docs in the final patch candidate, while
  requiring owner decisions for `dist-mobile/`, Satinoos binary assets,
  broad shared README/topic edits, and provider pane-status files.
- Reviewer2 completed final-packaging hygiene review in `job_fc9a05cdd528`:
  no Phase 6A program-matrix blocker; high packaging risks are `dist-mobile/`
  and mixed shared README/topic edits; medium risks are unowned
  `claude_pane.py` and Satinoos generated assets. Final source-control
  packaging must decide `.gitignore`/generated asset policy before a final
  acceptance commit or report package; see
  [topics/phase1-6-final-packaging-hygiene.md](../topics/phase1-6-final-packaging-hygiene.md).
- Module-level audit preparation is captured in
  [topics/phase1-6-module-level-audit-worksheet.md](../topics/phase1-6-module-level-audit-worksheet.md).
  It remains pending until `smoke-busy-release`, the full eight-case matrix,
  and per-case runtime evidence are available. Reviewer2 accepted the
  worksheet as planning/audit-prep state in `job_8f3c90ef8253`; no
  blocker/high/medium findings.
- Planner compact-import traceability follow-up from worker1
  `job_6fc415cce199`: focused tests -> `3 passed`;
  `python -m pytest test/test_plan_tasks_cli.py -q` -> `14 passed`;
  `python -m py_compile lib/cli/services/plan_tasks.py` -> passed; targeted
  `git diff --check` -> clean.
- Phase 5A follow-up verification after worker1 taxonomy reconciliation:
  `python -m pytest
  test/test_loop_capacity_cli.py::test_loop_runner_direct_execution_ask_failure_blocks_and_releases
  -q`
  -> `1 passed`.
- `python -m pytest test/test_loop_capacity_cli.py -q -k
  "direct_execution_route_runs_ask_first_round_without_dispatch or
  direct_execution_blocks_without_asks_when_topology_not_ready or
  direct_execution_ask_failure_blocks_and_releases or
  direct_execution_missing_round_result_blocks_before_release or
  direct_execution_unknown_round_result_blocks_and_releases"`
  -> `5 passed, 29 deselected`.
- `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
  test/test_loop_topology_cli.py test/test_loop_topology_dispatch_contract.py
  test/test_question_cli.py -q`
  -> `79 passed`.
- `python -m py_compile lib/cli/services/loop_topology.py
  lib/cli/services/loop_ask_first.py lib/cli/services/loop_runner.py
  lib/cli/services/plan_tasks.py scripts/phase6_fake_matrix_smoke.py
  test/test_phase6_fake_matrix_smoke_script.py`
  -> passed.
- `git diff --check -- lib/cli/services/loop_ask_first.py
  lib/cli/services/loop_runner.py test/test_loop_capacity_cli.py
  scripts/phase6_fake_matrix_smoke.py
  test/test_phase6_fake_matrix_smoke_script.py
  docs/plantree/plans/agentic-loop-workflow/implementation-status.md`
  -> clean.
- Phase 6A scaffold verification:
  `python -m pytest test/test_phase6_fake_matrix_smoke_script.py -q`
  -> `7 passed`; `python scripts/phase6_fake_matrix_smoke.py --json`
  exits `1` with `phase6_fake_matrix_status=incomplete` and
  `phase6a_pass=false`, as expected for the historical scaffold before matrix
  closure.
- Phase 6A scaffold hardening verification after worker3 `job_27002816e400`:
  `python -m py_compile scripts/phase6_fake_matrix_smoke.py
  test/test_phase6_fake_matrix_smoke_script.py` -> passed;
  `python -m pytest test/test_phase6_fake_matrix_smoke_script.py -q`
  -> `11 passed`; `python scripts/phase6_fake_matrix_smoke.py --json`
  exits `1` as expected with `phase6_fake_matrix_status=incomplete`,
  `phase6a_pass=false`, and all current rows classified under
  `summary.classification_counts.test_design_failure`.
- `reviewer1` Phase 5A audit, job `job_a0c108e8b37a`: verdict
  "Phase 5A accepted. No blockers."
- `reviewer2` Phase 6A scaffold audit, job `job_5b00939a7c0b`: accepted with
  residual notes as a scaffold only; remaining work includes real
  `communication_edges_absent` assertions, valid-non-success boundary tests,
  markdown history reporting, and seven case runners.
- Phase 4A accepted local gate:
  `python -m py_compile lib/cli/services/loop_ask_first.py
  lib/cli/services/loop_runner.py lib/cli/services/loop_topology.py
  lib/cli/services/plan_tasks.py lib/cli/parser_runtime/commands.py
  lib/cli/models_start.py lib/cli/render_runtime/ops_views_basic.py
  test/test_loop_capacity_cli.py test/test_loop_topology_cli.py
  test/test_plan_tasks_cli.py`
  -> passed.
- `python -m pytest
  test/test_loop_capacity_cli.py::test_loop_runner_direct_execution_route_runs_ask_first_round_without_dispatch
  test/test_loop_capacity_cli.py::test_loop_runner_direct_execution_missing_round_result_blocks_before_release
  test/test_loop_capacity_cli.py::test_loop_runner_direct_execution_rejects_unknown_round_result_without_release
  -q`
  -> `3 passed`.
- `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
  test/test_loop_topology_cli.py test/test_loop_topology_dispatch_contract.py
  test/test_question_cli.py -q`
  -> `76 passed`.
- `reviewer1` Phase 4A audit, job `job_477271c7d115`: verdict
  "Phase 4A acceptable, no blocker/high issue"; medium issues are carried into
  Phase 5/6 as failure cleanup, `ccb_round_reviewer` naming, and RolePack
  alignment.
- Source-wrapper Phase 4A direct-execution smoke from
  `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME`:
  `/home/bfly/yunwei/test_ccb2/phase4a-ask-first-smoke-20260704001222`.
  Result `workflow_smoke_status=ok`; final task status `done`,
  `round_result=pass`, `round_result_source=round_checker_reply`,
  `released_count=2`, `retained_count=0`, `topology_dispatch_absent=true`,
  and runtime checks confirmed the ask-first source proposal, normalized
  proposal, desired mount topology, and observed topology all omit `edges`,
  `artifacts`, and `gates`.
- Phase 3A local verification:
  `python -m py_compile lib/cli/services/loop_runner.py
  lib/cli/services/plan_tasks.py lib/cli/parser_runtime/commands.py
  lib/cli/models_start.py`
  -> passed.
- `python -m pytest test/test_loop_capacity_cli.py test/test_plan_tasks_cli.py
  -q`
  -> `42 passed`.
- `reviewer1` Phase 3A audit, job `job_c27531f0d6ac`: verdict
  "Phase 3A acceptable, no blocking high issue"; reviewer requested a
  source-wrapper smoke before closing the gate.
- Source-wrapper Phase 3A triage smoke from `/home/bfly/yunwei/test_ccb2`
  with isolated `HOME` and `CCB_SOURCE_HOME`:
  `/home/bfly/yunwei/test_ccb2/phase3a-triage-smoke-routes-YiiWhm`.
  Result `phase3a_triage_smoke=ok`; `needs_detail` activated
  orchestrator -> task_detailer -> orchestrator, `direct_execution` paused as
  Phase 4 not ready, `macro_adjustment_request` and `blocked` paused without
  execution agents, and no `topology_dispatch.json` was written.
- Phase 3A follow-up verification for bound-loop pause payload:
  `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
  test/test_question_cli.py -q`
  -> `49 passed`.
- `reviewer2` independent Phase 2 audit, job `job_f16656e84115`:
  verdict "No Phase 2 blockers remain"; residual notes are Phase 3
  orchestrator triage, legacy compatibility cleanup, and future freshness
  checks.
- `PYTHONPATH=lib python -m py_compile lib/cli/services/plan_tasks.py
  lib/cli/services/loop_runner.py lib/cli/models_start.py
  lib/cli/parser_runtime/commands.py`
  -> passed.
- `PYTHONPATH=lib python -m pytest test/test_plan_tasks_cli.py
  test/test_loop_capacity_cli.py test/test_question_cli.py -q`
  -> `45 passed`.
- `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
  test/test_loop_topology_dispatch_contract.py test/test_question_cli.py -q`
  -> `49 passed`.
- `python -m pytest test/test_loop_topology_dispatch_contract.py
  test/test_loop_topology_cli.py test/test_loop_capacity_cli.py -q`
  -> `50 passed`.
- Source-wrapper Decision 020 task-anchor smoke from
  `/home/bfly/yunwei/test_ccb2` with
  isolated `HOME=/home/bfly/yunwei/test_ccb2/source_home` and
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`:
  `/home/bfly/yunwei/test_ccb2/phase2-decision020-smoke-CAJxZmsD`.
  It created a task, imported `task_packet`, rejected
  `ready_for_orchestration` before `execution_contract`, imported
  `execution_contract` and `orchestration_notes --route direct_execution`,
  rejected `loop runner --once --consume-role-output`, bound the task,
  imported a blocked `round_summary`, and confirmed `loop runner --once`
  stopped without provider activation.
- Source-wrapper Phase 2 live smoke from `/home/bfly/yunwei/test_ccb2` with
  the same isolated env:
  `/home/bfly/yunwei/test_ccb2/phase2-anchor-live-HdfAeZ`.
  It verified the missing-`execution_contract` gate, `orchestration_notes
  --route direct_execution`, blocked `round_summary` import, terminal runner
  stop, and `--consume-role-output` rejection with CLI status `1`.
- `python -m py_compile lib/cli/services/loop_topology.py
  lib/cli/services/agent_lifecycle.py
  lib/agents/config_loader_runtime/dynamic_agent_overlays.py
  lib/agents/config_loader_runtime/loop_overlays.py
  test/test_loop_topology_cli.py`
  -> passed.
- `python -m pytest test/test_loop_topology_cli.py
  test/test_agent_lifecycle_cli.py test/test_agent_window_reflow.py
  test/test_loop_capacity_cli.py test/test_pane_growth_layout.py
  test/test_loop_topology_dispatch_contract.py -q`
  -> `87 passed`.
- `python -m pytest test/test_loop_topology_dispatch_contract.py
  test/test_loop_topology_cli.py test/test_loop_capacity_cli.py
  test/test_workflow_closure_smoke_script.py -q`
  -> `50 passed`, with no topology dispatch xfail remaining.
- `git diff --check`
  -> clean.
- Source-wrapper diagnose from `/home/bfly/yunwei/test_ccb2`:
  `HOME=/home/bfly/yunwei/test_ccb2/source_home
  CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home
  /home/bfly/yunwei/ccb_source/ccb_test --diagnose`
  -> wrapper/source checkout and allowed test root verified.
- Source-wrapper topology validator smoke:
  `/home/bfly/yunwei/test_ccb2/topology-validator-smoke-20260702230740`
  rejected unknown edge type `direct_tmux_mutation` and legacy profile
  `worker` with source `ccb_test`, returning `validator_smoke_status=ok`.
- Standalone single-window smoke from `/home/bfly/yunwei/test_ccb2`:
  `/home/bfly/yunwei/ccb_source/ccb_test layout dynamic-smoke --panes 6
  --window-prefix ccb-exec --json`
  -> `smoke_status=ok`, `layout_status=ok`, `dynamic_status=ok`,
  `cleanup_status=ok`, `event_count=11`.
- Live source-wrapper topology smoke:
  `/home/bfly/yunwei/test_ccb2/topology-window-smoke-final-20260702220620`
  with isolated `HOME`/`CCB_SOURCE_HOME` and fake provider roles.
  `config validate` and start passed; the earlier one-pair topology included
  an on-demand round reviewer and reconciled to
  `ccb-user=[bootstrap,wf-ccb-frontdesk,wf-ccb-task-detailer]`,
  `ccb-plan=[wf-ccb-planner,wf-ccb-orchestrator,wf-ccb-round-reviewer]`,
  and `ccb-exec=[wf-coder-1,wf-code-reviewer-1]`.
- Same live smoke then grew `ccb-exec` to two work pairs on the mounted
  runtime. Reconcile returned no drift and applied adds for `wf-coder-2` and
  `wf-code-reviewer-2`; ask smoke completed for both new agents with exact
  fake-provider replies.
- Same live smoke then committed compact topology with the second pair absent.
  Reconcile released `wf-coder-2` and `wf-code-reviewer-2`, retained count was
  `0`, drift was empty, final layout returned to one execution pair, and
  cleanup reached `kill_status: ok`.
- Source-wrapper auto-release smoke:
  `/home/bfly/yunwei/test_ccb2/topology-auto-release-smoke-20260703061442`
  committed a two-work-pair topology and then a one-work-pair desired
  topology. Reconcile returned `released_count=2`,
  `released_agents=[wf-code-reviewer-2,wf-coder-2]`, observed topology status
  was `ready`, both released agents had `lifecycle_state=unloaded`, and
  `.ccb/ccb.config` no longer contained the released agents.
- `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
  test/test_workflow_closure_smoke_script.py -q`
  -> `39 passed`.
- `python -m py_compile lib/cli/services/plan_tasks.py
  lib/cli/services/loop_runner.py lib/provider_execution/fake.py
  scripts/workflow_closure_smoke.py`
  -> passed.
- `pytest -q test/test_loop_capacity_cli.py::test_loop_runner_once_dispatches_committed_topology_edges_in_order
  test/test_loop_capacity_cli.py::test_loop_runner_topology_dispatch_rejects_invalid_runtime_graphs`
  -> `7 passed`, including hidden/parked target rejection.
- `pytest -q test/test_loop_capacity_cli.py test/test_loop_topology_cli.py
  test/test_workflow_closure_smoke_script.py`
  -> `52 passed`.
- `python -m pytest test/test_loop_capacity_cli.py test/test_loop_topology_cli.py
  test/test_workflow_closure_smoke_script.py test/test_loop_topology_dispatch_contract.py
  test/test_agent_lifecycle_cli.py test/test_agent_window_reflow.py
  test/test_pane_growth_layout.py -q`
  -> `98 passed`.
- `python -m pytest test/test_plan_tasks_cli.py test/test_loop_capacity_cli.py
  test/test_loop_topology_cli.py test/test_loop_topology_dispatch_contract.py
  test/test_workflow_closure_smoke_script.py -q`
  -> `68 passed`.
- `python -m compileall -q lib/cli/services/topology_dispatch.py
  lib/cli/services/loop_runner.py lib/provider_execution/fake.py`
  -> passed.
- Source-wrapper topology dispatch smoke from `/home/bfly/yunwei/test_ccb2`:
  `/home/bfly/yunwei/test_ccb2/topology-dispatch-smoke-20260702231020`.
  With isolated `HOME`, `CCB_SOURCE_HOME`, local fake role store, and
  `/home/bfly/yunwei/ccb_source/ccb_test`, `loop topology propose`, `commit
  --apply`, start, `plan task-bind-loop`, and `loop runner --once` completed.
  Runtime evidence showed `dispatch_status=ok` and ordered completed edges
  `coder-ask -> wf-coder-1`, `reviewer-ask -> wf-code-reviewer-1`, and
  `round-review -> wf-ccb-round-reviewer`; the round reviewer returned
  `round result: pass`, task status became `done`, and cleanup reached
  `kill_status: ok`.
- `python -m pytest test/test_loop_capacity_cli.py test/test_plan_tasks_cli.py test/test_loop_topology_cli.py test/test_workflow_closure_smoke_script.py -q`
  -> `50 passed`.
- Focused bridge/fake-provider verification:
  `test/test_loop_capacity_cli.py`,
  `test/test_v2_execution_service.py::test_execution_service_completes_fake_provider_jobs`,
  `test/test_v2_ccbd_dispatcher.py::test_dispatcher_persists_completion_items_and_state_updates_for_fake_provider`
  -> `24 passed`.
- Source-wrapper bridge smoke from `/home/bfly/yunwei/test_ccb2`:
  `/home/bfly/yunwei/test_ccb2/planner-bridge-smoke-20260702`
  advanced `draft -> imported_planner_output -> imported_plan_reviewer_output
  -> ready -> ran_one_round -> done`, released both dynamic agents, and
  cleaned up with `kill_status: ok`.
- Existing workflow closure smoke regression:
  `/home/bfly/yunwei/test_ccb2/agentic-loop-v1-smoke-20260702162851`
  returned `workflow_smoke_status=ok`, `task_detailer_imported=true`,
  `task_detailer_detail_ready=true`, `final_status=done`,
  `round_result=pass`, `release_status=released`, `retained_count=0`, and
  cleanup reached `kill_status: ok`.
- Phase 1 mount topology local verification:
  `python -m py_compile lib/cli/services/loop_topology.py
  lib/cli/services/topology_dispatch.py` -> passed;
  `python -m pytest test/test_loop_topology_cli.py
  test/test_loop_topology_dispatch_contract.py -q` -> `25 passed`;
  `python -m pytest test/test_loop_capacity_cli.py
  test/test_workflow_closure_smoke_script.py -q` -> `38 passed` in the
  reviewer2 acceptance audit;
  `python -m pytest test/test_agent_lifecycle_cli.py
  test/test_agent_window_reflow.py test/test_pane_growth_layout.py -q` ->
  `41 passed`;
  external source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/mount-topology-phase1-smoke-codex` proved
  `agent_mount_topology.desired.json` write/status and rejection of
  mount-topology `artifacts`.

## Handoff Notes

The hard boundary remains script authority. Agents may propose artifacts and
readiness through explicit bundles, but scripts decide whether to import them
and whether status transitions are valid. Do not add Markdown guessing or
direct index mutation as a shortcut for planner convenience.

Phase 1 mount-topology split is accepted by reviewer2 in
`job_901b6d77e156`. The final Phase 1-6 report can claim Phase 1 stage-level
acceptance, while carrying the residual legacy-compatibility and external
smoke-refresh notes into final reporting.

Phase 5A failure-cleanup work from `worker1` jobs `job_b9094cca425b` and
`job_81c641447a5a` is accepted by reviewer1 in `job_a0c108e8b37a`. The scoped
target was ask-first execution recovery only: non-ready topology stops before
asks, submit/watch failures and missing/unknown round results become explicit
non-success evidence rather than fake pass or stranded `running + current_loop`,
and dynamic resources release or retain through existing lifecycle semantics.
Chosen taxonomy: submit failure uses `ask_submission_failed`; watch failure
uses `watch_failed`. Source-wrapper failure-mode smokes remain unrun because
the current fake workflow smoke harness still needs failure hooks.

Phase 6A matrix scaffold work is dispatched to `worker3` as
`job_5bd9175962ef`. The scoped target is a fake-provider matrix harness and
structured evidence rows; missing matrix cases must report incomplete or
non-pass classifications rather than being skipped or counted as accepted.
Reviewer2 completed the scaffold acceptance checklist in
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5f0b3b729779-art_ec5c1149765b4204.txt`;
it is the review gate for matrix coverage, evidence fields, classification
semantics, source-wrapper isolation, mount-only topology, script authority, and
dynamic cleanup reporting. That checklist was forwarded to `worker3` as
supplemental context in `job_94e0a9ff7ecc`. Schema hardening for required row
fields (`task_id`, `cleanup_result`, `runtime_residue`, `ask_reachability`) was
completed in `job_69665da8646d`; reviewer2 accepted the scaffold as an
incomplete-reporting scaffold in `job_5b00939a7c0b` with residual notes in
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5b00939a7c0b-art_507140d2c6e14c58.txt`.
It is not a Phase 6A pass: later route-runner tranches narrowed the remaining
open case to `smoke-busy-release`, plus the integrated matrix and module-level
audits.
Scaffold hardening from reviewer2 residuals is assigned to `worker3` as
`job_27002816e400`: real `communication_edges_absent` evidence,
valid-non-success boundary tests, and markdown history report generation. The
work completed and was accepted by reviewer2 in `job_953728534f32`. Route
runners remain out of scope for that acceptance.

Phase 6 route-matrix runtime support for additional cases beyond
`direct_execution` was completed by `worker1` as `job_f801c31b11b3` for
`needs_detail`, `macro_adjustment_request`, and `blocked`. Worker evidence is
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f801c31b11b3-art_6f2be7afeb2649d0.txt`:
`needs_detail` routes through task detailer and returns to direct execution,
macro-adjustment maps to `replan_required`, blocked maps to `blocked`, and the
matrix remains intentionally incomplete. Worker1's supplemental checklist and
naming-constraint notes are in
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_e27fff956a45-art_44a3930f274b4b7e.txt`
and
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5d6dad0dc0c4-art_56ff412e718443cc.txt`.
Reviewer1 completed the acceptance checklist for this runtime tranche in
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c4a59d18bb49-art_48f7596bf35049a2.txt`;
it was forwarded to `worker1` as supplemental context in `job_e27fff956a45`.
Reviewer1 accepted the completed tranche in `job_240557da6f39` with no
blocker/high findings:
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_240557da6f39-art_cafd3ad2ac1541c2.txt`.
Medium follow-ups are explicit residue checks for some matrix rows, documenting
the fake loop bind used by macro/blocked smokes, and source-control hygiene for
the still-untracked matrix script/test. `partial_completion`, reviewer
reject/rework, reviewer cannot accept, and busy-release remain outside this
tranche. The checklist for those remaining cases is assigned to reviewer1 as
`job_10f4edb64910` and completed with artifact
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_10f4edb64910-art_42ad97f3a16d41eb.txt`.
It sets `partial_completion`, reviewer reject/rework, reviewer cannot accept,
and busy-release acceptance criteria; busy-release now waits on the matrix
runner that uses accepted Phase 5 lifecycle closure evidence. Worker1 completed
the three non-lifecycle cases as `job_ee4475e034ec`; reviewer1 accepted them in
`job_67657b4505b1`. `smoke-busy-release` remains the only case from that
checklist not accepted.

Module-level and final-report acceptance checklist preparation is assigned to
`reviewer2` as `job_9cb0746fad98`; the checklist artifact is
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_9cb0746fad98-art_25c9e57d83a840c1.txt`.
That checklist should gate any later Phase 6A/6B claim and the final
`history/phase1-6-acceptance-report-<YYYYMMDD>.md` report.

Phase 5 lifecycle closure is separate from the accepted Phase 5A
failure-cleanup slice and is now accepted with residual risk. Reviewer1
completed the acceptance checklist as `job_a715b88063ad`; worker2 completed
the package as `job_72c2e45f44d4`; reviewer1 accepted it in
`job_069b75debd58`. Residuals to carry forward are source-wrapper
failure-mode hooks remaining unit-test-only and real-provider busy detection
remaining unproven.

RolePack and target-name alignment inventory was dispatched to `worker2` as
`job_987a48380278` and completed with artifact
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_987a48380278-art_0c4ce25a7e5f43ed.txt`.
It found a must-migrate Phase 6A blocker: active ask-first still targets legacy
`round_checker`, source-wrapper smoke still installs legacy worker/checker
RolePacks, and formal accepted RolePacks for `ccb_task_detailer`,
`ccb_round_reviewer`, `coder`, and `code_reviewer` were missing. Formal
RolePack creation was completed by `worker3` as `job_3b2385ada87a`, adding draft
packages for `agentroles.ccb_task_detailer`, `agentroles.ccb_round_reviewer`,
`agentroles.coder`, and `agentroles.code_reviewer`. Worker evidence is
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_3b2385ada87a-art_352f0bf9af0c4807.txt`.
Reviewer2 accepted the package in `job_0cab915b5071` with no blocker/high
findings:
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_0cab915b5071-art_0affd7907e51440d.txt`.
Medium notes to carry forward are the legacy `agentroles.ccb_checker`
compatibility alias defaulting to `code_reviewer`, the need to keep RolePack
ids and `loop.capacity` profile names synchronized, and a stale
`role-catalog-and-boundaries.md` verification count. The naming constraint was
forwarded to `worker1` as `job_5d6dad0dc0c4` so the active route-matrix tranche
does not deepen the legacy target dependency. Ask-first target migration from
`round_checker` to `ccb_round_reviewer`, source-wrapper smoke config migration,
and aligned tests were completed by `worker3` as `job_2c083f64ba87`; worker
evidence is
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_2c083f64ba87-art_df8bad80a6e94013.txt`.
Reviewer2 accepted the migration in `job_be1921a3e3d8`; source-wrapper runtime
matrix validation still remains before Phase 6A can close.

Planner should work primarily through a compact plan brief: macro objective,
phase, active roadmap item, constraints, decision/open-question summaries,
detail links, current task entry, readiness, verification summary, and next
owner. Task-scoped detail docs and per-task executable packets should be
maintained by `ccb_task_detailer` only after orchestrator asks for refinement, then
summarized back into the brief or task document by script-owned import.
The planner-side compact import policy for `detail_summary`,
`macro_adjustment_request`, and `round_summary` is landed in worker1
`job_ae4b7235bf88`: compact evidence carries explicit macro-only planner
policy metadata, `macro_adjustment_request` remains request-only, and
`round_summary` must flow through script-owned `task-import-round`. Worker
evidence is
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ae4b7235bf88-art_6cb49ab41b6e4854.txt`;
reviewer2 checklist `job_ce8adccd030c` was forwarded as supplemental context in
`job_6fc415cce199`; reviewer2 accepted the package in `job_fbd5863fb80c`:
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_fbd5863fb80c-art_1928abb5b1284568.txt`.
Medium residual notes are that the guard is structural/auditable rather than a
semantic content classifier, no source-wrapper smoke was needed for this
non-runtime path, and `implementation-status.md` should be rechecked before
the final report.

## 2026-07-08 Deployment Readiness Acceptance Gate

A strict acceptance checklist for direct `talk2` validation is now prepared at
[topics/phase1-6-deployment-readiness-acceptance-gate-20260708.md](../topics/phase1-6-deployment-readiness-acceptance-gate-20260708.md).
The gate defines BLOCKER/HIGH/MEDIUM/LOW criteria, exact evidence fields and
paths for the L1-L4 route-mix lane, dynamic lifecycle/UI lane, and frontdesk
pressure lane, classification conditions, and explicit rejection criteria for
script-only passes, missing live project evidence, false dynamic unload, and
frontdesk direct implementation. Deployment readiness remains BLOCKED until
the remaining direct validation lanes produce raw opened-project evidence and
`talk2` applies the checklist.

## 2026-07-09 Immaculate Role Context Lifecycle

The immaculate (`无垢`) role design is now captured in
[decisions/021-immaculate-role-context-lifecycle.md](../decisions/021-immaculate-role-context-lifecycle.md)
and source-level guards have been added for the current loop paths. Before
resident `orchestrator` and `task_detailer` activations, the loop runner now
attempts provider-native clear and records `ccb_immaculate_activation_freshness`
evidence in the activation payload. The ask-first direct-execution path now
does the same before each new worker, reviewer, orchestrator, and
`ccb_round_reviewer` ask, with freshness evidence persisted in submission
intent, ask records, and round artifacts. Planner activation is explicitly not
cleared, preserving the long-lived planner/frontdesk context exception.

Verification: `python -m pytest test/test_loop_capacity_cli.py -q` passed
(`146 passed`), and the adjacent plan/topology/ask bundle passed
(`87 passed`). This is source-level regression coverage only; final production
readiness still requires the user-visible real opened-project validation lanes
under `/home/bfly/yunwei/test_ccb2`.

## 2026-07-09 Visible Window-First Workflow Layout

The V1 workflow layout direction is now explicit in
[topics/runtime-workflow-graph-and-reconciler.md](../topics/runtime-workflow-graph-and-reconciler.md)
and
[topics/dynamic-window-pane-agent-maintenance.md](../topics/dynamic-window-pane-agent-maintenance.md):
do not reduce pane count by hiding normal workflow roles by default. Instead,
active roles are visible and partitioned by deterministic windows:
`ccb_frontdesk` plus active `ccb_task_detailer` in `ccb-user`;
`ccb_planner`, `ccb_orchestrator`, and active `ccb_round_reviewer` in
`ccb-plan`; `coder` and `code_reviewer` in `ccb-exec`, `ccb-exec-2`, and later
execution pages with six panes per window. Context freshness for immaculate
roles remains separate from visibility.

Regression coverage in `test/test_loop_topology_cli.py` now proves the default
mount-topology placement for the five workflow control roles plus four
coder/reviewer work units, verifies all auto-assigned add commands are
`visibility="visible"`, checks the seventh execution pane creates
`ccb-exec-2`, and checks release compaction moves surviving execution agents
back into `ccb-exec` while removing the empty overflow page.

## 2026-07-10 Visible Workflow Resilience And Provider Gate

`talk2` directly completed and audited the visible five-task workflow,
same-turn daemon restart, dynamic Claude lifecycle, and AGY first-project trust
probes. The evidence report is
[history/visible-five-task-workflow-resilience-e2e-20260710.md](visible-five-task-workflow-resilience-e2e-20260710.md).

The full repository gate excluding Gemini nodes passed with `3854 passed, 2
skipped, 124 deselected`. OpenCode/Grok/AGY focused backend coverage passed
with `117 passed`. AGY then completed a real source-wrapper ask using Claude
Sonnet 4.6, including one bounded auto-mode trust confirmation and durable
`turn_boundary` evidence; safe mode did not confirm or deliver. OpenCode
remains blocked by an OpenAI OAuth refresh 401, and Grok remains blocked by a
missing active login. Gemini is no longer part of the current workflow
production gate; it must not be used to hide failures in shared provider code.
