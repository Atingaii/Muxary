class CcbWindow {
  const CcbWindow({
    required this.name,
    required this.label,
    required this.kind,
    required this.order,
    required this.active,
    required this.agents,
    this.tmuxWindowId,
    this.tmuxWindowIndex,
  });

  final String name;
  final String label;
  final String kind;
  final int order;
  final bool active;
  final List<String> agents;
  final String? tmuxWindowId;
  final int? tmuxWindowIndex;

  factory CcbWindow.fromJson(Map<String, Object?> json) {
    return CcbWindow(
      name: _text(json['name']),
      label: _text(json['label'], fallback: _text(json['name'])),
      kind: _text(json['kind'], fallback: 'agents'),
      order: _int(json['order']),
      active: json['active'] == true,
      agents: _stringList(json['agents']),
      tmuxWindowId: _optionalText(json['tmux_window_id']),
      tmuxWindowIndex: _optionalInt(json['tmux_window_index']),
    );
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

int _int(Object? value) => int.tryParse((value ?? '').toString()) ?? 0;

int? _optionalInt(Object? value) => int.tryParse((value ?? '').toString());

List<String> _stringList(Object? value) {
  if (value is Iterable) {
    return [
      for (final item in value) _text(item),
    ].where((e) => e.isNotEmpty).toList();
  }
  return const [];
}
