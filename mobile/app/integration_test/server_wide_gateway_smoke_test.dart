import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:file_picker/file_picker.dart';
import 'package:file_picker/src/platform/file_picker_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectAlphaId = String.fromEnvironment(
  'CCB_MOBILE_SERVER_PROJECT_ALPHA_ID',
);
const _projectAlphaName = String.fromEnvironment(
  'CCB_MOBILE_SERVER_PROJECT_ALPHA_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _projectBetaId = String.fromEnvironment(
  'CCB_MOBILE_SERVER_PROJECT_BETA_ID',
);
const _projectBetaName = String.fromEnvironment(
  'CCB_MOBILE_SERVER_PROJECT_BETA_NAME',
  defaultValue: 'test_ccb2_beta',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_AGENT',
  defaultValue: 'mobile_probe',
);
const _secondaryAgentName = String.fromEnvironment(
  'CCB_MOBILE_SECONDARY_AGENT',
  defaultValue: 'mobile_peer',
);
const _backfillEnabled = bool.fromEnvironment('CCB_MOBILE_BACKFILL_ENABLED');
const _backfillOnly = bool.fromEnvironment('CCB_MOBILE_BACKFILL_ONLY');
const _backfillProjectId = String.fromEnvironment(
  'CCB_MOBILE_BACKFILL_PROJECT_ID',
);
const _backfillProjectName = String.fromEnvironment(
  'CCB_MOBILE_BACKFILL_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _backfillAgentName = String.fromEnvironment(
  'CCB_MOBILE_BACKFILL_AGENT',
  defaultValue: 'mobile_probe',
);
const _backfillLatestText = String.fromEnvironment(
  'CCB_MOBILE_BACKFILL_LATEST_TEXT',
);
const _backfillOldestText = String.fromEnvironment(
  'CCB_MOBILE_BACKFILL_OLDEST_TEXT',
);
const _nativeArtifactTextFileName = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ARTIFACT_TEXT_FILE_NAME',
);
const _nativeArtifactImageFileName = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ARTIFACT_IMAGE_FILE_NAME',
);
const _nativeArtifactTextSha256 = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ARTIFACT_TEXT_SHA256',
);
const _nativeArtifactImageSha256 = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ARTIFACT_IMAGE_SHA256',
);
const _nativeArtifactMarker = String.fromEnvironment(
  'CCB_MOBILE_NATIVE_ARTIFACT_MARKER',
);
const _uploadStressBytes = int.fromEnvironment(
  'CCB_MOBILE_UPLOAD_STRESS_BYTES',
);
const _replyTimeout = Duration(seconds: 120);
const _onePixelPngBytes = <int>[
  137,
  80,
  78,
  71,
  13,
  10,
  26,
  10,
  0,
  0,
  0,
  13,
  73,
  72,
  68,
  82,
  0,
  0,
  0,
  1,
  0,
  0,
  0,
  1,
  8,
  6,
  0,
  0,
  0,
  31,
  21,
  196,
  137,
  0,
  0,
  0,
  13,
  73,
  68,
  65,
  84,
  120,
  156,
  99,
  248,
  15,
  4,
  0,
  9,
  251,
  3,
  253,
  167,
  156,
  129,
  226,
  0,
  0,
  0,
  0,
  73,
  69,
  68,
  174,
  66,
  96,
  130,
];

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
    'server-wide local gateway lists projects and exercises chat files artifacts',
    (tester) async {
      if (_backfillOnly) {
        return;
      }
      if (_projectAlphaId.trim().isEmpty || _projectBetaId.trim().isEmpty) {
        throw TestFailure('server project ids are required');
      }

      final originalPicker = FilePickerPlatform.instance;
      final tempDir = await Directory.systemTemp.createTemp(
        'ccb-mobile-server-wide-avd-',
      );
      final suffix = DateTime.now().millisecondsSinceEpoch;
      final alphaProbeOne = await _writeText(
        tempDir,
        'alpha-$_agentName-turn-1-$suffix.txt',
      );
      final alphaProbeTwo = await _writeText(
        tempDir,
        'alpha-$_agentName-turn-2-$suffix.txt',
      );
      final alphaPeerOne = await _writeText(
        tempDir,
        'alpha-$_secondaryAgentName-turn-1-$suffix.txt',
      );
      final betaProbeOne = await _writeText(
        tempDir,
        'beta-$_agentName-turn-1-$suffix.txt',
      );
      final alphaProbeImage = await _writePng(
        tempDir,
        'alpha-$_agentName-image-$suffix.png',
      );
      final alphaPeerImage = await _writePng(
        tempDir,
        'alpha-$_secondaryAgentName-image-$suffix.png',
      );
      final betaDoc =
          _uploadStressBytes > 0
              ? await _writeSizedText(
                tempDir,
                'beta-$_agentName-upload-stress-$suffix.txt',
                _uploadStressBytes,
              )
              : await _writeText(tempDir, 'beta-$_agentName-doc-$suffix.txt');

      FilePickerPlatform.instance = _FakeFilePicker([
        _picker(alphaProbeOne),
        _picker(alphaProbeTwo),
        _picker(alphaProbeImage),
        _picker(alphaPeerOne),
        _picker(alphaPeerImage),
        _picker(betaProbeOne),
        _picker(betaDoc),
      ]);
      addTearDown(() async {
        FilePickerPlatform.instance = originalPicker;
        if (await tempDir.exists()) {
          await tempDir.delete(recursive: true);
        }
      });

      app.main();

      await _openServerProject(tester, _projectAlphaId, _projectAlphaName);
      await _downloadSeededNativeArtifactsIfPresent(
        tester,
        agentName: _agentName,
      );
      await _sendTextFileAndDownload(
        tester,
        agentName: _agentName,
        ident: 'alpha-probe-round-1-$suffix',
        triggerFileName: alphaProbeOne.uri.pathSegments.last,
        triggerFileSha256: await _fileSha256(alphaProbeOne),
      );
      await _sendTextFileAndDownload(
        tester,
        agentName: _agentName,
        ident: 'alpha-probe-round-2-$suffix',
        triggerFileName: alphaProbeTwo.uri.pathSegments.last,
        triggerFileSha256: await _fileSha256(alphaProbeTwo),
      );
      await _sendImageAndWait(
        tester,
        agentName: _agentName,
        fileName: alphaProbeImage.uri.pathSegments.last,
        fileSha256: await _fileSha256(alphaProbeImage),
      );
      await _sendTextFileAndDownload(
        tester,
        agentName: _secondaryAgentName,
        ident: 'alpha-peer-round-1-$suffix',
        triggerFileName: alphaPeerOne.uri.pathSegments.last,
        triggerFileSha256: await _fileSha256(alphaPeerOne),
      );
      await _sendImageAndWait(
        tester,
        agentName: _secondaryAgentName,
        fileName: alphaPeerImage.uri.pathSegments.last,
        fileSha256: await _fileSha256(alphaPeerImage),
      );
      await _tapVisible(tester, const ValueKey('project-back-button'));
      await _openServerProject(tester, _projectBetaId, _projectBetaName);
      await _sendTextFileAndDownload(
        tester,
        agentName: _agentName,
        ident: 'beta-probe-round-1-$suffix',
        triggerFileName: betaProbeOne.uri.pathSegments.last,
        triggerFileSha256: await _fileSha256(betaProbeOne),
      );
      final betaDocResult = await _sendFileAndWait(
        tester,
        agentName: _agentName,
        fileName: betaDoc.uri.pathSegments.last,
        fileSha256: await _fileSha256(betaDoc),
      );
      if (_uploadStressBytes > 0) {
        // ignore: avoid_print
        print(
          'CCB_UPLOAD_STRESS_RESULT ${jsonEncode({'file_name': betaDoc.uri.pathSegments.last, 'size_bytes': betaDoc.lengthSync(), 'sha256': await _fileSha256(betaDoc), ...betaDocResult})}',
        );
      }
    },
  );

  testWidgets(
    'server-wide gateway dynamically backfills older chat on upward scroll',
    (tester) async {
      if (!_backfillEnabled) {
        return;
      }
      if (_backfillProjectId.trim().isEmpty ||
          _backfillLatestText.trim().isEmpty ||
          _backfillOldestText.trim().isEmpty) {
        throw TestFailure('backfill project id and markers are required');
      }

      final overall = Stopwatch()..start();
      app.main();

      await _openServerProject(
        tester,
        _backfillProjectId,
        _backfillProjectName,
      );
      await _selectAgent(tester, _backfillAgentName);
      final latestWatch = Stopwatch()..start();
      await _waitForConversationBody(
        tester,
        _backfillLatestText,
        timeout: const Duration(seconds: 60),
      );
      final latestVisibleMs = latestWatch.elapsedMilliseconds;

      final backfillWatch = Stopwatch()..start();
      final dragCount = await _dragTimelineUntilConversationBody(
        tester,
        _backfillOldestText,
        timeout: const Duration(seconds: 60),
      );
      final olderVisibleMs = backfillWatch.elapsedMilliseconds;
      // Keep a short settle window so the measurement includes the frame that
      // renders the prepended older page, not only the repository response.
      final settleWatch = Stopwatch()..start();
      await tester.pumpAndSettle(const Duration(milliseconds: 100));

      // ignore: avoid_print
      print(
        'CCB_BACKFILL_METRICS ${jsonEncode({'project_id': _backfillProjectId, 'agent': _backfillAgentName, 'latest_visible_ms': latestVisibleMs, 'older_visible_ms': olderVisibleMs, 'post_backfill_settle_ms': settleWatch.elapsedMilliseconds, 'total_ms': overall.elapsedMilliseconds, 'drag_count': dragCount})}',
      );
    },
  );
}

