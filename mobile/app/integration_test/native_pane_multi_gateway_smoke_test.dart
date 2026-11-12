import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectAlphaId = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ALPHA_PROJECT_ID',
);
const _projectAlphaName = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ALPHA_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _projectBetaId = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_BETA_PROJECT_ID',
);
const _projectBetaName = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_BETA_PROJECT_NAME',
  defaultValue: 'test_ccb2_beta',
);
const _alphaAgent = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ALPHA_AGENT',
  defaultValue: 'mobile_probe',
);
const _betaAgent = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_BETA_AGENT',
  defaultValue: 'mobile_peer',
);
const _alphaPrompt = String.fromEnvironment('CCB_MOBILE_NATIVE_ALPHA_PROMPT');
const _alphaExpected = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ALPHA_EXPECTED',
);
const _betaPrompt = String.fromEnvironment('CCB_MOBILE_NATIVE_BETA_PROMPT');
const _betaExpected = String.fromEnvironment('CCB_MOBILE_NATIVE_BETA_EXPECTED');

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('paired mobile chat sends native pane input across projects', (
    tester,
  ) async {
    if (_projectAlphaId.trim().isEmpty ||
        _projectBetaId.trim().isEmpty ||
        _alphaPrompt.trim().isEmpty ||
        _alphaExpected.trim().isEmpty ||
        _betaPrompt.trim().isEmpty ||
        _betaExpected.trim().isEmpty) {
      throw TestFailure('multi native pane smoke dart-defines are required');
    }

    app.main();

    await _openServerProject(tester, _projectAlphaId, _projectAlphaName);
    await _sendNativeTurn(
      tester,
      agentName: _alphaAgent,
      prompt: _alphaPrompt,
      expectedReply: _alphaExpected,
    );

    await _tapVisible(tester, const ValueKey('project-back-button'));
    await _openServerProject(tester, _projectBetaId, _projectBetaName);
    await _sendNativeTurn(
      tester,
      agentName: _betaAgent,
      prompt: _betaPrompt,
      expectedReply: _betaExpected,
    );

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

Future<void> _sendNativeTurn(
  WidgetTester tester, {
  required String agentName,
  required String prompt,
  required String expectedReply,
}) async {
  await _selectAgent(tester, agentName);
  await _waitForComposerActionsEnabled(tester);
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    prompt,
  );
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(
    tester,
    prompt,
    timeout: const Duration(seconds: 30),
  );
  await _waitForConversationBody(
    tester,
    expectedReply,
    timeout: const Duration(minutes: 4),
    exact: true,
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
    exact
        ? _renderedTextEquals(body, description: 'conversation body $body')
        : _renderedTextContaining(body, description: 'conversation body $body'),
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

Finder _renderedTextEquals(String text, {String? description}) {
  return find.byWidgetPredicate((widget) {
    if (widget is SelectableText) {
      return (widget.data ?? widget.textSpan?.toPlainText() ?? '').trim() ==
          text;
    }
    if (widget is Text) {
      return (widget.data ?? widget.textSpan?.toPlainText() ?? '').trim() ==
          text;
    }
    if (widget is RichText) {
      return widget.text.toPlainText().trim() == text;
    }
    return false;
  }, description: description ?? 'rendered text equal to $text');
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
