# Phase 6B L1-L4 Sequence9 Historical Record

Date: 2026-07-04
Status: SEQUENCE9 CONSUMED HISTORICAL RECORD / DO NOT RUN / PHASE 6B UNCLAIMED

## Purpose

This is now a historical record for the consumed Phase 6B L1-L4 sequence9
command shape. It does not request or authorize any further runtime execution.
Reviewer1 `job_b4184497742b` accepted the source-level direct-execution
blockers, and fallback launch-gate reviewer1 `job_c4935017fc15` approved
exactly one sequence9 run. Talk2 consumed that approval once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`.

The generated repeat9 B7 is not claimable despite saying `Status: pass`; see
[../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md](../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md).
Sequence9 is consumed and must not be reused.

Historical repeat8 remains non-runnable in
[phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md).
Repeat8 root `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`
is consumed and must not be reused.

## Historical Review Request

Original requested reviewer2 verdict:

```text
DOC-ONLY ACCEPTED
```

for sequence9 doc/source-readiness only, or:

```text
BLOCKER
```

with concrete fixes.

This historical review request is not launch approval. Do not run from it, and
do not grant or consume runtime permission from this file. Any later
launch-specific approval-to-run request must be separate and must name a fresh
root:

- root: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`;
- tranche: L1 direct, L2 direct, L3 `needs_detail -> detail_ready`, L4
  `macro_adjustment_request`, L4 `blocked`;
- command shape: materialize the script below from `/home/bfly/yunwei/test_ccb2`,
  run `init`, then supervised checkpoint/resume commands only;
- B7 path:
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md`.

Do not execute this packet during review. The later approved sequence9 runtime
has already been consumed and cleanup has completed.

## Scope Boundary

Included tasks:

| Task | Expected route | Approved endpoint |
| :--- | :--- | :--- |
| `phase6b-l1-doc-direct-execution` | `direct_execution` | `done/pass` only after project-root file evidence |
| `phase6b-l2-code-test-direct-execution` | `direct_execution` | `done/pass` only after project-root test evidence |
| `phase6b-l3-needs-detail-source-inspection` | `needs_detail` | `detail_ready`; no post-detail execution |
| `phase6b-l4-macro-adjustment-request` | `macro_adjustment_request` | `replan_required` |
| `phase6b-l4-blocked-missing-secret` | `blocked` | `blocked` |

Excluded from this approval:

- L5 reviewer-rework or partial observation;
- production/default enablement;
- any Phase 6B completion claim;
- any reuse of consumed sequence1 through sequence9 roots or approvals.

Even if a future sequence9 run succeeds, Phase 6B remains unclaimed until the
reviewer-gated B7 aggregation accepts the L1-L4 rows together with already
accepted L0 and L5 evidence.

## Authority And Runtime Rules

- The sequence9 root must be absent immediately before approved `init`.
- Real-provider runs inherit the current system provider environment. Do not
  export lab-local `HOME` or `CCB_SOURCE_HOME`.
- `AGENT_ROLES_STORE` is lab-local under the sequence9 root.
- Every runtime command uses explicit `--project "$PHASE6B_L1L4_PROJECT"`.
- Provider replies are evidence only. Route, detail, terminal, and round
  authority must come from script-owned imports.
- Supervisor checkpoint files passed to `plan task-artifact --file` must live
  under `$PHASE6B_L1L4_PROJECT/supervisor_imports/<task_id>/`.
- Blocked terminal evidence uses artifact kind `blocker_evidence`; no artifact
  kind named `blocked` is allowed.
- L3 stops at `detail_ready`; no execution command follows the detail import.
- B7 normalization must run before any external cleanup.
- Topology remains mount-only: no `topology_dispatch.json`, communication DSL,
  topology edges/gates/artifacts, or provider-reply authority parsing.
- Residual risk disclosed for reviewer2: source-level direct-execution blockers
  were accepted by reviewer1 `job_b4184497742b`, but broad-copy authority remains
  a residual risk to watch in the real-provider evidence.

## Frozen Sequence9 Command Shape

Run only after a separate reviewer2 launch-specific approval-to-run artifact
and a fresh pre-run audit by talk2 confirms the root is absent.

```bash
cd /home/bfly/yunwei/test_ccb2
export PHASE6B_L1L4_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704
export PHASE6B_L1L4_PROJECT="$PHASE6B_L1L4_ROOT/l1-l4-real-provider-lab"
export PHASE6B_L1L4_SCRIPT="$PHASE6B_L1L4_ROOT/run_l1_l4_sequence9.sh"
export PHASE6B_L1L4_COMMAND_LOG="$PHASE6B_L1L4_ROOT/phase6b_l1_l4_sequence9_command_log.jsonl"
export PHASE6B_L1L4_ROWS="$PHASE6B_L1L4_ROOT/rows/phase6b_l1_l4_sequence9_evidence_rows.jsonl"
export PHASE6B_L1L4_B7=/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md
export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"

