class CcbContentItem {
  const CcbContentItem({
    required this.id,
    required this.kind,
    required this.format,
    required this.text,
    this.agentName,
    this.title,
    this.source,
    this.sentAt,
    this.startedAt,
    this.completedAt,
    this.durationMs,
  });

  final String id;
  final String kind;
  final String format;
  final String text;
  final String? agentName;
  final String? title;
  final String? source;
  final DateTime? sentAt;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final int? durationMs;

  factory CcbContentItem.fromJson(Map<String, Object?> json) {
    return CcbContentItem(
      id: _text(json['id'], fallback: 'content'),
      kind: _text(json['kind'], fallback: 'unknown'),
      format: _text(json['format'], fallback: 'plain'),
      text: _text(json['text']),
      agentName:
          _optionalText(json['agent']) ?? _optionalText(json['agent_name']),
      title: _optionalText(json['title']),
      source: _optionalText(json['source']),
      sentAt:
          _optionalDateTime(json['sent_at']) ??
          _optionalDateTime(json['created_at']),
      startedAt:
          _optionalDateTime(json['started_at']) ??
          _optionalDateTime(json['execution_started_at']),
      completedAt:
          _optionalDateTime(json['completed_at']) ??
          _optionalDateTime(json['finished_at']) ??
          _optionalDateTime(json['execution_completed_at']),
      durationMs:
          _optionalInt(json['duration_ms']) ??
          _durationSecondsToMs(json['duration_seconds']),
    );
  }

  bool belongsToAgent(String name) {
    final agent = agentName;
    return agent == null || agent == name;
  }
}

String _text(Object? value, {String fallback = ''}) {
  final text = (value ?? '').toString().trim();
  return text.isEmpty ? fallback : text;
}

String? _optionalText(Object? value) {
  final text = _text(value);
  return text.isEmpty ? null : text;
}

DateTime? _optionalDateTime(Object? value) {
  final parsed = DateTime.tryParse((value ?? '').toString());
  return parsed?.toUtc();
}

int? _optionalInt(Object? value) {
  if (value is int) {
    return value;
  }
  return int.tryParse((value ?? '').toString());
}

int? _durationSecondsToMs(Object? value) {
  final seconds = double.tryParse((value ?? '').toString());
  return seconds == null ? null : (seconds * 1000).round();
}
