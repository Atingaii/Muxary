# Phase 1-6 Final Staging Manifest

Date: 2026-07-04
Status: DRY RUN ONLY / DO NOT STAGE FROM THIS FILE WITHOUT HUMAN REVIEW

## Purpose

This dry-run manifest classifies the current source-control state for the
accepted Phase 1-6 package. It records what should be included, ignored, or
deferred before a final human staging pass. It does not stage files, commit
files, move files, delete files, or claim Phase 6B readiness.

Authority:

- [Phase 1-6 final packaging hygiene](phase1-6-final-packaging-hygiene.md)
- Reviewer2 packaging hygiene acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_08484caac091-art_1299c45369de43a4.txt`
- Worker2 packaging formalization:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ac6140294b18-art_3982631569024f29.txt`
- Reviewer2 final package audit:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_055a5e798708-art_2255afc4ca87434a.txt`
- [Phase 1-6 evidence index](../history/phase1-6-evidence-index.md)

## Inventory Summary

Pre-manifest `git status --short` summary:

- modified tracked entries: `30`
- untracked entries: `31`
- ignored generated output observed separately: `dist/`, `dist-mobile/`

`dist/` and `dist-mobile/` are ignored by `.gitignore` and must not be staged.

## Include In Final Phase 1-6 Package

### Packaging / plan indexes

```text
.gitignore
docs/plantree/README.md
docs/plantree/plans/agentic-loop-workflow/README.md
docs/plantree/plans/agentic-loop-workflow/implementation-status.md
docs/plantree/plans/agentic-loop-workflow/open-questions.md
docs/plantree/plans/agentic-loop-workflow/roadmap.md
docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-final-packaging-hygiene.md
docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-final-staging-manifest-20260704.md
```

### Decisions, goals, topics, and acceptance evidence

```text
docs/plantree/plans/agentic-loop-workflow/decisions/019-orchestrator-triage-before-task-detailer.md
docs/plantree/plans/agentic-loop-workflow/decisions/020-mount-topology-and-ask-first-orchestration.md
docs/plantree/plans/agentic-loop-workflow/goals/minimum-production-candidate-goal.md
docs/plantree/plans/agentic-loop-workflow/goals/mount-topology-ask-first-landing-goal.md
docs/plantree/plans/agentic-loop-workflow/goals/phase1-6-acceptance-goal.zh.md
docs/plantree/plans/agentic-loop-workflow/goals/phase6-build-stage-verification.zh.md
docs/plantree/plans/agentic-loop-workflow/goals/phase6-real-capability-assessment-goal.md
docs/plantree/plans/agentic-loop-workflow/goals/phase6-single-round-task-matrix-goal.md
docs/plantree/plans/agentic-loop-workflow/history/phase1-6-acceptance-report-20260704.md
docs/plantree/plans/agentic-loop-workflow/history/phase1-6-acceptance-report-draft.md
docs/plantree/plans/agentic-loop-workflow/history/phase1-6-evidence-index.md
docs/plantree/plans/agentic-loop-workflow/history/phase6-real-capability-assessment-20260704.md
docs/plantree/plans/agentic-loop-workflow/topics/agentic-workflow-scheme.zh.md
docs/plantree/plans/agentic-loop-workflow/topics/architecture.md
docs/plantree/plans/agentic-loop-workflow/topics/mount-topology-and-ask-first-orchestration.md
docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-module-level-audit-worksheet.md
docs/plantree/plans/agentic-loop-workflow/topics/phase6-real-provider-lab-task-packs.md
docs/plantree/plans/agentic-loop-workflow/topics/phase6a-fake-provider-matrix-closure-runbook.md
docs/plantree/plans/agentic-loop-workflow/topics/phase6b-l0-launch-request-20260704.md
docs/plantree/plans/agentic-loop-workflow/topics/phase6b-l0-owner-decision-packet-20260704.md
docs/plantree/plans/agentic-loop-workflow/topics/phase6b-real-provider-lab-launch-checklist.md
docs/plantree/plans/agentic-loop-workflow/topics/planner-plan-tree-brief-and-detail-boundary.md
docs/plantree/plans/agentic-loop-workflow/topics/planner-role-design.md
docs/plantree/plans/agentic-loop-workflow/topics/role-catalog-and-boundaries.md
docs/plantree/plans/agentic-loop-workflow/topics/runtime-workflow-graph-and-reconciler.md
```

Phase 6B launch documents are included only as planning/readiness artifacts.
They do not package real-provider capability and do not approve L0.

### Satinoos selected assets

```text
docs/plantree/plans/agentic-loop-workflow/topics/satinoos-workflow-introduction.zh.md
docs/plantree/plans/agentic-loop-workflow/assets/satinoos-workflow-layered-flow.svg
docs/plantree/plans/agentic-loop-workflow/assets/satinoos-workflow-layered-flow.png
docs/plantree/plans/agentic-loop-workflow/assets/satinoos-workflow-introduction.zh.pdf
```

These are included because the accepted packaging guidance selected the
Markdown/SVG source plus PNG/PDF outputs for this package.

### RolePack drafts

```text
docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.ccb_round_reviewer/
docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.ccb_task_detailer/
docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.code_reviewer/
docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.coder/
```

These four draft directories are included as accepted package deliverables.
Legacy draft RolePacks remain tracked/history only where already present; do
not broaden the package by adding unrelated draft directories.

The review-only dry-run command keeps these four RolePack package paths as
directories because each accepted package contains nested package files. Human
package-owner review must still verify that only these four draft package roots
are included.

### Accepted code, scripts, and tests

```text
lib/cli/models_start.py
lib/cli/parser_runtime/commands.py
lib/cli/render_runtime/ops_views_basic.py
lib/cli/services/loop_ask_first.py
lib/cli/services/loop_runner.py
lib/cli/services/loop_topology.py
lib/cli/services/plan_tasks.py
lib/cli/services/topology_dispatch.py
lib/provider_execution/fake.py
scripts/workflow_closure_smoke.py
scripts/phase6_fake_matrix_smoke.py
test/test_loop_capacity_cli.py
test/test_loop_topology_cli.py
test/test_loop_topology_dispatch_contract.py
test/test_orchestrator_rolepack.py
test/test_phase6_fake_matrix_smoke_script.py
test/test_plan_tasks_cli.py
test/test_question_cli.py
test/test_workflow_closure_smoke_script.py
```

These are the accepted Phase 1-6 / Decision 020 / Phase 6A code and test
surfaces from the reviewer-gated packages.

## Exclude / Ignore

```text
dist/
dist-mobile/
```

Evidence:

```text
.gitignore:23:dist/ dist
.gitignore:24:dist-mobile/ dist-mobile
.gitignore:24:dist-mobile/ dist-mobile/ccb-mobile-v8.0.8.apk
```

Do not run `git add -f dist/` or `git add -f dist-mobile/`. Current ignored
inventory includes generated distribution output, including the large mobile
APK and related checksum/signing/badging files.

## Defer / Do Not Stage

```text
lib/provider_pane_status/claude_pane.py
test/test_provider_pane_status_claude_pane.py
```

These files are deferred to managed-provider/provider-pane reliability. They
are not part of the Phase 1-6 acceptance package unless that owner explicitly
adopts them in a later package.

## Needs Human / Package-Owner Decision

No remaining owner decision is known for the current `git status --short`
inventory under the accepted packaging checklist.

If a later status contains files not listed in this manifest, stop and ask the
package owner before staging them.

## Review-Only Dry-Run Commands

Do not execute these commands from this manifest without a human package-owner
review. They are provided as a reviewable staging shape only.

```bash
# Review-only: inspect ignored generated output.
git status --short --ignored=matching dist dist-mobile
git check-ignore -v dist dist-mobile dist-mobile/ccb-mobile-v8.0.8.apk

