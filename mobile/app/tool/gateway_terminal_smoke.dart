import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:ccb_mobile/models/ccb_agent.dart';
import 'package:ccb_mobile/models/ccb_scope.dart';
import 'package:ccb_mobile/models/ccb_terminal_target.dart';
import 'package:ccb_mobile/repository/gateway_mobile_ccb_repository.dart';
import 'package:ccb_mobile/transport/gateway_route_diagnostics.dart';
import 'package:ccb_mobile/transport/gateway_terminal_transport.dart';
import 'package:ccb_mobile/transport/http_gateway_transport.dart';
import 'package:ccb_mobile/transport/route_provider.dart';
import 'package:ccb_mobile/transport/terminal_transport.dart';

Future<void> main() async {
  try {
    final result = await _runSmoke().timeout(const Duration(seconds: 45));
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
  final env = Platform.environment;
  final gatewayUrl = _requiredUri(env, 'CCB_MOBILE_GATEWAY_URL');
  final pairingCode = _required(env, 'CCB_MOBILE_PAIRING_CODE');
  final deviceName =
      _optional(env, 'CCB_MOBILE_DEVICE_NAME') ?? 'Gateway Smoke';
  final requestedAgent = _optional(env, 'CCB_MOBILE_AGENT');
  final expectedRouteProvider = _optionalRouteProvider(
    env,
    'CCB_MOBILE_ROUTE_PROVIDER',
  );
  final dnsOverride = _optionalDnsOverride(env, 'CCB_MOBILE_DNS_OVERRIDE');
  final timeout = Duration(
    seconds: int.tryParse(env['CCB_MOBILE_TIMEOUT_SECONDS'] ?? '') ?? 12,
  );
  final historyMaxLines =
      int.tryParse(env['CCB_MOBILE_HISTORY_MAX_LINES'] ?? '') ?? 240;
  if (historyMaxLines < 1) {
    throw ArgumentError.value(
      env['CCB_MOBILE_HISTORY_MAX_LINES'],
      'CCB_MOBILE_HISTORY_MAX_LINES',
      'positive integer required',
    );
  }

  final httpClient = _httpClientForDnsOverride(dnsOverride);
  HttpGatewayTransport? httpTransport;
  late _ClaimedGateway claimed;
  TerminalSession? session;
  StreamSubscription<List<int>>? outputSubscription;
  final outputBytes = <int>[];
  final outputErrors = <Object>[];
  var outputDone = false;
  var reconnectCompleted = false;
  var closeCompleted = false;
  var closeTimedOut = false;

  try {
    claimed = await _claimPairing(
      gatewayUrl: gatewayUrl,
      pairingCode: pairingCode,
      deviceName: deviceName,
      timeout: timeout,
      httpClient: httpClient,
    );
    httpTransport = HttpGatewayTransport(
      profile: claimed.profile,
      deviceToken: claimed.deviceToken,
      httpClient: httpClient,
      timeout: timeout,
    );
    final repository = GatewayMobileCcbRepository(transport: httpTransport);
    if (expectedRouteProvider != null &&
        claimed.profile.routeProvider.kind != expectedRouteProvider) {
      throw StateError(
        'paired route provider ${claimed.profile.routeProvider.kind.wireName} '
        'did not match expected ${expectedRouteProvider.wireName}',
      );
    }
    final diagnostics = await GatewayRouteDiagnostics(
      transport: httpTransport,
    ).check(projectId: claimed.projectId).timeout(timeout);
    if (!diagnostics.ready) {
      throw StateError(
        'gateway route diagnostics failed: ${diagnostics.summary}',
      );
    }
    final health = await httpTransport.health().timeout(timeout);
    final projects = await repository.listProjects().timeout(timeout);
    if (projects.isEmpty) {
      throw StateError('gateway returned no projects');
    }
    final projectId = claimed.projectId ?? projects.single.id;
    final view = await repository.getProjectView(projectId).timeout(timeout);
    final agent = _selectAgent(view.agents, requestedAgent);
    final focusedView = await repository
        .focusAgent(
          projectId: projectId,
          agent: agent.name,
          namespaceEpoch: _requiredEpoch(view.namespaceEpoch),
        )
        .timeout(timeout);
    final focusedEpoch = _requiredEpoch(focusedView.namespaceEpoch);
    final selectedContentCount = focusedView.contentForAgent(agent.name).length;
    final embeddedHistory = focusedView.terminalHistoryForAgent(agent.name);
    final terminalHistory = await repository
        .getReadableTerminalHistory(
          projectId: projectId,
          agent: agent.name,
          namespaceEpoch: focusedEpoch,
          maxLines: historyMaxLines,
        )
        .timeout(timeout);
    if (terminalHistory == null) {
      throw StateError('gateway terminal history route returned no history');
    }
    if (terminalHistory.agentName != agent.name) {
      throw StateError(
        'gateway terminal history agent ${terminalHistory.agentName} '
        'did not match selected agent ${agent.name}',
      );
    }
    if (terminalHistory.historyScope.trim().isEmpty) {
      throw StateError('gateway terminal history missing history scope');
    }
    if (!_hasText(terminalHistory.sourcePaneId)) {
      throw StateError('gateway terminal history missing source pane id');
    }
    if (terminalHistory.stale) {
      throw StateError('gateway terminal history unexpectedly stale');
    }
    final target =
        focusedView
            .terminalTargetForAgent(
              agent.name,
              scopes: const {CcbScope.view, CcbScope.terminalInput},
            )
            .withoutDirectTmuxEvidence();
    if (target.hasDirectTmuxAttachEvidence) {
      throw StateError('gateway smoke target unexpectedly has tmux evidence');
    }

    session = await GatewayTerminalTransport(transport: httpTransport)
        .open(
          TerminalOpenRequest.gateway(
            target: target,
            geometry: const TerminalGeometry(
              columns: 100,
              rows: 30,
              pixelWidth: 960,
              pixelHeight: 640,
            ),
          ),
        )
        .timeout(timeout);
    if (expectedRouteProvider == RouteProviderKind.cloudflareTunnel &&
        !session.launchedCommand.startsWith('gateway terminal stream')) {
      throw StateError('unexpected gateway terminal launch command');
    }
    outputSubscription = session.output.listen(
      (bytes) {
        if (outputBytes.length < 8192) {
          outputBytes.addAll(bytes.take(8192 - outputBytes.length));
        }
      },
      onError: outputErrors.add,
      onDone: () {
        outputDone = true;
      },
    );

    await _waitFor(
      timeout: timeout,
      outputErrors: outputErrors,
      isDone: () => outputDone,
      predicate: () => outputBytes.isNotEmpty,
      description: 'initial gateway terminal output',
    );
    await session
        .writeBytes(
          utf8.encode('\u0002:display-message ccb-mobile-gateway-input\r'),
        )
        .timeout(timeout);
    await session
        .paste('\u0002:display-message ccb-mobile-gateway-paste\r')
        .timeout(timeout);
    await session
        .resize(
          const TerminalGeometry(
            columns: 120,
            rows: 36,
            pixelWidth: 1200,
            pixelHeight: 720,
          ),
        )
        .timeout(timeout);
    await Future<void>.delayed(const Duration(milliseconds: 500));
    _throwFirstOutputError(outputErrors);
    await session.reconnect().timeout(timeout);
    reconnectCompleted = true;
    try {
      await session.close().timeout(const Duration(seconds: 3));
      closeCompleted = true;
    } on TimeoutException {
      closeTimedOut = true;
    }
    await outputSubscription.cancel();
    outputSubscription = null;

    if (outputBytes.isEmpty) {
      throw StateError('gateway terminal smoke saw no output bytes');
    }
    return {
      'status': 'ok',
      'gateway_url': gatewayUrl.toString(),
      'dns_override': dnsOverride?.toJson(),
      'health_status': health.status,
      'health_capabilities': health.capabilities.toList()..sort(),
      'route_provider': claimed.profile.routeProvider.kind.wireName,
      'route_diagnostics_ready': diagnostics.ready,
      'route_diagnostics_checks':
          diagnostics.checks
              .map((check) => {'code': check.code, 'ok': check.ok})
              .toList(),
      'project_id': projectId,
      'project_count': projects.length,
      'agent': agent.name,
      'agent_window': agent.window,
      'selected_agent_content_count': selectedContentCount,
      'selected_agent_embedded_history_blocks':
          embeddedHistory?.blocks.length ?? 0,
      'terminal_history_loaded': true,
      'terminal_history_scope': terminalHistory.historyScope,
      'terminal_history_source_pane_id': terminalHistory.sourcePaneId,
      'terminal_history_generated_at': terminalHistory.generatedAt,
      'terminal_history_stale': terminalHistory.stale,
      'terminal_history_max_lines': historyMaxLines,
      'terminal_history_blocks': terminalHistory.blocks.length,
      'terminal_history_first_block_type':
          terminalHistory.blocks.isEmpty
              ? null
              : terminalHistory.blocks.first.type,
      'namespace_epoch': target.namespaceEpoch,
      'launched_command': session.launchedCommand,
      'target_has_direct_tmux_evidence': target.hasDirectTmuxAttachEvidence,
      'output_bytes_seen': outputBytes.length,
      'input_sent': true,
      'paste_sent': true,
      'resize_sent': true,
      'close_completed': closeCompleted,
      'close_timed_out': closeTimedOut,
      'reconnect_completed': reconnectCompleted,
      'device_id': claimed.profile.deviceId,
      'host_id': claimed.profile.hostId,
      'scopes': claimed.profile.scopes.toList()..sort(),
    };
  } finally {
    if (outputSubscription != null) {
      await outputSubscription.cancel();
    }
    if (session != null && !closeCompleted && !closeTimedOut) {
      try {
        await session.close().timeout(const Duration(seconds: 2));
      } catch (_) {
        // Best-effort cleanup after a failed smoke.
      }
    }
    if (httpTransport != null) {
      httpTransport.close(force: true);
    } else {
      httpClient.close(force: true);
    }
  }
}

Future<_ClaimedGateway> _claimPairing({
  required Uri gatewayUrl,
  required String pairingCode,
  required String deviceName,
  required Duration timeout,
  required HttpClient httpClient,
}) async {
  final claimEndpoint = gatewayUrl.resolve('/v1/pairing/claim');
  final json = await _postJson(
    claimEndpoint,
    {'pairing_code': pairingCode, 'device_name': deviceName},
    timeout: timeout,
    httpClient: httpClient,
  );
  final hostProfile = _map(json['host_profile']);
  final device = _map(json['device']);
  final projectId =
      _optionalText(hostProfile['project_id']) ??
      _optionalText(device['project_id']);
  final hostId =
      _optionalText(hostProfile['host_id']) ??
      projectId ??
      _requiredText(device['project_id'], 'device.project_id');
  final deviceId =
      _optionalText(hostProfile['device_id']) ??
      _requiredText(device['device_id'], 'device.device_id');
  final profile = GatewayHostProfile(
    hostId: hostId,
    deviceId: deviceId,
    routeProvider: RouteProvider(
      kind: RouteProviderKind.fromWireName(
        _optionalText(hostProfile['route_provider']) ??
            RouteProviderKind.lan.wireName,
      ),
      gatewayUrl: _optionalUri(hostProfile['gateway_url']) ?? gatewayUrl,
      websocketUrl: _optionalUri(hostProfile['websocket_url']),
      hostFingerprint: _optionalText(hostProfile['server_fingerprint']),
      capabilities: _stringSet(hostProfile['capabilities']),
      diagnostics: _stringMap(hostProfile['diagnostics']),
    ),
    scopes: _stringSet(hostProfile['scopes']),
  );
  return _ClaimedGateway(
    profile: profile,
    deviceToken: _requiredText(json['device_token'], 'device_token'),
    projectId: projectId,
  );
}

Future<Map<String, Object?>> _postJson(
  Uri uri,
  Map<String, Object?> payload, {
  required Duration timeout,
  required HttpClient httpClient,
}) async {
  final request = await httpClient.postUrl(uri).timeout(timeout);
  request.headers.set(HttpHeaders.acceptHeader, 'application/json');
  request.headers.contentType = ContentType.json;
  final bodyBytes = utf8.encode(jsonEncode(payload));
  request.contentLength = bodyBytes.length;
  request.add(bodyBytes);
  final response = await request.close().timeout(timeout);
  final body = await utf8.decodeStream(response).timeout(timeout);
  if (response.statusCode < 200 || response.statusCode >= 300) {
    throw HttpException(
      'pairing claim failed: HTTP ${response.statusCode} $body',
      uri: uri,
    );
  }
  final decoded = jsonDecode(body);
  if (decoded is Map) {
    return {
      for (final entry in decoded.entries) entry.key.toString(): entry.value,
    };
  }
  throw FormatException('pairing claim response is not a JSON object: $uri');
}

CcbAgent _selectAgent(List<CcbAgent> agents, String? requestedAgent) {
  if (agents.isEmpty) {
    throw StateError('ProjectView contains no agents');
  }
  if (_hasText(requestedAgent)) {
    return agents.firstWhere(
      (agent) => agent.name == requestedAgent,
      orElse:
          () =>
              throw ArgumentError.value(
                requestedAgent,
                'CCB_MOBILE_AGENT',
                'unknown agent',
              ),
    );
  }
  return agents.firstWhere((agent) => agent.active, orElse: () => agents.first);
}

int _requiredEpoch(int? value) {
  if (value == null) {
    throw StateError('ProjectView namespace epoch is required');
  }
  return value;
}

Future<void> _waitFor({
  required Duration timeout,
  required List<Object> outputErrors,
  required bool Function() isDone,
  required bool Function() predicate,
  required String description,
}) async {
  final deadline = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(deadline)) {
    _throwFirstOutputError(outputErrors);
    if (predicate()) {
      return;
    }
    if (isDone()) {
      break;
    }
    await Future<void>.delayed(const Duration(milliseconds: 50));
  }
  _throwFirstOutputError(outputErrors);
  throw TimeoutException('timed out waiting for $description', timeout);
}

