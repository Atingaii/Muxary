# Ideas Inbox

Date: 2026-05-25

## Promoted

- 2026-05-25: Redesign the public README for the v7 release line with new
  screenshots, demo videos, richer operation docs, and tmux onboarding for
  non-tmux users. Promoted to
  [readme-v7-redesign](../plans/readme-v7-redesign/README.md).
- 2026-06-10: Consider a generic external CCB maintenance heartbeat that
  periodically runs bounded agent-health diagnostics, checks configured-agent
  task and communication status, escalates risk, unknown, or unhealthy states
  to `ccb_self` by default, and exits immediately when the project is healthy
  and idle. The heartbeat must remain independent of provider context and must
  not make `ccb_self` a daemon lifecycle authority. Promoted to
  [ccb-maintenance-heartbeat](../plans/ccb-maintenance-heartbeat/README.md).

## Inbox

- 2026-07-16: Explore a bounded high-load concurrency path for CCB control-plane
  traffic after startup optimization is released and qualified. Current
  profiling of 80 `ask` submissions at concurrency 16 attributes about 62.3%
  of CPU to short-lived Python CLI processes and 30.6% to `ccbd`, while
  providers and tmux account for only a small remainder. Candidate work is to
  add p50/p95/p99 queue, RPC, and completion metrics; introduce an idempotent
  batch-submit API and a lightweight native/Rust `ask` client with Python
  fallback; bound socket framing/read concurrency and prioritize interactive
  traffic; replace completion polling with event hints plus a bounded
  read-only pool; and only then evaluate bounded provider-start concurrency.
  Preserve per-agent FIFO, single-writer mutation authority, and exact-once
  reply/cancel/chain terminalization behind feature flags. Promotion requires
  a frozen 80-task concurrency 1/4/16/32 provider matrix with zero loss,
  duplication, or session crossover, plus evidence targeting at least 80%
  lower client CPU and 40% lower total submit CPU without RPC expiry. Related
  evidence and constraints remain in
  [the shell/system split](../plans/ccb-runtime-performance/history/shell-system-bucket-split-2026-06-16.md)
  and
  [the low-latency plan](../plans/ccb-runtime-performance/topics/startup-and-runtime-low-latency-plan.md).
  Status: idea only; not committed to the roadmap.
