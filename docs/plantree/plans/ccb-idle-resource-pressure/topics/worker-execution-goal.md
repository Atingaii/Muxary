# Worker Execution Goal

Date: 2026-06-23

## Goal Statement

Plan, land, and verify the remaining CCB idle resource pressure reductions in
small phases, while preserving ask stability and keeping every phase traceable
from plan-tree intent to code, tests, runtime validation, and rollback notes.

Workers must treat this plan as an execution contract, not only a design note.
Each phase must finish with a concrete working-tree diff, focused automated
tests, source runtime validation when behavior crosses the daemon/provider
boundary, updated plan-tree evidence, and a clear handoff for the next phase.

## Non-Negotiable Constraints

- Do not trade ask correctness for lower CPU, memory, or write pressure.
- Keep socket submit/get/ps/cancel handling hot even when maintenance work is
  paced down.
- Treat queued jobs, active jobs, callback edges, callback continuations, reply
  deliveries, cancellations, and resubmits as active work.
- Do not suspend or deep-idle a provider while dispatcher or message-bureau work
  can still target it.
- Keep durable authority on disk. Move only rebuildable runtime residue toward
  tmpfs.
- Default aggressive behavior behind explicit feature flags until runtime and
  ask stability are proven.
- Source runtime validation must use `/home/bfly/yunwei/ccb_source/ccb_test`
  from `/home/bfly/yunwei/test_ccb2`, not the installed `ccb` command.
