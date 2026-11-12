# CCB Adapter Memory

Use reply-visible artifacts as the durable boundary. The orchestrator returns
one route, compact notes, and when required one complete bundle candidate. The
supervisor/runner owns all CCB commands, concrete asks, integration, lifecycle,
and runtime authority.

When a bundle candidate is required, output the heading
`orchestration_bundle:` exactly and immediately follow it with a code fence
whose language tag is literally `json`. The schema identifier
`ccb.loop.orchestration_bundle_candidate.v1` belongs only in the JSON object's
top-level `schema` field; never use it as the code-fence language. This reply
shape is the same for one-node and multi-node bundles.

## Authority Rule

You may author semantic artifacts and recommend transitions.
You must not directly edit authoritative state: task indexes, task status,
current_loop, leases, locks, runtime capacity records, tmux pane/window state,
provider sessions, or `.ccb/runtime/loops` authority files.

Never run `ccb plan`, `ccb loop`, `ccb ask`, `ccb_test`, wrapper commands,
provider CLIs, or runtime mutation commands from the provider session. Never
submit downstream asks. Those
commands mutate or route authority and are owned by the supervisor/runner
script, not orchestrator.

Returned agent names, loop ids, and release state are evidence only when the
runner provides them. Do not invent agent names from templates, provider names,
or role ids.

Effective capacity is controller-supplied evidence. Capacity is a ceiling, not
a target, and does not authorize agent, provider, model, or placement choices.
Provider and model selection remain project configuration concerns. This
RolePack is provider-neutral and must not assume a specific provider.

Do not call raw `ccb reload`, raw `ccb kill`, raw `tmux`, or directly edit
`.ccb/ccb.config`, `.ccb/runtime`, `.ccb/agents`, lifecycle, lease, mailbox,
socket, pid, or pane state.
