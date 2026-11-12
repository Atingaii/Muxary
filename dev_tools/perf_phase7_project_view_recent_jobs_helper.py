#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = REPO_ROOT / 'lib'
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from jobs.store import JobStore
from rust_helpers import RUST_HELPER_BIN_ENV
from storage.paths import PathLayout


SCHEMA_VERSION = 1
DEFAULT_RESULT_PATH = REPO_ROOT / 'dev_tools' / 'perf_results' / 'python_rust_phase7_project_view_recent_jobs_helper.json'
HELPER_MANIFEST = REPO_ROOT / 'tools' / 'ccb-rs-helper' / 'Cargo.toml'
RECENT_STATUSES = ('completed', 'cancelled', 'failed', 'incomplete')


@dataclass(frozen=True)
class Phase7Options:
    result_path: Path = DEFAULT_RESULT_PATH
    fixture_root: Path | None = None
    agents: int = 128
    rows_per_agent: int = 2_000
    tail: int = 128
    initial_tail: int | None = None
    result_limit: int = 64
    iterations: int = 8
    helper_bin: Path | None = None
    build_helper: bool = True
    keep_fixtures: bool = False


def run_phase7_project_view_recent_jobs_helper(options: Phase7Options) -> dict[str, Any]:
    fixture_root, cleanup = _fixture_root(options.fixture_root)
    try:
        project_root = fixture_root / 'project'
        layout = PathLayout(project_root)
        store = JobStore(layout)
        agent_names = tuple(f'agent{index}' for index in range(max(1, options.agents)))
        _generate_jobs(store, agent_names=agent_names, rows_per_agent=max(1, options.rows_per_agent))

        helper_bin = options.helper_bin
        build = {'status': 'skipped'}
        if helper_bin is None and options.build_helper:
            build = _build_helper()
            helper_bin = _default_helper_bin()
        if helper_bin is not None and not helper_bin.exists():
            build = {'status': 'missing', 'path': str(helper_bin)}
            helper_bin = None

        python_metric = _measure(
            lambda: _summary_signature(
                store.list_project_view_recent_jobs(
                    agent_names,
                    per_agent_limit=max(0, options.tail),
                    per_agent_initial_limit=_initial_tail(options),
                    result_limit=max(0, options.result_limit),
                    statuses=RECENT_STATUSES,
                )
            ),
            iterations=max(1, options.iterations),
        )
        helper_metric = _skipped('helper_missing')
        helper_used = False
        parity = {'matches_python': False, 'reason': 'helper_missing'}
        if helper_bin is not None:
            helper_metric = _measure(
                lambda: _read_with_helper(
                    store,
                    agent_names,
                    per_agent_limit=max(0, options.tail),
                    per_agent_initial_limit=_initial_tail(options),
                    result_limit=max(0, options.result_limit),
                    helper_bin=helper_bin,
                ),
                iterations=max(1, options.iterations),
            )
            python_value = _summary_signature(
                store.list_project_view_recent_jobs(
                    agent_names,
                    per_agent_limit=max(0, options.tail),
                    per_agent_initial_limit=_initial_tail(options),
                    result_limit=max(0, options.result_limit),
                    statuses=RECENT_STATUSES,
                )
            )
            helper_value = _read_with_helper(
                store,
                agent_names,
                per_agent_limit=max(0, options.tail),
                per_agent_initial_limit=_initial_tail(options),
                result_limit=max(0, options.result_limit),
                helper_bin=helper_bin,
            )
            parity = {'matches_python': helper_value == python_value, 'reason': 'matched' if helper_value == python_value else 'mismatch'}
            helper_used = parity['matches_python'] and helper_metric['status'] == 'measured'
            if not parity['matches_python']:
                helper_metric = _skipped('helper_python_mismatch')

        speedup = None
        p95_reduction = None
        if python_metric['status'] == 'measured' and helper_metric['status'] == 'measured':
            speedup = python_metric['p50_ms'] / helper_metric['p50_ms'] if helper_metric['p50_ms'] else None
            p95_reduction = (
                (python_metric['p95_ms'] - helper_metric['p95_ms']) / python_metric['p95_ms']
                if python_metric['p95_ms']
                else None
            )

        result = {
            'schema_version': SCHEMA_VERSION,
            'plan': 'python-rust-hybrid-performance',
            'phase': 'phase7_project_view_recent_jobs_helper',
            'generated_at': _utc_now(),
            'repo_root': str(REPO_ROOT),
            'fixture_root': str(fixture_root),
            'result_path': str(options.result_path),
            'parameters': {
                'agents': max(1, options.agents),
                'rows_per_agent': max(1, options.rows_per_agent),
                'tail': max(0, options.tail),
                'initial_tail': _initial_tail(options),
                'result_limit': max(0, options.result_limit),
                'iterations': max(1, options.iterations),
            },
            'python': {
                'version': platform.python_version(),
                'executable': sys.executable,
            },
            'platform': {
                'system': platform.system(),
                'release': platform.release(),
                'machine': platform.machine(),
            },
            'helper_build': build,
            'helper_bin': str(helper_bin) if helper_bin is not None else None,
            'helper_used': helper_used,
            'parity': parity,
            'metrics': {
                'python_project_view_recent_jobs': python_metric,
                'rust_helper_project_view_recent_jobs': helper_metric,
            },
            'speedup_p50': speedup,
            'p95_reduction': p95_reduction,
            'integration_gate': {
                'meets_1_5x_speedup': speedup is not None and speedup >= 1.5,
                'meets_20pct_p95_reduction': p95_reduction is not None and p95_reduction >= 0.20,
                'production_path_wired': True,
                'default_enabled': False,
                'python_fallback_removed_when_required': True,
            },
        }
        options.result_path.parent.mkdir(parents=True, exist_ok=True)
        options.result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        return result
    finally:
        if cleanup is not None and not options.keep_fixtures:
            cleanup.cleanup()


