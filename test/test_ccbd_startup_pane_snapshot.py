from __future__ import annotations

from types import SimpleNamespace

import pytest

from ccbd.services.project_namespace_pane import ProjectNamespacePaneRecord
from ccbd.services.project_namespace_pane import snapshot_project_namespace_panes
from ccbd.services.project_namespace_runtime.materialize_topology import (
    _list_sidebar_geometry_records,
    existing_topology_agent_panes,
    existing_topology_cmd_pane,
    topology_active_panes,
    topology_recreate_reason,
)


def test_startup_pane_snapshot_serves_topology_and_binding_without_rescan() -> None:
    calls: list[list[str]] = []

    class Backend:
        def _tmux_run(self, args, **kwargs):
            del kwargs
            calls.append(list(args))
            return SimpleNamespace(
                returncode=0,
                stdout=(
                    '%1\tccb-demo\t@0\tmain\t0\tagent\tagent1\tmain\t\t\tproj-1\tccbd\t7'
                    '\tagent1\tagent1\tlabel-1\tborder-1\tactive-1\tsession-1\t120\t80\n'
                    '%2\tccb-demo\t@1\treview\t0\tagent\tagent2\treview\t\t\tproj-1\tccbd\t7'
                    '\tagent2\tagent2\tlabel-2\tborder-2\tactive-2\tsession-2\t120\t80\n'
                    '%3\tccb-demo\t@1\treview\t0\tsidebar\tsidebar:review\treview\treview\thelper-v1'
                    '\tproj-1\tccbd\t7\tSidebar\tccb\tlabel-3\tborder-3\tactive-3\t\t120\t20\n'
                ),
            )

        def list_panes_by_user_options(self, expected):
            raise AssertionError(f'unexpected topology rescan: {expected}')

    backend = Backend()
    records = snapshot_project_namespace_panes(backend)
    assert records is not None
    controller = SimpleNamespace(_project_id='proj-1')
    context = SimpleNamespace(
        backend=backend,
        current=SimpleNamespace(namespace_epoch=7, tmux_session_name='ccb-demo'),
        desired_workspace_window_name='main',
        desired_session_name='ccb-demo',
    )
    topology_plan = SimpleNamespace(
        sidebar_enabled=False,
        windows=(
            SimpleNamespace(name='main', agent_names=('agent1',)),
            SimpleNamespace(name='review', agent_names=('agent2',)),
        ),
    )

    agent_panes = existing_topology_agent_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    active_panes = topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    recreate_reason = topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    sidebar_geometry = _list_sidebar_geometry_records(
        object(),
        session_name='ccb-demo',
        project_id='proj-1',
        pane_records=records,
        namespace_epoch=7,
    )

    assert len(calls) == 1
    assert calls[0][:3] == ['list-panes', '-a', '-F']
    assert agent_panes == {'agent1': '%1', 'agent2': '%2'}
    assert active_panes == ('%1', '%2')
    assert recreate_reason is None
    assert sidebar_geometry == [
        {
            'pane_id': '%3',
            'window_width': '120',
            'pane_width': '20',
            'sidebar_instance': 'review',
        }
    ]
    assert records['%2'].window_id == '@1'
    assert records['%2'].ccb_window == 'review'
    assert records['%2'].namespace_epoch == 7
    assert records['%2'].pane_title == 'agent2'
    assert records['%2'].label_style == 'label-2'
    assert records['%2'].ccb_session_id == 'session-2'
    assert records['%2'].window_width == 120
    assert records['%2'].pane_width == 80
    assert records['%3'].sidebar_helper_id == 'helper-v1'


def _topology_record(pane_id: str, **overrides) -> ProjectNamespacePaneRecord:
    values = {
        'pane_id': pane_id,
        'session_name': 'ccb-demo',
        'window_name': 'main',
        'role': 'agent',
        'slot_key': 'agent1',
        'ccb_window': 'main',
        'project_id': 'proj-1',
        'managed_by': 'ccbd',
        'namespace_epoch': 7,
        'alive': True,
    }
    values.update(overrides)
    return ProjectNamespacePaneRecord(**values)


def _topology_matrix_context():
    return (
        SimpleNamespace(_project_id='proj-1'),
        SimpleNamespace(
            backend=object(),
            current=SimpleNamespace(
                namespace_epoch=7,
                tmux_session_name='ccb-demo',
                workspace_window_name='main',
            ),
            desired_workspace_window_name='main',
            desired_session_name='ccb-demo',
        ),
        SimpleNamespace(
            sidebar_enabled=False,
            windows=(SimpleNamespace(name='main', agent_names=('agent1',), tool_names=()),),
        ),
    )


