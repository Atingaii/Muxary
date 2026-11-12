# Workflow Role Catalog And Boundaries

Date: 2026-06-27

## Purpose

Define the role catalog needed by the CCB agentic workflow before converting
the roles into Agent Roles specs.

This document follows the current architecture in
[architecture.md](architecture.md) and the Chinese workflow overview in
[agentic-workflow-scheme.zh.md](agentic-workflow-scheme.zh.md).

This document records the current CCB workflow role catalog. CCB-specific
workflow roles keep explicit `agentroles.ccb_*` ids; generic execution roles
such as `agentroles.coder` and `agentroles.code_reviewer` remain portable
host-neutral roles. Role Collections group installation, update, removal, list
hierarchy, and profiles, but they do not define runtime topology, inheritance,
or permissions.

The design principle remains:

```text
program kernel stays simple and stable
semantic flexibility belongs to roles
scripts commit or reject role artifacts
```

Roles should not be designed as one omnipotent main agent. Each role should
hold only the context required for its phase, produce explicit artifacts, and
respect script-owned authority.

The context-lifecycle split is part of the role boundary:

- `frontdesk` and `planner` are the only intended long-lived conversation
  holders.
- `frontdesk` keeps user-facing intake, preferences, confirmations, and
  escalation breadcrumbs, not implementation detail.
- `planner` keeps macro plan-tree state, the compact brief, roadmap/TODO,
  decisions, open questions, and stable evidence links.
- `orchestrator`, `task_detailer`, workers, reviewers, and round reviewers are
  immaculate (`无垢`) roles. They may be mounted or visible for observability,
  but each semantic activation must be fresh and rehydrated from durable
  artifacts, not old conversation memory.

## Role Design Tiers

### V1 Core RolePacks

These roles define the mainline CCB workflow surface. CCB-specific workflow
roles use `agentroles.ccb_*`; execution implementation/review roles stay
generic where they are useful outside CCB.

| RolePack | Default Agent | Lifetime | Main Output |
| :--- | :--- | :--- | :--- |
| `agentroles.ccb_frontdesk` | `ccb_frontdesk` | long-lived / user-facing | macro task intake, user-facing summary, escalation display |
| `agentroles.ccb_task_detailer` | `ccb_task_detailer` | V1 visible / immaculate task-scoped activation | task-scoped detail docs, detailed execution packet, source-evidence map, task-local clarification artifacts, stable summary backfill |
| `agentroles.ccb_planner` | `ccb_planner` | long-lived or phase-activated | macro task packet, plan-tree brief, readiness recommendation, macro adjustment review |
| `agentroles.ccb_orchestrator` | `ccb_orchestrator` | V1 visible / immaculate task-round activation | triage result, optional detailer request, node plan, constrained task dispatch, round aggregation |
| `agentroles.coder` | `coder` | immaculate per work item | bounded implementation or investigation result |
| `agentroles.code_reviewer` | `code_reviewer` | immaculate per work item | node verification, fallback audit, pass/rework/block decision |
| `agentroles.ccb_round_reviewer` | `ccb_round_reviewer` | immaculate per execution round | round result report: `pass`, `partial`, `replan_required`, or `global_blocker` |

### V1 Optional Or On-Demand RolePacks

These roles are installable capabilities but not required members of the core
planning path.

| RolePack | Default Agent | Trigger | Main Output |
| :--- | :--- | :--- | :--- |
| future CCB plan reviewer | `ccb_plan_reviewer` | macro or detail readiness review is requested | planner/detail quality review and readiness/blocker findings |
| future CCB clarification broker | `ccb_clarification_broker` | macro questions require user-facing filtering | user-question artifact, defaults, deferred questions, normalized answers |

### V1 Script/Hybrid Roles

These are part of the workflow architecture but should not initially become
heavy semantic RolePacks.

| Role | Form | Reason |
| :--- | :--- | :--- |
| `loop_runner` | CCB program/helper | Owns deterministic routing, locks, leases, status edges, and one-shot activation. It must not become an agent conversation. |
| plan stewardship | deterministic `ccb plan` first, optional `planner` work mode later | Script commands own authoritative task/index/status writes. Planner may summarize or audit plan-tree consistency, but cannot bypass scripts. |
| `runtime_layout_manager` | CCB program/helper | Owns tmux window/pane placement. Semantic roles request capacity; they do not mutate panes directly. |

### V1 Role Collections

Collections are Agent Roles catalog and install-management artifacts. They are
not parent Roles, source merges, permission grants, or runtime topology.

