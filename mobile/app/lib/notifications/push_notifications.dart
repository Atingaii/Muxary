import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import '../pairing/gateway_pairing.dart';

const pushNotificationsFeatureEnabled = bool.fromEnvironment(
  'CCB_MOBILE_PUSH_ENABLED',
  defaultValue: false,
);

class PushNotificationRoute {
  const PushNotificationRoute({
    required this.projectId,
    required this.agent,
    required this.dedupeKey,
    this.hostId,
    this.deviceId,
  });

  final String projectId;
  final String agent;
  final String dedupeKey;
  final String? hostId;
  final String? deviceId;

  factory PushNotificationRoute.fromData(Map<String, String> data) {
    String requiredValue(String key) {
      final value = data[key]?.trim();
      if (value == null || value.isEmpty) {
        throw const FormatException('push route is incomplete');
      }
      return value;
    }

    return PushNotificationRoute(
      projectId: requiredValue('project_id'),
      agent: requiredValue('agent'),
      dedupeKey: requiredValue('dedupe_key'),
      hostId: _optionalValue(data['host_id']),
      deviceId: _optionalValue(data['device_id']),
    );
  }

  bool get hasProfileIdentity => hostId != null && deviceId != null;

  bool matches(GatewayPairedHost host) =>
      (hostId == null || hostId == host.profile.hostId) &&
      (deviceId == null || deviceId == host.profile.deviceId);
}

String? _optionalValue(String? value) {
  final trimmed = value?.trim();
  return trimmed == null || trimmed.isEmpty ? null : trimmed;
}

abstract interface class PushMessagingClient {
  Future<bool> initializeAndRequestPermission();

  Future<String?> getToken();

  Stream<String> get onTokenRefresh;

  Future<PushNotificationRoute?> getInitialRoute();

  Stream<PushNotificationRoute> get onRouteOpened;

  Stream<PushNotificationRoute> get onForegroundRoute;
}

class FirebasePushMessagingClient implements PushMessagingClient {
  FirebasePushMessagingClient({FirebaseMessaging? messaging})
    : _messaging = messaging;

  FirebaseMessaging? _messaging;
  bool _initialized = false;

  @override
  Future<bool> initializeAndRequestPermission() async {
    try {
      if (!_initialized) {
        if (Firebase.apps.isEmpty) {
          await Firebase.initializeApp();
        }
        _messaging ??= FirebaseMessaging.instance;
        await _messaging!.setAutoInitEnabled(true);
        _initialized = true;
      }
      final settings = await _messaging!.requestPermission();
      return settings.authorizationStatus == AuthorizationStatus.authorized ||
          settings.authorizationStatus == AuthorizationStatus.provisional;
    } catch (_) {
      // A private Firebase configuration is optional. Its absence disables
      // push only; pairing and foreground control remain available.
      return false;
    }
  }

  @override
  Future<String?> getToken() async {
    try {
      final messaging = _messaging;
      return messaging == null
          ? null
          : _optionalValue(await messaging.getToken());
    } catch (_) {
      return null;
    }
  }

  @override
  Stream<String> get onTokenRefresh =>
      (_messaging?.onTokenRefresh ?? const Stream.empty())
          .map(_optionalValue)
          .where((token) => token != null)
          .map((token) => token!);

  @override
  Future<PushNotificationRoute?> getInitialRoute() async {
    try {
      final messaging = _messaging;
      if (messaging == null) return null;
      final message = await messaging.getInitialMessage();
      return message == null ? null : _routeOrNull(message.data);
    } catch (_) {
      return null;
    }
  }

  @override
  Stream<PushNotificationRoute> get onRouteOpened => (_messaging == null
          ? const Stream<RemoteMessage>.empty()
          : FirebaseMessaging.onMessageOpenedApp)
      .map((message) => _routeOrNull(message.data))
      .where((route) => route != null)
      .map((route) => route!);

  @override
  Stream<PushNotificationRoute> get onForegroundRoute => (_messaging == null
          ? const Stream<RemoteMessage>.empty()
          : FirebaseMessaging.onMessage)
      .map((message) => _routeOrNull(message.data))
      .where((route) => route != null)
      .map((route) => route!);

