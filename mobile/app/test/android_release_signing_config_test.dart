import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('release signing never falls back to debug key', () {
    final script = File('android/app/build.gradle.kts').readAsStringSync();

    expect(script, isNot(contains('signingConfigs.getByName("debug")')));
    expect(script, contains('CCB_MOBILE_RELEASE_STORE_FILE'));
    expect(script, contains('CCB_MOBILE_RELEASE_STORE_PASSWORD'));
    expect(script, contains('CCB_MOBILE_RELEASE_KEY_ALIAS'));
    expect(script, contains('CCB_MOBILE_RELEASE_KEY_PASSWORD'));
    expect(script, contains('signed with the debug key'));
    expect(script, contains('release-signing.properties.example'));
  });

  test('local release signing material stays ignored', () {
    final ignore = File('android/.gitignore').readAsStringSync();
    final example =
        File('android/release-signing.properties.example').readAsStringSync();

    expect(ignore, contains('release-signing.properties'));
    expect(ignore, contains('**/*.jks'));
    expect(ignore, contains('**/*.keystore'));
    expect(example, contains('storeFile='));
    expect(example, contains('CCB_MOBILE_RELEASE_STORE_FILE'));
  });
}
