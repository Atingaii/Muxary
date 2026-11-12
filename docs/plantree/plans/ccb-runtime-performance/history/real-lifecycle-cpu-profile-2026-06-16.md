# Real Lifecycle CPU Profile

Date: 2026-06-16

## Method

Worker `job_21a7c0c0b62a` ran a source-runtime profile in the isolated test
project:

- Working directory: `/home/bfly/yunwei/test_ccb2`
- Runtime command: `/home/bfly/yunwei/ccb_source/ccb_test`
- Isolated state:
  `HOME=/home/bfly/yunwei/test_ccb2/source_home`,
  `CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home`
- Startup sampling: 19 samples at 1 second.
- High-load sampling: 28 samples at 1 second.
- Load model: 80 `ccb ask` tasks, 12 concurrent, target `agent_codex`.
- JSON artifact:
  `/tmp/perf_realtarget/real_provider_cpu_profile_accurate3.json`

## Startup CPU Share

| Category | Share | Avg CPU | Peak RSS | Max Procs |
| :--- | ---: | ---: | ---: | ---: |
| shell-system | 56.0% | 73.23% | 892.3 MB | 20 |
| provider/gemini | 21.9% | 28.63% | 421.6 MB | 2 |
| ccb/ccbd/main | 13.9% | 18.24% | 40.0 MB | 1 |
| python-misc | 3.5% | 4.52% | 31.0 MB | 1 |
| ccb/keeper | 2.5% | 3.29% | 23.9 MB | 1 |
| provider/codex | 2.2% | 2.85% | 68.4 MB | 2 |
| ccbd/sidecar-sidebar | 0.0% | 0.00% | 2.3 MB | 1 |

Aggregate:

- CCB core: 16.5%
- Provider: 24.1%
- Shell/tmux/system: 56.0%

## High-Load CPU Share

| Category | Share | Avg CPU | Peak RSS | Max Procs |
| :--- | ---: | ---: | ---: | ---: |
| shell-system | 72.6% | 69.18% | 1984.8 MB | 25 |
| ccb/ccbd/main | 16.4% | 15.67% | 40.3 MB | 1 |
| provider/gemini | 8.0% | 7.64% | 364.8 MB | 2 |
| provider/codex | 1.3% | 1.21% | 69.0 MB | 2 |
| ccb/keeper | 0.8% | 0.81% | 23.9 MB | 1 |
| python-misc | 0.8% | 0.76% | 31.0 MB | 1 |
| ccbd/sidecar-sidebar | 0.0% | 0.00% | 2.3 MB | 1 |

Aggregate:

- CCB core: 17.3%
- Provider: 9.3%
- Shell/tmux/system: 72.6%

## Rust Helper Attribution

The landed Rust helpers reduce local hot paths, but the lifecycle profile does
not show those paths as the dominant total CPU cost:

- `native.output.observe`: p50 speedup `4.524x`, local work reduction about
  `77.9%`.
- `storage.scan.inventory`: p50 speedup `1.539x`, local work reduction about
  `35.0%`.
- `storage.scan.summary`: p50 speedup `2.079x`, local work reduction about
  `51.9%`; still opt-in.

Because CCB core is about 17% of sampled CPU in the current high-load run,
additional CCB-core-only optimization has a limited total-system ceiling until
shell/tmux/subprocess and provider lifecycle costs are reduced or separated.

## Interpretation

Do not prioritize broad CCB core rewrites from this evidence alone. The next
performance work should first isolate and reduce the `shell-system` bucket,
then decide whether provider lifecycle policy or CCB core paths remain the
largest controlled cost.
