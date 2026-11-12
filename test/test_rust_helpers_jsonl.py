from __future__ import annotations

import json
from pathlib import Path

import pytest

from rust_helpers import RUST_HELPER_BIN_ENV, RUST_HELPERS_ENV
from rust_helpers_jsonl import (
    RUST_JSONL_ENV,
    read_job_tail_summaries_required,
    read_jsonl_tail_batch,
    read_jsonl_tail_strict_required,
)
from storage.jsonl_store import JsonlStore


def _write_jsonl(path: Path, lines: list[object | str]) -> Path:
    with path.open('w', encoding='utf-8') as handle:
        for line in lines:
            if isinstance(line, str):
                handle.write(line + '\n')
            else:
                handle.write(json.dumps(line, ensure_ascii=False) + '\n')
    return path


def _write_helper(path: Path, body: str) -> Path:
    path.write_text('#!/usr/bin/env python3\n' + body, encoding='utf-8')
    path.chmod(0o755)
    return path


def _jsonl_stub_helper(path: Path) -> Path:
    return _write_helper(
        path,
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['contract.echo', 'jsonl.tail']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({
        'schema_version': 1,
        'ok': True,
        'capability': request['capability'],
        'payload': {
            'requests': [
                {'id': item['id'], 'rows': [{'source': 'helper', 'id': item['id'], 'n': item['n']}]}
                for item in request['payload']['requests']
            ]
        },
    }))
""",
    )


def _jsonl_strict_stub_helper(path: Path, *, payload: str | None = None) -> Path:
    payload = payload or """{
        'requests': [
            {'id': item['id'], 'rows': [{'source': 'strict-helper', 'id': item['id'], 'n': item['n']}]}
            for item in request['payload']['requests']
        ],
        'error': None,
    }"""
    return _write_helper(
        path,
        f"""import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({{'schema_version': 1, 'capabilities': ['contract.echo', 'jsonl.tail.strict']}}))
else:
    request = json.loads(sys.stdin.read())
    payload = {payload}
    print(json.dumps({{'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': payload}}))
""",
    )


def _job_summary_stub_helper(path: Path) -> Path:
    return _write_helper(
        path,
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['jobs.tail.summary']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {
        'requests': [
            {'id': item['id'], 'jobs': [{
                'job_id': 'job-summary-helper',
                'agent_name': item['id'],
                'target_name': item['id'],
                'provider': 'codex',
                'status': 'completed',
                'terminal_decision': {'reason': 'task_complete'},
                'created_at': '2026-06-15T00:00:00Z',
                'updated_at': '2026-06-15T00:00:01Z',
                'provider_options': {},
                'request': {
                    'project_id': 'proj',
                    'to_agent': item['id'],
                    'from_actor': 'cmd',
                    'body': 'summary body',
                    'task_id': None,
                    'reply_to': None,
                    'message_type': 'ask',
                    'delivery_scope': 'single',
                    'silence_on_success': False,
                    'route_options': {},
                    'body_artifact': None,
                },
            }]}
            for item in request['payload']['requests']
        ],
        'error': None,
    }}))
""",
    )


def test_default_disabled_does_not_discover_even_if_global_helpers_enabled(tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}, {'seq': 2}])

    def should_not_discover(name: str):
        raise AssertionError(f'unexpected helper discovery: {name}')

    result = read_jsonl_tail_batch(
        [{'id': 'events', 'path': str(data), 'n': 1}],
        env={RUST_HELPERS_ENV: '1'},
        which=should_not_discover,
        script_root=tmp_path / 'repo',
    )

    assert result.helper_used is False
    assert result.value == {'requests': [{'id': 'events', 'rows': [{'seq': 2}]}]}
    assert result.diagnostics[0].failure_kind == 'disabled'


