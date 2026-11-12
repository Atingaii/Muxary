# Implementation Status

Date: 2026-06-16

## Current Phase

Sequential default-enable gate: Phase 12 compact storage summary is implemented
and wired behind explicit `CCB_RUST_STORAGE_SUMMARY=1|auto|required`. It has
focused regression and benchmark evidence, but remains opt-in while the next
review decides whether to default-auto it or reduce the contract further.

Landing scope is positive-only for this commit: native output, storage
inventory, and compact storage summary helper paths may land; JSONL/job and
ProjectView helper experiments remain documented evidence only and should not
enter the code commit.

Lifecycle-level startup, high-load, and pane-interaction optimization is now
tracked by
[../ccb-runtime-performance/README.md](../ccb-runtime-performance/README.md);
use that plan to decide whether a Rust helper result is large enough to matter
for total-system CPU or latency.

## Active TODO

- Review Phase 12 storage summary evidence before any default enablement. The
  400-file synthetic fixture is positive, but larger or real-project fixtures
  should confirm stdout/object-volume behavior before flipping defaults.
- Keep native output and storage inventory as the only default-auto Rust helper
  paths from this sequence so far.
- Decide the next storage shape: default-auto review for compact summary, or a
  narrower count/bucket/detail-on-demand contract if real fixtures show the
  current summary payload is still too broad.
- Keep `project_view.tmux.parse` and full JobRecord `jsonl.tail.strict` out of
  default hot paths until their current negative benchmarks are solved.
- Treat ProjectView/comms recent jobs as adaptive Python by default for now:
  `jobs.query.recent` exists, but the adaptive 10-agent benchmark made Python
  faster than the subprocess helper.
- Continue the query-shaped job design after the recent-list slice: delta
  refresh, counts/buckets, and detail-on-demand. See
  `topics/job-fetch-design.md`.
- Treat broad per-agent job-summary projection as non-default and diagnostic
  only; it should not become the ProjectView/comms fetch contract.
- Keep optional `1|auto` behavior as fallback-tolerant; use `required` only for
  paths where helper availability is intentionally enforced.

## Done This Phase

- Initial low-risk plan reviewed by `coworker`
  (`job_38f7d1a16a12`).
- Accepted coworker blockers into the plan:
  fixture/result path, Rust toolchain probe, subprocess overhead probe, and
  baseline fallback contract.
- Cleared `worker1` context before dispatch:
  `clear_status: ok`, `cleared_count: 1`.
- Submitted Phase 0 measurement-only work to `worker1`:
  `job_40bcd34d4343`.
- Added `dev_tools/perf_phase0_baseline.py` and focused tests.
- Ran the benchmark and wrote
  `dev_tools/perf_results/python_rust_phase0_baseline.json`.
- Recorded evidence in
  `history/phase0-baseline-2026-06-15.md`.
- Main-agent review accepted Phase 0 for Phase 1 readiness:
  focused tests and py_compile passed; no Rust/helper workspace or runtime
  behavior replacement was introduced.
- Phase 0 evidence shows helper process startup proxy p95 around 31 ms, while
  several current Python hot-path probes are sub-ms. Phase 1 contract must
  support batched calls and fallback-first behavior rather than assuming
  per-call helper execution is always faster.
- Cleared `worker2` context before dispatch:
  `clear_status: ok`, `cleared_count: 1`.
- Submitted Phase 1 helper contract skeleton work to `worker2`:
  `job_e1c423a48f1d`.
- Worker2 produced a disabled-by-default helper contract skeleton:
  `tools/ccb-rs-helper/`, `lib/rust_helpers.py`, and focused fallback tests.
  Evidence is recorded in
  `history/phase1-helper-contract-2026-06-15.md`.
- Main integrated the Phase 1 skeleton into the source checkout.
- Main fixed one diagnostic detail before acceptance: already-redacted stderr
  markers are preserved instead of being redacted a second time.
- Regenerated `tools/ccb-rs-helper/Cargo.lock` in the current environment
  after Cargo reported a registry checksum mismatch for the worker-generated
  lock file.
- Submitted Phase 0/1 evidence to `coworker` for review:
  `job_5ad7f77497ae`.
