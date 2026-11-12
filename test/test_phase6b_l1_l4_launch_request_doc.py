from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLAN_ROOT = PROJECT_ROOT / 'docs' / 'plantree' / 'plans' / 'agentic-loop-workflow'
HISTORICAL_REQUEST = PLAN_ROOT / 'topics' / 'phase6b-l1-l4-launch-request-20260704.md'
SEQUENCE9_REQUEST = PLAN_ROOT / 'topics' / 'phase6b-l1-l4-launch-request-sequence9-20260704.md'
SEQUENCE10_REQUEST = PLAN_ROOT / 'topics' / 'phase6b-l1-l4-launch-request-sequence10-20260704.md'
SEQUENCE11_REQUEST = PLAN_ROOT / 'topics' / 'phase6b-l1-l4-launch-request-sequence11-20260704.md'
SEQUENCE12_REQUEST = PLAN_ROOT / 'topics' / 'phase6b-l1-l4-launch-request-sequence12-20260705.md'
IMPLEMENTATION_STATUS = PLAN_ROOT / 'implementation-status.md'
CLAIM_COVERAGE_MATRIX = PLAN_ROOT / 'topics' / 'phase6b-real-provider-claim-coverage-matrix.md'
ACTIVE_SUPERVISION_BOARD = PLAN_ROOT / 'topics' / 'phase1-6-active-supervision-board-20260704.md'
EVIDENCE_INDEX = PLAN_ROOT / 'history' / 'phase1-6-evidence-index.md'
FINAL_ACCEPTANCE_REPORT = PLAN_ROOT / 'history' / 'phase1-6-acceptance-report-20260705.md'

CONSUMED_REPEAT8_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence8-20260704'
SEQUENCE9_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence9-20260704'
SEQUENCE10_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence10-20260704'
SEQUENCE11_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence11-20260704'
SEQUENCE12_ROOT = '/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705'
CONSUMED_REPEAT8_B7 = (
    'docs/plantree/plans/agentic-loop-workflow/history/'
    'phase6b-real-provider-l1-l4-repeat8-b7-20260704.md'
)
SEQUENCE9_B7 = (
    'docs/plantree/plans/agentic-loop-workflow/history/'
    'phase6b-real-provider-l1-l4-repeat9-b7-20260704.md'
)
SEQUENCE10_B7 = (
    'docs/plantree/plans/agentic-loop-workflow/history/'
    'phase6b-real-provider-l1-l4-repeat10-b7-20260704.md'
)
SEQUENCE11_B7 = (
    'docs/plantree/plans/agentic-loop-workflow/history/'
    'phase6b-real-provider-l1-l4-repeat11-b7-20260704.md'
)
SEQUENCE12_B7 = (
    'docs/plantree/plans/agentic-loop-workflow/history/'
    'phase6b-real-provider-l1-l4-repeat12-b7-20260705.md'
)
L0_REPEAT6_B7 = 'phase6b-real-provider-l0-b-only-repeat6-b7-20260704.md'
L5_PARTIAL_REPEAT4_B7 = 'phase6b-real-provider-l5-partial-repeat4-b7-20260704.md'
SOURCE_REAUDIT_ACCEPTANCE_JOB = 'job_b4184497742b'
SOURCE_REPAIR_JOB = 'job_e2ff663087be'
SOURCE_REPAIR_REVIEW_JOB = 'job_a7e62fee5496'
SOURCE_REPAIR_REVIEW_ARTIFACT = (
    '/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/'
    'job_a7e62fee5496-art_d74161f1a0dd4d52.txt'
)
STALE_SOURCE_HOLD_PHRASES = (
    'APPROVAL BLOCKED BY ' + 'SOURCE REPAIR',
    'not currently approval-' + 'eligible',
)
STALE_SEQUENCE10_ACTIVE_PHRASES = (
    'Phase 6B L1-L4 sequence10 repair packet',
    'reviewer2 returns a launch-specific verdict for the sequence10 repair packet',
    'Pending reviewer-gated fresh L1-L4 sequence10 evidence',
)


