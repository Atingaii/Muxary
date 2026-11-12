from __future__ import annotations

import subprocess
import json
from http.client import HTTPConnection
from pathlib import Path
import os
import sys
import threading
import time

import pytest

from agents.models import AgentSpec, PermissionMode, QueuePolicy, RestoreMode, RuntimeMode, WorkspaceMode
from agents.store import AgentSpecStore
from mobile_gateway import MobileGatewayError, MobileGatewayProject, MobileGatewayProjectRegistry
from storage.paths import PathLayout
from workbench import WorkbenchService, build_workbench_server


def git(root: Path, *args: str) -> str:
    return subprocess.run(['git', '-C', str(root), *args], check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()


def spec(name='alpha', mode=WorkspaceMode.INPLACE, **kwargs):
    return AgentSpec(name=name, provider='codex', target='.', workspace_mode=mode,
                     workspace_root=kwargs.pop('workspace_root', None), runtime_mode=RuntimeMode.PANE_BACKED,
                     restore_default=RestoreMode.AUTO, permission_default=PermissionMode.MANUAL,
                     queue_policy=QueuePolicy.SERIAL_PER_AGENT, **kwargs)


class Client:
    def __init__(self, root, project_id):
        self.view = {'project': {'id': project_id, 'root': str(root)}, 'namespace': {'epoch': 7},
                     'agents': [{'name': 'alpha', 'provider': 'codex', 'workspace_path': str(root)}]}
        self.calls = 0

    def project_view(self, **kwargs):
        self.calls += 1
        return {'view': self.view}


class Gateway:
    def close(self):
        pass


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    (root / 'file.txt').write_text('base\n')
    git(root, 'add', 'file.txt')
    git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'base')
    layout = PathLayout(root)
    AgentSpecStore(layout).save(spec())
    client = Client(root, layout.project_id)
    registry = MobileGatewayProjectRegistry([MobileGatewayProject(layout.project_id, root, lambda: client)])
    assets = tmp_path / 'assets'
    assets.mkdir()
    service = WorkbenchService(project_registry=registry, assets_dir=assets,
                               state_dir=tmp_path / 'state', gateway=Gateway())
    yield service, client, layout
    service.close()


def endpoint(layout, suffix):
    return f'/api/projects/{layout.project_id}/{suffix}'


def binding(layout, path, *, name='alpha', mode='git-worktree', pointer=None):
    record = {'schema_version': 2, 'record_type': 'workspace_binding', 'target_project': str(layout.project_root),
              'project_id': layout.project_id, 'agent_name': name, 'workspace_mode': mode,
              'workspace_path': str(path), 'branch_name': f'ccb/{name}' if mode == 'git-worktree' else None}
    marker = path / '.ccb-workspace.json'
    marker.write_text(json.dumps(record))
    if pointer is not None:
        pointer.parent.mkdir(parents=True, exist_ok=True)
        pointer.write_text(json.dumps(record))
    return marker


def test_selected_agent_workspace_is_fresh_read_only_directory_metadata(workspace):
    service, client, layout = workspace
    before = {path: path.read_bytes() for path in layout.ccb_dir.rglob('*') if path.is_file()}
    status, result = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))
    assert status == 200
    assert result['project_id'] == layout.project_id and result['namespace_epoch'] == 7
    assert result['agent'] == 'alpha'
    details = result['workspace']
    assert details['path'] == str(layout.project_root)
    assert details['mode'] == 'inplace' and details['mode_source'] == 'persisted_agent_spec'
    assert details['source'] == 'ccbd_runtime' and details['git_state'] == 'attached'
    assert details['branch'] == 'main' and len(details['head']) == 40
    assert details['scope'] == 'startup_or_declared_directory'
    assert details['attribution'] == 'workspace_not_agent' and details['isolation'] == 'not_guaranteed'
    assert details['shared_agents'] == ['alpha'] and details['observed_at']
    assert client.calls == 1
    assert {path: path.read_bytes() for path in layout.ccb_dir.rglob('*') if path.is_file()} == before


