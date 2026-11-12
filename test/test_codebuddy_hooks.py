from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from provider_backends.codebuddy import hooks
from provider_backends.codebuddy.native_log import codebuddy_project_dir


@pytest.fixture
def launch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict:
    work_dir = tmp_path / 'workspace'
    config_dir = tmp_path / 'config'
    state_dir = tmp_path / 'state'
    work_dir.mkdir()
    state_dir.mkdir()
    identity = {
        'schema_version': 1,
        'launch_id': 'launch-current',
        'work_dir': str(work_dir),
        'config_dir': str(config_dir),
    }
    (state_dir / hooks.LAUNCH_IDENTITY_FILENAME).write_text(json.dumps(identity), encoding='utf-8')
    monkeypatch.setenv('CODEBUDDY_CONFIG_DIR', str(config_dir))
    monkeypatch.setenv('CODEBUDDY_PROJECT_DIR', str(work_dir))
    return {**identity, 'state_dir': state_dir}


def _event(launch: dict, *, session_id: str = 'session-start', source: str = 'startup') -> dict:
    return {
        'hook_event_name': 'SessionStart',
        'source': source,
        'session_id': session_id,
        'cwd': launch['work_dir'],
        'transcript_path': str(codebuddy_project_dir(
            Path(launch['work_dir']), root=Path(launch['config_dir']) / 'projects',
        ) / f'{session_id}.jsonl'),
    }


def _read(launch: dict) -> dict | None:
    return hooks.read_native_binding(
        launch['state_dir'], launch_id=launch['launch_id'],
        work_dir=Path(launch['work_dir']), config_dir=Path(launch['config_dir']),
    )


def _publish(launch: dict, event: object) -> dict:
    return hooks.publish_native_binding(launch['state_dir'], launch_id=launch['launch_id'], payload=event)


@pytest.mark.parametrize('source', ['startup', 'resume', 'clear', 'compact'])
def test_session_start_sources_bind_exact_transcript_before_file_exists(launch: dict, source: str) -> None:
    event = _event(launch, source=source)
    binding = _publish(launch, event)
    assert binding == {
        'schema_version': 1, 'launch_id': launch['launch_id'],
        'session_id': event['session_id'], 'session_path': event['transcript_path'],
    }
    assert _read(launch) == binding
    assert not Path(event['transcript_path']).exists()


def test_clear_rotates_only_native_binding_not_launcher_session(launch: dict) -> None:
    session_file = launch['state_dir'] / 'session.json'
    session_file.write_text('frozen launcher session', encoding='utf-8')
    old = _publish(launch, _event(launch))
    new = _publish(launch, _event(launch, session_id='session-after-clear', source='clear'))
    assert old['session_path'] != new['session_path']
    assert _read(launch) == new
    assert session_file.read_text(encoding='utf-8') == 'frozen launcher session'


def test_stale_launch_cannot_replace_existing_binding(launch: dict) -> None:
    expected = _publish(launch, _event(launch))
    with pytest.raises(ValueError, match='identity mismatch'):
        hooks.publish_native_binding(launch['state_dir'], launch_id='launch-stale', payload=_event(launch))
    assert _read(launch) == expected


@pytest.mark.parametrize('change', [
    {'cwd': '/different-workspace'},
    {'transcript_path': '/outside/session-start.jsonl'},
    {'session_id': '../traversal'},
    {'source': 'unknown'},
    {'hook_event_name': 'UserPromptSubmit'},
    {'transcript_path': 'relative/session-start.jsonl'},
])
def test_invalid_event_does_not_replace_existing_binding(launch: dict, change: dict) -> None:
    expected = _publish(launch, _event(launch))
    with pytest.raises(ValueError):
        _publish(launch, {**_event(launch), **change})
    assert _read(launch) == expected


def test_other_workspace_in_same_config_is_rejected(launch: dict) -> None:
    event = _event(launch)
    event['transcript_path'] = str(Path(launch['config_dir']) / 'projects' / 'other' / 'session-start.jsonl')
    with pytest.raises(ValueError, match='transcript does not match'):
        _publish(launch, event)


def test_transcript_filename_must_match_native_session_id(launch: dict) -> None:
    event = _event(launch)
    event['transcript_path'] = str(Path(event['transcript_path']).with_name('other-session.jsonl'))
    with pytest.raises(ValueError, match='transcript does not match'):
        _publish(launch, event)


