"""Read the selected Agent's declared startup directory, never change it.

ccbd's fresh view is the runtime authority. Persisted specs/owned bindings only
corroborate that path; neither a browser path nor a guessed project-root fallback
can select a directory. This is not proof of the shell's current cwd or isolation.
"""
from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import selectors
import stat
import subprocess
import time

from agents.models import normalize_agent_name
from agents.store import AgentSpecStore
from mobile_gateway import MobileGatewayError
from storage.paths import PathLayout
from workspace.binding import WorkspaceBindingStore


def git_environment() -> dict[str, str]:
    # A host-side GIT_DIR/GIT_WORK_TREE must not override the verified -C path.
    return {**{key: value for key, value in os.environ.items() if not key.startswith('GIT_')},
            'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0'}


def _path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value or '\0' in value or not Path(value).is_absolute():
        raise MobileGatewayError(f'{label} unavailable', status_code=409)
    try:
        return Path(value).resolve(strict=True)
    except (OSError, RuntimeError, ValueError) as exc:
        raise MobileGatewayError(f'{label} unavailable', status_code=409) from exc


def _regular_record(path: Path) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 65536:
        raise ValueError('workspace record must be a bounded regular file')


def _owned_binding(marker: Path, *, root: Path, project_id: str, path: Path, mode: str, owner: str | None):
    try:
        _regular_record(marker)
        binding = WorkspaceBindingStore().load(marker)
        if (binding.project_id != project_id or _path(binding.target_project, 'binding project') != root or
                _path(binding.workspace_path, 'binding workspace') != path or binding.workspace_mode.value != mode or
                (owner is not None and binding.agent_name != owner)):
            raise ValueError('binding identity mismatch')
        return binding
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise MobileGatewayError('workspace binding unavailable', status_code=409) from exc


class _GitProbe:
    """One on-demand probe has a shared five-second and 8 KiB/output budget."""
    def __init__(self) -> None:
        self.deadline = time.monotonic() + 5

    def run(self, root: Path, *args: str) -> tuple[int, str]:
        command = ['git', '-c', 'core.fsmonitor=false', '-c', 'core.pager=cat', '-C', str(root), *args]
        try:
            with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  env=git_environment()) as process:
                chunks, size = [], 0
                with selectors.DefaultSelector() as selector:
                    selector.register(process.stdout, selectors.EVENT_READ)
                    while selector.get_map():
                        remaining = self.deadline - time.monotonic()
                        if remaining <= 0:
                            process.kill()
                            process.wait()
                            raise MobileGatewayError('workspace git probe timed out', status_code=504)
                        for event, _ in selector.select(min(remaining, 0.1)):
                            chunk = os.read(event.fd, min(8193 - size, 8192))
                            if not chunk:
                                selector.unregister(event.fileobj)
                                continue
                            size += len(chunk)
                            if size > 8192:
                                process.kill()
                                process.wait()
                                raise MobileGatewayError('workspace git probe output exceeded limit', status_code=409)
                            chunks.append(chunk)
                try:
                    code = process.wait(timeout=max(0.001, self.deadline - time.monotonic()))
                except subprocess.TimeoutExpired as exc:
                    process.kill()
                    process.wait()
                    raise MobileGatewayError('workspace git probe timed out', status_code=504) from exc
                return code, b''.join(chunks).decode('utf-8', errors='strict').strip()
        except (OSError, UnicodeError, subprocess.TimeoutExpired) as exc:
            raise MobileGatewayError('workspace git probe unavailable', status_code=409) from exc


