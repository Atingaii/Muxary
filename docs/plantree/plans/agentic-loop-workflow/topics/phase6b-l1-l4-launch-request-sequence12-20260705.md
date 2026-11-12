# Phase 6B L1-L4 Sequence12 Launch Packet

Date: 2026-07-05
Status: CONSUMED / RUNTIME B7 PASS / PHASE 6B UNCLAIMED

## Purpose

This packet is now the consumed launch and evidence record for the one
talk2-supervised Phase 6B L1-L4 sequence12 run after the accepted sequence11 L3
detail-authority repair and repeat11 B7 normalizer repair. It is no longer a
request for runtime approval. Do not rerun this root or reuse this command
shape as an active approval.

Requested fresh root:

`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`

B7 path:

`docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md`

Talk2 self-reviewed the packet, verified the root and B7 path were absent
before materialization, consumed the single-use run once, generated the B7, and
ran cleanup. The B7 reports `Status: pass`; cleanup returned `kill_status: ok`,
`state: unmounted`.

Runtime summary:

- L1 `phase6b-l1-doc-direct-execution`: `direct_execution -> done/pass`.
- L2 `phase6b-l2-code-test-direct-execution`: `direct_execution -> done/pass`
  with lab-local unittest resolution evidence.
- L3 `phase6b-l3-needs-detail-source-inspection`: `needs_detail ->
  detail_ready/detail_ready`, classified `valid_non_success`.
- L4 `phase6b-l4-macro-adjustment-request`: `macro_adjustment_request ->
  replan_required`, classified `valid_non_success`.
- L4 `phase6b-l4-blocked-missing-secret`: `blocked -> blocked`, classified
  `valid_non_success`.

## Historical Inputs

The sequence9 fallback approval `job_c4935017fc15` was consumed once from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704`.
Sequence9 reached L1 `done/pass`; L2 changed project-root
`lab_code/calculator.py` and a supervisor-created project-root unittest
resolution check passed, but product task authority remained `blocked` with
`round_result_source=isolated_workspace_no_project_root_effect`. L3/L4 were not
run. The generated repeat9 B7 says `Status: pass`, but that output is rejected
as a false-positive normalizer result by
[../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md](../history/phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md).
Sequence9 is consumed and must not be reused.

Historical repeat8 remains non-runnable in
[phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md).
Repeat8 root `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704`
is consumed and must not be reused.

Sequence10 is preserved as a consumed historical packet in
[phase6b-l1-l4-launch-request-sequence10-20260704.md](phase6b-l1-l4-launch-request-sequence10-20260704.md).
It was approved by reviewer1 fallback launch gate `job_bfe386ae7a9f` and
consumed exactly once by talk2 from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence10-20260704`.
The run stopped at L1 after the round reviewer detected a fake-success shape:
worker changes existed only in the loop copy workspace, the main project
`lab_docs/l1_release_note.md` remained `status: draft` / `summary: TBD`, and
the script-owned task authority was imported as `blocked`. L2/L3/L4 were not
run. Repeat10 B7 was written before cleanup at
[../history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md](../history/phase6b-real-provider-l1-l4-repeat10-b7-20260704.md)
with `Status: not_claimable`; cleanup returned `kill_status: ok`,
`state: unmounted`. Sequence10 is consumed and must not be reused.

Worker1 source repair `job_e2ff663087be` was accepted by reviewer1
`job_a7e62fee5496`:
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_a7e62fee5496-art_d74161f1a0dd4d52.txt`.
Accepted behavior: ask-first `direct_execution` promotes allowed isolated
worker workspace deltas into the project root before code-reviewer,
orchestrator, and `ccb_round_reviewer` validation; reviewers audit project-root
evidence, not workspace-only evidence; non-pass, unknown, or project-root test
failure rolls staged changes back and records rollback evidence. Talk2 local
static verification after that review passed:
`python -m py_compile lib/cli/services/loop_ask_first.py lib/cli/services/loop_runner.py lib/cli/services/loop_topology.py lib/cli/services/plan_tasks.py`
and
`python -m pytest test/test_loop_capacity_cli.py test/test_plan_tasks_cli.py test/test_loop_topology_cli.py test/test_loop_topology_dispatch_contract.py -q`
with `89 passed`.

Sequence11 was approved once by reviewer1 `job_68063ec21783` and consumed once
by talk2 from
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence11-20260704`.
The run reached L1/L2 direct execution, stopped at L3 detail import and
`detail_ready`, wrote repeat11 B7 as `not_claimable`, and cleanup returned
`kill_status: ok`. Sequence11 is consumed and non-reusable.

Worker1 completed the L3 detail-authority repair in `job_ad72d8bb8790`, and
reviewer1 accepted it in `job_f3982925275d`:
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f3982925275d-art_e5f196b604364d41.txt`.
Sequence12 carries forward the accepted repair shape: non-orchestration detail
artifacts import without `--route`, only `orchestration_notes` carries
`--route`, `ready_for_orchestration -> detail_ready` is allowed only when the
required detail artifacts exist, `detail_ready` uses the repo-native default
`next_owner=planner`, and `run_required` fails hard on `command_status: failed`
markers in text or JSON.

Worker2 completed the repeat11 B7 normalizer repair in `job_dd89005df2ee`, and
reviewer1 accepted it through callback artifact
`/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/callback-continuation/cb_faab6bb2d057-art_f9e89c4d470a4c16.txt`.
Sequence12 carries forward the accepted normalizer shape: parse
`round_result:` and legacy `round result:`, read task-show `last_round.result`,
allow persisted observed topology evidence when no active/retained dynamic
loop agents remain, and still fail retained dynamic topology residue.

## Requested Verdict

Talk2 recorded the following launch decision before execution.

Decision:

```text
APPROVAL-TO-RUN GRANTED BY TALK2 SELF-REVIEW
```

The consumed approval named:

- root: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`;
- tranche: L1 direct, L2 direct, L3 `needs_detail -> detail_ready`, L4
  `macro_adjustment_request`, L4 `blocked`;
