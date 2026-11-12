# Fallback Readiness Regression

Date: 2026-06-15

## Verification

- Focused helper/source suite:
  - `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py`
  - `136 passed`
- py_compile:
  - `lib/rust_helpers.py`
  - `lib/rust_helpers_jsonl.py`
  - `lib/rust_helpers_native_output.py`
  - `lib/rust_helpers_storage.py`
  - `lib/rust_helpers_project_view.py`
  - production hook modules and benchmark scripts
- Rust helper:
  - `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
  - `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `11 passed`
- Helper CLI smoke:
  - `--capabilities` returned `contract.echo`, `jsonl.tail`,
    `native.output.observe`, `storage.scan.inventory`, and
    `project_view.tmux.parse`
  - `jsonl.tail` missing-file request returned ok with empty rows
  - `native.output.observe` missing-file request returned ok with empty
    observation
  - `storage.scan.inventory` missing-root request returned ok with empty
    payload
  - `project_view.tmux.parse` sample request returned focus/window/sidebar facts
- Full source gate:
  - `python -m pytest -q test/ -m "not provider_blackbox"`
  - `2736 passed, 2 skipped, 21 deselected`

## Fallback Readiness

Do not remove all Python fallbacks in this checkpoint.

Reasons:

- `jsonl.tail` currently has tolerant log-reader semantics: malformed rows and
  non-object rows are skipped.
- `storage.JsonlStore.read_tail` has strict store semantics: malformed JSON or
  non-object rows raise `ValueError`.
- A global JSONL production replacement would silently change behavior unless a
  strict helper contract is added and covered.
- `ccb-rs-helper` is not yet guaranteed as a mandatory release/install artifact
  on every supported platform.

Safe next step:

- Add a strict JSONL tail helper contract or a separate production-specific
  capability before wiring `JsonlStore`.
- Add release packaging checks for `ccb-rs-helper`.
- Revisit fallback removal per helper path after those contracts are proven.
