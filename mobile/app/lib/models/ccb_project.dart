class CcbProject {
  const CcbProject({
    required this.id,
    required this.displayName,
    required this.root,
    this.favorite = false,
    this.health = 'unknown',
    this.hasWorkingAgents = false,
    this.workingAgentCount = 0,
    this.lastOpenedAt,
    this.lastActivityAt,
  });

  final String id;
  final String displayName;
  final String root;
  final bool favorite;
  final String health;
  final bool hasWorkingAgents;
  final int workingAgentCount;
  final DateTime? lastOpenedAt;
  final DateTime? lastActivityAt;

  factory CcbProject.fromJson(Map<String, Object?> json) {
    final workingAgentCount =
        _optionalInt(json['working_agent_count']) ??
        _optionalInt(json['active_agent_count']) ??
        0;
    return CcbProject(
      id: _text(json['id']),
      displayName: _text(json['display_name'], fallback: _text(json['id'])),
      root: _text(json['root']),
      favorite: json['favorite'] == true,
      health: _text(json['health'], fallback: 'unknown'),
      hasWorkingAgents:
          json['has_working_agents'] == true ||
          json['has_active_agents'] == true ||
          workingAgentCount > 0,
      workingAgentCount: workingAgentCount,
      lastOpenedAt: _optionalDateTime(json['last_opened_at']),
      lastActivityAt: _optionalDateTime(json['last_activity_at']),
    );
  }
}

List<CcbProject> sortCcbProjectsByRecentActivity(
  List<CcbProject> projects, {
  Map<String, DateTime> optimisticActivityAt = const {},
}) {
  final indexed = projects.indexed.toList();
  indexed.sort((left, right) {
    final leftProject = left.$2;
    final rightProject = right.$2;
    final leftAt = ccbProjectRecentActivityAt(
      leftProject,
      optimisticActivityAt: optimisticActivityAt[leftProject.id],
    );
    final rightAt = ccbProjectRecentActivityAt(
      rightProject,
      optimisticActivityAt: optimisticActivityAt[rightProject.id],
    );
    if (leftAt != null && rightAt != null) {
      final compared = rightAt.compareTo(leftAt);
      if (compared != 0) {
        return compared;
      }
    } else if (leftAt != null) {
      return -1;
    } else if (rightAt != null) {
      return 1;
    } else if (leftProject.hasWorkingAgents != rightProject.hasWorkingAgents) {
      return leftProject.hasWorkingAgents ? -1 : 1;
    }
    return left.$1.compareTo(right.$1);
  });
  return [for (final item in indexed) item.$2];
}

DateTime? ccbProjectRecentActivityAt(
  CcbProject project, {
  DateTime? optimisticActivityAt,
}) {
  final openedAt = project.lastOpenedAt;
  final activityAt = project.lastActivityAt;
  return _latestDateTime([openedAt, activityAt, optimisticActivityAt]);
}

String _text(Object? value, {String fallback = ''}) {
  final text = (value ?? '').toString().trim();
  return text.isEmpty ? fallback : text;
}

int? _optionalInt(Object? value) => int.tryParse((value ?? '').toString());

DateTime? _optionalDateTime(Object? value) {
  final parsed = DateTime.tryParse((value ?? '').toString());
  return parsed?.toUtc();
}

DateTime? _latestDateTime(Iterable<DateTime?> values) {
  DateTime? latest;
  for (final value in values) {
    if (value == null) {
      continue;
    }
    final normalized = value.toUtc();
    if (latest == null || normalized.isAfter(latest)) {
      latest = normalized;
    }
  }
  return latest;
}