def test_agent_diff_follows_selected_worktree_not_project_or_other_agent(workspace, tmp_path):
    service, client, layout = workspace
    a, b = tmp_path / 'tree-a', tmp_path / 'tree-b'
    git(layout.project_root, 'worktree', 'add', '-qb', 'feature-a', str(a))
    git(layout.project_root, 'worktree', 'add', '-qb', 'feature-b', str(b))
    for name, path in [('alpha', a), ('beta', b)]:
        AgentSpecStore(layout).save(spec(name, WorkspaceMode.GIT_WORKTREE, workspace_path=str(path)))
        (path / 'file.txt').write_text(f'only-{name}\n')
    client.view['agents'] = [{'name': 'alpha', 'workspace_path': str(a)},
                             {'name': 'beta', 'workspace_path': str(b)}]
    (layout.project_root / 'file.txt').write_text('only-root\n')
    for name, path, branch in [('alpha', a, 'feature-a'), ('beta', b, 'feature-b')]:
        result = service.dispatch('GET', endpoint(layout, f'diff?agent={name}&path=/etc&cwd=/etc'))[1]
        assert f'+only-{name}' in result['patch'] and '+only-root' not in result['patch']
        assert result['workspace']['path'] == str(path)
        assert result['workspace']['branch'] == branch and result['agent'] == name
        assert result['scope'] == 'unstaged_tracked'
    assert '+only-root' in service.dispatch('GET', endpoint(layout, 'diff'))[1]['patch']
    assert client.calls == 2


def test_owned_managed_worktree_requires_binding_and_supports_detached_head(workspace):
    service, client, layout = workspace
    path = layout.workspace_path('alpha')
    git(layout.project_root, 'worktree', 'add', '-qb', 'ccb/alpha', str(path))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE))
    marker = binding(layout, path)
    client.view['agents'][0]['workspace_path'] = str(path)
    git(path, 'checkout', '--detach', '-q')
    (path / 'file.txt').write_text('detached-change\n')
    result = service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))[1]
    assert result['workspace']['git_state'] == 'detached' and result['workspace']['branch'] is None
    assert '+detached-change' in result['patch']
    # Single-factor ablation: the exact same Git directory is no longer owned.
    marker.unlink()
    with pytest.raises(MobileGatewayError, match='binding') as error:
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))
    assert error.value.status_code == 409


def test_shared_group_binding_can_point_to_controller_worktree_without_claiming_read_only(workspace, tmp_path):
    service, client, layout = workspace
    path = tmp_path / 'controller-tree'
    git(layout.project_root, 'worktree', 'add', '-qb', 'ccb/controller', str(path))
    pointer = layout.workspace_group_binding_path('review')
    marker = binding(layout, path, name='review', pointer=pointer)
    for name in ('alpha', 'beta'):
        AgentSpecStore(layout).save(spec(name, WorkspaceMode.GIT_WORKTREE, workspace_group='review'))
    client.view['agents'] = [{'name': name, 'workspace_path': str(path)} for name in ('alpha', 'beta')]
    result = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]['workspace']
    assert result['shared_agents'] == ['alpha', 'beta']
    assert result['isolation'] == 'not_guaranteed' and 'read_only' not in result
    # An owned target marker alone cannot override a missing group pointer.
    pointer.unlink()
    assert marker.exists()
    with pytest.raises(MobileGatewayError, match='binding'):
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))


def test_copy_workspace_metadata_does_not_fall_back_to_parent_git_diff(workspace):
    service, client, layout = workspace
    path = layout.workspace_path('alpha')
    path.mkdir(parents=True)
    (path / 'file.txt').write_text('copy-only\n')
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.COPY))
    binding(layout, path, mode='copy')
    client.view['agents'][0]['workspace_path'] = str(path)
    (layout.project_root / 'file.txt').write_text('root-not-copy\n')
    result = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]['workspace']
    assert result['mode'] == 'copy' and result['git_state'] == 'not_git'
    assert result['branch'] is None and result['head'] is None
    with pytest.raises(MobileGatewayError, match='workspace git diff unavailable') as error:
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))
    assert error.value.status_code == 409


