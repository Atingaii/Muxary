from __future__ import annotations

from http.client import HTTPConnection
from io import StringIO
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from ccbd.socket_client import CcbdClientError
from mobile_gateway import MobileGatewayError, MobileGatewayProject, MobileGatewayProjectRegistry
from project.ids import compute_project_id
from workbench import WorkbenchService, build_workbench_server
from workbench import cli


class Client:
    def __init__(self, root):
        self.root = root
        self.project_id = compute_project_id(root)
        self.state = 'mounted'
        self.fail = False
        self.submitted = []

    def with_timeout(self, timeout):
        assert timeout <= 3
        return self

    def project_view(self, **kwargs):
        if self.fail:
            raise CcbdClientError('private socket diagnostic')
        return {'schema_version': 1, 'view': {
            'project': {'id': self.project_id, 'root': str(self.root)},
            'ccbd': {'state': self.state, 'health': 'healthy'},
            'namespace': {'epoch': 1}, 'agents': [{'name': 'buddy', 'provider': 'codebuddy'}],
        }}

    def submit(self, envelope):
        self.submitted.append(envelope)
        return {'job_id': 'job_fixture', 'agent_name': 'buddy', 'status': 'queued'}


def entry(root):
    root.mkdir(exist_ok=True)
    (root / '.ccb').mkdir(exist_ok=True)
    client = Client(root)
    return MobileGatewayProject(client.project_id, root, lambda: client), client


@pytest.fixture
def fixture(tmp_path):
    old, old_client = entry(tmp_path / 'old')
    new, new_client = entry(tmp_path / 'new')
    assets = tmp_path / 'assets'
    assets.mkdir()
    (assets / 'index.html').write_text('fixture')
    current = [MobileGatewayProjectRegistry([old])]
    calls = []

    def start(root):
        calls.append(root)
        current[0] = MobileGatewayProjectRegistry([old, new])
        return 0

    service = WorkbenchService(
        project_registry=current[0], project_registry_provider=lambda: current[0],
        project_opener=start, assets_dir=assets, state_dir=tmp_path / 'state')
    yield SimpleNamespace(service=service, old=old, new=new, old_client=old_client,
                          new_client=new_client, calls=calls, current=current)
    service.close()


def open_project(fixture, path=None, **extra):
    return fixture.service.dispatch('POST', '/api/projects/open', {'path': str(path or fixture.new.project_root), **extra})


def test_open_refreshes_both_service_and_real_gateway_and_submit(fixture):
    status, result = open_project(fixture)
    assert status == 200
    assert result == {'schema_version': 1, 'project_id': fixture.new.project_id,
                      'root': str(fixture.new.project_root), 'status': 'ready'}
    assert fixture.calls == [fixture.new.project_root]
    assert fixture.service._project(fixture.new.project_id) is fixture.new
    assert fixture.service.gateway._require_project(fixture.new.project_id) is fixture.new
    status, payload = fixture.service.dispatch('GET', f'/api/projects/{fixture.new.project_id}/view')
    assert status == 200 and payload['view']['project']['id'] == fixture.new.project_id
    status, receipt = fixture.service.dispatch('POST', f'/api/projects/{fixture.new.project_id}/jobs',
        {'agent': 'buddy', 'body': 'fixture', 'idempotency_key': 'new-project'})
    assert status == 202 and receipt['job_id'] == 'job_fixture'
    assert fixture.new_client.submitted[0].project_id == fixture.new.project_id


def test_already_live_does_not_start_or_restart(fixture):
    assert open_project(fixture, fixture.old.project_root)[0] == 200
    assert fixture.calls == []


def test_canonical_symlink_and_subdirectory_reuse_project(fixture, tmp_path):
    child = fixture.old.project_root / 'src'
    child.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(child, target_is_directory=True)
    assert open_project(fixture, alias)[1]['root'] == str(fixture.old.project_root)
    assert fixture.calls == []


