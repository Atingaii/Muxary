# Grok Ask Skill Injection Test Plan

Date: 2026-07-11

## Goal

Verify that every CCB-managed Grok instance discovers CCB's inherited `ask`
skill from its own managed home and that asks remain bound to the intended
provider instance. Skill discovery and cross-window routing are separate
release gates: passing one does not imply the other.

This plan is execution-ready only after the Grok projection implementation
lands. Until then it defines test ownership, fixtures, evidence, and stop
conditions without changing runtime state.

## Scope

In scope:

- Native projection to
  `.ccb/agents/<agent>/provider-state/grok/home/.grok/skills/ask/SKILL.md`.
- `inherit_skills` enable, disable, refresh, and cleanup behavior.
- Startup and per-job materialization using the same managed Grok home.
- Storage classification for projected Grok skills.
- Single- and two-instance ask attribution, including restart and clear.
- Real Grok discovery through `grok inspect --json` and real headless asks.

Out of scope:

- Replacing Grok's current per-job headless execution adapter.
- Treating visible-pane text as the primary completion source.
- Changing leader-socket or session policy without a failing routing repro.
- Running source runtime from the `ccb_source` checkout.

## Test Ownership

- Implementation owner adds or updates focused unit tests with the source
  change.
- Validation owner runs isolated source-runtime and real authenticated gates
  directly from `/home/bfly/yunwei/test_ccb2` and records inspectable evidence.
- A routing failure is returned to the implementation owner with request id,
  target agent, observed agent/window, managed-home path, session binding, and
  subprocess command evidence. It is not reclassified as a skill failure.

## Gate 0: Capability Probe

Run before implementation if the installed Grok version changes:

1. Record `command -v grok` and `grok --version`.
2. Create a temporary isolated `HOME` containing only
   `.grok/skills/ask/SKILL.md`.
3. Run `HOME=<temp-home> grok inspect --json`.
4. Require exactly one `ask` skill whose source is the temporary native Grok
   path, without relying on `~/.claude/skills` compatibility discovery.

Pass condition: native `.grok/skills/<name>/SKILL.md` discovery is confirmed
for the tested CLI version.

## Gate 1: Focused Unit Tests

Add coverage for:

- `inherit_skills/grok_skills/ask/SKILL.md` is included in the shared ask-skill
  template contract and retains submit-only CCB ask behavior.
- Grok home materialization writes the managed native skill when
  `inherit_skills = true` and is byte-for-byte idempotent on refresh.
- `inherit_skills = false` removes only CCB-owned projected skill content and
  preserves `.grok/auth.json`, `.grok/config.toml`, provider sessions, logs,
  and unrelated user-owned skills.
- Startup preparation and per-job execution resolve the same per-agent managed
  `HOME`; `grok1` and `grok2` never share a projected skill path.
- Launcher and execution refresh stale managed skill content before Grok is
  invoked.
- Storage classification treats `.grok/skills/**` as projected configuration,
  keeps auth secret classification intact, and does not reclassify Grok
  session/log output as projected configuration.
- Named session binding for `grok1` and `grok2` uses the matching instance
  session file and does not silently fall back to another instance.

Initial focused command set:

```bash
PYTHONPATH=lib python -m pytest -q \
  test/test_ask_skill_templates.py \
  test/test_provider_hook_settings.py \
  test/test_v2_runtime_launch.py \
  test/test_storage_classification.py \
  test/test_v2_provider_core_registry.py \
  test/test_provider_execution_service_runtime.py
```

The implementation owner may add a dedicated `test/test_grok_provider.py` and
must include it in this gate. Passing unrelated existing tests is not a
substitute for the positive, negative, and two-instance cases above.

## Gate 2: Isolated Source-Runtime Smoke

Use a dedicated project such as
`/home/bfly/yunwei/test_ccb2/grok_ask_skill_smoke`. Run only the absolute source
wrapper, with isolated provider state:

```bash
cd /home/bfly/yunwei/test_ccb2/grok_ask_skill_smoke
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
  /home/bfly/yunwei/ccb_source/ccb_test --diagnose
```

Then use deterministic Grok command stubs to validate:

1. `config validate` accepts `cmd; grok1:grok, grok2:grok`.
2. Start mounts both agents and creates a distinct managed native ask skill in
   each Grok home.
3. The stub records `HOME`, provider instance, session id, cwd, request id, and
   argv for every job without recording credentials.
4. One exact-token ask to each agent returns only its own token.
5. At least eight mixed concurrent asks alternate targets; every result maps
   to the requested agent and managed home.
6. Visible pane captures contain no request id intended for the other agent.
7. Restart `grok1`; both agents still answer correctly and only `grok1` has a
   new runtime/session generation where expected.
8. Clear `grok2`; projection is restored or preserved according to the clear
   contract, and post-clear asks remain isolated.
9. Disable `inherit_skills` in a negative-control profile: native ask
   projection disappears for that profile while auth/config and unrelated
   state remain intact.
10. Stop the runtime with the source wrapper and retain only sanitized evidence
    required for review.

Pass condition: no missing projection, no cross-agent request/reply evidence,
and no mutation under the source checkout's active `.ccb/agents` runtime.

## Gate 3: Real Grok Discovery And Ask

This gate intentionally exercises authenticated inherited Grok configuration,
so it must be run separately from Gate 2 and explicitly record that isolation
is relaxed. Do not print or archive auth files.

1. Start one real managed Grok agent in an external test project.
2. Run `grok inspect --json` against that agent's managed `HOME` and require
   the `ask` source to be its native `.grok/skills/ask/SKILL.md` path.
3. Submit three serial exact-token asks and require exact target attribution,
   non-empty replies, and normal Grok subprocess completion.
4. Capture the visible pane before and after; headless ask request ids must not
   be typed into an unrelated pane.

Pass condition: the projected native skill is discoverable in the same managed
home used by real asks, and serial asks complete without pane leakage.

## Gate 4: Real Two-Instance Routing Pressure

Use `grok1:grok` and `grok2:grok` in one external project:

1. Record each instance's managed home, session binding, pane id, and startup
   command, redacting secrets.
2. Submit one warm-up ask per instance.
3. Submit at least six mixed asks with unique target-tagged tokens, including
   concurrent asks when account limits permit.
4. For every job, correlate target agent, provider instance, request id,
   subprocess command, managed `HOME`, completion artifact, and visible pane
   captures.
5. Restart only `grok1`, then submit one ask to each instance.
6. Fail if any request is observed in the wrong pane, uses the wrong managed
   home/session binding, or returns under the wrong agent even when the answer
   text appears correct.

If provider rate limits prevent concurrency, repeat the same tagged matrix
serially and record concurrency as blocked rather than passed.

Pass condition: zero cross-instance mismatches before and after restart.

## Gate 5: Regression And Documentation

After Gates 1-4 pass:

- Run the wider provider/home/storage test group selected by the touched diff.
- Run the repository non-blackbox pytest release gate.
- Run `git diff --check`.
- Confirm the startup supervision and provider-state storage contracts describe
  Grok native skill projection and cleanup semantics.
- Record CLI version, test project path, sanitized job ids, pass counts, and any
  skipped authenticated/concurrency coverage in plan evidence.

## Stop Conditions

Stop release acceptance and open a defect when any of these occur:

- Grok discovers `ask` only from a global Claude/Codex home instead of its
  managed native path.
- Disabling inheritance deletes auth, config, sessions, logs, or unrelated
  user-owned skills.
- `grok1` and `grok2` share a managed home or bind to the wrong session file.
- A request id, prompt, or completion artifact is attributed to the wrong
  agent/window.
- Source validation mutates `/home/bfly/yunwei/ccb_source/.ccb/agents` or runs
  a source runtime from the source checkout.
- Sanitized evidence cannot distinguish a skill-discovery failure from a
  routing/session failure.

## Evidence Record

For each executed gate, record:

- Date, Grok version, source revision, and exact test command.
- Isolated versus intentionally inherited provider environment.
- Agent-to-home/session/pane mapping with secrets redacted.
- Test counts and exact failed case names.
- Sanitized request-id-to-agent correlation for routing pressure.
- Cleanup result and remaining external test project path.

Do not record API keys, auth file contents, or raw provider configuration that
may contain credentials.

## Baseline Evidence: 2026-07-11

Environment:

- Grok Build `0.2.93 (f00f96316d)`.
- Source wrapper: `/home/bfly/yunwei/ccb_source/ccb_test`.
- External real-provider project:
  `/home/bfly/yunwei/test_ccb2/grok_ask_baseline`.
- Authenticated host Grok configuration was intentionally inherited; auth
  contents were not inspected or recorded.

Results before source implementation:

- Gate 0 passed: an isolated temporary `HOME` exposed exactly one `ask` skill
  from native `.grok/skills/ask/SKILL.md` discovery.
- `grok1` and `grok2` mounted successfully with distinct managed homes and
  pane ids `%1` and `%2`.
- Both current managed homes had inherited Grok auth/config and bundled skills,
  but neither contained or discovered an `ask` skill. This confirms the source
  projection gap.
- Two serial warm-up asks returned exact instance-tagged replies.
- Six mixed concurrent asks returned `6/6` exact target-tagged replies. Each
  completion artifact was stored only under the requested agent's provider
  runtime.
- After restarting only `grok1`, one ask to each instance returned `2/2` exact
  target-tagged replies.
- Across warm-up, concurrent, and post-restart asks, visible-pane captures had
  zero request-token hits. The reported cross-window behavior did not reproduce
  in this ten-ask real-provider baseline.

Temporary native-skill probe:

- Copying the packaged CCB ask skill into each managed
  `.grok/skills/ask/SKILL.md` made `grok inspect --json` report the correct,
  instance-local source path for both agents.
- A CCB headless ask to `grok1` caused Grok to read the skill and plan an
  `ask --silence grok2` command, but the run terminalized as
  `grok_run_finished:cancelled` before the terminal command executed. Current
  Grok per-job execution does not auto-approve terminal tools.
- The same skill invocation in the visible `grok1` TUI displayed an approval
  request. After interactive approval, Grok executed
  `command ask --silence grok2`, creating child job `job_871c0ab3b9f9`.
  The child completed on `grok2` with exact provider output
  `GROK2_VISIBLE_SKILL_0711`; Grok then emitted
  `GROK1_VISIBLE_SKILL_SUBMITTED_0711` in the originating visible session.
- The child ask remained headless and did not type its request or reply into
  the `grok2` visible pane.

Implications:

- Native skill projection is viable and visible-session delegation works.
- The source implementation still needs managed projection, disable/cleanup,
  storage classification, and unit coverage.
- Headless Grok delegation through the injected skill needs an explicit
  permission decision. Skill discovery alone does not authorize terminal tool
  execution, and a cancelled tool turn currently becomes an empty incomplete
  CCB reply.
- Cross-window routing remains an open incident question because it was not
  reproduced under this controlled two-instance run.

## Native Completion Decision: 2026-07-11

Grok completion follows the provider-native authority rule used by managed
Codex and Claude rather than a model-generated semantic sentinel:

- `CCB_REQ_ID` is retained only for request attribution.
- CCB does not ask Grok to print `CCB_DONE` or CCB turn-end text.
- Streaming `type=end` with `stopReason=EndTurn`, aggregated native
  `stopReason=EndTurn`, and documented compatible native turn-end events are
  successful completion authority when a non-empty assistant reply exists.
- Native terminal reasons such as `Cancelled` close immediately as incomplete
  with the provider reason preserved.
- Process exit is lifecycle evidence only. Exit zero without a native terminal
  event closes as `incomplete/grok_native_terminal_missing`, even if partial
  assistant text was captured.
- The normalized CCB `TURN_BOUNDARY` item is emitted only after native terminal
  evidence and is downstream evidence, not completion authority.

Landed verification:

- Parser/adapter-focused suite: `25 passed, 29 deselected`.
- Complete `test_grok_provider.py` and
  `test_native_cli_provider_execution.py`: `54 passed`.
- Wider native provider, execution-service, catalog, registry, and runtime-spec
  suite: `31 passed`.
- Real authenticated source-runtime job `job_8e38805500d5` completed with
  exact reply `GROK_NATIVE_ENDTURN_OK_0711` and terminal reason
  `grok_run_stop`. Its raw provider stream contained native
  `type=end`, `stopReason=EndTurn` and no CCB completion marker text.
