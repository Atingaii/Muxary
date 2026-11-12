# Phase 7 ProjectView Recent Jobs Helper

Date: 2026-06-15

## Landed

- Added Rust helper capability `project_view.recent_jobs`.
- Added Python required wrapper `read_project_view_recent_jobs_required`.
- Added `JobStore.list_project_view_recent_jobs`.
- Wired ProjectView `_recent_jobs` to use the narrow summary method when
  available.
- Added focused tests for:
  - helper capability payload,
  - required no-fallback wrapper behavior,
  - JobStore summary behavior,
  - ProjectView integration without Python tail fallback,
  - Phase 7 benchmark output.

## Boundary

Rust owns only the bounded scan of per-agent job JSONL files:

- strict JSONL row parsing,
- comms-status filtering,
- latest row per `job_id`,
- global sort by `updated_at`,
- result truncation,
- returning comms-visible job fields.

Python still owns:

- active and queued jobs,
- business status and status label,
- reply delivery folding,
- recoverability,
- final ProjectView response shape.

## Performance

Benchmark:

```text
python dev_tools/perf_phase7_project_view_recent_jobs_helper.py \
  --agents 128 --rows-per-agent 2000 --tail 128 --result-limit 64 --iterations 8
```

Result:

- Python p50 `228.253 ms`, p95 `288.065 ms`.
- Rust helper p50 `138.873 ms`, p95 `155.577 ms`.
- p50 speedup `1.644x`.
- p95 reduction `46.0%`.
- Parity matched.
- Required helper path has no Python fallback.
- Default remains disabled pending per-helper default-enable review.

## Verification

- `python -m pytest -q test/test_rust_helpers_project_view.py test/test_v2_job_store.py test/test_ccbd_project_view.py test/test_perf_phase7_project_view_recent_jobs_helper.py`
  - `81 passed`
- Combined helper/source focused suite:
  - `163 passed`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `16 passed`
- `tools/ccb-rs-helper/target/release/ccb-rs-helper --capabilities`
  includes `project_view.recent_jobs`.
- Full source gate:
  - `python -m pytest -q test/ -m "not provider_blackbox"`
  - `2762 passed, 2 skipped, 21 deselected`

## Decision

Use the narrow ProjectView recent-job summary helper for the sidebar/comms hot
path instead of full strict JobRecord tailing. The full JobRecord strict JSONL
helper remains useful as a correctness contract but should not be the default
hot path because Phase 6 showed it is slower than Python.