@pytest.mark.parametrize(
    ('noise', 'include_current', 'expected_reason'),
    (
        (None, True, None),
        (_topology_record('%sibling', session_name='ccb-sibling'), True, None),
        (_topology_record('%sibling-only', session_name='ccb-sibling'), False, 'topology_agent_panes_changed'),
        (_topology_record('%stale', namespace_epoch=6), False, 'topology_agent_panes_changed'),
        (_topology_record('%dead', alive=False), False, None),
        (_topology_record('%foreign', project_id='proj-foreign'), False, 'topology_agent_panes_changed'),
        (_topology_record('%missing-session', session_name=None), False, 'topology_agent_panes_changed'),
        (_topology_record('%missing-epoch', namespace_epoch=None), False, 'topology_agent_panes_changed'),
    ),
    ids=(
        'valid-current',
        'duplicate-in-sibling-session',
        'sibling-only',
        'wrong-epoch',
        'dead',
        'foreign-project',
        'missing-session-fails-closed',
        'missing-epoch-fails-closed',
    ),
)
def test_authoritative_topology_agent_matrix(noise, include_current: bool, expected_reason: str | None) -> None:
    controller, context, topology_plan = _topology_matrix_context()
    records = {'%cmd': _topology_record('%cmd', role='cmd', slot_key='cmd')}
    if include_current:
        records['%current'] = _topology_record('%current')
    if noise is not None:
        records[noise.pane_id] = noise

    assigned = existing_topology_agent_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    active = topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )
    reason = topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    )

    assert assigned == ({'agent1': '%current'} if include_current else {})
    assert active == (('%current',) if include_current else ())
    assert reason == expected_reason


def test_dead_owned_agent_pane_is_structural_but_not_active() -> None:
    controller, context, topology_plan = _topology_matrix_context()
    records = {
        '%dead': _topology_record('%dead', alive=False),
    }

    assert existing_topology_agent_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
        include_dead=True,
    ) == {'agent1': '%dead'}
    assert existing_topology_agent_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) == {}
    assert topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) == ()
    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) is None


def test_dead_owned_agent_keeps_a_single_pane_logical_window_structurally_present() -> None:
    controller = SimpleNamespace(_project_id='proj-1')
    context = SimpleNamespace(
        backend=object(),
        current=SimpleNamespace(
            namespace_epoch=7,
            tmux_session_name='ccb-demo',
            workspace_window_name='main',
        ),
        desired_workspace_window_name='main',
        desired_session_name='ccb-demo',
    )
    topology_plan = SimpleNamespace(
        sidebar_enabled=False,
        windows=(
            SimpleNamespace(name='main', agent_names=('agent1',), tool_names=()),
            SimpleNamespace(name='review', agent_names=('agent2',), tool_names=()),
        ),
    )
    records = {
        '%agent1': _topology_record('%agent1'),
        '%agent2': _topology_record(
            '%agent2',
            slot_key='agent2',
            window_name='review',
            ccb_window='review',
            alive=False,
        ),
    }

    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) is None


def test_authoritative_topology_sidebar_and_tool_duplicates_do_not_force_recreate() -> None:
    controller, context, _ = _topology_matrix_context()
    topology_plan = SimpleNamespace(
        sidebar_enabled=True,
        windows=(
            SimpleNamespace(
                name='main',
                agent_names=('agent1',),
                tool_names=('terminal',),
            ),
        ),
    )
    records = {
        '%cmd': _topology_record('%cmd', role='cmd', slot_key='cmd'),
        '%agent': _topology_record('%agent'),
        '%sidebar': _topology_record(
            '%sidebar',
            role='sidebar',
            slot_key='sidebar:main',
            sidebar_instance='main',
        ),
        '%sidebar-sibling': _topology_record(
            '%sidebar-sibling',
            session_name='ccb-sibling',
            role='sidebar',
            slot_key='sidebar:main',
            sidebar_instance='main',
        ),
        '%tool': _topology_record('%tool', role='tool', slot_key='tool:terminal'),
        '%tool-stale': _topology_record(
            '%tool-stale',
            role='tool',
            slot_key='tool:terminal',
            namespace_epoch=6,
        ),
    }

    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) is None
    assert topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) == ('%sidebar', '%agent', '%tool')

    without_sidebar = {key: value for key, value in records.items() if key != '%sidebar'}
    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=without_sidebar,
    ) == 'topology_sidebar_panes_changed'

    without_tool = {key: value for key, value in records.items() if key != '%tool'}
    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=without_tool,
    ) == 'topology_tool_panes_changed'


