# Startup Phase 0 Mixed-Recovery Checkpoint

Date: 2026-07-17

Status: S3 serial mixed-recovery smoke closed; Phase 0 remains open

## Finding

The first deterministic S3 run exposed a product correctness regression rather
than merely a slow startup.  The runtime had one exactly owned but dead Agent
pane and one healthy peer pane.  Foreground recovery treated the dead pane as a
structural topology mismatch, recreated the project namespace, and consequently
relaunched the healthy peer.  That violated S3's defining contract: preserve the
daemon, generation, namespace, and healthy peers while recovering only the
failed target.

The retained failure is
`phase0-s3-scenario-final-20260717-ao`.  Its measured round failed closed with
`mixed recovery relaunched a peer runtime`; the namespace identity and peer
identity changed, while official cleanup still reached stopped/unmounted with
two clean process snapshots.  This is evidence about the current dirty working
tree.  It does not establish that the released 8.2.0 tree contained the same
regression.

## Root Cause

Three topology layers had conflated structural ownership with process liveness:

- `ProjectNamespacePaneRecord.matches_authoritative_topology()` rejected an
  otherwise exact record whenever `alive=false`;
- topology completeness therefore classified an exact-owned dead leaf as
  `topology_agent_panes_changed` and selected whole-namespace recreation;
- the recreated namespace made the healthy peer foreign to the new epoch, so
  the ordinary binding path could no longer reuse it.

Pane liveness is required for active-pane selection and runtime binding reuse,
but it is not part of the structural proof that a pane belongs to the current
project/session/window/namespace epoch.  Applying the live requirement at both
layers converted a local recovery event into a project-wide cold rebuild.

## Product Fix Boundary

The working tree now separates exact structural ownership from live usability:

- `lib/ccbd/services/project_namespace_pane.py` gives authoritative topology
  matching an explicit `require_alive` policy;
- `lib/ccbd/services/project_namespace_runtime/materialize_topology.py` includes
  exact-owned dead Agent leaves when proving topology completeness and logical
  window existence, while its active-pane/binding helpers remain live-only;
- `lib/ccbd/services/project_namespace_runtime/ensure.py` retains those exact
  dead leaves in the current topology assignment so the normal Agent runtime
  path can relaunch only the failed slot.

The structural match still rejects a wrong session, project, managed-by owner,
logical window, duplicate record, or namespace epoch.  Active panes, UI focus,
and binding reuse still require a live process.  The correction adds no tmux
scan or new startup subprocess; it removes the erroneous whole-namespace rebuild
from the observed S3 path.

A follow-up independent review also found that the protected active-pane set
was broader than topology completeness: a live same-epoch pane with a plausible
role/window but an unconfigured slot could be preserved from orphan cleanup.
`topology_active_panes()` now protects only one live exact match for every
configured sidebar/cmd/Agent/tool identity.  Unknown or removed slots stay out
of the active set and are removed by ordinary orphan cleanup without forcing a
namespace rebuild.  The normal path still filters the single startup snapshot
in memory.  Its degraded no-snapshot path now performs one bounded candidate
listing and one description per candidate, rather than one tmux listing per
expected slot.

The corresponding structural/live distinction is now explicit in
`docs/ccbd-startup-supervision-contract.md` and
`docs/ccbd-pane-recovery-continuous-attach-plan.md`.

## Deterministic S3 Constructor

`dev_tools/perf_ccb_startup.py` now implements `mixed-recovery` as a serial,
source-test-only scenario:

- preflight requires an owner-marked external fixture, deterministic Provider
  stubs, at least two configured Agents, and launch cap 1;
- the prime round uses the existing official full-cold constructor;
- the measured constructor invokes official single-Agent `ccb_test restart`,
  selects one launch match for failure, and holds that process on a release
  latch until the restart RPC returns;
- after the selected failure is released, the ready phase requires the same
  daemon/generation/namespace, exactly one pseudonymous target slot dead, and
  all peer slots live and unchanged;
- the measured foreground start must relaunch exactly the target with
  `binding_reject_reason=pane_dead` and one Provider preparation, attach every
  peer with zero preparation, preserve peer and namespace identity, and show no
  intervening supervision recovery event;
- the launch probe must show target matches prime, selected failure, and
  recovery in exact order, one injected failure, no active process at terminal,
  and maximum observed launch concurrency 1.

The failure controls are passed through the fixture's already validated
Provider start command rather than widening product control-plane environment
allowlisting.  Scenario manifests persist only HMAC slot/identity values and
aggregate counts.  The raw stub event log, which may contain names or PIDs,
stays in the external `0700` benchmark directory as a `0600` file and is bound
by SHA256 from the final manifest.

