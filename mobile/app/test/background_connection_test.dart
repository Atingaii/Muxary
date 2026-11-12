import 'dart:async';

import 'package:flutter_test/flutter_test.dart';

import 'package:ccb_mobile/ccb_mobile.dart';

void main() {
  test('system status preserves Android restriction signals', () {
    final status = BackgroundConnectionSystemStatus.fromMap(const {
      'background_restricted': false,
      'battery_optimization_exempt': false,
      'low_power_standby_restricted': true,
    });

    expect(status.backgroundRestricted, isFalse);
    expect(status.batteryOptimizationExempt, isFalse);
    expect(status.lowPowerStandbyRestricted, isTrue);
    expect(status.isRestricted, isTrue);
  });

  test('runtime starts after an initially disabled reconciliation', () async {
    final platform = _FakeBackgroundConnectionPlatform();
    final states = <bool>[];
    final runtime = BackgroundConnectionRuntime(
      platform: platform,
      onRunningChanged: states.add,
      onStartFailed: () => fail('start should succeed'),
    );

    runtime.update(shouldRun: false, canStart: true);
    await pumpEventQueue();
    runtime.update(shouldRun: true, canStart: true);
    await pumpEventQueue();

    expect(platform.startCalls, 1);
    expect(runtime.running, isTrue);
    expect(states, [true]);
    await runtime.dispose();
  });

  test('runtime stops a service when opt-in changes during start', () async {
    final startResult = Completer<bool>();
    final platform = _FakeBackgroundConnectionPlatform(
      startResult: startResult.future,
    );
    final runtime = BackgroundConnectionRuntime(
      platform: platform,
      onRunningChanged: (_) {},
      onStartFailed: () => fail('start should succeed'),
    );

    runtime.update(shouldRun: true, canStart: true);
    await pumpEventQueue();
    runtime.update(shouldRun: false, canStart: true);
    startResult.complete(true);
    await pumpEventQueue();

    expect(platform.startCalls, 1);
    expect(platform.stopCalls, 1);
    expect(runtime.running, isFalse);
    await runtime.dispose();
  });
}

class _FakeBackgroundConnectionPlatform
    implements BackgroundConnectionPlatform {
  _FakeBackgroundConnectionPlatform({Future<bool>? startResult})
    : _startResult = startResult ?? Future<bool>.value(true);

  final Future<bool> _startResult;
  var startCalls = 0;
  var stopCalls = 0;

  @override
  Future<bool> start() {
    startCalls += 1;
    return _startResult;
  }

  @override
  Future<void> stop() async {
    stopCalls += 1;
  }

  @override
  Future<BackgroundConnectionSystemStatus> readSystemStatus() async {
    return const BackgroundConnectionSystemStatus(
      backgroundRestricted: false,
      batteryOptimizationExempt: true,
      lowPowerStandbyRestricted: false,
    );
  }

  @override
  Future<bool> openSystemSettings() async => true;
}
