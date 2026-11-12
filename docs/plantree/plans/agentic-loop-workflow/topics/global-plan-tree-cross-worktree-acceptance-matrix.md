# Global Plan Tree Cross-Worktree Acceptance Matrix

Date: 2026-07-15
Status: Required gate design; implementation not started
Authority: [Decision 031](../decisions/031-global-plan-tree-authority-across-worktrees.md)
Protocol: [global-plan-tree-authority-and-cross-worktree-control.md](global-plan-tree-authority-and-cross-worktree-control.md)
Read when: implementing or accepting control election, task-store migration,
cross-worktree proposals, lane scheduling, integration recovery, or global views

## Purpose

Make global Plan Tree consistency falsifiable. A generic two-lane pass is not
acceptance. Each row fixes the initial authority identity, injected race or
crash, allowed terminal state, forbidden observation, recovery action, and
residue evidence.

## Evidence Envelope

Every run records:

```text
case_id, run_id, source_commit, platform, filesystem
portfolio_id, local_repository_id
locator_revision, authority_generation, fencing_token, holder_id
target_ref, initial_authority_commit, final_authority_commit
lane_ids, task_ids, snapshot revisions, authority digests
integration_id, hidden_candidate, promoted_commit
fault_injection_point, recovery_command, final_state
process/lock/ref/worktree/runtime residue audit
```

The harness must preserve raw state before recovery. Automatic retries cannot
hide the first failure. Every recovery command is idempotently repeated once.
The second call must report the same accepted state without another commit,
integration, event, or revision increment.

Commands below are target interfaces, not claims that current source already
implements them.

## Universal Forbidden States

All cases forbid:

- two active holders for one local control domain;
- target-ref write from an expired generation or fencing token;
- duplicate authority commits, integration promotions, or completion events;
- global `done` before exact integration id reaches `published`;
- dependent-lane admission from `prepared` through `promoted`;
- stale or mixed query data labelled current;
- index projection overriding canonical task records;
- lane A state, agents, refs, locks, or cleanup mutating lane B ownership;
- silent fallback to unlocked operation, another control root, stronger model,
  or last-writer-wins merge;
- provider substitution different from the provider/model/RolePack accepted in
  the lane snapshot. Merely having another inactive provider installed is not
  fallback and is not a failure.

## A. Control Identity And Election

| Case | Initial state and fault | Required result | Recovery command | Required residue evidence |
| :--- | :--- | :--- | :--- | :--- |
| C01 concurrent init | No locator; two linked worktrees invoke init together | Exactly one atomic create wins; loser reports existing domain with same ids | `ccb plan control doctor --all-worktrees` | One locator, one local id, one control root, no temp locator |
| C02 missing locator | Committed portfolio exists; locator removed before ordinary plan command | Command returns `control_unavailable`; no new domain or id | `ccb plan control recover-locator --expected-portfolio <id>` | Restored locator matches existing runtime/authority or recovery refuses |
| C03 duplicate locator/root | Locator copy points to a second control root | All writes stop with `split_brain_suspected` | `ccb plan control doctor --all-worktrees --repair-plan` | No ref movement; both roots preserved as evidence until explicit owner choice |
| C04 planned handoff | Active holder G7/F20, no prepared transaction; move control workspace | Old holder drains; one CAS installs G8/new fence/workspace | `ccb plan control handoff --to <path> --expected-generation 7` | Old lease revoked; old workspace cannot publish; target unchanged |
| C05 holder crash/takeover | Holder dies after lease renewal; lease expires | State becomes `recovery_required`, not automatically active elsewhere | `ccb plan control takeover --expected-generation <g> --doctor <report>` | New generation/fence only once; old resumed process receives fenced rejection |
| C06 old holder resumes | Takeover completed; old process resumes with valid OS lock handle | Every old proposal/ref/event write is rejected by generation/fence | `ccb plan control doctor --holder-history` | No commit/event from old holder; rejection identifies old token |
| C07 missing/moved workspace | Locator workspace path disappears or points at wrong target ref | Startup fails closed and preserves locator/generation | `ccb plan control handoff --recover-to <path> --expected-generation <g>` | No auto-created worktree, no target movement, explicit new generation |
| C08 unsupported filesystem | Control root on NFS/SMB/drvfs/no-lock platform | Capability probe rejects control startup | `ccb plan control doctor --capabilities` | No lease, lock, journal, or proposal write after failed probe |
| C09 independent backends | Two worktrees have separate `.ccb` backends but one locator | Both read same authority; only fenced control holder writes | `ccb plan control status --all-worktrees` | Backend generations remain independent; Plan Tree ids/fence agree |
| C10 separate clone | Same committed portfolio id in another clone/local repository id | Clone is a separate local domain and cannot use first clone's local lease | `ccb plan control init --clone` | Distinct local id/root; no false same-host strong-consistency claim |