void _throwFirstOutputError(List<Object> outputErrors) {
  if (outputErrors.isNotEmpty) {
    throw StateError('gateway terminal output error: ${outputErrors.first}');
  }
}

String _required(Map<String, String> env, String name) {
  final value = env[name]?.trim();
  if (value == null || value.isEmpty) {
    throw ArgumentError('$name is required');
  }
  return value;
}

String? _optional(Map<String, String> env, String name) {
  final value = env[name]?.trim();
  return value == null || value.isEmpty ? null : value;
}

Uri _requiredUri(Map<String, String> env, String name) {
  final value = _required(env, name);
  final uri = Uri.tryParse(value);
  if (uri == null || !uri.hasScheme || uri.host.isEmpty) {
    throw ArgumentError.value(value, name, 'absolute URI required');
  }
  return uri;
}

RouteProviderKind? _optionalRouteProvider(
  Map<String, String> env,
  String name,
) {
  final text = _optional(env, name);
  if (text == null) {
    return null;
  }
  return RouteProviderKind.fromWireName(text);
}

_DnsOverride? _optionalDnsOverride(Map<String, String> env, String name) {
  final text = _optional(env, name);
  if (text == null) {
    return null;
  }
  final parts = text.split('=');
  if (parts.length != 2 ||
      parts.first.trim().isEmpty ||
      parts.last.trim().isEmpty) {
    throw ArgumentError.value(text, name, 'expected host=ip');
  }
  return _DnsOverride(parts.first.trim(), parts.last.trim());
}

