# Phase 1-6 Deployment Readiness P1 Dynamic Lifecycle Evidence

Date: 2026-07-08
Owner: talk2
Status: PASS

## Scope

This record covers P1 dynamic lifecycle validation for the post-acceptance
deployment-readiness lane. It is not a final deployment-readiness report and
does not claim production/default enablement.

## Real Project

- Root:
  `/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320`
- Project:
  `/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/p1-dynamic-lifecycle-real-provider-lab`
- Command wrapper: `/home/bfly/yunwei/ccb_source/ccb_test`
- Provider home policy: inherited system environment.
- Role store:
  `/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/roles`
- P1 B7:
  `/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/p1-dynamic-lifecycle-b7.md`
- Machine summary:
  `/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/p1-dynamic-lifecycle-summary.json`

## Result

P1 passed against a visible real opened project:

- Frontdesk handed off to planner, planner produced the L1-L4 route mix, and
  the auto-runner executed the chain without manual task creation after
  frontdesk entry.
- Three real direct-execution rounds reached `done/pass`: L1, L2, and L3
  post-detail execution.
- Each direct-execution round released dynamic coder/reviewer agents with
  `released_count=2`, `retained_count=0`, and observed topology `agents=[]`.
- L4 macro reached `replan_required`; L4 blocked reached `blocked`.
- Resident roles remained visible after dynamic release:
  `frontdesk`, `planner`, `orchestrator`, `task_detailer`, and
  `ccb_round_reviewer`.
- UI/sidebar/tmux evidence was captured under:
  `/home/bfly/yunwei/test_ccb2/deploy-p1-dynamic-lifecycle-talk2-20260708161320/ui-evidence`.
- Positive busy-retain was proven with real Codex dynamic agent
  `loop-p1busyreal-coder-1`: release while busy returned `retained_busy`
  with `runtime_state=busy`; release after terminal job completion returned
  `released` with `retained_count=0`.
- Explicit observer timeout was proven with real Codex dynamic agent
  `loop-p1timeoutreal-coder-1`: short `pend --watch` returned
  `command_status: failed` and `watch timed out`, then a normal watch reached
  terminal and cleanup released the dynamic node.

## Raw Evidence Paths

- Task authority:
  `p1-dynamic-lifecycle-real-provider-lab/docs/plantree/plans/phase6b-real-provider-l1-l4/tasks/index.json`
- Loop runtime evidence:
  `p1-dynamic-lifecycle-real-provider-lab/.ccb/runtime/loops/`
- UI evidence:
  `ui-evidence/ccb_test-ps-after-auto-runner.txt`
  and `ui-evidence/tmux-list-panes-after-auto-runner.txt`
- Busy retain evidence:
  `p1-busy-retain-real/topology-release-while-busy.json`
  and `p1-busy-retain-real/topology-release-after-idle.json`
- Timeout evidence:
  `p1-timeout-diagnostic-real/short-watch-timeout.stderr.txt`,
  `p1-timeout-diagnostic-real/final-watch.txt`, and
  `p1-timeout-diagnostic-real/topology-release-after-timeout-job.json`
- Post-B7 cleanup:
  `logs/post_b7_kill.stdout` and `logs/post_b7_ps.stdout`; cleanup returned
  `kill_status: ok`, and post-cleanup `ps` returned `ccbd_state: unmounted`
  with all resident roles stopped.

## Limits

- Persistent `.ccb/agents/loop-*` history directories remain as runtime
  records. Active `ps`, tmux panes, and observed topology files show no mounted
  dynamic residue after release.
- This closes P1 only. P2 frontdesk pressure, P3 module-level audit, P4 final
  deployment-readiness report, and P5 packaging/install/update gates remain
  open.
