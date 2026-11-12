from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from jobs.store import JobStore
from message_bureau import AttemptRecord, AttemptState, AttemptStore, MessageRecord, MessageState, MessageStore
from storage.paths import PathLayout
from cli.services.ask_runtime import AskSummary
from cli.models_start import ParsedLoopRunnerCommand
from cli.services.loop_runner import loop_runner_auto, loop_runner_once
from cli.services.plan_tasks import detail_ready_stop_contract_authority, plan_task
from cli.services.task_set_closure import create_task_set_authority, evaluate_task_set_closure
from cli.services.task_set_feedback_runtime import advance_task_set_feedback_runtime, _retry_successor_job
from cli.services.task_set_feedback_runtime import _deps


_EVIDENCE_DIGEST = 'sha256:' + 'a' * 64


def test_runtime_wires_default_transactional_planner_apply() -> None:
    assert _deps(None).apply_planner_feedback.__module__ == 'cli.services.planner_feedback_apply'


def _context(tmp_path: Path):
    return SimpleNamespace(
        project=SimpleNamespace(project_root=tmp_path, project_id='project-test'),
        paths=None,
    )


def _authority(tmp_path: Path, *, revision: int = 1) -> tuple[dict[str, object], dict[str, object]]:
    root = tmp_path / 'docs/plantree/plans/demo/task-sets/set-a'
    root.mkdir(parents=True, exist_ok=True)
    closure = {
        'schema': 'ccb.plan.task_set_closure.v1',
        'task_set_id': 'set-a',
        'task_set_revision': revision,
        'ordered_terminal_evidence_digest': _EVIDENCE_DIGEST,
        'aggregate_result': 'pass',
        'closure_digest': 'sha256:' + 'b' * 64,
    }
    (root / 'closure.json').write_text(json.dumps(closure), encoding='utf-8')
    task_set = {
        'task_set_id': 'set-a',
        'task_set_revision': revision,
        'plan_slug': 'demo',
        'state': 'closure_pending',
        'plan_revision': {'revision': 7, 'digest': 'sha256:' + 'c' * 64},
        'closure': {
            'path': 'docs/plantree/plans/demo/task-sets/set-a/closure.json',
            'closure_digest': closure['closure_digest'],
            'ordered_terminal_evidence_digest': _EVIDENCE_DIGEST,
        },
    }
    task_set_path = root / 'task-set.json'
    task_set_path.write_text(json.dumps(task_set), encoding='utf-8')
    intent = {
        'intent_id': 'intent-a',
        'task_set_id': 'set-a',
        'task_set_revision': revision,
        'ordered_terminal_evidence_digest': _EVIDENCE_DIGEST,
        'closure_digest': closure['closure_digest'],
        'task_set_path': str(task_set_path),
    }
    return intent, task_set


def _planner_reply(*, notify: bool = True) -> str:
    status = {
        'schema': 'ccb.planner.frontdesk_status.v1',
        'notification_identity': 'notice-a',
        'aggregate_result': 'pass',
        'accepted_scope': ['all required children'],
        'unresolved_scope': [],
        'blockers': [],
        'next_milestone': {
            'kind': 'workflow_terminal',
            'ref': 'done',
            'rationale': 'All required children passed.',
        },
        'evidence_refs': ['docs/plantree/plans/demo/task-sets/set-a/closure.json'],
        'user_report_body': 'All required work passed validated closure.',
    }
    proposal = {
        'schema': 'ccb.planner.backfill_proposal.v1',
        'mode': 'task_set_closure',
        'expected_plan_revision': 'sha256:' + 'c' * 64,
        'task_or_task_set_id': 'set-a',
        'task_or_task_set_revision': 1,
        'closure_evidence_digest': _EVIDENCE_DIGEST,
        'aggregate_result': 'pass',
        'result': 'closure_complete',
        'brief_summary': 'All required work passed.',
        'roadmap_transitions': [],
        'todo_transitions': [],
        'decision_refs': [],
        'open_question_refs': [],
        'evidence_refs': ['docs/plantree/plans/demo/task-sets/set-a/closure.json'],
        'accepted_scope': ['all required children'],
        'unresolved_scope': [],
        'blockers': [],
        'replan_inputs': [],
        'next_milestone': status['next_milestone'],
        'frontdesk_notification_required': notify,
        'frontdesk_status': status,
    }
    return '**planner-backfill.json**\n```json\n' + json.dumps(proposal) + '\n```'


