# Dynamic Pane Shrink And Release Goal

## Goal

Define and later land safe dynamic agent exit behavior: when a dynamic agent is
released, CCB closes only that released agent's pane, compacts the remaining
running panes, removes empty overflow windows, and preserves all still-running
agent sessions.

## Scope

- Define shrink behavior from 6 panes down to 1 pane in one page.
- Define overflow window collapse, especially 7->6 and 8->7->6.
- Define busy release behavior: busy agents are retained and no pane is closed.
- Define placeholder smoke tests first, then live dynamic-agent tests.
- Keep remaining pane IDs and provider processes alive during compaction.

## Non-Goals

- Do not restart remaining agents to obtain a prettier layout.
- Do not use shrink as a broad `.ccb/ccb.config` reload mechanism.
- Do not allow arbitrary user drag/drop in this slice.
- Do not release static config-owned agents before dynamic capacity ownership is
  clearly separated from configured startup agents.

## Shrink Model

CCB maintains a logical ordered list per window class. On release:

```text
current_order = [a1, a2, a3, a4, a5, a6]
release a4
remaining_order = [a1, a2, a3, a5, a6]
target_layout = growth-1-6(remaining_order)
```

The layout is recalculated from the remaining ordered list, not from numeric
suffixes. That means a middle removal compacts the visual layout without
renaming agents or changing pane ownership.

Tail shrink sequence:

| After release | Remaining panes | Target layout |
| --- | --- | --- |
| 6->5 | `p1 p2 p3 p4 p5` | `p1, p3, p5; p2, p4` |
| 5->4 | `p1 p2 p3 p4` | `p1, p3; p2, p4` |
| 4->3 | `p1 p2 p3` | `p1, p3; p2` |
| 3->2 | `p1 p2` | `p1; p2` |
| 2->1 | `p1` | `p1` |

## Release Safety Contract

Release must be guarded:

1. Resolve the target by CCB identity metadata, not by visible pane position.
2. Check ask/job/queue state.
3. If target is busy, mark `retained_busy` and do not close the pane.
4. If target is idle, request or record summary evidence when required.
5. Stop/unload only the target provider session.
6. Close only the target pane.
7. Compact remaining panes without killing or respawning them.
8. Update layout/runtime state after tmux operation succeeds.
9. Remove an empty overflow window only after all panes in it are released.

The remaining panes may be resized or moved within the same window, but their
pane IDs, provider sessions, and CCB slot metadata must remain valid.

## Testing Plan

### Planner Tests

- Build target layouts for tail shrink: 6->5->4->3->2->1.
- Build target layouts for middle/head removal from six panes.
- Verify overflow collapse:
  - 8->7 keeps `frontdesk-dialog-2` with one pane.
  - 7->6 removes `frontdesk-dialog-2`.

### Placeholder Tmux Smoke

- Create six placeholder panes, remove one pane at a time from tail to one.
- Observe that only the target pane disappears.
- Observe remaining pane titles and pane counts after each compaction.
- Create eight panes, remove panes until page two becomes empty, then remove
  the empty overflow window.

### Live Dynamic-Agent Smoke

- Ensure dynamic `worker + checker` agents.
- Release an idle dynamic checker; remaining worker stays mounted and askable.
- Attempt release of a busy worker; it is retained and layout does not change.
- After busy worker completes, release succeeds and compacts.

## First Landing Slice

1. Add shrink planner logic over ordered names.
2. Extend `ccb layout plan` to accept explicit names or removal candidates.
3. Add isolated placeholder shrink smoke.
4. Add read-only `layout status` against live tmux metadata.
5. Only after these pass, wire dynamic capacity release to live pane cleanup.

## Landed Evidence

- Placeholder/fake-agent dynamic smoke now exercises continuous grow and shrink
  in one isolated tmux session:
  `ccb layout dynamic-smoke --panes 6 --window-prefix frontdesk-dialog --json`.
- The single-page run observed `1,2,3,4,5,6,5,4,3,2,1`, with all retained
  panes alive at each step and cleanup successful.
- The paging run
  `ccb layout dynamic-smoke --panes 8 --window-prefix frontdesk-dialog --json`
  observed `1,2,3,4,5,6,7,8,7,6,5,4,3,2,1`; it created
  `frontdesk-dialog-2` at page overflow and removed that page when shrinking
  back to six.
- Live fake-provider release evidence now covers both default and explicit
  workflow windows:
  - same-window middle removal in `main` preserves surviving dynamic panes and
    reports `namespace_reflowed_windows=["main"]`;
  - explicit `--window-class plan-orchestrate` middle removal preserves the
    static `planner`, leaves `main=[frontdesk]` unchanged, removes only
    `planner_helper2`, reports
    `namespace_reflowed_windows=["plan-orchestrate"]`, and keeps surviving
    helpers askable.
