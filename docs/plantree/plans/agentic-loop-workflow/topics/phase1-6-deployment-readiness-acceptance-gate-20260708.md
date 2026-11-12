# Phase 1-6 Deployment Readiness Acceptance Gate

Date: 2026-07-08
Status: SUPERSEDED AS REVIEWER LANE / RETAINED AS CHECKLIST
Owner: talk2 direct validation after 2026-07-08 user direction
Scope: apply as a strict checklist to direct `talk2` real-project validation

## Purpose

This gate was created as the strict, read-only acceptance standard for a
validation evidence round. It does not approve deployment readiness by itself. Per
the user's later 2026-07-08 direction, future validation is executed and audited
directly by `talk2`; workers/reviewers are used only for concrete source-code
modification tasks. This file remains the checklist for rejecting weak evidence,
but it is no longer an independent reviewer execution lane.

The gate is anchored in:

- [../goals/phase1-6-acceptance-goal.zh.md](../goals/phase1-6-acceptance-goal.zh.md)
- [./phase1-6-deployment-readiness-supervision-20260707.md](./phase1-6-deployment-readiness-supervision-20260707.md)
- [../implementation-status.md](../implementation-status.md)

## Non-Negotiable Rejection Statement

The following results must be rejected as deployment-readiness evidence, with no
exceptions:

1. A script-only pass without visible opened-project, UI/pane, or raw authority
evidence.
2. Any run that lacks a fresh `/home/bfly/yunwei/test_ccb2` root with a local
`.ccb` anchor and inspectable command log.
3. Any dynamic unload claim that is not backed by observed topology
`agents=[]`, `released_count=2`, `retained_count=0`, and a matching final `ps`
with only resident roles. Automated release timeouts that hide residue are not
valid release.
4. Any frontdesk direct implementation: frontdesk must remain an intake and
planner-handoff role. If a frontdesk reply creates project artifacts, runs
tests/shell, or edits code directly, the row is `BLOCKER /
frontdesk_direct_implementation_boundary_violation`.
5. Any row where `blocked`, `partial`, timeout, reviewer rejection, or provider
empty reply is imported as `done` or `pass`.
6. Any B7 or normalizer report that emits `Status: pass` while raw task
authority, topology, or live project state disagrees. That mismatch is a
normalizer bug.

Final deployment readiness will not be claimed until all required artifacts are
available, inspected, and consistent with visible opened-project state and raw
authority.

## BLOCKER / HIGH / MEDIUM / LOW Checklist

### BLOCKER (reject the evidence round if any is missing or false)

