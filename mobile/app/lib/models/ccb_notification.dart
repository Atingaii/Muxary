enum CcbNotificationKind {
  taskCompleted('task_completed'),
  taskFailed('task_failed'),
  taskBlocked('task_blocked'),
  callbackWaiting('callback_waiting'),
  commsMention('comms_mention'),
  agentUnhealthy('agent_unhealthy');

  const CcbNotificationKind(this.wireName);

  final String wireName;
}

enum CcbNotificationSeverity {
  info('info'),
  warning('warning'),
  critical('critical');

  const CcbNotificationSeverity(this.wireName);

  final String wireName;
}

class CcbNotificationTarget {
  const CcbNotificationTarget({
    required this.projectId,
    this.agentName,
    this.windowName,
    this.contentId,
    this.commsId,
  });

  final String projectId;
  final String? agentName;
  final String? windowName;
  final String? contentId;
  final String? commsId;

  Map<String, Object?> toJson() {
    return {
      'project_id': projectId,
      if (_hasText(agentName)) 'agent': agentName,
      if (_hasText(windowName)) 'window': windowName,
      if (_hasText(contentId)) 'content_id': contentId,
      if (_hasText(commsId)) 'comms_id': commsId,
    };
  }
}

class CcbNotification {
  const CcbNotification({
    required this.id,
    required this.kind,
    required this.severity,
    required this.title,
    required this.body,
    required this.target,
  });

  final String id;
  final CcbNotificationKind kind;
  final CcbNotificationSeverity severity;
  final String title;
  final String body;
  final CcbNotificationTarget target;

  Map<String, Object?> toJson() {
    return {
      'id': id,
      'kind': kind.wireName,
      'severity': severity.wireName,
      'title': title,
      'body': body,
      'target': target.toJson(),
    };
  }
}

bool _hasText(String? value) => value != null && value.trim().isNotEmpty;