def _mixed_terminal_planner_reply(
    task_set: dict[str, object],
    closure: dict[str, object],
) -> str:
    evidence_refs = [
        f'docs/plantree/plans/demo/task-sets/{task_set["task_set_id"]}/closure.json'
    ]
    accepted_scope = ['done/pass and bounded detail-ready children']
    unresolved_scope = ['replan-required and blocked child follow-up']
    blockers: list[str] = []
    next_milestone = {
        'kind': 'selected',
        'ref': 'planner-replan',
        'rationale': 'The mixed terminal set requires a bounded Planner replan.',
    }
    status = {
        'schema': 'ccb.planner.frontdesk_status.v1',
        'notification_identity': 'mixed-terminal-notice',
        'aggregate_result': 'replan_required',
        'accepted_scope': accepted_scope,
        'unresolved_scope': unresolved_scope,
        'blockers': blockers,
        'next_milestone': next_milestone,
        'evidence_refs': evidence_refs,
        'user_report_body': 'Bounded terminal work is preserved; Planner replan is required.',
    }
    proposal = {
        'schema': 'ccb.planner.backfill_proposal.v1',
        'mode': 'task_set_closure',
        'expected_plan_revision': task_set['plan_revision']['digest'],
        'task_or_task_set_id': task_set['task_set_id'],
        'task_or_task_set_revision': task_set['task_set_revision'],
        'closure_evidence_digest': closure['ordered_terminal_evidence_digest'],
        'aggregate_result': 'replan_required',
        'result': 'task_set_replanned',
        'brief_summary': 'Mixed terminal children require a bounded replan.',
        'roadmap_transitions': [],
        'todo_transitions': [],
        'decision_refs': [],
        'open_question_refs': [],
        'evidence_refs': evidence_refs,
        'accepted_scope': accepted_scope,
        'unresolved_scope': unresolved_scope,
        'blockers': blockers,
        'replan_inputs': ['Preserve accepted children while replanning unresolved scope.'],
        'next_milestone': next_milestone,
        'frontdesk_notification_required': True,
        'frontdesk_status': status,
    }
    return '**planner-backfill.json**\n```json\n' + json.dumps(proposal) + '\n```'


def _create_runtime_task(
    context,
    task_id: str,
    *,
    ready: bool = True,
    stop_at_detail_ready: bool = False,
) -> dict[str, object]:
    created = plan_task(
        context,
        SimpleNamespace(
            action='task-create',
            plan_slug='demo',
            title=task_id,
            task_id=task_id,
        ),
    )
    if not ready:
        return created['task']
    revision = created['task']['task_revision']
    stop_contract = (
        f'Task: {task_id}\nRoute: needs_detail\nExpected stop: detail_ready.\n'
        if stop_at_detail_ready
        else f'Task: {task_id}\n'
    )
    for kind in ('task_packet', 'execution_contract'):
        path = Path(context.project.project_root) / 'drafts' / f'{task_id}-{kind}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'# {kind}\n{stop_contract}', encoding='utf-8')
        imported = plan_task(
            context,
            SimpleNamespace(
                action='task-artifact',
                task_id=task_id,
                artifact_kind=kind,
                file_path=str(path),
                expected_task_revision=revision,
            ),
        )
        revision = imported['task']['task_revision']
    return plan_task(
        context,
        SimpleNamespace(
            action='task-status',
            task_id=task_id,
            status='ready_for_orchestration',
            expected_task_revision=revision,
        ),
    )['task']


def _complete_runtime_child(context, task_id: str, result: str) -> None:
    task = plan_task(context, SimpleNamespace(action='task-show', task_id=task_id))['task']
    loop_id = f'loop-{task_id}'
    plan_task(
        context,
        SimpleNamespace(
            action='task-bind-loop',
            task_id=task_id,
            loop_id=loop_id,
            expected_task_revision=task['task_revision'],
        ),
    )
    summary = Path(context.project.project_root) / 'rounds' / f'{task_id}.md'
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(f'round result: {result}\n', encoding='utf-8')
    plan_task(
        context,
        SimpleNamespace(
            action='task-import-round',
            task_id=task_id,
            loop_id=loop_id,
            result=result,
            file_path=str(summary),
            expected_task_revision=task['task_revision'],
        ),
    )
    round_path = (
        Path(context.project.project_root) / '.ccb' / 'runtime' / 'loops' / loop_id / 'round.json'
    )
    round_path.parent.mkdir(parents=True, exist_ok=True)
    round_path.write_text(
        json.dumps(
            {
                'schema': 'ccb.loop.round_state.v1',
                'task_id': task_id,
                'loop_id': loop_id,
                'round_result': result,
                'dispatch_source': 'ask_first_direct_execution',
                'release': {
                    'loop_topology_status': 'released',
                    'released_count': 2,
                    'retained_count': 0,
                    'release_incomplete_count': 0,
                },
            },
            sort_keys=True,
        )
        + '\n',
        encoding='utf-8',
    )


