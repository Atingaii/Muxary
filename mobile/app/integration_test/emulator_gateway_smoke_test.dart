import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:file_picker/src/platform/file_picker_platform_interface.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:ccb_mobile/main.dart' as app;

const _gatewayUrl = String.fromEnvironment(
  'CCB_MOBILE_GATEWAY_URL',
  defaultValue: 'http://127.0.0.1:8787',
);
const _pairingCode = String.fromEnvironment('CCB_MOBILE_PAIRING_CODE');
const _agentName = String.fromEnvironment(
  'CCB_MOBILE_AGENT',
  defaultValue: 'mobile_probe',
);
const _secondaryAgentName = String.fromEnvironment(
  'CCB_MOBILE_SECONDARY_AGENT',
  defaultValue: 'mobile_peer',
);
const _realBackendReplyTimeout = Duration(seconds: 90);
const _requireGateway = bool.fromEnvironment(
  'CCB_MOBILE_REQUIRE_GATEWAY',
  defaultValue: false,
);
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
  78,
  68,
  174,
  66,
  96,
  130,
];
const _includeLifecycleStop = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_LIFECYCLE_STOP',
  defaultValue: false,
);
const _includeTerminalRoute = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_TERMINAL_ROUTE',
  defaultValue: true,
);
const _includeAttachmentRoute = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_ATTACHMENT_ROUTE',
  defaultValue: false,
);
const _includeImageRoute = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_IMAGE_ROUTE',
  defaultValue: false,
);
const _includeMarkdownRoute = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_MARKDOWN_ROUTE',
  defaultValue: false,
);
const _includeBackendArtifactRoute = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_BACKEND_ARTIFACT_ROUTE',
  defaultValue: false,
);
const _includeMultiAgentRoute = bool.fromEnvironment(
  'CCB_MOBILE_INCLUDE_MULTI_AGENT_ROUTE',
  defaultValue: false,
);

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('emulator UI smoke covers selected-agent route diagnostics', (
    tester,
  ) async {
    app.main();

    await _openCurrentProject(tester);
    expect(
      find.byKey(const ValueKey('selected-agent-workspace')),
      findsOneWidget,
    );
    expect(
      find.byKey(const ValueKey('connection-details-action')),
      findsWidgets,
    );

    await _switchFakeAgentWithoutOpeningTerminal(tester);
    await _selectFakeMobileAgent(tester);
    await _assertDefaultSelectedAgentReader(tester);
    await _assertFakeLifecycleControls(tester);

    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    await _claimLoopbackGateway(tester);
    await _assertPairedGatewayRoute(tester);
    await _assertPairedLifecycleControls(
      tester,
      includeStop: _includeLifecycleStop,
    );
    if (!_includeLifecycleStop) {
      await _assertPairedAgentChat(tester);
    }
  });

  testWidgets('emulator UI smoke opens selected-agent gateway terminal', (
    tester,
  ) async {
    if (_includeLifecycleStop || !_includeTerminalRoute) {
      return;
    }
    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    app.main();
    await _openCurrentProject(tester);
    await _activateStoredGatewayProfile(tester);
    await _openSelectedAgentGatewayTerminal(tester);
  });

  testWidgets('emulator UI smoke uploads and downloads gateway attachment', (
    tester,
  ) async {
    if (_includeLifecycleStop || !_includeAttachmentRoute) {
      return;
    }
    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-avd-attachment-',
    );
    final suffix = DateTime.now().millisecondsSinceEpoch;
    final fileName = 'ccb-avd-doc-$suffix.txt';
    final file = File('${tempDir.path}/$fileName');
    await file.writeAsString('CCB Mobile AVD attachment $suffix');
    FilePickerPlatform.instance = _FakeFilePicker([
      FilePickerResult([
        PlatformFile(name: fileName, path: file.path, size: file.lengthSync()),
      ]),
    ]);
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();
    await _openCurrentProject(tester);
    await _activateStoredGatewayProfile(tester);
    await _selectAgent(tester, _agentName);

    await _tapVisible(tester, const ValueKey('agent-attachment-button'));
    await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
    await _waitFor(
      tester,
      _renderedTextContaining(fileName, description: 'draft attachment'),
      timeout: const Duration(seconds: 15),
    );
    await _tapVisible(tester, const ValueKey('agent-message-send-button'));

    await _waitForConversationBody(
      tester,
      fileName,
      timeout: _realBackendReplyTimeout,
    );
    await _waitForConversationBody(
      tester,
      'FAKE[$_agentName] Uploaded attachment: $fileName',
      timeout: _realBackendReplyTimeout,
    );
    await _tapFinderVisible(tester, _downloadableAttachmentChip(fileName));
    await _waitForText(
      tester,
      'Saved $fileName',
      timeout: const Duration(seconds: 30),
    );
  });

  testWidgets('emulator UI smoke uploads and downloads gateway image', (
    tester,
  ) async {
    if (_includeLifecycleStop || !_includeImageRoute) {
      return;
    }
    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-avd-image-',
    );
    final suffix = DateTime.now().millisecondsSinceEpoch;
    final fileName = 'ccb-avd-image-$suffix.png';
    final file = File('${tempDir.path}/$fileName');
    await file.writeAsBytes(_onePixelPngBytes);
    FilePickerPlatform.instance = _FakeFilePicker([
      FilePickerResult([
        PlatformFile(name: fileName, path: file.path, size: file.lengthSync()),
      ]),
    ]);
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();
    await _openCurrentProject(tester);
    await _activateStoredGatewayProfile(tester);
    await _selectAgent(tester, _agentName);

    await _tapVisible(tester, const ValueKey('agent-attachment-button'));
    await _tapVisible(tester, const ValueKey('agent-attachment-pick-image'));
    await _waitFor(
      tester,
      _imageDraftAttachmentPreview(),
      timeout: const Duration(seconds: 15),
    );
    await _tapVisible(tester, const ValueKey('agent-message-send-button'));

    await _waitForConversationBody(
      tester,
      fileName,
      timeout: _realBackendReplyTimeout,
    );
    await _waitForConversationBody(
      tester,
      'FAKE[$_agentName] Uploaded attachment: $fileName',
      timeout: _realBackendReplyTimeout,
    );
    await _tapFinderVisible(tester, _downloadableAttachmentChip(fileName));
    await _waitForText(
      tester,
      'Saved $fileName',
      timeout: const Duration(seconds: 30),
    );
  });

  testWidgets('emulator UI smoke renders deterministic local markdown reply', (
    tester,
  ) async {
    if (_includeLifecycleStop || !_includeMarkdownRoute) {
      return;
    }
    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-avd-markdown-',
    );
    final suffix = DateTime.now().millisecondsSinceEpoch;
    final fileName = 'ccb-avd-md-$suffix.txt';
    final file = File('${tempDir.path}/$fileName');
    await file.writeAsString('CCB Mobile AVD markdown fixture $suffix');
    FilePickerPlatform.instance = _FakeFilePicker([
      FilePickerResult([
        PlatformFile(name: fileName, path: file.path, size: file.lengthSync()),
      ]),
    ]);
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();
    await _openCurrentProject(tester);
    await _activateStoredGatewayProfile(tester);
    await _selectAgent(tester, _agentName);

    await _enterTextVisible(
      tester,
      const ValueKey('agent-message-composer'),
      'ccb-local-md:$suffix',
    );
    await _tapVisible(tester, const ValueKey('agent-attachment-button'));
    await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
    await _waitFor(
      tester,
      _renderedTextContaining(
        fileName,
        description: 'markdown draft attachment',
      ),
      timeout: const Duration(seconds: 15),
    );
    await _tapVisible(tester, const ValueKey('agent-message-send-button'));

    await _waitForConversationBody(
      tester,
      'CCB Local Markdown $suffix',
      timeout: _realBackendReplyTimeout,
    );
    await _waitForConversationBody(
      tester,
      'ccb-local-reply:$suffix',
      timeout: _realBackendReplyTimeout,
    );
    await _waitForConversationBody(
      tester,
      'rendered list item from the real local backend',
      timeout: _realBackendReplyTimeout,
    );
    await _tapLastFinderVisible(tester, _conversationExpandButton('reply-'));
    await _waitForConversationBody(
      tester,
      'agent=$_agentName',
      timeout: _realBackendReplyTimeout,
    );
    await _waitForConversationBody(
      tester,
      'blocked local link',
      timeout: _realBackendReplyTimeout,
    );
  });

  testWidgets('emulator UI smoke downloads backend generated artifacts', (
    tester,
  ) async {
    if (_includeLifecycleStop || !_includeBackendArtifactRoute) {
      return;
    }
    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    final suffix = DateTime.now().millisecondsSinceEpoch;
    final triggerFileName = 'ccb-avd-artifact-trigger-$suffix.txt';
    final textArtifact = 'artifact-$suffix.txt';
    final imageArtifact = 'image-$suffix.png';
    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-avd-artifact-',
    );
    final triggerFile = File('${tempDir.path}/$triggerFileName');
    await triggerFile.writeAsString('CCB Mobile AVD artifact trigger $suffix');
    FilePickerPlatform.instance = _FakeFilePicker([
      FilePickerResult([
        PlatformFile(
          name: triggerFileName,
          path: triggerFile.path,
          size: triggerFile.lengthSync(),
        ),
      ]),
    ]);
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();
    await _openCurrentProject(tester);
    await _activateStoredGatewayProfile(tester);
    await _selectAgent(tester, _agentName);

    await _enterTextVisible(
      tester,
      const ValueKey('agent-message-composer'),
      'ccb-local-artifact:$suffix',
    );
    await _tapVisible(tester, const ValueKey('agent-attachment-button'));
    await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
    await _waitFor(
      tester,
      _renderedTextContaining(
        triggerFileName,
        description: 'artifact trigger draft attachment',
      ),
      timeout: const Duration(seconds: 15),
    );
    await _tapVisible(tester, const ValueKey('agent-message-send-button'));

    await _waitForConversationBody(
      tester,
      'CCB Local Artifacts $suffix',
      timeout: _realBackendReplyTimeout,
    );
    await _expandLatestReplyIfPresent(tester);
    await _waitForConversationBody(
      tester,
      textArtifact,
      timeout: _realBackendReplyTimeout,
    );
    await _waitForConversationBody(
      tester,
      imageArtifact,
      timeout: _realBackendReplyTimeout,
    );

    await _tapFinderVisible(tester, _artifactMarkdownLink(textArtifact));
    await _waitForText(
      tester,
      'Saved $textArtifact',
      timeout: const Duration(seconds: 30),
    );

    await _tapFinderVisible(tester, _artifactMarkdownLink(imageArtifact));
    await _waitForText(
      tester,
      'Saved $imageArtifact',
      timeout: const Duration(seconds: 30),
    );
  });

  testWidgets('emulator UI smoke covers multi-agent images and turns', (
    tester,
  ) async {
    if (_includeLifecycleStop || !_includeMultiAgentRoute) {
      return;
    }
    if (_pairingCode.trim().isEmpty) {
      if (_requireGateway) {
        throw TestFailure('CCB_MOBILE_PAIRING_CODE is required');
      }
      return;
    }

    final suffix = DateTime.now().millisecondsSinceEpoch;
    final probeIdentPrefix = _safeMarkdownIdentifierPart(_agentName);
    final peerIdentPrefix = _safeMarkdownIdentifierPart(_secondaryAgentName);
    final probeTurnOneName = 'ccb-avd-$_agentName-turn-1-$suffix.txt';
    final probeTurnTwoName = 'ccb-avd-$_agentName-turn-2-$suffix.txt';
    final peerTurnOneName = 'ccb-avd-$_secondaryAgentName-turn-1-$suffix.txt';
    final peerTurnTwoName = 'ccb-avd-$_secondaryAgentName-turn-2-$suffix.txt';
    final probeImageName = 'ccb-avd-$_agentName-image-$suffix.png';
    final peerImageName = 'ccb-avd-$_secondaryAgentName-image-$suffix.png';
    final probeTriggerName = 'ccb-avd-$_agentName-artifact-$suffix.txt';
    final peerTriggerName = 'ccb-avd-$_secondaryAgentName-artifact-$suffix.txt';
    final originalPicker = FilePickerPlatform.instance;
    final tempDir = await Directory.systemTemp.createTemp(
      'ccb-mobile-avd-multi-agent-',
    );
    final probeTurnOne = File('${tempDir.path}/$probeTurnOneName');
    final probeTurnTwo = File('${tempDir.path}/$probeTurnTwoName');
    final peerTurnOne = File('${tempDir.path}/$peerTurnOneName');
    final peerTurnTwo = File('${tempDir.path}/$peerTurnTwoName');
    final probeImage = File('${tempDir.path}/$probeImageName');
    final peerImage = File('${tempDir.path}/$peerImageName');
    final probeTrigger = File('${tempDir.path}/$probeTriggerName');
    final peerTrigger = File('${tempDir.path}/$peerTriggerName');
    await probeTurnOne.writeAsString('probe turn one $suffix');
    await probeTurnTwo.writeAsString('probe turn two $suffix');
    await peerTurnOne.writeAsString('peer turn one $suffix');
    await peerTurnTwo.writeAsString('peer turn two $suffix');
    await probeImage.writeAsBytes(_onePixelPngBytes);
    await peerImage.writeAsBytes(_onePixelPngBytes);
    await probeTrigger.writeAsString('probe artifact trigger $suffix');
    await peerTrigger.writeAsString('peer artifact trigger $suffix');
    FilePickerPlatform.instance = _FakeFilePicker([
      FilePickerResult([
        PlatformFile(
          name: probeTurnOneName,
          path: probeTurnOne.path,
          size: probeTurnOne.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: probeTurnTwoName,
          path: probeTurnTwo.path,
          size: probeTurnTwo.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: peerTurnOneName,
          path: peerTurnOne.path,
          size: peerTurnOne.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: peerTurnTwoName,
          path: peerTurnTwo.path,
          size: peerTurnTwo.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: probeImageName,
          path: probeImage.path,
          size: probeImage.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: peerImageName,
          path: peerImage.path,
          size: peerImage.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: probeTriggerName,
          path: probeTrigger.path,
          size: probeTrigger.lengthSync(),
        ),
      ]),
      FilePickerResult([
        PlatformFile(
          name: peerTriggerName,
          path: peerTrigger.path,
          size: peerTrigger.lengthSync(),
        ),
      ]),
    ]);
    addTearDown(() async {
      FilePickerPlatform.instance = originalPicker;
      if (await tempDir.exists()) {
        await tempDir.delete(recursive: true);
      }
    });

    app.main();
    await _openCurrentProject(tester);
    await _activateStoredGatewayProfile(tester);

    final probeDraft = '$_agentName draft $suffix';
    final peerDraft = '$_secondaryAgentName draft $suffix';
    await _selectAgent(tester, _agentName);
    await _enterTextVisible(
      tester,
      const ValueKey('agent-message-composer'),
      probeDraft,
    );
    await _selectAgent(tester, _secondaryAgentName);
    await _enterTextVisible(
      tester,
      const ValueKey('agent-message-composer'),
      peerDraft,
    );
    await _selectAgent(tester, _agentName);
    _expectComposerText(tester, probeDraft);
    await _selectAgent(tester, _secondaryAgentName);
    _expectComposerText(tester, peerDraft);

    await _sendMarkdownTurnAndWait(
      tester,
      agentName: _agentName,
      ident: '$probeIdentPrefix-round-1-$suffix',
      triggerFileName: probeTurnOneName,
    );
    await _sendMarkdownTurnAndWait(
      tester,
      agentName: _agentName,
      ident: '$probeIdentPrefix-round-2-$suffix',
      triggerFileName: probeTurnTwoName,
    );

    await _sendMarkdownTurnAndWait(
      tester,
      agentName: _secondaryAgentName,
      ident: '$peerIdentPrefix-round-1-$suffix',
      triggerFileName: peerTurnOneName,
    );
    await _sendMarkdownTurnAndWait(
      tester,
      agentName: _secondaryAgentName,
      ident: '$peerIdentPrefix-round-2-$suffix',
      triggerFileName: peerTurnTwoName,
    );

    await _selectAgent(tester, _agentName);
    await _waitForConversationBody(
      tester,
      'CCB Local Markdown $probeIdentPrefix-round-1-$suffix',
    );
    await _waitForConversationBody(
      tester,
      'CCB Local Markdown $probeIdentPrefix-round-2-$suffix',
    );
    await _sendImageAndWait(
      tester,
      agentName: _agentName,
      fileName: probeImageName,
    );

    await _selectAgent(tester, _secondaryAgentName);
    await _waitForConversationBody(
      tester,
      'CCB Local Markdown $peerIdentPrefix-round-1-$suffix',
    );
    await _waitForConversationBody(
      tester,
      'CCB Local Markdown $peerIdentPrefix-round-2-$suffix',
    );
    await _sendImageAndWait(
      tester,
      agentName: _secondaryAgentName,
      fileName: peerImageName,
    );

    await _sendBackendArtifactAndWait(
      tester,
      agentName: _agentName,
      ident: '$probeIdentPrefix-$suffix',
      triggerFileName: probeTriggerName,
    );
    await _sendBackendArtifactAndWait(
      tester,
      agentName: _secondaryAgentName,
      ident: '$peerIdentPrefix-$suffix',
      triggerFileName: peerTriggerName,
    );
  });
}

