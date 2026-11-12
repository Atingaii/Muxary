# Goal: Workflow Runner State Router V1

Date: 2026-06-27

## Objective

Extend the one-shot loop runner from "consume one ready task" into the first
minimal workflow state router.

The goal is not to build a heavy workflow engine. The goal is a small,
deterministic `--once` activation step:

```text
read committed task state
  -> select at most one actionable task
  -> route to exactly one next owner
  -> record activation evidence
  -> stop with next_action
```

This is the next goal after
[Loop Runner Bridge V1](loop-runner-bridge-goal.md). It should not start until
the bridge can bind a ready task, run one execution round, import the round
result, and expose the updated task status through script-owned state.

## Design Principle

This goal follows the same principle as
[Decision 010: Simple Kernel, Flexible Agents](../decisions/010-simple-kernel-flexible-agents.md):

```text
program order stays minimal and stable
semantic flexibility belongs to model roles
scripts commit or reject role artifacts
```

The program owns sequence, identity, locks, leases, state edges, artifact
manifests, budgets, and stop decisions. It must not try to understand complex
requirements, user intent, code quality, or replan strategy.

Model roles own flexible semantic work:

- planner understands `draft`, `partial`, and `replan_required` task evidence;
- planner reviewer checks ambiguity, risk, acceptance, and verification;
- broker/frontdesk handle user-facing clarification artifacts;
- orchestrator and round checker continue to own execution-round semantics.

The router must therefore activate roles by passing artifact references and a
bounded instruction. It should not inline every runtime log or parse Markdown
to infer meaning.

## Scope

In scope:

- extend `ccb loop runner --once --json` so it can route one committed task
  state, not only `ready`;
- add a task-selection helper that returns one actionable task and one action;
- route `ready` to the existing execution bridge;
- route `draft`, `partial`, and `replan_required` to planner activation;
- stop on `needs_clarification`, `blocked`, `done`, `cancelled`, or no
  actionable task;
- record activation evidence under runtime state with task id, action, owner,
  ask/job id when applicable, artifact refs, and next action;
- enforce one activation per `--once` invocation;
- keep per-task lock/lease behavior so two runners cannot activate the same
  task concurrently;
- focused unit tests and one external fake-provider smoke in
  `/home/bfly/yunwei/test_ccb2`.

Out of scope:

- long-running daemon or file watcher;
- multi-task scheduling;
- arbitrary workflow-spec interpreter;
- full clarification broker command surface;
- full planner RolePack publication;
- semantic parsing of planner or round-checker Markdown inside scripts;
- automatic frontdesk conversation;
- automatic multi-round fanout;
- runtime pane reflow or provider replacement.

## State Routing Contract

The router reads only committed task state and runtime authority. It chooses at
most one action.

| Task State | Router Action | Next Owner |
| :--- | :--- | :--- |
| `ready` | run execution bridge | `orchestrator` / execution round |
| `draft` | activate planner | planner group |
| `partial` | activate planner with partial evidence refs | planner group |
| `replan_required` | activate planner with replan evidence refs | planner group |
| `needs_clarification` | stop paused with question refs | broker/frontdesk |
| `blocked` | stop blocked with blocker refs | frontdesk/recovery |
| `done` | stop terminal | frontdesk summary path |
| `cancelled` | stop terminal | none |
| no actionable task | return idle | none |

Planner activation does not mean the script writes new plans. The script
creates a compact activation packet and asks the planner role to produce
artifacts. The planner or plan steward must still use `ccb plan` commands to
import artifacts and request status transitions.

## Planner Activation Packet

V1 planner activation should be reference-first:

```text
task_id
task_status
reason_for_activation
required_next_output
task_packet_root
artifact_refs
round_evidence_refs
open_question_refs
script_write_rules
stop_limits
```

The packet should be small enough to preserve context purity. Heavy evidence
should be linked by path or artifact id, not pasted into the prompt unless it
is essential for the current planning step.

## Stop And Budget Rules

`ccb loop runner --once` stops after one activation. It should return a
structured `next_action` instead of continuing recursively.

V1 should enforce deterministic limits:

- one task selected per invocation;
- one owner activated per invocation;
- no planner reactivation if the task already has an active planner lease;
- no execution round if the task has an active different loop binding;
- repeated script-validation failures for the same task produce a paused or
  blocked recommendation instead of silent retries;
- `partial` and `replan_required` remain planner-reactivation states, not
  success states.

## Acceptance Criteria

- A project with one `ready` task still runs the existing bridge and imports a
  round result.
- A project with one `draft` task activates planner and does not start worker
  or checker agents.
- A project with one `partial` or `replan_required` task activates planner
  with imported round evidence refs.
- A project with `needs_clarification` stops and returns the question artifact
  refs instead of asking the planner again.
- A project with no actionable tasks returns `idle`.
- The router never edits task Markdown directly and never infers semantic
  readiness from free-form text.
- All authoritative status, index, current-loop, artifact, and activation
  records are written through script-owned surfaces.
- External source-wrapper smoke proves the route with fake providers from
  `/home/bfly/yunwei/test_ccb2`.

## Test Targets

Focused tests:

- task selector chooses one actionable task and reports stable action;
- `ready` uses the existing `loop runner --once` execution bridge;
- `draft` activates planner and records activation metadata;
- `partial` and `replan_required` include round artifact refs in the planner
  activation packet;
- `needs_clarification`, `blocked`, `done`, `cancelled`, and no-task states
  stop without provider activation;
- active lease or conflicting loop binding fails closed;
- repeated identical activation is idempotent only when the prior activation
  has not been consumed.

External smoke:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --project <smoke-project> loop runner --once --json
```

The smoke must prove:

- source wrapper is used, not installed release `ccb`;
- a `draft` task routes to planner only;
- a `ready` task routes to the execution bridge only;
- planner activation and execution activation each produce compact runtime
  evidence;
- no high-frequency runtime logs are copied into plan-tree Markdown.

## Implementation Sequence

1. Close out `loop-runner-bridge-goal.md` with passing external smoke evidence.
2. Add a task selector that returns `(task_id, action, reason)` from committed
   task state.
3. Add a planner activation packet writer and ask adapter.
4. Extend `ccb loop runner --once` to route `draft`, `partial`, and
   `replan_required` to planner activation.
5. Add paused/terminal/idle stop responses for clarification, blocked, done,
   cancelled, and no-task states.
6. Add focused tests for routing, locking, idempotence, and stop behavior.
7. Run external source-wrapper smoke in `/home/bfly/yunwei/test_ccb2`.
8. Update roadmap evidence only after the smoke passes.

## Risks

- If the router tries to understand planner Markdown, it will become brittle.
  Keep semantic interpretation in planner and reviewer roles.
- If the runner keeps looping inside one command, failures will be harder to
  inspect. V1 must stay one activation per `--once`.
- If planner activation pastes too much evidence inline, context purity is
  lost. Prefer artifact refs.
- If `partial` is treated as success, later planning will silently miss
  unfinished branches.
- If lock and lease records are vague, multiple runners can activate the same
  task. Treat state ownership as a hard script invariant.

## Current Status

First V1 slice landed in the current worktree.

Implemented behavior:

- `ccb plan` artifact imports record actor/job provenance on each artifact;
- `ccb loop runner --once` selects one committed task status and routes it to
  exactly one action;
- `ready` still uses the existing execution bridge;
- `draft`, `partial`, and `replan_required` write compact planner activation
  packets and submit one planner ask;
- `needs_clarification`, `blocked`, `done`, and `cancelled` stop without
  provider activation;
- `partial` and `replan_required` planner packets include round evidence refs;
- runner CLI treats deterministic stop states as successful command exits.

Verification is recorded in
[../history/workflow-runner-state-router-2026-06-27.md](../history/workflow-runner-state-router-2026-06-27.md).

Remaining V1 work:

- `ccb question` broker/frontdesk artifact surface;
- planner artifact import/review follow-through after activation;
- richer runtime provenance when managed provider sessions expose explicit
  job/actor environment;
- more complete live-provider smokes for configured planner/orchestrator roles.
