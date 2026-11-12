# Phase 5 ProjectView/Tmux Helper Evidence

Date: 2026-06-15

## Landed Scope

- Added `project_view.tmux.parse` to `tools/ccb-rs-helper`.
- Added `lib/rust_helpers_project_view.py` with
  `CCB_RUST_PROJECT_VIEW=1|auto`.
- Wired `ccbd.project_view.service` to collect tmux stdout through the existing
  Python namespace backend, then parse via the helper only when enabled.
- Cached the combined focus/window/sidebar parse facts inside a single
  ProjectView build.
- Kept tmux execution, namespace interpretation, lifecycle authority, and final
  ProjectView payload shape in Python.
- Added `dev_tools/perf_phase5_project_view_tmux_helper.py` and result artifact
  `dev_tools/perf_results/python_rust_phase5_project_view_tmux_helper.json`.

## Verification

- `python -m pytest -q test/test_rust_helpers_project_view.py test/test_ccbd_project_view.py test/test_perf_phase5_project_view_tmux_helper.py`
  - `63 passed`
- `python -m py_compile lib/rust_helpers_project_view.py lib/ccbd/project_view/service.py dev_tools/perf_phase5_project_view_tmux_helper.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `11 passed`

## Benchmark

Command:

```bash
python dev_tools/perf_phase5_project_view_tmux_helper.py --no-build-helper --helper-bin tools/ccb-rs-helper/target/release/ccb-rs-helper
```

Result:

- Synthetic pane rows: `400000`
- Synthetic windows: `500`
- Python tmux parser p50: `251.885 ms`
- Rust helper tmux parser p50: `189.526 ms`
- Python tmux parser p95: `262.514 ms`
- Rust helper tmux parser p95: `199.966 ms`
- p50 speedup: `1.329x`
- p95 reduction: `23.8%`
- Parity: matched
- Production hook: wired behind `CCB_RUST_PROJECT_VIEW=1|auto`
- Default enabled: false

## Notes

The helper does not execute tmux. That is intentional: the Python namespace
backend remains the authority for socket/session selection and failure
handling. Rust only parses large stdout payloads into stable focus, window, and
sidebar facts.
