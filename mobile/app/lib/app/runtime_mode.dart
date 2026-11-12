import 'package:flutter/material.dart';

enum AppRuntimeMode {
  fake('Fake', Icons.layers_clear),
  pairedGateway('Paired', Icons.mobile_friendly);

  const AppRuntimeMode(this.label, this.icon);

  final String label;
  final IconData icon;
}
