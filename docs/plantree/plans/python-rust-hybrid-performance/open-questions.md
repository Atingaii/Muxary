# Open Questions

Date: 2026-06-16

1. Which hot path is currently worst in real user projects: ProjectView refresh,
   storage doctor, queue/watch tailing, provider completion polling, or startup?
   For Phase 2 only, `coworker` accepted JSONL tail/query as a narrow first
   helper slice; this broader real-project ranking remains open for later
   default-enablement decisions.

2. Should helper binaries stay as independent crates under the existing
   `tools/` tree, or move to a repo-level Cargo workspace such as `rust/` or
   `crates/` after more helper slices land?

3. Which exact timeout values should each helper use after Phase 0 measures
   subprocess startup and hot-path durations? Current contract: optional
   `1|auto` modes must fallback to Python and emit one structured diagnostic
   breadcrumb; `required` modes must raise instead of falling back.

4. Which benchmark threshold is strong enough for default enablement: 20% p95
   latency reduction, 2x speedup on large logs, or a user-visible UI threshold
   such as ProjectView under 50 ms?

5. Should `CCB_RUST_HELPERS=auto` and `CCB_RUST_HELPERS=1` have distinct
   diagnostic behavior once a production caller is wired? Current Phase 1/2
   behavior can treat both as "attempt helper and fallback on failure".

6. Should helper capability cache expose diagnostics or explicit invalidation
   controls after default-enabled helper paths are selected? Current
   implementation caches successful probes by helper path, mtime, and size.

7. Which helper paths should become default-enabled first now that release
   packaging is present and required-mode fallback removal is verified?
   Native output and storage inventory are now default-auto. Storage compact
   summary has positive synthetic evidence but remains opt-in pending review
   and broader fixture coverage. ProjectView recent jobs moved back to
   non-default after adaptive budgets made the Python path faster than the
   subprocess helper. ProjectView/tmux parser and full JobRecord strict JSONL
   should remain non-default until their current negative benchmarks are
   resolved.

8. Which delta cursor should the new job fetch design use after the recent-list
   contract lands: line number plus file size/mtime, byte offset, or a small
   per-agent index file? The recent-list direction is now captured in
   `topics/job-fetch-design.md`; cursor shape remains open.
