# Provider Pane Status Signal Module

Date: 2026-06-29
Role: Landing plan
Status: PR1 landed; Codex ProjectView/sidebar slice landed
Read when: Extracting pane-text provider status parsing from the Codex probe
into production code, or adding Claude pane parsing later.

## Goal

Create a small provider pane-status signal module that exposes explicit,
provider-specific pane observations without turning them into job lifecycle
authority.

The module should make status parsing reusable by:

- the standalone Codex pane probe;
- `ccbd.project_view` activity/status rendering;
- future Claude and other CLI provider pane parsers.

The design principle is strict:

```text
unknown stays unknown
source failure stays visible
pane observation never completes a CCB job by itself
```

## Package Boundary

Use a provider-pane-specific package name:

```text
lib/provider_pane_status/
  __init__.py
  models.py
  codex_pane.py
  codex_session.py
```

Initial landing includes `models.py`, `codex_pane.py`, and the Codex-specific
`codex_session.py` supplement. Keep future Claude/Gemini session supplements
provider-specific until a second implementation proves shared code is useful.

Do not add these in the first landing:

- `resolver.py`
- `project_view_adapter.py`
- generic `AgentRuntimeStatus` publisher logic
- smoothing / hysteresis cache
- tmux capture or pipe-pane acquisition code
- control-plane completion code

Rationale:

- `provider_pane_status` names the source and prevents confusion with runtime
  or job authority.
- `models.py` gives Claude a stable future contract without forcing a generic
  resolver before a second provider exists.
- `codex_pane.py` keeps the first production parser focused and testable.

## Signal Model

The first model should represent pane observations, not lifecycle decisions.
Keep `models.py` deliberately small in v1.

Initial runtime model set:

- `ProviderPaneStatusSignal`
- `PaneCompletionEvidence`

Do not add independent `PaneSourceStatus` or `PaneParsedState` enum classes in
the first landing. Use `source_status: Literal["ok", "error"]` or equivalent
constants, and keep `parsed_state` as a string plus provider-local
`STATUS_CATALOG`. If Claude later proves that a shared enum removes real
duplication, introduce it then.

`PaneCompletionEvidence` replaces wording such as `terminal_outcome` in shared
production models. It means "visible pane evidence only". It must not be used
to call `dispatcher.complete()` or mutate a job status.

The `PaneCompletionEvidence` dataclass must carry this warning in its runtime
docstring:

```text
Pane completion evidence is observation only, not job lifecycle authority.
Passing it to dispatcher.complete() or using it to build a CompletionDecision
directly is a bug.
```

Add a marker method such as `__not_a_job_terminator__()` so tests can identify
the type and keep it out of dispatcher/completion authority paths.

Minimum fields:

```text
ProviderPaneStatusSignal
  provider
  source_status: ok | error
  parsed_state: string
  reason
  matched_patterns
  notes
  completion_evidence
```

Important split:

- `source_status=error` means capture/acquisition failed, for example tmux
  failed, timed out, or the pane id was invalid.
- `parsed_state=unknown` means capture succeeded but the parser found no known
  explicit provider state.

The parser should only classify text. It should not manufacture source errors.

## Codex Parser Rules

Move the current strict parser from
`scripts/probe_codex_pane_status.py` into `codex_pane.py`.

Carry forward the current hard rules:

- active states require Codex status-line-shaped rows;
- conversation body text and indented examples are not authority;
- `Reconnecting...` is a recoverable active state and wins over nearby
  stream-disconnect text;
- retry counts and visible UI seconds are not lifecycle timing signals;
- `Worked for ...` is sufficient pane completion evidence, but still only
  observation;
- prompt visibility, pane quiet, output freshness, and job-running metadata do
  not imply `idle`, `working`, or `completed`;
- `Conversation interrupted` is historical pane text unless paired with a
  current hard marker.
