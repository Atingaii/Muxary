import 'package:ccb_mobile/ccb_mobile.dart';
import 'package:test/test.dart';

void main() {
  test('attach command is socket-aware', () {
    final builder = TmuxCommandBuilder(
      socketPath: '/tmp/ccb-demo/tmux.sock',
      sessionName: 'ccb-demo',
    );

    expect(builder.attachSession(), [
      'tmux',
      '-S',
      '/tmp/ccb-demo/tmux.sock',
      'attach-session',
      '-t',
      'ccb-demo',
    ]);
  });

  test('default tmux attach cannot be produced by builder', () {
    final builder = TmuxCommandBuilder(
      socketPath: '/tmp/ccb-demo/tmux.sock',
      sessionName: 'ccb-demo',
    );

    final command = TmuxCommandBuilder.shellCommand(builder.attachSession());

    expect(command, contains(' -S /tmp/ccb-demo/tmux.sock '));
    expect(command, isNot(equals('tmux attach')));
    expect(command, isNot(equals('tmux attach-session')));
  });

  test('builder can be created from direct terminal target evidence', () {
    final view = CcbProjectView.fromProjectViewPayload(demoProjectViewFixture);
    final builder = TmuxCommandBuilder.forTarget(
      view.terminalTargetForAgent('mobile'),
    );

    expect(builder.attachSession(), [
      'tmux',
      '-S',
      '/tmp/ccb-demo/tmux.sock',
      'attach-session',
      '-t',
      'ccb-demo',
    ]);
  });

  test('builder rejects terminal targets without direct tmux evidence', () {
    final target = CcbTerminalTarget.agent(
      projectId: 'proj-demo',
      namespaceEpoch: 4,
      agent: 'mobile',
      scopes: {CcbScope.view, CcbScope.terminalInput},
    );

    expect(() => TmuxCommandBuilder.forTarget(target), throwsStateError);
  });

  test('paste strategy keeps every tmux command socket-bound', () {
    final builder = TmuxCommandBuilder(
      socketPath: '/tmp/ccb-demo/tmux.sock',
      sessionName: 'ccb-demo',
    );

    final commands = builder.pasteViaBuffer(
      target: '%2',
      bufferName: 'ccb-mobile-1',
    );

    expect(commands, hasLength(3));
    for (final command in commands) {
      expect(command.take(3), ['tmux', '-S', '/tmp/ccb-demo/tmux.sock']);
    }
    expect(commands[1], containsAll(['paste-buffer', '-p', '-t', '%2']));
  });

  test('shell quoting preserves spaces in socket paths', () {
    final builder = TmuxCommandBuilder(
      socketPath: '/tmp/ccb demo/tmux.sock',
      sessionName: 'ccb-demo',
    );

    expect(
      TmuxCommandBuilder.shellCommand(builder.attachSession()),
      "tmux -S '/tmp/ccb demo/tmux.sock' attach-session -t ccb-demo",
    );
  });
}