def test_jsonl_zero_forces_fallback_even_when_helper_exists(tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}, {'seq': 2}])
    helper = _write_helper(tmp_path / 'helper.py', 'raise SystemExit(99)\n')

    result = read_jsonl_tail_batch(
        [{'id': 'events', 'path': str(data), 'n': 2}],
        env={RUST_JSONL_ENV: '0', RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is False
    assert result.value['requests'][0]['rows'] == [{'seq': 1}, {'seq': 2}]
    assert result.diagnostics[0].failure_kind == 'disabled'


@pytest.mark.parametrize('mode', ['1', 'auto'])
def test_jsonl_enabled_uses_stub_helper_and_overrides_global_disabled(tmp_path: Path, mode: str) -> None:
    helper = _jsonl_stub_helper(tmp_path / 'helper.py')
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}])

    result = read_jsonl_tail_batch(
        [{'id': 'events', 'path': str(data), 'n': 1}],
        env={RUST_HELPERS_ENV: '0', RUST_JSONL_ENV: mode, RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value == {'requests': [{'id': 'events', 'rows': [{'source': 'helper', 'id': 'events', 'n': 1}]}]}
    assert result.diagnostics == ()


def test_batch_missing_empty_malformed_unicode_large_and_tail_sizes(tmp_path: Path) -> None:
    mixed = _write_jsonl(
        tmp_path / 'mixed.jsonl',
        [
            {'seq': 1, 'text': 'first'},
            '',
            'not json',
            ['array'],
            {'seq': 2, 'text': 'snowman ☃'},
            {'seq': 3, 'payload': 'x' * (120 * 1024)},
        ],
    )
    empty = _write_jsonl(tmp_path / 'empty.jsonl', [])

    result = read_jsonl_tail_batch(
        [
            {'id': 'tail-two', 'path': str(mixed), 'n': 2},
            {'id': 'missing', 'path': str(tmp_path / 'missing.jsonl'), 'n': 5},
            {'id': 'empty', 'path': str(empty), 'n': 5},
            {'id': 'zero', 'path': str(mixed), 'n': 0},
            {'id': 'all', 'path': str(mixed), 'n': 100},
        ],
        env={},
    )

    payload = result.value['requests']
    assert payload[0]['rows'][0]['seq'] == 2
    assert payload[0]['rows'][0]['text'] == 'snowman ☃'
    assert payload[0]['rows'][1]['seq'] == 3
    assert len(payload[0]['rows'][1]['payload']) > 100 * 1024
    assert payload[1]['rows'] == []
    assert payload[2]['rows'] == []
    assert payload[3]['rows'] == []
    assert [row['seq'] for row in payload[4]['rows']] == [1, 2, 3]


def test_negative_n_raises_value_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match='non-negative'):
        read_jsonl_tail_batch([{'id': 'bad', 'path': str(tmp_path / 'events.jsonl'), 'n': -1}], env={})


def test_missing_crash_timeout_invalid_json_unknown_schema_and_unsupported_fallback(tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}, {'seq': 2}])
    request = [{'id': 'events', 'path': str(data), 'n': 1}]

    missing = read_jsonl_tail_batch(
        request,
        env={RUST_JSONL_ENV: '1'},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )
    assert missing.value['requests'][0]['rows'] == [{'seq': 2}]
    assert missing.diagnostics[0].failure_kind == 'missing'

    crash_helper = _write_helper(
        tmp_path / 'crash.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['jsonl.tail']}))
else:
    sys.stderr.write('secret token and provider transcript')
    raise SystemExit(2)
""",
    )
    crash = read_jsonl_tail_batch(request, env={RUST_JSONL_ENV: '1', RUST_HELPER_BIN_ENV: str(crash_helper)})
    assert crash.value['requests'][0]['rows'] == [{'seq': 2}]
    assert crash.diagnostics[0].failure_kind == 'nonzero_exit'
    assert 'secret token' not in str([diagnostic.to_dict() for diagnostic in crash.diagnostics])
    assert 'provider transcript' not in str([diagnostic.to_dict() for diagnostic in crash.diagnostics])

    timeout_helper = _write_helper(tmp_path / 'timeout.py', 'import time\ntime.sleep(2)\n')
    timeout = read_jsonl_tail_batch(
        request,
        env={RUST_JSONL_ENV: '1', RUST_HELPER_BIN_ENV: str(timeout_helper)},
        timeout_s=0.01,
    )
    assert timeout.value['requests'][0]['rows'] == [{'seq': 2}]
    assert timeout.diagnostics[0].failure_kind == 'timeout'

    invalid_json_helper = _write_helper(tmp_path / 'invalid.py', "print('not json')\n")
    invalid = read_jsonl_tail_batch(request, env={RUST_JSONL_ENV: '1', RUST_HELPER_BIN_ENV: str(invalid_json_helper)})
    assert invalid.value['requests'][0]['rows'] == [{'seq': 2}]
    assert invalid.diagnostics[0].failure_kind == 'invalid_json'

    unknown_schema_helper = _write_helper(
        tmp_path / 'schema.py',
        """import json
print(json.dumps({'schema_version': 999, 'capabilities': ['jsonl.tail']}))
""",
    )
    unknown = read_jsonl_tail_batch(request, env={RUST_JSONL_ENV: '1', RUST_HELPER_BIN_ENV: str(unknown_schema_helper)})
    assert unknown.value['requests'][0]['rows'] == [{'seq': 2}]
    assert unknown.diagnostics[0].failure_kind == 'unknown_schema'

    unsupported_helper = _write_helper(
        tmp_path / 'unsupported.py',
        """import json
print(json.dumps({'schema_version': 1, 'capabilities': ['contract.echo']}))
""",
    )
    unsupported = read_jsonl_tail_batch(request, env={RUST_JSONL_ENV: '1', RUST_HELPER_BIN_ENV: str(unsupported_helper)})
    assert unsupported.value['requests'][0]['rows'] == [{'seq': 2}]
    assert unsupported.diagnostics[0].failure_kind == 'unsupported_capability'


def test_invalid_helper_payload_falls_back_and_diagnostics_do_not_leak_content(tmp_path: Path) -> None:
    secret_row = {'seq': 1, 'payload': 'provider transcript secret'}
    data = _write_jsonl(tmp_path / 'events.jsonl', [secret_row])
    helper = _write_helper(
        tmp_path / 'bad_payload.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['jsonl.tail']}))
else:
    sys.stderr.write('raw secret stderr')
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'jsonl.tail', 'payload': {'unexpected': 'provider transcript secret'}}))
""",
    )

    result = read_jsonl_tail_batch(
        [{'id': 'events', 'path': str(data), 'n': 1}],
        env={RUST_JSONL_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is False
    assert result.value['requests'][0]['rows'] == [secret_row]
    diagnostics = [diagnostic.to_dict() for diagnostic in result.diagnostics]
    assert result.diagnostics[0].failure_kind == 'unknown_schema'
    assert 'provider transcript secret' not in str(diagnostics)
    assert 'raw secret stderr' not in str(diagnostics)


def test_strict_required_uses_helper_and_has_no_python_fallback(tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}])
    helper = _jsonl_strict_stub_helper(tmp_path / 'helper.py')

    result = read_jsonl_tail_strict_required(
        data,
        1,
        env={RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value == [{'source': 'strict-helper', 'id': 'default', 'n': 1}]


def test_strict_required_missing_helper_raises_without_python_fallback(tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}])

    with pytest.raises(RuntimeError, match='no Python fallback'):
        read_jsonl_tail_strict_required(
            data,
            1,
            env={RUST_HELPER_BIN_ENV: str(tmp_path / 'missing-helper')},
        )


