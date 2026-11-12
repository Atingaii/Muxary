from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import uuid
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.models import AgentSpec, PermissionMode, QueuePolicy, RestoreMode, RuntimeMode, WorkspaceMode
from cli.models import ParsedStartCommand
from provider_backends.codebuddy.home import materialize_codebuddy_home
from provider_backends.codebuddy.launcher import build_session_payload, build_start_cmd, prepare_launch_context
from provider_backends.codebuddy.manifest import build_manifest
from provider_backends.codebuddy.native_log import codebuddy_project_dir
from provider_command_defaults import SUPPORTED_PROVIDER_NAMES, provider_start_parts
from provider_core.pathing import session_filename_for_agent
from provider_profiles import ResolvedProviderProfile
from storage.paths import PathLayout


def _spec(**changes) -> AgentSpec:
    return replace(AgentSpec(
        name='buddy', provider='codebuddy', target='.',
        workspace_mode=WorkspaceMode.GIT_WORKTREE, workspace_root=None,
        runtime_mode=RuntimeMode.PANE_BACKED, restore_default=RestoreMode.AUTO,
        permission_default=PermissionMode.MANUAL, queue_policy=QueuePolicy.SERIAL_PER_AGENT,
    ), **changes)


def _launch(tmp_path: Path):
    root = tmp_path / 'project'
    root.mkdir()
    paths = PathLayout(root)
    runtime = paths.agent_provider_runtime_dir('buddy', 'codebuddy')
    runtime.mkdir(parents=True)
    context = SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='project-1'), paths=paths)
    plan = SimpleNamespace(workspace_path=root)
    prepared = prepare_launch_context(context, _spec(), plan, runtime, {})
    return context, plan, runtime, prepared


def _argv(cmd: str) -> list[str]:
    return shlex.split(cmd.rsplit('; ', 1)[-1])


def _command(*, restore=True, auto=False, reset=False):
    return ParsedStartCommand(project=None, agent_names=(), restore=restore, auto_permission=auto, reset_context=reset)


def test_registered_defaults_and_exact_native_manifest(monkeypatch):
    assert 'codebuddy' in SUPPORTED_PROVIDER_NAMES
    assert provider_start_parts('codebuddy') == ['codebuddy']
    monkeypatch.setenv('CODEBUDDY_START_CMD', 'custom-codebuddy --verbose')
    assert provider_start_parts('codebuddy') == ['custom-codebuddy', '--verbose']
    assert session_filename_for_agent('codebuddy', 'buddy') == '.codebuddy-buddy-session'
    manifest = build_manifest()
    assert manifest.supports_resume
    assert manifest.runtime_profiles[RuntimeMode.PANE_BACKED].supports_exact_completion


def test_new_launch_binds_exact_uuid_and_private_roots(tmp_path):
    context, plan, runtime, prepared = _launch(tmp_path)
    cmd = build_start_cmd(_command(), _spec(), runtime, 'generation-1', prepared_state=prepared)
    argv = _argv(cmd)
    session_id = argv[argv.index('--session-id') + 1]
    assert str(uuid.UUID(session_id)) == session_id
    assert '--resume' not in argv
    assert argv[argv.index('--permission-mode') + 1] == 'default'
    assert '--dangerously-skip-permissions' not in argv
    assert 'CODEBUDDY_IS_SANDBOX' not in cmd
    assert f'CODEBUDDY_CONFIG_DIR={prepared["codebuddy_config_dir"]}' in cmd
    settings = json.loads(Path(argv[argv.index('--settings') + 1]).read_text())
    hook = settings['hooks']['SessionStart'][-1]
    assert hook['matcher'] == '^(startup|resume|clear|compact)$'
    assert f'--launch-id {prepared["codebuddy_launch_id"]}' in hook['hooks'][0]['command']
    identity = json.loads((Path(prepared['codebuddy_state_dir']) / 'codebuddy-launch.json').read_text())
    assert identity['launch_id'] == prepared['codebuddy_launch_id']
    assert str(uuid.UUID(identity['launch_id'])) == identity['launch_id']
    payload = build_session_payload(context, _spec(), plan, runtime, plan.workspace_path, '%4', 'buddy', cmd, 'generation-1', prepared)
    assert payload['codebuddy_session_id'] == session_id
    expected = codebuddy_project_dir(plan.workspace_path, root=Path(payload['codebuddy_config_dir']) / 'projects') / f'{session_id}.jsonl'
    assert payload['codebuddy_session_path'] == str(expected)
    assert payload['codebuddy_launch_id'] == prepared['codebuddy_launch_id']
    assert not expected.exists()  # CLI writes the transcript after its first input.


@pytest.mark.parametrize('explicit', [(), ('--permission-mode', 'plan'), ('--permission-mode=default',), ('-y',)])
def test_auto_permission_does_not_override_explicit_mode(tmp_path, explicit):
    _, _, runtime, prepared = _launch(tmp_path)
    cmd = build_start_cmd(_command(auto=True), _spec(startup_args=explicit), runtime, 'g', prepared_state=prepared)
    argv = _argv(cmd)
    assert ('--dangerously-skip-permissions' in argv) is (not explicit)


@pytest.mark.parametrize('flag', ['--resume', '--resume=latest', '-r', '--continue', '-c', '--session-id=x', '--fork-session', '--no-session-persistence', '--print', '--acp', '--serve', '--bg', '--background', '--', '-rlatest', '-phello', '-cfoo'])
def test_unmanaged_session_modes_fail_before_launch(tmp_path, flag):
    _, _, runtime, prepared = _launch(tmp_path)
    with pytest.raises(ValueError, match='own session identity'):
        build_start_cmd(_command(), _spec(startup_args=(flag,)), runtime, 'g', prepared_state=prepared)


