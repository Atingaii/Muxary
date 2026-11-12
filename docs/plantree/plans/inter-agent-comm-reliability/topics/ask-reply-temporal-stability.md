# Ask Reply Temporal Stability

Date: 2026-07-06

## Focus

This topic narrows the reliability work to ask-after-reply stability, especially
when provider context is cleared or provider session files are large.

The target is temporal stability:

- every observed provider event is ordered against the job it may affect;
- send, provider acceptance, assistant progress, terminal completion, and reply
  delivery are separate monotonic states;
- clear/session rotation creates a hard evidence boundary;
- a late or stale provider event cannot complete the wrong job or reply to the
  wrong caller.

## Deep Cause Of Continued Jitter

Current behavior has useful partial guards, but no single cross-layer clock or
epoch that owns the whole ask lifecycle.

### 1. Send And Acceptance Are Conflated

Codex active start captures the reader state at the current log tail, then
sends the prompt. It records `accepted_at` immediately and sets
`delivery_state = pending_anchor`.

The later poll path changes `delivery_state` to `accepted` only after the
request anchor is observed. That is the correct direction, but the older
`accepted_at` name still allows readers and diagnostics to treat "daemon
accepted / prompt sent" as if "provider accepted the turn" had happened.

Temporal effect:

- a job can look accepted before the provider has actually accepted it;
- downstream reply handling can reason about a job that has not yet crossed the
  provider boundary.

### 2. Reader Binding Is Sampled, Not Transactional

The Codex reader initializes at EOF of the selected log. If the selected log is
correct, this is fast and avoids old history. If the selected log is stale, the
system later tries to recover by switching logs or scanning other same-workspace
logs for the active anchor.

Fallback is intentionally conservative, but it is still a sampled recovery path:

- current log may appear drained while the provider is about to write;
- a new log may be discovered after a delay;
- multiple same-workspace logs may be ambiguous;
- fallback scans large JSONL files to find the anchor.

Long session files amplify the problem because recovery paths reset offsets,
scan full files, or enumerate many logs. WSL/mac amplify it further because file
visibility, mtime, and cross-process I/O latency are less predictable than on a
local Linux filesystem.

Temporal effect:

- the daemon may observe "no anchor yet" and later "anchor exists in another
  log";
- completion decisions can lag, flip source logs, or attach to late evidence
  without a stable epoch identity.

### 3. Clear Is A Pane Command, Not A Timeline Barrier

Project clear currently sends `/clear` to the provider pane. It does not create
a durable CCB evidence epoch, does not invalidate active job evidence, and does
not wait for a provider-side clear acknowledgement.

The polling state can observe session rotation and reset anchor/reply state, but
that reset is local to the detector stream. It is not a global rule that says:
"events before this clear cannot complete jobs after this clear, and jobs sent
before this clear cannot be completed from events after this clear unless they
are explicitly re-bound."

Temporal effect:

- pre-clear jobs can remain active across a provider timeline reset;
- post-clear provider events can be interpreted as continuation of pre-clear
  state;
- manual clear is even harder because CCB may only see indirect symptoms such
  as rotation, truncation, offset rollback, or missing anchors.

### 4. Completion Detectors Have Local Order, Not Global Epoch Order

Completion detectors reset state on `SESSION_ROTATE` and track `anchor_seen`.
That protects some local cases, but the item stream does not currently carry a
first-class `provider_epoch_id`, and terminal items are not rejected by an epoch
predicate.

Temporal effect:

- the detector can make a correct local decision for the event order it sees,
  while the global question "does this event belong to the job's accepted epoch"
  is still unanswered.

### 5. Reply Delivery Inherits Upstream Attribution Errors

Mailbox delivery can persist a reply and lineage, but reply correctness depends
on the child job's terminal decision being attributed to the right provider
turn. If B's terminal decision is stale, empty, or wrong-caller-attributed, A
receives a durable but semantically wrong reply.

Temporal effect:

- B -> C chain reliability depends on both provider turn attribution and mailbox
  lineage;
- fixing mailbox alone cannot repair wrong provider completion attribution.

## Root Fix: A Monotonic Timeline State Machine

The durable model should be an event-sourced state machine with one monotonic
timeline per provider-backed agent.

### Timeline Identity

Each provider-backed agent needs:

- `provider_generation_id`: runtime launch/restart generation.
- `provider_epoch_id`: evidence epoch inside a provider generation.
- `provider_stream_id`: concrete transcript/session path or provider session id.
- `reader_cursor`: source cursor within that stream.
- `job_turn_id`: CCB job + request anchor + accepted epoch.

`provider_epoch_id` changes on:

- managed launch;
- CCB clear;
- observed manual clear;
- session path/session id change;
- offset rollback;
- file truncation;
- reader rebind with unknown continuity.

