# Agentic Loop Workflow Plan

Date: 2026-06-24

## Purpose

Design a CCB-native multi-agent workflow loop that further reduces the burden
on the `frontdesk` group. In this model, `frontdesk` remains the user-facing boundary and
escalation surface, while planning, execution-document maintenance, task
decomposition, dynamic worker-team activation, loop monitoring, recovery, and
plan-tree synchronization are handled by separate roles under a scripted state
machine.

The basic design premise is to combine a simple, stable program kernel with
flexible agent intelligence. Scripts enforce hard constraints, identity,
state, locks, indexes, and commit rules. Agents provide semantic understanding,
planning, review, diagnosis, and human-readable documents.

The direction borrows Trellis' durable-state idea, where workflow truth lives
outside the model conversation and is advanced through scripts rather than
free-form memory. It also borrows the Team Builder idea from AutoGen Studio:
teams, roles, handoffs, and termination conditions should be declared as
workflow objects rather than improvised in every run.

CCB should not copy Trellis' implicit provider-native subagent model. Because
CCB already has visible agents, `ask`, callbacks, panes, runtime status, and
daemon-owned communication state, this plan favors explicit, inspectable,
recoverable workflow loops.

## File Map

- [roadmap.md](roadmap.md): planning sequence, current design status, and
  readiness gates.
- [implementation-status.md](implementation-status.md): current operational
  handoff, latest landed workflow slice, active TODO, blockers, and last
  verification.
- [public three-layer architecture guide](../../../agentic-loop-workflow-architecture.zh.md):
  Chinese overview of the Frontdesk/Detailer, Planner/Orchestrator, and
  parallel workgroup layers, with Mermaid sources and an editable SVG/PNG
  promotional graphic; capability claims remain bounded by this plan's
  implementation status and acceptance evidence.
- [history/phase1-6-evidence-index.md](history/phase1-6-evidence-index.md):
  compact index of accepted Phase 1-6 evidence, checklist-only artifacts,
  planning inputs, real-provider B7 evidence, and final acceptance reports.
- [history/phase1-6-acceptance-report-20260705.md](history/phase1-6-acceptance-report-20260705.md):
  current final Phase 1-6 acceptance report; Phase 6A is accepted for
  fake-provider program-matrix scope, and Phase 6B is accepted for initial
  real-provider single-round capability with production/default enablement
  still out of scope.
- [history/phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md](history/phase1-6-deployment-readiness-p1-dynamic-lifecycle-20260708.md):
  P1 post-acceptance deployment-readiness evidence for real-project dynamic
  release, busy-retain, UI/sidebar visibility, and observer timeout behavior;
  not the final deployment-readiness report.
- [history/visible-three-round-dynamic-window-e2e-20260710.md](history/visible-three-round-dynamic-window-e2e-20260710.md):
  direct `talk2` evidence from an opened real-provider project covering three
  sequential direct-execution loops, visible window creation/removal, two
  resident roles, four dynamic roles per round, and repaired Claude session
  rotation after `/clear`.
- [history/visible-five-task-workflow-resilience-e2e-20260710.md](history/visible-five-task-workflow-resilience-e2e-20260710.md):
  direct `talk2` evidence from the same visible project after a five-task
  frontdesk/planner workflow, including bounded rework, four-agent release per
  round, same-turn ccbd restart recovery, dynamic Claude UI/session-security
  probing, performance attribution, and explicit credential-rehydration
  residuals.
- [history/single-lane-wave3-g3-scheduler-closure-20260711.md](history/single-lane-wave3-g3-scheduler-closure-20260711.md):
  direct source/runtime closure evidence for the one-to-four-workgroup
  ready-frontier scheduler, R2/T1 integration, crash recovery, strict release,
  and durable runtime accelerator ownership; no fake/live-provider claim.
- [history/single-lane-g5-source-fake-acceptance-20260711.md](history/single-lane-g5-source-fake-acceptance-20260711.md):
  direct `talk2` source/fake runtime acceptance evidence for one-to-four
  workgroups, restart, rework, partial, blocked, integration/root verification
  failure, round blocked, release, cleanup, and B7 campaign normalization; no
  live-provider claim.
- [history/decision028-frontdesk-direct-handoff-real-provider-20260712.md](history/decision028-frontdesk-direct-handoff-real-provider-20260712.md):
  direct `talk2` evidence from a visible real-provider project proving the
  Frontdesk-owned silent Planner handoff, two parallel Worker-owned Reviewer
  chains, genuine bounded rework in both nodes, deterministic integration,
  root and round pass, complete dynamic release, and project shutdown.
- [history/g6c-decision029-integration-and-root8-diagnostic-20260712.md](history/g6c-decision029-integration-and-root8-diagnostic-20260712.md):
  current G6C implementation checkpoint, rejected root8 real-provider
  diagnosis, detail-ready reconciliation repair, and the remaining P5/G6/G7
  acceptance gates.
- [history/g6c-root13-planner-terminal-constraint-diagnostic-20260713.md](history/g6c-root13-planner-terminal-constraint-diagnostic-20260713.md):
  rejected root13 real-provider evidence after the Git-capability repair;
  records the post-detail Planner/importer terminal-constraint gap and the
  root14 repair and acceptance gates.
- [history/g6c-root14-orchestrator-fence-diagnostic-20260713.md](history/g6c-root14-orchestrator-fence-diagnostic-20260713.md):
  rejected root14 real-provider evidence after L1 pass; records the
  Orchestrator schema-as-fence RolePack drift, fail-closed importer result,
  harness replay defect, and root15 repair gates.
- [history/g6c-source-gate-and-root15-readiness-20260714.md](history/g6c-source-gate-and-root15-readiness-20260714.md):
  accepted source/fake closure through `b14c66ef`, corrected full-suite
  environment contract, post-run live-residue audit, and fresh root15
  admission boundary.
- [history/g6c-current-main-source-acceptance-20260714.md](history/g6c-current-main-source-acceptance-20260714.md):
  accepted current-main source/fake candidate at `2c936a48`, including the
  focused and historical-failure gates, rejected harness-path diagnosis,
  clean full-suite proof, G7 safeguards, and zero-residue cleanup audit.
