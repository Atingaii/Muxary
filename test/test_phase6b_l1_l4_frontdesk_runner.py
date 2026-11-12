from __future__ import annotations

import copy
import importlib.util
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from cli.services.planner_task_set_import_transaction import (
    transaction_digest as planner_import_transaction_digest,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = PROJECT_ROOT / 'scripts' / 'phase6b_l1_l4_frontdesk_runner.py'


def _load_runner():
    spec = importlib.util.spec_from_file_location('phase6b_l1_l4_frontdesk_runner', RUNNER_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _materialize(tmp_path: Path, *, label: str = 'sequence19-worker1-20260707150000') -> tuple[Path, dict[str, object]]:
    root = tmp_path / f'deploy-l1-l4-frontdesk-{label}'
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_PATH),
            'materialize',
            '--root',
            str(root),
            '--label',
            label,
            '--project-name',
            'l1-l4-frontdesk-real-provider-lab',
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    manifest_path = Path(result.stdout.strip())
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    return root, manifest


def _command_log_records(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def _canonical_digest(value: object, *, prefixed: bool = False) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    digest = hashlib.sha256(encoded).hexdigest()
    return f'sha256:{digest}' if prefixed else digest


def _frontdesk_activation_digest(activation: dict[str, object]) -> str:
    source_job = activation['source_job']
    source_request = activation['source_request']
    assert isinstance(source_job, dict)
    assert isinstance(source_request, dict)
    mechanical = {
        key: activation[key]
        for key in (
            'schema_version', 'record_type', 'activation_id', 'project_id',
            'project_root', 'action', 'source', 'plan_slug', 'request_id',
            'intake_sha256', 'source_intake', 'planner_contract',
            'required_next_output', 'script_write_rules', 'expected_task_ids',
            'source_task_id', 'direct_ask',
        )
        if key in activation
    }
    mechanical['source_job'] = {
        key: source_job[key]
        for key in ('job_id', 'agent_name', 'reply_sha256')
        if key in source_job
    }
    mechanical['source_request'] = {
        key: source_request[key]
        for key in (
            'source_job_id', 'agent_name', 'project_id', 'to_agent',
            'from_actor', 'message_type', 'text', 'bytes', 'sha256',
        )
        if key in source_request
    }
    return _canonical_digest(mechanical, prefixed=True)


def _resident_ps(state: str = 'idle') -> str:
    return '\n'.join(
        [
            'project_id: test',
            'ccbd_state: mounted',
            f'agent: name=ccb_round_reviewer state={state} provider=claude queue=0',
            f'agent: name=frontdesk state={state} provider=codex queue=0',
            f'agent: name=orchestrator state={state} provider=codex queue=0',
            f'agent: name=planner state={state} provider=codex queue=0',
            f'agent: name=task_detailer state={state} provider=codex queue=0',
            '',
        ]
    )


def test_materializer_emits_fresh_root_manifest_and_current_label_consistently(tmp_path: Path) -> None:
    label = 'sequence19-worker1-20260707150000'
    root, manifest = _materialize(tmp_path, label=label)
    script = Path(str(manifest['script']))
    manifest_path = Path(str(manifest['manifest']))
    active_text = json.dumps(manifest, sort_keys=True) + script.read_text(encoding='utf-8')

    assert manifest['schema'] == 'ccb.phase6b_l1_l4.frontdesk_runner_manifest.v1'
    assert manifest['label'] == label
    assert manifest['root'] == str(root)
    assert manifest['project'] == str(root / 'l1-l4-frontdesk-real-provider-lab')
    assert manifest['script'] == str(root / f'run_l1_l4_frontdesk_{label}.sh')
    assert manifest['b7'] == str(root / f'phase6b-real-provider-l1-l4-{label}-b7.md')
    assert manifest['rows'] == str(root / 'rows' / f'phase6b_l1_l4_{label}_evidence_rows.jsonl')
    assert manifest['command_log'] == str(root / f'phase6b_l1_l4_{label}_command_log.jsonl')
    assert manifest['role_store'] == str(root / 'roles')
    assert manifest_path.is_file()
    assert script.is_file()
    assert str(root) in active_text
    assert label in active_text
    assert 'sequence14' not in active_text
    assert 'sequence17' not in active_text

    commands = manifest['command_sequence']
    assert isinstance(commands, list)
    assert commands[0]['step'] == 'init'
    assert commands[1]['step'] == 'frontdesk-entry'
    assert all(str(command['label']).startswith(label + '__') for command in commands)
    assert all(str(root) in ' '.join(command['argv']) for command in commands)


def test_write_fixtures_make_lab_tests_importable_by_module_name(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))

    runner.write_fixtures(manifest)
    test_module = project / 'tests' / 'test_l2_readiness.py'
    test_module.write_text(
        'import unittest\n\n'
        'class ReadinessImportTest(unittest.TestCase):\n'
        '    def test_imports_from_local_tests_package(self):\n'
        '        self.assertTrue(True)\n'
        '\n',
        encoding='utf-8',
    )
    result = subprocess.run(
        [sys.executable, '-m', 'unittest', 'tests.test_l2_readiness'],
        cwd=project,
        text=True,
        capture_output=True,
        check=False,
    )

    assert (project / 'tests' / '__init__.py').is_file()
    assert result.returncode == 0, result.stderr


def test_materializer_rejects_existing_root_and_stale_sequence_fragments(tmp_path: Path) -> None:
    existing = tmp_path / 'deploy-l1-l4-frontdesk-sequence19-existing'
    existing.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_PATH),
            'materialize',
            '--root',
            str(existing),
            '--label',
            'sequence19-existing',
            '--project-name',
            'l1-l4-frontdesk-real-provider-lab',
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert 'fresh root already exists' in result.stderr

    result = subprocess.run(
        [
            sys.executable,
            str(RUNNER_PATH),
            'materialize',
            '--root',
            str(tmp_path / 'deploy-l1-l4-frontdesk-sequence17-old'),
            '--label',
            'sequence19-new',
            '--project-name',
            'l1-l4-frontdesk-real-provider-lab',
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert 'stale sequence marker' in result.stderr


def test_provider_loop_runner_commands_are_unbounded(tmp_path: Path) -> None:
    _root, manifest = _materialize(tmp_path)
    source_text = RUNNER_PATH.read_text(encoding='utf-8')
    script_text = Path(str(manifest['script'])).read_text(encoding='utf-8')
    active_text = json.dumps(manifest, sort_keys=True) + script_text
    provider_invocations = manifest['provider_loop_invocations']

    assert 'timeout --preserve-status' not in source_text
    assert 'timeout --preserve-status' not in active_text
    assert provider_invocations
    for invocation in provider_invocations:
        argv = invocation['argv']
        assert invocation['unbounded'] is True
        assert argv[-4:] == ['loop', 'runner', '--once', '--json']
        assert '--timeout' not in argv
        assert 'timeout' not in argv


def test_frontdesk_request_is_natural_language_with_current_intake_contract(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)

    request_path = runner.write_frontdesk_request(manifest)
    request = request_path.read_text(encoding='utf-8')

    assert request.startswith('Please start ')
    assert not request.startswith('**Intake Evidence**')
    assert 'User Request' in request
    assert 'Macro request' in request
    assert 'Execution Contract' in request
    assert 'Acceptance Criteria' in request
    assert 'Scope' in request
    assert 'Constraints' in request
    assert '**Intake Evidence**' in request
    assert 'silent handoff to planner' in request.lower()
    assert 'must not directly implement' in request.lower()
    assert 'Project capability: git_repository=not_guaranteed.' in request
    assert 'This lab project may not be a Git repository.' in request
    assert 'Frontdesk must preserve this exact capability in Intake Evidence Constraints.' in request
    assert (
        'Planner verification for this activation must be repo-independent: do not use '
        'git diff, git status, git diff --name-only, or another Git-only scope check; '
        'use allowed_paths plus direct file existence, content, test, or manifest checks.'
    ) in request
    assert 'This constraint applies only to this activation and is not a global Git prohibition.' in request
    for task in runner.TASKS:
        expected_terminal = (
            f"{task['expected_final_status']}/{task['expected_round_result']}"
            if task['expected_final_status'] == 'done'
            else task['expected_final_status']
        )
        assert (
            f"{task['task_id']} ({task['expected_route']}) -> {expected_terminal}"
        ) in request


def test_generated_config_mounts_required_resident_ask_targets_not_only_role_profiles(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))

    runner.write_config(manifest)
    config_text = (project / '.ccb' / 'ccb.config').read_text(encoding='utf-8')
    resident_targets = set(runner.resident_targets_from_config_text(config_text))

    assert '[windows]' in config_text
    assert set(manifest['resident_ask_targets']) == {
        'frontdesk',
        'planner',
        'orchestrator',
        'task_detailer',
        'ccb_round_reviewer',
    }
    assert resident_targets >= set(manifest['resident_ask_targets'])
    assert 'frontdesk:codex' in config_text
    assert 'planner:codex' in config_text
    assert 'orchestrator:codex' in config_text
    assert 'task_detailer:codex' in config_text
    assert 'ccb_round_reviewer:claude' in config_text
    assert 'coder' not in resident_targets
    assert 'code_reviewer' not in resident_targets
    assert '[loop.role_profiles.coder]' in config_text
    assert '[loop.role_profiles.code_reviewer]' in config_text

    worker3_broken_config = """version = 2
entry_window = "main"

[windows]
ccb-user = "bootstrap:codex"

[loop.role_profiles.frontdesk]
role = "agentroles.ccb_frontdesk"
provider = "codex"

[loop.role_profiles.planner]
role = "agentroles.ccb_planner"
provider = "codex"

[loop.role_profiles.orchestrator]
role = "agentroles.ccb_orchestrator"
provider = "codex"

[loop.role_profiles.task_detailer]
role = "agentroles.ccb_task_detailer"
provider = "codex"

[loop.role_profiles.ccb_round_reviewer]
role = "agentroles.ccb_round_reviewer"
provider = "claude"
"""

    assert runner.resident_targets_from_config_text(worker3_broken_config) == ['bootstrap']
    with pytest.raises(runner.HarnessError, match='frontdesk'):
        runner.validate_config_mounts_resident_targets(worker3_broken_config)


def test_frontdesk_entry_rejects_resident_layout_without_mounted_agent_specs(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    command_log = Path(str(manifest['command_log']))
    runner.write_config(manifest)
    runner._write_json(project / '.ccb' / 'agents' / 'bootstrap' / 'agent.json', {'name': 'bootstrap'})
    command_log.write_text(
        json.dumps({'label': str(manifest['label']) + '__preexisting'}) + '\n',
        encoding='utf-8',
    )

    assert [target for target, _path in runner.missing_resident_agent_specs(manifest)] == [
        'frontdesk',
        'planner',
        'orchestrator',
        'task_detailer',
        'ccb_round_reviewer',
    ]

    result = subprocess.run(
        ['bash', str(manifest['script']), 'frontdesk-entry'],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert 'resident_agents_not_mounted' in result.stderr
    assert 'frontdesk:' in result.stderr
    assert all(
        record.get('label') != str(manifest['label']) + '__frontdesk_entry_ask'
        for record in _command_log_records(command_log)
    )


def test_resident_agent_guard_rejects_mismatched_agent_spec_identity(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    runner.write_config(manifest)
    for target in manifest['resident_agent_targets']:
        name = 'bootstrap' if target == 'frontdesk' else str(target)
        runner._write_json(project / '.ccb' / 'agents' / str(target) / 'agent.json', {'name': name})

    problems = runner.resident_agent_mount_problems(manifest)

    assert any(
        problem['target'] == 'frontdesk'
        and problem['reason'] == 'name_mismatch'
        and problem.get('observed') == 'bootstrap'
        for problem in problems
    )
    with pytest.raises(runner.HarnessError, match='resident_agents_not_mounted.*frontdesk.*bootstrap'):
        runner.assert_resident_agents_mounted(manifest)


def test_frontdesk_entry_allows_ask_path_when_all_resident_agent_specs_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    runner.write_config(manifest)
    for target in manifest['resident_agent_targets']:
        runner._write_json(project / '.ccb' / 'agents' / str(target) / 'agent.json', {'name': target})

    runner.assert_resident_agents_mounted(manifest)

    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((observed_manifest, label_suffix, argv))
        if label_suffix == 'resident_ps_before_frontdesk_entry':
            _label, stdout_path, _stderr_path = runner.command_output_paths(
                observed_manifest,
                label_suffix,
            )
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text(_resident_ps(), encoding='utf-8')

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.frontdesk_entry(manifest)

    assert runner.missing_resident_agent_specs(manifest) == []
    assert runner.resident_agent_mount_problems(manifest) == []
    assert [call[1] for call in calls] == [
        'resident_ps_before_frontdesk_entry',
        'frontdesk_entry_ask',
    ]
    assert calls[0][2] == [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps']
    observed_manifest, label_suffix, argv = calls[1]
    assert observed_manifest is manifest
    assert label_suffix == 'frontdesk_entry_ask'
    assert argv[:3] == [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project)]
    assert argv[3:6] == ['ask', 'frontdesk', '--']
    assert Path(str(manifest['frontdesk_request'])).is_file()
    request_text = Path(str(manifest['frontdesk_request'])).read_text(encoding='utf-8')
    assert argv[-4:] == ['ask', 'frontdesk', '--', request_text]
    assert 'controller-owned route-mix validation' in request_text
    assert not Path(str(manifest['command_log'])).exists()


def test_resident_readiness_accepts_all_idle_ps_state(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)

    states = runner.parse_resident_ps_states(_resident_ps())

    assert states == {target: 'idle' for target in manifest['resident_agent_targets']}
    assert runner.resident_readiness_problems(manifest, _resident_ps()) == []
    runner.assert_resident_agents_ready_from_ps(manifest, _resident_ps())


def test_resident_readiness_rejects_degraded_ps_state_before_frontdesk_ask(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    runner.write_config(manifest)
    for target in manifest['resident_agent_targets']:
        runner._write_json(project / '.ccb' / 'agents' / str(target) / 'agent.json', {'name': target})
    worker3_bad_ps = """project_id: 6ee7aaa7
ccbd_state: mounted
agent: name=ccb_round_reviewer state=degraded provider=claude queue=0
agent: name=frontdesk state=degraded provider=codex queue=0
agent: name=orchestrator state=degraded provider=codex queue=0
agent: name=planner state=degraded provider=codex queue=0
agent: name=task_detailer state=degraded provider=codex queue=0
"""

    states = runner.parse_resident_ps_states(worker3_bad_ps)
    assert states['frontdesk'] == 'degraded'
    problems = runner.resident_readiness_problems(manifest, worker3_bad_ps)

    assert {problem['target'] for problem in problems} == set(manifest['resident_agent_targets'])
    assert {problem['reason'] for problem in problems} == {'state_not_ready'}
    with pytest.raises(runner.HarnessError, match='resident_agents_not_ready.*frontdesk.*degraded'):
        runner.assert_resident_agents_ready_from_ps(manifest, worker3_bad_ps)
    with pytest.raises(runner.HarnessError, match='resident_agents_not_ready.*frontdesk.*busy'):
        runner.assert_resident_agents_ready_from_ps(manifest, _resident_ps('busy'))

    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        if label_suffix == 'frontdesk_entry_ask':
            pytest.fail('frontdesk ask must not run when resident ps is degraded')
        _label, stdout_path, _stderr_path = runner.command_output_paths(
            observed_manifest,
            label_suffix,
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(worker3_bad_ps, encoding='utf-8')

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    with pytest.raises(runner.HarnessError, match='resident_agents_not_ready.*frontdesk.*degraded'):
        runner.frontdesk_entry(manifest)

    assert calls == [
        (
            'resident_ps_before_frontdesk_entry',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps'],
        )
    ]
    assert not Path(str(manifest['frontdesk_request'])).exists()


def test_resident_readiness_retries_transient_empty_ps_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        _label, stdout_path, _stderr_path = runner.command_output_paths(
            observed_manifest,
            label_suffix,
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        if label_suffix == 'resident_ps_after_start':
            stdout_path.write_text('', encoding='utf-8')
        else:
            stdout_path.write_text(_resident_ps(), encoding='utf-8')

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)
    monkeypatch.setattr(runner.time, 'sleep', lambda _seconds: None)

    runner.assert_resident_agents_ready(manifest, 'resident_ps_after_start')

    assert calls == [
        (
            'resident_ps_after_start',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps'],
        ),
        (
            'resident_ps_after_start_retry_1',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps'],
        ),
    ]


def test_resident_readiness_rejects_persistently_empty_ps_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        _label, stdout_path, _stderr_path = runner.command_output_paths(
            observed_manifest,
            label_suffix,
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text('', encoding='utf-8')

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)
    monkeypatch.setattr(runner.time, 'sleep', lambda _seconds: None)

    with pytest.raises(runner.HarnessError, match='resident_agents_not_ready.*frontdesk.*state_missing'):
        runner.assert_resident_agents_ready(manifest, 'resident_ps_after_start')

    assert calls == [
        (
            'resident_ps_after_start',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps'],
        ),
        (
            'resident_ps_after_start_retry_1',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps'],
        ),
        (
            'resident_ps_after_start_retry_2',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'ps'],
        ),
    ]


def test_stale_provider_binding_snapshot_detects_log_path_outside_project(tmp_path: Path) -> None:
    runner = _load_runner()
    project = tmp_path / 'current-project'
    project.mkdir()
    snapshot = {
        'delivery_checked_session_root': str(project),
        'delivery_current_log_path': str(tmp_path / 'old-donor' / '.ccb' / 'codex.log'),
    }

    problems = runner.stale_provider_binding_problems(project, snapshot)

    assert problems == [
        {
            'reason': 'stale_provider_session_log_binding',
            'delivery_current_log_path': str(tmp_path / 'old-donor' / '.ccb' / 'codex.log'),
            'project': str(project),
            'delivery_checked_session_root': str(project),
        }
    ]
    assert runner.stale_provider_binding_problems(
        project,
        {'delivery_current_log_path': str(project / '.ccb' / 'agents' / 'frontdesk' / 'codex.log')},
    ) == []


def test_auto_runner_quiet_wait_blocks_manual_progress_while_lock_is_live(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    states = [
        {
            'status': 'live',
            'pid': 12345,
            'path': str(Path(str(manifest['project'])) / '.ccb/runtime/loops/auto-runner.lock'),
        },
        {
            'status': 'live',
            'pid': 12345,
            'path': str(Path(str(manifest['project'])) / '.ccb/runtime/loops/auto-runner.lock'),
        },
    ]
    sleeps = []

    monkeypatch.setattr(runner, 'AUTO_RUNNER_QUIET_ATTEMPTS', len(states))
    monkeypatch.setattr(runner, 'auto_runner_lock_state', lambda _manifest: states.pop(0))
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: sleeps.append(seconds))

    with pytest.raises(
        runner.HarnessBlocker,
        match='runner_resume_and_evidence_integrity.*frontdesk_auto_runner_still_active',
    ):
        runner.wait_for_auto_runner_quiet(manifest, before='start_task_phase6b-l1-doc-direct-execution')

    checkpoint = (
        Path(str(manifest['root']))
        / 'pending-checkpoints'
        / f"{manifest['label']}__auto_runner_active_before_start_task_phase6b-l1-doc-direct-execution.json"
    )
    payload = json.loads(checkpoint.read_text(encoding='utf-8'))
    assert payload['classification'] == 'runner_resume_and_evidence_integrity'
    assert payload['reason'] == 'frontdesk_auto_runner_still_active'
    assert payload['claimable'] is False
    assert payload['auto_runner_lock']['status'] == 'live'
    assert sleeps == [runner.AUTO_RUNNER_QUIET_RETRY_DELAY_SECONDS] * 2


def test_start_task_observes_already_completed_task_before_waiting_for_auto_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l2-code-test-direct-execution'
    calls = []

    monkeypatch.setattr(runner, 'wait_for_planner_task_set_handoff', lambda _manifest, *, before: {})
    monkeypatch.setattr(runner, 'assert_planner_task_set_present', lambda _manifest: {})
    monkeypatch.setattr(runner, 'validate_sequence_task_set_only', lambda _manifest: None)
    monkeypatch.setattr(runner, 'task_record_exists', lambda _manifest, _task_id: True)

    def fail_wait(_manifest, *, before):
        raise AssertionError(f'unexpected auto-runner wait before completed task observation: {before}')

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        assert label_suffix == f'{task_id}__task_observe_existing'
        _label, stdout_path, _stderr_path = runner.command_output_paths(
            observed_manifest,
            label_suffix,
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(
            json.dumps(
                {
                    'task': {
                        'task_id': task_id,
                        'status': 'done',
                        'current_loop': None,
                        'artifacts': {
                            'task_packet': {'path': 'task_packet.md'},
                            'execution_contract': {'path': 'execution_contract.md'},
                            'orchestration_notes': {'orchestrator_route': 'direct_execution'},
                        },
                    },
                }
            ),
            encoding='utf-8',
        )

    monkeypatch.setattr(runner, 'wait_for_auto_runner_quiet', fail_wait)
    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.start_task(manifest, task_id)

    assert [call[0] for call in calls] == [f'{task_id}__task_observe_existing']


def test_start_task_waits_for_frontdesk_auto_runner_before_manual_activation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l1-doc-direct-execution'
    calls = []
    handoff_seen = {'value': False}
    wait_seen = {'value': False}

    def fake_wait_for_planner_task_set_handoff(_manifest, *, before):
        calls.append(('wait_for_planner_task_set_handoff', before))
        handoff_seen['value'] = True
        return {'fenced_task_set_present': True}

    def fake_assert_planner_task_set_present(_manifest):
        assert handoff_seen['value'] is True
        calls.append(('assert_planner_task_set_present', None))
        return {}

    monkeypatch.setattr(runner, 'assert_planner_task_set_present', fake_assert_planner_task_set_present)
    monkeypatch.setattr(runner, 'validate_sequence_task_set_only', lambda _manifest: None)
    monkeypatch.setattr(runner, 'task_record_exists', lambda _manifest, _task_id: True)

    def fake_wait(_manifest, *, before):
        assert handoff_seen['value'] is True
        calls.append(('wait', before))
        wait_seen['value'] = True

    def fake_run_logged(observed_manifest, label_suffix, argv):
        assert handoff_seen['value'] is True
        calls.append(('run_logged', label_suffix))
        if label_suffix.startswith(f'{task_id}__task_observe_existing'):
            _label, stdout_path, _stderr_path = runner.command_output_paths(
                observed_manifest,
                label_suffix,
            )
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text(
                json.dumps(
                    {
                        'task': {
                            'task_id': task_id,
                            'status': 'ready_for_orchestration',
                            'current_loop': None,
                            'artifacts': {
                                'task_packet': {'path': 'task_packet.md'},
                                'execution_contract': {'path': 'execution_contract.md'},
                            },
                        }
                    }
                ),
                encoding='utf-8',
            )

    monkeypatch.setattr(runner, 'wait_for_planner_task_set_handoff', fake_wait_for_planner_task_set_handoff)
    monkeypatch.setattr(runner, 'wait_for_auto_runner_quiet', fake_wait)
    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.start_task(manifest, task_id)

    assert calls == [
        ('wait_for_planner_task_set_handoff', f'start_task_{task_id}'),
        ('assert_planner_task_set_present', None),
        ('run_logged', f'{task_id}__task_observe_existing'),
        ('wait', f'start_task_{task_id}'),
        ('run_logged', f'{task_id}__task_observe_existing__attempt_1'),
        ('run_logged', f'{task_id}__activate_orchestrator'),
    ]


def test_planner_task_set_handoff_wait_checkpoints_before_false_missing_task_set(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    states = [
        {'frontdesk_job_id': 'job_frontdesk', 'frontdesk_job_status': 'running'},
        {'frontdesk_job_id': 'job_frontdesk', 'frontdesk_job_status': 'running'},
    ]
    sleeps = []

    monkeypatch.setattr(runner, 'PLANNER_TASK_SET_WAIT_ATTEMPTS', len(states))
    monkeypatch.setattr(runner, 'planner_task_set_handoff_state', lambda _manifest: states.pop(0))
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: sleeps.append(seconds))

    with pytest.raises(
        runner.HarnessBlocker,
        match='runner_resume_and_evidence_integrity.*frontdesk_planner_handoff_pending',
    ):
        runner.wait_for_planner_task_set_handoff(
            manifest,
            before='start_task_phase6b-l1-doc-direct-execution',
        )

    checkpoint = (
        Path(str(manifest['root']))
        / 'pending-checkpoints'
        / (
            f"{manifest['label']}__planner_task_set_handoff_pending_before_"
            'start_task_phase6b-l1-doc-direct-execution.json'
        )
    )
    payload = json.loads(checkpoint.read_text(encoding='utf-8'))
    assert payload['classification'] == 'runner_resume_and_evidence_integrity'
    assert payload['reason'] == 'frontdesk_planner_handoff_pending'
    assert payload['claimable'] is False
    assert payload['handoff_state']['frontdesk_job_status'] == 'running'
    assert not Path(str(manifest['rows'])).exists()
    assert sleeps == [runner.PLANNER_TASK_SET_WAIT_RETRY_DELAY_SECONDS] * 2


def test_planner_task_set_handoff_blocks_immediately_when_frontdesk_failed_without_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    snapshot = Path(str(manifest['project'])) / '.ccb/ccbd/snapshots/job_frontdesk.json'
    state = {
        'frontdesk_job_id': 'job_frontdesk',
        'frontdesk_job_status': 'failed',
        'frontdesk_job_reason': 'frontdesk_direct_implementation_boundary_violation',
        'frontdesk_snapshot_path': str(snapshot),
        'planner_job_id': None,
        'activation_path': None,
        'fenced_task_set_present': False,
    }
    sleeps = []

    monkeypatch.setattr(runner, 'planner_task_set_handoff_state', lambda _manifest: state)
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: sleeps.append(seconds))

    with pytest.raises(
        runner.HarnessBlocker,
        match='runner_resume_and_evidence_integrity.*frontdesk_terminal_without_planner_handoff',
    ):
        runner.wait_for_planner_task_set_handoff(manifest, before='start_task_phase6b-l1-doc-direct-execution')

    checkpoint = (
        Path(str(manifest['root']))
        / 'pending-checkpoints'
        / (
            f"{manifest['label']}__frontdesk_terminal_without_planner_handoff_before_"
            'start_task_phase6b-l1-doc-direct-execution.json'
        )
    )
    payload = json.loads(checkpoint.read_text(encoding='utf-8'))
    assert payload['reason'] == 'frontdesk_terminal_without_planner_handoff'
    assert payload['handoff_state']['frontdesk_job_status'] == 'failed'
    assert payload['handoff_state']['frontdesk_job_reason'] == 'frontdesk_direct_implementation_boundary_violation'
    assert payload['handoff_state']['frontdesk_snapshot_path'] == str(snapshot)
    assert sleeps == []


def test_planner_task_set_handoff_state_preserves_frontdesk_terminal_snapshot(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    job_id = 'job_frontdesk'
    logs = root / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    (logs / 'entry__frontdesk_entry_ask.stdout').write_text(
        f'accepted job={job_id}\n',
        encoding='utf-8',
    )
    snapshot = project / f'.ccb/ccbd/snapshots/{job_id}.json'
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(
        json.dumps(
            {
                'latest_decision': {
                    'status': 'failed',
                    'reason': 'frontdesk_direct_implementation_boundary_violation',
                }
            }
        ),
        encoding='utf-8',
    )

    state = runner.planner_task_set_handoff_state(manifest)

    assert state['frontdesk_job_id'] == job_id
    assert state['frontdesk_job_status'] == 'failed'
    assert state['frontdesk_job_reason'] == 'frontdesk_direct_implementation_boundary_violation'
    assert state['frontdesk_snapshot_path'] == str(snapshot)
    assert state['planner_job_id'] is None
    assert state['activation_path'] is None


@pytest.mark.parametrize(
    'state',
    [
        {'frontdesk_job_status': 'pending'},
        {'frontdesk_job_status': 'running'},
    ],
)
def test_planner_task_set_handoff_keeps_waiting_for_nonterminal_frontdesk(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: dict[str, object],
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    observed = {'frontdesk_job_id': 'job_frontdesk', **state}
    sleeps = []

    monkeypatch.setattr(runner, 'PLANNER_TASK_SET_WAIT_ATTEMPTS', 1)
    monkeypatch.setattr(runner, 'planner_task_set_handoff_state', lambda _manifest: observed)
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: sleeps.append(seconds))

    with pytest.raises(runner.HarnessBlocker, match='frontdesk_planner_handoff_pending'):
        runner.wait_for_planner_task_set_handoff(manifest, before='start_task')

    assert sleeps == [runner.PLANNER_TASK_SET_WAIT_RETRY_DELAY_SECONDS]


@pytest.mark.parametrize(
    'state',
    [
        {'fenced_task_set_present': True, 'authoritative_parent_present': True},
        {'planner_job_id': 'job_planner', 'planner_job_status': 'failed'},
    ],
)
def test_planner_task_set_handoff_preserves_existing_terminal_conditions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: dict[str, object],
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    monkeypatch.setattr(runner, 'planner_task_set_handoff_state', lambda _manifest: state)
    monkeypatch.setattr(
        runner,
        'controlled_task_set_source_parent_ids',
        lambda _manifest: {'job_frontdesk'} if state.get('authoritative_parent_present') else set(),
    )
    monkeypatch.setattr(
        runner.time,
        'sleep',
        lambda _seconds: (_ for _ in ()).throw(AssertionError('unexpected sleep')),
    )

    assert runner.wait_for_planner_task_set_handoff(manifest, before='start_task') == state


def test_planner_task_set_evidence_ignores_activation_sidecars(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    activation_dir = project / '.ccb/runtime/loops/activations'
    canonical_activation = activation_dir / 'act-frontdesk-job_31092c1cac55.json'
    planner_job_id = 'job_planner'
    runner._write_json(
        canonical_activation,
        {
            'record_type': 'ccb_loop_frontdesk_planner_activation',
            'request_id': 'job_31092c1cac55',
            'source_job': {'job_id': 'job_31092c1cac55'},
            'ask': {'target': 'planner', 'job_id': planner_job_id},
        },
    )
    runner._write_json(
        activation_dir / 'act-frontdesk-job_31092c1cac55.direct-handoff.transaction.json',
        {'record_type': 'ccb_loop_frontdesk_direct_handoff_transaction'},
    )
    runner._write_json(
        activation_dir / 'act-frontdesk-job_31092c1cac55.recovery-error.json',
        {'record_type': 'ccb_loop_frontdesk_recovery_error'},
    )
    planner_reply = (
        project
        / '.ccb/ccbd/artifacts/text/completion-reply'
        / f'{planner_job_id}-art_test.txt'
    )
    planner_reply.parent.mkdir(parents=True, exist_ok=True)
    planner_reply.write_text('**task-set.json**\n', encoding='utf-8')
    state = runner.planner_task_set_evidence(manifest)

    assert state['activation_path'] == str(canonical_activation)
    assert state['planner_job_id'] == planner_job_id
    assert state['planner_reply_path'] == str(planner_reply)
    assert state['fenced_task_set_present'] is True


def test_start_task_waits_for_root10_authority_import_before_validating_source_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(runner, manifest)
    project = Path(str(manifest['project']))
    index_path = (
        project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG / 'tasks' / 'index.json'
    )
    index = json.loads(index_path.read_text(encoding='utf-8'))
    parent = next(task for task in index['tasks'] if task['task_id'] == source_task_id)
    parent['status'] = 'draft'
    parent.pop('task_set_parent')
    runner._write_json(index_path, index)
    sleeps = []

    assert runner.controlled_task_set_source_parent_ids(manifest) == set()
    assert runner.unexpected_plan_task_ids(manifest) == [source_task_id]
    monkeypatch.setattr(runner, 'PLANNER_TASK_SET_WAIT_ATTEMPTS', 1)
    monkeypatch.setattr(runner.time, 'sleep', lambda seconds: sleeps.append(seconds))

    with pytest.raises(
        runner.HarnessBlocker,
        match='runner_resume_and_evidence_integrity.*frontdesk_planner_handoff_pending',
    ):
        runner.start_task(manifest, 'phase6b-l1-doc-direct-execution')

    assert not Path(str(manifest['rows'])).exists()
    assert not Path(str(manifest['b7'])).exists()
    assert sleeps == [runner.PLANNER_TASK_SET_WAIT_RETRY_DELAY_SECONDS]


def test_init_writes_config_before_startup_and_validates_mount_after_startup() -> None:
    source = RUNNER_PATH.read_text(encoding='utf-8')
    init_start = source.index('def init_lab(')
    init_end = source.index('\n\ndef frontdesk_entry(', init_start)
    init_body = source[init_start:init_end]

    assert init_body.index('write_config(manifest)') < init_body.index('"start_project"')
    assert init_body.index('"start_project"') < init_body.index('assert_resident_agents_mounted(manifest)')
    assert init_body.index('assert_resident_agents_mounted(manifest)') < init_body.index(
        'assert_resident_agents_ready(manifest, "resident_ps_after_start")'
    )

    frontdesk_start = source.index('def frontdesk_entry(')
    frontdesk_end = source.index('\n\ndef task_record_exists(', frontdesk_start)
    frontdesk_body = source[frontdesk_start:frontdesk_end]

    assert frontdesk_body.index('assert_resident_agents_mounted(manifest)') < frontdesk_body.index(
        'assert_resident_agents_ready(manifest, "resident_ps_before_frontdesk_entry")'
    )
    assert frontdesk_body.index(
        'assert_resident_agents_ready(manifest, "resident_ps_before_frontdesk_entry")'
    ) < frontdesk_body.index('"frontdesk_entry_ask"')


def test_pending_guard_blocks_cleanup_for_pending_and_incomplete_authority(tmp_path: Path) -> None:
    runner = _load_runner()
    root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    task_id = 'phase6b-l1-doc-direct-execution'

    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lp-pending-round' / 'round.pending.json',
        {'task_id': task_id, 'round_result': 'pending'},
    )
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lp-ask-first' / 'ask_first_stage_state.json',
        {'task_id': task_id, 'status': 'pending'},
    )
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lp-incomplete' / 'round.json',
        {
            'task_id': task_id,
            'round_result_source': 'ask_job_incomplete',
            'worker': {'status': 'incomplete'},
        },
    )

    problems = runner.pending_authority_problems(project)
    reasons = {problem['reason'] for problem in problems}

    assert {'round_pending', 'ask_first_stage_pending', 'ask_job_incomplete'} <= reasons

    result = subprocess.run(
        ['bash', str(manifest['script']), 'cleanup-after-b7'],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert 'round authority pending/incomplete' in result.stderr
    assert not Path(str(manifest['command_log'])).exists()


def test_command_evidence_duplicate_label_is_rejected_before_overwrite(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    label_suffix = 'phase6b-l1-doc-direct-execution__run_direct_execution_round'
    label, stdout_path, stderr_path = runner.command_output_paths(manifest, label_suffix)
    command_log = Path(str(manifest['command_log']))
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text('original stdout evidence\n', encoding='utf-8')
    stderr_path.write_text('original stderr evidence\n', encoding='utf-8')
    command_log.write_text(json.dumps({'label': label, 'stdout': str(stdout_path)}) + '\n', encoding='utf-8')

    with pytest.raises(runner.HarnessError, match='evidence_integrity_duplicate_label'):
        runner.run_logged(manifest, label_suffix, [sys.executable, '-c', 'print("new output")'])

    assert stdout_path.read_text(encoding='utf-8') == 'original stdout evidence\n'
    assert stderr_path.read_text(encoding='utf-8') == 'original stderr evidence\n'


def test_continue_route_recovers_after_route_observation_evidence_is_already_recorded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l2-code-test-direct-execution'
    route_available = {'value': False}
    commands = []

    def fake_subprocess_run(argv, **kwargs):
        commands.append(argv)
        assert argv[-5:] == ['plan', 'task-show', '--task', task_id, '--json']
        artifacts = (
            {'orchestration_notes': {'orchestrator_route': 'direct_execution'}}
            if route_available['value']
            else {}
        )
        kwargs['stdout'].write(
            json.dumps({'task': {'task_id': task_id, 'status': 'done', 'artifacts': artifacts}})
        )
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(runner.subprocess, 'run', fake_subprocess_run)

    with pytest.raises(runner.HarnessError, match='supervisor checkpoint required'):
        runner.import_supervisor_route(manifest, task_id, 'direct_execution')

    route_available['value'] = True
    runner.import_supervisor_route(manifest, task_id, 'direct_execution')

    labels = [record['label'] for record in _command_log_records(Path(str(manifest['command_log'])))]
    assert labels == [
        f"{manifest['label']}__{task_id}__route_observe_existing",
        f"{manifest['label']}__{task_id}__route_observe_existing__attempt_1",
    ]
    assert len(commands) == 2
    assert all(argv[-5:] == ['plan', 'task-show', '--task', task_id, '--json'] for argv in commands)


def test_start_task_reuses_completed_resolved_task_without_provider_resubmission(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    predecessor_id = 'phase6b-l1-doc-direct-execution'
    task_id = 'phase6b-l2-code-test-direct-execution'
    commands = []

    monkeypatch.setattr(runner, 'wait_for_planner_task_set_handoff', lambda _manifest, *, before: {})
    monkeypatch.setattr(runner, 'assert_planner_task_set_present', lambda _manifest: {})
    monkeypatch.setattr(runner, 'validate_sequence_task_set_only', lambda _manifest: None)
    monkeypatch.setattr(
        runner,
        'resolve_sequence_task_id',
        lambda _manifest, requested_task_id: task_id if requested_task_id == predecessor_id else requested_task_id,
    )
    monkeypatch.setattr(runner, 'task_record_exists', lambda _manifest, _task_id: True)
    monkeypatch.setattr(
        runner,
        'wait_for_auto_runner_quiet',
        lambda _manifest, *, before: pytest.fail(f'unexpected auto-runner wait: {before}'),
    )

    def fake_subprocess_run(argv, **kwargs):
        commands.append(argv)
        assert argv[-5:] == ['plan', 'task-show', '--task', task_id, '--json']
        kwargs['stdout'].write(json.dumps({'task': {'task_id': task_id, 'status': 'done'}}))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(runner.subprocess, 'run', fake_subprocess_run)

    runner.start_task(manifest, predecessor_id)
    runner.start_task(manifest, task_id)

    labels = [record['label'] for record in _command_log_records(Path(str(manifest['command_log'])))]
    assert labels == [
        f"{manifest['label']}__{task_id}__task_observe_existing",
        f"{manifest['label']}__{task_id}__task_observe_existing__attempt_1",
    ]
    assert len(commands) == 2
    assert all(argv[-5:] == ['plan', 'task-show', '--task', task_id, '--json'] for argv in commands)


def test_sequence25_pending_reviewer_checkpoint_blocks_b7_and_cleanup(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    task_id = 'phase6b-l1-doc-direct-execution'
    loop_id = 'lp1b2b3a'
    pending_payload = {
        'schema_version': 1,
        'record_type': 'ccb_loop_ask_first_execution_round',
        'loop_run_status': 'pending',
        'loop_id': loop_id,
        'task_id': task_id,
        'pending': {
            'source': 'ask_job_pending',
            'stage': 'reviewer_ask',
            'purpose': 'reviewer',
            'reason': 'reviewer job status running is not terminal',
            'target': f'loop-{loop_id}-code_reviewer-1',
            'job_id': 'job_e9edbc409b48',
            'job_status': 'running',
            'watch_source': 'persisted_terminal',
            'watch_observation': 'not_terminal',
        },
        'reviewer': {
            'target': f'loop-{loop_id}-code_reviewer-1',
            'purpose': 'reviewer',
            'job_id': 'job_e9edbc409b48',
            'status': 'running',
            'terminal': False,
        },
    }
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.pending.json',
        pending_payload,
    )
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / loop_id / 'ask_first_stage_state.json',
        {
            'schema_version': 1,
            'record_type': 'ccb_loop_ask_first_stage_state',
            'status': 'pending',
            'task_id': task_id,
            'loop_id': loop_id,
            'stage': 'reviewer_ask',
            'target': f'loop-{loop_id}-code_reviewer-1',
            'job_id': 'job_e9edbc409b48',
            'purpose': 'reviewer',
            'pending': pending_payload['pending'],
        },
    )

    problems = runner.pending_authority_problems(project, task_id)

    assert {problem['reason'] for problem in problems} == {
        'round_pending',
        'ask_first_stage_pending',
    }
    assert all(problem['loop_id'] == loop_id for problem in problems)
    assert all(problem['task_id'] == task_id for problem in problems)
    assert all(problem['stage'] == 'reviewer_ask' for problem in problems)
    assert all(problem['job_id'] == 'job_e9edbc409b48' for problem in problems)

    for command in ('b7', 'cleanup-after-b7'):
        result = subprocess.run(
            ['bash', str(manifest['script']), command],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 2
        assert 'runner_resume_and_evidence_integrity' in result.stderr
        assert 'ask_first_execution_pending' in result.stderr
        assert 'reviewer_ask' in result.stderr
        assert 'job_e9edbc409b48' in result.stderr

    checkpoint = runner.pending_checkpoint_path(manifest, task_id)
    checkpoint_payload = json.loads(checkpoint.read_text(encoding='utf-8'))
    assert checkpoint_payload['classification'] == 'runner_resume_and_evidence_integrity'
    assert checkpoint_payload['claimable'] is False
    assert checkpoint_payload['resume_command'] == ['bash', str(manifest['script']), 'resume-pending', task_id]
    assert not Path(str(manifest['b7'])).exists()
    assert not Path(str(manifest['rows'])).exists()
    assert not Path(str(manifest['command_log'])).exists()


def test_resume_pending_refuses_nonterminal_job_without_resubmitting(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    task_id = 'phase6b-l1-doc-direct-execution'
    loop_id = 'lp1b2b3a'
    target = f'loop-{loop_id}-code_reviewer-1'
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.pending.json',
        {
            'loop_run_status': 'pending',
            'loop_id': loop_id,
            'task_id': task_id,
            'pending': {
                'stage': 'reviewer_ask',
                'target': target,
                'job_id': 'job_e9edbc409b48',
                'job_status': 'running',
            },
        },
    )
    jobs_path = project / '.ccb' / 'agents' / target / 'jobs.jsonl'
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        json.dumps({'job_id': 'job_e9edbc409b48', 'status': 'running'}) + '\n',
        encoding='utf-8',
    )

    result = subprocess.run(
        ['bash', str(manifest['script']), 'resume-pending', task_id],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert 'pending job is not terminal' in result.stderr
    assert 'job_e9edbc409b48' in result.stderr
    assert not Path(str(manifest['command_log'])).exists()


def test_resume_pending_terminal_job_uses_resume_label_without_duplicate_ask(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    task_id = 'phase6b-l1-doc-direct-execution'
    loop_id = 'lp1b2b3a'
    target = f'loop-{loop_id}-code_reviewer-1'
    pending_path = project / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.pending.json'
    stage_path = project / '.ccb' / 'runtime' / 'loops' / loop_id / 'ask_first_stage_state.json'
    runner._write_json(
        pending_path,
        {
            'loop_run_status': 'pending',
            'loop_id': loop_id,
            'task_id': task_id,
            'pending': {
                'stage': 'reviewer_ask',
                'target': target,
                'job_id': 'job_e9edbc409b48',
                'job_status': 'running',
            },
        },
    )
    runner._write_json(
        stage_path,
        {
            'status': 'pending',
            'loop_id': loop_id,
            'task_id': task_id,
            'pending': {
                'stage': 'reviewer_ask',
                'target': target,
                'job_id': 'job_e9edbc409b48',
                'job_status': 'running',
            },
        },
    )
    jobs_path = project / '.ccb' / 'agents' / target / 'jobs.jsonl'
    jobs_path.parent.mkdir(parents=True, exist_ok=True)
    jobs_path.write_text(
        '\n'.join(
            [
                json.dumps({'job_id': 'job_e9edbc409b48', 'status': 'running'}),
                json.dumps({'job_id': 'job_e9edbc409b48', 'status': 'completed'}),
            ]
        )
        + '\n',
        encoding='utf-8',
    )
    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        if label_suffix == f'{task_id}__resume_pending_round':
            pending_path.unlink()
            stage_path.unlink()
            runner._write_json(
                project / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.json',
                {'task_id': task_id, 'loop_id': loop_id, 'round_result': 'pass'},
            )
        elif label_suffix == f'{task_id}__task_show_after_resume':
            _label, stdout_path, _stderr_path = runner.command_output_paths(
                observed_manifest,
                label_suffix,
            )
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text(json.dumps({'task': {'task_id': task_id, 'status': 'done'}}), encoding='utf-8')

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.resume_pending_round(manifest, task_id)

    assert calls == [
        (
            f'{task_id}__resume_pending_round',
            [str(PROJECT_ROOT / 'ccb_test'), '--project', str(project), 'loop', 'runner', '--once', '--json'],
        ),
        (
            f'{task_id}__task_show_after_resume',
            [
                str(PROJECT_ROOT / 'ccb_test'),
                '--project',
                str(project),
                'plan',
                'task-show',
                '--task',
                task_id,
                '--json',
            ],
        ),
    ]
    assert all(not label.endswith('__run_direct_execution_round') for label, _argv in calls)


def test_start_task_observes_existing_running_task_without_mutating_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l1-doc-direct-execution'
    calls = []

    monkeypatch.setattr(runner, 'assert_planner_task_set_present', lambda _manifest: {})
    monkeypatch.setattr(runner, 'validate_sequence_task_set_only', lambda _manifest: None)
    monkeypatch.setattr(runner, 'wait_for_planner_task_set_handoff', lambda _manifest, *, before: {})
    monkeypatch.setattr(runner, 'wait_for_auto_runner_quiet', lambda _manifest, *, before: None)
    monkeypatch.setattr(runner, 'task_record_exists', lambda _manifest, _task_id: True)

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        assert label_suffix == f'{task_id}__task_observe_existing'
        _label, stdout_path, _stderr_path = runner.command_output_paths(
            observed_manifest,
            label_suffix,
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(
            json.dumps(
                {
                    'status': 'running',
                    'current_loop': 'lp-sequence21',
                    'task': {
                        'task_id': task_id,
                        'status': 'running',
                        'current_loop': 'lp-sequence21',
                        'artifacts': {
                            'task_packet': {'path': 'task_packet.md'},
                            'execution_contract': {'path': 'execution_contract.md'},
                            'orchestration_notes': {'orchestrator_route': 'direct_execution'},
                        },
                    },
                }
            ),
            encoding='utf-8',
        )

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.start_task(manifest, task_id)

    assert [call[0] for call in calls] == [f'{task_id}__task_observe_existing']
    assert not (Path(str(manifest['project'])) / 'drafts').exists()


def test_start_task_activates_existing_ready_task_without_reimporting_anchors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l2-code-test-direct-execution'
    calls = []

    monkeypatch.setattr(runner, 'assert_planner_task_set_present', lambda _manifest: {})
    monkeypatch.setattr(runner, 'validate_sequence_task_set_only', lambda _manifest: None)
    monkeypatch.setattr(runner, 'wait_for_planner_task_set_handoff', lambda _manifest, *, before: {})
    monkeypatch.setattr(runner, 'wait_for_auto_runner_quiet', lambda _manifest, *, before: None)
    monkeypatch.setattr(runner, 'task_record_exists', lambda _manifest, _task_id: True)

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        if label_suffix.startswith(f'{task_id}__task_observe_existing'):
            _label, stdout_path, _stderr_path = runner.command_output_paths(
                observed_manifest,
                label_suffix,
            )
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text(
                json.dumps(
                    {
                        'task': {
                            'task_id': task_id,
                            'status': 'ready_for_orchestration',
                            'current_loop': None,
                            'artifacts': {
                                'task_packet': {'path': 'task_packet.md'},
                                'execution_contract': {'path': 'execution_contract.md'},
                            },
                        }
                    }
                ),
                encoding='utf-8',
            )
            return
        assert label_suffix == f'{task_id}__activate_orchestrator'
        assert argv[-4:] == ['loop', 'runner', '--once', '--json']

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.start_task(manifest, task_id)

    assert [call[0] for call in calls] == [
        f'{task_id}__task_observe_existing',
        f'{task_id}__task_observe_existing__attempt_1',
        f'{task_id}__activate_orchestrator',
    ]
    assert not any('__artifact_' in call[0] for call in calls)
    assert not any(call[0].endswith('__ready_for_orchestration') for call in calls)


def test_existing_orchestrator_route_allows_continue_without_supervisor_route_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l1-doc-direct-execution'
    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        assert label_suffix == f'{task_id}__route_observe_existing'
        _label, stdout_path, _stderr_path = runner.command_output_paths(
            observed_manifest,
            label_suffix,
        )
        stdout_path.parent.mkdir(parents=True, exist_ok=True)
        stdout_path.write_text(
            json.dumps(
                {
                    'task': {
                        'task_id': task_id,
                        'status': 'running',
                        'artifacts': {
                            'orchestration_notes': {'orchestrator_route': 'direct_execution'}
                        },
                    }
                }
            ),
            encoding='utf-8',
        )

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.import_supervisor_route(manifest, task_id, 'direct_execution')

    assert [call[0] for call in calls] == [f'{task_id}__route_observe_existing']
    assert not (Path(str(manifest['project'])) / 'supervisor_imports' / task_id / 'route.txt').exists()


def test_existing_detail_artifacts_allow_detail_ready_without_supervisor_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    task_id = 'phase6b-l3-needs-detail'
    calls = []

    def fake_run_logged(observed_manifest, label_suffix, argv):
        calls.append((label_suffix, argv))
        if label_suffix == f'{task_id}__detail_observe_existing':
            _label, stdout_path, _stderr_path = runner.command_output_paths(
                observed_manifest,
                label_suffix,
            )
            stdout_path.parent.mkdir(parents=True, exist_ok=True)
            stdout_path.write_text(
                json.dumps(
                    {
                        'task': {
                            'task_id': task_id,
                            'status': 'ready_for_orchestration',
                            'artifacts': {
                                'detail_design': {'path': 'details/task-detail-design.md'},
                                'detail_summary': {'path': 'details/brief-update-summary.md'},
                                'detail_packet': {'path': 'details/detail-packet.manifest.json'},
                            },
                        }
                    }
                ),
                encoding='utf-8',
            )
            return
        assert label_suffix == f'{task_id}__status_detail_ready'
        assert argv[-5:] == [
            '--status',
            'detail_ready',
            '--activation-reason',
            f"{manifest['label']}_detail_ready",
            '--json',
        ]

    monkeypatch.setattr(runner, 'run_logged', fake_run_logged)

    runner.continue_detail(manifest, task_id)

    assert [call[0] for call in calls] == [
        f'{task_id}__detail_observe_existing',
        f'{task_id}__status_detail_ready',
    ]
    assert not (Path(str(manifest['project'])) / 'supervisor_imports' / task_id).exists()


def test_unexpected_frontdesk_meta_task_writes_invalid_harness_report(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    runner.materialize_plan_root(manifest)
    meta_task_id = 'controller-owned-real-provider-l1-l4-rou-20260707063849'
    runner._write_json(
        project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG / 'tasks' / 'index.json',
        {
            'schema': 'ccb.plan.tasks.v1',
            'tasks': [
                {
                    'task_id': meta_task_id,
                    'status': 'blocked',
                    'next_owner': 'terminal',
                    'authority_trace': {
                        'source_job': {
                            'job_id': 'job_31e0de7cb0fd',
                            'agent_name': 'planner',
                            'terminal_status': 'completed',
                        }
                    },
                }
            ],
        },
    )
    activation_path = (
        project / '.ccb' / 'runtime' / 'loops' / 'activations' / 'act-frontdesk-job_ef437696100b.json'
    )
    runner._write_json(
        activation_path,
        {
            'record_type': 'ccb_loop_frontdesk_planner_activation',
            'request_id': 'job_ef437696100b',
            'source_job': {'job_id': 'job_ef437696100b'},
            'ask': {'target': 'planner', 'job_id': 'job_31e0de7cb0fd'},
            'auto_runner': {'wait_job_id': 'job_31e0de7cb0fd'},
        },
    )
    planner_snapshot_path = project / '.ccb' / 'ccbd' / 'snapshots' / 'job_31e0de7cb0fd.json'
    runner._write_json(
        planner_snapshot_path,
        {'job_id': 'job_31e0de7cb0fd', 'agent_name': 'planner', 'record_type': 'completion_snapshot'},
    )
    planner_reply_path = (
        project
        / '.ccb'
        / 'ccbd'
        / 'artifacts'
        / 'text'
        / 'completion-reply'
        / 'job_31e0de7cb0fd-art_test.txt'
    )
    planner_reply_path.parent.mkdir(parents=True, exist_ok=True)
    planner_reply_path.write_text(
        '**task-set.json**\n```json\n{"tasks":[{"task_id":"phase6b-l1-doc-direct-execution"}]}\n```\n',
        encoding='utf-8',
    )

    with pytest.raises(
        runner.HarnessError,
        match='invalid_harness.*frontdesk_planner_unexpected_meta_task',
    ):
        runner.validate_sequence_task_set_only(manifest)

    rows_path = Path(str(manifest['rows']))
    b7_path = Path(str(manifest['b7']))
    rows = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines()]

    assert len(rows) == 1
    row = rows[0]
    assert row['case_id'] == 'frontdesk_planner_unexpected_meta_task'
    assert row['classification'] == 'invalid_harness'
    assert row['reason'] == 'frontdesk_planner_unexpected_meta_task'
    assert row['claimable_row'] is False
    assert row['route_mix_rows_claimable'] is False
    assert row['unexpected_plan_tasks'] == [meta_task_id]
    assert row['frontdesk_job_id'] == 'job_ef437696100b'
    assert row['planner_job_id'] == 'job_31e0de7cb0fd'
    assert row['activation_path'] == str(activation_path)
    assert row['planner_snapshot_path'] == str(planner_snapshot_path)
    assert row['planner_reply_path'] == str(planner_reply_path)
    assert row['fenced_task_set_present'] is True
    assert 'route-mix rows were never generated' in row['why_no_route_mix_rows_claimable']
    assert 'Status: invalid_harness' in b7_path.read_text(encoding='utf-8')


def _write_frontdesk_task_set_parent_authority(
    runner,
    manifest: dict[str, object],
    *,
    mutation: str | None = None,
    non_ascii: bool = False,
) -> str:
    project = Path(str(manifest['project']))
    source_task_id = 'job_a7545d776a18'
    activation_id = f'act-frontdesk-{source_task_id}'
    planner_job_id = 'job_836626329bb8'
    task_set_id = 'ts-709156b264e3b0bcfe49'
    project_id = 'project-root10-sanitized'
    body = f'CCB_REQ_ID: {source_task_id}\nSanitized root10 route mix intake'
    if non_ascii:
        body += '\n中文请求：保持任务身份。'
    body += '\n'
    body_bytes = len(body.encode('utf-8'))
    body_sha256 = hashlib.sha256(body.encode('utf-8')).hexdigest()
    planner_reply = '**task-set.json**\n```json\n{"tasks": []}\n```\n'
    planner_reply_sha256 = hashlib.sha256(planner_reply.encode('utf-8')).hexdigest()
    required_children = [str(case['task_id']) for case in runner.TASKS]
    parent_binding = {
        'schema': 'ccb.plan.task_set_binding.v1',
        'task_set_id': task_set_id,
        'task_set_revision': 1,
        'binding_role': 'parent',
        'bound_task_revision': 1,
    }
    parent = {
        'task_id': source_task_id,
        'task_revision': 1,
        'status': 'decomposed',
        'task_set_parent': parent_binding,
    }
    child_records = []
    task_set_children = []
    import_children = []
    identity_children = []
    for order, task_id in enumerate(required_children):
        binding = {
            'schema': 'ccb.plan.task_set_binding.v1',
            'task_set_id': task_set_id,
            'task_set_revision': 1,
            'binding_role': 'child',
            'bound_task_revision': 1,
            'required': True,
            'order': order,
        }
        child_records.append(
            {
                'task_id': task_id,
                'task_revision': 1,
                'status': 'ready_for_orchestration',
                'task_set': binding,
            }
        )
        task_set_children.append(
            {'task_id': task_id, 'task_revision': 1, 'required': True, 'order': order}
        )
        import_children.append(
            {'task_id': task_id, 'task_revision': 1, 'task_set': dict(binding)}
        )
        identity_children.append(
            {
                'task_id': task_id,
                'required': True,
                'title': f'任务 {order}' if non_ascii else f'Task {order}',
            }
        )
    source_request = {
        'source_job_id': source_task_id,
        'agent_name': 'frontdesk',
        'project_id': project_id,
        'to_agent': 'planner',
        'from_actor': 'frontdesk',
        'message_type': 'ask',
        'bytes': body_bytes,
        'sha256': body_sha256,
        'preview': '中文预览' if non_ascii else None,
        'body_artifact': None,
    }
    activation = {
        'schema_version': 1,
        'record_type': 'ccb_loop_frontdesk_planner_activation',
        'activation_id': activation_id,
        'project_id': project_id,
        'project_root': str(project),
        'action': 'activate_planner_from_frontdesk',
        'source': 'frontdesk_direct_silence_ask',
        'status': 'planner_submitted',
        'plan_slug': runner.PLAN_SLUG,
        'request_id': source_task_id,
        'intake_sha256': body_sha256,
        'source_intake': {
            'sha256': body_sha256,
            'bytes': body_bytes,
            'preview': body.strip()[:400],
        },
        'planner_contract': 'task_set',
        'required_next_output': 'reply-only task-set.json with exact bounded task IDs',
        'script_write_rules': ['Reply only.', 'Use exact task IDs.'],
        'expected_task_ids': required_children,
        'source_task_id': source_task_id,
        'source_job': {
            'job_id': source_task_id,
            'agent_name': 'frontdesk',
            'terminal_status': 'forwarded',
            'finished_at': None,
            'reply_sha256': body_sha256,
        },
        'source_request': source_request,
        'direct_ask': {
            'from_actor': 'frontdesk',
            'target': 'planner',
            'silence': True,
            'task_id': activation_id,
            'body_sha256': body_sha256,
            'controller_rewrote_body': False,
        },
        'ask': {
            'target': 'planner',
            'job_id': planner_job_id,
            'sender': 'frontdesk',
            'silence': True,
            'status': 'accepted',
        },
    }
    task_set = {
        'schema': 'ccb.plan.task_set.v1',
        'schema_version': 1,
        'task_set_id': task_set_id,
        'task_set_revision': 1,
        'project_id': project_id,
        'plan_slug': runner.PLAN_SLUG,
        'source_task_id': source_task_id,
        'source_request': {
            'source_job_id': source_task_id,
            'sha256': body_sha256,
            'bytes': body_bytes,
        },
        'planner_job': {'job_id': planner_job_id, 'reply_sha256': planner_reply_sha256},
        'plan_revision': {
            'schema': 'ccb.plan.revision.v1',
            'digest': 'sha256:' + '1' * 64,
            'files': [],
        },
        'children': task_set_children,
        'ordered_required_children': required_children,
        'state': 'running',
        'aggregate_result': None,
        'closure': None,
        'created_at': '2026-07-12T23:10:49.527255+00:00',
        'updated_at': '2026-07-12T23:10:49.543729+00:00',
    }
    request = {
        'project_id': project_id,
        'to_agent': 'planner',
        'from_actor': 'frontdesk',
        'body': body,
        'task_id': activation_id,
        'message_type': 'ask',
    }
    activation_digest = _frontdesk_activation_digest(activation)
    admission_authority = {
        'project_id': project_id,
        'activation_id': activation_id,
        'request_id': source_task_id,
        'plan_slug': runner.PLAN_SLUG,
        'request': request,
        'body_bytes': body_bytes,
        'body_sha256': body_sha256,
        'planner_contract': 'task_set',
        'source_task_id': source_task_id,
        'activation_digest': activation_digest,
    }
    admission = {
        'schema': 'ccb.frontdesk.direct_handoff_admission_transaction.v1',
        'record_type': 'ccb_frontdesk_direct_handoff_admission_transaction',
        'status': 'committed',
        **admission_authority,
        'transaction_digest': _canonical_digest(admission_authority, prefixed=True),
        'activation_record': dict(activation),
    }
    import_identity = {
        'project_id': project_id,
        'plan_slug': runner.PLAN_SLUG,
        'plan_revision': task_set['plan_revision'],
        'activation_id': activation_id,
        'source_task_id': source_task_id,
        'source_request': source_request,
        'source_job': activation['source_job'],
        'planner_job_id': planner_job_id,
        'planner_reply_sha256': planner_reply_sha256,
        'task_set_id': task_set_id,
        'ordered_children': identity_children,
    }
    import_authority = {
        'task_set_id': task_set_id,
        'task_set_revision': 1,
        'task_set': task_set,
        'source_task_id': source_task_id,
        'children': import_children,
        'task_set_path': str(
            project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG
            / 'task-sets' / task_set_id / 'task-set.json'
        ),
        'tasks': [
            {'task_id': task_id, 'required': True}
            for task_id in required_children
        ],
    }
    planner_import = {
        'schema': 'ccb.plan.planner_task_set_import_transaction.v1',
        'schema_version': 1,
        'status': 'committed',
        'journal_ref': (
            f'.ccb/runtime/role-output-imports/{planner_job_id}/'
            'planner-task-set-import.transaction.json'
        ),
        'transaction_digest': planner_import_transaction_digest(import_identity),
        'identity': import_identity,
        'authority': import_authority,
        'conflicts': [],
    }
    if mutation == 'parent_task_revision':
        parent['task_revision'] = 3
    elif mutation == 'task_set_id':
        parent_binding['task_set_id'] = 'ts-wrong'
    elif mutation == 'revision':
        parent_binding['task_set_revision'] = 2
    elif mutation == 'binding_role':
        parent_binding['binding_role'] = 'child'
    elif mutation == 'status':
        parent['status'] = 'ready_for_orchestration'
    elif mutation == 'source_task_id':
        task_set['source_task_id'] = 'job_other'
    elif mutation == 'planner_contract':
        activation['planner_contract'] = 'legacy_tasks'
    elif mutation == 'to_agent':
        activation['source_request']['to_agent'] = 'orchestrator'
    elif mutation == 'forwarded_flow':
        activation['source_job']['terminal_status'] = 'completed'
    elif mutation == 'admission_schema':
        admission['schema'] = 'ccb.wrong.v1'
    elif mutation == 'admission_status':
        admission['status'] = 'prepared'
    elif mutation == 'admission_activation':
        admission['activation_id'] = 'act-frontdesk-other'
    elif mutation == 'admission_body_digest':
        admission['body_sha256'] = '0' * 64
    elif mutation == 'import_status':
        planner_import['status'] = 'prepared'
    elif mutation == 'import_conflicts':
        planner_import['conflicts'] = [{'reason': 'identity_conflict'}]
    elif mutation == 'import_activation':
        import_identity['activation_id'] = 'act-frontdesk-other'
    elif mutation == 'import_source_task':
        import_identity['source_task_id'] = 'job_other'
    elif mutation == 'import_task_set_id':
        import_identity['task_set_id'] = 'ts-other'
    elif mutation == 'import_revision':
        import_authority['task_set_revision'] = 2
    elif mutation == 'import_reply_digest':
        import_identity['planner_reply_sha256'] = '0' * 64
    elif mutation == 'import_source_digest':
        import_identity['source_request'] = {**source_request, 'sha256': '0' * 64}
    elif mutation == 'task_set_state':
        task_set['state'] = 'closed'
    elif mutation == 'task_set_project':
        task_set['project_id'] = 'other-project'
    elif mutation == 'task_set_plan':
        task_set['plan_slug'] = 'other-plan'
    elif mutation == 'child_revision':
        task_set_children[0]['task_revision'] = 2
    elif mutation == 'child_order':
        task_set_children[0]['order'] = 1
    elif mutation == 'child_binding_revision':
        child_records[0]['task_set']['task_set_revision'] = 2
    elif mutation == 'extra_child':
        task_set_children.append(
            {'task_id': 'extra-child', 'task_revision': 1, 'required': False, 'order': 5}
        )
    runner._write_json(
        project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG / 'tasks' / 'index.json',
        {
            'schema': 'ccb.plan.tasks.v1',
            'tasks': [parent, *child_records, *([dict(parent)] if mutation == 'duplicate_parent' else [])],
        },
    )
    runner._write_json(
        project
        / '.ccb'
        / 'runtime'
        / 'loops'
        / 'activations'
        / f'{activation_id}.json',
        activation,
    )
    if mutation == 'duplicate_activation':
        duplicate = dict(activation)
        duplicate['activation_id'] = f'{activation_id}-duplicate'
        runner._write_json(
            project
            / '.ccb'
            / 'runtime'
            / 'loops'
            / 'activations'
            / f'{activation_id}-duplicate.json',
            duplicate,
        )
    admission_path = (
        project
        / '.ccb'
        / 'runtime'
        / 'loops'
        / 'activations'
        / f'{activation_id}.direct-handoff.transaction.json'
    )
    if mutation == 'bad_admission_json':
        admission_path.parent.mkdir(parents=True, exist_ok=True)
        admission_path.write_text('{', encoding='utf-8')
    else:
        runner._write_json(admission_path, admission)
    runner._write_json(
        project
        / 'docs'
        / 'plantree'
        / 'plans'
        / runner.PLAN_SLUG
        / 'task-sets'
        / task_set_id
        / 'task-set.json',
        task_set,
    )
    reply_path = (
        project
        / '.ccb'
        / 'ccbd'
        / 'artifacts'
        / 'text'
        / 'completion-reply'
        / f'{planner_job_id}-art_root10.txt'
    )
    reply_path.parent.mkdir(parents=True, exist_ok=True)
    reply_path.write_text(planner_reply, encoding='utf-8')
    import_path = (
        project
        / '.ccb'
        / 'runtime'
        / 'role-output-imports'
        / planner_job_id
        / 'planner-task-set-import.transaction.json'
    )
    if mutation == 'bad_import_json':
        import_path.parent.mkdir(parents=True, exist_ok=True)
        import_path.write_text('{', encoding='utf-8')
    else:
        runner._write_json(import_path, planner_import)
    if mutation == 'duplicate_import':
        runner._write_json(
            project
            / '.ccb'
            / 'runtime'
            / 'role-output-imports'
            / 'job_duplicate'
            / 'planner-task-set-import.transaction.json',
            planner_import,
        )
    return source_task_id


def _write_unrelated_history_authority(runner, manifest: dict[str, object]) -> None:
    project = Path(str(manifest['project']))
    current_source = 'job_a7545d776a18'
    current_activation_id = f'act-frontdesk-{current_source}'
    history_source = 'job_history_frontdesk'
    history_activation_id = f'act-frontdesk-{history_source}'
    history_planner = 'job_history_planner'
    history_task_set_id = 'ts-history-complete'
    activation_dir = project / '.ccb' / 'runtime' / 'loops' / 'activations'
    current_activation = json.loads(
        (activation_dir / f'{current_activation_id}.json').read_text(encoding='utf-8')
    )
    activation = copy.deepcopy(current_activation)
    activation.update(
        activation_id=history_activation_id,
        request_id=history_source,
        source_task_id=history_source,
    )
    activation['source_job']['job_id'] = history_source
    activation['source_request']['source_job_id'] = history_source
    activation['direct_ask']['task_id'] = history_activation_id
    activation['ask']['job_id'] = history_planner
    runner._write_json(activation_dir / f'{history_activation_id}.json', activation)

    current_admission = json.loads(
        (
            activation_dir / f'{current_activation_id}.direct-handoff.transaction.json'
        ).read_text(encoding='utf-8')
    )
    admission = copy.deepcopy(current_admission)
    admission.update(
        activation_id=history_activation_id,
        request_id=history_source,
        source_task_id=history_source,
        activation_digest=_frontdesk_activation_digest(activation),
        activation_record=activation,
    )
    admission['request']['task_id'] = history_activation_id
    admission_authority = {
        key: admission[key]
        for key in (
            'project_id', 'activation_id', 'request_id', 'plan_slug', 'request',
            'body_bytes', 'body_sha256', 'planner_contract', 'source_task_id',
            'activation_digest',
        )
    }
    admission['transaction_digest'] = _canonical_digest(admission_authority, prefixed=True)
    runner._write_json(
        activation_dir / f'{history_activation_id}.direct-handoff.transaction.json',
        admission,
    )

    current_task_set = json.loads(
        (
            project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG
            / 'task-sets' / 'ts-709156b264e3b0bcfe49' / 'task-set.json'
        ).read_text(encoding='utf-8')
    )
    task_set = copy.deepcopy(current_task_set)
    task_set.update(task_set_id=history_task_set_id, source_task_id=history_source)
    task_set['source_request']['source_job_id'] = history_source
    task_set['planner_job']['job_id'] = history_planner
    runner._write_json(
        project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG
        / 'task-sets' / history_task_set_id / 'task-set.json',
        task_set,
    )

    current_import = json.loads(
        (
            project / '.ccb' / 'runtime' / 'role-output-imports' / 'job_836626329bb8'
            / 'planner-task-set-import.transaction.json'
        ).read_text(encoding='utf-8')
    )
    planner_import = copy.deepcopy(current_import)
    identity = planner_import['identity']
    identity.update(
        activation_id=history_activation_id,
        source_task_id=history_source,
        planner_job_id=history_planner,
        task_set_id=history_task_set_id,
    )
    identity['source_request']['source_job_id'] = history_source
    identity['source_job']['job_id'] = history_source
    authority = planner_import['authority']
    authority.update(
        task_set_id=history_task_set_id,
        task_set=task_set,
        source_task_id=history_source,
    )
    for child in authority['children']:
        child['task_set']['task_set_id'] = history_task_set_id
    planner_import['journal_ref'] = (
        f'.ccb/runtime/role-output-imports/{history_planner}/'
        'planner-task-set-import.transaction.json'
    )
    planner_import['transaction_digest'] = planner_import_transaction_digest(identity)
    runner._write_json(
        project / planner_import['journal_ref'],
        planner_import,
    )
    current_reply = (
        project / '.ccb' / 'ccbd' / 'artifacts' / 'text' / 'completion-reply'
        / 'job_836626329bb8-art_root10.txt'
    )
    history_reply = current_reply.with_name(f'{history_planner}-art_history.txt')
    history_reply.write_bytes(current_reply.read_bytes())


def test_authoritative_frontdesk_task_set_source_parent_is_not_unexpected(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(runner, manifest)

    assert runner.unexpected_plan_task_ids(manifest) == []
    runner.validate_sequence_task_set_only(manifest)
    assert source_task_id not in runner.unexpected_plan_task_ids(manifest)


def test_root10_schema_frontdesk_task_set_source_parent_is_controlled(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(runner, manifest)

    assert runner.controlled_task_set_source_parent_ids(manifest) == {source_task_id}
    assert runner.unexpected_plan_task_ids(manifest) == []
    runner.validate_sequence_task_set_only(manifest)


def test_non_ascii_planner_import_digest_uses_production_rule(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(
        runner,
        manifest,
        non_ascii=True,
    )

    assert runner.controlled_task_set_source_parent_ids(manifest) == {source_task_id}


def test_unrelated_complete_authority_history_does_not_shadow_current_parent(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(runner, manifest)
    _write_unrelated_history_authority(runner, manifest)

    assert runner.controlled_task_set_source_parent_ids(manifest) == {source_task_id}
    assert runner.unexpected_plan_task_ids(manifest) == []


def test_second_import_matching_current_identity_is_rejected(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(
        runner,
        manifest,
        mutation='duplicate_import',
    )

    assert runner.controlled_task_set_source_parent_ids(manifest) == set()
    assert runner.unexpected_plan_task_ids(manifest) == [source_task_id]


@pytest.mark.parametrize(
    'mutation',
    (
        'parent_task_revision', 'task_set_id', 'revision', 'binding_role', 'status',
        'source_task_id', 'planner_contract', 'to_agent', 'forwarded_flow',
        'admission_schema', 'admission_status', 'admission_activation',
        'admission_body_digest', 'bad_admission_json', 'import_status',
        'import_conflicts', 'import_activation', 'import_source_task',
        'import_task_set_id', 'import_revision', 'import_reply_digest',
        'import_source_digest', 'bad_import_json', 'duplicate_activation',
        'duplicate_parent', 'duplicate_import', 'task_set_state', 'task_set_project',
        'task_set_plan', 'child_revision', 'child_order', 'child_binding_revision',
        'extra_child',
    ),
)
def test_frontdesk_task_set_source_parent_requires_exact_authority(
    tmp_path: Path,
    mutation: str,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    source_task_id = _write_frontdesk_task_set_parent_authority(
        runner,
        manifest,
        mutation=mutation,
    )

    assert runner.unexpected_plan_task_ids(manifest) == [source_task_id]


def test_planner_route_equivalent_task_ids_are_aliases_not_meta_tasks(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    runner.materialize_plan_root(manifest)
    records = []
    for task_id, route in (
        ('phase6b-l1-doc-direct-execution', 'direct_execution'),
        ('phase6b-l2-code-test-direct-execution', 'direct_execution'),
        ('phase6b-l3-needs-detail-detail-ready', 'needs_detail'),
        ('phase6b-l4-macro-adjustment-replan-required', 'macro_adjustment_request'),
        ('phase6b-l4-blocked-prerequisite', 'blocked'),
    ):
        task_root = project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG / 'tasks' / task_id
        task_root.mkdir(parents=True, exist_ok=True)
        (task_root / 'task_packet.md').write_text(f'# Task\nRoute: {route}\n', encoding='utf-8')
        records.append(
            {
                'task_id': task_id,
                'status': 'ready_for_orchestration',
                'next_owner': 'orchestrator',
                'task_root': str(task_root.relative_to(project)),
                'artifacts': {
                    'task_packet': {
                        'path': str((task_root / 'task_packet.md').relative_to(project)),
                    }
                },
            }
        )
    runner._write_json(
        project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG / 'tasks' / 'index.json',
        {'schema': 'ccb.plan.tasks.v1', 'tasks': records},
    )

    assert runner.sequence_task_aliases(manifest) == {
        'phase6b-l3-needs-detail': 'phase6b-l3-needs-detail-detail-ready',
        'phase6b-l4-macro-adjustment-request': 'phase6b-l4-macro-adjustment-replan-required',
    }
    assert runner.unexpected_plan_task_ids(manifest) == []
    runner.validate_sequence_task_set_only(manifest)


def test_missing_fenced_task_set_blocks_with_explicit_row(tmp_path: Path) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    project = Path(str(manifest['project']))
    runner.materialize_plan_root(manifest)
    planner_reply_path = (
        project
        / '.ccb'
        / 'ccbd'
        / 'artifacts'
        / 'text'
        / 'completion-reply'
        / 'job_31e0de7cb0fd-art_test.txt'
    )
    planner_reply_path.parent.mkdir(parents=True, exist_ok=True)
    planner_reply_path.write_text(
        '**task-packet.md**\n```markdown\n# Task\nroute: direct_execution\n```\n',
        encoding='utf-8',
    )
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'activations' / 'act-frontdesk-job_ef437696100b.json',
        {
            'record_type': 'ccb_loop_frontdesk_planner_activation',
            'request_id': 'job_ef437696100b',
            'source_job': {'job_id': 'job_ef437696100b'},
            'ask': {'target': 'planner', 'job_id': 'job_31e0de7cb0fd'},
            'auto_runner': {'wait_job_id': 'job_31e0de7cb0fd'},
        },
    )
    runner._write_json(
        project / '.ccb' / 'ccbd' / 'snapshots' / 'job_31e0de7cb0fd.json',
        {'job_id': 'job_31e0de7cb0fd', 'agent_name': 'planner', 'record_type': 'completion_snapshot'},
    )

    with pytest.raises(
        runner.HarnessBlocker,
        match='invalid_harness.*frontdesk_planner_missing_fenced_task_set',
    ):
        runner.assert_planner_task_set_present(manifest)

    rows_path = Path(str(manifest['rows']))
    row = json.loads(rows_path.read_text(encoding='utf-8').strip())
    assert row['case_id'] == 'frontdesk_planner_missing_fenced_task_set'
    assert row['classification'] == 'invalid_harness'
    assert row['planner_reply_path'] == str(planner_reply_path)
    assert row['fenced_task_set_present'] is False
    assert 'fenced task-set.json block' in row['why_no_route_mix_rows_claimable']


def _write_root14_b7_authority(runner, manifest: dict[str, object]) -> dict[str, Path]:
    source_task_id = _write_frontdesk_task_set_parent_authority(runner, manifest)
    project = Path(str(manifest['project']))
    plan_root = project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG
    tasks_path = plan_root / 'tasks' / 'index.json'
    records = json.loads(tasks_path.read_text(encoding='utf-8'))['tasks']
    parent = next(record for record in records if record['task_id'] == source_task_id)
    children = [
        next(record for record in records if record['task_id'] == case['task_id'])
        for case in runner.TASKS
    ]
    task_set_id = parent['task_set_parent']['task_set_id']
    revision = parent['task_set_parent']['task_set_revision']
    task_set_path = plan_root / 'task-sets' / task_set_id / 'task-set.json'
    task_set = json.loads(task_set_path.read_text(encoding='utf-8'))
    planner_feedback_digest = 'sha256:' + '2' * 64
    constraint = {
        'schema_version': 1,
        'status': 'detail_ready',
        'basis': 'verified_detail_ready_stop_contract',
        'task_id': runner.TASKS[2]['task_id'],
        'task_revision': 3,
        'state_version': 13,
        'authority_digest': '3' * 64,
        'basis_digest': '4' * 64,
        'required_reason': 'detail_ready_task',
    }

    terminal_revisions = (2, 2, 3, 2, 2)
    for index, (case, record, terminal_revision) in enumerate(
        zip(runner.TASKS, children, terminal_revisions),
        start=1,
    ):
        task_id = case['task_id']
        task_dir = plan_root / 'tasks' / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        notes_path = task_dir / 'orchestration_notes.md'
        notes_path.write_text(f"route: {case['expected_route']}\n", encoding='utf-8')
        artifacts = {
            'orchestration_notes': {
                'path': str(notes_path.relative_to(project)),
                'orchestrator_route': case['expected_route'],
                'actor': {'source': 'loop_runner_role_output_import'},
            }
        }
        if case['expected_route'] == 'direct_execution':
            loop_id = f'lp-root14-{index}'
            runner._write_json(
                project / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.json',
                {
                    'task_id': task_id,
                    'loop_id': loop_id,
                    'round_result': 'pass',
                    'round_result_source': 'round_reviewer_reply',
                    'release': {'released_count': 2, 'retained_count': 0},
                    'observed_topology': {'agents': []},
                },
            )
            summary = task_dir / 'round_summary.md'
            summary.write_text('round_result: pass\nround_result_source: round_reviewer_reply\n', encoding='utf-8')
            artifacts['round_summary'] = {
                'path': str(summary.relative_to(project)),
                'actor': {'source': 'loop_runner'},
                'loop_id': loop_id,
                'round_result': 'pass',
            }
        elif case['expected_route'] == 'needs_detail':
            detail = task_dir / 'details' / 'detail-packet.manifest.json'
            detail.parent.mkdir(parents=True, exist_ok=True)
            detail.write_text('{}\n', encoding='utf-8')
            artifacts['detail_packet'] = {
                'path': str(detail.relative_to(project)),
                'actor': {'source': 'loop_runner_role_output_import'},
            }
        elif case['expected_route'] == 'macro_adjustment_request':
            macro = task_dir / 'details' / 'macro-adjustment-request.json'
            macro.parent.mkdir(parents=True, exist_ok=True)
            macro.write_text('{}\n', encoding='utf-8')
            artifacts['macro_adjustment_request'] = {
                'path': str(macro.relative_to(project)),
                'actor': {'source': 'loop_runner/script-owned'},
            }
        else:
            blocker = task_dir / 'blocker-evidence.md'
            blocker.write_text('blocked\n', encoding='utf-8')
            artifacts['blocker_evidence'] = {
                'path': str(blocker.relative_to(project)),
                'actor': {'source': 'loop_runner/script-owned'},
            }
        record.update(
            task_revision=terminal_revision,
            state_version=constraint['state_version'] if task_id == constraint['task_id'] else 9,
            status=case['expected_final_status'],
            next_owner='terminal' if case['expected_final_status'] in {'done', 'blocked'} else 'planner',
            artifacts=artifacts,
        )

    ordered_children = []
    for record in children:
        status = record['status']
        result = {'done': 'pass', 'detail_ready': 'pass', 'replan_required': 'replan_required', 'blocked': 'blocked'}[status]
        authority = {'artifact_kind': 'terminal', 'release': {'status': 'not_applicable_no_execution'}, 'cleanup': {'status': 'not_applicable_no_execution'}}
        if status == 'detail_ready':
            authority = {
                'artifact_kind': 'detail_ready_stop_contract',
                'authority_digest': constraint['authority_digest'],
                'basis_digest': constraint['basis_digest'],
                'release': {'status': 'not_applicable_no_execution'},
                'cleanup': {'status': 'not_applicable_no_execution'},
            }
        ordered_children.append(
            {
                'task_id': record['task_id'],
                'task_revision': record['task_revision'],
                'required': True,
                'status': status,
                'result': result,
                'authority': authority,
                'evidence_status': 'terminal',
                'evidence_digest': runner._authority_digest(
                    {
                        'task_id': record['task_id'],
                        'task_revision': record['task_revision'],
                        **authority,
                    }
                ),
            }
        )
    evidence_digest = runner._authority_digest({'task_set_revision': revision, 'children': ordered_children})
    closure = {
        'schema': 'ccb.plan.task_set_closure.v1',
        'schema_version': 1,
        'task_set_id': task_set_id,
        'task_set_revision': revision,
        'source_request': task_set['source_request'],
        'planner_job': task_set['planner_job'],
        'expected_plan_revision': task_set['plan_revision']['digest'],
        'ordered_children': ordered_children,
        'ordered_terminal_evidence_digest': evidence_digest,
        'status': 'closure_pending',
        'aggregate_result': 'replan_required',
        'reason': 'one_or_more_required_children_require_replan',
        'created_at': '2026-07-13T00:00:01+00:00',
    }
    closure['closure_digest'] = runner._authority_digest(closure)
    closure_path = task_set_path.with_name('closure.json')
    runner._write_json(closure_path, closure)
    task_set.update(
        state='replan_required',
        aggregate_result='replan_required',
        closure={
            'path': str(closure_path.relative_to(project)),
            'closure_digest': closure['closure_digest'],
            'ordered_terminal_evidence_digest': evidence_digest,
        },
    )

    intent = {
        'schema': 'ccb.plan.task_set_closure_intent.v1',
        'schema_version': 1,
        'intent_id': 'tsi-root14-closure',
        'task_set_id': task_set_id,
        'task_set_revision': revision,
        'ordered_terminal_evidence_digest': evidence_digest,
        'closure_digest': closure['closure_digest'],
        'status': 'feedback_closed',
        'created_at': '2026-07-13T00:00:02+00:00',
        'feedback_closed_at': '2026-07-13T00:00:04+00:00',
    }
    runtime_path = project / '.ccb' / 'runtime' / 'task-sets' / task_set_id / f'feedback-r{revision}.json'
    backfill_path = task_set_path.with_name(f'planner-backfill-r{revision}.json')
    transport = {
        'runtime_state_path': str(runtime_path),
        'planner_job_id': 'job_root14_backfill',
        'frontdesk_job_id': 'job_root14_frontdesk_status',
        'planner_backfill_path': str(backfill_path),
        'planner_feedback_digest': planner_feedback_digest,
        'notification_status': 'delivered',
        'backfill_digest': None,
    }
    backfill = {
        'schema': 'ccb.plan.planner_backfill.v2',
        'schema_version': 2,
        'authority': {
            'task_set_id': task_set_id,
            'task_set_revision': revision,
            'closure_intent_id': intent['intent_id'],
            'closure_digest': closure['closure_digest'],
            'ordered_terminal_evidence_digest': evidence_digest,
            'expected_plan_revision': task_set['plan_revision']['digest'],
            'planner_job_id': transport['planner_job_id'],
            'planner_source_job_id': transport['planner_job_id'],
            'planner_effective_job_id': transport['planner_job_id'],
            'planner_retry_lineage': [],
            'planner_feedback_digest': planner_feedback_digest,
            'plan_slug': runner.PLAN_SLUG,
        },
        'proposal': {'frontdesk_notification_required': True},
        'transaction_digest': 'sha256:' + '5' * 64,
        'target_plan_revision': 'sha256:' + '6' * 64,
        'transaction_path': str(backfill_path.with_name(f'planner-backfill-r{revision}.transaction.json').relative_to(project)),
    }
    backfill['backfill_digest'] = runner._authority_digest(backfill)
    transport['backfill_digest'] = backfill['backfill_digest']
    intent['transport_ref'] = transport
    planner_message = 'root14 planner backfill transport'
    frontdesk_message = 'root14 frontdesk completion transport'
    backfill_import = {
        **backfill['authority'],
        'status': 'imported',
        'idempotent': False,
        'planner_backfill_path': str(backfill_path),
        'transaction_path': backfill['transaction_path'],
        'target_plan_revision': backfill['target_plan_revision'],
        'backfill_digest': backfill['backfill_digest'],
    }
    runner._write_json(
        runtime_path,
        {
            'schema': 'ccb.plan.task_set_feedback_runtime.v1',
            'schema_version': 1,
            'task_set_id': task_set_id,
            'task_set_revision': revision,
            'closure_intent_id': intent['intent_id'],
            'closure_digest': closure['closure_digest'],
            'terminal_evidence_digest': evidence_digest,
            'stage': 'closed',
            'planner': {
                'target': 'planner', 'purpose': 'planner_backfill',
                'task_id': f"task-set-feedback-{intent['intent_id']}",
                'message': planner_message,
                'message_sha256': hashlib.sha256(planner_message.encode('utf-8')).hexdigest(),
                'silent': True,
                'job_id': transport['planner_job_id'],
                'source_job_id': transport['planner_job_id'],
                'effective_job_id': transport['planner_job_id'],
                'retry_lineage': [],
                'status': 'completed',
                'reply': 'planner backfill completed',
            },
            'frontdesk': {
                'target': 'frontdesk', 'purpose': 'frontdesk_status',
                'task_id': f"task-set-status-{intent['intent_id']}",
                'message': frontdesk_message,
                'message_sha256': hashlib.sha256(frontdesk_message.encode('utf-8')).hexdigest(),
                'silent': False,
                'job_id': transport['frontdesk_job_id'],
                'source_job_id': transport['frontdesk_job_id'],
                'effective_job_id': transport['frontdesk_job_id'],
                'retry_lineage': [],
                'status': 'completed',
                'reply': 'frontdesk completion delivered',
            },
            'backfill_import': backfill_import,
            'notification': {'status': 'delivered', 'job_id': transport['frontdesk_job_id']},
            'runtime_digest': None,
        },
    )
    runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
    runtime['runtime_digest'] = runner._authority_digest(runtime, omit='runtime_digest')
    runner._write_json(runtime_path, runtime)
    runner._write_json(backfill_path, backfill)
    runner._write_json(
        task_set_path.with_name(f'closure-settlement-r{revision}.json'),
        {
            'schema': 'ccb.plan.task_set_closure_settlement.v2',
            'schema_version': 2,
            'task_set_id': task_set_id,
            'task_set_revision': revision,
            'intent_id': intent['intent_id'],
            'aggregate_result': 'replan_required',
            'closure_digest': closure['closure_digest'],
            'ordered_terminal_evidence_digest': evidence_digest,
            'transport_ref': transport,
            'settlement_digest': None,
        },
    )
    settlement_path = task_set_path.with_name(f'closure-settlement-r{revision}.json')
    settlement = json.loads(settlement_path.read_text(encoding='utf-8'))
    settlement['settlement_digest'] = runner._authority_digest(settlement, omit='settlement_digest')
    runner._write_json(settlement_path, settlement)
    runner._write_json(runtime_path.with_name('closure-intents.json'), {
        'schema': 'ccb.plan.task_set_closure_intent_store.v1',
        'schema_version': 1,
        'task_set_id': task_set_id,
        'intents': [intent],
    })
    parent.update(
        status='replan_required',
        next_owner='planner',
        task_set_closure={
            'schema': 'ccb.plan.task_set_parent_settlement.v1',
            'task_set_id': task_set_id,
            'task_set_revision': revision,
            'aggregate_result': 'replan_required',
            'closure_digest': closure['closure_digest'],
            'planner_feedback_digest': planner_feedback_digest,
        },
    )
    runner._write_json(tasks_path, {'schema': 'ccb.plan.tasks.v1', 'tasks': records})
    runner._write_json(task_set_path, task_set)
    activation_path = project / '.ccb' / 'runtime' / 'loops' / 'activations' / 'act-root14-l3-terminal.json'
    runner._write_json(activation_path, {
        'schema_version': 1,
        'record_type': 'ccb_loop_planner_activation',
        'activation_id': 'act-root14-l3-terminal',
        'task_id': constraint['task_id'],
        'task_revision': constraint['task_revision'],
        'task_status': 'detail_ready',
        'terminal_status_constraint': constraint,
        'ask': {'target': 'planner', 'job_id': 'job_root14_l3_terminal'},
    })
    import_path = project / '.ccb' / 'runtime' / 'role-output-imports.jsonl'
    import_path.parent.mkdir(parents=True, exist_ok=True)
    import_path.write_text(json.dumps({
        'schema_version': 1,
        'record_type': 'ccb_loop_role_output_import',
        'imported_at': '2026-07-13T00:00:03+00:00',
        'action': 'settled_planner_terminal_status_constraint',
        'status': 'ok',
        'task_id': constraint['task_id'],
        'task_status': 'detail_ready',
        'terminal_status_constraint': constraint,
        'source_job': {'job_id': 'job_root14_l3_terminal'},
    }) + '\n', encoding='utf-8')
    return {
        'tasks': tasks_path,
        'task_set': task_set_path,
        'closure': closure_path,
        'runtime': runtime_path,
        'backfill': backfill_path,
        'settlement': settlement_path,
        'activation': activation_path,
        'imports': import_path,
    }


def _write_production_generated_b7_authority(
    runner,
    manifest: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
    from cli.services.ask_runtime import AskSummary
    from cli.services.plan_tasks import plan_task
    from cli.services.task_set_closure import create_task_set_authority, evaluate_task_set_closure
    from cli.services.task_set_feedback_runtime import advance_task_set_feedback_runtime
    from jobs.store import JobStore
    from storage.paths import PathLayout
    from types import SimpleNamespace
    import cli.services.task_set_closure as task_set_closure

    project = Path(str(manifest['project']))
    plan_root = project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG
    plan_root.mkdir(parents=True, exist_ok=True)
    (plan_root / 'README.md').write_text('# Production-generated B7 authority\n', encoding='utf-8')
    context = SimpleNamespace(
        project=SimpleNamespace(project_root=project, project_id='production-generated-b7'),
        paths=None,
    )
    source_task_id = 'root14-production-source'
    task_ids = [case['task_id'] for case in runner.TASKS]

    def write(path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def create_task(task_id: str, *, route: str | None, ready: bool) -> None:
        created = plan_task(
            context,
            SimpleNamespace(
                action='task-create', plan_slug=runner.PLAN_SLUG,
                title=task_id, task_id=task_id,
            ),
        )
        revision = created['task']['task_revision']
        if not ready:
            return
        for kind in ('task_packet', 'execution_contract'):
            path = project / 'drafts' / task_id / f'{kind}.md'
            write(path, f'# {kind}\nRoute: {route}\n')
            imported = plan_task(
                context,
                SimpleNamespace(
                    action='task-artifact', task_id=task_id, artifact_kind=kind,
                    file_path=str(path), actor_source='loop_runner_role_output_import',
                    actor='loop_runner', job_id='job-production-planner',
                    expected_task_revision=revision,
                ),
            )
            revision = imported['task']['task_revision']
        notes = project / 'drafts' / task_id / 'orchestration_notes.md'
        write(notes, f'route: {route}\n')
        imported = plan_task(
            context,
            SimpleNamespace(
                action='task-artifact', task_id=task_id,
                artifact_kind='orchestration_notes', file_path=str(notes), route=route,
                actor_source='loop_runner_role_output_import', actor='loop_runner',
                job_id='job-production-orchestrator', expected_task_revision=revision,
            ),
        )
        plan_task(
            context,
            SimpleNamespace(
                action='task-status', task_id=task_id, status='ready_for_orchestration',
                next_owner='orchestrator', expected_task_revision=imported['task']['task_revision'],
            ),
        )

    def complete_round(task_id: str, result: str) -> None:
        shown = plan_task(context, SimpleNamespace(action='task-show', task_id=task_id))['task']
        loop_id = f'production-{task_id}'
        plan_task(
            context,
            SimpleNamespace(
                action='task-bind-loop', task_id=task_id, loop_id=loop_id,
                expected_task_revision=shown['task_revision'],
            ),
        )
        summary = project / 'rounds' / f'{task_id}.md'
        write(summary, f'round_result: {result}\n')
        plan_task(
            context,
            SimpleNamespace(
                action='task-import-round', task_id=task_id, loop_id=loop_id,
                result=result, file_path=str(summary),
                actor_source='loop_runner_role_output_import', actor='loop_runner',
                job_id='job-production-round', expected_task_revision=shown['task_revision'],
            ),
        )
        runner._write_json(
            project / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.json',
                {
                    'task_id': task_id, 'loop_id': loop_id, 'round_result': result,
                    'round_result_source': 'round_reviewer_reply',
                    'release': {
                        'loop_topology_status': 'released', 'released_count': 2,
                        'retained_count': 0, 'release_incomplete_count': 0,
                    },
                'observed_topology': {'agents': []},
            },
        )

    create_task(source_task_id, route=None, ready=False)
    for case in runner.TASKS:
        create_task(str(case['task_id']), route=str(case['expected_route']), ready=True)
    created = create_task_set_authority(
        context,
        plan_slug=runner.PLAN_SLUG,
        source_task_id=source_task_id,
        source_request={
            'source_job_id': 'job-production-frontdesk',
            'sha256': hashlib.sha256(b'production generated request').hexdigest(),
            'bytes': len(b'production generated request'),
        },
        planner_job={
            'job_id': 'job-production-planner',
            'reply_sha256': hashlib.sha256(b'production generated task set').hexdigest(),
        },
        children=[{'task_id': task_id, 'required': True} for task_id in task_ids],
        plan_task_fn=plan_task,
    )
    task_set_id = str(created['task_set']['task_set_id'])
    complete_round(task_ids[0], 'pass')
    complete_round(task_ids[1], 'pass')
    complete_round(task_ids[3], 'replan_required')
    complete_round(task_ids[4], 'blocked')

    l3_id = task_ids[2]
    l3 = plan_task(context, SimpleNamespace(action='task-show', task_id=l3_id))['task']
    for kind in ('detail_design', 'detail_summary', 'detail_packet'):
        path = project / '.ccb' / 'runtime' / 'role-output-imports' / 'job-production-detailer' / f'{kind}.md'
        write(path, f'# {kind}\n')
        plan_task(
            context,
            SimpleNamespace(
                action='task-artifact', task_id=l3_id, artifact_kind=kind,
                file_path=str(path), actor_source='loop_runner_role_output_import',
                actor='loop_runner', job_id='job-production-detailer',
                expected_task_revision=l3['task_revision'],
            ),
        )
    plan_task(
        context,
        SimpleNamespace(
            action='task-status', task_id=l3_id, status='detail_ready', next_owner='planner',
            expected_task_revision=l3['task_revision'],
        ),
    )
    original_detail_authority = task_set_closure.detail_ready_stop_contract_authority
    monkeypatch.setattr(
        task_set_closure,
        'detail_ready_stop_contract_authority',
        lambda record, *, project_root: (
            {'authority_digest': 'a' * 64, 'basis_digest': 'b' * 64}
            if record.get('task_id') == l3_id
            else original_detail_authority(record, project_root=project_root)
        ),
    )
    closed = evaluate_task_set_closure(
        context, task_set_id=task_set_id, plan_task_fn=plan_task,
    )
    assert closed['status'] == 'closure_pending'
    closure = closed['closure']
    intent = closed['closure_intent']
    task_set = closed['task_set']
    closure_path = project / 'docs' / 'plantree' / 'plans' / runner.PLAN_SLUG / 'task-sets' / task_set_id / 'closure.json'
    evidence_ref = str(closure_path.relative_to(project))
    next_milestone = {'kind': 'selected', 'ref': 'replan', 'rationale': 'Closure requires replan.'}
    frontdesk_status = {
        'schema': 'ccb.planner.frontdesk_status.v1',
        'notification_identity': f'{task_set_id}-r1',
        'aggregate_result': 'replan_required',
        'accepted_scope': ['direct children complete'],
        'unresolved_scope': ['macro replan required'],
        'blockers': [],
        'next_milestone': next_milestone,
        'evidence_refs': [evidence_ref],
        'user_report_body': 'Task-set replan required.',
    }
    planner_reply = '**planner-backfill.json**\n```json\n' + json.dumps(
        {
            'schema': 'ccb.planner.backfill_proposal.v1', 'mode': 'task_set_closure',
            'expected_plan_revision': task_set['plan_revision']['digest'],
            'task_or_task_set_id': task_set_id, 'task_or_task_set_revision': 1,
            'closure_evidence_digest': closure['ordered_terminal_evidence_digest'],
            'aggregate_result': 'replan_required', 'result': 'task_set_replanned',
            'brief_summary': 'Task-set requires replan.', 'roadmap_transitions': [],
            'todo_transitions': [], 'decision_refs': [], 'open_question_refs': [],
            'evidence_refs': [evidence_ref], 'accepted_scope': ['direct children complete'],
            'unresolved_scope': ['macro replan required'], 'blockers': [],
            'replan_inputs': ['macro adjustment request'], 'next_milestone': next_milestone,
            'frontdesk_notification_required': True, 'frontdesk_status': frontdesk_status,
        },
    ) + '\n```'
    replies: dict[str, str] = {}

    def submit_ask(_context, command):
        job_id = f'job-production-{command.target}'
        reply = planner_reply if command.target == 'planner' else 'delivered'
        replies[job_id] = reply
        request = MessageEnvelope(
            project_id=context.project.project_id, to_agent=command.target,
            from_actor='system', body=command.message, task_id=command.task_id,
            reply_to=None, message_type='task', delivery_scope=DeliveryScope.SINGLE,
            silence_on_success=command.silence,
        )
        JobStore(PathLayout(project)).append(
            JobRecord(
                job_id=job_id, submission_id=None, agent_name=command.target,
                provider='fake', request=request, status=JobStatus.COMPLETED,
                terminal_decision={'terminal': True, 'status': 'completed', 'reply': reply},
                cancel_requested_at=None, created_at='2026-07-13T00:00:00Z',
                updated_at='2026-07-13T00:00:01Z', provider_options={},
            )
        )
        return AskSummary(context.project.project_id, None, ({'agent_name': command.target, 'job_id': job_id},))

    services = SimpleNamespace(
        discover_task_set_closures=lambda *_args, **_kwargs: {
            'evaluated': [],
            'pending': [{
                **intent,
                'task_set_path': str(closure_path.with_name('task-set.json')),
            }],
        },
        plan_task=plan_task,
        submit_ask=submit_ask,
        persisted_terminal_watch=lambda _context, job_id: {
            'status': 'completed', 'reply': replies[job_id],
        },
        find_task_set_transport_job=lambda *_args, **_kwargs: None,
        find_task_set_retry_successor=lambda *_args, **_kwargs: None,
    )
    settled = advance_task_set_feedback_runtime(context, services)
    assert settled['action'] == 'task_set_feedback_closed'

    l3_record = plan_task(context, SimpleNamespace(action='task-show', task_id=l3_id))['task']
    constraint = {
        'schema_version': 1, 'status': 'detail_ready',
        'basis': 'verified_detail_ready_stop_contract', 'task_id': l3_id,
        'task_revision': l3_record['task_revision'], 'state_version': l3_record['state_version'],
        'authority_digest': 'a' * 64, 'basis_digest': 'b' * 64,
        'required_reason': 'detail_ready_task',
    }
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'activations' / 'act-production-l3-terminal.json',
        {
            'schema_version': 1, 'record_type': 'ccb_loop_planner_activation',
            'activation_id': 'act-production-l3-terminal', 'task_id': l3_id,
            'task_revision': l3_record['task_revision'], 'task_status': 'detail_ready',
            'terminal_status_constraint': constraint,
            'ask': {'target': 'planner', 'job_id': 'job-production-l3-terminal'},
        },
    )
    imports = project / '.ccb' / 'runtime' / 'role-output-imports.jsonl'
    imports.parent.mkdir(parents=True, exist_ok=True)
    imports.write_text(json.dumps({
        'schema_version': 1, 'record_type': 'ccb_loop_role_output_import',
        'imported_at': '2026-07-13T00:00:02Z',
        'action': 'settled_planner_terminal_status_constraint', 'status': 'ok',
        'task_id': l3_id, 'task_status': 'detail_ready',
        'terminal_status_constraint': constraint,
        'source_job': {'job_id': 'job-production-l3-terminal'},
    }) + '\n', encoding='utf-8')
    runner._write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'activations' / f'act-frontdesk-{source_task_id}.json',
        {
            'record_type': 'ccb_loop_frontdesk_planner_activation',
            'request_id': source_task_id, 'source_job': {'job_id': source_task_id},
            'ask': {'target': 'planner', 'job_id': 'job-production-planner'},
        },
    )
    reply_path = project / '.ccb' / 'ccbd' / 'artifacts' / 'text' / 'completion-reply' / 'job-production-planner-art_crosscheck.txt'
    write(reply_path, '**task-set.json**\n```json\n{}\n```\n')


def test_b7_uses_script_owned_task_index_routes_and_status_results(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    _write_root14_b7_authority(runner, manifest)
    runner.write_b7_report(manifest)

    rows = [
        json.loads(line)
        for line in Path(str(manifest['rows'])).read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]
    assert len(rows) == len(runner.TASKS)
    assert all(row['claimable_row'] for row in rows)
    assert all(row['route_decision_correct'] for row in rows)
    assert all(row['script_owned_route_imports'] for row in rows)
    assert all(row['script_owned_round_imports'] for row in rows)
    assert all(row['provider_reply_authority_parsing_absent'] for row in rows)
    assert all(row['runtime_residue'] is False for row in rows)
    assert all(row['dynamic_unload_ok'] is True for row in rows)
    assert [row['observed_route'] for row in rows] == [case['expected_route'] for case in runner.TASKS]
    assert [row['round_result'] for row in rows] == [case['expected_round_result'] for case in runner.TASKS]
    assert rows[0]['cleanup_result'] == 'clean'
    assert rows[1]['cleanup_result'] == 'clean'
    assert rows[0]['release_released_count'] == 2
    assert rows[0]['release_retained_count'] == 0
    assert rows[2]['cleanup_result'] == 'not_applicable'
    assert all(row['task_set_authority_valid'] for row in rows)
    assert all(row['settlement_action'] == 'settled_planner_terminal_status_constraint' for row in rows)
    assert all(row['auto_runner_state']['status'] == 'absent' for row in rows)
    assert 'Status: pass' in Path(str(manifest['b7'])).read_text(encoding='utf-8')


def test_b7_accepts_production_generated_decision029_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    _write_production_generated_b7_authority(runner, manifest, monkeypatch)

    evidence = runner.b7_task_set_evidence(
        manifest,
        [case['task_id'] for case in runner.TASKS],
    )
    assert evidence['valid'] is True, evidence['errors']
    runner.write_b7_report(manifest)
    assert 'Status: pass' in Path(str(manifest['b7'])).read_text(encoding='utf-8')
    assert all(row['task_set_authority_valid'] for row in _b7_rows(manifest))


def test_b7_distinguishes_bound_child_revision_from_terminal_evidence_revision(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    paths = _write_root14_b7_authority(runner, manifest)
    task_set = json.loads(paths['task_set'].read_text(encoding='utf-8'))
    tasks = json.loads(paths['tasks'].read_text(encoding='utf-8'))['tasks']
    closure = json.loads(paths['closure'].read_text(encoding='utf-8'))
    l3_id = runner.TASKS[2]['task_id']
    l3_task = next(record for record in tasks if record['task_id'] == l3_id)
    l3_set_child = next(child for child in task_set['children'] if child['task_id'] == l3_id)
    l3_closure_child = next(child for child in closure['ordered_children'] if child['task_id'] == l3_id)

    assert l3_task['task_set']['bound_task_revision'] == l3_set_child['task_revision'] == 1
    assert l3_task['task_revision'] == l3_closure_child['task_revision'] == 3
    runner.write_b7_report(manifest)
    assert 'Status: pass' in Path(str(manifest['b7'])).read_text(encoding='utf-8')

    l3_task['task_set']['bound_task_revision'] = 3
    runner._write_json(paths['tasks'], {'schema': 'ccb.plan.tasks.v1', 'tasks': tasks})
    runner.write_b7_report(manifest)
    assert 'task_set_child_binding_mismatch' in _b7_rows(manifest)[0]['evidence_errors']


def test_b7_accepts_production_shaped_retry_lineage_with_distinct_effective_job(
    tmp_path: Path,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    paths = _write_root14_b7_authority(runner, manifest)
    source_job_id = 'job_root14_backfill_source'
    effective_job_id = 'job_root14_backfill'
    lineage = [{
        'message_id': 'message-root14-backfill',
        'source_attempt_id': 'attempt-root14-backfill-source',
        'successor_attempt_id': 'attempt-root14-backfill-effective',
        'retry_source_job_id': source_job_id,
        'retry_successor_job_id': effective_job_id,
        'retry_index': 1,
    }]
    backfill = json.loads(paths['backfill'].read_text(encoding='utf-8'))
    backfill['authority'].update(
        planner_source_job_id=source_job_id,
        planner_effective_job_id=effective_job_id,
        planner_retry_lineage=lineage,
    )
    backfill['backfill_digest'] = runner._authority_digest(backfill, omit='backfill_digest')
    runner._write_json(paths['backfill'], backfill)
    runtime = json.loads(paths['runtime'].read_text(encoding='utf-8'))
    runtime['planner'].update(
        job_id=source_job_id,
        source_job_id=source_job_id,
        effective_job_id=effective_job_id,
        retry_lineage=lineage,
    )
    runtime['backfill_import'].update(
        planner_source_job_id=source_job_id,
        planner_effective_job_id=effective_job_id,
        planner_retry_lineage=lineage,
        backfill_digest=backfill['backfill_digest'],
    )
    runtime['runtime_digest'] = runner._authority_digest(runtime, omit='runtime_digest')
    runner._write_json(paths['runtime'], runtime)
    intent_path = paths['runtime'].with_name('closure-intents.json')
    intents = json.loads(intent_path.read_text(encoding='utf-8'))
    transport = intents['intents'][0]['transport_ref']
    transport.update(
        planner_source_job_id=source_job_id,
        planner_effective_job_id=effective_job_id,
        planner_retry_lineage=lineage,
        backfill_digest=backfill['backfill_digest'],
    )
    runner._write_json(intent_path, intents)
    settlement = json.loads(paths['settlement'].read_text(encoding='utf-8'))
    settlement['transport_ref'] = transport
    settlement['settlement_digest'] = runner._authority_digest(settlement, omit='settlement_digest')
    runner._write_json(paths['settlement'], settlement)

    runner.write_b7_report(manifest)

    assert 'Status: pass' in Path(str(manifest['b7'])).read_text(encoding='utf-8')
    assert _b7_rows(manifest)[0]['planner_backfill_job_id'] == effective_job_id


def _b7_rows(manifest: dict[str, object]) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in Path(str(manifest['rows'])).read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]


@pytest.mark.parametrize(
    ('mutation', 'expected_error'),
    (
        ('missing_constraint', 'l3_terminal_constraint_missing_or_ambiguous'),
        ('wrong_constraint_digest', 'l3_terminal_constraint_settlement_missing_or_mismatch'),
        ('wrong_constraint_revision', 'l3_terminal_constraint_settlement_missing_or_mismatch'),
        ('missing_settlement', 'l3_terminal_constraint_settlement_missing_or_mismatch'),
        ('post_settlement_reactivation', 'l3_post_settlement_reactivation'),
    ),
)
def test_b7_rejects_unsettled_or_reactivated_l3_terminal_authority(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    paths = _write_root14_b7_authority(runner, manifest)
    activation = json.loads(paths['activation'].read_text(encoding='utf-8'))
    if mutation == 'missing_constraint':
        activation.pop('terminal_status_constraint')
        runner._write_json(paths['activation'], activation)
    elif mutation == 'wrong_constraint_digest':
        activation['terminal_status_constraint']['authority_digest'] = '0' * 64
        runner._write_json(paths['activation'], activation)
    elif mutation == 'wrong_constraint_revision':
        activation['terminal_status_constraint']['task_revision'] = 2
        runner._write_json(paths['activation'], activation)
    elif mutation == 'missing_settlement':
        paths['imports'].write_text('', encoding='utf-8')
    else:
        repeated = dict(activation)
        repeated.update(activation_id='act-root14-l3-repeated', record_type='ccb_loop_orchestrator_activation')
        repeated.pop('terminal_status_constraint')
        runner._write_json(paths['activation'].with_name('act-root14-l3-repeated.json'), repeated)

    runner.write_b7_report(manifest)

    rows = _b7_rows(manifest)
    assert len(rows) == len(runner.TASKS)
    assert not any(row['claimable_row'] for row in rows)
    assert expected_error in rows[0]['evidence_errors']
    assert 'Status: pass' not in Path(str(manifest['b7'])).read_text(encoding='utf-8')


@pytest.mark.parametrize(
    ('mutation', 'expected_error'),
    (
        ('task_set_running', 'task_set_closure_not_settled'),
        ('closure_digest_conflict', 'task_set_closure_digest_or_reference_mismatch'),
        ('source_parent_unsettled', 'task_set_source_parent_not_settled'),
        ('missing_backfill', 'planner_backfill_authority_missing'),
        ('missing_frontdesk_notification', 'task_set_feedback_runtime_or_frontdesk_handoff_mismatch'),
    ),
)
def test_b7_rejects_incomplete_decision029_closure_authority(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    paths = _write_root14_b7_authority(runner, manifest)
    if mutation == 'task_set_running':
        task_set = json.loads(paths['task_set'].read_text(encoding='utf-8'))
        task_set['state'] = 'running'
        runner._write_json(paths['task_set'], task_set)
    elif mutation == 'closure_digest_conflict':
        closure = json.loads(paths['closure'].read_text(encoding='utf-8'))
        closure['closure_digest'] = 'sha256:' + '0' * 64
        runner._write_json(paths['closure'], closure)
    elif mutation == 'source_parent_unsettled':
        tasks = json.loads(paths['tasks'].read_text(encoding='utf-8'))
        parent = next(record for record in tasks['tasks'] if record['task_id'].startswith('job_'))
        parent.pop('task_set_closure')
        runner._write_json(paths['tasks'], tasks)
    elif mutation == 'missing_backfill':
        paths['backfill'].unlink()
    else:
        runtime = json.loads(paths['runtime'].read_text(encoding='utf-8'))
        runtime['notification'] = {'status': 'notification_not_required'}
        runtime['runtime_digest'] = runner._authority_digest(runtime, omit='runtime_digest')
        runner._write_json(paths['runtime'], runtime)

    runner.write_b7_report(manifest)

    rows = _b7_rows(manifest)
    if mutation == 'task_set_running':
        assert len(rows) == 1
        assert rows[0]['classification'] == 'invalid_harness'
        assert 'Status: invalid_harness' in Path(str(manifest['b7'])).read_text(encoding='utf-8')
        return
    assert len(rows) == len(runner.TASKS)
    assert not any(row['claimable_row'] for row in rows)
    assert expected_error in rows[0]['evidence_errors']
    assert rows[0]['task_set_authority_valid'] is False


def test_b7_rejects_live_auto_runner_and_cleanup_requires_successful_b7(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    _write_root14_b7_authority(runner, manifest)
    live = {'status': 'live', 'path': 'auto-runner.lock', 'reason': 'pid_alive', 'pid': 12345}
    monkeypatch.setattr(runner, 'auto_runner_lock_state', lambda _manifest: live)

    runner.write_b7_report(manifest)

    rows = _b7_rows(manifest)
    assert not any(row['claimable_row'] for row in rows)
    assert all(row['auto_runner_state'] == live for row in rows)
    assert 'auto_runner_lock_live_before_b7' in rows[0]['evidence_errors']
    with pytest.raises(runner.HarnessBlocker, match='auto_runner_lock_live_before_cleanup'):
        runner.cleanup_after_b7(manifest)


def test_cleanup_runs_only_after_claimable_b7_and_never_launders_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner()
    _root, manifest = _materialize(tmp_path)
    paths = _write_root14_b7_authority(runner, manifest)
    runner.write_b7_report(manifest)
    calls: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        runner,
        'run_logged',
        lambda _manifest, label, argv: calls.append((label, argv)),
    )

    runner.cleanup_after_b7(manifest)

    assert calls == [('cleanup_after_b7', runner.ccb_project_args(manifest, 'kill'))]
    task_set = json.loads(paths['task_set'].read_text(encoding='utf-8'))
    task_set['state'] = 'running'
    runner._write_json(paths['task_set'], task_set)
    runner.write_b7_report(manifest)

    with pytest.raises(runner.HarnessBlocker, match='b7_not_claimable_for_cleanup'):
        runner.cleanup_after_b7(manifest)
    assert calls == [('cleanup_after_b7', runner.ccb_project_args(manifest, 'kill'))]


def test_manifest_paths_are_inspectable_and_internally_consistent(tmp_path: Path) -> None:
    runner = _load_runner()
    root, manifest = _materialize(tmp_path)

    path_fields = ('project', 'script', 'manifest', 'b7', 'rows', 'command_log', 'role_store')
    for field in path_fields:
        path = Path(str(manifest[field]))
        assert path.is_absolute()
        assert path == root or root in path.parents

    assert Path(str(manifest['project'])) == root / str(manifest['project_name'])
    assert manifest['provider_environment_policy']['inherits_HOME'] is True
    assert manifest['provider_environment_policy']['inherits_CCB_SOURCE_HOME'] is True
    assert manifest['provider_environment_policy']['exports_HOME'] is False
    assert manifest['provider_environment_policy']['exports_CCB_SOURCE_HOME'] is False
    assert manifest['provider_environment_policy']['sets_CCB_SOURCE_RUNTIME_OK'] is False
    assert manifest['provider_environment_policy']['sets_AGENT_ROLES_STORE'] == str(root / 'roles')
    assert manifest['role_install_command_template'] == [
        str(PROJECT_ROOT / 'ccb_test'),
        'roles',
        'install',
        '<role_id>',
        '--skip-tools',
    ]
    assert manifest['controller_owned_authority']['b7'] == manifest['b7']
    assert manifest['controller_owned_authority']['rows'] == manifest['rows']
    assert manifest['resident_agent_targets'] == [
        'frontdesk',
        'planner',
        'orchestrator',
        'task_detailer',
        'ccb_round_reviewer',
    ]
    assert manifest['resident_ask_targets'] == [
        'frontdesk',
        'planner',
        'orchestrator',
        'task_detailer',
        'ccb_round_reviewer',
    ]
    assert manifest['resident_agent_specs'] == {
        target: str(root / 'l1-l4-frontdesk-real-provider-lab' / '.ccb' / 'agents' / target / 'agent.json')
        for target in manifest['resident_ask_targets']
    }
    assert manifest['dynamic_loop_profiles'] == ['coder', 'code_reviewer']

    broken_manifest = dict(manifest)
    broken_manifest['resident_agent_targets'] = ['planner', 'orchestrator']
    broken_manifest['resident_ask_targets'] = ['planner', 'orchestrator']
    with pytest.raises(runner.HarnessError, match='manifest missing resident agent target'):
        runner.validate_manifest(broken_manifest)
