# Callback Continuation Safety Plan

Date: 2026-06-22

## Purpose

Prevent chain continuation jobs from being mistaken for new upstream
delegation work. The immediate failure mode is a mixed-provider chain where
Claude receives a chain continuation and sends `ask --chain` back to the
original caller instead of finishing the current turn so CCB can auto-propagate
the result.

## Current Incident Summary

The observed chain was:

```text
bugb -> coworker -> archi -> coworker continuation
```

The `archi -> coworker` continuation was correct. The failure started when
`coworker` treated the continuation instruction as a new CCB send and issued a
new `ask --chain` to `bugb`. That created a second chain edge and allowed
the participants to keep replying through fresh result chain work instead of
settling the original edge.

Codex-only chains are less likely to hit this because Codex is handled as a
more tightly bound protocol turn. Claude runs as an interactive Claude Code pane
with projected ask guidance and command access, so ambiguous "reply to original
caller" language is more likely to become an actual `ask` command.

## Recommended Direction

Use runtime authority first, then prompt and skill hardening:

1. Add a `ccbd` guard that rejects `ask --chain` from a
   `chain_continuation` job when the target is the original caller or
   upstream caller for that continuation.
2. Rewrite chain continuation text so it says to finish the current turn and
   not call `ask`, `--chain`, or `--silence` to the original caller.
3. Add provider-neutral ask skill guidance for chain continuation finalizing,
   with Claude-specific validation because Claude is the easiest provider to
   trigger the loop.
4. Add mixed-provider regression coverage that proves the bad second edge is
   rejected while normal multi-hop chain routing still works.

## Authority

Product/runtime contracts under `docs/` still own shipped behavior. This plan
records the targeted safety change and readiness path.

Related authority and context:

- [../../baseline/runtime-flows.md](../../baseline/runtime-flows.md)
- [../../baseline/test-and-release-gates.md](../../baseline/test-and-release-gates.md)
- [../ask-parameter-policy/README.md](../ask-parameter-policy/README.md)
- [../ask-parameter-policy/topics/result chain-silence-boundaries.md](../ask-parameter-policy/topics/result chain-silence-boundaries.md)
- [../ask-parameter-policy/topics/skill-update-draft.md](../ask-parameter-policy/topics/skill-update-draft.md)
- [../managed-provider-completion-reliability/README.md](../managed-provider-completion-reliability/README.md)
- [../../../../lib/ccbd/services/dispatcher_runtime/callbacks.py](../../../../lib/ccbd/services/dispatcher_runtime/callbacks.py)
- [../../../../lib/message_bureau/callback_edges.py](../../../../lib/message_bureau/callback_edges.py)
- [../../../../lib/provider_backends/claude/execution_runtime/start.py](../../../../lib/provider_backends/claude/execution_runtime/start.py)
- [../../../../lib/provider_backends/codex/execution_runtime/start.py](../../../../lib/provider_backends/codex/execution_runtime/start.py)

## File Map

- [roadmap.md](roadmap.md): planning state, implementation slices, and gates.
- [implementation-status.md](implementation-status.md): current landed work,
  validation evidence, and remaining handoff.
- [open-questions.md](open-questions.md): unresolved policy choices.
- [topics/incident-analysis.md](topics/incident-analysis.md): observed failure
  shape and provider behavior analysis.
- [topics/runtime-guard-and-prompt-contract.md](topics/runtime-guard-and-prompt-contract.md):
  proposed runtime and prompt-level contract.
- [topics/test-matrix.md](topics/test-matrix.md): unit and external
  source-under-test validation matrix.
- [decisions/001-continuation-upstream-identity.md](decisions/001-continuation-upstream-identity.md):
  decision for resolving the upstream caller during runtime validation.
- [history/source-implementation-2026-06-22.md](history/source-implementation-2026-06-22.md):
  implementation and validation checkpoint.

## Scope

In scope:

- Callback continuation validation in `ccbd`.
- Callback continuation body text.
- Inherited ask skill wording for continuation finalization.
- Mixed Codex/Claude result chain-chain tests and source-under-test validation.
- Diagnostics that make bad second-edge attempts easy to identify.

Out of scope:

- Transport-level FIFO, ACK, large-payload spool, or cancel visibility work.
- Provider session isolation or startup supervision.
- General ask parameter policy unrelated to chain continuation finalization.
- Changing the public semantics that each waiting hop in a normal result chain
  chain uses `--chain`.
