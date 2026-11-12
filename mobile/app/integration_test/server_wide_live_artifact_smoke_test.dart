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
  'CCB_MOBILE_LIVE_ARTIFACT_PROJECT_ID',
);
const _projectName = String.fromEnvironment(
  'CCB_MOBILE_LIVE_ARTIFACT_PROJECT_NAME',
  defaultValue: 'test_ccb2_alpha',
);
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_LIVE_ARTIFACT_AGENT',
  defaultValue: 'mobile_probe',
);
const _artifactFileName = String.fromEnvironment(
  'CCB_MOBILE_LIVE_ARTIFACT_FILE_NAME',
);
const _artifactContent = String.fromEnvironment(
  'CCB_MOBILE_LIVE_ARTIFACT_CONTENT',
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('live provider generates artifact and downloads it', (
    tester,
  ) async {
    if (_projectId.trim().isEmpty) {
      throw TestFailure('live artifact smoke project id is required');
    }
    if (_artifactFileName.trim().isEmpty || _artifactContent.trim().isEmpty) {
      throw TestFailure('live artifact smoke file metadata is required');
    }

    app.main();

    await _openServerProject(tester, _projectId, _projectName);
    await _selectAgent(tester, _agentName);
    await _waitForRefreshEnabled(tester);

    // The host-side harness waits for this marker, then writes the artifact
    // request directly to the real agent pane. The app must pick the generated
    // link up via explicit refresh and download it through the mobile gateway.
    // ignore: avoid_print
    print('CCB_LIVE_ARTIFACT_READY $_artifactFileName');
    await _refreshUntilDownloadableAttachment(
      tester,
      _artifactFileName,
      timeout: const Duration(seconds: 240),
    );
    expect(find.textContaining('CCB_REQ_ID'), findsNothing);
    expect(find.text('mobile_gateway'), findsNothing);
    expect(find.text('completion_snapshot'), findsNothing);

    await _deleteDownloadedFileIfExists(_artifactFileName);
    await _tapFinderVisibleWithoutSettle(
      tester,
      _downloadableAttachmentChip(_artifactFileName),
    );

    await _waitForText(
      tester,
      'Saved $_artifactFileName',
      timeout: const Duration(seconds: 60),
    );
    final downloaded = await _downloadedFileBytes(_artifactFileName);
    final expectedBytes = utf8.encode(_artifactContent);
    expect(downloaded, expectedBytes, reason: 'downloaded live artifact bytes');
    final actualSha256 = sha256.convert(downloaded).toString();
    final payload = {
      'file_name': _artifactFileName,
      'size_bytes': downloaded.length,
      'sha256': actualSha256,
      'expected_sha256': sha256.convert(expectedBytes).toString(),
    };
    // ignore: avoid_print
    print('CCB_DOWNLOAD_SHA256 ${jsonEncode(payload)}');
    // ignore: avoid_print
    print('CCB_LIVE_ARTIFACT_SMOKE_DONE ${jsonEncode(payload)}');
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

Future<void> _refreshUntilDownloadableAttachment(
  WidgetTester tester,
  String fileName, {
  Duration timeout = const Duration(seconds: 240),
}) async {
  final stopwatch = Stopwatch()..start();
  final chip = _downloadableAttachmentChip(fileName);
  while (stopwatch.elapsed < timeout) {
    await tester.pump(const Duration(milliseconds: 250));
    if (tester.any(chip)) {
      return;
    }
    await _waitForRefreshEnabled(
      tester,
      timeout: const Duration(seconds: 15),
    );
    await _tapVisible(tester, const ValueKey('agent-conversation-refresh-action'));
    for (var i = 0; i < 20; i += 1) {
      await tester.pump(const Duration(milliseconds: 250));
      if (tester.any(chip)) {
        return;
      }
    }
  }
  throw TestFailure(
    'Timed out waiting for downloadable attachment $fileName. '
    '${_chatDiagnostics(tester)}',
  );
}

Future<void> _waitForRefreshEnabled(
  WidgetTester tester, {
  Duration timeout = const Duration(seconds: 30),
}) {
  return _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      final key = widget.key;
      return widget is IconButton &&
          key is ValueKey &&
          key.value == 'agent-conversation-refresh-action' &&
          widget.onPressed != null;
    }, description: 'enabled refresh action'),
    timeout: timeout,
    diagnostics: () => _chatDiagnostics(tester),
  );
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

Finder _renderedTextContaining(String pattern, {String? description}) {
  return find.byWidgetPredicate((widget) {
    if (widget is Text) {
      return (widget.data ?? widget.textSpan?.toPlainText() ?? '').contains(
        pattern,
      );
    }
    if (widget is SelectableText) {
      return (widget.data ?? widget.textSpan?.toPlainText() ?? '').contains(
        pattern,
      );
    }
    if (widget is RichText) {
      return widget.text.toPlainText().contains(pattern);
    }
    return false;
  }, description: description ?? 'rendered text containing "$pattern"');
}

Finder _downloadableAttachmentChip(String fileName) {
  return find.byWidgetPredicate((widget) {
    if (widget is! ActionChip || widget.onPressed == null) {
      return false;
    }
    return _plainText(widget.label).contains(fileName);
  }, description: 'downloadable attachment chip $fileName');
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

Future<List<int>> _downloadedFileBytes(String fileName) async {
  final dir = await getApplicationDocumentsDirectory();
  final file = File(p.join(dir.path, _safeFileName(fileName)));
  return file.readAsBytes();
}

String _safeFileName(String fileName) {
  final cleaned = fileName.replaceAll(RegExp(r'[\\/:*?"<>|]+'), '_').trim();
  return cleaned.isEmpty ? 'attachment' : cleaned;
}

String _chatDiagnostics(WidgetTester tester) {
  final visibleTexts = find
      .byWidgetPredicate((widget) => widget is Text || widget is SelectableText)
      .evaluate()
      .take(80)
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
      .where((value) => value.trim().isNotEmpty)
      .join('\n');
  return visibleTexts;
}
