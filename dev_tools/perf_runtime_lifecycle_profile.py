#!/usr/bin/env python3
from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import json
import os
import platform
import shlex
import statistics
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
LIB_ROOT = REPO_ROOT / 'lib'
if str(LIB_ROOT) not in sys.path:
    sys.path.insert(0, str(LIB_ROOT))

DEFAULT_RESULT_PATH = REPO_ROOT / 'dev_tools' / 'perf_results' / 'runtime_lifecycle_profile.json'
DEFAULT_CCB_TEST = REPO_ROOT / 'ccb_test'
DEFAULT_SOURCE_ROOT = Path('/home/bfly/yunwei/test_ccb2')
DEFAULT_SOURCE_HOME = DEFAULT_SOURCE_ROOT / 'source_home'

SCHEMA_VERSION = 1
DEFAULT_STARTUP_SAMPLES = 20
DEFAULT_LOAD_SAMPLES = 30
DEFAULT_SAMPLE_INTERVAL_S = 1.0
DEFAULT_ASK_COUNT = 80
DEFAULT_ASK_CONCURRENCY = 12
DEFAULT_ASK_MESSAGE = 'runtime heartbeat profiling probe'
DEFAULT_ASK_AGENT = 'agent_codex'

ALL_BUCKETS = (
    'ccb/ccbd/main',
    'ccb/keeper',
    'ccbd/sidebar',
    'provider/codex',
    'provider/claude',
    'provider/gemini',
    'provider/opencode',
    'provider/other',
    'tmux-server',
    'ask-cli-subprocess',
    'shell-wrapper',
    'terminal-frontend',
    'python-misc',
    'other-system',
)
KNOWN_PROVIDERS = ('codex', 'claude', 'gemini', 'opencode')
PROVIDER_KEYWORDS = KNOWN_PROVIDERS + ('opy', 'openai', 'native-cli')


@dataclass(frozen=True)
class LifecycleProfileOptions:
    result_path: Path = DEFAULT_RESULT_PATH
    project_root: Path | None = None
    source_root: Path = DEFAULT_SOURCE_ROOT
    source_home: Path = DEFAULT_SOURCE_HOME
    ccb_test_path: Path = DEFAULT_CCB_TEST
    startup_command: tuple[str, ...] | None = None
    load_command: tuple[str, ...] | None = None
    startup_samples: int = DEFAULT_STARTUP_SAMPLES
    load_samples: int = DEFAULT_LOAD_SAMPLES
    sample_interval_s: float = DEFAULT_SAMPLE_INTERVAL_S
    ask_count: int = DEFAULT_ASK_COUNT
    ask_concurrency: int = DEFAULT_ASK_CONCURRENCY
    ask_agent: str = DEFAULT_ASK_AGENT
    ask_message: str = DEFAULT_ASK_MESSAGE
    skip_startup: bool = False
    skip_load: bool = False
    startup_command_timeout_s: float = 60.0
    load_command_timeout_s: float = 180.0


@dataclass(frozen=True)
class SampledProcess:
    pid: int
    ppid: int
    cpu_pct: float
    rss_mib: float
    command: str
    bucket: str


@dataclass(frozen=True)
class ProcessSample:
    elapsed_s: float
    processes: tuple[SampledProcess, ...]


def _empty_bucket_summary() -> dict[str, dict[str, Any]]:
    return {
        bucket: {'samples': 0, 'avg_cpu_pct': 0.0, 'cpu_share': 0.0, 'rss_max_mib': 0.0, 'procs_max': 0}
        for bucket in ALL_BUCKETS
    }


def _default_skipped_phase(reason: str) -> dict[str, Any]:
    return {
        'status': 'skipped',
        'reason': reason,
        'samples': 0,
        'avg_cpu_pct': 0.0,
        'cpu_share': 0.0,
        'rss_max_mib': 0.0,
        'procs_max': 0,
        'buckets': _empty_bucket_summary(),
    }


