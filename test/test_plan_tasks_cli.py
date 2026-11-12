from __future__ import annotations

from contextlib import contextmanager
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import cli.services.planner_task_set_import_transaction as import_transaction

from cli.context import CliContextBuilder
from cli.models import ParsedPlanTaskCommand
from cli.parser import CliParser
from cli.phase2 import maybe_handle_phase2
from cli.services.plan_tasks import find_first_actionable_task, plan_task
from cli.services.planner_task_set_import_transaction import (
    PlannerTaskSetImportConflict,
    authority_trace,
    commit,
    prepare,
    runner_transaction_committed,
    transaction_digest,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _project_with_plan(tmp_path: Path) -> Path:
    project_root = tmp_path / 'repo-plan-tasks'
    (project_root / '.ccb').mkdir(parents=True)
    _write(
        project_root / '.ccb' / 'ccb.config',
        '''version = 2
entry_window = "ccb-user"

[windows]
ccb-user = "bootstrap:codex"

[loop.capacity]
enabled = true
max_nodes = 4

[loop.role_profiles.coder]
role = "agentroles.coder"
provider = "codex"
workspace_mode = "git-worktree"
max_instances = 2

[loop.role_profiles.code_reviewer]
role = "agentroles.code_reviewer"
provider = "codex"
workspace_mode = "git-worktree"
max_instances = 2
''',
    )
    _write(project_root / 'docs' / 'plantree' / 'plans' / 'demo-plan' / 'README.md', '# Demo Plan\n')
    return project_root


def _make_ready_task(project_root: Path, *, task_id: str = 'task-001') -> None:
    drafts = project_root / 'drafts'
    for name in ('task_packet', 'execution_contract'):
        _write(drafts / f'{name}.md', f'{name}\n')
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Bridge task',
            '--task-id',
            task_id,
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    for kind in ('task_packet', 'execution_contract'):
        code, _payload, _out, err = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                task_id,
                '--kind',
                kind,
                '--file',
                str(drafts / f'{kind}.md'),
                '--json',
            ],
            cwd=project_root,
        )
        assert code == 0, err
    code, payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', task_id, '--status', 'ready_for_orchestration', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['status'] == 'ready_for_orchestration'
    assert payload['task']['next_owner'] == 'orchestrator'


def _run_phase2(argv: list[str], *, cwd: Path) -> tuple[int, dict[str, object], str, str]:
    stdout = StringIO()
    stderr = StringIO()
    code = maybe_handle_phase2(argv, cwd=cwd, stdout=stdout, stderr=stderr)
    out_text = stdout.getvalue()
    payload = json.loads(out_text) if out_text.strip().startswith('{') else {}
    return code, payload, out_text, stderr.getvalue()


def _committed_transaction_task(tmp_path: Path, *, job_id: str = 'job-runner-gate'):
    project_root = _project_with_plan(tmp_path)
    context = CliContextBuilder().build(
        ParsedPlanTaskCommand(project=None, action='task-show', task_id='gate-child', json_output=True),
        cwd=project_root, bootstrap_if_missing=False,
    )
    identity = {
        'project_id': context.project.project_id, 'plan_slug': 'demo-plan',
        'activation_id': 'act-gate', 'source_task_id': 'source-gate',
        'source_request': {'source_job_id': 'job-source', 'bytes': 4, 'sha256': 'a' * 64},
        'planner_job_id': job_id, 'planner_reply_sha256': 'b' * 64,
        'task_set_id': 'ts-gate',
        'ordered_children': [{'task_id': 'gate-child', 'required': True}],
    }
    transaction = prepare(context, identity=identity)
    trace = authority_trace(transaction, source_job={'job_id': job_id})
    created = plan_task(context, SimpleNamespace(
        action='task-create', plan_slug='demo-plan', title='Gate child',
        task_id='gate-child', authority_trace=trace,
    ))
    bound = plan_task(context, SimpleNamespace(
        action='task-bind-task-set', task_id='gate-child', task_set_id='ts-gate',
        task_set_revision=1, binding_role='child', required=True, order=0,
        expected_task_revision=1,
    ))
    committed = commit(context, transaction, authority={
        'task_set_id': 'ts-gate', 'task_set_revision': 1,
        'children': [{'task_id': 'gate-child', 'task_revision': 1,
                      'task_set': bound['task']['task_set']}],
    })
    return project_root, context, committed, bound['task']


