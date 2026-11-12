# Agent Runtime Status V1

Date: 2026-06-28

Role: Solution map
Status: Draft - Phase 2 design
Read when: Improving provider working-state accuracy for ProjectView clients
such as the sidebar and CCB Mobile.

## Phase Boundary

This document describes the later structured `runtime_status` resolver and
publisher. It is not the PR1 contract for provider pane parsing.

Phase 1 is limited to the pane observation module described in
[provider-pane-status-signal-module.md](provider-pane-status-signal-module.md):
shared pane-observation models plus the Codex pane parser only. PR1 must not
synthesize `idle`, `stalled`, `confidence`, `elapsed_seconds`, or
`last_output_at` from pane evidence alone.

The target model, transition table, smoothing policy, and `stalled` state below
apply only after a second provider or consumer creates a real generic resolver
need.

## Goal

Build a normalized source-side agent runtime status layer so clients can show
accurate "working / waiting / reconnecting / failed / idle" state without
parsing Codex, Claude, tmux, or CCB job details themselves.

The first provider-specific improvements should target Codex and Claude, but
the implementation path should be generic first:

```text
provider hooks + pane/status-line evidence + CCB job/runtime facts
  -> normalized AgentRuntimeStatus
  -> project_view agent record
  -> sidebar / mobile gateway / future clients
```

## Current State

Existing source code already has the first version of activity inference:

- `provider_hooks.activity` writes scoped `activity.json` evidence from provider
  hooks.
- `ccbd.project_view.provider_activity` validates provider, project, agent,
  runtime session, pane, and workspace identity.
- `ccbd.project_view.activity.resolve_agent_activity()` merges lifecycle guards,
  provider activity, CCB job state, callback waiting state, pane text, and
  runtime health into `activity_state`, `activity_source`, and
  `activity_reason`.
- `mobile_gateway.service` currently flattens agent status into a plain
  `status_event` body, losing most useful state detail for mobile clients.

This is a useful base, but it is still too coarse for mobile or sidebar status
surfaces that may eventually need to distinguish:

- model is actively working;
- provider is waiting for approval/input;
- provider is reconnecting, and later possibly a distinct stalled state when a
  non-pane signal can prove it;
- background terminal/tool work is still running after the main prompt returns;
- CCB job metadata exists but provider is actually idle;
- provider hook evidence is stale and should no longer keep an agent active.

## Target Model

Add a structured runtime status object while keeping existing
`activity_state/activity_reason/activity_source` fields for compatibility.

Suggested record under each `project_view.view.agents[]` item:

```json
{
  "runtime_status": {
    "state": "working",
    "label": "Working",
    "detail": "1h 54m · 2 background terminals · esc to interrupt",
    "provider": "codex",
    "source": "provider_pane",
    "reason": "codex_working_status_line",
    "updated_at": "2026-06-28T00:00:00Z",
    "stable_since": "2026-06-28T00:00:00Z",
    "started_at": "2026-06-27T22:05:00Z",
    "background_terminal_count": 2,
    "interruptible": true,
    "action_hint": "/ps to view",
    "current_job_id": "optional"
  }
}
```

Initial normalized `state` values:

| State | Meaning |
| :--- | :--- |
| `idle` | Resolver-synthesized idle from an explicit idle authority; never emitted by the pane parser merely because work evidence is absent. |
| `working` | Provider is generating, running tools, or has active background work. |
| `waiting_for_user` | Provider requires approval, trust, input, or permission. |
| `queued` | CCB work is queued/accepted but not yet provider-active. |
| `reconnecting` | Stream/session/network evidence suggests recovery in progress. |
| `stalled` | Deferred until hook, process, protocol, or another non-pane progress source can prove active work plus missing progress. |
| `failed` | Provider/runtime/pane evidence indicates terminal failure. |
| `offline` | Namespace/runtime/pane ownership is not currently mounted/alive. |
| `unknown` | Source cannot classify safely. |

The existing five-color `activity_state` can derive from this model:

- `working` -> `active`
- `waiting_for_user`, `queued`, `reconnecting`, deferred `stalled`, `unknown` ->
  `pending`
- `idle` -> `idle`
- `failed` -> `failed`
- `offline` -> `offline`

## Evidence Sources

Use a layered resolver with explicit provenance.

1. **Lifecycle guard**: namespace, stopped state, runtime fault, pane death, and
   reconciliation failure still override everything.
2. **Fresh provider hook evidence**: event-state evidence from Codex/Claude
   hooks is strong while identity and freshness checks pass.
3. **Provider pane/status-line evidence**: recent tmux pane tail parsed by
   provider-specific adapters.
4. **CCB job/callback metadata**: queued/running/waiting records enrich status
   but should not by themselves prove provider execution.
5. **Runtime health/pane liveness fallback**: conservative `pending` or
   `unknown` only unless another explicit idle authority exists.

Important rules:

- Fresh provider failure remains sticky until next turn or runtime ownership
  changes.
