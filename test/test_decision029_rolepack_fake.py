from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from cli.services.ask_runtime.submission import _artifact_request_body
from cli.services.role_command_policy import claude_permission_allowlist, load_role_command_policy
from cli.services.plan_tasks import plan_task
from cli.services.task_set_closure import evaluate_task_set_closure
from provider_execution.fake import FakeProviderAdapter
from rolepacks.manifest import load_role_manifest
from storage.paths import PathLayout
from test_task_set_closure import _complete, _context, _create_set


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DRAFTS = REPO_ROOT / 'docs/plantree/plans/agentic-loop-workflow/drafts'
CORPUS_PATH = REPO_ROOT / 'test/fixtures/decision029_task_set_closure.v1.json'
RESULT_BY_AGGREGATE = {
    'pass': 'closure_complete',
    'partial': 'closure_partial',
    'replan_required': 'task_set_replanned',
    'blocked': 'closure_blocked',
}


def _corpus() -> dict[str, object]:
    return json.loads(CORPUS_PATH.read_text(encoding='utf-8'))


def _job(*, agent_name: str, body: str, task_id: str = 'decision029-closure') -> JobRecord:
    return JobRecord(
        job_id=f'job-{agent_name}', submission_id=None, agent_name=agent_name,
        provider='fake',
        request=MessageEnvelope(
            project_id='project-decision029', to_agent=agent_name,
            from_actor='system', body=body, task_id=task_id,
            reply_to=None, message_type='ask', delivery_scope=DeliveryScope.SINGLE,
        ),
        status=JobStatus.QUEUED, terminal_decision=None, cancel_requested_at=None,
        created_at='2026-07-12T00:00:00Z', updated_at='2026-07-12T00:00:00Z',
    )


def _planner_body(closure: dict[str, object]) -> str:
    envelope = {
        'schema': 'ccb.plan.task_set_closure_transport.v1',
        'closure': closure,
        'closure_ref': _closure_ref(closure),
        'closure_intent': {
            'intent_id': 'intent-decision029',
            'task_set_id': closure['task_set_id'],
            'task_set_revision': closure['task_set_revision'],
            'ordered_terminal_evidence_digest': closure['ordered_terminal_evidence_digest'],
            'closure_digest': closure['closure_digest'],
        },
    }
    return '**task-set-closure.json**\n```json\n' + json.dumps(envelope, sort_keys=True) + '\n```'


def _closure_ref(closure: dict[str, object]) -> dict[str, object]:
    return {
        'path': (
            'docs/plantree/plans/agentic-loop-workflow/task-sets/'
            f"{closure['task_set_id']}/closure.json"
        ),
        'closure_digest': closure['closure_digest'],
        'ordered_terminal_evidence_digest': closure['ordered_terminal_evidence_digest'],
    }


def _payload(reply: str, label: str) -> dict[str, object]:
    prefix = f'**{label}**\n```json\n'
    assert reply.startswith(prefix) and reply.endswith('\n```')
    return json.loads(reply[len(prefix):-4])


def _generated_closure(tmp_path: Path, results: list[str]) -> dict[str, object]:
    context = _context(tmp_path)
    specs = [(f'child-{index}', True) for index in range(len(results))]
    created = _create_set(context, specs)
    for (task_id, _required), result in zip(specs, results):
        _complete(context, task_id, result)
    evaluated = evaluate_task_set_closure(
        context,
        task_set_id=created['task_set']['task_set_id'],
    )
    assert evaluated['status'] == 'closure_pending'
    closure = evaluated['closure']
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', closure['expected_plan_revision'])
    return closure


