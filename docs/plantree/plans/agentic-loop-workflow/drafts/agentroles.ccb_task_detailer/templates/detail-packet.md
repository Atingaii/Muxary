## task-detail-design.md

# Task Detail Design

task id: <task-id>
detailer: <agent-name>

### Source Evidence

- <source path, test path, decision, or plan ref>

### Detailed Acceptance

- <acceptance item>

### Detailed Verification

- <verification command or deterministic check>

## brief-update-summary.md

# Brief Update Summary

global impact rationale: <compact rationale>
planner backfill evidence: <none or compact invariant/dependency/decision update>
planner action recommendation: <none|record_bounded_summary|replan_before_execution>

This reply is evidence only. The task detailer never dispatches workers,
writes import files, or mutates task authority. Its sole downstream action is
the versioned direct silent Planner ask for `planner_replan_required`.

Allowed contract: `global impact: none|bounded|macro`; use only the parser-
defined legal detail result, readiness, and global-impact combinations.

detail-packet.manifest.json:
```json
{
  "schema": "ccb.detail_packet_manifest.v1",
  "detail_result": "local_detail_ready",
  "readiness": "detail_ready",
  "global_impact": "none"
}
```
