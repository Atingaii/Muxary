# Rich Layout Alias Slice

Date: 2026-06-15

## Scope

Landed a simple `rich` layout alias so the CCB-owned rich workbench can be
mounted in existing `[windows]` layouts like provider panes, without becoming
an agent or participating in ask/Comms.

Example:

```toml
version = 2
entry_window = "main"

[windows]
main = "agent1:codex, rich"
rich_page = "rich"
```

## Landed Behavior

- `rich` is a reserved layout tool alias.
- `rich` must not declare a provider suffix such as `rich:codex`.
- `rich` is excluded from `config.agents`, `default_agents`, ask targets, and
  provider runtime authority.
- `rich` remains in the window layout so it receives the same tmux pane layout
  treatment as provider panes.
- Namespace materialization starts the `rich` pane with
  `CCB_WORKBENCH_PROFILE=rich CCB_WORKBENCH_FORCE_RICH=1 ccb-workbench files`,
  so Yazi does not silently fall back to the safe profile inside tmux.
- The pane receives CCB tool identity:
  - `@ccb_role=tool`
  - `@ccb_slot=tool:rich`
  - `@ccb_window=<containing-window>`
  - `@ccb_managed_by=ccbd`
- A window may contain both provider panes and `rich`, or can be a page/window
  made only from `rich`.

## Verification

Automatic checks:

- `python3 -m py_compile` for changed config/model/namespace files.
- Focused tests for config loading, namespace topology, additive namespace
  materialization, project view, reload patch/apply, workbench, and Neovim:
  `235 passed`.
- `git diff --check -- lib/agents lib/ccbd test docs/plantree/plans/managed-tool-windows`.

Live source-wrapper validation from `/home/bfly/yunwei/test_ccb2`:

- Created a manual validation project at
  `/home/bfly/yunwei/test_ccb2/rich-alias-manual`:

  ```toml
  version = 2
  entry_window = "main"

  [windows]
  main = "agent1:codex, rich"
  rich_page = "rich"
  ```

- Ran
  `/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/rich-alias-manual config validate`
  with isolated `HOME=/home/bfly/yunwei/test_ccb2/source_home` and
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`.
- Validation exited 0 and reported `config_status: valid`, `default_agents:
  agent1`, and `agents: agent1`, proving `rich` was not treated as a provider
  agent.

## Known Limits

- This slice keeps reload behavior conservative. Adding a new window/page that
  contains `rich` is covered by additive namespace tests; changing the layout
  of an already-mounted existing window still follows the existing reload
  safety policy.
- `rich` assumes the workbench bundle has been installed or is available on
  `PATH` as `ccb-workbench`.
