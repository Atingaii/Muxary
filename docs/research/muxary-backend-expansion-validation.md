# Muxary backend expansion validation

Date: 2026-11-11. Raw local evidence is retained under `~/.local/share/muxary-dev/expansion-review/`. This report distinguishes the complete-suite snapshot, later affected verification, observed failures, and untested limits.

## Frozen complete suite

- Original command/environment: `backend-full-context.json`; full original output: `backend-full.log`.
- 8,662 collected = **8,579 passed, 82 skipped, 1 failed**, 2,317.99 seconds; process exit **1**.
- The prior full run was 8,374 passed / 82 skipped / 11 failed. Its original log SHA256 remains unchanged. The old 11 failure node IDs are recorded prospectively in the start context. All 11 are absent from this run's failure summary; an explicit post-run node-by-node recheck passed **11/11 in 48.09s**, saved separately in `prior-failures-recheck.log`.
- New observed failure relative to that baseline: `test/test_v2_phase2_entrypoint.py::test_ccb_long_running_job_keeps_heartbeat_and_doctor_healthy`. This is not one of the old 11. Do not label this complete suite green.
- Shortening `TMPDIR` and unsetting the ambient `CCB_PYTHON_BIN` are environment corrections, not code fixes. No assertion, deadline, provider delay, failure log, or frozen evidence was weakened or deleted.
- The complete-suite process started before Q9 project-open changes. It does NOT certify the final Q9 patch. `backend-full-after-context.json` lists exact before/after SHA256 and added tests. Changes after start: `lib/workbench/service.py`, `lib/workbench/cli.py`, and the CLI forwarding test matrix. Added tests: project-open and canvas provenance. No Python source was removed.

## Frozen-source differences

| Source | SHA256 at complete-suite start | SHA256 at final affected verification |
| --- | --- | --- |
| `lib/workbench/service.py` | `d8bcdf04b4d69dbe065a32cd5ab49e1736cc8d20ae83b2261550a7471446b3fb` | `a57c84ba211e1b5fdbd75f6f57b57218ae997efdc98f2d2afb07a289eebc3309` |
| `lib/workbench/cli.py` | `cfb1a48597eab894967ff37d909d875692be7e0ae5bd30754b02fba1466559d5` | `a3394989ac05213f84dd48a76384fd8a25365f88ff8bef6c3fec31b24b702c67` |
| `test/test_muxary_cli.py` | `ba3f86076c38a9a14331e131939305e58127cc5aac49e4df203223b07f93752d` | `11d652facc108b22dd48b4fbf9c2058f44445f1a28dbca9ab489a2763e258edf` |

New after initial collection: `test/test_workbench_project_open.py` (`fa10d5caa50265ef8983464b7d70a062e0ede84d011e287e82b6ceca1fc3f63a`) and `test/test_muxary_canvas_ui_provenance.py` (`4c3bde309f6bd2c28c1de010df11db46a3da2b75885faca32c6e14edc2fb9992`). The manifest covers `ccb.py`, `lib/**/*.py`, and `test/**/*.py`; unlisted files in that scope were unchanged.

## Previous eleven failures: explicit recheck

| File | Previously failing cases | Final dedicated result |
| --- | --- | --- |
| `test_install_watchdog_optional.py` | managed venv reuse; legacy-pip refresh | 2 passed |
| `test_v2_ccbd_start_matrix.py` | restart dead daemon; forced accelerator reap; forced corrupt-owner recovery; normal-kill corrupt-owner preservation | 4 passed |
| `test_v2_config_loader.py` | runtime-registry provider priority | 1 passed |
| `test_v2_execution_registry.py` | core-only registry | 1 passed |
| `test_v2_provider_core_registry.py` | default session bindings; default runtime launcher map | 2 passed |
| `test_v2_runtime_launch.py` | Gemini user-session transport without runtime leaks | 1 passed |

These successes do not erase the newly observed failure below. The original complete log and the previous eleven-failure log remain intact.

## Unchanged heartbeat test: failure timing investigation

