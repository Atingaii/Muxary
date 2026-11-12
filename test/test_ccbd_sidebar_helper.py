from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from ccbd.services.project_namespace_pane import ProjectNamespacePaneRecord
from ccbd.services.project_namespace_runtime import materialize_topology
from ccbd.services.project_namespace_runtime.sidebar_helper import (
    SIDEBAR_ENV_PATH,
    missing_sidebar_respawn_args,
    resolve_sidebar_helper,
    sidebar_helper_fingerprint,
    sidebar_respawn_args,
)


def test_resolve_sidebar_helper_prefers_explicit_env_path(tmp_path: Path) -> None:
    helper = tmp_path / 'custom-sidebar'
    helper.write_text('#!/bin/sh\n', encoding='utf-8')
    helper.chmod(0o755)

    resolution = resolve_sidebar_helper(
        env={SIDEBAR_ENV_PATH: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert resolution.path == str(helper)
    assert resolution.source == SIDEBAR_ENV_PATH


def test_resolve_sidebar_helper_finds_repository_bin(tmp_path: Path) -> None:
    helper = tmp_path / 'repo' / 'bin' / 'ccb-agent-sidebar'
    helper.parent.mkdir(parents=True)
    helper.write_text('#!/bin/sh\n', encoding='utf-8')
    helper.chmod(0o755)

    resolution = resolve_sidebar_helper(
        env={},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert resolution.path == str(helper)
    assert resolution.source == 'script_root_bin'


def test_resolve_sidebar_helper_uses_path_as_last_discovery_source(tmp_path: Path) -> None:
    resolution = resolve_sidebar_helper(
        env={},
        which=lambda name: '/usr/local/bin/ccb-agent-sidebar',
        script_root=tmp_path / 'repo',
    )

    assert resolution.path == '/usr/local/bin/ccb-agent-sidebar'
    assert resolution.source == 'PATH'


def test_sidebar_respawn_args_replaces_symbolic_binary_with_resolved_path(tmp_path: Path) -> None:
    helper = tmp_path / 'ccb-agent-sidebar'
    helper.write_text('#!/bin/sh\n', encoding='utf-8')
    helper.chmod(0o755)

    args = sidebar_respawn_args(
        ('ccb-agent-sidebar', '--pane-window', 'main'),
        env={SIDEBAR_ENV_PATH: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert args == (str(helper), '--pane-window', 'main')


def test_sidebar_respawn_args_falls_back_to_visible_keepalive_message(tmp_path: Path) -> None:
    args = sidebar_respawn_args(
        ('ccb-agent-sidebar', '--pane-window', 'main'),
        env={},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert args[:2] == ('sh', '-lc')
    assert 'CCB sidebar helper unavailable' in args[2]
    assert 'while :; do sleep 3600; done' in args[2]
    assert missing_sidebar_respawn_args()[0] == 'sh'


def test_sidebar_helper_fingerprint_tracks_runtime_binary_behind_source_wrapper(tmp_path: Path) -> None:
    root = tmp_path / 'repo'
    wrapper = root / 'bin' / 'ccb-agent-sidebar'
    runtime_binary = root / 'tools' / 'ccb-agent-sidebar' / 'target' / 'release' / 'ccb-agent-sidebar'
    wrapper.parent.mkdir(parents=True)
    runtime_binary.parent.mkdir(parents=True)
    wrapper.write_text('#!/bin/sh\n# CCB_AGENT_SIDEBAR_WRAPPER\n', encoding='utf-8')
    wrapper.chmod(0o755)
    runtime_binary.write_bytes(b'old-sidebar')

    first = sidebar_helper_fingerprint(env={}, which=lambda name: None, script_root=root)
    runtime_binary.write_bytes(b'new-sidebar')
    second = sidebar_helper_fingerprint(env={}, which=lambda name: None, script_root=root)

    assert first is not None
    assert second is not None
    assert first != second


def test_changed_sidebar_helper_respawns_only_sidebar_pane(monkeypatch, tmp_path: Path) -> None:
    pane_options = {'%1': {'@ccb_sidebar_helper_id': 'sha256:old'}}
    respawns: list[tuple[str, tuple[str, ...], str]] = []

    class Backend:
        def set_pane_user_option(self, pane_id: str, key: str, value: str) -> None:
            pane_options.setdefault(pane_id, {})[key] = value

    backend = Backend()
    controller = SimpleNamespace(_project_id='project-1', _layout=SimpleNamespace(project_root=tmp_path))
    sidebar = SimpleNamespace(launch_args=('ccb-agent-sidebar', '--pane-window', 'main'))
    topology_plan = SimpleNamespace(windows=(SimpleNamespace(name='main', sidebar=sidebar),))

    monkeypatch.setattr(materialize_topology, 'sidebar_helper_fingerprint', lambda: 'sha256:new')
    monkeypatch.setattr(materialize_topology, '_list_panes_by_user_options', lambda *_args, **_kwargs: ['%1'])
    monkeypatch.setattr(
        materialize_topology,
        'inspect_project_namespace_pane',
        lambda _backend, pane_id: ProjectNamespacePaneRecord(
            pane_id=pane_id,
            session_name='ccb-project',
            window_name='main',
            role='sidebar',
            slot_key='sidebar:main',
            ccb_window='main',
            sidebar_instance='main',
            project_id='project-1',
            managed_by='ccbd',
            namespace_epoch=7,
            alive=True,
        ),
    )
    monkeypatch.setattr(
        materialize_topology,
        '_pane_option',
        lambda _backend, pane_id, key: pane_options.get(pane_id, {}).get(key, ''),
    )
    monkeypatch.setattr(
        materialize_topology,
        '_respawn_sidebar',
        lambda _backend, pane_id, args, *, cwd: respawns.append((pane_id, args, cwd)),
    )

    materialize_topology.refresh_topology_sidebar_helpers(
        controller,
        backend,
        topology_plan=topology_plan,
        tmux_session_name='ccb-project',
        namespace_epoch=7,
    )
    materialize_topology.refresh_topology_sidebar_helpers(
        controller,
        backend,
        topology_plan=topology_plan,
        tmux_session_name='ccb-project',
        namespace_epoch=7,
    )

    assert respawns == [('%1', sidebar.launch_args, str(tmp_path))]
    assert pane_options['%1']['@ccb_sidebar_helper_id'] == 'sha256:new'


def test_current_sidebar_helper_uses_startup_snapshot_without_tmux_reads(monkeypatch, tmp_path: Path) -> None:
    controller = SimpleNamespace(_project_id='project-1', _layout=SimpleNamespace(project_root=tmp_path))
    sidebar = SimpleNamespace(launch_args=('ccb-agent-sidebar', '--pane-window', 'main'))
    topology_plan = SimpleNamespace(windows=(SimpleNamespace(name='main', sidebar=sidebar),))
    record = ProjectNamespacePaneRecord(
        pane_id='%1',
        session_name='ccb-project',
        window_name='main',
        role='sidebar',
        slot_key='sidebar:main',
        ccb_window='main',
        sidebar_instance='main',
        sidebar_helper_id='sha256:current',
        project_id='project-1',
        managed_by='ccbd',
        namespace_epoch=7,
        alive=True,
    )
    monkeypatch.setattr(materialize_topology, 'sidebar_helper_fingerprint', lambda: 'sha256:current')

    refreshed = materialize_topology.refresh_topology_sidebar_helpers(
        controller,
        object(),
        topology_plan=topology_plan,
        pane_records={'%1': record},
        tmux_session_name='ccb-project',
        namespace_epoch=7,
    )

    assert refreshed == ()
