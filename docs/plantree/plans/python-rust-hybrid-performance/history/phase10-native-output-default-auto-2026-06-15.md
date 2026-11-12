# Phase 10 Native Output Default Auto

Date: 2026-06-15

## Landed

- Changed native output observation default behavior to `auto`.
- Preserved explicit controls:
  - `CCB_RUST_NATIVE_OUTPUT=0` forces Python fallback.
  - `CCB_RUST_NATIVE_OUTPUT=1|auto` attempts Rust and falls back to Python.
  - `CCB_RUST_NATIVE_OUTPUT=required` raises on helper missing/crash/bad
    payload.
  - `CCB_RUST_HELPERS=0` still disables default-auto helper attempts when no
    native-output-specific override is set.
- Updated production `observe_jsonl_output` to use the default-auto behavior.
- Updated Phase 3 benchmark metadata to record `production_path_wired=true`,
  `default_enabled=true`, and required-mode fallback removal.

## Performance

Command:

```bash
python dev_tools/perf_phase3_native_output_helper.py \
  --iterations 8 --rows 50000 --no-build-helper \
  --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper
```

Result:

- Python p50: `634.495 ms`, p95: `652.365 ms`.
- Rust p50: `140.237 ms`, p95: `151.770 ms`.
- p50 speedup: `4.524x`.
- Gate: `meets_2x_speedup=true`, `production_path_wired=true`,
  `default_enabled=true`.

## Verification

Passed:

- `python -m py_compile lib/rust_helpers_native_output.py lib/provider_backends/native_cli_support/execution.py test/test_rust_helpers_native_output.py`
- `python -m pytest -q test/test_rust_helpers_native_output.py test/test_native_cli_provider_execution.py`
  - `45 passed`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `19 passed`
- `python -m py_compile dev_tools/perf_phase3_native_output_helper.py`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py test/test_perf_phase8_job_summary_projection_helper.py`
  - `193 passed`
- `git diff --check` for touched native-output/perf/plan-tree files.

Blocked full gate:

- `python -m pytest -q test/ -m "not provider_blackbox"` failed with
  `20 failed, 2775 passed, 2 skipped, 21 deselected`.
- Failures were in currently dirty update/rich CLI surfaces outside this
  native-output step:
  - `test/test_cli_management_update.py`
  - `test/test_cli_tools_workbench.py`
  - `test/test_v2_cli_router.py`
  - related modules include `lib/cli/management_runtime/commands_runtime/update.py`
    and `lib/cli/entrypoint_runtime.py`

## Decision

Do not proceed to Step 2 storage default-auto until the full non-provider
blackbox gate is green or the unrelated update/rich failures are explicitly
accepted as out-of-scope for this optimization sequence.
