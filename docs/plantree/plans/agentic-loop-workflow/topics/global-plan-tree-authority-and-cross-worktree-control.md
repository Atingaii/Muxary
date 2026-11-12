# Global Plan Tree Authority And Cross-Worktree Control

Date: 2026-07-15
Status: Design accepted after review; implementation gated by Decision 024
Authority: [Decision 031](../decisions/031-global-plan-tree-authority-across-worktrees.md)
Read when: implementing Plan Tree storage, control election, planner writes,
worktree coordination, lane admission, global retrieval, integration, or
recovery

## Purpose And Authority

This is the sole detailed protocol specification for repository-global Plan
Tree consistency. Decision 031 owns stable principles. The parallel-roadmap
topic owns Roadmap Graph and lane scheduling semantics. This file owns locator,
lease/fencing, authority refs, revisions, task-store migration, transactions,
freshness, integration recovery, and implementation order.

The first-principles split is:

```text
Markdown stores human meaning.
Versioned manifests store machine planning authority.
Indexes provide rebuildable retrieval.
Runtime state records fast-changing execution facts.
Git commits and refs provide durable audit and publication.
```

## Required Invariants

1. All same-repository linked worktrees resolve one local control domain.
2. Exactly one fenced holder may publish one authority target ref.
3. The target ref is checked out in at most one registered control workspace.
4. Lane worktrees consume pinned snapshots and submit proposals; their local
   Plan Tree files are not writable replicas.
5. Provider work never holds a control transaction lock or holder lease open
   without renewal by deterministic code.
6. Every write verifies generation, fencing token, authority ref, and relevant
   revision/digest closure.
7. Runtime observations enter Markdown only as stable semantic transitions.
8. Code and an explicit Plan Tree `promotion_pending` record share one hidden
   candidate; final Plan Tree completion and event publication follow target
   promotion through recoverable, idempotent stages.
9. Every global view exposes its read fence and freshness/completeness state.
10. Unsupported lock/filesystem semantics and cross-machine concurrent writers
    fail closed.

## Identity Model

Two identities are required because neither a filesystem path nor a committed
id is sufficient alone:

- `portfolio_id`: immutable UUID-like id in committed
  `docs/plantree/plantree.toml`; shared by clones and used in durable artifacts;
- `local_repository_id`: random id created once by explicit local control
  initialization and stored under the Git common directory; shared only by
  linked worktrees of that local repository.

The same-host control-domain key is the pair
`(portfolio_id, local_repository_id)`. Moving a repository preserves the local
id because the locator moves with its Git common directory. A separate clone
receives a distinct local id and cannot accidentally join the first clone's
local lease domain.

The committed manifest begins minimally:

```toml
schema_version = 1
portfolio_id = "ptf_<stable-id>"
authority_schema = "ccb.plantree.authority.v1"
```

Changing `portfolio_id` is a portfolio migration requiring explicit export,
import, diagnostics, and rollback. It is never an ordinary plan edit.

## Locator And Runtime Root

Linked worktrees discover one locator at:

```text
<git-common-dir>/ccb/plantree/control-locator.v1.json
```

It contains only bootstrap identity and location data:

```json
{
  "schema": "ccb.plantree.control_locator.v1",
  "portfolio_id": "ptf_...",
  "local_repository_id": "ptr_...",
  "locator_revision": 4,
  "control_state_root": "/local/fs/...",
  "control_workspace": "/repo-or-worktree/...",
  "target_ref": "refs/heads/main",
  "authority_generation": 9,
  "updated_at": "..."
}
```

The runtime root may follow CCB runtime-state relocation policy, but the shared
locator remains the only pointer to it. All linked worktrees must resolve and
validate the same locator. Environment variables may select a test root but
cannot silently override production locator authority.

`ccb plan control init` is the only first-creation path. It requires an existing
committed portfolio manifest, a clean target ref/control workspace, a supported
filesystem capability probe, and atomic create-without-replace plus file and
parent-directory durability. If a locator is missing, unreadable, duplicated,
or points to missing state, ordinary commands return `control_unavailable` and
direct the operator to `doctor`; they do not bootstrap a second domain.

## Holder Lease, Fencing, And Handoff

The control root stores a lease record with:

```text
authority_generation, fencing_token, lease_revision
holder_id, holder_pid, holder_process_start, host_boot_id
control_workspace, target_ref, authority_commit
issued_at, renewed_at, expires_at, state
```

`authority_generation` increments when authority moves to a replacement
control workspace/service generation. `fencing_token` increments on every
holder acquisition or takeover within that generation. Both are monotonic and
included in proposals, transaction records, commit metadata, projections, and
events.

