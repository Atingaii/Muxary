# CCB Adapter Notes For Planner

Use reply-visible artifacts as the durable boundary. Prefer producing
`task-packet.md`, `readiness.json`, and `candidate-questions.jsonl` sections for
the supervisor/runner to import or review.

The active command surface is closed. Do not run shell commands, file searches,
file reads, tests, builds, or CCB commands from the provider session. Base your
reply on the Frontdesk-authored intake, compact artifacts, and prompt context.
Infer single-task versus task-set output from that intake: use task-set only
for explicit independent deliverables, distinct routes, or route-mix work.

When the prompt declares `detailer_replan` or `task_set_closure`, use the
`planner-closure-backfill` skill instead of the initial task-packet shape.
Return exactly one parser-stable `**planner-backfill.json**` fenced proposal.
Its `schema` is exactly `ccb.planner.backfill_proposal.v1`, its `mode` is the
exact declared activation mode, and it contains the complete structured
Frontdesk status envelope. The host validates the expected PlanTree revision
and performs every file write or Frontdesk delivery.

For `detailer_replan`, copy the controller authority, task identity and task
revision, and supplied Detailer macro-adjustment evidence exactly. Preserve
accepted facts, then return a complete replacement macro proposal that
invalidates the old orchestration semantics. Its mode must be exactly
`detailer_replan`; never emit `task_set_closure` for that activation.

For `task_set_closure`, the expected PlanTree revision is a digest-valued fence
and the mode is exactly `task_set_closure`. Retain the aggregate, closure, and
Frontdesk-status rules. Do not run wait/watch commands, notify Frontdesk, or
target any agent. The provider reply is evidence only.

For initial intake only (when neither backfill activation is declared), the
supervisor/runner imports exact `**task-packet.md**` and `**readiness.json**`
fenced sections. Do not use alternate section names, unfenced JSON, or
prose-only blocker summaries.

Never run `ccb plan task-create`, `ccb plan task-artifact`, `ccb plan
task-status`, `ccb plan breadcrumb`, `ccb loop`, `ccb ask`, `ccb_test`, or
wrapper commands from the provider session. Those commands mutate or route
authority and are owned by the supervisor/runner script, not planner.

Never edit `.ccb/runtime`, `.ccb/agents`, `current_loop`, lease, socket, pid,
mailbox, pane, provider-state, or tmux state files directly.
