from __future__ import annotations

from http.client import HTTPConnection
import json
from pathlib import Path
import sqlite3
import threading

import pytest

from ccbd.socket_client import CcbdClientError
from mobile_gateway import MobileGatewayError, MobileGatewayProject, MobileGatewayProjectRegistry
from workbench import WorkbenchService, build_workbench_server


class Client:
    def __init__(self, project_id='p1'):
        self.project_id = project_id
        self.calls = []
        self.state = 'running'
        self.fail_submit = False
        self.cancel_race = False
        self.watch_id = 'job_one'

    def project_view(self, **kwargs):
        return {'view': {'project': {'id': self.project_id}, 'namespace': {'epoch': 4},
                         'agents': [{'name': 'buddy', 'provider': 'codebuddy', 'current_job_id': 'job_one'}],
                         'comms': [{'id': 'job_old', 'target': 'buddy'}]}}

    def submit(self, envelope):
        self.calls.append(('submit', envelope.to_record()))
        if self.fail_submit:
            raise CcbdClientError('request timed out after commit with a secret detail')
        return {'job_id': 'job_one', 'agent_name': 'buddy', 'status': 'queued'}

    def get(self, job_id):
        self.calls.append(('get', job_id))
        return {'job_id': job_id, 'status': self.state, 'reply': 'partial',
                'job': {'job_id': job_id, 'agent_name': 'buddy', 'status': self.state,
                        'request': {'project_id': self.project_id, 'body': 'hello', 'from_actor': 'user', 'to_agent': 'buddy'}}}

    def watch(self, target, *, cursor=0):
        self.calls.append(('watch', target, cursor))
        return {'job_id': self.watch_id, 'status': self.state, 'terminal': False, 'cursor': cursor + 1, 'events': []}

    def queue(self, target, *, detail=False):
        self.calls.append(('queue', target, detail))
        return {'agent': {'active': {'job_id': 'job_one'}, 'queued_events': [{'job_id': 'job_two'}]}}

    def cancel(self, job_id):
        self.calls.append(('cancel', job_id))
        if self.cancel_race:
            self.state = 'completed'
            raise CcbdClientError('job already terminal')
        self.state = 'cancelled'
        return {'job_id': job_id, 'agent_name': 'buddy', 'status': 'cancelled'}

    def retry(self, job_id):
        self.calls.append(('retry', job_id))
        return {'job_id': 'job_new', 'agent_name': 'buddy', 'status': 'queued'}


class Gateway:
    def __init__(self):
        self.calls = []

    def projects_payload(self):
        return {'projects': [{'id': 'p1', 'health': 'unknown'}]}

    def dispatch_get(self, path, headers):
        self.calls.append(('get', path))
        return 200, {'view': {}}

    def dispatch_post(self, path, body, headers):
        self.calls.append(('post', path, body))
        return 201, {'terminal_id': 'term_one', 'terminal_token': 'fixture'}

    def close(self):
        self.calls.append(('close',))


@pytest.fixture
def setup(tmp_path):
    client, gateway = Client(), Gateway()
    root = tmp_path / 'repo'
    root.mkdir()
    assets = tmp_path / 'assets'
    assets.mkdir()
    (assets / 'index.html').write_text('<html>workbench</html>')
    registry = MobileGatewayProjectRegistry([MobileGatewayProject('p1', root, lambda: client)])
    service = WorkbenchService(project_registry=registry, assets_dir=assets, state_dir=tmp_path / 'state', gateway=gateway)
    yield service, client, gateway
    service.close()


def submit(service, **changes):
    return service.dispatch('POST', '/api/projects/p1/jobs', {'agent': 'buddy', 'body': 'hello', 'idempotency_key': 'key', **changes})