def test_explicit_settings_preserve_user_hook_and_add_private_binding(tmp_path):
    _, _, runtime, prepared = _launch(tmp_path)
    value = {'model': 'native-model', 'hooks': {'SessionStart': [{'matcher': 'startup', 'hooks': [{'type': 'command', 'command': 'echo user'}]}]}}
    cmd = build_start_cmd(_command(), _spec(startup_args=('--settings', json.dumps(value))), runtime, 'g', prepared_state=prepared)
    argv = _argv(cmd)
    assert argv.count('--settings') == 1
    settings = json.loads(Path(argv[argv.index('--settings') + 1]).read_text())
    assert settings['model'] == 'native-model'
    assert settings['hooks']['SessionStart'][0] == value['hooks']['SessionStart'][0]
    assert len(settings['hooks']['SessionStart']) == 2


@pytest.mark.parametrize('invalid', ['hooks_object', 'session_hooks_array'])
def test_rejected_relaunch_preserves_valid_generation_binding_and_settings(tmp_path, invalid):
    from provider_backends.codebuddy.hooks import read_native_binding

    _, plan, runtime, prepared = _launch(tmp_path)
    build_start_cmd(_command(), _spec(), runtime, 'g1', prepared_state=prepared)
    transcript = Path(prepared['codebuddy_session_path'])
    transcript.write_text('{}\n')
    state_dir = Path(prepared['codebuddy_state_dir'])
    sidecar = state_dir / 'native-binding.json'
    sidecar.write_text(json.dumps({
        'schema_version': 1, 'launch_id': prepared['codebuddy_launch_id'],
        'session_id': prepared['codebuddy_session_id'], 'session_path': str(transcript),
    }))
    artifacts = (state_dir / 'codebuddy-launch.json', sidecar, runtime / 'codebuddy-hooks-settings.json')
    before = {path: path.read_bytes() for path in artifacts}
    before_prepared = dict(prepared)
    if invalid == 'hooks_object':
        spec = _spec(startup_args=('--settings', '{"hooks": []}'))
        error = 'hooks must be an object'
    else:
        spec = _spec(startup_args=('--settings', '{"hooks": {"SessionStart": {}}}'))
        error = 'SessionStart must be an array'
    with pytest.raises(ValueError, match=error):
        build_start_cmd(_command(), spec, runtime, 'g2', prepared_state=prepared)
    assert {path: path.read_bytes() for path in artifacts} == before
    assert prepared == before_prepared
    binding = read_native_binding(state_dir, launch_id=prepared['codebuddy_launch_id'],
                                  work_dir=plan.workspace_path, config_dir=Path(prepared['codebuddy_config_dir']))
    assert binding is not None
    assert binding['session_id'] == prepared['codebuddy_session_id']
    # Removing only the invalid factor still publishes a new valid generation.
    build_start_cmd(_command(), _spec(), runtime, 'g2', prepared_state=prepared)
    assert prepared['codebuddy_launch_id'] != before_prepared['codebuddy_launch_id']


@pytest.mark.parametrize('source', ['inherited', 'launch'])
def test_native_settings_env_allows_matching_managed_values_and_ordinary_native_env(tmp_path, source):
    _, _, runtime, prepared = _launch(tmp_path)
    settings = {'model': 'fixture-model', 'env': {
        'HOME': prepared['codebuddy_home'],
        'CODEBUDDY_CONFIG_DIR': prepared['codebuddy_config_dir'],
        'XDG_STATE_HOME': str(Path(prepared['codebuddy_home']) / '.local/state'),
        'CCB_CALLER_ACTOR': 'buddy', 'CCB_CALLER_RUNTIME_DIR': str(runtime),
        'CCB_SESSION_ID': 'g',
        'CODEBUDDY_API_KEY': 'fixture-key', 'CODEBUDDY_BASE_URL': 'https://fixture.invalid',
        'FIXTURE_KEEP': 'keep', 'PATH': '/synthetic/native-command-path',
    }}
    inherited = Path(prepared['codebuddy_config_dir']) / 'settings.json'
    spec = _spec()
    if source == 'inherited':
        inherited.write_text(json.dumps(settings))
    else:
        spec = _spec(startup_args=('--settings', json.dumps(settings)))
    cmd = build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
    actual = json.loads(inherited.read_text()) if source == 'inherited' else json.loads(Path(_argv(cmd)[-1]).read_text())
    assert actual['env'] == settings['env']
    assert actual['model'] == settings['model']


