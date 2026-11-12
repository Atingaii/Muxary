# Phase 6B L0 Launch Request

Date: 2026-07-04
Status: B-ONLY REPEAT6 EXECUTED / L0 PASS / APPROVAL CONSUMED / DO NOT RUN

## Purpose

This document makes the Phase 6B L0 runtime-sanity launch gate reviewable
and records the executed launch attempts. The corrected repeat request was
approved once by reviewer2 in `job_f3adf3a31988` and executed once under
`talk2` supervision. That approval is consumed. The repeat2 request was then
approved once by reviewer2 in `job_041526ab5f10` and executed once under
`talk2` supervision. That approval is also consumed.

The repeat2 run repaired the stdin-fed ask harness defect and reached variant
B, but it did not pass. It remains `test_design_failure`. The repeat3 request
added explicit release-residue gating and a fixed `hashlib` import in the B7
normalizer. Reviewer2 approved one repeat3 run in `job_90cc9a80d7a0`; that run
was executed once under `talk2` supervision and the approval is consumed.
Reviewer2 then approved one repeat4 run in `job_46d3377feb21`; that run was
executed once under `talk2` supervision and the approval is consumed. Repeat4
produced an auditable `valid_non_success` L0 result. User decision "方案 2：只跑
B，不跑 A" changes the next request shape: repeat5 mounts only the former
variant B resident planning group on a fresh root. Reviewer2 approved one
B-only repeat5 run in `job_2953f5e7ab7e`; that run was executed once under
`talk2` supervision and the approval is consumed. Repeat5 produced an auditable
`valid_non_success` L0 result. The accepted release/drain repair now permits a
fresh B-only repeat6 request to classify a fully drained parked resident
planning group as clean release evidence. Reviewer2 approved one B-only
repeat6 run in `job_8c7b404ad63c`; worker3's package review records the same
launch-specific approval in `job_c7ebe2d2dade`. Talk2 executed that one
approved run from `/home/bfly/yunwei/test_ccb2`, captured B7 evidence before
external cleanup, and consumed the approval. Repeat6 is an L0 runtime-sanity
pass only; it does not approve L1-L5 or claim Phase 6B readiness.

References:

- [Phase 6B launch checklist](phase6b-real-provider-lab-launch-checklist.md)
- [Phase 6B L0 owner decision packet](phase6b-l0-owner-decision-packet-20260704.md)
- [Phase 6B task-pack catalog](phase6-real-provider-lab-task-packs.md)
- [Phase 1-6 evidence index](../history/phase1-6-evidence-index.md)
- Reviewer2 launch-readiness cleanup acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_af0277c593a5-art_fd27e853e98f4830.txt`
- Release/drain semantics repair acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_50ce63ab373b-art_159c32ab43394689.txt`
- Matrix/report `release_incomplete` classification acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_ebe46ce6cd8b-art_c895cae3d4ac466f.txt`
- L1-L4 planning package acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_b9eac0af0f9e-art_973372060e54411a.txt`

## Readiness Result

L0 was approved for one bounded approval-to-run attempt by reviewer2 in
`job_960ec614c477` and executed once under `talk2` supervision. The attempt
did not pass; it produced a `test_design_failure` B7 report. That one-run
approval has been consumed and cannot authorize a repeat.

The corrected repeat was then approved for one bounded run by reviewer2 in
`job_f3adf3a31988` and executed once under `talk2` supervision. This repeat
also did not pass; it produced a second `test_design_failure` B7 report. The
repeat execution submitted variant A ask job `job_25a9c7e4a9b6`, but the
command log stopped after `ask_a_orchestrator_compact`; A release and all
variant B commands were missing. Supervisor diagnosis: the frozen block was
executed through stdin piping, and `ccb_test ask` inherited stdin and consumed
the remaining script body. A further attempt must correct the execution harness
so ask commands cannot consume the runner script, then get fresh launch-review
approval.

The repeat2 request was approved for one bounded run by reviewer2 in
`job_041526ab5f10` and executed once under `talk2` supervision. This repeat2
also did not pass; it produced a third `test_design_failure` B7 report. The
stdin harness fix worked: the script continued past variant A ask/release and
reached variant B. Variant A submitted compact ask job `job_40835bfeed99` to
`phase6b-l0-ccb-orchestrator`; because the ask was submit-only, the job was
still `running` when release was attempted. `topology_a_release` returned `0`
but left `phase6b-l0-ccb-orchestrator` busy/bound and reported
`released_count=0`; variant B then failed at commit/apply with
`agent profile ccb_orchestrator exceeds max_instances=1`. The approved B7
normalizer also failed before writing evidence because it used
`hashlib.sha256` without importing `hashlib`; `talk2` generated a supervisor
fallback B7 from command logs and runtime artifacts.

Owner decisions are recorded for the provider profile map, provider-home
policy, RolePack seed scope, topology scope, ask boundary, timeout, and B7
normalization owner. The B-only repeat6 setup commands, proposal file,
command/evidence collection wrapper, materialized-script harness, cleanup shape,
and normalization procedure were approved once and executed once; they must not
be run again without a new launch-specific approval that names a new root and
command shape.
The decision packet is:
[phase6b-l0-owner-decision-packet-20260704.md](phase6b-l0-owner-decision-packet-20260704.md).

Run evidence:

- First-run B7 report:
  [../history/phase6b-real-provider-l0-b7-20260704.md](../history/phase6b-real-provider-l0-b7-20260704.md)
- First-run evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/phase6b_l0_evidence_row.json`
- First-run command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/phase6b_l0_command_log.jsonl`
- First-run post-run cleanup:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/post_b7_kill_with_roles.stdout`
- Repeat-run launch approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_f3adf3a31988-art_e0ad26e38f534e04.txt`
- Repeat-run B7 report:
  [../history/phase6b-real-provider-l0-repeat-b7-20260704.md](../history/phase6b-real-provider-l0-repeat-b7-20260704.md)
