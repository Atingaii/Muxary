# Coworker Review: Small Hard-Gate First Slice

Date: 2026-07-06

Status: accepted review input; first batch implemented in working tree.

Artifact:

- `.ccb/ccbd/artifacts/text/completion-reply/job_7311c8f04328-art_e6e9311357c74656.txt`

## Conclusion

Review result: `PASS`, with conditions.

The review agrees that the small hard-gate direction is the right first source
slice. It is small enough to land without a tailer, provider rewrite, new
supervisor, or global event-store abstraction.

Estimated implementation size from the review:

- provider acceptance from existing `delivery_state`: small;
- dispatcher completion hard gate: small;
- fallback quarantine: small and precise;
- session rotate gate: small;
- clear barrier: useful, but the biggest integration risk because current
  `project_clear.py` does not directly own dispatcher completion.

## Accepted Adjustments

### First Batch

Start with the three gates that are both small and mutually foundational:

1. provider acceptance gate using existing `delivery_state == "accepted"` plus
   `anchor_seen` or explicit `no_wrap`;
2. Codex broad anchor fallback quarantine so `**/*.jsonl` scans can produce
   recovery diagnostics but cannot complete a job by themselves;
3. session rotate gate so terminal evidence after rotate requires a fresh
   request anchor in the new stream.

This first batch can ship independently and is expected to remove most
wrong-turn completion and long-session fallback drift.

### Deferred From First Batch

Do not make these blockers for the first batch:

- `provider_accepted_at` as a new field. Reuse `delivery_state == "accepted"`
  first; add the timestamp later for diagnostics.
- full mailbox lineage gate for every chain path. Keep as a second batch
  hardening item after provider-turn correctness is proven.
- clear barrier. Keep it in the plan, but do not wire it directly into
  `project_clear.py` until the dispatcher integration point is selected.

## Gate Placement

Preferred first implementation hook:

- `lib/ccbd/services/dispatcher_runtime/polling_service.py`
  `_resolve_update_decision`;
- also cover terminal decisions produced by `_tick_tracker`.

The review discourages placing the gate in terminal persistence because that is
too late in the flow. Normalize the decision before `dispatcher.complete(...)`
is called.

## Clear Barrier Guidance

The review flags clear barrier as the largest integration complexity.

Current `project_clear.py` is a tmux-pane handler and does not directly own
dispatcher state. Therefore:

- do not directly resolve active jobs inside the pane clear helper as the first
  implementation;
- prefer a decoupled clear-pending signal that dispatcher/tick processing can
  consume;
- when implemented, resolve the active job as incomplete before relying on any
  post-clear provider evidence.

The semantic direction remains:

- not provider accepted -> `clear_before_provider_acceptance`;
- provider accepted without terminal -> `clear_during_provider_turn`;
- terminal already durably recorded -> leave terminal result unchanged.

## Mandatory First Tests

The first batch needs tests for:

- terminal item before anchor cannot complete;
- anchor seen plus non-empty terminal can complete;
- `SESSION_ROTATE` followed by terminal without a fresh anchor is incomplete;
- fallback can find an anchor candidate but cannot change acceptance or
  complete the job;
- empty terminal remains incomplete;
- explicit `no_wrap` path still completes normally;
- failed delivery state remains failed and is not re-normalized.

Second-batch tests:

- clear barrier active-job incomplete results;
- B -> C -> A lineage gate;
- WSL/mac large-session fallback diagnostics.

## Risks

- fallback rebind may be the only legal recovery in some existing scenarios, so
  the first patch should quarantine it from success completion without deleting
  the diagnostic/recovery path;
- the gate needs access to runtime-state acceptance facts near
  `_resolve_update_decision`;
- `no_wrap` must remain explicitly exempt from anchor requirements.

## Decision

Adopt the coworker narrowing:

1. first implement provider-acceptance, fallback-quarantine, and session-rotate
   hard gates;
2. then add reply non-empty and lineage hardening where not already covered;
3. then add clear barrier through a dispatcher-owned or dispatcher-consumed
   signal, not by making the pane clear helper own job completion.

## Follow-Through

The first batch was implemented according to this narrowing:

- dispatcher hard gate is placed before `dispatcher.complete(...)`;
- Codex active completed decisions require `delivery_state == "accepted"` plus
  anchor evidence, except explicit `no_wrap`;
- broad Codex anchor fallback is quarantined as diagnostic/recovery evidence;
- session rotate without fresh anchor is normalized to incomplete;
- clear barrier, `provider_accepted_at`, and full chain-lineage hardening remain
  second-batch work.
