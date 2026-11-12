from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "guarded_dynamic_layout_provider_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("guarded_dynamic_layout_provider_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_guarded_provider_matrix_defaults_to_prepare_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}

    def fake_matrix(**kwargs):
        captured.update(kwargs)
        return {
            "dynamic_layout_smoke_status": "prepared",
            "providers": list(kwargs["providers"]),
            "flows": list(kwargs["flows"]),
            "provider_home_mode": kwargs["provider_home_mode"],
            "resolve_preflight_static_provider": kwargs["resolve_preflight_static_provider"],
            "checks": {"codex": True, "claude": True},
            "provider_results": [],
        }

    monkeypatch.setattr(module.dynamic_layout_smoke, "run_dynamic_layout_provider_matrix", fake_matrix)

    payload = module.run_guarded_provider_matrix_smoke(
        test_root=tmp_path,
        project_prefix="matrix",
        ccb_test=Path(__file__),
    )

    assert payload["dynamic_layout_smoke_status"] == "prepared"
    assert captured["providers"] == ("codex", "claude")
    assert captured["flows"] == ("window-class", "move-agent", "resolve-preflight")
    assert captured["provider_home_mode"] == "real-home"
    assert captured["resolve_preflight_static_provider"] == "fake"
    assert captured["prepare_only"] is True


def test_guarded_provider_matrix_run_requires_real_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv(module.dynamic_layout_smoke.REAL_RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match=module.dynamic_layout_smoke.REAL_RUN_ENV):
        module.run_guarded_provider_matrix_smoke(
            test_root=tmp_path,
            project_prefix="matrix",
            ccb_test=Path(__file__),
            run=True,
        )


def test_guarded_provider_matrix_main_accepts_provider_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return {"dynamic_layout_smoke_status": "prepared", "providers": list(kwargs["providers"]), "provider_results": []}

    monkeypatch.setattr(module, "run_guarded_provider_matrix_smoke", fake_runner)

    assert module.main(
        [
            "--provider",
            "codex",
            "--flow",
            "window-class",
            "--command-timeout",
            "123",
            "--resolve-preflight-static-provider",
            "fake",
        ]
    ) == 0
    assert captured["providers"] == ("codex",)
    assert captured["flows"] == ("window-class",)
    assert captured["command_timeout_s"] == 123
    assert captured["resolve_preflight_static_provider"] == "fake"
    assert captured["run"] is False


def test_tests_workflow_runs_prepare_only_guarded_provider_matrix() -> None:
    text = Path(".github/workflows/test.yml").read_text(encoding="utf-8")

    assert "Guard dynamic layout provider matrix smoke" in text
    assert "scripts/guarded_dynamic_layout_provider_smoke.py" in text
    assert "matrix.os == 'ubuntu-latest' && matrix.python-version == '3.11'" in text
    assert "--project-prefix ci-guarded-dynamic-layout" in text
    assert "--ccb-test \"$GITHUB_WORKSPACE/ccb_test\"" in text
    assert 'payload["dynamic_layout_smoke_status"] == "prepared"' in text
    assert 'payload["providers"] == ["codex", "claude"]' in text
    assert 'payload["flows"] == ["window-class", "move-agent", "resolve-preflight"]' in text
    step = text.split("Guard dynamic layout provider matrix smoke", 1)[1].split("Guard workflow closure layout cleanup smoke", 1)[0]
    assert "--run" not in step
