# State, Command, And Result Contract

Date: 2026-07-14
Status: Proposed

## Authority Boundary

The TUI is a reducer and command client. It must not:

- scan provider panes to infer semantic progress;
- write task, question, PlanTree, or runtime JSON files directly;
- mark tasks complete based on a provider process becoming idle;
- decide which Agent receives an unaddressed clarification answer;
- keep the only copy of a conversation turn, queue action, or result.

Scripts and ccbd services own transition validation, persistence, queue
activation, interaction routing, cancellation, result collection, and dynamic
topology release.

## Workbench Snapshot

Proposed read endpoint:

```text
workbench_view(schema_version=1, after_cursor?, conversation_limit?)
```

The response contains:

```text
project identity
revision and event cursor
connection/backend health
conversation turns and pending Frontdesk submissions
tasks[] and active_task_ids[]
workflow phase/node projection per task
interactions[] keyed by question_id
outputs[] keyed by task_id/result_id
unread and attention counters
```

V1 enforces `active_task_ids.length <= 1`, while retaining a list shape for a
future parallel scheduler. High-frequency state remains under CCB runtime
storage; only accepted semantic workflow updates enter PlanTree documents.

## Event Vocabulary

The projection reducer should understand at least:

```text
conversation_submitted
conversation_reply_published
task_created
task_queued
task_activated
workflow_phase_changed
workflow_node_changed
interaction_required
interaction_answered
output_published
result_collected
task_cancel_requested
task_cancelled
task_completed
task_failed
```

Events carry stable ids and revisions. Replaying the same event is idempotent;
a cursor gap or revision mismatch triggers a fresh snapshot.

Polling a revisioned snapshot is acceptable for the first slice. A bounded
long-poll/watch endpoint may follow after the state contract is stable.

## Command Surface

Proposed commands are narrow rather than one free-form privileged endpoint:

```text
workbench_conversation_submit(body, client_request_id)
workbench_interaction_answer(task_id, question_id, answer, expected_revision)
workbench_task_cancel(task_id, expected_revision)
workbench_task_retry(task_id, failed_node_id?, expected_revision)
workbench_result_discuss(task_id, result_id)
workbench_status_discuss(task_id, node_id, observed_revision)
```

Conversation submission uses `from_actor=user` and the configured Frontdesk
entry. It reuses dispatcher submission and visible-reply authority rather than
creating a second provider transport.

Mutating commands require a `client_request_id` or expected revision so a TUI
retry cannot duplicate a message, answer a resolved question, or cancel the
wrong task generation.

## Clarification Routing

An interaction record minimally contains:

```text
interaction_id
loop_id
task_id
question_id
kind = macro_clarification | task_detail_clarification
source_role
status = pending | answered | resolved | superseded
question_ref
created_at / updated_at
```

The answer command validates that the interaction is still pending and that
the task generation matches. Macro clarification continues through its
broker/planner route. Task-local clarification returns to the indicated
TaskDetailer activation. The TUI presents one interaction model but does not
collapse those backend routes.

## Output And Result Routing

Three result intents remain distinct:

- `chain`: return to a calling Agent because its current task depends on the
  child result;
- `publish`: persist in TaskOutputStore and display in the workflow/result
  panel without Agent reinjection;
- `silent`: retain operational evidence without a normal user-facing success
  message.

TaskOutputStore records include result id, task id, kind, summary, body or body
artifact, verification state, artifact references, producer, timestamps, and
content digest. Large bodies remain artifact-backed.

`task_completed` may be published only after `result_collected`. The left-side
discussion action submits a stable result/status reference and bounded summary
to Frontdesk; it never copies raw logs into long-lived context automatically.

## Recovery And Privacy

- The TUI persists only local presentation preferences and unsent drafts.
- Authoritative conversation, task, interaction, and result state remains in
  backend stores.
- Socket responses follow existing local project-socket permissions and redact
  provider secrets, environment values, and unrestricted provider transcript
  content.
- Reconnect starts from the last cursor when valid and falls back to a complete
  bounded snapshot.