- Repeat-run evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/phase6b_l0_repeat_evidence_row.json`
- Repeat-run command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat-20260704/phase6b_l0_repeat_command_log.jsonl`
- Repeat2-run launch approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_041526ab5f10-art_5fb0add0afc141b7.txt`
- Repeat2-run B7 report:
  [../history/phase6b-real-provider-l0-repeat2-b7-20260704.md](../history/phase6b-real-provider-l0-repeat2-b7-20260704.md)
- Repeat2-run evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/phase6b_l0_repeat2_evidence_row.json`
- Repeat2-run command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/phase6b_l0_repeat2_command_log.jsonl`
- Repeat2-run post-run cleanup:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat2-20260704/logs/post_b7_kill_with_roles.stdout`
- Repeat3-run launch approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_90cc9a80d7a0-art_4b939eb8ba814845.txt`
- Repeat3-run B7 report:
  [../history/phase6b-real-provider-l0-repeat3-b7-20260704.md](../history/phase6b-real-provider-l0-repeat3-b7-20260704.md)
- Repeat3-run evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/phase6b_l0_repeat3_evidence_row.json`
- Repeat3-run command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/phase6b_l0_repeat3_command_log.jsonl`
- Repeat3-run post-run cleanup:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat3-20260704/logs/post_b7_kill_with_roles.stdout`
- Repeat4-run launch approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_46d3377feb21-art_43f3fcc63e90404f.txt`
- Repeat4-run B7 report:
  [../history/phase6b-real-provider-l0-repeat4-b7-20260704.md](../history/phase6b-real-provider-l0-repeat4-b7-20260704.md)
- Repeat4-run evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat4-20260704/phase6b_l0_repeat4_evidence_row.json`
- Repeat4-run command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat4-20260704/phase6b_l0_repeat4_command_log.jsonl`
- Repeat4-run post-run cleanup:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat4-20260704/logs/post_b7_kill_with_roles.stdout`
- B-only repeat5 launch approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_2953f5e7ab7e-art_44ef33571b3d4e09.txt`
- B-only repeat5 B7 report:
  [../history/phase6b-real-provider-l0-b-only-repeat5-b7-20260704.md](../history/phase6b-real-provider-l0-b-only-repeat5-b7-20260704.md)
- B-only repeat5 evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/phase6b_l0_b_only_repeat5_evidence_row.json`
- B-only repeat5 command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/phase6b_l0_b_only_repeat5_command_log.jsonl`
- B-only repeat5 post-run cleanup:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704/logs/post_b7_kill_with_roles.stdout`
- B-only repeat6 launch approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_8c7b404ad63c-art_948e9db1551a4458.txt`
- B-only repeat6 package approval:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_c7ebe2d2dade-art_350f83cd6ffa4770.txt`
- B-only repeat6 B7 report:
  [../history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md](../history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md)
- B-only repeat6 evidence row:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_evidence_row.json`
- B-only repeat6 command log:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_command_log.jsonl`
- B-only repeat6 post-run cleanup:
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/logs/post_b7_kill_with_roles.stdout`

Observed blockers from the executed attempts:

- Variant A mounted `phase6b-l0-ccb-orchestrator`, but the compact ask targeted
  `ccb_orchestrator`, so `ccb_test ask` returned `unknown agent`.
- Variant B proposal was rejected before apply because the generated proposal
  id exceeded the current agent-name length/regex; corrected repeat requests
  keep both the proposal id and generated agent ids inside that regex.
- The approved B7 normalizer could not handle missing runtime artifacts after
  variant B proposal failure.
- A release command returned `0`, but pre-cleanup evidence still showed the
  dynamic A agent in `ps`/config-derived status; cleanup was therefore not a
  pass condition.
- The corrected repeat submitted variant A successfully, then stopped because
  the stdin-fed shell harness let `ccb_test ask` consume the remaining runner
  text as ask stdin. Corrected repeat requests materialize `run_l0.sh` and
  redirects every `run_l0_command` child stdin from `/dev/null`.
- Repeat2 proved the stdin fix but surfaced a profile-capacity/release blocker:
  after submit-only A ask, `topology_a_release` returned `0` while the dynamic
  A orchestrator remained `busy`/bound; B failed at commit/apply with
  `agent profile ccb_orchestrator exceeds max_instances=1`.
- Repeat2 approved B7 normalizer missed `import hashlib`; the B7 report was
  generated by `talk2` supervisor fallback from command logs and runtime
  artifacts.
- Corrected source now reports active post-release topology residue as
  `release_incomplete` with blocking agent/profile evidence. The corrected
  repeat3 harness must stop before variant B when A release is not clean.
- Repeat3 proved the release gate: A compact ask submitted
  `job_b7a8ed0f671e`, A release reported `release_incomplete`, and
  `topology_a_release_clean_check` returned `66` before variant B. The B7
  normalizer still classified the run as `test_design_failure` because it
  expects `.ccb/runtime/asks.jsonl`; actual ask evidence existed under
  `.ccb/agents/phase6b-l0-ccb-orchestrator/jobs.jsonl`. This ask-evidence
  contract was corrected for repeat4, which used a fresh root and produced
  `valid_non_success` evidence.
- Repeat4 proved the repaired normalizer path: A compact ask submitted
  `job_0f9d5c50b756`, A release again reported `release_incomplete`, and
  `topology_a_release_clean_check` returned `66` before variant B. The
  normalizer found dynamic-agent/ccbd ask evidence and classified the run as
  `valid_non_success` with no test-design failures. Post-B7 cleanup returned
  `kill_status: ok` and `state: unmounted`. The next request intentionally
  drops the minimal orchestrator A probe and runs only the resident planning
  group topology.
- B-only repeat5 proved the former variant B can mount and submit its ask
  without the A capacity collision: compact ask submitted
  `job_699a6c2997ad` to `p6bl0b-orchestrator`, all command labels returned
  `0`, and the normalizer found dynamic-agent/ccbd ask evidence. It still
  classified as `valid_non_success` because `topology_b_release` reported
  `release_incomplete`: `p6bl0b-frontdesk`, `p6bl0b-detailer`,
  `p6bl0b-planner`, and `p6bl0b-orchestrator` remained parked/active after
  release. Post-B7 cleanup returned `kill_status: ok` and `state: unmounted`.
- B-only repeat6 proved the repaired drained-release path for L0 runtime
  sanity: compact ask submitted `job_4181721f9473` to
  `p6bl0b-orchestrator`, all command labels returned `0`, `topology_b_release`
  reported `loop_topology_status=released`, `drained_agents` contained
  `p6bl0b-frontdesk`, `p6bl0b-detailer`, `p6bl0b-planner`, and
  `p6bl0b-orchestrator`, and every `drain_reasons` entry was
  `parked_after_release`. B7 classified the row as `pass`; post-B7 cleanup
  returned `kill_status: ok` and `state: unmounted`.

## Proposed B-Only Repeat6 Lab Root

Proposed external root:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704
```