def binding(path, owner, **changes):
    path.mkdir()
    record = {'schema_version': 2, 'record_type': 'workspace_binding',
              'target_project': str(owner.project_root), 'project_id': owner.project_id,
              'agent_name': 'buddy', 'workspace_mode': 'git-worktree',
              'workspace_path': str(path), 'branch_name': 'fixture'}
    (path / '.ccb-workspace.json').write_text(json.dumps({**record, **changes}))


def test_managed_worktree_maps_owner_without_duplicate_start(fixture, tmp_path):
    worktree = tmp_path / 'worktree'
    binding(worktree, fixture.old)
    assert open_project(fixture, worktree)[1]['project_id'] == fixture.old.project_id
    assert fixture.calls == []


def test_cold_managed_worktree_starts_owner_not_workspace(fixture, tmp_path):
    worktree = tmp_path / 'worktree'
    binding(worktree, fixture.new)
    assert open_project(fixture, worktree)[1]['root'] == str(fixture.new.project_root)
    assert fixture.calls == [fixture.new.project_root]


@pytest.mark.parametrize('change', [{'project_id': 'foreign'}, {'workspace_path': '/tmp'}, {'schema_version': 1}])
def test_forged_or_stale_workspace_binding_is_rejected(fixture, tmp_path, change):
    path = tmp_path / 'worktree'
    binding(path, fixture.old, **change)
    with pytest.raises(MobileGatewayError) as error:
        open_project(fixture, path)
    assert error.value.status_code == 400
    assert fixture.calls == []


@pytest.mark.parametrize('path', ['', '.', 'relative/path', None, 12, '/definitely/no/project', '/tmp/abc\x00def', '/tmp/a\nb'])
def test_invalid_paths_never_start(fixture, path):
    with pytest.raises(MobileGatewayError) as error:
        fixture.service.dispatch('POST', '/api/projects/open', {'path': path})
    assert error.value.status_code == 400
    assert fixture.calls == []


def test_unknown_arguments_are_not_forwarded_to_cli(fixture):
    with pytest.raises(MobileGatewayError) as error:
        open_project(fixture, force=True)
    assert error.value.status_code == 400
    assert fixture.calls == []


def test_missing_opener_is_unavailable_not_fake_success(fixture):
    fixture.service._project_opener = None
    status, result = open_project(fixture)
    assert status == 503 and result['error'] == 'project_open_unavailable'
    assert fixture.calls == []


@pytest.mark.parametrize('outcome, expected', [(17, 503), (subprocess.TimeoutExpired('ccb', 45), 504), (OSError('private'), 503)])
def test_failure_or_timeout_visible_and_never_retried(fixture, outcome, expected):
    def fail(path):
        fixture.calls.append(path)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome
    fixture.service._project_opener = fail
    status, payload = open_project(fixture)
    assert status == expected and payload['outcome_unknown'] and payload['refresh_required']
    assert len(fixture.calls) == 1 and 'private' not in json.dumps(payload)
    assert fixture.service._project_open_lock.acquire(blocking=False)
    fixture.service._project_open_lock.release()


def test_unreachable_registered_project_is_not_automatically_restarted(fixture):
    fixture.old_client.fail = True
    status, result = open_project(fixture, fixture.old.project_root)
    assert status == 503 and result['refresh_required']
    assert fixture.calls == []


def test_unknown_start_is_not_repeated_but_live_confirmation_can_recover(fixture):
    original = fixture.service._project_opener
    def timeout(path):
        fixture.calls.append(path)
        raise subprocess.TimeoutExpired('ccb', 45)
    fixture.service._project_opener = timeout
    assert open_project(fixture)[0] == 504
    assert open_project(fixture)[0] == 409
    assert fixture.calls == [fixture.new.project_root]
    fixture.current[0] = MobileGatewayProjectRegistry([fixture.old, fixture.new])
    assert open_project(fixture)[0] == 200
    assert fixture.calls == [fixture.new.project_root]
    assert fixture.new.project_root not in fixture.service._uncertain_project_roots
    fixture.service._project_opener = original


