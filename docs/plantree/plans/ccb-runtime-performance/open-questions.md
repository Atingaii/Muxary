# Open Questions

Date: 2026-07-17

## Resolved

- Logical-window authority remains in config plus pane identity; generation
  window ids are derived from the request-scoped tmux snapshot and are not
  duplicated into a new `managed_windows` authority map.
- Startup running-intent and keeper transaction creation use one short project
  `startup.lock` transaction with a fresh lifecycle/lease read.  The lock is
  released before spawn/ping, and old success/failure finalizers are fenced by
  `startup_id + generation`; an already-running CLI intent is a no-op.
- Keeper now passes the exact `startup_id/generation` to the child.  Child
  claim/progress/mounted/cleanup and readiness identity are generation-fenced;
  all competing lifecycle/lease RMW writers use the shared lock with a fresh
  authority check, and timed-out spawned children are terminated and reaped.
- Question 7 is resolved without a new authority file: keeper samples the host
  performance counter immediately after durable `phase=starting`, carries it
  in the existing one-shot child fence, and the child consumes it into memory.
  The start handler upgrades T1 only after startup/generation/lease and
  timeline checks; raw absolute counters never enter reports.
- The former question 8 is resolved without a helper thread: bind/listen is
  transactional, an identifiable child self-client traverses the normal request
  worker, pre-existing clients are deferred within a bounded queue, ping remains
  available behind a runtime-bootstrap gate, and the current child publishes
  final `mounted/mounted` only after restoration and a fresh authority check.
  Keeper reconciliation treats recognized child startup stages as
  observation-only and cannot synthesize mounted from the interim lease.

## Open

1. What provider-specific concurrency caps satisfy cold-start speed without
   unacceptable CPU, memory, auth, or session contention?
2. After Linux, macOS, and WSL baselines exist, what p50/p95 budgets should
   replace the initial startup targets?
3. Should foreground-first/background-warm readiness remain opt-in or become
   the default after the unchanged eager-mount path meets its own SLO?
4. What are the target p50/p95 budgets for click-to-pane-focus and
   click-to-stable-sidebar-refresh?
5. Should high-throughput `ask` workloads use a persistent client/forwarder, or
   should the CLI remain process-per-call with lower-level batching only?
6. Before adding a daemon-owned startup scheduler, should the implementation
   restore the contract's single request/maintenance authority-write lane, or
   should the contract explicitly adopt the current two-thread model with a
   stronger shared commit/fencing boundary?
9. Can runtime restoration become bounded and recoverable so normal RPC
   readiness may move from final `mounted/mounted` to an explicit core-ready
   boundary, or must failed restoration continue to fail the whole generation?
