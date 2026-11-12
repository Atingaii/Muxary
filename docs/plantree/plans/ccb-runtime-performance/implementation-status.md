# Implementation Status

Date: 2026-07-17

## Current Phase

The earlier startup architecture plan's P0-P3 correctness/serial-path core is
implemented in the working tree.  The broader startup-efficiency Goal is in
Phase 0 execution and is not accepted yet.  Its dedicated harness now proves
native run-id/report/resource correlation, strict steady-reuse identity,
privacy-safe CPU/RSS/process/I/O sampling, and official-cleanup process residue
on one Linux Codex-stub fixture.  External wall attribution now exceeds `90%`
and the no-attach timeline is structurally complete with an exact cold keeper
T1.  The result remains `smoke_only` because the scenario, provider, fault, and
platform gates are open.  The latest formal same-fixture `3 + 20` A/B completed
with `20/20` valid pairs, passed the dedicated instrumentation-overhead budget,
and passed exact-T1 readiness plus `24/24` process-I/O-complete resource
profiles.  The lifecycle stale-RMW race found while locating exact T1 now has a
complete keeper-to-child generation
fence, unified lifecycle/lease transaction discipline, strict readiness
identity, timeout-child reaping, deterministic regressions, and clean external
source evidence.  Repeated resource sampling no longer accumulates dead
foreground identities in the active seed; the cumulative set is retained only
for final cleanup audit.  The strict mounted boundary is also closed: socket
publication is transactional, a child-owned self-ping traverses the normal
request worker, runtime restoration runs behind a generation-fenced bootstrap
gate while ping stays serviceable, and only the child may publish final
`phase=mounted/startup_stage=mounted`.  Keeper reconciliation cannot promote
the exact matching interim lease.  A retained external race failure was
converted into a deterministic regression.  A second deep review additionally
closed false mounted from direct `start()`, pre-serving worker-error loss,
foreign-lease lifecycle overwrite, stale child-stage masking of a replacement,
and shutdown-unlink lock ordering.  The post-closure external smoke cleaned up
without residue.  The final-worktree `3 + 20` formal A/B passed its warm
instrumentation-overhead, readiness, resource-quality, and cleanup gates.
A final suite pass then exposed the durable-mounted/in-memory-gate gap.  Final
publication is now dispatch-atomic, failed publication sets stopping while the
gate is held, inactive/no-callback/sticky-worker finish attempts fail closed,
and same-process restart validates its exact allocated generation.  Updated
external smoke and frozen A/B now pass; they qualify the instrumentation-
overhead and cleanup gates for this newer closure without completing Phase 0.
The S4 resource lane now also closes its observed zombie I/O race.  Stable
proc-I/O handles are acquired at first validated stat identity, remain bounded
and close-on-exec, and never turn a failed read into zero or a carried value.
The final S4 `3 + 20` run passed resource I/O `23/23`; the follow-up warm A/B
passed its `10 ms` overhead gate with a `+4.274 ms` confidence-interval upper
bound.  Phase 0 still remains open for the construction/fault/provider/platform
matrix.
Scenario evidence is now fail-closed rather than label-only.  Before and ready
phases are immutable and SHA-chained; final references are rebound to their
exact run and re-read by the summary; stable double-read authority rejects
mixed generations; cold constructors reject attachable namespace, live
runtime, and process residue; same-generation cold relabelling is invalid.
Deterministic startup/resource coverage passes `114/114`.  External S1, S4,
and one-use S5a smoke runs pass scenario, readiness, resource, process-I/O, and
cleanup gates with the expected `same`, `changed`, and `created` identity
relations.  This closes those three smoke construction slices, not the full
scenario or Phase 0 matrix.  The full suite is `5338 passed, 2 skipped, 4`
already-known additive-reload baseline failures, with no new failure from this
checkpoint.  Evidence:
[history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md](history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md).
The serial S3 constructor is now also closed on the same Linux stub fixture.
Its first retained run exposed an exact-owned dead pane being misclassified as
structural topology damage, which rebuilt the namespace and relaunched a healthy
peer.  Structural ownership and live usability are now separate gates: the
target alone is relaunched while the peer, daemon, generation, and namespace are
preserved.  Active cleanup protection now admits only unique live exact expected
slots, caller-owned launch controls are rejected, and the degraded candidate
path uses one bounded listing.  The focused matrix passes `219/219`; final AQ
measured `665.070 ms`,
observed target/peer prepare counts `1/0`, maximum launch concurrency 1, zero
supervision recovery events, and clean teardown.  This closes only S3 serial
smoke, not concurrency or the broader fault/provider/platform matrix.  Evidence:
[history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md](history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md).
The S0 CLI-only hot path is also closed on the Linux Codex-stub fixture.  Its
`ccb_test --print-version` boundary performs no startup transaction
or RPC, retains no startup id/trace, and preserves a single frozen daemon,
generation, namespace, configured-runtime, and report identity.  The retained
first smoke found a harness-only false negative for successful
`health=restored`; the corrected clean-HEAD `3 + 20` run passed `20/20`
measured commands, `23/23` resource/report checks, and `24/24` S0 manifests at
p50/p95 `286.132/298.046 ms`, with clean preservation and official teardown.
This closes S0 only; the overall result remains `smoke_only`.  Evidence:
[history/startup-phase0-cli-only-checkpoint-2026-07-17.md](history/startup-phase0-cli-only-checkpoint-2026-07-17.md).