Future<File> _writeText(Directory dir, String fileName) async {
  final file = File('${dir.path}/$fileName');
  return file.writeAsString('CCB Mobile server-wide AVD fixture $fileName');
}

Future<File> _writeSizedText(
  Directory dir,
  String fileName,
  int sizeBytes,
) async {
  final file = File('${dir.path}/$fileName');
  final pattern = utf8.encode('CCB Mobile upload stress fixture $fileName\n');
  final chunk = List<int>.generate(
    64 * 1024,
    (index) => pattern[index % pattern.length],
    growable: false,
  );
  final sink = file.openWrite();
  var remaining = sizeBytes;
  while (remaining > 0) {
    final writeLength = remaining < chunk.length ? remaining : chunk.length;
    sink.add(
      writeLength == chunk.length ? chunk : chunk.sublist(0, writeLength),
    );
    remaining -= writeLength;
  }
  await sink.close();
  return file;
}

Future<File> _writePng(Directory dir, String fileName) async {
  final file = File('${dir.path}/$fileName');
  return file.writeAsBytes(_onePixelPngBytes);
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

Future<void> _sendTextFileAndDownload(
  WidgetTester tester, {
  required String agentName,
  required String ident,
  required String triggerFileName,
  required String triggerFileSha256,
}) async {
  await _selectAgent(tester, agentName);
  await _waitForComposerActionsEnabled(tester);
  await _tapVisible(tester, const ValueKey('agent-attachment-button'));
  await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
  await _waitForConversationBody(tester, triggerFileName);
  final body = 'pane-file-turn:$ident';
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    body,
  );
  await _waitForComposerText(
    tester,
    body,
    timeout: const Duration(seconds: 10),
  );
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(tester, body);
  await _waitForConversationBody(tester, triggerFileName);
  await _tapFinderVisible(tester, _downloadableAttachmentChip(triggerFileName));
  await _waitForText(
    tester,
    'Saved $triggerFileName',
    timeout: const Duration(seconds: 30),
  );
  await _assertDownloadedFileSha256(triggerFileName, triggerFileSha256);
  await _waitForTextGone(
    tester,
    'Saved $triggerFileName',
    timeout: const Duration(seconds: 8),
  );
  await _waitForComposerText(tester, '', timeout: const Duration(seconds: 30));
}

