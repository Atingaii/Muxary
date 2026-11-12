# Stable Entrypoint Boundary

Date: 2026-06-15

## User Requirement

Normal `ccb` startup must always use the stable installed release selected for
the user work environment. Editing source files, running source validation, or
running install/update smoke tests must not change what a bare `ccb` imports or
which runtime root an existing project backend uses.

## Finding And Closure

This was not fully true in the local environment at the start of the
2026-06-15 audit.

Observed on 2026-06-15:

- `command -v ccb` resolves to `/tmp/ccb-v7.2.1-install-smoke/prefix/ccb`.
- `/home/bfly/.local/bin/ccb` is a symlink to
  `/tmp/ccb-v7.2.1-install-smoke/prefix/ccb`.
- The live `ccb_source` keeper and daemon run from
  `/tmp/ccb-v7.2.1-install-smoke/prefix/lib/ccbd/...`, with
  `PYTHONPATH=/tmp/ccb-v7.2.1-install-smoke/prefix/lib`.
- Multiple other live project daemons also run from the same temporary smoke
  prefix.
- The normal historical installed tree still exists at
  `/home/bfly/.local/share/codex-dual`, but it is no longer the first bare
  `ccb` authority.

The source entrypoint guards and absolute `ccb_test` workflow protect source
validation, but they do not by themselves protect the global installed
entrypoint from install/update smoke pollution.

Closed on 2026-06-15:

- `ccb doctor` now reports `entrypoint_*` fields for the resolved bare `ccb`,
  its realpath, expected install path, and match status.
- `ccb doctor` now reports `ccbd_implementation_*` fields so temporary daemon
  implementation roots can be surfaced when the process cmdline is available.
- `install.sh install` now refuses a temporary `CODEX_INSTALL_PREFIX` when
  `CODEX_BIN_DIR` is outside the same temporary prefix or temporary HOME,
  unless `CCB_ALLOW_TEMP_INSTALL_GLOBAL_BIN=1` is explicitly set.
- `/home/bfly/.local/bin/ccb` was restored to
  `/home/bfly/.local/share/codex-dual/ccb`.
- The active `ccb_source` tmux server global `PATH` was updated to remove
  `/tmp/ccb-v7.2.1-install-smoke/prefix/bin` and
  `/tmp/ccb-v7.2.1-install-smoke/prefix`, so newly created panes no longer
  inherit that temporary prefix first.
- A clean shell PATH resolves `ccb` to the durable installed release
  `v7.2.1`.

Residual operational note:

- Already-running CCB panes and project daemons may still have inherited the
  old `/tmp/ccb-v7.2.1-install-smoke/prefix` process environment or
  implementation root until those projects are restarted through the durable
  installed `ccb`.

## Boundary Contract

- A release/update smoke test may use temporary `HOME`, `XDG_*`,
  `CODEX_INSTALL_PREFIX`, and `CODEX_BIN_DIR`, but it must not rewrite the
  user's real `~/.local/bin/ccb` or persistent shell startup files.
- Bare `ccb` in a normal project must resolve to a stable managed install
  prefix, not to `/tmp`, a source checkout, or a disposable release simulation
  prefix.
- `ccb_test` may point at the source checkout only when invoked through the
  absolute source wrapper or after an explicit wrapper-resolution preflight.
- A project backend should record enough runtime-root evidence for `doctor` to
  flag a daemon whose implementation root is a temporary smoke prefix.
- Rich terminal launchers must drop inherited `TMUX`, `TMUX_PANE`,
  `CCB_TMUX_SOCKET`, and `CCB_TMUX_SOCKET_PATH` before opening a new terminal
  so nested startup cannot apply tmux UI changes to the wrong outer session.

## Required Gates

- `command -v ccb` and `readlink -f "$(command -v ccb)"` are recorded before
  work-environment startup and before declaring source validation complete.
- A stable-entrypoint audit fails if bare `ccb` resolves under `/tmp`, under
  `/home/bfly/yunwei/ccb_source`, or under a known smoke-test prefix.
- Install/update smoke tests prove `CODEX_BIN_DIR` and `CODEX_INSTALL_PREFIX`
  are isolated and do not mutate real user wrappers or shell rc files.
- `ccb doctor` reports the implementation root for the current daemon and
  warns when that root is temporary.
- Restarting a normal project after source edits still starts from the stable
  installed release, not from the edited checkout.

## Verification

- `pytest -q test/test_doctor_runtime_identity.py test/test_install_root_confirmation.py`
  passed.
- `pytest -q test/test_v2_tmux_cleanup_history.py test/test_doctor_runtime_identity.py test/test_install_root_confirmation.py test/test_cli_management_install.py test/test_cli_management_update.py`
  passed.
- `HOME=/home/bfly/yunwei/test_ccb2/source_home CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home /home/bfly/yunwei/ccb_source/ccb_test --diagnose`
  passed from `/home/bfly/yunwei/test_ccb2`.
- Source `ccb_test doctor` flagged the polluted inherited bare `ccb` as
  `entrypoint_status: degraded` with
  `entrypoint_reason: bare_ccb_resolves_under_temporary_directory`.
- `env -i HOME=/home/bfly USER=bfly SHELL=/bin/zsh PATH=/home/bfly/.local/bin:/usr/local/bin:/usr/bin:/bin zsh -lc 'command -v ccb; readlink -f "$(command -v ccb)"; ccb --print-version'`
  resolved to `/home/bfly/.local/share/codex-dual/ccb` and printed `v7.2.1`.

## Open Work

1. Add a small operator runbook for restarting affected live projects through
   the durable installed release without deleting project runtime state.
2. Extend managed update coverage so tarball update simulations also prove they
   cannot mutate real user wrappers or shell startup files.
