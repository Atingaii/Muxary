# Single-Lane Multi-Workgroup Modification And Test Plan

Date: 2026-07-12
Status: G6 two-workgroup Codex baseline passed; remaining visible matrix active

F1 authority interfaces and adaptive group selection are frozen by
[Decision 026](../decisions/026-authority-envelope-and-adaptive-workgroup-selection.md).
Worker-to-Reviewer collaboration and the minimal controller boundary are
frozen by
[Decision 027](../decisions/027-worker-owned-review-chain-and-minimal-controller.md).
Decision 026 controls where this older topic is less specific: Config V3
always requires an explicit one-to-four-node candidate, Config V2 alone may
use the deterministic one-node compatibility bundle, provenance is artifact
metadata rather than semantic bundle content, and node count is selected by
the orchestrator from complexity and cutability rather than by test scripts.
Decision 027 applies to that Config V3/generalized scheduler path. The frozen
Config V2 static single-node path remains a compatibility surface, not a
template for new controller-owned review communication.

R1 landed in commit `0c2f19ef`; direct evidence is recorded in
[single-lane-r1-authority-runtime-closure-20260711.md](../history/single-lane-r1-authority-runtime-closure-20260711.md).
Config V3 and adaptive RolePack contracts landed in `615460ec`, `95d9a409`,
`6c2a15ad`, and `fcf07b3a`; direct evidence is recorded in
[single-lane-wave1-config-rolepack-closure-20260711.md](../history/single-lane-wave1-config-rolepack-closure-20260711.md).
Wave 2 Git integration, topology/capacity, and evidence work landed through
`c64ab341`; direct evidence is recorded in
[single-lane-wave2-git-topology-evidence-closure-20260711.md](../history/single-lane-wave2-git-topology-evidence-closure-20260711.md).
Wave 3 scheduler and runtime-ownership work landed through `94ea6d73`; direct
evidence is recorded in
[single-lane-wave3-g3-scheduler-closure-20260711.md](../history/single-lane-wave3-g3-scheduler-closure-20260711.md).
G5 source/fake direct acceptance landed through `b42ec3b2`; direct evidence is
recorded in
[single-lane-g5-source-fake-acceptance-20260711.md](../history/single-lane-g5-source-fake-acceptance-20260711.md).
The Decision 027 two-workgroup Codex baseline is recorded in
[g6-worker-owned-review-chain-real-provider-20260712.md](../history/g6-worker-owned-review-chain-real-provider-20260712.md).
The next gate is the remaining G6 three/four-group, restart, rework,
busy-retain, and provider-profile matrix from fresh opened projects.

## Objective

Generalize the current one-pair direct-execution path into one task-round
engine that safely executes one to four `Worker + Reviewer` workgroups under a
single orchestration bundle. This is the last workflow architecture expansion
before the next release; concurrent roadmap lanes remain deferred.

The target is not a larger controller-owned prompt chain. The controller must
submit all currently ready root Worker jobs in one activation, stop, and
resume from durable root-job completion events. Each Worker collaborates
directly with its assigned Reviewer through bounded `ask --chain`. Serial
depth follows real dependencies, while independent Workers and node-local
reviews overlap.

## Baseline Findings

The pre-G3 source behavior that required deliberate change was:

- `loop_ask_first.py` constructs exactly one
  `loop-<loop>-coder-1` and one `loop-<loop>-code_reviewer-1`.
- mount topology, pending payloads, stage artifacts, failure synthesis, root
  promotion, and round-review messages accept scalar worker/reviewer values.
- one `ask_first_submission_intent.json` records a single current intent rather
  than node/purpose/attempt identities.
- the normal direct path asks an orchestrator again after worker/reviewer
  completion, although Decision 022 assigns bundle design to the pre-execution
  activation and deterministic integration to scripts.
- worker workspace changes are promoted to the project root before review;
  repeating that behavior concurrently would race and make rollback ambiguous.
- existing `worker=2` or four-agent release tests prove capacity/layout, not
  workgraph execution and reviewed integration.
- `loop_capacity.py` compares the sum of requested profile instances with
  `max_nodes`; two semantic workgroups already request four physical agents.
- Config V3 is not implemented and its earlier sample lists immaculate control
  roles under `workflow.resident`.

