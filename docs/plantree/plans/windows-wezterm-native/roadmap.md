# Windows WezTerm Native Roadmap

Date: 2026-06-15

## Done

- Confirmed current v7 public and internal contracts are tmux-centered:
  startup materializes a project tmux namespace, `[windows]` maps to managed
  tmux windows, and provider runtime records store tmux pane/session evidence.
- Confirmed an existing Windows-native design exists for `psmux`; that design
  explicitly prefers `psmux` first because it keeps tmux-family semantics.
- Confirmed old v4/v5 history contained `WeztermBackend` and Windows WezTerm
  fixes for pane creation, input injection, WSL path handling, Enter timing,
  and CWD-aware pane ownership.
- Verified current WezTerm CLI on this host exposes the required command
  surface for a prototype: `list`, `split-pane`, `send-text`, `get-text`,
  `kill-pane`, and `activate-pane`.
- Added a read-only capability probe and offline CWD-routing fixture under
  [demos/wezterm_capability_probe.py](demos/wezterm_capability_probe.py).

## In Progress

- Shape the backend contract and feasibility plan for a Windows-native
  WezTerm runtime without changing the production tmux path.

## Next

1. Run the demo probe in a real Windows WezTerm GUI session and record output.
2. Build a throwaway `WezTermMuxBackend` prototype outside the production
   provider path with read-only `list_panes`, `capture_pane`, and `pane_alive`.
3. Add a synthetic unit-test matrix that feeds WezTerm `list --format json`
   records into namespace ownership selection.
4. Prototype project namespace identity:
   - dedicated WezTerm `--class`;
   - dedicated workspace name;
   - CCB-owned window/tab/pane title prefix;
   - project id stored in generated WezTerm config or pane title/user vars if
     available.
5. Run a live Windows demo with fake providers:
   - create namespace;
   - create three panes;
   - send prompt text;
   - capture pane text;
   - kill one pane and respawn it;
   - destroy namespace.
6. Only after fake-provider success, test one real provider with native
   Windows process ownership and completion detection.

## Deferred

- Defaulting to WezTerm for any platform.
- Full parity with tmux copy-mode, key bindings, border styling, and sidebar
  rendering.
- Rich WezTerm UI config generation beyond the minimal namespace identity
  required for safe backend control.
- Replacing the existing `psmux` Windows plan.
- Supporting all provider CLIs on native Windows before Codex/Claude/Kimi fake
  and single-provider tests pass.

## Current Gate

Planning gate only. No production code should be modified until:

- the backend contract is explicit;
- the live Windows WezTerm demo proves namespace and pane operations;
- provider process-tree ownership on Windows is designed;
- tmux behavior remains covered by existing tests.