@pytest.mark.parametrize('key', ['USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'WSLENV'])
def test_native_settings_env_cannot_replace_wsl_private_storage(tmp_path, monkeypatch, key):
    monkeypatch.setenv('WSL_DISTRO_NAME', 'Synthetic-WSL')
    _, _, runtime, prepared = _launch(tmp_path)
    spec = _spec(startup_args=('--settings', json.dumps({'env': {key: '/synthetic/shared'}})))
    with pytest.raises(ValueError, match=f'settings.env.{key}.*managed'):
        build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
    assert not (Path(prepared['codebuddy_state_dir']) / 'codebuddy-launch.json').exists()


def test_resume_requires_same_agent_project_cwd_config_and_exact_file(tmp_path):
    context, plan, runtime, prepared = _launch(tmp_path)
    cmd = build_start_cmd(_command(), _spec(), runtime, 'g1', prepared_state=prepared)
    payload = build_session_payload(context, _spec(), plan, runtime, plan.workspace_path, '%4', 'buddy', cmd, 'g1', prepared)
    transcript = Path(payload['codebuddy_session_path'])
    transcript.write_text('{}\n')
    session = context.paths.ccb_dir / '.codebuddy-buddy-session'
    session.write_text(json.dumps(payload))
    binding_path = Path(payload['state_dir']) / 'native-binding.json'
    binding_path.write_text(json.dumps({
        'schema_version': 1, 'launch_id': payload['codebuddy_launch_id'],
        'session_id': payload['codebuddy_session_id'], 'session_path': str(transcript),
    }))
    assert prepare_launch_context(context, _spec(), plan, runtime, {})['codebuddy_resume_session_id'] == payload['codebuddy_session_id']
    for key, value in [('agent_name', 'other'), ('ccb_project_id', 'other'), ('work_dir', '/elsewhere'), ('codebuddy_config_dir', '/external')]:
        session.write_text(json.dumps({**payload, key: value}))
        assert not prepare_launch_context(context, _spec(), plan, runtime, {}).get('codebuddy_resume_session_id'), key
    session.write_text(json.dumps(payload))
    transcript.unlink()
    assert not prepare_launch_context(context, _spec(), plan, runtime, {}).get('codebuddy_resume_session_id')
    transcript.write_text('{}\n')
    restored = prepare_launch_context(context, _spec(), plan, runtime, {})
    argv = _argv(build_start_cmd(_command(), _spec(), runtime, 'g2', prepared_state=restored))
    assert argv[argv.index('--resume') + 1] == payload['codebuddy_session_id']
    assert '--session-id' not in argv


def test_restore_disabled_or_new_context_never_reuses_uuid(tmp_path):
    _, _, runtime, prepared = _launch(tmp_path)
    old = str(uuid.uuid4())
    for command in (_command(restore=False), _command(reset=True)):
        prepared['codebuddy_resume_session_id'] = old
        argv = _argv(build_start_cmd(command, _spec(), runtime, 'g', prepared_state=prepared))
        assert '--resume' not in argv
        assert argv[argv.index('--session-id') + 1] != old


def test_home_inherits_assets_one_way_not_history_or_plugin_cache(tmp_path):
    source = tmp_path / 'source'
    config = source / '.codebuddy'
    config.mkdir(parents=True)
    (config / '.credentials.json').write_text('{"token":"fixture"}')
    (config / 'settings.json').write_text('{"enabledPlugins":{"fixture":true}}')
    (config / 'CODEBUDDY.md').write_text('memory')
    (config / 'projects').mkdir()
    (config / 'projects' / 'old.jsonl').write_text('old history')
    (config / 'plugins').mkdir()
    (config / 'plugins' / 'cache').write_text('do not copy')
    skill = config / 'skills' / 'fixture'
    skill.mkdir(parents=True)
    (skill / 'SKILL.md').write_text('fixture skill')
    target = materialize_codebuddy_home(tmp_path / 'managed', source_home=source)
    actual = target / '.codebuddy'
    assert (actual / '.credentials.json').read_text() == '{"token":"fixture"}'
    assert not (actual / '.credentials.json').is_symlink()
    assert (actual / '.credentials.json').stat().st_mode & 0o777 == 0o600
    assert (actual / 'settings.json').read_text() == (config / 'settings.json').read_text()
    assert (actual / 'CODEBUDDY.md').read_text() == 'memory'
    assert (actual / 'skills' / 'fixture' / 'SKILL.md').read_text() == 'fixture skill'
    assert (actual / 'skills' / 'ask' / 'SKILL.md').is_file()
    assert not list((actual / 'projects').iterdir())
    assert not (actual / 'plugins').exists()
    (actual / '.credentials.json').write_text('changed privately')
    assert (config / '.credentials.json').read_text() == '{"token":"fixture"}'


def test_home_inheritance_flags_keep_only_required_controls(tmp_path):
    source = tmp_path / 'source'
    config = source / '.codebuddy'
    config.mkdir(parents=True)
    for name in ('.credentials.json', 'settings.json', 'models.json', 'mcp.json', 'CODEBUDDY.md'):
        (config / name).write_text('{}')
    profile = SimpleNamespace(**{f'inherit_{name}': False for name in ('auth', 'config', 'memory', 'skills', 'commands')})
    target = materialize_codebuddy_home(tmp_path / 'managed', source_home=source, profile=profile) / '.codebuddy'
    assert not any((target / name).exists() for name in ('.credentials.json', 'settings.json', 'models.json', 'mcp.json', 'CODEBUDDY.md'))
    assert (target / 'skills' / 'ask' / 'SKILL.md').is_file()


def test_native_clear_binding_is_selected_for_exact_resume(tmp_path, monkeypatch):
    from provider_backends.codebuddy.hooks import publish_native_binding

    context, plan, runtime, prepared = _launch(tmp_path)
    cmd = build_start_cmd(_command(), _spec(), runtime, 'same-ccb-id', prepared_state=prepared)
    original_launch = prepared['codebuddy_launch_id']
    payload = build_session_payload(context, _spec(), plan, runtime, plan.workspace_path, '%4', 'buddy', cmd, 'same-ccb-id', prepared)
    session = context.paths.ccb_dir / '.codebuddy-buddy-session'
    session.write_text(json.dumps(payload))
    rotated_id = str(uuid.uuid4())
    rotated_path = codebuddy_project_dir(plan.workspace_path, root=Path(prepared['codebuddy_config_dir']) / 'projects') / f'{rotated_id}.jsonl'
    rotated_path.write_text('{}\n')
    monkeypatch.setenv('CODEBUDDY_CONFIG_DIR', prepared['codebuddy_config_dir'])
    publish_native_binding(Path(prepared['codebuddy_state_dir']), launch_id=original_launch, payload={
        'session_id': rotated_id, 'transcript_path': str(rotated_path), 'source': 'clear', 'cwd': str(plan.workspace_path),
    })
    restored = prepare_launch_context(context, _spec(), plan, runtime, {})
    assert restored['codebuddy_resume_session_id'] == rotated_id
    argv = _argv(build_start_cmd(_command(), _spec(), runtime, 'same-ccb-id', prepared_state=restored))
    assert argv[argv.index('--resume') + 1] == rotated_id
    assert restored['codebuddy_launch_id'] != original_launch  # Even if CCB reuses its ID.


def test_modern_restore_requires_generation_sidecar_not_startup_uuid(tmp_path):
    context, plan, runtime, prepared = _launch(tmp_path)
    cmd = build_start_cmd(_command(), _spec(), runtime, 'g1', prepared_state=prepared)
    payload = build_session_payload(context, _spec(), plan, runtime, plan.workspace_path, '%4', 'buddy', cmd, 'g1', prepared)
    transcript = Path(payload['codebuddy_session_path'])
    transcript.write_text('{}\n')
    (context.paths.ccb_dir / '.codebuddy-buddy-session').write_text(json.dumps(payload))
    binding_path = Path(payload['state_dir']) / 'native-binding.json'
    binding = {
        'schema_version': 1, 'launch_id': payload['codebuddy_launch_id'],
        'session_id': payload['codebuddy_session_id'], 'session_path': str(transcript),
    }
    binding_path.write_text(json.dumps(binding))
    assert prepare_launch_context(context, _spec(), plan, runtime, {})['codebuddy_resume_session_id'] == payload['codebuddy_session_id']
    # Single-factor ablation: unchanged saved session and exact existing JSONL;
    # removing only the native generation binding must prevent old-history resume.
    binding_path.unlink()
    assert not prepare_launch_context(context, _spec(), plan, runtime, {}).get('codebuddy_resume_session_id')
    binding_path.write_text(json.dumps({**binding, 'launch_id': str(uuid.uuid4())}))
    assert not prepare_launch_context(context, _spec(), plan, runtime, {}).get('codebuddy_resume_session_id')
    binding_path.write_text(json.dumps(binding))
    assert prepare_launch_context(context, _spec(), plan, runtime, {})['codebuddy_resume_session_id'] == payload['codebuddy_session_id']


@pytest.mark.parametrize('args', [
    ('--worktree',), ('--worktree=feature',), ('-w',), ('-wfeature',),
    ('--worktree-branch', 'main'), ('--tmux',), ('--tmux-classic',),
])
def test_native_workspace_and_tmux_controls_cannot_escape_managed_cwd(tmp_path, args):
    _, _, runtime, prepared = _launch(tmp_path)
    # Only the native workspace/terminal selector changes; CCB already owns
    # run_cwd and pane identity and computes its transcript from that cwd.
    with pytest.raises(ValueError, match='own session identity'):
        build_start_cmd(_command(), _spec(startup_args=args), runtime, 'g', prepared_state=prepared)


def test_ordinary_native_options_remain_available(tmp_path):
    _, _, runtime, prepared = _launch(tmp_path)
    args = ('--model', 'fixture-model', '--effort', 'high', '--add-dir', str(tmp_path / 'additional'))
    argv = _argv(build_start_cmd(_command(), _spec(startup_args=args), runtime, 'g', prepared_state=prepared))
    for index, part in enumerate(args):
        assert argv[index + 1] == part


def _shell_env_probe(tmp_path, monkeypatch, runtime, prepared, *, profile, spec=None):
    (runtime / 'provider-profile.json').write_text(json.dumps(profile.to_record()))
    probe = tmp_path / 'environment_probe.py'
    probe.write_text('import json, os; print(json.dumps({key: value for key, value in os.environ.items() if key.startswith(("CODEBUDDY_", "FIXTURE_")) or key in ("HOME", "DISABLE_AUTOUPDATER")}))\n')
    monkeypatch.setenv('CODEBUDDY_START_CMD', f'{shlex.quote(sys.executable)} {shlex.quote(str(probe))}')
    cmd = build_start_cmd(_command(), spec or _spec(), runtime, 'probe', prepared_state=prepared)
    result = subprocess.run(['bash', '-c', cmd], env=dict(os.environ), check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_materialized_profile_env_reaches_shell_below_agent_env(tmp_path, monkeypatch):
    _, _, runtime, prepared = _launch(tmp_path)
    monkeypatch.setenv('CODEBUDDY_API_KEY', 'ambient-key')
    monkeypatch.setenv('CODEBUDDY_AUTH_TOKEN', 'ambient-token')
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', env={
        'CODEBUDDY_API_KEY': 'profile key', 'CODEBUDDY_BASE_URL': 'https://profile.invalid',
        'FIXTURE_PROFILE_ONLY': 'profile value', 'FIXTURE_OVERRIDE': 'profile',
    })
    actual = _shell_env_probe(tmp_path, monkeypatch, runtime, prepared, profile=profile, spec=_spec(env={
        'CODEBUDDY_API_KEY': 'agent key', 'FIXTURE_OVERRIDE': 'agent',
        'HOME': '/not-the-managed-home', 'CODEBUDDY_CONFIG_DIR': '/not-the-managed-config',
    }))
    assert actual['CODEBUDDY_API_KEY'] == 'agent key'
    assert 'CODEBUDDY_AUTH_TOKEN' not in actual  # Explicit credential owns both native credential sources.
    assert actual['CODEBUDDY_BASE_URL'] == 'https://profile.invalid'
    assert actual['FIXTURE_PROFILE_ONLY'] == 'profile value'
    assert actual['FIXTURE_OVERRIDE'] == 'agent'
    assert actual['HOME'] == prepared['codebuddy_home']
    assert actual['CODEBUDDY_CONFIG_DIR'] == prepared['codebuddy_config_dir']


@pytest.mark.parametrize('inherit_api', [True, False])
def test_inherit_api_is_a_real_shell_boundary(tmp_path, monkeypatch, inherit_api):
    _, _, runtime, prepared = _launch(tmp_path)
    ambient = {'CODEBUDDY_API_KEY': 'ambient-key', 'CODEBUDDY_AUTH_TOKEN': 'ambient-token', 'CODEBUDDY_BASE_URL': 'https://ambient.invalid'}
    for key, value in ambient.items():
        monkeypatch.setenv(key, value)
    # The inheritance switch is the only changed input in this paired probe.
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', inherit_api=inherit_api)
    actual = _shell_env_probe(tmp_path, monkeypatch, runtime, prepared, profile=profile)
    assert {key: actual[key] for key in ambient if key in actual} == (ambient if inherit_api else {})


def test_disabled_api_inheritance_still_allows_explicit_agent_credentials(tmp_path, monkeypatch):
    _, _, runtime, prepared = _launch(tmp_path)
    for key in ('CODEBUDDY_API_KEY', 'CODEBUDDY_AUTH_TOKEN', 'CODEBUDDY_BASE_URL'):
        monkeypatch.setenv(key, 'ambient')
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', inherit_api=False, env={'CODEBUDDY_API_KEY': 'profile'})
    actual = _shell_env_probe(tmp_path, monkeypatch, runtime, prepared, profile=profile, spec=_spec(env={'CODEBUDDY_AUTH_TOKEN': 'explicit-token'}))
    assert actual['CODEBUDDY_AUTH_TOKEN'] == 'explicit-token'
    assert actual['CODEBUDDY_API_KEY'] == 'profile'
    assert 'CODEBUDDY_BASE_URL' not in actual


@pytest.mark.parametrize('inherit_api', [True, False])
def test_home_settings_env_obeys_api_inheritance_without_mutating_source(tmp_path, inherit_api):
    source = tmp_path / 'source'
    source_config = source / '.codebuddy'
    source_config.mkdir(parents=True)
    value = {'model': 'fixture', 'env': {'CODEBUDDY_API_KEY': 'source-key', 'CODEBUDDY_AUTH_TOKEN': 'source-token', 'CODEBUDDY_BASE_URL': 'https://source.invalid', 'FIXTURE_KEEP': 'keep'}}
    raw = json.dumps(value)
    (source_config / 'settings.json').write_text(raw)
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', inherit_api=inherit_api)
    home = materialize_codebuddy_home(tmp_path / 'managed', source_home=source, profile=profile)
    actual = json.loads((home / '.codebuddy' / 'settings.json').read_text())
    assert actual['env'] == (value['env'] if inherit_api else {'FIXTURE_KEEP': 'keep'})
    assert actual['model'] == 'fixture'
    assert (source_config / 'settings.json').read_text() == raw


def test_explicit_profile_api_cannot_be_shadowed_by_inherited_settings_env(tmp_path):
    source = tmp_path / 'source'
    config = source / '.codebuddy'
    config.mkdir(parents=True)
    (config / 'settings.json').write_text(json.dumps({'env': {'CODEBUDDY_API_KEY': 'source-key', 'CODEBUDDY_AUTH_TOKEN': 'source-token', 'CODEBUDDY_BASE_URL': 'https://source.invalid', 'FIXTURE_KEEP': 'keep'}}))
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', env={'CODEBUDDY_API_KEY': 'explicit-key', 'CODEBUDDY_BASE_URL': 'https://explicit.invalid'})
    home = materialize_codebuddy_home(tmp_path / 'managed', source_home=source, profile=profile)
    assert json.loads((home / '.codebuddy' / 'settings.json').read_text())['env'] == {'FIXTURE_KEEP': 'keep'}


def test_disabled_auth_clears_shell_credentials_but_preserves_endpoint(tmp_path, monkeypatch):
    _, _, runtime, prepared = _launch(tmp_path)
    for key in ('CODEBUDDY_API_KEY', 'CODEBUDDY_AUTH_TOKEN', 'CODEBUDDY_BASE_URL'):
        monkeypatch.setenv(key, 'ambient')
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', inherit_auth=False)
    actual = _shell_env_probe(tmp_path, monkeypatch, runtime, prepared, profile=profile)
    assert 'CODEBUDDY_API_KEY' not in actual
    assert 'CODEBUDDY_AUTH_TOKEN' not in actual
    assert actual['CODEBUDDY_BASE_URL'] == 'ambient'


def test_managed_native_process_cannot_self_update_shared_installation(tmp_path, monkeypatch):
    _, _, runtime, prepared = _launch(tmp_path)
    monkeypatch.setenv('DISABLE_AUTOUPDATER', '0')
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', env={'DISABLE_AUTOUPDATER': 'false'})
    actual = _shell_env_probe(tmp_path, monkeypatch, runtime, prepared, profile=profile,
                              spec=_spec(env={'DISABLE_AUTOUPDATER': '0'}))
    assert actual['DISABLE_AUTOUPDATER'] == '1'


@pytest.mark.parametrize('source', ['inherited', 'launch'])
@pytest.mark.parametrize('enabled', ['0', '1'])
def test_native_settings_env_cannot_reenable_managed_self_update(tmp_path, source, enabled):
    _, _, runtime, prepared = _launch(tmp_path)
    settings = {'env': {'DISABLE_AUTOUPDATER': enabled}}
    spec = _spec()
    if source == 'inherited':
        (Path(prepared['codebuddy_config_dir']) / 'settings.json').write_text(json.dumps(settings))
    else:
        spec = _spec(startup_args=('--settings', json.dumps(settings)))
    if enabled == '0':
        with pytest.raises(ValueError, match='DISABLE_AUTOUPDATER'):
            build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
        assert not (Path(prepared['codebuddy_state_dir']) / 'codebuddy-launch.json').exists()
    else:
        assert 'DISABLE_AUTOUPDATER=1' in build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)


