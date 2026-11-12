# G6C Decision 029 Integration And Root8 Diagnostic

Date: 2026-07-12
Status: implementation integrated; real acceptance pending
Phase: G6C / Decision 029 P5
Read when: resuming the final source and visible real-provider acceptance

## Scope

This checkpoint records the current integration branch after the Decision 029
task-set closure package, transaction hardening, parent-authority harness
repairs, the rejected root8 real-provider run, and the follow-up detail-ready
reconciliation fix. It is not an acceptance report.

## Integrated Source

- Branch: `workflow/g6c-integration`
- Worktree: `/home/bfly/yunwei/ccb_worktrees/g6c-integration`
- Current accepted source implementation head: `c37c4ac4`
- Decision 029 core starts at `4f166209` and includes task-set parent authority,
  Detailer-to-Planner feedback, deterministic task-set aggregation, Planner
  backfill, Frontdesk notification, revision fencing, exact-once recovery, and
  transaction durability.
- Harness and admission hardening through `8faa6fa4` makes parent selection and
  transaction recovery follow persisted source authority instead of discovery
  order or provider prose.
- `d941fa2e` replaces duplicated detail-ready regexes with one clause-aware
  matcher and adds task-lock-owned, stale-fenced reconciliation from
  `ready_for_orchestration/orchestrator` to `detail_ready/planner` when all
  recorded detail artifacts and the explicit stop contract remain valid.
- `a62ebb34`, `52c8701d`, and `c37c4ac4` close independent-review findings:
  corpus-wide deny-first matching, canonical importer/job/path/SHA provenance,
  monotonic state fencing, verified normal stop corpora, post-state idempotence,
  Markdown task-scope normalization, and one semantic revision shared by all
  outputs from a real Detailer import.

## Source Evidence

- Fourth-round independent detail-ready authority review: PASS at
  `c37c4ac4`; focused matcher, reconciliation, loop-capacity, PlanTask, and
  real Detailer import gate: `344 passed`.
- Worker1 completion snapshot:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/snapshots/job_2ccb4102700d.json`,
  SHA-256 `1d920d45af105b2ec1e9f1e8b455e2fc8ba133dcde5603e3b78f589dbd9b20b0`.
- Parent-authority harness checkpoint: `78 passed`.
- Current-HEAD full non-provider-blackbox gate after the final authority and
  plan retrieval repairs: `4739 passed, 2 skipped, 21 deselected in 732.49s`.
- `compileall`, `pyflakes`, and `git diff --check` passed after the one-line
  unused-import cleanup at `2d897845`.
- Historical real roots 1-8 retain their evidence files but were all safely
  unmounted with no active/queued/pending work before root9 materialization.

## Root8 Real-Provider Evidence

Preserved root:
`/home/bfly/yunwei/test_ccb2/deploy-g6c-real-talk2-20260712-8`

The project was opened with the source worktree `ccb_test`, inherited real
provider configuration, and a root-local Role store. Script-owned parent
authority and Frontdesk/Planner transaction journals were valid. L1 and L2
reached `done/pass`; the macro-adjustment L4 child reached
`replan_required`; the blocked L4 child reached `blocked`.

L3 produced all three detail artifacts and a valid local-detail result, but
the then-current stop matcher did not recognize the provider's affirmative
phrases `with terminal status detail_ready` and
`Preserve terminal expectation detail_ready`. Planner was activated, L3 was
reset to `ready_for_orchestration`, and Orchestrator repeated until the
auto-runner 24-step limit. The task-set therefore remained running and root8
was rejected. It must remain preserved and must not be reused after repair.

## Review Decision And Repair

The accepted repair has two layers:

1. One fail-closed shared stop-contract matcher used by both activation and
   actionable-task selection. It rejects negation, weak modality, conditions,
   questions, examples, fenced code, blockquotes, other-task text, conflicting
   terminal states, and schema/token enumeration.
2. A root8-shaped recovery action that verifies task state, route, loop
   absence, task revision, timestamp, artifact paths and digests, actor
   presence, and explicit stop authority under the task lock before committing
   `detail_ready/planner`. Same-authority replay is idempotent; stale authority
   fails closed.

## Remaining Acceptance Gates

1. Fresh root9 opened-project L1-L4 run proving L3 reconciliation, task-set
   aggregate closure, Planner backfill, Frontdesk notification, B7, visible
   panes, release, shutdown, and zero residue.
2. Remaining G6 real rows: three/four workgroups, in-flight restart,
   busy-retain, and provider-profile qualification.
3. G7 clean candidate package/install/update/rollback and one visible
   installed-candidate workflow. Publication remains a separate explicit
   authorization gate.

## Acceptance Ownership

Workers may review or implement bounded source repairs. Under the active
project runtime rules, `talk2` directly runs, observes, and audits fresh opened
real-provider projects and owns the final pass/reject decision. RolePack or
role-contract changes are reviewed with `mother`; source/runtime diagnostics
outside that boundary may be assigned to `ccb_self`.

For nested review dependencies, workers use `ask --chain` so the reviewer
result returns through the active parent continuation. `--silence` is reserved
for independent work and must not be used when the parent or `talk2` needs the
successful result to decide the gate.