- The original test file SHA256 is unchanged from the full-suite start: `b3a10415e38df29e0bd81c7f7e8fd859e731450fa8161a4455952f6ad7be9f13`.
- Original full run failed. First unchanged isolated rerun also failed (13.89s): `heartbeat-rerun-01.log`. Second rerun with an external observational wrapper around `_run_ccb` failed too (13.31s): `heartbeat-rerun-timing.log`. The wrapper returns the original subprocess result unchanged; its source is `heartbeat_timing_plugin.py`.
- Actual task/attempt records have been copied without rewriting under `heartbeat-fixture-evidence/`; per-command wallclock and elapsed measurements are `heartbeat-command-timing.jsonl`.
- Timing run, UTC: fake execution running at `10:59:34.872725`, completed at `10:59:38.893307`, duration 4.020582s. The fake directive is still `latency_ms=4000`.
- `pend` took 1.219s and reported running. `doctor` started `10:59:36.174288`, took 1.639s, and reported healthy/active=1/recoverable=1. The first subsequent `ping ccbd` started `10:59:37.813337`, took 1.256s, and reported healthy/active=0/recoverable=0. The task genuinely completed before this ping returned (`10:59:39.069152`). A second ping again reported active=0.
- Evidence supports an invalid timing assumption: a four-second task cannot be assumed to remain active across sequential Python CLI launches. The observed active=0 is consistent with the actual completed record, not evidence that heartbeat maintenance failed. This is a bounded diagnosis, not proof that every heartbeat/lifecycle property works or that no performance regression exists. No core performance attribution was manufactured; the test remains failed and unchanged.
- In the frozen full run the same fake attempt ran at `10:47:35.391902` and completed at `10:47:39.414658`. The original full run did not prospectively record per-command wallclock, so the precise command timings above are from the explicitly labeled follow-up run only.

## Q9 affected suite before the final fresh-candidate repair

- `project-open-release.log`: **172 passed, 54.16s**, exit 0. Includes the expanded CLI forwarding matrix and final registry-generation patch.
- Source SHA256: service `a57c84ba211e1b5fdbd75f6f57b57218ae997efdc98f2d2afb07a289eebc3309`; CLI `a3394989ac05213f84dd48a76384fd8a25365f88ff8bef6c3fec31b24b702c67`.
- Covered: real authenticated HTTP project-open -> existing `ccb --safe` with independent CLI stubs -> fresh mounted ProjectView -> new-project submit -> provider control -> native terminal-handle issuance. Reopening a live project did not invoke the launcher again. Stubs are not actual model/API integration claims.
- Owner identity: managed worktree, child directory, and symlink aliases select/start their original CCB owner root, not a new project or a live Agent cwd. Marker/schema/project-id/path mismatch and nonregular/symlink/oversize markers fail closed. Both Web open and `muxary --project` use the same pure-read identity seam.
- Registry: both Workbench and the existing MobileGateway receive the updated immutable registry snapshot. A controlled old-discovery-late-result race was first red (new/view404), then green under a request-generation commit guard. Discovery/start/RPC do not hold the registry lock. Independent reviewer evidence is in `q9-adversarial/registry-race-red.log` and `registry-race-green.log`.
- The first affected run had one newly authored test bug: counting `x` in the entire capped-output string also counted the `x` in the Muxary truncation notice. That unfavorable output remains in `project-open-affected.log`. The corrected test asserts the exact full expected output, including notice, rather than weakening the cap. Later runs: 159 passed before final race regression; 172 passed on the release patch.

## Fresh-candidate repair and 175-case affected suite

- A second controlled ordering exposed a distinct bug in the request-generation guard: open's post-start discovery had computed the correct new registry, but a later read began discovery and remained pending. The guard suppressed open's candidate publication; open then consulted the old global snapshot and returned a false 503. This is not the earlier late-old-result overwrite ordering.
- Prospective red: `q9-adversarial/fresh-candidate-red.log`, **2 failed in 0.90s**, with the later read's candidate separately containing or excluding the opened project. Both cases returned 503 on the previous production source. The same two tests plus the old late-old-discovery regression then passed **3/3 in 0.97s** (`fresh-candidate-green.log`).
- Repair: `_refresh_registry` returns its own completed candidate even if a newer request prevents global publication. Open checks the requested root and actual identity/mount against that candidate. Only after successful confirmation, a short registry lock merges the confirmed entry into the current snapshot and advances the generation, fencing all discovery already in flight. Discovery, startup, and RPC remain outside this lock. A separate test confirms that a newly discovered unrelated project is preserved by the merge.
- Configured affected suite at this stage: **175 passed in 53.08s**, exit **0**, `q9-adversarial/fresh-candidate-configured.log`. This is the previous 172 cases plus the three new regressions. No existing timeout, provider delay, assertion, or CCB core/cache behavior changed.
- Source SHA256 at this stage: `lib/workbench/service.py` = `47dab3beb8e74de067f53ad5c22e229b35a843451a7f6172c7f30ff69137da8e`; `test/test_workbench_project_open.py` = `dc15663f9f21d770f2e5bbee2170b4aa2c63b3df9d3b14da956df54c45800c25`. CLI remains `a3394989ac05213f84dd48a76384fd8a25365f88ff8bef6c3fec31b24b702c67`. The earlier complete suite remains a different frozen snapshot and still has its recorded failure.
- An initial follow-up affected run was **174 passed / 1 failed in 45.44s** (`fresh-candidate-affected.log`). Its real-CCB test could not launch a compatible interpreter inside the fixture's isolated HOME because this invocation omitted `CCB_PYTHON` and the managed-venv PATH prefix. An external observational wrapper, without changing the production function's result, captured launcher exit **127**, no stdout, and the missing-compatible-Python diagnostic (`fresh-candidate-launch-diagnostic.log`; unchanged test failed again in 1.85s). The final run restored the previously recorded complete-suite environment: explicit original-venv `CCB_PYTHON`, original-venv PATH prefix, unset `CCB_PYTHON_BIN`, `TMPDIR=/tmp`, and `PYTHONDONTWRITEBYTECODE=1`. This is a validation-environment correction, not a product-code fix. Both unfavorable logs remain intact.