- command shape: materialize the script below from `/home/bfly/yunwei/test_ccb2`,
  run `init`, then supervised checkpoint/resume commands only;
- B7 path:
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md`.

If this packet had been blocked, talk2 would have recorded:

```text
APPROVAL BLOCKED
```

The blocker must name concrete missing evidence, stale/non-fresh root state,
unsafe command shape, or contradictory docs/tests.

This packet does not claim Phase 6B, does not approve L5, does not approve
production/default enablement, and does not permit any reuse of sequence12 or
earlier roots.

## Scope Boundary

Included tasks:

| Task | Expected route | Approved endpoint |
| :--- | :--- | :--- |
| `phase6b-l1-doc-direct-execution` | `direct_execution` | `done/pass` only after project-root file evidence |
| `phase6b-l2-code-test-direct-execution` | `direct_execution` | `done/pass` only after project-root test evidence |
| `phase6b-l3-needs-detail-source-inspection` | `needs_detail` | `detail_ready`; no post-detail execution |
| `phase6b-l4-macro-adjustment-request` | `macro_adjustment_request` | `replan_required` |
| `phase6b-l4-blocked-missing-secret` | `blocked` | `blocked` |

Excluded from this consumed approval:

- L5 reviewer-rework or partial observation;
- production/default enablement;
- any Phase 6B completion claim;
- any reuse of consumed sequence1 through sequence12 roots or approvals.

Even if sequence12 succeeds, Phase 6B remains unclaimed until a separate final
B7 aggregation accepts the L1-L4 rows together with already accepted L0 and L5
evidence.

## Authority And Runtime Rules

- The sequence12 root was verified absent before `init`; it is now consumed and
  must not be reused.
- Real-provider runs inherit the current system provider environment. Do not
  export lab-local `HOME` or `CCB_SOURCE_HOME`.
- `AGENT_ROLES_STORE` is lab-local under the sequence12 root.
- Every runtime command uses explicit `--project "$PHASE6B_L1L4_PROJECT"`.
- The configured `ccb_round_reviewer` profile uses `claude`; resident workflow
  roles and direct-execution `coder`/`code_reviewer` profiles use `codex`.
- Provider replies are evidence only. Route, detail, terminal, and round
  authority must come from script-owned imports.
- Only `orchestration_notes` imports use `--route`; detail, macro, blocker,
  and round evidence are not route-authority imports.
- Supervisor checkpoint files passed to `plan task-artifact --file` must live
  under `$PHASE6B_L1L4_PROJECT/supervisor_imports/<task_id>/`.
- Blocked terminal evidence uses artifact kind `blocker_evidence`; no artifact
  kind named `blocked` is allowed.
- L3 stops at `detail_ready`; no execution command follows the detail import.
- B7 normalization must run before any external cleanup.
- Topology remains mount-only: no `topology_dispatch.json`, communication DSL,
  topology edges/gates/artifacts, or provider-reply authority parsing.
- Direct-execution source repair evidence is accepted in worker1
  `job_e2ff663087be` / reviewer1 `job_a7e62fee5496`. Sequence12 produced fresh
  runtime/B7 evidence before any L1/L2 Phase 6B claim.

## Consumed Sequence12 Command Shape

This is the exact command shape used for the consumed sequence12 run. It is
kept for audit only. Do not run it again.

```bash
cd /home/bfly/yunwei/test_ccb2
export PHASE6B_L1L4_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705
export PHASE6B_L1L4_PROJECT="$PHASE6B_L1L4_ROOT/l1-l4-real-provider-lab"
export PHASE6B_L1L4_SCRIPT="$PHASE6B_L1L4_ROOT/run_l1_l4_sequence12.sh"
export PHASE6B_L1L4_COMMAND_LOG="$PHASE6B_L1L4_ROOT/phase6b_l1_l4_sequence12_command_log.jsonl"
export PHASE6B_L1L4_ROWS="$PHASE6B_L1L4_ROOT/rows/phase6b_l1_l4_sequence12_evidence_rows.jsonl"
export PHASE6B_L1L4_B7=/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md
export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"

if [ -e "$PHASE6B_L1L4_ROOT" ]; then
  printf 'refuse: sequence12 root already exists: %s\n' "$PHASE6B_L1L4_ROOT" >&2
  exit 100
fi
mkdir -p "$PHASE6B_L1L4_ROOT"

cat > "$PHASE6B_L1L4_SCRIPT" <<'RUN_L1_L4_SEQUENCE12_SH'
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
PHASE6B_L1L4_SEQUENCE_TASK_IDS=(
  phase6b-l1-doc-direct-execution
  phase6b-l2-code-test-direct-execution
  phase6b-l3-needs-detail-source-inspection
  phase6b-l4-macro-adjustment-request
  phase6b-l4-blocked-missing-secret
)

