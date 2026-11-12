# agentroles.ccb_task_detailer

Draft accepted RolePack for immaculate task-local detail refinement.

The task detailer converts a macro task packet into a detailed execution packet
and supporting evidence. It also returns compact
`global impact: none|bounded|macro` and planner-backfill evidence. It never
dispatches workers, submits arbitrary asks, mutates authoritative task state,
runs CCB authority commands, writes supervisor import files, or rewrites
durable macro plans directly. Its only Decision 029 exception is exactly one
restricted direct silent Planner replan handoff when validated macro impact
requires it. That handoff targets only `planner`; arbitrary asks, `--chain`,
wait/watch, and every other target remain forbidden.
