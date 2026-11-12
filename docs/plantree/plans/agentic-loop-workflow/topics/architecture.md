# Agentic Loop Workflow Architecture

Date: 2026-06-24

## Design Intent

The workflow should reduce `frontdesk` to an intelligent user-facing loop rather
than a universal executor. `frontdesk` talks to the user, captures the macro
objective, confirms scope and high-risk decisions, and receives final or
unrecoverable summaries. It should not micromanage planning, decomposition,
implementation, checking, recovery, or progress bookkeeping.

The system should instead be driven by a CCB-owned loop state machine. Agents
perform semantic work and produce artifacts; scripts and loop runner code write
authoritative progress state.

## Role Topology

```text
user
  -> frontdesk group
      -> V1 resident ccb-user surface:
          -> ccb_frontdesk
          -> ccb_task_detailer
      -> V1 resident ccb-plan surface:
          -> ccb_planner
          -> ccb_orchestrator
      -> planner
          -> plan brief, macro task refs, and durable plan-tree state
      -> loop runner
          -> orchestrator triage
              -> direct execution_group 1 (worker + reviewer)
              -> direct execution_group 2 (worker + reviewer)
              -> task_detailer when detail is required
                  -> task-scoped detail docs and detail packet
                  -> macro-adjustment-request when detail evidence changes macro assumptions
                  -> frontdesk/frontend notification (only when user input is needed)
                  -> user clarifies with task_detailer
              -> macro_adjustment_request back to planner
          -> round reviewer
          -> inner monitor
      -> planner plan-tree sync
      <- final summary or escalation
```

### Frontdesk Group

Responsibilities:

- User discussion and macro-task intake.
- Scope confirmation and risk confirmation.
- Final user-facing summaries.
- Unrecoverable escalation handling.

Non-responsibilities:

- Detailed implementation.
- Internal worker scheduling.
- Continuous task-progress bookkeeping.
- Reading or rewriting every plan-tree file.

### Planner

Responsibilities:

- Act as the long-lived or parked macro owner.
- Maintain long-lived plan-tree state: roadmap, decisions, open questions,
  evidence indexes, implementation-status handoff, compact plan brief, and
  macro task publication.
- Maintain the planner-owned plan brief as the primary planning work surface:
  macro objective, current phase, active roadmap item, constraints, decision
  summary, open-question summary, detail doc links, current executable task
  entry, readiness summary, verification summary, and next owner.
- Turn user macro intent into stable task goals, constraints, non-goals, and
  plan refs.
- Preserve durable planning context without absorbing code-level research,
  worker retries, or task-local clarification detail.
- Accept or reject stable summary backfill from `task_detailer` before
  importing it into the brief or other macro plan-tree surfaces.
- Import stable summaries from completed, partial, blocked, or replan-required
  rounds through CCB-owned plan scripts.
- Produce draft macro artifacts and readiness recommendations; CCB-owned
  `ccb plan` scripts write authoritative task status, indexes, and imported
  artifact records.
- Review `macro-adjustment-request` artifacts from `task_detailer` and decide
  whether one bounded roadmap, decision, open-question, or task patch is
  needed through script-owned plan state.

Expected internal nodes:

- `planner`: maintains durable plan-tree and macro task state.
- `plan stewardship` work mode: optional planner mode or deterministic script
  surface for low-noise plan-tree sync; not a separate required mainline Role.
- `plan_reviewer`: optional check of macro scope, ambiguity, acceptance
  criteria, and plan-level risks.
- `risk_reviewer`: optional node for destructive, release, or broad-runtime
  changes.

Non-responsibilities:

- Maintaining detailed implementation packets.
- Maintaining the body of task-scoped detail docs after summary import.
- Holding task-local user clarification context.
- Dispatching workers, reviewers, or runtime topology.
- Reading raw runtime logs or every worker retry unless imported as durable
  evidence.
- Treating a detailer's `macro-adjustment-request` as an accepted decision
  before planner review and script commit.
- Calling `task_detailer`, worker, reviewer, provider, tmux, or topology
  commands directly.