@pytest.mark.parametrize('inherit_auth', [True, False])
def test_native_account_login_inheritance_copies_only_current_private_file(tmp_path, inherit_auth):
    source = tmp_path / 'source'
    relative = Path('.local/share/CodeBuddyExtension/Data/Public/auth')
    original = source / relative / 'Tencent-Cloud.coding-copilot.info'
    original.parent.mkdir(parents=True)
    original.write_text('{"auth":{"accessToken":"fixture"}}')
    original.with_suffix('.info.backup').write_text('historical secret')
    original.chmod(0o644)
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', inherit_auth=inherit_auth)
    home = materialize_codebuddy_home(tmp_path / 'managed', source_home=source, profile=profile)
    target = home / relative / original.name
    assert target.exists() is inherit_auth
    assert not target.with_suffix('.info.backup').exists()
    if inherit_auth:
        assert target.read_bytes() == original.read_bytes()
        assert not os.path.samefile(target, original)
        assert target.stat().st_mode & 0o777 == 0o600
        target.write_text('private refresh')
    assert original.read_text() == '{"auth":{"accessToken":"fixture"}}'
    assert original.stat().st_mode & 0o777 == 0o644


def test_native_logout_marker_prevents_restoring_source_login(tmp_path):
    source = tmp_path / 'source'
    relative = Path('.local/share/CodeBuddyExtension/Data/Public/auth')
    original = source / relative / 'Tencent-Cloud.coding-copilot.info'
    original.parent.mkdir(parents=True)
    original.write_text('expired source login')
    marker = original.with_name(original.name + '.logged-out')
    marker.write_text('logout')
    home = materialize_codebuddy_home(tmp_path / 'managed', source_home=source)
    assert not (home / relative / original.name).exists()
    target_marker = home / relative / marker.name
    assert target_marker.read_text() == 'logout'
    assert target_marker.stat().st_mode & 0o777 == 0o600
    marker.unlink()
    materialize_codebuddy_home(home, source_home=source)
    assert (home / relative / original.name).read_text() == 'expired source login'
    assert not target_marker.exists()


