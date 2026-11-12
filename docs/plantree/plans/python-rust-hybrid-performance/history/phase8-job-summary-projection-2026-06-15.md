# Phase 8 Job Summary Projection Helper

Date: 2026-06-15

## Landed

- Added Python-process capability probe caching in `lib/rust_helpers.py`.
  Successful `--capabilities` envelopes are cached by helper path, mtime, and
  size.
- Added Rust helper capability `jobs.tail.summary`.
- Added Python wrapper `read_job_tail_summaries_required`.
- Added `JobStore.list_agent_tail_summaries_batch`.
- Added focused tests and a benchmark harness:
  `dev_tools/perf_phase8_job_summary_projection_helper.py`.

## Boundary

Rust owns:

- strict JSONL tail over per-agent job files,
- validating each tail row is a `job_record`,
- projecting JobRecord rows into comms-style summary fields.

Python still owns:

- full `JobRecord` loading paths,
- status/business semantics,
- ProjectView final response shape,
- default-enable decisions.

## Performance

Benchmark:

```text
python dev_tools/perf_phase8_job_summary_projection_helper.py \
  --agents 128 --rows-per-agent 2000 --tail 128 --iterations 8
```

Result:

- Python p50 `213.634 ms`, p95 `231.314 ms`.
- Rust helper p50 `369.602 ms`, p95 `384.386 ms`.
- p50 speedup `0.578x`.
- p95 reduction `-66.2%`.
- Parity matched.
- Required helper path has no Python fallback.
- Default remains disabled.

## Related Retests

- Typical-scale retest with 10 agents:
  - Phase 8 broad job summary projection: p50 `16.762 ms` Python versus
    `31.545 ms` helper (`0.531x`).
  - Phase 6 full JobRecord strict helper: p50 `12.653 ms` Python versus
    `34.693 ms` helper (`0.365x`).
  - Phase 7 ProjectView recent jobs: p50 `18.625 ms` Python versus
    `12.674 ms` helper, p95 reduction `37.7%`.
- Full JobRecord strict helper remains negative:
  `python dev_tools/perf_phase6_jsonl_store_strict_helper.py --agents 32 --rows-per-agent 800 --tail 64 --iterations 4`
  produced p50 speedup `0.431x`.
- ProjectView/tmux parser remains negative despite capability caching:
  p50 `0.155 ms` Python versus `1.089 ms` helper on the small payload retest.
- ProjectView recent jobs remains positive:
  p50 speedup `1.564x`, p95 reduction `34.2%`.

## Verification

- Focused Python tests:
  - `python -m pytest -q test/test_rust_helpers.py test/test_rust_helpers_jsonl.py test/test_v2_job_store.py test/test_perf_phase8_job_summary_projection_helper.py`
  - `44 passed`
- Combined helper/source focused suite:
  - `184 passed`
- Rust helper crate:
  - `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `17 passed`
- Full source gate:
  - `python -m pytest -q test/ -m "not provider_blackbox"`
  - `2784 passed, 2 skipped, 21 deselected`

## Decision

Capability caching is accepted as a low-risk general helper optimization.
Broad per-agent summary projection is not accepted for default enablement:
projection alone does not solve subprocess/stdout overhead when the helper
returns thousands of rows. Future job-query work should narrow results before
serialization or use a lower-overhead boundary.
