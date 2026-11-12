# Startup Critical-Path Optimization

Date: 2026-07-15

Role: implementation plan
Status: P0-P3 core implemented; P4-P5 deferred
Authority: subordinate to the startup and configuration contracts
Domain: `ccb start`, `ccbd` startup, managed provider mount, tmux namespace
Read when: changing startup reuse, provider preparation, topology discovery, or
startup readiness
Related:
[startup supervision contract](../../../../ccbd-startup-supervision-contract.md),
[configuration layout contract](../../../../ccb-config-layout-contract.md),
[baseline runtime flows](../../../baseline/runtime-flows.md)

## Objective

Reduce a reported warm `ccb` startup from more than 20 seconds to a predictable
sub-second or low-single-digit path without weakening project ownership,
provider identity, pane recovery, or durable runtime authority.

The optimization order is deliberate:

1. Stop false relaunches of healthy panes.
2. Remove repeated work from the remaining launch path.
3. Collapse global discovery into request-scoped snapshots.
4. Add bounded concurrency only after ownership and write ordering are clear.
5. Consider foreground-first readiness only as a separately gated behavior
change.

## Implementation Result

The 2026-07-15 working-tree implementation completed the correctness-led and
low-risk critical-path work:

- explicit topology reuse now matches logical window plus current namespace
  epoch and records each pane's actual tmux window id
- startup classifies bindings before provider mutation; reuse performs zero
  provider preparation and launch/relaunch performs one pass
- Codex profile resolution no longer duplicates managed-home projection inside
  one preparation pass
- existing namespace validation reuses one pane snapshot across topology,
  sidebar-helper, active-pane, binding, and pane-identity checks
- Codex live identity lazily reuses one `/proc` parent map for the startup
  classification batch
- unchanged pane identity is not rewritten; changed identity is issued as one
  tmux command batch per pane
- startup-sensitive spec/runtime, workspace-binding, and provider-profile
  writes skip identical content without changing generic `JsonStore.save()`
  semantics
- startup reports and `doctor` expose stage timings, per-agent duration,
  provider preparation count/time, binding reject reason, request-scoped tmux/
  subprocess counts, atomic durable write/skip counts, and cleanup topology

P0 remains partial because explicit process-snapshot, projection-file/byte, and
helper-spawn counters are not yet persisted, and absent operations still use a
sparse map rather than every formal zero field.  A separate source-only harness
now correlates CPU/RSS/process/I/O resource profiles and cleanup residue to
native startup run IDs, but that does not make the production startup report a
global process profiler.  P4 bounded launch concurrency and P5 foreground-first
readiness were intentionally not implemented.

Later Phase 0 testing exposed and fixed three additional serial correctness
defects before concurrency: legacy topology materialization could prune the cmd
root and let fallback placement overwrite sidebar identity; successful warm
reuse could toggle persisted runtime health from `restored` to `healthy`; and
identical project namespace state was rewritten.  Steady warm reuse now
preserves final restored provenance and skips identical namespace/runtime
content writes.  The current two-Agent smoke still executes `71` tmux backend
subprocesses per warm start, which remains a measured optimization target rather
than a correctness defect.

The 2026-07-17 source-only readiness/attribution smoke then measured a
`363.129 ms` warm wall, of which `94.664%` is now named.  Process bootstrap is
`243.986 ms`, dominated by `211.349 ms` from `ccb.py` entry through eager
imports.  Its no-attach T0-T6 shape is generation-correlated and monotonic, but
the cold T1 is deliberately classified as an observation upper bound rather
than the exact keeper checkpoint.  This is Phase 0 evidence, not acceptance of
P4 launch concurrency or P5 foreground-first behavior.

External source-runtime evidence used an isolated 5-window, 10-agent Codex-stub
project at
`/home/bfly/yunwei/test_ccb2/startup-perf-talk1-20260715`:

- cold daemon/namespace/provider start: `2.20s`
- 20 unchanged warm starts: `0.52s` to `0.64s`, p50 about `0.555s`,
  p95 `0.63s`
- all 10 agents attached with actual window ids `@0` through `@4`
- warm provider preparation count: `0`; relaunch count: `0`
- representative warm report: `flow_total=73.75ms`,
  `agent_runtime_commit=1.23ms`, `supervisor_total=252.30ms`