The implementation sequence, invariants, SLOs, test matrix, and rollback rules
are recorded in
[topics/startup-critical-path-optimization-2026-07-15.md](topics/startup-critical-path-optimization-2026-07-15.md).

## Active TODO

- Measure interactive attach/first-frame T5 separately from the no-attach
  latency lane.
- Add explicit process-snapshot, projection file/byte, helper-spawn, and zero
  counter fields where the request scope can prove them.
- Construct S5b and broader serial fault artifacts; automate a fresh fixture
  per S5a round; keep S2 unavailable until an official daemon-replacement
  primitive exists; then run macOS, WSL, slow-filesystem, real Codex, and Claude
  qualification.  S0/S1/S3/S4/one-use-S5a construction smoke is complete.
- Extend the now-proven serial S3 launch-attempt fence to the remaining fault
  cases before selecting any bounded Provider-specific concurrency cap.

## Blockers

- No implementation blocker remains for the landed P0-P3 core.
- Final provider concurrency caps and slow-filesystem SLOs remain evidence
  dependent and do not block the correctness fix.

## Last Landed

- `af2818d Add runtime performance profiling and latency fast paths`: lifecycle
  profiling harness, detached tmux prepare cache, project_focus fast path,
  pending sidebar-refresh support, tests, and plan evidence.
- `4347082 Optimize project view recent job scans`: pure Python adaptive
  ProjectView recent-job scanning through `JobStore.list_project_view_recent_jobs`,
  preserving the old per-agent maximum scan limit while reducing common-case
  initial reads.

## Next Commit Target

Build S5b and the remaining serial fault-compensation matrix, automate fresh
S5a fixtures, and keep S2 explicitly unavailable until an official replacement
primitive exists; then fill the interactive T5 lane.  Keep bounded
launch concurrency and foreground-first readiness as separate later patches,
and keep unrelated dirty PlanTree/mobile work out of any startup commit.

## Last Verified

- 2026-07-17 S0 CLI-only clean-HEAD formal-size stub run:
  `phase0-s0-cli-only-formal-clean-20260717-d` on commit `c1cf38df` completed
  `3 + 20` with zero failures/timeouts.  All `23/23` CLI-only rounds retained
  one immutable report identity, emitted no startup id, observed exactly one
  newly created command-process identity in sampled profiles, and had
  verified/formal/process-I/O resource profiles; all `24/24` S0 manifests
  passed.  Static `exec`/early-return inspection plus one isolated Linux
  process-syscall trace observed zero `fork`/`vfork`/`clone`/`clone3`; the
  sampled count is still recorded only as a lower bound.  Wall p50/p95 was
  `286.132/298.046 ms`; pre-teardown preservation passed and official cleanup
  was clean.  Summary/cleanup/final-manifest digests are `1629fc529c46`,
  `0a4dd08ed35d`, and `3c8c5a0dc261`.  The focused harness is `103 passed` and
  the expanded resource/source-guard/CLI-management/router matrix is
  `162 passed`.  Evidence:
  [history/startup-phase0-cli-only-checkpoint-2026-07-17.md](history/startup-phase0-cli-only-checkpoint-2026-07-17.md).
