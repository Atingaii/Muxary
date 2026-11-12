# Feasibility And Architecture

Date: 2026-06-15

## Short Verdict

Current CCB can plausibly regain a Windows-native WezTerm backend, but it
should be treated as a new mux backend implementation, not as a direct return
to the old v4 architecture.

The old WezTerm path proved basic control-plane operations. Current v7 moved
far beyond that model: `ccbd` owns a project namespace, supervises mounted
agents, restores panes, tracks runtime authority, renders sidebar/tool windows,
and relies on tmux evidence for diagnostics. A WezTerm backend must satisfy
that higher contract.

## Why It Is Feasible

- WezTerm has a scriptable CLI for listing panes, splitting panes, sending
  input, capturing text, killing panes, activating panes, and setting titles.
- Old CCB v4/v5 already implemented a `WeztermBackend` with:
  - pane creation;
  - text input;
  - Enter key fallback;
  - WSL/Windows path handling;
  - title marker lookup;
  - text capture;
  - pane liveness checks.
- Current provider execution already has small abstraction seams such as
  `send_prompt_to_runtime_target`, `is_runtime_target_alive`, and a
  `TerminalBackend` interface. Those seams are too small for full v7 parity,
  but they provide migration anchors.
- WezTerm is a real Windows-native GUI and ConPTY host, so it can avoid the
  Unix tmux dependency that blocks native Windows.

## Why It Is Not A Simple Merge-Back

Current v7 assumes tmux in more places than the old backend contract covered:

- project namespace is represented as a tmux server/socket/session;
- `[windows]` topology maps to tmux windows and panes;
- sidebar and tool windows are materialized in tmux windows;
- runtime records store `tmux_socket_path`, `tmux_session_name`, `pane_id`,
  `tmux_window_id`, and `tmux_window_name`;
- recovery and diagnostics use tmux pane liveness and `capture-pane` style
  evidence;
- tmux user options carry CCB pane identity and style state;
- startup applies CCB-owned tmux server/window policy.

WezTerm does not share tmux's socket/server/window option model. It has its own
GUI/mux targeting rules and CLI metadata. Therefore the required move is:

```text
current v7 code
  -> MuxBackend contract
       -> TmuxBackend
       -> WezTermBackend
```

not:

```text
tmux command string -> wezterm command string
```

## Recommended Architecture

### 1. Keep `ccbd` Authority Unchanged

Do not let WezTerm facts become project truth. The project authority remains:

1. effective config;
2. lifecycle state;
3. lease/current daemon generation;
4. namespace state;
5. agent runtime records.

WezTerm facts are evidence only, like tmux facts are supposed to be.

### 2. Introduce A Real `MuxBackend` Contract

Minimum contract:

- `ensure_namespace(project_id, layout_signature, topology)`
- `destroy_namespace(project_id)`
- `attach_namespace(project_id)`
- `namespace_exists(project_id)`
- `list_panes(project_id)`
- `describe_pane(pane_ref)`
- `create_window(name)`
- `split_pane(parent, direction, percent, command, cwd)`
- `send_text(pane_ref, text)`
- `send_key(pane_ref, key)`
- `capture_pane(pane_ref, lines)`
- `kill_pane(pane_ref)`
- `activate_pane(pane_ref)`
- `pane_alive(pane_ref)`
- `set_title(scope, title)`
- `apply_ui_policy(capabilities)`

The contract must use backend-neutral references, not raw tmux `%pane` ids.

### 3. Define WezTerm Namespace Identity

Recommended identity stack:

- dedicated WezTerm `--class ccb-<project-id>` for GUI instance selection;
- dedicated WezTerm workspace name `ccb-<project-id>`;
- CCB-owned tab/window titles;
- CCB-owned pane title prefix containing project id, slot, role, and epoch;
- persisted namespace record under `.ccb/ccbd/namespace.json`.

Do not rely on pane title alone. Old history shows title-only lookup is unsafe
when multiple WezTerm windows share titles; CWD-aware matching was added later
to prevent cross-project routing.

### 4. Keep Provider Completion Mostly Provider-Native

Do not make WezTerm screen scraping the primary completion detector. Current
v7 has provider-native completion paths for Codex, Claude, Gemini, Kimi,
OpenCode, AGY, and others. WezTerm should provide:

- pane launch;
- input delivery;
- liveness evidence;
- bounded text capture for diagnostics;
- fallback pane-quiet detection where a provider truly lacks native events.

### 5. Windows Process Ownership Is Separate From Pane Ownership

Native Windows must add Job Object or equivalent process-tree ownership. Pane
death does not prove all provider children died, and `kill-pane` cannot be the
only cleanup mechanism.

## Possible First Demo Slices

### Demo A: Read-Only Capability Probe

Run WezTerm CLI capability checks and parse `list --format json`.

Value:

- proves installed WezTerm version and command surface;
- no mutation;
- safe on Linux/WSL/macOS/Windows.

Status:

- implemented in [../demos/wezterm_capability_probe.py](../demos/wezterm_capability_probe.py).

### Demo B: Offline Pane Ownership Fixture

Feed sample WezTerm pane JSON with duplicate titles and different CWDs into a
selector.

Value:

- reproduces the historical multi-window routing pitfall;
- proves a safer matching rule before live Windows work.

Status:

- implemented in [../demos/wezterm_capability_probe.py](../demos/wezterm_capability_probe.py).

### Demo C: Live Windows Fake Provider

In native Windows WezTerm:

1. spawn a CCB-classed WezTerm GUI/mux namespace;
2. split three panes running simple fake agents;
3. send text to one pane;
4. capture text;
5. kill and recreate one pane;
6. destroy the namespace.

Value:

- proves the backend control loop without provider complexity.

Status:

- not run in this Linux session.

## Shortcomings And Risks

- WezTerm CLI instance targeting is not the same as tmux socket targeting;
  multi-project isolation needs explicit class/workspace/title/namespace
  design.
- WezTerm pane metadata may not replace tmux user options one-for-one.
- `get-text` captures the screen/scrollback differently from
  `tmux capture-pane`; `ccb_self` diagnostics may need backend-specific
  evidence semantics.
- Input reliability is historically sensitive: old fixes added `send-key`
  Enter fallback, paste delays, and Windows-specific retries.
- Native Windows process cleanup needs Job Objects or another process-tree
  model; pane cleanup alone is insufficient.
- Some provider CLIs may behave differently under Windows ConPTY than under
  WSL/Linux tmux.
- Sidebar, managed tool windows, focus hooks, border styling, and copy-mode
  shortcuts will not be identical to tmux.
- The old v4 implementation had fewer current v7 responsibilities; copying it
  back would regress authority, recovery, and diagnostics design.
- Maintaining tmux and WezTerm as equal backends increases test matrix size and
  release risk.

## Recommendation

Proceed only as an opt-in experimental backend after the contract refactor.

Do not replace the current tmux path, and do not make WezTerm the Windows
default until a live Windows demo proves namespace isolation, pane operations,
provider process ownership, and at least one real provider end-to-end.
