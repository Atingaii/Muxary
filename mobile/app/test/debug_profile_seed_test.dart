import 'dart:convert';

import 'package:ccb_mobile/debug/debug_profile_seed.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  String encodedProfile() {
    return base64Url
        .encode(
          utf8.encode(
            jsonEncode({
              'schema_version': 1,
              'profile': {
                'host_id': 'host-debug',
                'device_id': 'dev-debug',
                'route_provider': 'lan',
                'gateway_url': 'http://127.0.0.1:18890',
                'scopes': ['ask', 'view'],
              },
              'device_token': 'debug-token',
              'project_id': 'proj-debug',
            }),
          ),
        )
        .replaceAll('=', '');
  }

  test('debug paired host seed decodes secure profile in debug mode', () {
    final host = debugPairedHostFromEnvironment(
      debugMode: true,
      encoded: encodedProfile(),
    );

    expect(host?.profile.hostId, 'host-debug');
    expect(host?.profile.deviceId, 'dev-debug');
    expect(host?.profile.routeProvider.kind, RouteProviderKind.lan);
    expect(
      host?.profile.routeProvider.gatewayUrl.toString(),
      'http://127.0.0.1:18890',
    );
    expect(host?.profile.scopes, {'ask', 'view'});
    expect(host?.deviceToken, 'debug-token');
    expect(host?.projectId, 'proj-debug');
  });

  test('debug paired host seed is disabled outside debug mode', () {
    final host = debugPairedHostFromEnvironment(
      debugMode: false,
      encoded: encodedProfile(),
    );

    expect(host, isNull);
  });

  test('debug paired host seed can be enabled for profile integration tests', () {
    final host = debugPairedHostFromEnvironment(
      debugMode: false,
      allowProfileTestSeed: true,
      encoded: encodedProfile(),
    );

    expect(host?.profile.hostId, 'host-debug');
    expect(host?.deviceToken, 'debug-token');
  });
}
