# Global Plan Tree Storage And Projection Migration

Date: 2026-07-15
Status: Required migration design; implementation gated by Decision 024
Authority: [Decision 031](../decisions/031-global-plan-tree-authority-across-worktrees.md)
Protocol: [global-plan-tree-authority-and-cross-worktree-control.md](global-plan-tree-authority-and-cross-worktree-control.md)
Read when: changing task canonical storage, task indexes, Planner projection
targets, projection locks, upgrade compatibility, or rollback

## Purpose

Move current single-worktree task/index and Planner projection behavior onto the
global control protocol without silently changing the meaning of integrated
single-lane revisions.

## Current Constraints

Current source has two shared-write bottlenecks:

- `lib/cli/services/plan_tasks.py` treats one
  `plans/<plan>/tasks/index.json` as both lookup source and record store. Each
  update rewrites a previously loaded full index while locks are task-local, so
  two different tasks can lose one another's update.
- `lib/cli/services/planner_feedback_apply.py` defines the current PlanTree
  projection digest over only `brief.md`, `roadmap.md`, and `TODO.md`, and uses
  `.planner-projection.lock` inside the current worktree plan root. It does not
  cover decisions, open questions, status, another worktree, or repository
  contracts.

`lib/storage/locks.py` also runs without a lock when `fcntl` is unavailable.
That fallback is not allowed for this migration.

## Migration Invariants

- One authority mode is active at a time; index and canonical records are never
  simultaneous writable truth.
- Existing single-lane projection digests retain their exact three-target
  meaning until an explicit manifest cutover.
- Backfill and cutover run under the global fenced holder and plan-store lock.
- Every cutover is one authority commit with preimage/source-set digests.
- A mixed old/new binary must reject writes rather than downgrade storage or
  omit new authority surfaces.
- Rollback is allowed only before a newer-schema-only semantic write; afterward
  restore requires forward recovery.

## Canonical Task Store Migration

1. Enter `index_authority_v1` maintenance mode and freeze concurrent plan-task
   writes. Audit duplicate ids, malformed records, task directories, artifact
   refs, and the frozen index digest.
2. Backfill one `tasks/<task-id>/task.json` per index record under one plan-store
   lock. Legacy identity is qualified by `(portfolio_id, plan_id, task_id)`;
   newly created task ids are portfolio-unique.
3. Verify record count and every canonical record digest against the frozen
   index. Commit the records while keeping `index_authority_v1` read authority.
4. Build `index.json.tmp` only from canonical records. Its header contains
   schema, portfolio/plan id, authority commit, projection generation, record
   count, and canonical source-set digest.
5. One manifest transaction flips `task_store_mode` to
   `canonical_records_v1`, flushes the file and parent directory, and atomically
   renames the projection.
6. Readers validate the index header against current authority. Mismatch causes
   bounded rebuild or fail-closed error, never stale-record fallback.
7. Canonical per-task CAS owns semantic updates. One plan-store projection
   transaction rebuilds/switches the index so different-task writes cannot
   overwrite each other.
8. Remove index-authority write code only after upgrade, rollback, concurrent
   write, crash-point, and mixed-version rejection gates pass.

## Planner Projection Migration

The current three-file digest becomes explicitly named
`legacy_projection_digest`. Do not expand its input set in place; changing that
digest's meaning would break persisted Decision 029 intents and recovery.

New `ccb.plantree.change.v1` operations use manifest-declared typed surfaces:

```text
brief
roadmap narrative and Roadmap Graph
plan/task manifests
decision create/supersede
open-question add/narrow/resolve
implementation-status stable transition
evidence/index projection
external contract reference update
```

Each operation carries allowed path/selector, preimage digest, target digest,
semantic transition, and typed authority closure. The global controller lock
and target-ref CAS replace worktree-local `.planner-projection.lock` as publish
authority. The local lock may remain only as legacy single-lane compatibility
until cutover; it cannot protect a multi-worktree write.

Cutover sequence:

1. Inventory every persisted open Decision 029/detailer backfill transaction and
   its exact legacy projection digest/target set.
2. Add dual-read support that recognizes legacy transactions but emits new
   proposals with both `legacy_projection_digest` and full Decision 031 basis.
3. Reject a legacy-only proposal whenever multi-lane mode, a non-legacy target,
   external contract ref, or changed authority closure is involved.
4. Backfill manifest-declared surface ids and typed selectors; validate links,
   decision/open-question transitions, and generated projections.
5. Flip `planner_projection_mode` in one authority commit. New writes require
   typed operations; old persisted intents remain recoverable only within their
   frozen path/digest boundary.
6. Retire legacy write creation after restart/idempotence and rollback tests,
   while retaining a read-only decoder for supported upgrade history.

## Rollback And Recovery

Before cutover, rollback removes transaction-owned backfill records and restores
the frozen index/projection mode from its authority commit. After cutover but
before a new-schema-only write, one fenced authority commit may restore the old
mode and verified frozen projection.

After any canonical-record-only task update or typed non-legacy Planner
operation, rollback to an old binary is forbidden. Recovery must move forward,
rebuild projections from canonical records/manifests, and preserve the newer
authority commit.

Crash recovery records the last completed migration step and verifies source
and target digests before resuming. It never repeats a task revision, overwrites
a newer record, or changes mode based only on file presence.

## Acceptance

- Two processes update different tasks in one plan under distinct task locks;
  both canonical records and rebuilt projection retain both updates.
- Same-task stale CAS yields one winner and one structured conflict.
- Kill after every backfill, flush, rename, manifest cutover, and projection
  cutover boundary; recovery reaches one valid mode with no mixed authority.
- Duplicate legacy task ids are either deterministically qualified or reject
  migration before cutover.
- A stale/corrupt index cannot hide, invent, or roll back a canonical task.
- Corrupt canonical records that prevent bounded rebuild fail closed with
  record-level diagnostics; readers never fall back to an older index.
- Existing Decision 029 intents recover under the exact old three-file digest.
- A decision/open-question/status/external-contract change cannot be authorized
  by a matching legacy three-file digest alone.
- Old binaries reject `canonical_records_v1` or typed projection mode writes.
- Rebuilding all projections from canonical records/manifests produces the same
  source-set and authority digests.

Detailed fault rows are T01-T12 (including T03b, T09b, T10a, and T10b) in
[global-plan-tree-cross-worktree-acceptance-matrix.md](global-plan-tree-cross-worktree-acceptance-matrix.md).

## Related

- [global-plan-tree-authority-and-cross-worktree-control.md](global-plan-tree-authority-and-cross-worktree-control.md)
- [global-plan-tree-cross-worktree-acceptance-matrix.md](global-plan-tree-cross-worktree-acceptance-matrix.md)
- [planner-feedback-and-task-set-closure-plan.md](planner-feedback-and-task-set-closure-plan.md)
- [plan-update-script-landing.md](plan-update-script-landing.md)
- [../decisions/029-planner-feedback-and-task-set-closure.md](../decisions/029-planner-feedback-and-task-set-closure.md)
- [../decisions/031-global-plan-tree-authority-across-worktrees.md](../decisions/031-global-plan-tree-authority-across-worktrees.md)
