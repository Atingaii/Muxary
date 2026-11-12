import '../../models/ccb_project_view.dart';
import '../../notifications/task_completion_notifications.dart';

enum ProjectHomeTaskCompletionNotificationRouteKind {
  openProjectAgent,
  projectList,
}

class ProjectHomeTaskCompletionNotificationRoute {
  const ProjectHomeTaskCompletionNotificationRoute.openProjectAgent({
    required this.projectId,
    required this.agentName,
    required this.view,
  }) : kind = ProjectHomeTaskCompletionNotificationRouteKind.openProjectAgent;

  const ProjectHomeTaskCompletionNotificationRoute.projectList()
    : kind = ProjectHomeTaskCompletionNotificationRouteKind.projectList,
      projectId = null,
      agentName = null,
      view = null;

  final ProjectHomeTaskCompletionNotificationRouteKind kind;
  final String? projectId;
  final String? agentName;
  final CcbProjectView? view;
}

ProjectHomeTaskCompletionNotificationRoute
resolveProjectHomeTaskCompletionNotificationTap({
  required TaskCompletionNotificationTap tap,
  required CcbProjectView? targetView,
}) {
  final view = targetView;
  if (view == null || view.agentByName(tap.agent) == null) {
    return const ProjectHomeTaskCompletionNotificationRoute.projectList();
  }
  return ProjectHomeTaskCompletionNotificationRoute.openProjectAgent(
    projectId: view.project.id,
    agentName: tap.agent,
    view: view,
  );
}
