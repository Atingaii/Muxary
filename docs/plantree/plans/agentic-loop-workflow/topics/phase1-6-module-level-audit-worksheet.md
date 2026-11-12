# Phase 1-6 Module-Level Audit Worksheet

Date: 2026-07-04
Status: RECORDED MODULE AUDIT / NOT A PHASE 6B VERDICT

## Purpose

Record the module-level audit required by the Phase 1-6 acceptance goal after
the full Phase 6A fake-provider matrix completed. This worksheet maps the six
module checks to accepted evidence, residual risk, and the artifacts a reviewer
should inspect.

This does not replace the reviewer2 module/final checklist:
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_9cb0746fad98-art_25c9e57d83a840c1.txt`

Related tracking docs:

- [Phase 1-6 evidence index](../history/phase1-6-evidence-index.md)
- [Draft acceptance report](../history/phase1-6-acceptance-report-draft.md)

## Preconditions

The module-level audit is valid after:

- `smoke-busy-release` single-case runner acceptance in reviewer1
  `job_7fb1ad254939`;
- reviewer1 integrated matrix acceptance in `job_712002b8f005`;
- reviewer2 module/final-report claim-boundary acceptance in
  `job_a34e79ecfc00`;
- the integrated eight-case fake-provider source-wrapper matrix passes with
  `phase6_fake_matrix_status=pass` and `phase6a_pass=true`;
- JSON, JSONL, Markdown report, per-case loop ids, round summaries, ask logs,
  desired/observed topology, and cleanup/residue evidence are available;
- source-control packaging hygiene decisions are recorded separately in
  [phase1-6-final-packaging-hygiene.md](phase1-6-final-packaging-hygiene.md).

## Current Status By Module

| Module | Current State | Accepted Evidence | Residual / Not Covered |
| :--- | :--- | :--- | :--- |
| Plan/Task Document | Accepted with residual risk | Phase 2 accepted; compact-import policy accepted; matrix rows show `route_decision_correct=true` and script-owned round imports. | End-to-end source-wrapper traceability of digest, actor, job id, and imported-at across all eight cases was not independently re-verified beyond matrix fields. |
| Orchestration | Accepted | Phase 3A triage accepted; all eight routes observed with correct route decision, final status, and owner transitions; non-success cases are not marked `done`. | None for the Phase 6A program-matrix scope. |
| Mount Topology | Accepted | Phase 1 and Phase 4A accepted; every matrix row has `topology_dispatch_absent=true`, `communication_edges_absent=true`, and runtime residue booleans true. | Phase 1 remains current worktree evidence, not committed/default-enabled. |
| Ask Collaboration | Accepted with residual risk | Phase 4A ask-first accepted; all rows show correct ask reachability semantics and no provider reply authority parsing. | `smoke-macro-adjustment` and `smoke-blocked` have `ask_reachability=false` by design because no worker/reviewer is mounted. |
| Dynamic Lifecycle | Accepted with residual risk | Phase 5 lifecycle closure accepted with residual risk; `smoke-busy-release` shows busy retain and later idle release evidence. | Source-wrapper failure-mode hooks remain unit-test covered only; real-provider busy detection accuracy is unproven. |
| Evidence And Reporting | Accepted | Matrix report has 8/8 cases observed, no hard failures, complete runtime residue fields, and cleaned Markdown wording. | Phase 6B and real-provider capability remain out of scope. |

## Required Reviewer Evidence

For each module, the reviewer should be able to cite:

- the reviewer2 module/final checklist artifact:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_9cb0746fad98-art_25c9e57d83a840c1.txt`;
- accepted reviewer artifacts for the relevant phase/tranche;
- lifecycle closure acceptance with residual risk:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_069b75debd58-art_35fb1de286b34146.txt`;
- source-wrapper matrix report JSON and rows JSONL;
- generated Markdown matrix report;
- per-case runtime project path and loop id;
- `round.json`, `round_summary.md`, `asks.jsonl`;
- `agent_mount_topology.desired.json`,
  `agent_mount_topology.observed.json`, and topology events;
- `ccb ps`, `.ccb/ccb.config`, and observed topology residue checks;
- authority audit notes proving scripts, not provider replies, changed state.

## Audit Output Shape

The module-level audit result is:

| Module | Verdict | Evidence | Residual Risk |
| :--- | :--- | :--- | :--- |
| Plan/Task Document | `accepted_with_residual_risk` | Phase 2 accepted; compact-import policy accepted; matrix rows show route decisions and script-owned round imports. | Digest/actor/job-id/imported-at traceability across all eight cases was not independently re-verified beyond matrix fields. |
| Orchestration | `accepted` | Phase 3A triage accepted; all eight routes observed with correct route decision, final status, and owner transitions. | None for the Phase 6A program-matrix scope. |
| Mount Topology | `accepted` | Phase 1 and Phase 4A accepted; matrix rows show topology dispatch and communication edges absent; runtime residue booleans true. | Phase 1 remains current worktree evidence, not committed/default-enabled. |
| Ask Collaboration | `accepted_with_residual_risk` | Phase 4A ask-first accepted; ask reachability semantics and no provider reply authority parsing are reflected in all rows. | `macro_adjustment_request` and `blocked` have `ask_reachability=false` by design. |
| Dynamic Lifecycle | `accepted_with_residual_risk` | Phase 5 lifecycle closure accepted; `smoke-busy-release` includes retained-busy and later idle-release evidence. | Failure-mode hooks remain unit-test covered only; real-provider busy detection accuracy is unproven. |
| Evidence And Reporting | `accepted` | Matrix report has 8/8 cases observed, no hard failures, complete runtime residue fields, and cleaned Markdown wording. | Phase 6B and real-provider capability remain out of scope. |

Verdicts should use:

- `accepted`;
- `accepted_with_residual_risk`;
- `blocked`;
- `not_audited`.

Do not mark a module `accepted` from unit tests alone when the acceptance goal
requires source-wrapper or integrated matrix evidence.

## Stop Conditions

Stop module-level acceptance and return to implementation if any of these are
observed:

- agent/provider reply text directly mutates authority state;
- topology mainline accepts or emits communication DSL fields;
- runner revives topology dispatch or provider-output consumption;
- blocked, partial, replan, or busy outcomes become `done`;
- dynamic release leaves unexplained residue in `ps`, config, or observed
  topology;
- the integrated matrix omits a required row or lacks runtime residue fields.
