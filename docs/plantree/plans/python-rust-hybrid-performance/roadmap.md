# Roadmap

Date: 2026-06-16

## Done

- Confirmed existing Rust release surface exists through `ccb-agent-sidebar`.
- Identified initial performance candidates from current Python modules and
  metrics fields.
- Received `coworker` review for the low-risk execution plan; accepted the
  sequencing constraint to run Phase 0 before helper skeleton work.
- Added the Phase 0 Python-only benchmark harness and wrote the first baseline
  result artifact:
  `dev_tools/perf_results/python_rust_phase0_baseline.json`.
- Captured p50/p95 measurements for ProjectView build, JSONL tail/find,
  storage classification scan, native provider output parse, cleanup-style
  process inspection, and helper subprocess startup; Rust toolchain probes
  report `cargo` and `rustup` available in this environment.
- Accepted Phase 0 as sufficient to start Phase 1 contract-only work; helper
  startup overhead requires batch-aware helper design and disabled-by-default
  rollout.
- Worker2 produced a Phase 1 contract-only helper skeleton with a standalone
  `ccb-rs-helper` crate, disabled-by-default Python invocation wrapper, and
  focused fallback tests. Evidence:
  `history/phase1-helper-contract-2026-06-15.md`.
- Main integrated the Phase 1 skeleton, preserved the disabled-by-default
  boundary, fixed stderr diagnostic double-redaction, regenerated the Cargo
  lock file for the current registry state, and verified Python/Rust focused
  tests plus helper CLI smoke.
- Coworker accepted the Phase 0/1 gate and allowed a narrow Phase 2 JSONL helper
  slice, provided `CCB_RUST_JSONL` scoping is locked before dispatch. Evidence:
  `history/coworker-phase1-gate-2026-06-15.md`.
- Main locked `CCB_RUST_JSONL` as a JSONL-wrapper/call-site flag that overrides
  global `CCB_RUST_HELPERS` only for JSONL helper calls.
- Main integrated the optional Phase 2 JSONL helper wrapper and Rust
  `jsonl.tail` capability without wiring production callers. Main benchmark:
  Python fallback batch tail p50 `227.153 ms`, Rust release helper p50
  `66.353 ms`, p50 speedup `3.423x`. Evidence:
  `history/phase2-jsonl-helper-2026-06-15.md`.
- Main integrated the Phase 3 native provider output parser helper behind
  `CCB_RUST_NATIVE_OUTPUT=1|auto`. Default behavior remains Python. Main
  benchmark: Python p50 `639.651 ms`, Rust helper p50 `139.684 ms`, p50
  speedup `4.579x`. Evidence:
  `history/phase3-native-output-helper-2026-06-15.md`.
- Main integrated the Phase 4 storage scan inventory helper behind
  `CCB_RUST_STORAGE_SCAN=1|auto`. Default behavior remains Python. Main
  benchmark: Python p50 `1235.509 ms`, Rust helper-enabled summary p50
  `799.036 ms`, p50 speedup `1.546x`, parity matched. Evidence:
  `history/phase4-storage-scan-helper-2026-06-15.md`.
- Main integrated the Phase 5 ProjectView/tmux parser helper behind
  `CCB_RUST_PROJECT_VIEW=1|auto`. Default behavior remains Python. Main
  benchmark: Python p95 `262.514 ms`, Rust helper p95 `199.966 ms`, p95
  reduction `23.8%`, parity matched. Evidence:
  `history/phase5-project-view-tmux-helper-2026-06-15.md`.
- Main added strict JSONL required-mode support through `jsonl.tail.strict`,
  `JsonlStore`, and `JobStore.list_agent_tails_batch`. Required mode removes
  Python fallback, but remains opt-in.
- Main added release/install packaging for `ccb-rs-helper` and verified a Linux
  release preview artifact smoke. Evidence:
  `history/fallback-readiness-packaging-phase6-2026-06-15.md`.
- Main reran performance and regression gates before Phase 7. Phase 2/3/4 met
  their configured improvement gates, while Phase 6 strict full JobRecord
  tailing did not. Later Phase 5 retest supersedes the earlier ProjectView/tmux
  improvement claim for default-enable decisions.
