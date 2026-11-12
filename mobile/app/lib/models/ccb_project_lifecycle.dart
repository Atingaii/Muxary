import 'ccb_project_view.dart';

enum CcbLifecycleAction {
  wake('wake'),
  open('open'),
  close('close'),
  stop('stop');

  const CcbLifecycleAction(this.wireName);

  final String wireName;

  static CcbLifecycleAction fromWireName(String value) {
    final normalized = value.trim().toLowerCase();
    for (final action in values) {
      if (action.wireName == normalized) {
        return action;
      }
    }
    throw ArgumentError.value(value, 'value', 'unknown lifecycle action');
  }
}

class CcbProjectLifecycleResult {
  const CcbProjectLifecycleResult({
    required this.projectId,
    required this.action,
    required this.state,
    required this.effect,
    required this.ccbAuthority,
    required this.tmuxKillServer,
    this.forced = false,
    this.updatedAt,
    this.result = const {},
    this.view,
  });

  final String projectId;
  final CcbLifecycleAction action;
  final String state;
  final String effect;
  final bool ccbAuthority;
  final bool tmuxKillServer;
  final bool forced;
  final DateTime? updatedAt;
  final Map<String, Object?> result;
  final CcbProjectView? view;

  factory CcbProjectLifecycleResult.fromJson(Map<String, Object?> json) {
    final lifecycle = _map(json['lifecycle']);
    final view = _map(json['view']);
    final project = _map(view['project']);
    final projectId = _text(json['project_id'], fallback: _text(project['id']));
    return CcbProjectLifecycleResult(
      projectId: projectId,
      action: CcbLifecycleAction.fromWireName(_text(lifecycle['action'])),
      state: _text(lifecycle['state'], fallback: 'unknown'),
      effect: _text(lifecycle['effect'], fallback: 'unknown'),
      ccbAuthority: lifecycle['ccb_authority'] == true,
      tmuxKillServer: lifecycle['tmux_kill_server'] == true,
      forced: lifecycle['forced'] == true,
      updatedAt: DateTime.tryParse(_text(lifecycle['updated_at'])),
      result: _map(lifecycle['result']),
      view:
          json['view'] is Map
              ? CcbProjectView.fromProjectViewPayload(json)
              : null,
    );
  }

  Map<String, Object?> toJson() {
    return {
      'project_id': projectId,
      'lifecycle': {
        'action': action.wireName,
        'state': state,
        'effect': effect,
        'forced': forced,
        'ccb_authority': ccbAuthority,
        'tmux_kill_server': tmuxKillServer,
        if (updatedAt != null)
          'updated_at': updatedAt!.toUtc().toIso8601String(),
        if (result.isNotEmpty) 'result': result,
      },
    };
  }
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
