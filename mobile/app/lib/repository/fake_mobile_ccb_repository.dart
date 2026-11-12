import '../fixtures/project_view_fixture.dart';
import '../models/ccb_agent.dart';
import '../models/ccb_agent_conversation.dart';
import '../models/ccb_conversation_item.dart';
import '../models/ccb_project.dart';
import '../models/ccb_project_lifecycle.dart';
import '../models/ccb_project_view.dart';
import '../models/readable_terminal_history.dart';
import '../transport/gateway_transport.dart';
import 'mobile_ccb_repository.dart';

class FakeMobileCcbRepository implements MobileCcbRepository {
  FakeMobileCcbRepository({required Map<String, Object?> projectViewPayload})
    : _view = CcbProjectView.fromProjectViewPayload(projectViewPayload);

  factory FakeMobileCcbRepository.demo() {
    return FakeMobileCcbRepository(projectViewPayload: demoProjectViewFixture);
  }

  final CcbProjectView _view;
  final Set<String> _failedFakeSubmitKeys = {};
  final Map<String, List<int>> _files = {};
  final Map<String, List<CcbConversationItem>> _submittedMessages = {};

  @override
  Future<List<CcbProject>> listProjects() async => [_view.project];

  @override
  Future<CcbProjectView> getProjectView(String projectId) async {
    _requireProject(projectId);
    return _view;
  }

  @override
  Future<CcbProjectView> focusAgent({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
  }) async {
    _requireProject(projectId);
    _requireEpoch(namespaceEpoch);
    if (_view.agentByName(agent) == null) {
      throw ArgumentError.value(agent, 'agent', 'unknown CCB agent');
    }
    return _view;
  }

  @override
  Future<CcbProjectView> focusWindow({
    required String projectId,
    required String window,
    required int namespaceEpoch,
  }) async {
    _requireProject(projectId);
    _requireEpoch(namespaceEpoch);
    final exists = _view.windows.any((item) => item.name == window);
    if (!exists) {
      throw ArgumentError.value(window, 'window', 'unknown CCB window');
    }
    return _view;
  }

