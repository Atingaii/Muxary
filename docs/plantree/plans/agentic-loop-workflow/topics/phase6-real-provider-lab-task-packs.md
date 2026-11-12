# Phase 6 Real-Provider Lab Task Packs

Date: 2026-07-04
Status: PLANNING INPUT ACCEPTED / LAUNCH GATE NOT APPROVED / NOT READY TO RUN

This topic defines the minimum real-provider lab task-pack catalog for Phase
6B. It is planning material only. Phase 6A program-matrix acceptance and
task-pack planning acceptance are recorded, but this catalog is not launch
approval.

Primary references:

- [Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md)
- [Phase 6 real capability assessment goal](../goals/phase6-real-capability-assessment-goal.md)
- [Phase 6 build-stage verification](../goals/phase6-build-stage-verification.zh.md)
- [Current implementation status](../implementation-status.md)
- [Phase 1-6 acceptance report](../history/phase1-6-acceptance-report-20260704.md)
- [Phase 6B launch checklist](phase6b-real-provider-lab-launch-checklist.md)
- [Phase 6B L1-L4 launch preparation](phase6b-l1-l4-launch-prep.md)
- Reviewer2 Phase 6B readiness checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_723a4456a783-art_19fdabce655a4233.txt`
- Reviewer2 task-pack catalog acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5ce23d15f100-art_909fc6ba1eaa410b.txt`

## Claim Boundary

This catalog is not a Phase 6B readiness claim.

Phase 6B lab remains blocked until:

- real-provider profiles and provider-home isolation are prepared for the lab;
- lab-local `AGENT_ROLES_STORE` seeding is repeatable;
- exact launch commands and report schema are frozen;
- a reviewer accepts the launch checklist for the exact lab run.

L1-L4 candidate task details are refined in
[phase6b-l1-l4-launch-prep.md](phase6b-l1-l4-launch-prep.md). That topic is
planning-only and does not approve any launch.

Closed prerequisites:

- Phase 6A fake-provider program matrix is accepted with `phase6a_pass=true`.
- `smoke-busy-release` and lifecycle closure are accepted with residual risk.
- This L0-L5 task-pack catalog is accepted as planning input.

## Shared Lab Prerequisites