Focused regression finished with `322 passed`. The full Python suite reached
`5069 passed, 2 skipped` plus one first-attach restore regression; that condition
was narrowed to skip restore only for a pre-existing accepted binding, and the
failed black-box test plus the impacted startup matrix then passed.

## Incident Evidence

The inspected project uses an explicit multi-window layout:

- `main` is tmux window `@0` and contains `main` and `ccb_self`.
- `main2` is `@1` and contains `talk1`, `talk2`, and `mother`.
- `workers`, `reviewers`, and `ops` are `@2`, `@3`, and `@4`.
- Project state persists only one `workspace_window_id`, currently `@0`.

The startup binding path passes that single window id while also passing each
agent's declared window name. `ProjectNamespacePaneRecord.matches()` requires
both constraints to match. A healthy pane in `@1` through `@4` therefore fails
the global `@0` check and is treated as unusable. This explains the observed
shape where the entry-window agent is attached while other agents are
relaunched.

The health-assessment path already has the intended richer behavior: it accepts
a pane whose `@ccb_window` or tmux window name matches the configured logical
window before falling back to the legacy global workspace id. Startup and
health assessment currently disagree about pane identity.

The latest inspected startup report completed in about 7.6 seconds after an
intentional kill and therefore represents a cold/relaunch case, not the
reported warm-start failure. It does not invalidate the static warm-path bug.

## Root-Cause Chain

### 1. Multi-window identity is reduced to one entry-window id

Primary path:

- `lib/ccbd/start_flow_runtime/service.py`
- `lib/ccbd/start_preparation.py`
- `lib/ccbd/start_runtime/binding_runtime/common.py`
- `lib/ccbd/services/project_namespace_pane.py`

The first defect is correctness, not merely performance. A generation-local
tmux window id is being used as if it were the identity of every logical
window.

Target identity for an explicit topology:

```text
(project socket/session, namespace epoch, logical window name,
 slot key, role, managed_by)
```

The actual tmux `window_id` is a locator and diagnostic fact for the current
generation. It must not override a matching explicit logical window. For a
legacy layout with no logical window metadata, the entry `workspace_window_id`
remains the compatibility fallback.

### 2. Provider preparation occurs before reuse is known

`prepare_agents()` currently refreshes provider state for every configured
agent before deciding whether its existing runtime can be reused. A successful
warm attach therefore still pays projection and profile work that belongs only
to a launch.

On a relaunch, `start_agent_runtime()` invokes provider workspace preparation
again. The Codex path additionally materializes home configuration both during
profile refresh and during provider-home preparation. The effective upper
bound is three projection passes for one Codex relaunch and two for most other
providers.

The inspected inherited Codex plugin tree contains about 5,279 files and is
about 87 MB. Any fingerprint, completeness check, copy, or downstream CLI scan
multiplies sharply when repeated across many agents.

Required invariant:

- Reused runtime: zero mutating provider preparation passes.
- Launched or relaunched runtime: exactly one preparation pass.
- Shared inherited/plugin projection: one single-flight producer per source
  fingerprint, with per-agent projection limited to required local links or
  metadata.

### 3. Global discovery is repeated per agent

The current startup path repeats several whole-environment observations:

- tmux `list-panes -a` is called from topology checks, binding discovery, and
  active-pane collection.
- Codex live identity walks `/proc` to construct a process-parent map for each
  agent.
- Pane identity application emits many individual tmux commands even when the
  existing options already match.

With `N` agents, the undesirable shape is `N * global scan`. The target is one
tmux snapshot and one process snapshot per startup transaction, followed by
indexed in-memory lookups.

### 4. Durable state is rewritten when its meaning did not change

Agent specs, workspace bindings, provider profiles, runtime attach/restore
state, and health transitions can each trigger atomic write plus file and
directory `fsync`. Reused agents can also be marked `restored` merely because
startup revisited them.

This is especially expensive on WSL mounted drives and other slow metadata
filesystems. Durable stores must compare canonical content and skip no-op
writes. A reused active runtime should not execute restore bookkeeping or
toggle health solely to record an invocation.

