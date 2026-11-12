# Mother RolePack Design Review

Date: 2026-06-27

## Source

`mother` completed the RolePack design request for CCB agentic workflow roles.

- Job: `job_91c8cc2e374d`
- Reply: `rep_5a3c21688c97`
- Artifact:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_91c8cc2e374d-art_87dc4434f7c64b8b.txt`
- SHA256:
  `dce197536f7e207afc42b1aca70b5625753ed338874df169d5b94431a3aca955`

## Review Result

Accepted as the first Agent Roles spec handoff baseline, with one important
boundary: CCB command names, loop runner behavior, task locks, leases, tmux
layout, ask/callback mechanics, and runtime directory details must remain in a
CCB adapter layer, not in host-neutral core RolePack identity.

The report is aligned with the current workflow principle:

```text
scripts own hard authority
roles own semantic artifacts and recommendations
scripts commit or reject role outputs
```

## Accepted Priority Order

P0 complete RolePack design:

1. `agentroles.ccb_planner`
2. `agentroles.ccb_plan_reviewer`
3. `agentroles.ccb_clarification_broker`
4. `agentroles.ccb_orchestrator`
5. `agentroles.ccb_round_checker`

P1 simplified RolePack design:

1. `agentroles.ccb_frontdesk`
2. `agentroles.ccb_worker`
3. `agentroles.ccb_checker`

P2 boundary-only design:

1. `agentroles.ccb_risk_reviewer`
2. `agentroles.ccb_inner_monitor`
3. `agentroles.ccb_recovery`
4. `agentroles.ccb_plan_steward`
5. `agentroles.ccb_domain_researcher`
6. `agentroles.ccb_spec_checker`

## Accepted Common Rule

Every CCB workflow RolePack must carry a common authority rule:

```text
You may author semantic artifacts and recommend transitions.
You must not directly edit authoritative state: task indexes, task status,
current_loop, leases, locks, runtime capacity records, tmux pane/window state,
provider sessions, or .ccb/runtime/loops authority files.

Use CCB-owned commands or host-provided skill wrappers such as ccb plan,
ccb loop, and ccb question for authoritative writes. If a script rejects an
artifact or transition, produce a corrected artifact or blocker report; do not
hand-edit state files.
```

## Role-Specific Notes

- `ccb_planner`: should output task packet artifacts plus compact
  `readiness.json`; it must not talk directly to the user or mark task status.
- `ccb_plan_reviewer`: should reject vague acceptance, weak verification, and
  hidden fallback; it must not become a second full planner by default.
- `ccb_clarification_broker`: should filter, default, defer, or normalize
  questions; it must not directly ask the user or start execution.
- `ccb_orchestrator`: existing draft is directionally correct but needs
  stronger runner-router compatibility and stronger negative tests around
  runtime authority, fanout, and partial-to-done conversion.
- `ccb_round_checker`: must emit a standalone machine line:
  `round result: pass|rework_node|partial|replan_required|global_blocker`.
  Without that line, loop runner must not infer success from provider
  completion alone.
- `ccb_worker` and `ccb_checker`: can start as simplified reference roles
  because the worker/checker pattern is already widely understandable; the
  important boundary is no scope shrinkage and no hidden fallback acceptance.

## Host-Neutral Versus CCB Adapter Split

Host-neutral Agent Roles spec should contain:

- role identity and mission;
- authority and non-authority;
- generic skills and workflow steps;
- artifact schemas and templates;
- negative instructions;
- conformance prompts and smoke tests.

CCB adapter-specific material should contain:

- exact `ccb plan`, `ccb loop`, and `ccb question` command names;
- `loop runner --once` activation semantics;
- task lock, lease, `current_loop`, and runtime directory behavior;
- CCB `ask`, callback, and artifact-reply mechanics;
- capacity ensure/release and hot-load behavior;
- tmux, pane, provider-session, and rich/sidebar projection details.

## Landing Order

1. Add the common authority rule and shared artifact templates to the external
   Agent Roles spec baseline.
2. Materialize `ccb_planner` and `ccb_plan_reviewer`.
3. Materialize `ccb_round_checker`.
4. Tighten the existing `ccb_orchestrator` draft.
5. Add `ccb_clarification_broker`.
6. Add simplified `frontdesk`, `worker`, and `checker`.
7. Add conformance and negative smoke tests.
8. Defer monitor, recovery, risk, steward, researcher, and spec-checker roles
   until the V1 runner/router loop is stable.

## Follow-Up

The next planning or implementation step should be a concrete Agent Roles spec
handoff package for the P0 roles, not another broad role taxonomy.
