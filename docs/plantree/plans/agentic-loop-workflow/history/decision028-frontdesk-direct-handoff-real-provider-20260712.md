# Decision 028 Frontdesk Direct-Handoff Real-Provider Acceptance

Date: 2026-07-12
Status: Accepted for Decision 028 and the two-workgroup real-rework row
Branch: `workflow/agentic-loop-topology`

## Scope

This run validates the small-kernel boundary introduced by Decision 028 in one
fresh, visible Config V3 project. An ordinary user request entered Frontdesk;
Frontdesk classified it, authored intake evidence, and submitted exactly one
silent Planner ask through its sole managed capability. Controller code
validated and persisted the request but did not reconstruct the semantic
message or observe Frontdesk completion to create a second handoff.

The same project then exercised the complete downstream path: Planner,
immaculate Orchestrator, two parallel Worker/Reviewer workgroups, real bounded
rework in both groups, controller-owned Git integration, project-root tests,
immaculate Round Reviewer, task result import, dynamic release, and cleanup.

## Strict Failures And Repairs

Fresh consumed roots were preserved as non-success evidence while the source
was repaired:

- Planner initially failed to mount because an empty Role command allowlist
  was incorrectly treated as requiring a provider MCP capability. Empty
  allowlists now require no tool; Frontdesk still requires its one capability.
- Frontdesk's MCP call initially prompted for approval and inherited unrelated
  MCP servers. The generated Frontdesk Codex profile now removes inherited
  servers, enables only `ccb_frontdesk_ask_planner`, marks it required, and
  explicitly pre-approves that exact tool while unknown tools remain prompt
  gated.
- A successful direct handoff was initially followed by a false Frontdesk
  completion failure because the legacy prose boundary parser expected the old
  intake body in the provider's final receipt. Finalization now accepts a short
  receipt only after cross-validating the persisted script-owned activation,
  Planner job, target, silence flag, task id, project, and body digest.
- The first full repository gate exposed a fork-to-exec race in runtime
  accelerator ownership: the first complete `/proc` sample could still be the
  pre-exec Python identity. Ownership now waits on the same PID for the exact
  accelerator argv/cwd/executable identity; a persistent lookalike still fails
  closed. The former failing heartbeat case passed ten consecutive retries.
- The same gate exposed one stale CLI help assertion after adding the internal
  `--inline-request` transport flag. The router help contract now checks the
  complete public usage and flag description.

The fixes did not restore the legacy completed-reply relay, provider session
observer, generic shell access, arbitrary MCP tools, or Controller-authored
semantic prompts.

## Accepted Visible Run

Project root:
`/home/bfly/yunwei/test_ccb2/decision028-frontdesk-direct-final-20260712072335`

The source worktree's explicit `ccb_test` opened the project with inherited
system provider configuration and a project-local Role store. Config V3
validated with resident `frontdesk` and `planner`, five dynamic profiles, two
maximum workgroups, two maximum parallel workgroups, and capacity digest
`sha256:9ab9cf5518124ff6997171fc6af1e23762b93dc8e7fe7efe8f9d7fa20ac311f8`.

The user asked naturally for inventory normalization, deterministic reporting,
documentation, and tests. No routing, role, workgroup-count, or expected-result
instruction was included.

Direct handoff evidence:

| Boundary | Job | Evidence |
| :--- | :--- | :--- |
| User -> Frontdesk | `job_6c88e4472b20` | Completed once; final receipt reported the persisted Planner submission. |
| Frontdesk -> Planner | `job_2584ecf35c46` | `from_actor=frontdesk`, target `planner`, `silence=true`, task `act-frontdesk-job_6c88e4472b20`. |
| Planner -> authority import | same Planner job | Created task `deterministic-stock-health-library-20260711232606` and script-owned task packet/contract. |
| Orchestrator | `job_0776e13f0461` | Selected two path-disjoint parallel nodes and emitted one imported bundle. |

No second Planner job or legacy completed-Frontdesk relay was present.

## Worker-Owned Review And Rework

The controller mounted each Worker and Reviewer together but submitted only
the Worker root job. Each Worker contacted its assigned Reviewer through a
restricted chain and handled the returned result itself.

| Node | Worker root | First review | Finding | Recheck | Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `node-001` | `job_6ae6d8bcf570` | `job_3e404e0434ad` | `-0.5` was truncated to zero before negative validation. | `job_85f26b8da974` | `pass` after raw-value validation and regression test. |
| `node-002` | `job_1f21f843d09a` | `job_77f96febc145` | README documented unsupported `quantity` instead of `on_hand`. | `job_e26e572dbe9f` | `pass` after README-only correction. |

Both nodes recorded `rework_count=1`. The result-chain continuations returned
to the same Worker context. Controller code did not author Reviewer requests,
interpret findings into repair instructions, or bypass the Reviewer score.

## Integration, Round, And Lifecycle Evidence

- Controller-reviewed node commits:
  `981aab4b90e32fbdafd5251602b20bae6c322e1f` and
  `bb1744a774401b340a728d99319be5a76194138e`.
- Deterministic merge order: `node-001`, then `node-002`.
- Promoted root head: `d8a6b3a901d4f81868af6dbe0d81f30f64410b5d`.
- Promoted tree: `git-tree:sha1:e4c2977b4f4d84c24fa10f49f67781ae52826228`.
- Integration and supervisor root verification:
  `python -m unittest discover -s tests`, `7 passed`.
