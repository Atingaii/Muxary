import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment('CCB_MOBILE_BACKGROUND_PROJECT_ID');
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_AGENT',
  defaultValue: 'mobile_probe',
);
const _backgroundSeconds = int.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_SECONDS',
  defaultValue: 10,
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('selected-agent refresh survives Android background and resume', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('background/resume smoke project id is required');
    }
    if (_backgroundSeconds < 3) {
      throw TestFailure('background/resume smoke needs at least 3 seconds');
    }

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForRefreshEnabled(tester);
    await _waitUntilGone(
      tester,
      find.byKey(const ValueKey('agent-conversation-loading')),
      timeout: const Duration(seconds: 30),
      diagnostics: () => _chatDiagnostics(tester),
    );

    expect(
      find.byKey(const ValueKey('agent-message-composer')),
      findsOneWidget,
    );
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    // Host-side runner sends HOME and then relaunches MainActivity when it sees
    // this marker. The test waits in real time so Android lifecycle handling is
    // exercised by the emulator, not by a fake widget lifecycle call.
    // ignore: avoid_print
    print('CCB_BACKGROUND_RESUME_READY selected-agent');
    await Future<void>.delayed(Duration(seconds: _backgroundSeconds + 2));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('selected-agent-workspace')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('agent-message-composer')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('agent-conversation-loading')),
      findsNothing,
    );
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    await _tapVisible(
      tester,
      const ValueKey('agent-conversation-refresh-action'),
    );
    await _waitForRefreshEnabled(tester);
    expect(find.text('Conversation refresh failed'), findsNothing);

    // ignore: avoid_print
    print('CCB_BACKGROUND_RESUME_DONE selected-agent');
  });
}

Future<void> _openServerProject(
  WidgetTester tester,
  String projectId,
  String projectName,
) async {
  await _waitFor(
    tester,
    find.byKey(const ValueKey('project-list')),
    timeout: const Duration(seconds: 45),
    diagnostics: () => _chatDiagnostics(tester),
  );
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
    diagnostics: () => _chatDiagnostics(tester),
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
    diagnostics: () => _chatDiagnostics(tester),
  );
  await _waitFor(
    tester,
    find.byKey(const ValueKey('agent-message-composer')),
    timeout: const Duration(seconds: 30),
    diagnostics: () => _chatDiagnostics(tester),
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
  await _waitFor(tester, finder, diagnostics: () => _chatDiagnostics(tester));
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