def classify_process(
    command: str,
    *,
    command_basename: str,
    in_project: bool = False,
    scope_to_project: bool = False,
) -> str:
    text = (command or '').lower()
    name = command_basename.lower()

    if scope_to_project and not in_project:
        return 'other-system'

    if '/ccbd/main.py' in text or 'ccbd/main.py' in text or 'lib/ccbd/main.py' in text:
        return 'ccb/ccbd/main'
    if 'ccbd/keeper_main.py' in text or 'keeper_main.py' in text:
        return 'ccb/keeper'
    if 'ccbd/sidebar' in text or 'ccbd/sidecar_sidebar' in text or 'sidecar-sidebar' in text:
        return 'ccbd/sidebar'

    tokenized = text.split()
    has_ccb_invocation = any(
        token == 'ccb'
        or token == 'ccb_test'
        or token.endswith('/ccb')
        or token.endswith('/ccb_test')
        or token.endswith('\\ccb')
        or token.endswith('\\ccb_test')
        for token in tokenized
    )
    if has_ccb_invocation and 'ask' in tokenized:
        return 'ask-cli-subprocess'

    if 'tmux' in text and ('send-keys' in text or 'attach' in text or 'source-file' in text):
        return 'terminal-frontend'
    if ((' tmux ' in f' {text} ') or name.startswith('tmux')) and ('server' in text or 'tmux' in name):
        return 'tmux-server'

    for provider in KNOWN_PROVIDERS:
        marker = f'/{provider}/'
        provider_runtime_marker = f'provider-runtime/{provider}'
        provider_state_marker = f'provider-state/{provider}'
        if marker in text and ('provider-state' in text or 'provider-runtime' in text):
            return f'provider/{provider}'
        if provider_runtime_marker in text or provider_state_marker in text:
            return f'provider/{provider}'
        if f'provider/{provider}' in text or f'provider-{provider}' in text or f'{provider}-provider' in text:
            return f'provider/{provider}'
        if _command_uses_binary(text, provider):
            return f'provider/{provider}'
        if f' {provider} ' in f' {text} ':
            return f'provider/{provider}'

    if name in {'sh', 'bash', 'zsh'} or '-lc' in text or ' sh -c ' in f' {text} ':
        return 'shell-wrapper'

    if ('python' in name or name.endswith('.py')) and in_project:
        return 'python-misc'
    if in_project and any(token in text for token in PROVIDER_KEYWORDS):
        return 'provider/other'

    return 'other-system'


def _command_uses_binary(command: str, binary_name: str) -> bool:
    for token in str(command or '').split():
        cleaned = token.strip("'\"")
        if Path(cleaned).name == binary_name:
            return True
    return False


def _command_basename(raw: str) -> str:
    text = (raw or '').strip()
    if not text:
        return ''
    return Path(text.split()[0]).name


def _parse_ps_output(output: str) -> tuple[tuple[int, int, float, float, str], ...]:
    records: list[tuple[int, int, float, float, str]] = []
    for line in output.splitlines():
        parts = line.strip().split(None, 5)
        if len(parts) < 6:
            continue
        pid_text, ppid_text, cpu_text, rss_text, _vsz_text, command = parts
        try:
            pid = int(pid_text)
            ppid = int(ppid_text)
        except ValueError:
            continue
        try:
            cpu_pct = float(cpu_text)
        except ValueError:
            cpu_pct = 0.0
        try:
            rss_mib = float(rss_text) / 1024.0
        except ValueError:
            rss_mib = 0.0
        records.append((pid, ppid, cpu_pct, rss_mib, command))
    return tuple(records)


def _collect_process_snapshot() -> tuple[tuple[int, int, float, float, str], ...]:
    try:
        completed = subprocess.run(
            ['ps', '-eo', 'pid=,ppid=,pcpu=,rss=,vsz=,args='],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1.0,
        )
    except Exception:
        return ()
    if completed.returncode != 0:
        return ()
    return _parse_ps_output(completed.stdout)


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        resolved_path = path.resolve()
        resolved_root = root.resolve()
    except Exception:
        resolved_path = path.absolute()
        resolved_root = root.absolute()
    return resolved_path == resolved_root or resolved_root in resolved_path.parents