Proposed project root:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity
```

Source checkout and source wrapper:

```text
/home/bfly/yunwei/ccb_source
/home/bfly/yunwei/ccb_source/ccb_test
```

The lab root is intentionally outside `/home/bfly/yunwei/ccb_source`.
This repeat6 request uses a fresh fixed root. The command sequence refuses to
run if that root already exists and is non-empty. Previous L0 roots contain
execution evidence and must not be reused or wiped as part of another launch
attempt.

## Isolation Policy

Proposed environment paths:

```text
HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/source_home
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/source_home
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/roles
```

Provider home:

```text
approved_inherited_current_real_provider_home
```

Owner rationale:

- CCB has session isolation;
- execution remains constrained to an external project under
  `/home/bfly/yunwei/test_ccb2`;
- isolated `HOME`, `CCB_SOURCE_HOME`, and `AGENT_ROLES_STORE` still apply.

Risk to preserve for review: inherited provider home may use existing
real-provider credentials, quota, and account/session state. The launch
reviewer must explicitly accept this risk before L0 runs. The B7 report must
record the actual provider-home/account evidence observed during the run.

## Provider Profile Selection

Owner-selected L0 provider map:

| Role | Provider profile |
| :--- | :--- |
| `ccb_frontdesk` | `codex` |
| `ccb_planner` | `codex` |
| `ccb_orchestrator` | `codex` |
| `ccb_task_detailer` | `codex` |
| `ccb_round_reviewer` | `claude` |
| `coder` | `codex` |
| `code_reviewer` | `codex` |

Do not infer additional profile names, account homes, or credentials from
local state. L0 asks only the mounted resident planning group orchestrator
agent; the full map is recorded for lab consistency and B7 evidence.

## RolePack Seeding Plan

Use a lab-local RolePack store only:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/roles
```

Seed from the accepted source-tree RolePack drafts without installing into the
global/system CCB environment. The intended shape follows the source-wrapper
smoke seeding pattern:

```text
<AGENT_ROLES_STORE>/installed/<role-id>/current/
```

Role ids to seed for L0:

- `agentroles.ccb_frontdesk`
- `agentroles.ccb_planner`
- `agentroles.ccb_orchestrator`
- `agentroles.ccb_task_detailer`
- `agentroles.ccb_round_reviewer`
- `agentroles.coder`
- `agentroles.code_reviewer`

Do not pre-seed for L0:

- `agentroles.ccb_clarification_broker`
- `agentroles.ccb_plan_reviewer`

Launch-review decision `job_2953f5e7ab7e` approved the exact lab-local seed
command below for one run; that approval is consumed.

## L0 Task Shape

Task id:

```text
phase6b-l0-runtime-sanity
```

Objective:

```text
Verify one real-provider resident planning group mount:

- `p6bl0b-frontdesk` -> `ccb_frontdesk`;
- `p6bl0b-detailer` -> `ccb_task_detailer`;
- `p6bl0b-planner` -> `ccb_planner`;
- `p6bl0b-orchestrator` -> `ccb_orchestrator`.

Submit one compact reachability ask to the mounted target
`p6bl0b-orchestrator`. Record ask/job reachability, release the topology, and
prove no dynamic runtime residue remains.
```

Expected route:

```text
runtime_sanity
```

Allowed final statuses:

- `ok`
- `valid_non_success` with explicit provider/environment or release-residue
  evidence and bounded post-B7 cleanup

## Proposed B-Only Repeat6 Command Sequence

Status: LAUNCH-REVIEW PENDING / DO NOT RUN.

The command sequence below is the B-only repeat6 request prepared for
launch-specific reviewer approval. It omits the former
minimal orchestrator A probe and does not run `topology_a_*`, `ask_a_*`, or
`topology_a_release_clean_check`. Runtime commands must run from
`/home/bfly/yunwei/test_ccb2`, not from `/home/bfly/yunwei/ccb_source`.

The harness materializes the reviewed `run_l0.sh` under the fresh lab root and
executes it with `bash "$PHASE6B_L0_SCRIPT"`. The L0 runner must not be
executed from a Markdown-extracted stdin stream. Every child command launched
through `run_l0_command` receives stdin from `/dev/null`. Any helper, wrapper,
or future ask-invoking child outside `run_l0_command` must also redirect stdin
from `/dev/null`; otherwise that ask-invoking child is forbidden.