  PushNotificationRoute? _routeOrNull(Map<String, dynamic> data) {
    try {
      return PushNotificationRoute.fromData({
        for (final entry in data.entries) entry.key: '${entry.value}',
      });
    } on FormatException {
      return null;
    }
  }
}

class GatewayPushRegistrationClient {
  GatewayPushRegistrationClient({
    HttpClient? httpClient,
    this.timeout = const Duration(seconds: 10),
    bool Function()? isEnabled,
  }) : _httpClient = httpClient ?? HttpClient(),
       _isEnabled = isEnabled ?? (() => pushNotificationsFeatureEnabled);

  final HttpClient _httpClient;
  final Duration timeout;
  final bool Function() _isEnabled;

  Future<bool> register({
    required GatewayPairedHost host,
    required String token,
  }) async {
    final normalizedToken = token.trim();
    if (!_isEnabled() || normalizedToken.isEmpty) {
      return false;
    }
    try {
      final request = await _httpClient
          .putUrl(
            host.profile.routeProvider.gatewayUrl.resolve(
              '/v1/devices/me/push-token',
            ),
          )
          .timeout(timeout);
      request.headers
        ..set(HttpHeaders.authorizationHeader, 'Bearer ${host.deviceToken}')
        ..contentType = ContentType.json;
      request.add(utf8.encode(jsonEncode({'token': normalizedToken})));
      final response = await request.close().timeout(timeout);
      await response.drain<void>();
      return response.statusCode == HttpStatus.ok;
    } catch (_) {
      return false;
    }
  }

  Future<bool> delete({required GatewayPairedHost host}) async {
    try {
      final request = await _httpClient
          .deleteUrl(
            host.profile.routeProvider.gatewayUrl.resolve(
              '/v1/devices/me/push-token',
            ),
          )
          .timeout(timeout);
      request.headers.set(
        HttpHeaders.authorizationHeader,
        'Bearer ${host.deviceToken}',
      );
      final response = await request.close().timeout(timeout);
      await response.drain<void>();
      return response.statusCode == HttpStatus.ok;
    } catch (_) {
      return false;
    }
  }

  void close({bool force = false}) => _httpClient.close(force: force);
}

class PushNotificationRuntime {
  PushNotificationRuntime({
    required PushMessagingClient messaging,
    required GatewayPushRegistrationClient registration,
    required Future<void> Function(PushNotificationRoute route) onRouteOpened,
    Future<void> Function(PushNotificationRoute route)? onForegroundRoute,
    Future<bool> Function(String dedupeKey)? markSeenIfNew,
    bool Function(PushNotificationRoute route)? isRouteProfileAmbiguous,
    bool Function()? isEnabled,
  }) : _messaging = messaging,
       _registration = registration,
       _onRouteOpened = onRouteOpened,
       _onForegroundRoute = onForegroundRoute,
       _markSeenIfNew = markSeenIfNew,
       _isRouteProfileAmbiguous = isRouteProfileAmbiguous ?? ((_) => false),
       _isEnabled = isEnabled ?? (() => pushNotificationsFeatureEnabled);

  final PushMessagingClient _messaging;
  final GatewayPushRegistrationClient _registration;
  final Future<void> Function(PushNotificationRoute route) _onRouteOpened;
  final Future<void> Function(PushNotificationRoute route)? _onForegroundRoute;
  final Future<bool> Function(String dedupeKey)? _markSeenIfNew;
  final bool Function(PushNotificationRoute route) _isRouteProfileAmbiguous;
  final bool Function() _isEnabled;
  StreamSubscription<String>? _tokenRefreshSubscription;
  StreamSubscription<PushNotificationRoute>? _routeSubscription;
  StreamSubscription<PushNotificationRoute>? _foregroundRouteSubscription;
  final Set<String> _foregroundRouteDedupeKeys = <String>{};
  GatewayPairedHost? _host;
  GatewayPairedHost? _registeredHost;
  bool _started = false;

