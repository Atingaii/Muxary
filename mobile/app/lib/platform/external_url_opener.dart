import 'package:flutter/services.dart';

const MethodChannel _channel = MethodChannel('io.ccb.mobile/external_url');

Future<bool> openExternalUrl(String url) async {
  final opened = await _channel.invokeMethod<bool>('openUrl', {'url': url});
  return opened ?? false;
}
