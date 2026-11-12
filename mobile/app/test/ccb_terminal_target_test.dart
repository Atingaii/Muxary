import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:test/test.dart';

void main() {
  test('pane id alone cannot authorize terminal input', () {
    final target = CcbTerminalTarget.paneEvidence(
      projectId: 'proj-demo',
      namespaceEpoch: 4,
      paneId: '%2',
      scopes: {CcbScope.terminalInput},
    );

    expect(target.canAcceptTerminalInput, isFalse);
  });

  test('agent target with terminal input scope is valid', () {
    final target = CcbTerminalTarget.agent(
      projectId: 'proj-demo',
      namespaceEpoch: 4,
      agent: 'mobile',
      window: 'main',
      paneId: '%2',
      scopes: {CcbScope.view, CcbScope.terminalInput},
    );

    expect(target.canAcceptTerminalInput, isTrue);
  });

  test('window active pane target with terminal input scope is valid', () {
    final target = CcbTerminalTarget.windowActivePane(
      projectId: 'proj-demo',
      namespaceEpoch: 4,
      window: 'main',
      scopes: {CcbScope.view, CcbScope.terminalInput},
    );

    expect(target.kind, CcbTerminalTargetKind.windowActivePane);
    expect(target.canAcceptTerminalInput, isTrue);
  });

  test('terminal input scope is required', () {
    final target = CcbTerminalTarget.agent(
      projectId: 'proj-demo',
      namespaceEpoch: 4,
      agent: 'mobile',
      scopes: {CcbScope.view},
    );

    expect(target.canAcceptTerminalInput, isFalse);
  });
}