| # | Gate | Acceptance condition | Rejection condition |
| :--- | :--- | :--- | :--- |
| B1 | Explicit validation ownership | `talk2` directly runs and audits validation unless a concrete source-code modification task is delegated. | Workers/reviewers are used as validation authority, or a delegated artifact is treated as final evidence without direct `talk2` inspection. |
| B2 | Fresh test root | Each validation lane uses a fresh root under `/home/bfly/yunwei/test_ccb2`, created for this round, with project-local `.ccb` anchor and command log. | Root is reused, consumed, from `ccb_source`, or missing command log. |
| B3 | Inherited provider environment | Real-provider runs inherit the system provider environment; no lab-local `HOME`, `CCB_SOURCE_HOME`, or `CCB_SOURCE_RUNTIME_OK=1`. | Lab-local provider home, fake provider, or diagnostics override used for ordinary validation. |
| B4 | Project-local role store | `AGENT_ROLES_STORE=$ROOT/roles` and all required rolepacks are installed locally: `ccb_frontdesk`, `ccb_planner`, `ccb_orchestrator`, `ccb_task_detailer`, `code_reviewer`, `ccb_round_reviewer`, plus coder/worker profile. | Global role store used, missing rolepack, or role source not found. |
| B5 | Resident idle preflight | Before first `ask frontdesk`, `ccb_test --project <project> ps` shows all five resident roles present and `state=idle`. | Any resident is `degraded`, `busy`, missing, or `agent.json` absent. |
| B6 | Frontdesk natural-language entry | User request starts at `frontdesk` with natural language; frontdesk produces intake evidence and auto-hands off to planner. | Frontdesk asks for plan slug, requires manual planner activation, receives hard-coded task id, or implements the request directly. |
| B7 | Single planner authority | One user request produces exactly one planner handoff path; no duplicate planner jobs from dispatcher handoff plus legacy role-output import. | Two planner jobs from one frontdesk ask, or frontdesk handoff marker ignored. |
| B8 | Script-owned authority | Task status, route, and round result are imported by script-owned paths, not parsed from provider conversation text. | Provider reply mutates authority, or runner infers state from conversation memory. |
| B9 | Route correctness | Every task row has `expected_route`, `observed_route`, and `route_decision_correct=true` computed from those values. | Missing route fields, manually forced route, or provider-supplied correctness. |
| B10 | Direct execution project-root effect | Changed files and tests are in the project root before reviewer and round reviewer validation. | Success proven only in isolated copy workspace while project root unchanged. |
| B11 | Round result authority | `round_summary.md` is imported through script-owned path; final task status matches round result. | Timeout, blocked, partial, or reviewer rejection rewritten as `done/pass`. |
| B12 | Dynamic release truth | For every direct-execution loop, observed topology shows `agents=[]`, `released_count=2`, `retained_count=0`, lifecycle `removed`/`unloaded`, and final `ps` shows only resident roles. | Dynamic agents retained/active without bounded reason, config residue, or hidden timeout cleanup. |
| B13 | No topology dispatch DSL | Mount topology remains mount authority only; no `edges`, `gates`, `artifacts`, or communication DSL fields in observed/desired topology. | Topology dispatch DSL fields reappear in runner mainline. |
| B14 | No false pass in B7 | B7/normalizer `Status: pass` requires every required row to be `pass` or accepted `valid_non_success`, with raw authority and live project state consistent. | `not_claimable` / `valid_non_success` / blocker rows folded into `pass`. |

### HIGH (must be addressed; may block readiness if unclassified)

| # | Gate | Acceptance condition | Rejection condition |
| :--- | :--- | :--- | :--- |
| H1 | Full L1-L4 route mix | Frontdesk-started L1-L4 regression covers `direct_execution` (L1/L2), `needs_detail` (L3), `macro_adjustment_request` (L4), and `blocked` (L4) with terminal evidence for each. | Route mix collapsed to meta task, or L2-L4 not reached. |
| H2 | Positive busy-retain | Evidence shows a dynamic agent being `retained_busy` during an active provider ask, then released after idle proof with `retained_count=0`. | Busy agents killed early, or retain claimed without active-ask proof. |
| H3 | UI/sidebar operator evidence | Fresh project socket/tmux under the fresh root; timestamped sidebar/agent-switch proof for frontdesk/planner/orchestrator/task_detailer/ccb_round_reviewer. | UI attaches to `ccb_source`, switching fails without diagnosis, or only free-form claim. |
| H4 | Observer no-default-timeout | A real job longer than the historical 10 second window can be watched to terminal without default timeout; explicit `CCB_WATCH_TIMEOUT_S` still works as diagnostic timeout. | Default watch timeout truncates real provider jobs. |
| H5 | Module-level integration | Each row populates `module_checks.plan_task_document`, `orchestration`, `mount_topology`, `ask_collaboration`, `dynamic_lifecycle`, `evidence_reporting`. | Module checks missing or false without diagnosis. |
| H6 | Sequence13 contradiction | Fresh L1-L4 regression explicitly compares against the sequence13 `supervisor_timeout_after_reviewer_pass` shape and proves the observer repair in the same evidence set. | Sequence13 risk ignored or older repeat12 evidence reused to close this gate. |
| H7 | Frontdesk pressure lane | At least five frontdesk-entry bounded tasks across complexity levels, including L5 partial or reviewer-rework observation, with independent root and B7 rows. | Pressure lane missing or tasks created by supervisor instead of frontdesk. |