- `coworker` accepted Phase 0/1 as sufficient to start a narrow JSONL helper
  slice. Evidence:
  `history/coworker-phase1-gate-2026-06-15.md`.
- Main resolved the required worker3 scoping issue: `CCB_RUST_JSONL` belongs in
  the JSONL-specific wrapper/call site and overrides `CCB_RUST_HELPERS` only for
  JSONL helper calls.
- Cleared `worker3` context before dispatch:
  `clear_status: ok`, `cleared_count: 1`.
- Submitted Phase 2 JSONL helper slice to `worker3`:
  `job_382c6f5477c1`.
- Worker3 returned the Phase 2 JSONL helper artifact. Main integrated only the
  Phase 2 slice files into the current source checkout:
  `lib/rust_helpers_jsonl.py`, `test/test_rust_helpers_jsonl.py`,
  `tools/ccb-rs-helper/src/main.rs`, `dev_tools/perf_phase2_jsonl_helper.py`,
  and `history/phase2-jsonl-helper-2026-06-15.md`.
- Main regenerated the Phase 2 benchmark result in the source checkout:
  `dev_tools/perf_results/python_rust_phase2_jsonl_helper.json`.
- Phase 2 benchmark result: Python fallback batch tail p50 `227.153 ms`, Rust
  release helper batch tail p50 `66.353 ms`, p50 speedup `3.423x`, production
  path wired `false`.
- Main integrated Phase 3 native provider JSONL output observation helper:
  `lib/rust_helpers_native_output.py`, `native.output.observe` in
  `tools/ccb-rs-helper`, and optional production hook in
  `provider_backends.native_cli_support.observe_jsonl_output`.
- Phase 3 benchmark result: Python native-output observation p50 `639.651 ms`,
  Rust helper p50 `139.684 ms`, p50 speedup `4.579x`.
- Phase 3 production hook is feature-gated by
  `CCB_RUST_NATIVE_OUTPUT=1|auto`; default behavior remains Python.
- Evidence is recorded in
  `history/phase3-native-output-helper-2026-06-15.md`.
- Main integrated the Phase 4 storage scan inventory helper behind
  `CCB_RUST_STORAGE_SCAN=1|auto`. Default behavior remains Python.
- Phase 4 Rust capability: `storage.scan.inventory`; it owns directory
  walking, lstat size capture, symlink-as-entry traversal behavior, and deduped
  inventory output. Python still owns storage classification, cleanup meaning,
  redaction policy, report shape, and destructive decisions.
- Phase 4 benchmark result: Python storage summary p50 `1235.509 ms`, Rust
  helper-enabled summary p50 `799.036 ms`, p50 speedup `1.546x`, parity
  matched. Evidence is recorded in
  `history/phase4-storage-scan-helper-2026-06-15.md`.
- Main integrated the Phase 5 ProjectView/tmux parser helper behind
  `CCB_RUST_PROJECT_VIEW=1|auto`. Default behavior remains Python.
- Phase 5 Rust capability: `project_view.tmux.parse`; Python still executes
  tmux through the namespace backend and owns namespace/lifecycle authority and
  final ProjectView shape.
- Phase 5 benchmark result: Python tmux parser p95 `262.514 ms`, Rust helper
  p95 `199.966 ms`, p95 reduction `23.8%`, parity matched. Evidence is
  recorded in `history/phase5-project-view-tmux-helper-2026-06-15.md`.
- Combined helper/source regression passed. Evidence:
  `history/fallback-readiness-regression-2026-06-15.md`.
- Main added the strict `jsonl.tail.strict` capability, `JsonlStore` required
  helper path, and `JobStore.list_agent_tails_batch` required helper path. In
  this mode missing/broken helper raises; there is no Python fallback.
- Main added release/install packaging for `ccb-rs-helper`: build wrapper,
  source wrapper, `install.sh` build/install path, release artifact build path,
  Linux/macOS release workflow verification, and focused install/release tests.
- Linux release preview artifact smoke passed for both `bin/ccb-agent-sidebar`
  and `bin/ccb-rs-helper`.
