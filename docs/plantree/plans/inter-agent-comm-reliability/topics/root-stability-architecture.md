# Root Stability Architecture

Date: 2026-07-06

## Position

The root direction is accepted-turn ownership, not more degraded fallback.

PR238-style reason splitting and PR239-style no-reply taxonomy are useful only
after CCB has already decided that a job cannot be completed with current-turn
evidence. They improve operator clarity, but they do not prove that a provider
accepted the current ask, that the observed transcript belongs to the current
epoch, or that a reply reached the intended caller.

The primary stability goal is therefore:

- do not complete from stale provider events;
- do not call a paste/send operation "accepted";
- do not let clear/session rotation mix old and new evidence;
- do not route replies without durable lineage and caller identity;
- do not turn unknown state into success.

## Existing Hooks To Reuse

Current code already has partial support for the right shape:

- Codex active start writes `delivery_state = pending_anchor` unless `no_wrap`
  is requested.
- Codex polling sets `delivery_state = accepted` when the request anchor is
  later observed in provider events.
- Runtime state already tracks `request_anchor`, `anchor_seen`,
  `bound_turn_id`, `bound_task_id`, `session_path`, `reply_buffer`, and
  assistant-message fields.
- Polling already emits `SESSION_ROTATE` items when the session path changes.
- Completion detectors already know whether an anchor has been observed.

Important gaps:

- `accepted_at` is currently set at active submission creation time, before
  provider anchor evidence exists. That timestamp means "daemon accepted the
  job / prompt send started", not "provider accepted the turn".
- `project clear` only sends `/clear` to the pane. It does not record a
  provider evidence epoch, and it does not wait for a provider-side clear
  acknowledgement.
- A readable provider session file is treated as evidence source, but the
  current code does not have a first-class epoch object that separates pre-clear
  and post-clear observations.
- Reply delivery can prove mailbox persistence, but it does not yet prove
  recipient-side accepted-turn evidence for the continuation prompt.

## Core Model

### Provider Evidence Epoch

An epoch is the unit of trust for provider transcript evidence.

Minimum fields:

- `agent_name`
- `provider`
- `epoch_id`
- `started_at`
- `start_reason`: `launch`, `ccb_clear`, `manual_clear_observed`,
  `session_rotate`, `session_truncate`, `offset_rollback`, `unknown_rebind`
- `session_path`
- `session_id` when available
- `reader_cursor` or last observed source cursor
- `prior_epoch_id` when replacing a known epoch

Epoch change rules:

- CCB-controlled clear starts a new epoch immediately after the clear command is
  submitted.
- Session path or session id change starts a new epoch.
- Reader offset rollback, file truncation, or cursor invalidation starts a new
  epoch.
- Manual provider clear is harder: first version may detect it as a session
  rotate/truncate/anchor discontinuity and mark `manual_clear_observed`.

Completion rule:

- A job can only complete from events in the epoch where its request anchor was
  observed.

### Accepted Turn Evidence

Accepted turn evidence binds an ask job to a provider turn.

Minimum fields:

- `job_id`
- `message_id` when available
- `target_agent`
- `request_anchor`
- `epoch_id`
- `session_path`
- `bound_turn_id`
- `bound_task_id`
- `anchor_seen_at`
- `first_assistant_at`
- `terminal_seen_at`
- `terminal_reason`
- `source_cursor`

State distinction:

- `submitted`: CCB created the job.
- `send_attempted`: prompt was sent to the pane or provider transport.
- `provider_accepted`: current request anchor was observed in the current epoch.
- `running`: accepted and non-terminal assistant/provider progress has appeared.
- `terminal`: completed/failed/incomplete with current-turn evidence.
- `unbound_incomplete`: timeout, clear, restart, or epoch mismatch occurred
  before provider acceptance was proven.

The existing `delivery_state` can be the migration path:

- `pending_anchor` remains "sent but not accepted".
- `accepted` should mean "provider accepted in current epoch".
- Add `provider_accepted_at` and `provider_epoch_id`; do not overload
  `accepted_at`.

### CCB-Owned Event Index

Provider session files remain raw evidence, but CCB should persist compact
derived evidence so normal reply handling does not depend on rescanning large
provider sessions.

First version can be minimal:

- one JSONL ledger under ccbd runtime state for provider event evidence;
- append only from the existing provider polling path in the first slice;
- store only current-turn facts and source cursor references, not full provider
  transcript text;