| Collection | Required Members | Optional Members | Purpose |
| :--- | :--- | :--- | :--- |
| `agentroles.collections.planning_group` | `agentroles.ccb_planner` | future CCB plan-review or clarification roles | Install the macro planner and optional planning-adjacent capabilities without merging their contexts. |
| `agentroles.collections.execution_workgroup` | `agentroles.coder`, `agentroles.code_reviewer` | doc, research, test, and source-reviewer Roles | Install the default bounded implementation and independent review Roles. |
| `agentroles.collections.agentic_loop_core` | `agentroles.ccb_frontdesk`, `agentroles.ccb_task_detailer`, `agentroles.ccb_planner`, `agentroles.ccb_orchestrator`, `agentroles.coder`, `agentroles.code_reviewer`, `agentroles.ccb_round_reviewer` | future review/risk/monitor/recovery roles | Install the core workflow Role set for CCB-like agentic loops. |

CCB runtime topology may still use `planning_group`, `execution_group`, and
`workgroup-node1` as Project Binding or runtime-state concepts. Those runtime
groups do not derive membership, authority, or mounting behavior from
Collections. Orchestrator and topology policy must explicitly declare concrete
members, roles, profiles, edges, gates, lifecycle, and release policy.

### V2 Optional RolePacks

These should be designed after V1 loop closure is proven.

| RolePack | Default Agent | Trigger | Main Output |
| :--- | :--- | :--- | :--- |
| `agentroles.ccb_risk_reviewer` | `risk_reviewer` | destructive, release, migration, credential, or broad-runtime changes | risk gate and required approvals |
| `agentroles.ccb_inner_monitor` | `inner_monitor` | long-running or anomalous loop | health report and escalation recommendation |
| `agentroles.ccb_recovery` | `recovery` | provider/ask/tmux/lease failure | recovery plan or blocked evidence package |
| `agentroles.ccb_plan_steward` | `planner` work mode | legacy compatibility only | low-noise plan-tree sync summary |
| `agentroles.ccb_domain_researcher` | `domain_researcher` | planner lacks domain evidence | source-backed research brief |
| `agentroles.ccb_spec_checker` | `spec_checker` | public contract or RolePack/spec changes | spec conformance report |

## V1 Role Boundaries

### Frontdesk

Owns:

- user conversation;
- macro task intake;
- scope, non-goal, and high-risk confirmation;
- presenting curated clarification questions;
- final user-facing summary;
- unrecoverable escalation display.

Must not:

- implement code;
- call worker/checker directly;
- write authoritative task status;
- read high-frequency loop logs unless presenting an escalation artifact;
- micromanage planner or orchestrator internals.

Required skills/templates:

- macro task intake template;
- user clarification display template;
- final summary / escalation template;
- optional `ask` skill only for sending macro packets to planner or asking
  configured dialog experts.

### Planner

Owns:

- understanding macro task intent;
- maintaining durable plan-tree state, roadmap, decisions, open questions,
  evidence indexes, active brief, and macro task publication;
- reading relevant plan-tree context and durable evidence;
- producing macro task artifacts: goals, constraints, non-goals, high-level
  acceptance, plan refs, risk flags, and handoff to orchestrator triage;
- maintaining the planner-owned plan brief with stable summaries and links;
- producing candidate questions for broker when macro planning is blocked;
- reviewing `macro-adjustment-request` artifacts from `task_detailer` and
  deciding whether to request one bounded roadmap, decision, open-question, or
  task update through scripts;
- recommending `ready`, `needs_clarification`, `blocked`, or `not_ready`.

Must not:

- talk directly to the user;
- carry code-level task-local detail as long-term context;
- maintain the body of detail design docs under `topics/*`;
- maintain detailed implementation packets;
- accept a detailer's macro adjustment request as authority before script
  commit;
- manage runtime agents;
- call `task_detailer`, worker, reviewer, provider, tmux, or topology commands
  directly;
- mark status ready by editing files directly;
- lower acceptance criteria to make work executable;
- treat round checker output as permission to silently reduce scope.

Required skills/templates:

- macro task packet drafting template;
- plan brief template;
- verification contract template;
- candidate question template;
- readiness recommendation schema;
- `ccb plan` usage guide for artifact import through scripts.

### Task Detailer

Owns:

- converting macro task refs into a detailed execution packet;
- reading relevant plan-tree refs, accepted decisions, source files, tests, and
  prior durable evidence;
- consuming the planner-owned brief and existing task detail links when they
  exist;
- maintaining task-scoped detail design documents, scheme expansion, local
  technical research, options/tradeoffs, detailed constraints, detailed
  acceptance, and detailed verification;
- producing source-evidence maps, detailed scope, non-goals, implementation
  constraints, acceptance detail, verification detail, and worker handoff;