- Phase 6 strict JobStore JSONL benchmark result: Python p50 `181.583 ms`,
  Rust helper p50 `453.064 ms`, p50 speedup `0.401x`, parity matched, required
  helper path has no Python fallback, default remains disabled. Evidence is
  recorded in
  `history/fallback-readiness-packaging-phase6-2026-06-15.md`.
- Main integrated the Phase 7 ProjectView recent-job summary helper:
  `project_view.recent_jobs` in `ccb-rs-helper`,
  `read_project_view_recent_jobs_required`, `JobStore.list_project_view_recent_jobs`,
  and `_recent_jobs` production wiring. It is a narrower contract than full
  JobRecord tailing and only returns comms-visible fields; Python still owns
  business status, reply delivery folding, recoverability, and final view shape.
- Phase 7 benchmark result: Python p50 `228.253 ms`, Rust helper p50
  `138.873 ms`, p50 speedup `1.644x`, p95 reduction `46.0%`, parity matched,
  required helper path has no Python fallback, default remains disabled.
  Evidence is recorded in
  `history/phase7-project-view-recent-jobs-2026-06-15.md`.
- Pre-Phase9 performance retest results:
  - Phase 2 tolerant JSONL helper p50 speedup `4.094x`, production path still
    not wired by design.
  - Phase 3 native output helper p50 speedup `4.777x`.
  - Phase 4 storage scan helper p50 speedup `1.956x`.
  - Phase 5 ProjectView/tmux parser retest is negative when measured as a
    helper subprocess boundary: `0.069x` p50 on a small payload and `0.507x`
    p50 on a large payload. Keep it available but non-default.
  - Phase 6 full JobRecord strict helper remains negative: `0.599x` p50 on the
    latest smaller retest.
  - Phase 7 ProjectView recent jobs p50 speedup `1.511x`, p95 reduction
    `28.7%`, parity matched.
- Main added `required` no-fallback mode to native output, storage inventory,
  and ProjectView/tmux parser wrappers. Production entrypoints now respect
  `required`: helper missing, helper crash, bad payload, or import failure
  raises instead of silently falling back to Python.
- Focused required-mode regression passed:
  `102 passed` for native output, storage, ProjectView helper wrappers and
  production entrypoints.
- Combined helper/source focused regression passed: `176 passed`.
- Rust helper crate gate passed: `16 passed`.
- Full non-provider-blackbox source gate passed: `2775 passed, 2 skipped, 21
  deselected`.
- Main added helper capability probe caching in `lib/rust_helpers.py`. The
  cache stores successful `--capabilities` envelopes per helper path, mtime,
  and size, reducing repeated helper calls from two subprocess launches to one
  after the first call in a Python process.
- Main added Phase 8 `jobs.tail.summary`, a required no-fallback helper path
  for per-agent JobRecord tail summary projection, plus
  `JobStore.list_agent_tail_summaries_batch`.
- Phase 8 benchmark result: Python p50 `213.634 ms`, Rust helper p50
  `369.602 ms`, p50 speedup `0.578x`, parity matched, required helper path has
  no Python fallback, default remains disabled. Evidence is recorded in
  `history/phase8-job-summary-projection-2026-06-15.md`.
- Typical-scale retest with 10 agents and tail 128 still keeps broad summary
  projection non-default: Phase 8 p50 `16.762 ms` Python versus `31.545 ms`
  helper (`0.531x`). Phase 7 remains positive at the same scale: p50
  `18.625 ms` Python versus `12.674 ms` helper, p95 reduction `37.7%`.
- Capability caching improved small helper overhead but did not change the
  default-enable decision for ProjectView/tmux parsing: latest small-payload
  retest remains negative, p50 `0.155 ms` Python versus `1.089 ms` helper.
- Phase 7 recent jobs remains positive after cache changes: p50 speedup
  `1.564x`, p95 reduction `34.2%`.
- Combined helper/source focused regression passed: `184 passed`.
- Rust helper crate gate passed after Phase 8: `17 passed`.
- Full non-provider-blackbox source gate passed after Phase 8:
  `2784 passed, 2 skipped, 21 deselected`.
