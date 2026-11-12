# Implementation And Test Plan

Date: 2026-07-14
Status: Proposed

## Implementation Shape

Use a new Rust crate and binary, tentatively:

```text
tools/ccb-workbench-tui/
bin/ccb-workbench-tui
CLI entry: ccb tui
```

Do not add the conversation/workflow application to the existing
`tools/ccb-agent-sidebar/src/tui.rs`; that file already owns a compact sidebar
and has different layout and lifecycle responsibilities. Reuse or extract only
small stable transport, theme, and protocol pieces when duplication becomes
material. Avoid a broad shared-TUI refactor before the workbench slice passes.

The existing `ccb-workbench` name belongs to the optional Rich/Yazi/LazyVim
bundle and must not be repurposed.

## Expected Source Surfaces

Backend and protocol:

- ccbd service graph, handlers, socket client endpoints, and API models;
- conversation/workflow projection service and event cursor;
- interaction-answer service and TaskOutputStore;
- workflow queue/cancel/result transition commands;
- ProjectView client-window health projection.

Topology and config:

- Config V3 UI parsing and compiled project config;
- namespace topology plan, materialization, reload plan/apply, and supervision;
- layout/startup authoritative contracts.

Client and packaging:

- new Ratatui reducer, screens, widgets, input modes, and ccbd client;
- Rust workspace/build scripts and release artifact assembly;
- install/update smoke and generated executable links;
- CLI parser/router for `ccb tui` and managed launch arguments.

## Landing Slices

1. Freeze JSON fixtures and implement read-only backend projection.
2. Implement a read-only TUI against fake socket fixtures.
3. Add the Config V3 client window and prove first physical order.
4. Add normal Frontdesk conversation submission/reply recovery.
5. Add scoped clarification answer flow and separate draft buffers.
6. Add TaskOutputStore, result collection, and discussion references.
7. Add serial queue, cancellation, retry policy, and restart recovery.
8. Harden packaging, installer/update behavior, diagnostics, and visible
   real-provider acceptance.

Each slice updates this PlanTree and any affected authoritative runtime
contract. Do not combine first-window topology, new result authority, and all
interactive commands into one unreviewable change.

## Automated Test Matrix

| Layer | Required evidence |
| :--- | :--- |
| Model/reducer | Duplicate events, cursor gap, stale revision, one-active-task invariant, independent drafts. |
| Socket/API | Schema validation, idempotency keys, stale interaction rejection, redaction, local permissions. |
| Workflow | FIFO queue, clarification pause/resume, result-before-complete gate, cancellation cleanup. |
| Topology | Client first, Agents shifted, no client Agent identity, no duplicate Sidebar, V2 unchanged. |
| Reload/recovery | TUI restart, ccbd restart, missing window recovery, no task cancellation, no duplicate submission. |
| Rendering | `80x24`, `100x30`, `140x40`, long task ids/titles, CJK width, resize, mouse and keyboard parity. |
| Packaging | Linux/macOS supported artifacts, npm dry-run, source install/update smoke, executable resolution. |

Ratatui rendering tests should use `TestBackend` and assert stable regions,
focus, modal bounds, overflow behavior, and nonblank content rather than only
snapshotting decorative output.

## Visible Acceptance Scenarios

Final acceptance uses a real opened project under
`/home/bfly/yunwei/test_ccb2` and `/home/bfly/yunwei/ccb_source/ccb_test`:

1. Start an opted-in Config V3 project and observe workbench first, Frontdesk
   second, Planner third.
2. Continue normal Frontdesk discussion with no task panel focus theft.
3. Submit one executable request and observe one active task plus two later
   requests queued FIFO.
4. Open and fold workflow nodes while Agent windows remain independently
   inspectable.
5. Reach Detail clarification, answer by question id in the left composer, and
   return to the preserved normal draft.
6. Observe internal status only on the right; discuss one selected node on the
   left through a stable reference.
7. Collect a complete result on the right, then discuss it on the left without
   copying raw logs into Frontdesk context.
8. Restart the TUI and ccbd separately; confirm state restoration and no
   duplicate task, answer, or result.
9. Cancel the active task; confirm owned dynamic topology releases before the
   next queued task activates.
10. Kill the project and verify no managed client, Agent, socket, or helper
    residue remains.

## Rollout And Rollback

- First release is opt-in through Config V3.
- A failed workbench launch must leave Agent/backend operation diagnosable and
  recoverable; it must not silently fall back to a second state authority.
- Rollback disables the compiled client surface and restores `ccb-user` as the
  entry without converting or deleting workflow/task/result data.
- No default-on claim is allowed until installed-candidate visible acceptance
  is repeatable across Linux and macOS packaging lanes.
