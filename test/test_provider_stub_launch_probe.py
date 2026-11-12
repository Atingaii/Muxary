from __future__ import annotations

import json
import os
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path


STUB_PATH = (Path(__file__).resolve().parent / "stubs" / "provider_stub.py").resolve()


def _probe_env(tmp_path: Path, **overrides: str) -> dict[str, str]:
    env = os.environ.copy()
    for key in tuple(env):
        if "STUB_LAUNCH_" in key:
            env.pop(key, None)
    env.pop("CCB_CALLER_ACTOR", None)
    env.pop("CCB_AGENT_NAME", None)
    env["HOME"] = str(tmp_path / "home")
    env["USERPROFILE"] = env["HOME"]
    env["PYTHONUNBUFFERED"] = "1"
    env["STUB_DELAY"] = "0"
    env.update(overrides)
    return env


def _qwen_command(req_id: str) -> list[str]:
    return [
        sys.executable,
        str(STUB_PATH),
        "--provider",
        "qwen",
        "--bare",
        f"CCB_REQ_ID: {req_id}\n\nlaunch probe",
    ]


def _read_state(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _wait_for_state(path: Path, predicate, *, timeout: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout
    latest: dict = {}
    while time.monotonic() < deadline:
        try:
            latest = _read_state(path)
        except (FileNotFoundError, json.JSONDecodeError):
            time.sleep(0.01)
            continue
        if predicate(latest):
            return latest
        time.sleep(0.01)
    raise AssertionError(f"launch probe state did not converge: {latest!r}")


def _run_qwen(tmp_path: Path, env: dict[str, str], req_id: str = "job_probe") -> subprocess.CompletedProcess[str]:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return subprocess.run(
        _qwen_command(req_id),
        cwd=workspace,
        env=env,
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )


def test_provider_flag_does_not_accept_abbreviations(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(STUB_PATH), "--prov", "qwen"],
        cwd=tmp_path,
        env=_probe_env(tmp_path),
        text=True,
        capture_output=True,
        timeout=5,
        check=False,
    )

    assert result.returncode == 2
    assert "unknown provider: provider_stub.py" in result.stderr


def test_launch_probe_is_disabled_and_writes_no_artifacts_by_default(tmp_path: Path) -> None:
    env = _probe_env(tmp_path)

    result = _run_qwen(tmp_path, env)

    assert result.returncode == 0, result.stderr
    assert "stub reply for job_probe" in result.stdout
    assert not [path for path in (tmp_path / "home").rglob("*") if path.is_file()]
    assert not [path for path in (tmp_path / "workspace").rglob("*") if path.is_file()]


def test_launch_delay_is_opt_in_without_creating_an_implicit_artifact(tmp_path: Path) -> None:
    env = _probe_env(tmp_path, STUB_LAUNCH_DELAY="0.12")

    started = time.monotonic()
    result = _run_qwen(tmp_path, env)
    elapsed = time.monotonic() - started

    assert result.returncode == 0, result.stderr
    assert elapsed >= 0.10
    assert not [path for path in (tmp_path / "home").rglob("*") if path.is_file()]
    assert not [path for path in (tmp_path / "workspace").rglob("*") if path.is_file()]


def test_launch_barrier_records_atomic_max_injected_process_start_interval_and_cleanup(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "launch-state.json"
    barrier_path = tmp_path / "barriers" / "release"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    processes: list[subprocess.Popen[str]] = []
    try:
        for index in range(4):
            env = _probe_env(
                tmp_path,
                STUB_LAUNCH_STATE_PATH=str(state_path),
                STUB_LAUNCH_BARRIER_PATH=str(barrier_path),
                STUB_LAUNCH_BARRIER_TIMEOUT="5",
                STUB_LAUNCH_AGENT=f"worker{index + 1}",
                STUB_LAUNCH_RUN_ID="concurrency-test",
            )
            processes.append(
                subprocess.Popen(
                    _qwen_command(f"job_{index}"),
                    cwd=workspace,
                    env=env,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            )

        active_state = _wait_for_state(state_path, lambda payload: payload.get("active") == 4)
        assert active_state["metric_scope"] == "injected_process_start_interval"
        assert active_state["max_observed"] == 4
        assert len(active_state["active_processes"]) == 4

        barrier_path.parent.mkdir(parents=True)
        barrier_path.touch()
        results = [process.communicate(timeout=5) for process in processes]
        assert all(process.returncode == 0 for process in processes), results

        final_state = _wait_for_state(state_path, lambda payload: payload.get("active") == 0)
        assert final_state["max_observed"] == 4
        assert final_state["active_processes"] == {}
        events = final_state["events"]
        assert len([event for event in events if event["event"] == "entered"]) == 4
        assert len([event for event in events if event["event"] == "barrier_released"]) == 4
        assert len([event for event in events if event["event"] == "exited"]) == 4
        assert [event["seq"] for event in events] == list(range(1, len(events) + 1))
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)


def test_serial_long_lived_provider_launches_do_not_look_concurrent(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "serial-state.json"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    processes: list[subprocess.Popen[str]] = []
    try:
        for index in range(2):
            env = _probe_env(
                tmp_path,
                STUB_LAUNCH_STATE_PATH=str(state_path),
                STUB_LAUNCH_RUN_ID="serial-test",
                STUB_LAUNCH_DELAY="0.05",
                STUB_LAUNCH_AGENT=f"serial-worker{index + 1}",
            )
            process = subprocess.Popen(
                [sys.executable, str(STUB_PATH), "--provider", "codex"],
                cwd=workspace,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            processes.append(process)
            _wait_for_state(
                state_path,
                lambda payload, expected=index + 1: payload.get("active") == 0
                and len(
                    [
                        event
                        for event in payload.get("events", [])
                        if event["event"] == "exited" and event.get("reason") == "startup_probe_complete"
                    ]
                )
                == expected,
            )
            assert process.poll() is None

        state = _read_state(state_path)
        assert state["max_observed"] == 1
        assert state["active"] == 0
        assert state["active_processes"] == {}
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=2)


def test_launch_failure_can_target_provider_agent_and_stage_without_leaking_active(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "failure-state.json"
    targeted = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="failure-test",
        STUB_LAUNCH_AGENT="worker2",
        STUB_LAUNCH_FAIL_STAGE="after_active",
        STUB_LAUNCH_FAIL_PROVIDERS="qwen",
        STUB_LAUNCH_FAIL_AGENTS="worker2",
    )

    failed = _run_qwen(tmp_path, targeted, req_id="job_failed")

    assert failed.returncode == 86
    assert "injected launch failure" in failed.stderr
    failed_state = _read_state(state_path)
    assert failed_state["active"] == 0
    assert failed_state["active_processes"] == {}
    assert failed_state["max_observed"] == 1
    assert any(event["event"] == "injected_failure" and event["stage"] == "after_active" for event in failed_state["events"])

    non_target = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="failure-test",
        STUB_LAUNCH_AGENT="worker3",
        STUB_LAUNCH_FAIL_STAGE="after_active",
        STUB_LAUNCH_FAIL_PROVIDERS="qwen",
        STUB_LAUNCH_FAIL_AGENTS="worker2",
    )
    passed = _run_qwen(tmp_path, non_target, req_id="job_passed")
    assert passed.returncode == 0, passed.stderr
    final_state = _read_state(state_path)
    assert final_state["active"] == 0
    assert len([event for event in final_state["events"] if event["event"] == "injected_failure"]) == 1


def test_launch_failure_match_indices_fail_only_selected_matching_processes(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "artifacts" / "indexed-failure-state.json"
    env = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="indexed-failure-test",
        STUB_LAUNCH_AGENT="worker2",
        STUB_LAUNCH_FAIL_STAGE="after_active",
        STUB_LAUNCH_FAIL_PROVIDERS="qwen",
        STUB_LAUNCH_FAIL_AGENTS="worker2",
        STUB_LAUNCH_FAIL_MATCH_INDICES="2",
    )

    first = _run_qwen(tmp_path, env, req_id="job_first")
    second = _run_qwen(tmp_path, env, req_id="job_second")
    third = _run_qwen(tmp_path, env, req_id="job_third")

    assert first.returncode == 0, first.stderr
    assert second.returncode == 86
    assert "injected launch failure" in second.stderr
    assert third.returncode == 0, third.stderr
    state = _read_state(state_path)
    matches = [event for event in state["events"] if event["event"] == "injection_match"]
    assert [(event["match_index"], event["selected"]) for event in matches] == [
        (1, False),
        (2, True),
        (3, False),
    ]
    failures = [event for event in state["events"] if event["event"] == "injected_failure"]
    assert len(failures) == 1
    assert failures[0]["match_index"] == 2
    assert state["active"] == 0
    assert state["active_processes"] == {}


def test_launch_probe_uses_managed_caller_actor_for_agent_targeting(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "artifacts" / "caller-actor-state.json"
    env = _probe_env(
        tmp_path,
        CCB_CALLER_ACTOR="worker2",
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="caller-actor-test",
        STUB_LAUNCH_FAIL_STAGE="after_active",
        STUB_LAUNCH_FAIL_PROVIDERS="qwen",
        STUB_LAUNCH_FAIL_AGENTS="worker2",
        STUB_LAUNCH_FAIL_MATCH_INDICES="1",
    )

    result = _run_qwen(tmp_path, env, req_id="job_caller_actor")

    assert result.returncode == 86
    state = _read_state(state_path)
    matches = [event for event in state["events"] if event["event"] == "injection_match"]
    assert [(event["agent"], event["match_index"], event["selected"]) for event in matches] == [
        ("worker2", 1, True),
    ]
    assert stat.S_IMODE(state_path.stat().st_mode) == 0o600


def test_launch_probe_cli_failure_latch_arms_then_releases_selected_match(
    tmp_path: Path,
) -> None:
    state_path = tmp_path / "artifacts" / "cli-latch-state.json"
    release_dir = tmp_path / "artifacts" / "releases"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env = _probe_env(tmp_path, CCB_CALLER_ACTOR="worker2")
    command = [
        *_qwen_command("job_cli_latch"),
        "--stub-launch-state-path",
        str(state_path),
        "--stub-launch-run-id",
        "cli-latch-test",
        "--stub-launch-fail-stage",
        "after_active",
        "--stub-launch-fail-agents",
        "worker2",
        "--stub-launch-fail-match-indices",
        "1",
        "--stub-launch-fail-release-dir",
        str(release_dir),
        "--stub-launch-fail-release-timeout",
        "5",
    ]
    process = subprocess.Popen(
        command,
        cwd=workspace,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        armed = _wait_for_state(
            state_path,
            lambda payload: any(
                event.get("event") == "injected_failure_armed"
                and event.get("match_index") == 1
                for event in payload.get("events", [])
            ),
        )
        assert process.poll() is None
        assert not any(
            event.get("event") == "injected_failure" for event in armed["events"]
        )

        release_dir.mkdir(parents=True)
        (release_dir / "match-000001.release").touch()
        stdout, stderr = process.communicate(timeout=5)

        assert process.returncode == 86, (stdout, stderr)
        final = _read_state(state_path)
        assert [
            event["event"]
            for event in final["events"]
            if event["event"].startswith("injected_failure")
        ] == [
            "injected_failure_armed",
            "injected_failure_released",
            "injected_failure",
        ]
        assert final["active"] == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)


def test_launch_cancellation_uses_distinct_terminal_code_and_cleans_up(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "cancel-state.json"
    env = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="cancellation-test",
        STUB_LAUNCH_AGENT="worker1",
        STUB_LAUNCH_CANCEL_STAGE="after_delay",
        STUB_LAUNCH_CANCEL_PROVIDERS="qwen",
        STUB_LAUNCH_CANCEL_AGENTS="worker1",
    )

    result = _run_qwen(tmp_path, env, req_id="job_cancelled")

    assert result.returncode == 130
    assert "injected launch cancellation" in result.stderr
    state = _read_state(state_path)
    assert state["active"] == 0
    assert state["active_processes"] == {}
    assert any(event["event"] == "injected_cancellation" for event in state["events"])


def test_signal_during_launch_barrier_converges_active_counter(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "signal-state.json"
    barrier_path = tmp_path / "barriers" / "never-release"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    env = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="signal-test",
        STUB_LAUNCH_BARRIER_PATH=str(barrier_path),
        STUB_LAUNCH_BARRIER_TIMEOUT="5",
        STUB_LAUNCH_AGENT="worker-signal",
    )
    process = subprocess.Popen(
        [sys.executable, str(STUB_PATH), "--provider", "codex"],
        cwd=workspace,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_for_state(
            state_path,
            lambda payload: payload.get("active") == 1
            and any(event["event"] == "barrier_wait_started" for event in payload.get("events", [])),
        )
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=5)
        assert process.returncode == 0, (stdout, stderr)

        final_state = _wait_for_state(state_path, lambda payload: payload.get("active") == 0)
        assert final_state["active_processes"] == {}
        assert any(
            event["event"] == "exited" and event.get("reason") == "signal:SIGTERM"
            for event in final_state["events"]
        )
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=2)


def test_launch_probe_rejects_implicit_relative_artifact_paths(tmp_path: Path) -> None:
    env = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH="relative-state.json",
        STUB_LAUNCH_RUN_ID="relative-path-test",
    )

    result = _run_qwen(tmp_path, env)

    assert result.returncode == 2
    assert "must be an absolute path" in result.stderr
    assert not (tmp_path / "workspace" / "relative-state.json").exists()


def test_state_backed_probe_requires_explicit_nonempty_run_id(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "missing-run-id.json"
    env = _probe_env(tmp_path, STUB_LAUNCH_STATE_PATH=str(state_path))

    result = _run_qwen(tmp_path, env)

    assert result.returncode == 2
    assert "requires an explicit nonempty run id" in result.stderr
    assert not state_path.exists()


def test_reused_state_path_starts_a_fresh_evidence_epoch_for_new_run_id(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "reused-state.json"
    first = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="run-a",
    )
    second = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="run-b",
    )

    first_result = _run_qwen(tmp_path, first, req_id="job_first")
    first_state = _read_state(state_path)
    second_result = _run_qwen(tmp_path, second, req_id="job_second")
    second_state = _read_state(state_path)

    assert first_result.returncode == 0, first_result.stderr
    assert second_result.returncode == 0, second_result.stderr
    assert first_state["run_id"] == "run-a"
    assert second_state["run_id"] == "run-b"
    assert second_state["max_observed"] == 1
    assert [event["seq"] for event in second_state["events"]] == list(
        range(1, len(second_state["events"]) + 1)
    )
    assert {event.get("run_id") for event in second_state["events"]} == {"run-b"}


def test_reused_state_path_fails_closed_when_another_run_is_still_active(tmp_path: Path) -> None:
    state_path = tmp_path / "artifacts" / "mixed-active-state.json"
    state_path.parent.mkdir(parents=True)
    original = {
        "schema_version": 2,
        "run_id": "run-a",
        "metric_scope": "injected_process_start_interval",
        "active": 1,
        "max_observed": 1,
        "active_processes": {
            "existing-token": {
                "pid": os.getpid(),
                "provider": "qwen",
                "agent": "existing",
                "run_id": "run-a",
                "entered_ns": time.time_ns(),
            }
        },
        "next_event_seq": 1,
        "events": [],
    }
    state_path.write_text(json.dumps(original) + "\n", encoding="utf-8")
    env = _probe_env(
        tmp_path,
        STUB_LAUNCH_STATE_PATH=str(state_path),
        STUB_LAUNCH_RUN_ID="run-b",
    )

    result = _run_qwen(tmp_path, env)

    assert result.returncode == 2
    assert "active for a different run id" in result.stderr
    assert _read_state(state_path) == original
