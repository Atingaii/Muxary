import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment('CCB_MOBILE_RECOVERY_PROJECT_ID');
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_RECOVERY_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_RECOVERY_AGENT',
  defaultValue: 'mobile_probe',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('explicit refresh recovers after adb reverse is restored', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('recovery smoke project id is required');
    }

    app.main();

    await _waitForProjectList(tester);
    await _waitForRenderedText(
      tester,
      _projectName,
      timeout: const Duration(seconds: 15),
    );

    // First prove the server-wide project catalog fails visibly and recovers
    // through Retry when the emulator loses the host gateway mapping.
    // ignore: avoid_print
    print('CCB_RECOVERY_READY_REMOVE_REVERSE project-list');
    await tester.pump(const Duration(seconds: 2));

    final projectListFailure = Stopwatch()..start();
    await _tapVisible(tester, const ValueKey('project-list-refresh-action'));
    await _waitFor(
      tester,
      find.byKey(const ValueKey('project-list-load-error')),
      timeout: const Duration(seconds: 45),
      diagnostics: () => _chatDiagnostics(tester),
    );
    projectListFailure.stop();

    // ignore: avoid_print
    print('CCB_RECOVERY_READY_RESTORE_REVERSE project-list');
    await tester.pump(const Duration(seconds: 2));

    final projectListRecovery = Stopwatch()..start();
    await _tapVisible(tester, const ValueKey('project-list-retry-button'));
    await _waitForProjectList(tester);
    await _waitForRenderedText(
      tester,
      _projectName,
      timeout: const Duration(seconds: 45),
    );
    projectListRecovery.stop();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForRefreshEnabled(tester);

    // The host-side runner watches stdout for these markers and removes the
    // adb reverse mapping before the app triggers a real gateway refresh.
    // ignore: avoid_print
    print('CCB_RECOVERY_READY_REMOVE_REVERSE');
    await tester.pump(const Duration(seconds: 2));

    final conversationFailure = Stopwatch()..start();
    await _tapVisible(
      tester,
      const ValueKey('agent-conversation-refresh-action'),
    );
    await _waitForConversationRefreshFailure(tester);
    conversationFailure.stop();

    // The host-side runner restores the adb reverse mapping after this line.
    // The next explicit refresh must clear the failure item without reopening
    // the project or recreating the app.
    // ignore: avoid_print
    print('CCB_RECOVERY_READY_RESTORE_REVERSE');
    await tester.pump(const Duration(seconds: 2));

    await _waitForRefreshEnabled(tester);
    final conversationRecovery = Stopwatch()..start();
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
    conversationRecovery.stop();

    expect(
      find.byKey(const ValueKey('agent-message-composer')),
      findsOneWidget,
    );
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    // ignore: avoid_print
    print(
      'CCB_RECOVERY_TIMING_JSON ${jsonEncode({'project_list_refresh_to_error_ms': projectListFailure.elapsedMilliseconds, 'project_list_retry_to_recovered_ms': projectListRecovery.elapsedMilliseconds, 'conversation_refresh_to_error_ms': conversationFailure.elapsedMilliseconds, 'conversation_retry_to_recovered_ms': conversationRecovery.elapsedMilliseconds})}',
    );
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