```bash
# DO NOT RUN until reviewer launch approval exists.
cd /home/bfly/yunwei/test_ccb2

set -uo pipefail

export PHASE6B_L0_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704
export PHASE6B_L0_PROJECT="$PHASE6B_L0_ROOT/l0-runtime-sanity"
export PHASE6B_L0_SCRIPT="$PHASE6B_L0_ROOT/run_l0.sh"
export HOME="$PHASE6B_L0_ROOT/source_home"
export CCB_SOURCE_HOME="$PHASE6B_L0_ROOT/source_home"
export AGENT_ROLES_STORE="$PHASE6B_L0_ROOT/roles"

case "$PWD" in
  /home/bfly/yunwei/test_ccb2|/home/bfly/yunwei/test_ccb2/*) ;;
  *) echo "refuse: L0 must run from /home/bfly/yunwei/test_ccb2" >&2; exit 64 ;;
esac

case "$PHASE6B_L0_PROJECT" in
  "$PHASE6B_L0_ROOT"/*) ;;
  *) echo "refuse: project must live under PHASE6B_L0_ROOT" >&2; exit 64 ;;
esac

case "$AGENT_ROLES_STORE" in
  "$PHASE6B_L0_ROOT"/roles) ;;
  *) echo "refuse: AGENT_ROLES_STORE must be lab-local" >&2; exit 64 ;;
esac

if [ -e "$PHASE6B_L0_ROOT" ] && [ -n "$(find "$PHASE6B_L0_ROOT" -mindepth 1 -print -quit 2>/dev/null)" ]; then
  echo "refuse: repeat L0 root must be new or empty: $PHASE6B_L0_ROOT" >&2
  exit 65
fi

mkdir -p "$PHASE6B_L0_ROOT"

cat > "$PHASE6B_L0_SCRIPT" <<'RUN_L0_SH'
#!/usr/bin/env bash
set -uo pipefail

export PHASE6B_L0_ROOT=${PHASE6B_L0_ROOT:-/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704}
export PHASE6B_L0_PROJECT="$PHASE6B_L0_ROOT/l0-runtime-sanity"
export PHASE6B_L0_SCRIPT="${PHASE6B_L0_SCRIPT:-$PHASE6B_L0_ROOT/run_l0.sh}"
export PHASE6B_L0_SCRIPT_SHA256_PATH="$PHASE6B_L0_ROOT/run_l0.sh.sha256"
export HOME="$PHASE6B_L0_ROOT/source_home"
export CCB_SOURCE_HOME="$PHASE6B_L0_ROOT/source_home"
export AGENT_ROLES_STORE="$PHASE6B_L0_ROOT/roles"
export PHASE6B_L0_PROVIDER_HOME_MODE=approved_inherited_current_real_provider_home
export PHASE6B_L0_PROVIDER_PROFILE_MAP='{"ccb_frontdesk":"codex","ccb_planner":"codex","ccb_orchestrator":"codex","ccb_task_detailer":"codex","ccb_round_reviewer":"claude","coder":"codex","code_reviewer":"codex"}'
export PHASE6B_L0_TIMEOUT_SECONDS=600
export PHASE6B_L0_COMMAND_LOG="$PHASE6B_L0_ROOT/phase6b_l0_b_only_repeat6_command_log.jsonl"

case "$PWD" in
  /home/bfly/yunwei/test_ccb2|/home/bfly/yunwei/test_ccb2/*) ;;
  *) echo "refuse: L0 must run from /home/bfly/yunwei/test_ccb2" >&2; exit 64 ;;
esac

case "$PHASE6B_L0_PROJECT" in
  "$PHASE6B_L0_ROOT"/*) ;;
  *) echo "refuse: project must live under PHASE6B_L0_ROOT" >&2; exit 64 ;;
esac

case "$PHASE6B_L0_SCRIPT" in
  "$PHASE6B_L0_ROOT"/run_l0.sh) ;;
  *) echo "refuse: PHASE6B_L0_SCRIPT must be lab-local run_l0.sh" >&2; exit 64 ;;
esac

case "$AGENT_ROLES_STORE" in
  "$PHASE6B_L0_ROOT"/roles) ;;
  *) echo "refuse: AGENT_ROLES_STORE must be lab-local" >&2; exit 64 ;;
esac

mkdir -p \
  "$PHASE6B_L0_PROJECT/.ccb" \
  "$PHASE6B_L0_PROJECT/drafts" \
  "$PHASE6B_L0_ROOT/logs" \
  "$HOME" \
  "$CCB_SOURCE_HOME" \
  "$AGENT_ROLES_STORE/installed"

sha256sum "$PHASE6B_L0_SCRIPT" > "$PHASE6B_L0_SCRIPT_SHA256_PATH"
: > "$PHASE6B_L0_COMMAND_LOG"

run_l0_command() {
  local label="$1"
  shift
  local stdout_path="$PHASE6B_L0_ROOT/logs/${label}.stdout"
  local stderr_path="$PHASE6B_L0_ROOT/logs/${label}.stderr"
  local started_at
  local finished_at
  local rc
  started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  timeout --preserve-status "${PHASE6B_L0_TIMEOUT_SECONDS}s" "$@" \
    </dev/null >"$stdout_path" 2>"$stderr_path"
  rc=$?
  finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  python - "$PHASE6B_L0_COMMAND_LOG" "$label" "$rc" "$stdout_path" "$stderr_path" "$started_at" "$finished_at" "$@" <<'PY'
import hashlib
import json
import os
import sys
from pathlib import Path

log_path, label, rc, stdout_path, stderr_path, started_at, finished_at, *argv = sys.argv[1:]
script_path = os.environ.get("PHASE6B_L0_SCRIPT")
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

run_l0_required() {
  run_l0_command "$@"
  local rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "required L0 command failed: $1 rc=$rc" >&2
    exit "$rc"
  fi
}

# Lab-local RolePack seed: required seven roles only.
for role_id in \
  agentroles.ccb_frontdesk \
  agentroles.ccb_planner \
  agentroles.ccb_orchestrator \
  agentroles.ccb_task_detailer \
  agentroles.ccb_round_reviewer \
  agentroles.coder \
  agentroles.code_reviewer
do
  src="/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/drafts/${role_id}"
  dst="$AGENT_ROLES_STORE/installed/${role_id}/current"
  test -d "$src"
  rm -rf "$dst"
  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
done

python - "$PHASE6B_L0_ROOT" "$AGENT_ROLES_STORE" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
store = Path(sys.argv[2])
role_ids = [
    "agentroles.ccb_frontdesk",
    "agentroles.ccb_planner",
    "agentroles.ccb_orchestrator",
    "agentroles.ccb_task_detailer",
    "agentroles.ccb_round_reviewer",
    "agentroles.coder",
    "agentroles.code_reviewer",
]
records = []
for role_id in role_ids:
    source = Path("/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/drafts") / role_id
    destination = store / "installed" / role_id / "current"
    files = sorted(str(path.relative_to(destination)) for path in destination.rglob("*") if path.is_file())
    records.append(
        {
            "role_id": role_id,
            "source_path": str(source),
            "destination_path": str(destination),
            "files": files,
        }
    )
(root / "rolepack_seed_manifest.json").write_text(
    json.dumps({"role_count": len(records), "roles": records}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
PY

# Project config: ccb_round_reviewer=claude; the other six mapped roles=codex.
cat > "$PHASE6B_L0_PROJECT/.ccb/ccb.config" <<'EOF'
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
max_nodes = 4
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

# Mount-only topology proposal: resident planning group.
cat > "$PHASE6B_L0_PROJECT/drafts/phase6b-l0-mount-topology-b-resident-planning-group.json" <<'JSON'
{
  "schema": "ccb.loop.agent_mount_topology.v1",
  "release_policy": {
    "idle_only": true,
    "policy": "auto"
  },
  "nodes": [
    {
      "agents": [
        {
          "desired_state": "present",
          "id": "p6bl0b-frontdesk",
          "lifecycle": "ephemeral",
          "profile": "ccb_frontdesk",
          "release_policy": "auto"
        },
        {
          "desired_state": "present",
          "id": "p6bl0b-detailer",
          "lifecycle": "ephemeral",
          "profile": "ccb_task_detailer",
          "release_policy": "auto"
        }
      ],
      "id": "user-boundary"
    },
    {
      "agents": [
        {
          "desired_state": "present",
          "id": "p6bl0b-planner",
          "lifecycle": "ephemeral",
          "profile": "ccb_planner",
          "release_policy": "auto"
        },
        {
          "desired_state": "present",
          "id": "p6bl0b-orchestrator",
          "lifecycle": "ephemeral",
          "profile": "ccb_orchestrator",
          "release_policy": "auto"
        }
      ],
      "id": "planning"
    }
  ]
}
JSON

run_l0_required diagnose \
  /home/bfly/yunwei/ccb_source/ccb_test --diagnose

run_l0_required config_validate_initial \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" config validate

run_l0_required start_project \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT"

# B-only: resident planning group mount, only orchestrator asked.
run_l0_required topology_b_propose \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" \
  loop topology propose \
  --loop-id p6bl0b \
  --from "$PHASE6B_L0_PROJECT/drafts/phase6b-l0-mount-topology-b-resident-planning-group.json" \
  --proposal-id p6bl0b-plan \
  --json

run_l0_required topology_b_commit_apply \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" \
  loop topology commit \
  --loop-id p6bl0b \
  --proposal p6bl0b-plan \
  --apply \
  --json

# The wrapper enforces PHASE6B_L0_TIMEOUT_SECONDS for this compact submit-only ask.
run_l0_command ask_b_orchestrator_compact \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" \
  ask \
  --compact \
  p6bl0b-orchestrator \
  "Phase 6B L0 runtime sanity only. Reply with a short reachability acknowledgement. Do not change task status, topology, files, or plan state."

run_l0_command ps_b_after_ask \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" ps

run_l0_required topology_b_release \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" \
  loop topology release \
  --loop-id p6bl0b \
  --json

run_l0_required ps_b_after_release \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" ps

run_l0_required config_validate_after_b \
  /home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" config validate

# After the run, talk2 normalizes B7 from the exact inputs/outputs listed in
# the "Talk2-Owned B7 Normalization Procedure" section below. Provider replies
# remain evidence only and do not write authority fields.
RUN_L0_SH

chmod 700 "$PHASE6B_L0_SCRIPT"
sha256sum "$PHASE6B_L0_SCRIPT" > "$PHASE6B_L0_ROOT/run_l0.sh.sha256"
bash "$PHASE6B_L0_SCRIPT"
```

