import 'dart:async';

import 'package:ccb_mobile/features/agent_chat/agent_chat_controller.dart';
import 'package:ccb_mobile/features/agent_chat/agent_conversation_refresh_coordinator.dart';
import 'package:ccb_mobile/models/ccb_agent.dart';
import 'package:ccb_mobile/models/ccb_agent_conversation.dart';
import 'package:ccb_mobile/models/ccb_conversation_item.dart';
import 'package:ccb_mobile/transport/gateway_transport.dart';
import 'package:ccb_mobile/models/ccb_project.dart';
import 'package:ccb_mobile/models/ccb_project_lifecycle.dart';
import 'package:ccb_mobile/models/ccb_project_view.dart';
import 'package:ccb_mobile/models/readable_terminal_history.dart';
import 'package:ccb_mobile/repository/mobile_ccb_repository.dart';
import 'package:test/test.dart';

void main() {
  test('loads applies and scrolls changed active conversation', () async {
    final chatController = AgentChatController();
    final repository = _ConversationRepository(
      response: _conversation(body: 'ready'),
    );
    final scrolledAgents = <String>[];
    final coordinator = _coordinator(
      chatController: chatController,
      isTimelineNearEnd: (_) => true,
      scrollTimelineToEnd: scrolledAgents.add,
    );

    await coordinator.load(
      repository: repository,
      view: _view(epoch: 7),
      agentName: 'lead',
    );

    expect(repository.conversationCalls, [
      const _ConversationCall('proj', 'lead', 7),
    ]);
    expect(chatController.isLoadingConversation('lead'), isFalse);
    expect(
      chatController.remoteConversationFor('lead')?.items.single.body,
      ['ready'].single,
    );
    expect(chatController.hasNewMessages('lead'), isFalse);
    expect(scrolledAgents, const ['lead']);
  });

  test(
    'records new message flag when changed conversation arrives off bottom',
    () async {
      final chatController = AgentChatController();
      final repository = _ConversationRepository(
        responses: [
          _conversation(id: 'reply-1', body: 'ready'),
          _conversation(id: 'reply-2', body: 'updated'),
        ],
      );
      final scrolledAgents = <String>[];
      final coordinator = _coordinator(
        chatController: chatController,
        isTimelineNearEnd: (_) => false,
        scrollTimelineToEnd: scrolledAgents.add,
      );

      await coordinator.load(
        repository: repository,
        view: _view(epoch: 7),
        agentName: 'lead',
      );
      scrolledAgents.clear();

      await coordinator.load(
        repository: repository,
        view: _view(epoch: 7),
        agentName: 'lead',
      );

      expect(chatController.hasNewMessages('lead'), isTrue);
      expect(scrolledAgents, isEmpty);
    },
  );

  test(
    'coalesces overlapping latest loads into a trailing conversation reload',
    () async {
      final chatController = AgentChatController();
      final repository = _BlockingConversationRepository(
        first: _conversation(id: 'reply-1', body: 'first'),
        trailing: _conversation(id: 'reply-2', body: 'latest'),
      );
      final coordinator = _coordinator(chatController: chatController);

      final firstLoad = coordinator.load(
        repository: repository,
        view: _view(epoch: 7),
        agentName: 'lead',
      );
      await Future<void>.delayed(Duration.zero);

      await coordinator.load(
        repository: repository,
        view: _view(epoch: 7),
        agentName: 'lead',
      );
      await coordinator.load(
        repository: repository,
        view: _view(epoch: 7),
        agentName: 'lead',
      );

      expect(repository.conversationCalls, [
        const _ConversationCall('proj', 'lead', 7),
      ]);

      repository.completeFirst();
      await firstLoad;

      expect(repository.conversationCalls, [
        const _ConversationCall('proj', 'lead', 7),
        const _ConversationCall('proj', 'lead', 7),
      ]);
      expect(
        chatController.remoteConversationFor('lead')?.items.single.body,
        'latest',
      );
    },
  );

  test('stores load errors and clears loading state', () async {
    final chatController = AgentChatController();
    final repository = _ConversationRepository(
      response: StateError('gateway down'),
    );
    final coordinator = _coordinator(chatController: chatController);

    await coordinator.load(
      repository: repository,
      view: _view(epoch: 7),
      agentName: 'lead',
    );

    expect(chatController.isLoadingConversation('lead'), isFalse);
    expect(
      chatController.conversationErrorFor('lead'),
      contains('gateway down'),
    );
  });

  test(
    'loads older page with cursor and prepends without new-message flag',
    () async {
      final chatController = AgentChatController();
      chatController.applyRemoteConversation(
        agentName: 'lead',
        shouldScroll: true,
        conversation: _conversation(
          id: 'reply-new',
          body: 'new',
          nextCursor: '2',
        ),
      );
      final repository = _ConversationRepository(
        response: _conversation(id: 'reply-old', body: 'old', nextCursor: null),
      );
      final scrolledAgents = <String>[];
      final coordinator = _coordinator(
        chatController: chatController,
        isTimelineNearEnd: (_) => false,
        scrollTimelineToEnd: scrolledAgents.add,
      );

      final changed = await coordinator.loadOlder(
        repository: repository,
        view: _view(epoch: 7),
        agentName: 'lead',
      );

      expect(changed, isTrue);
      expect(repository.conversationCalls, [
        const _ConversationCall('proj', 'lead', 7, cursor: '2'),
      ]);
      expect(
        chatController
            .remoteConversationFor('lead')
            ?.items
            .map((item) => item.id),
        ['reply-old', 'reply-new'],
      );
      expect(chatController.hasOlderConversation('lead'), isFalse);
      expect(chatController.hasNewMessages('lead'), isFalse);
      expect(scrolledAgents, isEmpty);
    },
  );

  test('skips older load when no cursor is available', () async {
    final chatController = AgentChatController();
    chatController.applyRemoteConversation(
      agentName: 'lead',
      shouldScroll: true,
      conversation: _conversation(id: 'reply-new', body: 'new'),
    );
    final repository = _ConversationRepository(
      response: _conversation(id: 'reply-old', body: 'old'),
    );
    final coordinator = _coordinator(chatController: chatController);

    final changed = await coordinator.loadOlder(
      repository: repository,
      view: _view(epoch: 7),
      agentName: 'lead',
    );

    expect(changed, isFalse);
    expect(repository.conversationCalls, isEmpty);
    expect(
      chatController
          .remoteConversationFor('lead')
          ?.items
          .map((item) => item.id),
      ['reply-new'],
    );
  });
}

