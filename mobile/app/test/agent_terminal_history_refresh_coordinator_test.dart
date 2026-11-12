import 'package:ccb_mobile/features/agent_chat/agent_chat_controller.dart';
import 'package:ccb_mobile/features/agent_chat/agent_terminal_history_refresh_coordinator.dart';
import 'package:ccb_mobile/transport/gateway_transport.dart';
import 'package:ccb_mobile/models/ccb_agent.dart';
import 'package:ccb_mobile/models/ccb_agent_conversation.dart';
import 'package:ccb_mobile/models/ccb_project.dart';
import 'package:ccb_mobile/models/ccb_project_lifecycle.dart';
import 'package:ccb_mobile/models/ccb_project_view.dart';
import 'package:ccb_mobile/models/readable_terminal_history.dart';
import 'package:ccb_mobile/repository/mobile_ccb_repository.dart';
import 'package:test/test.dart';

void main() {
  test(
    'applies refreshed history and scrolls when timeline is near end',
    () async {
      final chatController = AgentChatController();
      final repository = _HistoryRepository(response: _history('output'));
      final scrolledAgents = <String>[];
      final coordinator = _coordinator(
        chatController: chatController,
        isTimelineNearEnd: (_) => true,
        scrollTimelineToEnd: scrolledAgents.add,
      );

      await coordinator.refreshAfterPaneSend(
        repository: repository,
        agent: _leadAgent,
        view: _view(epoch: 7),
      );

      expect(repository.historyCalls, [
        const _HistoryCall('proj', 'lead', 7, 240),
      ]);
      expect(
        chatController.refreshedTerminalHistoryFor('lead')?.blocks.single.text,
        'output',
      );
      expect(chatController.hasNewMessages('lead'), isFalse);
      expect(scrolledAgents, const ['lead']);
    },
  );

  test(
    'marks new messages without scrolling when timeline is not near end',
    () async {
      final chatController = AgentChatController();
      final repository = _HistoryRepository(response: _history('output'));
      final scrolledAgents = <String>[];
      final coordinator = _coordinator(
        chatController: chatController,
        isTimelineNearEnd: (_) => false,
        scrollTimelineToEnd: scrolledAgents.add,
      );

      await coordinator.refreshAfterPaneSend(
        repository: repository,
        agent: _leadAgent,
        view: _view(epoch: 7),
      );

      expect(chatController.hasNewMessages('lead'), isTrue);
      expect(scrolledAgents, isEmpty);
    },
  );

  test(
    'unchanged history does not mark new messages or scroll again',
    () async {
      final chatController = AgentChatController();
      final repository = _HistoryRepository(response: _history('output'));
      final scrolledAgents = <String>[];
      var mutations = 0;
      final coordinator = AgentTerminalHistoryRefreshCoordinator(
        chatController: chatController,
        isMounted: () => true,
        mutateState: (update) {
          mutations += 1;
          update();
        },
        isTimelineNearEnd: (_) => true,
        scrollTimelineToEnd: scrolledAgents.add,
      );

      await coordinator.refreshAfterPaneSend(
        repository: repository,
        agent: _leadAgent,
        view: _view(epoch: 7),
      );
      await coordinator.refreshAfterPaneSend(
        repository: repository,
        agent: _leadAgent,
        view: _view(epoch: 7),
      );

      expect(repository.historyCalls, hasLength(2));
      expect(mutations, 2);
      expect(scrolledAgents, const ['lead']);
      expect(chatController.hasNewMessages('lead'), isFalse);
    },
  );

  test('changed history still marks new messages when not near end', () async {
    final chatController = AgentChatController();
    final repository = _MutableHistoryRepository(response: _history('first'));
    final coordinator = _coordinator(
      chatController: chatController,
      isTimelineNearEnd: (_) => false,
      scrollTimelineToEnd: (_) {},
    );

    await coordinator.refreshAfterPaneSend(
      repository: repository,
      agent: _leadAgent,
      view: _view(epoch: 7),
    );
    chatController.clearNewMessageFlag('lead');
    await coordinator.refreshAfterPaneSend(
      repository: repository,
      agent: _leadAgent,
      view: _view(epoch: 7),
    );
    expect(chatController.hasNewMessages('lead'), isFalse);

    repository.response = _history('second');
    await coordinator.refreshAfterPaneSend(
      repository: repository,
      agent: _leadAgent,
      view: _view(epoch: 7),
    );

    expect(chatController.hasNewMessages('lead'), isTrue);
  });

  test('ignores missing history without mutating state', () async {
    final chatController = AgentChatController();
    final repository = _HistoryRepository(response: null);
    final scrolledAgents = <String>[];
    var mutations = 0;
    final coordinator = AgentTerminalHistoryRefreshCoordinator(
      chatController: chatController,
      isMounted: () => true,
      mutateState: (update) {
        mutations += 1;
        update();
      },
      isTimelineNearEnd: (_) => true,
      scrollTimelineToEnd: scrolledAgents.add,
    );

    await coordinator.refreshAfterPaneSend(
      repository: repository,
      agent: _leadAgent,
      view: _view(epoch: 7),
    );

    expect(chatController.refreshedTerminalHistoryFor('lead'), isNull);
    expect(mutations, 0);
    expect(scrolledAgents, isEmpty);
  });
}

