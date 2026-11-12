from __future__ import annotations

from io import StringIO
import json
from pathlib import Path

import pytest

from agents.config_loader import load_project_config
from cli.phase2 import maybe_handle_phase2


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + '\n')


def _write_installed_role(store_root: Path, role_id: str, *, default_agent_name: str) -> None:
    _write(
        store_root / 'installed' / role_id / 'current' / 'role.toml',
        f'''id = "{role_id}"
version = "0.1.0"

[identity]
default_agent_name = "{default_agent_name}"
''',
    )


def _run_phase2(argv: list[str], *, cwd: Path) -> tuple[int, dict[str, object], str]:
    stdout = StringIO()
    stderr = StringIO()
    result = maybe_handle_phase2(argv, cwd=cwd, stdout=stdout, stderr=stderr)
    payload = json.loads(stdout.getvalue()) if stdout.getvalue().strip() else {}
    return result, payload, stderr.getvalue()


def _project_with_dispatch_roles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project_root = tmp_path / 'repo-topology-dispatch'
    role_store = tmp_path / 'roles'
    for role_id, default_agent_name in (
        ('agentroles.ccb_orchestrator', 'ccb_orchestrator'),
        ('agentroles.ccb_round_reviewer', 'ccb_round_reviewer'),
        ('agentroles.coder', 'coder'),
        ('agentroles.code_reviewer', 'code_reviewer'),
    ):
        _write_installed_role(role_store, role_id, default_agent_name=default_agent_name)
    monkeypatch.setenv('AGENT_ROLES_STORE', str(role_store))
    _write(
        project_root / '.ccb' / 'ccb.config',
        """version = 2
entry_window = "ccb-plan"

[windows]
ccb-plan = "bootstrap:codex"

[loop.capacity]
enabled = true
max_nodes = 4
default_lifetime = "current_loop"
name_template = "loop-{loop_id}-{profile}-{index}"
reuse = "prefer_idle"

[loop.role_profiles.ccb_orchestrator]
role = "agentroles.ccb_orchestrator"
provider = "codex"
workspace_mode = "inplace"
max_instances = 1

[loop.role_profiles.ccb_round_reviewer]
role = "agentroles.ccb_round_reviewer"
provider = "codex"
workspace_mode = "inplace"
max_instances = 1

[loop.role_profiles.coder]
role = "agentroles.coder"
provider = "codex"
workspace_mode = "git-worktree"
max_instances = 1

[loop.role_profiles.code_reviewer]
role = "agentroles.code_reviewer"
provider = "codex"
workspace_mode = "git-worktree"
max_instances = 1
""",
    )
    return project_root


def _project_with_legacy_alias_roles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project_root = tmp_path / 'repo-topology-legacy-alias'
    role_store = tmp_path / 'roles-legacy'
    _write_installed_role(role_store, 'agentroles.ccb_worker', default_agent_name='worker')
    monkeypatch.setenv('AGENT_ROLES_STORE', str(role_store))
    _write(
        project_root / '.ccb' / 'ccb.config',
        """version = 2
entry_window = "main"

[windows]
main = "bootstrap:codex"

[loop.capacity]
enabled = true
max_nodes = 1
default_lifetime = "current_loop"
name_template = "loop-{loop_id}-{profile}-{index}"

[loop.role_profiles.worker]
role = "agentroles.ccb_worker"
provider = "codex"
workspace_mode = "git-worktree"
max_instances = 1
""",
    )
    return project_root


def _dispatch_proposal() -> dict[str, object]:
    return {
        'dispatch_compatibility': 'legacy',
        'nodes': [
            {
                'id': 'control',
                'agents': [
                    {'id': 'wf-ccb-orchestrator', 'profile': 'ccb_orchestrator'},
                    {'id': 'wf-ccb-round-reviewer', 'profile': 'ccb_round_reviewer'},
                ],
            },
            {
                'id': 'work-1',
                'agents': [
                    {'id': 'wf-coder-1', 'profile': 'coder'},
                    {'id': 'wf-code-reviewer-1', 'profile': 'code_reviewer'},
                ],
            },
        ],
        'edges': [
            {
                'id': 'dispatch-coder',
                'from': 'wf-ccb-orchestrator',
                'to': 'wf-coder-1',
                'type': 'ask',
                'order': 10,
                'output_artifact': 'work-1.coder.md',
            },
            {
                'id': 'dispatch-reviewer',
                'from': 'wf-coder-1',
                'to': 'wf-code-reviewer-1',
                'type': 'ask_after',
                'after': ['dispatch-coder'],
                'order': 20,
                'input_artifact': 'work-1.coder.md',
                'output_artifact': 'work-1.review.md',
            },
            {
                'id': 'dispatch-round-review',
                'from': 'wf-code-reviewer-1',
                'to': 'wf-ccb-round-reviewer',
                'type': 'ask_after',
                'after': ['dispatch-reviewer'],
                'order': 30,
                'input_artifact': 'work-1.review.md',
                'output_artifact': 'round-review.md',
            },
        ],
        'gates': [{'id': 'round-complete', 'type': 'all_edges_complete'}],
        'artifacts': {'round': 'round-review.md'},
    }


