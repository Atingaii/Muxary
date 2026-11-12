# Phase 6B L5 Partial Observation Launch Request

Date: 2026-07-04
Status: RUN CONSUMED / B7 VALID_NON_SUCCESS / PHASE 6B UNCLAIMED

## Purpose

This topic records a fresh Phase 6B L5 repeat4 launch-specific request. The
requested L5 tranche is partial-only:
`phase6b-l5-partial-budget-source-gap`. It would satisfy the acceptance goal's
"reviewer rework or partial" observation requirement only if a supervised run
produced a reviewer-gated B7 row with `round_result=partial`,
`final_status=partial`, and `classification=valid_non_success`.

Reviewer2 granted launch-specific approval-to-run in `job_5dd131a6ea7e` for
exactly one supervised repeat4 run using the root and command shape below.
Talk2 consumed that approval once. The run produced
[../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md)
with `Status: valid_non_success` and
`reviewer_rework_or_partial_observed=true`; post-B7 cleanup returned
`state: unmounted`. The approval does not extend to reviewer-rework, L1-L4,
Phase 6B readiness, or production/default enablement.

References:

- [Phase 1-6 acceptance goal](../goals/phase1-6-acceptance-goal.zh.md)
- [Phase 6B task-pack catalog](phase6-real-provider-lab-task-packs.md)
- [L5 reviewer-rework / partial tranche](phase6b-reviewer-rework-partial-observation-tranche.md)
- [Phase 6B claim coverage matrix](phase6b-real-provider-claim-coverage-matrix.md)
- [Phase 6B launch checklist](phase6b-real-provider-lab-launch-checklist.md)
- Reviewer2 L5 plan-only acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_3824dde8454e-art_f877efe2b9434c4f.txt`
- Reviewer2 static normalizer-shape acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f20daf37898d-art_82078d731cc04aa7.txt`
- Accepted ask-first system-sender source repair:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_766050825b27-art_2c89fbbb8e0f4b4d.txt`
- Reviewer2 repeat4 approval-to-run:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5dd131a6ea7e-art_a6ee6ab2386b4d47.txt`
- Previous ask-first child-ask chain-routing source repair, superseded by the
  system-sender repair for this repeat4 packet:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_56466011201a-art_21f1debeb5a44a6c.txt`
- Consumed first L5 partial-only approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_4e3c051ef168-art_c4326a8f0ce149b6.txt`
- Consumed L5 partial-only repeat2 approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_af5f6fb64a7d-art_974ef1da251d43fc.txt`
- Consumed L5 partial-only repeat3 approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_de6263827473-art_3efd39f6836548b8.txt`
- Repeat3 B7 report:
  [../history/phase6b-real-provider-l5-partial-repeat3-b7-20260704.md](../history/phase6b-real-provider-l5-partial-repeat3-b7-20260704.md)

## Claim Boundary

- L0 repeat6 remains L0 runtime-sanity evidence only.
- L1-L4 is a separate lane currently held for checkpoint/resume repair and is
  not combined with this request.
- Reviewer-rework is not requested in this first L5 run. If the partial row
  passes as `valid_non_success`, the reviewer-rework candidate remains optional
  follow-up evidence, not a prerequisite for this specific L5 observation.
- Phase 6B remains unclaimed until reviewer-gated L1-L4/L5 runtime evidence,
  B7 aggregation, cleanup/authority audits, and final claim review all exist.
- Reviewer2 approval `job_4e3c051ef168` and root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704` were
  consumed once and are historical, not runnable. That run failed before
  provider ask activation because `init` did not materialize
  `docs/plantree/plans/phase6b-real-provider-l5` before `plan task-create`.
  B7 was captured as `not_claimable` / `test_design_failure`, then post-B7
  cleanup returned `state: unmounted`.
- Reviewer2 approval `job_af5f6fb64a7d`, urgent addendum `job_663bad41c855`,
  and root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704`
  were consumed once and are historical, not runnable. That run reached
  `direct_execution`, then blocked with `round_result_source=ask_submission_failed`
  because ask-first submitted a plain child `ask` from an active CCB task. The
  source repair accepted by reviewer2 `job_56466011201a` now requires
  result-needed ask-first child asks to use `ParsedAskCommand(callback=True)`,
  which maps to CCB chain routing.
- Reviewer2 approval `job_de6263827473` and root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704`
  were consumed once and are historical, not runnable. That run inherited the
  current system provider environment, reached `direct_execution`, and produced
  worker partial evidence. Reviewer ask submission then failed before a
  reviewer verdict with `ask --chain requires an active parent job for the
  sender`. B7 was captured as `not_claimable` / `test_design_failure`, then
  post-B7 cleanup returned `kill_status: ok`, `state: unmounted` after
  retrying cleanup with lab-local `AGENT_ROLES_STORE`. The repeat3 B7 report is
  not claimable.
- The ask-first system-sender source repair accepted by reviewer2
  `job_766050825b27` now makes watched ask-first child asks runner-owned with
  `sender='system'`, `callback=False`, `silence=False`, and immediate
  `watch_ask_job`. Repeat4 must verify that repair before it starts.

## Launch-Specific Verdict

Reviewer2 returned:

- `APPROVAL-TO-RUN GRANTED`: exactly one L5 partial-only repeat4 run was
  approved for the root and command shape in this packet.

This approval was consumed by one talk2-supervised run. It must not be reused
for repeat1, repeat2, repeat3, repeat4 reruns, L1-L4, reviewer-rework,
production/default enablement, or Phase 6B completion. Worker3 did not execute
it.

## Proposed Lab Root

Fresh external lab root:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704
```

