# Pi Provider Landing

Date: 2026-06-13

## Summary

Added Pi as an optional native CLI provider:

- Provider key: `pi`.
- Default command: `pi`.
- Override env: `PI_START_CMD`.
- Session file: `.pi-session`.
- Visible pane: shared simple-tmux launcher with isolated
  `PI_CODING_AGENT_DIR=<provider-state>/home` and
  `PI_CODING_AGENT_SESSION_DIR=<provider-state>/sessions`.
- Ask execution: per-job native subprocess using `pi --mode json`.
- Completion boundary: native `turn_end` event with assistant message content.

## Evidence

Official Pi docs show:

- npm install package `@earendil-works/pi-coding-agent`.
- command `pi`.
- `pi --mode json "Your prompt"` emits JSON lines.
- JSON events include `turn_end` with the final assistant message.
- `PI_CODING_AGENT_DIR` and `PI_CODING_AGENT_SESSION_DIR` isolate config and
  sessions.

## Implementation

Touched source surfaces:

- `lib/provider_backends/pi/`
- `lib/provider_backends/native_cli_support/launcher.py`
- `lib/provider_backends/native_cli_support/execution.py`
- provider registry/spec/pathing/runtime command maps
- storage classification
- deterministic provider stub and focused provider tests

## Verification

- `python -m py_compile lib/provider_backends/pi/*.py
  lib/provider_backends/native_cli_support/launcher.py
  lib/provider_core/runtime_specs.py lib/provider_core/runtime_shared.py
  lib/provider_core/pathing.py
  lib/provider_core/registry_runtime/builtin_backends.py
  test/stubs/provider_stub.py`
- `python -m pytest -q test/test_native_cli_provider_execution.py
  test/test_v2_provider_catalog.py test/test_v2_provider_core_registry.py
  test/test_v2_execution_registry.py test/test_runtime_specs.py
  test/test_v2_runtime_launch.py::test_provider_start_parts_respect_env_override
  test/test_v2_runtime_launch.py::test_provider_start_parts_fall_back_to_default_binary
  test/test_v2_runtime_launch.py::test_native_cli_launcher_builds_provider_state_payload
  test/test_storage_classification.py`: `55 passed`
- Focused suite after adding control-plane coverage:
  `python -m pytest -q test/test_runtime_env_control_plane.py
  test/test_native_cli_provider_execution.py test/test_v2_provider_catalog.py
  test/test_v2_provider_core_registry.py test/test_v2_execution_registry.py
  test/test_runtime_specs.py
  test/test_v2_runtime_launch.py::test_provider_start_parts_respect_env_override
  test/test_v2_runtime_launch.py::test_provider_start_parts_fall_back_to_default_binary
  test/test_v2_runtime_launch.py::test_native_cli_launcher_builds_provider_state_payload
  test/test_storage_classification.py`: `62 passed`
- Installed `@earendil-works/pi-coding-agent@0.79.3` into the test lab npm
  prefix; `pi --version` returned `0.79.3`.
- Stub-backed source-runtime smoke mounted six next-wave providers and verified
  `pi1` ask completion with reply reason `pi_run_stop`.

## Follow-Ups

- Run authenticated real Pi ask after user credentials/provider setup are
  available.
- Decide whether Pi should receive richer CCB ask guidance through native
  skills/resources rather than prompt wrapping only.
