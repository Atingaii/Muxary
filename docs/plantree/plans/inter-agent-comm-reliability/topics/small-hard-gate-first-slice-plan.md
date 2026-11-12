# Small Hard-Gate First Slice Plan

Date: 2026-07-06

Status: first batch implemented in working tree; second-batch clear and lineage
gates remain pending.

## Purpose

Define the smallest source change that can stabilize most ask reply failures
caused by timing drift without starting a tailer, provider rewrite, or broad
fallback policy change.

The working hypothesis is that current CCB already has most of the required
state:

- Codex active start records `request_anchor` and
  `delivery_state = pending_anchor`.
- Codex polling ignores assistant and terminal events until the request anchor
  is observed.
- Codex finalization changes `delivery_state` to `accepted` when anchor evidence
  is observed.
- Completion detectors reset `anchor_seen` on `SESSION_ROTATE`.
- Empty provider terminal boundaries already become incomplete for the protocol
  and session-boundary detectors.

The missing piece is that these facts are still too soft. They must become hard
gates before CCB marks a job completed or lets clear/session drift leave an
active job ambiguous.

## Source Anchors

Current hooks to reuse:

- `lib/provider_backends/codex/execution_runtime/start.py`: active start
  captures reader state, wraps prompt with `request_anchor`, and sets
  `delivery_state = pending_anchor`.
- `lib/provider_backends/codex/execution_runtime/polling_runtime.py`: Codex
  ignores non-user events until `poll.anchor_seen` is true.
- `lib/provider_backends/codex/execution_runtime/state_machine_runtime/finalization.py`:
  Codex changes `delivery_state` to `accepted` and writes
  `delivery_confirmed_at` after anchor evidence.
- `lib/completion/detectors/base.py`: `SESSION_ROTATE` resets anchor and reply
  state.
- `lib/completion/detectors/protocol_turn.py` and
  `lib/completion/detectors/session_boundary.py`: empty terminal boundaries are
  already incomplete, not completed.

Current gaps to close:

- `accepted_at` is still creation/send time, not provider acceptance time.
- The dispatcher can complete from terminal decisions that do not carry a hard
  "same accepted turn" proof.
- `ccb clear` sends `/clear` to panes but does not resolve or invalidate active
  jobs.
- Codex anchor fallback can scan `**/*.jsonl` and silently rebind when the
  current log is drained and anchor is missing.
- Session rotation resets detector state, but terminal acceptance is not yet
  guarded by an explicit latest-anchor-after-rotation rule.

## Scope

In scope for the first implementation batch:

- Codex active provider path first.
- Provider acceptance from existing `delivery_state == accepted` plus
  `anchor_seen` or explicit `no_wrap`.
- Codex broad anchor fallback quarantine.
- Session rotate hard gate.
- Diagnostics and tests proving fallback scans do not complete normal jobs by
  themselves.

In scope for the second batch after the first gates prove out:

- Generic dispatcher/completion hard gate additions where the existing decision
  fields are sufficient.
- Reply non-empty and mailbox-lineage hardening where they are not already
  enforced.
- Clear-time active-job resolution for provider-backed agents.

Out of scope for this first slice:

- Persistent tailer.
- Global event-store redesign.
- New long-lived supervisors.
- Broad timeout terminalization such as a default 900 second Codex no-terminal
  fallback.
- Full provider parity for every provider before the Codex path proves the
  invariant.

## Proposed Changes

### 1. Provider Acceptance From Existing Delivery State

Treat Codex `delivery_state = accepted` as provider acceptance evidence.

First-batch implementation:

- keep storage unchanged and make the hard gate read
  `delivery_state == accepted` plus `anchor_seen`;
- keep explicit `no_wrap` as the narrow accepted exception.

Do not add `provider_accepted_at` in the first batch. It is useful diagnostic
metadata, but it is not required for the initial correctness gate.

Completion success requires provider acceptance unless the job is an explicit
`no_wrap` path with a separate contract.

Expected result:

- "prompt sent to pane" no longer counts as provider accepted;
- terminal output before request-anchor observation cannot become completed.

### 2. Dispatcher Completion Hard Gate

Add a last-mile guard before `dispatcher.complete(..., completed)` accepts a
provider-backed job.