Frozen command/schema review surfaces:

- exact role seed command;
- exact project config writer;
- exact B-only mount-only topology proposal file contents;
- command-log capture and timeout enforcement wrapper;
- `talk2` B7 normalization procedure below.

The topology proposal JSON file above is mount-only. It intentionally omits
`edges`, `gates`, and `artifacts`, and this request does not write or invoke
`topology_dispatch.json`.

Release semantics for this B-only repeat6 L0: `loop topology release --json` is
expected to report clean release. For resident planning-group agents that park
after release, the accepted clean path is explicit drained evidence: all
expected agent ids appear in `drained_agents` and
`drain_reasons={agent: parked_after_release}`. Observed topology authority must
omit the released agent ids or mark them absent/released. Bounded
`release_incomplete_agents` with bounded `release_blockers` may classify as
`valid_non_success`; missing, vague, or unbounded residue is hard failure
evidence. There is no A-release clean gate in this request because there is no
A probe. The final external `kill` cleanup below is retained as a separate
cleanup step and is not a substitute for pass-condition release evidence.

## Talk2-Owned B7 Normalization Procedure

Status: COMMAND FROZEN / DO NOT RUN UNTIL AFTER APPROVED L0 EXECUTION.

Owner: `talk2`.

Normalization inputs:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/run_l0.sh
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/run_l0.sh.sha256
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_command_log.jsonl
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/rolepack_seed_manifest.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccb.config
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/asks.jsonl (optional legacy ask index)
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/agents/*/jobs.jsonl
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccbd/snapshots/job_*.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccbd/messages/messages.jsonl
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/ccbd/mailboxes/*/inbox.jsonl
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/logs/*.stdout
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/logs/*.stderr
```

Normalization outputs:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_evidence_row.json
docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md
```

Exact normalization command shape for reviewer approval:

```bash
# DO NOT RUN until L0 has approved execution evidence.
python - "$PHASE6B_L0_ROOT" "$PHASE6B_L0_PROJECT" \
  /home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md <<'PY'
import hashlib
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
project = Path(sys.argv[2])
b7_path = Path(sys.argv[3])
command_log_path = root / "phase6b_l0_b_only_repeat6_command_log.jsonl"
row_path = root / "phase6b_l0_b_only_repeat6_evidence_row.json"
script_path = root / "run_l0.sh"
script_sha256_path = root / "run_l0.sh.sha256"

provider_mix = {
    "ccb_frontdesk": "codex",
    "ccb_planner": "codex",
    "ccb_orchestrator": "codex",
    "ccb_task_detailer": "codex",
    "ccb_round_reviewer": "claude",
    "coder": "codex",
    "code_reviewer": "codex",
}

def load_json(path):
    if not path.is_file():
        return None, f"missing artifact: {path}"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"invalid json: {path}: {exc}"

def load_jsonl(path):
    if not path.is_file():
        return [], f"missing artifact: {path}"
    records = []
    errors = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid jsonl: {path}:{line_number}: {exc}")
    return records, "; ".join(errors) if errors else None

def file_sha256(path):
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_text_from_record(record):
    raw_path = record.get("stdout_path") if record else None
    if not raw_path:
        return None
    path = Path(raw_path)
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")

def extract_agents(payload):
    if not isinstance(payload, dict):
        return []
    agents = []
    for agent in payload.get("agents", []):
        if isinstance(agent, dict):
            agents.append(agent)
    for node in payload.get("nodes", []):
        if not isinstance(node, dict):
            continue
        for agent in node.get("agents", []):
            if isinstance(agent, dict):
                agents.append(agent)
    return agents

def agent_ids(payload):
    return sorted(agent.get("id") for agent in extract_agents(payload) if agent.get("id"))

def agent_profiles(payload):
    return sorted(agent.get("profile") for agent in extract_agents(payload) if agent.get("profile"))

def no_dispatch_keys(payload):
    return isinstance(payload, dict) and all(key not in payload for key in ("edges", "gates", "artifacts"))

def observed_release_absent(payload, expected_ids):
    if not isinstance(payload, dict):
        return False
    observed_agents = [agent for agent in extract_agents(payload) if agent.get("id") in expected_ids]
    if not observed_agents:
        return True
    clean_states = {"absent", "released", "removed", "unmounted"}
    for agent in observed_agents:
        state = str(
            agent.get("observed_state")
            or agent.get("state")
            or agent.get("status")
            or agent.get("desired_state")
            or ""
        ).lower()
        if state not in clean_states:
            return False
    return True

def release_drained_expected(payload, expected_ids):
    if not isinstance(payload, dict):
        return False
    drained_agents = sorted(str(item) for item in payload.get("drained_agents", []) if str(item))
    expected = sorted(expected_ids)
    if drained_agents != expected:
        return False
    if int(payload.get("drained_count") or 0) != len(expected):
        return False
    reasons = payload.get("drain_reasons", {})
    if not isinstance(reasons, dict):
        return False
    return all(reasons.get(agent_id) == "parked_after_release" for agent_id in expected)

command_log, command_log_error = load_jsonl(command_log_path)
command_by_label = {
    item.get("label"): item
    for item in command_log
    if isinstance(item, dict) and item.get("label")
}
ask_evidence_records = []
ask_evidence_paths = []
ask_evidence_errors = []

ask_jsonl_candidates = [
    project / ".ccb/runtime/asks.jsonl",
    project / ".ccb/ccbd/messages/messages.jsonl",
    project / ".ccb/ccbd/replies/replies.jsonl",
]
ask_jsonl_candidates.extend(sorted((project / ".ccb/agents").glob("*/jobs.jsonl")))
ask_jsonl_candidates.extend(sorted((project / ".ccb/ccbd/mailboxes").glob("*/inbox.jsonl")))
for candidate in ask_jsonl_candidates:
    if not candidate.is_file():
        continue
    records, error = load_jsonl(candidate)
    ask_evidence_paths.append(str(candidate))
    ask_evidence_records.extend(records)
    if error:
        ask_evidence_errors.append(error)
for snapshot_path in sorted((project / ".ccb/ccbd/snapshots").glob("job_*.json")):
    payload, error = load_json(snapshot_path)
    ask_evidence_paths.append(str(snapshot_path))
    if payload is not None:
        ask_evidence_records.append(payload)
    if error:
        ask_evidence_errors.append(error)
