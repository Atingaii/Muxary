"""Web assets must be built from the archived release source, not local bundles."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("muxary_build_release", ROOT / "scripts/build_release.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _web_source(root: Path, identity: str = "frozen") -> None:
    (root / "web").mkdir(parents=True)
    (root / "web/package.json").write_text(json.dumps({"name": "muxary-workbench", "source": identity}))
    (root / "web/package-lock.json").write_text(json.dumps({"lockfileVersion": 3, "source": identity}))


def _assets(root: Path) -> None:
    assets = root / "assets/workbench"
    (assets / "assets").mkdir(parents=True, exist_ok=True)
    (assets / "index.html").write_text('<script type="module" src="/assets/entry.js"></script><link rel="stylesheet" href="/assets/entry.css">')
    (assets / "assets/entry.js").write_text("// built from frozen source\n")
    (assets / "assets/entry.css").write_text("body{}\n")
    (assets / "THIRD_PARTY_NOTICES.md").write_text("# Bundled dependency licenses\n\nFixture MIT notice.\n")
    (assets / "licenses").mkdir(exist_ok=True)
    for name in ("Apache-2.0.txt", "react-remove-scroll-bar-upstream-MIT.txt", "README.md"):
        (assets / "licenses" / name).write_text(f"Fixture supplementary license: {name}\n")


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def test_archived_ref_builds_and_packages_its_own_assets_not_ignored_worktree_bundle(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    repo = tmp_path / "repo"
    _web_source(repo)
    (repo / ".gitignore").write_text("/assets/workbench/\n")
    _git(repo, "init", "--quiet")
    _git(repo, "config", "user.email", "fixture@example.com")
    _git(repo, "config", "user.name", "Fixture")
    _git(repo, "add", ".")
    _git(repo, "commit", "--quiet", "-m", "frozen web source")
    source_ref = _git(repo, "rev-parse", "HEAD")
    # Keep the checkout clean but different from the explicitly selected ref.
    (repo / "web/package-lock.json").write_text('{"source":"newer-checkout"}')
    _git(repo, "add", "web/package-lock.json")
    _git(repo, "commit", "--quiet", "-m", "newer source")
    _assets(repo)
    (repo / "assets/workbench/assets/entry.js").write_text("// untrusted worktree bundle\n")

    stage = tmp_path / "stage"
    artifact = stage / "ccb-linux-x86_64"
    module.export_release_tree(repo, artifact, git_ref=source_ref, allow_dirty=False)
    assert not (artifact / "assets/workbench").exists()
    calls = []

    def npm(cmd, **kwargs):
        assert kwargs["cwd"] == artifact
        assert json.loads((artifact / "web/package-lock.json").read_text())["source"] == "frozen"
        calls.append(cmd)
        (artifact / "web/node_modules").mkdir(exist_ok=True)
        if cmd[-2:] == ["run", "build"]:
            _assets(artifact)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(module.subprocess, "run", npm)
    module.build_web_workbench_for_release(artifact)
    assert calls == [["npm", "--prefix", "web", "ci"], ["npm", "--prefix", "web", "run", "build"]]
    assert not (artifact / "web/node_modules").exists()
    assert "untrusted" in (repo / "assets/workbench/assets/entry.js").read_text()
    tar_path = tmp_path / "release.tar.gz"
    module.create_tarball(stage_root=stage, artifact_root=artifact, artifact_path=tar_path)
    with tarfile.open(tar_path) as archive:
        names = archive.getnames()
        assert "ccb-linux-x86_64/assets/workbench/index.html" in names
        assert "ccb-linux-x86_64/assets/workbench/assets/entry.css" in names
        notices = archive.extractfile("ccb-linux-x86_64/assets/workbench/THIRD_PARTY_NOTICES.md").read()
        assert notices == b"# Bundled dependency licenses\n\nFixture MIT notice.\n"
        for name in ("Apache-2.0.txt", "react-remove-scroll-bar-upstream-MIT.txt", "README.md"):
            content = archive.extractfile(f"ccb-linux-x86_64/assets/workbench/licenses/{name}").read()
            assert content == f"Fixture supplementary license: {name}\n".encode()
        content = archive.extractfile("ccb-linux-x86_64/assets/workbench/assets/entry.js").read()
        assert content == b"// built from frozen source\n"
        assert not any("node_modules" in name for name in names)


@pytest.mark.parametrize("web_failure", [False, True])
def test_main_builds_web_after_export_and_before_helpers_or_packaging(monkeypatch, tmp_path: Path, web_failure: bool) -> None:
    module = _module()
    args = SimpleNamespace(output_dir=tmp_path / "out", channel=None, allow_dirty=False, git_ref="frozen-ref", release_manifest=None)
    monkeypatch.setattr(module, "parse_args", lambda **kwargs: args)
    monkeypatch.setattr(module, "is_git_checkout", lambda root: True)
    monkeypatch.setattr(module.platform, "system", lambda: "Linux")
    monkeypatch.setattr(module, "resolve_version", lambda root, **kwargs: "0.1.0")
    monkeypatch.setattr(module, "resolve_git_metadata", lambda root, **kwargs: ("commit", "date"))
    monkeypatch.setattr(module, "validate_release_identity", lambda *a, **kw: None)
    monkeypatch.setattr(module, "patch_ccb_metadata", lambda *a, **kw: None)
    monkeypatch.setattr(module, "write_release_metadata", lambda *a, **kw: None)
    monkeypatch.setattr(module, "write_sha256", lambda **kw: None)
    calls = []

    def export(root, dest, **kwargs):
        assert kwargs["git_ref"] == "frozen-ref" and not kwargs["allow_dirty"]
        dest.mkdir(parents=True)
        calls.append("export")

    monkeypatch.setattr(module, "export_release_tree", export)
    def web(*args, **kwargs):
        calls.append("web")
        if web_failure:
            raise RuntimeError("fixture Web build failure")

    monkeypatch.setattr(module, "build_web_workbench_for_release", web)
    for function, label in (("build_sidebar_helper_for_release", "sidebar"), ("build_rs_helper_for_release", "rs"), ("build_runtime_accelerator_for_release", "accelerator")):
        monkeypatch.setattr(module, function, lambda *a, _label=label, **kw: calls.append(_label))
    monkeypatch.setattr(module, "create_tarball", lambda **kw: calls.append("tar"))
    if web_failure:
        with pytest.raises(RuntimeError, match="fixture Web build failure"):
            module.main_for_target("linux")
        assert calls == ["export", "web"]
        return
    assert module.main_for_target("linux") == 0
    assert calls == ["export", "web", "sidebar", "rs", "accelerator", "tar"]


def test_missing_lock_fails_before_any_npm_install(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _web_source(tmp_path)
    (tmp_path / "web/package-lock.json").unlink()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: pytest.fail("must not install without the archived lock"))
    with pytest.raises(RuntimeError, match="package-lock.json"):
        module.build_web_workbench_for_release(tmp_path)


def test_npm_failure_cleans_only_stage_dependencies_and_stops(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _web_source(tmp_path)
    calls = []

    def npm(cmd, **kwargs):
        calls.append(cmd)
        (tmp_path / "web/node_modules").mkdir()
        return SimpleNamespace(returncode=1, stdout="", stderr="fixture ci failure")

    monkeypatch.setattr(module.subprocess, "run", npm)
    with pytest.raises(RuntimeError, match="fixture ci failure"):
        module.build_web_workbench_for_release(tmp_path)
    assert len(calls) == 1
    assert not (tmp_path / "web/node_modules").exists()
    assert (tmp_path / "web/package-lock.json").is_file()


def test_failed_stage_dependency_cleanup_must_not_silently_ship_node_modules(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    _web_source(tmp_path)
    _assets(tmp_path)
    (tmp_path / "web/node_modules").mkdir()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""))
    monkeypatch.setattr(module.shutil, "rmtree", lambda *a, **kw: None)
    with pytest.raises(RuntimeError, match="refusing to package node_modules"):
        module.build_web_workbench_for_release(tmp_path)


@pytest.mark.parametrize("missing", ["index.html", "assets/entry.js", "assets/entry.css"])
def test_successful_npm_exit_does_not_replace_asset_evidence(monkeypatch, tmp_path: Path, missing: str) -> None:
    module = _module()
    _web_source(tmp_path)
    _assets(tmp_path)
    (tmp_path / "assets/workbench" / missing).unlink()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""))
    with pytest.raises(RuntimeError, match="Web.*(?:missing|entry)"):
        module.build_web_workbench_for_release(tmp_path)


@pytest.mark.parametrize("notice_content", [None, "", " \n\t"])
def test_successful_npm_exit_cannot_ship_missing_or_empty_dependency_notices(monkeypatch, tmp_path: Path, notice_content: str | None) -> None:
    module = _module()
    _web_source(tmp_path)
    _assets(tmp_path)
    notices = tmp_path / "assets/workbench/THIRD_PARTY_NOTICES.md"
    if notice_content is None:
        notices.unlink()
    else:
        notices.write_text(notice_content)
    (tmp_path / "web/node_modules").mkdir()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""))
    with pytest.raises(RuntimeError, match="Web.*notices.*(?:missing|empty)"):
        module.build_web_workbench_for_release(tmp_path)
    assert not (tmp_path / "web/node_modules").exists()


@pytest.mark.parametrize("name", ["Apache-2.0.txt", "react-remove-scroll-bar-upstream-MIT.txt", "README.md"])
@pytest.mark.parametrize("content", [None, "", " \n\t"])
def test_successful_npm_exit_cannot_ship_missing_or_empty_supplementary_license(
    monkeypatch, tmp_path: Path, name: str, content: str | None,
) -> None:
    module = _module()
    _web_source(tmp_path)
    _assets(tmp_path)
    license_file = tmp_path / "assets/workbench/licenses" / name
    if content is None:
        license_file.unlink()
    else:
        license_file.write_text(content)
    (tmp_path / "web/node_modules").mkdir()
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""))
    with pytest.raises(RuntimeError, match="Web.*supplementary license.*(?:missing|empty)"):
        module.build_web_workbench_for_release(tmp_path)
    assert not (tmp_path / "web/node_modules").exists()


@pytest.mark.parametrize("old,new", [
    ("/assets/entry.js", "../outside.js"),
    ("/assets/entry.js", "https://example.invalid/entry.js"),
    ("/assets/entry.css", "https://example.invalid/entry.css"),
])
def test_index_rejects_one_external_or_escaped_entry_while_other_assets_stay_valid(monkeypatch, tmp_path: Path, old: str, new: str) -> None:
    module = _module()
    _web_source(tmp_path)
    _assets(tmp_path)
    (tmp_path / "assets/outside.js").write_text("// outside\n")
    index = tmp_path / "assets/workbench/index.html"
    index.write_text(index.read_text().replace(old, new))
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""))
    with pytest.raises(RuntimeError, match="Web.*(?:entry|outside)"):
        module.build_web_workbench_for_release(tmp_path)
