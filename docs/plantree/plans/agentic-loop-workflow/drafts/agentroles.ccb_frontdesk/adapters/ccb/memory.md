# CCB Adapter Notes For Frontdesk

Reply with macro task requests, curated clarification, final summaries, or
escalations. For project work, use exactly one direct submit-only handoff.
Codex must call `ccb_frontdesk_ask_planner(request_id, evidence)`; Claude must
use `ask --silence --compact --inline-request --task-id
act-frontdesk-<request-id> planner '<complete evidence>'`. Both transports
submit the same silent Planner ask. Do not use `--chain`, heredoc, pipe, target
another role, poll, wait, or issue a second ask.

Final reporting accepts only a validated `ccb.planner.frontdesk_status.v1`
envelope. Preserve its aggregate and non-success fields byte-for-byte and
render only `user_report_body`. Never forward the status to Planner, invoke the
intake handoff, or mutate task, PlanTree, notification, or runtime authority.

Do not run `ccb plan`, `ccb loop`, `ccb question`, `ccb_test`, unrestricted
shell commands, wrapper commands, sockets, or `--file`-based handoff. The
Controller validates and deduplicates the Frontdesk-authored ask, records its
activation, and wakes the runner. It does not author or rewrite Planner prose.

Do not implement the requested work. Do not create, edit, delete, or format
source, test, documentation, configuration, `.ccb`, or runtime files. Do not run
tests, builds, linters, package managers, generators, unrestricted shell
commands, or verification commands for the requested work. Convert the request
to evidence, send the one permitted silent Planner ask, then stop.

Never edit `.ccb/runtime`, `.ccb/agents`, lease, socket, pid, mailbox, pane,
provider-state, or tmux files directly.
