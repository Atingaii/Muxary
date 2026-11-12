from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_runner():
    module_path = Path(__file__).resolve().parents[1] / 'dev_tools' / 'perf_phase7_project_view_recent_jobs_helper.py'
    spec = importlib.util.spec_from_file_location('perf_phase7_project_view_recent_jobs_helper', module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase7_project_view_recent_jobs_benchmark_writes_machine_readable_result(tmp_path: Path) -> None:
    runner = _load_runner()
    result_path = tmp_path / 'results' / 'phase7.json'
    fixture_root = tmp_path / 'fixtures'

    result = runner.run_phase7_project_view_recent_jobs_helper(
        runner.Phase7Options(
            result_path=result_path,
            fixture_root=fixture_root,
            agents=2,
            rows_per_agent=4,
            tail=2,
            result_limit=4,
            iterations=1,
            build_helper=False,
            keep_fixtures=True,
        )
    )

    written = json.loads(result_path.read_text(encoding='utf-8'))
    assert written['schema_version'] == 1
    assert written['phase'] == 'phase7_project_view_recent_jobs_helper'
    assert written['fixture_root'] == str(fixture_root)
    assert written['result_path'] == str(result_path)
    assert written['metrics']['python_project_view_recent_jobs']['status'] == 'measured'
    assert written['metrics']['rust_helper_project_view_recent_jobs']['status'] == 'skipped'
    assert written['integration_gate']['production_path_wired'] is True
    assert written['integration_gate']['python_fallback_removed_when_required'] is True
    assert result['parameters']['agents'] == 2


def test_phase7_project_view_recent_jobs_benchmark_rejects_active_ccb_fixture_root() -> None:
    runner = _load_runner()
    with pytest.raises(ValueError, match='active runtime state'):
        runner.run_phase7_project_view_recent_jobs_helper(
            runner.Phase7Options(
                fixture_root=runner.REPO_ROOT / '.ccb' / 'perf-fixtures',
                iterations=1,
                agents=1,
            )
        )