def _pid_cwd_under_project(pid: int, project_root: Path) -> bool:
    cwd_link = Path('/proc') / str(pid) / 'cwd'
    try:
        cwd = cwd_link.resolve()
    except Exception:
        return False
    return _path_is_under(cwd, project_root)


def _project_related_pids(
    process_rows: tuple[tuple[int, int, float, float, str], ...],
    project_root: Path | None,
) -> set[int]:
    if project_root is None:
        return set()
    project_root_text = str(project_root).lower()
    rows_by_pid = {pid: (ppid, command) for pid, ppid, _cpu_pct, _rss_mib, command in process_rows}
    related: set[int] = set()
    for pid, (_ppid, command) in rows_by_pid.items():
        text = (command or '').lower()
        if project_root_text and project_root_text in text:
            related.add(pid)
            continue
        if _pid_cwd_under_project(pid, project_root):
            related.add(pid)

    changed = True
    while changed:
        changed = False
        for pid, (ppid, _command) in rows_by_pid.items():
            if pid not in related and ppid in related:
                related.add(pid)
                changed = True
    return related


def _collect_phase_samples(
    *,
    is_active: Callable[[], bool],
    max_samples: int,
    interval_s: float,
    project_root: Path | None = None,
) -> list[ProcessSample]:
    samples: list[ProcessSample] = []
    start = time.perf_counter()
    remaining = max(1, max_samples)
    profile_pid = os.getpid()
    for _ in range(remaining):
        elapsed = time.perf_counter() - start
        process_rows = _collect_process_snapshot()
        project_pids = _project_related_pids(process_rows, project_root)
        snapshot_rows: list[SampledProcess] = []
        for pid, ppid, cpu_pct, rss_mib, command in process_rows:
            if pid == profile_pid or _is_sampler_process(command):
                continue
            in_project = project_root is not None and pid in project_pids
            if project_root is not None and not in_project:
                continue
            bucket = classify_process(
                command,
                command_basename=_command_basename(command),
                in_project=in_project,
                scope_to_project=project_root is not None,
            )
            snapshot_rows.append(
                SampledProcess(
                    pid=pid,
                    ppid=ppid,
                    cpu_pct=cpu_pct,
                    rss_mib=rss_mib,
                    command=command,
                    bucket=bucket,
                )
            )
        samples.append(ProcessSample(elapsed_s=elapsed, processes=tuple(snapshot_rows)))
        if not is_active():
            break
        if _ == remaining - 1:
            break
        time.sleep(max(0.0, interval_s))
    return samples


def _is_sampler_process(command: str) -> bool:
    return str(command or '').strip().startswith('ps -eo pid=,ppid=,pcpu=,rss=,vsz=,args=')