def _settle_runtime_detail_ready_child(context, task_id: str) -> dict[str, object]:
    root = Path(context.project.project_root)
    task = plan_task(context, SimpleNamespace(action='task-show', task_id=task_id))['task']
    notes = root / 'drafts' / f'{task_id}-orchestration-notes.md'
    notes.write_text(
        f'route: needs_detail\nTask: {task_id}\nExpected stop: detail_ready.\n',
        encoding='utf-8',
    )
    imported_notes = plan_task(
        context,
        SimpleNamespace(
            action='task-artifact',
            task_id=task_id,
            artifact_kind='orchestration_notes',
            file_path=str(notes),
            route='needs_detail',
            expected_task_revision=task['task_revision'],
        ),
    )
    revision = imported_notes['task']['task_revision']
    job_id = 'job-real-detailer'
    activation_path = root / '.ccb/runtime/loops/activations/act-real-detailer.json'
    activation_path.parent.mkdir(parents=True, exist_ok=True)
    activation_path.write_text(
        json.dumps(
            {
                'activation_id': 'act-real-detailer',
                'task_id': task_id,
                'task_revision': revision,
                'ask': {'target': 'task_detailer', 'job_id': job_id},
            }
        ),
        encoding='utf-8',
    )
    imported_artifacts: dict[str, dict[str, object]] = {}
    for kind, filename in (
        ('detail_design', 'task-detail-design.md'),
        ('detail_summary', 'brief-update-summary.md'),
        ('detail_packet', 'detail-packet.manifest.json'),
    ):
        source = root / '.ccb/runtime/role-output-imports' / job_id / filename
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f'{kind} for {task_id}\n', encoding='utf-8')
        imported = plan_task(
            context,
            SimpleNamespace(
                action='task-artifact',
                task_id=task_id,
                artifact_kind=kind,
                file_path=str(source),
                actor_source='loop_runner_role_output_import',
                actor='loop_runner',
                job_id=job_id,
                expected_task_revision=revision,
            ),
        )
        imported_artifacts[kind] = imported['artifact']
    trace_path = root / '.ccb/runtime/role-output-imports.jsonl'
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(
        json.dumps(
            {
                'action': 'imported_task_detailer_detail_authority',
                'task_id': task_id,
                'source_job': {'job_id': job_id},
                'artifacts': {
                    kind: {'sha256': artifact['sha256']}
                    for kind, artifact in imported_artifacts.items()
                },
            },
            sort_keys=True,
        )
        + '\n',
        encoding='utf-8',
    )
    settled = plan_task(
        context,
        SimpleNamespace(
            action='task-status',
            task_id=task_id,
            status='detail_ready',
            next_owner='planner',
            activation_reason='detail_ready_from_task_detailer',
            expected_task_revision=revision,
        ),
    )['task']
    authority = detail_ready_stop_contract_authority(settled, project_root=root)
    assert authority is not None
    return authority


def _persist_completed_transport_job(
    context,
    *,
    target: str,
    job_id: str,
    task_id: str,
    message: str,
    reply: str,
) -> None:
    request = MessageEnvelope(
        project_id=context.project.project_id,
        to_agent=target,
        from_actor='system',
        body=message,
        task_id=task_id,
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
        silence_on_success=target == 'planner',
    )
    JobStore(PathLayout(context.project.project_root)).append(
        JobRecord(
            job_id=job_id,
            submission_id=None,
            agent_name=target,
            provider='codex',
            request=request,
            status=JobStatus.COMPLETED,
            terminal_decision={'terminal': True, 'status': 'completed', 'reply': reply},
            cancel_requested_at=None,
            created_at='2026-07-13T00:00:00Z',
            updated_at='2026-07-13T00:00:01Z',
        )
    )


