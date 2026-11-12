# Coworker Review

Date: 2026-06-15

## Source

Artifact:
`.ccb/ccbd/artifacts/text/completion-reply/job_38f7d1a16a12-art_31e4140fbfc54dd4.txt`

## Accepted Blocking Feedback

- Lock fallback behavior before assigning Phase 1 helper skeleton work.
- Make Phase 0 fixture and result artifact locations explicit.
- Include Rust toolchain readiness probes in Phase 0.

## Accepted Non-Blocking Feedback

- Do not assume JSONL is the first real helper until Phase 0 proves it.
- Measure helper subprocess startup overhead before choosing high-frequency
  helper paths.
- Treat `ccb-agent-sidebar` as release/toolchain evidence, not as a complete
  template for Python-to-Rust helper contracts.
- Keep CI feature-flag coverage narrow; do not create a full matrix for every
  helper flag.

## Accepted Follow-Up

- Phase 3 requires another review gate before broader helper rollout.
- Process-tree/signaling helper requires its own review gate.
- Source-install helper build policy remains open until Phase 0 evidence and
  Phase 1 packaging review.

## Dispatch Decision

Only `worker1` should run first. `worker2` waits for Phase 0 results and the
fallback contract. `worker3` waits for a helper contract skeleton and target
selection.
