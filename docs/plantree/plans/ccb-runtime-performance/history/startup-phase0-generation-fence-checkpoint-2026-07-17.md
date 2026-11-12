# Startup Phase 0 Generation Fence Checkpoint

Date: 2026-07-17

Status: working-tree correctness and formal instrumentation-overhead
checkpoint; not a release or an overall startup-performance claim

## Root Cause

The first lifecycle transaction correction serialized CLI running intent and
keeper transaction creation, but it did not yet close the complete child
generation boundary:

- keeper assigned a lifecycle generation, while a child with no prior lease
  could independently choose generation `1`;
- child finalizers and several stop, heartbeat, keeper-observation, reload, and
  namespace writers could still perform a stale `load -> save` outside the
  project `startup.lock`;
- readiness checked serving-process fields but did not independently prove
  that current lifecycle authority still described the same mounted startup;
- readiness timeout did not terminate/reap the child that keeper had spawned,
  allowing a slow child to publish late;
- a superseded child could replace the single latest daemon-boot startup report
  with its late failure.

These were one authority-fencing problem, not five unrelated timing bugs.  A
durable atomic replace prevents torn JSON but cannot prevent an internally
valid stale record from overwriting a newer transaction.

## Working-Tree Correction

- Keeper passes an exact one-shot `startup_id + generation` fence to the child.
  The child consumes it, validates fresh lifecycle authority under
  `startup.lock`, and claims the keeper generation rather than deriving a new
  generation from `lease.json` alone.
- Child progress and mounted publication reacquire the short lock and validate
  the exact lifecycle transaction.  Mounted publication also validates the
  live lease PID, daemon instance, generation, socket, and mount state.
- Cleanup occurs only after this child actually claimed and successfully
  released its own lease.  Claim conflict, concurrent stop, or superseding
  startup cannot be rewritten as failed/unmounted by the old child.
- Lifecycle/lease RMW writers in CLI stop/finalize, daemon stop/heartbeat,
  keeper connectable observation, reload signature handoff, and namespace
  epoch publication now use the same lock with a fresh authority recheck.
  Read-only no-change paths retain their lock-free/no-fsync fast paths.
- Shutdown lifecycle intent and the shutdown-intent record are published
  together.  A delayed old shutdown finalizer is a no-op once a later start has
  cleared the intent or published a running transaction.
- Keeper readiness requires exact spawned PID, daemon instance, lease
  generation, current lifecycle generation, `mounted/running`, matching
  startup id, and mounted startup stage.  A contradictory old socket response
  is rejected.
- Readiness failure terminates and reaps only the `start_new_session` process
  group created by that spawn, and parent log handles close on success or
  failure.
- Latest daemon-boot report publication is lifecycle-fenced, so a superseded
  child cannot overwrite a newer generation's report.
- Process-I/O aggregation retains the last valid counter across a transient
  unreadable sample.  A later non-regressing value recovers the gap; baseline,
  terminal, never-valid, or regressing gaps remain fail-closed and visible.

The startup supervision, lifecycle stability, and diagnostics contracts were
updated with these rules.

## Deterministic Regression Evidence

The focused matrix proves:

- missing lease claims the keeper's non-contiguous generation;
- same/higher other-holder claims leave lifecycle, lease, and socket unchanged;
- stop or supersede during restore prevents old mounted/failed/unmounted
  publication;
- a delayed old shutdown finalize cannot cancel a new startup;
- real POSIX processes wait on the shared startup lock and fresh-read the newer
  transaction after release;
- stale keeper config-match and observation-failure snapshots cannot revive a
  stopped lifecycle;
- old socket identity and lifecycle/serving contradictions fail readiness;
- readiness failure reclaims the exact spawned process group and closes parent
  log handles;
- superseded daemon-boot failure cannot overwrite the newer startup report;
- transient process-I/O gaps recover only with a later valid non-regressing
  sample, while unresolved gaps remain partial.

The combined startup/lifecycle/reload matrix passed `282` tests.  The process
resource plus startup-harness matrix passed `95` tests before the external run.

## External Source Runtime Evidence

Safety smoke:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-startup-fence-resource-recovery-20260717-k`

Cold prime, one warmup, and one measured start completed on generation `7`
with zero failures/timeouts.  Measured warm wall was `366.028 ms`; daemon ensure
was `0.998 ms`; external attribution was `94.526%`; all three readiness and
resource records were present; process I/O was complete; official cleanup
reached `unmounted/stopped` and two clean discovery snapshots.

Formal same-fixture instrumentation A/B:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-fence-io-formal-20260717-l`

- frozen seed/order: `20260717`, `3` warmup pairs and `20` measured pairs;
- valid pairs: `20/20`; failures/timeouts: `0/0`;
- control/instrumented p50: `368.857 / 370.469 ms`;
- paired overhead p50: `+1.911 ms`;
- deterministic bootstrap median 95% CI: `[-4.581, +5.397] ms`;
- budget: `10 ms`; instrumentation-overhead gate: pass;
- readiness artifacts: `24/24`, structurally complete, with cold T1 still an
  honest upper bound;
- resource artifacts: `24/24` verified, formal-eligible, and process-I/O
  complete; resource gate: pass;
- cleanup: official kill plus two clean snapshots.

Artifact digests:

- `benchmark-plan.json`:
  `82c9cd14f5a98ca74f4a2f9174dc57a386413235cb035d43ba397c9bb9e22b6b`
- `summary.json`:
  `cda4064be37c6b3918089970ba659ff2f610e4217541183a023b2c57ca8f6c88`
- `cleanup-resource-audit.json`:
  `2598bda6265b37fc5a148a62cb5fda8dc2fe14c2079998f67a11e36b83d4918b`

Source coordinates remained commit
`76eef7f49dee519956072ec615d29a58d890c2e9`, version metadata `8.2.0`, and
working-tree fingerprint
`140206aa48f17a96f8314c64bd1db40fd316593549af294f7565e3674b490407`.

## Claim Boundary

This closes the child-generation fence and restores the dedicated
instrumentation/resource-quality gates on this Linux stub fixture.  Overall
`formal_claim_allowed` remains false.  At this checkpoint exact keeper T1 was
still absent; it was closed by the later
[exact-T1 checkpoint](startup-phase0-exact-t1-checkpoint-2026-07-17.md).  The
S0/S2/S3/S4/S5/fault matrix, interactive T5, real Codex/Claude qualification,
macOS/WSL/slow-filesystem coverage, and the strict mounted-after-self-ping
publication boundary remain open.  Bounded Provider launch concurrency has not
started.
