# Single-Lane Multi-Workgroup Release Goal

Date: 2026-07-12
Status: In progress; Decision 029 closure package planned before remaining G6 matrix

## Goal

Ship the next CCB version only after one visible, frontdesk-started Workflow
Lane can execute a real macro task through multiple independently reviewed
workgroups and a controlled integration gate:

```text
frontdesk
  -> planner
  -> optional task_detailer
  -> one orchestrator bundle
  -> deterministic controller
  -> 1..4 (worker --chain--> reviewer) workgroups
  -> integration worktree and tests
  -> project-root promotion and verification
  -> ccb_round_reviewer
  -> script-owned task result
  -> complete dynamic release
```

The same release must add opt-in Config V3 for dynamic workflow role/provider/
model/capacity declaration, preserve Config V2 static behavior, and pass clean
package/install/update gates.

## Current Baseline

Already available and preserved:

- frontdesk-to-planner handoff, route selection, optional detailer, one-pair
  direct execution, bounded review/rework, round review, rollback, and release;
- durable ask submission intent, callback/persisted-terminal resume, and
  unknown-submission pause;
- dynamic role profiles, Git worktree substrate, mount-only topology,
  deterministic window placement, six-pane execution windows, overflow,
  busy-retain, release retry, and visible sidebar evidence;
- source/fake and real-provider single-workgroup evidence;
- commit `34027943` adds the first G1 foundation: strict one-to-four-node
  bundle import/validation, canonical work packets, deterministic ordering,
  explicit orchestrator candidate import, one-node compatibility evidence,
  and a multi-node pre-bind pause. Evidence is recorded in
  [../history/single-lane-multi-workgroup-g1-foundation-20260710.md](../history/single-lane-multi-workgroup-g1-foundation-20260710.md).
- commit `0c2f19ef` closes R1: semantic task revision fencing, canonical
  effective-capacity binding, adaptive selection evidence, node-keyed
  exact-once intent, sole node-map one-group execution, immaculate freshness
  enforcement, V2 replan-safe compatibility, and removal of the normal
  post-worker orchestrator call. Evidence is recorded in
  [../history/single-lane-r1-authority-runtime-closure-20260711.md](../history/single-lane-r1-authority-runtime-closure-20260711.md).
- commits `615460ec`, `95d9a409`, `6c2a15ad`, and `fcf07b3a` close C1/P1:
  strict Config V3 and sanitized effective authority, V2 migration preview,
  complete RolePack/provider validation, adaptive bundle/node role contracts,
  and install/projection tests. Evidence is recorded in
  [../history/single-lane-wave1-config-rolepack-closure-20260711.md](../history/single-lane-wave1-config-rolepack-closure-20260711.md).
- commits `f3b6b7a6`, `bd7bcbd7`, `64f95b1b`, `912764f6`, `502cc3e1`,
  and `c64ab341` close Wave 2: exact controller-owned Git transactions,
  one-to-four-workgroup topology/capacity, and strict deterministic evidence.
  Evidence is recorded in
  [../history/single-lane-wave2-git-topology-evidence-closure-20260711.md](../history/single-lane-wave2-git-topology-evidence-closure-20260711.md).
- commits `8d3fc102`, `92da3faf`, and `bca51abd` close the G3 scheduler source
  kernel; `fb4b26c7`, `96172d92`, and `94ea6d73` close test-runtime and
  accelerator ownership exposed by the direct full-suite gate. Evidence is
  recorded in
  [../history/single-lane-wave3-g3-scheduler-closure-20260711.md](../history/single-lane-wave3-g3-scheduler-closure-20260711.md).
- commits `5163ad6f`, `9fceb5de`, and `b42ec3b2` close G5 source/fake
  acceptance: ten scenario rows, one-to-four workgroup source-wrapper flows,
  restart, rework, failure, integration/root verification failure, rollback,
  release, cleanup, and B7 campaign normalization. Evidence is recorded in
  [../history/single-lane-g5-source-fake-acceptance-20260711.md](../history/single-lane-g5-source-fake-acceptance-20260711.md).