Control lifecycle states are:

```text
uninitialized
  -> active
  -> handoff_pending -> active(new generation)
  -> recovery_required -> takeover_pending -> active(new generation)
  -> disabled
```

Rules:

- normal renewal is deterministic and never delegated to an Agent;
- lease expiry marks `recovery_required`; it does not elect a new holder;
- planned handoff drains proposals, proves no prepared transaction remains,
  verifies the new clean workspace/target ref, then compare-and-swaps locator
  revision, generation, fence, and holder;
- takeover requires an explicit command with expected locator revision and
  generation plus a fresh doctor report proving the old holder/process lease is
  invalid and classifying any incomplete transaction;
- the new holder increments generation/fence before recovery; every old-holder
  write, target-ref CAS, state update, or event is rejected;
- workspace move, locator repair, and target-ref change are never implicit
  side effects of ordinary Plan Tree commands.

The lease does not replace the short transaction lock. The lock serializes
live writers; generation/fencing rejects a paused or resumed stale writer.

## Supported Lock And Filesystem Contract

The first implementation supports only local filesystems where CCB proves:

- exclusive inter-process locking;
- atomic create-without-replace and atomic same-filesystem rename;
- durable file flush and parent-directory flush;
- stable process-start/boot identity for stale-holder diagnosis;
- Git ref lock/CAS behavior required by the selected target ref.

Linux/macOS local POSIX filesystems may use proven `fcntl`/`flock` semantics.
WSL must place the mutable control root on a Linux filesystem when drvfs cannot
pass the probe. NFS, SMB, drvfs, or native Windows are unsupported until their
specific lock and durability primitive passes the same crash/concurrency suite.
Native Windows requires an implemented `LockFileEx`/named-mutex equivalent; it
must not use a no-op fallback.

The current `lib/storage/locks.py` behavior that executes unlocked when
`fcntl` is unavailable is incompatible with this protocol and must be repaired
before control-domain implementation. Capability failure rejects startup with
diagnostics; it never degrades to best-effort locking.

## Durable And Runtime Layout

Target committed shape:

```text
docs/plantree/
  plantree.toml
  README.md
  baseline/
  indexes/                         # generated projections
  plans/<plan-id>/
    plan.toml                      # lifecycle/revisions/dependencies
    README.md
    roadmap.md
    roadmap.graph.json            # script-owned Roadmap Graph
    implementation-status.md      # short active handoff only
    decisions/
    topics/
    open-questions.md
    tasks/<task-id>/
      task.json                    # canonical task record
      brief.md
      detail.md
      acceptance.md
```

Shared control-runtime shape:

```text
control.json
lease.json
authority-cache.json
transactions/<proposal-or-integration-id>.json
journal.ndjson
proposals/{pending,accepted,rejected}/
locks/control.lock
lanes/<lane-id>/{lane,snapshot,claims}.json
integration/<target-ref-key>/{queue,active}.json
```

Canonical manifests and the published target-ref commit are durable semantic
truth. Indexes, authority cache, lane registry, and journal are rebuildable
projection/recovery surfaces. The locator and current fenced lease are writer
authority, not semantic project history.

## Ownership Matrix

| Surface | Semantic owner | Physical writer |
| :--- | :--- | :--- |
| Portfolio registry/cross-plan graph | User or global Planner | Plan Tree controller |
| Plan/Roadmap/decision state | Global or fenced scoped Planner | Plan Tree controller |
| Canonical task transition | Planner/Detailer/controller contract | Plan task transaction |
| `implementation-status.md` | Planner owns semantic handoff; controller may project accepted factual phase/evidence | Plan Tree controller |
| Product/runtime contract outside Plan Tree | Existing contract owner | Existing contract path/process |
| Lane execution observation | Lane controllers | Shared lane registry |
| Worker/reviewer code and evidence | Assigned lane | Lane branch/artifacts |
| Integration candidate and verification | Integration controller | Hidden integration ref |
| Global target promotion | Accepted integration policy | Fenced Plan Tree holder |
| Human status/index projection | Accepted authority/runtime facts | Plan Tree controller |

Plan Tree can reference an external contract but cannot acquire ownership by
listing it. The root authority order in `docs/plantree/README.md` remains valid.

## Typed Authority Reference

Every lane snapshot contains an explicit recursive authority closure. One ref
uses `ccb.plantree.authority_ref.v1` and carries:

```text
kind                    # portfolio, plan, roadmap_node, task, dependency,
                        # decision, scope_claim, acceptance, contract,
                        # base_ref, target_ref, integration_policy
authority_domain        # plantree | repository_contract | git
portfolio_id
repository_commit       # full immutable commit id
path                    # normalized repository-relative POSIX path
selector_type           # whole_file | json_pointer | stable_id | git_ref
selector                # type-specific stable selector
canonicalization        # bytes_v1 | canonical_json_v1 | typed_manifest_v1
content_digest          # sha256 over selected canonical content
impact                  # informational | task_fence | plan_fence | global_fence
required
```

V1 canonicalization rules:

- paths reject absolute paths, `..`, symlink escape, and platform separators;
- Git commits and resolved base/target refs use full object ids;
- JSON uses one deterministic canonical JSON encoder and JSON Pointer;
- typed manifests hash their parsed schema-defined representation;
- Markdown uses whole-file normalized UTF-8/LF bytes in V1; headings are
  retrieval hints, not digest selectors, until stable semantic ids exist;
- recursive edges come only from typed manifest fields, never implicit
  Markdown-link crawling;
- expansion rejects cycles and missing required refs;
- closure entries sort by domain, kind, commit, path, selector type, selector;
- `authority_digest` is SHA-256 over the canonical JSON array of all entries.

The minimum lane closure includes its Roadmap node, task, required
dependencies, scope claims, acceptance contract, referenced decisions,
external API/schema/migration/release contracts, integration policy, base
commit, and expected target ref. Controller-generated implicit additions are
returned in the admitted snapshot so the lane can audit the complete closure.

The controller also computes `fence_set_digest` over every active
`plan_fence` and `global_fence` applicable to the lane, including policy fences
that are not reachable from task-local refs. It uses the same canonical sorting
and digest rules as the authority closure. The fence set is an independent,
mandatory snapshot field so an unchanged task closure cannot hide a changed
global policy.

## Revision Relationship

Revisions are monotonic counters within one authority generation:

- a task semantic/state change increments `task_revision` and its containing
  `plan_revision`;
- a plan graph/decision/question/manifest change increments `plan_revision`;
- a root registry, cross-plan dependency, shared global fence, or portfolio
  schema change increments `portfolio_revision`;
- a control handoff/takeover increments `authority_generation` independently.

Every proposal carries observed portfolio/plan/task revisions, authority
closure/digest, and `fence_set_digest`. Required matching is:

- generation, fencing token, expected target commit, target ref, affected task
  revision, and every referenced content digest must match;
- a newer plan or portfolio revision may be deterministically rebased only when
  both closure and fence-set recomputation are byte-identical; the transaction
  records `rebased_from` and the newer observations;
- any changed applicable `plan_fence` or `global_fence` rejects rebase with
  `plan_fence_changed` or `global_fence_changed`, even when the task-local
  authority closure is byte-identical;
- otherwise the proposal returns `stale_plan_snapshot` or
  `plan_revision_conflict` and requires explicit planner action.

This permits unrelated task updates without silently accepting a changed
contract. A task result never bypasses its containing plan: plan revision drift
must pass the identical-closure rebase rule before import.

Decision 029's existing `expected PlanTree revision` remains a legacy digest of
its selected projection files. During migration it maps to
`legacy_projection_digest` inside one plan-level proposal; it is not equivalent
to `portfolio_revision`, `plan_revision`, or the authority closure. New
multi-lane writes require the full model.

## Proposal Envelope

Minimum envelope:

```json
{
  "schema": "ccb.plantree.change.v1",
  "proposal_id": "ptc_...",
  "portfolio_id": "ptf_...",
  "local_repository_id": "ptr_...",
  "actor": {
    "agent": "...",
    "lane_id": "...",
    "authority_generation": 9,
    "fencing_token": 31
  },
  "basis": {
    "target_ref": "refs/heads/main",
    "authority_commit": "...",
    "portfolio_revision": 18,
    "plan_revision": 42,
    "task_revision": 9,
    "authority_digest": "sha256:...",
    "fence_set_digest": "sha256:..."
  },
  "authority_refs": [],
  "scope": {"plan_id": "...", "task_id": "...", "paths": []},
  "operations": [],
  "evidence_refs": [],
  "code_refs": []
}
```

Free-form Markdown may accompany a typed semantic operation. A textual patch
alone cannot change lifecycle, graph, dependency, revision, or completion
authority.

## Plan-Only Transaction

The controller performs:

```text
proposal prepared without lock
  -> acquire control lock
  -> verify current holder lease/generation/fence
  -> recover or reject an incomplete prior transaction
  -> verify target ref, revisions, closure, scope, and clean workspace
  -> materialize candidate in transaction-owned state
  -> validate schema, graph, links, indexes, and transitions
  -> create candidate authority commit
  -> compare-and-swap target ref from expected commit
  -> synchronize/verify control workspace
  -> finalize journal/cache and publish idempotent event
```

