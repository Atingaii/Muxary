from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


def _load_runner():
    module_path = Path(__file__).resolve().parents[1] / "dev_tools" / "perf_runtime_lifecycle_profile.py"
    spec = importlib.util.spec_from_file_location("perf_runtime_lifecycle_profile", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_classify_process_buckets() -> None:
    runner = _load_runner()
    assert runner.classify_process("/usr/bin/python /repo/lib/ccbd/main.py --project /repo", command_basename="main.py") == "ccb/ccbd/main"
    assert runner.classify_process("/opt/venv/bin/python .../keeper_main.py --project /repo", command_basename="keeper_main.py") == "ccb/keeper"
    assert runner.classify_process("ccbd/sidebar --project /repo", command_basename="sidebar") == "ccbd/sidebar"
    assert runner.classify_process("python /repo/provider/claude-runtime --project /repo", command_basename="provider-runtime") == "provider/claude"
    assert runner.classify_process("sh -lc 'tmux list-panes'", command_basename="sh") == "shell-wrapper"
    assert runner.classify_process("tmux send-keys -t 0 C-c", command_basename="tmux") == "terminal-frontend"
    assert runner.classify_process("tmux: server (0)", command_basename="tmux:") == "tmux-server"
    assert runner.classify_process("tmux new-session sh -lc 'sleep 1'", command_basename="tmux") == "tmux-server"
    assert (
        runner.classify_process("python /path/ccb_test ask agent_codex hi", command_basename="python")
        == "ask-cli-subprocess"
    )
    assert (
        runner.classify_process("python /path/ccb ask agent_codex hi", command_basename="python")
        == "ask-cli-subprocess"
    )
    assert runner.classify_process("node /opt/bin/codex resume abc", command_basename="node") == "provider/codex"
    assert runner.classify_process("node /opt/bin/gemini --resume latest", command_basename="node") == "provider/gemini"
    assert (
        runner.classify_process("python -m helper --project /repo", command_basename="python", in_project=True)
        == "python-misc"
    )
    assert runner.classify_process("/usr/bin/python -V", command_basename="python") == "other-system"


def test_project_scoped_classification_keeps_unrelated_ccb_in_other_system() -> None:
    runner = _load_runner()

    assert (
        runner.classify_process(
            "/usr/bin/python /repo/lib/ccbd/main.py --project /other",
            command_basename="python",
            in_project=False,
            scope_to_project=True,
        )
        == "other-system"
    )
    assert (
        runner.classify_process(
            "/usr/bin/python /repo/lib/ccbd/main.py --project /target",
            command_basename="python",
            in_project=True,
            scope_to_project=True,
        )
        == "ccb/ccbd/main"
    )


def test_project_related_pids_include_children_of_project_process(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_runner()
    project = tmp_path / "project"
    rows = (
        (10, 1, 0.0, 1.0, f"tmux: server -S {project}/.ccb/ccbd/tmux.sock"),
        (11, 10, 0.0, 1.0, "codex --continue"),
        (12, 1, 0.0, 1.0, "python /other/lib/ccbd/main.py"),
    )
    monkeypatch.setattr(runner, "_pid_cwd_under_project", lambda _pid, _project: False)

    related = runner._project_related_pids(rows, project)

    assert related == {10, 11}


def test_coerce_command() -> None:
    runner = _load_runner()
    assert runner._coerce_command(None) is None
    assert runner._coerce_command("python -c 'print(1)'") == ("python", "-c", "print(1)")
    assert runner._coerce_command("   ") is None


def test_persisted_command_summary_drops_arguments_and_prompt_text() -> None:
    runner = _load_runner()
    secret = "private-workflow-prompt-token"

    summary = runner._summarize_command(f"python /private/path/worker.py --prompt {secret}")

    assert summary == "executable:python:worker.py"
    assert secret not in summary
    assert "/private/path" not in summary


def test_collect_phase_samples_stops_when_inactive() -> None:
    runner = _load_runner()
    process_rows = (
        (10, 1, 1.0, 1024.0, "python ccbd/main.py"),
        (11, 1, 2.0, 2048.0, "tmux: server"),
    )

    call_count = 0

    def _snapshot() -> tuple[tuple[int, int, float, float, str], ...]:
        nonlocal call_count
        call_count += 1
        return process_rows

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(runner, "_collect_process_snapshot", _snapshot)
    try:
        called = 0

        def is_active() -> bool:
            nonlocal called
            called += 1
            return called < 2

        samples = runner._collect_phase_samples(
            is_active=is_active,
            max_samples=5,
            interval_s=0.0,
            project_root=None,
        )
    finally:
        monkeypatch.undo()
    assert len(samples) == 2
    assert call_count == 2
    assert samples[0].processes[0].bucket == "ccb/ccbd/main"
    assert samples[1].processes[1].bucket == "tmux-server"


def test_collect_phase_samples_filters_unrelated_processes_when_project_scoped(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_runner()
    project = tmp_path / "project"
    process_rows = (
        (10, 1, 10.0, 1024.0, f"python {project}/lib/ccbd/main.py"),
        (11, 10, 3.0, 1024.0, "sh -lc 'ccb ask agent hi'"),
        (12, 1, 90.0, 1024.0, "python /unrelated/heavy.py"),
        (13, 10, 1.0, 1024.0, "ps -eo pid=,ppid=,pcpu=,rss=,vsz=,args="),
    )

    monkeypatch.setattr(runner, "_collect_process_snapshot", lambda: process_rows)
    monkeypatch.setattr(runner, "_pid_cwd_under_project", lambda _pid, _project: False)
    monkeypatch.setattr(runner.os, "getpid", lambda: 10)

    samples = runner._collect_phase_samples(
        is_active=lambda: False,
        max_samples=1,
        interval_s=0.0,
        project_root=project,
    )

    assert [proc.pid for proc in samples[0].processes] == [11]
    assert [proc.bucket for proc in samples[0].processes] == ["shell-wrapper"]


def test_aggregate_phase_rollup_math() -> None:
    runner = _load_runner()
    samples = [
        runner.ProcessSample(
            elapsed_s=0.0,
            processes=(
                runner.SampledProcess(
                    pid=1,
                    ppid=0,
                    cpu_pct=10.0,
                    rss_mib=4.0,
                    command="python ccbd/main.py",
                    bucket="ccb/ccbd/main",
                ),
                runner.SampledProcess(
                    pid=2,
                    ppid=0,
                    cpu_pct=20.0,
                    rss_mib=6.0,
                    command="tmux: server",
                    bucket="tmux-server",
                ),
            ),
        ),
        runner.ProcessSample(
            elapsed_s=1.0,
            processes=(
                runner.SampledProcess(
                    pid=3,
                    ppid=0,
                    cpu_pct=20.0,
                    rss_mib=6.0,
                    command="python ccbd/main.py",
                    bucket="ccb/ccbd/main",
                ),
                runner.SampledProcess(
                    pid=2,
                    ppid=0,
                    cpu_pct=10.0,
                    rss_mib=8.0,
                    command="tmux: server",
                    bucket="tmux-server",
                ),
            ),
        ),
    ]
    summary = runner._aggregate_phase(samples)
    assert summary["samples"] == 2
    assert summary["status"] == "sampled"
    assert summary["avg_cpu_pct"] == 30.0
    assert summary["buckets"]["ccb/ccbd/main"]["avg_cpu_pct"] == 15.0
    assert summary["buckets"]["tmux-server"]["avg_cpu_pct"] == 15.0
    assert summary["buckets"]["ccb/ccbd/main"]["cpu_share"] == 0.5
    assert summary["buckets"]["tmux-server"]["cpu_share"] == 0.5
    assert summary["buckets"]["ccb/ccbd/main"]["rss_max_mib"] == 6.0
    assert summary["buckets"]["tmux-server"]["rss_max_mib"] == 8.0
    assert summary["buckets"]["ccb/ccbd/main"]["top_commands"][0]["avg_cpu_pct"] == 15.0
    assert summary["buckets"]["tmux-server"]["top_commands"][0]["command"] == "executable:tmux-server"


def test_run_load_phase_branches(tmp_path: Path) -> None:
    runner = _load_runner()
    project_root = tmp_path / "project"

    called: dict[str, str] = {}

    def _storm(opts: object, *, project_root: Path, env: dict[str, str]) -> dict[str, object]:
        del opts, env
        called["mode"] = "storm"
        return {"status": "sampled", "samples": 1, "avg_cpu_pct": 0.0, "cpu_share": 0.0, "rss_max_mib": 0.0, "procs_max": 0, "buckets": runner._empty_bucket_summary()}

    def _command(opts: object, *, project_root: Path, env: dict[str, str]) -> dict[str, object]:
        del opts, env
        called["mode"] = "command"
        return {"status": "sampled", "samples": 1, "avg_cpu_pct": 0.0, "cpu_share": 0.0, "rss_max_mib": 0.0, "procs_max": 0, "buckets": runner._empty_bucket_summary()}

    options = runner.LifecycleProfileOptions(project_root=project_root, load_command=None)
    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(runner, "_run_load_phase_with_storm", _storm)
        runner._run_load_phase(options, project_root=project_root, env={})
        assert called["mode"] == "storm"

        called.clear()
        monkeypatch.setattr(runner, "_run_load_phase_with_command", _command)
        options_cmd = runner.LifecycleProfileOptions(project_root=project_root, load_command=("echo", "hello"))
        runner._run_load_phase(options_cmd, project_root=project_root, env={})
        assert called["mode"] == "command"
    finally:
        monkeypatch.undo()


def test_default_startup_command_runs_ccb_test_from_project_root(tmp_path: Path) -> None:
    runner = _load_runner()
    ccb_test = tmp_path / "source" / "ccb_test"
    options = runner.LifecycleProfileOptions(project_root=tmp_path / "project", ccb_test_path=ccb_test)

    command = runner._build_default_startup_command(options)

    assert command == (sys.executable, str(ccb_test))


def test_run_ask_worker_uses_project_cwd_without_project_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_runner()
    project_root = tmp_path / "project"
    project_root.mkdir()
    ccb_test = tmp_path / "source" / "ccb_test"
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)

    rc = runner._run_ask_worker(
        index=2,
        project_root=project_root,
        ccb_test_path=ccb_test,
        ask_agent="agent_codex",
        ask_message="hello",
        env={"HOME": str(tmp_path)},
    )

    assert rc == 0
    assert calls[0]["cwd"] == str(project_root)
    assert calls[0]["command"] == [
        sys.executable,
        str(ccb_test),
        "ask",
        "agent_codex",
        "hello #3",
    ]
    assert "--project" not in calls[0]["command"]


def test_run_lifecycle_profile_writes_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_runner()

    startup = {
        "status": "sampled",
        "samples": 2,
        "avg_cpu_pct": 10.0,
        "cpu_share": 1.0,
        "rss_max_mib": 20.0,
        "procs_max": 3,
        "buckets": runner._empty_bucket_summary(),
    }
    load = {
        "status": "sampled",
        "samples": 3,
        "avg_cpu_pct": 20.0,
        "cpu_share": 1.0,
        "rss_max_mib": 30.0,
        "procs_max": 4,
        "buckets": runner._empty_bucket_summary(),
    }
    monkeypatch.setattr(runner, "_run_startup_phase", lambda *_args, **_kwargs: startup)
    monkeypatch.setattr(runner, "_run_load_phase", lambda *_args, **_kwargs: load)

    result_path = tmp_path / "perf_runtime_lifecycle_profile.json"
    options = runner.LifecycleProfileOptions(
        project_root=tmp_path / "project",
        result_path=result_path,
        source_home=tmp_path / "source_home",
        startup_samples=1,
        load_samples=2,
        ask_count=5,
        ask_concurrency=2,
    )
    result = runner.run_lifecycle_profile(options)
    loaded = json.loads(result_path.read_text(encoding="utf-8"))

    assert result == loaded
    assert result["phases"]["startup"]["samples"] == 2
    assert result["phases"]["load"]["samples"] == 3
    assert result["parameters"]["ask_count"] == 5
    assert result["parameters"]["ask_concurrency"] == 2
    assert result["parameters"]["ask_message_persisted"] is False
    assert "ask_message" not in result["parameters"]
    assert result["schema_version"] == 1


def test_parse_args_defaults(tmp_path: Path) -> None:
    runner = _load_runner()
    parsed = runner._parse_args(["--project-root", str(tmp_path)])
    assert parsed.project_root == tmp_path
    assert parsed.startup_samples == 20
    assert parsed.load_samples == 30
    assert parsed.ask_count == 80
    assert parsed.ask_concurrency == 12