def test_wrong_config_environment_is_rejected(launch: dict, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('CODEBUDDY_CONFIG_DIR', str(tmp_path / 'unrelated-config'))
    with pytest.raises(ValueError, match='config directory mismatch'):
        _publish(launch, _event(launch))
    assert _read(launch) is None


def test_command_hook_payload_without_cwd_uses_official_project_environment(launch: dict) -> None:
    event = _event(launch)
    event.pop('cwd')
    assert _publish(launch, event)['session_id'] == event['session_id']


def test_command_hook_without_cwd_or_project_environment_checks_actual_cwd(
    launch: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    event = _event(launch)
    event.pop('cwd')
    monkeypatch.delenv('CODEBUDDY_PROJECT_DIR', raising=False)
    monkeypatch.chdir(launch['work_dir'])
    assert _publish(launch, event)['session_id'] == event['session_id']


def test_symlink_escape_from_project_directory_is_rejected(launch: dict, tmp_path: Path) -> None:
    event = _event(launch)
    project_dir = Path(event['transcript_path']).parent
    project_dir.parent.mkdir(parents=True)
    outside = tmp_path / 'outside'
    outside.mkdir()
    project_dir.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        _publish(launch, event)


def test_symlink_transcript_escape_is_rejected(launch: dict, tmp_path: Path) -> None:
    event = _event(launch)
    transcript = Path(event['transcript_path'])
    transcript.parent.mkdir(parents=True)
    transcript.symlink_to(tmp_path / 'outside.jsonl')
    with pytest.raises(ValueError):
        _publish(launch, event)


@pytest.mark.skipif(os.name == 'nt', reason='POSIX owner-only mode contract')
def test_publish_is_atomic_and_private(launch: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    original_replace = os.replace
    replaced = []

    def inspect_replace(src, dst, **kwargs):
        directory_fd = kwargs.get('src_dir_fd')
        info = os.stat(src, dir_fd=directory_fd) if directory_fd is not None else os.stat(src)
        assert stat.S_IMODE(info.st_mode) == 0o600
        replaced.append(Path(dst).name)
        return original_replace(src, dst, **kwargs)

    monkeypatch.setattr(os, 'replace', inspect_replace)
    _publish(launch, _event(launch))
    assert replaced == [hooks.NATIVE_BINDING_FILENAME]
    binding = launch['state_dir'] / hooks.NATIVE_BINDING_FILENAME
    assert stat.S_IMODE(binding.stat().st_mode) == 0o600
    assert sorted(path.name for path in launch['state_dir'].iterdir()) == [
        hooks.LAUNCH_IDENTITY_FILENAME, hooks.NATIVE_BINDING_FILENAME,
    ]


def test_identity_generation_changed_during_hook_does_not_publish(launch: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    original_validate = hooks._validated_session_path

    def change_identity(*args, **kwargs):
        path = original_validate(*args, **kwargs)
        identity_file = launch['state_dir'] / hooks.LAUNCH_IDENTITY_FILENAME
        identity = json.loads(identity_file.read_text(encoding='utf-8'))
        identity['launch_id'] = 'newer-launch'
        identity_file.write_text(json.dumps(identity), encoding='utf-8')
        return path

    monkeypatch.setattr(hooks, '_validated_session_path', change_identity)
    with pytest.raises(ValueError, match='identity mismatch'):
        _publish(launch, _event(launch))
    assert not (launch['state_dir'] / hooks.NATIVE_BINDING_FILENAME).exists()


@pytest.mark.parametrize('corruption', [
    {'launch_id': 'stale-launch'},
    {'session_path': '/external/session-start.jsonl'},
    {'session_id': 'wrong-id'},
    {'schema_version': 99},
])
def test_reader_rejects_untrusted_or_stale_sidecar(launch: dict, corruption: dict) -> None:
    binding = _publish(launch, _event(launch))
    (launch['state_dir'] / hooks.NATIVE_BINDING_FILENAME).write_text(
        json.dumps({**binding, **corruption}), encoding='utf-8',
    )
    assert _read(launch) is None


def test_reader_requires_callers_workspace_and_config_identity(launch: dict) -> None:
    _publish(launch, _event(launch))
    assert hooks.read_native_binding(
        launch['state_dir'], launch_id=launch['launch_id'],
        work_dir=Path('/wrong-workspace'), config_dir=Path(launch['config_dir']),
    ) is None
    assert hooks.read_native_binding(
        launch['state_dir'], launch_id=launch['launch_id'],
        work_dir=Path(launch['work_dir']), config_dir=Path('/wrong-config'),
    ) is None


def test_reader_rejects_generation_changed_during_read(launch: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    _publish(launch, _event(launch))
    original_validate = hooks._validated_session_path

    def change_identity(*args, **kwargs):
        path = original_validate(*args, **kwargs)
        identity_file = launch['state_dir'] / hooks.LAUNCH_IDENTITY_FILENAME
        identity = json.loads(identity_file.read_text(encoding='utf-8'))
        identity['launch_id'] = 'newer-launch'
        identity_file.write_text(json.dumps(identity), encoding='utf-8')
        return path

    monkeypatch.setattr(hooks, '_validated_session_path', change_identity)
    assert _read(launch) is None


def test_direct_script_invocation_reads_stdin_without_pythonpath(launch: dict) -> None:
    env = {key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}
    result = subprocess.run(
        [sys.executable, str(Path(hooks.__file__).resolve()), '--state-dir', str(launch['state_dir']),
         '--launch-id', launch['launch_id']],
        input=json.dumps(_event(launch)), text=True, capture_output=True, env=env,
        cwd=launch['work_dir'], check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ''
    assert _read(launch)['session_id'] == 'session-start'


def test_cli_rejection_is_bounded_and_does_not_expose_payload(launch: dict) -> None:
    secret = 'secret-provider-token'
    event = {**_event(launch), 'source': secret}
    result = subprocess.run(
        [sys.executable, str(Path(hooks.__file__).resolve()), '--state-dir', str(launch['state_dir']),
         '--launch-id', launch['launch_id']],
        input=json.dumps(event), text=True, capture_output=True, check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ''
    assert result.stderr == 'CodeBuddy native session binding rejected\n'
    assert secret not in result.stderr
    assert not (launch['state_dir'] / hooks.NATIVE_BINDING_FILENAME).exists()
