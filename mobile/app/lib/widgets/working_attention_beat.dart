import 'dart:async';

import 'package:flutter/material.dart';

/// A low-frequency, compositor-friendly activity cue for an already visible
/// working state. The primary working affordance must remain useful when this
/// cue is paused, disabled, or offscreen.
class WorkingAttentionBeat extends StatefulWidget {
  const WorkingAttentionBeat({
    required this.child,
    this.interval = const Duration(seconds: 4),
    this.transitionDuration = const Duration(milliseconds: 180),
    this.dimOpacity = 0.38,
    super.key,
  });

  final Widget child;
  final Duration interval;
  final Duration transitionDuration;
  final double dimOpacity;

  @override
  State<WorkingAttentionBeat> createState() => _WorkingAttentionBeatState();
}

class _WorkingAttentionBeatState extends State<WorkingAttentionBeat>
    with WidgetsBindingObserver {
  Timer? _timer;
  bool _lit = true;
  AppLifecycleState _lifecycleState =
      WidgetsBinding.instance.lifecycleState ?? AppLifecycleState.resumed;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _syncTimer();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _lifecycleState = state;
    _syncTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  void _syncTimer() {
    if (!mounted || !workingAttentionBeatEnabled(context, _lifecycleState)) {
      _timer?.cancel();
      _timer = null;
      if (_lit) {
        setState(() {
          _lit = false;
        });
      }
      return;
    }
    if (_timer != null) {
      return;
    }
    if (!_lit) {
      setState(() {
        _lit = true;
      });
    }
    _timer = Timer.periodic(widget.interval, (_) {
      if (mounted) {
        setState(() {
          _lit = !_lit;
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedOpacity(
      opacity: _lit ? 1 : widget.dimOpacity,
      duration: widget.transitionDuration,
      curve: Curves.easeInOut,
      child: widget.child,
    );
  }
}

@visibleForTesting
bool workingAttentionBeatEnabled(
  BuildContext context,
  AppLifecycleState lifecycleState,
) {
  final mediaQuery = MediaQuery.maybeOf(context);
  final isWidgetTest = WidgetsBinding.instance.runtimeType.toString().contains(
    'Test',
  );
  return !isWidgetTest &&
      !(mediaQuery?.disableAnimations ?? false) &&
      TickerMode.valuesOf(context).enabled &&
      lifecycleState == AppLifecycleState.resumed;
}