Mixed-recovery preflight also rejects any nonempty caller-supplied global or
known-Provider `STUB_LAUNCH_*` control.  This prevents caller Agent selectors,
delay/barrier settings, cancellation, or alternate probe state from changing a
run that would otherwise retain the same S3 label.  All such controls are
harness-owned for this scenario.

## Deterministic Verification

The focused pure-source matrix passes:

```text
219 passed in 25.46s
```

It covers the startup harness, launch probe, pane snapshot/topology planning,
additive namespace patching, Agent start runtime, foreground start flow, and
official single-Agent restart.  New cases distinguish exact-owned dead panes
from active panes, reject dead-only panes for live reuse, exercise indexed
failure/latch sequencing and caller-actor selection, reject caller-owned launch
controls, exclude unexpected current-epoch slots from the protected active set,
bound the degraded candidate listing, and validate the complete privacy-safe S3
report contract.

The companion project-namespace state/backend and tmux orphan-cleanup matrix
also passes:

```text
58 passed in 3.54s
```

The earlier full-suite result predates this final S3 patch and is not used as
acceptance evidence for it.  S3 remains bounded by the focused matrix plus the
external source-runtime run below.

## Retained External Evidence

All stateful runs used the absolute source wrapper from the owner-marked
external fixture below, isolated `HOME`/`CCB_SOURCE_HOME`, deterministic Codex
stubs, no attach, launch cap 1, and official lifecycle commands only:

```text
/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4
```

### AO: retained product failure

`phase0-s3-scenario-final-20260717-ao` correctly failed after a dead target
caused namespace recreation and peer relaunch.  The measured command wall was
`4113.680 ms`.  Its failed manifest and clean official teardown are retained
rather than overwritten.

### AP: retained validator false negative

After the product correction, `phase0-s3-scenario-final-20260717-ap` preserved
the namespace and peer, relaunched only the target in `667.483 ms`, and cleaned
up.  The harness nevertheless rejected the required targeted topology
assignment as if it were a project-wide cold reset.  The validator was corrected
to require that exact target assignment while continuing to reject bootstrap,
namespace recreation, cold reconstruction, or peer topology assignment.

### AQ: passing serial S3 smoke

`phase0-s3-scenario-final-20260717-aq` passed both prime and measured scenario
manifests, readiness, resource, process-I/O, supervision, privacy, and cleanup
gates:

- measured foreground wall: `665.070 ms`;
- daemon identity, daemon generation, and namespace identity: `same`;
- target slot: dead at ready, then `relaunched`, `pane_dead`, prepare count 1,
  and changed identity after recovery;
- peer slot: live and unchanged at ready, then `attached`, prepare count 0, and
  unchanged identity after recovery;
- launch probe: exact target matches 1/2/3, only match 2 selected and failed,
  one released failure, maximum observed concurrency 1, terminal active 0;
- supervision cursor: zero recovery events;
- final official cleanup: stopped/unmounted and two consecutive clean process
  snapshots.

Evidence digests:

```text
summary.json                              ece693aefe4ed7db86246bafafaa023bc3880fbdddb5d2daa6ae1901eb669646
cleanup-resource-audit.json               63d4511e80083a64d420e014c8d61a6081e79e623d79f98eefd7169e484b288a
run-0001/scenario-construction.json        3d497aaf0af84606f7ac1da7a0eb25848b10a47930379eb686c58e9b4867c653
run-0001/launch-probe.json                 416eb9b50b489a9853258f8f73e0806d8cda38889d1144c06471e1334c76ac37
```

The artifact identifies source commit `76eef7f49dee519956072ec615d29a58d890c2e9`
and working-tree fingerprint
`746e5c10059a903d39cc36ae6a5c4490e18339b128fdf578a0434201525dd61a`.
It remains `formal_claim_allowed=false` and `smoke_only`.

## Claim Boundary And Next Work

This closes the deterministic serial S3 construction and compensation smoke on
one Linux two-Agent stub fixture.  It proves that the corrected path recovers
only the failed target without broad rebuild or peer churn.  It is not a launch
concurrency result, a real Provider qualification, a p50/p95 performance claim,
or overall Phase 0 acceptance.

Still open:

- S0 report-unchanged semantics;
- S2, unavailable until an official daemon-replacement primitive exists;
- automated fresh-fixture-per-round S5a and cache-warm S5b;
- broader fault injection, interactive T5, real Codex/Claude, macOS, WSL, and
  slow-filesystem qualification;
- only after those serial gates, measured bounded launch-concurrency candidates.