class RealFeedbackTransport:
    def __init__(self):
        self.terminals: dict[str, dict[str, object]] = {}
        self.persisted: dict[str, str] = {}
        self.submissions: list[object] = []

    def services(self):
        return SimpleNamespace(
            submit_ask=self.submit,
            persisted_terminal_watch=lambda _context, job_id: self.terminals.get(job_id),
            find_task_set_transport_job=(
                lambda _context, *, task_id, **_kwargs: self.persisted.get(task_id)
            ),
            find_task_set_retry_successor=lambda *_args, **_kwargs: None,
        )

    def submit(self, context, command):
        self.submissions.append(command)
        job_id = f'job_real_{len(self.submissions)}'
        self.persisted[command.task_id] = job_id
        return AskSummary(
            context.project.project_id,
            'submission-real',
            ({'agent_name': command.target, 'job_id': job_id},),
        )


class Harness:
    def __init__(self, intent: dict[str, object], *, notify: bool = True):
        self.intent = intent
        self.notify = notify
        self.terminals: dict[str, dict[str, object]] = {}
        self.persisted: dict[str, str] = {}
        self.submissions: list[object] = []
        self.imports: list[dict[str, object]] = []
        self.settlements: list[dict[str, object]] = []
        self.successors: dict[str, str] = {}
        self.next_job = 1

    def services(self):
        return SimpleNamespace(
            discover_task_set_closures=self.discover,
            plan_task=lambda *_args, **_kwargs: None,
            submit_ask=self.submit,
            persisted_terminal_watch=lambda _context, job_id: self.terminals.get(job_id),
            find_task_set_transport_job=self.find,
            find_task_set_retry_successor=self.retry_successor,
            apply_planner_feedback=self.apply,
            settle_task_set_feedback=self.settle,
            resolve_plan_revision=lambda *_args, **_kwargs: 'sha256:' + 'c' * 64,
        )

    def discover(self, _context, **_kwargs):
        return {'evaluated': [], 'pending': [self.intent]}

    def submit(self, _context, command):
        self.submissions.append(command)
        job_id = f'job_{self.next_job}'
        self.next_job += 1
        self.persisted[command.task_id] = job_id
        return AskSummary('project-test', 'submission-a', ({'agent_name': command.target, 'job_id': job_id},))

    def find(self, _context, *, task_id: str, **_kwargs):
        return self.persisted.get(task_id)

    def retry_successor(self, _context, source_job_id: str, **_kwargs):
        successor = self.successors.get(source_job_id)
        if successor is None:
            return None
        return {
            'message_id': f'msg-{source_job_id}',
            'source_attempt_id': f'att-{source_job_id}',
            'successor_attempt_id': f'att-{successor}',
            'retry_source_job_id': source_job_id,
            'retry_successor_job_id': successor,
            'retry_index': 1,
        }

    def apply(self, _context, _proposal, authority):
        self.imports.append(authority)
        return {'status': 'imported', 'import_id': 'import-a'}

    def settle(self, _context, **authority):
        self.settlements.append(authority)
        return {'status': 'feedback_closed'}


