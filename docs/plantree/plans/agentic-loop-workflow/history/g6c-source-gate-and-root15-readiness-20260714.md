# G6C Source Gate And Root15 Readiness

Date: 2026-07-14
Status: accepted source/fake gate; root15 admitted
Phase: G6C / Decision 029 P5
Accepted source commit: `b14c66ef0d4e03987407cb4985eb1dfc15358f2c`

## Closed Blockers

The root14 follow-up smoke blocker was a real authority defect, not a waived
flake. After an initial Reviewer returned `rework_required`, the original
Worker parent was terminal while the scheduler attempted the next review hop.
CCB correctly rejected that chain. `58d9a9dc` linearizes Worker-owned chain
transitions, and `ed07d619` restores concurrent smoke submission without
manufacturing parent authority.

Subsequent repairs through `ded3ea48` made role-output evidence fail closed,
refreshed stale Detailer import authority, canonicalized V3/fake round results,
and terminated the Detailer manifest contract. P0 RolePack projection repairs
through `632892f8` require canonical Frontdesk request identity and exactly one
assigned-Reviewer chain per bounded Coder review hop. `rework_required` remains
intermediate; final outcomes are `pass`, `blocked`, or `non_converged`.

The first clean functional source run still exposed seven Phase 2 restart tests
that left live recovery runtime trees. `b14c66ef` registers those in-process
runtime owners for fixture cleanup and extends owner discovery to listening
Unix sockets. Direct targeted verification passed the seven recovery nodes and
the cleanup unit set with zero live process/listener residue.

## Final Source Gate

Accepted evidence root:
`/home/bfly/yunwei/test_ccb2/g6c-full-source-final2-b14c-20260714-121525`

The final run used an isolated short `HOME` and XDG directories, the complete
system/provider `PATH`, and no suite-global `CCB_SOURCE_HOME`. The latter is
important for this pytest gate because provider-profile tests intentionally
monkeypatch `HOME`; a global `CCB_SOURCE_HOME` overrides that isolation and
invalidates those rows. Stateful `ccb_test` acceptance continues to follow its
separate source-runtime isolation contract.

Result:

- `4674 passed, 2 skipped in 1064.46s (0:17:44)`;
- pytest exit `0` at exact head `b14c66ef`;
- related live processes after pytest: `0`;
- listening Unix sockets under the disposable root: `0`;
- four non-listening socket files from stale/corrupt-owner fixtures were
  recorded, then removed with the disposable root;
- integration worktree clean after cleanup.

An earlier 46-failure run is rejected as environment evidence: it set a global
`CCB_SOURCE_HOME` and used a truncated `PATH`. Re-running the exact 46 failed
nodes under the corrected environment produced `46 passed in 122.36s`, and the
single final full run above is the acceptance authority.

Rejected-run evidence:
`/home/bfly/yunwei/test_ccb2/g6c-full-source-final-b14c-20260714-115827`

Corrected 46-node recheck:
`/home/bfly/yunwei/test_ccb2/g6c-failed46-recheck-b14c-20260714-121224`

## Root15 Admission Contract

Root15 must be a fresh visible opened project under
`/home/bfly/yunwei/test_ccb2`, launched with
`/home/bfly/yunwei/ccb_source/ccb_test`, inherited real provider configuration
where required, and a lab-local `AGENT_ROLES_STORE`. Root13/root14 evidence and
installed-release runtime state are read-only boundaries.

The run must prove the entire Frontdesk-to-closure workflow again: exact five
route tasks, L1/L2 direct execution, L3 `detail_ready`, both L4 macro/blocked
terminals, task-set closure, Planner backfill, Frontdesk delivery, strict B7,
dynamic release, auto-runner exit, shutdown, and zero live residue. Root14's L1
pass cannot be carried forward.

## Remaining Claim Boundary

This gate admits root15 only. It does not accept remaining G6 three/four-group,
restart, busy-retain/sidebar, provider/model qualification, G7 packaging, or
G8 publication. Weaker models require at least five repeats per exact
provider/model/RolePack digest and cannot be named from aliases or assumptions.
