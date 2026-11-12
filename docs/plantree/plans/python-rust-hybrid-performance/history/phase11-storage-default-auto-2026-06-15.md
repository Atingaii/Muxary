# Phase 11 Storage Inventory Default Auto

Date: 2026-06-15

## Landed

- Changed storage inventory default behavior to `auto`.
- Preserved explicit controls:
  - `CCB_RUST_STORAGE_SCAN=0` forces Python inventory.
  - `CCB_RUST_STORAGE_SCAN=1|auto` attempts Rust and falls back to Python.
  - `CCB_RUST_STORAGE_SCAN=required` raises on helper missing/crash/bad
    payload.
  - `CCB_RUST_HELPERS=0` still disables default-auto helper attempts when no
    storage-specific override is set.
- Updated `storage_classification.service` so production storage summaries use
  default-auto inventory while Python still owns classification, cleanup
  authority, redaction, and report shape.
- Updated Phase 4 benchmark metadata to record `production_path_wired=true`
  and `default_enabled=true`.

## Performance

Command:

```bash
python dev_tools/perf_phase4_storage_scan_helper.py \
  --files 400 --agents 12 --iterations 6 --no-build-helper \
  --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper
```

Result:

- Python p50: `13.309 ms`, p95: `17.182 ms`.
- Rust p50: `8.649 ms`, p95: `11.209 ms`.
- p50 speedup: `1.539x`.
- Parity: matched.
- Gate: `meets_1_5x_speedup=true`, `production_path_wired=true`,
  `default_enabled=true`.

## Verification

Passed:

- `python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py test/test_perf_phase4_storage_scan_helper.py`
  - `27 passed`
- `python -m py_compile lib/rust_helpers_storage.py lib/storage_classification/service.py test/test_rust_helpers_storage.py test/test_storage_classification.py dev_tools/perf_phase4_storage_scan_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `19 passed`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py test/test_perf_phase8_job_summary_projection_helper.py`
  - `197 passed`

Full non-provider-blackbox gate was not rerun for this Step 2 checkpoint. The
latest full-gate attempt in this dirty checkout failed in unrelated update/rich
CLI tests, and the user explicitly accepted those failures as out-of-scope for
continuing Step 2.

## Decision

Storage inventory is now a default-auto Rust helper path. Proceed to Step 3
only as a new opt-in `storage.scan.summary`-style contract that reduces stdout
JSON/object volume and keeps destructive cleanup decisions in Python.
