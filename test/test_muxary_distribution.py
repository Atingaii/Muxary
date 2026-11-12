from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from cli.management_runtime.versioning_runtime import constants, remote, tags


ROOT = Path(__file__).resolve().parents[1]


def test_muxary_public_package_identity_matches_source_version() -> None:
    manifest = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert manifest["name"] == "@atingaii/muxary"
    version = (ROOT / "VERSION").read_text().strip()
    assert manifest["version"] == version
    assert f'VERSION = "{version}"' in (ROOT / "ccb.py").read_text()
    assert manifest["description"] == "Muxary local web workbench"
    assert manifest["repository"]["url"] == "git+https://github.com/Atingaii/Muxary.git"
    assert manifest["homepage"] == "https://github.com/Atingaii/Muxary#readme"
    assert manifest["bugs"]["url"] == "https://github.com/Atingaii/Muxary/issues"
    assert manifest["bin"]["muxary"] == "bin/muxary.js"
    assert manifest["bin"]["ccb"] == "bin/ccb.js"
    assert "bin/muxary.js" in manifest["files"]


def test_empty_fork_tag_lookup_never_requests_upstream(monkeypatch) -> None:
    requests: list[str] = []

    def fetch(url: str, **_kwargs):
        requests.append(url)
        return []

    def git_run(command, **_kwargs):
        assert command[:3] == ["git", "ls-remote", "--tags"]
        requests.append(command[3])
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(tags, "fetch_json_via_urllib", fetch)
    monkeypatch.setattr(tags, "fetch_json_via_curl", fetch)
    monkeypatch.setattr(tags.shutil, "which", lambda _name: "/git")
    monkeypatch.setattr(tags.subprocess, "run", git_run)

    assert tags.get_available_versions() == []
    assert requests == [
        "https://api.github.com/repos/Atingaii/Muxary/tags",
        "https://api.github.com/repos/Atingaii/Muxary/tags",
        "https://github.com/Atingaii/Muxary",
    ]
    assert constants.REPO_URL == requests[-1]


def test_unavailable_fork_commit_lookup_never_requests_upstream(monkeypatch) -> None:
    requests: list[str] = []

    def fetch(url: str, **_kwargs):
        requests.append(url)
        return None

    monkeypatch.setattr(remote, "fetch_json_via_urllib", fetch)
    monkeypatch.setattr(remote, "fetch_json_via_curl", fetch)

    assert remote.get_remote_version_info() is None
    assert requests == ["https://api.github.com/repos/Atingaii/Muxary/commits/main"] * 2
    assert constants.REMOTE_MAIN_COMMIT_API == requests[0]