Existing behavior to preserve:

- mount topology contains no semantic edges, gates, or artifact authority;
- script-owned task/round imports and project-root rollback;
- submit-once ask, persisted-terminal resume, and unknown-submission pause;
- bounded reviewer rework and no false pass on malformed results;
- visible window placement, busy retain, bounded release retry, and residue;
- V2 static config and the current single-workgroup route.

## Orchestration Bundle Contract

Add a versioned structured artifact accepted only through a script validator:

```json
{
  "schema": "ccb.loop.orchestration_bundle.v1",
  "task_id": "task-42",
  "task_revision": 7,
  "task_digest": "sha256:...",
  "capacity_digest": "sha256:...",
  "bundle_revision": 1,
  "nodes": [
    {
      "node_id": "node-001",
      "workgroup_id": "wg-001",
      "worker_profile": "coder",
      "reviewer_profile": "code_reviewer",
      "depends_on": [],
      "parallel_group": "wave-1",
      "work_packet_ref": "artifacts/work-packets/node-001.md",
      "allowed_paths": ["src/core/**", "test/test_core.py"],
      "acceptance_refs": ["artifacts/execution_contract.md#core"],
      "verification_refs": ["artifacts/verification_contract.md#core"],
      "integration_order": 10
    }
  ],
  "integration": {
    "verification_refs": ["artifacts/verification_contract.md#integration"],
    "project_root_verification_refs": ["artifacts/verification_contract.md#root"]
  },
  "policy": {
    "max_node_rework_rounds": 1,
    "on_required_node_failure": "partial_or_blocked",
    "on_structural_failure": "replan_required"
  }
}
```

The orchestrator reply uses a candidate envelope containing the structured
bundle plus one work-packet body per node. It does not pre-create authority
files. The importer writes candidate files under a temporary loop directory,
normalizes paths and digests, validates the complete set atomically, then
publishes canonical bundle/work-packet artifacts through the task artifact
service. If any packet or reference fails, none of the set becomes current.
The persisted bundle contains only canonical artifact refs and digests, not an
unbounded copy of provider prose.

Required validation:

- exact schema, task id/revision/digest, capacity digest, and positive bundle
  revision;
- one to configured-maximum nodes, unique stable node/workgroup ids, and one
  worker/reviewer profile per node;
- all dependency references exist, no self edge, no cycle, deterministic
  topological order, and no duplicate integration order;
- all referenced task/contract/work-packet artifacts exist and their digests
  are captured at import;
- profiles exist in effective config and their requested counts fit both
  per-profile and project dynamic limits;
- allowed paths are project-relative, normalized, non-empty, outside `.git`
  and `.ccb`, and do not escape the project;
- parallel nodes have disjoint allowed paths; overlap is valid only when the
  nodes are ordered by dependency;
- control/provider replies cannot supply concrete agent names, tmux panes,
  worktree paths, commands that mutate CCB authority, or task status;
- unknown fields fail in V1 rather than being ignored.

The validated artifact stores source reply digest, normalized bundle digest,
actor/job id, import timestamp, task revision, and capacity snapshot. A
conflicting second bundle for the same revision is rejected. A structural
replan increments bundle revision and starts a new activation.

### One-Node Fast Path

When deterministic checks prove a low-risk single-unit task, scripts construct
the same bundle shape with `node-001`. No separate scalar engine remains. The
synthetic bundle records its provenance and the rule that selected it.

## Durable Round State

Replace scalar stage state with a versioned node map. Suggested shape:

```json
{
  "schema": "ccb.loop.workgroup_round_state.v1",
  "loop_id": "loop-42",
  "task_id": "task-42",
  "bundle_revision": 1,
  "bundle_digest": "sha256:...",
  "base_commit": "...",
  "ready_frontier": ["node-001", "node-002"],
  "nodes": {
    "node-001": {
      "status": "worker_pending",
      "attempt": 1,
      "worker_agent": "loop-loop-42-node-001-coder",
      "reviewer_agent": "loop-loop-42-node-001-code-reviewer",
      "workspace_group": "loop-42-node-001",
      "worktree_path": "...",
      "branch": "ccb/loop-42/node-001",
      "base_commit": "...",
      "worker_job": {},
      "reviewer_job": {},
      "rework": [],
      "review_input_tree_digest": null,
      "reviewed_commit": null,
      "integration_status": "not_ready"
    }
  },
  "integration": {
    "worktree_path": "...",
    "branch": "ccb/loop-42/integration",
    "head": null,
    "merged_nodes": [],
    "verification": null,
    "promotion": null,
    "rollback": null
  },
  "round_reviewer": {},
  "round_result": null
}
```

