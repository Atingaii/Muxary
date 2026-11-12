# Startup Phase 0 Stable Process-I/O Checkpoint

Date: 2026-07-17

Status: S4 resource-quality checkpoint; Phase 0 remains open

## Finding

The first formal S4 runs exposed a real sampler race rather than startup or
provider failure.  In one process snapshot the sampler could read a valid
`/proc/<pid>/stat`, then observe the same process as a zombie while opening
`/proc/<pid>/io`.  Linux returns `EACCES` for a fresh zombie I/O open.  The next
`communicate()` reaped the foreground process, so the six missing I/O fields
could never be recovered and the profile correctly remained partial.

The evidence shape was stable:

- one unavailable process identity produced exactly six missing fields;
- the unavailable event occurred immediately before process count fell;
- both 50 ms and 20 ms intervals reproduced it, so faster periodic sampling
  was not a root fix;
- a same-UID host experiment proved a fresh zombie I/O open fails while an I/O
  descriptor opened when the task was alive remains readable until reap.

A second formal attempt proved that opening stable descriptors only after
cmdline/executable/cwd classification left a smaller first-observation race.
Two of twenty measured profiles first observed one short-lived identity with
no valid I/O value.  That retained failure was not discarded.

## Fix Boundary

`dev_tools/perf_process_resources.py` now uses a profile-local stable I/O
handle cache:

- cache identity is `(pid, start_ticks)`, never PID alone;
- a no-follow proc directory descriptor binds the `stat` and `io` opens to one
  proc instance;
- accepted handles are read-only, close-on-exec, bounded to 256 identities,
  and revalidated against the expected identity;
- targeted command-window discovery acquires the handle immediately after the
  stat identity read, before slower classification;
- repeated samples use one bounded offset-zero `pread`, not value carry-forward
  or a second I/O observation;
- success, timeout, spawn failure, sampling failure, aggregation failure, and
  all ordinary exception paths close every retained descriptor;
- missing fields, read failures, identity mismatch, limit exhaustion, and
  counter regression continue to fail closed as partial evidence.

This recovers a real kernel counter value; it does not interpolate a missing
value.  Process I/O remains labelled `sampled_lower_bound` because a task may
still be created and fully exit between samples.

Unprivileged TASKSTATS was evaluated and rejected.  This Linux 6.8 host has the
required kernel accounting, but same-UID live and zombie PID queries both
return `EPERM` because the family requires `CAP_NET_ADMIN`.  The benchmark must
not gain that capability or a privileged sidecar merely to improve telemetry.

## Deterministic Verification

The focused process-resource and startup-harness matrix passes:

```text
107 passed in 9.63s
```

Coverage includes:

- a real Linux zombie read through an already-open handle;
- offset-zero rereads and descriptor survival after path disappearance;
- PID/start-ticks reuse rejection;
- close-on-exec and the cache limit;
- success, timeout, `Popen`, capture, and aggregate exception cleanup;
- transient-gap recovery plus retained baseline, terminal, never-valid, and
  regression partial classifications;
- benchmark correlation, privacy, formal resource gating, and cleanup logic.

## Retained External Evidence

All stateful runs used the owner-marked external fixture under:

```text
/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4
```

They used the absolute source wrapper, isolated source HOME, the Codex provider
stub, no attach, and only official `ccb_test kill/start` lifecycle paths.

### Initial Stable-Handle Smoke

`phase0-s4-stable-io-smoke-20260717-ad`

- S4 start `1/1`, readiness `1/1`, process I/O `1/1`, zero timeout/failure;
- five stable identities, 146 reads, 142 reused reads, zero handle/read error;
- official cleanup reached `unmounted/stopped` and two clean snapshots;
- summary/cleanup/resource SHA256:
  `a25fe5b1dd9a153fcde12ea7997ee07487d7c14d2a0e34f5bd7bc628239c4701`,
  `9df79fd7e2633fc7c977edcfc77eb5602695d8702dadeb005d8d010b9657c3d2`,
  `3a35ab662ccd76f45f11d0df1f6c408d1e54002126235d0baf1f8de49416d4c5`.

### Retained First Formal Failure

`phase0-s4-stable-io-formal-20260717-ae`

- startup and readiness were `23/23`, measured starts `20/20`, cleanup clean;
- resource I/O was only `21/23` overall and `18/20` measured;
- the two failures were one never-valid identity times six fields, proving the
  handle was still acquired too late for first observation;
- summary/cleanup SHA256:
  `5e2f295b2162255425136544dbf57fe3583c57db059ed7510412dfc41715c22e`,
  `76e2ad734e05ce2b04a04479753a2e1af22828e965deb8ae4c050a786a992e66`.

### Early-Acquisition Stress

`phase0-s4-early-io-stress-20260717-af`

- measured starts, readiness, formal resource profiles, and process I/O all
  passed `10/10`;
- two early open attempts raced, then succeeded before the first I/O read;
  unavailable and unresolved counts remained zero;
- summary/cleanup SHA256:
  `85e446547e57bf2eca4570c4ba98ed48f682d5cdf9234c8592d2cd1cfd20055c`,
  `d447dbea484187379af3722dc11b3f83ad2472f4c4c95c6a0031110d9c831754`.

### Final S4 `3 + 20`

`phase0-s4-early-io-formal-20260717-ag`

- measured starts `20/20`, warm-ups `3/3`, zero failure/timeout;
- exact readiness `23/23`;
- resource profiles verified/formal/process-I/O complete `23/23`;
- 118 stable opens and 3518 reused reads, with zero open/read/mismatch/limit
  failure and zero unavailable/unresolved I/O fields;
- wall p50/p95 `1193.533/1327.391 ms`;
- official cleanup reached `unmounted/stopped` and two clean snapshots;
- summary/cleanup SHA256:
  `2e9603a9a71ea01b96b6c9e075fa22ad2c6024a022f4f50045fc82f14520f1cb`,
  `8dce37c3e985c14ddea9fa137c25eca73feec52606e3278ce58b2b7f7b74121e`.

The earlier same-fixture 20 ms run had p50/p95 `1195.060/1330.003 ms` and only
`17/20` measured I/O-complete profiles.  The final observation is
`-1.527/-2.613 ms`, but this is not an interleaved performance A/B and therefore
is only evidence of no visible material regression, not a speedup claim.

### Final Warm Instrumentation A/B

`phase0-warm-stable-io-ab-formal-20260717-ah`

- frozen `3 + 20`, `20/20` valid pairs, `40/40` measured commands;
- control/instrumented p50 `410.619/413.173 ms`;
- paired p50 `+2.783 ms`, bootstrap 95% CI `[-2.558,+4.274] ms`, below the
  `10 ms` budget;
- readiness and resource profiles `24/24`; measured I/O `20/20`; cleanup clean;
- plan/summary/cleanup SHA256:
  `41a727904643c96fa8027f7ccf0486098aa328fd871631b0963f90392c4c40e4`,
  `2c73a08bcfc5129417068faaa113850d3292b807f9f2c4ca40d171e650e912db`,
  `6fc62698eea06db8c2410fd2296de43b564f241283c6d3ba1d082dc19fc557b2`.

## Claim Boundary And Next Work

The S4 process-I/O and instrumentation-overhead gates now pass.  The summary
still correctly reports `formal_claim_allowed=false` and `smoke_only` because
the scenario, fault, provider, platform, interactive-T5, and comparison gates
are not complete.  Next work is the versioned scenario-construction manifest,
then deterministic S3 compensation and supported S0/S4/S5a constructors; S2
must remain unavailable until an official daemon-replacement control-plane
primitive exists.
