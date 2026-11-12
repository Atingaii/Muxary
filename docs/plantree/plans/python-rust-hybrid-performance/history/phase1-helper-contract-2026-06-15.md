# Phase 1 Helper Contract Evidence

Date: 2026-06-15

## Artifact

- Rust helper skeleton: `tools/ccb-rs-helper/`
- Python optional invocation wrapper: `lib/rust_helpers.py`
- Focused tests: `test/test_rust_helpers.py`
- Job: `job_e1c423a48f1d`

## Contract

- Helper binary name: `ccb-rs-helper`
- Schema version: `1`
- Implemented no-op capability: `contract.echo`
- CLI probes:
  - `--version`
  - `--capabilities`
  - stdin JSON request envelope for the no-op contract capability

## Fallback Behavior

- Helpers are disabled by default because an unset `CCB_RUST_HELPERS` falls
  back without discovery.
- `CCB_RUST_HELPERS=0` forces Python-only fallback.
- `CCB_RUST_HELPERS=auto` and `CCB_RUST_HELPERS=1` may attempt discovery, but
  missing helper, timeout, nonzero exit, invalid JSON, unknown schema, and
  unsupported capability return fallback output plus one structured diagnostic.
- Diagnostics contain helper name, failure kind, elapsed milliseconds, and a
  redacted stderr presence/length marker. Request payload, raw stderr, and
  provider transcript content are not included.

## Verification

```bash
python -m pytest -q test/test_rust_helpers.py
python -m py_compile lib/rust_helpers.py test/test_rust_helpers.py
cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check
cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --version
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities
printf '%s' '{"schema_version":1,"capability":"contract.echo","payload":{"ignored":true}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml
```

Main integration verification:

```bash
python -m pytest -q test/test_rust_helpers.py test/test_perf_phase0_baseline.py
python -m py_compile lib/rust_helpers.py test/test_rust_helpers.py dev_tools/perf_phase0_baseline.py test/test_perf_phase0_baseline.py
cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check
cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --version
cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities
printf '%s' '{"schema_version":1,"capability":"contract.echo","payload":{"ignored":true}}' | cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml
```

## Notes

- No ProjectView, JSONL, storage, provider parsing, process cleanup, startup,
  or `ccbd` runtime path was wired to the helper.
- Cargo is not required for source installs by this skeleton; the helper is
  source-only unless explicitly built.
- The verification built and ran a debug helper through Cargo, but no release
  helper binary was produced or checked into `bin/`.
- Main regenerated `Cargo.lock` after the worker-generated lock file failed
  current-environment checksum validation for `syn`.
- Main fixed diagnostic double-redaction so an already-redacted stderr marker is
  preserved instead of being redacted again.
