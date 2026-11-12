# Dynamic Pane Growth Goal

## Goal

Land a small, testable CCB tmux layout capability that can grow a logical
workspace from one pane to multiple panes and then multiple windows without
changing the normal project startup path first.

## Scope

- Define the fixed pane growth order for 1 to 6 panes in one page.
- Define overflow pages as additional tmux windows after six panes.
- Add a scriptable layout planning surface for tests and future orchestrator
  integration.
- Add an isolated tmux smoke surface that can create placeholder panes in a
  dedicated test session.
- Validate from `/home/bfly/yunwei/test_ccb2` with the source `ccb_test`
  wrapper.

## Non-Goals

- Do not move live agent panes across windows in this slice.
- Do not alter ordinary `ccb` startup or existing `.ccb/ccb.config` semantics.
- Do not add arbitrary drag-and-drop layout editing.
- Do not launch real provider processes for pane growth verification.

## Fixed 1->6 Pane Growth

The first page holds at most six panes. Addition order alternates columns while
preserving early pane positions:

| Count | Layout intent | Layout spec |
| --- | --- | --- |
| 1 | one full pane | `p1` |
| 2 | left/right | `p1; p2` |
| 3 | left stacked, right full | `(p1, p3); p2` |
| 4 | two columns, two rows | `(p1, p3); (p2, p4)` |
| 5 | left three rows, right two rows | `(p1, p3, p5); (p2, p4)` |
| 6 | two columns, three rows | `(p1, p3, p5); (p2, p4, p6)` |

Overflow uses another window with the same 1->6 pattern:

- `frontdesk-dialog`: panes 1-6.
- `frontdesk-dialog-2`: panes 7-12.
- `frontdesk-dialog-3`: panes 13-18.

## Worker Landing Plan

1. Layout planner worker
   - Add deterministic layout planning code for 1->6 and overflow windows.
   - Add focused unit tests for rendered layout specs and page membership.

2. CLI smoke worker
   - Add a narrow `ccb layout plan` and `ccb layout smoke` surface.
   - Keep smoke isolated to a dedicated tmux socket/session under the test
     project.

3. Verification worker
   - Run unit tests first.
   - Run `/home/bfly/yunwei/ccb_source/ccb_test` from
     `/home/bfly/yunwei/test_ccb2` for 1, 2, 3, 4, 5, 6, and multi-window
     counts.
   - Confirm no normal source-project runtime state is touched.

## Acceptance Criteria

- `layout plan --panes N --json` reports deterministic windows and layout specs.
- `layout smoke --panes 1` creates exactly one pane in one window.
- `layout smoke --panes 6` creates one window with six panes.
- `layout smoke --panes 7` creates two windows, with six panes in the first
  window and one pane in the second.
- Smoke cleanup removes the dedicated tmux server/session.
- Tests cover 1->6 and overflow behavior.

## Landed Evidence

- `ccb layout dynamic-smoke --panes 6 --window-prefix frontdesk-dialog --json`
  passed from `/home/bfly/yunwei/test_ccb2` through source `ccb_test`.
  Observed counts: `1,2,3,4,5,6,5,4,3,2,1`; all retained panes stayed alive;
  cleanup succeeded.
- `ccb layout dynamic-smoke --panes 8 --window-prefix frontdesk-dialog --json`
  passed from `/home/bfly/yunwei/test_ccb2` through source `ccb_test`.
  Observed counts: `1,2,3,4,5,6,7,8,7,6,5,4,3,2,1`;
  8 panes produced `frontdesk-dialog` with six panes and
  `frontdesk-dialog-2` with two panes; shrink back to six removed the overflow
  page; cleanup succeeded.
