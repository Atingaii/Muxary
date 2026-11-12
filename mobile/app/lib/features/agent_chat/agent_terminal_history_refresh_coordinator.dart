import '../../models/ccb_agent.dart';
import '../../models/ccb_project_view.dart';
import '../../repository/mobile_ccb_repository.dart';
import 'agent_chat_controller.dart';
import 'agent_terminal_history_loader.dart';

typedef AgentTerminalHistoryStateMutation =
    void Function(void Function() update);
typedef AgentTerminalHistoryIsMounted = bool Function();
typedef AgentTerminalHistoryTimelineNearEnd = bool Function(String agentName);
typedef AgentTerminalHistoryScrollTimelineToEnd =
    void Function(String agentName);

class AgentTerminalHistoryRefreshCoordinator {
  const AgentTerminalHistoryRefreshCoordinator({
    required AgentChatController chatController,
    required AgentTerminalHistoryIsMounted isMounted,
    required AgentTerminalHistoryStateMutation mutateState,
    required AgentTerminalHistoryTimelineNearEnd isTimelineNearEnd,
    required AgentTerminalHistoryScrollTimelineToEnd scrollTimelineToEnd,
  }) : _chatController = chatController,
       _isMounted = isMounted,
       _mutateState = mutateState,
       _isTimelineNearEnd = isTimelineNearEnd,
       _scrollTimelineToEnd = scrollTimelineToEnd;

  final AgentChatController _chatController;
  final AgentTerminalHistoryIsMounted _isMounted;
  final AgentTerminalHistoryStateMutation _mutateState;
  final AgentTerminalHistoryTimelineNearEnd _isTimelineNearEnd;
  final AgentTerminalHistoryScrollTimelineToEnd _scrollTimelineToEnd;

  Future<void> refresh({
    required MobileCcbRepository repository,
    required CcbAgent agent,
    required CcbProjectView view,
  }) async {
    final history = await AgentTerminalHistoryLoader(
      repository: repository,
    ).refresh(agent: agent, view: view);
    if (!_isMounted() || history == null) {
      return;
    }
    var changed = false;
    final shouldScroll = _isTimelineNearEnd(agent.name);
    _mutateState(() {
      changed = _chatController.setRefreshedTerminalHistory(
        agent.name,
        history,
      );
      if (changed) {
        _chatController.recordTimelineAppendState(
          agentName: agent.name,
          changed: true,
          shouldScroll: shouldScroll,
        );
      }
    });
    if (changed && shouldScroll) {
      _scrollTimelineToEnd(agent.name);
    }
  }

  Future<void> refreshAfterPaneSend({
    required MobileCcbRepository repository,
    required CcbAgent agent,
    required CcbProjectView view,
  }) async {
    await refresh(repository: repository, agent: agent, view: view);
  }
}