- [history/g6d-phase2-wiring-real-provider-diagnostic-20260714.md](history/g6d-phase2-wiring-real-provider-diagnostic-20260714.md):
  rejected Codex/Claude Frontdesk-to-Planner lanes, the production
  `loop_runner_auto`/Frontdesk service-assembly defect, repair `62753d63`,
  focused regression evidence, and zero-residue cleanup boundary.
- [history/g6e-planner-readless-provider-projection-diagnostic-20260714.md](history/g6e-planner-readless-provider-projection-diagnostic-20260714.md):
  accepted Phase2 regression closure, rejected real Planner permission
  projection, provider/model qualification boundaries, RolePack refreeze
  requirements, and the next safe admission order.
- [history/global-plan-tree-control-review-20260715.md](history/global-plan-tree-control-review-20260715.md):
  independent review findings and revision disposition for repository-global
  Plan Tree election, authority closure, migration, integration, and acceptance.
- [history/global-plan-tree-claude-coworker-review-20260715.md](history/global-plan-tree-claude-coworker-review-20260715.md):
  requested Claude coworker review accepting the revised global Plan Tree
  design with small specification clarifications, all now incorporated.
- [history/phase1-6-deployment-readiness-p2-frontdesk-pressure-20260708.md](history/phase1-6-deployment-readiness-p2-frontdesk-pressure-20260708.md):
  P2 post-acceptance deployment-readiness evidence for real-project
  frontdesk macro-intake pressure across direct, detail, macro-adjustment, and
  blocked route shapes; not the final deployment-readiness report.
- [history/phase1-6-deployment-readiness-p3-module-audit-20260708.md](history/phase1-6-deployment-readiness-p3-module-audit-20260708.md):
  P3 six-module deployment-readiness audit across Plan/Task Document,
  Orchestration, Mount Topology, Ask Collaboration, Dynamic Lifecycle, and
  Evidence/Reporting; result is `PASS_WITH_LIMITS`, not production/default
  enablement.
- [history/phase1-6-deployment-readiness-report-20260708.md](history/phase1-6-deployment-readiness-report-20260708.md):
  final deployment-readiness report, now including the post-fix fullflow
  retest at
  `/home/bfly/yunwei/test_ccb2/deploy-fullflow-talk2-selfrun-20260708202901`,
  P5 source packaging gate status, and the post-gate automatic frontdesk stress
  retest at
  `/home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921`;
  repeatability retest at
  `/home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126`; and
  real npm latest install smoke at
  `/home/bfly/yunwei/test_ccb2/p5-real-npm-install-talk2-20260708212535`;
  current-source preview release/install smoke at
  `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205`;
  installed-preview workflow closure smoke at
  `/home/bfly/yunwei/test_ccb2/p5-installed-preview-smoke-talk2-202607082220`;
  current source tree is ready for package-owner staging/release decisions,
  while production/default enablement remains blocked.
- [history/phase1-6-deployment-readiness-p5-packaging-gate-20260708.md](history/phase1-6-deployment-readiness-p5-packaging-gate-20260708.md):
  P5 source packaging gate; source-wrapper smoke, source tests, npm dry-run,
  project/local-prefix install smoke, global-prefix skip-download install
  smoke, public npm latest install smoke, current-source preview release/install
  smoke, installed-preview workflow closure smoke, and post-gate real-provider
  automatic frontdesk stress/repeatability passes after fixing deterministic
  fake-provider command-surface,
  workspace-promotion, manual-checkpoint/auto-runner idempotence, and release
  copy generated-output blockers. Release publication and production/default
  enablement remain separate package-owner decisions.
- [topics/phase1-6-active-supervision-board-20260704.md](topics/phase1-6-active-supervision-board-20260704.md):
  active `talk2` supervision lanes, current Phase 6B gates, and callback
  handling rules for the Phase 1-6 acceptance goal.
- [topics/phase1-6-deployment-readiness-supervision-20260707.md](topics/phase1-6-deployment-readiness-supervision-20260707.md):
  active post-acceptance deployment-readiness lane covering real-provider
  frontdesk entry, L1-L4 regression, dynamic lifecycle cleanup, UI/sidebar
  visibility, and observer behavior beyond the bounded Phase 6B claim.
- [topics/phase1-6-deployment-readiness-acceptance-gate-20260708.md](topics/phase1-6-deployment-readiness-acceptance-gate-20260708.md):
  strict checklist for direct `talk2` real-project validation after the
  2026-07-08 ownership change; keeps rejection rules for script-only passes,
  false dynamic unload, authority drift, frontdesk direct implementation, and
  missing visible opened-project evidence.
- [topics/phase1-6-p1-dynamic-lifecycle-runbook-20260708.md](topics/phase1-6-p1-dynamic-lifecycle-runbook-20260708.md):
  next direct validation runbook for P1 dynamic lifecycle, busy-retain,
  UI/sidebar, resident survival, observer timeout evidence, B7 row shape, and
  stop conditions.
- [topics/config-v3-dynamic-workflow.md](topics/config-v3-dynamic-workflow.md):
  implementation-ready release dependency for keeping `version = 2` static
  CCB config intact while adding opt-in `version = 3` dynamic workflow config
  with two resident roles, five immaculate dynamic profiles, provider/model
  settings, workgroup/physical capacity, rolepack checks, migration dry-run,
  and source/runtime acceptance criteria.
- [topics/config-v2-static-control-panel.md](topics/config-v2-static-control-panel.md):
  companion design topic for a `version = 2` static layout control panel that
  edits `[windows]` through a visual split builder, exposes agent overlays only
  as folded details, and keeps validate/dry-run/apply behind the same config
  authority boundary.
- [topics/phase6b-real-provider-claim-coverage-matrix.md](topics/phase6b-real-provider-claim-coverage-matrix.md):
  Phase 6B real-provider claim requirements mapped to current evidence,
  final aggregation state, and remaining non-production boundaries.