@pytest.mark.parametrize('suffix,code', [('agents/missing/workspace', 404), ('diff?agent=missing', 404),
                                       ('diff?agent=', 400), ('diff?agent=alpha&agent=beta', 400),
                                       ('agents/%2e%2e/workspace', 400), ('diff?agent=Alpha', 400)])
def test_unknown_or_invalid_agent_is_not_a_project_root_fallback(workspace, suffix, code):
    service, _, layout = workspace
    with pytest.raises(MobileGatewayError) as error:
        service.dispatch('GET', endpoint(layout, suffix))
    assert error.value.status_code == code


@pytest.mark.parametrize('runtime_path', [None, '', '.', '/a/definitely/nonexistent/muxary-workspace'])
def test_missing_relative_or_nonexistent_runtime_path_is_rejected_even_with_browser_override(workspace, runtime_path):
    service, client, layout = workspace
    client.view['agents'][0]['workspace_path'] = runtime_path
    with pytest.raises(MobileGatewayError, match='agent workspace') as error:
        service.dispatch('GET', endpoint(layout, f'diff?agent=alpha&path={layout.project_root}&cwd={layout.project_root}'))
    assert error.value.status_code == 409


@pytest.mark.parametrize('field,value', [('root', '/tmp'), ('root', None), ('id', 'other-project')])
def test_fresh_project_identity_must_match_registered_canonical_root(workspace, field, value):
    service, client, layout = workspace
    client.view['project'][field] = value
    with pytest.raises(MobileGatewayError) as error:
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))
    assert error.value.status_code == 409


@pytest.mark.parametrize('epoch', [None, True, -1, '7'])
def test_namespace_evidence_must_be_present_and_typed(workspace, epoch):
    service, client, layout = workspace
    client.view['namespace']['epoch'] = epoch
    with pytest.raises(MobileGatewayError, match='namespace'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


def test_main_directory_without_persisted_spec_has_unknown_mode_not_guessed_inplace(workspace):
    service, _, layout = workspace
    layout.agent_spec_path('alpha').unlink()
    details = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]['workspace']
    assert details['path'] == str(layout.project_root)
    assert details['mode'] is None and details['mode_source'] is None


def test_nonmain_runtime_directory_without_spec_is_not_authorized_by_git_membership(workspace, tmp_path):
    service, client, layout = workspace
    path = tmp_path / 'tree'
    git(layout.project_root, 'worktree', 'add', '--detach', '-q', str(path))
    client.view['agents'][0]['workspace_path'] = str(path)
    layout.agent_spec_path('alpha').unlink()
    with pytest.raises(MobileGatewayError, match='binding'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


def test_duplicate_runtime_identity_is_ambiguous_not_first_match(workspace):
    service, client, layout = workspace
    client.view['agents'].append(dict(client.view['agents'][0]))
    with pytest.raises(MobileGatewayError, match='ambiguous agent identity'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


def test_unknown_or_corrupt_persisted_mode_is_not_guessed(workspace):
    service, _, layout = workspace
    record = json.loads(layout.agent_spec_path('alpha').read_text())
    record['workspace_mode'] = 'future-mode'
    layout.agent_spec_path('alpha').write_text(json.dumps(record))
    with pytest.raises(MobileGatewayError, match='spec unavailable'):
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))