if not ask_evidence_records:
    ask_evidence_errors.append(
        "missing ask evidence artifacts: .ccb/runtime/asks.jsonl, .ccb/agents/*/jobs.jsonl, "
        ".ccb/ccbd/snapshots/job_*.json, .ccb/ccbd/messages/messages.jsonl, or .ccb/ccbd/mailboxes/*/inbox.jsonl"
    )
input_errors = [item for item in (command_log_error, *ask_evidence_errors) if item]
missing_artifacts = []
artifact_errors = []

def read_json_from_record(label):
    text = read_text_from_record(command_by_label.get(label, {}))
    if text is None:
        return None
    raw = text.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    for line in reversed(raw.splitlines()):
        if not line.strip():
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError as exc:
            artifact_errors.append(f"invalid command stdout json: {label}: {exc}")
            return None
    return None

script_sha256 = file_sha256(script_path)
script_sha256_recorded = None
if not script_path.is_file():
    missing_artifacts.append(str(script_path))
if not script_sha256_path.is_file():
    missing_artifacts.append(str(script_sha256_path))
else:
    script_sha256_parts = script_sha256_path.read_text(encoding="utf-8").split()
    if script_sha256_parts:
        script_sha256_recorded = script_sha256_parts[0]
    else:
        artifact_errors.append(f"empty script sha256 file: {script_sha256_path}")
if script_sha256 and script_sha256_recorded and script_sha256 != script_sha256_recorded:
    artifact_errors.append(f"script sha256 mismatch: {script_sha256_path}")

variant_paths = {
    "resident_planning_group": {
        "proposal": project / ".ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json",
        "desired": project / ".ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
        "observed": project / ".ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
        "events": project / ".ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
        "release_label": "topology_b_release",
        "ask_label": "ask_b_orchestrator_compact",
        "post_release_ps_label": "ps_b_after_release",
        "post_release_config_label": "config_validate_after_b",
        "ask_target": "p6bl0b-orchestrator",
        "expected_agent_ids": ["p6bl0b-frontdesk", "p6bl0b-detailer", "p6bl0b-planner", "p6bl0b-orchestrator"],
        "expected_profiles": ["ccb_frontdesk", "ccb_task_detailer", "ccb_planner", "ccb_orchestrator"],
    },
}

variant_results = {}
authority_write_violations = []
runtime_residue_by_variant = {}
for name, paths in variant_paths.items():
    proposal, proposal_error = load_json(paths["proposal"])
    desired, desired_error = load_json(paths["desired"])
    observed, observed_error = load_json(paths["observed"])
    events_present = paths["events"].is_file()
    for key, problem in (
        ("proposal", proposal_error),
        ("desired", desired_error),
        ("observed", observed_error),
    ):
        if problem:
            artifact_errors.append(f"{name}.{key}: {problem}")
            missing_artifacts.append(str(paths[key]))
    if not events_present:
        missing_artifacts.append(str(paths["events"]))
    proposal_profiles = agent_profiles(proposal)
    desired_profiles = agent_profiles(desired)
    observed_profiles = agent_profiles(observed)
    proposal_agent_ids = agent_ids(proposal)
    desired_agent_ids = agent_ids(desired)
    observed_agent_ids = agent_ids(observed)
    release_record = command_by_label.get(paths["release_label"], {})
    release_payload = read_json_from_record(paths["release_label"])
    drained_clean = release_drained_expected(release_payload, paths["expected_agent_ids"])
    for payload_name, payload in (("proposal", proposal), ("desired", desired), ("observed", observed)):
        if isinstance(payload, dict) and not no_dispatch_keys(payload):
            authority_write_violations.append(f"{name}.{payload_name}: topology dispatch keys present")
    desired_profiles_ok = desired_profiles == sorted(paths["expected_profiles"]) or (
        drained_clean and desired_profiles == []
    )
    if isinstance(desired, dict) and not desired_profiles_ok:
        authority_write_violations.append(f"{name}: desired profiles {desired_profiles} differ from expected {paths['expected_profiles']}")
    ask_record = command_by_label.get(paths["ask_label"], {})
    ps_record = command_by_label.get(paths["post_release_ps_label"], {})
    config_record = command_by_label.get(paths["post_release_config_label"], {})
    ps_text = read_text_from_record(ps_record)
    config_text = read_text_from_record(config_record)
    dynamic_absent = ps_text is not None and all(agent_id not in ps_text for agent_id in paths["expected_agent_ids"])
    config_absent = config_text is not None and all(agent_id not in config_text for agent_id in paths["expected_agent_ids"])
    observed_absent = observed_release_absent(observed, paths["expected_agent_ids"])
    runtime_residue_by_variant[name] = {
        "dynamic_agents_absent": dynamic_absent,
        "config_dynamic_agents_absent": config_absent,
        "observed_topology_residue_absent": observed_absent,
    }
    variant_results[name] = {
        "proposal_path": str(paths["proposal"]),
        "desired_path": str(paths["desired"]),
        "observed_path": str(paths["observed"]),
        "events_path": str(paths["events"]),
        "missing_artifacts": [str(path) for path in (paths["proposal"], paths["desired"], paths["observed"], paths["events"]) if not path.is_file()],
        "ask_target": paths["ask_target"],
        "expected_agent_ids": paths["expected_agent_ids"],
        "proposal_agent_ids": proposal_agent_ids,
        "desired_agent_ids": desired_agent_ids,
        "observed_agent_ids": observed_agent_ids,
        "proposal_profiles": proposal_profiles,
        "desired_profiles": desired_profiles,
        "observed_profiles": observed_profiles,
        "ask_returncode": ask_record.get("returncode"),
        "release_returncode": release_record.get("returncode"),
        "release_loop_topology_status": release_payload.get("loop_topology_status") if isinstance(release_payload, dict) else None,
        "release_drained_agents": release_payload.get("drained_agents", []) if isinstance(release_payload, dict) else [],
        "release_drained_clean": drained_clean,
        "release_incomplete_agents": release_payload.get("release_incomplete_agents", []) if isinstance(release_payload, dict) else [],
        "release_blockers": release_payload.get("release_blockers", {}) if isinstance(release_payload, dict) else {},
        "dynamic_agents_absent_after_release": dynamic_absent,
        "config_dynamic_agents_absent_after_release": config_absent,
        "observed_topology_residue_absent": observed_absent,
    }

base_required_labels = {
    "diagnose",
    "config_validate_initial",
    "start_project",
    "topology_b_propose",
    "topology_b_commit_apply",
    "ask_b_orchestrator_compact",
    "ps_b_after_ask",
    "topology_b_release",
    "ps_b_after_release",
    "config_validate_after_b",
}
required_labels = base_required_labels

missing_labels = sorted(required_labels - set(command_by_label))
ask_targets = {name: paths["ask_target"] for name, paths in variant_paths.items()}
ask_targets_logged = {}
ask_reachability_by_variant = {}
for name, paths in variant_paths.items():
    target_logged = any(paths["ask_target"] in json.dumps(item, sort_keys=True) for item in ask_evidence_records)
    ask_targets_logged[name] = target_logged
    ask_reachability_by_variant[name] = (
        command_by_label.get(paths["ask_label"], {}).get("returncode") == 0
        and target_logged
    )
