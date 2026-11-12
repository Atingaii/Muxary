# State And Script Contract

Date: 2026-06-24

## Core Principle

Agents may propose progress. CCB-owned scripts own authoritative admission and
commits.

This mirrors the Trellis pattern where natural-language task artifacts can be
written by AI, but structured task creation, active-task selection, and phase
changes go through scripts. CCB should apply the same principle more strictly
because it can chain visible agents without returning every decision to `frontdesk`.

The intent is not to make scripts intelligent. Scripts should remain a simple,
stable workflow kernel. They enforce hard constraints: identity, legal state
edges, locks, leases, indexes, path safety, artifact manifests, required
evidence, counters, and recoverability.

Agents should handle semantic work: requirements, plans, verification
contracts, reviews, explanations, risk tradeoffs, partial/replan analysis, and
complex human-readable Markdown.

When a workflow needs both, the agent writes an artifact and the script imports
or rejects it:

```text
agent drafts semantic content
  -> script validates hard constraints
  -> script records metadata and digest
  -> script updates authority state
```

The durable plan packet and runtime loop list layout is defined in
[plan-and-runtime-list-structure.md](plan-and-runtime-list-structure.md). This
file focuses on state transitions, artifact contracts, and script semantics.

## Document Ownership Classes

Use three document classes instead of asking scripts to write every document.

| Class | Owner | Examples | Rule |
| :--- | :--- | :--- | :--- |
| Machine authority | scripts | `index.json`, `current_loop`, locks, leases, manifests, counters | Agents must not edit directly. |
| Semantic artifact | agents | `requirements.md`, `design-notes.md`, `review.md`, `partial-report.md`, `risk-notes.md` | Scripts import, index, and validate required metadata. |
| Mixed document | scripts + agents | task `README.md`, breadcrumb, plan status summaries | Scripts own protected fields; agents own narrative sections. |

For mixed documents, prefer protected blocks or generated summaries so scripts
can update hard fields without rewriting the whole human-authored document.

## State Layers

### Long-Term Plan Tree

Committed, durable state:

```text
docs/plantree/plans/<plan>/
  README.md
  roadmap.md
  implementation-status.md
  open-questions.md
  topics/
  decisions/
  history/
  tasks/
```

Use for:

- Accepted plans.
- Stable decisions.
- Durable blockers.
- Evidence links.
- Completion summaries.
- Handoff notes.

Do not use for:

- Every ask event.
- Every retry.
- Temporary node heartbeat.
- Raw logs.
- High-frequency loop progress.

### Short-Term Loop State

Runtime-local, high-frequency state:

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
    clarification/<phase>/
    verification/
    artifacts/
    locks/
```

Use for:

- Current phase.
- Current owner.
- Dynamic node list.
- Ask/job/callback refs.
- Artifact refs.
- Heartbeats.
- Retry counters.
- Timeouts.
- Escalation packets.

## Proposed `loop.json`

```json
{
  "loop_id": "20260624-rich-workflow-001",
  "plan_root": "docs/plantree/plans/agentic-loop-workflow",
  "macro_task": "Design frontdesk-light agentic workflow loop",
  "phase": "planning",
  "owner": "planner_group",
  "status": "running",
  "created_at": "2026-06-24T00:00:00Z",
  "updated_at": "2026-06-24T00:00:00Z",
  "limits": {
    "max_iterations": 3,
    "max_recovery_rounds": 2,
    "max_node_rework_rounds": 2,
    "max_same_failure_signature": 2,
    "max_execution_nodes": 4
  },
  "required_artifacts": [
    "plan",
    "execution_summary",
    "verification"
  ],
  "escalation_target": "frontdesk"
}
```

## Script Surface

Minimum shape:

```bash
ccb plan current
ccb plan breadcrumb
ccb plan start --plan <slug> --task "<title>"
ccb plan task-create --plan <slug> --title "<title>"
ccb plan task-artifact --task <task-id> \
  --kind <requirements|acceptance|verification|risk|handoff|review|completion|round_pass|round_partial|round_replan|round_blocker> \
  --file <path>
ccb plan task-status --task <task-id> --status <draft|ready|running|partial|replan_required|done|blocked>
ccb plan task-bind-loop --task <task-id> --loop <loop-id>
ccb plan task-import-round --task <task-id> --loop <loop-id> --result <pass|partial|replan_required|blocked> --report <path>
ccb plan task-sync --task <task-id> --loop <loop-id>
ccb plan artifact --type <type> --path <path>
ccb plan evidence --commit <hash> --test "<command>"
ccb plan sync