def test_external_git_repository_is_rejected_by_common_directory_not_branch_or_commit(workspace, tmp_path):
    service, client, layout = workspace
    path = tmp_path / 'unrelated'
    subprocess.run(['git', 'clone', '-q', '--shared', str(layout.project_root), str(path)], check=True)
    assert git(path, 'rev-parse', 'HEAD') == git(layout.project_root, 'rev-parse', 'HEAD')
    assert git(path, 'branch', '--show-current') == 'main'
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE, workspace_path=str(path)))
    client.view['agents'][0]['workspace_path'] = str(path)
    with pytest.raises(MobileGatewayError, match='common directory mismatch'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


def test_external_subdirectory_is_not_a_worktree_root(workspace):
    service, client, layout = workspace
    path = layout.project_root / 'nested'
    path.mkdir()
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE, workspace_path=str(path)))
    client.view['agents'][0]['workspace_path'] = str(path)
    with pytest.raises(MobileGatewayError, match='toplevel mismatch'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


@pytest.mark.parametrize('field,value', [('project_id', 'other'), ('target_project', '/tmp'),
                                       ('workspace_path', '/tmp'), ('workspace_mode', 'copy'),
                                       ('agent_name', 'beta'), ('schema_version', 1)])
def test_managed_binding_authority_fields_are_not_interchangeable(workspace, field, value):
    service, client, layout = workspace
    path = layout.workspace_path('alpha')
    git(layout.project_root, 'worktree', 'add', '-qb', 'ccb/alpha', str(path))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE))
    marker = binding(layout, path)
    client.view['agents'][0]['workspace_path'] = str(path)
    record = json.loads(marker.read_text())
    record[field] = value
    marker.write_text(json.dumps(record))
    with pytest.raises(MobileGatewayError) as error:
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))
    assert error.value.status_code == 409


def test_symlink_binding_and_spec_records_are_rejected(workspace, tmp_path):
    service, client, layout = workspace
    path = layout.workspace_path('alpha')
    git(layout.project_root, 'worktree', 'add', '-qb', 'ccb/alpha', str(path))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE))
    marker = binding(layout, path)
    client.view['agents'][0]['workspace_path'] = str(path)
    saved = tmp_path / 'saved-binding'
    marker.rename(saved)
    marker.symlink_to(saved)
    with pytest.raises(MobileGatewayError, match='binding'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))
    marker.unlink()
    saved.rename(marker)
    spec_path = layout.agent_spec_path('alpha')
    spec_path.rename(tmp_path / 'saved-spec')
    spec_path.symlink_to(tmp_path / 'saved-spec')
    with pytest.raises(MobileGatewayError, match='spec'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


def test_correct_marker_cannot_override_mismatched_persisted_directory(workspace, tmp_path):
    service, client, layout = workspace
    path = tmp_path / 'external-tree'
    git(layout.project_root, 'worktree', 'add', '-qb', 'external', str(path))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE))
    binding(layout, path)
    client.view['agents'][0]['workspace_path'] = str(path)
    with pytest.raises(MobileGatewayError) as error:
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))
    assert error.value.status_code == 409


def test_external_declaration_must_match_runtime_path_canonically(workspace, tmp_path):
    service, client, layout = workspace
    a, b = tmp_path / 'tree-a', tmp_path / 'tree-b'
    git(layout.project_root, 'worktree', 'add', '-qb', 'a', str(a))
    git(layout.project_root, 'worktree', 'add', '-qb', 'b', str(b))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE, workspace_path=str(a)))
    client.view['agents'][0]['workspace_path'] = str(b)
    with pytest.raises(MobileGatewayError, match='spec path mismatch'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))
    alias = tmp_path / 'alias-a'
    alias.symlink_to(a, target_is_directory=True)
    client.view['agents'][0]['workspace_path'] = str(alias)
    details = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]['workspace']
    assert details['path'] == str(a)


def test_managed_external_root_reuses_existing_path_layout(workspace, tmp_path):
    service, client, layout = workspace
    external_root = tmp_path / 'workspace-home'
    path = layout.workspace_path('alpha', workspace_root=str(external_root))
    git(layout.project_root, 'worktree', 'add', '-qb', 'ccb/alpha', str(path))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE, workspace_root=str(external_root)))
    binding(layout, path)
    client.view['agents'][0]['workspace_path'] = str(path)
    details = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]['workspace']
    assert details['path'] == str(path) and details['mode'] == 'git-worktree'


