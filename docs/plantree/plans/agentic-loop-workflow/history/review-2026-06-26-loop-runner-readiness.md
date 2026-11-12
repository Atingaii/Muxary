# Loop Runner Readiness Review

Date: 2026-06-26

## Sources

- `reviewer1` reply artifact:
  `.ccb/ccbd/artifacts/text/completion-reply/job_17337939a263-art_542f7c545e0a4a0d.txt`
- `coworker` reply artifact:
  `.ccb/ccbd/artifacts/text/completion-reply/job_0398dfff549e-art_6ecbe7aa54d9475f.txt`

## Verdict

The workflow-loop design can proceed, but not directly to a long-running
daemon or full autonomous planner/execution cycle.

The next implementation slice should remove the manual bridge between a ready
task packet and one `ccb loop run-once` round:

```bash
ccb plan task-bind-loop
ccb plan task-import-round
ccb loop run-once --task-id
ccb loop runner --once
```

## Accepted Findings

- Round completion writeback is a consistency boundary. Loop runner must not
  activate planner or another round from a half-imported round report.
- `rework_node` needs a hard boundary. It is only valid for bounded fixes
  inside the current plan; otherwise the result must become `partial`,
  `replan_required`, or `global_blocker`.
- Script validation must check that agent-produced artifacts describe legal
  state transitions before updating task status.
- `current_loop` already exists conceptually, but the current implementation
  needs a command that writes it and clears it deterministically.
- First-class round artifact kinds are needed instead of storing every round
  checker reply as generic `completion`.
- A one-shot runner is the right V1 process model. A daemon, automatic planner
  activation, clarification routing, stale-lease automation, and multi-task
  parallelism should remain later slices.

## Required Next Slice

Minimum behavior:

1. Bind one ready task to one loop with per-task locking.
2. Run one execution round through `ccb loop run-once --task-id`.
3. Import the round checker result as one of:
   `round_pass`, `round_partial`, `round_replan`, or `round_blocker`.
4. Map round result to task status and clear `current_loop`.
5. Return `idle` when `ccb loop runner --once` finds no ready task.

## Deferred

- Long-running loop runner daemon.
- Planner auto-activation from `draft`, `partial`, or `replan_required`.
- `ccb question` clarification command family.
- Failure-signature dedup beyond simple counters.
- Multi-task or multi-plan parallel execution.
- Full lease/heartbeat recovery; V1 may start with per-task lock plus explicit
  stale-lease evidence.
