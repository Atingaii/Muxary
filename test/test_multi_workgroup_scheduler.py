from __future__ import annotations

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from cli.models import ParsedLoopRunnerCommand
from cli.services import loop_runner as loop_runner_module
from cli.services.loop_runner import loop_runner_auto
from cli.services.loop_orchestration_bundle import bundle_digest, task_input_digest
from cli.services.multi_workgroup_scheduler import (
    MultiWorkgroupScheduler,
    _round_decision,
    _review_decision_with_reason,
    _verification_commands,
    _worker_terminal_decision,
    resume_pending_multi_workgroup_scheduler,
)
from cli.services.workgroup_integration import GitIntegrationError
from cli.services.workgroup_integration.git_ops import GitOperations


class FakeIntegration:
    def __init__(self, bundle: dict[str, object], root: Path) -> None:
        self.bundle = bundle
        self.root = root
        self.calls: list[object] = []
        self.payload = {
            'status': 'new',
            'nodes': {
                node['node_id']: {
                    'status': 'planned',
                    'worktree_path': str(root / 'worktrees' / node['node_id']),
                    'branch': f'ccb/test/{node["node_id"]}',
                    'base_commit': 'base',
                    'reviewed_commit': None,
                }
                for node in bundle['nodes']
            },
            'integration': {'status': 'planned', 'head': 'base', 'merge_order': []},
            'root': {'promotion': None, 'checks': [], 'rollback': None},
        }

    def preflight(self):
        self.calls.append('preflight')
        return self.payload

    def prepare_integration(self):
        self.calls.append('prepare_integration')
        self.payload['integration']['status'] = 'ready'
        return self.payload

    def prepare_node(self, node_id: str):
        self.calls.append(('prepare_node', node_id))
        path = Path(self.payload['nodes'][node_id]['worktree_path'])
        path.mkdir(parents=True, exist_ok=True)
        self.payload['nodes'][node_id]['status'] = (
            self.payload['nodes'][node_id]['status']
            if self.payload['nodes'][node_id]['status'] != 'planned'
            else 'prepared'
        )
        return self.payload

    def capture_review_input(self, node_id: str, *, worker_job_id: str):
        self.calls.append(('capture_review_input', node_id, worker_job_id))
        return {
            'input_digest': f'sha256:input-{node_id}',
            'tree_digest': f'git-tree:sha1:{node_id}',
        }

    def record_review(self, node_id: str, **kwargs):
        self.calls.append(('record_review', node_id, kwargs['reviewer_job_id']))
        self.payload['nodes'][node_id]['review'] = {
            'input_digest': kwargs['input_digest'],
            'tree_digest': kwargs['tree_digest'],
            'reviewer_job_id': kwargs['reviewer_job_id'],
            'result': kwargs['result'],
            'recorded_at': '2026-07-11T00:00:00Z',
        }
        self.payload['nodes'][node_id]['reviewed_tree_digest'] = kwargs['tree_digest']
        self.payload['nodes'][node_id]['status'] = (
            'review_passed' if kwargs['result'] == 'pass' else 'review_rejected'
        )
        return kwargs

    def record_node_failure(self, node_id: str, *, authority_id: str, job_id: str | None, source: str):
        self.calls.append(('record_node_failure', node_id, authority_id, job_id, source))
        self.payload['nodes'][node_id]['status'] = 'excluded'
        self.payload['nodes'][node_id]['terminal_failure'] = {
            'job_id': job_id,
            'authority_id': authority_id,
            'source': source,
        }
        return self.payload['nodes'][node_id]

    def finalize_node(self, node_id: str):
        self.calls.append(('finalize_node', node_id))
        commit = f'commit-{node_id}'
        self.payload['nodes'][node_id]['status'] = 'integration_ready'
        self.payload['nodes'][node_id]['reviewed_commit'] = commit
        return {**self.payload['nodes'][node_id], 'reviewed_commit': commit}

    def integrate_ready(self):
        self.calls.append('integrate_ready')
        changed = True
        while changed:
            changed = False
            for node in self.bundle['nodes']:
                record = self.payload['nodes'][node['node_id']]
                if record['status'] != 'integration_ready':
                    continue
                if not all(
                    self.payload['nodes'][dep]['status'] == 'integrated'
                    for dep in node['depends_on']
                ):
                    continue
                record['status'] = 'integrated'
                self.payload['integration']['merge_order'].append(node['node_id'])
                changed = True
        if all(
            record['status'] in {'integrated', 'excluded'}
            for record in self.payload['nodes'].values()
        ):
            self.payload['integration']['status'] = 'verified'
        return self.payload

    def promote(self):
        self.calls.append('promote')
        self.payload['root']['promotion'] = {'status': 'applied'}
        return self.payload

    def verify_root(self):
        self.calls.append('verify_root')
        self.payload['root']['checks'] = [{'status': 'pass'}]
        return self.payload

    def accept(self):
        self.calls.append('accept')
        self.payload['status'] = 'accepted'
        return self.payload

    def rollback(self, *, reason: str):
        self.calls.append(('rollback', reason))
        self.payload['status'] = 'rolled_back'
        self.payload['root']['rollback'] = {'status': 'restored', 'reason': reason}
        return self.payload

    def close_without_promotion(self, *, result: str, reason: str):
        self.calls.append(('close_without_promotion', result, reason))
        self.payload['status'] = 'replan_required' if result == 'replan_required' else 'integration_failed'
        self.payload['closure'] = {'result': result, 'reason': reason}
        return self.payload

    def cleanup_readiness(self, *, evidence_captured: bool, active_workspaces):
        active = tuple(active_workspaces)
        self.calls.append(('cleanup_readiness', evidence_captured, active))
        return {'eligible': evidence_captured and not active, 'reason': 'eligible' if not active else 'active'}

    def cleanup(self, *, active_workspaces):
        active = tuple(active_workspaces)
        self.calls.append(('cleanup', active))
        return {'status': 'complete', 'active_workspaces': list(active)}

    def state(self):
        return self.payload


