# Sequential Optimization Gates

Date: 2026-06-15

## Rule

Optimize one Rust-backed path at a time. Each step must have:

- a bounded behavior contract;
- helper-off and helper-on regression tests;
- missing/broken helper fallback tests, unless the mode is explicitly
  `required`;
- a benchmark result after the change;
- a plan-tree evidence note before moving to the next step.

Do not default-enable a helper only because Rust is faster in isolation. The
production caller must still be faster or more reliable under the current data
shape.

## Sequence

### 1. Native Output Observe

Target:

- `native.output.observe`
- `provider_backends.native_cli_support.observe_jsonl_output`

Reason:

- Latest benchmark: Python p50 `660.382 ms`, Rust p50 `138.244 ms`, p50
  speedup `4.777x`.
- Contract is narrow: parse native CLI JSONL/stdout event streams into one
  observation object.

Allowed change:

- Make default behavior equivalent to `auto`: try Rust helper when available,
  fall back to Python on helper missing/crash/bad payload.
- Preserve `CCB_RUST_NATIVE_OUTPUT=0` as force-Python.
- Preserve `CCB_RUST_NATIVE_OUTPUT=required` as no-fallback enforcement.

Required verification:

- wrapper tests for default auto, force-Python, explicit helper, missing helper,
  broken helper, bad payload, and required mode;
- production observer tests for default auto and fallback;
- native provider execution regression;
- Rust helper crate tests;
- benchmark rerun for Phase 3.

Rollback:

- Revert default mode to empty-is-disabled; keep explicit `1|auto|required`.

### 2. Storage Inventory Scan

Target:

- `storage.scan.inventory`
- `storage_classification.service`

Reason:

- Latest benchmark: Python p50 `18.800 ms`, Rust p50 `9.610 ms`, p50 speedup
  `1.956x`.
- Contract is still low risk: Rust owns filesystem inventory only. Python owns
  classification, cleanup authority, redaction, and report shape.

Allowed change:

- Make default behavior equivalent to `auto` only after Step 1 lands cleanly.
- Preserve `CCB_RUST_STORAGE_SCAN=0` as force-Python and `required` as
  no-fallback enforcement.

Required verification:

- helper-off/on parity tests;
- missing/broken helper fallback tests;
- storage classification regression;
- install/release helper availability smoke;
- benchmark rerun for Phase 4.

Rollback:

- Revert default mode to empty-is-disabled.

Status:

- Landed as default-auto in
  `history/phase11-storage-default-auto-2026-06-15.md`.

### 3. Storage Summary Contract

Target:

- new capability such as `storage.scan.summary`.

Reason:

- Inventory still returns many entries to Python. A summary contract can reduce
  stdout JSON size and Python object construction while keeping cleanup
  decisions in Python.

Allowed change:

- Add opt-in helper capability only.
- Return counts/sizes/newest timestamps and cleanup-candidate metadata by
  storage class.
- Do not move destructive cleanup decisions into Rust.

Required verification:

- golden storage fixtures;
- symlink/missing/permission fixture parity;
- no-secret-path diagnostic test;
- benchmark against inventory-plus-Python-summary.

Rollback:

- Leave existing `storage.scan.inventory` as the production path.

### 4. JSONL Delta And Counts

Target:

- capabilities such as `jsonl.find_last`, `jsonl.read_since_cursor`,
  `jobs.query.delta`, and `jobs.counts`.

Reason:

- Raw batch `jsonl.tail` is fast, but full JobRecord transfer is slower than
  Python. Rust wins when it filters, counts, or returns bounded deltas before
  stdout serialization.

Allowed change:

- Add opt-in query contracts only.
- Return bounded summaries, cursors, counts, or one detail record.
- Do not default-enable full JobRecord `jsonl.tail.strict`.

Required verification:

- malformed JSONL, empty/missing files, rotated files, large rows, Unicode;
- cursor stale/mismatch behavior;
- parity with Python query semantics;
- benchmark on typical 3/5/10-agent fixtures and sparse-history fixtures.

Rollback:

- Keep Python `JsonlStore` paths as authority.

### 5. Provider Event Parser Expansion

Target:

- provider-specific native CLI stream parsers for qwen/cursor/copilot/crush/kiro
  where event shapes diverge from the generic parser.

Reason:

- Phase 3 showed event parsing is a strong Rust fit. Provider policy and auth
  should stay in Python.

Allowed change:

- Add parser variants behind explicit capabilities.
- Keep completion policy, auth, command launch, and error classification in
  Python until contracts are stable.

Required verification:

- provider event golden fixtures;
- empty reply, tool-only, permission/auth error, timeout, final result;
- production execution regression with stub provider.

Rollback:

- Fall back to generic Python/native parser.

## Explicit Non-Targets For This Sequence

- ProjectView/tmux subprocess parser default enablement.
- ProjectView/comms recent jobs default Rust path under current adaptive
  query shape.
- Full JobRecord batch tail default enablement.
- Process cleanup/signaling until a separate safety review and dry-run planner
  exist.
