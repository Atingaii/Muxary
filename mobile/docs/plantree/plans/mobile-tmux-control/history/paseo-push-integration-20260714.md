# Paseo-Inspired Push Integration Evidence - 2026-07-14

Branch: `integration/mobile-paseo-reliability-d4032749`
Base: `d4032749`

Scope: device-bound Push gateway, FlutterFire FCM opt-in runtime, route-only
completion payload contract, and blocked-device evidence audit.

## Dependency Gate

- Need: official Firebase Cloud Messaging client support for Android token
  acquisition, refresh, and notification click routing.
- Package change: `firebase_messaging 16.4.1`, `firebase_core 4.11.0`,
  pinned in `mobile/app/pubspec.lock`.
- License/publisher: FlutterFire packages, publisher `firebase.google.com`,
  BSD-3-Clause on pub.dev.
- Latest-attempt result: pub.dev listed `firebase_messaging 16.4.2` and
  `firebase_core 4.12.0` on 2026-07-14, but that pair failed the compile gate
  because `firebase_messaging` could not resolve `FirebasePlugin` /
  `pluginConstants`; the integration keeps the latest build-passing official
  pins.
- Credentials: no `google-services.json`, `firebase_options.dart`, service
  account, sender credential, or release key material is committed.

## Verification

- Gateway focused:
  `PYTHONPATH=lib python -m pytest test/test_mobile_gateway_notifications.py test/test_mobile_gateway_service.py -q`
  -> `105 passed in 5.26s`.
- Source full:
  `PYTHONPATH=lib python -m pytest test -q --tb=short -m "not provider_blackbox"`
  -> `3644 passed, 2 skipped, 21 deselected in 436.08s`.
- Flutter focused:
  `flutter test test/push_notifications_test.dart` -> `7 passed` after
  reviewer fix `rep_f6ee21cbee77`.
- Flutter focused analyze:
  `flutter analyze lib/notifications/push_notifications.dart test/push_notifications_test.dart`
  -> no issues.
- Flutter full:
  `flutter analyze && flutter test` -> analyze clean, `632` tests passed
  after reviewer fix `rep_f6ee21cbee77`.
- Diff check: `git diff --check` -> clean.
- Android debug build:
  `flutter build apk --debug` -> built
  `build/app/outputs/flutter-apk/app-debug.apk`.
- Android profile build:
  `flutter build apk --profile --dart-define=CCB_MOBILE_PUSH_ENABLED=true`
  -> built `build/app/outputs/flutter-apk/app-profile.apk`.
- Android release build:
  `flutter build apk --release --dart-define=CCB_MOBILE_PUSH_ENABLED=true`
  -> built `build/app/outputs/flutter-apk/app-release.apk`.

## APK Evidence

- Version: package `io.ccb.mobile.ccb_mobile`, versionName `8.1.4`,
  versionCode `8010004`, compileSdk `36`, targetSdk `36`.
- Manifest permissions include `android.permission.POST_NOTIFICATIONS`,
  `INTERNET`, `WAKE_LOCK`, and `ACCESS_NETWORK_STATE`.
- Debug APK: SHA-256
  `69aa1059ab8ff41fd126a3d655a24a00357c206afd09ce462333c31909a7bb9c`,
  size `207M`, signer SHA-256
  `65fd14a21ac4fb058f411f6082b11bf83702c9aca58e428c4ab80379b477b901`
  (`C=US, O=Android, CN=Android Debug`).
- Profile APK: SHA-256
  `0e3d0f3394da3c1721c273a8d00d39d02f478b3c3c07a1f84794eae1d44a4c40`,
  size `118M`, signer SHA-256
  `65fd14a21ac4fb058f411f6082b11bf83702c9aca58e428c4ab80379b477b901`
  (`C=US, O=Android, CN=Android Debug`).
- Release APK: SHA-256
  `0c6a70616e339f53c248facd1dd2c07589667ec069d0b7e708ef46b58bba3cfb`,
  size `72M`, signer SHA-256
  `5a30b9b9fcb0882232b1e1f3896c2420b1f67b1e39ba325ca3a8dafe2d2d1697`
  (`CN=CCB Mobile, OU=Release, O=CCB, L=San Francisco, ST=California, C=US`).
- Release signing source: ignored local
  `mobile/app/android/release-signing.properties` was present; release signing
  environment variables were unset. The file contents were not read or
  committed.

## Blocked Evidence

- Emulator/physical device: BLOCKED. `/home/bfly/.local/share/android-sdk/platform-tools/adb devices -l`
  reported no attached devices.
- Physical Android phone: BLOCKED. No online physical device was available.
- Real Firebase operator credentials: BLOCKED. `GOOGLE_APPLICATION_CREDENTIALS`,
  `FIREBASE_CONFIG`, `FIREBASE_PROJECT_ID`,
  `CCB_MOBILE_FIREBASE_CREDENTIALS`, and
  `CCB_MOBILE_FCM_SENDER_CREDENTIALS` were unset.
- Real completion Push delivery, lockscreen, Doze, process-kill, gateway
  restart, network recovery, Push+SSE device dedupe, permission-denied device
  behavior, multi-device isolation on hardware, screenshots, logcat, gateway
  audit log, push delivery receipt, and device request-count evidence:
  BLOCKED by the missing device and Firebase prerequisites.
- Force-stop remains NOT GUARANTEED by FCM and is not claimed.

## Acceptance Notes

- Gateway unit tests cover notify-scope authorization, route-only payload
  fields, per-device visible-target suppression, invalid-token cleanup,
  revoke cleanup, timeout bounding, and device isolation.
- App unit tests cover complete route parsing, permission denial fail-closed,
  absent native Firebase config fail-closed, token refresh binding, canonical
  `PUT /v1/devices/me/push-token`, cross-device route rejection, push-open
  `dedupe_key` marking before cursor catch-up, ambiguous identity-free route
  rejection, and `DELETE /v1/devices/me/push-token` when switching away from a
  registered profile.
- Production Android background evidence requires the deployment sender to send
  a real FCM notification+data message with only the canonical route fields in
  the data payload. Data-only background delivery is not accepted as production
  evidence for user-visible notifications.
- Foreground service remains intentionally unimplemented: no policy-compliant
  active-terminal or large-transfer native owner exists in this package.
