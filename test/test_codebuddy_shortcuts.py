from __future__ import annotations

import pytest

from ccbd.handlers.project_clear import CLEAR_COMMANDS, DEFAULT_CLEAR_COMMAND
from ccbd.handlers.project_context import COMPACT_COMMANDS
from provider_model_shortcuts import (
    provider_model_flag_tokens,
    provider_model_runtime_env,
    provider_model_startup_args,
    startup_args_contain_model_flag,
    strip_provider_model_startup_args,
    supported_provider_model_shortcuts,
)
from provider_thinking_shortcuts import (
    normalize_provider_thinking,
    provider_thinking_levels,
    provider_thinking_runtime_env,
    provider_thinking_startup_args,
    startup_args_contain_thinking_flag,
    strip_provider_thinking_startup_args,
)


def test_codebuddy_model_uses_native_flag_without_environment_override() -> None:
    assert 'codebuddy' in supported_provider_model_shortcuts()
    assert provider_model_flag_tokens('codebuddy') == ('--model',)
    assert provider_model_startup_args('codebuddy', model='native-model') == (
        '--model', 'native-model',
    )
    assert provider_model_runtime_env('codebuddy', model='native-model') == {}
    assert strip_provider_model_startup_args(
        'codebuddy', ['--model', 'native-model', '--resume', 'session'], model='native-model',
    ) == ('--resume', 'session')


@pytest.mark.parametrize('args', [['--model', 'native-model'], ['--model=native-model']])
def test_codebuddy_model_detects_explicit_native_flag(args: list[str]) -> None:
    assert startup_args_contain_model_flag('codebuddy', args)


def test_codebuddy_model_does_not_claim_unsupported_alias() -> None:
    assert not startup_args_contain_model_flag('codebuddy', ['-m', 'native-model'])
    assert strip_provider_model_startup_args(
        'codebuddy', ['--model', 'other-model'], model='native-model',
    ) == ('--model', 'other-model')
    with pytest.raises(ValueError, match='model cannot be empty'):
        provider_model_startup_args('codebuddy', model=' ')


def test_codebuddy_thinking_matches_installed_cli_levels() -> None:
    assert provider_thinking_levels('codebuddy') == (
        'minimal', 'low', 'medium', 'high', 'xhigh', 'max',
    )
    assert provider_thinking_startup_args('codebuddy', thinking=None) == ()
    assert normalize_provider_thinking(' CodeBuddy ', ' XHIGH ') == 'xhigh'


@pytest.mark.parametrize('level', ['minimal', 'low', 'medium', 'high', 'xhigh', 'max'])
def test_codebuddy_thinking_round_trips_native_effort(level: str) -> None:
    assert provider_thinking_startup_args('codebuddy', thinking=level) == ('--effort', level)
    assert provider_thinking_runtime_env('codebuddy', thinking=level) == {}
    assert strip_provider_thinking_startup_args(
        'codebuddy', ['--effort', level, '--resume', 'session'], thinking=level,
    ) == ('--resume', 'session')


@pytest.mark.parametrize('level', ['off', 'none', 'ultra', ''])
def test_codebuddy_thinking_rejects_levels_outside_cli_contract(level: str) -> None:
    with pytest.raises(ValueError, match='must be one of'):
        provider_thinking_startup_args('codebuddy', thinking=level)


@pytest.mark.parametrize('args', [['--effort', 'high'], ['--effort=max']])
def test_codebuddy_thinking_detects_explicit_native_flag(args: list[str]) -> None:
    assert startup_args_contain_thinking_flag('codebuddy', args)


def test_codebuddy_thinking_does_not_claim_other_provider_flags() -> None:
    assert not startup_args_contain_thinking_flag('codebuddy', ['--thinking', 'high'])
    assert strip_provider_thinking_startup_args(
        'codebuddy', ['--effort', 'low'], thinking='high',
    ) == ('--effort', 'low')


def test_codebuddy_context_commands_use_verified_native_spellings() -> None:
    assert COMPACT_COMMANDS['codebuddy'] == '/compact'
    # Native /clear starts a new session; this asserts input spelling only,
    # not confirmation of the resulting session rotation.
    assert CLEAR_COMMANDS.get('codebuddy', DEFAULT_CLEAR_COMMAND) == '/clear'