- Main added the narrower Phase 7 ProjectView recent-job summary helper. It
  avoids full JobRecord transfer/reconstruction and meets the configured gates:
  p50 speedup `1.644x`, p95 reduction `46.0%`, parity matched. Evidence:
  `history/phase7-project-view-recent-jobs-2026-06-15.md`.
- Main added `required` no-fallback mode to native output, storage inventory,
  and ProjectView/tmux parser wrappers, and fixed the production entrypoints so
  `required` does not silently fall back to Python. Existing `1|auto` modes
  remain fallback-tolerant.
- Latest regression gate passed after required-mode changes:
  `2775 passed, 2 skipped, 21 deselected`.
- Pre-adaptive performance retest split default candidates from experimental paths:
  native output `4.777x` p50, storage inventory `1.956x` p50, and ProjectView
  recent jobs `1.511x` p50 / `28.7%` p95 reduction are positive; ProjectView
  tmux parser and full JobRecord strict JSONL remain non-default because their
  helper subprocess boundary is currently slower than Python.
- Main added helper capability probe caching, reducing repeated helper calls
  after the first call in a Python process from capability probe + request to
  request only.
- Main added Phase 8 `jobs.tail.summary` as a broader per-agent JobRecord
  summary projection helper. It preserves required no-fallback semantics and
  parity, but misses the performance gate because returning 16k summary rows
  over stdout JSON is still too much cross-process output. Evidence:
  `history/phase8-job-summary-projection-2026-06-15.md`.
- Main captured the follow-up fetch design after Phase 8: fixed `tail=128`
  should not be the production query shape. ProjectView/comms should move to
  global top-N recent queries, adaptive per-agent scan budgets, delta refresh,
  counts/buckets, and detail-on-demand. Design:
  `topics/job-fetch-design.md`.
- Main landed the first fetch-design slice: `jobs.query.recent`, adaptive
  `JobStore` deepening, and ProjectView/comms initial scan budgets. Adaptive
  10-agent benchmark shows Python p50 `2.042 ms` versus Rust helper p50
  `2.987 ms`, so this slice improves the default Python path and keeps Rust
  non-default for ProjectView recent jobs. Evidence:
  `history/phase9-adaptive-job-query-2026-06-15.md`.
- Main default-enabled native output observation as auto. Phase 3 retest:
  Python p50 `634.495 ms`, Rust p50 `140.237 ms`, p50 speedup `4.524x`.
  Evidence: `history/phase10-native-output-default-auto-2026-06-15.md`.
- Main default-enabled storage inventory scan as auto. Phase 4 retest:
  Python p50 `13.309 ms`, Rust p50 `8.649 ms`, p50 speedup `1.539x`, parity
  matched. Evidence:
  `history/phase11-storage-default-auto-2026-06-15.md`.
- Main added the Phase 12 compact storage summary helper behind explicit
  `CCB_RUST_STORAGE_SUMMARY=1|auto|required`. Benchmark result:
  inventory-plus-Python compact summary p50 `7.605 ms`, Rust helper p50
  `3.658 ms`, p50 speedup `2.079x`, parity matched. It remains opt-in with
  `default_enabled=false`. Evidence:
  `history/phase12-storage-summary-helper-2026-06-16.md`.

## In Progress

- Sequential default-enable follow-up:
  native output and storage inventory are complete; new summary/query
  contracts only proceed after each step records regression and benchmark
  evidence.
  Gate file: `topics/sequential-optimization-gates.md`.
- Step 3 storage summary contract is landed as an opt-in helper. The next gate
  is review plus broader fixture evidence before any default-auto decision.

## Next

1. Review and approval phase.
   - Done for initial plan.
   - Phase 0/1 coworker gate passed.
   - Main reviewed and integrated worker3 artifact as an optional helper slice.
   - Native provider output parser is wired only behind
     `CCB_RUST_NATIVE_OUTPUT=1|auto|required`.
   - Next gate: review before any default enablement or fallback removal.

2. Baseline measurement phase.
   - Initial generated-fixture baseline is complete. Remaining work is to
     review whether additional real-project or larger synthetic fixtures are
     needed before selecting the first helper target.

