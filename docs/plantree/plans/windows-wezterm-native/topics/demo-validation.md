# Demo Validation

Date: 2026-06-15

## Demo Goals

The planning slice needs two kinds of evidence:

1. capability evidence: is the WezTerm CLI surface present on the current
   machine?
2. model evidence: can old multi-window routing pitfalls be expressed and
   tested without a live Windows GUI?

The current Linux session cannot prove native Windows GUI behavior, but it can
run read-only checks and an offline fixture.

## Probe

Run:

```bash
python docs/plantree/plans/windows-wezterm-native/demos/wezterm_capability_probe.py
```

The probe:

- records `wezterm --version`;
- checks `wezterm cli --help` for required subcommands;
- runs `wezterm cli --no-auto-start list --format json`;
- treats absence of a live GUI/mux session as a non-fatal live-demo blocker;
- runs an offline fixture with duplicate pane titles and different CWDs to
  validate CWD-aware pane selection.

## Current Result

See [../history/demo-run-2026-06-15.md](../history/demo-run-2026-06-15.md).

Summary:

- WezTerm binary exists on this host.
- CLI capability surface is present.
- No active GUI/mux instance is reachable in this Linux shell.
- Offline CWD-aware selection passes.

## Missing Live Evidence

Still required before implementation readiness:

- native Windows `wezterm cli list --format json` with multiple CCB projects;
- live `split-pane` returning a pane id;
- live `send-text` plus `send-key Enter`;
- live `get-text` with provider-like TUI content;
- live pane kill/respawn;
- native Windows process-tree cleanup proof.