HttpClient _httpClientForDnsOverride(_DnsOverride? dnsOverride) {
  final client = HttpClient();
  if (dnsOverride == null) {
    return client;
  }
  client.findProxy = (_) => 'DIRECT';
  client.connectionFactory = (uri, proxyHost, proxyPort) async {
    if (proxyHost != null || proxyPort != null) {
      throw UnsupportedError('DNS override smoke does not support proxies');
    }
    final targetHost =
        uri.host == dnsOverride.host ? dnsOverride.address : uri.host;
    final targetPort =
        uri.hasPort ? uri.port : (uri.scheme == 'https' ? 443 : 80);
    if (uri.scheme == 'https') {
      final socket = await Socket.connect(
        targetHost,
        targetPort,
        timeout: const Duration(seconds: 10),
      );
      return ConnectionTask.fromSocket(
        SecureSocket.secure(socket, host: uri.host),
        () {},
      );
    }
    return await Socket.startConnect(targetHost, targetPort);
  };
  return client;
}

Map<String, Object?> _map(Object? value) {
  if (value is Map) {
    return {
      for (final entry in value.entries) entry.key.toString(): entry.value,
    };
  }
  return const {};
}

Set<String> _stringSet(Object? value) {
  if (value is Iterable) {
    return {for (final item in value) item.toString()};
  }
  return const {};
}

