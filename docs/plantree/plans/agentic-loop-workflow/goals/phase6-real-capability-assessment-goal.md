# Phase 6 Real Capability Assessment Goal

Date: 2026-07-03
Status: Planning

## Objective

Design the full Phase 6 capability assessment under the assumption that token,
quota, and real-provider usage are not the limiting factor.

This goal extends
[phase6-single-round-task-matrix-goal.md](phase6-single-round-task-matrix-goal.md).
The single-round task matrix remains the minimum acceptance gate. This document
adds a broader real execution assessment whose purpose is to expose weak
points, abnormal states, role-boundary drift, provider instability, and task
complexity limits.

The staged build gates for implementing and accepting this assessment are
defined in
[phase6-build-stage-verification.zh.md](phase6-build-stage-verification.zh.md).

The target is not "all real tasks must pass". The target is:

- prove which task types the workflow can complete reliably;
- identify where the workflow fails under complexity;
- classify failures by system layer;
- produce evidence that can drive the next implementation phase.

## Assessment Principles

- Test real workflow behavior, not only command success.
- Use real CCB runtime, real panes, real `ask`, real topology reconcile, and
  real dynamic release where possible.
- Use fake providers only for deterministic CI regression and fault injection.
- Use real providers for capability discovery, prompt/role-boundary stress,
  context-drift checks, and abnormal-state observation.
- Treat `partial`, `blocked`, and `replan_required` as valid outcomes when
  they match the execution contract.
- Fail the assessment only when the system misclassifies an outcome, hides
  failure, mutates authority state outside scripts, loses evidence, or leaves
  dynamic runtime residue.

## Test Environments

### Reproducible Source-Wrapper Matrix

Run from the external source test root:

```text
/home/bfly/yunwei/test_ccb2/phase6-fake-matrix-<stamp>
```

Required controls:

- command: `/home/bfly/yunwei/ccb_source/ccb_test`;
- isolated `HOME` and `CCB_SOURCE_HOME`;
- project-local `AGENT_ROLES_STORE`;
- fake provider roles for deterministic replies;
- no real provider credentials required;
- cleanup must end with `kill_status: ok`.

Purpose:

- prove script/state/topology/release correctness;
- keep CI-grade regression coverage;
- inject abnormal states deterministically.

### Real Provider Capability Lab

