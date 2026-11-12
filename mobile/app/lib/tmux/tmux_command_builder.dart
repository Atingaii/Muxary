import '../models/ccb_terminal_target.dart';

class TmuxCommandBuilder {
  TmuxCommandBuilder({required this.socketPath, required this.sessionName}) {
    if (socketPath.trim().isEmpty) {
      throw ArgumentError.value(socketPath, 'socketPath', 'required');
    }
    if (sessionName.trim().isEmpty) {
      throw ArgumentError.value(sessionName, 'sessionName', 'required');
    }
  }

  final String socketPath;
  final String sessionName;

  factory TmuxCommandBuilder.forTarget(CcbTerminalTarget target) {
    if (!target.hasDirectTmuxAttachEvidence) {
      throw StateError('tmux socket path and session name are required');
    }
    return TmuxCommandBuilder(
      socketPath: target.tmuxSocketPath!,
      sessionName: target.tmuxSessionName!,
    );
  }

  List<String> attachSession() {
    return [..._base, 'attach-session', '-t', sessionName];
  }

  List<String> capturePane({required String target, int lines = 120}) {
    _requireTarget(target);
    final safeLines = lines < 1 ? 1 : lines;
    return [..._base, 'capture-pane', '-p', '-t', target, '-S', '-$safeLines'];
  }

  List<List<String>> pasteViaBuffer({
    required String target,
    required String bufferName,
  }) {
    _requireTarget(target);
    _requireBuffer(bufferName);
    return [
      [..._base, 'load-buffer', '-b', bufferName, '-'],
      [..._base, 'paste-buffer', '-p', '-t', target, '-b', bufferName],
      [..._base, 'delete-buffer', '-b', bufferName],
    ];
  }

  List<String> selectWindow(String windowName) {
    _requireTarget(windowName);
    return [..._base, 'select-window', '-t', '$sessionName:$windowName'];
  }

  List<String> get _base => ['tmux', '-S', socketPath];

  static String shellCommand(List<String> command) {
    return command.map(shellQuote).join(' ');
  }

  static String shellQuote(String value) {
    if (value.isEmpty) {
      return "''";
    }
    final safe = RegExp(r'^[A-Za-z0-9_./:=@%+-]+$');
    if (safe.hasMatch(value)) {
      return value;
    }
    return "'${value.replaceAll("'", "'\"'\"'")}'";
  }
}

void _requireTarget(String target) {
  if (target.trim().isEmpty) {
    throw ArgumentError.value(target, 'target', 'required');
  }
}

void _requireBuffer(String bufferName) {
  if (bufferName.trim().isEmpty) {
    throw ArgumentError.value(bufferName, 'bufferName', 'required');
  }
}