3. Rust helper framework.
   - Skeleton completed as a standalone `tools/ccb-rs-helper` crate.
   - Keep the JSON input/output envelope, stable error envelope, version probe,
     capability probe, timeout behavior, and `CCB_RUST_HELPERS=0/1/auto`
     fallback contract stable.
   - Cargo workspace/build packaging remains deferred until a real helper slice
     proves the helper boundary is worth shipping.

4. First helper: bounded JSONL tail/query.
   - Optional wrapper/helper slice is integrated.
   - Batch `jsonl.tail` requests are supported in one helper invocation.
   - Golden-file style tests, crash/timeout fallback tests, and a large fixture
     benchmark passed in the source checkout.
   - Production caller selection and wiring remain deferred to the next review
     gate.

5. Second helper: native provider output parser.
   - Done behind `CCB_RUST_NATIVE_OUTPUT`.
   - Provider policy and terminal decisions remain in Python.
   - Parity, provider regression, Rust tests, CLI smoke, and benchmark evidence
     passed.

6. Third helper: storage classification scan.
   - Done as a low-risk inventory helper and now default-auto.
   - Rust owns directory walking, lstat size capture, symlink-as-entry traversal
     behavior, and deduped inventory output.
   - Python still owns storage class interpretation, cleanup authority, report
     shape, and redaction.
   - Compact summary generation is now available behind
     `CCB_RUST_STORAGE_SUMMARY`, but remains opt-in pending review and broader
     fixture evidence.
   - Full Rust cleanup authority remains deferred unless a separate review gate
     approves the larger semantic move.

7. Fourth helper: ProjectView/tmux collection.
   - Done as a parser helper.
   - Python still executes tmux through the namespace backend and owns
     namespace/lifecycle authority.
   - Rust parses focus, window, and sidebar facts from large tmux stdout
     payloads.

8. Final low/medium-risk fallback removal gate.
   - Required no-fallback mode is available for the helper-backed production
     paths, but global default fallback removal is not approved yet.
   - Remove Python fallback by default only for helper-backed paths whose Rust
     replacement has parity tests, production-path regression coverage,
     performance evidence, matching semantics, and guaranteed release/install
     packaging.
   - Current default-auto paths: native provider output parser and storage
     inventory scan.
   - Storage compact summary is opt-in despite positive synthetic evidence;
     it needs a default-enable review before joining the default-auto set.
   - Keep ProjectView/tmux parser and full JobRecord strict JSONL as opt-in
     required/experimental paths until their negative subprocess-boundary
     benchmarks are solved.
   - Keep broad per-agent job-summary projection non-default until output is
     reduced by result limits/filtering/aggregation or moved to a persistent
     helper/PyO3 boundary.
   - Replace fixed `tail=128` ProjectView/comms budgets with the
     `topics/job-fetch-design.md` plan before treating any broad job-summary
     helper as production-ready. The first adaptive recent-list slice is
     landed; Rust remains non-default for this path because Python is now
     faster under the reduced query shape.
   - JSONL tolerant batch tail remains a benchmarked helper slice, not a
     production default path.
   - `process tree cleanup` remains deferred because it is medium-high risk and
     touches process signaling authority.
   - Current blocker: default enablement still needs per-helper decisions.
   - Evidence:
     `history/fallback-readiness-regression-2026-06-15.md` and
     `history/fallback-readiness-packaging-phase6-2026-06-15.md` and
     `history/phase7-project-view-recent-jobs-2026-06-15.md` and
     `history/required-mode-fallback-removal-2026-06-15.md` and
     `history/phase8-job-summary-projection-2026-06-15.md` and
     `history/phase9-adaptive-job-query-2026-06-15.md` and
     `history/phase12-storage-summary-helper-2026-06-16.md`.

9. Deferred medium-high helper: process tree and cleanup.
   - Move pid-tree discovery, zombie handling, and group termination support
     into Rust helper code after lifecycle tests cover parity.
   - Requires a separate review gate before any process-signaling behavior is
     implemented or enabled.

## Deferred

- PyO3 in-process extension modules.
- Rust sidecar service for cached ProjectView/index state.
- Rust `ccbd` rewrite.
- Rust provider implementation for every provider backend.
- Python fallback removal for any path without parity, regression, and
  performance evidence.