- 2026-07-17 S3 serial mixed-recovery: focused topology/restart/harness matrix
  `219 passed in 25.46s`.  Retained AO failed closed after a dead target forced
  namespace rebuild and healthy-peer relaunch; AP proved the product correction
  but exposed a validator false negative; final AQ passed both manifests plus
  readiness/resource/process-I/O/supervision/cleanup gates at `665.070 ms`.
  Daemon/generation/namespace and peer identity stayed the same, target alone
  relaunched with `pane_dead`, prepare counts were `1/0`, probe concurrency was
  1, and supervision recovery events were 0.  Summary/cleanup/manifest/probe
  digests are `ece693aefe4e`, `63d4511e8008`, `3d497aaf0af8`, and
  `416eb9b50b48`.  The companion project-namespace/tmux-cleanup matrix passes
  `58/58`.

- 2026-07-17 stable process-I/O final evidence: retained S4 runs first proved
  both the live-to-zombie terminal race and the narrower first-observation
  race.  After identity-validated handles moved to immediate stat observation,
  a 10-run stress passed `10/10`.  Final S4
  `phase0-s4-early-io-formal-20260717-ag` passed `20/20` measured starts,
  `23/23` readiness/resource/process-I/O, and clean teardown at wall p50/p95
  `1193.533/1327.391 ms`; summary/cleanup digests are `2e9603a9a71e` and
  `8dce37c3e985`.  Warm A/B
  `phase0-warm-stable-io-ab-formal-20260717-ah` passed `20/20` pairs, paired p50
  `+2.783 ms`, CI `[-2.558,+4.274] ms`, resource/readiness `24/24`, and clean
  teardown; plan/summary/cleanup digests are `41a727904643`, `2c73a08bcfc5`,
  and `6fc62698eea0`.  The focused resource/harness matrix is `107 passed`.
  Evidence:
  [history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md](history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md).
- 2026-07-17 atomic-ready final regression and external evidence: focused,
  expanded, and restart/provider matrices passed `80`, `263`, and `87` tests.
  The full suite finished `5324 passed, 2 skipped, 4 failed`; only the known
  additive-reload namespace baseline failed, and all five prior readiness-race
  failures disappeared.  The two deterministic publication races then passed
  `100` repetitions each.  A `7 x 50,000` alternating dispatch micro A/B
  measured a net RLock cost of `41.385 ns/RPC`.  External smoke
  `phase0-warm-strict-atomic-ready-smoke-20260717-y` completed three warm starts
  at p50 `379.489 ms` with clean teardown.  Frozen A/B
  `phase0-warm-strict-atomic-ready-formal-20260717-z` completed `20/20` pairs:
  control/instrumented p50 `389.326/387.804 ms`, paired p50 `-3.562 ms`, CI
  `[-9.150,+8.481] ms`, readiness `24/24`, measured resource profiles `20/20`,
  and clean teardown.  Plan/summary/cleanup digests are `cdab2d62b040`,
  `2b41046e382a`, and `037aaf58d0b4`.  Overall qualification remains
  `smoke_only` because the scenario matrix is incomplete.
