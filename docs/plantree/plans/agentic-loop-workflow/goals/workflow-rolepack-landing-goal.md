# Workflow RolePack Landing Goal

Date: 2026-06-27
Status: Historical / superseded by flat Role naming

## Goal

Land the first CCB workflow RolePack draft set for external Agent Roles spec
iteration while preserving the simple-kernel/flexible-agent design rule.

This goal records the first legacy `agentroles.ccb_*` draft landing slice. The
current mainline Role naming is described in
[../topics/role-class-naming-and-hierarchy.md](../topics/role-class-naming-and-hierarchy.md)
and [../decisions/019-orchestrator-triage-before-task-detailer.md](../decisions/019-orchestrator-triage-before-task-detailer.md):
use `agentroles.planner` for macro planning, treat `agentroles.ccb_planner` as
legacy compatibility, and activate `agentroles.task_detailer` only through
orchestrator triage.

The landing slice covers:

1. common authority rule and shared artifact templates;
2. `agentroles.ccb_planner`;
3. `agentroles.ccb_plan_reviewer`;
4. `agentroles.ccb_round_checker`;
5. tightened `agentroles.ccb_orchestrator`;
6. `agentroles.ccb_clarification_broker`;
7. simplified `agentroles.ccb_frontdesk`, `agentroles.ccb_worker`, and
   `agentroles.ccb_checker`.

## Authority Boundary

Every RolePack must include the common rule:

```text
You may author semantic artifacts and recommend transitions.
You must not directly edit authoritative state.
Use CCB-owned commands or host-provided skill wrappers for authoritative writes.
```

Roles can produce semantic artifacts, ask requests, reviews, and reports.
Scripts remain responsible for committing or rejecting task indexes, task
status, current_loop, capacity records, pane/window state, provider sessions,
and loop authority files.

## Landing Requirements

- Each role has `role.toml`, `README.md`, `memory.md`, CCB adapter metadata,
  CCB adapter memory, at least one skill, and role-specific templates.
- P0 roles have explicit machine-readable result schemas:
  - planner readiness: `ready|needs_clarification|blocked|not_ready`
  - plan reviewer: `approve|needs_revision|needs_clarification|blocked`
  - round checker: `pass|rework_node|partial|replan_required|global_blocker`
  - orchestrator aggregation: `complete|partial|blocked|replan_required`
- P1 roles are intentionally simple:
  - frontdesk handles user-facing intake/reporting;
  - worker handles one bounded work item;
  - checker handles one node-level quality gate.
- Orchestrator keeps the CCB runtime adapter split and uses only
  `orchestrator-capacity` for dynamic capacity.

## Verification

Targeted test:

```bash
PYTHONPATH=lib pytest -q test/test_orchestrator_rolepack.py
```

Expected result after landing:

```text
7 passed
```

The test verifies:

- all eight workflow RolePacks translate through the current preview
  manifest adapter;
- supported providers include `codex`, `claude`, `qwen`, and `zai`;
- role skills project through the CCB role lookup path;
- every role memory includes the shared authority rule;
- required templates exist;
- orchestrator and round checker share the same non-downgrade result language.
