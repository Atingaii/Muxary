import 'dart:async';
import 'dart:typed_data';

import 'package:ccb_mobile/features/agent_chat/agent_pane_message_submitter.dart';
import 'package:ccb_mobile/features/agent_chat/pane_chat_controller.dart';
import 'package:ccb_mobile/models/ccb_agent.dart';
import 'package:ccb_mobile/models/ccb_conversation_item.dart';
import 'package:ccb_mobile/models/ccb_project.dart';
import 'package:ccb_mobile/models/ccb_project_view.dart';
import 'package:ccb_mobile/transport/http_gateway_transport.dart';
import 'package:ccb_mobile/transport/terminal_transport.dart';
import 'package:test/test.dart';

void main() {
  group('AgentPaneMessageSubmitter', () {
    test('sends through terminal transport and emits pane events', () async {
      final transport = _RecordingTerminalTransport();
      final events = <PaneChatEvent>[];
      final submitter = AgentPaneMessageSubmitter(onEvent: events.add);

      final outcome = await submitter.submit(
        transport: transport,
        agent: _leadAgent,
        message: _localMessage(),
        view: _view(4),
        refreshView: null,
      );
      transport.sessions.single.addOutput(' pane reply ');
      await pumpEventQueue();

      expect(outcome.replacement.state, CcbConversationDeliveryState.sent);
      expect(outcome.terminalHistoryView?.namespaceEpoch, 4);
      expect(transport.requests.single.target.namespaceEpoch, 4);
      expect(transport.sessions.single.pasted, ['hello pane']);
      expect(transport.sessions.single.written, [
        [13],
      ]);
      expect(events.single.kind, PaneChatEventKind.output);
      expect(events.single.body, 'pane reply');

      await submitter.closeSessions();
      expect(transport.sessions.single.closed, isTrue);
    });

    test(
      'returns failed replacement when terminal transport is missing',
      () async {
        final submitter = AgentPaneMessageSubmitter(onEvent: (_) {});

        final outcome = await submitter.submit(
          transport: null,
          agent: _leadAgent,
          message: _localMessage(),
          view: _view(4),
          refreshView: null,
        );

        expect(outcome.replacement.state, CcbConversationDeliveryState.failed);
        expect(outcome.terminalHistoryView, isNull);
      },
    );

    test('sends Tab key through existing pane session', () async {
      final transport = _RecordingTerminalTransport();
      final submitter = AgentPaneMessageSubmitter(onEvent: (_) {});

      final outcome = await submitter.sendKey(
        transport: transport,
        agent: _leadAgent,
        view: _view(4),
        refreshView: null,
        bytes: const [9],
      );

      expect(outcome.sent, isTrue);
      expect(transport.requests.single.target.namespaceEpoch, 4);
      expect(transport.sessions.single.pasted, isEmpty);
      expect(transport.sessions.single.written, [
        [9],
      ]);

      await submitter.closeSessions();
    });

    test(
      'types text then sends Tab key through existing pane session',
      () async {
        final transport = _RecordingTerminalTransport();
        final submitter = AgentPaneMessageSubmitter(onEvent: (_) {});

        final outcome = await submitter.sendTextThenKey(
          transport: transport,
          agent: _leadAgent,
          view: _view(4),
          refreshView: null,
          body: 'draft before tab',
          bytes: const [9],
        );

        expect(outcome.sent, isTrue);
        expect(transport.requests.single.target.namespaceEpoch, 4);
        expect(transport.sessions.single.pasted, ['draft before tab']);
        expect(transport.sessions.single.written, [
          [9],
        ]);

        await submitter.closeSessions();
      },
    );

    test(
      'does not replay pane input when opening terminal hits stale epoch',
      () async {
        final transport = _RecordingTerminalTransport(
          openResponses: [_staleEpochError(), null],
        );
        final submitter = AgentPaneMessageSubmitter(onEvent: (_) {});
        var refreshCount = 0;

        final outcome = await submitter.submit(
          transport: transport,
          agent: _leadAgent,
          message: _localMessage(),
          view: _view(4),
          refreshView: () async {
            refreshCount += 1;
            return _view(5);
          },
        );

        expect(outcome.replacement.state, CcbConversationDeliveryState.failed);
        expect(outcome.terminalHistoryView, isNull);
        expect(refreshCount, 0);
        expect(transport.requests, isEmpty);

        await submitter.closeSessions();
      },
    );

    test('does not retry after partial pane input may have happened', () async {
      final transport = _RecordingTerminalTransport(
        pasteError: const TerminalTransportException('paste failed'),
      );
      final submitter = AgentPaneMessageSubmitter(onEvent: (_) {});
      var refreshCount = 0;

      final outcome = await submitter.submit(
        transport: transport,
        agent: _leadAgent,
        message: _localMessage(),
        view: _view(4),
        refreshView: () async {
          refreshCount += 1;
          return _view(5);
        },
      );

      expect(
        outcome.replacement.state,
        CcbConversationDeliveryState.unconfirmed,
      );
      expect(outcome.terminalHistoryView, isNull);
      expect(refreshCount, 0);
      expect(transport.requests.single.target.namespaceEpoch, 4);

      await submitter.closeSessions();
    });

    test(
      'returns failed replacement when stale refresh cannot recover',
      () async {
        final transport = _RecordingTerminalTransport(
          openResponses: [_staleEpochError()],
        );
        final submitter = AgentPaneMessageSubmitter(onEvent: (_) {});

        final outcome = await submitter.submit(
          transport: transport,
          agent: _leadAgent,
          message: _localMessage(),
          view: _view(4),
          refreshView: () async => _view(5, agents: const []),
        );

        expect(outcome.replacement.state, CcbConversationDeliveryState.failed);
        expect(outcome.terminalHistoryView, isNull);
        expect(transport.requests, isEmpty);
      },
    );
  });
}

