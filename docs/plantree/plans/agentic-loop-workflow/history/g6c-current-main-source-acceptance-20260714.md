# G6C Current-Main Source Acceptance

Date: 2026-07-14
Status: accepted source/fake gate
Accepted code commit: `2c936a4826501b5fe9a52df56e7a4c003c3a053f`
Merge base: current main `ccac20349a2cb038acb637a158bc15ceca5ce2b6`

## Accepted Scope

The current-main candidate integrates the accepted single-lane workflow with
provider restart/default repairs, strict Detailer-to-Planner replan authority,
durable transaction recovery, retry and replay fencing, RolePack projection
contracts, and G7 release/update rollback safeguards.

Key terminal commits are:

- `6746d749` and `e08409ce`: provider registry/default and Codex/Claude restart
  recovery;
- `87ef660b` through `55eb738e`: Detailer replan authority, projection,
  transaction interruption recovery, retry fencing, and Planner backfill;
- `de84865d` and `2c936a48`: release identity collision rejection and external
  rollback-backup retention.

Mother's authority review accepted the Detailer transaction/retry/recovery
boundary at `55eb738e`. The G7 commits were accepted after a first review
rejected unsafe in-prefix rollback storage and unconditional tag rejection;
the follow-up makes rollback storage external and permits an exact tag/build
commit match.

## Focused And Historical Gates

Evidence root:
`/home/bfly/yunwei/test_ccb2/gate-l1-source-2c936a48-20260714TyZKFBB`

- Detailer authority/recovery, RolePack projection/backfill, and G7 management,
  build, install, update, and version tests: `222 passed in 6.37s`.
- The exact 26 failed nodes from the rejected `72b8e568` full run were parsed
  from its original log and rerun as literal node ids: `26 passed in 290.10s`.
- Three restart-test runtime projects were force-unmounted after the run;
  direct post-cleanup audit found no related process, listener, or socket.

## Rejected Harness Run

Rejected evidence root:
`/home/bfly/yunwei/test_ccb2/gate-full-source-2c936a48-20260714T101801Z-3366141`

The suite reported `4987 passed, 5 failed, 2 skipped`. Its basetemp contained a
literal unexpanded `{RANDOM}` token. That token caused `shlex.quote` to add
quotes to otherwise ordinary generated command paths, changing five
string-format assertions without changing runtime behavior. The exact five
nodes passed under the safe alphanumeric basetemp at:

`/home/bfly/yunwei/test_ccb2/g6c-5node-2c936a48-1784025373645524323`

Result: `5 passed in 6.32s`. The rejected run is environment-diagnostic only.
Its fourteen test-owned runtime projects were force-unmounted and audited to
zero live residue.

## Final Full Source Gate

Accepted evidence root:
`/home/bfly/yunwei/test_ccb2/gate-full-source-2c936a48-20260714T183827Z-3882094`

The accepted run used:

- candidate repo as pytest cwd;
- `/home/bfly/anaconda3/bin/python`;
- a pre-expanded safe basetemp,
  `/tmp/g6cfinal-1784025507-3882094`;
- isolated HOME and XDG config/cache/state roots;
- complete inherited PATH;
- no suite-global `CCB_SOURCE_HOME` or `CCB_SOURCE_RUNTIME_OK`;
- one serial, unfiltered pytest invocation with no xdist.

Result: `4992 passed, 2 skipped in 785.04s (0:13:05)`, exit `0`.

After pytest, fourteen basetemp-owned restart/Phase 2 projects were identified
from live process command lines and force-unmounted with the candidate
`ccb_test`. Direct post-cleanup checks found zero related processes, pytest
instances, Unix listeners, and socket files. Git remained clean at the exact
accepted code commit.

## Control-Plane Evidence Note

Several delegated jobs returned zero-byte `failed` completion artifacts while
their provider sessions and pytest processes continued normally. Those
callbacks were rejected as evidence; `talk2` recovered the actual provider
sessions, logs, process state, and cleanup directly. This installed-release
result-collection behavior remains an active diagnostic item before visible
provider acceptance relies on delegated completion callbacks.

## Claim Boundary

This checkpoint accepts the current-main source/fake candidate only. It does
not accept current-candidate visible Codex/Claude workflows, exact weaker-model
repeatability, package installation/update/rollback, production/default
enablement, npm publication, or Git tagging.