Journal stages are `prepared`, `commit_created`, `ref_advanced`, `committed`,
and `event_published`. The target ref is semantic publication authority:

- before `ref_advanced`, an unreferenced candidate may be retried or discarded;
- after `ref_advanced`, recovery finalizes journal/cache/event from commit
  metadata and never creates a duplicate authority commit;
- if target CAS fails, the candidate remains hidden and the proposal becomes a
  structured conflict;
- if the control workspace is partially updated, it enters
  `recovery_required`; the target ref remains the source for repair.

No provider call, test campaign, or human review runs while the lock is held.

Proposal directories are a physical lifecycle projection, not authority by
file presence:

- creation writes one immutable envelope under `proposals/pending/` before the
  transaction is admitted;
- successful target-ref publication plus committed journal state moves it once
  to `accepted/` with authority commit and event identity;
- validation, scope, revision/fence conflict, or explicit cancellation moves it
  once to `rejected/` with a structured terminal reason;
- crash recovery decides the directory from target ref and journal, then uses
  atomic same-filesystem rename; it never infers semantic state from the
  directory alone;
- retention may archive accepted/rejected envelopes only after their commit and
  evidence refs are durable. A stale pending envelope is always diagnosed,
  recovered, or rejected, never silently deleted.

## Storage And Projection Migration

Current task records live inside one shared `tasks/index.json`, while the legacy
Planner revision covers only `brief.md`, `roadmap.md`, and `TODO.md` under a
worktree-local lock. Neither model is safe to expand implicitly.

The guarded canonical-task and typed Planner-projection cutover, compatibility
mode, rollback boundary, mixed-version rejection, and crash tests are defined
in
[global-plan-tree-storage-and-projection-migration.md](global-plan-tree-storage-and-projection-migration.md).
That migration must finish before concurrent Plan Tree writes or multi-lane
admission.

## Lane Registry And Snapshot

Shared lane records include:

```text
lane_id, plan_id, roadmap_node_id, task_id
worktree_path, branch, base_commit, head_commit
authority_generation, fencing_token, authority_commit
portfolio_revision, plan_revision, task_revision
authority_refs, authority_digest, fence_set_digest, lane_snapshot_revision
scope_claims, runtime_status, integration_id, integration_status
blocker, dirty_digest, registry_sequence, observed_at
```

Admission writes an immutable snapshot and registry entry before dispatch.
Authority is rechecked before dispatch, accepting review, integration, and
completion publication. Unrelated closure-identical changes continue; relevant
changes enter `stale_plan_snapshot`. Worktree loss does not erase lane identity
or permit reuse without explicit recovery/cancellation.

`dirty_digest` is `null` when the lane worktree equals its recorded HEAD plus
controller-owned generated exclusions. Otherwise it is SHA-256 over a sorted
canonical JSON list of repository-relative path, index/worktree status, and
content digest for every tracked or untracked change outside those exclusions.
It is captured after worker return, before accepting review, and before hidden
integration. An unexpected change produces `workspace_dirty_unexpected`; it is
execution evidence and never participates in `authority_digest`.

When a waiting dependency becomes `published`, the scheduler performs a
`dependency_refresh` transaction: resolve the predecessor output/commit,
recompute closure and fence set against current authority, create a new
immutable snapshot with incremented `lane_snapshot_revision`, and preserve the
old snapshot. This operation, not in-place mutation or a query, is what the
acceptance matrix calls `closure refreshed`. A changed relevant ref enters
`stale_plan_snapshot` instead of admitting the dependent lane.

## Consistent Global Read

`ccb plan global`, `lanes`, `context`, and generated projections return:

```text
authority_commit, authority_generation, target_ref
portfolio_revision, plan_revision(s)
registry_sequence, registry_observed_at
projection_generation, generated_at
read_complete, stale_reasons[]
```

A reader captures authority commit and registry sequence, materializes the
view, then re-reads both fences. If either changed it retries a bounded number
of times. Exhaustion returns `read_complete=false` with both observed ranges;
it never labels the result current. Generated indexes and Markdown snapshots
use the same envelope and cannot combine an old authority commit with an
unlabelled newer runtime registry.

Retrieval remains layered:

| Level | Default content |
| :--- | :--- |
| Portfolio | Active plans, phases, blockers, lanes, joins, freshness envelope |
| Plan resume | Manifest, README, short status, current roadmap slice, blockers |
| Task/lane | Pinned task, closure, claims, dependencies, acceptance, integration |
| Evidence | Selected decisions, contracts, topics, and accepted history |

