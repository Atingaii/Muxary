# Neovim Enhancement Implementation Slice: 2026-06-13

Date: 2026-06-13

## Scope

Implemented the first Linux/tmux-safe managed Neovim enhancement slice.

Changed source surfaces:

- `lib/cli/tools_runtime/neovim.py`
- `test/test_cli_tools_neovim.py`

The implementation kept production runtime authority unchanged: managed
Neovim remains a tool window, not an agent or provider runtime participant.

## Landed Behavior

- The generated managed `init.lua` records system parser runtime paths before
  lazy.nvim setup and restores them after lazy.nvim setup.
- The generated profile computes `vim.g.ccb_markdown_parser_ready` before
  plugin specs are evaluated.
- A managed `ccb-markdown.lua` overlay enables
  `render-markdown.nvim` only when `markdown` and `markdown_inline` parsers are
  visible.
- A managed `ccb-treesitter.lua` overlay disables implicit Treesitter parser
  installation by default, avoiding parser download/compile attempts during
  normal file open. Users can opt in with `CCB_LAZYVIM_TS_INSTALL=1`.
- The Snacks overlay now enables the folder explorer/picker baseline, replaces
  netrw for directories, disables explorer watcher behavior by default, and
  enables Snacks image support behind Snacks' own terminal checks.
- `ccb tools doctor neovim` reports read-only capability fields:
  `markdown_parser_status`, `opener_status`, `clipboard_status`,
  `image_status`, and `imagemagick_status`.
- Missing optional capabilities do not degrade the top-level Neovim status
  when LazyVim health is otherwise OK.

## Verification

Unit and static checks:

- `python3 -m py_compile lib/cli/tools_runtime/neovim.py`
- `pytest -q test/test_cli_tools_neovim.py`
- `git diff --check -- lib/cli/tools_runtime/neovim.py test/test_cli_tools_neovim.py`

Source wrapper validation from `/home/bfly/yunwei/test_ccb2`:

- `HOME=/home/bfly/yunwei/test_ccb2/source_home`
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose`
- Same isolated environment:
  `/home/bfly/yunwei/ccb_source/ccb_test tools doctor neovim`
- Same isolated environment with `CCB_LAZYVIM_SYNC_TIMEOUT_S=240`:
  `/home/bfly/yunwei/ccb_source/ccb_test tools install neovim`

Observed isolated install result:

- `neovim_status: ok`
- `lazyvim_sync_status: ok`
- `lazyvim_health_status: ok`
- `markdown_parser_status: ok`
- `markdown_parser_detail: markdown:ok:1,markdown_inline:ok:1`
- `opener_status: ok`, `opener_tool: xdg-open`
- `clipboard_status: ok`, `clipboard_tool: xclip`
- `image_status: degraded` in current tmux, as expected
- `imagemagick_status: ok`, `imagemagick_tool: convert`

Manual headless checks with the generated wrapper:

- Opening `/home/bfly/yunwei/test_ccb2` lands in `snacks_picker_list` without
  watcher `EMFILE` output.
- Opening the Markdown sample loads `render-markdown.nvim` and registers
  `:RenderMarkdown`.
- Opening the PNG sample loads Snacks, reports terminal image support as false
  in tmux, and exits without Markdown parser errors.
- After adding the CCB Treesitter policy, Markdown and PNG opens no longer emit
  parser download messages.

## Remaining Work

- Add user-facing external open/reveal keymaps and clipboard behavior after
  finalizing WSL fallback order.
- Add macOS, WSL home, and WSL mounted-drive validation.
- Decide whether Markview should become an automatic fallback when parser
  readiness fails.
- Decide whether inline image rendering should auto-attempt when terminal
  support is detected or stay behind an explicit command.
