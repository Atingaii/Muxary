import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/features/agent_chat/conversation_bubble.dart';
import 'package:ccb_mobile/main.dart' as app;
import 'package:ccb_mobile/models/ccb_conversation_item.dart';

const _projectId = String.fromEnvironment('CCB_MOBILE_NATIVE_PROJECT_ID');
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_PROJECT_NAME',
  defaultValue: 'test_ccb2_native',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_AGENT',
  defaultValue: 'mobile_probe',
);
const _prompt = String.fromEnvironment('CCB_MOBILE_NATIVE_PROMPT');
const _expectedReply = String.fromEnvironment('CCB_MOBILE_NATIVE_EXPECTED');
const _expectedMode = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_EXPECTED_MODE',
  defaultValue: 'agent_reply',
);
const _requireLiveTerminalExpected = bool.fromEnvironment(
  'CCB_MOBILE_NATIVE_REQUIRE_LIVE_TERMINAL_EXPECTED',
);
const _linePrefix = String.fromEnvironment('CCB_MOBILE_NATIVE_LINE_PREFIX');
const _minLinePrefixCount = int.fromEnvironment(
  'CCB_MOBILE_NATIVE_MIN_LINE_PREFIX_COUNT',
);
const _maxNonLocalItems = int.fromEnvironment(
  'CCB_MOBILE_NATIVE_MAX_NON_LOCAL_ITEMS',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('paired mobile chat sends native pane input', (tester) async {
    if (_projectId.trim().isEmpty ||
        _prompt.trim().isEmpty ||
        _expectedReply.trim().isEmpty) {
      throw TestFailure('native pane smoke dart-defines are required');
    }

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForComposerActionsEnabled(tester);
    await _enterTextVisible(
      tester,
      const ValueKey('agent-message-composer'),
      _prompt,
    );
    // ignore: avoid_print, host harness may start device metrics from here.
    print('CCB_MOBILE_NATIVE_READY_TO_SEND');
    final sendStopwatch = await _tapVisibleTimed(
      tester,
      const ValueKey('agent-message-send-button'),
      settleAfterTap: false,
    );
    final firstLocalState = await _waitForPromptAndFirstFeedback(
      tester,
      prompt: _prompt,
      expectedReply: _expectedReply,
      stopwatch: sendStopwatch,
    );
    await _waitForConversationBody(
      tester,
      _prompt,
      timeout: const Duration(seconds: 30),
    );
    final expectedReplyTimeout = _expectedReplyTimeout();
    switch (_expectedMode) {
      case 'agent_reply':
        await _waitForConversationItemBody(
          tester,
          title: 'Agent reply',
          _expectedReply,
          timeout: expectedReplyTimeout,
        );
        break;
      case 'any_non_local':
        await _waitForNonLocalConversationBody(
          tester,
          _expectedReply,
          timeout: expectedReplyTimeout,
        );
        break;
      default:
        throw TestFailure(
          'Unsupported CCB_MOBILE_NATIVE_EXPECTED_MODE=$_expectedMode',
        );
    }
    if (_requireLiveTerminalExpected) {
      await _waitForConversationItemBody(
        tester,
        _expectedReply,
        title: 'Terminal output',
        timeout: const Duration(minutes: 2),
      );
    }
    if (_minLinePrefixCount > 0) {
      if (_linePrefix.trim().isEmpty) {
        throw TestFailure(
          'CCB_MOBILE_NATIVE_LINE_PREFIX is required when '
          'CCB_MOBILE_NATIVE_MIN_LINE_PREFIX_COUNT is set',
        );
      }
      await _waitForNonLocalLinePrefixCount(
        tester,
        prefix: _linePrefix,
        minCount: _minLinePrefixCount,
        timeout: expectedReplyTimeout,
      );
    }
    final expectedReplyVisibleMs = sendStopwatch.elapsedMilliseconds;
    final nonLocalItemCount = _conversationItemCount(includeLocal: false);
    if (_maxNonLocalItems > 0 && nonLocalItemCount > _maxNonLocalItems) {
      throw TestFailure(
        'Expected at most $_maxNonLocalItems non-local conversation items, '
        'found $nonLocalItemCount. ${_chatDiagnostics(tester)}',
      );
    }
    final linePrefixCount =
        _linePrefix.trim().isEmpty
            ? null
            : _conversationLinePrefixCount(
              tester,
              includeLocal: false,
              prefix: _linePrefix,
            );
    final timingPayload = {
      'schema_version': 1,
      'project_id': _projectId,
      'project_name': _projectName,
      'agent': _agentName,
      'send_to_local_bubble_ms': firstLocalState.localBubbleMs,
      'send_to_working_ms': firstLocalState.workingMs,
      'send_to_first_feedback_ms': firstLocalState.firstFeedbackMs,
      'first_feedback_kind': firstLocalState.firstFeedbackKind,
      'send_to_expected_reply_ms': expectedReplyVisibleMs,
      'non_local_item_count': nonLocalItemCount,
      'expected_reply_item_count': _conversationItemCountContaining(
        tester,
        includeLocal: false,
        body: _expectedReply,
        excludeTitle: 'You',
      ),
      'live_terminal_output_item_count': _conversationItemCount(
        includeLocal: false,
        title: 'Terminal output',
      ),
      'live_terminal_output_expected_item_count':
          _conversationItemCountContaining(
            tester,
            includeLocal: false,
            title: 'Terminal output',
            body: _expectedReply,
          ),
      'line_prefix': _linePrefix.trim().isEmpty ? null : _linePrefix,
      'line_prefix_count': linePrefixCount,
      'min_line_prefix_count':
          _minLinePrefixCount > 0 ? _minLinePrefixCount : null,
      'max_non_local_items': _maxNonLocalItems > 0 ? _maxNonLocalItems : null,
      'expected_mode': _expectedMode,
    };

    // ignore: avoid_print, integration harness parses this stdout marker.
    print('CCB_MOBILE_NATIVE_TIMING_JSON ${jsonEncode(timingPayload)}');

    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);
  });
}

