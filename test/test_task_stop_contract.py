import pytest

from cli.services.task_stop_contract import match_detail_ready_stop_contract


@pytest.mark.parametrize(
    'text',
    (
        'Expected stop: detail_ready',
        'Terminal expectation detail_ready.',
        'Preserve terminal expectation detail_ready.',
        'Continue with terminal status detail_ready.',
        'Proceed with terminal status detail_ready.',
        'The task must stop at detail_ready.',
        'The task shall stop as detail_ready.',
        'The controller-visible task outcome remains detail_ready.',
    ),
)
def test_match_detail_ready_stop_contract_accepts_explicit_normative_text(text: str) -> None:
    assert match_detail_ready_stop_contract(text) is not None


@pytest.mark.parametrize(
    'text',
    (
        'Do not preserve terminal expectation detail_ready.',
        'The task must not stop at detail_ready.',
        'detail_ready is not the terminal expectation.',
        'detail_ready is no longer the terminal expectation.',
        'The task may stop at detail_ready.',
        'The task might stop at detail_ready.',
        'The task could stop at detail_ready.',
        'The task would stop at detail_ready.',
        'The task should stop at detail_ready.',
        'The task can stop at detail_ready.',
        'If validation succeeds, expected stop: detail_ready.',
        'Should the expected stop be detail_ready?',
        'Example: Expected stop: detail_ready.',
        'For example, terminal expectation detail_ready.',
        'e.g. expected stop: detail_ready',
        'Sample: terminal expectation detail_ready.',
        'Hypothetical: expected stop: detail_ready.',
        '```\nExpected stop: detail_ready\n```',
        '> Expected stop: detail_ready',
        'Other task phase6b-l3: expected stop: detail_ready.',
        'Task phase6b-l3-other: expected stop: detail_ready.',
        'Expected stop: detail_ready, not replan_required.',
        'Expected stop: detail_ready or blocked.',
        'Allowed statuses: detail_ready, replan_required, blocked.',
        'detail_ready',
        'status enum: detail_ready',
    ),
)
def test_match_detail_ready_stop_contract_rejects_unsafe_context(text: str) -> None:
    assert match_detail_ready_stop_contract(text) is None


@pytest.mark.parametrize(
    'text',
    (
        'Expected stop: detail_ready. Do not stop at detail_ready.',
        'Expected stop: detail_ready. Expected stop: blocked.',
        'Expected stop: detail_ready when validation succeeds.',
        '- > Expected stop: detail_ready',
        '{"description":"Expected stop: detail_ready"}',
        'For task unrelated-task, expected stop: detail_ready.',
    ),
)
def test_match_detail_ready_stop_contract_rejects_any_unsafe_statement_in_corpus(text: str) -> None:
    assert match_detail_ready_stop_contract(text) is None


@pytest.mark.parametrize(
    'text',
    (
        'Expected controller-visible task outcome is detail_ready.',
        'The task stops at detail_ready.',
    ),
)
def test_match_detail_ready_stop_contract_preserves_legacy_grammar(text: str) -> None:
    assert match_detail_ready_stop_contract(text) is not None


@pytest.mark.parametrize(
    'corpus',
    (
        {'task_packet': 'Expected stop: detail_ready.', 'execution_contract': 'Do not stop at detail_ready.'},
        {'task_packet': 'Expected stop: detail_ready.', 'orchestration_notes': 'Expected stop: blocked.'},
        {'task_packet': 'Expected stop: detail_ready.', 'execution_contract': '- > Expected stop: detail_ready'},
        {'task_packet': 'Expected stop: detail_ready.', 'execution_contract': '{"status":"detail_ready"}'},
        {'task_packet': 'Expected stop: detail_ready.', 'execution_contract': 'For task other-task, expected stop: detail_ready.'},
    ),
)
def test_match_detail_ready_stop_contract_rejects_unsafe_cross_artifact_corpus(corpus: dict[str, str]) -> None:
    assert match_detail_ready_stop_contract(corpus, task_id='current-task') is None


def test_match_detail_ready_stop_contract_allows_explicit_current_task_scope() -> None:
    assert match_detail_ready_stop_contract(
        {'task_packet': 'For task current-task, expected stop: detail_ready.'},
        task_id='current-task',
    ) is not None


@pytest.mark.parametrize(
    'text',
    (
        '1. > Expected stop: detail_ready.',
        '  1. - > Expected stop: detail_ready.',
        'Task: other-task\nExpected stop: detail_ready.',
        '**task_id:** `other-task`\nExpected stop: detail_ready.',
    ),
)
def test_match_detail_ready_stop_contract_rejects_ordered_quote_and_mismatched_scope_label(text: str) -> None:
    assert match_detail_ready_stop_contract(text, task_id='current-task') is None


@pytest.mark.parametrize('label', ('Task: `current-task`', '**task_id:** current-task'))
def test_match_detail_ready_stop_contract_allows_exact_current_scope_label(label: str) -> None:
    assert match_detail_ready_stop_contract(
        f'{label}\nExpected stop: detail_ready.',
        task_id='current-task',
    ) is not None


@pytest.mark.parametrize(
    'label',
    (
        'Task: [other-task](tasks/other-task)',
        'task-id: other-task',
        'Task: <other-task>',
        'Task: **other-task**',
    ),
)
def test_match_detail_ready_stop_contract_rejects_wrapped_other_task_scope(label: str) -> None:
    assert match_detail_ready_stop_contract(
        f'{label}\nExpected stop: detail_ready.',
        task_id='current-task',
    ) is None


@pytest.mark.parametrize(
    'label',
    (
        'Task: [current-task](tasks/current-task)',
        'task-id: `current-task`',
        'Task: <current-task>',
        'Task: **current-task**',
    ),
)
def test_match_detail_ready_stop_contract_allows_wrapped_current_task_scope(label: str) -> None:
    assert match_detail_ready_stop_contract(
        f'{label}\nExpected stop: detail_ready.',
        task_id='current-task',
    ) is not None
