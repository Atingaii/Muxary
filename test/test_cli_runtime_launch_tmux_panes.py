from __future__ import annotations

import subprocess
from pathlib import Path

from cli.services.runtime_launch_runtime import tmux_panes


class FakeBackend:
    def __init__(self, *, socket_path: str | None = None, socket_name: str | None = None, returncode: int = 0) -> None:
        self.socket_path = socket_path
        self.socket_name = socket_name
        self.returncode = returncode
        self.calls: list[tuple[str, ...]] = []
        self.respawned: list[tuple[str, str, str | None]] = []

    def _tmux_run(self, argv, **kwargs):
        del kwargs
        self.calls.append(tuple(argv))
        stdout = '%7\n' if tuple(argv[:1]) == ('list-panes',) else ''
        return subprocess.CompletedProcess(args=argv, returncode=self.returncode, stdout=stdout, stderr='')

    def respawn_pane(self, pane_id: str, *, cmd: str, cwd: str | None = None, remain_on_exit: bool = True) -> None:
        del remain_on_exit
        self.respawned.append((pane_id, cmd, cwd))


def setup_function() -> None:
    tmux_panes._PREPARED_DETACHED_TMUX_SERVER_KEYS.clear()


def test_prepare_detached_tmux_server_reuses_same_socket_and_environment(monkeypatch) -> None:
    monkeypatch.setenv('DISPLAY', ':1')
    backend = FakeBackend(socket_path='/tmp/ccb.sock')

    tmux_panes.prepare_detached_tmux_server(backend)
    first_count = len(backend.calls)
    tmux_panes.prepare_detached_tmux_server(backend)

    assert first_count > 0
    assert len(backend.calls) == first_count
    assert ('start-server',) not in backend.calls


def test_prepare_detached_tmux_server_does_not_share_different_sockets(monkeypatch) -> None:
    monkeypatch.setenv('DISPLAY', ':1')
    first = FakeBackend(socket_path='/tmp/ccb-a.sock')
    second = FakeBackend(socket_path='/tmp/ccb-b.sock')

    tmux_panes.prepare_detached_tmux_server(first)
    tmux_panes.prepare_detached_tmux_server(second)

    assert first.calls
    assert second.calls


def test_prepare_detached_tmux_server_refreshes_when_environment_changes(monkeypatch) -> None:
    backend = FakeBackend(socket_path='/tmp/ccb.sock')
    monkeypatch.setenv('DISPLAY', ':1')
    tmux_panes.prepare_detached_tmux_server(backend)
    first_count = len(backend.calls)

    monkeypatch.setenv('DISPLAY', ':2')
    tmux_panes.prepare_detached_tmux_server(backend)

    assert len(backend.calls) > first_count


def test_prepare_detached_tmux_server_retries_after_failed_prepare(monkeypatch) -> None:
    monkeypatch.setenv('DISPLAY', ':1')
    backend = FakeBackend(socket_path='/tmp/ccb.sock', returncode=1)

    tmux_panes.prepare_detached_tmux_server(backend)
    first_count = len(backend.calls)
    tmux_panes.prepare_detached_tmux_server(backend)

    assert first_count > 0
    assert len(backend.calls) == first_count * 2


def test_create_detached_tmux_pane_creates_session_before_server_policy(tmp_path: Path) -> None:
    backend = FakeBackend(socket_path='/tmp/ccb.sock')

    pane_id = tmux_panes.create_detached_tmux_pane(
        backend,
        cmd='codex',
        cwd=tmp_path,
        session_name='ccb-agent1',
    )

    assert pane_id == '%7'
    assert backend.calls[0][:1] == ('new-session',)
    assert ('start-server',) not in backend.calls
    policy_index = backend.calls.index(('set-option', '-g', 'destroy-unattached', 'off'))
    assert policy_index > 0
    assert backend.respawned == [('%7', 'codex', str(tmp_path))]