required_artifacts_present = not missing_artifacts and not artifact_errors
ask_reachability = all(value is True for value in ask_reachability_by_variant.values() if value is not None)
release_commands_ok = command_by_label.get("topology_b_release", {}).get("returncode") == 0
release_loop_topology_status = variant_results["resident_planning_group"]["release_loop_topology_status"]
runtime_residue = {
    "dynamic_agents_absent": all(item["dynamic_agents_absent"] for item in runtime_residue_by_variant.values()),
    "config_dynamic_agents_absent": all(item["config_dynamic_agents_absent"] for item in runtime_residue_by_variant.values()),
    "observed_topology_residue_absent": all(item["observed_topology_residue_absent"] for item in runtime_residue_by_variant.values()),
}
drained_release_clean = (
    all(item["release_drained_clean"] for item in variant_results.values())
    and runtime_residue["observed_topology_residue_absent"]
)
release_clean = (
    release_commands_ok
    and release_loop_topology_status == "released"
    and (all(runtime_residue.values()) or drained_release_clean)
)
authority_clean = not authority_write_violations
ask_command_returncode = command_by_label.get("ask_b_orchestrator_compact", {}).get("returncode")
ask_command_failed = ask_command_returncode not in (None, 0)
test_design_failures = []
if missing_labels:
    test_design_failures.append("Required command labels are missing: " + ", ".join(missing_labels))
if missing_artifacts:
    test_design_failures.append("Required runtime artifacts are missing: " + ", ".join(sorted(set(missing_artifacts))))
if artifact_errors:
    test_design_failures.extend(artifact_errors)
if input_errors:
    test_design_failures.extend(input_errors)
pass_conditions = (
    not missing_labels
    and not input_errors
    and script_sha256 is not None
    and script_sha256 == script_sha256_recorded
    and required_artifacts_present
    and ask_reachability
    and release_clean
    and authority_clean
)
if pass_conditions:
    classification = "pass"
elif test_design_failures:
    classification = "test_design_failure"
elif ask_command_failed:
    classification = "provider_failure"
else:
    classification = "valid_non_success"

row = {
    "task_id": "phase6b-l0-runtime-sanity",
    "complexity_level": "L0",
    "provider_mix": provider_mix,
    "provider_home_mode": "approved_inherited_current_real_provider_home",
    "script_path": str(script_path),
    "script_sha256": script_sha256,
    "script_sha256_recorded": script_sha256_recorded,
    "script_sha256_matches": script_sha256 is not None and script_sha256 == script_sha256_recorded,
    "topology_variants": ["resident_planning_group"],
    "ask_targets": ask_targets,
    "ask_targets_logged": ask_targets_logged,
    "ask_reachability_by_variant": ask_reachability_by_variant,
    "ask_evidence_paths": ask_evidence_paths,
    "ask_evidence_errors": ask_evidence_errors,
    "expected_route": "runtime_sanity",
    "observed_route": "runtime_sanity",
    "route_decision_correct": True,
    "required_artifacts_present": required_artifacts_present,
    "ask_reachability": ask_reachability,
    "detailer_activated_expected": False,
    "detailer_activated_observed": False,
    "worker_reviewer_ask_success": None,
    "reviewer_contract_citation": None,
    "round_result": "not_applicable",
    "final_status": "ok" if classification == "pass" else classification,
    "cleanup_result": "released" if release_clean else "release_incomplete",
    "runtime_residue": runtime_residue,
    "role_boundary_violations": [],
    "authority_write_violations": authority_write_violations,
    "classification": classification,
    "human_diagnosis_summary": "L0 runtime sanity normalized from command logs, topology artifacts, ask log, and release residue evidence. Provider replies are evidence only and do not mutate authority fields.",
    "missing_command_labels": missing_labels,
    "missing_artifacts": sorted(set(missing_artifacts)),
    "input_errors": input_errors,
    "test_design_failures": test_design_failures,
    "command_returncodes": {label: record.get("returncode") for label, record in sorted(command_by_label.items())},
    "variant_results": variant_results,
}

