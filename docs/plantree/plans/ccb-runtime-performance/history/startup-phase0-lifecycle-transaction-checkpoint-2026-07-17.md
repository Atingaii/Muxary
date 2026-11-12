# Startup Phase 0 Lifecycle Transaction Checkpoint

Date: 2026-07-17

Status: working-tree correctness and external-smoke checkpoint; not a release

## Root Cause

`lifecycle.json` was written with durable atomic replacement, but several
cross-process `load -> modify -> save` sequences were not transactional.  A
foreground CLI could load an old `unmounted` record, keeper could then publish
`starting` with a new `startup_id` and generation, and the CLI could finally
replace it with the complete stale record.  Keeper lifecycle initialization
had the same create race, and keeper success/failure finalization rebuilt state
from the pre-spawn `starting` snapshot.

That ordering could lose startup intent, regress phase/generation, erase the
keeper startup identity or child-published fields, and make startup timing
appear nondeterministic.  Atomic JSON replacement prevented a torn file but did
not prevent a valid stale file from winning.

## Working-Tree Correction

- CLI running intent now acquires the project `startup.lock`, reloads lifecycle
  after lock acquisition, and writes only a real `stopped -> running`
  transition or missing-record materialization.  An already-running lifecycle
  is a no-op, so warm start no longer performs this durable rewrite or projects
  disk config into an accepted generation.
- keeper lifecycle materialization uses an unlocked read-only fast path, then
  acquires the same lock and reloads before any create or keeper-pid update.
- keeper loads config outside the lock, then reloads lifecycle and lease
  inspection inside the short transaction before assigning generation and
  `startup_id` and publishing `starting`.
- keeper releases the lock before spawning or waiting for `ccbd`; the child
  needs the same lock to claim ownership, so holding it across spawn would
  deadlock.
- keeper success/failure finalization reacquires the short lock and fences on
  both `startup_id` and generation.  It cannot overwrite a newer startup or
  concurrent stop, and an already child-published matching `mounted` record is
  a no-op rather than a rebuild from stale `starting` state.

Contracts were updated in `docs/ccbd-startup-supervision-contract.md` and
`docs/ccbd-lifecycle-stability-plan.md`.

## Deterministic Regression Evidence

The focused race matrix includes:

- a real POSIX child process blocked behind the keeper-held startup lock;
- zero rewrite for active `starting` and warm `mounted` lifecycle records;
- fresh lifecycle reload after lock acquisition when another writer creates
  the record first;
- proof that the startup lock is released before the spawn callback;
- preservation of child-mounted namespace/owner fields;
- preservation of a superseding startup transaction;
- preservation of a concurrent stop when the older spawn later fails.

Focused lock/keeper/startup tests passed `39`; the expanded
startup/readiness/resource matrix passed `278`; daemon config-drift, kill,
service-graph, keeper, and CLI lifecycle tests passed `75`.  Python compilation
and changed-path `git diff --check` passed.

## External Source Runtime Smoke

Artifact:

`/home/bfly/yunwei/test_ccb2/startup-phase0-resource-20260717-76eef7f4/artifacts/startup/phase0-warm-lifecycle-lock-race-20260717-i`

Source coordinates:

- commit: `76eef7f49dee519956072ec615d29a58d890c2e9`
- working-tree fingerprint:
  `fc75884a4727dab2a8de6dd94c05705a14b5e9dde37ab041830be4ff41836713`
- source version metadata: `8.2.0`

Cold prime, one warmup, and one measured start completed against generation
`5` with zero failures or timeouts.  The measured wall was `376.255 ms`, CLI
daemon ensure was `0.921 ms`, external attribution was `94.410%`, all three
readiness records were structurally complete, all three resource profiles were
formal-eligible, and official cleanup produced two clean snapshots.

Artifact digests:

- `summary.json`:
  `807a7a5b17b6d52e1211a0dd4cb0e518a8b8b17d1cb5b39340e847400128db51`
- `cleanup-resource-audit.json`:
  `9e981ea315af7ea3f2406eb9670073561d4ffa6dfb282455836df6b1edfc6322`

This single measured sample proves functional source-runtime compatibility and
clean teardown, not a before/after startup-speed improvement.

## Remaining Boundaries

- Exact keeper T1 correlation is still absent; the cold readiness point remains
  an `observed_upper_bound`.
- The child-generation fence, broader lifecycle/lease writer audit, strict
  readiness identity, timeout child reaping, and stale latest-report fence were
  completed in the follow-up
  [generation-fence checkpoint](startup-phase0-generation-fence-checkpoint-2026-07-17.md).
- The strict mounted-after-self-ping publication boundary and the remaining
  Phase 0 scenario/fault/provider/platform matrix are still open.
- `storage.locks.file_lock` currently relies on POSIX `fcntl`; native Windows
  must not be claimed protected by this regression.  Linux, macOS, and WSL use
  the intended lock semantics, with WSL mounted-drive runtime state relocated
  to the Linux state root.