Node status enum:

```text
created
worker_submission_unknown
worker_pending
worker_failed
worker_complete
reviewer_pending
reviewer_rework
review_failed
review_passed
integration_ready
integrated
blocked
released
```

Round/controller status enum:

```text
bundle_pending
topology_pending
executing
integration_pending
project_verification_pending
round_review_pending
pass
partial
replan_required
blocked
```

Every transition records previous state, next state, event id, node id when
applicable, job id, digest, and timestamp in an append-only event stream.

## Exact-Once Event Loop

One `runner --once` activation performs bounded deterministic work:

1. Lock task/loop and load bundle/state.
2. Reconcile persisted provider-job terminal states into node records.
3. Validate capacity/topology/config digests have not drifted.
4. Compute the ready frontier.
5. For every ready node without an intent/job, durably write an intent keyed by
   `(bundle_revision, node_id, purpose, attempt)`, submit once, and durably bind
   the returned job id.
6. Keep a root Worker job pending while its Reviewer child or Worker
   continuation is active; do not submit Reviewer or rework jobs from the
   controller.
7. Validate the persisted chain contains only the assigned Reviewer, stays
   within the configured review count, and ends in `status: pass`.
8. Capture and commit the final node tree only after the root Worker chain is
   terminal and its final scope/tree checks pass.
9. Integrate newly accepted nodes in deterministic order; unlock dependents
   whose predecessors are now integrated.
10. If jobs remain, persist `pending` and return. Do not poll or infer failure
    from elapsed task time.
11. When all required nodes are integrated, run integration/promotion/root
    verification and round review.

Crash windows that need explicit recovery tests:

- before intent write;
- after intent write but before submit;
- after submit but before job-id append;
- after terminal provider state but before callback consumption;
- after reviewer pass but before node commit;
- after one merge but before integration-state write;
- after root promotion but before verification/result import;
- after result import but before release.

Unknown submit state pauses and exposes an operator diagnostic. It is never
automatically retried. Duplicate/stale callbacks are idempotent and cannot move
a newer attempt.

## Node Workspace And Review Protocol

### Preflight

- Require Git for multi-workgroup execution.
- Record project root, repository identity, HEAD/base commit, status, config
  digest, bundle digest, and allowed paths.
- First release requires no uncommitted project changes. This avoids silently
  excluding user edits from node worktrees or overwriting them at promotion.
- Reject existing controller branch/worktree names unless they match resumable
  state for the same project/task/loop/bundle.

### Worker

- Create node worktree/branch from its dependency base.
- Bind worker and reviewer to the same node workspace group.
- Worker packet includes task/contract refs, allowed paths, acceptance,
  verification, dependency evidence, role constraints, the assigned Reviewer,
  and the bounded review protocol.
- After implementation and focused verification, Worker directly submits
  `ask --chain` to only that Reviewer and stops for continuation.
- On `rework_required`, Worker repairs the same worktree and chains to the same
  Reviewer again within the configured bound. On `pass`, it performs no more
  file/tool mutation and returns the final node result immediately.
- Plain ask, silence, another target, task/topology authority commands,
  commits, integration, promotion, and release remain prohibited.

### Reviewer

- Reviewer receives the node/worktree identity, Worker evidence, acceptance
  refs, verification refs, and current changed-file evidence directly from
  the Worker chain request.
- Reviewer is reply-only and must not edit files or run CCB authority commands.
- The Worker is quiescent while the Reviewer child runs. Rework returns by CCB
  continuation to the same Worker/worktree. Structural graph/scope changes do
  not enter node rework; they produce `blocked` or `non_converged` evidence.
- Controller validates the persisted child job/verdict and captures the final
  tree after the Worker root chain completes.

