# Phase 0 Baseline Evidence

Date: 2026-06-15

## Artifact

- Result JSON: `dev_tools/perf_results/python_rust_phase0_baseline.json`
- Harness: `dev_tools/perf_phase0_baseline.py`
- Fixture root for this run: temporary directory recorded in the JSON artifact.

## Command

```bash
python dev_tools/perf_phase0_baseline.py --iterations 10 --rows 2000 --agents 6 --processes 80
```

## Measurements

All Phase 0 metrics were measured with generated fixtures; none were skipped.

| Metric | p50 ms | p95 ms | Notes |
| :--- | ---: | ---: | :--- |
| ProjectView build | 1.061101 | 1.208625 | 6 synthetic agents, no live tmux backend |
| JSONL tail/find | 0.446905 | 0.575786 | 2,000-row queue/watch-style JSONL |
| Storage classification scan | 0.993189 | 2.147013 | 27 generated `.ccb` fixture entries |
| Native provider output parse | 14.868364 | 15.988011 | 2,000 assistant JSONL rows plus final event |
| Cleanup process inspection | 0.54272 | 0.559516 | 80 fake `/proc` entries, 20 candidates |
| Helper subprocess startup | 31.532643 | 31.611106 | `python -c ""` harmless subprocess proxy |

## Toolchain Probe

- `cargo`: available, `cargo 1.95.0 (f2d3ce0bd 2026-03-21)`
- `rustup`: available, default host `x86_64-unknown-linux-gnu`

## Notes

- This is a generated-fixture baseline only. It does not read active
  `.ccb/agents` runtime state in the source checkout.
- Helper startup was measured with a harmless Python subprocess as a conservative
  subprocess-overhead proxy, not with a Rust helper binary.
- The first helper target still needs review against larger or real-project
  fixture evidence before Phase 1 changes runtime-adjacent code.
- Main-agent review accepted this evidence for Phase 1 contract-only work,
  because Phase 1 remains disabled by default and does not replace runtime
  behavior. The 31 ms p95 subprocess proxy means future helper calls must be
  batch-aware and should not target sub-ms paths unless amortized or moved to a
  different boundary.