## Integration Saga

One `integration_id` owns the complete state machine:

| Stage | Durable meaning | Public target visibility | Recovery |
| :--- | :--- | :--- | :--- |
| `prepared` | Pinned lane commit, expected target/authority, snapshot, closure | None | Revalidate then continue or reject |
| `integrated_hidden` | Merge candidate exists on `refs/ccb/integration/<id>` | None | Verify or delete only after rejection evidence |
| `verified` | Combined tests accepted for exact hidden commit | None | Recheck authority/target, then build final candidate |
| `authority_recorded` | Hidden candidate includes code plus explicit Plan Tree `promotion_pending` record and bidirectional refs | None | CAS target or mark conflict if basis moved |
| `promoted` | Target ref CAS points to exact candidate | Code and explicit pending state are visible; not globally done | Create one completion commit, then finalize runtime/event |
| `published` | Final Plan Tree completion commit, registry, journal, and event agree with promoted code commit | Complete | Idempotent event/finalization replay only |

The registered control workspace is the only checkout allowed to advance the
target ref. Hidden candidate construction may occur in an integration worktree,
but only the current fenced holder promotes it. A target change before promotion
requires candidate rebuild or explicit conflict; no force update is allowed.

After promotion, the holder creates one target-ref completion commit that
replaces `promotion_pending` with the stable Plan Tree outcome and references
the promoted code commit/integration id. A crash after that ref update but
before the event is recovered from completion-commit metadata.

Dependent roadmap admission requires `published` with matching integration id,
verified candidate digest, promoted code commit, completion commit, and cleanup
status. A crash at `promoted` may expose code plus an explicit pending state, but
cannot admit dependents until recovery reaches `published`. A failed or rejected
saga records the hidden ref disposition and never marks the macro node done.

## Implementation Slices

All slices remain behind Decision 024's single-lane production gate:

1. Add portfolio/local repository identity, explicit locator initialization,
   capability probes, diagnostics, and control lifecycle state machine.
2. Implement supported-platform lock primitives, holder lease/fencing,
   handoff/takeover, and stale-holder rejection.
3. Add canonical plan/task manifests and perform the guarded task-store/index
   and Planner projection migration with rollback and mixed-version rejection.
4. Add typed authority refs, closure/canonicalization, revision relationships,
   external contract refs, and legacy Decision 029 mapping.
5. Add proposal transactions, target-ref CAS, journal recovery, consistent read,
   and generated projection freshness envelopes.
6. Add Roadmap Graph schema/cycle validation, shared lane registry, immutable
   snapshots, scope claims, and staleness transitions.
7. Pass the control, transaction, migration, and authority-change rows in the
   cross-worktree acceptance matrix before enabling ready-frontier concurrency.
8. Add per-lane scheduling/locks, hidden integration candidates, promotion saga,
   combined verification, and dependent-admission fences.
9. Add lane-aware global/UI projections and run the full two-lane fault matrix.
10. Measure planner/control queue contention before considering scoped semantic
    planners; the physical authority commit stream remains serialized.

## Deferred

- Multiple physical Plan Tree target-ref writers.
- Cross-machine strong consistency without a remote lease/CAS service.
- Markdown subsection digests without stable semantic ids.
- Automatic semantic merge of conflicting planner proposals.
- Arbitrary quorum or `any` Roadmap Graph joins.

## Related

- [global-plan-tree-cross-worktree-acceptance-matrix.md](global-plan-tree-cross-worktree-acceptance-matrix.md)
- [global-plan-tree-storage-and-projection-migration.md](global-plan-tree-storage-and-projection-migration.md)
- [parallel-roadmap-lanes-and-planner-authority.md](parallel-roadmap-lanes-and-planner-authority.md)
- [state-and-script-contract.md](state-and-script-contract.md)
- [plan-and-runtime-list-structure.md](plan-and-runtime-list-structure.md)
- [../decisions/023-roadmap-graph-and-workflow-lanes.md](../decisions/023-roadmap-graph-and-workflow-lanes.md)
- [../decisions/024-project-topology-controller-and-single-lane-first.md](../decisions/024-project-topology-controller-and-single-lane-first.md)
- [../decisions/029-planner-feedback-and-task-set-closure.md](../decisions/029-planner-feedback-and-task-set-closure.md)
- [../decisions/031-global-plan-tree-authority-across-worktrees.md](../decisions/031-global-plan-tree-authority-across-worktrees.md)
