# Workbench Bundle Slice

Date: 2026-06-15

## Scope

Landed the first CCB-owned rich terminal workbench bundle slice.

Touched source files:

- `lib/cli/tools_runtime/workbench.py`
- `lib/cli/tools_runtime/__init__.py`
- `lib/cli/router.py`
- `test/test_cli_tools_workbench.py`

The slice adds a new `workbench` tool runtime without moving the existing
Neovim runtime into the bundle implementation.

Follow-up on 2026-06-15 added the simple top-level installer alias:

- `ccb rich-install`

This command installs and enables the rich workbench bundle in one step. The
lower-level `ccb tools ... workbench --profile rich` entry remains available
for internal tests and advanced diagnostics, but `ccb rich-install` is the
preferred user-facing setup command for the `rich` layout alias.

Follow-up on 2026-06-15 sealed the WezTerm visual defaults inside the rich
bundle:

- `ccb-workbench terminal` now launches WezTerm with the generated
  `profiles/wezterm/wezterm.lua` via `--config-file`.
- The generated WezTerm profile owns compact workbench defaults, including
  `font_size = 10.5`, fixed initial columns/rows, tight window padding, a
  simple tab bar, and CCB workbench environment variables.
- This prevents user global WezTerm font/window settings from making the CCB
  rich workbench oversized or visually inconsistent.
- Live retest removed the old `-n`/`--skip-config` flag because it conflicts
  with `--config-file`, added `start --always-new-process --no-auto-connect`,
  and removed `default_cwd` from the generated config so `--cwd "$PWD"` remains
  the project directory authority.
- Follow-up font tuning moved rich WezTerm to a CCB-owned family-only fallback
  stack: JetBrains Mono, Fira Code, Noto Sans Mono, Noto Sans Mono CJK SC,
  symbol fonts, and platform emoji fonts. The config avoids pinning
  `weight = "Regular"` so WezTerm can resolve bold/italic faces correctly, with
  ligatures disabled for predictable terminal rendering and
  `font_size = 10.5` / `line_height = 1.05`.
- Follow-up tmux styling fixed rich/tool panes participating in active window
  border coloring, restored the border hook, and sets `pane-border-lines` to
  `heavy` where tmux supports it so the rich split line and focused pane are
  visibly highlighted.

## Landed Behavior

- `ccb tools doctor workbench --profile rich`
- `ccb tools install workbench --profile rich`
- `ccb tools update workbench --profile rich`
- `ccb tools enable workbench --profile rich`
- `ccb tools launch workbench --profile rich --dry-run`
- `ccb tools disable workbench --profile rich`
- `ccb tools uninstall workbench --profile rich`

The generated bundle is independent from user dotfiles:

- root: `$XDG_DATA_HOME/ccb/tools/workbench`
- state: `$XDG_STATE_HOME/ccb/tools/workbench`
- cache: `$XDG_CACHE_HOME/ccb/tools/workbench`
- bin links: `$CODEX_BIN_DIR` or `$HOME/.local/bin`
- no writes to `~/.config/yazi`, `~/.config/nvim`, `~/.config/wezterm`, or
  global tmux config.

Generated bundle artifacts include:

- `ccb-workbench`
- `ccb-yazi`
- `ccb-yazi-rich`
- `ccb-md-preview`
- `ccb-pdf-preview`
- `ccb-video-preview`
- CCB-owned Yazi safe and rich profiles
- CCB-owned minimal piper-compatible Yazi preview plugin
- CCB-owned WezTerm config
- JSON manifest with component statuses, generated paths, enabled state, and
  degraded reasons

The safe Yazi profile renders Markdown through a generated Markdown helper and
uses text/metadata fallback for PDF and video. The rich Yazi wrapper selects
the rich profile only when a direct rich terminal candidate is detected or
`CCB_WORKBENCH_FORCE_RICH` is set; otherwise it falls back to the safe profile.

## Verification

Automatic checks:

- `python3 -m py_compile lib/cli/tools_runtime/workbench.py lib/cli/tools_runtime/__init__.py lib/cli/tools_runtime/neovim.py lib/cli/router.py test/test_cli_tools_workbench.py`
- `pytest -q test/test_cli_tools_neovim.py test/test_cli_tools_workbench.py test/test_v2_cli_router.py test/test_v2_cli_parser.py` (`116 passed`)
- `git diff --check -- lib/cli/tools_runtime lib/cli/router.py test/test_cli_tools_workbench.py test/test_cli_tools_neovim.py docs/plantree/plans/managed-tool-windows`
- Follow-up alias checks: `pytest -q test/test_v2_cli_router.py test/test_cli_tools_workbench.py` (`58 passed`) and
  `/home/bfly/yunwei/ccb_source/ccb_test rich-install` exited 0.

Live source-wrapper validation from `/home/bfly/yunwei/test_ccb2` with isolated
`HOME=/home/bfly/yunwei/test_ccb2/source_home`:

- `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` confirmed the source
  wrapper, allowed test root, and non-source checkout cwd.
- `/home/bfly/yunwei/ccb_source/ccb_test tools install workbench --profile rich`
  exited 0 and produced `config_status: ok`, `yazi_status: ok`,
  `wezterm_status: ok`, `neovim_status: ok`, Markdown/PDF/video helper statuses
  `ok`, and `terminal_status: degraded` because the validation session was
  inside tmux.
- Sequential `enable`, `launch --dry-run`, `disable`, and final `enable`
  exited 0. `launch --dry-run` reported the generated `ccb-workbench terminal`,
  `ccb-yazi-rich "$PWD"`, and `ccb-nvim "$PWD"` command path.
