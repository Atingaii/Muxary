# Required-Mode Fallback Removal Gate

Date: 2026-06-15

## Landed

- Added `required` mode to:
  - `CCB_RUST_NATIVE_OUTPUT`
  - `CCB_RUST_STORAGE_SCAN`
  - `CCB_RUST_PROJECT_VIEW`
- Production entrypoints now preserve required-mode semantics instead of
  catching helper errors and falling back to Python:
  - native provider JSONL observation,
  - storage classification inventory scan,
  - ProjectView tmux output parser.
- Existing `1|auto` behavior remains fallback-tolerant for rollout safety.
- Existing required no-fallback paths remain in place for:
  - `CCB_RUST_JSONL_STORE`
  - `CCB_RUST_PROJECT_VIEW_RECENT_JOBS`

## Current Default Candidates

Positive current benchmark evidence:

- Phase 3 native output helper: p50 speedup `4.777x`.
- Phase 4 storage scan helper: p50 speedup `1.956x`.
- Phase 7 ProjectView recent jobs: p50 speedup `1.511x`, p95 reduction
  `28.7%`.

Keep non-default for now:

- Phase 5 ProjectView/tmux parser: latest subprocess-boundary retest is slower
  than Python (`0.069x` p50 on small payload, `0.507x` p50 on large payload).
- Phase 6 full JobRecord strict JSONL: latest retest remains slower than Python
  (`0.599x` p50).
- Phase 2 tolerant JSONL tail: strong helper benchmark (`4.094x` p50), but no
  production caller is selected yet.

## Verification

- Focused required-mode regression:
  - `python -m pytest -q test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_storage_classification.py test/test_ccbd_project_view.py`
  - `102 passed`
- Combined helper/source regression:
  - `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py`
  - `176 passed`
- Rust helper crate:
  - `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
  - `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `16 passed`
- Full source gate:
  - `python -m pytest -q test/ -m "not provider_blackbox"`
  - `2775 passed, 2 skipped, 21 deselected`

## Decision

Required-mode fallback removal is complete for the current low/medium-risk
helper-backed paths. Default fallback removal is still a separate per-helper
decision. Do not flip a global helper requirement or remove Python
implementations from all paths in one change.
