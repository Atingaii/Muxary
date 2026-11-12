from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from types import SimpleNamespace

import pytest

from cli.services.loop_effective_capacity import effective_capacity_digest
from cli.services.loop_capacity import loop_capacity
from cli.services.loop_workgroup_topology import (
    WORKGROUP_MOUNT_DEMAND_SCHEMA,
    compile_workgroup_mount_demand,
)
import cli.services.loop_topology as loop_topology_module


def _profile(
    role_id: str,
    *,
    max_instances: int,
    provider: str = 'codex',
    model: str | None = 'gpt-5.5',
    workspace_mode: str = 'inplace',
    release_policy: str = 'auto',
) -> dict[str, object]:
    return {
        'role_id': role_id,
        'provider': provider,
        'model': model,
        'workspace_mode': workspace_mode,
        'release_policy': release_policy,
        'max_instances': max_instances,
    }


def _snapshot(
    *,
    config_version: int = 3,
    max_workgroups: int = 4,
    max_parallel_workgroups: int | None = None,
    max_active_dynamic_agents: int = 11,
    coder_instances: int = 4,
    reviewer_instances: int = 4,
    name_template: str | None = None,
) -> dict[str, object]:
    max_parallel = max_workgroups if max_parallel_workgroups is None else max_parallel_workgroups
    v3 = config_version == 3
    return {
        'schema': 'ccb.loop.effective_capacity_snapshot.v1',
        'config_version': config_version,
        'workflow_profile': 'agentic_loop_v1' if v3 else 'v2_static_compatibility',
        'workflow_mode': 'agentic-loop' if v3 else 'route_only',
        'limits': {
            'max_workgroups': max_workgroups,
            'max_parallel_workgroups': max_parallel,
            'max_active_dynamic_agents': max_active_dynamic_agents,
        },
        'policies': {
            'node_rework': {'max_rounds': 1},
            'workspace': {'mode': 'git-worktree-required' if v3 else 'single_workgroup_compatibility'},
            'integration': {'mode': 'controller-owned' if v3 else 'single_node_compatibility'},
            'release': {
                'default_lifetime': 'current_activation' if v3 else 'current_round',
                'policy': 'auto',
                'idle_only': True,
            },
            'naming': {
                'template': name_template
                or ('loop-{loop_id}-{node_id}-{profile}' if v3 else 'loop-{loop_id}-{profile}-{index}')
            },
            'execution_windows': {'policy': 'auto:max_panes=6' if v3 else 'existing_loop_capacity'},
        },
        'resident_profiles': {
            'frontdesk': _profile('agentroles.ccb_frontdesk', max_instances=1, release_policy='resident'),
            'planner': _profile('agentroles.ccb_planner', max_instances=1, release_policy='resident'),
        },
        'dynamic_profiles': {
            'task_detailer': _profile('agentroles.ccb_task_detailer', max_instances=1),
            'orchestrator': _profile('agentroles.ccb_orchestrator', max_instances=1),
            'ccb_round_reviewer': _profile(
                'agentroles.ccb_round_reviewer',
                max_instances=1,
                provider='claude',
                model='claude-sonnet-4-5',
            ),
            'coder': _profile(
                'agentroles.coder',
                max_instances=coder_instances,
                workspace_mode='git-worktree',
            ),
            'code_reviewer': _profile(
                'agentroles.code_reviewer',
                max_instances=reviewer_instances,
                workspace_mode='git-worktree',
            ),
        },
        'profile_aliases': {'worker': 'coder'} if v3 else {},
    }


