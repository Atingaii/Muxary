from __future__ import annotations

import json
import os
import re
import shlex
import sys
import uuid
from pathlib import Path

from agents.models import AgentSpec
from cli.context import CliContext
from cli.models import ParsedStartCommand
from provider_backends.native_cli_support.home import build_native_private_env
from provider_core.caller_env import caller_context_env, export_env_clause, join_env_prefix, provider_user_session_env
from provider_core.contracts import ProviderRuntimeLauncher
from provider_core.one_way_inheritance import ensure_private_directory
from provider_core.pathing import session_filename_for_agent
from provider_core.runtime_shared import apply_provider_command_template, provider_start_parts
from provider_profiles import load_resolved_provider_profile
from project.identity import normalize_work_dir
from storage.atomic import atomic_write_json
from workspace.models import WorkspacePlan

from .home import codebuddy_api_env_to_clear, materialize_codebuddy_home
from .native_log import codebuddy_project_dir

_PERMISSION_FLAGS = {'--permission-mode', '--dangerously-skip-permissions', '-y'}
# These modes either select an unbound session or do not run an interactive pane.
_UNMANAGED_FLAGS = {
    '--session-id', '--resume', '-r', '--continue', '-c', '--fork-session',
    '--no-session-persistence', '--print', '-p', '--acp', '--serve', '--bg', '--background', '--',
    '--worktree', '-w', '--worktree-branch', '--tmux', '--tmux-classic',
}


def build_runtime_launcher() -> ProviderRuntimeLauncher:
    return ProviderRuntimeLauncher(
        provider='codebuddy',
        launch_mode='simple_tmux',
        prepare_launch_context=prepare_launch_context,
        build_start_cmd=build_start_cmd,
        build_session_payload=build_session_payload,
    )


def prepare_launch_context(
    context: CliContext,
    spec: AgentSpec,
    plan: WorkspacePlan,
    runtime_dir: Path,
    prepared_state: dict[str, object],
) -> dict[str, object]:
    prepared = dict(prepared_state or {})
    work_dir = Path(str(prepared.get('run_cwd') or plan.workspace_path)).resolve()
    state_dir = context.paths.agent_provider_state_dir(spec.name, 'codebuddy')
    home = materialize_codebuddy_home(
        state_dir / 'home', profile=load_resolved_provider_profile(Path(runtime_dir)),
        extra_env=spec.env,
    )
    config = home / '.codebuddy'
    prepared.update({
        'workspace_path': str(work_dir),
        'codebuddy_home': str(home),
        'codebuddy_state_dir': str(state_dir),
        'codebuddy_config_dir': str(config),
    })
    saved_path = context.paths.ccb_dir / session_filename_for_agent('codebuddy', spec.name)
    saved = _read_object(saved_path)
    if (
        saved.get('agent_name') == spec.name
        and saved.get('ccb_project_id') == context.project.project_id
        and normalize_work_dir(str(saved.get('work_dir') or '')) == normalize_work_dir(work_dir)
        and str(saved.get('codebuddy_config_dir') or '') == str(config)
    ):
        # Native /clear rotates the ID. Only this generation's validated
        # SessionStart sidecar may replace the original startup binding.
        from .hooks import read_native_binding

        binding = read_native_binding(
            state_dir,
            launch_id=str(saved.get('codebuddy_launch_id') or saved.get('ccb_session_id') or ''),
            work_dir=work_dir,
            config_dir=config,
        )
        # With generation-aware hooks, a missing/invalid sidecar may mean
        # /clear already rotated the native ID. Never resurrect startup history.
        if binding is None:
            binding = {} if saved.get('codebuddy_launch_id') else saved
        session_id = str(binding.get('session_id') or binding.get('codebuddy_session_id') or '')
        session_path = str(binding.get('session_path') or binding.get('codebuddy_session_path') or '')
        expected = _native_session_path(work_dir, config, session_id)
        if (
            expected is not None
            and session_path == str(expected)
            and expected.resolve(strict=False) == expected
            and expected.is_file()
            and not expected.is_symlink()
            and expected.stat().st_nlink == 1
        ):
            prepared['codebuddy_resume_session_id'] = session_id
            prepared['codebuddy_resume_session_path'] = str(expected)
    return prepared


