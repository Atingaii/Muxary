# Implementation Status

Date: 2026-06-22

## Current Phase

Source implementation landed in the working tree. Runtime/unit validation is
complete; live mixed-provider validation remains pending until a clean external
source-test runtime is available.

## Active TODO

- Run a real Codex/Claude multi-hop chain from `/home/bfly/yunwei/test_ccb2` or
  another allowed external test project after the stale/degraded ccbd state is
  repaired or a clean project is prepared.
- Watch for any user-facing need to reject plain `ask` or `--silence` from a
  chain continuation to the upstream caller.

## Done This Phase

- Added a chain validation guard that rejects `ask --chain` from a
  `chain_continuation` job to the edge's original caller.
- Made missing continuation edge metadata fail closed for chain requests
  from continuation jobs.
- Rewrote chain continuation prompt text to require direct finalization and
  prohibit `ask`, `--chain`, or `--silence` to the original caller.
- Updated inherited ask skills and generated runtime memory coordination rules.
- Updated chain behavior docs and manuals.
- Added regression tests for the bad second chain edge, allowed different
  child result chain, missing edge metadata, prompt wording, and three-hop
  propagation.

## Blockers

- No source blocker for the implemented guard.
- Live provider-chain validation is blocked by the current external test
  project's stale/degraded ccbd state unless the project is intentionally
  repaired or replaced.

## Last Verified Commands

- `python -m pytest -q test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_callback_routes_child_result_as_parent_continuation test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_rejects_callback_from_continuation_to_original_caller test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_allows_callback_from_continuation_to_different_child test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_rejects_callback_from_continuation_with_missing_edge test/test_v2_message_bureau_dispatcher_integration.py::test_dispatcher_three_hop_callback_chain_propagates_sequential_continuations test/test_ask_skill_templates.py`
  -> `8 passed`
- `python -m pytest -q test/test_project_memory.py test/test_v2_message_bureau_dispatcher_integration.py test/test_ask_skill_templates.py test/test_v2_ask_service.py test/test_ask_cli.py test/test_v2_cli_router.py`
  -> `175 passed`
- `python -m pytest -q`
  -> first run `2954 passed, 2 skipped`; second run after runtime-memory update
  produced one startup readiness flake, `2953 passed, 2 skipped, 1 failed`.
- `python -m pytest -q test/test_v2_phase2_entrypoint.py::test_ccb_start_loads_claude_binding_from_project_anchor`
  -> `1 passed`, confirming the full-run failure was a startup timing flake.
- `HOME=/home/bfly/yunwei/test_ccb2/source_home CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home /home/bfly/yunwei/ccb_source/ccb_test --diagnose`
  -> allowed source-test project, source checkout cwd `no`, project inside
  source `no`.
- `HOME=/home/bfly/yunwei/test_ccb2/source_home CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home /home/bfly/yunwei/ccb_source/ccb_test doctor`
  -> command completed; reported historical stale/degraded ccbd state in
  `/home/bfly/yunwei/test_ccb2`.

## Handoff Notes

The runtime guard is provider-neutral and should remain in `ccbd`, not in
Claude-specific code. The prompt and skill text reduce accidental misuse, but
the hard rejection is the safety boundary.
