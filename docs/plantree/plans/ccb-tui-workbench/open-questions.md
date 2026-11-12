# CCB TUI Workbench Open Questions

Date: 2026-07-14

Only unresolved choices belong here.

## Managed Exit Semantics

When the managed workbench receives an explicit quit command, should it detach
the current tmux client, leave a reconnect screen in the managed pane, or exit
the process and rely on bounded client-slot respawn? An unexpected crash must
be recoverable and must never cancel workflow work regardless of this choice.

## Conversation Retention

What bounded retention should the project conversation projection expose by
default, and when should older turns move behind an explicit history query?
The answer must preserve useful Frontdesk continuity without turning every TUI
refresh into an unbounded transcript scan.

## Large Result Viewing

Should the first slice include an internal read-only pager for large Markdown,
logs, and diffs, or open those artifacts through an external pager while the
right panel retains the result summary and references?

## Default Enablement

After opt-in Config V3 acceptance, should `agentic_loop_v1` make the workbench
default-on for new projects, or should it remain an explicit
`ui.workbench.enabled` choice for another release cycle? This does not block
the opt-in implementation.