class Harness:
    def __init__(self, root: Path, bundle: dict[str, object], integration: FakeIntegration) -> None:
        self.root = root
        self.bundle = bundle
        self.integration = integration
        self.jobs: dict[tuple[str, str], dict[str, object]] = {}
        self.job_attempts: dict[tuple[str, str, int], dict[str, object]] = {}
        self.submissions: list[tuple[str, str]] = []
        self.controller_submissions: list[tuple[str, str]] = []
        self.submission_attempts: list[tuple[str, str, int]] = []
        self.messages: dict[tuple[str, str], str] = {}
        self.bindings: list[dict[str, object]] = []
        self.demand_calls: list[dict[str, object]] = []
        self.imports: list[object] = []
        self.release = {
            'loop_topology_status': 'released',
            'released_count': len(bundle['nodes']) * 2 + 1,
            'retained_count': 0,
            'release_incomplete_count': 0,
        }
        self.observed_agents: list[dict[str, object]] = []
        self.include_release_observed = True
        self.status_observed_path: Path | None = None
        self.current_capacity_digest = str(bundle['capacity_digest'])
        self.apply_status = 'ready'
        self.submit_failures: set[tuple[str, str]] = set()

    def services(self):
        return SimpleNamespace(
            workgroup_integration_factory=lambda _scheduler: self.integration,
            compile_workgroup_mount_demand=self.compile_demand,
            apply_workgroup_topology=lambda *_args: {'loop_topology_status': self.apply_status},
            release_workgroup_topology=self.release_topology,
            workgroup_topology_status=self.topology_status,
            bind_workgroup_workspace=self.bind_workspace,
            submit_or_recover_ask_once=self.submit,
            plan_task=self.plan_task,
            task_text=lambda *_args: 'task execution evidence',
            workgroup_capacity_digest=lambda _context: self.current_capacity_digest,
        )

    def release_topology(self, *_args):
        payload = dict(self.release)
        if self.include_release_observed:
            payload['observed'] = {
                'agents': list(self.observed_agents),
                'retained_count': self.release.get('retained_count', 0),
                'release_incomplete_count': self.release.get('release_incomplete_count', 0),
            }
        if self.status_observed_path is not None:
            payload['observed_path'] = str(self.status_observed_path)
        return payload

    def topology_status(self, *_args):
        payload = {
            'loop_topology_status': self.release.get('loop_topology_status'),
            'observed': {
                'revision': 1,
                'status': self.release.get('loop_topology_status'),
                'agent_count': len(self.observed_agents),
            },
        }
        if self.status_observed_path is not None:
            payload['observed_path'] = str(self.status_observed_path)
        return payload

    def compile_demand(self, _root, bundle, *, active_node_ids, control_profiles=(), **_kwargs):
        active = list(active_node_ids)
        self.demand_calls.append(
            {'active_node_ids': list(active), 'control_profiles': list(control_profiles)}
        )
        bindings = [
            {
                'node_id': node_id,
                'workgroup_id': f'wg-{node_id}',
                'attempt': 1,
                'workspace_group': f'compact-{node_id}',
                'worker_profile': 'coder',
                'reviewer_profile': 'code_reviewer',
                'worker_agent': f'compact-{node_id}-worker',
                'reviewer_agent': f'compact-{node_id}-reviewer',
                'window_name': 'ccb-exec',
                'pane_orders': {'coder': 0, 'code_reviewer': 1},
            }
            for node_id in active
        ]
        controls = (
            [{'profile': 'ccb_round_reviewer', 'agent': 'compact-round-reviewer'}]
            if control_profiles
            else []
        )
        return {
            'bindings': bindings,
            'control_bindings': controls,
            'mount_topology': {
                'schema': 'ccb.loop.agent_mount_topology.v1',
                'nodes': active,
                'controls': list(control_profiles),
            },
        }

    def bind_workspace(self, _context, **kwargs):
        self.bindings.append(kwargs)

    def submit(self, _context, *, target: str, purpose: str, node_id: str, attempt: int, **_kwargs):
        key = (node_id, purpose)
        attempt_key = (node_id, purpose, attempt)
        if attempt_key not in self.job_attempts:
            self.submissions.append(key)
            self.controller_submissions.append(key)
            self.submission_attempts.append(attempt_key)
            result = {
                'target': target,
                'purpose': purpose,
                'job_id': f'job-{node_id}-{purpose}-{attempt}',
                'status': 'running',
                'terminal': False,
                'reply': '',
                'submission_identity': {
                    'bundle_revision': 1,
                    'node_id': node_id,
                    'purpose': purpose,
                    'attempt': attempt,
                },
                'allowed_chain_targets': list(_kwargs.get('allowed_chain_targets') or ()),
                'bind_chain_workspace_tree': bool(_kwargs.get('bind_chain_workspace_tree')),
            }
            self.job_attempts[attempt_key] = result
            if key in self.submit_failures:
                result.update(status='failed', terminal=True)
        self.jobs[key] = self.job_attempts[attempt_key]
        self.messages[key] = str(_kwargs.get('message') or '')
        return dict(self.job_attempts[attempt_key])

    def complete(
        self,
        node_id: str,
        purpose: str,
        *,
        attempt: int | None = None,
        reply: str = 'status: done',
        status: str = 'completed',
    ):
        result = (
            self.job_attempts[(node_id, purpose, attempt)]
            if attempt is not None
            else self.jobs[(node_id, purpose)]
        )
        if purpose == 'worker' and status == 'completed':
            result.update(status='running', terminal=False, implementation_complete=True, reply=reply)
            self._start_internal_job(node_id, 'reviewer', attempt=1)
            return
        result.update(status=status, terminal=True, reply=reply)
        if purpose not in {'reviewer', 'reviewer_recheck'}:
            if purpose == 'worker_rework' and status == 'completed':
                self._start_internal_job(node_id, 'reviewer_recheck', attempt=int(attempt or 1))
            return
        root = self.jobs[(node_id, 'worker')]
        chain = root.setdefault('chain_evidence', [])
        reviewer_target = f'compact-{node_id}-reviewer'
        workspace = next(
            (
                Path(str(binding['workspace_path']))
                for binding in self.bindings
                if str(binding.get('workspace_group') or '') == f'compact-{node_id}'
            ),
            self.root / 'worktrees' / node_id,
        )
        try:
            review_tree_digest = GitOperations(self.root).current_tree_digest(
                workspace,
                ignore_controller_state=True,
            )
        except Exception:
            review_tree_digest = f'git-tree:sha1:{node_id}'
        chain.append(
            {
                'edge_id': f'cb-{node_id}-{purpose}-{int(attempt or 1)}',
                'parent_job_id': root['job_id'],
                'child_job_id': result['job_id'],
                'child_agent': reviewer_target,
                'state': 'done',
                'child_status': status,
                'reply': reply,
                'review_workspace_path': str(workspace),
                'review_tree_digest': review_tree_digest,
            }
        )
        decision = _review_status(reply)
        maximum = int(self.bundle['policy']['max_node_rework_rounds'])
        if status != 'completed' or decision in {'pass', 'blocked', 'non_converged'}:
            root.update(
                status='completed',
                terminal=True,
                reply='status: done' if decision == 'pass' else 'status: blocked',
            )
            return
        if decision == 'rework_required' and len(chain) <= maximum:
            self._start_internal_job(node_id, 'worker_rework', attempt=len(chain))
            return
        root.update(status='completed', terminal=True, reply='status: done')

    def _start_internal_job(self, node_id: str, purpose: str, *, attempt: int) -> None:
        attempt_key = (node_id, purpose, attempt)
        if attempt_key in self.job_attempts:
            return
        target = (
            f'compact-{node_id}-reviewer'
            if purpose in {'reviewer', 'reviewer_recheck'}
            else f'compact-{node_id}-worker'
        )
        result = {
            'target': target,
            'purpose': purpose,
            'job_id': f'job-{node_id}-{purpose}-{attempt}',
            'status': 'running',
            'terminal': False,
            'reply': '',
            'submission_identity': {
                'bundle_revision': 1,
                'node_id': node_id,
                'purpose': purpose,
                'attempt': attempt,
            },
            'internal_chain': True,
        }
        if (node_id, purpose) in self.submit_failures:
            result.update(status='failed', terminal=True)
        self.submissions.append((node_id, purpose))
        self.submission_attempts.append(attempt_key)
        self.job_attempts[attempt_key] = result
        self.jobs[(node_id, purpose)] = result
        if result['terminal'] and purpose in {'reviewer', 'reviewer_recheck'}:
            self.complete(node_id, purpose, attempt=attempt, status='failed')

    def plan_task(self, _context, command):
        assert command.action == 'task-import-round'
        self.imports.append(command)
        return {'status': 'done' if command.result == 'pass' else command.result, 'result': command.result}


def _run_until_job_submitted(
    scheduler: MultiWorkgroupScheduler,
    harness: Harness,
    node_id: str,
    purpose: str,
    *,
    max_runs: int = 4,
) -> None:
    last_state: dict[str, object] | None = None
    for _attempt in range(max_runs):
        if (node_id, purpose) in harness.jobs:
            return
        payload = scheduler.run_once()
        last_state = {
            key: payload.get(key)
            for key in (
                'scheduler_action',
                'controller_status',
                'round_result',
                'round_result_source',
                'failure',
            )
            if payload.get(key) is not None
        }
    raise AssertionError(
        f'job was not submitted after {max_runs} scheduler runs: '
        f'{node_id}/{purpose}; last_state={last_state}'
    )


def _review_status(reply: str) -> str:
    for line in str(reply or '').splitlines():
        if line.strip().lower().startswith('status:'):
            return line.split(':', 1)[1].strip().lower()
    return 'malformed'


def _record(root: Path) -> dict[str, object]:
    artifact = root / 'execution-contract.md'
    artifact.write_text(
        '# Execution Contract\n\nVerification:\n- python -m unittest test_integration.py\n',
        encoding='utf-8',
    )
    (root / 'test_integration.py').write_text(
        'from pathlib import Path\n'
        'import unittest\n\n'
        'class IntegrationTest(unittest.TestCase):\n'
        '    def test_worker_outputs(self):\n'
        "        outputs = list(Path('parts').glob('*/result.txt'))\n"
        '        self.assertTrue(outputs)\n'
        '        self.assertTrue(all(path.read_text().strip() for path in outputs))\n',
        encoding='utf-8',
    )
    return {
        'task_id': 'task-g3',
        'task_revision': 1,
        'artifacts': {
            'task_packet': {'path': 'execution-contract.md', 'sha256': 'a'},
            'execution_contract': {'path': 'execution-contract.md', 'sha256': 'b'},
        },
    }


def _bundle(
    record: dict[str, object],
    count: int,
    *,
    mixed: bool = False,
    max_rework: int = 1,
) -> dict[str, object]:
    nodes = []
    for index in range(1, count + 1):
        node_id = f'node-{index:03d}'
        depends = ['node-001'] if mixed and index == 3 else []
        nodes.append(
            {
                'node_id': node_id,
                'workgroup_id': f'wg-{index:03d}',
                'worker_profile': 'coder',
                'reviewer_profile': 'code_reviewer',
                'depends_on': depends,
                'parallel_group': 'wave-2' if depends else 'wave-1',
                'work_packet_ref': 'execution-contract.md',
                'allowed_paths': [f'parts/{index}/'],
                'acceptance_refs': ['execution-contract.md'],
                'verification_refs': ['execution-contract.md'],
                'integration_order': index * 10,
            }
        )
    return {
        'schema': 'ccb.loop.orchestration_bundle.v1',
        'task_id': record['task_id'],
        'task_revision': 1,
        'task_digest': task_input_digest(record),
        'capacity_digest': 'sha256:' + ('c' * 64),
        'bundle_revision': 1,
        'selection': {
            'workgroup_count': count,
            'complexity': 'bounded',
            'cutability': 'high',
            'execution_shape': 'mixed_dag' if mixed else 'parallel',
            'rationale': 'bounded workgroups',
        },
        'nodes': nodes,
        'integration': {
            'verification_refs': ['execution-contract.md'],
            'project_root_verification_refs': ['execution-contract.md'],
        },
        'policy': {
            'max_node_rework_rounds': max_rework,
            'on_required_node_failure': 'partial_or_blocked',
            'on_structural_failure': 'replan_required',
        },
    }


