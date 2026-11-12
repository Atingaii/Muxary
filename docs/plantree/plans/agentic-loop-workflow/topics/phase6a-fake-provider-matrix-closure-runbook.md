# Phase 6A Fake-Provider Matrix Closure Runbook

Date: 2026-07-04
Status: COMPLETED MATRIX RUN / REVIEWER ACCEPTED PROGRAM-MATRIX EVIDENCE

This runbook records the Phase 6A fake-provider matrix closure sequence after
the busy-release runner gate landed. It is documentation and rerun guidance
only. The integrated matrix evidence is accepted for the Phase 6A
program-matrix scope; it does not claim Phase 6B, real-provider capability,
production/default enablement, long-running multi-round workflows, or arbitrary
workflow authoring.

Primary references:

- [Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md)
- [Phase 6 build-stage verification](../goals/phase6-build-stage-verification.zh.md)
- [Phase 6 single-round task matrix goal](../goals/phase6-single-round-task-matrix-goal.md)
- [Current implementation status](../implementation-status.md)
- [Draft final acceptance report](../history/phase1-6-acceptance-report-draft.md)
- Module/final checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_9cb0746fad98-art_25c9e57d83a840c1.txt`
- Remaining matrix checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_10f4edb64910-art_42ad97f3a16d41eb.txt`
- Accepted non-lifecycle matrix tranche:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_67657b4505b1-art_bfe488836bb447f8.txt`
- Remaining lifecycle checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_a715b88063ad-art_1bd7d58cd0d14087.txt`

## Readiness Boundary

This runbook is now a Phase 6A program-matrix evidence record, not a Phase 6B
or production readiness claim.

The closure run became valid after:

- `smoke-busy-release` runner implementation is accepted. Phase 5 lifecycle
  closure is accepted with residual risk in reviewer1 `job_069b75debd58`;
  reviewer1 `job_d9820cc82c80` returned needs changes because
  `busy_worker_ask` used invalid sender `phase6`; worker2 follow-up
  `job_c690c97e0b8b` closed the argv-level regression proof and reviewer1
  accepted the single-case runner in `job_7fb1ad254939`;
- `smoke-busy-release` has an implemented runner in
  `scripts/phase6_fake_matrix_smoke.py`;
- `case_manifest()` reports all eight required cases as implemented;
- the matrix runner can produce JSON, JSONL, and Markdown reports for all
  eight cases.

Reviewer1 accepted the residue-clean integrated matrix package in
`job_712002b8f005`. Reviewer2 accepted the module/final-report evidence package
and Phase 6A claim boundary in `job_a34e79ecfc00`.

## Post-Lifecycle Acceptance Sequence

Worker2 lifecycle closure returned as `job_72c2e45f44d4` and reviewer1
accepted it with residual risk in `job_069b75debd58`. The
`smoke-busy-release` single-case runner is now accepted in reviewer1
`job_7fb1ad254939`. Use this sequence:

1. Read the worker2 completion artifact fully and confirm it covers the
   reviewer1 lifecycle checklist, especially busy retain, later idle release,
   resident reachability, reflow identity, failure hooks, and residue audits.
2. Run the integrated eight-case source-wrapper matrix only from
   `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME`.
3. Confirm every row has explicit booleans for
   `runtime_residue.dynamic_agents_absent`,
   `runtime_residue.config_dynamic_agents_absent`, and
   `runtime_residue.observed_topology_residue_absent`.
4. Use the generated matrix evidence to complete the module-level audit
   worksheet, then update the draft final report. Keep Phase 6B blocked until
   a separate real-provider launch gate passes.

Completed lifecycle reviewer request shape:

```text
Please audit worker2's Phase 5 lifecycle closure package against
job_a715b88063ad. Scope is beyond accepted Phase 5A failure cleanup.

Confirm blocker criteria:
- idle dynamic execution agents release after evidence import;
- busy active ask/provider state returns retained_busy without forced kill;
- resident roles remain in config and ps after loop cleanup;
- grow/shrink reflow preserves surviving pane identity;
- released dynamic agents are absent from config, ps, desired topology, and
  observed topology.

Also check overflow window removal, surviving-agent ask reachability,
source-wrapper failure hooks, park/resume, release taxonomy fields, and whether
the package supplies accepted evidence for smoke-busy-release.

Do not treat this as Phase 6A acceptance; it only decides whether the lifecycle
gate is closed enough to run the integrated fake-provider matrix.
```

