# Planner Brief And Task Detailer Detail Docs

Date: 2026-07-02

## Purpose

The long-lived planner needs one compact plan-tree work surface. It should not
maintain many large detail design documents directly.

Each active plan root should therefore have a planner-owned brief document. The
brief is the macro index and current planning handoff. It keeps stable
summaries and links; it does not contain the detailed design body.

In V1, `task_detailer` is an orchestrator-demanded detail document owner for a
selected macro task. It owns the high-noise task-scoped detail docs, execution
packet, local technical research, source evidence, detailed acceptance,
detailed verification, and task-local clarification. After refinement, it
returns the detail packet to orchestrator and returns stable summary backfill,
detail links, readiness, and any `macro-adjustment-request` for planner
review.

Recommended plan-root shape:

```text
docs/plantree/plans/<plan>/
  README.md                 # entrypoint and file map
  brief.md                  # planner macro work surface
  roadmap.md                # durable roadmap state
  open-questions.md         # unresolved macro questions
  decisions/                # accepted durable decisions
  topics/                   # task-scoped detail docs and technical expansion
  history/                  # accepted evidence and archived detail
```

`README.md` remains the discoverability entrypoint. `brief.md` is the planner's
main editable planning surface for active work.

## Long-Lived Context Exception

`planner` is one of the two deliberate long-lived context holders in the
workflow, alongside `frontdesk`. This is an exception for macro planning state,
not permission to accumulate implementation detail.

Planner's retained context should stay limited to coarse plan shape: current
objective, roadmap/TODO state, accepted constraints, decisions, open questions,
brief summaries, readiness state, and stable evidence links. It should consume
`task_detailer`, worker, reviewer, and round-review outputs through compact
imported artifacts. It should not keep raw task-local clarification threads,
source-evidence bodies, worker logs, or review transcripts as conversational
memory.

This boundary keeps planner useful across many tasks without forcing
orchestrator, detailer, workers, or reviewers to become long-lived memory
owners. Those roles are expected to be fresh per activation and to rehydrate
from planner/task artifacts only.

## Brief Schema

The brief should stay compact and link-rich.

```markdown
# <Plan Name> Brief

Date: <YYYY-MM-DD>
Status: planning|ready|detail_ready|running|partial|blocked|done

## Purpose

<Why this plan exists, in a few sentences.>

## Current Phase

<One current phase and what changed recently.>

## Macro Objective

<The durable user/business objective.>

## Active Roadmap Item

- Item: <roadmap item title>
- Ref: <roadmap.md#...>
- Owner: planner|orchestrator|task_detailer

## Accepted Constraints And Non-Goals

- <constraint or non-goal, with refs when useful>

## Decision Summary

- <short summary> ([decision](decisions/NNN-example.md))

## Open Question Summary

- <short question/status> ([open questions](open-questions.md))

## Detail Links

- <summary of task-scoped detail area> ([detail doc](topics/example-detail.md))

## Current Task And Detail Packet

- Macro task: <task ref>
- Detail packet: <detail packet ref, if accepted>
- Detail readiness: ready|needs_clarification|blocked|not_ready

## Readiness State

<Macro readiness plus whether task detail is required.>

## Verification Summary

<High-level verification contract and links to detailed verification docs.>

## Next Owner / Handoff

<Next role or script-owned surface.>

## Last Stable Evidence

- <date, evidence ref, short meaning>
```

## Planner Authority

Planner may:

- create and update `brief.md`;
- maintain macro objective, current phase, active roadmap item, constraints,
  non-goals, decision summaries, open-question summaries, task links,
  readiness summary, verification summary, next owner, and last stable
  evidence;
- decide whether to accept stable summary backfill from `task_detailer`;
- publish macro task refs and handoff refs for detail refinement;
- review `macro-adjustment-request` artifacts and request script-owned plan
  updates when accepted.
- own the compact global architecture map, cross-task dependency summary,
  invariants, acceptance coverage, and integration milestones used by the
  Decision 022 global-consistency gate.

Planner must not:

- maintain the body of detail design documents under `topics/*`;
- rewrite local technical investigation, source evidence maps, detailed
  acceptance, detailed verification, or worker handoff docs as planner-owned
  state;
- turn task-local clarification into long-lived planner conversation context;
- accept a detail summary or macro adjustment as authority before script-owned
  import or decision handling.
- read every detail body merely to decide whether local work is globally safe;
  the detailer must provide a compact global-impact artifact with evidence
  refs.

## Task Detailer Detail Docs Boundary

Detail expansion belongs to `task_detailer` in V1.

`task_detailer` owns task-scoped detail docs:

- `topics/*` docs that expand the selected macro task;
- scheme expansion and local technical research;
- source evidence maps and inspected refs;
- detailed options and tradeoffs for the task;
- detailed acceptance and verification expansion;
- worker/reviewer handoff material;
- task-local clarification artifacts;
- stable summary backfill for the brief or task document;
- mandatory compact global-impact classification, including an explicit
  `none` result when no macro surface changes;
- `macro-adjustment-request` when detail evidence invalidates a macro
  assumption.

This is intentionally high-noise work. The role is short-lived, so its
conversation context can be released after artifacts are imported and linked.
The retained plan-tree value is the stable summary, the detail document links,
the detail packet, and any macro adjustment request.

An independent detail-design role is deferred. V1 should not introduce one as
a required RolePack member or runtime handoff.

## Stable Summary Backfill

`task_detailer` should not edit `brief.md` directly. It should return a compact
summary artifact:

```json
{
  "schema": "ccb.plan_brief_update_summary.v1",
  "plan": "agentic-loop-workflow",
  "detail_role": "task_detailer",
  "detail_refs": [
    "docs/plantree/plans/agentic-loop-workflow/topics/example-detail.md"
  ],
  "summary": "The task detail work confirms the current macro path.",
  "decision_refs": [],
  "open_question_refs": [],
  "task_refs": [],
  "verification_summary": "Use existing fake-provider closure smoke.",
  "macro_adjustment_request_ref": null,
  "recommended_brief_patch": [
    {
      "section": "Detail Links",
      "text": "Add link to example detail design."
    }
  ]
}
```

Planner decides whether this summary is stable enough for the brief. If it is
not stable, the task detail docs remain linked as work in progress rather than
absorbed into the macro summary.

Stable summary backfill remains optional because not every local fact belongs
in long-lived planner context. Global-impact classification is separate and
mandatory: it exists to prove that the local detail packet was checked against
planner-owned interfaces, dependencies, invariants, and acceptance coverage.

## Compact Planner Import Policy

Planner consumes task evidence through compact imported artifacts, not by
copying detail bodies into planner-owned state.

The compact planner import evidence kinds are:

- `detail_summary`: stable summary backfill from detail work. It may inform
  `brief.md`, roadmap/status handoff text, decision links, open-question links,
  and task refs after planner review. It must not copy detail design bodies,
  source-evidence maps, task-local clarification, or worker handoff detail into
  the brief or roadmap.
- `macro_adjustment_request`: a request for planner review. It may propose one
  macro update, but importing it must not mutate roadmap, decisions,
  open questions, task status, or next owner by itself. Planner either rejects
  it with a short reason or requests a script-owned plan update.
- `round_summary`: compact round result evidence. It is imported only through
  script-owned round import, not generic artifact import. Planner may use it to
  rehydrate the brief, update a compact status handoff, or plan the next task
  after explicit review.

The script-side import contract records compact policy metadata on these
artifacts:

```text
planner_compact_import.policy = planner_compact_import
planner_compact_import.allowed_updates =
  brief, roadmap_status_handoff, decision_links, open_question_links, task_refs
```

Forbidden planner-owned imports remain:

- detail design body;
- source-evidence map;
- task-local clarification thread or transcript;
- worker/reviewer handoff detail;
- provider reply text as authority.

`round_summary` has one additional guard: `ccb plan task-artifact --kind
round_summary` is rejected. A round result must pass through `ccb plan
task-import-round`, which binds the loop id, round result, actor metadata, and
status transition in one script-owned operation.

## Cleanup And Retention Rules

After `task_detailer` finishes or blocks:

- retain detail docs, detail packet, source evidence, clarification summaries,
  and macro adjustment requests by link;
- import only compact stable summaries into the brief or task document;
- release or clear the short-lived task-detailer context after artifact import
  and any required user clarification;
- do not convert task-local clarification or detailed research into long-lived
  planner memory;
- leave unresolved macro drift as a planner-owned
  `macro-adjustment-request`, not as an implicit roadmap change.

## Collection And Runtime Boundary

Role Collections may install `planner`, optional `task_detailer`, and
supporting reviewers together. Collections do not decide which runtime agents
are mounted for a task, and they do not imply task-detailer activation.

Runtime launch remains explicit CCB Project Binding or topology state. The
orchestrator/topology proposal must declare concrete roles, members, edges, and
gates; it must not load a group by Collection id.

## Validation Prompts

Positive prompts:

- Ask planner to create a brief for a plan root with roadmap, decisions, and
  detail links.
- Ask `task_detailer` to consume the brief, expand task-scoped detail docs,
  and produce a detail packet plus stable summary backfill.

Negative prompts:

- Ask planner to maintain a long technical design body under `topics/*`.
- Ask `task_detailer` to keep a long-lived planning conversation after
  summary import and release.
- Ask `task_detailer` to update roadmap directly after finding macro drift.
