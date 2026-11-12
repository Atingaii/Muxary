import json
from pathlib import Path

import pytest

from message_bureau import (
    AttemptRecord,
    AttemptState,
    AttemptStore,
    MessageRecord,
    MessageState,
    MessageStore,
    RetryLineageError,
    authoritative_retry_successor,
)
from storage.paths import PathLayout


def _authority(tmp_path: Path, *, targets: tuple[str, ...], attempt_agent: str = 'planner') -> PathLayout:
    layout = PathLayout(tmp_path)
    MessageStore(layout).append(MessageRecord(
        message_id='msg-retry', origin_message_id=None, from_actor='system',
        target_scope='single', target_agents=targets, message_class='ask',
        retry_policy={'mode': 'auto', 'max_attempts': 3},
        created_at='2026-07-12T00:00:00Z', updated_at='2026-07-12T00:00:02Z',
        message_state=MessageState.COMPLETED,
    ))
    store = AttemptStore(layout)
    for index, state in enumerate((AttemptState.FAILED, AttemptState.COMPLETED)):
        store.append(AttemptRecord(
            attempt_id=f'att-{index}', message_id='msg-retry', agent_name=attempt_agent,
            provider='codex', job_id=f'job-{index}', retry_index=index,
            health_snapshot_ref=None, started_at=f'2026-07-12T00:00:0{index}Z',
            updated_at=f'2026-07-12T00:00:0{index + 1}Z', attempt_state=state,
        ))
    return layout


def test_retry_rejects_attempt_agent_not_authorized_by_message_target(tmp_path: Path) -> None:
    layout = _authority(tmp_path, targets=('other-agent',))

    with pytest.raises(RetryLineageError, match='not uniquely authorized'):
        authoritative_retry_successor(layout, 'job-0')


@pytest.mark.parametrize('targets', [('Planner',), ('other-agent', 'PLANNER')])
def test_retry_accepts_normalized_single_and_multi_target_authority(
    tmp_path: Path, targets: tuple[str, ...],
) -> None:
    layout = _authority(tmp_path, targets=targets, attempt_agent='Planner')

    edge = authoritative_retry_successor(layout, 'job-0')

    assert edge is not None
    assert edge.retry_successor_job_id == 'job-1'


def test_retry_rejects_duplicate_normalized_target_authority(tmp_path: Path) -> None:
    layout = _authority(tmp_path, targets=('Planner', 'planner'))

    with pytest.raises(RetryLineageError, match='not uniquely authorized'):
        authoritative_retry_successor(layout, 'job-0')


@pytest.mark.parametrize('targets', [[], ['bad target!']])
def test_retry_rejects_empty_or_malformed_persisted_targets(
    tmp_path: Path, targets: list[str],
) -> None:
    layout = _authority(tmp_path, targets=('planner',))
    record = json.loads(layout.ccbd_messages_path.read_text(encoding='utf-8'))
    record['target_agents'] = targets
    layout.ccbd_messages_path.write_text(json.dumps(record) + '\n', encoding='utf-8')

    with pytest.raises(RetryLineageError, match='target authority malformed'):
        authoritative_retry_successor(layout, 'job-0')
