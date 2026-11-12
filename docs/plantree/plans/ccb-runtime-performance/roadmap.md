# Roadmap

Date: 2026-07-17

## Done

- Captured a real lifecycle CPU profile from an isolated source runtime under
  `/home/bfly/yunwei/test_ccb2` using `/home/bfly/yunwei/ccb_source/ccb_test`.
  Evidence:
  [history/real-lifecycle-cpu-profile-2026-06-16.md](history/real-lifecycle-cpu-profile-2026-06-16.md).
- Confirmed the currently landed Rust helpers improve local paths but do not
  explain the dominant lifecycle CPU share in the sampled workload.
- Established the current optimization priority: shell/tmux/subprocess
  orchestration first, then provider lifecycle policy, then CCB core only if it
  remains above the agreed threshold after those reductions.
- Added a repeatable lifecycle profiling harness and reviewed it for
  source-runtime-safe invocation and project-scoped process attribution.
- Added a low-risk detached tmux prepare cache keyed by socket identity and
  environment fingerprint.
- Added a narrow project_focus fast path that queues sidebar refresh through
  project_view when available, while preserving synchronous refresh fallback.
- Fixed the pending sidebar-refresh crash exposed by that fast path by adding
  the missing project_view refresh metrics helper and regression coverage.
- Split the previous `shell-system` bucket with corrected project-scoped
  profiling. Evidence:
  [history/shell-system-bucket-split-2026-06-16.md](history/shell-system-bucket-split-2026-06-16.md).
  High-load submission CPU is dominated by `ask-cli-subprocess`; startup CPU is
  dominated by provider launch/mount, not tmux server work.
- Added a working-tree interactive-latency slice for sidebar clicks:
  `ccb __sidebar-click` can now focus through one daemon RPC
  (`project_sidebar_click`) instead of a CLI-side `project_view` request
  followed by a second focus request, with old-daemon fallback preserved.
- Added `dev_tools/perf_sidebar_click_latency.py` as a focused single-RPC
  latency probe for live daemon socket measurements.
- Fixed explicit multi-window startup binding so logical window and namespace
  epoch determine reuse while actual tmux window ids remain runtime facts.
- Enforced zero provider preparation for reuse and one preparation pass for
  launch/relaunch, including one Codex managed-home projection per launch.
- Added request-scoped tmux and Codex process snapshots, tmux pane-identity
  batching, unchanged-identity suppression, and scoped no-op persistence.
- Added persisted startup stage/per-agent timings and surfaced them through
  `doctor`.
- Validated a 5-window, 10-agent isolated source runtime: 20 warm starts had
  p50 about `0.555s`, p95 `0.63s`, 10/10 attaches, zero relaunches, and zero
  provider preparation.
- Added the Phase 0 working-tree startup harness with owner marker and lock,
  source/wrapper/fingerprint checks, official cold/reset/cleanup control-plane
  paths, immutable per-round report snapshots, native startup-run correlation,
  statistical summary, and fail-closed scenario labels.
- Split CLI, supervisor, and Agent runtime timings; added request-scoped tmux,
  subprocess, Provider preparation, atomic-write, and orphan-cleanup counters.
- Added a strict warm identity gate covering lease/generation, namespace,
  pane topology, runtime/session authority, PID start time, FIFO type, reuse
  actions, zero Provider preparation, zero launch stage, and stable double
  observation.
- Fixed three correctness defects exposed by the harness: legacy topology could
  prune the cmd root and overwrite sidebar placement, warm reuse toggled
  persisted `restored` health to `healthy`, and identical namespace state was
  rewritten.
- Added privacy-safe `/proc` CPU/RSS/process/I/O sampling tied to native startup
  run IDs plus a bounded two-clean-snapshot post-kill residue audit.  The latest
  smoke passed the resource gate with `1.375 ms` measured sampler/runner wall
  outside the command, while remaining explicitly non-formal.
- Added a source-wrapper/Python bootstrap trace and attributed `94.664%` of the
  latest measured external warm wall.  The dominant fixed startup slice is now
  measured as `211.349 ms` from `ccb.py` entry through eager imports.
