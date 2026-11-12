from __future__ import annotations

from io import StringIO
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from workbench import cli
from workbench import service


def _root(tmp_path):
    root = tmp_path / 'source'
    assets = root / 'assets' / 'workbench'
    assets.mkdir(parents=True)
    (assets / 'index.html').write_text('fixture')
    (root / 'VERSION').write_text('0.1.0\n')
    return root


def _registry(project):
    entry = SimpleNamespace(project_id='fixture', project_root=project)
    return SimpleNamespace(projects=lambda: (entry,))


def _fake_server(monkeypatch):
    calls = {}
    class Service:
        def __init__(self, **kwargs):
            calls['service'] = kwargs
            self.bootstrap_token = 'fixture-token'
        def close(self):
            calls['service_closed'] = True
    class Server:
        server_address = ('127.0.0.1', 43210)
        def serve_forever(self):
            calls['served'] = True
            raise KeyboardInterrupt
        def server_close(self):
            calls['closed'] = True
    def build(svc, **kwargs):
        calls['bind'] = kwargs
        return Server()
    monkeypatch.setattr(service, 'WorkbenchService', Service)
    monkeypatch.setattr(service, 'build_workbench_server', build)
    return calls


def test_version_is_muxary_local_identity(tmp_path):
    out = StringIO()
    assert cli.run_muxary(['--version'], script_root=_root(tmp_path), stdout=out) == 0
    assert out.getvalue() == 'Muxary 0.1.0\n'


@pytest.mark.parametrize('tokens, forwarded', [
    (['tui', '--safe'], ['--safe']),
    (['tui', '--project', '/fixture', 'ask', 'buddy', 'body'], ['--project', '/fixture', 'ask', 'buddy', 'body']),
    *[(tokens, tokens) for tokens in [
        ['ask', 'buddy', 'fixture'], ['watch', 'job_fixture'], ['ping', 'ccbd'],
        ['doctor'], ['config', 'ui', '--no-open'], ['config', 'approve-commands'],
        ['clear', 'buddy'], ['compact', 'buddy'], ['reload'], ['restart'],
        ['kill'], ['update', '--providers', 'check'],
    ]],
])
def test_tui_and_compatibility_commands_delegate_without_rewriting(monkeypatch, tmp_path, tokens, forwarded):
    calls = []
    monkeypatch.setattr(cli.subprocess, 'call', lambda argv, **kwargs: calls.append((argv, kwargs)) or 17)
    root = _root(tmp_path)
    assert cli.run_muxary(tokens, script_root=root, cwd=tmp_path) == 17
    assert calls[0][0] == [str(root / 'ccb'), *forwarded]
    assert calls[0][1]['env']['CCB_SOURCE_RUNTIME_OK'] == '1'


@pytest.mark.parametrize('tokens', [[], ['web']])
def test_default_web_reuses_registry_and_closes_loopback_server(monkeypatch, tmp_path, tokens):
    root = _root(tmp_path)
    registry = _registry(tmp_path)
    monkeypatch.setattr(cli, '_project_registry_or_none', lambda: registry)
    monkeypatch.setattr(cli, '_start_project', lambda *a, **k: pytest.fail('running registry must not restart providers'))
    opened = []
    monkeypatch.setattr(cli.webbrowser, 'open', lambda url: opened.append(url) or True)
    calls = _fake_server(monkeypatch)
    out = StringIO()
    assert cli.run_muxary(tokens, script_root=root, cwd=tmp_path, stdout=out) == 0
    assert calls['service']['project_registry'] is registry
    assert calls['bind'] == {'host': '127.0.0.1', 'port': 0}
    assert calls['served'] and calls['closed']
    assert opened == ['http://127.0.0.1:43210/#token=fixture-token']
    assert opened[0] in out.getvalue()


