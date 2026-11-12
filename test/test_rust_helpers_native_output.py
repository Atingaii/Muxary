from __future__ import annotations

import json
from pathlib import Path

import pytest

from provider_backends.native_cli_support import observe_jsonl_output
from rust_helpers import RUST_HELPER_BIN_ENV, RUST_HELPERS_ENV
from rust_helpers_native_output import RUST_NATIVE_OUTPUT_ENV, observe_native_jsonl_output


def _write_jsonl(path: Path, rows: list[object | str]) -> Path:
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            if isinstance(row, str):
                handle.write(row + '\n')
            else:
                handle.write(json.dumps(row, ensure_ascii=False) + '\n')
    return path


def _observation_dict(path: Path) -> dict[str, object]:
    observation = observe_jsonl_output(path)
    return {
        'text': observation.text,
        'finished': observation.finished,
        'finish_reason': observation.finish_reason,
        'turn_ref': observation.turn_ref,
        'completed_at': observation.completed_at,
        'error': observation.error,
        'intermediate': observation.intermediate,
    }


def _write_helper(path: Path, body: str) -> Path:
    path.write_text('#!/usr/bin/env python3\n' + body, encoding='utf-8')
    path.chmod(0o755)
    return path


def test_native_output_global_zero_disables_default_auto(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'hello'}])

    def should_not_discover(name: str):
        raise AssertionError(f'unexpected helper discovery: {name}')

    result = observe_native_jsonl_output(
        output,
        env={RUST_HELPERS_ENV: '0'},
        which=should_not_discover,
        script_root=tmp_path / 'repo',
    )

    assert result.helper_used is False
    assert result.value == _observation_dict(output)
    assert result.diagnostics[0].failure_kind == 'disabled'


def test_native_output_default_auto_uses_helper_when_available(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python'}])
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'native.output.observe', 'payload': {
        'text': 'helper-default',
        'finished': True,
        'finish_reason': 'completed',
        'turn_ref': 'turn-default',
        'completed_at': '2026-06-15T00:00:00Z',
        'error': '',
        'intermediate': False,
    }}))
""",
    )

    result = observe_native_jsonl_output(
        output,
        env={RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value['text'] == 'helper-default'


def test_native_output_default_auto_falls_back_when_helper_missing(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python fallback'}])

    result = observe_native_jsonl_output(
        output,
        env={RUST_HELPER_BIN_ENV: str(tmp_path / 'missing-helper')},
    )

    assert result.helper_used is False
    assert result.value == _observation_dict(output)
    assert result.diagnostics[0].failure_kind == 'missing'


def test_native_output_zero_forces_python_fallback(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'hello'}])
    helper = _write_helper(tmp_path / 'helper.py', 'raise SystemExit(99)\n')

    result = observe_native_jsonl_output(
        output,
        env={RUST_NATIVE_OUTPUT_ENV: '0', RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is False
    assert result.value == _observation_dict(output)
    assert result.diagnostics[0].failure_kind == 'disabled'


@pytest.mark.parametrize('mode', ['1', 'auto', 'required'])
def test_native_output_enabled_uses_stub_helper(tmp_path: Path, mode: str) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python'}])
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'native.output.observe', 'payload': {
        'text': 'helper',
        'finished': True,
        'finish_reason': 'completed',
        'turn_ref': 'turn-1',
        'completed_at': '2026-06-15T00:00:00Z',
        'error': '',
        'intermediate': False,
    }}))
""",
    )

    result = observe_native_jsonl_output(
        output,
        env={RUST_HELPERS_ENV: '0', RUST_NATIVE_OUTPUT_ENV: mode, RUST_HELPER_BIN_ENV: str(helper)},
    )

    assert result.helper_used is True
    assert result.value['text'] == 'helper'
    assert result.value['finished'] is True
    assert result.diagnostics == ()


@pytest.mark.parametrize('mode', ['1', 'required'])
def test_production_observer_uses_helper_when_native_output_enabled(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mode: str
) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python'}])
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'native.output.observe', 'payload': {
        'text': 'helper-production',
        'finished': True,
        'finish_reason': 'completed',
        'turn_ref': 'turn-production',
        'completed_at': '2026-06-15T00:00:00Z',
        'error': '',
        'intermediate': False,
    }}))
""",
    )
    monkeypatch.setenv(RUST_NATIVE_OUTPUT_ENV, mode)
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))

    observation = observe_jsonl_output(output)

    assert observation.text == 'helper-production'
    assert observation.finished is True
    assert observation.turn_ref == 'turn-production'


def test_production_observer_default_auto_uses_helper_when_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python'}])
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'native.output.observe', 'payload': {
        'text': 'helper-default-production',
        'finished': True,
        'finish_reason': 'completed',
        'turn_ref': 'turn-default-production',
        'completed_at': '2026-06-15T00:00:00Z',
        'error': '',
        'intermediate': False,
    }}))
""",
    )
    monkeypatch.delenv(RUST_NATIVE_OUTPUT_ENV, raising=False)
    monkeypatch.delenv(RUST_HELPERS_ENV, raising=False)
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(helper))

    observation = observe_jsonl_output(output)

    assert observation.text == 'helper-default-production'
    assert observation.finished is True
    assert observation.turn_ref == 'turn-default-production'


