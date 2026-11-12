import '../../models/ccb_agent.dart';
import '../../models/ccb_agent_conversation.dart';
import '../../models/ccb_content_item.dart';
import '../../models/ccb_conversation_item.dart';
import '../../models/ccb_project_view.dart';
import '../../models/readable_terminal_history.dart';
import 'terminal_history_conversation_items.dart';

List<CcbConversationItem> selectedAgentTimelineItems({
  required CcbProjectView view,
  required CcbAgent agent,
  required List<CcbContentItem> contentItems,
  required ReadableTerminalHistory? terminalHistory,
  required CcbAgentConversation? remoteConversation,
  required List<CcbConversationItem> localMessages,
  bool preferSupplementalTerminalHistoryAtEnd = false,
  bool isLoadingConversation = false,
}) {
  final remoteItems = remoteConversation?.items;
  return [
    if (remoteItems != null) ...remoteItems,
    // SelectedAgentWorkspaceModel does not use this fallback for default Chat.
    if (remoteConversation == null && !isLoadingConversation)
      ...conversationItemsFor(
        view: view,
        agent: agent,
        contentItems: contentItems,
        terminalHistory: terminalHistory,
      ),
    ...localMessages,
  ];
}
