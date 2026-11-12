import 'package:flutter_test/flutter_test.dart';

import 'package:ccb_mobile/features/agent_chat/pane_chat_controller.dart';
import 'package:ccb_mobile/features/agent_chat/pane_chat_event_messages.dart';
import 'package:ccb_mobile/models/ccb_conversation_item.dart';

void main() {
  test('does not map pane output into conversation messages', () {
    var outputIds = 0;
    final current = [
      CcbConversationItem.userMessage(
        id: 'user',
        agentName: 'lead',
        body: 'hello',
      ),
    ];

    final update = localMessagesAfterPaneChatEvent(
      event: const PaneChatEvent(
        agentName: 'lead',
        kind: PaneChatEventKind.output,
        body: '\x1B[31mstreaming line\x1B[0m',
      ),
      currentMessages: current,
      nextOutputId: () => 'out-${outputIds++}',
    );

    expect(update.changed, isFalse);
    expect(update.messages, same(current));
    expect(outputIds, 0);
  });

  test('does not map pane notices into conversation messages', () {
    final current = [
      CcbConversationItem.userMessage(
        id: 'user',
        agentName: 'lead',
        body: 'hello',
      ),
    ];

    final update = localMessagesAfterPaneChatEvent(
      event: const PaneChatEvent(
        agentName: 'lead',
        kind: PaneChatEventKind.notice,
        body: 'TerminalTransportException(expired)',
      ),
      currentMessages: current,
      nextOutputId: () => 'output',
    );

    expect(update.changed, isFalse);
    expect(update.messages, same(current));
  });
}
