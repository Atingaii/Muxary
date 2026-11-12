#!/usr/bin/env python3
"""Probe CCB Mobile local real-backend capabilities.

This is intentionally stricter than the emulator UI smoke. It verifies that a
loopback gateway can be paired, can expose a real project view, can accept a
message, can surface a deterministic Markdown agent reply marker, and can
handle the file upload/download routes used by the mobile app.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import time
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse
from urllib.request import Request, urlopen
import uuid


DEFAULT_GATEWAY_URL = 'http://127.0.0.1:8787'
DEFAULT_AGENT = 'mobile_probe'
DEFAULT_REPLY_TIMEOUT_SECONDS = 15.0
DEFAULT_HTTP_TIMEOUT_SECONDS = 5.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.5


class ProbeHttpClient(Protocol):
    def json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, object] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, object]]:
        ...

    def bytes(
        self,
        method: str,
        path: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        token: str | None = None,
    ) -> tuple[int, bytes]:
        ...


class ProbeHttpError(RuntimeError):
    def __init__(self, *, method: str, path: str, status: int, body: str) -> None:
        super().__init__(f'{method} {path} failed with HTTP {status}: {body[:240]}')
        self.method = method
        self.path = path
        self.status = status
        self.body = body


@dataclass(frozen=True)
class ProbeConfig:
    gateway_url: str
    pairing_code: str
    project_id: str | None
    agent: str
    send_body: str | None
    reply_marker: str | None
    reply_timeout_seconds: float = DEFAULT_REPLY_TIMEOUT_SECONDS
    http_timeout_seconds: float = DEFAULT_HTTP_TIMEOUT_SECONDS
    poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS
    include_revoke_gate: bool = False


class GatewayProbeHttpClient:
    def __init__(self, *, gateway_url: str, timeout_seconds: float) -> None:
        self._base_url = _normalize_gateway_url(gateway_url)
        self._timeout_seconds = timeout_seconds

    def json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, object] | None = None,
        token: str | None = None,
    ) -> tuple[int, dict[str, object]]:
        body = None
        headers = {'Accept': 'application/json'}
        if payload is not None:
            body = json.dumps(payload).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        if token:
            headers['Authorization'] = f'Bearer {token}'
        request = Request(
            urljoin(self._base_url, path),
            data=body,
            method=method,
            headers=headers,
        )
        status, response_body = self._open(request, method=method, path=path)
        try:
            decoded = json.loads(response_body.decode('utf-8'))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f'{method} {path} did not return JSON') from exc
        if not isinstance(decoded, dict):
            raise RuntimeError(f'{method} {path} did not return a JSON object')
        return status, {str(key): value for key, value in decoded.items()}

    def bytes(
        self,
        method: str,
        path: str,
        *,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        token: str | None = None,
    ) -> tuple[int, bytes]:
        request_headers = dict(headers or {})
        if token:
            request_headers['Authorization'] = f'Bearer {token}'
        request = Request(
            urljoin(self._base_url, path),
            data=data,
            method=method,
            headers=request_headers,
        )
        return self._open(request, method=method, path=path)

    def _open(self, request: Request, *, method: str, path: str) -> tuple[int, bytes]:
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                return response.status, response.read()
        except HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')
            raise ProbeHttpError(
                method=method,
                path=path,
                status=exc.code,
                body=body,
            ) from exc
        except URLError as exc:
            raise RuntimeError(f'{method} {path} failed: {exc.reason}') from exc


def run_probe(
    config: ProbeConfig,
    *,
    client: ProbeHttpClient | None = None,
    clock=time.monotonic,
    sleep=time.sleep,
) -> dict[str, object]:
    http = client or GatewayProbeHttpClient(
        gateway_url=config.gateway_url,
        timeout_seconds=config.http_timeout_seconds,
    )
    run_id = uuid.uuid4().hex[:10]
    send_body = config.send_body or f'ccb-local-md:{run_id}'
    reply_marker = config.reply_marker or send_body.replace(
        'ccb-local-md:',
        'ccb-local-reply:',
        1,
    )
    steps: list[dict[str, object]] = []
    token = ''
    project_id = config.project_id or ''
    device_id = ''
    namespace_epoch: int | None = None
    uploaded_file_id = ''

    steps.append(_measure_step('health', clock, lambda: _probe_health(http)))

    if config.pairing_code.strip():
        claim = _measure_step(
            'pairing_claim',
            clock,
            lambda: _probe_pairing_claim(http, config.pairing_code),
        )
        steps.append(claim)
        if claim['status'] == 'pass':
            details = _as_dict(claim.get('details'))
            token = str(details.get('device_token') or '')
            device_id = str(details.get('device_id') or '')
            project_id = project_id or str(details.get('project_id') or '')
    else:
        steps.append(
            _step(
                'pairing_claim',
                'blocked',
                'pairing code is required for authenticated local backend gates',
            )
        )

    if token and project_id:
        view_step = _measure_step(
            'project_view',
            clock,
            lambda: _probe_project_view(http, project_id, token),
        )
        steps.append(view_step)
        if view_step['status'] == 'pass':
            details = _as_dict(view_step.get('details'))
            namespace_epoch = _optional_int(details.get('namespace_epoch'))
    else:
        steps.append(_step('project_view', 'blocked', 'missing device token or project id'))

    if token and project_id and namespace_epoch is not None:
        submit_step = _measure_step(
            'message_submit',
            clock,
            lambda: _probe_message_submit(
                http,
                project_id=project_id,
                agent=config.agent,
                namespace_epoch=namespace_epoch,
                token=token,
                body=send_body,
                run_id=run_id,
            ),
        )
        steps.append(submit_step)
    else:
        steps.append(_step('message_submit', 'blocked', 'missing project view epoch'))

    if token and project_id and namespace_epoch is not None:
        reply_step = _measure_step(
            'agent_reply_marker',
            clock,
            lambda: _probe_reply_marker(
                http,
                project_id=project_id,
                agent=config.agent,
                namespace_epoch=namespace_epoch,
                token=token,
                marker=reply_marker,
                timeout_seconds=config.reply_timeout_seconds,
                poll_interval_seconds=config.poll_interval_seconds,
                clock=clock,
                sleep=sleep,
            ),
        )
        steps.append(reply_step)
    else:
        steps.append(_step('agent_reply_marker', 'blocked', 'missing project view epoch'))

    if token and project_id:
        upload_step = _measure_step(
            'file_upload_route',
            clock,
            lambda: _probe_file_upload(
                http,
                project_id=project_id,
                agent=config.agent,
                token=token,
            ),
            blocked_http_statuses={400, 404, 405, 501},
        )
        steps.append(upload_step)
        file_id = ''
        if upload_step['status'] == 'pass':
            file_id = str(_as_dict(upload_step.get('details')).get('file_id') or '')
            uploaded_file_id = file_id
        if file_id:
            steps.append(
                _measure_step(
                    'file_download_route',
                    clock,
                    lambda: _probe_file_download(
                        http,
                        project_id=project_id,
                        agent=config.agent,
                        token=token,
                        file_id=file_id,
                    ),
                    blocked_http_statuses={400, 404, 405, 501},
                )
            )
        else:
            steps.append(
                _step(
                    'file_download_route',
                    'blocked',
                    'file upload did not return a downloadable file_id',
                )
            )
    else:
        steps.append(_step('file_upload_route', 'blocked', 'missing device token or project id'))
        steps.append(_step('file_download_route', 'blocked', 'missing upload file_id'))

    if token and project_id and namespace_epoch is not None:
        artifact_step = _measure_step(
            'backend_artifact_route',
            clock,
            lambda: _probe_backend_artifact_route(
                http,
                project_id=project_id,
                agent=config.agent,
                namespace_epoch=namespace_epoch,
                token=token,
                run_id=run_id,
                timeout_seconds=config.reply_timeout_seconds,
                poll_interval_seconds=config.poll_interval_seconds,
                clock=clock,
                sleep=sleep,
            ),
            blocked_http_statuses={400, 404, 405, 501},
        )
        steps.append(artifact_step)
    else:
        steps.append(_step('backend_artifact_route', 'blocked', 'missing project view epoch'))

    if config.include_revoke_gate:
        if token and project_id and device_id and namespace_epoch is not None:
            steps.append(
                _measure_step(
                    'revoke_fail_closed',
                    clock,
                    lambda: _probe_revoke_fail_closed(
                        http,
                        project_id=project_id,
                        agent=config.agent,
                        namespace_epoch=namespace_epoch,
                        token=token,
                        device_id=device_id,
                        file_id=uploaded_file_id,
                        run_id=run_id,
                    ),
                )
            )
        else:
            steps.append(
                _step(
                    'revoke_fail_closed',
                    'blocked',
                    'missing device token, device id, project id, or namespace epoch',
                )
            )

    return {
        'schema_version': 1,
        'status': overall_status(steps),
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'gateway_url': config.gateway_url,
        'project_id': project_id or None,
        'agent': config.agent,
        'send_body': send_body,
        'reply_marker': reply_marker,
        'steps': steps,
        'timing': timing_summary(steps),
        'next_actions': next_actions_for_steps(steps),
    }


def _probe_health(http: ProbeHttpClient) -> dict[str, object]:
    _status, payload = http.json('GET', '/v1/health')
    return {'gateway_status': payload.get('status'), 'capabilities': payload.get('capabilities')}


def _probe_pairing_claim(http: ProbeHttpClient, pairing_code: str) -> dict[str, object]:
    _status, payload = http.json(
        'POST',
        '/v1/pairing/claim',
        payload={'pairing_code': pairing_code, 'device_name': 'Local Backend Capability Probe'},
    )
    host_profile = _as_dict(payload.get('host_profile'))
    device = _as_dict(payload.get('device'))
    token = str(payload.get('device_token') or '')
    if not token:
        raise RuntimeError('pairing claim did not return device_token')
    return {
        'project_id': payload.get('project_id') or host_profile.get('project_id') or device.get('project_id'),
        'device_id': payload.get('device_id') or host_profile.get('device_id') or device.get('device_id'),
        'device_token': token,
        'scopes': payload.get('scopes') or host_profile.get('scopes') or device.get('scopes'),
    }


def _probe_project_view(
    http: ProbeHttpClient,
    project_id: str,
    token: str,
) -> dict[str, object]:
    _status, payload = http.json('GET', f'/v1/projects/{quote(project_id)}/view', token=token)
    view = _as_dict(payload.get('view'))
    namespace = _as_dict(view.get('namespace'))
    agents = [
        str(_as_dict(item).get('name') or '')
        for item in _as_list(view.get('agents'))
        if str(_as_dict(item).get('name') or '').strip()
    ]
    epoch = _optional_int(namespace.get('epoch'))
    if epoch is None:
        raise RuntimeError('project view did not include namespace epoch')
    return {
        'project_id': _as_dict(view.get('project')).get('id') or project_id,
        'namespace_epoch': epoch,
        'agents': agents,
    }


def _probe_message_submit(
    http: ProbeHttpClient,
    *,
    project_id: str,
    agent: str,
    namespace_epoch: int,
    token: str,
    body: str,
    run_id: str,
) -> dict[str, object]:
    _status, payload = http.json(
        'POST',
        f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/messages',
        token=token,
        payload={
            'schema_version': 1,
            'project_id': project_id,
            'agent': agent,
            'namespace_epoch': namespace_epoch,
            'idempotency_key': f'local-probe-{run_id}',
            'body': body,
            'format': 'markdown',
        },
    )
    submit = _as_dict(payload.get('message_submit'))
    if submit.get('accepted') is not True:
        raise RuntimeError('message_submit.accepted was not true')
    return {
        'message_id': submit.get('message_id'),
        'job_id': submit.get('job_id'),
        'state': submit.get('state'),
    }


def _probe_reply_marker(
    http: ProbeHttpClient,
    *,
    project_id: str,
    agent: str,
    namespace_epoch: int,
    token: str,
    marker: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
    clock,
    sleep,
) -> dict[str, object]:
    deadline = clock() + timeout_seconds
    polls = 0
    last_bodies: list[str] = []
    while True:
        polls += 1
        _status, payload = http.json(
            'GET',
            (
                f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/'
                f'conversation?namespace_epoch={namespace_epoch}&limit=50'
            ),
            token=token,
        )
        if conversation_has_agent_reply_marker(payload, marker):
            return {'marker': marker, 'polls': polls}
        last_bodies = conversation_bodies(payload)[-5:]
        if clock() >= deadline:
            raise CapabilityBlocked(
                f'agent reply marker not visible before timeout: {marker}',
                {'marker': marker, 'polls': polls, 'last_bodies': last_bodies},
            )
        sleep(poll_interval_seconds)


def _probe_file_upload(
    http: ProbeHttpClient,
    *,
    project_id: str,
    agent: str,
    token: str,
) -> dict[str, object]:
    _status, payload_bytes = http.bytes(
        'POST',
        f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/files',
        token=token,
        data=b'ccb mobile local backend file probe\n',
        headers={
            'Accept': 'application/json',
            'Content-Type': 'text/plain; charset=utf-8',
            'X-Ccb-File-Name': quote('local-backend-probe.txt'),
        },
    )
    payload = json.loads(payload_bytes.decode('utf-8'))
    if not isinstance(payload, dict):
        raise RuntimeError('file upload response was not a JSON object')
    file_id = str(payload.get('file_id') or payload.get('attachment_id') or '')
    if not file_id:
        raise RuntimeError('file upload response did not include file_id')
    return {
        'file_id': file_id,
        'file_name': payload.get('file_name') or payload.get('filename'),
        'size_bytes': payload.get('size_bytes'),
    }


def _probe_file_download(
    http: ProbeHttpClient,
    *,
    project_id: str,
    agent: str,
    token: str,
    file_id: str,
) -> dict[str, object]:
    _status, body = http.bytes(
        'GET',
        f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/files/{quote(file_id)}',
        token=token,
        headers={'Accept': '*/*'},
    )
    expected = b'ccb mobile local backend file probe\n'
    if body != expected:
        raise RuntimeError(f'downloaded bytes mismatch: {len(body)} bytes')
    return {'file_id': file_id, 'size_bytes': len(body)}


def _probe_backend_artifact_route(
    http: ProbeHttpClient,
    *,
    project_id: str,
    agent: str,
    namespace_epoch: int,
    token: str,
    run_id: str,
    timeout_seconds: float,
    poll_interval_seconds: float,
    clock,
    sleep,
) -> dict[str, object]:
    _status, submit_payload = http.json(
        'POST',
        f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/messages',
        token=token,
        payload={
            'schema_version': 1,
            'project_id': project_id,
            'agent': agent,
            'namespace_epoch': namespace_epoch,
            'idempotency_key': f'local-probe-artifact-{run_id}',
            'body': f'ccb-local-artifact:{run_id}',
            'format': 'markdown',
        },
    )
    submit = _as_dict(submit_payload.get('message_submit'))
    if submit.get('accepted') is not True:
        raise RuntimeError('artifact message_submit.accepted was not true')

    deadline = clock() + timeout_seconds
    polls = 0
    file_id = ''
    while True:
        polls += 1
        _status, conv_payload = http.json(
            'GET',
            (
                f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/'
                f'conversation?namespace_epoch={namespace_epoch}&limit=50'
            ),
            token=token,
        )
        conversation = _as_dict(conv_payload.get('conversation'))
        items = _as_list(conversation.get('items'))
        for item in items:
            item_dict = _as_dict(item)
            if item_dict.get('kind') == 'agent_reply':
                body = str(item_dict.get('body') or '')
                if f'CCB Local Artifacts {run_id}' in body:
                    attachments = _as_list(item_dict.get('attachments'))
                    for att in attachments:
                        att_dict = _as_dict(att)
                        if str(att_dict.get('file_name') or '').startswith(f'artifact-{run_id}'):
                            file_id = str(att_dict.get('file_id') or '')
                            break
                    if file_id:
                        break
        if file_id:
            break
        if clock() >= deadline:
            raise CapabilityBlocked(
                f'artifact reply not visible before timeout',
                {'run_id': run_id, 'polls': polls},
            )
        sleep(poll_interval_seconds)

    _status, body = http.bytes(
        'GET',
        f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/files/{quote(file_id)}',
        token=token,
        headers={'Accept': '*/*'},
    )
    expected = f'Generated text artifact for {run_id}'.encode('utf-8')
    if body != expected:
        raise RuntimeError(f'downloaded artifact bytes mismatch: {len(body)} bytes')

    return {'file_id': file_id, 'size_bytes': len(body), 'polls': polls}


def _probe_revoke_fail_closed(
    http: ProbeHttpClient,
    *,
    project_id: str,
    agent: str,
    namespace_epoch: int,
    token: str,
    device_id: str,
    file_id: str,
    run_id: str,
) -> dict[str, object]:
    _status, payload = http.json(
        'POST',
        f'/v1/devices/{quote(device_id)}/revoke',
        payload={},
        token=token,
    )
    device = _as_dict(payload.get('device'))
    if device.get('revoked') is not True:
        raise RuntimeError('device revoke did not mark device as revoked')

    denied_routes = [
        _expect_json_denied(
            http,
            'GET',
            '/v1/devices/me',
            token=token,
        ),
        _expect_json_denied(
            http,
            'GET',
            f'/v1/projects/{quote(project_id)}/view',
            token=token,
        ),
        _expect_json_denied(
            http,
            'POST',
            f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/messages',
            token=token,
            payload={
                'schema_version': 1,
                'project_id': project_id,
                'agent': agent,
                'namespace_epoch': namespace_epoch,
                'idempotency_key': f'local-probe-revoked-{run_id}',
                'body': f'ccb-local-echo:revoked-{run_id}',
                'format': 'markdown',
            },
        ),
        _expect_json_denied(
            http,
            'POST',
            f'/v1/projects/{quote(project_id)}/terminals',
            token=token,
            payload={
                'schema_version': 1,
                'project_id': project_id,
                'namespace_epoch': namespace_epoch,
                'target': {'kind': 'agent', 'agent': agent},
                'geometry': {'columns': 80, 'rows': 24},
            },
        ),
    ]
    if file_id:
        denied_routes.append(
            _expect_bytes_denied(
                http,
                'GET',
                (
                    f'/v1/projects/{quote(project_id)}/agents/{quote(agent)}/'
                    f'files/{quote(file_id)}'
                ),
                token=token,
            )
        )
    return {
        'device_id': device_id,
        'revoked': True,
        'denied_routes': denied_routes,
    }


def _expect_json_denied(
    http: ProbeHttpClient,
    method: str,
    path: str,
    *,
    token: str,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    try:
        http.json(method, path, payload=payload, token=token)
    except ProbeHttpError as exc:
        if exc.status in {401, 403}:
            return {'method': method, 'path': path, 'status': exc.status}
        raise
    raise RuntimeError(f'{method} {path} succeeded after device revoke')


def _expect_bytes_denied(
    http: ProbeHttpClient,
    method: str,
    path: str,
    *,
    token: str,
) -> dict[str, object]:
    try:
        http.bytes(method, path, token=token, headers={'Accept': '*/*'})
    except ProbeHttpError as exc:
        if exc.status in {401, 403}:
            return {'method': method, 'path': path, 'status': exc.status}
        raise
    raise RuntimeError(f'{method} {path} succeeded after device revoke')


class CapabilityBlocked(RuntimeError):
    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


def _measure_step(
    name: str,
    clock,
    fn,
    *,
    blocked_http_statuses: set[int] | None = None,
) -> dict[str, object]:
    started = clock()
    try:
        details = fn()
        duration_ms = round((clock() - started) * 1000, 3)
        return _step(name, 'pass', None, duration_ms=duration_ms, details=details)
    except CapabilityBlocked as exc:
        duration_ms = round((clock() - started) * 1000, 3)
        return _step(name, 'blocked', str(exc), duration_ms=duration_ms, details=exc.details)
    except ProbeHttpError as exc:
        duration_ms = round((clock() - started) * 1000, 3)
        status = 'blocked' if exc.status in (blocked_http_statuses or set()) else 'fail'
        return _step(
            name,
            status,
            str(exc),
            duration_ms=duration_ms,
            details={'http_status': exc.status},
        )
    except Exception as exc:
        duration_ms = round((clock() - started) * 1000, 3)
        return _step(name, 'fail', str(exc), duration_ms=duration_ms)


def _step(
    name: str,
    status: str,
    error: str | None,
    *,
    duration_ms: float | None = None,
    details: dict[str, object] | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {'name': name, 'status': status}
    if duration_ms is not None:
        result['duration_ms'] = duration_ms
    if details:
        result['details'] = details
    if error:
        result['error'] = error
    return result


def overall_status(steps: list[dict[str, object]]) -> str:
    statuses = {str(step.get('status') or '') for step in steps}
    if 'fail' in statuses:
        return 'fail'
    if 'blocked' in statuses:
        return 'blocked'
    if not steps:
        return 'blocked'
    return 'ok'


def timing_summary(steps: list[dict[str, object]]) -> dict[str, object]:
    durations = [
        float(step['duration_ms'])
        for step in steps
        if step.get('status') == 'pass' and isinstance(step.get('duration_ms'), (int, float))
    ]
    if not durations:
        return {'samples': 0}
    ordered = sorted(durations)
    return {
        'samples': len(ordered),
        'p50_ms': percentile(ordered, 50),
        'p95_ms': percentile(ordered, 95),
        'max_ms': round(max(ordered), 3),
    }


def percentile(ordered_values: list[float], percentile_value: float) -> float:
    if not ordered_values:
        raise ValueError('percentile requires at least one value')
    if len(ordered_values) == 1:
        return round(float(ordered_values[0]), 3)
    rank = (len(ordered_values) - 1) * (percentile_value / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered_values) - 1)
    weight = rank - lower
    value = ordered_values[lower] * (1.0 - weight) + ordered_values[upper] * weight
    return round(value, 3)


def next_actions_for_steps(steps: list[dict[str, object]]) -> list[str]:
    actions: list[str] = []
    by_name = {str(step.get('name')): step for step in steps}
    if by_name.get('agent_reply_marker', {}).get('status') == 'blocked':
        actions.append(
            'Add or start a deterministic local backend fixture that turns '
            'ccb-local-md:<id> into ccb-local-reply:<id>.'
        )
    if by_name.get('file_upload_route', {}).get('status') == 'blocked':
        actions.append(
            'Implement source gateway /v1/projects/{project}/agents/{agent}/files upload.'
        )
    if by_name.get('file_download_route', {}).get('status') == 'blocked':
        actions.append(
            'Implement source gateway file download and byte-hash verification.'
        )
    if by_name.get('backend_artifact_route', {}).get('status') == 'blocked':
        actions.append(
            'Register backend-agent generated artifacts as mobile-downloadable resources.'
        )
    return actions


def conversation_has_agent_reply_marker(payload: dict[str, object], marker: str) -> bool:
    conversation = _as_dict(payload.get('conversation'))
    for item in _as_list(conversation.get('items')):
        record = _as_dict(item)
        if str(record.get('kind') or '') != 'agent_reply':
            continue
        if marker in str(record.get('body') or ''):
            return True
    return False


def conversation_bodies(payload: dict[str, object]) -> list[str]:
    conversation = _as_dict(payload.get('conversation'))
    return [str(_as_dict(item).get('body') or '') for item in _as_list(conversation.get('items'))]


def _normalize_gateway_url(value: str) -> str:
    text = str(value or '').strip()
    parsed = urlparse(text)
    if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
        raise ValueError(f'gateway URL must be absolute HTTP(S): {value}')
    return text.rstrip('/') + '/'


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    return int(text) if text else None


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Probe a loopback CCB Mobile gateway for real local backend gates.',
    )
    parser.add_argument('--gateway-url', default=DEFAULT_GATEWAY_URL)
    parser.add_argument('--pairing-code', default='')
    parser.add_argument('--project-id')
    parser.add_argument('--agent', default=DEFAULT_AGENT)
    parser.add_argument('--send-body')
    parser.add_argument('--reply-marker')
    parser.add_argument('--reply-timeout', type=float, default=DEFAULT_REPLY_TIMEOUT_SECONDS)
    parser.add_argument('--http-timeout', type=float, default=DEFAULT_HTTP_TIMEOUT_SECONDS)
    parser.add_argument('--poll-interval', type=float, default=DEFAULT_POLL_INTERVAL_SECONDS)
    parser.add_argument(
        '--include-revoke-gate',
        action='store_true',
        help='after normal gates pass, revoke the claimed device and verify protected routes fail closed',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_probe(
        ProbeConfig(
            gateway_url=args.gateway_url,
            pairing_code=args.pairing_code,
            project_id=args.project_id,
            agent=args.agent,
            send_body=args.send_body,
            reply_marker=args.reply_marker,
            reply_timeout_seconds=args.reply_timeout,
            http_timeout_seconds=args.http_timeout,
            poll_interval_seconds=args.poll_interval,
            include_revoke_gate=args.include_revoke_gate,
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
