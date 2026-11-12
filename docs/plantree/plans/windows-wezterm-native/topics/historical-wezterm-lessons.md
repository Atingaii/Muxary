# Historical WezTerm Lessons

Date: 2026-06-15

## Evidence Sources

Local git history shows WezTerm was a real prior backend:

- `v4.1.3:lib/terminal.py` defines `WeztermBackend`.
- `v4.1.3:README.md` describes `TmuxBackend / WeztermBackend`.
- Commit `8d3fc57` released Windows WezTerm support in the v5 era.
- Commit `96debeb` fixed CWD-aware pane resolution for WezTerm multi-window
  routing.
- Commit `1dafed9` added Enter timing workarounds for older WezTerm.
- Commit `6f2bcaf` used bracketed paste plus `send-key Enter` for completion
  hook response.

## Reusable Design

The old backend used:

- `wezterm cli list --format json` for pane inventory;
- pane titles as coarse markers;
- CWD parsing from `file://...` pane metadata;
- `wezterm cli split-pane` for pane creation;
- `wezterm cli send-text` for prompt injection;
- `wezterm cli send-key` for raw key fallback;
- `wezterm cli get-text` for screen capture;
- `wezterm cli kill-pane` and `activate-pane` for pane lifecycle/focus;
- Windows/WSL path conversion and a cached WezTerm executable path.

These are still useful for a prototype.

## Lessons Not To Forget

### Title-Only Routing Is Unsafe

Commit `96debeb` documents the key bug: when multiple CCB workspaces exist in
separate WezTerm windows, a global title lookup can select the wrong pane. Any
new backend must combine project identity, slot identity, CWD or workspace
identity, and generation/epoch evidence.

### Enter Injection Was Fragile

Old code had to support:

- `send-text --no-paste` for single-line input;
- bracketed paste for multiline prompts;
- `send-key Enter` fallback;
- configurable delays and retries on Windows.

This should be treated as a first-class provider input policy, not an
incidental implementation detail.

### WSL Path Handling Was A Major Source Of Bugs

Old code included special cases for:

- `/wsl.localhost/...`
- `\\wsl.localhost\...`
- Windows drive paths;
- WSL `wslpath` conversion;
- launching Windows `wezterm.exe` from a safer cwd when called through WSL
  interop.

If the new goal is pure native Windows, these can be reduced. If the goal is
Windows WezTerm GUI controlling WSL provider processes, this complexity returns.

### Old Backend Scope Was Smaller

The old backend did not need to support the full current v7 surface:

- `ccbd` project namespace authority;
- versioned `[windows]` topology;
- sidebar and Comms state;
- managed tool windows;
- maintenance heartbeat;
- per-agent restart;
- provider-specific completion reliability;
- `ccb_self` diagnostics and recovery boundaries.

Therefore the historical backend is a reference, not a drop-in module.
