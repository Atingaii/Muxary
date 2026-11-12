round result: pass|partial|replan_required|blocked
task id: <task-id>
loop id: <loop-id>
round id: <round-id>

The `round result:` line above must be the first non-empty line of the reply.
Do not put any preamble before it. Do not wrap it in a Markdown fence, bullet,
quote, or backticks.
Do not run tests, tools, shell commands, CCB commands, or workflow wrappers
before this line. Judge only supplied evidence. If evidence is insufficient,
use `round result: blocked` as the first line.

## Evidence Reviewed

- planner verification contract: <ref>
- orchestration bundle: <ref and digest>
- compact node-review evidence: <one ref/result/tree digest per required node>
- integration evidence: <merge order, commit/digest, checks>
- project-root verification evidence: <promotion digest and checks>
- authority checks: <no provider authority mutation; no topology dispatch DSL>
- cleanup/release evidence: <released, retained, residue>

## Integrated Verification

- <check and result>

## Rejection Audit

- missing node review: <none or evidence>
- integration drift: <none or evidence>
- scope violation: <none or evidence>
- hidden fallback or degradation: <none or evidence>
- partial promoted delta: <none or evidence>
- rollback drift: <none or evidence>
- unproven cleanup or dynamic residue: <none or evidence>

## Next Recommendation

- <done, rework node, replan, escalate, or pause>

This reply is evidence only. The round reviewer cannot mark the task or round
done, import artifacts, release agents, or submit downstream asks.
