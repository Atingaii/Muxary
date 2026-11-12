import '../../models/ccb_notification.dart';
import '../../models/ccb_project_view.dart';
import 'project_view_selection.dart';

class ProjectHomeNotificationTargetResolution {
  const ProjectHomeNotificationTargetResolution({
    required this.selectedAgentName,
    required this.snackMessage,
  });

  final String? selectedAgentName;
  final String snackMessage;
}

class ProjectHomeNotificationOpenOutcome {
  const ProjectHomeNotificationOpenOutcome({
    required this.openedProjectId,
    required this.selectedAgentName,
    required this.snackMessage,
  });

  final String? openedProjectId;
  final String? selectedAgentName;
  final String snackMessage;
}

ProjectHomeNotificationTargetResolution resolveProjectHomeNotificationTarget(
  CcbProjectView view,
  CcbNotification notification,
) {
  final outcome = resolveProjectHomeNotificationOpenOutcome(view, notification);
  return ProjectHomeNotificationTargetResolution(
    selectedAgentName: outcome.selectedAgentName,
    snackMessage: outcome.snackMessage,
  );
}

ProjectHomeNotificationOpenOutcome resolveProjectHomeNotificationOpenOutcome(
  CcbProjectView view,
  CcbNotification notification,
) {
  final target = notification.target;
  final explicitAgentName = target.agentName;
  String? selectedAgentName;
  if (explicitAgentName != null) {
    if (view.agentByName(explicitAgentName) != null) {
      selectedAgentName = explicitAgentName;
    }
  } else {
    final windowName = target.windowName;
    if (windowName != null) {
      selectedAgentName = firstAgentNameForWindow(view, windowName);
    }
  }
  return ProjectHomeNotificationOpenOutcome(
    openedProjectId: selectedAgentName == null ? null : view.project.id,
    selectedAgentName: selectedAgentName,
    snackMessage: notificationOpenMessage(notification),
  );
}

String notificationOpenMessage(CcbNotification notification) {
  final target = notification.target;
  if (target.contentId != null) {
    return 'Opened content ${target.contentId}';
  }
  if (target.commsId != null) {
    return 'Opened Comms ${target.commsId}';
  }
  if (target.agentName != null) {
    return 'Opened agent ${target.agentName}';
  }
  return 'Opened notification';
}
