import 'package:ccb_mobile/features/project_home/project_home_gateway_profiles.dart';
import 'package:ccb_mobile/features/project_home/project_home_profile_bootstrapper.dart';
import 'package:ccb_mobile/features/project_home/project_home_profile_loading.dart';
import 'package:ccb_mobile/pairing/gateway_pairing.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:test/test.dart';

import 'support/project_home_test_fakes.dart';

void main() {
  test('no-debug bootstrap returns load-required outcome', () async {
    final selected = _pairedHost(hostId: 'selected', deviceId: 'phone');
    final loaded = ProjectHomeProfileBootstrapResult(
      profiles: [selected],
      selectedProfile: selected,
    );
    final bootstrapper = _RecordingBootstrapper(loadResult: loaded);
    final coordinator = ProjectHomeProfileLoadingCoordinator(
      bootstrapper: bootstrapper,
    );

    final bootstrapOutcome = await coordinator.bootstrap(
      selectedProfile: selected,
      debugProfile: null,
      autoActivateDebugProfile: false,
    );
    final loadOutcome = await coordinator.load(selectedProfile: selected);

    expect(
      bootstrapOutcome.kind,
      ProjectHomeProfileBootstrapLoadKind.loadRequired,
    );
    expect(bootstrapper.bootstrapCalls, 0);
    expect(loadOutcome.kind, ProjectHomeProfileLoadKind.success);
    expect(loadOutcome.result?.selectedProfile, same(selected));
    expect(bootstrapper.loadCalls, 1);
  });

  test('debug bootstrap success carries auto-activate result', () async {
    final store = GatewayHostProfileStore(secureStore: MemorySecureStore());
    final stored = _pairedHost(hostId: 'stored', deviceId: 'phone');
    final debug = _pairedHost(hostId: 'debug', deviceId: 'phone');
    await store.save(stored);
    final coordinator = ProjectHomeProfileLoadingCoordinator(
      bootstrapper: ProjectHomeProfileBootstrapper(store: store),
    );

    final outcome = await coordinator.bootstrap(
      selectedProfile: stored,
      debugProfile: debug,
      autoActivateDebugProfile: true,
    );

    expect(outcome.kind, ProjectHomeProfileBootstrapLoadKind.success);
    expect(outcome.result?.selectedProfile, same(debug));
    expect(outcome.result?.activateProfile, same(debug));
    expect(outcome.result?.profiles.map(projectHomeGatewayProfileLabel), [
      'debug / phone / lan',
      'stored / phone / lan',
    ]);
  });

  test('bootstrap failure returns fallback intent without loading', () async {
    final bootstrapper = _RecordingBootstrapper(
      bootstrapError: StateError('x'),
    );
    final coordinator = ProjectHomeProfileLoadingCoordinator(
      bootstrapper: bootstrapper,
    );

    final outcome = await coordinator.bootstrap(
      selectedProfile: null,
      debugProfile: _pairedHost(hostId: 'debug', deviceId: 'phone'),
      autoActivateDebugProfile: true,
    );

    expect(outcome.kind, ProjectHomeProfileBootstrapLoadKind.fallbackToLoad);
    expect(outcome.result, isNull);
    expect(bootstrapper.bootstrapCalls, 1);
    expect(bootstrapper.loadCalls, 0);
  });

  test('load failure returns preservation outcome', () async {
    final bootstrapper = _RecordingBootstrapper(loadError: StateError('x'));
    final coordinator = ProjectHomeProfileLoadingCoordinator(
      bootstrapper: bootstrapper,
    );

    final outcome = await coordinator.load(
      selectedProfile: _pairedHost(hostId: 'selected', deviceId: 'phone'),
    );

    expect(outcome.kind, ProjectHomeProfileLoadKind.failure);
    expect(outcome.result, isNull);
  });

  test(
    'load preserves selection or chooses store first in store order',
    () async {
      final beta = _pairedHost(hostId: 'beta', deviceId: 'phone');
      final alpha = _pairedHost(hostId: 'alpha', deviceId: 'phone');
      final coordinator = ProjectHomeProfileLoadingCoordinator(
        bootstrapper: ProjectHomeProfileBootstrapper(
          store: _OrderedProfileStore([beta, alpha]),
        ),
      );

      final keptSelection = await coordinator.load(selectedProfile: alpha);
      final firstSelection = await coordinator.load(selectedProfile: null);

      expect(keptSelection.result?.selectedProfile, same(alpha));
      expect(firstSelection.result?.selectedProfile, same(beta));
      expect(
        firstSelection.result?.profiles.map(projectHomeGatewayProfileLabel),
        ['beta / phone / lan', 'alpha / phone / lan'],
      );
    },
  );
}

class _RecordingBootstrapper extends ProjectHomeProfileBootstrapper {
  _RecordingBootstrapper({this.loadResult, this.bootstrapError, this.loadError})
    : super(store: GatewayHostProfileStore(secureStore: MemorySecureStore()));

  final ProjectHomeProfileBootstrapResult? loadResult;
  final Object? bootstrapError;
  final Object? loadError;
  var bootstrapCalls = 0;
  var loadCalls = 0;

  @override
  Future<ProjectHomeProfileBootstrapResult> bootstrap({
    required GatewayPairedHost? selectedProfile,
    GatewayPairedHost? debugProfile,
    bool autoActivateDebugProfile = false,
  }) async {
    bootstrapCalls += 1;
    final error = bootstrapError;
    if (error != null) {
      throw error;
    }
    throw StateError('unexpected bootstrap call');
  }

  @override
  Future<ProjectHomeProfileBootstrapResult> load({
    required GatewayPairedHost? selectedProfile,
  }) async {
    loadCalls += 1;
    final error = loadError;
    if (error != null) {
      throw error;
    }
    return loadResult!;
  }
}

class _OrderedProfileStore extends GatewayHostProfileStore {
  _OrderedProfileStore(this._profiles)
    : super(secureStore: MemorySecureStore());

  final List<GatewayPairedHost> _profiles;

  @override
  Future<List<GatewayPairedHost>> list() async => List.of(_profiles);
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
        gatewayUrl: Uri.parse('http://$hostId.example.test'),
      ),
      scopes: const {'view'},
    ),
    deviceToken: '$hostId-token',
    projectId: hostId,
    createdAt: DateTime.utc(2026, 6, 22),
  );
}
