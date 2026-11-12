from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from typing import TextIO
import webbrowser

from cli.context import CliContextBuilder
from cli.models import ParsedConfigUiCommand
from cli.services.config_ui import prepare_config_ui
from cli.services.mobile import _running_server_project_registry

_PROJECT_START_TIMEOUT = 45
_PROJECT_START_OUTPUT_LIMIT = 65536


def run_muxary(
    argv: list[str], *, script_root: Path, cwd: Path | None = None,
    stdout: TextIO | None = None, stderr: TextIO | None = None,
) -> int:
    """Keep one public CLI seam: Web by default, unchanged CCB for other commands."""
    out, err = stdout or sys.stdout, stderr or sys.stderr
    root = Path(script_root)
    current = Path(cwd or Path.cwd()).resolve()
    tokens = list(argv)
    if tokens and tokens[0] in {'--version', '-v', '--print-version', 'version'}:
        print(f'Muxary {(root / "VERSION").read_text().strip()}', file=out)
        return 0
    if tokens and tokens[0] == 'tui':
        return _delegate_ccb(tokens[1:], script_root=root, cwd=current)
    if tokens and not tokens[0].startswith('-') and tokens[0] not in {'web', 'help'}:
        return _delegate_ccb(tokens, script_root=root, cwd=current)
    if tokens[:1] == ['help']:
        tokens = ['--help']
    if tokens[:1] == ['web']:
        tokens = tokens[1:]
    parser = argparse.ArgumentParser(
        prog='muxary',
        description='Muxary local Web workbench, powered by the CCB runtime.',
        epilog='muxary tui [CCB_ARGS...] opens the existing TUI; ccb retains its original behavior.',
    )
    parser.add_argument('--project', type=Path, help='start/include this project using the existing CCB runtime')
    parser.add_argument('--port', type=int, default=0, help='loopback port (default: choose a free port)')
    parser.add_argument('--no-open', action='store_true', help='print the authenticated URL without opening a browser')
    try:
        with redirect_stdout(out), redirect_stderr(err):
            options = parser.parse_args(tokens)
    except SystemExit as exc:
        return int(exc.code)
    if not 0 <= options.port <= 65535:
        print('muxary: --port must be between 0 and 65535', file=err)
        return 2
    try:
        return _serve_web(options, script_root=root, cwd=current, stdout=out, stderr=err)
    except subprocess.TimeoutExpired:
        print('muxary: CCB startup timed out; project agents may still be running. Refresh the project list before starting again.', file=err)
        return 1
    except (OSError, RuntimeError, ValueError) as exc:
        print(f'muxary: {exc}', file=err)
        return 1


def _delegate_ccb(tokens: list[str], *, script_root: Path, cwd: Path) -> int:
    # Selecting `muxary tui` explicitly authorizes this fork's source runtime;
    # the old ccb source-checkout diagnostic gate itself is left unchanged.
    env = {**os.environ, 'CCB_SOURCE_RUNTIME_OK': '1'}
    return subprocess.call([str(script_root / 'ccb'), *tokens], cwd=cwd, env=env)