def _generated_non_execution_closure(tmp_path: Path, *, result: str) -> dict[str, object]:
    context = _context(tmp_path)
    created = _create_set(context, [('child-no-execution', True)])
    kind = 'blocker_evidence' if result == 'blocked' else 'macro_adjustment_request'
    artifact = Path(context.project.project_root) / 'drafts' / f'{kind}.md'
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(f'# {kind}\n', encoding='utf-8')
    plan_task(context, SimpleNamespace(
        action='task-artifact', task_id='child-no-execution',
        artifact_kind=kind, file_path=str(artifact),
    ))
    plan_task(context, SimpleNamespace(
        action='task-status', task_id='child-no-execution', status=result,
        activation_reason='decision029_fixture',
    ))
    evaluated = evaluate_task_set_closure(
        context, task_set_id=created['task_set']['task_set_id'],
    )
    assert evaluated['status'] == 'closure_pending'
    closure = evaluated['closure']
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', closure['expected_plan_revision'])
    return closure


def _canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(',', ':'),
    ).encode('utf-8')
    return 'sha256:' + hashlib.sha256(encoded).hexdigest()


def _planner_reply(
    closure: dict[str, object], *, notification_required: bool = True,
) -> dict[str, object]:
    reply = FakeProviderAdapter(latency_seconds=0).start(
        _job(
            agent_name='planner', body=_planner_body(closure),
            task_id=(
                'decision029-closure' if notification_required
                else 'decision029-closure-no-notify'
            ),
        ),
        context=None,
        now='2026-07-12T00:00:00Z',
    ).reply
    return _payload(reply, 'planner-backfill.json')


def _assert_exact_closure_echo(proposal: dict[str, object], path: str) -> None:
    refs = proposal.get('evidence_refs')
    status = proposal.get('frontdesk_status')
    if not isinstance(refs, list) or path not in refs:
        raise ValueError('proposal omits closure_ref.path')
    if not isinstance(status, dict) or status.get('evidence_refs') != refs:
        raise ValueError('embedded Frontdesk status omits exact evidence refs')


def test_corpus_is_generator_backed_and_non_acceptance() -> None:
    corpus = _corpus()
    assert corpus['schema'] == 'ccb.decision029.fake_closure_scenarios.v2'
    assert corpus['generator'].endswith('evaluate_task_set_closure')
    assert corpus['closure_representation'] == 'worker2-frozen-digest-string'
    assert corpus['evidence_scope'] == 'source_fake_protocol_only_not_acceptance'
    assert corpus['transport_contract'] == 'exact-production-envelope-with-script-owned-closure_ref'
    retry = corpus['retry_authority_contract']
    assert retry['transport_fields'] == ['source_job_id', 'effective_job_id', 'retry_lineage']
    assert retry['retry_edge_fields'] == [
        'message_id', 'source_attempt_id', 'successor_attempt_id',
        'retry_source_job_id', 'retry_successor_job_id', 'retry_index',
    ]
    assert retry['authority'] == 'message-store-and-attempt-store-only-not-provider-options'


@pytest.mark.parametrize('scenario', _corpus()['scenarios'], ids=lambda case: case['case_id'])
def test_fake_planner_accepts_exact_production_closure(tmp_path: Path, scenario: dict[str, object]) -> None:
    closure = _generated_closure(tmp_path, scenario['child_results'])
    assert set(closure) == {
        'schema', 'schema_version', 'task_set_id', 'task_set_revision',
        'source_request', 'planner_job', 'expected_plan_revision', 'ordered_children',
        'ordered_terminal_evidence_digest', 'status', 'aggregate_result', 'reason',
        'created_at', 'closure_digest',
    }
    notification_required = scenario.get('fake_provider_semantics') != 'notification_not_required'
    proposal = _planner_reply(closure, notification_required=notification_required)
    assert proposal['expected_plan_revision'] == closure['expected_plan_revision']
    assert proposal['aggregate_result'] == scenario['aggregate_result']
    assert proposal['result'] == RESULT_BY_AGGREGATE[scenario['aggregate_result']]
    assert proposal['closure_evidence_digest'] == closure['ordered_terminal_evidence_digest']
    expected_refs = [
        *(f"task:{child['task_id']}@{child['task_revision']}#{child['evidence_digest']}"
          for child in closure['ordered_children']),
        _closure_ref(closure)['path'],
    ]
    assert proposal['evidence_refs'] == expected_refs
    assert proposal['frontdesk_status']['evidence_refs'] == expected_refs
    _assert_exact_closure_echo(proposal, str(_closure_ref(closure)['path']))
    assert proposal['frontdesk_status']['aggregate_result'] == scenario['aggregate_result']
    assert proposal['frontdesk_notification_required'] is notification_required
    assert 'accepted_scope' not in closure
    assert 'frontdesk_notification_required' not in closure


