from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cli.services.planner_feedback import parse_planner_feedback_reply, planner_feedback_digest
from cli.services.planner_feedback_apply import apply_planner_feedback


def _digest(char: str) -> str:
    return 'sha256:' + char * 64


def _context(tmp_path: Path):
    root = tmp_path / 'project'
    plan = root / 'docs/plantree/plans/demo'
    plan.mkdir(parents=True)
    (plan / 'README.md').write_text('# Demo\n', encoding='utf-8')
    return SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='p'))


def _proposal(
    plan_revision: str, *, identity: str = 'set-a', identity_revision: int = 1
):
    evidence = [f'docs/plantree/plans/demo/task-sets/{identity}/closure.json']
    status = {
        'schema': 'ccb.planner.frontdesk_status.v1', 'notification_identity': f'{identity}-r1',
        'aggregate_result': 'pass', 'accepted_scope': ['landed'], 'unresolved_scope': [],
        'blockers': [], 'next_milestone': {'kind': 'workflow_terminal', 'ref': 'done', 'rationale': 'Done.'},
        'evidence_refs': evidence, 'user_report_body': 'Done.',
    }
    payload = {
        'schema': 'ccb.planner.backfill_proposal.v1', 'mode': 'task_set_closure',
        'expected_plan_revision': plan_revision, 'task_or_task_set_id': identity,
        'task_or_task_set_revision': identity_revision, 'closure_evidence_digest': _digest('a'),
        'aggregate_result': 'pass', 'result': 'closure_complete', 'brief_summary': 'Closed.',
        'roadmap_transitions': [{'id': 'm1', 'status': 'done', 'summary': 'Landed.', 'evidence_refs': evidence}],
        'todo_transitions': [{'id': 't1', 'status': 'done', 'summary': 'Checked.', 'evidence_refs': evidence}],
        'decision_refs': ['decisions/029.md'], 'open_question_refs': [], 'evidence_refs': evidence,
        'accepted_scope': ['landed'], 'unresolved_scope': [], 'blockers': [], 'replan_inputs': [],
        'next_milestone': status['next_milestone'], 'frontdesk_notification_required': True,
        'frontdesk_status': status,
    }
    return parse_planner_feedback_reply('**planner-backfill.json**\n```json\n' + json.dumps(payload) + '\n```\n')


def _authority_files(context, authority: dict[str, object]) -> None:
    identity = str(authority['task_set_id'])
    root = Path(context.project.project_root) / f'docs/plantree/plans/demo/task-sets/{identity}'
    root.mkdir(parents=True)
    (root / 'task-set.json').write_text(json.dumps({
        'task_set_id': identity, 'task_set_revision': authority['task_set_revision'], 'state': 'closure_pending',
        'plan_slug': 'demo',
        'plan_revision': {'digest': authority['expected_plan_revision']},
    }), encoding='utf-8')
    (root / 'closure.json').write_text(json.dumps({
        'task_set_id': identity, 'task_set_revision': authority['task_set_revision'],
        'closure_digest': authority['closure_digest'],
        'ordered_terminal_evidence_digest': authority['ordered_terminal_evidence_digest'],
        'aggregate_result': 'pass',
    }), encoding='utf-8')


def _run_apply(context, *, task_set_revision: int = 1):
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision, identity_revision=task_set_revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': task_set_revision,
        'closure_intent_id': f'tsi-a{task_set_revision}',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': f'job-planner-{task_set_revision}',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    return service.apply_planner_feedback(context, proposal, authority)


def test_apply_is_revision_fenced_persisted_and_idempotent(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services.planner_feedback_apply import current_plan_revision
    revision = current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)

    first = apply_planner_feedback(context, proposal, authority)
    replay = apply_planner_feedback(context, proposal, authority)

    assert first['status'] == replay['status'] == 'imported'
    assert replay['idempotent'] is True
    backfill = Path(first['planner_backfill_path'])
    assert backfill.is_file()
    assert json.loads(backfill.read_text())['authority']['planner_job_id'] == 'job-planner'
    assert '<!-- ccb-planner-backfill:set-a:r1:brief:start -->' in (
        Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md'
    ).read_text()


