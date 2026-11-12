from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_REQUEST = (
    PROJECT_ROOT
    / 'docs'
    / 'plantree'
    / 'plans'
    / 'agentic-loop-workflow'
    / 'topics'
    / 'phase6b-l5-partial-launch-request-20260704.md'
)
EXPECTED_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat4-20260704'
CONSUMED_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704'
CONSUMED_REPEAT2_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704'
CONSUMED_REPEAT3_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704'
TASK_ID = 'phase6b-l5-partial-budget-source-gap'


def _text() -> str:
    return LAUNCH_REQUEST.read_text(encoding='utf-8')


def _frozen_command_block() -> str:
    match = re.search(
        r'## Frozen L5 Command Shape.*?```bash\n(.*?)\n```',
        _text(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _embedded_phase_driver() -> str:
    match = re.search(
        r"cat > \"\$PHASE6B_L5_SCRIPT\" <<'RUN_L5_SH'\n(.*?)\nRUN_L5_SH",
        _frozen_command_block(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _embedded_b7_normalizer() -> str:
    match = re.search(
        r'Exact B7 normalization command shape for reviewer approval:.*?```bash\n(.*?)\n```',
        _text(),
        flags=re.S,
    )
    assert match is not None
    py_match = re.search(r"<<'PY'\n(.*?)\nPY", match.group(1), flags=re.S)
    assert py_match is not None
    code = py_match.group(1)
    compile(code, '<phase6b-l5-partial-b7-normalizer>', 'exec')
    return code


def _b7_command_block() -> str:
    match = re.search(
        r'Exact B7 normalization command shape for reviewer approval:.*?```bash\n(.*?)\n```',
        _text(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _shared_environment_block() -> str:
    match = re.search(
        r'Shared environment:\n\n```bash\n(.*?)\n```',
        _text(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _schema_fields(section_intro: str) -> set[str]:
    match = re.search(
        rf'{re.escape(section_intro)}\n\n```text\n(.*?)\n```',
        _text(),
        flags=re.S,
    )
    assert match is not None
    return {line.strip() for line in match.group(1).splitlines() if line.strip()}


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in records),
        encoding='utf-8',
    )


def test_phase6b_l5_launch_request_is_partial_only_and_not_runtime() -> None:
    text = _text()
    command_block = _frozen_command_block()
    shared_environment = _shared_environment_block()
    b7_command_block = _b7_command_block()
    normalizer = _embedded_b7_normalizer()

    assert 'RUN CONSUMED / B7 VALID_NON_SUCCESS / PHASE 6B UNCLAIMED' in text
    assert 'Reviewer2 granted launch-specific approval-to-run in `job_5dd131a6ea7e`' in text
    assert 'Talk2 consumed that approval once.' in text
    assert 'phase6b-real-provider-l5-partial-repeat4-b7-20260704.md' in text
    assert '`reviewer_rework_or_partial_observed=true`' in text
    assert 'Worker3 did not execute' in text
    assert 'This approval was consumed by one talk2-supervised run.' in text
    assert EXPECTED_ROOT in text
    assert EXPECTED_ROOT in command_block
    assert EXPECTED_ROOT in shared_environment
    assert CONSUMED_ROOT in text
    assert CONSUMED_ROOT not in command_block
    assert CONSUMED_REPEAT2_ROOT in text
    assert CONSUMED_REPEAT2_ROOT not in command_block
    assert CONSUMED_REPEAT3_ROOT in text
    assert CONSUMED_REPEAT3_ROOT not in command_block
    assert CONSUMED_REPEAT3_ROOT not in shared_environment
    assert CONSUMED_REPEAT3_ROOT not in b7_command_block
    assert 'job_4e3c051ef168' in text
    assert 'job_af5f6fb64a7d' in text
    assert 'job_663bad41c855' in text
    assert 'job_de6263827473' in text
    assert 'job_766050825b27' in text
    assert 'job_5dd131a6ea7e' in text
    assert 'job_56466011201a' in text
    assert 'historical, not runnable' in text
    assert 'not_claimable' in text
    assert 'ask --chain requires an active parent job for the' in text
    assert 'sender' in text
    assert '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704' not in command_block
    assert '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704' not in command_block
    assert TASK_ID in command_block
    assert TASK_ID in normalizer
    assert 'phase6b-l5-reviewer-bounded-rework-contract' not in command_block
    assert 'phase6b-l5-reviewer-bounded-rework-contract' not in normalizer
    assert 'approved_inherited_current_real_provider_home' in command_block
    assert '"ccb_round_reviewer":"claude"' in command_block
    assert '"code_reviewer":"codex"' in command_block
    assert 'phase6b_l5_partial_only_repeat4_command_log.jsonl' in command_block
    assert 'phase6b_l5_partial_only_repeat4_evidence_rows.jsonl' in text
    assert 'phase6b-real-provider-l5-partial-repeat4-b7-20260704.md' in text
    assert 'phase6b-real-provider-l5-partial-repeat4-b7-20260704.md' in b7_command_block
    assert 'phase6b-real-provider-l5-partial-repeat3-b7-20260704.md' in text
    assert 'phase6b-real-provider-l5-partial-repeat3-b7-20260704.md' not in command_block
    assert 'phase6b-real-provider-l5-partial-repeat3-b7-20260704.md' not in b7_command_block
    assert 'post_b7_cleanup.json' in text
    assert '$PHASE6B_L5_PROJECT/supervisor_imports/phase6b-l5-partial-budget-source-gap/route.txt' in text
    assert 'HOME=inherited from current system provider environment; do not export lab-local HOME' in text
    assert (
        'CCB_SOURCE_HOME=inherited from current system provider environment; do not export lab-local CCB_SOURCE_HOME'
        in text
    )


def test_phase6b_l5_command_shape_is_external_root_and_stdin_safe() -> None:
    text = _text()
    command_block = _frozen_command_block()
    phase_driver = _embedded_phase_driver()

    shell_parse = subprocess.run(
        ['bash', '-n'],
        input=phase_driver,
        text=True,
        capture_output=True,
        check=False,
    )
    assert shell_parse.returncode == 0, shell_parse.stderr
    for embedded_python in re.findall(r"<<'PY'\n(.*?)\nPY", phase_driver, flags=re.S):
        compile(embedded_python, '<phase6b-l5-driver-python>', 'exec')

    assert 'cd /home/bfly/yunwei/test_ccb2' in command_block
    assert '/home/bfly/yunwei/ccb_source/ccb_test' in command_block
    assert 'run_l5.sh' in command_block
    assert 'PHASE6B_L5_SUPERVISION_DIR="$PHASE6B_L5_PROJECT/supervisor_imports"' in command_block
    assert 'PHASE6B_L5_SUPERVISION_DIR="$PHASE6B_L5_ROOT/supervisor_imports"' not in command_block
    assert 'export HOME=' not in command_block
    assert 'export HOME=' not in _shared_environment_block()
    assert 'export CCB_SOURCE_HOME=' not in command_block
    assert 'export CCB_SOURCE_HOME=' not in _shared_environment_block()
    assert '$PHASE6B_L5_ROOT/source_home' not in command_block
    assert '"$HOME"' not in command_block
    assert '"$CCB_SOURCE_HOME"' not in command_block
    assert '</dev/null >"$stdout_path" 2>"$stderr_path"' in command_block
    assert 'timeout --preserve-status "${PHASE6B_L5_TIMEOUT_SECONDS}s" "$@"' in command_block
    assert 'bash "$PHASE6B_L5_SCRIPT" init' in text
    assert 'bash "$PHASE6B_L5_SCRIPT" start-partial' in text
    assert 'bash "$PHASE6B_L5_SCRIPT" continue-partial-route' in text
    assert 'bash "$PHASE6B_L5_SCRIPT" finalize-partial' in text
    assert 'Run the B7 normalization command before any external cleanup' in text
    assert 'topology_dispatch.json' in text
    assert 'provider-reply authority parsing' in text
    assert 'loop run-once' not in command_block
    assert 'topology dispatch' not in command_block.lower()
    assert 'verify_ask_first_system_sender_repair()' in phase_driver
    assert "RUNNER_ASK_SENDER = 'system'" in phase_driver
    assert 'sender=RUNNER_ASK_SENDER' in phase_driver
    assert 'watch_ask_job' in phase_driver
    assert 'callback=True" in body or "silence=True" in body' in phase_driver
    assert 'refuse: accepted ask-first system-sender repair is absent' in phase_driver


def test_phase6b_l5_driver_materializes_plan_root_before_task_create() -> None:
    phase_driver = _embedded_phase_driver()
    init_body = re.search(r'init_lab\(\) \{\n(.*?)\n\}', phase_driver, flags=re.S)
    create_body = re.search(r'create_task_record\(\) \{\n(.*?)\n\}', phase_driver, flags=re.S)
    assert init_body is not None
    assert create_body is not None

    assert 'PHASE6B_L5_PLAN_SLUG=phase6b-real-provider-l5' in phase_driver
    assert 'PHASE6B_L5_PLAN_ROOT="$PHASE6B_L5_PROJECT/docs/plantree/plans/$PHASE6B_L5_PLAN_SLUG"' in phase_driver
    assert 'materialize_plan_root()' in phase_driver
    assert 'validate_plan_root()' in phase_driver
    assert 'mkdir -p "$PHASE6B_L5_PLAN_ROOT" "$PHASE6B_L5_PLAN_ROOT/tasks"' in phase_driver
    assert '$PHASE6B_L5_PROJECT/docs/plantree/README.md' in phase_driver
    assert '$PHASE6B_L5_PLAN_ROOT/README.md' in phase_driver

    init = init_body.group(1)
    assert (
        init.index('verify_ask_first_system_sender_repair')
        < init.index('write_config')
        < init.index('materialize_plan_root')
        < init.index('seed_rolepacks')
    )
    create = create_body.group(1)
    assert create.index('validate_plan_root') < create.index('__task_create')
    assert 'plan task-create --plan "$PHASE6B_L5_PLAN_SLUG"' in create


def test_phase6b_l5_b7_normalizer_emits_declared_schema_for_partial(tmp_path: Path) -> None:
    code = _embedded_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l5-partial-only-repeat4-20260704'
    task_dir = root / 'l5-partial-real-provider-lab' / 'supervisor_imports' / TASK_ID
    b7_path = tmp_path / 'phase6b-real-provider-l5-partial-repeat4-b7-20260704.md'
    task_dir.mkdir(parents=True)

    for artifact in (
        'task_packet.md',
        'execution_contract.md',
        'orchestration_notes.md',
        'worker_reply.md',
    ):
        (task_dir / artifact).write_text(f'{artifact}\ntask_packet\nexecution_contract\n', encoding='utf-8')
    (task_dir / 'reviewer_verdict.md').write_text(
        'Reviewer cites task_packet and execution_contract; partial is not done.\n',
        encoding='utf-8',
    )
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text(
        'round_result: partial\nfinal_status: partial\ncleanup_result: released\n',
        encoding='utf-8',
    )
    (task_dir / 'partial_evidence.md').write_text('required source file is absent\n', encoding='utf-8')
    (task_dir / 'completed_steps.md').write_text('inspected existing summary\n', encoding='utf-8')
    (task_dir / 'unfinished_steps.md').write_text('missing source synchronization\n', encoding='utf-8')
    _write_json(
        task_dir / 'runtime_residue.json',
        {
            'config_dynamic_agents_absent': True,
            'dynamic_agents_absent': True,
            'observed_topology_residue_absent': True,
        },
    )
    _write_json(task_dir / 'release.json', {'release_blockers': {}, 'release_incomplete_agents': []})
    _write_json(task_dir / 'role_boundary_violations.json', [])
    _write_json(task_dir / 'authority_write_violations.json', [])
    _write_json(
        root / 'runtime' / 'loops' / 'l5-partial' / 'agent_mount_topology.desired.json',
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
    )
    _write_jsonl(
        root / 'phase6b_l5_partial_only_repeat4_command_log.jsonl',
        [
            {'label': f'{TASK_ID}__run_direct_execution_round', 'returncode': 0},
            {'label': 'config_validate_after_l5', 'returncode': 0},
        ],
    )

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(b7_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    row_path = root / 'rows' / 'phase6b_l5_partial_only_repeat4_evidence_rows.jsonl'
    row = json.loads(row_path.read_text(encoding='utf-8'))
    declared_fields = _schema_fields('Every row must include at least:') | _schema_fields('Additional required L5 fields:')
    assert declared_fields <= set(row)
    assert row['task_id'] == TASK_ID
    assert row['observation_type'] == 'partial_completion'
    assert row['expected_route'] == 'direct_execution'
    assert row['observed_route'] == 'direct_execution'
    assert row['round_result'] == 'partial'
    assert row['final_status'] == 'partial'
    assert row['classification'] == 'valid_non_success'
    assert row['partial_observed'] is True
    assert row['partial_completed_steps'] == ['inspected existing summary']
    assert row['partial_unfinished_steps'] == ['missing source synchronization']
    assert row['reviewer_rework_observed'] is False
    assert row['rework_attempt_count'] == 0
    assert row['topology_dispatch_absent'] is True
    assert row['topology_communication_dsl_absent'] is True
    assert row['provider_reply_authority_parsing_absent'] is True
    assert row['release_blockers'] == {}
    assert row['release_incomplete_agents'] == []
    assert 'reviewer_rework_or_partial_observed=true' in b7_path.read_text(encoding='utf-8')


def test_phase6b_l5_b7_normalizer_rejects_vague_partial(tmp_path: Path) -> None:
    code = _embedded_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l5-partial-only-repeat4-20260704'
    task_dir = root / 'l5-partial-real-provider-lab' / 'supervisor_imports' / TASK_ID
    b7_path = tmp_path / 'phase6b-real-provider-l5-partial-repeat4-b7-20260704.md'
    task_dir.mkdir(parents=True)

    for artifact in (
        'task_packet.md',
        'execution_contract.md',
        'orchestration_notes.md',
        'worker_reply.md',
        'reviewer_verdict.md',
        'round_summary.md',
        'partial_evidence.md',
        'runtime_residue.json',
        'release.json',
    ):
        (task_dir / artifact).write_text('task_packet execution_contract\n', encoding='utf-8')
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text(
        'round_result: partial\nfinal_status: partial\ncleanup_result: released\n',
        encoding='utf-8',
    )
    _write_json(
        root / 'runtime' / 'loops' / 'l5-partial' / 'agent_mount_topology.desired.json',
        {'schema': 'ccb.loop.agent_mount_topology.v1', 'nodes': []},
    )
    _write_jsonl(root / 'phase6b_l5_partial_only_repeat4_command_log.jsonl', [{'label': f'{TASK_ID}__run_direct_execution_round'}])

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(b7_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    row = json.loads((root / 'rows' / 'phase6b_l5_partial_only_repeat4_evidence_rows.jsonl').read_text(encoding='utf-8'))
    assert row['classification'] == 'test_design_failure'
    assert row['partial_completed_steps'] == []
    assert row['partial_unfinished_steps'] == []
    assert 'reviewer_rework_or_partial_observed=false' in b7_path.read_text(encoding='utf-8')
