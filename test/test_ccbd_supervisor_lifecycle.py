from __future__ import annotations

from types import SimpleNamespace

from ccbd.supervisor_runtime.lifecycle import _uses_explicit_windows_topology


def test_supervisor_uses_topology_for_explicit_windows_config() -> None:
    assert _uses_explicit_windows_topology(
        SimpleNamespace(windows_explicit=True),
        interactive_tmux_layout=True,
    ) is True


def test_supervisor_uses_topology_for_legacy_config_with_default_sidebar() -> None:
    assert _uses_explicit_windows_topology(
        SimpleNamespace(
            windows_explicit=False,
            sidebar=SimpleNamespace(mode='every_window'),
            tool_windows=(),
        ),
        interactive_tmux_layout=True,
    ) is True


def test_supervisor_skips_topology_when_sidebar_is_off_for_legacy_config() -> None:
    assert _uses_explicit_windows_topology(
        SimpleNamespace(
            windows_explicit=False,
            sidebar=SimpleNamespace(mode='off'),
            tool_windows=(),
        ),
        interactive_tmux_layout=True,
    ) is False


def test_supervisor_skips_topology_without_interactive_layout() -> None:
    assert _uses_explicit_windows_topology(
        SimpleNamespace(windows_explicit=True),
        interactive_tmux_layout=False,
    ) is False
