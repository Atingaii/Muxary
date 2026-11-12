# Performance Replacement Map

Date: 2026-06-15

## Principle

Move work to Rust only when it is:

- CPU-bound parsing, scanning, filtering, or aggregation;
- repeated on sidebar/project-view refresh paths;
- expensive over large JSONL/log/storage trees;
- easy to define with a stable data contract;
- safe to fall back to Python.

Do not move provider policy, runtime authority, or completion semantics until
their input/output contracts are frozen.

## Hybrid Boundary Choice

### Preferred First Boundary: Rust Helper Binary

Shape:

```text
Python caller -> rust helper argv/stdin JSON -> stdout JSON/JSONL -> Python fallback on error
```

Use for:

- JSONL tail/query;
- storage scan/classification;
- tmux project-view collection;
- process tree cleanup;
- provider stdout/jsonl parsing.

Benefits:

- Low packaging risk compared with Python native extensions.
- Crashes do not kill `ccbd`.
- Works with source and release install models.
- Easy golden-file tests.

Costs:

- Subprocess startup overhead.
- Requires timeout, schema version, stderr, and fallback policy.
- Large stdout JSON payloads can dominate runtime even when Rust parsing is
  faster. Prefer bounded summaries, top-N results, filters, or aggregation over
  returning thousands of records to Python.

### Later Boundary: PyO3 Extension

Use only if benchmarks show helper process startup dominates the workload.

Candidate functions:

- JSON/JSONL decode and tail loops;
- config/layout parser if startup parsing becomes material;
- provider event parsers used every poll.

Do not start here because PyO3 increases Python ABI, wheel, macOS universal,
and source install complexity.

### Later Boundary: Rust Sidecar

Use only after helper binaries prove the contract and ProjectView/sidebar still
needs lower latency.

Candidate shape:

- project-scoped cache/index sidecar;
- Unix socket or inherited stdin/stdout protocol;
- Python `ccbd` remains authority and can restart/ignore sidecar.

## Replacement Priority

| Priority | Target | Why Rust Helps | Expected Gain | Risk |
| :--- | :--- | :--- | :--- | :--- |
| P0 | Metrics and benchmark harness | Prevents optimizing blind paths. | Enables decisions, no runtime gain. | Low |
| P1 | JSONL tail/query helper | Large logs and queue/watch views are parse-heavy and easy to contract. | 2x-10x on large files; lower CPU. | Low |
| P1 | Provider output parser helper | Native CLI providers emit JSONL/stream JSON; parsing is bounded and testable. | 2x-5x parsing speed on large outputs. | Low-medium |
| P2 | ProjectView/tmux collector | Sidebar refresh repeats tmux output parsing and state aggregation. | Landed parser slice, but latest helper-subprocess retest is slower than Python; keep non-default. | Medium |
| P2 | Storage classification scanner | Directory walking and aggregation are classic Rust wins. | Landed inventory slice: latest retest 1.956x p50; full classifier still deferred. | Medium |
| P3 | Process tree cleanup helper | Rust can make pid/process-group handling stricter and faster. | Better shutdown consistency; modest speedup. | Medium-high |
| P4 | Rust sidecar cache | Avoids repeated subprocess startup and rebuild work. | High for very frequent sidebar refresh. | High |
| P5 | Rust `ccbd` core | Strong type/concurrency benefits. | Not performance-first; migration risk dominates. | Very high |

## Proposed Helper Commands

### `ccb-rs-jsonl`

Responsibilities:

- tail N JSONL rows;
- find latest row matching field predicates;
- read since cursor;
- optionally return byte offsets for future incremental indexing.

Python fallback:

- existing `JsonlStore` and provider-specific readers.

Acceptance:

- golden fixtures for malformed rows, empty files, rotated files, large rows,
  Unicode, and missing files.

### `ccb-rs-project-view`

Responsibilities:

- parse batched tmux `list-panes`, `list-windows`, and `display-message`
  stdout;
- normalize pane facts;
- optionally prepare sidebar-ready summary fragments.

Python remains owner of:

- tmux execution through the namespace backend;
- authority decisions;
- lifecycle state interpretation;
- final ProjectView schema.

Acceptance:

- same ProjectView payload as Python for synthetic namespace fixtures.
- improved p95 refresh when sidebar is enabled.

### `ccb-rs-storage-scan`

Responsibilities:

- directory walk;
- symlink-safe size aggregation;
- deduped inventory output.

Python remains owner of:

- provider-state rule matching;
- summary by storage class;
- cleanup decisions;
- destructive operations;
- diagnostics redaction policy until the Rust classifier is fully trusted.

Acceptance:

- parity with storage doctor fixtures.
- no secret path leaked in helper output.

### `ccb-rs-proc`

Responsibilities:

- process tree discovery;
- process group signaling;
- zombie/uninterruptible-state classification where platform support exists.

Python remains owner of:

- lifecycle authority;
- when cleanup is allowed;
- shutdown transaction sequencing.

Acceptance:

- Linux/macOS smoke parity.
- no blind global process-name cleanup.

## Rollout Policy

Every helper must support:

- `--version`;
- `--capabilities`;
- schema version in every JSON response;
- bounded timeout from Python caller;
- stderr capture in diagnostics;
- feature flag and Python fallback;
- release artifact inclusion test;
- source install behavior: build if Cargo exists, otherwise fallback.

Current packaging status:

- `ccb-rs-helper` now has `bin/build-ccb-rs-helper`, a source wrapper at
  `bin/ccb-rs-helper`, `install.sh` build/install handling, and release artifact
  build handling.
- Linux release preview artifact smoke verified executable `bin/ccb-rs-helper`
  and `jsonl.tail.strict` in `--capabilities`.

Suggested feature flags:

- `CCB_RUST_HELPERS=0|1|auto`
- `CCB_RUST_JSONL=0|1|auto`
- `CCB_RUST_JSONL_STORE=0|1|required`
- `CCB_RUST_NATIVE_OUTPUT=0|1|auto|required`
- `CCB_RUST_PROJECT_VIEW=0|1|auto|required`
- `CCB_RUST_PROJECT_VIEW_RECENT_JOBS=0|1|required`
- `CCB_RUST_STORAGE_SCAN=0|1|auto|required`
- `CCB_RUST_PROC=0|1|auto`

Optional `1|auto` modes are fallback-tolerant. `required` modes intentionally
raise when the helper is missing, crashes, or returns an invalid payload.

Default fallback removal is not allowed per helper slice. It is a separate
low/medium-risk completion gate after each candidate target has:

- helper-backed parity tests;
- production-path regression coverage;
- missing/broken helper behavior reviewed;
- benchmark evidence meeting the configured threshold;
- a reviewed decision that the Python implementation is no longer needed.

Phase 6 update: strict JSONL semantics are available and the required path has
no Python fallback, but full JobRecord tailing misses the performance gate. Do
not default-enable or globally remove the Python JSONL path until a narrower
contract, cache, or sidecar changes that measurement.

Phase 7/9 update: ProjectView recent jobs first showed a Rust win under the old
fixed-tail fixture, but the fetch-design slice changed the default query shape.
ProjectView/comms now starts with an adaptive per-agent scan budget and deepens
only when needed. Under the adaptive 10-agent fixture, Python p50 is `2.042 ms`
and Rust `jobs.query.recent` p50 is `2.987 ms`, so this path should remain
non-default unless a persistent/in-process boundary or heavier real fixture
changes the measurement.

Required-mode gate update: native output, storage inventory, and
ProjectView/tmux parsing now support `required` no-fallback semantics at both
wrapper and production entrypoint layers. Current benchmark evidence supports
considering native output and storage inventory for default enablement. After
Phase 9, keep ProjectView recent jobs, ProjectView/tmux parser, and full
JobRecord strict JSONL non-default until their latest negative
helper-subprocess benchmarks are addressed.

Phase 8 update: helper capability probe results are cached per Python process
by helper path, mtime, and size. The broader `jobs.tail.summary` projection
proved that projection alone is not enough when the result set remains large:
returning 16k job summaries over stdout JSON is still slower than Python
(`0.578x` p50). Future job-query helpers need either much narrower top-N
contracts, stronger server-side filtering/aggregation, or a lower-overhead
boundary such as a persistent helper or PyO3.

Job fetch design update: fixed per-agent `tail=128` is also not the right
production contract. Even with the typical project size of fewer than 10
agents, it can still overfetch hundreds or thousands of summaries when the UI
only needs a small recent list, a delta refresh, counts, or one expanded job.
Use `topics/job-fetch-design.md` as the authority for the next job-query slice:
top-N recent list first, adaptive per-agent scan budgets, cursor delta later,
counts/buckets for badges, and detail-on-demand for full records.

Phase 9 update: the top-N recent-list slice is landed. It confirms the design
premise: reducing query volume matters more than moving this small UI refresh
through a subprocess helper. Continue with delta/count/detail contracts before
revisiting Rust default enablement for ProjectView/comms.

## Performance Gates

Default enablement should require:

- functional parity tests pass with helper off and on;
- Linux and macOS CI pass;
- helper missing/broken fallback path tested;
- no loss of diagnostics detail;
- at least one measured threshold:
  - 2x speedup for large JSONL or storage scan fixtures;
  - 1.5x speedup for low-risk storage inventory when Python retains storage
    classification and cleanup policy;
  - 20% p95 latency reduction for ProjectView or queue/watch;
  - lower CPU during sidebar refresh under a multi-window project.

## Rough Effort

| Slice | Calendar Estimate | Token Estimate |
| :--- | :--- | :--- |
| Baseline benchmarks and metrics | 3-5 days | 0.3M-0.8M |
| Cargo workspace/helper contract | 3-5 days | 0.5M-1M |
| JSONL helper | 1-2 weeks | 1M-2.5M |
| ProjectView/tmux helper | 2-3 weeks | 2M-5M |
| Storage scan helper | 1-2 weeks | 1M-3M |
| Process cleanup helper | 2-3 weeks | 2M-4M |
| Optional Rust sidecar prototype | 4-8 weeks | 5M-12M |

## Non-Goals

- Do not replace all Python just to reduce language count.
- Do not move policy-heavy provider behavior before schema and golden tests
  prove equivalence.
- Do not make Rust helper availability a hard startup requirement in the first
  release.
