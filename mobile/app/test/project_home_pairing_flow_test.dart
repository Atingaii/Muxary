import 'package:ccb_mobile/features/project_home/project_home_pairing_flow.dart';
import 'package:ccb_mobile/features/project_home/project_home_pairing_request.dart';
import 'package:ccb_mobile/pairing/gateway_pairing.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:test/test.dart';

import 'support/project_home_test_fakes.dart';

void main() {
  final coordinator = const ProjectHomePairingFlowCoordinator();

  group('request build outcome', () {
    test('maps successful builder result', () {
      final request = ProjectHomePairingRequest(
        pairing: _pairingPayload(code: 'manual-code'),
        deviceName: 'Pixel Fold',
      );

      final outcome = coordinator.buildRequest(
        builder: ({pairingOverride}) => request,
      );

      expect(outcome.kind, ProjectHomePairingRequestOutcomeKind.success);
      expect(outcome.request, same(request));
      expect(outcome.snackMessage, isNull);
    });

    test('maps request exception to invalid snack', () {
      final outcome = coordinator.buildRequest(
        builder: ({pairingOverride}) {
          throw const ProjectHomePairingRequestException(
            'Gateway URL is required',
          );
        },
      );

      expect(outcome.kind, ProjectHomePairingRequestOutcomeKind.invalid);
      expect(outcome.request, isNull);
      expect(outcome.snackMessage, 'Gateway URL is required');
    });
  });

  group('scan outcome', () {
    test('busy skips scanner without snack or payload', () async {
      var scanCalls = 0;

      final outcome = await coordinator.scan(
        isClaimingPairing: true,
        scanner: () async {
          scanCalls += 1;
          return _pairingPayload(code: 'qr-code');
        },
      );

      expect(outcome.kind, ProjectHomePairingFlowScanOutcomeKind.busy);
      expect(scanCalls, 0);
      expect(outcome.pairingToApply, isNull);
      expect(outcome.pairingToClaim, isNull);
      expect(outcome.snackMessage, isNull);
    });

    test('cancel calls scanner once and returns no-op outcome', () async {
      var scanCalls = 0;

      final outcome = await coordinator.scan(
        isClaimingPairing: false,
        scanner: () async {
          scanCalls += 1;
          return null;
        },
      );

      expect(outcome.kind, ProjectHomePairingFlowScanOutcomeKind.canceled);
      expect(scanCalls, 1);
      expect(outcome.pairingToApply, isNull);
      expect(outcome.pairingToClaim, isNull);
    });

    test('failure maps scanner error to snack', () async {
      final outcome = await coordinator.scan(
        isClaimingPairing: false,
        scanner: () async => throw StateError('scan failed'),
      );

      expect(outcome.kind, ProjectHomePairingFlowScanOutcomeKind.failure);
      expect(outcome.snackMessage, 'Bad state: scan failed');
      expect(outcome.pairingToApply, isNull);
      expect(outcome.pairingToClaim, isNull);
    });

    test(
      'success carries same payload for form apply and claim override',
      () async {
        final pairing = _pairingPayload(code: 'qr-code');

        final outcome = await coordinator.scan(
          isClaimingPairing: false,
          scanner: () async => pairing,
        );

        expect(outcome.kind, ProjectHomePairingFlowScanOutcomeKind.success);
        expect(outcome.pairingToApply, same(pairing));
        expect(outcome.pairingToClaim, same(pairing));
        expect(outcome.snackMessage, isNull);
      },
    );
  });

  group('claim outcome', () {
    test('success delegates exact request store and merge callbacks', () async {
      final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
      final pairing = _pairingPayload(code: 'manual-code');
      final request = ProjectHomePairingRequest(
        pairing: pairing,
        deviceName: 'Pixel Fold',
      );
      final paired = _pairedHost('paired');
      final merged = [paired, _pairedHost('other')];
      late GatewayPairingPayload seenPairing;
      late String seenDeviceName;
      late GatewayHostProfileStore seenStore;
      late GatewayPairedHost seenMergeProfile;

      final outcome = await coordinator.claim(
        request: request,
        store: store,
        claimAndStore: ({
          required pairing,
          required deviceName,
          required store,
          deviceId,
        }) async {
          seenPairing = pairing;
          seenDeviceName = deviceName;
          seenStore = store;
          return paired;
        },
        mergeProfiles: (profile) async {
          seenMergeProfile = profile;
          return merged;
        },
      );

      expect(outcome.kind, ProjectHomePairingFlowClaimOutcomeKind.success);
      expect(seenPairing, same(pairing));
      expect(seenDeviceName, 'Pixel Fold');
      expect(seenStore, same(store));
      expect(seenMergeProfile, same(paired));
      expect(outcome.paired, same(paired));
      expect(outcome.profiles, same(merged));
      expect(outcome.snackMessage, 'Gateway paired');
    });

    test('claim failure maps to failure without success data', () async {
      final outcome = await coordinator.claim(
        request: ProjectHomePairingRequest(
          pairing: _pairingPayload(code: 'manual-code'),
          deviceName: 'Phone',
        ),
        store: GatewayHostProfileStore(secureStore: MemorySecureStore()),
        claimAndStore: ({
          required pairing,
          required deviceName,
          required store,
          deviceId,
        }) async {
          throw StateError('claim failed');
        },
        mergeProfiles: (_) async {
          throw StateError('merge should not run');
        },
      );

      expect(outcome.kind, ProjectHomePairingFlowClaimOutcomeKind.failure);
      expect(outcome.snackMessage, 'Bad state: claim failed');
      expect(outcome.paired, isNull);
      expect(outcome.profiles, isNull);
    });

    test('merge failure maps to failure without success data', () async {
      var mergeCalls = 0;

      final outcome = await coordinator.claim(
        request: ProjectHomePairingRequest(
          pairing: _pairingPayload(code: 'manual-code'),
          deviceName: 'Phone',
        ),
        store: GatewayHostProfileStore(secureStore: MemorySecureStore()),
        claimAndStore: ({
          required pairing,
          required deviceName,
          required store,
          deviceId,
        }) async {
          return _pairedHost('paired');
        },
        mergeProfiles: (_) async {
          mergeCalls += 1;
          throw StateError('merge failed');
        },
      );

      expect(mergeCalls, 1);
      expect(outcome.kind, ProjectHomePairingFlowClaimOutcomeKind.failure);
      expect(outcome.snackMessage, 'Bad state: merge failed');
      expect(outcome.paired, isNull);
      expect(outcome.profiles, isNull);
    });
  });
}

GatewayPairingPayload _pairingPayload({required String code}) {
  return GatewayPairingPayload(
    pairingCode: code,
    claimEndpoint: Uri.parse('https://mobile.example.com/v1/pairing/claim'),
    routeProvider: RouteProviderKind.cloudflareTunnel,
    gatewayUrl: Uri.parse('https://mobile.example.com'),
    projectId: 'proj-demo',
    scopes: const {'view', 'focus', 'terminal_input'},
  );
}

GatewayPairedHost _pairedHost(String hostId) {
  return GatewayPairedHost(
    profile: GatewayHostProfile(
      hostId: hostId,
      deviceId: 'dev-phone',
      routeProvider: RouteProvider(
        kind: RouteProviderKind.cloudflareTunnel,
        gatewayUrl: Uri.parse('https://mobile.example.com'),
      ),
      scopes: const {'view'},
    ),
    deviceToken: '$hostId-token',
    projectId: hostId,
  );
}
