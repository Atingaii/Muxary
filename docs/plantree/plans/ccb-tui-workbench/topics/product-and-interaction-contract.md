# Product And Interaction Contract

Date: 2026-07-14
Status: Proposed

## Product Model

The workbench is one stable human-facing surface with two responsibilities:

```text
conversation anchor                  workflow drawer
normal Frontdesk discussion          queue and current task
scoped clarification input           phase and PlanTree projection
compact milestone notices            internal activity and verification
status/result discussion references  complete results and artifacts
```

The right side is not a second chat. It is the authoritative UI projection for
work state and outputs. The left side is not a log stream. It is the
conversation and user-input surface.

## Opening And Focus Rules

- With no workflow task, the conversation consumes the full window and a
  compact activity rail may remain visible.
- `task_created` or `task_queued` opens the right panel on wide terminals.
- Internal Planner retries or replans do not open, close, or recreate panels.
- Status refresh never steals input focus, destroys a draft, or forces scroll
  to the bottom. New off-screen events increment a visible unread counter.
- Folding the panel preserves selected task, selected node, expansion state,
  result scroll, and all input drafts.

## Responsive Layout

| Terminal width | Presentation |
| :--- | :--- |
| `>= 120` columns | Stable split, approximately 58% conversation and 42% workflow. |
| `90-119` columns | Conversation plus toggleable workflow drawer; no automatic focus transfer. |
| `< 90` columns | Full-screen `Conversation`, `Work`, and `Result` views using the same state and commands. |

Minimum acceptance sizes are `80x24`, `100x30`, and `140x40`. CJK text,
wrapping, selection, resize, and modal dimensions must be tested explicitly.

## Top-level Queue Contract

V1 has `scheduler_capacity = 1` at the top-level workflow lane:

```text
task A  active
task B  queued position 1
task C  queued position 2
```

- New accepted workflow tasks append FIFO.
- A queued task does not interrupt the active task.
- A task waiting for user clarification remains the active task and therefore
  blocks later tasks in strict serial V1.
- V1 does not support preemption, parking, or queue reordering.
- Existing one-task internal workgroup fanout remains visible as child nodes
  and does not violate the one-active-top-level-task rule.
- Active cancellation must settle owned jobs and topology before the next task
  activates.

## Workflow Panel Information Hierarchy

Always visible:

- task title/id, queue position, phase, elapsed time, and attention state;
- explicit phase progression rather than estimated percentage;
- the active node, known completed/total node count, and latest verification;
- unresolved user interaction;
- final result summary after collection.

Collapsed by default:

- complete PlanTree/workflow tree;
- internal ask flow and Agent assignment;
- event timeline, retries, and diagnostics;
- artifact and verification details.

The user may inspect or discuss any node, but raw execution noise must not be
copied into the left conversation automatically.

## Input Routing

Normal mode sends to Frontdesk. A selected unresolved interaction temporarily
changes the composer to a question-addressed mode:

```text
Answer task A / Detail q-003
```

The submission carries `loop_id`, `task_id`, and `question_id`. It is accepted
by the interaction service and routed by workflow authority. It is not a plain
ask to whichever Agent appears to be waiting.

Priority is deterministic:

1. An explicitly selected `question_id` receives the answer.
2. Otherwise the composer remains normal Frontdesk conversation.
3. Pending questions may be listed and selected, but free-form text is never
   semantically guessed to be an answer.
4. `New instruction` leaves the question pending and returns to Frontdesk.

Each normal and task-scoped input mode retains its own draft. Resolving the
question restores the previous Frontdesk draft and focus.

## Status And Result Routing

- Continuous status remains on the right.
- Major milestones may add one compact notice on the left.
- Blocking failures and clarification add a left-side attention entry.
- Full task results remain on the right.
- `Discuss status` inserts a stable workflow-node reference and compact
  snapshot into the left conversation.
- `Discuss result` inserts a result reference and summary, not the entire log
  or artifact body.

Task completion is visible only after the result collector has persisted the
result, verification status, and artifact references.

## Initial Command Set

| Action | Default key |
| :--- | :--- |
| Switch conversation/work focus | `F6` |
| Fold/unfold workflow panel | `F4` |
| Command palette | `Ctrl+K` |
| Create an explicit task request | `Ctrl+T` |
| Start a new Frontdesk instruction from clarification mode | `Ctrl+N` |
| Open selected task/question/result | `Enter` |
| Back or leave scoped interaction | `Esc` |
| Request active-task cancellation | `Ctrl+X`, followed by confirmation |

Key bindings must be represented as commands so mouse actions and future user
keymap configuration invoke the same validation path.
