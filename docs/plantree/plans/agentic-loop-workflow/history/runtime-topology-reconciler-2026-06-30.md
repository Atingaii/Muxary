# Runtime Topology Reconciler Landing

Date: 2026-06-30

## Summary

Landed the first `ccb loop topology` desired-state command surface:

- `propose`: import an orchestrator-authored runtime workflow graph proposal;
- `validate`: check profiles, capacity limits, duplicate agents, unknown edge
  dependencies, and edge dependency cycles;
- `commit`: write `agent_topology.desired.json` as a revisioned authority file;
- `reconcile`: compare desired topology with runtime lifecycle state and call
  existing dynamic agent lifecycle and layout code for add, move, park, release,
  and reflow;
- `status`: read desired/observed topology summaries;
- `release`: mark topology-owned agents absent and release idle dynamic agents.

The implementation keeps orchestrator semantic and non-authoritative. It
generates graph proposals only; CCB scripts validate, commit, and reconcile
runtime authority.

## Files

- `lib/cli/services/loop_topology.py`
- `lib/cli/parser_runtime/commands.py`
- `lib/cli/models_start.py`
- `lib/cli/phase2*.py`
- `lib/cli/render*.py`
- `test/test_loop_topology_cli.py`

## Verified

- `PYTHONPATH=lib python -m py_compile lib/cli/services/loop_topology.py test/test_loop_topology_cli.py`
- `PYTHONPATH=lib python -m pytest -q test/test_loop_topology_cli.py test/test_loop_capacity_cli.py`
  passed: 33 tests after post-review hardening.
- `PYTHONPATH=lib python -m pytest -q test/test_agent_lifecycle_cli.py test/test_layout_status_cli.py test/test_v2_config_loader.py test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py test/test_loop_topology_cli.py test/test_loop_capacity_cli.py`
  passed: 281 tests after post-review hardening.
- `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` from
  `/home/bfly/yunwei/test_ccb2` confirmed the source wrapper and external test
  root.
- External source-wrapper smoke in
  `/home/bfly/yunwei/test_ccb2/topology-smoke-20260630194447` validated
  `propose -> commit --apply -> status -> release`, with `released_count = 2`
  and `retained_count = 0`.
- External source-wrapper two-revision smoke in
  `/home/bfly/yunwei/test_ccb2/topology-move-20260630194621` validated
  move, park, release, and reflow actions. The worker lifecycle ended
  `parked` in `node-smoke2-node2`; the reviewer lifecycle ended `unloaded`.
- External source-wrapper post-review policy smoke in
  `/home/bfly/yunwei/test_ccb2/topology-policy-20260630200311` validated
  long-lived planner `absent` with release policy `auto`: lifecycle ended
  `parked`, resolved policy was `park`, and observed drift was empty.
- External source-wrapper post-review release smoke in
  `/home/bfly/yunwei/test_ccb2/topology-release-20260630200347` validated
  short-lived worker/reviewer release still unloads with `released_count = 2`
  and `retained_count = 0`.
- External source-wrapper release/shrink regression smoke on 2026-07-01 in
  `/home/bfly/yunwei/test_ccb2/orchestrator-topology-fix-20260701-211256`
  validated `1 -> 2 -> 4` topology growth followed by `4 -> 2 -> 1 -> 0`
  shrink and final release. All shrink commits reconciled with empty drift.
- External source-wrapper codex-worker release replay on 2026-07-01 in
  `/home/bfly/yunwei/test_ccb2/orchestrator-autonomous-smoke-20260701-193340`
  replayed the earlier `pane missing for removed agent` failure and validated
  release now reports `released_count = 1`, observed state `released`, and
  empty drift.
- Focused regression after the release/shrink fix passed:
  `PYTHONPATH=lib python -m pytest -q test/test_loop_topology_cli.py`
  produced `14 passed`.
- Neighboring regression after the release/shrink fix passed:
  `PYTHONPATH=lib python -m pytest -q test/test_agent_lifecycle_cli.py test/test_layout_status_cli.py test/test_v2_config_loader.py test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py test/test_loop_topology_cli.py test/test_loop_capacity_cli.py test/test_ccbd_reload_apply.py`
  produced `318 passed`.

## Post-Review Hardening

Review artifact:
`.ccb/ccbd/artifacts/text/completion-reply/job_221e05b36355-art_45786ea1af5a46ec.txt`.

Accepted and fixed:

- Topology release now defaults to `auto` and propagates topology/per-agent
  release policy into `agent_lifecycle`; long-lived roles park while
  short-lived execution roles unload.
- Reconcile failure now writes an observed `failed` record with the partial
  action list and error, then re-raises the failure instead of hiding it.
- Existing same-loop dynamic agents are treated as an idempotent add noop in
  the narrow recovery path.
- Duplicate node ids are rejected during proposal validation.
- Drift treats `absent` satisfied by released, parked, or hidden runtime state,
  matching role-class release policy.
- Topology release/shrink now batches same-policy dynamic releases so removing
  multiple short-lived loop agents is applied as one future-safe reload instead
  of a sequence of unsafe intermediate reloads.
- Reconcile skips already `unloaded` loop-owned dynamic records so repeated
  shrink/release does not try to remove already released agents again.
- Batch lifecycle release now writes retained-busy evidence back to lifecycle
  state, preserving the previous single-agent behavior when one target is busy
  and other idle siblings can still be released.
- `loop topology status` now surfaces observed reconcile failure as top-level
  `failed` instead of reporting `ready` when desired and observed revisions
  match but the last reconcile failed.

Added tests cover repeat reconcile idempotency, busy retain, cross-loop
isolation, stale base revision, unknown profile, capacity overflow, duplicate
node id, absent-to-present reactivation, missing desired/release safety, and
partial reconcile recovery.

## Remaining Boundaries

- The V1 reconciler writes and applies runtime topology, but does not yet
  execute topology ask edges.
- Mounted real-provider movement and busy-agent release retention should remain
  opt-in gates before production default enablement.
- `loop runner --once` still needs to consume committed topology before and
  after round dispatch.