def build_start_cmd(
    command: ParsedStartCommand,
    spec: AgentSpec,
    runtime_dir: Path,
    launch_session_id: str,
    *,
    prepared_state: dict[str, object] | None = None,
) -> str:
    prepared = prepared_state if prepared_state is not None else {}
    for name in ('workspace_path', 'codebuddy_home', 'codebuddy_config_dir', 'codebuddy_state_dir'):
        if not str(prepared.get(name) or '').strip():
            raise ValueError(f'CodeBuddy launcher requires prepared {name}')
    work_dir = Path(str(prepared['workspace_path']))
    profile = load_resolved_provider_profile(Path(runtime_dir))
    explicit_env = {**dict(getattr(profile, 'env', {}) or {}), **spec.env}
    project_config_value = str(explicit_env.get('CODEBUDDY_PROJECT_CONFIG_DIR', os.environ.get('CODEBUDDY_PROJECT_CONFIG_DIR')) or '').strip() or str(work_dir / '.codebuddy')
    project_config = Path(project_config_value)
    if not project_config.is_absolute():
        project_config = work_dir / project_config
    parts = [*provider_start_parts('codebuddy'), *spec.startup_args]
    incompatible = next((part for part in parts if _is_unmanaged_option(str(part))), None)
    if incompatible:
        raise ValueError(f'CodeBuddy managed panes own session identity and persistence; remove {incompatible} from startup_args')
    parts, settings = _extract_settings(parts, work_dir=work_dir)
    selected_sources = _enabled_setting_sources(parts)
    settings_sources = [settings]
    if 'user' in selected_sources:
        settings_sources.append(_read_settings_object(Path(str(prepared['codebuddy_config_dir'])) / 'settings.json'))
    if 'project' in selected_sources:
        settings_sources.append(_read_settings_object(project_config / 'settings.json'))
    if 'local' in selected_sources:
        settings_sources.append(_read_settings_object(project_config / 'settings.local.json'))
    for policy in ('disableAllHooks', 'allowManagedHooksOnly'):
        if any(configured.get(policy) is True for configured in settings_sources):
            raise ValueError(f'CodeBuddy {policy}=true conflicts with the required managed SessionStart hook')
    for configured in settings_sources:
        configured_env = configured.get('env')
        if isinstance(configured_env, dict) and 'DISABLE_AUTOUPDATER' in configured_env:
            if str(configured_env['DISABLE_AUTOUPDATER']).strip().lower() not in {'1', 'true'}:
                raise ValueError('CodeBuddy settings.env.DISABLE_AUTOUPDATER must not enable shared-binary updates in a managed pane')
    if not any(str(part).split('=', 1)[0] in _PERMISSION_FLAGS for part in parts):
        if command.auto_permission:
            parts.append('--dangerously-skip-permissions')
        else:
            # Do not inherit an account-level bypass/auto permission mode when
            # the CCB agent explicitly uses manual permission handling.
            parts.extend(['--permission-mode', 'default'])
    resume_id = str(prepared.get('codebuddy_resume_session_id') or '')
    if command.restore and not command.reset_context and resume_id:
        session_id = resume_id
        parts.extend(['--resume', session_id])
        resume_status = 'exact_session_selected'
    else:
        session_id = str(uuid.uuid4())
        parts.extend(['--session-id', session_id])
        resume_status = 'fresh_session'
    config = Path(str(prepared['codebuddy_config_dir']))
    state = Path(str(prepared['codebuddy_state_dir']))
    session_path = _native_session_path(work_dir, config, session_id)
    if session_path is None:
        raise ValueError('CodeBuddy managed session identity must be a canonical UUID')
    native_launch_id = str(uuid.uuid4())
    hook_command = ' '.join(shlex.quote(str(part)) for part in (
        sys.executable, Path(__file__).with_name('hooks.py').resolve(),
        '--state-dir', state, '--launch-id', native_launch_id,
    ))
    hooks = settings.setdefault('hooks', {})
    if not isinstance(hooks, dict):
        raise ValueError('CodeBuddy --settings hooks must be an object')
    session_hooks = hooks.setdefault('SessionStart', [])
    if not isinstance(session_hooks, list):
        raise ValueError('CodeBuddy --settings hooks.SessionStart must be an array')
    session_hooks.append({
        'matcher': '^(startup|resume|clear|compact)$',
        'hooks': [{'type': 'command', 'command': hook_command}],
    })
    settings_path = Path(runtime_dir) / 'codebuddy-hooks-settings.json'
    parts.extend(['--settings', str(settings_path)])
    start_cmd = ' '.join(shlex.quote(str(part)) for part in parts)
    start_cmd = apply_provider_command_template(start_cmd, spec.provider_command_template)
    private_env = build_native_private_env(
        Path(str(prepared['codebuddy_home'])), extra_path_env_names=('CODEBUDDY_CONFIG_DIR', 'CODEBUDDY_PROJECT_CONFIG_DIR'),
    )
    private_env['CODEBUDDY_CONFIG_DIR'] = str(config)
    private_env['CODEBUDDY_PROJECT_CONFIG_DIR'] = project_config_value
    # Native self-update changes the shared CLI binary even with private HOME.
    # Keep a managed session on its verified CLI version for its whole lifetime.
    private_env['DISABLE_AUTOUPDATER'] = '1'
    caller_env = caller_context_env(actor=spec.name, runtime_dir=Path(runtime_dir), launch_session_id=launch_session_id)
    # CodeBuddy applies settings.env inside each native agent run, after shell
    # exports. Reject conflicting policy rather than letting it escape private
    # storage or impersonate a different CCB caller/session at that later seam.
    managed_env = {
        **{key: value for key, value in private_env.items() if key != 'DISABLE_AUTOUPDATER'},
        **{key: value for key, value in caller_env.items() if key.startswith('CCB_CALLER_') or key == 'CCB_SESSION_ID'},
    }
    for configured in settings_sources:
        configured_env = configured.get('env')
        if isinstance(configured_env, dict):
            for key in managed_env.keys() & configured_env.keys():
                if str(configured_env[key]) != managed_env[key]:
                    raise ValueError(f'CodeBuddy settings.env.{key} conflicts with the managed storage or caller identity')
    env_prefix = join_env_prefix(
        export_env_clause(provider_user_session_env()),
        *(f'unset {key}' for key in sorted(codebuddy_api_env_to_clear(profile=profile, extra_env=spec.env))),
        export_env_clause(explicit_env),
        export_env_clause(private_env),
        export_env_clause(caller_env),
    )
    # Reject invalid settings/templates before publishing a new generation.
    # Advancing identity early would invalidate the still-running session's
    # valid sidecar even though no replacement pane can be launched.
    ensure_private_directory(state)
    ensure_private_directory(session_path.parent)
    atomic_write_json(settings_path, settings)
    atomic_write_json(state / 'codebuddy-launch.json', {
        'schema_version': 1,
        'launch_id': native_launch_id,
        'work_dir': str(work_dir.resolve()),
        'config_dir': str(config.resolve()),
    })
    prepared.update({
        'codebuddy_resume_status': resume_status,
        'codebuddy_launch_id': native_launch_id,
        'codebuddy_session_id': session_id,
        'codebuddy_session_path': str(session_path),
    })
    return f'{env_prefix}; {start_cmd}' if env_prefix else start_cmd