## B. Task Store, Revisions, And Proposals

| Case | Initial state and fault | Required result | Recovery command | Required residue evidence |
| :--- | :--- | :--- | :--- | :--- |
| T01 distinct-task race | Processes A/B update different tasks in one plan under different task locks | Both canonical records survive; plan revision and rebuilt index include both | `ccb plan task-index rebuild --plan <id>` | Record count/digests/index source-set digest match; no lost update |
| T02 same-task race | A/B submit from same task revision | One CAS wins; loser gets `task_revision_conflict` | `ccb plan context --task <id> --diff-from <rev>` | One task revision increment and one semantic commit |
| T03 closure-identical drift | Another task advances plan revision; target closure and applicable fence set are unchanged | Controller records deterministic rebase and accepts once | `ccb plan transaction recover --id <proposal>` | `rebased_from` present; closure and `fence_set_digest` identical; no Agent rerun |
| T03b global fence with identical closure | Task-local closure is byte-identical but an applicable `global_fence` changes | Rebase/import is rejected with `global_fence_changed` | `ccb plan transaction explain --id <proposal>` | Old/new fence-set entries and digests preserved; no semantic commit |
| T04 referenced decision changes | Lane pins decision digest; decision changes before result import | Lane enters `stale_plan_snapshot`; completion rejected | `ccb plan lane replan --lane <id>` | Old snapshot retained; new snapshot has new digest/revision |
| T05 external contract changes | Pinned `docs/` API/schema/release contract changes | Same stale behavior as T04 despite Plan Tree not owning contract | `ccb plan lane replan --lane <id>` | Authority ref shows old/new immutable commit/path/digest |
| T06 unrelated portfolio change | Another plan changes without touching closure/global fence | Lane continues and records newer observed portfolio revision | `ccb plan context --lane <id>` | Original authority digest unchanged; no false restart |
| T07 global fence changes | Portfolio schema/integration policy changes | Every affected lane pauses before next authority boundary | `ccb plan lanes --stale` | No dispatch/review/integration publication under old global fence |
| T08 migration crash | Kill after each task-store migration step, including temp index flush | Recovery resumes/rolls back exactly one step; authority mode flips once | `ccb plan task-store recover --plan <id>` | Canonical/index counts agree; temp files classified; rollback remains possible |
| T09 stale generated index | Index header authority commit/generation differs from records | Reader rebuilds boundedly or fails closed; never returns stale task | `ccb plan task-index rebuild --plan <id>` | New projection header/source digest match current records |
| T09b rebuild source corrupt | Index header mismatches and one canonical task record is corrupt, so bounded rebuild fails | Reader fails closed with canonical-record diagnostics; old index is not returned | `ccb plan doctor --plan <id> --task-store` | Corrupt record preserved/quarantined by explicit repair only; no fabricated task |
| T10 legacy closure drift | Legacy projection digest matches but full authority closure changed | Import rejects legacy-only authority with closure conflict | `ccb plan transaction explain --id <proposal>` | No ambiguous single `PlanTree revision` accepted as full fence |
| T10a legacy in multi-lane mode | Legacy digest and closure match, but proposal is lane-scoped/multi-lane and lacks Decision 031 basis | Import rejects with `legacy_authority_insufficient` | `ccb plan transaction explain --id <proposal>` | No typed revision, snapshot, or target-ref write is inferred from legacy state |
| T10b legacy with external contract | Legacy digest matches, but operation depends on an external contract ref absent from the legacy envelope | Import rejects with `external_authority_missing` | `ccb plan transaction explain --id <proposal>` | Required contract commit/path/digest identified; no projection write |
| T11 non-legacy Planner surface | Decision/open-question/status/external contract changes while legacy three-file digest matches | Typed proposal or stale conflict is required; legacy lock/digest cannot publish | `ccb plan transaction explain --id <proposal>` | Exact surface selector/preimage/target digest appears in authority closure |
| T12 proposal lifecycle crash | Kill before/after pending-to-accepted or pending-to-rejected rename | Recovery derives one terminal directory from target ref and journal | `ccb plan transaction recover --id <proposal>` | Exactly one envelope location; no orphan pending file or duplicate event |

## C. Lane Admission And Isolation

