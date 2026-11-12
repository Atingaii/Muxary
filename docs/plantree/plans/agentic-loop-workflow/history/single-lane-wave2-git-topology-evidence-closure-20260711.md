# Single-Lane Wave 2 Git, Topology, And Evidence Closure

Date: 2026-07-11
Status: Accepted component gate; no live multi-workgroup claim
Branch: `workflow/agentic-loop-topology`
Final commit before this record: `c64ab341`

## Scope

Wave 2 integrated three bounded packages in the required order:

1. R2 controller-owned Git integration;
2. T1 one-to-four-workgroup physical topology/capacity;
3. E1 deterministic evidence and failure classification.

The gate proves the three component surfaces compose on one branch. It does
not prove the G3 scheduler, provider fanout, or a visible real project.

## Landed Commits

- `f3b6b7a6`: node and integration worktrees, reviewed controller commits,
  deterministic merges, verification, root promotion, rollback, and recovery.
- `bd7bcbd7`: exact Git authority intents, failed-verification quarantine,
  lookalike rejection, rollback hardening, and idempotent cleanup.
- `64f95b1b`: deterministic one-to-four-workgroup demand/mount planning,
  capacity binding, placement, busy-retain, and owner-scoped release.
- `912764f6`: compacted generated placement names and strict pane bounds.
- `502cc3e1`: versioned row/report schemas and 19-case deterministic matrix.
- `c64ab341`: expected-outcome campaign semantics, nested malformed-input
  handling, all dynamic-control-role accounting, and schema-valid reports.

## Direct Audit Findings And Repairs

`talk2` reproduced and rejected three R2 false-authority paths before closure:
failed project-root verification could leave the root dirty, crash recovery
could accept lookalike Git commits without a durable intent, and cleanup had no
performing state machine. The landed hardening adds exact intent fencing,
verification quarantine, exact commit identity checks, rollback recovery, and
non-destructive eligibility plus idempotent cleanup.

T1 originally allowed generated workspace-group names and pane positions to
escape physical limits for long loop identifiers. The landed repair uses the
compiler's compacted names and rejects pane indexes outside the window.

E1 originally made the campaign impossible to pass by treating deliberate
negative controls as unexpected failures, could throw on malformed nested
data, omitted dynamic orchestrator/round-reviewer identities, and did not
validate produced reports with the declared JSON Schema. The landed repair
compares each case with its declared expected classification and always emits
structured schema-valid evidence.

## Verification

- R2 focused real-Git suite: `42 passed`.
- R2 adjacent workspace/lifecycle/hygiene suite: `61 passed`.
- T1 focused topology/capacity/lifecycle suite after repair: `75 passed`.
- R2+T1 combined gate on the integration branch: `180 passed`.
- R2+T1+E1 plus Phase 6/lifecycle adjacent smoke: `249 passed`.
- Changed-source `py_compile`: passed.
- `git diff --check` and clean integration worktree: passed.

The E1 command-line matrix completed with all 19 cases matching their declared
outcome: six `pass`, six `valid_non_success`, one `test_design_failure`, and
six `system_failure`, with no mismatches.

## Residual Gates

- G3 must pass the current active-workspace set into R2 cleanup authority.
- G3 must consume T1's returned final agent names; it must not reconstruct
  names that may have been compacted to physical limits.
- E1 fixtures are deterministic evidence tests, not live scheduler proof.
- No real-provider project, UI, package, install, update, or publication gate
  was opened or claimed at Wave 2.
