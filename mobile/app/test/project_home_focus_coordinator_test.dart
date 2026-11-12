import 'dart:async';

import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:ccb_mobile/features/project_home/project_home_focus_coordinator.dart';
import 'package:test/test.dart';

void main() {
  group('ProjectHomeFocusCoordinator', () {
    test('default timeout is 10 seconds', () {
      expect(
        const ProjectHomeFocusCoordinator().timeout,
        const Duration(seconds: 10),
      );
    });

    test(
      'agent stale view does not call repository and returns stale snack',
      () async {
        final repository = _RecordingFocusRepository();
        final outcome = await const ProjectHomeFocusCoordinator().focusAgent(
          repository: repository,
          view: _view(namespaceEpoch: null),
          agentName: 'lead',
        );

        expect(outcome.kind, ProjectHomeFocusOutcomeKind.stale);
        expect(outcome.snackMessage, 'Project view is stale');
        expect(repository.focusAgentCalls, isEmpty);
        expect(repository.focusWindowCalls, isEmpty);
      },
    );

    test(
      'window stale view does not call repository and returns stale snack',
      () async {
        final repository = _RecordingFocusRepository();
        final outcome = await const ProjectHomeFocusCoordinator().focusWindow(
          repository: repository,
          view: _view(namespaceEpoch: null),
          windowName: 'main',
          previousSelectedAgentName: 'mobile',
        );

        expect(outcome.kind, ProjectHomeFocusOutcomeKind.stale);
        expect(outcome.snackMessage, 'Project view is stale');
        expect(repository.focusAgentCalls, isEmpty);
        expect(repository.focusWindowCalls, isEmpty);
      },
    );

    test('agent success records exact repo args and selected agent', () async {
      final focusedView = _view(activeAgent: 'lead');
      final repository = _RecordingFocusRepository(focusedView: focusedView);
      final outcome = await const ProjectHomeFocusCoordinator().focusAgent(
        repository: repository,
        view: _view(),
        agentName: 'lead',
      );

      expect(outcome.kind, ProjectHomeFocusOutcomeKind.success);
      expect(outcome.focusedView, same(focusedView));
      expect(outcome.selectedAgentName, 'lead');
      expect(repository.focusAgentCalls, [('proj-demo', 'lead', 4)]);
      expect(repository.focusWindowCalls, isEmpty);
    });

    test(
      'window success selects first focused-view agent for window',
      () async {
        final focusedView = _view(activeWindow: 'review');
        final repository = _RecordingFocusRepository(focusedView: focusedView);
        final outcome = await const ProjectHomeFocusCoordinator().focusWindow(
          repository: repository,
          view: _view(),
          windowName: 'review',
          previousSelectedAgentName: 'mobile',
        );

        expect(outcome.kind, ProjectHomeFocusOutcomeKind.success);
        expect(outcome.focusedView, same(focusedView));
        expect(outcome.selectedAgentName, 'reviewer');
        expect(repository.focusWindowCalls, [('proj-demo', 'review', 4)]);
        expect(repository.focusAgentCalls, isEmpty);
      },
    );

    test(
      'window success preserves selected agent without matching agent',
      () async {
        final focusedView = _view(
          windows: const [
            CcbWindow(
              name: 'empty',
              label: 'empty',
              kind: 'agents',
              order: 0,
              active: true,
              agents: [],
            ),
          ],
        );
        final repository = _RecordingFocusRepository(focusedView: focusedView);
        final outcome = await const ProjectHomeFocusCoordinator().focusWindow(
          repository: repository,
          view: _view(),
          windowName: 'empty',
          previousSelectedAgentName: 'mobile',
        );

        expect(outcome.kind, ProjectHomeFocusOutcomeKind.success);
        expect(outcome.focusedView, same(focusedView));
        expect(outcome.selectedAgentName, 'mobile');
      },
    );

    test(
      'repository failure returns failure snack and original view',
      () async {
        final originalView = _view();
        final repository = _RecordingFocusRepository(
          focusError: StateError('focus failed'),
        );
        final outcome = await const ProjectHomeFocusCoordinator().focusAgent(
          repository: repository,
          view: originalView,
          agentName: 'lead',
        );

        expect(outcome.kind, ProjectHomeFocusOutcomeKind.failure);
        expect(outcome.originalView, same(originalView));
        expect(outcome.snackMessage, 'Bad state: focus failed');
      },
    );

    test(
      'window repository failure returns failure snack and original view',
      () async {
        final originalView = _view();
        final repository = _RecordingFocusRepository(
          focusError: StateError('window focus failed'),
        );
        final outcome = await const ProjectHomeFocusCoordinator().focusWindow(
          repository: repository,
          view: originalView,
          windowName: 'review',
          previousSelectedAgentName: 'mobile',
        );

        expect(outcome.kind, ProjectHomeFocusOutcomeKind.failure);
        expect(outcome.originalView, same(originalView));
        expect(outcome.snackMessage, 'Bad state: window focus failed');
        expect(repository.focusWindowCalls, [('proj-demo', 'review', 4)]);
      },
    );

    test('timeout returns failure snack and original view', () async {
      final originalView = _view();
      final repository = _RecordingFocusRepository(completeFocus: false);
      final outcome = await const ProjectHomeFocusCoordinator(
        timeout: Duration(milliseconds: 1),
      ).focusWindow(
        repository: repository,
        view: originalView,
        windowName: 'main',
        previousSelectedAgentName: 'mobile',
      );

      expect(outcome.kind, ProjectHomeFocusOutcomeKind.failure);
      expect(outcome.originalView, same(originalView));
      expect(outcome.snackMessage, contains('TimeoutException'));
      expect(repository.focusWindowCalls, [('proj-demo', 'main', 4)]);
    });
  });
}

