import '../../pairing/gateway_pairing.dart';
import 'project_home_pairing_request.dart';

typedef ProjectHomePairingClaim =
    Future<GatewayPairedHost> Function({
      required GatewayPairingPayload pairing,
      required String deviceName,
      required GatewayHostProfileStore store,
      String? deviceId,
    });

typedef ProjectHomePairingProfileMerger =
    Future<List<GatewayPairedHost>> Function(GatewayPairedHost paired);

enum ProjectHomePairingClaimOutcomeKind { success, failure }

class ProjectHomePairingClaimOutcome {
  const ProjectHomePairingClaimOutcome._({
    required this.kind,
    this.paired,
    this.profiles,
    this.snackMessage,
  });

  const ProjectHomePairingClaimOutcome.success({
    required GatewayPairedHost paired,
    required List<GatewayPairedHost> profiles,
  }) : this._(
         kind: ProjectHomePairingClaimOutcomeKind.success,
         paired: paired,
         profiles: profiles,
         snackMessage: 'Gateway paired',
       );

  ProjectHomePairingClaimOutcome.failure(Object error)
    : this._(
        kind: ProjectHomePairingClaimOutcomeKind.failure,
        snackMessage: error.toString(),
      );

  final ProjectHomePairingClaimOutcomeKind kind;
  final GatewayPairedHost? paired;
  final List<GatewayPairedHost>? profiles;
  final String? snackMessage;
}

class ProjectHomePairingClaimCoordinator {
  const ProjectHomePairingClaimCoordinator();

  Future<ProjectHomePairingClaimOutcome> complete({
    required ProjectHomePairingRequest request,
    required ProjectHomePairingClaim claimAndStore,
    required GatewayHostProfileStore store,
    required ProjectHomePairingProfileMerger mergeProfiles,
  }) async {
    try {
      final deviceId = await store.reusableDeviceIdFor(request.pairing);
      final paired = await claimAndStore(
        pairing: request.pairing,
        deviceName: request.deviceName,
        store: store,
        deviceId: deviceId,
      );
      final profiles = await mergeProfiles(paired);
      return ProjectHomePairingClaimOutcome.success(
        paired: paired,
        profiles: profiles,
      );
    } catch (error) {
      return ProjectHomePairingClaimOutcome.failure(error);
    }
  }
}
