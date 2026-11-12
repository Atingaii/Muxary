import '../../pairing/gateway_pairing.dart';
import 'project_home_gateway_profiles.dart';

class ProjectHomeProfileBootstrapResult {
  const ProjectHomeProfileBootstrapResult({
    required this.profiles,
    required this.selectedProfile,
    this.activateProfile,
  });

  final List<GatewayPairedHost> profiles;
  final GatewayPairedHost? selectedProfile;
  final GatewayPairedHost? activateProfile;
}

class ProjectHomeProfileBootstrapper {
  ProjectHomeProfileBootstrapper({required GatewayHostProfileStore store})
    : _store = store;

  final GatewayHostProfileStore _store;

  Future<ProjectHomeProfileBootstrapResult> bootstrap({
    required GatewayPairedHost? selectedProfile,
    GatewayPairedHost? debugProfile,
    bool autoActivateDebugProfile = false,
  }) async {
    if (debugProfile == null) {
      return load(selectedProfile: selectedProfile);
    }
    await _store.save(debugProfile);
    final storedProfiles = await _store.list();
    return ProjectHomeProfileBootstrapResult(
      profiles: mergeProjectHomeGatewayProfiles(storedProfiles, debugProfile),
      selectedProfile: debugProfile,
      activateProfile: autoActivateDebugProfile ? debugProfile : null,
    );
  }

  Future<ProjectHomeProfileBootstrapResult> load({
    required GatewayPairedHost? selectedProfile,
  }) async {
    final profiles = await _store.list();
    return ProjectHomeProfileBootstrapResult(
      profiles: profiles,
      selectedProfile:
          selectedProfile ?? await _store.resolvePreferred(profiles),
    );
  }

  Future<List<GatewayPairedHost>> mergeStoredWith(
    GatewayPairedHost paired,
  ) async {
    final storedProfiles = await _store.list();
    return mergeProjectHomeGatewayProfiles(storedProfiles, paired);
  }
}
