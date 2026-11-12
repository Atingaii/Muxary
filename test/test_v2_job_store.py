from __future__ import annotations

import json
from pathlib import Path

from ccbd.api_models import DeliveryScope, JobEvent, JobRecord, JobStatus, MessageEnvelope, SubmissionRecord, TargetKind
from jobs.store import JobEventStore, JobStore, SubmissionStore
from rust_helpers import RUST_HELPER_BIN_ENV
from storage.paths import PathLayout


def _envelope() -> MessageEnvelope:
    return MessageEnvelope(
        project_id='proj-1',
        to_agent='agent1',
        from_actor='user',
        body='hello',
        task_id='task-1',
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
    )


def _write_helper(path: Path, body: str) -> Path:
    path.write_text('#!/usr/bin/env python3\n' + body, encoding='utf-8')
    path.chmod(0o755)
    return path


def _strict_jsonl_file_helper(path: Path) -> Path:
    return _write_helper(
        path,
        """import json, sys
from pathlib import Path

if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['jsonl.tail.strict']}))
else:
    request = json.loads(sys.stdin.read())
    output = []
    for item in request['payload']['requests']:
        target = Path(item['path'])
        rows = []
        if target.is_file() and item['n'] > 0:
            parsed = []
            for line in target.read_text(encoding='utf-8').splitlines():
                text = line.strip()
                if not text:
                    continue
                value = json.loads(text)
                if not isinstance(value, dict):
                    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
                        'requests': [], 'error': {'kind': 'non_object', 'path': str(target), 'message': 'expected object'}
                    }}))
                    raise SystemExit(0)
                parsed.append(value)
            rows = parsed[-int(item['n']):]
        output.append({'id': item['id'], 'rows': rows})
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {'requests': output, 'error': None}}))
""",
    )


