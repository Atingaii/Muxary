import 'dart:async';
import 'dart:typed_data';

import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:ccb_mobile/features/project_home/project_home_profile_bootstrapper.dart';
import 'package:ccb_mobile/features/project_home/project_home_runtime_activation.dart';
import 'package:test/test.dart';

import 'support/project_home_test_fakes.dart';

void main() {
  test('paired runtime selection returns no-profile snack', () {
    final selection = selectProjectHomePairedRuntimeProfile(
      profiles: const [],
      selectedProfile: null,
    );

    expect(selection.kind, ProjectHomePairedRuntimeSelectionKind.noProfile);
    expect(selection.snackMessage, 'Pair a gateway profile first');
    expect(selection.activation, isNull);
  });

  test('selected profile beats first profile without membership filtering', () {
    final first = _pairedHost(hostId: 'first', deviceId: 'phone');
    final selected = _pairedHost(hostId: 'selected', deviceId: 'tablet');

    final selection = selectProjectHomePairedRuntimeProfile(
      profiles: [first],
      selectedProfile: selected,
    );

    expect(selection.kind, ProjectHomePairedRuntimeSelectionKind.activate);
    expect(selection.activation?.profile, same(selected));
  });

  test('null selected profile uses first profile in list order', () {
    final first = _pairedHost(hostId: 'beta', deviceId: 'phone');
    final second = _pairedHost(hostId: 'alpha', deviceId: 'tablet');

    final selection = selectProjectHomePairedRuntimeProfile(
      profiles: [first, second],
      selectedProfile: null,
    );

    expect(selection.activation?.profile, same(first));
  });

  test(
    'runtime activation follows restored selection for a newer route',
    () async {
      final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
      final oldRoute = _pairedHost(
        hostId: 'host-id',
        deviceId: 'old-device',
        gatewayUrl: Uri.parse('http://127.0.0.1:18899'),
      );
      final newRoute = _pairedHost(
        hostId: 'host-id',
        deviceId: 'new-device',
        gatewayUrl: Uri.parse('http://127.0.0.1:8787'),
      );
      await store.save(oldRoute);
      await store.save(newRoute);
      await store.markSuccessful(newRoute);

      final restored = await ProjectHomeProfileBootstrapper(
        store: store,
      ).load(selectedProfile: null);
      final selection = selectProjectHomePairedRuntimeProfile(
        profiles: restored.profiles,
        selectedProfile: restored.selectedProfile,
      );

      expect(selection.kind, ProjectHomePairedRuntimeSelectionKind.activate);
      expect(selection.activation?.profile.profile.deviceId, 'new-device');
      expect(selection.activation?.gatewayUrlText, 'http://127.0.0.1:8787');
    },
  );

  test('activation data uses project id when present', () {
    final profile = _pairedHost(
      hostId: 'host-id',
      deviceId: 'phone',
      projectId: 'project-id',
    );

    final data = activateProjectHomeGatewayProfile(profile);

    expect(data.activeProjectId, 'project-id');
  });

  test('activation data falls back to host id', () {
    final profile = _pairedHost(hostId: 'host-id', deviceId: 'phone');

    final data = activateProjectHomeGatewayProfile(profile);

    expect(data.activeProjectId, 'host-id');
  });

  test('activation data preserves gateway URL text and route kind', () {
    final profile = _pairedHost(
      hostId: 'project',
      deviceId: 'phone',
      gatewayUrl: Uri.parse('https://mobile.example.com'),
      routeKind: RouteProviderKind.cloudflareTunnel,
    );

    final data = activateProjectHomeGatewayProfile(profile);

    expect(data.gatewayUrlText, 'https://mobile.example.com');
    expect(data.routeKind, RouteProviderKind.cloudflareTunnel);
    expect(data.profile, same(profile));
  });

  test('fake reset carries default project id', () {
    final reset = resetProjectHomeFakeRuntime(defaultProjectId: 'proj-demo');

    expect(reset.defaultProjectId, 'proj-demo');
  });

  test('fake runtime session uses repository and default project id', () async {
    final repository = _RecordingRepository();
    final session = const ProjectHomeRuntimeSessionCoordinator().activateFake(
      repository: repository,
      defaultProjectId: 'proj-demo',
    );

    expect(session.repository, same(repository));
    expect(session.activeProjectId, 'proj-demo');
    expect(session.terminalTransport, isNull);
    await session.viewFuture;
    expect(repository.getProjectViewCalls, ['proj-demo']);
  });

  test(
    'gateway runtime session calls factories once with same profile',
    () async {
      final profile = _pairedHost(
        hostId: 'host-id',
        deviceId: 'phone',
        projectId: 'project-id',
      );
      final repository = _RecordingRepository();
      final terminalTransport = _RecordingTerminalTransport();
      final repositoryProfiles = <GatewayPairedHost>[];
      final terminalProfiles = <GatewayPairedHost>[];

      final session = const ProjectHomeRuntimeSessionCoordinator()
          .activateGateway(
            activation: activateProjectHomeGatewayProfile(profile),
            repositoryFactory: (profile) {
              repositoryProfiles.add(profile);
              return repository;
            },
            terminalTransportFactory: (profile) {
              terminalProfiles.add(profile);
              return terminalTransport;
            },
          );

      expect(repositoryProfiles, [same(profile)]);
      expect(terminalProfiles, [same(profile)]);
      expect(session.activation.profile, same(profile));
      expect(session.repository, same(repository));
      expect(session.preferredProjectId, 'project-id');
      expect(session.terminalTransport, same(terminalTransport));
      await session.projectsFuture;
      expect(repository.listProjectsCalls, 1);
      expect(repository.healthCalls, 1);
      expect(repository.deviceCalls, 1);
      expect(repository.getProjectViewCalls, isEmpty);
    },
  );

  test(
    'gateway runtime session carries host id fallback preferred project id',
    () async {
      final profile = _pairedHost(hostId: 'host-id', deviceId: 'phone');
      final repository = _RecordingRepository();

      final session = const ProjectHomeRuntimeSessionCoordinator()
          .activateGateway(
            activation: activateProjectHomeGatewayProfile(profile),
            repositoryFactory: (_) => repository,
            terminalTransportFactory: (_) => _RecordingTerminalTransport(),
          );

      expect(session.preferredProjectId, 'host-id');
      await session.projectsFuture;
      expect(repository.listProjectsCalls, 1);
      expect(repository.healthCalls, 1);
      expect(repository.deviceCalls, 1);
      expect(repository.getProjectViewCalls, isEmpty);
    },
  );

  test(
    'gateway runtime fails invalid profile token before project list',
    () async {
      final profile = _pairedHost(hostId: 'host-id', deviceId: 'phone');
      final repository =
          _RecordingRepository()
            ..deviceError = GatewayHttpException(
              Uri.parse('http://host-id.local:8787/v1/devices/me'),
              401,
              'unauthorized',
            );

      final session = const ProjectHomeRuntimeSessionCoordinator()
          .activateGateway(
            activation: activateProjectHomeGatewayProfile(profile),
            repositoryFactory: (_) => repository,
            terminalTransportFactory: (_) => _RecordingTerminalTransport(),
          );

      await expectLater(
        session.projectsFuture,
        throwsA(
          isA<ProjectHomeGatewayActivationException>()
              .having(
                (error) => error.kind,
                'kind',
                ProjectHomeGatewayActivationFailureKind.tokenInvalid,
              )
              .having(
                (error) => error.toString(),
                'message',
                contains('Re-pair'),
              ),
        ),
      );
      expect(repository.healthCalls, 1);
      expect(repository.deviceCalls, 1);
      expect(repository.listProjectsCalls, 0);
    },
  );

  test(
    'gateway runtime reports unreachable profile before project list',
    () async {
      final profile = _pairedHost(hostId: 'host-id', deviceId: 'phone');
      final repository =
          _RecordingRepository()
            ..healthError = TimeoutException('route timed out');

      final session = const ProjectHomeRuntimeSessionCoordinator()
          .activateGateway(
            activation: activateProjectHomeGatewayProfile(profile),
            repositoryFactory: (_) => repository,
            terminalTransportFactory: (_) => _RecordingTerminalTransport(),
          );

      await expectLater(
        session.projectsFuture,
        throwsA(
          isA<ProjectHomeGatewayActivationException>().having(
            (error) => error.kind,
            'kind',
            ProjectHomeGatewayActivationFailureKind.gatewayUnreachable,
          ),
        ),
      );
      expect(repository.healthCalls, 1);
      expect(repository.deviceCalls, 0);
      expect(repository.listProjectsCalls, 0);
    },
  );

  test('403 scope denial preserves paired identity semantics', () {
    final error = projectHomeGatewayActivationExceptionFor(
      GatewayHttpException(
        Uri.parse('http://host.local/v1/devices/me'),
        403,
        'device scope denied',
      ),
    );

    expect(error.kind, ProjectHomeGatewayActivationFailureKind.scopeDenied);
    expect(error.message, isNot(contains('Re-pair')));
  });

  test('gateway runtime session times out project list load', () async {
    final profile = _pairedHost(
      hostId: 'host-id',
      deviceId: 'phone',
      projectId: 'project-id',
    );
    final repository = _HangingRepository();

    final session = const ProjectHomeRuntimeSessionCoordinator()
        .activateGateway(
          activation: activateProjectHomeGatewayProfile(profile),
          repositoryFactory: (_) => repository,
          terminalTransportFactory: (_) => _RecordingTerminalTransport(),
          projectListTimeout: const Duration(milliseconds: 1),
        );

    await expectLater(session.projectsFuture, throwsA(isA<TimeoutException>()));
    expect(repository.listProjectsCalls, 1);
    expect(repository.healthCalls, 1);
    expect(repository.deviceCalls, 1);
    expect(repository.getProjectViewCalls, isEmpty);
  });
}

