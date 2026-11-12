import 'package:test/test.dart';

import 'package:ccb_mobile/models/ccb_project.dart';

void main() {
  test('project parses mobile activity timestamps', () {
    final project = CcbProject.fromJson({
      'id': 'proj-a',
      'display_name': 'Project A',
      'root': '/srv/a',
      'last_opened_at': '2026-07-04T09:00:00Z',
      'last_activity_at': '2026-07-04T09:02:00Z',
    });

    expect(project.lastOpenedAt, DateTime.utc(2026, 7, 4, 9));
    expect(project.lastActivityAt, DateTime.utc(2026, 7, 4, 9, 2));
    expect(ccbProjectRecentActivityAt(project), DateTime.utc(2026, 7, 4, 9, 2));
  });

  test('project recent activity sort is descending and stable', () {
    final projects = [
      const CcbProject(id: 'a', displayName: 'A', root: '/srv/a'),
      CcbProject(
        id: 'b',
        displayName: 'B',
        root: '/srv/b',
        lastOpenedAt: DateTime.utc(2026, 7, 4, 9, 1),
      ),
      CcbProject(
        id: 'c',
        displayName: 'C',
        root: '/srv/c',
        lastActivityAt: DateTime.utc(2026, 7, 4, 9, 3),
      ),
      const CcbProject(id: 'd', displayName: 'D', root: '/srv/d'),
    ];

    expect(
      sortCcbProjectsByRecentActivity(projects).map((project) => project.id),
      ['c', 'b', 'a', 'd'],
    );
  });
}