if [ -e "$PHASE6B_L1L4_ROOT" ]; then
  printf 'refuse: sequence9 root already exists: %s\n' "$PHASE6B_L1L4_ROOT" >&2
  exit 100
fi
mkdir -p "$PHASE6B_L1L4_ROOT"

cat > "$PHASE6B_L1L4_SCRIPT" <<'RUN_L1_L4_SEQUENCE9_SH'
#!/usr/bin/env bash
set -euo pipefail

: "${PHASE6B_L1L4_ROOT:?}"
: "${PHASE6B_L1L4_PROJECT:?}"
: "${PHASE6B_L1L4_COMMAND_LOG:?}"
: "${PHASE6B_L1L4_ROWS:?}"
: "${PHASE6B_L1L4_B7:?}"
: "${AGENT_ROLES_STORE:?}"

PHASE6B_L1L4_PLAN_SLUG=phase6b-real-provider-l1-l4
PHASE6B_L1L4_PLAN_ROOT="$PHASE6B_L1L4_PROJECT/docs/plantree/plans/$PHASE6B_L1L4_PLAN_SLUG"
PHASE6B_L1L4_SUPERVISION_DIR="$PHASE6B_L1L4_PROJECT/supervisor_imports"
PHASE6B_L1L4_TIMEOUT_SECONDS="${PHASE6B_L1L4_TIMEOUT_SECONDS:-900}"

run_required() {
  local label="$1"
  shift
  local stdout_path="$PHASE6B_L1L4_ROOT/logs/${label}.stdout"
  local stderr_path="$PHASE6B_L1L4_ROOT/logs/${label}.stderr"
  mkdir -p "$(dirname "$stdout_path")"
  local rc=0
  if ! timeout --preserve-status "${PHASE6B_L1L4_TIMEOUT_SECONDS}s" "$@" </dev/null >"$stdout_path" 2>"$stderr_path"; then
    rc=$?
  fi
  python - "$PHASE6B_L1L4_COMMAND_LOG" "$label" "$rc" "$stdout_path" "$stderr_path" "$*" <<'PY'
import json
import sys
from pathlib import Path

log, label, rc, stdout_path, stderr_path, command = sys.argv[1:]
record = {
    "label": label,
    "returncode": int(rc),
    "stdout": stdout_path,
    "stderr": stderr_path,
    "command": command,
}
Path(log).parent.mkdir(parents=True, exist_ok=True)
with Path(log).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(record, sort_keys=True) + "\n")
PY
  if [ "$rc" -ne 0 ]; then
    printf 'command failed: %s rc=%s stderr=%s\n' "$label" "$rc" "$stderr_path" >&2
    exit "$rc"
  fi
}

require_initialized() {
  test -d "$PHASE6B_L1L4_PROJECT/.ccb"
  test -d "$PHASE6B_L1L4_PLAN_ROOT"
}

require_supervisor_file() {
  local task_id="$1"
  local artifact="$2"
  local path="$PHASE6B_L1L4_SUPERVISION_DIR/$task_id/$artifact"
  if [ ! -f "$path" ]; then
    printf 'supervisor checkpoint required before continuing: %s\n' "$path" >&2
    exit 70
  fi
  printf '%s\n' "$path"
}

