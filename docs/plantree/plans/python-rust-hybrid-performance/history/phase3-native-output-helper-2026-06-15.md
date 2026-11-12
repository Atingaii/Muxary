# Phase 3 Native Output Helper Evidence

Date: 2026-06-15

## Artifact

- Python wrapper: `lib/rust_helpers_native_output.py`
- Production optional hook: `lib/provider_backends/native_cli_support/execution.py`
- Rust helper capability: `tools/ccb-rs-helper/src/main.rs`
- Focused tests: `test/test_rust_helpers_native_output.py`
- Benchmark runner: `dev_tools/perf_phase3_native_output_helper.py`
- Benchmark result:
  `dev_tools/perf_results/python_rust_phase3_native_output_helper.json`

## Behavior

- `CCB_RUST_NATIVE_OUTPUT` is scoped to native provider JSONL observation.
- Unset or `0` keeps the existing Python observer path.
- `1` or `auto` allows the production `observe_jsonl_output` entrypoint to use
  the Rust helper and still fall back through the wrapper if the helper is
  missing, crashes, times out, returns invalid JSON, or returns an invalid
  payload shape.
- Provider policy, terminal decisions, process management, and provider-specific
  Pi observation remain in Python.
- No Python fallback was removed in this phase.

## Benchmark

Command:

```bash
python dev_tools/perf_phase3_native_output_helper.py --iterations 8 --rows 50000
```

Result:

- Python native-output observation p50: 639.651 ms; p95: 724.931 ms.
- Rust helper observation p50: 139.684 ms; p95: 167.100 ms.
- p50 speedup: 4.579x.
- Reply chars: 580064.
- Integration gate recorded `meets_2x_speedup: true`.
- Production path wired behind flag: `CCB_RUST_NATIVE_OUTPUT=1|auto`.

## Verification

```bash
python -m pytest -q test/test_rust_helpers_native_output.py test/test_native_cli_provider_execution.py test/test_rust_helpers_jsonl.py test/test_rust_helpers.py test/test_perf_phase0_baseline.py
python -m py_compile lib/provider_backends/native_cli_support/execution.py lib/rust_helpers_native_output.py test/test_rust_helpers_native_output.py dev_tools/perf_phase3_native_output_helper.py
cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check
cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities
printf '%s' '{"schema_version":1,"capability":"native.output.observe","payload":{"path":"/tmp/ccb-phase3-missing.jsonl"}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml
python dev_tools/perf_phase3_native_output_helper.py --iterations 8 --rows 50000
cargo clean --manifest-path tools/ccb-rs-helper/Cargo.toml
```

Observed source-checkout results:

- Python focused/provider regression: 54 passed.
- Rust helper tests: 7 passed.
- Helper capability smoke includes `contract.echo`, `jsonl.tail`, and
  `native.output.observe`.

## Integration Notes

- Default runtime behavior remains Python because `CCB_RUST_NATIVE_OUTPUT` is
  unset by default.
- Fallback removal remains blocked until all low/medium-risk replacements have
  parity, regression, and performance evidence.