Remaining acceptance gaps:

- Config V3 visible two-workgroup Codex execution is proven, but broader
  opened-project enablement remains gated until all G6 rows complete;
- visible three/four-workgroup, restart, busy-retain, and qualified
  non-Codex provider evidence is still missing;
- no packed-candidate install/update/rollback evidence exists for this branch.

## Scope

- One project, one active Workflow Lane, one macro task, one loop round.
- One to four workgroups, each exactly one worker and one reviewer.
- Parallel, serial, and mixed acyclic dependency graphs.
- One bounded reviewer rework cycle per node by default.
- Git-worktree-isolated multi-workgroup execution and controller-owned
  integration.
- Exact-once event-driven ask submission and crash recovery.
- Visible window/pane placement, busy retain, full release, and residue audit.
- Config V3 parser/compiler/validator/migration dry-run and V2 regression.
- Source, fake-provider, real-provider, package, fresh-install, upgrade, and
  rollback verification.

## Non-Goals

- Concurrent Roadmap Graph lanes or multiple global planners.
- Multiple orchestrators for one bundle.
- Arbitrary user-authored workflow DSL or topology communication graph.
- Automatic semantic merge-conflict resolution.
- Non-Git multi-workgroup write execution in the first release.
- Long-running workflow daemon or unlimited rework.
- Default conversion of existing V2 projects to V3.
- Gemini release gating. Provider-specific claims for OpenCode or Grok require
  separate authenticated evidence and are not inferred from core Codex/Claude
  tests.

## Release Invariants

1. Provider replies are evidence, never task/topology/runtime authority.
2. Only scripts import bundle, node, integration, round, and task state.
3. Mount topology contains agents, windows, placement, lifecycle, and observed
   readiness only; no semantic dispatch DSL is reintroduced.
4. A reviewer never reviews an unpromoted shared-project guess. It reviews the
   exact node worktree tree digest later committed by the controller.
5. No node result enters integration before its reviewer passes.
6. No task reaches `done` before all required nodes, integration tests,
   project-root verification, and round review pass.
7. A partial, blocked, replan, unknown, or failed final result cannot leave an
   unaccepted promoted project-root delta.
8. Slow providers remain pending. Observer health limits may diagnose a broken
   runtime, but elapsed business time alone is not a task failure.
9. All dynamic immaculate roles release or produce bounded busy/residue
   evidence; resident frontdesk/planner remain visible.
10. V2 static config behavior remains byte/behavior compatible where the
    existing contract is defined.
11. Worker/Reviewer semantic communication is node-local `ask --chain`;
    controller code does not relay reviewer or rework prompts.
12. Frontdesk/Planner semantic communication is one Frontdesk-authored
    `ask --silence`; controller code validates, deduplicates, records, wakes,
    and recovers but never observes a completed reply to rewrite Planner prose.

## Production-Ready Definition

For this goal, "single-lane production-ready" means all of the following at
the same frozen commit:

- one project has one active Workflow Lane and one macro task at a time;
- that task can use one to four reviewed workgroups in parallel, serial, or
  mixed DAG form without enabling concurrent Roadmap Lanes;
- the one-workgroup case uses the same bundle, node state, recovery, review,
  integration, result, and release kernel as the multi-workgroup case;
- Config V2 remains the static compatibility surface and Config V3 is an
  opt-in validated dynamic surface;
- source, fake-provider, visible Codex/Claude, UI/lifecycle, restart/failure,
  package install, update, and rollback gates all pass;
- the packed candidate can be installed and run outside the source checkout
  with evidence tied to one commit and artifact digest.

Production-ready does not automatically authorize registry publication.
Publishing, tagging, and changing the installed global CCB remain a separate
explicit user decision after the candidate gate passes.

## Remaining Dependency Graph

The critical path is deliberately ordered:

```text
F1 authority-interface freeze
  -> G1 one-node generalized kernel
  -> G2 Git worktree/integration kernel
  -> G3 ready-frontier scheduler and lifecycle
  -> G5 source/fake acceptance
  -> G6 visible real-provider acceptance
  -> G7 packed-candidate/install/update/rollback gate
```

Config V3 and RolePack work may proceed beside the runtime critical path only
after F1 freezes task revision, capacity snapshot/digest, bundle/node schemas,
role names, and capacity terminology. They must rejoin before G3 capacity and
G5 acceptance. Test/evidence scaffolding may proceed early, but it cannot
claim runtime behavior before the implementation exists.

## Whole-Block Parallel Delegation Plan

Workers may be used for coherent implementation packages, not for validation
authority and not for several agents editing the same kernel concurrently.
Each package has one owner, one dedicated Git worktree/branch, an explicit
file boundary, focused tests, and a clean commit.

### Wave 0: Talk2 Contract Freeze - Landed

`talk2` owns F1 and does not delegate it. The remaining V1 authority fields,
capacity snapshot interface, node-state enum, exact-once intent key, result
mapping, ownership boundaries, and adaptive one-to-four selection rules are
frozen by
[Decision 026](../decisions/026-authority-envelope-and-adaptive-workgroup-selection.md).
Implementation must update the decision first if it discovers a contradiction.

### Wave 1: Three Parallel Whole Blocks

| Package | Scope | Primary ownership | Depends on |
| :--- | :--- | :--- | :--- |
| R1 G1 runtime closure | Task revision/capacity binding, sole node-map one-group execution, node-keyed intent/recovery, node work-packet consumption, remove normal post-worker orchestrator | Bundle, plan-task, runner, ask-first, role-output import services and focused tests | F1 |
| C1 Config V3 core | Version dispatch, V3 models/compiler/validator/effective JSON/migration dry-run, required roles/provider/model/RolePack/capacity checks, frozen V2 corpus | Config loader/models/CLI validation and new config tests; no loop runtime edits | F1 |
| P1 RolePack contract | Orchestrator candidate output, node worker/reviewer, integration and round-review compact contracts, role projection tests | RolePack/spec/projection surfaces only; no controller authority code | F1 |

`talk2` reviews and integrates R1 first, then C1 and P1 one at a time. The
wave closes only after focused suites and the non-Gemini repository gate pass
on the combined branch.

### Wave 2: Three Parallel Whole Blocks - Landed

| Package | Scope | Primary ownership | Depends on |
| :--- | :--- | :--- | :--- |
| R2 Git integration kernel | Clean-Git/scope preflight, node and integration worktrees, tree digest, reviewed commit, deterministic merge/test, promotion, rollback, cleanup | New integration service plus isolated Git tests | R1 |
| T1 topology/capacity generalization | Compile one to four pairs, semantic versus physical limits, names/windows/overflow, owner-scoped release and busy-retain | Topology, capacity, placement/lifecycle services and focused tests | R1 + C1 |
| E1 evidence and fake harness | Bundle/node/Git/integration/release/B7 schemas, deterministic fixtures, negative classifications | New or existing evidence scripts and dedicated tests; no source authority mutation | R1 contract |

`talk2` integrates R2 before T1 and E1, then runs the combined Git/topology/
evidence matrix. A package that requires another package's private helper must
stop and request an interface decision instead of copying the helper.

The required order is complete through `c64ab341`; the combined gate passed
`249` tests. This closes component readiness only, not live scheduler behavior.

### Wave 3: Central Scheduler Closure - Landed

The complete G3 scheduler block is integrated through `bca51abd`:
ready-frontier computation, submit-all-ready behavior, the original
controller-relayed per-node review/rework flow, dependency unblocking,
callback/persisted-terminal recovery,
structured final results, real R2 integration, raw T1 release authority, and
full dynamic release. Runtime ownership hardening through `94ea6d73` closes
the process-residue defect exposed by the direct full-suite gate.

A separate test-only worker may prepare failure/permutation fixtures in new
test files after scheduler interfaces freeze. It must not change scheduler
source or weaken an expected failure to make the suite pass.

