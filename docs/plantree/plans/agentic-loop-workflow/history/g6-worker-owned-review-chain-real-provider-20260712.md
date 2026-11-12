# G6 Worker-Owned Review Chain Real-Provider Checkpoint

Date: 2026-07-12
Status: Accepted for the two-workgroup Codex baseline; G6 matrix remains open
Branch: `workflow/agentic-loop-topology`

## Scope

This checkpoint validates Decision 027 in fresh, visible Config V3 projects:
the controller submits one root Worker per node, each Worker owns its assigned
Reviewer chain, controller code validates durable lineage and tree identity,
and only script-owned Git, task, topology, release, and cleanup authority can
advance the round.

It does not close all of G6. Three- and four-workgroup real-provider rows,
restart recovery, real rework, busy-retain, and packaged-candidate behavior
remain separate gates.

## Strict Failures And Repairs

The campaign deliberately preserved non-success evidence instead of relaxing
the authority boundary:

- A configured Claude Reviewer profile, whose live pane identified itself as
  `DeepSeek-V4-pro`, returned prose before or instead of the required first
  `status:` line. The controller rejected it as
  `review_chain_final_malformed`; no integration occurred. The Role request
  was tightened, but the strict parser was not weakened. That provider/profile
  is not accepted for the parser-stable Reviewer role by this checkpoint.
- The auto runner initially treated the delegated Worker's intermediate
  provider turn as terminal while its chain child was active. Recovery now
  reads durable callback and JobStore state and waits for the effective
  continuation result without an elapsed-time business timeout.
- Whole-round review initially received early node-review snapshots and was
  asked to prove cleanup before its own immaculate process could be released.
  It now receives integration-owned review records plus an explicit
  pre-round cleanup envelope; its own activation may be the sole dynamic
  process, and final zero residue remains a post-reply controller gate.
- A Planner put prose (`Review ...`) in `Verification:`. The controller tried
  to execute it as argv. Planner instructions now require executable argv only,
  and parser validation rejects entries whose executable cannot be resolved.
- A job start exception could previously leave a non-terminal dispatch record.
  Dispatcher start failures now terminalize durably for recovery.
- The new persisted watch path initially crashed on older completion snapshots
  without `profile_family`. It now conservatively ignores the incompatible
  snapshot model and reconstructs delegated completion from durable
  Attempt/Job/Reply records; both pending and completed callbacks remain
  distinguishable.
- Static analysis found that cancel-notice injection referenced an unimported
  `cancel_flag_path`; the broad best-effort guard silently removed every
  provider cancel notice. The explicit import and regression now prove the
  real-provider execution-only request receives the project/job flag while
  stored authority retains the original user body. Deterministic test-double
  providers are excluded because they cannot inspect files and require an
  unmodified protocol body.

No repair normalized contradictory evidence to pass, created controller-owned
Reviewer messages, introduced topology communication edges, or added a
provider timeout.

## Accepted Visible Run

Project root:
`/home/bfly/yunwei/test_ccb2/g6-minimal-controller-final-20260712013224`

Provider policy: inherited system environment. Role store: lab-local. All
roles in this accepted baseline used Codex. The project was opened with the
source worktree's explicit `ccb_test` and displayed resident and dynamic panes
through the project-local tmux socket.

Natural Frontdesk intake produced task
`add-inventory-reorder-policy-and-anomaly-20260711173446`. Planner and the
immaculate Orchestrator produced a two-node mixed DAG:

1. `node-001` implemented reorder-policy code, tests, and documentation.
2. `node-002` depended on the integrated first node and implemented anomaly
   reporting, tests, integration coverage, and documentation.

For each node, Worker and Reviewer were mounted together. The controller
submitted only the Worker. Each Worker then ran exactly one
`ask --chain --artifact-reply` to its assigned Reviewer:

| Node | Worker root job | Reviewer child job | Callback edge | Result |
|---|---|---|---|---|
| `node-001` | `job_f2ed8ef562ba` | `job_5e771123856a` | `cb_11d155278b54` | `pass` |
| `node-002` | `job_889b4e0bb44e` | `job_498f37e5d4f6` | `cb_80f9c6b2d34a` | `pass` |

Both Worker continuations returned `done` only after Reviewer pass. Controller
review records bound each child job to the exact reviewed tree digest before
creating commits and integrating in dependency order.

## Round And Lifecycle Evidence

- Integrated root head: `71da31ae47343331d4aa1f01381d20db922215b6`.
- Integrated root tree:
  `git-tree:sha1:92ee2fd126757535bd63ae013fc0819f90f681e6`.
- Project-root verification: `79` unittest tests passed.
- Round Reviewer job: `job_bc8fc7bcd2de`.
- Round result: `pass`.
- Authority envelope reported Worker-owned chains verified, matching review
  tree digests, zero controller-authored node Reviewer jobs, and zero topology
  communication edges.
- Pre-round topology contained only the expected Round Reviewer and no
  unexpected workgroup residue.
- Post-round observed topology contained zero dynamic agents, retained count
  `0`, release-incomplete count `0`, and released the Round Reviewer.
- Integration and both node worktrees and branches were removed by the
  controller cleanup state machine.
- Only resident Frontdesk and Planner panes remained before project shutdown.

The supervisor then ran project-root unittest discovery again: `79` passed.
The project was immediately closed with project-level `ccb_test kill -f`:
`kill_status: ok`, `state: unmounted`. Process, tmux socket, and runtime socket
scans for the project root were empty.

Post-run source verification:

- Worker-owned scheduler/RolePack/smoke/ask/dispatcher bundle: `274 passed`.
- Capacity/task/topology/RolePack adjacent bundle: `294 passed`.
- Dispatcher/callback bundle: `112 passed`.
- Ask service: `44 passed`.
- Full non-provider-blackbox repository gate: `4306 passed, 2 skipped,
  21 deselected in 707.09s`.
- Changed-source `py_compile`, `pyflakes`, tracked/untracked whitespace checks,
  and `git diff --check`: passed.
- The final pytest root had zero process and socket residue. A separate stale
  2026-07-10 project owned by this workflow worktree was also closed with an
  exact project-level kill; the final worktree-owned runtime scan was empty.

## Remaining G6 Gates

- Fresh visible three- and four-workgroup tasks, including genuine overlap.
- A separately observed real Reviewer rework cycle.
- ccbd restart while a Worker-owned chain is in flight.
- Busy-retain followed by eventual complete release.
- Provider/profile qualification beyond the accepted Codex baseline. The
  rejected Claude/DeepSeek profile cannot be claimed without a fresh strict
  protocol pass.
- Final normalized B7 aggregation across the complete G6 matrix.

## Related

- [../decisions/027-worker-owned-review-chain-and-minimal-controller.md](../decisions/027-worker-owned-review-chain-and-minimal-controller.md)
- [../goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md)
- [../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md)