# Review-only: dry-run include set.
git add --dry-run -- \
  .gitignore \
  docs/plantree/README.md \
  docs/plantree/plans/agentic-loop-workflow/README.md \
  docs/plantree/plans/agentic-loop-workflow/decisions/019-orchestrator-triage-before-task-detailer.md \
  docs/plantree/plans/agentic-loop-workflow/decisions/020-mount-topology-and-ask-first-orchestration.md \
  docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.ccb_round_reviewer \
  docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.ccb_task_detailer \
  docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.code_reviewer \
  docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.coder \
  docs/plantree/plans/agentic-loop-workflow/goals/minimum-production-candidate-goal.md \
  docs/plantree/plans/agentic-loop-workflow/goals/mount-topology-ask-first-landing-goal.md \
  docs/plantree/plans/agentic-loop-workflow/goals/phase1-6-acceptance-goal.zh.md \
  docs/plantree/plans/agentic-loop-workflow/goals/phase6-build-stage-verification.zh.md \
  docs/plantree/plans/agentic-loop-workflow/goals/phase6-real-capability-assessment-goal.md \
  docs/plantree/plans/agentic-loop-workflow/goals/phase6-single-round-task-matrix-goal.md \
  docs/plantree/plans/agentic-loop-workflow/history/phase1-6-acceptance-report-20260704.md \
  docs/plantree/plans/agentic-loop-workflow/history/phase1-6-acceptance-report-draft.md \
  docs/plantree/plans/agentic-loop-workflow/history/phase1-6-evidence-index.md \
  docs/plantree/plans/agentic-loop-workflow/history/phase6-real-capability-assessment-20260704.md \
  docs/plantree/plans/agentic-loop-workflow/implementation-status.md \
  docs/plantree/plans/agentic-loop-workflow/open-questions.md \
  docs/plantree/plans/agentic-loop-workflow/roadmap.md \
  docs/plantree/plans/agentic-loop-workflow/topics/agentic-workflow-scheme.zh.md \
  docs/plantree/plans/agentic-loop-workflow/topics/architecture.md \
  docs/plantree/plans/agentic-loop-workflow/topics/mount-topology-and-ask-first-orchestration.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-final-packaging-hygiene.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-final-staging-manifest-20260704.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase1-6-module-level-audit-worksheet.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase6-real-provider-lab-task-packs.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase6a-fake-provider-matrix-closure-runbook.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase6b-l0-launch-request-20260704.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase6b-l0-owner-decision-packet-20260704.md \
  docs/plantree/plans/agentic-loop-workflow/topics/phase6b-real-provider-lab-launch-checklist.md \
  docs/plantree/plans/agentic-loop-workflow/topics/planner-plan-tree-brief-and-detail-boundary.md \
  docs/plantree/plans/agentic-loop-workflow/topics/planner-role-design.md \
  docs/plantree/plans/agentic-loop-workflow/topics/role-catalog-and-boundaries.md \
  docs/plantree/plans/agentic-loop-workflow/topics/runtime-workflow-graph-and-reconciler.md \
  docs/plantree/plans/agentic-loop-workflow/topics/satinoos-workflow-introduction.zh.md \
  docs/plantree/plans/agentic-loop-workflow/assets/satinoos-workflow-introduction.zh.pdf \
  docs/plantree/plans/agentic-loop-workflow/assets/satinoos-workflow-layered-flow.png \
  docs/plantree/plans/agentic-loop-workflow/assets/satinoos-workflow-layered-flow.svg \
  lib/cli/models_start.py \
  lib/cli/parser_runtime/commands.py \
  lib/cli/render_runtime/ops_views_basic.py \
  lib/cli/services/loop_ask_first.py \
  lib/cli/services/loop_runner.py \
  lib/cli/services/loop_topology.py \
  lib/cli/services/plan_tasks.py \
  lib/cli/services/topology_dispatch.py \
  lib/provider_execution/fake.py \
  scripts/workflow_closure_smoke.py \
  scripts/phase6_fake_matrix_smoke.py \
  test/test_loop_capacity_cli.py \
  test/test_loop_topology_cli.py \
  test/test_loop_topology_dispatch_contract.py \
  test/test_orchestrator_rolepack.py \
  test/test_phase6_fake_matrix_smoke_script.py \
  test/test_plan_tasks_cli.py \
  test/test_question_cli.py \
  test/test_workflow_closure_smoke_script.py

# Review-only: guard against accidentally staging deferred files.
git status --short -- \
  lib/provider_pane_status/claude_pane.py \
  test/test_provider_pane_status_claude_pane.py
```

## Final Guardrails

- Do not stage `dist-mobile/`.
- Do not stage `dist/`.
- Do not stage deferred provider-pane files.
- Do not claim Phase 6B or real-provider capability from this package.
- Do not run source-wrapper runtime validation or real-provider lab commands as
  part of this dry-run manifest.
- After a human stages files, require a staged-file review before committing.
