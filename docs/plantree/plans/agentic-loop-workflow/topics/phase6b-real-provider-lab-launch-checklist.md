# Phase 6B Real-Provider Lab Launch Checklist

Date: 2026-07-04
Status: B-ONLY REPEAT6 EXECUTED / L0 PASS / PHASE 6B NOT READY / APPROVAL CONSUMED

## Purpose

This checklist separates what Phase 6A already closed from what must still be
accepted before the Phase 6B real-provider lab can start. It is planning
material only. Do not run L0 or any real-provider task until a reviewer accepts
the launch request for the exact lab root, provider profiles, evidence schema,
and command shape.

References:

- [Phase 1-6 acceptance report](../history/phase1-6-acceptance-report-20260704.md)
- [Phase 6B task-pack catalog](phase6-real-provider-lab-task-packs.md)
- [Phase 1-6 evidence index](../history/phase1-6-evidence-index.md)
- [Draft L0 launch request](phase6b-l0-launch-request-20260704.md)
- [Frozen L1-L4 launch request](phase6b-l1-l4-launch-request-20260704.md)
- [L0 owner decision packet](phase6b-l0-owner-decision-packet-20260704.md)
- Reviewer2 Phase 6B readiness checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_723a4456a783-art_19fdabce655a4233.txt`
- Reviewer2 task-pack catalog acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_5ce23d15f100-art_909fc6ba1eaa410b.txt`
- Reviewer2 owner-decision packet checklist:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_7723afe08de3-art_39477072078b4fd0.txt`
- Reviewer2 owner-decision packet acceptance:
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_28befb34936c-art_8f995baaa15d4a2e.txt`

## Closed Prerequisites From Phase 6A

These are no longer Phase 6B launch blockers:

- Phase 6A fake-provider matrix accepted for the program-matrix scope:
  reviewer1 `job_712002b8f005`, reviewer2 `job_a34e79ecfc00`.
- `smoke-busy-release` accepted inside the integrated matrix; busy retain and
  later idle release evidence are recorded.
- Phase 5 lifecycle closure accepted with residual risk; source-wrapper
  failure-mode hooks remain a residual risk, not a Phase 6A blocker.
- Required fake-provider matrix cases are implemented and observed: direct
  execution, needs detail, macro adjustment, blocked, partial completion,
  reviewer rework, reviewer cannot accept, and busy release.
- L0-L5 Phase 6B task-pack catalog exists and is accepted as planning input,
  not as launch approval.

## Open Before Further Real-Provider Runs

The repeat6 L0 runtime-sanity gate has passed, but Phase 6B remains blocked
until any further real-provider run is accepted by a launch-specific reviewer
gate:

- The owner-selected provider profile map is reviewed and accepted:
  `ccb_round_reviewer -> claude`, all other six L0 roles -> `codex`.
- The provider-environment policy is reviewed and explicitly accepted:
  real-provider labs inherit the current system provider environment and must
  not export lab-local `HOME` or `CCB_SOURCE_HOME` to a fresh `source_home`.
  This intentionally uses existing real-provider credentials, quota, and
  account/session state to avoid login churn.
- Lab-local `AGENT_ROLES_STORE` seeding is repeatable, uses the accepted
  RolePack ids, and seeds only the seven required L0 roles.
- The exact launch command and report schema are frozen. If a command name or
  flag depends on pending work, the launch request must mark it pending rather
  than inventing it.
- The L0 runtime-sanity task record is concrete: prompt, expected route/status,
  artifacts, timeout, stop conditions, and cleanup assertions are listed.
- The B7 report path and report sections are named before execution.
- The owner-decision packet is filled and reviewer-audited for provider
  profiles, system provider-environment inheritance, lab-local RolePack
  seeding, L0 command/schema, and B7 normalization.
- A reviewer explicitly approves any further L0 rerun or L1-L5 runtime packet.
  The repeat6 L0 approval has been consumed and does not imply approval for
  L1-L5.
