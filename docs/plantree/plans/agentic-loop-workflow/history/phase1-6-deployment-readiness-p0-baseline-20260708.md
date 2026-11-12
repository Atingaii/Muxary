# Phase 1-6 Deployment Readiness P0 Baseline

Date: 2026-07-08
Owner: talk2
Status: P0 baseline frozen for the next direct validation lanes

## Purpose

Freeze the current validation baseline before more production-readiness tests.
This prevents later evidence from silently mixing stale delegated-worker roots,
old artifacts, source-checkout runtime state, or the global role store.

This file is not a deployment-readiness pass. It is the baseline contract for
the next P1/P2/P3 runs.

## Source Baseline

- Source root: `/home/bfly/yunwei/ccb_source`
- Active branch at freeze time: `workflow/agentic-loop-topology`
- HEAD short id at freeze time: `f1bb7fd4`
- Source wrapper to use: `/home/bfly/yunwei/ccb_source/ccb_test`
- PATH `ccb_test` observed separately at freeze time:
  `/home/bfly/.local/share/codex-dual/ccb_test`
- Rule: production-readiness validation must call
  `/home/bfly/yunwei/ccb_source/ccb_test` explicitly, not bare `ccb_test`.

Current worktree is dirty. That is acceptable for source-lane validation, but
P5 packaging must resolve or consciously carry every changed file before any
release/update claim.

## Diagnostic Baseline

Command run from `/home/bfly/yunwei/test_ccb2`:

```bash
/home/bfly/yunwei/ccb_source/ccb_test --diagnose
```

Observed result:

```text
wrapper: /home/bfly/yunwei/ccb_source/ccb_test
source_ccb: /home/bfly/yunwei/ccb_source/ccb.py
cwd: /home/bfly/yunwei/test_ccb2
project_paths: <none>
default_roots: /home/bfly/yunwei/test_ccb2
env_CCB_TEST_ROOTS: <none>
env_CCB_SOURCE_ALLOWED_ROOTS: <none>
effective_roots: /home/bfly/yunwei/test_ccb2
checked_paths: /home/bfly/yunwei/test_ccb2
source_checkout_cwd: no
project_inside_source: no
allowed_source_test_project: yes
```

This confirms the next validation roots must live under
`/home/bfly/yunwei/test_ccb2`, not under the source checkout.

## Role Store Baseline

Global role store observed at `/home/bfly/.roles/installed`:

```text
agentroles.archi
agentroles.ccb_self
agentroles.coder
agentroles.frontend_engineer
agentroles.mobile_app_engineer
agentroles.mother
agentroles.open-design
```

The global store does not contain the full workflow role set such as
`agentroles.ccb_frontdesk`, `agentroles.ccb_planner`,
`agentroles.ccb_orchestrator`, `agentroles.ccb_task_detailer`,
`agentroles.ccb_round_reviewer`, or `agentroles.code_reviewer`.

Production-readiness runs must therefore use a root-local
`AGENT_ROLES_STORE` and must record the role installation path in the manifest.
If role lookup falls back to `/home/bfly/.roles/installed`, the run is rejected
for production-readiness evidence.

## Current Accepted Evidence Anchor

The latest direct talk2 route-mix pass remains:

- Root:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814`
- B7:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/phase6b-real-provider-l1-l4-sequence38-talk2-selfrun-20260708124814-b7.md`
- Manifest:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/phase6b_l1_l4_sequence38-talk2-selfrun-20260708124814_manifest.json`
- Command log:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/phase6b_l1_l4_sequence38-talk2-selfrun-20260708124814_command_log.jsonl`
- Cleanup logs:
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/logs/sequence38-talk2-selfrun-20260708124814__cleanup_after_b7.stdout`
  and
  `/home/bfly/yunwei/test_ccb2/deploy-l1-l4-frontdesk-sequence38-talk2-selfrun-20260708124814/logs/sequence38-talk2-selfrun-20260708124814__cleanup_after_b7.stderr`

The B7 status line is `Status: pass`. This covers the current L1-L4 route-mix
lane only. It does not close P1 dynamic lifecycle/busy-retain/UI/sidebar,
P2 frontdesk pressure, P3 six-module audit, P4 final report, or P5 packaging.

## Consumed Or Stale Roots

The following root patterns must not be reused for future acceptance evidence:

- Any `deploy-l1-l4-frontdesk-sequence*` root older than the next fresh talk2
  lane.
- Any worker-owned deployment root from 2026-07-07 or 2026-07-08.
- Any `manual-real-*` root created during UI/manual-open attempts.
- Any `phase6-real-*` historical Phase 6B launch root.

Runs may inspect these paths for diagnosis, but any new claim must use a fresh
root and a new B7/report path.

## Next Fresh Root Rules

P1 dynamic lifecycle roots should use a new talk2-owned prefix:

```text
/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-<timestamp>
```

P2 frontdesk pressure roots should use:

```text
/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-<timestamp>
```

Before `init` or start, the root must be absent. If the root exists, the lane
must choose a new suffix and record the consumed root as historical.

## Execution Policy For Next Lanes

- Run from `/home/bfly/yunwei/test_ccb2`.
- Use `/home/bfly/yunwei/ccb_source/ccb_test` explicitly.
- For real-provider validation, inherit system provider environment; do not
  export lab-local `HOME` or `CCB_SOURCE_HOME`.
- Use root-local `AGENT_ROLES_STORE`.
- Open or retain visible project evidence when the lane claims UI/sidebar or
  operator-observable behavior.
- Run B7/normalization before external cleanup.
- Cleanup must be logged, not assumed.

## Reject Conditions

Reject any later evidence if:

- it uses a reused root;
- it uses `ccb_source` as the runtime project;
- it relies on bare `ccb_test` from PATH;
- role lookup uses `/home/bfly/.roles/installed`;
- it starts from a supervisor-created route when the lane requires frontdesk
  intake;
- script rows contradict raw task/loop/ps/UI evidence;
- cleanup hides dynamic residue instead of reporting it.