- Added one-origin no-attach T0-T6 records with trace/run/generation
  correlation, fixed provenance, monotonic ordering, command-wall containment,
  requested/desired Agent scope checks, and explicit T5 non-applicability.
  The initial checkpoint honestly separated cold T1 as an observation upper
  bound; the later exact-T1 correction below replaced it only with fenced proof.
- Added the warm-only instrumentation A/B lane with a persisted seeded ABBA
  plan, adjacent same-generation control/treatment pairs, strict evidence
  separation, paired bootstrap interval, and fail-closed formal budget gate.
  The first external `1 + 2` smoke had two valid pairs and clean teardown; its
  point estimate was under budget but its interval upper bound was not, so it
  remains `smoke_only`.
- Closed the startup-intent/keeper-transaction stale-RMW race in the working
  tree with fresh-read short locking, warm no-op intent, spawn-before-unlock
  proof, and startup-id/generation-fenced finalization.  Deterministic POSIX
  process tests and a clean external cold-prime/warm smoke passed.
- Completed the frozen formal `3 + 20` instrumentation A/B run: `20/20` valid
  pairs, paired p50 `4.098 ms`, bootstrap 95% CI upper bound `8.676 ms`, and a
  `10 ms` budget.  The dedicated overhead gate passed with clean teardown.
- Closed the follow-up child-generation boundary: keeper-to-child
  `startup_id/generation`, exact lifecycle/lease claim and finalization fences,
  shared-lock stop/heartbeat/keeper/reload/namespace writes, strict readiness
  identity, timeout child-group reaping, and stale latest-report suppression.
  The repeated formal `3 + 20` A/B passed with paired p50 `1.911 ms`, CI upper
  `5.397 ms`, and `24/24` process-I/O-complete resource profiles.
- Closed the exact keeper T1 diagnostics boundary without another authority
  file or durable write.  Keeper samples immediately after the durable
  `phase=starting` commit and carries the one-shot value to child memory; exact
  projection requires startup/generation/lease and monotonic-order proof, while
  malformed or absent diagnostics fail open to an honest upper bound.
- Split repeated resource sampling into a terminal active seed and a cumulative
  cleanup identity set, added privacy-safe unresolved I/O cause attribution,
  and prioritized the short-lived foreground tree without extra procfs reads.
  The post-fix formal `3 + 20` A/B passed with `20/20` pairs, paired p50
  `-0.283 ms`, CI upper `7.868 ms`, exact-T1 readiness `24/24`, resource quality
  `24/24`, bounded warm vanished-PID observations, and clean teardown.
- Closed the strict mounted/self-ping boundary: socket replacement is
  ownership-safe and transactional, the normal accept loop serves fenced ping
  during runtime bootstrap, keeper cannot promote an interim child lease, and
  final `mounted/mounted` publication is child-owned and identity-fenced.  The
  retained keeper-promotion race was converted into a deterministic regression;
  the final external smoke completed with zero failures and clean teardown, and
  the post-closure formal `3 + 20` warm A/B passed the `10 ms` overhead gate.
  Evidence:
  [history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md](history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md).
- Closed the follow-up final-publication gap: durable `mounted/mounted` and
  normal-RPC gate opening are atomic at request dispatch; callback, stop, and
  worker failures remain fail-closed even after file replacement; queued
  mutations cannot run during shutdown; and same-process restart keeps the
  exact next generation.  The focused/expanded/restart-provider matrices pass
  `80/263/87`; the full suite has no new failure, 100 repeated success/failure
  publication races pass, and the final external smoke plus frozen A/B pass
  readiness, resource, overhead, and cleanup gates.
- Closed the S4 process-I/O observation race without adding privilege or value
  imputation.  The sampler opens a bounded, no-follow, close-on-exec I/O handle
  at first validated PID/start-ticks stat observation and reuses it through the
  zombie window.  Retained formal failures proved both the terminal and
  first-observation windows.  The final S4 `3 + 20` run passed process I/O
  `23/23`; the repeated warm A/B passed the `10 ms` overhead gate with CI upper
  `4.274 ms`.  TASKSTATS was rejected because unprivileged same-UID queries
  require `CAP_NET_ADMIN` on the validation host.  Evidence:
  [history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md](history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md).