def test_mixed_terminal_closure_feedback_preserves_real_detail_ready_authority(
    tmp_path: Path,
) -> None:
    context = _context(tmp_path)
    plan_root = tmp_path / 'docs/plantree/plans/demo'
    plan_root.mkdir(parents=True, exist_ok=True)
    (plan_root / 'README.md').write_text('# Demo Plan\n', encoding='utf-8')
    _create_runtime_task(context, 'source-intake', ready=False)
    child_ids = ('child-pass', 'child-detail-ready', 'child-replan', 'child-blocked')
    for task_id in child_ids:
        _create_runtime_task(
            context,
            task_id,
            stop_at_detail_ready=task_id == 'child-detail-ready',
        )
    _complete_runtime_child(context, 'child-pass', 'pass')
    _complete_runtime_child(context, 'child-replan', 'replan_required')
    _complete_runtime_child(context, 'child-blocked', 'blocked')
    _settle_runtime_detail_ready_child(context, 'child-detail-ready')
    created = create_task_set_authority(
        context,
        plan_slug='demo',
        source_task_id='source-intake',
        source_request={
            'source_job_id': 'job-frontdesk-source',
            'sha256': hashlib.sha256(b'user request').hexdigest(),
            'bytes': len(b'user request'),
        },
        planner_job={
            'job_id': 'job-planner-source',
            'reply_sha256': hashlib.sha256(b'planner reply').hexdigest(),
        },
        children=[{'task_id': task_id, 'required': True} for task_id in child_ids],
        plan_task_fn=plan_task,
        task_set_id='mixed-terminal-set',
    )
    detail_before = plan_task(
        context,
        SimpleNamespace(action='task-show', task_id='child-detail-ready'),
    )['task']
    detail_authority_before = detail_ready_stop_contract_authority(
        detail_before,
        project_root=tmp_path,
    )
    assert detail_authority_before is not None

    evaluated = evaluate_task_set_closure(
        context,
        task_set_id='mixed-terminal-set',
        plan_task_fn=plan_task,
    )

    assert evaluated['status'] == 'closure_pending'
    assert evaluated['closure']['aggregate_result'] == 'replan_required'
    assert [
        (item['task_id'], item['status'], item['result'])
        for item in evaluated['closure']['ordered_children']
    ] == [
        ('child-pass', 'done', 'pass'),
        ('child-detail-ready', 'detail_ready', 'pass'),
        ('child-replan', 'replan_required', 'replan_required'),
        ('child-blocked', 'blocked', 'blocked'),
    ]
    detail_evidence = evaluated['closure']['ordered_children'][1]
    assert detail_evidence['authority']['artifact_kind'] == 'detail_ready_stop_contract'
    assert (
        detail_evidence['authority']['authority_digest']
        == detail_authority_before['authority_digest']
    )

    transport = RealFeedbackTransport()
    planner_pending = advance_task_set_feedback_runtime(context, transport.services())
    assert planner_pending['action'] == 'task_set_planner_backfill_pending'
    planner_command = transport.submissions[0]
    planner_reply = _mixed_terminal_planner_reply(
        created['task_set'],
        evaluated['closure'],
    )
    _persist_completed_transport_job(
        context,
        target='planner',
        job_id='job_real_1',
        task_id=planner_command.task_id,
        message=planner_command.message,
        reply=planner_reply,
    )
    transport.terminals['job_real_1'] = {'status': 'completed', 'reply': planner_reply}

    frontdesk_pending = advance_task_set_feedback_runtime(context, transport.services())
    assert frontdesk_pending['action'] == 'task_set_frontdesk_status_pending'
    frontdesk_command = transport.submissions[1]
    _persist_completed_transport_job(
        context,
        target='frontdesk',
        job_id='job_real_2',
        task_id=frontdesk_command.task_id,
        message=frontdesk_command.message,
        reply='delivered',
    )
    transport.terminals['job_real_2'] = {'status': 'completed', 'reply': 'delivered'}

    settled = advance_task_set_feedback_runtime(context, transport.services())
    replay = advance_task_set_feedback_runtime(context, transport.services())

    assert settled['action'] == 'task_set_feedback_closed'
    assert replay is None
    task_set_path = Path(created['task_set_path'])
    task_set = json.loads(task_set_path.read_text(encoding='utf-8'))
    assert task_set['state'] == 'replan_required'
    parent = plan_task(
        context,
        SimpleNamespace(action='task-show', task_id='source-intake'),
    )['task']
    assert parent['status'] == 'replan_required'
    assert parent['task_set_closure']['aggregate_result'] == 'replan_required'
    detail_after = plan_task(
        context,
        SimpleNamespace(action='task-show', task_id='child-detail-ready'),
    )['task']
    detail_authority_after = detail_ready_stop_contract_authority(
        detail_after,
        project_root=tmp_path,
    )
    assert detail_after == detail_before
    assert detail_authority_after == detail_authority_before
    runtime = json.loads(
        (
            tmp_path
            / '.ccb/runtime/task-sets/mixed-terminal-set/feedback-r1.json'
        ).read_text(encoding='utf-8')
    )
    assert runtime['stage'] == 'closed'
    assert runtime['notification'] == {'status': 'delivered', 'job_id': 'job_real_2'}
    settlement = json.loads(
        (
            task_set_path.parent / 'closure-settlement-r1.json'
        ).read_text(encoding='utf-8')
    )
    assert settlement['transport_ref']['frontdesk_effective_job_id'] == 'job_real_2'