Run from a separate external test root:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-<stamp>
```

Required controls:

- command: `/home/bfly/yunwei/ccb_source/ccb_test`;
- explicitly selected provider profiles for `ccb_frontdesk`,
  `ccb_planner`, `ccb_orchestrator`, `ccb_task_detailer`, `coder`, and
  `code_reviewer`;
- either inherited real provider auth by explicit test setup, or a project-
  local provider home prepared only for this lab;
- no tests run from the source checkout as a live runtime directory;
- all evidence copied or linked into plan-tree history after the lab.

Purpose:

- discover real semantic reliability;
- test route selection under ambiguous user inputs;
- test worker/reviewer negotiation;
- test provider-specific stalls, prompts, and formatting drift;
- measure whether roles stay inside their boundaries.

## Complexity Ladder

Every route should be tested at multiple complexity levels.

| Level | Name | Scope | Expected Purpose |
| :--- | :--- | :--- | :--- |
| L0 | Runtime sanity | mount, ask, status, release only | Prove environment and dynamic topology are healthy. |
| L1 | Simple document task | one small Markdown or config update | Prove direct route and artifact import without code risk. |
| L2 | Simple code task | one narrow code change plus focused test | Prove worker/reviewer loop and contract-cited review. |
| L3 | Detail-needed task | task requires source inspection and step expansion | Prove `ccb_task_detailer` adds value before execution. |
| L4 | Ambiguous or conflicting task | user intent is incomplete or contradicts plan constraints | Prove clarification, blocked, or macro adjustment routing. |
| L5 | Stress task | larger scope, multiple files, deliberate reviewer challenge | Expose context drift, overreach, hidden fallback, and partial handling. |

Phase 6 should not require L5 to pass. L5 exists to discover the first
reliable breaking point.

## Required Route Tests

### `direct_execution`

Purpose:

- prove planner can produce a macro task packet that is already executable;
- prove orchestrator skips `ccb_task_detailer`;
- prove one `worker + code_reviewer` pair can finish and release cleanly.

Minimum real cases:

- L1 document update;
- L2 code/test update.

Pass evidence:

- `route_decision_correct=true`;
- `detailer_activated=false`;
- worker/reviewer ask artifacts exist;
- reviewer cites `execution_contract`;
- `round_result=pass`;
- dynamic agents released or explicitly retained with evidence.

### `needs_detail`

Purpose:

- prove orchestrator can detect that macro artifacts are insufficient;
- prove `ccb_task_detailer` can create detail packet and step files;
- prove execution resumes after detail import.

Minimum real cases:

- L3 task requiring source inspection before implementation;
- L3 task requiring task-local clarification before execution.

Pass evidence:

- `route_decision_correct=true`;
- `detailer_activated=true`;
- `detail_packet`, `detail_summary`, and required step files imported;
- planner does not rewrite detail docs;
- worker/reviewer executes only after detail readiness;
- `round_result=pass`.

### `macro_adjustment_request`

Purpose:

- prove orchestrator/detailer can stop execution when macro assumptions are
  wrong;
- prove the task returns to planner without mounting workers.

Minimum real cases:

- request conflicts with Decision 020 by asking topology to become a semantic
  dispatch DSL;
- request invalidates a macro task assumption discovered during detail review.

Pass evidence:

- `route_decision_correct=true`;
- no worker/reviewer mount;
- visible `macro_adjustment_request` evidence imported;
- `next_owner=planner`;
- task is not marked `done`.

### `blocked`

Purpose:

- prove missing hard dependency or unresolved user decision becomes explicit
  blocker evidence, not fake success.

Minimum real cases:

- missing external credential/tool;
- user decision required before execution can be safe.

Pass evidence:

- `route_decision_correct=true`;
- blocker evidence imported;
- task status is `blocked`;
- no hidden fallback, no scope shrinkage, no execution without authority.

### `partial_completion`

Purpose:

- prove the system can preserve accepted progress without pretending the whole
  task is complete.

Minimum real cases:

- multi-step L4/L5 task where one bounded step succeeds and another exceeds
  the single-round budget;
- reviewer accepts completed step evidence and rejects remaining work as
  unfinished.

Pass evidence:

- explicit step list exists;
- completed and unfinished steps are separated;
- `round_result=partial`;
- task status is not `done`;
- planner import receives compact remaining-work summary.

## Abnormal-State Injection

These tests should deliberately create conditions that are expected to stress
the workflow.

| Scenario | Expected Correct Behavior |
| :--- | :--- |
| Reviewer rejects once | Worker gets exactly one rework chance inside the round, then reviewer decides. |
| Reviewer rejects twice | Round ends `partial`, `replan_required`, or `blocked`; no repeated hidden retry. |
| Provider output lacks machine marker | Import rejects success or records blocker; no success inference. |
| Worker omits contract reference | Reviewer or import rejects approval. |
| Detailer oversteps into roadmap edits | Script import rejects authority mutation or records role-boundary violation. |
| Orchestrator mounts workers for macro adjustment | Test fails; macro adjustment must return to planner. |
| Dynamic release while busy | Agent becomes `retained_busy`; no forced kill. |
| Ask timeout or transport failure | Blocker evidence is recorded; task does not become `done`. |
| Restart between route and execution | Runner resumes from committed state without duplicate dynamic agents. |
| User clarification arrives late | State resumes only through normalized answer import. |

## Metrics And Scoring

Each real-provider run should produce a structured assessment row.

Required fields:

- task id and complexity level;
- provider mix;
- expected route and observed route;
- `route_decision_correct`;
- required artifacts present;
- detailer activation expected/observed;
- worker/reviewer ask success;
- reviewer contract citation;
- round result;
- final task status;
- dynamic release result;
- residue check result;
- role-boundary violations;
- authority-write violations;
- unresolved blockers;
- human diagnosis summary.

Recommended scoring:

| Score | Meaning |
| :--- | :--- |
| `pass` | Expected route, expected status, evidence complete, cleanup clean. |
| `valid_non_success` | Expected `partial`, `blocked`, or `replan_required` with correct evidence. |
| `system_failure` | CCB state, topology, ask, import, or release failed incorrectly. |
| `role_failure` | Agent chose wrong route, overstepped authority, ignored contract, or hid fallback. |
| `provider_failure` | Provider auth, timeout, formatting, or interaction failure blocked the task. |
| `test_design_failure` | Task prompt or acceptance was ambiguous enough to invalidate the result. |

## Deep Analysis Report

After the assessment run, create a report under plan-tree history:

```text
docs/plantree/plans/agentic-loop-workflow/history/
  phase6-real-capability-assessment-<YYYYMMDD>.md
```

The report should include:

- environment and provider profiles used;
- task matrix summary table;
- pass and valid non-success counts;
- failure taxonomy counts;
- strongest capability observed;
- first complexity level where reliability breaks;
- top role-boundary drift findings;
- top script/runtime defects;
- provider-specific issues;
- recommended next implementation work;
- whether Phase 6A, Phase 6B, or neither can be claimed.

## Phase 6A And Phase 6B Claims

Use two separate claims.

### Phase 6A: Program Matrix

Can be claimed when:

- fake-provider source-wrapper matrix passes;
- abnormal-state injection passes deterministic checks;
- no dynamic runtime residue remains after cleanup;
- focused unit/CLI tests pass.

Meaning:

- the program kernel and workflow state machine can support the workflow.

### Phase 6B: Real Capability

Can be claimed when:

- real-provider lab completes L1 and L2 `direct_execution`;
- real-provider lab completes at least one L3 `needs_detail`;
- real-provider lab correctly handles at least one `blocked` or
  `macro_adjustment_request`;
- reviewer rejection or partial handling is observed with correct evidence;
- all failures are classified without losing state or cleanup authority.

Meaning:

- Satinoös has initial real workflow capability for bounded single-round tasks.

Phase 6B still does not mean:

- autonomous multi-round production workflow;
- unattended daemon operation;
- broad real-world reliability across providers;
- no need for human escalation.

## Execution Order

Recommended order:

1. Run Phase 6A fake-provider matrix.
2. Fix any system-level blocker before using real providers.
3. Run real-provider L0/L1 sanity tasks.
4. Run L2 direct code task with reviewer contract citation.
5. Run L3 detail-needed task with detail packet and step files.
6. Run L4 blocked or macro-adjustment task.
7. Run reviewer rejection and partial-completion stress tasks.
8. Run cleanup and residue audit.
9. Write the deep analysis report.

## Stop Conditions

Stop the assessment early only when:

- `ccb_test --diagnose` fails;
- source-wrapper root or provider-home isolation is invalid;
- authority state is corrupted;
- dynamic release leaves unrecoverable runtime residue;
- repeated provider auth failures make semantic assessment impossible.

Do not stop merely because a task returns `partial`, `blocked`, or
`replan_required`. Those are expected capability observations when evidence is
complete.