Completed decisions must satisfy:

- anchor was seen, or the submission is an explicit `no_wrap` contract;
- reply text is non-empty for providers where empty terminal output is not a
  valid success;
- source cursor or runtime state still points at the accepted stream;
- if a session rotate happened after the last anchor, a later anchor must be
  observed before completion;
- mailbox lineage exists for continuation and chain replies.

If the gate fails, normalize to incomplete or failed with a precise reason:

- `terminal_before_provider_acceptance`
- `task_complete_empty_reply`
- `terminal_after_session_rotate_without_anchor`
- `missing_reply_lineage`
- `ambiguous_provider_turn`

Expected result:

- stale terminal, empty terminal, wrong-caller, and post-rotate terminal events
  cannot be reported as success.

First-batch placement:

- validate decisions in
  `lib/ccbd/services/dispatcher_runtime/polling_service.py`
  `_resolve_update_decision`;
- apply the same validation to terminal decisions surfaced by `_tick_tracker`;
- normalize before `dispatcher.complete(...)`, not inside terminal persistence.

The first batch should avoid a gate-chain abstraction. A small validation
function is enough until the number of rules proves otherwise.

### 3. Clear Barrier For Active Jobs

Status: second batch; keep the semantic plan, but do not make it a blocker for
the first implementation batch.

Before sending provider-native `/clear` for an agent, inspect the active job for
that agent.

Minimal first-slice behavior:

- no provider acceptance yet:
  `incomplete(clear_before_provider_acceptance)`;
- provider accepted but no terminal evidence before the clear:
  `incomplete(clear_during_provider_turn)`;
- terminal already durably recorded before clear:
  leave existing terminal result unchanged.

Then send the provider-native clear.

Implementation caution:

Current `project_clear.py` is a pane-clear handler and does not directly own
dispatcher completion. The first clear-barrier implementation should use a
dispatcher-owned or dispatcher-consumed signal instead of making the tmux clear
helper directly complete jobs.

Expected result:

- clear does not leave an active ask waiting forever;
- clear cannot make a later unrelated provider output complete the old job.

### 4. Quarantine Broad Anchor Fallback

Status: first batch.

Keep Codex broad anchor fallback as recovery evidence, but remove it from the
normal success path.

Rules:

- `**/*.jsonl` fallback may record diagnostics or a recovery candidate;
- fallback alone cannot mark `delivery_state = accepted`;
- ambiguous or multiple matches are diagnostics only;
- same-workspace match without same-stream continuity does not complete a job.

Expected result:

- WSL/mac large-session or directory-drift behavior cannot silently rebind a job
  to an old session file.

### 5. Session Rotate Gate

Status: first batch.

Use existing `SESSION_ROTATE` reset behavior as a hard invariant.

Rules:

- after session rotate, terminal completion requires a fresh request anchor in
  the new session path;
- terminal item from the old path after rotate becomes stale evidence;
- offset rollback or truncation is treated like rotate for this first slice.

Expected result:

- session switch, provider clear, or log truncation cannot mix old and new
  provider turns.

## Expected State Outcomes

After this slice, every active ask should converge into one of three states:

- `completed`: same accepted provider turn, same anchor/session continuity,
  non-empty reply, valid caller lineage.
- `incomplete`: clear, missing provider acceptance, empty terminal, stale
  terminal, session rotate without fresh anchor, fallback ambiguity.
- `failed`: provider, pane, transport, or mailbox error with concrete evidence.

The slice does not guarantee that the provider always replies. It guarantees
that CCB does not report success from uncertain evidence and does not leave
clear-induced timing drift ambiguous.

## Test Plan

Add focused tests before or with the first implementation batch:

- terminal item before anchor cannot complete;
- anchor seen with non-empty terminal can complete;
- session rotate resets anchor and terminal before fresh anchor is rejected;
- broad fallback finds a candidate but cannot complete without continuity;
- empty terminal boundary remains incomplete;
- explicit `no_wrap` path still completes normally;
- failed delivery state remains failed and is not re-normalized.

Second-batch tests:

- prompt sent but anchor never observed remains pending until timeout or becomes
  incomplete through explicit clear/failure;