def _bundle(
    snapshot: dict[str, object],
    count: int,
    *,
    serial: bool = False,
) -> dict[str, object]:
    nodes = []
    for index in range(1, count + 1):
        node_id = f'node-{index:03d}'
        nodes.append(
            {
                'node_id': node_id,
                'workgroup_id': f'wg-{index:03d}',
                'worker_profile': 'coder',
                'reviewer_profile': 'code_reviewer',
                'depends_on': [f'node-{index - 1:03d}'] if serial and index > 1 else [],
                'parallel_group': f'wave-{index}' if serial else 'wave-1',
                'work_packet_ref': f'artifacts/{node_id}.md',
                'work_packet_sha256': f'sha256:{index:064x}',
                'allowed_paths': [f'src/part{index}/'],
                'acceptance_refs': ['artifacts/execution_contract.md'],
                'verification_refs': ['artifacts/execution_contract.md'],
                'integration_order': index * 10,
            }
        )
    return {
        'schema': 'ccb.loop.orchestration_bundle.v1',
        'task_id': 'task-topology',
        'task_revision': 1,
        'task_digest': 'sha256:' + ('a' * 64),
        'capacity_digest': effective_capacity_digest(snapshot),
        'bundle_revision': 1,
        'selection': {
            'workgroup_count': count,
            'complexity': 'bounded',
            'cutability': 'high' if count > 1 else 'none',
            'execution_shape': 'serial' if serial else ('single_unit' if count == 1 else 'parallel'),
            'rationale': 'test fixture',
        },
        'nodes': nodes,
        'integration': {'verification_refs': [], 'project_root_verification_refs': []},
        'policy': {
            'max_node_rework_rounds': 1,
            'on_required_node_failure': 'partial_or_blocked',
            'on_structural_failure': 'replan_required',
        },
    }


def _all_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            keys.add(str(key))
            keys.update(_all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_all_keys(item))
    return keys


@pytest.mark.parametrize('workgroup_count', (1, 2, 3, 4))
def test_compile_workgroup_mount_demand_places_one_to_four_adjacent_pairs(
    workgroup_count: int,
) -> None:
    snapshot = _snapshot()
    demand = compile_workgroup_mount_demand(
        _bundle(snapshot, workgroup_count),
        loop_id='r7',
        capacity_snapshot=snapshot,
        control_profiles=('orchestrator',),
    )

    assert demand['schema'] == WORKGROUP_MOUNT_DEMAND_SCHEMA
    assert demand['workgroup_count'] == workgroup_count
    assert demand['active_workgroup_count'] == workgroup_count
    assert demand['control_agent_count'] == 1
    assert demand['physical_agent_count'] == workgroup_count * 2 + 1
    assert demand['profile_counts'] == {
        'code_reviewer': workgroup_count,
        'coder': workgroup_count,
        'orchestrator': 1,
    }
    assert len(demand['bindings']) == workgroup_count
    topology = demand['mount_topology']
    assert topology['schema'] == 'ccb.loop.agent_mount_topology.v1'
    assert topology['loop_id'] == 'r7'
    assert topology['capacity_digest'] == effective_capacity_digest(snapshot)
    assert not {'edges', 'gates', 'artifacts', 'depends_on', 'work_packet_ref'} & _all_keys(topology)

    bindings = demand['bindings']
    for index, binding in enumerate(bindings, start=1):
        expected_window = 'ccb-exec' if index <= 3 else 'ccb-exec-2'
        assert binding['node_id'] == f'node-{index:03d}'
        assert binding['workspace_group'] == f'loop-r7-node-{index:03d}'
        assert binding['worker_agent'] == f'loop-r7-node-{index:03d}-coder'
        assert binding['reviewer_agent'] == f'loop-r7-node-{index:03d}-code_reviewer'
        assert binding['window_name'] == expected_window
        assert binding['pane_orders'] == {'coder': ((index - 1) * 2) % 6, 'code_reviewer': ((index - 1) * 2 + 1) % 6}

    windows = [window['name'] for window in topology['windows']]
    assert windows == (['ccb-plan', 'ccb-exec'] if workgroup_count <= 3 else ['ccb-plan', 'ccb-exec', 'ccb-exec-2'])


