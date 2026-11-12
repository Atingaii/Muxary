# Next-Wave CLI Lab

Date: 2026-06-13

## Scope

Install and inspect the five requested CLI candidates before implementing CCB
provider support:

- Qwen Code
- GitHub Copilot CLI
- Cursor Agent
- Kiro CLI
- Charm Crush

The lab was created outside the source checkout at:

`/home/bfly/yunwei/test_ccb2/cli-integration-lab`

## Environment

- Node: `v22.20.0`
- npm: `10.9.3`
- `go`: not installed
- npm prefix:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/npm-prefix`
- isolated installer home:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/home`

## Installed CLIs

| CLI | Install source | Binary | Version check |
| :--- | :--- | :--- | :--- |
| Qwen Code | `npm install -g @qwen-code/qwen-code@latest` | `qwen` | `0.18.0` |
| GitHub Copilot CLI | `npm install -g @github/copilot@latest` | `copilot` | `GitHub Copilot CLI 1.0.61` |
| Cursor Agent | `https://cursor.com/install` | `agent` | `2026.06.12-19-59-36-f6aba9a` |
| Kiro CLI | `https://cli.kiro.dev/install` | `kiro-cli` | `kiro-cli 2.7.0` |
| Charm Crush | `npm install -g @charmland/crush@latest` | `crush` | `crush version v0.76.0` |

Installed lab binaries:

- npm prefix: `qwen`, `copilot`, `crush`.
- isolated home `.local/bin`: `agent`, `cursor-agent`, `kiro-cli`,
  `kiro-cli-chat`, `kiro-cli-term`.

## Source And Bundle Locations

- Qwen source:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/src/qwen-code`
  from `https://github.com/QwenLM/qwen-code.git`.
- Copilot source:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/src/copilot-cli`
  from `https://github.com/github/copilot-cli.git`.
- Crush source:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/src/crush`
  from `https://github.com/charmbracelet/crush.git`.
- Kiro project/docs source:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/src/kiro`
  from `https://github.com/kirodotdev/Kiro.git`; this is not full CLI source.
- Cursor installed bundle:
  `/home/bfly/yunwei/test_ccb2/cli-integration-lab/home/.local/share/cursor-agent/versions/2026.06.12-19-59-36-f6aba9a`.

## Integration Ranking

1. `qwen`: best first candidate. It has one-shot prompt mode, structured JSON
   output, `--session-id`, and `QWEN_HOME` state isolation.
2. `cursor`: strong structured candidate. `agent --print --output-format
   stream-json --workspace <path> --trust` maps directly to CCB subprocess
   execution, but public source is not available.
3. `copilot`: strong structured candidate. Prompt-mode JSONL, `COPILOT_HOME`,
   `--session-id`, and `--plugin-dir` make the adapter plausible; auth and
   permission defaults need careful validation.
4. `crush`: good deterministic candidate. `crush run` exits on a matching
   source-level `RunComplete` and supports `--data-dir`, but stdout is the
   first practical completion surface.
5. `kiro`: installable but riskiest. Chat mode has `--no-interactive` and
   `--wrap never`, but no confirmed structured output for normal chat turns.

## First Implementation Notes

- Keep all first adapters per-job subprocess based where possible.
- Do not register an optional provider until the backend has a modern
  `manifest.py`, `launcher.py`, `execution.py`, runtime spec, config loader
  coverage, registry tests, and parser tests.
- Reuse MiMo's structured-result execution pattern for Qwen, Cursor, and
  Copilot where their output formats allow it.
- Use prompt wrapping for inherited CCB ask guidance unless a native
  skill/plugin surface is source-confirmed and covered by tests.
