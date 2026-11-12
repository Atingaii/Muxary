# agentroles.ccb_planner

Draft RolePack for the CCB workflow planner.

The planner owns semantic understanding and task-packet drafting. It does not
own authoritative task state, loop state, panes, provider sessions, or direct
user clarification. It emits artifacts that `plan_reviewer`, broker, and CCB
scripts can accept or reject.

Primary templates:

- `templates/task-packet.md`
- `templates/readiness.json`
- `templates/candidate-questions.jsonl`
