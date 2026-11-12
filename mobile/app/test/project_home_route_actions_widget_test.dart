import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:xterm/xterm.dart';

import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:ccb_mobile/features/project_home/project_home_route_actions.dart';

import 'support/project_home_test_fakes.dart';

void main() {
  testWidgets('terminal route helper pushes fake terminal screen', (
    tester,
  ) async {
    final transport = RecordingTerminalTransport();
    await tester.pumpWidget(
      MaterialApp(
        home: _ActionHost(
          onPressed:
              (context) => pushProjectHomeTerminalRoute(
                context,
                repository: FakeMobileCcbRepository.demo(),
                projectId: 'proj-demo',
                agentName: 'lead',
                terminalTransport: transport,
                gatewayTerminal: true,
              ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('route-action-button')));
    await tester.pumpAndSettle();

    expect(find.byType(TerminalView), findsOneWidget);
    expect(
      find.byKey(const ValueKey('ccb-live-terminal-view')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('terminal-connection-status')),
      findsNothing,
    );
    expect(find.textContaining('gateway terminal stream'), findsNothing);
    expect(transport.requests, hasLength(1));
    expect(transport.requests.single.target.projectId, 'proj-demo');
    expect(transport.requests.single.target.agent, 'lead');

    transport.openErrors.add(
      const TerminalTransportException('terminal stream disconnected'),
    );
    await transport.sessions.single.endOutput();
    await tester.pump();

    expect(
      find.byKey(const ValueKey('terminal-compact-connection-status')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('terminal-compact-reconnect')),
      findsOneWidget,
    );
  });

  testWidgets('terminal route rejects a changed agent window identity', (
    tester,
  ) async {
    final transport = RecordingTerminalTransport();
    await tester.pumpWidget(
      MaterialApp(
        home: _ActionHost(
          onPressed:
              (context) => pushProjectHomeTerminalRoute(
                context,
                repository: FakeMobileCcbRepository(
                  projectViewPayload: _payloadWithLeadWindow('review'),
                ),
                projectId: 'proj-demo',
                agentName: 'lead',
                expectedNamespaceEpoch: 4,
                expectedWindowName: 'main',
                expectedPaneId: '%1',
                terminalTransport: transport,
                gatewayTerminal: true,
              ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('route-action-button')));
    await tester.pumpAndSettle();

    expect(find.byType(TerminalView), findsNothing);
    expect(transport.requests, isEmpty);
    expect(find.textContaining('Project view is stale'), findsOneWidget);
  });

  testWidgets('connection details route helper shows supplied panel', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: _ActionHost(
          onPressed:
              (context) => pushProjectHomeConnectionDetailsRoute(
                context,
                panel: const Text(
                  'sentinel panel',
                  key: ValueKey('sentinel-connection-panel'),
                ),
              ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('route-action-button')));
    await tester.pumpAndSettle();

    expect(find.text('Diagnostics'), findsOneWidget);
    expect(
      find.byKey(const ValueKey('sentinel-connection-panel')),
      findsOneWidget,
    );
  });

  testWidgets('notification sheet helper pops before callback', (tester) async {
    final opened = <CcbNotification>[];
    final notification = _notification();
    await tester.pumpWidget(
      MaterialApp(
        home: _ActionHost(
          onPressed:
              (context) => showProjectHomeNotificationCenter(
                context,
                notifications: [notification],
                onOpen: opened.add,
              ),
        ),
      ),
    );

    await tester.tap(find.byKey(const ValueKey('route-action-button')));
    await tester.pumpAndSettle();
    expect(find.byKey(const ValueKey('notification-center')), findsOneWidget);

    await tester.tap(find.byKey(ValueKey('notification-${notification.id}')));
    await tester.pumpAndSettle();

    expect(opened, [same(notification)]);
    expect(find.byKey(const ValueKey('notification-center')), findsNothing);
  });

  testWidgets('stop confirmation helper returns false from cancel', (
    tester,
  ) async {
    await _pumpStopConfirmationHost(tester);

    await tester.tap(find.byKey(const ValueKey('route-action-button')));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('cancel-lifecycle-stop-button')),
    );
    await tester.pumpAndSettle();

    expect(find.text('result: false'), findsOneWidget);
  });

  testWidgets('stop confirmation helper returns true from confirm', (
    tester,
  ) async {
    await _pumpStopConfirmationHost(tester);

    await tester.tap(find.byKey(const ValueKey('route-action-button')));
    await tester.pumpAndSettle();
    await tester.tap(
      find.byKey(const ValueKey('confirm-lifecycle-stop-button')),
    );
    await tester.pumpAndSettle();

    expect(find.text('result: true'), findsOneWidget);
  });
}

Map<String, Object?> _payloadWithLeadWindow(String window) {
  final payload =
      jsonDecode(jsonEncode(demoPayloadWithReviewWindow()))
          as Map<String, Object?>;
  final view = payload['view']! as Map<String, Object?>;
  final agents = view['agents']! as List<Object?>;
  final lead = agents.cast<Map<String, Object?>>().firstWhere(
    (agent) => agent['name'] == 'lead',
  );
  lead['window'] = window;
  return payload;
}

Future<void> _pumpStopConfirmationHost(WidgetTester tester) {
  return tester.pumpWidget(
    MaterialApp(
      home: _ResultHost(
        onPressed:
            (context) async => confirmProjectHomeStop(
              context,
              view: CcbProjectView.fromProjectViewPayload(
                demoPayloadWithEpoch(4),
              ),
            ),
      ),
    ),
  );
}

class _ActionHost extends StatelessWidget {
  const _ActionHost({required this.onPressed});

  final Future<void> Function(BuildContext context) onPressed;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: ElevatedButton(
          key: const ValueKey('route-action-button'),
          onPressed: () {
            onPressed(context);
          },
          child: const Text('Run'),
        ),
      ),
    );
  }
}

class _ResultHost extends StatefulWidget {
  const _ResultHost({required this.onPressed});

  final Future<bool?> Function(BuildContext context) onPressed;

  @override
  State<_ResultHost> createState() => _ResultHostState();
}

class _ResultHostState extends State<_ResultHost> {
  bool? _result;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          ElevatedButton(
            key: const ValueKey('route-action-button'),
            onPressed: () async {
              final result = await widget.onPressed(context);
              if (!mounted) {
                return;
              }
              setState(() {
                _result = result;
              });
            },
            child: const Text('Run'),
          ),
          Text('result: $_result'),
        ],
      ),
    );
  }
}

CcbNotification _notification() {
  return const CcbNotification(
    id: 'route-action-notification',
    kind: CcbNotificationKind.callbackWaiting,
    severity: CcbNotificationSeverity.warning,
    title: 'Notification',
    body: 'Needs attention',
    target: CcbNotificationTarget(projectId: 'proj-demo', agentName: 'lead'),
  );
}