Duration _expectedReplyTimeout() {
  if (_minLinePrefixCount >= 1000) {
    return const Duration(minutes: 18);
  }
  if (_minLinePrefixCount >= 200) {
    return const Duration(minutes: 8);
  }
  return const Duration(minutes: 4);
}

Future<void> _waitForNonLocalLinePrefixCount(
  WidgetTester tester, {
  required String prefix,
  required int minCount,
  Duration timeout = const Duration(seconds: 10),
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    final count = _conversationLinePrefixCount(
      tester,
      includeLocal: false,
      prefix: prefix,
    );
    if (count >= minCount) {
      return;
    }
  }
  final count = _conversationLinePrefixCount(
    tester,
    includeLocal: false,
    prefix: prefix,
  );
  throw TestFailure(
    'Timed out waiting for at least $minCount non-local lines starting with '
    '$prefix; found $count. ${_chatDiagnostics(tester)}',
  );
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

Future<void> _enterTextVisible(
  WidgetTester tester,
  Key key,
  String value,
) async {
  final finder = find.byKey(key, skipOffstage: false);
  await _waitFor(tester, finder);
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.enterText(find.byKey(key), value);
  await tester.pumpAndSettle();
}

Future<void> _tapVisible(
  WidgetTester tester,
  Key key, {
  bool settleAfterTap = true,
}) async {
  await _tapVisiblePrepared(tester, key, settleAfterTap: settleAfterTap);
}

Future<Stopwatch> _tapVisibleTimed(
  WidgetTester tester,
  Key key, {
  bool settleAfterTap = true,
}) async {
  return _tapVisiblePrepared(
    tester,
    key,
    settleAfterTap: settleAfterTap,
    startStopwatchBeforeTap: true,
  );
}

Future<Stopwatch> _tapVisiblePrepared(
  WidgetTester tester,
  Key key, {
  required bool settleAfterTap,
  bool startStopwatchBeforeTap = false,
}) async {
  final onstageFinder = find.byKey(key);
  final finder =
      tester.any(onstageFinder)
          ? onstageFinder
          : find.byKey(key, skipOffstage: false);
  await _waitFor(tester, finder);
  final target = finder.first;
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  final stopwatch = Stopwatch();
  if (startStopwatchBeforeTap) {
    stopwatch.start();
  }
  await tester.tap(target);
  if (settleAfterTap) {
    await tester.pumpAndSettle();
  } else {
    await tester.pump();
  }
  return stopwatch;
}

Future<void> _waitForComposerActionsEnabled(WidgetTester tester) {
  return _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      final key = widget.key;
      return key is ValueKey &&
          key.value == 'agent-message-send-button' &&
          widget is IconButton &&
          widget.onPressed != null;
    }, description: 'enabled send button'),
    timeout: const Duration(seconds: 30),
  );
}