- Direct wrapper validation succeeded:
  - `ccb-workbench commands` printed the Yazi and Neovim component commands.
  - `ccb-workbench files -V` reported `Yazi 26.5.6`.
  - `ccb-workbench edit --version` reported managed `NVIM v0.12.0-dev`.
- Generated helper validation succeeded:
  - `ccb-yazi-rich -V` reported `Yazi 26.5.6`.
  - `ccb-md-preview README.md` rendered readable Markdown.
  - `ccb-pdf-preview sample.pdf` produced PDF metadata and extracted text.
  - `ccb-video-preview sample.mp4` produced ffprobe stream metadata.
- WezTerm config validation succeeded with
  `wezterm --config-file .../workbench/profiles/wezterm/wezterm.lua show-keys`.
- Manifest inspection showed `enabled=True`, component keys for terminal,
  WezTerm, Yazi, Neovim, Markdown, PDF, and video helpers, and no generated
  `source_home/.config/yazi` or `source_home/.config/wezterm`.

Follow-up `rich-install` source-wrapper validation from
`/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME`:

- `/home/bfly/yunwei/ccb_source/ccb_test rich-install` exited 0.
- Output reported `rich_install_status: degraded` only because the validation
  session was inside tmux and rich image passthrough could not be verified.
- Output reported `enabled: True`, `config_status: ok`, `wezterm_status: ok`,
  `yazi_status: ok`, `ya_status: ok`, `neovim_status: ok`,
  `markdown_status: ok`, `pdf_text_status: ok`, `pdf_image_status: ok`,
  `video_metadata_status: ok`, and `video_thumbnail_status: ok`.
- `/home/bfly/yunwei/ccb_source/ccb_test rich-install --help` exited 0.

Follow-up visual encapsulation validation from `/home/bfly/yunwei/test_ccb2`:

- `ccb_test rich-install` regenerated the rich bundle under isolated
  `source_home` with the family-only WezTerm font fallback stack and
  `font_size = 10.5` / `line_height = 1.05`.
- `wezterm --config-file .../workbench/profiles/wezterm/wezterm.lua show-keys`
  exited 0, proving the generated visual config is readable by WezTerm.
- `ccb_test rich` launched the regenerated rich wrapper and reported
  `launch_status: started`.
- Applying the current tmux UI service to
  `ccb-test_ccb2-e809bff7` produced `pane-border-lines: heavy`,
  `pane-border-style: fg=#5d82d6`, and
  `pane-active-border-style: fg=#7aa2f7,bold` for the active
  `tool:rich` pane.
- Regression checks:
  `pytest -q test/test_cli_tools_workbench.py test/test_v2_cli_router.py test/test_v2_tmux_ui.py test/test_tmux_identity.py test/test_ccbd_namespace_additive_patch.py::test_apply_add_window_materializes_rich_alias_as_tool_pane`
  passed with `77 passed`.

Follow-up rich-media pane correction from `/home/bfly/yunwei/test_ccb2`:

- Generated WezTerm config now sets `warn_about_missing_glyphs = false`, keeps
  the compact family-only fallback stack, and includes `Noto Sans Symbols2`,
  WezTerm's built-in `Symbols Nerd Font Mono`, and `Unifont CSUR` so the
  observed `U+E6B8` private-use glyph is covered without adding unavailable
  Nerd Font families.
- Generated rich Yazi profile explicitly prepends Markdown, image, PDF, and
  video previewers; safe Yazi profile keeps text helpers but no longer emits
  chafa symbol art for images.
- CCB tmux server policy now applies `allow-passthrough on` and syncs
  `TERM`, `TERM_PROGRAM`, WezTerm/Kitty image-protocol variables, and CCB
  workbench variables. The WezTerm launcher also exports
  `CCB_WORKBENCH_TERMINAL_PROGRAM` and
  `CCB_WORKBENCH_TERMINAL_PROGRAM_VERSION`, and `ccb-yazi-rich` uses them to
  restore `TERM_PROGRAM=WezTerm` inside tmux panes where tmux would otherwise
  overwrite the value.
- The reserved `rich` layout alias now starts
  `CCB_WORKBENCH_PROFILE=rich CCB_WORKBENCH_FORCE_RICH=1 ccb-workbench files`,
  preventing tmux from forcing `ccb-yazi-rich` back to the safe profile.
- Validation:
  - `pytest -q test/test_cli_tools_workbench.py test/test_v2_project_namespace_backend.py ...` focused slice passed with `41 passed`.
  - `/home/bfly/yunwei/ccb_source/ccb_test rich-install` regenerated the
    isolated test bundle.
  - `wezterm --config-file .../workbench/profiles/wezterm/wezterm.lua ls-fonts`
    loaded without missing-font-family warnings.
  - Cold-starting `/home/bfly/yunwei/test_ccb2` with source `ccb_test` applied
    `allow-passthrough on` and the expanded `update-environment` list to the
    project tmux server.
  - The live `tool:rich` yazi process reported `YAZI_CONFIG_HOME=.../yazi-rich`,
    `TERM_PROGRAM=WezTerm`, and `TERM_PROGRAM_VERSION=20260615` under the
    isolated test launch.

## Known Limits

- Live validation can prove generated config, tmux passthrough policy, and rich
  profile selection. Direct pixel inspection of inline images still requires a
  live GUI WezTerm surface.
- `launch` has a dry-run path and a simple generated wrapper path; deeper
  CCBD-managed tool-window preset integration remains future work.
- The first slice tracks and closes recorded workbench launch PIDs, but GUI
  terminal lifecycle hardening still needs platform-specific validation.