def test_apply_rejects_revision_conflict_before_write(tmp_path: Path) -> None:
    context = _context(tmp_path)
    proposal = _proposal(_digest('f'))
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': _digest('f'), 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    with pytest.raises(ValueError, match='revision conflict'):
        apply_planner_feedback(context, proposal, authority)
    assert not list(Path(context.project.project_root).rglob('planner-backfill.json'))


@pytest.mark.parametrize('crash_on_write', (2, 3))
def test_apply_recovers_after_each_partial_target_write_exactly_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, crash_on_write: int,
) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    original = service.atomic_write_text
    writes = 0

    def crash_after_partial_write(path, text):
        nonlocal writes
        writes += 1
        if writes == crash_on_write:
            raise RuntimeError('injected crash')
        return original(path, text)

    monkeypatch.setattr(service, 'atomic_write_text', crash_after_partial_write)
    with pytest.raises(RuntimeError, match='injected crash'):
        service.apply_planner_feedback(context, proposal, authority)
    monkeypatch.setattr(service, 'atomic_write_text', original)

    recovered = service.apply_planner_feedback(context, proposal, authority)
    assert recovered['status'] == 'imported'
    assert Path(recovered['planner_backfill_path']).is_file()
    for target in json.loads(Path(recovered['transaction_path']).read_text())['targets']:
        assert (Path(context.project.project_root) / target['path']).read_text() == target['target_text']


