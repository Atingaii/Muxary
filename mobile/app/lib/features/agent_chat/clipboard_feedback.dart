import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void copyTextWithFeedback(BuildContext context, String text) {
  Clipboard.setData(ClipboardData(text: text));
  ScaffoldMessenger.of(
    context,
  ).showSnackBar(const SnackBar(content: Text('Copied')));
}
