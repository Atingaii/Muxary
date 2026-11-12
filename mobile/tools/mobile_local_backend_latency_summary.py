#!/usr/bin/env python3
"""Summarize repeated CCB Mobile local-backend probe latency runs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path


STEP_BUDGETS_MS: dict[str, dict[str, float]] = {
    'pairing_claim': {'p50_target_ms': 1500.0, 'hard_cap_ms': 5000.0},
    'project_view': {'p50_target_ms': 500.0, 'hard_cap_ms': 2000.0},
    'message_submit': {'p50_target_ms': 1000.0, 'hard_cap_ms': 5000.0},
    'agent_reply_marker': {'p50_target_ms': 3000.0, 'hard_cap_ms': 15000.0},
    'file_upload_route': {'p50_target_ms': 2000.0, 'hard_cap_ms': 8000.0},
    'file_download_route': {'p50_target_ms': 2000.0, 'hard_cap_ms': 8000.0},
    'backend_artifact_route': {'p50_target_ms': 2000.0, 'hard_cap_ms': 8000.0},
}


def summarize_latency_runs(
    runs: list[dict[str, object]],
    *,
    min_runs: int = 5,
) -> dict[str, object]:
    generated_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    by_step: dict[str, list[dict[str, object]]] = {}
    run_statuses: list[str] = []
    for run in runs:
        run_statuses.append(str(run.get('status') or 'unknown'))
        for step in _as_list(run.get('steps')):
            record = _as_dict(step)
            name = str(record.get('name') or '').strip()
            if name:
                by_step.setdefault(name, []).append(record)

    steps = {
        name: _summarize_step(name, records)
        for name, records in sorted(by_step.items())
    }
    status = _overall_status(run_statuses, steps, min_runs=max(1, int(min_runs)))
    return {
        'schema_version': 1,
        'generated_at': generated_at,
        'status': status,
        'run_count': len(runs),
        'min_runs': max(1, int(min_runs)),
        'run_statuses': run_statuses,
        'steps': steps,
        'budgeted_steps': sorted(STEP_BUDGETS_MS),
    }


def _summarize_step(name: str, records: list[dict[str, object]]) -> dict[str, object]:
    statuses: dict[str, int] = {}
    durations = []
    for record in records:
        status = str(record.get('status') or 'unknown')
        statuses[status] = statuses.get(status, 0) + 1
        if status == 'pass' and isinstance(record.get('duration_ms'), (int, float)):
            durations.append(float(record['duration_ms']))

    summary: dict[str, object] = {
        'samples': len(records),
        'pass_samples': len(durations),
        'statuses': statuses,
    }
    if durations:
        ordered = sorted(durations)
        summary.update(
            {
                'p50_ms': percentile(ordered, 50),
                'p95_ms': percentile(ordered, 95),
                'max_ms': round(max(ordered), 3),
            }
        )
    budget = STEP_BUDGETS_MS.get(name)
    if budget is not None:
        summary.update(budget)
        summary['budget_status'] = _budget_status(summary, budget)
    return summary


def _budget_status(
    summary: dict[str, object],
    budget: dict[str, float],
) -> str:
    if int(summary.get('pass_samples') or 0) == 0:
        return 'no_samples'
    p50 = float(summary.get('p50_ms') or 0)
    maximum = float(summary.get('max_ms') or 0)
    if p50 > budget['p50_target_ms'] or maximum > budget['hard_cap_ms']:
        return 'fail'
    return 'pass'


def _overall_status(
    run_statuses: list[str],
    steps: dict[str, object],
    *,
    min_runs: int,
) -> str:
    if not run_statuses:
        return 'blocked'
    if len(run_statuses) < min_runs:
        return 'blocked'
    if not steps:
        return 'blocked'
    if any(status == 'fail' for status in run_statuses):
        return 'fail'
    if any(status in {'blocked', 'unknown'} for status in run_statuses):
        return 'blocked'
    budget_statuses = {
        name: str(_as_dict(steps.get(name)).get('budget_status') or '')
        for name in STEP_BUDGETS_MS
    }
    if any(not status for status in budget_statuses.values()):
        return 'blocked'
    if any(status == 'fail' for status in budget_statuses.values()):
        return 'fail'
    if any(status == 'no_samples' for status in budget_statuses.values()):
        return 'blocked'
    return 'ok'


def percentile(ordered_values: list[float], percentile_value: float) -> float:
    if not ordered_values:
        raise ValueError('percentile requires at least one value')
    if len(ordered_values) == 1:
        return round(float(ordered_values[0]), 3)
    rank = (len(ordered_values) - 1) * (percentile_value / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(ordered_values) - 1)
    weight = rank - lower
    value = ordered_values[lower] * (1.0 - weight) + ordered_values[upper] * weight
    return round(value, 3)


def load_runs(paths: list[Path]) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding='utf-8'))
        if isinstance(payload, dict) and isinstance(payload.get('runs'), list):
            runs.extend(_normalize_run_payload(item) for item in payload['runs'])
        elif isinstance(payload, dict):
            runs.append(_normalize_run_payload(payload))
        else:
            raise ValueError(f'{path} did not contain a probe JSON object')
    return runs


def _normalize_run_payload(value: object) -> dict[str, object]:
    payload = _as_dict(value)
    probe_json = payload.get('probe_json')
    if isinstance(probe_json, dict):
        return _as_dict(probe_json)
    return payload


def _as_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return {str(key): item for key, item in value.items()}
    return {}


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    return []


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Aggregate repeated mobile local-backend probe latency JSON.',
    )
    parser.add_argument('json_paths', nargs='+', type=Path)
    parser.add_argument(
        '--min-runs',
        type=int,
        default=5,
        help='minimum run count required for an ok summary (default: 5)',
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = summarize_latency_runs(load_runs(args.json_paths), min_runs=args.min_runs)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary['status'] == 'ok' else 1


if __name__ == '__main__':
    raise SystemExit(main())