Future<void> _waitForConversationBody(
  WidgetTester tester,
  String body, {
  Duration timeout = const Duration(seconds: 10),
  bool exact = false,
}) {
  return _waitFor(
    tester,
    _conversationBodyFinder(body, exact: exact),
    timeout: timeout,
    diagnostics: () => _chatDiagnostics(tester),
  );
}

Future<_FirstLocalStateTiming> _waitForPromptAndFirstFeedback(
  WidgetTester tester, {
  required String prompt,
  required String expectedReply,
  required Stopwatch stopwatch,
}) async {
  int? localBubbleMs;
  int? workingMs;
  int? firstFeedbackMs;
  String? firstFeedbackKind;
  final waitStopwatch = Stopwatch()..start();
  while (waitStopwatch.elapsed < const Duration(seconds: 5)) {
    await tester.pump(const Duration(milliseconds: 16));
    localBubbleMs ??=
        _hasConversationModelBody(tester, prompt, includeLocal: true)
            ? stopwatch.elapsedMilliseconds
            : null;
    workingMs ??=
        tester.any(find.byKey(const ValueKey('agent-working-status'))) &&
                tester.any(find.text('Working'))
            ? stopwatch.elapsedMilliseconds
            : null;
    if (workingMs != null && firstFeedbackMs == null) {
      firstFeedbackMs = workingMs;
      firstFeedbackKind = 'working';
    }
    if (firstFeedbackMs == null &&
        _hasNonLocalConversationText(tester, expectedReply)) {
      firstFeedbackMs = stopwatch.elapsedMilliseconds;
      firstFeedbackKind = 'expected_reply';
    }
    if (localBubbleMs != null && firstFeedbackMs != null) {
      return _FirstLocalStateTiming(
        localBubbleMs: localBubbleMs,
        workingMs: workingMs,
        firstFeedbackMs: firstFeedbackMs,
        firstFeedbackKind: firstFeedbackKind!,
      );
    }
  }
  throw TestFailure(
    'Timed out waiting for local prompt and first feedback after send. '
    'localBubbleMs=$localBubbleMs workingMs=$workingMs '
    'firstFeedbackMs=$firstFeedbackMs firstFeedbackKind=$firstFeedbackKind '
    '${_chatDiagnostics(tester)}',
  );
}

Finder _conversationBodyFinder(String body, {required bool exact}) {
  return find.byWidgetPredicate((widget) {
    if (widget is ConversationBubble) {
      return exact ? widget.item.body == body : widget.item.body.contains(body);
    }
    if (widget is SelectableText) {
      final text = widget.data ?? widget.textSpan?.toPlainText() ?? '';
      return exact ? text == body : text.contains(body);
    }
    if (widget is Text) {
      final text = widget.data ?? widget.textSpan?.toPlainText() ?? '';
      return exact ? text == body : text.contains(body);
    }
    return false;
  }, description: 'conversation body $body');
}

Future<void> _waitForConversationItemBody(
  WidgetTester tester,
  String body, {
  required String title,
  Duration timeout = const Duration(seconds: 10),
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (_hasConversationItemText(tester, title: title, body: body)) {
      return;
    }
  }
  throw TestFailure(
    'Timed out waiting for conversation item $title containing $body. '
    '${_chatDiagnostics(tester)}',
  );
}

Future<void> _waitForNonLocalConversationBody(
  WidgetTester tester,
  String body, {
  Duration timeout = const Duration(seconds: 10),
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (_hasNonLocalConversationText(tester, body)) {
      return;
    }
  }
  throw TestFailure(
    'Timed out waiting for non-local conversation body containing $body. '
    '${_chatDiagnostics(tester)}',
  );
}