const _leadAgent = CcbAgent(
  name: 'lead',
  provider: 'codex',
  window: 'main',
  order: 0,
  active: true,
  queueDepth: 0,
  paneId: '%2',
);

CcbProjectView _view(int epoch, {List<CcbAgent> agents = const [_leadAgent]}) {
  return CcbProjectView(
    project: const CcbProject(
      id: 'proj',
      displayName: 'Project',
      root: '/repo',
    ),
    namespaceEpoch: epoch,
    tmuxSocketPath: null,
    tmuxSessionName: null,
    activeWindow: 'main',
    activePaneId: '%2',
    windows: const [],
    agents: agents,
    contentItems: const [],
    notifications: const [],
    terminalHistories: const {},
  );
}

CcbConversationItem _localMessage() {
  return CcbConversationItem.userMessage(
    id: 'local-lead-0',
    agentName: 'lead',
    body: 'hello pane',
  );
}

GatewayHttpException _staleEpochError() {
  return GatewayHttpException(
    Uri.parse('http://127.0.0.1/v1/projects/proj/terminal/open'),
    409,
    'stale namespace epoch',
  );
}

class _RecordingTerminalTransport implements TerminalTransport {
  _RecordingTerminalTransport({
    this.openResponses = const [null],
    this.pasteError,
  });

  final List<Object?> openResponses;
  final Object? pasteError;
  final requests = <TerminalOpenRequest>[];
  final sessions = <_RecordingTerminalSession>[];
  var _openIndex = 0;

  @override
  Future<TerminalSession> open(TerminalOpenRequest request) async {
    final response =
        _openIndex < openResponses.length ? openResponses[_openIndex] : null;
    _openIndex += 1;
    if (response is Exception) {
      throw response;
    }
    if (response is Error) {
      throw response;
    }
    requests.add(request);
    final session = _RecordingTerminalSession(
      request.attachCommand,
      pasteError: pasteError,
    );
    sessions.add(session);
    return session;
  }
}

class _RecordingTerminalSession implements TerminalSession {
  _RecordingTerminalSession(this.launchedCommand, {this.pasteError});

  final Object? pasteError;
  final StreamController<Uint8List> _output = StreamController.broadcast();
  final pasted = <String>[];
  final written = <List<int>>[];
  var closed = false;

  @override
  final String launchedCommand;

  @override
  Stream<Uint8List> get output => _output.stream;

  @override
  Future<void> close() async {
    closed = true;
    await _output.close();
  }

  @override
  Future<void> paste(String text) async {
    final error = pasteError;
    if (error != null) {
      throw error;
    }
    pasted.add(text);
  }

  @override
  Future<void> reconnect() async {}

  @override
  Future<void> resize(TerminalGeometry geometry) async {}

  @override
  Future<void> writeBytes(List<int> bytes) async {
    written.add(bytes);
  }

  void addOutput(String text) {
    _output.add(Uint8List.fromList(text.codeUnits));
  }
}