def test_fake_planner_schema_locks_digest_plan_revision_and_rejects_object(tmp_path: Path) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    assert isinstance(closure['expected_plan_revision'], str)
    assert _planner_reply(closure)['expected_plan_revision'] == closure['expected_plan_revision']
    old_shape = deepcopy(closure)
    old_shape['expected_plan_revision'] = {
        'schema': 'ccb.plan.revision.v1', 'files': [],
        'digest': closure['expected_plan_revision'],
    }
    old_shape['closure_digest'] = _canonical_digest({
        key: value for key, value in old_shape.items() if key != 'closure_digest'
    })
    with pytest.raises(ValueError, match='expected_plan_revision is not a digest'):
        _planner_reply(old_shape)


def test_notification_not_required_does_not_launder_non_success(tmp_path: Path) -> None:
    closure = _generated_closure(tmp_path, ['pass', 'blocked'])
    proposal = _planner_reply(closure, notification_required=False)
    assert proposal['frontdesk_notification_required'] is False
    assert proposal['aggregate_result'] == 'partial'
    assert proposal['result'] == 'closure_partial'
    assert proposal['unresolved_scope']


def test_fake_planner_rejects_unknown_transport_fields(tmp_path: Path) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    envelope = json.loads(_planner_body(closure).split('```json\n', 1)[1].rsplit('\n```', 1)[0])
    envelope['fake_provider_semantics'] = {'frontdesk_notification_required': False}
    body = '**task-set-closure.json**\n```json\n' + json.dumps(envelope) + '\n```'
    with pytest.raises(ValueError, match='transport fields'):
        FakeProviderAdapter(latency_seconds=0).start(
            _job(agent_name='planner', body=body), context=None,
            now='2026-07-12T00:00:00Z',
        )


@pytest.mark.parametrize(
    ('mutation', 'error'),
    (
        (lambda envelope: envelope.pop('closure_ref'), 'transport fields'),
        (lambda envelope: envelope['closure_ref'].update(extra=True), 'closure_ref fields'),
        (lambda envelope: envelope['closure_ref'].update(closure_digest='sha256:' + '0' * 64), 'closure_digest mismatch'),
        (lambda envelope: envelope['closure_ref'].update(ordered_terminal_evidence_digest='sha256:' + '0' * 64), 'ordered_terminal_evidence_digest mismatch'),
        (lambda envelope: envelope['closure_ref'].update(path='/docs/plantree/plans/demo/task-sets/set-a/closure.json'), 'closure_ref.path'),
        (lambda envelope: envelope['closure_ref'].update(path=''), 'closure_ref.path'),
        (lambda envelope: envelope['closure_ref'].update(path='../docs/plantree/plans/demo/task-sets/set-a/closure.json'), 'closure_ref.path'),
        (lambda envelope: envelope['closure_ref'].update(path='docs/plantree/plans/./task-sets/set-a/closure.json'), 'closure_ref.path'),
        (lambda envelope: envelope['closure_ref'].update(path=r'docs\plantree\plans\demo\task-sets\set-a\closure.json'), 'closure_ref.path'),
        (lambda envelope: envelope['closure_ref'].update(path='docs/plantree/plans/demo/task-sets/other/closure.json'), 'task_set_id mismatch'),
        (lambda envelope: envelope['closure_ref'].update(path='docs/plantree/plans/demo/alternate/set-a/closure.json'), 'closure_ref.path'),
    ),
)
def test_fake_planner_rejects_invalid_closure_ref(tmp_path: Path, mutation, error: str) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    envelope = json.loads(_planner_body(closure).split('```json\n', 1)[1].rsplit('\n```', 1)[0])
    mutation(envelope)
    body = '**task-set-closure.json**\n```json\n' + json.dumps(envelope) + '\n```'
    with pytest.raises(ValueError, match=error):
        FakeProviderAdapter(latency_seconds=0).start(
            _job(agent_name='planner', body=body), context=None,
            now='2026-07-12T00:00:00Z',
        )


