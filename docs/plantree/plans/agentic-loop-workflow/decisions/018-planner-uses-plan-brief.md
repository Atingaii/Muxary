# 018 Planner Brief And Task Detailer Detail Docs

Date: 2026-07-02
Status: Accepted for planning

## Decision

The long-lived planner should primarily maintain a compact plan-tree brief,
not the body of detailed design documents.

For active plan roots, use a planner-owned brief document such as `brief.md`.
The brief carries macro objective, current phase, selected roadmap item,
accepted constraints, decision summary, open-question summary, links to detail
design, current task/detail packet links, readiness state, verification
summary, next owner, and last stable evidence.

In V1, `agentroles.task_detailer` owns both task-local execution detail and
the task-related detail design work surface. It may maintain task-scoped detail
design docs, scheme expansion, local technical research, source evidence,
detailed acceptance, detailed verification, and task-local clarification. This
keeps high-noise detail in a short-lived role that can be released after
summary import.

An independent detail-design role is deferred. It should not be part of the V1
RolePack or runtime path unless a later decision proves that task-scoped detail
work has become too broad for `task_detailer`.

## Authority

Planner may create and update the brief, accept or reject stable summary
backfill from `task_detailer`, publish macro tasks, and review
`macro-adjustment-request` artifacts.

Planner must not directly maintain large detail design bodies, source-evidence
maps, task-local clarification threads, detailed acceptance, detailed
verification, or worker handoff documents.

`task_detailer` may maintain task-scoped `topics/*` detail docs, source-backed
analysis, task-local clarification, and detail packets after orchestrator asks
for refinement. It must return stable summary backfill, detail links,
readiness, and any `macro-adjustment-request` artifacts for planner review. It
must not directly update roadmap, status, decisions, or the planner-owned
brief.

## Collection And Runtime Boundary

Role Collections may install related Roles and expose profiles. They do not
participate in runtime launch. CCB runtime topology must explicitly declare
selected roles, members, edges, gates, lifecycle, and release policy; it must
not load agents by Collection id.

## Related

- [017-flat-roles-and-role-collections.md](017-flat-roles-and-role-collections.md)
- [016-agent-groups-and-macro-adjustment-request.md](016-agent-groups-and-macro-adjustment-request.md)
- [../topics/planner-plan-tree-brief-and-detail-boundary.md](../topics/planner-plan-tree-brief-and-detail-boundary.md)
