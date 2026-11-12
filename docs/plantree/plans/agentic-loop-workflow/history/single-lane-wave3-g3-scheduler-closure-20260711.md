# Single-Lane Wave 3 G3 Scheduler Closure

Date: 2026-07-11
Status: Accepted source/runtime closure; no fake or live provider claim
Branch: `workflow/agentic-loop-topology`
Final commit before this record: `94ea6d73`

## Scope

Wave 3 connected the landed R1 authority state machine, R2 Git transactions,
T1 topology/capacity authority, Config V3 capacity snapshot, and E1 evidence
interfaces into one controller-owned ready-frontier scheduler. It also closed
test-runtime and accelerator ownership leaks exposed while running the full
repository gate.

This checkpoint proves the integrated source kernel and its crash/recovery
contracts. It does not substitute deterministic fixtures for scheduler-driven
fake-provider flows and does not claim a visible real-provider project.

## Landed Commits

- `8d3fc102`: submit-all-ready scheduler, durable node state, reviewer/rework,
  dependency progression, integration, round completion, and resume entrypoint.
- `92da3faf`: automatic frontier continuation, unique event identity, bounded
  rework, public round schema, structured no-progress, and strict release.
- `bca51abd`: real R2 commit/review/integration authority, raw T1 observed
  topology validation, final compacted agent names, and active-workspace cleanup.
- `fb4b26c7`: explicit phase2 runtime-owner fixture and bounded process cleanup.
- `96172d92`: versioned runtime accelerator owner authority, safe takeover,
  kill integration, PID-reuse/lookalike protection, and residue accounting.
- `94ea6d73`: first-start fallback, exact deleted-executable normalization,
  corrupt-manifest recovery, and fail-closed socket/owner conflict handling.

## Direct Audit Findings And Repairs

`talk2` rejected scheduler states that stopped after the first frontier,
reported release residue as pass, reused event ids, ignored configured rework
limits, wrote the wrong round schema, or stalled without a structured reason.
It also rejected reviewer rework that was not recorded through R2 and compact
topology summaries used as if they were raw observed authority.

The full repository gate then exposed a separate ownership defect: phase2
tests could leave managed runtimes, and an accelerator started in a new
session could outlive ccbd with no durable owner. A later daemon could unlink
and rebind the same socket, producing duplicate sidecars. The landed repair
persists exact process identity, conservatively reclaims only verified owners,
preserves ambiguous evidence, and extends residue checks to process cwd.

## Verification

- G3 plus Wave 2 adjacent scheduler/integration gate: `495 passed`.
- Full non-provider-blackbox repository gate: `4210 passed, 2 skipped, 21 deselected`.
- Current-run command-line residue after the full gate: `0`.
- Current-run cwd-owned runtime residue after the full gate: `0`.
- Runtime accelerator population before/after the full gate: `6 -> 6`.
- Accelerator ownership/lifecycle/kill focused suites and real subprocess
  recovery scenarios passed before integration.
- Changed-source `py_compile`, `pyflakes`, `git diff --check`, and clean
  workflow worktree checks passed.

## Residual Gates

- G5 must execute the scheduler through one-, two-, three-, and four-workgroup
  source/fake flows rather than only unit state transitions or E1 fixtures.
- G5 must cover restart, rework, partial, blocked, replan, integration failure,
  rollback, busy-retain, release, and strict evidence normalization.
- G6 still requires fresh visible opened projects with inherited real provider
  configuration and project-local role authority.
- No package, install, update, rollback, default enablement, or publication
  claim follows from this checkpoint.
