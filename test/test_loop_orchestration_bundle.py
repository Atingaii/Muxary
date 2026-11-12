from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from cli.services.loop_orchestration_bundle import (
    ORCHESTRATION_BUNDLE_CANDIDATE_SCHEMA,
    build_single_node_candidate,
    bundle_digest,
    bundle_text,
    load_task_orchestration_bundle,
    normalize_bundle_candidate,
    task_input_digest,
)
from cli.services.loop_effective_capacity import (
    effective_capacity_digest,
    normalize_effective_capacity_snapshot,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _record(project_root: Path, *, task_id: str = 'task-bundle') -> dict[str, object]:
    task_root = project_root / 'docs' / 'plantree' / 'plans' / 'demo' / 'tasks' / task_id
    artifacts: dict[str, dict[str, object]] = {}
    for kind, filename, text in (
        ('task_packet', 'task_packet.md', 'Build the requested feature.\n'),
        (
            'execution_contract',
            'execution_contract.md',
            'allowed_change_paths:\n- src/core/\n- src/cli/\n- tests/\nverification: python -m pytest\n',
        ),
        ('orchestration_notes', 'orchestration_notes.md', 'route: direct_execution\n'),
    ):
        path = task_root / filename
        _write(path, text)
        artifacts[kind] = {
            'path': path.relative_to(project_root).as_posix(),
            'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        }
    return {
        'task_id': task_id,
        'task_revision': 1,
        'task_root': task_root.relative_to(project_root).as_posix(),
        'artifacts': artifacts,
    }


def _capacity_snapshot(
    *,
    max_workgroups: int = 4,
    max_parallel_workgroups: int | None = None,
    max_active_dynamic_agents: int = 8,
) -> dict[str, object]:
    max_parallel_workgroups = max_parallel_workgroups or max_workgroups
    return {
        'schema': 'ccb.loop.effective_capacity_snapshot.v1',
        'config_version': 2,
        'workflow_profile': 'v2_static_compatibility',
        'workflow_mode': 'route_only',
        'limits': {
            'max_workgroups': max_workgroups,
            'max_parallel_workgroups': max_parallel_workgroups,
            'max_active_dynamic_agents': max_active_dynamic_agents,
        },
        'policies': {
            'node_rework': {'max_rounds': 1},
            'workspace': {'mode': 'single_workgroup_compatibility'},
            'integration': {'mode': 'single_node_compatibility'},
            'release': {'default_lifetime': 'current_loop', 'policy': 'auto', 'idle_only': True},
            'naming': {'template': 'loop-{loop_id}-{profile}-{index}'},
            'execution_windows': {'policy': 'existing_loop_capacity'},
        },
        'resident_profiles': {},
        'dynamic_profiles': {
            'coder': {
                'role_id': 'agentroles.coder',
                'provider': 'codex',
                'model': None,
                'workspace_mode': 'git-worktree',
                'release_policy': 'current_loop',
                'max_instances': 4,
            },
            'code_reviewer': {
                'role_id': 'agentroles.code_reviewer',
                'provider': 'codex',
                'model': None,
                'workspace_mode': 'git-worktree',
                'release_policy': 'current_loop',
                'max_instances': 4,
            },
        },
        'profile_aliases': {},
    }


def _node(
    *,
    node_id: str,
    workgroup_id: str,
    allowed_paths: list[str],
    execution_contract_ref: str,
    depends_on: list[str] | None = None,
    integration_order: int,
) -> dict[str, object]:
    return {
        'node_id': node_id,
        'workgroup_id': workgroup_id,
        'worker_profile': 'coder',
        'reviewer_profile': 'code_reviewer',
        'depends_on': depends_on or [],
        'parallel_group': 'wave-1' if not depends_on else 'wave-2',
        'work_packet': f'Implement {node_id} and return verification evidence.',
        'allowed_paths': allowed_paths,
        'acceptance_refs': [execution_contract_ref],
        'verification_refs': [execution_contract_ref],
        'integration_order': integration_order,
    }


def _candidate(record: dict[str, object], nodes: list[dict[str, object]]) -> dict[str, object]:
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    return {
        'schema': ORCHESTRATION_BUNDLE_CANDIDATE_SCHEMA,
        'task_id': record['task_id'],
        'bundle_revision': 1,
        'selection': {
            'workgroup_count': len(nodes),
            'complexity': 'atomic' if len(nodes) == 1 else 'bounded',
            'cutability': 'none' if len(nodes) == 1 else 'high',
            'execution_shape': 'single_unit' if len(nodes) == 1 else 'parallel',
            'rationale': 'Use the smallest independently reviewable workgroup set.',
        },
        'nodes': nodes,
        'integration': {
            'verification_refs': [contract_ref],
            'project_root_verification_refs': [contract_ref],
        },
        'policy': {
            'max_node_rework_rounds': 1,
            'on_required_node_failure': 'partial_or_blocked',
            'on_structural_failure': 'replan_required',
        },
    }


def test_bundle_normalizes_two_disjoint_parallel_workgroups(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    candidate = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/cli/'],
                execution_contract_ref=contract_ref,
                integration_order=20,
            ),
        ],
    )

    bundle, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )

    assert bundle['schema'] == 'ccb.loop.orchestration_bundle.v1'
    assert bundle['task_revision'] == 1
    assert bundle['capacity_digest']
    assert bundle['selection']['workgroup_count'] == 2
    assert 'source' not in bundle
    assert [node['node_id'] for node in bundle['nodes']] == ['node-001', 'node-002']
    assert set(packets) == {
        f'{record["task_root"]}/orchestration/work-packets/node-001.md',
        f'{record["task_root"]}/orchestration/work-packets/node-002.md',
    }