def test_topology_active_panes_protects_only_unique_expected_current_slots() -> None:
    controller, context, _ = _topology_matrix_context()
    topology_plan = SimpleNamespace(
        sidebar_enabled=True,
        windows=(
            SimpleNamespace(
                name='main',
                user_layout='cmd; agent1',
                agent_names=('agent1',),
                tool_names=('terminal',),
            ),
        ),
    )
    records = {
        '%sidebar': _topology_record(
            '%sidebar',
            role='sidebar',
            slot_key='sidebar:main',
            sidebar_instance='main',
        ),
        '%cmd': _topology_record('%cmd', role='cmd', slot_key='cmd'),
        '%agent': _topology_record('%agent'),
        '%tool': _topology_record('%tool', role='tool', slot_key='tool:terminal'),
        '%removed-sidebar': _topology_record(
            '%removed-sidebar',
            role='sidebar',
            slot_key='sidebar:removed',
            sidebar_instance='main',
        ),
        '%removed-cmd': _topology_record(
            '%removed-cmd',
            role='cmd',
            slot_key='not-cmd',
        ),
        '%removed-agent': _topology_record(
            '%removed-agent',
            slot_key='removed-agent',
        ),
        '%removed-tool': _topology_record(
            '%removed-tool',
            role='tool',
            slot_key='tool:removed',
        ),
    }

    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) is None
    assert topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) == ('%sidebar', '%cmd', '%agent', '%tool')


def test_topology_active_panes_fallback_uses_one_bounded_candidate_listing() -> None:
    controller, context, topology_plan = _topology_matrix_context()
    list_calls: list[dict[str, str]] = []
    describe_calls: list[str] = []

    class Backend:
        def list_panes_by_user_options(self, expected):
            list_calls.append(dict(expected))
            return ('%agent', '%removed-agent')

        def describe_pane(self, pane_id, *, user_options):
            del user_options
            describe_calls.append(pane_id)
            return {
                'pane_id': pane_id,
                'session_name': 'ccb-demo',
                'window_name': 'main',
                'pane_dead': '0',
                '@ccb_role': 'agent',
                '@ccb_slot': 'agent1' if pane_id == '%agent' else 'removed-agent',
                '@ccb_window': 'main',
                '@ccb_project_id': 'proj-1',
                '@ccb_managed_by': 'ccbd',
                '@ccb_namespace_epoch': '7',
            }

    context.backend = Backend()

    assert topology_active_panes(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=None,
    ) == ('%agent',)
    assert list_calls == [
        {
            '@ccb_project_id': 'proj-1',
            '@ccb_managed_by': 'ccbd',
            '@ccb_namespace_epoch': '7',
        }
    ]
    assert describe_calls == ['%agent', '%removed-agent']


def test_authoritative_topology_cmd_is_unique_and_fail_closed() -> None:
    controller, context, _ = _topology_matrix_context()
    topology_plan = SimpleNamespace(
        sidebar_enabled=False,
        windows=(
            SimpleNamespace(
                name='main',
                user_layout='cmd; agent1',
                agent_names=('agent1',),
                tool_names=(),
            ),
        ),
    )
    records = {
        '%cmd': _topology_record('%cmd', role='cmd', slot_key='cmd'),
        '%agent': _topology_record('%agent'),
        '%sibling-cmd': _topology_record(
            '%sibling-cmd',
            session_name='ccb-sibling',
            role='cmd',
            slot_key='cmd',
        ),
    }

    assert existing_topology_cmd_pane(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) == '%cmd'
    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=records,
    ) is None

    without_cmd = {key: value for key, value in records.items() if key != '%cmd'}
    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=without_cmd,
    ) == 'topology_cmd_panes_changed'

    duplicate_cmd = dict(records)
    duplicate_cmd['%duplicate-cmd'] = _topology_record(
        '%duplicate-cmd',
        role='cmd',
        slot_key='cmd',
    )
    assert existing_topology_cmd_pane(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=duplicate_cmd,
    ) is None
    assert topology_recreate_reason(
        controller,
        context,
        topology_plan=topology_plan,
        pane_records=duplicate_cmd,
    ) == 'topology_cmd_panes_changed'