- [topics/phase6b-repeat8-direct-execution-failure-note.md](topics/phase6b-repeat8-direct-execution-failure-note.md):
  supervisor diagnosis for the consumed L1-L4 repeat8 run where worker copy
  workspace success did not land in the lab project root.
- [open-questions.md](open-questions.md): unresolved product, safety, and
  implementation questions.
- [goals/orchestrator-dynamic-capacity-goal.md](goals/orchestrator-dynamic-capacity-goal.md):
  historical implementation and real-test goal for the `loop.role_profiles`
  and `ccb loop capacity` substrate, now superseded as the
  orchestrator-facing path by topology proposal and reconciliation.
- [goals/single-lane-multi-workgroup-release-goal.md](goals/single-lane-multi-workgroup-release-goal.md):
  current release goal for one task lane, one orchestration bundle, one to four
  independently reviewed worker/reviewer workgroups, deterministic Git
  integration, Config V3, whole-block parallel implementation waves,
  `talk2`-owned visible real-provider acceptance, and separate package/install
  versus explicitly authorized publication gates while preserving Config V2.
- [goals/planner-plan-script-goal.md](goals/planner-plan-script-goal.md):
  implementation and source-test goal for the first planner role boundary and
  `ccb plan` task-packet command surface.
- [goals/loop-runner-bridge-goal.md](goals/loop-runner-bridge-goal.md):
  next implementation goal for removing the manual bridge between a ready task
  packet and one script-owned execution round, while preserving the
  simple-kernel/flexible-agent boundary.
- [goals/workflow-rolepack-landing-goal.md](goals/workflow-rolepack-landing-goal.md):
  landing goal for the first CCB workflow RolePack draft set, including common
  authority rule, shared templates, P0 planner/reviewer/broker/orchestrator/
  round checker roles, simplified P1 frontdesk/worker/checker roles, and
  targeted manifest/projection tests.
- [goals/workflow-runner-state-router-goal.md](goals/workflow-runner-state-router-goal.md):
  follow-up goal for extending the one-shot runner into a minimal workflow
  state router that activates planner for planning states, execution for ready
  states, and stops on paused or terminal states without moving semantic
  judgment into scripts.
- [goals/clarification-planner-followthrough-goal.md](goals/clarification-planner-followthrough-goal.md):
  next implementation goal for adding the V1 `ccb question` artifact surface,
  macro broker/frontdesk clarification loop, normalized answers, planner
  artifact import, plan-reviewer gate, optional task-detailer refinement, and
  script-owned transition to `ready`.
- [goals/workflow-rolepack-external-spec-handoff-goal.md](goals/workflow-rolepack-external-spec-handoff-goal.md):
  external handoff goal for promoting the workflow Role drafts into
  `/home/bfly/yunwei/agent-roles-spec`, installing them through CCB's Role
  store, and proving planner/task-detailer/broker/frontdesk/reviewer/
  orchestrator artifact collaboration.
- [goals/workflow-closure-smoke-goal.md](goals/workflow-closure-smoke-goal.md):
  repeatable source-wrapper smoke for the complete fake-provider workflow
  closure, including macro planner/broker/frontdesk/reviewer transitions,
  optional task-detailer refinement, ready execution, dynamic worker/checker
  release with `--policy auto`, and the current explicit-windows follow-up
  finding.
- [goals/minimum-production-candidate-goal.md](goals/minimum-production-candidate-goal.md):
  narrow production-candidate gate for one scripted workflow closure using
  `ccb plan`, `ccb question`, `ccb loop runner --once`, dynamic worker/checker
  capacity, round-result import, and auto-release cleanup.
- [goals/mount-topology-ask-first-landing-goal.md](goals/mount-topology-ask-first-landing-goal.md):
  phased landing plan for Decision 020, including mount-topology schema split,
  task document anchors, orchestrator triage, ask-first execution, release/
  retain hardening, and stage-specific test/review gates.
- [goals/phase6-single-round-task-matrix-goal.md](goals/phase6-single-round-task-matrix-goal.md):
  Phase 6 acceptance target for single-round workflow success across different
  task types, including direct execution, detail-needed, macro-adjustment, and
  blocked routes.
- [goals/phase6-real-capability-assessment-goal.md](goals/phase6-real-capability-assessment-goal.md):
  extended Phase 6 capability assessment for real-provider task complexity,
  abnormal-state injection, failure taxonomy, and deep post-run analysis.
- [goals/phase6-build-stage-verification.zh.md](goals/phase6-build-stage-verification.zh.md):
  Chinese build-stage verification and acceptance plan that maps Satinoos
  documentation, fake-provider matrix, real-provider lab, abnormal injection,
  and final analysis report into staged gates.
- [goals/phase1-6-acceptance-goal.zh.md](goals/phase1-6-acceptance-goal.zh.md):
  Chinese acceptance-goal summary for Phase 1-6 stage gates, post-completion
  module-level acceptance, and final deep Phase 6A/6B testing claims.
- [topics/architecture.md](topics/architecture.md): proposed role topology,
  loop lifecycle, handoff rules, and failure escalation model.
- [topics/complete-workflow-design.md](topics/complete-workflow-design.md):
  end-to-end workflow loop design, planner activation rules, result routing,
  stop conditions, script authority, and current V1 implementation status.
- [topics/agentic-workflow-scheme.zh.md](topics/agentic-workflow-scheme.zh.md):
  Chinese system design that reorganizes the workflow around a simple stable
  kernel, flexible semantic agents, state projection, role groups, script
  capabilities, lifecycle, V1 loop closure, and deferred items.
- [topics/planner-role-design.md](topics/planner-role-design.md): planner
  authority, readiness rules, clarification boundaries, script authority, and
  orchestrator triage handoff.
- [topics/ccb-workflow-plan-tree-skill-overlay.md](topics/ccb-workflow-plan-tree-skill-overlay.md):
  Config V3/Planner-only replacement of the public logical `plan-tree` skill,
  with managed-home isolation, Decision 030 proposal-only permissions,
  projection digest binding, reload behavior, and negative activation gates.
