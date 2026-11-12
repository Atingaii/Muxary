# Low Risk Execution Plan

Date: 2026-06-15

## Goal

Introduce Rust for performance without changing CCB's product semantics in the
early slices. The first implementation round must make measurement and fallback
stronger even if every Rust helper remains disabled by default.

## Safety Model

Every slice must preserve these invariants:

- Python remains control-plane authority.
- Rust helpers are optional acceleration paths, not required startup
  dependencies.
- Helper failure must degrade to the existing Python path.
- No helper may mutate `.ccb` authority files in the first round.
- No helper may delete files, signal processes, or decide provider completion
  terminal state until a later reviewed slice explicitly grants that authority.
- Benchmarks and parity tests must exist before any default enablement.

## Phase 0: Measurement Only

Owner target: `worker1`

Scope:

- Add a small benchmark harness that exercises current Python-only paths.
- Measure ProjectView build latency, queue/watch JSONL tail latency, storage
  classification scan time, native provider output parse time, and cleanup
  process-inspection time.
- Measure helper subprocess startup overhead with a harmless command so Phase 1
  can decide whether helper binaries are still appropriate for high-frequency
  paths.
- Probe Rust toolchain readiness with `cargo version` and `rustup show` when
  available; record missing tools as data, not as a benchmark failure.
- Use generated fixtures under `dev_tools/perf_fixtures/` or a temporary
  directory created by the benchmark runner. Do not read or write active
  `.ccb/agents` runtime state in this source checkout.
- Write a machine-readable Phase 0 result artifact to
  `dev_tools/perf_results/python_rust_phase0_baseline.json`.

Allowed files:

- `test/` benchmark-style tests or focused perf smoke utilities.
- `scripts/` or `dev_tools/` benchmark runner.
- Plan-tree evidence update only after results exist.

Not allowed:

- Adding Rust code.
- Changing runtime behavior.
- Changing provider completion logic.

Verification:

- Existing unit tests remain green for touched areas.
- Benchmark command prints machine-readable JSON with p50/p95 or comparable
  summary.
- Result JSON includes fixture root, result path, timestamp, Python version,
  platform, Rust toolchain probe, subprocess overhead, and measured hot paths.

Exit criteria:

- We know which first helper has the best measured payoff.

## Phase 1: Helper Contract And Packaging Skeleton

Owner target: `worker2`

Scope:

- Add a CCB-owned Rust helper workspace or extend the existing Rust helper
  build pattern.
- Implement a no-op helper contract with:
  - `--version`
  - `--capabilities`
  - JSON request envelope
  - JSON response envelope
  - schema version
  - nonzero exit/error envelope behavior
- Add Python helper discovery and fallback wrapper, disabled by default.
- Use the Phase 0 result to choose default timeout values and decide whether
  helper binary startup overhead is acceptable for the first helper target.

Baseline fallback contract:

- `CCB_RUST_HELPERS=0` must force Python-only behavior.
- `CCB_RUST_HELPERS=auto` may try helpers when present, but must fallback to
  Python on helper missing, nonzero exit, timeout, invalid JSON, unknown schema,
  or unsupported capability.
- `CCB_RUST_HELPERS=1` may surface helper failures in tests, but user-facing
  runtime paths should still preserve Python fallback unless the test explicitly
  asserts hard-helper failure.
- A successful fallback returns the Python result and records exactly one
  structured diagnostic breadcrumb containing helper name, failure kind, elapsed
  time, and stderr tail. It must not raise to the user when Python fallback
  succeeds.
- Fallback diagnostics must not write secrets or provider transcript content.

Allowed files:

- Rust helper workspace files.
- Python helper invocation wrapper.
- Release/build tests only for helper discovery and graceful fallback.

Not allowed:

- Replacing JSONL, ProjectView, storage, provider, or cleanup behavior.
- Making Cargo a required source install dependency.

Verification:

- Helper missing path falls back.
- Helper present path returns capabilities.
- Build/release tests either include the helper or clearly mark it optional.

Exit criteria:

- Future helpers can plug into one stable invocation contract.

## Phase 2: First Real Helper, JSONL Tail/Query

Owner target: `worker3`

Scope:

- Implement the first JSONL helper capability in the existing
  `tools/ccb-rs-helper` skeleton. Start with `jsonl.tail`; leave read-since and
  find-last for a later slice unless they are needed for local test structure.