- `ccb clear <agent>` resolves active unaccepted job as
  `clear_before_provider_acceptance`;
- `ccb clear <agent>` resolves active accepted job without terminal as
  `clear_during_provider_turn`;
- B -> C chain reply requires parent/child lineage before B replies to A;
- wrong or missing caller lineage cannot complete as success.

## Implementation Evidence

Working-tree source slice:

- `lib/provider_execution/service_runtime/models.py` and
  `lib/provider_execution/service_runtime/polling.py` carry the current
  `ProviderSubmission` with each emitted `ExecutionUpdate`.
- `lib/ccbd/services/dispatcher_runtime/polling_service.py` validates Codex
  active completed decisions before `dispatcher.complete(...)`.
- `lib/ccbd/services/dispatcher_runtime/completion_runtime/terminal_service.py`
  respects the hard-gate normalization marker so old tracker/prior reply state
  cannot be merged back into a rejected completion.
- `lib/provider_backends/codex/execution.py` records broad anchor fallback as
  quarantined diagnostics instead of rebinding normal polling to the fallback
  log.
- `test/test_v2_ccbd_dispatcher.py` covers terminal before acceptance, terminal
  after rotate without fresh anchor, accepted-anchor success, and explicit
  `no_wrap` success.
- `test/test_v2_execution_service.py` covers Codex fallback quarantine without
  rebind, and the strict delayed path where fallback remains quarantined for a
  fake-clock 30 minute window before an official new Codex session binding is
  adopted with fresh anchor evidence.

Verification:

- `PYTHONPATH=lib python -m pytest -q test/test_v2_ccbd_dispatcher.py`
  -> passed.
- `PYTHONPATH=lib python -m pytest -q test/test_v2_execution_service.py`
  -> passed.
- `PYTHONPATH=lib python -m pytest -q test/test_v2_execution_service.py::test_execution_service_codex_adapter_adopts_new_session_after_delayed_fallback_quarantine`
  -> passed; this is the dedicated long-duration/new-session temporal check.
- `PYTHONPATH=lib python -m compileall -q ...` -> passed.
- `git diff --check -- ...` -> passed.

## Coworker Review Outcome

Coworker review `job_7311c8f04328` returned `PASS` with conditions. See
[coworker-review-20260706-small-hard-gate.md](coworker-review-20260706-small-hard-gate.md).

Accepted review adjustments:

- first batch should be #1 provider acceptance gate, #4 fallback quarantine, and
  #5 session rotate gate;
- do not add `provider_accepted_at` in the first batch; reuse existing
  `delivery_state == accepted`;
- place the hard gate in `polling_service.py` before `dispatcher.complete(...)`;
- keep clear barrier as second batch because `project_clear.py` currently does
  not own dispatcher state;
- do not introduce a new gate-chain abstraction or terminal-persistence API
  change for the first patch.

## Review Questions For Coworker

1. Is this small enough to land without introducing a new subsystem?
2. Are any of the hard gates likely to break valid existing provider flows?
3. Should the first patch add explicit `provider_accepted_at`, or should it
   initially reuse `delivery_state == accepted` to reduce migration risk?
4. Where is the best dispatcher-level hook for the completion hard gate?
5. Is clear-time active-job completion safe, or should clear only mark the job
   incomplete after provider-native `/clear` is successfully sent?
6. Which tests are mandatory before implementation, and which can follow after
   the Codex path is proven?

## Acceptance Criteria

First-batch acceptance:

- No completed Codex active job can be produced before current request-anchor
  evidence.
- Broad anchor fallback cannot complete a job or rebind normal polling by
  itself.
- Empty terminal output cannot complete a provider-backed ask unless a provider
  has an explicit empty-success contract.
- Session rotate without fresh anchor evidence cannot complete as success.
- The first slice changes no tailer, no provider supervisor, and no global
  event-store architecture.

Full-plan acceptance still pending:

- No completed job can be produced before current request-anchor evidence.
- No completed job can be produced from a stale session after rotate/clear.
- `ccb clear` no longer leaves target-agent active jobs ambiguous.
- Broad anchor fallback cannot complete a job by itself.
- Empty terminal output cannot complete a provider-backed ask unless a provider
  has an explicit empty-success contract.