@pytest.mark.parametrize('kind', ['symlink', 'fifo', 'oversize'])
def test_workspace_marker_special_or_unbounded_file_is_rejected(fixture, tmp_path, kind):
    path = tmp_path / 'workspace'
    path.mkdir()
    marker = path / '.ccb-workspace.json'
    if kind == 'symlink':
        marker.symlink_to(tmp_path / 'nonexistent')
    elif kind == 'fifo':
        os.mkfifo(marker)
    else:
        marker.write_text('x' * 65537)
    with pytest.raises(MobileGatewayError) as error:
        open_project(fixture, path)
    assert error.value.status_code == 400 and fixture.calls == []


@pytest.mark.parametrize('wrong', ['root', 'id', 'unmounted'])
def test_start_success_requires_fresh_confirmed_identity_and_mount(fixture, wrong):
    if wrong == 'root':
        fixture.new_client.root = fixture.old.project_root
    elif wrong == 'id':
        fixture.new_client.project_id = 'foreign'
    else:
        fixture.new_client.state = 'unmounted'
    status, result = open_project(fixture)
    assert status == 503 and result['refresh_required'] and result['outcome_unknown']


def test_slow_start_does_not_lock_other_requests_and_concurrent_open_conflicts(fixture):
    started, release = threading.Event(), threading.Event()
    original = fixture.service._project_opener
    def slow(path):
        started.set()
        assert release.wait(5)
        return original(path)
    fixture.service._project_opener = slow
    results = []
    thread = threading.Thread(target=lambda: results.append(open_project(fixture)))
    thread.start()
    try:
        assert started.wait(2)
        before = time.monotonic()
        assert fixture.service.dispatch('GET', '/api/session')[0] == 200
        assert fixture.service._project(fixture.old.project_id) is fixture.old
        assert open_project(fixture)[0] == 409
        assert open_project(fixture, fixture.old.project_root)[0] == 409
        assert time.monotonic() - before < 0.5
    finally:
        release.set()
        thread.join(5)
    assert results[0][0] == 200 and len(fixture.calls) == 1


def test_late_old_discovery_cannot_replace_registry_confirmed_by_open(fixture):
    captured, release = threading.Event(), threading.Event()
    old = fixture.current[0]
    def discover():
        snapshot = fixture.current[0]
        if threading.current_thread().name == 'old-discovery':
            captured.set()
            assert release.wait(5)
        return snapshot
    fixture.service._project_registry_provider = discover
    thread = threading.Thread(target=fixture.service._refresh_registry, name='old-discovery')
    thread.start()
    try:
        assert captured.wait(2)
        assert fixture.service._registry_snapshot() is old
        assert open_project(fixture)[0] == 200
        assert fixture.service._project(fixture.new.project_id) is fixture.new
    finally:
        release.set()
        thread.join(5)
    assert fixture.service._project(fixture.new.project_id) is fixture.new
    assert fixture.service.gateway._require_project(fixture.new.project_id) is fixture.new


def test_stale_preflight_candidate_cannot_start_project_already_published_live(fixture):
    captured, release = threading.Event(), threading.Event()
    opening_discoveries = 0
    results = []

    def discover():
        nonlocal opening_discoveries
        snapshot = fixture.current[0]
        if threading.current_thread().name == 'opening-project':
            opening_discoveries += 1
            if opening_discoveries == 1:
                captured.set()
                assert release.wait(5)
        return snapshot

    fixture.service._project_registry_provider = discover
    opening = threading.Thread(target=lambda: results.append(open_project(fixture)), name='opening-project')
    opening.start()
    try:
        assert captured.wait(2)
        fixture.current[0] = MobileGatewayProjectRegistry([fixture.old, fixture.new])
        fixture.service._refresh_registry()
        assert fixture.service._project(fixture.new.project_id) is fixture.new
        assert fixture.service._project_is_ready(fixture.new, fixture.new.project_root)
    finally:
        release.set()
        opening.join(5)
    assert not opening.is_alive() and results[0][0] == 200, results
    assert fixture.calls == [], 'a superseded preflight must not launch an already live project'
    assert fixture.service.gateway._require_project(fixture.new.project_id) is fixture.new


