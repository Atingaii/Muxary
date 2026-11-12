import 'package:ccb_mobile/features/project_home/project_home_route_diagnostics.dart';
import 'package:ccb_mobile/pairing/gateway_pairing.dart';
import 'package:ccb_mobile/transport/gateway_route_diagnostics.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:test/test.dart';

void main() {
  test('no selected profile returns snack and does not start checking', () {
    final outcome = const ProjectHomeRouteDiagnosticsCoordinator().begin(
      selectedProfile: null,
      checking: false,
    );

    expect(outcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.noProfile);
    expect(outcome.snackMessage, 'Select a gateway profile first');
    expect(outcome.report, isNull);
  });

  test('busy route check is a no-op', () {
    final outcome = const ProjectHomeRouteDiagnosticsCoordinator().begin(
      selectedProfile: _pairedHost(),
      checking: true,
    );

    expect(outcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.busy);
    expect(outcome.snackMessage, isNull);
    expect(outcome.report, isNull);
  });

  test('ready route check lets screen own checking state mutation', () {
    final outcome = const ProjectHomeRouteDiagnosticsCoordinator().begin(
      selectedProfile: _pairedHost(),
      checking: false,
    );

    expect(outcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.ready);
    expect(outcome.snackMessage, isNull);
    expect(outcome.report, isNull);
  });

  test(
    'screen orchestration starts checking before diagnostics call',
    () async {
      final events = <String>[];
      final profile = _pairedHost();
      final coordinator = const ProjectHomeRouteDiagnosticsCoordinator();
      final beginOutcome = coordinator.begin(
        selectedProfile: profile,
        checking: false,
      );

      expect(beginOutcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.ready);
      events.add('start-checking');
      final outcome = await coordinator.complete(
        profile: profile,
        diagnostics: (checkedProfile) async {
          events.add('diagnostics');
          return _report(checkedProfile, 'Route ready');
        },
      );

      expect(outcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.success);
      expect(events, ['start-checking', 'diagnostics']);
    },
  );

  test('success returns report and summary snack', () async {
    var calls = 0;
    final profile = _pairedHost();
    final outcome = await const ProjectHomeRouteDiagnosticsCoordinator()
        .complete(
          profile: profile,
          diagnostics: (checkedProfile) async {
            calls += 1;
            expect(checkedProfile, same(profile));
            return _report(checkedProfile, 'Route ready');
          },
        );

    expect(outcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.success);
    expect(outcome.report?.summary, 'Route ready');
    expect(outcome.snackMessage, 'Route ready');
    expect(calls, 1);
  });

  test('failure returns error snack and no replacement report', () async {
    var calls = 0;
    final outcome = await const ProjectHomeRouteDiagnosticsCoordinator()
        .complete(
          profile: _pairedHost(),
          diagnostics: (profile) async {
            calls += 1;
            throw StateError('route failed');
          },
        );

    expect(outcome.kind, ProjectHomeRouteDiagnosticsOutcomeKind.failure);
    expect(outcome.report, isNull);
    expect(outcome.snackMessage, 'Bad state: route failed');
    expect(calls, 1);
  });
}

GatewayPairedHost _pairedHost() {
  return GatewayPairedHost(
    profile: GatewayHostProfile(
      hostId: 'proj-demo',
      deviceId: 'device',
      routeProvider: RouteProvider(
        kind: RouteProviderKind.lan,
        gatewayUrl: Uri.parse('http://127.0.0.1:8787'),
      ),
      scopes: const {'view'},
    ),
    deviceToken: 'device-secret',
    projectId: 'proj-demo',
  );
}

GatewayRouteDiagnosticReport _report(
  GatewayPairedHost profile,
  String message,
) {
  return GatewayRouteDiagnosticReport(
    profile: profile.profile,
    checkedProjectId: profile.projectId,
    checks: [
      GatewayRouteDiagnosticCheck(
        code: 'route_ready',
        ok: message == 'Route ready',
        message: message,
      ),
    ],
  );
}