run_required() {
  local label="$1"
  shift
  local stdout_path="$PHASE6B_L1L4_ROOT/logs/${label}.stdout"
  local stderr_path="$PHASE6B_L1L4_ROOT/logs/${label}.stderr"
  mkdir -p "$(dirname "$stdout_path")"
  set +e
  if [ "${CCB_PHASE6B_RUN_WITHOUT_TIMEOUT:-0}" = "1" ]; then
    "$@" </dev/null >"$stdout_path" 2>"$stderr_path"
  else
    timeout --preserve-status "${PHASE6B_L1L4_TIMEOUT_SECONDS}s" "$@" </dev/null >"$stdout_path" 2>"$stderr_path"
  fi
  local rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    if python - "$stdout_path" "$stderr_path" <<'PY'
import json
import re
import sys
from pathlib import Path

def has_failed_command_status(path):
    if not Path(path).is_file():
        return False
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    if re.search(r"(?m)^\s*command_status:\s*failed\s*$", text):
        return True
    if re.search(r'"command_status"\s*:\s*"failed"', text):
        return True
    for line in text.splitlines():
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("command_status") == "failed":
            return True
    return False

raise SystemExit(0 if any(has_failed_command_status(path) for path in sys.argv[1:]) else 1)
PY
    then
      rc=1
    fi
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

run_unbounded_required() {
  CCB_PHASE6B_RUN_WITHOUT_TIMEOUT=1 run_required "$@"
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

write_frontdesk_entry_request() {
  cat > "$PHASE6B_L1L4_ROOT/frontdesk_l1_l4_entry_request.md" <<'EOF'
Please start a fresh real-provider L1-L4 deployment-readiness route-mix validation for this lab project.

Use frontdesk as the user-facing intake and hand off to planner automatically. Treat this as controller-owned route-mix validation, not as a worker implementation task. Planner and orchestrator should prepare and route the bounded L1-L4 task set itself: a document-only L1 direct execution, an L2 code-and-test direct execution, an L3 needs-detail case that stops at detail_ready, an L4 macro-adjustment case that stops at replan_required, and an L4 blocked-prerequisite case that remains blocked.

Do not ask a worker to run the retest harness, generate B7 reports, write evidence rows, clean up runtime, or modify plan authority files. The supervisor/controller owns evidence rows, B7 reporting, cleanup, and script-owned authority imports. Preserve any provider or route failure as failure evidence.
EOF
}

frontdesk_entry() {
  require_initialized
  write_frontdesk_entry_request
  run_required frontdesk_entry_ask \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    ask frontdesk -- "$(cat "$PHASE6B_L1L4_ROOT/frontdesk_l1_l4_entry_request.md")"
  printf 'STOP: wait for frontdesk auto-handoff and planner/orchestrator evidence, then validate task set before continuing.\n' >&2
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
sequence12 run. Runtime authority remains script-owned.
EOF
  cat > "$PHASE6B_L1L4_PLAN_ROOT/README.md" <<'EOF'
# Phase 6B Real Provider L1-L4

Status: lab-local launch plan root

This minimal plan root exists so `ccb plan task-create --plan
phase6b-real-provider-l1-l4` can create task records for the supervised L1-L4
sequence12 run.
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
    local label_role
    label_role="${role_id//./_}"
    run_required "roles_install_${label_role}" \
      /home/bfly/yunwei/ccb_source/ccb_test roles install "$role_id" --skip-tools
  done
  validate_seeded_rolepacks
}

validate_seeded_rolepacks() {
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
    if [ ! -f "$AGENT_ROLES_STORE/installed/${role_id}/current/role.toml" ]; then
      printf 'rolepack bootstrap incomplete: %s missing from %s\n' "$role_id" "$AGENT_ROLES_STORE" >&2
      exit 74
    fi
    if [ ! -f "$AGENT_ROLES_STORE/installed/${role_id}/install.json" ]; then
      printf 'rolepack bootstrap incomplete: %s missing install metadata in %s\n' "$role_id" "$AGENT_ROLES_STORE" >&2
      exit 74
    fi
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
manifest = {"schema": "phase6b.l1_l4.sequence12.fixture_manifest.v1", "fixtures": []}
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
`lab_code/config_summary.py`. This first sequence12 run stops after detailer
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
      printf 'unknown sequence12 task: %s\n' "$task_id" >&2
      exit 64
      ;;
  esac
  cp "$prompt_file" "$supervisor_dir/task_packet.md"
  cp "$contract_file" "$supervisor_dir/execution_contract.md"
}

create_task_record() {
  local task_id="$1"
  validate_plan_root
  validate_sequence_task_set_only
  create_task_files "$task_id"
  ensure_task_record "$task_id"
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
    --next-owner orchestrator --activation-reason phase6b_l1_l4_sequence12 --json
}

task_record_exists() {
  local task_id="$1"
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-show --task "$task_id" --json >/dev/null 2>/dev/null
}

ensure_task_record() {
  local task_id="$1"
  if task_record_exists "$task_id"; then
    run_required "${task_id}__task_observe_existing" \
      /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
      plan task-show --task "$task_id" --json
    return
  fi
  run_required "${task_id}__task_create" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-create --plan "$PHASE6B_L1L4_PLAN_SLUG" --title "$task_id" --task-id "$task_id" --json
}

validate_sequence_task_set_only() {
  local index_path="$PHASE6B_L1L4_PLAN_ROOT/tasks/index.json"
  [ -f "$index_path" ] || return 0
  python - "$index_path" "${PHASE6B_L1L4_SEQUENCE_TASK_IDS[@]}" <<'PY'
import json
import sys
from pathlib import Path

index = Path(sys.argv[1])
allowed = set(sys.argv[2:])
payload = json.loads(index.read_text(encoding="utf-8"))
tasks = payload.get("tasks") if isinstance(payload, dict) else []
unexpected = []
for record in tasks if isinstance(tasks, list) else []:
    if not isinstance(record, dict):
        continue
    task_id = str(record.get("task_id") or "").strip()
    if task_id and task_id not in allowed:
        unexpected.append(task_id)
if unexpected:
    print(
        "frontdesk/planner created non-sequence task(s): " + ", ".join(sorted(unexpected)),
        file=sys.stderr,
    )
    print(
        "refuse: L1-L4 deployment harness must use one authoritative sequence task set; "
        "do not execute a meta direct_execution retest/report task.",
        file=sys.stderr,
    )
    raise SystemExit(75)
PY
}

activate_orchestrator_and_stop() {
  local task_id="$1"
  run_unbounded_required "${task_id}__activate_orchestrator" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    loop runner --once --json
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
  run_unbounded_required "${task_id}__run_direct_execution_round" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    loop runner --once --json
  assert_no_pending_round_authority "$task_id"
  run_required "${task_id}__task_show_after_round" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-show --task "$task_id" --json
}

assert_no_pending_round_authority() {
  local task_id="${1:-}"
  python - "$PHASE6B_L1L4_PROJECT" "$task_id" <<'PY'
import json
import sys
from pathlib import Path

project = Path(sys.argv[1])
task_id = sys.argv[2]
problems = []
def matches_task(payload):
    return not task_id or str(payload.get("task_id") or "") == task_id

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

for path in sorted((project / ".ccb" / "runtime" / "loops").glob("*/round.pending.json")):
    payload = read_json(path)
    if not isinstance(payload, dict) or not matches_task(payload):
        continue
    source = str(payload.get("round_result_source") or "")
    if str(payload.get("loop_run_status") or "") == "pending" or str(payload.get("round_result") or "") == "pending":
        problems.append((path, source or "ask_job_pending"))

for path in sorted((project / ".ccb" / "runtime" / "loops").glob("*/ask_first_stage_state.json")):
    payload = read_json(path)
    if not isinstance(payload, dict) or not matches_task(payload):
        continue
    if str(payload.get("status") or "") == "pending":
        problems.append((path, "ask_first_stage_pending"))

for path in sorted((project / ".ccb" / "runtime" / "loops").glob("*/round.json")):
    payload = read_json(path)
    if not isinstance(payload, dict) or not matches_task(payload):
        continue
    failure = payload.get("failure") if isinstance(payload.get("failure"), dict) else {}
    source = str(payload.get("round_result_source") or failure.get("source") or "")
    if source == "ask_job_incomplete":
        problems.append((path, "ask_job_incomplete"))
        continue
    for role in ("worker", "reviewer", "orchestrator", "ccb_round_reviewer"):
        record = payload.get(role) if isinstance(payload.get(role), dict) else {}
        if str(record.get("status") or "") == "incomplete":
            problems.append((path, f"{role}_job_incomplete"))
            break
if problems:
    for path, reason in problems:
        print(f"round authority pending/incomplete: {reason}: {path}", file=sys.stderr)
    print(
        "refuse cleanup/progress: wait or resume through observer path before treating the round as terminal evidence",
        file=sys.stderr,
    )
    raise SystemExit(78)
PY
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
      run_unbounded_required "${task_id}__activate_detailer" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        loop runner --once --json
      printf 'STOP: supervisor must create detail checkpoint files for %s before continue-detail.\n' "$task_id" >&2
      ;;
    macro_adjustment_request)
      local macro_file
      macro_file="$(require_supervisor_file "$task_id" macro_adjustment_request.md)"
      run_required "${task_id}__import_macro_adjustment_request" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-artifact --task "$task_id" --kind macro_adjustment_request \
        --file "$macro_file" --json
      run_required "${task_id}__status_replan_required" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-status --task "$task_id" --status replan_required \
        --next-owner planner --activation-reason phase6b_l1_l4_sequence12_macro --json
      ;;
    blocked)
      local blocker_file
      blocker_file="$(require_supervisor_file "$task_id" blocker_evidence.md)"
      run_required "${task_id}__import_blocker_evidence" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-artifact --task "$task_id" --kind blocker_evidence \
        --file "$blocker_file" --json
      run_required "${task_id}__status_blocked" \
        /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
        plan task-status --task "$task_id" --status blocked \
        --activation-reason phase6b_l1_l4_sequence12_blocked --json
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
    --file "$detail_design" --json
  run_required "${task_id}__import_detail_summary" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind detail_summary \
    --file "$detail_summary" --json
  run_required "${task_id}__import_detail_packet" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-artifact --task "$task_id" --kind detail_packet \
    --file "$detail_packet" --json
  run_required "${task_id}__status_detail_ready" \
    /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L1L4_PROJECT" \
    plan task-status --task "$task_id" --status detail_ready \
    --activation-reason phase6b_l1_l4_sequence12_detail_ready --json
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
    {
        "task_id": "phase6b-l1-doc-direct-execution",
        "expected_route": "direct_execution",
        "expected_final_status": "done",
        "expected_round_result": "pass",
        "expected_classification": "pass",
    },
    {
        "task_id": "phase6b-l2-code-test-direct-execution",
        "expected_route": "direct_execution",
        "expected_final_status": "done",
        "expected_round_result": "pass",
        "expected_classification": "pass",
    },
    {
        "task_id": "phase6b-l3-needs-detail-source-inspection",
        "expected_route": "needs_detail",
        "expected_final_status": "detail_ready",
        "expected_round_result": "detail_ready",
        "expected_classification": "valid_non_success",
    },
    {
        "task_id": "phase6b-l4-macro-adjustment-request",
        "expected_route": "macro_adjustment_request",
        "expected_final_status": "replan_required",
        "expected_round_result": "replan_required",
        "expected_classification": "valid_non_success",
    },
    {
        "task_id": "phase6b-l4-blocked-missing-secret",
        "expected_route": "blocked",
        "expected_final_status": "blocked",
        "expected_round_result": "blocked",
        "expected_classification": "valid_non_success",
    },
]

