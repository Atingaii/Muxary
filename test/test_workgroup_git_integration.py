from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from cli.services.workgroup_integration import (
    GitIntegrationError,
    VerificationCommand,
    WORKGROUP_GIT_TRANSACTION_SCHEMA,
    WorkgroupGitIntegration,
    WorkgroupNodeSpec,
)


BUNDLE_DIGEST = 'sha256:' + ('a' * 64)


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    root = tmp_path / 'repo'
    root.mkdir()
    (root / '.gitignore').write_text('.ccb/\n__pycache__/\n', encoding='utf-8')
    (root / 'README.md').write_text('base\n', encoding='utf-8')
    (root / 'protected.txt').write_text('protected\n', encoding='utf-8')
    _git(root, 'init')
    _git(root, 'config', 'user.email', 'test@example.com')
    _git(root, 'config', 'user.name', 'Test User')
    _git(root, 'add', '.')
    _git(root, 'commit', '-m', 'base')
    return root


def _node(
    index: int,
    *,
    allowed_paths: tuple[str, ...] | None = None,
    depends_on: tuple[str, ...] = (),
    integration_order: int | None = None,
) -> WorkgroupNodeSpec:
    return WorkgroupNodeSpec(
        node_id=f'node-{index:03d}',
        workgroup_id=f'wg-{index:03d}',
        depends_on=depends_on,
        allowed_paths=allowed_paths or (f'parts/node-{index:03d}.txt',),
        integration_order=integration_order or index * 10,
    )


def _kernel(
    root: Path,
    nodes: tuple[WorkgroupNodeSpec, ...],
    *,
    integration_verification: tuple[VerificationCommand, ...] = (),
    root_verification: tuple[VerificationCommand, ...] = (),
    verify_each_layer: bool = False,
) -> WorkgroupGitIntegration:
    return WorkgroupGitIntegration(
        project_root=root,
        state_path=root / '.ccb' / 'runtime' / 'loops' / 'loop-r2' / 'git-transaction.json',
        task_id='task-r2',
        loop_id='loop-r2',
        bundle_revision=1,
        bundle_digest=BUNDLE_DIGEST,
        nodes=nodes,
        integration_verification=integration_verification,
        root_verification=root_verification,
        verify_each_layer=verify_each_layer,
    )


def _node_record(kernel: WorkgroupGitIntegration, node_id: str) -> dict[str, object]:
    return kernel.state()['nodes'][node_id]


