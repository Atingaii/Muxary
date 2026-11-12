import 'agent_chat_controller.dart';
import 'pane_chat_controller.dart';
import 'pane_chat_event_messages.dart';

typedef AgentPaneEventStateMutation = void Function(void Function() update);
typedef AgentPaneEventIsMounted = bool Function();
typedef AgentPaneEventTimelineNearEnd = bool Function(String agentName);
typedef AgentPaneEventScrollTimelineToEnd = void Function(String agentName);

class AgentPaneEventCoordinator {
  const AgentPaneEventCoordinator({
    required AgentChatController chatController,
    required AgentPaneEventIsMounted isMounted,
    required AgentPaneEventStateMutation mutateState,
    required AgentPaneEventTimelineNearEnd isTimelineNearEnd,
    required AgentPaneEventScrollTimelineToEnd scrollTimelineToEnd,
  }) : _chatController = chatController,
       _isMounted = isMounted,
       _mutateState = mutateState,
       _isTimelineNearEnd = isTimelineNearEnd,
       _scrollTimelineToEnd = scrollTimelineToEnd;

  final AgentChatController _chatController;
  final AgentPaneEventIsMounted _isMounted;
  final AgentPaneEventStateMutation _mutateState;
  final AgentPaneEventTimelineNearEnd _isTimelineNearEnd;
  final AgentPaneEventScrollTimelineToEnd _scrollTimelineToEnd;

  bool apply(PaneChatEvent event) {
    if (!_isMounted()) {
      return false;
    }
    final agentName = event.agentName;
    final update = localMessagesAfterPaneChatEvent(
      event: event,
      currentMessages: _chatController.localMessagesFor(agentName),
      nextOutputId: () => _chatController.nextTerminalLiveOutputId(agentName),
    );
    if (!update.changed) {
      return false;
    }
    final shouldScroll = _isTimelineNearEnd(agentName);
    _mutateState(() {
      _chatController.updateLocalMessages(agentName, (_) => update.messages);
      _chatController.recordTimelineAppendState(
        agentName: agentName,
        changed: true,
        shouldScroll: shouldScroll,
      );
    });
    if (shouldScroll) {
      _scrollTimelineToEnd(agentName);
    }
    return true;
  }
}
