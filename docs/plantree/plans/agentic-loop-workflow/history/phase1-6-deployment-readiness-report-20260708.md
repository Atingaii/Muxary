# Phase 1-6 Deployment Readiness Report

Date: 2026-07-08
Owner: talk2
Status: REPORT_COMPLETE / P5_SOURCE_GATE_PASSED / RELEASE_NOT_PUBLISHED / PRODUCTION_DEFAULT_NOT_ENABLED

## Verdict

The current source tree has enough direct real-project evidence and source
packaging evidence to move from validation into package-owner staging and
release decisions.

It is not approved for production/default enablement yet. The remaining gate
is not another hidden worker/reviewer validation round; it is package-owner
source-control staging, real release-artifact publication/update smoke, and
explicit deployment policy.

This report preserves the bounded P3 result:
`PASS_WITH_LIMITS`.

## Scope

This report covers the post-acceptance deployment-readiness lane for the
[Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md). It is
the P4 report in the queue tracked by
[phase1-6-deployment-readiness-supervision-20260707.md](../topics/phase1-6-deployment-readiness-supervision-20260707.md).

Required operator-facing standard:

- real opened project under `/home/bfly/yunwei/test_ccb2`;
- explicit source wrapper `/home/bfly/yunwei/ccb_source/ccb_test`;
- inherited system provider environment for real-provider tests;
- root-local `AGENT_ROLES_STORE`;
- visible project/UI/pane evidence where claimed;
- frontdesk-started handoff through planner/orchestrator;
- raw task, route, round, topology, release, cleanup, and B7 evidence.

## Primary Evidence

| Lane | Result | Evidence |
| :--- | :--- | :--- |
| P0 baseline freeze | Frozen | [phase1-6-deployment-readiness-p0-baseline-20260708.md](phase1-6-deployment-readiness-p0-baseline-20260708.md) |
| L1-L4 sequence38 route mix | `Status: pass` | `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/phase6b-real-provider-l1-l4-sequence38-talk2-selfrun-20260708124814-b7.md` |
| L1-L4 post-fix fullflow retest | `Status: pass` | `/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901/phase6b-real-provider-l1-l4-deploy-fullflow-talk2-selfrun-20260708202901-b7.md` |
| P1 dynamic lifecycle | `status: pass` | [phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md](phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md) |
| P2 frontdesk pressure | `Status: pass` | [phase1-6-deployment-readiness-p2-frontdesk-pressure-20260708.md](phase1-6-deployment-readiness-p2-frontdesk-pressure-20260708.md) |
| P3 module audit | `PASS_WITH_LIMITS` | [phase1-6-deployment-readiness-p3-module-audit-20260708.md](phase1-6-deployment-readiness-p3-module-audit-20260708.md) |
| P5 source packaging gate | `PASS_FOR_SOURCE_PACKAGING_GATE` | [phase1-6-deployment-readiness-p5-packaging-gate-20260708.md](phase1-6-deployment-readiness-p5-packaging-gate-20260708.md) |
| P5 post-gate automatic frontdesk stress | `Status: pass` | `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/phase6b-real-provider-l1-l4-deploy-stress-talk2-selfrun-20260708205921-b7.md` |
| P5 repeatability automatic frontdesk fullflow | `Status: pass` | `/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126/phase6b-real-provider-l1-l4-deploy-repeatability-talk2-202607082126-b7.md` |
| Real npm latest install smoke | `ok` for published `8.0.19` | `/home/bfly/yunwei/test_ccb2/p5-real-npm-install-talk2-20260708212535/real-npm-install-result.json` |
| Current-source preview release install smoke | `ok` for local preview `8.0.14` | `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/current-source-release-install-result.json` |
| Installed-preview workflow closure smoke | `workflow_smoke_status: ok` | `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/installed-preview-workflow-smoke-result.json` |
| Historical L5 partial supplement | `valid_non_success` | [phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](phase6b-real-provider-l5-partial-repeat4-b7-20260704.md) |
| Historical Phase 6A matrix supplement | `phase6a_pass=true` | `/home/bfly/yunwei/test_ccb2/phase6-final-matrix-20260704-final-report/phase6_fake_matrix_rows.jsonl` |

## Latest Fullflow Retest