- Fresh active hook can be downgraded only by a stronger explicit idle authority
  for the same pane/session. A visible input prompt alone is not sufficient.
- CCB job `running` without provider working evidence should not mask an idle
  provider forever.
- Stale working evidence should degrade to `pending` in the first resolver
  slice. A distinct `stalled` state is deferred until a non-pane progress
  source exists.
- Transition decisions must include source-side smoothing so sidebar and mobile
  clients do not independently debounce or flicker on every refresh.
- Pane/status-line capture must be throttled and reused; a `project_view`
  refresh must not imply an unconditional `capture-pane` for every agent.
- No prompt text, reply text, API key, OAuth token, or full transcript content
  may be stored in runtime status.

## Stability And Refresh Policy

`runtime_status` is a read model for display and diagnostics. It is not reload,
unload, cancellation, or completion authority. Runtime ownership, job records,
and provider completion contracts remain the control-plane sources for those
decisions.

This section is Phase 2. It must not be implemented inside the PR1
`provider_pane_status` extraction.

The resolver should separate raw evidence from the published status:

- Raw evidence may be short-lived hook events, pane/status-line snippets, CCB
  job metadata, or runtime liveness facts.
- Published `runtime_status.state` is stabilized with freshness windows,
  transition hysteresis, and previous status only when the previous status still
  belongs to the same project, agent, runtime generation, and pane.
- Downstream clients should consume the stabilized `project_view` result rather
  than implementing their own provider parsing or debounce logic.

Initial transition policy:

| Transition | Policy |
| :--- | :--- |
| Any -> `offline` | Immediate when lifecycle/runtime/pane ownership is invalid. |
| Any -> `failed` | Immediate on explicit provider/runtime failure, then sticky until next provider turn or runtime ownership change. |
| Any -> `waiting_for_user` | Immediate on explicit approval, permission, trust, or input evidence. |
| `working` -> `idle` | Requires explicit idle authority plus a short idle confirmation window; prompt visibility alone does not qualify. |
| `working` -> `stalled` | Deferred until active work evidence and a non-pane progress source can prove missing progress past a threshold. |
| `idle` -> `working` | Immediate on fresh hook or strong pane/status-line evidence. |
| Any -> `reconnecting` | Requires disconnect/reconnect evidence, with a short grace window before calling it stalled or failed. |
| CCB job-only `running` -> provider unknown | Do not stay `working`; expose running job metadata beside provider `unknown`. |

Suggested first tuning values, to be adjusted after live validation:

- `working_min_hold_s`: 2 seconds, preventing active/idle flicker during short
  status-line gaps.
- `idle_confirm_s`: 2 seconds, requiring explicit idle authority to remain
  stable before leaving `working`.
- `pane_capture_min_interval_s`: 1-2 seconds per pane when pane evidence is
  needed; fresh hooks should avoid capture entirely.
- `reconnect_grace_s`: 2-5 seconds before turning a transient disconnect into
  user-visible reconnecting/stalled detail.
- `stalled_after_s`: deferred until a non-pane progress source exists.

If implementation needs previous-status memory, keep it as a small in-memory
ProjectView/runtime cache keyed by project id, agent name, runtime generation,
and pane id. Reset it on ownership changes so old status cannot leak across
agent reloads, slot replacement, or pane recreation.

## Generic Resolver Slice

Before the generic resolver lands, extract the provider pane parsing surface
described in
[provider-pane-status-signal-module.md](provider-pane-status-signal-module.md).
That package is generic by boundary (`provider_pane_status`) but intentionally
small in its first landing: shared models plus the Codex pane parser only.
It must not introduce a resolver, compatibility adapter, smoothing, or fallback
mapping until a second provider or consumer creates a real composition need.

When a generic resolver becomes justified by a second provider or consumer, it
should:

- introduce an `AgentRuntimeStatus` data model;
- add a resolver that maps current `AgentActivityFacts` plus optional parsed
  provider details into structured status;
- apply the source-side stability and refresh policy before publishing
  `runtime_status`;
- preserve all current `activity_state` values as compatibility output;
- expose `runtime_status` in `project_view` agent records;
- keep status observation separate from reload/unload/completion authority;
- add focused tests for lifecycle guard, provider activity, stale hook, CCB job,
  callback wait, pane fault, smoothing, throttling, and fallback cases.

This makes later provider adapters small and reviewable.

## Codex Adapter Slice

Read
[codex-pane-status-probe-spike.md](codex-pane-status-probe-spike.md)
before implementing Codex pane/status-line parsing. The first parser should be
backed by sanitized probe fixtures from a disposable tmux run under
`/home/bfly/yunwei/test_ccb2`, not by guessed provider copy.

Codex parsing should recognize recent pane/status-line forms such as:

- `Working (1h 54m 08s • esc to interrupt)`
- `Working (...) · 2 background terminals running · /ps to view`
- `Messages to be submitted after next tool call`
- `stream disconnected before completion`
- provider/API/rate-limit text already covered by terminal error markers
- explicit terminal summaries such as `Worked for ...`

