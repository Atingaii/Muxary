# Phase 1-6 Deployment Readiness P2 Frontdesk Pressure Evidence

Date: 2026-07-08
Owner: talk2
Status: PASS

## Scope

This record covers P2 frontdesk pressure validation for the
post-acceptance deployment-readiness lane. It is not the final
deployment-readiness report and does not claim production/default enablement.

The covered shape is one visible, natural-language frontdesk macro-intake that
produces five frontdesk-derived route-mix tasks. It proves frontdesk intake and
handoff over multiple complexity levels in one operator-facing request. It does
not separately claim five independent user messages into frontdesk.

## Real Project

- Root:
  `/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920`
- Project:
  `/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920/p2-frontdesk-pressure-real-provider-lab`
- Command wrapper: `/home/bfly/yunwei/ccb_source/ccb_test`
- Provider home policy: inherited system environment.
- Role store:
  `/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920/roles`
- B7:
  `/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920/phase6b-real-provider-l1-l4-p2-frontdesk-pressure-talk2-20260708170920-b7.md`
- Rows:
  `/home/bfly/yunwei/test_ccb2/deploy-p2-frontdesk-pressure-talk2-20260708170920/rows/phase6b_l1_l4_p2-frontdesk-pressure-talk2-20260708170920_evidence_rows.jsonl`

## Result

P2 passed against a visible real opened project:

- Frontdesk was Codex-backed and received one natural-language operator
  request through `ccb_test ask frontdesk`.
- Frontdesk returned structured Intake Evidence and did not directly edit
  project artifacts, run tests, create B7 rows, clean runtime, or implement the
  requested work.
- Dispatcher auto-handoff created exactly one
  `.ccb/runtime/frontdesk-handoff/<job>.json` marker for the user-facing
  frontdesk job.
- `frontdesk forward-planner` submitted exactly one silence ask to planner for
  the intake activation. The additional frontdesk job in the log was a
  `reply_delivery` notification from planner completion back to frontdesk, not
  a second planner handoff.
- Planner produced one fenced `task-set.json` with five bounded tasks:
  L1 doc direct execution, L2 code/test direct execution, L3 `needs_detail`,
  L4 `macro_adjustment_request`, and L4 `blocked`.
- L1 and L2 reached `direct_execution -> done/pass` with dynamic
  coder/reviewer release `released_count=2`, `retained_count=0`, and no active
  dynamic agents in final `ps`.
- L3 reached `needs_detail -> detail_ready`; L4 macro reached
  `macro_adjustment_request -> replan_required`; L4 blocked reached
  `blocked -> blocked`.
- Valid non-success rows were classified as `valid_non_success`, not `pass`
  and not `system_failure`.
- Post-B7 cleanup returned the project to `ccbd_state: unmounted`.

## Raw Evidence Paths

- Frontdesk request:
  `frontdesk_l1_l4_entry_request.md`
- Frontdesk job log:
  `p2-frontdesk-pressure-real-provider-lab/.ccb/agents/frontdesk/jobs.jsonl`
- Handoff marker:
  `p2-frontdesk-pressure-real-provider-lab/.ccb/runtime/frontdesk-handoff/job_fe83d6513744.json`
- Frontdesk activation:
  `p2-frontdesk-pressure-real-provider-lab/.ccb/runtime/loops/activations/act-frontdesk-job_fe83d6513744.json`
- Planner reply artifact:
  `p2-frontdesk-pressure-real-provider-lab/.ccb/ccbd/artifacts/text/completion-reply/job_ac0779f4ab23-art_d222edf67bdc4729.txt`
- Task authority:
  `p2-frontdesk-pressure-real-provider-lab/docs/plantree/plans/phase6b-real-provider-l1-l4/tasks/index.json`
- Direct-execution round evidence:
  `p2-frontdesk-pressure-real-provider-lab/.ccb/runtime/loops/lp2ee7de/round.json`
  and
  `p2-frontdesk-pressure-real-provider-lab/.ccb/runtime/loops/lp6cbec9/round.json`
- Dynamic release observed topology:
  `p2-frontdesk-pressure-real-provider-lab/.ccb/runtime/loops/lp2ee7de/agent_mount_topology.observed.json`
  and
  `p2-frontdesk-pressure-real-provider-lab/.ccb/runtime/loops/lp6cbec9/agent_mount_topology.observed.json`
- Cleanup evidence:
  `logs/p2-frontdesk-pressure-talk2-20260708170920__cleanup_after_b7.stdout`

## Limits

- Persistent `.ccb/agents/loop-*` and `.ccb/runtime/agents/loop-*` directories
  remain as historical runtime records. Active `ps` and observed topology show
  no mounted dynamic residue after release.
- This closes the P2 macro-intake pressure lane. A stricter future P2-B lane
  could run five independent frontdesk user messages if product acceptance
  later requires that exact shape.
- P3 module-level audit, P4 final deployment-readiness report, and P5
  packaging/install/update gates remain open.