Future<void> _openCurrentProject(WidgetTester tester) async {
  await _waitFor(
    tester,
    find.byKey(const ValueKey('project-list')),
    timeout: const Duration(seconds: 30),
  );
  if (tester.any(find.byKey(const ValueKey('selected-agent-workspace')))) {
    return;
  }
  if (tester.any(find.byKey(const ValueKey('project-open-current')))) {
    await _tapVisible(tester, const ValueKey('project-open-current'));
  } else {
    await _tapFinderVisible(tester, _serverProjectOpenActions().first);
  }
  await _waitFor(
    tester,
    find.byKey(const ValueKey('selected-agent-workspace')),
    timeout: const Duration(seconds: 30),
  );
}

Finder _serverProjectOpenActions() {
  return find.byWidgetPredicate((widget) {
    final key = widget.key;
    if (key is! ValueKey<String>) {
      return false;
    }
    return key.value.startsWith('project-open-') &&
        key.value != 'project-open-current';
  }, description: 'server project open action');
}

Future<void> _assertPairedLifecycleControls(
  WidgetTester tester, {
  required bool includeStop,
}) async {
  if (!tester.any(find.byKey(const ValueKey('connection-details-panel')))) {
    await _tapVisible(tester, const ValueKey('connection-details-action'));
  }
  await _expandPanel(
    tester,
    const ValueKey('project-lifecycle-panel'),
    childKey: const ValueKey('lifecycle-wake-button'),
  );

  await _tapVisible(tester, const ValueKey('lifecycle-wake-button'));
  await _waitForText(
    tester,
    'Lifecycle wake: already_running',
    timeout: const Duration(seconds: 30),
  );
  await _waitForLifecycleDetail(
    tester,
    'running / already_running / ccb / no raw tmux',
  );

  await _tapVisible(tester, const ValueKey('lifecycle-open-button'));
  await _waitForText(
    tester,
    'Lifecycle open: opened',
    timeout: const Duration(seconds: 30),
  );
  await _waitForLifecycleDetail(tester, 'running / opened / ccb / no raw tmux');

  await _tapVisible(tester, const ValueKey('lifecycle-close-button'));
  await _waitForText(
    tester,
    'Lifecycle close: mobile_view_closed',
    timeout: const Duration(seconds: 30),
  );
  await _waitForLifecycleDetail(
    tester,
    'running / mobile_view_closed / ccb / no raw tmux',
  );

  if (includeStop) {
    await _tapVisible(tester, const ValueKey('lifecycle-stop-button'));
    await _waitForText(tester, 'Stop project');
    await _tapVisible(tester, const ValueKey('confirm-lifecycle-stop-button'));
    await _waitForText(
      tester,
      'Lifecycle stop: ccbd_stop_requested',
      timeout: const Duration(seconds: 30),
    );
    await _waitForLifecycleDetail(
      tester,
      'stopping / ccbd_stop_requested / ccb / no raw tmux',
    );
    return;
  }

  await _dismissCurrentRoute(
    tester,
    goneKey: const ValueKey('connection-details-panel'),
  );
}