### MEDIUM (track and fix before final report)

| # | Gate | Acceptance condition | Rejection condition |
| :--- | :--- | :--- | :--- |
| M1 | Fixed JSON/JSONL row shape | Every case has a row with all required fields from the Required Evidence Row Shape section. | Free-form summary is the only evidence, or required fields missing. |
| M2 | Evidence path validity | Every path listed in `evidence_paths` exists and is readable from the fresh root. | Named path missing, zero-byte artifact, or points to consumed root. |
| M3 | Cleanup sequencing | B7 and cleanup run only after no pending ask-first or round authority remains; cleanup evidence shows `kill_status: ok` and `state: unmounted`. | Cleanup ran while worker job incomplete, or B7 used stale pre-terminal evidence. |
| M4 | Role failure classification | Role/prompt/policy failures are classified as `role_failure` with a human diagnosis, not folded into `provider_failure` or `pass`. | Role failures hidden or misclassified. |
| M5 | Valid non-success handling | `blocked`, `macro_adjustment_request`, `partial`, and `needs_detail` (pre-execution) rows are classified as `valid_non_success` with clear diagnosis. | Valid non-success rows treated as failures or successes. |

### LOW (improvement items; do not block by themselves)

| # | Gate | Acceptance condition | Rejection condition |
| :--- | :--- | :--- | :--- |
| L1 | Final report completeness | A `history/phase1-6-deployment-readiness-report-<YYYYMMDD>.md` exists with phase results, module results, fake matrix, real lab, failure taxonomy, first stable breakpoint, unresolved blockers, Phase 6A/6B verdicts, and next priorities. | Final report missing or verdict issued without audit. |
| L2 | Evidence index update | [../history/phase1-6-evidence-index.md](../history/phase1-6-evidence-index.md) references the new gate, new B7 paths, and classification of each validation artifact. | Index stale or missing new entries. |
| L3 | Source hygiene | `git diff --check` clean; touched source/tests pass `py_compile` and focused pytest. | Source hygiene regressions introduced while producing evidence. |

## Exact Evidence Fields and Paths Required

### Common required artifacts (every validation lane)

For each case, the validation artifact must name absolute paths for:

1. `fresh_root`: the test project directory under `/home/bfly/yunwei/test_ccb2`.
2. `command_log`: a timestamped command log inside the fresh root.
3. `resident_ps_before_frontdesk_entry`: `ccb_test --project <project> ps` output
taken after startup and before the first `ask frontdesk`.
4. `gate_evidence_rows.json` and `gate_evidence_rows.jsonl`: fixed-schema rows.
5. `b7_report` or equivalent normalized markdown report.
6. `cleanup_after_b7.stdout` / `.stderr`: final cleanup output.
7. `final_ps`: `ccb_test --project <project> ps` output after cleanup.

### L1-L4 route mix

Required per row:

- `case_id`: `l1-doc-direct-execution`, `l2-test-direct-execution`,
  `l3-needs-detail`, `l4-macro-adjustment-request`, `l4-blocked`.
- `expected_route` and `observed_route`.
- `route_decision_correct=true`.
- `frontdesk_job_id`, `planner_job_id`, `orchestrator_job_id`.
- For direct rows: `worker_job_id`, `reviewer_job_id`, `round_reviewer_job_id`.
- `final_status`: `done` for L1/L2, `detail_ready` for L3,
  `replan_required` for L4 macro, `blocked` for L4 blocked.
- `next_owner`: `terminal` for L1/L2, `planner` for L3/L4 macro,
  `n/a` for L4 blocked.
- `round_result`: `pass` for L1/L2, `detail_ready` for L3,
  `replan_required` for L4 macro, `blocked` for L4 blocked.
- `round_result_source`: `script_owned_import` or `round_reviewer_reply`.
- `changed_files` and `test_commands`/`test_result` for direct rows.
- `dynamic_release` for direct rows.
- `authority_checks.script_owned_route_imports=true`.
- `authority_checks.topology_dispatch_absent=true`.