def test_compile_workgroup_mount_demand_places_activation_controls_without_residents() -> None:
    snapshot = _snapshot(max_active_dynamic_agents=5)
    demand = compile_workgroup_mount_demand(
        _bundle(snapshot, 1),
        loop_id='controls',
        capacity_snapshot=snapshot,
        control_profiles=('ccb_round_reviewer', 'task_detailer', 'orchestrator'),
    )

    topology = demand['mount_topology']
    agents = [agent for node in topology['nodes'] for agent in node['agents']]
    by_profile = {agent['profile']: agent for agent in agents}
    assert set(by_profile) == {
        'task_detailer',
        'orchestrator',
        'ccb_round_reviewer',
        'coder',
        'code_reviewer',
    }
    assert by_profile['task_detailer']['window_name'] == 'ccb-user'
    assert by_profile['orchestrator']['window_name'] == 'ccb-plan'
    assert by_profile['ccb_round_reviewer']['window_name'] == 'ccb-plan'
    assert by_profile['ccb_round_reviewer']['provider'] == 'claude'
    assert by_profile['ccb_round_reviewer']['model'] == 'claude-sonnet-4-5'
    assert {agent['lifecycle'] for agent in agents} == {'immaculate'}
    assert {agent['lifetime'] for agent in agents} == {'current_activation'}
    assert not {'frontdesk', 'planner'} & set(by_profile)


def test_compile_workgroup_mount_demand_supports_control_only_topology() -> None:
    snapshot = _snapshot()
    demand = compile_workgroup_mount_demand(
        _bundle(snapshot, 4),
        loop_id='control-only',
        capacity_snapshot=snapshot,
        active_node_ids=(),
        control_profiles=('ccb_round_reviewer',),
    )

    assert demand['active_workgroup_count'] == 0
    assert demand['bindings'] == []
    assert demand['control_agent_count'] == 1
    assert demand['physical_agent_count'] == 1
    assert demand['profile_counts'] == {'ccb_round_reviewer': 1}
    assert demand['mount_topology']['windows'] == [
        {
            'name': 'ccb-plan',
            'class': 'planning',
            'max_panes': 6,
            'layout_policy': 'append-or-create-window',
        }
    ]
    assert [node['id'] for node in demand['mount_topology']['nodes']] == ['control']


def test_compile_workgroup_mount_demand_rejects_empty_nodes_and_controls() -> None:
    snapshot = _snapshot()

    with pytest.raises(ValueError, match='requires at least one active node or control profile'):
        compile_workgroup_mount_demand(
            _bundle(snapshot, 1),
            loop_id='empty-all',
            capacity_snapshot=snapshot,
            active_node_ids=(),
            control_profiles=(),
        )


def test_compile_workgroup_mount_demand_enforces_parallel_and_physical_peak_without_serializing() -> None:
    serial_snapshot = _snapshot(
        max_workgroups=2,
        max_parallel_workgroups=1,
        max_active_dynamic_agents=3,
        coder_instances=2,
        reviewer_instances=2,
    )
    serial_bundle = _bundle(serial_snapshot, 2, serial=True)

    demand = compile_workgroup_mount_demand(
        serial_bundle,
        loop_id='serial',
        capacity_snapshot=serial_snapshot,
        active_node_ids=('node-001',),
        control_profiles=('orchestrator',),
    )
    assert demand['physical_agent_count'] == 3
    assert demand['active_workgroup_count'] == 1

    one_pair_snapshot = _snapshot(
        max_workgroups=4,
        max_parallel_workgroups=1,
        max_active_dynamic_agents=2,
        coder_instances=1,
        reviewer_instances=1,
    )
    one_pair_demand = compile_workgroup_mount_demand(
        _bundle(one_pair_snapshot, 4, serial=True),
        loop_id='serial-four',
        capacity_snapshot=one_pair_snapshot,
        active_node_ids=('node-004',),
    )
    assert one_pair_demand['workgroup_count'] == 4
    assert one_pair_demand['active_workgroup_count'] == 1
    assert one_pair_demand['profile_counts'] == {'code_reviewer': 1, 'coder': 1}
    assert one_pair_demand['bindings'][0]['node_id'] == 'node-004'
    assert one_pair_demand['bindings'][0]['window_name'] == 'ccb-exec'
    assert one_pair_demand['bindings'][0]['pane_orders'] == {'coder': 0, 'code_reviewer': 1}

    with pytest.raises(ValueError, match='max_parallel_workgroups=1'):
        compile_workgroup_mount_demand(
            serial_bundle,
            loop_id='serial',
            capacity_snapshot=serial_snapshot,
            active_node_ids=('node-001', 'node-002'),
            control_profiles=('orchestrator',),
        )

    parallel_snapshot = _snapshot(
        max_workgroups=2,
        max_parallel_workgroups=2,
        max_active_dynamic_agents=4,
        coder_instances=2,
        reviewer_instances=2,
    )
    with pytest.raises(ValueError, match='max_active_dynamic_agents=4.*requested 5'):
        compile_workgroup_mount_demand(
            _bundle(parallel_snapshot, 2),
            loop_id='parallel',
            capacity_snapshot=parallel_snapshot,
            control_profiles=('ccb_round_reviewer',),
        )


