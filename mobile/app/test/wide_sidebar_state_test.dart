import 'package:ccb_mobile/features/project_home/wide_sidebar_state.dart';
import 'package:test/test.dart';

void main() {
  group('wide sidebar button transitions', () {
    test('collapse moves down one level and allCollapsed is stable', () {
      expect(
        collapseWideSidebarLevel(WideSidebarState.expanded),
        WideSidebarState.projectCollapsed,
      );
      expect(
        collapseWideSidebarLevel(WideSidebarState.projectCollapsed),
        WideSidebarState.allCollapsed,
      );
      expect(
        collapseWideSidebarLevel(WideSidebarState.allCollapsed),
        WideSidebarState.allCollapsed,
      );
    });

    test('expand moves up one level and expanded is stable', () {
      expect(
        expandWideSidebarLevel(WideSidebarState.allCollapsed),
        WideSidebarState.projectCollapsed,
      );
      expect(
        expandWideSidebarLevel(WideSidebarState.projectCollapsed),
        WideSidebarState.expanded,
      );
      expect(
        expandWideSidebarLevel(WideSidebarState.expanded),
        WideSidebarState.expanded,
      );
    });

    test('toggle expands from allCollapsed and collapses otherwise', () {
      expect(
        toggleWideSidebarLevel(WideSidebarState.allCollapsed),
        WideSidebarState.projectCollapsed,
      );
      expect(
        toggleWideSidebarLevel(WideSidebarState.projectCollapsed),
        WideSidebarState.allCollapsed,
      );
      expect(
        toggleWideSidebarLevel(WideSidebarState.expanded),
        WideSidebarState.projectCollapsed,
      );
    });
  });

  group('wide sidebar drag target', () {
    test('expanded uses inclusive left thresholds and clamps right', () {
      expect(
        wideSidebarTargetForDrag(WideSidebarState.expanded, -95.9),
        WideSidebarState.expanded,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.expanded, -96),
        WideSidebarState.projectCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.expanded, -259.9),
        WideSidebarState.projectCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.expanded, -260),
        WideSidebarState.allCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.expanded, 260),
        WideSidebarState.expanded,
      );
    });

    test('projectCollapsed snaps both directions at inclusive thresholds', () {
      expect(
        wideSidebarTargetForDrag(WideSidebarState.projectCollapsed, -95.9),
        WideSidebarState.projectCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.projectCollapsed, -96),
        WideSidebarState.allCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.projectCollapsed, 95.9),
        WideSidebarState.projectCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.projectCollapsed, 96),
        WideSidebarState.expanded,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.projectCollapsed, 260),
        WideSidebarState.expanded,
      );
    });

    test('allCollapsed uses inclusive right thresholds and clamps left', () {
      expect(
        wideSidebarTargetForDrag(WideSidebarState.allCollapsed, 95.9),
        WideSidebarState.allCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.allCollapsed, 96),
        WideSidebarState.projectCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.allCollapsed, 259.9),
        WideSidebarState.projectCollapsed,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.allCollapsed, 260),
        WideSidebarState.expanded,
      );
      expect(
        wideSidebarTargetForDrag(WideSidebarState.allCollapsed, -260),
        WideSidebarState.allCollapsed,
      );
    });
  });

  test('drag end resets delta and starts next drag from current state', () {
    final reset = endWideSidebarDrag(WideSidebarState.projectCollapsed);

    expect(reset.dragStartState, WideSidebarState.projectCollapsed);
    expect(reset.dragDelta, 0);
  });
}