## Final preflight published-project reuse repair

- Independent adversarial review exposed the converse preflight ordering: an opening request captures a registry without the target and pauses; another read publishes a registry containing the already-live target; then the old preflight returns its own superseded candidate. Using only that candidate caused a redundant launcher invocation, even though the published target was already mounted. Reviewer reproduction is `q9-adversarial/preflight-candidate-offline.py` with its frozen `preflight-candidate-offline-red.log`.
- A new single-ordering repository test first reproduced **1 failure in 0.84s**: HTTP dispatch returned 200 but the launcher call list incorrectly had one entry (`preflight-red.log`). Before the fix, the test explicitly verified that the target was published and `_project_is_ready` returned true before releasing the old preflight. It therefore tests duplicate invocation, not merely eventual project visibility.
- Minimal repair: pre-start checks prefer a matching current published entry; only when none exists do they use the request's discovery candidate. An unreachable registered entry still fails closed rather than automatically restarting. The post-start candidate confirmation, confirmed-entry merge/fence, fixed safe launcher, and existing timeouts remain unchanged. No scheduler, retry, waiting layer, or core cache modification was introduced. This ordering guarantee is not a claim to atomically coordinate arbitrary external project startup/shutdown processes.
- The new test plus the previous four controlled race cases passed **5/5 in 0.84s** (`preflight-green.log`). Final configured affected suite: **176 passed in 52.53s**, exit **0**, `q9-adversarial/preflight-configured.log`, using exactly the original managed-venv environment described above.
- The independent reviewer reran the same frozen reproducer without editing production or tests: `preflight-candidate-offline-green.log` confirms the newer read had published a ready target, open returned 200, and launcher calls were zero on final service SHA `a6ae5de2...`.
- Final SHA256: service `a6ae5de244df2099ad91cf7abd52d48aa884bb2485663b924e3f3f6195d43ebe`; CLI `a3394989ac05213f84dd48a76384fd8a25365f88ff8bef6c3fec31b24b702c67`; project-open tests `69949d689f8c09cd2ed5f8a633a3d2054e67b02310e400c617221c7bdaacd5a1`. All prior red/failure logs remain retained. These results do not reclassify the original complete suite or attribute the browser failure below.

## Browser attempt03: bounded diagnosis, not an attributed repair

- The parent's independent browser attempt03 observed project-open 503 after an explicit fixture-only `ccb kill -f`, while the project daemon/socket did restart. Its original failure output remains `q9-browser-acceptance-03/result.json`; this follow-up did not repeat its POST or stop its BFF/Agents.
- Read-only evidence: the opened project's startup report was generated at `2026-11-11T11:06:45.011253Z`, status `ok`, `daemon_started:true`, daemon generation 3. The browser attempt finished at `11:06:45.338Z`. A subsequent authenticated read returned 200 with mounted generation/namespace 3. Cookies and bootstrap credentials were not printed.
- `CcbdClient` reconnects for each request and does not cache RPC results; it only binds endpoint methods. The ccbd `ProjectViewService` does have a server-side cached response, keyed by dispatcher/drain revisions and a default work/idle TTL of 1s/5s. The public client payload and handler accept `schema_version` only, with no refresh/bypass flag. The existing start handler does not explicitly invalidate this cache. These are code facts, not proof that a cached unmounted view caused this browser 503.
- Existing attempt03 artifacts did not capture the POST response body or the internal exception. Therefore neither the independently reproduced registry ordering nor the ProjectView cache can be conclusively assigned as this attempt's cause. The controlled registry defect is repaired; this report does not claim that it has proven or repaired the exact browser failure. No CCB cache, provider, or lifecycle core was changed for this investigation.

