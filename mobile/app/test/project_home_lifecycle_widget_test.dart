import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ccb_mobile/ccb_mobile.dart';

import 'support/project_home_test_driver.dart';
import 'support/project_home_test_fakes.dart';

void main() {
  testWidgets('canceling stop confirmation does not request lifecycle', (
    tester,
  ) async {
    final repository = _ControlledLifecycleRepository();
    await tester.pumpWidget(
      MaterialApp(home: ProjectHomeScreen(repository: repository)),
    );
    await tester.pumpAndSettle();

    await openConnectionDetails(tester);
    await expandTile(tester, const ValueKey('project-lifecycle-panel'));
    await tapVisible(tester, const ValueKey('lifecycle-stop-button'));

    expect(find.text('Stop project'), findsOneWidget);

    await tester.tap(
      find.byKey(const ValueKey('cancel-lifecycle-stop-button')),
    );
    await tester.pumpAndSettle();

    expect(repository.lifecycleCalls, isEmpty);
    expect(
      find.byKey(const ValueKey('project-lifecycle-detail')),
      findsNothing,
    );
    expect(find.text('No lifecycle action yet'), findsOneWidget);
    expect(find.text('Stopping'), findsNothing);
    expect(find.text('Lifecycle stop: ccbd_stop_requested'), findsNothing);
    expect(
      tester
          .widget<FilledButton>(
            find.byKey(const ValueKey('lifecycle-stop-button')),
          )
          .onPressed,
      isNotNull,
    );
  });

  testWidgets('failed lifecycle action preserves previous success detail', (
    tester,
  ) async {
    final repository = _ControlledLifecycleRepository();
    await tester.pumpWidget(
      MaterialApp(home: ProjectHomeScreen(repository: repository)),
    );
    await tester.pumpAndSettle();

    await openConnectionDetails(tester);
    await expandTile(tester, const ValueKey('project-lifecycle-panel'));
    await tapVisible(tester, const ValueKey('lifecycle-open-button'));

    expect(repository.lifecycleCalls, [('proj-demo', CcbLifecycleAction.open)]);
    expect(find.text('Lifecycle open: opened'), findsOneWidget);
    expect(find.text('running / opened / ccb / no raw tmux'), findsOneWidget);

    repository.failNextLifecycle = StateError('lifecycle failed');
    await tapVisible(tester, const ValueKey('lifecycle-close-button'));

    expect(repository.lifecycleCalls, [
      ('proj-demo', CcbLifecycleAction.open),
      ('proj-demo', CcbLifecycleAction.close),
    ]);
    expect(
      find.descendant(
        of: find.byType(SnackBar, skipOffstage: false),
        matching: find.text('Bad state: lifecycle failed', skipOffstage: false),
      ),
      findsAtLeastNWidgets(1),
    );
    expect(find.text('running / opened / ccb / no raw tmux'), findsOneWidget);
    expect(find.text('Working'), findsNothing);
    expect(
      tester
          .widget<OutlinedButton>(
            find.byKey(const ValueKey('lifecycle-close-button')),
          )
          .onPressed,
      isNotNull,
    );
  });
}

class _ControlledLifecycleRepository extends RecordingGatewayRepository {
  Object? failNextLifecycle;

  @override
  Future<CcbProjectLifecycleResult> requestLifecycle({
    required String projectId,
    required CcbLifecycleAction action,
  }) async {
    lifecycleCalls.add((projectId, action));
    final failure = failNextLifecycle;
    if (failure != null) {
      failNextLifecycle = null;
      throw failure;
    }
    return CcbProjectLifecycleResult(
      projectId: projectId,
      action: action,
      state: action == CcbLifecycleAction.stop ? 'stopping' : 'running',
      effect: switch (action) {
        CcbLifecycleAction.wake => 'already_running',
        CcbLifecycleAction.open => 'opened',
        CcbLifecycleAction.close => 'mobile_view_closed',
        CcbLifecycleAction.stop => 'ccbd_stop_requested',
      },
      ccbAuthority: true,
      tmuxKillServer: false,
      view:
          action == CcbLifecycleAction.wake || action == CcbLifecycleAction.open
              ? CcbProjectView.fromProjectViewPayload(demoProjectViewFixture)
              : null,
    );
  }
}