def _project_view_recent_jobs_helper(path: Path) -> Path:
    return _write_helper(
        path,
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['project_view.recent_jobs']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
        'jobs': [{
            'job_id': 'job-helper-1',
            'agent_name': 'agent1',
            'target_name': 'agent1',
            'provider': 'codex',
            'status': 'completed',
            'terminal_decision': {'reason': 'task_complete'},
            'created_at': '2026-03-18T00:00:00Z',
            'updated_at': '2026-03-18T00:00:09Z',
            'provider_options': {},
            'request': {
                'project_id': 'proj-1',
                'to_agent': 'agent1',
                'from_actor': 'cmd',
                'body': 'from helper',
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


def _jobs_query_recent_helper(path: Path) -> Path:
    return _write_helper(
        path,
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
            'job_id': 'job-query-helper',
            'agent_name': 'agent1',
            'target_name': 'agent1',
            'provider': 'codex',
            'status': 'completed',
            'terminal_decision': {'reason': 'task_complete'},
            'created_at': '2026-03-18T00:00:00Z',
            'updated_at': '2026-03-18T00:00:09Z',
            'provider_options': {},
            'request': {
                'project_id': 'proj-1',
                'to_agent': 'agent1',
                'from_actor': 'cmd',
                'body': 'from query helper',
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


def _job_summary_tail_helper(path: Path) -> Path:
    return _write_helper(
        path,
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['jobs.tail.summary']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
        'requests': [
            {'id': item['id'], 'jobs': [{
                'job_id': 'job-summary-helper',
                'agent_name': item['id'],
                'target_name': item['id'],
                'provider': 'codex',
                'status': 'completed',
                'terminal_decision': {'reason': 'task_complete'},
                'created_at': '2026-06-15T00:00:00Z',
                'updated_at': '2026-06-15T00:00:01Z',
                'provider_options': {},
                'request': {
                    'project_id': 'proj-1',
                    'to_agent': item['id'],
                    'from_actor': 'cmd',
                    'body': 'summary helper body',
                    'task_id': None,
                    'reply_to': None,
                    'message_type': 'ask',
                    'delivery_scope': 'single',
                    'silence_on_success': False,
                    'route_options': {},
                    'body_artifact': None,
                },
            }]}
            for item in request['payload']['requests']
        ],
        'error': None,
    }}))
""",
    )


def test_job_store_tracks_latest_job_record(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    store = JobStore(layout)
    store.append(
        JobRecord(
            job_id='job-1',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            request=_envelope(),
            status=JobStatus.QUEUED,
            terminal_decision=None,
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:00Z',
        )
    )
    store.append(
        JobRecord(
            job_id='job-1',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            request=_envelope(),
            status=JobStatus.RUNNING,
            terminal_decision=None,
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:01Z',
        )
    )

    latest = store.get_latest('agent1', 'job-1')
    assert latest is not None
    assert latest.status is JobStatus.RUNNING


def test_event_and_submission_stores_roundtrip(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    event_store = JobEventStore(layout)
    submission_store = SubmissionStore(layout)

    event_store.append(
        JobEvent(
            event_id='evt-1',
            job_id='job-1',
            agent_name='agent1',
            type='job_started',
            payload={'status': 'running'},
            timestamp='2026-03-18T00:00:00Z',
        )
    )
    line_no, events = event_store.read_since('agent1', 0)
    assert line_no == 1
    assert events[0].type == 'job_started'

    submission_store.append(
        SubmissionRecord(
            submission_id='sub-1',
            project_id='proj-1',
            from_actor='system',
            target_scope='all',
            task_id='task-1',
            job_ids=['job-1', 'job-2'],
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:01Z',
        )
    )
    latest = submission_store.get_latest('sub-1')
    assert latest is not None
    assert latest.job_ids == ['job-1', 'job-2']


def test_event_store_skips_provider_diagnostics_in_event_log(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    event_store = JobEventStore(layout)
    event_store.append(
        JobEvent(
            event_id='evt-1',
            job_id='job-1',
            agent_name='agent1',
            type='job_started',
            payload={'status': 'running'},
            timestamp='2026-03-18T00:00:00Z',
        )
    )
    events_path = layout.agent_events_path('agent1')
    with events_path.open('a', encoding='utf-8') as handle:
        handle.write(
            json.dumps(
                {
                    'record_type': 'agent_event',
                    'event_type': 'codex_memory_projection_ok',
                    'provider': 'codex',
                    'agent_name': 'agent1',
                },
                ensure_ascii=False,
            )
            + '\n'
        )
    event_store.append(
        JobEvent(
            event_id='evt-2',
            job_id='job-1',
            agent_name='agent1',
            type='job_completed',
            payload={'status': 'completed'},
            timestamp='2026-03-18T00:00:01Z',
        )
    )

    line_no, events = event_store.read_since('agent1', 0)
    assert line_no == 3
    assert [event.event_id for event in events] == ['evt-1', 'evt-2']


def test_submission_store_preserves_user_sender(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    submission_store = SubmissionStore(layout)

    submission_store.append(
        SubmissionRecord(
            submission_id='sub-user',
            project_id='proj-1',
            from_actor='USER',
            target_scope='single',
            task_id='task-user',
            job_ids=['job-9'],
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:01Z',
        )
    )

    latest = submission_store.get_latest('sub-user')
    assert latest is not None
    assert latest.from_actor == 'user'


def test_job_store_supports_explicit_target_lookup(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    store = JobStore(layout)
    store.append(
        JobRecord(
            job_id='job-agent-1',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            provider_options={'no_wrap': True},
            target_kind=TargetKind.AGENT,
            target_name='agent1',
            request=_envelope(),
            status=JobStatus.ACCEPTED,
            terminal_decision=None,
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:00Z',
        )
    )

    latest = store.get_latest_target(TargetKind.AGENT, 'agent1', 'job-agent-1')
    assert latest is not None
    assert latest.target_kind is TargetKind.AGENT
    assert latest.target_name == 'agent1'
    assert latest.provider_options == {'no_wrap': True}


def test_job_store_lists_agent_tail(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    store = JobStore(layout)
    for index in range(6):
        store.append(
            JobRecord(
                job_id=f'job-{index}',
                submission_id=None,
                agent_name='agent1',
                provider='codex',
                request=_envelope(),
                status=JobStatus.COMPLETED,
                terminal_decision={'reason': 'task_complete'},
                cancel_requested_at=None,
                created_at='2026-03-18T00:00:00Z',
                updated_at=f'2026-03-18T00:00:0{index}Z',
            )
        )

    records = store.list_agent_tail('agent1', limit=3)

    assert [record.job_id for record in records] == ['job-3', 'job-4', 'job-5']


def test_job_store_lists_agent_tails_batch(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo-batch-tail')
    store = JobStore(layout)
    for agent_name in ('agent1', 'agent2'):
        for index in range(3):
            store.append(
                JobRecord(
                    job_id=f'{agent_name}-job-{index}',
                    submission_id=None,
                    agent_name=agent_name,
                    provider='codex',
                    request=_envelope(),
                    status=JobStatus.COMPLETED,
                    terminal_decision={'reason': 'task_complete'},
                    cancel_requested_at=None,
                    created_at='2026-03-18T00:00:00Z',
                    updated_at=f'2026-03-18T00:00:0{index}Z',
                )
            )

    records = store.list_agent_tails_batch(('agent1', 'agent2'), limit=2)

    assert [record.job_id for record in records['agent1']] == ['agent1-job-1', 'agent1-job-2']
    assert [record.job_id for record in records['agent2']] == ['agent2-job-1', 'agent2-job-2']


def test_job_store_batch_tail_uses_required_strict_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-batch-tail-helper')
    store = JobStore(layout)
    helper = _strict_jsonl_file_helper(tmp_path / 'helper.py')
    monkeypatch.setenv('CCB_RUST_JSONL_STORE', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))
    for agent_name in ('agent1', 'agent2'):
        for index in range(3):
            store.append(
                JobRecord(
                    job_id=f'{agent_name}-job-{index}',
                    submission_id=None,
                    agent_name=agent_name,
                    provider='codex',
                    request=_envelope(),
                    status=JobStatus.COMPLETED,
                    terminal_decision={'reason': 'task_complete'},
                    cancel_requested_at=None,
                    created_at='2026-03-18T00:00:00Z',
                    updated_at=f'2026-03-18T00:00:0{index}Z',
                )
            )

    records = store.list_agent_tails_batch(('agent1', 'agent2'), limit=1)

    assert [record.job_id for record in records['agent1']] == ['agent1-job-2']
    assert [record.job_id for record in records['agent2']] == ['agent2-job-2']


def test_job_store_required_batch_tail_missing_helper_does_not_fallback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-batch-tail-helper-missing')
    store = JobStore(layout)
    store.append(
        JobRecord(
            job_id='job-1',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            request=_envelope(),
            status=JobStatus.COMPLETED,
            terminal_decision={'reason': 'task_complete'},
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:01Z',
        )
    )
    monkeypatch.setenv('CCB_RUST_JSONL_STORE', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(tmp_path / 'missing-helper'))

    try:
        store.list_agent_tails_batch(('agent1',), limit=1)
    except RuntimeError as exc:
        assert 'no Python fallback' in str(exc)
    else:
        raise AssertionError('expected required helper path to fail without Python fallback')


def test_job_store_lists_agent_tail_summaries_batch(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo-batch-summary-tail')
    store = JobStore(layout)
    for agent_name in ('agent1', 'agent2'):
        for index in range(3):
            store.append(
                JobRecord(
                    job_id=f'{agent_name}-job-{index}',
                    submission_id=None,
                    agent_name=agent_name,
                    provider='codex',
                    request=_envelope(),
                    status=JobStatus.COMPLETED,
                    terminal_decision={'reason': 'task_complete'},
                    cancel_requested_at=None,
                    created_at='2026-03-18T00:00:00Z',
                    updated_at=f'2026-03-18T00:00:0{index}Z',
                )
            )

    summaries = store.list_agent_tail_summaries_batch(('agent1', 'agent2'), limit=2)

    assert [summary.job_id for summary in summaries['agent1']] == ['agent1-job-1', 'agent1-job-2']
    assert summaries['agent2'][1].request.from_actor == 'user'


def test_job_store_agent_tail_summaries_use_required_projection_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-batch-summary-helper')
    store = JobStore(layout)
    helper = _job_summary_tail_helper(tmp_path / 'job_summary.py')
    monkeypatch.setenv('CCB_RUST_JOB_SUMMARY_TAIL', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))
    store.append(
        JobRecord(
            job_id='job-python-path-should-not-run',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            request=_envelope(),
            status=JobStatus.COMPLETED,
            terminal_decision={'reason': 'task_complete'},
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:01Z',
        )
    )

    summaries = store.list_agent_tail_summaries_batch(('agent1',), limit=1)

    assert [summary.job_id for summary in summaries['agent1']] == ['job-summary-helper']
    assert summaries['agent1'][0].request.body == 'summary helper body'


def test_job_store_agent_tail_summaries_missing_helper_does_not_fallback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-batch-summary-helper-missing')
    store = JobStore(layout)
    monkeypatch.setenv('CCB_RUST_JOB_SUMMARY_TAIL', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(tmp_path / 'missing-helper'))

    try:
        store.list_agent_tail_summaries_batch(('agent1',), limit=1)
    except RuntimeError as exc:
        assert 'no Python fallback' in str(exc)
    else:
        raise AssertionError('expected required helper path to fail without Python fallback')


def test_job_store_lists_project_view_recent_job_summaries(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo-project-view-summary')
    store = JobStore(layout)
    for index, status in enumerate((JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.FAILED)):
        store.append(
            JobRecord(
                job_id=f'job-{index}',
                submission_id=None,
                agent_name='agent1',
                provider='codex',
                request=_envelope(),
                status=status,
                terminal_decision={'reason': status.value} if status in {JobStatus.COMPLETED, JobStatus.FAILED} else None,
                cancel_requested_at=None,
                created_at='2026-03-18T00:00:00Z',
                updated_at=f'2026-03-18T00:00:0{index}Z',
            )
        )

    summaries = store.list_project_view_recent_jobs(
        ('agent1',),
        per_agent_limit=10,
        result_limit=8,
        statuses=('completed', 'failed'),
    )

    assert [summary.job_id for summary in summaries] == ['job-2', 'job-1']
    assert summaries[0].status is JobStatus.FAILED
    assert summaries[0].request.from_actor == 'user'


def test_job_store_project_view_recent_jobs_uses_required_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-project-view-summary-helper')
    store = JobStore(layout)
    helper = _project_view_recent_jobs_helper(tmp_path / 'recent_jobs.py')
    monkeypatch.setenv('CCB_RUST_PROJECT_VIEW_RECENT_JOBS', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))

    summaries = store.list_project_view_recent_jobs(
        ('agent1',),
        per_agent_limit=128,
        result_limit=8,
        statuses=('completed',),
    )

    assert [summary.job_id for summary in summaries] == ['job-helper-1']
    assert summaries[0].request.body == 'from helper'


def test_job_store_project_view_recent_jobs_adaptive_python_scan(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-project-view-summary-adaptive')
    store = JobStore(layout)
    for index in range(12):
        store.append(
            JobRecord(
                job_id=f'job-{index}',
                submission_id=None,
                agent_name='agent1',
                provider='codex',
                request=_envelope(),
                status=JobStatus.COMPLETED,
                terminal_decision={'reason': 'task_complete'},
                cancel_requested_at=None,
                created_at='2026-03-18T00:00:00Z',
                updated_at=f'2026-03-18T00:00:{index:02d}Z',
            )
        )
    original = store.list_agent_tail
    limits: list[int] = []

    def recording_tail(agent_name: str, *, limit: int):
        limits.append(limit)
        return original(agent_name, limit=limit)

    monkeypatch.setattr(store, 'list_agent_tail', recording_tail)

    summaries = store.list_project_view_recent_jobs(
        ('agent1',),
        per_agent_initial_limit=4,
        per_agent_limit=16,
        result_limit=8,
        statuses=('completed',),
    )

    assert limits == [4, 8]
    assert [summary.job_id for summary in summaries] == [
        'job-11',
        'job-10',
        'job-9',
        'job-8',
        'job-7',
        'job-6',
        'job-5',
        'job-4',
    ]


def test_job_store_project_view_recent_jobs_adaptive_required_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-project-view-summary-query-helper')
    store = JobStore(layout)
    helper = _jobs_query_recent_helper(tmp_path / 'recent_query.py')
    monkeypatch.setenv('CCB_RUST_PROJECT_VIEW_RECENT_JOBS', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))

    summaries = store.list_project_view_recent_jobs(
        ('agent1',),
        per_agent_initial_limit=4,
        per_agent_limit=16,
        result_limit=8,
        statuses=('completed',),
    )

    assert [summary.job_id for summary in summaries] == ['job-query-helper']
    assert summaries[0].request.body == 'from query helper'


def test_job_store_project_view_recent_jobs_missing_helper_does_not_fallback(
    monkeypatch,
    tmp_path: Path,
) -> None:
    layout = PathLayout(tmp_path / 'repo-project-view-summary-helper-missing')
    store = JobStore(layout)
    store.append(
        JobRecord(
            job_id='job-python-fallback-would-return',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            request=_envelope(),
            status=JobStatus.COMPLETED,
            terminal_decision={'reason': 'task_complete'},
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:01Z',
        )
    )
    monkeypatch.setenv('CCB_RUST_PROJECT_VIEW_RECENT_JOBS', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(tmp_path / 'missing-helper'))

    try:
        store.list_project_view_recent_jobs(('agent1',), per_agent_limit=128, result_limit=8)
    except RuntimeError as exc:
        assert 'no Python fallback' in str(exc)
    else:
        raise AssertionError('expected required helper path to fail without Python fallback')


def test_job_store_roundtrips_silence_on_success_request_flag(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    store = JobStore(layout)
    envelope = MessageEnvelope(
        project_id='proj-1',
        to_agent='agent1',
        from_actor='user',
        body='hello',
        task_id='task-1',
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
        silence_on_success=True,
    )
    store.append(
        JobRecord(
            job_id='job-silent-1',
            submission_id=None,
            agent_name='agent1',
            provider='codex',
            request=envelope,
            status=JobStatus.ACCEPTED,
            terminal_decision=None,
            cancel_requested_at=None,
            created_at='2026-03-18T00:00:00Z',
            updated_at='2026-03-18T00:00:00Z',
        )
    )

    latest = store.get_latest('agent1', 'job-silent-1')
    assert latest is not None
    assert latest.request.silence_on_success is True


def test_job_store_roundtrips_request_route_options(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo-job-store-route-options')
    store = JobStore(layout)
    envelope = MessageEnvelope(
        project_id='project-1',
        to_agent='agent1',
        from_actor='agent2',
        body='hello',
        task_id=None,
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
        route_options={'mode': 'chain', 'chain_edge_id': 'cb_1'},
    )
    record = JobRecord(
        job_id='job_route_options',
        submission_id=None,
        agent_name='agent1',
        provider='codex',
        request=envelope,
        status=JobStatus.ACCEPTED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-03-30T00:00:00Z',
        updated_at='2026-03-30T00:00:00Z',
    )

    store.append(record)

    latest = store.get_latest('agent1', 'job_route_options')
    assert latest is not None
    assert latest.request.route_options == {'mode': 'chain', 'chain_edge_id': 'cb_1'}


def test_event_store_supports_explicit_target_lookup(tmp_path: Path) -> None:
    layout = PathLayout(tmp_path / 'repo')
    event_store = JobEventStore(layout)
    event_store.append(
        JobEvent(
            event_id='evt-agent-1',
            job_id='job-agent-1',
            agent_name='agent1',
            target_kind=TargetKind.AGENT,
            target_name='agent1',
            type='job_started',
            payload={'status': 'running'},
            timestamp='2026-03-18T00:00:00Z',
        )
    )

    line_no, events = event_store.read_since_target(TargetKind.AGENT, 'agent1', 0)
    assert line_no == 1
    assert events[0].target_kind is TargetKind.AGENT
    assert events[0].target_name == 'agent1'