The planner's default plan-tree work surface should be a compact `brief.md` or
equivalent outline, not the linked detail design body. Detailed design,
technical expansion, local research, and detailed acceptance or verification
belong to `task_detailer` in V1 only after orchestrator requests refinement
and are linked back through stable summaries.
An independent detail-design role is deferred until task-scoped detail work
proves too broad for `task_detailer`.

### Task Detailer

Responsibilities:

- Read the planner-owned brief, macro task refs, relevant plan-tree refs,
  existing task detail refs, accepted decisions, source refs, and prior
  evidence.
- Self-research the relevant code and documents enough to make the task
  executable.
- Maintain task-scoped detail docs for scheme expansion, local technical
  research, source evidence, detailed options and tradeoffs, detailed
  acceptance, and detailed verification.
- Produce detailed scope, non-goals, acceptance detail, verification detail,
  risk notes, source-evidence map, and worker handoff artifacts.
- Return stable summary backfill and detail links for planner-owned brief or
  task-document import.
- Link the accepted detail packet back to the task document so loop runner can
  activate orchestration from document state instead of conversation memory.
- Own task-local clarification when needed.
- Produce a clarification-needed artifact and wait for the user to clarify
  with the same `task_detailer` instance when source/plan evidence is
  insufficient.
- Record clarification summary and normalized answers before continuing
  refinement.
- Produce `macro-adjustment-request` when source-backed detail work proves a
  macro roadmap, decision, acceptance, or open-question adjustment is needed.

Non-responsibilities:

- Long-term plan-tree stewardship.
- Broad multi-task design document maintenance after summary import.
- Macro roadmap or product-direction changes.
- Direct worker/reviewer dispatch.
- Authoritative task status, loop state, runtime topology, or provider state
  writes.
- Long-lived user relationship after task-local clarification is resolved.
- Directly applying its own macro adjustment request.

In the V1 topology, `ccb_task_detailer` is kept resident and visible beside
`ccb_frontdesk` so task-local refinement and clarification can be reached
without first hot-loading or dispatching to a hidden pane. That residence is a
runtime simplification only: orchestrator still sends task work to
`task_detailer` only after triage decides `needs_detail`, and the detailer must
reset or rehydrate task-scoped context between tasks. Orchestrator consumes the
accepted detail packet and returns macro drift to planner; `task_detailer`
should not become the fallback planner or a long-lived user relationship.

### Clarification Broker

Responsibilities:

- Receive a stage-level batch of candidate questions from planner group.
- Merge duplicates and remove questions already answerable from code, plan-tree,
  prior user answers, or accepted assumptions.
- Apply safe defaults for non-blocking choices and record them as assumptions.
- Defer questions that are real but not needed for the current phase.
- Mark obsolete questions when the plan changed before user input was needed.
- Publish only the remaining user-facing questions as compact display artifacts
  for `frontdesk`.
- Normalize user answers into planner-readable artifacts and notify planner
  that the phase can continue.

Non-responsibilities:

- Direct user conversation.
- Starting or advancing the execution loop.
- Long-term plan-tree authority.
- Keeping a large persistent semantic context.

The persistent component is the question queue and artifact set. The semantic
broker can be launched with fresh context per phase batch, then released after
questions are ready, defaulted, deferred, or answered.

The broker remains useful for macro planning clarification and batch filtering.
It is not required for task-local implementation-detail clarification in V1;
that narrower clarification stays inside `task_detailer`, with `frontdesk` or
the frontend only notifying the user where to answer.

### Plan Stewardship Mode

Responsibilities:

- Maintain the mapping between macro tasks, plan-tree plan roots, and short-term
  loop tasks.
- Keep `docs/plantree` durable and low-noise.
- Write or update `implementation-status.md`, roadmap evidence, decisions, and
  blockers only when durable boundaries are reached.
- Provide a compact breadcrumb for current loop state.
- In V1, enforce the boundary through deterministic `ccb plan` commands. A
  planner in stewardship mode may audit or summarize, but cannot bypass script
  validation.

Non-responsibilities:

- Product implementation.
- Runtime lifecycle ownership.
- Provider recovery outside sanctioned CCB commands.

