import 'dart:async';

import 'package:ccb_mobile/features/project_home/mobile_connection_supervisor.dart';
import 'package:ccb_mobile/notifications/task_completion_notifications.dart';
import 'package:ccb_mobile/pairing/gateway_pairing.dart';
import 'package:ccb_mobile/repository/gateway_mobile_ccb_repository.dart';
import 'package:ccb_mobile/transport/http_gateway_transport.dart';
import 'package:ccb_mobile/transport/gateway_transport.dart';
import 'package:ccb_mobile/transport/gateway_connection_outcome.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:test/test.dart';

void main() {
  test('temporary route failure keeps profile and retries to online', () async {
    final states = <MobileConnectionState>[];
    final repository = _ProbeRepository()..fail = true;
    final supervisor = MobileConnectionSupervisor(
      onChanged: (value) => states.add(value.state),
      initialDelay: Duration.zero,
      maxDelay: Duration.zero,
    );
    supervisor.start(profile: _profile(), probe: repository);
    await Future<void>.delayed(Duration.zero);
    expect(states, contains(MobileConnectionState.reconnecting));
    repository.fail = false;
    supervisor.foregroundResume();
    await Future<void>.delayed(Duration.zero);
    expect(supervisor.snapshot.state, MobileConnectionState.online);
    supervisor.dispose();
  });

  test('only explicit credential disposition is authentication required', () {
    final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
    supervisor.start(profile: _profile(), probe: _ProbeRepository());
    supervisor.reportFailure(
      GatewayHttpException(Uri(), 401, 'revoked'),
      auth: MobileAuthDisposition.credentialInvalid,
    );
    expect(
      supervisor.snapshot.state,
      MobileConnectionState.authenticationRequired,
    );
    supervisor.dispose();
  });

  test(
    'probe classifies an invalid credential as authentication required',
    () async {
      final repository =
          _ProbeRepository()
            ..healthError = GatewayHttpException(Uri(), 401, 'revoked');
      final supervisor = MobileConnectionSupervisor(
        onChanged: (_) {},
        initialDelay: const Duration(seconds: 1),
        maxDelay: const Duration(seconds: 1),
      );

      supervisor.start(profile: _profile(), probe: repository);
      await Future<void>.delayed(const Duration(milliseconds: 5));

      expect(
        supervisor.snapshot.state,
        MobileConnectionState.authenticationRequired,
      );
      supervisor.dispose();
    },
  );

  test('403 scope denial and mutation failure keep the stored session', () {
    final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
    supervisor.start(profile: _profile(), probe: _ProbeRepository());
    supervisor.reportFailure(
      GatewayHttpException(Uri(), 403, 'scope denied'),
      auth: MobileAuthDisposition.scopeDenied,
      kind: MobileTransportKind.mutation,
    );
    expect(
      supervisor.snapshot.state,
      isNot(MobileConnectionState.authenticationRequired),
    );
    supervisor.dispose();
  });

  test('outcome adapter classifies timeout, 401, 403, and recovery', () {
    final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
    supervisor.start(profile: _profile(), probe: _ProbeRepository());
    final adapter = MobileConnectionOutcomeAdapter(
      supervisor: supervisor,
      isCurrent: () => true,
    );

    adapter.failed(
      GatewayConnectionOperation.coreRead,
      TimeoutException('route'),
    );
    expect(supervisor.snapshot.state, MobileConnectionState.reconnecting);
    adapter.succeeded(GatewayConnectionOperation.coreRead);
    expect(supervisor.snapshot.state, MobileConnectionState.online);
    adapter.failed(
      GatewayConnectionOperation.mutation,
      GatewayHttpException(Uri(), 403, 'scope denied'),
    );
    expect(
      supervisor.snapshot.state,
      isNot(MobileConnectionState.authenticationRequired),
    );
    adapter.failed(
      GatewayConnectionOperation.coreRead,
      GatewayHttpException(Uri(), 401, 'invalid token'),
    );
    expect(
      supervisor.snapshot.state,
      MobileConnectionState.authenticationRequired,
    );
    supervisor.dispose();
  });

  test(
    'data timeout probes core once without entering global reconnect',
    () async {
      final states = <MobileConnectionState>[];
      final gate = Completer<void>();
      final repository = _ProbeRepository()..gate = gate;
      final supervisor = MobileConnectionSupervisor(
        onChanged: (value) => states.add(value.state),
      );
      supervisor.start(
        profile: _profile(),
        probe: repository,
        probeImmediately: false,
      );
      final adapter = MobileConnectionOutcomeAdapter(
        supervisor: supervisor,
        isCurrent: () => true,
      );

      adapter.failed(
        GatewayConnectionOperation.dataRead,
        TimeoutException('conversation'),
      );
      adapter.failed(
        GatewayConnectionOperation.dataRead,
        TimeoutException('conversation wrapper'),
      );
      await Future<void>.delayed(Duration.zero);

      expect(repository.healthCalls, 1);
      expect(states, isNot(contains(MobileConnectionState.reconnecting)));
      gate.complete();
      await Future<void>.delayed(Duration.zero);
      expect(supervisor.snapshot.state, MobileConnectionState.online);
      supervisor.dispose();
    },
  );

  test(
    'data timeout enters reconnect only when the core probe fails',
    () async {
      final repository = _ProbeRepository()..fail = true;
      final supervisor = MobileConnectionSupervisor(
        onChanged: (_) {},
        initialDelay: const Duration(hours: 1),
        maxDelay: const Duration(hours: 1),
      );
      supervisor.start(
        profile: _profile(),
        probe: repository,
        probeImmediately: false,
      );
      final adapter = MobileConnectionOutcomeAdapter(
        supervisor: supervisor,
        isCurrent: () => true,
      );

      adapter.failed(
        GatewayConnectionOperation.dataRead,
        TimeoutException('conversation'),
      );
      await Future<void>.delayed(Duration.zero);

      expect(supervisor.snapshot.state, MobileConnectionState.reconnecting);
      supervisor.dispose();
    },
  );

  test('data read 401 still requires authentication', () {
    final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
    supervisor.start(
      profile: _profile(),
      probe: _ProbeRepository(),
      probeImmediately: false,
    );
    final adapter = MobileConnectionOutcomeAdapter(
      supervisor: supervisor,
      isCurrent: () => true,
    );

    adapter.failed(
      GatewayConnectionOperation.dataRead,
      GatewayHttpException(Uri(), 401, 'invalid token'),
    );

    expect(
      supervisor.snapshot.state,
      MobileConnectionState.authenticationRequired,
    );
    supervisor.dispose();
  });

  test('outcome adapter ignores a stale profile generation', () {
    final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
    supervisor.start(profile: _profile(), probe: _ProbeRepository());
    final adapter = MobileConnectionOutcomeAdapter(
      supervisor: supervisor,
      isCurrent: () => false,
    );
    adapter.failed(
      GatewayConnectionOperation.coreRead,
      TimeoutException('stale'),
    );
    expect(supervisor.snapshot.state, MobileConnectionState.connecting);
    supervisor.dispose();
  });

  test(
    'stream connected probes core HTTP and does not clear reconnect on failure',
    () async {
      final repository = _ProbeRepository()..fail = true;
      final supervisor = MobileConnectionSupervisor(
        onChanged: (_) {},
        initialDelay: const Duration(seconds: 1),
        maxDelay: const Duration(seconds: 1),
      );
      supervisor.start(
        profile: _profile(),
        probe: repository,
        probeImmediately: false,
      );
      supervisor.reportFailure(TimeoutException('core route unavailable'));
      final adapter = MobileConnectionOutcomeAdapter(
        supervisor: supervisor,
        isCurrent: () => true,
      );

      adapter.succeeded(GatewayConnectionOperation.stream);
      await Future<void>.delayed(const Duration(milliseconds: 20));

      expect(repository.healthCalls, 1);
      expect(supervisor.snapshot.state, MobileConnectionState.reconnecting);
      supervisor.dispose();
    },
  );

  test(
    'structured stream auth errors retain only scope-denied credentials',
    () {
      final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
      supervisor.start(profile: _profile(), probe: _ProbeRepository());
      final adapter = MobileConnectionOutcomeAdapter(
        supervisor: supervisor,
        isCurrent: () => true,
      );

      adapter.failed(
        GatewayConnectionOperation.stream,
        GatewayTaskCompletionNotificationStreamException(Uri(), 403, 'scope'),
      );
      expect(supervisor.snapshot.state, MobileConnectionState.degraded);

      adapter.failed(
        GatewayConnectionOperation.stream,
        Exception('invalid token'),
      );
      expect(
        supervisor.snapshot.state,
        isNot(MobileConnectionState.authenticationRequired),
      );

      adapter.failed(
        GatewayConnectionOperation.stream,
        GatewayTaskCompletionNotificationStreamException(Uri(), 401, 'revoked'),
      );
      expect(
        supervisor.snapshot.state,
        MobileConnectionState.authenticationRequired,
      );
      supervisor.dispose();
    },
  );

  test(
    'old same-profile activation terminal outcomes are generation fenced',
    () {
      final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
      supervisor.start(profile: _profile(), probe: _ProbeRepository());
      var generation = 1;
      final oldAdapter = MobileConnectionOutcomeAdapter(
        supervisor: supervisor,
        isCurrent: () => generation == 1,
      );
      generation = 2;
      supervisor.reportFailure(TimeoutException('new activation route failed'));

      oldAdapter.succeeded(GatewayConnectionOperation.terminal);
      oldAdapter.failed(GatewayConnectionOperation.terminal, Exception('old'));

      expect(supervisor.snapshot.state, MobileConnectionState.reconnecting);
      supervisor.dispose();
    },
  );

  test('terminal ready probes but cannot mask a core HTTP outage', () async {
    final repository = _ProbeRepository()..fail = true;
    final supervisor = MobileConnectionSupervisor(
      onChanged: (_) {},
      initialDelay: const Duration(seconds: 1),
      maxDelay: const Duration(seconds: 1),
    );
    supervisor.start(
      profile: _profile(),
      probe: repository,
      probeImmediately: false,
    );
    supervisor.reportFailure(TimeoutException('core route unavailable'));
    final adapter = MobileConnectionOutcomeAdapter(
      supervisor: supervisor,
      isCurrent: () => true,
    );

    adapter.succeeded(GatewayConnectionOperation.terminal);
    await Future<void>.delayed(const Duration(milliseconds: 20));
    adapter.failed(GatewayConnectionOperation.terminal, StateError('closed'));

    expect(repository.healthCalls, 1);
    expect(supervisor.snapshot.state, MobileConnectionState.reconnecting);
    supervisor.dispose();
  });

  test(
    'probe scope denial degrades without invalidating credentials',
    () async {
      final repository =
          _ProbeRepository()
            ..healthError = GatewayHttpException(Uri(), 403, 'scope denied');
      final supervisor = MobileConnectionSupervisor(onChanged: (_) {});

      supervisor.start(profile: _profile(), probe: repository);
      await Future<void>.delayed(Duration.zero);

      expect(supervisor.snapshot.state, MobileConnectionState.degraded);
      supervisor.dispose();
    },
  );

  test(
    'deferred startup uses activation result instead of duplicate probe',
    () {
      final repository = _ProbeRepository();
      final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
      supervisor.start(
        profile: _profile(),
        probe: repository,
        probeImmediately: false,
      );

      expect(repository.healthCalls, 0);
      expect(supervisor.snapshot.state, MobileConnectionState.connecting);

      supervisor.reportSuccess();
      expect(supervisor.snapshot.state, MobileConnectionState.online);
      supervisor.dispose();
    },
  );

  test('sse failure degrades while a bounded core probe is pending', () async {
    final states = <MobileConnectionState>[];
    final repository = _ProbeRepository();
    final supervisor = MobileConnectionSupervisor(
      onChanged: (value) => states.add(value.state),
      initialDelay: Duration.zero,
      maxDelay: Duration.zero,
    );
    supervisor.start(
      profile: _profile(),
      probe: repository,
      probeImmediately: false,
    );
    supervisor.reportFailure(
      TimeoutException('sse disconnected'),
      kind: MobileTransportKind.sse,
    );

    expect(supervisor.snapshot.state, MobileConnectionState.degraded);
    await Future<void>.delayed(const Duration(milliseconds: 5));
    expect(repository.healthCalls, 1);
    expect(supervisor.snapshot.state, MobileConnectionState.online);
    supervisor.dispose();
  });

  test(
    'profile switch drains a queued latest probe after stale completion',
    () async {
      final first = _ProbeRepository()..gate = Completer<void>();
      final second = _ProbeRepository();
      final supervisor = MobileConnectionSupervisor(onChanged: (_) {});
      supervisor.start(profile: _profile(), probe: first);
      supervisor.start(profile: _profile(device: 'new'), probe: second);
      first.gate!.complete();
      await Future<void>.delayed(Duration.zero);
      await Future<void>.delayed(Duration.zero);
      expect(second.healthCalls, greaterThan(0));
      expect(supervisor.snapshot.state, MobileConnectionState.online);
      supervisor.dispose();
    },
  );
}

