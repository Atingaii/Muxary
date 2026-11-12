# Orchestrator RolePack Blueprint

Date: 2026-06-24

## Purpose

Record the reviewed `mother` role design for the first `orchestrator`
RolePack. This document turns the design into a stable handoff for later
RolePack materialization without giving the role extra runtime authority.

Source input:

- CCB artifact:
  `.ccb/ccbd/artifacts/text/completion-reply/job_c13be87160c2-art_95755ee494f94cc5.txt`
- SHA256:
  `0fd84fca0253dab406eb4f763d5f832b285860a16a28abbfb19521e65ecb1251`

## Current Update

This blueprint predates the topology-driven runtime direction. Keep its core
role boundary: `orchestrator` is a short-lived semantic dispatcher and has no
runtime mutation authority. For new Role materialization, replace
`runtime-capacity request` as the primary artifact with a topology proposal
that includes nodes, information-flow edges, artifact refs, call order, and
release gates. See
[runtime-workflow-graph-and-reconciler.md](runtime-workflow-graph-and-reconciler.md).

## Audit Result

The proposed design is accepted as a V1 blueprint with one important boundary:
it is a role content plan, not a runtime implementation plan.

Accepted:

- Stable role id should be `agentroles.ccb_orchestrator`.
- Default local agent name should be `orchestrator`.
- The role shape should be `single_role`, not a bundled worker/checker team.
- The role is activated by `loop_runner` through `ask` for one round or one
  orchestration batch.
- It may assess complexity, choose a 1-4 node budget, slice work, build a
  dependency graph, prepare constrained worker/checker ask payloads, request
  runtime capacity as structured data, and aggregate node results.
- It must produce runtime-capacity requests only as artifacts. `loop_runner`,
  scripts, and ccbd own whether those requests become fixed-agent reuse,
  guarded reload, or rejection.

Rejected or kept out of V1:

- Direct `.ccb/ccb.config` edits.
- Direct `ccb reload`, kill, restart, or pane manipulation.
- Direct writes to `.ccb/runtime/loops/*` authority files.
- Provider session/auth reads.
- Background watcher behavior inside the role.
- Marking partial or non-converged work as done.
- Replacing checker, round checker, planner, `frontdesk`, or `ccb_self`.

## Identity

Recommended manifest identity:

```toml
schema = "rolepack/v1"
id = "agentroles.ccb_orchestrator"
name = "CCB Loop Orchestrator"
version = "0.1.0"
description = "Short-lived semantic dispatcher for CCB agentic execution loops."

[identity]
default_agent_name = "orchestrator"
category = "orchestration"
purpose = "Decompose ready execution tasks into bounded CCB work items and ask payloads."
responsibilities = [
  "Assess task complexity and choose a 1-4 node budget",
  "Slice execution-ready tasks into bounded work items",
  "Build small dependency graphs and branch freeze/drain plans",
  "Prepare constrained worker and checker ask payloads",
  "Emit structured runtime-capacity requests without executing them",
  "Aggregate node results into round-checker handoff or partial reports"
]
non_goals = [
  "Runtime daemon supervision",
  "Provider repair or restart",
  "Direct CCB reload, kill, or pane management",
  "Authoritative plan-tree or runtime-state writes",
  "User-facing scope confirmation",
  "Checker or round-checker override"
]
```

Relationship to existing roles:

- `ccb_self` remains the maintenance and diagnostics operator. It may perform
  controlled CCB repair when explicitly asked; `orchestrator` must not.
- `su_ccb` remains a broader workflow operator. `orchestrator` is narrower and
  loop-internal.
- `frontdesk` remains the user-facing intake and reporting role.
- Planner owns durable planning artifacts and readiness; orchestrator consumes
  ready task packets and reports execution structure.

## Role Memory Requirements

The role memory should state:

- It is a short-lived semantic dispatcher inside a CCB execution loop.
- Its unit of work is one round or one orchestration batch.
- It receives references to task packet, acceptance criteria, verification
  contract, loop breadcrumb, and runtime capacity summary.
- It should prefer references and schemas over copied long text.
- It can draft artifacts and semantic recommendations only.
- CCB scripts own authoritative writes.
- `loop_runner` owns phase transitions, ask submission policy, runtime-capacity
  request execution, and conversion of role output into `ccb loop` or
  `ccb plan` state.
- V1 assumes fixed configured agents; dynamic load/unload is only represented
  by a structured request.
