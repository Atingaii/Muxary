# Phase 6B Real-Provider L0 B7 Report

Date: 2026-07-04
Status: valid_non_success / test_design_failure

## Claim Boundary

This report covers one approved Phase 6B L0 runtime-sanity attempt only. It does not approve Phase 6B, L1-L5, production/default enablement, or real-provider workflow capability.

## Launch Approval

- Static launch approval: `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_960ec614c477-art_e3692fee6841495a.txt`
- Approved scope: one run from `/home/bfly/yunwei/test_ccb2` using `/home/bfly/yunwei/ccb_source/ccb_test`.
- Lab root: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704`
- Project root: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity`
- Provider map: `ccb_round_reviewer -> claude`; all other six mapped roles -> `codex`.
- Provider home mode: inherited current real provider home, accepted for this L0 run by reviewer2.

## Result Summary

The L0 attempt did not pass. It is classified as `test_design_failure` because the frozen launch script was internally inconsistent with current runtime constraints:

- Variant A compact ask targeted ccb_orchestrator, but runtime ask target was phase6b-l0-ccb-orchestrator; ccb_test returned unknown agent.
- Variant B topology proposal used an invalid long proposal id; proposal was rejected before apply. The repeat request must keep both proposal and agent ids inside the accepted name regex.
- Approved normalizer could not handle the missing p6bl0b runtime proposal after proposal failure and raised FileNotFoundError.

No topology communication DSL was observed in the inspected proposal/desired/observed payloads, and no `topology_dispatch` artifact was found.

## Evidence Row

The approved inline normalizer crashed on the missing variant B runtime
proposal after proposal validation failed. The final row below was produced by
`talk2` supervisor fallback from command logs and runtime artifacts. It was not
derived from provider reply text and did not mutate authority fields.

```json
{
  "ask_reachability": false,
  "authority_write_violations": [],
  "classification": "test_design_failure",
  "cleanup_result": "release_incomplete",
  "command_returncodes": {
    "ask_a_orchestrator_compact": 1,
    "config_validate_after_a": 0,
    "config_validate_initial": 0,
    "diagnose": 0,
    "ps_a_after_ask": 0,
    "ps_a_after_release": 0,
    "start_project": 0,
    "topology_a_commit_apply": 0,
    "topology_a_propose": 0,
    "topology_a_release": 0,
    "topology_b_propose": 1
  },
  "complexity_level": "L0",
  "detailer_activated_expected": false,
  "detailer_activated_observed": false,
  "expected_route": "runtime_sanity",
  "final_status": "valid_non_success",
  "human_diagnosis_summary": "The approved L0 launch script reached topology A but used an unregistered ask target, then rejected topology B because the generated proposal id exceeded the CLI name limit. A release command returned 0, but post-release ps/config evidence still showed the dynamic A agent, so cleanup cannot be classified as clean.",
  "missing_command_labels": [
    "ask_b_orchestrator_compact",
    "config_validate_after_b",
    "ps_b_after_ask",
    "ps_b_after_release",
    "topology_b_commit_apply",
    "topology_b_release"
  ],
  "observed_route": "runtime_sanity",
  "provider_home_mode": "approved_inherited_current_real_provider_home",
  "provider_mix": {
    "ccb_frontdesk": "codex",
    "ccb_orchestrator": "codex",
    "ccb_planner": "codex",
    "ccb_round_reviewer": "claude",
    "ccb_task_detailer": "codex",
    "code_reviewer": "codex",
    "coder": "codex"
  },
  "required_artifacts_present": false,
  "reviewer_contract_citation": null,
  "role_boundary_violations": [],
  "round_result": "not_applicable",
  "route_decision_correct": true,
  "runtime_residue": {
    "config_dynamic_agents_absent": false,
    "dynamic_agents_absent": false,
    "observed_topology_residue_absent": false
  },
  "task_id": "phase6b-l0-runtime-sanity",
  "test_design_failures": [
    "Variant A compact ask targeted ccb_orchestrator, but runtime ask target was phase6b-l0-ccb-orchestrator; ccb_test returned unknown agent.",
    "Variant B topology proposal used an invalid long proposal id; proposal was rejected before apply.",
    "Approved normalizer could not handle the missing p6bl0b runtime proposal after proposal failure and raised FileNotFoundError."
  ],
  "topology_variants": [
    "minimal_orchestrator",
    "resident_planning_group"
  ],
  "variant_results": {
    "minimal_orchestrator": {
      "ask_returncode": 1,
      "ask_stderr": "command_status: failed\nerror: unknown agent: ccb_orchestrator",
      "commit_apply_returncode": 0,
      "post_release_ps_contains_dynamic_agent": true,
      "proposal_returncode": 0,
      "release_returncode": 0,
      "runtime_paths": {
        "desired": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.desired.json",
        "events": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.events.jsonl",
        "observed": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/agent_mount_topology.observed.json",
        "proposal": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0a/topology_proposals/phase6b-l0-minimal-orchestrator.json"
      }
    },
    "resident_planning_group": {
      "ask_returncode": null,
      "commit_apply_returncode": null,
      "proposal_returncode": 1,
      "proposal_stderr": "command_status: failed\nerror: proposal_id is invalid: agent name must match ^[a-zA-Z][a-zA-Z0-9_-]{0,31}$\nerror_cause: agent name must match ^[a-zA-Z][a-zA-Z0-9_-]{0,31}$",
      "runtime_paths": {
        "desired": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.desired.json",
        "events": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.events.jsonl",
        "observed": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/agent_mount_topology.observed.json",
        "proposal": "/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity/.ccb/runtime/loops/p6bl0b/topology_proposals/phase6b-l0-resident-planning-group.json"
      }
    }
  },
  "worker_reviewer_ask_success": null
}
```