| Case | Initial state and fault | Required result | Recovery command | Required residue evidence |
| :--- | :--- | :--- | :--- | :--- |
| L01 disjoint lanes | Two ready nodes, disjoint write claims, sufficient capacity | Both admit with distinct lane/snapshot/worktree ids and overlap in execution | `ccb plan lanes --read-fence` | No identity/ref/agent/runtime crossover; both snapshots trace same authority domain |
| L02 write/write conflict | Two nodes claim same file/interface/schema | At most one admits; other waits with explicit conflict owner | `ccb plan lane resolve-conflict --lane <id>` | No second worktree mutation or worker dispatch before resolution |
| L03 dependency wait | Lane B depends on A; A not `published` | B waits through every A saga stage; after publication one `dependency_refresh` creates a higher immutable snapshot before admission | `ccb plan frontier refresh --node <node-b>` | B dispatch count zero before refresh; old/new snapshots and predecessor commit remain traceable |
| L04 worktree deletion | Delete lane worktree while provider/runtime job exists | Lane becomes `workspace_lost`; id is not reused; unrelated lane continues | `ccb plan lane recover --lane <id>` | Missing worktree classified; branch/ref/artifacts retained or explicitly cancelled |
| L05 stale callback | Old attempt replies after task/lane fence advances | Callback persists as stale evidence and cannot mutate current lane | `ccb plan lane explain-callback <message-id>` | No task revision, integration, or agent ownership change |
| L06 lane controller crash | Kill lane A controller while lane B runs | A recovers/blocks independently; B remains live | `ccb plan lane recover --lane <a>` | No project-wide runner lock blocks B; A intent remains exact-once |
| L07 capacity pressure | Two safe lanes ready but capacity admits one | Waiting reason is capacity, not false dependency/conflict | `ccb plan frontier --explain-all` | Priority/fairness evidence; no silent roadmap serialization |
| L08 lane cancellation | Cancel one active lane during provider/review activity | Matching intents fence; owned resources release only after busy-safe gate | `ccb plan lane cancel --lane <id> --expected-snapshot <r>` | Other lane agents/panes/locks survive; cancelled callbacks remain stale evidence |
| L09 unexpected dirty worktree | An unowned tracked/untracked change appears after review and changes `dirty_digest` | Integration pauses with `workspace_dirty_unexpected`; no hidden candidate is built | `ccb plan lane explain-dirty --lane <id>` | Canonical path/status/content entries identify the change; adopt/revert requires explicit owner action |

## D. Integration Saga And Crash Recovery

| Case | Initial state and fault | Required result | Recovery command | Required residue evidence |
| :--- | :--- | :--- | :--- | :--- |
| I01 kill at `prepared` | Journal persisted; no hidden candidate | Recover continues from pinned basis or rejects without ref change | `ccb plan integration recover --id <id>` | One journal lineage; no hidden/public ref leak on rejection |
| I02 kill at `integrated_hidden` | Hidden merge exists; no accepted verification | Public target unchanged; recovery verifies exact hidden commit | `ccb plan integration recover --id <id>` | Hidden ref owned by id; no duplicate merge candidate |
| I03 kill at `verified` | Verification accepted; final authority candidate absent | Recovery rechecks authority/target then creates one final candidate | `ccb plan integration recover --id <id>` | Exact test evidence digest bound to candidate |
| I04 kill at `authority_recorded` | Hidden candidate contains code plus Plan Tree `promotion_pending` record | Public target unchanged; recovery performs one CAS or conflict | `ccb plan integration recover --id <id>` | Candidate has bidirectional refs; no global done before CAS |
| I05 kill at `promoted` | Target exposes code plus explicit pending state; completion commit/runtime absent | Dependents remain frozen; recovery creates one completion commit and event | `ccb plan integration recover --id <id>` | One promotion, one completion commit, one event after replay |
| I06 event crash | Completion commit advanced target; event emission interrupted | Event replay is idempotent and reaches `published` once | `ccb plan integration recover --id <id>` | One event identity and no extra completion commit/revision on second recovery |
| I07 target moves before promote | Another accepted authority commit advances expected target | Candidate CAS fails; integration becomes conflict/rebuild-required | `ccb plan integration rebase --id <id>` | No force update; old candidate retained/classified; new verification policy explicit |
| I08 merge conflict | Lane commits cannot merge into current target | No hidden candidate is accepted; Planner/integration owner receives conflict | `ccb plan integration resolve --id <id>` | Target/Plan Tree status unchanged; conflict files confined to integration worktree |
| I09 verification failure | Hidden candidate builds but combined test fails | Saga records rejected/blocked; no promotion or completion | `ccb plan integration retry --id <id> --new-candidate <commit>` | Failed evidence immutable; retry uses new candidate identity or revision |
| I10 Plan Tree validation failure | Code merges hidden; final Plan Tree schema/link/index validation fails | No authority-recorded/promoted transition | `ccb plan integration recover --id <id>` | Hidden code not public; validation diagnostics point to exact proposal |
| I11 cleanup crash | Publish succeeds; release/worktree cleanup crashes | Completion stays published but cleanup remains explicit incomplete gate where required | `ccb plan integration cleanup --id <id>` | No active lock/lease/agent/process/socket/worktree residue after retry |

