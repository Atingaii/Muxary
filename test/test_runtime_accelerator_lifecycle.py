from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ccbd.app_runtime.lifecycle import _runtime_accelerator_startup_actions
from runtime_accelerator.lifecycle import (
    RuntimeAcceleratorHandle,
    maybe_start_runtime_accelerator,
    stop_runtime_accelerator,
)
from runtime_accelerator.ownership import RuntimeAcceleratorOwnershipError, owner_manifest_path


class FakeProcess:
    def __init__(self) -> None:
        self.pid = 321
        self.returncode: int | None = None
        self.terminated = False
        self.killed = False

    def poll(self):
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9

    def wait(self, timeout=None):
        return self.returncode


def test_runtime_accelerator_lifecycle_can_be_disabled(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_CODEX", "0")

    handle = maybe_start_runtime_accelerator(tmp_path)

    assert handle.enabled is False
    assert handle.process is None
    assert handle.error == ""


def test_runtime_accelerator_lifecycle_is_default_on_with_fallback(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CCB_RUNTIME_ACCELERATOR_CODEX", raising=False)
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_BIN", str(tmp_path / "missing-bin"))

    handle = maybe_start_runtime_accelerator(tmp_path)

    assert handle.enabled is True
    assert handle.process is None
    assert handle.error == "missing_binary"


def test_runtime_accelerator_missing_binary_keeps_fallback(monkeypatch, tmp_path: Path) -> None:
    socket_path = tmp_path / "manual.sock"
    socket_path.write_text("", encoding="utf-8")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_CODEX", "1")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_BIN", str(tmp_path / "missing-bin"))
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_SOCKET", str(socket_path))

    handle = maybe_start_runtime_accelerator(tmp_path)
    stop_runtime_accelerator(handle)

    assert handle.enabled is True
    assert handle.process is None
    assert handle.error == "missing_binary"
    assert socket_path.exists()


def test_runtime_accelerator_start_and_stop_are_owned_by_handle(monkeypatch, tmp_path: Path) -> None:
    fake_process = FakeProcess()
    socket_path = tmp_path / ".ccb" / "runtime-accelerator" / "accelerator.sock"
    calls: dict[str, object] = {}
    events: list[str] = []

    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_CODEX", "1")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_SOCKET", str(socket_path))
    monkeypatch.setattr("runtime_accelerator.lifecycle.accelerator_binary", lambda: "/bin/fake")
    monkeypatch.setattr("runtime_accelerator.lifecycle.wait_for_socket", lambda *args, **kwargs: True)
    def fake_reclaim(project_root, *, socket_path):
        events.append("reclaim")
        calls["reclaim"] = (project_root, socket_path)
        return (111,)

    monkeypatch.setattr("runtime_accelerator.lifecycle.reclaim_runtime_accelerator", fake_reclaim)
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.record_runtime_accelerator_owner",
        lambda project_root, *, socket_path, pid: events.append("record")
        or calls.setdefault("record", (project_root, socket_path, pid)),
    )
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.load_runtime_accelerator_owner",
        lambda project_root: SimpleNamespace(pid=fake_process.pid),
    )
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.remove_runtime_accelerator_owner",
        lambda project_root, *, pid: calls.setdefault("remove", (project_root, pid)),
    )

    def fake_popen(args, **kwargs):
        events.append("popen")
        calls["args"] = args
        calls["kwargs"] = kwargs
        return fake_process

    monkeypatch.setattr("runtime_accelerator.lifecycle.subprocess.Popen", fake_popen)

    handle = maybe_start_runtime_accelerator(tmp_path)

    assert handle.started is True
    assert calls["args"] == ["/bin/fake", "serve", "--socket", str(socket_path)]
    assert calls["kwargs"]["cwd"] == str(tmp_path.resolve())
    assert calls["reclaim"] == (tmp_path.resolve(), socket_path)
    assert calls["record"] == (tmp_path.resolve(), socket_path, fake_process.pid)
    assert events == ["reclaim", "popen", "record"]
    assert handle.reclaimed_pids == (111,)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.write_text("", encoding="utf-8")

    stop_runtime_accelerator(handle)

    assert fake_process.terminated is True
    assert fake_process.killed is False
    assert calls["remove"] == (tmp_path.resolve(), fake_process.pid)
    assert not socket_path.exists()


