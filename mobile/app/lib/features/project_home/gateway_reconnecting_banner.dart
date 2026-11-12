import 'package:flutter/material.dart';

class GatewayReconnectingBanner extends StatelessWidget {
  const GatewayReconnectingBanner({
    required this.retryIn,
    required this.onRetry,
    required this.onDiagnostics,
    super.key,
  });

  final Duration? retryIn;
  final VoidCallback onRetry;
  final VoidCallback onDiagnostics;

  @override
  Widget build(BuildContext context) {
    final seconds = retryIn?.inSeconds;
    final label =
        seconds == null || seconds <= 0
            ? 'Reconnecting'
            : 'Reconnecting · retry in ${seconds}s';
    final colors = Theme.of(context).colorScheme;
    return Semantics(
      liveRegion: true,
      label: label,
      child: Material(
        key: const ValueKey('gateway-reconnecting-banner'),
        color: colors.surfaceContainerHigh,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(8),
          side: BorderSide(color: colors.outlineVariant),
        ),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
          child: Row(
            children: [
              const SizedBox(
                width: 16,
                height: 16,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
              const SizedBox(width: 8),
              Expanded(child: Text(label)),
              TextButton(onPressed: onRetry, child: const Text('Retry')),
              IconButton(
                tooltip: 'Diagnostics',
                onPressed: onDiagnostics,
                icon: const Icon(Icons.route_outlined),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
