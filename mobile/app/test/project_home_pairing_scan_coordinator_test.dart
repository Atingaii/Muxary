import 'package:ccb_mobile/features/project_home/project_home_pairing_scan_coordinator.dart';
import 'package:ccb_mobile/pairing/gateway_pairing.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:test/test.dart';

void main() {
  group('project home pairing scan coordinator', () {
    test('busy skips scanner', () async {
      var scanCalls = 0;

      final outcome = await const ProjectHomePairingScanCoordinator().scan(
        isClaimingPairing: true,
        scanner: () async {
          scanCalls += 1;
          return _payload();
        },
      );

      expect(scanCalls, 0);
      expect(outcome.kind, ProjectHomePairingScanOutcomeKind.busy);
      expect(outcome.pairing, isNull);
      expect(outcome.snackMessage, isNull);
    });

    test('cancel returns no-op', () async {
      var scanCalls = 0;

      final outcome = await const ProjectHomePairingScanCoordinator().scan(
        isClaimingPairing: false,
        scanner: () async {
          scanCalls += 1;
          return null;
        },
      );

      expect(scanCalls, 1);
      expect(outcome.kind, ProjectHomePairingScanOutcomeKind.canceled);
      expect(outcome.pairing, isNull);
      expect(outcome.snackMessage, isNull);
    });

    test('success returns exact payload', () async {
      final payload = _payload();

      final outcome = await const ProjectHomePairingScanCoordinator().scan(
        isClaimingPairing: false,
        scanner: () async => payload,
      );

      expect(outcome.kind, ProjectHomePairingScanOutcomeKind.success);
      expect(outcome.pairing, same(payload));
      expect(outcome.snackMessage, isNull);
    });

    test('scanner failure returns failure snack text', () async {
      final outcome = await const ProjectHomePairingScanCoordinator().scan(
        isClaimingPairing: false,
        scanner: () async {
          throw StateError('scanner failed');
        },
      );

      expect(outcome.kind, ProjectHomePairingScanOutcomeKind.failure);
      expect(outcome.pairing, isNull);
      expect(outcome.snackMessage, 'Bad state: scanner failed');
    });
  });
}

GatewayPairingPayload _payload() {
  return GatewayPairingPayload(
    pairingCode: 'qr-code',
    claimEndpoint: Uri.parse('https://mobile.example.com/v1/pairing/claim'),
    routeProvider: RouteProviderKind.cloudflareTunnel,
    gatewayUrl: Uri.parse('https://mobile.example.com'),
    projectId: 'proj-demo',
    scopes: const {'view', 'focus', 'terminal_input', 'lifecycle'},
  );
}