Future<void> _waitForLifecycleDetail(
  WidgetTester tester,
  String expected,
) async {
  final finder = find.byKey(
    const ValueKey('project-lifecycle-detail'),
    skipOffstage: false,
  );
  await _waitFor(tester, finder, timeout: const Duration(seconds: 30));
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  final detail = tester.widget<Text>(finder.first);
  expect(detail.data, expected);
}

Future<void> _assertFakeLifecycleControls(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('connection-details-action'));
  await _expandPanel(
    tester,
    const ValueKey('project-lifecycle-panel'),
    childKey: const ValueKey('lifecycle-open-button'),
  );
  await _tapVisible(tester, const ValueKey('lifecycle-open-button'));
  await _waitForText(tester, 'Lifecycle open: opened');

  await _tapVisible(tester, const ValueKey('lifecycle-stop-button'));
  await _waitForText(tester, 'Stop project');
  await _tapVisible(tester, const ValueKey('confirm-lifecycle-stop-button'));
  await _waitForText(tester, 'Lifecycle stop: ccbd_stop_requested');
  await _dismissCurrentRoute(
    tester,
    goneKey: const ValueKey('connection-details-panel'),
  );
}

Future<void> _assertDefaultSelectedAgentReader(WidgetTester tester) async {
  final contentToggle = find.byKey(
    const ValueKey('conversation-expand-reply-content-mobile-emulator'),
  );
  if (tester.any(contentToggle)) {
    await _tapVisible(
      tester,
      const ValueKey('conversation-expand-reply-content-mobile-emulator'),
    );
    await _waitFor(
      tester,
      find.byKey(const ValueKey('structured-content-reader')),
    );
    expect(
      find.byKey(const ValueKey('markdown-body-content-mobile-emulator')),
      findsOneWidget,
    );
    expect(find.text('Emulator landing status'), findsWidgets);
  }

  final historyToggle = find.byKey(
    const ValueKey('conversation-expand-terminal-history-mobile'),
  );
  if (!tester.any(historyToggle)) {
    expect(
      find.byKey(const ValueKey('selected-agent-workspace')),
      findsOneWidget,
    );
    expect(find.byKey(const ValueKey('ccb-live-terminal-view')), findsNothing);
    expect(find.byKey(const ValueKey('ccb-terminal-view')), findsNothing);
    return;
  }

  await _tapVisible(
    tester,
    const ValueKey('conversation-expand-terminal-history-mobile'),
  );
  expect(
    find.byKey(const ValueKey('readable-terminal-history')),
    findsOneWidget,
  );

  final historyScroll = find.byKey(
    const ValueKey('readable-terminal-history-scroll'),
  );
  expect(historyScroll, findsOneWidget);
  expect(find.text('Checkpoint 09'), findsNothing);

  await tester.ensureVisible(historyScroll);
  await tester.pumpAndSettle();
  await tester.drag(historyScroll, const Offset(0, -900));
  await tester.pumpAndSettle();

  expect(find.text('Checkpoint 09'), findsOneWidget);
  expect(
    find.text('Long retained scrollback stays reachable by drag.'),
    findsOneWidget,
  );
}

