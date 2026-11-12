# Phase 6B L0 Ask Stdin Harness Fix Plan

Date: 2026-07-04
Status: ACCEPTED FOR WORKER DISPATCH / DO NOT RUN

## Purpose

Define the repair for the second Phase 6B L0 `test_design_failure` before any
new real-provider launch approval is requested.

This plan is not approval to run L0. It is a reviewable work package for fixing
the launch harness and, optionally, hardening `ccb ask`/Ask skill guidance so
future scripts cannot accidentally feed runner text into an ask message.

## Current Evidence

- Repeat launch approval consumed:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f3adf3a31988-art_e0ad26e38f534e04.txt`.
- Repeat B7 report:
  [../history/phase6b-real-provider-l0-repeat-b7-20260704.md](../history/phase6b-real-provider-l0-repeat-b7-20260704.md).
- Repeat evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/phase6b_l0_repeat_evidence_row.json`.
- Repeat command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/phase6b_l0_repeat_command_log.jsonl`.
- Post-B7 cleanup returned `kill_status: ok`, `state: unmounted`.

The repeat command log contains only:

```text
diagnose
config_validate_initial
start_project
topology_a_propose
topology_a_commit_apply
ask_a_orchestrator_compact
```

Variant A ask submitted successfully as `job_25a9c7e4a9b6`; A release and all
variant B commands were not logged.

## Root Cause

The approved command block was executed by piping Markdown-extracted shell text
into `bash`. That made the shell script body the stdin stream for every child
process that inherited stdin.

`ccb ask` intentionally supports stdin as message text:

- Ask skill examples use stdin/heredoc for message bodies.
- [lib/cli/parser.py](/home/bfly/yunwei/ccb_source/lib/cli/parser.py:108)
  reads stdin when it is not a TTY.
- [lib/cli/parser_runtime/ask.py](/home/bfly/yunwei/ccb_source/lib/cli/parser_runtime/ask.py:94)
  appends stdin text to the ask message.

Therefore a long script must not call `ccb ask` while the script itself is being
fed through stdin unless the ask subprocess stdin is explicitly closed or
redirected. This was a launch-harness defect, not valid evidence about real
provider capability.

## Immediate Repair

The next launch request must change the harness before asking for a new
approval:

1. Materialize the frozen launch block into a script file under a fresh lab
   root, for example:
   `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/run_l0.sh`.
2. Execute the materialized file with `bash "$PHASE6B_L0_SCRIPT"`, not
   `sed ... | bash`.
3. In `run_l0_command`, redirect child stdin from `/dev/null`:

   ```bash
   timeout --preserve-status "${PHASE6B_L0_TIMEOUT_SECONDS}s" "$@" \
     </dev/null >"$stdout_path" 2>"$stderr_path"
   ```

4. Record the materialized script path and sha256 in the command log or B7
   evidence row.
5. Keep the existing no-reuse root refusal; use a fresh empty root or require
   explicit reviewer approval for any alternate root.
6. Keep provider replies as evidence only; B7 remains script-owned.

This is enough to fix the observed failure without changing product behavior.

## Optional Product Hardening

These are useful but should not be required for the next L0 if they would slow
the launch harness repair:

- Add `ccb ask --no-stdin` and teach scripts to use it.
- Or change `ccb ask` to read stdin only when no positional message is present.
- Or reject positional message plus non-empty stdin unless `--append-stdin` is
  explicit.
- Update Ask skill guidance: do not invoke `ask` inside stdin-fed scripts; use a
  materialized script file, `</dev/null`, or a deliberate heredoc only for the
  ask message.

Any product-level behavior change needs compatibility review because current
Ask skill and CLI behavior intentionally support stdin messages.

Deferred follow-up: product-level stdin hardening remains open after the
repeat2 harness repair. Candidate changes include `ccb ask --no-stdin`, an
explicit `--append-stdin` policy, or Ask skill guidance updates. These are not
blockers for repeat2 launch-review because the immediate accepted scope is
docs/harness only.

## Acceptance Criteria

- The corrected launch request cannot be executed through a stdin-fed shell
  pipeline.
- Every `run_l0_command` child receives stdin from `/dev/null`.
- Static review confirms variant A and B ask targets remain:
  `phase6b-l0-ccb-orchestrator` and `p6bl0b-orchestrator`.
- Static review confirms topology proposals remain mount-only: no `edges`,
  `gates`, `artifacts`, or `topology_dispatch.json`.
- Static review confirms B7 classifies truncated command logs as
  `test_design_failure`, not pass.
- The next reviewer approval, if any, is for exactly one fresh L0 run only.

## Worker Chain Protocol

After coworker review accepts this plan, dispatch workers with chained internal
review:

1. Implementation worker updates the launch request/checklist/B7 normalizer
   shape only. No L0 runtime run and no real provider command.
2. The implementation worker asks the reviewer directly with `ask --chain`
   from their active worker job, because the review result is needed to finish.
3. If the reviewer reports blockers or high findings, the worker fixes them and
   re-asks the reviewer directly.
4. The worker reports back to `talk2` only after reviewer acceptance or a true
   blocker that prevents progress.
5. Intermediate review artifacts should not route through the user or through
   `talk2` unless they require an owner decision.

## Owner Decisions Applied

- Immediate worker scope is docs/harness only. Product-level
  `ccb ask --no-stdin` or stdin policy changes are deferred.
- The next fresh root is fixed as
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704`.
- The launch request embeds the full reviewed `run_l0.sh` materializer instead
  of relying on a separate unchecked runtime-only file.