class _RecordingFocusRepository implements MobileCcbRepository {
  _RecordingFocusRepository({
    CcbProjectView? focusedView,
    this.focusError,
    this.completeFocus = true,
  }) : focusedView = focusedView ?? _view();

  final CcbProjectView focusedView;
  final Object? focusError;
  final bool completeFocus;
  final focusAgentCalls = <(String, String, int)>[];
  final focusWindowCalls = <(String, String, int)>[];

  @override
  Future<CcbProjectView> focusAgent({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
  }) {
    focusAgentCalls.add((projectId, agent, namespaceEpoch));
    return _focusResult();
  }

  @override
  Future<CcbProjectView> focusWindow({
    required String projectId,
    required String window,
    required int namespaceEpoch,
  }) {
    focusWindowCalls.add((projectId, window, namespaceEpoch));
    return _focusResult();
  }

  Future<CcbProjectView> _focusResult() {
    final error = focusError;
    if (error != null) {
      return Future<CcbProjectView>.error(error);
    }
    if (!completeFocus) {
      return Completer<CcbProjectView>().future;
    }
    return Future.value(focusedView);
  }

  @override
  Future<CcbProjectView> getProjectView(String projectId) async => focusedView;

  @override
  Future<List<CcbProject>> listProjects() async => [focusedView.project];

  @override
  Future<CcbAgentConversation> getAgentConversation({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int limit = 50,
    String? cursor,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectLifecycleResult> requestLifecycle({
    required String projectId,
    required CcbLifecycleAction action,
  }) {
    throw UnimplementedError();
  }

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

  @override
  Future<CcbAgentMessageSubmitResult> submitAgentMessage(
    CcbAgentMessageSubmitRequest request,
  ) {
    throw UnimplementedError();
  }
}

CcbProjectView _view({
  int? namespaceEpoch = 4,
  String activeWindow = 'main',
  String activeAgent = 'mobile',
  List<CcbWindow> windows = _windows,
  List<CcbAgent>? agents,
}) {
  final resolvedAgents =
      agents ??
      [
        for (final agent in _agents)
          CcbAgent(
            name: agent.name,
            provider: agent.provider,
            window: agent.window,
            order: agent.order,
            active: agent.name == activeAgent,
            queueDepth: agent.queueDepth,
            paneId: agent.paneId,
            runtimeHealth: agent.runtimeHealth,
            activityState: agent.activityState,
          ),
      ];
  return CcbProjectView(
    project: const CcbProject(
      id: 'proj-demo',
      displayName: 'demo',
      root: '/srv/ccb/demo',
    ),
    namespaceEpoch: namespaceEpoch,
    tmuxSocketPath: '/tmp/ccb-demo/tmux.sock',
    tmuxSessionName: 'ccb-demo',
    activeWindow: activeWindow,
    activePaneId: '%2',
    windows: windows,
    agents: resolvedAgents,
    contentItems: const [],
    notifications: const [],
    terminalHistories: const {},
  );
}

const _windows = [
  CcbWindow(
    name: 'main',
    label: 'main',
    kind: 'agents',
    order: 0,
    active: true,
    agents: ['lead', 'mobile'],
  ),
  CcbWindow(
    name: 'review',
    label: 'review',
    kind: 'agents',
    order: 1,
    active: false,
    agents: ['reviewer'],
  ),
];

const _agents = [
  CcbAgent(
    name: 'lead',
    provider: 'codex',
    window: 'main',
    order: 0,
    active: false,
    queueDepth: 0,
  ),
  CcbAgent(
    name: 'mobile',
    provider: 'codex',
    window: 'main',
    order: 1,
    active: true,
    queueDepth: 1,
  ),
  CcbAgent(
    name: 'reviewer',
    provider: 'codex',
    window: 'review',
    order: 0,
    active: false,
    queueDepth: 0,
  ),
];