row_path.write_text(json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
b7_path.parent.mkdir(parents=True, exist_ok=True)
b7_path.write_text(
    "\n".join(
        [
            "# Phase 6B Real-Provider L0 B7 Report",
            "",
            "Status: " + row["classification"],
            "",
            "## Claim Boundary",
            "",
            "This report covers Phase 6B L0 runtime sanity only. It does not approve Phase 6B, L1-L5, production/default enablement, or real capability beyond the observed L0 evidence.",
            "",
            "## Evidence Provenance",
            "",
            "The evidence row is generated from command logs and runtime artifacts. Provider reply text remains evidence only and does not write task or topology authority fields.",
            "",
            "## Script Harness",
            "",
            f"Script path: {script_path}",
            "",
            f"Script sha256: {script_sha256}",
            "",
            "## Evidence Row",
            "",
            "```json",
            json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Command Log",
            "",
            str(command_log_path),
            "",
        ]
    )
    + "\n",
    encoding="utf-8",
)
PY
```

Normalization rules:

- Inputs must come from command logs and runtime artifacts listed above.
- Ask reachability must be discovered from actual runtime ask/job artifacts,
  including dynamic-agent `.ccb/agents/*/jobs.jsonl` and ccbd job/message
  artifacts. The legacy `.ccb/runtime/asks.jsonl` index is optional evidence,
  not the only accepted source.
- Provider reply text is evidence only; it must not mutate authority fields.
- `runtime_residue.dynamic_agents_absent`,
  `runtime_residue.config_dynamic_agents_absent`, and
  `runtime_residue.observed_topology_residue_absent` must be explicit
  booleans in `phase6b_l0_b_only_repeat6_evidence_row.json`.
- `script_path`, `script_sha256`, `script_sha256_recorded`, and
  `script_sha256_matches` must be present in the evidence row and report.
- `classification=pass` requires required B-only artifacts, compact ask
  reachability for `p6bl0b-orchestrator`, clean B topology release, no authority
  violations, and matching script sha256 evidence. Runtime cleanup is clean when
  all residue booleans are true, or when the resident planning group release
  reports all expected agents in `drained_agents` with `parked_after_release`
  reasons and observed topology authority is absent.
- Former A command labels and p6bl0a artifacts are not expected and must not be
  classified as missing evidence for this B-only request.
- Missing command labels, missing runtime artifacts, malformed JSON/JSONL, or
  failed artifact reads become explicit `test_design_failure` evidence, not a
  normalizer crash.
- A failed compact ask with otherwise complete command/runtime evidence should
  classify as `provider_failure`, not pass and not provider-reply authority.
- If environment/provider behavior prevents pass but cleanup remains bounded
  and auditable, use `valid_non_success` with a diagnosis; do not mark L0
  `done` from provider reply text.

## Post-B7 External Cleanup Command

Status: FINAL CLEANUP SHAPE / DO NOT RUN UNTIL AFTER APPROVED L0 EXECUTION
AND B7 EVIDENCE CAPTURE.

The final cleanup is separate from pass-condition release evidence. It must use
the same lab-local `AGENT_ROLES_STORE` so the source wrapper resolves the
seeded RolePacks while unmounting the external project.

```bash
# DO NOT RUN until B7 evidence has been captured.
cd /home/bfly/yunwei/test_ccb2

export PHASE6B_L0_ROOT=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704
export PHASE6B_L0_PROJECT="$PHASE6B_L0_ROOT/l0-runtime-sanity"
export HOME="$PHASE6B_L0_ROOT/source_home"
export CCB_SOURCE_HOME="$PHASE6B_L0_ROOT/source_home"
export AGENT_ROLES_STORE="$PHASE6B_L0_ROOT/roles"

/home/bfly/yunwei/ccb_source/ccb_test --project "$PHASE6B_L0_PROJECT" kill
```

## Expected Evidence Files

Harness files under the proposed lab root:

```text
run_l0.sh
run_l0.sh.sha256
```

Runtime files under the proposed project root:

```text
.ccb/ccb.config
.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json
.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json
.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl
.ccb/runtime/loops/p6bl0b/topology_proposals/p6bl0b-plan.json
.ccb/runtime/asks.jsonl (optional legacy ask index)
.ccb/agents/*/jobs.jsonl
.ccb/ccbd/snapshots/job_*.json
.ccb/ccbd/messages/messages.jsonl
.ccb/ccbd/replies/replies.jsonl
.ccb/ccbd/mailboxes/*/inbox.jsonl
```

Report files:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_evidence_row.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/phase6b_l0_b_only_repeat6_command_log.jsonl
docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md
```

## Evidence Row Schema

The L0 row must include at least:

```json
{
  "task_id": "phase6b-l0-runtime-sanity",
  "complexity_level": "L0",
  "provider_mix": {
    "ccb_frontdesk": "codex",
    "ccb_planner": "codex",
    "ccb_orchestrator": "codex",
    "ccb_task_detailer": "codex",
    "ccb_round_reviewer": "claude",
    "coder": "codex",
    "code_reviewer": "codex"
  },
  "script_path": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704/run_l0.sh",
  "script_sha256": "<sha256>",
  "script_sha256_recorded": "<sha256>",
  "script_sha256_matches": true,
  "topology_variants": [
    "resident_planning_group"
  ],
  "ask_targets": {
    "resident_planning_group": "p6bl0b-orchestrator"
  },
  "ask_targets_logged": {
    "resident_planning_group": true
  },
  "ask_reachability_by_variant": {
    "resident_planning_group": true
  },
  "ask_evidence_paths": [
    ".ccb/agents/<mounted-agent>/jobs.jsonl"
  ],
  "expected_route": "runtime_sanity",
  "observed_route": "runtime_sanity",
  "route_decision_correct": true,
  "required_artifacts_present": true,
  "ask_reachability": true,
  "detailer_activated_expected": false,
  "detailer_activated_observed": false,
  "worker_reviewer_ask_success": null,
  "reviewer_contract_citation": null,
  "round_result": "not_applicable",
  "final_status": "ok",
  "cleanup_result": "released",
  "runtime_residue": {
    "dynamic_agents_absent": true,
    "config_dynamic_agents_absent": true,
    "observed_topology_residue_absent": true
  },
  "role_boundary_violations": [],
  "authority_write_violations": [],
  "classification": "pass",
  "human_diagnosis_summary": ""
}
```

For an approved run, `ask_reachability`, the `ask_targets_logged` field, and
all three `runtime_residue` fields must be explicit booleans, not `null`.
`script_sha256_matches` must also be an explicit boolean. `classification` may
be `valid_non_success`, `provider_failure`,
`system_failure`, or `test_design_failure` if evidence supports that result.

## B7 Report Shape

Proposed B-only repeat6 B7 report path:

```text
docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md
```

Required sections:

- status and claim boundary;
- approved lab root, source checkout, `ccb_test`, `HOME`,
  `CCB_SOURCE_HOME`, provider-home path, and `AGENT_ROLES_STORE`;
- provider profile map and inherited-provider-home risk decision;
- command sequence actually run, with return codes, command-log path, script
  path, and script sha256;
- L0 evidence row;
- artifact/runtime path table;
- authority audit: no topology communication DSL, no topology dispatch, no
  provider-reply authority parsing;
- cleanup/residue audit for process/status evidence, `.ccb/ccb.config`, and
  observed topology;
- failure taxonomy and human diagnosis;
- reviewer conclusion: L0 pass, valid non-success, or blocked.

## Stop Rule

No real-provider command may run again from this B-only repeat6 request. The
one approved repeat6 execution has already consumed the approval for root
`/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704`.
The one-run approvals from
`job_960ec614c477`, `job_f3adf3a31988`, `job_041526ab5f10`,
`job_90cc9a80d7a0`, `job_46d3377feb21`, `job_2953f5e7ab7e`,
`job_8c7b404ad63c`, and `job_c7ebe2d2dade` have all been consumed for their
approved scopes.

## Owner Decisions Recorded And Remaining Review Gates

Recorded owner decisions:

1. Provider map: `ccb_round_reviewer -> claude`; all other six roles ->
   `codex`.
2. Provider home/account policy: approved inherited current real provider home
   with external-root and source-home isolation.
3. RolePack seed scope: seven required roles only.
4. Topology scope: B-only resident planning group with only orchestrator asked.
5. Ask schema: `ask --compact p6bl0b-orchestrator`, 600 second timeout,
   runtime sanity prompt boundary.
6. B7 normalization owner: `talk2`; provider replies are evidence only.
7. Launch reviewer scope: approve Phase 6B L0 runtime sanity only.

Remaining gates before any further real-provider run:

1. Repeat6 L0 runtime sanity passed, but this does not approve L1-L5 or Phase
   6B completion. Any further L0 rerun or L1-L4 launch needs fresh
   launch-specific approval with a new frozen command packet.
2. The expected clean path is drained resident planning-group release evidence:
   all expected agents in `drained_agents` with every drain reason
   `parked_after_release`.
3. If release returns bounded `release_incomplete_agents` plus bounded
   `release_blockers`, B7 may classify the run as `valid_non_success`; missing,
   vague, or unbounded residue remains hard failure evidence.
4. Any future request after repeat6 must re-approve inherited-provider-home
   risk, mounted ask targets, proposal/agent ids, capacity policy, cleanup
   semantics, and B7 normalizer behavior.
8. Confirm no Phase 6B completion, L1-L5 approval, production/default
   enablement, or real capability claim is made.