@pytest.mark.parametrize('count', [1, 2, 3, 4])
def test_bundle_supports_one_to_four_workgroups_with_deterministic_order(
    tmp_path: Path,
    count: int,
) -> None:
    project_root = tmp_path / f'repo-{count}'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    scopes = ['src/core/', 'src/cli/', 'tests/core/', 'tests/cli/']
    nodes = [
        _node(
            node_id=f'node-{index:03d}',
            workgroup_id=f'wg-{index:03d}',
            allowed_paths=[scopes[index - 1]],
            execution_contract_ref=contract_ref,
            integration_order=index * 10,
        )
        for index in range(1, count + 1)
    ]

    ordered, _packets = normalize_bundle_candidate(
        _candidate(record, nodes),
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )
    reversed_order, _reversed_packets = normalize_bundle_candidate(
        _candidate(record, list(reversed(nodes))),
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )

    assert [node['node_id'] for node in ordered['nodes']] == [f'node-{index:03d}' for index in range(1, count + 1)]
    assert reversed_order == ordered
    assert bundle_digest(reversed_order) == bundle_digest(ordered)


def test_bundle_rejects_more_than_four_workgroups_and_missing_root_fields(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    oversized = _candidate(
        record,
        [
            _node(
                node_id=f'node-{index:03d}',
                workgroup_id=f'wg-{index:03d}',
                allowed_paths=[f'src/core/{index}/'],
                execution_contract_ref=contract_ref,
                integration_order=index * 10,
            )
            for index in range(1, 6)
        ],
    )
    with pytest.raises(ValueError, match='exceeds max_workgroups=4'):
        normalize_bundle_candidate(
            oversized,
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )

    missing_policy = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            )
        ],
    )
    missing_policy.pop('policy')
    with pytest.raises(ValueError, match='missing fields: policy'):
        normalize_bundle_candidate(
            missing_policy,
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )


@pytest.mark.parametrize(
    ('field', 'value'),
    [
        ('node_id', 'todo-cli-json-core-implementation'),
        ('workgroup_id', 'todo-cli-json-core-workgroup-too-long'),
    ],
)
def test_bundle_rejects_node_identity_not_safe_for_agent_names(
    tmp_path: Path,
    field: str,
    value: str,
) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    node = _node(
        node_id='node-001',
        workgroup_id='wg-001',
        allowed_paths=['src/core/'],
        execution_contract_ref=contract_ref,
        integration_order=10,
    )
    node[field] = value

    with pytest.raises(ValueError, match=fr'nodes\[0\]\.{field} is invalid: agent name must match'):
        normalize_bundle_candidate(
            _candidate(record, [node]),
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )


def test_bundle_rejects_parallel_scope_overlap(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    candidate = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/core/api.py'],
                execution_contract_ref=contract_ref,
                integration_order=20,
            ),
        ],
    )

    with pytest.raises(ValueError, match='overlapping allowed paths'):
        normalize_bundle_candidate(
            candidate,
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )


def test_bundle_accepts_overlapping_scope_when_dependency_orders_nodes(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    candidate = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/core/api.py'],
                execution_contract_ref=contract_ref,
                depends_on=['node-001'],
                integration_order=20,
            ),
        ],
    )

    bundle, _packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )

    assert bundle['nodes'][1]['depends_on'] == ['node-001']


def test_bundle_rejects_cycle_and_scope_outside_execution_contract(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    cycle = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['src/core/'],
                execution_contract_ref=contract_ref,
                depends_on=['node-002'],
                integration_order=10,
            ),
            _node(
                node_id='node-002',
                workgroup_id='wg-002',
                allowed_paths=['src/cli/'],
                execution_contract_ref=contract_ref,
                depends_on=['node-001'],
                integration_order=20,
            ),
        ],
    )
    with pytest.raises(ValueError, match='dependency cycle'):
        normalize_bundle_candidate(
            cycle,
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )

    outside = _candidate(
        record,
        [
            _node(
                node_id='node-001',
                workgroup_id='wg-001',
                allowed_paths=['README.md'],
                execution_contract_ref=contract_ref,
                integration_order=10,
            )
        ],
    )
    with pytest.raises(ValueError, match='exceed execution contract scope'):
        normalize_bundle_candidate(
            outside,
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )


def test_single_node_bundle_round_trips_and_detects_stale_task_digest(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    candidate = build_single_node_candidate(record, project_root=project_root)
    bundle, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )
    for relative, text in packets.items():
        _write(project_root / relative, text)
    bundle_path = project_root / record['task_root'] / 'orchestration_bundle.json'
    text = bundle_text(bundle)
    _write(bundle_path, text)
    record['artifacts']['orchestration_bundle'] = {
        'path': bundle_path.relative_to(project_root).as_posix(),
        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'bundle_digest': bundle_digest(bundle),
    }

    loaded, artifact = load_task_orchestration_bundle(
        project_root,
        record,
        capacity_snapshot=_capacity_snapshot(),
    )
    assert loaded == bundle
    assert artifact['bundle_digest'] == bundle_digest(bundle)

    record['artifacts']['execution_contract']['sha256'] = 'changed'
    with pytest.raises(ValueError, match='task_digest is stale'):
        load_task_orchestration_bundle(project_root, record, capacity_snapshot=_capacity_snapshot())


def test_bundle_loader_rejects_tampered_normalized_node_even_with_updated_file_digest(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    candidate = build_single_node_candidate(record, project_root=project_root)
    bundle, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )
    for relative, text in packets.items():
        _write(project_root / relative, text)
    bundle['nodes'][0]['worker_profile'] = 'untrusted_worker'
    bundle_path = project_root / record['task_root'] / 'orchestration_bundle.json'
    text = bundle_text(bundle)
    _write(bundle_path, text)
    record['artifacts']['orchestration_bundle'] = {
        'path': bundle_path.relative_to(project_root).as_posix(),
        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'bundle_digest': bundle_digest(bundle),
        'task_digest': bundle['task_digest'],
    }

    with pytest.raises(ValueError, match='worker_profile must be coder'):
        load_task_orchestration_bundle(project_root, record, capacity_snapshot=_capacity_snapshot())