- Main added Phase 9 adaptive ProjectView/comms recent-job querying:
  `jobs.query.recent`, Python wrapper support, adaptive `JobStore`
  deepening, ProjectView initial scan budgets, and Phase 7 benchmark support
  for `--initial-tail`.
- Adaptive 10-agent recent-job benchmark: Python p50 `2.042 ms`, Rust
  `jobs.query.recent` p50 `2.987 ms`, parity matched, p50 speedup `0.684x`.
  This removes ProjectView recent jobs from the immediate default-enable
  candidate list. Evidence:
  `history/phase9-adaptive-job-query-2026-06-15.md`.
- Focused helper/source regression passed after Phase 9: `189 passed`.
- Rust helper crate gate passed after Phase 9: `19 passed`.
- Main default-enabled native output observation as auto with explicit
  force-Python and required controls preserved. Phase 3 benchmark remains
  positive: Python p50 `634.495 ms`, Rust p50 `140.237 ms`, p50 speedup
  `4.524x`. Focused helper/source regression passed: `193 passed`. Evidence:
  `history/phase10-native-output-default-auto-2026-06-15.md`.
- Full non-provider-blackbox gate is not green in the current dirty checkout:
  `20 failed, 2775 passed, 2 skipped, 21 deselected`. Failures are in
  update/rich CLI tests outside this native-output step.
- Main default-enabled storage inventory scan as auto with explicit
  force-Python and required controls preserved. Phase 4 benchmark remains
  positive: Python p50 `13.309 ms`, Rust p50 `8.649 ms`, p50 speedup
  `1.539x`, parity matched. Focused storage regression passed: `27 passed`;
  combined helper/source focused regression passed: `197 passed`. Evidence:
  `history/phase11-storage-default-auto-2026-06-15.md`.
- Main added Phase 12 compact storage summary as an opt-in helper path:
  `storage.scan.summary` in `ccb-rs-helper`, `scan_storage_summary`, and
  production wiring through `summarize_storage_compact`.
- Phase 12 controls: `CCB_RUST_STORAGE_SUMMARY=1|auto` attempts Rust with
  Python fallback, `required` raises instead of falling back, and default
  behavior remains Python.
- Phase 12 benchmark result: inventory-plus-Python compact summary p50
  `7.605 ms`, Rust compact summary helper p50 `3.658 ms`, p50 speedup
  `2.079x`, parity matched, production path wired `true`, default enabled
  `false`. Evidence:
  `history/phase12-storage-summary-helper-2026-06-16.md`.
- Phase 12 focused regression passed: storage helper/classification/perf tests
  `31 passed`; broader helper/project-view/job-store regression `147 passed`;
  install/release packaging tests `43 passed`; runtime source gate slice
  `246 passed`; isolated `ccb_test doctor storage` passed with and without
  `CCB_RUST_STORAGE_SUMMARY=1`.

## Blockers

- Full JSONL fallback removal remains blocked by performance, not semantics:
  `jsonl.tail.strict` matches strict `JsonlStore` behavior and has a required
  no-fallback path, but full JobRecord batch tailing is slower than Python due
  to stdout JSON transfer and Python dataclass reconstruction.
- Broad per-agent summary projection is also blocked by output volume:
  returning `agents * tail` summary rows over stdout JSON is still slower than
  Python even without full JobRecord dataclass reconstruction. Future Rust wins
  need user-facing query contracts rather than fixed `tail=128`: top-N recent
  lists, adaptive per-agent scan budgets, delta cursors, counts/buckets, and
  detail-on-demand.
- ProjectView/comms recent-job default enablement is blocked by the improved
  Python baseline: once adaptive budgets reduce the query to tens/low hundreds
  of rows, subprocess Rust is slower than Python for the normal 10-agent UI
  refresh fixture.
- Storage compact summary default enablement is not approved yet. The new
  helper is parity-positive on a synthetic fixture, but remains opt-in until a
  review gate checks broader fixtures and confirms the compact payload is the
  right production contract.
- Global default fallback removal remains blocked until each helper path has a
  reviewed default-enable decision. Required-mode fallback removal is now
  available for native output, storage inventory, ProjectView/tmux parsing,
  full strict JSONL tailing, and ProjectView recent jobs, but not all are
  performance-positive enough to become defaults.