### Waves 4-5: Direct Acceptance And Candidate Packaging

Workers are not acceptance authorities in these waves. `talk2` directly runs
G5-G7, audits raw evidence, and decides pass/blocker. A worker is dispatched
only when a concrete defect requires a bounded source repair; after that
repair, direct acceptance restarts from the affected gate.

## Worker Delivery Contract

Every delegated package must return:

- base commit, worktree path, branch, final commit SHA, and clean `git status`;
- changed-file list and confirmation that no out-of-scope file was edited;
- implemented contract and any interface assumption;
- exact focused test commands and results, plus `py_compile` and
  `git diff --check` where applicable;
- failing-before evidence for each repaired bug when practical;
- residual risks, deferred cases, and any discovered plan contradiction.

Workers must not merge, publish, install globally, run destructive cleanup,
reuse consumed real-test roots, or claim production readiness. They must not
introduce silent serialization, fake success, timeout-as-business-failure,
provider-reply authority, shared-worktree writes, hidden fallback, reduced
maximum capacity, or test-only bypasses.

## Talk2 Review And Integration Protocol

For each returned package, `talk2` must:

1. compare the diff with this goal and the package file boundary;
2. inspect authority, crash-window, rollback, lifecycle, and compatibility
   behavior before considering the worker's test report;
3. run the package's focused tests directly in its worktree;
4. integrate one commit/package at a time into
   `workflow/agentic-loop-topology`, resolving no semantic conflict by guess;
5. rerun affected adjacent suites after each integration and the non-Gemini
   repository gate after each wave;
6. record blockers honestly and return concrete repairs to a worker only when
   source modification is required;
7. keep the workflow worktree clean and update Plan Tree evidence at each
   closed gate.

Worker self-tests are supporting evidence only. Final source, fake-provider,
visible-project, package, and release acceptance belongs to `talk2`.

## Implementation Phases

### G0 Contract And Baseline Freeze - Complete

- Land Decision 025, bundle schema, node/round state schema, result mapping,
  workspace/integration policy, V3 role lifecycle correction, and evidence
  contract.
- Freeze current one-workgroup tests and a V2 config corpus before source
  changes.
- Record the exact source test baseline and dirty/generated-file exclusions.

Gate: planning links resolve, schemas have rejection cases, and no core
behavior is left to implementation-time interpretation.

### G1 Bundle Authority And One-Node Generalization - Complete

- Add `ccb.loop.orchestration_bundle.v1` validation and script-owned import.
- Add a deterministic one-node bundle for the validated simple fast path.
- Replace scalar worker/reviewer stage state with a node map while preserving
  existing one-node external behavior.
- Remove the normal post-worker orchestrator aggregation call; retain fresh
  activation only for structural replan.

Gate: all current one-workgroup tests pass through the generalized engine and
provider replies still cannot write authority.

Direct evidence: commit `0c2f19ef`, `195` owned tests, `117` adjacent tests,
and the non-Gemini portion of the full repository run passed. Multi-node
execution remains blocked intentionally at the G2/G3 boundary.

### G2 Worktree And Integration Kernel - Complete

- Add clean-Git/scope preflight, node worktree/branch creation, tree-digest
  capture, reviewer-pass commit, deterministic integration worktree, merge,
  test, project-root promotion, and rollback.
- Reject overlapping parallel scope claims, wrong-base workspaces, reviewer
  tree drift, merge conflicts, and project-root drift.

Gate: deterministic two-node synthetic tests prove disjoint merge, dependency
wave, conflict failure, rollback, and preservation of unrelated files.

Direct evidence: commits `f3b6b7a6` and `bd7bcbd7`; `42` focused real-Git
tests, `61` adjacent tests, exact intent/lookalike rejection, failed-root-test
quarantine and rollback, recovery, and cleanup passed.

### G3 Multi-Workgroup Scheduler And Lifecycle - Complete

- Submit all ready-frontier workers in one runner activation.
- Resume from callbacks or persisted terminal jobs without polling or business
  timeout.
