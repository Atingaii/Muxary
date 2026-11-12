# Phase 2 JSONL Helper Evidence

Date: 2026-06-15

## Artifact

- Job: `job_382c6f5477c1`
- Python wrapper: `lib/rust_helpers_jsonl.py`
- Rust helper capability: `tools/ccb-rs-helper/src/main.rs`
- Focused tests: `test/test_rust_helpers_jsonl.py`
- Benchmark runner: `dev_tools/perf_phase2_jsonl_helper.py`
- Benchmark result:
  `dev_tools/perf_results/python_rust_phase2_jsonl_helper.json`

## Behavior

- `CCB_RUST_JSONL` is scoped to the JSONL wrapper only.
- Unset or `0` maps to Python fallback without helper discovery.
- `1` or `auto` maps to `CCB_RUST_HELPERS` for the helper call only and still
  falls back on missing helper, timeout, crash, nonzero exit, invalid JSON,
  unknown schema, unsupported capability, or invalid helper payload shape.
- The wrapper does not mutate `os.environ`.
- Python fallback handles batch tail requests, missing files, `n=0`, empty
  lines, malformed rows, Unicode, large rows, and non-object row skips.
- Negative `n` raises `ValueError`.
- No ProjectView, storage classification, provider parsing, process cleanup,
  startup, `ccbd` lifecycle, or production JSONL caller path was wired.

## Benchmark

Command:

```bash
python dev_tools/perf_phase2_jsonl_helper.py --iterations 8 --rows 50000 --files 4 --tail 128
```

Result summary from worker3:

- Python fallback batch tail p50: 241.525 ms; p95: 268.528 ms.
- Rust release helper batch tail p50: 62.752 ms; p95: 72.926 ms.
- p50 speedup: 3.8489x.
- Rows returned per iteration: 512.
- Integration gate recorded `meets_2x_speedup: true`.
- Production path remains unwired: `production_path_wired: false`.

Main regenerated the benchmark result in the source checkout after integration.
Local source-checkout result:

- Python fallback batch tail p50: 227.153 ms; p95: 234.591 ms.
- Rust release helper batch tail p50: 66.353 ms; p95: 77.726 ms.
- p50 speedup: 3.4234x.
- Rows returned per iteration: 512.
- Integration gate recorded `meets_2x_speedup: true`.
- Production path remains unwired: `production_path_wired: false`.

## Verification

Worker3 passed:

```bash
python -m py_compile lib/rust_helpers_jsonl.py test/test_rust_helpers_jsonl.py dev_tools/perf_phase2_jsonl_helper.py lib/rust_helpers.py test/test_rust_helpers.py dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py
python -m pytest -q test/test_rust_helpers_jsonl.py test/test_rust_helpers.py
cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check
cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities
printf '%s' '{"schema_version":1,"capability":"jsonl.tail","payload":{"requests":[{"id":"missing","path":"/tmp/ccb-phase2-missing.jsonl","n":5}]}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml
python dev_tools/perf_phase2_jsonl_helper.py --iterations 8 --rows 50000 --files 4 --tail 128
cargo clean --manifest-path tools/ccb-rs-helper/Cargo.toml
```

Main source-checkout verification:

```bash
python -m pytest -q test/test_rust_helpers_jsonl.py test/test_rust_helpers.py test/test_perf_phase0_baseline.py
python -m py_compile lib/rust_helpers_jsonl.py test/test_rust_helpers_jsonl.py dev_tools/perf_phase2_jsonl_helper.py lib/rust_helpers.py test/test_rust_helpers.py dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py
cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check
cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities
printf '%s' '{"schema_version":1,"capability":"jsonl.tail","payload":{"requests":[{"id":"missing","path":"/tmp/ccb-phase2-missing.jsonl","n":5}]}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml
python dev_tools/perf_phase2_jsonl_helper.py --iterations 8 --rows 50000 --files 4 --tail 128
cargo clean --manifest-path tools/ccb-rs-helper/Cargo.toml
```

Validation caveat from worker3:

- `python -m pytest -q test/test_rust_helpers_jsonl.py test/test_rust_helpers.py test/test_perf_phase0_baseline.py`
  was blocked in the worker workspace because the copied Phase 0 harness expects
  `provider_backends.native_cli_support`, which exists in the newer source
  checkout but not that older worker branch.

## Integration Notes

- The slice is integration-ready for review as an optional helper wrapper, not
  as a production caller replacement.
- Before wiring any runtime caller, review the wrapper output contract and
  decide whether batch tail IDs should be caller-owned stable IDs or path-based
  defaults.
- Cargo build output was cleaned after validation.