### Loop Runner

Responsibilities:

- Deterministically read loop state.
- Enforce leases, phase transitions, per-loop limits, and escalation rules.
- Activate orchestrator, execution groups, monitor, recovery, or planner
  stewardship mode according to state.
- Release temporary loop resources at the end of a round.

The loop runner should be a CCB program/helper, not an agent conversation.

### Orchestrator

Responsibilities:

- Triage planner macro packets as `direct_execution`, `needs_detail`,
  `macro_adjustment_request`, or `blocked`.
- Request a short-lived `task_detailer` only when triage finds that source-
  backed task refinement is required.
- Consume detail packets returned by `task_detailer` and dispatch from the
  accepted packet, not from detailer conversation memory.
- Decompose an execution-ready task into bounded work items.
- Choose execution-group topology and dependencies.
- Define required artifacts and per-node done conditions.
- Dispatch direct worker/reviewer asks when the macro packet is already
  concrete enough for execution.
- Aggregate node results and dependency graph state.
- Freeze non-converged branches without stopping unrelated sibling work.
- Produce a round summary for round checker after unaffected work drains.
- Return `macro_adjustment_request` artifacts to planner when macro assumptions
  must change before safe execution.

Non-responsibilities:

- Long-term plan-tree authority.
- User-facing product decisions.
- Unbounded fanout.
- Direct roadmap, decision, open-question, status, provider, tmux, or topology
  authority writes.

### Execution Groups

An execution group is a temporary or scoped team for one work item. It is the
runtime topology unit that should normally be loaded, placed, drained, and
released together.

Default v1 shape:

```text
execution_group/workgroup
  worker: implement bounded work item
  reviewer: review, test, and audit against original detail packet
```

The reviewer is a peer quality gate, not the worker's manager and not a hidden
implementer. It may reject, request rework, block, or mark the group
non-converged. It must not lower acceptance criteria, silently accept fallback,
or turn partial work into success.

The preferred V1 runtime shape is `execution_group`, with members such as
`worker_coder_1` and `reviewer_code_1`, group-local artifact root, ask edges,
and a release gate of `artifacts_imported && members_idle`.

Runtime groups are independently managed by CCB Project Binding and committed
topology. They should not use Collection ids as a selection key; orchestrator
must explicitly declare the selected roles, members, profiles, edges, gates,
lifecycle, and release policy.

Deferred complex shape:

- `fixer`: handles checker findings.
- `verifier`: runs focused validation.
- `specialist`: handles domain-specific investigation.
- `node_coordinator`: temporary intra-node coordination only when the work item
  cannot be safely split by orchestrator.

Each execution group must return structured artifacts:

- Work item id.
- Files touched or evidence inspected.
- Summary.
- Verification performed.
- Reviewer findings.
- Fallback or degradation audit.
- Node status: `passed`, `rework`, `blocked`, or `non_converged`.
- Remaining risks.

### Round Checker

The round checker verifies the loop round as an integrated result. It is
separate from per-node checker roles.

Responsibilities:

- Read planner's verification contract.
- Read orchestrator's dependency graph, node summaries, partial branches, and
  changed surfaces.
- Design the concrete round verification plan for the actual round output.
- Reuse node-level test evidence where valid.
- Add cross-node, integration, regression, and real-path tests where needed.
- Detect hidden degradation, partial work reported as done, or incompatible
  sibling changes.
- Return `pass`, `rework_node`, `replan_required`, or `global_blocker`.

Non-responsibilities:

- Product scope changes.
- Implementation fixes.
- Lowering acceptance criteria.
- Authoritative state writes.

Planner defines what must be proven. Round checker decides how to prove it for
the actual completed or drained round.

Round checker does not create the next loop plan. For `partial` or
`replan_required`, it returns a compact report and evidence refs. Planner is
then rehydrated from the task packet and round evidence to produce the next
task or clarification batch.

### Inner Monitor

The inner monitor watches loop health, not product correctness.

It should be split into two layers:

- Deterministic monitor: checks ask/job state, callback completion, timeouts,
  pane/provider health, missing artifacts, stale leases, and repeated retries.