- ProjectView may apply an explicitly designed display stabilizer for Codex
  rows only after active pane evidence disappears: a visible Codex
  `Working (...)`, tool-running, or reconnecting status line remains active no
  matter how long it stays visible; if no active status line is present and pane
  content is unchanged for 60s, display runtime becomes `free` with reason
  `codex_pane_no_active_stale_no_progress`. This does not change parser
  output, does not imply completion, and must preserve raw state/reason in
  diagnostics.

Tighten during extraction rather than preserving known weak signals:

- waiting/user-input detection must be shape-aware enough to avoid generic
  body-text keyword matches;
- priority should be expressed as a visible table or ordered matcher list, not
  hidden as a long informal `if` chain;
- the probe script must not retain duplicate regex or parser constants after
  importing the shared module.

## ProjectView Integration

First ProjectView use should be direct and visible:

- `activity.py` calls the Codex pane parser for Codex panes.
- Codex-specific keyword scans in `_provider_working` and
  `_provider_terminal_error` are deleted instead of migrated.
- `provider_prompt_idle_after_request` and `provider_prompt_input_stuck` are
  deleted with their activity-status call paths. Prompt visibility is not a
  status or recovery authority.

Do not create a compatibility adapter in the first landing. If legacy
`activity_state` needs to remain present, map explicitly at the call site so
that `unknown` cannot be hidden behind a wrapper.

Required display behavior:

```text
job_status=running + pane parsed_state=unknown
  => expose both facts, do not synthesize working
```

If ProjectView needs a legacy single-field value before structured
`runtime_status` lands, unknown must map to an explicit unknown/pending reason,
not to idle, working, completed, or failed.

## Completion Boundary

Pane evidence is not job terminal authority.

Strong job lifecycle authority remains:

- `CompletionDecision`;
- provider protocol/session terminal events;
- hook artifacts when a provider contract declares them authoritative;
- reliability timeout terminalization, which should produce `incomplete`, not
  `completed`.

Pane completion evidence is useful for status display and diagnostics. It must
not bypass the existing completion pipeline.

## Fallback Decision

- failure handled: unknown text, ambiguous text, capture/acquisition failure,
  unsupported provider, missing completion evidence.
- continue or fail: continue rendering status, but surface `unknown` or
  `source_status=error`; do not substitute idle, working, completed, or failed.
- surfacing: status records carry `reason`, `source_status`, and matched
  evidence; capture failure is distinct from parse unknown.
- test: unknown mapping tests, capture-error tests, and ProjectView integration
  tests must prevent hidden fallback behavior.
- review needed: any future smoothing, stale-state reuse, or compatibility
  adapter must be separately reviewed because it can hide unknown evidence.

## Large File Decision

- file: `scripts/probe_codex_pane_status.py`
- signal: about 1000 lines mixing parser, tmux runner, prompt stimulus,
  timing, metrics, artifacts, and CLI.
- decision: extract the pure parser to `provider_pane_status.codex_pane`.
- rationale: extraction removes duplicated future parser logic while keeping
  runner behavior local to the demo script.
- verification: parser fixtures pass unchanged; script smoke output remains
  schema-compatible.

- file: `lib/ccbd/project_view/activity.py`
- signal: lifecycle guards, job/callback facts, pane heuristics, and provider
  text parsing share one module.
- decision: remove Codex-specific text heuristics from this file and call the
  shared parser directly. Do not grow a generic resolver here.
- rationale: provider parsing should be isolated; ProjectView should compose
  already-classified evidence.
- verification: ProjectView tests prove `unknown` is visible and not converted
  into a stronger state.

## Landing Sequence

PR1:

1. Add `lib/provider_pane_status/models.py` and
   `lib/provider_pane_status/codex_pane.py`.
2. Move the existing Codex parser fixtures under the new module tests and keep
   the current 28 behavior checks passing.
3. Update `scripts/probe_codex_pane_status.py` to import the shared parser;
   remove local parser constants and regex duplicates.
4. Add a smoke check proving probe artifact schema compatibility.

PR1 landed on 2026-06-29 with:

- `lib/provider_pane_status/models.py`
- `lib/provider_pane_status/codex_pane.py`
- `lib/provider_pane_status/codex_session.py`
- `test/test_provider_pane_status_codex.py`
- `test/test_provider_pane_status_codex_session.py`
- `scripts/probe_codex_pane_status.py` importing the shared parser and no
  longer retaining local `STATUS_MARKER_RE` or `CODEX_*_RE` duplicates.

Verification:

- `python -m py_compile scripts/probe_codex_pane_status.py
  lib/provider_pane_status/__init__.py lib/provider_pane_status/models.py
  lib/provider_pane_status/codex_pane.py
  lib/provider_pane_status/codex_session.py`
- `python -m pytest -q test/test_provider_pane_status_codex.py
  test/test_provider_pane_status_codex_session.py
  test/test_codex_pane_status_probe.py` -> `49 passed`
- Live test-home run:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T133020Z-2455185/artifacts/run.json`
  observed `unknown -> working -> unknown`, capture p95 1.6 ms, zero 1 s
  flicker transitions, and no completion without `Worked for ...`.
- Live isolated no-login run:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T133248Z-2540939/artifacts/run.json`
  observed `unknown -> auth_required`, capture p95 1.5 ms, zero flicker
  transitions.
- Live bad-config startup run:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T133335Z-2576972/artifacts/run.json`
  observed `unknown -> pane_dead`; its normalized pipe log contains explicit
  `Error loading config.toml`, but the pane/server exited before `capture-pane`
  could read that text. PR1 intentionally did not add raw-log backfill or
  source fallback; this is a source-acquisition design question for PR2.
- Live session-supplement run:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T141909Z-4154029/artifacts/run.json`
  observed runtime `unknown -> working -> free` while pane-only evidence stayed
  `unknown -> working -> unknown`. The `free` transition came from
  `codex_session_task_complete`, and turn timing terminalized as
  `terminal_state=free`, `terminal_outcome=completed`.
- Live boundary runs:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T142008Z-4183944/artifacts/run.json`
  stayed `pane_dead` despite an empty session root, and
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T142024Z-4191985/artifacts/run.json`
  stayed `waiting_for_user` for an untrusted new workdir. These prove
  session-derived `free` is not a fallback over explicit pane states.

Claude runtime-status slice landed after PR1 with:

- `lib/provider_pane_status/claude_session.py`
- `lib/provider_pane_status/claude_pane.py`
- `test/test_provider_pane_status_claude_session.py`
- `test/test_provider_pane_status_claude_pane.py`
- ProjectView wiring that emits `provider_runtime_status` for Claude from
  provider activity hooks, bound Claude JSONL session evidence, and visible
  Claude pane evidence.

Claude pane parsing is deliberately narrower than Codex pane parsing. It only
classifies explicit Claude status shapes such as:

- `Thinking ..., running N shell command` as `tool_running`;
- spinner/status rows with elapsed time and token/thought metadata as
  `working`;
- `Running scheduled task` or `shell still running` as `tool_running`;
- explicit permission/API/error text as waiting or failed states;
- past-tense rows such as `Thought for ... ran ...` or `Sautéed for ...` as
  `terminal_summary`.

`terminal_summary` is observation-only. It is not a job completion signal and
must not be passed to dispatcher completion. ProjectView uses it only to break
stale Claude hook activity: if a Claude hook remains active while the pane shows
a stable terminal summary for 60s, sidebar status becomes `free` with reason
`claude_pane_no_active_stale_no_progress`. Claude prompt visibility remains
non-authoritative because real running Claude panes can still display `❯`.

Unknown session or pane evidence stays `unknown`, while a clean runtime with no
active job and no Claude session path is displayed as `free`.

Verification:

- `python -m pytest -q test/test_provider_pane_status_claude_session.py
  test/test_provider_pane_status_claude_pane.py` -> `15 passed`
- `python -m pytest -q test/test_provider_pane_status_claude_pane.py
  test/test_provider_pane_status_claude_session.py test/test_ccbd_project_view.py
  -k 'claude_runtime_status or claude_activity_includes_pane_probe or
  claude_pane_active or claude_stale_active'` -> `10 passed`
