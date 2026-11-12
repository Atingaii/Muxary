# Incident Analysis

Role: context
Status: active
Read when: diagnosing result chain loops, mixed Claude/Codex chains, or bad second result chain edges
Related: [../roadmap.md](../roadmap.md), [runtime guard contract](runtime-guard-and-prompt-contract.md)

Date: 2026-06-22

## Failure Shape

The failure requires at least one chain continuation:

```text
A asks B with result chain
B asks C with result chain
C finishes
CCB sends chain_continuation to B
B should finish current turn so CCB can return to A
B instead asks A with result chain
```

The last step is the bug. It creates a new chain edge where the intended
operation is finalization of the existing edge.

## Observed Provider Difference

Codex-only chains are less likely to misroute because the Codex backend starts
active submissions as `PROTOCOL_EVENT_STREAM` and sends the wrapped prompt
directly into a bound protocol turn:

- [codex start runtime](../../../../../lib/provider_backends/codex/execution_runtime/start.py)

Claude-involved chains are more fragile because the Claude backend runs through
an interactive Claude Code session event log. It stores prompt text and dispatches
later when the pane is ready:

- [claude start runtime](../../../../../lib/provider_backends/claude/execution_runtime/start.py)
- [claude deferred prompt dispatch](../../../../../lib/provider_backends/claude/execution_runtime/polling.py)

That interaction model means Claude sees the continuation as ordinary task text
inside a tool-capable session. If the text says "reply to original caller",
Claude can satisfy that by running `ask --chain` instead of producing the
current turn's final answer.

## Runtime Acceptance Gap

The current chain validation path accepts chain requests when:

- the route is chain mode;
- there is message bureau support;
- delivery is single target;
- the sender has an active parent job;
- the parent message resolves;
- the parent has no existing outstanding result chain;
- the chain depth/cycle check passes.

The missing check is specific to continuation jobs: a
`chain_continuation` parent should not open a new result chain to the upstream
caller as a way to deliver the final result.

Relevant source:

- [chain validation and continuation generation](../../../../../lib/ccbd/services/dispatcher_runtime/callbacks.py)
  (`validate_callback_request`, `_continuation_request`, and
  `_continuation_body`).
- [chain edge record storage](../../../../../lib/message_bureau/callback_edges.py)
  (`CallbackEdgeRecord.original_caller`).

## Prompt Ambiguity

The continuation body currently includes original task context, child task,
child result, and the final instruction to continue the original task and reply
to the original caller.

That is correct at the product level but ambiguous at the agent-command level.
For tool-capable providers, "reply to original caller" must be rephrased as:

```text
Finish this current turn with the final result. Do not call ask, --chain, or
--silence to the original caller; CCB will deliver this continuation result.
```

## Working Conclusion

This is not an `archi` auto-reply bug. The child reply is the expected trigger
for the continuation. The safety issue is that the continuation receiver can
turn finalization into a new upstream result chain, and the runtime currently
permits that edge.
