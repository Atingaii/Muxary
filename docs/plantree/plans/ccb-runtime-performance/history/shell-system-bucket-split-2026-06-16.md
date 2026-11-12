# Shell/System Bucket Split

Date: 2026-06-16

## Method

Main agent reran source-runtime-safe profiling from `/home/bfly/yunwei/test_ccb2`
with isolated state:

- `HOME=/home/bfly/yunwei/test_ccb2/source_home`
- `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`
- runtime wrapper: `/home/bfly/yunwei/ccb_source/ccb_test`

Before rerunning, the profiler was corrected to exclude unrelated machine-wide
processes from project-scoped samples, exclude the profiler/sampler process,
recognize `/path/ccb ask` as `ask-cli-subprocess`, and report top commands per
bucket.

Verification:

- `PYTHONPATH=lib python -m pytest -q test/test_perf_runtime_lifecycle_profile.py`
  passed with `12 passed`.
- `python -m py_compile dev_tools/perf_runtime_lifecycle_profile.py
  test/test_perf_runtime_lifecycle_profile.py` passed.

## High-Load Ask Storm

Artifact: `/tmp/ccb_runtime_shellsplit_profile_v2.json`

Workload:

- Project: `/home/bfly/yunwei/test_ccb2/ccb_perf_hotload`
- Load: 80 `ccb ask` submissions, concurrency 16, target `agent_codex`
- Samples: 6 at 0.25s before the submission storm completed

Top CPU buckets:

| Bucket | Share | Avg CPU | Max Procs |
| :--- | ---: | ---: | ---: |
| `ask-cli-subprocess` | 62.3% | 34.33% | 16 |
| `ccb/ccbd/main` | 30.6% | 16.88% | 1 |
| `provider/opencode` | 2.4% | 1.30% | 1 |
| `provider/codex` | 1.6% | 0.90% | 3 |
| `other-system` | 1.6% | 0.90% | 13 |
| `tmux-server` | 0.7% | 0.40% | 1 |

Interpretation: high-load submission CPU is dominated by repeated `ccb ask`
Python subprocess creation plus daemon-side job ingestion. Tmux is not the main
CPU owner in this workload.

## Startup

Artifact: `/tmp/ccb_runtime_shellsplit_startup_profile.json`

Workload:

- Project: `/home/bfly/yunwei/test_ccb2/ccb_perf_shellsplit_startup_20260616`
- Config copied from the four-provider `ccb_perf_hotload` project.
- Startup sampled for up to 12s; the new test project was cleaned with
  `/home/bfly/yunwei/ccb_source/ccb_test kill` after profiling.

Top CPU buckets:

| Bucket | Share | Avg CPU | Max Procs |
| :--- | ---: | ---: | ---: |
| `provider/opencode` | 35.4% | 56.22% | 1 |
| `provider/gemini` | 26.2% | 41.54% | 2 |
| `provider/claude` | 10.0% | 15.89% | 1 |
| `ccb/ccbd/main` | 7.2% | 11.41% | 1 |
| `python-misc` | 7.1% | 11.31% | 3 |
| `shell-wrapper` | 5.7% | 9.00% | 8 |
| `provider/codex` | 4.1% | 6.58% | 5 |
| `ccb/keeper` | 2.5% | 3.98% | 1 |
| `tmux-server` | 1.8% | 2.88% | 1 |

Interpretation: startup CPU is mostly provider process launch/mount cost, with
some frontend shell/WezTerm cost and small tmux server cost. The previous
`shell-system` aggregate overstates tmux as an optimization target.

## Optimization Direction

- High-load first target: reduce one-Python-process-per-ask overhead through a
  persistent or batched submission path into `ccbd`.
- Startup first target: lazy or policy-controlled provider mounting, especially
  for expensive non-target providers, plus avoiding repeated provider setup work.
- Tmux optimization remains useful for latency and startup polish, but it is not
  the largest CPU owner in the corrected samples.