- 2026-07-17 strict race-closure final-worktree formal A/B:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-strict-race-closure-formal-20260717-x`.
  The frozen `3 + 20` run completed `20/20` valid pairs with zero failures or
  timeouts.  Control/instrumented p50 was `372.368/376.085 ms`; paired p50 was
  `+4.341 ms` and bootstrap 95% CI was `[-0.515,+9.619] ms`, within the `10 ms`
  budget.  Readiness was `24/24` complete with exact cold T1 `405.138 ms`;
  resource profiles were `24/24` verified/formal/process-I/O complete, and
  official cleanup produced two clean snapshots.  Plan/summary/cleanup digests
  are `d0044f302029`, `3bb835bb07cb`, and `f053c77db219`.
- 2026-07-17 strict mounted/self-ping final regression: the latest focused
  matrix passed `80` tests, the expanded matrix passed `263` tests, and the
  restart plus phase2 provider black-box group passed `87` tests.  The five
  black-box tests that previously exposed the publication race pass as an exact
  subset.  Earlier second-review checkpoints were `128` and `256` tests.
  These cover startup fence, start flow, mount ownership, socket server,
  keeper, daemon wait, bootstrap probe, socket lifecycle, and dispatcher tests.
  The retained pre-atomic-gate source-runtime smoke is
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-strict-race-closure-smoke-20260717-w`:
  cold prime `1109.695 ms`, exact T1 `404.215 ms`, three warm starts with p50
  `372.707 ms`, readiness/resource `5/5`, zero failures/timeouts, and two clean
  cleanup snapshots.  Retained failure, design, and evidence are recorded in
  [history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md](history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md).
- 2026-07-17 exact-T1/active-resource-seed formal A/B:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-exact-t1-active-seed-formal-20260717-p`.
  The frozen `3 + 20` run completed `20/20` valid pairs with zero failures or
  timeouts.  Control/instrumented p50 was `384.835/383.057 ms`; paired p50 was
  `-0.283 ms` and bootstrap 95% CI was `[-4.316,+7.868] ms`, within the
  `10 ms` budget.  Readiness was `24/24` complete with one exact cold T1 and
  23 warm not-required records; resource profiles were `24/24` verified,
  formal-eligible, and process-I/O complete.  Warm active scans observed only
  one or two vanished PIDs rather than growth with round ordinal.  Official
  cleanup produced two clean snapshots.  Plan/summary/cleanup digests are
  `80fc7b2c491c`, `2794468cbcc4`, and `0d37490e2cb5`.
- Exact-T1/resource-harness focused matrix after active-seed correction:
  `216 passed`; the narrower process-resource/harness matrix: `100 passed`.
- 2026-07-17 generation-fence/resource-quality formal A/B:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-fence-io-formal-20260717-l`.
  The frozen `3 + 20` run completed `20/20` valid pairs with zero failures or
  timeouts.  Control/instrumented p50 was `368.857/370.469 ms`; paired p50 was
  `+1.911 ms` and bootstrap 95% CI was `[-4.581,+5.397] ms`, within the
  `10 ms` budget.  Resource profiles were `24/24` verified,
  formal-eligible, and process-I/O complete; readiness artifacts were `24/24`
  complete with cold T1 still provisional.  Official cleanup produced two
  clean snapshots.  Plan/summary/cleanup digests are `82c9cd14f5a9`,
  `cda4064be37c`, and `2598bda6265b`.
- Generation-fence/lifecycle/reload focused matrix: `282 passed`; process
  resource plus startup-harness matrix: `95 passed`.
- 2026-07-17 generation-fence safety smoke:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-startup-fence-resource-recovery-20260717-k`.
  Cold prime, warmup, and measured start completed on generation `7` with zero
  failures/timeouts; measured wall was `366.028 ms`, daemon ensure was
  `0.998 ms`, all three resource profiles were I/O complete, and cleanup had
  two clean snapshots.
- 2026-07-17 formal owner-marked instrumentation A/B:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-formal-20260717-j`.
  The frozen `3 + 20` run completed `20/20` measured pairs with zero failures,
  timeouts, or invalid pairs.  Control/instrumented p50 was
  `371.935/374.550 ms`; paired p50 was `+4.098 ms` and bootstrap 95% CI upper
  bound was `+8.676 ms`, both within the `10 ms` budget.  The overhead gate
  passed.  This earlier run's `2/20` partial process-I/O profiles were resolved
  by the later generation-fence/resource-quality recheck above.
  Plan/summary/cleanup digests are `39a76ae166f2`, `4d8714f30164`, and
  `4ea98707916b`.
