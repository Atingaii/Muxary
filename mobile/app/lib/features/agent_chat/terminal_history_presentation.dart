import 'package:flutter/material.dart';

import '../../models/readable_terminal_history.dart';

String terminalBlockText(ReadableTerminalBlock block) {
  return block.type == 'command' ? r'$ ' + block.text : block.text;
}

String historyScopeLabel(String scope) {
  return switch (scope) {
    'tmux_scrollback' => 'tmux scrollback',
    'terminal_journal' => 'terminal journal',
    'current_screen' => 'current screen',
    _ => scope,
  };
}

String terminalBlockLabel(String type) {
  return switch (type) {
    'command' => 'Command',
    'code' => 'Code',
    'diff' => 'Diff',
    'error' => 'Error',
    _ => 'Log',
  };
}

IconData terminalBlockIcon(String type) {
  return switch (type) {
    'command' => Icons.terminal,
    'code' => Icons.code,
    'diff' => Icons.difference,
    'error' => Icons.error_outline,
    _ => Icons.notes,
  };
}

Color terminalBlockColor(ColorScheme colorScheme, String type) {
  return switch (type) {
    'command' => colorScheme.primary,
    'code' => colorScheme.tertiary,
    'diff' => colorScheme.secondary,
    'error' => colorScheme.error,
    _ => colorScheme.outline,
  };
}

Color terminalBlockBackgroundColor(ColorScheme colorScheme, String type) {
  final accent = terminalBlockColor(colorScheme, type);
  final alpha = colorScheme.brightness == Brightness.dark ? 0.16 : 0.10;
  return accent.withValues(alpha: alpha);
}

TextStyle terminalBlockTextStyle({
  required TextTheme textTheme,
  required ColorScheme colorScheme,
  required String type,
}) {
  final base = textTheme.bodyMedium ?? const TextStyle();
  return base.copyWith(
    color: terminalBlockTextColor(colorScheme, type),
    fontFamily: type == 'log' ? null : 'monospace',
  );
}

Color terminalBlockTextColor(ColorScheme colorScheme, String type) {
  return switch (type) {
    'command' => colorScheme.primary,
    'code' => colorScheme.tertiary,
    'diff' => colorScheme.secondary,
    'error' => colorScheme.error,
    _ => colorScheme.onSurfaceVariant,
  };
}
