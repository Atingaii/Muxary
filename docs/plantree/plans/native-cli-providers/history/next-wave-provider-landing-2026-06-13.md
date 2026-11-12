# Next-Wave Provider Landing

Date: 2026-06-13

## Scope

Landed minimal source support for five optional built-in native CLI providers:

- `qwen`
- `cursor`
- `copilot`
- `crush`
- `kiro`

## Implementation Summary

- Added shared `provider_backends.native_cli_support` modules for:
  - structured-result manifests
  - generic session binding
  - simple tmux launcher state payloads
  - per-job subprocess execution, stdout/stderr artifacts, JSONL parsing,
    stdout-on-exit completion, empty reply diagnostics, and nonzero exit
    failures
- Upgraded `qwen` and `copilot` from old partial protocol-only packages to
  modern backend packages while leaving old protocol helpers in place for
  compatibility tests.
- Added new `cursor`, `crush`, and `kiro` provider backend packages.
- Registered all five providers in provider-core optional built-ins, runtime
  specs, command defaults, session filename mapping, and execution registry.
- Extended `test/stubs/provider_stub.py` with deterministic native run modes
  for JSONL providers and stdout providers.

## Completion Contract

- Qwen: `qwen --bare --output-format stream-json --session-id <job>`.
- Cursor: `agent --print --output-format stream-json --workspace <workdir>
  --trust`.
- Copilot: `copilot -C <workdir> -p <prompt> --output-format json
  --session-id <job>`.
- Crush: `crush --data-dir <state> --cwd <workdir> run --quiet <prompt>`.
- Kiro: `kiro-cli chat --no-interactive --wrap never <prompt>`.

Qwen, Cursor, and Copilot complete from final/result JSON envelopes. Crush and
Kiro complete from process exit plus stdout. None of these adapters require
model-printed `CCB_DONE`.

## Verification

- Compile check passed for new provider modules, shared native CLI support,
  provider-core tables, and provider stub.
- Focused tests:
  `pytest -q test/test_native_cli_provider_execution.py
  test/test_v2_provider_catalog.py test/test_v2_provider_core_registry.py
  test/test_v2_execution_registry.py test/test_runtime_specs.py
  test/test_v2_runtime_launch.py::test_provider_start_parts_respect_env_override
  test/test_v2_runtime_launch.py::test_provider_start_parts_fall_back_to_default_binary
  test/test_v2_runtime_launch.py::test_native_cli_launcher_builds_provider_state_payload`
  returned `35 passed`.
- Control-plane env regression passed:
  `pytest -q test/test_runtime_env_control_plane.py
  test/test_v2_runtime_launch.py::test_provider_start_parts_respect_env_override
  test/test_v2_runtime_launch.py::test_provider_start_parts_fall_back_to_default_binary`
  returned `9 passed`.
- Initial wider touched-provider suite passed with `218 passed`; later
  post-timeout and storage-classification reruns are recorded below.
- Native CLI adapter timeout regression passed:
  `pytest -q test/test_native_cli_provider_execution.py` returned `23 passed`
  after adding provider-specific run-timeout coverage for all five adapters.
- Source-runtime smoke passed from
  `/home/bfly/yunwei/test_ccb2/next_wave_provider_smoke`:
  `config validate`, `ccb_test -s`, five ask traces, and queue idle check all
  succeeded.
- Real installed CLI version smoke passed for Qwen, Cursor Agent, Copilot,
  Crush, and Kiro from `/home/bfly/yunwei/test_ccb2/cli-integration-lab`.
- `git diff --check` passed.

## Review Follow-Up

Talk1 review found one release-blocking drift: Crush ask execution used
`--data-dir <provider-state>` but the visible pane launcher did not, so visible
interactive Crush state was not isolated the same way as CCB ask execution.

Follow-up changes:

- Shared native CLI launchers can now derive visible-pane arguments from
  prepared provider-state.
- Crush visible panes now start with
  `crush --data-dir <provider-state>/data ...`.
- Storage classification now covers Qwen, Cursor, Copilot, Crush, and Kiro
  provider-state contents as native CLI provider-owned session/cache or
  projected skill evidence.

Verification:

- `pytest -q
  test/test_v2_runtime_launch.py::test_native_cli_launcher_builds_provider_state_payload
  test/test_storage_classification.py`: `14 passed`.
- `pytest -q test/test_native_cli_provider_execution.py
  test/test_runtime_env_control_plane.py`: `30 passed`.
- `python -m py_compile lib/provider_backends/native_cli_support/launcher.py
  lib/provider_backends/crush/launcher.py
  lib/storage_classification/provider_home.py
  test/test_v2_runtime_launch.py test/test_storage_classification.py`: passed.
- Wider touched-provider suite including storage classification:
  `pytest -q test/test_native_cli_provider_execution.py
  test/test_v2_provider_catalog.py test/test_v2_provider_core_registry.py
  test/test_v2_execution_registry.py test/test_runtime_specs.py
  test/test_v2_config_loader.py test/test_v2_runtime_launch.py
  test/test_repo_hygiene.py test/test_runtime_env_control_plane.py
  test/test_storage_classification.py`: `232 passed`.
- Post-review source-runtime recheck from
  `/home/bfly/yunwei/test_ccb2/next_wave_provider_smoke` confirmed Crush
  visible-pane `--data-dir` in `.ccb/.crush-crush1-session`, completed asks for
  Qwen/Cursor/Copilot/Crush/Kiro, observed queue depth 0 and pending replies 0,
  then stopped the runtime with `ccb_test kill -f`.
- Full source gate after review follow-up:
  `pytest test/ -q -m "not provider_blackbox"`:
  `2621 passed, 2 skipped, 21 deselected`.
- `python -m compileall -q lib bin ccb` and `git diff --check`: passed.

## Follow-Up

- Decide provider-specific auth diagnostics and native skill projection after
  the first source-runtime pass.
- Review release readiness with the known `main` CI failure from the already
  published `v7.5.1` gate tracked separately.
