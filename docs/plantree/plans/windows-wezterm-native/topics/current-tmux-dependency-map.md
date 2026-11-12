# Current Tmux Dependency Map

Date: 2026-06-15

## Current Contract Anchors

Current v7 behavior is explicitly tmux-centered:

- [../../../../ccbd-startup-supervision-contract.md](../../../../ccbd-startup-supervision-contract.md)
  defines CCB-managed tmux servers as project-scoped backend resources.
- [../../../../ccb-config-layout-contract.md](../../../../ccb-config-layout-contract.md)
  defines compact and `[windows]` layout semantics in tmux terms.
- [../../../../ccbd-project-namespace-lifecycle-plan.md](../../../../ccbd-project-namespace-lifecycle-plan.md)
  models one project namespace as a dedicated tmux server/socket/session.
- [../../../baseline/runtime-flows.md](../../../baseline/runtime-flows.md)
  records startup as `ccbd` materializing a project tmux namespace.

## Code-Level Hotspots

The current codebase has a small `TerminalBackend` abstraction, but production
resolution returns only `TmuxBackend`:

- `lib/terminal_runtime/backend_types.py`
- `lib/terminal_runtime/api.py`
- `lib/terminal_runtime/api_selection.py`
- `lib/terminal_runtime/detect.py`
- `lib/terminal_runtime/tmux_backend.py`

The project namespace controller is tmux-specific:

- `lib/ccbd/services/project_namespace_runtime/backend.py`
- `lib/ccbd/services/project_namespace_runtime/controller.py`
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py`
- `lib/ccbd/services/project_namespace_runtime/topology_plan.py`
- `lib/ccbd/services/project_namespace_runtime/reflow.py`
- `lib/ccbd/services/project_namespace_runtime/destroy.py`

Runtime execution and diagnostics assume pane-backed terminal semantics:

- `lib/provider_execution/common_runtime/terminal.py`
- `lib/provider_execution/service_runtime/start.py`
- `lib/provider_execution/service_runtime/polling.py`
- `lib/ccbd/services/health_assessment/tmux.py`
- `lib/ccbd/services/health_assessment/tmux_runtime/`
- `lib/provider_core/tmux_ownership.py`
- `lib/provider_core/tmux_ownership_runtime/`

UI and foreground attach are tmux-specific:

- `config/tmux-ccb.conf`
- `config/ccb-tmux-on.sh`
- `config/ccb-tmux-off.sh`
- `lib/cli/services/tmux_ui.py`
- `lib/ccbd/project_focus/tmux.py`

## Required Refactor Boundary

Before a production WezTerm backend, these names should stop leaking above the
backend layer:

- `tmux_socket_path`
- `tmux_socket_name`
- `tmux_session_name`
- `tmux_window_id`
- `tmux_window_name`
- raw `%pane` tmux pane ids
- tmux user options as the only identity store

They can remain in tmux-specific backend records, but the upper layers need
backend-neutral concepts:

- `mux_backend_kind`
- `namespace_ref`
- `window_ref`
- `pane_ref`
- `slot_ref`
- `backend_capabilities`
- `identity_evidence`

## Stable Semantics That Must Survive

- One `.ccb` anchor owns one authoritative `ccbd`.
- Effective config is the desired-state authority.
- Mux facts are evidence, not authority.
- Pane death is supervised by `ccbd`.
- `ccb kill` is project-level cleanup.
- `ccb restart <agent>` restarts one slot without mutating unrelated slots.
- Provider-native completion remains provider-owned.
- Tool windows do not become agents.
- `ccb_self` can read pane evidence but must not use raw destructive mux
  mutation.
