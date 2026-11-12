import 'dart:async';

import '../../models/ccb_project_view.dart';
import '../../repository/mobile_ccb_repository.dart';

class ProjectHomeViewRefreshCoordinator {
  const ProjectHomeViewRefreshCoordinator({
    this.timeout = const Duration(seconds: 10),
  });

  final Duration timeout;

  Future<ProjectHomeViewRefreshOutcome> refresh({
    required MobileCcbRepository repository,
    required String projectId,
    required String? selectedAgentName,
  }) async {
    try {
      final refreshed = await repository
          .getProjectView(projectId)
          .timeout(timeout);
      return ProjectHomeViewRefreshOutcome.success(
        refreshedView: refreshed,
        selectedAgentName: _nextSelectedAgentName(refreshed, selectedAgentName),
      );
    } catch (error) {
      return ProjectHomeViewRefreshOutcome.failure(
        snackMessage: error.toString(),
      );
    }
  }

  String? _nextSelectedAgentName(
    CcbProjectView refreshed,
    String? selectedAgentName,
  ) {
    if (selectedAgentName == null) {
      return null;
    }
    return refreshed.agentByName(selectedAgentName) == null
        ? null
        : selectedAgentName;
  }
}

enum ProjectHomeViewRefreshOutcomeKind { success, failure }

class ProjectHomeViewRefreshOutcome {
  const ProjectHomeViewRefreshOutcome.success({
    required this.refreshedView,
    required this.selectedAgentName,
  }) : kind = ProjectHomeViewRefreshOutcomeKind.success,
       snackMessage = null;

  const ProjectHomeViewRefreshOutcome.failure({required this.snackMessage})
    : kind = ProjectHomeViewRefreshOutcomeKind.failure,
      refreshedView = null,
      selectedAgentName = null;

  final ProjectHomeViewRefreshOutcomeKind kind;
  final CcbProjectView? refreshedView;
  final String? selectedAgentName;
  final String? snackMessage;
}
