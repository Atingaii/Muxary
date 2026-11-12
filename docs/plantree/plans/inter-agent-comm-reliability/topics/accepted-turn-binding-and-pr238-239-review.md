# Accepted Turn Binding And PR238/239 Review

Date: 2026-07-06

## Status

Planning and review record only. Do not merge PR238 or PR239 from this note.

The current communication-stability investigation is about cases where an ask
appears delivered but later produces an empty reply, no reply, a reply routed to
the wrong caller, or a blocked queue after provider context clear or large
provider session files. Reports concentrate on WSL and macOS, but directory
drift before the project-local ask routing fix was also observed on Linux.

## Problem Statement

The failure family is not explained by the later project-boundary tightening
for `ask`; users saw it before that change.

The risky boundary is provider turn identity:

- A successful tmux paste only proves text was sent to a pane, not that the
  provider accepted it as the current request.
- A provider session file being readable only proves a session exists, not that
  the observed events belong to the current job after clear, rotate, truncation,
  or stale reader binding.
- A hook, idle pane, or terminal boundary can be stale or unrelated unless it
  is tied to the current request anchor and provider epoch.
- Empty reply is never success. It must be classified as incomplete or failed
  with evidence.
- Unknown state must not be promoted to completed.

The desired stable behavior is not "always return something". It is "never
misclassify": if the provider is still genuinely running, keep waiting; if CCB
cannot prove current-turn ownership, report a degraded/incomplete state with
specific evidence instead of completing the job silently or delivering to the
wrong caller.

## Required Stability Boundary

Future source changes should converge on these invariants:

1. Accepted turn binding.
   A job should only move from delivered to accepted/running after the current
   request anchor or request id is observed in the active provider stream.

2. Provider epoch.
   Clear, manual provider clear, session path change, session id change, file
   truncation, offset rollback, or session rotation must create a new evidence
   epoch. Only events from the same epoch can complete the job.

3. CCB-owned event index.
   Provider sessions can remain the raw source, but CCB should tail them
   incrementally and persist compact per-agent/per-job evidence. Normal reply
   lookup should read CCB-owned evidence, not repeatedly rescan huge provider
   transcripts.

4. Reply delivery acknowledgement.
   B-to-A reply delivery should not be considered fully delivered merely
   because a prompt was pasted. Durable mailbox state and, when possible,
   recipient-side accepted evidence should distinguish pending, accepted,
   stalled, and failed delivery.

5. Project-local ask routing.
   Plain `ask` should route inside the current `.ccb` project anchor even if an
   agent's shell cwd drifts. Cross-project sends should require an explicit
   dangerous/remote project argument that names the target CCB project path.

## PR238 Review

PR: `https://github.com/SeemSeam/claude_codex_bridge/pull/238`

Title: `feat(completion): split empty reply reason into model_empty_output / delivery_late_empty / api_empty_after_error`

State at review time:

- Open.
- Target: `main`.
- Merge state: conflicting/dirty against current `origin/main`.
- Scope: 2 commits, 13 files.
- Current `origin/main` still uses the generic `task_complete_empty_reply`
  reason in the completion detectors at review time.

Useful changes:

- Splits the old generic `task_complete_empty_reply` into:
  `model_empty_output`, `delivery_late_empty`, and `api_empty_after_error`.
- Propagates Codex `api_error_seen` into turn-boundary payloads.
- Adds tests for empty-boundary classification.

Assessment:

- This is a good diagnostic improvement.
- `delivery_late_empty` is particularly useful because it names the exact class
  that suggests prompt delivery failure or stale reader binding.
- It does not by itself stabilize communication. It classifies an already-empty
  terminal boundary after the fact.
- It does not add accepted-turn gating, provider epoch isolation, durable event
  indexing, or reply-delivery acknowledgement.

Adoption guidance:

- Reasonable to rebase and consider as a small diagnostic slice.
- Do not treat it as a root fix for WSL/mac clear-session instability or wrong
  caller delivery.