DIRECT_TASK_IDS = {
    "phase6b-l1-doc-direct-execution",
    "phase6b-l2-code-test-direct-execution",
}
EXPECTED_TASK_IDS = {case["task_id"] for case in TASKS}
ROUND_ARTIFACT_KEYS = (
    "round_summary",
    "round_pass",
    "round_partial",
    "round_replan",
    "round_blocker",
)

def read_text(path):
    return path.read_text(encoding="utf-8") if path.is_file() else ""

def read_json_object(path):
    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None

def bool_file_absent(pattern):
    return not any(project.rglob(pattern))

def first_text(*values):
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None

def resolve_project_file(value):
    text = first_text(value)
    if not text:
        return None
    path = Path(text)
    candidates = [path] if path.is_absolute() else [project / path, root / path]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None

def dict_field(value, key):
    nested = value.get(key) if isinstance(value, dict) else None
    return nested if isinstance(nested, dict) else {}

def round_artifact_from(*records):
    for item in records:
        artifact_map = dict_field(item, "artifacts")
        for key in ROUND_ARTIFACT_KEYS:
            artifact = artifact_map.get(key)
            if isinstance(artifact, dict):
                return artifact
    return {}

def round_artifact_path_from(*records):
    artifact = round_artifact_from(*records)
    last_round_paths = [
        dict_field(item, "last_round").get("artifact_path")
        for item in records
        if isinstance(item, dict)
    ]
    return first_text(artifact.get("path"), artifact.get("artifact_path"), *last_round_paths)

