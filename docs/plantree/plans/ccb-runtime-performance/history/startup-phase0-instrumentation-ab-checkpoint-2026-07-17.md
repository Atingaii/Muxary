# Startup Phase 0 Instrumentation A/B Checkpoint

Date: 2026-07-17

Status: working-tree smoke checkpoint; not a release or formal performance
claim

## Scope

This checkpoint validates the warm-only instrumentation-overhead A/B lane on
one owner-marked external fixture with two deterministic Codex stub Agents.
The control and instrumented arms use the same source, fixture, daemon
generation, config signature, native run/report correlation, and complete warm
reuse identity. Only the instrumented arm enables process/resource tracing and
readiness evidence.

Source coordinates:

- commit: `76eef7f49dee519956072ec615d29a58d890c2e9`
- working-tree fingerprint:
  `16a0ee92a6c679a1ddc369e0cdece3b9c4a450b0c7bd67577724d0b4c17a2872`
- source version metadata: `8.2.0`
- platform: Linux `6.8.0-90-generic`, x86_64, ext4
- artifact:
  `/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-20260717-h`

Artifact digests:

- `benchmark-plan.json`:
  `713edb511eb6f424fdd7feee08ddbd6d379f2cc60a799bba8ad967a634ccde8a`
- `summary.json`:
  `198273a87cc2f0dd4adec5ae046f8d88cc85dff53356e91369056fb01defe2a4`
- `cleanup-resource-audit.json`:
  `ff3adcd5661fe7b902920ef255f18bd1969164514a277e0becbab681964346a1`

## Result

The persisted seed `20260717` produced one warmup pair and two measured pairs
with the frozen balanced order:

| Pair | Arm order | Control | Instrumented | Delta |
| :--- | :--- | ---: | ---: | ---: |
| warmup | instrumented, control | not scored | not scored | not scored |
| 0 | control, instrumented | `376.221 ms` | `387.819 ms` | `+11.599 ms` |
| 1 | instrumented, control | `385.535 ms` | `384.706 ms` | `-0.828 ms` |

Both measured pairs were valid. The control p50 was `380.878 ms`, the
instrumented p50 was `386.263 ms`, and the paired-delta p50 was `+5.385 ms`.
The budget computed as `max(10 ms, 2% * control p50)` was `10 ms`. The
deterministic 5,000-resample median bootstrap 95% interval was
`[-0.828, +11.599] ms`.

The control trust gate passed with no process trace, resource profile, or
readiness evidence emitted by either control arm. The instrumented-evidence
gate passed with four of four expected resource/readiness records: cold prime,
one warmup treatment arm, and two measured treatment arms. Treatment-only
external attribution had p50 `94.349%` and minimum `93.792%`; measured resource
profiles were two of two present and formal-eligible. All startup commands used
daemon generation `4` and the same warm reuse identity. There were no failures
or timeouts.

Official `ccb_test kill` reached lifecycle `unmounted` with desired state
`stopped`, and two consecutive full-discovery snapshots found no residue.

## Claim Boundary

The result is `smoke_only` with `formal_claim_allowed=false`. The paired point
estimate is below the budget, but the 95% interval upper bound is above it and
the run has only `1 + 2` pairs instead of the required `3 + 20`. Therefore it
does not qualify instrumentation overhead and must not be reported as a pass,
regression, or stable performance estimate.

The smoke proves that the A/B execution and evidence-separation mechanism works
on this fixture. It did not qualify overhead by itself.

## Formal Follow-Up

