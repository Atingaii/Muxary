import 'dart:async';

import '../../repository/gateway_mobile_ccb_repository.dart';

class MobilePresenceCoordinator {
  MobilePresenceCoordinator({
    this.heartbeatInterval = const Duration(seconds: 30),
    this.onFailure,
  });

  final Duration heartbeatInterval;
  final void Function(Object error)? onFailure;

  MobileGatewayPresenceReporter? _reporter;
  Timer? _heartbeatTimer;
  String? _focusedProjectId;
  String? _focusedAgent;
  bool _visible = false;
  bool _disposed = false;
  int _generation = 0;
  Future<void>? _inFlight;
  bool _queued = false;
  bool _queuedUserActivity = false;

  void start({
    required MobileGatewayPresenceReporter? reporter,
    required bool visible,
  }) {
    _generation += 1;
    _reporter = reporter;
    _visible = visible;
    _restartHeartbeat();
    _send(userActivity: false);
  }

  void updateTarget({
    required String? projectId,
    required String? agent,
    bool userActivity = false,
  }) {
    final projectChanged = _focusedProjectId != projectId;
    final agentChanged = _focusedAgent != agent;
    _focusedProjectId = projectId;
    _focusedAgent = agent;
    if (projectChanged || agentChanged || userActivity) {
      _send(userActivity: userActivity);
    }
  }

  void setVisible(bool visible) {
    if (_visible == visible) return;
    _visible = visible;
    _restartHeartbeat();
    _send(userActivity: false);
  }

  void markUserActivity() {
    _send(userActivity: true);
  }

  void stop() {
    _generation += 1;
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    _reporter = null;
    _queued = false;
    _queuedUserActivity = false;
  }

  void dispose() {
    _disposed = true;
    stop();
  }

  void _restartHeartbeat() {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    if (!_visible || _reporter == null || heartbeatInterval <= Duration.zero) {
      return;
    }
    _heartbeatTimer = Timer.periodic(
      heartbeatInterval,
      (_) => _send(userActivity: false),
    );
  }

  void _send({required bool userActivity}) {
    if (_disposed || _reporter == null) return;
    if (_inFlight != null) {
      _queued = true;
      _queuedUserActivity = _queuedUserActivity || userActivity;
      return;
    }
    final generation = _generation;
    final reporter = _reporter!;
    final request = reporter.reportPresence(
      visible: _visible,
      focusedProjectId: _focusedProjectId,
      focusedAgent: _focusedAgent,
      userActivity: userActivity,
    );
    _inFlight = request;
    unawaited(
      request
          .catchError((Object error) {
            if (generation == _generation && !_disposed) {
              onFailure?.call(error);
            }
          })
          .whenComplete(() {
            if (generation != _generation || _disposed) return;
            _inFlight = null;
            if (_queued) {
              final queuedUserActivity = _queuedUserActivity;
              _queued = false;
              _queuedUserActivity = false;
              _send(userActivity: queuedUserActivity);
            }
          }),
    );
  }
}