GatewayPairedHost _profile({String device = 'device'}) => GatewayPairedHost(
  profile: GatewayHostProfile(
    hostId: 'host',
    deviceId: device,
    scopes: const {'view'},
    routeProvider: RouteProvider(
      kind: RouteProviderKind.lan,
      gatewayUrl: Uri.parse('http://127.0.0.1'),
    ),
  ),
  deviceToken: 'token',
);

class _ProbeRepository
    implements MobileGatewayProfileHealthProbe, MobileGatewayCoreRouteVerifier {
  bool fail = false;
  Object? healthError;
  Completer<void>? gate;
  var healthCalls = 0;
  @override
  Future<GatewayHealth> health() async {
    healthCalls += 1;
    await gate?.future;
    if (healthError case final error?) throw error;
    if (fail) throw TimeoutException('route');
    return GatewayHealth(
      status: 'ok',
      serverTime: DateTime.utc(2026),
      capabilities: {},
    );
  }

  @override
  Future<GatewayDevice> device() async => GatewayDevice(
    deviceId: 'd',
    projectId: 'p',
    revoked: false,
    scopes: {},
    routeProvider: RouteProviderKind.lan,
  );

  @override
  Future<void> verifyCoreRoutes() async {
    final health = await this.health();
    if (health.status.toLowerCase() != 'ok') {
      throw GatewayHttpException(Uri(), 503, 'gateway health is degraded');
    }
    final device = await this.device();
    if (device.revoked) {
      throw GatewayHttpException(Uri(), 401, 'device revoked');
    }
  }
}