def test_planner_task_set_import_transaction_fences_runner_until_commit(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    context = CliContextBuilder().build(
        ParsedPlanTaskCommand(project=None, action='task-show', task_id='tx-child', json_output=True),
        cwd=project_root,
        bootstrap_if_missing=False,
    )
    identity = {
        'project_id': context.project.project_id,
        'plan_slug': 'demo-plan',
        'activation_id': 'act-tx',
        'source_task_id': 'source-tx',
        'source_request': {'source_job_id': 'job-source', 'bytes': 4, 'sha256': 'a' * 64},
        'planner_job_id': 'job-planner-tx',
        'planner_reply_sha256': 'b' * 64,
        'task_set_id': 'ts-test',
        'ordered_children': [{'task_id': 'tx-child'}],
    }
    transaction = prepare(context, identity=identity)
    trace = authority_trace(
        transaction,
        source_job={'job_id': 'job-planner-tx', 'reply_sha256': 'b' * 64},
    )
    plan_task(context, SimpleNamespace(
        action='task-create', plan_slug='demo-plan', title='Transaction child',
        task_id='tx-child', authority_trace=trace,
    ))
    for kind in ('task_packet', 'execution_contract'):
        source = project_root / 'drafts' / f'{kind}.md'
        _write(source, f'{kind}\n')
        plan_task(context, SimpleNamespace(
            action='task-artifact', task_id='tx-child', artifact_kind=kind, file_path=str(source),
        ))
    plan_task(context, SimpleNamespace(
        action='task-status', task_id='tx-child', status='ready_for_orchestration',
    ))
    bound = plan_task(context, SimpleNamespace(
        action='task-bind-task-set', task_id='tx-child', task_set_id='ts-test',
        task_set_revision=1, binding_role='child', required=True, order=0,
        expected_task_revision=1,
    ))

    assert find_first_actionable_task(context, task_id='tx-child') is None
    commit(context, transaction, authority={
        'task_set_id': 'ts-test', 'task_set_revision': 1,
        'children': [{'task_id': 'tx-child', 'task_revision': 1, 'task_set': bound['task']['task_set']}],
    })
    assert find_first_actionable_task(context, task_id='tx-child')['record']['task_id'] == 'tx-child'


def test_planner_import_journal_directory_is_durable_before_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_plan(tmp_path)
    context = CliContextBuilder().build(
        ParsedPlanTaskCommand(project=None, action='task-show', task_id='unused', json_output=True),
        cwd=project_root,
        bootstrap_if_missing=False,
    )
    events: list[str] = []
    real_ensure = import_transaction.ensure_durable_directory
    real_lock = import_transaction.file_lock

    def tracking_ensure(path):
        events.append('durable-directory')
        return real_ensure(path)

    @contextmanager
    def tracking_lock(path):
        events.append('lock')
        with real_lock(path):
            yield

    monkeypatch.setattr(import_transaction, 'ensure_durable_directory', tracking_ensure)
    monkeypatch.setattr(import_transaction, 'file_lock', tracking_lock)

    prepare(context, identity={
        'planner_job_id': 'job-durable-order',
        'task_set_id': 'ts-durable-order',
        'ordered_children': [],
    })

    assert events[:2] == ['durable-directory', 'lock']


def test_planner_task_set_import_transaction_ref_cannot_redirect_runner(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    context = CliContextBuilder().build(
        ParsedPlanTaskCommand(project=None, action='task-show', task_id='tx-redirect', json_output=True),
        cwd=project_root,
        bootstrap_if_missing=False,
    )
    transaction = prepare(context, identity={
        'project_id': context.project.project_id, 'plan_slug': 'demo-plan',
        'activation_id': 'act-tx', 'source_task_id': 'source-tx',
        'source_request': {'source_job_id': 'job-source', 'bytes': 4, 'sha256': 'a' * 64},
        'planner_job_id': 'job-planner-redirect', 'planner_reply_sha256': 'b' * 64,
        'task_set_id': 'ts-test', 'ordered_children': [{'task_id': 'tx-redirect'}],
    })
    trace = authority_trace(transaction, source_job={'job_id': 'job-planner-redirect'})
    trace['planner_task_set_import_transaction']['journal_ref'] = '.ccb/runtime/elsewhere.json'
    plan_task(context, SimpleNamespace(
        action='task-create', plan_slug='demo-plan', title='Redirect child',
        task_id='tx-redirect', authority_trace=trace,
    ))
    assert find_first_actionable_task(context, task_id='tx-redirect') is None


def test_planner_task_set_import_same_job_different_reply_is_durable_failure(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    context = CliContextBuilder().build(
        ParsedPlanTaskCommand(project=None, action='task-show', task_id='unused', json_output=True),
        cwd=project_root,
        bootstrap_if_missing=False,
    )
    identity = {
        'project_id': context.project.project_id, 'plan_slug': 'demo-plan',
        'activation_id': 'act-conflict', 'source_task_id': 'source-conflict',
        'source_request': {'source_job_id': 'job-source', 'bytes': 4, 'sha256': 'a' * 64},
        'planner_job_id': 'job-planner-conflict', 'planner_reply_sha256': 'b' * 64,
        'task_set_id': 'ts-conflict', 'ordered_children': [{'task_id': 'child-a'}],
    }
    first = prepare(context, identity=identity)
    assert prepare(context, identity=identity)['transaction_digest'] == first['transaction_digest']
    with pytest.raises(PlannerTaskSetImportConflict, match='identity_conflict'):
        prepare(context, identity={**identity, 'planner_reply_sha256': 'c' * 64})
    journal = json.loads(
        (project_root / first['journal_ref']).read_text(encoding='utf-8')
    )
    assert journal['status'] == 'failed'
    assert journal['identity'] == identity
    assert journal['conflicts'][-1]['observed_identity']['planner_reply_sha256'] == 'c' * 64


def test_committed_planner_task_set_import_rejects_conflict_without_downgrade(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    context = CliContextBuilder().build(
        ParsedPlanTaskCommand(project=None, action='task-show', task_id='unused', json_output=True),
        cwd=project_root, bootstrap_if_missing=False,
    )
    identity = {
        'project_id': context.project.project_id, 'plan_slug': 'demo-plan',
        'activation_id': 'act-committed', 'source_task_id': 'source-committed',
        'source_request': {'source_job_id': 'job-source', 'bytes': 4, 'sha256': 'a' * 64},
        'planner_job_id': 'job-planner-committed', 'planner_reply_sha256': 'b' * 64,
        'task_set_id': 'ts-committed',
        'ordered_children': [{'task_id': 'child-a', 'required': True}],
    }
    transaction = prepare(context, identity=identity)
    binding = {'schema': 'ccb.plan.task_set_binding.v1', 'task_set_id': 'ts-committed',
               'task_set_revision': 1, 'binding_role': 'child', 'bound_task_revision': 1,
               'required': True, 'order': 0}
    committed = commit(context, transaction, authority={
        'task_set_id': 'ts-committed', 'task_set_revision': 1,
        'children': [{'task_id': 'child-a', 'task_revision': 1, 'task_set': binding}],
    })
    with pytest.raises(PlannerTaskSetImportConflict, match='identity_conflict'):
        prepare(context, identity={**identity, 'planner_reply_sha256': 'c' * 64})
    journal = json.loads((project_root / committed['journal_ref']).read_text(encoding='utf-8'))
    assert journal == committed
    conflict_path = (project_root / committed['journal_ref']).with_name(
        'planner-task-set-import.transaction.conflicts.json'
    )
    conflicts = json.loads(conflict_path.read_text(encoding='utf-8'))
    assert conflicts['transaction_digest'] == committed['transaction_digest']
    assert conflicts['conflicts'][-1]['observed_identity']['planner_reply_sha256'] == 'c' * 64


@pytest.mark.parametrize(
    'mutation',
    ('missing', 'prepared', 'failed', 'corrupt', 'foreign_task', 'missing_membership',
     'duplicate_membership', 'tampered_authority', 'tampered_binding'),
)
def test_runner_transaction_gate_fails_closed_for_invalid_authority(tmp_path: Path, mutation: str) -> None:
    project_root, _context, committed, task = _committed_transaction_task(tmp_path)
    journal_path = project_root / committed['journal_ref']
    candidate = dict(task)
    record = json.loads(journal_path.read_text(encoding='utf-8'))
    if mutation == 'missing':
        journal_path.unlink()
    elif mutation in {'prepared', 'failed'}:
        record['status'] = mutation
        _write(journal_path, json.dumps(record))
    elif mutation == 'corrupt':
        _write(journal_path, '{not-json')
    elif mutation == 'foreign_task':
        candidate['task_id'] = 'foreign-task'
    elif mutation == 'missing_membership':
        record['identity']['ordered_children'] = []
        record['transaction_digest'] = transaction_digest(record['identity'])
        _write(journal_path, json.dumps(record))
    elif mutation == 'duplicate_membership':
        record['identity']['ordered_children'].append(dict(record['identity']['ordered_children'][0]))
        record['transaction_digest'] = transaction_digest(record['identity'])
        _write(journal_path, json.dumps(record))
    elif mutation == 'tampered_authority':
        record['authority']['children'][0]['task_id'] = 'other-child'
        _write(journal_path, json.dumps(record))
    elif mutation == 'tampered_binding':
        candidate['task_set'] = {**candidate['task_set'], 'task_set_id': 'ts-other'}
    assert runner_transaction_committed(project_root, candidate) is False


@pytest.mark.parametrize('target', ('journal', 'lock', 'parent'))
def test_runner_transaction_gate_rejects_symlink_layout(tmp_path: Path, target: str) -> None:
    project_root, _context, committed, task = _committed_transaction_task(
        tmp_path, job_id=f'job-symlink-{target}'
    )
    journal_path = project_root / committed['journal_ref']
    external = tmp_path / 'external'
    external.mkdir()
    if target == 'journal':
        copy = external / journal_path.name
        copy.write_bytes(journal_path.read_bytes())
        journal_path.unlink()
        journal_path.symlink_to(copy)
    elif target == 'lock':
        lock = journal_path.with_name('planner-task-set-import.transaction.lock')
        lock.unlink()
        lock.symlink_to(external / 'lock')
    else:
        job_dir = journal_path.parent
        moved = external / job_dir.name
        job_dir.rename(moved)
        job_dir.symlink_to(moved, target_is_directory=True)
    assert runner_transaction_committed(project_root, task) is False


def test_plan_parser_supports_v1_task_commands() -> None:
    parser = CliParser()

    assert parser.parse(
        ['plan', 'task-create', '--plan', 'demo-plan', '--title', 'Ship slice', '--task-id', 'task-001', '--json']
    ) == ParsedPlanTaskCommand(
        project=None,
        action='task-create',
        plan_slug='demo-plan',
        title='Ship slice',
        task_id='task-001',
        json_output=True,
    )
    assert parser.parse(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-001',
            '--kind',
            'orchestration_notes',
            '--file',
            'drafts/notes.md',
            '--route',
            'direct_execution',
            '--json',
        ]
    ) == ParsedPlanTaskCommand(
        project=None,
        action='task-artifact',
        task_id='task-001',
        artifact_kind='orchestration_notes',
        file_path='drafts/notes.md',
        route='direct_execution',
        json_output=True,
    )
    assert parser.parse(
        [
            'plan',
            'task-status',
            '--task',
            'task-001',
            '--status',
            'ready_for_orchestration',
            '--next-owner',
            'orchestrator',
            '--activation-reason',
            'contract_imported',
            '--json',
        ]
    ) == ParsedPlanTaskCommand(
        project=None,
        action='task-status',
        task_id='task-001',
        status='ready_for_orchestration',
        next_owner='orchestrator',
        activation_reason='contract_imported',
        json_output=True,
    )
    assert parser.parse(['plan', 'task-show', '--task', 'task-001', '--json']) == ParsedPlanTaskCommand(
        project=None,
        action='task-show',
        task_id='task-001',
        json_output=True,
    )
    assert parser.parse(['plan', 'task-list', '--plan', 'demo-plan', '--json']) == ParsedPlanTaskCommand(
        project=None,
        action='task-list',
        plan_slug='demo-plan',
        json_output=True,
    )
    assert parser.parse(['plan', 'breadcrumb', '--task', 'task-001']) == ParsedPlanTaskCommand(
        project=None,
        action='breadcrumb',
        task_id='task-001',
    )
    assert parser.parse(
        ['plan', 'task-bind-loop', '--task', 'task-001', '--loop', 'loop-a', '--json']
    ) == ParsedPlanTaskCommand(
        project=None,
        action='task-bind-loop',
        task_id='task-001',
        loop_id='loop-a',
        json_output=True,
    )
    assert parser.parse(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-001',
            '--loop',
            'loop-a',
            '--result',
            'pass',
            '--report',
            'round.json',
            '--json',
        ]
    ) == ParsedPlanTaskCommand(
        project=None,
        action='task-import-round',
        task_id='task-001',
        loop_id='loop-a',
        result='pass',
        file_path='round.json',
        json_output=True,
    )


def test_plan_task_imports_validated_single_node_orchestration_bundle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    role_store = tmp_path / 'roles'
    for role_id, default_name in (
        ('agentroles.coder', 'coder'),
        ('agentroles.code_reviewer', 'code_reviewer'),
    ):
        _write(
            role_store / 'installed' / role_id / 'current' / 'role.toml',
            f'id = "{role_id}"\nversion = "0.1.0"\n\n[identity]\ndefault_agent_name = "{default_name}"\n',
        )
    monkeypatch.setenv('AGENT_ROLES_STORE', str(role_store))
    project_root = _project_with_plan(tmp_path)
    _make_ready_task(project_root, task_id='bundle-task')
    drafts = project_root / 'drafts'
    notes_path = drafts / 'orchestration_notes.md'
    _write(notes_path, 'route: direct_execution\norchestration_notes: one bounded workgroup\n')
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'bundle-task',
            '--kind',
            'orchestration_notes',
            '--file',
            str(notes_path),
            '--route',
            'direct_execution',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    task_root = 'docs/plantree/plans/demo-plan/tasks/bundle-task'
    execution_contract_ref = f'{task_root}/execution_contract.md'
    candidate = {
        'schema': 'ccb.loop.orchestration_bundle_candidate.v1',
        'task_id': 'bundle-task',
        'bundle_revision': 1,
        'selection': {
            'workgroup_count': 1,
            'complexity': 'atomic',
            'cutability': 'none',
            'execution_shape': 'single_unit',
            'rationale': 'The task is one tightly coupled implementation unit.',
        },
        'nodes': [
            {
                'node_id': 'node-001',
                'workgroup_id': 'wg-001',
                'worker_profile': 'coder',
                'reviewer_profile': 'code_reviewer',
                'depends_on': [],
                'parallel_group': 'wave-1',
                'work_packet': 'Implement the bounded task and report verification.',
                'allowed_paths': [],
                'acceptance_refs': [execution_contract_ref],
                'verification_refs': [execution_contract_ref],
                'integration_order': 10,
            }
        ],
        'integration': {
            'verification_refs': [execution_contract_ref],
            'project_root_verification_refs': [execution_contract_ref],
        },
        'policy': {
            'max_node_rework_rounds': 1,
            'on_required_node_failure': 'partial_or_blocked',
            'on_structural_failure': 'replan_required',
        },
    }
    candidate_path = drafts / 'orchestration_bundle.candidate.json'
    _write(candidate_path, json.dumps(candidate, indent=2) + '\n')

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'bundle-task',
            '--kind',
            'orchestration_bundle',
            '--file',
            str(candidate_path),
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 0, err
    artifact = payload['artifact']
    assert artifact['bundle_schema'] == 'ccb.loop.orchestration_bundle.v1'
    assert artifact['bundle_revision'] == 1
    assert artifact['node_count'] == 1
    assert artifact['node_ids'] == ['node-001']
    bundle_path = project_root / artifact['path']
    bundle = json.loads(bundle_path.read_text(encoding='utf-8'))
    assert bundle['task_id'] == 'bundle-task'
    assert bundle['task_revision'] == 1
    assert bundle['capacity_digest']
    assert 'source' not in bundle
    assert artifact['bundle_source'] == 'script_owned_import'
    assert bundle['nodes'][0]['work_packet_ref'] == f'{task_root}/orchestration/work-packets/node-001.md'
    assert (project_root / bundle['nodes'][0]['work_packet_ref']).read_text(encoding='utf-8') == (
        'Implement the bounded task and report verification.\n'
    )
    code, repeated, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'bundle-task',
            '--kind',
            'orchestration_bundle',
            '--file',
            str(candidate_path),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert repeated['idempotent'] is True
    assert repeated['artifact']['bundle_digest'] == artifact['bundle_digest']

    packet_path = project_root / bundle['nodes'][0]['work_packet_ref']
    original_packet = packet_path.read_text(encoding='utf-8')
    candidate['nodes'][0]['work_packet'] = 'Conflicting packet must not become current.'
    conflicting_path = drafts / 'orchestration_bundle.conflicting.json'
    _write(conflicting_path, json.dumps(candidate, indent=2) + '\n')
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'bundle-task',
            '--kind',
            'orchestration_bundle',
            '--file',
            str(conflicting_path),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'conflicts with existing bundle' in err
    assert packet_path.read_text(encoding='utf-8') == original_packet

    candidate['bundle_revision'] = 3
    skipped_path = drafts / 'orchestration_bundle.skipped.json'
    _write(skipped_path, json.dumps(candidate, indent=2) + '\n')
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'bundle-task',
            '--kind',
            'orchestration_bundle',
            '--file',
            str(skipped_path),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'revision must increase exactly once: expected 2, got 3' in err

    candidate['bundle_revision'] = 2
    next_path = drafts / 'orchestration_bundle.next.json'
    _write(next_path, json.dumps(candidate, indent=2) + '\n')
    code, advanced, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'bundle-task',
            '--kind',
            'orchestration_bundle',
            '--file',
            str(next_path),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert advanced['idempotent'] is False
    assert advanced['artifact']['bundle_revision'] == 2


def test_plan_task_semantic_revision_is_monotonic_idempotent_and_running_fenced(
    tmp_path: Path,
) -> None:
    project_root = _project_with_plan(tmp_path)
    drafts = project_root / 'drafts'
    _write(drafts / 'task-packet-v1.md', 'task packet v1\n')
    _write(drafts / 'task-packet-v1-copy.md', 'task packet v1\n')
    _write(drafts / 'task-packet-v2.md', 'task packet v2\n')
    _write(drafts / 'task-packet-v3.md', 'task packet v3\n')
    _write(drafts / 'execution-contract.md', 'execution contract\n')
    code, created, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Revision fencing',
            '--task-id',
            'task-revision',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert created['task']['task_revision'] == 1

    def import_packet(path: Path) -> tuple[int, dict[str, object], str]:
        rc, payload, _stdout, stderr = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                'task-revision',
                '--kind',
                'task_packet',
                '--file',
                str(path),
                '--json',
            ],
            cwd=project_root,
        )
        return rc, payload, stderr

    code, first, err = import_packet(drafts / 'task-packet-v1.md')
    assert code == 0, err
    assert first['task']['task_revision'] == 1
    assert first['idempotent'] is False

    code, repeated, err = import_packet(drafts / 'task-packet-v1-copy.md')
    assert code == 0, err
    assert repeated['task']['task_revision'] == 1
    assert repeated['idempotent'] is True

    code, replaced, err = import_packet(drafts / 'task-packet-v2.md')
    assert code == 0, err
    assert replaced['task']['task_revision'] == 2
    assert replaced['idempotent'] is False

    code, repeated_v2, err = import_packet(drafts / 'task-packet-v2.md')
    assert code == 0, err
    assert repeated_v2['task']['task_revision'] == 2
    assert repeated_v2['idempotent'] is True

    code, _contract, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-revision',
            '--kind',
            'execution_contract',
            '--file',
            str(drafts / 'execution-contract.md'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    context_command = ParsedPlanTaskCommand(
        project=None,
        action='task-show',
        task_id='task-revision',
        json_output=True,
    )
    context = CliContextBuilder().build(context_command, cwd=project_root, bootstrap_if_missing=False)
    with pytest.raises(ValueError, match='stale managed activation task_revision: expected 1, current 2'):
        plan_task(
            context,
            SimpleNamespace(
                action='task-status',
                task_id='task-revision',
                status='ready_for_orchestration',
                expected_task_revision=1,
            ),
        )
    shown = plan_task(context, SimpleNamespace(action='task-show', task_id='task-revision'))
    assert shown['task']['status'] == 'draft'
    assert shown['task']['task_revision'] == 2
    code, _ready, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-revision', '--status', 'ready_for_orchestration', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    code, bound, _out, err = _run_phase2(
        ['plan', 'task-bind-loop', '--task', 'task-revision', '--loop', 'loop-revision', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert bound['task']['status'] == 'running'

    code, _blocked, err = import_packet(drafts / 'task-packet-v3.md')
    assert code == 1
    assert 'cannot replace semantic artifact while task is bound to running loop' in err


def test_plan_task_legacy_revision_reads_as_one_and_materializes_on_mutation(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _make_ready_task(project_root, task_id='legacy-revision')
    index_path = project_root / 'docs' / 'plantree' / 'plans' / 'demo-plan' / 'tasks' / 'index.json'
    index = json.loads(index_path.read_text(encoding='utf-8'))
    index['tasks'][0].pop('task_revision', None)
    _write(index_path, json.dumps(index, indent=2) + '\n')

    code, shown, _out, err = _run_phase2(
        ['plan', 'task-show', '--task', 'legacy-revision', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert shown['task']['task_revision'] == 1

    risk = project_root / 'drafts' / 'risk.md'
    _write(risk, 'risk evidence\n')
    code, mutated, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'legacy-revision',
            '--kind',
            'risk',
            '--file',
            str(risk),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert mutated['task']['task_revision'] == 1
    persisted = json.loads(index_path.read_text(encoding='utf-8'))
    assert persisted['tasks'][0]['task_revision'] == 1


def test_plan_task_ready_for_orchestration_can_pause_for_clarification(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _make_ready_task(project_root, task_id='external-sync-contract')

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            'external-sync-contract',
            '--status',
            'needs_clarification',
            '--activation-reason',
            'needs_clarification_from_task_detailer',
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 0, err
    assert payload['task']['status'] == 'needs_clarification'
    assert payload['task']['owner'] == 'task_detailer'
    assert payload['task']['next_owner'] == 'task_detailer'
    assert payload['task']['activation_reason'] == 'needs_clarification_from_task_detailer'


def test_plan_task_packet_flow_enforces_review_before_ready(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    drafts = project_root / 'drafts'
    _write(drafts / 'requirements.md', 'requirements\n')
    _write(drafts / 'acceptance.md', 'acceptance\n')
    _write(drafts / 'verification.md', 'verification\n')
    _write(drafts / 'handoff.md', 'handoff\n')
    _write(drafts / 'review.md', 'review\n')

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Ship planner slice',
            '--task-id',
            'task-001',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['plan_task_status'] == 'ok'
    assert payload['task_id'] == 'task-001'
    assert payload['status'] == 'draft'

    for kind, file_name in (
        ('requirements', 'requirements.md'),
        ('acceptance', 'acceptance.md'),
        ('verification', 'verification.md'),
        ('handoff', 'handoff.md'),
    ):
        code, payload, _out, err = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                'task-001',
                '--kind',
                kind,
                '--file',
                str(drafts / file_name),
                '--json',
            ],
            cwd=project_root,
        )
        assert code == 0, err
        assert payload['artifact']['kind'] == kind
        assert payload['artifact']['path'].startswith('docs/plantree/plans/demo-plan/tasks/task-001/')

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-001', '--status', 'ready', '--json'],
        cwd=project_root,
    )
    assert code == 1
    assert 'ready requires artifacts: review' in err

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-001',
            '--kind',
            'review',
            '--file',
            str(drafts / 'review.md'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['artifact']['sha256']

    code, payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-001', '--status', 'ready', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['status'] == 'ready'
    assert payload['task']['owner'] == 'loop_runner'

    code, payload, _out, err = _run_phase2(['plan', 'task-show', '--task', 'task-001', '--json'], cwd=project_root)
    assert code == 0, err
    assert payload['task']['status'] == 'ready'
    assert set(payload['task']['artifacts']) == {'acceptance', 'handoff', 'requirements', 'review', 'verification'}

    code, payload, _out, err = _run_phase2(['plan', 'task-list', '--plan', 'demo-plan', '--json'], cwd=project_root)
    assert code == 0, err
    assert payload['task_count'] == 1
    assert payload['tasks'][0]['task_id'] == 'task-001'

    code, _payload, out, err = _run_phase2(['plan', 'breadcrumb', '--task', 'task-001'], cwd=project_root)
    assert code == 0, err
    assert 'Task: task-001' in out
    assert 'Status: ready' in out
    assert 'Artifacts: acceptance, handoff, requirements, review, verification' in out

    assert not (project_root / '.ccb' / 'runtime').exists()


def test_plan_task_phase2_anchors_gate_ready_for_orchestration(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    drafts = project_root / 'drafts'
    _write(drafts / 'task_packet.md', '# Task Packet\n')
    _write(drafts / 'execution_contract.md', '# Execution Contract\n')
    _write(drafts / 'orchestration_notes.md', '# Orchestration Notes\n')

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Phase 2 anchors',
            '--task-id',
            'task-phase2',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['status'] == 'draft'
    assert payload['task']['next_owner'] == 'planner'
    assert payload['task']['activation_reason'] == 'task_created'

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-phase2',
            '--kind',
            'task_packet',
            '--file',
            str(drafts / 'task_packet.md'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['artifact']['artifact_kind'] == 'task_packet'
    assert payload['artifact']['artifact_path'].endswith('/task_packet.md')

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-phase2', '--status', 'ready_for_orchestration', '--json'],
        cwd=project_root,
    )
    assert code == 1
    assert 'ready_for_orchestration requires artifacts: execution_contract' in err

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-phase2',
            '--kind',
            'orchestration_notes',
            '--file',
            str(drafts / 'orchestration_notes.md'),
            '--route',
            'direct_execution',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err

    code, shown, _out, err = _run_phase2(['plan', 'task-show', '--task', 'task-phase2', '--json'], cwd=project_root)
    assert code == 0, err
    assert shown['task']['status'] == 'draft'
    assert shown['task']['next_owner'] == 'planner'
    assert shown['task']['artifacts']['orchestration_notes']['orchestrator_route'] == 'direct_execution'

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-phase2',
            '--kind',
            'execution_contract',
            '--file',
            str(drafts / 'execution_contract.md'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err

    code, ready, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            'task-phase2',
            '--status',
            'ready_for_orchestration',
            '--next-owner',
            'orchestrator',
            '--activation-reason',
            'contract_imported',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert ready['status'] == 'ready_for_orchestration'
    assert ready['task']['next_owner'] == 'orchestrator'
    assert ready['task']['activation_reason'] == 'contract_imported'
    assert ready['task']['artifacts']['task_packet']['path'].endswith('/task_packet.md')
    assert ready['task']['artifacts']['execution_contract']['path'].endswith('/execution_contract.md')


def test_plan_task_phase2_rejects_unknown_machine_values(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    drafts = project_root / 'drafts'
    _write(drafts / 'task_packet.md', '# Task Packet\n')
    _write(drafts / 'execution_contract.md', '# Execution Contract\n')
    _write(drafts / 'orchestration_notes.md', '# Orchestration Notes\n')

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Reject invalid machine fields',
            '--task-id',
            'task-invalid-machine',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-invalid-machine',
            '--kind',
            'orchestration_notes',
            '--file',
            str(drafts / 'orchestration_notes.md'),
            '--route',
            'teleport',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'unknown orchestrator route' in err

    for kind in ('task_packet', 'execution_contract'):
        code, _payload, _out, err = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                'task-invalid-machine',
                '--kind',
                kind,
                '--file',
                str(drafts / f'{kind}.md'),
                '--json',
            ],
            cwd=project_root,
        )
        assert code == 0, err

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            'task-invalid-machine',
            '--status',
            'ready_for_orchestration',
            '--next-owner',
            'worker',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'unknown plan task next_owner' in err

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            'task-invalid-machine',
            '--status',
            'ready_for_orchestration',
            '--next-owner',
            'planner',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'requires next_owner orchestrator' in err


def test_plan_task_artifact_records_actor_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = _project_with_plan(tmp_path)
    artifact = project_root / 'drafts' / 'requirements.md'
    _write(artifact, 'requirements\n')
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'planner')
    monkeypatch.setenv('CCB_ACTOR_ROLE', 'agentroles.ccb_planner')
    monkeypatch.setenv('CCB_JOB_ID', 'job_planner123')

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Actor metadata',
            '--task-id',
            'task-actor',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-actor',
            '--kind',
            'requirements',
            '--file',
            str(artifact),
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 0, err
    assert payload['artifact']['actor'] == {
        'source': 'cli',
        'actor': 'planner',
        'role': 'agentroles.ccb_planner',
        'job_id': 'job_planner123',
    }
    assert payload['task']['artifacts']['requirements']['actor']['job_id'] == 'job_planner123'


def test_plan_task_artifact_imports_plan_brief_and_task_detail_docs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_plan(tmp_path)
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'plan_script')
    monkeypatch.setenv('CCB_ACTOR_ROLE', 'ccb.plan')
    monkeypatch.setenv('CCB_JOB_ID', 'job_compact123')
    drafts = project_root / 'drafts'
    _write(drafts / 'brief.md', '# Brief\n\nPlanner-owned macro summary.\n')
    _write(drafts / 'detail-design.md', '# Detail Design\n\nTask-scoped detail body.\n')
    _write(drafts / 'detail-summary.md', '# Detail Summary\n\nStable summary backfill.\n')
    _write(drafts / 'step-1.md', '# Step 1\n\nInspect.\n')
    _write(drafts / 'step-2.md', '# Step 2\n\nExecute.\n')
    _write(
        drafts / 'detail-packet.json',
        '{"schema":"ccb.loop.detail_packet_manifest/v1","status":"ready_for_review"}\n',
    )
    _write(
        drafts / 'macro-adjustment-request.json',
        '{"schema":"ccb.loop.macro_adjustment_request/v1","reason":"macro assumption changed"}\n',
    )
    _write(drafts / 'blocker-evidence.md', '# Blocker Evidence\n\nBlocked on frontdesk input.\n')

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Brief and detail docs',
            '--task-id',
            'task-detail',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err

    for kind, file_name in (
        ('brief', 'brief.md'),
        ('detail_design', 'detail-design.md'),
        ('detail_summary', 'detail-summary.md'),
    ):
        code, payload, _out, err = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                'task-detail',
                '--kind',
                kind,
                '--file',
                str(drafts / file_name),
                '--json',
            ],
            cwd=project_root,
        )
        assert code == 0, err
        assert payload['artifact']['kind'] == kind

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-detail', '--status', 'detail_ready', '--json'],
        cwd=project_root,
    )
    assert code == 1
    assert 'detail_ready requires artifacts' in err

    for kind, file_name in (
        ('detail_packet', 'detail-packet.json'),
        ('detail_step_1', 'step-1.md'),
        ('detail_step_2', 'step-2.md'),
        ('macro_adjustment_request', 'macro-adjustment-request.json'),
        ('blocker_evidence', 'blocker-evidence.md'),
    ):
        code, payload, _out, err = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                'task-detail',
                '--kind',
                kind,
                '--file',
                str(drafts / file_name),
                '--json',
            ],
            cwd=project_root,
        )
        assert code == 0, err
        assert payload['artifact']['kind'] == kind

    code, payload, _out, err = _run_phase2(['plan', 'task-show', '--task', 'task-detail', '--json'], cwd=project_root)
    assert code == 0, err
    artifacts = payload['task']['artifacts']
    assert artifacts['brief']['scope'] == 'plan'
    assert artifacts['brief']['path'] == 'docs/plantree/plans/demo-plan/brief.md'
    assert artifacts['detail_design']['scope'] == 'task'
    assert artifacts['detail_design']['path'].endswith('/tasks/task-detail/details/task-detail-design.md')
    assert artifacts['detail_summary']['path'].endswith('/tasks/task-detail/details/brief-update-summary.md')
    assert artifacts['detail_summary']['planner_compact_import']['authority'] == 'artifact_only_no_plan_mutation'
    assert artifacts['detail_summary']['planner_compact_import']['planner_action'] == 'review_for_brief_or_task_refs'
    assert 'source_evidence_map' in artifacts['detail_summary']['planner_compact_import']['forbidden_updates']
    assert artifacts['detail_summary']['sha256']
    assert artifacts['detail_summary']['imported_at']
    assert artifacts['detail_summary']['actor']['job_id'] == 'job_compact123'
    assert artifacts['detail_packet']['path'].endswith('/tasks/task-detail/details/detail-packet.manifest.json')
    assert artifacts['detail_step_1']['path'].endswith('/tasks/task-detail/details/steps/step-1.md')
    assert artifacts['detail_step_2']['path'].endswith('/tasks/task-detail/details/steps/step-2.md')
    assert artifacts['macro_adjustment_request']['path'].endswith('/tasks/task-detail/details/macro-adjustment-request.json')
    assert artifacts['macro_adjustment_request']['planner_compact_import']['authority'] == 'request_only_no_auto_mutation'
    assert artifacts['macro_adjustment_request']['planner_compact_import']['planner_action'] == 'review_before_plan_update'
    assert 'automatic_status_mutation' in artifacts['macro_adjustment_request']['planner_compact_import']['forbidden_updates']
    assert artifacts['macro_adjustment_request']['sha256']
    assert artifacts['macro_adjustment_request']['imported_at']
    assert artifacts['macro_adjustment_request']['actor']['job_id'] == 'job_compact123'
    assert artifacts['blocker_evidence']['path'].endswith('/tasks/task-detail/blocker-evidence.md')
    assert payload['task']['status'] == 'draft'
    assert payload['task']['next_owner'] == 'planner'
    assert payload['task']['current_loop'] is None
    assert (project_root / 'docs' / 'plantree' / 'plans' / 'demo-plan' / 'brief.md').read_text(encoding='utf-8').startswith('# Brief')

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-detail', '--status', 'detail_ready', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-status', '--task', 'task-detail', '--status', 'ready', '--json'],
        cwd=project_root,
    )
    assert code == 1
    assert 'ready requires artifacts' in err


