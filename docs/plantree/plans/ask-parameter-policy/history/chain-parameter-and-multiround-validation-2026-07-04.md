# Chain Parameter And Multi-Round Validation

Date: 2026-07-04

## Summary

The public dependent-child ask flag is now `--chain`. The old public
`--callback` parameter is removed from CLI usage, parser support, inherited ask
skills, and user-facing docs. This records the landing evidence and the
clarified boundary that prevented misuse in root A-to-B delegation.

## Landed Behavior

- Root/top-level delegation uses plain `ask`.
- `--chain` is used only when the sender is already running an active CCB task
  and cannot finish without a child result.
- `--artifact-reply` remains orthogonal: it preserves the child reply as an
  artifact, and can be combined with `--chain` when the active parent needs the
  full child result.
- A chain continuation must be answered directly when it can finish the current
  task; it must not open a new ask to the original caller just to return the
  final result.

## Regression Evidence

- `test_dispatcher_allows_same_child_chain_across_multiple_continuations`
  covers `A -> B`, then two sequential `B --chain -> C` rounds, then B's final
  reply reaching A.
- `test_dispatcher_three_hop_callback_chain_propagates_sequential_continuations`
  covers multi-hop continuation propagation through `A -> B -> C -> D`.
- The first version of the same-child multi-round test found that the earlier
  B-to-C edge stayed in `CONTINUATION_SUBMITTED`; the dispatcher now marks prior
  continuation edges for the same parent message as `DONE` when the final
  continuation completes.

## Verification Commands

```bash
PYTHONPATH=lib python -m pytest -q test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_allows_same_child_chain_across_multiple_continuations
PYTHONPATH=lib python -m pytest -q test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_callback_routes_child_result_as_parent_continuation test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_callback_chain_waits_for_nested_child_message test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_allows_callback_from_continuation_to_different_child test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_rejects_callback_from_continuation_to_original_caller test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_three_hop_callback_chain_propagates_sequential_continuations test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_allows_same_child_chain_across_multiple_continuations
PYTHONPATH=lib python -m pytest -q test/test_v2_message_bureau_dispatcher_integration.py
PYTHONPATH=lib python -m compileall -q lib/ccbd/services/dispatcher_runtime/callbacks.py
git diff --check -- lib/ccbd/services/dispatcher_runtime/callbacks.py test/test_v2_message_bureau_dispatcher_integration.py
```

Results recorded during landing:

- same-child multi-round test: 1 passed
- focused chain continuation regression set: 6 passed
- full dispatcher/message-bureau integration file: 66 passed
- compileall and diff check: passed

## Follow-Up

The inherited ask skill should keep the root/plain boundary prominent:

```text
A starts work by asking B: plain ask.
B is already handling A's task and needs C: ask --chain C.
B receives C's chain result and can finish: answer the current task directly.
```
