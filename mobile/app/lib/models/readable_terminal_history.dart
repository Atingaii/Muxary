class ReadableTerminalHistory {
  const ReadableTerminalHistory({
    required this.agentName,
    required this.historyScope,
    required this.blocks,
    this.sourcePaneId,
    this.generatedAt,
    this.stale = false,
  });

  final String agentName;
  final String historyScope;
  final String? sourcePaneId;
  final String? generatedAt;
  final bool stale;
  final List<ReadableTerminalBlock> blocks;

  factory ReadableTerminalHistory.fromJson({
    required String agentName,
    required Map<String, Object?> json,
  }) {
    return ReadableTerminalHistory(
      agentName: agentName,
      historyScope: _text(json['history_scope'], fallback: 'tmux_scrollback'),
      sourcePaneId: _optionalText(json['source_pane_id']),
      generatedAt: _optionalText(json['generated_at']),
      stale: json['stale'] == true,
      blocks: [
        for (final item in _mapList(json['blocks']))
          ReadableTerminalBlock.fromJson(item),
      ],
    );
  }
}

class ReadableTerminalBlock {
  const ReadableTerminalBlock({
    required this.id,
    required this.type,
    required this.text,
    this.title,
    this.language,
    this.status,
  });

  final String id;
  final String type;
  final String text;
  final String? title;
  final String? language;
  final String? status;

  factory ReadableTerminalBlock.fromJson(Map<String, Object?> json) {
    return ReadableTerminalBlock(
      id: _text(json['id'], fallback: 'block'),
      type: _text(json['type'], fallback: 'log'),
      title: _optionalText(json['title']),
      text: _text(json['text']),
      language: _optionalText(json['language']),
      status: _optionalText(json['status']),
    );
  }
}

List<Map<String, Object?>> _mapList(Object? value) {
  if (value is Iterable) {
    return [for (final item in value) _map(item)];
  }
  return const [];
}

Map<String, Object?> _map(Object? value) {
  if (value is Map) {
    return {
      for (final entry in value.entries) entry.key.toString(): entry.value,
    };
  }
  return const {};
}

String _text(Object? value, {String fallback = ''}) {
  final text = (value ?? '').toString().trim();
  return text.isEmpty ? fallback : text;
}

String? _optionalText(Object? value) {
  final text = _text(value);
  return text.isEmpty ? null : text;
}