- include enough source metadata to debug WSL/mac stale-reader cases.

This is not a replacement for provider logs. It is the stable CCB view used by
dispatcher, reply finalization, diagnostics, and recovery.

### Reply Delivery Ownership

Reply delivery is a separate trust boundary from provider completion.

For A -> B -> C:

- A -> B does not need `chain`; it is the root ask.
- B -> C uses `chain` when B needs C's result before replying to A.
- B's final reply to A must carry lineage back to A's original job.

Required evidence:

- child job id and parent job id;
- caller/callee actor names at submit time;
- reply id and mailbox inbound event id;
- whether recipient accepted the continuation prompt when the continuation is
  provider-backed.

Do not equate "reply stored" with "caller provider accepted the continuation".
The first is durable mailbox delivery; the second is provider turn acceptance.

## Recommended Implementation Slices

### Slice 0: Contract And Tests First

No behavior change except test scaffolding and documentation.

Add failing tests for:

- stale terminal boundary before current request anchor;
- clear between send and anchor observation;
- session rotate after send but before anchor observation;
- large session offset rollback;
- empty reply with anchor missing;
- B -> C multi-round chain before B replies to A;
- reply sent to wrong caller or unknown caller must fail, not complete.

### Slice 1: Separate Send From Provider Acceptance

Smallest source change:

- keep current submit/start behavior;
- add explicit `send_attempted_at`;
- add `provider_accepted_at`;
- keep `accepted_at` for backward compatibility, but stop using it as provider
  acceptance evidence in new logic;
- make diagnostics render the difference.

Acceptance criteria:

- job snapshots can show "sent, waiting for provider acceptance";
- no user-visible success is generated before current request anchor evidence.

### Slice 2: Provider Epoch Ledger

Add a small epoch manager for provider-backed agents.

Initial triggers:

- launch;
- CCB clear;
- session path/session id change;
- truncation or offset rollback observed by reader.

Acceptance criteria:

- post-clear events are in a new epoch;
- pre-clear terminal boundaries cannot complete post-clear jobs;
- old job waiting through a clear becomes `unbound_incomplete` or an explicit
  recoverable state, never completed from post-clear unrelated output.

### Slice 3: Turn Evidence Index

Persist accepted-turn evidence from the existing provider polling path.

Acceptance criteria:

- the dispatcher can answer "which epoch accepted this job";
- no reply extraction path needs to rescan a huge transcript just to know the
  current job state;
- diagnostics can report session path, epoch, cursor, anchor, and bound turn.

### Slice 4: Detector Enforcement

Update completion detectors and provider poll finalization to enforce:

- terminal boundary before anchor in the same epoch is not success;
- terminal boundary from a stale epoch is not success;
- empty terminal with no reply stays incomplete with a precise reason;
- reply harvested from runtime state is degraded evidence unless it is tied to
  current anchor and epoch.

PR238-style reason split fits here as a secondary diagnostic improvement.

### Slice 5: Reply Delivery And Chain Evidence

Strengthen chain reply ownership after provider acceptance is stable.

Acceptance criteria:

- A -> B root ask needs no `chain`;
- B -> C child asks carry parent lineage;
- B can talk to C multiple times before one final reply to A;
- reply delivery records caller/callee/mailbox ids;
- wrong-caller or missing-caller reply attempts are explicit failures.

## What To Avoid

- Do not make Codex 900 second terminalization the root fix. It can be a policy
  option later, but it does not prove current-turn ownership.
- Do not rely on pane idle, stale pane text, or provider hook alone for success.
- Do not make repeated full transcript scans the normal path.
- Do not merge broad PRs that mix Rust shims, provider probes, and reliability
  semantics before the core evidence contract is explicit.

## Open Questions

1. Should CCB-controlled clear immediately invalidate active jobs for that
   agent, or keep them waiting in a recoverable "epoch changed before
   acceptance" state?
2. Should manual clear detection be best-effort in the first slice, or must it
   block landing?
3. Where should the compact evidence ledger live: under existing completion
   snapshot storage, dispatcher job records, or a new ccbd provider-evidence
   JSONL?
4. Do we keep `accepted_at` backward-compatible forever, or migrate all readers
   to `send_attempted_at` / `provider_accepted_at` and later deprecate it?