  @override
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
  }) async {
    _requireProject(projectId);
    _requireEpoch(namespaceEpoch);
    return _view.terminalHistoryForAgent(agent);
  }

  @override
  Future<CcbAgentConversation> getAgentConversation({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int limit = 50,
    String? cursor,
  }) async {
    _requireProject(projectId);
    _requireEpoch(namespaceEpoch);
    final selectedAgent = _view.agentByName(agent);
    if (selectedAgent == null) {
      throw ArgumentError.value(agent, 'agent', 'unknown CCB agent');
    }
    final items = _conversationItemsForAgent(agent).take(limit).toList();
    return CcbAgentConversation(
      projectId: projectId,
      agentName: agent,
      namespaceEpoch: namespaceEpoch,
      items: items,
      generatedAt: DateTime.utc(2026, 6, 21),
    );
  }

  @override
  Future<CcbAgentMessageSubmitResult> submitAgentMessage(
    CcbAgentMessageSubmitRequest request,
  ) async {
    _requireProject(request.projectId);
    _requireEpoch(request.namespaceEpoch);
    if (_view.agentByName(request.agentName) == null) {
      throw ArgumentError.value(
        request.agentName,
        'agentName',
        'unknown CCB agent',
      );
    }
    await Future<void>.delayed(const Duration(milliseconds: 80));
    final shouldFailOnce =
        request.body.toLowerCase().contains('fail') &&
        !_failedFakeSubmitKeys.contains(request.idempotencyKey);
    if (shouldFailOnce) {
      _failedFakeSubmitKeys.add(request.idempotencyKey);
      throw StateError('fake message submit failed');
    }
    final message = CcbConversationItem.userMessage(
      id: request.idempotencyKey,
      agentName: request.agentName,
      body: request.body,
      attachments: request.attachments,
      state: CcbConversationDeliveryState.sent,
    );
    _submittedMessages.putIfAbsent(request.agentName, () => []).add(message);
    final conversation = await getAgentConversation(
      projectId: request.projectId,
      agent: request.agentName,
      namespaceEpoch: request.namespaceEpoch,
    );
    return CcbAgentMessageSubmitResult(
      accepted: true,
      idempotencyKey: request.idempotencyKey,
      messageId: request.idempotencyKey,
      state: CcbConversationDeliveryState.sent,
      message: message,
      conversation: conversation,
    );
  }

  @override
  Future<CcbProjectLifecycleResult> requestLifecycle({
    required String projectId,
    required CcbLifecycleAction action,
  }) async {
    _requireProject(projectId);
    return CcbProjectLifecycleResult(
      projectId: projectId,
      action: action,
      state: action == CcbLifecycleAction.stop ? 'stopping' : 'running',
      effect: switch (action) {
        CcbLifecycleAction.wake => 'already_running',
        CcbLifecycleAction.open => 'opened',
        CcbLifecycleAction.close => 'mobile_view_closed',
        CcbLifecycleAction.stop => 'ccbd_stop_requested',
      },
      ccbAuthority: true,
      tmuxKillServer: false,
      forced: false,
      updatedAt: DateTime.utc(2026, 6, 21),
      result:
          action == CcbLifecycleAction.stop
              ? const {'stopped': true, 'force': false}
              : const {},
      view:
          action == CcbLifecycleAction.wake || action == CcbLifecycleAction.open
              ? _view
              : null,
    );
  }

  void _requireProject(String projectId) {
    if (projectId != _view.project.id) {
      throw ArgumentError.value(projectId, 'projectId', 'unknown CCB project');
    }
  }

  void _requireEpoch(int namespaceEpoch) {
    if (namespaceEpoch != _view.namespaceEpoch) {
      throw StateError('ProjectView namespace epoch is stale');
    }
  }

  List<CcbConversationItem> _conversationItemsForAgent(String agentName) {
    final agent = _view.agentByName(agentName);
    if (agent == null) {
      return const [];
    }
    return [
      CcbConversationItem.status(
        id: 'status-$agentName',
        agentName: agentName,
        title: 'Agent status',
        body: _agentStatusSummary(agent),
      ),
      for (final content in _view.contentForAgent(agentName))
        CcbConversationItem.agentReplyFromContent(
          agentName: agentName,
          content: content,
        ),
      if (_view.terminalHistoryForAgent(agentName) != null)
        CcbConversationItem.terminalHistory(agentName: agentName),
      ...(_submittedMessages[agentName] ?? const []),
    ];
  }

  @override
  Future<GatewayFileUploadResult> uploadFile({
    required String projectId,
    required String agentName,
    required String fileName,
    required String mimeType,
    required List<int> bytes,
  }) async {
    _requireProject(projectId);
    if (_view.agentByName(agentName) == null) {
      throw ArgumentError.value(agentName, 'agentName', 'unknown CCB agent');
    }
    if (bytes.isEmpty) {
      throw ArgumentError.value(bytes.length, 'bytes', 'file is empty');
    }
    final id = 'fake-file-${_files.length + 1}';
    _files[id] = List<int>.unmodifiable(bytes);
    return GatewayFileUploadResult(
      fileId: id,
      fileName: fileName,
      mimeType: mimeType,
      sizeBytes: bytes.length,
    );
  }

  @override
  Future<List<int>> downloadFile({
    required String projectId,
    required String agentName,
    required String fileId,
  }) async {
    _requireProject(projectId);
    if (_view.agentByName(agentName) == null) {
      throw ArgumentError.value(agentName, 'agentName', 'unknown CCB agent');
    }
    final bytes = _files[fileId];
    if (bytes == null) {
      throw ArgumentError.value(fileId, 'fileId', 'unknown CCB attachment');
    }
    return bytes;
  }
}

String _agentStatusSummary(CcbAgent agent) {
  final state = agent.activityState ?? 'idle';
  final health = agent.runtimeHealth ?? 'unknown';
  final queue = agent.queueDepth;
  if (queue > 0) {
    return '$state, $health, $queue queued item${queue == 1 ? '' : 's'}';
  }
  return '$state, $health, no queued items';
}