- 2026-07-17 lifecycle-transaction external smoke:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-lifecycle-lock-race-20260717-i`.
  Cold prime, warmup, and measured start completed on generation `5` with zero
  failures/timeouts; measured wall was `376.255 ms`, daemon ensure was
  `0.921 ms`, readiness was `3/3` complete, resource gate passed, and cleanup
  had two clean snapshots.  Summary digest: `807a7a5b17b6`.
- Lifecycle race regressions: focused `39 passed`; expanded
  startup/readiness/resource `278 passed`; daemon config-drift/kill/
  service-graph lifecycle matrix `75 passed`.
- 2026-07-17 owner-marked instrumentation A/B smoke:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-20260717-h`.
  One warmup pair and two measured pairs used the same generation/config/reuse
  identity; both measured pairs were valid and the control and instrumented
  evidence gates passed.  Control/instrumented p50 was
  `380.878/386.263 ms`; paired p50 delta was `+5.385 ms` against a `10 ms`
  budget, but the bootstrap 95% CI upper bound was `+11.599 ms`.  The gate is
  correctly `smoke_only`, not pass.  Official cleanup left two clean
  snapshots.  Plan/summary/cleanup digests are `713edb511eb6`,
  `198273a87cc2`, and `ff3adcd5661f` respectively.
- 2026-07-17 owner-marked readiness/attribution smoke:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-readiness-attribution-20260717-g`.
  Prime/warmup/measured wall was `1093.006/372.574/363.129 ms`; process
  bootstrap was `243.986 ms`, CLI was `99.766 ms`, and external attribution
  reached `94.664%`.  Three of three no-attach timelines were structurally
  complete, but the cold prime correctly remained a T1 upper bound.  The
  measured resource profile and cleanup gate passed; official cleanup reached
  unmounted/stopped with two clean discovery snapshots.  Summary digest:
  `bccee3886a7220884ab1048a4b5c7732e19869ba4f2dd6045175230a49aa8efb`.
- Earlier focused startup/readiness/resource matrix: `232 passed`.
- 2026-07-16 owner-marked external resource-correlation smoke:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260716-7f08a9db/artifacts/startup/phase0-warm-resource-correlation-20260716-b`.
  Prime/warmup/measured command wall was `1266.136/438.609/400.884 ms`;
  three of three resource profiles were complete and native-run correlated;
  measured sampled CPU was `0.270 s`, peak RSS `160,440,320 B`, process peak
  `5`, and sampler/runner wall outside the command `1.375 ms`.  Official kill
  reached unmounted/stopped and two consecutive full-discovery snapshots found
  zero residue.  Summary digest:
  `3662986319b10cbe77f5276e9001f6f98c1488bdf730750b43e491d0da5df517`.
- Earlier resource/harness unit matrix: `50 passed` across
  `test_perf_process_resources.py` and `test_perf_ccb_startup.py`; lifecycle
  profiler compatibility remained `12 passed` before the external smoke.

- Isolated source-runtime project:
  `/home/bfly/yunwei/test_ccb2/startup-perf-talk1-20260715` with 5 explicit
  windows, 10 Codex-stub agents, isolated `HOME` / `CCB_SOURCE_HOME`, and the
  absolute source `ccb_test` wrapper.
- Cold start after clean kill: `2.20s`. Twenty unchanged warm starts ranged
  from `0.52s` to `0.64s`, p50 about `0.555s`, p95 `0.63s`.
- Warm report proved 10 `attached`, zero relaunches, zero provider preparation,
  actual tmux window ids `@0` through `@4`, and no repeated pane relabel actions.
- `doctor` surfaced `startup_last_timings_ms` and
  `startup_last_provider_prepare_count=0`.
- Focused changed-surface regression: `322 passed`.
- Full Python run: `5069 passed, 2 skipped`, then one restore-contract failure.
  The failure was corrected and its black-box test plus impacted startup tests
  passed (`8 passed`); the broader changed-surface matrix passed afterward.
- `git diff --check` passed.
- 2026-07-15 static startup trace covered `start_flow_runtime`,
  `start_preparation`, binding matching, topology health assessment, provider
  preparation/materialization, Codex live identity, tmux topology discovery,
  and durable runtime stores.
- Read-only live facts confirmed an explicit five-window layout with entry
  window `@0` and managed panes in `@0` through `@4`, while project state holds
  only one `workspace_window_id`.