- When source runtime validation needs provider/account isolation, run with
  `HOME=/home/bfly/yunwei/test_ccb2/source_home` and
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home` unless the test
  deliberately validates inherited provider configuration.

## Worker Operating Protocol

Before coding a phase:

- Read [../roadmap.md](../roadmap.md) and
  [idle-resource-pressure-solution.md](idle-resource-pressure-solution.md).
- Inventory the exact files and loops the phase will touch.
- Write down the phase's acceptance checks before implementation.
- Capture a small baseline when the phase targets write rate, RSS, idle mode, or
  wake latency.

While coding:

- Keep the diff scoped to one phase.
- Prefer no-op suppression and measurement before adding lifecycle states.
- Add observable counters or debug evidence when behavior becomes less frequent
  or less visible.
- Keep compatibility with existing startup, shutdown, `ccb kill`, `ccb -n`,
  callback continuation, and project restart semantics.

Before handing off:

- Run the phase's automated tests and report exact commands.
- Run source runtime validation from `/home/bfly/yunwei/test_ccb2` when daemon,
  provider, ask, callback, or runtime-root behavior changes.
- Update roadmap Done/In Progress/Next with concrete landed evidence.
- Record residual risks, skipped tests, and the next phase's starting point.
- Do not mark a phase complete if ask stability scenarios were not covered or
  explicitly deferred with a reason.

## Phase Plan

### Phase 1: Measurement And Ask-Stability Gate

Purpose:

- Establish counters and tests that make later reductions safe to evaluate.

Deliverables:

- Counters or diagnostics for runtime store writes, helper manifest writes,
  no-op JSON skips, heartbeat persists, provider RSS, provider idle age, socket
  request latency, wake latency, and callback continuation pending age.
- A reusable ask-stability test matrix covering plain ask, queued asks,
  `ask --chain`, `ask --silence`, cancel/resubmit, and first ask after idle.
- Plan-tree evidence showing the baseline measurement command and result shape.

Minimum tests:

- Unit tests for counter increments and idle/activity classification helpers.
- Integration or source-runtime tests proving callback continuation completes
  once and reply delivery does not loop before any pacing/suspend change lands.

Exit criteria:

- Later phases can fail fast when they regress ask routing, callback delivery,
  or write-pressure counters.

### Phase 2: No-Op JSON Write Suppression

Purpose:

- Reduce durable write churn without changing runtime state machines.

Deliverables:

- Content-equality skip for JSON store writes where safe.
- Helper manifest equality skip.
- Runtime timestamp debounce for fields that are diagnostic freshness only.
- Counters for skipped writes and persisted writes.

Minimum tests:

- Unit tests showing identical JSON payloads do not rewrite files or change
  mtimes.
- Unit tests showing material state changes still persist atomically.
- Regression tests for runtime/helper readers that depend on those files.

Exit criteria:

- A no-op idle heartbeat across mounted agents does not rewrite
  `runtime.json` or `helper.json` except at the configured max-persist window.

### Phase 3: Idle Heartbeat And Maintenance Pacing

Purpose:

- Reduce idle CPU and repeated control-plane writes while keeping socket and
  dispatcher responsiveness.

Deliverables:

- Explicit activity tracker for socket requests, job queues, active jobs,
  callback edges, reply deliveries, provider output movement, and health
  transitions.
- Active, warm-idle, and deep-idle maintenance modes.
- Immediate wake on submit, callback continuation, reply delivery, cancel,
  resubmit, repair, focus, or provider output.
- Feature flags or conservative defaults for pacing intervals.

Minimum tests:

- Unit tests for activity-to-mode transitions.
- Tests proving queued work and callback/reply-delivery work block deep-idle
  dispatcher throttling.
- Source runtime validation for first ask after warm-idle/deep-idle.

Exit criteria:

- Idle loop work decreases measurably, while ask submit and callback
  continuation still complete without manual intervention.

### Phase 4: Runtime Tmpfs Split

Purpose:

- Move rebuildable runtime residue off durable project storage without moving
  auth, config, session authority, or evidence needed for recovery.

Deliverables:

- Runtime-state root resolver with `/run/user/$UID/ccb`, `/dev/shm/ccb-$USER`,
  and project `.ccb` fallback.
- A project `.ccb` ref file or diagnostic path that keeps runtime-root
  discoverable.
- Migration/fallback behavior when tmpfs is unavailable or stale refs exist.

Minimum tests:

- Unit tests for resolver fallback order and stale runtime-root handling.
- Integration/source-runtime test for startup, project restart, `ccb kill`, and
  provider recovery with runtime residue in tmpfs.
- Storage classification tests proving durable auth/session/config stay on disk.

Exit criteria:

- Rebuildable runtime files can live in tmpfs without breaking restart,
  diagnostics, or cleanup.

### Phase 5: Opt-In Provider Suspend/Resume

Purpose:

- Reduce memory and CPU from mounted but unused providers after lower-risk write
  reductions are proven.

Deliverables:

- Opt-in Codex suspend policy.
- Provider states for idle, suspended, waking, and busy.
- Suspend blockers for active jobs, queued jobs, callback edges, reply
  deliveries, wake/recovery attempts, and unstable health.
- Wake path on ask/focus that keeps accepted jobs in dispatcher authority until
  provider transport is actionable.

Minimum tests:

- Unit tests for suspend eligibility and blockers.
- Source runtime validation for first ask after suspend.
- Callback chain test across suspend boundary:
  `A -> B -> C -> B -> A` completes once.
- Cancel/resubmit while provider is idle or waking.

Exit criteria:

- Opt-in Codex suspend materially reduces RSS and does not drop, reorder, or
  loop asks.

### Phase 6: Provider-State Retention And Cleanup

Purpose:

- Reduce accumulated disk footprint without deleting authority or active
  sessions.

Deliverables:

- Dry-run storage report before destructive cleanup.
- WAL checkpoint/truncate for stopped or suspended providers where safe.
- Retention policy for old session JSONL, caches, and rebuildable bundles.
- Explicit never-delete rules for auth, active session authority, and current
  config projections.

Minimum tests:

- Unit tests for storage classification and dry-run output.
- Tests proving active session/auth paths are excluded.
- Manual dry-run on a populated external test project before any cleanup write.

Exit criteria:

- Operators can see what would be removed or compacted before any destructive
  action, and default cleanup cannot delete active authority.

## Required Handoff Format

Every worker should end with:

- Phase completed or phase still in progress.
- Files changed.
- Tests run, with exact commands.
- Source runtime validation command and result, or why it was not required.
- Measured before/after evidence when the phase targets writes, CPU, memory, or
  disk footprint.
- Ask-stability scenarios covered.
- Known risks and the next worker's first concrete task.

## Reusable Worker Prompt

Use this prompt when delegating a phase:

```text
Goal: Execute the next phase of docs/plantree/plans/ccb-idle-resource-pressure,
following topics/worker-execution-goal.md as the authority for scope,
landing discipline, and tests.

Read first:
- docs/plantree/plans/ccb-idle-resource-pressure/README.md
- docs/plantree/plans/ccb-idle-resource-pressure/roadmap.md
- docs/plantree/plans/ccb-idle-resource-pressure/topics/idle-resource-pressure-solution.md
- docs/plantree/plans/ccb-idle-resource-pressure/topics/worker-execution-goal.md

Deliver:
- A scoped implementation for the assigned phase only.
- Focused automated tests.
- Source runtime validation from /home/bfly/yunwei/test_ccb2 with
  /home/bfly/yunwei/ccb_source/ccb_test when daemon/provider/ask behavior
  changes.
- Plan-tree updates recording landed evidence, remaining risks, and next steps.

Constraints:
- Do not use installed/global ccb for source validation.
- Do not break ask submit, queueing, callback continuation, reply delivery,
  cancellation, resubmit, project restart, ccb -n, or ccb kill.
- Keep aggressive idle/suspend behavior feature-flagged until proven.
- Preserve durable auth, config, session authority, and diagnostic recovery
  evidence.
```
