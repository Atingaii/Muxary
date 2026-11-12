# Phase 1-6 Final Packaging Hygiene

Date: 2026-07-04
Status: STAGING MANIFEST ACCEPTED FOR HUMAN REVIEW / FINAL STAGING PENDING

## Purpose

Track source-control packaging decisions that must be resolved before a final
Phase 1-6 acceptance commit or report package. Reviewer2 confirmed these
hygiene issues do not block the Phase 6A program-matrix technical claim, but
they do block final source-control packaging.

## Authority

- Inventory:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_cfb3cde1fe2c-art_741b3f7d240e41e5.txt`
- Reviewer2 decision guidance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_fc9a05cdd528-art_be5f86df458c4bb7.txt`
- Worker2 formalization:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ac6140294b18-art_3982631569024f29.txt`
- Reviewer2 final packaging hygiene acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_08484caac091-art_1299c45369de43a4.txt`
- Dry-run staging manifest:
  [phase1-6-final-staging-manifest-20260704.md](phase1-6-final-staging-manifest-20260704.md)
- Reviewer2 dry-run staging manifest acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_6e27efd2bf13-art_734269e45fd04a07.txt`

## Include In Final Patch Candidate

- Decision 020 and Phase 1-6 / Phase 6A goals, status, runbook, evidence, and
  draft/final acceptance report docs.
- Ask-first / Decision 020 runtime code and focused tests that are accepted by
  the relevant reviewer gates.
- `scripts/phase6_fake_matrix_smoke.py` and
  `test/test_phase6_fake_matrix_smoke_script.py`.
- Accepted RolePack draft directories for `ccb_task_detailer`,
  `ccb_round_reviewer`, `coder`, and `code_reviewer`.
- Satinoos source and selected distributable outputs:
  `topics/satinoos-workflow-introduction.zh.md`,
  `assets/satinoos-workflow-layered-flow.svg`,
  `assets/satinoos-workflow-layered-flow.png`, and
  `assets/satinoos-workflow-introduction.zh.pdf`. The SVG is the editable
  source; the PNG is embedded by the Markdown topic; the PDF is a selected B0
  verification/distribution output named by the build-stage verification goal.
- Shared plan README/topic edits reviewed in this pass when they are limited
  to Phase 1-6 / Decision 020 index, route-name, RolePack naming,
  compact-import policy, or legacy-dispatch boundary updates.

## Exclude Or Ignore

- `dist/` and `dist-mobile/`: generated release/mobile output, including the
  large APK and signing/checksum artifacts. Reviewer2 classifies this as
  exclude and says it should be archived or ignored before final packaging.
  The repository `.gitignore` now ignores both directories.
- `lib/provider_pane_status/claude_pane.py` and
  `test/test_provider_pane_status_claude_pane.py`: defer from the Phase 1-6
  acceptance package. Current source search shows no active Phase 1-6 runtime
  import; this belongs to managed-provider/provider-pane reliability follow-up
  unless a provider-pane owner explicitly adopts it.

## Needs Owner Decision

- No owner decision remains open for the four packaging questions in this pass.
- Long-term `drafts/` governance remains a later docs-organization question,
  but it does not block this Phase 1-6 package: the four accepted RolePack
  draft directories are included as package deliverables.
- Final source-control staging/commit/package execution is still pending. The
  accepted guidance defines what belongs in the package; it does not itself
  stage or commit files.
- The dry-run staging manifest is accepted for human package-owner staging
  review. A human package-owner must still review the include/exclude/defer
  sets against current `git status --short`, avoid broad unintended staging,
  and require staged-file review before commit.

## Recorded Packaging Decisions

- `dist/` and `dist-mobile/` are generated release/mobile output and are
  ignored through `.gitignore`. Do not stage them in the Phase 1-6 package.
- Satinoos tracks source plus selected outputs for this package: Markdown,
  SVG, PNG, and PDF listed above. Do not treat this as a blanket rule to track
  all future generated assets; future generated outputs need an explicit
  reference from a goal, report, or release package.
- `claude_pane.py` and its focused test are deferred to managed-provider
  reliability and should not be staged in the Phase 1-6 acceptance package.
- Broad README/topic diffs reviewed in this pass are classified as include:
  `docs/plantree/README.md`,
  `docs/plantree/plans/agentic-loop-workflow/README.md`,
  `topics/agentic-workflow-scheme.zh.md`, `topics/architecture.md`,
  `topics/planner-plan-tree-brief-and-detail-boundary.md`,
  `topics/planner-role-design.md`, `topics/role-catalog-and-boundaries.md`,
  and `topics/runtime-workflow-graph-and-reconciler.md`.
- Final staging should still remain slice-aware: code/tests, docs/evidence,
  RolePack drafts, selected assets, and ignored/deferred artifacts.

## Dry-Run Staging Manifest

- [phase1-6-final-staging-manifest-20260704.md](phase1-6-final-staging-manifest-20260704.md)
  classifies the current `git status --short` inventory into include,
  exclude/ignore, and defer/do-not-stage sets. It includes review-only
  dry-run command shapes, but does not stage or commit files. Reviewer2
  accepted it for human package-owner staging review in `job_6e27efd2bf13`.
  Worker3 tightened the broad `goals`, `history`, and `topics` dry-run paths in
  `job_cd066f5d6147`; only accepted RolePack draft package roots remain as
  directory paths, with package-root rationale. Reviewer2 accepted the
  tightened manifest for human package-owner final staging review in
  `job_055a5e798708`; actual staging, staged-file review, and commit remain
  human-owned. A later manifest refresh records the current 61-entry status and
  the ignored `dist/` directory alongside `dist-mobile/`; request a refreshed
  package-owner audit before staging from the refreshed manifest. Reviewer2
  accepted the refreshed inventory in `job_2f61849ef1a4`; the Phase 6B L0
  owner-decision packet is included only as a planning/readiness artifact.

## Non-Goals

- Do not use this checklist to block the Phase 6A program-matrix technical
  decision once runtime evidence is complete.
- Do not delete, move, ignore, or revert files from this checklist without an
  explicit owner decision.
- Do not treat this checklist as a substitute for worker2 lifecycle closure,
  the full eight-case matrix run, module-level audit, or dated final report.