def test_production_observer_default_auto_falls_back_when_helper_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python fallback'}])
    monkeypatch.delenv(RUST_NATIVE_OUTPUT_ENV, raising=False)
    monkeypatch.delenv(RUST_HELPERS_ENV, raising=False)
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(tmp_path / 'missing-helper'))

    observation = observe_jsonl_output(output)

    assert observation.text == 'python fallback'
    assert observation.finished is False


def test_production_observer_required_missing_helper_raises_without_python_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python fallback'}])
    monkeypatch.setenv(RUST_NATIVE_OUTPUT_ENV, 'required')
    monkeypatch.setenv(RUST_HELPER_BIN_ENV, str(tmp_path / 'missing-helper'))

    with pytest.raises(RuntimeError, match='no Python fallback'):
        observe_jsonl_output(output)


def test_force_python_fallback_matches_current_observer_for_nested_events(tmp_path: Path) -> None:
    output = _write_jsonl(
        tmp_path / 'native.jsonl',
        [
            '',
            'not json',
            ['array'],
            {'role': 'user', 'text': 'ignore me'},
            {'type': 'message_delta', 'message': {'role': 'assistant', 'content': [{'text': 'hello '}]}, 'id': 'turn-a'},
            {'type': 'tool_call', 'role': 'assistant', 'status': 'tool_calls', 'name': 'demo'},
            {
                'type': 'final_result',
                'result': {
                    'role': 'assistant',
                    'text': 'world',
                    'finish_reason': 'stop',
                    'updated_at': '2026-06-15T00:00:01Z',
                },
            },
        ],
    )

    result = observe_native_jsonl_output(output, env={RUST_NATIVE_OUTPUT_ENV: '0'})

    assert result.helper_used is False
    assert result.value == _observation_dict(output)
    assert result.value['text'] == 'hello world'
    assert result.value['finished'] is True
    assert result.value['intermediate'] is True
    assert result.value['finish_reason'] == 'stop'
    assert result.value['turn_ref'] == 'turn-a'


def test_error_events_and_missing_file_match_current_observer(tmp_path: Path) -> None:
    output = _write_jsonl(
        tmp_path / 'native-error.jsonl',
        [
            {'type': 'error', 'message': {'text': 'permission denied'}, 'request_id': 'req-1'},
            {'role': 'assistant', 'text': 'ignored after error?'},
        ],
    )
    missing = tmp_path / 'missing.jsonl'

    assert observe_native_jsonl_output(output, env={RUST_NATIVE_OUTPUT_ENV: '0'}).value == _observation_dict(output)
    assert observe_native_jsonl_output(missing, env={RUST_NATIVE_OUTPUT_ENV: '0'}).value == _observation_dict(missing)


def test_helper_failures_fallback_without_leaking_content(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'provider transcript secret'}])

    missing = observe_native_jsonl_output(output, env={RUST_NATIVE_OUTPUT_ENV: '1'}, which=lambda name: None, script_root=tmp_path / 'repo')
    assert missing.value == _observation_dict(output)
    assert missing.diagnostics[0].failure_kind == 'missing'

    crash_helper = _write_helper(
        tmp_path / 'crash.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    sys.stderr.write('raw secret stderr')
    raise SystemExit(2)
""",
    )
    crash = observe_native_jsonl_output(output, env={RUST_NATIVE_OUTPUT_ENV: '1', RUST_HELPER_BIN_ENV: str(crash_helper)})
    assert crash.value == _observation_dict(output)
    assert crash.diagnostics[0].failure_kind == 'nonzero_exit'
    diagnostics = str([diagnostic.to_dict() for diagnostic in crash.diagnostics])
    assert 'provider transcript secret' not in diagnostics
    assert 'raw secret stderr' not in diagnostics

    bad_payload_helper = _write_helper(
        tmp_path / 'bad_payload.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'native.output.observe', 'payload': {'text': 'provider transcript secret'}}))
""",
    )
    bad_payload = observe_native_jsonl_output(output, env={RUST_NATIVE_OUTPUT_ENV: '1', RUST_HELPER_BIN_ENV: str(bad_payload_helper)})
    assert bad_payload.helper_used is False
    assert bad_payload.value == _observation_dict(output)
    assert bad_payload.diagnostics[0].failure_kind == 'unknown_schema'
    assert 'provider transcript secret' not in str([diagnostic.to_dict() for diagnostic in bad_payload.diagnostics])


def test_native_output_required_missing_helper_raises_without_python_fallback(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python fallback'}])

    with pytest.raises(RuntimeError, match='no Python fallback'):
        observe_native_jsonl_output(
            output,
            env={RUST_NATIVE_OUTPUT_ENV: 'required'},
            which=lambda name: None,
            script_root=tmp_path / 'repo',
        )


def test_native_output_required_bad_payload_raises_without_python_fallback(tmp_path: Path) -> None:
    output = _write_jsonl(tmp_path / 'native.jsonl', [{'role': 'assistant', 'text': 'python fallback'}])
    bad_payload_helper = _write_helper(
        tmp_path / 'bad_payload.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['native.output.observe']}))
else:
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': 'native.output.observe', 'payload': {'text': 'invalid'}}))
""",
    )

    with pytest.raises(RuntimeError, match='no Python fallback'):
        observe_native_jsonl_output(
            output,
            env={RUST_NATIVE_OUTPUT_ENV: 'required', RUST_HELPER_BIN_ENV: str(bad_payload_helper)},
        )
