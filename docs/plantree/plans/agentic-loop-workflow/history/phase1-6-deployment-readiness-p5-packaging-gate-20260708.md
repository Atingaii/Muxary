# Phase 1-6 Deployment Readiness P5 Packaging Gate

Date: 2026-07-08
Owner: talk2
Status: PASS_FOR_SOURCE_PACKAGING_GATE / RELEASE_NOT_PUBLISHED / PRODUCTION_DEFAULT_NOT_ENABLED

## Scope

This record covers P5 source hygiene, wrapper, packaging, and install-smoke
checks after the P4 deployment-readiness report. It does not publish a
release, install into the system CCB environment, switch the main checkout
back to `main`, or enable production/default workflow behavior.

The runtime validation standard remains:

- source validation uses `/home/bfly/yunwei/ccb_source/ccb_test`;
- source runtime commands run from `/home/bfly/yunwei/test_ccb2`;
- deterministic source-wrapper smoke may use isolated source homes;
- real-provider validation must inherit the system provider environment;
- global role store and runtime test roots must not be mixed into source
  packaging.

## Result

P5 source packaging gate passes for the current source tree after two source
repairs found by this gate:

1. Role command-surface enforcement blocked deterministic `ccb_test` fake
   provider smoke for `agentroles.ccb_frontdesk`.
2. Deterministic fake worker replies did not create a declared workspace file,
   so the newer direct-execution project-root promotion guard correctly
   rejected the pass as `isolated_workspace_no_project_root_effect`.

Both were treated as blockers and fixed without weakening production
authority:

- `fake` is allowed through hard role command-surface checks only when
  `CCB_TEST_ENTRYPOINT=1`; normal runtime still rejects unsupported providers.
- The workflow smoke contract declares
  `allowed_change_paths: workflow_smoke_output.txt`.
- The fake worker writes that file in the runtime workspace using
  `ProviderRuntimeContext.workspace_path`, so the smoke now exercises the real
  isolated-workspace promotion path before reviewer and round-reviewer pass.

## Source Changes From P5

Code and tests touched directly by P5:

- `lib/cli/services/role_command_policy.py`
- `lib/provider_execution/fake.py`
- `scripts/workflow_closure_smoke.py`
- `test/test_provider_hook_settings.py`
- `test/test_provider_execution_fake_runtime.py`

Post-gate harness hardening touched:

- `scripts/phase6b_l1_l4_frontdesk_runner.py`
- `test/test_phase6b_l1_l4_frontdesk_runner.py`

Current-source preview release packaging hardening touched:

- `scripts/build_release.py`
- `test/test_build_linux_release_script.py`

The wider worktree still contains earlier P0-P4 and workflow source changes.
This P5 record does not stage, commit, revert, or publish them.

## Verification

Wrapper and source smoke:

```text
/home/bfly/yunwei/ccb_source/ccb_test --diagnose
allowed_source_test_project: yes

HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
python /home/bfly/yunwei/ccb_source/scripts/workflow_closure_smoke.py \
  --test-root /home/bfly/yunwei/test_ccb2 \
  --ccb-test /home/bfly/yunwei/ccb_source/ccb_test \
  --project-name p5-source-wrapper-smoke-20260708 \
  --provider fake \
  --reset \
  --run \
  --json
```

Smoke result:

```text
workflow_smoke_status: ok
final_status: done
round_result: pass
round_result_source: round_reviewer_reply
ask_reachability: true
mount_topology_ready: true
topology_dispatch_absent: true
released_count: 2
retained_count: 0
dynamic_agents_absent_from_ps: true
```

Python checks:

```text
python -m py_compile \
  lib/cli/services/role_command_policy.py \
  lib/provider_execution/fake.py \
  scripts/workflow_closure_smoke.py \
  test/test_provider_hook_settings.py \
  test/test_provider_execution_fake_runtime.py \
  test/test_workflow_closure_smoke_script.py

python -m pytest -q \
  test/test_provider_execution_fake_runtime.py \
  test/test_provider_hook_settings.py \
  test/test_workflow_closure_smoke_script.py \
  test/test_orchestrator_rolepack.py::test_frontdesk_rolepack_declares_hard_forward_planner_command_surface
```

Result:

```text
64 passed
```

Broad source bundle:

```text
python -m pytest -q \
  test/test_loop_capacity_cli.py \
  test/test_phase6b_l1_l4_frontdesk_runner.py \
  test/test_v2_phase2_entrypoint.py \
  test/test_v2_ask_service.py \
  test/test_loop_topology_cli.py \
  test/test_plan_tasks_cli.py
```

Result:

```text
322 passed in 456.19s
```

Packaging and install smoke:

```text
npm pack --dry-run
```

Result:

```text
@seemseam/ccb@8.0.14
package size: 43.3 kB
unpacked size: 165.3 kB
total files: 20
```