- `python -m pytest -q test/test_ccbd_project_view.py` -> `78 passed`
- `python -m pytest -q test/test_provider_pane_status_claude_pane.py
  test/test_provider_pane_status_claude_session.py test/test_provider_pane_status_codex.py
  test/test_provider_pane_status_codex_session.py test/test_codex_pane_status_probe.py`
  -> `67 passed`
- `python -m pytest -q test/test_provider_activity_artifacts.py
  test/test_provider_activity_hook_script.py test/test_claude_event_reading.py
  test/test_claude_comm_parsing.py test/test_claude_execution_polling.py`
  -> `25 passed`
- `python -m pytest -q test/test_provider_pane_status_codex.py
  test/test_provider_pane_status_codex_session.py
  test/test_codex_pane_status_probe.py
  test/test_provider_pane_status_claude_session.py` -> `60 passed`
- `python -m pytest -q test/test_claude_event_reading.py
  test/test_claude_comm_parsing.py test/test_claude_execution_polling.py
  test/test_provider_activity_hook_script.py test/test_provider_activity_artifacts.py`
  -> `25 passed`
- Stabilization evidence:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T143303Z-455718/artifacts/run.json`
  kept startup display at `unknown -> working -> free` instead of allowing old
  session `free` to jump ahead of pane boot work, and
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T143329Z-468685/artifacts/run.json`
  held `working` over the raw `codex_session_task_complete` transition for the
  bounded active-hold window before switching to `free`.
- Post-review cleanup: coworker review `job_2578d60d2d46` timed out with no
  actionable findings, so the local cleanup removed runtime `completed` from
  the display catalog, blocked prompt submission while a pane is already
  active, and made `empty_capture` reuse explicitly bounded by its own start
  time instead of by a refreshed stable-state timestamp.
- Compact follow-up review `job_c54b68ed7ac2` returned upstream 429 after
  retries were exhausted, so it did not provide a code-review signal. Treat
  the current state as locally verified, not coworker-approved.
- User decision on 2026-06-29: stop waiting for coworker review on this slice.
  Acceptance for the pane/session status probe is local tests plus live
  `/home/bfly/yunwei/test_ccb2` pressure evidence.
- Post-cleanup pressure evidence:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T144549Z-901054/artifacts/run.json`
  exposed new-workdir `waiting_for_user` immediately with zero flicker;
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T144608Z-910979/artifacts/run.json`
  and
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T144656Z-947753/artifacts/run.json`
  both stayed `unknown -> working -> free` with zero flicker; high-frequency
  sampling in
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T144755Z-990498/artifacts/run.json`
  reached 9.65 samples/s, 242 captures, p95 capture 1.7 ms, and zero flicker;
  isolated no-login
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T144836Z-1012045/artifacts/run.json`
  exposed `auth_required` immediately with zero flicker.
- Start-state decision: after prompt submission, raw `unknown` before the first
  explicit pane/session signal displays as runtime `start`, not `free` and not
  real `working`. Raw runtime remains recorded separately.
- Final no-review smoke:
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe/run-20260629T152132Z-2210496/artifacts/run.json`
  stayed `start -> working -> free`, while raw runtime stayed
  `unknown -> working -> free`; it ended with runtime `free` from
  `codex_session_task_complete`, had zero flicker transitions, and measured
  p95 capture latency at 1.8 ms.

Stabilization is intentionally separate from parsing:

- pane parser output remains strict and raw;
- session output remains explicit and raw;
- `runtime_status` is the only state that applies bounded time extension;
- Codex ProjectView display may also collapse no-active pane status to `free`
  after 60s of unchanged pane content; visible active status lines such as
  `Working (...)`, tool-running, and reconnecting are never collapsed by this
  timer;
- snapshots and metrics retain raw runtime, pane, and session streams for
  diagnostics.

Codex ProjectView/sidebar slice landed on 2026-06-29 with:

- `ccbd.project_view.service` now captures Codex pane text for ProjectView,
  composes shared pane parser output with the bounded managed-session
  supplement, and publishes `provider_runtime_status` on the agent row.