def test_bundle_digest_excludes_provenance_and_capacity_drift_is_rejected(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    candidate = build_single_node_candidate(record, project_root=project_root)
    first, packets = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )
    second, _ = normalize_bundle_candidate(
        candidate,
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(),
    )
    assert first == second
    assert 'source' not in first
    assert bundle_digest(first) == bundle_digest(second)
    for relative, text in packets.items():
        _write(project_root / relative, text)
    bundle_path = project_root / record['task_root'] / 'orchestration_bundle.json'
    text = bundle_text(first)
    _write(bundle_path, text)
    record['artifacts']['orchestration_bundle'] = {
        'path': bundle_path.relative_to(project_root).as_posix(),
        'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'bundle_digest': bundle_digest(first),
        'task_digest': first['task_digest'],
        'task_revision': first['task_revision'],
        'capacity_digest': first['capacity_digest'],
    }

    with pytest.raises(ValueError, match='capacity_digest is stale'):
        load_task_orchestration_bundle(
            project_root,
            record,
            capacity_snapshot=_capacity_snapshot(max_workgroups=3),
        )


def test_bundle_selection_count_must_match_nodes(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    candidate = build_single_node_candidate(record, project_root=project_root)
    candidate['selection']['workgroup_count'] = 2

    with pytest.raises(ValueError, match='selection.workgroup_count must equal node count'):
        normalize_bundle_candidate(
            candidate,
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(),
        )


def test_effective_capacity_snapshot_digest_is_canonical_and_strict() -> None:
    first = _capacity_snapshot()
    first['profile_aliases'] = {'reviewer': 'code_reviewer', 'worker': 'coder'}
    second = dict(reversed(list(first.items())))
    second['profile_aliases'] = {'worker': 'coder', 'reviewer': 'code_reviewer'}

    assert normalize_effective_capacity_snapshot(first) == normalize_effective_capacity_snapshot(second)
    assert effective_capacity_digest(first) == effective_capacity_digest(second)

    invalid = dict(first)
    invalid['runtime_path'] = '/tmp/provider-state'
    with pytest.raises(ValueError, match='contains unknown fields: runtime_path'):
        normalize_effective_capacity_snapshot(invalid)


def test_bundle_capacity_uses_dependency_frontier_not_provider_parallel_labels(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    contract_ref = str(record['artifacts']['execution_contract']['path'])
    nodes = [
        _node(
            node_id='node-001',
            workgroup_id='wg-001',
            allowed_paths=['src/core/'],
            execution_contract_ref=contract_ref,
            integration_order=10,
        ),
        _node(
            node_id='node-002',
            workgroup_id='wg-002',
            allowed_paths=['src/cli/'],
            execution_contract_ref=contract_ref,
            integration_order=20,
        ),
    ]
    nodes[0]['parallel_group'] = 'provider-label-a'
    nodes[1]['parallel_group'] = 'provider-label-b'

    with pytest.raises(ValueError, match='dependency frontier requests 2'):
        normalize_bundle_candidate(
            _candidate(record, nodes),
            record=record,
            project_root=project_root,
            capacity_snapshot=_capacity_snapshot(max_parallel_workgroups=1),
        )

    nodes[1]['depends_on'] = ['node-001']
    bundle, _packets = normalize_bundle_candidate(
        _candidate(record, nodes),
        record=record,
        project_root=project_root,
        capacity_snapshot=_capacity_snapshot(max_parallel_workgroups=1),
    )
    assert [node['node_id'] for node in bundle['nodes']] == ['node-001', 'node-002']


def test_v2_single_node_compatibility_reuses_current_revision_and_advances_after_replan(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / 'repo'
    record = _record(project_root)
    current_digest = task_input_digest(record)
    record['artifacts']['orchestration_bundle'] = {
        'bundle_revision': 3,
        'task_revision': 1,
        'task_digest': current_digest,
    }

    replay = build_single_node_candidate(record, project_root=project_root)
    assert replay['bundle_revision'] == 3

    record['task_revision'] = 2
    record['artifacts']['task_packet']['sha256'] = 'replanned-task-packet-digest'
    replacement = build_single_node_candidate(record, project_root=project_root)
    assert replacement['bundle_revision'] == 4