Reviewer1 accepted this gate with residual risk in `job_069b75debd58`.

Current known scaffold state from source inspection:

- `--run` selects direct execution, route tranche, execution tranche, and
  `smoke-busy-release`.
- All eight cases have runners; `partial_completion`, reviewer
  reject/rework, and reviewer cannot-accept were accepted by reviewer1 in
  `job_67657b4505b1`.
- `smoke-busy-release` now has a visible runner and `--run-busy-release` CLI
  flag in `scripts/phase6_fake_matrix_smoke.py`; focused tests pass with
  `15 passed`.
- Worker2 validation evidence: source-wrapper `--run-busy-release` from
  `/home/bfly/yunwei/test_ccb2` with isolated `HOME`/`CCB_SOURCE_HOME` wrote a
  single-case report; reviewer1 accepted the busy row in `job_7fb1ad254939` as
  `direct_execution / busy / running / retained_busy / valid_non_success`, with
  authority and runtime-residue checks true.
- Talk2 integrated matrix run:
  `/home/bfly/yunwei/test_ccb2/phase6-final-matrix-20260704-final-report/phase6_fake_matrix_report.json`
  returned `phase6_fake_matrix_status=pass`, `phase6a_pass=true`,
  `observed_case_count=8`, no hard failures, and all runtime-residue booleans
  true on every row. JSONL rows are beside it, and Markdown was generated at
  `docs/plantree/plans/agentic-loop-workflow/history/phase6-real-capability-assessment-20260704.md`.
  Worker3 `job_9fff172b9685` cleaned the generated Markdown wording. Reviewer1
  accepted this evidence package in `job_712002b8f005`; reviewer2 accepted the
  module/final-report claim boundary in `job_a34e79ecfc00`.

Pending `smoke-busy-release` runner review request shape:

```text
Please audit worker2's `smoke-busy-release` matrix runner package against
reviewer1's remaining matrix checklist `job_10f4edb64910` and lifecycle
acceptance `job_069b75debd58`.

Scope:
- only the `smoke-busy-release` runner and directly necessary harness tests;
- no Phase 6A full-matrix acceptance claim;
- no Phase 6B or real-provider claim.

Required case semantics:
- case_id/task_id: smoke-busy-release;
- expected_route and observed_route: direct_execution;
- route_decision_correct computed from observed route versus expected route;
- round_result: busy;
- final_status: running;
- cleanup_result: retained_busy;
- classification: valid_non_success;
- dynamic busy execution agent retained with retained_busy reason;
- task remains bound to current_loop until later idle reconcile;
- later idle reconcile releases the retained agent cleanly or records accepted
  lifecycle evidence proving the path.

Authority checks:
- round/status evidence is script-owned;
- provider reply text does not mutate task authority;
- ask-first mainline does not write or read topology dispatch runtime state;
- mount topology evidence does not synthesize communication DSL fields
  edges/gates/artifacts.

Verification expected:
- focused pytest for the busy-release row and manifest implementation status;
- focused regression coverage proving the `busy_worker_ask` command does not
  include `from phase6` or any other unknown sender token;
- relevant lifecycle/topology tests if those surfaces changed;
- py_compile for touched scripts/services;
- git diff --check for touched files;
- source-wrapper smoke only from /home/bfly/yunwei/test_ccb2 with isolated
  HOME and CCB_SOURCE_HOME if runtime evidence is claimed.
```

## Hard Stop Conditions

Stop before or during the closure run if any condition is true:

- run would start from `/home/bfly/yunwei/ccb_source` as a live runtime root;
- `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` fails from the external
  test root;
- `HOME` or `CCB_SOURCE_HOME` is not isolated to the source-wrapper test home;
- any required case is still `not_implemented` or `missing_evidence`;
- `phase6_fake_matrix_status` is not `pass`;
- `phase6a_pass` is not `true`;
- any case has `classification` of `system_failure`, `role_failure`, or
  `provider_failure`;
- topology mainline contains `edges`, `gates`, `artifacts`, or
  `topology_dispatch.json`;
- provider replies mutate authority state directly;
- blocked, partial, replan, or busy cases are marked `done`;
- released dynamic agents remain in `ps`, `.ccb/ccb.config`, or observed
  topology without a `retained_busy` explanation.