GatewayPairedHost _pairedHost({
  required String hostId,
  required String deviceId,
  String? projectId,
  Uri? gatewayUrl,
  RouteProviderKind routeKind = RouteProviderKind.lan,
}) {
  return GatewayPairedHost(
    profile: GatewayHostProfile(
      hostId: hostId,
      deviceId: deviceId,
      routeProvider: RouteProvider(
        kind: routeKind,
        gatewayUrl: gatewayUrl ?? Uri.parse('http://$hostId.local:8787'),
      ),
      scopes: const {'view', 'focus', 'terminal_input'},
    ),
    deviceToken: 'token-$hostId-$deviceId',
    projectId: projectId,
  );
}

class _RecordingRepository
    implements
        MobileCcbRepository,
        MobileGatewayProfileHealthProbe,
        MobileGatewayCoreRouteVerifier {
  final getProjectViewCalls = <String>[];
  var listProjectsCalls = 0;
  var healthCalls = 0;
  var deviceCalls = 0;
  Object? healthError;
  Object? deviceError;
  String healthStatus = 'ok';

  @override
  Future<GatewayHealth> health() async {
    healthCalls += 1;
    final error = healthError;
    if (error != null) {
      throw error;
    }
    return GatewayHealth(
      status: healthStatus,
      serverTime: DateTime.utc(2026, 7, 5, 12),
    );
  }

  @override
  Future<GatewayDevice> device() async {
    deviceCalls += 1;
    final error = deviceError;
    if (error != null) {
      throw error;
    }
    return GatewayDevice(
      deviceId: 'phone',
      projectId: 'project-id',
      scopes: const {'view', 'focus', 'terminal_input'},
      routeProvider: RouteProviderKind.lan,
      revoked: false,
    );
  }

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

  @override
  Future<CcbProjectView> getProjectView(String projectId) async {
    getProjectViewCalls.add(projectId);
    return CcbProjectView.fromProjectViewPayload(demoProjectViewFixture);
  }

  @override
  Future<List<CcbProject>> listProjects() async {
    listProjectsCalls += 1;
    return [
      CcbProjectView.fromProjectViewPayload(demoProjectViewFixture).project,
    ];
  }

  @override
  Future<CcbProjectView> focusAgent({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
  }) => throw UnimplementedError();

  @override
  Future<CcbProjectView> focusWindow({
    required String projectId,
    required String window,
    required int namespaceEpoch,
  }) => throw UnimplementedError();

  @override
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
  }) => throw UnimplementedError();

  @override
  Future<CcbAgentConversation> getAgentConversation({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int limit = 50,
    String? cursor,
  }) => throw UnimplementedError();

  @override
  Future<CcbAgentMessageSubmitResult> submitAgentMessage(
    CcbAgentMessageSubmitRequest request,
  ) => throw UnimplementedError();

  @override
  Future<CcbProjectLifecycleResult> requestLifecycle({
    required String projectId,
    required CcbLifecycleAction action,
  }) => throw UnimplementedError();

  @override
  Future<GatewayFileUploadResult> uploadFile({
    required String projectId,
    required String agentName,
    required String fileName,
    required String mimeType,
    required List<int> bytes,
  }) async {
    throw UnimplementedError();
  }

  @override
  Future<List<int>> downloadFile({
    required String projectId,
    required String agentName,
    required String fileId,
  }) async {
    throw UnimplementedError();
  }
}

class _HangingRepository extends _RecordingRepository {
  @override
  Future<List<CcbProject>> listProjects() {
    listProjectsCalls += 1;
    return Completer<List<CcbProject>>().future;
  }
}

class _RecordingTerminalTransport implements TerminalTransport {
  @override
  Future<TerminalSession> open(TerminalOpenRequest request) async {
    return _RecordingTerminalSession();
  }
}

class _RecordingTerminalSession implements TerminalSession {
  @override
  String get launchedCommand => 'test';

  @override
  Stream<Uint8List> get output => const Stream.empty();

  @override
  Future<void> close() async {}

  @override
  Future<void> paste(String text) async {}

  @override
  Future<void> reconnect() async {}

  @override
  Future<void> resize(TerminalGeometry geometry) async {}

  @override
  Future<void> writeBytes(List<int> bytes) async {}
}
