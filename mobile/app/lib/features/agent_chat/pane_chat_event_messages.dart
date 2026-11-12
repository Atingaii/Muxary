import '../../models/ccb_conversation_item.dart';
import 'pane_chat_controller.dart';

typedef PaneChatEventIdFactory = String Function();

class PaneChatEventMessageUpdate {
  const PaneChatEventMessageUpdate({
    required this.changed,
    required this.messages,
  });

  final bool changed;
  final List<CcbConversationItem> messages;
}

PaneChatEventMessageUpdate localMessagesAfterPaneChatEvent({
  required PaneChatEvent event,
  required List<CcbConversationItem> currentMessages,
  required PaneChatEventIdFactory nextOutputId,
}) {
  switch (event.kind) {
    case PaneChatEventKind.output:
      return PaneChatEventMessageUpdate(
        changed: false,
        messages: currentMessages,
      );
    case PaneChatEventKind.notice:
      return _localMessagesAfterNoticeEvent(currentMessages: currentMessages);
  }
}

PaneChatEventMessageUpdate _localMessagesAfterNoticeEvent({
  required List<CcbConversationItem> currentMessages,
}) {
  return PaneChatEventMessageUpdate(changed: false, messages: currentMessages);
}
