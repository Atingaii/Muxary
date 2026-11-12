# Chain Continuation Safety Roadmap

Date: 2026-06-22

## Status Summary

- Current status: In progress.
- Work mode: execute-ready, then status-update.
- Current priority: finish any live mixed-provider validation that requires a
  healthy external runtime environment.
- Last landed: source implementation in the working tree on 2026-06-22; see
  [history/source-implementation-2026-06-22.md](history/source-implementation-2026-06-22.md).
- Last verified: targeted pytest, full pytest, source wrapper diagnose, and
  source doctor smoke on 2026-06-22; see implementation status.

## Done

- Classified the failure as a chain continuation finalization bug, not a
  child-agent reply bug.
- Identified the runtime acceptance gap in
  [callbacks.py](../../../../lib/ccbd/services/dispatcher_runtime/callbacks.py):
  chain validation checks active parent, single target, outstanding edge,
  depth, and cycles, but does not reject upstream callbacks from continuation
  jobs.
- Identified the prompt ambiguity in chain continuation text: it says to
  reply to the original caller without saying that the agent must answer in the
  current turn and must not call `ask`.
- Identified why Claude exposes the problem more readily than Codex: Claude is
  an interactive pane with ask command affordances, while Codex is bound through
  a protocol event stream.
- Accepted the slice-1 guard boundary: reject `ask --chain` from a
  chain-continuation job to its upstream caller, while treating plain `ask`
  and `--silence` to that caller as residual risks for later review.
- Recorded the upstream identity source in
  [decisions/001-continuation-upstream-identity.md](decisions/001-continuation-upstream-identity.md):
  resolve the continuation edge by `route_options.chain_edge_id`, then use
  `CallbackEdgeRecord.original_caller`.
- Routed ask skill wording changes through
  [ask-parameter-policy](../ask-parameter-policy/README.md), so this plan owns
  the runtime safety rule while the ask-parameter plan owns inherited skill
  template wording.
- Created this plan root and linked it from the plantree entrypoint.
- Implemented the runtime guard in
  [callbacks.py](../../../../lib/ccbd/services/dispatcher_runtime/callbacks.py).
- Rewrote chain continuation prompt text to require direct finalization and
  prohibit `ask`, `--chain`, and `--silence` to the original caller.
- Updated inherited ask skill templates and runtime memory coordination rules
  with chain-continuation finalization guidance.
- Updated chain behavior documentation in
  [managed-provider-completion-reliability-plan.md](../../../managed-provider-completion-reliability-plan.md),
  [developer communication chapter](../../../manuals/developer-guide/chapters/04-communication.tex),
  and [ccb-self expert guide](../../../manuals/ccb-self-expert-guide.md).
- Added regression coverage for upstream result chain rejection, missing
  continuation edge metadata, allowed result chain to a different child, prompt
  wording, and three-hop continuation propagation.

## In Progress

- Keep this workstream open until a healthy external source runtime can run a
  real mixed-provider multi-hop chain. The current external project doctor is
  runnable but reports a stale/degraded ccbd from historical state.

## Next

1. Run a live mixed-provider multi-hop chain from a clean or repaired external
   source-test project when real provider panes are intentionally available.
2. If live validation exposes Claude-specific prompt drift, adjust only prompt
   or skill text; keep the runtime guard provider-neutral.
3. Revisit whether plain `ask` or `--silence` from a chain continuation to
   the upstream caller should become warnings or hard errors after one release
   cycle.

## Deferred

- Rejecting plain `ask` or `--silence` from a chain continuation to the
  upstream caller. Slice 1 accepts this residual risk because those routes can
  create confusing extra work but do not create the result chain loop edge that this
  plan is blocking.
- Moving reply-delivery notices out of Claude's visible conversation history.
- Adding public README examples for chain continuation internals.
- Adding or revising `ccb-manuals` result chain communication content after the
  runtime change lands.
- Provider-specific policy drift where Claude and Codex would have different
  user-facing ask semantics.

## Release Gate

This safety change is ready when:

- the bad continuation pattern `A -> B -> C`, then `B continuation --chain
  -> A`, is rejected with a clear error;
- normal result chains with each waiting hop using `--chain` still pass;
- continuation prompt text explicitly tells the agent to finish in the current
  turn and not send a new ask to the original caller;
- the continuation finalization rule is present in inherited ask skill
  templates and covered by at least one static assertion per provider where
  ask skills are projected;
- shipped chain behavior docs and `ccb-manuals` have either been updated or
  explicitly marked not applicable for this internal guard;
- unit tests cover chain validation and continuation body wording;
- external source-under-test validation covers at least one Codex-only chain
  one Claude-involved chain, and one three-hop continuation propagation chain.
