import 'package:flutter/material.dart';

import '../../models/ccb_agent.dart';
import '../../models/ccb_project_view.dart';

class WideCollapsedSidebarRail extends StatelessWidget {
  const WideCollapsedSidebarRail({
    required this.view,
    required this.selectedAgent,
    required this.onExpand,
    required this.onOpenNotifications,
    required this.onOpenConnectionDetails,
    super.key,
  });

  final CcbProjectView view;
  final CcbAgent? selectedAgent;
  final VoidCallback onExpand;
  final VoidCallback onOpenNotifications;
  final VoidCallback onOpenConnectionDetails;

  @override
  Widget build(BuildContext context) {
    final agent = selectedAgent;
    final colorScheme = Theme.of(context).colorScheme;
    return ColoredBox(
      key: const ValueKey('wide-collapsed-sidebar-rail'),
      color: Theme.of(context).colorScheme.surface,
      child: Column(
        children: [
          const SizedBox(height: 8),
          IconButton(
            key: const ValueKey('wide-sidebar-expand-action'),
            tooltip: 'Show agents',
            onPressed: onExpand,
            icon: Icon(Icons.auto_awesome_rounded, color: colorScheme.primary),
          ),
          IconButton(
            key: const ValueKey('notification-center-action'),
            tooltip: 'Notifications',
            onPressed: onOpenNotifications,
            icon: Icon(
              view.notifications.isEmpty
                  ? Icons.notifications_none
                  : Icons.notifications_active,
            ),
          ),
          IconButton(
            key: const ValueKey('connection-details-action'),
            tooltip: 'Diagnostics',
            onPressed: onOpenConnectionDetails,
            icon: const Icon(Icons.more_horiz),
          ),
          const Divider(height: 16),
          Tooltip(
            message: view.project.displayName,
            child: const Icon(Icons.terminal),
          ),
          const SizedBox(height: 16),
          if (agent != null)
            Tooltip(
              message: agent.name,
              child: Icon(
                agent.active
                    ? Icons.auto_awesome_rounded
                    : Icons.auto_awesome_outlined,
                size: 20,
                color:
                    agent.active
                        ? colorScheme.tertiary
                        : colorScheme.onSurfaceVariant,
              ),
            ),
          const Spacer(),
        ],
      ),
    );
  }
}
