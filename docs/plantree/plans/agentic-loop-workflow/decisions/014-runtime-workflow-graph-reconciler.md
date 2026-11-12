# 014 Runtime Workflow Graph And Reconciler

Date: 2026-06-30
Status: Accepted for planning

## Decision

Dynamic agent loading, unloading, parking, layout placement, and call ordering
should be driven by a committed runtime workflow graph, not by `orchestrator`
directly calling agent lifecycle commands.

`orchestrator` may produce a topology proposal that describes:

- required agents and role profiles;
- node grouping;
- information-flow edges;
- call order and dependencies;
- input and output artifact refs;
- lifecycle and release gates.

CCB scripts validate and commit the proposal as desired topology. A topology
reconciler then compares desired topology with observed runtime state and
applies the minimal safe changes.

## Runtime Boundary

The authority chain is:

```text
orchestrator semantic proposal
  -> ccb loop topology validate/propose/commit
  -> agent_topology.desired.json revision
  -> topology reconciler
  -> agent lifecycle, layout, capacity, ask dispatch readiness
  -> agent_topology.observed.json and events
```

`orchestrator` must not directly write desired topology, runtime state,
capacity state, lifecycle records, tmux layout state, or `.ccb/ccb.config`.

## Consequences

- The system gains a durable, inspectable graph for both structure and
  information flow.
- Runtime changes become diffable and replayable.
- Load/release failures can be represented as observed-state drift instead of
  hidden role-local failure.
- Existing `loop.role_profiles`, `ccb loop capacity`, dynamic lifecycle, and
  layout commands remain useful as lower-level reconciler mechanisms.
- The preferred orchestrator-facing skill changes from
  `orchestrator-capacity` to `orchestrator-topology`.

## V1 Trigger Model

V1 should use explicit reconciliation:

```bash
ccb loop topology commit --loop-id <id> --proposal <id> --apply --json
ccb loop topology reconcile --loop-id <id> --json
```

Avoid a background file watcher in V1. `loop runner --once` should reconcile at
round start, before dispatch, after round drain, and during release cleanup.

V2 may add a ccbd reconciler that watches topology revision changes with
debounce and loop-level locks.

## Non-Goals

- Do not make scripts infer semantic work split from Markdown.
- Do not let topology files replace planner artifacts or task packets.
- Do not let `orchestrator` bypass validation by writing runtime files.
- Do not implement arbitrary unbounded team graphs.
- Do not kill busy agents merely because desired topology removed them.
