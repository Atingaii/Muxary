# CCB TUI Workbench Roadmap

Date: 2026-07-14
Status: Planning

## Done

- Registered a separate PlanTree root so workflow UI does not become part of
  the config editor or the optional rich file workbench.
- Frozen the first-window, two-region interaction, scoped clarification, and
  ccbd-client authority decisions.
- Audited the current topology ordering, Config V3 compilation, Rust sidebar
  stack, local socket client, ProjectView, submit, watch, cancel, and question
  import surfaces.

## In Progress

- Complete a ready-check of the proposed workbench projection and command API.
- Resolve the remaining lifecycle and retention questions in
  [open-questions.md](open-questions.md).

## Next

### Phase 1: Read-only projection contract

- Add a versioned `workbench_view` projection with revision/cursor semantics.
- Project conversation turns, top-level task queue, active workflow phases,
  interactions, verification, and task outputs from backend-owned stores.
- Prove that the projection does not require the client to scan `.ccb/runtime`
  or infer workflow truth from provider pane text.

Gate: deterministic snapshot/reducer tests cover restart, duplicate events,
out-of-order refresh, and one-active-task invariants.

### Phase 2: Standalone TUI and first-window topology

- Add a separate Rust binary behind `ccb tui`; do not reuse the existing
  `ccb-workbench` rich-tool binary name.
- Add the managed `client` topology kind and Config V3 workbench opt-in.
- Materialize `ccb-workbench` first, without a duplicate Sidebar; shift
  `ccb-user`, `ccb-plan`, and dynamic Agent windows after it.
- Keep Config V2 and generic `tool_windows` ordering unchanged.

Gate: tmux topology tests prove physical order, selected entry, pane identity,
reload behavior, no Agent identity, no ask target, and no duplicate Sidebar.

### Phase 3: Conversation and task creation

- Submit ordinary left-side messages to Frontdesk as `from_actor=user`.
- Treat the accepted structured Frontdesk-to-Planner handoff as the boundary
  that creates or queues a top-level workflow task.
- Preserve normal discussion, per-mode drafts, scroll position, and focus while
  the right panel updates.

Gate: one user message has one Frontdesk job and at most one Planner handoff;
provider replies are shown once and are recoverable after client restart.

### Phase 4: Clarification, status discussion, and result collection

- Add question-addressed interaction answer commands and task-scoped input
  mode on the left.
- Keep full status and results on the right; add explicit `discuss status` and
  `discuss result` references for Frontdesk.
- Add TaskOutputStore publication so user-facing results do not automatically
  re-enter an Agent conversation.

Gate: no answer can reach the wrong task or Agent; completion is not shown
until result collection and verification references are persisted.

### Phase 5: Serial queue and task controls

- Enforce one active top-level task and FIFO activation of queued tasks.
- Add task cancellation, bounded retry where workflow state permits it, and
  explicit queue inspection.
- Cancel the active backend task and release owned dynamic topology before
  activating the next queued task.

Gate: queue and cancellation survive ccbd/TUI restart, are idempotent, and do
not cancel unrelated jobs or provider sessions.

### Phase 6: Acceptance and rollout

- Run reducer, socket, topology, rendering, resize, CJK-width, and fake-provider
  workflow tests.
- Run final visible opened-project acceptance from
  `/home/bfly/yunwei/test_ccb2` with the source `ccb_test` wrapper and the
  project runtime discipline required by `AGENTS.md`.
- Validate Frontdesk discussion during execution, Detail clarification,
  completion/result discussion, cancellation, reconnect, and clean shutdown.
- Keep the workbench Config V3 opt-in until installed-candidate acceptance is
  repeatable; consider default-on for the Agentic Loop profile separately.

## Deferred

- More than one active top-level workflow lane.
- Queue drag/reorder and active-task preemption.
- Browser GUI and shared remote clients.
- Inline image, PDF, and full IDE-class diff rendering.
- Config V2 default workbench adoption.
- Automatic semantic routing of unaddressed text to a pending question.

## Readiness Blockers

- A versioned interaction-answer command does not yet exist.
- Current topology always appends generic tool windows after Agent windows.
- There is no single workbench projection or TaskOutputStore authority.
- TUI exit-versus-detach behavior and transcript retention remain unresolved.