After the P4 report was first written, `talk2` found a real-provider L3
`needs_detail` stop-contract bug in a fresh opened project. The `task_detailer`
reply contained complete detail artifacts and an explicit
`controller_expected_stop: detail_ready`, but it also used the older
`detail readiness recommendation: needs_clarification` wording. The importer
blocked the row instead of honoring the controller-visible detail-ready stop
contract.

Source repair:

- [role_output_import.py](/home/bfly/yunwei/ccb_source/lib/cli/services/role_output_import.py)
  now accepts complete task-detailer artifacts as `detail_ready` when the
  activation has `detail_ready_stop_contract.status=detail_ready` and the
  reply declares `controller_expected_stop: detail_ready`.
- [loop_runner.py](/home/bfly/yunwei/ccb_source/lib/cli/services/loop_runner.py)
  now recognizes `Expected stop: detail_ready` in the task contract when
  building the task-detailer activation.
- [test_loop_capacity_cli.py](/home/bfly/yunwei/ccb_source/test/test_loop_capacity_cli.py)
  includes the failing-before regression
  `test_loop_runner_imports_task_detailer_controller_expected_stop_detail_ready`.

Post-fix real-provider retest:

- Root:
  `/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901`
- Project:
  `/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901/deploy-fullflow-talk2-selfrun-20260708202901-project`
- B7:
  `/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901/phase6b-real-provider-l1-l4-deploy-fullflow-talk2-selfrun-20260708202901-b7.md`
- Status: `pass`
- Rows: 5
- Classification: 2 `pass`, 3 `valid_non_success`
- Routes: 2 `direct_execution`, 1 `needs_detail`, 1
  `macro_adjustment_request`, 1 `blocked`
- L3: `needs_detail -> detail_ready`, with `detail_design`,
  `detail_summary`, and `detail_packet` imported from real task-detailer job
  `job_7b0e141d22cb`.
- Dynamic release for L1/L2: `released_count=2`, `retained_count=0`,
  `dynamic_unload_ok=true`, and `runtime_residue=false`.
- Cleanup: post-B7 cleanup stopped the project-local ccbd/tmux/provider
  processes; follow-up `ps` showed no target-project runtime residue.

Regression verification after the source repair:

```text
python -m pytest test/test_loop_capacity_cli.py -q -k \
  'task_detailer or macro_and_blocked_routes or auto_continues_after_macro'
13 passed, 121 deselected

python -m py_compile lib/cli/services/role_output_import.py \
  lib/cli/services/loop_runner.py test/test_loop_capacity_cli.py
python -m pytest test/test_loop_capacity_cli.py test/test_plan_tasks_cli.py -q
150 passed

git diff --check -- lib/cli/services/role_output_import.py \
  lib/cli/services/loop_runner.py test/test_loop_capacity_cli.py
clean
```

This retest strengthens the P4 operator-facing evidence. It does not broaden
the production/default enablement claim and does not replace P5 packaging or
release-owner decisions.

## P5 Post-Gate Automatic Frontdesk Stress Retest

After P5 source packaging smoke, `talk2` ran another fresh real-provider
opened-project route-mix lane to verify the current automatic product path
rather than only the older manual checkpoint path.

- First attempted root:
  `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205853`
  was abandoned because `init` was mistakenly invoked from the source checkout,
  and `ccb_test` correctly refused source-checkout runtime execution.
- Fresh accepted root:
  `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921`
- Project:
  `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/deploy-stress-talk2-selfrun-20260708205921-project`
- B7:
  `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/phase6b-real-provider-l1-l4-deploy-stress-talk2-selfrun-20260708205921-b7.md`
- Rows:
  `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/rows/phase6b_l1_l4_deploy-stress-talk2-selfrun-20260708205921_evidence_rows.jsonl`

Result:

- Status: `pass`
- Rows: 5
- Claimable rows: all true
- Classification: 2 `pass`, 3 `valid_non_success`
- L1/L2: `direct_execution -> done/pass`, `released_count=2`,
  `retained_count=0`, `runtime_residue=false`,
  `dynamic_unload_ok=true`, and no active dynamic agents.
- L3: `needs_detail -> detail_ready`
- L4 macro: `macro_adjustment_request -> replan_required`
- L4 blocked: `blocked -> blocked`
- Frontdesk automatically produced intake evidence and a single planner
  handoff marker; planner returned the five-task set; the auto-runner completed
  the route mix without manual task advancement.
