# Execution Node And Round Verification

Date: 2026-06-24

## Principle

Loop execution should keep two quality gates separate:

- Node checker proves one bounded work item is correct.
- Round checker proves the whole loop round still satisfies the planned goal
  after all completed and drained node work is combined.

The loop must not silently lower product scope, acceptance criteria, safety
requirements, or verification standards to make execution converge. Degradation
or scope reduction must leave execution, return to planner, and reach
`frontdesk` only when it changes user intent, product scope, or risk tolerance.

## Default Execution Node Shape

V1 should use a flat execution node by default:

```text
execution_node
  checker: derive node verification contract
  worker: implement bounded work item
  checker: review, test, and audit
```

The checker is a peer quality gate, not the worker's manager. Complex
node-internal teams are deferred until orchestrator cannot safely split the
work item without losing local consistency.

## Checker Responsibilities

Checker should:

- Derive node-level verification from the work item, planner acceptance
  criteria, and orchestrator dependency notes.
- Review whether worker preserved the original design intent.
- Design and run focused node-level tests.
- Reuse existing tests when they really cover the changed behavior.
- Audit fallback, default, retry, compatibility, and graceful-degradation paths.
- Detect scope shrinkage, hidden skips, false success, and test expectation
  changes that make the task easier instead of correct.
- Return `pass`, `rework`, `blocked`, or `non_converged`.

Checker must not:

- Take over the main implementation.
- Lower acceptance criteria.
- Convert missing functionality into optional functionality.
- Mark partial work as done.
- Change product scope or user-facing semantics.
- Advance authoritative loop state.

## Anti-Degradation Rule

Fallback is allowed only when it is:

- Explicitly allowed by the plan or by a planner-approved update.
- Visible to the user or operator when it matters.
- Tested.
- Bounded with a clear reason and failure mode.

Otherwise checker should reject the node result. Examples that should fail
review unless explicitly authorized:

- Swallowing errors and returning success.
- Falling back to builtin/default config when user config fails to parse.
- Skipping dependency-backed behavior but reporting ok.
- Replacing a real-path test with a mock and claiming real validation.
- Editing tests to match incorrect behavior.
- Adding sleeps to hide a race instead of fixing synchronization.

## Node Non-Convergence

Worker and checker should have bounded rework. Suggested defaults:

```text
max_node_rework_rounds = 2
max_same_failure_signature = 2
```

When a node does not converge, it should return:

```text
non_convergence_report
  original_task
  acceptance_criteria
  attempted_solutions
  failed_checks
  repeated_failure_signature
  suspected_root_cause
  design_conflict
  implementation_blocker
  worker_position
  checker_position
  evidence_refs
  recommended_replan_options
```

The node must not downgrade itself into success.

## Partial Branch Semantics

One node's non-convergence should not automatically stop the whole loop.

The loop runner should track:

```text
node_status
branch_status
loop_status
```

When a node is non-converged:

```text
node non_converged
  -> freeze the node
  -> freeze dependent downstream nodes
  -> continue unrelated sibling nodes when safe
  -> drain unaffected work
  -> aggregate partial round evidence
```

The whole loop should stop immediately only when the node failure:

- Invalidates a global design assumption.
- Blocks all meaningful downstream work.
- Contaminates shared state or makes sibling results untrustworthy.
- Reveals that acceptance criteria are wrong or incomplete.
- Requires user-level scope or risk confirmation.
- Would make continued execution wasteful or conflicting.

## Round-Level Verification

Node checker proves local correctness. Round checker proves round correctness.

Planner writes a verification contract before execution:

```text
verification_contract
  objective
  acceptance_criteria
  required_behaviors
  forbidden_degradations
  required_test_categories
  risk_areas
  minimum_evidence
  partial_not_done_rules
```

Round checker receives:

```text
verification_contract
node_reports
checker_reports
changed_files
dependency_graph
partial_branches
non_converged_nodes
known_risks
```

Then it writes and executes:

```text
round_verification_plan
  tests_to_run
  why_each_test_is_needed
  reused_node_tests
  additional_integration_tests
  regression_tests
  real_path_smokes
  skipped_tests_with_reason
  expected_result
```

Round checker may decide how to prove the current round result. It may not
change what must be proven.

## Round Results

Round checker should return one of:

| Result | Meaning | Next Owner |
| :--- | :--- | :--- |
| `pass` | All required behavior is proven and no hidden degradation was found | planner / `ccb plan` |
| `rework_node` | A specific node can fix the issue within the current plan | `orchestrator` |
| `partial` | Independent work is complete, but one or more branches need replanning | planner |
| `replan_required` | The plan, task split, acceptance criteria, or risk model needs revision | planner |
| `global_blocker` | Execution cannot continue without external input or environment change | `frontdesk` only if user decision is needed |

`partial` must never mean degraded completion. It means completed sibling work
can be preserved while blocked branches return to planner.

## Rework Escalation Rules

`rework_node` is only valid for bounded fixes inside the current plan. It
should remain inside the execution round only when all of these are true:

- The same work item can be fixed without changing task requirements.
- The current node split and dependency graph are still valid.
- Acceptance criteria, verification contract, and risk model do not need to
  change.
- The issue is local to one node or one dependent branch.
- Rework limits and same-failure-signature limits have not been reached.
- Continued execution will not contaminate sibling results or create false
  confidence.

Escalate instead of retrying when:

- The node split is wrong or a different decomposition is needed.
- The fix requires changing acceptance criteria, scope, risk tolerance, or
  verification standards.
- The same failure signature repeats beyond the configured limit.
- The failed branch blocks all meaningful downstream work.
- The provider/runtime problem has exceeded recovery limits.
- A user or environment decision is required.

Escalation target:

| Condition | Result |
| :--- | :--- |
| Completed sibling work can be preserved, failed branch needs replanning | `partial` |
| The plan, split, verification contract, or risk model is invalid | `replan_required` |
| External/user/environment action is required | `global_blocker` |

Orchestrator should aggregate these signals for round checker. It must not
convert repeated `rework_node` attempts into success or keep issuing rework
after the bounded fix criteria are no longer true.

## Handoff Package To Planner

For partial or non-converged rounds, orchestrator and round checker should
produce:

```text
partial_loop_report
  completed_nodes
  non_converged_nodes
  blocked_downstream_nodes
  skipped_nodes
  dependency_graph
  failed_assumptions
  round_verification_result
  evidence_refs
  recommended_replan_options
```

Planner decides whether to keep completed work, re-split failed branches,
change the plan, or ask clarification broker to prepare user-facing questions.

Planner should make that decision by rehydrating from task and round evidence,
not from retained conversation memory. The minimum rehydration package is the
original task packet, the orchestrator summary, node/checker reports, the round
checker report, and evidence refs. See
[round-checker-and-planner-rehydration.md](round-checker-and-planner-rehydration.md).
