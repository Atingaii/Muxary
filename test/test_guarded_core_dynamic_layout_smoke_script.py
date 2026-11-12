from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "guarded_core_dynamic_layout_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("guarded_core_dynamic_layout_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _complete_payload(module, *, flows: tuple[str, ...] | None = None) -> dict[str, object]:
    selected_flows = flows or module.DEFAULT_FLOWS
    return {
        "dynamic_layout_smoke_status": "ok",
        "flows": list(selected_flows),
        "checks": {name: True for name in module.REQUIRED_TOP_CHECKS},
        "results": [
            {
                "flow": flow,
                "flow_status": "ok",
                "checks": {name: True for name in checks},
                "commands": [],
            }
            for flow, checks in module.REQUIRED_FLOW_CHECKS.items()
        ],
    }


def test_validate_core_dynamic_layout_payload_accepts_complete_bundle() -> None:
    module = _load_module()

    module.validate_core_dynamic_layout_payload(_complete_payload(module))


def test_validate_core_dynamic_layout_payload_rejects_missing_flow_check() -> None:
    module = _load_module()
    payload = _complete_payload(module)
    result = next(item for item in payload["results"] if item["flow"] == "mixed_move_add_explicit_windows")
    result["checks"].pop("new_beta_pane_created")

    with pytest.raises(AssertionError, match="mixed_move_add_explicit_windows"):
        module.validate_core_dynamic_layout_payload(payload)


def test_validate_core_dynamic_layout_payload_rejects_failed_top_check() -> None:
    module = _load_module()
    payload = _complete_payload(module)
    payload["checks"]["resolve_preflight_chain"] = False

    with pytest.raises(AssertionError, match="top-level dynamic layout checks failed"):
        module.validate_core_dynamic_layout_payload(payload)


def test_guarded_core_dynamic_layout_smoke_defaults_to_fake_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}
    payload = _complete_payload(module)

    def fake_smoke(**kwargs):
        captured.update(kwargs)
        return payload

    monkeypatch.setattr(module.dynamic_layout_smoke, "run_dynamic_layout_smoke", fake_smoke)
    monkeypatch.setattr(module.dynamic_layout_smoke, "compact_smoke_payload", lambda value: value)

    result = module.run_guarded_core_dynamic_layout_smoke(
        test_root=tmp_path,
        project_prefix="core",
        ccb_test=Path(__file__),
    )

    assert result["dynamic_layout_smoke_status"] == "ok"
    assert captured["provider"] == "fake"
    assert captured["flows"] == module.DEFAULT_FLOWS
    assert captured["provider_home_mode"] == "source-home"
    assert captured["prepare_only"] is False
    assert captured["keep_running"] is False


def test_guarded_core_dynamic_layout_smoke_non_fake_requires_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    monkeypatch.delenv(module.dynamic_layout_smoke.REAL_RUN_ENV, raising=False)

    with pytest.raises(RuntimeError, match=module.dynamic_layout_smoke.REAL_RUN_ENV):
        module.run_guarded_core_dynamic_layout_smoke(
            test_root=tmp_path,
            project_prefix="core",
            ccb_test=Path(__file__),
            provider="codex",
        )


def test_guarded_core_dynamic_layout_main_accepts_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return {"dynamic_layout_smoke_status": "ok", "flows": ["same-window-continuous"]}

    monkeypatch.setattr(module, "run_guarded_core_dynamic_layout_smoke", fake_runner)

    assert module.main(
        [
            "--provider",
            "fake",
            "--flow",
            "same-window-continuous",
            "--command-timeout",
            "123",
            "--reset",
        ]
    ) == 0
    assert captured["provider"] == "fake"
    assert captured["flows"] == ("same-window-continuous",)
    assert captured["command_timeout_s"] == 123
    assert captured["reset"] is True
