import 'dart:async';
import 'dart:math';

import '../../pairing/gateway_pairing.dart';
import '../../notifications/task_completion_notifications.dart';
import '../../repository/gateway_mobile_ccb_repository.dart';
import '../../transport/http_gateway_transport.dart';
import '../../transport/gateway_connection_outcome.dart';

/// App-lifetime authority for route/auth state. Pages keep their cached data;
/// they report request outcomes here instead of independently clearing profiles
/// or scheduling retries.
enum MobileConnectionState {
  offline,
  connecting,
  online,
  degraded,
  reconnecting,
  authenticationRequired,
  stopped,
}

enum MobileTransportKind { httpRead, sse, terminalRead, mutation }

/// Explicitly distinguishes a revoked device/invalid credential from a
/// route error or a scope denial. A 403 alone never deletes a profile.
enum MobileAuthDisposition { none, credentialInvalid, scopeDenied }

class MobileConnectionSnapshot {
  const MobileConnectionSnapshot(this.state, {this.retryIn});

  final MobileConnectionState state;
  final Duration? retryIn;
}

typedef MobileConnectionStateListener =
    void Function(MobileConnectionSnapshot snapshot);

class MobileConnectionSupervisor {
  MobileConnectionSupervisor({
    required MobileConnectionStateListener onChanged,
    this.initialDelay = const Duration(seconds: 1),
    this.maxDelay = const Duration(seconds: 30),
    Random? random,
  }) : _onChanged = onChanged,
       _random = random ?? Random();

  final MobileConnectionStateListener _onChanged;
  final Duration initialDelay;
  final Duration maxDelay;
  final Random _random;
  Timer? _retryTimer;
  GatewayPairedHost? _profile;
  MobileGatewayProfileHealthProbe? _probe;
  Duration? _nextDelay;
  var _disposed = false;
  int? _inFlightGeneration;
  int? _queuedGeneration;
  var _generation = 0;

  MobileConnectionSnapshot _snapshot = const MobileConnectionSnapshot(
    MobileConnectionState.stopped,
  );
  MobileConnectionSnapshot get snapshot => _snapshot;

  void start({
    required GatewayPairedHost profile,
    MobileGatewayProfileHealthProbe? probe,
    bool probeImmediately = true,
  }) {
    _generation += 1;
    _profile = profile;
    _probe = probe;
    _nextDelay = initialDelay;
    _retryTimer?.cancel();
    _retryTimer = null;
    _emit(const MobileConnectionSnapshot(MobileConnectionState.connecting));
    if (probeImmediately) {
      _probeNow(_generation);
    }
  }

  void reportSuccess() {
    if (_profile == null || _disposed) return;
    _retryTimer?.cancel();
    _retryTimer = null;
    _nextDelay = initialDelay;
    _emit(const MobileConnectionSnapshot(MobileConnectionState.online));
  }

  void reportFailure(
    Object error, {
    MobileTransportKind kind = MobileTransportKind.httpRead,
    MobileAuthDisposition auth = MobileAuthDisposition.none,
  }) {
    if (_profile == null || _disposed) return;
    if (auth == MobileAuthDisposition.credentialInvalid) {
      _retryTimer?.cancel();
      _emit(
        const MobileConnectionSnapshot(
          MobileConnectionState.authenticationRequired,
        ),
      );
      return;
    }
    if (kind == MobileTransportKind.mutation) {
      return;
    }
    if (kind == MobileTransportKind.terminalRead) {
      // Terminal availability is independent of the core HTTP authority.
      // A terminal fault must not disable ordinary gateway reads or chat.
      if (auth == MobileAuthDisposition.scopeDenied) {
        _emit(const MobileConnectionSnapshot(MobileConnectionState.degraded));
      }
      return;
    }
    if (auth == MobileAuthDisposition.scopeDenied) {
      _emit(const MobileConnectionSnapshot(MobileConnectionState.degraded));
      return;
    }
    _scheduleRetry(degraded: kind == MobileTransportKind.sse);
  }

  void foregroundResume() {
    if (_profile == null || _disposed) return;
    _retryTimer?.cancel();
    _retryTimer = null;
    _probeNow(_generation);
  }

  void retryNow() => foregroundResume();

  void verifyCoreAfterDataFailure() {
    if (_profile == null || _disposed) return;
    if (_retryTimer != null || _inFlightGeneration != null) return;
    _probeNow(_generation);
  }

  void stop() {
    _retryTimer?.cancel();
    _retryTimer = null;
    _profile = null;
    _probe = null;
    _generation += 1;
    _emit(const MobileConnectionSnapshot(MobileConnectionState.stopped));
  }

  void dispose() {
    _disposed = true;
    stop();
  }

