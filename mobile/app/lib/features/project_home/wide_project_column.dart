import 'package:flutter/material.dart';

import '../../models/ccb_agent.dart';
import '../../models/ccb_project_view.dart';
import 'project_list.dart';

class WideProjectColumn extends StatelessWidget {
  const WideProjectColumn({
    required this.view,
    required this.selectedAgent,
    required this.onProjectSelected,
    required this.onOpenNotifications,
    required this.onOpenConnectionDetails,
    this.hasUnreadTaskCompletion = false,
    this.hasWorkingAgents = false,
    super.key,
  });

  final CcbProjectView view;
  final CcbAgent? selectedAgent;
  final VoidCallback onProjectSelected;
  final VoidCallback onOpenNotifications;
  final VoidCallback onOpenConnectionDetails;
  final bool hasUnreadTaskCompletion;
  final bool hasWorkingAgents;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return Padding(
      key: const ValueKey('wide-project-column'),
      padding: const EdgeInsets.fromLTRB(12, 8, 8, 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          SizedBox(
            height: 56,
            child: Row(
              children: [
                Expanded(child: Text('Projects', style: textTheme.titleMedium)),
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
              ],
            ),
          ),
          const SizedBox(height: 4),
          Expanded(
            child: ListView(
              key: const ValueKey('project-list'),
              children: [
                ProjectListTile(
                  view: view,
                  selectedAgent: selectedAgent,
                  selected: true,
                  hasUnreadTaskCompletion: hasUnreadTaskCompletion,
                  hasWorkingAgents: hasWorkingAgents,
                  onOpen: onProjectSelected,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