- Replaced label-only scenario evidence with a durable before/ready/final
  SHA chain, exact run/reference rebinding, stable double-read authority,
  cold-residue and new-generation gates, orphan-attempt detection, and
  privacy-safe identity digests.  Deterministic startup/resource tests pass
  `114/114`; external S1, S4, and one-use S5a smoke artifacts pass with the
  required `same`, `changed`, and `created` identity relations and clean
  teardown.  Evidence:
  [history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md](history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md).
- Closed the serial S3 mixed-recovery smoke.  A retained external failure proved
  that requiring liveness in structural topology matching converted one dead
  exact-owned Agent pane into namespace recreation and healthy-peer relaunch.
  Structural ownership is now independent of live active/binding eligibility,
  so ordinary recovery preserves the daemon, generation, namespace, and peer
  while relaunching only the target.  The source-test constructor uses official
  single-Agent restart, an indexed release latch, supervision cursor, HMAC slot
  identities, and a SHA-bound restricted raw probe.  A follow-up review also
  excluded unknown current-epoch slots from active cleanup protection, reduced
  the fallback to one bounded candidate listing, and rejected caller-owned
  launch controls.  Focused tests pass `219/219`; final AQ passed at
  `665.070 ms`, prepare counts `1/0`, maximum
  concurrency 1, zero supervision recovery events, and clean teardown.  Evidence:
  [history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md](history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md).
- Closed the S0 CLI-only hot-path slice with an explicit no-startup-transaction
  contract.  The measured command is exactly `ccb_test --print-version`; it
  emits no startup id/trace, preserves one frozen daemon/namespace/runtime/
  report baseline, and observes exactly one newly created command-process
  identity in every sampled profile.  The count is explicitly a sampling lower
  bound; wrapper `exec`, early CLI return, and a separate Linux process-syscall
  trace with zero `fork`/`vfork`/`clone`/`clone3` support the no-subprocess boundary.  A
  retained smoke exposed and corrected a harness false negative for the product
  success health `restored`.  The final clean-HEAD `3 + 20` run passed `20/20`
  measured commands, `23/23` CLI resource/report checks, `24/24` scenario
  manifests, and clean preservation/teardown at p50/p95
  `286.132/298.046 ms`, below the S0 budget.  Evidence:
  [history/startup-phase0-cli-only-checkpoint-2026-07-17.md](history/startup-phase0-cli-only-checkpoint-2026-07-17.md).

## In Progress

- Complete Phase 0 readiness semantics with a separate interactive T5 lane;
  retain explicit projection/helper/
  process-snapshot zero counters and public redacted identity summaries.
- Fill S5b plus automated fresh-per-round S5a artifacts and
  cross-platform/slow-filesystem coverage before treating Phase 0 as complete;
  S0/S1/S3/S4/one-use-S5a construction smoke is closed, while S2 remains
  unavailable without an official daemon-replacement primitive.
- Extend the proven S3 serial compensation fence across the remaining fault
  matrix before any cold-launch concurrency experiment.
- Make sampled process-count completeness machine-readable and split the
  measured-profile resource gate from the all-profile audit.  Current S0 is not
  blocked because all `23/23` profiles passed, but future consumers must not
  infer event completeness from `created_process_instance_count` alone.

## Next

1. Automate fresh-per-round S5a and add cache/first-update S5b; keep S2
   unavailable until an official daemon-replacement primitive exists.
2. Complete the remaining serial fault/compensation cases using the S3 fence
   before evaluating launch concurrency.
3. Run macOS, WSL ext4, WSL mounted-drive, real Codex primary, and Claude
   cross-provider qualification.
4. Add measured, bounded provider-launch concurrency only after the serial
   authority stages are explicit and generation-fenced.
5. Evaluate foreground-first readiness as a separate opt-in policy after the
   eager path meets its performance and reliability gates.
6. Resume persistent/batched ask and interactive-latency work after the startup
   regression is isolated and accepted.

## Deferred

- Full CCB core rewrite or broad Rust migration.
- Provider CLI internal optimization.
- Default-enabling opt-in Rust storage summary without broader fixture evidence.
