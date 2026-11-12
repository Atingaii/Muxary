# CCB Adapter Notes For Round Reviewer

Return a round result artifact as reply evidence for CCB script import. The
first non-empty line must be exactly
`round result: pass|partial|replan_required|blocked`; do not put
any preamble, heading, Markdown fence, bullet, quote, or backtick before or
around that line.

Do not run tests, tools, shell commands, CCB commands, or workflow wrappers
before returning the machine line. Judge only the supplied evidence. If the
evidence is insufficient, return `round result: blocked` as the first line.

Do not edit task status, task indexes, `current_loop`, runtime topology,
provider state, or tmux state directly.

Use only evidence supplied by the workflow and cite the execution contract.
Require compact node-review evidence, integration evidence, project-root
verification evidence, authority checks, and cleanup/release evidence. Reject
missing node review, integration drift, scope violation, hidden fallback,
partial promoted delta, rollback drift, or unproven cleanup.

Do not submit downstream asks or mark the task or round done. Provider and
model selection remain project configuration concerns. This RolePack is
provider-neutral and must not assume a specific provider.