def _aggregate_phase(samples: list[ProcessSample]) -> dict[str, Any]:
    if not samples:
        phase_summary = _default_skipped_phase('no_samples')
        phase_summary['status'] = 'sampled'
        return phase_summary

    per_bucket_cpu: dict[str, list[float]] = {bucket: [] for bucket in ALL_BUCKETS}
    per_bucket_rss: dict[str, list[float]] = {bucket: [] for bucket in ALL_BUCKETS}
    per_bucket_proc_counts: dict[str, list[int]] = {bucket: [] for bucket in ALL_BUCKETS}
    per_bucket_command_cpu: dict[str, dict[str, float]] = {bucket: {} for bucket in ALL_BUCKETS}
    per_bucket_command_rss: dict[str, dict[str, float]] = {bucket: {} for bucket in ALL_BUCKETS}
    per_bucket_command_pids: dict[str, dict[str, set[int]]] = {bucket: {} for bucket in ALL_BUCKETS}
    total_cpu_by_sample: list[float] = []
    total_rss_by_sample: list[float] = []
    total_proc_count_by_sample: list[int] = []

    for sample in samples:
        totals: dict[str, float] = {bucket: 0.0 for bucket in ALL_BUCKETS}
        pids: dict[str, set[int]] = {bucket: set() for bucket in ALL_BUCKETS}
        rss_totals: dict[str, float] = {bucket: 0.0 for bucket in ALL_BUCKETS}
        for proc in sample.processes:
            bucket = proc.bucket if proc.bucket in ALL_BUCKETS else 'other-system'
            totals[bucket] += proc.cpu_pct
            rss_totals[bucket] += proc.rss_mib
            pids[bucket].add(proc.pid)
            command_key = _summarize_command(proc.command)
            per_bucket_command_cpu[bucket][command_key] = per_bucket_command_cpu[bucket].get(command_key, 0.0) + proc.cpu_pct
            per_bucket_command_rss[bucket][command_key] = max(
                per_bucket_command_rss[bucket].get(command_key, 0.0),
                proc.rss_mib,
            )
            per_bucket_command_pids[bucket].setdefault(command_key, set()).add(proc.pid)
        total_cpu_by_sample.append(sum(totals.values()))
        total_rss_by_sample.append(sum(rss_totals.values()))
        total_proc_count_by_sample.append(sum(len(pid_set) for pid_set in pids.values()))
        for bucket in ALL_BUCKETS:
            per_bucket_cpu[bucket].append(round(totals[bucket], 6))
            per_bucket_rss[bucket].append(round(rss_totals[bucket], 6))
            per_bucket_proc_counts[bucket].append(len(pids[bucket]))

    avg_total_cpu = statistics.fmean(total_cpu_by_sample) if total_cpu_by_sample else 0.0
    buckets_summary: dict[str, Any] = {}
    for bucket in ALL_BUCKETS:
        avg_cpu = statistics.fmean(per_bucket_cpu[bucket]) if per_bucket_cpu[bucket] else 0.0
        buckets_summary[bucket] = {
            'samples': len(per_bucket_cpu[bucket]),
            'avg_cpu_pct': round(avg_cpu, 6),
            'cpu_share': round((avg_cpu / avg_total_cpu) if avg_total_cpu > 0 else 0.0, 6),
            'rss_max_mib': round(max(per_bucket_rss[bucket], default=0.0), 3),
            'procs_max': max(per_bucket_proc_counts[bucket], default=0),
            'top_commands': _top_bucket_commands(
                per_bucket_command_cpu[bucket],
                per_bucket_command_rss[bucket],
                per_bucket_command_pids[bucket],
                sample_count=len(samples),
            ),
        }

    return {
        'status': 'sampled',
        'samples': len(samples),
        'avg_cpu_pct': round(avg_total_cpu, 6),
        'cpu_share': 1.0 if avg_total_cpu > 0 else 0.0,
        'rss_max_mib': round(max(total_rss_by_sample, default=0.0), 3),
        'procs_max': max(total_proc_count_by_sample, default=0),
        'buckets': buckets_summary,
    }


def _summarize_command(command: str, *, limit: int = 240) -> str:
    del limit
    text = ' '.join(str(command or '').split())
    if not text:
        return 'executable:<unknown>'
    if text.lower().startswith('tmux: server'):
        return 'executable:tmux-server'
    tokens = text.split()
    executable = Path(tokens[0].strip("'\"")).name or '<unknown>'
    if executable.startswith('python') and len(tokens) > 1:
        script = Path(tokens[1].strip("'\"")).name
        if script and not script.startswith('-'):
            return f'executable:{executable}:{script}'
    return f'executable:{executable}'