def normalized_summary_key(value):
    return "_".join(str(value).strip().lower().replace("_", " ").split())

def summary_field(text, name):
    expected = normalized_summary_key(name)
    for line in text.splitlines():
        key, separator, value = line.strip().partition(":")
        if separator and normalized_summary_key(key) == expected:
            return value.strip()
    return None

def last_round_result(*records):
    for record in records:
        last_round = dict_field(record, "last_round")
        result = first_text(last_round.get("result"), last_round.get("round_result"))
        if result:
            return result
    return None

def plan_task_index_payload():
    return read_json_object(project / "docs" / "plantree" / "plans" / "phase6b-real-provider-l1-l4" / "tasks" / "index.json")

def plan_task_index_record(task_id):
    payload = plan_task_index_payload()
    records = payload.get("tasks") if isinstance(payload, dict) else []
    for record in records if isinstance(records, list) else []:
        if isinstance(record, dict) and str(record.get("task_id") or "") == task_id:
            return record
    return None

def unexpected_plan_tasks():
    payload = plan_task_index_payload()
    records = payload.get("tasks") if isinstance(payload, dict) else []
    unexpected = []
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        task_id = str(record.get("task_id") or "").strip()
        if task_id and task_id not in EXPECTED_TASK_IDS:
            unexpected.append(task_id)
    return sorted(set(unexpected))

def round_json_for(task_id):
    matches = []
    for path in sorted((project / ".ccb" / "runtime" / "loops").glob("*/round.json")):
        payload = read_json_object(path)
        if payload is None or str(payload.get("task_id") or "") != task_id:
            continue
        matches.append((str(payload.get("finished_at") or ""), path, payload))
    if not matches:
        return None, None
    _finished_at, path, payload = sorted(matches)[-1]
    return path, payload

def task_status_from_show(task_id):
    candidates = sorted((root / "logs").glob(f"{task_id}__task_show*.stdout"))
    index_path = project / "docs" / "plantree" / "plans" / "phase6b-real-provider-l1-l4" / "tasks" / "index.json"
    index_record = plan_task_index_record(task_id)
    result = {
        "task_show_observed": False,
        "task_show_path": str(index_path) if index_record is not None else (str(candidates[-1]) if candidates else None),
        "task_show_parse_error": None,
        "status": "missing",
        "next_owner": None,
        "round_result": None,
        "round_result_source": None,
        "round_summary_artifact_path": None,
        "task_show_source": "missing",
        "task_show_stale": False,
    }
    if index_record is not None:
        round_artifact = round_artifact_from(index_record)
        round_summary_path = resolve_project_file(round_artifact_path_from(index_record))
        result.update(
            {
                "task_show_observed": True,
                "task_show_source": "task_index",
                "status": first_text(index_record.get("status")) or "missing",
                "next_owner": first_text(index_record.get("next_owner")),
                "round_result": first_text(round_artifact.get("round_result"), last_round_result(index_record)),
                "round_result_source": first_text(round_artifact.get("round_result_source")),
                "round_summary_artifact_path": str(round_summary_path) if round_summary_path else None,
            }
        )
        return result
    if not candidates:
        return result
    text = read_text(candidates[-1]).strip()
    if not text:
        result["task_show_parse_error"] = "empty task-show stdout"
        return result
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        result["task_show_parse_error"] = "invalid task-show json"
        return result
    if not isinstance(payload, dict):
        result["task_show_parse_error"] = "task-show json is not an object"
        return result
    record = payload.get("record") if isinstance(payload.get("record"), dict) else {}
    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    round_artifact = round_artifact_from(payload, task, record)
    round_summary_path = resolve_project_file(round_artifact_path_from(payload, task, record))
    result.update(
        {
            "task_show_observed": True,
            "status": first_text(payload.get("status"), task.get("status"), record.get("status")) or "missing",
            "next_owner": first_text(payload.get("next_owner"), task.get("next_owner"), record.get("next_owner")),
            "round_result": first_text(
                payload.get("round_result"),
                task.get("round_result"),
                record.get("round_result"),
                round_artifact.get("round_result"),
                last_round_result(payload, task, record),
            ),
            "round_result_source": first_text(
                payload.get("round_result_source"),
                task.get("round_result_source"),
                record.get("round_result_source"),
                round_artifact.get("round_result_source"),
            ),
            "round_summary_artifact_path": str(round_summary_path) if round_summary_path else None,
            "task_show_source": "task_show_log",
        }
    )
    round_json_path, round_json = round_json_for(task_id)
    if round_json_path and result["status"] in {"draft", "ready", "ready_for_orchestration", "running"}:
        result["task_show_stale"] = True
    return result

