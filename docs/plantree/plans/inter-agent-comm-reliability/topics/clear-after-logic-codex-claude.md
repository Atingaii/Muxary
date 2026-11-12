# Clear-After Logic: Codex and Claude

Date: 2026-07-06

Status: source-backed analysis; no source behavior changed by this note.

## Question

When an agent conversation is cleared, why can later `ask` reply detection become
unstable on WSL/macOS, especially with large provider session files, while the
same workflow often looks fine on Linux?

The target is not to add another degraded timeout. The target is to understand
the original post-clear behavior for Codex and Claude, then define the smallest
root-level boundary that makes reply ownership stable.

## Source Evidence

Current project clear behavior:

- `lib/ccbd/handlers/project_clear.py`
  - `_clear_agent_context()` resolves the mounted agent pane and calls
    `_send_clear_sequence()`.
  - `_send_clear_sequence()` sends `C-u`, literal `/clear`, then `Enter` into
    the provider pane.
  - The handler returns `status=cleared` after input submission.
  - Only OpenCode gets a small submit delay. Codex and Claude do not get
    provider-specific clear acknowledgement, epoch recording, or active-job
    invalidation.

Codex active request behavior:

- `lib/provider_backends/codex/execution_runtime/start.py`
  - active start captures the current reader state, wraps the prompt with a
    request anchor, sends it to the pane, and records
    `delivery_state=pending_anchor`.
- `lib/provider_backends/codex/execution_runtime/state_machine_runtime/finalization.py`
  - delivery becomes accepted only after the poller observes the request anchor.
- `lib/provider_backends/codex/comm_runtime/polling_runtime/logs.py`
  - when the latest log changes, the reader can switch logs and reset offset to
    zero.
- `lib/provider_backends/codex/execution_runtime/state_machine_runtime/models.py`
  - session rotation resets local poll buffers and anchor state.
- `lib/provider_backends/codex/execution.py`
  - if the current log is drained and the anchor is still missing, Codex may
    scan other workspace logs for a unique matching anchor before failing
    delivery.

Claude active request behavior:

- `lib/provider_backends/claude/execution_runtime/start.py`
  - active start captures the current reader state and request anchor, but keeps
    `prompt_sent=False`; the prompt is dispatched later when the pane is ready.
- `lib/provider_backends/claude/execution_runtime/polling.py`
  - polling first dispatches the deferred prompt when ready, then checks exact
    hook artifacts, then reads session events.
- `bin/ccb-provider-finish-hook.py`
  - Claude Stop hook extracts a request id from the transcript and writes a
    completion event.
- `lib/provider_backends/claude/execution_runtime/hook_results_runtime.py`
  - polling loads `completion/events/<req_id>.json` and terminalizes from that
    exact event, normalizing empty hook replies to `incomplete`.
- `lib/provider_backends/claude/execution_runtime/state_machine_runtime/models.py`
  - session rotation resets local poll buffers and anchor state.

Design documents already point at the same boundary:

- `docs/managed-provider-completion-reliability-plan.md`
  - Claude hook handling needs a real turn-identity contract, not merely the
    latest visible `CCB_REQ_ID`.
  - single-file terminal hook overwrite is too weak; append-oriented turn
    evidence is the target model.
- `docs/claude-session-isolation-contract.md`
  - managed Claude session reading must remain bound to the agent's managed
    home and must not drift to a newer workspace session outside explicit
    rebinding logic.

## Current Shared Clear Semantics

Today `ccb clear <agent>` is a pane input operation, not a CCB evidence boundary.

It means:

- CCB submitted `/clear` into the provider UI.
- CCB did not record a provider epoch.
- CCB did not prove the provider accepted or completed the clear.
- CCB did not mark active submissions as pre-clear work.
- CCB did not prevent post-clear provider events from being considered by a
  pre-clear submission, except where individual provider pollers happen to
  reject them through anchor/session logic.

This is the core reason the behavior is timing-sensitive. The provider timeline
has reset, but CCB's job timeline has not recorded a corresponding monotonic
barrier.

## Ordinary Manual Clear

Ordinary provider clear is harder than `ccb clear` because CCB does not submit
the command itself. A user may type `/clear` directly in the pane, or a provider
may reset the conversation/session for its own reasons.

In the original logic, manual clear is only visible indirectly:

- a user event containing `/clear`, if the provider records it;
- a session path or session id change;
- a session file truncation or offset rollback;
- disappearance of expected request-anchor evidence;
- a hook event with no usable answer text;
- a provider UI state transition that the poller interprets as a new session.

These symptoms reset provider context, but there is no shared CCB object saying
"all evidence before this point belongs to epoch N, and all evidence after this
point belongs to epoch N+1."

Therefore ordinary clear and `ccb clear` are currently different only in how
they are triggered. Neither creates a first-class reply ownership boundary.

## Codex After Clear

Codex is mostly anchor-and-session-log driven.

The intended happy path is:

1. Capture current session log state.
2. Send wrapped prompt with `CCB_REQ_ID`.
3. Wait until the session log shows the anchor.
4. Treat anchor observation as provider acceptance.
5. Complete from a terminal provider event or assistant-final evidence bound to
   that request.

After clear, the original code handles only local reader symptoms:

- if a newer session log is selected, the reader can rotate and reset offset;
- session rotation clears local buffers and anchor state;
- if the current log is drained and anchor is missing, fallback scans other
  workspace logs for a unique copy of the same request anchor;
