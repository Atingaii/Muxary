import 'dart:async';

import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract class CcbBackgroundConnectionPreferenceStore {
  Future<bool> read();

  Future<void> write(bool enabled);
}

class FlutterCcbBackgroundConnectionPreferenceStore
    implements CcbBackgroundConnectionPreferenceStore {
  FlutterCcbBackgroundConnectionPreferenceStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _key = 'ccb_mobile.background_connection.enabled';

  final FlutterSecureStorage _storage;

  @override
  Future<bool> read() async {
    return await _storage.read(key: _key) == 'true';
  }

  @override
  Future<void> write(bool enabled) {
    return _storage.write(key: _key, value: enabled.toString());
  }
}

abstract interface class BackgroundConnectionPlatform {
  Future<bool> start();

  Future<void> stop();

  Future<BackgroundConnectionSystemStatus> readSystemStatus();

  Future<bool> openSystemSettings();
}

class BackgroundConnectionSystemStatus {
  const BackgroundConnectionSystemStatus({
    required this.backgroundRestricted,
    required this.batteryOptimizationExempt,
    required this.lowPowerStandbyRestricted,
  });

  factory BackgroundConnectionSystemStatus.fromMap(
    Map<Object?, Object?> value,
  ) {
    return BackgroundConnectionSystemStatus(
      backgroundRestricted: value['background_restricted'] == true,
      batteryOptimizationExempt: value['battery_optimization_exempt'] == true,
      lowPowerStandbyRestricted: value['low_power_standby_restricted'] == true,
    );
  }

  final bool backgroundRestricted;
  final bool batteryOptimizationExempt;
  final bool lowPowerStandbyRestricted;

  bool get isRestricted => backgroundRestricted || lowPowerStandbyRestricted;
}

class BackgroundConnectionPlatformException implements Exception {
  const BackgroundConnectionPlatformException(this.message);

  final String message;

  @override
  String toString() => 'BackgroundConnectionPlatformException($message)';
}

class MethodChannelBackgroundConnectionPlatform
    implements BackgroundConnectionPlatform {
  const MethodChannelBackgroundConnectionPlatform();

  static const _channel = MethodChannel('io.ccb.mobile/background_connection');

  @override
  Future<bool> start() async {
    try {
      return await _channel.invokeMethod<bool>('start') ?? false;
    } on PlatformException catch (error) {
      throw BackgroundConnectionPlatformException(error.message ?? error.code);
    } on MissingPluginException {
      throw const BackgroundConnectionPlatformException(
        'Background connection is not supported on this platform.',
      );
    }
  }

  @override
  Future<void> stop() async {
    try {
      await _channel.invokeMethod<void>('stop');
    } on PlatformException catch (error) {
      throw BackgroundConnectionPlatformException(error.message ?? error.code);
    } on MissingPluginException {
      throw const BackgroundConnectionPlatformException(
        'Background connection is not supported on this platform.',
      );
    }
  }

  @override
  Future<BackgroundConnectionSystemStatus> readSystemStatus() async {
    try {
      final value = await _channel.invokeMethod<Map<Object?, Object?>>(
        'readSystemStatus',
      );
      if (value == null) {
        throw const BackgroundConnectionPlatformException(
          'Android did not return background restriction status.',
        );
      }
      return BackgroundConnectionSystemStatus.fromMap(value);
    } on PlatformException catch (error) {
      throw BackgroundConnectionPlatformException(error.message ?? error.code);
    } on MissingPluginException {
      throw const BackgroundConnectionPlatformException(
        'Background settings are not supported on this platform.',
      );
    }
  }

  @override
  Future<bool> openSystemSettings() async {
    try {
      return await _channel.invokeMethod<bool>('openSystemSettings') ?? false;
    } on PlatformException catch (error) {
      throw BackgroundConnectionPlatformException(error.message ?? error.code);
    } on MissingPluginException {
      throw const BackgroundConnectionPlatformException(
        'Background settings are not supported on this platform.',
      );
    }
  }
}

class BackgroundConnectionRuntime {
  BackgroundConnectionRuntime({
    required BackgroundConnectionPlatform platform,
    required void Function(bool running) onRunningChanged,
    required void Function() onStartFailed,
  }) : _platform = platform,
       _onRunningChanged = onRunningChanged,
       _onStartFailed = onStartFailed;

  final BackgroundConnectionPlatform _platform;
  final void Function(bool running) _onRunningChanged;
  final void Function() _onStartFailed;

  bool _desired = false;
  bool _canStart = false;
  bool _running = false;
  bool _startFailureLatched = false;
  bool _reconcileRequested = false;
  bool _disposed = false;
  Future<void>? _reconcileFuture;

  bool get running => _running;

  void update({required bool shouldRun, required bool canStart}) {
    if (_disposed) {
      return;
    }
    if (!shouldRun || !_desired) {
      _startFailureLatched = false;
    }
    _desired = shouldRun;
    _canStart = canStart;
    _requestReconcile();
  }

  void _requestReconcile() {
    _reconcileRequested = true;
    if (_reconcileFuture != null) {
      return;
    }
    final completer = Completer<void>();
    _reconcileFuture = completer.future;
    unawaited(_drainReconcile(completer));
  }

  Future<void> _drainReconcile(Completer<void> completer) async {
    try {
      while (_reconcileRequested && !_disposed) {
        _reconcileRequested = false;
        if (_desired == _running) {
          continue;
        }
        if (_desired) {
          if (!_canStart || _startFailureLatched) {
            continue;
          }
          var started = false;
          try {
            started = await _platform.start();
          } on BackgroundConnectionPlatformException {
            started = false;
          }
          if (_disposed) {
            if (started) {
              await _stopPlatform();
            }
            return;
          }
          if (!started) {
            _startFailureLatched = true;
            _onStartFailed();
            continue;
          }
          _setRunning(true);
          if (!_desired) {
            _reconcileRequested = true;
          }
        } else {
          await _stopPlatform();
          _setRunning(false);
        }
      }
    } finally {
      _reconcileFuture = null;
      if (!completer.isCompleted) {
        completer.complete();
      }
      if (_reconcileRequested && !_disposed) {
        _requestReconcile();
      }
    }
  }

  void _setRunning(bool running) {
    if (_running == running) {
      return;
    }
    _running = running;
    _onRunningChanged(running);
  }

  Future<void> _stopPlatform() async {
    try {
      await _platform.stop();
    } on BackgroundConnectionPlatformException {
      // The service owns no durable mutations or queued input. A later
      // explicit transition can retry without replaying work.
    }
  }

  Future<void> dispose() async {
    if (_disposed) {
      return;
    }
    _disposed = true;
    final reconcile = _reconcileFuture;
    if (reconcile != null) {
      await reconcile;
    }
    if (_running) {
      await _stopPlatform();
      _running = false;
    }
  }
}
