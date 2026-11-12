import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ccb_mobile/ccb_mobile.dart';

void main() {
  testWidgets('project view load failure shows recoverable error state', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: ProjectHomeScreen(repository: _FailingProjectViewRepository()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.byType(CircularProgressIndicator), findsNothing);
    expect(
      find.byKey(const ValueKey('project-view-load-error')),
      findsOneWidget,
    );
    expect(find.text('Could not load project'), findsOneWidget);
    expect(find.textContaining('gateway unavailable'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('project-view-retry-button')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('project-view-use-fake-button')),
      findsOneWidget,
    );
  });
}

class _FailingProjectViewRepository extends FakeMobileCcbRepository {
  _FailingProjectViewRepository()
    : super(projectViewPayload: demoProjectViewFixture);

  @override
  Future<CcbProjectView> getProjectView(String projectId) async {
    throw StateError('gateway unavailable');
  }
}
