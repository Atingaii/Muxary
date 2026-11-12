# Decision 006: Configured Role Profiles And Capacity Skill

Date: 2026-06-24

## Status

Superseded as the orchestrator-facing contract by
[014 Runtime Workflow Graph And Reconciler](014-runtime-workflow-graph-reconciler.md).
Retained as the lower-level capacity/profile substrate for topology
reconciliation.

## Context

The workflow needs dynamic execution nodes, but letting `orchestrator` directly
edit `.ccb/ccb.config`, run raw `ccb reload`, or kill panes would merge semantic
task routing with runtime authority. Current CCB already has guarded reload
support for append-only add-agent/add-window and idle remove-agent, but that
surface is config-oriented rather than loop-oriented.

The user wants each dynamic role's provider, model, and thinking strength to be
declared in config, then loaded or released through parameterized scripts that
can be wrapped as a skill.

## Decision

Use configured role profiles plus a narrow capacity command surface as the
runtime substrate.

- `.ccb/ccb.config` declares allowed `loop.role_profiles`.
- `orchestrator` proposes a topology graph from task complexity, including
  concrete profile needs.
- CCB topology scripts may use `ccb loop capacity ensure/status/release`
  internally or expose it as a compatibility/debugging surface.
- CCB scripts and ccbd own validation, locking, runtime writes, reload
  transactions, busy checks, and release cleanup.

`orchestrator` does not have direct dynamic load/unload authority through the
capacity API. It submits topology intent; CCB commits desired state and the
reconciler applies capacity, lifecycle, and layout changes.

## Consequences

Positive:

- Users keep policy control over provider, model, thinking, workspace, max
  instances, and reuse behavior.
- `orchestrator` can remain a short-context semantic dispatcher.
- Runtime mutation stays centralized and testable.
- Existing reload internals can be reused without exposing raw reload to roles.
- Capacity blockers become structured loop evidence instead of silent fallback.
- The same profile policy can support topology-driven reconciliation.

Tradeoffs:

- CCB must preserve or adapt the `ccb loop capacity` command layer as a lower
  substrate while adding topology proposal/commit/reconcile above it.
- `thinking` needs provider-specific adapter mapping.
- The design must decide whether V1 uses a daemon-side transient overlay or a
  generated config block over existing reload.
- Sidebar and cleanup semantics for generated agents need explicit UX rules.

## Boundary

This decision does not authorize:

- raw `ccb reload` from orchestrator;
- raw `ccb kill` from orchestrator;
- direct config edits by orchestrator;
- direct `ccb loop capacity ensure/release` from normal orchestrator workflow
  once topology commands are available;
- unbounded generated agents;
- provider/model/thinking values outside declared profiles;
- busy unload without a later explicit policy.
