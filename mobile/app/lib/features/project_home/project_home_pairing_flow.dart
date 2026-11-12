import '../../pairing/gateway_pairing.dart';
import 'project_home_pairing_claim_coordinator.dart';
import 'project_home_pairing_request.dart';
import 'project_home_pairing_scan_coordinator.dart';

typedef ProjectHomePairingRequestBuilder =
    ProjectHomePairingRequest Function({
      GatewayPairingPayload? pairingOverride,
    });

enum ProjectHomePairingRequestOutcomeKind { success, invalid }

class ProjectHomePairingRequestOutcome {
  const ProjectHomePairingRequestOutcome._({
    required this.kind,
    this.request,
    this.snackMessage,
  });

  const ProjectHomePairingRequestOutcome.success(
    ProjectHomePairingRequest request,
  ) : this._(
        kind: ProjectHomePairingRequestOutcomeKind.success,
        request: request,
      );

  const ProjectHomePairingRequestOutcome.invalid(String snackMessage)
    : this._(
        kind: ProjectHomePairingRequestOutcomeKind.invalid,
        snackMessage: snackMessage,
      );

  final ProjectHomePairingRequestOutcomeKind kind;
  final ProjectHomePairingRequest? request;
  final String? snackMessage;
}

enum ProjectHomePairingFlowScanOutcomeKind { busy, canceled, success, failure }

class ProjectHomePairingFlowScanOutcome {
  const ProjectHomePairingFlowScanOutcome._({
    required this.kind,
    this.pairingToApply,
    this.pairingToClaim,
    this.snackMessage,
  });

  const ProjectHomePairingFlowScanOutcome.busy()
    : this._(kind: ProjectHomePairingFlowScanOutcomeKind.busy);

  const ProjectHomePairingFlowScanOutcome.canceled()
    : this._(kind: ProjectHomePairingFlowScanOutcomeKind.canceled);

  const ProjectHomePairingFlowScanOutcome.success(GatewayPairingPayload pairing)
    : this._(
        kind: ProjectHomePairingFlowScanOutcomeKind.success,
        pairingToApply: pairing,
        pairingToClaim: pairing,
      );

  const ProjectHomePairingFlowScanOutcome.failure(String snackMessage)
    : this._(
        kind: ProjectHomePairingFlowScanOutcomeKind.failure,
        snackMessage: snackMessage,
      );

  final ProjectHomePairingFlowScanOutcomeKind kind;
  final GatewayPairingPayload? pairingToApply;
  final GatewayPairingPayload? pairingToClaim;
  final String? snackMessage;
}

enum ProjectHomePairingFlowClaimOutcomeKind { success, failure }

class ProjectHomePairingFlowClaimOutcome {
  const ProjectHomePairingFlowClaimOutcome._({
    required this.kind,
    this.paired,
    this.profiles,
    this.snackMessage,
  });

  const ProjectHomePairingFlowClaimOutcome.success({
    required GatewayPairedHost paired,
    required List<GatewayPairedHost> profiles,
    required String snackMessage,
  }) : this._(
         kind: ProjectHomePairingFlowClaimOutcomeKind.success,
         paired: paired,
         profiles: profiles,
         snackMessage: snackMessage,
       );

  const ProjectHomePairingFlowClaimOutcome.failure(String snackMessage)
    : this._(
        kind: ProjectHomePairingFlowClaimOutcomeKind.failure,
        snackMessage: snackMessage,
      );

  final ProjectHomePairingFlowClaimOutcomeKind kind;
  final GatewayPairedHost? paired;
  final List<GatewayPairedHost>? profiles;
  final String? snackMessage;
}

class ProjectHomePairingFlowCoordinator {
  const ProjectHomePairingFlowCoordinator({
    ProjectHomePairingScanCoordinator scanCoordinator =
        const ProjectHomePairingScanCoordinator(),
    ProjectHomePairingClaimCoordinator claimCoordinator =
        const ProjectHomePairingClaimCoordinator(),
  }) : _scanCoordinator = scanCoordinator,
       _claimCoordinator = claimCoordinator;

  final ProjectHomePairingScanCoordinator _scanCoordinator;
  final ProjectHomePairingClaimCoordinator _claimCoordinator;

  ProjectHomePairingRequestOutcome buildRequest({
    required ProjectHomePairingRequestBuilder builder,
    GatewayPairingPayload? pairingOverride,
  }) {
    try {
      return ProjectHomePairingRequestOutcome.success(
        builder(pairingOverride: pairingOverride),
      );
    } on ProjectHomePairingRequestException catch (error) {
      return ProjectHomePairingRequestOutcome.invalid(error.message);
    }
  }

  Future<ProjectHomePairingFlowScanOutcome> scan({
    required bool isClaimingPairing,
    required ProjectHomePairingScan scanner,
  }) async {
    final outcome = await _scanCoordinator.scan(
      isClaimingPairing: isClaimingPairing,
      scanner: scanner,
    );
    return switch (outcome.kind) {
      ProjectHomePairingScanOutcomeKind.busy =>
        const ProjectHomePairingFlowScanOutcome.busy(),
      ProjectHomePairingScanOutcomeKind.canceled =>
        const ProjectHomePairingFlowScanOutcome.canceled(),
      ProjectHomePairingScanOutcomeKind.success =>
        ProjectHomePairingFlowScanOutcome.success(outcome.pairing!),
      ProjectHomePairingScanOutcomeKind.failure =>
        ProjectHomePairingFlowScanOutcome.failure(outcome.snackMessage!),
    };
  }

  Future<ProjectHomePairingFlowClaimOutcome> claim({
    required ProjectHomePairingRequest request,
    required ProjectHomePairingClaim claimAndStore,
    required GatewayHostProfileStore store,
    required ProjectHomePairingProfileMerger mergeProfiles,
  }) async {
    final outcome = await _claimCoordinator.complete(
      request: request,
      claimAndStore: claimAndStore,
      store: store,
      mergeProfiles: mergeProfiles,
    );
    return switch (outcome.kind) {
      ProjectHomePairingClaimOutcomeKind.success =>
        ProjectHomePairingFlowClaimOutcome.success(
          paired: outcome.paired!,
          profiles: outcome.profiles!,
          snackMessage: outcome.snackMessage!,
        ),
      ProjectHomePairingClaimOutcomeKind.failure =>
        ProjectHomePairingFlowClaimOutcome.failure(outcome.snackMessage!),
    };
  }
}
