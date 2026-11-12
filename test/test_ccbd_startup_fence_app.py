from __future__ import annotations

from pathlib import Path

import pytest

from ccbd.app import CcbdApp
from ccbd.models import CcbdStartupReport, MountState
from ccbd.services.lifecycle import build_lifecycle
from ccbd.startup_fence import ExpectedStartupFence, StartupFenceError


STARTUP_ID = 'a' * 32


def _app(tmp_path: Path, *, startup_id: str = STARTUP_ID, generation: int = 7) -> CcbdApp:
    project_root = tmp_path / 'repo'
    config_path = project_root / '.ccb' / 'ccb.config'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('agent1:codex\n', encoding='utf-8')
    return CcbdApp(
        project_root,
        pid=2222,
        expected_startup_fence=ExpectedStartupFence(
            startup_id=startup_id,
            generation=generation,
        ),
    )


def _starting_lifecycle(app: CcbdApp, *, startup_id: str, generation: int):
    return build_lifecycle(
        project_id=app.project_id,
        occurred_at='2026-07-17T00:00:00Z',
        desired_state='running',
        phase='starting',
        generation=generation,
        startup_id=startup_id,
        startup_stage='spawn_requested',
        last_progress_at='2026-07-17T00:00:00Z',
        startup_deadline_at='2026-07-17T00:01:00Z',
        config_signature=str(app.config_identity['config_signature']),
        socket_path=app.paths.ccbd_socket_path,
    )


def test_fenced_child_claims_keeper_generation_when_lease_is_missing(tmp_path: Path) -> None:
    app = _app(tmp_path, generation=7)
    app.lifecycle_store.save(
        _starting_lifecycle(app, startup_id=STARTUP_ID, generation=7)
    )
    try:
        lease = app.start()

        lifecycle = app.lifecycle_store.load()
        assert lease.generation == 7
        assert lease.ccbd_pid == app.pid
        assert lease.daemon_instance_id == app.daemon_instance_id
        assert lifecycle is not None
        assert lifecycle.phase == 'starting'
        assert lifecycle.startup_stage == 'runtime_bootstrap'
        assert lifecycle.generation == 7
        assert lifecycle.startup_id == STARTUP_ID
    finally:
        if app.lease is not None:
            app.release_backend_ownership()


def test_fenced_child_rejects_superseded_transaction_before_lease_or_socket_mutation(
    tmp_path: Path,
) -> None:
    app = _app(tmp_path, startup_id=STARTUP_ID, generation=7)
    superseding = _starting_lifecycle(app, startup_id='b' * 32, generation=8)
    app.lifecycle_store.save(superseding)
    lifecycle_bytes = app.paths.ccbd_lifecycle_path.read_bytes()
    assert app.mount_manager.load_state() is None
    assert not app.paths.ccbd_socket_path.exists()

    with pytest.raises(StartupFenceError, match='startup_id mismatch'):
        app.serve_forever(poll_interval=0.01)

    assert app.lease is None
    assert app.mount_manager.load_state() is None
    assert app.paths.ccbd_lifecycle_path.read_bytes() == lifecycle_bytes
    assert not app.paths.ccbd_socket_path.exists()


def test_unfenced_child_rejects_keeper_owned_startup_transaction(tmp_path: Path) -> None:
    project_root = tmp_path / 'repo-unfenced-keeper-transaction'
    config_path = project_root / '.ccb' / 'ccb.config'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('agent1:codex\n', encoding='utf-8')
    app = CcbdApp(project_root)
    lifecycle = build_lifecycle(
        project_id=app.project_id,
        occurred_at='2026-07-17T00:00:00Z',
        desired_state='running',
        phase='starting',
        generation=7,
        startup_id=STARTUP_ID,
        startup_stage='spawn_requested',
        keeper_pid=3333,
        config_signature=str(app.config_identity['config_signature']),
        socket_path=app.paths.ccbd_socket_path,
    )
    app.lifecycle_store.save(lifecycle)
    lifecycle_bytes = app.paths.ccbd_lifecycle_path.read_bytes()

    with pytest.raises(StartupFenceError, match='requires an expected startup fence'):
        app.start()

    assert app.paths.ccbd_lifecycle_path.read_bytes() == lifecycle_bytes
    assert app.mount_manager.load_state() is None
    assert app.startup_report_store.load() is None
    assert not app.paths.ccbd_socket_path.exists()


def test_unfenced_child_progress_cannot_overwrite_newer_generation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    project_root = tmp_path / 'repo-unfenced-progress-fence'
    config_path = project_root / '.ccb' / 'ccb.config'
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text('agent1:codex\n', encoding='utf-8')
    app = CcbdApp(project_root)
    superseding = build_lifecycle(
        project_id=app.project_id,
        occurred_at='2026-07-17T00:00:01Z',
        desired_state='running',
        phase='starting',
        generation=2,
        startup_stage='socket_listening',
        owner_pid=9999,
        owner_daemon_instance_id='newer-daemon',
        config_signature=str(app.config_identity['config_signature']),
        socket_path=app.paths.ccbd_socket_path,
    )
    original_save = app.lifecycle_store.save
    superseded = False

    def supersede_after_claim(lifecycle) -> None:
        nonlocal superseded
        original_save(lifecycle)
        if (
            not superseded
            and lifecycle.phase == 'starting'
            and lifecycle.startup_stage == 'socket_listening'
            and lifecycle.owner_daemon_instance_id == app.daemon_instance_id
        ):
            superseded = True
            original_save(superseding)

    monkeypatch.setattr(app.lifecycle_store, 'save', supersede_after_claim)

    with pytest.raises(StartupFenceError, match='generation mismatch'):
        app.start()

    assert app.lifecycle_store.load() == superseding
    assert app.mount_manager.load_state() is None
    assert app.startup_report_store.load() is None
    assert not app.paths.ccbd_socket_path.exists()