def test_pending_planner_then_frontdesk_then_exact_once_close(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)

    planner_pending = advance_task_set_feedback_runtime(context, harness.services())
    assert planner_pending['action'] == 'task_set_planner_backfill_pending'
    assert planner_pending['pending_job_ids'] == ['job_1']
    assert harness.submissions[0].target == 'planner'
    assert harness.submissions[0].silence is True
    planner_envelope = json.loads(
        harness.submissions[0].message.split('```json\n', 1)[1].rsplit('\n```', 1)[0]
    )
    assert planner_envelope['closure_ref'] == {
        'path': 'docs/plantree/plans/demo/task-sets/set-a/closure.json',
        'closure_digest': 'sha256:' + 'b' * 64,
        'ordered_terminal_evidence_digest': _EVIDENCE_DIGEST,
    }

    harness.terminals['job_1'] = {'status': 'completed', 'reply': _planner_reply()}
    frontdesk_pending = advance_task_set_feedback_runtime(context, harness.services())
    assert frontdesk_pending['action'] == 'task_set_frontdesk_status_pending'
    assert frontdesk_pending['pending_job_ids'] == ['job_2']
    assert harness.submissions[1].target == 'frontdesk'
    assert harness.submissions[1].silence is False
    assert len(harness.imports) == 1

    harness.terminals['job_2'] = {'status': 'completed', 'reply': 'delivered'}
    closed = advance_task_set_feedback_runtime(context, harness.services())
    replay = advance_task_set_feedback_runtime(context, harness.services())
    assert closed['action'] == replay['action'] == 'task_set_feedback_closed'
    assert len(harness.submissions) == 2
    assert len(harness.imports) == 1
    assert len(harness.settlements) == 2


def test_planner_proposal_must_echo_exact_transport_closure_ref(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)
    advance_task_set_feedback_runtime(context, harness.services())
    reply = _planner_reply()
    payload = json.loads(reply.split('```json\n', 1)[1].rsplit('\n```', 1)[0])
    payload['evidence_refs'] = ['tasks/child-a/round_summary.md']
    payload['frontdesk_status']['evidence_refs'] = payload['evidence_refs']
    harness.terminals['job_1'] = {
        'status': 'completed',
        'reply': '**planner-backfill.json**\n```json\n' + json.dumps(payload) + '\n```\n',
    }

    with pytest.raises(ValueError, match='omits required evidence refs'):
        advance_task_set_feedback_runtime(context, harness.services())


def test_planner_and_frontdesk_retry_successors_resume_exactly_once(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)
    advance_task_set_feedback_runtime(context, harness.services())
    harness.terminals['job_1'] = {'status': 'failed', 'reply': 'source failed'}
    harness.successors['job_1'] = 'job_1_retry'
    harness.terminals['job_1_retry'] = {'status': 'completed', 'reply': _planner_reply()}

    planner_done = advance_task_set_feedback_runtime(context, harness.services())

    assert planner_done['action'] == 'task_set_frontdesk_status_pending'
    assert harness.imports[0]['planner_source_job_id'] == 'job_1'
    assert harness.imports[0]['planner_effective_job_id'] == 'job_1_retry'
    assert harness.imports[0]['planner_retry_lineage'] == [{
        'message_id': 'msg-job_1',
        'source_attempt_id': 'att-job_1',
        'successor_attempt_id': 'att-job_1_retry',
        'retry_source_job_id': 'job_1',
        'retry_successor_job_id': 'job_1_retry',
        'retry_index': 1,
    }]
    harness.terminals['job_2'] = {'status': 'incomplete', 'reply': 'delivery failed'}
    harness.successors['job_2'] = 'job_2_retry'
    harness.terminals['job_2_retry'] = {'status': 'completed', 'reply': 'delivered'}

    closed = advance_task_set_feedback_runtime(context, harness.services())

    assert closed['action'] == 'task_set_feedback_closed'
    settlement = harness.settlements[0]['transport_ref']
    assert settlement['frontdesk_source_job_id'] == 'job_2'
    assert settlement['frontdesk_effective_job_id'] == 'job_2_retry'
    assert settlement['frontdesk_retry_lineage'] == [{
        'message_id': 'msg-job_2',
        'source_attempt_id': 'att-job_2',
        'successor_attempt_id': 'att-job_2_retry',
        'retry_source_job_id': 'job_2',
        'retry_successor_job_id': 'job_2_retry',
        'retry_index': 1,
    }]
    assert len(harness.imports) == 1


def test_retry_successor_cycle_fails_closed(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)
    advance_task_set_feedback_runtime(context, harness.services())
    harness.terminals['job_1'] = {'status': 'failed'}
    harness.successors['job_1'] = 'job_retry'
    harness.terminals['job_retry'] = {'status': 'failed'}
    harness.successors['job_retry'] = 'job_1'

    with pytest.raises(RuntimeError, match='retry_lineage_cycle'):
        advance_task_set_feedback_runtime(context, harness.services())