- The inherited Codex plugin projection source contained about 5,279 files and
  87 MB, confirming that repeated scans/copies have material amplification.
- Source runtime profile artifact:
  `/tmp/perf_realtarget/real_provider_cpu_profile_accurate3.json`
- Worker1 harness review:
  `python -m pytest -q test/test_perf_runtime_lifecycle_profile.py`
  passed with `11 passed`.
- Worker1 smoke checks from `/home/bfly/yunwei/test_ccb2`:
  `/tmp/ccb_runtime_profile_startup_diagnose_scoped.json` and
  `/tmp/ccb_runtime_profile_load_sleep_scoped.json`.
- Worker2/main tmux prepare cache review:
  `PYTHONPATH=lib python -m pytest -q
  test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py -q`
  passed.
- Main focus fast-path review:
  `PYTHONPATH=lib python -m pytest -q
  test/test_ccbd_project_focus.py test/test_sidebar_click.py` passed with
  `15 passed`.
- Combined targeted regression:
  `PYTHONPATH=lib python -m pytest -q
  test/test_perf_runtime_lifecycle_profile.py
  test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py
  test/test_ccbd_project_focus.py test/test_sidebar_click.py` passed with
  `117 passed`.
- Project_view dirty-state regression:
  `PYTHONPATH=lib python -m pytest -q
  test/test_ccbd_project_view.py test/test_ccbd_service_graph.py` passed with
  `65 passed`; this verifies current consistency but does not accept worker3's
  mismatched project_view/Rust-helper slice.
- Project_view pending-refresh blocker fix:
  `PYTHONPATH=lib python -m pytest -q
  test/test_ccbd_project_focus.py test/test_sidebar_click.py
  test/test_ccbd_project_view.py test/test_ccbd_service_graph.py` passed with
  `81 passed`.
- Final targeted regression:
  `PYTHONPATH=lib python -m pytest -q
  test/test_perf_runtime_lifecycle_profile.py
  test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py
  test/test_ccbd_project_focus.py test/test_sidebar_click.py
  test/test_ccbd_project_view.py test/test_ccbd_service_graph.py` passed with
  `183 passed`.
- Sidebar single-RPC working-tree slice:
  `PYTHONPATH=lib python -m pytest -q test/test_sidebar_click.py
  test/test_ccbd_socket_client.py test/test_ccbd_service_graph.py` passed with
  `27 passed`; `python -m py_compile
  dev_tools/perf_sidebar_click_latency.py` passed; `git diff --check` passed
  for the touched sidebar/RPC/test/plan paths.
- Source wrapper smoke after runtime helper change:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` and
  `ccb_test config validate` passed from `/home/bfly/yunwei/test_ccb2`.
- Shell/system bucket split:
  `PYTHONPATH=lib python -m pytest -q test/test_perf_runtime_lifecycle_profile.py`
  passed with `12 passed`; `python -m py_compile
  dev_tools/perf_runtime_lifecycle_profile.py
  test/test_perf_runtime_lifecycle_profile.py` passed.
  High-load artifact: `/tmp/ccb_runtime_shellsplit_profile_v2.json`.
  Startup artifact: `/tmp/ccb_runtime_shellsplit_startup_profile.json`.
- Worker report artifact:
  `.ccb/ccbd/artifacts/text/completion-reply/job_21a7c0c0b62a-art_19c8d2c809734472.txt`
- Rust helper benchmark evidence remains in
  `dev_tools/perf_results/python_rust_phase3_native_output_helper.json`,
  `python_rust_phase4_storage_scan_helper.json`, and
  `python_rust_phase12_storage_summary_helper.json`.

## Execution Notes

- `talk1` owns analysis, implementation, and verification directly for this
  workstream. Do not dispatch worker agents unless the user explicitly changes
  that instruction.
- Source runtime validation must run from `/home/bfly/yunwei/test_ccb2` with
  `/home/bfly/yunwei/ccb_source/ccb_test` and isolated `HOME` /
  `CCB_SOURCE_HOME`.
- Do not use the source checkout as a live runtime directory and do not mutate
  its installed-release `.ccb` runtime state during source validation.
