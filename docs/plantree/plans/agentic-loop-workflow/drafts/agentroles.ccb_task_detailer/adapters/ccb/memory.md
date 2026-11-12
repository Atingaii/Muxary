# CCB Adapter Notes For Task Detailer

Use reply-visible artifacts as the durable boundary. Prefer producing
`task-detail-design.md`, `brief-update-summary.md`, and one
`detail-packet.manifest.json:` literal-`json` fence for the supervisor/runner
to import or review. The manifest uses only `ccb.detail_packet_manifest.v1`;
Markdown packets, old labels, non-`json` fences, and mixed outcome fields are
not importable.

The brief update must include `global impact: none|bounded|macro`, its compact
rationale, and planner backfill evidence. The detail packet remains task-local.

Never run `ccb plan task-artifact`, `ccb plan task-status`, `ccb plan
task-create`, `ccb loop`, generic `ccb ask`, `ccb_test`, or wrapper commands
from the provider session. Those commands mutate or route authority and are
owned by the supervisor/runner script, not task_detailer. The sole managed
Planner handoff below is the only routing exception.

Never edit `.ccb/runtime`, `.ccb/agents`, `current_loop`, lease, socket, pid,
mailbox, pane, provider-state, or tmux state files directly. Do not write
supervisor import files into the project tree for later self-import.

Classify the result as exactly `local_detail_ready`,
`planner_replan_required`, `needs_clarification`, or `blocked`. Local detail
returns through script import to Orchestrator without a Planner ask.

For `planner_replan_required` only, author one
`ccb.detailer.replan_request.v1` body and send exactly one direct silent inline
ask to resident `planner`. Codex uses `ccb_task_detailer_replan_planner`;
Claude uses only the allowlisted `ask --silence --compact --inline-request
--task-id detailer-replan-<request-identity-prefix> planner '<exact JSON>'`
form. Do not add `--chain`, wait, watch, poll, target another agent, or submit a
second identity.

Never dispatch workers or submit any other downstream ask. Provider and model
selection remain project configuration concerns.
