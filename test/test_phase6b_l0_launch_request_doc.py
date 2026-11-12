from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_REQUEST = (
    PROJECT_ROOT
    / 'docs'
    / 'plantree'
    / 'plans'
    / 'agentic-loop-workflow'
    / 'topics'
    / 'phase6b-l0-launch-request-20260704.md'
)


def _embedded_b7_normalizer() -> str:
    text = LAUNCH_REQUEST.read_text(encoding='utf-8')
    assert 'sed' not in text or '| bash' not in text
    assert 'timeout --preserve-status "${PHASE6B_L0_TIMEOUT_SECONDS}s" "$@"' in text
    assert '</dev/null >"$stdout_path" 2>"$stderr_path"' in text
    match = re.search(
        r'Exact normalization command shape for reviewer approval:.*?```bash\n(.*?)\n```',
        text,
        flags=re.S,
    )
    assert match is not None
    py_match = re.search(r"<<'PY'\n(.*?)\nPY", match.group(1), flags=re.S)
    assert py_match is not None
    code = py_match.group(1)
    compile(code, '<phase6b-l0-b7-normalizer>', 'exec')
    assert 'import hashlib' in code
    return code


def _proposed_b_only_command_block() -> str:
    text = LAUNCH_REQUEST.read_text(encoding='utf-8')
    match = re.search(
        r'## Proposed B-Only Repeat6 Command Sequence.*?```bash\n(.*?)\n```',
        text,
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def test_phase6b_l0_request_active_blocks_are_b_only() -> None:
    command_block = _proposed_b_only_command_block()
    normalizer = _embedded_b7_normalizer()

    for active_block in (command_block, normalizer):
        assert 'topology_a_' not in active_block
        assert 'ask_a_' not in active_block
        assert 'phase6b-l0-ccb-orchestrator' not in active_block
        assert 'p6bl0a' not in active_block
        assert 'topology_a_release_clean_check' not in active_block
        assert 'minimal_orchestrator' not in active_block

    for required_label in (
        'diagnose',
        'config_validate_initial',
        'start_project',
        'topology_b_propose',
        'topology_b_commit_apply',
        'ask_b_orchestrator_compact',
        'ps_b_after_ask',
        'topology_b_release',
        'ps_b_after_release',
        'config_validate_after_b',
    ):
        assert required_label in command_block
        assert required_label in normalizer

    assert 'p6bl0b-orchestrator' in command_block
    assert 'p6bl0b-orchestrator' in normalizer
    assert 'phase6-real-lab-l0-b-only-repeat6-20260704' in command_block
    assert 'phase6b_l0_b_only_repeat6_evidence_row.json' in normalizer
    assert 'phase6b_l0_b_only_repeat6_command_log.jsonl' in normalizer
    assert 'phase6-real-lab-l0-b-only-repeat5-20260704' not in command_block
    assert 'phase6-real-lab-l0-b-only-repeat5-20260704' not in normalizer
    assert 'phase6b_l0_b_only_repeat5_evidence_row.json' not in normalizer
    assert 'phase6b_l0_b_only_repeat5_command_log.jsonl' not in normalizer
    assert 'phase6b_l0_repeat4_evidence_row.json' not in normalizer
    assert 'drained_agents' in normalizer
    assert 'parked_after_release' in normalizer
    assert 'release_drained_clean' in normalizer


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in records),
        encoding='utf-8',
    )