Future<Map<String, Object?>> _sendFileAndWait(
  WidgetTester tester, {
  required String agentName,
  required String fileName,
  required String fileSha256,
}) async {
  await _selectAgent(tester, agentName);
  await _waitForComposerActionsEnabled(tester);
  await _tapVisible(tester, const ValueKey('agent-attachment-button'));
  await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
  await _waitForConversationBody(tester, fileName);
  final sendToSave = Stopwatch()..start();
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(tester, fileName, timeout: _replyTimeout);
  final download = Stopwatch()..start();
  await _tapFinderVisible(tester, _downloadableAttachmentChip(fileName));
  await _waitForText(
    tester,
    'Saved $fileName',
    timeout: const Duration(seconds: 30),
  );
  final savedVisibleMs = download.elapsedMilliseconds;
  final hashDetails = await _assertDownloadedFileSha256(fileName, fileSha256);
  await _waitForTextGone(
    tester,
    'Saved $fileName',
    timeout: const Duration(seconds: 8),
  );
  return {
    'send_to_save_ms': sendToSave.elapsedMilliseconds,
    'download_saved_visible_ms': savedVisibleMs,
    'downloaded': hashDetails,
  };
}

Future<void> _sendImageAndWait(
  WidgetTester tester, {
  required String agentName,
  required String fileName,
  required String fileSha256,
}) async {
  await _selectAgent(tester, agentName);
  await _waitForComposerActionsEnabled(tester);
  await _tapVisible(tester, const ValueKey('agent-attachment-button'));
  await _tapVisible(tester, const ValueKey('agent-attachment-pick-image'));
  await _waitFor(
    tester,
    _imageDraftAttachmentPreview(),
    timeout: const Duration(seconds: 15),
  );
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(tester, fileName, timeout: _replyTimeout);
  await _tapFinderVisible(tester, _downloadableAttachmentChip(fileName));
  await _waitForText(
    tester,
    'Saved $fileName',
    timeout: const Duration(seconds: 30),
  );
  await _assertDownloadedFileSha256(fileName, fileSha256);
  await _waitForTextGone(
    tester,
    'Saved $fileName',
    timeout: const Duration(seconds: 8),
  );
}

