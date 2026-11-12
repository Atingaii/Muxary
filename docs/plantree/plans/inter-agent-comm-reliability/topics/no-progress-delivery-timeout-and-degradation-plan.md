# No-Progress Delivery Timeout And Degradation Plan

Date: 2026-07-07

Status: first source slice implemented in the working tree.

## Purpose

Replace Codex prompt-delivery timeout semantics from "elapsed since send" to
"elapsed since last trustworthy progress" so slow WSL/mac session writes do not
produce false `delivery_anchor_missing` failures while the provider session is
still moving.

This is the second timing slice after the first hard-gate implementation. It
keeps the first-slice invariant: unknown or stale evidence may become
incomplete/failed with diagnostics, but never successful completion.

## Current Problem

Current Codex active delivery has a fixed default deadline:

- `delivery_started_at + CCB_CODEX_DELIVERY_TIMEOUT_S`
- default `CCB_CODEX_DELIVERY_TIMEOUT_S = 120`
- failure reason: `codex_prompt_delivery_failed` with
  `delivery_failure_kind = delivery_anchor_missing`

That protects the queue from waiting forever, but it is still start-time based.
On WSL/mac, a provider may be alive and session evidence may be slowly appearing
or rotating while the current request anchor is not yet visible. A start-time
deadline can therefore fail a job while useful evidence is still changing.

## Design Decision

Use a no-progress timer for prompt delivery:

```text
delivery_no_progress_deadline = delivery_last_progress_at + delivery_timeout_s
```

`delivery_started_at` remains diagnostic metadata. It is no longer the primary
deadline once progress tracking is available.

This preserves the user's desired behavior:

- if provider/session evidence keeps moving, keep waiting;
- if evidence stops moving long enough, return an attributable incomplete or
  failed result;
- if current-turn ownership is never proven, never complete successfully.

## Progress Evidence

Progress should be evidence that the provider/session boundary is still moving,
not merely that a pane process exists.

Counts as progress:

- official Codex session binding path or session id changes;
- current session file appears after being missing;
- current session file size or mtime changes;
- reader offset advances;
- `SESSION_ROTATE` is emitted;
- request `ANCHOR_SEEN` is emitted;
- reply/assistant/terminal completion item is emitted;
- broad anchor fallback quarantine evidence changes;
- high-confidence provider pane signal is observed
  (`usage_limit`, `auth_failed`, `api_error`, `config_error`, `auth_required`);
- runtime crash/pane-dead evidence is observed.

Does not count by itself:

- pane is alive;
- tmux pane text is unchanged;
- old fallback log still exists;
- stale session path still resolves but size/mtime/offset are unchanged.

Rationale: pane liveness proves the target may still exist, but it does not
prove the current request is being accepted or written. Treating pane alive as
progress would recreate indefinite stalls.

## Runtime State Shape

Add or reuse only compact runtime-state fields:

- `delivery_last_progress_at`
- `delivery_progress_marker`
- `delivery_progress_kind`
- `delivery_no_progress_deadline_at` for snapshots/diagnostics
- `delivery_session_missing_since` when no official session path/log can be
  resolved

The marker should be a compact comparable tuple or dict derived from:

- official current log path;
- official session id;
- file exists flag;
- file size;
- mtime ns;
- poll state log path;
- poll offset;
- anchor/fallback quarantine marker.

No provider transcript content should be copied into runtime state.

Implementation note: the first patch reuses `delivery_timeout_s` as the
no-progress timeout value instead of adding a second timeout field.

## Algorithm

On every Codex active poll while `delivery_state = pending_anchor`:

1. Refresh official session binding.
2. Build a compact progress marker.
3. If marker changed from prior runtime state:
   - set `delivery_last_progress_at = now`;
   - store the new marker and progress kind;
   - persist by returning a non-emitting `ProviderPollResult` when there are no
     completion items.
4. Run normal polling and first-slice hard gates.
5. If no anchor is seen and no-progress timeout elapsed, classify the degraded
   outcome.