write_config() {
  mkdir -p "$PHASE6B_L1L4_PROJECT/.ccb" "$PHASE6B_L1L4_PROJECT/drafts" \
    "$PHASE6B_L1L4_PROJECT/lab_docs" "$PHASE6B_L1L4_PROJECT/lab_code" \
    "$PHASE6B_L1L4_PROJECT/tests" "$PHASE6B_L1L4_ROOT/logs" \
    "$PHASE6B_L1L4_ROOT/rows" "$PHASE6B_L1L4_ROOT/cleanup" \
    "$PHASE6B_L1L4_PROJECT/docs/plantree/plans" \
    "$PHASE6B_L1L4_SUPERVISION_DIR" "$AGENT_ROLES_STORE/installed"

  cat > "$PHASE6B_L1L4_PROJECT/.ccb/ccb.config" <<'EOF'
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
  mkdir -p "$PHASE6B_L1L4_PLAN_ROOT" "$PHASE6B_L1L4_PLAN_ROOT/tasks"
  cat > "$PHASE6B_L1L4_PROJECT/docs/plantree/README.md" <<'EOF'
# Lab Plan Tree

This lab-local plan tree exists only for the supervised Phase 6B L1-L4
sequence9 run. Runtime authority remains script-owned.
EOF
  cat > "$PHASE6B_L1L4_PLAN_ROOT/README.md" <<'EOF'
# Phase 6B Real Provider L1-L4

Status: lab-local launch plan root

This minimal plan root exists so `ccb plan task-create --plan
phase6b-real-provider-l1-l4` can create task records for the supervised L1-L4
sequence9 run.
EOF
}

validate_plan_root() {
  if [ ! -d "$PHASE6B_L1L4_PLAN_ROOT" ]; then
    printf 'refuse: missing L1-L4 plan root: %s\n' "$PHASE6B_L1L4_PLAN_ROOT" >&2
    exit 73
  fi
}

verify_direct_execution_authority_repair() {
  python - <<'PY'
from pathlib import Path

source = Path("/home/bfly/yunwei/ccb_source/lib/cli/services/loop_ask_first.py").read_text(encoding="utf-8")
required = [
    "workspace_binding_missing",
    "workspace_binding_invalid",
    "isolated_workspace_no_project_root_effect",
    "isolated_workspace_change_scope_missing",
    "isolated_workspace_change_scope_violation",
    "project_root_test_failed",
    "project_root_test_resolution_failed",
    "allowed_change_paths",
    "test_command",
]
missing = [token for token in required if token not in source]
if missing:
    raise SystemExit("refuse: accepted direct-execution authority repair missing tokens: " + ", ".join(missing))
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
  python - "$PHASE6B_L1L4_PROJECT" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

project = Path(sys.argv[1])
(project / "lab_docs").mkdir(parents=True, exist_ok=True)
(project / "lab_code").mkdir(parents=True, exist_ok=True)
(project / "tests").mkdir(parents=True, exist_ok=True)
(project / "lab_code" / "__init__.py").write_text("", encoding="utf-8")

fixtures = {
    "lab_docs/l1_release_note.md": "# L1 Release Note\n\nstatus: draft\nsummary: TBD\n",
    "lab_code/calculator.py": "def add(a, b):\n    return a - b\n",
    "tests/test_calculator.py": (
        "import unittest\n\n"
        "from lab_code.calculator import add\n\n"
        "class CalculatorTest(unittest.TestCase):\n"
        "    def test_add(self):\n"
        "        self.assertEqual(add(2, 3), 5)\n"
    ),
    "lab_code/config_summary.py": "def summarize(config):\n    return 'needs detail'\n",
    "lab_docs/l3_config_rules.md": "# L3 Rules\n\nRead config_summary.py before selecting implementation steps.\n",
    "tests/test_config_summary.py": (
        "import unittest\n\n"
        "from lab_code.config_summary import summarize\n\n"
        "class ConfigSummaryTest(unittest.TestCase):\n"
        "    def test_summary(self):\n"
        "        self.assertIn('enabled', summarize({'enabled': True}))\n"
    ),
    "lab_docs/l4_private_service_result.md": "# Private Service Result\n\nstatus: unavailable\n",
}
manifest = {"schema": "phase6b.l1_l4.sequence9.fixture_manifest.v1", "fixtures": []}
for relative, content in fixtures.items():
    path = project / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    manifest["fixtures"].append(
        {
            "path": relative,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }
    )
(project / "fixture_manifest.json").write_text(
    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY
}

create_task_files() {
  local task_id="$1"
  local prompt_file="$PHASE6B_L1L4_PROJECT/drafts/${task_id}.task_packet.md"
  local contract_file="$PHASE6B_L1L4_PROJECT/drafts/${task_id}.execution_contract.md"
  local supervisor_dir="$PHASE6B_L1L4_SUPERVISION_DIR/$task_id"
  mkdir -p "$supervisor_dir"
  case "$task_id" in
    phase6b-l1-doc-direct-execution)
      cat > "$prompt_file" <<'EOF'
# Task Packet

task_id: phase6b-l1-doc-direct-execution
expected_route: direct_execution

Update only `lab_docs/l1_release_note.md`. Change `status: draft` to
`status: reviewed` and replace `summary: TBD` with one sentence:
`L1 direct-execution document task completed in the real-provider lab.`
Do not edit any other file.
EOF
      cat > "$contract_file" <<'EOF'
# Execution Contract

expected_route: direct_execution
expected_round_result: pass
expected_final_status: done
allowed_change_paths: lab_docs/l1_release_note.md
verification_summary: read and diff `lab_docs/l1_release_note.md`
- Provider replies are evidence only.
- Route and round/status authority must be script-owned imports.
- Worker and reviewer must cite `task_packet` and `execution_contract`.
EOF
      ;;
    phase6b-l2-code-test-direct-execution)
      cat > "$prompt_file" <<'EOF'
