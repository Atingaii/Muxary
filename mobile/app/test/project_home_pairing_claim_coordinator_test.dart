import 'package:ccb_mobile/features/project_home/project_home_pairing_claim_coordinator.dart';
import 'package:ccb_mobile/features/project_home/project_home_pairing_request.dart';
import 'package:ccb_mobile/pairing/gateway_pairing.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:test/test.dart';

import 'support/project_home_test_fakes.dart';

void main() {
  group('project home pairing claim coordinator', () {
    test(
      'success calls claim with exact request and merges paired profile',
      () async {
        final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
        final request = _request();
        final paired = _pairedHost(hostId: 'paired', deviceId: 'phone');
        final merged = [
          _pairedHost(hostId: 'alpha', deviceId: 'tablet'),
          paired,
        ];
        GatewayPairingPayload? seenPairing;
        String? seenDeviceName;
        GatewayHostProfileStore? seenStore;
        GatewayPairedHost? seenMergePaired;

        final outcome = await const ProjectHomePairingClaimCoordinator()
            .complete(
              request: request,
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
              store: store,
              mergeProfiles: (paired) async {
                seenMergePaired = paired;
                return merged;
              },
            );

        expect(seenPairing, same(request.pairing));
        expect(seenDeviceName, request.deviceName);
        expect(seenStore, same(store));
        expect(seenMergePaired, same(paired));
        expect(outcome.kind, ProjectHomePairingClaimOutcomeKind.success);
        expect(outcome.paired, same(paired));
        expect(outcome.profiles, same(merged));
        expect(outcome.snackMessage, 'Gateway paired');
      },
    );

    test(
      'reuses a same-host same-route device id for the new QR claim',
      () async {
        final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
        await store.save(
          _pairedHost(hostId: 'proj-demo', deviceId: 'phone-old'),
        );
        String? seenDeviceId;

        final outcome = await const ProjectHomePairingClaimCoordinator()
            .complete(
              request: _request(projectId: 'proj-demo'),
              claimAndStore: ({
                required pairing,
                required deviceName,
                required store,
                deviceId,
              }) async {
                seenDeviceId = deviceId;
                return _pairedHost(hostId: 'proj-demo', deviceId: 'phone-old');
              },
              store: store,
              mergeProfiles: (paired) async => [paired],
            );

        expect(outcome.kind, ProjectHomePairingClaimOutcomeKind.success);
        expect(seenDeviceId, 'phone-old');
      },
    );

    test('claim failure returns failure snack and does not merge', () async {
      final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
      var mergeCalls = 0;

      final outcome = await const ProjectHomePairingClaimCoordinator().complete(
        request: _request(),
        claimAndStore: ({
          required pairing,
          required deviceName,
          required store,
          deviceId,
        }) async {
          throw StateError('claim failed');
        },
        store: store,
        mergeProfiles: (paired) async {
          mergeCalls += 1;
          return [paired];
        },
      );

      expect(mergeCalls, 0);
      expect(outcome.kind, ProjectHomePairingClaimOutcomeKind.failure);
      expect(outcome.paired, isNull);
      expect(outcome.profiles, isNull);
      expect(outcome.snackMessage, 'Bad state: claim failed');
    });

    test(
      'merge failure returns failure snack without success outcome',
      () async {
        final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
        final paired = _pairedHost(hostId: 'paired', deviceId: 'phone');

        final outcome = await const ProjectHomePairingClaimCoordinator()
            .complete(
              request: _request(),
              claimAndStore: ({
                required pairing,
                required deviceName,
                required store,
                deviceId,
              }) async {
                return paired;
              },
              store: store,
              mergeProfiles: (paired) async {
                throw StateError('merge failed');
              },
            );

        expect(outcome.kind, ProjectHomePairingClaimOutcomeKind.failure);
        expect(outcome.paired, isNull);
        expect(outcome.profiles, isNull);
        expect(outcome.snackMessage, 'Bad state: merge failed');
      },
    );
  });
}

ProjectHomePairingRequest _request({String? projectId}) {
  return ProjectHomePairingRequest(
    pairing: GatewayPairingPayload(
      pairingCode: 'pair-code',
      claimEndpoint: Uri.parse('http://127.0.0.1:8787/v1/pairing/claim'),
      routeProvider: RouteProviderKind.lan,
      gatewayUrl: Uri.parse('http://127.0.0.1:8787'),
      projectId: projectId,
      scopes: const {'view', 'content', 'focus', 'terminal_input', 'lifecycle'},
    ),
    deviceName: 'Pixel Fold',
  );
}

GatewayPairedHost _pairedHost({
  required String hostId,
  required String deviceId,
}) {
  return GatewayPairedHost(
    profile: GatewayHostProfile(
      hostId: hostId,
      deviceId: deviceId,
      routeProvider: RouteProvider(
        kind: RouteProviderKind.lan,
        gatewayUrl: Uri.parse('http://127.0.0.1:8787'),
      ),
      scopes: const {'view', 'content', 'focus'},
    ),
    deviceToken: 'device-token-$hostId-$deviceId',
    projectId: hostId,
  );
}
