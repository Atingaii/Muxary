# G6C Root13 Planner Terminal Constraint Diagnostic

Date: 2026-07-13
Status: rejected real-provider acceptance; bounded source repair verified; root14 pending
Phase: G6C / Decision 029 P5
Read when: implementing the post-detail terminal constraint or preparing root14

## Accepted Preconditions

- Source head `3a5e1810` included the Frontdesk/Planner Git-capability RolePack
  repair at `c4dbeed1` and the harness request injection at `3a5e1810`.
- The focused harness and RolePack gates passed with `79` and `24` tests.
- Before provider start, the generated request contained
  `git_repository=not_guaranteed`, repo-independent verification rules, and
  all five expected route/terminal pairs.
- The opened project used a fresh root-local Role store and five ready resident
  panes. The direct handoff preserved the capability and recorded
  `controller_rewrote_body=false`.

## Preserved Root13 Evidence

Root:
`/home/bfly/yunwei/test_ccb2/deploy-g6c-real-talk2-20260713-13`

Frontdesk job `job_6c76260c7668` activated Planner job
`job_32603cf62469`. Planner returned exactly the five bounded task ids and
routes. L1 and L2 used repo-independent file/content or unittest verification;
no imported task packet or execution contract used a Git-only scope check.

Observed terminal results before the failure:

- L1 document direct execution: `done/pass`.
- L2 code/test direct execution: `done/pass`.
- L3 needs-detail: reached `detail_ready` with all three Detailer artifacts.
- L4 macro adjustment: `replan_required`.
- L4 blocked prerequisite: `blocked`.

## Rejection Reason

The post-detail Planner activation `act-aee989c0566b` started from
`task_status=detail_ready` with reason `detail_ready_task`. Planner job
`job_564275f23588` returned `readiness=ready`, `route=needs_detail`, empty
`allowed_paths`, and `status_recommendation=detail_ready`. Its task packet also
explicitly required the bounded task to remain at `detail_ready`.

The single-task Planner importer did not parse `status_recommendation`; it
unconditionally mapped the reply to `ready_for_orchestration` with activation
reason `planner_reply_imported`. L3 advanced to revision 3, the required child
was no longer terminal, and task-set closure could not begin. This is an
activation-contract plus importer gap, not a provider compliance failure.

Root13 was safely unmounted without generating a false B7 pass. Auto-runner
pid `4118860` was terminated and all project evidence was preserved.

## Repair Boundary

The repair must be generic and activation-scoped:

1. Carry a verified, digest-backed terminal constraint into the post-detail
   Planner activation only when current artifact provenance and revision prove
   the bounded stop contract.
2. Parse and validate `status_recommendation` in the Planner reply.
3. Preserve `detail_ready` only when activation constraint, reply route,
   recommendation, empty allowed paths, provenance, and CAS revision all
   match. Conflicts fail closed.
4. Keep legacy activations and ordinary `detail_ready -> ready_for_orchestration`
   behavior unchanged.
5. Settled bounded tasks must not be selected again by auto-runner, and task-
   set closure must consume their terminal evidence.

Do not hard-code Phase 6B task ids, force status from the harness, globally
reinterpret `readiness=ready`, weaken path/provenance checks, or let provider
text write authority directly.

## Repair Landing And Source Gate

- `c6bd0235` adds the activation-scoped, revision/state/digest-backed terminal
  constraint, fail-closed matching settlement, legacy compatibility, and
  verified terminal closure semantics.
- `6dbbfef8` aligns the Planner RolePack reply contract; `5485f722` separates
  initial task-set binding revision from the terminal task revision in B7.
- `b4a1f200`, `c3b653ee`, and `77c54a98` prove real authority, bounded replay
  across restart, no reactivation, and mixed-terminal task-set closure through
  Planner backfill, Frontdesk delivery, and parent settlement.
- `82a3a622` repairs the unrelated Gemini ccbd-restart observation failures
  discovered by the first full-suite attempt without relaxing other provider
  restore behavior.
- Direct current-HEAD verification passed the four prior Gemini failures, the
  complete Phase 2 entrypoint (`77 passed`), and the full source suite
  (`4792 passed, 2 skipped in 732.93s`). Root14 is therefore no longer blocked
  by a source-test failure, but none of this substitutes for visible real-
  project acceptance.

## Root14 Gates

- Exact root13-shaped importer regression fails before the repair and passes
  after it.
- Constraint conflict, missing recommendation, non-empty allowed paths, stale
  revision, and tampered digest fail closed without status mutation.
- Legacy activation and ordinary post-detail execution retain their current
  behavior.
- Repeated import and repeated auto-run are idempotent and produce no new L3
  Planner or Orchestrator activation after bounded settlement.
- Planner RolePack documents the optional constraint and matching reply shape.
- A fresh root14 proves the five expected terminals, task-set closure, Planner
  backfill, Frontdesk reporting, B7, dynamic release, auto-runner exit,
  shutdown, and zero residue.

## Ownership

Workers may implement the bounded source repair. `mother` owns the RolePack
contract update after the controller capability exists. `talk2` owns source
review and direct opened-project root14 execution and acceptance.