After the lifecycle transaction race correction, the frozen `3 + 20` run was
executed on the same owner-marked fixture:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-formal-20260717-j`

All `20/20` measured pairs were valid with zero command failures or timeouts.
The control and instrumented p50 values were `371.935 ms` and `374.550 ms`.
Paired overhead p50 was `+4.098 ms`; the deterministic bootstrap 95% interval
was `[+0.944, +8.676] ms`.  Both the point estimate and interval upper bound
were within the `10 ms` budget, so the dedicated instrumentation-overhead gate
passed.

Formal follow-up digests:

- `benchmark-plan.json`:
  `39a76ae166f20300081d046db844e4c02d2deae205d62fa0399cdd8199d2eb63`
- `summary.json`:
  `4d8714f3016475685db520492bd3769c904facfd702969ef566c38a9796503e8`
- `cleanup-resource-audit.json`:
  `4ea98707916bdd134b7f2aac80a91397a7dfc6c8efb9d60e83a128621e1e897b`

This passes only the instrumentation-overhead gate.  Overall
`formal_claim_allowed` remains false: readiness still has a cold T1 upper
bound, scenario/provider/fault/platform gates remain open, and the treatment
resource gate was degraded because `2/20` measured profiles had honest
`process_io_partial` classification.  All 24 expected treatment readiness and
resource artifacts were present and correlated, and official cleanup still
produced two clean snapshots.

## Generation-Fence And Resource-Quality Recheck

After the complete child-generation fence and transient process-I/O recovery
rules were implemented, the frozen `3 + 20` lane was repeated at:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-fence-io-formal-20260717-l`

All `20/20` measured pairs remained valid with zero failures/timeouts.
Control/instrumented p50 was `368.857/370.469 ms`, paired overhead p50 was
`+1.911 ms`, and the deterministic 95% CI was `[-4.581, +5.397] ms`; the
`10 ms` overhead gate passed.  All `24/24` instrumented resource profiles were
verified, formal-eligible, and process-I/O complete, so the previous resource
degradation is closed on this fixture.  Official cleanup again produced two
clean snapshots.

Recheck digests:

- `benchmark-plan.json`:
  `82c9cd14f5a98ca74f4a2f9174dc57a386413235cb035d43ba397c9bb9e22b6b`
- `summary.json`:
  `cda4064be37c6b3918089970ba659ff2f610e4217541183a023b2c57ca8f6c88`
- `cleanup-resource-audit.json`:
  `2598bda6265b37fc5a148a62cb5fda8dc2fe14c2079998f67a11e36b83d4918b`

Overall qualification remains false because exact T1 and the remaining
scenario/provider/fault/platform gates are still open.

## Exact-T1 And Active-Seed Formal Recheck

The exact keeper T1 and resource active-seed correction were rechecked at:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-instrumentation-ab-exact-t1-active-seed-formal-20260717-p`

All `20/20` measured pairs were valid with zero failures/timeouts.  Control and
instrumented p50 were `384.835` and `383.057 ms`; paired p50 was `-0.283 ms`
and deterministic bootstrap 95% CI was `[-4.316,+7.868] ms`, so the `10 ms`
overhead gate passed.  Readiness was `24/24` complete with one exact cold
keeper checkpoint, 23 warm not-required records, and zero cold upper bounds.
All `24/24` resource profiles were verified, formal-eligible, and process-I/O
complete.  Warm active scans observed only one or two vanished PIDs rather than
growth with round ordinal; official cleanup produced two clean snapshots.

Artifact digests:

- `benchmark-plan.json`:
  `80fc7b2c491c7348eec9616635deb45350c61ddc870673729d00ef4d26976b03`
- `summary.json`:
  `2794468cbcc464ebea235abcfb6b8cac2567e52b3bfdf4c7395dc23e3930a55f`
- `cleanup-resource-audit.json`:
  `0d37490e2cb55c22d7b37da3f028fb40aad841cf2df6cb983bfe73ae295f6196`

The benchmark still reports `formal_claim_allowed=false` only because the
Phase 0 scenario matrix is incomplete; this A/B lane does not claim provider,
fault, interactive-T5, or cross-platform qualification.  Detailed design and
the preserved earlier degraded N evidence are recorded in
[the exact-T1 checkpoint](startup-phase0-exact-t1-checkpoint-2026-07-17.md).
