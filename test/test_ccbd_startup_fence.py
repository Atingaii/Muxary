from __future__ import annotations

from pathlib import Path

import pytest

from ccbd.services.lifecycle import build_lifecycle
from ccbd.startup_fence import (
    EXPECTED_GENERATION_ENV,
    EXPECTED_STARTUP_ID_ENV,
    KEEPER_STARTUP_ACCEPTED_PERF_COUNTER_NS_ENV,
    ExpectedStartupFence,
    KeeperStartupCheckpoint,
    StartupFenceError,
    consume_expected_startup_fence,
    consume_keeper_startup_checkpoint,
    validate_expected_startup_lifecycle,
)


STARTUP_ID = 'a' * 32


def test_consume_expected_startup_fence_removes_private_environment() -> None:
    environ = {
        EXPECTED_STARTUP_ID_ENV: STARTUP_ID,
        EXPECTED_GENERATION_ENV: '7',
        'KEEP': 'value',
    }

    fence = consume_expected_startup_fence(environ)

    assert fence == ExpectedStartupFence(startup_id=STARTUP_ID, generation=7)
    assert environ == {'KEEP': 'value'}


def test_consume_expected_startup_fence_allows_legacy_absence() -> None:
    assert consume_expected_startup_fence({}) is None


def test_consume_keeper_startup_checkpoint_is_one_shot_and_identity_bound() -> None:
    environ = {
        KEEPER_STARTUP_ACCEPTED_PERF_COUNTER_NS_ENV: '1234567',
        'KEEP': 'value',
    }
    fence = ExpectedStartupFence(startup_id=STARTUP_ID, generation=7)

    checkpoint = consume_keeper_startup_checkpoint(fence, environ)

    assert checkpoint == KeeperStartupCheckpoint(
        startup_id=STARTUP_ID,
        generation=7,
        accepted_perf_counter_ns=1234567,
    )
    assert environ == {'KEEP': 'value'}


@pytest.mark.parametrize('raw_value', ('', 'bad', '0', '-1', '1.0'))
def test_invalid_keeper_checkpoint_is_dropped_without_weakening_authority_fence(
    raw_value: str,
) -> None:
    environ = {KEEPER_STARTUP_ACCEPTED_PERF_COUNTER_NS_ENV: raw_value}
    fence = ExpectedStartupFence(startup_id=STARTUP_ID, generation=7)

    assert consume_keeper_startup_checkpoint(fence, environ) is None
    assert environ == {}


def test_keeper_checkpoint_without_authority_fence_is_dropped() -> None:
    environ = {KEEPER_STARTUP_ACCEPTED_PERF_COUNTER_NS_ENV: '1234567'}

    assert consume_keeper_startup_checkpoint(None, environ) is None
    assert environ == {}


@pytest.mark.parametrize(
    'environ',
    (
        {EXPECTED_STARTUP_ID_ENV: STARTUP_ID},
        {EXPECTED_GENERATION_ENV: '7'},
        {EXPECTED_STARTUP_ID_ENV: 'not-a-token', EXPECTED_GENERATION_ENV: '7'},
        {EXPECTED_STARTUP_ID_ENV: STARTUP_ID, EXPECTED_GENERATION_ENV: '0'},
        {EXPECTED_STARTUP_ID_ENV: STARTUP_ID, EXPECTED_GENERATION_ENV: 'bad'},
    ),
)
def test_consume_expected_startup_fence_rejects_incomplete_or_invalid_pair(environ) -> None:
    with pytest.raises(StartupFenceError):
        consume_expected_startup_fence(dict(environ))


def test_validate_expected_startup_lifecycle_accepts_exact_transaction(tmp_path: Path) -> None:
    socket_path = tmp_path / '.ccb' / 'ccbd' / 'ccbd.sock'
    fence = ExpectedStartupFence(startup_id=STARTUP_ID, generation=5)
    lifecycle = build_lifecycle(
        project_id='project-1',
        occurred_at='2026-07-17T00:00:00Z',
        desired_state='running',
        phase='starting',
        generation=5,
        startup_id=STARTUP_ID,
        config_signature='config-1',
        socket_path=socket_path,
    )

    validate_expected_startup_lifecycle(
        fence,
        lifecycle,
        project_id='project-1',
        config_signature='config-1',
        socket_path=socket_path,
    )


@pytest.mark.parametrize(
    ('field', 'value', 'reason'),
    (
        ('project_id', 'other-project', 'project_id mismatch'),
        ('desired_state', 'stopped', 'desired_state is not running'),
        ('phase', 'failed', 'phase is not starting'),
        ('startup_id', 'b' * 32, 'startup_id mismatch'),
        ('generation', 6, 'generation mismatch'),
        ('config_signature', 'other-config', 'config_signature mismatch'),
        ('socket_path', '/tmp/other.sock', 'socket_path mismatch'),
    ),
)
def test_validate_expected_startup_lifecycle_rejects_mismatch(
    tmp_path: Path,
    field: str,
    value,
    reason: str,
) -> None:
    socket_path = tmp_path / '.ccb' / 'ccbd' / 'ccbd.sock'
    values = {
        'project_id': 'project-1',
        'desired_state': 'running',
        'phase': 'starting',
        'generation': 5,
        'startup_id': STARTUP_ID,
        'config_signature': 'config-1',
        'socket_path': socket_path,
    }
    values[field] = value
    lifecycle = build_lifecycle(
        occurred_at='2026-07-17T00:00:00Z',
        **values,
    )

    with pytest.raises(StartupFenceError, match=reason):
        validate_expected_startup_lifecycle(
            ExpectedStartupFence(startup_id=STARTUP_ID, generation=5),
            lifecycle,
            project_id='project-1',
            config_signature='config-1',
            socket_path=socket_path,
        )
