# Phase 6B L0 Owner Decision Packet

Date: 2026-07-04
Status: OWNER DECISIONS RECORDED / LAUNCH-REVIEW PENDING / DO NOT RUN

## Purpose

This packet records the owner decisions for the Phase 6B L0 launch request.
It is planning/readiness material only. It does not approve L0, does not claim
Phase 6B readiness, and must not be used as an execution instruction until a
launch-specific reviewer approves the final L0 request.

References:

- [Phase 6B L0 launch request](phase6b-l0-launch-request-20260704.md)
- [Phase 6B launch checklist](phase6b-real-provider-lab-launch-checklist.md)
- [Phase 6B task-pack catalog](phase6-real-provider-lab-task-packs.md)
- [Open questions](../open-questions.md)
- Reviewer2 acceptance for owner decision:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_28befb34936c-art_8f995baaa15d4a2e.txt`

## Decision Summary

| Area | Owner decision | Still pending before execution |
| :--- | :--- | :--- |
| Provider profile map | `ccb_round_reviewer -> claude`; all other L0 roles -> `codex`. | Launch reviewer accepts the map and any provider-specific limits. |
| Provider-home policy | Inherit the current real provider home, while still running only from the external lab root with isolated `HOME` and `CCB_SOURCE_HOME`. | Launch reviewer explicitly accepts inherited-provider-home risk. |
| RolePack seeding | Seed only the seven required roles; do not pre-seed `ccb_clarification_broker` or `ccb_plan_reviewer`. | Exact lab-local seed command/helper is approved. |
| L0 command/schema | Verify mount topology A then B; ask `ccb_orchestrator` with compact runtime-sanity prompt and 600 second timeout. | Exact setup/proposal files and command sequence are launch-review approved. |
| B7 evidence/reporting | `talk2` owns outer supervision and final normalization; provider replies remain evidence only. | Reviewer accepts the command/log/evidence collection shape. |

## Provider Profile Mapping

Do not infer these values from local developer state, existing credentials, or
old smoke examples. The owner-selected L0 provider profile map is:

| Role | L0/Lab function | Recommended class | Owner-selected profile |
| :--- | :--- | :--- | :--- |
| `ccb_frontdesk` | user-facing boundary for later L1-L5 lab stages | coordination / low-risk dialogue | `codex` |
| `ccb_planner` | macro planning and rehydration for later stages | planning / reasoning | `codex` |
| `ccb_orchestrator` | L0 ask reachability target | orchestration / reasoning | `codex` |
| `ccb_task_detailer` | detail route in later L3 lab stages | source-inspection / reasoning | `codex` |
| `ccb_round_reviewer` | round summary/review in later execution stages | review / reasoning | `claude` |
| `coder` | code/document execution worker in later direct routes | code execution | `codex` |
| `code_reviewer` | code/document execution reviewer in later direct routes | code review | `codex` |

The B7 `provider_mix` field must record this exact map. L0 asks only
`ccb_orchestrator`; `ccb_round_reviewer`, `coder`, and `code_reviewer` are
profile-mapped for lab consistency but are not expected to receive L0 asks.

## Provider Home And Account Policy

Owner decision:

```text
provider_home_mode=approved_inherited_current_real_provider_home
provider_home_root=<inherited from the approved launch environment>
```

Required isolation paths remain:

```text
HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/source_home
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/source_home
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/roles
```

Rationale: CCB has session isolation, and the run remains constrained to an
external project under `/home/bfly/yunwei/test_ccb2`.

Risk to preserve for review: inherited provider home may use existing
real-provider credentials, quota, and account/session state. The launch
reviewer must explicitly accept this risk before L0 runs. The B7 report must
record the actual provider-home/account evidence observed by `talk2`; this
packet does not infer provider credential paths from local state.

## Lab-Local RolePack Seeding

Owner decision: seed RolePacks into the lab-local store only, without
installing or mutating global/system CCB state. Seed only the seven required
roles for L0/L1 continuity.

Seed set:

```text
agentroles.ccb_frontdesk
agentroles.ccb_planner
agentroles.ccb_orchestrator
agentroles.ccb_task_detailer
agentroles.ccb_round_reviewer
agentroles.coder
agentroles.code_reviewer
```

Explicitly do not pre-seed for L0:

```text
agentroles.ccb_clarification_broker
agentroles.ccb_plan_reviewer
```

Source package roots:

```text
/home/bfly/yunwei/ccb_source/docs/plantree/plans/agentic-loop-workflow/drafts/<role-id>/
```

Proposed seed procedure shape, pending launch-review approval:

```text
1. Set AGENT_ROLES_STORE to the lab-local roles path.
2. Create AGENT_ROLES_STORE/installed/<role-id>/current/ for each approved
   role id.
3. Copy the source-tree role package directory into that current/ directory,
   preserving role.toml, README.md, memory.md, and any nested package files.
4. Write PHASE6B_L0_ROOT/rolepack_seed_manifest.json with source path,
   destination path, role id, and file list for each seeded role.
