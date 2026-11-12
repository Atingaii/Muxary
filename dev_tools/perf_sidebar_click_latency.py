#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = REPO_ROOT / 'lib'
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

from ccbd.socket_client import CcbdClient


SCHEMA_VERSION = 1
DEFAULT_RESULT_PATH = REPO_ROOT / 'dev_tools' / 'perf_results' / 'sidebar_click_latency.json'


@dataclass(frozen=True)
class SidebarClickLatencyOptions:
    socket_path: Path
    mouse_y: int
    pane_top: int
    pane_height: int
    result_path: Path = DEFAULT_RESULT_PATH
    iterations: int = 20
    warmup: int = 3
    timeout_s: float | None = None


def run_sidebar_click_latency(options: SidebarClickLatencyOptions) -> dict[str, Any]:
    client = CcbdClient(options.socket_path, timeout_s=options.timeout_s)
    metric = _measure(
        lambda: client.project_sidebar_click(
            mouse_y=options.mouse_y,
            pane_top=options.pane_top,
            pane_height=options.pane_height,
            schema_version=SCHEMA_VERSION,
        ),
        iterations=max(1, options.iterations),
        warmup=max(0, options.warmup),
    )
    result = {
        'schema_version': SCHEMA_VERSION,
        'phase': 'sidebar_click_latency',
        'generated_at': _utc_now(),
        'repo_root': str(REPO_ROOT),
        'result_path': str(options.result_path),
        'parameters': {
            'socket_path': str(options.socket_path),
            'mouse_y': options.mouse_y,
            'pane_top': options.pane_top,
            'pane_height': options.pane_height,
            'iterations': max(1, options.iterations),
            'warmup': max(0, options.warmup),
            'timeout_s': options.timeout_s,
        },
        'project_sidebar_click': metric,
    }
    _write_json(options.result_path, result)
    return result


def _measure(call: Callable[[], dict], *, iterations: int, warmup: int) -> dict[str, Any]:
    for _ in range(warmup):
        call()

    timings_ms: list[float] = []
    last_payload: dict[str, Any] = {}
    for _ in range(iterations):
        started = time.perf_counter_ns()
        last_payload = call()
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        timings_ms.append(elapsed_ms)

    return {
        'status': 'measured',
        'samples': len(timings_ms),
        'min_ms': min(timings_ms),
        'p50_ms': statistics.median(timings_ms),
        'p95_ms': _percentile(timings_ms, 0.95),
        'max_ms': max(timings_ms),
        'last_target': last_payload.get('target') if isinstance(last_payload, dict) else None,
        'last_focused': last_payload.get('focused') if isinstance(last_payload, dict) else None,
    }


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((len(ordered) - 1) * percentile)))
    return ordered[index]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _parse_args(argv: list[str] | None = None) -> SidebarClickLatencyOptions:
    parser = argparse.ArgumentParser(description='Measure project_sidebar_click RPC latency.')
    parser.add_argument('--socket', required=True, type=Path)
    parser.add_argument('--mouse-y', required=True, type=int)
    parser.add_argument('--pane-top', required=True, type=int)
    parser.add_argument('--pane-height', required=True, type=int)
    parser.add_argument('--result-path', type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument('--iterations', type=int, default=20)
    parser.add_argument('--warmup', type=int, default=3)
    parser.add_argument('--timeout-s', type=float, default=None)
    args = parser.parse_args(argv)
    return SidebarClickLatencyOptions(
        socket_path=args.socket,
        mouse_y=args.mouse_y,
        pane_top=args.pane_top,
        pane_height=args.pane_height,
        result_path=args.result_path,
        iterations=args.iterations,
        warmup=args.warmup,
        timeout_s=args.timeout_s,
    )


def main(argv: list[str] | None = None) -> int:
    result = run_sidebar_click_latency(_parse_args(argv))
    metric = result['project_sidebar_click']
    print(
        'project_sidebar_click '
        f"p50={metric['p50_ms']:.3f}ms "
        f"p95={metric['p95_ms']:.3f}ms "
        f"max={metric['max_ms']:.3f}ms "
        f"target={metric['last_target']}"
    )
    print(result['result_path'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
