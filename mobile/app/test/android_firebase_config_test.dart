import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Firebase Android config is deployment injected and ignored', () {
    final settings = File('android/settings.gradle.kts').readAsStringSync();
    final buildScript = File('android/app/build.gradle.kts').readAsStringSync();
    final manifest =
        File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
    final ignore = File('android/.gitignore').readAsStringSync();

    expect(settings, contains('com.google.gms.google-services'));
    expect(settings, contains('apply false'));
    expect(buildScript, contains('CCB_MOBILE_FIREBASE_ANDROID_CONFIG'));
    expect(
      buildScript,
      contains('apply(plugin = "com.google.gms.google-services")'),
    );
    expect(manifest, contains('firebase_messaging_auto_init_enabled'));
    expect(manifest, contains('firebase_analytics_collection_enabled'));
    expect(
      manifest,
      contains('com.google.firebase.messaging.default_notification_channel_id'),
    );
    expect(ignore, contains('google-services.json'));
    expect(File('android/app/google-services.json').existsSync(), isFalse);
  });

  test('push background handler is registered after Flutter binding init', () {
    final mainSource = File('lib/main.dart').readAsStringSync();
    final bindingIndex = mainSource.indexOf(
      'WidgetsFlutterBinding.ensureInitialized()',
    );
    final handlerIndex = mainSource.indexOf(
      'registerPushNotificationBackgroundHandler()',
    );
    final runAppIndex = mainSource.indexOf('runApp(const CcbMobileApp())');

    expect(bindingIndex, greaterThanOrEqualTo(0));
    expect(handlerIndex, greaterThan(bindingIndex));
    expect(runAppIndex, greaterThan(handlerIndex));
  });
}