Required files to inspect:

- `$ROOT/.ccb/ccb.config`
- `$ROOT/.ccb/runtime/frontdesk-handoff/*.json`
- `$ROOT/.ccb/runtime/planner/*.json`
- `$ROOT/.ccb/runtime/orchestrator/*.json`
- `$ROOT/.ccb/runtime/loops/*/round.json` and `round.pending.json`
- `$ROOT/.ccb/runtime/loops/*/observed_topology.json`
- `$ROOT/.ccb/runtime/loops/*/lifecycle.json`
- `$ROOT/task-show/*` or equivalent task authority output
- `$ROOT/round_summary/*` or equivalent round authority output
- `$ROOT/gate/*_gate_evidence_rows.jsonl` or equivalent row output.
- `$ROOT/gate/*_structured_report.md` or equivalent B7/structured report.

### Dynamic lifecycle / UI / sidebar

Required per row:

- `case_id`: `w3-direct-unload-1`, `w3-direct-unload-2`, `w3-busy-retain-positive`,
  `w3-ui-sidebar-switch`, `w3-observer-watch-timeouts`, etc.
- `dynamic_release.loop_id`, `observed_agents=0`, `released_count=2`,
  `retained_count=0`, `lifecycle_removed_unloaded=true`.
- `busy_retain.observed=true`, `retained_busy_count>=1`,
  `idle_release_verified=true`.
- `resident_reachability`: all five resident roles `true` after dynamic release.
- `ui_checks.project_socket_under_fresh_root=true`.
- `ui_checks.source_checkout_backend_isolated=true`.
- `ui_checks.sidebar_agent_switch_verified=true`.
- `observer_checks.default_watch_waited_to_terminal=true`.
- `observer_checks.explicit_timeout_still_times_out=true`.

Required files to inspect:

- `$ROOT/.ccb/project.socket` or socket path under the fresh root
- `$ROOT/.ccb/tmux/session` or equivalent tmux session evidence
- UI/agent-switch log, screenshot, or `ccb status --json` before/after
- `$ROOT/.ccb/runtime/loops/*/observed_topology.json`
- `$ROOT/.ccb/runtime/loops/*/lifecycle.json`
- `$ROOT/resident_ps_after_release.stdout`
- `$ROOT/gate/*_gate_evidence_rows.jsonl` or equivalent row output.
- `$ROOT/gate/*_structured_report.md` or equivalent B7/structured report.

### Frontdesk pressure / source-hardening

Required per row:

- `case_id`: `w1-frontdesk-direct-1`, `w1-frontdesk-direct-2`,
  `w1-frontdesk-l5-partial`, etc.
- `entrypoint=frontdesk`.
- `frontdesk_job_id` present.
- `final_status`, `next_owner`, `round_result`, `round_result_source`.
- `changed_files` and `test_result` for direct rows.
- `dynamic_release` for direct rows.
- `authority_checks.provider_reply_authority_parsing_absent=true`.
- `authority_checks.project_root_effect_verified=true`.

Required files to inspect:

- `$ROOT/.ccb/runtime/frontdesk-handoff/*.json`
- `$ROOT/.ccb/runtime/frontdesk-boundary/*.json` (must be empty or absent)
- `$ROOT/.ccb/runtime/planner/*.json`
- `$ROOT/task-show/*` or task authority output
- `$ROOT/gate/*_gate_evidence_rows.jsonl` or equivalent row output.
- `$ROOT/gate/*_structured_report.md` or equivalent B7/structured report.

### Cleanup (all lanes)

Required evidence:

- Cleanup command log entry after B7/rows are materialized.
- `cleanup_after_b7.stdout` contains `kill_status: ok` and `state: unmounted`.
- `final_ps` shows only resident roles: `frontdesk`, `planner`, `orchestrator`,
  `task_detailer`, `ccb_round_reviewer`.
