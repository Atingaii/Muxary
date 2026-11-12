# Windows WezTerm Native Plan

Date: 2026-06-15

## Purpose

Plan whether current CCB can regain a Windows-native WezTerm backend without
tmux-based communication, while preserving the current v7 project authority,
supervision, config, provider runtime, ask/reply, sidebar, tool-window, and
maintenance semantics.

This is a planning root, not an implementation commitment. It exists because
old v3/v4/v5 CCB had a `WeztermBackend`, while current v7 is intentionally
tmux-centered.

## File Map

- [roadmap.md](roadmap.md): phase plan, current status, gates, and deferred
  work.
- [open-questions.md](open-questions.md): unresolved product and technical
  questions.
- [topics/feasibility-and-architecture.md](topics/feasibility-and-architecture.md):
  feasibility verdict, architecture options, migration strategy, and known
  shortcomings.
- [topics/current-tmux-dependency-map.md](topics/current-tmux-dependency-map.md):
  current v7 tmux assumptions that must be abstracted before WezTerm can be a
  first-class runtime backend.
- [topics/historical-wezterm-lessons.md](topics/historical-wezterm-lessons.md):
  reusable lessons from the old WezTerm implementation.
- [topics/demo-validation.md](topics/demo-validation.md): local demo/probe
  design and current evidence.
- [demos/wezterm_capability_probe.py](demos/wezterm_capability_probe.py):
  read-only capability probe and offline CWD-routing fixture.
- [history/demo-run-2026-06-15.md](history/demo-run-2026-06-15.md):
  current demo output and interpretation.

## Related Sources

- [../../../ccbd-startup-supervision-contract.md](../../../ccbd-startup-supervision-contract.md)
- [../../../ccb-config-layout-contract.md](../../../ccb-config-layout-contract.md)
- [../../../ccbd-project-namespace-lifecycle-plan.md](../../../ccbd-project-namespace-lifecycle-plan.md)
- [../../../ccbd-windows-psmux-plan.md](../../../ccbd-windows-psmux-plan.md)
- [../managed-tool-windows/README.md](../managed-tool-windows/README.md)
- [../../baseline/runtime-flows.md](../../baseline/runtime-flows.md)

## Scope

In scope:

- A Windows-native WezTerm backend for the project mux/control plane.
- A backend contract that can support tmux and WezTerm without leaking
  backend-specific details into provider runtimes.
- Mapping current CCB v7 requirements onto WezTerm CLI and mux concepts.
- Isolated demos that prove capability shape and old routing pitfalls.
- A staged path that avoids destabilizing current Linux/macOS/WSL tmux users.

Out of scope for the first planning slice:

- Replacing the current tmux backend.
- Shipping Windows-native support without live Windows GUI validation.
- Rewriting provider-native completion detection.
- Making WezTerm the default backend on Linux/macOS.
- Reusing old v4 WezTerm code verbatim.

## Initial Verdict

Feasible, but only as a second backend behind a real mux backend contract.

The old WezTerm backend proves that pane creation, input, focus, text capture,
and liveness are possible. The current v7 system, however, now depends on a
project-scoped daemon, namespace ownership, canonical windows, sidebar state,
tool windows, heartbeat, restart, completion reliability, and stronger
authority/evidence separation. Those semantics cannot be recovered by a direct
tmux-command-to-WezTerm-command substitution.

The safest route is:

1. define a `MuxBackend` contract from current tmux behavior;
2. move existing tmux code behind `TmuxBackend`;
3. add `WezTermBackend` as an experimental Windows-only backend;
4. prove namespace, pane ownership, send/capture, restart, and kill on real
   Windows;
5. only then expose it as an opt-in runtime backend.
