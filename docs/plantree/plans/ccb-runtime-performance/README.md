# CCB Runtime Performance Plan

Date: 2026-07-17

## Purpose

Track startup, high-load, and interactive-latency performance work for CCB
across the full lifecycle. This plan is broader than the Rust helper plan: it
attributes cost across CCB core, shell/tmux orchestration, provider processes,
and UI/pane switching paths before selecting implementation work.

## Scope

In scope:

- Startup CPU, wall time, and process count attribution.
- Sustained high-load ask/queue behavior and provider mix attribution.
- Pane switching, sidebar/project-view refresh, and click-to-focus latency.
- Provider mount, idle, and lifecycle policies when they dominate CPU or
  memory.
- Shell/tmux subprocess and polling overhead inside CCB orchestration.
- Cross-reference to Rust helper evidence where it changes a measured hot path.

Out of scope for the first phase:

- A full rewrite of `ccbd` or the Python control plane.
- Replacing provider CLI internals.
- Optimizing based only on synthetic microbenchmarks without lifecycle
  attribution.

## Current Finding

The 2026-07-15 startup incident had a correctness-led critical path: explicit
multi-window panes were checked against the single entry-window id, so healthy
non-entry panes could be rejected and relaunched. The P0-P3 core fix now uses
logical-window identity, reuse-aware exactly-once provider preparation,
request-scoped discovery, batched/no-op tmux updates, scoped no-op persistence,
and persisted stage timings. Implementation and evidence are recorded in:
[topics/startup-critical-path-optimization-2026-07-15.md](topics/startup-critical-path-optimization-2026-07-15.md).

Goal Phase 0 is now executing.  The working tree contains a fail-closed
repeated-start harness, native run/report/process correlation, detailed startup
timings and operation counts, strict steady-reuse and readiness-integrity gates,
privacy-safe Linux resource profiles, and a two-snapshot post-cleanup residue
audit.  The attribution smoke measured `363.129 ms` and attributed `94.664%`
of external wall.  The latest formal same-fixture `3 + 20` instrumentation A/B
run passed its dedicated overhead gate: `20/20` valid pairs, paired p50
`-0.283 ms`, and 95% CI upper bound `7.868 ms` against a `10 ms` budget.  All
`24/24` instrumented resource profiles were process-I/O complete, and the
readiness gate had one exact cold keeper T1 plus 23 correctly not-required warm
records with no upper-bound substitution.  The overall result remains
non-formal because the scenario/provider/fault/platform matrices remain open.
The startup
lifecycle stale-RMW race found while locating T1 now has a complete child
generation fence, unified lifecycle/lease RMW discipline, strict readiness
identity, timeout-child reaping, and deterministic plus external regression
evidence.  Resource sampling now separates terminal active seeds from the
cumulative cleanup identity set, preventing dead foreground PIDs from making
repeated sampling work grow with round count.
The strict mounted boundary is also closed in the working tree: bind/listen is
transactional, the child self-pings through the normal request worker, the
normal accept loop runs during fenced runtime bootstrap, final lifecycle
mounted is child-owned, and keeper cannot promote an exact matching interim
lease.  A second deep review then closed direct-start false mounted, sticky
worker-error loss, foreign-lease lifecycle clobber, stale child-stage masking,
and shutdown-unlink lock races.  The post-closure external smoke passed with
clean teardown.  The final-worktree formal `3 + 20` warm overhead A/B also
passed: `20/20` valid pairs, paired p50 `+4.341 ms`, and 95% CI upper bound
`+9.619 ms` against the `10 ms` budget.  Phase 0 remains open for the scenario/
provider/fault/platform matrices and the request/maintenance commit boundary.
After that artifact, a full-suite pass exposed a final mounted-file versus
in-memory gate race.  The working tree now makes publication dispatch-atomic,
fails closed across post-replace write errors and shutdown, and validates exact
same-process restart generations.  Correctness matrices pass `80/263/87`, but
the prior formal artifact did not qualify this newer gate closure.  The fresh
external smoke now passes at warm p50 `379.489 ms`, and the frozen `3 + 20` A/B
passes with paired p50 `-3.562 ms`, CI upper `+8.481 ms`, `24/24` readiness,
`20/20` measured resource profiles, and clean teardown.  The full suite has no
new failures, and a direct dispatch A/B measures only `41.385 ns/RPC` net gate
cost.  This remains `smoke_only`; it is not overall Phase 0 acceptance.
S4 then exposed a Linux process-I/O observation race: a fresh proc I/O open
fails after a task becomes a zombie even while stat remains readable.  The
sampler now acquires bounded, close-on-exec, PID/start-ticks-validated handles
at first stat observation and reads the real final counters without filling or
carrying values.  The final S4 `3 + 20` run has `23/23` process-I/O-complete
profiles, and a fresh warm A/B passes with paired p50 `+2.783 ms` and bootstrap
95% CI upper `+4.274 ms` against the `10 ms` budget.  This closes the S4
resource-quality slice only; the broader scenario matrix remains open.
The harness now also has a durable, SHA-chained scenario-construction record.
It publishes immutable before/ready evidence, verifies final artifacts against
their exact run, rejects residue/same-generation cold labels/orphan attempts,
and persists only privacy-safe aggregate identity.  Deterministic tests pass
`114/114`; external S1, S4, and one-use S5a smoke artifacts all pass their
scenario/readiness/resource/cleanup gates.  S1 measured reuse kept all four
identities `same`, S4 changed all four, and S5a created all four.  At that
checkpoint only those construction slices were closed; S0/S2/S3/S5b, fault,
provider, platform, and interactive gates remained open.
The serial S3 constructor has since closed one more slice and exposed a real
working-tree correctness regression: an exact-owned dead pane was treated as
structural topology damage, causing a namespace rebuild and healthy-peer
relaunch.  Structural ownership is now separate from live binding eligibility.
The corrected external AQ run preserved daemon/generation/namespace and the
healthy peer, relaunched only the target with prepare counts `1/0`, observed
maximum launch concurrency 1 and no supervision recovery, completed in
`665.070 ms`, and cleaned up.  Follow-up review also excluded unknown slots
from cleanup protection, bounded the fallback listing, and rejected caller-
owned launch controls.  Focused tests pass `219/219`.  This remains a
Linux stub serial smoke; S2/S5b, fresh-per-round S5a, broader fault,
provider, platform, interactive, and concurrency gates remain open.
The S0 CLI-only slice is now closed on that Linux stub boundary.  Its exact
`ccb_test --print-version` command creates no startup transaction or RPC,
preserves one frozen healthy daemon/namespace/runtime/report baseline, and
requires the sampler to observe exactly one newly created command-process
identity.  That observation is a sampling lower bound; the wrapper `exec`, the
early version return, and one isolated Linux process-syscall trace (zero
`fork`/`vfork`/`clone`/`clone3`) supply the separate no-subprocess evidence for this
boundary.  A retained first smoke exposed the harness incorrectly rejecting
the valid runtime health `restored`; the corrected clean-HEAD `3 + 20` run
passed `20/20` measured commands, `23/23` resource/report checks, and `24/24`
S0 manifests with p50/p95 `286.132/298.046 ms` and clean teardown.  This result
is still `smoke_only` and does not qualify full startup or real Providers.
Evidence:
[history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md](history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md),
[history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md](history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md),
[history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md](history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md),
and
[history/startup-phase0-generation-fence-checkpoint-2026-07-17.md](history/startup-phase0-generation-fence-checkpoint-2026-07-17.md).
The exact-T1 and active-resource-seed follow-up is recorded in
[history/startup-phase0-exact-t1-checkpoint-2026-07-17.md](history/startup-phase0-exact-t1-checkpoint-2026-07-17.md).
The strict mounted/self-ping boundary and its retained keeper-race failure are
recorded in
[history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md](history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md).
The retained S4 failures, stable-I/O fix, and final resource/overhead evidence
are recorded in
[history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md](history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md).
The scenario-construction integrity fixes and retained S1/S4/S5a artifacts are
recorded in
[history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md](history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md).
The retained S3 product failure, topology fix, validator correction, and passing
serial mixed-recovery artifact are recorded in
[history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md](history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md).
The S0 boundary, retained health-classification failure, and clean formal-size
stub evidence are recorded in
[history/startup-phase0-cli-only-checkpoint-2026-07-17.md](history/startup-phase0-cli-only-checkpoint-2026-07-17.md).

