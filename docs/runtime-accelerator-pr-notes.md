# Runtime accelerator PR review notes

## Intent

Reduce Python idle CPU without changing the `.ccb` user-facing runtime contract.
Python remains the owner of CLI behavior, socket protocol, dispatcher state,
mailbox delivery, lifecycle, and provider hook configuration. Rust is added as
an optional hotpath sidecar for active Codex observation.

## Commit stack

- `f1e1383 Reduce idle CPU without changing runtime semantics`
  - Python idle-loop reductions: Codex bridge wait, binding follow interval,
    and ccbd idle full-maintenance gate.
- `76d9f75 Add Rust runtime accelerator sidecar`
  - Standalone `rust/crates/ccb-runtime-accelerator` workspace.
- `4ea58bf Wire Python runtime to the Rust accelerator`
  - Python glue, sidecar lifecycle, fallback handling, tests, and switch docs.
- PR regression follow-up in the final merge review:
  - release artifacts now build and ship `bin/ccb-runtime-accelerator`;
  - GitHub Actions Rust helper checks compile/test the accelerator crate;
  - install links the packaged accelerator binary when present;
  - accelerator default socket placement falls back to a short runtime socket
    root when the project-local socket path exceeds Unix socket limits.

## Switches and rollback

Primary rollback:

```bash
CCB_RUNTIME_ACCELERATOR_CODEX=0
```

This forces the legacy Python Codex polling path. It does not disable Codex
hooks.

Additional rollout controls:

```bash
CCB_RUNTIME_ACCELERATOR_BIN=/path/to/ccb-runtime-accelerator
CCB_RUNTIME_ACCELERATOR_SOCKET=/path/to/accelerator.sock
CCB_RUNTIME_ACCELERATOR_TIMEOUT_S=0.2
CCB_RUNTIME_ACCELERATOR_STARTUP_TIMEOUT_S=0.5
CCB_BRIDGE_IDLE_SLEEP=0.05
CCB_CODEX_BIND_POLL_INTERVAL=0.5
CCB_CCBD_IDLE_FULL_HEARTBEAT_INTERVAL_S=30
CCB_CCBD_HEARTBEAT_WRITE_INTERVAL_S=5
CCB_KEEPER_STATE_WRITE_INTERVAL_S=5
```

`CCB_BRIDGE_IDLE_SLEEP=0.05` and `CCB_CODEX_BIND_POLL_INTERVAL=0.5` restore the
legacy low-latency polling cadence for diagnostics.

## Fallback matrix

Rust acceleration is non-fatal. Python fallback is used when:

- `CCB_RUNTIME_ACCELERATOR_CODEX=0`
- the sidecar binary is missing
- sidecar startup fails
- the sidecar socket is unavailable
- RPC times out
- response is malformed
- a per-job observation returns `error`
- an unknown completion item kind is returned

Successful empty Rust observations are authoritative for that tick and do not
also pay the Python polling cost.

## Compatibility boundaries

- Do not replace Python `ccbd` with `ccbrd`.
- Do not import `.ccbr` state assumptions.
- Do not disable, skip, or mask Codex hooks.
- Keep ccb-legacy as the compatibility proof line for future Rust hotpath work.

## Verification used for this stack

Python targeted checks:

```bash
PYTHONPATH=lib pytest -q \
  test/test_runtime_accelerator_client.py \
  test/test_runtime_accelerator_lifecycle.py \
  test/test_codex_runtime_accelerator_polling.py \
  test/test_codex_execution_polling.py \
  test/test_codex_bridge_runtime.py \
  test/test_codex_binding_update.py

python -m compileall -q \
  lib/runtime_accelerator \
  lib/provider_backends/codex/execution_runtime \
  lib/ccbd/app_runtime/bootstrap.py \
  lib/ccbd/app_runtime/lifecycle.py
```

Rust targeted checks:

```bash
cd rust
cargo fmt --check -p ccb-runtime-accelerator
cargo test -p ccb-runtime-accelerator -- --test-threads=1
```

Live local observation after restart showed Codex bridge CPU dropping from the
previous ~16-19% hotspot to low single digits or below for idle agents; ccbd
still has a remaining idle thread hotspot for later P1 work.

Final merge review additionally ran a real `/home/bfly/yunwei/test_ccb2`
source-runtime communication pressure project with three Codex agents. The
review first exposed an overlong accelerator socket path failure, then verified
the fixed short socket fallback with 9 completed ask jobs across active and
queued per-agent execution.

Extended integration on 2026-06-27 added:

- a 3-agent Codex soak with 4 rounds separated by 300-second idle windows; all
  12 asks completed, the sidecar ping stayed `ok`, ccbd stayed healthy, and
  mailbox consistency stayed `ok`;
- a Claude live direct ask plus Codex-to-Claude callback chain; the Claude child
  reply and callback continuation completed normally;
- a mixed-provider startup and completion check covering Codex, Claude, Gemini,
  OpenCode, Kimi, Z.ai, and AGY in one project. OpenCode, Kimi, and AGY
  completed native-detected asks. Gemini and Z.ai were environment-blocked by
  first-run authentication and missing `ZAI_API_KEY`, respectively, and the
  project returned to a healthy zero-active state after cancellation/cleanup.

Heartbeat write debounce check:

```bash
PYTHONPATH=lib uv run --with pytest pytest -q test/test_v2_ccbd_mount_ownership.py
```

Keeper/lifecycle idle-write check:

```bash
PYTHONPATH=lib uv run --with pytest pytest -q test/test_v2_ccbd_keeper.py
```

## Known follow-up

- Remaining ccbd idle thread and keeper loop are separate P1 optimizations.