- `.ccb/ccb.config` does not list dynamic loop agents after cleanup.
- No `loop-*` directories under `.ccb/agents/` remain active after cleanup
  unless a bounded reason is documented.
- No pending `round.pending.json` or `ask_first_stage_state.json` remains.

## Classification Conditions

Use these labels when triaging each worker row. Do not invent new labels.

### `pass`

- Observed route matches expected route.
- Final task status and round result are consistent with the route.
- Project-root effect verified for direct execution.
- Dynamic release verified.
- Raw authority, live project state, and B7 row are consistent.

### `valid_non_success`

- The workflow reached a bounded, intended non-success terminal state.
- Examples:
  - `macro_adjustment_request -> replan_required -> next_owner=planner`
  - `blocked -> blocked` with blocker evidence and no worker mounts
  - `needs_detail -> detail_ready -> next_owner=planner` (pre-execution)
  - `partial_completion -> partial` with unfinished-step evidence
- The row explains why this is the correct outcome, not a failure.

### `normalizer_bug`

- B7 or the worker row claims `pass` while raw authority or live project state
  disagrees.
- B7 folds `not_claimable`, `valid_non_success`, or blocker rows into `pass`.
- Row fields are missing, paths are invalid, or classification contradicts the
  evidence.
- This is a reporting/normalizer/system failure even if the underlying provider
  task behaved correctly.

### `provider_failure`

- The provider returned a genuine API or runtime failure that is outside CCB
  control: `codex_prompt_delivery_failed`, `empty_provider_reply` exhausted,
  `pane_dead`, `provider_api_error`.
- The failure is not caused by CCB role/prompt/policy misconfiguration.
- Evidence includes provider job id, diagnostics, and session log.

### `role_failure`

- A CCB-managed role produced wrong behavior because of role instructions,
  policy, or prompt design.
- Examples:
  - frontdesk implements the request directly instead of handing off.
  - orchestrator imports `orchestration_notes` instead of replying.
  - reviewer gives a contract-free pass.
  - planner emits a meta task instead of the requested L1-L4 task set.

### `system_failure`

- A failure in CCB program logic, dispatcher, retry policy, topology reconciler,
  loop runner, or evidence importer.
- Examples:
  - Duplicate planner jobs from dispatcher handoff + legacy role-output import.
  - `ask --chain` from active CCB task context.
  - Topology dispatch DSL fields leak into mount authority.
  - Retry policy does not retry empty provider replies.
  - Runner resumes with pending `round.pending.json` and overwrites evidence.

### `test_design_failure`

- The harness, test command, or evidence expectation is wrong for the scenario.
- Examples:
  - Unittest command resolves to site-packages package in inherited environment.
  - Expected file path differs from project root layout.
  - Row schema expects fields that are not applicable to the case.
- This is a harness or expectation bug, not a product bug.

## What To Do When Worker Artifacts Arrive

1. Read the full artifact reply before any classification.
2. Verify the named fresh root exists and has not been consumed by a prior
   sequence/repeat.
3. Inspect `resident_ps_before_frontdesk_entry`; fail as
   `resident_agents_not_ready` if any resident is not `idle`.
4. Inspect the command log for provider-home policy and role store policy.
5. For each case, read the required files listed above and fill the row checklist.
6. Classify each row using the Classification Conditions section.
7. If any BLOCKER is violated, stop and file a focused repair task with
   reproduction command and required regression test.
8. If all BLOCKERs pass and HIGH items are addressed or precisely classified,
   record the `talk2` direct audit result in the supervision/status documents.
9. Do not update `implementation-status.md` or the supervision doc to claim
   readiness until the direct audit evidence has been inspected against this
   checklist.

## Current Verdict

Deployment readiness is **PARTIALLY PROVEN / STILL BLOCKED** after the
2026-07-08 direct `talk2` self-run. The L1-L4 frontdesk route-mix lane has
fresh passing evidence, but dynamic lifecycle/busy-retain/UI/sidebar pressure
and final packaging evidence are still open. No final deployment-readiness
claim is made by this gate.