- Submit each reviewer only after its worker; run bounded node-local rework;
  unblock dependents only after reviewed integration.
- Generalize topology, naming, placement, capacity, release, busy-retain, and
  residue evidence for one to four pairs plus dynamic control roles.

Source gate: exact-once crash-window, frontier, dependency, review/rework,
R2 integration, raw topology/release, runtime ownership, and residue tests
pass. Scheduler-driven fake-provider 2/3/4-workgroup flows remain the G5 gate.

Direct evidence: commits `8d3fc102`, `92da3faf`, `bca51abd`, `fb4b26c7`,
`96172d92`, and `94ea6d73`; the integrated full source gate passed `4210`
tests with zero current-run command-line and cwd-owned runtime residue.

### G4 Config V3 - Complete, Runtime Enablement Gated

- Implement V3 version dispatch, models, validator, effective compiler,
  `config validate --json`, effective-config reporting, and migration dry-run.
- Require resident `frontdesk`/`planner`; require dynamic detailer,
  orchestrator, coder, code reviewer, and round reviewer profiles.
- Validate provider/model/RolePack/default resolution, workgroup/agent limits,
  profile maxima, Git-worktree multi-group policy, generated names, and
  forbidden V2/V3 field mixing.

Gate: V2 corpus is unchanged; valid V3 opens a generated dynamic project;
invalid V3 fails before provider or tmux startup.

Source/config evidence: commits `6c2a15ad` and `fcf07b3a`; parser, effective
config, diagnostics, migration preview, provider/model/RolePack/capacity, and
V2 compatibility gates passed. Opened-project enablement remains gated by G6
visible real-provider acceptance.

### G5 Direct Source And Fake-Provider Acceptance - Complete

- Run focused unit/integration suites, full source suite, py_compile, static
  schema guards, source-wrapper smoke, and fake-provider matrix.
- Prove one-node compatibility plus 2, 3, and 4-workgroup task completion,
  rework, partial, blocked, replan, integration failure, restart recovery,
  busy retain, and release.

Gate result: passed for source/fake scope. Direct evidence: commits
`5163ad6f`, `9fceb5de`, and `b42ec3b2`; ten-scenario campaign row count `10`,
`37` full-flow tests, `126` adjacent tests, changed-source `py_compile`,
`pyflakes`, `git diff --check`, and narrow residue scans passed. See
[../history/single-lane-g5-source-fake-acceptance-20260711.md](../history/single-lane-g5-source-fake-acceptance-20260711.md).

### G6 Visible Real-Provider Acceptance - Active, Two-Group Rework Passed

- From `/home/bfly/yunwei/test_ccb2`, use the current source `ccb_test`, inherit
  system provider environment, use a lab-local Role store, and open a visible
  project/UI.
- Start with a natural user prompt to frontdesk and inspect every handoff.
- Run separate real tasks with two, three, and four workgroups. The four-group
  run is mandatory if V3 permits `max_workgroups = 4`.
- Prove actual worker overlap, per-node reviewer order, integration, tests,
  project-root output, round review, pane/sidebar state, and zero final dynamic
  residue.
- Prove each node has one controller-submitted root Worker job, Reviewer jobs
  are Worker-initiated chain children, and the controller accepts only a
  bounded assigned-Reviewer lineage ending in pass.
- Restart ccbd during active work once and inject one provider/node failure in
  a separate run.

Gate: raw project/task/job/topology/Git/UI evidence agrees with B7. Scripts may
prepare and collect evidence but cannot substitute for the opened project.

Checkpoint: the 2026-07-12 visible Codex run passed a natural two-workgroup
mixed DAG with Worker-owned Reviewer chains, deterministic Git integration,
`79` root tests, Round Reviewer pass, complete worktree cleanup, and zero
dynamic residue. See
[../history/g6-worker-owned-review-chain-real-provider-20260712.md](../history/g6-worker-owned-review-chain-real-provider-20260712.md).