@pytest.mark.parametrize('case', ('ambiguous', 'mismatched_task'))
def test_retry_successor_authority_rejects_ambiguous_or_mismatched_jobs(
    tmp_path: Path, case: str
) -> None:
    context = _context(tmp_path)
    store = JobStore(PathLayout(tmp_path))
    message = 'exact retry message'
    count = 2 if case == 'ambiguous' else 1
    for index in range(count):
        request = MessageEnvelope(
            project_id='project-test', to_agent='planner', from_actor='system',
            body=message,
            task_id='wrong-task' if case == 'mismatched_task' else 'task-a',
            reply_to=None, message_type='ask', delivery_scope=DeliveryScope.SINGLE,
        )
        store.append(JobRecord(
            job_id=f'job_retry_{index}', submission_id=None, agent_name='planner',
            provider='codex', request=request, status=JobStatus.QUEUED,
            terminal_decision=None, cancel_requested_at=None,
            created_at=f'2026-07-12T00:00:0{index}Z',
            updated_at=f'2026-07-12T00:00:0{index}Z',
            provider_options={'retry_source_job_id': 'job_source'},
        ))

    with pytest.raises(RuntimeError, match='source attempt authority missing'):
        _retry_successor_job(
            context,
            source_job_id='job_source', target='planner', task_id='task-a',
            message=message,
            message_sha256=hashlib.sha256(message.encode()).hexdigest(),
        )


def test_retry_successor_requires_attempt_message_authority_and_supports_chain(tmp_path: Path) -> None:
    context = _context(tmp_path)
    layout = PathLayout(tmp_path)
    message = 'exact retry message'
    MessageStore(layout).append(MessageRecord(
        message_id='msg-authority', origin_message_id=None, from_actor='system',
        target_scope='single', target_agents=('planner',), message_class='ask',
        retry_policy={'mode': 'auto', 'max_attempts': 3}, created_at='2026-07-12T00:00:00Z',
        updated_at='2026-07-12T00:00:03Z', message_state=MessageState.COMPLETED,
    ))
    attempts = AttemptStore(layout)
    jobs = ['job_source', 'job_retry_1', 'job_retry_2']
    for index, job_id in enumerate(jobs):
        attempts.append(AttemptRecord(
            attempt_id=f'att_{index}', message_id='msg-authority', agent_name='planner',
            provider='codex', job_id=job_id, retry_index=index, health_snapshot_ref=None,
            started_at=f'2026-07-12T00:00:0{index}Z', updated_at=f'2026-07-12T00:00:0{index + 1}Z',
            attempt_state=AttemptState.COMPLETED if index == 2 else AttemptState.FAILED,
        ))
        request = MessageEnvelope(
            project_id='project-test', to_agent='planner', from_actor='system', body=message,
            task_id='task-a', reply_to=None, message_type='ask', delivery_scope=DeliveryScope.SINGLE,
        )
        JobStore(layout).append(JobRecord(
            job_id=job_id, submission_id=None, agent_name='planner', provider='codex', request=request,
            status=JobStatus.COMPLETED if index == 2 else JobStatus.FAILED,
            terminal_decision={'terminal': True, 'status': 'completed' if index == 2 else 'failed', 'reply': ''},
            cancel_requested_at=None, created_at='2026-07-12T00:00:00Z',
            updated_at='2026-07-12T00:00:01Z',
        ))

    first = _retry_successor_job(
        context, source_job_id='job_source', target='planner', task_id='task-a',
        message=message, message_sha256=hashlib.sha256(message.encode()).hexdigest(),
    )
    second = _retry_successor_job(
        context, source_job_id='job_retry_1', target='planner', task_id='task-a',
        message=message, message_sha256=hashlib.sha256(message.encode()).hexdigest(),
    )

    assert first['retry_successor_job_id'] == 'job_retry_1'
    assert first['source_attempt_id'] == 'att_0'
    assert second['retry_successor_job_id'] == 'job_retry_2'
    assert second['retry_index'] == 2


@pytest.mark.parametrize('accepted_before_raise', [False, True])
def test_prepared_submission_crash_recovers_without_duplicate(
    tmp_path: Path,
    accepted_before_raise: bool,
) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent, notify=False)
    context = _context(tmp_path)
    original = harness.submit
    calls = 0

    def crashing_submit(context, command):
        nonlocal calls
        calls += 1
        if accepted_before_raise:
            original(context, command)
        raise RuntimeError('crash-window')

    services = harness.services()
    services.submit_ask = crashing_submit
    with pytest.raises(RuntimeError, match='crash-window'):
        advance_task_set_feedback_runtime(context, services)

    if accepted_before_raise:
        harness.terminals['job_1'] = {'status': 'completed', 'reply': _planner_reply(notify=False)}
    result = advance_task_set_feedback_runtime(context, harness.services())
    if accepted_before_raise:
        assert result['action'] == 'task_set_feedback_closed'
        assert calls == 1
    else:
        assert result['action'] == 'task_set_planner_backfill_pending'
        assert len(harness.submissions) == 1


