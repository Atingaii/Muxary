import 'dart:async';
import 'dart:io';

import '../../models/ccb_project.dart';
import '../../models/ccb_project_view.dart';
import '../../pairing/gateway_pairing.dart';
import '../../repository/gateway_mobile_ccb_repository.dart';
import '../../repository/mobile_ccb_repository.dart';
import '../../transport/http_gateway_transport.dart';
import '../../transport/terminal_transport.dart';
import '../../transport/route_provider.dart';

const projectHomeRuntimeNoProfileSnack = 'Pair a gateway profile first';
const projectHomeRuntimeViewLoadTimeout = Duration(seconds: 10);
const projectHomeRuntimeGatewayHealthTimeout = Duration(seconds: 4);

typedef ProjectHomeGatewayRepositoryFactory =
    MobileCcbRepository Function(GatewayPairedHost profile);

typedef ProjectHomeGatewayTerminalTransportFactory =
    TerminalTransport Function(GatewayPairedHost profile);

ProjectHomePairedRuntimeSelection selectProjectHomePairedRuntimeProfile({
  required List<GatewayPairedHost> profiles,
  required GatewayPairedHost? selectedProfile,
}) {
  final profile = selectedProfile ?? (profiles.isEmpty ? null : profiles.first);
  if (profile == null) {
    return const ProjectHomePairedRuntimeSelection.noProfile(
      snackMessage: projectHomeRuntimeNoProfileSnack,
    );
  }
  return ProjectHomePairedRuntimeSelection.activate(
    ProjectHomeGatewayActivationData.fromProfile(profile),
  );
}

ProjectHomeGatewayActivationData activateProjectHomeGatewayProfile(
  GatewayPairedHost profile,
) {
  return ProjectHomeGatewayActivationData.fromProfile(profile);
}

ProjectHomeFakeRuntimeResetData resetProjectHomeFakeRuntime({
  required String defaultProjectId,
}) {
  return ProjectHomeFakeRuntimeResetData(defaultProjectId: defaultProjectId);
}

class ProjectHomeRuntimeSessionCoordinator {
  const ProjectHomeRuntimeSessionCoordinator();

  ProjectHomeFakeRuntimeSession activateFake({
    required MobileCcbRepository repository,
    required String defaultProjectId,
    Duration viewLoadTimeout = projectHomeRuntimeViewLoadTimeout,
  }) {
    return ProjectHomeFakeRuntimeSession(
      repository: repository,
      activeProjectId: defaultProjectId,
      terminalTransport: null,
      viewFuture: repository
          .getProjectView(defaultProjectId)
          .timeout(viewLoadTimeout),
    );
  }

  ProjectHomeGatewayRuntimeSession activateGateway({
    required ProjectHomeGatewayActivationData activation,
    required ProjectHomeGatewayRepositoryFactory repositoryFactory,
    required ProjectHomeGatewayTerminalTransportFactory
    terminalTransportFactory,
    Duration projectListTimeout = projectHomeRuntimeViewLoadTimeout,
  }) {
    final profile = activation.profile;
    final repository = repositoryFactory(profile);
    return ProjectHomeGatewayRuntimeSession(
      activation: activation,
      repository: repository,
      preferredProjectId: activation.activeProjectId,
      terminalTransport: terminalTransportFactory(profile),
      projectsFuture: Future<List<CcbProject>>(() async {
        try {
          await verifyProjectHomeGatewayProfile(repository);
          return sortCcbProjectsByRecentActivity(
            await repository.listProjects(),
          );
        } catch (error) {
          if (error is ProjectHomeGatewayActivationException) {
            rethrow;
          }
          throw projectHomeGatewayActivationExceptionFor(error);
        }
      }).timeout(projectListTimeout),
    );
  }
}

enum ProjectHomeGatewayActivationFailureKind {
  tokenInvalid,
  scopeDenied,
  gatewayUnreachable,
  serverUnhealthy,
}

class ProjectHomeGatewayActivationException implements Exception {
  const ProjectHomeGatewayActivationException({
    required this.kind,
    required this.message,
    this.cause,
  });

  final ProjectHomeGatewayActivationFailureKind kind;
  final String message;
  final Object? cause;

  @override
  String toString() {
    return message;
  }
}

Future<void> verifyProjectHomeGatewayProfile(
  MobileCcbRepository repository, {
  Duration timeout = projectHomeRuntimeGatewayHealthTimeout,
}) async {
  final probe =
      repository is MobileGatewayProfileHealthProbe
          ? repository as MobileGatewayProfileHealthProbe
          : null;
  if (probe == null) {
    return;
  }
  try {
    if (probe case final MobileGatewayCoreRouteVerifier verifier) {
      await verifier.verifyCoreRoutes().timeout(timeout);
      return;
    }
    final health = await probe.health().timeout(timeout);
    if (health.status.trim().toLowerCase() != 'ok') {
      throw ProjectHomeGatewayActivationException(
        kind: ProjectHomeGatewayActivationFailureKind.serverUnhealthy,
        message: 'Gateway health check failed: ${health.status}',
      );
    }
    final device = await probe.device().timeout(timeout);
    if (device.revoked) {
      throw const ProjectHomeGatewayActivationException(
        kind: ProjectHomeGatewayActivationFailureKind.tokenInvalid,
        message:
            'Gateway profile token is no longer valid. Re-pair this phone.',
      );
    }
  } catch (error) {
    if (error is ProjectHomeGatewayActivationException) {
      rethrow;
    }
    throw projectHomeGatewayActivationExceptionFor(error);
  }
}

