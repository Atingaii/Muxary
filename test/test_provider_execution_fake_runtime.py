from __future__ import annotations

import pytest

from ccbd.api_models import (
    DeliveryScope,
    JobRecord,
    JobStatus,
    MessageEnvelope,
)
from completion.models import (
    CompletionConfidence,
    CompletionCursor,
    CompletionItemKind,
    CompletionSourceKind,
    CompletionStatus,
)
from provider_execution.base import ProviderSubmission
from provider_execution.base import ProviderRuntimeContext
from provider_execution.fake import FakeProviderAdapter
from provider_execution.fake_runtime import FakeDirective, build_terminal_decision, default_script, materialize_payload
from provider_execution.fake_runtime.parsing import parse_directive


def _submission() -> ProviderSubmission:
    return ProviderSubmission(
        job_id="job_1",
        agent_name="agent1",
        provider="fake",
        accepted_at="2026-04-06T00:00:00Z",
        ready_at="2026-04-06T00:00:00Z",
        source_kind=CompletionSourceKind.STRUCTURED_RESULT_STREAM,
        reply="default reply",
        status=CompletionStatus.COMPLETED,
        reason="result_message",
        confidence=CompletionConfidence.EXACT,
        diagnostics={"origin": "test"},
    )


def test_materialize_payload_merges_chunk_and_sets_terminal_reason() -> None:
    chunk_payload, reply_buffer = materialize_payload(
        CompletionItemKind.ASSISTANT_CHUNK,
        {},
        reply_buffer="hello",
        default_reply="ignored",
        turn_ref="job_1",
        terminal_reason="result_message",
    )
    terminal_payload, final_reply = materialize_payload(
        CompletionItemKind.RESULT,
        {},
        reply_buffer=reply_buffer,
        default_reply="ignored",
        turn_ref="job_1",
        terminal_reason="result_message",
    )

    assert chunk_payload["merged_text"] == "helloignored"
    assert terminal_payload["reply"] == "helloignored"
    assert terminal_payload["reason"] == "result_message"
    assert final_reply == "helloignored"


def test_build_terminal_decision_records_fake_terminal_kind() -> None:
    decision = build_terminal_decision(
        _submission(),
        payload={"kind": "result", "turn_id": "turn_1"},
        cursor=CompletionCursor(
            source_kind=CompletionSourceKind.STRUCTURED_RESULT_STREAM,
            event_seq=3,
            updated_at="2026-04-06T00:00:01Z",
        ),
        finished_at="2026-04-06T00:00:01Z",
        reply="done",
    )

    assert decision.status is CompletionStatus.COMPLETED
    assert decision.provider_turn_ref == "turn_1"
    assert decision.diagnostics["fake_terminal_kind"] == "result"


def test_default_script_protocol_turn_cancelled_uses_aborted_terminal_event() -> None:
    directive = FakeDirective(
        status=CompletionStatus.CANCELLED,
        reason="cancelled_by_test",
        confidence=CompletionConfidence.EXACT,
        latency_seconds=0.2,
        script=(),
    )

    events = default_script(directive, mode="protocol_turn")

    assert [event["type"] for event in events] == [
        CompletionItemKind.ANCHOR_SEEN.value,
        CompletionItemKind.TURN_ABORTED.value,
    ]
    assert events[-1]["reason"] == "cancelled_by_test"
    assert events[-1]["status"] == CompletionStatus.CANCELLED.value


def test_parse_directive_defaults_to_completed_for_plain_task_id() -> None:
    directive = parse_directive('task-1', default_latency_seconds=0.3)

    assert directive.status is CompletionStatus.COMPLETED
    assert directive.reason == 'result_message'
    assert directive.confidence is CompletionConfidence.EXACT
    assert directive.latency_seconds == 0.3
    assert directive.script == ()


def test_parse_directive_reads_latency_reason_and_script() -> None:
    directive = parse_directive(
        'fake;status=failed;confidence=observed;latency_ms=1200;script=[{"type":"result"}]',
        default_latency_seconds=0.1,
    )

    assert directive.status is CompletionStatus.FAILED
    assert directive.reason == 'api_error'
    assert directive.confidence is CompletionConfidence.OBSERVED
    assert directive.latency_seconds == 1.2
    assert directive.script == ({'type': 'result'},)


def test_parse_directive_rejects_invalid_segments() -> None:
    with pytest.raises(ValueError, match='invalid fake task_id directive segment'):
        parse_directive('fake;bad-segment', default_latency_seconds=0.1)


