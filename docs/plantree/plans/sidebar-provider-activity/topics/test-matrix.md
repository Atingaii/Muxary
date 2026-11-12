# Sidebar Provider Activity Test Matrix

## 1. Purpose

This plan defines the validation strategy for provider-native activity signals
used by `ccbd project_view` and rendered by `ccb-agent-sidebar`.

The target is to prove that sidebar state is accurate across normal turns,
manual pane usage, CCB-managed jobs, provider errors, interrupted work, and
network/API failures.

The sidebar remains a read-only `project_view` client. Tests must validate the
`provider signal -> CCB activity artifact -> project_view -> sidebar` chain
instead of teaching the Rust sidebar to read provider files directly.

## 2. Test API Isolation

Status tests must not depend on the developer's normal global provider account,
global provider home, terminal profile, or tmux config.

Use a dedicated smoke project such as:

```text
/home/bfly/yunwei/test_ccb2
```

Use agent-local API authority in `.ccb/ccb.config`:

```toml
version = 2
entry_window = "main"

[windows]
main = "agent1:codex, agent2:codex"
review = "agent3:claude"
fault = "agent4:claude"

[agents.agent1]
key = "$CCB_TEST_OPENAI_KEY"
url = "$CCB_TEST_OPENAI_BASE_URL"

[agents.agent2]
key = "$CCB_TEST_OPENAI_FAULT_KEY"
url = "$CCB_TEST_OPENAI_FAULT_BASE_URL"

[agents.agent3]
key = "$CCB_TEST_ANTHROPIC_KEY"
url = "$CCB_TEST_ANTHROPIC_BASE_URL"

[agents.agent4]
key = "$CCB_TEST_ANTHROPIC_FAULT_KEY"
url = "$CCB_TEST_ANTHROPIC_FAULT_BASE_URL"

[ui.sidebar]
mode = "every_window"
width = 32
bottom_height = 20
```

The real config should materialize literal keys or a local generated config
from a private `.env` file. Do not commit secrets.

Recommended API lanes:

- stable Codex lane: valid key, normal OpenAI-compatible base URL
- fault Codex lane: valid key routed through a local controllable proxy
- stable Claude lane: valid key, normal Anthropic-compatible base URL
- fault Claude lane: valid key routed through a local controllable proxy
- invalid-auth lane: wrong key, real or mock base URL
- invalid-model lane: valid key with an unavailable model override

The fault lanes should be separate agents so a failure drill does not corrupt
the known-good baseline panes.

## 3. Signal Contract Tests

These tests are fast unit tests. They do not launch real providers.

Required coverage:

- activity writer accepts provider event payloads and writes atomic JSON
- malformed hook stdin exits successfully and writes a degraded diagnostic or no
  status, never blocking provider execution
- activity reader rejects missing, malformed, stale, wrong-provider,
  wrong-agent, wrong-pane, wrong-generation, and future-timestamp artifacts
- state mapping:
  - `active` and `tool` map to `activity_state=active`
  - `waiting` maps to `activity_state=pending`
  - `idle` maps to `activity_state=idle`
  - `failed` maps to `activity_state=failed`
- freshness expiry prevents permanent active state when `Stop` never arrives
- CCB ownership/lifecycle guards win over provider artifact
- CCB job/message state is metadata, not primary execution-state authority
- runtime fault, stopped agent, missing pane, and failed reconciliation win over
  provider artifact
- pane text fallback is used only when no fresh provider evidence exists
- runtime status smoothing keeps `working` visible through a short transient
  idle gap, then returns to `idle` only after confirmation
- high-confidence `waiting_for_user`, `failed`, and `offline` states bypass
  ordinary display smoothing when they need user attention
- stale working evidence crosses the stalled threshold instead of remaining
  active forever
- previous-status smoothing resets when runtime generation or pane ownership
  changes

## 4. Provider Hook Tests

These tests execute the hook helpers directly with captured or synthetic JSON.

Codex cases:

- `SessionStart` writes `idle`
- `UserPromptSubmit` writes `active`
- `PreToolUse` writes `active` with compact tool metadata
- `PermissionRequest` writes `pending`
- `PostToolUse` writes `active`
- `Stop` writes `idle`
- failure/system-error style payload writes `failed` when Codex exposes one

Claude cases:

- `UserPromptSubmit` writes `active`
- `PreToolUse` writes `active`
- `PostToolUse` writes `active`
- `Notification` maps to `pending` when it requests user attention
- `Stop` writes `idle`
- `Stop` with running `background_tasks` keeps `active`
- `system/api_error` writes `failed` with compact error fields

Privacy assertions:

- no full prompt text is stored
- no full assistant reply is stored
- keys/tokens are never stored
- transcript paths may be stored only as runtime evidence when already present
  in managed provider records