def test_compile_workgroup_mount_demand_rejects_limits_profile_shortage_and_bad_selection() -> None:
    too_small = _snapshot(max_workgroups=2, coder_instances=2, reviewer_instances=2)
    oversized_bundle = _bundle(too_small, 3)
    with pytest.raises(ValueError, match='max_workgroups=2'):
        compile_workgroup_mount_demand(
            oversized_bundle,
            loop_id='limits',
            capacity_snapshot=too_small,
        )

    shortage = _snapshot(max_workgroups=2, coder_instances=1, reviewer_instances=2)
    with pytest.raises(ValueError, match='profile coder.*max_instances=1.*requested 2'):
        compile_workgroup_mount_demand(
            _bundle(shortage, 2),
            loop_id='shortage',
            capacity_snapshot=shortage,
            active_node_ids=('node-001', 'node-002'),
        )

    snapshot = _snapshot()
    with pytest.raises(ValueError, match='unknown active node'):
        compile_workgroup_mount_demand(
            _bundle(snapshot, 1),
            loop_id='unknown',
            capacity_snapshot=snapshot,
            active_node_ids=('node-999',),
        )


def test_compile_workgroup_mount_demand_rejects_malformed_or_stale_capacity_digest() -> None:
    original = _snapshot(max_active_dynamic_agents=9)
    bundle = _bundle(original, 1)
    stale = _snapshot(max_active_dynamic_agents=8)
    with pytest.raises(ValueError, match='capacity_digest is stale'):
        compile_workgroup_mount_demand(
            bundle,
            loop_id='stale',
            capacity_snapshot=stale,
        )

    bundle['capacity_digest'] = 'not-a-digest'
    with pytest.raises(ValueError, match='capacity_digest must use sha256'):
        compile_workgroup_mount_demand(
            bundle,
            loop_id='malformed',
            capacity_snapshot=original,
        )


def test_compile_workgroup_mount_demand_uses_deterministic_attempt_names() -> None:
    snapshot = _snapshot()
    bundle = _bundle(snapshot, 1)
    first = compile_workgroup_mount_demand(
        bundle,
        loop_id='a',
        capacity_snapshot=snapshot,
        control_profiles=('orchestrator',),
    )
    second = compile_workgroup_mount_demand(
        bundle,
        loop_id='a',
        capacity_snapshot=snapshot,
        control_profiles=('orchestrator',),
        node_attempts={'node-001': 2},
        control_attempts={'orchestrator': 2},
    )

    assert first['bindings'][0]['worker_agent'] == 'loop-a-node-001-coder'
    assert second['bindings'][0]['worker_agent'] != first['bindings'][0]['worker_agent']
    assert len(second['bindings'][0]['worker_agent']) <= 32
    first_controls = first['control_bindings']
    second_controls = second['control_bindings']
    assert first_controls[0]['agent'] == 'loop-a-control-orchestrator'
    assert second_controls[0]['agent'] != first_controls[0]['agent']
    assert len(second_controls[0]['agent']) <= 32
    assert first == compile_workgroup_mount_demand(
        bundle,
        loop_id='a',
        capacity_snapshot=snapshot,
        control_profiles=('orchestrator',),
    )