Every real-provider lab run must use an external source-wrapper root such as:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-<stamp>
```

Required controls:

- Use `/home/bfly/yunwei/ccb_source/ccb_test`, never the installed `ccb` for
  source validation.
- Run commands from `/home/bfly/yunwei/test_ccb2` or the lab project root, not
  from `/home/bfly/yunwei/ccb_source`.
- Run `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` before any runtime
  action.
- Set isolated `HOME` and `CCB_SOURCE_HOME`, for example:
  `/home/bfly/yunwei/test_ccb2/source_home`.
- Use a lab-local provider home or an explicitly approved inherited provider
  setup. Do not accidentally inherit production credentials.
- Use a project-local `AGENT_ROLES_STORE` seeded with accepted RolePacks:
  `agentroles.ccb_frontdesk`, `agentroles.ccb_planner`,
  `agentroles.ccb_orchestrator`, `agentroles.ccb_task_detailer`,
  `agentroles.coder`, `agentroles.code_reviewer`, and
  `agentroles.ccb_round_reviewer`.
- Select provider profiles deliberately for `ccb_frontdesk`, `ccb_planner`,
  `ccb_orchestrator`, `ccb_task_detailer`, `coder`, and `code_reviewer`.
- Keep topology mount-only: no mainline `edges`, `gates`, `artifacts`, or
  `topology_dispatch.json`.
- Preserve script authority: provider replies are evidence, not authority
  imports.

Minimum evidence row fields for all task packs:

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

Accepted classifications:

- `pass`
- `valid_non_success`
- `system_failure`
- `role_failure`
- `provider_failure`
- `test_design_failure`

## Task Pack L0: Runtime Sanity

| Field | Requirement |
| :--- | :--- |
| Objective | Prove the real-provider lab environment can mount, ask, observe status, and release without running a product task. |
| Initial prompt shape | "Runtime sanity only. Mount the minimal orchestration topology, send a compact ping to `ccb_orchestrator`, record ask reachability, then release any dynamic lab agents." |
| Expected route | None; sanity-only. `observed_route` may be `runtime_sanity`. |
| Allowed final statuses | `ok` or `valid_non_success` with explicit provider/environment reason. |
| Required artifacts | `agent_mount_topology.desired.json`, `agent_mount_topology.observed.json`, topology events, `asks.jsonl`, release summary. |
| Required evidence row fields | Shared fields plus `diagnose_status`, `mount_topology_ready`, `orchestrator_ping_job_id`, `release_status`. |
| Cleanup/residue checks | `retained_count=0`; no dynamic lab agent remains in `.ccb/ccb.config`; observed topology has no unexplained runtime residue. |
| Blocker findings | `ccb_test --diagnose` fails; lab root or provider home is not isolated; topology contains communication DSL fields. |
| High findings | Ask submission cannot return a job id; release leaves dynamic agents mounted. |
| Medium findings | Provider ping is slow but completes within the configured timeout. |
| Why launch-gated now | L0 spends real-provider budget and may touch live provider state; launch approval must first freeze provider-home isolation, profile selection, RolePack seeding, and the B7 report shape. |

## Task Pack L1: Document / Config Direct Execution

| Field | Requirement |
| :--- | :--- |
| Objective | Prove a concrete low-risk document or config task can route directly to execution and finish cleanly. |
| Initial prompt shape | "Update one named Markdown file or one small config key. Acceptance: exact file changed, no unrelated edits, reviewer cites `execution_contract`, focused verification is a read/diff check." |
| Expected route | `direct_execution`. |
| Allowed final statuses | `done` for pass; `blocked` only if provider/environment failure is explicit and cleanup is clean. |
| Required artifacts | `task_packet.md`, `execution_contract.md`, `orchestration_notes.md`, worker reply artifact, reviewer reply artifact, `round_summary.md`. |
| Required evidence row fields | Shared fields plus `detailer_activated=false`, `round_result=pass`, `final_status=done`, `changed_files`, `verification_summary`. |
| Cleanup/residue checks | Dynamic `coder` and `code_reviewer` agents released or retained only with explicit busy evidence; no `topology_dispatch.json`. |
| Blocker findings | Orchestrator activates detailer; topology dispatch is called; an agent directly mutates task authority fields. |
| High findings | Reviewer does not cite `execution_contract`; round result is missing; task is marked done without summary import. |
| Medium findings | Provider output formatting drifts but script-owned artifacts remain complete. |
| Why launch-gated now | L1 is the first real semantic task; launch approval must first prove L0 isolation, ask reachability, and cleanup with the selected provider profiles. |

## Task Pack L2: Narrow Code / Test Direct Execution

| Field | Requirement |
| :--- | :--- |
| Objective | Prove real worker/reviewer collaboration can complete a small code change with a focused test or equivalent command. |
| Initial prompt shape | "Fix one named failing function or add one narrow behavior with one focused test. Acceptance: minimal code diff, test command named in `execution_contract`, reviewer confirms test evidence." |
| Expected route | `direct_execution`. |
| Allowed final statuses | `done` for pass; `blocked` for provider/tool failure with evidence; `partial` only if completed and unfinished steps are separated. |
| Required artifacts | L1 artifacts plus code diff summary, focused test output, reviewer contract-audit note. |
| Required evidence row fields | Shared fields plus `reviewer_cites_execution_contract=true`, `test_command`, `test_result`, `scope_shrink_detected=false`. |
| Cleanup/residue checks | Same as L1; also verify no generated test/runtime files remain outside expected paths. |
| Blocker findings | Reviewer approves without test evidence; worker edits unrelated files; round result is inferred from provider prose. |
| High findings | Test fails but final status is `done`; hidden fallback or scope shrink is accepted. |
| Medium findings | Test passes but reviewer diagnosis is thin; follow-up review recommended. |
| Why launch-gated now | L2 introduces real source edits; launch approval must define the lab project, allowed edit surface, verification command, and reviewer evidence requirements. |

## Task Pack L3: Needs Detail With Source Inspection

| Field | Requirement |
| :--- | :--- |
| Objective | Prove `ccb_orchestrator` can detect insufficient macro detail and activate `ccb_task_detailer` before execution. |
| Initial prompt shape | "Implement a change that requires reading two or more named source files before deciding steps. Acceptance: detailer emits source-evidence map, step files, and detail packet before execution starts." |
| Expected route | `needs_detail`, then `direct_execution` after detail readiness. |
| Allowed final statuses | `done` for pass; `blocked` if detailer finds a hard dependency; `replan_required` if detailer finds macro drift. |
| Required artifacts | `detail_design.md`, `detail_summary.md`, `detail_packet.manifest.json`, `steps/step-*.md`, then L1/L2 round artifacts. |
| Required evidence row fields | Shared fields plus `detailer_activated=true`, `detail_packet_imported=true`, `step_files_present=true`, `execution_after_detail_ready=true`. |
| Cleanup/residue checks | Detailer and execution agents release/retain according to lifecycle policy; no duplicate dynamic agents after route-to-execution transition. |
| Blocker findings | Execution starts before detail readiness; detailer emits no step files; planner directly writes task-local detail body. |
| High findings | Detail packet lacks source-evidence map; detail summary tries to rewrite plan topics or decisions. |
| Medium findings | Detail summary is verbose but imports cleanly and remains task-scoped. |
| Why launch-gated now | L3 depends on real-provider detailer/orchestrator ask reachability and must wait until L0-L2 prove isolation, evidence capture, and cleanup. |

## Task Pack L3: Task-Local Clarification

Status: conditional. Run only if the task-local clarification path is accepted
and source-wrapper evidence exists.

| Field | Requirement |
| :--- | :--- |
| Objective | Prove task-detailer can pause for a narrow task-local user clarification and resume only through normalized answer import. |
| Initial prompt shape | "The implementation depends on one user choice, such as a config default or API compatibility mode. Detailer must ask a blocking task-local question before execution." |
| Expected route | `needs_detail`, clarification pause, then `direct_execution` after normalized answer import. |
| Allowed final statuses | `done` after answer import; `blocked` if the answer is unavailable; `valid_non_success` if clarification exposes macro drift. |
| Required artifacts | `clarification-needed.md`, `clarification-summary.md`, `normalized-answers.jsonl`, detail packet artifacts, round artifacts when execution resumes. |
| Required evidence row fields | Shared fields plus `clarification_artifact_imported=true`, `normalized_answers_imported=true`, `execution_before_answer=false`. |
| Cleanup/residue checks | Broker/detailer state is released or retained with evidence; no execution agents mount before normalized answer import. |
| Blocker findings | Execution proceeds before answer import; agent directly edits task status from the clarification reply. |
| High findings | Clarification question is not marked blocking or lacks the exact decision needed. |
| Medium findings | User answer format drifts but normalized import preserves meaning and traceability. |
| Why launch-gated now | Clarification combines user interaction, route state, and execution gating; keep this conditional until the launch reviewer approves the normalized-answer path for the lab. |

## Task Pack L4: Macro Adjustment Request

| Field | Requirement |
| :--- | :--- |
| Objective | Prove macro-level contradictions stop execution and return to planner without mounting worker/reviewer agents. |
| Initial prompt shape | "Ask for a change that conflicts with an accepted decision, such as requiring topology to carry communication edges, or reveals that the task packet's macro assumption is invalid." |
| Expected route | `macro_adjustment_request`. |
| Allowed final statuses | `replan_required`; `blocked` only if evidence shows a hard dependency instead of macro drift. |
| Required artifacts | `macro_adjustment_request` artifact with evidence refs, orchestration notes, no worker/reviewer round artifacts. |
| Required evidence row fields | Shared fields plus `worker_reviewer_mounted=false`, `next_owner=planner`, `macro_adjustment_request_imported=true`, `final_status=replan_required`. |
| Cleanup/residue checks | No dynamic execution agents mounted; no topology dispatch file; no planner state mutation except script-owned compact artifact import. |
| Blocker findings | Worker/reviewer agents are mounted; task is marked `done`; macro adjustment directly rewrites roadmap or decisions. |
| High findings | Macro adjustment lacks evidence refs or does not name the conflicting assumption. |
| Medium findings | Planner has not yet processed the adjustment, but evidence is complete and status is correct. |
| Why launch-gated now | L4 intentionally returns a valid non-success result; launch approval must require evidence that worker/reviewer agents were not mounted. |

## Task Pack L4: Blocked

| Field | Requirement |
| :--- | :--- |
| Objective | Prove missing hard dependencies or unresolved safety decisions become blocker evidence, not fake success. |
| Initial prompt shape | "The task requires an unavailable external credential, unavailable tool, or explicit user/security decision before execution can be safe." |
| Expected route | `blocked`. |
| Allowed final statuses | `blocked`. |
| Required artifacts | `blocker_evidence.md` or equivalent blocker artifact, orchestration notes, no execution round artifacts unless the blocker is discovered during an allowed round. |
| Required evidence row fields | Shared fields plus `blocker_evidence_imported=true`, `final_status=blocked`, `hidden_fallback_detected=false`, `scope_shrink_detected=false`. |
| Cleanup/residue checks | No execution agents for pre-execution blockers; if discovered during execution, dynamic agents release/retain with explicit evidence. |
| Blocker findings | Hidden fallback, scope shrink, or task marked `done`. |
| High findings | Blocker evidence lacks root-cause category or next-owner guidance. |
| Medium findings | Blocker format is inconsistent but evidence is complete and status is correct. |
| Why launch-gated now | Blocked real-provider tasks can look like normal provider failures; launch approval must freeze blocker taxonomy, cleanup checks, and next-owner handling. |

## Task Pack L5: Stress And Abnormal Observations

L5 is for discovering the first reliable breaking point. It is not required to
pass before Phase 6B can make a bounded real-capability claim, but every L5
outcome must be classified without hiding state loss or residue.

| Field | Requirement |
| :--- | :--- |
| Objective | Expose context drift, hidden fallback, role-boundary overreach, reviewer rejection handling, partial completion, provider formatting drift, and busy release behavior. |
| Initial prompt shape | One controlled stressor at a time: multi-file change, deliberate reviewer rework, partial budget, missing machine marker, ask timeout, restart between route and execution, or busy dynamic agent release. |
| Expected route | Depends on the stressor; must be declared per task. |
| Allowed final statuses | `done`, `partial`, `replan_required`, or `blocked` when evidence matches; `valid_non_success` is expected for many stressors. |
| Required artifacts | Complete `round.json`, `asks.jsonl`, `events.jsonl`, blocker/rework/partial evidence, cleanup report, and any accepted step artifacts. |
| Required evidence row fields | Shared fields plus `failure_domain`, `rework_attempt_count`, `partial_completed_steps`, `partial_unfinished_steps`, `provider_format_drift`, `busy_retain_observed`. |
| Cleanup/residue checks | No unexplained dynamic residue; busy agents become `retained_busy` and later reconcile/release through accepted lifecycle path. |
| Blocker findings | System misclassifies failure as pass, authority mutation occurs, or dynamic runtime residue is unrecoverable. |
| High findings | Reviewer rejects twice but system hides extra retries; provider missing marker is imported as success; partial is marked `done`. |
| Medium findings | Provider timeout or formatting drift is classified correctly and cleanup remains clean. |
| Why launch-gated now | L5 intentionally stresses abnormal paths. Run it only after L0-L4 produce clean evidence, so provider behavior, product bugs, and test design failures stay distinguishable. |

Minimum L5 observations:

- reviewer rejects once and bounded rework occurs;
- reviewer cannot accept after bounded rework and the task ends as
  `partial`, `replan_required`, or `blocked`;
- partial completion separates completed and unfinished steps;
- dynamic release while busy results in `retained_busy`, not forced kill;
- provider output without a machine marker does not become success.

## Launch-Readiness Tracking

Closed prerequisite findings:

| ID | Finding | Close Condition |
| :--- | :--- | :--- |
| C1 | Phase 6A fake-provider matrix closure. | Closed by reviewer1 `job_712002b8f005` and reviewer2 `job_a34e79ecfc00`. |
| C2 | Remaining matrix cases, including busy release. | Closed by integrated eight-case matrix acceptance. |
| C3 | Lifecycle closure for fake-provider launch baseline. | Accepted with residual risk; real-provider lifecycle accuracy remains a Phase 6B observation target. |
| C4 | L0-L5 task-pack catalog definition. | Closed as planning input by reviewer2 `job_5ce23d15f100`. |

Current launch blockers:

| ID | Finding | Close Condition |
| :--- | :--- | :--- |
| B1 | Provider profile and provider-home selection is not frozen. | Launch reviewer accepts explicit provider profiles and isolated provider-home paths. |
| B2 | Lab-local `AGENT_ROLES_STORE` seeding procedure is not frozen. | Launch reviewer accepts repeatable seed procedure using accepted RolePack ids. |
| B3 | Exact launch command/schema is not frozen. | Launch reviewer accepts the L0 command sequence, report output paths, and row schema. |
| B4 | Phase 6B reviewer launch gate has not approved L0. | Reviewer approval artifact exists for the exact lab root and launch request. |

Current known medium findings:

| ID | Finding | Risk |
| :--- | :--- | :--- |
| M1 | First stable complexity breakpoint method is still draft. | Final report may need manual interpretation. |
| M2 | B7 report template must align with matrix row schema. | Evidence consolidation could become manual. |
| M3 | Task-local clarification path is conditional. | L3 clarification may need to remain optional for the first Phase 6B lab. |

## Launch Sequence After Launch-Gate Approval

1. Confirm the reviewer launch approval artifact names the exact lab root,
   provider profiles, RolePack seed procedure, L0 command sequence, report
   schema, and stop conditions.
2. Create `/home/bfly/yunwei/test_ccb2/phase6-real-lab-<stamp>`.
3. Prepare isolated `HOME`, `CCB_SOURCE_HOME`, provider homes, and
   `AGENT_ROLES_STORE`.
4. Run `ccb_test --diagnose` from the external test root.
5. Run L0 only. Stop if isolation, ask reachability, or cleanup fails.
6. Run L1 and L2 direct-execution packs.
7. Run L3 source-inspection detail pack. Run L3 clarification only if its path
   has accepted source-wrapper evidence.
8. Run L4 macro adjustment and blocked packs.
9. Run selected L5 observations one at a time.
10. Write `history/phase6-real-capability-assessment-<YYYYMMDD>.md` and send
    it through the Phase 6B reviewer gate.

## Stop Conditions

Stop the lab immediately if:

- source-wrapper root or provider-home isolation is invalid;
- `ccb_test --diagnose` fails;
- authority state is mutated outside scripts;
- topology communication DSL appears in mainline mount topology;
- dynamic runtime residue is unrecoverable;
- blocked, partial, or reviewer-rejected work is marked `done`;
- repeated provider auth failures make semantic assessment meaningless.

Do not stop only because a task returns `partial`, `blocked`, or
`replan_required`; those are valid observations when evidence and cleanup are
complete.
