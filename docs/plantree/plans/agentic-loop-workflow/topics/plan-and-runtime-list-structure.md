# Plan And Runtime List Structure

Date: 2026-06-24

## Principle

Follow the useful Trellis idea: workflow truth should live outside model
conversation and be advanced through scripts. Adapt it for CCB: agents are
visible, `ask` jobs are inspectable, and runtime state must carry job, node,
branch, and round evidence.

The split is:

- Durable plan packets live in `docs/plantree` and are human-reviewable.
- Runtime loop lists live under `.ccb/runtime/loops` and are machine-owned.
- Agents may propose content and write draft artifacts.
- CCB scripts write authoritative status, indexes, owner, phase, and transition
  records.

## Layer 1: Durable Plan Tree

Plan roots keep stable context:

```text
docs/plantree/plans/<plan-slug>/
  README.md
  roadmap.md
  open-questions.md
  topics/
  decisions/
  history/
  tasks/
```

`tasks/` is optional and should appear only when the plan has loop-executable
work. It stores durable task packets, not runtime events:

```text
docs/plantree/plans/<plan-slug>/tasks/<task-id>/
  README.md
  plan.md
  acceptance-criteria.md
  verification-contract.md
  handoff.md
  completion.md
```

Use durable task packets for:

- Accepted macro task.
- Planner-approved requirements.
- Acceptance criteria.
- Verification contract.
- Handoff into loop.
- Final completion or partial/replan summary.

Do not use durable task packets for:

- Every ask submission.
- Node heartbeats.
- Raw command logs.
- Retry counters.
- Temporary branch status.
- Large stdout/stderr.

## Durable Task Packet Fields

`README.md` should stay compact:

```text
Task: <title>
Task ID: <task-id>
Plan Root: <plan-slug>
Status: draft|ready|running|partial|replan_required|done|blocked
Current Loop: <loop-id|none>
Owner: planner|loop_runner|frontdesk
Created: <timestamp>
Updated: <timestamp>
```

`plan.md` contains the planner's semantic plan.

`acceptance-criteria.md` contains testable criteria and forbidden
degradations.

`verification-contract.md` defines what must be proven, not every concrete
command:

```text
objective
required_behaviors
forbidden_degradations
required_test_categories
risk_areas
minimum_evidence
partial_not_done_rules
```

`handoff.md` is the execution-ready summary used by loop runner and
orchestrator.

`completion.md` is written only at a durable boundary: done, partial, blocked,
or replan required.

## Layer 2: Runtime Loop List

The runtime list is project-local, high-frequency, and machine-owned:

```text
.ccb/runtime/loops/
  index.json
  active.json
  <loop-id>/
    loop.json
    breadcrumb.md
    tasks.jsonl
    events.jsonl
    asks.jsonl
    work-items/
    nodes/
    branches/
    clarification/
    verification/
    artifacts/
    locks/
```

`index.json` is the loop registry:

```json
{
  "schema_version": 1,
  "updated_at": "2026-06-24T00:00:00Z",
  "loops": [
    {
      "loop_id": "loop-001",
      "task_id": "task-001",
      "plan_root": "docs/plantree/plans/agentic-loop-workflow",
      "status": "running",
      "phase": "execution",
      "owner": "orchestrator",
      "created_at": "2026-06-24T00:00:00Z",
      "updated_at": "2026-06-24T00:00:00Z"
    }
  ]
}
```

`active.json` is the small current-work index:

```json
{
  "schema_version": 1,
  "active_loop_ids": ["loop-001"],
  "frontdesk_visible_loop_id": "loop-001",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

`loop.json` is the authoritative current loop record:

```json
{
  "schema_version": 1,
  "loop_id": "loop-001",
  "task_id": "task-001",
  "plan_root": "docs/plantree/plans/agentic-loop-workflow",
  "phase": "execution",
  "status": "running",
  "owner": "orchestrator",
  "limits": {
    "max_iterations": 3,
    "max_node_rework_rounds": 2,
    "max_same_failure_signature": 2,
    "max_execution_nodes": 4
  },
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z"
}
```

`breadcrumb.md` is the compact state block that can be injected or displayed:

```text
Loop: loop-001
Task: task-001
Plan: docs/plantree/plans/agentic-loop-workflow
Phase: execution
Owner: orchestrator
Next: wait for node reports
Blocked: none
Needs user: no
Evidence: .ccb/runtime/loops/loop-001/events.jsonl#12
```

## Runtime Subdirectories

`work-items/`:

```text
work-items/<work-item-id>.json
```

Contains orchestrator-produced work item boundaries, dependency refs, required
artifacts, and assigned node.

`nodes/`:

```text
nodes/<node-id>.json
nodes/<node-id>.check-plan.md
nodes/<node-id>.result.md
nodes/<node-id>.non-convergence.md
```

Contains worker/checker status, ask refs, node-level verification, rework
count, and terminal node result.

`branches/`:

```text
branches/<branch-id>.json
```

Contains dependency branch status, freeze reason, downstream blocked nodes, and
drain state.

`clarification/`:

```text
clarification/<phase>/
  candidate_questions.jsonl
  broker_review.json
  user_questions.md
  raw_answers.jsonl
  normalized_answers.jsonl
