from __future__ import annotations

from pathlib import Path

from rust_helpers import (
    CONTRACT_ECHO_CAPABILITY,
    RUST_HELPER_BIN_ENV,
    RUST_HELPERS_ENV,
    call_rust_helper_or_fallback,
)


def _write_helper(path: Path, body: str) -> Path:
    path.write_text('#!/usr/bin/env python3\n' + body, encoding='utf-8')
    path.chmod(0o755)
    return path


def test_disabled_by_default_uses_fallback_without_discovery(tmp_path: Path) -> None:
    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={'provider_transcript': 'do not report this'},
        fallback=lambda: {'source': 'python'},
        env={},
        which=lambda name: str(tmp_path / 'should-not-be-used'),
        script_root=tmp_path / 'repo',
    )

    assert result.value == {'source': 'python'}
    assert result.helper_used is False
    assert result.diagnostics[0].failure_kind == 'disabled'
    assert 'do not report this' not in str(result.diagnostics[0].to_dict())


def test_env_zero_forces_disabled_even_when_helper_exists(tmp_path: Path) -> None:
    helper = _write_helper(tmp_path / 'helper.py', 'raise SystemExit(99)\n')

    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={},
        fallback=lambda: 'python-only',
        env={RUST_HELPERS_ENV: '0', RUST_HELPER_BIN_ENV: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.value == 'python-only'
    assert result.diagnostics[0].failure_kind == 'disabled'


def test_missing_helper_falls_back_when_enabled(tmp_path: Path) -> None:
    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: 'auto'},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.value == 'fallback'
    assert result.diagnostics[0].failure_kind == 'missing'


def test_present_helper_returns_contract_payload(tmp_path: Path) -> None:
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
if sys.argv[1:] == ['--capabilities']:
    print(json.dumps({'schema_version': 1, 'capabilities': ['contract.echo']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {'accepted': True}}))
""",
    )

    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={'ignored': True},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.helper_used is True
    assert result.value == {'accepted': True}
    assert result.diagnostics == ()


def test_capability_probe_is_cached_for_unchanged_helper(tmp_path: Path) -> None:
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json, sys
from pathlib import Path
counter = Path(sys.argv[0]).with_suffix('.count')
if sys.argv[1:] == ['--capabilities']:
    value = int(counter.read_text() or '0') if counter.exists() else 0
    counter.write_text(str(value + 1))
    print(json.dumps({'schema_version': 1, 'capabilities': ['contract.echo']}))
else:
    request = json.loads(sys.stdin.read())
    print(json.dumps({'schema_version': 1, 'ok': True, 'capability': request['capability'], 'payload': {'accepted': True}}))
""",
    )

    for _ in range(2):
        result = call_rust_helper_or_fallback(
            capability=CONTRACT_ECHO_CAPABILITY,
            payload={},
            fallback=lambda: 'fallback',
            env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
            which=lambda name: None,
            script_root=tmp_path / 'repo',
        )
        assert result.helper_used is True

    assert (tmp_path / 'helper.count').read_text() == '1'


def test_invalid_json_from_capability_probe_falls_back(tmp_path: Path) -> None:
    helper = _write_helper(tmp_path / 'helper.py', "print('not json')\n")

    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.value == 'fallback'
    assert result.diagnostics[0].failure_kind == 'invalid_json'


def test_timeout_falls_back(tmp_path: Path) -> None:
    helper = _write_helper(tmp_path / 'helper.py', 'import time\ntime.sleep(2)\n')

    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
        timeout_s=0.01,
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.value == 'fallback'
    assert result.diagnostics[0].failure_kind == 'timeout'


def test_unknown_schema_and_unsupported_capability_fall_back(tmp_path: Path) -> None:
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import json
print(json.dumps({'schema_version': 999, 'capabilities': ['other']}))
""",
    )

    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.value == 'fallback'
    assert result.diagnostics[0].failure_kind == 'unknown_schema'

    helper = _write_helper(
        tmp_path / 'helper2.py',
        """import json
print(json.dumps({'schema_version': 1, 'capabilities': ['other']}))
""",
    )
    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    assert result.value == 'fallback'
    assert result.diagnostics[0].failure_kind == 'unsupported_capability'


def test_nonzero_exit_falls_back_with_redacted_stderr(tmp_path: Path) -> None:
    helper = _write_helper(
        tmp_path / 'helper.py',
        """import sys
sys.stderr.write('token abc123\\n')
raise SystemExit(2)
""",
    )

    result = call_rust_helper_or_fallback(
        capability=CONTRACT_ECHO_CAPABILITY,
        payload={'provider_transcript': 'secret transcript'},
        fallback=lambda: 'fallback',
        env={RUST_HELPERS_ENV: '1', RUST_HELPER_BIN_ENV: str(helper)},
        which=lambda name: None,
        script_root=tmp_path / 'repo',
    )

    diagnostic = result.diagnostics[0]
    assert diagnostic.failure_kind == 'nonzero_exit'
    assert diagnostic.stderr_tail == '[redacted stderr: 12 chars captured]'
    assert 'abc123' not in diagnostic.stderr_tail
    assert 'secret transcript' not in str(diagnostic.to_dict())
