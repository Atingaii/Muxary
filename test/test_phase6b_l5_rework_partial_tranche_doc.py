from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TRANCHE_DOC = (
    PROJECT_ROOT
    / 'docs'
    / 'plantree'
    / 'plans'
    / 'agentic-loop-workflow'
    / 'topics'
    / 'phase6b-reviewer-rework-partial-observation-tranche.md'
)


def _text() -> str:
    return TRANCHE_DOC.read_text(encoding='utf-8')


def _embedded_l5_normalizer() -> str:
    match = re.search(
        r'Exact normalization command shape for future reviewer approval:.*?```bash\n(.*?)\n```',
        _text(),
        flags=re.S,
    )
    assert match is not None
    py_match = re.search(r"<<'PY'\n(.*?)\nPY", match.group(1), flags=re.S)
    assert py_match is not None
    code = py_match.group(1)
    compile(code, '<phase6b-l5-reviewer-rework-partial-normalizer>', 'exec')
    return code


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in records),
        encoding='utf-8',
    )


def test_phase6b_l5_tranche_declares_plan_only_normalizer_shape() -> None:
    text = _text()
    normalizer = _embedded_l5_normalizer()

    assert 'Status: PLAN-ONLY NORMALIZER SKETCH / DO NOT RUN' in text
    assert '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-reviewer-rework-partial-20260704' in text
    assert 'phase6b-real-provider-l5-reviewer-rework-partial-b7-20260704.md' in text
    assert 'inherited current system provider environment' in text
    assert re.search(r'lab-local\s+`AGENT_ROLES_STORE`', text)
    assert 'isolated source wrapper environment' not in text
    assert 'phase6b-l5-partial-budget-source-gap' in normalizer
    assert 'phase6b-l5-reviewer-bounded-rework-contract' in normalizer
    assert 'reviewer_rework_or_partial_observed' in normalizer
    assert 'topology_dispatch_absent' in normalizer
    assert 'topology_communication_dsl_absent' in normalizer
    assert 'provider_reply_authority_parsing_absent' in normalizer


def test_phase6b_l5_normalizer_classifies_bounded_partial(tmp_path: Path) -> None:
    code = _embedded_l5_normalizer()
    root = tmp_path / 'phase6-real-lab-l5-reviewer-rework-partial-20260704'
    task_id = 'phase6b-l5-partial-budget-source-gap'
    task_dir = root / 'supervisor_imports' / task_id
    task_dir.mkdir(parents=True)
    b7_path = tmp_path / 'phase6b-real-provider-l5-reviewer-rework-partial-b7-20260704.md'

    for artifact in (
        'task_packet.md',
        'execution_contract.md',
        'orchestration_notes.md',
        'worker_reply.md',
        'reviewer_verdict.md',
    ):
        (task_dir / artifact).write_text(f'{artifact}\nexecution_contract\n', encoding='utf-8')
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text(
        'round_result: partial\nfinal_status: partial\ncleanup_result: released\n',
        encoding='utf-8',
    )
    (task_dir / 'partial_evidence.md').write_text('required source file is absent\n', encoding='utf-8')
    (task_dir / 'completed_steps.md').write_text('inspected existing summary\n', encoding='utf-8')
    (task_dir / 'unfinished_steps.md').write_text('missing source synchronization\n', encoding='utf-8')
    (task_dir / 'runtime_residue.json').write_text(
        json.dumps(
            {
                'dynamic_agents_absent': True,
                'config_dynamic_agents_absent': True,
                'observed_topology_residue_absent': True,
            },
            sort_keys=True,
        )
        + '\n',
        encoding='utf-8',
    )
    (task_dir / 'release.json').write_text(
        json.dumps({'release_blockers': {}, 'release_incomplete_agents': []}, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    topology_dir = root / 'runtime' / 'loops' / 'l5-partial'
    topology_dir.mkdir(parents=True)
    (topology_dir / 'agent_mount_topology.desired.json').write_text(
        json.dumps(
            {
                'schema': 'ccb.loop.agent_mount_topology.v1',
                'nodes': [
                    {
                        'id': 'execution',
                        'agents': [
                            {'id': 'loop-l5-coder-1', 'profile': 'coder', 'desired_state': 'present'},
                            {'id': 'loop-l5-code_reviewer-1', 'profile': 'code_reviewer', 'desired_state': 'present'},
                        ],
                    }
                ],
            },
            sort_keys=True,
        )
        + '\n',
        encoding='utf-8',
    )
    _write_jsonl(
        root / 'command_log.jsonl',
        [
            {
                'label': f'{task_id}__run_direct_execution_round',
                'returncode': 0,
                'stdout_path': str(root / 'logs' / 'round.stdout'),
            }
        ],
    )

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(b7_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    row_path = root / 'rows' / 'phase6b_l5_reviewer_rework_partial_evidence_rows.jsonl'
    rows = [json.loads(line) for line in row_path.read_text(encoding='utf-8').splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row['task_id'] == task_id
    assert row['classification'] == 'valid_non_success'
    assert row['partial_observed'] is True
    assert row['partial_completed_steps'] == ['inspected existing summary']
    assert row['partial_unfinished_steps'] == ['missing source synchronization']
    assert row['topology_dispatch_absent'] is True
    assert row['topology_communication_dsl_absent'] is True
    assert row['provider_reply_authority_parsing_absent'] is True
    assert 'reviewer_rework_or_partial_observed=true' in b7_path.read_text(encoding='utf-8')
