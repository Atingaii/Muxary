# Phase 1-6 P1 Dynamic Lifecycle Runbook

Date: 2026-07-08
Owner: talk2
Status: COMPLETE / PASS

## Purpose

P1 proves the runtime lifecycle surface that is not fully covered by the
sequence38 route-mix pass: repeated dynamic worker/reviewer unload, positive
busy-retain behavior, resident-role survival, visible UI/sidebar switching, and
observer timeout behavior in a real opened project.

This lane must be run directly by `talk2` from `/home/bfly/yunwei/test_ccb2`
with `/home/bfly/yunwei/ccb_source/ccb_test`. It must not use workers or
reviewers as validation authority.

## Baseline Dependency

P1 depends on the frozen P0 baseline:
[../history/phase1-6-deployment-readiness-p0-baseline-20260708.md](../history/phase1-6-deployment-readiness-p0-baseline-20260708.md).

Reject the run before start if:

- the proposed root already exists;
- the command would use bare `ccb_test`;
- role lookup would use `/home/bfly/.roles/installed`;
- the project would run under `ccb_source`;
- real-provider runs export lab-local `HOME` or `CCB_SOURCE_HOME`.

## Fresh Root Shape

Use a new root:

```text
/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-<timestamp>
```

Required local paths:

- project: `<root>/p1-dynamic-lifecycle-real-provider-lab`
- role store: `<root>/roles`
- command log: `<root>/p1-command-log.jsonl`
- B7/report: `<root>/p1-dynamic-lifecycle-b7.md`
- cleanup logs: `<root>/logs/*cleanup*`
- UI/sidebar evidence: `<root>/ui-evidence/`

Before `init` or start, the root must be absent. If the root exists, the lane
must choose a new suffix and record the consumed root as historical.

## Existing Harness Candidates

Existing lower-level scripts can be reused, but none is sufficient alone for
P1 deployment-readiness acceptance:

- `scripts/dynamic_layout_smoke.py`: useful for repeated dynamic layout,
  release, move, and multi-window flows; can run with `--provider-home-mode
  real-home`, but by itself does not prove frontdesk/resident workflow
  authority or P1 B7 rows.
- `scripts/reload_busy_drain_smoke.py`: useful for positive busy-retain and
  sidebar drain rendering with `--check-sidebar-render`; by itself it is a
  reload/drain smoke, not the whole opened-project workflow lane.
- `scripts/dynamic_agent_lifecycle_smoke.py`: useful for park/resume/release
  lifecycle policy, but it does not cover B7 row shape or observer timeout.
- `scripts/guarded_dynamic_layout_provider_smoke.py`: useful as a guarded
  provider matrix wrapper, but real execution requires explicit opt-in and
  still needs P1 evidence normalization.

P1 therefore needs an upper harness or manual supervisor sequence that invokes
the relevant lower-level checks, records root-local evidence, and writes the
P1 B7/report before cleanup.

## Cases

### P1-A. Repeated Direct Execution Release

Run two independent direct-execution tasks in the same fresh opened project.

Required evidence per task:

- route: `direct_execution`;
- final status: `done`;
- round result: `pass`;
- dynamic release: `released_count=2`, `retained_count=0`;
- observed topology after release: no active dynamic `loop-*` agents;
- `ps` after release shows only resident roles;
- provider reply authority parsing is absent;
- project-root artifacts/tests prove the worker changes were promoted before
  reviewer and round-reviewer validation.

Reject if cleanup removes residue that release should have reported.

### P1-B. Positive Busy Retain

Create a real active provider ask on a dynamic execution agent, then attempt a
release/reconcile while it is still busy.

Required evidence:

- release result is `retained_busy` or equivalent bounded non-success;
- busy agent is not killed;
- retained agent has a live ask/job reference;
- after the job reaches terminal/idle, the same agent releases cleanly;
- final observed topology and `ps` agree.

Reject if a busy agent is killed, hidden by cleanup, or classified as pass
without a bounded retained-busy record.

### P1-C. Resident Survival And UI/Sidebar Switching

After dynamic release and after busy-retain cleanup, verify resident roles
remain visible/reachable:

- `frontdesk`
- `planner`
- `orchestrator`
- `task_detailer`
- `ccb_round_reviewer`

Required evidence:

- project-local tmux/socket path belongs to the fresh root;
- sidebar/window switching can focus each resident role;
- no UI or tmux attachment points to `/home/bfly/yunwei/ccb_source`;
- screenshots or textual pane/sidebar snapshots are stored under
  `<root>/ui-evidence/`;
- at least one user-facing frontdesk pane is visible as the entry surface.

Reject if sidebar switching is asserted only in free text without project-local
evidence.

### P1-D. Observer Timeout Behavior

Run a provider task that naturally exceeds the old short timeout window and
prove it reaches terminal without being treated as failed only because it was
long-running.

Also run one explicit short diagnostic timeout case to prove configured timeout
still fails when requested.

Required evidence:

- default observer path has no premature timeout;
- terminal status is detected from provider/ask completion evidence;
- explicit diagnostic timeout records a timeout classification;
- no fake pass, route downgrade, or release skip occurs after timeout.

## B7 Row Requirements

Each row must include at least:

- `case_id`
- `expected_route`
- `observed_route`
- `route_decision_correct`
- `round_result`
- `final_status`
- `classification`
- `cleanup_result`
- `runtime_residue`
- `released_count`
- `retained_count`
- `observed_dynamic_agents`
- `resident_reachable`
- `ui_sidebar_evidence_path`
- `provider_reply_authority_parsing_absent`
- `raw_authority_paths`

Valid non-success is acceptable for the busy-retain-in-progress checkpoint,
but the final P1 report needs clean terminal release after the busy job drains.

## Completion Criteria

P1 is complete only when:

- P1-A has two clean direct-execution release rows;
- P1-B proves both retain-while-busy and release-after-idle;
- P1-C proves visible resident/UI/sidebar state from the fresh project;
- P1-D proves no default observer timeout and one explicit timeout diagnostic;
- B7 rows match raw task/loop/topology/ps/UI evidence;
- cleanup is logged and does not hide residue.

If any case exposes a source bug, stop P1, record the root as failure evidence,
and open a concrete source-fix task. Do not continue by weakening the test or
marking the row as pass.

## 2026-07-08 Completion

Talk2 executed P1 directly from `/home/bfly/yunwei/test_ccb2` against fresh
root
`/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320`.
The B7 report is
`/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/p1-dynamic-lifecycle-b7.md`
and returned `status: pass`.

Durable evidence is summarized in
[../history/phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md](../history/phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md).
