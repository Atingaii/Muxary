# Node Work Result

node id: <node-id>
workgroup id: <workgroup-id>
coder: <agent-name>
status: done|blocked|needs_rework
canonical node work packet: <ref>

## Assigned Boundary

- declared refs: <refs>
- allowed paths: <paths>
- dependency evidence: <refs or none>

## Work Performed

- <work item>

## Changed Paths

- <project-relative path or none>

## Verification Evidence

- command/check: <exact check>
- result: <exit/result and evidence ref>

## Blockers

- <none or blocker>

## Boundary Declaration

- scope expanded: no
- undeclared fallback or degradation: no
- workflow authority mutated: no
- assigned Reviewer chain outcome: <pass|blocked|non_converged>
- rework_required is bounded intermediate evidence, never a final Coder artifact outcome.
- unauthorized downstream asks submitted: no