## 5. ProjectView Integration Tests

These tests call `ProjectViewService` with fake dispatcher/runtime/tmux facts.

Required scenarios:

- every agent row keeps backward-compatible `activity_state` fields and also
  exposes redacted structured `runtime_status`;
- no active CCB job, fresh Codex activity `active` -> agent row `active`
- no active CCB job, fresh Claude activity `active` -> agent row `active`
- fresh `waiting` -> row `pending`
- fresh `failed` -> row `failed`
- fresh `failed` plus idle pane text -> row stays `failed`
- fresh `failed` plus next provider turn -> row changes to `active`
- stale `active` plus idle pane text -> row `idle`
- stale `active` plus missing pane -> row `failed` or `offline` according to
  existing runtime health rules
- CCB running job plus fresh provider `failed` -> agent row shows failed
- CCB running job plus fresh provider `idle` -> agent row follows provider
  activity unless lifecycle/recovery guards override it
- terminal failed job may appear in Comms, but Comms failure does not by itself
  make the agent row failed without provider/runtime evidence
- cache hit path does not call tmux or reread provider artifacts unnecessarily
- one ProjectView build reads each activity artifact at most once per agent
- repeated ProjectView builds do not oscillate `runtime_status.state` when raw
  evidence alternates within the configured smoothing windows
- Codex visible `working`/`tool_running`/`reconnecting` pane status remains
  active even when the status line is unchanged for more than 60s
- Codex pane without an active status line becomes display `free` after 60s of
  unchanged pane content with reason `codex_pane_no_active_stale_no_progress`
- Codex pane without an active status line resets the 60s no-progress timer
  when pane content changes
- Claude runtime status is derived from provider activity hooks, the bound
  Claude JSONL session path, and narrow explicit Claude pane status shapes
- Claude running job with no hook/session signal renders `start`/pending
  instead of being inferred as active or idle
- Claude runtime with no active job and no session path renders `free` by
  explicit clean-start rule; malformed or unclassified session evidence remains
  `unknown`
- Claude visible `Thinking ..., running N shell command`, spinner status rows,
  scheduled tasks, and shell-still-running rows render active/tool-running even
  if a stale hook/session says idle
- Claude `Thought for ... ran ...` and `Sautéed for ...` rows are terminal
  summaries only; they do not complete jobs, but they can release stale active
  hook evidence after the no-progress window
- Claude prompt visibility (`❯`) is not idle/free authority

Performance assertions:

- no global tmux session scan
- no global provider-home scan
- no large transcript scan from the sidebar refresh path
- Codex and Claude use one cached per-pane `capture-pane` read per ProjectView
  build when runtime status needs pane evidence
- per-pane `capture-pane` fallback is throttled and reused within the configured
  minimum capture interval

## 5.1 Mobile Gateway Status Tests

Mobile gateway should consume ProjectView status, not reinvent provider state.

Required scenarios:

- conversation `status_event` summary is derived from `activity_state` and
  `runtime_status`, not a separate coarse agent state fallback;
- `runtime_status` fields exposed through mobile APIs are redacted and compact;
- legacy clients still receive a plain status summary;
- stale-active, waiting-for-user, reconnecting/stalled, and failed states
  produce user-readable summaries suitable for the mobile conversation header;
- rapid ProjectView refreshes do not generate alternating active/idle mobile
  status events for one unresolved provider turn;
- no prompt text, reply text, API key, OAuth token, or full transcript body is
  emitted through status fields.

## 5.2 Codex Pane Probe Spike

Before production Codex status-line parsing lands, run the independent probe
from
[codex-pane-status-probe-spike.md](codex-pane-status-probe-spike.md).

Required scenarios:

- startup-idle: Codex pane starts, pane facts are recorded, and the current
  screen establishes the input-ready baseline;
- quick-turn: a short prompt produces `working -> idle` evidence with
  first-output latency;
- long-tool: a visible multi-second command/tool run produces fresh output and
  active state evidence;
- interrupt: Escape/Ctrl-C during work does not leave status permanently
  active;
- pane-death: killing the dedicated test pane reports pane death and stops
  parsing stale output;
- stale-scrollback: old `Working (...)` text before a newer idle prompt does
  not keep the state active;
- approval-wait and API/model/auth failure either pass in a credential-enabled
  lane or produce explicit skip reasons.

Required artifacts under `/home/bfly/yunwei/test_ccb2`:

- redacted `run.json` summary;
- timestamped `events.jsonl` and `snapshots.jsonl`;
- raw and normalized pane-output logs kept private unless sanitized;
- capture samples for each `capture-pane` variant under test;
- `metrics.json` with output latency, capture count, capture duration, and
  parser mismatch counts.

Promotion gate:

- only sanitized probe fixtures may be committed;
- Codex parser tests must cite the fixture scenario they cover;
- parser scope is limited to high- or medium-confidence patterns observed by
  the probe;
- low-confidence provider copy remains display detail or `unknown/pending`
  evidence, not a hard status transition.

## 6. Fault Injection Tests

Fault injection must cover errors that users actually see as "agent is stuck" or
"sidebar says idle while the model failed".

Automatable with mock or proxy:

- connection refused before request starts
- connection drop after request starts
- HTTP 401/403 invalid auth
- HTTP 404/400 unavailable model
- HTTP 429 rate limit
- HTTP 500/502/503 provider outage
- slow streaming with no tokens for longer than activity TTL
- stream starts, then closes without terminal provider event
- provider CLI exits while pane remains alive
- pane is killed while provider activity says `active`
- hook command fails or times out
- activity file write fails because the directory is temporarily unwritable
- provider `failed` followed by an idle prompt remains `failed`
- provider `failed` followed by the next `UserPromptSubmit` becomes `active`

Expected outcomes:

- CCB-managed jobs terminalize as `failed` or `pending/recoverable` according to
  completion reliability rules
- manual pane activity does not remain `active` forever
- sidebar shows `failed` when provider evidence is a real terminal failure, and
  keeps it visible until the next provider turn or runtime ownership change
- sidebar shows `pending` when evidence is inconclusive but the provider may
  still be recovering
- every failure leaves diagnostics explaining the source:
  `provider_activity`, `runtime_health`, `pane_liveness`, `provider_pane`, or
  `ccb_metadata`

## 7. Live Manual Test Matrix

Run these in `/home/bfly/yunwei/test_ccb2` with the development build installed
or explicitly launched from the test checkout.

Baseline startup:

- `ccb kill -f`
- remove `.ccb` in the test project
- write the dedicated test config
- `ccb`
- verify every window has a sidebar and all agents start as `idle`

Codex manual pane:

- click `agent1`
- type a manual prompt
- sidebar changes `idle -> active` within two refresh intervals
- let it finish
- sidebar returns `active -> idle`

Claude manual pane:

- click `agent3`
- type a manual prompt
- sidebar changes `idle -> active`
- force a tool call if possible
- verify tool execution does not show idle
- let it finish
- sidebar returns to idle

CCB-managed job:

- run `ccb ask agent1 "short task"`
- verify provider activity drives sidebar active/pending while job metadata is
  available for diagnostics
- verify completion returns to idle
- repeat for Claude

Interrupt:

- start a long manual task
- press Escape or run `ccb cancel <agent>`
- verify sidebar leaves active and does not get stuck

API disconnect:

- start work on the fault lane
- cut proxy connectivity after provider begins work
- verify job/manual activity transitions to failed or pending, not idle
- restore proxy
- submit a new task
- verify state recovers without `ccb kill`

Invalid auth:

- use a known bad key on a fault agent
- start a task
- verify `failed` with auth/API diagnostic

Unavailable model:

- configure a bad model only for one test agent
- start a task
- verify `failed` with model/API diagnostic

Pane death:

- start active work
- kill the agent pane
- verify sidebar reports recovery pending or failed according to reconciliation
- verify no stale activity file keeps it active

Sidebar restart:

- kill only the sidebar pane
- verify it respawns and reflects the same state from `project_view`
- no provider hook or job state should be lost

Window switch and resize:

- while an agent is active, switch windows
- verify every sidebar instance shows the same agent state
- resize sidebar width in one window
- verify synchronized width does not affect state polling

## 8. Acceptance Criteria

The feature is not ready until all of these hold:

- manual Codex work is not shown idle while a turn is active
- manual Claude work is not shown idle while a turn is active
- CCB-managed jobs and manual pane turns share provider-native execution-state
  detection
- API/auth/model failures are visible as failure or recoverable pending states
- provider failures remain visible until the next provider turn or runtime
  ownership change
- no activity state can remain active forever without fresh evidence
- stale/wrong artifacts are ignored
- provider activity does not increase ProjectView CPU hotspots
- sidebar behavior is project/session scoped and does not require global tmux or
  terminal settings
- diagnostic output can explain why each row chose its state

## 9. Release Gate

Before release, run:

- focused unit tests for activity writer/reader/resolver
- provider hook helper tests for Codex and Claude
- Codex pane probe spike with redacted fixture summary for parser-backed
  patterns
- full `pytest -q`
- Rust sidebar tests
- compile checks
- live `/home/bfly/yunwei/test_ccb2` smoke for stable lanes
- live fault-lane smoke for disconnect, invalid auth, and unavailable model

If real provider fault lanes cannot be run in CI, keep them as an explicit
manual release checklist item and attach the observed `project_view` records to
the release validation notes.
