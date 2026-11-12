from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from agents.config_loader import load_project_config
from ccbd.reload_plan import build_reload_dry_run_plan
from cli.models import ParsedAgentCommand
from cli.parser import CliParser
from cli.phase2 import maybe_handle_phase2


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _write_installed_role(store_root: Path, role_id: str, *, default_agent_name: str) -> None:
    _write(
        store_root / 'installed' / role_id / 'current' / 'role.toml',
        f'''id = "{role_id}"
version = "0.1.0"

[identity]
default_agent_name = "{default_agent_name}"
''',
    )


def _project_with_agent_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    project_root = tmp_path / 'repo-agent-lifecycle'
    role_store = tmp_path / 'roles'
    _write_installed_role(role_store, 'agentroles.general', default_agent_name='general')
    _write_installed_role(role_store, 'agentroles.code_reviewer', default_agent_name='code_reviewer')
    monkeypatch.setenv('AGENT_ROLES_STORE', str(role_store))
    _write(
        project_root / '.ccb' / 'ccb.config',
        """main:codex

[loop.capacity]
enabled = true
max_nodes = 2

[loop.role_profiles.code_reviewer]
role = "agentroles.code_reviewer"
provider = "codex"
thinking = "medium"
max_instances = 2
""",
    )
    return project_root


def _run_phase2(argv: list[str], *, cwd: Path) -> tuple[int, dict[str, object], str]:
    stdout = StringIO()
    stderr = StringIO()
    result = maybe_handle_phase2(argv, cwd=cwd, stdout=stdout, stderr=stderr)
    payload = json.loads(stdout.getvalue()) if stdout.getvalue().strip() else {}
    return result, payload, stderr.getvalue()


def _namespace(project_id: str):
    return SimpleNamespace(
        project_id=project_id,
        namespace_epoch=1,
        tmux_socket_path='/tmp/ccb-test-tmux.sock',
        tmux_session_name='ccb-test-session',
        workspace_window_name='main',
        workspace_window_id='@main',
        workspace_epoch=1,
        ui_attachable=True,
    )


