# Kimi Receipt And Diagnostics Hardening

Date: 2026-06-17

## Purpose

Record Kimi-only reliability improvements for CCB-managed `kimi` workers without
changing runtime semantics for Codex, Claude, Gemini, OpenCode, DeepSeek, MiMo,
AGY, or the next-wave native CLI providers.

The goal is not to make Kimi a governed completion owner. The goal is to make
Kimi's known limits explicit, keep Kimi tasks small and structured, and prevent
empty or process-style Kimi receipts from being mistaken for accepted lifecycle
evidence.

## Landed Status

Status: landed in source on 2026-06-17.

Implemented surfaces:

- Kimi inherited ask skill: structured final receipt contract.
- Kimi provider execution: explicit no-captured-reply diagnostics for
  `kimi_native_turn_timeout + reply_chars=0`.
- Dispatcher finalization: Kimi-guarded forced-artifact wording for empty
  no-captured replies.
- Trace summary/rendering: Kimi terminal metadata fields.
- Kimi provider manifest: `supports_resume=false` for CCB in-flight execution
  restore semantics.

The optional timeout knob remains deferred.

## Current Finding

Observed Kimi issues are cooperation and diagnostics issues, not a new provider
crash class:

- `sl_ki` can return process-style replies such as "reading" or "doing" that
  do not prove completion.
- Retried small, structured Kimi tasks can return useful inventory evidence.
- `kimi_native_turn_timeout` with `reply_chars=0` can produce an artifact-reply
  transport stub that looks actionable even though no provider reply was
  captured.
- Kimi execution restore diagnostics already say `resume_supported=false` and
  `resubmit_required`; interrupted in-flight Kimi execution should be treated as
  resubmit-only.

## Non-Impact Constraint

All implementation slices must be Kimi-scoped:

- Prefer `provider == "kimi"` checks, Kimi adapter diagnostics, Kimi inherited
  skill text, and Kimi-specific tests.
- Do not change default timeout, artifact, trace, retry, or receipt semantics
  for other providers.
- Shared code may only receive additive fields or Kimi-guarded formatting. If a
  shared helper would change output for other providers, split the Kimi behavior
  into a provider-specific branch instead.
- Do not require provider login during source validation. Stub-backed tests and
  no-login source runtime validation are the default.

## Landed Slices

### Slice 1: Kimi Worker Receipt Contract

Updated the Kimi inherited ask skill so CCB-managed
Kimi workers must answer with a structured receipt:

```text
status:
inspected:
exact_files:
findings:
reject_cases:
required_tests:
no_open:
blockers:
```

Rules:

- `sl_ki` tasks should be small: one repo/package, three to six files when
  possible, one or two verifier commands, and a 180-240 second target.
- Process replies are invalid: "I am reading", "I will test", or "completed"
  without file/evidence fields is not a receipt.
- Kimi output is candidate evidence only. `mn_c` keeps ownership of diff
  review, verification, final receipt, and commit decisions.

Acceptance:

- Managed Kimi skill/projection tests prove the receipt contract is projected
  only to Kimi.
- Existing non-Kimi ask-skill projection tests do not change expected output.

### Slice 2: Kimi No-Captured-Reply Diagnostics

For Kimi terminal decisions where:

- `reason == "kimi_native_turn_timeout"`
- `reply_chars == 0`
- no assistant reply was captured

emit explicit Kimi diagnostics such as:

- `no_captured_reply=true`
- `provider_no_reply=true`
- `receipt_valid=false`
- `receipt_class=no_captured_reply`

If `--artifact-reply` is forced, the visible terminal reply should explain that
no Kimi provider reply was captured instead of implying that a useful full reply
exists in the artifact.

Implementation boundary:

- Prefer implementing this in `provider_backends/kimi/execution.py` or a
  Kimi-guarded finalization branch.
- Do not alter generic `artifact_stub()` wording for other providers in this
  slice.

Acceptance:

- A focused Kimi timeout test covers empty reply, forced artifact reply, and
  diagnostics.
- Existing artifact-reply behavior for non-Kimi providers remains unchanged.

