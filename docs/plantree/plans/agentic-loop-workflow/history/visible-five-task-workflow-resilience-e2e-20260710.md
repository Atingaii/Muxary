# Visible Five-Task Workflow Resilience E2E

Date: 2026-07-10
Status: PASS WITH BOUNDED RESIDUALS

## Scope

`talk2` directly supervised the opened real-provider project:

```text
/home/bfly/yunwei/test_ccb2/workflow-window-e2e-talk2-20260710-093408
```

The run used the `workflow/agentic-loop-topology` worktree `ccb_test`, inherited
the system Codex/Claude provider environment, and used the project-local role
store. The visible steady state was two windows:

- `ccb-user`: sidebar plus resident Codex frontdesk;
- `ccb-plan`: sidebar plus resident Codex planner.

Coder, code reviewer, orchestrator, task detailer, and round reviewer capacity
remained dynamic. Runtime commands were executed and evidence was audited by
`talk2`; no worker or reviewer was used as validation authority.

## Workflow Result

One natural-language frontdesk request asked for an inventory-baseline and
comparison extension while intentionally leaving significance policy details
underspecified. Frontdesk handed the macro request to planner. Planner produced
five bounded direct-execution tasks:

| Task | Loop | Result | Dynamic release |
| :--- | :--- | :--- | :--- |
| `inventory-baseline-core` | `lpc80e62` | `done/pass` | 4 released, 0 retained |
| `inventory-baseline-cli` | `lpab6b82` | `done/pass` | 4 released, 0 retained |
| `inventory-baseline-tests` | `lpcf2ab3` | `done/pass` | 4 released, 0 retained |
| `inventory-baseline-docs-ci` | `lpf12827` | `done/pass` | 4 released, 0 retained |
| `inventory-baseline-review-fixes` | `lp516a90` | `done/pass` | 4 released, 0 retained |

Each round mounted fresh coder, code reviewer, orchestrator, and
`ccb_round_reviewer` panes. Every round removed all four dynamic agents and the
empty `ccb-exec` window. Frontdesk and planner pane identities survived all
rounds and the later daemon-restart probe.

The product review loop found and repaired three nontrivial defects in the lab
task rather than accepting degraded behavior:

1. Python bool/numeric equality hid `False` versus `0` and `True` versus `1`
   changes, including nested values.
2. `--json` argparse failures emitted plain usage instead of a parseable JSON
   error envelope.
3. Human baseline output allowed unsafe SKU/field tokens to inject line breaks;
   unsafe tokens are now JSON-encoded while simple tokens stay readable.

Direct supervisor acceptance passed 32 inventory tests. Independent probes
confirmed no-diff JSON success, significant-change exit code `4` with
added/removed/changed evidence, and JSON argument errors with exit code `2`
and empty stderr.

## Runtime Defects Exposed And Repaired

1. Frontdesk session observation could reuse a stale request id from prior
   conversation. Request authority is now bound to the current Codex user turn,
   with a deterministic turn-derived id when no explicit id is supplied.
2. Auto-runner could continue into stale tasks after a failed seed job and
   could import an unbound role output first. Failed seeds now stop explicitly;
   the first import is bound to `--wait-job`.
3. Codex readiness depended on the startup banner remaining in pane history.
   A visible idle prompt is now accepted after the banner scrolls away, while
   active Working/Thinking/Running prompts remain rejected.
4. One Claude-compatible round-reviewer turn rendered a final result and became
   idle without a final assistant text event or Stop hook. A bounded
   `ccb_round_reviewer`-only pane fallback now requires the current request
   anchor, a marked Claude assistant result (`●`, `•`, or `⏺`), and an idle input
   box. Unmarked result text from the prompt cannot terminate the job.
5. ccbd restart previously abandoned an active provider turn even when the
   exact pane process and binding were still alive. Restore now resumes only
   when PID, runtime ref, session ref, and workspace all match.
6. Claude's permanent `Auto-update failed` footer was misclassified as a
   provider failure in the sidebar. The footer is now nonfatal while real API
   error markers remain failures.
7. Provider session files could be group-readable and Claude session commands
   persisted auth values or inline settings. Session writes are now `0600`;
   persisted Claude commands remove API key/token assignments and replace
   supported inline settings with the managed settings path. Connection route
   parameters such as `ANTHROPIC_BASE_URL` remain available for recovery.
8. AGY treated a live process at its first-project trust dialog as a running
   provider even though the pane was not ready for prompt delivery. Auto-mode
   launches now confirm only the complete AGY trust UI, only when both the
   script-owned auto-permission bit and `--dangerously-skip-permissions` are
   present, and only once. Safe mode observes but never confirms the dialog.
   Prompt delivery still waits for the real idle input box.

## Live Recovery And Lifecycle Probes

### Same-turn daemon restart

A real planner diagnostic ask, `job_e9dcdca842ad`, was allowed to enter
`running`. ccbd was then killed while the provider turn was active. The keeper
started a new daemon:

```text
ccbd PID: 3361976 -> 3427767
planner pane: %3
planner pane PID: 2842595 -> 2842595
request anchors: 1 -> 1
job record count: unchanged
```

The original job completed naturally with `task_complete`; no replacement job,
duplicate submission, or pane recreation occurred.

### Dynamic Claude mount and release

