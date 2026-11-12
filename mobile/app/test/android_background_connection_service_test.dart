import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('Android background connection uses an explicit remote messaging FGS', () {
    final manifest =
        File('android/app/src/main/AndroidManifest.xml').readAsStringSync();
    final activity =
        File(
          'android/app/src/main/kotlin/io/ccb/mobile/ccb_mobile/MainActivity.kt',
        ).readAsStringSync();
    final service =
        File(
          'android/app/src/main/kotlin/io/ccb/mobile/ccb_mobile/'
          'BackgroundConnectionService.kt',
        ).readAsStringSync();

    expect(manifest, contains('android.permission.FOREGROUND_SERVICE'));
    expect(manifest, contains('android.permission.WAKE_LOCK'));
    expect(
      manifest,
      contains('android.permission.FOREGROUND_SERVICE_REMOTE_MESSAGING'),
    );
    expect(
      manifest,
      contains('android:foregroundServiceType="remoteMessaging"'),
    );
    expect(manifest, contains('android:exported="false"'));
    expect(activity, contains('io.ccb.mobile/background_connection'));
    expect(activity, contains('isBackgroundRestricted'));
    expect(activity, contains('isIgnoringBatteryOptimizations'));
    expect(activity, contains('isLowPowerStandbyEnabled'));
    expect(activity, contains('ACTION_APPLICATION_DETAILS_SETTINGS'));
    expect(service, contains('startForeground('));
    expect(service, contains('START_NOT_STICKY'));
    expect(service, contains('.setOngoing(true)'));
    expect(service, contains('PowerManager.PARTIAL_WAKE_LOCK'));
    expect(service, contains('Intent.ACTION_SCREEN_OFF'));
    expect(service, contains('Intent.ACTION_SCREEN_ON'));
    expect(service, contains('lock.release()'));
  });
}
