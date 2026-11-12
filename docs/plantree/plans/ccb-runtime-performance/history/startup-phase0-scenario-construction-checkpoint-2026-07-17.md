# Startup Phase 0 Scenario-Construction Checkpoint

Date: 2026-07-17

Status: S1/S4/S5a construction and artifact-integrity checkpoint; Phase 0 remains open

## Finding

The first scenario-manifest implementation was not yet trustworthy enough for
performance attribution.  A deep audit found several ways that a labelled
scenario could pass without proving its constructor:

- warm priming invoked official `ccb_test kill` before it captured `before`, so
  its supposed before-state was already the constructor result;
- S4 accepted stopped lifecycle/lease even when the namespace remained
  attachable or runtime records remained active;
- S4 calculated daemon/generation relations but did not require a new identity,
  allowing a same-generation daemon to be relabelled cold;
- the summary checked only the shape of an embedded reference and did not read
  the file or verify its SHA256, run binding, phase chain, or privacy contract;
- a start-spawn exception could leave an attempted directory outside the run
  list, while a duplicate native run id could make `run.json` failed after its
  manifest had already been written pass;
- atomic replacement did not directory-sync the artifact parent.

These were measurement-integrity bugs in the Phase 0 harness, not evidence of
a product startup failure.  Retaining them would have made later concurrency or
performance comparisons invalid.

## Fix Boundary

`dev_tools/perf_ccb_startup.py` now treats scenario construction as a
fail-closed, three-phase evidence chain:

- `scenario-construction.before.json` is atomically written and directory-
  synced before any constructor mutation;
- `scenario-construction.ready.json` is immutable and names the before SHA256;
- terminal `scenario-construction.json` names the ready SHA256 and is referenced
  from `run.json` with benchmark, ordinal, scenario, variant, instrumentation
  arm, status, artifact path, and digest bindings.

The summary reopens all three artifacts, validates both predecessor links,
recomputes every digest, checks the reference against its run, rejects
pass-with-reasons, and inventories attempted directories so an orphan ready
record cannot disappear from the gate.  Duplicate native run-id rejection now
happens before terminal manifest publication, keeping run and manifest status
consistent.

Scenario identity is a stable double-read.  Lifecycle, lease, namespace, and
runtime record types, project ids, config signatures, and daemon generations
must be internally consistent.  Runtime liveness is checked without persisting
PIDs.  Equality uses HMAC digests under a fresh non-exported benchmark key;
only sanitized authority state, aggregate counts, and declared privacy flags
are stored.

Implemented constructor gates are now:

- S1 prime and S4: official kill, stopped/unmounted consistent authority,
  non-attachable namespace, zero active/live runtime records, and two clean
  full-discovery process snapshots before measurement;
- ordinary S1: mounted consistent authority and every configured runtime live,
  with daemon, generation, namespace, and runtime identity unchanged through
  the measured start;
- S4: mounted/live authority afterward, with daemon, generation, namespace,
  and runtime identity created or changed;
- S5a: no ccbd or Agent runtime state, empty isolated source home, clean process
  audit, then newly created mounted/live authority.

The phase writes and constructor audits are outside the measured spawn-to-exit
startup wall.  They make benchmark execution slower but add no product startup
path and do not contaminate the measured wall distribution.

## Deterministic Verification

The combined startup-harness and process-resource matrix passes:

```text
114 passed in 18.90s
```

New coverage includes:

- pre-kill before-phase visibility for warm prime;
- S1/S4/S5a success semantics and exact identity relations;
- mismatched lifecycle/lease generations and unstable authority rejection;
- attachable namespace, active runtime, and real project-attributed process
  residue rejection before start;
- kill failure without a start attempt;
- final, before-phase, and predecessor-chain tampering;
- missing artifacts, missing references, orphan attempts, and swapped run
  references;
- spawn exception preservation at non-passing ready state;
- duplicate native run id with aligned failed run/manifest status;
- file and parent-directory `fsync` on atomic artifact publication.