def _text(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _flat(text: str) -> str:
    return ' '.join(text.split())


def _sequence10_text() -> str:
    return _text(SEQUENCE10_REQUEST)


def _sequence10_driver() -> str:
    match = re.search(
        r"cat > \"\$PHASE6B_L1L4_SCRIPT\" <<'RUN_L1_L4_SEQUENCE10_SH'\n(.*?)\nRUN_L1_L4_SEQUENCE10_SH",
        _sequence10_text(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _sequence10_b7_normalizer() -> str:
    match = re.search(
        r"write_b7_report\(\) \{\n\s+python .*? <<'PY'\n(.*?)\nPY\n\}",
        _sequence10_driver(),
        flags=re.S,
    )
    assert match is not None
    code = match.group(1)
    compile(code, '<phase6b-l1-l4-sequence10-b7-normalizer>', 'exec')
    return code


def _sequence11_text() -> str:
    return _text(SEQUENCE11_REQUEST)


def _sequence11_driver() -> str:
    match = re.search(
        r"cat > \"\$PHASE6B_L1L4_SCRIPT\" <<'RUN_L1_L4_SEQUENCE11_SH'\n(.*?)\nRUN_L1_L4_SEQUENCE11_SH",
        _sequence11_text(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _sequence11_b7_normalizer() -> str:
    match = re.search(
        r"write_b7_report\(\) \{\n\s+python .*? <<'PY'\n(.*?)\nPY\n\}",
        _sequence11_driver(),
        flags=re.S,
    )
    assert match is not None
    code = match.group(1)
    compile(code, '<phase6b-l1-l4-sequence11-b7-normalizer>', 'exec')
    return code


def _sequence11_run_required_function() -> str:
    driver = _sequence11_driver()
    start = driver.index('run_required() {')
    end = driver.index('\n}\n\nrequire_initialized()', start) + len('\n}')
    return driver[start:end]


def _sequence12_text() -> str:
    return _text(SEQUENCE12_REQUEST)


def _sequence12_driver() -> str:
    match = re.search(
        r"cat > \"\$PHASE6B_L1L4_SCRIPT\" <<'RUN_L1_L4_SEQUENCE12_SH'\n(.*?)\nRUN_L1_L4_SEQUENCE12_SH",
        _sequence12_text(),
        flags=re.S,
    )
    assert match is not None
    return match.group(1)


def _sequence12_b7_normalizer() -> str:
    match = re.search(
        r"write_b7_report\(\) \{\n\s+python .*? <<'PY'\n(.*?)\nPY\n\}",
        _sequence12_driver(),
        flags=re.S,
    )
    assert match is not None
    code = match.group(1)
    compile(code, '<phase6b-l1-l4-sequence12-b7-normalizer>', 'exec')
    return code


def _sequence12_run_required_function() -> str:
    driver = _sequence12_driver()
    start = driver.index('run_required() {')
    end = driver.index('\n}\n\nrequire_initialized()', start) + len('\n}')
    return driver[start:end]


def _run_sequence12_driver_fragment(tmp_path: Path, command: str) -> subprocess.CompletedProcess[str]:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    env = {
        **os.environ,
        'PHASE6B_L1L4_ROOT': str(root),
        'PHASE6B_L1L4_PROJECT': str(project),
        'PHASE6B_L1L4_COMMAND_LOG': str(root / 'phase6b_l1_l4_sequence12_command_log.jsonl'),
        'PHASE6B_L1L4_ROWS': str(root / 'rows' / 'phase6b_l1_l4_sequence12_evidence_rows.jsonl'),
        'PHASE6B_L1L4_B7': str(root / 'phase6b-real-provider-l1-l4-repeat12-b7-20260705.md'),
        'AGENT_ROLES_STORE': str(root / 'roles'),
    }
    script = _sequence12_driver().replace('main "$@"', command)
    return subprocess.run(
        ['bash'],
        input=script,
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n' for record in records),
        encoding='utf-8',
    )


def _task_dir(project: Path, task_id: str) -> Path:
    path = project / 'supervisor_imports' / task_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_task_show(root: Path, task_id: str, payload: dict[str, object]) -> None:
    _write_json(root / 'logs' / f'{task_id}__task_show_after_round.stdout', payload)


def _write_released_observed_topology(project: Path, loop_id: str) -> None:
    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / loop_id / 'agent_mount_topology.observed.json',
        {
            'schema': 'ccb.loop.agent_mount_topology.observed.v1',
            'record_type': 'ccb_loop_agent_mount_topology_observed',
            'loop_id': loop_id,
            'agents': [],
            'retained': [],
            'retained_agents': [],
            'retained_count': 0,
            'released_agents': [
                f'loop-{loop_id}-code_reviewer-1',
                f'loop-{loop_id}-coder-1',
            ],
            'released_count': 2,
        },
    )


def _run_sequence10_normalizer(tmp_path: Path) -> tuple[Path, list[dict[str, object]], str]:
    code = _sequence10_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence10-20260704'
    project = root / 'l1-l4-real-provider-lab'
    b7_path = tmp_path / 'phase6b-real-provider-l1-l4-repeat10-b7-20260704.md'
    rows_path = root / 'rows' / 'phase6b_l1_l4_sequence10_evidence_rows.jsonl'

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(project), str(b7_path), str(rows_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines()]
    return b7_path, rows, b7_path.read_text(encoding='utf-8')


def _run_sequence11_normalizer(tmp_path: Path) -> tuple[Path, list[dict[str, object]], str]:
    code = _sequence11_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence11-20260704'
    project = root / 'l1-l4-real-provider-lab'
    b7_path = tmp_path / 'phase6b-real-provider-l1-l4-repeat11-b7-20260704.md'
    rows_path = root / 'rows' / 'phase6b_l1_l4_sequence11_evidence_rows.jsonl'

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(project), str(b7_path), str(rows_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines()]
    return b7_path, rows, b7_path.read_text(encoding='utf-8')


def _run_sequence12_normalizer(tmp_path: Path) -> tuple[Path, list[dict[str, object]], str]:
    code = _sequence12_b7_normalizer()
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    b7_path = tmp_path / 'phase6b-real-provider-l1-l4-repeat12-b7-20260705.md'
    rows_path = root / 'rows' / 'phase6b_l1_l4_sequence12_evidence_rows.jsonl'

    result = subprocess.run(
        [sys.executable, '-c', code, str(root), str(project), str(b7_path), str(rows_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines()]
    return b7_path, rows, b7_path.read_text(encoding='utf-8')


def test_l1_l4_request_is_repeat8_historical_non_runnable() -> None:
    text = _text(HISTORICAL_REQUEST)

    assert text.startswith('# Phase 6B L1-L4 Launch Request Historical Record')
    assert (
        'Status: REPEAT8 CONSUMED HISTORICAL RECORD / DO NOT RUN / '
        'NO ACTIVE L1-L4 LAUNCH REQUEST / PHASE 6B UNCLAIMED'
    ) in text
    assert 'non-runnable historical record for the consumed Phase 6B' in text
    assert 'This file is not an approval-to-run request' in text
    assert 'no executable command block, no B7 normalizer command' in _flat(text)
    assert 'no active repeat8 or sequence9 runtime shape' in _flat(text)
    assert 'No source-wrapper, `ccb_test`, provider, L1-L4, L5, B7, cleanup, or runtime' in text
    assert 'must not grant approval-to-run from this historical record' in text
    assert 'PHASE 6B UNCLAIMED' in text


def test_repeat8_evidence_and_source_reaudit_are_preserved() -> None:
    text = _text(HISTORICAL_REQUEST)

    assert CONSUMED_REPEAT8_ROOT in text
    assert CONSUMED_REPEAT8_B7 in text
    assert 'Status: not_claimable' in text
    assert 'cleanup: complete, state=unmounted' in text
    assert 'Sequence8 must not be reapproved or reused.' in text
    assert 'phase6b-repeat8-direct-execution-failure-note.md' in text
    assert SOURCE_REAUDIT_ACCEPTANCE_JOB in text
    assert 'source-level blockers accepted' in text
    assert 'provider/reviewer replies remain evidence only' in text


def test_historical_file_has_no_runtime_command_or_normalizer_blocks() -> None:
    text = _text(HISTORICAL_REQUEST)

    assert '```bash' not in text
    assert 'PHASE6B_L1L4_ROOT=' not in text
    assert 'PHASE6B_L1L4_SCRIPT' not in text
    assert 'run_l1_l4_sequence9.sh' not in text
    assert 'loop runner --once' not in text
    assert 'Draft repeat9 B7 normalization command shape' not in text
    assert 'Archived Draft Command Shape' not in text
    assert 'write_b7_report()' not in text


def test_future_sequence9_requirements_are_documented_without_authority() -> None:
    text = _text(HISTORICAL_REQUEST)

    assert 'Future Sequence9 Requirements' in text
    assert 'phase6b-l1-l4-launch-request-sequence9-20260704.md' in text
    assert SEQUENCE9_ROOT in text
    assert SEQUENCE9_B7 in text
    assert 'Before any approved future `init`, talk2 must reconfirm the sequence9 root is' in text
    assert 'absent' in text
    assert 'Future sequence9 active request file prepared only after talk2 explicitly' in text
    assert 'Reviewer2 launch-specific approval-to-run for that future file only' in text
    assert 'Reviewer-gated B7 aggregation before any Phase 6B claim' in text


def test_sequence9_packet_if_present_is_consumed_not_launch_approval() -> None:
    if not SEQUENCE9_REQUEST.exists():
        return

    text = _text(SEQUENCE9_REQUEST)
    flat = _flat(text)
    assert 'PHASE 6B UNCLAIMED' in text
    assert 'DO NOT RUN' in text
    assert 'APPROVAL-TO-RUN GRANTED' not in text
    assert 'does not request or authorize any further runtime execution' in flat
    assert 'job_c4935017fc15' in text
    assert 'Sequence9 is consumed and must not be reused' in text
    assert 'phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md' in text


def test_sequence10_packet_records_consumed_repeat10_result() -> None:
    text = _sequence10_text()
    flat = _flat(text)
    driver = _sequence10_driver()

    assert text.startswith('# Phase 6B L1-L4 Sequence10 Repair Launch Packet')
    assert 'SEQUENCE10 CONSUMED HISTORICAL RECORD / DO NOT RUN / PHASE 6B UNCLAIMED' in text
    assert 'does not request or authorize any further runtime execution' in flat
    assert 'This section is retained for traceability only' in flat
    assert 'Do not execute this historical packet' in flat
    assert 'This is the command shape from the consumed sequence10 packet' in flat
    assert 'Do not run this root again' in flat
    assert 'This packet prepares a fresh Phase 6B L1-L4 sequence10 repair launch' not in text
    assert 'reviewer1 fallback launch gate' in text
    assert 'job_bfe386ae7a9f' in text
    assert 'Status: not_claimable' in text
    assert 'cleanup returned `kill_status: ok`' in text
    assert SEQUENCE10_ROOT in text
    assert ': "${PHASE6B_L1L4_ROOT:?}"' in driver
    assert SEQUENCE10_B7 in text
    assert ': "${PHASE6B_L1L4_B7:?}"' in driver
    assert 'phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md' in text
    assert 'Sequence9 is consumed and must not be reused' in text
    assert 'any reuse of consumed sequence1 through sequence9 roots or approvals' in text
    assert 'phase6-real-lab-l1-l4-sequence9-20260704' in text
    assert 'phase6-real-lab-l1-l4-sequence9-20260704' not in driver
    assert 'repeat9-b7-20260704' not in driver
    assert 'repeat10-supervisor-correction' not in text
    assert 'PHASE 6B UNCLAIMED' in text
    assert 'does not claim Phase 6B' in flat
    assert 'export HOME=' not in driver
    assert 'export CCB_SOURCE_HOME=' not in driver
    assert 'export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"' in text
    assert ': "${AGENT_ROLES_STORE:?}"' in driver
    assert '--project "$PHASE6B_L1L4_PROJECT"' in driver
    assert '--kind blocker_evidence' in driver
    assert 'execution_after_detail_ready: false' in text
    assert 'No runtime/provider/source-wrapper/L1-L4/L5/B7/cleanup/launch command is run' in text


def test_sequence11_packet_is_consumed_historical_after_supervised_run() -> None:
    text = _sequence11_text()
    flat = _flat(text)
    driver = _sequence11_driver()

    assert text.startswith('# Phase 6B L1-L4 Sequence11 Repair Launch Packet')
    assert 'SEQUENCE11 CONSUMED HISTORICAL RECORD / DO NOT RUN THIS ROOT AGAIN' in text
    assert 'no longer requests or grants runtime approval' in flat
    assert 'Do not run this root again' in flat
    assert 'do not reuse the embedded command block except for forensic review' in flat
    assert 'APPROVAL-TO-RUN GRANTED' in text
    assert SEQUENCE11_ROOT in text
    assert ': "${PHASE6B_L1L4_ROOT:?}"' in driver
    assert SEQUENCE11_B7 in text
    assert ': "${PHASE6B_L1L4_B7:?}"' in driver
    assert 'phase6b-l1-l4-launch-request-sequence10-20260704.md' in text
    assert 'Sequence10 is consumed and must not be reused' in text
    assert SOURCE_REPAIR_JOB in text
    assert SOURCE_REPAIR_REVIEW_JOB in text
    assert SOURCE_REPAIR_REVIEW_ARTIFACT in text
    assert 'promotes allowed isolated worker workspace deltas into the project root' in flat
    assert 'rolls staged changes back' in text
    assert '89 passed' in text
    assert 'approved once by reviewer1 `job_68063ec21783` and consumed once' in text
    assert 'repeat11 B7 as `not_claimable`' in text
    assert 'cleanup returned' in text
    assert 'does not claim Phase 6B' in flat
    assert 'does not approve L5' in flat
    assert 'any reuse of sequence10 or earlier roots' in flat
    assert 'FRESH SEQUENCE11 APPROVAL REQUEST' not in text
    assert 'Reviewer2 is asked to return exactly one of' not in text
    assert 'BLOCKER' not in text


def test_sequence11_command_shape_preserves_real_provider_constraints() -> None:
    text = _sequence11_text()
    driver = _sequence11_driver()

    assert 'cd /home/bfly/yunwei/test_ccb2' in text
    assert f'export PHASE6B_L1L4_ROOT={SEQUENCE11_ROOT}' in text
    assert 'export HOME=' not in driver
    assert 'export HOME=' not in text
    assert 'export CCB_SOURCE_HOME=' not in driver
    assert 'export CCB_SOURCE_HOME=' not in text
    assert '$PHASE6B_L1L4_ROOT/source_home' not in driver
    assert 'source_home' not in text
    assert 'export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"' in text
    assert ': "${AGENT_ROLES_STORE:?}"' in driver
    assert 'frontdesk:codex; planner:codex; task_detailer:codex; orchestrator:codex; ccb_round_reviewer:claude' in driver
    assert '[loop.role_profiles.ccb_round_reviewer]' in driver
    assert 'provider = "claude"' in driver
    assert '[loop.role_profiles.coder]' in driver
    assert '[loop.role_profiles.code_reviewer]' in driver
    assert '--project "$PHASE6B_L1L4_PROJECT"' in driver
    assert '--kind blocker_evidence' in driver
    assert '--kind blocked' not in driver
    assert 'blocked.md' not in driver
    assert 'blocked.md' not in text
    assert 'execution_after_detail_ready: false' in text
    assert 'B7 normalization must run before any external cleanup' in text
    assert 'topology_dispatch_absent' in driver
    assert 'topology_dispatch.json' in text
    assert 'communication_edges_absent' in driver
    assert 'provider_reply_authority_parsing_absent' in driver
    assert '"edges"' not in driver
    assert '"gates"' not in driver
    assert '"artifacts":' not in driver
    assert 'edges =' not in driver
    assert 'gates =' not in driver
    assert 'artifacts =' not in driver
    assert 'phase6-real-lab-l1-l4-sequence9-20260704' not in driver
    assert 'phase6-real-lab-l1-l4-sequence10-20260704' not in driver
    assert 'repeat9-b7-20260704' not in driver
    assert 'repeat10-b7-20260704' not in driver


def test_sequence11_detail_import_command_shape_keeps_route_authority_on_orchestration_notes_only() -> None:
    driver = _sequence11_driver()

    assert '--kind orchestration_notes \\\n    --file "$notes_file" --route "$observed_route" --json' in driver
    assert '--file "$detail_design" --route needs_detail --json' not in driver
    assert '--file "$detail_summary" --route needs_detail --json' not in driver
    assert '--file "$detail_packet" --route needs_detail --json' not in driver
    assert '--kind macro_adjustment_request \\\n        --file "$macro_file" --json' in driver
    assert '--kind blocker_evidence \\\n        --file "$blocker_file" --json' in driver
    assert '--next-owner orchestrator --activation-reason phase6b_l1_l4_sequence11_detail_ready' not in driver
    assert (
        'plan task-status --task "$task_id" --status detail_ready \\\n'
        '    --activation-reason phase6b_l1_l4_sequence11_detail_ready --json'
    ) in driver


def test_sequence11_run_required_fails_hard_on_command_status_failed_text_and_json(tmp_path: Path) -> None:
    for label, shell_command in (
        ('failed_text', 'printf "command_status: failed\\nerror: fake\\n" >&2'),
        ('failed_json', 'printf "{\\"command_status\\":\\"failed\\",\\"error\\":\\"fake\\"}\\n"'),
    ):
        root = tmp_path / label
        command_log = root / 'command_log.jsonl'
        script = "\n".join(
            (
                'set -euo pipefail',
                f'PHASE6B_L1L4_ROOT={shlex.quote(str(root))}',
                f'PHASE6B_L1L4_COMMAND_LOG={shlex.quote(str(command_log))}',
                'PHASE6B_L1L4_TIMEOUT_SECONDS=5',
                'timeout() { shift; shift; "$@"; }',
                _sequence11_run_required_function(),
                f'run_required {shlex.quote(label)} bash -c {shlex.quote(shell_command)}',
            )
        )

        result = subprocess.run(['bash'], input=script, text=True, capture_output=True, check=False)

        assert result.returncode == 1
        records = [json.loads(line) for line in command_log.read_text(encoding='utf-8').splitlines()]
        assert len(records) == 1
        assert records[0]['label'] == label
        assert records[0]['returncode'] == 1
        assert records[0]['stderr'] == str(root / 'logs' / f'{label}.stderr')
        assert records[0]['stdout'] == str(root / 'logs' / f'{label}.stdout')
        assert str(records[0]['command']).startswith('bash -c ')
        assert f'command failed: {label} rc=1' in result.stderr


def test_sequence11_embedded_driver_and_normalizer_are_static_parseable() -> None:
    driver = _sequence11_driver()
    shell_parse = subprocess.run(
        ['bash', '-n'],
        input=driver,
        text=True,
        capture_output=True,
        check=False,
    )
    assert shell_parse.returncode == 0, shell_parse.stderr

    for embedded_python in re.findall(r"<<'PY'\n(.*?)\nPY", driver, flags=re.S):
        compile(embedded_python, '<phase6b-l1-l4-sequence11-driver-python>', 'exec')


def test_sequence11_evidence_is_consumed_after_supervised_run() -> None:
    combined = '\n'.join(
        _text(path)
        for path in (IMPLEMENTATION_STATUS, CLAIM_COVERAGE_MATRIX, ACTIVE_SUPERVISION_BOARD)
        if path.exists()
    )
    assert 'Sequence11 is consumed' in combined
    assert 'Sequence12 is consumed/non-reusable' in combined


def test_sequence12_packet_records_consumed_single_use_runtime() -> None:
    text = _sequence12_text()
    flat = _flat(text)
    driver = _sequence12_driver()

    assert text.startswith('# Phase 6B L1-L4 Sequence12 Launch Packet')
    assert 'CONSUMED / RUNTIME B7 PASS / PHASE 6B UNCLAIMED' in text
    assert 'consumed launch and evidence record' in flat
    assert 'Do not rerun this root or reuse this command shape' in flat
    assert 'APPROVAL-TO-RUN GRANTED BY TALK2 SELF-REVIEW' in text
    assert 'APPROVAL BLOCKED' in text
    assert 'Talk2 recorded the following launch decision before execution' in text
    assert SEQUENCE12_ROOT in text
    assert SEQUENCE12_B7 in text
    assert 'Sequence11 is consumed and non-reusable' in text
    assert 'job_ad72d8bb8790' in text
    assert 'job_f3982925275d' in text
    assert 'job_dd89005df2ee' in text
    assert 'cb_faab6bb2d057-art_f9e89c4d470a4c16.txt' in text
    assert 'does not permit any reuse of sequence12 or earlier roots' in flat
    assert 'Do not run it again' in text
    assert 'phase6-real-lab-l1-l4-sequence11-20260704' not in driver
    assert 'phase6b-real-provider-l1-l4-repeat11-b7-20260704' not in driver


def test_sequence12_b7_is_consumed_after_runtime() -> None:
    b7_path = PROJECT_ROOT / SEQUENCE12_B7
    assert b7_path.exists()
    assert 'Status: pass' in _text(b7_path)


def test_sequence12_command_shape_preserves_real_provider_constraints_and_repairs() -> None:
    text = _sequence12_text()
    driver = _sequence12_driver()
    run_required = _sequence12_run_required_function()

    assert 'cd /home/bfly/yunwei/test_ccb2' in text
    assert f'export PHASE6B_L1L4_ROOT={SEQUENCE12_ROOT}' in text
    assert 'export HOME=' not in driver
    assert 'export HOME=' not in text
    assert 'export CCB_SOURCE_HOME=' not in driver
    assert 'export CCB_SOURCE_HOME=' not in text
    assert '$PHASE6B_L1L4_ROOT/source_home' not in driver
    assert 'source_home' not in text
    assert 'export AGENT_ROLES_STORE="$PHASE6B_L1L4_ROOT/roles"' in text
    assert ': "${AGENT_ROLES_STORE:?}"' in driver
    assert '/home/bfly/yunwei/ccb_source/ccb_test roles install "$role_id" --skip-tools' in driver
    assert '--project "$PHASE6B_L1L4_PROJECT" \\\n      roles install' not in driver
    assert 'validate_seeded_rolepacks' in driver
    assert '$AGENT_ROLES_STORE/installed/${role_id}/current/role.toml' in driver
    assert '$AGENT_ROLES_STORE/installed/${role_id}/install.json' in driver
    assert 'frontdesk:codex; planner:codex; task_detailer:codex; orchestrator:codex; ccb_round_reviewer:claude' in driver
    assert '[loop.role_profiles.ccb_round_reviewer]' in driver
    assert 'provider = "claude"' in driver
    assert '[loop.role_profiles.coder]' in driver
    assert '[loop.role_profiles.code_reviewer]' in driver
    assert '--project "$PHASE6B_L1L4_PROJECT"' in driver
    assert '--kind orchestration_notes \\\n    --file "$notes_file" --route "$observed_route" --json' in driver
    assert '--file "$detail_design" --route needs_detail --json' not in driver
    assert '--file "$detail_summary" --route needs_detail --json' not in driver
    assert '--file "$detail_packet" --route needs_detail --json' not in driver
    assert '--kind macro_adjustment_request \\\n        --file "$macro_file" --json' in driver
    assert '--kind blocker_evidence \\\n        --file "$blocker_file" --json' in driver
    assert '--kind blocked' not in driver
    assert 'blocked.md' not in driver
    assert 'blocked.md' not in text
    assert (
        'plan task-status --task "$task_id" --status detail_ready \\\n'
        '    --activation-reason phase6b_l1_l4_sequence12_detail_ready --json'
    ) in driver
    assert '--next-owner orchestrator --activation-reason phase6b_l1_l4_sequence12_detail_ready' not in driver
    assert 'timeout --preserve-status' in run_required
    assert 'CCB_PHASE6B_RUN_WITHOUT_TIMEOUT' in run_required
    assert 'run_unbounded_required "${task_id}__activate_orchestrator"' in driver
    assert 'run_unbounded_required "${task_id}__run_direct_execution_round"' in driver
    assert 'run_unbounded_required "${task_id}__activate_detailer"' in driver
    assert 'loop runner --once --timeout "$PHASE6B_L1L4_TIMEOUT_SECONDS"' not in driver
    assert 'command_status' in run_required
    assert 'ensure_task_record "$task_id"' in driver
    assert 'task_record_exists()' in driver
    assert 'plan task-show --task "$task_id" --json >/dev/null 2>/dev/null' in driver
    assert '__task_observe_existing' in driver
    assert 'frontdesk_l1_l4_entry_request.md' in driver
    assert 'run_l1_l4_sequence12.sh frontdesk-entry' in driver
    assert 'ask frontdesk -- "$(cat "$PHASE6B_L1L4_ROOT/frontdesk_l1_l4_entry_request.md")"' in driver
    assert 'controller-owned route-mix validation, not as a worker implementation task' in driver
    assert 'Do not ask a worker to run the retest harness' in driver
    assert 'validate_sequence_task_set_only' in driver
    assert 'frontdesk/planner created non-sequence task(s)' in driver
    assert 'refuse: L1-L4 deployment harness must use one authoritative sequence task set' in driver
    assert 'assert_no_pending_round_authority "$task_id"' in driver
    assert 'assert_no_pending_round_authority ""' in driver
    assert 'ask_job_incomplete' in driver
    assert 'round authority pending/incomplete' in driver
    assert 'task_show_source' in driver
    assert 'task_show_stale' in driver
    assert 'round_json_path' in driver
    assert 'unexpected_plan_tasks' in driver
    assert 'topology_dispatch_absent' in driver
    assert 'topology_dispatch.json' in text
    assert 'communication_edges_absent' in driver
    assert 'provider_reply_authority_parsing_absent' in driver
    assert '"edges"' not in driver
    assert '"gates"' not in driver
    assert '"artifacts":' not in driver
    assert 'edges =' not in driver
    assert 'gates =' not in driver
    assert 'artifacts =' not in driver
    assert 'normalized_summary_key' in driver
    assert 'last_round_result' in driver
    assert 'round_artifact_path_from' in driver
    assert 'direct_round_observed' in driver
    assert 'cleanup_after_b7_unmounted' in driver
    assert 'observed_topology_has_dynamic_residue' in driver
    assert '"# Phase 6B L1-L4 Repeat12 B7\\n\\n"' in driver


def test_sequence12_embedded_driver_and_normalizer_are_static_parseable() -> None:
    driver = _sequence12_driver()
    shell_parse = subprocess.run(
        ['bash', '-n'],
        input=driver,
        text=True,
        capture_output=True,
        check=False,
    )
    assert shell_parse.returncode == 0, shell_parse.stderr

    for embedded_python in re.findall(r"<<'PY'\n(.*?)\nPY", driver, flags=re.S):
        compile(embedded_python, '<phase6b-l1-l4-sequence12-driver-python>', 'exec')


def test_sequence12_driver_rejects_meta_task_and_pending_round_before_cleanup(tmp_path: Path) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    index_path = (
        project
        / 'docs'
        / 'plantree'
        / 'plans'
        / 'phase6b-real-provider-l1-l4'
        / 'tasks'
        / 'index.json'
    )
    _write_json(
        index_path,
        {
            'tasks': [
                {'task_id': 'fresh-sequence17-real-provider-deploymen-20260707052218'},
                {'task_id': 'phase6b-l1-doc-direct-execution'},
            ],
        },
    )

    result = _run_sequence12_driver_fragment(tmp_path, 'validate_sequence_task_set_only')

    assert result.returncode == 75
    assert 'frontdesk/planner created non-sequence task(s)' in result.stderr
    assert 'fresh-sequence17-real-provider-deploymen-20260707052218' in result.stderr
    assert 'one authoritative sequence task set' in result.stderr

    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lppending' / 'round.pending.json',
        {
            'task_id': 'phase6b-l1-doc-direct-execution',
            'loop_run_status': 'pending',
            'round_result': 'pending',
            'round_result_source': 'ask_job_pending',
            'pending': {
                'purpose': 'worker',
                'job_id': 'job_live_worker',
                'watch_observation': 'timeout',
            },
        },
    )
    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lppending' / 'ask_first_stage_state.json',
        {
            'task_id': 'phase6b-l1-doc-direct-execution',
            'loop_id': 'lppending',
            'status': 'pending',
            'stage': 'worker_ask',
            'purpose': 'worker',
            'job_id': 'job_live_worker',
        },
    )

    result = _run_sequence12_driver_fragment(tmp_path, 'assert_no_pending_round_authority ""')

    assert result.returncode == 78
    assert 'round authority pending/incomplete: ask_job_pending' in result.stderr
    assert 'round.pending.json' in result.stderr
    assert 'refuse cleanup/progress' in result.stderr

    (project / '.ccb' / 'runtime' / 'loops' / 'lppending' / 'round.pending.json').unlink()
    (project / '.ccb' / 'runtime' / 'loops' / 'lppending' / 'ask_first_stage_state.json').unlink()

    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lppending' / 'round.json',
        {
            'task_id': 'phase6b-l1-doc-direct-execution',
            'round_result': 'blocked',
            'round_result_source': 'ask_job_incomplete',
            'worker': {'job_id': 'job_e26da64f009c', 'status': 'incomplete'},
        },
    )

    result = _run_sequence12_driver_fragment(tmp_path, 'assert_no_pending_round_authority ""')

    assert result.returncode == 78
    assert 'round authority pending/incomplete: ask_job_incomplete' in result.stderr
    assert 'refuse cleanup/progress' in result.stderr


def test_sequence12_b7_normalizer_uses_final_index_and_round_json_not_stale_task_show(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    meta_task = 'fresh-sequence17-real-provider-deploymen-20260707052218'
    round_path = (
        project
        / 'docs'
        / 'plantree'
        / 'plans'
        / 'phase6b-real-provider-l1-l4'
        / 'tasks'
        / l1
        / 'round_summary.md'
    )

    task_dir = _task_dir(project, l1)
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
    round_path.parent.mkdir(parents=True)
    round_path.write_text(
        'round_result: blocked\nround_result_source: ask_job_incomplete\n',
        encoding='utf-8',
    )
    _write_task_show(
        root,
        l1,
        {
            'status': 'ready_for_orchestration',
            'task': {
                'status': 'ready_for_orchestration',
                'next_owner': 'orchestrator',
            },
        },
    )
    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / 'lp451adf' / 'round.json',
        {
            'task_id': l1,
            'finished_at': '2026-07-07T05:40:00Z',
            'round_result': 'blocked',
            'round_result_source': 'ask_job_incomplete',
            'paths': {'round': str(round_path.relative_to(project))},
            'worker': {'job_id': 'job_e26da64f009c', 'status': 'incomplete'},
        },
    )
    _write_json(
        project
        / 'docs'
        / 'plantree'
        / 'plans'
        / 'phase6b-real-provider-l1-l4'
        / 'tasks'
        / 'index.json',
        {
            'tasks': [
                {
                    'task_id': meta_task,
                    'status': 'blocked',
                    'next_owner': 'terminal',
                },
                {
                    'task_id': l1,
                    'status': 'blocked',
                    'next_owner': 'terminal',
                    'artifacts': {
                        'round_summary': {
                            'path': str(round_path.relative_to(project)),
                            'round_result': 'blocked',
                            'round_result_source': 'ask_job_incomplete',
                        },
                    },
                    'last_round': {
                        'result': 'blocked',
                        'artifact_kind': 'round_summary',
                        'artifact_path': str(round_path.relative_to(project)),
                    },
                },
            ],
        },
    )

    _b7_path, rows, report = _run_sequence12_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert 'Status: not_claimable' in report
    assert row['task_show_observed'] is True
    assert row['task_show_source'] == 'task_index'
    assert row['task_show_path'].endswith('tasks/index.json')
    assert row['task_show_stale'] is False
    assert row['final_status'] == 'blocked'
    assert row['next_owner'] == 'terminal'
    assert row['round_summary_observed'] is True
    assert row['round_summary_path'] == str(round_path)
    assert row['round_json_path'] == str(project / '.ccb' / 'runtime' / 'loops' / 'lp451adf' / 'round.json')
    assert row['round_result'] == 'blocked'
    assert row['round_result_source'] == 'ask_job_incomplete'
    assert row['classification'] == 'test_design_failure'
    assert row['claimable_row'] is False
    assert row['unexpected_plan_tasks'] == [meta_task]
    assert 'unexpected non-sequence task(s): ' + meta_task in row['evidence_errors']
    assert 'status mismatch: blocked' in row['evidence_errors']
    assert 'round/result mismatch: blocked' in row['evidence_errors']
    assert 'task-show missing status' not in row['evidence_errors']
    assert 'missing round/result evidence' not in row['evidence_errors']


def test_sequence12_b7_normalizer_preserves_sequence11_repairs(tmp_path: Path) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    l2 = 'phase6b-l2-code-test-direct-execution'
    l3 = 'phase6b-l3-needs-detail-source-inspection'
    l4_macro = 'phase6b-l4-macro-adjustment-request'
    l4_blocked = 'phase6b-l4-blocked-missing-secret'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_code').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    (project / 'lab_code' / 'calculator.py').write_text('def add(a, b):\n    return a + b\n', encoding='utf-8')

    for task_id, loop_id in ((l1, 'lpseq12a'), (l2, 'lpseq12b')):
        task_dir = _task_dir(project, task_id)
        (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
        (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
        (task_dir / 'round_summary.md').write_text(
            'round result: pass\nround_result_source: round_reviewer_reply\n',
            encoding='utf-8',
        )
        (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
        (task_dir / 'reviewer_verdict.md').write_text(
            'reviewed task_packet and execution_contract\n',
            encoding='utf-8',
        )
        _write_task_show(
            root,
            task_id,
            {
                'task': {
                    'status': 'done',
                    'next_owner': 'terminal',
                    'last_round': {'result': 'pass', 'artifact_kind': 'round_summary'},
                },
            },
        )
        _write_released_observed_topology(project, loop_id)

    _write_json(
        project / 'supervisor_imports' / l2 / 'project_root_test_resolution.json',
        {
            'test_result': 'pass',
            'test_file_resolved_to_lab': True,
            'test_sys_path_project_first': True,
        },
    )

    l3_dir = _task_dir(project, l3)
    (l3_dir / 'route.txt').write_text('needs_detail\n', encoding='utf-8')
    (l3_dir / 'orchestration_notes.md').write_text('route: needs_detail\n', encoding='utf-8')
    (l3_dir / 'round_summary.md').write_text('round_result: detail_ready\n', encoding='utf-8')
    (l3_dir / 'detail_packet.manifest.json').write_text('{}\n', encoding='utf-8')
    (l3_dir / 'steps').mkdir(parents=True)
    (l3_dir / 'steps' / 'step-001.md').write_text('# Step\n', encoding='utf-8')
    _write_task_show(
        root,
        l3,
        {
            'status': 'ready_for_orchestration',
            'task': {'status': 'ready_for_orchestration', 'next_owner': 'orchestrator'},
        },
    )

    _write_jsonl(
        root / 'phase6b_l1_l4_sequence12_command_log.jsonl',
        [
            {'label': f'{l1}__run_direct_execution_round', 'returncode': 0},
            {'label': f'{l2}__run_direct_execution_round', 'returncode': 0},
        ],
    )

    _b7_path, rows, report = _run_sequence12_normalizer(tmp_path)
    by_task = {str(item['task_id']): item for item in rows}

    assert 'Status: not_claimable' in report
    for task_id in (l1, l2):
        row = by_task[task_id]
        assert row['classification'] == 'pass'
        assert row['claimable_row'] is True
        assert row['round_result'] == 'pass'
        assert row['authority_checks']['script_owned_round_imports'] is True
        assert row['authority_checks']['observed_topology_residue_absent'] is True
        assert row['evidence_errors'] == []

    assert by_task[l3]['classification'] == 'test_design_failure'
    assert by_task[l3]['claimable_row'] is False
    assert 'status mismatch: ready_for_orchestration' in by_task[l3]['evidence_errors']

    for task_id in (l4_macro, l4_blocked):
        assert by_task[task_id]['classification'] == 'test_design_failure'
        assert by_task[task_id]['claimable_row'] is False
        assert 'missing task-show evidence' in by_task[task_id]['evidence_errors']


def test_sequence12_b7_normalizer_reads_round_summary_from_task_show_artifact_path(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    round_path = (
        project
        / 'docs'
        / 'plantree'
        / 'plans'
        / 'phase6b-real-provider-l1-l4'
        / 'tasks'
        / l1
        / 'round_summary.md'
    )

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    task_dir = _task_dir(project, l1)
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
    (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
    (task_dir / 'reviewer_verdict.md').write_text(
        'reviewed task_packet and execution_contract\n',
        encoding='utf-8',
    )
    round_path.parent.mkdir(parents=True)
    round_path.write_text(
        'round_result: pass\nround_result_source: runtime_round_summary\n',
        encoding='utf-8',
    )
    _write_task_show(
        root,
        l1,
        {
            'status': 'done',
            'task': {
                'status': 'done',
                'next_owner': 'terminal',
                'artifacts': {
                    'round_summary': {
                        'path': str(round_path.relative_to(project)),
                        'round_result': 'pass',
                    },
                },
                'last_round': {
                    'result': 'pass',
                    'artifact_kind': 'round_summary',
                    'artifact_path': str(round_path.relative_to(project)),
                },
            },
        },
    )
    _write_released_observed_topology(project, 'lpseq12artifact')

    _b7_path, rows, _report = _run_sequence12_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert row['classification'] == 'pass'
    assert row['round_summary_observed'] is True
    assert row['round_summary_path'] == str(round_path)
    assert row['round_result'] == 'pass'
    assert row['round_result_source'] == 'runtime_round_summary'
    assert row['authority_checks']['script_owned_round_imports'] is True
    assert 'missing round/result evidence' not in row['evidence_errors']


def test_sequence12_b7_normalizer_treats_stale_topology_as_released_after_cleanup_unmounted(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence12-20260705'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    loop_id = 'lpstale'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    task_dir = _task_dir(project, l1)
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text(
        'round_result: pass\nround_result_source: round_reviewer_reply\n',
        encoding='utf-8',
    )
    (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
    (task_dir / 'reviewer_verdict.md').write_text(
        'reviewed task_packet and execution_contract\n',
        encoding='utf-8',
    )
    _write_task_show(
        root,
        l1,
        {
            'status': 'done',
            'task': {
                'status': 'done',
                'next_owner': 'terminal',
                'last_round': {'result': 'pass', 'artifact_kind': 'round_summary'},
            },
        },
    )
    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / loop_id / 'agent_mount_topology.observed.json',
        {
            'schema': 'ccb.loop.agent_mount_topology.observed.v1',
            'record_type': 'ccb_loop_agent_mount_topology_observed',
            'loop_id': loop_id,
            'agents': [{'id': f'loop-{loop_id}-coder-1'}],
            'retained_agents': [f'loop-{loop_id}-coder-1'],
            'retained_count': 1,
        },
    )
    _write_jsonl(
        root / 'phase6b_l1_l4_sequence12_command_log.jsonl',
        [{'label': f'{l1}__run_direct_execution_round', 'returncode': 0}],
    )

    _b7_path, rows, _report = _run_sequence12_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert row['authority_checks']['observed_topology_residue_absent'] is False
    assert 'authority check failed: observed_topology_residue_absent' in row['evidence_errors']

    (root / 'logs').mkdir(parents=True, exist_ok=True)
    (root / 'logs' / 'cleanup_after_b7.stdout').write_text(
        'kill_status: ok\nstate: unmounted\n',
        encoding='utf-8',
    )

    _b7_path, rows, _report = _run_sequence12_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert row['round_result'] == 'pass'
    assert row['authority_checks']['observed_topology_residue_absent'] is True
    assert 'authority check failed: observed_topology_residue_absent' not in row['evidence_errors']


def test_sequence10_embedded_driver_and_normalizer_are_static_parseable() -> None:
    driver = _sequence10_driver()
    shell_parse = subprocess.run(
        ['bash', '-n'],
        input=driver,
        text=True,
        capture_output=True,
        check=False,
    )
    assert shell_parse.returncode == 0, shell_parse.stderr

    for embedded_python in re.findall(r"<<'PY'\n(.*?)\nPY", driver, flags=re.S):
        compile(embedded_python, '<phase6b-l1-l4-sequence10-driver-python>', 'exec')


def test_sequence10_b7_normalizer_rejects_repeat9_false_pass_shape(tmp_path: Path) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence10-20260704'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    l2 = 'phase6b-l2-code-test-direct-execution'
    l3 = 'phase6b-l3-needs-detail-source-inspection'
    l4_macro = 'phase6b-l4-macro-adjustment-request'
    l4_blocked = 'phase6b-l4-blocked-missing-secret'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_code').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    (project / 'lab_code' / 'calculator.py').write_text('def add(a, b):\n    return a + b\n', encoding='utf-8')

    for task_id, final_status, round_result, source in (
        (l1, 'done', 'pass', 'round_reviewer_reply'),
        (l2, 'blocked', 'blocked', 'isolated_workspace_no_project_root_effect'),
    ):
        task_dir = _task_dir(project, task_id)
        (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
        (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
        (task_dir / 'round_summary.md').write_text(
            f'round_result: {round_result}\nround_result_source: {source}\n',
            encoding='utf-8',
        )
        (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
        (task_dir / 'reviewer_verdict.md').write_text('cites task_packet and execution_contract\n', encoding='utf-8')
        _write_task_show(
            root,
            task_id,
            {
                'status': final_status,
                'round_result_source': source,
                'task': {'status': final_status, 'next_owner': 'orchestrator'},
            },
        )

    _write_json(
        project / 'supervisor_imports' / l2 / 'project_root_test_resolution.json',
        {
            'test_result': 'pass',
            'test_file_resolved_to_lab': True,
            'test_sys_path_project_first': True,
        },
    )
    _write_jsonl(
        root / 'phase6b_l1_l4_sequence10_command_log.jsonl',
        [
            {'label': f'{l1}__run_direct_execution_round', 'returncode': 0},
            {'label': f'{l2}__run_direct_execution_round', 'returncode': 0},
        ],
    )

    _b7_path, rows, report = _run_sequence10_normalizer(tmp_path)
    by_task = {str(row['task_id']): row for row in rows}

    assert 'Status: not_claimable' in report
    assert by_task[l1]['classification'] == 'pass'
    assert by_task[l1]['task_show_observed'] is True
    assert by_task[l1]['final_status'] == 'done'
    assert by_task[l2]['final_status'] == 'blocked'
    assert by_task[l2]['round_result'] == 'blocked'
    assert by_task[l2]['round_result_source'] == 'isolated_workspace_no_project_root_effect'
    assert by_task[l2]['classification'] == 'test_design_failure'
    assert by_task[l2]['claimable_row'] is False
    assert 'status mismatch: blocked' in by_task[l2]['evidence_errors']
    assert by_task[l3]['final_status'] == 'missing'
    assert by_task[l3]['classification'] == 'test_design_failure'
    assert by_task[l3]['claimable_row'] is False
    assert 'missing task-show evidence' in by_task[l3]['evidence_errors']
    assert by_task[l4_macro]['classification'] == 'test_design_failure'
    assert by_task[l4_macro]['classification'] != 'valid_non_success'
    assert by_task[l4_blocked]['classification'] == 'test_design_failure'
    assert by_task[l4_blocked]['classification'] != 'valid_non_success'


def test_sequence10_b7_normalizer_missing_task_show_does_not_fallback_to_expected(tmp_path: Path) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence10-20260704'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    task_dir = _task_dir(project, l1)
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text('round_result: pass\nround_result_source: static-test\n', encoding='utf-8')
    (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
    (task_dir / 'reviewer_verdict.md').write_text('cites task_packet and execution_contract\n', encoding='utf-8')
    _write_jsonl(
        root / 'phase6b_l1_l4_sequence10_command_log.jsonl',
        [{'label': f'{l1}__run_direct_execution_round', 'returncode': 0}],
    )

    _b7_path, rows, report = _run_sequence10_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert 'Status: not_claimable' in report
    assert row['final_status'] == 'missing'
    assert row['expected_final_status'] == 'done'
    assert row['classification'] == 'test_design_failure'
    assert row['claimable_row'] is False
    assert 'missing task-show evidence' in row['evidence_errors']


def test_sequence11_b7_normalizer_missing_task_show_does_not_fallback_to_expected(tmp_path: Path) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence11-20260704'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    task_dir = _task_dir(project, l1)
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text('round_result: pass\nround_result_source: static-test\n', encoding='utf-8')
    (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
    (task_dir / 'reviewer_verdict.md').write_text('cites task_packet and execution_contract\n', encoding='utf-8')
    _write_jsonl(
        root / 'phase6b_l1_l4_sequence11_command_log.jsonl',
        [{'label': f'{l1}__run_direct_execution_round', 'returncode': 0}],
    )

    _b7_path, rows, report = _run_sequence11_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert 'Status: not_claimable' in report
    assert row['final_status'] == 'missing'
    assert row['expected_final_status'] == 'done'
    assert row['classification'] == 'test_design_failure'
    assert row['claimable_row'] is False
    assert 'missing task-show evidence' in row['evidence_errors']


def test_sequence11_b7_normalizer_accepts_direct_rows_with_legacy_round_result_and_topology_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence11-20260704'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    l2 = 'phase6b-l2-code-test-direct-execution'
    l3 = 'phase6b-l3-needs-detail-source-inspection'
    l4_macro = 'phase6b-l4-macro-adjustment-request'
    l4_blocked = 'phase6b-l4-blocked-missing-secret'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_code').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    (project / 'lab_code' / 'calculator.py').write_text('def add(a, b):\n    return a + b\n', encoding='utf-8')

    for task_id, loop_id in ((l1, 'lp5fe8bb'), (l2, 'lp22e4d1')):
        task_dir = _task_dir(project, task_id)
        (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
        (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
        (task_dir / 'round_summary.md').write_text(
            'round result: pass\nround_result_source: round_reviewer_reply\n',
            encoding='utf-8',
        )
        (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
        (task_dir / 'reviewer_verdict.md').write_text(
            'reviewed task_packet and execution_contract\n',
            encoding='utf-8',
        )
        _write_task_show(
            root,
            task_id,
            {
                'status': 'done',
                'task': {
                    'status': 'done',
                    'next_owner': 'terminal',
                    'last_round': {'result': 'pass', 'artifact_kind': 'round_summary'},
                },
            },
        )
        _write_released_observed_topology(project, loop_id)

    _write_json(
        project / 'supervisor_imports' / l2 / 'project_root_test_resolution.json',
        {
            'test_result': 'pass',
            'test_file_resolved_to_lab': True,
            'test_sys_path_project_first': True,
        },
    )

    l3_dir = _task_dir(project, l3)
    (l3_dir / 'route.txt').write_text('needs_detail\n', encoding='utf-8')
    (l3_dir / 'orchestration_notes.md').write_text('route: needs_detail\n', encoding='utf-8')
    (l3_dir / 'round_summary.md').write_text('round_result: detail_ready\n', encoding='utf-8')
    (l3_dir / 'detail_packet.manifest.json').write_text('{}\n', encoding='utf-8')
    (l3_dir / 'steps').mkdir(parents=True)
    (l3_dir / 'steps' / 'step-001.md').write_text('# Step\n', encoding='utf-8')
    _write_task_show(
        root,
        l3,
        {
            'status': 'ready_for_orchestration',
            'task': {'status': 'ready_for_orchestration', 'next_owner': 'orchestrator'},
        },
    )

    _write_jsonl(
        root / 'phase6b_l1_l4_sequence11_command_log.jsonl',
        [
            {'label': f'{l1}__run_direct_execution_round', 'returncode': 0},
            {'label': f'{l2}__run_direct_execution_round', 'returncode': 0},
        ],
    )

    _b7_path, rows, report = _run_sequence11_normalizer(tmp_path)
    by_task = {str(item['task_id']): item for item in rows}

    assert 'Status: not_claimable' in report
    for task_id in (l1, l2):
        row = by_task[task_id]
        assert row['classification'] == 'pass'
        assert row['claimable_row'] is True
        assert row['round_result'] == 'pass'
        assert row['authority_checks']['script_owned_round_imports'] is True
        assert row['authority_checks']['observed_topology_residue_absent'] is True
        assert row['evidence_errors'] == []

    assert by_task[l3]['classification'] == 'test_design_failure'
    assert by_task[l3]['claimable_row'] is False
    assert by_task[l3]['expected_classification'] == 'valid_non_success'
    assert 'status mismatch: ready_for_orchestration' in by_task[l3]['evidence_errors']

    for task_id in (l4_macro, l4_blocked):
        assert by_task[task_id]['classification'] == 'test_design_failure'
        assert by_task[task_id]['claimable_row'] is False
        assert 'missing task-show evidence' in by_task[task_id]['evidence_errors']


def test_sequence11_b7_normalizer_rejects_retained_dynamic_topology_residue(tmp_path: Path) -> None:
    root = tmp_path / 'phase6-real-lab-l1-l4-sequence11-20260704'
    project = root / 'l1-l4-real-provider-lab'
    l1 = 'phase6b-l1-doc-direct-execution'
    loop_id = 'lpbusy'

    (project / 'lab_docs').mkdir(parents=True)
    (project / 'lab_docs' / 'l1_release_note.md').write_text('status: reviewed\n', encoding='utf-8')
    task_dir = _task_dir(project, l1)
    (task_dir / 'route.txt').write_text('direct_execution\n', encoding='utf-8')
    (task_dir / 'orchestration_notes.md').write_text('route: direct_execution\n', encoding='utf-8')
    (task_dir / 'round_summary.md').write_text(
        'round_result: pass\nround_result_source: round_reviewer_reply\n',
        encoding='utf-8',
    )
    (task_dir / 'worker_reply.md').write_text('used task_packet and execution_contract\n', encoding='utf-8')
    (task_dir / 'reviewer_verdict.md').write_text(
        'reviewed task_packet and execution_contract\n',
        encoding='utf-8',
    )
    _write_task_show(
        root,
        l1,
        {
            'status': 'done',
            'task': {
                'status': 'done',
                'next_owner': 'terminal',
                'last_round': {'result': 'pass', 'artifact_kind': 'round_summary'},
            },
        },
    )
    _write_json(
        project / '.ccb' / 'runtime' / 'loops' / loop_id / 'agent_mount_topology.observed.json',
        {
            'schema': 'ccb.loop.agent_mount_topology.observed.v1',
            'record_type': 'ccb_loop_agent_mount_topology_observed',
            'loop_id': loop_id,
            'agents': [{'id': f'loop-{loop_id}-coder-1'}],
            'retained_agents': [f'loop-{loop_id}-coder-1'],
            'retained_count': 1,
        },
    )
    _write_jsonl(
        root / 'phase6b_l1_l4_sequence11_command_log.jsonl',
        [{'label': f'{l1}__run_direct_execution_round', 'returncode': 0}],
    )

    _b7_path, rows, _report = _run_sequence11_normalizer(tmp_path)
    row = {str(item['task_id']): item for item in rows}[l1]

    assert row['round_result'] == 'pass'
    assert row['authority_checks']['script_owned_round_imports'] is True
    assert row['authority_checks']['observed_topology_residue_absent'] is False
    assert row['classification'] == 'test_design_failure'
    assert row['claimable_row'] is False
    assert 'authority check failed: observed_topology_residue_absent' in row['evidence_errors']


def test_stale_source_hold_wording_is_absent_from_active_docs() -> None:
    docs = (
        HISTORICAL_REQUEST,
        SEQUENCE9_REQUEST,
        SEQUENCE10_REQUEST,
        IMPLEMENTATION_STATUS,
        CLAIM_COVERAGE_MATRIX,
        ACTIVE_SUPERVISION_BOARD,
    )
    combined = '\n'.join(_text(path) for path in docs if path.exists())

    for phrase in STALE_SOURCE_HOLD_PHRASES:
        assert phrase not in combined


def test_active_status_docs_do_not_treat_sequence10_as_pending() -> None:
    docs = (
        IMPLEMENTATION_STATUS,
        CLAIM_COVERAGE_MATRIX,
        ACTIVE_SUPERVISION_BOARD,
    )
    combined = '\n'.join(_text(path) for path in docs if path.exists())

    for phrase in STALE_SEQUENCE10_ACTIVE_PHRASES:
        assert phrase not in combined
    assert 'phase6b-l1-l4-launch-request-sequence11-20260704.md' in combined
    assert SEQUENCE11_ROOT in combined
    assert 'phase6b-real-provider-l1-l4-repeat11-b7-20260704.md' in combined
    assert 'Sequence11 is consumed' in combined
    assert 'phase6b-l1-l4-launch-request-sequence12-20260705.md' in combined
    assert SEQUENCE12_ROOT in combined
    assert 'phase6b-real-provider-l1-l4-repeat12-b7-20260705.md' in combined
    assert 'job_a218e823a78f' in combined
    assert 'job_f4ee3f0cc58e' in combined


def test_archived_phase6b_docs_preserve_final_bounded_claim_while_active_status_advances() -> None:
    status_text = _text(IMPLEMENTATION_STATUS)
    coverage_text = _text(CLAIM_COVERAGE_MATRIX)
    board_text = _text(ACTIVE_SUPERVISION_BOARD)
    evidence_index_text = _text(EVIDENCE_INDEX)
    final_report_text = _text(FINAL_ACCEPTANCE_REPORT)

    for text in (coverage_text, board_text):
        assert CONSUMED_REPEAT8_ROOT in text
        assert 'phase6b-real-provider-l1-l4-repeat8-b7-20260704.md' in text
        assert SOURCE_REAUDIT_ACCEPTANCE_JOB in text
        assert SEQUENCE9_ROOT in text
        assert 'phase6b-real-provider-l1-l4-repeat9-b7-20260704.md' in text
        assert 'phase6b-real-provider-l1-l4-repeat9-supervisor-correction-20260704.md' in text
        assert SEQUENCE10_ROOT in text
        assert 'phase6b-l1-l4-launch-request-sequence10-20260704.md' in text
        assert 'phase6b-real-provider-l1-l4-repeat10-b7-20260704.md' in text
        assert SEQUENCE11_ROOT in text
        assert 'phase6b-l1-l4-launch-request-sequence11-20260704.md' in text
        assert 'phase6b-real-provider-l1-l4-repeat11-b7-20260704.md' in text
        assert SEQUENCE12_ROOT in text
        assert 'phase6b-l1-l4-launch-request-sequence12-20260705.md' in text
        assert 'phase6b-real-provider-l1-l4-repeat12-b7-20260705.md' in text

    for text in (coverage_text, board_text):
        assert SOURCE_REPAIR_JOB in text
        assert SOURCE_REPAIR_REVIEW_JOB in text

    for text in (coverage_text, board_text, evidence_index_text, final_report_text):
        assert 'Phase 6B is claimable' in text
        assert 'initial real-provider' in text
        assert L0_REPEAT6_B7 in text
        assert L5_PARTIAL_REPEAT4_B7 in text
        assert 'production/default enablement' in text
    for text in (coverage_text, board_text, evidence_index_text):
        assert 'phase1-6-acceptance-report-20260705.md' in text
    assert 'phase1-6-acceptance-report-20260705.md' in status_text
    assert 'The active release target is single-lane production closure' in status_text
    assert 'The branch is not production-ready' in status_text
    assert 'single-lane-r1-authority-runtime-closure-20260711.md' in status_text
    assert 'Phase 6B remains unclaimed' not in coverage_text
    assert 'Phase 6B remains unclaimed' not in board_text
    assert 'Phase 6B still needs fresh approval-to-run plus real-provider' not in board_text
    assert final_report_text.startswith('# Phase 1-6 Acceptance Report')

    assert 'Sequence9 is consumed/non-reusable' in _flat(board_text)
    assert 'Sequence9 is consumed/non-reusable' in _flat(coverage_text)
    assert 'no repeat9 evidence is claimable' in _flat(coverage_text)
    assert 'Repeat9 is not claimable' in board_text
    assert 'Closed by talk2 final aggregation on 2026-07-05' in coverage_text
    assert 'reviewer_rework_or_partial_observed=true' in final_report_text
    assert 'Status: pass' in _text(PROJECT_ROOT / SEQUENCE12_B7)