### 5. The agent loop serializes bookkeeping and launch initiation

The per-agent loop is serial, but unbounded parallelism is not the first fix.
False relaunches and repeated preparation would only create concurrent I/O and
CPU contention. Concurrency is safe only after startup is split into explicit
classify, prepare, launch, and commit stages.

## Target Startup Pipeline

One startup transaction should execute these stages:

1. Load and validate project authority once.
2. Ensure the namespace and materialize the declared topology.
3. Capture one tmux pane snapshot and one process snapshot.
4. Classify every configured agent as `REUSE`, `LAUNCH`, `RELAUNCH`, or
   `DEGRADED`, including a machine-readable reason.
5. Immediately finalize reused agents without provider projection, restore
   churn, or redundant pane relabeling.
6. Prepare only the launch set, exactly once per agent, with shared projection
   work single-flighted.
7. Initiate tmux respawns in deterministic topology order; allow provider
   processes to initialize concurrently under provider-specific limits.
8. Commit runtime authority serially and deterministically.
9. Publish the startup report with stage and per-agent timing.

Shared mutable authority remains single-writer. Read-only discovery and
provider-local preparation may be parallel after their inputs are frozen.

## Implementation Phases

### P0: Measurement Contract

Add monotonic timing and counters before optimizing behavior.

Required startup-report fields:

- Total wall time and stage durations.
- Per-agent provider, logical window, outcome, and reject reason.
- Provider-preparation invocation count and projection scan file/byte counts.
- tmux command count, process snapshot count, and durable-write count.
- Time from command entry to namespace attachable and to all requested agents
  mounted.

Do not record commands, environment values, auth material, prompts, or other
secrets. Diagnostics contract changes must accompany report-schema changes.

Gate: the same workload can explain at least 90% of wall time through named
stages, and a second warm run reports why every agent was reused or relaunched.

### P1: Correct Multi-window Reuse

Align startup binding with health-assessment identity rules.

- For explicit layouts, match project/session, namespace epoch, logical window
  name, slot, role, and ownership marker.
- Do not require the entry `workspace_window_id` after the logical window has
  matched.
- Capture the actual pane `window_id` from the tmux snapshot for runtime facts.
- Retain global workspace-id validation only for legacy records without logical
  window metadata.
- Require an explicit reject reason for stale epoch, wrong project/session,
  wrong logical window, wrong slot/role, dead pane, or provider identity
  mismatch.

The startup supervision contract must be updated in the same patch. The
configuration contract already supports multiple explicit windows.

Gate: a second start of an unchanged five-window project yields 100%
`reuse_binding`, zero provider preparation, and zero relaunches.

### P2: Exactly-once Preparation And No-op Persistence

- Split cheap provider/profile resolution from mutating workspace preparation.
- Move mutating preparation after classification and execute it once only for
  `LAUNCH` and `RELAUNCH`.
- Remove the duplicate Codex home materialization within one preparation call.
- Skip writes when canonical AgentSpec, WorkspaceBinding, ProviderProfile, or
  RestoreState content is unchanged.
- Collapse launch attach and restore bookkeeping into one final runtime write.
- Do not call restore for a reused healthy runtime.

Gate: instrumentation proves preparation count `0` for reuse and `1` for each
launch; unchanged warm startup performs no authority writes except the final
startup diagnostic artifact when enabled.

### P3: Request-scoped Snapshots And tmux Batching

- Build one `NamespacePaneSnapshot` using a single formatted
  `tmux list-panes -a` call.
- Index by project/session, epoch, logical window, slot, role, pane id, and pid.
- Reuse the snapshot across topology checks, binding, active-pane discovery,
  and relabel decisions.
- Build one `/proc` process-parent snapshot and reuse it for all provider live
  identity checks.
- Skip pane relabel when inspected options already equal the desired identity.
- Batch pane option/style changes where tmux permits it.
- Invalidate snapshots only after a namespace mutation, pane respawn, reflow,
  or observed generation change.

Gate: one whole tmux topology scan and at most one process-tree scan per
startup, independent of agent count.

### P4: Bounded Launch Concurrency

