# Phase 12 Storage Summary Helper

Date: 2026-06-16

## Landed

- Added `storage.scan.summary` to `ccb-rs-helper`.
- Added `scan_storage_summary` in `lib/rust_helpers_storage.py`.
- Wired `summarize_storage_compact` to use the helper only when
  `CCB_RUST_STORAGE_SUMMARY=1|auto|required`.
- Preserved the storage boundary: Rust may build the compact summary payload,
  but Python still owns destructive cleanup decisions and the default
  `doctor storage` behavior.
- Added `dev_tools/perf_phase12_storage_summary_helper.py` and focused tests
  for its machine-readable result artifact.

## Controls

- Default remains disabled. Without `CCB_RUST_STORAGE_SUMMARY`, compact storage
  summaries use the existing Python path.
- `CCB_RUST_STORAGE_SUMMARY=1|auto` attempts Rust and falls back to Python if
  the helper is unavailable or invalid.
- `CCB_RUST_STORAGE_SUMMARY=required` raises on helper missing/crash/bad
  payload instead of silently falling back.

## Performance

Command:

```bash
PYTHONPATH=lib python dev_tools/perf_phase12_storage_summary_helper.py \
  --files 400 --agents 12 --iterations 6 --no-build-helper \
  --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper
```

Result:

- Inventory-plus-Python compact summary p50: `7.605 ms`, p95: `10.777 ms`.
- Rust compact summary helper p50: `3.658 ms`, p95: `4.831 ms`.
- p50 speedup: `2.079x`.
- Parity: matched.
- Gate: `meets_1_2x_speedup=true`, `production_path_wired=true`,
  `default_enabled=false`.

Result artifact:

- `dev_tools/perf_results/python_rust_phase12_storage_summary_helper.json`

## Verification

Passed:

- `PYTHONPATH=lib python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py`
  - `29 passed`
- `PYTHONPATH=lib python -m pytest -q test/test_perf_phase12_storage_summary_helper.py`
  - `2 passed`
- `PYTHONPATH=lib python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py test/test_perf_phase12_storage_summary_helper.py`
  - `31 passed`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `20 passed`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- `bin/build-ccb-rs-helper && bin/ccb-rs-helper --capabilities`
- `PYTHONPATH=lib python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_project_view.py test/test_rust_helpers_storage.py test/test_v2_job_store.py test/test_ccbd_project_view.py`
  - `147 passed`
- `PYTHONPATH=lib python -m pytest -q test/test_build_linux_release_script.py test/test_install_script_sidebar.py`
  - `43 passed`
- From `/home/bfly/yunwei/test_ccb2` with isolated source home:
  `HOME=/home/bfly/yunwei/test_ccb2/source_home CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home /home/bfly/yunwei/ccb_source/ccb_test --diagnose`
- From `/home/bfly/yunwei/test_ccb2` with isolated source home:
  `PYTHONPATH=lib python -m pytest -q test/test_v2_phase2_entrypoint.py test/test_v2_cli_router.py test/test_cli_tools_workbench.py test/test_runtime_env_control_plane.py test/test_v2_runtime_launch.py`
  - `246 passed`
- From `/home/bfly/yunwei/test_ccb2` with isolated source home:
  `/home/bfly/yunwei/ccb_source/ccb_test doctor storage`
  - `storage_status: ok`
- From `/home/bfly/yunwei/test_ccb2` with isolated source home and
  `CCB_RUST_STORAGE_SUMMARY=1`:
  `/home/bfly/yunwei/ccb_source/ccb_test doctor storage`
  - compact output completed successfully.

## Decision

Keep `storage.scan.summary` opt-in for now. It has positive synthetic
performance and parity evidence, but default enablement should wait for review
and broader real-project or larger synthetic fixtures. Native output and
storage inventory remain the only default-auto helper paths from this sequence
so far.
