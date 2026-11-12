from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli.context import CliContextBuilder
from cli.models import ParsedLoopRunnerCommand, ParsedQuestionCommand
from cli.parser import CliParser
from cli.phase2 import maybe_handle_phase2
from cli.services.ask_runtime import AskSummary
from cli.services.loop_runner import loop_runner_once


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _project_with_plan(tmp_path: Path) -> Path:
    project_root = tmp_path / 'repo-question'
    (project_root / '.ccb').mkdir(parents=True)
    _write(project_root / 'docs' / 'plantree' / 'plans' / 'demo-plan' / 'README.md', '# Demo Plan\n')
    return project_root


def _run_phase2(argv: list[str], *, cwd: Path) -> tuple[int, dict[str, object], str, str]:
    stdout = StringIO()
    stderr = StringIO()
    code = maybe_handle_phase2(argv, cwd=cwd, stdout=stdout, stderr=stderr)
    out_text = stdout.getvalue()
    payload = json.loads(out_text) if out_text.strip().startswith('{') else {}
    return code, payload, out_text, stderr.getvalue()


def _create_task(project_root: Path, *, task_id: str = 'task-001') -> None:
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Clarify the slice',
            '--task-id',
            task_id,
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err


def _import_plan_artifact(project_root: Path, *, task_id: str, kind: str, text: str | None = None) -> dict[str, object]:
    artifact = project_root / 'drafts' / f'{kind}.md'
    _write(artifact, text if text is not None else f'{kind}\n')
    code, payload, _out, err = _run_phase2(
        ['plan', 'task-artifact', '--task', task_id, '--kind', kind, '--file', str(artifact), '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    return payload


def test_question_parser_supports_v1_commands() -> None:
    parser = CliParser()

    assert parser.parse(
        ['question', 'candidate-import', '--task', 'task-001', '--file', 'drafts/candidate.jsonl', '--json']
    ) == ParsedQuestionCommand(
        project=None,
        action='candidate-import',
        task_id='task-001',
        file_path='drafts/candidate.jsonl',
        json_output=True,
    )
    assert parser.parse(
        ['question', 'user-batch-import', '--task', 'task-001', '--file', 'drafts/user-questions.json', '--json']
    ) == ParsedQuestionCommand(
        project=None,
        action='user-batch-import',
        task_id='task-001',
        file_path='drafts/user-questions.json',
        json_output=True,
    )
    assert parser.parse(
        ['question', 'answer-import', '--task', 'task-001', '--file', 'drafts/raw-answer.md', '--json']
    ) == ParsedQuestionCommand(
        project=None,
        action='answer-import',
        task_id='task-001',
        file_path='drafts/raw-answer.md',
        json_output=True,
    )
    assert parser.parse(
        ['question', 'normalized-import', '--task', 'task-001', '--file', 'drafts/normalized.jsonl', '--json']
    ) == ParsedQuestionCommand(
        project=None,
        action='normalized-import',
        task_id='task-001',
        file_path='drafts/normalized.jsonl',
        json_output=True,
    )
    assert parser.parse(['question', 'status', '--task', 'task-001', '--json']) == ParsedQuestionCommand(
        project=None,
        action='status',
        task_id='task-001',
        json_output=True,
    )


def test_question_candidate_import_records_provenance_and_digest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_plan(tmp_path)
    _create_task(project_root)
    candidate = project_root / 'drafts' / 'candidate-questions.jsonl'
    _write(
        candidate,
        json.dumps(
            {
                'id': 'q1',
                'stage': 'planning',
                'question': 'Which target platform is blocking?',
                'why_blocking': 'Verification cannot be scoped without the platform.',
                'default_if_unanswered': 'linux',
                'defer_allowed': True,
            },
            ensure_ascii=False,
        )
        + '\n',
    )
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'planner')
    monkeypatch.setenv('CCB_ACTOR_ROLE', 'agentroles.ccb_planner')
    monkeypatch.setenv('CCB_JOB_ID', 'job_planner_question')

    code, payload, _out, err = _run_phase2(
        ['question', 'candidate-import', '--task', 'task-001', '--file', str(candidate), '--json'],
        cwd=project_root,
    )

    assert code == 0, err
    assert payload['question_status'] == 'ok'
    assert payload['task_status'] == 'draft'
    assert payload['artifact']['kind'] == 'candidate_questions'
    assert payload['artifact']['question_count'] == 1
    assert payload['artifact']['sha256']
    assert payload['artifact']['bytes'] == len(candidate.read_text(encoding='utf-8').encode('utf-8'))
    assert payload['artifact']['actor'] == {
        'source': 'cli',
        'actor': 'planner',
        'role': 'agentroles.ccb_planner',
        'job_id': 'job_planner_question',
    }
    imported = project_root / str(payload['artifact']['path'])
    assert imported.read_text(encoding='utf-8') == candidate.read_text(encoding='utf-8')

    code, status, _out, err = _run_phase2(
        ['question', 'status', '--task', 'task-001', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert status['artifact_count'] == 1
    assert status['latest']['candidate_questions']['path'] == payload['artifact']['path']
    assert not (project_root / '.ccb' / 'runtime').exists()


def test_question_import_rejects_invalid_jsonl_unknown_task_malformed_fields_and_external_files(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _create_task(project_root)
    invalid_jsonl = project_root / 'drafts' / 'invalid.jsonl'
    _write(invalid_jsonl, '{"id":"q1"\n')

    code, _payload, _out, err = _run_phase2(
        ['question', 'candidate-import', '--task', 'task-001', '--file', str(invalid_jsonl), '--json'],
        cwd=project_root,
    )

    assert code == 1
    assert 'candidate questions JSONL line 1 is invalid JSON' in err

    malformed = project_root / 'drafts' / 'malformed.jsonl'
    _write(malformed, '{"id":"q1","stage":"planning","question":"A?","why_blocking":"B"}\n')

    code, _payload, _out, err = _run_phase2(
        ['question', 'candidate-import', '--task', 'task-001', '--file', str(malformed), '--json'],
        cwd=project_root,
    )

    assert code == 1
    assert 'candidate question field defer_allowed must be boolean' in err

    code, _payload, _out, err = _run_phase2(
        ['question', 'candidate-import', '--task', 'missing-task', '--file', str(malformed), '--json'],
        cwd=project_root,
    )

    assert code == 1
    assert 'plan task not found: missing-task' in err

    broken = project_root / 'drafts' / 'broken.jsonl'
    _write(
        broken,
        '{"id":"q1","stage":"planning","question":"A?","why_blocking":"B","defer_allowed":false}\n'
        '{"id":"q1","stage":"planning","question":"C?","why_blocking":"D","defer_allowed":true}\n',
    )

    code, _payload, _out, err = _run_phase2(
        ['question', 'candidate-import', '--task', 'task-001', '--file', str(broken), '--json'],
        cwd=project_root,
    )

    assert code == 1
    assert 'duplicate candidate question id: q1' in err

    outside = tmp_path / 'outside.jsonl'
    outside.write_text('{}\n', encoding='utf-8')
    code, _payload, _out, err = _run_phase2(
        ['question', 'candidate-import', '--task', 'task-001', '--file', str(outside), '--json'],
        cwd=project_root,
    )

    assert code == 1
    assert 'question artifact file must be inside project root' in err


def test_question_status_reports_candidate_user_raw_and_normalized_refs(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _create_task(project_root)
    candidate = project_root / 'drafts' / 'candidate-questions.jsonl'
    user_questions = project_root / 'drafts' / 'user-questions.json'
    raw_answer = project_root / 'drafts' / 'raw-answer.md'
    normalized = project_root / 'drafts' / 'normalized-answers.jsonl'
    _write(
        candidate,
        json.dumps(
            {
                'id': 'q1',
                'stage': 'planning',
                'question': 'Use fake providers?',
                'why_blocking': 'The smoke target must be bounded.',
                'default_if_unanswered': 'yes',
                'defer_allowed': False,
            },
            ensure_ascii=False,
        )
        + '\n',
    )
    _write(
        user_questions,
        json.dumps(
            {
                'schema': 'ccb.workflow.user_questions/v1',
                'task_id': 'task-001',
                'batch_id': 'qbatch-001',
                'questions': [{'id': 'q1', 'text': 'Use fake providers?', 'why': 'Bounded smoke.', 'required': True}],
                'defaults': [],
                'deferred': [],
            },
            ensure_ascii=False,
        ),
    )
    _write(raw_answer, 'Yes.\n')
    _write(
        normalized,
        json.dumps(
            {'question_id': 'q1', 'answer': 'Yes.', 'source': 'user', 'planner_note': 'Continue.'},
            ensure_ascii=False,
        )
        + '\n',
    )

    for action, path in (
        ('candidate-import', candidate),
        ('user-batch-import', user_questions),
        ('answer-import', raw_answer),
        ('normalized-import', normalized),
    ):
        code, _payload, _out, err = _run_phase2(
            ['question', action, '--task', 'task-001', '--file', str(path), '--json'],
            cwd=project_root,
        )
        assert code == 0, err

    code, status, _out, err = _run_phase2(['question', 'status', '--task', 'task-001', '--json'], cwd=project_root)

    assert code == 0, err
    assert status['artifact_count'] == 4
    assert set(status['latest']) == {'candidate_questions', 'normalized_answers', 'raw_answer', 'user_questions'}
    assert status['latest']['candidate_questions']['count'] == 1
    assert status['latest']['user_questions']['batch_id'] == 'qbatch-001'
    assert status['latest']['raw_answer']['path'].endswith('raw-answer.md')
    assert status['latest']['normalized_answers']['count'] == 1


def test_question_user_batch_pauses_runner_with_question_refs(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _create_task(project_root)
    user_questions = project_root / 'drafts' / 'user-questions.json'
    _write(
        user_questions,
        json.dumps(
            {
                'schema': 'ccb.workflow.user_questions/v1',
                'task_id': 'task-001',
                'batch_id': 'qbatch-001',
                'questions': [
                    {
                        'id': 'q1',
                        'text': 'Should the first slice include runner integration?',
                        'why': 'It changes the activation boundary.',
                        'required': True,
                    }
                ],
                'defaults': [],
                'deferred': [],
            },
            ensure_ascii=False,
        ),
    )

    code, payload, _out, err = _run_phase2(
        ['question', 'user-batch-import', '--task', 'task-001', '--file', str(user_questions), '--json'],
        cwd=project_root,
    )

    assert code == 0, err
    assert payload['task_status'] == 'needs_clarification'
    assert payload['status_update']['status'] == 'updated'
    assert payload['artifact']['kind'] == 'user_questions'
    assert payload['artifact']['batch_id'] == 'qbatch-001'
    assert payload['artifact']['required_count'] == 1

    code, runner, _out, err = _run_phase2(['loop', 'runner', '--once', '--json'], cwd=project_root)
    assert code == 0, err
    assert runner['loop_runner_status'] == 'paused'
    assert runner['action'] == 'paused'
    assert runner['question_refs']['next_owner'] == 'task_detailer'
    assert runner['question_refs']['latest']['user_questions']['path'] == payload['artifact']['path']


def test_question_answers_wake_planner_with_answer_refs(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _create_task(project_root)
    user_questions = project_root / 'drafts' / 'user-questions.json'
    raw_answer = project_root / 'drafts' / 'raw-answer.md'
    normalized = project_root / 'drafts' / 'normalized-answers.jsonl'
    _write(
        user_questions,
        json.dumps(
            {
                'schema': 'ccb.workflow.user_questions/v1',
                'task_id': 'task-001',
                'batch_id': 'qbatch-001',
                'questions': [
                    {'id': 'q1', 'text': 'Use runner refs?', 'why': 'Planner wakeup needs a compact answer.', 'required': True}
                ],
                'defaults': [],
                'deferred': [],
            },
            ensure_ascii=False,
        ),
    )
    _write(raw_answer, 'Yes, include runner refs.\n')
    _write(
        normalized,
        json.dumps(
            {
                'question_id': 'q1',
                'answer': 'Include runner refs.',
                'source': 'user',
                'planner_note': 'Planner can continue with compact refs.',
            },
            ensure_ascii=False,
        )
        + '\n',
    )
    assert _run_phase2(['question', 'user-batch-import', '--task', 'task-001', '--file', str(user_questions), '--json'], cwd=project_root)[0] == 0
    assert _run_phase2(['question', 'answer-import', '--task', 'task-001', '--file', str(raw_answer), '--json'], cwd=project_root)[0] == 0
    code, normalized_payload, _out, err = _run_phase2(
        ['question', 'normalized-import', '--task', 'task-001', '--file', str(normalized), '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert normalized_payload['task_status'] == 'draft'
    assert normalized_payload['status_update']['reason'] == 'normalized_answers_imported'

    command = ParsedLoopRunnerCommand(project=None, once=True, json_output=True)
    context = CliContextBuilder().build(command, cwd=project_root, bootstrap_if_missing=False)

    def fake_submit_ask(_context, ask_command):
        assert ask_command.target == 'planner'
        assert 'Open question refs:' in ask_command.message
        return AskSummary(
            project_id=context.project.project_id,
            submission_id=None,
            jobs=({'job_id': 'job_planner_answers', 'agent_name': 'planner', 'status': 'submitted'},),
        )

    payload = loop_runner_once(context, command, services=SimpleNamespace(submit_ask=fake_submit_ask))

    assert payload['action'] == 'activated_planner'
    activation = json.loads(Path(str(payload['activation_path'])).read_text(encoding='utf-8'))
    assert activation['open_question_refs']['next_owner'] == 'planner'
    assert activation['open_question_refs']['latest']['raw_answer']['path']
    assert activation['open_question_refs']['latest']['normalized_answers']['path'] == normalized_payload['artifact']['path']


def test_runner_keeps_new_draft_with_planner_and_plan_guard_requires_review(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _create_task(project_root, task_id='task-review')
    for kind in ('requirements', 'acceptance', 'verification', 'handoff'):
        _import_plan_artifact(project_root, task_id='task-review', kind=kind)

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-review', '--status', 'ready', '--json'],
        cwd=project_root,
    )
    assert code == 1
    assert 'ready requires artifacts: review' in err

    command = ParsedLoopRunnerCommand(project=None, once=True, json_output=True)
    context = CliContextBuilder().build(command, cwd=project_root, bootstrap_if_missing=False)
    seen: dict[str, object] = {}

    def fake_submit_ask(_context, ask_command):
        seen['target'] = ask_command.target
        seen['message'] = ask_command.message
        return AskSummary(
            project_id=context.project.project_id,
            submission_id=None,
            jobs=({'job_id': 'job_planner', 'agent_name': 'planner', 'status': 'submitted'},),
        )

    payload = loop_runner_once(context, command, services=SimpleNamespace(submit_ask=fake_submit_ask))

    assert payload['loop_runner_status'] == 'ok'
    assert payload['action'] == 'activated_planner'
    assert payload['next_owner'] == 'planner'
    assert seen['target'] == 'planner'
    assert 'Task packet root:' in str(seen['message'])
    activation = json.loads(Path(str(payload['activation_path'])).read_text(encoding='utf-8'))
    assert set(activation['artifact_refs']) == {'acceptance', 'handoff', 'requirements', 'verification'}
    assert activation['script_write_rules']

    _import_plan_artifact(project_root, task_id='task-review', kind='review')
    code, ready, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-review', '--status', 'ready', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert ready['status'] == 'ready'