def _top_bucket_commands(
    cpu_by_command: dict[str, float],
    rss_by_command: dict[str, float],
    pids_by_command: dict[str, set[int]],
    *,
    sample_count: int,
    limit: int = 8,
) -> list[dict[str, Any]]:
    if sample_count <= 0:
        return []
    rows: list[dict[str, Any]] = []
    for command, cpu_sum in sorted(cpu_by_command.items(), key=lambda item: item[1], reverse=True)[:limit]:
        rows.append(
            {
                'command': command,
                'avg_cpu_pct': round(cpu_sum / sample_count, 6),
                'rss_max_mib': round(rss_by_command.get(command, 0.0), 3),
                'pids_seen': len(pids_by_command.get(command, set())),
            }
        )
    return rows


def _build_default_startup_command(options: LifecycleProfileOptions) -> tuple[str, ...] | None:
    if options.project_root is None:
        return None
    if options.startup_command is not None:
        return options.startup_command
    return (sys.executable, str(options.ccb_test_path))


def _run_startup_phase(options: LifecycleProfileOptions, *, project_root: Path, env: dict[str, str]) -> dict[str, Any]:
    command = _build_default_startup_command(options)
    if command is None:
        return _default_skipped_phase('no_startup_command')

    start = time.perf_counter()
    command_timeout_s = options.startup_command_timeout_s if options.startup_command_timeout_s > 0 else float('inf')
    proc = None
    terminated_by_profile = False
    try:
        proc = subprocess.Popen(
            list(command),
            cwd=str(project_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        samples = _collect_phase_samples(
            is_active=lambda: (time.perf_counter() - start) < command_timeout_s,
            max_samples=max(1, options.startup_samples),
            interval_s=options.sample_interval_s,
            project_root=project_root,
        )
    finally:
        if proc is not None and proc.poll() is None:
            terminated_by_profile = True
            proc.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired, OSError):
                proc.wait(timeout=3)
            if proc.poll() is None:
                with contextlib.suppress(OSError):
                    proc.kill()

    elapsed = round(time.perf_counter() - start, 6)
    timed_out = elapsed >= command_timeout_s
    summary = _aggregate_phase(samples)
    summary['command'] = {
        'kind': 'startup_subprocess',
        'executable': Path(command[0]).name if command else None,
        'argv_persisted': False,
    }
    summary['metadata'] = {
        'samples_requested': max(1, options.startup_samples),
        'sample_interval_s': options.sample_interval_s,
        'elapsed_s': elapsed,
        'command_exit_code': proc.returncode if proc is not None else None,
        'terminated_by_profile': terminated_by_profile,
        'timed_out': timed_out,
    }
    return summary


def _run_ask_worker(
    *,
    index: int,
    project_root: Path,
    ccb_test_path: Path,
    ask_agent: str,
    ask_message: str,
    env: dict[str, str],
    timeout_s: float = 45.0,
) -> int:
    command = [
        sys.executable,
        str(ccb_test_path),
        'ask',
        ask_agent,
        f'{ask_message} #{index + 1}',
    ]
    proc = subprocess.run(
        command,
        cwd=str(project_root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout_s,
        text=True,
    )
    return proc.returncode


def _load_storm_loop(options: LifecycleProfileOptions, env: dict[str, str], *, project_root: Path) -> None:
    if options.ask_count <= 0:
        return
    workers = max(1, options.ask_concurrency)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                _run_ask_worker,
                index=index,
                project_root=project_root,
                ccb_test_path=options.ccb_test_path,
                ask_agent=options.ask_agent,
                ask_message=options.ask_message,
                env=env,
            )
            for index in range(max(0, options.ask_count))
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()


def _run_load_phase_with_storm(options: LifecycleProfileOptions, *, project_root: Path, env: dict[str, str]) -> dict[str, Any]:
    start = time.perf_counter()
    load_finished = threading.Event()

    def _run_load() -> None:
        try:
            _load_storm_loop(options, env, project_root=project_root)
        finally:
            load_finished.set()

    worker = threading.Thread(target=_run_load, name='ccb-load-storm', daemon=True)
    worker.start()
    samples = _collect_phase_samples(
        is_active=lambda: not load_finished.is_set(),
        max_samples=max(1, options.load_samples),
        interval_s=options.sample_interval_s,
        project_root=project_root,
    )
    worker.join(timeout=options.load_command_timeout_s)
    elapsed = round(time.perf_counter() - start, 6)

    summary = _aggregate_phase(samples)
    summary['command'] = {
        'kind': 'load_storm',
        'ask_count': options.ask_count,
        'ask_concurrency': options.ask_concurrency,
        'ask_agent': options.ask_agent,
        'message_bytes': len(options.ask_message.encode('utf-8')),
        'message_persisted': False,
    }
    summary['metadata'] = {
        'samples_requested': max(1, options.load_samples),
        'sample_interval_s': options.sample_interval_s,
        'elapsed_s': elapsed,
        'timed_out': worker.is_alive(),
    }
    return summary


def _run_load_phase_with_command(
    options: LifecycleProfileOptions,
    *,
    project_root: Path,
    env: dict[str, str],
) -> dict[str, Any]:
    if options.load_command is None:
        return _default_skipped_phase('missing_load_command')

    start = time.perf_counter()
    process = None
    terminated_by_profile = False
    try:
        process = subprocess.Popen(
            list(options.load_command),
            cwd=str(project_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        samples = _collect_phase_samples(
            is_active=lambda: process is not None and process.poll() is None,
            max_samples=max(1, options.load_samples),
            interval_s=options.sample_interval_s,
            project_root=project_root,
        )
    finally:
        if process is not None and process.poll() is None:
            terminated_by_profile = True
            process.terminate()
            with contextlib.suppress(subprocess.TimeoutExpired, OSError):
                process.wait(timeout=3)
            if process.poll() is None:
                with contextlib.suppress(OSError):
                    process.kill()

    elapsed = round(time.perf_counter() - start, 6)
    summary = _aggregate_phase(samples)
    summary['command'] = {
        'kind': 'load_subprocess',
        'executable': Path(options.load_command[0]).name if options.load_command else None,
        'argv_persisted': False,
    }
    summary['metadata'] = {
        'samples_requested': max(1, options.load_samples),
        'sample_interval_s': options.sample_interval_s,
        'elapsed_s': elapsed,
        'command_exit_code': process.returncode if process is not None else None,
        'terminated_by_profile': terminated_by_profile,
    }
    return summary


def _run_load_phase(options: LifecycleProfileOptions, *, project_root: Path, env: dict[str, str]) -> dict[str, Any]:
    if options.skip_load:
        return _default_skipped_phase('load_skipped')
    if options.load_command is None:
        return _run_load_phase_with_storm(options, project_root=project_root, env=env)
    return _run_load_phase_with_command(options, project_root=project_root, env=env)


def _coerce_command(value: str | None) -> tuple[str, ...] | None:
    if value is None:
        return None
    parts = tuple(shlex.split(value))
    return parts if parts else None


def _build_profile_env(options: LifecycleProfileOptions) -> dict[str, str]:
    env = dict(os.environ)
    env['HOME'] = str(options.source_home)
    env['CCB_SOURCE_HOME'] = str(options.source_home)
    env.pop('CCB_SOURCE_RUNTIME_OK', None)
    return env


def run_lifecycle_profile(options: LifecycleProfileOptions) -> dict[str, Any]:
    project_root = options.project_root
    if project_root is None:
        raise ValueError('project_root is required for lifecycle profile')

    env = _build_profile_env(options)
    result: dict[str, Any] = {
        'schema_version': SCHEMA_VERSION,
        'plan': 'ccb-runtime-performance',
        'phase': 'runtime_lifecycle_profile_v1',
        'generated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'repo_root': str(REPO_ROOT),
        'result_path': str(options.result_path),
        'source_runtime_root': str(options.source_root),
        'source_home': str(options.source_home),
        'project_root': str(project_root),
        'sample_interval_s': options.sample_interval_s,
        'parameters': {
            'startup_samples': options.startup_samples,
            'load_samples': options.load_samples,
            'ask_count': options.ask_count,
            'ask_concurrency': options.ask_concurrency,
            'ask_agent': options.ask_agent,
            'ask_message_bytes': len(options.ask_message.encode('utf-8')),
            'ask_message_persisted': False,
            'skip_startup': options.skip_startup,
            'skip_load': options.skip_load,
            'startup_command_timeout_s': options.startup_command_timeout_s,
            'load_command_timeout_s': options.load_command_timeout_s,
        },
        'python': {
            'version': platform.python_version(),
            'executable': sys.executable,
        },
        'platform': {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
        },
    }

    startup = _default_skipped_phase('skip_startup') if options.skip_startup else _run_startup_phase(
        options,
        project_root=project_root,
        env=env,
    )
    load = _default_skipped_phase('skip_load') if options.skip_load else _run_load_phase(
        options,
        project_root=project_root,
        env=env,
    )
    startup.setdefault('status', 'sampled')
    load.setdefault('status', 'sampled')

    result['phases'] = {
        'startup': startup,
        'load': load,
    }
    options.result_path.parent.mkdir(parents=True, exist_ok=True)
    options.result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return result


def _parse_args(argv: list[str]) -> LifecycleProfileOptions:
    parser = argparse.ArgumentParser(description='Run CCB runtime lifecycle CPU/CPU-share profiling slices.')
    parser.add_argument('--result-path', type=Path, default=DEFAULT_RESULT_PATH)
    parser.add_argument('--project-root', type=Path, default=None)
    parser.add_argument('--source-root', type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument('--source-home', type=Path, default=DEFAULT_SOURCE_HOME)
    parser.add_argument('--ccb-test', type=Path, default=DEFAULT_CCB_TEST)
    parser.add_argument('--startup-command', default=None)
    parser.add_argument('--load-command', default=None)
    parser.add_argument('--startup-samples', type=int, default=DEFAULT_STARTUP_SAMPLES)
    parser.add_argument('--load-samples', type=int, default=DEFAULT_LOAD_SAMPLES)
    parser.add_argument('--sample-interval-s', type=float, default=DEFAULT_SAMPLE_INTERVAL_S)
    parser.add_argument('--ask-count', type=int, default=DEFAULT_ASK_COUNT)
    parser.add_argument('--ask-concurrency', type=int, default=DEFAULT_ASK_CONCURRENCY)
    parser.add_argument('--ask-agent', default=DEFAULT_ASK_AGENT)
    parser.add_argument('--ask-message', default=DEFAULT_ASK_MESSAGE)
    parser.add_argument('--skip-startup', action='store_true')
    parser.add_argument('--skip-load', action='store_true')
    parser.add_argument('--startup-command-timeout-s', type=float, default=60.0)
    parser.add_argument('--load-command-timeout-s', type=float, default=180.0)

    args = parser.parse_args(argv)
    startup_command = _coerce_command(args.startup_command)
    load_command = _coerce_command(args.load_command)
    return LifecycleProfileOptions(
        result_path=args.result_path,
        project_root=args.project_root,
        source_root=args.source_root,
        source_home=args.source_home,
        ccb_test_path=args.ccb_test,
        startup_command=startup_command,
        load_command=load_command,
        startup_samples=args.startup_samples,
        load_samples=args.load_samples,
        sample_interval_s=args.sample_interval_s,
        ask_count=args.ask_count,
        ask_concurrency=args.ask_concurrency,
        ask_agent=args.ask_agent,
        ask_message=args.ask_message,
        skip_startup=args.skip_startup,
        skip_load=args.skip_load,
        startup_command_timeout_s=args.startup_command_timeout_s,
        load_command_timeout_s=args.load_command_timeout_s,
    )


def main(argv: list[str] | None = None) -> int:
    options = _parse_args(list(argv or sys.argv[1:]))
    result = run_lifecycle_profile(options)
    print(
        json.dumps(
            {'schema_version': result['schema_version'], 'result_path': result['result_path'], 'phases': result['phases']},
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