def build_session_payload(
    context: CliContext,
    spec: AgentSpec,
    plan: WorkspacePlan,
    runtime_dir: Path,
    run_cwd: Path,
    pane_id: str,
    pane_title_marker: str,
    start_cmd: str,
    launch_session_id: str,
    prepared_state: dict[str, object],
) -> dict[str, object]:
    prepared = prepared_state or {}
    return {
        'ccb_session_id': launch_session_id,
        'agent_name': spec.name,
        'ccb_project_id': context.project.project_id,
        'runtime_dir': str(runtime_dir),
        'state_dir': str(prepared.get('codebuddy_state_dir') or ''),
        'completion_artifact_dir': str(Path(runtime_dir) / 'completion'),
        'terminal': 'tmux',
        'tmux_session': pane_id,
        'pane_id': pane_id,
        'pane_title_marker': pane_title_marker,
        'workspace_path': str(plan.workspace_path),
        'work_dir': str(run_cwd),
        'start_dir': str(context.project.project_root),
        'start_cmd': start_cmd,
        'codebuddy_launch_id': str(prepared.get('codebuddy_launch_id') or ''),
        'codebuddy_home': str(prepared.get('codebuddy_home') or ''),
        'codebuddy_config_dir': str(prepared.get('codebuddy_config_dir') or ''),
        'codebuddy_session_id': str(prepared.get('codebuddy_session_id') or ''),
        'codebuddy_session_path': str(prepared.get('codebuddy_session_path') or ''),
        'codebuddy_resume_status': str(prepared.get('codebuddy_resume_status') or ''),
    }