- Freeze classification before concurrent work begins.
- Use a small I/O preparation pool, initially capped at `min(4, cpu_count)`.
- Single-flight shared Codex plugin/inherited-tree preparation by content
  fingerprint.
- Apply provider-specific launch limits and tune from measured CPU, memory,
  and auth/session contention.
- Keep topology mutation and runtime authority commit deterministic and
  serialized.
- Aggregate per-agent failures; never roll back by killing successfully reused
  agents.

Gate: cold all-agent startup is faster without increased failure rate,
provider-session crossover, peak-memory regression beyond the agreed bound, or
non-deterministic runtime records.

### P5: Optional Foreground-first Readiness

Only after P1 through P4 are stable, evaluate:

- Return foreground control after daemon, namespace, entry window, and
  requested agents are ready.
- Warm remaining configured agents in the background under a CPU budget.
- Expose `control_plane_ready`, `namespace_ready`, `requested_agents_ready`,
  and `fully_warm` as distinct states.

This changes visible startup semantics and requires a contract decision,
feature flag, clear UI state, and recovery tests. It is not needed to fix the
current warm-start defect and must not be bundled with P1.

## Performance Budgets

Initial budgets for a 15-agent explicit multi-window project on local Linux:

| Scenario | Initial target |
| --- | --- |
| Warm start, backend and all panes healthy | p50 <= 0.5 s, p95 <= 1.0 s |
| Daemon restart with live namespace/providers | p95 <= 2.0 s |
| Cold namespace attachable | p95 <= 2.0 s after P5 only |
| Cold all requested agents mounted | p95 <= 8.0 s |
| Supported slow filesystem | no unexplained run above 12 s |

P0 measurements may revise the numeric budgets, but not the structural gates:
warm reuse must not launch providers, global scans must be `O(1)` per startup,
and provider preparation must be at most once per launched agent.

Benchmark reports must include machine, filesystem, agent count, exact provider
and model identifiers, cold/warm definition, and p50/p95 over at least 20 runs.

## Verification Matrix

Topologies:

- Legacy single-window layout.
- Explicit one-window and five-window layouts.
- Window rename, reflow, namespace recreation, and epoch change.

Binding outcomes:

- All panes reusable.
- One dead pane among reusable peers.
- Foreign socket/session or project marker.
- Wrong logical window, slot, role, or provider identity.
- Mixed reuse and relaunch.

Scale and environment:

- 1, 8, 15, and 32 agents.
- Linux local filesystem, macOS, WSL ext4, and supported mounted-drive paths.
- Codex primary and Claude cross-provider real-provider acceptance; source-level
  fake/stub coverage for other adapters.

Faults:

- tmux query or respawn failure.
- Provider binary unavailable.
- Projection/fingerprint failure.
- Atomic state-write failure.
- Daemon generation change during startup.

Correctness assertions:

- No cross-project, cross-window, cross-slot, or cross-provider attachment.
- No duplicate provider process for a reused runtime.
- No partial authority record claims a failed launch is healthy.
- Pane recovery and `ccb kill` semantics remain unchanged.

Source-runtime validation must use `/home/bfly/yunwei/ccb_source/ccb_test` from
`/home/bfly/yunwei/test_ccb2` with isolated `HOME` and `CCB_SOURCE_HOME` unless
the test explicitly requires inherited real-provider configuration.

## Patch And Rollout Order

1. Instrumentation and reproducible benchmark harness.
2. Multi-window reuse correction, focused tests, and contract update.
3. Exactly-once preparation and no-op persistence.
4. Snapshot reuse and tmux batching.
5. Bounded launch concurrency behind a configurable limit.
6. Optional readiness split behind a separate feature gate.

Each patch must carry focused regression tests and before/after startup-report
evidence. Concurrency and readiness changes need independent rollback switches.
The identity correction should be the default behavior after compatibility
tests pass because retaining the false-relaunch behavior is itself incorrect.

## Residual Decisions

- Whether to persist a `managed_windows` name-to-id map in namespace state in
  P1 or derive it entirely from the request-scoped tmux snapshot.
- Final per-provider concurrency limits after P0 profiling.
- Whether P5 becomes a default policy or remains opt-in.
- Final slow-filesystem SLO after WSL and macOS evidence is collected.
