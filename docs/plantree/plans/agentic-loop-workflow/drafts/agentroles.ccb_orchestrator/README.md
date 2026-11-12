# CCB Loop Orchestrator Draft

This draft materializes the `agentroles.ccb_orchestrator` RolePack for adaptive
single-lane one-to-four-workgroup execution. The role is immaculate and
reply-only: it returns one semantic route, compact notes, and when required one
complete orchestration bundle candidate.

Primary references:

- Config V3 execution routes always include an explicit candidate;
- Config V2 may omit it only for deterministic one-node compatibility;
- adaptive selection uses task complexity, cutability, independent scopes,
  dependencies, and effective capacity without targeting a preset count;
- the controller alone owns validation, binding, asks, integration, imports,
  topology, and lifecycle.

This draft is installable by path for source tests, but it is not a published
Agent Roles catalog entry.
