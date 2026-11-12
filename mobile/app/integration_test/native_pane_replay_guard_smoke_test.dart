import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:file_picker/src/platform/file_picker_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment('CCB_MOBILE_REPLAY_PROJECT_ID');
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_REPLAY_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_REPLAY_AGENT',
  defaultValue: 'mobile_probe',
);
const _prompt = String.fromEnvironment('CCB_MOBILE_REPLAY_PROMPT');
const _expectedReply = String.fromEnvironment('CCB_MOBILE_REPLAY_EXPECTED');
const _stage = String.fromEnvironment(
  'CCB_MOBILE_REPLAY_STAGE',
  defaultValue: 'full',
);
const _failureMode = String.fromEnvironment(
  'CCB_MOBILE_REPLAY_FAILURE_MODE',
  defaultValue: 'reverse',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('failed send preserves attachment and retry does not replay', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty ||
        _prompt.trim().isEmpty ||
        _expectedReply.trim().isEmpty) {
      throw TestFailure('replay guard smoke dart-defines are required');
    }

    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-replay-guard-',
    );
    final attachment = await File(
      '${tempDir.path}/replay-guard-attachment.txt',
    ).writeAsString('CCB Mobile replay guard attachment for $_expectedReply');
    FilePickerPlatform.instance = _FakeFilePicker(_picker(attachment));
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (_stage != 'fail' && await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    if (_stage == 'retry') {
      await _assertFailedDraftVisible(tester);
      await _retryAndExpectReply(tester);
      return;
    }

    await _prepareDraftAndFailSend(tester);
    if (_stage == 'fail') {
      // ignore: avoid_print
      print('CCB_REPLAY_GUARD_FAILED_PERSIST_READY');
      return;
    }

    // Host-side runner restores adb reverse when this marker appears. Retry is
    // explicit and user-visible, so duplicate input replay is caught by the
    // source-side transcript verification after Flutter exits.
    // ignore: avoid_print
    print('CCB_REPLAY_GUARD_RESTORE_REVERSE_READY');
    await Future<void>.delayed(const Duration(seconds: 2));
    await _retryAndExpectReply(tester);
  });
}

Future<void> _prepareDraftAndFailSend(WidgetTester tester) async {
  await _waitForComposerActionsEnabled(tester);
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    _prompt,
  );
  await _tapVisible(tester, const ValueKey('agent-attachment-button'));
  await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
  await _waitForConversationBody(tester, 'replay-guard-attachment.txt');

  // Host-side runner breaks connectivity when this marker appears. The
  // following delay lets the real emulator routing failure take effect before
  // the app attempts upload/send.
  // ignore: avoid_print
  print(
    _failureMode == 'gateway'
        ? 'CCB_REPLAY_GUARD_STOP_GATEWAY_READY'
        : 'CCB_REPLAY_GUARD_REMOVE_REVERSE_READY',
  );
  await Future<void>.delayed(const Duration(seconds: 2));
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForText(tester, 'Retry', timeout: const Duration(seconds: 45));
  await _waitForConversationBody(tester, _prompt);
  await _waitForConversationBody(tester, 'replay-guard-attachment.txt');
}

Future<void> _assertFailedDraftVisible(WidgetTester tester) async {
  await _waitForText(tester, 'Retry', timeout: const Duration(seconds: 45));
  await _waitForConversationBody(tester, _prompt);
  await _waitForConversationBody(tester, 'replay-guard-attachment.txt');
}

Future<void> _retryAndExpectReply(WidgetTester tester) async {
  await _tapFinderVisible(tester, find.text('Retry'));
  await _waitForConversationBody(
    tester,
    _expectedReply,
    timeout: const Duration(minutes: 4),
    exact: true,
  );

  expect(find.textContaining('CCB_REQ_ID'), findsNothing);
  expect(find.text('mobile_gateway'), findsNothing);
  expect(find.text('completion_snapshot'), findsNothing);

  // ignore: avoid_print
  print('CCB_REPLAY_GUARD_DONE');
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

Future<void> _enterTextVisible(
  WidgetTester tester,
  Key key,
  String value,
) async {
  final finder = find.byKey(key, skipOffstage: false);
  await _waitFor(tester, finder, diagnostics: () => _chatDiagnostics(tester));
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
  await _waitFor(tester, finder, diagnostics: () => _chatDiagnostics(tester));
  await _tapFinderVisible(tester, finder);
}

Future<void> _tapFinderVisible(WidgetTester tester, Finder finder) async {
  await _waitFor(tester, finder, diagnostics: () => _chatDiagnostics(tester));
  final target = finder.first;
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Future<void> _waitForText(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 10),
}) {
  return _waitFor(
    tester,
    find.text(text),
    timeout: timeout,
    diagnostics: () => _chatDiagnostics(tester),
  );
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
    diagnostics: () => _chatDiagnostics(tester),
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
  final detail = diagnostics == null ? '' : ': ${diagnostics()}';
  throw TestFailure('Timed out waiting for $finder$detail');
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
  final visibleTexts = find
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
  return 'visibleText=$visibleTexts';
}

FilePickerResult _picker(File file) {
  return FilePickerResult([
    PlatformFile(
      name: file.uri.pathSegments.last,
      path: file.path,
      size: file.lengthSync(),
    ),
  ]);
}

class _FakeFilePicker extends FilePickerPlatform {
  _FakeFilePicker(this.result);

  final FilePickerResult result;
  var _used = false;

  @override
  Future<FilePickerResult?> pickFiles({
    String? dialogTitle,
    String? initialDirectory,
    FileType type = FileType.any,
    List<String>? allowedExtensions,
    Function(FilePickerStatus)? onFileLoading,
    int compressionQuality = 0,
    bool allowMultiple = false,
    bool withData = false,
    bool withReadStream = false,
    bool lockParentWindow = false,
    bool readSequential = false,
    bool cancelUploadOnWindowBlur = true,
  }) async {
    if (_used) {
      return null;
    }
    _used = true;
    return result;
  }
}