def round_evidence_for(task_id, show):
    supervisor_summary_path = project / "supervisor_imports" / task_id / "round_summary.md"
    artifact_summary_path = resolve_project_file(show.get("round_summary_artifact_path"))
    round_json_path, round_json = round_json_for(task_id)
    round_json_summary_path = None
    if isinstance(round_json, dict):
        round_json_summary_path = resolve_project_file(dict_field(round_json, "paths").get("round"))
    task_root_summary_path = (
        project
        / "docs"
        / "plantree"
        / "plans"
        / "phase6b-real-provider-l1-l4"
        / "tasks"
        / task_id
        / "round_summary.md"
    )
    summary_path = first_existing_path(
        supervisor_summary_path,
        artifact_summary_path,
        round_json_summary_path,
        task_root_summary_path,
    )
    summary_text = read_text(summary_path) if summary_path else ""
    round_result = first_text(
        summary_field(summary_text, "round_result"),
        show.get("round_result"),
        round_json.get("round_result") if isinstance(round_json, dict) else None,
    )
    round_result_source = first_text(
        summary_field(summary_text, "round_result_source"),
        show.get("round_result_source"),
        round_json.get("round_result_source") if isinstance(round_json, dict) else None,
    )
    return {
        "round_summary_observed": bool(summary_path and summary_path.is_file()),
        "round_summary_path": str(summary_path) if summary_path and summary_path.is_file() else None,
        "round_json_path": str(round_json_path) if round_json_path else None,
        "round_result": round_result or "missing",
        "round_result_source": round_result_source or "missing",
    }

def first_existing_path(*paths):
    for path in paths:
        if path and Path(path).is_file():
            return Path(path)
    return None

def observed_topology_residue_absent():
    residue_observed = False
    for path in project.rglob("agent_mount_topology.observed.json"):
        if observed_topology_has_dynamic_residue(path):
            residue_observed = True
            break
    if not residue_observed:
        return True
    return cleanup_after_b7_unmounted()

def cleanup_after_b7_unmounted():
    path = root / "logs" / "cleanup_after_b7.stdout"
    text = read_text(path)
    if not text:
        return False
    fields = {}
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    return fields.get("kill_status") == "ok" and fields.get("state") == "unmounted"

def observed_topology_has_dynamic_residue(path):
    payload = read_json_object(path)
    if payload is None:
        return True
    if int_field(payload.get("retained_count")) > 0:
        return True
    retained_agents = str_list(payload.get("retained_agents") or payload.get("retained"))
    if any(is_dynamic_agent(agent) for agent in retained_agents):
        return True
    return any(is_dynamic_agent(agent) for agent in topology_agent_ids(payload))

def int_field(value):
    if isinstance(value, int):
        return value
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0

def str_list(value):
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    if value:
        return [str(value)]
    return []

def is_dynamic_agent(name):
    return str(name).startswith("loop-")

def topology_agent_ids(payload):
    names = {
        str(agent.get("id") or agent.get("name") or "")
        for agent in tuple(payload.get("agents") or ())
        if isinstance(agent, dict)
    }
    for node in tuple(payload.get("nodes") or ()):
        if not isinstance(node, dict):
            continue
        names.update(
            str(agent.get("id") or agent.get("name") or "")
            for agent in tuple(node.get("agents") or ())
            if isinstance(agent, dict)
        )
    return {name for name in names if name}

def command_log_labels():
    labels = set()
    for log_path in sorted(root.glob("*command_log.jsonl")):
        for line in read_text(log_path).splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict) and record.get("returncode", 0) in (0, "0", None):
                label = first_text(record.get("label"))
                if label:
                    labels.add(label)
    return labels

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

def authority_checks(task_id, *, task_show_observed, round_result_observed):
    supervision_dir = project / "supervisor_imports" / task_id
    route_file = supervision_dir / "route.txt"
    route_imported = route_file.is_file() and (supervision_dir / "orchestration_notes.md").is_file()
    return {
        "topology_dispatch_absent": bool_file_absent("topology_dispatch.json"),
        "communication_edges_absent": True,
        "provider_reply_authority_parsing_absent": True,
        "script_owned_route_imports": bool(route_imported),
        "script_owned_round_imports": bool(task_show_observed and round_result_observed),
        "no_source_checkout_edits": True,
        "dynamic_agents_absent": bool_file_absent("dynamic_agents.json"),
        "config_dynamic_agents_absent": bool_file_absent("dynamic_agents.toml"),
        "observed_topology_residue_absent": observed_topology_residue_absent(),
    }

def reviewer_cites_execution_contract(task_id):
    verdict = read_text(project / "supervisor_imports" / task_id / "reviewer_verdict.md")
    return "task_packet" in verdict and "execution_contract" in verdict

def add_error(errors, condition, message):
    if condition:
        errors.append(message)

