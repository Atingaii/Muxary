#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
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
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = REPO_ROOT / 'lib'
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from rust_helpers_jsonl import RUST_JSONL_ENV, read_jsonl_tail_batch


SCHEMA_VERSION = 1
DEFAULT_RESULT_PATH = REPO_ROOT / 'dev_tools' / 'perf_results' / 'python_rust_phase2_jsonl_helper.json'
HELPER_MANIFEST = REPO_ROOT / 'tools' / 'ccb-rs-helper' / 'Cargo.toml'


@dataclass(frozen=True)
class Phase2Options:
    result_path: Path = DEFAULT_RESULT_PATH
    fixture_root: Path | None = None
    rows: int = 50_000
    files: int = 4
    tail: int = 128
    iterations: int = 12
    helper_bin: Path | None = None
    build_helper: bool = True
    keep_fixtures: bool = False


def run_phase2_jsonl_helper(options: Phase2Options) -> dict[str, Any]:
    fixture_root, cleanup = _fixture_root(options.fixture_root)
    try:
        files = _generate_fixtures(fixture_root, rows=max(50_000, options.rows), files=max(1, options.files))
        requests = [
            {'id': f'file-{index}', 'path': str(path), 'n': max(0, options.tail)}
            for index, path in enumerate(files)
        ]

        helper_bin = options.helper_bin
        build = {'status': 'skipped'}
        if helper_bin is None and options.build_helper:
            build = _build_helper()
            helper_bin = _default_helper_bin()
        if helper_bin is not None and not helper_bin.exists():
            build = {'status': 'missing', 'path': str(helper_bin)}
            helper_bin = None

        python_metric = _measure(
            lambda: read_jsonl_tail_batch(requests, env={RUST_JSONL_ENV: '0'}).value,
            iterations=max(1, options.iterations),
        )
        helper_metric = _skipped('helper_missing')
        helper_used = False
        if helper_bin is not None:
            helper_metric = _measure(
                lambda: read_jsonl_tail_batch(
                    requests,
                    env={RUST_JSONL_ENV: '1'},
                    helper_bin=helper_bin,
                    timeout_s=5.0,
                ).value,
                iterations=max(1, options.iterations),
            )
            helper_probe = read_jsonl_tail_batch(
                requests,
                env={RUST_JSONL_ENV: '1'},
                helper_bin=helper_bin,
                timeout_s=5.0,
            )
            helper_used = helper_probe.helper_used
            if helper_probe.value != read_jsonl_tail_batch(requests, env={RUST_JSONL_ENV: '0'}).value:
                helper_metric = _skipped('helper_python_mismatch')

        speedup = None
        if python_metric['status'] == 'measured' and helper_metric['status'] == 'measured':
            speedup = python_metric['p50_ms'] / helper_metric['p50_ms'] if helper_metric['p50_ms'] else None

        result = {
            'schema_version': SCHEMA_VERSION,
            'plan': 'python-rust-hybrid-performance',
            'phase': 'phase2_jsonl_helper',
            'generated_at': _utc_now(),
            'repo_root': str(REPO_ROOT),
            'fixture_root': str(fixture_root),
            'result_path': str(options.result_path),
            'parameters': {
                'rows_per_file': max(50_000, options.rows),
                'files': max(1, options.files),
                'tail': max(0, options.tail),
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
            'metrics': {
                'python_fallback_batch_tail': python_metric,
                'rust_helper_batch_tail': helper_metric,
            },
            'speedup_p50': speedup,
            'integration_gate': {
                'meets_2x_speedup': speedup is not None and speedup >= 2.0,
                'production_path_wired': False,
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
        temp = tempfile.TemporaryDirectory(prefix='ccb-phase2-jsonl-')
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


def _generate_fixtures(root: Path, *, rows: int, files: int) -> list[Path]:
    root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for file_index in range(files):
        path = root / f'events-{file_index}.jsonl'
        paths.append(path)
        with path.open('w', encoding='utf-8') as handle:
            for row_index in range(rows):
                handle.write(
                    json.dumps(
                        {
                            'file': file_index,
                            'seq': row_index,
                            'agent': f'agent{row_index % 8}',
                            'status': 'done' if row_index % 5 else 'running',
                            'payload': 'x' * 96,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    + '\n'
                )
    return paths


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
    row_count = 0
    for _ in range(iterations):
        started = time.perf_counter()
        value = call()
        samples.append((time.perf_counter() - started) * 1000)
        row_count = _row_count(value)
    return {
        'status': 'measured',
        'iterations': iterations,
        'p50_ms': round(statistics.median(samples), 3),
        'p95_ms': round(_percentile(samples, 0.95), 3),
        'min_ms': round(min(samples), 3),
        'max_ms': round(max(samples), 3),
        'rows_returned': row_count,
    }


def _row_count(value: object) -> int:
    if not isinstance(value, dict) or not isinstance(value.get('requests'), list):
        return 0
    total = 0
    for request in value['requests']:
        if isinstance(request, dict) and isinstance(request.get('rows'), list):
            total += len(request['rows'])
    return total


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
    parser = argparse.ArgumentParser(description='Benchmark Phase 2 JSONL helper batch tail behavior.')
    parser.add_argument('--result-path', type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument('--fixture-root', type=Path)
    parser.add_argument('--rows', type=int, default=50_000)
    parser.add_argument('--files', type=int, default=4)
    parser.add_argument('--tail', type=int, default=128)
    parser.add_argument('--iterations', type=int, default=12)
    parser.add_argument('--helper-bin', type=Path)
    parser.add_argument('--no-build-helper', action='store_true')
    parser.add_argument('--keep-fixtures', action='store_true')
    args = parser.parse_args(argv)

    result = run_phase2_jsonl_helper(
        Phase2Options(
            result_path=args.result_path,
            fixture_root=args.fixture_root,
            rows=args.rows,
            files=args.files,
            tail=args.tail,
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