  Future<bool> start(GatewayPairedHost host) async {
    await stop();
    if (!_isEnabled() || !host.profile.scopes.contains('notify')) {
      return false;
    }
    if (!await _messaging.initializeAndRequestPermission()) {
      return false;
    }
    _host = host;
    _started = true;
    _tokenRefreshSubscription = _messaging.onTokenRefresh.listen(
      _registerToken,
    );
    _routeSubscription = _messaging.onRouteOpened.listen(_openRoute);
    _foregroundRouteSubscription = _messaging.onForegroundRoute.listen(
      _recordForegroundRoute,
    );
    final token = await _messaging.getToken();
    if (token == null || !await _registerToken(token)) {
      await stop();
      return false;
    }
    final initialRoute = await _messaging.getInitialRoute();
    if (initialRoute != null) {
      await _openRoute(initialRoute);
    }
    return true;
  }

  Future<void> stop() async {
    final registeredHost = _registeredHost;
    _registeredHost = null;
    _started = false;
    _host = null;
    await _tokenRefreshSubscription?.cancel();
    await _routeSubscription?.cancel();
    await _foregroundRouteSubscription?.cancel();
    _tokenRefreshSubscription = null;
    _routeSubscription = null;
    _foregroundRouteSubscription = null;
    _foregroundRouteDedupeKeys.clear();
    if (registeredHost != null) {
      await _registration.delete(host: registeredHost);
    }
  }

  Future<void> dispose() async {
    await stop();
    _registration.close(force: true);
  }

  Future<bool> _registerToken(String token) async {
    final host = _host;
    if (!_started || host == null) return false;
    final registered = await _registration.register(host: host, token: token);
    if (registered && _isCurrentHost(host)) {
      _registeredHost = host;
    }
    return registered;
  }

  Future<void> _openRoute(PushNotificationRoute route) async {
    if (!_acceptsRoute(route)) {
      return;
    }
    if (!await _markRouteSeenIfNew(route)) return;
    await _onRouteOpened(route);
  }

  Future<void> _recordForegroundRoute(PushNotificationRoute route) async {
    if (!_acceptsRoute(route)) {
      return;
    }
    if (!_rememberForegroundRoute(route.dedupeKey)) return;
    await _onForegroundRoute?.call(route);
  }

  bool _rememberForegroundRoute(String dedupeKey) {
    if (!_foregroundRouteDedupeKeys.add(dedupeKey)) return false;
    while (_foregroundRouteDedupeKeys.length > 256) {
      _foregroundRouteDedupeKeys.remove(_foregroundRouteDedupeKeys.first);
    }
    return true;
  }

  bool _acceptsRoute(PushNotificationRoute route) {
    final host = _host;
    return _started &&
        host != null &&
        _isCurrentHost(host) &&
        _isRegisteredHost(host) &&
        route.matches(host) &&
        (route.hasProfileIdentity || !_isRouteProfileAmbiguous(route));
  }

  Future<bool> _markRouteSeenIfNew(PushNotificationRoute route) async {
    final markSeenIfNew = _markSeenIfNew;
    if (markSeenIfNew == null) return true;
    try {
      return await markSeenIfNew(route.dedupeKey);
    } catch (_) {}
    return false;
  }

  bool _isCurrentHost(GatewayPairedHost host) =>
      _host != null && _sameGatewayHost(_host!, host);

  bool _isRegisteredHost(GatewayPairedHost host) =>
      _registeredHost != null && _sameGatewayHost(_registeredHost!, host);

  bool _sameGatewayHost(GatewayPairedHost left, GatewayPairedHost right) =>
      left.profile.hostId == right.profile.hostId &&
      left.profile.deviceId == right.profile.deviceId;
}

@pragma('vm:entry-point')
Future<void> ccbMobileFirebaseMessagingBackgroundHandler(
  RemoteMessage message,
) async {
  try {
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp();
    }
  } catch (_) {
    // Missing deployment-owned Firebase config disables push in this isolate.
  }
}

void registerPushNotificationBackgroundHandler() {
  if (!pushNotificationsFeatureEnabled) return;
  FirebaseMessaging.onBackgroundMessage(
    ccbMobileFirebaseMessagingBackgroundHandler,
  );
}
