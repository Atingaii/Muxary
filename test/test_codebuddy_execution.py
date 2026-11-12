from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from ccbd.api_models import DeliveryScope, JobRecord, JobStatus, MessageEnvelope
from completion.models import CompletionConfidence, CompletionItemKind, CompletionSourceKind, CompletionStatus
from provider_backends.codebuddy import execution
from provider_execution.base import ProviderRuntimeContext, ProviderSubmission


NOW = '2026-11-11T01:00:00Z'
LATER = '2026-11-11T01:00:01Z'


def _message(role: str, text: str, *, generation: str = 'generation-wanted', **extra) -> dict:
    # Responses-style JSONL shape observed in CodeBuddy CLI 2.178.0. All text
    # is synthetic; no host conversation or credentials are test fixtures.
    return {
        'type': 'message', 'role': role,
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


@dataclass
class _Backend:
    alive: bool = True
    sent: list[tuple[str, str]] = field(default_factory=list)
    keys: list[tuple[str, str]] = field(default_factory=list)

    def send_text_to_pane(self, pane: str, text: str) -> None:
        self.sent.append((pane, text))

    def is_tmux_pane_alive(self, pane: str) -> bool:
        assert pane == '%codebuddy1'
        return self.alive

    def send_key(self, pane: str, key: str) -> None:
        self.keys.append((pane, key))

    def get_pane_content(self, *args, **kwargs):
        raise AssertionError('terminal text is never authoritative CodeBuddy completion evidence')


@dataclass
class _Runtime:
    path: Path
    backend: _Backend
    session: object
    job: JobRecord
    context: ProviderRuntimeContext
    adapter: execution.CodebuddyProviderAdapter

    @property
    def done(self) -> str:
        return f'CCB_DONE: {self.job.job_id}'

    def start(self) -> ProviderSubmission:
        return self.adapter.start(self.job, context=self.context, now=NOW)

    def anchor(self, text: str | None = None, **extra) -> dict:
        return _message('user', text if text is not None else f'CCB_REQ_ID: {self.job.job_id}\n\nDo the task.', **extra)

    def answer(self, text: str = 'Verified answer', **extra) -> dict:
        return _message('assistant', f'{text}\n{self.done}', **extra)


@pytest.fixture
def runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Runtime:
    work_dir = tmp_path / 'repo'
    work_dir.mkdir()
    path = work_dir / '.ccb' / 'agents' / 'codebuddy1' / 'provider-state' / 'codebuddy' / 'config' / 'projects' / 'repo' / 'fixture.jsonl'
    config_dir = path.parents[2]
    session = SimpleNamespace(data={
        'active': True, 'agent_name': 'codebuddy1', 'work_dir': str(work_dir),
        'pane_id': '%codebuddy1', 'codebuddy_session_id': 'fixture',
        'codebuddy_session_path': str(path), 'codebuddy_config_dir': str(config_dir),
    }, ensure_pane=lambda: (True, '%codebuddy1'))
    backend = _Backend()
    monkeypatch.setattr(execution, 'load_project_session', lambda work_dir, *, instance=None: session if instance == 'codebuddy1' else None)
    monkeypatch.setattr(execution, 'get_backend_for_session', lambda data: backend)
    job = JobRecord(
        job_id='job_codebuddy123', submission_id='sub_codebuddy', agent_name='codebuddy1', provider='codebuddy',
        request=MessageEnvelope(project_id='project', to_agent='codebuddy1', from_actor='main', body='Do the task.',
            task_id=None, reply_to=None, message_type='ask', delivery_scope=DeliveryScope.SINGLE),
        status=JobStatus.RUNNING, terminal_decision=None, cancel_requested_at=None,
        created_at=NOW, updated_at=NOW, workspace_path=str(work_dir),
    )
    context = ProviderRuntimeContext(agent_name='codebuddy1', workspace_path=str(work_dir), backend_type='tmux',
        runtime_ref='%codebuddy1', session_ref=str(work_dir / '.ccb' / '.codebuddy1-session'))
    return _Runtime(path, backend, session, job, context, execution.build_execution_adapter())


def test_start_pins_native_transcript_before_sending_wrapped_prompt(runtime: _Runtime) -> None:
    _append(runtime.path, runtime.anchor(), runtime.answer('Historical answer'))
    submission = runtime.start()
    assert submission.source_kind is CompletionSourceKind.SESSION_EVENT_LOG
    assert submission.runtime_state['state']['offset'] == runtime.path.stat().st_size
    assert submission.runtime_state['reader'].current_session_path() == runtime.path
    assert runtime.backend.sent == [('%codebuddy1', execution.wrap_codebuddy_prompt('Do the task.', runtime.job.job_id))]
    assert runtime.adapter.poll(submission, now=LATER) is None


@pytest.mark.parametrize('error_type', [PermissionError, IsADirectoryError, OSError])
def test_unreadable_transcript_is_rejected_before_prompt_submission(runtime: _Runtime, monkeypatch, error_type) -> None:
    def denied_open(*args, **kwargs):
        raise error_type('fixture-unobservable-transcript')

    monkeypatch.setattr(Path, 'open', denied_open)
    submission = runtime.start()
    assert submission.runtime_state['mode'] == 'error'
    assert submission.runtime_state['reason'] == 'codebuddy_send_failed'
    assert submission.runtime_state['error'].startswith(error_type.__name__ + ':')
    assert runtime.backend.sent == []


@pytest.mark.parametrize('error_type', [PermissionError, IsADirectoryError, OSError])
def test_transcript_io_error_fails_poll_instead_of_waiting_for_timeout(runtime: _Runtime, monkeypatch, error_type) -> None:
    submission = runtime.start()

    def denied_open(*args, **kwargs):
        raise error_type('fixture-unobservable-transcript')

    monkeypatch.setattr(Path, 'open', denied_open)
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert result.decision.reason == f'codebuddy_log_read_failed:{error_type.__name__}'
    assert 'fixture-unobservable' not in result.decision.reason


def test_transcript_disappearance_after_anchor_fails_closed(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor())
    anchored = runtime.adapter.poll(submission, now=LATER)
    assert anchored is not None and anchored.decision is None
    assert anchored.submission.runtime_state['anchor_seen']
    runtime.path.unlink()
    result = runtime.adapter.poll(anchored.submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert result.decision.reason == 'codebuddy_log_read_failed:FileNotFoundError'


def test_completed_assistant_after_exact_anchor_finishes_with_native_evidence(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), runtime.answer('中文答案'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.COMPLETED
    assert result.decision.confidence is CompletionConfidence.EXACT
    assert result.decision.reason == 'codebuddy_done_marker'
    assert result.decision.reply == '中文答案'
    assert result.decision.anchor_seen
    assert [item.kind for item in result.items] == [
        CompletionItemKind.ANCHOR_SEEN, CompletionItemKind.ASSISTANT_FINAL, CompletionItemKind.TURN_BOUNDARY,
    ]
    assert [item.cursor.event_seq for item in result.items] == [1, 2, 3]
    assert all(item.cursor.session_path == str(runtime.path) for item in result.items)


@pytest.mark.parametrize('source', ['user', 'tool', 'reasoning', 'terminal', 'other-block', 'partial-assistant'])
def test_non_authoritative_marker_echo_never_completes(runtime: _Runtime, source: str) -> None:
    submission = runtime.start()
    echoes = {
        'user': runtime.anchor(f'CCB_REQ_ID: {runtime.job.job_id}\n{runtime.done}'),
        'tool': {'type': 'function_call_result', 'status': 'completed', 'output': runtime.done},
        'reasoning': {'type': 'reasoning', 'content': [{'type': 'output_text', 'text': runtime.done}]},
        'terminal': {'type': 'terminal', 'status': 'completed', 'text': runtime.done},
        'other-block': _message('assistant', '', content=[{'type': 'input_text', 'text': runtime.done}]),
        'partial-assistant': runtime.answer(status='incomplete'),
    }
    _append(runtime.path, runtime.anchor(), echoes[source])
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is None
    assert result.submission.status is not CompletionStatus.COMPLETED
    assert not any(item.kind is CompletionItemKind.ASSISTANT_FINAL for item in result.items)


def test_assistant_marker_before_user_anchor_is_ignored(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.answer('Unowned reply'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is None
    assert not result.submission.runtime_state['anchor_seen']
    assert result.submission.reply == ''


@pytest.mark.parametrize('status', ['completed', 'incomplete'])
def test_other_generation_reply_and_error_cannot_end_owned_turn(runtime: _Runtime, status: str) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), runtime.answer(status=status, providerData={
        'conversationRequestId': 'unrelated-generation', 'error': {'code': 'FOREIGN_FAILURE'},
    }))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is None
    assert result.submission.reply == ''
    _append(runtime.path, runtime.answer())
    result = runtime.adapter.poll(result.submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.COMPLETED


def test_commentary_completed_is_not_a_turn_boundary(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), _message('assistant', 'I will inspect the repository.'))
    first = runtime.adapter.poll(submission, now=LATER)
    assert first is not None and first.decision is None
    assert first.submission.reply == 'I will inspect the repository.'
    assert [item.kind for item in first.items] == [CompletionItemKind.ANCHOR_SEEN, CompletionItemKind.ASSISTANT_CHUNK]
    _append(runtime.path, {'type': 'function_call', 'name': 'read_file', 'arguments': '{}'}, runtime.answer('Inspected and fixed.'))
    final = runtime.adapter.poll(first.submission, now=LATER)
    assert final is not None and final.decision is not None
    assert final.decision.reply == 'Inspected and fixed.'
    assert [item.cursor.event_seq for item in final.items] == [3, 4]


def test_marker_for_another_request_and_nonfinal_marker_do_not_complete(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), _message('assistant', 'Wrong request\nCCB_DONE: job_other'),
        _message('assistant', f'{runtime.done}\nStill working.'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is None
    assert result.submission.reply == f'{runtime.done}\nStill working.'


def test_native_incomplete_error_fails_and_redacts_untrusted_details(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), runtime.answer('private body', status='incomplete', providerData={
        'conversationRequestId': 'generation-wanted', 'error': {'code': 'AUTH_ERROR', 'message': 'private credential'},
    }))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert 'AUTH_ERROR' in result.decision.reason
    assert 'private' not in repr(result)
    assert result.decision.reply == ''


def test_unrelated_user_after_anchor_interrupts_instead_of_claiming_next_answer(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), _message('user', 'A different task', generation='different'),
        runtime.answer('Do not attribute', generation='different'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.INCOMPLETE
    assert result.decision.reason == 'codebuddy_turn_interrupted'
    assert result.decision.reply == ''


def test_image_only_user_also_interrupts_owned_turn(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), _message('user', '', generation='different',
        content=[{'type': 'input_image', 'image_url': 'synthetic-fixture'}]),
        runtime.answer('Unowned image answer', generation='different'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.reason == 'codebuddy_turn_interrupted'


def test_quoted_request_anchor_inside_unrelated_user_message_is_not_ownership(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(f'Please explain this quoted marker:\nCCB_REQ_ID: {runtime.job.job_id}'), runtime.answer('Unowned'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is None
    assert not result.submission.runtime_state['anchor_seen']


@pytest.mark.parametrize('damage', ['truncate', 'replace'])
def test_log_reset_after_anchor_cannot_replay_historical_done(runtime: _Runtime, damage: str) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(f'CCB_REQ_ID: {runtime.job.job_id}\n' + 'padding' * 500))
    anchored = runtime.adapter.poll(submission, now=LATER)
    assert anchored is not None and anchored.decision is None
    if damage == 'truncate':
        runtime.path.write_text('', encoding='utf-8')
        _append(runtime.path, runtime.answer('Replayed historical answer'))
    else:
        replacement = runtime.path.with_suffix('.replacement')
        _append(replacement, runtime.anchor(), runtime.answer('Replayed historical answer' * 500))
        replacement.replace(runtime.path)
    result = runtime.adapter.poll(anchored.submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.INCOMPLETE
    assert result.decision.reason == 'codebuddy_log_reset'
    assert result.decision.reply == ''


def test_partial_last_jsonl_record_waits_for_newline(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor())
    raw = json.dumps(runtime.answer('Final 中文'), ensure_ascii=False).encode('utf-8')
    split = raw.index('中'.encode('utf-8')) + 1
    with runtime.path.open('ab') as handle:
        handle.write(raw[:split])
    first = runtime.adapter.poll(submission, now=LATER)
    assert first is not None and first.decision is None
    with runtime.path.open('ab') as handle:
        handle.write(raw[split:])
    second = runtime.adapter.poll(first.submission, now=LATER)
    assert second is None
    with runtime.path.open('ab') as handle:
        handle.write(b'\n')
    final = runtime.adapter.poll(first.submission, now=LATER)
    assert final is not None and final.decision is not None
    assert final.decision.reply == 'Final 中文'


@pytest.mark.parametrize('damaged', [b'{bad}\n', b'[]\n', b'\xff\n'])
def test_corrupted_intervening_record_fails_closed(runtime: _Runtime, damaged: bytes) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor())
    with runtime.path.open('ab') as handle:
        handle.write(damaged)
    _append(runtime.path, runtime.answer('Possibly another turn'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert result.decision.reason.startswith('codebuddy_log_read_failed:')
    assert result.decision.reply == ''


def test_missing_generation_does_not_bypass_native_identity_check(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), runtime.answer(providerData={}))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED


@pytest.mark.parametrize('provider_data', [{}, {'conversationRequestId': 7}, {'conversationRequestId': ''}],
    ids=['missing', 'number', 'empty'])
def test_invalid_user_generation_cannot_authorize_a_foreign_final(runtime: _Runtime, provider_data: dict) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(providerData=provider_data),
        runtime.answer('Unowned answer', generation='unrelated-generation'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert result.decision.reason == 'codebuddy_log_read_failed:ValueError'
    assert not result.decision.anchor_seen
    assert result.decision.reply == ''
    assert not any(item.kind is CompletionItemKind.ASSISTANT_FINAL for item in result.items)


def test_unbound_session_path_is_rejected_before_prompt_submission(runtime: _Runtime) -> None:
    runtime.session.data.pop('codebuddy_session_path')
    submission = runtime.start()
    assert submission.runtime_state['mode'] == 'error'
    assert submission.runtime_state['error'] == 'codebuddy_session_path_missing'
    assert runtime.backend.sent == []


def test_missing_context_is_rejected_without_sending(runtime: _Runtime) -> None:
    submission = runtime.adapter.start(runtime.job, context=None, now=NOW)
    assert submission.runtime_state['mode'] == 'error'
    assert submission.runtime_state['error'] == 'missing_runtime_context'
    assert runtime.backend.sent == []


def test_no_wrap_is_explicitly_unsupported(runtime: _Runtime) -> None:
    runtime.job.provider_options['no_wrap'] = True
    submission = runtime.start()
    assert submission.runtime_state['mode'] == 'error'
    assert submission.runtime_state['reason'] == 'codebuddy_no_wrap_unsupported'
    assert runtime.backend.sent == []


def test_named_agent_does_not_fall_back_to_default_or_another_agent(runtime: _Runtime, monkeypatch) -> None:
    calls = []

    def load(work_dir, *, instance=None):
        calls.append(instance)
        return runtime.session if instance in {None, 'codebuddy1'} else None

    monkeypatch.setattr(execution, 'load_project_session', load)
    runtime.job.agent_name = 'codebuddy2'
    submission = runtime.start()
    assert calls == ['codebuddy2']
    assert submission.runtime_state['error'] == 'missing_codebuddy_session'
    assert runtime.backend.sent == []


def test_provider_instance_selects_only_its_bound_session(runtime: _Runtime, monkeypatch) -> None:
    calls = []

    def load(work_dir, *, instance=None):
        calls.append(instance)
        return None

    monkeypatch.setattr(execution, 'load_project_session', load)
    runtime.job.provider_instance = 'codebuddy-special'
    submission = runtime.start()
    assert calls == ['codebuddy-special']
    assert submission.runtime_state['mode'] == 'error'


def test_timeout_preserves_commentary_without_claiming_completion(runtime: _Runtime, monkeypatch) -> None:
    monkeypatch.setenv('CCB_CODEBUDDY_RUN_TIMEOUT_S', '1')
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), _message('assistant', 'Still working.'))
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.INCOMPLETE
    assert result.decision.reason == 'codebuddy_run_timeout'
    assert result.decision.reply == 'Still working.'


def test_cancel_interrupts_and_clears_only_bound_pane(runtime: _Runtime) -> None:
    runtime.adapter.cancel(runtime.start())
    assert runtime.backend.keys == [('%codebuddy1', 'C-c'), ('%codebuddy1', 'Escape'), ('%codebuddy1', 'C-u')]


def test_dead_pane_fails_before_processing_a_forged_final(runtime: _Runtime) -> None:
    submission = runtime.start()
    _append(runtime.path, runtime.anchor(), runtime.answer())
    runtime.backend.alive = False
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert result.decision.reason == 'pane_dead'


def test_invalid_runtime_state_fails_closed(runtime: _Runtime) -> None:
    submission = runtime.start()
    submission = replace(submission, runtime_state={**submission.runtime_state, 'reader': None})
    result = runtime.adapter.poll(submission, now=LATER)
    assert result is not None and result.decision is not None
    assert result.decision.status is CompletionStatus.FAILED
    assert result.decision.reason == 'codebuddy_runtime_state_invalid'


@pytest.mark.parametrize('value', ['bad', 'nan', 'inf', '-1', '0'])
def test_invalid_timeout_value_uses_bounded_default(runtime: _Runtime, monkeypatch, value: str) -> None:
    monkeypatch.setenv('CCB_CODEBUDDY_RUN_TIMEOUT_S', value)
    assert runtime.start().runtime_state['run_timeout_s'] == 900.0


def test_restore_does_not_claim_inflight_job_replay_support(runtime: _Runtime) -> None:
    diagnostics = runtime.adapter.restore_diagnostics()
    assert diagnostics['resume_supported'] is False
    assert diagnostics['restore_mode'] == 'resubmit_required'
