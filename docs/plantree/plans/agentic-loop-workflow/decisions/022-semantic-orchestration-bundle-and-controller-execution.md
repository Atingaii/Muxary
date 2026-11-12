# 022 Semantic Orchestration Bundle And Controller Execution

Date: 2026-07-10
Status: Accepted for planning

## Context

The workflow currently separates planner, task detailer, orchestrator, dynamic
workers, reviewers, mount topology, and script-owned state. That separation is
useful, but two design risks remain:

- turning every responsibility boundary into another serial provider call;
- separating work slicing, dependency design, logical assignment, and task
  publication so far that two components repeat the same semantic work.

Work slicing and logical task assignment are one semantic decision. Reliable
`ask` submission, exact-once recovery, concrete agent binding, topology
reconciliation, and authority writes are runtime side effects. They need a
hard boundary, but they must not become two competing planners.

The planner/detailer boundary also needs a global consistency loop. Local
detail can invalidate plan assumptions without requiring the long-lived
planner to absorb every source-level detail.

## Decision

CCB keeps semantic orchestration coupled and separates only its runtime side
effects.

For a task that requires semantic orchestration, one immaculate
`ccb_orchestrator` activation produces one complete orchestration bundle. The
bundle owns all of these decisions together:

- bounded work-unit slicing;
- dependency and parallelism graph;
- logical role assignment for each work unit;
- complete worker task packets;
- acceptance and verification references;
- reviewer assignment and integration points;
- bounded rework and partial-result policy;
- capacity intent and immediately dispatchable nodes.

The controller must not reinterpret or redesign that bundle. It owns only:

- schema and authority validation;
- concrete role-to-agent binding from an allowed capacity snapshot;
- mount topology commit, reconcile, and readiness checks;
- exact-once `ask` submission and durable job references;
- callback-driven resume, artifact import, and script-owned transitions;
- busy-retain, release, and lifecycle evidence.

The orchestrator decides **what is published and to which logical role**. The
controller performs the physical publication to a concrete mounted agent.

## Planner And Detail Feedback

The long-lived planner remains the owner of global goals, architecture
boundaries, cross-task dependencies, invariants, macro acceptance, and
integration milestones. It does not absorb source-level implementation noise.

Every task-detail pass must return both:

- a local detail packet for execution design;
- a compact global-impact result, including `none`, `bounded`, or `macro`.

`none` may pass a deterministic global-consistency gate. `bounded` updates a
script-owned compact summary and may require an integration review. `macro`
must return to planner before execution. A detail result is only locally ready
until this gate passes.

## Activation And Latency

Logical role boundaries do not imply mandatory provider calls.

- A planner packet that explicitly qualifies for the predefined
  single-worker/single-reviewer template may bypass an orchestrator provider
  activation after deterministic validation.
- A task with multiple work units, dependencies, integration points, uncertain
  execution shape, structural rework, or partial continuation activates the
  orchestrator once to produce the complete bundle.
- A task detailer is activated only when source-backed refinement or task-local
  clarification is actually required.
- Topology and round-control modules are program code, not additional agents.

The target serial provider depth is four calls for a normal single-unit project
task and five to six for a genuinely complex task. Multiple workers should be
parallel where the accepted bundle declares them independent.

## Capacity Coupling

Before orchestration, the controller provides a read-only capacity envelope:
allowed roles and profiles, maximum instances, provider constraints, window
capacity, and lifecycle policy. The orchestrator designs against that envelope
once.

If runtime capacity changes before dispatch, the controller returns an
explicit `capacity_conflict`. It must not silently shrink, serialize, reassign,
or otherwise rewrite the graph. A new immaculate orchestration activation may
then produce a replacement bundle.

## Consequences

- There is no separate LLM task publisher after the orchestrator.
- `Workgraph Planner` is a capability name for the narrowed orchestrator, not a
  second role.
- Mount topology remains free of semantic communication edges.
- Provider replies cannot own task status or runtime authority.
- The controller can resume after crashes without repeating semantic planning.
- Simple tasks can avoid an unnecessary orchestrator call, while complex tasks
  retain one coherent semantic owner.
- Detail-to-plan feedback becomes mandatory but compact.

This decision refines Decision 019 by separating current triage behavior from a
future validated single-unit fast path. It refines Decision 020 by assigning
physical `ask` submission to the controller rather than to provider-side
orchestrator commands. It does not invalidate mount-only topology or ask-first
collaboration.

## Non-Goals

- Do not add a separate topology-planning agent.
- Do not add a second LLM that republishes or re-slices an accepted bundle.
- Do not let the controller infer semantic work from natural-language replies.
- Do not bypass independent review merely to reduce latency.
- Do not claim that the optimized bundle path is implemented until source and
  real opened-project evidence exist.

## Related

- [019-orchestrator-triage-before-task-detailer.md](019-orchestrator-triage-before-task-detailer.md)
- [020-mount-topology-and-ask-first-orchestration.md](020-mount-topology-and-ask-first-orchestration.md)
- [021-immaculate-role-context-lifecycle.md](021-immaculate-role-context-lifecycle.md)
- [../topics/semantic-orchestration-and-controller-boundary.md](../topics/semantic-orchestration-and-controller-boundary.md)
