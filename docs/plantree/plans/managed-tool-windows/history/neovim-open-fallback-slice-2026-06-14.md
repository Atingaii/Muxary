# Neovim Open And Fallback Slice: 2026-06-14

Date: 2026-06-14

## Scope

Implemented a conservative managed Neovim OS-integration slice.

Changed source surfaces:

- `lib/cli/tools_runtime/neovim.py`
- `test/test_cli_tools_neovim.py`

The implementation keeps managed Neovim isolated and does not auto-launch
external programs during doctor checks.

## Landed Behavior

- The generated managed profile now writes `lua/plugins/ccb-open.lua`.
- The profile registers:
  - `:CCBOpenCurrent`
  - `:CCBOpenUnderCursor`
  - `:CCBOpenImage`
  - `:CCBRevealCurrent`
- Default keymaps:
  - `<leader>co` opens the current file externally.
  - `<leader>cO` opens the path or URL under cursor.
  - `<leader>ci` opens the current image externally.
  - `<leader>cr` reveals the current file through Snacks explorer when
    available, falling back to external open of the parent directory.
- The opener helper chooses platform tools conservatively:
  - macOS: `open`
  - WSL: `wslview`, `explorer.exe`, then `xdg-open`
  - Linux: `xdg-open`, `gio open`, `kde-open`, then `gnome-open`
- `ccb tools doctor neovim` now reports `wsl_status` and `wsl_reason`.
  WSL projects under `/mnt/<drive>` are reported as `mounted_drive` so plugin
  IO and watcher performance risk is visible.
- The generated compatibility overlay installs a narrow `string.buffer`
  fallback when the running Neovim/Lua runtime does not provide that module.
  This keeps Snacks picker folder opens from failing during text formatting or
  history persistence on the current test host.
- Direct image opens now have an interactive fallback: when a PNG/JPEG/GIF/WebP
  style file is opened in a terminal that cannot render inline images, the
  managed profile tries the system opener and replaces the image buffer with a
  short command surface instead of showing an empty or binary buffer.
- On terminals that are not likely to support Kitty/WezTerm/Ghostty graphics
  and do not set `CCB_LAZYVIM_IMAGE_INLINE=1`, the managed profile clears
  Snacks image `formats`. That prevents Snacks `BufReadCmd` from intercepting
  direct image opens and stopping at its Image viewer protocol warning before
  the CCB external-open fallback can run.

## Verification

Unit and static checks:

- `python3 -m py_compile lib/cli/tools_runtime/neovim.py`
- `pytest -q test/test_cli_tools_neovim.py` (`20 passed`)
- `git diff --check -- lib/cli/tools_runtime/neovim.py test/test_cli_tools_neovim.py`

Source wrapper validation from `/home/bfly/yunwei/test_ccb2`:

- `HOME=/home/bfly/yunwei/test_ccb2/source_home`
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose`
- Same isolated environment with `CCB_LAZYVIM_SYNC_TIMEOUT_S=240`:
  `/home/bfly/yunwei/ccb_source/ccb_test tools install neovim`
- Same isolated environment:
  `/home/bfly/yunwei/ccb_source/ccb_test tools doctor neovim`

Observed doctor result:

- `neovim_status: ok`
- `lazyvim_sync_status: ok`
- `lazyvim_health_status: ok`
- `markdown_parser_status: ok`
- `opener_status: ok`, `opener_tool: xdg-open`
- `clipboard_status: ok`, `clipboard_tool: xclip`
- `wsl_status: not_wsl`
- `image_status: degraded` in current tmux, as expected
- `imagemagick_status: ok`, `imagemagick_tool: convert`

Manual headless check:

- The generated `ccb-open.lua` exists in the isolated profile.
- A headless `ccb-nvim` run confirmed `CCBOpenCurrent`,
  `CCBOpenUnderCursor`, and `CCBRevealCurrent` are registered commands.
- A headless Markdown open reported `filetype=markdown`,
  `RenderMarkdown` registered, and `ccb_markdown_parser_ready=true`.
- A headless PNG open confirmed the current file buffer, the CCB open commands,
  Snacks loading, and `require("string.buffer")` success.
- A headless `:CCBOpenImage` run with `vim.ui.open` stubbed confirmed the
  command targets the current PNG path without launching a GUI during tests.
- A headless Snacks config probe after reinstall confirmed
  `snacks.image.config.formats={}`, `doc.enabled=false`, and PNG support
  disabled in the current tmux/xterm test environment, leaving direct image
  files to the CCB fallback path.
- A headless directory open landed in a `snacks_picker_list` buffer and exited
  cleanly with `require("string.buffer")` success.

Implementation note:

- The first directory-open run exposed a Snacks `ExitPre` failure because
  `snacks.picker.util.kv` called `require("string.buffer").encode` on a runtime
  where `string.buffer` was absent. The managed compatibility overlay now
  provides `new`, `encode`, and `decode` only when the native module is missing.

## Remaining Work

- Run live tool-window add/remove reload validation in `/home/bfly/yunwei/test_ccb2`.
- Validate WSL home, WSL mounted-drive, and macOS behavior.
- Decide whether clipboard integration should set Neovim `clipboard` or remain
  command-only.
- Decide whether inline image rendering should auto-attempt when terminal
  support is detected or stay behind explicit commands.
