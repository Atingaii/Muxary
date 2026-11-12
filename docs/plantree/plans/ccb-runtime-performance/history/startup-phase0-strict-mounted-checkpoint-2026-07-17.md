# Startup Phase 0 Strict Mounted Checkpoint

Date: 2026-07-17

Status: working-tree correctness checkpoint; Phase 0 remains open

## Scope

This checkpoint closes the previously open boundary between socket existence,
self-ping, lease publication, runtime restoration, and final lifecycle
`mounted`.  It does not authorize provider-launch concurrency and does not
complete the S0-S6/provider/platform matrix.

## Root Causes Found

The pre-checkpoint child path could publish a mounted lease before listen and
had no child-owned self-ping.  Moving only the lease later exposed four deeper
failures:

- restore/adopt before the probe could write a generation that never mounted;
- publishing mounted before the normal accept loop left a connectable backlog
  with no continuous RPC service;
- clearing the bootstrap gate while unwinding a failed probe allowed a queued
  mutation to race shutdown;
- keeper steady-state reconciliation could observe the interim mounted lease
  during `starting/runtime_bootstrap`, promote lifecycle early to the invalid
  combination `mounted/runtime_bootstrap`, and make the correctly fenced child
  exit.

The audit also found blind socket-path unlink, bind/listen failure residue, an
unfenced legacy child able to claim a keeper startup, and legacy progress/
failure/report writes without complete generation/owner checks.

A second deep review after the first post-race smoke found five additional
generation-boundary defects:

- direct `CcbdApp.start()` could publish final mounted before continuous accept,
  so disk said ready while a real ping timed out;
- starting request/maintenance workers cleared a pre-serving worker error,
  allowing the serving loop to return without reporting startup failure;
- an old holder mismatch was collapsed to `lease=None`, allowing lifecycle-only
  unmount to overwrite the old lifecycle while a replacement lease was mounted;
- the keeper child-promotion suppression matched only stage text, so stale
  `starting/runtime_bootstrap` could mask a different live lease generation;
- old-daemon socket unlink ran before `startup.lock`, leaving a stat/unlink
  window against a replacement bind.

A final full-suite pass exposed a publication-order race and prompted a third
fail-closed review:

- final lifecycle `mounted/mounted` was saved immediately before the in-memory
  runtime-bootstrap flag was cleared.  A waiter could observe durable mounted,
  issue its first non-ping RPC in that gap, and receive
  `ccbd bootstrap accepts ping only`; five provider/start black-box tests
  reproduced this probabilistically;
- `shutdown_server()` cleared both bootstrap booleans, while request dispatch
  did not prioritize `_stop_event`.  A queued request could therefore interpret
  failed-cleanup state as ready and enter a mutating handler;
- `finish_runtime_bootstrap()` accepted a missing publication callback and did
  not reject an inactive/stopped gate or a sticky request-worker failure;
- a lifecycle atomic write can complete file replacement and then fail the
  parent-directory `fsync`.  Without a gate-held stop transition, ping could
  briefly report the visible mounted record as ready even though startup was
  failing;
- an unfenced same-process restart reused the OS PID and socket path but had a
  new daemon instance.  Recomputing ownership at mounted publication selected
  the predecessor generation instead of validating the already allocated next
  generation.

## Implemented Boundary

The child sequence is now:

1. validate the keeper fence or a safe legacy transaction under
   `startup.lock`;
2. reject live/non-socket path replacement, bind/listen transactionally, and
   durably claim the starting owner;
3. run a nonce-bound self-ping through the existing request worker without
   holding the startup lock;
4. publish the mounted lease, then persist
   `phase=starting/startup_stage=runtime_bootstrap`; the in-memory lease becomes
   visible only after both durable writes succeed;
5. enter the normal accept loop immediately.  Ping remains serviceable while
   normal RPC is gated;
6. restore jobs/handoffs/runtime authority with generation checks between
   recoverable units;
7. revalidate lease/lifecycle/PID/daemon-instance/startup identity and publish
   final `phase=mounted/startup_stage=mounted` before normal callers proceed.

The probe self-client has an identifiable local UNIX peer path.  Connections
that arrived first are deferred until the self-client completes, so a slow
half-request cannot consume the full probe deadline.  Probe failure freezes the
gate and stops the worker before shutdown.  Socket shutdown and failed bind
cleanup unlink only the inode owned by that server attempt.

Keeper reconciliation now treats recognized active child startup stages as
observation-only; it cannot synthesize mounted from the interim lease.  An
unfenced child rejects keeper-owned startup ids, and heartbeat, progress,
failure, release, and daemon-boot report writers are generation/owner fenced.

The follow-up closure makes direct `start()` stop at
`starting/runtime_bootstrap`; only the continuous serving path can finish final
mounted.  Worker error state is first-error-sticky per bound socket generation.
Keeper suppression now requires exact lifecycle/lease generation, PID, daemon
instance, and socket identity, while a stale lifecycle can be reconciled to a
verified replacement.  Socket close/unlink and lease/lifecycle release share
the startup lock, worker joins remain outside it, and lifecycle-only fallback
requires a fresh proof that no lease exists.

