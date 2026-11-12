import '../../pairing/gateway_pairing.dart';
import '../../transport/gateway_route_diagnostics.dart';

typedef ProjectHomeGatewayRouteDiagnostics =
    Future<GatewayRouteDiagnosticReport> Function(GatewayPairedHost profile);

enum ProjectHomeRouteDiagnosticsOutcomeKind {
  noProfile,
  busy,
  ready,
  success,
  failure,
}

class ProjectHomeRouteDiagnosticsOutcome {
  const ProjectHomeRouteDiagnosticsOutcome._({
    required this.kind,
    this.report,
    this.snackMessage,
  });

  const ProjectHomeRouteDiagnosticsOutcome.noProfile()
    : this._(
        kind: ProjectHomeRouteDiagnosticsOutcomeKind.noProfile,
        snackMessage: 'Select a gateway profile first',
      );

  const ProjectHomeRouteDiagnosticsOutcome.busy()
    : this._(kind: ProjectHomeRouteDiagnosticsOutcomeKind.busy);

  const ProjectHomeRouteDiagnosticsOutcome.ready()
    : this._(kind: ProjectHomeRouteDiagnosticsOutcomeKind.ready);

  ProjectHomeRouteDiagnosticsOutcome.success(
    GatewayRouteDiagnosticReport report,
  ) : this._(
        kind: ProjectHomeRouteDiagnosticsOutcomeKind.success,
        report: report,
        snackMessage: report.summary,
      );

  ProjectHomeRouteDiagnosticsOutcome.failure(Object error)
    : this._(
        kind: ProjectHomeRouteDiagnosticsOutcomeKind.failure,
        snackMessage: error.toString(),
      );

  final ProjectHomeRouteDiagnosticsOutcomeKind kind;
  final GatewayRouteDiagnosticReport? report;
  final String? snackMessage;
}

class ProjectHomeRouteDiagnosticsCoordinator {
  const ProjectHomeRouteDiagnosticsCoordinator();

  ProjectHomeRouteDiagnosticsOutcome begin({
    required GatewayPairedHost? selectedProfile,
    required bool checking,
  }) {
    if (selectedProfile == null) {
      return const ProjectHomeRouteDiagnosticsOutcome.noProfile();
    }
    if (checking) {
      return const ProjectHomeRouteDiagnosticsOutcome.busy();
    }
    return const ProjectHomeRouteDiagnosticsOutcome.ready();
  }

  Future<ProjectHomeRouteDiagnosticsOutcome> complete({
    required GatewayPairedHost profile,
    required ProjectHomeGatewayRouteDiagnostics diagnostics,
  }) async {
    try {
      final report = await diagnostics(profile);
      return ProjectHomeRouteDiagnosticsOutcome.success(report);
    } catch (error) {
      return ProjectHomeRouteDiagnosticsOutcome.failure(error);
    }
  }
}
