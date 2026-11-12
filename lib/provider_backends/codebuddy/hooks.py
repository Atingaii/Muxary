"""Bind CodeBuddy SessionStart events to a launch-scoped native transcript.

This file is also a command hook entry point, invoked by its absolute path.
Only CCB-owned sidecars are written; provider configuration and transcripts
are never modified. No transcript discovery or latest-session fallback exists.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

if __package__ in {None, ''}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from provider_backends.codebuddy.native_log import codebuddy_project_dir
from storage.atomic import atomic_write_json


LAUNCH_IDENTITY_FILENAME = 'codebuddy-launch.json'
NATIVE_BINDING_FILENAME = 'native-binding.json'
_SESSION_ID_RE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z')
_SESSION_START_SOURCES = frozenset({'startup', 'resume', 'clear', 'compact'})


def _absolute_path(value: object) -> Path:
    if not isinstance(value, (str, Path)) or not str(value).strip():
        raise ValueError('Expected an absolute path')
    path = Path(value).expanduser()
    if not path.is_absolute():
        raise ValueError('Expected an absolute path')
    return path.resolve(strict=False)


def _read_object(path: Path) -> dict:
    if path.is_symlink():
        raise ValueError('Binding sidecars must not be symlinks')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise ValueError('Expected a JSON object')
    return value


def _read_launch_identity(state_dir: Path, launch_id: str) -> dict:
    if not isinstance(launch_id, str) or not launch_id.strip():
        raise ValueError('A launch ID is required')
    identity = _read_object(state_dir / LAUNCH_IDENTITY_FILENAME)
    if identity.get('schema_version') != 1 or identity.get('launch_id') != launch_id:
        raise ValueError('CodeBuddy launch identity mismatch')
    return {
        'schema_version': 1,
        'launch_id': launch_id,
        'work_dir': _absolute_path(identity.get('work_dir')),
        'config_dir': _absolute_path(identity.get('config_dir')),
    }


def _validated_session_path(session_id: object, session_path: object, identity: dict) -> Path:
    if not isinstance(session_id, str) or not _SESSION_ID_RE.fullmatch(session_id):
        raise ValueError('Invalid CodeBuddy session ID')
    config_dir = identity['config_dir']
    projects_root = (config_dir / 'projects').resolve(strict=False)
    project_dir = codebuddy_project_dir(identity['work_dir'], root=projects_root).resolve(strict=False)
    # Reject symlink escapes as well as another workspace under the same root.
    if not projects_root.is_relative_to(config_dir) or project_dir.parent != projects_root:
        raise ValueError('CodeBuddy project path is outside its config directory')
    path = _absolute_path(session_path)
    if path.parent != project_dir or path.name != f'{session_id}.jsonl':
        raise ValueError('CodeBuddy transcript does not match this workspace and session')
    return path


def publish_native_binding(state_dir: Path, *, launch_id: str, payload: object) -> dict:
    """Validate one native SessionStart event and atomically publish its binding."""
    state_dir = _absolute_path(state_dir)
    identity = _read_launch_identity(state_dir, launch_id)
    if not isinstance(payload, dict):
        raise ValueError('Expected a SessionStart object')
    if payload.get('hook_event_name', 'SessionStart') != 'SessionStart':
        raise ValueError('Expected a SessionStart event')
    if payload.get('source') not in _SESSION_START_SOURCES:
        raise ValueError('Unsupported SessionStart source')
    # CodeBuddy 2.178.0's command-hook SessionStart payload may omit cwd. Its
    # HookManager supplies CODEBUDDY_PROJECT_DIR; spawn also inherits CLI cwd.
    cwd = payload.get('cwd') if 'cwd' in payload else os.environ.get('CODEBUDDY_PROJECT_DIR') or Path.cwd()
    if _absolute_path(cwd) != identity['work_dir']:
        raise ValueError('CodeBuddy hook workspace mismatch')
    config_dir = (os.environ.get('CODEBUDDY_CONFIG_DIR') or '').strip()
    actual_config = _absolute_path(config_dir or Path.home() / '.codebuddy')
    if actual_config != identity['config_dir']:
        raise ValueError('CodeBuddy hook config directory mismatch')
    session_id = payload.get('session_id')
    session_path = _validated_session_path(session_id, payload.get('transcript_path'), identity)
    binding = {
        'schema_version': 1,
        'launch_id': launch_id,
        'session_id': session_id,
        'session_path': str(session_path),
    }
    # Reject generation changes observed during validation. Readers validate
    # the binding's launch_id too, so a remaining read/replace race fails closed
    # instead of binding another launch's session.
    if _read_launch_identity(state_dir, launch_id) != identity:
        raise ValueError('CodeBuddy launch identity changed during the hook')
    atomic_write_json(state_dir / NATIVE_BINDING_FILENAME, binding)
    return binding


def read_native_binding(
    state_dir: Path,
    *,
    launch_id: str,
    work_dir: Path,
    config_dir: Path,
) -> dict | None:
    """Read a validated binding at task start, then pin it for the whole task."""
    try:
        state_dir = _absolute_path(state_dir)
        identity = _read_launch_identity(state_dir, launch_id)
        if identity['work_dir'] != _absolute_path(work_dir) or identity['config_dir'] != _absolute_path(config_dir):
            return None
        binding = _read_object(state_dir / NATIVE_BINDING_FILENAME)
        if binding.get('schema_version') != 1 or binding.get('launch_id') != launch_id:
            return None
        path = _validated_session_path(binding.get('session_id'), binding.get('session_path'), identity)
        if _read_launch_identity(state_dir, launch_id) != identity:
            return None
        return {
            'schema_version': 1,
            'launch_id': launch_id,
            'session_id': binding['session_id'],
            'session_path': str(path),
        }
    except (OSError, ValueError, TypeError, RuntimeError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', required=True, type=Path)
    parser.add_argument('--launch-id', required=True)
    args = parser.parse_args(argv)
    try:
        publish_native_binding(args.state_dir, launch_id=args.launch_id, payload=json.load(sys.stdin))
    except (OSError, ValueError, TypeError, RuntimeError):
        # Never inject hook input, paths, or provider credentials into a prompt.
        print('CodeBuddy native session binding rejected', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())


__all__ = [
    'LAUNCH_IDENTITY_FILENAME',
    'NATIVE_BINDING_FILENAME',
    'publish_native_binding',
    'read_native_binding',
]