Local project and global-prefix install smoke under `/home/bfly/yunwei/test_ccb2`:

```text
CCB_NPM_SKIP_DOWNLOAD=1 npm install --prefix \
  /home/bfly/yunwei/test_ccb2/p5-install-smoke-talk2-20260708205754/prefix \
  /home/bfly/yunwei/test_ccb2/p5-install-smoke-talk2-20260708205754/pack/seemseam-ccb-8.0.14.tgz

CCB_NPM_SKIP_DOWNLOAD=1 npm install -g --prefix \
  /home/bfly/yunwei/test_ccb2/p5-install-smoke-talk2-20260708205754/global-prefix \
  /home/bfly/yunwei/test_ccb2/p5-install-smoke-talk2-20260708205754/pack/seemseam-ccb-8.0.14.tgz
```

Result:

```json
{
  "status": "ok",
  "root": "/home/bfly/yunwei/test_ccb2/p5-install-smoke-talk2-20260708205754",
  "package_version": "8.0.14",
  "project_install_bin_links": {
    "ccb": true,
    "ask": true,
    "autonew": true,
    "ctx-transfer": true
  },
  "global_prefix_install_bin_links": {
    "ccb": true,
    "ask": true,
    "autonew": true,
    "ctx-transfer": true
  },
  "release_vendor_present": false,
  "skip_download_expected": true
}
```

Project installs place command links under `node_modules/.bin`; global-prefix
installs place them under the selected prefix `bin`. Both were verified. This
is still a wrapper/package-shape smoke because `CCB_NPM_SKIP_DOWNLOAD=1`
intentionally skips release-artifact download.

Post-gate real-provider automatic frontdesk stress:

```text
root: /home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921
B7: /home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/phase6b-real-provider-l1-l4-deploy-stress-talk2-selfrun-20260708205921-b7.md
rows: /home/bfly/yunwei/test_ccb2/deploy-stress-talk2-selfrun-20260708205921/rows/phase6b_l1_l4_deploy-stress-talk2-selfrun-20260708205921_evidence_rows.jsonl
```

Result:

```text
Status: pass
rows: 5
claimable_row: true for all rows
L1/L2: direct_execution -> done/pass
L3: needs_detail -> detail_ready
L4 macro: macro_adjustment_request -> replan_required
L4 blocked: blocked -> blocked
L1/L2 release: released_count=2, retained_count=0, runtime_residue=false
post-B7 cleanup: exit 0, no target-project process residue in follow-up ps
```

The run also confirmed the preferred production-facing shape: one frontdesk
entry can hand off to planner and the auto-runner can complete the five-task
route mix without manual task advancement.

Real npm latest install smoke:

```text
root: /home/bfly/yunwei/test_ccb2/p5-real-npm-install-talk2-20260708212535
command: npm install --prefix <root>/prefix @seemseam/ccb
installed package: @seemseam/ccb@8.0.19
ccb --print-version: v8.0.19
```

Result:

```json
{
  "status": "ok",
  "bin_links": {
    "ccb": true,
    "ask": true,
    "autonew": true,
    "ctx-transfer": true
  },
  "release_vendor_present": true,
  "release_vendor_entries": [
    "ccb-linux-x86_64",
    "ccb-linux-x86_64.tar.gz"
  ]
}
```

This proves the currently published npm package can install and fetch a real
release artifact in an isolated test prefix. It does not prove the current
dirty source tree is published: the registry latest is `8.0.19`, while the
current checkout `package.json` still says `8.0.14`.

Current-source preview release/install smoke:

```text
root: /home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205
build command: python3 /home/bfly/yunwei/ccb_source/scripts/build_linux_release.py --allow-dirty --output-dir <root>/dist
artifact: <root>/dist/ccb-linux-x86_64.tar.gz
artifact size: 32M
artifact sha256: 4454560c3e846cbc475fa05ab289e47e0cd7417a19f5cb18f0151ebcdee4af23
result json: <root>/current-source-release-install-result.json
```

Result:

```json
{
  "status": "ok",
  "version": "8.0.14",
  "ccb_print_version": "v8.0.14",
  "install_mode": "release",
  "source_kind": "preview",
  "channel": "preview",
  "bin_links": {
    "ccb": true,
    "ask": true,
    "autonew": true,
    "ctx-transfer": true
  },
  "release_helpers": {
    "ccb-agent-sidebar": true,
    "ccb-rs-helper": true,
    "ccb-runtime-accelerator": true
  },
  "forbidden_mobile_build_entries_present": false
}
```

This smoke proves the current dirty source tree can build a local Linux
release-shaped preview artifact and install it through `install.sh` into an
isolated prefix. It does not publish npm, create a GitHub release, or claim the
dirty source as an official stable artifact.

Packaging blocker found and fixed during this smoke:

- Failing-before evidence: `build_linux_release.py --allow-dirty` copied
  generated Flutter/Gradle mobile output into the release stage. The stage grew
  to about `11G`, and the partially written tarball reached about `1.3G` before
  the build was interrupted during `create_tarball()`.
- Fix: `scripts/build_release.py` now excludes generated mobile/frontend
  build caches such as `build`, `.dart_tool`, `.gradle`, `.idea`,
  `node_modules`, and `dist-mobile`.
- Regression: `test_copy_repo_tree_excludes_runtime_state` now asserts those
  generated paths are absent from the release copy.

Installed-preview workflow closure smoke:

```text
project root: /home/bfly/yunwei/test_ccb2/p5-installed-preview-smoke-talk2-202607082220
installed source: /home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/install-prefix
command source: <install-prefix>/scripts/workflow_closure_smoke.py
ccb_test: <install-prefix>/ccb_test
result: /home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205/installed-preview-workflow-smoke-result.json
```

Result:

```json
{
  "workflow_smoke_status": "ok",
  "provider": "fake",
  "final_status": "done",
  "round_result": "pass",
  "round_result_source": "round_reviewer_reply",
  "released_count": 2,
  "retained_count": 0,
  "kill_returncode": 0
}
```

The installed-preview workflow smoke used the release artifact's own
`scripts/workflow_closure_smoke.py` and `ccb_test`, not the source checkout
script. It verifies the installed current-source preview artifact can run the
deterministic project workflow path under `/home/bfly/yunwei/test_ccb2`, mount
dynamic workers, import a script-owned round pass, release both dynamic agents,
and unmount the project without target-process residue.

Repeatability real-provider fullflow:

```text
root: /home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126
B7: /home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126/phase6b-real-provider-l1-l4-deploy-repeatability-talk2-202607082126-b7.md
summary: /home/bfly/yunwei/test_ccb2/deploy-repeatability-talk2-202607082126/repeatability-summary.json
```

Result:

```text
Status: pass
rows: 5
claimable rows: 5
classifications: 2 pass, 3 valid_non_success
L1/L2 dynamic release: released_count=2, retained_count=0,
  dynamic_unload_ok=true, runtime_residue=false
post-cleanup process scan: no target-project process residue
```

This run was started after the package/install checks and used
`/home/bfly/yunwei/ccb_source/ccb_test` from `/home/bfly/yunwei/test_ccb2`,
with inherited system provider home and root-local role store. It verifies
that the automatic frontdesk -> planner -> auto-runner route-mix path is
repeatable for the current source tree.

Harness hardening after the stress run:

- Bug reproduced: manual `start-task` launched while the frontdesk auto-runner
  was still active could block on `auto-runner.lock` even if the target task
  was already completed by the automatic flow.
- Fix: `start_task` now observes an existing task before waiting for
  auto-runner quiet, and returns immediately for already running or terminal
  tasks. It still waits before creating or activating new task authority.
- Regression:
  `test_start_task_observes_already_completed_task_before_waiting_for_auto_runner`.

Whitespace:

```text
git diff --check
```

Result: clean.

## Worktree And Packaging State

- Source checkout:
  `/home/bfly/yunwei/ccb_source`
- Current branch:
  `workflow/agentic-loop-topology`
- Current HEAD at inventory:
  `f1bb7fd4`
- P5 did not switch branches or mutate the main GitHub checkout.
- P5 did not publish npm, create a GitHub release, or install source changes
  into the global/system CCB environment.
- P5 did build and install a local current-source Linux preview release artifact
  under `/home/bfly/yunwei/test_ccb2/p5-current-source-release-talk2-202607082205`.
- A real npm latest install smoke passed for published `@seemseam/ccb@8.0.19`,
  but that package is not the current dirty checkout.
- Runtime test roots remain under `/home/bfly/yunwei/test_ccb2` and are not
  source packaging inputs.

The npm package currently packages wrapper files and localized readmes. It
does not package the Python source tree directly; the wrapper install path
expects a matching GitHub release artifact. P5 verified package shape,
skip-download installs, public npm/latest release download, and a local
current-source preview release/install path. It has not verified an official
current-source GitHub release asset because no such package-owner release was
created.

## Remaining Release Boundary

P5 is complete for source packaging preflight. Production/default enablement
still requires an explicit package-owner release step if the project is to be
published or installed from a real release artifact:

- decide whether the current dirty source tree is staged into one release
  branch/commit or split into follow-up commits;
- resolve the version drift between current source `8.0.14` and npm latest
  `8.0.19`;
- build or verify the matching official GitHub release archive for the chosen
  version;
- run an install/update smoke against the actual release artifact if publishing
  through npm;
- only then consider production/default enablement policy.

## Final P5 Decision

The current source tree passes P5 source packaging gate checks and is ready
for package-owner staging/release decisions.

It is not published, not globally installed, and not production/default
enabled.
