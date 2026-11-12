#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import json
import platform
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import os
import shutil


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = REPO_ROOT / 'lib'
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from rust_helpers import RUST_HELPER_BIN_ENV
from rust_helpers_storage import RUST_STORAGE_SCAN_ENV, RUST_STORAGE_SUMMARY_ENV
from storage.paths import PathLayout
from storage_classification import summarize_storage_compact


SCHEMA_VERSION = 1
DEFAULT_RESULT_PATH = REPO_ROOT / 'dev_tools' / 'perf_results' / 'python_rust_phase12_storage_summary_helper.json'
HELPER_MANIFEST = REPO_ROOT / 'tools' / 'ccb-rs-helper' / 'Cargo.toml'


@dataclass(frozen=True)
class Phase12Options:
    result_path: Path = DEFAULT_RESULT_PATH
    fixture_root: Path | None = None
    files: int = 60_000
    agents: int = 12
    iterations: int = 8
    entries_limit: int = 50
    helper_bin: Path | None = None
    build_helper: bool = True
    keep_fixtures: bool = False


def run_phase12_storage_summary_helper(options: Phase12Options) -> dict[str, Any]:
    fixture_root, cleanup = _fixture_root(options.fixture_root)
    try:
        project_root = fixture_root / 'project'
        layout = PathLayout(project_root)
        _generate_storage_fixture(project_root, files=max(1, options.files), agents=max(1, options.agents))

        helper_bin = options.helper_bin
        build = {'status': 'skipped'}
        if helper_bin is None and options.build_helper:
            build = _build_helper()
            helper_bin = _default_helper_bin()
        if helper_bin is not None and not helper_bin.exists():
            build = {'status': 'missing', 'path': str(helper_bin)}
            helper_bin = None

        baseline_metric = _measure(
            lambda: _compact_with_env(
                layout,
                storage_summary_mode='0',
                storage_scan_mode='auto',
                helper_bin=helper_bin,
                entries_limit=max(0, options.entries_limit),
            ),
            iterations=max(1, options.iterations),
        )
        helper_metric = _skipped('helper_missing')
        helper_used = False
        parity = {'matches_python': False, 'reason': 'helper_missing'}
        if helper_bin is not None:
            helper_metric = _measure(
                lambda: _compact_with_env(
                    layout,
                    storage_summary_mode='1',
                    storage_scan_mode='auto',
                    helper_bin=helper_bin,
                    entries_limit=max(0, options.entries_limit),
                ),
                iterations=max(1, options.iterations),
            )
            baseline_payload = _compact_with_env(
                layout,
                storage_summary_mode='0',
                storage_scan_mode='auto',
                helper_bin=helper_bin,
                entries_limit=max(0, options.entries_limit),
            )
            helper_payload = _compact_with_env(
                layout,
                storage_summary_mode='1',
                storage_scan_mode='auto',
                helper_bin=helper_bin,
                entries_limit=max(0, options.entries_limit),
            )
            parity = _parity_result(baseline_payload, helper_payload)
            helper_used = parity['matches_python'] and helper_metric['status'] == 'measured'
            if not parity['matches_python']:
                helper_metric = _skipped('helper_python_mismatch')

        speedup = None
        if baseline_metric['status'] == 'measured' and helper_metric['status'] == 'measured':
            speedup = baseline_metric['p50_ms'] / helper_metric['p50_ms'] if helper_metric['p50_ms'] else None

        result = {
            'schema_version': SCHEMA_VERSION,
            'plan': 'python-rust-hybrid-performance',
            'phase': 'phase12_storage_summary_helper',
            'generated_at': _utc_now(),
            'repo_root': str(REPO_ROOT),
            'fixture_root': str(fixture_root),
            'result_path': str(options.result_path),
            'parameters': {
                'files': max(1, options.files),
                'agents': max(1, options.agents),
                'iterations': max(1, options.iterations),
                'entries_limit': max(0, options.entries_limit),
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
                'inventory_python_compact_summary': baseline_metric,
                'rust_helper_storage_compact_summary': helper_metric,
            },
            'speedup_p50': speedup,
            'integration_gate': {
                'meets_1_2x_speedup': speedup is not None and speedup >= 1.2,
                'production_path_wired': True,
                'default_enabled': False,
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
        temp = tempfile.TemporaryDirectory(prefix='ccb-phase12-storage-summary-')
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


def _generate_storage_fixture(project_root: Path, *, files: int, agents: int) -> None:
    ccb = project_root / '.ccb'
    _write(ccb / 'ccb.config', 'main:codex\n')
    _write(ccb / 'ccb_memory.md', '# shared memory\n')
    _write(ccb / 'ccbd' / 'state.json', '{}\n')
    for agent_index in range(agents):
        agent = f'agent{agent_index}'
        _write(ccb / 'agents' / agent / 'agent.json', '{}\n')
        _write(ccb / 'agents' / agent / 'runtime.json', '{}\n')
        provider_root = ccb / 'agents' / agent / 'provider-state' / 'codex' / 'home'
        _write(provider_root / 'auth.json', '{}\n')
        _write(provider_root / 'config.toml', '# config\n')

    for index in range(files):
        agent = f'agent{index % agents}'
        bucket = index % 97
        if index % 5 == 0:
            path = ccb / 'agents' / agent / 'provider-state' / 'codex' / 'home' / 'sessions' / f'{bucket}' / f'{index}.jsonl'
        elif index % 5 == 1:
            path = ccb / 'agents' / agent / 'provider-runtime' / 'codex' / f'{bucket}' / f'{index}.tmp'
        elif index % 5 == 2:
            path = ccb / 'shared-cache' / 'codex' / f'{bucket}' / f'{index}.bin'
        elif index % 5 == 3:
            path = ccb / 'workspaces' / agent / f'{bucket}' / f'{index}.txt'
        else:
            path = ccb / 'ccbd' / 'messages' / f'{bucket}' / f'{index}.json'
        _write(path, f'{index}:{"x" * 64}\n')


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _compact_with_env(
    layout: PathLayout,
    *,
    storage_summary_mode: str,
    storage_scan_mode: str,
    helper_bin: Path | None,
    entries_limit: int,
) -> dict[str, object]:
    updates = {
        RUST_STORAGE_SUMMARY_ENV: storage_summary_mode,
        RUST_STORAGE_SCAN_ENV: storage_scan_mode,
    }
    if helper_bin is not None:
        updates[RUST_HELPER_BIN_ENV] = str(helper_bin)
    with _temporary_env(updates):
        return summarize_storage_compact(layout, entries_limit=entries_limit)


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


def _parity_result(baseline_payload: dict[str, object], helper_payload: dict[str, object]) -> dict[str, object]:
    if _stable_compact_summary(baseline_payload) == _stable_compact_summary(helper_payload):
        return {'matches_python': True, 'reason': 'matched'}
    return {
        'matches_python': False,
        'reason': 'summary_mismatch',
        'baseline_total_count': baseline_payload.get('total_count'),
        'helper_total_count': helper_payload.get('total_count'),
        'baseline_total_bytes': baseline_payload.get('total_bytes'),
        'helper_total_bytes': helper_payload.get('total_bytes'),
    }


def _stable_compact_summary(payload: dict[str, object]) -> dict[str, object]:
    stable = dict(payload)
    stable.pop('generated_at', None)
    stable.pop('summary_helper_used', None)
    stable['entries'] = sorted(
        [dict(item) for item in payload.get('entries', []) if isinstance(item, dict)],
        key=lambda item: (str(item.get('relative_path')), str(item.get('path'))),
    )
    return stable


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
    total_count = 0
    total_bytes = 0
    for _ in range(iterations):
        started = time.perf_counter()
        value = call()
        samples.append((time.perf_counter() - started) * 1000)
        total_count = int(value.get('total_count') or 0) if isinstance(value, dict) else 0
        total_bytes = int(value.get('total_bytes') or 0) if isinstance(value, dict) else 0
    return {
        'status': 'measured',
        'iterations': iterations,
        'p50_ms': round(statistics.median(samples), 3),
        'p95_ms': round(_percentile(samples, 0.95), 3),
        'min_ms': round(min(samples), 3),
        'max_ms': round(max(samples), 3),
        'total_count': total_count,
        'total_bytes': total_bytes,
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
    parser = argparse.ArgumentParser(description='Benchmark Phase 12 storage summary helper behavior.')
    parser.add_argument('--result-path', type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument('--fixture-root', type=Path)
    parser.add_argument('--files', type=int, default=60_000)
    parser.add_argument('--agents', type=int, default=12)
    parser.add_argument('--iterations', type=int, default=8)
    parser.add_argument('--entries-limit', type=int, default=50)
    parser.add_argument('--helper-bin', type=Path)
    parser.add_argument('--no-build-helper', action='store_true')
    parser.add_argument('--keep-fixtures', action='store_true')
    args = parser.parse_args(argv)

    result = run_phase12_storage_summary_helper(
        Phase12Options(
            result_path=args.result_path,
            fixture_root=args.fixture_root,
            files=args.files,
            agents=args.agents,
            iterations=args.iterations,
            entries_limit=args.entries_limit,
            helper_bin=args.helper_bin,
            build_helper=not args.no_build_helper,
            keep_fixtures=args.keep_fixtures,
        )
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
