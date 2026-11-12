# Minimal Temporal Stability Plan

Date: 2026-07-06

## Context

The coworker consultation for this plan was interrupted by a provider API
disconnect before it produced usable conclusions. This note continues from the
source-backed analysis already recorded in:

- [ask-reply-temporal-stability.md](ask-reply-temporal-stability.md)
- [root-stability-architecture.md](root-stability-architecture.md)
- [accepted-turn-binding-and-pr238-239-review.md](accepted-turn-binding-and-pr238-239-review.md)

The goal is to avoid over-engineering while still fixing the actual timing
problem: replies must be attributed to the correct provider turn and caller, and
large provider sessions must not slow the normal path.

## Design Choice

Do not start with a large event-index subsystem, persistent tailer, or broad
provider rewrite.

Start with a smaller polling-first rule:

- use the existing provider polling path as the normal writer of provider turn
  evidence;
- persist compact evidence into existing completion items, runtime state, and
  completion snapshots;
- add clear barriers as dispatcher/provider-state facts;
- move expensive transcript search into recovery/diagnostics, not the normal
  ask reply path.

## Minimal Phases

### Phase 0: Failing Tests And Timing Probes

No behavior change.

Add tests and probes for:

- stale terminal event before current request anchor;
- clear after send but before anchor observation;
- clear while a job is already provider-accepted;
- session path rotate after send before anchor;
- reader offset rollback or file truncation;
- large session where current log size is unchanged across polls;
- large session where fallback search would otherwise scan multiple JSONL files;
- B -> C multi-round chain, then one final B -> A reply;
- wrong caller or missing caller reply attempt.

Acceptance:

- tests fail against current behavior where relevant;
- probes report normal-path poll count, fallback-scan count, bytes scanned, and
  terminal decision source.

### Phase 1: Separate Send From Provider Acceptance

Reuse existing structures:

- `delivery_state`
- `anchor_seen`
- `delivery_confirmed_at`
- `runtime_state`
- completion snapshots

Add only lightweight fields:

- `send_attempted_at`
- `provider_accepted_at`
- `provider_stream_id`
- `provider_epoch_id`
- `provider_source_cursor`

Rules:

- `accepted_at` remains backward-compatible daemon/job acceptance time.
- `provider_accepted_at` is the only provider acceptance evidence.
- a job cannot complete successfully until `provider_accepted_at` exists unless
  it is an explicit `no_wrap` provider path with a separate contract.

Acceptance:

- diagnostics can show "sent, waiting for provider acceptance";
- terminal completion before provider acceptance becomes incomplete/failed with
  evidence, never completed.

### Phase 2: `ccb_clear` Barrier

- `provider_epoch_barrier`
- `agent_name`
- `provider`
- `old_epoch_id`
- `new_epoch_id`
- `reason = ccb_clear`
- `created_at`

Simplest stable semantics:

- active jobs without `provider_accepted_at` become
  `incomplete(clear_before_provider_acceptance)`;
- active jobs with `provider_accepted_at` become
  `incomplete(clear_during_provider_turn)` unless terminal evidence was already
  durably recorded before the barrier;
- new jobs after clear use the new epoch;
- pre-clear events cannot complete post-clear jobs, and post-clear events cannot
  complete pre-clear jobs.

This is intentionally simpler than recoverable/unbound queue states. Operators
can explicitly retry after clear. The first fix should prefer a clear terminal
state over hidden recovery semantics.

Acceptance:

- clear never causes a stale reply to be delivered as success;
- no active job remains ambiguous across a clear barrier;
- tests prove old/new epoch terminal items are rejected.

Post-clear readiness is a separate concern. Use
[ccb-clear-epoch-probe-design.md](ccb-clear-epoch-probe-design.md) for the
short internal probe that binds the new epoch to fresh provider stream evidence
before real work resumes.

### Phase 3: Compact Evidence On Existing Polling Path

Extend existing polling ingestion so every accepted-turn fact emits compact
evidence:

- anchor observed;
- first assistant/progress observed;
- session rotate observed;
- terminal observed;
- source cursor and session path;
- epoch id.

Store this through existing completion item, runtime state, and completion
snapshot machinery. The normal finalization path should use this compact
evidence rather than rescanning provider transcripts.

Acceptance:

- once a job is provider-accepted, normal completion reads only incremental
  events/snapshots;
- large session size does not increase successful reply finalization time;
- fallback search count is zero on the normal happy path.

### Phase 4: Recovery-Only Fallback Search

Current fallback can scan same-workspace `**/*.jsonl` looking for an anchor.
Keep that capability, but move it out of the fast path:

- throttle it;
- run at most once per pending job per epoch unless explicit repair requests
  another scan;
- never silently adopt a new stream without epoch continuity proof;
- ambiguous matches produce diagnostics, not completion.

Acceptance:

- current-bound stream tailing is the default;
- fallback scan cannot complete a job by itself;
- WSL/mac large-session tests show bounded scan cost.

## When To Add A Persistent Tailer

Add a dedicated per-agent provider tailer only if benchmarks show the polling
path still misses latency targets after Phase 3 and Phase 4.

Promotion criteria:

- normal-path polling still performs repeated file discovery or large reads;
- WSL/mac file visibility delay causes frequent missed anchors even with clear
  barriers and recovery-only fallback;
- multiple active evidence consumers duplicate parsing work;
- measured p95 ask reply finalization latency remains above the target after
  compact evidence is stored through existing polling.

If promoted, the tailer should stay small:

- one per mounted provider-backed agent;
- reads only current stream from known cursor;
- writes compact evidence records only;
- does not mark jobs completed;
- does not deliver replies;
- does not store full provider transcript text;
- no provider-specific reply semantics outside adapter parsers.

## What Not To Do First

- Do not make Codex 900 second degraded terminalization the primary fix.
- Do not create a new global event-store abstraction before existing dispatcher
  events/snapshots are proven insufficient.
- Do not scan all provider logs on every poll.
- Do not classify pane text as successful completion.
- Do not keep active jobs alive across clear in a hidden recoverable state for
  the first implementation.
- Do not merge broad PR239-style branches wholesale for this problem.

## Expected Result

This minimal plan fixes correctness first and improves latency without a large
new subsystem:

- correctness comes from provider acceptance fields and clear barriers;
- speed comes from compact evidence on the existing polling path and
  recovery-only fallback;
- future persistent tailing remains a benchmark-backed optimization.