## External Test Root And Environment

Use a dedicated external test root:

```bash
cd /home/bfly/yunwei/test_ccb2
export HOME=/home/bfly/yunwei/test_ccb2/source_home
export CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home
export CCB_PHASE6_MATRIX_TEST_ROOT=/home/bfly/yunwei/test_ccb2
```

Run diagnose before any matrix command:

```bash
/home/bfly/yunwei/ccb_source/ccb_test --diagnose
```

Required environment evidence:

- current working directory is not `/home/bfly/yunwei/ccb_source`;
- `HOME` and `CCB_SOURCE_HOME` match the isolated source home;
- `ccb_test --diagnose` reports the external source test root is allowed;
- no real provider credentials are required or used;
- accepted RolePacks are installed through the source-wrapper project setup,
  not from the live source checkout runtime state.

## Local Source Checks

Run these from `/home/bfly/yunwei/ccb_source` before the source-wrapper matrix.
They are source checks, not source runtime commands.

```bash
python -m py_compile \
  lib/cli/services/loop_ask_first.py \
  lib/cli/services/loop_runner.py \
  lib/cli/services/loop_topology.py \
  lib/cli/services/plan_tasks.py \
  scripts/phase6_fake_matrix_smoke.py \
  scripts/workflow_closure_smoke.py

python -m pytest \
  test/test_phase6_fake_matrix_smoke_script.py \
  test/test_workflow_closure_smoke_script.py \
  test/test_loop_capacity_cli.py \
  test/test_plan_tasks_cli.py \
  test/test_loop_topology_cli.py \
  test/test_loop_topology_dispatch_contract.py \
  test/test_question_cli.py \
  -q
```

If the busy-release runner follow-up changes lifecycle/reflow code, add the
lifecycle bundle before the source-wrapper matrix:

```bash
python -m pytest \
  test/test_agent_lifecycle_cli.py \
  test/test_agent_window_reflow.py \
  test/test_pane_growth_layout.py \
  -q
```

Repeat the same focused source checks after the source-wrapper matrix if the
runbook execution required any source edits or acceptance follow-up fixes.

## Matrix Commands

### Full Matrix Candidate Command

This command is known from the current scaffold shape. Do not claim Phase 6A
acceptance unless the generated report observes all eight rows and passes.

```bash
cd /home/bfly/yunwei/test_ccb2
export HOME=/home/bfly/yunwei/test_ccb2/source_home
export CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home

/home/bfly/yunwei/ccb_source/ccb_test --diagnose

stamp=$(date -u +%Y%m%dT%H%M%SZ)
project_name="phase6-fake-matrix-${stamp}"
report_dir="/home/bfly/yunwei/test_ccb2/${project_name}/reports"
history_report="/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6-real-capability-assessment-${stamp}.md"

python /home/bfly/yunwei/ccb_source/scripts/phase6_fake_matrix_smoke.py \
  --test-root /home/bfly/yunwei/test_ccb2 \
  --project-name "${project_name}" \
  --provider fake \
  --ccb-test /home/bfly/yunwei/ccb_source/ccb_test \
  --timeout 120 \
  --reset \
  --run \
  --output-dir "${report_dir}" \
  --history-report-path "${history_report}" \
  --json
```

Expected report outputs:

- `${report_dir}/phase6_fake_matrix_report.json`
- `${report_dir}/phase6_fake_matrix_rows.jsonl`
- `${history_report}`

Expected result before a full integrated run is performed:

- `phase6_fake_matrix_status == "incomplete"` for partial/single-case reports
- `phase6a_pass == false` for partial/single-case reports
- `phase6a_pass == true` only after the full integrated eight-case report
  passes

### Final Eight-Case Closure Command

Pending integrated execution. The command above is the candidate full-matrix
runner; its output is accepted only after reviewer audit of the generated JSON,
JSONL, and Markdown evidence.

Owner: the integrated full-matrix run is a distinct integrator/reviewer task
after the `smoke-busy-release` runner is reviewer-accepted. Default owner is
`talk2`, or a designated reviewer if explicitly assigned. Do not fold this run
into a worker implementation package or count partial tranche evidence as the
full matrix run.

Closure command requirements:

- runs all eight required cases in one evidence report;
- writes JSON report, JSONL rows, and Markdown history report;
- uses `/home/bfly/yunwei/ccb_source/ccb_test`;
- runs from `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and
  `CCB_SOURCE_HOME`;
- includes `smoke-busy-release` through the implemented runner.

The command is accepted only if its report says:

```text
phase6_fake_matrix_status == "pass"
phase6a_pass == true
required_case_count == observed_case_count == implemented_case_count == 8
missing_case_ids == []
not_implemented_case_ids == []
hard_failure_case_ids == []
```

## Required Eight-Case Coverage

| Case | Expected Route | Expected Round | Final Status | Cleanup | Expected Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `smoke-direct-execution-pass` | `direct_execution` | `pass` | `done` | `released` | `pass` |
| `smoke-needs-detail-pass` | `needs_detail` | `pass` | `done` | `released` | `pass` |
| `smoke-macro-adjustment` | `macro_adjustment_request` | `replan_required` | `replan_required` | `released` | `valid_non_success` |
| `smoke-blocked` | `blocked` | `blocked` | `blocked` | `released` | `valid_non_success` |
| `smoke-partial-completion` | `partial_completion` | `partial` | `partial` | `released` | `valid_non_success` |
| `smoke-reviewer-reject-rework` | `direct_execution` | `pass` | `done` | `released` | `pass` |
| `smoke-reviewer-cannot-accept` | `direct_execution` | `replan_required` | `replan_required` | `released` | `valid_non_success` |
| `smoke-busy-release` | `direct_execution` | `busy` | `running` | `retained_busy` | `valid_non_success` |

Every row must include:

```text
task_id
expected_route
observed_route
route_decision_correct
round_result
final_status
cleanup_result
runtime_residue
classification
ask_reachability
authority_checks.topology_dispatch_absent
authority_checks.communication_edges_absent
authority_checks.provider_reply_authority_parsing_absent
```

## Authority Checks

The evidence package must prove all of the following:

- `route_decision_correct=true` is computed from observed route versus
  expected route, not provider assertion.
- All status, route, and round-result transitions are script-owned imports.
- No provider reply directly writes `index.json`, `status`, `next_owner`,
  `current_loop`, task README authority sections, or topology files.
- Mainline mount topology proposals, desired files, and observed files omit
  `edges`, `gates`, and `artifacts`.
- `topology_dispatch.json` is absent for ask-first mainline cases.
- Runner does not consume provider output bundles through
  `--consume-role-output` or an equivalent authority path.
- Planner compact imports remain macro-only; detail docs remain task-detailer
  owned.

Suggested audit files per case:

```text
.ccb/runtime/loops/<loop-id>/agent_mount_topology.desired.json
.ccb/runtime/loops/<loop-id>/agent_mount_topology.observed.json
.ccb/runtime/loops/<loop-id>/agent_mount_topology.events.jsonl
.ccb/runtime/loops/<loop-id>/asks.jsonl
.ccb/runtime/loops/<loop-id>/round.json
.ccb/runtime/loops/<loop-id>/round_summary.md
.ccb/ccb.config
```

## Cleanup And Residue Checks

Released cases must prove:

- dynamic execution agents are absent from `ccb ps`;
- dynamic execution agents are absent from `.ccb/ccb.config`;
- dynamic execution agents are absent from observed topology;
- resident roles remain present and askable;
- no active leases remain for released agents;
- loop evidence files may remain as history but do not represent active
  runtime residue.

The busy-release case must prove:

- release returns `retained_busy`;
- the busy agent pane/session is preserved;
- the task remains `running` with bound `current_loop`;
- resident roles are unaffected;
- a later idle reconcile releases the retained agent cleanly;
- the final report clearly distinguishes retained evidence from residue.

Triangulate cleanup with:

```bash
/home/bfly/yunwei/ccb_source/ccb_test --project <case-project> ps
cat <case-project>/.ccb/ccb.config
cat <case-project>/.ccb/runtime/loops/<loop-id>/agent_mount_topology.observed.json
rg -n "topology_dispatch|edges|gates|artifacts|consume-role-output" <case-project>/.ccb/runtime/loops/<loop-id>
```

Use the actual case project path and loop id from
`phase6_fake_matrix_report.json`. Do not run these from the source checkout as
a live runtime project.

## Acceptance Evidence Package

Hand this package to reviewer1/reviewer2:

- exact command transcript or command list, including cwd and environment;
- `ccb_test --diagnose` output;
- source check outputs for `py_compile`, focused pytest, and `git diff --check`;
- `phase6_fake_matrix_report.json`;
- `phase6_fake_matrix_rows.jsonl`;
- generated Markdown history report;
- per-case project roots and loop ids;
- per-case `round.json`, `round_summary.md`, `asks.jsonl`, topology desired and
  observed files, topology events, and release evidence;
- residue audit outputs for `ps`, `.ccb/ccb.config`, and observed topology;
- authority audit summary for no topology communication DSL, no topology
  dispatch, no provider-reply authority parsing, and no false `done`;
- accepted review artifact for worker1 remaining matrix work, accepted review
  artifact for worker2 lifecycle closure, and accepted review artifact for the
  `smoke-busy-release` runner;
- explicit statement that Phase 6A is a program-matrix claim only, not a real
  provider or long-running workflow claim.

## Reviewer Gate

Reviewer1 should confirm:

- all eight matrix cases observed;
- expected route, round result, final status, cleanup, and classification match
  the matrix;
- non-success outcomes are not counted as pass;
- no hidden retry loop beyond the bounded reviewer rework case;
- busy-release depends on accepted lifecycle closure and has later idle release
  evidence.

Reviewer2 should confirm:

- module-level gates from `job_9cb0746fad98` are satisfied for program-side
  evidence;
- final report wording does not overclaim Phase 6B or production readiness;
- authority boundaries remain intact across task docs, topology, ask
  collaboration, lifecycle, and reporting.

Post-matrix reviewer request shape:

```text
Please audit the integrated Phase 6A fake-provider matrix evidence package and
the module-level worksheet against:
- Phase 1-6 acceptance goal:
  docs/plantree/plans/agentic-loop-workflow/goals/phase1-6-acceptance-goal.zh.md