## Project-open limits

- API: authenticated same-origin `POST /api/projects/open {path}`. Success is `200 {schema_version:1,project_id,root,status:'ready'}`. No command, environment, force, restart, worktree delete/merge, or hot cwd switch is accepted.
- Fixed `ccb --safe`, `CCB_NO_ATTACH=1`, no shell; launcher timeout 45s. File-backed stdout/stderr avoids descendant-held PIPE readers after timeout, and displayed output is capped. A real disposable launcher/descendant test confirmed bounded timeout without killing its descendant. Only that exact test descendant was then cleaned up by its owning test.
- Concurrent opens receive 409 without blocking ordinary HTTP operations. A successful launcher exit alone is insufficient: refreshed registry and mounted, matching project id/root are required.
- Failed/timeout results explicitly have outcome_unknown/refresh_required/retry_safe:false. No automatic retry, rollback, force/restart, or Agent kill. Within one server instance, the canonical-root uncertainty set prevents a second unconfirmed launch of the same project; a later genuine live confirmation can recover it. This in-memory guard is not persistent across Web server restarts. The frontend must preserve the unknown outcome and require read-only confirmation.
- Missing opener is 503 with outcome_unknown:false/retry_safe:true (no launch occurred). The test fixture must explicitly provide an opener to allow project lifecycle actions.

## Workspace/diff limits retained

- Agent workspace is a fresh runtime-declared/startup directory with persisted ownership evidence, not a claim about an arbitrary running shell's current cwd, perpetual isolation, or per-Agent change authorship. Shared directories are not labeled read-only. Directory diff is not Agent attribution.
- Existing no-ext-diff/no-textconv, output caps, and five-second Git deadlines are retained. `filter.clean` can still be invoked by local Git despite those options; the reproduced limitation is retained in `git-clean-filter-boundary.md`. `filter.process` was not separately exercised. Do not claim that all Git plugins or repository-controlled commands are disabled.

## Cleanup

Exact task-owned process/project/basetemp inventory and per-project CCB cleanup receipts are saved separately. Original HOME CCB/Agent processes and the parent's browser fixture are outside the allowlist and are not cleanup targets. Original logs, contexts, timing source, copied failure evidence, and reusable dependencies are retained.

The exact inventory found 96 task-owned processes across 18 temporary project roots. Existing CCB `kill -f` was used only on those enumerated roots; after enabling the source checkout's explicit diagnostic gate, all 18 cleanup commands returned zero. The initial source-gate refusals remain recorded rather than deleted. A subsequent `/proc` recheck found zero processes under the seven enumerated task basetemps. Only those seven basetemps were then removed; all logs, frozen manifests, original failure outputs, and copied task/attempt records remain. Cleanup receipts are `backend-cleanup-inventory.json`, `backend-cleanup-commands.json`, `backend-cleanup-diagnostics-commands.json`, `backend-cleanup-postcheck.json`, and `backend-cleanup-result.json`.

The fresh-candidate follow-up separately inventoried and removed only its three dedicated `/tmp/mxw-5czq10`, `/tmp/mxy-jJUjk3`, and `/tmp/mxz-1bz1EC` basetemps, after finding zero processes owned by those paths. Its two controlled-test directories (`/tmp/pytest-of-lucentzhou/pytest-148` and `pytest-149`) were also individually checked for exact expected test children and no fixture processes, then removed. Receipts are `q9-adversarial/fresh-candidate[-controlled]-cleanup-{inventory,result}.json`. Parent browser fixture PID 621139 and all original HOME Agent processes remained outside this cleanup scope. All raw red/green/failure/configured evidence remains available.

The final preflight follow-up similarly inventoried `/tmp/mxp-REtbMn`, `/tmp/mxs-87TQAO`, and `/tmp/mxv-spQoV3`, found no path-owned processes after the test fixture cleanup, then removed only these three basetemps. Receipts are `q9-adversarial/preflight-cleanup-{inventory,result}.json`. No parent browser fixture lifecycle action was performed by this subtask, and no task-owned fixture remains pending cleanup.
