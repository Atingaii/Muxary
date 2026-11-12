# Workflow RolePack External Spec Handoff V1

Date: 2026-06-27
Status: Historical / legacy CCB compatibility handoff

## Goal

Move the CCB workflow role drafts from
`docs/plantree/plans/agentic-loop-workflow/drafts/agentroles.*` into the
external Agent Roles spec repository as installable catalog Roles, then verify
that CCB can consume them through the normal Role store, provider skill
projection, and artifact command surfaces.

This handoff records the legacy `agentroles.ccb_*` draft migration surface. It
is not the current mainline Role naming plan. Current design uses
`agentroles.planner`, treats `agentroles.ccb_planner` as compatibility
material, and makes `agentroles.task_detailer` an orchestrator-demanded
refinement role rather than a planner-group member.

## Scope

External target:

- `/home/bfly/yunwei/agent-roles-spec`

Roles:

- `agentroles.ccb_frontdesk`
- `agentroles.ccb_planner`
- `agentroles.ccb_clarification_broker`
- `agentroles.ccb_plan_reviewer`
- `agentroles.ccb_orchestrator`
- `agentroles.ccb_worker`
- `agentroles.ccb_checker`
- `agentroles.ccb_round_checker`

Core chain to prove:

```text
planner -> clarification_broker -> frontdesk -> plan_reviewer -> orchestrator
```

## Requirements

- Planner Role can be installed and carries task-packet, readiness, and
  candidate-question artifact templates.
- Clarification broker Role can be installed and carries candidate-question
  compression plus user-batch and normalized-answer templates.
- Plan reviewer Role can be installed and carries a review artifact contract.
- Orchestrator Role keeps runtime mutation behind `orchestrator-capacity`; it
  must not edit `.ccb/ccb.config`, runtime files, tmux state, or provider
  sessions directly.
- Every CCB workflow Role declares the full CCB provider set in
  `adapters/ccb/adapter.toml`, so CCB can project provider-local `ask` skills
  and role skills consistently.
- CCB source carries provider-local `ask` instructions for the declared
  provider set: Codex, Claude, Gemini, OpenCode, Kimi, Mimo, Qwen, Z.ai, and
  Droid. Native CLI providers may consume these as text assets until they gain
  richer skill-directory projection.
- Source-wrapper smoke must run from `/home/bfly/yunwei/test_ccb2`, not from
  the CCB source checkout.

## External Landing

Materialized in `/home/bfly/yunwei/agent-roles-spec`:

- catalog role directories under `roles/ccb-*`;
- aliases in `aliases.toml`;
- catalog discovery notes in `roles/README.md`;
- focused tests in `tests/test_ccb_workflow_roles.py`;
- existing `tests/test_ccb_orchestrator_role.py` updated for
  `round-aggregation`;
- existing `roles/code-reviewer` remains separate from `agentroles.ccb_checker`.

Important correction:

- `normalized-answers.jsonl` now uses `"source":"user"` instead of the invalid
  placeholder enum string `"user|default|deferred"`. The same fix was mirrored
  back into the CCB plan-tree draft templates.

## Verification

External Agent Roles spec tests:

```bash
cd /home/bfly/yunwei/agent-roles-spec
python -m pytest -q
```

Result:

```text
69 passed in 2.80s
```

CCB targeted tests after draft template correction:

```bash
cd /home/bfly/yunwei/ccb_source
PYTHONPATH=lib pytest -q \
  test/test_ask_skill_templates.py \
  test/test_repo_hygiene.py \
  test/test_orchestrator_rolepack.py \
  test/test_question_cli.py \
  test/test_plan_tasks_cli.py
```

Result:

```text
37 passed in 0.50s
```

Source wrapper diagnose:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --diagnose
```

Result:

```text
allowed_source_test_project: yes
```

Install/config/capacity smoke project:

```text
/home/bfly/yunwei/test_ccb2/workflow-rolepack-handoff-smoke
```

Evidence:

- `ccb_test roles install` installed all eight workflow Roles from
  `/home/bfly/yunwei/agent-roles-spec` into the smoke Role store.
- `ccb_test config validate` loaded the project config with
  `frontdesk`, `planner`, `clarification_broker`, `plan_reviewer`, and
  `orchestrator` as configured agents.
- `ccb_test loop capacity ensure --loop-id smoke --profile worker=1 --profile
  code_reviewer=1 --json` returned `loop_capacity_status: ensured` with
  `agentroles.ccb_worker` and `agentroles.ccb_checker`; apply was correctly
  `deferred_until_start` because the smoke project was unmounted.
- Direct Codex materialization proved `ask` plus role skills were projected
  for `frontdesk`, `planner`, `clarification_broker`, `plan_reviewer`, and
  `orchestrator`.
- Artifact smoke imported planner artifacts, candidate questions, frontdesk
  question batch, raw answer, normalized answers, review artifact, and then
  moved task `role-handoff-001` to `ready`.

## Completion Audit

- External Role source exists and is installable: proven by Agent Roles full
  test suite and `ccb_test roles install` smoke.
- Planner artifact path is usable: proven by planner templates imported through
  `ccb plan task-artifact` and `ccb question candidate-import`.
- Clarification broker path is usable: proven by `user-batch-import`,
  `answer-import`, and corrected `normalized-import`.
- Plan reviewer path is usable: proven by `review` artifact import and
  `task-status ready`.
- Orchestrator capacity boundary is preserved: proven by role tests and
  capacity smoke using `ccb loop capacity ensure/status`, not direct runtime
  edits.
- Provider/ask projection is covered: proven by adapter provider declarations
  and Codex materialization smoke checking both `skills/ask/SKILL.md` and
  each role skill. CCB source also now includes provider-local `ask` assets for
  Gemini, Qwen, and Z.ai in addition to the pre-existing Codex, Claude, Droid,
  Kimi, Mimo, and OpenCode assets, with template/hygiene tests covering the
  full set.