### Reviewed Commit

After the Worker-owned chain ends in Reviewer pass, the controller creates a
node commit with generated CCB identity
and trailers for project/task/loop/bundle/node/reviewer job/digest. Providers
do not create authority commits. The exact reviewed tree is the commit tree.

## Integration And Project-Root Authority

- Create one integration worktree from the recorded task base.
- Merge reviewed commits by topological layer, then `integration_order`, then
  `node_id`. The order is evidence.
- A dependency node starts from the current accepted integration head, not the
  original base.
- Run bundle-declared integration verification after each dependency wave when
  required and always after the final merge.
- A merge conflict or unexpected path overlap is structural failure. Preserve
  evidence and return `replan_required`; do not ask a provider to improvise a
  conflict resolution inside the controller.
- Snapshot project-root declared paths and current HEAD/status immediately
  before promotion. Apply only the integrated delta and verify resulting tree
  digest.
- Run project-root verification from the real project root.
- Give `ccb_round_reviewer` compact per-node review records, integration commit
  and tests, promotion digest, root tests, and authority checks.
- On pass, retain the accepted project-root delta and import round/task result.
- On every non-pass, malformed result, ask failure after promotion, or root
  verification failure, restore the snapshot and verify rollback digest before
  task result import.

Node worktrees and integration worktree are evidence surfaces until B7 capture.
Agent release happens first; worktree deletion happens only after terminal
evidence is durable and no process is using the path.

## Failure And Result Semantics

| Condition | Node/round behavior | Task result |
| :--- | :--- | :--- |
| All required nodes review pass; integration/root/round checks pass | Commit integrated delta | `done/pass` |
| One node requests bounded rework then passes | Continue same node attempt lineage | eligible for `done/pass` |
| One independent node fails after other reviewed nodes exist | Freeze dependents, preserve accepted evidence, no root promotion | `partial` |
| First/root required node fails and nothing usable is accepted | Freeze dependents | `blocked` |
| Bundle/scope/dependency/merge assumptions are invalid | Stop current bundle | `replan_required` |
| Integration or project-root tests fail | Roll back promotion or retain only isolated evidence | `partial` or `replan_required`, never pass |
| Round reviewer rejects accepted integration | Roll back project root | `partial` or `replan_required` |
| Ask submit state is unknown | Pause, retain evidence/agents as needed | no terminal result |
| Release finds busy agent | Retain only that owned agent with blocker evidence | terminal semantics unchanged; cleanup not falsely complete |

The mapper must be program-owned and based on structured node/integration
state, not provider wording.

## Topology, Capacity, And UI

Concrete names are generated by the controller:

```text
loop-<loop-id>-node-001-coder
loop-<loop-id>-node-001-code-reviewer
```

Placement:

- Window 1 `ccb-user`: resident frontdesk plus active dynamic task detailer.
- Window 2 `ccb-plan`: resident planner plus active dynamic orchestrator and
  round reviewer.
- Window 3+ `ccb-exec`, `ccb-exec-2`, ...: adjacent worker/reviewer pairs,
  maximum six panes per window.
- Two workgroups use four execution panes; three use six; four use six plus two
  in the overflow window.

Capacity must distinguish:

- semantic `max_workgroups`;
- `max_parallel_workgroups` or workers;
- physical `max_active_dynamic_agents`;
- per-profile `max_instances`;
- one-instance dynamic control profiles;
- window pane capacity.

The controller validates peak topology before asks. A capacity conflict does
not silently reduce workgroups, change providers, or serialize independent
nodes. It returns `capacity_conflict` for structural replan.

Release is node/loop ownership scoped. A node may release only after its job,
review, and integration/evidence gates permit it. Final pass requires zero
active/retained dynamic roles; a bounded busy-retain result remains visible and
prevents cleanup from being reported as complete.

## Source Modification Map

Expected ownership surfaces; exact file splits may follow existing local
patterns:

