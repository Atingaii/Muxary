# Startup Phase 0 Exact Keeper T1 Checkpoint

Date: 2026-07-17

Status: working-tree exact-readiness, resource-sampler, and formal
instrumentation-overhead checkpoint; not a release or an overall Phase 0 claim

## Problem Closed

The correlated readiness timeline previously knew only when the foreground CLI
observed a compatible daemon.  On a cold start that observation occurred at T2,
so T1 could only be an honest `observed_upper_bound`.  Persisting an absolute
performance-counter value in lifecycle authority would have mixed diagnostics
with state-machine truth and created a new durability cost.

The exact-T1 formal run also exposed an independent harness issue.  Resource
sampling used one cumulative process-identity set for both the next active
round and final cleanup.  Dead foreground PIDs therefore remained candidates
forever: in run N, `vanished_process_count` grew from `51` near the beginning to
`241` by pair 20.  This did not fabricate resource values, but it made scan work
grow with round count and widened the process-exit observation window.

## Working-Tree Correction

Exact T1 uses no new authority file and no extra durable write:

- keeper samples `time.perf_counter_ns()` immediately after the durable
  `phase=starting` lifecycle save returns, while still inside the short startup
  lock;
- the absolute value travels with the existing one-shot
  `startup_id + generation` child environment fence and is removed from the
  environment at child process entry;
- the child retains it only in memory.  The start handler trusts it only while
  the checkpoint and expected fence match the current app lease PID, daemon
  instance, and generation;
- the readiness recorder upgrades the cold T1 upper bound only when startup id,
  generation, origin, T2, and RPC ordering prove
  `T0 <= T1 <= T2 <= RPC`;
- reports persist only relative `elapsed_ms` with source
  `keeper_lifecycle_starting_committed`.  Neither absolute counter is
  persisted.  Missing or malformed diagnostics never block child boot and
  retain the upper-bound fallback;
- already-mounted warm starts remain `not_required_already_mounted` and cannot
  reuse the daemon boot checkpoint.

Resource sampling now keeps two scopes:

- `active_process_instances` is replaced by identities present in the prior
  terminal snapshot, so dead foreground processes do not accumulate in later
  sampling work;
- the cumulative observed set is retained only for final cleanup residue audit;
- foreground root and discovered descendants are read before persistent peers,
  narrowing the stat-to-I/O exit race without another procfs read;
- every sample carries only an aggregate unavailable-I/O event count, while
  unresolved fields are partitioned into mutually exclusive baseline,
  terminal, never-valid, and regression counters.  No PID, argv, cwd,
  environment, or raw procfs text is added;
- the formal gate remains fail-closed.  Terminal or otherwise unresolved I/O is
  still `process_io_partial`; the new counters explain it rather than hiding it.

## Preserved Degraded Evidence

The first exact-T1 formal A/B is preserved at:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-exact-t1-formal-20260717-n`

Its readiness and overhead gates passed: `20/20` pairs, paired p50
`+2.809 ms`, 95% CI `[-4.587,+6.754] ms`, one exact cold T1 at
`397.053 ms`, 23 warm not-required records, and `24/24` complete timelines.
One measured resource profile remained honestly degraded, so this run was not
used to claim resource completeness:

- profile:
  `pair-0012-instrumented/resource-profile.json`;
- startup run: `start_23b820ef9ca144549513276c61239585`;
- status/reason: `degraded / process_io_partial`;
- counters: one unavailable event, zero recovered gaps, six unresolved fields,
  one affected identity, zero identity gaps, and zero regressions;
- profile SHA256:
  `b3d388e13ea6fd10a33901366677bca1d2aeb22f10c142b50833e02122f0f649`.

The old artifact did not retain per-sample unavailable counts or the new cause
partition, so the strongest post-hoc conclusion is an unresolved endpoint gap,
not a proven baseline-versus-terminal classification.  It is intentionally not
relabelled complete.

## Active-Seed Smoke

The first post-correction smoke is:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-active-seed-exact-t1-smoke-20260717-o`

Prime, one warmup, and three measured starts completed with zero command
failures/timeouts.  All three measured profiles were formal-eligible and
process-I/O complete; exact-T1 readiness was `5/5`; cleanup had two clean
snapshots.  Every warm scan reported `vanished_process_count=1`, rather than
ordinal growth.  The non-statistical warmup captured one endpoint event and the
new partition identified it exactly as six terminal gaps, demonstrating that
diagnostic precision improved without weakening the measured-resource gate.

Summary/cleanup digests are
`b0ce55d9d8fe5e794887c170466b5f5f25488ade01e0f5c19542ba40fe92a4e6`
and
`15d5222ca5c2801c30a361926070f0cacddf17f6a491d3e4bd110bd86e583755`.

## Final Formal Recheck

The final same-fixture frozen `3 + 20` A/B is:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-exact-t1-active-seed-formal-20260717-p`

- valid pairs: `20/20`; command failures/timeouts: `0/0`;
- control/instrumented p50: `384.835 / 383.057 ms`;
- paired overhead p50: `-0.283 ms`;
- deterministic bootstrap median 95% CI: `[-4.316,+7.868] ms`;
- overhead budget: `10 ms`; gate: pass;
- readiness: `24/24` complete, exact cold T1 `421.969 ms`, 23 warm
  not-required records, zero upper bounds; gate: pass;
- resource: `24/24` present, verified, formal-eligible, and process-I/O
  complete; gate: pass;
- warm active scans: bounded at one or two vanished PIDs with no ordinal growth;
- cleanup: official `ccb_test kill`, `unmounted/stopped`, two clean snapshots.

Artifact digests:

- `benchmark-plan.json`:
  `80fc7b2c491c7348eec9616635deb45350c61ddc870673729d00ef4d26976b03`
- `summary.json`:
  `2794468cbcc464ebea235abcfb6b8cac2567e52b3bfdf4c7395dc23e3930a55f`
- `cleanup-resource-audit.json`:
  `0d37490e2cb55c22d7b37da3f028fb40aad841cf2df6cb983bfe73ae295f6196`

Source coordinates remained commit
`76eef7f49dee519956072ec615d29a58d890c2e9`, version metadata `8.2.0`, and
working-tree fingerprint
`6bc73052ec0fc4ee1bb9aebb465fcfc210a3fb75af754b0650ebbcff499787fb`.

## Deterministic Evidence And Claim Boundary

The exact-T1/startup-fence/readiness/resource-harness matrix passed `216`
tests.  The narrower process-resource/startup-harness matrix passed `100`.

This closes the exact keeper T1 and repeated active-resource-seed boundaries on
the Linux Codex-stub fixture.  It does not complete Phase 0.  The final summary
correctly retains `formal_claim_allowed=false` for
`phase0_measurement_contract_incomplete` and `scenario_matrix_incomplete`.
Interactive T5, the S0/S2/S3/S4/S5/fault matrix, strict
mounted-after-self-ping publication, real Codex/Claude qualification,
macOS/WSL/slow-filesystem coverage, and bounded Provider launch concurrency
remain open.
