import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ccb_mobile/ccb_mobile.dart';

import 'support/project_home_test_driver.dart';
import 'support/project_home_test_fakes.dart';

void main() {
  testWidgets('notification center deep-links to agent content and Comms', (
    tester,
  ) async {
    await tester.pumpWidget(const CcbMobileApp(enableProductOnboarding: false));
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('notification-center-action')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('notification-center')), findsOneWidget);
    final count = tester.widget<Text>(
      find.byKey(const ValueKey('notification-count')),
    );
    expect(count.data, '3');

    await tester.tap(
      find.byKey(const ValueKey('notification-agent-lead-completed')),
    );
    await tester.pumpAndSettle();

    expectAgentSelected(tester, 'lead');
    await tapVisible(
      tester,
      const ValueKey('conversation-expand-reply-content-lead-plan'),
    );
    expect(
      find.byKey(const ValueKey('content-item-content-lead-plan')),
      findsOneWidget,
    );
    expect(find.text('Opened content content-lead-plan'), findsOneWidget);

    await tester.tap(find.byKey(const ValueKey('project-back-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('notification-center-action')));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('notification-comms-comms-mobile-callback')),
    );
    await tester.pumpAndSettle();

    expectAgentSelected(tester, 'mobile');
    expect(find.text('Opened Comms comms-mobile-callback'), findsOneWidget);
  });

  testWidgets('window-only notification selects first agent for window', (
    tester,
  ) async {
    final view = CcbProjectView.fromProjectViewPayload(demoPayloadWithEpoch(4));
    final repository = _NotificationRepository(
      _copyViewWithNotifications(view, [
        CcbNotification(
          id: 'window-main-attention',
          kind: CcbNotificationKind.callbackWaiting,
          severity: CcbNotificationSeverity.warning,
          title: 'Main window attention',
          body: 'main has pending work',
          target: const CcbNotificationTarget(
            projectId: 'proj-demo',
            windowName: 'main',
          ),
        ),
      ]),
    );

    await tester.pumpWidget(
      MaterialApp(home: ProjectHomeScreen(repository: repository)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('notification-center-action')));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('notification-window-main-attention')),
    );
    await tester.pumpAndSettle();

    expectAgentSelected(tester, 'lead');
    expect(find.text('Opened notification'), findsOneWidget);
  });

  testWidgets('unknown explicit agent does not fallback to target window', (
    tester,
  ) async {
    final view = CcbProjectView.fromProjectViewPayload(demoPayloadWithEpoch(4));
    final repository = _NotificationRepository(
      _copyViewWithNotifications(view, [
        CcbNotification(
          id: 'unknown-agent-with-window',
          kind: CcbNotificationKind.callbackWaiting,
          severity: CcbNotificationSeverity.warning,
          title: 'Ghost agent attention',
          body: 'review has pending work',
          target: const CcbNotificationTarget(
            projectId: 'proj-demo',
            agentName: 'ghost',
            windowName: 'review',
            contentId: 'content-ghost',
            commsId: 'comms-ghost',
          ),
        ),
      ]),
    );

    await tester.pumpWidget(
      MaterialApp(home: ProjectHomeScreen(repository: repository)),
    );
    await tester.pumpAndSettle();

    await tester.tap(find.byKey(const ValueKey('notification-center-action')));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('notification-unknown-agent-with-window')),
    );
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('notification-center')), findsNothing);
    expect(find.byKey(const ValueKey('project-list')), findsOneWidget);
    expect(find.byKey(const ValueKey('agent-switcher')), findsNothing);
    expect(find.text('Opened content content-ghost'), findsOneWidget);
  });
}

class _NotificationRepository extends RecordingGatewayRepository {
  _NotificationRepository(this.view);

  final CcbProjectView view;

  @override
  Future<List<CcbProject>> listProjects() async {
    return [view.project];
  }

  @override
  Future<CcbProjectView> getProjectView(String projectId) async {
    return view;
  }
}

CcbProjectView _copyViewWithNotifications(
  CcbProjectView view,
  List<CcbNotification> notifications,
) {
  return CcbProjectView(
    project: view.project,
    namespaceEpoch: view.namespaceEpoch,
    tmuxSocketPath: view.tmuxSocketPath,
    tmuxSessionName: view.tmuxSessionName,
    activeWindow: view.activeWindow,
    activePaneId: view.activePaneId,
    windows: view.windows,
    agents: view.agents,
    contentItems: view.contentItems,
    notifications: notifications,
    terminalHistories: view.terminalHistories,
  );
}