Future<void> _downloadSeededNativeArtifactsIfPresent(
  WidgetTester tester, {
  required String agentName,
}) async {
  if (_nativeArtifactTextFileName.trim().isEmpty ||
      _nativeArtifactImageFileName.trim().isEmpty ||
      _nativeArtifactTextSha256.trim().isEmpty ||
      _nativeArtifactImageSha256.trim().isEmpty) {
    return;
  }
  await _selectAgent(tester, agentName);
  if (_nativeArtifactMarker.trim().isNotEmpty) {
    await _waitForConversationBody(
      tester,
      _nativeArtifactMarker,
      timeout: _replyTimeout,
    );
  }
  await _expandLatestReplyIfPresent(tester);
  await _waitForConversationBody(
    tester,
    _nativeArtifactTextFileName,
    timeout: _replyTimeout,
  );
  await _waitForConversationBody(
    tester,
    _nativeArtifactImageFileName,
    timeout: _replyTimeout,
  );
  await _tapFinderVisible(
    tester,
    _downloadableAttachmentChip(_nativeArtifactTextFileName),
  );
  await _waitForText(
    tester,
    'Saved $_nativeArtifactTextFileName',
    timeout: const Duration(seconds: 30),
  );
  await _assertDownloadedFileSha256(
    _nativeArtifactTextFileName,
    _nativeArtifactTextSha256,
  );
  await _waitForTextGone(
    tester,
    'Saved $_nativeArtifactTextFileName',
    timeout: const Duration(seconds: 8),
  );
  await _tapFinderVisible(
    tester,
    _downloadableAttachmentChip(_nativeArtifactImageFileName),
  );
  await _waitForText(
    tester,
    'Saved $_nativeArtifactImageFileName',
    timeout: const Duration(seconds: 30),
  );
  await _assertDownloadedFileSha256(
    _nativeArtifactImageFileName,
    _nativeArtifactImageSha256,
  );
  await _waitForTextGone(
    tester,
    'Saved $_nativeArtifactImageFileName',
    timeout: const Duration(seconds: 8),
  );
}

Future<void> _selectAgent(WidgetTester tester, String agentName) async {
  await _tapVisible(tester, ValueKey('agent-$agentName'));
  await _waitForAgentSelected(tester, agentName);
  await _waitFor(
    tester,
    find.byKey(const ValueKey('agent-message-composer')),
    timeout: const Duration(seconds: 30),
  );
}