5. Do not call global role install/update commands.
6. Do not read or mutate installed/system CCB RolePack stores.
```

Launch-review decision required:

- approve the exact copy/helper command;
- decide whether the seed manifest is produced manually or by a helper script.

## L0 Command And Schema

Owner decisions now recorded:

```text
provider_home_mode=approved_inherited_current_real_provider_home
provider_profile_map={"ccb_frontdesk":"codex","ccb_planner":"codex","ccb_orchestrator":"codex","ccb_task_detailer":"codex","ccb_round_reviewer":"claude","coder":"codex","code_reviewer":"codex"}
rolepack_seed_scope=required_7_roles_only
topology_sequence=A_minimal_orchestrator_then_B_resident_planning_group
l0_ask_target=ccb_orchestrator
l0_ask_mode=compact
l0_ask_timeout_seconds=600
normalization_owner=talk2
```

Topology A:

```text
mount only: ccb_orchestrator
ask target: ccb_orchestrator
```

Topology B:

```text
mount only: ccb_frontdesk, ccb_planner, ccb_orchestrator, ccb_task_detailer
ask target: ccb_orchestrator
```

Both topology proposals must be mount-only:

- no `edges`, `gates`, `artifacts`, or `topology_dispatch.json`;
- no communication graph/DSL semantics;
- no provider-reply authority parsing.

The L0 ask prompt boundary is:

```text
Phase 6B L0 runtime sanity only. Reply with a short reachability acknowledgement. Do not change task status, topology, files, or plan state.
```

Launch-review pending:

- exact lab-local RolePack seed command/helper;
- exact `.ccb/ccb.config` writer shape;
- exact topology proposal file contents for A and B;
- exact command-log capture wrapper;
- exact B7 row/report normalization procedure.

L0 result rules:

- expected route is `runtime_sanity`;
- final status is `ok` only when ask reachability and cleanup residue checks
  are explicit; otherwise use a non-pass classification supported by evidence.

## B7 Evidence Row And Report Normalization

Owner decision: `talk2` owns outer supervision and final normalization from
command logs and runtime artifacts after the run. Provider replies must remain
evidence only and must not write authority fields.

Required output paths, pending launch-review confirmation:

```text
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/phase6b_l0_evidence_row.json
/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/phase6b_l0_command_log.jsonl
docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l0-b7-20260704.md
```

Collection shape pending launch-review approval:

- capture return code, stdout/stderr path, timestamp, and command label for
  each source-wrapper command;
- record topology proposal/desired/observed/events paths for A and B;
- record ask log/job evidence for the compact `ccb_orchestrator` ask;
- record release and residue checks for both topology variants;
- write row JSON and B7 Markdown after the run from script/checklist-owned
  evidence, not from provider-authored authority files.

Minimum L0 row fields:

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

Normalization rules:

- `route_decision_correct` is computed from `observed_route == expected_route`.
- For the proposed L0 runtime-sanity scope, expected placeholders are
  `detailer_activated_expected=false`, `detailer_activated_observed=false`,
  `worker_reviewer_ask_success=null`, and
  `reviewer_contract_citation=null` unless the owner approves a broader L0
  scope before launch review.
- `runtime_residue.dynamic_agents_absent`,
  `runtime_residue.config_dynamic_agents_absent`, and
  `runtime_residue.observed_topology_residue_absent` must be explicit
  booleans, not `null`.
- `classification=pass` requires ask reachability, required artifacts, clean
  release, no authority violations, and explicit residue booleans.
- `classification=valid_non_success` is allowed only when the environment or
  provider result is understood, bounded, and cleanup evidence is clean.

## Reviewer Launch Request Checklist

Before asking reviewer approval for L0, fill all items below:

- exact external lab root under `/home/bfly/yunwei/test_ccb2`;
- exact `HOME`, `CCB_SOURCE_HOME`, `AGENT_ROLES_STORE`, and provider-home
  paths;
- provider profile map for all seven mapped roles: six `codex`, one
  `ccb_round_reviewer -> claude`;
- inherited-provider-home policy and risk acceptance;
- seven-role RolePack seed set and exact lab-local seed procedure;
- exact `.ccb/ccb.config` provider/profile mapping procedure;
- exact mount-only topology proposal content for A and B;
- exact L0 compact ask command, 600 second timeout, and expected response
  boundary;
- exact evidence row JSON path, command log path, and B7 Markdown path;
- `talk2` normalizer procedure;
- stop conditions copied from the launch checklist;
- explicit request for L0 approval only, not Phase 6B or L1-L5 approval.

## Remaining Launch-Review Decisions

L0 remains blocked until a launch-specific reviewer accepts:

1. inherited-provider-home risk for the selected real-provider profiles;
2. the lab-local seven-role seed command/helper;
3. the project config writer and topology proposal writers for A and B;
4. the command-log and evidence collection wrapper;
5. the B7 row/report normalization procedure owned by `talk2`;
6. the launch request text for Phase 6B L0 only.
