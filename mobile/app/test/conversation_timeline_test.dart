import 'package:ccb_mobile/features/agent_chat/conversation_timeline.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('detects near-start threshold for older conversation loading', () {
    expect(_nearStart(72), isTrue);
    expect(_nearStart(73), isFalse);
  });

  test('detects near-end threshold for latest-message clearing', () {
    expect(_nearEnd(pixels: 928, maxScrollExtent: 1000), isTrue);
    expect(_nearEnd(pixels: 879, maxScrollExtent: 1000), isFalse);
  });

  testWidgets('detects user-driven drag scroll notifications', (tester) async {
    late BuildContext context;
    await tester.pumpWidget(
      Builder(
        builder: (builderContext) {
          context = builderContext;
          return const SizedBox.shrink();
        },
      ),
    );
    final metrics = _metrics(928);

    expect(
      isUserDrivenScrollNotification(
        UserScrollNotification(
          metrics: metrics,
          context: context,
          direction: ScrollDirection.reverse,
        ),
      ),
      isFalse,
    );
    expect(
      isUserDrivenScrollNotification(
        ScrollUpdateNotification(
          metrics: metrics,
          context: context,
          dragDetails: DragUpdateDetails(globalPosition: Offset.zero),
        ),
      ),
      isTrue,
    );
    expect(
      isUserDrivenScrollNotification(
        ScrollUpdateNotification(metrics: metrics, context: context),
      ),
      isFalse,
    );
    expect(
      isUserDrivenScrollNotification(
        OverscrollNotification(
          metrics: metrics,
          context: context,
          overscroll: 12,
          dragDetails: DragUpdateDetails(globalPosition: Offset.zero),
        ),
      ),
      isTrue,
    );
    expect(
      isUserDrivenScrollNotification(
        OverscrollNotification(
          metrics: metrics,
          context: context,
          overscroll: 12,
        ),
      ),
      isFalse,
    );
  });

  testWidgets('maps user drag notifications to scroll direction', (
    tester,
  ) async {
    late BuildContext context;
    await tester.pumpWidget(
      Builder(
        builder: (builderContext) {
          context = builderContext;
          return const SizedBox.shrink();
        },
      ),
    );
    final metrics = _metrics(100);

    expect(
      userScrollDirectionForNotification(
        ScrollUpdateNotification(
          metrics: metrics,
          context: context,
          dragDetails: DragUpdateDetails(
            globalPosition: Offset.zero,
            delta: Offset(0, -12),
          ),
        ),
      ),
      ScrollDirection.reverse,
    );
    expect(
      userScrollDirectionForNotification(
        ScrollUpdateNotification(
          metrics: metrics,
          context: context,
          dragDetails: DragUpdateDetails(
            globalPosition: Offset.zero,
            delta: Offset(0, 12),
          ),
        ),
      ),
      ScrollDirection.forward,
    );
  });
}

bool _nearStart(double pixels) {
  return isScrollMetricsNearStart(_metrics(pixels));
}

bool _nearEnd({required double pixels, required double maxScrollExtent}) {
  return isScrollMetricsNearEnd(
    _metrics(pixels, maxScrollExtent: maxScrollExtent),
  );
}

FixedScrollMetrics _metrics(double pixels, {double maxScrollExtent = 1000}) {
  return FixedScrollMetrics(
    minScrollExtent: 0,
    maxScrollExtent: maxScrollExtent,
    pixels: pixels,
    viewportDimension: 360,
    axisDirection: AxisDirection.down,
    devicePixelRatio: 1,
  );
}