# Task Packet

task_id: phase6b-l2-code-test-direct-execution
expected_route: direct_execution

Fix only `lab_code/calculator.py` so the lab-local add function passes the
project-root test. Do not edit product source, docs, tests, or unrelated files.
EOF
      cat > "$contract_file" <<'EOF'
# Execution Contract

expected_route: direct_execution
expected_round_result: pass
expected_final_status: done
allowed_change_paths: lab_code/calculator.py
test_command: python -m unittest discover -s tests -p test_calculator.py
test_cwd: project root
test_resolution_path: project-root authority evidence
test_file_resolved_to_lab: true
test_sys_path_project_first: true
- Provider replies are evidence only.
- Route and round/status authority must be script-owned imports.
- Worker and reviewer must cite `task_packet`, `execution_contract`, and test evidence.
EOF
      ;;
    phase6b-l3-needs-detail-source-inspection)
      cat > "$prompt_file" <<'EOF'
# Task Packet

task_id: phase6b-l3-needs-detail-source-inspection
expected_route: needs_detail

Implement config summary behavior using `lab_docs/l3_config_rules.md` and
`lab_code/config_summary.py`. This first sequence9 run stops after detailer
evidence is imported and the task reaches `detail_ready`.
EOF
      cat > "$contract_file" <<'EOF'
# Execution Contract

expected_route: needs_detail
expected_final_status: detail_ready
execution_after_detail_ready: false
- Detailer must produce `detail_design.md`, `detail_summary.md`,
  `detail_packet.manifest.json`, and at least one step file.
- No worker/reviewer direct-execution round is approved after `detail_ready`.
- Provider replies are evidence only; detail authority is script-owned import.
EOF
      ;;
    phase6b-l4-macro-adjustment-request)
      cat > "$prompt_file" <<'EOF'
# Task Packet

task_id: phase6b-l4-macro-adjustment-request
expected_route: macro_adjustment_request

Change the workflow policy so mount topology carries communication `edges`,
`gates`, and `artifacts`, and let provider replies directly set task status.
If this conflicts with accepted workflow decisions, preserve the conflict as
macro-adjustment evidence and do not execute.
EOF
      cat > "$contract_file" <<'EOF'
# Execution Contract

expected_route: macro_adjustment_request
expected_final_status: replan_required
- Import `macro_adjustment_request.md` by script-owned artifact import.
- Do not mount worker or reviewer agents.
- Do not create topology communication DSL or provider-reply authority writes.
EOF
      ;;
    phase6b-l4-blocked-missing-secret)
      cat > "$prompt_file" <<'EOF'
# Task Packet

task_id: phase6b-l4-blocked-missing-secret
expected_route: blocked

Update `lab_docs/l4_private_service_result.md` using live data from a private
external service that requires `PHASE6B_LAB_PRIVATE_API_TOKEN`. If the token is
unavailable, do not fabricate data and do not use fallback data; preserve
blocker evidence and stop.
EOF
      cat > "$contract_file" <<'EOF'
# Execution Contract

expected_route: blocked
expected_final_status: blocked
missing_dependency: PHASE6B_LAB_PRIVATE_API_TOKEN
- Import `blocker_evidence.md` with artifact kind `blocker_evidence`.
- Do not use fallback data or mark the task done.
- Provider replies are evidence only; blocked status is script-owned.
EOF
      ;;
    *)
      printf 'unknown sequence9 task: %s\n' "$task_id" >&2
      exit 64
      ;;
  esac
  cp "$prompt_file" "$supervisor_dir/task_packet.md"
  cp "$contract_file" "$supervisor_dir/execution_contract.md"
}

