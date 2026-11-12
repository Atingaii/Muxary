from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'source_fake_runtime_campaign.py'
SCHEMA_ROOT = ROOT / 'scripts' / 'schemas'


def _load_script():
    spec = importlib.util.spec_from_file_location('source_fake_runtime_campaign', SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema(name: str) -> dict[str, object]:
    return json.loads((SCHEMA_ROOT / name).read_text(encoding='utf-8'))


def _report(tmp_path: Path, *, scenario: str, module) -> Path:
    project = tmp_path / f'project-{scenario}'
    project.mkdir()
    evidence_paths = {}
    digests = {}
    for key in ('bundle', 'scheduler_state', 'round', 'integration_state', 'raw_observed'):
        path = project / f'{key}.json'
        path.write_text(json.dumps({'scenario': scenario, 'kind': key}) + '\n', encoding='utf-8')
        evidence_paths[key] = str(path)
        digests[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    report_path = project / 'report.json'
    evidence_paths['report'] = str(report_path)
    outcome = dict(
        zip(
            ('classification', 'task_status', 'round_result', 'round_source'),
            module.SCENARIO_OUTCOMES[scenario],
        )
    )
    requested_count, requested_shape = module.SCENARIO_MATRIX[scenario]
    report = {
        'schema': 'ccb.g5.source_fake_runtime_report.v1',
        'status': 'pass',
        'execution_mode': 'source_fake_runtime',
        'coverage': {
            'provider': 'fake',
            'real_provider': False,
            'live_provider': False,
            'disclaimer': 'fake only',
        },
        'project_root': str(project),
        'project_id': f'project-{scenario}',
        'role_store': str(project / 'roles'),
        'provider': 'fake',
        'scenario': scenario,
        'expected': outcome,
        'observed': dict(outcome),
        'config_version': 3,
        'matrix': {
            'requested_count': requested_count,
            'requested_shape': requested_shape,
        },
        'task_id': 'g5-multi-workgroup-task',
        'loop_id': f'loop-{scenario}',
        'bundle': {'node_count': requested_count},
        'jobs': {},
        'integration': {},
        'task': {'status': outcome['task_status']},
        'round': {'result': outcome['round_result'], 'source': outcome['round_source']},
        'release': {'released_count': 3, 'retained_count': 0},
        'root_changes': {},
        'runner_results': [],
        'execution': {},
        'checks': {'authority': True, 'release': True},
        'paths': evidence_paths,
        'raw_evidence_sha256': digests,
        'command_log': [],
        'external_cleanup': {'returncode': 0},
        'post_cleanup': {
            'owned_processes': [],
            'socket_entries': [],
            'connectable_sockets': [],
            'child_worktrees': [],
        },
    }
    report_path.write_text(json.dumps(report, sort_keys=True) + '\n', encoding='utf-8')
    return report_path


def _all_reports(tmp_path: Path, module) -> list[Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    return [_report(tmp_path, scenario=scenario, module=module) for scenario in module.REQUIRED_SCENARIOS]


def test_campaign_aggregates_ten_explicit_reports_without_mutating_raw(tmp_path: Path) -> None:
    module = _load_script()
    reports = _all_reports(tmp_path, module)
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in reports}
    output = tmp_path / 'campaign'

    campaign = module.aggregate_reports(report_paths=list(reversed(reports)), output_dir=output)

    assert campaign['status'] == 'pass'
    assert campaign['row_count'] == 10
    assert [row['scenario'] for row in campaign['rows']] == sorted(module.REQUIRED_SCENARIOS)
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest for path, digest in before.items())
    assert len((output / 'evidence_rows.jsonl').read_text(encoding='utf-8').splitlines()) == 10
    assert 'no live or real provider coverage' in (output / 'B7.md').read_text(encoding='utf-8')


def test_draft_202012_schemas_validate_normalized_report_rows_and_campaign(tmp_path: Path) -> None:
    module = _load_script()
    reports = _all_reports(tmp_path, module)
    output = tmp_path / 'campaign'
    campaign = module.aggregate_reports(report_paths=reports, output_dir=output)
    report_validator = Draft202012Validator(_schema('source_fake_runtime_report.schema.json'))
    row_validator = Draft202012Validator(_schema('source_fake_runtime_row.schema.json'))
    campaign_validator = Draft202012Validator(_schema('source_fake_runtime_campaign.schema.json'))

    for path in reports:
        report_validator.validate(json.loads(path.read_text(encoding='utf-8')))
    for row in campaign['rows']:
        row_validator.validate(row)
    campaign_validator.validate(campaign)

    missing = json.loads(reports[0].read_text(encoding='utf-8'))
    missing.pop('task_id')
    assert list(report_validator.iter_errors(missing))
    additional = json.loads(reports[0].read_text(encoding='utf-8'))
    additional['unexpected_authority'] = True
    assert list(report_validator.iter_errors(additional))


def test_campaign_rejects_missing_duplicate_digest_and_key_drift(tmp_path: Path) -> None:
    module = _load_script()
    reports = _all_reports(tmp_path, module)
    with pytest.raises(module.CampaignFailure, match='scenario set mismatch'):
        module.aggregate_reports(report_paths=reports[:-1], output_dir=tmp_path / 'missing')
    with pytest.raises(module.CampaignFailure, match='duplicate scenario'):
        module.aggregate_reports(report_paths=[*reports, reports[0]], output_dir=tmp_path / 'duplicate')

    payload = json.loads(reports[0].read_text(encoding='utf-8'))
    Path(payload['paths']['round']).write_text('{}\n', encoding='utf-8')
    with pytest.raises(module.CampaignFailure, match='raw evidence digest mismatch'):
        module.aggregate_reports(report_paths=reports, output_dir=tmp_path / 'digest')

    reports = _all_reports(tmp_path / 'keys', module)
    drifted = json.loads(reports[0].read_text(encoding='utf-8'))
    drifted['unexpected_authority'] = True
    reports[0].write_text(json.dumps(drifted), encoding='utf-8')
    with pytest.raises(module.CampaignFailure, match='report key mismatch'):
        module.aggregate_reports(report_paths=reports, output_dir=tmp_path / 'key-drift')

    reports = _all_reports(tmp_path / 'matrix', module)
    drifted = json.loads(reports[0].read_text(encoding='utf-8'))
    drifted['matrix'] = {'requested_count': 1, 'requested_shape': 'parallel'}
    reports[0].write_text(json.dumps(drifted), encoding='utf-8')
    with pytest.raises(module.CampaignFailure, match='campaign matrix contract mismatch'):
        module.aggregate_reports(report_paths=reports, output_dir=tmp_path / 'matrix-drift')


def test_campaign_rejects_output_under_ccb_authority(tmp_path: Path) -> None:
    module = _load_script()
    reports = _all_reports(tmp_path, module)

    with pytest.raises(module.CampaignFailure, match='outside project .ccb'):
        module.aggregate_reports(report_paths=reports, output_dir=tmp_path / '.ccb' / 'campaign')
