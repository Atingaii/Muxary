import '../../models/ccb_project_view.dart';
import 'project_view_selection.dart';

class ProjectHomeMobileAgentsCollapseOutcome {
  const ProjectHomeMobileAgentsCollapseOutcome({
    required this.collapsed,
    required this.shouldUpdate,
  });

  final bool collapsed;
  final bool shouldUpdate;
}

class ProjectHomeOpenedProjectOutcome {
  const ProjectHomeOpenedProjectOutcome({required this.openedProjectId});

  final String? openedProjectId;
}

class ProjectHomeSelectedAgentOutcome {
  const ProjectHomeSelectedAgentOutcome({
    required this.selectedAgentName,
    required this.shouldUpdate,
  });

  final String? selectedAgentName;
  final bool shouldUpdate;
}

ProjectHomeMobileAgentsCollapseOutcome collapseProjectHomeMobileAgents(
  bool collapsed,
) {
  return ProjectHomeMobileAgentsCollapseOutcome(
    collapsed: true,
    shouldUpdate: !collapsed,
  );
}

ProjectHomeMobileAgentsCollapseOutcome expandProjectHomeMobileAgents(
  bool collapsed,
) {
  return ProjectHomeMobileAgentsCollapseOutcome(
    collapsed: false,
    shouldUpdate: collapsed,
  );
}

ProjectHomeOpenedProjectOutcome openProjectHomeProject(CcbProjectView view) {
  return ProjectHomeOpenedProjectOutcome(openedProjectId: view.project.id);
}

ProjectHomeOpenedProjectOutcome closeProjectHomeProject() {
  return const ProjectHomeOpenedProjectOutcome(openedProjectId: null);
}

ProjectHomeSelectedAgentOutcome selectProjectHomeAgent(String agentName) {
  return ProjectHomeSelectedAgentOutcome(
    selectedAgentName: agentName,
    shouldUpdate: true,
  );
}

ProjectHomeSelectedAgentOutcome selectProjectHomeLocalWindow(
  CcbProjectView view,
  String windowName,
) {
  final agentName = projectHomeLocalWindowSelectionAgentName(view, windowName);
  return ProjectHomeSelectedAgentOutcome(
    selectedAgentName: agentName,
    shouldUpdate: agentName != null,
  );
}