Map<String, String> _stringMap(Object? value) {
  if (value is Map) {
    return {
      for (final entry in value.entries)
        entry.key.toString(): entry.value.toString(),
    };
  }
  return const {};
}

String _requiredText(Object? value, String name) {
  final text = _optionalText(value);
  if (text == null) {
    throw FormatException('missing field: $name');
  }
  return text;
}

String? _optionalText(Object? value) {
  final text = (value ?? '').toString().trim();
  return text.isEmpty ? null : text;
}

Uri? _optionalUri(Object? value) {
  final text = _optionalText(value);
  if (text == null) {
    return null;
  }
  final uri = Uri.tryParse(text);
  return uri != null && uri.hasScheme && uri.host.isNotEmpty ? uri : null;
}

bool _hasText(String? value) => value != null && value.trim().isNotEmpty;

class _ClaimedGateway {
  const _ClaimedGateway({
    required this.profile,
    required this.deviceToken,
    required this.projectId,
  });

  final GatewayHostProfile profile;
  final String deviceToken;
  final String? projectId;
}

class _DnsOverride {
  const _DnsOverride(this.host, this.address);

  final String host;
  final String address;

  Map<String, String> toJson() => {'host': host, 'address': address};
}

extension on CcbTerminalTarget {
  CcbTerminalTarget withoutDirectTmuxEvidence() {
    return CcbTerminalTarget(
      projectId: projectId,
      namespaceEpoch: namespaceEpoch,
      kind: kind,
      scopes: scopes,
      agent: agent,
      window: window,
      paneId: paneId,
    );
  }
}