- Post-B7 cleanup exited 0 and a follow-up process scan found no process
  residue for the target project.

Operational discovery:

- A manual `start-task` command launched while the frontdesk auto-runner was
  still active can block waiting for the auto-runner lock. This is now covered
  by a harness regression and repaired so already completed/running tasks are
  observed before waiting for auto-runner quiet. The manual checkpoint path
  still waits before creating or activating new task authority, preserving the
  no-duplicate-authority guard.

P5 repeatability run:

- Root:
  `/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126`
- B7:
  `/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126/phase6b-real-provider-l1-l4-deploy-repeatability-talk2-202607082126-b7.md`
- Summary:
  `/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126/repeatability-summary.json`
- Status: `pass`
- Rows: 5
- Claimable rows: 5
- Classification: 2 `pass`, 3 `valid_non_success`
- L1/L2 dynamic release: `released_count=2`, `retained_count=0`,
  `dynamic_unload_ok=true`, `runtime_residue=false`
- Post-cleanup process scan: no target-project process residue

Real npm latest install smoke:

- Root:
  `/home/bfly/yunwei/test_ccb2/p5-real-npm-install-talk2-20260708212535`
- Installed package: `@seemseam/ccb@8.0.19`
- `ccb --print-version`: `v8.0.19`
- Bin links: `ccb`, `ask`, `autonew`, `ctx-transfer`
- Release payload present: `.ccb-release/ccb-linux-x86_64`

This proves the public npm/latest install path works. It also exposes a release
boundary: the current checkout `package.json` is `8.0.14`, so the current
dirty source tree has not been proven as the published `8.0.19` artifact.

Current-source preview release/install smoke:

- Root:
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205`
- Artifact:
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/dist/ccb-linux-x86_64.tar.gz`
- Result:
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/current-source-release-install-result.json`
- Version: `8.0.14`
- `ccb --print-version`: `v8.0.14`
- Artifact size: `32M`
- Artifact sha256:
  `4454560c3e846cbc475fa05ab289e47e0cd7417a19f5cb18f0151ebcdee4af23`
- Install metadata: `install_mode=release`, `source_kind=preview`,
  `channel=preview`
- Bin links: `ccb`, `ask`, `autonew`, `ctx-transfer`
- Release helpers: `ccb-agent-sidebar`, `ccb-rs-helper`,
  `ccb-runtime-accelerator`

This smoke proves the current dirty source tree can build a local
release-shaped Linux preview artifact and install through `install.sh` into an
isolated prefix. It also exposed and fixed a release-copy bug: generated
`mobile/app/build`, `.dart_tool`, Gradle, IDE, `node_modules`, and
`dist-mobile` paths were entering the preview release tree, making the stage
about `11G` before the fix. The fixed artifact has no forbidden mobile build
entries.

Installed-preview workflow closure smoke:

- Project root:
  `/home/bfly/yunwei/test_ccb2/p5-installed-preview-smoke-talk2-202607082220`
- Result:
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/installed-preview-workflow-smoke-result.json`
- Command source:
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/install-prefix/scripts/workflow_closure_smoke.py`
- `ccb_test`:
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/install-prefix/ccb_test`
- Status: `workflow_smoke_status=ok`
- Final task status: `done`
- Round result: `pass`
- Round result source: `round_reviewer_reply`
- Dynamic release: `released_count=2`, `retained_count=0`
- Cleanup: `kill_returncode=0`, no target-project process residue in follow-up
  process scan

This closes the installed-preview runtime gap: the current-source preview
artifact is not only installable, it can run the deterministic workflow closure
path from the external test folder using its own installed scripts and wrapper.

## Current Phase 1-6 Status