Extract when possible:

- interruptibility;
- background terminal count;
- action hint such as `/ps to view`;
- reconnect/failure reason;
- compact label/detail for clients.

Do not extract Codex visible UI timers as lifecycle elapsed time in the pane
parser. `stalled` and resolver-synthesized `idle` are Phase-2 concepts; prompt
visibility is not idle authority in the pane parser.

Acceptance criteria:

- Codex active work is `working` even with no CCB job.
- Background terminals keep status `working` until current pane evidence shows
  they have stopped.
- Old working scrollback before a newer explicit hard marker does not keep
  status active.
- Parser coverage cites probe scenarios for every hard transition pattern.
- `/status` output and other provider text are rendered as conversation/pane
  content, not confused with status authority unless they match known status
  patterns.

## Claude Adapter Slice

Claude parsing should recognize recent pane/status-line forms such as:

- scheduled tasks still running;
- shell/tool still running;
- user permission/input required;
- API/auth/model errors;
- interrupted or cancelled turns;
- explicit idle/ready authority if Claude exposes one. Prompt visibility alone
  is not enough.

Hook evidence remains preferred when Claude provides a meaningful event, but
pane evidence should fill gaps for long-running tool/shell work.

Acceptance criteria:

- Tool/shell execution is `working`, not `idle`.
- Permission/input prompts are `waiting_for_user`.
- API/auth/model failures are `failed` with compact reason.
- Stop events with background tasks remain `working` until bounded freshness
  rules degrade them.

## ProjectView And Mobile Gateway Exposure

`project_view` is the authority boundary. Downstream clients should not parse
provider pane text.

Required exposure:

- keep existing `activity_state`, `activity_symbol`, `activity_color`,
  `activity_source`, and `activity_reason`;
- add structured `runtime_status`;
- include only redacted, compact fields safe for project view and mobile
  gateway transport;
- update mobile gateway conversation status events to use `activity_state` and
  `runtime_status`, not a separate coarse `agent.state` summary.

CCB Mobile can then render a status strip above the conversation, for example:

```text
Working · 1h54m · 2 background terminals · /ps to view
Waiting for permission
Reconnecting...
Stalled · no protocol progress for 2m
```

## Test Plan

Direct tests:

Phase-2 resolver tests:

- normalized model maps to existing compatibility `activity_state`;
- lifecycle guard wins over hook and pane evidence;
- fresh hook active/idle/waiting/failed cases;
- explicit waiting and failed evidence enters immediately;
- `working` minimum hold prevents one-refresh active/idle flicker;
- idle confirmation requires explicit idle authority, not a transient prompt
  capture;
- stale hook plus explicit idle authority downgrades to idle;
- stale hook without explicit idle authority degrades to pending;
- stale working evidence crosses a deferred stalled threshold only when a
  non-pane progress source exists;
- previous-status smoothing resets on runtime generation or pane ownership
  changes;

Provider pane parser tests:

- Codex working line with interrupt marker;
- Codex background terminal count and action hint;
- Codex historical working text before a newer hard marker ignored;
- Codex parser fixtures produced by the pane probe spike cover startup-idle,
  quick-turn, long-tool, interrupt, pane-death, and stale-scrollback;
- Claude scheduled task/shell running;
- Claude waiting-for-user notification/pane evidence;
- provider terminal errors map to failed and keep prompt/reply secrets redacted.

ProjectView tests:

- `runtime_status` appears on every agent row with backward-compatible
  `activity_state`;
- no extra `capture-pane` when fresh hook evidence is enough;
- bounded `capture-pane` when pane evidence is needed to disprove stale active;
- repeated ProjectView refreshes reuse recent pane evidence within the capture
  interval and do not make status oscillate;
- wrong project/agent/provider/session/pane/workspace evidence is ignored.

Mobile gateway tests:

- `/v1/projects/{id}/conversation` status event includes structured status or a
  summary derived from `runtime_status`;
- legacy clients still tolerate old fields;
- no raw provider transcript, prompt, API key, or token leaks in status fields.
- rapid ProjectView refreshes do not produce alternating mobile status events
  for the same unresolved provider state.

Live validation:

- use `/home/bfly/yunwei/test_ccb2`, not the source checkout itself;
- run one Codex and one Claude stable lane;
- start long work and verify `working` with elapsed/background detail;
- trigger waiting-for-user and verify `waiting_for_user`;
- trigger stream/API failure and verify `failed` or `reconnecting`;
- verify CCB Mobile displays status without parsing tmux text locally.

## Non-Goals

- Do not make mobile or sidebar read provider runtime files directly.
- Do not use global tmux or global provider-home scans.
- Do not change ask/dispatch/retry semantics in this phase.
- Do not store provider prompt/reply content in runtime status.
- Do not treat status as completion authority for jobs until a separate design
  explicitly promotes that behavior.
