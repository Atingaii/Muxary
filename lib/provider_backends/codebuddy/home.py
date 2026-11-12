from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from provider_core.inherited_skills import (
    materialize_required_control_skills,
    required_control_skill_names,
    route_inherited_skill_entries,
)
from provider_core.one_way_inheritance import (
    copy_regular_file,
    copy_regular_tree,
    ensure_private_descendant_directory,
    ensure_private_inheritance_directory,
)
from provider_core.source_home import current_provider_source_home
from provider_profiles import provider_api_env_keys
from storage.atomic import atomic_write_json


_CREDENTIAL_ENV_KEYS = {'CODEBUDDY_API_KEY', 'CODEBUDDY_AUTH_TOKEN'}


def materialize_codebuddy_home(
    home_dir: Path,
    *,
    profile=None,
    source_home: Path | None = None,
    extra_env: dict[str, str] | None = None,
) -> Path:
    """Seed a private CodeBuddy account without copying conversation history.

    Plugin caches are intentionally not copied: installed plugins may contain
    mutable repositories and very large toolchains. Native --plugin-dir remains
    available for explicitly selected plugins.
    """
    source = Path(source_home).expanduser() if source_home is not None else current_provider_source_home()
    source_config = source / '.codebuddy'
    if source_home is None and not os.environ.get('CCB_SOURCE_HOME'):
        override = str(os.environ.get('CODEBUDDY_CONFIG_DIR') or '').strip()
        if override and 'provider-state' not in Path(override).parts:
            source_config = Path(override).expanduser()
    home = ensure_private_inheritance_directory(home_dir, source)
    config = ensure_private_descendant_directory(home, Path('.codebuddy'))
    ensure_private_inheritance_directory(config, source_config)
    ensure_private_descendant_directory(config, Path('projects'))

    if _inherits(profile, 'auth'):
        if copy_regular_file(source_config / '.credentials.json', config / '.credentials.json'):
            (config / '.credentials.json').chmod(0o600)
        _materialize_native_login(home, source)
    if _inherits(profile, 'config'):
        for name in ('settings.json', 'models.json', 'mcp.json'):
            copy_regular_file(source_config / name, config / name)
    _filter_inherited_api_settings(config / 'settings.json', profile=profile, extra_env=extra_env)
    if _inherits(profile, 'memory'):
        copy_regular_file(source_config / 'CODEBUDDY.md', config / 'CODEBUDDY.md')
    if _inherits(profile, 'commands'):
        for name in ('commands', 'agents'):
            copy_regular_tree(source_config / name, config / name)
    route_inherited_skill_entries(
        source_config / 'skills',
        config / 'skills',
        enabled=_inherits(profile, 'skills'),
        label='codebuddy-inherited-skills',
        exclude=required_control_skill_names('codebuddy'),
        include_patterns=tuple(getattr(profile, 'inherited_skill_include', ()) or ()),
        exclude_patterns=tuple(getattr(profile, 'inherited_skill_exclude', ()) or ()),
    )
    materialize_required_control_skills(provider='codebuddy', target_dir=config / 'skills')
    return home


def _materialize_native_login(home: Path, source: Path) -> None:
    # .credentials.json contains MCP OAuth, not the native account login. The
    # default CodeBuddy product stores that one account in shared extension data.
    # Do not copy auth backups, IDE state, or the local_storage/history trees.
    if sys.platform == 'darwin':
        base = Path('Library/Application Support')
    elif sys.platform == 'win32':
        base = Path('AppData/Local')
    else:
        base = Path('.local/share')
    relative = base / 'CodeBuddyExtension/Data/Public/auth'
    original = source / relative / 'Tencent-Cloud.coding-copilot.info'
    marker = original.with_name(original.name + '.logged-out')
    if not original.is_file() and not marker.is_file():
        return
    target_dir = ensure_private_descendant_directory(home, relative)
    target = target_dir / original.name
    target_marker = target_dir / marker.name
    if marker.is_file():
        if copy_regular_file(marker, target_marker):
            target_marker.chmod(0o600)
        return
    if copy_regular_file(original, target):
        target.chmod(0o600)
        if target_marker.is_file() or target_marker.is_symlink():
            target_marker.unlink()


def _inherits(profile, name: str) -> bool:
    return True if profile is None else bool(getattr(profile, f'inherit_{name}', True))


def codebuddy_api_env_to_clear(*, profile=None, extra_env: dict[str, str] | None = None) -> set[str]:
    """Use the same inheritance boundary for shell and native settings.env."""
    cleared: set[str] = set()
    if not _inherits(profile, 'api'):
        cleared.update(provider_api_env_keys('codebuddy'))
    if not _inherits(profile, 'auth'):
        cleared.update(_CREDENTIAL_ENV_KEYS)
    explicit = {**dict(getattr(profile, 'env', {}) or {}), **dict(extra_env or {})}
    if any(str(explicit.get(key) or '').strip() for key in _CREDENTIAL_ENV_KEYS):
        cleared.update(_CREDENTIAL_ENV_KEYS)
    if str(explicit.get('CODEBUDDY_BASE_URL') or '').strip():
        cleared.add('CODEBUDDY_BASE_URL')
    return cleared


def _filter_inherited_api_settings(path: Path, *, profile, extra_env: dict[str, str] | None) -> None:
    cleared = codebuddy_api_env_to_clear(profile=profile, extra_env=extra_env)
    if not cleared or not path.exists():
        return
    # Never let a legacy managed alias turn projection into an external write.
    if path.is_symlink():
        path.unlink()
        return
    try:
        settings = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise ValueError('cannot apply CodeBuddy API inheritance to invalid private settings.json') from exc
    if not isinstance(settings, dict):
        raise ValueError('CodeBuddy private settings.json must contain a JSON object')
    changed = False
    env = settings.get('env')
    if isinstance(env, dict):
        for key in cleared:
            if key in env:
                del env[key]
                changed = True
    if _CREDENTIAL_ENV_KEYS <= cleared and 'apiKeyHelper' in settings:
        del settings['apiKeyHelper']
        changed = True
    if changed:
        atomic_write_json(path, settings)


__all__ = ['materialize_codebuddy_home', 'codebuddy_api_env_to_clear']