def test_runtime_accelerator_takeover_failure_blocks_new_process(monkeypatch, tmp_path: Path) -> None:
    socket_path = tmp_path / "accelerator.sock"
    socket_path.write_text("owned", encoding="utf-8")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_CODEX", "1")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_SOCKET", str(socket_path))
    monkeypatch.setattr("runtime_accelerator.lifecycle.accelerator_binary", lambda: "/bin/fake")
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.reclaim_runtime_accelerator",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("owner_identity_mismatch")),
    )
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.subprocess.Popen",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not start after takeover failure")),
    )

    with pytest.raises(RuntimeError, match="owner_identity_mismatch"):
        maybe_start_runtime_accelerator(tmp_path)

    assert socket_path.exists()


def test_runtime_accelerator_first_start_identity_unavailable_falls_back(monkeypatch, tmp_path: Path) -> None:
    fake_process = FakeProcess()
    socket_path = tmp_path / "accelerator.sock"
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_CODEX", "1")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_SOCKET", str(socket_path))
    monkeypatch.setattr("runtime_accelerator.lifecycle.accelerator_binary", lambda: "/bin/fake")
    monkeypatch.setattr("runtime_accelerator.lifecycle.reclaim_runtime_accelerator", lambda *args, **kwargs: ())

    def fake_popen(*args, **kwargs):
        socket_path.write_text("new-sidecar", encoding="utf-8")
        return fake_process

    monkeypatch.setattr("runtime_accelerator.lifecycle.subprocess.Popen", fake_popen)
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.record_runtime_accelerator_owner",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeAcceleratorOwnershipError("runtime_accelerator_identity_unavailable:pid=321")
        ),
    )
    monkeypatch.setattr("runtime_accelerator.lifecycle.load_runtime_accelerator_owner", lambda project_root: None)
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.runtime_accelerator_socket_is_connectable",
        lambda path: False,
    )

    handle = maybe_start_runtime_accelerator(tmp_path)

    assert handle.process is None
    assert handle.error == "runtime_accelerator_identity_unavailable:pid=321"
    assert fake_process.terminated is True
    assert not socket_path.exists()
    assert not owner_manifest_path(tmp_path).exists()
    assert _runtime_accelerator_startup_actions(SimpleNamespace(runtime_accelerator=handle)) == [
        "runtime_accelerator_fallback:runtime_accelerator_identity_unavailable:pid=321"
    ]


def test_runtime_accelerator_new_sidecar_identity_mismatch_fails_closed(monkeypatch, tmp_path: Path) -> None:
    fake_process = FakeProcess()
    socket_path = tmp_path / "accelerator.sock"
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_CODEX", "1")
    monkeypatch.setenv("CCB_RUNTIME_ACCELERATOR_SOCKET", str(socket_path))
    monkeypatch.setattr("runtime_accelerator.lifecycle.accelerator_binary", lambda: "/bin/fake")
    monkeypatch.setattr("runtime_accelerator.lifecycle.reclaim_runtime_accelerator", lambda *args, **kwargs: ())
    monkeypatch.setattr("runtime_accelerator.lifecycle.subprocess.Popen", lambda *args, **kwargs: fake_process)
    monkeypatch.setattr(
        "runtime_accelerator.lifecycle.record_runtime_accelerator_owner",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeAcceleratorOwnershipError("runtime_accelerator_identity_mismatch:pid=321")
        ),
    )
    monkeypatch.setattr("runtime_accelerator.lifecycle.load_runtime_accelerator_owner", lambda project_root: None)

    with pytest.raises(RuntimeAcceleratorOwnershipError, match="identity_mismatch"):
        maybe_start_runtime_accelerator(tmp_path)

    assert fake_process.terminated is True


def test_ccbd_startup_actions_record_started_or_fallback() -> None:
    started = SimpleNamespace(runtime_accelerator=RuntimeAcceleratorHandle(True, None, process=FakeProcess()))
    fallback = SimpleNamespace(runtime_accelerator=RuntimeAcceleratorHandle(True, None, error="missing_binary"))
    disabled = SimpleNamespace(runtime_accelerator=RuntimeAcceleratorHandle(False, None))
    reclaimed = SimpleNamespace(
        runtime_accelerator=RuntimeAcceleratorHandle(True, None, process=FakeProcess(), reclaimed_pids=(101, 202))
    )

    assert _runtime_accelerator_startup_actions(started) == ["start_runtime_accelerator"]
    assert _runtime_accelerator_startup_actions(fallback) == ["runtime_accelerator_fallback:missing_binary"]
    assert _runtime_accelerator_startup_actions(disabled) == []
    assert _runtime_accelerator_startup_actions(reclaimed) == [
        "reclaim_runtime_accelerator:101,202",
        "start_runtime_accelerator",
    ]