def test_fake_protocol_contract_rejects_missing_closure_ref_echo(tmp_path: Path) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    proposal = _planner_reply(closure)
    proposal['evidence_refs'].remove(_closure_ref(closure)['path'])
    with pytest.raises(ValueError, match='omits closure_ref.path'):
        _assert_exact_closure_echo(proposal, str(_closure_ref(closure)['path']))


@pytest.mark.parametrize(
    ('field', 'value'),
    (
        ('missing', None),
        ('extra', True),
        ('path', '/tmp/request.txt'),
        ('path', '../request.txt'),
        ('path', r'..\request.txt'),
        ('bytes', -1),
        ('bytes', True),
        ('sha256', 'not-a-digest'),
        ('kind', ''),
        ('kind', 'totally-unknown'),
    ),
)
def test_fake_planner_rejects_malformed_source_body_artifact(
    tmp_path: Path, field: str, value: object,
) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    artifact = {
        'kind': 'ask-request', 'path': '.ccb/artifacts/request.txt',
        'bytes': 12, 'sha256': 'a' * 64,
    }
    if field == 'missing':
        artifact.pop('path')
    elif field == 'extra':
        artifact['unexpected'] = value
    else:
        artifact[field] = value
    closure['source_request']['body_artifact'] = artifact
    closure['closure_digest'] = _canonical_digest({
        key: item for key, item in closure.items() if key != 'closure_digest'
    })
    with pytest.raises(ValueError, match='body_artifact'):
        _planner_reply(closure)


@pytest.mark.parametrize('artifact_bytes', (0, 2**100))
def test_fake_planner_matches_nonnegative_integer_artifact_byte_contract(
    tmp_path: Path, artifact_bytes: int,
) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    closure['source_request']['body_artifact'] = {
        'kind': 'ask-request', 'path': '.ccb/artifacts/request.txt',
        'bytes': artifact_bytes, 'sha256': 'a' * 64,
    }
    closure['closure_digest'] = _canonical_digest({
        key: item for key, item in closure.items() if key != 'closure_digest'
    })
    assert _planner_reply(closure)['aggregate_result'] == 'pass'


def test_fake_planner_accepts_real_spilled_request_above_rpc_frame_limit(
    tmp_path: Path,
) -> None:
    body = 'x' * (1024 * 1024 + 1)
    _stub, produced = _artifact_request_body(
        PathLayout(tmp_path / 'artifact-project'), body,
        owner_id='job-frontdesk', force=True,
    )
    assert produced is not None
    assert produced['kind'] == 'ask-request'
    assert produced['bytes'] == len(body.encode('utf-8')) > 1024 * 1024
    closure = _generated_closure(tmp_path, ['pass'])
    closure['source_request']['body_artifact'] = {
        'kind': produced['kind'], 'path': '.ccb/artifacts/request.txt',
        'bytes': produced['bytes'], 'sha256': produced['sha256'],
    }
    closure['closure_digest'] = _canonical_digest({
        key: item for key, item in closure.items() if key != 'closure_digest'
    })
    assert _planner_reply(closure)['aggregate_result'] == 'pass'


@pytest.mark.parametrize(
    'mutation',
    ('missing_task_revision', 'missing_round', 'missing_release', 'missing_cleanup', 'unknown_child'),
)
def test_fake_planner_rejects_incomplete_or_extended_child_authority(tmp_path: Path, mutation: str) -> None:
    closure = deepcopy(_generated_closure(tmp_path, ['pass']))
    child = closure['ordered_children'][0]
    if mutation == 'missing_task_revision':
        child.pop('task_revision')
    elif mutation == 'missing_round':
        child['authority'].pop('round_path')
    elif mutation == 'missing_release':
        child['authority'].pop('release')
    elif mutation == 'missing_cleanup':
        child['authority'].pop('cleanup')
    else:
        child['unexpected'] = True
    with pytest.raises(ValueError, match='child'):
        _planner_reply(closure)