- The frozen L1-L4 request is prepared in
  [phase6b-l1-l4-launch-request-20260704.md](phase6b-l1-l4-launch-request-20260704.md).
  The prior checkpoint/resume approval `job_7800c403f864`, repeat2 approval
  `job_0c8596e0895d`, repeat3 approval `job_51a85fa2fc58`, root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence-20260704`, and
  repeat2 root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence2-20260704`, and
  repeat3 root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence3-20260704` are
  consumed/historical after setup/driver failures and must not be reused.
  Repeat3 proved project-local supervisor imports through L1/L2 direct
  execution, L3 `detail_ready`, and L4 macro evidence, then failed because the
  blocked terminal used unknown artifact kind `blocked`; the B7 normalizer also
  marked otherwise useful rows as `test_design_failure`. A future L1-L4 packet
  must use a fresh root, accepted blocker evidence kind such as
  `blocker_evidence`, and repaired B7 classification ordering.
- L5 partial-only approvals `job_4e3c051ef168`, `job_af5f6fb64a7d`,
  `job_663bad41c855`, and `job_de6263827473`, plus roots
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-20260704` and
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat2-20260704`
  and
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l5-partial-only-repeat3-20260704`,
  are consumed/historical and must not be reused. Repeat2 proved the plan-root
  and project-local supervisor import repairs through `direct_execution`, then
  failed with `round_result_source=ask_submission_failed` because ask-first
  direct execution submitted plain `ask` from an active CCB task context.
  Worker1 repaired that source blocker in `job_19092d158390`, accepted by
  reviewer2 `job_56466011201a`: result-needed ask-first child asks now use CCB
  chain routing. Repeat3 inherited the current system provider environment and
  reached worker partial evidence, but reviewer ask submission failed with
  `ask --chain requires an active parent job for the sender`. Worker1 source
  repair `job_52ec099f6427` is accepted by reviewer2 `job_766050825b27`:
  watched ask-first child asks now use runner-owned `system` sender, no
  callback/chain, no silence, and immediate watch. A future L5 packet must use
  a fresh root, inherit the current system provider environment without
  lab-local `HOME`/`CCB_SOURCE_HOME` overrides, verify the `system` sender
  repair, and obtain fresh launch-specific reviewer approval before any runtime
  command. The current fresh-packet lane is worker3 `job_2faf4fd57789`.
- A future L1-L4 or L5 launch packet must prove that every supervisor artifact
  passed to `ccb plan task-artifact --file`, including route, detail, terminal,
  and round-evidence files, is created or copied inside the lab project root.
  Files under only the outer lab root are invalid for `plan task-artifact
  --file`.

Current L0 request draft:

- [phase6b-l0-launch-request-20260704.md](phase6b-l0-launch-request-20260704.md)
  is marked
  `B-ONLY REPEAT5 EXECUTED / VALID_NON_SUCCESS / APPROVAL CONSUMED / DO NOT RUN`.
  Reviewer2 `job_960ec614c477` was consumed by the first failed run. Reviewer2
  `job_f3adf3a31988` approved one corrected repeat run; that approval is also
  consumed. The repeat run submitted variant A ask job `job_25a9c7e4a9b6`, but
  its command log stopped after `ask_a_orchestrator_compact` because the
  supervisor execution harness piped the frozen script through stdin and
  `ccb_test ask` inherited/consumed the remaining script body. Reviewer2
  `job_041526ab5f10` then approved one repeat2 run; that approval is consumed.
  Repeat2 proved the stdin fix and reached variant B, but it did not pass:
  variant A compact ask submitted as `job_40835bfeed99`, A release left the
  dynamic orchestrator busy/bound with `released_count=0`, and B commit/apply
  failed with `agent profile ccb_orchestrator exceeds max_instances=1`. The
  approved repeat2 B7 normalizer also missed `import hashlib`, so talk2 wrote a
  supervisor fallback B7 from command logs and runtime artifacts. Reviewer2
  `job_90cc9a80d7a0` then approved one repeat3 run; that approval is consumed.
  Repeat3 proved the release gate: A compact ask submitted
  `job_b7a8ed0f671e`, A release reported `release_incomplete`, and
  `topology_a_release_clean_check` stopped before B with rc `66`. The B7
  normalizer still classified the run as `test_design_failure` because it
  expects `.ccb/runtime/asks.jsonl`; actual ask evidence existed under
  `.ccb/agents/phase6b-l0-ccb-orchestrator/jobs.jsonl`. Repair plan for the
  stdin issue:
  [phase6b-l0-ask-stdin-harness-fix-plan-20260704.md](phase6b-l0-ask-stdin-harness-fix-plan-20260704.md).
  The follow-up normalizer contract now accepts dynamic-agent `jobs.jsonl` and
  ccbd job/message artifacts as ask evidence. Reviewer2 `job_46d3377feb21`
  then approved exactly one repeat4 run; talk2 executed it once from
  `/home/bfly/yunwei/test_ccb2` with root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-repeat4-20260704`, and that
  approval is consumed. Repeat4 submitted variant A ask job
  `job_0f9d5c50b756`, then stopped before B because
  `topology_a_release` reported `release_incomplete` and
  `topology_a_release_clean_check` returned rc `66`. The repaired B7
  normalizer found dynamic-agent/ccbd ask evidence and classified the run as
  `valid_non_success`, with no input errors, no missing command labels, no
  missing artifacts, and no test-design failures. Post-B7 cleanup returned
  `kill_status: ok` and `state: unmounted`. User decision "方案 2：只跑 B，不跑
  A" is now reflected in a B-only repeat5 request using fresh root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat5-20260704`.
  Reviewer2 `job_2953f5e7ab7e` approved exactly one B-only repeat5 run; talk2
  executed it once and that approval is consumed. Repeat5 submitted compact ask
  job `job_699a6c2997ad` to `p6bl0b-orchestrator`, all command labels returned
  `0`, and B7 classified the run as `valid_non_success` with no missing
  labels, no missing artifacts, no input errors, and no test-design failures.
  The non-success reason is release residue: `topology_b_release` reported
  `release_incomplete` for `p6bl0b-frontdesk`, `p6bl0b-detailer`,
  `p6bl0b-planner`, and `p6bl0b-orchestrator`. Post-B7 cleanup returned
  `kill_status: ok` and `state: unmounted`. Worker1 `job_26e39b154740`
  implemented a source-side release/drain repair and reviewer2 accepted it in
  `/home/bfly/yunwei/ccb_source/.ccb/ccbd/artifacts/text/completion-reply/job_50ce63ab373b-art_159c32ab43394689.txt`.
  Future B-only resident planning-group release can now report explicit drained
  parked agents without killing provider sessions. Reviewer2 approved exactly
  one B-only repeat6 run in `job_8c7b404ad63c`, and the package review records
  matching approval in `job_c7ebe2d2dade`; talk2 executed it once from
  `/home/bfly/yunwei/test_ccb2` using root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l0-b-only-repeat6-20260704`.
  Repeat6 submitted compact ask job `job_4181721f9473` to
  `p6bl0b-orchestrator`, all command labels returned `0`,
  `topology_b_release` reported `released` with all four resident
  planning-group agents in `drained_agents`, B7 classified the row as `pass`,
  and post-B7 cleanup returned `kill_status: ok` / `state: unmounted`. This is
  L0 runtime-sanity evidence only, not L1-L5 or Phase 6B readiness.

## Stop Conditions

Stop before or during the lab if any condition is observed:

- commands would run from `/home/bfly/yunwei/ccb_source` instead of the
  external source-wrapper root;
- `/home/bfly/yunwei/ccb_source/ccb_test --diagnose` fails from the approved
  external root;
- any supervisor route, detail, terminal, or round-evidence file that will be
  passed to `ccb plan task-artifact --file` is outside the lab project root;
- a real-provider launch script exports lab-local `HOME` or `CCB_SOURCE_HOME`
  and therefore hides the current system provider environment;
- `AGENT_ROLES_STORE` is not the approved lab-local role store when the packet
  seeds lab-local RolePacks;
- mount topology contains mainline `edges`, `gates`, `artifacts`, or writes
  `topology_dispatch.json`;
- provider reply text mutates task authority directly;
- dynamic runtime residue is unrecoverable in `.ccb/ccb.config`, observed
  topology, or process/status evidence;
- the B-only resident planning group release records `release_incomplete` or
  records parked resident agents without explicit `drained_agents` /
  `parked_after_release` evidence; classify the row from B evidence and rely on
  the final external cleanup only after B7 evidence is captured;
- `blocked`, `partial`, reviewer-rejected, or busy-retained work is marked
  `done` without script-owned evidence;
- provider authentication or quota failures make semantic assessment
  meaningless.

## Evidence Row Schema

Every L0-L5 row must include at least:

```text
task_id
complexity_level
provider_mix
expected_route
observed_route
route_decision_correct
required_artifacts_present
ask_reachability
detailer_activated_expected
detailer_activated_observed
worker_reviewer_ask_success
reviewer_contract_citation
round_result
final_status
cleanup_result
runtime_residue
role_boundary_violations
authority_write_violations
classification
human_diagnosis_summary
```

Accepted classifications remain:

- `pass`
- `valid_non_success`
- `system_failure`
- `role_failure`
- `provider_failure`
- `test_design_failure`

## B7 Report Requirements

The Phase 6B B7 report must include:

- exact lab root, source checkout, `ccb_test` path, provider-environment
  policy, and `AGENT_ROLES_STORE`;
- provider profile selection and any provider-specific limits or safety
  controls;
- L0-L5 row table with the schema above;
- raw artifact/runtime paths for task packets, ask logs, round summaries,
  topology desired/observed files, release evidence, and cleanup checks;
- authority audit for no topology communication DSL, no topology dispatch, and
  no provider-reply authority parsing;
- runtime residue audit for process/status evidence, `.ccb/ccb.config`, and
  observed topology;
- failure taxonomy summary and human diagnosis for each non-pass row;
- first stable task-complexity breakpoint, or `unknown` with evidence;
- clear claim boundary: real-provider observations only, no production default
  enablement unless separately approved.

## Reviewer Launch Request Shape

Send the launch reviewer a short request with:

- lab root and provider-environment policy;
- provider profiles and current-system credential/session inheritance plan;
- lab-local RolePack seed command or procedure;
- exact L0 command sequence and timeout;
- L0 prompt/task record;
- expected artifacts and evidence row fields;
- stop conditions copied or linked from this checklist;
- B7 report output path;
- explicit request: approve L0 only, or approve the named L0-Ln sequence.

Do not start Phase 6B from this checklist alone.