def _fixture_root(requested: Path | None) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    if requested is None:
        temp = tempfile.TemporaryDirectory(prefix='ccb-phase7-project-view-jobs-')
        return Path(temp.name), temp
    root = requested.expanduser()
    _reject_active_runtime_fixture_root(root)
    root.mkdir(parents=True, exist_ok=True)
    return root, None


def _reject_active_runtime_fixture_root(root: Path) -> None:
    active_ccb = (REPO_ROOT / '.ccb').resolve()
    try:
        resolved = root.resolve()
    except Exception:
        resolved = root.absolute()
    if resolved == active_ccb or active_ccb in resolved.parents:
        raise ValueError(f'fixture root must not be inside active runtime state: {active_ccb}')


def _generate_jobs(store: JobStore, *, agent_names: tuple[str, ...], rows_per_agent: int) -> None:
    statuses = (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.INCOMPLETE)
    for agent_name in agent_names:
        for index in range(rows_per_agent):
            status = statuses[index % len(statuses)]
            store.append(
                JobRecord(
                    job_id=f'{agent_name}-job-{index}',
                    submission_id=None,
                    agent_name=agent_name,
                    provider='codex',
                    request=MessageEnvelope(
                        project_id='proj-1',
                        to_agent=agent_name,
                        from_actor='cmd' if index % 3 else 'agent0',
                        body=f'project view recent job {agent_name} {index}',
                        task_id=None,
                        reply_to=None,
                        message_type='ask',
                        delivery_scope=DeliveryScope.SINGLE,
                        silence_on_success=index % 11 == 0,
                    ),
                    status=status,
                    terminal_decision={'reason': status.value if status is not JobStatus.COMPLETED else 'task_complete'},
                    cancel_requested_at=None,
                    created_at='2026-06-15T00:00:00Z',
                    updated_at=f'2026-06-15T{(index // 3600) % 24:02d}:{(index // 60) % 60:02d}:{index % 60:02d}Z',
                )
            )