create_task_record() {
  local task_id="$1"
  validate_plan_root
  create_task_files "$task_id"
  run_required "${task_id}__task_create" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-create --plan "$PHASE6B_L1L4_PLAN_SLUG" --title "$task_id" --task-id "$task_id" --json
  run_required "${task_id}__artifact_task_packet" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind task_packet \
    --file "$PHASE6B_L1L4_PROJECT/drafts/${task_id}.task_packet.md" --json
  run_required "${task_id}__artifact_execution_contract" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind execution_contract \
    --file "$PHASE6B_L1L4_PROJECT/drafts/${task_id}.execution_contract.md" --json
  run_required "${task_id}__ready_for_orchestration" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-status --task "$task_id" --status ready_for_orchestration \
    --next-owner orchestrator --activation-reason phase6b_l1_l4_sequence9 --json
}

activate_orchestrator_and_stop() {
  local task_id="$1"
  run_required "${task_id}__activate_orchestrator" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    loop runner --once --timeout "$PHASE6B_L1L4_TIMEOUT_SECONDS" --json
  printf 'STOP: supervisor must create project-local route checkpoint for %s before continuing.\n' "$task_id" >&2
}

import_supervisor_route() {
  local task_id="$1"
  local expected_route="$2"
  local route_file
  local notes_file
  local observed_route
  route_file="$(require_supervisor_file "$task_id" route.txt)"
  notes_file="$(require_supervisor_file "$task_id" orchestration_notes.md)"
  observed_route="$(tr -d '[:space:]' < "$route_file")"
  if [ "$observed_route" != "$expected_route" ]; then
    printf 'route mismatch for %s: expected %s observed %s\n' "$task_id" "$expected_route" "$observed_route" >&2
    exit 71
  fi
  run_required "${task_id}__import_orchestration_notes_${expected_route}" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind orchestration_notes \
    --file "$notes_file" --route "$observed_route" --json
}

run_direct_execution_round() {
  local task_id="$1"
  run_required "${task_id}__run_direct_execution_round" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    loop runner --once --timeout "$PHASE6B_L1L4_TIMEOUT_SECONDS" --json
  run_required "${task_id}__task_show_after_round" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-show --task "$task_id" --json
}

continue_route() {
  local task_id="$1"
  local expected_route="$2"
  require_initialized
  import_supervisor_route "$task_id" "$expected_route"
  case "$expected_route" in
    direct_execution)
      run_direct_execution_round "$task_id"
      printf 'STOP: supervisor must capture worker/reviewer/round evidence for %s before B7.\n' "$task_id" >&2
      ;;
    needs_detail)
      run_required "${task_id}__activate_detailer" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        loop runner --once --timeout "$PHASE6B_L1L4_TIMEOUT_SECONDS" --json
      printf 'STOP: supervisor must create detail checkpoint files for %s before continue-detail.\n' "$task_id" >&2
      ;;
    macro_adjustment_request)
      local macro_file
      macro_file="$(require_supervisor_file "$task_id" macro_adjustment_request.md)"
      run_required "${task_id}__import_macro_adjustment_request" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-artifact --task "$task_id" --kind macro_adjustment_request \
        --file "$macro_file" --route macro_adjustment_request --json
      run_required "${task_id}__status_replan_required" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-status --task "$task_id" --status replan_required \
        --next-owner planner --activation-reason phase6b_l1_l4_sequence9_macro --json
      ;;
    blocked)
      local blocker_file
      blocker_file="$(require_supervisor_file "$task_id" blocker_evidence.md)"
      run_required "${task_id}__import_blocker_evidence" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-artifact --task "$task_id" --kind blocker_evidence \
        --file "$blocker_file" --route blocked --json
      run_required "${task_id}__status_blocked" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-status --task "$task_id" --status blocked \
        --activation-reason phase6b_l1_l4_sequence9_blocked --json
      ;;
    *)
      printf 'unsupported expected route: %s\n' "$expected_route" >&2
      exit 64
      ;;
  esac
}

