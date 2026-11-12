from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = REPO_ROOT / 'mcp' / 'ccb-role-command' / 'server.py'


def _load_module():
    spec = importlib.util.spec_from_file_location('ccb_role_command_server', SERVER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_role_command_server_exposes_only_managed_planner_handoffs() -> None:
    module = _load_module()

    assert [tool['name'] for tool in module._TOOL_DEFS] == [
        'ccb_frontdesk_ask_planner',
        'ccb_task_detailer_replan_planner',
    ]
    schema = module._TOOL_DEFS[0]['inputSchema']
    assert schema['required'] == ['request_id', 'evidence']
    assert schema['additionalProperties'] is False


def test_role_command_server_stdio_handshake_exposes_only_managed_tools() -> None:
    requests = '\n'.join(
        json.dumps(item, ensure_ascii=True)
        for item in (
            {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'initialize',
                'params': {'protocolVersion': '2024-11-05'},
            },
            {'jsonrpc': '2.0', 'method': 'initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'shutdown'},
        )
    ) + '\n'

    completed = subprocess.run(
        [sys.executable, str(SERVER_PATH)],
        input=requests,
        text=True,
        capture_output=True,
        check=True,
    )
    replies = [json.loads(line) for line in completed.stdout.splitlines()]

    assert [reply['id'] for reply in replies] == [1, 2, 3]
    assert [tool['name'] for tool in replies[1]['result']['tools']] == [
        'ccb_frontdesk_ask_planner',
        'ccb_task_detailer_replan_planner',
    ]


def test_frontdesk_tool_submits_exact_silent_planner_ask(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    project_root = tmp_path / 'repo'
    (project_root / '.ccb').mkdir(parents=True)
    (project_root / '.ccb' / 'ccb.config').write_text('frontdesk:codex; planner:codex\n', encoding='utf-8')
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'frontdesk')
    monkeypatch.setenv('CCB_CALLER_PROJECT_ROOT', str(project_root))
    seen: dict[str, object] = {}
    context = object()

    class Builder:
        def build(self, command, *, cwd, bootstrap_if_missing):
            seen['built_command'] = command
            seen['cwd'] = cwd
            seen['bootstrap'] = bootstrap_if_missing
            return context

    monkeypatch.setattr(module, 'CliContextBuilder', Builder)

    def _submit(current, command):
        seen['context'] = current
        seen['command'] = command
        return SimpleNamespace(
            project_id='project-1',
            jobs=[{'job_id': 'job-planner', 'target_name': 'planner', 'status': 'accepted'}],
        )

    monkeypatch.setattr(module, 'submit_ask', _submit)
    evidence = (
        '**Intake Evidence**\n'
        'CCB_REQ_ID: req-1\n'
        'Macro request: ship it\n'
        'Scope:\n- project\n'
        'Required behavior:\n- works\n'
        'Constraints:\n- controlled\n'
    )

    payload = module.submit_frontdesk_planner({'request_id': 'req-1', 'evidence': evidence})
    data = json.loads(payload['content'][0]['text'])
    command = seen['command']

    assert payload.get('isError') is None
    assert data['job_id'] == 'job-planner'
    assert command.target == 'planner'
    assert command.sender is None
    assert command.message == evidence
    assert command.task_id == 'act-frontdesk-req-1'
    assert command.silence is True
    assert command.compact is True
    assert command.inline_request is True
    assert seen['context'] is context
    assert seen['cwd'] == project_root.resolve()
    assert seen['bootstrap'] is False


def test_frontdesk_tool_rejects_wrong_actor_and_mismatched_request(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'planner')
    wrong_actor = module.submit_frontdesk_planner(
        {'request_id': 'req-1', 'evidence': '**Intake Evidence**\nCCB_REQ_ID: req-1'}
    )
    assert wrong_actor['isError'] is True
    assert 'restricted to frontdesk' in wrong_actor['content'][0]['text']

    monkeypatch.setenv('CCB_CALLER_ACTOR', 'frontdesk')
    mismatch = module.submit_frontdesk_planner(
        {'request_id': 'req-1', 'evidence': '**Intake Evidence**\nCCB_REQ_ID: other'}
    )
    assert mismatch['isError'] is True
    assert 'must match request_id' in mismatch['content'][0]['text']

    missing = module.submit_frontdesk_planner(
        {'request_id': 'req-1', 'evidence': '**Intake Evidence**\nMacro request: missing id'}
    )
    assert missing['isError'] is True
    assert 'CCB_REQ_ID must match request_id' in missing['content'][0]['text']


def test_task_detailer_tool_submits_exact_silent_planner_request(monkeypatch, tmp_path: Path) -> None:
    module = _load_module()
    project_root = tmp_path / 'repo'
    (project_root / '.ccb').mkdir(parents=True)
    (project_root / '.ccb' / 'ccb.config').write_text('task_detailer:codex; planner:codex\n', encoding='utf-8')
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'task_detailer')
    monkeypatch.setenv('CCB_CALLER_PROJECT_ROOT', str(project_root))
    request = {
        'schema': 'ccb.detailer.replan_request.v1',
        'request_identity': 'sha256:' + 'a' * 64,
        'task_id': 'task-a',
        'task_revision': 3,
    }
    request_text = json.dumps(request, sort_keys=True, separators=(',', ':'))
    seen: dict[str, object] = {}
    context = object()

    class Builder:
        def build(self, command, *, cwd, bootstrap_if_missing):
            seen['command'] = command
            seen['cwd'] = cwd
            return context

    monkeypatch.setattr(module, 'CliContextBuilder', Builder)
    monkeypatch.setattr(
        module,
        'submit_ask',
        lambda current, command: SimpleNamespace(
            project_id='project-1',
            jobs=[{'job_id': 'job-planner', 'target_name': 'planner', 'status': 'accepted'}],
        ),
    )

    payload = module.submit_task_detailer_replan(
        {'activation_id': 'act-detailer-task-a', 'request': request_text}
    )
    command = seen['command']
    assert payload.get('isError') is None
    assert command.target == 'planner'
    assert command.message == request_text
    assert command.task_id == 'detailer-replan-' + 'a' * 32
    assert command.silence is True
    assert command.compact is True
    assert command.inline_request is True
    assert seen['cwd'] == project_root.resolve()


def test_task_detailer_tool_rejects_wrong_actor_target_or_schema(monkeypatch) -> None:
    module = _load_module()
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'planner')
    payload = module.submit_task_detailer_replan(
        {'activation_id': 'act-detailer-task-a', 'request': '{}'}
    )
    assert payload['isError'] is True
    assert 'restricted to task_detailer' in payload['content'][0]['text']

    monkeypatch.setenv('CCB_CALLER_ACTOR', 'task_detailer')
    invalid_schema = module.submit_task_detailer_replan(
        {'activation_id': 'act-detailer-task-a', 'request': '{}'}
    )
    assert invalid_schema['isError'] is True
    assert 'ccb.detailer.replan_request.v1' in invalid_schema['content'][0]['text']
