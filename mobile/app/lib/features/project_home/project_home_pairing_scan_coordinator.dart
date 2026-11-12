import '../../pairing/gateway_pairing.dart';

typedef ProjectHomePairingScan = Future<GatewayPairingPayload?> Function();

enum ProjectHomePairingScanOutcomeKind { busy, canceled, success, failure }

class ProjectHomePairingScanOutcome {
  const ProjectHomePairingScanOutcome._({
    required this.kind,
    this.pairing,
    this.snackMessage,
  });

  const ProjectHomePairingScanOutcome.busy()
    : this._(kind: ProjectHomePairingScanOutcomeKind.busy);

  const ProjectHomePairingScanOutcome.canceled()
    : this._(kind: ProjectHomePairingScanOutcomeKind.canceled);

  const ProjectHomePairingScanOutcome.success(GatewayPairingPayload pairing)
    : this._(kind: ProjectHomePairingScanOutcomeKind.success, pairing: pairing);

  ProjectHomePairingScanOutcome.failure(Object error)
    : this._(
        kind: ProjectHomePairingScanOutcomeKind.failure,
        snackMessage: error.toString(),
      );

  final ProjectHomePairingScanOutcomeKind kind;
  final GatewayPairingPayload? pairing;
  final String? snackMessage;
}

class ProjectHomePairingScanCoordinator {
  const ProjectHomePairingScanCoordinator();

  Future<ProjectHomePairingScanOutcome> scan({
    required bool isClaimingPairing,
    required ProjectHomePairingScan scanner,
  }) async {
    if (isClaimingPairing) {
      return const ProjectHomePairingScanOutcome.busy();
    }
    try {
      final pairing = await scanner();
      if (pairing == null) {
        return const ProjectHomePairingScanOutcome.canceled();
      }
      return ProjectHomePairingScanOutcome.success(pairing);
    } catch (error) {
      return ProjectHomePairingScanOutcome.failure(error);
    }
  }
}
