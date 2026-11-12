import 'package:ccb_mobile/features/agent_chat/agent_chat_controller.dart';
import 'package:ccb_mobile/features/agent_chat/agent_pane_event_coordinator.dart';
import 'package:ccb_mobile/features/agent_chat/pane_chat_controller.dart';
import 'package:test/test.dart';

void main() {
  test('does not render pane output as local conversation messages', () {
    final chatController = AgentChatController();
    final scrolledAgents = <String>[];
    var mutations = 0;
    final coordinator = _coordinator(
      chatController: chatController,
      isTimelineNearEnd: (_) => true,
      scrollTimelineToEnd: scrolledAgents.add,
      onMutation: () {
        mutations += 1;
      },
    );

    final changed = coordinator.apply(
      const PaneChatEvent(
        agentName: 'lead',
        kind: PaneChatEventKind.output,
        body: 'hello',
      ),
    );

    expect(changed, isFalse);
    expect(chatController.localMessagesFor('lead'), isEmpty);
    expect(chatController.hasNewMessages('lead'), isFalse);
    expect(scrolledAgents, isEmpty);
    expect(mutations, 0);
  });

  test('ignores terminal notices without mutating state or scrolling', () {
    final chatController = AgentChatController();
    final scrolledAgents = <String>[];
    var mutations = 0;
    final coordinator = _coordinator(
      chatController: chatController,
      isTimelineNearEnd: (_) => true,
      scrollTimelineToEnd: scrolledAgents.add,
      onMutation: () {
        mutations += 1;
      },
    );

    final changed = coordinator.apply(
      const PaneChatEvent(
        agentName: 'lead',
        kind: PaneChatEventKind.notice,
        body: 'Terminal stream closed',
      ),
    );

    expect(changed, isFalse);
    expect(chatController.localMessagesFor('lead'), isEmpty);
    expect(mutations, 0);
    expect(scrolledAgents, isEmpty);
  });

  test('ignores output when unmounted', () {
    final chatController = AgentChatController();
    final coordinator = AgentPaneEventCoordinator(
      chatController: chatController,
      isMounted: () => false,
      mutateState: (update) {
        throw StateError('should not mutate');
      },
      isTimelineNearEnd: (_) => true,
      scrollTimelineToEnd: (_) {
        throw StateError('should not scroll');
      },
    );

    final changed = coordinator.apply(
      const PaneChatEvent(
        agentName: 'lead',
        kind: PaneChatEventKind.output,
        body: 'hello',
      ),
    );

    expect(changed, isFalse);
    expect(chatController.localMessagesFor('lead'), isEmpty);
  });
}

AgentPaneEventCoordinator _coordinator({
  required AgentChatController chatController,
  required bool Function(String agentName) isTimelineNearEnd,
  required void Function(String agentName) scrollTimelineToEnd,
  required void Function() onMutation,
}) {
  return AgentPaneEventCoordinator(
    chatController: chatController,
    isMounted: () => true,
    mutateState: (update) {
      onMutation();
      update();
    },
    isTimelineNearEnd: isTimelineNearEnd,
    scrollTimelineToEnd: scrollTimelineToEnd,
  );
}