| Surface | Change |
| :--- | :--- |
| `plan_tasks.py` and task artifact models | Add `orchestration_bundle` import/traceability and bundle revision binding. |
| `role_output_import.py` | Parse orchestrator output into a candidate bundle and invoke script validator; never import status from reply text. |
| New bundle service/module | Schema, DAG, scope, capacity, artifact-ref, and digest validation. |
| `loop_runner.py` | Activate bundle path, select one-node template, resume node scheduler, and remove normal post-worker orchestrator aggregation. |
| `loop_ask_first.py` | Extract generalized node event engine; retain compatibility facade and rollback helpers. |
| New workgroup/integration service | Git preflight, worktrees, review tree digest, node commit, integration, promotion, rollback, cleanup. |
| submission intent helpers | Key durable intent/job state by bundle/node/purpose/attempt. |
| `loop_topology.py` | Compile 1..4 pairs and dynamic control roles into mount-only placement; preserve reconcile/release rules. |
| `loop_capacity.py` and config models | Separate workgroup limits from physical agent limits; retain V2 semantics. |
| config loader/models/validator | Add isolated V3 parse/compile/report path. |
| parser/CLI services | Add effective config and migration dry-run reporting where approved. |
| RolePack templates | Update orchestrator bundle output and compact node/round reviewer contracts. |
| B7/reporting | Add bundle, node, Git integration, overlap, UI, release, and config/package evidence. |

Avoid a broad rewrite. First extract a one-node node-map path with current
behavior, then add worktree integration, then fanout.

## Test Matrix

### T0 Baseline And Compatibility

- Freeze current one-workgroup pass, rework, partial, submit-failure,
  unknown-submit, project-root rollback, and release tests.
- Freeze V2 compact, rich `[windows]`, `[agents]`, loop capacity, and layout
  behavior.
- Record full-suite baseline and current real one-workgroup evidence.

### T1 Bundle And Config Unit Tests

- Valid one, two, three, and four-node bundles.
- DAG serial, parallel, and mixed graph.
- Reject duplicate/missing ids, cycles, self edges, missing artifacts, stale
  task/capacity digest, unknown fields, forbidden names/paths, unsupported
  profiles, profile over-capacity, and workgroup over-capacity.
- Reject overlapping parallel scope; accept overlap when dependency orders it.
- Prove deterministic normalized digest and one-node template.
- V3 valid/invalid/provider/model/RolePack/default/capacity/migration tests and
  unchanged V2 corpus.

### T2 State Machine And Exact-Once Tests

- Two or more ready workers are submitted before any completes.
- Callback completion permutations produce the same state.
- Reviewer starts only for its completed worker.
- Dependent starts only after predecessor review and integration.
- Node rework once then pass; repeated same failure stops.
- Every listed crash window resumes without duplicate ask/commit/merge/import.
- Duplicate/stale callbacks are no-op; unknown submit pauses.
- No elapsed business timeout converts pending provider work to failure.

### T3 Topology, Layout, And Release Tests

- 1/2/3/4 workgroups create 2/4/6/8 execution agents.
- Pairs are adjacent and stable; fourth pair overflows to `ccb-exec-2`.
- Dynamic orchestrator/round reviewer/detailer use their specified windows and
  are fresh per activation.
- Capacity conflict is explicit and does not rewrite the bundle.
- Normal release clears all; one busy agent retains only itself; retry clears a
  transient reconcile failure; release cannot affect another loop/node.
- Sidebar/window identity remains stable across add/reflow/remove.

### T4 Git Worktree And Integration Tests

- Two disjoint parallel nodes merge and test.
- Three-node mixed DAG uses the accepted predecessor integration head.
- Four-node deterministic merge order is stable.
- Scope violation, dirty base, tree drift after review, missing reviewer pass,
  merge conflict, integration test failure, and root test failure all reject.
- Root promotion preserves exact integrated tree and rollback restores exact
  prior digest.
- Unrelated files and CCB authority paths are never committed or overwritten.
- Worktree cleanup waits for evidence and active-process gates.

### T5 Result And Authority Tests

- Full pass, bounded rework pass, independent partial, root blocker,
  structural replan, integration failure, malformed round review, and release
  residue classifications.
- No provider reply or topology file can mark node/task pass.
- No accepted sibling evidence is lost on partial, but no partial delta reaches
  project root as completed work.
- Project-root promotion is rolled back on every non-pass after promotion.

### T6 Fake-Provider Full Flow