ccb loop create --task <task-id>
ccb loop list --active
ccb loop start --task <task-id>
ccb loop status --loop <loop-id>
ccb loop breadcrumb --loop <loop-id>
ccb loop event --loop <loop-id> --kind <kind> --file <payload-json>
ccb loop transition --loop <loop-id> --to <phase> --owner <agent-or-team>
ccb loop ask-record --loop <loop-id> --target <agent> --job <job-id> --node <node-id>
ccb loop node-add --loop <loop-id> --kind execution --team execution_node
ccb loop node-done --loop <loop-id> --node <node-id> --artifact <path>
ccb loop node-status --loop <loop-id> --node <node-id> --status <running|passed|rework|blocked|non_converged>
ccb loop node-rework --loop <loop-id> --node <node-id> --reason <text>
ccb loop node-non-converged --loop <loop-id> --node <node-id> --report <path>
ccb loop branch-status --loop <loop-id> --branch <branch-id> --status <running|frozen|draining|drained>
ccb loop branch-freeze --loop <loop-id> --branch <branch-id> --reason <text>
ccb loop drain-unaffected --loop <loop-id>
ccb loop round-check --loop <loop-id> --contract <path> --summary <path>
ccb loop round-result --loop <loop-id> --result <pass|partial|replan_required|blocked> --report <path>
ccb loop block --loop <loop-id> --reason <text>
ccb loop finish --loop <loop-id>
ccb loop run-once --task-id <task-id>
ccb loop runner --once