def test_phase6b_l0_b7_normalizer_handles_b_only_release_incomplete(tmp_path: Path) -> None:
    code = _embedded_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l0-b-only-repeat6-20260704'
    project = root / 'l0-runtime-sanity'
    logs = root / 'logs'
    loops = project / '.ccb' / 'runtime' / 'loops'
    script_path = root / 'run_l0.sh'
    b7_path = tmp_path / 'phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md'
    logs.mkdir(parents=True)

    script_path.write_text('#!/usr/bin/env bash\n', encoding='utf-8')
    script_digest = hashlib.sha256(script_path.read_bytes()).hexdigest()
    (root / 'run_l0.sh.sha256').write_text(f'{script_digest}  {script_path}\n', encoding='utf-8')

    proposal = {
        'schema': 'ccb.loop.agent_mount_topology.v1',
        'nodes': [
            {
                'id': 'user-boundary',
                'agents': [
                    {
                        'id': 'p6bl0b-frontdesk',
                        'profile': 'ccb_frontdesk',
                        'desired_state': 'present',
                    },
                    {
                        'id': 'p6bl0b-detailer',
                        'profile': 'ccb_task_detailer',
                        'desired_state': 'present',
                    },
                ],
            },
            {
                'id': 'planning',
                'agents': [
                    {
                        'id': 'p6bl0b-planner',
                        'profile': 'ccb_planner',
                        'desired_state': 'present',
                    },
                    {
                        'id': 'p6bl0b-orchestrator',
                        'profile': 'ccb_orchestrator',
                        'desired_state': 'present',
                    },
                ],
            }
        ],
    }
    desired = {
        'schema': 'ccb.loop.agent_mount_topology.v1',
        'agents': [],
        'nodes': proposal['nodes'],
    }
    observed = {
        'schema': 'ccb.loop.agent_mount_topology.observed.v1',
        'agents': [
            {
                'id': 'p6bl0b-frontdesk',
                'profile': 'ccb_frontdesk',
                'desired_state': 'absent',
                'observed_state': 'released',
            },
            {
                'id': 'p6bl0b-detailer',
                'profile': 'ccb_task_detailer',
                'desired_state': 'absent',
                'observed_state': 'released',
            },
            {
                'id': 'p6bl0b-planner',
                'profile': 'ccb_planner',
                'desired_state': 'absent',
                'observed_state': 'released',
            },
            {
                'id': 'p6bl0b-orchestrator',
                'profile': 'ccb_orchestrator',
                'desired_state': 'absent',
                'observed_state': 'parked',
            }
        ],
    }
    _write_json(
        loops / 'p6bl0b' / 'topology_proposals' / 'p6bl0b-plan.json',
        proposal,
    )
    _write_json(loops / 'p6bl0b' / 'agent_mount_topology.desired.json', desired)
    _write_json(loops / 'p6bl0b' / 'agent_mount_topology.observed.json', observed)
    (loops / 'p6bl0b' / 'agent_mount_topology.events.jsonl').write_text('{}\n', encoding='utf-8')
    _write_jsonl(
        project / '.ccb' / 'agents' / 'p6bl0b-orchestrator' / 'jobs.jsonl',
        [
            {
                'job_id': 'job_fake',
                'record_type': 'job_record',
                'agent_name': 'p6bl0b-orchestrator',
                'target_name': 'p6bl0b-orchestrator',
                'request': {'to_agent': 'p6bl0b-orchestrator'},
                'status': 'running',
            }
        ],
    )
    assert not (project / '.ccb' / 'runtime' / 'asks.jsonl').exists()

    stdout_by_label = {
        'topology_b_release': {
            'loop_topology_status': 'release_incomplete',
            'release_blockers': {
                'p6bl0b-orchestrator': {
                    'profile': 'ccb_orchestrator',
                    'reason': 'active_after_release',
                }
            },
            'release_incomplete_agents': ['p6bl0b-orchestrator'],
            'release_incomplete_profile_counts': {'ccb_orchestrator': 1},
        },
        'ps_b_after_release': 'p6bl0b-orchestrator busy\n',
        'config_validate_after_b': 'p6bl0b-orchestrator\n',
    }
    labels = [
        'diagnose',
        'config_validate_initial',
        'start_project',
        'topology_b_propose',
        'topology_b_commit_apply',
        'ask_b_orchestrator_compact',
        'ps_b_after_ask',
        'topology_b_release',
        'ps_b_after_release',
        'config_validate_after_b',
    ]
    command_records = []
    for label in labels:
        stdout_path = logs / f'{label}.stdout'
        payload = stdout_by_label.get(label, '')
        if isinstance(payload, dict):
            stdout_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
        else:
            stdout_path.write_text(str(payload), encoding='utf-8')
        stderr_path = logs / f'{label}.stderr'
        stderr_path.write_text('', encoding='utf-8')
        command_records.append(
            {
                'label': label,
                'returncode': 0,
                'stdout_path': str(stdout_path),
                'stderr_path': str(stderr_path),
            }
        )
    _write_jsonl(root / 'phase6b_l0_b_only_repeat6_command_log.jsonl', command_records)

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(project), str(b7_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    row = json.loads((root / 'phase6b_l0_b_only_repeat6_evidence_row.json').read_text(encoding='utf-8'))
    assert row['classification'] == 'valid_non_success'
    assert row['ask_reachability'] is True
    assert row['ask_targets_logged'] == {
        'resident_planning_group': True,
    }
    assert row['cleanup_result'] == 'release_incomplete'
    assert 'release_gate' not in row
    assert row['ask_evidence_paths'] == [
        str(project / '.ccb' / 'agents' / 'p6bl0b-orchestrator' / 'jobs.jsonl')
    ]
    assert row['ask_evidence_errors'] == []
    assert row['missing_command_labels'] == []
    assert row['missing_artifacts'] == []
    assert row['input_errors'] == []
    assert row['test_design_failures'] == []
    assert row['topology_variants'] == ['resident_planning_group']
    assert row['variant_results']['resident_planning_group']['release_loop_topology_status'] == 'release_incomplete'
    assert 'minimal_orchestrator' not in row['variant_results']
    assert b7_path.is_file()


def test_phase6b_l0_b7_normalizer_accepts_drained_resident_release(tmp_path: Path) -> None:
    code = _embedded_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l0-b-only-repeat6-drained-20260704'
    project = root / 'l0-runtime-sanity'
    logs = root / 'logs'
    loops = project / '.ccb' / 'runtime' / 'loops'
    script_path = root / 'run_l0.sh'
    b7_path = tmp_path / 'phase6b-real-provider-l0-b-only-repeat6-drained-b7-20260704.md'
    logs.mkdir(parents=True)

    expected_agents = ['p6bl0b-frontdesk', 'p6bl0b-detailer', 'p6bl0b-planner', 'p6bl0b-orchestrator']
    script_path.write_text('#!/usr/bin/env bash\n', encoding='utf-8')
    script_digest = hashlib.sha256(script_path.read_bytes()).hexdigest()
    (root / 'run_l0.sh.sha256').write_text(f'{script_digest}  {script_path}\n', encoding='utf-8')
    proposal = {
        'schema': 'ccb.loop.agent_mount_topology.v1',
        'nodes': [
            {
                'id': 'user-boundary',
                'agents': [
                    {'id': 'p6bl0b-frontdesk', 'profile': 'ccb_frontdesk', 'desired_state': 'present'},
                    {'id': 'p6bl0b-detailer', 'profile': 'ccb_task_detailer', 'desired_state': 'present'},
                ],
            },
            {
                'id': 'planning',
                'agents': [
                    {'id': 'p6bl0b-planner', 'profile': 'ccb_planner', 'desired_state': 'present'},
                    {'id': 'p6bl0b-orchestrator', 'profile': 'ccb_orchestrator', 'desired_state': 'present'},
                ],
            },
        ],
    }
    _write_json(loops / 'p6bl0b' / 'topology_proposals' / 'p6bl0b-plan.json', proposal)
    _write_json(loops / 'p6bl0b' / 'agent_mount_topology.desired.json', {'schema': 'ccb.loop.agent_mount_topology.v1', 'nodes': []})
    _write_json(
        loops / 'p6bl0b' / 'agent_mount_topology.observed.json',
        {
            'schema': 'ccb.loop.agent_mount_topology.observed.v1',
            'agents': [],
            'drained_agents': sorted(expected_agents),
            'drained_count': len(expected_agents),
            'drain_reasons': {agent: 'parked_after_release' for agent in expected_agents},
        },
    )
    (loops / 'p6bl0b' / 'agent_mount_topology.events.jsonl').write_text('{}\n', encoding='utf-8')
    _write_jsonl(
        project / '.ccb' / 'agents' / 'p6bl0b-orchestrator' / 'jobs.jsonl',
        [
            {
                'job_id': 'job_fake',
                'record_type': 'job_record',
                'agent_name': 'p6bl0b-orchestrator',
                'target_name': 'p6bl0b-orchestrator',
                'request': {'to_agent': 'p6bl0b-orchestrator'},
                'status': 'running',
            }
        ],
    )

    stdout_by_label = {
        'topology_b_release': {
            'loop_topology_status': 'released',
            'drained_agents': sorted(expected_agents),
            'drained_count': len(expected_agents),
            'drain_reasons': {agent: 'parked_after_release' for agent in expected_agents},
        },
        'ps_b_after_release': '\n'.join(expected_agents) + '\n',
        'config_validate_after_b': '\n'.join(expected_agents) + '\n',
    }
    labels = [
        'diagnose',
        'config_validate_initial',
        'start_project',
        'topology_b_propose',
        'topology_b_commit_apply',
        'ask_b_orchestrator_compact',
        'ps_b_after_ask',
        'topology_b_release',
        'ps_b_after_release',
        'config_validate_after_b',
    ]
    command_records = []
    for label in labels:
        stdout_path = logs / f'{label}.stdout'
        payload = stdout_by_label.get(label, '')
        if isinstance(payload, dict):
            stdout_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')
        else:
            stdout_path.write_text(str(payload), encoding='utf-8')
        stderr_path = logs / f'{label}.stderr'
        stderr_path.write_text('', encoding='utf-8')
        command_records.append(
            {
                'label': label,
                'returncode': 0,
                'stdout_path': str(stdout_path),
                'stderr_path': str(stderr_path),
            }
        )
    _write_jsonl(root / 'phase6b_l0_b_only_repeat6_command_log.jsonl', command_records)

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(project), str(b7_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    row = json.loads((root / 'phase6b_l0_b_only_repeat6_evidence_row.json').read_text(encoding='utf-8'))
    assert row['classification'] == 'pass'
    assert row['cleanup_result'] == 'released'
    assert row['runtime_residue'] == {
        'dynamic_agents_absent': False,
        'config_dynamic_agents_absent': False,
        'observed_topology_residue_absent': True,
    }
    variant = row['variant_results']['resident_planning_group']
    assert variant['release_drained_agents'] == sorted(expected_agents)
    assert variant['release_drained_clean'] is True
    assert variant['desired_agent_ids'] == []
    assert variant['observed_agent_ids'] == []
