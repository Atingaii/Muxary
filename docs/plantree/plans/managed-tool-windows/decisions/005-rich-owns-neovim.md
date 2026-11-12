# Rich Owns Neovim

Date: 2026-06-15

## Context

The earlier managed-tool plan added a standalone CCB-managed Neovim/LazyVim
tool path. That was useful during exploration because it proved isolated
profiles, folder opening, Markdown rendering, opener behavior, and terminal
capability checks.

The product direction has changed: the richer editor/file/media surface is now
the optional rich workbench. Normal CCB should stay focused on the core
agent/tmux/sidebar runtime and should not install or update a standalone
Neovim tool.

## Decision

Neovim/LazyVim is no longer a normal CCB feature. It is an internal component of
the optional rich bundle.

User-facing consequences:

- `ccb install` and ordinary `ccb update` do not install, update, or repair
  Neovim/LazyVim.
- `ccb update rich` is the explicit lifecycle entry for installing or updating
  the rich bundle, including its managed LazyVim/Neovim profile.
- `ccb rich` may launch only when the rich bundle is installed and enabled; if
  it is missing, it should tell the user to run `ccb update rich`.
- Existing lower-level Neovim commands are removed from the public normal CCB
  command surface.
- `ccb rich-install` is removed; it is not kept as a compatibility alias.
- The `rich` layout alias remains a non-agent tool alias and must not create
  provider runtime, ask targets, completion records, or Comms rows.

Implementation consequences:

- Remove install/update post-hooks that call standalone Neovim provisioning.
- Remove or hide `ccb tools install/update/doctor neovim` from the public
  normal CCB surface.
- Keep the isolated Neovim implementation reusable internally by rich until it
  is either renamed or absorbed into the workbench runtime.
- Update docs and tests so acceptance is based on `ccb update rich`, not
  automatic Neovim provisioning.

## Compatibility

Existing generated `ccb-nvim` files may remain on disk after upgrade. They are
treated as old optional tool artifacts, not as normal CCB runtime authority.
Rich install/update may reuse or regenerate them under CCB-owned tool paths.

## Follow-Up

- Add `ccb update rich` parsing and route it to rich bundle provisioning.
- Make normal `ccb update` skip rich and Neovim work unless a rich-specific
  target is provided.
- Remove `ccb rich-install` routing and help text.
