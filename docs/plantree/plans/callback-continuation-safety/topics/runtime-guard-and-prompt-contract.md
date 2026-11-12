# Runtime Guard And Prompt Contract

Role: implementation plan
Status: active
Read when: implementing chain continuation loop prevention
Related: [incident analysis](incident-analysis.md), [test matrix](test-matrix.md)

Date: 2026-06-22

## Target Behavior

When an agent is running a `chain_continuation` job, its job is to finish the
original task using the child result. The final answer should be captured as the
completion of the continuation job and then propagated by CCB.

The continuation receiver must not create a new `ask --chain` to the original
caller just to deliver that final result.

## Runtime Guard

Add a guard in chain request validation after the active parent job and
parent message are resolved:

1. Detect whether the active parent job's request is a chain continuation.
   Use `message_type == "chain_continuation"` and/or
   `route_options.mode == "chain_continuation"`.
2. Resolve the upstream recipient by following
   [decision 001](../decisions/001-continuation-upstream-identity.md):
   read `route_options.chain_edge_id` from the active continuation parent
   job, load that edge through message bureau storage, and use
   `CallbackEdgeRecord.original_caller`. Do not parse the prompt body, do not
   infer from free text, and do not traverse the whole edge graph.
3. If the new chain request target matches that upstream recipient, reject it
   with a clear dispatch error:

```text
ask --chain from a chain continuation to the original caller is not allowed;
finish the current response and CCB will deliver it upstream.
```

This should be a hard runtime guard, not just skill guidance, because the
failure creates durable result chain edges and can loop across providers.

If the active parent is a chain continuation but its `chain_edge_id`
cannot be resolved, chain requests from that continuation should fail closed
with a metadata error. A continuation without a resolvable edge cannot safely
prove that a new upstream result chain is legitimate.

## Prompt Contract

Rewrite the continuation final instruction from the ambiguous form to a
tool-aware form:

```text
Continue the original task using the child result.
Finish this current response with the final result.
Do not call ask, --chain, or --silence to the original caller; CCB will
deliver this continuation result upstream.
```

Keep original task context and child result in the body, but make any original
routing instructions historical context rather than active instructions.

The body must retain explicit continuation markers and upstream context so an
agent can apply the ask skill rule without guessing. At minimum it should state
that this is a `CCB chain continuation`, name the original caller, identify
the child result, and include the no-ask finalization instruction.

## Ask Skill Contract

Inherited ask skills should keep the existing rule that each waiting hop uses
`--chain` for real child dependencies. Add a separate continuation
finalization rule:

```text
If the current task is a CCB chain continuation, do not use ask to send the
final result to the original caller. Answer the current task directly; CCB will
route the completion.
```

This preserves normal multi-hop chain routing while preventing final-delivery loops.
The wording source of truth for inherited ask skill templates remains
[ask-parameter-policy/topics/skill-update-draft.md](../../ask-parameter-policy/topics/skill-update-draft.md);
this plan defines the runtime safety rule and test expectations.

## Diagnostics

When the guard rejects a request, the error should include:

- the active continuation parent job id;
- the rejected target agent;
- the chain edge id when available;
- an instruction to finish the current continuation directly.

Do not include private prompt bodies in the error.

## Non-Goals

- Do not block legitimate result chain fan-out from a continuation to a different
  child agent in the first slice.
- Do not change the semantics of normal `A --chain -> B`,
  `B --chain -> C` chains.
- Do not make provider-specific ask semantics where Claude has a different
  public contract from Codex.
