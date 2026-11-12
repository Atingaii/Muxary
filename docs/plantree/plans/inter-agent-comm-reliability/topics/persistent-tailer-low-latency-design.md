# Persistent Tailer Low-Latency Design

Date: 2026-07-06

Status: candidate optimization; deferred from first implementation slice after
coworker review on 2026-07-06.

## Purpose

Make low-latency ask reply detection a first-class part of the temporal
stability design.

This topic records the tailer-first option. After review, it is not the first
implementation path. The immediate plan keeps provider ingestion in the existing
polling/completion item path and adds epoch/acceptance/clear enforcement first.

The candidate tailer rule remains:

Each mounted provider-backed agent gets one lightweight tailer. The tailer keeps
the current provider stream cursor warm and writes compact CCB-owned evidence.
Completion and reply delivery consume that CCB evidence instead of rescanning
large provider session files.

## Review Outcome

Coworker review `job_b5689ffafbf1` classified tailer-first as overdesigned for
the first slice.

Accepted concerns:

- existing polling already incrementally reads provider streams from a cursor;
- a persistent tailer adds a long-lived runtime component and supervisor surface;
- integrating tailer output with dispatcher/completion risks duplicate ingestion
  or ack-path drift;
- the correctness bug can be fixed first with provider acceptance fields, epoch
  enforcement, clear barrier, terminal predicates, and recovery-only fallback.

Tailer should be promoted only after benchmarks show the existing polling path
still misses latency targets once broad fallback scans are removed from the
normal path.

## Why Tailer First

Tailer-first is simpler because there is one provider-session ingestion path:

- provider adapters parse raw provider streams;
- tailer writes compact facts;
- dispatcher/completion consumes compact facts;
- recovery scans remain explicit diagnostics.

Without a tailer, provider polling must both drive job finalization and extract
evidence. If a tailer is later added, the system must reconcile two ingestion
paths. That increases risk around duplicate terminal events, stale cursors, and
provider-specific drift.

Tailer-first also matches the latency goal:

- the current stream and cursor stay warm between asks;
- large provider sessions are never normal completion input;
- `ccb_clear` probe evidence is recorded before the next real task;
- WSL/mac file visibility delay becomes delayed evidence arrival, not repeated
  broad scanning.

## What The Tailer Is Not

The tailer is not another provider session.

It must not store full prompt text, full assistant replies, tool output, or raw
transcript bodies as the normal record. It stores small CCB control-plane facts.

Provider raw sessions remain the full source of truth for forensic recovery.
Tailer evidence is the CCB coordination index.

## Evidence Shape

Each tailer writes append-only compact events such as:

```text
event_kind = epoch_started | stream_bound | anchor_seen | progress_seen |
             terminal_seen | session_rotated | stream_gap | parse_error
agent_name
provider
provider_generation_id
provider_epoch_id
provider_stream_id
source_cursor
job_id
request_anchor
observed_at
status
reply_hash
reply_preview
reply_artifact_id
diagnostics
```

Size rules:

- no full transcript text;
- small bounded preview only;
- large reply text goes to an artifact, referenced by id/path/hash;
- per-event size limit should be enforced;
- old evidence can be compacted or rotated after retention windows.

## Lifecycle

Tailer lifecycle follows mounted agent lifecycle, not ask job lifecycle.

- agent mounted or started: start one tailer for that agent/provider runtime.
- ask job starts: job consumes current tailer evidence/cursor; tailer continues.
- ask job ends: clear active job state; keep tailer running.
- `ccb_clear`: keep or restart the tailer as needed, but always advance epoch,
  rebind stream/cursor, and write probe evidence in the new epoch.
- agent restart: stop old tailer; start new tailer with new
  `provider_generation_id`.
- config reload removes agent or project kill: stop tailer and clean runtime pid,
  lease, and cursor locks.
- tailer degraded: supervisor marks `tailer_degraded` and restarts or reports
  explicit diagnostics; it must not silently fall back to broad completion scans.

Evidence retention is separate from tailer lifecycle:

- runtime pid/lease/locks are cleaned dynamically;
- compact evidence is retained by policy, rotated or compressed, not deleted just
  because an ask ended.

## Runtime Boundary

The tailer produces facts. It does not decide job completion.

Tailer can emit:

- request anchor observed;
- first progress observed;
- terminal-looking provider event observed;
- stream rotate/truncate/offset rollback;
- provider hook event observed;
- parse error or stream gap.

Tailer must not:

- mark a job completed;
- deliver a reply to a caller;
- infer caller lineage;
- resolve ambiguous terminal events as success;
- retry user work.

The dispatcher/state machine owns:

- provider acceptance state;
- epoch barrier effects;
- terminal predicates;
- mailbox lineage;
- final reply delivery.

## Provider Adapter Boundary

Provider adapters are narrow parsers:

- Codex adapter reads current JSONL stream and emits anchor/progress/terminal
  facts with cursor.
- Claude adapter reads transcript/session events and hook artifacts, then emits
  the same compact facts.
- Future providers map their native session surface into the same evidence
  vocabulary.

Provider-specific differences stay below the tailer evidence contract.

## Low-Latency Path

Normal successful ask flow:

1. dispatcher submits ask and records request anchor;
2. provider runtime sends prompt;
3. tailer observes anchor in current stream and writes `anchor_seen`;
4. state machine marks `provider_accepted_at`;
5. tailer observes progress/terminal and writes compact evidence;
6. state machine applies terminal predicate;
7. reply delivery uses mailbox lineage and compact terminal evidence.

No step needs broad provider-session scanning on the normal path.

## `ccb_clear` Path

`ccb_clear` uses the same tailer substrate:

1. clear advances `provider_epoch_id`;
2. active jobs are resolved according to pre-clear acceptance state;
3. tailer writes `epoch_started` and `stream_bound` for the new epoch;
4. post-clear probe produces `anchor_seen` and exact ready reply evidence;
5. real work resumes only after new epoch readiness is proven or explicitly
   degraded.

## Recovery Path

Recovery may still inspect raw provider sessions:

- missing evidence;
- tailer degraded;
- ambiguous stream rotation;
- operator `repair` or diagnostics;
- old job reconstruction.

Recovery scans are bounded and diagnostic. They do not silently complete jobs
without same-epoch accepted-turn evidence.

## Acceptance Criteria

- one active tailer per mounted provider-backed agent;
- no tailer per ask job;
- ask completion reads compact evidence first;
- provider raw-session scan count is zero on normal successful replies;
- `ccb_clear` probe evidence is written in the new epoch before real work
  resumes;
- tailer evidence remains small and bounded, with large replies stored as
  artifacts;
- tailer failure is visible as `tailer_degraded`, not hidden by broad fallback.

## Decision

Keep persistent lightweight per-agent tailer as the primary candidate if
polling-based compact evidence is still too slow after the correctness slice.

The tailer is a mounted-agent runtime companion, not a job-scoped process and
not a second provider session. It converts provider-specific raw streams into
small CCB-owned evidence so the temporal state machine can be both stable and
fast, but it should not be introduced before measurement justifies the extra
runtime surface.
