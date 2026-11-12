# Visible Three-Round Dynamic Window E2E

Date: 2026-07-10
Status: PASS WITH RECOVERED PROVIDER-SESSION DEFECT

## Scope

`talk2` directly ran an inspectable real-provider project from:

```text
/home/bfly/yunwei/test_ccb2/workflow-window-e2e-talk2-20260710-093408
```

The run used the workflow worktree `ccb_test`, inherited the system provider
environment, and used the project-local role store under `roles/`. The V2
project config statically mounted only `frontdesk:codex` in `ccb-user` and
`planner:codex` in `ccb-plan`. Orchestrator, round reviewer, coder, and code
reviewer capacity was dynamic.

## Visible Flow

The opened WezTerm/tmux project showed these states:

1. Idle: `ccb-user=[sidebar,frontdesk]` and
   `ccb-plan=[sidebar,planner]`.
2. Route activation: one immaculate Codex orchestrator was appended to
   `ccb-plan`, then removed after script-owned route import.
3. Direct execution: `ccb-exec` was created with sidebar, Codex coder, and
   Codex code reviewer. `ccb-plan` temporarily added a fresh Codex
   orchestrator and Claude `ccb_round_reviewer`.
4. Round completion: all four dynamic agents were unloaded, the empty
   `ccb-exec` window was removed, and the two resident panes remained visible.

No active window exceeded six panes. Three sequential planner tasks produced
three different loop ids and fresh pane ids; no execution pane was reused as
hidden persistent capacity.

## Task Evidence

| Task | Loop | Result | Release |
| :--- | :--- | :--- | :--- |
| `inventory-audit-cli` | `lp2dc427` | `done/pass` | 4 released, 0 retained |
| `inventory-audit-tests` | `lp433dc1` | `done/pass` | 4 released, 0 retained |
| `inventory-audit-readme` | `lpbb98de` | `done/pass` | 4 released, 0 retained |

The final product contains `inventory_audit.py`,
`tests/test_inventory_audit.py`, and the documented README workflow. Direct
supervisor verification passed 12 unit tests, human and JSON CLI success
output, task authority `3/3 done`, config validation, and final tmux state with
only the two resident agents.

## Defects Exposed And Repaired

1. Route activation assumed a statically configured `orchestrator` target.
   Commit `c845c8f2` now mounts orchestrator and task detailer activations
   dynamically and releases them after script-owned role-output import.
2. Claude execution permanently locked its log reader to the session captured
   before `/clear`. Commit `7a134400` keeps the exact initial binding for safe
   offset capture, then permits rotation only to a newer session in the same
   agent-local project namespace.
3. Claude session scanning read only the first JSONL entry for
   `isSidechain`. A new session beginning with a `summary` record was therefore
   treated as unknown and lost to an older normal session. Commit `df164fb1`
   scans the bounded metadata prelude for an explicit sidechain flag.

The second round intentionally retained the real failure trail. Two jobs were
marked `runtime_unavailable` when ccbd was restarted to load the fixes; retry
lineage used `continue`, selected the corrected session, emitted an observed
assistant text turn boundary, and allowed the original loop to finish and
release. The third round then completed through a newly cleared Claude session
without a daemon restart, proving the steady-state repair.

## Verification

- Dynamic activation/lifecycle/topology source suite: `208 passed`.
- Claude session, communication, parsing, polling, and execution suite:
  `92 passed`.
- Real project tests: `12 passed`.
- `ccb config validate`: valid, project config, default agents
  `frontdesk, planner`.
- All three observed loop topologies ended with `agents=[]`,
  `released_count=4`, and `retained_count=0`.
- Final visible tmux state: two windows, two agent panes, resident frontdesk
  and planner still alive.

## Boundaries

Frontdesk-to-planner handoff and planner task-set import were automatic. This
run deliberately invoked `loop runner --once` at supervisor checkpoints so
that route activation, execution windows, provider completion, restart
recovery, and release could be inspected between stages. It is strong visible
layout/lifecycle and multi-task evidence, but it does not replace the earlier
automatic frontdesk/auto-runner stress evidence.

The project remains mounted for operator inspection. This evidence does not
publish a release or enable dynamic workflow behavior by default.
