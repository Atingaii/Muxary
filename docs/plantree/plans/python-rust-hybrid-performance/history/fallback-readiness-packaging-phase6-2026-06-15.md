# Fallback Readiness Packaging And Phase 6 Checkpoint

Date: 2026-06-15

## Landed

- Added strict `jsonl.tail.strict` support in `ccb-rs-helper`.
- Added required/no-fallback Python wrappers for strict JSONL store reads.
- Wired `JsonlStore.read_tail` and `JobStore.list_agent_tails_batch` to use the
  required helper path when `CCB_RUST_JSONL_STORE=1|true|yes|on|required`.
- Added `ccb-rs-helper` packaging:
  - `bin/build-ccb-rs-helper`
  - `bin/ccb-rs-helper` source wrapper
  - `install.sh` build/install path
  - `scripts/build_release.py` release artifact build path
  - CI/release workflow verification for Linux/macOS artifacts
- Added focused tests for strict helper behavior, required no-fallback failure,
  install script handling, release builder handling, and Phase 6 benchmark
  output.

## Verification

- `python -m pytest -q test/test_install_script_sidebar.py test/test_build_linux_release_script.py`
  - `43 passed`
- `python -m pytest -q test/ -m "not provider_blackbox"`
  - `2754 passed, 2 skipped, 21 deselected`
- `python -m py_compile` for touched helper, packaging, benchmark, and test
  modules.
- `cargo fmt --manifest-path tools/ccb-rs-helper/Cargo.toml --check`
- `cargo test --manifest-path tools/ccb-rs-helper/Cargo.toml`
  - `14 passed`
- `python scripts/build_linux_release.py --allow-dirty --output-dir /tmp/ccb-release-preview-rs-helper`
- Extracted `/tmp/ccb-release-preview-rs-helper/ccb-linux-x86_64.tar.gz` and
  verified:
  - executable `bin/ccb-agent-sidebar`
  - executable `bin/ccb-rs-helper`
  - `ccb-rs-helper --capabilities` includes `jsonl.tail.strict`

## Performance Retest

- Phase 2 tolerant JSONL tail:
  - Python p50 `237.518 ms`
  - Rust p50 `67.027 ms`
  - p50 speedup `3.544x`
- Phase 3 native output:
  - Python p50 `659.587 ms`
  - Rust p50 `140.761 ms`
  - p50 speedup `4.686x`
- Phase 4 storage scan:
  - Python p50 `1209.606 ms`
  - Rust p50 `767.444 ms`
  - p50 speedup `1.576x`
- Phase 5 ProjectView/tmux parser:
  - Python p95 `249.045 ms`
  - Rust p95 `184.527 ms`
  - p95 reduction `25.9%`
- Phase 6 strict JobStore JSONL:
  - Python p50 `181.583 ms`
  - Rust p50 `453.064 ms`
  - p50 speedup `0.401x`
  - parity matched
  - required helper path has no Python fallback
  - default remains disabled

## Decision

Do not remove all Python fallbacks globally in this checkpoint.

The remaining blocker is not strict JSONL semantics or release packaging.
The blocker is that the strict full JobRecord helper path is slower than Python
for ProjectView-style batch tailing because it transfers full JSON rows over
stdout and reconstructs full Python records.

Safe next direction: design a narrower ProjectView recent-job summary helper
that returns only comms-visible fields, or introduce cached/sidecar indexing,
then re-run the performance gate before default enablement or fallback removal.