| Scope | Current status | Deployment-readiness implication |
| :--- | :--- | :--- |
| Phase 1 mount topology | Accepted | Current P1/P2 topology evidence still has no communication DSL keys and releases to zero mounted dynamic agents. |
| Phase 2 task/document anchors | Accepted | Current P1/P2 task indexes show artifact path, sha256, imported_at, actor, and provider job lineage where applicable. |
| Phase 3 orchestration triage | Accepted | Current route evidence covers direct, detail, macro-adjustment, and blocked. |
| Phase 4 ask-first execution | Accepted | Current direct-execution rounds reach worker/reviewer/round-reviewer pass and script-owned round import. |
| Phase 5 lifecycle | Accepted with limits | Current P1 proves repeated release, busy-retain, after-idle release, resident survival, UI/sidebar, and timeout diagnostics. Full historical park/resume/reflow breadth is not fully rerun in P1. |
| Phase 6A fake-provider matrix | Accepted for program-matrix scope | Used only as bounded supplement for reviewer-rework and partial branches not rerun in P1/P2. |
| Phase 6B real-provider single-round | Accepted for initial bounded scope | P0-P5 and the post-gate stress retest strengthen the operator-facing path, but production/default enablement still requires package-owner release and deployment policy. |

## L1-L4 Sequence38 Result

Sequence38 was the first current direct `talk2` self-run route-mix pass for
the source tree after the worker/reviewer validation ownership change.

- Root:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814`
- B7:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/phase6b-real-provider-l1-l4-sequence38-talk2-selfrun-20260708124814-b7.md`
- Status: `pass`
- Rows: 5
- Classification: 2 `pass`, 3 `valid_non_success`
- Routes: 2 `direct_execution`, 1 `needs_detail`, 1
  `macro_adjustment_request`, 1 `blocked`
- Claimable rows: all true
- Dynamic release for direct rows: `released_count=2`, `retained_count=0`,
  `runtime_residue=false`
- Provider-reply authority parsing: absent
- Cleanup: post-B7 cleanup returned unmounted project state.

## P1 Validation Result

P1 passed on fresh visible root:

```text
/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320
```

P1 proves:

- three real direct-execution rounds reached `done/pass`;
- L3 post-detail execution can continue past `detail_ready` and complete;
- each direct-execution loop released dynamic coder/reviewer nodes with
  `released_count=2`, `retained_count=0`, and observed topology `agents=[]`;
- macro and blocked routes ended as valid non-success;
- positive real-provider `retained_busy` was observed and later released after
  idle proof;
- resident frontdesk, planner, orchestrator, task_detailer, and
  `ccb_round_reviewer` remained visible;
- UI/sidebar/tmux evidence was captured under the fresh root;
- explicit timeout diagnostic failed as expected, then a normal watch reached
  terminal and released cleanly;
- post-B7 cleanup returned `ccbd_state: unmounted`.

## P2 Validation Result

P2 passed on fresh visible root:

```text
/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920
```

P2 proves:

- one natural-language frontdesk macro-intake produced five route-mix tasks;
- frontdesk was Codex-backed and did not implement, edit project artifacts,
  run tests, create B7 rows, or clean runtime;
- dispatcher created exactly one frontdesk handoff marker;
- `frontdesk forward-planner` submitted exactly one silence ask to planner;
- the second frontdesk job was reply delivery from planner completion, not a
  duplicate planner handoff;
- planner returned a fenced `task-set.json`;
- L1/L2 direct rows reached `done/pass` with clean dynamic release;
- L3/L4 valid non-success outcomes were classified as `valid_non_success`,
  not `pass` and not `system_failure`;
- cleanup returned `ccbd_state: unmounted`.

This is a macro-intake pressure pass, not proof of five independent user
messages into frontdesk.

## Module-Level Verdicts

P3 recorded `PASS_WITH_LIMITS`.

| Module | Verdict | Summary |
| :--- | :--- | :--- |
| Plan/Task Document | `pass_with_limits` | Current task artifacts are linked with path, sha256, imported_at, actor, and provider job lineage where applicable. Script-owned macro/blocker artifacts are intentionally script-owned. |
| Orchestration | `pass_with_limits` | Current direct/detail/macro/blocked routes match expected outcomes. Partial/rework are accepted historical supplements, not current P1/P2 reruns. |
| Mount Topology | `pass` | Desired/observed topology reconciles, release truth is visible, and communication DSL keys are absent. |
| Ask Collaboration | `pass_with_limits` | Current asks traverse frontdesk/planner/orchestrator/detailer/worker/reviewer/round-reviewer, and provider replies do not mutate authority. Full live failure-injection breadth was not rerun. |
| Dynamic Lifecycle | `pass_with_limits` | Current P1 proves release, busy-retain, resident survival, UI/sidebar, timeout, and cleanup agreement. Full historical park/resume/reflow breadth was not rerun. |
| Evidence And Reporting | `pass` | Rows have classifications, valid non-success is not normalized into pass, and B7 claims match raw task/topology/cleanup evidence. |

