"""Separate current fork claims from the retained, credited upstream archive."""
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_BASELINE_VERSION = "8.7.22"
HISTORY_MARKER = "<!-- muxary-upstream-history -->"


def test_current_fork_package_versions_match_source() -> None:
    version = (ROOT / "VERSION").read_text().strip()
    manifest = json.loads((ROOT / "package.json").read_text())

    assert manifest["name"] == "@atingaii/muxary"
    assert manifest["version"] == version
    assert f'VERSION = "{version}"' in (ROOT / "ccb.py").read_text()
    notes = (ROOT / "docs/releases" / f"v{version}.md").read_text()
    assert "## English" in notes and "## 中文" in notes


def test_current_readmes_describe_source_fork_without_inventing_published_artifacts() -> None:
    version = (ROOT / "VERSION").read_text().strip()
    for readme in (ROOT / "README.md", ROOT / "README/zh.md"):
        content = readme.read_text()
        assert HISTORY_MARKER in content, str(readme)
        current, _history = content.split(HISTORY_MARKER, 1)
        assert "Muxary" in current and version in current, str(readme)
        assert "Atingaii/Muxary" in current, str(readme)
        assert UPSTREAM_BASELINE_VERSION in current, str(readme)
        assert "muxary" in current and "install.sh" in current, str(readme)
        badges = re.findall(r"img\.shields\.io/badge/version-([\d.]+)-", current)
        assert not badges or badges == [version], str(readme)
        fenced_commands = "\n".join(re.findall(r"```[^\n]*\n(.*?)```", current, re.DOTALL))
        assert not re.search(r"npm\s+(?:install|i)\s+-g\s+@atingaii/muxary", fenced_commands), str(readme)
        assert not re.search(r"github\.com/Atingaii/Muxary/releases/download/", content), str(readme)


def test_retained_translations_and_upstream_history_keep_their_actual_release_identity() -> None:
    # A fork version bump must not relabel old CCB APKs or translated history.
    for readme in (ROOT / "README.md", *sorted((ROOT / "README").glob("*.md"))):
        content = readme.read_text()
        if HISTORY_MARKER in content:
            content = content.split(HISTORY_MARKER, 1)[1]
        badges = re.findall(r"img\.shields\.io/badge/version-([\d.]+)-", content)
        assert all(badge == UPSTREAM_BASELINE_VERSION for badge in badges), str(readme)
        downloads = re.findall(r"releases/download/v([\d.]+)/ccb-mobile-v([\d.]+)\.apk", content)
        if readme not in (ROOT / "README.md", ROOT / "README/zh.md"):
            assert badges and downloads, str(readme)
        assert all(pair == (UPSTREAM_BASELINE_VERSION, UPSTREAM_BASELINE_VERSION) for pair in downloads), str(readme)
        assert not re.search(r"github\.com/Atingaii/Muxary/releases/download/", content), str(readme)