- module/final checklist:
  job_9cb0746fad98-art_25c9e57d83a840c1.txt
- closure runbook:
  docs/plantree/plans/agentic-loop-workflow/topics/phase6a-fake-provider-matrix-closure-runbook.md
- module worksheet:
  docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-module-level-audit-worksheet.md
- draft final report:
  docs/plantree/plans/agentic-loop-workflow/history/phase1-6-acceptance-report-draft.md

Scope:
- decide whether Phase 6A program-matrix claim is acceptable;
- audit all six program-side modules against actual matrix evidence;
- verify final report wording and residual risks;
- do not approve Phase 6B, real-provider capability, production default
  enablement, or long-running multi-round workflow claims.

Required evidence:
- exact source-wrapper command transcript with cwd, HOME, CCB_SOURCE_HOME, and
  ccb_test path;
- ccb_test --diagnose output from /home/bfly/yunwei/test_ccb2;
- local source checks and git diff --check output;
- phase6_fake_matrix_report.json and phase6_fake_matrix_rows.jsonl;
- generated Markdown matrix history report;
- per-case project roots, loop ids, round_summary, asks, topology
  desired/observed/events, and release/retain evidence;
- residue audit for ps, .ccb/ccb.config, and observed topology;
- authority audit for no topology communication DSL, no topology dispatch, no
  provider-reply authority parsing, and no false done.

Required verdict:
- reviewer1: matrix-case and lifecycle/residue verdict;
- reviewer2: module-level and final-report wording verdict;
- explicit answer whether Phase 6A is claimable only for program-matrix scope;
- explicit answer that Phase 6B remains blocked unless a separate real-provider
  lab later passes its own launch gate and B7 review.
```

## Final Report

After reviewer acceptance, the current dated report is
[phase1-6-acceptance-report-20260704.md](../history/phase1-6-acceptance-report-20260704.md).
It records:

1. Phase 6A accepted only for the fake-provider, single-round program-matrix
   scope.
2. Links to the accepted matrix report JSON, JSONL, Markdown report, and
   reviewer artifacts.
3. Module verdicts and residual risks from reviewer2.
4. Phase 6B not claimable until the real-provider lab completes and passes B7
   review.

The superseded draft remains at
[phase1-6-acceptance-report-draft.md](../history/phase1-6-acceptance-report-draft.md)
as the audit trail.