def test_projection_preflight_rejects_later_target_conflict_without_partial_write(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    plan_root = Path(context.project.project_root) / 'docs/plantree/plans/demo'
    transaction = service._derive_transaction(context, plan_root, proposal, authority, persisted=None)
    roadmap = plan_root / 'roadmap.md'
    roadmap.write_text('concurrent roadmap edit\n', encoding='utf-8')

    with pytest.raises(ValueError, match='file revision conflict'):
        service.apply_plan_projection_targets(context, transaction, write=service.atomic_write_text)

    assert not (plan_root / 'brief.md').exists()
    assert roadmap.read_text(encoding='utf-8') == 'concurrent roadmap edit\n'
    assert not (plan_root / 'TODO.md').exists()


def test_same_plan_revision_competitor_is_stale_and_has_no_success_record(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    first_proposal = _proposal(revision, identity='set-a')
    first_authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner-a',
        'planner_feedback_digest': planner_feedback_digest(first_proposal), 'plan_slug': 'demo',
    }
    second_proposal = _proposal(revision, identity='set-b')
    second_authority = {
        'task_set_id': 'set-b', 'task_set_revision': 1, 'closure_intent_id': 'tsi-b',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner-b',
        'planner_feedback_digest': planner_feedback_digest(second_proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, first_authority)
    _authority_files(context, second_authority)
    service.apply_planner_feedback(context, first_proposal, first_authority)
    projected = (Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md').read_text()

    with pytest.raises(ValueError, match='revision conflict'):
        service.apply_planner_feedback(context, second_proposal, second_authority)

    plan_root = Path(context.project.project_root) / 'docs/plantree/plans/demo'
    assert (plan_root / 'brief.md').read_text() == projected
    assert not (plan_root / 'task-sets/set-b/planner-backfill-r1.json').exists()


def test_persisted_transaction_rejects_arbitrary_target_and_tampering(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    transaction = service._derive_transaction(
        context,
        Path(context.project.project_root) / 'docs/plantree/plans/demo',
        proposal,
        authority,
        persisted=None,
    )
    transaction['targets'][0]['path'] = 'unrelated-user-file.txt'
    transaction['transaction_digest'] = service._semantic_digest(transaction, omit='transaction_digest')
    path = Path(context.project.project_root) / 'docs/plantree/plans/demo/task-sets/set-a/planner-backfill-r1.transaction.json'
    path.write_text(json.dumps(transaction), encoding='utf-8')

    with pytest.raises(ValueError, match='target path authority'):
        service.apply_planner_feedback(context, proposal, authority)
    assert not (Path(context.project.project_root) / 'unrelated-user-file.txt').exists()


@pytest.mark.parametrize('tamper', ('extra_field', 'target_body', 'transaction_digest', 'duplicate_path'))
def test_persisted_transaction_rejects_semantic_tampering(
    tmp_path: Path, tamper: str
) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    plan_root = Path(context.project.project_root) / 'docs/plantree/plans/demo'
    tx = service._derive_transaction(context, plan_root, proposal, authority, persisted=None)
    if tamper == 'extra_field':
        tx['unexpected'] = True
    elif tamper == 'target_body':
        tx['targets'][0]['target_text'] += 'attacker\n'
    elif tamper == 'transaction_digest':
        tx['transaction_digest'] = _digest('f')
    else:
        tx['targets'][1]['path'] = tx['targets'][0]['path']
        tx['transaction_digest'] = service._semantic_digest(tx, omit='transaction_digest')
    path = plan_root / 'task-sets/set-a/planner-backfill-r1.transaction.json'
    path.write_text(json.dumps(tx), encoding='utf-8')

    with pytest.raises(ValueError):
        service.apply_planner_feedback(context, proposal, authority)


def test_user_marker_collision_is_not_replaced(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    readme = Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md'
    user_text = '# Demo\n\n<!-- ccb-planner-backfill:set-a:r1:brief:start -->\nUSER OWNED\n<!-- ccb-planner-backfill:set-a:r1:brief:end -->\n'
    readme.write_text(user_text, encoding='utf-8')
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    with pytest.raises(ValueError, match='marker|transaction authority'):
        service.apply_planner_feedback(context, proposal, authority)
    assert readme.read_text(encoding='utf-8') == user_text


def test_replay_rejects_projected_file_drift(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    service.apply_planner_feedback(context, proposal, authority)
    roadmap = Path(context.project.project_root) / 'docs/plantree/plans/demo/roadmap.md'
    roadmap.write_text(roadmap.read_text() + 'drift\n', encoding='utf-8')
    with pytest.raises(ValueError, match='revision conflict|projected target drift'):
        service.apply_planner_feedback(context, proposal, authority)


def test_later_task_set_revision_uses_distinct_transaction_and_backfill(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision1 = service.current_plan_revision(context, 'demo')
    proposal1 = _proposal(revision1)
    authority1 = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a1',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision1, 'planner_job_id': 'job-planner-1',
        'planner_feedback_digest': planner_feedback_digest(proposal1), 'plan_slug': 'demo',
    }
    _authority_files(context, authority1)
    first = service.apply_planner_feedback(context, proposal1, authority1)

    task_set_root = Path(context.project.project_root) / 'docs/plantree/plans/demo/task-sets/set-a'
    revision2 = service.current_plan_revision(context, 'demo')
    task_set = json.loads((task_set_root / 'task-set.json').read_text())
    task_set.update({'task_set_revision': 2, 'plan_revision': {'digest': revision2}})
    (task_set_root / 'task-set.json').write_text(json.dumps(task_set), encoding='utf-8')
    closure = json.loads((task_set_root / 'closure.json').read_text())
    closure.update({'task_set_revision': 2})
    (task_set_root / 'closure.json').write_text(json.dumps(closure), encoding='utf-8')
    proposal2 = _proposal(revision2, identity_revision=2)
    authority2 = {
        'task_set_id': 'set-a', 'task_set_revision': 2, 'closure_intent_id': 'tsi-a2',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision2, 'planner_job_id': 'job-planner-2',
        'planner_feedback_digest': planner_feedback_digest(proposal2), 'plan_slug': 'demo',
    }
    second = service.apply_planner_feedback(context, proposal2, authority2)

    assert first['planner_backfill_path'].endswith('planner-backfill-r1.json')
    assert second['planner_backfill_path'].endswith('planner-backfill-r2.json')
    assert Path(first['planner_backfill_path']).is_file()
    assert Path(second['planner_backfill_path']).is_file()
    brief = (Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md').read_text()
    assert '<!-- ccb-planner-backfill:set-a:r1:brief:start -->' in brief
    assert '<!-- ccb-planner-backfill:set-a:r2:brief:start -->' in brief


@pytest.mark.parametrize('tamper', ('extra_field', 'backfill_digest'))
def test_replay_rejects_backfill_schema_or_digest_tampering(
    tmp_path: Path, tamper: str
) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    imported = service.apply_planner_feedback(context, proposal, authority)
    path = Path(imported['planner_backfill_path'])
    record = json.loads(path.read_text())
    if tamper == 'extra_field':
        record['unexpected'] = True
    else:
        record['backfill_digest'] = _digest('f')
    path.write_text(json.dumps(record), encoding='utf-8')

    with pytest.raises(ValueError, match='persisted authority'):
        service.apply_planner_feedback(context, proposal, authority)


@pytest.mark.parametrize(
    ('files', 'expected_targets', 'absent'),
    (
        ({'brief.md': 'brief\n', 'roadmap.md': 'roadmap\n', 'TODO.md': 'todo\n'},
         ('brief.md', 'roadmap.md', 'TODO.md'), ('Roadmap.md', 'todo.md')),
        ({'README.md': 'readme\n', 'roadmap.md': 'roadmap\n', 'todo.md': 'todo\n'},
         ('brief.md', 'roadmap.md', 'todo.md'), ('Roadmap.md', 'TODO.md')),
        ({'brief.md': 'brief\n'},
         ('brief.md', 'roadmap.md', 'TODO.md'), ('Roadmap.md', 'todo.md')),
        ({'brief.md': 'brief\n', 'Roadmap.md': 'roadmap\n', 'TODO.md': 'todo\n'},
         ('brief.md', 'Roadmap.md', 'TODO.md'), ('roadmap.md', 'todo.md')),
    ),
)
def test_real_plan_layout_selects_one_frozen_surface_per_semantic(
    tmp_path: Path,
    files: dict[str, str],
    expected_targets: tuple[str, ...],
    absent: tuple[str, ...],
) -> None:
    context = _context(tmp_path)
    plan_root = Path(context.project.project_root) / 'docs/plantree/plans/demo'
    for name in ('README.md', 'brief.md', 'roadmap.md', 'Roadmap.md', 'TODO.md', 'todo.md'):
        path = plan_root / name
        if path.exists():
            path.unlink()
    for name, body in files.items():
        (plan_root / name).write_text(body, encoding='utf-8')

    imported = _run_apply(context)
    transaction = json.loads(Path(imported['transaction_path']).read_text())
    actual_names = {path.name for path in plan_root.iterdir()}

    assert tuple(Path(item['path']).name for item in transaction['targets']) == expected_targets
    assert all(name in actual_names for name in expected_targets)
    assert all(name not in actual_names for name in absent)


@pytest.mark.parametrize(
    'files',
    (
        ('roadmap.md', 'Roadmap.md'),
        ('TODO.md', 'todo.md'),
    ),
)
def test_case_duplicate_semantic_files_are_rejected(
    tmp_path: Path, files: tuple[str, str]
) -> None:
    context = _context(tmp_path)
    plan_root = Path(context.project.project_root) / 'docs/plantree/plans/demo'
    (plan_root / 'brief.md').write_text('brief\n', encoding='utf-8')
    for name in files:
        (plan_root / name).write_text(name + '\n', encoding='utf-8')
    actual_names = {path.name for path in plan_root.iterdir()}
    if not all(name in actual_names for name in files):
        pytest.skip('filesystem does not support case-distinct semantic files')

    with pytest.raises(ValueError, match='ambiguous semantic files'):
        _run_apply(context)


@pytest.mark.parametrize('name', ('README.md', 'brief.md', 'roadmap.md', 'TODO.md'))
@pytest.mark.parametrize('outside', (False, True))
def test_plan_surface_symlinks_never_modify_link_targets(
    tmp_path: Path, name: str, outside: bool
) -> None:
    context = _context(tmp_path)
    root = Path(context.project.project_root)
    plan_root = root / 'docs/plantree/plans/demo'
    link = plan_root / name
    if link.exists() or link.is_symlink():
        link.unlink()
    target = (tmp_path / 'outside.txt') if outside else (root / 'unrelated.txt')
    target.write_text('USER CONTENT\n', encoding='utf-8')
    link.symlink_to(target)

    with pytest.raises(ValueError, match='symlink path is forbidden'):
        _run_apply(context)

    assert target.read_text(encoding='utf-8') == 'USER CONTENT\n'
    assert not list(plan_root.glob('task-sets/set-a/planner-backfill-r1.transaction.json'))


def test_plan_root_symlink_is_rejected_before_authority_write(tmp_path: Path) -> None:
    context = _context(tmp_path)
    root = Path(context.project.project_root)
    plan_root = root / 'docs/plantree/plans/demo'
    target = root / 'unrelated-plan'
    plan_root.rename(target)
    plan_root.symlink_to(target, target_is_directory=True)
    before = (target / 'README.md').read_text(encoding='utf-8')

    with pytest.raises(ValueError, match='symlink path is forbidden'):
        _run_apply(context)

    assert (target / 'README.md').read_text(encoding='utf-8') == before


@pytest.mark.parametrize(
    ('marker_text', 'reason'),
    (
        ('<!-- ccb-planner-backfill:foreign:r1:brief:start -->\nx\n'
         '<!-- ccb-planner-backfill:foreign:r1:brief:end -->\n', 'authority unreadable'),
        ('<!-- ccb-planner-backfill:set-a:r2:brief:start -->\nx\n'
         '<!-- ccb-planner-backfill:set-a:r2:brief:end -->\n', 'foreign or future'),
        ('<!-- ccb-planner-backfill:set-a:r1:brief:start -->\nx\n', 'unmatched'),
        ('<!-- ccb-planner-backfill:set-a:r1:brief:bogus -->\n', 'malformed'),
        ('<!-- ccb-planner-backfill:set-a:r1:brief:start -->\n'
         '<!-- ccb-planner-backfill:set-a:r1:brief:start -->\n'
         '<!-- ccb-planner-backfill:set-a:r1:brief:end -->\n'
         '<!-- ccb-planner-backfill:set-a:r1:brief:end -->\n', 'nested'),
    ),
)
def test_foreign_future_malformed_and_nested_markers_are_rejected(
    tmp_path: Path, marker_text: str, reason: str
) -> None:
    context = _context(tmp_path)
    brief = Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md'
    original = 'USER PREFIX\n' + marker_text + 'USER SUFFIX\n'
    brief.write_text(original, encoding='utf-8')

    with pytest.raises(ValueError, match=reason):
        _run_apply(context)

    assert brief.read_text(encoding='utf-8') == original


def test_all_target_preimages_are_validated_before_first_write(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision)
    authority = {
        'task_set_id': 'set-a', 'task_set_revision': 1, 'closure_intent_id': 'tsi-a',
        'closure_digest': _digest('c'), 'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)
    plan_root = Path(context.project.project_root) / 'docs/plantree/plans/demo'
    transaction = service._derive_transaction(
        context, plan_root, proposal, authority, persisted=None
    )
    tx_path = plan_root / 'task-sets/set-a/planner-backfill-r1.transaction.json'
    tx_path.write_text(json.dumps(transaction), encoding='utf-8')
    (plan_root / 'TODO.md').write_text('concurrent user file\n', encoding='utf-8')

    with pytest.raises(ValueError, match='file revision conflict'):
        service.apply_planner_feedback(context, proposal, authority)

    assert not (plan_root / 'brief.md').exists()
    assert not (plan_root / 'roadmap.md').exists()


def test_two_authoritative_task_sets_coexist_on_same_plan_surfaces(tmp_path: Path) -> None:
    context = _context(tmp_path)
    from cli.services import planner_feedback_apply as service
    _run_apply(context)
    revision = service.current_plan_revision(context, 'demo')
    proposal = _proposal(revision, identity='set-b')
    authority = {
        'task_set_id': 'set-b', 'task_set_revision': 1,
        'closure_intent_id': 'tsi-b1', 'closure_digest': _digest('c'),
        'ordered_terminal_evidence_digest': _digest('a'),
        'expected_plan_revision': revision, 'planner_job_id': 'job-planner-b1',
        'planner_feedback_digest': planner_feedback_digest(proposal), 'plan_slug': 'demo',
    }
    _authority_files(context, authority)

    imported = service.apply_planner_feedback(context, proposal, authority)

    assert Path(imported['planner_backfill_path']).is_file()
    brief = (Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md').read_text()
    assert '<!-- ccb-planner-backfill:set-a:r1:brief:start -->' in brief
    assert '<!-- ccb-planner-backfill:set-b:r1:brief:start -->' in brief


def test_forged_foreign_marker_without_own_authority_is_rejected(tmp_path: Path) -> None:
    context = _context(tmp_path)
    brief = Path(context.project.project_root) / 'docs/plantree/plans/demo/brief.md'
    forged = (
        '<!-- ccb-planner-backfill:set-forged:r1:brief:start -->\nFORGED\n'
        '<!-- ccb-planner-backfill:set-forged:r1:brief:end -->\n'
    )
    brief.write_text(forged, encoding='utf-8')

    with pytest.raises(ValueError, match='authority unreadable|prior marker authority'):
        _run_apply(context)
    assert brief.read_text(encoding='utf-8') == forged
