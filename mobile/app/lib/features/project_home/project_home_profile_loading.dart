import '../../pairing/gateway_pairing.dart';
import 'project_home_profile_bootstrapper.dart';

enum ProjectHomeProfileBootstrapLoadKind {
  loadRequired,
  success,
  fallbackToLoad,
}

class ProjectHomeProfileBootstrapLoadOutcome {
  const ProjectHomeProfileBootstrapLoadOutcome.loadRequired()
    : kind = ProjectHomeProfileBootstrapLoadKind.loadRequired,
      result = null;

  const ProjectHomeProfileBootstrapLoadOutcome.success(this.result)
    : kind = ProjectHomeProfileBootstrapLoadKind.success;

  const ProjectHomeProfileBootstrapLoadOutcome.fallbackToLoad()
    : kind = ProjectHomeProfileBootstrapLoadKind.fallbackToLoad,
      result = null;

  final ProjectHomeProfileBootstrapLoadKind kind;
  final ProjectHomeProfileBootstrapResult? result;
}

enum ProjectHomeProfileLoadKind { success, failure }

class ProjectHomeProfileLoadOutcome {
  const ProjectHomeProfileLoadOutcome.success(this.result)
    : kind = ProjectHomeProfileLoadKind.success;

  const ProjectHomeProfileLoadOutcome.failure()
    : kind = ProjectHomeProfileLoadKind.failure,
      result = null;

  final ProjectHomeProfileLoadKind kind;
  final ProjectHomeProfileBootstrapResult? result;
}

class ProjectHomeProfileLoadingCoordinator {
  const ProjectHomeProfileLoadingCoordinator({
    required ProjectHomeProfileBootstrapper bootstrapper,
  }) : _bootstrapper = bootstrapper;

  final ProjectHomeProfileBootstrapper _bootstrapper;

  Future<ProjectHomeProfileBootstrapLoadOutcome> bootstrap({
    required GatewayPairedHost? selectedProfile,
    required GatewayPairedHost? debugProfile,
    required bool autoActivateDebugProfile,
  }) async {
    if (debugProfile == null) {
      return const ProjectHomeProfileBootstrapLoadOutcome.loadRequired();
    }
    try {
      final result = await _bootstrapper.bootstrap(
        selectedProfile: selectedProfile,
        debugProfile: debugProfile,
        autoActivateDebugProfile: autoActivateDebugProfile,
      );
      return ProjectHomeProfileBootstrapLoadOutcome.success(result);
    } catch (_) {
      return const ProjectHomeProfileBootstrapLoadOutcome.fallbackToLoad();
    }
  }

  Future<ProjectHomeProfileLoadOutcome> load({
    required GatewayPairedHost? selectedProfile,
  }) async {
    try {
      final result = await _bootstrapper.load(selectedProfile: selectedProfile);
      return ProjectHomeProfileLoadOutcome.success(result);
    } catch (_) {
      return const ProjectHomeProfileLoadOutcome.failure();
    }
  }
}