This keeps the current polling architecture; it does not require a persistent
tailer.

## Missing Session File Degradation

If the official session file/path cannot be resolved for longer than the
no-progress timeout, do not immediately guess a fallback session.

Degradation order:

1. If pane/runtime is dead:
   - status: `failed`
   - reason: `pane_dead` or `runtime_unavailable`
   - `no_reply_reason = provider_crashed` or `agent_unreachable_dead`
2. If pane shows a high-confidence provider error, borrow PR239's diagnostic
   taxonomy:
   - `provider_usage_limit`
   - `provider_auth_failed`
   - `provider_api_error`
   - `provider_config_error`
   - `provider_waiting_for_user`
3. If there is no high-confidence provider signal:
   - status: `incomplete` or current delivery-failure status by policy;
   - reason: `codex_session_file_missing`;
   - diagnostics include `session_file_missing_since`,
     `delivery_last_progress_at`, `delivery_no_progress_timeout_s`,
     `current_session_path`, `current_session_id`, and pane liveness facts.

The important rule: missing session file never falls back to completing from
`**/*.jsonl`. It can only produce diagnostics or a non-success terminal state.

## PR238 Adoption

Use PR238 as diagnostic classification, not as the root stability fix.

Adoptable pieces:

- split generic `task_complete_empty_reply` into:
  - `model_empty_output`
  - `delivery_late_empty`
  - `api_empty_after_error`
- propagate `api_error_seen` into Codex terminal payloads;
- add tests for empty-boundary classification.

How it fits this plan:

- `delivery_late_empty` means CCB observed terminal-ish evidence before current
  request-anchor ownership. It should remain incomplete.
- `api_empty_after_error` gives better user-facing remediation when provider API
  failed and then emitted an empty terminal.
- `model_empty_output` is still incomplete, but not a routing/session fault.

## PR239 Adoption

Do not merge PR239 wholesale. Adopt only narrow degradation/observability ideas:

- bounded pane capture/pane-alive queries so diagnostics do not hang;
- high-confidence provider error classification for quota/auth/API/config/user
  action required;
- `no_reply_reason` style diagnostics for non-success terminal replies;
- reply-delivery-stalled tagging as a separate mailbox slice.

Do not adopt as default in this slice:

- Codex `no_terminal_timeout_s = 900` terminalization;
- broad pane-content terminalization without current-turn proof;
- large Rust/mailbox/heartbeat changes bundled in PR239.

## Status Mapping

Recommended first implementation mapping:

| Condition | Status | Reason | Diagnostics |
| --- | --- | --- | --- |
| no progress, official session file missing, pane alive, no provider signal | `incomplete` | `codex_session_file_missing` | `no_reply_reason=completion_detection_gap` |
| no progress, current log drained, no anchor | `failed` or existing policy | `codex_prompt_delivery_failed` | `delivery_failure_kind=delivery_anchor_missing` |
| high-confidence usage limit | `failed` | `provider_usage_limit` | `no_reply_reason=provider_usage_limit`, `retry_after` if known |
| auth required/failed | `failed` | `provider_auth_failed` or `provider_waiting_for_user` | pane signal details |
| API/config error | `failed` | `provider_api_error` or `provider_config_error` | pane signal details |
| pane/runtime dead | `failed` | `pane_dead` | `no_reply_reason=provider_crashed` |
| terminal boundary empty before anchor | `incomplete` | `delivery_late_empty` | PR238 empty-reply diagnostics |

The exact `failed` versus `incomplete` status for
`codex_prompt_delivery_failed` can preserve current behavior in the first patch
to reduce migration risk. New missing-session cases should prefer
`incomplete` unless there is concrete provider/runtime failure evidence.

## Landed Slice

Implemented on 2026-07-07:

- Codex active start now seeds `delivery_last_progress_at`.
- Codex active poll records a compact `delivery_progress_marker` while
  `delivery_state = pending_anchor`.
