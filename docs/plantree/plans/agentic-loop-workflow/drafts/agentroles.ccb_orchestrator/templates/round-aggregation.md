# Round Aggregation

Historical filename retained for compatibility. This template is not used on
the normal post-worker path: controller-owned integration and
`ccb_round_reviewer` evidence replace orchestrator aggregation.

task id: <task-id>
loop id: <loop-id>
orchestrator: <agent-name>
aggregation result: complete|partial|blocked|replan_required

## Capacity Used

- profile: <worker|code_reviewer>
  agent: <returned agent name>
  state: <used|retained|released|blocked>

## Node Results

- node: <node-id>
  worker result: done|blocked|needs_rework
  checker result: pass|rework_required|blocked|non_converged
  dependency state: independent|blocks:<node-id>

## Release Summary

- released: <agents>
- retained: <agents and reason>

## Handoff To Round Checker

- task packet ref: <ref>
- verification ref: <ref>
- worker/checker refs: <refs>

Only a structural `replan_required` starts another immaculate orchestrator
activation. The orchestrator does not import this report or mutate authority.
