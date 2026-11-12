Input: validated `ccb.planner.frontdesk_status.v1` only
Preservation: retain every field below byte-for-byte; never mutate authority or forward this status
Rendering: render only `user_report_body` exactly as Planner supplied it
Schema: ccb.planner.frontdesk_status.v1
Notification identity: <stable-id>
Aggregate result: pass|partial|replan_required|blocked
Accepted scope:
- <accepted scope or none>
Unresolved scope:
- <unresolved scope or none>
Blockers:
- <blocker or none>
Next milestone:
- kind: selected|workflow_terminal|blocked_none
- ref: <stable milestone ref>
- rationale: <Planner-authored rationale>
Evidence refs:
- <stable ref>
User report body: <Planner-authored factual report rendered without reinterpretation>