@pytest.mark.parametrize('pending_has_new_project', [False, True])
def test_open_confirms_own_fresh_discovery_while_later_read_is_pending(fixture, pending_has_new_project):
    old = fixture.current[0]
    new = MobileGatewayProjectRegistry([fixture.old, fixture.new])
    fresh_captured, release_fresh = threading.Event(), threading.Event()
    pending_started, release_pending = threading.Event(), threading.Event()
    opening_discoveries = 0
    results = {}

    def discover():
        nonlocal opening_discoveries
        if threading.current_thread().name == 'opening-project':
            opening_discoveries += 1
            if opening_discoveries == 1:
                return old
            assert opening_discoveries == 2
            fresh_captured.set()
            assert release_fresh.wait(5)
            return new
        assert threading.current_thread().name == 'pending-projects-read'
        snapshot = new if pending_has_new_project else old
        pending_started.set()
        assert release_pending.wait(5)
        return snapshot

    fixture.service._project_registry_provider = discover
    opening = threading.Thread(
        target=lambda: results.update(open=open_project(fixture)), name='opening-project')
    pending = threading.Thread(
        target=lambda: results.update(read=fixture.service.dispatch('GET', '/api/projects')),
        name='pending-projects-read')
    opening.start()
    try:
        assert fresh_captured.wait(2)
        pending.start()
        assert pending_started.wait(2)
        release_fresh.set()
        opening.join(3)
        assert not opening.is_alive(), 'open must not wait for unrelated discovery'
        assert results['open'][0] == 200, results['open']
        assert fixture.calls == [fixture.new.project_root]
        assert fixture.service._project(fixture.new.project_id) is fixture.new
        assert fixture.service.gateway._require_project(fixture.new.project_id) is fixture.new
    finally:
        release_fresh.set()
        release_pending.set()
        opening.join(5)
        if pending.ident is not None:
            pending.join(5)
    assert not pending.is_alive()
    assert results['read'][0] == 200
    assert fixture.service._project(fixture.new.project_id) is fixture.new
    assert fixture.service.gateway._require_project(fixture.new.project_id) is fixture.new


def test_confirmed_project_merge_preserves_newer_unrelated_discovery(fixture, tmp_path):
    other, _ = entry(tmp_path / 'other')
    old = fixture.current[0]
    candidate = MobileGatewayProjectRegistry([fixture.old, fixture.new])
    unrelated = MobileGatewayProjectRegistry([fixture.old, other])
    checking, release = threading.Event(), threading.Event()
    original_view = fixture.new_client.project_view
    opening_discoveries = 0
    results = []

    def discover():
        nonlocal opening_discoveries
        if threading.current_thread().name != 'opening-project':
            return unrelated
        opening_discoveries += 1
        return old if opening_discoveries == 1 else candidate

    def confirm(**kwargs):
        payload = original_view(**kwargs)
        checking.set()
        assert release.wait(5)
        return payload

    fixture.service._project_registry_provider = discover
    fixture.new_client.project_view = confirm
    opening = threading.Thread(target=lambda: results.append(open_project(fixture)), name='opening-project')
    opening.start()
    try:
        assert checking.wait(2)
        fixture.service._refresh_registry()
        assert fixture.service._project(other.project_id) is other
    finally:
        release.set()
        opening.join(5)
    assert not opening.is_alive() and results[0][0] == 200, results
    for project in (fixture.old, fixture.new, other):
        assert fixture.service._project(project.project_id) is project
        assert fixture.service.gateway._require_project(project.project_id) is project