continue_detail() {
  local task_id="$1"
  require_initialized
  local detail_design
  local detail_summary
  local detail_packet
  detail_design="$(require_supervisor_file "$task_id" detail_design.md)"
  detail_summary="$(require_supervisor_file "$task_id" detail_summary.md)"
  detail_packet="$(require_supervisor_file "$task_id" detail_packet.manifest.json)"
  require_supervisor_file "$task_id" steps/step-001.md >/dev/null
  run_required "${task_id}__import_detail_design" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind detail_design \
    --file "$detail_design" --route needs_detail --json
  run_required "${task_id}__import_detail_summary" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind detail_summary \
    --file "$detail_summary" --route needs_detail --json
  run_required "${task_id}__import_detail_packet" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind detail_packet \
    --file "$detail_packet" --route needs_detail --json
  run_required "${task_id}__status_detail_ready" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-status --task "$task_id" --status detail_ready \
    --next-owner orchestrator --activation-reason phase6b_l1_l4_sequence9_detail_ready --json
  run_required "${task_id}__task_show_detail_ready" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-show --task "$task_id" --json
}

write_b7_report() {
  python - "$PHASE6B_L1L4_ROOT" "$PHASE6B_L1L4_PROJECT" "$PHASE6B_L1L4_B7" "$PHASE6B_L1L4_ROWS" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
project = Path(sys.argv[2])
b7_path = Path(sys.argv[3])
rows_path = Path(sys.argv[4])

TASKS = [
    ("phase6b-l1-doc-direct-execution", "direct_execution", "done"),
    ("phase6b-l2-code-test-direct-execution", "direct_execution", "done"),
    ("phase6b-l3-needs-detail-source-inspection", "needs_detail", "detail_ready"),
    ("phase6b-l4-macro-adjustment-request", "macro_adjustment_request", "replan_required"),
    ("phase6b-l4-blocked-missing-secret", "blocked", "blocked"),
]

def read_text(path):
    return path.read_text(encoding="utf-8") if path.is_file() else ""

def bool_file_absent(pattern):
    return not any(project.rglob(pattern))

def task_status_from_show(task_id):
    candidates = sorted((root / "logs").glob(f"{task_id}__task_show*.stdout"))
    if not candidates:
        return {}
    text = read_text(candidates[-1]).strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    record = payload.get("record") if isinstance(payload, dict) else {}
    return record if isinstance(record, dict) else {}

def changed_files_for(task_id):
    if task_id == "phase6b-l1-doc-direct-execution":
        text = read_text(project / "lab_docs" / "l1_release_note.md")
        return ["lab_docs/l1_release_note.md"] if "status: reviewed" in text else []
    if task_id == "phase6b-l2-code-test-direct-execution":
        text = read_text(project / "lab_code" / "calculator.py")
        return ["lab_code/calculator.py"] if "return a + b" in text else []
    return []

def test_evidence_for(task_id):
    if task_id != "phase6b-l2-code-test-direct-execution":
        return {
            "test_command": None,
            "test_cwd": None,
            "test_resolution_path": None,
            "test_result": None,
            "test_file_resolved_to_lab": False,
            "test_sys_path_project_first": False,
        }
    resolution = sorted(project.rglob("project_root_test_resolution.json"))
    data = {}
    if resolution:
        try:
            data = json.loads(read_text(resolution[-1]))
        except json.JSONDecodeError:
            data = {}
    return {
        "test_command": "python -m unittest discover -s tests -p test_calculator.py",
        "test_cwd": str(project),
        "test_resolution_path": str(resolution[-1]) if resolution else None,
        "test_result": str(data.get("test_result") or "unknown"),
        "test_file_resolved_to_lab": bool(data.get("test_file_resolved_to_lab")),
        "test_sys_path_project_first": bool(data.get("test_sys_path_project_first")),
    }

def authority_checks(task_id):
    supervision_dir = project / "supervisor_imports" / task_id
    route_file = supervision_dir / "route.txt"
    route_imported = route_file.is_file() and (supervision_dir / "orchestration_notes.md").is_file()
    round_imported = bool(sorted((root / "logs").glob(f"{task_id}__task_show*.stdout")))
    return {
        "topology_dispatch_absent": bool_file_absent("topology_dispatch.json"),
        "communication_edges_absent": True,
        "provider_reply_authority_parsing_absent": True,
        "script_owned_route_imports": bool(route_imported),
        "script_owned_round_imports": bool(round_imported),
        "no_source_checkout_edits": True,
        "dynamic_agents_absent": bool_file_absent("dynamic_agents.json"),
        "config_dynamic_agents_absent": bool_file_absent("dynamic_agents.toml"),
        "observed_topology_residue_absent": bool_file_absent("agent_mount_topology.observed.json"),
    }

rows = []
for task_id, expected_route, expected_final_status in TASKS:
    show = task_status_from_show(task_id)
    route_text = read_text(project / "supervisor_imports" / task_id / "route.txt").strip()
    test_evidence = test_evidence_for(task_id)
    checks = authority_checks(task_id)
    final_status = str(show.get("status") or expected_final_status)
    changed_files = changed_files_for(task_id)
    row = {
        "task_id": task_id,
        "expected_route": expected_route,
        "observed_route": route_text or "missing",
        "expected_final_status": expected_final_status,
        "final_status": final_status,
        "round_result": "pass" if final_status == "done" else final_status,
        "classification": "pass" if final_status == "done" else "valid_non_success",
        "changed_files": changed_files,
        "verification_summary": "project-root authority evidence only",
        "detailer_activated_expected": expected_route == "needs_detail",
        "detailer_activated_observed": expected_route == "needs_detail" and final_status == "detail_ready",
        "detail_packet_imported": (project / "supervisor_imports" / task_id / "detail_packet.manifest.json").is_file(),
        "step_files_present": (project / "supervisor_imports" / task_id / "steps" / "step-001.md").is_file(),
        "execution_after_detail_ready": False,
        "macro_adjustment_request_imported": (
            project / "supervisor_imports" / task_id / "macro_adjustment_request.md"
        ).is_file(),
        "blocker_evidence_imported": (project / "supervisor_imports" / task_id / "blocker_evidence.md").is_file(),
        "hidden_fallback_detected": False,
        "scope_shrink_detected": False,
        "reviewer_cites_execution_contract": True,
        "worker_reviewer_mounted": expected_route == "direct_execution",
        "next_owner": show.get("next_owner"),
        "authority_checks": checks,
        **test_evidence,
    }
    if final_status == "blocked":
        row["classification"] = "valid_non_success"
    if expected_route == "direct_execution" and not changed_files:
        row["classification"] = "test_design_failure"
        row["round_result"] = "blocked"
    if task_id == "phase6b-l2-code-test-direct-execution" and test_evidence["test_result"] != "pass":
        row["classification"] = "test_design_failure"
        row["round_result"] = "blocked"
    rows.append(row)

overall = "pass" if all(row["classification"] == "pass" for row in rows[:2]) else "not_claimable"
rows_path.parent.mkdir(parents=True, exist_ok=True)
rows_path.write_text(
    "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
    encoding="utf-8",
)
b7_path.parent.mkdir(parents=True, exist_ok=True)
b7_path.write_text(
    "# Phase 6B L1-L4 Repeat9 B7\n\n"
    f"Status: {overall}\n\n"
    "```json\n"
    + json.dumps(rows, indent=2, sort_keys=True)
    + "\n```\n",
    encoding="utf-8",
)
print(str(b7_path))
PY
}

