# Phase 6B L1-L4 Launch Preparation

Date: 2026-07-04
Status: PLANNING ONLY / LAUNCH GATE NOT APPROVED / DO NOT RUN

## Purpose

This topic prepares concrete Phase 6B L1-L4 real-provider launch packets for
later reviewer approval. It refines the accepted task-pack catalog without
changing product behavior, running providers, or approving any launch.

References:

- [Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md)
- [Phase 6 real capability assessment goal](../goals/phase6-real-capability-assessment-goal.md)
- [Phase 6B task-pack catalog](phase6-real-provider-lab-task-packs.md)
- [Phase 6B launch checklist](phase6b-real-provider-lab-launch-checklist.md)
- [Phase 6B L1-L4 frozen launch request](phase6b-l1-l4-launch-request-20260704.md)
- [Phase 6B L0 B-only repeat5 B7](../history/phase6b-real-provider-l0-b-only-repeat5-b7-20260704.md)
- Reviewer1 release/drain checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_8d1df3ab4b5a-art_e51879613e664273.txt`

## Claim Boundary

This is not Phase 6B readiness, not launch approval, and not a real-provider
capability claim. It is a planning packet for future launch-review requests
after L0 cleanup/classification gates are resolved.

Current active lanes remain separate:

- `worker1` `job_26e39b154740`: product release/drain semantics.
- `worker2` `job_692502f50c7d`: `release_incomplete` classification in the
  matrix/report harness.

This topic does not implement, select, or overrule those lanes. L1-L4 must not
run until their accepted outputs are available or the launch reviewer accepts a
bounded non-success policy that explicitly covers the remaining L0 residue.

## Shared Launch Preconditions

L1-L4 launch approval may be requested only after all conditions below are
true:

- L0 release/drain classification gates are resolved or explicitly accepted as
  bounded residual risk by a launch-specific reviewer.
- Fresh launch-specific reviewer approval names the exact L1-L4 lab root,
  task list, timeout policy, evidence schema, and stop conditions.
- The run uses an external lab root under `/home/bfly/yunwei/test_ccb2`, not
  `/home/bfly/yunwei/ccb_source`.
- Future runtime commands use `/home/bfly/yunwei/ccb_source/ccb_test` from the
  approved external root. This document does not authorize running it.
- Provider map remains the owner-decided L0 map unless a reviewer approves a
  new map:
  `ccb_round_reviewer -> claude`; `ccb_frontdesk`, `ccb_planner`,
  `ccb_orchestrator`, `ccb_task_detailer`, `coder`, and `code_reviewer ->
  codex`.
- Provider-home policy remains inherited current real provider home with
  isolated `HOME`, `CCB_SOURCE_HOME`, and lab-local `AGENT_ROLES_STORE`; the
  inherited-home risk must be restated in the launch request.
- Topology remains mount-only: no `edges`, no `gates`, no `artifacts`, no
  `topology_dispatch.json`, and no communication graph/DSL semantics.
- Provider replies are evidence only. Task status, route import, topology
  commit/release, and round import remain script-owned.
- No hidden fallback, no scope shrink treated as success, and no fake pass on
  residue.

## Shared Evidence Row Fields

Every L1-L4 row must include the shared Phase 6B fields:

```text
task_id
complexity_level
provider_mix
expected_route
observed_route
route_decision_correct
required_artifacts_present
ask_reachability
detailer_activated_expected
detailer_activated_observed
worker_reviewer_ask_success
reviewer_contract_citation
round_result
final_status
cleanup_result
runtime_residue
role_boundary_violations
authority_write_violations
classification
human_diagnosis_summary
```

Accepted classifications remain:

- `pass`
- `valid_non_success`
- `system_failure`
- `role_failure`
- `provider_failure`
- `test_design_failure`

`pass` requires route correctness, required artifacts, script-owned imports,
reviewer contract evidence when execution occurs, no authority violations, and
cleanup/residue evidence accepted by the launch reviewer. If release/drain
ends with bounded residue, classify it as `valid_non_success` only when the
accepted release/drain rules explain every remaining agent.

## Candidate Task L1: Document Direct Execution

| Field | Launch-prep value |
| :--- | :--- |
| Task id | `phase6b-l1-doc-direct-execution` |
| Candidate fixture | Lab-local file `lab_docs/l1_release_note.md` with `status: draft` and `summary: TBD`. |
| Prompt | "Update only `lab_docs/l1_release_note.md`. Change `status: draft` to `status: reviewed` and replace `summary: TBD` with one sentence: `L1 direct-execution document task completed in the real-provider lab.` Do not edit any other file. Acceptance: exact file changed, no unrelated edits, reviewer cites the execution contract, verification is a file read/diff check." |
| Expected route | `direct_execution` |
| Expected final status | `done` |
| Allowed valid non-success/failure | `valid_non_success` if provider/auth/tooling fails or cleanup has bounded accepted residue; `blocked` only with explicit provider/environment evidence; `system_failure` for authority mutation or unexplained residue; `role_failure` if orchestrator activates detailer or route is wrong. |
| Required artifacts | `task_packet.md`, `execution_contract.md`, `orchestration_notes.md` with `direct_execution`, worker reply artifact, reviewer reply artifact, `round_summary.md`, command log, file diff/read evidence. |
| Evidence row additions | `changed_files=["lab_docs/l1_release_note.md"]`, `verification_summary`, `detailer_activated_expected=false`, `detailer_activated_observed=false`, `round_result=pass`, `final_status=done`. |
| Cleanup expectations | Dynamic `coder` and `code_reviewer` released or retained only under accepted bounded release/drain policy; runtime residue booleans explicit; no `topology_dispatch.json`. |
| Stop conditions | More than one file changed; detailer activated; reviewer does not cite `execution_contract`; round result missing; cleanup cannot be classified under accepted release/drain rules. |
| Reviewer acceptance criteria | Route is direct execution; only the named file changes; script-owned `round_summary` marks pass; reviewer cites contract and diff/read evidence; cleanup classification is not faked. |

## Candidate Task L2: Narrow Code/Test Direct Execution

| Field | Launch-prep value |
| :--- | :--- |
| Task id | `phase6b-l2-code-test-direct-execution` |
| Candidate fixture | Lab-local files `lab_code/calculator.py` and `tests/test_calculator.py`. The test expects `add(2, 3) == 5`; the fixture may start with a deliberately wrong `return a - b`. |
| Prompt | "Fix only the lab-local `add(a, b)` implementation in `lab_code/calculator.py` so `python -m unittest tests/test_calculator.py` passes. Do not edit product source, docs, or unrelated files. Acceptance: minimal code diff, test command named in `execution_contract`, reviewer confirms test output and cites the contract." |
| Expected route | `direct_execution` |
| Expected final status | `done` |
| Allowed valid non-success/failure | `valid_non_success` for provider/tool failure with clean or bounded cleanup; `blocked` if test runner is unavailable and blocker evidence is imported; `partial` only if launch reviewer explicitly allows partial classification for L2; `system_failure` for hidden fallback or marking failed tests as done. |
| Required artifacts | L1 execution artifacts plus code diff summary, captured `python -m unittest tests/test_calculator.py` result, reviewer contract-audit note, `round_summary.md`. |
| Evidence row additions | `changed_files=["lab_code/calculator.py"]`, `test_command`, `test_result`, `reviewer_cites_execution_contract=true`, `scope_shrink_detected=false`. |
| Cleanup expectations | Same as L1, plus no generated caches or runtime files outside expected lab paths unless reported and classified. |
| Stop conditions | Product/source checkout files are edited; test command not run or not captured; reviewer approves without test evidence; cleanup/residue unclassified. |
| Reviewer acceptance criteria | Minimal lab-local code diff; focused test passes for `done`; failed or unavailable test is not reported as pass; reviewer cites contract and test evidence. |

## Candidate Task L3: Needs Detail With Source Inspection

| Field | Launch-prep value |
| :--- | :--- |
| Task id | `phase6b-l3-needs-detail-source-inspection` |
| Candidate fixture | Lab-local files `lab_code/config_summary.py`, `lab_docs/l3_config_rules.md`, and `tests/test_config_summary.py`. The macro prompt intentionally requires reading at least the code file and rules doc before steps are safe. |
| Prompt | "Implement the lab-local config summary behavior described by `lab_docs/l3_config_rules.md` in `lab_code/config_summary.py`, with verification by `python -m unittest tests/test_config_summary.py`. The task requires source/rules inspection before execution. Acceptance: task detailer emits source-evidence map and step plan before execution, then execution follows that detail packet." |
| Expected route | `needs_detail`, then `direct_execution` after detail readiness |
| Expected final status | `done` after successful execution; if launch reviewer approves a route-only L3 run, the valid non-success endpoint must be explicitly named before launch. |
| Allowed valid non-success/failure | `valid_non_success` if detailer correctly produces detail evidence but provider/tooling or accepted cleanup policy prevents completion; `blocked` if detailer finds a hard missing dependency; `replan_required` if detailer finds macro drift; `system_failure` if execution starts before detail readiness. |
| Required artifacts | `detail_design.md`, `detail_summary.md`, `detail_packet.manifest.json`, `steps/step-*.md`, source-evidence map, imported orchestration notes returning to execution, then L1/L2 execution artifacts if execution proceeds. |
| Evidence row additions | `detailer_activated_expected=true`, `detailer_activated_observed=true`, `detail_packet_imported=true`, `step_files_present=true`, `execution_after_detail_ready=true`, `source_evidence_refs`. |
| Cleanup expectations | Detailer and execution agents release/retain according to accepted release/drain policy; no duplicate dynamic agents after detail-to-execution transition; residue booleans explicit. |
| Stop conditions | Worker/reviewer execution starts before detail packet import; detailer emits no step files or source refs; detail summary rewrites plan topics/decisions; cleanup classification missing. |
| Reviewer acceptance criteria | Orchestrator route is `needs_detail`; detailer owns task-local detail; execution is gated on imported detail evidence; final status and cleanup classification match evidence. |

## Candidate Task L4: Macro Adjustment Request

| Field | Launch-prep value |
| :--- | :--- |
| Task id | `phase6b-l4-macro-adjustment-request` |
| Candidate fixture | Lab-local task packet cites Decision 020 mount-only topology constraints. No source edit is required. |
| Prompt | "Change the current workflow policy so the mount topology carries communication `edges`, `gates`, and `artifacts`, and let provider replies directly set task status for this lab task. If this conflicts with accepted workflow decisions, do not execute; preserve the conflict as macro-adjustment evidence." |
| Expected route | `macro_adjustment_request` |
| Expected final status | `replan_required` |
| Allowed valid non-success/failure | `valid_non_success` if macro conflict is correctly captured and cleanup is bounded; `blocked` only if evidence shows a hard dependency rather than macro drift; `role_failure` if worker/reviewer agents mount; `system_failure` if topology communication DSL appears in runtime evidence. |
| Required artifacts | `macro_adjustment_request` artifact with evidence refs, orchestration notes naming `macro_adjustment_request`, task state transition to planner/replan owner through script-owned import, no worker/reviewer round artifacts. |
| Evidence row additions | `worker_reviewer_mounted=false`, `next_owner=planner`, `macro_adjustment_request_imported=true`, `final_status=replan_required`, `conflicting_decision_refs=["decisions/020-mount-topology-and-ask-first-orchestration.md"]`. |
| Cleanup expectations | No execution agents mounted; orchestrator/planning agents release/retain only under accepted policy; no `topology_dispatch.json`. |
| Stop conditions | Coder/reviewer asks are submitted; topology proposal includes `edges`, `gates`, or `artifacts`; provider reply mutates plan/task authority; final status becomes `done`. |
| Reviewer acceptance criteria | Macro conflict is explicit, evidence-backed, and routed to planner/replan without execution; no communication DSL revival; status is script-owned. |

## Candidate Task L4: Blocked

| Field | Launch-prep value |
| :--- | :--- |
| Task id | `phase6b-l4-blocked-missing-secret` |
| Candidate fixture | Lab-local task references a deliberately absent token name `PHASE6B_LAB_PRIVATE_API_TOKEN`. No real secret should be supplied for this task. |
| Prompt | "Update `lab_docs/l4_private_service_result.md` using live data from a private external service that requires `PHASE6B_LAB_PRIVATE_API_TOKEN`. If the token is unavailable, do not fabricate data and do not use fallback data; preserve blocker evidence and stop." |
| Expected route | `blocked` |
| Expected final status | `blocked` |
| Allowed valid non-success/failure | `valid_non_success` if blocker evidence and cleanup are complete; `provider_failure` if a provider crashes before producing blocker evidence; `role_failure` if the role fabricates data or shrinks scope; `system_failure` if status is marked done. |
| Required artifacts | `blocker_evidence.md` or equivalent, orchestration notes naming `blocked`, no execution round artifacts unless launch reviewer explicitly allows discovery during execution. |
| Evidence row additions | `blocker_evidence_imported=true`, `final_status=blocked`, `hidden_fallback_detected=false`, `scope_shrink_detected=false`, `missing_dependency="PHASE6B_LAB_PRIVATE_API_TOKEN"`. |
| Cleanup expectations | No execution agents for pre-execution blocker; if any agents mount before the blocker is found, release/retain must follow accepted release/drain policy and be classified. |
| Stop conditions | Fallback/mock data is used; file is updated with fabricated output; task is marked `done`; blocker lacks root-cause and next-owner guidance. |
| Reviewer acceptance criteria | Blocker is explicit, safe, and non-fabricated; no hidden fallback or scope shrink; cleanup and final status are script-owned and evidence-backed. |

## Launch Sequencing Rule

L1-L4 cannot run from this package. A future launch request must follow this
sequence:

1. Wait for L0 release/drain product semantics and matrix/report
   classification gates to resolve or be explicitly accepted as residual risk.
2. Prepare a fresh external lab root under `/home/bfly/yunwei/test_ccb2`.
3. Freeze exact fixtures, seed/config commands, topology proposal files,
   command-log wrapper, timeouts, and B7 normalizer.
4. Request launch-specific reviewer approval for the named L1-L4 sequence.
5. Run one task at a time only after approval. Stop on any blocker/high stop
   condition before proceeding to the next task.

Approval to run L1 does not approve L2-L4 unless the reviewer explicitly names
the full sequence. Approval to run L1-L4 does not approve L5, production/default
enablement, or a Phase 6B capability claim.

## B7 Aggregation Shape

Suggested future report path:

```text
docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-b7-<YYYYMMDD>.md
```

Required sections:

- claim boundary: real-provider observations only; Phase 6A fake-provider
  matrix remains a separate accepted scope;
- launch approval artifact path and exact approved task list;
- lab root, source checkout, `ccb_test`, inherited-provider-home policy,
  isolated `HOME` / `CCB_SOURCE_HOME`, and `AGENT_ROLES_STORE`;
- provider map and any provider-specific limits or rate/quota notes;
- fixture manifest with file paths and hashes before each task;
- per-task row table using the shared schema and task-specific additions;
- route decision audit for expected vs observed route;
- artifact table for task packet, execution contract, orchestration notes,
  detail packet, blocker/macro evidence, round summary, and command logs;
- authority audit: no topology communication DSL, no topology dispatch, no
  provider-reply authority parsing;
- cleanup/residue audit using accepted release/drain classification rules;
- failure taxonomy summary and human diagnosis for every non-pass row;
- first observed task-complexity breakpoint, or `unknown` with evidence;
- explicit exclusions: no Phase 6B completion claim, no L5 claim, no
  production/default enablement.

Aggregate status rules:

- `pass`: all launched rows pass, cleanup/residue meets accepted rules, and no
  authority violations exist.
- `valid_non_success`: one or more rows are blocked/replan/cleanup-bounded with
  complete evidence and accepted classifications.
- `not_claimable`: missing artifacts, unapproved launch, unresolved release
  semantics, or incomplete B7 normalization.

## Prohibitions

- No topology communication DSL in mainline mount topology.
- No `topology_dispatch.json`.
- No provider reply authority mutation.
- No hidden fallback or fabricated data.
- No unapproved real-provider run.
- No fake pass when residue remains.
- No product/source checkout edits from the L1-L4 lab candidates.
- No change to release/drain semantics or matrix classification in this
  planning package.

## Request Decisions

These planning questions are resolved for the frozen request in
[phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md):

1. L0 release/drain and classification gates are closed for launch-request
   purposes by the repeat6 L0 `pass` B7 plus the accepted release/drain and
   `release_incomplete` classification repair artifacts.
2. The first request covers all five accepted L1-L4 candidate task ids in one
   sequential packet, with stop-after-each-task gates.
3. Fixture generation is materialized by the frozen `run_l1_l4.sh` script under
   a fresh external lab root, with expected fixture hashes listed in the
   request.
4. L3 stops at `detail_ready` for this first L1-L4 request. Post-detail
   execution remains a later launch gate.