- Guarded Codex real-provider evidence now covers explicit workflow-window
  middle release:
  - `frontdesk` and `planner` Codex panes started in explicit `[windows]`;
  - `planner_helper1/2/3` hot-loaded into `plan-orchestrate`;
  - unloading middle `planner_helper2` removed only that dynamic agent,
    reflowed `plan-orchestrate`, preserved surviving helper panes, and kept
    asks to the survivors accepted.
- Guarded Claude real-provider evidence now covers the same explicit
  workflow-window middle release:
  - `frontdesk` and `planner` Claude panes started in explicit `[windows]`;
  - `planner_helper1/2/3` hot-loaded into `plan-orchestrate`;
  - unloading middle `planner_helper2` removed only that dynamic agent,
    reflowed `plan-orchestrate`, preserved surviving helper panes, kept asks
    to the survivors accepted, and final cleanup unmounted the test project.
- `layout status --json` now exposes ownership/apply diagnostics for each
  agent record: static configured panes, dynamic session helpers, loop capacity
  agents, parked/dispatch-disabled nodes, and failed apply attempts can be
  distinguished without reading raw lifecycle files.
- `ccb agent status --json` and `ccb agent show --json` now mirror the same
  ownership/apply diagnostics for configured and dynamic lifecycle records.
- The stable command vocabulary is now packaged as
  `dynamic-agent-lifecycle` in the orchestrator draft RolePack, with loop
  execution capacity still routed through `orchestrator-capacity`.
- The guarded provider smokes now have a standard repeated-`--provider`
  matrix entrypoint and have passed for Codex+Claude on `window-class`.
- The guarded provider matrix now also has a fixed wrapper entrypoint for
  release/local validation: `scripts/guarded_dynamic_layout_provider_smoke.py`.
- Startup diagnostics now use the same pane identity vocabulary as
  `layout status`: non-interactive `ccb` start output includes compact
  `layout_window` and `layout_agent` lines with `ownership_class`,
  `dispatch_state`, `pane_id`, `pane_identity_source`, runtime state, and apply
  status, while diagnostic failure is surfaced as
  `layout_summary_status: unavailable` without failing an otherwise successful
  start.
- The guarded provider wrapper is now part of the default `Tests` workflow as
  a prepare-only Ubuntu py3.11 gate. It verifies the Codex+Claude
  `window-class` wrapper contract without `--run`, so CI catches wrapper/config
  drift while real provider execution remains explicit.
- Mounted dynamic apply reports now include `pane_identity_report` under the
  `apply` payload for `ccb agent add/remove --json` and
  `ccb loop capacity ensure/release --json`. The report records added panes,
  removed panes, preserved before/after panes, reflowed windows, mounted
  agents, and unloaded agents from the reload transaction itself, so scripts
  can verify hot-load/hot-unload effects without immediately re-querying raw
  tmux state.
- `layout status --json` now exposes best-effort tmux pane geometry
  (`pane_index`, `pane_left`, `pane_top`, `pane_width`, and `pane_height`) for
  observed panes. Dynamic layout smokes use this metadata to prove same-window
  `1->6->1` and multi-window add/remove preserve observable agent pane
  geometry while excluding sidebar panes from agent layout counts.
- Append-only `add_agent` now performs the same best-effort window reflow and
  managed sidebar width sync as idle `remove_agent`, recording
  `namespace_reflowed_windows` / `namespace_reflow_errors`. The
  same-window continuous smoke asserts a minimum observed agent pane width so
  repeated hot-load splits cannot silently collapse later panes into unusable
  columns.
- Fully managed one-to-six agent windows now reflow to the fixed planner
  visual order (`p1,p3,p5` left and `p2,p4,p6` right) before falling back to
  tmux even compaction for unsupported shapes. Source-wrapper evidence in
  `/home/bfly/yunwei/test_ccb2/fixed-reflow-smoke.json` proved the six-agent
  same-window layout uses two columns while preserving pane IDs, and
  `/home/bfly/yunwei/test_ccb2/fixed-reflow-combined-smoke.json` kept the
  same-window and multi-window fake-provider flows green.
- Window-class overflow now has continuous fake-provider evidence:
  `/home/bfly/yunwei/test_ccb2/window-class-continuous-smoke.json` grows
  `plan-orchestrate` to a full first page, creates and appends to
  `plan-orchestrate-2`, verifies fixed columns on both pages, asks the overflow
  helper, unloads helpers in reverse order, and confirms the empty overflow
  page is removed. `/home/bfly/yunwei/test_ccb2/ci-combined-layout-smoke.json`
  proves the same guard can run with same-window `1->6->1` in one CI-style
  pass.
- The source-wrapper combined shrink/release proof now has direct artifact
  output. `/home/bfly/yunwei/test_ccb2/dynamic-layout-output-latest.json`
  was written by `scripts/dynamic_layout_smoke.py --output` and passed
  `same-window-continuous`, `multi-window-continuous`, and
  `window-class-continuous` together. It proves same-window `1->6->1`,
  explicit review-window add/remove back to a single `main` window, and
  `plan-orchestrate-2` overflow cleanup in one reusable JSON artifact.
