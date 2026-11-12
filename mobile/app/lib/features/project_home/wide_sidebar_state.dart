const projectHomeWideLayoutBreakpoint = 900.0;
const projectHomeWideProjectColumnWidth = 300.0;
const projectHomeWideAgentColumnWidth = 220.0;
const projectHomeWideCollapsedSidebarWidth = 56.0;
const _wideSidebarDragFirstStopThreshold = 96.0;
const _wideSidebarDragSecondStopThreshold = 260.0;

enum WideSidebarState { expanded, projectCollapsed, allCollapsed }

WideSidebarState collapseWideSidebarLevel(WideSidebarState state) {
  return switch (state) {
    WideSidebarState.expanded => WideSidebarState.projectCollapsed,
    WideSidebarState.projectCollapsed => WideSidebarState.allCollapsed,
    WideSidebarState.allCollapsed => WideSidebarState.allCollapsed,
  };
}

WideSidebarState expandWideSidebarLevel(WideSidebarState state) {
  return switch (state) {
    WideSidebarState.expanded => WideSidebarState.expanded,
    WideSidebarState.projectCollapsed => WideSidebarState.expanded,
    WideSidebarState.allCollapsed => WideSidebarState.projectCollapsed,
  };
}

WideSidebarState toggleWideSidebarLevel(WideSidebarState state) {
  return state == WideSidebarState.allCollapsed
      ? expandWideSidebarLevel(state)
      : collapseWideSidebarLevel(state);
}

WideSidebarState wideSidebarTargetForDrag(
  WideSidebarState start,
  double delta,
) {
  final startLevel = _wideSidebarLevel(start);
  final offset =
      delta <= -_wideSidebarDragSecondStopThreshold
          ? 2
          : delta <= -_wideSidebarDragFirstStopThreshold
          ? 1
          : delta >= _wideSidebarDragSecondStopThreshold
          ? -2
          : delta >= _wideSidebarDragFirstStopThreshold
          ? -1
          : 0;
  return _wideSidebarStateForLevel((startLevel + offset).clamp(0, 2).toInt());
}

WideSidebarDragEndState endWideSidebarDrag(WideSidebarState currentState) {
  return WideSidebarDragEndState(dragStartState: currentState, dragDelta: 0);
}

class WideSidebarDragEndState {
  const WideSidebarDragEndState({
    required this.dragStartState,
    required this.dragDelta,
  });

  final WideSidebarState dragStartState;
  final double dragDelta;
}

int _wideSidebarLevel(WideSidebarState state) {
  return switch (state) {
    WideSidebarState.expanded => 0,
    WideSidebarState.projectCollapsed => 1,
    WideSidebarState.allCollapsed => 2,
  };
}

WideSidebarState _wideSidebarStateForLevel(int level) {
  return switch (level) {
    0 => WideSidebarState.expanded,
    1 => WideSidebarState.projectCollapsed,
    _ => WideSidebarState.allCollapsed,
  };
}