Decision 028 then passed a second fresh visible two-workgroup run with an exact
Frontdesk-owned silent Planner handoff and genuine Reviewer findings in both
nodes. Each Worker completed one bounded rework/recheck cycle, root verification
passed `7` tests, the Round Reviewer passed, temporary Git state was removed,
and only resident Frontdesk/Planner panes remained. See
[../history/decision028-frontdesk-direct-handoff-real-provider-20260712.md](../history/decision028-frontdesk-direct-handoff-real-provider-20260712.md).

A follow-up fresh long-root run closed successful-silence delivery, relocated
managed-caller socket, isolated Worker authority-ref, and Round Reviewer
request-spill gaps. The one-group task completed with a Worker-owned Reviewer
chain, `13` root tests, an inline compact round envelope, empty final topology,
and clean project shutdown. The final non-provider-blackbox repository gate
passed `4324` tests; this strengthens V0/Decision 028 evidence but does not
replace the remaining three/four-group, restart, busy-retain, or provider rows.
The remaining bullets above still gate G6 closure.

### G6C Planner Feedback And Task-Set Closure - Planned

- Add a restricted direct Detailer-to-Planner silent replan request when source
  inspection or user clarification changes macro scope, dependencies,
  acceptance, risk, or Roadmap semantics.
- Keep local Detailer completion on the direct return to a fresh Orchestrator.
- Persist task-set parent identity and stop treating decomposition as macro
  completion.
- Aggregate all-pass, pass+blocked, pass+partial, multiple-replan, all-blocked,
  and system-failure outcomes deterministically after child release/cleanup.
- Submit exactly one revision-fenced Planner closure backfill and one required
  Frontdesk status notification, with crash recovery and stale-revision
  rejection.
- Run source/fake and fresh visible real-provider tests for local detail,
  user-driven replan, mixed closure, final-child replay, restart, and revision
  races.

Gate: the source request, task-set record, child authority, Planner
Brief/Roadmap/TODO update, Frontdesk status, and final user summary agree. No
Controller-authored semantic relay, premature completion, duplicate ask,
stale update, hidden downgrade, or runtime residue is accepted. Detailed
authority and test design:
[../topics/planner-feedback-and-task-set-closure-plan.md](../topics/planner-feedback-and-task-set-closure-plan.md).

### G7 Release Candidate And Deployment Gate - Pending

- Merge the accepted workflow branch into a clean release commit through the
  project branch policy; do not publish from a dirty worktree.
- Query the current npm version, choose the next unused SemVer feature release,
  synchronize package/version/changelog surfaces, and create the exact tag
  only after the commit is frozen.
- Run `npm pack --dry-run`, inspect contents, install the packed candidate into
  a fresh external prefix, verify `ccb`, `ask`, config V2, config V3, roles,
  and a visible installed-candidate workflow task.
- Test update from the current public stable version and a rollback to that
  version.
- Produce a deployment-readiness report tied to the commit, packed artifact
  hash, V2/V3 configs, external install root, real-project root, and rollback
  evidence.

Gate: package name, candidate version, artifact hash, commit, external install,
visible workflow, update, rollback, and deployment-readiness report all agree.
Passing this gate marks the single-lane candidate production-ready.

### G8 Explicit Publication - User Authorization Required

- Resolve the exact registry/package/version and verify that the version is
  unused immediately before publishing.
- Create the exact tag only from the frozen accepted commit.
- Publish only after explicit user approval, then verify registry metadata,
  fresh download/install, CLI entrypoints, payload hash, tag, and release
  notes.

Gate: publication intent, registry state, commit, tag, package digest, and
post-publish installation agree. G8 changes the state from production-ready to
released; it is never entered automatically by G7.

## Required Real Tasks

Use inspectable tasks whose work units are independently meaningful but need a
final integration gate. At minimum:

- two groups: Python library core + CLI/tests;
- three groups: persistence/domain module + command/API module + documentation
  and integration tests;
- four groups: parser/model + storage + CLI + test/documentation integration,
  with at least one declared dependency wave.