### Slice 3: Kimi Trace Visibility

Expose enough Kimi terminal metadata for `ccb trace <job>` to classify the
result without opening artifacts:

- `terminal_reason`
- `reply_chars`
- `total_secs`
- `artifact_reply_forced`
- `receipt_class`

Implementation boundary:

- Add fields only when present, or only for Kimi/Kimi-prefixed reasons.
- Keep existing trace lines stable for providers that do not emit these fields.

Acceptance:

- Trace rendering for a Kimi timeout shows `kimi_native_turn_timeout`,
  `reply_chars=0`, and `receipt_class=no_captured_reply`.
- Existing trace rendering tests for normal replies continue to pass.

### Slice 4: Kimi Resume Metadata Consistency

Kimi execution restore diagnostics report `resume_supported=false`, while the
provider manifest previously represented a broader session/provider capability.
This distinction is now clarified so UI/doctor/trace users do not infer that an
interrupted Kimi CCB execution can resume.

Selected semantics:

- Kimi manifest `supports_resume=false` describes CCB execution restore.
- Provider session continuity, if Kimi later supports a separate prompt/session
  restore mode, must be represented by a separate capability rather than this
  manifest flag.

Acceptance:

- Restore-report and execution-state diagnostics do not imply Kimi in-flight
  execution recovery.
- Provider catalog tests document the selected semantics.

### Slice 5: Optional Timeout Knob, Deferred

Do not increase Kimi timeout by default. If needed later, add an opt-in
Kimi-only setting such as an env/config override for native-turn timeout.

Acceptance threshold before implementation:

- Real workload evidence shows useful Kimi replies are being cut off shortly
  after 300 seconds.
- Queue occupancy impact is understood.

## Verification

Focused tests passed:

- `PYTHONPATH=lib python -m pytest -q test/test_ask_skill_templates.py`:
  `3 passed`.
- `PYTHONPATH=lib python -m pytest -q test/test_native_cli_completion.py -k kimi`:
  `8 passed, 5 deselected`.
- `PYTHONPATH=lib python -m pytest -q test/test_v2_message_bureau_dispatcher_integration.py -k artifact`:
  `7 passed, 54 deselected`.
- `PYTHONPATH=lib python -m pytest -q test/test_v2_cli_render.py -k trace`:
  `3 passed, 21 deselected`.
- `PYTHONPATH=lib python -m pytest -q test/test_v2_provider_catalog.py`:
  `4 passed`.
- `PYTHONPATH=lib python -m py_compile` for touched Kimi, artifact, trace, and
  catalog modules: passed.
- `git diff --check`: passed.

Source runtime validation:

- Run from `/home/bfly/yunwei/test_ccb2`.
- Use `/home/bfly/yunwei/ccb_source/ccb_test`.
- Isolate `HOME=/home/bfly/yunwei/test_ccb2/source_home` and
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`.
- Prefer Kimi stubs or existing no-login source fixtures; do not require a
  fresh Kimi login.

Regression guard:

- Include at least one non-Kimi provider artifact/trace test when touching
  shared finalization or trace code.
- `git diff --check` on touched files.

## Rollout Result

1. Receipt-contract projection landed first and only changed Kimi inherited
   skill text.
2. Kimi no-captured-reply diagnostics landed with focused timeout and artifact
   tests.
3. Trace visibility landed after diagnostics fields were stable.
4. Kimi resume metadata was resolved as CCB in-flight execution restore
   capability.
5. Timeout configurability remains deferred until measured evidence shows that
   useful Kimi replies are being cut off shortly after 300 seconds.

## Resolved Questions

- Kimi structured receipt contract lives in inherited Kimi skill projection for
  this slice. CCB generic `ask` prompt injection remains unchanged.
- `kimi_native_turn_timeout` with no reply remains `failed`, with
  `no_captured_reply` diagnostics to classify it.
- Kimi manifest `supports_resume` describes CCB in-flight execution restore and
  is now `false`.
- `sl_ki` routing policy remains an operator convention enforced by `mn_c` for
  now; role/config enforcement is deferred until convention proves insufficient.