def test_workspace_and_epoch_are_refreshed_on_each_selection(workspace, tmp_path):
    service, client, layout = workspace
    first = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]
    path = tmp_path / 'new-tree'
    git(layout.project_root, 'worktree', 'add', '-qb', 'new', str(path))
    AgentSpecStore(layout).save(spec('alpha', WorkspaceMode.GIT_WORKTREE, workspace_path=str(path)))
    client.view['agents'][0]['workspace_path'] = str(path)
    client.view['namespace']['epoch'] = 8
    second = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]
    assert first['workspace']['path'] == str(layout.project_root) and first['namespace_epoch'] == 7
    assert second['workspace']['path'] == str(path) and second['namespace_epoch'] == 8
    assert client.calls == 2


def test_git_environment_cannot_redirect_validated_agent_diff(workspace, tmp_path, monkeypatch):
    service, _, layout = workspace
    decoy = tmp_path / 'decoy'
    subprocess.run(['git', 'clone', '-q', str(layout.project_root), str(decoy)], check=True)
    (layout.project_root / 'file.txt').write_text('verified-root\n')
    (decoy / 'file.txt').write_text('wrong-directory\n')
    monkeypatch.setenv('GIT_DIR', str(decoy / '.git'))
    monkeypatch.setenv('GIT_WORK_TREE', str(decoy))
    monkeypatch.setenv('GIT_INDEX_FILE', str(decoy / '.git/index'))
    result = service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))[1]
    assert '+verified-root' in result['patch'] and 'wrong-directory' not in result['patch']


def test_agent_diff_never_executes_external_diff_or_textconv_and_remains_bounded(workspace, tmp_path):
    service, _, layout = workspace
    marker = tmp_path / 'must-not-exist'
    command = f'touch {marker}'
    git(layout.project_root, 'config', 'diff.external', command)
    git(layout.project_root, 'config', 'diff.fixture.textconv', command)
    (layout.project_root / '.gitattributes').write_text('file.txt diff=fixture\n')
    (layout.project_root / 'file.txt').write_text('long-line\n' * 40000)
    result = service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))[1]
    assert result['patch_truncated'] and len(result['patch'].encode()) <= 262144
    assert len(result['stat'].encode()) <= 32768 and not marker.exists()


def test_workspace_inspection_does_not_load_config_or_expose_spec_secrets(workspace, monkeypatch):
    service, _, layout = workspace
    (layout.ccb_dir / 'config.toml').write_text('not valid config = [\n')
    AgentSpecStore(layout).save(spec(env={'SECRET_FIXTURE': 'do-not-expose'}))
    monkeypatch.delenv('CCB_RUNTIME_MUX_BACKEND', raising=False)
    result = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]
    assert 'do-not-expose' not in json.dumps(result)
    assert 'CCB_RUNTIME_MUX_BACKEND' not in os.environ


def test_broken_git_metadata_is_an_error_not_a_claim_that_directory_is_not_git(workspace):
    service, _, layout = workspace
    git_dir = layout.project_root / '.git'
    git_dir.rename(layout.project_root / '.saved-git')
    git_dir.write_text('gitdir: /a/definitely/nonexistent/git-metadata\n')
    with pytest.raises(MobileGatewayError, match='git probe unavailable') as error:
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))
    assert error.value.status_code == 409


def test_plain_directory_is_explicitly_not_git_and_agent_diff_is_unavailable(workspace):
    service, _, layout = workspace
    (layout.project_root / '.git').rename(layout.project_root / '.saved-git')
    details = service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))[1]['workspace']
    assert details['git_state'] == 'not_git' and details['branch'] is None
    with pytest.raises(MobileGatewayError, match='git diff unavailable'):
        service.dispatch('GET', endpoint(layout, 'diff?agent=alpha'))