The full pure-source suite completed with:

```text
5338 passed, 2 skipped, 4 failed in 977.92s
```

All four failures are the already-known additive-reload namespace baseline in
`test/test_ccbd_reload_apply.py`; there is no new startup, scenario,
diagnostics, readiness, resource, provider, or cleanup failure.

## Retained External Evidence

All stateful validation used the absolute source `ccb_test` wrapper from
external owner-marked projects, isolated `HOME`/`CCB_SOURCE_HOME`, the Codex
provider stub, no attach, and official lifecycle commands only.

### S4 Full Cold

Fixture:

```text
/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4
```

Final artifact id: `phase0-s4-scenario-final-20260717-al`

- startup, readiness, resource, process-I/O, and scenario gates passed `1/1`;
- ready state had zero active/live runtimes and a clean constructor process
  audit;
- daemon identity, daemon generation, namespace identity, and Agent runtime
  identity all changed;
- measured wall was `1173.125 ms`;
- final official cleanup reached `unmounted/stopped` with two clean snapshots;
- summary/cleanup SHA256:
  `a98014413b2cab775a17503af9cb18837bbe69a0562816ea399c145a2a0161fd`,
  `e4f4a22543bc485dff8bd8b34949e4889c7eff795248feabcd1ae7a66bd59bd4`.

### S1 Prime And Warm Reuse

Same fixture; final artifact id:
`phase0-s1-scenario-final-20260717-am`

- prime and measured scenario manifests passed `2/2`;
- prime used official full-cold reset and changed all four identities;
- measured warm start retained two live configured runtimes and kept daemon,
  generation, namespace, and runtime identities exactly the same;
- measured warm wall was `381.719 ms`;
- final official cleanup reached `unmounted/stopped` with two clean snapshots;
- summary/cleanup SHA256:
  `20bc150782ec0c3a693200f4a6c8b621833ae03a42800eeaee790f53c6094e1d`,
  `3455fa94c557a102ecef53a7620140b6ffdf58237e60dc690f135187c9e77158`.

### S5a Pristine Cold

One-use owner-marked fixture:

```text
/home/bfly/yunwei/test_ccb2/startup-phase0-pristine-final-20260717-76eef7f4
```

Final artifact id: `phase0-s5a-scenario-final-20260717-an`

- before/ready proved no ccbd directory, no Agent directory, zero runtime
  records, an empty source home, and a clean process audit;
- daemon, generation, namespace, and runtime identity were all created;
- startup, readiness, resource, process-I/O, and scenario gates passed `1/1`;
- measured wall was `1172.478 ms`;
- final official cleanup reached `unmounted/stopped` with two clean snapshots;
- summary/cleanup SHA256:
  `9417bde4b016b2f7fd1ac7ca5afd32f09a7b4e9ae6c1c140eabd48dee8ef53a2`,
  `bdf3f2334aebfeeab203196b33be4ba1c54ee2bc91a81331b9a949930914da41`.

All four retained manifests (S4, S1 prime, S1 measured, and S5a) declare and
pass the privacy contract: no Agent names, process ids, provider prompts, or raw
runtime records are persisted.

## Claim Boundary And Next Work

This closes smoke-level scenario construction and artifact integrity for S1,
S4, and one-use S5a.  It does not complete the Phase 0 scenario matrix and is
not a performance improvement claim.  Every summary correctly remains
`formal_claim_allowed=false` and `smoke_only`.

Still open:

- S0 CLI-only report-unchanged semantics;
- S2, which remains unavailable until an official daemon-replacement control
  plane primitive exists;
- deterministic S3 partial-recovery construction and serial failure
  compensation;
- automated fresh-fixture-per-round S5a and cache-warm S5b;
- interactive T5, provider, platform, slow-filesystem, and full fault matrices;
- only after those serial correctness gates, bounded concurrency experiments.

The next concrete task is deterministic S3 serial compensation through
official single-Agent restart/fault injection, without enabling concurrency.