- Natural frontdesk request through planner and orchestrator bundle.
- One-node compatibility plus 2/3/4-workgroup tasks.
- Event overlap evidence for parallel workers.
- Restart recovery and injected provider/reviewer/release failures.
- Source-wrapper runs only from `/home/bfly/yunwei/test_ccb2` with current
  `ccb_test` and an isolated fake-provider environment.

### T7 Visible Real-Provider Flow

- Fresh opened Git projects under `/home/bfly/yunwei/test_ccb2`.
- Current source `ccb_test`, inherited system provider environment, lab-local
  Role store, and visible UI/sidebar/panes.
- Frontdesk receives ordinary user requests; no explicit routing/group-count
  instructions.
- An atomic task must naturally produce one group; separate tasks with two,
  three, and four independently reviewable surfaces must naturally produce
  2/3/4 groups. Test setup never injects or overrides the count.
- Codex workers/reviewers and configured Claude round review are used where
  available; raw candidate selection evidence must explain complexity,
  cutability, execution shape, and the observed count.
- Raw timestamps prove real overlap; Git history proves review-before-merge;
  project tests and outputs are directly inspectable.
- One in-flight ccbd restart, one node/provider failure, one reviewer rework,
  one busy release, and three sequential tasks prove freshness/repeatability.

### T8 Config V3 Opened-Project Flow

- Minimal V3 project opens without `[windows]`/`[agents]` and generates only
  resident frontdesk/planner initially.
- Dynamic roles mount in correct windows and use configured providers/models.
- Missing required role/profile/RolePack/provider/model/capacity fails at
  `ccb config validate`, before provider startup.
- V2 static project opens unchanged alongside V3 test evidence.
- Migration dry-run is deterministic and never rewrites ambiguous V2 config.

### T9 Release Candidate

- Full non-Gemini source suite, compile, lint/static checks used by the repo,
  and package-content audit.
- `npm pack --dry-run`, packed tarball inspection, external-prefix install,
  `ccb --version`, diagnose, V2 validate/open, V3 validate/open, role loading,
  and visible installed-candidate task.
- Update from current npm stable and rollback smoke.
- OpenCode/Grok provider adapter/config probes run when authenticated and are
  reported separately; no provider claim is made without real evidence.
- Clean commit, synchronized version files, unused npm version, tag, release
  notes, registry verification, and post-publish fresh install.

## Required Evidence Row

Each real/final B7 run must include:

- source commit, package/version when applicable, project root, config version
  and digest, Role store, provider-home policy;
- task id/revision/digest, bundle revision/digest, capacity digest;
- workgroup count, maximum advertised count, node ids, dependencies,
  parallel groups, scope claims, and concrete bindings;
- each worker/reviewer job id/status/start/end, attempt, callback source,
  workspace/branch/base/tree digest, review result, reviewed commit;
- overlap intervals for parallel claims;
- integration worktree, merge order, head, tests, conflict/scope status;
- root pre/post/rollback digest, promotion result, project-root tests;
- round reviewer job/result/source and script-owned final task transition;
- topology desired/observed paths, pane/window map, release/retain/drain counts,
  blockers, runtime residue, and final resident/dynamic agent state;
- authority checks proving no provider-side CCB mutation, no topology dispatch
  DSL, and no result normalization that contradicts raw state.

Missing or contradictory required evidence is `test_design_failure` or
`system_failure`; it is never normalized to pass.

## Stop Conditions

Stop the lane and repair source before broader testing when any of these occur:

- duplicate ask, duplicate commit, duplicate merge, or duplicate authority
  import after restart;
- provider reply changes task/runtime authority directly;
- parallel workers write the same shared project root;
- reviewer pass is accepted for a different tree digest;
- unreviewed node enters integration;
- root remains changed after non-pass rollback;
- controller silently changes graph, profile, provider, parallelism, or scope;
- busy/residue agents are reported as released;
- V3 starts providers despite invalid required roles/config;
- V2 behavior changes without an explicit compatibility decision;
- B7 disagrees with raw task/Git/provider/topology/UI evidence.

Do not weaken a test, classify a failure as acceptable, reduce the advertised
workgroup maximum, or add hidden serialization merely to close a gate. Repair
the owning source boundary and rerun from a fresh project root.
