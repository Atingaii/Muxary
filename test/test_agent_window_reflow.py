from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

from ccbd.services.project_namespace_runtime.agent_window_reflow import reflow_agent_window_fixed


@dataclass
class _Window:
    name: str
    agent_names: tuple[str, ...]
    user_layout: str = ''
    sidebar: object | None = None


@dataclass
class _Topology:
    windows: tuple[_Window, ...]


@dataclass
class _FakeBackend:
    tmux_calls: list[tuple[str, ...]] = field(default_factory=list)
    pane_rows: tuple[str, ...] = ()

    def _tmux_run(self, args: list[str], *, check=False, capture=False, timeout=None):
        del check, capture, timeout
        self.tmux_calls.append(tuple(args))
        if args[:2] == ['list-panes', '-t']:
            rows = self.pane_rows or (
                '%1\t0\t0\t0\t24\t29\tsidebar\tsidebar:main\t\tmain',
                '%2\t1\t25\t0\t95\t29\tagent\tmain\tmain\t',
                '%3\t2\t72\t0\t48\t9\tagent\thelper1\tmain\t',
                '%4\t3\t25\t10\t47\t9\tagent\thelper2\tmain\t',
                '%5\t4\t72\t10\t48\t9\tagent\thelper3\tmain\t',
                '%6\t5\t25\t20\t47\t9\tagent\thelper4\tmain\t',
                '%7\t6\t72\t20\t48\t9\tagent\thelper5\tmain\t',
            )
            return SimpleNamespace(
                returncode=0,
                stdout='\n'.join(rows),
                stderr='',
            )
        if args[:2] == ['select-layout', '-t']:
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        if args[:1] == ['swap-pane']:
            return SimpleNamespace(returncode=0, stdout='', stderr='')
        raise AssertionError(f'unexpected tmux command: {args}')


def test_reflow_agent_window_fixed_builds_column_layout_and_swaps_visual_order() -> None:
    backend = _FakeBackend()
    topology = _Topology(windows=(_Window('main', ('main', 'helper1', 'helper2', 'helper3', 'helper4', 'helper5')),))

    applied, error = reflow_agent_window_fixed(
        backend,
        session_name='ccb-test',
        window_target='ccb-test:main',
        topology_plan=topology,
        window_name='main',
        timeout_s=0.0,
    )

    assert applied is True
    assert error is None
    select_calls = [call for call in backend.tmux_calls if call[:2] == ('select-layout', '-t')]
    assert len(select_calls) == 1
    layout = select_calls[0][3]
    assert layout.endswith(
        '120x29,0,0{24x29,0,0,0,95x29,25,0{47x29,25,0[47x9,25,0,1,47x9,25,10,2,47x9,25,20,3],47x29,73,0[47x9,73,0,4,47x9,73,10,5,47x9,73,20,6]}}'
    )
    swap_calls = [call for call in backend.tmux_calls if call[:1] == ('swap-pane',)]
    assert swap_calls == [
        ('swap-pane', '-s', '%3', '-t', '%4'),
        ('swap-pane', '-s', '%3', '-t', '%6'),
        ('swap-pane', '-s', '%5', '-t', '%3'),
    ]


def test_reflow_agent_window_fixed_skips_unmanaged_extra_panes() -> None:
    backend = _FakeBackend()
    topology = _Topology(windows=(_Window('main', ('main', 'helper1', 'helper2', 'helper3', 'helper4')),))

    applied, error = reflow_agent_window_fixed(
        backend,
        session_name='ccb-test',
        window_target='ccb-test:main',
        topology_plan=topology,
        window_name='main',
        timeout_s=0.0,
    )

    assert applied is False
    assert error is None
    assert not any(call[:2] == ('select-layout', '-t') for call in backend.tmux_calls)


