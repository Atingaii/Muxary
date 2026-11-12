# 027 Worker-Owned Review Chain And Minimal Controller

Date: 2026-07-11
Status: Accepted for implementation

## Context

The first multi-workgroup scheduler made the controller submit the worker,
wait for it, construct a reviewer request, submit the reviewer, parse rework,
and submit the worker again. That is recoverable, but it duplicates a semantic
collaboration loop that CCB already supports through durable `ask --chain`.
It also makes ordinary node execution depend on repeated controller scheduling
steps and turns program code into a natural-language message broker.

The original workflow principle is smaller:

- program code owns deterministic authority and recovery;
- roles own semantic work and role-to-role collaboration;
- topology mounts agents but does not encode communication edges;
- slow provider work remains pending until a real terminal result exists.

## Decision

Each node mounts one immaculate Worker and one immaculate Reviewer together.
The controller submits exactly one root Worker job for the node. The Worker
owns the bounded semantic review loop:

```text
controller -> Worker
                |
                +-- ask --chain assigned Reviewer
                         |
                         +-- pass -> Worker returns final node result
                         +-- rework_required -> Worker repairs and chains again
                         +-- blocked/non_converged -> Worker returns non-pass
```

The Reviewer target, node contract, allowed paths, verification requirements,
maximum rework count, and response protocol are injected in the root Worker
task and Worker Role memory. The Worker may use only `ask --chain` to the
assigned Reviewer. Plain ask, silence, another target, another role, and CCB
authority commands remain prohibited.

The Reviewer remains read-only and returns a parser-stable first line:
`status: pass`, `status: rework_required`, `status: blocked`, or
`status: non_converged`.

## Compatibility Scope

This decision is the production contract for Config V3 and the generalized
one-to-four-workgroup scheduler. Config V2 remains the frozen static-agent
compatibility surface and keeps its established single-node behavior; it is
not extended with multi-workgroup semantics. New workflow features and release
claims must exercise the V3 path. The legacy V2 relay implementation is not a
model for new controller behavior and must not leak into V3 scheduling.

## Minimal Controller Authority

The controller no longer authors or submits reviewer/rework messages and does
not interpret reviewer prose to plan a repair. It retains only mechanical
authority:

- validate the orchestration bundle and capacity digest;
- create and bind node worktrees and mount the pair;
- submit the root Worker job exactly once;
- keep the root job pending while a chain child or continuation is active;
- validate persisted chain lineage, assigned Reviewer identity, bounded review
  count, terminal child status, final `status: pass`, and the dispatcher-bound
  worktree digest recorded at the final review submission;
- capture the final node tree and verify scope after the chain completes;
- create controller commits, integrate the DAG, verify and promote the root;
- run round review, import task authority, roll back, release, and recover.

Provider replies remain evidence. Callback edges, jobs, final tree identity,
commits, task state, topology, and cleanup remain script-owned authority.

## Quiescence And Tree Binding

`ask --chain` delegates the active Worker turn and stops it until the Reviewer
returns. The Worker therefore cannot edit concurrently with the read-only
Reviewer. On `pass`, Worker Role memory requires an immediate final response
with no further file or tool mutation. On `rework_required`, the continuation
may edit and must ask the same Reviewer again.

After the final continuation, the controller captures the node tree, validates
allowed paths and verification evidence, compares its canonical digest with
the script-owned callback-edge digest, records the final Reviewer child job,
and creates the authority commit. A missing chain, wrong target, non-pass last
verdict, extra review round, tree mismatch, scope drift, or post-review
validation failure is never accepted.

## Runtime Guardrails

- The root Worker request carries an internal allowed-chain-target list with
  exactly its assigned Reviewer.
- Each restricted chain submission is bound by the dispatcher to the parent
  Job's canonical worktree digest; provider text cannot supply or replace it.
- Dispatcher validation rejects Worker chain calls to any other target and
  rejects plain or silent nested asks from that restricted root/continuation.
- The allowed target propagates through chain continuations for bounded
  re-review.
- Callback chains have no elapsed-time business timeout. Health diagnostics
  may report silence, but only child/provider terminal state ends the chain.
- The final visible reply for the root Worker job is unavailable while a child
  or continuation is pending; persisted-terminal recovery must not expose the
  delegated intermediate reply as node completion.

## Consequences

- Normal node execution has one controller submission instead of separate
  Worker, Reviewer, and rework submissions.
- Worker and Reviewer communication is internal CCB collaboration, not an
  orchestration graph or controller-owned prompt relay.
- Reviewer latency overlaps sibling Worker latency naturally without an
  auto-runner scheduling barrier.
- Crash recovery follows the existing durable callback edge and root job
  lineage instead of adding another scheduler protocol.
- The controller becomes smaller but remains the final integrity boundary.

## Superseded Details

This decision refines the physical-publication wording in Decisions 022, 025,
and 026. Their bundle, capacity, topology, Git, authority, integration, round,
and release rules remain active. Their controller-submitted Reviewer and
controller-submitted node rework details are superseded by this decision.

## Acceptance

- RolePack tests prove the Worker has only the assigned Reviewer chain command
  and Reviewer remains read-only.
- Dispatcher tests prove target restriction, continuation propagation, no
  plain/silent bypass, no callback timeout, and crash recovery.
- Scheduler tests prove one root Worker submission per node, no controller
  Reviewer submission, pass/rework/non-pass lineage validation, no duplicate
  asks, exact final tree integration, and sibling overlap.
- A fresh visible real-provider project proves Worker-initiated review,
  Reviewer pass/rework delivery, integration, round review, and zero dynamic
  residue.

## Related

- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [025-single-lane-multi-workgroup-release-gate.md](025-single-lane-multi-workgroup-release-gate.md)
- [026-authority-envelope-and-adaptive-workgroup-selection.md](026-authority-envelope-and-adaptive-workgroup-selection.md)
- [../topics/single-lane-multi-workgroup-modification-and-test-plan.md](../topics/single-lane-multi-workgroup-modification-and-test-plan.md)
