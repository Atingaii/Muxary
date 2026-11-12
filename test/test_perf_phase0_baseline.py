from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_runner():
    module_path = Path(__file__).resolve().parents[1] / "dev_tools" / "perf_phase0_baseline.py"
    spec = importlib.util.spec_from_file_location("perf_phase0_baseline", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_phase0_baseline_writes_machine_readable_result(tmp_path: Path) -> None:
    runner = _load_runner()
    result_path = tmp_path / "results" / "baseline.json"
    fixture_root = tmp_path / "fixtures"

    result = runner.run_phase0_baseline(
        runner.Phase0Options(
            result_path=result_path,
            fixture_root=fixture_root,
            iterations=1,
            rows=24,
            agents=2,
            processes=8,
            keep_fixtures=True,
        )
    )

    written = json.loads(result_path.read_text(encoding="utf-8"))
    assert written["schema_version"] == 1
    assert written["phase"] == "phase0_baseline"
    assert written["fixture_root"] == str(fixture_root)
    assert written["result_path"] == str(result_path)
    assert set(written["metrics"]) == {
        "project_view_build",
        "queue_watch_jsonl_tail",
        "storage_classification_scan",
        "native_provider_output_parse",
        "cleanup_process_inspection",
        "helper_subprocess_startup",
    }
    assert written["metrics"]["queue_watch_jsonl_tail"]["status"] == "measured"
    assert written["metrics"]["helper_subprocess_startup"]["details"]["command_kind"] == "python_empty_process"
    assert written["rust_toolchain"]["cargo"]["status"] in {"available", "missing", "error"}
    assert result["metrics"]["native_provider_output_parse"]["details"]["finished"] is True


def test_phase0_baseline_rejects_active_ccb_fixture_root() -> None:
    runner = _load_runner()
    with pytest.raises(ValueError, match="active runtime state"):
        runner.run_phase0_baseline(
            runner.Phase0Options(
                fixture_root=runner.REPO_ROOT / ".ccb" / "perf-fixtures",
                iterations=1,
                rows=1,
            )
        )
