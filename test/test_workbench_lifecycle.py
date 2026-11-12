"""Browser HTTP/WS -> actual ccbd/tmux -> independent CLI stubs, no model API."""
from __future__ import annotations

import base64
from http.client import HTTPConnection
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time

import pytest

from ccbd.socket_client import CcbdClient
from mobile_gateway import MobileGatewayProject, MobileGatewayProjectRegistry
from storage.paths import PathLayout
from workbench import WorkbenchService, build_workbench_server
from test_mobile_gateway_service import _websocket_send_json, _websocket_read_until


@pytest.mark.ccb_lifecycle_smoke
def test_browser_jobs_and_terminal_reuse_real_control_plane(tmp_path, phase2_runtime_owner):
    if not shutil.which('tmux'):
        pytest.skip('tmux required')
    project = tmp_path / 'workbench-project'
    config = project / '.ccb' / 'ccb.config'
    config.parent.mkdir(parents=True)
    config.write_text('buddy:codebuddy,coder:codex\n')
    phase2_runtime_owner.track(project)
    source_root = Path(__file__).resolve().parents[1]
    boot = subprocess.run([sys.executable, str(source_root / 'ccb.py'), '--safe'], cwd=project,
                          env={**os.environ, 'CCB_NO_ATTACH': '1', 'CCB_SOURCE_RUNTIME_OK': '1'},
                          capture_output=True, text=True, timeout=40)
    assert boot.returncode == 0, (boot.stdout, boot.stderr)
    layout = PathLayout(project)
    registry = MobileGatewayProjectRegistry([
        MobileGatewayProject(layout.project_id, project, lambda: CcbdClient(layout.ccbd_socket_path))])
    assets = tmp_path / 'assets'
    assets.mkdir()
    (assets / 'index.html').write_text('<html>fixture</html>')
    service = WorkbenchService(project_registry=registry, assets_dir=assets, state_dir=tmp_path / 'web-state')
    server = build_workbench_server(service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    cookie = ''

    def call(method, path, body=None):
        connection = HTTPConnection(*server.server_address, timeout=8)
        headers = {'Origin': service.origin, 'Cookie': cookie}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        connection.request(method, path, json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse()
        status, headers, payload = response.status, dict(response.getheaders()), json.loads(response.read())
        connection.close()
        return status, headers, payload

    try:
        status, headers, _ = call('POST', '/api/session', {'token': service.bootstrap_token})
        assert status == 200
        cookie = headers['Set-Cookie'].split(';')[0]
        prefix = f'/api/projects/{layout.project_id}'
        status, _, payload = call('GET', prefix + '/view')
        assert status == 200, payload
        epoch = payload['view']['namespace']['epoch']
        job_ids = {}
        for agent in ('buddy', 'coder'):
            status, _, receipt = call('POST', prefix + '/jobs', {
                'agent': agent, 'body': 'browser contract fixture', 'idempotency_key': f'fixture-{agent}',
                'namespace_epoch': epoch})
            assert status == 202 and receipt['job_id'].startswith('job_'), receipt
            assert receipt['status'] != 'completed'
            job_ids[agent] = receipt['job_id']
        deadline = time.monotonic() + 16
        for agent, job_id in job_ids.items():
            while time.monotonic() < deadline:
                status, _, watched = call('GET', prefix + f'/jobs/{job_id}/watch?cursor=0')
                assert status == 200, watched
                assert watched['status'] not in {'failed', 'incomplete'}, watched
                if watched['terminal']:
                    assert watched['status'] == 'completed', watched
                    assert 'stub reply for' in watched['reply']
                    break
                time.sleep(.1)
            else:
                raise AssertionError(watched)
            status, _, result = call('GET', prefix + f'/jobs/{job_id}')
            assert status == 200 and result['job']['request']['project_id'] == layout.project_id
            assert result['job']['provider'] == ('codebuddy' if agent == 'buddy' else 'codex')
            status, _, history = call('GET', prefix + f'/jobs?agent={agent}')
            assert status == 200 and job_id in {item['job_id'] for item in history['jobs']}, history
            status, _, result = call('POST', prefix + f'/jobs/{job_id}/cancel', {'idempotency_key': f'cancel-{agent}'})
            assert status == 409 and result['job']['status'] == 'completed'

        # Exercise the real mutation RPC receipts and retry lineage, not a BFF
        # mock that could accidentally accept a fabricated "sent" response.
        status, _, pending = call('POST', prefix + '/jobs', {
            'agent': 'buddy', 'body': 'cancel and retry browser fixture',
            'idempotency_key': 'fixture-cancellable', 'namespace_epoch': epoch})
        assert status == 202, pending
        cancelled_job = pending['job_id']
        status, _, cancelled = call('POST', prefix + f'/jobs/{cancelled_job}/cancel', {'idempotency_key': 'fixture-cancel'})
        assert status == 202 and cancelled['job_id'] == cancelled_job and cancelled['status'] == 'cancelled', cancelled
        status, _, retried = call('POST', prefix + f'/jobs/{cancelled_job}/retry', {'idempotency_key': 'fixture-retry'})
        assert status == 202 and retried['job_id'] != cancelled_job and retried['status'] in {'accepted', 'queued', 'running'}, retried
        deadline = time.monotonic() + 16
        while time.monotonic() < deadline:
            status, _, watched = call('GET', prefix + f"/jobs/{retried['job_id']}/watch?cursor=0")
            assert status == 200 and watched['status'] not in {'failed', 'incomplete'}, watched
            if watched['terminal']:
                assert watched['status'] == 'completed' and 'stub reply for' in watched['reply'], watched
                break
            time.sleep(.1)
        else:
            raise AssertionError(watched)

        status, _, terminal = call('POST', prefix + '/terminals', {
            'namespace_epoch': epoch, 'target': {'kind': 'agent', 'agent': 'buddy'},
            'geometry': {'columns': 100, 'rows': 30}})
        assert status == 201, terminal
        host, port = server.server_address
        with socket.create_connection((host, port), timeout=4) as sock:
            key = base64.b64encode(b'workbench-fixture').decode()
            sock.sendall((f"GET /api/terminals/{terminal['terminal_id']}/ws HTTP/1.1\r\n"
                          f'Host: {host}:{port}\r\nOrigin: {service.origin}\r\nCookie: {cookie}\r\n'
                          'Upgrade: websocket\r\nConnection: Upgrade\r\n'
                          f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
            response = b''
            while b'\r\n\r\n' not in response:
                response += sock.recv(1)
            assert b' 101 ' in response.split(b'\r\n', 1)[0]
            _websocket_send_json(sock, {'type': 'open', 'terminal_id': terminal['terminal_id'], 'token': terminal['terminal_token']})
            opened = _websocket_read_until(sock, 'open')
            assert opened['terminal_id'] == terminal['terminal_id']
            output = _websocket_read_until(sock, 'output')
            assert output['type'] == 'output'
            _websocket_send_json(sock, {'type': 'closed', 'reason': 'client_closed'})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