@pytest.mark.parametrize('result', ('blocked', 'replan_required'))
def test_fake_planner_accepts_production_non_execution_authority(tmp_path: Path, result: str) -> None:
    closure = _generated_non_execution_closure(tmp_path, result=result)
    authority = closure['ordered_children'][0]['authority']
    assert set(authority) == {'artifact_kind', 'artifact_digest', 'release', 'cleanup'}
    assert authority['release']['status'] == 'not_applicable_no_execution'
    assert _planner_reply(closure)['aggregate_result'] == result


def test_fake_planner_rejects_ordered_evidence_and_closure_digest_tampering(tmp_path: Path) -> None:
    closure = _generated_closure(tmp_path, ['pass'])
    terminal_tamper = deepcopy(closure)
    terminal_tamper['ordered_terminal_evidence_digest'] = 'sha256:' + '0' * 64
    with pytest.raises(ValueError, match='ordered terminal evidence digest mismatch'):
        _planner_reply(terminal_tamper)
    closure_tamper = deepcopy(closure)
    closure_tamper['reason'] = 'tampered'
    with pytest.raises(ValueError, match='closure digest mismatch'):
        _planner_reply(closure_tamper)


def test_nonterminal_or_system_failure_child_cannot_produce_pass(tmp_path: Path) -> None:
    closure = deepcopy(_generated_closure(tmp_path, ['pass']))
    closure['ordered_children'][0]['evidence_status'] = 'system_failure'
    with pytest.raises(ValueError, match='terminal evidence'):
        _planner_reply(closure)


def test_duplicate_closure_envelope_is_rejected(tmp_path: Path) -> None:
    body = _planner_body(_generated_closure(tmp_path, ['pass']))
    with pytest.raises(ValueError, match='exactly one fenced'):
        FakeProviderAdapter(latency_seconds=0).start(
            _job(agent_name='planner', body=body + '\n' + body), context=None,
            now='2026-07-12T00:00:00Z',
        )


def _frontdesk_status(tmp_path: Path, results: list[str]) -> dict[str, object]:
    return _planner_reply(_generated_closure(tmp_path, results))['frontdesk_status']


def _send_frontdesk(status: dict[str, object]) -> str:
    body = '**frontdesk-status.json**\n```json\n' + json.dumps(status, sort_keys=True) + '\n```'
    return FakeProviderAdapter(latency_seconds=0).start(
        _job(agent_name='frontdesk', body=body), context=None,
        now='2026-07-12T00:00:00Z',
    ).reply


def test_duplicate_frontdesk_envelope_is_rejected(tmp_path: Path) -> None:
    status = _frontdesk_status(tmp_path, ['pass'])
    section = '**frontdesk-status.json**\n```json\n' + json.dumps(status, sort_keys=True) + '\n```'
    with pytest.raises(ValueError, match='exactly one fenced'):
        FakeProviderAdapter(latency_seconds=0).start(
            _job(agent_name='frontdesk', body=section + '\n' + section), context=None,
            now='2026-07-12T00:00:00Z',
        )


def test_fake_frontdesk_preserves_validated_non_success_report(tmp_path: Path) -> None:
    status = _frontdesk_status(tmp_path, ['pass', 'blocked'])
    original = deepcopy(status)
    assert _send_frontdesk(status) == original['user_report_body']
    assert status == original


@pytest.mark.parametrize(
    ('mutation', 'error'),
    (
        (lambda status: status.update(notification_identity=''), 'notification_identity'),
        (lambda status: status['next_milestone'].update(kind='made_up'), 'kind'),
        (lambda status: status['next_milestone'].update(ref=''), 'ref'),
        (lambda status: status['next_milestone'].update(rationale=''), 'rationale'),
        (lambda status: status.update(unresolved_scope=[]), 'unresolved_scope'),
        (lambda status: status.update(extra='unknown'), 'fields'),
    ),
)
def test_fake_frontdesk_rejects_invalid_or_laundered_status(
    tmp_path: Path, mutation, error: str,
) -> None:
    status = _frontdesk_status(tmp_path, ['pass', 'blocked'])
    mutation(status)
    with pytest.raises(ValueError, match=error):
        _send_frontdesk(status)