- Semantic monitor: classifies ambiguous evidence only when deterministic checks
  cannot decide whether the loop is healthy, recoverable, or needs escalation.

The monitor may request recovery or escalation. It must not silently mutate
business task state.

## Handoff Model

Handoffs should be state-machine edges, not free-form agent forwarding.

Example:

```text
planning_ready -> orchestrator_triage
macro_clarification_needed -> clarification_broker -> frontdesk
answers_normalized -> planner
direct_execution -> execution_group[*]
detail_needed -> task_detailer
detail_packet_ready -> orchestrator
detail_clarification_needed -> frontdesk_notification -> task_detailer
macro_adjustment_requested -> planner
detail_revision_needed -> task_detailer
work_decomposed -> execution_group[*]
node_done(all_or_drained) -> orchestrator
node_non_converged -> branch_frozen -> drain_unaffected
orchestrator_done -> round_reviewer
round_passed -> planner
round_partial -> planner
check_failed -> recovery
unrecoverable -> frontdesk
done -> planner -> frontdesk
```

Each handoff should include:

- Task id.
- Phase.
- Owner.
- Required artifact refs.
- Evidence refs.
- Timeout.
- Escalation target.

## Termination Rules

Every loop must have explicit termination conditions:

- Done condition.
- Partial condition.
- Blocked condition.
- Replan-required condition.
- User-decision-needed condition.
- Maximum node rework rounds.
- Maximum same failure signature per node.
- Maximum loop iterations.
- Maximum recovery rounds.
- Maximum dynamic execution nodes.
- Maximum wall-clock runtime.
- Required verification evidence.

If a loop reaches a limit, it must stop and escalate to `frontdesk` with a compact
evidence package.

Local non-convergence should not automatically stop the whole loop. The loop
runner should freeze the affected node and dependent branch, drain unrelated
work, and return a partial package to planner unless the failure invalidates a
global design assumption or contaminates shared state.

## Team Spec Direction

Borrow the Team Builder idea by declaring workflow teams:

```yaml
teams:
  planner_group:
    agents: [planner]
    termination: plan_ready_or_blocked
    lifecycle: long_lived_or_parked

  optional_planning_review:
    agents: [plan_reviewer]
    termination: reviewed_or_blocked

  clarification_broker:
    agents: [semantic_broker]
    termination: questions_ready_or_defaulted

  task_detailer:
    agents: [task_detailer]
    termination: detail_ready_needs_clarification_blocked_or_not_ready

  execution_group:
    agents: [worker, reviewer]
    termination: reviewer_passed_blocked_or_non_converged

  round_checker:
    agents: [round_checker]
    termination: round_passed_partial_or_replan

  recovery_node:
    agents: [diagnoser, fixer, verifier]
    termination: root_cause_fixed_or_escalate

handoffs:
  macro_clarification_needed: clarification_broker
  questions_ready: frontdesk
  answers_normalized: planner
  planning_ready: orchestrator_triage
  direct_execution: execution_group
  detail_needed: task_detailer
  detail_packet_ready: orchestrator
  detail_clarification_needed: frontdesk_notification
  detail_answered: task_detailer
  macro_adjustment_requested: planner
  detail_revision_needed: task_detailer
  work_decomposed: execution_group
  nodes_drained: round_reviewer
  round_partial: planner
  check_failed: recovery_node
  done: planner
  unrecoverable: frontdesk
```

These team declarations are CCB runtime or Project Binding declarations. Agent
Roles source uses flat Roles and Role Collections; Collections may suggest
members for a runtime team, but they do not define mounted topology by
themselves. The runtime spec should be declarative; the loop runner enforces
it.

## Trellis Comparison

Trellis:

- Uses project-local files for workflow state.
- Uses hooks and skills to remind the main session.
- Relies on provider-native subagents where available.
- Keeps much of the flow main-session driven.

CCB target:

- Uses project-local and runtime-local files for workflow state.
- Uses scripts as the authority for transitions.
- Uses visible CCB agents and `ask`/callback state for execution.
- Makes the loop state machine, not `frontdesk`, drive the next handoff.