def test_topology_records_dispatch_edge_order_and_fresh_observed_revision(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_dispatch_roles(tmp_path, monkeypatch)
    proposal_path = project_root / 'dispatch-topology.json'
    _write_json(proposal_path, _dispatch_proposal())

    result, proposed, stderr = _run_phase2(
        [
            'loop',
            'topology',
            'propose',
            '--loop-id',
            'dispatch1',
            '--from',
            str(proposal_path),
            '--proposal-id',
            'dispatch1',
            '--json',
        ],
        cwd=project_root,
    )
    assert result == 0, stderr
    normalized = json.loads(Path(proposed['proposal_path']).read_text(encoding='utf-8'))
    assert [edge['id'] for edge in normalized['edges']] == [
        'dispatch-coder',
        'dispatch-reviewer',
        'dispatch-round-review',
    ]
    assert normalized['gates'] == [{'id': 'round-complete', 'type': 'all_edges_complete'}]
    assert normalized['artifacts'] == {'round': 'round-review.md'}

    result, committed, stderr = _run_phase2(
        ['loop', 'topology', 'commit', '--loop-id', 'dispatch1', '--proposal', 'dispatch1', '--apply', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr

    desired = json.loads(Path(committed['desired_path']).read_text(encoding='utf-8'))
    observed = json.loads(Path(committed['reconcile']['observed_path']).read_text(encoding='utf-8'))
    assert [edge['id'] for edge in desired['edges']] == [
        'dispatch-coder',
        'dispatch-reviewer',
        'dispatch-round-review',
    ]
    assert desired['gates'] == [{'id': 'round-complete', 'type': 'all_edges_complete'}]
    assert desired['artifacts'] == {'round': 'round-review.md'}
    assert observed['desired_revision'] == desired['revision']
    assert [edge['id'] for edge in observed['edges']] == [edge['id'] for edge in desired['edges']]
    assert observed['retained_count'] == 0
    assert observed['drift']['mismatched_agents'] == []

    windows = {str(window.name): tuple(window.agent_names) for window in load_project_config(project_root).config.windows}
    assert windows['ccb-plan'] == ('bootstrap', 'wf-ccb-orchestrator', 'wf-ccb-round-reviewer')
    assert windows['ccb-exec'] == ('wf-coder-1', 'wf-code-reviewer-1')


def test_topology_status_exposes_stale_observed_revision_before_dispatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_dispatch_roles(tmp_path, monkeypatch)
    proposal_path = project_root / 'dispatch-topology.json'
    _write_json(proposal_path, _dispatch_proposal())
    for proposal_id, apply in (('rev1', True), ('rev2', False)):
        result, _proposed, stderr = _run_phase2(
            [
                'loop',
                'topology',
                'propose',
                '--loop-id',
                'dispatch1',
                '--from',
                str(proposal_path),
                '--proposal-id',
                proposal_id,
                '--json',
            ],
            cwd=project_root,
        )
        assert result == 0, stderr
        command = ['loop', 'topology', 'commit', '--loop-id', 'dispatch1', '--proposal', proposal_id, '--json']
        if apply:
            command.insert(-1, '--apply')
        result, _committed, stderr = _run_phase2(command, cwd=project_root)
        assert result == 0, stderr

    result, status, stderr = _run_phase2(
        ['loop', 'topology', 'status', '--loop-id', 'dispatch1', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    assert status['loop_topology_status'] == 'drift'
    assert status['desired']['revision'] == 2
    assert status['observed']['revision'] == 1


def test_topology_rejects_unknown_dispatch_edge_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_dispatch_roles(tmp_path, monkeypatch)
    proposal = _dispatch_proposal()
    proposal['edges'][0]['type'] = 'direct_tmux_mutation'  # type: ignore[index]
    proposal_path = project_root / 'bad-edge-type.json'
    _write_json(proposal_path, proposal)

    result, payload, stderr = _run_phase2(
        [
            'loop',
            'topology',
            'propose',
            '--loop-id',
            'dispatch1',
            '--from',
            str(proposal_path),
            '--proposal-id',
            'bad-edge-type',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 1
    assert payload == {}
    assert 'unsupported topology edge type' in stderr


def test_topology_rejects_legacy_worker_role_alias_even_with_explicit_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_legacy_alias_roles(tmp_path, monkeypatch)
    proposal_path = project_root / 'legacy-worker.json'
    _write_json(
        proposal_path,
        {
            'nodes': [
                {
                    'id': 'work-1',
                    'agents': [
                        {
                            'id': 'wf-worker-1',
                            'profile': 'worker',
                            'window_name': 'ccb-exec',
                            'desired_state': 'present',
                        }
                    ],
                }
            ],
            'edges': [],
        },
    )

    result, payload, stderr = _run_phase2(
        [
            'loop',
            'topology',
            'propose',
            '--loop-id',
            'dispatch1',
            '--from',
            str(proposal_path),
            '--proposal-id',
            'legacy-worker',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 1
    assert payload == {}
    assert 'legacy workflow profile alias' in stderr