- [topics/parallel-roadmap-lanes-and-planner-authority.md](topics/parallel-roadmap-lanes-and-planner-authority.md):
  target Plan Tree Roadmap Graph, Workflow Lane, ready-frontier, planner
  single-writer, code-worktree, conflict, and integration-gate design for
  serial and parallel project work.
- [topics/global-plan-tree-authority-and-cross-worktree-control.md](topics/global-plan-tree-authority-and-cross-worktree-control.md):
  sole detailed protocol for portfolio/local identity, locator election,
  holder lease/fencing, canonical task migration, typed authority closure,
  consistent retrieval, and integration recovery across Git worktrees.
- [topics/global-plan-tree-cross-worktree-acceptance-matrix.md](topics/global-plan-tree-cross-worktree-acceptance-matrix.md):
  falsifiable control, task-store, lane, integration-saga, freshness, real
  provider, and zero-residue gates with explicit fault injection and recovery.
- [topics/global-plan-tree-storage-and-projection-migration.md](topics/global-plan-tree-storage-and-projection-migration.md):
  guarded migration from shared task-index authority and three-file legacy
  Planner projection into canonical task records and typed global proposals.
- [topics/planner-feedback-and-task-set-closure-plan.md](topics/planner-feedback-and-task-set-closure-plan.md):
  implementation and real-test plan for Detailer-to-Planner macro correction,
  task-set terminal aggregation, revision-fenced Planner Roadmap backfill, and
  Frontdesk/user completion reporting.
- [topics/planner-plan-tree-brief-and-detail-boundary.md](topics/planner-plan-tree-brief-and-detail-boundary.md):
  planner-owned plan brief shape and boundary with task-detailer-owned detail
  docs and per-task execution refinement.
- [topics/task-detailer-role-design.md](topics/task-detailer-role-design.md):
  short-lived task refinement role that reads macro task refs, plan-tree/source
  evidence, performs detailed self-research, owns task-local clarification, and
  emits detailed execution packets without becoming the long-lived planner.
- [decisions/029-planner-feedback-and-task-set-closure.md](decisions/029-planner-feedback-and-task-set-closure.md):
  accepted planning boundary for direct restricted Detailer feedback, durable
  task-set closure authority, exact-once Planner rehydration, and Frontdesk
  status notification.
- [decisions/031-global-plan-tree-authority-across-worktrees.md](decisions/031-global-plan-tree-authority-across-worktrees.md):
  decision that linked worktrees share one repository Plan Tree control domain,
  one elected and fenced writer and authority stream, while lanes consume
  immutable typed snapshots and integration uses a recoverable promotion saga.
- [topics/state-and-script-contract.md](topics/state-and-script-contract.md):
  proposed short-term progress store, script entrypoints, state transitions,
  artifact requirements, and plan-tree synchronization rules.
- [topics/plan-and-runtime-list-structure.md](topics/plan-and-runtime-list-structure.md):
  durable plan packet layout, runtime loop list layout, and script-owned write
  surfaces inspired by Trellis but adapted for visible CCB agents.
- [topics/plan-update-script-landing.md](topics/plan-update-script-landing.md):
  V1 landing plan for `ccb plan task-*` scripts, task packet layout, authority
  rules, and test targets.
- [topics/orchestrator-role-capability.md](topics/orchestrator-role-capability.md):
  orchestrator role capability boundary, ask activation model, 1-4 node
  complexity slicing, runtime-agent request semantics, and task-dispatch
  constraints.
- [topics/semantic-orchestration-and-controller-boundary.md](topics/semantic-orchestration-and-controller-boundary.md):
  target boundary where planner owns global structure, detailer returns compact
  global impact, orchestrator emits one coupled workgraph/task-assignment
  bundle, and the controller performs physical dispatch without semantic
  reinterpretation.
- [topics/single-lane-multi-workgroup-modification-and-test-plan.md](topics/single-lane-multi-workgroup-modification-and-test-plan.md):
  implementation-ready source map, bundle and node-state contracts, exact-once
  scheduler, Git worktree/integration protocol, failure semantics, 1-4 pair
  topology, direct/fake/real test matrix, B7 evidence, and release stop rules.
- [topics/runtime-workflow-graph-and-reconciler.md](topics/runtime-workflow-graph-and-reconciler.md):
  landed desired-state topology controller and earlier broader workflow-graph
  direction; Decision 020 narrows the preferred future scope to mount
  topology.
- [topics/mount-topology-and-ask-first-orchestration.md](topics/mount-topology-and-ask-first-orchestration.md):
  simplified landing direction where topology owns agent/window/pane/provider
  lifecycle, normal collaboration uses `ask`, and small task/contract/summary
  documents activate the next process.
- [topics/phase6-real-provider-lab-task-packs.md](topics/phase6-real-provider-lab-task-packs.md):
  accepted-as-planning-input Phase 6B real-provider lab task-pack catalog for
  L0-L5; not a lab launch approval.
- [topics/phase6b-l1-l4-launch-prep.md](topics/phase6b-l1-l4-launch-prep.md):
  planning-only Phase 6B L1-L4 candidate task and B7 aggregation prep for a
  future launch-review request after the L0 repeat6 runtime-sanity pass.
- [topics/phase6b-l1-l4-launch-request-20260704.md](topics/phase6b-l1-l4-launch-request-20260704.md):
  frozen L1-L4 real-provider launch request; reviewer2 accepted it as
  doc-only, with no approval-to-run.
- [topics/phase6b-l1-l4-launch-request-sequence10-20260704.md](topics/phase6b-l1-l4-launch-request-sequence10-20260704.md):
  consumed L1-L4 sequence10 launch packet; reviewer1 fallback approved one run,
  which stopped at L1 with copy-workspace-only changes and repeat10 B7
  `not_claimable`; not a Phase 6B claim.
- [topics/phase6b-l1-l4-launch-request-sequence11-20260704.md](topics/phase6b-l1-l4-launch-request-sequence11-20260704.md):
  consumed L1-L4 sequence11 launch packet; reviewer1 approved one run, L1/L2
  reached `done/pass`, L3 failed at detail packet import and `detail_ready`,
  repeat11 B7 is `not_claimable`, and follow-up repairs are accepted for
  future fresh packets.