def test_reflow_agent_window_fixed_preserves_target_vertical_topology_after_removal() -> None:
    backend = _FakeBackend(
        pane_rows=(
            '%1\t0\t0\t0\t24\t29\tsidebar\tsidebar:main\t\tmain',
            '%2\t1\t25\t0\t95\t14\tagent\thelper1\tmain\t',
            '%3\t2\t25\t15\t95\t14\tagent\thelper2\tmain\t',
        )
    )
    topology = _Topology(
        windows=(
            _Window(
                'main',
                ('helper1', 'helper2'),
                user_layout='helper1:claude, helper2:gemini',
                sidebar=SimpleNamespace(position='left'),
            ),
        )
    )

    applied, error = reflow_agent_window_fixed(
        backend,
        session_name='ccb-test',
        window_target='ccb-test:main',
        topology_plan=topology,
        window_name='main',
        timeout_s=0.0,
        prefer_topology_layout=True,
    )

    assert applied is True
    assert error is None
    select_calls = [call for call in backend.tmux_calls if call[:2] == ('select-layout', '-t')]
    assert len(select_calls) == 1
    assert select_calls[0][3].endswith(
        '120x29,0,0{24x29,0,0,0,95x29,25,0[95x14,25,0,1,95x14,25,15,2]}'
    )
    assert not any(call[:1] == ('swap-pane',) for call in backend.tmux_calls)


def test_reflow_agent_window_fixed_keeps_dynamic_fixed_columns_by_default() -> None:
    backend = _FakeBackend(
        pane_rows=(
            '%1\t0\t0\t0\t24\t29\tsidebar\tsidebar:main\t\tmain',
            '%2\t1\t25\t0\t47\t29\tagent\thelper1\tmain\t',
            '%3\t2\t73\t0\t47\t29\tagent\thelper2\tmain\t',
        )
    )
    topology = _Topology(
        windows=(
            _Window(
                'main',
                ('helper1', 'helper2'),
                user_layout='helper1:claude, helper2:gemini',
                sidebar=SimpleNamespace(position='left'),
            ),
        )
    )

    applied, error = reflow_agent_window_fixed(
        backend,
        session_name='ccb-test',
        window_target='ccb-test:main',
        topology_plan=topology,
        window_name='main',
        timeout_s=0.0,
    )

    assert applied is True
    assert error is None
    select_calls = [call for call in backend.tmux_calls if call[:2] == ('select-layout', '-t')]
    assert len(select_calls) == 1
    assert select_calls[0][3].endswith(
        '120x29,0,0{24x29,0,0,0,95x29,25,0{47x29,25,0,1,47x29,73,0,2}}'
    )


def test_reflow_agent_window_fixed_honors_percent_with_right_sidebar() -> None:
    backend = _FakeBackend(
        pane_rows=(
            '%2\t0\t0\t0\t38\t29\tagent\thelper1\tmain\t',
            '%3\t1\t39\t0\t56\t29\tagent\thelper2\tmain\t',
            '%1\t2\t96\t0\t24\t29\tsidebar\tsidebar:main\t\tmain',
        )
    )
    topology = _Topology(
        windows=(
            _Window(
                'main',
                ('helper1', 'helper2'),
                user_layout='helper1:claude@40; helper2:grok',
                sidebar=SimpleNamespace(position='right'),
            ),
        )
    )

    applied, error = reflow_agent_window_fixed(
        backend,
        session_name='ccb-test',
        window_target='ccb-test:main',
        topology_plan=topology,
        window_name='main',
        timeout_s=0.0,
        prefer_topology_layout=True,
    )

    assert applied is True
    assert error is None
    select_calls = [call for call in backend.tmux_calls if call[:2] == ('select-layout', '-t')]
    assert len(select_calls) == 1
    assert select_calls[0][3].endswith(
        '120x29,0,0{95x29,0,0{38x29,0,0,0,56x29,39,0,1},24x29,96,0,2}'
    )
    assert not any(call[:1] == ('swap-pane',) for call in backend.tmux_calls)