def _scheduler(tmp_path: Path, count: int, *, mixed: bool = False, max_rework: int = 1):
    root = tmp_path / 'repo'
    root.mkdir()
    record = _record(root)
    bundle = _bundle(record, count, mixed=mixed, max_rework=max_rework)
    integration = FakeIntegration(bundle, root)
    harness = Harness(root, bundle, integration)
    context = SimpleNamespace(
        project=SimpleNamespace(project_root=root, project_id='project-g3'),
    )
    scheduler = MultiWorkgroupScheduler(
        context,
        loop_id='loop-g3',
        task_record=record,
        bundle=bundle,
        bundle_artifact={'bundle_digest': bundle_digest(bundle)},
        services=harness.services(),
    )
    return scheduler, harness, integration


def _real_r2_scheduler(tmp_path: Path, *, max_rework: int):
    root = tmp_path / 'real-r2-repo'
    root.mkdir()
    record = _record(root)
    (root / '.gitignore').write_text('.ccb/\n', encoding='utf-8')
    _git(root, 'init')
    _git(root, 'config', 'user.name', 'Test User')
    _git(root, 'config', 'user.email', 'test@example.com')
    _git(root, 'add', '.')
    _git(root, 'commit', '-m', 'base')
    bundle = _bundle(record, 1, max_rework=max_rework)
    harness = Harness(root, bundle, FakeIntegration(bundle, root))
    services = harness.services()
    delattr(services, 'workgroup_integration_factory')
    context = SimpleNamespace(
        project=SimpleNamespace(project_root=root, project_id='project-real-r2-rework'),
    )
    scheduler = MultiWorkgroupScheduler(
        context,
        loop_id='loop-real-r2-rework',
        task_record=record,
        bundle=bundle,
        bundle_artifact={'bundle_digest': bundle_digest(bundle)},
        services=services,
    )
    return scheduler, harness, root


def _write_node_result(scheduler: MultiWorkgroupScheduler, text: str) -> Path:
    state = json.loads(scheduler.state_path.read_text(encoding='utf-8'))
    path = Path(state['nodes']['node-001']['worktree_path']) / 'parts/1/result.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


@pytest.mark.parametrize('count', (1, 2, 3, 4))
def test_scheduler_submits_entire_ready_frontier_before_any_reviewer(tmp_path: Path, count: int) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, count)

    result = scheduler.run_once()

    expected = [(f'node-{index:03d}', 'worker') for index in range(1, count + 1)]
    assert harness.submissions == expected
    assert result['scheduler_action'] == 'submitted_ready_frontier'
    assert result['loop_runner_status'] == 'pending'
    assert all(node['worker_agent'].startswith('compact-') for node in result['nodes'].values())
    assert not any(purpose.startswith('reviewer') for _node_id, purpose in harness.submissions)
    assert harness.controller_submissions == expected
    assert {item['workspace_group'] for item in harness.bindings} == {
        f'compact-node-{index:03d}' for index in range(1, count + 1)
    }