AgentTerminalHistoryRefreshCoordinator _coordinator({
  required AgentChatController chatController,
  required bool Function(String agentName) isTimelineNearEnd,
  required void Function(String agentName) scrollTimelineToEnd,
}) {
  return AgentTerminalHistoryRefreshCoordinator(
    chatController: chatController,
    isMounted: () => true,
    mutateState: (update) {
      update();
    },
    isTimelineNearEnd: isTimelineNearEnd,
    scrollTimelineToEnd: scrollTimelineToEnd,
  );
}

const _leadAgent = CcbAgent(
  name: 'lead',
  provider: 'codex',
  window: 'main',
  order: 0,
  active: true,
  queueDepth: 0,
  paneId: '%2',
);

CcbProjectView _view({required int? epoch}) {
  return CcbProjectView(
    project: const CcbProject(
      id: 'proj',
      displayName: 'Project',
      root: '/repo',
    ),
    namespaceEpoch: epoch,
    tmuxSocketPath: null,
    tmuxSessionName: null,
    activeWindow: 'main',
    activePaneId: '%2',
    windows: const [],
    agents: const [_leadAgent],
    contentItems: const [],
    notifications: const [],
    terminalHistories: const {},
  );
}

ReadableTerminalHistory _history(String text) {
  return ReadableTerminalHistory(
    agentName: 'lead',
    historyScope: 'tmux_scrollback',
    blocks: [ReadableTerminalBlock(id: 'out', type: 'output', text: text)],
  );
}

class _HistoryRepository implements MobileCcbRepository {
  _HistoryRepository({required this.response});

  final ReadableTerminalHistory? response;
  final historyCalls = <_HistoryCall>[];

  @override
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
  }) async {
    historyCalls.add(_HistoryCall(projectId, agent, namespaceEpoch, maxLines));
    return response;
  }

  @override
  Future<List<CcbProject>> listProjects() => throw UnimplementedError();

  @override
  Future<CcbProjectView> getProjectView(String projectId) {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectView> focusAgent({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectView> focusWindow({
    required String projectId,
    required String window,
    required int namespaceEpoch,
  }) {
    throw UnimplementedError();
  }

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
  Future<CcbAgentMessageSubmitResult> submitAgentMessage(
    CcbAgentMessageSubmitRequest request,
  ) {
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
}

class _MutableHistoryRepository extends _HistoryRepository {
  _MutableHistoryRepository({required super.response}) : _response = response;

  ReadableTerminalHistory? _response;

  set response(ReadableTerminalHistory? value) {
    _response = value;
  }

  @override
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
  }) async {
    historyCalls.add(_HistoryCall(projectId, agent, namespaceEpoch, maxLines));
    return _response;
  }
}

class _HistoryCall {
  const _HistoryCall(
    this.projectId,
    this.agent,
    this.namespaceEpoch,
    this.maxLines,
  );

  final String projectId;
  final String agent;
  final int namespaceEpoch;
  final int maxLines;

  @override
  bool operator ==(Object other) {
    return other is _HistoryCall &&
        other.projectId == projectId &&
        other.agent == agent &&
        other.namespaceEpoch == namespaceEpoch &&
        other.maxLines == maxLines;
  }

  @override
  int get hashCode => Object.hash(projectId, agent, namespaceEpoch, maxLines);

  @override
  String toString() {
    return '_HistoryCall($projectId, $agent, $namespaceEpoch, $maxLines)';
  }
}