def _read_with_helper(
    store: JobStore,
    agent_names: tuple[str, ...],
    *,
    per_agent_limit: int,
    per_agent_initial_limit: int | None,
    result_limit: int,
    helper_bin: Path,
) -> tuple[tuple[str, str, str, str], ...]:
    with _temporary_env({'CCB_RUST_PROJECT_VIEW_RECENT_JOBS': '1', RUST_HELPER_BIN_ENV: str(helper_bin)}):
        return _summary_signature(
            store.list_project_view_recent_jobs(
                agent_names,
                per_agent_limit=per_agent_limit,
                per_agent_initial_limit=per_agent_initial_limit,
                result_limit=result_limit,
                statuses=RECENT_STATUSES,
            )
        )


def _initial_tail(options: Phase7Options) -> int | None:
    if options.initial_tail is None:
        return None
    return max(0, options.initial_tail)


def _summary_signature(records) -> tuple[tuple[str, str, str, str], ...]:
    return tuple(
        (
            str(record.job_id),
            str(record.status.value),
            str(record.updated_at),
            str(record.request.body),
        )
        for record in records
    )


@contextlib.contextmanager
def _temporary_env(updates: dict[str, str]) -> Iterator[None]:
    old: dict[str, str | None] = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            os.environ[key] = value
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _build_helper() -> dict[str, object]:
    cargo = shutil.which('cargo')
    if cargo is None:
        return {'status': 'missing_cargo'}
    started = time.perf_counter()
    completed = subprocess.run(
        [cargo, 'build', '--release', '--manifest-path', str(HELPER_MANIFEST)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=120,
    )
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    if completed.returncode != 0:
        return {'status': 'failed', 'elapsed_ms': elapsed_ms, 'stderr_chars': len(completed.stderr or '')}
    return {'status': 'built', 'elapsed_ms': elapsed_ms}


def _default_helper_bin() -> Path:
    suffix = '.exe' if platform.system().lower() == 'windows' else ''
    return HELPER_MANIFEST.parent / 'target' / 'release' / f'ccb-rs-helper{suffix}'


def _measure(call, *, iterations: int) -> dict[str, object]:
    samples: list[float] = []
    job_count = 0
    for _ in range(iterations):
        started = time.perf_counter()
        value = call()
        samples.append((time.perf_counter() - started) * 1000)
        if isinstance(value, tuple):
            job_count = len(value)
    return {
        'status': 'measured',
        'iterations': iterations,
        'p50_ms': round(statistics.median(samples), 3),
        'p95_ms': round(_percentile(samples, 0.95), 3),
        'min_ms': round(min(samples), 3),
        'max_ms': round(max(samples), 3),
        'job_count': job_count,
    }


def _percentile(samples: list[float], percentile: float) -> float:
    if len(samples) == 1:
        return samples[0]
    ordered = sorted(samples)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _skipped(reason: str) -> dict[str, object]:
    return {'status': 'skipped', 'reason': reason}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Benchmark Phase 7 ProjectView recent-job summary helper behavior.')
    parser.add_argument('--result-path', type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument('--fixture-root', type=Path)
    parser.add_argument('--agents', type=int, default=128)
    parser.add_argument('--rows-per-agent', type=int, default=2_000)
    parser.add_argument('--tail', type=int, default=128)
    parser.add_argument('--initial-tail', type=int)
    parser.add_argument('--result-limit', type=int, default=64)
    parser.add_argument('--iterations', type=int, default=8)
    parser.add_argument('--helper-bin', type=Path)
    parser.add_argument('--no-build-helper', action='store_true')
    parser.add_argument('--keep-fixtures', action='store_true')
    args = parser.parse_args(argv)

    result = run_phase7_project_view_recent_jobs_helper(
        Phase7Options(
            result_path=args.result_path,
            fixture_root=args.fixture_root,
            agents=args.agents,
            rows_per_agent=args.rows_per_agent,
            tail=args.tail,
            initial_tail=args.initial_tail,
            result_limit=args.result_limit,
            iterations=args.iterations,
            helper_bin=args.helper_bin,
            build_helper=not args.no_build_helper,
            keep_fixtures=args.keep_fixtures,
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
