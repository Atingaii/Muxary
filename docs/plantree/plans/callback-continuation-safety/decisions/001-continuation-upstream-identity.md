# Continuation Upstream Identity Source

Date: 2026-06-22

## Context

The chain-continuation guard needs to know which upstream actor must receive
the continuation result. The unsafe pattern is a continuation receiver opening a
new `ask --chain` to that upstream actor instead of finishing the current
continuation job.

The current chain edge model stores `CallbackEdgeRecord.original_caller`.
The continuation request stores `route_options.chain_edge_id`,
`chain_parent_job_id`, `chain_child_job_id`, and
`chain_child_message_id`; it does not copy `original_caller` directly into
route options.

## Decision

The runtime guard resolves upstream identity from chain edge authority:

1. Confirm the active parent job is a chain continuation by
   `message_type == "chain_continuation"` and/or
   `route_options.mode == "chain_continuation"`.
2. Read `route_options.chain_edge_id` from that active parent job.
3. Load the edge through message bureau storage by edge id.
4. Treat `CallbackEdgeRecord.original_caller` as the upstream recipient that
   must not receive a new `ask --chain` from this continuation.
5. Compare the new chain request target against that normalized upstream
   recipient.

The guard must not parse the continuation body, infer from free text, or walk
the whole result chain graph to guess the upstream recipient.

If the continuation parent is missing `chain_edge_id` or the edge cannot be
loaded, chain requests from that continuation fail closed with a metadata
diagnostic instead of creating a new chain edge.

## Consequences

This keeps the guard tied to durable chain edge authority rather than prompt
text. It preserves normal multi-hop result chains because each real child
dependency still creates its own edge, while only final-delivery asks back to
the current continuation's upstream caller are blocked.

Plain `ask` and `--silence` from a continuation to the upstream caller are not
blocked in slice 1. They remain accepted residual risks because they can create
confusing extra work but do not create the chain loop edge this decision is
designed to prevent.
