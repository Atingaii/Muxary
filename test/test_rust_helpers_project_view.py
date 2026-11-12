from __future__ import annotations

import json
from pathlib import Path

import pytest

from rust_helpers import RUST_HELPER_BIN_ENV, RUST_HELPERS_ENV
from rust_helpers_project_view import (
    RUST_PROJECT_VIEW_ENV,
    read_jobs_query_recent_required,
    read_project_view_recent_jobs_required,
    parse_tmux_project_view_outputs,
)


FOCUS_STDOUT = 'main\t%11\tagent\tagent1\n'
WINDOWS_STDOUT = 'main\t@1\t0\nops\t@2\t1\nbad\nempty\t\tnope\n'
SIDEBARS_STDOUT = (
    'ccb-snap\tmain\t%90\tproj-snap\tsidebar\tmain\tmain\n'
    'ccb-snap\tops\t%91\tproj-snap\tsidebar\tops\tops\n'
    'other\tmain\t%99\tproj-snap\tsidebar\tmain\tmain\n'
)


def _write_helper(path: Path, body: str) -> Path:
    path.write_text('#!/usr/bin/env python3\n' + body, encoding='utf-8')
    path.chmod(0o755)
    return path


def test_default_disabled_does_not_discover_even_if_global_helpers_enabled(tmp_path: Path) -> None:
    def should_not_discover(name: str):
        raise AssertionError(f'unexpected helper discovery: {name}')

    result = parse_tmux_project_view_outputs(
        focus_stdout=FOCUS_STDOUT,
        windows_stdout=WINDOWS_STDOUT,
        sidebars_stdout=SIDEBARS_STDOUT,
        session_name='ccb-snap',
        project_id='proj-snap',
        env={RUST_HELPERS_ENV: '1'},
        which=should_not_discover,
        script_root=tmp_path / 'repo',
    )

    assert result.helper_used is False
    assert result.value['focus']['active_agent'] == 'agent1'
    assert result.value['windows']['main']['tmux_window_index'] == 0
    assert result.value['windows']['empty']['tmux_window_index'] is None
    assert result.value['sidebars'] == {'main': '%90', 'ops': '%91'}
    assert result.diagnostics[0].failure_kind == 'disabled'


def test_project_view_zero_forces_python_fallback_even_when_helper_exists(tmp_path: Path) -> None:
    helper = _write_helper(tmp_path / 'helper.py', 'raise SystemExit(99)\n')

    result = parse_tmux_project_view_outputs(
        focus_stdout=FOCUS_STDOUT,
        windows_stdout=WINDOWS_STDOUT,
        sidebars_stdout=SIDEBARS_STDOUT,
        session_name='ccb-snap',
        project_id='proj-snap',
        env={RUST_PROJECT_VIEW_ENV: '0', RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is False
    assert result.value['focus']['active_window'] == 'main'
    assert result.diagnostics[0].failure_kind == 'disabled'


@pytest.mark.parametrize('mode', ['1', 'auto', 'required'])
def test_project_view_enabled_uses_stub_helper(tmp_path: Path, mode: str) -> None:
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['project_view.tmux.parse']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
        'focus': {'active_window': 'ops', 'active_pane_id': '%22', 'active_agent': 'agent3'},
        'windows': {'ops': {'tmux_window_id': '@2', 'tmux_window_index': 1}},
        'sidebars': {'ops': '%91'},
    }}))