- Add a JSONL-specific Python wrapper or call site, preferably
  `lib/rust_helpers_jsonl.py`, instead of changing the public
  `call_rust_helper_or_fallback` contract.
- Add golden fixtures for empty files, missing files, malformed rows, Unicode,
  large rows, rotated/truncated files, and predicate misses.
- Do not wire production callers in the worker3 slice. Expose helper-enabled
  behavior only through the JSONL wrapper tests and benchmark/evidence path.

Feature flag decision:

- `CCB_RUST_JSONL` is checked in the JSONL-specific wrapper or call site.
- Unset `CCB_RUST_JSONL` means disabled/default Python path.
- `CCB_RUST_JSONL=0` forces Python fallback.
- `CCB_RUST_JSONL=1` or `CCB_RUST_JSONL=auto` allows helper discovery and still
  falls back to Python on missing helper, timeout, crash, invalid JSON, unknown
  schema, or unsupported capability.
- `CCB_RUST_JSONL` overrides `CCB_RUST_HELPERS` only for JSONL helper calls.

Batching requirement:

- The helper payload must support multiple `(path, n)` tail requests in one
  subprocess invocation. Per-row or per-line subprocess calls are out of scope
  because Phase 0 measured helper startup p95 around 31 ms.

Preferred first caller:

- A read-only queue/watch or JobStore tail path where Python fallback already
  exists and output shape is simple.

Not allowed:

- Replacing provider transcript parsing in the same patch.
- Changing job/event/submission record schemas.
- Default enabling without benchmark evidence.

Verification:

- Python and Rust outputs match golden fixtures.
- `CCB_RUST_JSONL=0` forces old path.
- `CCB_RUST_JSONL=1` exercises helper.
- Helper crash/timeout returns old-path result with diagnostic breadcrumb.
- Large fixture benchmark records whether helper-enabled batch tailing shows
  2x throughput or lower CPU; if it does not, record that result instead of
  wiring production callers.

Exit criteria:

- Large JSONL fixture shows material speedup or lower CPU.

## Phase 3: Review Gate Before More Replacement

Owner target: main agent plus `coworker`

Scope:

- Compare benchmark results and review feedback.
- Decide whether next helper should be ProjectView, storage scan, or provider
  output parser.
- Update roadmap and open questions.
- `coworker` reviews Phase 0/1 evidence before the next helper changes runtime
  behavior. The main agent owns final dispatch; unresolved `coworker` blockers
  must either be fixed or explicitly deferred in plan-tree before dispatch.

Gate:

- Do not start Phase 4 until Phase 0-2 have evidence and reviewer objections
  are resolved or explicitly deferred.

## Worker Dispatch Rules

- Clear each worker context before assigning a new slice:
  `ccb clear worker1 worker2 worker3` or only the target worker if a smaller
  assignment is enough.
- Assign one bounded slice per worker.
- Each worker request must include:
  - exact files or directories in scope;
  - forbidden files/behaviors;
  - expected tests;
  - fallback requirement;
  - plan-tree update requirement if evidence changes.
- Use `ask --chain --artifact-reply` only when the main agent needs the
  result to continue; otherwise use `ask --silence` for independent work.
- Do not ask a worker to both design and implement a broad phase. Design
  review and implementation slices stay separate.

## Proposed First Dispatch After Review

Accepted after initial `coworker` review:

1. Clear `worker1`; assign Phase 0 measurement harness.
2. Clear `worker2`; assign Phase 1 helper contract skeleton only after Phase 0
   confirms target metrics and reviewer accepts the helper boundary.
3. Clear `worker3`; hold until Phase 1 contract exists, then assign JSONL
   helper.

Do not run `worker1` and `worker2` in parallel for the first round.

## Review Questions For Coworker

1. Is helper-binary-first the lowest-risk boundary for this repository, or
   should PyO3 be considered earlier for any specific path?
2. Is JSONL tail/query still the best first real helper after considering
   release and test complexity?
3. Are the forbidden behaviors strict enough to avoid runtime authority drift?
4. Which existing tests should be mandatory before enabling any helper in CI?
5. Should helper build artifacts live beside `tools/ccb-agent-sidebar` or in a
   new Cargo workspace?

## Rollback

- Set `CCB_RUST_HELPERS=0` or the per-helper flag to force Python paths.
- Keep helper invocation wrappers side-effect-free.
- Do not remove Python implementations until a separate deprecation plan exists.
- Release notes must describe helpers as optional acceleration until default
  enablement is proven.
