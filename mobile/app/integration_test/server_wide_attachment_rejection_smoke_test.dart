import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:file_picker/src/platform/file_picker_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/features/agent_chat/selected_agent_workspace.dart';
import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment(
  'CCB_MOBILE_ATTACHMENT_REJECTION_PROJECT_ID',
);
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_ATTACHMENT_REJECTION_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_ATTACHMENT_REJECTION_AGENT',
  defaultValue: 'mobile_probe',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('server-wide attachment rejection does not create a draft', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('attachment rejection project id is required');
    }

    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-attachment-rejection-',
    );
    final unsupported = await _writeText(tempDir, 'installer.exe');
    final tooLarge = await _writeLargeFile(
      tempDir,
      'too-large.pdf',
      agentMessageMaxAttachmentBytes + 1,
    );
    FilePickerPlatform.instance = _FakeFilePicker([
      _picker(unsupported),
      _picker(tooLarge),
    ]);
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForComposerActionsEnabled(tester);

    await _tapVisible(tester, const ValueKey('agent-attachment-button'));
    await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
    await _waitForText(
      tester,
      'installer.exe is not a supported attachment type',
    );
    expect(find.byKey(const ValueKey('agent-attachment-tray')), findsNothing);
    await _waitForTextGone(
      tester,
      'installer.exe is not a supported attachment type',
    );
    await _waitForComposerActionsEnabled(tester);

    await _tapVisible(tester, const ValueKey('agent-attachment-button'));
    await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
    await _waitForText(tester, 'too-large.pdf is larger than 25 MB');
    expect(find.byKey(const ValueKey('agent-attachment-tray')), findsNothing);
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    // ignore: avoid_print
    print('CCB_ATTACHMENT_REJECTION_SMOKE_DONE');
  });
}

Future<File> _writeText(Directory dir, String fileName) async {
  final file = File('${dir.path}/$fileName');
  return file.writeAsString('unsupported fixture $fileName');
}

Future<File> _writeLargeFile(
  Directory dir,
  String fileName,
  int sizeBytes,
) async {
  final file = File('${dir.path}/$fileName');
  final sink = file.openWrite();
  final chunk = List<int>.filled(1024 * 1024, 0x61);
  var remaining = sizeBytes;
  while (remaining > 0) {
    final count = remaining < chunk.length ? remaining : chunk.length;
    sink.add(chunk.take(count).toList(growable: false));
    remaining -= count;
  }
  await sink.close();
  return file;
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
  await _waitForText(tester, 'Message $agentName');
}

Future<void> _waitForComposerActionsEnabled(WidgetTester tester) async {
  await _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      return widget is IconButton &&
          widget.key is ValueKey &&
          (widget.key! as ValueKey).value == 'agent-attachment-button' &&
          widget.onPressed != null;
    }, description: 'enabled attachment action'),
  );
  await _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      return widget is IconButton &&
          widget.key is ValueKey &&
          (widget.key! as ValueKey).value == 'agent-message-send-button' &&
          widget.onPressed != null;
    }, description: 'enabled send action'),
  );
}

Future<void> _tapVisible(WidgetTester tester, Key key) async {
  final finder = find.byKey(key);
  await _waitFor(tester, finder);
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> _waitForText(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 15),
}) {
  return _waitFor(tester, find.text(text), timeout: timeout);
}

Future<void> _waitForTextGone(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 8),
}) {
  return _waitForAbsent(tester, find.text(text), timeout: timeout);
}

Future<void> _waitForConversationBody(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 30),
}) {
  return _waitFor(
    tester,
    _renderedTextContaining(text, description: 'conversation body $text'),
    timeout: timeout,
  );
}

Finder _renderedTextContaining(String text, {required String description}) {
  return find.byWidgetPredicate((widget) {
    if (widget is Text) {
      return widget.data?.contains(text) == true ||
          widget.textSpan?.toPlainText().contains(text) == true;
    }
    if (widget is SelectableText) {
      return widget.data?.contains(text) == true ||
          widget.textSpan?.toPlainText().contains(text) == true;
    }
    if (widget is RichText) {
      return widget.text.toPlainText().contains(text);
    }
    return false;
  }, description: description);
}

Future<void> _waitFor(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 20),
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (tester.any(finder)) {
      return;
    }
  }
  expect(finder, findsOneWidget);
}

Future<void> _waitForAbsent(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 20),
}) async {
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (!tester.any(finder)) {
      return;
    }
  }
  expect(finder, findsNothing);
}

class _FakeFilePicker extends FilePickerPlatform {
  _FakeFilePicker(this.results);

  final List<FilePickerResult?> results;
  var _index = 0;

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
    if (_index >= results.length) {
      return null;
    }
    return results[_index++];
  }
}