  Future<void> _probeNow(int generation) async {
    if (_profile == null || _disposed) return;
    if (_inFlightGeneration != null) {
      _queuedGeneration = generation;
      return;
    }
    _inFlightGeneration = generation;
    _emit(const MobileConnectionSnapshot(MobileConnectionState.connecting));
    try {
      final probe = _probe;
      if (probe != null) {
        if (probe case final MobileGatewayCoreRouteVerifier verifier) {
          await verifier.verifyCoreRoutes().timeout(const Duration(seconds: 4));
        } else {
          final health = await probe.health().timeout(
            const Duration(seconds: 4),
          );
          if (health.status.toLowerCase() != 'ok') {
            throw GatewayHttpException(
              Uri(),
              503,
              'gateway health is degraded',
            );
          }
          final device = await probe.device().timeout(
            const Duration(seconds: 4),
          );
          if (device.revoked) {
            throw GatewayHttpException(Uri(), 401, 'device revoked');
          }
        }
      }
      if (generation != _generation) return;
      reportSuccess();
    } catch (error) {
      if (generation == _generation) {
        reportFailure(
          error,
          auth: switch (error) {
            GatewayHttpException(statusCode: 401) =>
              MobileAuthDisposition.credentialInvalid,
            GatewayHttpException(statusCode: 403) =>
              MobileAuthDisposition.scopeDenied,
            _ => MobileAuthDisposition.none,
          },
        );
      }
    } finally {
      _inFlightGeneration = null;
      final queued = _queuedGeneration;
      _queuedGeneration = null;
      if (queued != null && queued == _generation && !_disposed) {
        _probeNow(queued);
      }
    }
  }

  void _scheduleRetry({bool degraded = false}) {
    if (_retryTimer != null || _disposed) return;
    final base = _nextDelay ?? initialDelay;
    final jitter = 0.9 + (_random.nextDouble() * 0.2);
    final delay = Duration(
      milliseconds: max(1, (base.inMilliseconds * jitter).round()),
    );
    _emit(
      MobileConnectionSnapshot(
        degraded
            ? MobileConnectionState.degraded
            : MobileConnectionState.reconnecting,
        retryIn: delay,
      ),
    );
    final doubled = Duration(milliseconds: base.inMilliseconds * 2);
    _nextDelay = doubled > maxDelay ? maxDelay : doubled;
    _retryTimer = Timer(delay, () {
      _retryTimer = null;
      _probeNow(_generation);
    });
  }

  void _emit(MobileConnectionSnapshot value) {
    _snapshot = value;
    if (!_disposed) _onChanged(value);
  }
}

/// Converts raw gateway outcomes into the sole app-lifetime connection state.
/// The adapter intentionally has no retry mechanism: a failed mutation is
/// reported but never repeated, while the supervisor probes only safe health
/// endpoints before consumers refresh their reads.
class MobileConnectionOutcomeAdapter
    implements GatewayConnectionOutcomeReporter {
  MobileConnectionOutcomeAdapter({
    required MobileConnectionSupervisor supervisor,
    required bool Function() isCurrent,
  }) : _supervisor = supervisor,
       _isCurrent = isCurrent;

  final MobileConnectionSupervisor _supervisor;
  final bool Function() _isCurrent;

  @override
  void succeeded(GatewayConnectionOperation operation) {
    if (!_isCurrent()) return;
    switch (operation) {
      case GatewayConnectionOperation.coreRead:
        _supervisor.reportSuccess();
      case GatewayConnectionOperation.dataRead:
        // A successful content read does not prove that both core authority
        // routes are healthy, and must not clear a core reconnect state.
        return;
      case GatewayConnectionOperation.stream:
      case GatewayConnectionOperation.terminal:
        // Optional live-update and terminal transports do not establish that
        // the core HTTP routes are usable. Probe only bounded safe reads.
        _supervisor.foregroundResume();
      case GatewayConnectionOperation.mutation:
        // A mutation is never retried or used as route-health authority.
        return;
    }
  }

  @override
  void failed(GatewayConnectionOperation operation, Object error) {
    if (!_isCurrent()) return;
    final auth = _authDisposition(error);
    if (operation == GatewayConnectionOperation.dataRead &&
        auth == MobileAuthDisposition.none) {
      // Conversation, view, history, and download timeouts are local failures.
      // Probe the core routes once to distinguish a slow endpoint from a real
      // gateway outage without entering a global reconnect loop.
      _supervisor.verifyCoreAfterDataFailure();
      return;
    }
    _supervisor.reportFailure(
      error,
      kind: switch (operation) {
        GatewayConnectionOperation.coreRead => MobileTransportKind.httpRead,
        GatewayConnectionOperation.dataRead => MobileTransportKind.httpRead,
        GatewayConnectionOperation.stream => MobileTransportKind.sse,
        GatewayConnectionOperation.terminal => MobileTransportKind.terminalRead,
        GatewayConnectionOperation.mutation => MobileTransportKind.mutation,
      },
      auth: auth,
    );
  }

  MobileAuthDisposition _authDisposition(Object error) {
    if (error is GatewayHttpException) {
      if (error.statusCode == 401) {
        return MobileAuthDisposition.credentialInvalid;
      }
      if (error.statusCode == 403) return MobileAuthDisposition.scopeDenied;
    }
    if (error is GatewayTaskCompletionNotificationStreamException) {
      if (error.statusCode == 401) {
        return MobileAuthDisposition.credentialInvalid;
      }
      if (error.statusCode == 403) return MobileAuthDisposition.scopeDenied;
    }
    return MobileAuthDisposition.none;
  }
}