AgentConversationRefreshCoordinator _coordinator({
  required AgentChatController chatController,
  bool Function(String agentName)? isTimelineNearEnd,
  void Function(String agentName)? scrollTimelineToEnd,
}) {
  return AgentConversationRefreshCoordinator(
    chatController: chatController,
    isMounted: () => true,
    mutateState: (update) {
      update();
    },
    isTimelineNearEnd: isTimelineNearEnd ?? (_) => true,
    scrollTimelineToEnd: scrollTimelineToEnd ?? (_) {},
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

CcbAgentConversation _conversation({
  String id = 'reply',
  required String body,
  String? nextCursor,
}) {
  return CcbAgentConversation(
    projectId: 'proj',
    agentName: 'lead',
    namespaceEpoch: 7,
    items: [
      CcbConversationItem(
        id: id,
        agentName: 'lead',
        kind: CcbConversationItemKind.agentReply,
        title: 'Agent reply',
        body: body,
      ),
    ],
    nextCursor: nextCursor,
    generatedAt: DateTime.utc(2026, 6, 22),
  );
}

class _ConversationRepository implements MobileCcbRepository {
  _ConversationRepository({Object? response, List<Object>? responses})
    : _responses = responses ?? [if (response != null) response];

  final List<Object> _responses;
  final conversationCalls = <_ConversationCall>[];
  var _responseIndex = 0;

  @override
  Future<CcbAgentConversation> getAgentConversation({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int limit = 50,
    String? cursor,
  }) async {
    conversationCalls.add(
      _ConversationCall(
        projectId,
        agent,
        namespaceEpoch,
        limit: limit,
        cursor: cursor,
      ),
    );
    if (_responseIndex >= _responses.length) {
      throw StateError('missing queued conversation response');
    }
    final response = _responses[_responseIndex];
    _responseIndex += 1;
    if (response is Exception) {
      throw response;
    }
    if (response is Error) {
      throw response;
    }
    return response as CcbAgentConversation;
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
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
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

class _BlockingConversationRepository extends _ConversationRepository {
  _BlockingConversationRepository({required this.first, required this.trailing})
    : super(responses: const []);

  final CcbAgentConversation first;
  final CcbAgentConversation trailing;
  final _firstGate = Completer<void>();

  void completeFirst() {
    if (!_firstGate.isCompleted) {
      _firstGate.complete();
    }
  }

  @override
  Future<CcbAgentConversation> getAgentConversation({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int limit = 50,
    String? cursor,
  }) async {
    conversationCalls.add(
      _ConversationCall(
        projectId,
        agent,
        namespaceEpoch,
        limit: limit,
        cursor: cursor,
      ),
    );
    if (conversationCalls.length == 1) {
      await _firstGate.future;
      return first;
    }
    return trailing;
  }
}

class _ConversationCall {
  const _ConversationCall(
    this.projectId,
    this.agent,
    this.namespaceEpoch, {
    this.limit = 50,
    this.cursor,
  });

  final String projectId;
  final String agent;
  final int namespaceEpoch;
  final int limit;
  final String? cursor;

  @override
  bool operator ==(Object other) {
    return other is _ConversationCall &&
        other.projectId == projectId &&
        other.agent == agent &&
        other.namespaceEpoch == namespaceEpoch &&
        other.limit == limit &&
        other.cursor == cursor;
  }

  @override
  int get hashCode =>
      Object.hash(projectId, agent, namespaceEpoch, limit, cursor);

  @override
  String toString() {
    return '_ConversationCall($projectId, $agent, $namespaceEpoch, '
        'limit: $limit, cursor: $cursor)';
  }
}
