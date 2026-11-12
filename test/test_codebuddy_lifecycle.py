"""Real CCB processes and tmux, with an independently encoded native CLI stub."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import pytest


def _ccb(project: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[1] / 'ccb.py'), *args],
        cwd=project, env=dict(os.environ), capture_output=True, text=True, timeout=35,
    )
    assert result.returncode == 0, (args, result.stdout, result.stderr)
    return result


def _wait_binding(session: dict, *, previous: str = '') -> dict:
    path = Path(session['state_dir']) / 'native-binding.json'
    end = time.monotonic() + 10
    while time.monotonic() < end:
        if path.is_file():
            data = json.loads(path.read_text())
            if data['launch_id'] == session['codebuddy_launch_id'] and data['session_id'] != previous:
                return data
        time.sleep(.05)
    raise AssertionError(f'No current native binding: {path}')


def _ask(project: Path) -> None:
    accepted = _ccb(project, 'ask', 'buddy', 'from', 'user', 'native lifecycle test').stdout
    assert 'accepted job=job_' in accepted, accepted
    end = time.monotonic() + 12
    last = ''
    while time.monotonic() < end:
        last = _ccb(project, 'pend', 'buddy').stdout
        if 'status: completed' in last:
            assert 'stub reply for' in last
            assert 'CCB_DONE:' not in last
            return
        assert 'status: failed' not in last, last
        time.sleep(.1)
    raise AssertionError(last)


@pytest.mark.ccb_lifecycle_smoke
def test_native_ask_clear_compact_and_exact_resume(tmp_path, phase2_runtime_owner):
    if not shutil.which('tmux'):
        pytest.skip('tmux required')
    project = tmp_path / 'codebuddy-project'
    config = project / '.ccb' / 'ccb.config'
    config.parent.mkdir(parents=True)
    config.write_text('buddy:codebuddy\n')
    phase2_runtime_owner.track(project)
    _ccb(project)
    session_path = project / '.ccb' / '.codebuddy-buddy-session'
    session = json.loads(session_path.read_text())
    first = _wait_binding(session)
    _ask(project)
    _ccb(project, 'clear', 'buddy')
    cleared = _wait_binding(session, previous=first['session_id'])
    _ask(project)
    _ccb(project, 'compact', 'buddy')
    events_path = Path(cleared['session_path']).parent / 'stub-lifecycle.jsonl'
    end = time.monotonic() + 10
    while time.monotonic() < end:
        events = [json.loads(line) for line in events_path.read_text().splitlines()]
        if {'event': 'compact', 'session_id': cleared['session_id']} in events:
            break
        time.sleep(.05)
    else:
        raise AssertionError(f'Native CLI never received /compact: {events}')
    assert _wait_binding(session)['session_id'] == cleared['session_id']
    _ask(project)
    _ccb(project, 'kill')
    _ccb(project)
    resumed_session = json.loads(session_path.read_text())
    resumed = _wait_binding(resumed_session)
    assert resumed['session_id'] == cleared['session_id']
    assert resumed['session_path'] == cleared['session_path']
    assert resumed_session['codebuddy_resume_status'] == 'exact_session_selected'
    assert resumed_session['codebuddy_launch_id'] != session['codebuddy_launch_id']
    _ask(project)
