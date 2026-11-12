from __future__ import annotations

import pytest

from agents.models import build_pane_growth_layout, build_pane_growth_windows


def _names(count: int) -> tuple[str, ...]:
    return tuple(f'p{index}' for index in range(1, count + 1))


@pytest.mark.parametrize(
    ('count', 'expected'),
        (
            (1, 'p1'),
            (2, 'p1; p2'),
            (3, 'p1, p3; p2'),
            (4, 'p1, p3; p2, p4'),
            (5, 'p1, p3, p5; p2, p4'),
            (6, 'p1, p3, p5; p2, p4, p6'),
    ),
)
def test_build_pane_growth_layout_renders_fixed_one_to_six_order(count: int, expected: str) -> None:
    assert build_pane_growth_layout(_names(count)).render() == expected


def test_build_pane_growth_windows_overflows_after_six_panes() -> None:
    windows = build_pane_growth_windows(_names(8), window_prefix='frontdesk-dialog')

    assert [window.name for window in windows] == ['frontdesk-dialog', 'frontdesk-dialog-2']
    assert windows[0].agent_names == ('p1', 'p2', 'p3', 'p4', 'p5', 'p6')
    assert windows[0].layout_spec == 'p1, p3, p5; p2, p4, p6'
    assert windows[1].agent_names == ('p7', 'p8')
    assert windows[1].layout_spec == 'p7; p8'


def test_build_pane_growth_layout_rejects_duplicate_names() -> None:
    with pytest.raises(ValueError, match='unique'):
        build_pane_growth_layout(('p1', 'p1'))