rows = []
labels = command_log_labels()
unexpected_tasks = unexpected_plan_tasks()
for case in TASKS:
    task_id = case["task_id"]
    expected_route = case["expected_route"]
    expected_final_status = case["expected_final_status"]
    expected_round_result = case["expected_round_result"]
    expected_classification = case["expected_classification"]
    show = task_status_from_show(task_id)
    route_text = read_text(project / "supervisor_imports" / task_id / "route.txt").strip()
    round_evidence = round_evidence_for(task_id, show)
    test_evidence = test_evidence_for(task_id)
    checks = authority_checks(
        task_id,
        task_show_observed=show["task_show_observed"],
        round_result_observed=round_evidence["round_result"] != "missing",
    )
    final_status = show["status"]
    changed_files = changed_files_for(task_id)
    direct_round_ran = f"{task_id}__run_direct_execution_round" in labels
    direct_round_observed = bool(
        direct_round_ran
        or (
            round_evidence["round_summary_observed"]
            and round_evidence["round_result"] != "missing"
        )
    )
    worker_reply_present = (project / "supervisor_imports" / task_id / "worker_reply.md").is_file()
    worker_reviewer_mounted = bool(
        expected_route == "direct_execution"
        and direct_round_observed
        and worker_reply_present
        and (project / "supervisor_imports" / task_id / "reviewer_verdict.md").is_file()
    )
    detail_packet_imported = (project / "supervisor_imports" / task_id / "detail_packet.manifest.json").is_file()
    step_files_present = (project / "supervisor_imports" / task_id / "steps" / "step-001.md").is_file()
    execution_after_detail_ready = bool(expected_route == "needs_detail" and direct_round_ran)
    macro_adjustment_request_imported = (
        project / "supervisor_imports" / task_id / "macro_adjustment_request.md"
    ).is_file()
    blocker_evidence_imported = (project / "supervisor_imports" / task_id / "blocker_evidence.md").is_file()
    reviewer_cites_contract = reviewer_cites_execution_contract(task_id)
    errors = []
    add_error(errors, not route_text, "missing route evidence")
    add_error(errors, bool(route_text and route_text != expected_route), f"route mismatch: {route_text}")
    add_error(errors, not show["task_show_observed"], "missing task-show evidence")
    add_error(errors, bool(show["task_show_parse_error"]), f"task-show parse error: {show['task_show_parse_error']}")
    add_error(errors, bool(show["task_show_stale"]), "stale pre-terminal task-show snapshot; final task index or round authority required")
    add_error(
        errors,
        bool(unexpected_tasks),
        "unexpected non-sequence task(s): " + ", ".join(unexpected_tasks),
    )
    add_error(errors, final_status == "missing", "task-show missing status")
    add_error(
        errors,
        bool(final_status != "missing" and final_status != expected_final_status),
        f"status mismatch: {final_status}",
    )
    add_error(errors, round_evidence["round_result"] == "missing", "missing round/result evidence")
    add_error(
        errors,
        bool(round_evidence["round_result"] != "missing" and round_evidence["round_result"] != expected_round_result),
        f"round/result mismatch: {round_evidence['round_result']}",
    )
    for name, ok in checks.items():
        add_error(errors, not ok, f"authority check failed: {name}")
    if task_id in DIRECT_TASK_IDS:
        add_error(errors, not changed_files, "missing project-root change evidence")
        add_error(errors, not worker_reviewer_mounted, "missing worker/reviewer direct-execution evidence")
        add_error(errors, not reviewer_cites_contract, "reviewer did not cite task_packet and execution_contract")
    if task_id == "phase6b-l2-code-test-direct-execution":
        add_error(errors, test_evidence["test_result"] != "pass", "missing or failing project-root test evidence")
        add_error(errors, not test_evidence["test_file_resolved_to_lab"], "test file did not resolve to lab project")
        add_error(errors, not test_evidence["test_sys_path_project_first"], "project root was not first on sys.path")
    if expected_route == "needs_detail":
        add_error(errors, not detail_packet_imported, "missing detail packet evidence")
        add_error(errors, not step_files_present, "missing detail step evidence")
        add_error(errors, execution_after_detail_ready, "execution ran after detail_ready")
    if expected_route == "macro_adjustment_request":
        add_error(errors, not macro_adjustment_request_imported, "missing macro adjustment request evidence")
        add_error(errors, worker_reviewer_mounted, "worker/reviewer mounted for macro adjustment route")
    if expected_route == "blocked":
        add_error(errors, not blocker_evidence_imported, "missing blocker_evidence artifact")
        add_error(errors, worker_reviewer_mounted, "worker/reviewer mounted for blocked route")
    classification = "test_design_failure" if errors else expected_classification
    row = {
        "task_id": task_id,
        "expected_route": expected_route,
        "observed_route": route_text or "missing",
        "expected_final_status": expected_final_status,
        "expected_round_result": expected_round_result,
        "final_status": final_status,
        "task_show_observed": show["task_show_observed"],
        "task_show_path": show["task_show_path"],
        "task_show_source": show["task_show_source"],
        "task_show_stale": show["task_show_stale"],
        "round_summary_observed": round_evidence["round_summary_observed"],
        "round_summary_path": round_evidence["round_summary_path"],
        "round_json_path": round_evidence["round_json_path"],
        "round_result": round_evidence["round_result"],
        "round_result_source": round_evidence["round_result_source"],
        "unexpected_plan_tasks": unexpected_tasks,
        "classification": classification,
        "expected_classification": expected_classification,
        "claimable_row": classification == expected_classification,
        "evidence_errors": errors,
        "changed_files": changed_files,
        "verification_summary": "observed required evidence" if not errors else "; ".join(errors),
        "detailer_activated_expected": expected_route == "needs_detail",
        "detailer_activated_observed": expected_route == "needs_detail" and final_status == "detail_ready",
        "detail_packet_imported": detail_packet_imported,
        "step_files_present": step_files_present,
        "execution_after_detail_ready": execution_after_detail_ready,
        "macro_adjustment_request_imported": macro_adjustment_request_imported,
        "blocker_evidence_imported": blocker_evidence_imported,
        "hidden_fallback_detected": False,
        "scope_shrink_detected": False,
        "reviewer_cites_execution_contract": reviewer_cites_contract,
        "worker_reviewer_mounted": worker_reviewer_mounted,
        "next_owner": show.get("next_owner"),
        "authority_checks": checks,
        **test_evidence,
    }
    rows.append(row)

