import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:ccb_mobile/models/ccb_agent_conversation.dart';
import 'package:ccb_mobile/models/ccb_project.dart';
import 'package:ccb_mobile/models/ccb_project_lifecycle.dart';
import 'package:ccb_mobile/models/ccb_project_view.dart';
import 'package:ccb_mobile/models/ccb_scope.dart';
import 'package:ccb_mobile/models/ccb_terminal_target.dart';
import 'package:ccb_mobile/models/readable_terminal_history.dart';
import 'package:ccb_mobile/transport/gateway_terminal_transport.dart';
import 'package:ccb_mobile/transport/gateway_transport.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:ccb_mobile/transport/terminal_transport.dart';

Future<void> main() async {
  try {
    final result = await _runSmoke().timeout(const Duration(seconds: 8));
    stdout.writeln(const JsonEncoder.withIndent('  ').convert(result));
    exitCode = 0;
  } catch (error, stackTrace) {
    stderr.writeln(error);
    stderr.writeln(stackTrace);
    stdout.writeln(
      const JsonEncoder.withIndent(
        '  ',
      ).convert({'status': 'error', 'error': error.toString()}),
    );
    exitCode = 1;
  }
}

Future<Map<String, Object?>> _runSmoke() async {
  final gateway = _RenewalGatewayTransport();
  final transport = GatewayTerminalTransport(transport: gateway);
  final session = await transport.open(
    TerminalOpenRequest.gateway(
      target: CcbTerminalTarget.agent(
        projectId: 'proj-renewal-smoke',
        namespaceEpoch: 7,
        agent: 'mobile_probe',
        window: 'main',
        paneId: '%2',
        scopes: const {CcbScope.view, CcbScope.terminalInput},
      ),
      geometry: const TerminalGeometry(
        columns: 100,
        rows: 30,
        pixelWidth: 960,
        pixelHeight: 640,
      ),
    ),
  );
  final output = <String>[];
  final errors = <Object>[];
  final subscription = session.output
      .map(utf8.decode)
      .listen(output.add, onError: errors.add);
  var closeCompleted = false;
  try {
    gateway.emit(
      GatewayTerminalFrame.output(
        sequence: 11,
        bytes: utf8.encode('before-expiry'),
      ),
    );
    await _waitFor(
      () => output.contains('before-expiry'),
      description: 'initial output',
    );

    await session.resize(
      const TerminalGeometry(
        columns: 132,
        rows: 43,
        pixelWidth: 1000,
        pixelHeight: 700,
      ),
    );
    gateway.emit(GatewayTerminalFrame.error('expired'));
    await _waitFor(
      () =>
          gateway.openRequests.length == 2 && gateway.resumeCursors.length == 2,
      description: 'renewed terminal handle',
    );

    gateway.emit(
      GatewayTerminalFrame.output(
        sequence: 12,
        bytes: utf8.encode('after-renewal'),
      ),
    );
    await _waitFor(
      () => output.contains('after-renewal'),
      description: 'post-renewal output',
    );

    await session.writeBytes(utf8.encode('after-renewal-input'));
    await session.paste('after-renewal-paste');
    await session.close();
    closeCompleted = true;
  } finally {
    await subscription.cancel();
    if (!closeCompleted) {
      await session.close().catchError((_) {});
    }
  }

  if (errors.isNotEmpty) {
    throw StateError('renewal smoke saw output errors: $errors');
  }
  final renewalRequest = gateway.openRequests.last;
  final postRenewalInput = gateway.sentFrames.any(
    (entry) =>
        entry.terminalId == 'term_renewal_2' &&
        entry.frame.type == GatewayTerminalFrameType.input,
  );
  final postRenewalPaste = gateway.sentFrames.any(
    (entry) =>
        entry.terminalId == 'term_renewal_2' &&
        entry.frame.type == GatewayTerminalFrameType.paste,
  );
  if (!postRenewalInput || !postRenewalPaste) {
    throw StateError('post-renewal input/paste did not use renewed handle');
  }

  return {
    'status': 'ok',
    'renewal_completed': true,
    'open_count': gateway.openRequests.length,
    'resume_cursors': gateway.resumeCursors,
    'first_terminal_id': 'term_renewal_1',
    'renewed_terminal_id': 'term_renewal_2',
    'renewal_geometry': {
      'columns': renewalRequest.geometry.columns,
      'rows': renewalRequest.geometry.rows,
      'pixel_width': renewalRequest.geometry.pixelWidth,
      'pixel_height': renewalRequest.geometry.pixelHeight,
    },
    'output': output,
    'output_error_count': errors.length,
    'post_renewal_input_sent': postRenewalInput,
    'post_renewal_paste_sent': postRenewalPaste,
    'close_completed': closeCompleted,
  };
}