- `ccbd.project_view.activity` now lets Codex runtime status drive the sidebar
  presentation through explicit `activity_symbol` and `activity_color` values:
  `start` -> `◌` yellow, `working` -> `●` green, `tool_running` -> `◆` green,
  `reconnecting` -> `↻` yellow, `free` -> `◇` blue, known failures -> `✕` red,
  and `unknown` -> `?` gray.
- Legacy pane keyword/prompt/error heuristics are disabled for Codex rows. The
  generic helpers remain in place only for non-Codex providers until Claude has
  its own strict parser.
- Codex prompt-visible recovery hints are disabled. A running Codex job with raw
  runtime `unknown` now displays as runtime `start`; it does not become
  `provider_prompt_idle`, `provider_prompt_input_stuck`, or a recoverable
  prompt-stuck comm from the old logic.
- `unknown` remains visible as `provider_runtime_status.state=unknown`; it is
  not converted to idle, working, completed, or failed.
- On 2026-06-30 the old CCB Codex activity hook path was disabled for Codex:
  managed Codex homes no longer install `ccb-provider-activity-hook`, the hook
  script no-ops for `--provider codex`, and ProjectView ignores any stale
  `codex_hook` activity artifact for Codex rows. The generic hook framework is
  retained for non-Codex providers.

Verification:

- `python -m py_compile lib/ccbd/project_view/activity.py
  lib/ccbd/project_view/service.py`
- `python -m pytest -q test/test_ccbd_project_view.py` -> `71 passed`

Defer generic resolver or adapter work until at least one of these exists:

- a Claude pane parser;
- a second ProjectView/mobile consumer with the same mapping need;
- a structured `runtime_status` record ready to publish.

## Required Tests

Parser tests:

- current Codex working/status-line fixtures;
- hollow bullet `Booting MCP server` active row;
- conversation-body and indented status-shaped text stays unknown;
- reconnect wins over nearby stream-disconnect error text;
- auth-required, auth-failed, API error, config error, waiting, pane dead;
- `Worked for ...` completion evidence;
- `unknown after active` does not complete.

ProjectView tests:

- Codex conversation body containing `Working (...)`, API key text, or error
  examples does not become working/auth/error;
- unsupported provider with pane text returns unknown/no-provider-signal, not
  generic keyword status;
- job running plus Codex pane unknown displays runtime `start`, not working;
- capture/source error is visible and does not mutate job lifecycle;
- old prompt-idle/input-stuck functions cannot keep affecting Codex activity or
  Codex comm recoverability.

Hard deletion and authority tests:

- after Claude has its own parser, `activity.py` should no longer need to expose
  `_provider_working`;
- after Claude has its own parser, `activity.py` should no longer need to expose
  `provider_prompt_idle_after_request`;
- after Claude has its own parser, `activity.py` should no longer need to expose
  `provider_prompt_input_stuck`;
- unknown mapping is one-way: unknown pane input must not map to idle,
  working, completed, or failed;
- `PaneCompletionEvidence` must not appear in dispatcher completion paths or be
  passed to `dispatcher.complete()`;
- after PR1, `scripts/probe_codex_pane_status.py` must import parser constants
  and must not retain local `STATUS_MARKER_RE` or `CODEX_*_RE` duplicates.

Fixture tests:

- use one or two sanitized screen tails from
  `/home/bfly/yunwei/test_ccb2/codex-pane-status-probe` to tie real artifacts
  to parser fixtures.
- store sanitized committed fixtures under `test/fixtures/codex_pane/`, not as
  large inline strings in test code.

## Claude Pane Path

Claude pane status lives in the same package:

```text
lib/provider_pane_status/claude_pane.py
```

Claude must follow the same evidence discipline:

- provider-specific parser;
- explicit status shapes only;
- no prompt-visible idle authority;
- no quiet-output completion;
- pane evidence remains separate from hook/session completion authority.

Only after Codex and Claude both use the package should a resolver be
considered. At that point the resolver should compose typed signals; it should
not re-parse provider text or introduce fallback states.
