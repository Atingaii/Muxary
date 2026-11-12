import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ccb_mobile/ccb_mobile.dart';

Future<void> openConnectionDetails(WidgetTester tester) async {
  await tester.tap(find.byKey(const ValueKey('connection-details-action')));
  await tester.pumpAndSettle();
}

Future<void> activateStoredGatewayProfile(WidgetTester tester) async {
  await openConnectionDetails(tester);
  await expandTile(tester, const ValueKey('runtime-mode-panel'));
  final segments = tester.widget<SegmentedButton<AppRuntimeMode>>(
    find.byKey(const ValueKey('runtime-mode-segments')),
  );
  segments.onSelectionChanged?.call({AppRuntimeMode.pairedGateway});
  await tester.pumpAndSettle();
  await dismissConnectionDetails(tester);
  await openCurrentProject(tester);
}

Future<void> setTestSurfaceSize(WidgetTester tester, Size size) async {
  tester.view.devicePixelRatio = 1;
  tester.view.physicalSize = size;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

void setTestViewInsets(WidgetTester tester, EdgeInsets insets) {
  tester.view.viewInsets = FakeViewPadding(
    left: insets.left,
    top: insets.top,
    right: insets.right,
    bottom: insets.bottom,
  );
  addTearDown(tester.view.resetViewInsets);
}

Future<void> openCurrentProject(WidgetTester tester) async {
  expect(find.byKey(const ValueKey('project-list')), findsOneWidget);
  final currentProject = find.byKey(const ValueKey('project-open-current'));
  if (currentProject.evaluate().isNotEmpty) {
    await tester.tap(currentProject);
  } else {
    await tester.tap(_serverProjectTileFinder().first);
  }
  await tester.pumpAndSettle();
  expect(find.byKey(const ValueKey('agent-switcher')), findsOneWidget);
  expect(
    find.byKey(const ValueKey('selected-agent-workspace')),
    findsOneWidget,
  );
}

Finder _serverProjectTileFinder() {
  return find.byWidgetPredicate((widget) {
    final key = widget.key;
    return key is ValueKey<String> &&
        key.value.startsWith('project-open-') &&
        key.value != 'project-open-current';
  });
}

void expectAgentTileSelected(WidgetTester tester, String agentName) {
  final tile = tester.widget<ListTile>(
    find.byKey(ValueKey('agent-$agentName')),
  );
  expect(tile.selected, isTrue);
}

void expectAgentSelected(WidgetTester tester, String agentName) {
  final chip = tester.widget<ChoiceChip>(
    find.byKey(ValueKey('agent-$agentName')),
  );
  expect(chip.selected, isTrue);
}

void expectWindowSelected(WidgetTester tester, String windowName) {
  final chip = tester.widget<ChoiceChip>(
    find.byKey(ValueKey('window-tab-$windowName')),
  );
  expect(chip.selected, isTrue);
}

Future<void> expandTile(WidgetTester tester, Key key) async {
  await tester.ensureVisible(find.byKey(key));
  await tester.pump(const Duration(milliseconds: 100));
  await tester.tap(find.byKey(key));
  await tester.pump(const Duration(milliseconds: 350));
}

Future<void> dismissConnectionDetails(WidgetTester tester) async {
  final close = find.byTooltip('Close');
  if (close.evaluate().isNotEmpty) {
    await tester.tap(close);
  } else {
    await tester.tap(find.byTooltip('Back'));
  }
  await tester.pumpAndSettle();
}

Future<void> tapVisible(WidgetTester tester, Key key) async {
  final finder = find.byKey(key);
  if (finder.evaluate().isEmpty &&
      find.byKey(const ValueKey('agent-chat-timeline')).evaluate().isNotEmpty) {
    final foundByScrollingDown = await _dragUntilVisibleMaybe(
      tester,
      key,
      const Offset(0, -560),
    );
    if (!foundByScrollingDown) {
      await _dragUntilVisibleMaybe(tester, key, const Offset(0, 560));
    }
  }
  final scrollable =
      find.byKey(const ValueKey('connection-details-scroll')).evaluate().isEmpty
          ? find.byType(Scrollable).last
          : find.byKey(const ValueKey('connection-details-scroll'));
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
  for (var i = 0; i < 8; i += 1) {
    final center = tester.getCenter(finder);
    if (center.dy > 72 && center.dy < 540) {
      break;
    }
    await tester.drag(scrollable, Offset(0, center.dy >= 540 ? -120 : 120));
    await tester.pump(const Duration(milliseconds: 100));
  }
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> dragUntilVisible(
  WidgetTester tester,
  Key key,
  Offset offset, {
  int maxDrags = 40,
}) async {
  final found = await _dragUntilVisibleMaybe(
    tester,
    key,
    offset,
    maxDrags: maxDrags,
  );
  if (found) {
    return;
  }
  final foundInReverse = await _dragUntilVisibleMaybe(
    tester,
    key,
    Offset(-offset.dx, -offset.dy),
    maxDrags: maxDrags,
  );
  expect(foundInReverse, isTrue);
}

Future<bool> _dragUntilVisibleMaybe(
  WidgetTester tester,
  Key key,
  Offset offset, {
  int maxDrags = 40,
}) async {
  final finder = find.byKey(key);
  final scrollable = find.byKey(const ValueKey('agent-chat-timeline'));
  for (var i = 0; i < maxDrags && finder.evaluate().isEmpty; i += 1) {
    await tester.drag(scrollable, offset);
    await tester.pump(const Duration(milliseconds: 50));
  }
  return finder.evaluate().isNotEmpty;
}