""",
    )

    result = parse_tmux_project_view_outputs(
        focus_stdout=FOCUS_STDOUT,
        windows_stdout=WINDOWS_STDOUT,
        sidebars_stdout=SIDEBARS_STDOUT,
        session_name='ccb-snap',
        project_id='proj-snap',
        env={RUST_HELPERS_ENV: '0', RUST_PROJECT_VIEW_ENV: mode, RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value['focus']['active_agent'] == 'agent3'
    assert result.value['windows'] == {'ops': {'tmux_window_id': '@2', 'tmux_window_index': 1}}
    assert result.diagnostics == ()


def test_project_view_recent_jobs_required_uses_helper_without_python_fallback(tmp_path: Path) -> None:
    helper = _write_helper(
        tmp_path / 'recent_jobs.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['project_view.recent_jobs']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
        'jobs': [{
            'job_id': 'job-1',
            'agent_name': 'agent1',
            'target_name': 'agent1',
            'provider': 'codex',
            'status': 'completed',
            'terminal_decision': {'reason': 'task_complete'},
            'created_at': '2026-06-15T00:00:00Z',
            'updated_at': '2026-06-15T00:00:01Z',
            'provider_options': {},
            'request': {
                'project_id': 'proj',
                'to_agent': 'agent1',
                'from_actor': 'cmd',
                'body': 'work',
                'task_id': None,
                'reply_to': None,
                'message_type': 'ask',
                'delivery_scope': 'single',
                'silence_on_success': False,
                'route_options': {},
                'body_artifact': None,
            },
        }],
        'error': None,
    }}))
""",
    )

    result = read_project_view_recent_jobs_required(
        [{'id': 'agent1', 'path': str(tmp_path / 'missing.jsonl'), 'n': 128}],
        statuses=('completed', 'failed'),
        result_limit=8,
        env={RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value['jobs'][0]['job_id'] == 'job-1'
    assert result.value['jobs'][0]['request']['from_actor'] == 'cmd'


def test_project_view_recent_jobs_required_missing_helper_raises_without_python_fallback(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match='no Python fallback'):
        read_project_view_recent_jobs_required(
            [{'id': 'agent1', 'path': str(tmp_path / 'missing.jsonl'), 'n': 128}],
            statuses=('completed',),
            result_limit=8,
            env={RUST_HELPER_BIN_ENV: str(tmp_path / 'missing-helper')},
        )


def test_jobs_query_recent_required_uses_helper_without_python_fallback(tmp_path: Path) -> None:
    helper = _write_helper(
        tmp_path / 'recent_query.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['jobs.query.recent']}))
else:
    request = json.loads(sys.stdin.read())
    payload = request['payload']
    assert payload['per_agent_initial'] == 4
    assert payload['per_agent_max'] == 16
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
        'jobs': [{
            'job_id': 'job-query-1',
            'agent_name': 'agent1',
            'target_name': 'agent1',
            'provider': 'codex',
            'status': 'completed',
            'terminal_decision': {'reason': 'task_complete'},
            'created_at': '2026-06-15T00:00:00Z',
            'updated_at': '2026-06-15T00:00:01Z',
            'provider_options': {},
            'request': {
                'project_id': 'proj',
                'to_agent': 'agent1',
                'from_actor': 'cmd',
                'body': 'work',
                'task_id': None,
                'reply_to': None,
                'message_type': 'ask',
                'delivery_scope': 'single',
                'silence_on_success': False,
                'route_options': {},
                'body_artifact': None,
            },
        }],
        'scanned': 4,
        'returned': 1,
        'truncated': False,
        'next_budget_hint': {'per_agent_initial': 4, 'per_agent_max': 16},
        'error': None,
    }}))
