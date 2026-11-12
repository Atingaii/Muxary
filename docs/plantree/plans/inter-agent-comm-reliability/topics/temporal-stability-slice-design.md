# Temporal Stability Slice Design

Date: 2026-07-06

Status: design continuation; implementation pending.

## Purpose

Continue the ask reply temporal-stability design after the `ccb_clear` workflow
has been settled.

The target is a small implementation sequence that makes reply completion
monotonic while avoiding a new long-lived tailer service in the first slice.

## Inputs

- [ask-reply-temporal-stability.md](ask-reply-temporal-stability.md)
- [minimal-temporal-stability-plan.md](minimal-temporal-stability-plan.md)
- [ccb-clear-epoch-probe-design.md](ccb-clear-epoch-probe-design.md)
- [coworker-review-20260706-temporal-stability.md](coworker-review-20260706-temporal-stability.md)
- [persistent-tailer-low-latency-design.md](persistent-tailer-low-latency-design.md)
- [clear-after-logic-codex-claude.md](clear-after-logic-codex-claude.md)

## Core Invariants

1. A job is not provider-accepted until its request anchor is observed in the
   current provider epoch.
2. A terminal provider item can complete a job only if it belongs to the same
   provider epoch that accepted that job.
3. `ccb_clear` advances the target agent's provider epoch before post-clear
   evidence can complete work.
4. A post-clear probe can make a new epoch ready, but it cannot complete or
   resume a user task by itself.
5. Large provider sessions are raw evidence and diagnostics; normal reply
   completion should use compact evidence from the existing provider
   polling/completion item path.
6. A final reply to a caller requires both correct provider-terminal evidence and
   correct mailbox lineage.

## Slice 0: Failing Tests And Probes

No behavior change.

Add focused tests that document the current unstable cases:

- terminal item appears before current request anchor;
- clear after prompt send but before provider anchor observation;
- clear after provider acceptance but before terminal answer;
- session path/session id changes while a job is pending;
- reader offset rollback or file truncation;
- large provider session where fallback search would scan broad history;
- B calls C more than once, then B replies once to A;
- reply attempt has wrong caller, missing caller, or stale caller lineage.

Add timing probes around:

- prompt send time;
- anchor observed time;
- provider terminal item time;
- reply delivery time;
- fallback scan count;
- bytes or files scanned on fallback paths.

Acceptance:

- tests fail or expose weak assertions on the current behavior where applicable;
- probes can distinguish normal incremental completion from recovery scanning;
- no production behavior changes are required in this slice.

## Slice 1: Provider Acceptance Fields

Keep existing structures and names where possible, but stop overloading
`accepted_at`.

Add or normalize fields on provider submissions / runtime state:

```text
send_attempted_at
provider_accept_pending_at
provider_accepted_at
provider_generation_id
provider_epoch_id
provider_stream_id
provider_source_cursor
request_anchor
```

Rules:

- `accepted_at` remains daemon/job acceptance time for compatibility.
- `provider_accepted_at` is written only when the current request anchor is
  observed in the current epoch.
- `provider_epoch_id` is copied into terminal completion decisions.
- terminal completed before `provider_accepted_at` is rejected or normalized to
  explicit incomplete/failed.

Acceptance:

- diagnostics can show `sent`, `waiting_for_provider_acceptance`, and
  `provider_accepted` separately;
- terminal item before anchor cannot become completed;
- existing happy-path behavior remains unchanged except for added diagnostics.

## Slice 2: `ccb_clear` Epoch Barrier

Implement the `ccb_clear` workflow contract:

- `ccb_clear` clears current agent;
- `ccb_clear <agent>` clears named agent;
- `ccb_clear all` explicitly clears all mounted agents in the current project.

On each target agent:

1. record the pre-clear epoch and active-job acceptance state;
2. create a new `provider_epoch_id`;
3. resolve active jobs:
   - no provider acceptance ->
     `incomplete(clear_before_provider_acceptance)`;
   - provider accepted, no terminal evidence before barrier ->
     `incomplete(clear_during_provider_turn)`;