- [topics/phase6b-l1-l4-launch-request-sequence12-20260705.md](topics/phase6b-l1-l4-launch-request-sequence12-20260705.md):
  consumed L1-L4 sequence12 launch/evidence record for root
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-l1-l4-sequence12-20260705`
  and B7 path
  `docs/plantree/plans/agentic-loop-workflow/history/phase6b-real-provider-l1-l4-repeat12-b7-20260705.md`;
  `Status: pass`, with L1/L2 pass and L3/L4 valid non-success rows.
- [topics/phase6b-reviewer-rework-partial-observation-tranche.md](topics/phase6b-reviewer-rework-partial-observation-tranche.md):
  planning-only L5 tranche packet for the remaining Phase 6B requirement to
  observe reviewer rework or partial classification; not launch approval.
- [topics/phase6b-l5-partial-launch-request-20260704.md](topics/phase6b-l5-partial-launch-request-20260704.md):
  launch-specific Phase 6B L5 partial-only request packet for reviewer2
  disposition; no runtime evidence or Phase 6B claim by itself.
- [topics/phase6b-real-provider-lab-launch-checklist.md](topics/phase6b-real-provider-lab-launch-checklist.md):
  Phase 6B launch-readiness checklist separating prerequisites closed by Phase
  6A from still-open provider/profile/isolation/schema/reviewer launch gates.
- [topics/phase6b-l0-launch-request-20260704.md](topics/phase6b-l0-launch-request-20260704.md):
  consumed L0-only real-provider launch request history; B-only repeat6 passed
  runtime sanity, but this remains L0 evidence and does not approve L1-L4 or
  Phase 6B completion.
- [topics/phase6b-l0-owner-decision-packet-20260704.md](topics/phase6b-l0-owner-decision-packet-20260704.md):
  planning-only owner-decision packet for Phase 6B L0 provider profile,
  provider-home, RolePack seed, command/schema, and B7 reporting choices; not
  launch approval.
- [topics/phase6a-fake-provider-matrix-closure-runbook.md](topics/phase6a-fake-provider-matrix-closure-runbook.md):
  Phase 6A fake-provider matrix closure runbook and evidence/rerun guide; not
  Phase 6B or production launch approval.
- [topics/phase1-6-final-packaging-hygiene.md](topics/phase1-6-final-packaging-hygiene.md):
  final source-control packaging hygiene checklist for generated artifacts,
  shared README/topic edits, provider-pane files, and RolePack draft tracking.
- [topics/phase1-6-module-level-audit-worksheet.md](topics/phase1-6-module-level-audit-worksheet.md):
  worksheet for the post-matrix six-module audit required before the final
  Phase 1-6 acceptance report.
- [topics/orchestrator-rolepack-blueprint.md](topics/orchestrator-rolepack-blueprint.md):
  reviewed `mother` design for the `agentroles.ccb_orchestrator` RolePack,
  including identity, memory, skills, templates, package shape, and validation
  gates.
- [topics/role-catalog-and-boundaries.md](topics/role-catalog-and-boundaries.md):
  V1/V2 role catalog and role boundaries for converting the workflow design
  into Agent Roles specs, including frontdesk, planner, plan reviewer, broker,
  orchestrator, worker, checker, round checker, monitor, recovery, and plan
  steward boundaries.
- [topics/role-class-naming-and-hierarchy.md](topics/role-class-naming-and-hierarchy.md):
  current flat Role naming and Role Collection direction, including replacement
  mapping from experimental `agentroles.ccb_*` roles and recommended
  `agentroles.collections.*` bundles.
- [topics/role-profiles-and-capacity-skill.md](topics/role-profiles-and-capacity-skill.md):
  lower-level design for `loop.role_profiles` config and `ccb loop capacity`;
  retained as the capacity substrate that topology reconciliation may use,
  rather than the preferred orchestrator-facing contract.
- [topics/dynamic-window-pane-agent-maintenance.md](topics/dynamic-window-pane-agent-maintenance.md):
  design for runtime-managed tmux windows and panes, including
  `frontdesk-dialog`, `plan-orchestrate`, per-node execution windows, runtime
  diagnostics, placement rules, release/retain behavior, and V1 layout state.
- [topics/dynamic-agent-lifecycle-and-skills.md](topics/dynamic-agent-lifecycle-and-skills.md):
  design for dynamic agent lifecycle policy, including visible/hidden/parked/
  unloaded states, long-lived role park defaults, profile-based and inline
  role-based `ccb agent add ...`, policy-based `remove`, and the
  `dynamic-agent-lifecycle` skill boundary.
- [goals/dynamic-pane-growth-goal.md](goals/dynamic-pane-growth-goal.md):
  landing target for deterministic 1->6 pane growth, overflow windows, and
  isolated tmux smoke verification before live dynamic agent movement.
- [goals/dynamic-pane-shrink-release-goal.md](goals/dynamic-pane-shrink-release-goal.md):
  planning target for dynamic agent release, 6->1 pane compaction, overflow
  window removal, busy-agent retain behavior, and live-agent safety gates.
- [topics/context-purity.md](topics/context-purity.md): context-purity
  principle, immaculate (`无垢`) activation contract, short-lived execution
  context policy, and role boundaries that keep `frontdesk` and long-lived
  planning roles free of fast-changing noise.
- [topics/clarification-flow.md](topics/clarification-flow.md): staged
  clarification flow where planner emits macro candidate questions, broker
  filters them, `frontdesk` displays curated question references, and
  `task_detailer` separately owns task-local clarification with frontend
  notification.
- [topics/execution-node-and-round-verification.md](topics/execution-node-and-round-verification.md):
  execution-node structure, checker boundaries, non-convergence handling,
  partial branch draining, and round-level verification.
- [topics/round-checker-and-planner-rehydration.md](topics/round-checker-and-planner-rehydration.md):
  round checker separation, planner next-loop rehydration inputs, and result
  routing back to planner or frontdesk.
- [decisions/001-frontdesk-name.md](decisions/001-frontdesk-name.md):
  decision to call the user-facing non-executing role `frontdesk` instead of
  `main`.
- [decisions/002-stage-batched-clarification.md](decisions/002-stage-batched-clarification.md):
  decision to use stage-batched clarification with an artifact-first broker
  instead of direct planner-to-user questioning.
- [decisions/003-flat-execution-node-and-round-checker.md](decisions/003-flat-execution-node-and-round-checker.md):
  decision to make v1 execution nodes flat `worker + checker` units and add a
  separate round-level checker for loop completion.
- [decisions/004-script-owned-plan-and-runtime-lists.md](decisions/004-script-owned-plan-and-runtime-lists.md):
  decision to keep plan packets durable and runtime lists machine-owned, with
  all authoritative writes going through CCB scripts.
- [decisions/005-orchestrator-is-asked-semantic-dispatcher.md](decisions/005-orchestrator-is-asked-semantic-dispatcher.md):
  decision to make orchestrator an ask-activated semantic dispatcher that
  requests, but does not directly perform, runtime agent load/unload.
- [decisions/006-configured-role-profiles-and-capacity-skill.md](decisions/006-configured-role-profiles-and-capacity-skill.md):
  decision to give orchestrator dynamic capacity through config-declared role
  profiles and a narrow `ccb loop capacity` command surface.
- [decisions/007-planner-proposes-scripts-write-plan-state.md](decisions/007-planner-proposes-scripts-write-plan-state.md):
  decision that planner proposes semantic artifacts while CCB scripts write
  authoritative plan state.
- [decisions/008-round-checker-separate-planner-rehydrates.md](decisions/008-round-checker-separate-planner-rehydrates.md):
  decision that round checker remains separate while planner rehydrates next
  loops from durable task and round evidence.
- [decisions/009-loop-runner-activates-planner-and-stops.md](decisions/009-loop-runner-activates-planner-and-stops.md):
  decision that planner is inside the workflow loop while loop runner owns
  activation and stop decisions from authoritative state.
- [decisions/010-simple-kernel-flexible-agents.md](decisions/010-simple-kernel-flexible-agents.md):
  decision that the workflow kernel should stay simple and stable while agents
  provide semantic flexibility through artifacts that scripts commit or reject.
- [decisions/011-runtime-layout-manager.md](decisions/011-runtime-layout-manager.md):
  decision that runtime layout manager owns dynamic tmux window/pane placement
  while orchestrator only requests semantic execution capacity.
- [decisions/012-long-lived-roles-park-before-unload.md](decisions/012-long-lived-roles-park-before-unload.md):
  decision that long-lived interactive roles default to hide/park, while
  short-lived execution roles can unload only after idle/evidence gates.
- [decisions/013-role-class-prefix-naming.md](decisions/013-role-class-prefix-naming.md):
  historical decision to replace experimental CCB-prefixed workflow role ids
  with host-neutral names; its source hierarchy direction is superseded by
  Decision 017.
- [decisions/014-runtime-workflow-graph-reconciler.md](decisions/014-runtime-workflow-graph-reconciler.md):
  decision to drive dynamic agent load/release through committed runtime
  workflow graphs and topology reconciliation instead of direct orchestrator
  lifecycle commands.
- [decisions/015-task-detailer-owns-task-refinement-and-clarification.md](decisions/015-task-detailer-owns-task-refinement-and-clarification.md):
  historical decision to keep the long-lived planner macro-level, introduce a
  short-lived `task_detailer` for detailed execution refinement, and keep
  task-local clarification inside that detailer while frontend/frontdesk only
  notifies the user; Decision 019 now adds orchestrator triage before detailer
  activation.
- [decisions/016-agent-groups-and-macro-adjustment-request.md](decisions/016-agent-groups-and-macro-adjustment-request.md):
  decision that `task_detailer` macro-drift findings must flow through
  `macro-adjustment-request` artifacts instead of direct roadmap or decision
  mutation; its source-level reusable group design is superseded by Decision
  017.
- [decisions/017-flat-roles-and-role-collections.md](decisions/017-flat-roles-and-role-collections.md):
  decision to use flat installable Roles plus Role Collections for Agent Roles
  source, while keeping CCB runtime groups in Project Binding or runtime
  topology.
- [decisions/018-planner-uses-plan-brief.md](decisions/018-planner-uses-plan-brief.md):
  decision that planner primarily maintains a compact plan brief, while V1
  task-related detail docs and execution refinement are owned by
  `task_detailer` after orchestrator asks for refinement.
- [decisions/019-orchestrator-triage-before-task-detailer.md](decisions/019-orchestrator-triage-before-task-detailer.md):
  decision that orchestrator triages planner macro packets before activating
  `task_detailer`, can dispatch direct execution, and routes macro adjustment
  requests back to planner.
- [decisions/020-mount-topology-and-ask-first-orchestration.md](decisions/020-mount-topology-and-ask-first-orchestration.md):
  decision to narrow topology to runtime mount state while keeping ordinary
  agent collaboration on `ask` and importing only stable outcomes through
  script-owned task/round artifacts.
- [decisions/021-immaculate-role-context-lifecycle.md](decisions/021-immaculate-role-context-lifecycle.md):
  decision that `orchestrator`, `task_detailer`, workers, reviewers, and round
  reviewers are immaculate (`无垢`) activation-scoped roles, while only
  `frontdesk` and `planner` retain compact long-lived conversation context.
- [decisions/022-semantic-orchestration-bundle-and-controller-execution.md](decisions/022-semantic-orchestration-bundle-and-controller-execution.md):
  decision to keep slicing, dependency design, logical assignment, and task
  publication intent in one orchestrator bundle while scripts own concrete
  binding, exact-once ask submission, state import, and lifecycle side effects.
- [decisions/023-roadmap-graph-and-workflow-lanes.md](decisions/023-roadmap-graph-and-workflow-lanes.md):
  decision that Plan Tree models serial/parallel roadmap branches and joins,
  Workflow Lane is the concurrent execution unit, one planner remains the
  default global graph writer, and multiple planners require disjoint scopes.
- [decisions/024-project-topology-controller-and-single-lane-first.md](decisions/024-project-topology-controller-and-single-lane-first.md):
  decision that lanes own independent immaculate orchestration and topology
  state, one deterministic project Topology Controller owns physical runtime
  reconciliation, and single-lane production closure precedes multi-lane code.
- [decisions/025-single-lane-multi-workgroup-release-gate.md](decisions/025-single-lane-multi-workgroup-release-gate.md):
  decision that the next release gate is one task lane with one semantic bundle
  and one to four Git-isolated `Worker + Reviewer` workgroups, controlled
  integration, Config V3, V2 compatibility, and real/package acceptance.
- [decisions/026-authority-envelope-and-adaptive-workgroup-selection.md](decisions/026-authority-envelope-and-adaptive-workgroup-selection.md):
  decision that freezes task revision, effective capacity digest, semantic
  bundle fields, node-keyed exact-once state, and orchestrator-owned adaptive
  one-to-four workgroup selection with V2-only one-group fallback.
- [decisions/027-worker-owned-review-chain-and-minimal-controller.md](decisions/027-worker-owned-review-chain-and-minimal-controller.md):
  decision that each Worker owns its bounded `ask --chain` review loop with
  the assigned Reviewer while controller code retains only deterministic
  authority, integration, recovery, and lifecycle duties.
- [decisions/028-frontdesk-owned-planner-silence-handoff.md](decisions/028-frontdesk-owned-planner-silence-handoff.md):
  decision that Frontdesk directly authors and submits one silent Planner ask,
  while Controller code only validates, deduplicates, records activation, and
  wakes or recovers the runner without semantic relay.
- [history/g6-worker-owned-review-chain-real-provider-20260712.md](history/g6-worker-owned-review-chain-real-provider-20260712.md):
  strict live-provider checkpoint for the Decision 027 two-workgroup Codex
  baseline, preserved provider-protocol failures, integration, round review,
  release, cleanup, and remaining G6 gates.
- [history/review-2026-06-26-loop-runner-readiness.md](history/review-2026-06-26-loop-runner-readiness.md):
  reviewer/coworker readiness review that narrowed the next implementation
  slice to task-loop binding, round-result import, `run-once --task-id`, and
  one-shot `loop runner --once`.
- [history/mother-rolepack-design-2026-06-27.md](history/mother-rolepack-design-2026-06-27.md):
  `mother` RolePack design review that accepted the P0/P1/P2 role priorities,
  common authority rule, host-neutral versus CCB-adapter split, and the first
  external Agent Roles spec landing order.
- [history/runtime-topology-reconciler-2026-06-30.md](history/runtime-topology-reconciler-2026-06-30.md):
  landing evidence for `ccb loop topology
  propose/validate/commit/reconcile/status/release`, desired/observed
  topology files, and add/move/park/release/reflow source-wrapper tests.
- [history/workflow-role-output-import-2026-07-02.md](history/workflow-role-output-import-2026-07-02.md):
  landing evidence for the planner/plan-reviewer role-output import bridge,
  source-wrapper draft-to-done smoke, and existing workflow closure regression.

## Related Sources

- [../ccb-self-role/README.md](../ccb-self-role/README.md)
- [../ccb-maintenance-heartbeat/README.md](../ccb-maintenance-heartbeat/README.md)
- [../managed-provider-completion-reliability/README.md](../managed-provider-completion-reliability/README.md)
- [../inter-agent-comm-reliability/README.md](../inter-agent-comm-reliability/README.md)
- [../callback-continuation-safety/README.md](../callback-continuation-safety/README.md)
- [../../baseline/runtime-flows.md](../../baseline/runtime-flows.md)
- [../../../agent-message-timeout-retry-contract.md](../../../agent-message-timeout-retry-contract.md)
- [../../../ccbd-startup-supervision-contract.md](../../../ccbd-startup-supervision-contract.md)
- [../../../ccbd-diagnostics-contract.md](../../../ccbd-diagnostics-contract.md)

## Scope

In scope:

- A user-facing `frontdesk` group that only handles user discussion, macro-task
  intake, confirmations, final reporting, and unrecoverable escalation.
- A planner that maintains long-term plan-tree state, compact plan brief,
  macro task publication, roadmap/evidence hygiene, and readiness
  recommendations without carrying implementation detail.
- A task detailer role that is resident and visible in the V1 `ccb-user`
  topology, but is semantically immaculate and activated with fresh context only
  when orchestrator triage requires detailed execution refinement; it turns
  macro task refs into task-scoped detail docs and a detail packet, then
  returns normal outputs to orchestrator and macro drift back to planner.
- A deterministic loop runner that reads short-term workflow state and starts
  or advances execution loops without relying on one agent's conversation
  memory.
- An orchestrator role that decomposes a ready execution task into bounded
  work items, selects required execution agents, proposes mount topology for
  CCB scripts to validate/commit/reconcile, and coordinates normal
  worker/reviewer/detailer collaboration through `ask`; its pane may be
  resident for observability, but each task or round activation must be fresh.
- A dynamic agent lifecycle layer where the V1 default visible baseline is
  four panes, `ccb_frontdesk + ccb_task_detailer` in `ccb-user` and
  `ccb_planner + ccb_orchestrator` in `ccb-plan`, while execution and
  round-review roles can be loaded and released after idle/evidence gates
  through topology or lifecycle reconciliation. Visible baseline membership is
  not a context-retention grant: `task_detailer` and `orchestrator` still follow
  immaculate fresh-activation rules.
- Dynamic execution nodes, each defaulting to a flat `worker + checker`
  structure. More complex node-internal teams are deferred until the work item
  cannot be safely split by orchestrator.
- Checker as an independent quality gate that designs node-level verification,
  audits worker output against the original design, and rejects hidden
  fallback, degradation, scope shrinkage, or false success.
- Partial execution semantics where non-converged nodes freeze only their
  dependent branch while unrelated sibling work drains to completion.
- A round-level checker that verifies the whole loop round after node work is
  drained, using planner-defined verification contracts and the actual
  orchestrator dependency graph.
- An inner monitor layer that watches loop health, `ask`/callback status,
  node heartbeats, artifacts, timeouts, and communication anomalies.
- A clarification broker path that receives stage-level candidate questions
  from planner group, filters or defaults non-blocking items, and sends only
  curated user-facing question references to `frontdesk`.
- Scripted state transitions so agents can propose progress but CCB-owned
  commands write authority state.
- Script-owned plan packets and runtime lists: durable Markdown records live
  under plan-tree, while high-frequency loop state lives under `.ccb/runtime`
  and is updated only through CCB command surfaces.
- Context-purity boundaries that keep volatile execution detail out of `frontdesk`
  and out of long-term plan-tree files unless it becomes durable evidence,
  decision material, or a blocker.
- Team-spec style declarations for roles, handoffs, termination conditions,
  escalation conditions, and per-loop limits.
- Plan-tree synchronization only at durable boundaries such as accepted plans,
  decisions, evidence, blockers, and completion.

Out of scope:

- Making `frontdesk` a hidden central executor.
- Letting worker agents freely modify authoritative loop state without a
  scripted transition.
- Replacing ccbd, dispatcher, message bureau, or provider completion authority.
- Treating the inner monitor as a business-task decision maker.
- Keeping high-frequency loop events in committed plan-tree Markdown.
- Allowing unbounded agent chains, unbounded recovery loops, or unbounded
  dynamic node creation.
- Automatically publishing releases, deleting files, or performing destructive
  repair without the existing user-confirmation and release gates.

## Role Summary

| Role | Authority | Non-Authority |
| :--- | :--- | :--- |
| `frontdesk` group | User conversation, scope confirmation, final summary, escalation handling | Direct business implementation or internal loop micromanagement |
| planner | Macro planning artifacts, global Roadmap Graph, plan brief, serial/parallel branches, priorities, cross-lane dependencies, high-level acceptance, readiness recommendation, macro adjustment and integration review | Detail design body maintenance, detailed implementation packet maintenance, runtime worker lifecycle, direct detailer/worker dispatch, concurrent writing of another planner scope, or final authority over code correctness |
| `task_detailer` | Task-local refinement, task-scoped detail docs, source evidence, detail packet, stable summary backfill, task-local clarification | Roadmap/status authority, runtime dispatch, worker/reviewer control, or long-term user conversation |
| clarification broker | Candidate-question filtering, user-question artifact, answer normalization | Direct user conversation or execution-loop activation |
| planner stewardship mode / `ccb plan` scripts | Plan-tree consistency, short-term progress state, evidence linking, authoritative task/index/status writes through scripts | Business implementation, provider repair, daemon supervision, or bypassing script validation |
| loop runner | Deterministic state-machine execution and loop start/advance | Semantic product decisions |
| orchestrator | One activation owns coupled work slicing, dependencies, logical role assignment, worker packets, review/integration intent, and bounded semantic replanning | Long-term plan authority, concrete agent binding, physical `ask` submission, topology mutation, or runtime authority writes |
| execution node | Bounded `worker + checker` implementation and node-quality gate | Global task routing, hidden degradation, or durable plan mutation |
| round checker | Whole-round verification plan and execution | Product scope changes, implementation fixes, or authoritative state writes |
| inner monitor | Health observation, timeout/anomaly escalation, communication checks | Product judgment or arbitrary repair |

## Reading Path

Start with [topics/complete-workflow-design.md](topics/complete-workflow-design.md),
then read [topics/architecture.md](topics/architecture.md), then read
[topics/state-and-script-contract.md](topics/state-and-script-contract.md) and
[topics/plan-and-runtime-list-structure.md](topics/plan-and-runtime-list-structure.md),
then [topics/orchestrator-role-capability.md](topics/orchestrator-role-capability.md),
then [topics/semantic-orchestration-and-controller-boundary.md](topics/semantic-orchestration-and-controller-boundary.md),
then [topics/mount-topology-and-ask-first-orchestration.md](topics/mount-topology-and-ask-first-orchestration.md),
then [topics/runtime-workflow-graph-and-reconciler.md](topics/runtime-workflow-graph-and-reconciler.md)
for landed topology-controller context,
then [topics/orchestrator-rolepack-blueprint.md](topics/orchestrator-rolepack-blueprint.md),
then [topics/role-profiles-and-capacity-skill.md](topics/role-profiles-and-capacity-skill.md),
then [goals/orchestrator-dynamic-capacity-goal.md](goals/orchestrator-dynamic-capacity-goal.md),
then [topics/planner-role-design.md](topics/planner-role-design.md), then
[topics/parallel-roadmap-lanes-and-planner-authority.md](topics/parallel-roadmap-lanes-and-planner-authority.md), then
[topics/global-plan-tree-authority-and-cross-worktree-control.md](topics/global-plan-tree-authority-and-cross-worktree-control.md), then
[topics/global-plan-tree-storage-and-projection-migration.md](topics/global-plan-tree-storage-and-projection-migration.md), then
[topics/global-plan-tree-cross-worktree-acceptance-matrix.md](topics/global-plan-tree-cross-worktree-acceptance-matrix.md), then
[topics/planner-plan-tree-brief-and-detail-boundary.md](topics/planner-plan-tree-brief-and-detail-boundary.md), then
[topics/task-detailer-role-design.md](topics/task-detailer-role-design.md), then
[topics/plan-update-script-landing.md](topics/plan-update-script-landing.md),
then [goals/planner-plan-script-goal.md](goals/planner-plan-script-goal.md),
then [topics/clarification-flow.md](topics/clarification-flow.md), then read
[topics/execution-node-and-round-verification.md](topics/execution-node-and-round-verification.md),
then [topics/round-checker-and-planner-rehydration.md](topics/round-checker-and-planner-rehydration.md).
Use [roadmap.md](roadmap.md) for readiness and implementation sequencing.
