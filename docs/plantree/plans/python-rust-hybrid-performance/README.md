# Python Rust Hybrid Performance Plan

Date: 2026-06-15

## Purpose

This plan defines a performance-oriented Python + Rust hybrid path for CCB.
It does not propose a full Rust rewrite. The goal is to keep the Python
control plane and provider iteration speed while moving bounded hot paths into
Rust where the payoff is measurable and rollback is simple.

## Scope

In scope:

- Rust helper binaries for JSONL tailing, storage scans, tmux/project-view
  collection, process-tree cleanup, and provider output parsing.
- A stable JSON/JSONL command contract between Python and Rust helpers.
- Feature-flagged fallback to the existing Python implementation for every
  replaced path.
- Benchmarks and regression gates that prove latency, CPU, memory, or startup
  improvement before enabling a helper by default.

Out of scope for the first phase:

- Rewriting `ccbd` itself in Rust.
- Replacing provider-specific semantics or completion decisions wholesale.
- Replacing the Python config/rolepack/provider authoring surface.
- Removing Python runtime packaging before helper adoption is proven.

## Evidence

- CCB currently enters through a Python launcher and Python `lib/cli` /
  `ccbd` runtime.
- The codebase already ships a Rust sidebar helper under
  `tools/ccb-agent-sidebar/`, so Rust toolchain and release packaging exist.
- Current performance-sensitive areas include ProjectView/sidebar refresh,
  JSONL tail/read paths, storage classification scans, tmux pane inspection,
  provider output parsing, and process cleanup.
- Existing metrics already expose ProjectView latency and tmux/store scan
  counters, which are suitable baseline probes.

## Reading Path

1. [roadmap.md](roadmap.md)
2. [implementation-status.md](implementation-status.md)
3. [topics/low-risk-execution-plan.md](topics/low-risk-execution-plan.md)
4. [topics/performance-replacement-map.md](topics/performance-replacement-map.md)
5. [topics/sequential-optimization-gates.md](topics/sequential-optimization-gates.md)
6. [topics/job-fetch-design.md](topics/job-fetch-design.md)
7. [open-questions.md](open-questions.md)

## Recommended Direction

Prefer Rust helper binaries first, not PyO3 as the first step.

Reason:

- Helper binaries keep Python packaging simple and isolate crashes.
- JSON input/output contracts are easy to test as golden files.
- The release artifact already handles Rust sidebar binaries.
- PyO3 can be considered later only for hot loops where subprocess startup
  cost dominates.

## Success Criteria

- Each Rust helper has a Python fallback and an explicit feature flag.
- Existing tests stay green with helpers disabled.
- Helper-enabled tests cover Linux and macOS.
- Worker execution starts from benchmark/contracts only, not from replacing
  behavior in the first patch.
- At least one measured hot path improves materially before default enablement:
  - ProjectView p95 latency,
  - queue/watch JSONL tail latency,
  - storage doctor scan duration,
  - provider completion parsing latency,
  - shutdown/process cleanup duration.
