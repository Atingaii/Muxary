from __future__ import annotations

import os
import json
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"


def _python310_executable() -> str:
    for candidate in (
        sys.executable,
        "python3.14",
        "python3.13",
        "python3.12",
        "python3.11",
        "python3.10",
        "python3",
        "python",
    ):
        try:
            output = subprocess.check_output(
                [
                    candidate,
                    "-c",
                    "import sys\nif sys.version_info < (3, 10): raise SystemExit(1)\nprint(sys.executable)",
                ],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            continue
        if output:
            return output
    raise AssertionError("Python 3.10+ is required to test source/dev wrappers")


def _run_source_dev_snippet(tmp_path: Path, shell_body: str) -> subprocess.CompletedProcess[str]:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    python310 = _python310_executable()
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home_dir),
            "CODEX_INSTALL_PREFIX": str(tmp_path / "managed"),
            "CODEX_BIN_DIR": str(tmp_path / "bin"),
            "CODEX_HOME": str(tmp_path / "codex-home"),
            "CCB_LANG": "en",
            "CCB_SOURCE_KIND": "source",
            "CCB_SOURCE_ROOT": str(REPO_ROOT),
            "CCB_PYTHON_BIN": python310,
        }
    )
    command = textwrap.dedent(
        f"""
        set -euo pipefail
        source {shlex.quote(str(INSTALL_SH))}
        {shell_body}
        """
    )
    return subprocess.run(
        ["bash", "-lc", command],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )


def test_source_dev_install_links_live_bin_and_ask_skill_asset(tmp_path: Path) -> None:
    completed = _run_source_dev_snippet(
        tmp_path,
        """
        install_bin_links
        verify_installed_entrypoints
        install_codex_skills
        """,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "OK: Installed entrypoints passed runtime smoke check" in completed.stdout

    bin_dir = tmp_path / "bin"
    ccb_path = bin_dir / "ccb"
    assert ccb_path.exists()
    assert not ccb_path.is_symlink()
    assert str(REPO_ROOT / 'ccb.py') in ccb_path.read_text()
    assert 'export CCB_SOURCE_RUNTIME_OK=1' in ccb_path.read_text()
    muxary_path = bin_dir / "muxary"
    assert not muxary_path.is_symlink()
    assert str(REPO_ROOT / 'muxary.py') in muxary_path.read_text()
    assert 'export CCB_SOURCE_RUNTIME_OK=1' in muxary_path.read_text()

    ask_path = bin_dir / "ask"
    assert ask_path.exists()
    assert not ask_path.is_symlink()
    assert str(REPO_ROOT / 'bin' / 'ask.py') in ask_path.read_text()
    assert 'export CCB_SOURCE_RUNTIME_OK=1' not in ask_path.read_text()

    reconnect_path = bin_dir / "codex-reconnect"
    assert reconnect_path.exists()
    assert not reconnect_path.is_symlink()
    assert str(REPO_ROOT / 'bin' / 'codex-reconnect.py') in reconnect_path.read_text()
    reconnect_version = subprocess.run(
        [str(reconnect_path), "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert reconnect_version.returncode == 0, reconnect_version.stderr
    assert reconnect_version.stdout.strip() == "codex-reconnect 0.3.6"

    runtime_env = {**os.environ, 'HOME': str(tmp_path / 'home')}
    runtime_env.pop('CCB_PYTHON', None)
    runtime_env.pop('CCB_SOURCE_RUNTIME_OK', None)
    for executable in ('ccb', 'muxary', 'ask', 'codex-reconnect'):
        probe = subprocess.run([str(bin_dir / executable), '--help'], env=runtime_env,
                               capture_output=True, text=True)
        assert probe.returncode == 0, (executable, probe.stdout, probe.stderr)

    ask_skill_md = tmp_path / "codex-home" / "skills" / "ask" / "SKILL.md"
    assert ask_skill_md.is_file()
    assert not ask_skill_md.is_symlink()
    assert "name: ask" in ask_skill_md.read_text(encoding="utf-8")

    ccb_clear_skill_md = tmp_path / "codex-home" / "skills" / "ccb-clear" / "SKILL.md"
    assert ccb_clear_skill_md.is_file()
    assert not ccb_clear_skill_md.is_symlink()
    assert "name: ccb-clear" in ccb_clear_skill_md.read_text(encoding="utf-8")

    ccb_compact_skill_md = tmp_path / "codex-home" / "skills" / "ccb-compact" / "SKILL.md"
    assert ccb_compact_skill_md.is_file()
    assert not ccb_compact_skill_md.is_symlink()
    assert "name: ccb-compact" in ccb_compact_skill_md.read_text(encoding="utf-8")

    ccb_diagnose_skill_md = tmp_path / "codex-home" / "skills" / "ccb-diagnose" / "SKILL.md"
    assert ccb_diagnose_skill_md.is_file()
    assert not ccb_diagnose_skill_md.is_symlink()
    assert "name: ccb-diagnose" in ccb_diagnose_skill_md.read_text(encoding="utf-8")


    reconnect_skill_md = tmp_path / "codex-home" / "skills" / "reconnect" / "SKILL.md"
    assert reconnect_skill_md.is_file()
    assert not reconnect_skill_md.is_symlink()
    assert "name: reconnect" in reconnect_skill_md.read_text(encoding="utf-8")

    skills_dir = tmp_path / "codex-home" / "skills"
    assert not (skills_dir / "ccb-config").exists()
    assert not (skills_dir / "all-plan").exists()
    assert not (skills_dir / "ping").exists()
    assert not (skills_dir / "pend").exists()
    assert not (skills_dir / "file-op").exists()


def test_source_install_rejects_missing_web_assets_before_install_side_effects(tmp_path: Path) -> None:
    source = tmp_path / 'unbuilt-source'
    source.mkdir()
    (source / 'ccb').write_text('fixture')
    completed = _run_source_dev_snippet(tmp_path, f'''
        export CCB_SOURCE_ROOT={shlex.quote(str(source))}
        validate_temporary_install_scope() {{ :; }}
        install_requirements() {{ echo UNEXPECTED_DEPENDENCY_INSTALL; }}
        install_cli_only
    ''')
    assert completed.returncode != 0
    assert 'Muxary Web assets are missing' in completed.stderr
    assert 'npm --prefix' in completed.stderr
    assert 'UNEXPECTED_DEPENDENCY_INSTALL' not in completed.stdout
    assert not (tmp_path / 'bin').exists()
    # Removing only the missing-assets factor should allow the same gate.
    (source / 'assets' / 'workbench').mkdir(parents=True)
    (source / 'assets' / 'workbench' / 'index.html').write_text('<html>fixture</html>')
    (tmp_path / 'built-case').mkdir()
    second = _run_source_dev_snippet(tmp_path / 'built-case', f'''
        export CCB_SOURCE_ROOT={shlex.quote(str(source))}
        validate_source_workbench_assets
    ''')
    assert second.returncode == 0, second.stderr



def test_source_dev_install_ignores_managed_codex_home_for_skill_assets(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    managed_home = (
        tmp_path
        / "project"
        / ".ccb"
        / "agents"
        / "agent2"
        / "provider-state"
        / "codex"
        / "home"
    )
    python310 = _python310_executable()
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home_dir),
            "CODEX_INSTALL_PREFIX": str(tmp_path / "managed"),
            "CODEX_BIN_DIR": str(tmp_path / "bin"),
            "CODEX_HOME": str(managed_home),
            "CCB_LANG": "en",
            "CCB_SOURCE_KIND": "source",
            "CCB_SOURCE_ROOT": str(REPO_ROOT),
            "CCB_PYTHON_BIN": python310,
        }
    )
    command = textwrap.dedent(
        f"""
        set -euo pipefail
        source {shlex.quote(str(INSTALL_SH))}
        install_codex_skills
        """
    )
    completed = subprocess.run(
        ["bash", "-lc", command],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    ccb_clear_skill_md = home_dir / ".codex" / "skills" / "ccb-clear" / "SKILL.md"
    assert ccb_clear_skill_md.is_file()
    assert not ccb_clear_skill_md.is_symlink()
    assert not (home_dir / ".codex" / "skills" / "ccb-config").exists()
    assert not (managed_home / "skills" / "ccb-config").exists()
    assert not (managed_home / "skills" / "ccb-clear").exists()
    assert (home_dir / ".codex" / "skills" / "ccb-compact" / "SKILL.md").is_file()
    assert (home_dir / ".codex" / "skills" / "ccb-diagnose" / "SKILL.md").is_file()


def test_installed_source_ccb_wrapper_sets_guard_without_modifying_checkout(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    source.mkdir()
    launcher = source / 'ccb'
    launcher.write_text('#!/usr/bin/env bash\nexec _ccb-python "$0.py" "$@"\n')
    body = source / 'ccb.py'
    body.write_text('import json, os, sys\nprint(json.dumps([os.getenv("CCB_SOURCE_RUNTIME_OK"), os.getenv("CCB_PYTHON"), sys.argv[1:]]))\n')
    before = launcher.read_bytes(), body.read_bytes()
    destination = tmp_path / 'bin' / 'ccb'
    result = _run_source_dev_snippet(tmp_path,
        f'install_entrypoint_executable {shlex.quote(str(launcher))} {shlex.quote(str(destination))}')
    assert result.returncode == 0, result.stderr or result.stdout
    env = dict(os.environ)
    env.pop('CCB_SOURCE_RUNTIME_OK', None)
    env.pop('CCB_PYTHON', None)
    actual = subprocess.run([str(destination), 'ask', 'buddy'], env=env, cwd=tmp_path,
                            capture_output=True, text=True, check=True)
    assert json.loads(actual.stdout) == ['1', _python310_executable(), ['ask', 'buddy']]
    assert (launcher.read_bytes(), body.read_bytes()) == before


def test_direct_source_checkout_keeps_diagnostic_guard(tmp_path: Path) -> None:
    env = dict(os.environ)
    for name in ('CCB_SOURCE_RUNTIME_OK', 'CCB_SOURCE_ALLOWED_ROOTS', 'PYTEST_CURRENT_TEST'):
        env.pop(name, None)
    result = subprocess.run([_python310_executable(), str(REPO_ROOT / 'ccb.py'), 'doctor'],
                            env=env, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'Refusing to run the CCB source checkout' in result.stderr + result.stdout


def test_cli_only_install_does_not_project_global_agent_or_shell_config(tmp_path: Path) -> None:
    home = tmp_path / 'home'
    home.mkdir()
    protected = ('.claude/settings.json', '.claude.json', '.codex/config.toml',
                 '.factory/settings.json', '.bashrc', '.tmux.conf')
    for relative in protected:
        path = home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('user-owned fixture\n')
    before = {path.relative_to(home): path.read_bytes() for path in home.rglob('*') if path.is_file()}
    env = {**os.environ, 'HOME': str(home), 'MUXARY_INSTALL_PREFIX': str(home / 'managed'),
           'MUXARY_BIN_DIR': str(home / 'bin'), 'CCB_SOURCE_KIND': 'source',
           'CCB_SOURCE_ROOT': str(REPO_ROOT), 'CCB_PYTHON_BIN': _python310_executable()}
    script = f'''source {shlex.quote(str(INSTALL_SH))}
install_requirements() {{ :; }}
build_sidebar_helper_if_possible() {{ :; }}
build_rs_helper_if_possible() {{ :; }}
main install-cli
'''
    result = subprocess.run(['bash', '-c', script], env=env, cwd=tmp_path,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr or result.stdout
    assert 'CLI-only installation complete' in result.stdout
    after = {path.relative_to(home): path.read_bytes() for path in home.rglob('*')
             if path.is_file() and path.relative_to(home).parts[0] != 'bin'}
    # Existing entrypoint introspection initializes this empty runtime log;
    # this is not permission/skill/config projection.
    assert after.pop(Path('.ccb/logs/comm.log')) == b''
    assert after == before
    assert (home / 'bin/muxary').is_file()
    assert (home / 'bin/ccb').is_file()


def test_python_selection_falls_back_to_versioned_python_command(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    fake_bin = tmp_path / "fake-bin"
    home_dir.mkdir()
    fake_bin.mkdir()
    for name in ("python3", "python3.14", "python3.13", "python3.11", "python3.10"):
        (fake_bin / name).write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (fake_bin / name).chmod(0o755)
    (fake_bin / "python3.12").write_text(
        (
            "#!/usr/bin/env bash\n"
            "if [[ \"${1:-}\" == \"-c\" && \"${2:-}\" == *sys.executable* ]]; then\n"
            "  printf '%s\\n' \"$0\"\n"
            "fi\n"
            "exit 0\n"
        ),
        encoding="utf-8",
    )
    (fake_bin / "python3.12").chmod(0o755)
    env = os.environ.copy()
    env.pop("CCB_PYTHON_BIN", None)
    env.update(
        {
            "HOME": str(home_dir),
            "CODEX_INSTALL_PREFIX": str(tmp_path / "managed"),
            "CODEX_BIN_DIR": str(tmp_path / "bin"),
            "CCB_LANG": "en",
        }
    )
    command = textwrap.dedent(
        f"""
        set -euo pipefail
        source {shlex.quote(str(INSTALL_SH))}
        export PATH={shlex.quote(str(fake_bin))}:$PATH
        selected_python_executable
        """
    )

    completed = subprocess.run(
        ["bash", "-lc", command],
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert completed.stdout.strip() == str(fake_bin / "python3.12")


def test_claude_route_install_preserves_unmarked_external_rules_file(tmp_path: Path) -> None:
    completed = _run_source_dev_snippet(
        tmp_path,
        """
        mkdir -p "$HOME/.claude/rules"
        printf 'user custom claude rule\\n' > "$HOME/.claude/rules/ccb-config.md"
        export CCB_CLAUDE_MD_MODE=route
        install_claude_md_config
        """,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    external_config = tmp_path / "home" / ".claude" / "rules" / "ccb-config.md"
    assert external_config.read_text(encoding="utf-8") == "user custom claude rule\n"
    assert "Preserved non-CCB external CCB config" in completed.stdout


def test_claude_route_install_removes_marked_external_rules_file(tmp_path: Path) -> None:
    completed = _run_source_dev_snippet(
        tmp_path,
        """
        mkdir -p "$HOME/.claude/rules"
        printf '<!-- CCB_CONFIG_START -->\\nold ccb block\\n<!-- CCB_CONFIG_END -->\\n' > "$HOME/.claude/rules/ccb-config.md"
        export CCB_CLAUDE_MD_MODE=route
        install_claude_md_config
        """,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    external_config = tmp_path / "home" / ".claude" / "rules" / "ccb-config.md"
    assert not external_config.exists()
    assert "Removed CCB-owned external CCB config" in completed.stdout


def test_claude_uninstall_preserves_unmarked_external_rules_file(tmp_path: Path) -> None:
    completed = _run_source_dev_snippet(
        tmp_path,
        """
        mkdir -p "$HOME/.claude/rules"
        printf 'user custom claude rule\\n' > "$HOME/.claude/rules/ccb-config.md"
        uninstall_claude_md_config
        """,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    external_config = tmp_path / "home" / ".claude" / "rules" / "ccb-config.md"
    assert external_config.read_text(encoding="utf-8") == "user custom claude rule\n"
    assert "Preserved non-CCB external CCB config" in completed.stdout


def test_claude_uninstall_removes_marked_external_rules_file(tmp_path: Path) -> None:
    completed = _run_source_dev_snippet(
        tmp_path,
        """
        mkdir -p "$HOME/.claude/rules"
        printf '<!-- CCB_CONFIG_START -->\\nold ccb block\\n<!-- CCB_CONFIG_END -->\\n' > "$HOME/.claude/rules/ccb-config.md"
        uninstall_claude_md_config
        """,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    external_config = tmp_path / "home" / ".claude" / "rules" / "ccb-config.md"
    assert not external_config.exists()
    assert "Removed CCB-owned external CCB config" in completed.stdout