def test_fake_provider_generates_mobile_artifacts_from_route_file_store(tmp_path) -> None:
    files_dir = tmp_path / 'mobile' / 'files'
    request = MessageEnvelope(
        project_id='proj-1',
        to_agent='mobile',
        from_actor='user',
        body='ccb-local-artifact:probe',
        task_id=None,
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
        route_options={'mobile_files_dir': str(files_dir)},
    )
    job = JobRecord(
        job_id='job-1',
        submission_id=None,
        agent_name='mobile',
        provider='fake',
        request=request,
        status=JobStatus.QUEUED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-06-23T00:00:00Z',
        updated_at='2026-06-23T00:00:00Z',
        workspace_path=None,
    )

    submission = FakeProviderAdapter(latency_seconds=0).start(
        job,
        context=None,
        now='2026-06-23T00:00:00Z',
    )

    attachments = submission.runtime_state['attachments']
    assert len(attachments) == 2
    file_ids = {item['file_name']: item['file_id'] for item in attachments}
    txt_file_id = file_ids['artifact-probe.txt']
    png_file_id = file_ids['image-probe.png']
    txt_dir = files_dir / 'proj-1' / 'mobile' / txt_file_id
    png_dir = files_dir / 'proj-1' / 'mobile' / png_file_id
    assert (txt_dir / 'content.bin').read_bytes() == b'Generated text artifact for probe'
    assert (png_dir / 'content.bin').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    assert '"file_name": "artifact-probe.txt"' in (txt_dir / 'metadata.json').read_text(
        encoding='utf-8'
    )
    assert f'ccb-artifact://{txt_file_id}' in submission.reply
    assert f'ccb-artifact://{png_file_id}' in submission.reply


def test_fake_provider_completes_mobile_artifact_reply(tmp_path) -> None:
    files_dir = tmp_path / 'mobile' / 'files'
    request = MessageEnvelope(
        project_id='proj-1',
        to_agent='mobile',
        from_actor='user',
        body='ccb-local-artifact:probe',
        task_id=None,
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
        route_options={'mobile_files_dir': str(files_dir)},
    )
    job = JobRecord(
        job_id='job-1',
        submission_id=None,
        agent_name='mobile',
        provider='fake',
        request=request,
        status=JobStatus.QUEUED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-06-23T00:00:00Z',
        updated_at='2026-06-23T00:00:00Z',
        workspace_path=None,
    )
    adapter = FakeProviderAdapter(latency_seconds=0)
    submission = adapter.start(job, context=None, now='2026-06-23T00:00:00Z')

    result = adapter.poll(submission, now='2026-06-23T00:00:00Z')

    assert result is not None
    assert result.decision is not None
    assert result.decision.status is CompletionStatus.COMPLETED
    assert 'CCB Local Artifacts probe' in result.decision.reply


def test_fake_worker_writes_declared_workspace_change(tmp_path) -> None:
    workspace = tmp_path / 'workspace'
    request = MessageEnvelope(
        project_id='proj-1',
        to_agent='worker',
        from_actor='loop_runner',
        body=(
            'Loop: lp1\n'
            'Role: worker\n'
            'Task: task-1\n\n'
            'Task packet and execution contract evidence:\n'
            'allowed_change_paths: workflow_smoke_output.txt\n'
        ),
        task_id='task-1',
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
    )
    job = JobRecord(
        job_id='job-1',
        submission_id=None,
        agent_name='loop-lp1-coder-1',
        provider='fake',
        request=request,
        status=JobStatus.QUEUED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-06-23T00:00:00Z',
        updated_at='2026-06-23T00:00:00Z',
        workspace_path=str(workspace),
    )

    submission = FakeProviderAdapter(latency_seconds=0).start(
        job,
        context=None,
        now='2026-06-23T00:00:00Z',
    )

    output = workspace / 'workflow_smoke_output.txt'
    assert output.is_file()
    assert 'deterministic fake worker wrote declared project-root evidence' in output.read_text(
        encoding='utf-8'
    )
    assert 'changed_files: workflow_smoke_output.txt' in submission.reply


def test_fake_worker_writes_declared_workspace_change_from_runtime_context(tmp_path) -> None:
    workspace = tmp_path / 'context-workspace'
    request = MessageEnvelope(
        project_id='proj-1',
        to_agent='worker',
        from_actor='loop_runner',
        body=(
            'Loop: lp1\n'
            'Role: worker\n'
            'Task: task-1\n\n'
            'Task packet and execution contract evidence:\n'
            'allowed_change_paths: workflow_smoke_output.txt\n'
        ),
        task_id='task-1',
        reply_to=None,
        message_type='ask',
        delivery_scope=DeliveryScope.SINGLE,
    )
    job = JobRecord(
        job_id='job-1',
        submission_id=None,
        agent_name='loop-lp1-coder-1',
        provider='fake',
        request=request,
        status=JobStatus.QUEUED,
        terminal_decision=None,
        cancel_requested_at=None,
        created_at='2026-06-23T00:00:00Z',
        updated_at='2026-06-23T00:00:00Z',
        workspace_path=None,
    )

    FakeProviderAdapter(latency_seconds=0).start(
        job,
        context=ProviderRuntimeContext(
            agent_name='loop-lp1-coder-1',
            workspace_path=str(workspace),
            backend_type='fake',
            runtime_ref='runtime',
            session_ref='session',
        ),
        now='2026-06-23T00:00:00Z',
    )

    assert (workspace / 'workflow_smoke_output.txt').is_file()