## E. Retrieval And Projection Freshness

| Case | Initial state and fault | Required result | Recovery command | Required residue evidence |
| :--- | :--- | :--- | :--- | :--- |
| Q01 authority changes during read | Target ref advances between first and second fence read | Bounded retry; exhaustion returns `read_complete=false` | `ccb plan global --read-fence` | Response includes both observed commit ranges |
| Q02 registry changes during read | Lane registry sequence advances during join | Same bounded retry/incomplete behavior | `ccb plan lanes --read-fence` | Response includes registry sequence range and observation times |
| Q03 stale Markdown projection | Generated snapshot predates authority/runtime state | UI labels snapshot stale and offers authoritative query | `ccb plan projection rebuild --name <name>` | Projection generation, source commit, registry time updated |
| Q04 partial/corrupt registry | One lane record unreadable | Global view is incomplete, not silently missing the lane | `ccb plan doctor --lanes --repair-plan` | Corrupt record quarantined/preserved; no fabricated terminal state |

## F. Real Opened-Project Qualification

| Case | Initial state and fault | Required result | Recovery command | Required residue evidence |
| :--- | :--- | :--- | :--- | :--- |
| R01 real disjoint lanes | Opened project under `/home/bfly/yunwei/test_ccb2`; two ordinary Frontdesk tasks with disjoint code scopes | Genuine overlapping Codex-primary execution, independent review, hidden integration, one join, published completion | Same target CLI recovery commands used by source/fake cases | Inspectable panes/UI/refs/artifacts plus zero cross-lane contamination |
| R02 real conflict/dependency | One conflicting pair and one dependency pair | Conflict serializes explicitly; dependency waits until published | `ccb plan frontier --explain-all` | No premature ask, worktree mutation, or dependent admission |
| R03 real controller restart | Restart control/lane controller at selected saga and lane stages | Same identities recover without duplicate provider work or promotion | `ccb plan control recover` and integration/lane recover commands | Visible recovery plus no duplicate jobs/events/commits |
| R04 provider qualification | Exact available Codex profiles, then qualified Claude secondary profile, using the frozen corpus | Each supported profile independently passes or is reported unsupported/ENV_UNMET | No provider substitution recovery | Exact provider/model/RolePack digests; no hidden fallback/retry masking |
| R05 final cleanup | Complete/cancel/fail a mixed two-lane campaign | All dynamic agents, panes, locks, hidden refs, worktrees, processes, listeners, and runtime intent are released or explicitly retained by policy | `ccb plan doctor --all-worktrees --residue` | Zero unexplained residue and control holder remains healthy |

Real source acceptance uses `/home/bfly/yunwei/ccb_source/ccb_test` from the
external test project and an inspectable opened project. Codex is primary and
Claude is the secondary cross-provider check. Gemini, Grok, OpenCode, and other
providers are not real-provider blockers for this workflow. Weak-model rows use
only exact available Codex/Claude model-profile identifiers and the same frozen
corpus; failures remain unsupported rather than being hidden by substitution.

## Gate Order

1. Schema/canonicalization and pure state-machine tests.
2. Control locator, capability, lease/fence, handoff, and takeover tests.
3. Canonical task-store migration and concurrent proposal tests.
4. Plan-only transaction crash matrix and consistent-read tests.
5. Fake-provider two-lane isolation, conflict, dependency, and saga matrix.
6. Real opened-project R01-R05 qualification.
7. Package/install/update/rollback acceptance remains a separate release gate.

No later gate waives an earlier forbidden state. A single duplicate promotion,
premature dependent admission, split holder, lost task update, mixed view marked
current, or cross-lane cleanup mutation rejects the candidate.

## Related

- [global-plan-tree-authority-and-cross-worktree-control.md](global-plan-tree-authority-and-cross-worktree-control.md)
- [global-plan-tree-storage-and-projection-migration.md](global-plan-tree-storage-and-projection-migration.md)
- [parallel-roadmap-lanes-and-planner-authority.md](parallel-roadmap-lanes-and-planner-authority.md)
- [../decisions/024-project-topology-controller-and-single-lane-first.md](../decisions/024-project-topology-controller-and-single-lane-first.md)
- [../decisions/031-global-plan-tree-authority-across-worktrees.md](../decisions/031-global-plan-tree-authority-across-worktrees.md)
