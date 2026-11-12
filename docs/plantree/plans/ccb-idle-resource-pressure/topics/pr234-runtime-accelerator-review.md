# PR234 Runtime Accelerator Review Matrix

Date: 2026-06-27

## Scope

PR234 is not only the original Claude callback completion repair. Current PR
head `origin/pr/234` is a broad idle-resource reduction stack:

1. Claude callback completion capture:
   stale prompt clearing before paste, queue-operation callback anchors, and
   transcript request identity hardening.
2. Rust runtime accelerator:
   optional `ccb-runtime-accelerator` Unix-socket sidecar for Codex active-job
   observation, with Python fallback.
3. Codex idle polling reduction:
   bridge idle wait defaults and unchanged session/binding scan suppression.
4. ccbd idle write/churn reduction:
   debounced lease/keeper writes, runtime last-seen-only no-op persistence, and
   idle ProjectView cache backed by dispatcher revision invalidation.
5. Release and CI integration:
   the accelerator must compile in CI and be available in official release
   artifacts; otherwise the default-enabled sidecar path would silently fall
   back for release users.

## Current Merge State

- Latest base inspected: `origin/main` at `4a9038b8`
  (`v7.6.19`, long-running ask wait policy).
- PR head fetched as `origin/pr/234`.
- `git merge --no-commit --no-ff origin/pr/234` applied cleanly with no text
  conflicts.
- Version drift found and fixed during review: `rust/Cargo.toml` had
  workspace version `7.6.18`; merged tree must align with current `VERSION`
  `7.6.19`.

## Review Findings

### Accepted With Tests

- Claude queue-operation callback anchors are parsed as prompt records, while
  forwarded body-only `CCB_REQ_ID` text is ignored.
- Claude send prompt now clears non-empty stale input at the visible prompt line
  before pasting the CCB request.
- Rust accelerator failures are non-fatal and fall back to Python observation.
- Idle ProjectView uses dispatcher revision invalidation rather than relying on
  a longer TTL for correctness.
- Runtime `last_seen_at`-only updates stay in memory until a material runtime
  field changes.

### Fixed During Review

- Release artifacts now build and ship `bin/ccb-runtime-accelerator`.
- GitHub Actions Rust helper job now tests and builds the runtime accelerator.
- `install.sh` links the packaged accelerator binary when present and treats it
  as optional for source installs without a built binary.
- Pending callback edges now count as hot-loop work so idle full-heartbeat
  skipping does not delay callback repair/timeout progression.
- Codex deferred session-switch scan signatures now use the configured Codex
  session root, not the ambient process session root, so cache invalidation
  follows the managed agent home instead of the reviewer process environment.
- Runtime accelerator socket placement now falls back to a short runtime socket
  root when a project path makes `<project>/.ccb/runtime-accelerator/accelerator.sock`
  exceed Unix socket path limits. The live regression project exposed this as
  Rust sidecar startup failure: `path must be shorter than SUN_LEN`.
- Removed a duplicate `project_view` import introduced by the PR stack.

## Regression Matrix

| Slice | Required Evidence |
| --- | --- |
| Claude transcript and stale prompt | `test/test_provider_hook_transcript.py`, `test/test_claude_execution_runtime_start.py`, `test/test_provider_finish_hook_script.py`, `test/test_claude_protocol.py`, `test/test_terminal_runtime_tmux_send.py` |
| Runtime accelerator Python glue | `test/test_runtime_accelerator_client.py`, `test/test_runtime_accelerator_lifecycle.py`, `test/test_codex_runtime_accelerator_polling.py`, `test/test_codex_execution_polling.py` |
| Codex bridge/binding idle scans | `test/test_codex_bridge_runtime.py`, `test/test_codex_binding_update.py`, `test/test_codex_session_switch.py`, `test/test_codex_comm_io.py` |
| ccbd idle heartbeat/write churn | selected `test/test_v2_ccbd_socket.py`, `test/test_v2_ccbd_mount_ownership.py`, `test/test_v2_ccbd_keeper.py`, `test/test_ccbd_registry.py` |
| ProjectView idle cache freshness | `test/test_ccbd_project_view.py` |
| Release/CI packaging | `test/test_build_linux_release_script.py`, `test/test_install_script_sidebar.py`, `.github/workflows/test.yml`, `.github/workflows/release-artifacts.yml` |
| Rust sidecar | `cargo fmt --check -p ccb-runtime-accelerator`, `cargo test -p ccb-runtime-accelerator -- --test-threads=1`, and `cargo build -p ccb-runtime-accelerator` from `rust/` |

