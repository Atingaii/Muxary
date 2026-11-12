import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment(
  'CCB_MOBILE_GATEWAY_RESTART_PROJECT_ID',
);
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_GATEWAY_RESTART_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_GATEWAY_RESTART_AGENT',
  defaultValue: 'mobile_probe',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('explicit refresh recovers after gateway process restart', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('gateway restart smoke project id is required');
    }

    app.main();

    await _waitForProjectList(tester);
    await _waitForRenderedText(
      tester,
      _projectName,
      timeout: const Duration(seconds: 15),
    );

    // Host-side runner stops the real mobile gateway after this marker.
    // ignore: avoid_print
    print('CCB_GATEWAY_RESTART_READY_STOP project-list');
    await tester.pump(const Duration(seconds: 2));

    await _tapVisible(tester, const ValueKey('project-list-refresh-action'));
    await _waitFor(
      tester,
      find.byKey(const ValueKey('project-list-load-error')),
      timeout: const Duration(seconds: 45),
      diagnostics: () => _chatDiagnostics(tester),
    );

    // Host-side runner restarts the gateway on the same loopback port and
    // same state_home after this marker. The stored paired profile/token must
    // continue to work without clearing app data or claiming a new QR code.
    // ignore: avoid_print
    print('CCB_GATEWAY_RESTART_READY_START project-list');
    await tester.pump(const Duration(seconds: 2));

    await _tapVisible(tester, const ValueKey('project-list-retry-button'));
    await _waitForProjectList(tester);
    await _waitForRenderedText(
      tester,
      _projectName,
      timeout: const Duration(seconds: 45),
    );

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForRefreshEnabled(tester);

    // Repeat after the project is open to prove selected-agent refresh
    // recovery, not just the server project catalog.
    // ignore: avoid_print
    print('CCB_GATEWAY_RESTART_READY_STOP selected-agent');
    await tester.pump(const Duration(seconds: 2));

    await _tapVisible(
      tester,
      const ValueKey('agent-conversation-refresh-action'),
    );
    await _waitForConversationRefreshFailure(tester);

    // ignore: avoid_print
    print('CCB_GATEWAY_RESTART_READY_START selected-agent');
    await tester.pump(const Duration(seconds: 2));

    await _waitForRefreshEnabled(tester);
    await _tapVisible(
      tester,
      const ValueKey('agent-conversation-refresh-action'),
    );
    await _waitUntilGone(
      tester,
      find.text('Conversation refresh failed'),
      timeout: const Duration(seconds: 45),
      diagnostics: () => _chatDiagnostics(tester),
    );

    expect(
      find.byKey(const ValueKey('agent-message-composer')),
      findsOneWidget,
    );
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);
  });
}

Future<void> _waitForProjectList(WidgetTester tester) {
  return _waitFor(
    tester,
    find.byKey(const ValueKey('project-list')),
    timeout: const Duration(seconds: 45),
    diagnostics: () => _chatDiagnostics(tester),
  );
}

Future<void> _openServerProject(
  WidgetTester tester,
  String projectId,
  String projectName,
) async {
  await _waitForProjectList(tester);
  await _waitForRenderedText(
    tester,
    projectName,
    timeout: const Duration(seconds: 15),
  );
  await _tapVisible(tester, ValueKey('project-open-$projectId'));
  await _waitFor(
    tester,
    find.byKey(const ValueKey('selected-agent-workspace')),
    timeout: const Duration(seconds: 45),
  );
}

Future<void> _selectAgent(WidgetTester tester, String agentName) async {
  await _tapVisible(tester, ValueKey('agent-$agentName'));
  await _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      final key = widget.key;
      if (key is! ValueKey || key.value != 'agent-$agentName') {
        return false;
      }
      if (widget is ChoiceChip) {
        return widget.selected;
      }
      if (widget is ListTile) {
        return widget.selected;
      }
      return false;
    }, description: 'selected agent $agentName'),
    timeout: const Duration(seconds: 30),
  );
  await _waitFor(
    tester,
    find.byKey(const ValueKey('agent-message-composer')),
    timeout: const Duration(seconds: 30),
  );
}

Future<void> _waitForRefreshEnabled(WidgetTester tester) {
  return _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      final key = widget.key;
      return key is ValueKey &&
          key.value == 'agent-conversation-refresh-action' &&
          widget is IconButton &&
          widget.onPressed != null;
    }, description: 'enabled conversation refresh button'),
    timeout: const Duration(seconds: 30),
  );
}

Future<void> _waitForConversationRefreshFailure(WidgetTester tester) {
  return _waitFor(
    tester,
    find.text('Conversation refresh failed'),
    timeout: const Duration(seconds: 45),
    diagnostics: () => _chatDiagnostics(tester),
  );
}

Future<void> _waitForRenderedText(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 10),
}) {
  return _waitFor(
    tester,
    _renderedTextContaining(text, description: 'rendered text $text'),
    timeout: timeout,
    diagnostics: () => _chatDiagnostics(tester),
  );
}

Future<void> _tapVisible(WidgetTester tester, Key key) async {
  final onstageFinder = find.byKey(key);
  final finder =
      tester.any(onstageFinder)
          ? onstageFinder
          : find.byKey(key, skipOffstage: false);
  await _waitFor(tester, finder);
  final target = finder.first;
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Finder _renderedTextContaining(String text, {String? description}) {
  return find.byWidgetPredicate((widget) {
    if (widget is SelectableText) {
      return (widget.data ?? widget.textSpan?.toPlainText() ?? '').contains(
        text,
      );
    }
    if (widget is Text) {
      return (widget.data ?? widget.textSpan?.toPlainText() ?? '').contains(
        text,
      );
    }
    if (widget is RichText) {
      return widget.text.toPlainText().contains(text);
    }
    return false;
  }, description: description ?? 'rendered text containing $text');
}

String _chatDiagnostics(WidgetTester tester) {
  return find
      .byWidgetPredicate((widget) => widget is Text || widget is SelectableText)
      .evaluate()
      .take(60)
      .map((element) {
        final widget = element.widget;
        if (widget is Text) {
          return widget.data ?? widget.textSpan?.toPlainText() ?? '';
        }
        if (widget is SelectableText) {
          return widget.data ?? widget.textSpan?.toPlainText() ?? '';
        }
        return '';
      })
      .where((text) => text.isNotEmpty)
      .join(' | ');
}

Future<void> _waitFor(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 10),
  String Function()? diagnostics,
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (tester.any(finder)) {
      return;
    }
  }
  throw TestFailure(
    'Timed out waiting for $finder. '
    '${diagnostics == null ? '' : diagnostics()}',
  );
}

Future<void> _waitUntilGone(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 10),
  String Function()? diagnostics,
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (!tester.any(finder)) {
      return;
    }
  }
  throw TestFailure(
    'Timed out waiting for $finder to disappear. '
    '${diagnostics == null ? '' : diagnostics()}',
  );
}
