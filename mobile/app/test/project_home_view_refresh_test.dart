import 'dart:async';

import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:ccb_mobile/features/project_home/project_home_view_refresh.dart';
import 'package:test/test.dart';

import 'support/project_home_test_fakes.dart';

void main() {
  test(
    'success calls repository with exact project id and returns same view',
    () async {
      final view = CcbProjectView.fromProjectViewPayload(
        demoPayloadWithEpoch(5),
      );
      final repository = _RefreshRepository(refreshedView: view);
      const coordinator = ProjectHomeViewRefreshCoordinator();

      final outcome = await coordinator.refresh(
        repository: repository,
        projectId: 'proj-demo',
        selectedAgentName: 'mobile',
      );

      expect(repository.getProjectViewCalls, ['proj-demo']);
      expect(outcome.kind, ProjectHomeViewRefreshOutcomeKind.success);
      expect(outcome.refreshedView, same(view));
    },
  );

  test('success preserves selected agent when present', () async {
    final view = CcbProjectView.fromProjectViewPayload(demoPayloadWithEpoch(5));

    final outcome = await ProjectHomeViewRefreshCoordinator().refresh(
      repository: _RefreshRepository(refreshedView: view),
      projectId: 'proj-demo',
      selectedAgentName: 'mobile',
    );

    expect(outcome.selectedAgentName, 'mobile');
  });

  test('success clears selected agent when absent', () async {
    final view = _viewWithoutAgent('lead');

    final outcome = await ProjectHomeViewRefreshCoordinator().refresh(
      repository: _RefreshRepository(refreshedView: view),
      projectId: 'proj-demo',
      selectedAgentName: 'lead',
    );

    expect(outcome.selectedAgentName, isNull);
  });

  test('success preserves null selected agent', () async {
    final view = CcbProjectView.fromProjectViewPayload(demoPayloadWithEpoch(5));

    final outcome = await ProjectHomeViewRefreshCoordinator().refresh(
      repository: _RefreshRepository(refreshedView: view),
      projectId: 'proj-demo',
      selectedAgentName: null,
    );

    expect(outcome.selectedAgentName, isNull);
  });

  test('repository error returns failure snack', () async {
    final outcome = await ProjectHomeViewRefreshCoordinator().refresh(
      repository: _RefreshRepository(error: StateError('refresh failed')),
      projectId: 'proj-demo',
      selectedAgentName: 'mobile',
    );

    expect(outcome.kind, ProjectHomeViewRefreshOutcomeKind.failure);
    expect(outcome.refreshedView, isNull);
    expect(outcome.snackMessage, 'Bad state: refresh failed');
  });

  test('timeout returns failure outcome with short timeout', () async {
    final outcome = await ProjectHomeViewRefreshCoordinator(
      timeout: const Duration(milliseconds: 1),
    ).refresh(
      repository: _RefreshRepository(delay: const Duration(seconds: 1)),
      projectId: 'proj-demo',
      selectedAgentName: 'mobile',
    );

    expect(outcome.kind, ProjectHomeViewRefreshOutcomeKind.failure);
    expect(outcome.snackMessage, contains('TimeoutException'));
  });
}

class _RefreshRepository extends RecordingGatewayRepository {
  _RefreshRepository({this.refreshedView, this.error, this.delay});

  final CcbProjectView? refreshedView;
  final Object? error;
  final Duration? delay;
  final getProjectViewCalls = <String>[];

  @override
  Future<CcbProjectView> getProjectView(String projectId) async {
    getProjectViewCalls.add(projectId);
    final delay = this.delay;
    if (delay != null) {
      await Future<void>.delayed(delay);
    }
    final error = this.error;
    if (error != null) {
      throw error;
    }
    return refreshedView ??
        CcbProjectView.fromProjectViewPayload(demoPayloadWithEpoch(5));
  }
}

CcbProjectView _viewWithoutAgent(String agentName) {
  final payload = demoPayloadWithEpoch(5);
  final view = payload['view']! as Map<String, Object?>;
  final agents = view['agents']! as List<Object?>;
  agents.removeWhere((item) {
    final agent = item! as Map<String, Object?>;
    return agent['name'] == agentName;
  });
  return CcbProjectView.fromProjectViewPayload(payload);
}