Future<void> _switchFakeAgentWithoutOpeningTerminal(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('agent-lead'));
  await _waitForAgentSelected(tester, 'lead');
  expect(find.byKey(const ValueKey('ccb-live-terminal-view')), findsNothing);
  expect(find.byKey(const ValueKey('ccb-terminal-view')), findsNothing);
}

Future<void> _selectFakeMobileAgent(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('agent-mobile'));
  await _waitForAgentSelected(tester, 'mobile');
}

Future<void> _claimLoopbackGateway(WidgetTester tester) async {
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
    _pairingCode,
  );
  await _enterTextVisible(
    tester,
    const ValueKey('pairing-device-name-field'),
    'Android Emulator UI Smoke',
  );
  await _tapVisible(tester, const ValueKey('gateway-pairing-claim-button'));

  await _waitForText(
    tester,
    'Gateway paired',
    timeout: const Duration(seconds: 30),
  );
  await _dismissCurrentRoute(
    tester,
    goneKey: const ValueKey('connection-details-panel'),
  );
  await _openCurrentProject(tester);
  await _waitForAgentSelected(tester, _agentName);
}

Future<void> _assertPairedGatewayRoute(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('connection-details-action'));
  await _expandPanel(
    tester,
    const ValueKey('runtime-mode-panel'),
    childKey: const ValueKey('gateway-route-check-button'),
  );
  await _tapVisible(tester, const ValueKey('gateway-route-check-button'));
  await _waitForText(
    tester,
    'Route ready',
    timeout: const Duration(seconds: 30),
  );
  expect(
    find.byKey(const ValueKey('gateway-route-diagnostics-status')),
    findsOneWidget,
  );
}