ccb question candidates --loop <loop-id> --phase <phase> --file <path>
ccb question broker-review --loop <loop-id> --phase <phase>
ccb question publish --loop <loop-id> --phase <phase>
ccb question answer --loop <loop-id> --question <question-id> --text <text>
ccb question resolve --loop <loop-id> --phase <phase>
```

`ccb plan` owns durable planning surfaces. `ccb loop` owns runtime loop state.
`ccb question` owns staged clarification artifacts and answer normalization.
The first implementation should start with the narrower `ccb plan` slice in
[plan-update-script-landing.md](plan-update-script-landing.md) before exposing
the full command set above.

The next implementation slice should stay narrower than the full command list:

```bash
ccb plan task-bind-loop
ccb plan task-import-round
ccb loop run-once --task-id
ccb loop runner --once
```

That slice is enough to remove the manual shell bridge between a ready task
packet and one completed execution round. It deliberately avoids a daemon,
automatic planner activation, clarification routing, and multi-task
parallelism.

## Loop Runner Activation Contract

The loop runner is the automatic activator. It reads task and loop state, then
chooses the next role or script to invoke. It does not rely on `frontdesk` or a
long-lived planner conversation to decide the next phase.

Planner is activated for planning states such as `draft`, resolved
clarification, `partial`, `replan_required`, resolved blockers, or changed
user scope. Planner is not active during the execution round.

Execution is activated for `ready` tasks. Round checker result and runtime
evidence are written back through scripts before the loop runner decides
whether to stop, pause, rework, or activate planner again.

Stop conditions are terminal states, paused states, or configured limits. The
complete activation and stop rules are defined in
[complete-workflow-design.md](complete-workflow-design.md).

## Transition Contract

Every transition request should include:

- Current loop id.
- Current phase and target phase.
- Current owner and next owner.
- Actor requesting transition.
- Lease id or job id proving the actor owns the current step.
- Artifact refs required for the target phase.
- Verification refs when claiming done.
- Escalation reason when claiming blocked.

The script should reject transitions when:

- The phase edge is not allowed.
- The actor does not own the lease.
- Required artifacts are missing.
- Required verification is missing.
- The loop is already terminal.
- The loop exceeded configured limits.

## Script Validation Rules

Scripts are not passive importers. They must validate that agent-produced
artifacts describe a legal transition before writing authority.

Minimum validation:

- `ready` requires the configured readiness artifacts and semantic review
  evidence.
- `running` requires a valid `current_loop` binding or a command that creates
  one atomically.
- `done` requires completion or `round_pass` evidence and the round checker
  result must be `pass`.
- `partial` requires partial evidence that names preserved branches,
  non-converged branches, and evidence refs.
- `replan_required` requires a replan report that identifies the invalid plan,
  split, acceptance criterion, verification contract, or risk assumption.
- `blocked` requires blocker evidence, owner, and whether the blocker is user,
  environment, provider, recovery, or policy driven.
- A round result import must match the currently bound loop id unless the
  command is explicitly recovering a stale lease.
- A status edge must be allowed by the current state and must include required
  actor, job, artifact, and verification refs when available.

If validation fails after an agent report exists, loop runner records a
script/state validation failure and stops automatic progress for that task.
It must not continue from a report file that was not imported.

## Locking And Idempotence

The task packet is the durable owner of `current_loop`. V1 should protect each
task with a per-task lock during read-modify-write operations.

`task-bind-loop` should be idempotent for the same `(task_id, loop_id)` pair
and reject attempts to bind a different loop while the task is already
running. It should reject terminal tasks.

`task-import-round` should be idempotent for the same imported report digest
and reject conflicting re-imports. On success it writes the round artifact,
updates the task status, clears `current_loop`, and appends or updates counters
needed for limits.

If a process crashes while a task is `running`, the next runner should inspect
the lock, lease metadata, loop state, and report artifacts before deciding
whether to recover, retry, or block. Early V1 may require manual stale-lease
reset, but it should record enough metadata to make that decision explicit.

## Phase Edges

Initial v1 edges:

```text
intake -> planning
planning -> planning_review
planning -> clarification
clarification -> planning
planning_review -> ready
ready -> orchestration
orchestration -> execution
execution -> drain_unaffected
execution -> round_checking
drain_unaffected -> round_checking
round_checking -> spec_update
round_checking -> done
round_checking -> blocked
round_checking -> replan_required
round_checking -> recovery
recovery -> round_checking
spec_update -> done
replan_required -> planning
any_nonterminal -> blocked
blocked -> planning
blocked -> frontdesk_escalation
```

`frontdesk_escalation` is terminal from the loop runner's perspective. `frontdesk` may
start a new loop or resume after user input.

## Artifact Contract

Planner group must provide:

- Requirements or PRD.
- Acceptance criteria.
- Implementation plan.
- Verification contract.
- Risk notes.
- Readiness decision.

Clarification broker must provide:

- Broker review summary.
- Curated user-facing question artifact when user input is needed.
- Recorded assumptions for questions it defaulted.
- Deferred question list for questions not needed in the current phase.
- Obsolete question list for questions made irrelevant by plan changes.
- Normalized answer artifact before waking planner.

Orchestrator must provide:

- Work item list.
- Dependency map.
- Execution-node team choice.
- Per-node done criteria.
- Node status summary.
- Branch freeze and drain summary when any node is non-converged.
- Round summary for round checker.

Execution node must provide:

- Work summary.
- Files changed or evidence inspected.
- Checker result.
- Node verification plan and result.
- Fallback or degradation audit.
- Non-convergence report when repeated rework does not converge.
- Remaining risk.

Round checker must provide:

- Concrete round verification plan derived from planner's verification contract.
- Reused node-level evidence refs.
- Additional integration, regression, or real-path tests.
- Skipped tests with explicit reason.
- Whole-round result: `pass`, `partial`, `replan_required`, or `global_blocker`.
- Evidence refs and residual risk.

Recovery node must provide:

- Failure summary.
- Evidence.
- Root cause hypothesis.
- Fix or recommended next owner.
- Whether escalation is required.

Plan steward must provide:

- Plan-tree sync summary.
- Durable evidence refs.
- Remaining open questions.
- Final breadcrumb.

## Breadcrumb Contract

The lightweight state injected or shown to `frontdesk` should fit in a small block:

```text
Loop: <loop-id>
Plan: <plan-root>
Phase: <phase>
Owner: <owner>
Next: <next-action>
Blocked: <none|reason>
Evidence: <latest refs>
Needs user: <yes|no>
```

This is intentionally closer to Trellis' per-turn breadcrumb than to a full
plan-tree dump. Full context should be loaded only by the role that needs it.

## Synchronization Policy

Sync short-term loop state into `docs/plantree` only when one of these happens:

- Planner group marks a plan execution-ready.
- A durable decision is made.
- A blocker changes product or architecture direction.
- A commit, test result, release, or accepted artifact lands.
- A loop finishes.
- `frontdesk` asks for durable documentation.

Do not sync:

- Individual ask submissions.
- Intermediate node heartbeats.
- Raw stdout/stderr.
- Retry counters unless they create a durable risk.

## Monitor Contract

Deterministic monitor inputs:

- Loop state.
- Node state.
- Ask job ids.
- Callback ids.
- Message-bureau attempts.
- Dispatcher job state.
- Provider runtime evidence.
- Pane health evidence.
- Timeouts and leases.

Semantic monitor inputs:

- Compact evidence packet from deterministic monitor.
- Node summaries.
- Recent terminal failure reasons.
- Relevant plan/task artifact refs.

Semantic monitor outputs:

- `healthy`
- `recoverable`
- `blocked`
- `unrecoverable`
- Suggested next owner
- Evidence refs

Only the loop runner may convert this output into a state transition.