def _write_node_file(kernel: WorkgroupGitIntegration, node_id: str, relative: str, text: str) -> None:
    worktree = Path(str(_node_record(kernel, node_id)['worktree_path']))
    path = worktree / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _review_and_finalize(kernel: WorkgroupGitIntegration, node_id: str) -> dict[str, object]:
    review = kernel.capture_review_input(node_id, worker_job_id=f'worker-{node_id}')
    kernel.record_review(
        node_id,
        reviewer_job_id=f'reviewer-{node_id}',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    return kernel.finalize_node(node_id)


def _prepare_changed_node(
    kernel: WorkgroupGitIntegration,
    spec: WorkgroupNodeSpec,
    *,
    relative: str | None = None,
    text: str | None = None,
) -> dict[str, object]:
    kernel.prepare_node(spec.node_id)
    target = relative or spec.allowed_paths[0]
    _write_node_file(kernel, spec.node_id, target, text or f'{spec.node_id}\n')
    return _review_and_finalize(kernel, spec.node_id)


@pytest.mark.parametrize('node_count', (1, 2, 3, 4))
def test_one_to_four_independent_nodes_integrate_promote_and_preserve_worktrees(
    tmp_path: Path,
    node_count: int,
) -> None:
    root = _init_repo(tmp_path)
    nodes = tuple(_node(index) for index in range(1, node_count + 1))
    kernel = _kernel(root, nodes)

    preflight = kernel.preflight()
    kernel.prepare_integration()
    for spec in reversed(nodes):
        _prepare_changed_node(kernel, spec)

    integrated = kernel.integrate_ready()
    promoted = kernel.promote()
    verified = kernel.verify_root()
    accepted = kernel.accept()

    assert preflight['schema'] == WORKGROUP_GIT_TRANSACTION_SCHEMA
    assert integrated['integration']['merge_order'] == [node.node_id for node in nodes]
    assert integrated['integration']['status'] == 'verified'
    assert promoted['root']['promotion']['status'] == 'applied'
    assert verified['root']['checks'][-1]['status'] == 'pass'
    assert accepted['status'] == 'accepted'
    assert _git(root, 'status', '--porcelain') == ''
    for spec in nodes:
        assert (root / spec.allowed_paths[0]).read_text(encoding='utf-8') == f'{spec.node_id}\n'
        record = accepted['nodes'][spec.node_id]
        assert record['status'] == 'integrated'
        assert record['reviewed_commit']
        assert record['reviewed_tree_digest'] == record['review']['tree_digest']
        assert Path(str(record['worktree_path'])).is_dir()

    active_path = Path(str(accepted['nodes'][nodes[0].node_id]['worktree_path']))
    blocked_cleanup = kernel.cleanup_readiness(
        evidence_captured=True,
        active_workspaces=(active_path,),
    )
    ready_cleanup = kernel.cleanup_readiness(evidence_captured=True)

    assert blocked_cleanup['eligible'] is False
    assert blocked_cleanup['reason'] == 'owned_worktree_active'
    assert ready_cleanup['eligible'] is True
    assert ready_cleanup['worktrees_preserved'] is True
    assert active_path.is_dir()


def test_mixed_dependency_graph_uses_current_integrated_head_and_stable_order(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    node_1 = _node(1, integration_order=20)
    node_2 = _node(2, integration_order=10)
    node_3 = _node(
        3,
        depends_on=('node-001', 'node-002'),
        integration_order=30,
    )
    check = VerificationCommand(
        'completed-wave',
        (
            sys.executable,
            '-c',
            'from pathlib import Path; '
            'assert all(Path(f"parts/node-{i:03d}.txt").is_file() for i in (1,2))',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(
        root,
        (node_1, node_2, node_3),
        integration_verification=(check,),
        verify_each_layer=True,
    )
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, node_1)
    _prepare_changed_node(kernel, node_2)

    first_wave = kernel.integrate_ready()
    first_head = first_wave['integration']['head']
    assert first_wave['integration']['merge_order'] == ['node-002', 'node-001']
    assert first_wave['status'] == 'integration_pending'

    kernel.prepare_node(node_3.node_id)
    dependent = _node_record(kernel, node_3.node_id)
    assert dependent['base_commit'] == first_head
    _write_node_file(kernel, node_3.node_id, node_3.allowed_paths[0], 'dependent\n')
    _review_and_finalize(kernel, node_3.node_id)

    final = kernel.integrate_ready()

    assert final['integration']['merge_order'] == ['node-002', 'node-001', 'node-003']
    assert [check['key'] for check in final['integration']['checks']] == ['layer-0', 'layer-1', 'final']
    assert all(check['status'] == 'pass' for check in final['integration']['checks'])
    assert final['nodes']['node-003']['base_commit'] == first_head
    integration_root = Path(str(final['integration']['worktree_path']))
    assert (integration_root / node_3.allowed_paths[0]).read_text(encoding='utf-8') == 'dependent\n'


def test_terminal_failed_node_is_durably_excluded_while_reviewed_sibling_integrates(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    node_1 = _node(1)
    node_2 = _node(2)
    kernel = _kernel(root, (node_1, node_2))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(node_1.node_id)
    _prepare_changed_node(kernel, node_2)

    excluded = kernel.record_node_failure(
        node_1.node_id,
        authority_id='job:job-worker-failed',
        job_id='job-worker-failed',
        source='provider_job_failed',
    )
    replayed = kernel.record_node_failure(
        node_1.node_id,
        authority_id='job:job-worker-failed',
        job_id='job-worker-failed',
        source='provider_job_failed',
    )
    integrated = kernel.integrate_ready()

    assert excluded['status'] == 'excluded'
    assert replayed['terminal_failure'] == excluded['terminal_failure']
    assert integrated['nodes'][node_1.node_id]['status'] == 'excluded'
    assert integrated['nodes'][node_2.node_id]['status'] == 'integrated'
    assert integrated['integration']['merge_order'] == [node_2.node_id]
    assert integrated['integration']['status'] == 'verified'
    assert integrated['root']['promotion'] is None

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.record_node_failure(
            node_1.node_id,
            authority_id='job:job-lookalike',
            job_id='job-lookalike',
            source='provider_job_failed',
        )
    assert exc_info.value.code == 'node_failure_authority_drift'


def test_reviewer_failure_quarantines_exact_unreviewed_delta_before_cleanup(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    node = _node(1)
    kernel = _kernel(root, (node,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(node.node_id)
    _write_node_file(kernel, node.node_id, node.allowed_paths[0], 'unreviewed\n')
    kernel.capture_review_input(node.node_id, worker_job_id='job-worker')

    fired = False

    def crash_after_restore(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_node_failure_worktree_restore' and not fired:
            fired = True
            raise RuntimeError('crash:after-node-failure-worktree-restore')

    kernel._checkpoint_hook = crash_after_restore
    with pytest.raises(RuntimeError, match='crash:after-node-failure-worktree-restore'):
        kernel.record_node_failure(
            node.node_id,
            authority_id='job:job-reviewer-failed',
            job_id='job-reviewer-failed',
            source='provider_job_failed',
        )
    assert kernel.state()['nodes'][node.node_id]['terminal_failure']['status'] == 'restoring'
    kernel._checkpoint_hook = None
    excluded = kernel.record_node_failure(
        node.node_id,
        authority_id='job:job-reviewer-failed',
        job_id='job-reviewer-failed',
        source='provider_job_failed',
    )
    worktree = Path(str(excluded['worktree_path']))
    failure = excluded['terminal_failure']

    assert excluded['status'] == 'excluded'
    assert failure['status'] == 'restored'
    quarantine_manifest = Path(str(failure['quarantine']['manifest_path']))
    assert quarantine_manifest.is_file()
    assert json.loads(quarantine_manifest.read_text(encoding='utf-8'))['schema'] == (
        'ccb.loop.node_failure_quarantine.v1'
    )
    assert _git(worktree, 'status', '--porcelain') == ''
    assert not (worktree / node.allowed_paths[0]).exists()

    kernel.close_without_promotion(result='partial', reason='required_node_failure')
    assert kernel.cleanup_readiness(evidence_captured=True)['eligible'] is True
    assert kernel.cleanup(active_workspaces=())['status'] == 'complete'
    assert not worktree.exists()


def test_rejected_dirty_preflight_does_not_create_branches_or_worktrees(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    (root / 'user-change.txt').write_text('keep me\n', encoding='utf-8')
    kernel = _kernel(root, (_node(1),))
    before_head = _git(root, 'rev-parse', 'HEAD')
    before_branches = _git(root, 'branch', '--format=%(refname)')
    before_worktrees = _git(root, 'worktree', 'list', '--porcelain')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.preflight()

    assert exc_info.value.code == 'dirty_project_root'
    assert _git(root, 'rev-parse', 'HEAD') == before_head
    assert _git(root, 'branch', '--format=%(refname)') == before_branches
    assert _git(root, 'worktree', 'list', '--porcelain') == before_worktrees
    assert (root / 'user-change.txt').read_text(encoding='utf-8') == 'keep me\n'
    assert kernel.state_path.exists() is False


def test_preflight_ignores_controller_owned_plan_tree_state(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    tracked_plan = root / 'docs' / 'plantree' / 'plans' / 'frontdesk-intake' / 'README.md'
    tracked_plan.parent.mkdir(parents=True)
    tracked_plan.write_text('tracked plan\n', encoding='utf-8')
    _git(root, 'add', 'docs/plantree/plans/frontdesk-intake/README.md')
    _git(root, 'commit', '-m', 'track controller plan root')
    tracked_plan.write_text('updated by controller\n', encoding='utf-8')
    generated_task = (
        root
        / 'docs'
        / 'plantree'
        / 'plans'
        / 'frontdesk-intake'
        / 'tasks'
        / 'task-1'
        / 'task_packet.md'
    )
    generated_task.parent.mkdir(parents=True)
    generated_task.write_text('# Task\n', encoding='utf-8')
    kernel = _kernel(root, (_node(1),))

    preflight = kernel.preflight()

    assert preflight['status'] == 'preflighted'
    assert 'docs/plantree/plans/frontdesk-intake/README.md' in _git(
        root, 'status', '--porcelain'
    )
    assert '?? docs/plantree/plans/frontdesk-intake/tasks/' in _git(
        root, 'status', '--porcelain'
    )


def test_preflight_rejects_stale_controller_branch_without_resumable_state(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    kernel = _kernel(root, (_node(1),))
    stale_branch = f'ccb/workgroup/{kernel.transaction_key}/integration'
    _git(root, 'branch', stale_branch)

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.preflight()

    assert exc_info.value.code == 'controller_workspace_collision'
    assert {'kind': 'branch', 'value': stale_branch} in exc_info.value.details['collisions']
    assert kernel.state_path.exists() is False


def test_public_from_bundle_api_uses_explicit_semantic_digest(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    bundle = {
        'task_id': 'task-r2',
        'bundle_revision': 1,
        'nodes': [
            {
                'node_id': 'node-001',
                'workgroup_id': 'wg-001',
                'depends_on': [],
                'allowed_paths': ['parts/node-001.txt'],
                'integration_order': 10,
            }
        ],
    }

    kernel = WorkgroupGitIntegration.from_bundle(
        project_root=root,
        state_path=root / '.ccb' / 'runtime' / 'loops' / 'loop-r2' / 'git-transaction.json',
        loop_id='loop-r2',
        bundle=bundle,
        bundle_digest=BUNDLE_DIGEST,
    )
    state = kernel.preflight()

    assert state['task']['bundle_digest'] == BUNDLE_DIGEST
    assert list(state['nodes']) == ['node-001']


def test_durable_state_rejects_node_scope_drift(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    payload = json.loads(kernel.state_path.read_text(encoding='utf-8'))
    payload['nodes']['node-001']['allowed_paths'] = ['other.txt']
    kernel.state_path.write_text(json.dumps(payload), encoding='utf-8')

    with pytest.raises(GitIntegrationError) as exc_info:
        _kernel(root, (spec,)).state()

    assert exc_info.value.code == 'integration_state_node_drift'


def test_scope_violation_and_out_of_contract_deletion_block_before_review(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1, allowed_paths=('parts/allowed.txt',))
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, 'parts/allowed.txt', 'allowed\n')
    worktree = Path(str(_node_record(kernel, spec.node_id)['worktree_path']))
    (worktree / 'protected.txt').unlink()

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')

    assert exc_info.value.code == 'node_scope_violation'
    assert 'protected.txt' in exc_info.value.details['changed_paths']
    assert _git(worktree, 'rev-parse', 'HEAD') == kernel.state()['task']['base_commit']
    assert _git(worktree, 'rev-list', '--count', '--all', '--not', kernel.state()['task']['base_commit']) == '0'


def test_controller_workspace_binding_is_not_node_scope_or_commit_content(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    worktree = Path(str(_node_record(kernel, spec.node_id)['worktree_path']))
    (worktree / '.ccb-workspace.json').write_text(
        '{"target_project":"' + str(root.resolve()) + '"}\n',
        encoding='utf-8',
    )
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'first\n')

    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    finalized = kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    committed = kernel.finalize_node(spec.node_id)

    assert review['input']['changed_paths'] == [spec.allowed_paths[0]]
    assert finalized['result'] == 'pass'
    assert committed['status'] == 'integration_ready'
    assert '.ccb-workspace.json' not in _git(worktree, 'ls-tree', '-r', '--name-only', 'HEAD').splitlines()
    assert '?? .ccb-workspace.json' in _git(worktree, 'status', '--porcelain')


def test_python_bytecode_cache_is_not_node_scope_or_commit_content(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    (root / '.gitignore').write_text('.ccb/\n', encoding='utf-8')
    _git(root, 'add', '.gitignore')
    _git(root, 'commit', '-m', 'stop ignoring python cache')
    spec = _node(1, allowed_paths=('todo.py', 'tests/test_todo.py'))
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    worktree = Path(str(_node_record(kernel, spec.node_id)['worktree_path']))
    _write_node_file(kernel, spec.node_id, 'todo.py', 'print("todo")\n')
    _write_node_file(kernel, spec.node_id, 'tests/test_todo.py', 'def test_todo(): pass\n')
    (worktree / '__pycache__').mkdir()
    (worktree / '__pycache__' / 'todo.cpython-311.pyc').write_bytes(b'bytecode')
    (worktree / 'tests' / '__pycache__').mkdir()
    (worktree / 'tests' / '__pycache__' / 'test_todo.cpython-311.pyc').write_bytes(b'bytecode')

    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    finalized = kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    committed = kernel.finalize_node(spec.node_id)

    assert review['input']['changed_paths'] == ['tests/test_todo.py', 'todo.py']
    assert finalized['result'] == 'pass'
    assert committed['status'] == 'integration_ready'
    committed_paths = _git(worktree, 'ls-tree', '-r', '--name-only', 'HEAD').splitlines()
    assert 'todo.py' in committed_paths
    assert 'tests/test_todo.py' in committed_paths
    assert all('__pycache__' not in path for path in committed_paths)
    assert '?? __pycache__/' in _git(worktree, 'status', '--porcelain')
    assert '?? tests/__pycache__/' in _git(worktree, 'status', '--porcelain')


def test_reviewer_input_and_tree_digests_are_exact_fences(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'first\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')

    with pytest.raises(GitIntegrationError) as mismatch:
        kernel.record_review(
            spec.node_id,
            reviewer_job_id='reviewer-1',
            result='pass',
            input_digest='sha256:' + ('b' * 64),
            tree_digest=str(review['tree_digest']),
        )
    assert mismatch.value.code == 'review_input_digest_mismatch'

    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'drifted\n')
    with pytest.raises(GitIntegrationError) as drift:
        kernel.record_review(
            spec.node_id,
            reviewer_job_id='reviewer-1',
            result='pass',
            input_digest=str(review['input_digest']),
            tree_digest=str(review['tree_digest']),
        )
    assert drift.value.code == 'reviewed_tree_drift'
    assert _node_record(kernel, spec.node_id)['reviewed_commit'] is None


def test_missing_reviewer_pass_cannot_create_controller_commit(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'pending\n')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.finalize_node(spec.node_id)

    assert exc_info.value.code == 'missing_reviewer_pass'
    assert _node_record(kernel, spec.node_id)['reviewed_commit'] is None


def test_rework_review_lineage_is_preserved_and_duplicate_result_is_idempotent(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'first attempt\n')
    first = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    first_result = kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='rework',
        input_digest=str(first['input_digest']),
        tree_digest=str(first['tree_digest']),
    )
    duplicate = kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='rework',
        input_digest=str(first['input_digest']),
        tree_digest=str(first['tree_digest']),
    )
    assert duplicate == first_result

    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'second attempt\n')
    second = kernel.capture_review_input(spec.node_id, worker_job_id='worker-2')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-2',
        result='pass',
        input_digest=str(second['input_digest']),
        tree_digest=str(second['tree_digest']),
    )
    finalized = kernel.finalize_node(spec.node_id)

    assert [review['result'] for review in finalized['reviews']] == ['rework', 'pass']
    assert finalized['reviewed_tree_digest'] == second['tree_digest']


def test_dirty_drift_after_reviewed_commit_blocks_integration(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    finalized = _prepare_changed_node(kernel, spec)
    worktree = Path(str(finalized['worktree_path']))
    (worktree / spec.allowed_paths[0]).write_text('post-review drift\n', encoding='utf-8')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    assert exc_info.value.code == 'reviewed_commit_worktree_drift'
    assert kernel.state()['integration']['merge_order'] == []


def test_merge_conflict_is_structured_and_never_auto_resolved(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    file_node = _node(1, allowed_paths=('shared',), integration_order=10)
    directory_node = _node(2, allowed_paths=('shared/file.txt',), integration_order=20)
    kernel = _kernel(root, (file_node, directory_node))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, file_node, relative='shared', text='file\n')
    _prepare_changed_node(kernel, directory_node, relative='shared/file.txt', text='child\n')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    state = kernel.state()
    integration_path = Path(str(state['integration']['worktree_path']))
    assert exc_info.value.code == 'integration_merge_conflict'
    assert state['status'] == 'replan_required'
    assert state['integration']['status'] == 'merge_conflict'
    assert state['integration']['merge_order'] == ['node-001']
    assert _git(integration_path, 'status', '--porcelain') == ''
    assert not (root / 'shared').exists()


def test_integration_verification_failure_never_promotes_root(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    failing = VerificationCommand(
        'fail-integration',
        (
            sys.executable,
            '-c',
            'import sys; print("integration-out"); print("integration-err", file=sys.stderr); '
            'raise SystemExit(7)',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), integration_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    base = kernel.state()['task']['base_commit']

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    state = kernel.state()
    assert exc_info.value.code == 'integration_verification_failed'
    assert state['status'] == 'integration_failed'
    assert state['integration']['checks'][-1]['results'][0]['exit_code'] == 7
    assert state['integration']['checks'][-1]['results'][0]['stdout'] == 'integration-out\n'
    assert state['integration']['checks'][-1]['results'][0]['stderr'] == 'integration-err\n'
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert not (root / spec.allowed_paths[0]).exists()


def test_integration_verification_missing_executable_is_structured_failure(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    missing = VerificationCommand(
        'missing-executable',
        ('definitely-not-a-ccb-test-command',),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), integration_verification=(missing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    base = kernel.state()['task']['base_commit']

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    result = kernel.state()['integration']['checks'][-1]['results'][0]
    assert exc_info.value.code == 'integration_verification_failed'
    assert result['result'] == 'failed'
    assert result['exit_code'] is None
    assert result['timed_out'] is False
    assert 'FileNotFoundError' in result['stderr']
    assert _git(root, 'rev-parse', 'HEAD') == base


def test_integration_verification_timeout_is_bounded_and_recorded(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    timeout = VerificationCommand(
        'timeout-integration',
        (sys.executable, '-c', 'import time; time.sleep(2)'),
        timeout_seconds=0.05,
    )
    kernel = _kernel(root, (spec,), integration_verification=(timeout,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    result = kernel.state()['integration']['checks'][-1]['results'][0]
    assert exc_info.value.code == 'integration_verification_failed'
    assert result['timed_out'] is True
    assert result['exit_code'] is None
    assert result['result'] == 'failed'


def test_root_drift_blocks_promotion_without_overwriting_user_change(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    base = kernel.state()['task']['base_commit']
    (root / 'user-local.txt').write_text('do not overwrite\n', encoding='utf-8')

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.promote()

    assert exc_info.value.code == 'root_drift_before_promotion'
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert (root / 'user-local.txt').read_text(encoding='utf-8') == 'do not overwrite\n'
    assert not (root / spec.allowed_paths[0]).exists()


def test_root_branch_drift_blocks_promotion_even_when_head_is_unchanged(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    base = kernel.state()['task']['base_commit']
    _git(root, 'switch', '-c', 'user/other-branch')
    assert _git(root, 'rev-parse', 'HEAD') == base

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.promote()

    assert exc_info.value.code == 'root_drift_before_promotion'
    assert exc_info.value.details['observed_branch'] == 'user/other-branch'
    assert _git(root, 'rev-parse', 'HEAD') == base


def test_root_verification_failure_restores_exact_pre_promotion_root(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    failing = VerificationCommand(
        'fail-root',
        (
            sys.executable,
            '-c',
            'raise SystemExit(9)',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    base = kernel.state()['task']['base_commit']
    base_tree = kernel.state()['task']['base_tree_digest']

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.verify_root()

    state = kernel.state()
    assert exc_info.value.code == 'root_verification_failed'
    assert state['status'] == 'rolled_back'
    assert state['root']['rollback']['status'] == 'restored'
    assert state['root']['rollback']['tree_digest'] == base_tree
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert _git(root, 'status', '--porcelain') == ''
    assert not (root / spec.allowed_paths[0]).exists()


@pytest.mark.parametrize(
    ('script', 'changed_path', 'quarantined_text'),
    (
        (
            'from pathlib import Path; Path("verification.out").write_text("generated\\n"); '
            'raise SystemExit(9)',
            'verification.out',
            'generated\n',
        ),
        (
            'from pathlib import Path; Path("README.md").write_text("verification changed\\n"); '
            'raise SystemExit(9)',
            'README.md',
            'verification changed\n',
        ),
    ),
)
def test_root_verification_mutation_is_quarantined_then_exactly_rolled_back(
    tmp_path: Path,
    script: str,
    changed_path: str,
    quarantined_text: str,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    failing = VerificationCommand(
        'mutate-and-fail-root',
        (sys.executable, '-c', script),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    base = kernel.state()['task']['base_commit']

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.verify_root()

    state = kernel.state()
    quarantine = state['root']['verification']['quarantine']
    preserved = Path(str(quarantine['path'])) / 'files' / changed_path
    assert exc_info.value.code == 'root_verification_failed'
    assert state['status'] == 'rolled_back'
    assert quarantine['status'] == 'preserved'
    assert root not in preserved.parents
    assert preserved.read_text(encoding='utf-8') == quarantined_text
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert _git(root, 'status', '--porcelain') == ''
    assert (root / 'README.md').read_text(encoding='utf-8') == 'base\n'
    assert not (root / 'verification.out').exists()


def test_root_verification_quarantine_crash_replays_rollback_without_rerun(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    marker = tmp_path / 'verification-runs.txt'
    failing = VerificationCommand(
        'mutate-and-fail-root',
        (
            sys.executable,
            '-c',
            'from pathlib import Path; '
            f'p=Path({str(marker)!r}); p.write_text(p.read_text() + "run\\n" if p.exists() else "run\\n"); '
            'Path("verification.out").write_text("generated\\n"); raise SystemExit(9)',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_root_verification_quarantine' and not fired:
            fired = True
            raise RuntimeError('crash:verification-quarantine')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:verification-quarantine'):
        kernel.verify_root()

    replay = _kernel(root, (spec,), root_verification=(failing,))
    with pytest.raises(GitIntegrationError) as exc_info:
        replay.verify_root()

    assert exc_info.value.code == 'root_verification_failed'
    assert marker.read_text(encoding='utf-8') == 'run\n'
    assert replay.state()['status'] == 'rolled_back'
    assert _git(root, 'status', '--porcelain') == ''


def test_root_verification_intent_crash_does_not_resubmit_command(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    marker = tmp_path / 'verification-command-ran.txt'
    command = VerificationCommand(
        'must-not-rerun',
        (
            sys.executable,
            '-c',
            f'from pathlib import Path; Path({str(marker)!r}).write_text("ran\\n")',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(command,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_root_verification_intent' and not fired:
            fired = True
            raise RuntimeError('crash:verification-intent')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:verification-intent'):
        kernel.verify_root()

    replay = _kernel(root, (spec,), root_verification=(command,))
    with pytest.raises(GitIntegrationError) as exc_info:
        replay.verify_root()

    state = replay.state()
    assert exc_info.value.code == 'root_verification_failed'
    assert state['root']['verification']['interrupted'] is True
    assert state['status'] == 'rolled_back'
    assert not marker.exists()


def test_concurrent_drift_after_verification_quarantine_blocks_rollback(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    failing = VerificationCommand(
        'mutate-and-fail-root',
        (
            sys.executable,
            '-c',
            'from pathlib import Path; Path("verification.out").write_text("generated\\n"); '
            'raise SystemExit(9)',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(failing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    integrated_head = kernel.state()['integration']['head']

    def concurrent_write(name: str, _state: dict[str, object]) -> None:
        if name == 'after_root_verification_quarantine':
            (root / 'user-concurrent.txt').write_text('preserve me\n', encoding='utf-8')

    kernel._checkpoint_hook = concurrent_write
    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.verify_root()

    assert exc_info.value.code == 'rollback_root_drift'
    assert _git(root, 'rev-parse', 'HEAD') == integrated_head
    assert (root / 'verification.out').read_text(encoding='utf-8') == 'generated\n'
    assert (root / 'user-concurrent.txt').read_text(encoding='utf-8') == 'preserve me\n'


def test_explicit_nonpass_rollback_after_root_verification(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    passing = VerificationCommand(
        'root-pass',
        (sys.executable, '-c', 'from pathlib import Path; assert Path("parts/node-001.txt").is_file()'),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(passing,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    base = kernel.state()['task']['base_commit']

    rolled_back = kernel.rollback(reason='round_reviewer_rejected')

    assert rolled_back['status'] == 'rolled_back'
    assert rolled_back['root']['rollback']['reason'] == 'round_reviewer_rejected'
    assert _git(root, 'rev-parse', 'HEAD') == base
    assert not (root / spec.allowed_paths[0]).exists()


def test_nonpromoted_partial_closure_is_durable_and_cleanup_eligible(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    unstarted = _node(2)
    kernel = _kernel(root, (spec, unstarted))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)

    closed = kernel.close_without_promotion(
        result='partial',
        reason='worker_failed',
    )
    replay = kernel.close_without_promotion(
        result='partial',
        reason='worker_failed',
    )
    readiness = kernel.cleanup_readiness(evidence_captured=True)

    assert closed['status'] == 'integration_failed'
    assert replay['closure'] == closed['closure']
    assert readiness['eligible'] is True
    assert closed['root']['promotion'] is None
    assert closed['nodes'][unstarted.node_id]['status'] == 'planned'


@pytest.mark.parametrize(
    'checkpoint',
    ('after_node_commit_intent', 'after_node_commit', 'after_node_state_write'),
)
def test_node_finalize_replay_never_duplicates_controller_commit(
    tmp_path: Path,
    checkpoint: str,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'replay\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == checkpoint and not fired:
            fired = True
            raise RuntimeError(f'crash:{checkpoint}')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match=f'crash:{checkpoint}'):
        kernel.finalize_node(spec.node_id)

    replay = _kernel(root, (spec,))
    replay.prepare_node(spec.node_id)
    finalized = replay.finalize_node(spec.node_id)
    worktree = Path(str(finalized['worktree_path']))
    base = replay.state()['task']['base_commit']

    assert finalized['reviewed_commit']
    assert _git(worktree, 'rev-list', '--count', f'{base}..HEAD') == '1'


@pytest.mark.parametrize('tamper', ('actor', 'message'))
def test_provider_lookalike_node_commit_is_not_controller_recovery_authority(
    tmp_path: Path,
    tamper: str,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, spec.allowed_paths[0], 'provider commit\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_node_commit_intent' and not fired:
            fired = True
            raise RuntimeError('crash:node-intent')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:node-intent'):
        kernel.finalize_node(spec.node_id)

    record = _node_record(kernel, spec.node_id)
    worktree = Path(str(record['worktree_path']))
    _git(worktree, 'add', '-A')
    _git(
        worktree,
        '-c',
        f'user.name={"Provider Actor" if tamper == "actor" else "CCB Controller"}',
        '-c',
        f'user.email={"provider@example.com" if tamper == "actor" else "ccb-controller@localhost"}',
        'commit',
        '-m',
        str(record['commit_intent']['message']) + ('\nlookalike' if tamper == 'message' else ''),
    )

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.finalize_node(spec.node_id)

    assert exc_info.value.code == 'node_commit_authority_drift'
    assert _node_record(kernel, spec.node_id)['reviewed_commit'] is None


@pytest.mark.parametrize(
    ('checkpoint', 'expected_recovered'),
    (
        ('after_integration_merge_intent', False),
        ('after_integration_merge', True),
    ),
)
def test_integration_merge_replay_records_existing_merge_without_duplication(
    tmp_path: Path,
    checkpoint: str,
    expected_recovered: bool,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == checkpoint and not fired:
            fired = True
            raise RuntimeError('crash:merge')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:merge'):
        kernel.integrate_ready()

    replay = _kernel(root, (spec,))
    replay.prepare_integration()
    state = replay.integrate_ready()
    integration = state['integration']
    worktree = Path(str(integration['worktree_path']))
    base = state['task']['base_commit']

    assert integration['merge_order'] == ['node-001']
    assert integration['merges'][0]['recovered'] is expected_recovered
    assert _git(worktree, 'rev-list', '--first-parent', '--count', f'{base}..HEAD') == '1'


@pytest.mark.parametrize('tamper', ('actor', 'message'))
def test_provider_lookalike_merge_is_not_controller_recovery_authority(
    tmp_path: Path,
    tamper: str,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    finalized = _prepare_changed_node(kernel, spec)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_integration_merge_intent' and not fired:
            fired = True
            raise RuntimeError('crash:merge-intent')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:merge-intent'):
        kernel.integrate_ready()

    state = kernel.state()
    integration_path = Path(str(state['integration']['worktree_path']))
    _git(
        integration_path,
        '-c',
        f'user.name={"Provider Actor" if tamper == "actor" else "CCB Controller"}',
        '-c',
        f'user.email={"provider@example.com" if tamper == "actor" else "ccb-controller@localhost"}',
        'merge',
        '--no-ff',
        '-m',
        str(state['integration']['merge_intent']['message'])
        + ('\nlookalike' if tamper == 'message' else ''),
        str(finalized['reviewed_commit']),
    )

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.integrate_ready()

    assert exc_info.value.code == 'integration_merge_authority_drift'
    assert kernel.state()['integration']['merge_order'] == []


def test_cleanup_removes_only_owned_worktrees_and_branches_and_is_idempotent(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    accepted = kernel.accept()
    unrelated_branch = 'user/unrelated'
    unrelated_path = tmp_path / 'unrelated-worktree'
    _git(root, 'branch', unrelated_branch)
    _git(root, 'worktree', 'add', str(unrelated_path), unrelated_branch)
    owned_paths = [
        Path(str(accepted['integration']['worktree_path'])),
        Path(str(accepted['nodes'][spec.node_id]['worktree_path'])),
    ]
    owned_branches = [
        str(accepted['integration']['branch']),
        str(accepted['nodes'][spec.node_id]['branch']),
    ]
    assert kernel.cleanup_readiness(evidence_captured=True)['eligible'] is True

    cleaned = kernel.cleanup(active_workspaces=())
    replayed = kernel.cleanup(active_workspaces=())

    assert cleaned['status'] == 'complete'
    assert replayed == cleaned
    assert cleaned['worktrees_preserved'] is False
    assert all(not path.exists() for path in owned_paths)
    for branch in owned_branches:
        result = subprocess.run(
            ['git', '-C', str(root), 'show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
            check=False,
        )
        assert result.returncode == 1
    assert unrelated_path.is_dir()
    assert _git(root, 'show-ref', '--verify', f'refs/heads/{unrelated_branch}')


def test_cleanup_crash_after_owned_worktree_removal_replays_without_unrelated_removal(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    kernel.accept()
    kernel.cleanup_readiness(evidence_captured=True)
    unrelated_branch = 'user/unrelated'
    _git(root, 'branch', unrelated_branch)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_cleanup_worktree_removed' and not fired:
            fired = True
            raise RuntimeError('crash:cleanup-worktree')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:cleanup-worktree'):
        kernel.cleanup(active_workspaces=())

    replay = _kernel(root, (spec,))
    cleaned = replay.cleanup(active_workspaces=())

    assert cleaned['status'] == 'complete'
    assert _git(root, 'show-ref', '--verify', f'refs/heads/{unrelated_branch}')


def test_cleanup_crash_after_owned_branch_removal_replays(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    kernel.accept()
    kernel.cleanup_readiness(evidence_captured=True)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_cleanup_branch_removed' and not fired:
            fired = True
            raise RuntimeError('crash:cleanup-branch')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:cleanup-branch'):
        kernel.cleanup(active_workspaces=())

    cleaned = _kernel(root, (spec,)).cleanup(active_workspaces=())

    assert cleaned['status'] == 'complete'
    assert all(item['status'] == 'removed' for item in cleaned['branches'])


@pytest.mark.parametrize(
    ('mutation', 'expected_reason'),
    (('dirty', 'owned_worktree_dirty'), ('missing', 'owned_worktree_missing')),
)
def test_cleanup_preserves_dirty_and_missing_owned_workspace_blockers(
    tmp_path: Path,
    mutation: str,
    expected_reason: str,
) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    kernel.accept()
    path = Path(str(kernel.state()['nodes'][spec.node_id]['worktree_path']))
    if mutation == 'dirty':
        (path / spec.allowed_paths[0]).write_text('dirty after terminal\n', encoding='utf-8')
    else:
        subprocess.run(
            ['git', '-C', str(root), 'worktree', 'remove', '--force', str(path)],
            check=True,
        )

    readiness = kernel.cleanup_readiness(evidence_captured=True)
    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.cleanup(active_workspaces=())

    assert readiness['reason'] == expected_reason
    assert exc_info.value.code == expected_reason
    assert kernel.state()['cleanup']['blocker']['code'] == expected_reason
    if mutation == 'dirty':
        assert (path / spec.allowed_paths[0]).read_text(encoding='utf-8') == (
            'dirty after terminal\n'
        )
    else:
        assert not path.exists()


def test_cleanup_rechecks_active_owned_workspace_at_execution_time(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    kernel.accept()
    kernel.cleanup_readiness(evidence_captured=True)
    active = Path(str(kernel.state()['nodes'][spec.node_id]['worktree_path']))

    with pytest.raises(GitIntegrationError) as exc_info:
        kernel.cleanup(active_workspaces=(active,))

    assert exc_info.value.code == 'owned_worktree_active'
    assert active.is_dir()
    assert kernel.state()['cleanup']['blocker']['details']['active_workspaces'] == [
        str(active)
    ]


def test_cleanup_ignores_and_removes_controller_workspace_binding(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    kernel.accept()
    node_worktree = Path(str(kernel.state()['nodes'][spec.node_id]['worktree_path']))
    binding = node_worktree / '.ccb-workspace.json'
    binding.write_text('{"controller_owned": true}\n', encoding='utf-8')
    git_status = _git(node_worktree, 'status', '--porcelain')
    assert git_status
    assert '.ccb-workspace.json' in git_status

    readiness = kernel.cleanup_readiness(evidence_captured=True)
    cleaned = kernel.cleanup(active_workspaces=())

    assert readiness['eligible'] is True
    assert readiness['dirty_workspaces'] == []
    assert cleaned['status'] == 'complete'
    assert not node_worktree.exists()


def test_cleanup_removes_generated_python_cache_before_clean_worktree_remove(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    (root / '.gitignore').write_text('.ccb/\n', encoding='utf-8')
    _git(root, 'add', '.gitignore')
    _git(root, 'commit', '-m', 'stop ignoring python cache')
    spec = _node(1, allowed_paths=('todo.py', 'tests/test_todo.py'))
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, 'todo.py', 'print("todo")\n')
    _write_node_file(kernel, spec.node_id, 'tests/test_todo.py', 'def test_todo(): pass\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    kernel.finalize_node(spec.node_id)
    kernel.integrate_ready()
    kernel.promote()
    kernel.verify_root()
    kernel.accept()
    integration_worktree = Path(str(kernel.state()['integration']['worktree_path']))
    cache = integration_worktree / 'tests' / '__pycache__'
    cache.mkdir(parents=True)
    (cache / 'test_todo.cpython-311.pyc').write_bytes(b'bytecode')
    assert '?? tests/__pycache__/' in _git(integration_worktree, 'status', '--porcelain')

    readiness = kernel.cleanup_readiness(evidence_captured=True)
    cleaned = kernel.cleanup(active_workspaces=())

    assert readiness['eligible'] is True
    assert readiness['dirty_workspaces'] == []
    assert cleaned['status'] == 'complete'
    assert not integration_worktree.exists()


def test_root_verification_removes_generated_python_cache_from_project_root(
    tmp_path: Path,
) -> None:
    root = _init_repo(tmp_path)
    (root / '.gitignore').write_text('.ccb/\n', encoding='utf-8')
    _git(root, 'add', '.gitignore')
    _git(root, 'commit', '-m', 'stop ignoring python cache')
    spec = _node(1, allowed_paths=('todo.py', 'tests/test_todo.py'))
    root_cache_command = VerificationCommand(
        'root-creates-pycache',
        (
            sys.executable,
            '-c',
            'from pathlib import Path; '
            'p=Path("tests/__pycache__"); '
            'p.mkdir(parents=True, exist_ok=True); '
            '(p/"test_todo.cpython-311.pyc").write_bytes(b"bytecode")',
        ),
        timeout_seconds=10,
    )
    kernel = _kernel(root, (spec,), root_verification=(root_cache_command,))
    kernel.preflight()
    kernel.prepare_integration()
    kernel.prepare_node(spec.node_id)
    _write_node_file(kernel, spec.node_id, 'todo.py', 'print("todo")\n')
    _write_node_file(kernel, spec.node_id, 'tests/test_todo.py', 'def test_todo(): pass\n')
    review = kernel.capture_review_input(spec.node_id, worker_job_id='worker-1')
    kernel.record_review(
        spec.node_id,
        reviewer_job_id='reviewer-1',
        result='pass',
        input_digest=str(review['input_digest']),
        tree_digest=str(review['tree_digest']),
    )
    kernel.finalize_node(spec.node_id)
    kernel.integrate_ready()
    kernel.promote()

    verified = kernel.verify_root()

    assert verified['root']['checks'][-1]['status'] == 'pass'
    assert not (root / 'tests' / '__pycache__').exists()
    assert '__pycache__' not in _git(root, 'status', '--porcelain')


def test_promotion_replay_recovers_applied_delta_without_second_promotion(tmp_path: Path) -> None:
    root = _init_repo(tmp_path)
    spec = _node(1)
    kernel = _kernel(root, (spec,))
    kernel.preflight()
    kernel.prepare_integration()
    _prepare_changed_node(kernel, spec)
    kernel.integrate_ready()
    integrated_head = kernel.state()['integration']['head']
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_root_promotion' and not fired:
            fired = True
            raise RuntimeError('crash:promotion')

    kernel._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:promotion'):
        kernel.promote()
    assert _git(root, 'rev-parse', 'HEAD') == integrated_head

    replay = _kernel(root, (spec,))
    state = replay.promote()

    assert state['root']['promotion']['status'] == 'applied'
    assert state['root']['promotion']['recovered'] is True
    assert _git(root, 'rev-parse', 'HEAD') == integrated_head
