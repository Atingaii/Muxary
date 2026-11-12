# Common CCB Workflow Authority Rule

You may author semantic artifacts and recommend transitions.
You must not directly edit authoritative state: task indexes, task status,
current_loop, leases, locks, runtime capacity records, tmux pane/window state,
provider sessions, or `.ccb/runtime/loops` authority files.

Return semantic artifacts, readiness recommendations, and blocker reports as
reply content. Do not run CCB authority commands such as `ccb plan`, `ccb loop`,
`ccb question`, `ccb ask`, `ccb_test`, or wrapper scripts to create tasks,
import artifacts, change task status, start execution, or route work. The
supervisor/runner script imports or rejects your reply through hard constraints.
If an import is rejected, produce a corrected artifact or blocker report; do not
hand-edit state files or retry by mutating authority yourself.

The program kernel should stay simple and stable. Agents provide semantic
judgment, plans, checks, and human-readable artifacts. Scripts commit or reject
those artifacts through hard constraints.