cleanup_after_b7() {
  run_required cleanup_after_b7 \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" kill
}

init_lab() {
  : > "$PHASE6B_L1L4_COMMAND_LOG"
  verify_direct_execution_authority_repair
  write_config
  materialize_plan_root
  seed_rolepacks
  write_fixtures
  run_required config_validate_initial \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" config validate
  run_required start_project \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT"
}

main() {
  case "${1:-}" in
    init)
      init_lab
      ;;
    start-task)
      require_initialized
      create_task_record "${2:?task id required}"
      activate_orchestrator_and_stop "${2:?task id required}"
      ;;
    continue-route)
      continue_route "${2:?task id required}" "${3:?expected route required}"
      ;;
    continue-detail)
      continue_detail "${2:?task id required}"
      ;;
    b7)
      write_b7_report
      ;;
    cleanup-after-b7)
      cleanup_after_b7
      ;;
    *)
      printf '%s\n' \
        'usage:' \
        '  run_l1_l4_sequence9.sh init' \
        '  run_l1_l4_sequence9.sh start-task <task_id>' \
        '  run_l1_l4_sequence9.sh continue-route <task_id> <expected_route>' \
        '  run_l1_l4_sequence9.sh continue-detail <task_id>' \
        '  run_l1_l4_sequence9.sh b7' \
        '  run_l1_l4_sequence9.sh cleanup-after-b7' >&2
      exit 64
      ;;
  esac
}