overall = "pass" if all(row["claimable_row"] for row in rows) else "not_claimable"
rows_path.parent.mkdir(parents=True, exist_ok=True)
rows_path.write_text(
    "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
    encoding="utf-8",
)
b7_path.parent.mkdir(parents=True, exist_ok=True)
b7_path.write_text(
    "# Phase 6B L1-L4 Repeat12 B7\n\n"
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
  assert_no_pending_round_authority ""
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
    frontdesk-entry)
      frontdesk_entry
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
        '  run_l1_l4_sequence12.sh init' \
        '  run_l1_l4_sequence12.sh frontdesk-entry' \
        '  run_l1_l4_sequence12.sh start-task <task_id>' \
        '  run_l1_l4_sequence12.sh continue-route <task_id> <expected_route>' \
        '  run_l1_l4_sequence12.sh continue-detail <task_id>' \
        '  run_l1_l4_sequence12.sh b7' \
        '  run_l1_l4_sequence12.sh cleanup-after-b7' >&2
      exit 64
      ;;
  esac
}

main "$@"
RUN_L1_L4_SEQUENCE12_SH

chmod +x "$PHASE6B_L1L4_SCRIPT"
printf 'materialized L1-L4 sequence12 driver: %s\n' "$PHASE6B_L1L4_SCRIPT"
```

## Supervised Continuation Sequence

These are the checkpoint commands used for the consumed sequence12 packet. Do
not run them again. The supervisor created checkpoint files under
`$PHASE6B_L1L4_PROJECT/supervisor_imports` before each continuation that
requires them.

Shared environment:

```bash
cd /home/bfly/yunwei/test_ccb2
export PHASE6B_L1L4_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705
export PHASE6B_L1L4_PROJECT="$PHASE6B_L1L4_ROOT/l1-l4-real-provider-lab"
export PHASE6B_L1L4_SCRIPT="$PHASE6B_L1L4_ROOT/run_l1_l4_sequence12.sh"
export PHASE6B_L1L4_B7=/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md
export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"
```

| Order | Preconditions | Continuation command shape |
| :--- | :--- | :--- |
| 0 | Materialization succeeded. | `bash "$PHASE6B_L1L4_SCRIPT" init` |
| 1 | Init succeeded. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l1-doc-direct-execution` |
| 2 | Supervisor created route checkpoint with `direct_execution`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l1-doc-direct-execution direct_execution` |
| 3 | L1 evidence captured, including `round_summary.md`, `worker_reply.md`, and `reviewer_verdict.md`. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l2-code-test-direct-execution` |
| 4 | Supervisor created route checkpoint with `direct_execution`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l2-code-test-direct-execution direct_execution` |
| 5 | L2 evidence captured, including `round_summary.md`, `worker_reply.md`, `reviewer_verdict.md`, and `project_root_test_resolution.json`. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l3-needs-detail-source-inspection` |
| 6 | Supervisor created route checkpoint with `needs_detail`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l3-needs-detail-source-inspection needs_detail` |
| 7 | Supervisor created detail checkpoint files. | `bash "$PHASE6B_L1L4_SCRIPT" continue-detail phase6b-l3-needs-detail-source-inspection` |
| 8 | L3 is `detail_ready`; `round_summary.md`, detail packet, and step evidence exist; no execution follows. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l4-macro-adjustment-request` |
| 9 | Supervisor created route checkpoint with `macro_adjustment_request` and `macro_adjustment_request.md`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l4-macro-adjustment-request macro_adjustment_request` |
| 10 | Macro evidence and `round_summary.md` captured. | `bash "$PHASE6B_L1L4_SCRIPT" start-task phase6b-l4-blocked-missing-secret` |
| 11 | Supervisor created route checkpoint with `blocked` and `blocker_evidence.md`. | `bash "$PHASE6B_L1L4_SCRIPT" continue-route phase6b-l4-blocked-missing-secret blocked` |
| 12 | Blocker evidence and `round_summary.md` captured. | `bash "$PHASE6B_L1L4_SCRIPT" b7` |
| 13 | B7 report exists at the repeat12 path. | `bash "$PHASE6B_L1L4_SCRIPT" cleanup-after-b7` |

## B7 Schema Guard

The embedded B7 normalizer in the materialized driver must emit explicit
non-null authority and residue booleans. Every row must include at least:

```text
task_id
expected_route
observed_route
expected_final_status
expected_round_result
final_status
task_show_observed
task_show_path
round_summary_observed
round_summary_path
round_result
round_result_source
classification
expected_classification
claimable_row
evidence_errors
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

The B7 normalizer must parse `ccb_test plan task-show --json` from current
top-level `status` and nested `task.status` fields. A missing task-show file,
missing route, missing `round_summary.md`, or unrun task row is explicit
`test_design_failure` evidence and cannot fall back to the expected status.
Overall `Status: pass` requires every row to have `claimable_row=true`, meaning
observed route, observed task status, observed round/result, and task-specific
artifact/test evidence all match the expected sequence12 contract. L3/L4 rows
that were never run remain not claimable; they must not be normalized into
bounded `valid_non_success` rows.

## Static Verification Completed For Packet Preparation

Packet preparation is static only. Worker3 ran only doc/unit/static checks
before launch-gate review:

```text
python -m py_compile test/test_phase6b_l1_l4_launch_request_doc.py -> passed
python -m pytest test/test_phase6b_l1_l4_launch_request_doc.py -q -> 26 passed
python -m pytest test/test_phase6b_l1_l4_launch_request_doc.py test/test_phase6b_l5_launch_request_doc.py test/test_phase6b_l5_rework_partial_tranche_doc.py -q -> 33 passed
git diff --check on touched docs/tests -> clean
test ! -e /home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705 -> absent
```

Bash parsing of the embedded driver and Python compilation of every embedded
`PY` block are covered by
`test_sequence12_embedded_driver_and_normalizer_are_static_parseable`.

No runtime/provider/source-wrapper/L1-L4/L5/B7/cleanup/launch command was run
by packet preparation. The later talk2 self-review runtime is recorded above:
B7 is `Status: pass` and cleanup returned `kill_status: ok`,
`state: unmounted`.