def test_submit_is_real_ccbd_and_replay_does_not_resubmit(setup):
    service, client, _ = setup
    status, receipt = submit(service)
    assert status == 202 and receipt['job_id'] == 'job_one' and receipt['status'] == 'queued'
    assert submit(service)[1]['replayed'] is True
    sends = [call for call in client.calls if call[0] == 'submit']
    assert len(sends) == 1
    assert sends[0][1]['project_id'] == 'p1' and sends[0][1]['from_actor'] == 'user'
    assert sends[0][1]['body'] == 'hello'
    assert submit(service, body='different')[0] == 409


def test_timeout_is_unknown_and_survives_new_service_instance(setup):
    service, client, gateway = setup
    client.fail_submit = True
    assert submit(service) == (503, {'schema_version': 1, 'error': 'outcome_unknown', 'idempotency_key': 'key', 'retry_safe': False})
    client.fail_submit = False
    assert submit(service)[1]['error'] == 'outcome_unknown'
    second = WorkbenchService(project_registry=service.registry, assets_dir=service.assets_dir,
                              state_dir=service.state_dir, gateway=gateway)
    try:
        assert submit(second)[1]['error'] == 'outcome_unknown'
        assert len([call for call in client.calls if call[0] == 'submit']) == 1
    finally:
        second.close()


def test_pending_receipt_does_not_resend_after_crash(setup):
    service, client, _ = setup
    assert submit(service)[0] == 202
    with sqlite3.connect(service._db_path) as db:
        db.execute('UPDATE receipts SET status=NULL,payload=NULL')
    assert submit(service)[1]['error'] == 'outcome_unknown'
    assert len([call for call in client.calls if call[0] == 'submit']) == 1


@pytest.mark.parametrize('body', [{'agent': 'buddy', 'body': 'hi'}, {'agent': 'buddy', 'body': ''},
                                  {'agent': 'other', 'body': 'hi', 'idempotency_key': 'x'},
                                  {'agent': 'buddy', 'body': 'hi', 'idempotency_key': 'x', 'namespace_epoch': 3}])
def test_invalid_submit_never_calls_rpc(setup, body):
    service, client, _ = setup
    with pytest.raises(MobileGatewayError):
        service.dispatch('POST', '/api/projects/p1/jobs', body)
    assert not any(call[0] == 'submit' for call in client.calls)


def test_cross_project_job_is_not_read_watched_or_mutated(setup):
    service, client, _ = setup
    client.project_id = 'p2'
    for method, suffix in [('GET', ''), ('GET', '/watch'), ('POST', '/cancel'), ('POST', '/retry')]:
        with pytest.raises(MobileGatewayError) as exc:
            service.dispatch(method, '/api/projects/p1/jobs/job_one' + suffix, {'idempotency_key': 'x'})
        assert exc.value.status_code == 404
    assert all(call[0] == 'get' for call in client.calls)
    with pytest.raises(MobileGatewayError):
        submit(service)
    assert not any(call[0] == 'submit' for call in client.calls)


def test_get_watch_preserve_unknown_and_never_infer_completion(setup):
    service, client, _ = setup
    client.state = 'unknown'
    status, result = service.dispatch('GET', '/api/projects/p1/jobs/job_one')
    assert status == 200 and result['status'] == 'unknown' and result['job']['status'] == 'unknown'
    result = service.dispatch('GET', '/api/projects/p1/jobs/job_one/watch?cursor=7')[1]
    assert result['status'] == 'unknown' and not result['terminal'] and result['cursor'] == 8
    assert ('watch', 'job_one', 7) in client.calls
    client.watch_id = 'job_other'
    with pytest.raises(MobileGatewayError):
        service.dispatch('GET', '/api/projects/p1/jobs/job_one/watch')


@pytest.mark.parametrize('target', ['buddy', 'all', '../job_one'])
def test_job_endpoints_never_fallback_to_agent_alias(setup, target):
    service, client, _ = setup
    with pytest.raises(MobileGatewayError):
        service.dispatch('GET', '/api/projects/p1/jobs/' + target + '/watch')
    assert not client.calls


