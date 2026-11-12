from __future__ import annotations

from pathlib import Path

from ccbd.socket_client import CcbdClientError
from cli.sidebar_click import SidebarClick, focus_sidebar_click, sidebar_tree_targets


SAMPLE_VIEW = {
    'namespace': {'epoch': 7},
    'windows': [
        {'name': 'main'},
        {'name': 'work'},
        {'name': 'review'},
    ],
    'agents': [
        {'name': 'agent1', 'window': 'main'},
        {'name': 'agent2', 'window': 'main'},
        {'name': 'agent3', 'window': 'work'},
        {'name': 'agent4', 'window': 'review'},
    ],
}


class FakeClient:
    calls: list[tuple[str, str, int | None]] = []

    def __init__(self, socket_path: Path) -> None:
        self.socket_path = socket_path

    def project_view(self, *, schema_version: int) -> dict:
        assert schema_version == 1
        return {'view': SAMPLE_VIEW}

    def project_focus_window(self, window: str, *, namespace_epoch: int | None = None) -> dict:
        self.calls.append(('window', window, namespace_epoch))
        return {}

    def project_focus_agent(self, agent: str, *, namespace_epoch: int | None = None) -> dict:
        self.calls.append(('agent', agent, namespace_epoch))
        return {}


class FastFakeClient:
    calls: list[tuple[str, dict]] = []

    def __init__(self, socket_path: Path) -> None:
        self.socket_path = socket_path

    def project_sidebar_click(
        self,
        *,
        mouse_y: int,
        pane_top: int,
        pane_height: int,
        schema_version: int,
    ) -> dict:
        self.calls.append(
            (
                'project_sidebar_click',
                {
                    'mouse_y': mouse_y,
                    'pane_top': pane_top,
                    'pane_height': pane_height,
                    'schema_version': schema_version,
                },
            )
        )
        return {'focused': True, 'target': 'window:work'}

    def project_view(self, *, schema_version: int) -> dict:
        raise AssertionError('fast sidebar click must not fetch project_view')


class UnknownOpFakeClient(FakeClient):
    def project_sidebar_click(self, **kwargs) -> dict:
        del kwargs
        raise CcbdClientError('unknown op: project_sidebar_click')


def test_sidebar_tree_targets_match_sidebar_render_order() -> None:
    assert sidebar_tree_targets(SAMPLE_VIEW) == [
        ('window', 'main'),
        ('agent', 'agent1'),
        ('agent', 'agent2'),
        ('window', 'work'),
        ('agent', 'agent3'),
        ('window', 'review'),
        ('agent', 'agent4'),
    ]


def test_sidebar_click_uses_single_daemon_endpoint_when_available() -> None:
    FastFakeClient.calls = []

    target = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=4, pane_top=1, pane_height=47),
        client_factory=FastFakeClient,
    )

    assert target == 'window:work'
    assert FastFakeClient.calls == [
        (
            'project_sidebar_click',
            {'mouse_y': 4, 'pane_top': 1, 'pane_height': 47, 'schema_version': 1},
        )
    ]


def test_sidebar_click_focuses_window_from_pane_relative_tmux_row() -> None:
    FakeClient.calls = []

    target = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=4, pane_top=1, pane_height=47),
        client_factory=FakeClient,
    )

    assert target == 'window:work'
    assert FakeClient.calls == [('window', 'work', 7)]


def test_sidebar_click_focuses_agent_from_second_agent_row() -> None:
    FakeClient.calls = []

    target = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=3, pane_top=1, pane_height=47),
        client_factory=FakeClient,
    )

    assert target == 'agent:agent2'
    assert FakeClient.calls == [('agent', 'agent2', 7)]


def test_sidebar_click_falls_back_when_daemon_lacks_click_endpoint() -> None:
    UnknownOpFakeClient.calls = []

    target = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=4, pane_top=1, pane_height=47),
        client_factory=UnknownOpFakeClient,
    )

    assert target == 'window:work'
    assert UnknownOpFakeClient.calls == [('window', 'work', 7)]


def test_sidebar_click_accepts_absolute_tmux_row_when_outside_pane_relative_range() -> None:
    FakeClient.calls = []

    target = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=52, pane_top=48, pane_height=47),
        client_factory=FakeClient,
    )

    assert target == 'window:work'
    assert FakeClient.calls == [('window', 'work', 7)]


def test_sidebar_click_ignores_title_border_and_empty_rows() -> None:
    FakeClient.calls = []

    title = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=0, pane_top=1, pane_height=47),
        client_factory=FakeClient,
    )
    empty = focus_sidebar_click(
        SidebarClick(socket_path=Path('/tmp/ccbd.sock'), mouse_y=20, pane_top=1, pane_height=47),
        client_factory=FakeClient,
    )

    assert title is None
    assert empty is None
    assert FakeClient.calls == []