def test_strict_required_maps_helper_errors_to_store_style_exceptions(tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}])
    non_object_helper = _jsonl_strict_stub_helper(
        tmp_path / 'non_object.py',
        payload=f"{{'requests': [], 'error': {{'kind': 'non_object', 'path': {str(data)!r}, 'message': 'expected object'}}}}",
    )
    invalid_json_helper = _jsonl_strict_stub_helper(
        tmp_path / 'invalid_json.py',
        payload=f"{{'requests': [], 'error': {{'kind': 'invalid_json', 'path': {str(data)!r}, 'message': 'Expecting value'}}}}",
    )

    with pytest.raises(ValueError, match='expected JSON object rows'):
        read_jsonl_tail_strict_required(data, 1, env={RUST_HELPER_BIN_ENV: str(non_object_helper)})

    with pytest.raises(json.JSONDecodeError):
        read_jsonl_tail_strict_required(data, 1, env={RUST_HELPER_BIN_ENV: str(invalid_json_helper)})


def test_jsonl_store_read_tail_uses_strict_helper_when_required(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}])
    helper = _jsonl_strict_stub_helper(tmp_path / 'helper.py')
    monkeypatch.setenv('CCB_RUST_JSONL_STORE', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))

    rows = JsonlStore().read_tail(data, 1)

    assert rows == [{'source': 'strict-helper', 'id': 'default', 'n': 1}]


def test_jsonl_store_read_tail_required_helper_missing_does_not_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    data = _write_jsonl(tmp_path / 'events.jsonl', [{'seq': 1}])
    monkeypatch.setenv('CCB_RUST_JSONL_STORE', '1')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(tmp_path / 'missing-helper'))

    with pytest.raises(RuntimeError, match='no Python fallback'):
        JsonlStore().read_tail(data, 1)


def test_job_tail_summaries_required_uses_helper_without_python_fallback(tmp_path: Path) -> None:
    helper = _job_summary_stub_helper(tmp_path / 'job_summary.py')

    result = read_job_tail_summaries_required(
        [{'id': 'agent1', 'path': str(tmp_path / 'missing.jsonl'), 'n': 4}],
        env={RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value['requests'][0]['jobs'][0]['job_id'] == 'job-summary-helper'
    assert result.value['requests'][0]['jobs'][0]['request']['body'] == 'summary body'


def test_job_tail_summaries_required_missing_helper_raises_without_python_fallback(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match='no Python fallback'):
        read_job_tail_summaries_required(
            [{'id': 'agent1', 'path': str(tmp_path / 'missing.jsonl'), 'n': 4}],
            env={RUST_HELPER_BIN_ENV: str(tmp_path / 'missing-helper')},
        )
