# Global Plan Tree Control Architecture Review

Date: 2026-07-15
Status: Initial review completed; required document revisions applied
Scope: Decision 031 and cross-worktree Plan Tree control design

## Review Evidence

- Reviewer: CCB `worker1`, read-only architecture review
- Job: `job_c147ef896b20`
- Reply: `rep_c5623c92f9ef`
- Artifact SHA-256:
  `aa4bdc4628a3db383a172bcfa88f1be0697fc8e9da3052e2c5f09fed92194ca7`
- Initial conclusion: document redesign required before implementation; Decision
  024's single-lane gate remained valid

The runtime artifact itself is not durable Plan Tree authority. This file keeps
only the accepted findings and revision disposition.

## Required Findings And Disposition

| Severity | Finding | Disposition |
| :--- | :--- | :--- |
| Critical | Git common-dir path plus an unspecified locator could split into two control holders | Added committed `portfolio_id`, local repository id, exact locator, explicit init/handoff/takeover state machine, holder lease, generation, and fencing |
| Critical | Code target, Plan Tree, journal, and events cannot be one atomic transaction | Replaced atomic-completion language with hidden-candidate integration saga and one target-ref promotion; runtime publication is recoverable |
| High | Revisions and an undefined authority digest could both over- and under-invalidate lanes | Added typed authority refs, deterministic closure/canonicalization, impact classes, and closure-identical rebase rule |
| High | Short lock did not fence resumed holders and current no-`fcntl` path runs unlocked | Added lease/fence checks, supported-filesystem probes, explicit fail-closed platform contract, and stale-holder rejection |
| High | Rebuildable index conflicted with current full-index overwrite/task-local locking | Added guarded canonical task-record migration, plan-store projection transaction, cutover, rollback, and A/B race gate |
| High | External `docs/` contracts were outside Plan Tree digest despite higher authority | Preserved root authority order and added immutable external contract refs to every relevant lane closure |
| High | Two-lane acceptance was too broad to falsify crash and isolation defects | Added per-stage control/task/lane/integration/freshness/real-provider fault matrix with recovery and residue requirements |
| Medium | Decision, global topic, and parallel topic repeated protocol details | Reduced Decision 031 to stable choices, made the global topic the protocol authority, kept lane semantics in the parallel topic, and split storage migration/acceptance by responsibility |
| Medium | Global query/projection freshness was unspecified | Added read-fence retry, incomplete/stale response contract, registry sequence, projection generation, and observation time |
| Low | New design files were not yet committed | Remains a Git-owner action; no commit was requested as part of this review turn |

## Additional Source-Backed Clarification

Review confirmed that current source:

- identifies a repository by the absolute Git common-dir path;
- rewrites the full task index from a previously loaded copy;
- uses task-local locks for task changes;
- executes `file_lock` without a lock when `fcntl` is unavailable;
- computes the legacy Planner projection digest from only `brief.md`,
  `roadmap.md`, and `TODO.md` under a worktree-local lock.

The revised documents treat these as migration prerequisites rather than
claiming they already satisfy the global protocol.

## Revised Authority Set

- [Decision 031](../decisions/031-global-plan-tree-authority-across-worktrees.md)
- [global control protocol](../topics/global-plan-tree-authority-and-cross-worktree-control.md)
- [storage and projection migration](../topics/global-plan-tree-storage-and-projection-migration.md)
- [cross-worktree acceptance matrix](../topics/global-plan-tree-cross-worktree-acceptance-matrix.md)
- [parallel Roadmap/Lane semantics](../topics/parallel-roadmap-lanes-and-planner-authority.md)
- [Decision 029 compatibility mapping](../decisions/029-planner-feedback-and-task-set-closure.md)

## Remaining Boundary

No multi-lane implementation is authorized. The next implementation-ready
sequence begins only after Decision 024's single-lane production gate, then the
control identity/election, locking, storage migration, authority closure, and
pre-concurrency acceptance rows. The requested independent Claude coworker
review is now recorded in
[global-plan-tree-claude-coworker-review-20260715.md](global-plan-tree-claude-coworker-review-20260715.md).