def test_no_open_only_prints_local_url(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, '_project_registry_or_none', lambda: _registry(tmp_path))
    monkeypatch.setattr(cli.webbrowser, 'open', lambda url: pytest.fail('no-open must not launch browser'))
    calls = _fake_server(monkeypatch)
    assert cli.run_muxary(['--no-open', '--port', '1234'], script_root=_root(tmp_path), cwd=tmp_path, stdout=StringIO()) == 0
    assert calls['bind']['port'] == 1234


def test_missing_assets_fails_before_cold_start(monkeypatch, tmp_path):
    monkeypatch.setattr(cli, '_start_project', lambda *a, **k: pytest.fail('missing UI must not start providers'))
    err = StringIO()
    assert cli.run_muxary([], script_root=tmp_path, stderr=err) == 1
    assert 'Web assets are missing' in err.getvalue()


def test_cold_start_reuses_ccb_and_reload_registry(monkeypatch, tmp_path):
    root = _root(tmp_path)
    registries = iter([None, _registry(tmp_path)])
    monkeypatch.setattr(cli, '_project_registry_or_none', lambda: next(registries))
    started = []
    monkeypatch.setattr(cli, '_start_project', lambda path, **kwargs: started.append(path) or 0)
    _fake_server(monkeypatch)
    assert cli.run_muxary(['--no-open'], script_root=root, cwd=tmp_path, stdout=StringIO()) == 0
    assert started == [tmp_path]


def test_cold_start_is_manual_permission_and_detached(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(cli.subprocess, 'run', lambda argv, **kwargs: calls.append((argv, kwargs)) or SimpleNamespace(returncode=0, stdout='', stderr=''))
    assert cli._start_project(tmp_path, script_root=tmp_path, stdout=StringIO(), stderr=StringIO()) == 0
    assert calls[0][0] == [str(tmp_path / 'ccb'), '--safe']
    assert calls[0][1]['cwd'] == tmp_path
    assert calls[0][1]['env']['CCB_NO_ATTACH'] == '1'
    assert calls[0][1]['env']['CCB_SOURCE_RUNTIME_OK'] == '1'


def test_explicit_project_must_be_registered_after_successful_start(monkeypatch, tmp_path):
    root = _root(tmp_path)
    registries = iter([_registry(root), _registry(root)])
    monkeypatch.setattr(cli, '_project_registry_or_none', lambda: next(registries))
    monkeypatch.setattr(cli, '_start_project', lambda *a, **k: 0)
    err = StringIO()
    assert cli.run_muxary(['--project', str(tmp_path)], script_root=root, cwd=tmp_path, stderr=err) == 1
    assert 'did not register' in err.getvalue()


@pytest.mark.parametrize('port', ['-1', '65536'])
def test_invalid_port_is_rejected_without_start(tmp_path, port):
    assert cli.run_muxary(['--port', port], script_root=_root(tmp_path), stderr=StringIO()) == 2


def test_config_ui_reuses_existing_editor_and_closes_owned_threads(monkeypatch, tmp_path):
    import threading
    stopped = threading.Event()
    handles = []
    class Handle:
        url = 'http://127.0.0.1:43567/?token=fixture'
        def serve_forever(self):
            stopped.wait(5)
        def close(self):
            stopped.set()
    monkeypatch.setattr(cli, 'CliContextBuilder', lambda: SimpleNamespace(build=lambda *a, **k: 'existing-context'))
    monkeypatch.setattr(cli, 'prepare_config_ui', lambda context, command: handles.append((context, command)) or Handle())
    sessions = cli._ConfigUiSessions()
    project = SimpleNamespace(project_id='fixture', project_root=tmp_path)
    try:
        assert sessions.open(project) == Handle.url
        assert sessions.open(project) == Handle.url
        assert len(handles) == 1
        assert handles[0][0] == 'existing-context'
        assert handles[0][1].no_open and handles[0][1].port == 0
    finally:
        sessions.close()
    assert stopped.is_set()