def _serve_web(options, *, script_root: Path, cwd: Path, stdout: TextIO, stderr: TextIO) -> int:
    from .service import WorkbenchService, _project_open_root, build_workbench_server

    assets = script_root / 'assets' / 'workbench'
    if not (assets / 'index.html').is_file():
        raise RuntimeError('Web assets are missing; run `npm --prefix web ci && npm --prefix web run build` first')
    registry = _project_registry_or_none()
    requested = Path(options.project).expanduser() if options.project is not None else cwd
    if not requested.is_absolute():
        requested = cwd / requested
    requested = requested.resolve()
    if options.project is not None and not requested.is_dir():
        raise ValueError(f'project directory does not exist: {requested}')
    requested = _project_open_root(str(requested))
    if registry is None or (options.project is not None and not any(
        project.project_root.resolve() == requested for project in registry.projects()
    )):
        result = _start_project(requested, script_root=script_root, stdout=stdout, stderr=stderr)
        if result:
            return result
        registry = _project_registry_or_none()
        if registry is not None and not any(project.project_root.resolve() == requested for project in registry.projects()):
            raise RuntimeError('CCB startup did not register the requested project; inspect `muxary tui doctor`')
    if registry is None:
        raise RuntimeError('no running projects found after CCB startup; inspect `muxary tui doctor`')
    config_sessions = _ConfigUiSessions()
    state_dir = Path(os.environ.get('XDG_STATE_HOME') or Path.home() / '.local' / 'state') / 'muxary' / 'workbench'
    service = WorkbenchService(
        project_registry=registry, assets_dir=assets, state_dir=state_dir,
        config_opener=config_sessions.open, project_registry_provider=_project_registry_or_none,
        project_opener=lambda root: _start_project(root, script_root=script_root, stdout=stdout, stderr=stderr))
    try:
        server = build_workbench_server(service, host='127.0.0.1', port=options.port)
    except BaseException:
        service.close()
        config_sessions.close()
        raise
    try:
        port = server.server_address[1]
        url = f'http://127.0.0.1:{port}/#token={service.bootstrap_token}'
        print(f'Muxary: {url}', file=stdout, flush=True)
        print('Press Ctrl+C to close the Web workbench. Project agents continue running.', file=stdout, flush=True)
        if not options.no_open and not webbrowser.open(url):
            print('Browser did not open; use the local URL above.', file=stderr)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
    finally:
        server.server_close()
        config_sessions.close()
    return 0


def _project_registry_or_none():
    try:
        return _running_server_project_registry()
    except ValueError:
        return None


def _start_project(project_root: Path, *, script_root: Path, stdout: TextIO, stderr: TextIO) -> int:
    if not project_root.is_dir():
        raise ValueError(f'project directory does not exist: {project_root}')
    # Reuse CCB's config/bootstrap/lifecycle/approval gates. --safe prevents
    # a new Web entry point from silently enabling provider permission bypass.
    # File-backed output avoids communicate() waiting for a descendant that
    # inherited a PIPE after the launcher timeout. Only the direct launcher
    # is terminated by subprocess.run; CCB-owned agent processes are untouched.
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        try:
            completed = subprocess.run(
                [str(script_root / 'ccb'), '--safe'], cwd=project_root,
                env={**os.environ, 'CCB_NO_ATTACH': '1', 'CCB_SOURCE_RUNTIME_OK': '1'},
                stdout=output, stderr=errors, timeout=_PROJECT_START_TIMEOUT,
            )
        finally:
            for source, destination in ((output, stdout), (errors, stderr)):
                source.seek(0)
                data = source.read(_PROJECT_START_OUTPUT_LIMIT + 1)
                print(data[:_PROJECT_START_OUTPUT_LIMIT].decode('utf-8', errors='replace'), end='', file=destination)
                if len(data) > _PROJECT_START_OUTPUT_LIMIT:
                    print('\n[Muxary startup output truncated]', file=destination)
    return completed.returncode


class _ConfigUiSessions:
    """Own existing Config UI handles, not a second configuration editor."""

    def __init__(self) -> None:
        self._handles: dict[str, tuple[object, threading.Thread]] = {}
        self._lock = threading.Lock()

    def open(self, project) -> str:
        with self._lock:
            existing = self._handles.get(project.project_id)
            if existing is not None and existing[1].is_alive():
                return existing[0].url
            if existing is not None:
                existing[0].close()
            command = ParsedConfigUiCommand(project=str(project.project_root), port=0, no_open=True)
            context = CliContextBuilder().build(command, cwd=project.project_root)
            handle = prepare_config_ui(context, command)
            thread = threading.Thread(target=handle.serve_forever, name='muxary-config-ui', daemon=True)
            self._handles[project.project_id] = handle, thread
            thread.start()
            return handle.url

    def close(self) -> None:
        with self._lock:
            handles = list(self._handles.values())
            self._handles.clear()
        for handle, thread in handles:
            handle.close()
            thread.join(timeout=2)


__all__ = ['run_muxary']