def test_native_account_projection_detaches_legacy_home_ancestor_alias(tmp_path):
    source = tmp_path / 'source'
    relative = Path('.local/share/CodeBuddyExtension/Data/Public/auth')
    original = source / relative / 'Tencent-Cloud.coding-copilot.info'
    original.parent.mkdir(parents=True)
    original.write_text('source login')
    external = tmp_path / 'external'
    external.mkdir()
    managed = tmp_path / 'managed'
    managed.mkdir()
    (managed / '.local').symlink_to(external, target_is_directory=True)
    materialize_codebuddy_home(managed, source_home=source)
    assert not (managed / '.local').is_symlink()
    assert (managed / relative / original.name).read_text() == 'source login'
    assert not list(external.iterdir())


def test_api_inheritance_refresh_removes_stale_settings_credentials_and_helper(tmp_path):
    source = tmp_path / 'source'
    config = source / '.codebuddy'
    config.mkdir(parents=True)
    value = {'apiKeyHelper': 'fixture-helper', 'env': {'CODEBUDDY_AUTH_TOKEN': 'source-token', 'FIXTURE_KEEP': 'keep'}}
    (config / 'settings.json').write_text(json.dumps(value))
    home = materialize_codebuddy_home(tmp_path / 'managed', source_home=source)
    settings_path = home / '.codebuddy' / 'settings.json'
    assert json.loads(settings_path.read_text()) == value
    # Only the API switch changes; the same already-projected settings must be
    # sanitized even when config copying has subsequently been disabled.
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', inherit_api=False, inherit_config=False)
    materialize_codebuddy_home(home, source_home=source, profile=profile)
    assert json.loads(settings_path.read_text()) == {'env': {'FIXTURE_KEEP': 'keep'}}
    assert json.loads((config / 'settings.json').read_text()) == value


