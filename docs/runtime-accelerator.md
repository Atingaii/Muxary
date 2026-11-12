# Runtime accelerator switches

This repository keeps the Python `.ccb` runtime as the owner of public CLI, socket protocol, dispatcher, mailbox, lifecycle, and Codex hooks. The Rust `ccb-runtime-accelerator` is a local sidecar for hot paths only.

Official release artifacts build and include `bin/ccb-runtime-accelerator`.
Source checkouts can build it with `bin/build-ccb-runtime-accelerator`; when
the binary is missing, Python falls back to the legacy Codex observation path.
When ccbd starts the sidecar, it records exact PID, cwd, argv, executable,
socket, and process-start-token ownership. Linux resolves that evidence through
`/proc`; macOS uses `ps` plus the executable and cwd mappings reported by
`lsof` while retaining the same fail-closed identity checks.
Socket arguments are compared by canonical path so platform aliases such as
macOS `/tmp` and `/private/tmp` identify the same owned Unix socket.

## Python/Rust switch controls

| Variable | Default | Effect | Review note |
| --- | --- | --- | --- |
| `CCB_RUNTIME_ACCELERATOR_CODEX` | enabled when unset | Set `0`, `false`, `no`, `off`, or `disabled` to force the legacy Python Codex polling path. | Main Python/Rust module switch. |
| `CCB_RUNTIME_ACCELERATOR_BIN` | `ccb-runtime-accelerator` lookup | Override the Rust sidecar binary path. | Packaging can wire this to an installed binary. |
| `CCB_RUNTIME_ACCELERATOR_SOCKET` | `<project>/.ccb/runtime-accelerator/accelerator.sock`, or a short runtime socket root when the project path is too long for Unix sockets | Override sidecar Unix socket. | Useful for smoke tests and staged rollout. |
| `CCB_RUNTIME_ACCELERATOR_TIMEOUT_S` | `0.2` | Sidecar RPC timeout before falling back to Python polling. | Failure is non-fatal. |
| `CCB_RUNTIME_ACCELERATOR_STARTUP_TIMEOUT_S` | `0.5` | Startup wait for ccbd-managed sidecar. | Missing binary records fallback action. |
| `CCB_BRIDGE_IDLE_SLEEP` | `1.0` | Codex bridge FIFO wait timeout; set `0.05` to restore legacy low-latency idle polling for diagnostics. | FIFO messages still wake through the persistent reader. |
| `CCB_CODEX_BIND_POLL_INTERVAL` | `5.0` | Codex session/log binding follow interval; set `0.5` to restore legacy follow cadence. | Does not disable binding follow. |
| `CCB_CCBD_IDLE_FULL_HEARTBEAT_INTERVAL_S` | `30.0` | Idle full-maintenance interval for ccbd. | Active jobs/queues still run full maintenance immediately. |

## Rollback

Use `CCB_RUNTIME_ACCELERATOR_CODEX=0` to bypass the Rust Codex observation path without disabling Codex hooks. Existing Python behavior remains the fallback for unavailable sidecar, timeout, malformed response, per-job error, or unknown item kind.