def test_plan_task_needs_detail_sequence_can_reach_detail_ready_from_orchestration_ready(
    tmp_path: Path,
) -> None:
    project_root = _project_with_plan(tmp_path)
    task_id = 'phase6b-l3-needs-detail-source-inspection'
    _make_ready_task(project_root, task_id=task_id)
    drafts = project_root / 'drafts'
    _write(drafts / 'orchestration_notes.md', '# Orchestration Notes\n\nroute: needs_detail\n')
    _write(drafts / 'detail-design.md', '# Detail Design\n\nInspect source shape.\n')
    _write(drafts / 'detail-summary.md', '# Detail Summary\n\nReady for bounded import.\n')
    _write(
        drafts / 'detail-packet.json',
        '{"schema":"ccb.loop.detail_packet_manifest/v1","status":"detail_ready"}\n',
    )

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            task_id,
            '--kind',
            'orchestration_notes',
            '--file',
            str(drafts / 'orchestration_notes.md'),
            '--route',
            'needs_detail',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['task']['status'] == 'ready_for_orchestration'
    assert payload['task']['artifacts']['orchestration_notes']['orchestrator_route'] == 'needs_detail'

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            task_id,
            '--kind',
            'detail_design',
            '--file',
            str(drafts / 'detail-design.md'),
            '--route',
            'needs_detail',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'plan task artifact --route is only valid for orchestration_notes' in err

    for kind, file_name in (
        ('detail_design', 'detail-design.md'),
        ('detail_summary', 'detail-summary.md'),
    ):
        code, payload, _out, err = _run_phase2(
            [
                'plan',
                'task-artifact',
                '--task',
                task_id,
                '--kind',
                kind,
                '--file',
                str(drafts / file_name),
                '--json',
            ],
            cwd=project_root,
        )
        assert code == 0, err
        assert 'orchestrator_route' not in payload['artifact']

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            task_id,
            '--status',
            'detail_ready',
            '--activation-reason',
            'phase6b_l1_l4_sequence11_detail_ready',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'detail_ready requires artifacts: detail_packet' in err
    assert 'invalid plan task status transition' not in err

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            task_id,
            '--kind',
            'detail_packet',
            '--file',
            str(drafts / 'detail-packet.json'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert 'orchestrator_route' not in payload['artifact']

    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            task_id,
            '--status',
            'detail_ready',
            '--activation-reason',
            'phase6b_l1_l4_sequence11_detail_ready',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['status'] == 'detail_ready'
    assert payload['next_owner'] == 'planner'
    assert payload['current_loop'] is None
    artifacts = payload['task']['artifacts']
    assert {'detail_design', 'detail_summary', 'detail_packet'} <= set(artifacts)


def test_plan_task_macro_and_blocked_routes_can_reach_terminal_states_from_orchestration_ready(
    tmp_path: Path,
) -> None:
    project_root = _project_with_plan(tmp_path)
    drafts = project_root / 'drafts'

    macro_task = 'phase6b-l4-macro-adjustment-request'
    _make_ready_task(project_root, task_id=macro_task)
    _write(drafts / 'macro-notes.md', '# Orchestration Notes\n\nroute: macro_adjustment_request\n')
    _write(
        drafts / 'macro-adjustment-request.md',
        '# Macro Adjustment Request\n\nAccepted workflow authority conflicts with requested topology DSL.\n',
    )
    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            macro_task,
            '--kind',
            'orchestration_notes',
            '--file',
            str(drafts / 'macro-notes.md'),
            '--route',
            'macro_adjustment_request',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['task']['status'] == 'ready_for_orchestration'
    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            macro_task,
            '--kind',
            'macro_adjustment_request',
            '--file',
            str(drafts / 'macro-adjustment-request.md'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            macro_task,
            '--status',
            'replan_required',
            '--next-owner',
            'planner',
            '--activation-reason',
            'phase6b_l1_l4_sequence12_macro',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['status'] == 'replan_required'
    assert payload['next_owner'] == 'planner'

    blocked_task = 'phase6b-l4-blocked-missing-secret'
    _make_ready_task(project_root, task_id=blocked_task)
    _write(drafts / 'blocked-notes.md', '# Orchestration Notes\n\nroute: blocked\n')
    _write(drafts / 'blocker-evidence.md', '# Blocker Evidence\n\nMissing PHASE6B_LAB_PRIVATE_API_TOKEN.\n')
    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            blocked_task,
            '--kind',
            'orchestration_notes',
            '--file',
            str(drafts / 'blocked-notes.md'),
            '--route',
            'blocked',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['task']['status'] == 'ready_for_orchestration'
    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            blocked_task,
            '--kind',
            'blocker_evidence',
            '--file',
            str(drafts / 'blocker-evidence.md'),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    code, payload, _out, err = _run_phase2(
        [
            'plan',
            'task-status',
            '--task',
            blocked_task,
            '--status',
            'blocked',
            '--activation-reason',
            'phase6b_l1_l4_sequence12_blocked',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert payload['status'] == 'blocked'
    assert payload['next_owner'] == 'terminal'
    artifacts = payload['task']['artifacts']
    assert 'round_summary' not in artifacts
    assert 'last_round' not in payload['task']


def test_plan_task_artifact_rejects_project_external_file(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    outside = tmp_path / 'outside.md'
    outside.write_text('outside\n', encoding='utf-8')

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Unsafe artifact',
            '--task-id',
            'task-unsafe',
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-unsafe',
            '--kind',
            'requirements',
            '--file',
            str(outside),
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 1
    assert 'must be inside project root' in err


def test_plan_task_rejects_invalid_existing_index(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _write(project_root / 'docs' / 'plantree' / 'plans' / 'demo-plan' / 'tasks' / 'index.json', '{broken')

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-create',
            '--plan',
            'demo-plan',
            '--title',
            'Do not overwrite corrupt index',
            '--task-id',
            'task-corrupt',
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 1
    assert 'plan task index is invalid JSON' in err


def test_plan_task_artifact_rejects_direct_round_summary_import(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _make_ready_task(project_root, task_id='task-round-artifact')
    report = project_root / 'rounds' / 'pass.md'
    _write(report, 'round result: pass\n')

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-artifact',
            '--task',
            'task-round-artifact',
            '--kind',
            'round_summary',
            '--file',
            str(report),
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 1
    assert 'cannot import round_summary directly' in err


def test_plan_task_bind_loop_and_import_round_are_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = _project_with_plan(tmp_path)
    monkeypatch.setenv('CCB_CALLER_ACTOR', 'plan_script')
    monkeypatch.setenv('CCB_ACTOR_ROLE', 'ccb.plan')
    monkeypatch.setenv('CCB_JOB_ID', 'job_round123')
    _make_ready_task(project_root, task_id='task-bridge')

    code, payload, _out, err = _run_phase2(
        ['plan', 'task-bind-loop', '--task', 'task-bridge', '--loop', 'loop-a', '--json'],
        cwd=project_root,
    )

    assert code == 0, err
    assert payload['status'] == 'running'
    assert payload['task']['current_loop'] == 'loop-a'
    assert payload['task']['next_owner'] == 'orchestrator'
    assert payload['task']['loop_lease']['status'] == 'active'

    code, retry, _out, err = _run_phase2(
        ['plan', 'task-bind-loop', '--task', 'task-bridge', '--loop', 'loop-a', '--json'],
        cwd=project_root,
    )
    assert code == 0, err
    assert retry['task']['loop_lease']['lease_id'] == payload['task']['loop_lease']['lease_id']

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-bind-loop', '--task', 'task-bridge', '--loop', 'loop-b', '--json'],
        cwd=project_root,
    )
    assert code == 1
    assert 'already bound to loop: loop-a' in err

    report = project_root / 'rounds' / 'pass.md'
    _write(report, 'round result: pass\n')
    code, imported, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-a',
            '--result',
            'pass',
            '--report',
            str(report),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert imported['status'] == 'done'
    assert imported['round_result'] == 'pass'
    assert imported['idempotent'] is False
    assert imported['artifact']['kind'] == 'round_summary'
    assert imported['artifact']['path'].endswith('/round_summary.md')
    assert imported['artifact']['planner_compact_import']['authority'] == 'script_owned_task_import_round'
    assert imported['artifact']['planner_compact_import']['planner_action'] == 'rehydrate_for_brief_or_next_task_planning'
    assert imported['artifact']['sha256']
    assert imported['artifact']['imported_at']
    assert imported['artifact']['actor']['job_id'] == 'job_round123'
    assert imported['legacy_artifact']['kind'] == 'round_pass'
    assert imported['task']['current_loop'] is None
    assert imported['task']['next_owner'] == 'terminal'
    assert imported['task']['round_counters'] == {'pass': 1}

    code, repeated, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-a',
            '--result',
            'pass',
            '--report',
            str(report),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 0, err
    assert repeated['idempotent'] is True
    assert repeated['task']['round_counters'] == {'pass': 1}

    conflicting = project_root / 'rounds' / 'conflicting.md'
    _write(conflicting, 'round result: pass\nchanged\n')
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-a',
            '--result',
            'pass',
            '--report',
            str(conflicting),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'conflicts with existing round_summary artifact' in err


@pytest.mark.parametrize(
    ('result', 'expected_status', 'expected_legacy_kind'),
    (
        ('partial', 'partial', 'round_partial'),
        ('replan_required', 'replan_required', 'round_replan'),
        ('blocked', 'blocked', 'round_blocker'),
    ),
)
def test_plan_task_import_round_maps_non_pass_results(
    tmp_path: Path,
    result: str,
    expected_status: str,
    expected_legacy_kind: str,
) -> None:
    project_root = _project_with_plan(tmp_path)
    _make_ready_task(project_root, task_id='task-bridge')

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-bind-loop', '--task', 'task-bridge', '--loop', 'loop-a', '--json'],
        cwd=project_root,
    )
    assert code == 0, err

    report = project_root / 'rounds' / f'{result}.md'
    _write(report, f'round result: {result}\n')
    code, imported, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-a',
            '--result',
            result,
            '--report',
            str(report),
            '--json',
        ],
        cwd=project_root,
    )

    assert code == 0, err
    assert imported['status'] == expected_status
    assert imported['artifact']['kind'] == 'round_summary'
    assert imported['legacy_artifact']['kind'] == expected_legacy_kind
    assert imported['task']['current_loop'] is None
    assert imported['task']['next_owner'] == ('terminal' if result == 'blocked' else 'planner')
    assert imported['task']['last_round']['result'] == result
    assert imported['task']['last_round']['artifact_kind'] == 'round_summary'
    assert imported['task']['last_round']['legacy_artifact_kind'] == expected_legacy_kind
    assert imported['task']['round_counters'] == {result: 1}


def test_plan_task_import_round_rejects_wrong_loop_and_missing_report(tmp_path: Path) -> None:
    project_root = _project_with_plan(tmp_path)
    _make_ready_task(project_root, task_id='task-bridge')

    code, _payload, _out, err = _run_phase2(
        ['plan', 'task-bind-loop', '--task', 'task-bridge', '--loop', 'loop-a', '--json'],
        cwd=project_root,
    )
    assert code == 0, err

    report = project_root / 'rounds' / 'blocked.md'
    _write(report, 'round result: blocked\n')
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-b',
            '--result',
            'blocked',
            '--report',
            str(report),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'requires current_loop=loop-b; current_loop is loop-a' in err

    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-a',
            '--result',
            'mystery',
            '--report',
            str(report),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'unknown round result' in err

    missing = project_root / 'rounds' / 'missing.md'
    code, _payload, _out, err = _run_phase2(
        [
            'plan',
            'task-import-round',
            '--task',
            'task-bridge',
            '--loop',
            'loop-a',
            '--result',
            'blocked',
            '--report',
            str(missing),
            '--json',
        ],
        cwd=project_root,
    )
    assert code == 1
    assert 'plan artifact file not found' in err