def test_cancel_race_reports_completed_not_cancelled(setup):
    service, client, _ = setup
    client.cancel_race = True
    status, result = service.dispatch('POST', '/api/projects/p1/jobs/job_one/cancel', {'idempotency_key': 'cancel'})
    assert status == 409 and result['error'] == 'job_already_terminal'
    assert result['job']['status'] == 'completed'
    service.dispatch('POST', '/api/projects/p1/jobs/job_one/cancel', {'idempotency_key': 'cancel'})
    assert len([call for call in client.calls if call[0] == 'cancel']) == 1


def test_retry_is_explicit_and_not_allowed_for_active_or_completed(setup):
    service, client, _ = setup
    path = '/api/projects/p1/jobs/job_one/retry'
    for state in ('running', 'completed', 'unknown'):
        client.state = state
        assert service.dispatch('POST', path, {'idempotency_key': state})[0] == 409
    client.state = 'failed'
    assert service.dispatch('POST', path, {'idempotency_key': 'failed'})[1]['job_id'] == 'job_new'
    assert service.dispatch('POST', path, {'idempotency_key': 'failed'})[1]['replayed'] is True
    assert len([call for call in client.calls if call[0] == 'retry']) == 1


def test_job_list_uses_queue_and_view_without_local_job_index(setup):
    service, client, _ = setup
    result = service.dispatch('GET', '/api/projects/p1/jobs?agent=buddy')[1]
    assert {item['job_id'] for item in result['jobs']} == {'job_one', 'job_two', 'job_old'}
    assert result['source'] == 'ccbd_queue_and_project_view' and not result['history_complete']
    assert all(item['request']['project_id'] == 'p1' and item['reply'] == 'partial' for item in result['jobs'])
    assert ('queue', 'buddy', True) in client.calls
    with pytest.raises(MobileGatewayError):
        service.dispatch('GET', '/api/projects/p1/jobs?agent=not_found')


def test_gateway_conversation_and_terminal_are_thin_bridges(setup):
    service, _, gateway = setup
    service.origin = 'http://127.0.0.1:12345'
    service.dispatch('GET', '/api/projects/p1/agents/buddy/conversation?limit=5')
    assert gateway.calls[-1] == ('get', '/v1/projects/p1/agents/buddy/conversation?limit=5')
    status, result = service.dispatch('POST', '/api/projects/p1/terminals', {'target': {'agent': 'buddy'}})
    assert status == 201 and result['terminal_token'] == 'fixture'
    assert result['websocket_url'] == 'ws://127.0.0.1:12345/api/terminals/term_one/ws'
    for path in ('/api/pairing/claim', '/api/devices/me', '/api/terminals', '/api/projects/p1/agents/buddy/messages'):
        with pytest.raises(MobileGatewayError):
            service.dispatch('POST', path, {})


