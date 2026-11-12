#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib.parse import unquote


REQUIRED_SUBCOMMANDS = {
    "list",
    "split-pane",
    "send-text",
    "get-text",
    "kill-pane",
    "activate-pane",
}


def run_command(argv: list[str], *, timeout: float = 5.0) -> dict[str, object]:
    try:
        cp = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "argv": argv,
            "returncode": cp.returncode,
            "stdout": cp.stdout,
            "stderr": cp.stderr,
        }
    except Exception as exc:
        return {
            "argv": argv,
            "returncode": None,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }


def extract_cwd_path(file_url: str) -> str:
    if not file_url:
        return ""
    value = str(file_url).strip()
    if not value.startswith("file://"):
        return value.rstrip("/") or "/"
    rest = value[7:]
    if rest.startswith("/"):
        path = rest
    else:
        slash = rest.find("/")
        path = rest[slash:] if slash >= 0 else ""
    return unquote(path).rstrip("/") or "/"


def cwd_matches(pane_cwd: str, work_dir: str) -> bool:
    if not pane_cwd or not work_dir:
        return False
    try:
        return os.path.normpath(extract_cwd_path(pane_cwd)) == os.path.normpath(work_dir)
    except Exception:
        return False


def find_pane_by_title_and_cwd(panes: list[dict[str, object]], marker: str, work_dir: str) -> str | None:
    for pane in panes:
        title = str(pane.get("title") or "")
        if title.startswith(marker) and cwd_matches(str(pane.get("cwd") or ""), work_dir):
            pane_id = pane.get("pane_id")
            return str(pane_id) if pane_id is not None else None
    return None


def offline_fixture_result() -> dict[str, object]:
    panes = [
        {
            "window_id": 1,
            "tab_id": 1,
            "pane_id": 101,
            "workspace": "ccb-alpha",
            "title": "CCB-Codex",
            "cwd": "file://host/home/user/project-alpha",
        },
        {
            "window_id": 2,
            "tab_id": 2,
            "pane_id": 202,
            "workspace": "ccb-beta",
            "title": "CCB-Codex",
            "cwd": "file://host/home/user/project-beta",
        },
    ]
    selected = find_pane_by_title_and_cwd(panes, "CCB-Codex", "/home/user/project-beta")
    return {
        "fixture": "duplicate-title-cwd-aware-selection",
        "selected_pane_id": selected,
        "expected_pane_id": "202",
        "passed": selected == "202",
    }


def parse_live_panes(stdout: str) -> tuple[bool, object]:
    try:
        data = json.loads(stdout or "[]")
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"
    if not isinstance(data, list):
        return False, "json output is not a list"
    return True, data


def main() -> int:
    wezterm = shutil.which("wezterm") or shutil.which("wezterm.exe")
    result: dict[str, object] = {
        "wezterm_path": wezterm,
        "version": None,
        "cli_required_subcommands": sorted(REQUIRED_SUBCOMMANDS),
        "cli_missing_subcommands": sorted(REQUIRED_SUBCOMMANDS),
        "live_instance": False,
        "live_pane_count": 0,
        "offline_fixture": offline_fixture_result(),
        "demo_status": "missing_wezterm",
    }

    if not wezterm:
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0

    version = run_command([wezterm, "--version"])
    result["version"] = (str(version.get("stdout") or "").strip() or str(version.get("stderr") or "").strip())

    help_result = run_command([wezterm, "cli", "--help"])
    help_text = f"{help_result.get('stdout') or ''}\n{help_result.get('stderr') or ''}"
    missing = [name for name in sorted(REQUIRED_SUBCOMMANDS) if name not in help_text]
    result["cli_missing_subcommands"] = missing

    live = run_command([wezterm, "cli", "--no-auto-start", "list", "--format", "json"])
    result["live_list_returncode"] = live["returncode"]
    result["live_list_stderr"] = str(live.get("stderr") or "").strip()
    if live["returncode"] == 0:
        ok, panes = parse_live_panes(str(live.get("stdout") or ""))
        result["live_instance"] = ok
        if ok:
            result["live_pane_count"] = len(panes)  # type: ignore[arg-type]
        else:
            result["live_parse_error"] = panes

    if missing:
        result["demo_status"] = "missing_required_cli_surface"
    elif not bool(result["offline_fixture"]["passed"]):  # type: ignore[index]
        result["demo_status"] = "offline_fixture_failed"
    elif result["live_instance"]:
        result["demo_status"] = "ok_live_read_only"
    else:
        result["demo_status"] = "ok_capability_live_session_absent"

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
