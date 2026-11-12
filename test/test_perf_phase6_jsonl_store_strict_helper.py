from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_runner():
    module_path = Path(__file__).resolve().parents[1] / 'dev_tools' / 'perf_phase6_jsonl_store_strict_helper.py'
    spec = importlib.util.spec_from_file_location('perf_phase6_jsonl_store_strict_helper', module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase6_jsonl_store_benchmark_writes_machine_readable_result(tmp_path: Path) -> None:
    runner = _load_runner()
    result_path = tmp_path / 'results' / 'phase6.json'
    fixture_root = tmp_path / 'fixtures'

    result = runner.run_phase6_jsonl_store_strict_helper(
        runner.Phase6Options(
            result_path=result_path,
            fixture_root=fixture_root,
            agents=2,
            rows_per_agent=4,
            tail=2,
            iterations=1,
            build_helper=False,
            keep_fixtures=True,
        )
    )

    written = json.loads(result_path.read_text(encoding='utf-8'))
    assert written['schema_version'] == 1
    assert written['phase'] == 'phase6_jsonl_store_strict_helper'
    assert written['fixture_root'] == str(fixture_root)
    assert written['result_path'] == str(result_path)
    assert written['metrics']['python_jobstore_batch_tail']['status'] == 'measured'
    assert written['metrics']['rust_helper_jobstore_batch_tail']['status'] == 'skipped'
    assert written['integration_gate']['production_path_wired'] is True
    assert written['integration_gate']['python_fallback_removed_when_required'] is True
    assert result['parameters']['agents'] == 2


def test_phase6_jsonl_store_benchmark_rejects_active_ccb_fixture_root() -> None:
    runner = _load_runner()
    with pytest.raises(ValueError, match='active runtime state'):
        runner.run_phase6_jsonl_store_strict_helper(
            runner.Phase6Options(
                fixture_root=runner.REPO_ROOT / '.ccb' / 'perf-fixtures',
                iterations=1,
                agents=1,
            )
        )