## Command Log

Command log path: `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/phase6b_l0_command_log.jsonl`

| Label | Return Code | Stdout | Stderr |
| :--- | :--- | :--- | :--- |
| `diagnose` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/diagnose.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/diagnose.stderr` |
| `config_validate_initial` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/config_validate_initial.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/config_validate_initial.stderr` |
| `start_project` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/start_project.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/start_project.stderr` |
| `topology_a_propose` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_a_propose.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_a_propose.stderr` |
| `topology_a_commit_apply` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_a_commit_apply.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_a_commit_apply.stderr` |
| `ask_a_orchestrator_compact` | `1` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/ask_a_orchestrator_compact.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/ask_a_orchestrator_compact.stderr` |
| `ps_a_after_ask` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/ps_a_after_ask.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/ps_a_after_ask.stderr` |
| `topology_a_release` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_a_release.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_a_release.stderr` |
| `ps_a_after_release` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/ps_a_after_release.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/ps_a_after_release.stderr` |
| `config_validate_after_a` | `0` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/config_validate_after_a.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/config_validate_after_a.stderr` |
| `topology_b_propose` | `1` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_b_propose.stdout` | `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/topology_b_propose.stderr` |

## Variant A: Minimal Orchestrator

- `topology_a_propose`: `0`
- `topology_a_commit_apply`: `0`
- `ask_a_orchestrator_compact`: `1`
- Ask failure: `command_status: failed
error: unknown agent: ccb_orchestrator`
- `topology_a_release`: `0`
- `config_validate_after_a`: `0`
- Post-release `ps` still contains `phase6b-l0-ccb-orchestrator`: `True`
- Post-release config validation output still lists `phase6b-l0-ccb-orchestrator`: `True`

## Variant B: Resident Planning Group

- `topology_b_propose`: `1`
- Proposal failure: `command_status: failed
error: proposal_id is invalid: agent name must match ^[a-zA-Z][a-zA-Z0-9_-]{0,31}$
error_cause: agent name must match ^[a-zA-Z][a-zA-Z0-9_-]{0,31}$`
- Variant B did not reach commit/apply, ask, release, or post-release validation.

## Authority Audit

- Topology proposal A, desired A, observed A, and draft B were inspected for `edges`, `gates`, and `artifacts` keys.
- `topology_dispatch` path scan under the L0 project returned no files.
- Provider reply text did not mutate authority because the compact ask never reached a provider target.
- Authority write violations: `[]`

## Cleanup And Residue Audit

- A release command returned `0`, but runtime evidence is not clean because `ps_a_after_release` still lists `phase6b-l0-ccb-orchestrator`.
- B did not mount any dynamic agents because proposal validation failed before apply.
- Runtime residue booleans are intentionally explicit and non-pass:

```json
{
  "config_dynamic_agents_absent": false,
  "dynamic_agents_absent": false,
  "observed_topology_residue_absent": false
}
```

## Post-Run External Cleanup

After this B7 evidence was captured, `talk2` ran external-project cleanup with
the same lab-local role store:

```text
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/source_home
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/source_home
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/roles
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/l0-runtime-sanity kill
```

Cleanup result:

```text
kill_status: ok
state: unmounted
```

Logs:

- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/post_b7_kill_with_roles.stdout`
- `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-20260704/logs/post_b7_kill_with_roles.stderr`

This post-run cleanup does not change the L0 evidence classification above.
The attempted run remains `test_design_failure`.

## Follow-Up Required

Before any repeat L0 run, revise and re-review the launch request:

1. Use the actual mounted ask target (`phase6b-l0-ccb-orchestrator`) or configure a stable `ccb_orchestrator` ask target that exists.
2. Shorten B topology proposal and agent ids to satisfy `^[a-zA-Z][a-zA-Z0-9_-]{0,31}$`.
3. Make the B7 normalizer tolerate missing runtime artifacts after proposal/validation failures.
4. Define whether topology release is expected to unload, park, or merely mark absent; update cleanup assertions accordingly.
5. Use a fresh empty repeat lab root or make any root wipe explicit in the launch review.
6. Treat reviewer2 `job_960ec614c477` as consumed by this failed run; a repeat requires fresh launch-specific approval.
