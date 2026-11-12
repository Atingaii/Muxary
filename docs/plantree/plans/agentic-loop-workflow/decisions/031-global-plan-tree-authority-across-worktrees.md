# 031 Global Plan Tree Authority Across Worktrees

Date: 2026-07-15
Status: Accepted for planning; implementation gated by Decision 024
Coworker review: [Claude accepted with clarifications; all applied on 2026-07-15](../history/global-plan-tree-claude-coworker-review-20260715.md)
Prior review: [initial architecture findings and redesign disposition](../history/global-plan-tree-control-review-20260715.md)

## Context

Decision 023 makes Plan Tree the durable Roadmap Graph authority and Workflow
Lane the concurrent execution unit. Separate lane worktrees isolate code, but
every Git worktree also contains a checkout of `docs/plantree`. If those copies
are independently writable, parallel work creates divergent roadmaps, lost
task-index updates, stale decisions, and conflicting completion claims.

Git history alone is not live coordination. A lane must know which authority it
accepted, whether a relevant contract changed, and where to submit an update.
Multiple worktree-local CCB backends also need one repository-level planning
authority without merging their independent backend lifecycle ownership.

## Decision

One Plan Tree portfolio has one repository control domain, one active fenced
control holder, one registered control workspace, and one serialized authority
commit stream. All linked worktrees resolve that same domain. A worktree-local
Plan Tree checkout is a snapshot unless it is the registered control workspace.

```text
one committed portfolio identity
  -> one shared control locator
  -> one generation and fenced holder lease
  -> one canonical authority commit stream
  -> many immutable lane snapshots and revision-fenced proposals
```

Lane planners, workers, reviewers, integration worktrees, and independent CCB
backends cannot directly publish global macro state. They submit structured
proposals. Deterministic control code validates and commits accepted proposals.

## Control Identity And Single-Writer Election

The portfolio has a committed, immutable `portfolio_id` and schema identity.
Same-host linked worktrees combine that identity with their Git common
repository to locate one non-committed control locator. The locator records the
control state root, registered workspace, target authority ref, locator
revision, and current authority generation.

Initialization, workspace handoff, orphan recovery, and holder takeover are
explicit compare-and-swap operations. A missing or unreadable locator never
causes automatic initialization. Lease expiry alone never authorizes a second
writer; takeover requires diagnostics, proof that the prior holder is no longer
authoritative, and an incremented generation/fencing token.

Every authority proposal, transaction, commit record, runtime projection, and
event carries the current generation and holder fence. An old holder cannot
publish after handoff even if its process resumes. A short file lock serializes
transactions; holder lease and fencing prevent stale-writer failover races.

Each `.ccb` project anchor continues to own its own `ccbd` backend. Plan Tree
election coordinates repository planning writes only and does not create one
backend across worktrees.

## Authority Boundary

The control workspace is the sole physical writer for:

- the Plan Tree registry, baseline references, and portfolio graph;
- plan manifests, Roadmap Graphs, decisions, open questions, and stable status;
- canonical task records and rebuildable indexes;
- accepted integration and release evidence projections.

This does not make Plan Tree superior to shipped product/runtime contracts
elsewhere under `docs/`. External repository contracts retain their existing
authority. A lane references them through immutable Git commit, path/selector,
and digest records, so a relevant external contract change can invalidate the
lane without granting Plan Tree permission to rewrite that contract.

## State And Revision Principles

Plan Tree separates human meaning, machine planning manifests, immutable lane
snapshots, high-frequency runtime observations, and Git audit history. Runtime
heartbeats, retries, panes, and provider noise do not create Markdown commits.

Monotonic `portfolio_revision`, `plan_revision`, and `task_revision` values are
conflict/search counters, not sufficient relevance tests. Every lane also pins
a canonical typed closure of authority references and its digest. The closure
includes the Roadmap node, task, dependencies, scope claims, acceptance,
external contracts, integration policy, and base/target refs needed by that
lane.

An unrelated authority commit may advance without stopping a lane. A changed
referenced digest, control generation, required global fence, or incompatible
task/plan revision enters `stale_plan_snapshot`. Refresh is explicit; a running
prompt is never silently changed to new authority.