@pytest.fixture
def server(setup):
    service, _, _ = setup
    server = build_workbench_server(service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield service, server
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def request(server, method, path, body=None, headers=None):
    service, http = server
    connection = HTTPConnection(*http.server_address, timeout=3)
    headers = dict(headers or {})
    if body is not None:
        headers.setdefault('Content-Type', 'application/json')
        body = json.dumps(body)
    connection.request(method, path, body, headers)
    response = connection.getresponse()
    status, response_headers, data = response.status, dict(response.getheaders()), response.read()
    connection.close()
    if 'application/json' in response_headers.get('Content-Type', ''):
        data = json.loads(data)
    return status, response_headers, data


def login(server):
    service, _ = server
    status, headers, _ = request(server, 'POST', '/api/session', {'token': service.bootstrap_token}, {'Origin': service.origin})
    assert status == 200
    return headers['Set-Cookie'].split(';')[0]


def test_session_bootstrap_is_fragment_only_single_use_and_cookie_is_private(server):
    service, _ = server
    assert request(server, 'GET', '/')[0] == 200
    assert request(server, 'GET', '/api/projects')[0] == 401
    assert request(server, 'GET', '/api/projects?token=' + service.bootstrap_token)[0] == 401
    assert request(server, 'POST', '/api/session', {'token': service.bootstrap_token})[0] == 403
    status, headers, _ = request(server, 'POST', '/api/session', {'token': service.bootstrap_token}, {'Origin': service.origin})
    assert status == 200 and 'HttpOnly' in headers['Set-Cookie'] and 'SameSite=Strict' in headers['Set-Cookie']
    cookie = headers['Set-Cookie'].split(';')[0]
    assert request(server, 'GET', '/api/projects', headers={'Cookie': cookie})[0] == 200
    assert request(server, 'POST', '/api/session', {'token': service.bootstrap_token}, {'Origin': service.origin})[0] == 401


@pytest.mark.parametrize('headers', [{'Host': 'evil.invalid'}, {'Host': 'localhost'},
                                    {'Origin': 'http://evil.invalid'}, {'Origin': 'null'}, {'Sec-Fetch-Site': 'cross-site'},
                                    {'Sec-Fetch-Site': 'same-site'}])
def test_host_origin_and_dns_rebinding_boundaries(server, headers):
    cookie = login(server)
    status, response_headers, _ = request(server, 'GET', '/api/projects', headers={'Cookie': cookie, **headers})
    assert status == 403
    assert 'Access-Control-Allow-Origin' not in response_headers


def test_mutations_need_same_origin_even_with_valid_cookie(server):
    service, _ = server
    cookie = login(server)
    assert request(server, 'POST', '/api/projects/p1/jobs', {}, {'Cookie': cookie})[0] == 403
    status, _, result = request(server, 'POST', '/api/projects/p1/jobs',
                                {'agent': 'buddy', 'body': 'hello', 'idempotency_key': 'web'},
                                {'Cookie': cookie, 'Origin': service.origin})
    assert status == 202 and result['job_id'] == 'job_one'


def test_static_traversal_and_symlinks_are_rejected(server, tmp_path):
    service, _ = server
    outside = tmp_path / 'private.txt'
    outside.write_text('private')
    (service.assets_dir / 'leak').symlink_to(outside)
    for path in ('/../private.txt', '/%2e%2e/private.txt', '/leak'):
        assert request(server, 'GET', path)[0] == 404
    _, headers, _ = request(server, 'GET', '/')
    assert headers['Referrer-Policy'] == 'no-referrer'
    assert "frame-ancestors 'none'" in headers['Content-Security-Policy']


def test_non_loopback_binding_is_rejected(setup):
    service, _, _ = setup
    with pytest.raises(ValueError):
        build_workbench_server(service, host='0.0.0.0')


def test_read_only_diff_uses_registered_root_and_disables_external_filters(setup, monkeypatch):
    service, _, _ = setup
    import subprocess
    root = service.registry.default_project.project_root
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    (root / 'file.txt').write_text('old\n')
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    (root / 'file.txt').write_text('new\n')
    subprocess.run(['git', '-C', str(root), 'config', 'diff.external', 'must-never-execute'], check=True)
    result = service.dispatch('GET', '/api/projects/p1/diff?path=/etc')[1]
    assert '-old' in result['patch'] and '+new' in result['patch']
    assert 'file.txt' in result['stat'] and result['scope'] == 'unstaged_tracked'
    assert not result['patch_truncated']


def test_diff_output_is_bounded(setup):
    service, _, _ = setup
    import subprocess
    root = service.registry.default_project.project_root
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    (root / 'large.txt').write_text('old\n')
    subprocess.run(['git', '-C', str(root), 'add', '.'], check=True)
    (root / 'large.txt').write_text('new\n' * 100000)
    result = service.dispatch('GET', '/api/projects/p1/diff')[1]
    assert result['patch_truncated'] and len(result['patch'].encode()) <= 262144


def test_replay_is_returned_before_changed_namespace_or_offline_preflight(setup, monkeypatch):
    service, client, _ = setup
    assert submit(service, namespace_epoch=4)[0] == 202
    def offline(**kwargs):
        raise CcbdClientError('offline')
    monkeypatch.setattr(client, 'project_view', offline)
    assert submit(service, namespace_epoch=4)[1]['replayed'] is True
    assert len([call for call in client.calls if call[0] == 'submit']) == 1


def test_concurrent_same_key_is_reserved_before_rpc(setup, monkeypatch):
    service, client, _ = setup
    entered, release = threading.Event(), threading.Event()
    original = client.submit
    def blocked(envelope):
        entered.set()
        assert release.wait(3)
        return original(envelope)
    monkeypatch.setattr(client, 'submit', blocked)
    results = []
    thread = threading.Thread(target=lambda: results.append(submit(service)))
    thread.start()
    try:
        assert entered.wait(3)
        status, result = submit(service)
        assert status == 503 and result['error'] == 'outcome_unknown' and not result['retry_safe']
    finally:
        release.set()
        thread.join(timeout=3)
    assert results[0][0] == 202
    assert len([call for call in client.calls if call[0] == 'submit']) == 1


def test_cold_registry_project_remains_visible_without_fabricated_health(setup, monkeypatch):
    service, client, gateway = setup
    monkeypatch.setattr(gateway, 'projects_payload', lambda: {'projects': [], 'health_warming': True})
    result = service.dispatch('GET', '/api/projects')[1]
    assert result['projects'][0]['id'] == 'p1'
    assert result['projects'][0]['availability'] == 'unknown'
    assert result['projects'][0]['health'] == 'unknown'
    assert not client.calls


def test_job_object_identity_and_schema_must_match_route(setup, monkeypatch):
    service, client, _ = setup
    for response in ({'job_id': 'job_one', 'job': None},
                     {'job_id': 'job_one', 'job': {'job_id': 'job_other', 'request': {'project_id': 'p1'}}}):
        monkeypatch.setattr(client, 'get', lambda job_id: response)
        with pytest.raises(MobileGatewayError) as exc:
            service.dispatch('GET', '/api/projects/p1/jobs/job_one')
        assert exc.value.status_code == 404


def test_config_opener_receives_only_registered_project(setup):
    service, _, _ = setup
    seen = []
    service._config_opener = lambda project: seen.append(project.project_root) or 'http://127.0.0.1:12345/'
    assert service.dispatch('GET', '/api/config')[1]['available']
    assert service.dispatch('POST', '/api/projects/p1/config/open', {'path': '/etc'})[1]['url'].endswith('12345/')
    assert seen == [service.registry.default_project.project_root]


def test_websocket_upgrade_requires_session_and_exact_origin(server):
    service, _ = server
    headers = {'Upgrade': 'websocket', 'Connection': 'Upgrade', 'Sec-WebSocket-Key': 'ZmFrZS1maXh0dXJl'}
    assert request(server, 'GET', '/api/terminals/term_one/ws', headers={**headers, 'Origin': service.origin})[0] == 401
    cookie = login(server)
    assert request(server, 'GET', '/api/terminals/term_one/ws', headers={**headers, 'Cookie': cookie})[0] == 403
    assert request(server, 'GET', '/api/terminals/term_one/ws', headers={**headers, 'Cookie': cookie, 'Origin': 'http://evil.invalid'})[0] == 403


def test_non_ascii_bootstrap_is_denied_without_consuming_token(server):
    service, _ = server
    assert request(server, 'POST', '/api/session', {'token': '不是令牌'}, {'Origin': service.origin})[0] == 401
    assert login(server).startswith(service.session_cookie_name + '=')


def test_expired_cookie_is_not_an_authorization_fallback(server):
    service, _ = server
    cookie = login(server)
    with service._auth_lock:
        for digest in service._sessions:
            service._sessions[digest] = 0
    assert request(server, 'GET', '/api/projects', headers={'Cookie': cookie})[0] == 401
    assert request(server, 'GET', '/api/projects', headers={'Authorization': 'Bearer ' + service.bootstrap_token})[0] == 401


def test_separate_loopback_ports_do_not_overwrite_the_browser_session(server, tmp_path):
    service, _ = server
    first_cookie = login(server)
    second = WorkbenchService(project_registry=service.registry, assets_dir=service.assets_dir,
                              state_dir=tmp_path / 'second-state', gateway=Gateway())
    second_http = build_workbench_server(second)
    thread = threading.Thread(target=second_http.serve_forever, daemon=True)
    thread.start()
    try:
        second_cookie = login((second, second_http))
        assert first_cookie.split('=')[0] != second_cookie.split('=')[0]
        shared_host_cookies = first_cookie + '; ' + second_cookie
        assert request(server, 'GET', '/api/projects', headers={'Cookie': shared_host_cookies})[0] == 200
        assert request((second, second_http), 'GET', '/api/projects', headers={'Cookie': shared_host_cookies})[0] == 200
        assert request(server, 'GET', '/api/projects', headers={'Cookie': second_cookie})[0] == 401
    finally:
        second_http.shutdown()
        second_http.server_close()
        thread.join(timeout=3)


@pytest.mark.parametrize('body,extra_headers,status', [
    ('x' * 65537, {}, 400),
    ('{}', {'Content-Length': '-1'}, 400),
    ('{}', {'Content-Length': 'invalid'}, 400),
    ('{}', {'Content-Type': 'text/plain'}, 415),
    ('{}', {'Transfer-Encoding': 'chunked'}, 400),
    ('[]', {}, 400),
    ('{malformed', {}, 400),
])
def test_http_body_boundary_never_reaches_job_authority(server, setup, body, extra_headers, status):
    service, http = server
    _, client, _ = setup
    cookie = login(server)
    connection = HTTPConnection(*http.server_address, timeout=3)
    connection.request('POST', '/api/projects/p1/jobs', body,
                       {'Origin': service.origin, 'Cookie': cookie, 'Content-Type': 'application/json', **extra_headers})
    response = connection.getresponse()
    assert response.status == status
    response.read()
    connection.close()
    assert not any(call[0] == 'submit' for call in client.calls)


def _raw_response(http, header_lines, body=b'', *, finish_writes=False):
    import socket
    with socket.create_connection(http.server_address, timeout=3) as connection:
        connection.sendall(('\r\n'.join(header_lines) + '\r\n\r\n').encode() + body)
        if finish_writes:
            connection.shutdown(socket.SHUT_WR)
        output = b''
        while chunk := connection.recv(4096):
            output += chunk
    return int(output.split(b' ', 2)[1]), output


@pytest.mark.parametrize('duplicate', ['Host', 'Origin', 'Content-Length'])
def test_duplicate_security_headers_are_rejected(server, duplicate):
    service, http = server
    host = service.origin.removeprefix('http://')
    headers = ['POST /api/session HTTP/1.1', f'Host: {host}', f'Origin: {service.origin}',
               'Content-Type: application/json', 'Content-Length: 2']
    value = {'Host': host, 'Origin': service.origin, 'Content-Length': '2'}[duplicate]
    status, _ = _raw_response(http, [*headers, f'{duplicate}: {value}'], b'{}')
    assert status == (400 if duplicate == 'Content-Length' else 403)


def test_incomplete_body_and_inactive_body_fail_without_consuming_bootstrap(server, monkeypatch):
    service, http = server
    host = service.origin.removeprefix('http://')
    headers = ['POST /api/session HTTP/1.1', f'Host: {host}', f'Origin: {service.origin}',
               'Content-Type: application/json', 'Content-Length: 20']
    assert _raw_response(http, headers, b'{}', finish_writes=True)[0] == 400
    monkeypatch.setattr('workbench.service._HTTP_READ_TIMEOUT', .05)
    status, output = _raw_response(http, headers, b'{')
    assert status == 408 and b'request_read_timeout' in output
    assert login(server)


@pytest.mark.parametrize('receipt', [
    {'job_id': 'job_one', 'agent_name': 'buddy', 'status': 'sent'},
    {'job_id': 'job_one', 'agent_name': 'buddy', 'status': 'completed'},
    {'job_id': 'job_one', 'agent_name': 'buddy', 'status': 'unknown'},
    {'job_id': 'job_one', 'agent_name': 'other', 'status': 'queued'},
    {'job_id': 'not-a-job', 'agent_name': 'buddy', 'status': 'queued'},
])
def test_invalid_submit_receipt_is_unknown_and_not_automatically_resent(setup, monkeypatch, receipt):
    service, client, _ = setup
    original = client.submit
    def invalid(envelope):
        original(envelope)
        return receipt
    monkeypatch.setattr(client, 'submit', invalid)
    status, result = submit(service)
    assert status == 503 and result['error'] == 'outcome_unknown' and not result['retry_safe']
    assert submit(service)[1]['replayed']
    assert len([call for call in client.calls if call[0] == 'submit']) == 1


@pytest.mark.parametrize('action,receipt', [
    ('cancel', {'job_id': 'job_other', 'agent_name': 'buddy', 'status': 'cancelled'}),
    ('cancel', {'job_id': 'job_one', 'agent_name': 'buddy', 'status': 'completed'}),
    ('retry', {'job_id': 'job_one', 'agent_name': 'buddy', 'status': 'queued'}),
    ('retry', {'job_id': 'job_new', 'agent_name': 'other', 'status': 'queued'}),
    ('retry', {'job_id': 'job_new', 'agent_name': 'buddy', 'status': 'sent'}),
])
def test_mutation_receipt_must_match_exact_job_agent_and_operation(setup, monkeypatch, action, receipt):
    service, client, _ = setup
    client.state = 'failed' if action == 'retry' else 'running'
    calls = []
    def invalid(job_id):
        calls.append(job_id)
        return receipt
    monkeypatch.setattr(client, action, invalid)
    path = f'/api/projects/p1/jobs/job_one/{action}'
    assert service.dispatch('POST', path, {'idempotency_key': 'same'})[1]['error'] == 'outcome_unknown'
    assert service.dispatch('POST', path, {'idempotency_key': 'same'})[1]['replayed']
    assert calls == ['job_one']


def test_terminal_mutation_receipt_does_not_persist_job_prompt_or_reply(setup):
    service, client, _ = setup
    client.state = 'completed'
    status, result = service.dispatch('POST', '/api/projects/p1/jobs/job_one/cancel', {'idempotency_key': 'cancel'})
    assert status == 409 and result['job'] == {'job_id': 'job_one', 'status': 'completed'}
    with sqlite3.connect(service._db_path) as db:
        saved = db.execute('SELECT payload FROM receipts').fetchone()[0]
    assert 'hello' not in saved and 'partial' not in saved and 'request' not in saved


def test_receipt_write_failure_after_rpc_keeps_pending_and_is_never_resent(setup, monkeypatch):
    from contextlib import contextmanager
    service, client, _ = setup
    original = service._db
    count = 0
    @contextmanager
    def fail_receipt_write():
        nonlocal count
        count += 1
        if count == 2:
            raise sqlite3.OperationalError('disk full after submit committed')
        with original() as db:
            yield db
    monkeypatch.setattr(service, '_db', fail_receipt_write)
    status, result = submit(service)
    assert status == 503 and result == {'schema_version': 1, 'error': 'outcome_unknown', 'idempotency_key': 'key', 'retry_safe': False}
    assert submit(service)[1]['error'] == 'outcome_unknown'
    assert len([call for call in client.calls if call[0] == 'submit']) == 1
    with original() as db:
        assert db.execute('SELECT status FROM receipts').fetchone() == (None,)