The final closure makes durable mounted publication and opening the normal-RPC
gate atomic relative to request dispatch.  Requests hold the short gate from
stop/bootstrap evaluation through handler selection/start; the serial request
lane therefore loses no request concurrency.  Bootstrap finish now requires a
publication callback, validates the listening socket, active state, stop state,
sticky worker error, and live request worker before and after the callback, and
sets stop while still holding the gate on any failure.  Thus a post-replace
`fsync` failure cannot admit ping or a mutating RPC.  Same-process restart now
validates the exact allocated generation plus the new daemon instance.

## Deterministic Evidence

- First expanded startup/keeper/socket/dispatcher matrix: `253 passed`.
- Strict mounted, legacy fence, socket transaction, slow-client, continuous
  accept, probe failure, lease/lifecycle split-write, concurrent child, stop,
  and supersede regressions are included in that matrix.
- An earlier focused keeper race recheck after the interim-promotion fix passed
  `37` tests; the first `253`-test matrix above includes that guard.
- The second deep-review closure passed a `128`-test focused matrix and its
  expanded startup/keeper/socket/dispatcher matrix passed `256` tests,
  including the socket-lock assertion.
- The final publication/fail-closed closure passed an `80`-test focused matrix
  and a `263`-test expanded startup/keeper/socket/dispatcher matrix.  Its
  deterministic tests hold the final lifecycle save after file replacement,
  prove a concurrent normal RPC waits, then cover both successful gate opening
  and simulated directory-fsync failure with zero handler calls.
- The complete restart plus phase2 provider black-box group passed `87` tests;
  the five tests that had exposed the publication gap passed both as an exact
  subset and inside that group.
- The complete source suite finished with `5324 passed, 2 skipped, 4 failed`.
  All four failures are the pre-existing additive-reload namespace baseline
  (`anchor pane missing for preserved agent 'agent2'`); the previous five
  readiness-race failures are absent.
- The successful-publication and post-replace-failure concurrency tests were
  then repeated `100` times each (`200` executions) with no failure or handler
  escape.
- A seven-trial alternating in-process dispatch micro A/B used `50,000` RPCs
  per arm/trial.  Median no-op-gate dispatch was `5492.004 ns/RPC`; RLock-gated
  dispatch was `5533.389 ns/RPC`, a net `41.385 ns/RPC` (`0.754%` of this
  socket-free JSON/dispatch micro path).  Real UNIX socket RPC includes larger
  transport cost, so this is a conservative relative denominator rather than
  an end-to-end latency claim.
- `py_compile` passed for the changed lifecycle, socket runtime, keeper, and
  daemon-wait modules.

One external smoke before the keeper fix failed safely and retained its
artifact:

- `phase0-warm-strict-final-mounted-smoke-20260717-t`
- failure: prime command exit `1`; official cleanup reached
  `unmounted/stopped` with two clean resource snapshots
- diagnosis: keeper promoted the active child transaction from interim lease
  evidence; the child fence rejected the contradictory phase/stage

That failure was converted into a deterministic keeper regression rather than
discarded as noise.

## External Source-Runtime Evidence

