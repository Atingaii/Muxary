from __future__ import annotations

from pathlib import Path

from cli.management_runtime import install as install_runtime


def test_resolve_installer_paths_uses_live_source_repo_with_managed_prefix(monkeypatch, tmp_path: Path) -> None:
    source_dir = tmp_path / "source-install"
    source_dir.mkdir()
    (source_dir / "install.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (source_dir / ".git").mkdir()
    managed_prefix = tmp_path / "managed-install"
    monkeypatch.setenv("CODEX_INSTALL_PREFIX", str(managed_prefix))

    source_root, install_dir = install_runtime.resolve_installer_paths("install", script_root=source_dir)

    assert source_root == source_dir
    assert install_dir == managed_prefix


def test_resolve_managed_install_dir_uses_managed_prefix_for_source_repo(monkeypatch, tmp_path: Path) -> None:
    source_dir = tmp_path / "source-install"
    source_dir.mkdir()
    (source_dir / "install.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    (source_dir / ".git").mkdir()
    managed_prefix = tmp_path / "managed-install"
    monkeypatch.setenv("CODEX_INSTALL_PREFIX", str(managed_prefix))

    install_dir = install_runtime.resolve_managed_install_dir(script_root=source_dir)

    assert install_dir == managed_prefix


def test_build_unix_installer_env_marks_source_repo_root(monkeypatch, tmp_path: Path) -> None:
    source_dir = tmp_path / "source-install"
    source_dir.mkdir()
    (source_dir / ".git").mkdir()
    install_dir = tmp_path / "managed-install"
    monkeypatch.delenv("CCB_SOURCE_KIND", raising=False)
    monkeypatch.delenv("CCB_SOURCE_ROOT", raising=False)
    monkeypatch.delenv("CCB_GIT_COMMIT", raising=False)
    monkeypatch.delenv("CCB_GIT_DATE", raising=False)
    monkeypatch.setattr(install_runtime, "_detect_git_head", lambda _source_dir: ("abc1234", "2026-04-25"))

    env = install_runtime._build_unix_installer_env(install_dir, source_dir=source_dir)

    assert env["CODEX_INSTALL_PREFIX"] == str(install_dir)
    assert env["MUXARY_INSTALL_PREFIX"] == str(install_dir)
    assert env["CCB_SOURCE_KIND"] == "source"
    assert env["CCB_SOURCE_ROOT"] == str(source_dir)
    assert env["CCB_GIT_COMMIT"] == "abc1234"
    assert env["CCB_GIT_DATE"] == "2026-04-25"


def test_run_installer_stages_and_normalizes_crlf_checkout(tmp_path: Path) -> None:
    source_dir = tmp_path / "source-install"
    source_dir.mkdir()
    install_sh = source_dir / "install.sh"
    marker_path = source_dir / "ran.txt"
    install_sh.write_bytes(
        b"#!/usr/bin/env bash\r\n"
        b"set -euo pipefail\r\n"
        b"printf '%s\\n' \"$0\" > \"$CODEX_INSTALL_PREFIX/ran.txt\"\r\n"
    )

    code = install_runtime.run_installer("install", script_root=source_dir)

    assert code == 0
    ran_from = marker_path.read_text(encoding="utf-8").strip()
    assert ran_from != str(install_sh)
    assert "ccb-installer-" in ran_from


def test_muxary_install_prefix_takes_precedence_over_legacy_prefix(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MUXARY_INSTALL_PREFIX", str(tmp_path / "muxary"))
    monkeypatch.setenv("CODEX_INSTALL_PREFIX", str(tmp_path / "upstream"))

    assert install_runtime._default_install_dir() == tmp_path / "muxary"


def test_muxary_default_install_path_is_isolated_from_upstream(monkeypatch) -> None:
    monkeypatch.delenv("MUXARY_INSTALL_PREFIX", raising=False)
    monkeypatch.delenv("CODEX_INSTALL_PREFIX", raising=False)
    monkeypatch.setattr(install_runtime.platform, "system", lambda: "Linux")

    assert install_runtime._default_install_dir() == Path.home() / ".local/share/muxary"


def test_windows_default_install_candidates_do_not_reuse_upstream(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))

    assert install_runtime._windows_install_dir_candidates() == [
        tmp_path / "local/muxary",
        Path.home() / "AppData/Local/muxary",
    ]


def test_staged_installer_overrides_inherited_muxary_prefix(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MUXARY_INSTALL_PREFIX", str(tmp_path / "unrelated"))
    install_dir = tmp_path / "selected"

    env = install_runtime._build_unix_installer_env(install_dir, source_dir=tmp_path)

    assert env["MUXARY_INSTALL_PREFIX"] == env["CODEX_INSTALL_PREFIX"] == str(install_dir)
