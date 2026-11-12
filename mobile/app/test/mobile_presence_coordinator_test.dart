import 'dart:async';

import 'package:ccb_mobile/features/project_home/mobile_presence_coordinator.dart';
import 'package:ccb_mobile/repository/gateway_mobile_ccb_repository.dart';
import 'package:test/test.dart';

void main() {
  test('publishes visibility, target, and real user activity', () async {
    final reporter = _RecordingPresenceReporter();
    final coordinator = MobilePresenceCoordinator(
      heartbeatInterval: const Duration(hours: 1),
    );

    coordinator.start(reporter: reporter, visible: true);
    await _flush();
    coordinator.updateTarget(
      projectId: 'project-a',
      agent: 'talk1',
      userActivity: true,
    );
    await _flush();
    coordinator.setVisible(false);
    await _flush();

    expect(reporter.calls, [
      const _PresenceCall(visible: true),
      const _PresenceCall(
        visible: true,
        projectId: 'project-a',
        agent: 'talk1',
        userActivity: true,
      ),
      const _PresenceCall(
        visible: false,
        projectId: 'project-a',
        agent: 'talk1',
      ),
    ]);
    coordinator.dispose();
  });

  test('coalesces an in-flight heartbeat without retrying a failure', () async {
    final gate = Completer<void>();
    final failures = <Object>[];
    final reporter = _RecordingPresenceReporter(gate: gate, failFirst: true);
    final coordinator = MobilePresenceCoordinator(
      heartbeatInterval: const Duration(hours: 1),
      onFailure: failures.add,
    );

    coordinator.start(reporter: reporter, visible: true);
    coordinator.updateTarget(
      projectId: 'project-b',
      agent: 'worker',
      userActivity: true,
    );
    gate.complete();
    await _flush();
    await _flush();

    expect(failures, hasLength(1));
    expect(reporter.calls, hasLength(2));
    expect(reporter.calls.last.userActivity, isTrue);
    expect(reporter.calls.last.projectId, 'project-b');
    coordinator.dispose();
  });
}

Future<void> _flush() async {
  await Future<void>.delayed(Duration.zero);
  await Future<void>.delayed(Duration.zero);
}

class _RecordingPresenceReporter implements MobileGatewayPresenceReporter {
  _RecordingPresenceReporter({this.gate, this.failFirst = false});

  final Completer<void>? gate;
  final bool failFirst;
  final calls = <_PresenceCall>[];

  @override
  Future<void> reportPresence({
    required bool visible,
    String? focusedProjectId,
    String? focusedAgent,
    bool userActivity = false,
  }) async {
    calls.add(
      _PresenceCall(
        visible: visible,
        projectId: focusedProjectId,
        agent: focusedAgent,
        userActivity: userActivity,
      ),
    );
    if (calls.length == 1 && gate != null) await gate!.future;
    if (calls.length == 1 && failFirst) throw StateError('route unavailable');
  }
}

class _PresenceCall {
  const _PresenceCall({
    required this.visible,
    this.projectId,
    this.agent,
    this.userActivity = false,
  });

  final bool visible;
  final String? projectId;
  final String? agent;
  final bool userActivity;

  @override
  bool operator ==(Object other) =>
      other is _PresenceCall &&
      other.visible == visible &&
      other.projectId == projectId &&
      other.agent == agent &&
      other.userActivity == userActivity;

  @override
  int get hashCode => Object.hash(visible, projectId, agent, userActivity);
}
