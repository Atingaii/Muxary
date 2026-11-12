# AGY Delivery Stability Hardening

Date: 2026-06-17

## Problem

Real project evidence from `/home/bfly/Documents/工作室/服务器` showed
`main -> frontend_engineer:agy` jobs reaching the AGY pane but returning empty
`incomplete` replies with `agy_native_anchor_missing`.

The failure was not mailbox delivery loss. The weak points were AGY-specific:

- CCB sent prompts into the AGY pane without first checking that Antigravity had
  returned to an empty input prompt.
- When AGY was still processing a previous task, retry prompts could be folded
  into one native `USER_INPUT` with multiple `CCB_REQ_ID` anchors.
- The 120 second anchor-missing path could terminalize before AGY wrote a late
  transcript response.
- AGY transcript logs are provider-owned observed evidence, not a structured
  CCB protocol stream like Codex or OpenCode storage.

## Target Behavior

AGY should approach OpenCode-style attribution stability while preserving AGY's
native transcript authority:

- Do not send a CCB prompt until the AGY pane is input-ready.
- Keep an unsent job running while AGY is busy, instead of terminalizing early
  and letting later jobs stack into the same provider turn.
- If transcript writes lag but the pane shows a stable completed answer for the
  submitted `CCB_REQ_ID`, emit pane fallback evidence after a stability window.
- If tmux reports an ambiguous send error, keep observing transcript/pane
  evidence for the submitted `CCB_REQ_ID` instead of immediately failing or
  blindly resending the prompt.
- If a historical transcript contains multiple `CCB_REQ_ID` anchors in one
  `USER_INPUT`, never attribute a later combined answer to an older superseded
  job; report `agy_request_coalesced` with the involved ids.
- Keep Codex, Claude, OpenCode, Kimi, DeepSeek, MiMo, and next-wave provider
  behavior unchanged.

## Implementation Notes

- `AgyPaneReader` remains a thin tmux/pane snapshot reader; readiness detection
  is a small AGY-specific helper keyed to the Antigravity empty prompt plus
  `? for shortcuts` / model footer.
- `start_submission` stores `pending_prompt` and sets
  `prompt_deferred_until_ready` when AGY is busy.
- `poll_submission` sends deferred prompts only after readiness, resets
  `started_at` when the prompt is actually sent, and uses longer AGY-specific
  windows for busy/long-running observed turns.
- Ambiguous tmux delivery errors are preserved in diagnostics while polling
  continues for native transcript or pane evidence; clearly fatal backend
  capability errors still fail immediately.
- Pane fallback is secondary evidence: it emits an answer before final boundary
  only after the same candidate remains stable for the fallback window.
- Native transcript parsing records `coalesced_request_ids` and whether the
  target request was the latest anchor inside that native user input.

## Acceptance

- AGY start defers prompt delivery when the pane is busy.
- AGY poll dispatches the pending prompt once the pane returns to the empty
  input prompt.
- AGY no longer emits anchor-missing terminal decisions merely because the pane
  is still busy past the old 120 second window.
- AGY can complete from stable pane fallback when transcript persistence lags.
- AGY can still complete when tmux reports an ambiguous send error but the
  native transcript proves the request was accepted and answered.
- Coalesced native input is diagnosed as coalesced instead of accepted as a
  valid old-job reply.
- Focused AGY/native provider tests pass without changing OpenCode behavior.

## Verification

- `PYTHONPATH=lib python -m pytest -q test/test_agy_execution_polling.py test/test_native_cli_completion.py -k agy`:
  `8 passed, 12 deselected`.
- `PYTHONPATH=lib python -m pytest -q test/test_agy_execution_polling.py test/test_native_cli_completion.py test/test_native_cli_providers.py test/test_v2_provider_catalog.py test/test_opencode_execution_polling.py`:
  `34 passed`.
- Isolated source-runtime smoke from
  `/home/bfly/yunwei/test_ccb2/native_provider_smoke` with
  `/home/bfly/yunwei/ccb_source/ccb_test`, stub AGY, isolated `HOME` and
  `CCB_SOURCE_HOME`: completed `job_74d4989cca04` with
  `agy_transcript_response_done`.