4. submit provider-native clear to the target pane;
5. run the post-clear probe;
6. mark the new epoch ready only after probe success or explicit degraded
   diagnostics.

Acceptance:

- bare `ccb_clear` never clears all agents;
- `ccb_clear all` is the only bulk form;
- active jobs never stay ambiguous across the barrier;
- post-clear terminal events cannot complete pre-clear jobs.

## Slice 3: Compact Evidence On Existing Polling Path

Do not add a dedicated tailer in the first slice. Existing provider polling is
already the incremental reader from the current provider stream cursor.

Extend that path so each accepted-turn fact carries compact CCB-owned evidence:

```text
event_kind = anchor_seen | progress_seen | session_rotated | terminal_seen
agent_name
job_id
request_anchor
provider_epoch_id
provider_stream_id
source_cursor
observed_at
reply_preview_or_hash
diagnostics
```

The raw provider transcript remains the source for parser input and recovery,
but dispatcher/completion finalization should rely on completion items and
snapshots that are already attributed to a job and epoch.

Acceptance:

- happy-path completion does not rescan large provider sessions;
- fallback scan count is zero for normal Codex/Claude successful replies;
- compact evidence contains enough detail for diagnostics and replay.

## Slice 4: Terminal Predicate And Reply Lineage

Centralize terminal acceptance rules:

Completed reply requires:

- same `provider_epoch_id` as the job's `provider_accepted` epoch;
- same `request_anchor`;
- non-empty reply for providers where empty terminal output is not a valid
  answer;
- terminal status from a trusted provider parser/hook path;
- mailbox lineage that identifies the intended caller.

Reject or normalize:

- terminal item from stale epoch;
- terminal item before anchor;
- empty provider terminal marked completed;
- reply delivery without parent/child lineage;
- ambiguous caller identity.

Acceptance:

- B -> C multi-round chain can converge and B replies once to A;
- wrong caller or missing caller becomes explicit incomplete/failed;
- duplicate or late terminal evidence does not cause duplicate replies.

## Slice 5: Recovery-Only Fallback

Keep expensive scanning, but remove it from the normal completion path.

Fallback rules:

- throttle fallback per job/epoch;
- never silently adopt a new stream without continuity proof;
- ambiguous anchor matches are diagnostics only;
- recovery results can suggest retry/resubmit/clear, but do not create completed
  replies by themselves.

Acceptance:

- WSL/mac large-session tests show bounded normal-path work;
- fallback diagnostics include files scanned and reason for non-adoption;
- recovery can still help operators find evidence after a failed job.

## Data Ownership

Provider adapters own parsing details:

- how to find current stream id/path;
- how to detect request anchor;
- how to parse progress/terminal/hook events;
- how to report session rotate/truncate/offset rollback.

CCB owns semantics:

- epoch creation;
- job acceptance state;
- terminal predicates;
- reply lineage;
- clear/probe workflow;
- diagnostics exposed to users.

## Implementation Readiness

The first code slice is ready only after:

- tests from Slice 0 are enumerated with target files;
- the storage location or existing snapshot/event surface for compact evidence is
  selected;
- the minimal field names are confirmed against current provider submission
  structures;
- Codex and Claude happy paths have provider-specific expectations listed;
- `ccb_clear` skill/workflow routing is specified without a second user-facing
  clear command.

## Decision

Proceed with temporal stability as an incremental state-machine hardening:

1. tests and probes;
2. provider acceptance fields;
3. `ccb_clear` epoch barrier and post-clear probe;
4. compact evidence on the existing polling path;
5. terminal predicate and reply lineage;
6. recovery-only fallback search.

Do not start with broad timeout fallback, persistent tailer, or wholesale
provider rewrite. Tailer remains a benchmark-backed optimization candidate.