The supervisor committed a mount-only topology for one temporary
`runtime-probe-round-reviewer` in `ccb-plan`. The live runtime reported
`idle/alive`, the sidebar showed a normal idle marker rather than a red failure,
and the new session file was `0600` with no persisted Anthropic API key/token.
Topology release returned `released_count=1`, `retained_count=0`, removed the
temporary pane, and preserved both resident panes. All 22 provider session
files in the project were normalized to `0600` for the retained evidence root.

### Additional provider probes

Gemini is excluded from the current production gate by product direction.
OpenCode, Grok, and AGY remain in scope alongside Codex and Claude.

- OpenCode `1.16.2` is installed and lists OpenAI OAuth, but a real
  `openai/gpt-5.5` request failed with `Token refresh failed: 401`. It is an
  authentication blocker, not a provider pass.
- Grok `0.2.93` is installed, but `grok models` reported `You are not
  authenticated`. It is an authentication blocker, not a provider pass.
- AGY `1.1.0` completed a direct real request with Claude Sonnet 4.6 and then
  completed CCB job `job_88d19f4374e8` in the fresh source-wrapper project
  `/home/bfly/yunwei/test_ccb2/provider-agy-evidence-talk2-20260710-140128`.
  The exact reply was `AGY_CCB_DURABLE_EVIDENCE_OK`. The persisted
  `turn_boundary` records trust authority, dialog observation, one confirmation
  attempt, count `1`, and confirmation success. A separate `ccb -s` project
  left the trust dialog untouched, did not place the request anchor in the
  pane, and was cleanly unmounted.

## Performance Findings

Observed round wall times and provider segments:

| Loop | Total | Worker | Reviewer | Rework/recheck | Orchestrator | Round reviewer |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `lpc80e62` | 1629s | 470s | 211s | 319s | 91s | 535s |
| `lpab6b82` | 886s | 324s | 158s | 320s | 64s | 17s |
| `lpcf2ab3` | 629s | 375s | 134s | - | 98s | 20s |
| `lpf12827` | 376s | 195s | 90s | - | 70s | 19s |
| `lp516a90` | 627s | 320s | 201s | - | 89s | 16s |

The first round includes daemon/provider recovery and is not representative.
Normal round-review latency was 16-20 seconds. Worker/reviewer model turns and
broad verification prompts dominate steady-state latency. Coder and reviewer
RolePack skills now tell agents to detect repository metadata once and avoid
repeated Git commands in non-Git labs.

## Verification

- Core workflow/provider/control-plane bundle: `406 passed`, including the
  final prompt-contamination hardening.
- Full repository gate excluding Gemini nodes: `3854 passed, 2 skipped, 124
  deselected` in 552.07 seconds.
- OpenCode/Grok/AGY backend, polling, storage, session, and registry matrix:
  `117 passed`.
- AGY trust/readiness focused matrix after the live-capture fixes: `17 passed`.
- Claude pane fallback focused tests: `12 passed`.
- Real project product suite: `32 passed`.
- All five task records: `done`, last round `pass`, no active loops.
- Final visible topology: only resident frontdesk/planner panes; no
  `ccb-exec`, no dynamic agents, no auto-runner lock.
- Dynamic Claude lifecycle probe: one added, one released, zero retained.
- Same-live-runtime restart probe: original job completed without duplicate
  submission.
- AGY real adapter probe: automatic trust completed once with durable evidence;
  safe mode did not confirm or deliver.

## Residuals And Boundaries

- The current inherited-system Claude login path is proven. A custom
  profile-only auth token cannot be written back into the session command; a
  future secure credential rehydration mechanism must rebuild it without
  plaintext persistence before that profile shape is claimed restart-safe.
- Proxy transport variables remain in restart commands and may themselves
  contain credentials. Session files are `0600`, but credential-bearing proxy
  URLs need a separate secure reference design.
- OpenCode is not currently real-provider ready because its configured OpenAI
  OAuth refresh returns HTTP 401. Grok is not real-provider ready because no
  active login is available. These are explicit environment blockers; neither
  was replaced with a stub or another provider.
- AGY model selection currently requires provider-specific `startup_args`;
  the v2 `model` shortcut rejects AGY. Config v3 must expose model selection
  consistently for supported workflow role/provider assignments.
- Gemini results are not part of the current acceptance gate. Shared provider
  infrastructure remains tested through the non-Gemini suite.
- The full pytest run left about 30 test-only tmux/sidebar/bridge processes
  under `/tmp/pytest-of-bfly/pytest-6385` after their socket files had already
  been removed. `talk2` terminated only those basetemp-owned processes and
  verified zero residue. Automatic test-fixture teardown remains a host
  resource-hygiene gap even though no real CCB project was affected.
- The planner diagnostic prompt asked for file inspection and caused the
  provider to run tests despite the planner RolePack prohibiting shell/tests.
  Resulting tempfile setup errors are prompt-design evidence, not product-test
  failures. Future planner probes must use controller-supplied compact evidence.
- This run proves a bounded five-task workflow, dynamic lifecycle, UI
  visibility, and same-turn daemon recovery. It does not publish a release,
  enable dynamic workflow by default, or prove arbitrary multi-round DAGs and
  unlimited concurrent worker groups.

The real project remains mounted and inspectable.