Earlier lifecycle attribution remains relevant:

The first real lifecycle profile shows CCB core is not the dominant CPU cost:

- Startup: CCB core `16.5%`, provider `24.1%`, shell/tmux/system `56.0%`.
- High load: CCB core `17.3%`, provider `9.3%`, shell/tmux/system `72.6%`.

This points first to shell/tmux/subprocess overhead, provider lifecycle policy,
and interactive refresh isolation rather than broad CCB-core rewrites.

## Reading Path

1. [roadmap.md](roadmap.md)
2. [topics/startup-efficiency-analysis-and-optimization-goal.zh.md](topics/startup-efficiency-analysis-and-optimization-goal.zh.md)
3. [implementation-status.md](implementation-status.md)
4. [history/real-lifecycle-cpu-profile-2026-06-16.md](history/real-lifecycle-cpu-profile-2026-06-16.md)
5. [history/startup-phase0-resource-correlation-checkpoint-2026-07-16.md](history/startup-phase0-resource-correlation-checkpoint-2026-07-16.md)
6. [history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md](history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md)
7. [history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md](history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md)
8. [history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md](history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md)
9. [history/startup-phase0-generation-fence-checkpoint-2026-07-17.md](history/startup-phase0-generation-fence-checkpoint-2026-07-17.md)
10. [history/startup-phase0-exact-t1-checkpoint-2026-07-17.md](history/startup-phase0-exact-t1-checkpoint-2026-07-17.md)
11. [history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md](history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md)
12. [history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md](history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md)
13. [history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md](history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md)
14. [history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md](history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md)
15. [history/shell-system-bucket-split-2026-06-16.md](history/shell-system-bucket-split-2026-06-16.md)
16. [topics/startup-and-runtime-low-latency-plan.md](topics/startup-and-runtime-low-latency-plan.md)
17. [topics/startup-critical-path-optimization-2026-07-15.md](topics/startup-critical-path-optimization-2026-07-15.md)
18. [topics/candidate-commit-scope-2026-06-16.md](topics/candidate-commit-scope-2026-06-16.md)
19. [open-questions.md](open-questions.md)

## Related Plans

- [python-rust-hybrid-performance](../python-rust-hybrid-performance/README.md)
  covers Rust helper hot-path replacements. This plan uses those results as
  local evidence but owns lifecycle-level prioritization.
- [managed-tool-windows](../managed-tool-windows/README.md) and
  [windows-wezterm-native](../windows-wezterm-native/README.md) may affect
  terminal/UI latency and non-tmux backend choices.