def test_scheduler_orders_review_integration_round_release_and_cleanup(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    scheduler.run_once()
    for node_id in ('node-001', 'node-002'):
        harness.complete(node_id, 'worker')

    pending_review = scheduler.run_once()
    assert harness.submissions[-2:] == [('node-001', 'reviewer'), ('node-002', 'reviewer')]
    assert pending_review['loop_runner_status'] == 'pending'
    for node_id in ('node-001', 'node-002'):
        harness.complete(node_id, 'reviewer', reply='status: pass')

    pending_round = scheduler.run_once()
    assert ('round', 'ccb_round_reviewer') in harness.submissions
    assert pending_round['controller_status'] == 'round_review_pending'
    round_message = harness.messages[('round', 'ccb_round_reviewer')]
    assert len(round_message.encode('utf-8')) < 4 * 1024
    assert '"schema":"ccb.loop.round_review_envelope.v1"' in round_message
    assert '"review_input"' not in round_message
    assert '"worktree_path"' not in round_message
    assert '"reviewer_job_id":"job-node-001-reviewer-1"' in round_message
    assert '"reviewer_job_id":"job-node-002-reviewer-1"' in round_message
    assert '"review_result":"pass"' in round_message
    assert '"controller_authored_node_reviewer_jobs":false' in round_message
    assert '"controller_scope_validation_passed":true' in round_message
    assert '"worker_owned_review_chain_verified":true' in round_message
    assert '"final_round_reviewer_release_required_after_reply":true' in round_message
    assert '"bundle_digest":"' in round_message
    assert '"results_digest":"sha256:' in round_message
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert final['controller_status'] == 'pass'
    assert final['task_status'] == 'done'
    assert integration.payload['integration']['merge_order'] == ['node-001', 'node-002']
    assert integration.calls.index('promote') < integration.calls.index('verify_root') < integration.calls.index('accept')
    assert any(call[0] == 'cleanup_readiness' and call[2] == () for call in integration.calls if isinstance(call, tuple))
    assert ('cleanup', ()) in integration.calls
    assert final['topology']['observed_evidence']['source'] == 'release_payload'
    assert 'agents' not in final['topology']['status_after_release']['observed']
    assert harness.controller_submissions == [
        ('node-001', 'worker'),
        ('node-002', 'worker'),
        ('round', 'ccb_round_reviewer'),
    ]


def test_round_reviewer_envelope_stays_inline_at_four_workgroups(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 4)
    scheduler.run_once()
    for node_id in ('node-001', 'node-002', 'node-003', 'node-004'):
        harness.complete(node_id, 'worker')
    scheduler.run_once()
    for node_id in ('node-001', 'node-002', 'node-003', 'node-004'):
        harness.complete(node_id, 'reviewer', reply='status: pass')

    pending_round = scheduler.run_once()
    round_message = harness.messages[('round', 'ccb_round_reviewer')]

    assert pending_round['controller_status'] == 'round_review_pending'
    assert len(round_message.encode('utf-8')) < 4 * 1024
    assert '"schema":"ccb.loop.round_review_envelope.v1"' in round_message
    assert '"node-004"' in round_message


def test_scheduler_rejects_bare_node_reviewer_pass_without_status_contract(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete(
        'node-001',
        'reviewer',
        reply='pass\n\nReviewed exact tree and found no blockers.',
    )
    scheduler.run_once()
    final = scheduler.run_once()

    assert final['round_result'] == 'blocked'
    assert final['controller_status'] == 'blocked'
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert integration.payload['status'] != 'accepted'


@pytest.mark.parametrize(
    ('reply', 'decision', 'reason'),
    [
        ('status: pass', 'pass', 'reviewer_status'),
        ('\n\nstatus: pass', 'pass', 'reviewer_status'),
        ('status: rework_required\nRepair this file.', 'rework_required', 'reviewer_status'),
        ('- status: pass', None, 'malformed_reviewer_status'),
        ('Status: pass', None, 'malformed_reviewer_status'),
        ('```\nstatus: pass', None, 'malformed_reviewer_status'),
        ('Reviewed.\nstatus: pass', None, 'malformed_reviewer_status'),
        ('status: approved', None, 'malformed_reviewer_status'),
        ('status: pass\nstatus: pass', None, 'duplicate_or_conflicting_reviewer_status'),
        ('status: pass\n- STATUS: blocked', None, 'duplicate_or_conflicting_reviewer_status'),
    ],
)
def test_reviewer_terminal_status_parser_is_strict(
    reply: str,
    decision: str | None,
    reason: str,
) -> None:
    assert _review_decision_with_reason(reply) == (decision, reason)


@pytest.mark.parametrize(
    ('reply', 'decision', 'reason'),
    [
        ('status: done', 'done', 'worker_status'),
        ('\nstatus: done', 'done', 'worker_status'),
        ('status: blocked\nCannot access worktree.', 'blocked', 'worker_status'),
        ('status: needs_rework', 'needs_rework', 'worker_status'),
        ('done', None, 'malformed_worker_status'),
        ('Status: done', None, 'malformed_worker_status'),
        ('status: pass', None, 'malformed_worker_status'),
        ('status: done\nstatus: blocked', None, 'duplicate_or_conflicting_worker_status'),
    ],
)
def test_worker_terminal_status_parser_is_strict(
    reply: str,
    decision: str | None,
    reason: str,
) -> None:
    assert _worker_terminal_decision(reply) == (decision, reason)


def test_scheduler_worker_prompt_injects_only_assigned_reviewer_chain_contract(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    state = json.loads(scheduler.state_path.read_text(encoding='utf-8'))
    node = state['nodes']['node-001']
    request = harness.job_attempts[('node-001', 'worker', 1)]
    message = scheduler._node_message(state, node, purpose='worker')

    assert 'Assigned reviewer: compact-node-001-reviewer' in message
    assert f'Project authority root: {scheduler.project_root}' in message
    assert 'Authority refs below are read-only project-root evidence' in message
    assert f'Work packet ref: {scheduler.project_root}/execution-contract.md' in message
    assert f'Acceptance refs: ["{scheduler.project_root}/execution-contract.md"]' in message
    assert f'Verification refs: ["{scheduler.project_root}/execution-contract.md"]' in message
    assert 'ask --chain --artifact-reply' in message
    assert 'first non-empty reply line' in message
    assert 'no preamble or code fence' in message
    assert 'Do not use plain ask, silence, another target' in message
    assert request['allowed_chain_targets'] == ['compact-node-001-reviewer']
    assert request['bind_chain_workspace_tree'] is True
    assert not any(purpose.startswith('reviewer') for _node_id, purpose in harness.submissions)
    assert harness.controller_submissions == [('node-001', 'worker')]


def test_scheduler_rejects_completed_worker_without_review_chain(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    root = harness.jobs[('node-001', 'worker')]
    root.update(status='completed', terminal=True, reply='status: done')

    final = scheduler.run_once()

    assert final['nodes']['node-001']['status'] == 'review_failed'
    assert final['nodes']['node-001']['failure']['source'] == 'worker_owned_review_chain_invalid'
    assert 'review_chain_missing' in final['nodes']['node-001']['failure']['reasons']
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert harness.controller_submissions == [('node-001', 'worker')]


def test_scheduler_waits_for_callback_edge_to_finish_before_validating_chain(
    tmp_path: Path,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    root = harness.jobs[('node-001', 'worker')]
    root['chain_evidence'][0]['state'] = 'continuation_submitted'

    pending = scheduler.run_once()

    node = pending['nodes']['node-001']
    assert node['status'] == 'worker_pending'
    assert node['worker']['pending_source'] == 'worker_review_chain_pending'
    assert node['worker']['terminal'] is False
    assert node['failure'] is None
    assert ('finalize_node', 'node-001') not in integration.calls

    root['chain_evidence'][0]['state'] = 'done'
    completed = scheduler.run_once()

    assert completed['nodes']['node-001']['status'] == 'integrated'
    assert ('finalize_node', 'node-001') in integration.calls


@pytest.mark.parametrize(
    ('reply', 'reason'),
    [
        ('status: blocked', 'worker_terminal_not_done_blocked'),
        ('status: needs_rework', 'worker_terminal_not_done_needs_rework'),
        ('done', 'malformed_worker_status'),
        ('status: done\nstatus: blocked', 'duplicate_or_conflicting_worker_status'),
    ],
)
def test_invalid_worker_terminal_never_finalizes_node(
    tmp_path: Path,
    reply: str,
    reason: str,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    root = harness.jobs[('node-001', 'worker')]
    root.update(
        status='completed',
        terminal=True,
        reply=reply,
        chain_evidence=[
            {
                'edge_id': 'cb-pass',
                'child_job_id': 'job-pass',
                'child_agent': 'compact-node-001-reviewer',
                'state': 'done',
                'child_status': 'completed',
                'reply': 'status: pass',
                'review_tree_digest': 'git-tree:sha1:node-001',
            }
        ],
    )

    final = scheduler.run_once()

    node = final['nodes']['node-001']
    assert node['status'] == 'review_failed'
    assert node['failure']['source'] == 'worker_terminal_invalid'
    assert node['failure']['reasons'] == [reason]
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert ('finalize_node', 'node-001') not in integration.calls


def test_invalid_reviewer_verdict_never_finalizes_node(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass\nstatus: blocked')

    final = scheduler.run_once()

    node = final['nodes']['node-001']
    assert node['status'] == 'review_failed'
    assert node['failure']['source'] == 'reviewer_verdict_invalid'
    assert 'review_chain_final_malformed' in node['failure']['reasons']
    assert 'reviewer_verdict_duplicate_or_conflicting_reviewer_status' in node['failure']['reasons']
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert ('finalize_node', 'node-001') not in integration.calls


def test_scheduler_rejects_chain_to_unassigned_reviewer(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    harness.complete('node-001', 'reviewer', reply='status: pass')
    harness.jobs[('node-001', 'worker')]['chain_evidence'][0]['child_agent'] = 'other-reviewer'

    final = scheduler.run_once()

    assert final['nodes']['node-001']['status'] == 'review_failed'
    assert 'review_chain_target_mismatch' in final['nodes']['node-001']['failure']['reasons']
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert harness.controller_submissions == [('node-001', 'worker')]


def test_scheduler_rejects_final_tree_that_differs_from_bound_review_tree(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    harness.complete('node-001', 'reviewer', reply='status: pass')
    harness.jobs[('node-001', 'worker')]['chain_evidence'][0][
        'review_tree_digest'
    ] = 'git-tree:sha1:different-tree'

    final = scheduler.run_once()

    assert final['nodes']['node-001']['status'] == 'review_failed'
    assert final['nodes']['node-001']['failure']['reasons'] == [
        'review_chain_tree_digest_mismatch'
    ]
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert harness.controller_submissions == [('node-001', 'worker')]


def test_scheduler_rejects_nonfinal_pass_hidden_before_final_pass(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1, max_rework=1)
    scheduler.run_once()
    root = harness.jobs[('node-001', 'worker')]
    root.update(
        status='completed',
        terminal=True,
        reply='status: done',
        chain_evidence=[
            {
                'edge_id': 'cb-early-pass',
                'child_job_id': 'job-early-pass',
                'child_agent': 'compact-node-001-reviewer',
                'state': 'done',
                'child_status': 'completed',
                'reply': 'status: pass',
                'review_tree_digest': 'git-tree:sha1:node-001',
            },
            {
                'edge_id': 'cb-final-pass',
                'child_job_id': 'job-final-pass',
                'child_agent': 'compact-node-001-reviewer',
                'state': 'done',
                'child_status': 'completed',
                'reply': 'status: pass',
                'review_tree_digest': 'git-tree:sha1:node-001',
            },
        ],
    )

    final = scheduler.run_once()

    assert final['nodes']['node-001']['status'] == 'review_failed'
    assert 'review_chain_nonfinal_verdict_invalid' in final['nodes']['node-001']['failure']['reasons']
    assert integration.payload['nodes']['node-001']['reviewed_commit'] is None
    assert harness.controller_submissions == [('node-001', 'worker')]


def test_verification_parser_stops_before_scope_notes_bullets(tmp_path: Path) -> None:
    contract = tmp_path / 'execution_contract.md'
    contract.write_text(
        '# Execution Contract\n'
        'Route: direct_execution\n\n'
        'Verification:\n'
        '- python -m unittest discover -s tests -p test_todo.py\n'
        '\n'
        'Scope notes:\n'
        '- Do not change implementation in this task.\n'
        '- Keep changes within the allowed path.\n',
        encoding='utf-8',
    )

    commands = _verification_commands(tmp_path, ['execution_contract.md'], prefix='root')

    assert [command.argv for command in commands] == [
        ('python', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_todo.py')
    ]


def test_verification_parser_rejects_prose_as_an_argv_command(tmp_path: Path) -> None:
    contract = tmp_path / 'execution_contract.md'
    contract.write_text(
        '# Execution Contract\n\n'
        'Verification:\n'
        '- python -m unittest discover -s tests\n'
        '- Review docs/api.md for English API coverage.\n',
        encoding='utf-8',
    )

    with pytest.raises(ValueError, match='not an executable argv command'):
        _verification_commands(tmp_path, ['execution_contract.md'], prefix='integration')


def test_scheduler_accepts_legacy_round_result_field_with_space(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass\n\nNo blockers.')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert final['controller_status'] == 'pass'
    assert integration.payload['status'] == 'accepted'


def test_scheduler_rejects_noncanonical_late_round_result(
    tmp_path: Path,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete(
        'round',
        'ccb_round_reviewer',
        reply=(
            '根据角色定义，我需要审查证据。\n\n'
            '**证据分析：**\n'
            '- 集成验证通过\n'
            '- 清理验证通过\n\n'
            'round result: pass'
        ),
    )

    final = scheduler.run_once()

    assert final['round_result'] == 'replan_required'
    assert final['controller_status'] == 'replan_required'
    assert integration.payload['status'] == 'rolled_back'


@pytest.mark.parametrize(
    'reply',
    (
        'round_result: pass',
        '- round result: pass',
        '```\nround result: pass\n```',
        'preamble\nround result: pass',
        'round result: accepted',
        'round result: pass\nround result: blocked',
    ),
)
def test_round_decision_v3_rejects_noncanonical_or_conflicting_reply(reply: str) -> None:
    assert _round_decision(reply)[0] is None


def test_scheduler_rejects_conflicting_round_result_lines(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete(
        'round',
        'ccb_round_reviewer',
        reply='round result: pass\n\nround_result: blocked',
    )

    final = scheduler.run_once()

    assert final['round_result'] == 'replan_required'
    assert final['round_result_source'] == 'conflicting_round_result'
    assert ('rollback', 'round_reviewer:replan_required') in integration.calls


def test_scheduler_final_round_topology_is_control_only_after_four_nodes_integrate(
    tmp_path: Path,
) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 4, mixed=True)
    scheduler.run_once()
    for node_id in ('node-001', 'node-002', 'node-004'):
        harness.complete(node_id, 'worker')
    scheduler.run_once()
    for node_id in ('node-001', 'node-002', 'node-004'):
        harness.complete(node_id, 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('node-003', 'worker')
    scheduler.run_once()
    harness.complete('node-003', 'reviewer', reply='status: pass')
    scheduler.run_once()

    pending_round = scheduler.run_once()

    assert pending_round['controller_status'] == 'round_review_pending'
    assert harness.demand_calls[-1] == {
        'active_node_ids': [],
        'control_profiles': ['ccb_round_reviewer'],
    }
    assert pending_round['topology']['demand']['bindings'] == []
    assert pending_round['topology']['demand']['mount_topology']['nodes'] == []
    assert pending_round['topology']['demand']['mount_topology']['controls'] == [
        'ccb_round_reviewer'
    ]
    assert all(node['status'] == 'integrated' for node in pending_round['nodes'].values())


def test_mixed_dag_unblocks_dependent_while_independent_sibling_is_pending(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 3, mixed=True)
    scheduler.run_once()
    assert harness.submissions == [('node-001', 'worker'), ('node-002', 'worker')]
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')

    result = scheduler.run_once()

    assert ('node-003', 'worker') in harness.submissions
    assert not harness.jobs[('node-002', 'worker')]['terminal']
    assert result['loop_runner_status'] == 'pending'
    assert integration.payload['nodes']['node-001']['status'] == 'integrated'


def test_bounded_rework_stays_on_same_compacted_agents_and_worktree(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')

    scheduler.run_once()

    assert harness.submissions[-1] == ('node-001', 'worker_rework')
    state = scheduler.run_once()['nodes']['node-001']
    assert state['worker_agent'] == 'compact-node-001-worker'
    assert state['worktree_path'].endswith('/worktrees/node-001')


def test_busy_release_passes_latest_active_workspaces_and_blocks_cleanup(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    harness.release = {
        'loop_topology_status': 'release_incomplete',
        'released_count': 2,
        'retained_count': 1,
        'release_incomplete_count': 0,
    }
    harness.observed_agents = [
        {'id': 'compact-node-001-worker', 'observed_state': 'present'},
    ]

    result = scheduler.run_once()

    worktree = Path(integration.payload['nodes']['node-001']['worktree_path'])
    assert result['controller_status'] == 'release_blocked'
    assert result['loop_runner_status'] == 'pending'
    assert ('cleanup_readiness', True, (worktree,)) in integration.calls
    assert not any(call[0] == 'cleanup' for call in integration.calls if isinstance(call, tuple))

    harness.release = {
        'loop_topology_status': 'released',
        'released_count': 1,
        'retained_count': 0,
        'release_incomplete_count': 0,
    }
    harness.observed_agents = []
    retried = scheduler.run_once()

    assert retried['controller_status'] == 'pass'
    assert ('cleanup', ()) in integration.calls


def test_result_import_crash_resumes_release_without_second_import(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_result_import' and not fired:
            fired = True
            raise RuntimeError('crash:after-result-import')

    scheduler._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:after-result-import'):
        scheduler.run_once()
    assert len(harness.imports) == 1

    resume_services = harness.services()

    def resume_plan_task(context, command):
        if command.action == 'task-show':
            return {'task': scheduler.task_record}
        return harness.plan_task(context, command)

    resume_services.plan_task = resume_plan_task
    final = resume_pending_multi_workgroup_scheduler(
        scheduler.context,
        services=resume_services,
    )

    assert len(harness.imports) == 1
    assert final is not None
    assert final['controller_status'] == 'pass'
    assert ('cleanup', ()) in integration.calls


def test_cleanup_intent_crash_resumes_without_rechecking_readiness(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')

    def crash(name: str, _state: dict[str, object]) -> None:
        if name == 'after_result_import':
            raise RuntimeError('crash:before-cleanup')

    scheduler._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:before-cleanup'):
        scheduler.run_once()
    integration.payload['cleanup'] = {
        'schema': 'ccb.loop.workgroup_cleanup_intent.v1',
        'status': 'executing',
    }
    services = harness.services()

    def resume_plan_task(context, command):
        if command.action == 'task-show':
            return {'task': scheduler.task_record}
        return harness.plan_task(context, command)

    services.plan_task = resume_plan_task
    final = resume_pending_multi_workgroup_scheduler(
        scheduler.context,
        services=services,
    )

    assert final is not None
    assert final['controller_status'] == 'pass'
    assert not any(
        call[0] == 'cleanup_readiness'
        for call in integration.calls
        if isinstance(call, tuple)
    )
    assert ('cleanup', ()) in integration.calls


def test_scheduler_uses_real_r2_worktrees_commits_merge_promotion_and_cleanup(tmp_path: Path) -> None:
    root = tmp_path / 'real-repo'
    root.mkdir()
    record = _record(root)
    (root / '.gitignore').write_text('.ccb/\n', encoding='utf-8')
    _git(root, 'init')
    _git(root, 'config', 'user.name', 'Test User')
    _git(root, 'config', 'user.email', 'test@example.com')
    _git(root, 'add', '.')
    _git(root, 'commit', '-m', 'base')
    bundle = _bundle(record, 2)
    harness = Harness(root, bundle, FakeIntegration(bundle, root))
    services = harness.services()
    delattr(services, 'workgroup_integration_factory')
    context = SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='project-real-r2'))
    scheduler = MultiWorkgroupScheduler(
        context,
        loop_id='loop-real-r2',
        task_record=record,
        bundle=bundle,
        bundle_artifact={'bundle_digest': bundle_digest(bundle)},
        services=services,
    )
    scheduler.run_once()
    state = scheduler.run_once()['nodes']
    for index, node_id in enumerate(('node-001', 'node-002'), start=1):
        path = Path(state[node_id]['worktree_path']) / f'parts/{index}/result.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'{node_id}\n', encoding='utf-8')
        harness.complete(node_id, 'worker')
    scheduler.run_once()
    for node_id in ('node-001', 'node-002'):
        harness.complete(node_id, 'reviewer', reply='status: pass')
    _run_until_job_submitted(scheduler, harness, 'round', 'ccb_round_reviewer')
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')

    final = scheduler.run_once()

    assert final['controller_status'] == 'pass'
    assert (root / 'parts/1/result.txt').read_text(encoding='utf-8') == 'node-001\n'
    assert (root / 'parts/2/result.txt').read_text(encoding='utf-8') == 'node-002\n'
    integration_state = final['paths']['integration_state']
    assert Path(integration_state).is_file()
    assert final['cleanup']['result']['status'] == 'complete'
    assert len(final['cleanup']['removed_workspace_bindings']) == 2
    assert all(
        not Path(path).exists()
        for path in final['cleanup']['removed_workspace_bindings']
    )
    assert _git(root, 'status', '--porcelain') == ''


@pytest.mark.parametrize('cycles', (1, 2))
def test_real_r2_scheduler_records_rework_cycles_then_integrates(
    tmp_path: Path,
    cycles: int,
) -> None:
    scheduler, harness, root = _real_r2_scheduler(tmp_path, max_rework=cycles)
    scheduler.run_once()
    worktree = _write_node_result(scheduler, 'initial\n').parents[2]
    harness.complete('node-001', 'worker')
    scheduler.run_once()

    for cycle in range(1, cycles + 1):
        purpose = 'reviewer' if cycle == 1 else 'reviewer_recheck'
        harness.complete(
            'node-001',
            purpose,
            attempt=cycle - 1 if purpose == 'reviewer_recheck' else None,
            reply='status: rework_required',
        )
        scheduler.run_once()
        assert json.loads(
            (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
        )['nodes']['node-001']['status'] == 'prepared'
        _write_node_result(scheduler, f'rework-{cycle}\n')
        harness.complete('node-001', 'worker_rework', attempt=cycle)
        scheduler.run_once()

    harness.complete('node-001', 'reviewer_recheck', attempt=cycles, reply='status: pass')
    _run_until_job_submitted(scheduler, harness, 'round', 'ccb_round_reviewer')
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    final = scheduler.run_once()
    integration = json.loads(
        (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
    )

    assert final['controller_status'] == 'pass'
    assert [item['result'] for item in integration['nodes']['node-001']['reviews']] == ['pass']
    assert integration['nodes']['node-001']['status'] == 'integrated'
    assert integration['nodes']['node-001']['reviewed_commit']
    assert harness.submission_attempts.count(('node-001', 'worker_rework', cycles)) == 1
    assert [item['decision'] for item in final['nodes']['node-001']['rework_history']] == [
        *(['rework_required'] * cycles),
        'pass',
    ]
    assert final['nodes']['node-001']['worktree_path'] == str(worktree)
    assert (root / 'parts/1/result.txt').read_text(encoding='utf-8') == f'rework-{cycles}\n'


def test_real_r2_exhausted_rework_records_failed_review_without_false_replan(tmp_path: Path) -> None:
    scheduler, harness, _root = _real_r2_scheduler(tmp_path, max_rework=2)
    scheduler.run_once()
    _write_node_result(scheduler, 'initial\n')
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    _write_node_result(scheduler, 'rework-1\n')
    harness.complete('node-001', 'worker_rework', attempt=1)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=1, reply='status: rework_required')
    scheduler.run_once()
    _write_node_result(scheduler, 'rework-2\n')
    harness.complete('node-001', 'worker_rework', attempt=2)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=2, reply='status: rework_required')

    final = scheduler.run_once()
    integration = json.loads(
        (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
    )

    assert final['round_result'] == 'blocked'
    assert final['round_result_source'] == 'required_node_failure'
    assert integration['nodes']['node-001']['reviews'] == []
    assert integration['root']['promotion'] is None
    assert not any(attempt == 3 for _node_id, _purpose, attempt in harness.submission_attempts)


def test_real_r2_rework_stays_inside_worker_chain_without_controller_submit(tmp_path: Path) -> None:
    scheduler, harness, _root = _real_r2_scheduler(tmp_path, max_rework=1)
    scheduler.run_once()
    _write_node_result(scheduler, 'initial\n')
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    integration = json.loads(
        (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
    )
    assert integration['nodes']['node-001']['status'] == 'prepared'
    assert integration['nodes']['node-001']['reviews'] == []
    assert scheduler.run_once()['nodes']['node-001']['status'] == 'worker_pending'
    assert harness.submission_attempts.count(('node-001', 'worker_rework', 1)) == 1


def test_real_r2_blocked_reviewer_records_failed_authority(tmp_path: Path) -> None:
    scheduler, harness, _root = _real_r2_scheduler(tmp_path, max_rework=1)
    scheduler.run_once()
    _write_node_result(scheduler, 'initial\n')
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: blocked')

    final = scheduler.run_once()
    integration = json.loads(
        (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
    )

    assert final['round_result'] == 'blocked'
    assert integration['nodes']['node-001']['reviews'] == []
    assert integration['nodes']['node-001']['status'] == 'excluded'
    assert integration['nodes']['node-001']['terminal_failure']['status'] == 'restored'


def test_real_r2_all_failed_dirty_worker_is_quarantined_before_cleanup(tmp_path: Path) -> None:
    scheduler, harness, _root = _real_r2_scheduler(tmp_path, max_rework=1)
    scheduler.run_once()
    _write_node_result(scheduler, 'failed-worker-delta\n')
    harness.complete('node-001', 'worker', status='failed')

    final = scheduler.run_once()
    integration = json.loads(
        (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
    )
    failure = integration['nodes']['node-001']['terminal_failure']

    assert final['round_result'] == 'blocked'
    assert final['controller_status'] == 'blocked'
    assert integration['nodes']['node-001']['status'] == 'excluded'
    assert failure['schema'] == 'ccb.loop.workgroup_node_failure.v1'
    assert failure['status'] == 'restored'
    assert failure['worktree_status']
    assert Path(failure['quarantine']['manifest_path']).is_file()
    assert final['cleanup']['result']['status'] == 'complete'
    assert not Path(integration['nodes']['node-001']['worktree_path']).exists()


def test_real_r2_exhausted_rework_dirty_delta_is_quarantined_before_cleanup(
    tmp_path: Path,
) -> None:
    scheduler, harness, _root = _real_r2_scheduler(tmp_path, max_rework=1)
    scheduler.run_once()
    _write_node_result(scheduler, 'initial\n')
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    _write_node_result(scheduler, 'rework-exhausted\n')
    harness.complete('node-001', 'worker_rework', attempt=1)
    scheduler.run_once()
    harness.complete(
        'node-001',
        'reviewer_recheck',
        attempt=1,
        reply='status: rework_required',
    )

    final = scheduler.run_once()
    integration = json.loads(
        (scheduler.loop_dir / 'git-transaction.json').read_text(encoding='utf-8')
    )
    failure = integration['nodes']['node-001']['terminal_failure']

    assert final['round_result'] == 'blocked'
    assert final['controller_status'] == 'blocked'
    assert integration['nodes']['node-001']['status'] == 'excluded'
    assert integration['nodes']['node-001']['reviews'] == []
    assert failure['status'] == 'restored'
    assert failure['worktree_status']
    assert Path(failure['quarantine']['manifest_path']).is_file()
    assert final['cleanup']['result']['status'] == 'complete'
    assert not Path(integration['nodes']['node-001']['worktree_path']).exists()


def test_malformed_round_review_rolls_back_and_imports_replan(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='looks good')

    final = scheduler.run_once()

    assert final['round_result'] == 'replan_required'
    assert ('rollback', 'round_reviewer:replan_required') in integration.calls
    assert harness.imports[-1].result == 'replan_required'


def test_capacity_drift_replans_without_submitting_more_provider_jobs(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    scheduler.run_once()
    submitted = list(harness.submissions)
    harness.current_capacity_digest = 'sha256:' + ('d' * 64)

    result = scheduler.run_once()

    assert result['round_result'] == 'replan_required'
    assert result['round_result_source'] == 'scheduler_contract_invalid'
    assert harness.submissions == submitted
    assert ('close_without_promotion', 'replan_required', 'scheduler_contract_invalid') in integration.calls


def test_busy_topology_apply_remains_pending_and_retries_without_provider_submit(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    harness.apply_status = 'retained_busy'

    pending = scheduler.run_once()

    assert pending['controller_status'] == 'topology_pending'
    assert harness.submissions == []
    harness.apply_status = 'ready'
    resumed = scheduler.run_once()

    assert resumed['scheduler_action'] == 'submitted_ready_frontier'
    assert harness.submissions == [('node-001', 'worker'), ('node-002', 'worker')]


def test_scheduler_state_before_git_preflight_crash_replays_initialization(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    fired = False

    def crash(name: str, _state: dict[str, object]) -> None:
        nonlocal fired
        if name == 'after_scheduler_state_before_git_preflight' and not fired:
            fired = True
            raise RuntimeError('crash:before-git-preflight')

    scheduler._checkpoint_hook = crash
    with pytest.raises(RuntimeError, match='crash:before-git-preflight'):
        scheduler.run_once()
    assert scheduler.state_path.is_file()
    assert integration.calls == []

    replay = MultiWorkgroupScheduler(
        scheduler.context,
        loop_id=scheduler.loop_id,
        task_record=scheduler.task_record,
        bundle=scheduler.bundle,
        bundle_artifact=scheduler.bundle_artifact,
        services=harness.services(),
    )
    result = replay.run_once()

    assert result['scheduler_action'] == 'submitted_ready_frontier'
    assert integration.calls[:2] == ['preflight', 'prepare_integration']


def test_one_frontier_submission_failure_does_not_hide_or_serialize_sibling_submit(
    tmp_path: Path,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    harness.submit_failures.add(('node-001', 'worker'))

    result = scheduler.run_once()

    assert harness.submissions == [('node-001', 'worker'), ('node-002', 'worker')]
    assert result['nodes']['node-001']['status'] == 'worker_failed'
    assert result['nodes']['node-002']['status'] == 'worker_pending'


def test_rework_cycle_rechecks_same_tree_then_completes(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework')
    scheduler.run_once()
    assert harness.submissions[-1] == ('node-001', 'reviewer_recheck')
    harness.complete('node-001', 'reviewer_recheck', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert final['nodes']['node-001']['reviewed_commit'] == 'commit-node-001'


def test_independent_worker_failure_preserves_reviewed_sibling_as_partial(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    harness.complete('node-002', 'worker', status='failed')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'partial'
    assert final['nodes']['node-001']['status'] == 'integrated'
    assert final['nodes']['node-002']['status'] == 'worker_failed'
    assert integration.payload['root']['promotion'] is None


def test_structural_integration_failure_imports_replan_without_promotion(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')

    def fail_integration():
        raise GitIntegrationError(
            'integration_merge_conflict',
            'integration.merge.node-001',
            'conflict',
        )

    integration.integrate_ready = fail_integration
    final = scheduler.run_once()

    assert final['round_result'] == 'replan_required'
    assert final['round_result_source'] == 'integration_merge_conflict'
    assert integration.payload['root']['promotion'] is None


def test_reviewer_pass_and_promotion_crash_windows_replay_without_duplicate_import(
    tmp_path: Path,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    fired_review = False

    def crash_review(name: str, _state: dict[str, object]) -> None:
        nonlocal fired_review
        if name == 'after_reviewer_pass_before_node_commit' and not fired_review:
            fired_review = True
            raise RuntimeError('crash:review-pass')

    scheduler._checkpoint_hook = crash_review
    with pytest.raises(RuntimeError, match='crash:review-pass'):
        scheduler.run_once()
    scheduler._checkpoint_hook = None
    fired_promotion = False

    def crash_promotion(name: str, _state: dict[str, object]) -> None:
        nonlocal fired_promotion
        if name == 'after_root_promotion_before_verification' and not fired_promotion:
            fired_promotion = True
            raise RuntimeError('crash:promotion')

    scheduler._checkpoint_hook = crash_promotion
    with pytest.raises(RuntimeError, match='crash:promotion'):
        scheduler.run_once()
    scheduler._checkpoint_hook = None
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')

    final = scheduler.run_once()

    assert final['round_result'] == 'pass'
    assert len(harness.imports) == 1
    assert integration.calls.count(('finalize_node', 'node-001')) == 1


def test_auto_runner_advances_full_multi_workgroup_round_without_manual_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 2)
    terminal_returned = False
    once_calls = 0

    def fake_once(_context, _command, _services):
        nonlocal terminal_returned, once_calls
        once_calls += 1
        if terminal_returned:
            return {'loop_runner_status': 'idle', 'action': 'none'}
        payload = scheduler.run_once()
        if payload['controller_status'] == 'pass':
            terminal_returned = True
        return payload

    def fake_trace(_context, trace_command):
        job_id = trace_command.target
        for result in harness.job_attempts.values():
            if result['job_id'] != job_id:
                continue
            purpose = str(result['purpose'])
            node_id = str(result['submission_identity']['node_id'])
            if purpose == 'worker':
                harness.complete(node_id, 'worker')
                harness.complete(node_id, 'reviewer', reply='status: pass')
            else:
                result.update(status='completed', terminal=True, reply='round result: pass')
            return {'job': {'job_id': job_id, 'status': 'completed'}}
        raise AssertionError(f'unknown wait job: {job_id}')

    monkeypatch.setattr(loop_runner_module, 'loop_runner_once', fake_once)
    command = ParsedLoopRunnerCommand(
        project=None,
        auto=True,
        once=False,
        max_steps=10,
        poll_interval_s=0.0,
        json_output=True,
    )
    payload = loop_runner_auto(
        scheduler.context,
        command,
        services=SimpleNamespace(trace_target=fake_trace, sleep=lambda _seconds: None),
    )

    assert payload['final_action'] == 'none'
    assert once_calls == 5
    assert harness.submissions[:2] == [('node-001', 'worker'), ('node-002', 'worker')]
    assert harness.submissions[2:4] == [('node-001', 'reviewer'), ('node-002', 'reviewer')]
    assert harness.submissions[4] == ('round', 'ccb_round_reviewer')
    assert scheduler.run_once()['controller_status'] == 'pass'
    assert integration.payload['integration']['merge_order'] == ['node-001', 'node-002']
    assert integration.calls.index('promote') < integration.calls.index('verify_root')
    assert ('cleanup', ()) in integration.calls


def test_auto_runner_starts_node_reviewer_before_slower_sibling_worker_finishes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 2)
    terminal_returned = False
    event_log: list[tuple[str, str, str]] = []
    terminal_events: list[tuple[str, str]] = []

    def fake_once(_context, _command, _services):
        nonlocal terminal_returned
        if terminal_returned:
            return {'loop_runner_status': 'idle', 'action': 'none'}
        submission_count = len(harness.submissions)
        payload = scheduler.run_once()
        for node_id, purpose in harness.submissions[submission_count:]:
            event_log.append(('submitted', node_id, purpose))
        if payload['controller_status'] == 'pass':
            terminal_returned = True
        return payload

    def fake_trace(_context, trace_command):
        job_id = trace_command.target
        for result in harness.job_attempts.values():
            if result['job_id'] != job_id:
                continue
            node_id = str(result['submission_identity']['node_id'])
            purpose = str(result['purpose'])
            if node_id == 'node-002' and purpose == 'worker':
                reviewer_one_submitted = ('node-001', 'reviewer') in harness.submissions
                if not reviewer_one_submitted:
                    return {'job': {'job_id': job_id, 'status': 'running'}}
            if not result['terminal']:
                if purpose == 'worker':
                    harness.complete(node_id, 'worker')
                    event_log.append(('submitted', node_id, 'reviewer'))
                    harness.complete(node_id, 'reviewer', reply='status: pass')
                else:
                    result.update(status='completed', terminal=True, reply='round result: pass')
                terminal_events.append((node_id, purpose))
                event_log.append(('terminal', node_id, purpose))
            return {'job': {'job_id': job_id, 'status': result['status']}}
        raise AssertionError(f'unknown wait job: {job_id}')

    monkeypatch.setattr(loop_runner_module, 'loop_runner_once', fake_once)
    command = ParsedLoopRunnerCommand(
        project=None,
        auto=True,
        once=False,
        max_steps=12,
        poll_interval_s=0.0,
        json_output=True,
    )
    payload = loop_runner_auto(
        scheduler.context,
        command,
        services=SimpleNamespace(trace_target=fake_trace, sleep=lambda _seconds: None),
    )

    assert payload['final_action'] == 'none'
    assert harness.submissions[:3] == [
        ('node-001', 'worker'),
        ('node-002', 'worker'),
        ('node-001', 'reviewer'),
    ]
    assert terminal_events.index(('node-001', 'worker')) < terminal_events.index(
        ('node-002', 'worker')
    )
    assert event_log.index(('submitted', 'node-001', 'reviewer')) < event_log.index(
        ('terminal', 'node-002', 'worker')
    )
    assert harness.submissions.index(('node-001', 'reviewer')) < harness.submissions.index(
        ('node-002', 'reviewer')
    )
    assert scheduler.run_once()['controller_status'] == 'pass'


def test_auto_runner_stops_without_spin_when_scheduler_has_no_waitable_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / 'auto-no-wait'
    root.mkdir()
    context = SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='project-auto'))
    calls = 0

    def fake_once(_context, _command, _services):
        nonlocal calls
        calls += 1
        return {
            'loop_runner_status': 'pending',
            'action': 'multi_workgroup_execution_pending',
            'scheduler_action': 'topology_pending',
            'controller_status': 'topology_pending',
            'pending_job_ids': [],
        }

    monkeypatch.setattr(loop_runner_module, 'loop_runner_once', fake_once)
    command = ParsedLoopRunnerCommand(project=None, auto=True, once=False, max_steps=8, json_output=True)
    payload = loop_runner_auto(context, command, services=SimpleNamespace())

    assert calls == 1
    assert payload['final_action'] == 'multi_workgroup_execution_pending'
    assert payload['steps'][0]['scheduler_action'] == 'topology_pending'


def test_auto_runner_reports_blocked_when_terminal_wait_does_not_advance_signature(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / 'auto-no-progress'
    root.mkdir()
    context = SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='project-auto'))
    calls = 0
    traces = []

    def fake_once(_context, _command, _services):
        nonlocal calls
        calls += 1
        return {
            'loop_runner_status': 'pending',
            'action': 'multi_workgroup_execution_pending',
            'scheduler_action': 'provider_jobs_pending',
            'controller_status': 'executing',
            'pending_job_ids': ['job-stuck'],
            'submission_unknown': False,
        }

    def fake_trace(_context, command):
        traces.append(command.target)
        return {'job': {'job_id': command.target, 'status': 'completed'}}

    monkeypatch.setattr(loop_runner_module, 'loop_runner_once', fake_once)
    command = ParsedLoopRunnerCommand(
        project=None,
        auto=True,
        once=False,
        max_steps=8,
        poll_interval_s=0.0,
        json_output=True,
    )
    payload = loop_runner_auto(
        context,
        command,
        services=SimpleNamespace(trace_target=fake_trace, sleep=lambda _seconds: None),
    )

    assert calls == 2
    assert traces == ['job-stuck']
    assert payload['loop_runner_status'] == 'blocked'
    assert payload['action'] == 'auto_runner_scheduler_no_progress'
    assert payload['pending_job_ids'] == ['job-stuck']
    assert payload['next_activation'] == 'inspect_scheduler_job_authority_then_rerun'


def test_auto_runner_waits_for_delegated_chain_continuation_before_rerun(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / 'auto-delegated-chain'
    root.mkdir()
    context = SimpleNamespace(project=SimpleNamespace(project_root=root, project_id='project-auto'))
    calls = 0
    persisted_calls = 0

    def fake_once(_context, _command, _services):
        nonlocal calls
        calls += 1
        if calls == 1:
            return {
                'loop_runner_status': 'pending',
                'action': 'multi_workgroup_execution_pending',
                'scheduler_action': 'provider_jobs_pending',
                'controller_status': 'executing',
                'pending_job_ids': ['job-delegated'],
                'submission_unknown': False,
            }
        return {'loop_runner_status': 'idle', 'action': 'none'}

    def fake_trace(_context, command):
        return {
            'job': {
                'job_id': command.target,
                'status': 'completed',
                'terminal_decision': {
                    'reason': 'task_complete',
                    'delegated': True,
                    'chain_edge_id': 'cb-delegated',
                },
            }
        }

    def fake_persisted(_context, job_id):
        nonlocal persisted_calls
        persisted_calls += 1
        if persisted_calls < 3:
            return None
        return {'job_id': job_id, 'terminal': True, 'status': 'completed'}

    monkeypatch.setattr(loop_runner_module, 'loop_runner_once', fake_once)
    command = ParsedLoopRunnerCommand(
        project=None,
        auto=True,
        once=False,
        max_steps=8,
        poll_interval_s=0.0,
        json_output=True,
    )
    payload = loop_runner_auto(
        context,
        command,
        services=SimpleNamespace(
            trace_target=fake_trace,
            persisted_terminal_watch=fake_persisted,
            delegated_callback_pending=lambda _context, _job_id: persisted_calls < 3,
            sleep=lambda _seconds: None,
        ),
    )

    assert persisted_calls == 3
    assert calls == 2
    assert payload['action'] == 'auto_runner_finished'
    assert payload['final_action'] == 'none'


@pytest.mark.parametrize(
    ('release', 'observed_agent'),
    (
        (
            {
                'loop_topology_status': 'release_incomplete',
                'released_count': 2,
                'retained_count': 0,
                'release_incomplete_count': 1,
            },
            {'id': 'compact-node-001-worker', 'observed_state': 'present'},
        ),
        (
            {
                'loop_topology_status': 'release_incomplete',
                'released_count': 2,
                'retained_count': 0,
                'release_incomplete_count': 1,
            },
            {'id': 'compact-round-reviewer', 'observed_state': 'hidden'},
        ),
        (
            {'released_count': 3, 'retained_count': 0, 'release_incomplete_count': 0},
            None,
        ),
        (
            {
                'loop_topology_status': 'failed',
                'released_count': 0,
                'retained_count': 0,
                'release_incomplete_count': 0,
            },
            None,
        ),
    ),
)
def test_release_authority_residue_never_normalizes_to_pass_and_clean_retry_succeeds(
    tmp_path: Path,
    release: dict[str, object],
    observed_agent: dict[str, object] | None,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    harness.release = release
    harness.observed_agents = [observed_agent] if observed_agent else []

    blocked = scheduler.run_once()

    assert blocked['controller_status'] == 'release_blocked'
    assert blocked['cleanup']['readiness']['reason'] == 'topology_release_incomplete'
    assert 'result' not in blocked['cleanup']
    harness.release = {
        'loop_topology_status': 'released',
        'released_count': 1,
        'retained_count': 0,
        'release_incomplete_count': 0,
    }
    harness.observed_agents = []
    final = scheduler.run_once()
    assert final['controller_status'] == 'pass'
    assert ('cleanup', ()) in integration.calls


@pytest.mark.parametrize('evidence_shape', ('missing', 'corrupt'))
def test_missing_or_corrupt_raw_observed_release_evidence_blocks_cleanup(
    tmp_path: Path,
    evidence_shape: str,
) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    observed_path = scheduler.project_root / '.ccb' / 'runtime' / 'loops' / 'raw-observed.json'
    if evidence_shape == 'corrupt':
        observed_path.parent.mkdir(parents=True, exist_ok=True)
        observed_path.write_text('{not-json\n', encoding='utf-8')
    harness.include_release_observed = False
    harness.status_observed_path = observed_path

    blocked = scheduler.run_once()

    assert blocked['controller_status'] == 'release_blocked'
    expected_reason = (
        'raw_observed_path_missing' if evidence_shape == 'missing' else 'raw_observed_corrupt'
    )
    assert blocked['topology']['observed_evidence']['reason'] == expected_reason
    assert 'result' not in blocked['cleanup']
    assert not any(call[0] == 'cleanup' for call in integration.calls if isinstance(call, tuple))
    harness.include_release_observed = True
    final = scheduler.run_once()
    assert final['controller_status'] == 'pass'


def test_compact_status_observed_path_loads_valid_raw_release_authority(tmp_path: Path) -> None:
    scheduler, harness, integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    observed_path = scheduler.project_root / '.ccb' / 'runtime' / 'loops' / 'raw-observed.json'
    observed_path.parent.mkdir(parents=True, exist_ok=True)
    observed_path.write_text(
        json.dumps({'agents': [], 'retained_count': 0, 'release_incomplete_count': 0}),
        encoding='utf-8',
    )
    harness.include_release_observed = False
    harness.status_observed_path = observed_path

    final = scheduler.run_once()

    assert final['controller_status'] == 'pass'
    assert final['topology']['observed_evidence'] == {
        'source': 'observed_path',
        'reason': None,
        'path': str(observed_path),
    }
    assert ('cleanup', ()) in integration.calls


@pytest.mark.parametrize('count', (1, 2, 3, 4))
def test_transition_events_are_unique_authoritative_and_replay_idempotent(
    tmp_path: Path,
    count: int,
) -> None:
    scheduler, _harness, _integration = _scheduler(tmp_path, count)
    scheduler.run_once()
    first = [json.loads(line) for line in scheduler.events_path.read_text(encoding='utf-8').splitlines()]
    transitions = [event for event in first if event['kind'] == 'node_transition']

    assert len({event['event_id'] for event in first}) == len(first)
    assert len({event['evidence_digest'] for event in first}) == len(first)
    assert len(transitions) == count
    assert {(event['previous'], event['current']) for event in transitions} == {
        ('created', 'worker_pending')
    }
    assert all(isinstance(event['state_revision'], int) for event in first)
    scheduler.run_once()
    replay = [json.loads(line) for line in scheduler.events_path.read_text(encoding='utf-8').splitlines()]
    assert [event for event in replay if event['kind'] == 'node_transition'] == transitions


@pytest.mark.parametrize('maximum', (0, 1, 2))
def test_rework_policy_honors_exact_frozen_maximum(tmp_path: Path, maximum: int) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1, max_rework=maximum)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    result = scheduler.run_once()

    if maximum == 0:
        assert result['round_result'] == 'blocked'
        assert result['nodes']['node-001']['failure']['source'] == 'worker_owned_review_chain_invalid'
        assert 'review_chain_final_rework_required' in result['nodes']['node-001']['failure']['reasons']
    else:
        assert result['nodes']['node-001']['status'] == 'worker_pending'
        assert harness.submission_attempts[-1] == ('node-001', 'worker_rework', 1)


def test_two_rework_cycles_use_distinct_intents_same_binding_and_then_pass(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1, max_rework=2)
    scheduler.run_once()
    binding = scheduler.run_once()['nodes']['node-001']['workspace_group']
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework', attempt=1)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=1, reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework', attempt=2)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=2, reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    final = scheduler.run_once()

    assert final['controller_status'] == 'pass'
    assert final['nodes']['node-001']['rework_count'] == 2
    assert final['nodes']['node-001']['workspace_group'] == binding
    rework_attempts = [
        item
        for item in harness.submission_attempts
        if item[1] in {'worker_rework', 'reviewer_recheck'}
    ]
    assert rework_attempts == [
        ('node-001', 'worker_rework', 1),
        ('node-001', 'reviewer_recheck', 1),
        ('node-001', 'worker_rework', 2),
        ('node-001', 'reviewer_recheck', 2),
    ]
    assert len(final['nodes']['node-001']['rework_history']) == 3
    assert harness.controller_submissions == [
        ('node-001', 'worker'),
        ('round', 'ccb_round_reviewer'),
    ]


def test_second_rework_stays_inside_chain_without_controller_intent(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1, max_rework=2)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework', attempt=1)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=1, reply='status: rework_required')
    result = scheduler.run_once()

    assert result['nodes']['node-001']['status'] == 'worker_pending'
    assert harness.submission_attempts.count(('node-001', 'worker_rework', 2)) == 1
    assert not any(
        item[1] in {'worker_rework', 'reviewer', 'reviewer_recheck'}
        for item in harness.submission_attempts
        if item not in {
            ('node-001', 'reviewer', 1),
            ('node-001', 'worker_rework', 1),
            ('node-001', 'reviewer_recheck', 1),
            ('node-001', 'worker_rework', 2),
        }
    )


def test_second_rework_non_convergence_exhausts_without_third_submission(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1, max_rework=2)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework', attempt=1)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=1, reply='status: rework_required')
    scheduler.run_once()
    harness.complete('node-001', 'worker_rework', attempt=2)
    scheduler.run_once()
    harness.complete('node-001', 'reviewer_recheck', attempt=2, reply='status: rework_required')

    final = scheduler.run_once()

    assert final['round_result'] == 'blocked'
    assert final['nodes']['node-001']['failure']['source'] == 'worker_owned_review_chain_invalid'
    assert 'review_chain_final_rework_required' in final['nodes']['node-001']['failure']['reasons']
    assert not any(attempt == 3 for _node_id, _purpose, attempt in harness.submission_attempts)


def test_final_round_json_uses_public_workgroup_round_schema(tmp_path: Path) -> None:
    scheduler, harness, _integration = _scheduler(tmp_path, 1)
    scheduler.run_once()
    harness.complete('node-001', 'worker')
    scheduler.run_once()
    harness.complete('node-001', 'reviewer', reply='status: pass')
    scheduler.run_once()
    harness.complete('round', 'ccb_round_reviewer', reply='round result: pass')
    scheduler.run_once()

    raw = json.loads((scheduler.loop_dir / 'round.json').read_text(encoding='utf-8'))
    private = json.loads(scheduler.state_path.read_text(encoding='utf-8'))
    assert raw['schema'] == 'ccb.loop.workgroup_round_state.v1'
    assert raw['record_type'] == 'ccb_loop_workgroup_round'
    assert raw['workgroup_state_schema'] == raw['schema']
    assert raw['project_root'] == str(scheduler.project_root)
    assert raw['project_id'] == 'project-g3'
    assert raw['workgroups']['node-001']['node_id'] == 'node-001'
    assert raw['paths']['scheduler_state'] == str(scheduler.state_path)
    assert raw['release']['loop_topology_status'] == 'released'
    assert raw['cleanup']['result']['status'] == 'complete'
    assert private['schema'] == 'ccb.loop.multi_workgroup_scheduler.v1'


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ['git', '-C', str(cwd), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()
