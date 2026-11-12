# Positive Landing Scope

Date: 2026-06-16

## Commit Scope

Land only the positive-benefit Rust helper paths:

- `native.output.observe`
- `storage.scan.inventory`
- `storage.scan.summary`
- shared helper contract, build/install/release support, focused tests, and
  positive benchmark evidence

Do not land the negative or unresolved helper implementations in this commit:

- `jsonl.tail` / `jsonl.tail.strict`
- `jobs.tail.summary`
- `jobs.query.recent`
- `project_view.tmux.parse`
- `project_view.recent_jobs`

Those experiments remain documented in the plan history as evidence for future
query-shape or in-process designs, but their code paths should not enter the
main branch from this landing.

## Evidence

- Phase 3 native output observation: positive, default-auto path retained.
- Phase 4 storage inventory scan: positive, default-auto path retained.
- Phase 12 compact storage summary: positive in synthetic fixture, opt-in path
  retained for further default-enable review.
- Phase 5/6/8/9 job and project-view experiments: insufficient or negative
  subprocess-boundary benefit; keep as notes only.