- returning the detail packet to orchestrator and stable summary backfill plus
  detail links for planner import;
- asking task-local clarification when self-research cannot safely resolve a
  detail;
- recording clarification summary and normalized answers before continuing
  refinement;
- emitting `macro-adjustment-request` when a source-backed finding requires
  macro planner review.

Must not:

- become the long-lived plan-tree maintainer;
- maintain broad multi-task detail design as an ongoing document owner after
  summary import;
- rewrite roadmap, macro plan direction, or accepted decisions;
- apply its own `macro-adjustment-request`;
- dispatch workers, reviewers, orchestrator, or runtime topology directly;
- write authoritative task status, indexes, runtime state, provider state, or
  `.ccb` authority files;
- reuse old detailer conversation as context for a new task, detail pass, or
  clarification continuation;
- lower acceptance criteria to avoid user clarification;
- stay alive as a general user conversation agent after the task-local
  clarification is resolved.

Required skills/templates:

- task detail intake and context scan;
- task-scoped detail design template;
- source-evidence map template;
- option/tradeoff summary template;
- execution spec template;
- detailed acceptance template;
- detailed verification template;
- clarification-needed artifact;
- clarification summary / normalized answer artifact;
- `detail-packet.manifest.json` schema;
- source-evidence entry schema;
- worker handoff template;
- detail readiness schema;
- stable summary backfill / plan brief update summary template.

### Plan Reviewer

Owns:

- checking planner macro artifacts and accepted detail packets for ambiguity,
  scope drift, missing acceptance, weak verification, unhandled risk, and hidden
  assumptions;
- approving or rejecting macro readiness and detail readiness as semantic
  recommendations;
- returning task-local blockers to `task_detailer` for revision or
  clarification;
- forcing broker clarification only when macro planning user input is truly
  blocking.

Must not:

- rewrite the whole plan as a second planner unless asked;
- rewrite the detail packet as a second detailer unless explicitly asked;
- implement code;
- mark task status directly;
- approve vague acceptance criteria.

Required skills/templates:

- readiness checklist;
- macro artifact ambiguity/risk review template;
- detail packet review template;
- negative prompt checklist for hidden fallback and scope shrinkage.

### Clarification Broker

Owns:

- merging planner candidate questions;
- removing duplicate, obsolete, already-answerable, or non-blocking questions;
- recording safe defaults and deferred questions;
- producing a compact user-facing question artifact for frontdesk;
- normalizing user answers for planner.

Must not:

- directly converse with user except through frontdesk artifacts;
- activate execution;
- rewrite product scope;
- ask every possible question upfront.

Required skills/templates:

- candidate-question filter template;
- user-question display artifact;
- normalized-answer artifact;
- defaults/deferred-question ledger.

### Orchestrator

Owns:

- reading ready task packet and verification contract;
- estimating complexity;
- choosing 1-4 execution nodes;
- proposing `execution_group` runtime topology for each bounded work item
  instead of directly loading isolated agents;
- requesting capacity through the fixed capacity skill;
- dispatching bounded worker/checker tasks with constraints;
- aggregating node results and dependency state;
- returning a round summary for round checker.

Must not:

- call reload/kill/tmux directly;
- write `.ccb/runtime` or task status directly;
- reuse previous task or round conversation as dispatch context;
- create unbounded fanout;
- convert `partial` into `done`;
- lower acceptance criteria.

Required skills/templates:

- `orchestrator-topology` skill;
- legacy/debugging capacity status only through topology or diagnostics;
- node slicing template;
- worker dispatch template;
- checker dispatch template;
- round aggregation template;
- partial/non-convergence escalation rules.

### Worker

Owns:

- executing one bounded work item;
- producing concise implementation or investigation evidence;
- reporting files touched, commands run, and unresolved blockers.

Must not:

- change task scope;
- silently degrade;
- hide failed tests;
- edit plan-tree authority files;
- claim global success.

Required skills/templates:

- bounded work-item template;
- evidence report template;
- failure/blocker report template.

### Checker

Owns:

- deriving node-level verification from the planner contract and worker task;
- running or specifying focused tests;
- reviewing worker output for correctness, hidden fallback, degradation,
  scope shrinkage, and missing evidence;
- returning `pass`, `rework_required`, `blocked`, or `non_converged`.

Must not:

- become the primary implementer by default;
- lower acceptance criteria;
- approve partial work as complete;
- change global plan or task split.

Required skills/templates:

- node check plan template;
- fallback/degradation audit;
- rework request template;
- non-convergence report.

### Round Checker

Owns:

- verifying the integrated execution round;
- reading planner verification contract, orchestrator summary, and node reports;
- deciding concrete round result:
  `pass`, `rework_node`, `partial`, `replan_required`, or `global_blocker`;
- producing durable round report suitable for `ccb plan task-import-round`.

Must not:

- fix code;
- change product scope;
- directly write task status;
- infer success without evidence;
- route next loop by itself.

Required skills/templates:

- round verification plan;
- round result report with a standalone machine line:
  `round result: pass|partial|replan_required|global_blocker`;
- evidence reference checklist;
- hidden degradation audit.

## Script Boundary Required In Every RolePack

Every CCB workflow RolePack should include a common CCB authority rule:

```text
You may author semantic artifacts and recommend transitions.
You must not directly edit authoritative state:
- task index
- task status
- current_loop
- leases or locks
- runtime capacity records
- tmux pane/window state

Use CCB commands such as `ccb plan`, `ccb loop`, `ccb question`, or the
provided skill wrappers for authoritative writes.
```

## Design Requirements For Mother

When `mother` designs these RolePacks, it should produce for each V1 role:

- role id and default local agent name;
- identity and mission;
- authority and non-authority;
- required inputs;
- expected outputs and artifact schemas;
- required skills;
- reusable templates;
- negative instructions;
- CCB script boundary text;
- minimal smoke-test scenario;
- compatibility notes for CCB visible agents and future non-CCB hosts.

The first external Agent Roles spec pass should focus on:

1. `agentroles.ccb_planner`
2. `agentroles.ccb_orchestrator`
3. `agentroles.coder`
4. `agentroles.code_reviewer`
5. `agentroles.ccb_round_reviewer`
6. `agentroles.collections.planning_group`
7. `agentroles.collections.execution_workgroup`
8. `agentroles.collections.agentic_loop_core`
9. optional `agentroles.ccb_task_detailer`
10. future CCB plan-review and clarification roles if still needed

`agentroles.ccb_frontdesk`, optional worker specialties, optional reviewer
specialties, monitor, recovery, and risk reviewer can follow after the core
closure path is stable.

## Mother Design Review

The first `mother` RolePack design pass was completed on 2026-06-27 and is
recorded in
[../history/mother-rolepack-design-2026-06-27.md](../history/mother-rolepack-design-2026-06-27.md).

Accepted refinements:

- Treat `planner`, `plan_reviewer`, `clarification_broker`, `orchestrator`,
  and `round_checker` as P0 complete RolePack work.
- Treat `frontdesk`, `worker`, and `checker` as P1 simplified reference roles.
- Keep monitor, recovery, risk, planner stewardship mode, domain researcher,
  and spec checker as P2 boundary-only roles until V1 loop closure is stable.
- Require a shared authority rule in every CCB workflow RolePack.
- Split host-neutral RolePack content from CCB adapter-specific command,
  runtime, tmux, ask/callback, lease, and capacity details.

Immediate external Agent Roles spec handoff order:

1. common authority rule and artifact templates;
2. `agentroles.ccb_planner` as the macro planner, with
   `agentroles.ccb_task_detailer` as an orchestrator-demanded optional
   refinement role;
3. `agentroles.collections.planning_group`;
4. `agentroles.ccb_round_reviewer`;
5. tightened `agentroles.ccb_orchestrator`;
6. future CCB clarification or plan-review roles only if the V1 loop proves
   they are needed;
7. `agentroles.collections.execution_workgroup`;
8. simplified `agentroles.ccb_frontdesk`, `agentroles.coder`, and
   `agentroles.code_reviewer`;
9. `agentroles.collections.agentic_loop_core`.

## Draft Landing Status

The first CCB workflow RolePack draft set is now present under
`drafts/`:

- `_shared/authority-rule.md` and `_shared/templates/*`;
- `agentroles.ccb_planner`;
- `agentroles.ccb_task_detailer`;
- `agentroles.ccb_plan_reviewer`;
- `agentroles.ccb_clarification_broker`;
- `agentroles.ccb_orchestrator`;
- `agentroles.ccb_frontdesk`;
- `agentroles.coder`;
- `agentroles.code_reviewer`;
- `agentroles.ccb_round_reviewer`;
- legacy compatibility/history packages:
  `agentroles.ccb_worker`, `agentroles.ccb_checker`, and
  `agentroles.ccb_round_checker`.

Current targeted verification:

```bash
PYTHONPATH=lib pytest -q test/test_orchestrator_rolepack.py
```

Result:

```text
7 passed
```

This verifies manifest translation, CCB adapter provider coverage, skill
projection paths, shared authority-rule presence, required templates, and the
shared round-result contract.
