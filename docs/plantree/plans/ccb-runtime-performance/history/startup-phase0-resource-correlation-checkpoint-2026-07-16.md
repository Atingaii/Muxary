# Startup Phase 0 Resource-Correlation Checkpoint

Date: 2026-07-16

Status: working-tree smoke checkpoint; not a release or formal performance
claim

Follow-up bootstrap/readiness evidence is recorded in
[startup-phase0-readiness-attribution-checkpoint-2026-07-17.md](startup-phase0-readiness-attribution-checkpoint-2026-07-17.md).

## Scope

This checkpoint validates the fail-closed startup harness, steady warm-reuse
identity gate, native startup-run correlation, privacy-safe Linux resource
sampling, and post-cleanup process-residue audit on one owner-marked external
fixture with two deterministic Codex stub Agents.

Source coordinates:

- commit: `7f08a9db32cdc23d8b3374c4fa92076236228a9f`
- working-tree fingerprint:
  `ed3af7d72ecf53f99d0e0cae298ec3f616f390e509607fcd441e30d5a559d0b7`
- source version metadata: `8.2.0`
- platform: Linux `6.8.0-90-generic`, x86_64, ext4
- artifact:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260716-7f08a9db/artifacts/startup/phase0-warm-resource-correlation-20260716-b`

Artifact digests:

- `summary.json`:
  `3662986319b10cbe77f5276e9001f6f98c1488bdf730750b43e491d0da5df517`
- `cleanup-resource-audit.json`:
  `56ba1b0baf1645001940b0ef686fdd9781c99e525630086685db41867e5611a1`
- measured `resource-profile.json`:
  `c402598168d765603ba3adb71a059fe69377385c98903a09dcaf5e97986e832d`

## Result

| Field | Evidence |
| :--- | ---: |
| prime command wall | `1266.136 ms` |
| warmup command wall | `438.609 ms` |
| measured warm command wall | `400.884 ms` |
| measured CLI total | `125.867 ms` |
| measured supervisor total | `107.791 ms` |
| measured external unattributed | `275.017 ms` |
| measured external attribution | `31.397%` |
| sampled process-tree CPU | `0.270 s` |
| command child rusage CPU | `0.288 s` |
| sampled peak RSS | `160,440,320 B` |
| peak RSS above baseline | `41,664,512 B` |
| sampled process-count peak | `5` |
| physical read / write | `0 B / 20,480 B` |
| sampler/runner wall outside command | `1.375 ms` |

All three startup rounds have distinct native run IDs and complete resource
profiles whose stdout ID, startup-report ID, report digest, and benchmark
coordinates validate.  Process I/O capability was available in every round.
The final official `ccb_test kill` reached `unmounted`/`stopped`; two
consecutive full-discovery `/proc` snapshots found zero project or known
process residue.

The warmup and measured reports both preserved the same runtime/session/pane/
PID/namespace reuse identity, reported both Agents as `attached/restored`,
performed zero Provider preparation and zero launch-only Agent stages, and
showed no durable content write.  Each steady run still executed `71` tmux
backend commands/subprocesses and three identical-write skips.

## Claim Boundary

The summary remains `smoke_only` with `formal_claim_allowed=false`.  This run
has one warmup and one measured sample rather than the required `3 + 20`;
external attribution is `31.397%`, below the `90%` exit gate; T1 and T5 are
missing; instrumentation overhead has no uninstrumented A/B control; and the
scenario, real-provider, fault, slow-filesystem, macOS, and WSL matrices remain
open.  The `1.375 ms` sampler/runner difference is useful local evidence but
is not the required instrumentation-overhead qualification.