def test_workspace_probe_output_is_bounded_and_does_not_fall_back(workspace, tmp_path, monkeypatch):
    service, _, layout = workspace
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    launcher = bin_dir / 'git'
    launcher.write_text(f'#!{sys.executable}\nimport sys\nsys.stdout.write("x" * 16384)\n')
    launcher.chmod(0o700)
    monkeypatch.setenv('PATH', str(bin_dir))
    with pytest.raises(MobileGatewayError, match='output exceeded limit') as error:
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))
    assert error.value.status_code == 409


def test_workspace_git_probe_has_one_shared_five_second_deadline(workspace, tmp_path, monkeypatch):
    service, _, layout = workspace
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    launcher = bin_dir / 'git'
    launcher.write_text(f'#!{sys.executable}\nimport sys,time\ntime.sleep(1.8)\n'
                        f'print({str(layout.project_root)!r} if "--show-toplevel" in sys.argv else "main")\n')
    launcher.chmod(0o700)
    monkeypatch.setenv('PATH', str(bin_dir))
    start = time.monotonic()
    with pytest.raises(MobileGatewayError, match='probe timed out') as error:
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))
    assert error.value.status_code == 504
    assert 4.5 <= time.monotonic() - start < 7.5


def test_workspace_probe_deadline_also_bounds_process_after_stdout_eof(workspace, tmp_path, monkeypatch):
    service, _, layout = workspace
    bin_dir = tmp_path / 'bin'
    bin_dir.mkdir()
    launcher = bin_dir / 'git'
    launcher.write_text(f'#!{sys.executable}\nimport os,time\nos.close(1)\ntime.sleep(6)\n')
    launcher.chmod(0o700)
    monkeypatch.setenv('PATH', str(bin_dir))
    start = time.monotonic()
    with pytest.raises(MobileGatewayError, match='probe timed out') as error:
        service.dispatch('GET', endpoint(layout, 'agents/alpha/workspace'))
    assert error.value.status_code == 504
    assert time.monotonic() - start < 5.8


@pytest.fixture
def workspace_server(workspace):
    service, client, layout = workspace
    server = build_workbench_server(service)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield service, client, layout, server
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)


def http(server, path, *, headers=None, body=None):
    connection = HTTPConnection(*server.server_address, timeout=10)
    connection.request('POST' if body is not None else 'GET', path,
                       json.dumps(body) if body is not None else None,
                       {'Content-Type': 'application/json', **(headers or {})})
    response = connection.getresponse()
    status, response_headers, payload = response.status, dict(response.getheaders()), response.read()
    connection.close()
    return status, response_headers, json.loads(payload)


@pytest.mark.parametrize('suffix', ['agents/alpha/workspace', 'diff?agent=alpha'])
def test_workspace_and_scoped_diff_require_cookie_exact_host_and_origin_before_any_probe(workspace_server, suffix):
    service, client, layout, server = workspace_server
    path = endpoint(layout, suffix)
    assert http(server, path)[0] == 401
    assert http(server, path + '&token=' + service.bootstrap_token)[0] == 401
    assert client.calls == 0
    status, headers, _ = http(server, '/api/session', body={'token': service.bootstrap_token},
                              headers={'Origin': service.origin})
    assert status == 200
    cookie = headers['Set-Cookie'].split(';')[0]
    for denied in ({'Host': 'evil.invalid'}, {'Host': 'localhost'}, {'Origin': 'null'},
                   {'Origin': 'http://evil.invalid'}, {'Sec-Fetch-Site': 'same-site'},
                   {'Sec-Fetch-Site': 'cross-site'}):
        assert http(server, path, headers={'Cookie': cookie, **denied})[0] == 403
        assert client.calls == 0
    assert http(server, path, headers={'Cookie': cookie, 'Origin': service.origin})[0] == 200
    assert client.calls == 1