- Full non-provider-blackbox gate is not a Step 2 blocker in the current dirty
  checkout because the user explicitly accepted the unrelated update/rich CLI
  failures as out-of-scope for continuing storage default-auto work.

## Next Commit Target

Commit helper packaging, strict/required no-fallback coverage, adaptive
ProjectView recent-job querying, storage default-auto, the opt-in storage
summary helper, latest performance evidence, and the default-enable decision
notes.

## Last Verified Commands

- `ccb clear worker1` completed successfully.
- `python -m pytest -q test/test_perf_phase0_baseline.py`
- `python -m py_compile dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py`
- `ccb clear worker2` completed successfully.
- `python dev_tools/perf_phase0_baseline.py --iterations 10 --rows 2000 --agents 6 --processes 80`
- `python -m py_compile dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py`
- `python -m pytest -q test/test_rust_helpers.py test/test_perf_phase0_baseline.py`
- `python -m py_compile lib/rust_helpers.py test/test_rust_helpers.py dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --version`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- `printf '%s' '{"schema_version":1,"capability":"contract.echo","payload":{"ignored":true}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python -m pytest -q test/test_rust_helpers_jsonl.py test/test_rust_helpers.py test/test_perf_phase0_baseline.py`
- `python -m py_compile lib/rust_helpers_jsonl.py test/test_rust_helpers_jsonl.py dev_tools/perf_phase2_jsonl_helper.py lib/rust_helpers.py test/test_rust_helpers.py dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- `printf '%s' '{"schema_version":1,"capability":"jsonl.tail","payload":{"requests":[{"id":"missing","path":"/tmp/ccb-phase2-missing.jsonl","n":5}]}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python dev_tools/perf_phase2_jsonl_helper.py --iterations 8 --rows 50000 --files 4 --tail 128`
- `cargo clean --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python -m pytest -q test/test_rust_helpers_native_output.py test/test_native_cli_provider_execution.py test/test_rust_helpers_jsonl.py test/test_rust_helpers.py test/test_perf_phase0_baseline.py`
- `python -m py_compile lib/provider_backends/native_cli_support/execution.py lib/rust_helpers_native_output.py test/test_rust_helpers_native_output.py dev_tools/perf_phase3_native_output_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- `printf '%s' '{"schema_version":1,"capability":"native.output.observe","payload":{"path":"/tmp/ccb-phase3-missing.jsonl"}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python dev_tools/perf_phase3_native_output_helper.py --iterations 8 --rows 50000`
- `cargo clean --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py test/test_perf_phase4_storage_scan_helper.py`
- `python -m py_compile lib/rust_helpers_storage.py lib/storage_classification/service.py dev_tools/perf_phase4_storage_scan_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python dev_tools/perf_phase4_storage_scan_helper.py --files 60000 --agents 12 --iterations 8 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python -m pytest -q test/test_rust_helpers_project_view.py test/test_ccbd_project_view.py test/test_perf_phase5_project_view_tmux_helper.py`
- `python -m py_compile lib/rust_helpers_project_view.py lib/ccbd/project_view/service.py dev_tools/perf_phase5_project_view_tmux_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python dev_tools/perf_phase5_project_view_tmux_helper.py --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py`
- `python -m py_compile lib/rust_helpers.py lib/rust_helpers_jsonl.py lib/rust_helpers_native_output.py lib/rust_helpers_storage.py lib/rust_helpers_project_view.py lib/provider_backends/native_cli_support/execution.py lib/storage_classification/service.py lib/ccbd/project_view/service.py dev_tools/perf_phase0_baseline.py dev_tools/perf_phase2_jsonl_helper.py dev_tools/perf_phase3_native_output_helper.py dev_tools/perf_phase4_storage_scan_helper.py dev_tools/perf_phase5_project_view_tmux_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- helper CLI smoke for `jsonl.tail`, `native.output.observe`,
  `storage.scan.inventory`, and `project_view.tmux.parse`
- `python -m pytest -q test/ -m "not provider_blackbox"`
- `cargo clean --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python -m pytest -q test/test_install_script_sidebar.py test/test_build_linux_release_script.py`
- `bash -n install.sh bin/build-ccb-agent-sidebar bin/build-ccb-rs-helper bin/ccb-agent-sidebar bin/ccb-rs-helper`
- `python scripts/build_linux_release.py --allow-dirty --output-dir /tmp/ccb-release-preview-rs-helper`
- release preview smoke: extracted `/tmp/ccb-release-preview-rs-helper/ccb-linux-x86_64.tar.gz`,
  verified executable `bin/ccb-agent-sidebar`, executable `bin/ccb-rs-helper`,
  and `ccb-rs-helper --capabilities` containing `jsonl.tail.strict`
- `python dev_tools/perf_phase2_jsonl_helper.py --iterations 8 --rows 50000 --files 4 --tail 128 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python dev_tools/perf_phase3_native_output_helper.py --iterations 8 --rows 50000 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python dev_tools/perf_phase4_storage_scan_helper.py --files 60000 --agents 12 --iterations 8 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python dev_tools/perf_phase5_project_view_tmux_helper.py --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python dev_tools/perf_phase6_jsonl_store_strict_helper.py --agents 128 --rows-per-agent 2000 --tail 128 --iterations 8 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
- `python -m pytest -q test/ -m "not provider_blackbox"` (`2754 passed, 2 skipped, 21 deselected`)
- `python -m py_compile` for touched helper, packaging, benchmark, and test modules
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `python -m pytest -q test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_ccbd_project_view.py test/test_perf_phase7_project_view_recent_jobs_helper.py`
- `python dev_tools/perf_phase7_project_view_recent_jobs_helper.py --agents 128 --rows-per-agent 2000 --tail 128 --result-limit 64 --iterations 8`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py`
- `python -m pytest -q test/ -m "not provider_blackbox"` (`2762 passed, 2 skipped, 21 deselected`)
- `python -m pytest -q test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_storage_classification.py test/test_ccbd_project_view.py`
  (`102 passed`)
- `python -m py_compile lib/rust_helpers_native_output.py lib/rust_helpers_storage.py lib/rust_helpers_project_view.py lib/provider_backends/native_cli_support/execution.py lib/storage_classification/service.py lib/ccbd/project_view/service.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_storage_classification.py test/test_ccbd_project_view.py`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py`
  (`176 passed`)
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml` (`16 passed`)
- `python dev_tools/perf_phase2_jsonl_helper.py --iterations 8`
- `python dev_tools/perf_phase3_native_output_helper.py --iterations 8`
- `python dev_tools/perf_phase4_storage_scan_helper.py --agents 12 --files 400 --iterations 6`
- `python dev_tools/perf_phase5_project_view_tmux_helper.py --windows 96 --panes 96 --iterations 10`
- `python dev_tools/perf_phase5_project_view_tmux_helper.py --windows 4096 --panes 8192 --iterations 6`
- `python dev_tools/perf_phase6_jsonl_store_strict_helper.py --agents 32 --rows-per-agent 800 --tail 64 --iterations 4`
- `python dev_tools/perf_phase7_project_view_recent_jobs_helper.py --agents 128 --rows-per-agent 2000 --tail 128 --result-limit 64 --iterations 8`
- `python -m pytest -q test/ -m "not provider_blackbox"` (`2775 passed, 2 skipped, 21 deselected`)
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_v2_job_store.py test/test_perf_phase8_job_summary_projection_helper.py`
  (`44 passed`)
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml` (`17 passed`)
- `python dev_tools/perf_phase8_job_summary_projection_helper.py --agents 128 --rows-per-agent 2000 --tail 128 --iterations 8`
- `python dev_tools/perf_phase6_jsonl_store_strict_helper.py --agents 32 --rows-per-agent 800 --tail 64 --iterations 4`
- `python dev_tools/perf_phase5_project_view_tmux_helper.py --windows 96 --panes 96 --iterations 10`
- `python dev_tools/perf_phase7_project_view_recent_jobs_helper.py --agents 128 --rows-per-agent 2000 --tail 128 --result-limit 64 --iterations 8`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py test/test_perf_phase8_job_summary_projection_helper.py`
  (`184 passed`)