def test_fenced_child_claim_conflict_leaves_lifecycle_and_lease_unchanged(
    tmp_path: Path,
) -> None:
    app = _app(tmp_path, startup_id=STARTUP_ID, generation=7)
    app.lifecycle_store.save(
        _starting_lifecycle(app, startup_id=STARTUP_ID, generation=7)
    )
    app.mount_manager.mark_mounted(
        project_id=app.project_id,
        pid=3333,
        socket_path=app.paths.ccbd_socket_path,
        generation=7,
        config_signature=str(app.config_identity['config_signature']),
        daemon_instance_id='other-daemon',
    )
    lifecycle_bytes = app.paths.ccbd_lifecycle_path.read_bytes()
    lease_bytes = app.paths.ccbd_lease_path.read_bytes()

    with pytest.raises(RuntimeError, match='already held or superseded'):
        app.start()

    assert app.lease is None
    assert app.paths.ccbd_lifecycle_path.read_bytes() == lifecycle_bytes
    assert app.paths.ccbd_lease_path.read_bytes() == lease_bytes
    assert not app.paths.ccbd_socket_path.exists()

def test_fenced_child_preserves_superseding_transaction_during_restore(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = _app(tmp_path, startup_id=STARTUP_ID, generation=7)
    app.lifecycle_store.save(
        _starting_lifecycle(app, startup_id=STARTUP_ID, generation=7)
    )
    superseding = _starting_lifecycle(app, startup_id='b' * 32, generation=8)

    def supersede_startup() -> None:
        app.lifecycle_store.save(superseding)

    monkeypatch.setattr(app.dispatcher, 'restore_running_jobs', supersede_startup)

    with pytest.raises(StartupFenceError, match='startup_id mismatch'):
        app.serve_forever(poll_interval=0.01)

    lifecycle = app.lifecycle_store.load()
    lease = app.mount_manager.load_state()
    assert lifecycle == superseding
    assert lease is not None
    assert lease.generation == 7
    assert lease.mount_state is MountState.UNMOUNTED
    assert app.lease == lease
    assert not app.paths.ccbd_socket_path.exists()


def test_superseded_child_cannot_overwrite_newer_startup_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = _app(tmp_path, startup_id=STARTUP_ID, generation=7)
    app.lifecycle_store.save(
        _starting_lifecycle(app, startup_id=STARTUP_ID, generation=7)
    )
    superseding = _starting_lifecycle(app, startup_id='b' * 32, generation=8)
    newer_report = CcbdStartupReport(
        project_id=app.project_id,
        generated_at='2026-07-17T00:00:08Z',
        trigger='daemon_boot',
        status='ok',
        requested_agents=(),
        desired_agents=('agent1',),
        restore_requested=False,
        auto_permission=False,
        daemon_generation=8,
        daemon_started=True,
        inspection={'startup_id': 'b' * 32},
    )

    def publish_superseding_startup() -> None:
        app.lifecycle_store.save(superseding)
        app.startup_report_store.save(newer_report)

    monkeypatch.setattr(app.dispatcher, 'restore_running_jobs', publish_superseding_startup)

    with pytest.raises(StartupFenceError, match='startup_id mismatch'):
        app.serve_forever(poll_interval=0.01)

    assert app.lifecycle_store.load() == superseding
    assert app.startup_report_store.load().to_record() == newer_report.to_record()


def test_fenced_child_honors_concurrent_stop_during_restore(
    tmp_path: Path,
    monkeypatch,
) -> None:
    app = _app(tmp_path, startup_id=STARTUP_ID, generation=7)
    starting = _starting_lifecycle(app, startup_id=STARTUP_ID, generation=7)
    app.lifecycle_store.save(starting)

    def request_stop() -> None:
        app.lifecycle_store.save(
            starting.with_phase(
                'stopping',
                occurred_at='2026-07-17T00:00:01Z',
                desired_state='stopped',
                startup_stage=None,
                shutdown_intent='operator_stop',
            )
        )

    monkeypatch.setattr(app.dispatcher, 'restore_running_jobs', request_stop)

    with pytest.raises(StartupFenceError, match='desired_state is not running'):
        app.serve_forever(poll_interval=0.01)

    lifecycle = app.lifecycle_store.load()
    lease = app.mount_manager.load_state()
    assert lifecycle is not None
    assert lifecycle.startup_id == STARTUP_ID
    assert lifecycle.generation == 7
    assert lifecycle.desired_state == 'stopped'
    assert lifecycle.phase == 'unmounted'
    assert lifecycle.shutdown_intent == 'operator_stop'
    assert lifecycle.last_failure_reason is None
    assert lease is not None
    assert lease.mount_state is MountState.UNMOUNTED
    assert app.lease == lease
    assert not app.paths.ccbd_socket_path.exists()