""",
    )

    result = read_jobs_query_recent_required(
        [{'id': 'agent1', 'path': str(tmp_path / 'missing.jsonl')}],
        statuses=('completed', 'failed'),
        result_limit=8,
        per_agent_initial=4,
        per_agent_max=16,
        env={RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value['jobs'][0]['job_id'] == 'job-query-1'
    assert result.value['scanned'] == 4


def test_jobs_query_recent_required_missing_helper_raises_without_python_fallback(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match='no Python fallback'):
        read_jobs_query_recent_required(
            [{'id': 'agent1', 'path': str(tmp_path / 'missing.jsonl')}],
            statuses=('completed',),
            result_limit=8,
            per_agent_initial=4,
            per_agent_max=16,
            env={RUST_HELPER_BIN_ENV: str(tmp_path / 'missing-helper')},
        )


def test_helper_failures_fallback_without_leaking_content(tmp_path: Path) -> None:
    secret_sidebars = SIDEBARS_STDOUT + 'ccb-snap\tsecret\t%92\tproj-snap\tsidebar\tprovider transcript secret\tsecret\n'

    missing = parse_tmux_project_view_outputs(
        focus_stdout=FOCUS_STDOUT,
        windows_stdout=WINDOWS_STDOUT,
        sidebars_stdout=secret_sidebars,
        session_name='ccb-snap',
        project_id='proj-snap',
        env={RUST_PROJECT_VIEW_ENV: '1'},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )
    assert missing.value['sidebars']['main'] == '%90'
    assert missing.diagnostics[0].failure_kind == 'missing'

    crash_helper = _write_helper(
        tmp_path / 'crash.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['project_view.tmux.parse']}))
else:
    sys.stderr.write('raw secret stderr')
    raise SystemExit(2)
""",
    )
    crash = parse_tmux_project_view_outputs(
        focus_stdout=FOCUS_STDOUT,
        windows_stdout=WINDOWS_STDOUT,
        sidebars_stdout=secret_sidebars,
        session_name='ccb-snap',
        project_id='proj-snap',
        env={RUST_PROJECT_VIEW_ENV: '1', RUST_HELPER_BIN_ENV: str(crash_helper)},
    )
    diagnostics = str([diagnostic.to_dict() for diagnostic in crash.diagnostics])
    assert crash.value['sidebars']['main'] == '%90'
    assert crash.diagnostics[0].failure_kind == 'nonzero_exit'
    assert 'provider transcript secret' not in diagnostics
    assert 'raw secret stderr' not in diagnostics

    bad_payload_helper = _write_helper(
        tmp_path / 'bad_payload.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['project_view.tmux.parse']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'project_view.tmux.parse', 'payload': {'leak': 'provider transcript secret'}}))
""",
    )
    bad_payload = parse_tmux_project_view_outputs(
        focus_stdout=FOCUS_STDOUT,
        windows_stdout=WINDOWS_STDOUT,
        sidebars_stdout=secret_sidebars,
        session_name='ccb-snap',
        project_id='proj-snap',
        env={RUST_PROJECT_VIEW_ENV: '1', RUST_HELPER_BIN_ENV: str(bad_payload_helper)},
    )
    assert bad_payload.helper_used is False
    assert bad_payload.value['sidebars']['main'] == '%90'
    assert bad_payload.diagnostics[0].failure_kind == 'unknown_schema'
    assert 'provider transcript secret' not in str([diagnostic.to_dict() for diagnostic in bad_payload.diagnostics])


def test_project_view_required_missing_helper_raises_without_python_fallback(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match='no Python fallback'):
        parse_tmux_project_view_outputs(
            focus_stdout=FOCUS_STDOUT,
            windows_stdout=WINDOWS_STDOUT,
            sidebars_stdout=SIDEBARS_STDOUT,
            session_name='ccb-snap',
            project_id='proj-snap',
            env={RUST_PROJECT_VIEW_ENV: 'required'},
            which=lambda name: None,
            script_root=tmp_path / 'repo',
        )


def test_project_view_required_bad_payload_raises_without_python_fallback(tmp_path: Path) -> None:
    bad_payload_helper = _write_helper(
        tmp_path / 'bad_payload.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['project_view.tmux.parse']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'project_view.tmux.parse', 'payload': {'invalid': True}}))
""",
    )

    with pytest.raises(RuntimeError, match='no Python fallback'):
        parse_tmux_project_view_outputs(
            focus_stdout=FOCUS_STDOUT,
            windows_stdout=WINDOWS_STDOUT,
            sidebars_stdout=SIDEBARS_STDOUT,
            session_name='ccb-snap',
            project_id='proj-snap',
            env={RUST_PROJECT_VIEW_ENV: 'required', RUST_HELPER_BIN_ENV: str(bad_payload_helper)},
        )
