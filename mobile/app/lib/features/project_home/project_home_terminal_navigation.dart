import '../../models/ccb_project_view.dart';

const projectHomeTerminalTransportNotReadySnack =
    'Gateway terminal transport is not ready';

ProjectHomeTerminalNavigationOutcome projectHomeFakeTerminalNavigation({
  required CcbProjectView view,
  required String agentName,
}) {
  return ProjectHomeTerminalNavigationOutcome.open(
    ProjectHomeTerminalNavigationSpec(
      projectId: view.project.id,
      agentName: agentName,
      gatewayTerminal: false,
    ),
  );
}

ProjectHomeTerminalNavigationOutcome projectHomeGatewayTerminalNavigation({
  required CcbProjectView? view,
  required String agentName,
  required bool hasTerminalTransport,
}) {
  if (view == null) {
    return const ProjectHomeTerminalNavigationOutcome.none();
  }
  if (!hasTerminalTransport) {
    return const ProjectHomeTerminalNavigationOutcome.noTransport(
      snackMessage: projectHomeTerminalTransportNotReadySnack,
    );
  }
  final agent = view.agentByName(agentName);
  if (agent == null || view.namespaceEpoch == null || agent.paneId == null) {
    return const ProjectHomeTerminalNavigationOutcome.none();
  }
  return ProjectHomeTerminalNavigationOutcome.open(
    ProjectHomeTerminalNavigationSpec(
      projectId: view.project.id,
      agentName: agentName,
      gatewayTerminal: true,
      namespaceEpoch: view.namespaceEpoch,
      windowName: agent.window,
      paneId: agent.paneId,
    ),
  );
}

enum ProjectHomeTerminalNavigationKind { none, noTransport, open }

class ProjectHomeTerminalNavigationOutcome {
  const ProjectHomeTerminalNavigationOutcome.none()
    : kind = ProjectHomeTerminalNavigationKind.none,
      spec = null,
      snackMessage = null;

  const ProjectHomeTerminalNavigationOutcome.noTransport({
    required String snackMessage,
  }) : this._(
         kind: ProjectHomeTerminalNavigationKind.noTransport,
         snackMessage: snackMessage,
       );

  const ProjectHomeTerminalNavigationOutcome.open(
    ProjectHomeTerminalNavigationSpec spec,
  ) : this._(kind: ProjectHomeTerminalNavigationKind.open, spec: spec);

  const ProjectHomeTerminalNavigationOutcome._({
    required this.kind,
    this.spec,
    this.snackMessage,
  });

  final ProjectHomeTerminalNavigationKind kind;
  final ProjectHomeTerminalNavigationSpec? spec;
  final String? snackMessage;
}

class ProjectHomeTerminalNavigationSpec {
  const ProjectHomeTerminalNavigationSpec({
    required this.projectId,
    required this.agentName,
    required this.gatewayTerminal,
    this.namespaceEpoch,
    this.windowName,
    this.paneId,
  });

  final String projectId;
  final String agentName;
  final bool gatewayTerminal;
  final int? namespaceEpoch;
  final String? windowName;
  final String? paneId;
}