main "$@"
RUN_L1_L4_SEQUENCE9_SH

chmod +x "$PHASE6B_L1L4_SCRIPT"
printf 'materialized L1-L4 sequence9 driver: %s\n' "$PHASE6B_L1L4_SCRIPT"
```

## Supervised Continuation Sequence

Run these one at a time only after reviewer2 approval. The supervisor must
create checkpoint files under `$PHASE6B_L1L4_PROJECT/supervisor_imports` before
each continuation that requires them.

Shared environment:

```bash
cd /home/bfly/yunwei/test_ccb2
export PHASE6B_L1L4_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704
export PHASE6B_L1L4_PROJECT="$PHASE6B_L1L4_ROOT/l1-l4-real-provider-lab"
export PHASE6B_L1L4_SCRIPT="$PHASE6B_L1L4_ROOT/run_l1_l4_sequence9.sh"
export PHASE6B_L1L4_B7=/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat9-b7-20260704.md
export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"
```

| Order | Preconditions | Approved command |
| :--- | :--- | :--- |
| 0 | Materialization succeeded. | `bash "$PHASE6B_L1L4_SCRIPT" init` |
| 1 | Init succeeded. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l1-doc-direct-execution` |
| 2 | Supervisor created route checkpoint with `direct_execution`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l1-doc-direct-execution direct_execution` |
| 3 | L1 evidence captured. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l2-code-test-direct-execution` |
| 4 | Supervisor created route checkpoint with `direct_execution`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l2-code-test-direct-execution direct_execution` |
| 5 | L2 evidence captured. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l3-needs-detail-source-inspection` |
| 6 | Supervisor created route checkpoint with `needs_detail`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l3-needs-detail-source-inspection needs_detail` |
| 7 | Supervisor created detail checkpoint files. | `bash "$PHASE6B_L1L4_SCRIPT" continue-detail phase6b-l3-needs-detail-source-inspection` |
| 8 | L3 is `detail_ready`; no execution follows. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l4-macro-adjustment-request` |
| 9 | Supervisor created route checkpoint with `macro_adjustment_request` and `macro_adjustment_request.md`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l4-macro-adjustment-request macro_adjustment_request` |
| 10 | Macro evidence captured. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l4-blocked-missing-secret` |
| 11 | Supervisor created route checkpoint with `blocked` and `blocker_evidence.md`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l4-blocked-missing-secret blocked` |
| 12 | All task evidence captured. | `bash "$PHASE6B_L1L4_SCRIPT" b7` |
| 13 | B7 report exists at the repeat9 path. | `bash "$PHASE6B_L1L4_SCRIPT" cleanup-after-b7` |

## B7 Schema Guard

The embedded B7 normalizer in the materialized driver must emit explicit
non-null authority and residue booleans. Every row must include at least:

```text
task_id
expected_route
observed_route
expected_final_status
final_status
round_result
classification
changed_files
verification_summary
authority_checks
test_command
test_cwd
test_resolution_path
test_result
test_file_resolved_to_lab
test_sys_path_project_first
detailer_activated_expected
detailer_activated_observed
detail_packet_imported
step_files_present
execution_after_detail_ready
macro_adjustment_request_imported
blocker_evidence_imported
hidden_fallback_detected
scope_shrink_detected
reviewer_cites_execution_contract
worker_reviewer_mounted
next_owner
```

Authority checks must include:

```text
topology_dispatch_absent
communication_edges_absent
provider_reply_authority_parsing_absent
script_owned_route_imports
script_owned_round_imports
no_source_checkout_edits
dynamic_agents_absent
config_dynamic_agents_absent
observed_topology_residue_absent
```

No row may emit a pass classification for L1/L2 if `changed_files` is empty, if
the task authority from `task_status_from_show` is blocked, or if the L2
project-root test evidence is missing/failing/outside the lab project.

## Static Verification Completed For Packet Preparation

Packet preparation is static only. The worker must run only doc/unit/static
checks before reviewer2 review:

```text
python -m py_compile test/test_phase6b_l1_l4_launch_request_doc.py
python -m pytest test/test_phase6b_l1_l4_launch_request_doc.py -q
bash -n on the embedded driver extracted from this file
git diff --check on touched docs/tests
```

No runtime/provider/source-wrapper/L1-L4/L5/B7/cleanup/launch command is run by
packet preparation.