def test_agent_parser_supports_add_and_remove_commands() -> None:
    parser = CliParser()

    assert parser.parse(
        [
            'agent',
            'add',
            'helper:codex',
            '--role',
            'agentroles.general',
            '--hidden',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='add',
        agent_name='helper',
        provider='codex',
        role='agentroles.general',
        visibility='hidden',
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'move',
            'helper',
            '--window',
            'review',
            '--reason',
            'operator layout',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='move',
        agent_name='helper',
        window_name='review',
        reason='operator layout',
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'move',
            '--agents',
            'helper1,helper2',
            '--window',
            'review',
            '--reason',
            'batch layout',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='move',
        agent_names=('helper1', 'helper2'),
        window_name='review',
        reason='batch layout',
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'move',
            '--agents',
            'planner2,broker1',
            '--window-class',
            'plan-orchestrate',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='move',
        agent_names=('planner2', 'broker1'),
        window_class='plan-orchestrate',
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'move',
            '--agents',
            'worker1,checker1',
            '--loop-id',
            'round1',
            '--node-id',
            'node1',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='move',
        agent_names=('worker1', 'checker1'),
        loop_id='round1',
        node_id='node1',
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'remove',
            'helper',
            '--policy',
            'kill',
            '--force',
            '--reason',
            'operator reset',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='remove',
        agent_name='helper',
        policy='kill',
        force=True,
        reason='operator reset',
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'remove',
            '--agents',
            'helper1,helper2',
            '--policy',
            'unload',
            '--idle-only',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='remove',
        agent_names=('helper1', 'helper2'),
        policy='unload',
        idle_only=True,
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'release',
            'reviewer',
            '--idle-only',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='release',
        agent_name='reviewer',
        policy='auto',
        idle_only=True,
        json_output=True,
    )
    assert parser.parse(
        [
            'agent',
            'release',
            '--agents',
            'worker1,checker1',
            '--idle-only',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='release',
        agent_names=('worker1', 'checker1'),
        policy='auto',
        idle_only=True,
        json_output=True,
    )
    assert parser.parse(['agent', 'park', 'planner2', '--json']) == ParsedAgentCommand(
        project=None,
        action='park',
        agent_name='planner2',
        json_output=True,
    )
    assert parser.parse(['agent', 'park', '--agents', 'planner2,broker1', '--json']) == ParsedAgentCommand(
        project=None,
        action='park',
        agent_names=('planner2', 'broker1'),
        json_output=True,
    )
    assert parser.parse(['agent', 'resume', 'planner2', '--hidden', '--json']) == ParsedAgentCommand(
        project=None,
        action='resume',
        agent_name='planner2',
        visibility='hidden',
        json_output=True,
    )
    assert parser.parse(['agent', 'resume', '--agents', 'planner2,broker1', '--visible', '--json']) == ParsedAgentCommand(
        project=None,
        action='resume',
        agent_names=('planner2', 'broker1'),
        visibility='visible',
        json_output=True,
    )


def test_agent_parser_supports_hot_load_placement_options() -> None:
    parser = CliParser()

    assert parser.parse(
        [
            'agent',
            'add',
            'worker1:codex',
            '--profile',
            'code_reviewer',
            '--window',
            'node-loop1-node1',
            '--window-class',
            'execution-node',
            '--loop-id',
            'loop1',
            '--node-id',
            'node1',
            '--hidden',
            '--json',
        ]
    ) == ParsedAgentCommand(
        project=None,
        action='add',
        agent_name='worker1',
        provider='codex',
        profile='code_reviewer',
        window_name='node-loop1-node1',
        window_class='execution-node',
        loop_id='loop1',
        node_id='node1',
        visibility='hidden',
        json_output=True,
    )


def test_agent_add_profile_writes_runtime_overlay_and_config_includes_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)

    result, payload, stderr = _run_phase2(
        ['agent', 'add', 'reviewer', '--profile', 'code_reviewer', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['agent_lifecycle_status'] == 'active'
    assert payload['agent'] == 'reviewer'
    assert payload['profile'] == 'code_reviewer'
    assert payload['role'] == 'agentroles.code_reviewer'
    assert payload['provider'] == 'codex'
    assert payload['lifecycle_state'] == 'hidden'
    assert payload['apply']['apply_status'] == 'deferred_until_start'
    state_path = Path(str(payload['state_path']))
    assert state_path.exists()

    loaded = load_project_config(project_root)
    assert 'reviewer' in loaded.config.agents
    assert 'reviewer' in loaded.config.default_agents
    assert loaded.config.agents['reviewer'].role == 'agentroles.code_reviewer'

    result, status, stderr = _run_phase2(['agent', 'status', '--json'], cwd=project_root)

    assert result == 0, stderr
    records = {record['agent']: record for record in status['agents']}
    assert records['main']['agent_kind'] == 'static'
    assert records['main']['ownership_class'] == 'static_configured'
    assert records['main']['dispatch_state'] == 'enabled'
    assert records['main']['failed_apply'] is False
    assert records['reviewer']['agent_kind'] == 'dynamic'
    assert records['reviewer']['ownership_class'] == 'dynamic_session'
    assert records['reviewer']['dispatch_state'] == 'enabled'
    assert records['reviewer']['apply_status'] == 'deferred_until_start'
    assert records['reviewer']['failed_apply'] is False
    assert records['reviewer']['pane_identity_source'] == 'missing'

    result, shown, stderr = _run_phase2(['agent', 'show', 'reviewer', '--json'], cwd=project_root)

    assert result == 0, stderr
    assert shown['agent_kind'] == 'dynamic'
    assert shown['ownership_class'] == 'dynamic_session'
    assert shown['dispatch_state'] == 'enabled'
    assert shown['apply_status'] == 'deferred_until_start'


def test_agent_add_to_existing_window_projects_add_agent_reload_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    current = load_project_config(project_root, include_loop_overlays=False).config

    result, payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['window_name'] == 'main'
    loaded = load_project_config(project_root).config
    assert loaded.windows_explicit is True
    assert [(window.name, window.agent_names, window.layout_spec) for window in loaded.windows] == [
        ('main', ('main', 'helper'), 'main:codex; helper:codex'),
    ]
    plan = build_reload_dry_run_plan(current, loaded, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'add_agent'
    assert plan['namespace_patch_plan']['status'] == 'planned'
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'create_agent_pane',
            'window': 'main',
            'agent': 'helper',
            'role': 'agent',
            'slot_key': 'helper',
            'managed_by': 'ccbd',
            'anchor_agent': 'main',
            'reason': 'new agent appended to existing managed window',
        }
    ]


def test_agent_remove_middle_dynamic_agent_preserves_remaining_order_and_uses_remove_agent_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for helper in ('helper1', 'helper2', 'helper3'):
        result, _payload, stderr = _run_phase2(
            [
                'agent',
                'add',
                f'{helper}:codex',
                '--role',
                'agentroles.general',
                '--window',
                'main',
                '--hidden',
                '--json',
            ],
            cwd=project_root,
        )
        assert result == 0, stderr
    before_remove = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in before_remove.windows] == [
        (
            'main',
            ('main', 'helper1', 'helper2', 'helper3'),
            'main:codex; helper1:codex; helper2:codex; helper3:codex',
        ),
    ]

    result, removed, stderr = _run_phase2(
        ['agent', 'remove', 'helper2', '--policy', 'unload', '--idle-only', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert removed['resolved_policy'] == 'unload'
    assert removed['lifecycle_state'] == 'unloaded'
    after_remove = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in after_remove.windows] == [
        (
            'main',
            ('main', 'helper1', 'helper3'),
            'main:codex; helper1:codex; helper3:codex',
        ),
    ]
    plan = build_reload_dry_run_plan(before_remove, after_remove, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'remove_agent'
    assert plan['future_safe_to_apply'] is True
    assert set(plan['namespace_patch_plan']['preserved_agents']) == {'main', 'helper1', 'helper3'}
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'kill_agent_pane',
            'window': 'main',
            'agent': 'helper2',
            'role': 'agent',
            'slot_key': 'helper2',
            'managed_by': 'ccbd',
            'reason': 'agent exists only in current published config',
        }
    ]


def test_agent_add_to_new_window_projects_add_window_reload_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    current = load_project_config(project_root, include_loop_overlays=False).config

    result, payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'review', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['window_name'] == 'review'
    loaded = load_project_config(project_root).config
    assert loaded.windows_explicit is True
    assert [(window.name, window.agent_names, window.layout_spec) for window in loaded.windows] == [
        ('main', ('main',), 'main:codex'),
        ('review', ('helper',), 'helper:codex'),
    ]
    plan = build_reload_dry_run_plan(current, loaded, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'add_window'
    assert {'add_agent', 'add_window'} == {item['op'] for item in plan['operations']}
    assert plan['namespace_patch_plan']['status'] == 'planned'
    assert [step['action'] for step in plan['namespace_patch_plan']['steps']] == [
        'create_window',
        'create_sidebar_pane',
        'create_agent_pane',
    ]
    assert plan['namespace_patch_plan']['steps'][-1]['window'] == 'review'
    assert plan['namespace_patch_plan']['steps'][-1]['agent'] == 'helper'


def test_agent_move_dynamic_agent_uses_move_agent_reload_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _helper, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    result, _reviewer, stderr = _run_phase2(
        ['agent', 'add', 'reviewer:codex', '--role', 'agentroles.general', '--window', 'review', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        ['agent', 'move', 'helper', '--window', 'review', '--reason', 'group review node', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['previous_window_name'] == 'main'
    assert moved['resolved_window_name'] == 'review'
    assert moved['placement']['window_name'] == 'review'
    assert moved['apply']['apply_status'] == 'deferred_until_start'
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in after_move.windows] == [
        ('main', ('main',), 'main:codex'),
        ('review', ('reviewer', 'helper'), 'reviewer:codex; helper:codex'),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'move_agent_pane',
            'window': 'main',
            'target_window': 'review',
            'agent': 'helper',
            'role': 'agent',
            'slot_key': 'helper',
            'managed_by': 'ccbd',
            'reason': 'existing dynamic agent window membership changed',
        }
    ]


def test_agent_move_dynamic_agent_to_new_window_uses_add_window_move_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _helper, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        ['agent', 'move', 'helper', '--window', 'review', '--reason', 'new review window', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['previous_window_name'] == 'main'
    assert moved['resolved_window_name'] == 'review'
    assert moved['placement']['window_name'] == 'review'
    assert moved['placement']['placement_sequence'] == 1
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in after_move.windows] == [
        ('main', ('main',), 'main:codex'),
        ('review', ('helper',), 'helper:codex'),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert [item['op'] for item in plan['operations']] == ['add_window', 'move_agent']
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'create_window',
            'window': 'review',
            'managed_by': 'ccbd',
            'reason': 'window exists only in new config',
        },
        {
            'action': 'create_sidebar_pane',
            'window': 'review',
            'role': 'sidebar',
            'slot_key': 'sidebar:review',
            'managed_by': 'ccbd',
            'reason': 'new managed window needs a sidebar pane',
        },
        {
            'action': 'move_agent_pane',
            'window': 'main',
            'target_window': 'review',
            'agent': 'helper',
            'role': 'agent',
            'slot_key': 'helper',
            'managed_by': 'ccbd',
            'reason': 'existing dynamic agent window membership changed',
        },
    ]


def test_agent_move_dynamic_agent_back_removes_empty_source_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _helper, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'review', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        ['agent', 'move', 'helper', '--window', 'main', '--reason', 'return to main', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['previous_window_name'] == 'review'
    assert moved['resolved_window_name'] == 'main'
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in after_move.windows] == [
        ('main', ('main', 'helper'), 'main:codex; helper:codex'),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert [item['op'] for item in plan['operations']] == ['move_agent', 'layout_change']
    assert plan['operations'][1]['change'] == 'remove_window'
    assert plan['operations'][1]['window'] == 'review'
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'move_agent_pane',
            'window': 'review',
            'target_window': 'main',
            'agent': 'helper',
            'role': 'agent',
            'slot_key': 'helper',
            'managed_by': 'ccbd',
            'reason': 'existing dynamic agent window membership changed',
        },
        {
            'action': 'kill_window',
            'window': 'review',
            'managed_by': 'ccbd',
            'reason': 'window emptied by moved agents',
        },
    ]


def test_agent_move_dynamic_agent_from_shared_source_keeps_source_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for helper in ('helper1', 'helper2'):
        result, _payload, stderr = _run_phase2(
            [
                'agent',
                'add',
                f'{helper}:codex',
                '--role',
                'agentroles.general',
                '--window',
                'review',
                '--hidden',
                '--json',
            ],
            cwd=project_root,
        )
        assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        ['agent', 'move', 'helper1', '--window', 'main', '--reason', 'split shared review source', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['previous_window_name'] == 'review'
    assert moved['resolved_window_name'] == 'main'
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in after_move.windows] == [
        ('main', ('main', 'helper1'), 'main:codex; helper1:codex'),
        ('review', ('helper2',), 'helper2:codex'),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert [item['op'] for item in plan['operations']] == ['move_agent']
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'move_agent_pane',
            'window': 'review',
            'target_window': 'main',
            'agent': 'helper1',
            'role': 'agent',
            'slot_key': 'helper1',
            'managed_by': 'ccbd',
            'reason': 'existing dynamic agent window membership changed',
        }
    ]