## PR239 Review

PR: `https://github.com/SeemSeam/claude_codex_bridge/pull/239`

Title: `feat(provider): Wave 1.5/2/3/4 obs, identity, quota, CLI probes`

State at review time:

- Open.
- Target: `main`.
- Mergeable according to GitHub, but based on an old feature branch.
- Scope is very large: provider observation, no-reply taxonomy, queue tagging,
  Kimi sentinel completion, Rust shims, CLI probes, and Codex fallback timeout.
- Current `origin/main` still has Codex `no_terminal_timeout_s = 0.0` at review
  time; the PR's 900 second default has not been adopted there.

Communication-stability-relevant pieces:

- Bounded tmux `capture-pane` / pane-alive queries with a 2 second timeout.
- `NoReplyReason` taxonomy plus `ccb why` style surfacing.
- Provider pane high-confidence error terminalization for quota/auth/API/config
  failures.
- Reply delivery stalled tagging for replies that remain unconsumed.
- Busy-queue tagging for jobs blocked behind a stale busy slot.
- Kimi `CCB_DONE:<anchor>` sentinel completion.
- Codex `no_terminal_timeout_s = 900.0` fallback that terminalizes as degraded
  after 15 minutes without protocol terminal evidence, with optional reply
  harvest from runtime state.

Assessment:

- Several pieces improve observability and reduce indefinite queue blockage.
- The bounded tmux query change is a clean hygiene improvement.
- The no-reply taxonomy is valuable if every non-success terminal state is
  backed by evidence and no silent success is created.
- Kimi sentinel completion is a provider-specific stronger completion signal.
- The Codex 900 second fallback is not a root stability fix. It changes the
  contract from "wait for provider/completion authority while the provider is
  alive" to "release the queue after a bounded degraded timeout". This may be
  operationally useful, but it can still terminate a long-running valid Codex
  job if the protocol terminal event is missing or delayed.
- Pane-content terminalization remains heuristic. High-confidence marker tests
  reduce false positives, but stale/truncated pane capture on WSL/mac is still
  not the same as current-turn proof.
- Reply-delivery stalled tagging identifies unconsumed replies; it does not
  prove recipient-side acceptance or repair wrong-caller routing.
- The branch is too broad to merge as a communication-stability fix. It mixes
  unrelated Rust shims and provider-observation work with reliability behavior.

Adoption guidance:

- Do not merge PR239 wholesale for communication stability.
- Peel small candidates only after rebase and targeted tests:
  bounded tmux query timeouts, no-reply taxonomy, and possibly PR238-style
  empty-reply classification.
- Keep Codex bounded terminalization behind an explicit policy decision. It
  should not replace accepted-turn binding and provider-epoch ownership.

## Recommended Next Slice

Do not start with more fallback timeout logic. First implement the ownership
boundary that prevents false attribution:

1. Add an accepted-turn state transition and tests: delivered is not accepted
   until the current request anchor is observed.
2. Add provider epoch evidence and epoch mismatch handling for clear, manual
   clear, session rotation, offset rollback, and truncation.
3. Persist compact CCB-owned provider event evidence keyed by agent/job/epoch.
4. Update empty-reply and no-reply handling so empty or unknown states can only
   become incomplete/failed with evidence, never completed.
5. Add WSL/mac stress tests for large sessions, clear-before-ask,
   clear-during-busy, old-job-blocks-new, reply-to-wrong-caller, and multi-hop
   chain ask.

## Test Gates

Before landing any stability change in this area, require:

- Unit tests for accepted-turn transition, provider epoch mismatch, and empty
  boundary classification.
- Integration tests where a stale session boundary appears before the current
  request anchor.
- Large-session replay tests that exercise EOF tailing, offset rollback, and
  full-rescan fallback.
- WSL/mac manual probe results using the documented communication-stability
  test package.
- Chain tests for A to B to C with multiple B-C rounds before B replies to A.
