# Phase 9 Adaptive Job Query

Date: 2026-06-15

## Landed

- Added Rust helper capability `jobs.query.recent`.
- Added Python wrapper `read_jobs_query_recent_required`.
- Added adaptive ProjectView/comms scan budgets:
  - normal max per agent: `64`;
  - initial per-agent scan: `ceil(result_limit / agent_count) * 2`, clamped
    to `8..32`.
- Updated `JobStore.list_project_view_recent_jobs`:
  - old single-pass behavior remains when no initial budget is passed;
  - Python fallback now deepens from initial budget to max only when the
    result set is too small;
  - required helper path calls `jobs.query.recent` when adaptive budgets are
    provided.
- Kept `project_view.recent_jobs` for backward-compatible fixed-budget helper
  calls.

## Performance

Adaptive 10-agent benchmark:

```bash
python dev_tools/perf_phase7_project_view_recent_jobs_helper.py \
  --agents 10 --rows-per-agent 2000 --tail 64 --initial-tail 14 \
  --result-limit 64 --iterations 10
```

Result:

- Python adaptive ProjectView recent jobs p50: `2.042 ms`, p95: `2.331 ms`.
- Rust `jobs.query.recent` p50: `2.987 ms`, p95: `5.036 ms`.
- p50 speedup: `0.684x`.
- Parity matched.

Interpretation:

- The main win came from reducing the fetch shape, not from moving this small
  UI query into Rust.
- `jobs.query.recent` is a useful required/experimental contract and keeps the
  subprocess output bounded, but it should not be default-enabled for
  ProjectView/comms at this scale.
- ProjectView recent jobs should be removed from the immediate default-enable
  candidate list unless a persistent helper, PyO3 boundary, or heavier real
  fixture changes the measurement.

## Verification

- `python -m py_compile lib/rust_helpers_project_view.py lib/jobs/store.py lib/ccbd/project_view/service.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_ccbd_project_view.py`
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
- `cargo run --quiet --manifest-path tools/ccb-rs-helper/Cargo.toml -- --capabilities`
- `python -m pytest -q test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_ccbd_project_view.py test/test_perf_phase7_project_view_recent_jobs_helper.py`
- `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_rust_helpers_native_output.py test/test_rust_helpers_storage.py test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_native_cli_provider_execution.py test/test_storage_classification.py test/test_ccbd_project_view.py test/test_perf_phase0_baseline.py test/test_perf_phase4_storage_scan_helper.py test/test_perf_phase5_project_view_tmux_helper.py test/test_perf_phase6_jsonl_store_strict_helper.py test/test_perf_phase7_project_view_recent_jobs_helper.py test/test_perf_phase8_job_summary_projection_helper.py`

Focused helper/source regression result: `189 passed`.