Fresh lab project root:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704/l5-partial-real-provider-lab
```

Environment policy:

```text
HOME=inherited from current system provider environment; do not export lab-local HOME
CCB_SOURCE_HOME=inherited from current system provider environment; do not export lab-local CCB_SOURCE_HOME
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704/roles
```

Provider-home policy:

```text
approved_inherited_current_real_provider_home
```

Provider profile map:

```json
{
  "ccb_frontdesk": "codex",
  "ccb_planner": "codex",
  "ccb_orchestrator": "codex",
  "ccb_task_detailer": "codex",
  "ccb_round_reviewer": "claude",
  "coder": "codex",
  "code_reviewer": "codex"
}
```

## Planned Task

| Order | Task id | Complexity | Expected route | Expected round result | Expected endpoint | Expected classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `phase6b-l5-partial-budget-source-gap` | L5 | `direct_execution` | `partial` | `partial` | `valid_non_success` |

Fixture shape:

- Present file:
  `lab_docs/l5_partial_existing_summary.md`.
- Intentionally absent source dependency:
  `lab_docs/l5_partial_required_source.md`.
- Task packet forbids inventing missing source content.
- Execution contract requires a partial result if the required source is absent:
  completed and unfinished steps must be explicit, reviewer must cite
  `task_packet` and `execution_contract`, and partial must not be marked
  `done`.

Reviewer-rework candidate
`phase6b-l5-reviewer-bounded-rework-contract` remains outside this launch
request. It must not appear in the active command, active normalizer task list,
or approved task sequence unless reviewer2 explicitly requests a combined or
ordered future packet.

## Artifact Paths

The future run must use these paths:

```text
$PHASE6B_L5_ROOT/run_l5.sh
$PHASE6B_L5_ROOT/run_l5.sh.sha256
$PHASE6B_L5_ROOT/phase6b_l5_partial_only_repeat4_command_log.jsonl
$PHASE6B_L5_ROOT/rows/phase6b_l5_partial_only_repeat4_evidence_rows.jsonl
$PHASE6B_L5_ROOT/cleanup/post_b7_cleanup.json
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/task_packet.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/execution_contract.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/route.txt
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/orchestration_notes.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/worker_reply.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/reviewer_verdict.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/round_summary.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/partial_evidence.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/completed_steps.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/unfinished_steps.md
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/runtime_residue.json
$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/release.json
/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md
```

## Frozen L5 Command Shape

Status: APPROVED FROZEN COMMAND SHAPE / RUN EXACTLY ONCE UNDER TALK2
SUPERVISION ONLY.

The command shape is checkpointed and stdin-safe. Provider replies are evidence
only; route and round/status authority must be imported by scripts. The script
refuses to continue when supervisor checkpoint artifacts are absent. The outer
command only materializes a lab-local phase driver under a fresh root; it does
not start the L5 task.

```bash
# APPROVED by reviewer2 job_5dd131a6ea7e for exactly one supervised repeat4 run.
# Do not reuse after one run, and do not broaden the task scope.
cd /home/bfly/yunwei/test_ccb2

set -uo pipefail

export PHASE6B_L5_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704
export PHASE6B_L5_PROJECT="$PHASE6B_L5_ROOT/l5-partial-real-provider-lab"
export PHASE6B_L5_SCRIPT="$PHASE6B_L5_ROOT/run_l5.sh"
export AGENT_ROLES_STORE="$PHASE6B_L5_ROOT/roles"