- if no anchor appears and delivery timeout policy says so, the job can fail as
  missing anchor.

What it does not do:

- it does not mark a CCB-owned clear epoch when `/clear` is submitted;
- it does not immediately resolve active pre-clear jobs as interrupted by clear;
- it does not prevent old active submissions from continuing to search across
  large session roots after a context reset;
- it does not separate "prompt never accepted" from "provider accepted but
  cleared before terminal reply" as monotonic states.

This makes large session files worse. The fallback and anchor checks can require
full scans across candidate logs. On Linux this may still be fast and ordered
enough to look stable. On WSL/macOS, slower file visibility and filesystem
metadata behavior widen the race window between pane input, log writes, session
rotation, and poller reads.

Codex conclusion:

The problem is not only that large session files are slow. The deeper issue is
that clear/session rotation is observed as a reader side effect instead of a CCB
job-state boundary.

## Claude After Clear

Claude has two completion paths:

1. Hook artifact path.
2. Session event log path.

The hook path can be faster and more exact when it is correct:

- the Stop hook reads the transcript;
- it extracts the current turn request id;
- it writes `completion/events/<req_id>.json`;
- polling loads the event for the active request anchor and terminalizes.

The session event path:

- observes a user event containing the request anchor;
- collects assistant text after anchor observation;
- uses a turn boundary event to finish the answer.

After clear, the original code again handles local symptoms, not a shared epoch:

- start captures the current session state, but may defer prompt dispatch until
  the pane is ready;
- a clear before deferred dispatch can make the prompt land in a fresh provider
  context while the submission's `accepted_at` already exists;
- session rotation resets local poll buffers and anchor state;
- hook completion is keyed by request id, but the hook event itself does not
  carry a CCB epoch;
- an empty Stop hook is normalized to `incomplete`, which improves diagnosis but
  does not prove whether the underlying cause was clear, wrong turn, API issue,
  or transcript race.

The existing design document already notes that Claude Stop hooks must bind the
assistant stop to the actual transcript turn and not to the latest visible
request id. That is the same class of problem as post-clear instability: the
terminal event must be tied to the accepted request turn, not merely to text that
can be found in a large or recently reset transcript.

Claude conclusion:

Claude can be faster than Codex when hook artifacts are correct, but after clear
it still lacks an epoch guard. A hook or session event can describe a request id
without proving it belongs to the same provider timeline that accepted the ask.

## Why Clear Produces Empty Replies

Empty replies after clear are usually not one bug. They are a symptom family:

- the provider hook fired for a side turn, auth/info turn, interruption turn, or
  freshly cleared context without answer text;
- the poller found a terminal-looking event before assistant text was visible;
- the active submission lost its original accepted-turn evidence after session
  rotation;
- the request anchor was never accepted, but the system only discovered that
  later through timeout or missing evidence;
- old and new provider timelines were mixed because no clear epoch separated
  them.

PR238-style empty-reply diagnostics are useful because they name the symptom.
They are not a root boundary because they still operate after the timeline is
already ambiguous.

## Minimal Root Boundary

The first root fix should be a simple monotonic boundary, not a broad recovery
framework.

For `ccb clear`:

- write a CCB-owned provider epoch barrier immediately after the clear command is
  submitted;
- record agent, provider, pane id, prior session path/id if known, timestamp,
  and reason `ccb_clear`;
- all active submissions for that agent must be resolved or marked as
  interrupted by the barrier:
  - no provider anchor yet: `incomplete(clear_before_provider_acceptance)`;
  - anchor accepted but no terminal answer: `incomplete(clear_during_provider_turn)`;
- all later asks start in the new epoch;
- pre-clear evidence cannot complete post-clear jobs, and post-clear evidence
  cannot complete pre-clear jobs.

For ordinary manual clear:

- first slice can be best-effort detection only;
- if a poller observes a strong clear symptom, create
  `manual_clear_observed`;
- after the barrier is created, use the same invalidation rules as `ccb clear`.

For Codex:

- bind delivery acceptance to `{request_anchor, session_path/session_id, epoch}`;
- keep anchor fallback as recovery evidence, but only inside the current epoch;
- record anchor observation in compact CCB-owned evidence so reply detection no
  longer repeatedly scans large session files for the same fact.

For Claude:

- bind hook artifacts to `{request_anchor, provider_turn_ref, transcript_path,
  epoch}`;
- move from single terminal overwrite toward append-style hook evidence;
- keep empty hook replies as diagnostics, but do not let them substitute for
  turn ownership.

## Non-Goals For The First Slice

- Do not implement automatic provider-specific recovery across clear.
- Do not keep old jobs alive across clear in hidden recoverable state.
- Do not introduce a persistent tailer until benchmarks prove the existing
  polling path remains too slow after fallback scans are removed from the normal
  path. If added later, it must store compact CCB facts and artifact pointers
  only, not full transcript text.
- Do not rely on more timeout fallback to solve wrong-turn or empty-reply
  ambiguity.

## Decision

The original clear logic is insufficient for absolute reply stability because
it treats clear as pane input and session rotation as local reader state. It does
not make clear a CCB-owned monotonic state transition.

Codex and Claude differ in mechanics, but they share the same missing boundary:
accepted-turn evidence must be tied to a provider epoch, and clear must advance
that epoch before later provider events can be used for completion.