def test_agent_move_batch_moves_dynamic_agents_to_new_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for helper in ('zeta', 'alpha'):
        result, _payload, stderr = _run_phase2(
            [
                'agent',
                'add',
                f'{helper}:codex',
                '--role',
                'agentroles.general',
                '--window',
                'review',
                '--hidden',
                '--json',
            ],
            cwd=project_root,
        )
        assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        [
            'agent',
            'move',
            '--agents',
            'zeta,alpha',
            '--window',
            'archive',
            '--reason',
            'batch archive',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['agent_lifecycle_status'] == 'active'
    assert moved['moved_agents'] == ['zeta', 'alpha']
    assert moved['target_window_name'] == 'archive'
    assert moved['apply']['apply_status'] == 'deferred_until_start'
    assert [(agent['agent'], agent['resolved_window_name']) for agent in moved['agents']] == [
        ('zeta', 'archive'),
        ('alpha', 'archive'),
    ]
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in after_move.windows] == [
        ('main', ('main',), 'main:codex'),
        ('archive', ('zeta', 'alpha'), 'zeta:codex; alpha:codex'),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert [item['op'] for item in plan['operations']] == [
        'add_window',
        'move_agent',
        'move_agent',
        'layout_change',
    ]
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'create_window',
            'window': 'archive',
            'managed_by': 'ccbd',
            'reason': 'window exists only in new config',
        },
        {
            'action': 'create_sidebar_pane',
            'window': 'archive',
            'role': 'sidebar',
            'slot_key': 'sidebar:archive',
            'managed_by': 'ccbd',
            'reason': 'new managed window needs a sidebar pane',
        },
        {
            'action': 'move_agent_pane',
            'window': 'review',
            'target_window': 'archive',
            'agent': 'zeta',
            'role': 'agent',
            'slot_key': 'zeta',
            'managed_by': 'ccbd',
            'reason': 'existing dynamic agent window membership changed',
        },
        {
            'action': 'move_agent_pane',
            'window': 'review',
            'target_window': 'archive',
            'agent': 'alpha',
            'role': 'agent',
            'slot_key': 'alpha',
            'managed_by': 'ccbd',
            'reason': 'existing dynamic agent window membership changed',
        },
        {
            'action': 'kill_window',
            'window': 'review',
            'managed_by': 'ccbd',
            'reason': 'window emptied by moved agents',
        },
    ]


