# Startup Phase 0 Readiness And Attribution Checkpoint

Date: 2026-07-17

Status: working-tree smoke checkpoint; not a release or formal performance
claim

## Scope

This checkpoint validates the source-wrapper/Python bootstrap trace, one-origin
no-attach readiness timeline, strict timeline provenance/order/scope checks,
privacy-safe Linux resource correlation, and official post-run cleanup on one
owner-marked external fixture with two deterministic Codex stub Agents.

Source coordinates:

- commit: `76eef7f49dee519956072ec615d29a58d890c2e9`
- working-tree fingerprint:
  `6267ef7d1060c90d8f5187128a8705668f8884f9c10b15935b8c5ba890e90645`
- source version metadata: `8.2.0`
- platform: Linux `6.8.0-90-generic`, x86_64, ext4
- artifact:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-readiness-attribution-20260717-g`

Artifact digests:

- `summary.json`:
  `bccee3886a7220884ab1048a4b5c7732e19869ba4f2dd6045175230a49aa8efb`
- measured `run.json`:
  `b3009cd7fa3c6aa8f9f57fd5ce8811e590d813411d1eb1fbe3ea387acb1dfa63`
- measured `startup-report.json`:
  `ba47b06b58aaee2978405bd1f048e1357e8d4b8891679048290611665bbc0482`
- measured `resource-profile.json`:
  `4085c60ff2dc3e97a506de2a123da97c003b3d9872ae11ac0811939141c49b29`
- `cleanup-resource-audit.json`:
  `e4ba310ae6b0b3722f3d7da031deddecfc8002c1efb759bd6a79f321e3516d22`

## Result

| Field | Evidence |
| :--- | ---: |
| prime / warmup / measured command wall | `1093.006 / 372.574 / 363.129 ms` |
| measured process bootstrap total | `243.986 ms` |
| measured `ccb.py` entry-to-main eager imports | `211.349 ms` |
| measured CLI total | `99.766 ms` |
| measured supervisor / flow total | `83.098 / 12.599 ms` |
| measured external residual | `19.377 ms` |
| measured external attribution | `94.664%` |
| measured T2 / T3 / T4 / T6 | `217.477 / 288.077 / 298.488 / 298.494 ms` |
| cold-prime T1 observation upper bound | `728.212 ms` |
| sampled process-tree / child-rusage CPU | `0.260 / 0.276 s` |
| measured peak RSS above baseline | `43,778,048 B` |
| measured sampled process-count peak | `6` |
| signed sampler/runner wall outside command | `1.462 ms` |

All three rounds had a native run id, process trace id, startup report, and
resource profile with verified correlation.  All three no-attach readiness
records were structurally complete and generation-matched.  Warmup and measured
T1 were correctly `not_required_already_mounted`; T5 was explicitly
`not_applicable_no_attach`.  The cold prime did not claim an exact keeper
checkpoint: its T1 is an `observed_upper_bound` taken at the same observation as
T2 and tied to the keeper startup id.

The measured profile was complete and formal-eligible.  The cold-prime resource
profile was degraded only for partial process-I/O telemetry, so two of three
profiles were formal-eligible while all three remained run/report correlated.
The measured-resource gate passed.  Official `ccb_test kill` reached
`unmounted`/`stopped`, and two consecutive full-discovery snapshots found no
known or project-attributed process residue.

## Claim Boundary

The result remains `smoke_only` with `formal_claim_allowed=false`.  It has one
warmup and one measured sample rather than `3 + 20`; the exact keeper T1
checkpoint is still unavailable; instrumentation overhead has no paired
uninstrumented control; and the scenario, fault, real-provider,
slow-filesystem, macOS, and WSL matrices remain open.  The readiness gate is
therefore `provisional_upper_bound`, not pass.  T5 is intentionally unavailable
for this no-attach latency lane and must be measured separately in an
interactive attach/first-frame lane.

Focused validation before the external run passed `232` tests across the start
handler/service/socket/flow, supervisor lifecycle, startup identity/counters,
readiness, resource sampler, source guard, and lifecycle-profiler surfaces.
