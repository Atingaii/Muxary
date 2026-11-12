import 'package:ccb_mobile/features/agent_chat/agent_chat_ui_controller_store.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('keeps stable draft and timeline controllers per agent', () {
    final store = AgentChatUiControllerStore();
    addTearDown(store.dispose);

    final draft = store.draftController('mobile_probe')..text = 'hello';
    final timeline = store.timelineScrollController('mobile_probe');

    expect(store.draftController('mobile_probe'), same(draft));
    expect(store.draftController('mobile_probe').text, 'hello');
    expect(store.timelineScrollController('mobile_probe'), same(timeline));
    expect(timeline.initialScrollOffset, initialTimelineScrollOffset);
    expect(store.draftController('mobile_peer'), isNot(same(draft)));
  });

  test('treats unattached timelines as near the end', () {
    final store = AgentChatUiControllerStore();
    addTearDown(store.dispose);

    store.timelineScrollController('mobile_probe');

    expect(store.isTimelineNearEnd('mobile_probe'), isTrue);
    expect(store.isTimelineNearEnd('missing_agent'), isTrue);
  });

  testWidgets('scrollTimelineToEnd animates attached timeline to max extent', (
    tester,
  ) async {
    final store = AgentChatUiControllerStore();
    addTearDown(store.dispose);
    final controller = store.timelineScrollController('mobile_probe');

    await tester.pumpWidget(
      MaterialApp(
        home: SizedBox(
          height: 120,
          child: ListView(
            controller: controller,
            children: List.generate(
              16,
              (index) => const SizedBox(height: 40, child: Text('row')),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    controller.jumpTo(0);

    store.scrollTimelineToEnd(
      'mobile_probe',
      isActive: (agentName) => agentName == 'mobile_probe',
    );
    await tester.pump();
    await tester.pumpAndSettle();

    expect(controller.position.pixels, controller.position.maxScrollExtent);
  });

  testWidgets('rapid follow-latest requests coalesce into one smooth settle', (
    tester,
  ) async {
    final store = AgentChatUiControllerStore();
    addTearDown(store.dispose);
    final controller = store.timelineScrollController('mobile_probe');

    await tester.pumpWidget(
      MaterialApp(
        home: SizedBox(
          height: 120,
          child: ListView(
            controller: controller,
            children: List.generate(
              24,
              (index) => const SizedBox(height: 40, child: Text('row')),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    controller.jumpTo(0);

    for (var index = 0; index < 8; index += 1) {
      store.scrollTimelineToEnd(
        'mobile_probe',
        isActive: (agentName) => agentName == 'mobile_probe',
      );
    }
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 1));
    await tester.pump(agentChatFollowLatestScrollDuration);
    await tester.pump(const Duration(milliseconds: 1));

    expect(controller.position.pixels, controller.position.maxScrollExtent);
    expect(controller.position.isScrollingNotifier.value, isFalse);
  });

  testWidgets('user scroll cancellation wins over queued follow-latest', (
    tester,
  ) async {
    final store = AgentChatUiControllerStore();
    addTearDown(store.dispose);
    final controller = store.timelineScrollController('mobile_probe');

    await tester.pumpWidget(
      MaterialApp(
        home: SizedBox(
          height: 120,
          child: ListView(
            controller: controller,
            children: List.generate(
              24,
              (index) => const SizedBox(height: 40, child: Text('row')),
            ),
          ),
        ),
      ),
    );
    await tester.pump();
    controller.jumpTo(0);

    store.scrollTimelineToEnd(
      'mobile_probe',
      isActive: (agentName) => agentName == 'mobile_probe',
    );
    store.cancelTimelineAutoFollow('mobile_probe');
    await tester.pump();
    await tester.pump(agentChatFollowLatestScrollDuration);

    expect(controller.position.pixels, 0);
  });
}