- Non-converged branches are frozen and returned as partial packages. They are
  not downgraded to success.

## Skill Set

The V1 RolePack should carry six generic skills.

| Skill | Purpose | Output |
| :--- | :--- | :--- |
| `orchestrator-assess-complexity` | Classify the task as `single`, `split_serial`, `split_parallel`, or `replan_needed`. | Complexity class, node budget, and replan reason when needed. |
| `orchestrator-slice-work` | Turn a ready task packet into bounded, testable work items. | Work-item list with scope, non-goals, acceptance refs, verification refs, and assigned node. |
| `orchestrator-dependency-graph` | Build the node DAG, branch ids, freeze rules, and drain-unaffected rules. | Dependency graph artifact. |
| `orchestrator-ask-payload` | Generate constrained worker and checker asks from work items and criteria. | Worker ask and checker ask templates with expected result schemas. |
| `orchestrator-runtime-request` | Describe needed execution capacity without mutating runtime state. | Structured runtime-capacity request artifact. |
| `orchestrator-summary` | Aggregate node/checker results for round checker or planner. | Orchestration summary or partial loop report. |

Each skill must explicitly forbid:

- open-ended broad implementation asks;
- hidden fallback, degradation, or scope shrinkage;
- more than four execution nodes;
- direct runtime or plan authority writes;
- bypassing checker or round-checker gates.

## Templates

Required templates:

- `work-item.json`
- `dependency-graph.json`
- `worker-ask.md`
- `checker-ask.md`
- `runtime-capacity-request.json`
- `orchestration-summary.md`
- `partial-loop-report.md`

Template field groups should match
[orchestrator-role-capability.md](orchestrator-role-capability.md):

- work item: id, title, goal, scope, non-goals, acceptance refs,
  verification refs, dependencies, risks, expected artifacts, assigned node.
- dependency graph: nodes, edges, branches, shared surfaces, freeze rules,
  drain-unaffected rules, global stop conditions.
- worker ask: goal, scope, non-goals, refs, forbidden degradations, expected
  output schema, retry limits.
- checker ask: worker result refs, acceptance refs, verification refs,
  fallback audit, allowed statuses.
- runtime request: request type, reason, node count, maximum, preferred roles,
  lifetime, V1 fallback, unsupported conditions.
- summaries: completed, rework, blocked, non-converged, frozen branches,
  drained siblings, evidence refs, and round-checker handoff.

## Package Shape

The concrete RolePack should live in the Agent Roles content surface, not as
production CCB runtime state.

Recommended source shape:

```text
reference_roles/ccb-orchestrator/
  role.toml
  README.md
  memory.md
  skills/generic/orchestrator-assess-complexity/SKILL.md
  skills/generic/orchestrator-slice-work/SKILL.md
  skills/generic/orchestrator-dependency-graph/SKILL.md
  skills/generic/orchestrator-ask-payload/SKILL.md
  skills/generic/orchestrator-runtime-request/SKILL.md
  skills/generic/orchestrator-summary/SKILL.md
  templates/
  references/
    ccb-loop-boundary.md
    plan-runtime-authority.md
    execution-node-verification.md
  adapters/ccb.toml
  tests/validation.md
```

If drafted inside this repository before the external Agent Roles package is
ready, it should stay under a plan or draft directory and must not be treated as
installed runtime authority.

## Validation Gates

Before the role can be installed by CCB:

1. Manifest parses as `rolepack/v1`.
2. Role id and default local name resolve without colliding with configured
   project agents.
3. All skill paths and template refs exist.
4. Negative prompts prove the role refuses direct reload, kill, runtime-state
   writes, partial-to-done conversion, checker override, and more than four
   nodes.
5. CCB adapter notes explain that `ask` dispatch is loop-runner-mediated.
6. Content boundary scan confirms no credentials, provider sessions, runtime
   pids, sockets, pane state, or project-private state.
7. V1 smoke can consume the role with fixed configured coder/checker agents,
   even if actual fanout is serialized by `loop_runner`.

## Implementation Sequence

1. Materialize the RolePack draft from this blueprint.
2. Validate manifest and content paths against the current RolePack spec.
3. Run the negative-boundary prompt set.
4. Add CCB adapter notes for projection, ask target behavior, and fixed-agent
   V1 operation.
5. Keep runtime-capacity execution deferred until the loop runner and hot-reload
   contracts can translate requests safely.