## Proposal And Write Rule

Agents reason and prepare proposals without holding a lock. Control code then
uses one short, fail-closed transaction to verify the active holder fence,
expected authority commit, relevant revisions/digests, writer scope, clean
control workspace, schema, graph, links, indexes, and status transitions.

Revision or fence mismatch returns a structured conflict. It never performs a
best-effort textual merge or last-writer-wins update. Unsupported lock or
filesystem semantics reject control startup rather than running unlocked.

## Code And Plan Integration Saga

Git target-ref promotion, Plan Tree authority commits, runtime journal writes,
and event publication are different persistence operations and are not claimed
to be atomic. Their contract is a recoverable integration saga:

```text
prepared
  -> integrated_hidden
  -> verified
  -> authority_recorded
  -> promoted
  -> published
```

Code first exists on an integration-id-owned hidden staging ref. Verification
and a pending Plan Tree authority record precede compare-and-swap promotion to
the public target ref. Final Plan Tree completion and events follow promotion.

Temporary disagreement is observable after a crash, but it is never interpreted
as global completion. Dependent roadmap nodes remain frozen until one
integration id is `published` with matching verified code, target commit,
authority commit, and bidirectional references. Recovery has one idempotent
forward or reject action for every saga stage; it does not invent success.

## Global View And Freshness

The durable portfolio/plan manifests and shared lane registry form the macro
view. Queries and generated projections state their authority commit, registry
observation sequence/time, projection generation, and completeness. A mixed or
changing read fence is reported as `incomplete` or `stale`, never as current.

High-frequency lane facts stay in shared runtime state. Markdown receives only
stable lifecycle, blocker, integration, decision, and evidence transitions.

## Consistency Boundary

Strong single-writer consistency is required for supported same-host linked
worktrees in one control domain. Separate clones or machines are eventually
consistent through Git unless a remote lease/CAS service is configured.
Cross-machine concurrent writers are outside the first implementation and fail
closed.

## Sequencing Gate

This decision does not authorize multi-lane source work. Decision 024's visible,
repeatable single-lane production closure remains the first gate. After that,
control identity/election, task-store migration, fail-closed locking, proposal
transactions, authority closure, and recovery tests must pass before
ready-frontier concurrency is enabled.

## Consequences

- Parallel code work cannot create independently authoritative Plan Tree copies.
- Split-brain prevention becomes an explicit lease/fencing protocol rather than
  an assumption about paths or process count.
- Relevant external contracts participate in lane validity without moving
  their ownership into Plan Tree.
- Code/Plan completion uses an inspectable saga, not impossible cross-system
  atomicity.
- Runtime state and generated indexes remain rebuildable projections, while
  canonical manifests and authority commits retain durable meaning.

## Non-Goals

- Do not turn Markdown into a high-frequency workflow database.
- Do not use filesystem read-only bits as the authority model.
- Do not reconcile independently writable Plan Trees through ordinary Git
  merges.
- Do not hold a global lock while an Agent reasons or a lane executes.
- Do not enable multiple physical Plan Tree commit writers in the first design.
- Do not claim cross-machine strong consistency without a remote lease service.

## Related

- [023-roadmap-graph-and-workflow-lanes.md](023-roadmap-graph-and-workflow-lanes.md)
- [024-project-topology-controller-and-single-lane-first.md](024-project-topology-controller-and-single-lane-first.md)
- [029-planner-feedback-and-task-set-closure.md](029-planner-feedback-and-task-set-closure.md)
- [../topics/global-plan-tree-authority-and-cross-worktree-control.md](../topics/global-plan-tree-authority-and-cross-worktree-control.md)
- [../topics/global-plan-tree-storage-and-projection-migration.md](../topics/global-plan-tree-storage-and-projection-migration.md)
- [../topics/global-plan-tree-cross-worktree-acceptance-matrix.md](../topics/global-plan-tree-cross-worktree-acceptance-matrix.md)
- [../topics/parallel-roadmap-lanes-and-planner-authority.md](../topics/parallel-roadmap-lanes-and-planner-authority.md)
- [../history/global-plan-tree-control-review-20260715.md](../history/global-plan-tree-control-review-20260715.md)