class _RenewalGatewayTransport implements GatewayTransport {
  @override
  Future<GatewayFileUploadResult> uploadFile({
    required String projectId,
    required String agentName,
    required String fileName,
    required String mimeType,
    required List<int> bytes,
  }) => throw UnimplementedError();

  @override
  Future<List<int>> downloadFile({
    required String projectId,
    required String agentName,
    required String fileId,
  }) => throw UnimplementedError();

  final openRequests = <GatewayTerminalOpenRequest>[];
  final resumeCursors = <int?>[];
  final sentFrames = <_SentFrame>[];
  final _frames = StreamController<GatewayTerminalFrame>.broadcast();

  @override
  final GatewayHostProfile profile = GatewayHostProfile(
    hostId: 'host-renewal-smoke',
    deviceId: 'device-renewal-smoke',
    routeProvider: RouteProvider(
      kind: RouteProviderKind.lan,
      gatewayUrl: Uri.parse('http://127.0.0.1:8787'),
    ),
    scopes: const {'view', 'focus', 'terminal_input'},
  );

  void emit(GatewayTerminalFrame frame) {
    _frames.add(frame);
  }

  @override
  Future<GatewayTerminalHandle> openTerminal(
    GatewayTerminalOpenRequest request,
  ) async {
    final sequence = openRequests.length + 1;
    openRequests.add(request);
    return GatewayTerminalHandle(
      terminalId: 'term_renewal_$sequence',
      terminalToken: 'terminal-token-$sequence',
      expiresAt: DateTime.utc(2026, 6, 21, 0, 5),
      websocketUrl: Uri.parse(
        'ws://127.0.0.1:8787/v1/terminals/term_renewal_$sequence',
      ),
      targetEpoch: request.target.namespaceEpoch,
      targetSummary: GatewayTerminalTargetSummary(
        projectId: request.target.projectId,
        agent: request.target.agent,
        window: request.target.window,
      ),
    );
  }

  @override
  Stream<GatewayTerminalFrame> terminalFrames(
    GatewayTerminalHandle handle, {
    int? resumeCursor,
  }) {
    resumeCursors.add(resumeCursor);
    return _frames.stream;
  }

  @override
  Future<void> sendTerminalFrame(
    GatewayTerminalHandle handle,
    GatewayTerminalFrame frame,
  ) async {
    sentFrames.add(_SentFrame(handle.terminalId, frame));
  }

  @override
  Future<GatewayDevice> device() {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectView> focusAgent({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectView> focusWindow({
    required String projectId,
    required String window,
    required int namespaceEpoch,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectView> getProjectView(String projectId) {
    throw UnimplementedError();
  }

  @override
  Future<ReadableTerminalHistory?> getReadableTerminalHistory({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int maxLines = 200,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<CcbAgentConversation> getAgentConversation({
    required String projectId,
    required String agent,
    required int namespaceEpoch,
    int limit = 50,
    String? cursor,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<CcbAgentMessageSubmitResult> submitAgentMessage(
    CcbAgentMessageSubmitRequest request,
  ) {
    throw UnimplementedError();
  }

  @override
  Future<CcbProjectLifecycleResult> requestLifecycle({
    required String projectId,
    required CcbLifecycleAction action,
  }) {
    throw UnimplementedError();
  }

  @override
  Future<GatewayHealth> health() {
    throw UnimplementedError();
  }

  @override
  Future<List<CcbProject>> listProjects() {
    throw UnimplementedError();
  }
}

class _SentFrame {
  const _SentFrame(this.terminalId, this.frame);

  final String terminalId;
  final GatewayTerminalFrame frame;
}

Future<void> _waitFor(
  bool Function() predicate, {
  required String description,
  Duration timeout = const Duration(seconds: 2),
}) async {
  final deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    if (predicate()) {
      return;
    }
    await Future<void>.delayed(const Duration(milliseconds: 10));
  }
  throw TimeoutException('timed out waiting for $description', timeout);
}
