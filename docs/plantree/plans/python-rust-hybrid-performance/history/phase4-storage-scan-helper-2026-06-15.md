# Phase 4 Storage Scan Helper Evidence

Date: 2026-06-15

## Landed Scope

- Added `storage.scan.inventory` to `tools/ccb-rs-helper`.
- Added `lib/rust_helpers_storage.py` with `CCB_RUST_STORAGE_SCAN=1|auto`.
- Wired `storage_classification.summarize_storage(...)` to use the helper only
  when `CCB_RUST_STORAGE_SCAN` is enabled.
- Kept default behavior on the Python path.
- Kept storage classification, cleanup authority, redaction policy, report
  shape, and destructive decisions in Python.
- Added `dev_tools/perf_phase4_storage_scan_helper.py` and result artifact
  `dev_tools/perf_results/python_rust_phase4_storage_scan_helper.json`.

## Verification

- `python -m pytest -q test/test_rust_helpers_storage.py test/test_storage_classification.py test/test_perf_phase4_storage_scan_helper.py`
  - `19 passed`
- `python -m py_compile lib/rust_helpers_storage.py lib/storage_classification/service.py dev_tools/perf_phase4_storage_scan_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `9 passed`

## Benchmark

Command:

```bash
python dev_tools/perf_phase4_storage_scan_helper.py --files 60000 --agents 12 --iterations 8 --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper
```

Result:

- Python storage summary p50: `1235.509 ms`
- Rust helper-enabled storage summary p50: `799.036 ms`
- Speedup p50: `1.546x`
- Total records: `60051`
- Parity: matched
- Production hook: wired behind `CCB_RUST_STORAGE_SCAN=1|auto`
- Default enabled: false

## Notes

This is an inventory helper, not a full Rust storage classifier. The helper
captures traversal facts and sizes; Python still interprets storage class and
cleanup safety. That keeps the slice low risk while reducing repeated Python
filesystem work on large provider homes.