## Evidence So Far

- Provider/accelerator focused suite: `54 passed`.
- ccbd idle/project-view/registry/keeper suite: `173 passed`.
- Packaging/install focused suite after review fixes: `52 passed`.
- Final broadened regression:
  `test_provider_hook_transcript.py`, `test_claude_execution_runtime_start.py`,
  `test_provider_finish_hook_script.py`, `test_claude_protocol.py`,
  `test_terminal_runtime_tmux_send.py`, `test_runtime_accelerator_client.py`,
  `test_runtime_accelerator_lifecycle.py`,
  `test_codex_runtime_accelerator_polling.py`,
  `test_codex_execution_polling.py`, `test_codex_session_switch.py`,
  `test_codex_binding_update.py`, `test_codex_bridge_runtime.py`,
  `test_codex_comm_io.py`, `test_v2_ccbd_socket.py`,
  `test_v2_ccbd_mount_ownership.py`, `test_v2_ccbd_keeper.py`,
  `test_ccbd_project_view.py`, `test_ccbd_registry.py`,
  `test_build_linux_release_script.py`, `test_install_script_sidebar.py`, and
  `test_v2_phase2_entrypoint.py::test_ccb_long_running_job_keeps_heartbeat_and_doctor_healthy`:
  `279 passed`.
- Rust sidecar: `cargo fmt --check -p ccb-runtime-accelerator`,
  `cargo test -p ccb-runtime-accelerator -- --test-threads=1`, and
  `cargo build --release -p ccb-runtime-accelerator` passed.
- Linux release preview: `scripts/build_linux_release.py --allow-dirty`
  produced `ccb-linux-x86_64.tar.gz`; the tarball contains
  `bin/ccb-runtime-accelerator`, and the unpacked binary returned a project
  `.ccb/runtime-accelerator/accelerator.sock` path.
- Python compile check for changed runtime modules passed.
- `git diff --check` passed.
- First full-suite run: `python -m pytest -q` returned
  `3058 passed, 2 skipped` in `0:12:29`.
- Real `/home/bfly/yunwei/test_ccb2` source-runtime pressure test:
  dedicated project
  `pr234-runtime-accelerator-live-20260627-084649`, 3 Codex agents, PR234
  `ccb_test`, real provider home. Initial isolated-home run correctly exposed
  missing Codex auth and then sidecar startup failure on an overlong project
  socket path.
- After socket fallback fix, the sidecar started at
  `/run/user/1000/ccb-runtime/accelerator-3f3c486ccb4b2dfd.sock` and
  `ccb-runtime-accelerator ping` returned status `ok`.
- Warmup ask `job_b74f835f430f` completed with reply `PR234_WARMUP_OK`.
- Pressure run submitted 9 asks across `agent1`, `agent2`, and `agent3` in
  about 2 seconds. All completed, including queued per-agent jobs:
  `A1_OK_1`, `A2_OK_1`, `A3_OK_1`, `A1_OK_42`, `A2 QUEUE OK`,
  `A3_QUEUE_OK`, `A1_DONE_3`, `A2_DONE_3`, and `A3_DONE_3`.
- Post-pressure doctor summary: `ccbd_health: healthy`,
  `ccbd_active_execution_count: 0`, `ccbd_pending_items_count: 0`,
  `ccbd_terminal_pending_count: 0`, and mailbox consistency `ok` for all 3
  agents. Accelerator ping still returned status `ok`.