def test_closure_rolepack_templates_use_digest_revision_and_exact_mode() -> None:
    planner_root = WORKFLOW_DRAFTS / 'agentroles.ccb_planner'
    backfill = json.loads((planner_root / 'templates/planner-backfill.json').read_text(encoding='utf-8'))
    detailer = json.loads(
        (planner_root / 'templates/planner-backfill-detailer-replan.json').read_text(encoding='utf-8')
    )
    skill = (planner_root / 'skills/planner-closure-backfill/SKILL.md').read_text(encoding='utf-8')
    assert backfill['mode'] == 'task_set_closure'
    assert re.fullmatch(r'sha256:[0-9a-f]{64}', backfill['expected_plan_revision'])
    assert backfill['aggregate_result'] == 'pass'
    assert backfill['result'] == 'closure_complete'
    assert list(backfill).count('frontdesk_status') == 1
    expected_path = 'docs/plantree/plans/example-plan/task-sets/task-set-a/closure.json'
    assert backfill['evidence_refs'] == [expected_path]
    assert backfill['frontdesk_status']['evidence_refs'] == [expected_path]
    assert detailer['mode'] == 'detailer_replan'
    assert detailer['aggregate_result'] == 'replan_required'
    assert detailer['result'] == 'task_set_replanned'
    assert detailer['frontdesk_status']['aggregate_result'] == detailer['aggregate_result']
    assert 'expected_plan_revision is a digest' in skill
    assert 'Treat `closure_ref` as script-owned input' in skill
    assert 'Never rewrite, normalize, infer, or reconstruct that path' in skill
    for mapping in ('pass -> closure_complete', 'partial -> closure_partial', 'replan_required -> task_set_replanned', 'blocked -> closure_blocked'):
        assert mapping in skill
    assert 'No PlanTree write' in skill


def test_planner_and_frontdesk_command_surfaces_remain_narrow() -> None:
    planner = load_role_manifest(WORKFLOW_DRAFTS / 'agentroles.ccb_planner')
    planner_policy = load_role_command_policy(planner)
    frontdesk = load_role_manifest(WORKFLOW_DRAFTS / 'agentroles.ccb_frontdesk')
    frontdesk_policy = load_role_command_policy(frontdesk)
    assert planner_policy is not None and planner_policy.allowed == ()
    assert planner_policy.provider_tools == () and claude_permission_allowlist(planner_policy) == ()
    assert {'shell_exec', 'generic_ccb', 'file_write', 'test_exec', 'wait', 'watch', 'arbitrary_target', 'notification_send'} <= set(planner_policy.forbidden_effects)
    assert frontdesk_policy is not None and len(frontdesk_policy.allowed) == 1
    assert frontdesk_policy.allowed[0].required_args[-1] == 'planner'
    assert frontdesk_policy.allowed[0].stdin_schema == 'inline:ccb.frontdesk.intake.v1'
    assert frontdesk_policy.provider_tools == (('codex', 'ccb_frontdesk_ask_planner'),)
    assert claude_permission_allowlist(frontdesk_policy) == ('Bash(ask --silence --compact --inline-request --task-id *)',)


def test_frontdesk_rolepack_renders_only_validated_status_and_never_forwards_it() -> None:
    root = WORKFLOW_DRAFTS / 'agentroles.ccb_frontdesk'
    combined = '\n'.join((root / path).read_text(encoding='utf-8') for path in (
        'memory.md', 'adapters/ccb/memory.md', 'skills/frontdesk-intake/SKILL.md',
        'templates/workflow-status-report.md',
    ))
    assert 'validated `ccb.planner.frontdesk_status.v1`' in combined
    assert 'byte-for-byte' in combined
    assert 'render only `user_report_body`' in combined.lower()
    assert 'never forward' in combined.lower()
    assert 'never mutate authority' in combined.lower()
