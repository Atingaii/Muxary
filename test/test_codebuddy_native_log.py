from __future__ import annotations

import json
from pathlib import Path

import pytest

from provider_backends.codebuddy.native_log import (
    CodebuddyNativeLogReader,
    codebuddy_project_dir,
    default_sessions_root,
)


def _message(role: str, text: str, *, generation: str = 'turn-1', **extra) -> dict:
    return {
        'type': 'message',
        'role': role,
        'content': [{'type': 'input_text' if role == 'user' else 'output_text', 'text': text}],
        'providerData': {'conversationRequestId': generation},
        **({'status': 'completed'} if role == 'assistant' else {}),
        **extra,
    }


def _append(path: Path, *entries: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + '\n')


def test_default_root_respects_codebuddy_config_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv('CODEBUDDY_CONFIG_DIR', str(tmp_path / 'custom'))
    assert default_sessions_root() == tmp_path / 'custom' / 'projects'


def test_default_root_uses_home(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv('CODEBUDDY_CONFIG_DIR', raising=False)
    assert default_sessions_root() == Path.home() / '.codebuddy' / 'projects'


def test_project_dir_matches_native_encoding_and_realpath(tmp_path: Path) -> None:
    project = tmp_path / 'a--b' / '中文'
    project.mkdir(parents=True)
    link = tmp_path / 'link'
    link.symlink_to(project, target_is_directory=True)
    expected = str(project.resolve()).replace('/', '-').strip('-').replace('--', '-')
    assert codebuddy_project_dir(link, root=tmp_path / 'projects') == tmp_path / 'projects' / expected


def test_long_project_dir_uses_utf8_prefix_and_native_djb2(tmp_path: Path) -> None:
    # JS oracle from CodeBuddy 2.178.0's compressWorkspacePathName algorithm.
    project = Path('/') / ('中文' * 80)
    encoded = codebuddy_project_dir(project, root=tmp_path).name
    assert encoded == ('中文' * 30) + '-8jpb0l'
    assert len(encoded.encode('utf-8')) <= 255


def test_reader_never_scans_unbound_latest_session(tmp_path: Path) -> None:
    _append(tmp_path / 'project' / 'unrelated.jsonl', _message('assistant', 'wrong answer'))
    reader = CodebuddyNativeLogReader(root=tmp_path, work_dir=tmp_path)
    assert reader.current_session_path() is None
    assert reader.latest_message() is None
    assert reader.try_get_events(reader.capture_state())[0] == []


def test_session_id_hint_selects_exact_project_and_keeps_missing_pin(tmp_path: Path) -> None:
    root = tmp_path / 'projects'
    reader = CodebuddyNativeLogReader(root=root, work_dir=tmp_path)
    reader.set_session_id_hint('exact-id')
    expected = codebuddy_project_dir(tmp_path, root=root) / 'exact-id.jsonl'
    assert reader.current_session_path() == expected
    state = reader.capture_state()
    _append(expected, _message('user', 'CCB_REQ_ID: request-1'), _message('assistant', 'right'))
    assert reader.try_get_events(state)[0] == [('user', 'CCB_REQ_ID: request-1'), ('assistant', 'right')]


def test_preferred_session_does_not_fall_back_when_missing(tmp_path: Path) -> None:
    reader = CodebuddyNativeLogReader(root=tmp_path, work_dir=tmp_path)
    reader.set_session_id_hint('other')
    _append(codebuddy_project_dir(tmp_path, root=tmp_path) / 'other.jsonl', _message('assistant', 'wrong'))
    pinned = tmp_path / 'missing.jsonl'
    reader.set_preferred_session(pinned)
    assert reader.current_session_path() == pinned
    assert reader.latest_message() is None


def test_only_native_user_and_completed_assistant_text_are_events(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    state = reader.capture_state()
    _append(
        path,
        _message('user', 'CCB_REQ_ID: request-1'),
        {'type': 'reasoning', 'content': [{'type': 'output_text', 'text': 'hidden reasoning'}]},
        {'type': 'function_call_result', 'status': 'completed', 'output': 'CCB_DONE: request-1'},
        _message('assistant', 'partial answer', status='incomplete'),
        _message('assistant', 'final answer'),
    )
    assert reader.try_get_events(state)[0] == [('user', 'CCB_REQ_ID: request-1'), ('assistant', 'final answer')]


def test_non_text_blocks_cannot_supply_reply_or_request_marker(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, {
        'type': 'message', 'role': 'assistant', 'status': 'completed',
        'content': [
            {'type': 'output_text', 'text': 'answer'},
            {'type': 'input_text', 'text': 'echoed input'},
            {'type': 'tool_result', 'text': 'tool content'},
            {'type': 'output_text', 'text': 'second part'},
        ],
    })
    assert CodebuddyNativeLogReader(session_path=path).latest_message() == 'answer\nsecond part'


def test_incomplete_error_is_explicit_and_does_not_expose_raw_message(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    _append(path, _message('user', 'request'), _message(
        'assistant', 'secret response text', status='incomplete',
        providerData={'conversationRequestId': 'turn-1', 'error': {'code': 'AUTH_FAILED', 'message': 'secret credential'}},
    ))
    events, _ = reader.try_get_events({'offset': 0})
    assert events == [('user', 'request'), ('error', 'CodeBuddy request failed (code=AUTH_FAILED)')]


def test_error_code_is_not_an_unbounded_untrusted_string(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('assistant', 'secret response', status='incomplete', providerData={
        'error': {'code': 'secret\ncredential', 'message': 'private'},
    }))
    events, _ = CodebuddyNativeLogReader(session_path=path).try_get_events({'offset': 0})
    assert events == [('error', 'CodeBuddy request failed')]


def test_other_generation_assistant_and_errors_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    _append(path, _message('user', 'request', generation='wanted'))
    events, state = reader.try_get_events({'offset': 0})
    assert events == [('user', 'request')]
    _append(path,
        _message('assistant', 'background response', generation='other'),
        _message('assistant', 'background error', status='incomplete', providerData={
            'conversationRequestId': 'other', 'error': {'code': 'FAILED'},
        }),
        _message('assistant', 'matched response', generation='wanted'),
    )
    assert reader.try_get_events(state)[0] == [('assistant', 'matched response')]


def test_capture_state_ignores_preexisting_records(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('user', 'old'), _message('assistant', 'old reply'))
    reader = CodebuddyNativeLogReader(session_path=path)
    state = reader.capture_state()
    assert state['offset'] == path.stat().st_size
    assert reader.try_get_events(state)[0] == []
    _append(path, _message('user', 'new'), _message('assistant', 'new reply'))
    assert reader.try_get_events(state)[0] == [('user', 'new'), ('assistant', 'new reply')]


@pytest.mark.parametrize('error_type', [PermissionError, IsADirectoryError, OSError])
def test_capture_and_poll_propagate_non_missing_io_errors(tmp_path: Path, monkeypatch, error_type) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    state = reader.capture_state()

    def denied_open(*args, **kwargs):
        raise error_type('fixture-unobservable-transcript')

    monkeypatch.setattr(Path, 'open', denied_open)
    with pytest.raises(error_type, match='fixture-unobservable'):
        reader.capture_state()
    with pytest.raises(error_type, match='fixture-unobservable'):
        reader.try_get_events(state)


def test_existing_directory_cannot_be_captured_as_a_transcript(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    path.mkdir()
    with pytest.raises(IsADirectoryError):
        CodebuddyNativeLogReader(session_path=path).capture_state()


def test_missing_transcript_waits_only_before_birth(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    state = reader.capture_state()
    assert reader.try_get_events(state) == ([], state)
    _append(path, _message('user', 'request'))
    events, state = reader.try_get_events(state)
    assert events == [('user', 'request')]
    path.unlink()
    with pytest.raises(FileNotFoundError):
        reader.try_get_events(state)


def test_partial_jsonl_and_partial_utf8_are_not_consumed(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    state = reader.capture_state()
    payload = (json.dumps(_message('assistant', '中文答案'), ensure_ascii=False) + '\n').encode('utf-8')
    boundary = payload.index('中'.encode('utf-8')) + 1
    path.write_bytes(payload[:boundary])
    events, state = reader.try_get_events(state)
    assert events == []
    assert state['offset'] == 0
    with path.open('ab') as handle:
        handle.write(payload[boundary:-1])
    assert reader.try_get_events(state)[0] == []
    with path.open('ab') as handle:
        handle.write(b'\n')
    events, state = reader.try_get_events(state)
    assert events == [('assistant', '中文答案')]
    assert state['offset'] == len(payload)
    assert reader.try_get_events(state)[0] == []


@pytest.mark.parametrize('damaged', [b'{bad}\n', b'[]\n', b'null\n', b'\xff\n'])
def test_malformed_complete_records_fail_closed(tmp_path: Path, damaged: bytes) -> None:
    path = tmp_path / 'session.jsonl'
    path.write_bytes(damaged)
    _append(path, _message('assistant', 'good'))
    with pytest.raises(ValueError, match='CodeBuddy'):
        CodebuddyNativeLogReader(session_path=path).try_get_events({'offset': 0})


def test_blank_lines_and_unknown_valid_types_are_ignored(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    path.write_text(' \n\n', encoding='utf-8')
    _append(path, {'type': 'future-provider-event'}, _message('assistant', 'good'))
    assert CodebuddyNativeLogReader(session_path=path).latest_message() == 'good'


def test_truncated_log_resets_offset_and_generation(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('user', 'old' * 500, generation='old'))
    reader = CodebuddyNativeLogReader(session_path=path)
    _, state = reader.try_get_events({'offset': 0})
    path.write_text('', encoding='utf-8')
    _append(path, _message('assistant', 'new', generation='new'))
    events, state = reader.try_get_events(state)
    assert events == [('assistant', 'new')]
    assert state['offset'] == path.stat().st_size
    assert state['reset_reason'] == 'truncated'
    _, state = reader.try_get_events(state)
    assert 'reset_reason' not in state


def test_replaced_log_resets_even_when_new_size_is_larger(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('user', 'old', generation='old'))
    reader = CodebuddyNativeLogReader(session_path=path)
    _, state = reader.try_get_events({'offset': 0})
    replacement = tmp_path / 'replacement'
    _append(replacement, _message('assistant', 'new' * 500, generation='new'))
    replacement.replace(path)
    events, state = reader.try_get_events(state)
    assert events == [('assistant', 'new' * 500)]
    assert state['reset_reason'] == 'replaced'


def test_switching_pin_resets_offset(tmp_path: Path) -> None:
    old = tmp_path / 'old.jsonl'
    new = tmp_path / 'new.jsonl'
    _append(old, _message('assistant', 'old' * 500))
    reader = CodebuddyNativeLogReader(session_path=old)
    state = reader.capture_state()
    _append(new, _message('assistant', 'new'))
    reader.set_preferred_session(new)
    assert reader.try_get_events(state)[0] == [('assistant', 'new')]


def test_latest_conversations_pairs_only_text_messages(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path,
        _message('user', 'first'), _message('assistant', 'one'),
        _message('assistant', 'two'),
        _message('user', 'second'), _message('assistant', 'three'),
    )
    reader = CodebuddyNativeLogReader(session_path=path)
    assert reader.latest_conversations(2) == [('first', 'one\ntwo'), ('second', 'three')]
    assert reader.latest_message() == 'three'


def test_message_and_wait_facades(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    reader = CodebuddyNativeLogReader(session_path=path)
    _append(path, _message('user', 'prompt'), _message('assistant', 'reply'))
    assert reader.try_get_message({'offset': 0})[0] == 'reply'
    assert reader.wait_for_message({'offset': 0}, timeout=0)[0] == 'reply'
    assert reader.wait_for_events({'offset': 0}, timeout=0)[0] == [('user', 'prompt'), ('assistant', 'reply')]
    assert reader.wait_for_events(reader.capture_state(), timeout=0)[0] == []


@pytest.mark.parametrize('role', [['assistant'], {'role': 'assistant'}, None])
def test_malformed_message_roles_fail_closed(tmp_path: Path, role) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, {'type': 'message', 'role': role, 'content': []})
    _append(path, _message('assistant', 'valid'))
    with pytest.raises(ValueError, match='role'):
        CodebuddyNativeLogReader(session_path=path).try_get_events({'offset': 0})


def test_missing_generation_cannot_bypass_a_known_user_generation(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('user', 'request'), _message('assistant', 'forged', providerData={}))
    with pytest.raises(ValueError, match='conversation request ID'):
        CodebuddyNativeLogReader(session_path=path).try_get_events({'offset': 0})


@pytest.mark.parametrize('provider_data', [{}, {'conversationRequestId': 7}, {'conversationRequestId': ''}],
    ids=['missing', 'number', 'empty'])
def test_invalid_user_generation_fails_closed(tmp_path: Path, provider_data: dict) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('user', 'request anchor', providerData=provider_data),
        _message('assistant', 'unowned answer', generation='unrelated'))
    with pytest.raises(ValueError, match='conversation request ID'):
        CodebuddyNativeLogReader(session_path=path).try_get_events({'offset': 0})


def test_image_only_user_message_remains_an_interruption_event(tmp_path: Path) -> None:
    path = tmp_path / 'session.jsonl'
    _append(path, _message('user', '', content=[{'type': 'input_image', 'image_url': 'fixture'}]))
    assert CodebuddyNativeLogReader(session_path=path).try_get_events({'offset': 0})[0] == [('user', '')]