```

`verification/`:

```text
verification/round-verification-plan.md
verification/round-verification-result.md
verification/commands.jsonl
```

`artifacts/` stores raw logs, large outputs, diffs, screenshots, or external
evidence referenced by structured records.

## Runtime Event Lines

`events.jsonl` is append-only. Example:

```json
{"event_id":"evt-001","ts":"2026-06-24T00:00:00Z","kind":"phase_changed","actor":"loop_runner","from":"orchestration","to":"execution","refs":[]}
```

`asks.jsonl` is append-only. Example:

```json
{"ask_id":"ask-001","ts":"2026-06-24T00:00:00Z","target":"coder","purpose":"work_item","job_id":"job-123","node_id":"node-001","status":"submitted"}
```

Events are runtime evidence. They are synced to durable plan-tree only when
they become decision material, blocker evidence, or final completion evidence.

## Script-Owned Writes

Agents must not directly edit authoritative runtime files. They may write
draft artifacts and pass file refs to scripts.

Minimum CCB-owned write surfaces:

```bash
ccb plan task-create --plan <plan-slug> --title "<title>"
ccb plan task-artifact --task <task-id> \
  --kind <requirements|acceptance|verification|risk|handoff|review|completion|round_pass|round_partial|round_replan|round_blocker> \
  --file <path>
ccb plan task-status --task <task-id> --status <draft|ready|running|partial|replan_required|done|blocked>
ccb plan task-bind-loop --task <task-id> --loop <loop-id>
ccb plan task-import-round --task <task-id> --loop <loop-id> --result <pass|partial|replan_required|blocked> --report <path>
ccb plan task-sync --task <task-id> --loop <loop-id>

ccb loop create --task <task-id>
ccb loop list --active
ccb loop breadcrumb --loop <loop-id>
ccb loop event --loop <loop-id> --kind <kind> --file <payload-json>
ccb loop transition --loop <loop-id> --to <phase> --owner <owner>
ccb loop ask-record --loop <loop-id> --target <agent> --job <job-id> --node <node-id>
ccb loop node-status --loop <loop-id> --node <node-id> --status <running|passed|rework|blocked|non_converged>
ccb loop branch-status --loop <loop-id> --branch <branch-id> --status <running|frozen|draining|drained>
ccb loop round-result --loop <loop-id> --result <pass|partial|replan_required|blocked> --report <path>
ccb loop run-once --task-id <task-id>
ccb loop runner --once
```

The first implementation may use fewer commands, but it must preserve the
authority split:

- `ccb plan` writes durable task packet indexes and statuses.
- `ccb loop` writes runtime indexes, loop state, node/branch/round state, and
  breadcrumbs.
- `ccb question` writes clarification artifacts.

## Agent Write Boundary

Allowed agent writes:

- Draft plan files under a temporary artifact path.
- Node result files under `artifacts/` or a node-scoped draft path.
- Human-readable summaries passed to CCB scripts.

Disallowed agent writes:

- `index.json`
- `active.json`
- `loop.json`
- `events.jsonl`
- `asks.jsonl`
- `nodes/*.json`
- `branches/*.json`
- durable task status fields

If an agent needs a state transition, it submits a transition request to the
script. The script validates ownership, required refs, phase edge, and limits
before writing.

## Trellis Comparison

Trellis-style principle retained:

- External files carry workflow state.
- Scripts, not model memory, advance authoritative progress.
- A small breadcrumb can rehydrate the next step.

CCB-specific changes:

- Runtime state must include visible agent, `ask`, callback, node, branch, and
  round refs.
- Partial branch draining is first-class.
- Plan-tree sync is only at durable boundaries.
- Dynamic agents are not required for v1; fixed configured agents can run the
  first loop.

## V1 Practical Cut

The first usable version can start with:

```text
docs/plantree/plans/<plan-slug>/tasks/<task-id>/
  README.md
  plan.md
  acceptance-criteria.md
  verification-contract.md
  handoff.md

.ccb/runtime/loops/
  index.json
  active.json
  <loop-id>/
    loop.json
    breadcrumb.md
    events.jsonl
    asks.jsonl
    nodes/
    artifacts/
```

Branches, clarification, and full round-verification directories can be added
as soon as the minimal loop can run one planner, one orchestrator, one coder,
and one checker.