Future<void> _waitForAgentSelected(
  WidgetTester tester,
  String agentName, {
  Duration timeout = const Duration(seconds: 15),
}) {
  return _waitFor(
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
    timeout: timeout,
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
  if (!tester.any(_textFieldWithControllerText(key, value))) {
    final textField = tester.widget<TextField>(find.byKey(key));
    final controller = textField.controller;
    if (controller != null) {
      controller.value = TextEditingValue(
        text: value,
        selection: TextSelection.collapsed(offset: value.length),
      );
      await tester.pumpAndSettle();
    }
  }
}

Finder _textFieldWithControllerText(Key key, String value) {
  return find.byWidgetPredicate((widget) {
    return widget is TextField &&
        widget.key == key &&
        widget.controller?.text == value;
  }, description: 'text field $key with controller text $value');
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

Future<void> _tapFinderVisible(WidgetTester tester, Finder finder) async {
  await _waitFor(tester, finder);
  final target = finder.first;
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Future<void> _tapLastFinderVisible(WidgetTester tester, Finder finder) async {
  await _waitFor(tester, finder);
  final target = finder.last;
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pumpAndSettle();
}

Future<void> _expandLatestReplyIfPresent(WidgetTester tester) async {
  final expand = _conversationExpandButton('reply-');
  if (!tester.any(expand)) {
    return;
  }
  await _tapLastFinderVisible(tester, expand);
}

Future<void> _waitForText(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 10),
  String Function()? diagnostics,
}) {
  return _waitFor(
    tester,
    find.text(text),
    timeout: timeout,
    diagnostics: diagnostics,
  );
}

Future<void> _waitForTextGone(
  WidgetTester tester,
  String text, {
  Duration timeout = const Duration(seconds: 10),
}) async {
  final finder = find.text(text);
  final stopwatch = Stopwatch()..start();
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 100));
    if (!tester.any(finder)) {
      return;
    }
  }
  throw TestFailure('Timed out waiting for text to disappear: $text');
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
    '$body: ${_chatDiagnostics(tester)}',
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

Future<String> _fileSha256(File file) async {
  return sha256.convert(await file.readAsBytes()).toString();
}

Future<Map<String, Object?>> _assertDownloadedFileSha256(
  String fileName,
  String expectedSha256,
) async {
  final dir = await getApplicationDocumentsDirectory();
  final file = File(p.join(dir.path, _safeFileName(fileName)));
  final bytes = await file.readAsBytes();
  final actualSha256 = sha256.convert(bytes).toString();
  final details = {
    'file_name': fileName,
    'path': file.path,
    'size_bytes': bytes.length,
    'sha256': actualSha256,
  };
  debugPrint('CCB_DOWNLOAD_SHA256 ${jsonEncode(details)}');
  expect(actualSha256, expectedSha256, reason: 'download hash for $fileName');
  return details;
}

String _safeFileName(String fileName) {
  final cleaned = fileName.replaceAll(RegExp(r'[\\/:*?"<>|]+'), '_').trim();
  return cleaned.isEmpty ? 'attachment' : cleaned;
}

Finder _downloadableAttachmentChip(String fileName) {
  return find.byWidgetPredicate((widget) {
    if (widget is! ActionChip || widget.onPressed == null) {
      return false;
    }
    return _plainText(widget.label).contains(fileName);
  }, description: 'downloadable attachment chip $fileName');
}

Finder _conversationExpandButton(String idPrefix) {
  return find.byWidgetPredicate((widget) {
    if (widget is! IconButton) {
      return false;
    }
    final key = widget.key;
    return key is ValueKey &&
        key.value.toString().startsWith('conversation-expand-$idPrefix');
  }, description: 'conversation expand button $idPrefix');
}

Finder _imageDraftAttachmentPreview() {
  return find.byWidgetPredicate((widget) {
    final key = widget.key;
    return key is ValueKey &&
        key.value.toString().startsWith('agent-attachment-image-preview-');
  }, description: 'draft image attachment preview');
}

String _plainText(Widget widget) {
  if (widget is Text) {
    return widget.data ?? widget.textSpan?.toPlainText() ?? '';
  }
  if (widget is RichText) {
    return widget.text.toPlainText();
  }
  if (widget is ProxyWidget) {
    return _plainText(widget.child);
  }
  if (widget is SingleChildRenderObjectWidget && widget.child != null) {
    return _plainText(widget.child!);
  }
  return '';
}

String _chatDiagnostics(WidgetTester tester) {
  final visibleTexts = find
      .byWidgetPredicate((widget) => widget is Text || widget is SelectableText)
      .evaluate()
      .take(30)
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

Future<void> _waitForComposerText(
  WidgetTester tester,
  String expected, {
  Duration timeout = const Duration(seconds: 10),
}) {
  return _waitFor(
    tester,
    find.byWidgetPredicate(
      (widget) => widget is TextField && widget.controller?.text == expected,
      description: 'composer text $expected',
    ),
    timeout: timeout,
  );
}

Future<void> _waitForComposerActionsEnabled(
  WidgetTester tester, {
  Duration timeout = const Duration(seconds: 30),
}) {
  return _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      final key = widget.key;
      return widget is IconButton &&
          key is ValueKey &&
          key.value == 'agent-attachment-button' &&
          widget.onPressed != null;
    }, description: 'enabled attachment action'),
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