bool _hasConversationItemText(
  WidgetTester tester, {
  required String title,
  required String body,
}) {
  for (final bubble in _conversationBubbles(tester, includeLocal: false)) {
    if (bubble.item.title == title && bubble.item.body.contains(body)) {
      return true;
    }
  }
  return false;
}

bool _hasNonLocalConversationText(WidgetTester tester, String text) {
  for (final bubble in _conversationBubbles(tester, includeLocal: false)) {
    if (bubble.item.kind == CcbConversationItemKind.userMessage) {
      continue;
    }
    if (bubble.item.body.contains(text)) {
      return true;
    }
  }
  return _hasNonLocalRenderedText(tester, text);
}

bool _hasNonLocalRenderedText(WidgetTester tester, String text) {
  final items = _conversationItemFinder(includeLocal: false);
  for (final element in items.evaluate()) {
    final item = find.byElementPredicate(
      (candidate) => candidate == element,
      description: 'non-local conversation item',
    );
    if (find
        .descendant(
          of: item,
          matching: _renderedTextContaining(
            text,
            description: 'rendered non-local text $text',
          ),
        )
        .evaluate()
        .isNotEmpty) {
      return true;
    }
  }
  return false;
}

bool _hasConversationModelBody(
  WidgetTester tester,
  String text, {
  required bool includeLocal,
}) {
  for (final bubble in _conversationBubbles(
    tester,
    includeLocal: includeLocal,
  )) {
    if (bubble.item.body.contains(text)) {
      return true;
    }
  }
  return false;
}

Finder _conversationItemFinder({required bool includeLocal}) {
  return find.byWidgetPredicate((widget) {
    final key = widget.key;
    if (key is! ValueKey<String> ||
        !key.value.startsWith('conversation-item-')) {
      return false;
    }
    return includeLocal || !key.value.startsWith('conversation-item-local-');
  });
}

int _conversationItemCount({required bool includeLocal, String? title}) {
  var count = 0;
  final items = _conversationItemFinder(includeLocal: includeLocal);
  for (final element in items.evaluate()) {
    if (title == null) {
      count += 1;
      continue;
    }
    final item = find.byElementPredicate(
      (candidate) => candidate == element,
      description: 'conversation item',
    );
    if (find
        .descendant(of: item, matching: find.text(title))
        .evaluate()
        .isNotEmpty) {
      count += 1;
    }
  }
  return count;
}

int _conversationItemCountContaining(
  WidgetTester tester, {
  required bool includeLocal,
  required String body,
  String? title,
  String? excludeTitle,
}) {
  var count = 0;
  for (final bubble in _conversationBubbles(
    tester,
    includeLocal: includeLocal,
  )) {
    final item = bubble.item;
    if (excludeTitle != null && item.title == excludeTitle) {
      continue;
    }
    final titleMatches = title == null || item.title == title;
    if (titleMatches && item.body.contains(body)) {
      count += 1;
    }
  }
  return count;
}

int _conversationLinePrefixCount(
  WidgetTester tester, {
  required bool includeLocal,
  required String prefix,
}) {
  var count = 0;
  for (final bubble in _conversationBubbles(
    tester,
    includeLocal: includeLocal,
  )) {
    for (final line in bubble.item.body.split('\n')) {
      if (line.trimLeft().startsWith(prefix)) {
        count += 1;
      }
    }
  }
  return count;
}

Iterable<ConversationBubble> _conversationBubbles(
  WidgetTester tester, {
  required bool includeLocal,
}) sync* {
  for (final bubble in tester.widgetList<ConversationBubble>(
    find.byType(ConversationBubble),
  )) {
    if (!includeLocal &&
        bubble.item.kind == CcbConversationItemKind.userMessage) {
      continue;
    }
    yield bubble;
  }
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

class _FirstLocalStateTiming {
  const _FirstLocalStateTiming({
    required this.localBubbleMs,
    required this.workingMs,
    required this.firstFeedbackMs,
    required this.firstFeedbackKind,
  });

  final int localBubbleMs;
  final int? workingMs;
  final int firstFeedbackMs;
  final String firstFeedbackKind;
}