def test_compile_workgroup_mount_demand_compacts_long_workspace_group_names_stably() -> None:
    snapshot = _snapshot()
    bundle = _bundle(snapshot, 2)
    loop_id = 'abcdefghijklmnopqrstuvwx123456'

    first = compile_workgroup_mount_demand(bundle, loop_id=loop_id, capacity_snapshot=snapshot)
    second = compile_workgroup_mount_demand(bundle, loop_id=loop_id, capacity_snapshot=snapshot)
    groups = [binding['workspace_group'] for binding in first['bindings']]

    assert first == second
    assert len(set(groups)) == 2
    assert all(len(group) <= 32 for group in groups)
    for binding, node in zip(first['bindings'], first['mount_topology']['nodes'], strict=True):
        assert {agent['workspace_group'] for agent in node['agents']} == {binding['workspace_group']}


def test_compile_workgroup_mount_demand_preserves_v2_one_group_compatibility(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _snapshot(
        config_version=2,
        max_workgroups=1,
        max_parallel_workgroups=1,
        max_active_dynamic_agents=2,
        coder_instances=1,
        reviewer_instances=1,
    )
    demand = compile_workgroup_mount_demand(
        _bundle(snapshot, 1),
        loop_id='v2',
        capacity_snapshot=snapshot,
    )

    assert demand['config_version'] == 2
    assert demand['workgroup_count'] == 1
    assert demand['bindings'] == [
        {
            'node_id': 'node-001',
            'workgroup_id': 'wg-001',
            'attempt': 1,
            'workspace_group': 'loop-v2-node-001',
            'worker_profile': 'coder',
            'reviewer_profile': 'code_reviewer',
            'worker_agent': 'loop-v2-coder-1',
            'reviewer_agent': 'loop-v2-code_reviewer-1',
            'window_name': 'ccb-exec',
            'pane_orders': {'coder': 0, 'code_reviewer': 1},
        }
    ]
    assert 'worker' not in demand['profile_counts']

    aliased_snapshot = _snapshot(
        config_version=2,
        max_workgroups=1,
        max_parallel_workgroups=1,
        max_active_dynamic_agents=2,
        coder_instances=1,
        reviewer_instances=1,
    )
    aliased_snapshot['dynamic_profiles']['worker'] = aliased_snapshot['dynamic_profiles'].pop('coder')
    aliased_snapshot['profile_aliases'] = {'coder': 'worker'}
    aliased_demand = compile_workgroup_mount_demand(
        _bundle(aliased_snapshot, 1),
        loop_id='v2alias',
        capacity_snapshot=aliased_snapshot,
    )
    assert aliased_demand['bindings'][0]['worker_profile'] == 'worker'
    assert aliased_demand['profile_counts'] == {'code_reviewer': 1, 'worker': 1}
    loaded = SimpleNamespace(
        config=SimpleNamespace(
            version=2,
            loop_capacity=SimpleNamespace(
                enabled=True,
                max_nodes=2,
                role_profiles={
                    'worker': SimpleNamespace(max_instances=1),
                    'code_reviewer': SimpleNamespace(max_instances=1),
                },
            ),
            agents={},
        ),
        source_kind='test',
        source_path=None,
    )
    context = SimpleNamespace(project=SimpleNamespace(project_root='/tmp/v2-alias-plan'))
    monkeypatch.setattr(loop_topology_module, 'load_project_config', lambda *_args, **_kwargs: loaded)
    monkeypatch.setattr(
        loop_topology_module,
        'compile_project_effective_capacity_snapshot',
        lambda _project_root: aliased_snapshot,
    )
    validation = loop_topology_module._validate_topology(
        context,
        aliased_demand['mount_topology'],
        loop_id='v2alias',
    )
    assert validation['profile_counts'] == {'code_reviewer': 1, 'worker': 1}


def test_compile_workgroup_mount_demand_rejects_worker_profile_outside_compatibility_boundary() -> None:
    snapshot = _snapshot()
    bundle = _bundle(snapshot, 1)
    bundle['nodes'][0]['worker_profile'] = 'worker'  # type: ignore[index]

    with pytest.raises(ValueError, match='worker_profile must be coder'):
        compile_workgroup_mount_demand(
            bundle,
            loop_id='aliases',
            capacity_snapshot=snapshot,
        )


def test_v3_mount_plan_validation_binds_capacity_digest_and_excludes_residents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot = _snapshot(max_workgroups=2, max_parallel_workgroups=2, max_active_dynamic_agents=5)
    demand = compile_workgroup_mount_demand(
        _bundle(snapshot, 2),
        loop_id='v3plan',
        capacity_snapshot=snapshot,
        control_profiles=('ccb_round_reviewer',),
    )
    loaded = SimpleNamespace(
        config=SimpleNamespace(version=3),
        source_kind='test',
        source_path=None,
    )
    context = SimpleNamespace(project=SimpleNamespace(project_root='/tmp/v3-plan'))
    monkeypatch.setattr(loop_topology_module, 'load_project_config', lambda *_args, **_kwargs: loaded)
    monkeypatch.setattr(
        loop_topology_module,
        'compile_project_effective_capacity_snapshot',
        lambda _project_root: snapshot,
    )

    validation = loop_topology_module._validate_topology(
        context,
        demand['mount_topology'],
        loop_id='v3plan',
    )

    assert validation['config_version'] == 3
    assert validation['capacity_digest'] == effective_capacity_digest(snapshot)
    assert validation['profile_counts'] == {'ccb_round_reviewer': 1, 'code_reviewer': 2, 'coder': 2}
    stale = dict(demand['mount_topology'], capacity_digest='sha256:' + ('0' * 64))
    with pytest.raises(ValueError, match='capacity_digest is stale'):
        loop_topology_module._validate_topology(context, stale, loop_id='v3plan')

    resident = dict(demand['mount_topology'])
    resident['nodes'] = list(resident['nodes']) + [
        {
            'id': 'resident',
            'agents': [
                {
                    'id': 'frontdesk',
                    'profile': 'frontdesk',
                    'window_name': 'ccb-user',
                    'desired_state': 'present',
                }
            ],
        }
    ]
    with pytest.raises(ValueError, match='frontdesk'):
        loop_topology_module._validate_topology(context, resident, loop_id='v3plan')

    wrong_owner = dict(demand['mount_topology'], owner={'kind': 'loop', 'loop_id': 'other'})
    with pytest.raises(ValueError, match='owner loop_id=other.*loop_id=v3plan'):
        loop_topology_module._validate_topology(context, wrong_owner, loop_id='v3plan')

    wrong_agent_loop = dict(demand['mount_topology'])
    wrong_agent_loop['nodes'] = [dict(node) for node in wrong_agent_loop['nodes']]
    wrong_agent_loop['nodes'][0]['agents'] = [dict(agent) for agent in wrong_agent_loop['nodes'][0]['agents']]
    wrong_agent_loop['nodes'][0]['agents'][0]['loop_id'] = 'other'
    with pytest.raises(ValueError, match='agent .* loop_id=other.*loop_id=v3plan'):
        loop_topology_module._validate_topology(context, wrong_agent_loop, loop_id='v3plan')

    out_of_range_pane = deepcopy(demand['mount_topology'])
    out_of_range_pane['nodes'][0]['agents'][0]['pane_order'] = 6
    with pytest.raises(ValueError, match='pane_order=6.*max_panes=6'):
        loop_topology_module._validate_topology(context, out_of_range_pane, loop_id='v3plan')


def test_v3_rejects_legacy_profile_count_capacity_ensure(monkeypatch: pytest.MonkeyPatch) -> None:
    loaded = SimpleNamespace(config=SimpleNamespace(version=3))
    monkeypatch.setattr('cli.services.loop_capacity.load_project_config', lambda *_args, **_kwargs: loaded)
    context = SimpleNamespace(project=SimpleNamespace(project_root='/tmp/v3-capacity'))
    command = SimpleNamespace(action='ensure', loop_id='v3', profile_counts=(('coder', 1),))

    with pytest.raises(RuntimeError, match='V2 physical-capacity compatibility only'):
        loop_capacity(context, command)