ProjectHomeGatewayActivationException projectHomeGatewayActivationExceptionFor(
  Object error,
) {
  if (error is GatewayHttpException && error.statusCode == 401) {
    return ProjectHomeGatewayActivationException(
      kind: ProjectHomeGatewayActivationFailureKind.tokenInvalid,
      message: 'Gateway profile token is invalid. Re-pair this phone.',
      cause: error,
    );
  }
  if (error is GatewayHttpException && error.statusCode == 403) {
    return ProjectHomeGatewayActivationException(
      kind: ProjectHomeGatewayActivationFailureKind.scopeDenied,
      message:
          'Gateway profile is paired but lacks permission for this action.',
      cause: error,
    );
  }
  if (error is TimeoutException ||
      error is SocketException ||
      error is HttpException ||
      error is HandshakeException ||
      error is OSError) {
    return ProjectHomeGatewayActivationException(
      kind: ProjectHomeGatewayActivationFailureKind.gatewayUnreachable,
      message:
          'Gateway is unreachable. Check VPN, LAN, or route diagnostics, then retry.',
      cause: error,
    );
  }
  if (error is GatewayHttpException) {
    return ProjectHomeGatewayActivationException(
      kind: ProjectHomeGatewayActivationFailureKind.serverUnhealthy,
      message: 'Gateway rejected health check: ${error.statusCode}',
      cause: error,
    );
  }
  return ProjectHomeGatewayActivationException(
    kind: ProjectHomeGatewayActivationFailureKind.serverUnhealthy,
    message: 'Gateway health check failed: $error',
    cause: error,
  );
}

enum ProjectHomePairedRuntimeSelectionKind { noProfile, activate }

class ProjectHomePairedRuntimeSelection {
  const ProjectHomePairedRuntimeSelection.noProfile({
    required String snackMessage,
  }) : this._(
         kind: ProjectHomePairedRuntimeSelectionKind.noProfile,
         snackMessage: snackMessage,
       );

  const ProjectHomePairedRuntimeSelection.activate(
    ProjectHomeGatewayActivationData activation,
  ) : this._(
        kind: ProjectHomePairedRuntimeSelectionKind.activate,
        activation: activation,
      );

  const ProjectHomePairedRuntimeSelection._({
    required this.kind,
    this.activation,
    this.snackMessage,
  });

  final ProjectHomePairedRuntimeSelectionKind kind;
  final ProjectHomeGatewayActivationData? activation;
  final String? snackMessage;
}

class ProjectHomeGatewayActivationData {
  const ProjectHomeGatewayActivationData({
    required this.profile,
    required this.gatewayUrlText,
    required this.routeKind,
    required this.activeProjectId,
  });

  factory ProjectHomeGatewayActivationData.fromProfile(
    GatewayPairedHost profile,
  ) {
    return ProjectHomeGatewayActivationData(
      profile: profile,
      gatewayUrlText: profile.profile.routeProvider.gatewayUrl.toString(),
      routeKind: profile.profile.routeProvider.kind,
      activeProjectId: profile.projectId ?? profile.profile.hostId,
    );
  }

  final GatewayPairedHost profile;
  final String gatewayUrlText;
  final RouteProviderKind routeKind;
  final String activeProjectId;
}

class ProjectHomeFakeRuntimeResetData {
  const ProjectHomeFakeRuntimeResetData({required this.defaultProjectId});

  final String defaultProjectId;
}

class ProjectHomeFakeRuntimeSession {
  const ProjectHomeFakeRuntimeSession({
    required this.repository,
    required this.activeProjectId,
    required this.terminalTransport,
    required this.viewFuture,
  });

  final MobileCcbRepository repository;
  final String activeProjectId;
  final TerminalTransport? terminalTransport;
  final Future<CcbProjectView> viewFuture;
}

class ProjectHomeGatewayRuntimeSession {
  const ProjectHomeGatewayRuntimeSession({
    required this.activation,
    required this.repository,
    required this.preferredProjectId,
    required this.terminalTransport,
    required this.projectsFuture,
  });

  final ProjectHomeGatewayActivationData activation;
  final MobileCcbRepository repository;
  final String preferredProjectId;
  final TerminalTransport terminalTransport;
  final Future<List<CcbProject>> projectsFuture;
}