def test_agent_move_batch_resolves_window_class_capacity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / 'repo-agent-lifecycle-batch-window-class'
    role_store = tmp_path / 'roles'
    _write_installed_role(role_store, 'agentroles.general', default_agent_name='general')
    monkeypatch.setenv('AGENT_ROLES_STORE', str(role_store))
    _write(
        project_root / '.ccb' / 'ccb.config',
        """version = 2
entry_window = "main"

[windows]
main = "main:codex"
plan-orchestrate = "p1:codex, p2:codex, p3:codex, p4:codex, p5:codex"
""",
    )
    for helper in ('zeta', 'alpha'):
        result, _payload, stderr = _run_phase2(
            [
                'agent',
                'add',
                f'{helper}:codex',
                '--role',
                'agentroles.general',
                '--window',
                'review',
                '--hidden',
                '--json',
            ],
            cwd=project_root,
        )
        assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        [
            'agent',
            'move',
            '--agents',
            'zeta,alpha',
            '--window-class',
            'plan-orchestrate',
            '--reason',
            'batch class placement',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['agent_lifecycle_status'] == 'active'
    assert moved['moved_agents'] == ['zeta', 'alpha']
    assert moved['target_window_name'] is None
    assert moved['target_window_names'] == ['plan-orchestrate', 'plan-orchestrate-2']
    assert [(agent['agent'], agent['resolved_window_name']) for agent in moved['agents']] == [
        ('zeta', 'plan-orchestrate'),
        ('alpha', 'plan-orchestrate-2'),
    ]
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names) for window in after_move.windows] == [
        ('main', ('main',)),
        ('plan-orchestrate', ('p1', 'p2', 'p3', 'p4', 'p5', 'zeta')),
        ('plan-orchestrate-2', ('alpha',)),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert [item['op'] for item in plan['operations']] == [
        'add_window',
        'move_agent',
        'move_agent',
        'layout_change',
    ]
    assert plan['namespace_patch_plan']['steps'][-1] == {
        'action': 'kill_window',
        'window': 'review',
        'managed_by': 'ccbd',
        'reason': 'window emptied by moved agents',
    }


def test_agent_move_batch_resolves_execution_node_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for agent in ('worker', 'checker'):
        result, _payload, stderr = _run_phase2(
            [
                'agent',
                'add',
                f'{agent}:codex',
                '--role',
                'agentroles.general',
                '--window',
                'review',
                '--hidden',
                '--json',
            ],
            cwd=project_root,
        )
        assert result == 0, stderr
    before_move = load_project_config(project_root).config

    result, moved, stderr = _run_phase2(
        [
            'agent',
            'move',
            '--agents',
            'worker,checker',
            '--loop-id',
            'round1',
            '--node-id',
            'node1',
            '--reason',
            'batch execution node placement',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['agent_lifecycle_status'] == 'active'
    assert moved['target_window_name'] == 'node-round1-node1'
    assert moved['target_window_names'] == ['node-round1-node1']
    assert [(agent['agent'], agent['resolved_window_name']) for agent in moved['agents']] == [
        ('worker', 'node-round1-node1'),
        ('checker', 'node-round1-node1'),
    ]
    after_move = load_project_config(project_root).config
    assert [(window.name, window.agent_names) for window in after_move.windows] == [
        ('main', ('main',)),
        ('node-round1-node1', ('worker', 'checker')),
    ]
    plan = build_reload_dry_run_plan(before_move, after_move, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'move_agent'
    assert plan['future_safe_to_apply'] is True
    assert [item['op'] for item in plan['operations']] == [
        'add_window',
        'move_agent',
        'move_agent',
        'layout_change',
    ]
    assert plan['namespace_patch_plan']['steps'][-1] == {
        'action': 'kill_window',
        'window': 'review',
        'managed_by': 'ccbd',
        'reason': 'window emptied by moved agents',
    }


def test_agent_add_with_loop_node_places_agent_in_node_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)

    result, payload, stderr = _run_phase2(
        [
            'agent',
            'add',
            'worker1:codex',
            '--role',
            'agentroles.general',
            '--loop-id',
            'round1',
            '--node-id',
            'node1',
            '--hidden',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['placement']['mode'] == 'execution_node'
    assert payload['resolved_window_name'] == 'node-round1-node1'
    assert payload['placement']['window_name'] == 'node-round1-node1'
    loaded = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in loaded.windows] == [
        ('main', ('main',), 'main:codex'),
        ('node-round1-node1', ('worker1',), 'worker1:codex'),
    ]


def test_agent_add_second_loop_node_agent_appends_without_reordering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, worker, stderr = _run_phase2(
        [
            'agent',
            'add',
            'worker1:codex',
            '--role',
            'agentroles.general',
            '--loop-id',
            'round1',
            '--node-id',
            'node1',
            '--hidden',
            '--json',
        ],
        cwd=project_root,
    )
    assert result == 0, stderr
    assert worker['created_sequence'] == 1
    after_worker = load_project_config(project_root).config

    result, checker, stderr = _run_phase2(
        [
            'agent',
            'add',
            'checker1:codex',
            '--role',
            'agentroles.general',
            '--loop-id',
            'round1',
            '--node-id',
            'node1',
            '--hidden',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert checker['created_sequence'] == 2
    assert checker['resolved_window_name'] == 'node-round1-node1'
    loaded = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in loaded.windows] == [
        ('main', ('main',), 'main:codex'),
        ('node-round1-node1', ('worker1', 'checker1'), 'worker1:codex; checker1:codex'),
    ]
    plan = build_reload_dry_run_plan(after_worker, loaded, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert plan['plan_class'] == 'add_agent'
    assert plan['namespace_patch_plan']['steps'] == [
        {
            'action': 'create_agent_pane',
            'window': 'node-round1-node1',
            'agent': 'checker1',
            'role': 'agent',
            'slot_key': 'checker1',
            'managed_by': 'ccbd',
            'anchor_agent': 'worker1',
            'reason': 'new agent appended to existing managed window',
        }
    ]


def test_agent_add_with_window_class_creates_class_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)

    result, payload, stderr = _run_phase2(
        [
            'agent',
            'add',
            'planner2:codex',
            '--role',
            'agentroles.general',
            '--window-class',
            'plan-orchestrate',
            '--hidden',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['placement']['mode'] == 'window_class'
    assert payload['resolved_window_name'] == 'plan-orchestrate'
    assert payload['placement']['window_name'] == 'plan-orchestrate'
    loaded = load_project_config(project_root).config
    assert [(window.name, window.agent_names, window.layout_spec) for window in loaded.windows] == [
        ('main', ('main',), 'main:codex'),
        ('plan-orchestrate', ('planner2',), 'planner2:codex'),
    ]


def test_agent_add_with_window_class_overflows_to_next_class_window(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / 'repo-agent-lifecycle-overflow'
    role_store = tmp_path / 'roles'
    _write_installed_role(role_store, 'agentroles.general', default_agent_name='general')
    monkeypatch.setenv('AGENT_ROLES_STORE', str(role_store))
    _write(
        project_root / '.ccb' / 'ccb.config',
        """version = 2
entry_window = "main"

[windows]
main = "main:codex"
plan-orchestrate = "p1:codex, p2:codex, p3:codex, p4:codex, p5:codex, p6:codex"
""",
    )

    result, payload, stderr = _run_phase2(
        [
            'agent',
            'add',
            'planner2:codex',
            '--role',
            'agentroles.general',
            '--window-class',
            'plan-orchestrate',
            '--hidden',
            '--json',
        ],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['placement']['mode'] == 'window_class'
    assert payload['window_class'] == 'plan-orchestrate'
    assert payload['resolved_window_name'] == 'plan-orchestrate-2'
    assert payload['placement']['window_name'] == 'plan-orchestrate-2'
    loaded = load_project_config(project_root).config
    assert [(window.name, window.agent_names) for window in loaded.windows] == [
        ('main', ('main',)),
        ('plan-orchestrate', ('p1', 'p2', 'p3', 'p4', 'p5', 'p6')),
        ('plan-orchestrate-2', ('planner2',)),
    ]


def test_agent_add_while_mounted_applies_reload_and_reports_runtime_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'add_agent',
            'published_graph_version': 2,
            'namespace_patch': {
                'status': 'applied',
                'agent_panes': {'helper': '%3'},
                'preserved_before': {'main': '%1'},
                'preserved_after': {'main': '%1'},
            },
            'runtime_mount': {
                'status': 'mounted',
                'mounted_agents': ['helper'],
                'runtime_authority_written_agents': ['helper'],
            },
        },
    )

    result, payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert payload['apply']['apply_status'] == 'applied'
    assert payload['apply']['reload_status'] == 'published'
    assert payload['apply']['plan_class'] == 'add_agent'
    assert payload['apply']['namespace_agent_panes'] == {'helper': '%3'}
    assert payload['apply']['namespace_preserved_before'] == {'main': '%1'}
    assert payload['apply']['namespace_preserved_after'] == {'main': '%1'}
    assert payload['apply']['runtime_mount_status'] == 'mounted'
    assert payload['apply']['runtime_authority_written_agents'] == ['helper']
    assert payload['apply']['pane_identity_report']['added_agents'] == [
        {'agent': 'helper', 'pane_id': '%3', 'pane_identity_source': 'namespace_agent_panes'}
    ]
    assert payload['apply']['pane_identity_report']['preserved_agents'] == [
        {
            'agent': 'main',
            'before_pane_id': '%1',
            'after_pane_id': '%1',
            'pane_identity_source': 'namespace_preserved_before_after',
            'changed': False,
        }
    ]
    assert payload['apply']['pane_identity_report']['mounted_agents'] == ['helper']
    assert payload['pane_id'] == '%3'
    assert payload['applied']['status'] == 'applied'
    assert payload['applied']['window_name'] == 'main'
    assert payload['applied']['pane_id'] == '%3'
    assert payload['placement']['window_name'] == 'main'
    assert payload['placement']['pane_id'] == '%3'
    assert 'helper' in load_project_config(project_root).config.agents


def test_agent_add_while_mounted_reports_reload_failure_details_and_rolls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: {
            'status': 'failed',
            'stage': 'namespace_patch',
            'plan_class': 'add_agent',
            'diagnostics': {'reason': 'namespace_patch_failed'},
            'namespace_patch': {
                'status': 'failed',
                'diagnostics': {
                    'reason': 'namespace_patch_failed',
                    'error': "anchor pane missing for preserved agent 'main'",
                },
            },
        },
    )

    result, _payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 1
    assert 'stage=namespace_patch' in stderr
    assert 'plan_class=add_agent' in stderr
    assert 'reason=namespace_patch_failed' in stderr
    assert "anchor pane missing for preserved agent 'main'" in stderr
    assert 'helper' not in load_project_config(project_root).config.agents


def test_agent_remove_auto_parks_unknown_or_long_lived_dynamic_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    assert payload['role_class'] == 'unknown'

    result, removed, stderr = _run_phase2(
        ['agent', 'remove', 'helper', '--policy', 'auto', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert removed['requested_policy'] == 'auto'
    assert removed['resolved_policy'] == 'park'
    assert removed['lifecycle_state'] == 'parked'
    loaded = load_project_config(project_root).config
    assert 'helper' in loaded.agents
    assert loaded.agents['helper'].dispatch_disabled is True


def test_agent_park_resume_projects_dispatch_disabled_overlay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    before_park = load_project_config(project_root).config
    assert before_park.agents['helper'].dispatch_disabled is False

    result, parked, stderr = _run_phase2(['agent', 'park', 'helper', '--json'], cwd=project_root)

    assert result == 0, stderr
    assert parked['lifecycle_state'] == 'parked'
    assert parked['dispatch_disabled'] is True
    after_park = load_project_config(project_root).config
    assert after_park.agents['helper'].dispatch_disabled is True
    result, status, stderr = _run_phase2(['agent', 'status', '--json'], cwd=project_root)
    assert result == 0, stderr
    helper_status = {record['agent']: record for record in status['agents']}['helper']
    assert helper_status['dispatch_state'] == 'disabled'
    assert helper_status['ownership_class'] == 'dynamic_session'
    assert helper_status['failed_apply'] is False
    park_plan = build_reload_dry_run_plan(before_park, after_park, project_id='proj-1', current_namespace=_namespace('proj-1'))
    assert park_plan['plan_class'] == 'view_only_change'
    assert park_plan['operations'] == [
        {
            'op': 'view_only_change',
            'agent': 'helper',
            'fields': ['dispatch_disabled'],
            'reason': 'existing agent dispatch availability changed without runtime replacement',
        }
    ]

    result, resumed, stderr = _run_phase2(['agent', 'resume', 'helper', '--hidden', '--json'], cwd=project_root)

    assert result == 0, stderr
    assert resumed['lifecycle_state'] == 'hidden'
    assert resumed['dispatch_disabled'] is False
    assert load_project_config(project_root).config.agents['helper'].dispatch_disabled is False


def test_agent_remove_unload_removes_dynamic_overlay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _payload, stderr = _run_phase2(
        ['agent', 'add', 'reviewer', '--profile', 'code_reviewer', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr

    result, removed, stderr = _run_phase2(
        ['agent', 'remove', 'reviewer', '--policy', 'unload', '--idle-only', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert removed['resolved_policy'] == 'unload'
    assert removed['lifecycle_state'] == 'unloaded'
    assert removed['apply']['apply_status'] == 'deferred_until_start'
    assert 'reviewer' not in load_project_config(project_root).config.agents


def test_agent_release_auto_unloads_short_lived_dynamic_agent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, payload, stderr = _run_phase2(
        ['agent', 'add', 'reviewer', '--profile', 'code_reviewer', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    assert payload['role_class'] == 'short_lived_execution'

    result, released, stderr = _run_phase2(
        ['agent', 'release', 'reviewer', '--idle-only', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert released['action'] == 'release'
    assert released['requested_action'] == 'release'
    assert released['requested_policy'] == 'auto'
    assert released['resolved_policy'] == 'unload'
    assert released['lifecycle_state'] == 'unloaded'
    assert released['apply']['apply_status'] == 'deferred_until_start'
    assert 'reviewer' not in load_project_config(project_root).config.agents


def test_agent_release_batch_auto_unloads_short_lived_dynamic_agents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for name in ('reviewer1', 'reviewer2'):
        result, payload, stderr = _run_phase2(
            ['agent', 'add', name, '--profile', 'code_reviewer', '--hidden', '--json'],
            cwd=project_root,
        )
        assert result == 0, stderr
        assert payload['role_class'] == 'short_lived_execution'

    result, released, stderr = _run_phase2(
        ['agent', 'release', '--agents', 'reviewer1,reviewer2', '--idle-only', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert released['action'] == 'release'
    assert released['agent_lifecycle_status'] == 'removed'
    assert released['requested_policy'] == 'auto'
    assert released['resolved_policies'] == {'reviewer1': 'unload', 'reviewer2': 'unload'}
    assert released['removed_agents'] == ['reviewer1', 'reviewer2']
    assert released['apply']['apply_status'] == 'deferred_until_start'
    assert {item['agent']: item['lifecycle_state'] for item in released['agents']} == {
        'reviewer1': 'unloaded',
        'reviewer2': 'unloaded',
    }
    loaded = load_project_config(project_root).config
    assert 'reviewer1' not in loaded.agents
    assert 'reviewer2' not in loaded.agents


def test_agent_remove_while_mounted_unloads_and_reports_runtime_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    reload_results = [
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'add_agent',
            'published_graph_version': 2,
            'namespace_patch': {
                'status': 'applied',
                'agent_panes': {'helper': '%3'},
                'preserved_before': {'main': '%1'},
                'preserved_after': {'main': '%1'},
            },
            'runtime_mount': {
                'status': 'mounted',
                'mounted_agents': ['helper'],
                'runtime_authority_written_agents': ['helper'],
            },
        },
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'remove_agent',
            'published_graph_version': 3,
            'namespace_patch': {
                'status': 'applied',
                'removed_agents': {'helper': '%3'},
                'removed_panes': ['%3'],
                'preserved_before': {'main': '%1'},
                'preserved_after': {'main': '%1'},
                'reflowed_windows': ['main'],
            },
            'runtime_mount': {
                'status': 'unloaded',
                'unloaded_agents': ['helper'],
                'runtime_authority_stopped_agents': ['helper'],
            },
        },
    ]
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: reload_results.pop(0),
    )

    result, added, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    assert added['pane_id'] == '%3'
    assert 'helper' in load_project_config(project_root).config.agents

    result, removed, stderr = _run_phase2(
        ['agent', 'remove', 'helper', '--policy', 'unload', '--idle-only', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert removed['resolved_policy'] == 'unload'
    assert removed['lifecycle_state'] == 'unloaded'
    assert removed['apply']['apply_status'] == 'applied'
    assert removed['apply']['plan_class'] == 'remove_agent'
    assert removed['apply']['namespace_removed_agents'] == {'helper': '%3'}
    assert removed['apply']['namespace_removed_panes'] == ['%3']
    assert removed['apply']['namespace_preserved_before'] == {'main': '%1'}
    assert removed['apply']['namespace_preserved_after'] == {'main': '%1'}
    assert removed['apply']['namespace_reflowed_windows'] == ['main']
    assert removed['apply']['runtime_mount_status'] == 'unloaded'
    assert removed['apply']['unloaded_agents'] == ['helper']
    assert removed['apply']['runtime_authority_stopped_agents'] == ['helper']
    assert removed['apply']['pane_identity_report']['removed_agents'] == [
        {'agent': 'helper', 'pane_id': '%3', 'pane_identity_source': 'namespace_removed_agents'}
    ]
    assert removed['apply']['pane_identity_report']['removed_panes'] == ['%3']
    assert removed['apply']['pane_identity_report']['reflowed_windows'] == ['main']
    assert removed['apply']['pane_identity_report']['preserved_agents'] == [
        {
            'agent': 'main',
            'before_pane_id': '%1',
            'after_pane_id': '%1',
            'pane_identity_source': 'namespace_preserved_before_after',
            'changed': False,
        }
    ]
    assert removed['apply']['pane_identity_report']['unloaded_agents'] == ['helper']
    assert removed['last_pane_id'] == '%3'
    assert removed['pane_id'] is None
    assert removed['placement']['last_pane_id'] == '%3'
    assert removed['placement']['pane_id'] is None
    assert removed['applied']['status'] == 'unloaded'
    assert removed['applied']['removed_pane_id'] == '%3'
    assert removed['applied']['window_name'] == 'main'
    assert removed['applied']['unloaded_agents'] == ['helper']
    assert 'helper' not in load_project_config(project_root).config.agents
    assert reload_results == []


def test_agent_remove_batch_while_mounted_unloads_and_reports_runtime_details(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for name in ('helper1', 'helper2'):
        result, _payload, stderr = _run_phase2(
            ['agent', 'add', f'{name}:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
            cwd=project_root,
        )
        assert result == 0, stderr
    reload_results = [
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'remove_agent',
            'published_graph_version': 4,
            'namespace_patch': {
                'status': 'applied',
                'removed_agents': {'helper1': '%3', 'helper2': '%4'},
                'removed_panes': ['%3', '%4'],
                'preserved_before': {'main': '%1'},
                'preserved_after': {'main': '%1'},
                'reflowed_windows': ['main'],
            },
            'runtime_mount': {
                'status': 'unloaded',
                'unloaded_agents': ['helper1', 'helper2'],
                'runtime_authority_stopped_agents': ['helper1', 'helper2'],
            },
        },
    ]
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: reload_results.pop(0),
    )

    result, removed, stderr = _run_phase2(
        ['agent', 'remove', '--agents', 'helper1,helper2', '--policy', 'unload', '--idle-only', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert removed['agent_lifecycle_status'] == 'removed'
    assert removed['removed_agents'] == ['helper1', 'helper2']
    assert removed['resolved_policies'] == {'helper1': 'unload', 'helper2': 'unload'}
    assert removed['apply']['apply_status'] == 'applied'
    assert removed['apply']['plan_class'] == 'remove_agent'
    assert removed['apply']['namespace_removed_agents'] == {'helper1': '%3', 'helper2': '%4'}
    assert removed['apply']['namespace_removed_panes'] == ['%3', '%4']
    assert removed['apply']['namespace_reflowed_windows'] == ['main']
    assert removed['apply']['runtime_mount_status'] == 'unloaded'
    assert removed['apply']['unloaded_agents'] == ['helper1', 'helper2']
    assert removed['apply']['runtime_authority_stopped_agents'] == ['helper1', 'helper2']
    by_agent = {item['agent']: item for item in removed['agents']}
    assert by_agent['helper1']['apply_plan_class'] == 'remove_agent'
    assert by_agent['helper2']['apply_plan_class'] == 'remove_agent'
    assert by_agent['helper1']['pane_id'] is None
    assert by_agent['helper2']['pane_id'] is None
    loaded = load_project_config(project_root).config
    assert 'helper1' not in loaded.agents
    assert 'helper2' not in loaded.agents
    assert reload_results == []


def test_agent_move_while_mounted_reports_move_apply_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _helper, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    result, _reviewer, stderr = _run_phase2(
        ['agent', 'add', 'reviewer:codex', '--role', 'agentroles.general', '--window', 'review', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'move_agent',
            'published_graph_version': 4,
            'namespace_patch': {
                'status': 'applied',
                'moved_agents': {'helper': '%3'},
                'moved_agent_windows': {'helper': 'review'},
                'preserved_before': {'main': '%1', 'reviewer': '%4'},
                'preserved_after': {'main': '%1', 'reviewer': '%4', 'helper': '%3'},
                'reflowed_windows': ['main', 'review'],
            },
            'runtime_mount': {
                'status': 'moved',
                'moved_agents': ['helper'],
                'runtime_authority_moved_agents': ['helper'],
            },
        },
    )

    result, moved, stderr = _run_phase2(
        ['agent', 'move', 'helper', '--window', 'review', '--reason', 'mounted move', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert moved['apply']['apply_status'] == 'applied'
    assert moved['apply']['plan_class'] == 'move_agent'
    assert moved['apply']['namespace_moved_agents'] == {'helper': '%3'}
    assert moved['apply']['namespace_moved_agent_windows'] == {'helper': 'review'}
    assert moved['apply']['namespace_reflowed_windows'] == ['main', 'review']
    assert moved['apply']['runtime_mount_status'] == 'moved'
    assert moved['apply']['moved_agents'] == ['helper']
    assert moved['apply']['runtime_authority_moved_agents'] == ['helper']
    assert moved['apply']['pane_identity_report']['moved_agents'] == [
        {
            'agent': 'helper',
            'pane_id': '%3',
            'window_name': 'review',
            'pane_identity_source': 'namespace_moved_agents',
        }
    ]
    assert moved['apply']['pane_identity_report']['moved_agents_runtime'] == ['helper']
    assert moved['previous_window_name'] == 'main'
    assert moved['resolved_window_name'] == 'review'
    assert moved['pane_id'] == '%3'
    assert moved['placement']['window_name'] == 'review'
    assert moved['placement']['pane_id'] == '%3'
    assert moved['applied']['status'] == 'moved'
    assert moved['applied']['previous_window_name'] == 'main'
    assert moved['applied']['window_name'] == 'review'
    assert moved['applied']['pane_id'] == '%3'
    assert moved['applied']['runtime_authority_moved_agents'] == ['helper']


def test_agent_park_while_mounted_publishes_config_only_change_without_losing_pane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    reload_results = [
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'add_agent',
            'published_graph_version': 2,
            'namespace_patch': {
                'status': 'applied',
                'agent_panes': {'helper': '%3'},
            },
            'runtime_mount': {
                'status': 'mounted',
                'mounted_agents': ['helper'],
                'runtime_authority_written_agents': ['helper'],
            },
        },
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'view_only_change',
            'published_graph_version': 3,
            'namespace_patch': {'status': 'applied'},
            'runtime_mount': {'status': 'noop'},
        },
    ]
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: reload_results.pop(0),
    )

    result, added, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr
    assert added['pane_id'] == '%3'

    result, parked, stderr = _run_phase2(['agent', 'park', 'helper', '--json'], cwd=project_root)

    assert result == 0, stderr
    assert parked['lifecycle_state'] == 'parked'
    assert parked['dispatch_disabled'] is True
    assert parked['apply']['apply_status'] == 'applied'
    assert parked['apply']['plan_class'] == 'view_only_change'
    assert parked['pane_id'] == '%3'
    assert parked['placement']['pane_id'] == '%3'
    assert parked['applied']['status'] == 'transitioned'
    assert parked['applied']['pane_id'] == '%3'
    assert parked['applied']['dispatch_disabled'] is True
    assert reload_results == []


def test_agent_batch_park_resume_while_mounted_preserves_panes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    for name in ('planner2', 'broker1'):
        result, _payload, stderr = _run_phase2(
            ['agent', 'add', f'{name}:codex', '--role', 'agentroles.general', '--window', 'main', '--hidden', '--json'],
            cwd=project_root,
        )
        assert result == 0, stderr
    reload_results = [
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'view_only_change',
            'published_graph_version': 4,
            'namespace_patch': {'status': 'applied'},
            'runtime_mount': {'status': 'noop'},
        },
        {
            'status': 'published',
            'stage': 'publish_transaction',
            'plan_class': 'view_only_change',
            'published_graph_version': 5,
            'namespace_patch': {'status': 'applied'},
            'runtime_mount': {'status': 'noop'},
        },
    ]
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.ping_local_state',
        lambda _context: SimpleNamespace(mount_state='mounted', socket_connectable=True, reason=None),
    )
    monkeypatch.setattr(
        'cli.services.agent_lifecycle.reload_config',
        lambda _context, _command: reload_results.pop(0),
    )

    result, parked, stderr = _run_phase2(
        ['agent', 'park', '--agents', 'planner2,broker1', '--reason', 'quiet long-lived group', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert parked['action'] == 'park'
    assert parked['transitioned_agents'] == ['planner2', 'broker1']
    assert parked['lifecycle_state'] == 'parked'
    assert parked['dispatch_disabled'] is True
    assert parked['apply']['apply_status'] == 'applied'
    assert parked['apply']['plan_class'] == 'view_only_change'
    assert {item['agent']: item['lifecycle_state'] for item in parked['agents']} == {
        'planner2': 'parked',
        'broker1': 'parked',
    }
    assert all(item['dispatch_disabled'] is True for item in parked['agents'])
    loaded = load_project_config(project_root).config
    assert loaded.agents['planner2'].dispatch_disabled is True
    assert loaded.agents['broker1'].dispatch_disabled is True

    result, resumed, stderr = _run_phase2(
        ['agent', 'resume', '--agents', 'planner2,broker1', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 0, stderr
    assert resumed['action'] == 'resume'
    assert resumed['transitioned_agents'] == ['planner2', 'broker1']
    assert resumed['lifecycle_state'] == 'hidden'
    assert resumed['dispatch_disabled'] is False
    assert resumed['apply']['apply_status'] == 'applied'
    assert resumed['apply']['plan_class'] == 'view_only_change'
    assert {item['agent']: item['lifecycle_state'] for item in resumed['agents']} == {
        'planner2': 'hidden',
        'broker1': 'hidden',
    }
    assert all(item['dispatch_disabled'] is False for item in resumed['agents'])
    loaded = load_project_config(project_root).config
    assert loaded.agents['planner2'].dispatch_disabled is False
    assert loaded.agents['broker1'].dispatch_disabled is False
    assert reload_results == []


def test_agent_remove_kill_requires_force_and_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)
    result, _payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--role', 'agentroles.general', '--hidden', '--json'],
        cwd=project_root,
    )
    assert result == 0, stderr

    result, _payload, stderr = _run_phase2(
        ['agent', 'remove', 'helper', '--policy', 'kill', '--json'],
        cwd=project_root,
    )

    assert result == 1
    assert 'requires --force and --reason' in stderr


def test_agent_add_requires_role_or_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_agent_profiles(tmp_path, monkeypatch)

    result, _payload, stderr = _run_phase2(
        ['agent', 'add', 'helper:codex', '--hidden', '--json'],
        cwd=project_root,
    )

    assert result == 1
    assert 'requires --role or --profile' in stderr