Future<void> _assertPairedAgentChat(WidgetTester tester) async {
  await _selectAgent(tester, _agentName);
  await _waitForAgentSelected(tester, _agentName);
  expect(find.byKey(const ValueKey('ccb-live-terminal-view')), findsNothing);
  expect(find.byKey(const ValueKey('ccb-terminal-view')), findsNothing);

  const primaryDraft = 'primary draft survives agent switch';
  const secondaryDraft = 'secondary draft survives agent switch';
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    primaryDraft,
  );
  await _selectAgent(tester, _secondaryAgentName);
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    secondaryDraft,
  );
  await _selectAgent(tester, _agentName);
  _expectComposerText(tester, primaryDraft);
  await _selectAgent(tester, _secondaryAgentName);
  _expectComposerText(tester, secondaryDraft);
  await _selectAgent(tester, _agentName);

  final suffix = DateTime.now().millisecondsSinceEpoch;
  final firstBody = 'ccb-mobile-chat-c5-first-$suffix';
  final secondBody = 'ccb-mobile-chat-c5-second-$suffix';
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    firstBody,
  );
  FocusManager.instance.primaryFocus?.unfocus();
  await tester.pumpAndSettle();
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(
    tester,
    firstBody,
    timeout: const Duration(seconds: 30),
  );
  await _waitForComposerText(tester, '', timeout: const Duration(seconds: 30));

  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    secondBody,
  );
  FocusManager.instance.primaryFocus?.unfocus();
  await tester.pumpAndSettle();
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(
    tester,
    firstBody,
    timeout: const Duration(seconds: 30),
  );
  await _waitForConversationBody(
    tester,
    secondBody,
    timeout: const Duration(seconds: 30),
  );
  await _waitForComposerText(tester, '', timeout: const Duration(seconds: 30));
  expect(find.byKey(const ValueKey('ccb-live-terminal-view')), findsNothing);
  expect(find.byKey(const ValueKey('ccb-terminal-view')), findsNothing);
}

