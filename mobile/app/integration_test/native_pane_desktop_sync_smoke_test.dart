import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment('CCB_MOBILE_DESKTOP_SYNC_PROJECT_ID');
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_DESKTOP_SYNC_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_DESKTOP_SYNC_AGENT',
  defaultValue: 'mobile_probe',
);
const _marker = String.fromEnvironment('CCB_MOBILE_DESKTOP_SYNC_MARKER');
const _idleBeforeRefreshSeconds = int.fromEnvironment(
  'CCB_MOBILE_DESKTOP_SYNC_IDLE_SECONDS',
  defaultValue: 30,
);
const _latestBackfillText = String.fromEnvironment(
  'CCB_MOBILE_DESKTOP_SYNC_LATEST_TEXT',
);
const _oldestBackfillText = String.fromEnvironment(
  'CCB_MOBILE_DESKTOP_SYNC_OLDEST_TEXT',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('desktop pane input appears after explicit refresh', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty || _marker.trim().isEmpty) {
      throw TestFailure('desktop sync smoke dart-defines are required');
    }

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForRefreshEnabled(tester);

    final useScrolledAwayPath =
        _latestBackfillText.trim().isNotEmpty &&
        _oldestBackfillText.trim().isNotEmpty;
    if (useScrolledAwayPath) {
      await _waitForConversationBody(
        tester,
        _latestBackfillText,
        timeout: const Duration(seconds: 60),
      );
      final dragCount = await _dragTimelineUntilConversationBody(
        tester,
        _oldestBackfillText,
        timeout: const Duration(seconds: 90),
      );
      await _waitForTimelineAwayFromEnd(tester);
      await _clearExistingNewMessagesAndReturnAway(tester, _oldestBackfillText);
      // ignore: avoid_print
      print('CCB_DESKTOP_SYNC_SCROLLED_AWAY $dragCount');
    }

    expect(_renderedTextContaining(_marker), findsNothing);
    // The host-side smoke runner waits for this line, then writes directly to
    // the real tmux pane. The following idle window verifies that the app does
    // not pick the marker up through blind fixed polling before user refresh.
    // ignore: avoid_print
    print('CCB_DESKTOP_SYNC_READY $_marker');
    await tester.pump(Duration(seconds: _idleBeforeRefreshSeconds));
    expect(_renderedTextContaining(_marker), findsNothing);

    if (useScrolledAwayPath) {
      await _refreshUntilNewMessageAffordance(
        tester,
        timeout: const Duration(seconds: 60),
      );
      await _waitForTimelineAwayFromEnd(tester);
      await _tapVisible(tester, const ValueKey('agent-new-messages-jump'));
      await _waitForTimelineNearEnd(tester);
      await _waitForConversationBody(
        tester,
        _marker,
        timeout: const Duration(seconds: 45),
      );
    } else {
      await _tapVisible(
        tester,
        const ValueKey('agent-conversation-refresh-action'),
      );
      await _waitForConversationBody(
        tester,
        _marker,
        timeout: const Duration(seconds: 45),
      );
    }

    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);
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
  );
  await _waitForConversationBody(
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

Future<int> _dragTimelineUntilConversationBody(
  WidgetTester tester,
  String body, {
  required Duration timeout,
}) async {
  final finder = _renderedTextContaining(
    body,
    description: 'conversation body $body',
  );
  final timeline = find.byKey(const ValueKey('agent-chat-timeline'));
  final stopwatch = Stopwatch()..start();
  var drags = 0;
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (tester.any(finder)) {
      return drags;
    }
    await _waitFor(tester, timeline, timeout: const Duration(seconds: 5));
    await tester.drag(timeline, const Offset(0, 720));
    drags += 1;
    await tester.pump(const Duration(milliseconds: 250));
  }
  throw TestFailure(
    'Timed out waiting for older conversation body after $drags drags: '
    '$body. ${_chatDiagnostics(tester)}',
  );
}

Future<void> _refreshUntilNewMessageAffordance(
  WidgetTester tester, {
  required Duration timeout,
}) async {
  final jump = find.byKey(const ValueKey('agent-new-messages-jump'));
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (tester.any(jump)) {
      return;
    }
    await _waitForRefreshEnabled(tester);
    await _tapVisible(
      tester,
      const ValueKey('agent-conversation-refresh-action'),
    );
    for (var i = 0; i < 20; i += 1) {
      await tester.pump(const Duration(milliseconds: 100));
      if (tester.any(jump)) {
        return;
      }
    }
  }
  throw TestFailure(
    'Timed out waiting for New messages after refresh. '
    '${_chatDiagnostics(tester)}',
  );
}

Future<void> _clearExistingNewMessagesAndReturnAway(
  WidgetTester tester,
  String anchorBody,
) async {
  final jump = find.byKey(const ValueKey('agent-new-messages-jump'));
  if (!tester.any(jump)) {
    return;
  }
  await _tapVisible(tester, const ValueKey('agent-new-messages-jump'));
  await _waitForTimelineNearEnd(tester);
  await _dragTimelineUntilConversationBody(
    tester,
    anchorBody,
    timeout: const Duration(seconds: 45),
  );
  await _waitForTimelineAwayFromEnd(tester);
}

Future<void> _waitForTimelineAwayFromEnd(WidgetTester tester) async {
  await _waitFor(
    tester,
    find.byKey(const ValueKey('agent-chat-timeline')),
    timeout: const Duration(seconds: 5),
  );
  final distance = _timelineDistanceFromEnd(tester);
  if (distance <= 72) {
    throw TestFailure(
      'Expected timeline away from end, distance=$distance. '
      '${_chatDiagnostics(tester)}',
    );
  }
}

Future<void> _waitForTimelineNearEnd(WidgetTester tester) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < const Duration(seconds: 10)) {
    await tester.pump(const Duration(milliseconds: 100));
    if (_timelineDistanceFromEnd(tester) <= 72) {
      return;
    }
  }
  throw TestFailure(
    'Timed out waiting for timeline near end, '
    'distance=${_timelineDistanceFromEnd(tester)}. '
    '${_chatDiagnostics(tester)}',
  );
}

double _timelineDistanceFromEnd(WidgetTester tester) {
  final timeline = tester.widget<ListView>(
    find.byKey(const ValueKey('agent-chat-timeline')),
  );
  final controller = timeline.controller;
  if (controller == null || !controller.hasClients) {
    throw TestFailure('agent chat timeline has no attached controller');
  }
  return controller.position.maxScrollExtent - controller.position.pixels;
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

Future<void> _waitForConversationBody(
  WidgetTester tester,
  String body, {
  Duration timeout = const Duration(seconds: 10),
}) {
  return _waitFor(
    tester,
    _renderedTextContaining(body, description: 'conversation body $body'),
    timeout: timeout,
    diagnostics: () => _chatDiagnostics(tester),
  );
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
      .take(40)
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
