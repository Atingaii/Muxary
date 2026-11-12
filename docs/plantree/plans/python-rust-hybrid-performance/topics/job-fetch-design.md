# Job Fetch Design

Date: 2026-06-15

## Problem

The current broad helper experiments used a conservative tail budget:

```text
agents * tail
```

For stress tests this became `128 * 128 = 16384` rows. In typical user
projects the agent count is usually below 10, but `tail=128` is still a
bottom-layer data access choice, not a user-facing need. With 10 agents it
still returns up to `1280` summaries even when the UI only needs a recent list,
counts, or a small visible window.

The root issue is API semantics:

- `list_agent_tails_batch` means "return N rows per agent".
- Most production consumers mean "return the newest useful items", "return
  changes since last refresh", "return counts", or "return one job detail".

The old `tail=128` budget existed as a safety catch-all: it made sparse
terminal-status histories less likely to disappear from ProjectView/comms
without requiring per-agent state. That is a reasonable diagnostic fallback,
but it is too blunt as a production refresh contract.

Rust should own bounded scanning/filtering/aggregation. It should not be used
to ship a large tail matrix back to Python unless the caller explicitly asks
for a debug/audit export.

## Fetch Classes

### Recent List

Use for ProjectView/comms/sidebar recent jobs.

Contract:

- scan multiple agent job JSONL files;
- filter by status/message/source/time if requested;
- dedupe by `job_id`;
- globally sort by `updated_at`;
- return only top `result_limit` summaries.

Default budgets:

- `result_limit`: `32` or `64`;
- `per_agent_initial`: `ceil(result_limit / agent_count) * 2`, clamped to
  `8..32`;
- `per_agent_max`: `64` for normal UI, `128` only for explicit diagnostics.

Adaptive deepening:

1. Scan `per_agent_initial` per agent.
2. Filter, dedupe, sort, and check whether enough rows were found.
3. If not enough, deepen only agents that reached their scan limit and have not
   reached `per_agent_max`.
4. Stop when `result_limit` is satisfied or all agents hit `per_agent_max`.

This keeps the typical 10-agent case around tens or low hundreds of rows
scanned per refresh, while still recovering sparse terminal-status histories.

Implementation target:

- replace `lib/ccbd/project_view/service.py` fixed
  `_RECENT_JOB_SCAN_LIMIT_PER_AGENT = 128` with an adaptive budget helper;
- keep `JobStore.list_project_view_recent_jobs` result-limited and status-aware;
- avoid exposing `per_agent_limit` as the primary call-site meaning once
  `jobs.query.recent` exists;
- use `jobs.tail.summary` only for benchmark/debug comparisons.

### Delta Refresh

Use for high-frequency sidebar/project view refresh.

Contract:

- caller passes per-agent cursor;
- helper returns rows after the cursor and next cursor;
- optional fallback to recent-list scan when cursor state is missing or stale.

Cursor shape should be implementation-driven:

- line number plus file size/mtime for simple JSONL files; or
- byte offset if tail readers grow offset support later.

Returned payload must be bounded by `result_limit` or `max_new_rows`.

### Counts And Buckets

Use for dashboards and status badges.

Contract:

- scan recent or since-cursor rows;
- return counts by status/provider/agent;
- optionally return newest timestamp per bucket.

No job bodies or request payloads should cross the helper boundary.

### Detail On Demand

Use when the user expands one job or asks for an exact record.

Contract:

- input: `agent_name` and `job_id`;
- output: one full job record or a detail projection.

This avoids returning full JobRecord data for every list row.

### Debug Tail Matrix

Use only for explicit diagnostics.

Contract:

- keep `agents * tail` behavior;
- keep Python path or helper path opt-in;
- do not default-enable for UI refresh.

## Recommended Next Capability

Add a new capability rather than expanding `jobs.tail.summary`:

```text
jobs.query.recent
```

Input:

```json
{
  "requests": [
    {"id": "agent1", "path": "..."}
  ],
  "result_limit": 64,
  "per_agent_initial": 16,
  "per_agent_max": 64,
  "statuses": ["completed", "failed", "cancelled", "incomplete"],
  "updated_after": null,
  "dedupe_by_job_id": true,
  "body_preview_chars": 160
}
```

Output:

```json
{
  "jobs": [
    {
      "job_id": "job-1",
      "agent_name": "agent1",
      "status": "completed",
      "updated_at": "2026-06-15T00:00:00Z",
      "body_preview": "..."
    }
  ],
  "scanned": 140,
  "returned": 64,
  "truncated": false,
  "next_budget_hint": {
    "per_agent_initial": 16,
    "per_agent_max": 64
  }
}
```

## Rollout

1. Keep `project_view.recent_jobs` as the fixed-budget compatibility path.
2. Replace fixed `tail=128` in ProjectView/comms with adaptive budget inputs.
   Status: landed for the primary `JobStore.list_project_view_recent_jobs`
   path.
3. Add `jobs.query.recent` only after the adaptive budget contract is tested
   against typical 3/5/10-agent fixtures and sparse-history fixtures.
   Status: landed as a required/experimental helper path; not default-enabled
   because adaptive Python is faster on the 10-agent fixture.
4. Keep `jobs.tail.summary` non-default as a benchmark/debug contract.
5. Add cursor-based delta refresh after recent-list semantics are stable.

## Acceptance

- Typical 10-agent fixture:
  - returned rows no more than `result_limit`;
  - p95 at least 20% lower than Python for ProjectView/comms recent list;
  - parity with Python for sorting, status filtering, and dedupe.
- Sparse terminal-status fixture:
  - adaptive deepening finds enough matching terminal jobs without scanning
    every agent to max by default.
- Stress fixture:
  - 128-agent benchmark remains bounded by `result_limit` output and does not
    return `agents * tail`.
- Debug tail matrix remains available but explicitly non-default.
