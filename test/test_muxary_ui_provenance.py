from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "web/src/vendor/agent-elements"
SOURCE = json.loads((VENDOR / "SOURCE.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("relative,record", SOURCE["files"].items())
def test_vendored_source_matches_recorded_hash(relative, record):
    # Offline integrity gate, not independent proof of the upstream's authorship.
    path = (VENDOR / relative).resolve()
    assert path.is_relative_to(VENDOR.resolve())
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest == record["vendored_sha256"]
    assert (digest != record["registry_sha256"]) == bool(record["local_modifications"])
    assert f'/{SOURCE["commit"]}/' in record["registry_url"]
    assert f'/{SOURCE["commit"]}/' in record["upstream_source_url"]


def test_vendor_retains_pinned_source_license_and_modification_boundary():
    assert SOURCE["repository"] == "https://github.com/21st-dev/agent-elements"
    assert SOURCE["commit"] == "b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37"
    assert SOURCE["license"]["spdx"] == "MIT"
    license_bytes = (VENDOR / SOURCE["license"]["path"]).read_bytes()
    assert hashlib.sha256(license_bytes).hexdigest() == SOURCE["license"]["sha256"]
    assert b"Copyright (c) 2026 21st.dev" in license_bytes
    assert {name for name, record in SOURCE["files"].items() if record["local_modifications"]} == {
        "input-bar.tsx", "input/send-button.tsx", "markdown.tsx",
    }
    assert (VENDOR / SOURCE["integration_verification"]["report"]).resolve() == ROOT / "docs/research/muxary-validation.md"
