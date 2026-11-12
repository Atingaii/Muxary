import 'dart:convert';
import 'dart:io';

import 'package:crypto/crypto.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import 'package:ccb_mobile/main.dart' as app;

const _projectId = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_PROJECT_ID',
);
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_AGENT',
  defaultValue: 'mobile_probe',
);
const _backgroundSeconds = int.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_SECONDS',
  defaultValue: 10,
);
const _artifactMarker = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_ARTIFACT_MARKER',
);
const _artifactFileName = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_ARTIFACT_NAME',
);
const _artifactSha256 = String.fromEnvironment(
  'CCB_MOBILE_BACKGROUND_FILE_ARTIFACT_SHA256',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('artifact download survives Android background and resume', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('background file smoke project id is required');
    }
    if (_artifactFileName.trim().isEmpty || _artifactSha256.trim().isEmpty) {
      throw TestFailure('background file smoke artifact metadata is required');
    }
    if (_backgroundSeconds < 3) {
      throw TestFailure('background file smoke needs at least 3 seconds');
    }

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    if (_artifactMarker.trim().isNotEmpty) {
      await _waitForConversationBody(
        tester,
        _artifactMarker,
        timeout: const Duration(seconds: 120),
      );
    }
    await _expandLatestReplyIfPresent(tester);
    await _waitForConversationBody(
      tester,
      _artifactFileName,
      timeout: const Duration(seconds: 120),
    );
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    await _deleteDownloadedFileIfExists(_artifactFileName);
    await _tapFinderVisibleWithoutSettle(
      tester,
      _downloadableAttachmentChip(_artifactFileName),
    );

    // Host-side runner sends HOME and relaunches MainActivity when it sees
    // this marker. The download has already been requested, so the app has to
    // finish or surface the saved state across a real Android lifecycle hop.
    // ignore: avoid_print
    print('CCB_BACKGROUND_FILE_DOWNLOAD_READY $_artifactFileName');
    await Future<void>.delayed(Duration(seconds: _backgroundSeconds + 3));
    await tester.pumpAndSettle();

    expect(
      find.byKey(const ValueKey('selected-agent-workspace')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('agent-message-composer')),
      findsOneWidget,
    );
    await _waitForText(
      tester,
      'Saved $_artifactFileName',
      timeout: const Duration(seconds: 60),
    );
    await _assertDownloadedFileSha256(_artifactFileName, _artifactSha256);
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    // ignore: avoid_print
    print('CCB_BACKGROUND_FILE_DOWNLOAD_DONE $_artifactFileName');
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

Future<void> _tapFinderVisibleWithoutSettle(
  WidgetTester tester,
  Finder finder,
) async {
  await _waitFor(tester, finder, diagnostics: () => _chatDiagnostics(tester));
  final target = finder.first;
  await tester.ensureVisible(target);
  await tester.pumpAndSettle();
  await tester.tap(target);
  await tester.pump(const Duration(milliseconds: 50));
}

Future<void> _tapLastFinderVisible(WidgetTester tester, Finder finder) async {
  await _waitFor(tester, finder, diagnostics: () => _chatDiagnostics(tester));
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
}) {
  return _waitFor(
    tester,
    find.text(text),
    timeout: timeout,
    diagnostics: () => _chatDiagnostics(tester),
  );
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

Future<void> _deleteDownloadedFileIfExists(String fileName) async {
  final dir = await getApplicationDocumentsDirectory();
  final file = File(p.join(dir.path, _safeFileName(fileName)));
  if (await file.exists()) {
    await file.delete();
  }
}

Future<void> _assertDownloadedFileSha256(
  String fileName,
  String expectedSha256,
) async {
  final dir = await getApplicationDocumentsDirectory();
  final file = File(p.join(dir.path, _safeFileName(fileName)));
  final bytes = await file.readAsBytes();
  final actualSha256 = sha256.convert(bytes).toString();
  debugPrint(
    'CCB_DOWNLOAD_SHA256 ${jsonEncode({'file_name': fileName, 'path': file.path, 'size_bytes': bytes.length, 'sha256': actualSha256})}',
  );
  expect(actualSha256, expectedSha256, reason: 'download hash for $fileName');
}

String _safeFileName(String fileName) {
  final cleaned = fileName.replaceAll(RegExp(r'[\\/:*?"<>|]+'), '_').trim();
  return cleaned.isEmpty ? 'attachment' : cleaned;
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
