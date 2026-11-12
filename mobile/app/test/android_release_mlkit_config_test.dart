import 'dart:io';

import 'package:flutter_test/flutter_test.dart';

void main() {
  test('release build preserves reflectively loaded ML Kit registrars', () {
    final buildScript =
        File('android/app/build.gradle.kts').readAsStringSync();
    final rules = File('android/app/proguard-rules.pro').readAsStringSync();

    expect(buildScript, contains('"proguard-rules.pro"'));
    expect(
      rules,
      contains(
        '-keep class com.google.mlkit.** implements '
        'com.google.firebase.components.ComponentRegistrar',
      ),
    );
    expect(rules, contains('<init>();'));
  });
}
