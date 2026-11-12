# Runtime Agent Groups And Macro Adjustment Requests

Date: 2026-07-02
Status: Partially superseded by
[017-flat-roles-and-role-collections.md](017-flat-roles-and-role-collections.md)
and
[019-orchestrator-triage-before-task-detailer.md](019-orchestrator-triage-before-task-detailer.md)

## Context

The workflow separates long-lived macro planning from short-lived task
refinement. Planner maintains durable plan-tree direction, while
`task_detailer` turns a selected macro task into an executable detail packet
only when orchestrator triage requests it. This split needs one durable
constraint:

- a detailer that discovers macro drift must not rewrite roadmap, decisions, or
  task authority directly.

The original version of this decision also proposed reusable group templates as
Agent Roles source objects. That source-layer design is superseded by Decision
017. CCB may still use runtime agent groups in Project Binding or topology
state, but Agent Roles source grouping belongs to Role Collections.

## Decision Still In Force

`task_detailer` may report macro drift only through a
`macro-adjustment-request` artifact. That artifact records the affected macro
task, requested change type, evidence, impact, urgency, and one recommended
adjustment. Planner decides whether to accept it and writes any authoritative
plan-tree change through `ccb plan` or the equivalent
script-owned surface.

CCB runtime topology may still model coupled runtime teams such as
`planning_group`, `execution_group`, or `workgroup-node1`. These are Project
Binding or runtime-state concepts. They must explicitly declare selected
members, roles, profiles, edges, gates, lifecycle, and release policy; they do
not derive runtime membership or authority from Role Collection ids.

## Consequences

- Planner stays macro-level and does not absorb implementation-detail packets.
- Detailer can surface necessary macro changes without mutating roadmap,
  decisions, task status, runtime topology, or provider state.
- Orchestrator may propose execution groups in the CCB runtime workflow graph,
  but those groups are not Agent Roles source objects and do not grant member
  permissions.
- Reconciler can load, lay out, drain, and release a runtime workgroup
  atomically while still preserving busy members.
- Agent Roles spec grouping should use Role Collections; `role.toml` remains
  a single-Role contract.

## Related

- [../topics/planner-role-design.md](../topics/planner-role-design.md)
- [../topics/task-detailer-role-design.md](../topics/task-detailer-role-design.md)
- [../topics/runtime-workflow-graph-and-reconciler.md](../topics/runtime-workflow-graph-and-reconciler.md)
- [../topics/role-class-naming-and-hierarchy.md](../topics/role-class-naming-and-hierarchy.md)
