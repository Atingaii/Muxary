import 'dart:convert';

import 'package:flutter/foundation.dart';

import '../pairing/gateway_pairing.dart';

const debugPairedHostBase64 = String.fromEnvironment(
  'CCB_MOBILE_DEBUG_PAIRED_HOST_BASE64',
);

const debugAutoActivatePairedHost = bool.fromEnvironment(
  'CCB_MOBILE_DEBUG_AUTO_ACTIVATE',
  defaultValue: true,
);

const testProfileSeedEnabled = bool.fromEnvironment(
  'CCB_MOBILE_TEST_PROFILE_SEED',
);

GatewayPairedHost? debugPairedHostFromEnvironment({
  bool debugMode = kDebugMode,
  bool allowProfileTestSeed = testProfileSeedEnabled,
  String encoded = debugPairedHostBase64,
}) {
  if ((!debugMode && !allowProfileTestSeed) || encoded.trim().isEmpty) {
    return null;
  }
  final decodedText = utf8.decode(base64Url.decode(_paddedBase64Url(encoded)));
  final decodedJson = jsonDecode(decodedText);
  if (decodedJson is! Map) {
    throw const FormatException('debug paired host payload must be a JSON map');
  }
  return GatewayPairedHost.fromSecureJson({
    for (final entry in decodedJson.entries) entry.key.toString(): entry.value,
  });
}

String _paddedBase64Url(String value) {
  final trimmed = value.trim();
  final remainder = trimmed.length % 4;
  return switch (remainder) {
    0 => trimmed,
    2 => '$trimmed==',
    3 => '$trimmed=',
    _ => throw const FormatException('invalid base64url debug profile'),
  };
}
