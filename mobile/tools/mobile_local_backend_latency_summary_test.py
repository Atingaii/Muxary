#!/usr/bin/env python3
"""Self-tests for repeated local-backend latency summaries."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name('mobile_local_backend_latency_summary.py')
SPEC = importlib.util.spec_from_file_location(
    'mobile_local_backend_latency_summary',
    MODULE_PATH,
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f'could not load {MODULE_PATH}')
SUMMARY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SUMMARY
SPEC.loader.exec_module(SUMMARY)


def run_with_steps(*durations: float, status: str = 'ok') -> dict[str, object]:
    steps = [
        {'name': 'pairing_claim', 'status': 'pass', 'duration_ms': durations[0]},
        {'name': 'project_view', 'status': 'pass', 'duration_ms': durations[1]},
        {'name': 'message_submit', 'status': 'pass', 'duration_ms': durations[2]},
        {'name': 'agent_reply_marker', 'status': 'pass', 'duration_ms': durations[3]},
        {'name': 'file_upload_route', 'status': 'pass', 'duration_ms': durations[4]},
        {'name': 'file_download_route', 'status': 'pass', 'duration_ms': durations[5]},
        {'name': 'backend_artifact_route', 'status': 'pass', 'duration_ms': durations[6]},
    ]
    return {'status': status, 'steps': steps}


class LocalBackendLatencySummaryTest(unittest.TestCase):
    def test_summarizes_repeated_pass_runs(self) -> None:
        summary = SUMMARY.summarize_latency_runs(
            [
                run_with_steps(100, 50, 80, 900, 70, 30, 120),
                run_with_steps(200, 60, 90, 1000, 80, 40, 130),
                run_with_steps(300, 70, 100, 1100, 90, 50, 140),
            ],
            min_runs=3,
        )

        self.assertEqual(summary['status'], 'ok')
        self.assertEqual(summary['run_count'], 3)
        pairing = summary['steps']['pairing_claim']
        self.assertEqual(pairing['samples'], 3)
        self.assertEqual(pairing['pass_samples'], 3)
        self.assertEqual(pairing['p50_ms'], 200.0)
        self.assertEqual(pairing['p95_ms'], 290.0)
        self.assertEqual(pairing['budget_status'], 'pass')

    def test_fails_when_budget_is_exceeded(self) -> None:
        summary = SUMMARY.summarize_latency_runs(
            [run_with_steps(6000, 50, 80, 900, 70, 30, 120)],
            min_runs=1,
        )

        self.assertEqual(summary['status'], 'fail')
        self.assertEqual(
            summary['steps']['pairing_claim']['budget_status'],
            'fail',
        )

    def test_blocked_run_blocks_summary(self) -> None:
        run = run_with_steps(100, 50, 80, 900, 70, 30, 120, status='blocked')
        run['steps'][3] = {
            'name': 'agent_reply_marker',
            'status': 'blocked',
            'duration_ms': 15000,
        }

        summary = SUMMARY.summarize_latency_runs([run], min_runs=1)

        self.assertEqual(summary['status'], 'blocked')
        self.assertEqual(
            summary['steps']['agent_reply_marker']['budget_status'],
            'no_samples',
        )

    def test_load_runs_accepts_wrapper_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'runs.json'
            path.write_text(
                json.dumps({'runs': [run_with_steps(100, 50, 80, 900, 70, 30, 120)]}),
                encoding='utf-8',
            )

            runs = SUMMARY.load_runs([path])

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['status'], 'ok')

    def test_load_runs_unwraps_probe_json_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'probe-wrapper.json'
            path.write_text(
                json.dumps(
                    {
                        'status': 'pass',
                        'probe_json': run_with_steps(100, 50, 80, 900, 70, 30, 120),
                    }
                ),
                encoding='utf-8',
            )

            runs = SUMMARY.load_runs([path])

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]['status'], 'ok')
        self.assertIn('steps', runs[0])

    def test_empty_step_runs_do_not_pass(self) -> None:
        summary = SUMMARY.summarize_latency_runs([{'status': 'ok'}], min_runs=1)

        self.assertEqual(summary['status'], 'blocked')

    def test_default_requires_five_runs(self) -> None:
        summary = SUMMARY.summarize_latency_runs(
            [
                run_with_steps(100, 50, 80, 900, 70, 30, 120),
                run_with_steps(200, 60, 90, 1000, 80, 40, 130),
                run_with_steps(300, 70, 100, 1100, 90, 50, 140),
            ]
        )

        self.assertEqual(summary['status'], 'blocked')
        self.assertEqual(summary['min_runs'], 5)


if __name__ == '__main__':
    unittest.main()
