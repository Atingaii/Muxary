# Startup And Runtime Low-Latency Plan

Date: 2026-06-16

## Goal

Reduce startup CPU/wall time, high-load CPU, and interactive click latency
without changing provider semantics or weakening CCB daemon ownership rules.

## Priority Order

1. Attribute and reduce shell/tmux/subprocess overhead.
2. Reduce provider startup and idle cost through lifecycle policy.
3. Isolate interactive pane switching from background status refresh.
4. Continue Rust/helper optimization only for measured CCB-local hot paths.

## Startup Optimization

Current evidence: startup CPU is dominated by `shell-system` at 56.0%, followed
by provider processes at 24.1%, while CCB core is 16.5%.

High-ROI candidates:

- Lazy provider mount for non-foreground providers. Mount the foreground or
  requested provider first; defer inactive providers until first use or a
  background warmup budget.
- Stagger provider startup. Avoid simultaneous CLI/session initialization when
  multiple mounted providers create peak CPU and terminal contention.
- Cache startup authority reads. Keep config/layout/agent topology parsing
  cached per daemon generation where the authority files are unchanged.
- Replace repeated shell wrappers with direct exec where possible. Eliminate
  avoidable `sh -lc` layers in startup paths that do not need shell expansion.
- Batch tmux setup. Prefer fewer tmux commands with explicit layout/pane
  batches over many command invocations.
- Separate readiness from full warm state. Make the UI usable as soon as the
  daemon, foreground pane, and configured authority are ready; complete
  non-critical provider/status work asynchronously.

Acceptance gates:

- Startup ready wall time p50/p95 by provider set.
- Startup cumulative CPU split by CCB core, provider, tmux, shell wrappers, and
  terminal frontend.
- No regression in mounted-agent readiness semantics.
- No daemon generation drift or nested project bootstrap regression.

## High-Load Runtime Optimization

Current evidence: high-load CPU is dominated by `shell-system` at 72.6%, while
CCB core is 17.3% and provider is 9.3% in the Codex-targeted test.

High-ROI candidates:

- Persistent ask client path. Reduce per-ask process startup by using a daemon
  socket client or a small persistent local forwarder for high-throughput ask
  workloads.
- Queue batching and coalescing. Combine repeated status/project-view reads
  during bursts, and collapse redundant refreshes into the latest requested
  state.
- Event-driven update paths. Prefer file/socket/tmux event signals over fixed
  polling where provider and daemon state already have durable markers.
- Backpressure on UI/status refresh. Under ask bursts, preserve request
  delivery first and degrade non-critical live status refresh cadence.
- Keep Rust helpers for bounded hot loops. `native.output.observe` and
  `storage.scan.inventory` are useful when those paths are on the request
  path, but they are not a replacement for reducing process orchestration
  overhead.

Acceptance gates:

- 80-task / 12-concurrency ask profile with CPU attribution.
- Mixed-provider profile matrix rather than Codex-only pressure.
- Queue latency p50/p95, delivery success, and reply detection reliability.
- No lost ask messages, duplicate job completion, or provider-session boundary
  regression.

## Interactive Pane And Click Latency

Click latency should be measured separately from background CPU. The target
path is input event to visible pane focus or stable sidebar/project-view state.

High-ROI candidates:

- Optimistic focus path. Pane focus should execute immediately from cached pane
  identity and should not wait for full ProjectView/status refresh.
- Async refresh after focus. Trigger status/sidebar refresh after the focus
  command returns; stale-but-reasonable display is better than blocking input.
- Debounce sidebar/project-view rebuilds. During rapid clicks or ask bursts,
  coalesce redraws and skip intermediate states.
- Cache tmux pane layout facts with generation/version invalidation. Avoid
  recapturing pane metadata on every interaction when the layout has not
  changed.
- Instrument click-to-focus and click-to-stable separately. This avoids hiding
  fast focus behind slower background refresh.

Acceptance gates:

- Click-to-focus p50/p95 under idle, startup-warm, and high-load conditions.
- Click-to-stable-sidebar p50/p95 separately.
- No stale focus target after pane death/recovery.
- No overlap with provider completion detection or pane recovery authority.

## Provider Lifecycle Policy Options

Options to evaluate:

- Eager mount all configured providers: lowest first-use latency, highest
  startup and idle cost.
- Lazy mount inactive providers: lower startup and idle cost, first-use delay.
- Staggered warmup: usable foreground quickly, background providers warm in a
  CPU budget.
- Idle hibernation: reduce long-lived provider CPU/memory but needs robust
  resume semantics and user-visible state.

Preferred first experiment: foreground-first plus staggered warmup, because it
preserves low first-screen latency without committing to full provider
hibernation semantics.

## When To Optimize CCB Core Further

Reopen broad CCB-core optimization only when a refined profile shows one of:

- CCB core stays above 25% of sampled CPU after shell/tmux/provider policy
  reductions.
- A specific CCB-local path appears in click-to-focus or ask latency p95.
- Rust helper evidence overlaps with a lifecycle hot path, not only a
  microbenchmark.
