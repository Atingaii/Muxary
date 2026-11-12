# Rich Update Entry Slice

Date: 2026-06-15

## Scope

Landed the product boundary from
[../decisions/005-rich-owns-neovim.md](../decisions/005-rich-owns-neovim.md):

- `ccb update rich` is the single public install/update entry for the rich
  workbench bundle.
- `ccb rich-install` is removed and is not retained as an alias.
- Standalone public `ccb tools doctor/install/update neovim` is removed from
  normal CCB behavior.
- Normal `install.sh install` and release `ccb update` no longer provision
  Neovim/LazyVim.
- `ccb rich` launches only after the rich bundle is already installed/enabled.

## Changed Surfaces

- `lib/cli/management_runtime/commands_runtime/update.py`
- `lib/cli/entrypoint_runtime.py`
- `lib/cli/router.py`
- `lib/cli/tools_runtime/__init__.py`
- `lib/cli/tools_runtime/neovim.py`
- `lib/cli/tools_runtime/workbench.py`
- `install.sh`
- focused CLI, workbench, update, Neovim-internal, and install-script tests.

## Validation

Automatic checks from `/home/bfly/yunwei/ccb_source`:

- `python3 -m py_compile lib/cli/tools_runtime/workbench.py lib/cli/tools_runtime/__init__.py lib/cli/tools_runtime/neovim.py lib/cli/management_runtime/commands_runtime/update.py lib/cli/entrypoint_runtime.py lib/cli/router.py`
- `bash -n install.sh`
- `git diff --check -- ...`
- `pytest -q test/test_v2_cli_router.py test/test_cli_tools_workbench.py test/test_cli_tools_neovim.py test/test_cli_management_update.py test/test_install_script_sidebar.py test/test_install_watchdog_optional.py`
  passed: `157 passed in 35.35s`.

Source-wrapper validation from `/home/bfly/yunwei/test_ccb2` with isolated
`HOME=/home/bfly/yunwei/test_ccb2/source_home` and
`CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`:

- `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` passed and confirmed the
  allowed external source test project.
- `/home/bfly/yunwei/ccb_source/ccb_test update rich` exited 0. Status was
  `degraded` only because the current path was tmux and image passthrough is
  not verified; WezTerm, Yazi, Neovim, Markdown, PDF, image, and video helper
  components reported available.
- `/home/bfly/yunwei/ccb_source/ccb_test rich --help` exited 0.
- `/home/bfly/yunwei/ccb_source/ccb_test rich-install` exited 2 with guidance
  to use `ccb update rich`.
- `/home/bfly/yunwei/ccb_source/ccb_test tools doctor neovim` exited 2 with
  guidance to use `ccb update rich`.
- `/home/bfly/yunwei/ccb_source/ccb_test tools --help` no longer lists
  standalone Neovim commands and points to `ccb update rich`.