case "$PWD" in
  /home/bfly/yunwei/test_ccb2|/home/bfly/yunwei/test_ccb2/*) ;;
  *) echo "refuse: L5 must run from /home/bfly/yunwei/test_ccb2" >&2; exit 64 ;;
esac

case "$PHASE6B_L5_PROJECT" in
  "$PHASE6B_L5_ROOT"/*) ;;
  *) echo "refuse: project must live under PHASE6B_L5_ROOT" >&2; exit 64 ;;
esac

case "$AGENT_ROLES_STORE" in
  "$PHASE6B_L5_ROOT"/roles) ;;
  *) echo "refuse: AGENT_ROLES_STORE must be lab-local" >&2; exit 64 ;;
esac

case "${HOME:-}" in
  "$PHASE6B_L5_ROOT"/*)
    echo "refuse: real-provider L5 must inherit HOME from the current system provider environment" >&2
    exit 64
    ;;
esac

case "${CCB_SOURCE_HOME:-}" in
  "$PHASE6B_L5_ROOT"/*)
    echo "refuse: real-provider L5 must inherit CCB_SOURCE_HOME from the current system provider environment" >&2
    exit 64
    ;;
esac

if [ -e "$PHASE6B_L5_ROOT" ] && [ -n "$(find "$PHASE6B_L5_ROOT" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  echo "refuse: L5 root must be new or empty: $PHASE6B_L5_ROOT" >&2
  exit 65
fi

mkdir -p "$PHASE6B_L5_ROOT"

cat > "$PHASE6B_L5_SCRIPT" <<'RUN_L5_SH'
#!/usr/bin/env bash
set -uo pipefail

export PHASE6B_L5_ROOT=${PHASE6B_L5_ROOT:-/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704}
export PHASE6B_L5_PROJECT="$PHASE6B_L5_ROOT/l5-partial-real-provider-lab"
export PHASE6B_L5_PLAN_SLUG=phase6b-real-provider-l5
export PHASE6B_L5_PLAN_ROOT="$PHASE6B_L5_PROJECT/docs/plantree/plans/$PHASE6B_L5_PLAN_SLUG"
export PHASE6B_L5_SCRIPT="${PHASE6B_L5_SCRIPT:-$PHASE6B_L5_ROOT/run_l5.sh}"
export PHASE6B_L5_SCRIPT_SHA256_PATH="$PHASE6B_L5_ROOT/run_l5.sh.sha256"
export PHASE6B_L5_COMMAND_LOG="$PHASE6B_L5_ROOT/phase6b_l5_partial_only_repeat4_command_log.jsonl"
export PHASE6B_L5_ROWS_PATH="$PHASE6B_L5_ROOT/rows/phase6b_l5_partial_only_repeat4_evidence_rows.jsonl"
export PHASE6B_L5_SUPERVISION_DIR="$PHASE6B_L5_PROJECT/supervisor_imports"
export PHASE6B_L5_CLEANUP_PATH="$PHASE6B_L5_ROOT/cleanup/post_b7_cleanup.json"
export PHASE6B_L5_TIMEOUT_SECONDS=900
export AGENT_ROLES_STORE="$PHASE6B_L5_ROOT/roles"
export PHASE6B_L5_PROVIDER_HOME_MODE=approved_inherited_current_real_provider_home
export PHASE6B_L5_PROVIDER_PROFILE_MAP='{"ccb_frontdesk":"codex","ccb_planner":"codex","ccb_orchestrator":"codex","ccb_task_detailer":"codex","ccb_round_reviewer":"claude","coder":"codex","code_reviewer":"codex"}'
export PHASE6B_L5_TASK_ID=phase6b-l5-partial-budget-source-gap

case "$PWD" in
  /home/bfly/yunwei/test_ccb2|/home/bfly/yunwei/test_ccb2/*) ;;
  *) echo "refuse: L5 must run from /home/bfly/yunwei/test_ccb2" >&2; exit 64 ;;
esac

case "$PHASE6B_L5_SCRIPT" in
  "$PHASE6B_L5_ROOT"/run_l5.sh) ;;
  *) echo "refuse: PHASE6B_L5_SCRIPT must be lab-local run_l5.sh" >&2; exit 64 ;;
esac

case "${HOME:-}" in
  "$PHASE6B_L5_ROOT"/*)
    echo "refuse: real-provider L5 must inherit HOME from the current system provider environment" >&2
    exit 64
    ;;
esac

case "${CCB_SOURCE_HOME:-}" in
  "$PHASE6B_L5_ROOT"/*)
    echo "refuse: real-provider L5 must inherit CCB_SOURCE_HOME from the current system provider environment" >&2
    exit 64
    ;;
esac

run_l5_command() {
  local label="$1"
  shift
  local stdout_path="$PHASE6B_L5_ROOT/logs/${label}.stdout"
  local stderr_path="$PHASE6B_L5_ROOT/logs/${label}.stderr"
  local started_at
  local finished_at
  local rc
  mkdir -p "$PHASE6B_L5_ROOT/logs"
  started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  timeout --preserve-status "${PHASE6B_L5_TIMEOUT_SECONDS}s" "$@" \
    </dev/null >"$stdout_path" 2>"$stderr_path"
  rc=$?
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python - "$PHASE6B_L5_COMMAND_LOG" "$label" "$rc" "$stdout_path" "$stderr_path" "$started_at" "$finished_at" "$@" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

log_path, label, rc, stdout_path, stderr_path, started_at, finished_at, *argv = sys.argv[1:]
script_path = os.environ.get("PHASE6B_L5_SCRIPT")
script_sha256 = None
if script_path and Path(script_path).is_file():
    script_sha256 = hashlib.sha256(Path(script_path).read_bytes()).hexdigest()
record = {
    "label": label,
    "argv": argv,
    "returncode": int(rc),
    "stdout_path": stdout_path,
    "stderr_path": stderr_path,
    "started_at": started_at,
    "finished_at": finished_at,
    "script_path": script_path,
    "script_sha256": script_sha256,
}
with open(log_path, "a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
PY
  return "$rc"
}

run_required() {
  run_l5_command "$@"
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "required L5 command failed: $1 rc=$rc" >&2
    exit "$rc"
  fi
}

require_initialized() {
  if [ ! -f "$PHASE6B_L5_COMMAND_LOG" ] \
    || [ ! -f "$PHASE6B_L5_PROJECT/fixture_manifest.json" ] \
    || [ ! -d "$PHASE6B_L5_PLAN_ROOT" ] \
    || [ ! -f "$PHASE6B_L5_PROJECT/.ccb/ccb.config" ]; then
    echo "refuse: run init before L5 continuation phases" >&2
    exit 72
  fi
}

require_supervisor_file() {
  local task_id="$1"
  local artifact="$2"
  local path="$PHASE6B_L5_SUPERVISION_DIR/$task_id/$artifact"
  if [ ! -f "$path" ]; then
    echo "supervisor checkpoint required before continuing: $path" >&2
    exit 70
  fi
  printf '%s\n' "$path"
}

write_config() {
  mkdir -p "$PHASE6B_L5_PROJECT/.ccb" "$PHASE6B_L5_PROJECT/lab_docs" \
    "$PHASE6B_L5_PROJECT/drafts" "$PHASE6B_L5_ROOT/logs" \
    "$PHASE6B_L5_ROOT/rows" "$PHASE6B_L5_ROOT/cleanup" \
    "$PHASE6B_L5_PROJECT/docs/plantree/plans" \
    "$PHASE6B_L5_SUPERVISION_DIR" "$AGENT_ROLES_STORE/installed"

  cat > "$PHASE6B_L5_PROJECT/.ccb/ccb.config" <<'EOF'
frontdesk:codex; planner:codex; task_detailer:codex; orchestrator:codex; ccb_round_reviewer:claude

[agents.frontdesk]
role = "agentroles.ccb_frontdesk"

[agents.planner]
role = "agentroles.ccb_planner"

[agents.task_detailer]
role = "agentroles.ccb_task_detailer"

[agents.orchestrator]
role = "agentroles.ccb_orchestrator"

[agents.ccb_round_reviewer]
role = "agentroles.ccb_round_reviewer"

[loop.capacity]
enabled = true
max_nodes = 6
default_lifetime = "current_round"
name_template = "loop-{loop_id}-{profile}-{index}"
reuse = "prefer_idle"

[loop.role_profiles.ccb_frontdesk]
role = "agentroles.ccb_frontdesk"
provider = "codex"
workspace_mode = "inplace"
max_instances = 1
reuse = "prefer_idle"

[loop.role_profiles.ccb_planner]
role = "agentroles.ccb_planner"
provider = "codex"
workspace_mode = "inplace"
max_instances = 1
reuse = "prefer_idle"

[loop.role_profiles.ccb_orchestrator]
role = "agentroles.ccb_orchestrator"
provider = "codex"
workspace_mode = "inplace"
max_instances = 1
reuse = "prefer_idle"

[loop.role_profiles.ccb_task_detailer]
role = "agentroles.ccb_task_detailer"
provider = "codex"
workspace_mode = "inplace"
max_instances = 1
reuse = "prefer_idle"

[loop.role_profiles.ccb_round_reviewer]
role = "agentroles.ccb_round_reviewer"
provider = "claude"
workspace_mode = "inplace"
max_instances = 1
reuse = "prefer_idle"

[loop.role_profiles.coder]
role = "agentroles.coder"
provider = "codex"
workspace_mode = "copy"
max_instances = 1
reuse = "prefer_idle"

[loop.role_profiles.code_reviewer]
role = "agentroles.code_reviewer"
provider = "codex"
workspace_mode = "copy"
max_instances = 1
reuse = "prefer_idle"
EOF
}

materialize_plan_root() {
  mkdir -p "$PHASE6B_L5_PLAN_ROOT" "$PHASE6B_L5_PLAN_ROOT/tasks"
  cat > "$PHASE6B_L5_PROJECT/docs/plantree/README.md" <<'EOF'
# Lab Plan Tree

This lab-local plan tree exists only for the Phase 6B L5 partial-only launch
request. Runtime authority remains script-owned.
EOF
  cat > "$PHASE6B_L5_PLAN_ROOT/README.md" <<'EOF'
# Phase 6B Real Provider L5

Status: lab-local launch plan root

This minimal plan root exists so `ccb plan task-create --plan
phase6b-real-provider-l5` can create task records for the supervised L5
partial-only run.
EOF
}

validate_plan_root() {
  if [ ! -d "$PHASE6B_L5_PLAN_ROOT" ]; then
    echo "refuse: missing L5 plan root: $PHASE6B_L5_PLAN_ROOT" >&2
    exit 73
  fi
}

verify_ask_first_system_sender_repair() {
  python - <<'PY'
import re
from pathlib import Path

source = Path("/home/bfly/yunwei/ccb_source/lib/cli/services/loop_ask_first.py").read_text(encoding="utf-8")
if "RUNNER_ASK_SENDER = 'system'" not in source:
    raise SystemExit("refuse: accepted ask-first system-sender repair is absent")
match = re.search(
    r"def _submit_and_watch\(\n(?P<body>.*?)(?=\ndef _worker_message\()",
    source,
    flags=re.S,
)
if not match:
    raise SystemExit("refuse: ask-first _submit_and_watch guard not found")
body = match.group("body")
if "sender=RUNNER_ASK_SENDER" not in body:
    raise SystemExit("refuse: ask-first watched child asks are not runner-owned")
if "watch_ask_job" not in body:
    raise SystemExit("refuse: ask-first watched child asks are not watched immediately")
if "callback=True" in body or "silence=True" in body:
    raise SystemExit("refuse: watched ask-first child asks must not request callback or silence")
PY
}

seed_rolepacks() {
  local role_id
  for role_id in \
    agentroles.ccb_frontdesk \
    agentroles.ccb_planner \
    agentroles.ccb_orchestrator \
    agentroles.ccb_task_detailer \
    agentroles.ccb_round_reviewer \
    agentroles.coder \
    agentroles.code_reviewer
  do
    local src="/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/drafts/${role_id}"
    local dst="$AGENT_ROLES_STORE/installed/${role_id}/current"
    test -d "$src"
    rm -rf "$dst"
    mkdir -p "$(dirname "$dst")"
    cp -a "$src" "$dst"
  done
}

write_fixtures() {
  python - "$PHASE6B_L5_PROJECT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

project = Path(sys.argv[1])
summary = project / "lab_docs" / "l5_partial_existing_summary.md"
missing = project / "lab_docs" / "l5_partial_required_source.md"
summary.parent.mkdir(parents=True, exist_ok=True)
initial = "# L5 Partial Existing Summary\n\nstatus: needs-source-sync\n"
summary.write_text(initial, encoding="utf-8")
if missing.exists():
    raise SystemExit(f"refuse: missing-source fixture unexpectedly exists: {missing}")
manifest = {
    "schema": "phase6b.l5.partial.fixture_manifest.v1",
    "fixtures": [
        {
            "path": "lab_docs/l5_partial_existing_summary.md",
            "sha256": hashlib.sha256(initial.encode("utf-8")).hexdigest(),
            "expected_state": "present",
        },
        {
            "path": "lab_docs/l5_partial_required_source.md",
            "expected_state": "absent",
            "purpose": "bounded partial trigger; worker must not invent content",
        },
    ],
}
(project / "fixture_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

create_task_files() {
  local task_id="$PHASE6B_L5_TASK_ID"
  local prompt_file="$PHASE6B_L5_PROJECT/drafts/${task_id}.task_packet.md"
  local contract_file="$PHASE6B_L5_PROJECT/drafts/${task_id}.execution_contract.md"
  local supervisor_dir="$PHASE6B_L5_SUPERVISION_DIR/$task_id"
  mkdir -p "$supervisor_dir"
  cat > "$prompt_file" <<'EOF'
# Task Packet

task_id: phase6b-l5-partial-budget-source-gap
expected_route: direct_execution
expected_round_result: partial
expected_final_status: partial

Update only `lab_docs/l5_partial_existing_summary.md` using
`lab_docs/l5_partial_required_source.md`.

The required source file is intentionally absent. Do not invent source content.
If the source is absent, complete only the safe inspection/update work, return
partial, and list completed and unfinished steps explicitly.
EOF
  cat > "$contract_file" <<'EOF'
# Execution Contract

- Provider replies are evidence only.
- Route and round/status authority must be script-owned imports.
- No topology communication DSL, no topology_dispatch.json, and no provider
  reply authority parsing.
- Worker must cite `task_packet` and `execution_contract`.
- Reviewer must cite `task_packet` and `execution_contract`.
- Partial must not be marked `done`.
- Completed and unfinished steps must be explicit.
EOF
  cp "$prompt_file" "$supervisor_dir/task_packet.md"
  cp "$contract_file" "$supervisor_dir/execution_contract.md"
}

create_task_record() {
  local task_id="$PHASE6B_L5_TASK_ID"
  validate_plan_root
  create_task_files
  run_required "${task_id}__task_create" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    plan task-create --plan "$PHASE6B_L5_PLAN_SLUG" --title "$task_id" --task-id "$task_id" --json
  run_required "${task_id}__artifact_task_packet" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    plan task-artifact --task "$task_id" --kind task_packet \
    --file "$PHASE6B_L5_PROJECT/drafts/${task_id}.task_packet.md" --json
  run_required "${task_id}__artifact_execution_contract" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    plan task-artifact --task "$task_id" --kind execution_contract \
    --file "$PHASE6B_L5_PROJECT/drafts/${task_id}.execution_contract.md" --json
  run_required "${task_id}__ready_for_orchestration" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    plan task-status --task "$task_id" --status ready_for_orchestration \
    --next-owner orchestrator --activation-reason phase6b_l5_partial_launch --json
}

activate_orchestrator_and_stop() {
  local task_id="$PHASE6B_L5_TASK_ID"
  run_required "${task_id}__activate_orchestrator" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    loop runner --once --timeout "$PHASE6B_L5_TIMEOUT_SECONDS" --json
  echo "STOP: supervisor must import direct_execution route for $task_id before continuing." >&2
}

import_supervisor_route() {
  local task_id="$PHASE6B_L5_TASK_ID"
  local route_file
  local notes_file
  local observed_route
  route_file="$(require_supervisor_file "$task_id" route.txt)"
  notes_file="$(require_supervisor_file "$task_id" orchestration_notes.md)"
  observed_route="$(tr -d '[:space:]' < "$route_file")"
  if [ "$observed_route" != "direct_execution" ]; then
    echo "route mismatch for $task_id: expected direct_execution observed $observed_route" >&2
    exit 71
  fi
  run_required "${task_id}__import_orchestration_notes_direct_execution" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    plan task-artifact --task "$task_id" --kind orchestration_notes \
    --file "$notes_file" --route "$observed_route" --json
}

run_direct_execution_round() {
  local task_id="$PHASE6B_L5_TASK_ID"
  run_required "${task_id}__run_direct_execution_round" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    loop runner --once --timeout "$PHASE6B_L5_TIMEOUT_SECONDS" --json
  echo "STOP: supervisor must capture partial evidence and round_summary before B7." >&2
}

finalize_partial_evidence() {
  local task_id="$PHASE6B_L5_TASK_ID"
  require_initialized
  require_supervisor_file "$task_id" worker_reply.md >/dev/null
  require_supervisor_file "$task_id" reviewer_verdict.md >/dev/null
  require_supervisor_file "$task_id" round_summary.md >/dev/null
  require_supervisor_file "$task_id" partial_evidence.md >/dev/null
  require_supervisor_file "$task_id" completed_steps.md >/dev/null
  require_supervisor_file "$task_id" unfinished_steps.md >/dev/null
  require_supervisor_file "$task_id" runtime_residue.json >/dev/null
  require_supervisor_file "$task_id" release.json >/dev/null
  run_required "${task_id}__task_show_after_round" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" \
    plan task-show --task "$task_id" --json
  run_required config_validate_after_l5 \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" config validate
}

init_lab() {
  sha256sum "$PHASE6B_L5_SCRIPT" > "$PHASE6B_L5_SCRIPT_SHA256_PATH"
  : > "$PHASE6B_L5_COMMAND_LOG"
  verify_ask_first_system_sender_repair
  write_config
  materialize_plan_root
  seed_rolepacks
  write_fixtures
  run_required diagnose /home/bfly/yunwei/ccb_source/ccb_test --diagnose
  run_required config_validate_initial \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT" config validate
  run_required start_project \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L5_PROJECT"
}

main() {
  case "${1:-}" in
    init)
      init_lab
      ;;
    start-partial)
      require_initialized
      create_task_record
      activate_orchestrator_and_stop
      ;;
    continue-partial-route)
      require_initialized
      import_supervisor_route
      run_direct_execution_round
      ;;
    finalize-partial)
      finalize_partial_evidence
      ;;
    *)
      printf '%s\n' \
        'usage:' \
        '  run_l5.sh init' \
        '  run_l5.sh start-partial' \
        '  run_l5.sh continue-partial-route' \
        '  run_l5.sh finalize-partial' >&2
      exit 64
      ;;
  esac
}

main "$@"
RUN_L5_SH

chmod +x "$PHASE6B_L5_SCRIPT"
printf 'materialized L5 phase driver: %s\n' "$PHASE6B_L5_SCRIPT"
printf 'run the approved supervised continuation commands in the next section\n'
```

## Supervised Continuation Command Sequence

The materialization command above creates the phase driver only. The launch
supervisor must then run these commands one at a time from
`/home/bfly/yunwei/test_ccb2`. Do not pipe this sequence through stdin, do not
poll for checkpoint files, and do not run a continuation command before its
precondition is satisfied.

Shared environment:

```bash
cd /home/bfly/yunwei/test_ccb2
export PHASE6B_L5_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704
export PHASE6B_L5_PROJECT="$PHASE6B_L5_ROOT/l5-partial-real-provider-lab"
export PHASE6B_L5_SCRIPT="$PHASE6B_L5_ROOT/run_l5.sh"
export AGENT_ROLES_STORE="$PHASE6B_L5_ROOT/roles"
```

| Order | Preconditions | Approved command |
| :--- | :--- | :--- |
| 0 | Materialization command succeeded. | `bash "$PHASE6B_L5_SCRIPT" init` |
| 1 | Init succeeded. | `bash "$PHASE6B_L5_SCRIPT" start-partial` |
| 2 | Supervisor created project-local `supervisor_imports/phase6b-l5-partial-budget-source-gap/route.txt` with `direct_execution` and `orchestration_notes.md`. | `bash "$PHASE6B_L5_SCRIPT" continue-partial-route` |
| 3 | Direct-execution round returned and script-owned round import evidence exists. Supervisor created `worker_reply.md`, `reviewer_verdict.md`, `round_summary.md`, `partial_evidence.md`, `completed_steps.md`, `unfinished_steps.md`, `runtime_residue.json`, and `release.json`. | `bash "$PHASE6B_L5_SCRIPT" finalize-partial` |
| 4 | Finalize succeeded. | Run the exact B7 normalization command in the next section before any external cleanup. |

## B7 Normalization Command Shape

Exact B7 normalization command shape for reviewer approval:

```bash
# Run only after approved L5 repeat4 execution evidence exists and before external cleanup.
python - "$PHASE6B_L5_ROOT" \
  /home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l5-partial-repeat4-b7-20260704.md <<'PY'
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
b7_path = Path(sys.argv[2])
task_id = "phase6b-l5-partial-budget-source-gap"
project = root / "l5-partial-real-provider-lab"
task_dir = project / "supervisor_imports" / task_id
command_log_path = root / "phase6b_l5_partial_only_repeat4_command_log.jsonl"
rows_path = root / "rows" / "phase6b_l5_partial_only_repeat4_evidence_rows.jsonl"
cleanup_path = root / "cleanup" / "post_b7_cleanup.json"

provider_mix = {
    "ccb_frontdesk": "codex",
    "ccb_planner": "codex",
    "ccb_orchestrator": "codex",
    "ccb_task_detailer": "codex",
    "ccb_round_reviewer": "claude",
    "coder": "codex",
    "code_reviewer": "codex",
}
shared_fields = [
    "task_id",
    "complexity_level",
    "provider_mix",
    "expected_route",
    "observed_route",
    "route_decision_correct",
    "required_artifacts_present",
    "ask_reachability",
    "detailer_activated_expected",
    "detailer_activated_observed",
    "worker_reviewer_ask_success",
    "reviewer_contract_citation",
    "round_result",
    "final_status",
    "cleanup_result",
    "runtime_residue",
    "role_boundary_violations",
    "authority_write_violations",
    "classification",
    "human_diagnosis_summary",
]
l5_fields = [
    "observation_type",
    "failure_domain",
    "rework_attempt_count",
    "rework_attempt_limit",
    "reviewer_rework_observed",
    "reviewer_rework_request_path",
    "reviewer_final_verdict_path",
    "partial_observed",
    "partial_completed_steps",
    "partial_unfinished_steps",
    "partial_reason",
    "provider_format_drift",
    "busy_retain_observed",
    "topology_dispatch_absent",
    "topology_communication_dsl_absent",
    "provider_reply_authority_parsing_absent",
    "release_blockers",
    "release_incomplete_agents",
]

def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""

def read_lines(path):
    return [line.strip() for line in read_text(path).splitlines() if line.strip()]

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default

def load_jsonl(path):
    records = []
    if not path.is_file():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records

def summary_field(text, field, default):
    match = re.search(rf"^{re.escape(field)}:\s*(.+)$", text, flags=re.M)
    return match.group(1).strip() if match else default

def has_dispatch_keys(payload):
    if isinstance(payload, dict):
        if any(key in payload for key in ("edges", "gates", "artifacts")):
            return True
        return any(has_dispatch_keys(value) for value in payload.values())
    if isinstance(payload, list):
        return any(has_dispatch_keys(value) for value in payload)
    return False

def topology_paths():
    return [
        path
        for path in root.rglob("*.json")
        if path.name.startswith("agent_mount_topology") or path.parent.name == "topology_proposals"
    ]

def topology_communication_dsl_absent():
    paths = topology_paths()
    if not paths:
        return False
    return not any(has_dispatch_keys(load_json(path, {})) for path in paths)

def bounded_release(release_payload, cleanup_result):
    blockers = release_payload.get("release_blockers", {})
    incomplete = release_payload.get("release_incomplete_agents", [])
    if cleanup_result == "released":
        return not blockers and not incomplete
    if cleanup_result != "release_incomplete":
        return False
    if not isinstance(blockers, dict) or not blockers:
        return False
    allowed = {"parked", "drained", "retained_busy", "parked_after_release", "inherited_provider_home_safety"}
    for value in blockers.values():
        if not isinstance(value, dict):
            return False
        reason = str(value.get("reason") or value.get("lifecycle_state") or value.get("observed_state") or "")
        if reason not in allowed:
            return False
    return isinstance(incomplete, list) and bool(incomplete)

command_records = load_jsonl(command_log_path)
labels = {str(record.get("label")): record for record in command_records}
summary_text = read_text(task_dir / "round_summary.md")
reviewer_text = read_text(task_dir / "reviewer_verdict.md")
release_payload = load_json(task_dir / "release.json", {})
runtime_residue = load_json(task_dir / "runtime_residue.json", {})
role_boundary_violations = load_json(task_dir / "role_boundary_violations.json", [])
authority_write_violations = load_json(task_dir / "authority_write_violations.json", [])
route = read_text(task_dir / "route.txt").strip() or "unknown"
round_result = summary_field(summary_text, "round_result", "unknown")
final_status = summary_field(summary_text, "final_status", "unknown")
cleanup_result = summary_field(summary_text, "cleanup_result", "unknown")
required_artifacts = [
    "task_packet.md",
    "execution_contract.md",
    "orchestration_notes.md",
    "worker_reply.md",
    "reviewer_verdict.md",
    "round_summary.md",
    "partial_evidence.md",
    "completed_steps.md",
    "unfinished_steps.md",
    "runtime_residue.json",
    "release.json",
]
row = {
    "task_id": task_id,
    "complexity_level": "L5",
    "provider_mix": provider_mix,
    "expected_route": "direct_execution",
    "observed_route": route,
    "route_decision_correct": route == "direct_execution",
    "required_artifacts_present": all((task_dir / artifact).is_file() for artifact in required_artifacts),
    "ask_reachability": f"{task_id}__run_direct_execution_round" in labels,
    "detailer_activated_expected": False,
    "detailer_activated_observed": f"{task_id}__activate_detailer" in labels,
    "worker_reviewer_ask_success": (task_dir / "worker_reply.md").is_file() and (task_dir / "reviewer_verdict.md").is_file(),
    "reviewer_contract_citation": str(task_dir / "execution_contract.md")
    if "task_packet" in reviewer_text and "execution_contract" in reviewer_text
    else None,
    "round_result": round_result,
    "final_status": final_status,
    "cleanup_result": cleanup_result,
    "runtime_residue": {
        "dynamic_agents_absent": runtime_residue.get("dynamic_agents_absent"),
        "config_dynamic_agents_absent": runtime_residue.get("config_dynamic_agents_absent"),
        "observed_topology_residue_absent": runtime_residue.get("observed_topology_residue_absent"),
    },
    "role_boundary_violations": role_boundary_violations if isinstance(role_boundary_violations, list) else ["invalid role-boundary evidence"],
    "authority_write_violations": authority_write_violations if isinstance(authority_write_violations, list) else ["invalid authority evidence"],
    "classification": "test_design_failure",
    "human_diagnosis_summary": "missing or incomplete L5 partial evidence",
    "observation_type": "partial_completion",
    "failure_domain": "task_scope",
    "rework_attempt_count": 0,
    "rework_attempt_limit": 1,
    "reviewer_rework_observed": False,
    "reviewer_rework_request_path": None,
    "reviewer_final_verdict_path": None,
    "partial_observed": round_result == "partial" or final_status == "partial",
    "partial_completed_steps": read_lines(task_dir / "completed_steps.md"),
    "partial_unfinished_steps": read_lines(task_dir / "unfinished_steps.md"),
    "partial_reason": read_text(task_dir / "partial_evidence.md").strip() or None,
    "provider_format_drift": (task_dir / "provider_format_drift.md").is_file(),
    "busy_retain_observed": (task_dir / "busy_retain_observed.md").is_file(),
    "topology_dispatch_absent": not any(root.rglob("topology_dispatch.json")),
    "topology_communication_dsl_absent": topology_communication_dsl_absent(),
    "provider_reply_authority_parsing_absent": (task_dir / "round_summary.md").is_file()
    and not (task_dir / "provider_reply_authority_import.json").exists(),
    "release_blockers": release_payload.get("release_blockers", {}),
    "release_incomplete_agents": release_payload.get("release_incomplete_agents", []),
    "cleanup_evidence_path": str(cleanup_path),
}
if row["authority_write_violations"] or row["role_boundary_violations"]:
    row["classification"] = "system_failure"
    row["human_diagnosis_summary"] = "authority or role-boundary violation evidence is present"
elif (
    row["route_decision_correct"]
    and row["required_artifacts_present"]
    and row["ask_reachability"]
    and row["worker_reviewer_ask_success"]
    and row["reviewer_contract_citation"]
    and row["round_result"] == "partial"
    and row["final_status"] == "partial"
    and row["partial_completed_steps"]
    and row["partial_unfinished_steps"]
    and row["topology_dispatch_absent"]
    and row["topology_communication_dsl_absent"]
    and row["provider_reply_authority_parsing_absent"]
    and bounded_release(release_payload, cleanup_result)
):
    row["classification"] = "valid_non_success"
    row["human_diagnosis_summary"] = "bounded partial observation with explicit completed and unfinished steps"

for field in shared_fields + l5_fields:
    if field not in row:
        row["classification"] = "test_design_failure"
        row.setdefault("test_design_failures", []).append(f"missing row field: {field}")

observation_requirement_met = row["classification"] == "valid_non_success" and row["partial_observed"]
failure_taxonomy = {
    name: 1 if row["classification"] == name else 0
    for name in ["pass", "valid_non_success", "system_failure", "role_failure", "provider_failure", "test_design_failure"]
}
aggregate_status = "valid_non_success" if observation_requirement_met else "not_claimable"

rows_path.parent.mkdir(parents=True, exist_ok=True)
rows_path.write_text(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
b7_path.parent.mkdir(parents=True, exist_ok=True)
b7_path.write_text(
    "\n".join(
        [
            "# Phase 6B L5 Partial B7 Report",
            "",
            f"Status: {aggregate_status}",
            "",
            "## Claim Boundary",
            "",
            "This report covers only the approved L5 partial-only observation tranche.",
            "It does not approve L1-L4, reviewer-rework follow-up, or Phase 6B completion.",
            "",
            "## Observation Requirement",
            "",
            f"reviewer_rework_or_partial_observed={str(observation_requirement_met).lower()}",
            "",
            "## Row",
            "",
            "```json",
            json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Failure Taxonomy",
            "",
            "```json",
            json.dumps(failure_taxonomy, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
        ]
    )
    + "\n",
    encoding="utf-8",
)
PY
```

## Required B7 Row Fields

Every row must include at least:

```text
task_id
complexity_level
provider_mix
expected_route
observed_route
route_decision_correct
required_artifacts_present
ask_reachability
detailer_activated_expected
detailer_activated_observed
worker_reviewer_ask_success
reviewer_contract_citation
round_result
final_status
cleanup_result
runtime_residue
role_boundary_violations
authority_write_violations
classification
human_diagnosis_summary
```

Additional required L5 fields:

```text
observation_type
failure_domain
rework_attempt_count
rework_attempt_limit
reviewer_rework_observed
reviewer_rework_request_path
reviewer_final_verdict_path
partial_observed
partial_completed_steps
partial_unfinished_steps
partial_reason
provider_format_drift
busy_retain_observed
topology_dispatch_absent
topology_communication_dsl_absent
provider_reply_authority_parsing_absent
release_blockers
release_incomplete_agents
```

## Stop Conditions

Stop the launch before the next command if:

- reviewer2 has not granted approval-to-run for this exact root and command
  shape;
- the root is not fresh or is outside `/home/bfly/yunwei/test_ccb2`;
- external test root, inherited provider environment policy, or lab-local
  `AGENT_ROLES_STORE` is wrong;
- inherited provider home was not explicitly accepted by the reviewer verdict;
- route checkpoint is missing or is not `direct_execution`;
- required task, contract, worker, reviewer, partial, round, runtime residue, or
  release evidence is missing;
- reviewer does not cite `task_packet` and `execution_contract`;
- partial completed or unfinished steps are empty or vague;
- provider reply text mutates authority state or provider-reply authority parsing appears;
- topology dispatch, topology communication DSL, or `topology_dispatch.json`
  appears in mainline evidence;
- cleanup/release leaves unbounded residue;
- the row would classify as `pass`, `system_failure`, `role_failure`,
  `provider_failure`, or `test_design_failure` instead of bounded
  `valid_non_success`.

Run the B7 normalization command before any external cleanup. Post-B7 external
cleanup evidence, if needed, must be written to
`$PHASE6B_L5_ROOT/cleanup/post_b7_cleanup.json`.

## Future Claim Boundary

Approval-to-run, if reviewer2 grants it, authorizes exactly one future
supervised L5 partial-only run. It does not approve L1-L4, does not approve the
reviewer-rework optional task, does not claim Phase 6B, and does not authorize
production/default enablement.