@pytest.mark.parametrize('policy', ['disableAllHooks', 'allowManagedHooksOnly'])
@pytest.mark.parametrize('enabled', [False, True])
def test_explicit_hook_policy_is_not_silently_overridden(tmp_path, policy, enabled):
    _, _, runtime, prepared = _launch(tmp_path)
    spec = _spec(startup_args=('--settings', json.dumps({policy: enabled})))
    if enabled:
        with pytest.raises(ValueError, match=policy):
            build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
        assert not (runtime / 'codebuddy-hooks-settings.json').exists()
        assert not (Path(prepared['codebuddy_state_dir']) / 'codebuddy-launch.json').exists()
    else:
        cmd = build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
        argv = _argv(cmd)
        assert json.loads(Path(argv[argv.index('--settings') + 1]).read_text())[policy] is False


@pytest.mark.parametrize('policy', ['disableAllHooks', 'allowManagedHooksOnly'])
def test_inherited_hook_policy_cannot_be_overridden_by_launch_settings(tmp_path, policy):
    _, _, runtime, prepared = _launch(tmp_path)
    inherited = Path(prepared['codebuddy_config_dir']) / 'settings.json'
    inherited.write_text(json.dumps({policy: True}))
    spec = _spec(startup_args=('--settings', json.dumps({policy: False})))
    with pytest.raises(ValueError, match=policy):
        build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
    assert json.loads(inherited.read_text())[policy] is True