## Failure Taxonomy

| Evidence set | Pass | Valid non-success | Expected diagnostic failure | Hard failure in claimed scope |
| :--- | ---: | ---: | ---: | ---: |
| Sequence38 L1-L4 | 2 | 3 | 0 | 0 |
| P1 dynamic lifecycle | 3 | 2 | 1 explicit timeout diagnostic | 0 |
| P2 frontdesk pressure | 2 | 3 | 0 | 0 |
| Historical L5 partial | 0 | 1 | 0 | 0 |
| Historical Phase 6A matrix | 3 | 5 | 0 | 0 |

Valid non-success rows are bounded outcomes: `detail_ready`,
`replan_required`, `blocked`, `partial`, and retained-busy lifecycle
diagnostics. They are not treated as success and not treated as system failure.

## First Stable Complexity Breakpoint

The first stable complexity breakpoint remains L5 partial completion:

- Evidence:
  [phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](phase6b-real-provider-l5-partial-repeat4-b7-20260704.md)
- Task: `phase6b-l5-partial-budget-source-gap`
- Route: `direct_execution`
- Final status: `partial`
- Round result: `partial`
- Classification: `valid_non_success`
- Reason: a required source file was absent, so the worker preserved completed
  and unfinished steps instead of inventing source-derived content.

This proves bounded partial progress classification. It does not prove
reviewer-rework convergence.

## Unresolved Blockers For Production/Default Enablement

P5 source packaging gate no longer blocks source staging. This report still
blocks any immediate production/default enablement claim.

Open blockers before deployment/default enablement:

- The source worktree is dirty and includes untracked plan-tree/source-lane
  files; a package owner must stage, defer, or explicitly exclude each item.
- P5 verified npm wrapper packaging, skip-download installs, a local
  current-source preview release install, and a public npm latest install. It
  did not publish npm, create a GitHub release, or install into the
  global/system CCB environment. The published `8.0.19` release-artifact path
  works, but it is not the current dirty source tree.
- Current source version drift remains: `package.json` is `8.0.14`, npm latest
  is `8.0.19`.
- The main checkout has not been switched back to `main`; workflow work should
  remain isolated through an explicit worktree/branch decision before release.
- Reviewer-rework convergence/stability is still unproven. Historical
  Phase 6A rework evidence is fake-provider/program-matrix supplement only.
- Full live ask submit/watch failure injection was not rerun in P1/P2.
- Full historical park/resume/reflow breadth was not rerun in P1.
- Five independent frontdesk user-message pressure runs were not executed;
  P2 covered one macro-intake that generated five route-mix tasks.
- The new `version = 3` dynamic workflow config direction is design input,
  not implemented deployment behavior.

## Explicit Non-Goals

This report does not claim:

- production/default enablement;
- automatic enablement for all user projects;
- arbitrary long-running multi-round workflow completion;
- arbitrary workflow authoring outside the evidenced task packs;
- reviewer-rework convergence;
- all possible provider failure recovery branches under real providers;
- source-control packaging, release, or installer readiness;
- `version = 3` dynamic workflow config support.

## Next Release Priorities

Package-owner staging and release are the next gates.

Required release-owner work:

1. Freeze source-control inventory for the workflow branch and decide what is
   staged, deferred, or excluded.
2. Keep runtime test roots under `/home/bfly/yunwei/test_ccb2` out of source
   packaging.
3. Keep the main GitHub checkout separable from workflow work; use worktree
   isolation when returning the main checkout to the main branch.
4. Run `python -m py_compile` on touched source/tests/scripts.
5. Run focused pytest for changed surfaces plus relevant integration bundles.
6. Run `git diff --check`.
7. Run install/update smoke against the actual deployment path and official
   release artifact for the chosen package-owner version, not only local
   preview artifacts.
8. Produce a package-owner release/deployment decision before any
   production/default claim.

## Final Deployment-Readiness Decision

P4 and the P5 source packaging gate are complete for the current source tree.

The project is ready for package-owner staging/release decisions. It is not
published, not globally installed, and not production/default ready.