- `python -m pytest -q test/ -m "not provider_blackbox"` (`2784 passed, 2 skipped, 21 deselected`)
- `python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py test/test_perf_phase4_storage_scan_helper.py`
  (`27 passed`)
- `python -m py_compile lib/rust_helpers_storage.py lib/storage_classification/service.py test/test_rust_helpers_storage.py test/test_storage_classification.py dev_tools/perf_phase4_storage_scan_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml` (`19 passed`)
- `python dev_tools/perf_phase4_storage_scan_helper.py --files 400 --agents 12 --iterations 6 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
  (`1.539x` p50 speedup, parity matched)
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py test/test_perf_phase8_job_summary_projection_helper.py`
  (`197 passed`)
- `PYTHONPATH=lib python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py`
  (`29 passed`)
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml` (`20 passed`)
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- `bin/build-ccb-rs-helper && bin/ccb-rs-helper --capabilities`
- `PYTHONPATH=lib python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_project_view.py test/test_rust_helpers_storage.py test/test_v2_job_store.py test/test_ccbd_project_view.py`
  (`147 passed`)
- `PYTHONPATH=lib python -m pytest -q test/test_build_linux_release_script.py test/test_install_script_sidebar.py`
  (`43 passed`)
- From `/home/bfly/yunwei/test_ccb2` with isolated source home:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose`
- `PYTHONPATH=lib python -m pytest -q test/test_v2_phase2_entrypoint.py test/test_v2_cli_router.py test/test_cli_tools_workbench.py test/test_runtime_env_control_plane.py test/test_v2_runtime_launch.py`
  (`246 passed`)