- Round Reviewer job `job_8a99582b80cd` returned `round result: pass`.
- Script-owned task state became `done`, `next_owner=terminal`,
  `current_loop=null`, and `last_round.result=pass`.
- Controller removed both node worktrees, the integration worktree, and all
  three temporary branches after evidence capture.
- Desired and observed topology ended with `agents=[]`; orchestrator, four
  node agents, and Round Reviewer all ended `stopped`.
- The visible `ccb-exec` window disappeared. Only Frontdesk in `ccb-user` and
  Planner in `ccb-plan` remained mounted and idle.

The project was then detached and closed with exact project-level
`ccb_test kill -f`. Final state was `unmounted`; project process and socket
scans were empty.

## Closure Follow-Up

Commit `6646f6a3` closed three runtime gaps exposed by fresh real-provider
reruns rather than weakening the accepted protocol:

- Successful `ask --silence` jobs are still persisted as terminal evidence,
  but no hidden `result=hidden` completion is delivered back to Frontdesk.
  Failed silent jobs remain visible to the caller.
- Managed in-project callers now use the validated mounted lease socket as
  socket authority. This fixes long project roots whose daemon socket is
  relocated under `/run/user/...` when a provider MCP child intentionally does
  not inherit `XDG_RUNTIME_DIR`; normal callers still use the configured local
  socket path.
- Worker prompts now expose Planner-authored task packets and acceptance/test
  references as absolute, read-only project-root authority paths. Workers no
  longer attempt to resolve untracked PlanTree authority inside isolated Git
  worktrees.
- Round Reviewer input is now the versioned compact
  `ccb.loop.round_review_envelope.v1`. It preserves task/bundle/capacity
  identity, reviewed commit/tree lineage, integration/root verification
  digests, authority checks, and cleanup state while remaining inline below
  the request-artifact spill threshold.

The final accepted follow-up project was
`/home/bfly/yunwei/test_ccb2/decision028-silence-round-inline-final4-20260712085421`.
It used inherited system provider credentials, a project-local Role store, and
a long root that forced relocated daemon sockets.

| Boundary | Evidence |
| :--- | :--- |
| User -> Frontdesk | `job_4eb671304e32`; completed with no successful-silence reply delivery. |
| Frontdesk -> Planner | `job_4597d7295169`; `from_actor=frontdesk`, `silence=true`, exactly one submission. |
| Orchestrator | `job_fb6181c00bb0`; selected one workgroup because the shared API/test/doc change was not safely path-disjoint. |
| Worker -> Reviewer | Worker `job_3eb5614cb5bd` created Reviewer chain child `job_48cebdaa09ca`; continuation returned as `job_6fed21dde81b`. |
| Round Reviewer | `job_10c751eca40e`; 3161-byte inline request, no `body_artifact`, `round result: pass`. |

The reviewed node commit was
`fa65c5678f87f07208eb4173eb416518ce2be2da`; promoted root head was
`cef0b44a0c9db422a7dddf4b6d589eae9ef6673b` with tree
`git-tree:sha1:9ae832e59420668997cc5638a3ae682beb1dd8cc`. Root verification passed
`13` tests. Task authority ended `done/pass`, `next_owner=terminal`, and
`current_loop=null`. Observed topology ended empty with retained and
release-incomplete counts both zero. Project-level `ccb_test kill -f` then
left lifecycle state `unmounted` and no related process residue.

Three preceding fresh roots were consumed as strict failure evidence: one
exposed caller-environment contamination, one reproduced the relocated-socket
MCP failure, and one exposed project-authority refs incorrectly resolved from
the Worker worktree. None was reused after repair.

## Source Verification

- Affected MCP/RolePack/provider/dispatcher/daemon/CLI suite: `393 passed`.
- Runtime accelerator ownership/lifecycle and CLI help regression: `30 passed`.
- Former heartbeat race selector repeated ten times: `10/10 passed`.
- Final full non-provider-blackbox repository gate after the closure follow-up:
  `4324 passed, 2 skipped, 21 deselected in 671.99s`.
- Full G5 multi-workgroup real-CLI/fake-runtime matrix after adapting the fake
  provider to the versioned compact round envelope: `39 passed`.
- Changed-source `py_compile`, `pyflakes`, Markdown link checks, whitespace
  checks, and `git diff --check`: passed.
- Post-suite process and socket scans for the workflow worktree and both pytest
  roots were empty.

## Acceptance Boundary

Decision 028 is accepted: Frontdesk owns the semantic Planner handoff, the
Controller remains a deterministic validation/recovery kernel, and the full
visible two-workgroup workflow closes without dynamic residue.

This run also closes the previously missing real bounded-rework row for the
two-workgroup Codex baseline. It does not close G6 three/four-workgroup,
in-flight restart, busy-retain, non-Codex provider qualification, packaged
candidate, default enablement, or publication gates.

## Related

- [../decisions/028-frontdesk-owned-planner-silence-handoff.md](../decisions/028-frontdesk-owned-planner-silence-handoff.md)
- [g6-worker-owned-review-chain-real-provider-20260712.md](g6-worker-owned-review-chain-real-provider-20260712.md)
- [../goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md)