- The marker includes only official session path/id, file exists/size/mtime,
  poll log path/offset, and fallback quarantine markers.
- Delivery timeout is now measured from `delivery_last_progress_at` first, then
  falls back to `delivery_started_at` for legacy active records.
- Official session/log missing past the no-progress window now returns terminal
  `incomplete` with reason `codex_session_file_missing` and
  `no_reply_reason=completion_detection_gap`.
- If the pane already has high-confidence shutdown text while the session/log
  is missing, the same guard returns `failed/codex_prompt_delivery_failed` with
  `no_reply_reason=provider_crashed`.
- Current official log drained past the no-progress window still returns the
  existing `codex_prompt_delivery_failed` /
  `delivery_anchor_missing` failure.
- Runtime snapshots expose `delivery_last_progress_at`,
  `delivery_progress_kind`, `delivery_session_missing_since`, and a derived
  `delivery_no_progress_deadline_at`.

Not implemented in this slice:

- PR238 empty-reply sub-classification.
- PR239 high-confidence pane provider error classification.
- Persistent tailer or CCB-owned compact evidence log.
- A separate hard maximum for noisy but never-accepted active jobs.

## Test Plan

Required tests before implementation:

- done: session file size/mtime changes without anchor; after more than
  the old 120 second start-time window, no delivery failure occurs and
  `delivery_last_progress_at` advances;
- done: official session file missing for less than the no-progress window stays
  pending;
- done: official session file missing past the no-progress window becomes
  `codex_session_file_missing` with `no_reply_reason=completion_detection_gap`;
- deferred: missing session plus high-confidence pane usage/auth/API/config signal maps to
  the matching PR239-style provider reason;
- done: current log drained and unchanged past the no-progress window still produces
  the existing `delivery_anchor_missing` class;
- done: fallback quarantine does not reset no-progress time forever unless its marker
  actually changes;
- done: official new session appears after a long no-progress/fallback interval and
  still wins over stale fallback quarantine;
- deferred: PR238 empty-boundary classification covers `delivery_late_empty`,
  `api_empty_after_error`, and `model_empty_output`.

Verification run for the landed slice:

- `PYTHONPATH=lib python -m pytest -q test/test_v2_execution_service.py`
  -> `65 passed`
- `PYTHONPATH=lib python -m pytest -q test/test_stability_regressions.py`
  -> `16 passed`
- `PYTHONPATH=lib python -m pytest -q test/test_provider_execution_service_runtime.py`
  -> `11 passed`
- `PYTHONPATH=lib python -m pytest -q test/test_codex_runtime_accelerator_polling.py`
  -> `5 passed`
- `PYTHONPATH=lib python -m compileall -q lib/provider_backends/codex lib/provider_execution test/test_v2_execution_service.py test/test_stability_regressions.py`
  -> passed
- `git diff --check` -> passed

Recommended integration/stress tests:

- WSL/mac large session replay where file writes are delayed but mtime/size
  changes continue;
- clear then ask where a new session appears late;
- provider pane waiting for login where no session file appears;
- old job blocked behind a missing-session ask and later releases with a
  non-success terminal.

## Risks

- If unrelated provider log noise keeps the current session file changing, the
  job may wait longer than desired. This is acceptable for this slice because
  completion still requires current-anchor evidence, and CCB must not guess
  success from noisy evidence.
- If no hard maximum exists, pathological active-noise cases can hold a serial
  queue. This should be addressed by a later policy decision or agent health
  monitor, not by silently completing or wrong-session fallback.
- Pane-content classification must stay high-confidence and bounded. Broad
  marker parsing can diagnose an already-failed state, but must not become a
  success or broad terminalization source.

## Acceptance Criteria

- Start-time-only delivery timeout no longer fires while session evidence is
  still changing.
- Missing session files produce attributable non-success diagnostics after a
  no-progress window.
- PR238/PR239-derived degradation improves explanations without weakening the
  accepted-turn/session-epoch hard gates.
- No new path completes from broad fallback logs or from pane heuristics alone.
