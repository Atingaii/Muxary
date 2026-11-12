import 'package:flutter/material.dart';

import 'wide_sidebar_state.dart';

class WideSidebarDragHandle extends StatelessWidget {
  const WideSidebarDragHandle({
    required this.sidebarState,
    required this.onToggle,
    required this.onHorizontalDragStart,
    required this.onHorizontalDragUpdate,
    required this.onHorizontalDragEnd,
    super.key,
  });

  final WideSidebarState sidebarState;
  final VoidCallback onToggle;
  final GestureDragStartCallback onHorizontalDragStart;
  final GestureDragUpdateCallback onHorizontalDragUpdate;
  final GestureDragEndCallback onHorizontalDragEnd;

  @override
  Widget build(BuildContext context) {
    final colorScheme = Theme.of(context).colorScheme;
    final fullyCollapsed = sidebarState == WideSidebarState.allCollapsed;
    final label = switch (sidebarState) {
      WideSidebarState.expanded => 'Hide project sidebar',
      WideSidebarState.projectCollapsed => 'Hide agent sidebar',
      WideSidebarState.allCollapsed => 'Show agent sidebar',
    };
    final tooltip = switch (sidebarState) {
      WideSidebarState.expanded =>
        'Drag left to hide projects, keep dragging to hide agents, or tap to hide projects',
      WideSidebarState.projectCollapsed =>
        'Drag left to hide agents, right to show projects, or tap to hide agents',
      WideSidebarState.allCollapsed =>
        'Drag right to show agents, keep dragging to show projects, or tap to show agents',
    };
    return Semantics(
      button: true,
      label: label,
      child: GestureDetector(
        key: const ValueKey('wide-sidebar-drag-handle'),
        behavior: HitTestBehavior.opaque,
        onTap: onToggle,
        onHorizontalDragStart: onHorizontalDragStart,
        onHorizontalDragUpdate: onHorizontalDragUpdate,
        onHorizontalDragEnd: onHorizontalDragEnd,
        child: MouseRegion(
          cursor: SystemMouseCursors.resizeColumn,
          child: Tooltip(
            message: tooltip,
            child: SizedBox(
              width: fullyCollapsed ? 18 : 20,
              child: Center(
                child: Container(
                  width: 4,
                  height: 56,
                  decoration: BoxDecoration(
                    color: colorScheme.outlineVariant,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