Future<void> _sendMarkdownTurnAndWait(
  WidgetTester tester, {
  required String agentName,
  required String ident,
  required String triggerFileName,
}) async {
  await _selectAgent(tester, agentName);
  await _waitForComposerActionsEnabled(tester);
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    'ccb-local-md:$ident',
  );
  await _tapVisible(tester, const ValueKey('agent-attachment-button'));
  await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
  await _waitFor(
    tester,
    _renderedTextContaining(
      triggerFileName,
      description: 'multi-agent markdown trigger attachment',
    ),
    timeout: const Duration(seconds: 15),
  );
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));
  await _waitForConversationBody(
    tester,
    'CCB Local Markdown $ident',
    timeout: _realBackendReplyTimeout,
  );
  await _waitForConversationBody(
    tester,
    'ccb-local-reply:$ident',
    timeout: _realBackendReplyTimeout,
  );
  await _expandLatestReplyIfPresent(tester);
  await _waitForConversationBody(
    tester,
    'agent=$agentName',
    timeout: _realBackendReplyTimeout,
  );
  await _waitForComposerText(tester, '', timeout: const Duration(seconds: 30));
  await _waitForComposerActionsEnabled(tester);
}

Future<void> _sendImageAndWait(
  WidgetTester tester, {
  required String agentName,
  required String fileName,
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
  await _waitForConversationBody(
    tester,
    fileName,
    timeout: _realBackendReplyTimeout,
  );
  await _waitForConversationBody(
    tester,
    'FAKE[$agentName] Uploaded attachment: $fileName',
    timeout: _realBackendReplyTimeout,
  );
  await _waitForComposerText(tester, '', timeout: const Duration(seconds: 30));
  await _waitForComposerActionsEnabled(tester);
  await _tapFinderVisible(tester, _downloadableAttachmentChip(fileName));
  await _waitForText(
    tester,
    'Saved $fileName',
    timeout: const Duration(seconds: 30),
  );
  await _waitForTextGone(
    tester,
    'Saved $fileName',
    timeout: const Duration(seconds: 8),
  );
  await _waitForComposerActionsEnabled(tester);
}

Future<void> _sendBackendArtifactAndWait(
  WidgetTester tester, {
  required String agentName,
  required String ident,
  required String triggerFileName,
}) async {
  await _selectAgent(tester, agentName);
  await _waitForComposerActionsEnabled(tester);
  await _enterTextVisible(
    tester,
    const ValueKey('agent-message-composer'),
    'ccb-local-artifact:$ident',
  );
  await _tapVisible(tester, const ValueKey('agent-attachment-button'));
  await _tapVisible(tester, const ValueKey('agent-attachment-pick-file'));
  await _waitFor(
    tester,
    _renderedTextContaining(
      triggerFileName,
      description: 'multi-agent artifact trigger attachment',
    ),
    timeout: const Duration(seconds: 15),
  );
  await _tapVisible(tester, const ValueKey('agent-message-send-button'));

  final textArtifact = 'artifact-$ident.txt';
  final imageArtifact = 'image-$ident.png';
  await _waitForConversationBody(
    tester,
    'CCB Local Artifacts $ident',
    timeout: _realBackendReplyTimeout,
  );
  await _expandLatestReplyIfPresent(tester);
  await _waitForConversationBody(
    tester,
    textArtifact,
    timeout: _realBackendReplyTimeout,
  );
  await _waitForConversationBody(
    tester,
    imageArtifact,
    timeout: _realBackendReplyTimeout,
  );
  await _waitForComposerText(tester, '', timeout: const Duration(seconds: 30));
  await _waitForComposerActionsEnabled(tester);
  await _tapFinderVisible(tester, _artifactMarkdownLink(textArtifact));
  await _waitForText(
    tester,
    'Saved $textArtifact',
    timeout: const Duration(seconds: 30),
  );
  await _waitForTextGone(
    tester,
    'Saved $textArtifact',
    timeout: const Duration(seconds: 8),
  );
  await _tapFinderVisible(tester, _artifactMarkdownLink(imageArtifact));
  await _waitForText(
    tester,
    'Saved $imageArtifact',
    timeout: const Duration(seconds: 30),
  );
  await _waitForTextGone(
    tester,
    'Saved $imageArtifact',
    timeout: const Duration(seconds: 8),
  );
  await _waitForComposerActionsEnabled(tester);
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
  Duration timeout = const Duration(seconds: 10),
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

void _expectComposerText(WidgetTester tester, String expected) {
  final composer = tester.widget<TextField>(
    find.byKey(const ValueKey('agent-message-composer')),
  );
  expect(composer.controller?.text, expected);
}

String _safeMarkdownIdentifierPart(String value) {
  final sanitized = value
      .replaceAll(RegExp(r'[^A-Za-z0-9-]+'), '-')
      .replaceAll(RegExp(r'-+'), '-')
      .replaceAll(RegExp(r'^-|-$'), '');
  return sanitized.isEmpty ? 'agent' : sanitized;
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

Future<void> _activateStoredGatewayProfile(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('connection-details-action'));
  await _expandPanel(
    tester,
    const ValueKey('runtime-mode-panel'),
    childKey: const ValueKey('runtime-mode-segments'),
  );
  await _waitFor(
    tester,
    find.byWidgetPredicate((widget) {
      final key = widget.key;
      if (key is! ValueKey) {
        return false;
      }
      final value = key.value.toString();
      return value.startsWith('gateway-profile-select-') &&
          value != 'gateway-profile-select-none';
    }),
    timeout: const Duration(seconds: 30),
  );
  await _tapTextVisible(tester, 'Paired');
  await _dismissCurrentRoute(
    tester,
    goneKey: const ValueKey('connection-details-panel'),
  );
  await _openCurrentProject(tester);
  await _waitForAgentSelected(tester, _agentName);
}

Future<void> _openSelectedAgentGatewayTerminal(WidgetTester tester) async {
  await _tapVisible(tester, const ValueKey('open-agent-terminal-button'));
  await _waitFor(
    tester,
    find.byKey(const ValueKey('ccb-live-terminal-view')),
    timeout: _realBackendReplyTimeout,
  );
  await _waitForText(
    tester,
    'Gateway WebSocket',
    timeout: _realBackendReplyTimeout,
  );
  await _exerciseTerminalControls(tester);
}

Future<void> _exerciseTerminalControls(WidgetTester tester) async {
  await _enterTextVisible(
    tester,
    const ValueKey('terminal-command-input'),
    'ccb-mobile-ui-send',
  );
  await _tapVisible(tester, const ValueKey('terminal-send-button'));
  await _waitForText(tester, 'Sent', timeout: const Duration(seconds: 15));

  await _enterTextVisible(
    tester,
    const ValueKey('terminal-command-input'),
    'ccb-mobile-ui-paste',
  );
  await _tapVisible(tester, const ValueKey('terminal-paste-button'));
  await _waitForText(tester, 'Pasted', timeout: const Duration(seconds: 15));

  await _tapVisible(tester, const ValueKey('terminal-resize-button'));
  await _waitForText(
    tester,
    'Size synced',
    timeout: const Duration(seconds: 15),
  );

  await _tapVisible(tester, const ValueKey('terminal-reconnect-button'));
  await _waitForAnyText(
    tester,
    const ['Reconnecting', 'Reconnected'],
    timeout: const Duration(seconds: 5),
    diagnostics: () => _terminalControlStatus(tester),
  );
  await _waitForText(
    tester,
    'Reconnected',
    timeout: const Duration(seconds: 20),
    diagnostics: () => _terminalControlStatus(tester),
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

Future<void> _tapTextVisible(WidgetTester tester, String text) async {
  final finder = find.text(text, skipOffstage: false).last;
  await _waitFor(tester, finder);
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  await tester.tap(find.text(text).last);
  await tester.pump();
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

Finder _artifactMarkdownLink(String fileName) {
  return find.byWidgetPredicate((widget) {
    if (widget is! RichText) {
      return false;
    }
    return widget.text.toPlainText().contains(fileName);
  }, description: 'artifact markdown link $fileName');
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
  final composerFinder = find.byKey(
    const ValueKey('agent-message-composer'),
    skipOffstage: false,
  );
  final sendFinder = find.byKey(
    const ValueKey('agent-message-send-button'),
    skipOffstage: false,
  );
  final composerTexts = [
    for (final element in composerFinder.evaluate())
      if (element.widget is TextField)
        (element.widget as TextField).controller?.text ?? '<no-controller>',
  ];
  final sendStates = [
    for (final element in sendFinder.evaluate())
      if (element.widget is IconButton)
        ((element.widget as IconButton).onPressed == null
            ? 'disabled'
            : 'enabled'),
  ];
  final visibleTexts = find
      .byWidgetPredicate((widget) => widget is Text || widget is SelectableText)
      .evaluate()
      .take(24)
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
  return 'composer=$composerTexts send=$sendStates visibleText=$visibleTexts';
}

Future<void> _waitForAnyText(
  WidgetTester tester,
  List<String> texts, {
  Duration timeout = const Duration(seconds: 10),
  String Function()? diagnostics,
}) {
  return _waitFor(
    tester,
    find.byWidgetPredicate(
      (widget) => widget is Text && texts.contains(widget.data),
      description: 'text in ${texts.join(', ')}',
    ),
    timeout: timeout,
    diagnostics: diagnostics,
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

String _terminalControlStatus(WidgetTester tester) {
  final finder = find.byKey(
    const ValueKey('terminal-control-status'),
    skipOffstage: false,
  );
  if (!tester.any(finder)) {
    return 'terminal-control-status not found';
  }
  final widget = tester.widget<Text>(finder.first);
  return 'terminal-control-status=${widget.data ?? ''}';
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