def test_terminal_before_import_is_consumed_without_resubmit(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent, notify=False)
    context = _context(tmp_path)
    harness.persisted['task-set-feedback-intent-a'] = 'job_existing'
    harness.terminals['job_existing'] = {'status': 'completed', 'reply': _planner_reply(notify=False)}

    result = advance_task_set_feedback_runtime(context, harness.services())

    assert result['action'] == 'task_set_feedback_closed'
    assert harness.submissions == []
    assert len(harness.imports) == 1


def test_stale_revision_and_terminal_failure_are_visible(tmp_path: Path) -> None:
    intent, task_set = _authority(tmp_path)
    task_set['task_set_revision'] = 2
    Path(intent['task_set_path']).write_text(json.dumps(task_set), encoding='utf-8')
    harness = Harness(intent)
    with pytest.raises(RuntimeError, match='stale_revision'):
        advance_task_set_feedback_runtime(_context(tmp_path), harness.services())

    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)
    advance_task_set_feedback_runtime(context, harness.services())
    harness.terminals['job_1'] = {'status': 'failed', 'reply': 'provider failure'}
    failed = advance_task_set_feedback_runtime(context, harness.services())
    assert failed['loop_runner_status'] == 'blocked'
    assert failed['action'] == 'task_set_planner_backfill_failed'


def test_bound_job_authority_mismatch_fails_closed(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)
    advance_task_set_feedback_runtime(context, harness.services())
    harness.persisted['task-set-feedback-intent-a'] = 'job_lookalike'

    with pytest.raises(RuntimeError, match='bound_job_authority_mismatch'):
        advance_task_set_feedback_runtime(context, harness.services())


def test_frontdesk_terminal_failure_is_visible(tmp_path: Path) -> None:
    intent, _ = _authority(tmp_path)
    harness = Harness(intent)
    context = _context(tmp_path)
    advance_task_set_feedback_runtime(context, harness.services())
    harness.terminals['job_1'] = {'status': 'completed', 'reply': _planner_reply()}
    advance_task_set_feedback_runtime(context, harness.services())
    harness.terminals['job_2'] = {'status': 'cancelled', 'reply': ''}

    failed = advance_task_set_feedback_runtime(context, harness.services())

    assert failed['loop_runner_status'] == 'blocked'
    assert failed['action'] == 'task_set_frontdesk_status_failed'


def test_runner_advances_closure_before_idle(monkeypatch, tmp_path: Path) -> None:
    expected = {
        'loop_runner_status': 'pending',
        'action': 'task_set_planner_backfill_pending',
        'pending_job_ids': ['job_closure'],
    }
    monkeypatch.setattr('cli.services.loop_runner.find_first_actionable_task', lambda *_args, **_kwargs: None)
    services = SimpleNamespace(
        resume_multi_workgroup_scheduler=lambda *_args, **_kwargs: None,
        consume_activation_role_output=lambda *_args, **_kwargs: None,
        task_set_feedback=lambda *_args, **_kwargs: expected,
    )
    command = SimpleNamespace(task_id=None, consume_role_output=False)

    assert loop_runner_once(_context(tmp_path), command, services) == expected


def test_auto_runner_waits_for_closure_transport_and_continues(monkeypatch, tmp_path: Path) -> None:
    steps = iter(
        [
            {
                'loop_runner_status': 'pending',
                'action': 'task_set_planner_backfill_pending',
                'ask': {'target': 'planner', 'job_id': 'job_closure'},
                'pending_job_ids': ['job_closure'],
            },
            {'loop_runner_status': 'ok', 'action': 'task_set_feedback_closed'},
            {'loop_runner_status': 'idle', 'action': 'none', 'reason': 'no_actionable_task'},
        ]
    )
    monkeypatch.setattr('cli.services.loop_runner.loop_runner_once', lambda *_args, **_kwargs: next(steps))
    services = SimpleNamespace(
        persisted_terminal_watch=lambda *_args, **_kwargs: {'status': 'completed'},
    )
    command = ParsedLoopRunnerCommand(
        project=None,
        once=False,
        auto=True,
        poll_interval_s=0,
        max_steps=4,
    )

    result = loop_runner_auto(_context(tmp_path), command, services)

    assert result['action'] == 'auto_runner_finished'
    assert result['step_count'] == 3
    assert result['steps'][0]['pending_job_ids'] == ['job_closure']