Prompts must be ordinary product requests. They must not tell frontdesk how to
route, tell orchestrator how many groups to create, or tell providers which
test result to report.

## Visible Real-Validation Campaign

All runs use fresh roots under `/home/bfly/yunwei/test_ccb2`, the explicit
source `ccb_test`, inherited system provider environment, and a root-local
`AGENT_ROLES_STORE`. The project must be opened in a separate visible terminal
or WezTerm window. Script output alone is insufficient.

| Run | Natural task shape | Required proof |
| :--- | :--- | :--- |
| V0 one group | Small bounded code/test task | Compatibility path uses the generalized node kernel; no post-worker orchestrator; pass and zero dynamic residue. |
| V1 two groups | Core library plus independent CLI/tests | Both workers overlap in real time, each reviewer follows only its worker, deterministic integration and root tests pass. |
| V2 three groups | Persistence/domain, API/command, docs/integration | Mixed DAG dependency unblocks from accepted predecessor commits; independent work still overlaps. |
| V3 four groups | Parser/model, storage, CLI, tests/docs | Advertised maximum is real, fourth pair uses expected execution-window overflow, integration order is deterministic. |
| V4 restart/failure | Separate active two-or-more-group task | Restart after durable intent causes no duplicate ask; worker failure, reviewer rework, merge/test failure, rollback, busy-retain, and final cleanup are visible and correctly classified. |
| V5 installed candidate | One normal task from the packed external install | Same frontdesk-started behavior works outside source checkout; V2 and V3 open correctly; update and rollback remain usable. |

Core acceptance uses Codex for frontdesk/planner/orchestrator/detailer/workers
and supports a Claude `ccb_round_reviewer` cross-provider gate. Provider/model
selection must come from Config V3, not test-script substitution. OpenCode or
Grok evidence is recorded only when authenticated and actually run; Gemini is
not a release gate.

For every V0-V5 run, capture raw task index/artifacts, bundle and node state,
ask jobs and terminal snapshots, Git branches/worktrees/commits, integration
and project-root digests, test commands/results, topology desired/observed
state, window/pane/sidebar state, release counts, retained blockers, final
process residue, config digest, and B7 classification. `talk2` compares raw
evidence with B7 before accepting the run.

Stop the campaign immediately on provider-reply authority, duplicate ask,
hidden serialization of independent nodes, unreviewed integration, dirty or
wrong-base worktree, scope escape, false pass, rollback drift, cross-loop
release, missing UI evidence, or unexplained residue. Repair the source and
restart from the affected run with a new root; do not normalize the failure
away.

## Acceptance Summary

The production-ready goal is complete at G7 only when:

- one-node behavior is regression clean;
- real 2/3/4-workgroup evidence exists for the advertised maximum;
- all required nodes are independently reviewed before integration;
- exact-once restart recovery and failure semantics are proven;
- project-root authority and rollback are correct;
- UI placement and dynamic release are visibly correct;
- Detailer macro correction and task-set Roadmap closure are exact-once,
  revision-fenced, and visibly reported;
- V3 is implemented and validated while V2 remains compatible;
- a clean packed candidate installs and executes the same workflow externally;
- final deployment metadata and rollback evidence are explicit and agree.

Actual release is complete only after separately authorized G8 publication
and post-publish verification.

## Evidence

The canonical evidence fields and test matrix are defined in
[../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md).
Release evidence belongs under `history/` and must link to the exact commit,
config digest, package hash, project root, and raw runtime paths.

Wave 2 component evidence:
[../history/single-lane-wave2-git-topology-evidence-closure-20260711.md](../history/single-lane-wave2-git-topology-evidence-closure-20260711.md).

Wave 3 scheduler evidence:
[../history/single-lane-wave3-g3-scheduler-closure-20260711.md](../history/single-lane-wave3-g3-scheduler-closure-20260711.md).

G5 source/fake acceptance evidence:
[../history/single-lane-g5-source-fake-acceptance-20260711.md](../history/single-lane-g5-source-fake-acceptance-20260711.md).