def _is_unmanaged_option(part: str) -> bool:
    return part.split('=', 1)[0] in _UNMANAGED_FLAGS or (
        len(part) > 2 and part.startswith(('-r', '-c', '-p', '-w')) and not part.startswith('--')
    )


def _native_session_path(work_dir: Path, config_dir: Path, session_id: str) -> Path | None:
    # CCB creates UUIDs rather than accepting arbitrary native path components.
    try:
        if str(uuid.UUID(session_id)) != session_id:
            return None
    except (ValueError, AttributeError):
        return None
    return codebuddy_project_dir(work_dir, root=config_dir / 'projects') / f'{session_id}.jsonl'


def _read_object(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _read_settings_object(path: Path) -> dict:
    # Native CodeBuddy accepts JSONC. Until a compatible parser is available,
    # fail explicitly rather than treating an unvalidated env/policy as absent.
    try:
        raw = path.read_text(encoding='utf-8')
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeError) as exc:
        raise ValueError(f'cannot validate enabled CodeBuddy settings file: {path}') from exc
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ValueError(f'CodeBuddy managed startup requires standard JSON in enabled settings file (JSONC is not supported): {path}') from exc
    if not isinstance(data, dict):
        raise ValueError(f'CodeBuddy enabled settings file must contain a JSON object: {path}')
    return data


def _extract_settings(parts: list[str], *, work_dir: Path) -> tuple[list[str], dict]:
    remaining: list[str] = []
    settings: dict = {}
    iterator = iter(parts)
    for part in iterator:
        if part != '--settings' and not part.startswith('--settings='):
            remaining.append(part)
            continue
        raw = part.split('=', 1)[1] if '=' in part else next(iterator, '')
        if not raw:
            raise ValueError('CodeBuddy --settings requires a JSON object or JSON file')
        if not raw.lstrip().startswith('{'):
            path = Path(raw).expanduser()
            if not path.is_absolute():
                path = work_dir / path
            try:
                raw = path.read_text(encoding='utf-8')
            except OSError as exc:
                raise ValueError(f'cannot read CodeBuddy --settings file: {path}') from exc
        try:
            value = json.loads(raw)
        except ValueError as exc:
            raise ValueError('CodeBuddy --settings must contain valid JSON') from exc
        if not isinstance(value, dict):
            raise ValueError('CodeBuddy --settings must contain a JSON object')
        settings.update(value)
    return remaining, settings


def _enabled_setting_sources(parts: list[str]) -> set[str]:
    """Match CodeBuddy's native --setting-sources disk-scope selection."""
    value = None
    for index, part in enumerate(parts):
        if part == '--setting-sources':
            if index + 1 == len(parts):
                raise ValueError('CodeBuddy --setting-sources requires a value')
            value = parts[index + 1]
        elif part.startswith('--setting-sources='):
            value = part.split('=', 1)[1]
    defaults = {'user', 'project', 'local'}
    if not value:
        return defaults
    if value.strip().lower() in {'', 'none'}:
        return set()
    # Native validation lowercases tokens but mapping uses their original case;
    # retain that behavior rather than silently changing actual source loading.
    return set(re.split(r'[,\s]+', value.strip())) & defaults or defaults


__all__ = ['build_runtime_launcher', 'prepare_launch_context', 'build_start_cmd', 'build_session_payload']
