# Startup Phase 0 CLI-Only Checkpoint

Date: 2026-07-17

Status: S0 CLI-only hot-path slice closed on one Linux stub fixture; Phase 0 remains open

## Contract Decision

S0 now measures one introspection-only CLI command:

```text
ccb_test --print-version
```

The wrapper `exec`s into the source CLI, and the version branch returns before
project resolution, phase-2 dispatch, daemon ensure, RPC, namespace work, or
Provider work.  This makes S0 an honest wrapper/Python/import/early-dispatch
measurement; it is not a replacement for S1 warm attach or a claim about the
full visible startup path.

The measured command must not create a startup transaction.  It therefore has
no `startup_run_id`, no startup process trace, and no T1-T6 or supervisor/Agent
statistics.  A successful ordinary cold prime creates one mounted healthy
fixture and one startup report.  The harness then freezes daemon, generation,
namespace, every configured runtime identity, and the complete report file
identity.  Every S0 round must preserve that one baseline.  The pre-existing
report is copied only as `startup-report-sentinel.json`; it is never attributed
to the measured command.

Resource correlation is bound by benchmark coordinates, profile id, command
output hash, frozen authority token, and identical report identity.  A supplied
profile must observe exactly one newly created command-process identity across
sampled snapshots.  Same-bytes report rewrite, changed content, deletion,
startup metadata in stdout, more than one observed process, runtime/generation/
namespace drift, unhealthy/degraded runtime, non-steady reconcile state,
command failure, or final preservation drift all fail closed.

The procfs sample count is intentionally a lower bound: it cannot exclude a
process whose complete lifetime falls between two snapshots.  The separate
no-subprocess evidence for this boundary is the wrapper's `os.execvpe`, the
CLI entrypoint's immediate version return before phase 2, and an isolated Linux
`strace -f -e trace=process` validation.  That trace exited 0 with `v8.2.1`,
showed only `execve` replacements/path attempts plus `exit_group`, and showed
zero `fork`, `vfork`, `clone`, or `clone3`.  This one Linux trace is not
promoted into a cross-platform guarantee or a replacement for the benchmark.
It was run from `/home/bfly/yunwei/test_ccb2` with an empty inherited
environment and explicit isolated source home:

```text
env -i HOME=/home/bfly/yunwei/test_ccb2/source_home \
  CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
  CCB_TEST_ROOTS=/home/bfly/yunwei/test_ccb2 \
  CCB_SOURCE_ALLOWED_ROOTS=/home/bfly/yunwei/test_ccb2 \
  PATH=/usr/local/bin:/usr/bin:/bin \
  strace -f -e trace=process \
  /home/bfly/yunwei/ccb_source/ccb_test --print-version
```

The raw trace is retained outside the source checkout at mode `0600` beneath a
mode `0700` directory:

```text
/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/
  artifacts/startup/phase0-s0-cli-only-process-trace-20260717-e/
  strace-process.txt
size: 691 bytes
SHA256: e4fb2b4a423977aa0183d6dcf8695f0e1c3bb95828268c2142a40aaea7dbdede
```

`ccb ping ccbd` was rejected as the S0 command because its current control path
may recover a stale daemon.  `ping all` is non-recovering but still includes
project/RPC work already owned by other scenarios.  `--print-version` gives the
smallest stable boundary matching S0's CLI-only definition.

## Retained Failure And Correction

The first external smoke, `phase0-s0-cli-only-smoke-20260717-a`, stopped after
the prime because the new health gate counted only literal `healthy`.  Real
restored Codex-stub runtimes correctly persist `health=restored`, which the
runtime supervision, mount, warm-reuse, and mixed-recovery contracts all treat
as a success state.  The failure was retained rather than bypassed.

The correction centralizes the benchmark success-health set as
`healthy|restored`; `failed` and `degraded` remain rejected.  A dedicated
regression exercises the restored state.  This is a harness classification fix,
not a product runtime relaxation.

## Deterministic Verification

The final startup-harness file passes:

```text
103 passed in 25.55s
```

The S0 subset is `13 passed`; it covers the command/trace boundary, immutable
sentinel semantics, same-bytes rewrite, content change, deletion, stale startup
metadata, strict mounted/live/success-health/steady baselines, restored health,
command failure, resource correlation without startup id, exactly-one-observed-
process enforcement, and final cleanup/preservation.  A direct CLI-router
regression also proves the version branch returns before the first downstream
handler.  The expanded process-resource, source-guard, CLI-management, and full
CLI-router matrix passes:

```text
162 passed in 6.56s
```

The complete startup-harness pass and the adjacent matrix both ran with stable
HEAD observations.

## Retained External Evidence

All stateful validation used the absolute source wrapper from the existing
owner-marked external fixture, isolated `HOME`/`CCB_SOURCE_HOME`, deterministic
Codex stubs, no attach, launch cap 1, and official lifecycle commands only:

```text
/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4
```

The final clean-HEAD artifact is:

```text
artifacts/startup/phase0-s0-cli-only-formal-clean-20260717-d
```

It is bound to source commit
`c1cf38df3001b672e3c35967cc52c9756788971b`, version `8.2.1`, and the absolute
source `ccb_test` wrapper.

- frozen schedule: 3 warmups plus 20 measured rounds;
- measured completion: `20/20`, zero failure and zero timeout;
- measured wall p50/p95: `286.132/298.046 ms`, below the S0 budget of
  `750/1000 ms`;
- CLI-only evidence: `23/23` rounds passed, all startup ids absent, all report
  before/after identities equal, and exactly one unique frozen report identity;
- resource evidence: `23/23` verified/formal/process-I/O-complete profiles, all
  with exactly one observed newly created process identity; measured profiles
  `20/20`;
- scenario evidence: `24/24` S0 manifests valid and passing, including the one
  ordinary prime;
- readiness: explicitly `not_applicable_cli_only`; the prime startup timeline
  is excluded rather than reused;
- final preservation: daemon/generation/namespace/runtime/report baseline
  unchanged before teardown;
- official cleanup: stopped/unmounted generation `140` and two clean resource
  snapshots.

Artifact SHA256 values:

```text
summary.json                                      1629fc529c46498a55bd3efc0c7ef54c1cfe32f758673727f613e09f2080bb05
cleanup-resource-audit.json                       0a4dd08ed35dbb4ca5fc637ec4959d816fa9f1c7055d4bca9071543b86db986b
run-0001/scenario-construction.json               82f90f15aaec2964fc4082d1a3bcdaa60359efc26e6818b7ac20cece2b69d3cc
run-0020/scenario-construction.json               3c8c5a0dc2613203a4996c2783262da52f9550b683619b596bad72f2494c52a2
```

The earlier corrected `0 + 1` smoke
`phase0-s0-cli-only-smoke-20260717-b` also passed every scenario/resource/
preservation/cleanup gate at `290.340 ms`; it is retained as the safety gate
before the repeated run.

## Claim Boundary And Next Work

This closes S0 on one Linux ext4, two-Agent Codex-stub fixture and shows that
this CLI-only layer is not the source of the previously observed multi-second
full cold startup on that fixture.  It does not qualify real Codex/Claude,
macOS, WSL, slow filesystems, interactive attach, S5b first/update start, or
full end-to-end S1-
S5 performance.  The summary correctly remains `smoke_only` and
`formal_claim_allowed=false` because the overall scenario/provider/fault/
platform matrix and instrumentation-overhead qualification remain incomplete.

Next Phase 0 work is automated fresh-per-round S5a and cache/first-update S5b,
then the remaining serial fault matrix and platform/real-provider lanes.  S2
remains explicitly unavailable until an official daemon-replacement primitive
exists.  The resource schema should also add an explicit
`process_count_completeness=sampled_lower_bound` field and separate the measured
resource gate from an all-profile audit before external consumers depend on the
count.  Provider-launch concurrency remains deferred until those serial
authority and compensation gates are complete.