def test_real_http_auth_and_origin_before_project_open(fixture):
    server = build_workbench_server(fixture.service, host='127.0.0.1', port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = HTTPConnection(*server.server_address, timeout=5)
    def post(path, body, **headers):
        connection.request('POST', path, json.dumps(body), {'Content-Type': 'application/json', **headers})
        response = connection.getresponse()
        result = response.status, json.loads(response.read()), response.getheader('Set-Cookie')
        return result
    try:
        origin = fixture.service.origin
        assert post('/api/projects/open', {'path': str(fixture.new.project_root)}, Origin=origin)[0] == 401
        _, _, cookie = post('/api/session', {'token': fixture.service.bootstrap_token}, Origin=origin)
        assert post('/api/projects/open', {'path': str(fixture.new.project_root)}, Cookie=cookie)[0] == 403
        assert post('/api/projects/open', {'path': str(fixture.new.project_root)}, Cookie=cookie, Origin='https://evil.example')[0] == 403
        assert fixture.calls == []
        assert post('/api/projects/open', {'path': str(fixture.new.project_root)}, Cookie=cookie, Origin=origin)[0] == 200
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(3)


def test_cli_start_is_fixed_safe_bounded_and_has_no_inherited_pipe_reader(monkeypatch, tmp_path):
    calls = []
    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        kwargs['stdout'].write(b'fixture output')
        kwargs['stderr'].write(b'fixture error')
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(cli.subprocess, 'run', run)
    out, err = StringIO(), StringIO()
    assert cli._start_project(tmp_path, script_root=tmp_path, stdout=out, stderr=err) == 0
    argv, options = calls[0]
    assert argv == [str(tmp_path / 'ccb'), '--safe']
    assert options['cwd'] == tmp_path and options['timeout'] == 45
    assert not options.get('shell') and not options.get('capture_output')
    assert options['stdout'] != subprocess.PIPE and options['stderr'] != subprocess.PIPE
    assert 'fixture output' in out.getvalue() and 'fixture error' in err.getvalue()


def test_cli_start_timeout_does_not_wait_on_or_kill_descendant(monkeypatch, tmp_path):
    descendant_pid = tmp_path / 'descendant.pid'
    launcher = tmp_path / 'ccb'
    launcher.write_text(f'''#!{sys.executable}
import os, subprocess, sys, time
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
open({str(descendant_pid)!r}, 'w').write(str(child.pid))
print('before timeout', flush=True)
time.sleep(30)
''')
    launcher.chmod(0o755)
    monkeypatch.setattr(cli, '_PROJECT_START_TIMEOUT', 0.3)
    out = StringIO()
    before = time.monotonic()
    pid = None
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            cli._start_project(tmp_path, script_root=tmp_path, stdout=out, stderr=StringIO())
        assert time.monotonic() - before < 3
        pid = int(descendant_pid.read_text())
        os.kill(pid, 0)  # Only the launcher, not the CCB-owned descendant, ended.
        assert 'before timeout' in out.getvalue()
    finally:
        if pid is None and descendant_pid.exists():
            pid = int(descendant_pid.read_text())
        if pid is not None:
            os.kill(pid, 15)  # Exact child created by this disposable launcher.


def test_cli_start_output_is_capped(monkeypatch, tmp_path):
    def run(argv, **kwargs):
        kwargs['stdout'].write(b'x' * 80000)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(cli.subprocess, 'run', run)
    out = StringIO()
    assert cli._start_project(tmp_path, script_root=tmp_path, stdout=out, stderr=StringIO()) == 0
    assert out.getvalue() == 'x' * 65536 + '\n[Muxary startup output truncated]\n'


def test_cli_explicit_workspace_reuses_owner_registry(monkeypatch, fixture, tmp_path):
    root = tmp_path / 'source'
    assets = root / 'assets' / 'workbench'
    assets.mkdir(parents=True)
    (assets / 'index.html').write_text('fixture')
    workspace = tmp_path / 'workspace'
    binding(workspace, fixture.old)
    monkeypatch.setattr(cli, '_project_registry_or_none', lambda: fixture.current[0])
    monkeypatch.setattr(cli, '_start_project', lambda *a, **k: pytest.fail('must not duplicate owner'))
    monkeypatch.setattr('workbench.service.WorkbenchService', lambda **kwargs: SimpleNamespace(bootstrap_token='fixture', close=lambda: None))
    class Server:
        server_address = ('127.0.0.1', 12345)
        def serve_forever(self):
            raise KeyboardInterrupt
        def server_close(self):
            pass
    monkeypatch.setattr('workbench.service.build_workbench_server', lambda *a, **k: Server())
    assert cli.run_muxary(['--project', str(workspace), '--no-open'], script_root=root, cwd=tmp_path, stdout=StringIO()) == 0


@pytest.mark.ccb_lifecycle_smoke
def test_open_real_ccb_then_submit_native_and_terminal(tmp_path, phase2_runtime_owner):
    if not shutil.which('tmux'):
        pytest.skip('tmux required')
    from ccbd.socket_client import CcbdClient
    from storage.paths import PathLayout

    old, _ = entry(tmp_path / 'old')
    project = tmp_path / 'p'
    config = project / '.ccb' / 'ccb.config'
    config.parent.mkdir(parents=True)
    config.write_text('buddy:codebuddy\n')
    phase2_runtime_owner.track(project)
    assets = tmp_path / 'a'
    assets.mkdir()
    (assets / 'index.html').write_text('fixture')
    initial = MobileGatewayProjectRegistry([old])
    source = Path(__file__).resolve().parents[1]
    opened = []

    def registry():
        layout = PathLayout(project)
        if not layout.ccbd_socket_path.exists():
            return initial
        return MobileGatewayProjectRegistry([old, MobileGatewayProject(
            layout.project_id, project, lambda: CcbdClient(layout.ccbd_socket_path))])

    def start(root):
        opened.append(root)
        return cli._start_project(root, script_root=source, stdout=StringIO(), stderr=StringIO())

    service = WorkbenchService(project_registry=initial, project_registry_provider=registry,
                              project_opener=start, assets_dir=assets, state_dir=tmp_path / 's')
    server = build_workbench_server(service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    cookie = ''
    def call(method, path, body=None):
        connection = HTTPConnection(*server.server_address, timeout=50)
        headers = {'Origin': service.origin, 'Cookie': cookie}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        connection.request(method, path, json.dumps(body) if body is not None else None, headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read()), response.getheader('Set-Cookie')
        connection.close()
        return result
    try:
        _, _, cookie = call('POST', '/api/session', {'token': service.bootstrap_token})
        status, result, _ = call('POST', '/api/projects/open', {'path': str(project)})
        assert status == 200, result
        prefix = f"/api/projects/{result['project_id']}"
        assert opened == [project]
        assert call('POST', '/api/projects/open', {'path': str(project)})[0] == 200
        assert opened == [project], 'live project must never be restarted'
        status, payload, _ = call('GET', prefix + '/view')
        assert status == 200 and payload['view']['project']['root'] == str(project), payload
        epoch = payload['view']['namespace']['epoch']
        status, receipt, _ = call('POST', prefix + '/jobs', {
            'agent': 'buddy', 'body': 'Web open fixture', 'idempotency_key': 'open-fixture', 'namespace_epoch': epoch})
        assert status == 202 and receipt['job_id'].startswith('job_'), receipt
        status, native, _ = call('GET', prefix + '/agents/buddy/provider-control')
        assert status == 200, native
        status, terminal, _ = call('POST', prefix + '/terminals', {
            'target': {'kind': 'agent', 'agent': 'buddy'}, 'namespace_epoch': epoch,
            'geometry': {'cols': 80, 'rows': 24}})
        assert status == 201 and terminal['terminal_id'].startswith('term_'), terminal
        assert terminal['websocket_url'].startswith(service.origin.replace('http:', 'ws:'))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(3)
