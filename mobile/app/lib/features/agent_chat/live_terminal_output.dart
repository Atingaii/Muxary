import '../../models/ccb_conversation_item.dart';

const maxLiveTerminalOutputChars = 800;
const maxLiveTerminalOutputLines = 8;

final _ansiOscPattern = RegExp(r'\x1B\][^\x07]*(?:\x07|\x1B\\)');
final _ansiControlPattern = RegExp(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])');

List<CcbConversationItem> appendOrMergeLiveTerminalOutput(
  List<CcbConversationItem> items,
  CcbConversationItem item,
) {
  if (items.isEmpty || !isLiveTerminalOutputItem(items.last)) {
    return [...items, item];
  }
  final previous = items.last;
  final mergedBody = compactLiveTerminalOutput(
    '${previous.body}\n${item.body}',
  );
  return [
    ...items.take(items.length - 1),
    CcbConversationItem(
      id: previous.id,
      agentName: previous.agentName,
      kind: previous.kind,
      title: previous.title,
      body: mergedBody,
      format: previous.format,
      state: previous.state,
      contentId: previous.contentId,
      source: previous.source,
    ),
  ];
}

bool isLiveTerminalOutputItem(CcbConversationItem item) {
  return item.kind == CcbConversationItemKind.agentReply &&
      item.source == 'tmux output / live';
}

String compactLiveTerminalOutput(String body) {
  final plain = stripAnsiControlSequences(
    body.replaceAll('\r\n', '\n').replaceAll('\r', '\n'),
  );
  final lines = [
    for (final line in plain.split('\n'))
      if (line.trim().isNotEmpty && !_isTerminalLifecycleNoise(line))
        line.trimRight(),
  ];
  if (lines.isEmpty) {
    return '';
  }
  final visibleLines =
      lines.length > maxLiveTerminalOutputLines
          ? lines.sublist(lines.length - maxLiveTerminalOutputLines)
          : lines;
  var compact = visibleLines.join('\n').trim();
  if (compact.length > maxLiveTerminalOutputChars) {
    compact =
        '...\n${compact.substring(compact.length - maxLiveTerminalOutputChars)}';
  }
  return compact;
}

String stripAnsiControlSequences(String text) {
  return text
      .replaceAll(_ansiOscPattern, '')
      .replaceAll(_ansiControlPattern, '');
}

bool _isTerminalLifecycleNoise(String line) {
  return switch (line.trim()) {
    'server exited unexpectedly' => true,
    _ => false,
  };
}
