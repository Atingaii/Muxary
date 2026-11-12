import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment('CCB_MOBILE_REPAIR_PROJECT_ID');
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_REPAIR_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_REPAIR_AGENT',
  defaultValue: 'mobile_probe',
);
const _gatewayUrl = String.fromEnvironment('CCB_MOBILE_REPAIR_GATEWAY_URL');
const _repairPairingCode = String.fromEnvironment(
  'CCB_MOBILE_REPAIR_PAIRING_CODE',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('revoked device fails closed and re-pair restores access', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('re-pair smoke project id is required');
    }
    if (_gatewayUrl.trim().isEmpty || _repairPairingCode.trim().isEmpty) {
      throw TestFailure('re-pair smoke gateway URL and pairing code required');
    }

    app.main();

    await _waitForProjectList(tester);
    await _waitForRenderedText(
      tester,
      _projectName,
      timeout: const Duration(seconds: 15),
    );
    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForRefreshEnabled(tester);

    // Host-side runner revokes the current paired device after this marker.
    // The next protected selected-agent refresh must fail closed.
    // ignore: avoid_print
    print('CCB_REPAIR_READY_REVOKE');
    await tester.pump(const Duration(seconds: 2));

    await _tapVisible(
      tester,
      const ValueKey('agent-conversation-refresh-action'),
    );
    await _waitForConversationRefreshFailure(tester);

    await _claimReplacementPairing(tester);

    await _ensureProjectOpen(tester);
    await _selectAgent(tester, _agentName);
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

    // ignore: avoid_print
    print('CCB_REPAIR_DONE');
  });
}

Future<void> _claimReplacementPairing(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('connection-details-action'));
  await _expandPanel(
    tester,
    const ValueKey('gateway-pairing-panel'),
    childKey: const ValueKey('gateway-url-field'),
  );
  await _enterTextVisible(
    tester,
    const ValueKey('gateway-url-field'),
    _gatewayUrl,
  );
  await _enterTextVisible(
    tester,
    const ValueKey('pairing-code-field'),
    _repairPairingCode,
  );
  await _enterTextVisible(
    tester,
    const ValueKey('pairing-device-name-field'),
    'Android Emulator Re-Pair Smoke',
  );
  await _tapVisible(tester, const ValueKey('gateway-pairing-claim-button'));
  await _waitForRenderedText(
    tester,
    'Gateway paired',
    timeout: const Duration(seconds: 45),
  );
  await _dismissCurrentRoute(
    tester,
    goneKey: const ValueKey('connection-details-panel'),
  );
}

Future<void> _ensureProjectOpen(WidgetTester tester) async {
  if (tester.any(find.byKey(const ValueKey('selected-agent-workspace')))) {
    return;
  }
  await _openServerProject(tester, _projectId, _projectName);
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

Future<void> _expandPanel(
  WidgetTester tester,
  Key panelKey, {
  required Key childKey,
}) async {
  if (tester.any(find.byKey(childKey))) {
    return;
  }
  await _tapVisible(tester, panelKey);
  await _waitFor(tester, find.byKey(childKey));
}

Future<void> _dismissCurrentRoute(
  WidgetTester tester, {
  required Key goneKey,
}) async {
  final goneFinder = find.byKey(goneKey);
  for (var attempt = 0; attempt < 4; attempt += 1) {
    if (!tester.any(goneFinder)) {
      return;
    }
    await tester.binding.handlePopRoute();
    await tester.pumpAndSettle();
    if (!tester.any(goneFinder)) {
      return;
    }
    final close = find.byTooltip('Close');
    if (tester.any(close)) {
      await tester.tap(close);
    } else if (tester.any(find.byTooltip('Back'))) {
      await tester.tap(find.byTooltip('Back'));
    }
    await tester.pumpAndSettle();
  }
  throw TestFailure('Timed out dismissing route with $goneKey');
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
