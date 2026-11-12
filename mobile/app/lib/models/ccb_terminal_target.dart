import 'ccb_scope.dart';

enum CcbTerminalTargetKind {
  agent('agent'),
  windowActivePane('window_active_pane'),
  paneEvidence('pane_evidence');

  const CcbTerminalTargetKind(this.wireName);

  final String wireName;
}

class CcbTerminalTarget {
  const CcbTerminalTarget({
    required this.projectId,
    required this.namespaceEpoch,
    required this.kind,
    required this.scopes,
    this.agent,
    this.window,
    this.paneId,
    this.tmuxSocketPath,
    this.tmuxSessionName,
  });

  final String projectId;
  final int namespaceEpoch;
  final CcbTerminalTargetKind kind;
  final Set<CcbScope> scopes;
  final String? agent;
  final String? window;
  final String? paneId;
  final String? tmuxSocketPath;
  final String? tmuxSessionName;

  factory CcbTerminalTarget.agent({
    required String projectId,
    required int namespaceEpoch,
    required String agent,
    required Set<CcbScope> scopes,
    String? window,
    String? paneId,
    String? tmuxSocketPath,
    String? tmuxSessionName,
  }) {
    return CcbTerminalTarget(
      projectId: projectId,
      namespaceEpoch: namespaceEpoch,
      kind: CcbTerminalTargetKind.agent,
      agent: agent,
      window: window,
      paneId: paneId,
      tmuxSocketPath: tmuxSocketPath,
      tmuxSessionName: tmuxSessionName,
      scopes: scopes,
    );
  }

  factory CcbTerminalTarget.windowActivePane({
    required String projectId,
    required int namespaceEpoch,
    required String window,
    required Set<CcbScope> scopes,
    String? paneId,
    String? tmuxSocketPath,
    String? tmuxSessionName,
  }) {
    return CcbTerminalTarget(
      projectId: projectId,
      namespaceEpoch: namespaceEpoch,
      kind: CcbTerminalTargetKind.windowActivePane,
      window: window,
      paneId: paneId,
      tmuxSocketPath: tmuxSocketPath,
      tmuxSessionName: tmuxSessionName,
      scopes: scopes,
    );
  }

  factory CcbTerminalTarget.paneEvidence({
    required String projectId,
    required int namespaceEpoch,
    required String paneId,
    required Set<CcbScope> scopes,
    String? agent,
    String? window,
    String? tmuxSocketPath,
    String? tmuxSessionName,
  }) {
    return CcbTerminalTarget(
      projectId: projectId,
      namespaceEpoch: namespaceEpoch,
      kind: CcbTerminalTargetKind.paneEvidence,
      agent: agent,
      window: window,
      paneId: paneId,
      tmuxSocketPath: tmuxSocketPath,
      tmuxSessionName: tmuxSessionName,
      scopes: scopes,
    );
  }

  bool get hasStableIdentity {
    if (projectId.trim().isEmpty || namespaceEpoch < 0) {
      return false;
    }
    return switch (kind) {
      CcbTerminalTargetKind.agent => _hasText(agent),
      CcbTerminalTargetKind.windowActivePane => _hasText(window),
      CcbTerminalTargetKind.paneEvidence => _hasText(agent) || _hasText(window),
    };
  }

  bool get canAcceptTerminalInput {
    return hasStableIdentity && scopes.contains(CcbScope.terminalInput);
  }

  bool get hasDirectTmuxAttachEvidence {
    return _hasText(tmuxSocketPath) && _hasText(tmuxSessionName);
  }
}

bool _hasText(String? value) => value != null && value.trim().isNotEmpty;