def inspect_workspace(project, view: dict, agent_name: str) -> dict:
    try:
        if normalize_agent_name(agent_name) != agent_name:
            raise ValueError('noncanonical name')
    except ValueError as exc:
        raise MobileGatewayError('invalid agent name', status_code=400) from exc
    agents = [agent for agent in view.get('agents', []) if isinstance(agent, dict)]
    selected = [agent for agent in agents if agent.get('name') == agent_name]
    if not selected:
        raise MobileGatewayError('agent not found', status_code=404)
    if len(selected) != 1:
        raise MobileGatewayError('ambiguous agent identity', status_code=409)
    identity = view.get('project', {})
    root = _path(str(project.project_root), 'registered project root')
    if identity.get('id') != project.project_id or _path(identity.get('root'), 'project root') != root:
        raise MobileGatewayError('project identity mismatch', status_code=409)
    namespace = view.get('namespace')
    epoch = namespace.get('epoch') if isinstance(namespace, dict) else None
    if not isinstance(epoch, int) or isinstance(epoch, bool) or epoch < 0:
        raise MobileGatewayError('workspace namespace unavailable', status_code=409)
    path = _path(selected[0].get('workspace_path'), 'agent workspace')
    if not path.is_dir():
        raise MobileGatewayError('agent workspace unavailable', status_code=409)
    try:
        layout = PathLayout(root)
        if layout.project_id != project.project_id:
            raise ValueError('project identity mismatch')
        spec_path = layout.agent_spec_path(agent_name)
        if spec_path.exists() or spec_path.is_symlink():
            _regular_record(spec_path)
        spec = AgentSpecStore(layout).load(agent_name)
        if spec is not None and spec.name != agent_name:
            raise ValueError('agent spec identity mismatch')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise MobileGatewayError('workspace spec unavailable', status_code=409) from exc
    if path == root:
        if spec is not None and spec.workspace_mode.value != 'inplace':
            raise MobileGatewayError('workspace spec path mismatch', status_code=409)
    elif spec is None or spec.workspace_mode.value not in ('git-worktree', 'copy'):
        raise MobileGatewayError('workspace binding unavailable', status_code=409)
    elif spec.workspace_path is not None:
        if _path(spec.workspace_path, 'declared workspace') != path:
            raise MobileGatewayError('workspace spec path mismatch', status_code=409)
    else:
        if spec.workspace_group is not None:
            pointer = _owned_binding(layout.workspace_group_binding_path(spec.workspace_group), root=root,
                                     project_id=project.project_id, path=path, mode=spec.workspace_mode.value, owner=None)
            owner = pointer.agent_name
        else:
            if spec.workspace_root is not None and not Path(spec.workspace_root).expanduser().is_absolute():
                raise MobileGatewayError('workspace root unavailable', status_code=409)
            expected = layout.workspace_path(agent_name, workspace_root=spec.workspace_root)
            if _path(str(expected), 'declared workspace') != path:
                raise MobileGatewayError('workspace spec path mismatch', status_code=409)
            owner = agent_name
        _owned_binding(path / '.ccb-workspace.json', root=root, project_id=project.project_id,
                       path=path, mode=spec.workspace_mode.value, owner=owner)
    probe = _GitProbe()
    code, toplevel = probe.run(path, 'rev-parse', '--show-toplevel')
    git_state, branch, head = 'not_git', None, None
    is_copy = spec is not None and spec.workspace_mode.value == 'copy'
    if code and ((path / '.git').exists() or (path / '.git').is_symlink()):
        raise MobileGatewayError('workspace git probe unavailable', status_code=409)
    if code == 0 and _path(toplevel, 'git toplevel') != path:
        if not is_copy:
            raise MobileGatewayError('workspace git toplevel mismatch', status_code=409)
        code = 1  # A copy inside the parent repository is not its own Git root.
    if code == 0:
        code, branch_value = probe.run(path, 'symbolic-ref', '--quiet', '--short', 'HEAD')
        if code not in (0, 1):
            raise MobileGatewayError('workspace branch unavailable', status_code=409)
        git_state, branch = ('attached', branch_value) if code == 0 else ('detached', None)
        code, head_value = probe.run(path, 'rev-parse', '--verify', 'HEAD')
        head = head_value if code == 0 else None
    if path != root and not is_copy:
        if git_state == 'not_git':
            raise MobileGatewayError('workspace git unavailable', status_code=409)
        common_dirs = []
        for git_root in (root, path):
            code, common_dir = probe.run(git_root, 'rev-parse', '--path-format=absolute', '--git-common-dir')
            if code:
                raise MobileGatewayError('workspace git common directory unavailable', status_code=409)
            common_dirs.append(_path(common_dir, 'git common directory'))
        if common_dirs[0] != common_dirs[1]:
            raise MobileGatewayError('workspace git common directory mismatch', status_code=409)
    shared_agents = []
    for agent in agents:
        try:
            if _path(agent.get('workspace_path'), 'agent workspace') == path:
                shared_agents.append(agent['name'])
        except MobileGatewayError:
            pass
    return {'schema_version': 1, 'project_id': project.project_id, 'namespace_epoch': epoch, 'agent': agent_name,
            'workspace': {'path': str(path), 'source': 'ccbd_runtime',
                          'mode': spec.workspace_mode.value if spec is not None else None,
                          'mode_source': 'persisted_agent_spec' if spec is not None else None,
                          'shared_agents': sorted(set(shared_agents)), 'git_state': git_state,
                          'branch': branch, 'head': head, 'observed_at': datetime.now(timezone.utc).isoformat(),
                          'scope': 'startup_or_declared_directory', 'attribution': 'workspace_not_agent',
                          'isolation': 'not_guaranteed'}}
