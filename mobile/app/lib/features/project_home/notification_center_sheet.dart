import 'package:flutter/material.dart';

import '../../models/ccb_notification.dart';
import 'project_home_notification_target.dart' as notification_target;

class NotificationCenterSheet extends StatelessWidget {
  const NotificationCenterSheet({
    required this.notifications,
    required this.onOpen,
    super.key,
  });

  final List<CcbNotification> notifications;
  final ValueChanged<CcbNotification> onOpen;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    return SafeArea(
      child: SizedBox(
        height: MediaQuery.sizeOf(context).height * 0.65,
        child: Padding(
          key: const ValueKey('notification-center'),
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.notifications_active),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text('Notifications', style: textTheme.titleLarge),
                  ),
                  Text(
                    notifications.length.toString(),
                    key: const ValueKey('notification-count'),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              if (notifications.isEmpty)
                const Expanded(child: Center(child: Text('No notifications')))
              else
                Expanded(
                  child: ListView.separated(
                    itemCount: notifications.length,
                    separatorBuilder:
                        (context, index) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final notification = notifications[index];
                      return ListTile(
                        key: ValueKey('notification-${notification.id}'),
                        contentPadding: EdgeInsets.zero,
                        leading: Icon(_notificationIcon(notification.kind)),
                        title: Text(notification.title),
                        subtitle: Text(
                          '${notification.body}\n'
                          '${_notificationTargetLabel(notification.target)}',
                        ),
                        isThreeLine: true,
                        trailing: Icon(
                          _notificationSeverityIcon(notification.severity),
                        ),
                        onTap: () {
                          onOpen(notification);
                        },
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

String notificationOpenMessage(CcbNotification notification) {
  return notification_target.notificationOpenMessage(notification);
}

IconData _notificationIcon(CcbNotificationKind kind) {
  return switch (kind) {
    CcbNotificationKind.taskCompleted => Icons.check_circle_outline,
    CcbNotificationKind.taskFailed => Icons.error_outline,
    CcbNotificationKind.taskBlocked => Icons.block,
    CcbNotificationKind.callbackWaiting => Icons.record_voice_over,
    CcbNotificationKind.commsMention => Icons.forum,
    CcbNotificationKind.agentUnhealthy => Icons.health_and_safety,
  };
}

IconData _notificationSeverityIcon(CcbNotificationSeverity severity) {
  return switch (severity) {
    CcbNotificationSeverity.info => Icons.info_outline,
    CcbNotificationSeverity.warning => Icons.warning_amber,
    CcbNotificationSeverity.critical => Icons.priority_high,
  };
}

String _notificationTargetLabel(CcbNotificationTarget target) {
  return [
    target.projectId,
    if (target.agentName != null) 'agent ${target.agentName}',
    if (target.windowName != null) 'window ${target.windowName}',
    if (target.contentId != null) 'content ${target.contentId}',
    if (target.commsId != null) 'Comms ${target.commsId}',
  ].join(' / ');
}
