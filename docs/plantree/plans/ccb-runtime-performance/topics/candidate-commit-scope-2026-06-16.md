# Candidate Commit Scope

Date: 2026-06-16

## Purpose

Define the hunk-level scope for the first runtime-performance candidate commit.
The worktree contains unrelated and unaccepted changes, so file-level staging
is not safe for this slice.

## Include

### Lifecycle Profiling Harness

- `dev_tools/perf_runtime_lifecycle_profile.py`
- `test/test_perf_runtime_lifecycle_profile.py`

Include the source-runtime-safe defaults, project-cwd `ccb_test` invocation,
project-scoped process attribution, and regression tests.

### Detached Tmux Prepare Cache

- `lib/cli/services/runtime_launch_runtime/tmux_panes.py`
- `test/test_cli_runtime_launch_tmux_panes.py`

Include only the prepare-cache mechanics:

- `_PREPARED_DETACHED_TMUX_SERVER_KEYS`
- `_detached_tmux_server_prepare_key`
- `prepare_detached_tmux_server` cache lookup and success-only caching
- `best_effort_tmux_run` returning `bool`
- `_best_effort_tmux_environment_policy` returning `bool`
- tests for same socket reuse, different socket separation, environment
  refresh, and retry after failure

Do not include unrelated terminal/workbench environment key expansion or
`allow-passthrough` changes unless that work is selected separately.

### Focus Fast Path

- `lib/ccbd/project_focus/service.py`
- `test/test_ccbd_project_focus.py`

Include the cache invalidation plus optional `request_sidebar_refresh()` path
and fallback to existing synchronous sidebar refresh.

### Pending Sidebar Refresh Support

- `lib/ccbd/project_view/service.py`
- `lib/ccbd/metrics.py`
- `test/test_ccbd_project_view.py`

Include only the minimal support needed by the focus fast path:

- `ProjectViewService.request_sidebar_refresh`
- `_consume_sidebar_refresh_request`
- `_refresh_sidebar_panes`
- `_record_project_view_sidebar_refresh`
- `ControlPlaneMetrics` sidebar-refresh fields
- regression test for `request_sidebar_refresh()` followed by `build_response()`

Do not include the wider worker3 changes for tmux fact parsing, Rust parser
selection, recent-job scan budget changes, or extra project-view schema fields
unless they pass a separate review.

### Plan Evidence

- `docs/plantree/README.md`
- `docs/plantree/plans/ccb-runtime-performance/`
- `docs/plantree/plans/python-rust-hybrid-performance/implementation-status.md`

Include the plan root registration, lifecycle profile evidence, current status,
roadmap, and this scope note.

## Exclude

- Production Rust/helper entry points that need a separate risk/benefit gate:
  - `lib/jobs/store.py` helper paths behind `CCB_RUST_JSONL_STORE`,
    `CCB_RUST_PROJECT_VIEW_RECENT_JOBS`, and `CCB_RUST_JOB_SUMMARY_TAIL`
  - `lib/storage/jsonl_store.py` helper path behind `CCB_RUST_JSONL_STORE`
  - `lib/ccbd/project_view/service.py` helper parser path behind
    `CCB_RUST_PROJECT_VIEW`
- `lib/rust_helpers_project_view.py`
- `lib/rust_helpers_jsonl.py`
- `test/test_rust_helpers_project_view.py`
- `test/test_rust_helpers_jsonl.py`
- `dev_tools/perf_phase5_project_view_tmux_helper.py`
- `dev_tools/perf_phase2_jsonl_helper.py`
- `dev_tools/perf_phase6_jsonl_store_strict_helper.py`
- `dev_tools/perf_phase7_project_view_recent_jobs_helper.py`
- `dev_tools/perf_phase8_job_summary_projection_helper.py`
- `dev_tools/perf_results/python_rust_phase5_project_view_tmux_helper.json`
- `dev_tools/perf_results/python_rust_phase2_jsonl_helper.json`
- `dev_tools/perf_results/python_rust_phase6_jsonl_store_strict_helper.json`
- `dev_tools/perf_results/python_rust_phase7_project_view_recent_jobs_helper.json`
- `dev_tools/perf_results/python_rust_phase8_job_summary_projection_helper.json`
- Any unrelated README, install, namespace, layout, workbench, Windows, or
  provider-storage changes currently present in the worktree.

Rationale: the current lifecycle profile is dominated by shell/tmux/system
overhead rather than JSONL parsing or local tmux-output parsing. These helper
paths also add environment-gated production branches, required-helper failure
modes, and untracked wrapper/test artifacts. They should remain outside the
main performance branch until measured against the already-landed Python paths.

## Required Verification Before Commit

- `PYTHONPATH=lib python -m pytest -q test/test_perf_runtime_lifecycle_profile.py test/test_cli_runtime_launch_tmux_panes.py test/test_v2_runtime_launch.py test/test_ccbd_project_focus.py test/test_sidebar_click.py test/test_ccbd_project_view.py test/test_ccbd_service_graph.py`
- `git diff --check` on the selected hunk set
- From `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and
  `CCB_SOURCE_HOME`:
  `/home/bfly/yunwei/ccb_source/ccb_test --diagnose`
- From `/home/bfly/yunwei/test_ccb2` with isolated `HOME` and
  `CCB_SOURCE_HOME`:
  `/home/bfly/yunwei/ccb_source/ccb_test config validate`

## Current Risk

The accepted focus fast path depends on a minimal `ProjectViewService`
`request_sidebar_refresh()` implementation, but the current file also contains
larger worker3 edits. Commit packaging must use hunk-level staging or a clean
worktree reconstruction to avoid landing unreviewed project_view/Rust-helper
changes.