- From `/home/bfly/yunwei/test_ccb2` with isolated source home:
  `/home/bfly/yunwei/ccb_source/ccb_test doctor storage`
- From `/home/bfly/yunwei/test_ccb2` with isolated source home and
  `CCB_RUST_STORAGE_SUMMARY=1`:
  `/home/bfly/yunwei/ccb_source/ccb_test doctor storage`
- `PYTHONPATH=lib python -m pytest -q test/test_perf_phase12_storage_summary_helper.py`
  (`2 passed`)
- `PYTHONPATH=lib python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py test/test_perf_phase12_storage_summary_helper.py`
  (`31 passed`)
- `PYTHONPATH=lib python dev_tools/perf_phase12_storage_summary_helper.py --files 400 --agents 12 --iterations 6 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper`
  (`2.079x` p50 speedup, parity matched)

## Handoff Notes

The Phase 0 harness is measurement-only: no Rust code, no helper workspace, no
runtime behavior replacement, and generated fixtures only. The current result
uses temporary fixtures, not the active source checkout `.ccb/agents` state.

For Phase 2, do not wire helpers into ProjectView, storage, provider parsing,
process cleanup, startup, or `ccbd` lifecycle paths. The next candidate should
be a narrow JSONL helper slice with golden-file equivalence, Python fallback,
and helpers still disabled by default.

The `worker3` scope is intentionally not a production replacement. The JSONL
wrapper can expose helper-enabled behavior for tests and benchmarks, but
existing runtime callers must remain on the Python path until a later review
gate.

The worker3 workspace was stale and had a Phase 0 test import issue there; the
same combined focused suite passed in the source checkout after integration.

For Phase 4, Rust owns only inventory generation. Python still owns cleanup
authority, classification/report shape, redaction, and any decision about what
is safe to delete. Full Rust rule matching remains outside the accepted
low-risk slice unless a separate review gate approves it.

Fallback removal target: optional helper modes (`1|auto`) remain
fallback-tolerant. The no-fallback contract is now expressed through
per-helper `required` modes and is verified for native output, storage
inventory, ProjectView/tmux parsing, strict JSONL tailing, and ProjectView
recent jobs.

Current fallback-removal finding: do not delete all Python fallbacks or flip a
global default yet. Native output, storage inventory, and ProjectView recent
jobs have positive current evidence. Full JobRecord strict tailing and
ProjectView/tmux parser subprocess calls are currently slower than Python at
the latest benchmark scales, so keep them required/experimental rather than
default-enabled. Process cleanup remains outside this gate because it is
medium-high risk.