@pytest.mark.parametrize('source', ['inherited', 'launch', 'project', 'project_local'])
@pytest.mark.parametrize('key', [
    'HOME', 'XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME',
    'CODEBUDDY_CONFIG_DIR', 'CODEBUDDY_PROJECT_CONFIG_DIR', 'CCB_CALLER_ACTOR', 'CCB_CALLER_RUNTIME_DIR',
    'CCB_CALLER_PROJECT_ROOT', 'CCB_CALLER_PROJECT_ID', 'CCB_SESSION_ID',
])
def test_native_settings_env_cannot_replace_managed_roots_or_identity(tmp_path, source, key):
    from provider_backends.codebuddy.hooks import read_native_binding

    _, plan, runtime, prepared = _launch(tmp_path)
    build_start_cmd(_command(), _spec(), runtime, 'g1', prepared_state=prepared)
    transcript = Path(prepared['codebuddy_session_path'])
    transcript.write_text('{}\n')
    state_dir = Path(prepared['codebuddy_state_dir'])
    sidecar = state_dir / 'native-binding.json'
    sidecar.write_text(json.dumps({
        'schema_version': 1, 'launch_id': prepared['codebuddy_launch_id'],
        'session_id': prepared['codebuddy_session_id'], 'session_path': str(transcript),
    }))
    artifacts = (state_dir / 'codebuddy-launch.json', sidecar, runtime / 'codebuddy-hooks-settings.json')
    before = {path: path.read_bytes() for path in artifacts}
    before_prepared = dict(prepared)
    # Native EnvInterceptor applies settings.env after shell startup: correct
    # shell exports alone cannot enforce managed storage/caller isolation.
    settings = {'model': 'fixture-model', 'env': {
        key: '/synthetic/unmanaged-or-other-identity',
        'CODEBUDDY_API_KEY': 'fixture-key', 'FIXTURE_KEEP': 'keep',
    }}
    inherited = Path(prepared['codebuddy_config_dir']) / 'settings.json'
    spec = _spec()
    if source in {'project', 'project_local'}:
        inherited = plan.workspace_path / '.codebuddy' / ('settings.local.json' if source == 'project_local' else 'settings.json')
        inherited.parent.mkdir(exist_ok=True)
    if source != 'launch':
        inherited.write_text(json.dumps(settings))
    else:
        spec = _spec(startup_args=('--settings', json.dumps(settings)))
    with pytest.raises(ValueError, match=f'settings.env.{key}.*managed'):
        build_start_cmd(_command(), spec, runtime, 'g2', prepared_state=prepared)
    assert {path: path.read_bytes() for path in artifacts} == before
    assert prepared == before_prepared
    if source != 'launch':
        assert json.loads(inherited.read_text()) == settings
    binding = read_native_binding(state_dir, launch_id=prepared['codebuddy_launch_id'],
                                  work_dir=plan.workspace_path, config_dir=Path(prepared['codebuddy_config_dir']))
    assert binding is not None
    assert binding['session_id'] == prepared['codebuddy_session_id']
    # Removing only the conflicting key restores the unchanged API/model/env
    # settings. The adapter must not delete or silently override user policy.
    del settings['env'][key]
    if source != 'launch':
        inherited.write_text(json.dumps(settings))
    else:
        spec = _spec(startup_args=('--settings', json.dumps(settings)))
    cmd = build_start_cmd(_command(), spec, runtime, 'g2', prepared_state=prepared)
    actual = json.loads(inherited.read_text()) if source != 'launch' else json.loads(Path(_argv(cmd)[-1]).read_text())
    assert actual['model'] == 'fixture-model'
    assert actual['env'] == {'CODEBUDDY_API_KEY': 'fixture-key', 'FIXTURE_KEEP': 'keep'}
    assert prepared['codebuddy_launch_id'] != before_prepared['codebuddy_launch_id']