Fixture:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/project`

Final post-race-fix smoke:

`artifacts/startup/phase0-warm-strict-final-mounted-racefix-smoke-20260717-v`

- cold prime `1140.102 ms`; exact keeper T1 `412.596 ms`;
- three measured warm starts, p50 `376.554 ms`, zero failures/timeouts;
- readiness `5/5` complete: one exact cold T1 and four warm not-required T1s;
- resource profiles `5/5` present, verified, formal-eligible, and process-I/O
  complete;
- official cleanup reached `unmounted/stopped` with two clean snapshots;
- summary SHA256
  `48ade2379f306b0365e9f48990357d426e45d0aff62e5197863023fc49d0fb9c`;
  cleanup SHA256
  `92cc6647a7f8927b1b8510fdf1d4982cfed49ae08a43bbfa2b3dce41aaa3ee84`.

The same strict-mounted implementation completed two frozen `3 + 20` warm
instrumentation A/B runs before the final keeper-only race guard.  The first
retained a noisy failed overhead interval (paired p50 `+2.048 ms`, 95% upper
bound `+11.999 ms` against `10 ms`).  The required same-fixture recheck passed:

`artifacts/startup/phase0-warm-strict-mounted-formal-recheck-20260717-s`

- `20/20` valid pairs, zero failures/timeouts;
- control/instrumented p50 `374.437/372.389 ms`;
- paired p50 `-1.462 ms`, bootstrap 95% CI
  `[-4.406,+1.954] ms`, overhead gate pass;
- readiness `24/24` complete, exact cold T1 `398.026 ms`;
- resource profiles `24/24` verified/formal/process-I/O complete;
- official cleanup clean;
- plan/summary/cleanup SHA256:
  `82d9deb7ba2413cff4273b7e90239e6df5838a0d11e5f2e33348d68776a80736`,
  `f84c5f871152c7f77edc5b02e59528f46de7761d180e7cd80ec5bf4180a1ee6a`,
  `c31920a9687d6993d94558c9d30e8385cf63eac8719fc4782e806bbb7093dada`.

These are performance-safety and correctness artifacts, not a formal overall
startup claim: scenario/provider/fault/platform qualification remains open.

Post-second-review source-runtime smoke:

`artifacts/startup/phase0-warm-strict-race-closure-smoke-20260717-w`

- cold prime `1109.695 ms`; exact keeper T1 `404.215 ms`;
- three measured warm starts, p50 `372.707 ms`, zero failures/timeouts;
- readiness and resource profiles `5/5` complete, verified, formal-eligible,
  and process-I/O complete;
- official cleanup reached `unmounted/stopped` with two clean snapshots;
- summary SHA256
  `345af8db1f14130d423a9280f6205030e8ae9bf64cf9b84010de35dbe5b38692`;
  cleanup SHA256
  `7750788646ee328707a41a2c79a836eb5bf80beee54249ea8043c419000033a5`.

Final-worktree formal A/B after the second-review closure:

`artifacts/startup/phase0-warm-strict-race-closure-formal-20260717-x`

- frozen `3 + 20`, `20/20` valid pairs, zero failures/timeouts;
- control/instrumented p50 `372.368/376.085 ms`;
- paired p50 `+4.341 ms`, bootstrap 95% CI `[-0.515,+9.619] ms`, within the
  `10 ms` overhead budget;
- readiness `24/24` complete, exact cold T1 `405.138 ms`;
- resource profiles `24/24` verified/formal/process-I/O complete;
- official cleanup reached `unmounted/stopped` with two clean snapshots;
- plan/summary/cleanup SHA256:
  `d0044f3020293c17a21c6aedabf2709ef0aea21efc252e5b63a4107a7d31792b`,
  `3bb835bb07cb7d2e8bb64982883a7b0b844820eb2757c2f9960a25ac5d7448a4`,
  `f053c77db219cc84a8f6ee718cca2a3a7532ccda3ac6aff25023c9838e7d0447`.

The interval passed with only `0.381 ms` headroom.  This is sufficient for the
frozen instrumentation gate, but it must not be described as a broad speedup or
as overall Phase 0 acceptance.

Post-atomic-gate source-runtime smoke:

`artifacts/startup/phase0-warm-strict-atomic-ready-smoke-20260717-y`

- cold prime `1160.745 ms`; exact keeper T1 `401.900 ms`;
- three measured warm starts, p50 `379.489 ms`, zero failures/timeouts;
- readiness `5/5` complete; all five resource profiles present and verified,
  measured profiles `3/3` formal/process-I/O complete;
- official cleanup reached `unmounted/stopped` with two clean snapshots;
- summary/cleanup SHA256:
  `6ea9571a1eb955b43139b9275500bf9c322d2680661c38ac913156b5d5a17879`,
  `677b8177503a55c1aa093a8dc5803da5421b4a0f61aab91eedfbed486406db34`.

Final post-atomic-gate frozen A/B:

`artifacts/startup/phase0-warm-strict-atomic-ready-formal-20260717-z`

- frozen `3 + 20`, `20/20` valid pairs and `40/40` measured commands, zero
  failures/timeouts;
- control/instrumented p50 `389.326/387.804 ms`;
- paired p50 `-3.562 ms`, bootstrap 95% CI `[-9.150,+8.481] ms`, inside the
  `10 ms` overhead budget;
- readiness `24/24` complete with exact cold T1 `472.442 ms` and no upper-bound
  substitution;
- all `24/24` resource profiles present and verified; all `20/20` measured
  profiles formal/process-I/O complete; official cleanup produced two clean
  snapshots;
- plan/summary/cleanup SHA256:
  `cdab2d62b04007f3712e0f88f0c2118275c6a8238e4d53d07ec71d12eecb3c52`,
  `2b41046e382a6c3fd9c86bea705f906c046afc356c69e855e6ab2ca4ca8a78d2`,
  `037aaf58d0b43370acbf631bd561c95755f659e57569e4c4bc211035829d0af1`.

The control arm contained two large environmental outliers, so the absolute
tail is not a speedup claim.  The frozen paired median interval still passed,
and the isolated gate micro A/B above found only nanosecond-scale steady-state
cost.  Overall `formal_claim_allowed` remains false because the scenario,
provider, fault, and platform matrices are incomplete.

## Remaining Work

- Decide whether runtime bootstrap can become recoverable/non-fatal so normal
  RPC readiness may move safely to the core-ready boundary; current normal RPC
  waits for final mounted.
- Resolve the broader request-worker versus maintenance-worker authority-write
  contract drift before provider launch concurrency.
- Build deterministic S2/S3/S5b constructors and finish S0/S4/S5a artifacts,
  interactive T5, slow-filesystem, macOS/WSL, Codex, and Claude qualification.