### State Transitions

Allowed job states should be monotonic:

```text
submitted
  -> send_attempted
  -> provider_accept_pending
  -> provider_accepted
  -> running
  -> terminal_completed | terminal_failed | terminal_incomplete
```

Side exits:

```text
provider_accept_pending
  -> unbound_incomplete(epoch_changed_before_acceptance)
  -> unbound_incomplete(anchor_not_observed)

provider_accepted/running
  -> terminal_incomplete(epoch_changed_after_acceptance)
  -> terminal_failed(provider_failure)
```

Forbidden transitions:

- `send_attempted -> terminal_completed`
- `provider_accept_pending -> terminal_completed`
- any terminal completion from a different `provider_epoch_id`
- empty provider terminal -> completed
- reply delivery success without a terminal child job whose lineage matches the
  caller chain

### Clear Barrier Rule

`ccb_clear` should write a CCB-owned epoch barrier immediately after the clear
workflow is submitted:

- active jobs that have not reached `provider_accepted` become
  `unbound_incomplete(clear_before_acceptance)` or an explicit recoverable
  state;
- active jobs already accepted become
  `terminal_incomplete(clear_during_running)` unless a provider-specific
  completion event from the old epoch is already durably recorded before the
  barrier;
- new asks after clear are assigned to the new epoch and cannot be completed by
  pre-clear events;
- the post-clear readiness probe from
  [ccb-clear-epoch-probe-design.md](ccb-clear-epoch-probe-design.md) binds the
  new epoch before real work resumes.

This does not require trusting provider clear acknowledgement in the first
implementation. The CCB barrier is enough to prevent cross-epoch completion.

### Long Session Rule

Large provider sessions must remain raw evidence, not the normal coordination
surface.

Normal path:

- tail incrementally from captured cursor;
- append compact CCB-owned event evidence for anchor/progress/terminal;
- complete jobs from compact evidence, not repeated transcript rescans.

Fallback path:

- full-file anchor search is diagnostic/recovery only;
- any rebind from fallback creates a new epoch or records explicit continuity
  proof;
- ambiguous fallback never completes; it only produces an incomplete diagnostic.

### Reply Stability Rule

A reply to a caller is stable only when both layers agree:

- provider layer: the callee job has terminal evidence in its accepted epoch;
- mailbox layer: the reply is stored with parent/child lineage and delivered to
  the intended caller mailbox.

For A -> B -> C:

- A -> B root ask does not use `chain`;
- B -> C uses `chain` for dependency;
- B can have multiple B -> C child jobs before one final B -> A reply;
- B -> A final reply must reference A's parent job/message lineage;
- if lineage is missing or caller no longer matches, fail explicitly rather
  than guessing a recipient.

## Minimal Implementation Order

1. Add timeline fields and tests without changing behavior:
   `send_attempted_at`, `provider_accepted_at`, `provider_generation_id`,
   `provider_epoch_id`, `provider_stream_id`, `source_cursor`.

2. Add CCB clear barriers:
   on clear, create a new epoch and terminalize or mark active jobs according to
   whether they crossed provider acceptance.

3. Enforce terminal epoch predicates:
   a completion item can terminalize only if its epoch equals the job's accepted
   epoch and the job has observed its anchor.

4. Add compact event evidence:
   persist anchor/progress/terminal facts per job/epoch; use this evidence for
   finalization and diagnostics.

5. Move fallback scans behind recovery semantics:
   fallback can find evidence, but cannot silently adopt a new stream without
   epoch continuity proof.

6. Strengthen reply delivery lineage:
   final reply delivery requires explicit parent/child lineage and intended
   caller mailbox identity.

## Acceptance Criteria

- Clearing an agent during a pending ask never lets a pre-clear or post-clear
  stale event complete the wrong job.
- A large Codex session only affects diagnostic/recovery latency, not normal
  ask completion latency.
- A missing anchor remains pending or becomes explicit incomplete; it never
  becomes completed.
- A terminal event without same-epoch anchor evidence cannot complete.
- B -> C multi-round chain can complete and B can reply once to A with correct
  lineage.
- Wrong caller, missing caller, or ambiguous caller becomes failed/incomplete
  with diagnostics, not a best-effort delivery.

## Why This Solves The WSL/mac Pattern

WSL/mac make file observation less deterministic; they do not create the
semantic bug by themselves. The semantic bug is that CCB currently relies on a
sampled view of mutable provider files to infer a total order.

By introducing CCB-owned epochs, monotonic state transitions, and compact
evidence, delayed file visibility becomes a delay in evidence arrival, not a
source of wrong completion. Late evidence from the wrong epoch is rejected.
Ambiguous evidence is diagnostic. Current-turn evidence remains the only path to
completion.
