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

from rust_helpers_project_view import RUST_PROJECT_VIEW_ENV, parse_tmux_project_view_outputs


SCHEMA_VERSION = 1
DEFAULT_RESULT_PATH = REPO_ROOT / 'dev_tools' / 'perf_results' / 'python_rust_phase5_project_view_tmux_helper.json'
HELPER_MANIFEST = REPO_ROOT / 'tools' / 'ccb-rs-helper' / 'Cargo.toml'


@dataclass(frozen=True)
class Phase5Options:
    result_path: Path = DEFAULT_RESULT_PATH
    fixture_root: Path | None = None
    windows: int = 500
    panes: int = 400_000
    iterations: int = 6
    helper_bin: Path | None = None
    build_helper: bool = True
    keep_fixtures: bool = False


def run_phase5_project_view_tmux_helper(options: Phase5Options) -> dict[str, Any]:
    fixture_root, cleanup = _fixture_root(options.fixture_root)
    try:
        fixture = _generate_tmux_fixture(
            windows=max(1, options.windows),
            panes=max(1, options.panes),
            session_name='ccb-perf',
            project_id='proj-perf',
        )

        helper_bin = options.helper_bin
        build = {'status': 'skipped'}
        if helper_bin is None and options.build_helper:
            build = _build_helper()
            helper_bin = _default_helper_bin()
        if helper_bin is not None and not helper_bin.exists():
            build = {'status': 'missing', 'path': str(helper_bin)}
            helper_bin = None

        python_metric = _measure(
            lambda: _parse_fixture(fixture, mode='0', helper_bin=None),
            iterations=max(1, options.iterations),
        )
        helper_metric = _skipped('helper_missing')
        helper_used = False
        parity = {'matches_python': False, 'reason': 'helper_missing'}
        if helper_bin is not None:
            helper_metric = _measure(
                lambda: _parse_fixture(fixture, mode='1', helper_bin=helper_bin),
                iterations=max(1, options.iterations),
            )
            python_payload = _parse_fixture(fixture, mode='0', helper_bin=None)
            helper_probe = parse_tmux_project_view_outputs(
                **fixture,
                env={RUST_PROJECT_VIEW_ENV: '1'},
                helper_bin=helper_bin,
                timeout_s=10.0,
            )
            helper_payload = helper_probe.value
            helper_used = helper_probe.helper_used
            parity = {'matches_python': helper_payload == python_payload, 'reason': 'matched' if helper_payload == python_payload else 'mismatch'}
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
            'phase': 'phase5_project_view_tmux_helper',
            'generated_at': _utc_now(),
            'repo_root': str(REPO_ROOT),
            'fixture_root': str(fixture_root),
            'result_path': str(options.result_path),
            'parameters': {
                'windows': max(1, options.windows),
                'panes': max(1, options.panes),
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
                'python_tmux_parser': python_metric,
                'rust_helper_tmux_parser': helper_metric,
            },
            'speedup_p50': speedup,
            'p95_reduction': p95_reduction,
            'integration_gate': {
                'meets_1_5x_speedup': speedup is not None and speedup >= 1.5,
                'meets_20pct_p95_reduction': p95_reduction is not None and p95_reduction >= 0.20,
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
        temp = tempfile.TemporaryDirectory(prefix='ccb-phase5-project-view-')
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


def _generate_tmux_fixture(*, windows: int, panes: int, session_name: str, project_id: str) -> dict[str, str]:
    focus_stdout = f'win-{windows - 1}\t%{panes}\tagent\tagent-{windows - 1}\n'
    windows_stdout = ''.join(f'win-{index}\t@{index}\t{index}\n' for index in range(windows))
    sidebars: list[str] = []
    for index in range(panes):
        window = f'win-{index % windows}'
        role = 'sidebar' if index < windows else 'agent'
        pane_project = project_id if index % 3 else 'other-project'
        session = session_name if index % 5 else 'other-session'
        sidebar_instance = window if role == 'sidebar' else ''
        sidebars.append(
            f'{session}\t{window}\t%{index}\t{pane_project}\t{role}\t{sidebar_instance}\t{window}\n'
        )
    return {
        'focus_stdout': focus_stdout,
        'windows_stdout': windows_stdout,
        'sidebars_stdout': ''.join(sidebars),
        'session_name': session_name,
        'project_id': project_id,
    }


def _parse_fixture(fixture: dict[str, str], *, mode: str, helper_bin: Path | None) -> dict[str, object]:
    return parse_tmux_project_view_outputs(
        **fixture,
        env={RUST_PROJECT_VIEW_ENV: mode},
        helper_bin=helper_bin,
        timeout_s=10.0,
    ).value


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
    window_count = 0
    sidebar_count = 0
    for _ in range(iterations):
        started = time.perf_counter()
        value = call()
        samples.append((time.perf_counter() - started) * 1000)
        if isinstance(value, dict):
            windows = value.get('windows')
            sidebars = value.get('sidebars')
            window_count = len(windows) if isinstance(windows, dict) else 0
            sidebar_count = len(sidebars) if isinstance(sidebars, dict) else 0
    return {
        'status': 'measured',
        'iterations': iterations,
        'p50_ms': round(statistics.median(samples), 3),
        'p95_ms': round(_percentile(samples, 0.95), 3),
        'min_ms': round(min(samples), 3),
        'max_ms': round(max(samples), 3),
        'window_count': window_count,
        'sidebar_count': sidebar_count,
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
    parser = argparse.ArgumentParser(description='Benchmark Phase 5 ProjectView tmux parser helper behavior.')
    parser.add_argument('--result-path', type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument('--fixture-root', type=Path)
    parser.add_argument('--windows', type=int, default=500)
    parser.add_argument('--panes', type=int, default=400_000)
    parser.add_argument('--iterations', type=int, default=6)
    parser.add_argument('--helper-bin', type=Path)
    parser.add_argument('--no-build-helper', action='store_true')
    parser.add_argument('--keep-fixtures', action='store_true')
    args = parser.parse_args(argv)

    result = run_phase5_project_view_tmux_helper(
        Phase5Options(
            result_path=args.result_path,
            fixture_root=args.fixture_root,
            windows=args.windows,
            panes=args.panes,
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
