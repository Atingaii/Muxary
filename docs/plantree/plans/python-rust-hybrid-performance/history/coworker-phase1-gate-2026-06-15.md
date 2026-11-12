# Coworker Phase 1 Gate

Date: 2026-06-15

## Artifact

- Job: `job_5ad7f77497ae`
- Reply artifact:
  `.ccb/ccbd/artifacts/text/completion-reply/job_5ad7f77497ae-art_0733135765834a99.txt`

## Conclusion

`coworker` accepted the Phase 0 baseline and Phase 1 helper contract as
sufficient to start a narrow Phase 2 JSONL helper slice.

No release-blocking issue was identified.

## Required Scoping Fix Before Worker3

`coworker` flagged one worker3-scoping issue: the per-helper
`CCB_RUST_JSONL` feature flag location must be specified before dispatch so
worker3 does not invent a new contract.

Main-agent resolution:

- Keep `call_rust_helper_or_fallback` public API unchanged.
- Add the per-helper `CCB_RUST_JSONL` decision in a JSONL-specific Python
  wrapper or JSONL-specific call site.
- Treat `CCB_RUST_JSONL` as an override of `CCB_RUST_HELPERS` for JSONL calls:
  unset means disabled/default Python path; `0` forces Python; `1` or `auto`
  allows helper discovery and still falls back to Python on any helper failure.

## Worker3 Constraints

- Implement only a disabled-by-default JSONL helper slice.
- Prefer a new JSONL-specific Python wrapper such as
  `lib/rust_helpers_jsonl.py`.
- Add `jsonl.tail` capability to `tools/ccb-rs-helper`.
- Support batch requests in one helper invocation; do not design a per-row or
  per-line subprocess call path.
- Do not wire into ProjectView, storage classification, provider parsing,
  process cleanup, startup, or `ccbd` lifecycle paths.
- Do not modify job/event/submission record schemas.
- Preserve all Phase 0/1 tests.

## Follow-Up Notes

- `auto` vs `1` semantics can be documented in a later contract pass.
- Workspace/build packaging can remain deferred while there is only one helper
  crate.
- CI/macOS coverage and capabilities caching remain follow-up topics.