- Final full-suite run after the socket fallback fix:
  `python -m pytest -q` returned `3059 passed, 2 skipped` in `0:12:22`.
- Final Rust sidecar gate after the socket fallback fix:
  `cargo fmt --check -p ccb-runtime-accelerator`,
  `cargo test -p ccb-runtime-accelerator -- --test-threads=1`, and
  `cargo build --release -p ccb-runtime-accelerator` passed with 9 Rust tests.
- Final release preview after the socket fallback fix:
  `scripts/build_linux_release.py --allow-dirty` produced the Linux tarball,
  included `bin/ccb-runtime-accelerator`, and the unpacked binary returned a
  valid default socket path.
- Extended real source-runtime integration on 2026-06-27:
  - Codex soak project
    `/home/bfly/yunwei/test_ccb2/pr234-soak-codex-20260627-111357` used 3
    Codex agents, PR234 `ccb_test`, real provider home, and the Rust sidecar at
    `/run/user/1000/ccb-runtime/accelerator-9d6cbed77176aff5.sock`.
  - The soak ran 4 rounds separated by 300-second idle windows. All 12 asks
    completed with exact replies:
    `SOAK_1_agent1_OK`, `SOAK_1_agent2_OK`, `SOAK_1_agent3_OK`,
    `SOAK_2_agent1_OK`, `SOAK_2_agent2_OK`, `SOAK_2_agent3_OK`,
    `SOAK_3_agent1_OK`, `SOAK_3_agent2_OK`, `SOAK_3_agent3_OK`,
    `SOAK_4_agent1_OK`, `SOAK_4_agent2_OK`, and `SOAK_4_agent3_OK`.
  - After every soak round, `ccb-runtime-accelerator ping` returned `ok`;
    `ccbd_health` stayed `healthy`; active execution, pending queue, and
    terminal-pending counts stayed at `0`; mailbox consistency was `ok` for
    all 3 agents.
  - Claude live project
    `/home/bfly/yunwei/test_ccb2/pr234-claude-live-20260627-111653` completed
    direct ask `job_f03ee12e0b81` with `CLAUDE_DIRECT_OK`. Callback chain
    parent `job_3658f8245faf` delegated to Claude child `job_29bcbf04cfa0`
    (`CLAUDE_CHILD_OK`) and continuation `job_559da97c5d82` completed with
    `CALLBACK_CHAIN_OK: CLAUDE_CHILD_OK`; doctor ended healthy with no active,
    pending, or terminal-pending work.
  - Mixed provider project
    `/home/bfly/yunwei/test_ccb2/pr234-mixed-provider-20260627-112030`
    mounted Codex, Claude, Gemini, OpenCode, Kimi, Z.ai, and AGY together.
    Startup, ping, and doctor showed all agents restored and mailbox
    consistency `ok`. OpenCode completed `job_909d70b7bdc2` with
    `OPENCODE_MIXED_OK`; Kimi completed `job_a93a19e0a6f3` with
    `KIMI_MIXED_OK`; AGY completed `job_2a7089cc1326` with `AGY_MIXED_OK`
    after approving the test-folder trust prompt. Gemini was cancelled after
    blocking on first-run authentication confirmation; Z.ai failed with
    provider stderr `API key required` because `ZAI_API_KEY` was absent. Final
    doctor after cancellation showed `ccbd_health: healthy`, active execution
    count `0`, pending item count `0`, terminal-pending count `0`, and all
    mailbox consistency checks `ok`.

## Final Gate

The PR234 merge state has passed full unit/integration regression, release
artifact preview, Rust sidecar gates, real source-runtime communication
pressure, long-idle Codex soak, Claude callback live validation, and mixed
provider startup/native-completion validation where local credentials allowed
execution. It is ready to land as the amended review merge commit.