@pytest.mark.parametrize('source', ['user', 'project', 'local'])
@pytest.mark.parametrize(('selected', 'enabled'), [
    (None, {'user', 'project', 'local'}),
    ('', {'user', 'project', 'local'}), (' ', set()), ('none', set()), ('NONE', set()),
    ('user', {'user'}), ('project', {'project'}), ('local', {'local'}),
    ('user,local', {'user', 'local'}), ('unknown', {'user', 'project', 'local'}),
    ('USER', {'user', 'project', 'local'}), ('user,PROJECT', {'user'}),
    ('unknown,project', {'project'}), ('user project local', {'user', 'project', 'local'}),
])
def test_native_setting_sources_only_validate_enabled_disk_scopes(tmp_path, source, selected, enabled):
    _, plan, runtime, prepared = _launch(tmp_path)
    if source == 'user':
        path = Path(prepared['codebuddy_config_dir']) / 'settings.json'
    else:
        path = plan.workspace_path / '.codebuddy' / ('settings.local.json' if source == 'local' else 'settings.json')
        path.parent.mkdir(exist_ok=True)
    value = {'disableAllHooks': True, 'env': {'HOME': '/synthetic/shared'}}
    path.write_text(json.dumps(value))
    args = () if selected is None else ('--setting-sources', selected)
    if source in enabled:
        with pytest.raises(ValueError, match='required managed SessionStart'):
            build_start_cmd(_command(), _spec(startup_args=args), runtime, 'g', prepared_state=prepared)
    else:
        cmd = build_start_cmd(_command(), _spec(startup_args=args), runtime, 'g', prepared_state=prepared)
        argv = _argv(cmd)
        assert argv[argv.index('--setting-sources') + 1] == selected
        assert json.loads(Path(argv[-1]).read_text())['hooks']['SessionStart']
    assert json.loads(path.read_text()) == value


@pytest.mark.parametrize('location', ['relative', 'absolute', 'relative_spaces', 'absolute_spaces', 'blank'])
@pytest.mark.parametrize('level', ['ambient', 'profile', 'agent'])
def test_native_project_config_override_keeps_source_semantics_and_is_frozen(tmp_path, monkeypatch, location, level):
    _, plan, runtime, prepared = _launch(tmp_path)
    custom = plan.workspace_path / ('.codebuddy' if location == 'blank' else 'native-config')
    custom.mkdir()
    expected = 'native-config' if location.startswith('relative') else str(custom)
    raw = '   ' if location == 'blank' else f'  {expected}  ' if location.endswith('_spaces') else expected
    # Project config selection obeys the same ambient < profile < agent order.
    monkeypatch.setenv('CODEBUDDY_PROJECT_CONFIG_DIR', raw if level == 'ambient' else '/synthetic/ambient')
    profile_env = {} if level == 'ambient' else {'CODEBUDDY_PROJECT_CONFIG_DIR': raw if level == 'profile' else '/synthetic/profile'}
    profile = ResolvedProviderProfile(provider='codebuddy', agent_name='buddy', env=profile_env)
    (runtime / 'provider-profile.json').write_text(json.dumps(profile.to_record()))
    spec = _spec(env={'CODEBUDDY_PROJECT_CONFIG_DIR': raw} if level == 'agent' else {})
    path = custom / 'settings.local.json'
    path.write_text(json.dumps({'env': {'HOME': '/synthetic/shared'}}))
    with pytest.raises(ValueError, match='settings.env.HOME.*managed'):
        build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
    path.write_text(json.dumps({'env': {'FIXTURE_KEEP': 'keep'}, 'model': 'fixture-model'}))
    cmd = build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
    assert f'CODEBUDDY_PROJECT_CONFIG_DIR={shlex.quote(expected)}' in cmd
    assert json.loads(path.read_text())['env'] == {'FIXTURE_KEEP': 'keep'}


@pytest.mark.parametrize('selector', [('--setting-sources', 'none'), ('--setting-sources=none',)])
def test_native_cli_overlay_remains_enabled_without_disk_setting_sources(tmp_path, selector):
    _, _, runtime, prepared = _launch(tmp_path)
    settings = {'env': {'HOME': '/synthetic/shared'}}
    spec = _spec(startup_args=(*selector, '--settings', json.dumps(settings)))
    with pytest.raises(ValueError, match='settings.env.HOME.*managed'):
        build_start_cmd(_command(), spec, runtime, 'g', prepared_state=prepared)
    # Remove only the conflicting CLI env; no disabled disk source is reopened.
    cmd = build_start_cmd(_command(), _spec(startup_args=selector), runtime, 'g', prepared_state=prepared)
    assert '--setting-sources' in cmd


@pytest.mark.parametrize('source', ['user', 'project', 'local'])
@pytest.mark.parametrize('raw', [
    '{\n// native JSONC comment\n"env":{"HOME":"/synthetic/shared"}\n}',
    '{"env":{"HOME":"/synthetic/shared"},}',
])
def test_native_nonstandard_json_settings_do_not_bypass_launch_validation(tmp_path, source, raw):
    _, plan, runtime, prepared = _launch(tmp_path)
    if source == 'user':
        path = Path(prepared['codebuddy_config_dir']) / 'settings.json'
    else:
        path = plan.workspace_path / '.codebuddy' / ('settings.local.json' if source == 'local' else 'settings.json')
        path.parent.mkdir(exist_ok=True)
    path.write_text(raw)
    with pytest.raises(ValueError, match='standard JSON'):
        build_start_cmd(_command(), _spec(), runtime, 'g', prepared_state=prepared)
    assert not (Path(prepared['codebuddy_state_dir']) / 'codebuddy-launch.json').exists()
    assert path.read_text() == raw
    # Only disable the source: an unused native file must not be rejected.
    build_start_cmd(_command(), _spec(startup_args=('--setting-sources', 'none')), runtime, 'g', prepared_state=prepared)
    assert path.read_text() == raw
