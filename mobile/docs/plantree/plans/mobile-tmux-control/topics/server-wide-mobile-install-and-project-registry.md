# Server-Wide Mobile Install And Project Registry

Date: 2026-06-24
Status: Server-wide source/app project listing and routing are the accepted
foundation. Chat acceptance is reopened by the 2026-06-25 agent-native
correction: any prior send/reply evidence using the mobile ask/message route
must be rerun through selected-pane/native input before it can close default
chat behavior. Physical Tailnet/relay validation remains later work.

## Purpose

Make CCB Mobile a server-level capability instead of a per-project demo or
per-project gateway.

The target user command is:

```bash
ccb install mobile
```

After that command succeeds, the phone should pair with the server once, see
all CCB projects currently mounted on that server, open any project, switch
agents inside that project, send ordinary chat through the selected
agent-native input path, receive provider-native replies/transcript, upload
attachments, and download backend-generated artifacts. The App first page must
not be a fake `demo` project when a paired server gateway is available.

## Current Mismatch

The current source gateway is still a current-project sidecar:

- `MobileGatewayService.projects_payload()` returns exactly one project:
  `self._project_id`.
- `project_view_payload(project_id)` rejects any id that is not the serve-time
  project id.
- `prepare_mobile_gateway()` constructs a gateway from the current CLI
  context's `project_id`, `project_root`, `ccbd_socket_path`, and
  `ccbd_mobile_dir`.

The current app first page is also still current-ProjectView driven:

- `ProjectHomeScreen` initializes `_activeProjectId = 'proj-demo'`.
- startup calls `getProjectView(_activeProjectId)` before any
  `listProjects()`.
- `ProjectListScaffold` renders `itemCount: 1` from the current
  `CcbProjectView`.

That architecture can prove one real project, but it cannot satisfy "show all
server CCB projects" because neither side has a host-level project registry.

## Target Experience

### Install / Activation

`ccb install mobile` is idempotent and server-scoped:

1. Installs or repairs the optional mobile bundle and dependencies.
2. Starts or refreshes a server-level, loopback-only CCB Mobile gateway.
3. Detects available route providers:
   - local LAN/manual URL;
   - Tailnet via Tailscale Serve when available;
   - later CCB Relay by default for non-LAN remote access;
   - Cloudflare remains an advanced route.
4. Prints or displays one pairing QR for the server gateway.
5. Does not require running from a specific CCB project root.
6. Does not default to `0.0.0.0`, Funnel, stored OAuth/admin tokens, or
   automatic tailnet ACL/grant modification.

### Phone First Page

After pairing:

1. App activates paired gateway mode automatically when a valid server profile
   exists.
2. App calls `GET /v1/projects` on the server gateway.
3. App shows all mounted/reachable CCB projects with display name, root,
   health, and activity metadata.
4. Tapping a project calls `GET /v1/projects/{project_id}/view`.
5. All following operations carry the selected `project_id`.
6. Project switching clears stale selected-agent/opened-project state and
   never silently falls back to `demo`.

## Non-Goals

- Do not list arbitrary tmux sessions.
- Do not list filesystem directories that are not CCB projects.
- Do not expose host-local socket paths, tmux session names, runtime roots, or
  provider transcripts in `/v1/projects`.
- Do not make the app run CCB/provider CLI locally.
- Do not make Tailnet/Cloudflare/Relay change project ids, terminal ids,
  ProjectView shape, or terminal frame schemas.
- Do not require external LLM provider availability for the deterministic
  local acceptance lane.

## Source Architecture

### Host Gateway Mode

Add a server-level mobile gateway mode that can run outside a project root:

```text
ccb install mobile
  -> ensure optional mobile bundle
  -> ensure server gateway supervisor/sidecar
  -> expose loopback gateway
  -> prepare route provider
  -> emit pairing QR
```

The gateway should have a host identity distinct from a project identity:

- `host_id`: stable server/mobile gateway identity;
- `project_id`: per CCB project identity;
- `device_id`: paired phone identity;
- route provider metadata: reachability only.

Existing single-project `ccb mobile serve` can stay as a developer/debug
command, but product onboarding should use the server gateway.

### Project Registry

Create a host-level project registry service with two inputs:

1. runtime-state discovery:
   - scan `runtime_state_root_candidates()`;
   - read runtime root markers where available;
   - locate CCB lease/socket metadata;
   - ping each candidate `ccbd` with a short timeout;
2. optional user pins/favorites:
   - later persisted under server mobile state;
   - not required for P0.

Only projects with a valid CCB runtime identity should be listed. For each
project, return a redacted summary:

```json
{
  "id": "project_id",
  "display_name": "test_ccb2",
  "root": "/home/bfly/yunwei/test_ccb2",
  "health": "healthy",
  "lifecycle": "mounted",
  "last_seen_at": "2026-06-24T00:00:00Z",
  "capabilities": ["project_view", "focus", "message_submit", "file_upload"]
}
```

Do not include `ccbd_socket_path`, tmux socket path, tmux session name,
runtime-state root, provider cache paths, or host-local artifact paths.

### Request Routing

After discovery, all project routes resolve through the registry:

- `GET /v1/projects` returns the redacted registry list.
- `GET /v1/projects/{project_id}/view` connects to that project's `ccbd`.
- `POST /v1/projects/{project_id}/focus-agent` routes to that project's
  focus endpoint.
- ordinary chat sends route to that project's selected-pane/native input path;
- `POST /v1/projects/{project_id}/agents/{agent}/messages` remains available
  only as an explicit ask/compatibility path unless a later decision changes
  Decision 015.
- file upload/download, terminal open, lifecycle, and refresh all use the
  selected `project_id`.

If a project disappears or becomes unreachable, return a typed degraded
project summary in `listProjects()` and fail closed for unsafe actions.

## App Architecture

### Home State

Add a project-list loading state separate from project-view loading:

```text
ProjectHomeScreen
  paired gateway profile active
  -> load projects
  -> show ProjectListScaffold(projects)
  -> user opens project
  -> load ProjectView(project.id)
  -> show selected-agent workspace
```

The fake repository can still provide demo UI tests, but production paired mode
must not default to fake `proj-demo` when a server profile is available.

### Project List UI

Replace current single-item list with a real list:

- render all `CcbProject` entries;
- show health, display name, root, and optional activity;
- add pull-to-refresh / retry;
- show connection details and diagnostics on the list page;
- keep fake demo clearly labelled as demo when no paired profile exists.

### Project Selection

On project open:

- set `_activeProjectId = project.id`;
- clear stale `_openedProjectId` and `_selectedAgentName`;
- load `getProjectView(project.id)`;
- enter mobile chat scaffold when the view arrives;
- show recoverable error UI if view load fails or times out.

On project switch:

- do not reuse old namespace epoch;
- do not reuse old terminal handle;
- do not reuse old selected agent unless that exact agent exists in the new
  view and the UX explicitly preserves it later.

## Security Boundary

- Pair once to the server gateway, not to arbitrary project directories.
- Device token scopes apply across project routes but are checked per action.
- Registry must only route to locally discovered CCB projects.
- Gateway remains loopback-bound; remote access is via route providers.
- No Funnel by default.
- No saved Tailscale password, OAuth token, admin API token, or automatic
  tailnet ACL/grant edits.
- No public HTTP route for host-local filesystem browsing.
- File download uses gateway-authenticated opaque file/artifact ids, not host
  paths.

## Implementation Packages

### Package A: Source Host Project Registry

Files likely in `/home/bfly/yunwei/ccb_source`:

- new `lib/mobile_gateway/project_registry.py`;
- update `lib/mobile_gateway/service.py`;
- update focused source tests around `/v1/projects` and unknown project
  routing.

Acceptance:

- unit tests can create two fake project runtime roots;
- `/v1/projects` returns both;
- `/v1/projects/{id}/view` calls the correct fake `ccbd` client;
- unknown ids still fail closed;
- redaction tests prove no socket/runtime paths leak.

Status 2026-06-24: first registry package landed in source worktree
`/home/bfly/yunwei/ccb_source_mobile_server_install` at commit `a52d5b32`
(`refactor: add mobile gateway project registry`). The package adds
`MobileGatewayProjectRegistry`, keeps the default single-project path
compatible, routes `/v1/projects/{project_id}/view` and related gateway
actions through registry lookup, rejects unknown project ids with 404, and
tests two-project listing/routing without leaking tmux socket evidence.
Verification passed:

```bash
PYTHONPATH=lib python -m pytest test/test_mobile_gateway_service.py -q
PYTHONPATH=lib python -m pytest \
  test/test_mobile_gateway_service.py \
  test/test_cli_management_update.py \
  test/test_v2_cli_router.py \
  test/test_v2_cli_parser.py -q
python -m py_compile \
  lib/mobile_gateway/service.py \
  lib/mobile_gateway/project_registry.py \
  lib/mobile_gateway/__init__.py
git diff --check
```

This is not the final product behavior yet: discovery and `ccb install mobile`
still need to construct a real server registry instead of injecting one in
tests.

### Package B: Server-Level `ccb install mobile`

Files likely in `/home/bfly/yunwei/ccb_source`:

- CLI parser/router for `ccb install mobile`;
- service that ensures mobile bundle, host gateway state, route-provider
  setup, and pairing QR;
- Tailnet/Tailscale checks can reuse the existing mobile update work where
  safe.

Acceptance:

- command works outside a CCB project directory;
- gateway stays loopback-only;
- emitted pairing payload uses `host_id`, not a current project id as host id;
- existing `ccb update mobile` can call or suggest this path without
  ambiguous per-project semantics.

Status 2026-06-24: first server-level install gateway package landed in source
worktree `/home/bfly/yunwei/ccb_source_mobile_server_install` at commit
`b258cfe2` (`feat: add server-wide mobile install gateway`). The package adds
`ccb install mobile` as a management command so it runs before project-context
phase2 parsing and can be invoked outside a CCB project. CCB runtime startup
now best-effort publishes mounted projects into a user-level mobile host
registry; `ccb install mobile` reads that registry, starts a loopback-only
`loopback_server_registry` gateway, stores pairing/device state under server
mobile state, and emits a server `host_id` pairing payload instead of using a
current project id. Verification passed:

```bash
PYTHONPATH=lib python -m pytest \
  test/test_mobile_cli_service.py \
  test/test_mobile_gateway_service.py \
  test/test_cli_management_update.py \
  test/test_v2_cli_router.py \
  test/test_v2_cli_parser.py \
  test/test_ccbd_service_graph.py \
  test/test_ccbd_start_preparation.py \
  test/test_ccbd_runtime_attach.py -q
python -m py_compile \
  lib/mobile_gateway/project_registry.py \
  lib/mobile_gateway/__init__.py \
  lib/mobile_gateway/service.py \
  lib/cli/services/mobile.py \
  lib/cli/router.py \
  lib/cli/entrypoint_runtime.py \
  lib/cli/management.py \
  lib/cli/management_runtime/__init__.py \
  lib/cli/management_runtime/commands.py \
  lib/cli/management_runtime/commands_runtime/__init__.py \
  lib/cli/management_runtime/commands_runtime/install.py \
  lib/cli/render_runtime/ops_views_basic.py \
  lib/ccbd/app_runtime/bootstrap.py \
  lib/ccbd/keeper.py
git diff --check
```

This still needs App Package C before user acceptance: current app paired-mode
startup still expects one active ProjectView and must be changed to load
`/v1/projects` first.

### Package C: App Multi-Project Home

Files likely in `app/`:

- project-home state coordinator for project list load/open;
- `ProjectListScaffold` accepts `List<CcbProject>`;
- runtime activation no longer immediately loads a default project view when
  a paired server profile is active;
- widget tests for multi-project list, open, refresh, and load failure.

Acceptance:

- paired gateway startup calls `listProjects()` first;
- first page shows two server projects;
- tapping project A loads A;
- tapping project B loads B;
- fake demo is only shown when explicitly in fake mode or no paired server
  profile exists.

Status 2026-06-24: first App multi-project home package landed in the mobile
repo at commit `6e02d2d` (`refactor: load paired gateway server projects first`).
The app now treats paired gateway profiles as server profiles: gateway
activation constructs the repository/terminal session and loads
`listProjects()` first instead of `getProjectView(host_id)`. The paired first
page renders server `CcbProject` entries, opens a project by setting
`_activeProjectId = project.id`, and then loads that exact ProjectView.
Mobile back from a paired project returns to the server project list. Focused
widget coverage simulates a server gateway with `test_ccb2` and `ccb_mobile`
projects and asserts that no host-id ProjectView is requested before project
selection and that message submit carries `projectId = test_ccb2`. Verification
passed:

```bash
source tools/mobile_toolchain_env.sh && cd app && \
  flutter test test/project_home_server_projects_widget_test.dart \
    test/project_home_runtime_activation_test.dart
source tools/mobile_toolchain_env.sh && cd app && \
  flutter test \
    test/project_home_runtime_activation_widget_test.dart \
    test/project_home_layout_widget_test.dart \
    test/project_home_focus_widget_test.dart \
    test/project_home_terminal_navigation_widget_test.dart \
    test/project_home_pairing_widget_test.dart \
    test/project_home_pairing_scan_widget_test.dart \
    test/widget_test.dart
source tools/mobile_toolchain_env.sh && cd app && flutter test
git diff --check
```

`flutter analyze` still exits non-zero because the analysis server hits the
known local `Too many open files` condition; the tail reports `No issues
found!`. This package is not final user acceptance: Package D must still run a
real local AVD multi-project smoke against the source server-wide gateway and
record latency/file/artifact evidence.

### Package D: Real Local AVD Multi-Project Matrix

Run a real emulator smoke with two host-side CCB projects:

- project `test_ccb2-a`;
- project `test_ccb2-b`;
- one server-level mobile gateway;
- one pairing profile;
- one app install.

Acceptance:

- App first page shows both projects.
- Sending to agent in project A appears in project A backend only.
- Sending to agent in project B appears in project B backend only.
- File upload/download works in both.
- Backend-generated artifact download works in both.
- Response latency captures p50/p95 for list, project view, send, reply, upload,
  download.

Status 2026-06-24: Package D has a passing backend-only source smoke and a
passing Android Emulator app smoke against the combined source worktree
`/home/bfly/yunwei/ccb_source_mobile_server_wide_full`.

Source worktree commits now used for the smoke:

- `5ea57831` merge of the local backend file/artifact matrix into
  server-wide install;
- `49871df0` (`fix: route mobile files through project registry`);
- `79f7777b` (`fix: preserve mobile host registry env`);
- `227e2963` (`fix: resolve mobile artifacts from gateway file store`).

Mobile repo commit `bc57020` (`test: add server-wide emulator gateway smoke`)
adds:

- `app/integration_test/server_wide_gateway_smoke_test.dart`;
- `tools/mobile_server_wide_emulator_smoke.py`.

The backend-only source smoke artifact is
[../history/server-wide-backend-full-smoke-20260624.json](../history/server-wide-backend-full-smoke-20260624.json).
It starts two real CCB projects, runs one `ccb install mobile` gateway, claims
one device profile, lists both projects, and for both `test_ccb2_alpha` and
`test_ccb2_beta` verifies ProjectView, message submit, deterministic backend
Markdown reply, file upload/download, and backend-generated artifact download.
The recorded timings include:

- project view: `0.009-0.011 s`;
- message-to-reply visible through gateway conversation: `1.515-1.518 s`;
- file upload/download: `0.002-0.003 s`;
- backend artifact route: `1.523 s`.

The Android Emulator smoke artifact is
[../history/server-wide-avd-full-smoke-20260624.json](../history/server-wide-avd-full-smoke-20260624.json).
It uses Android Emulator `emulator-5554`, `adb reverse tcp:18891 tcp:18891`,
and the app debug-profile seed to connect to the same server-wide gateway
shape. The app first page lists server projects, opens `test_ccb2_alpha` and
`test_ccb2_beta`, and completes:

- multi-turn chat for `mobile_probe`;
- chat plus image/artifact lanes for `mobile_peer`;
- document upload/download;
- PNG upload/download;
- backend-generated text and PNG artifact downloads.

Verification passed:

```bash
# source worktree
PYTHONPATH=lib python -m pytest \
  test/test_mobile_gateway_service.py \
  test/test_mobile_cli_service.py \
  test/test_runtime_env_control_plane.py \
  test/test_provider_execution_fake_runtime.py \
  test/test_cli_management_update.py \
  test/test_v2_cli_router.py \
  test/test_v2_cli_parser.py -q
python -m py_compile \
  lib/mobile_gateway/service.py \
  lib/mobile_gateway/project_registry.py \
  lib/cli/services/mobile.py \
  lib/runtime_env/control_plane.py \
  lib/cli/management_runtime/commands_runtime/update.py \
  lib/cli/router.py \
  lib/cli/parser.py
git diff --check

# mobile repo
./tools/mobile_server_wide_emulator_smoke.py \
  --source-ccb /home/bfly/yunwei/ccb_source_mobile_server_wide_full/ccb \
  --gateway-listen 127.0.0.1:18891 \
  --device-id emulator-5554 \
  --force-config
source tools/mobile_toolchain_env.sh && cd app && flutter test
python -m py_compile tools/mobile_server_wide_emulator_smoke.py
git diff --check
```

The deterministic local provider is used only as the backend test provider so
the AVD lane can make exact assertions without depending on external LLM
latency. The route is still the real CCB source runtime and gateway, not
`FakeMobileCcbRepository` or an app-local demo repository.

Manual real-provider handoff 2026-06-24:

- source worktree:
  `/home/bfly/yunwei/ccb_source_mobile_server_wide_full`;
- source head: `227e2963 fix: resolve mobile artifacts from gateway file store`;
- mobile head: `52a0ab0 test: support manual server-wide emulator session`;
- gateway: `127.0.0.1:18893`, route provider `lan`, mode
  `loopback_server_registry`;
- provider: `codex`;
- emulator: `emulator-5554`, `adb reverse tcp:18893 tcp:18893`;
- visible projects: `test_ccb2_beta` and `test_ccb2_alpha` under
  `/home/bfly/yunwei/test_ccb2/...`.

The manual session evidence is
[../history/server-wide-manual-codex-session-20260624.json](../history/server-wide-manual-codex-session-20260624.json).
It exists to let a user verify the real provider path in the already-open
emulator. The automated acceptance lane remains deterministic so it can assert
messages, files, and generated artifacts without depending on external model
latency.

Landing merge validation 2026-06-24:

- landing worktree:
  `/home/bfly/yunwei/ccb_source_mobile_server_wide_landing`;
- base: source main `af53f5a4`;
- merge commit: `adb18294 merge: land server-wide mobile backend`;
- source focused test batch: `200 passed`;
- source `py_compile`: passed;
- source `git diff --check`: passed;
- AVD server-wide smoke on `127.0.0.1:18894`: `status=ok`, integration test
  `All tests passed!`.
- final candidate after whitespace cleanup:
  `b47488c1 fix: clean server-wide mobile whitespace`;
- final candidate range `git diff --check af53f5a4..HEAD`: passed;
- final candidate source focused test batch: `200 passed`;
- final candidate source `py_compile`: passed;
- final candidate AVD server-wide smoke on `127.0.0.1:18895`: `status=ok`,
  integration test `All tests passed!`.
- review-fix candidate after reviewer1 High blocker:
  `9de121bc fix: tolerate unreachable mobile projects in list`;
- `9de121bc` keeps reachable projects visible when another registry entry is
  stale/unreachable and degrades only the stale entry;
- review-fix candidate range `git diff --check af53f5a4..HEAD`: passed;
- review-fix candidate source focused test batch: `201 passed`;
- review-fix candidate source full pytest: `3001 passed, 2 skipped`;
- review-fix candidate source `py_compile`: passed;
- review-fix candidate AVD server-wide smoke on `127.0.0.1:18896`:
  `status=ok`, integration test `All tests passed!`.
- reviewer1 re-review `job_1902074f73dd`: accept, previous stale-project list
  blocker closed.
- mobile repo full `flutter test`: `364 passed`.
- source main merge commit:
  `59f1c07b merge: land server-wide mobile backend`;
- source main post-merge focused tests: `201 passed`;
- source main post-merge `py_compile`: passed;
- source main merge range `git diff --check HEAD^..HEAD`: passed;
- source main AVD server-wide smoke on `127.0.0.1:18897`: `status=ok`,
  integration test `All tests passed!`.

Evidence:
[../history/server-wide-landing-avd-smoke-20260624.json](../history/server-wide-landing-avd-smoke-20260624.json).
Final candidate evidence:
[../history/server-wide-landing-final-avd-smoke-20260624.json](../history/server-wide-landing-final-avd-smoke-20260624.json).
Review-fix candidate evidence:
[../history/server-wide-landing-review-fix-avd-smoke-20260624.json](../history/server-wide-landing-review-fix-avd-smoke-20260624.json).
Source main evidence:
[../history/server-wide-source-main-avd-smoke-20260624.json](../history/server-wide-source-main-avd-smoke-20260624.json).

### Landing Checklist

Before this topic is considered fully landed rather than worktree-green:

1. Preserve the app-side smoke support currently on mobile main, including the
   server-wide AVD smoke and manual `--hold` session path.
2. Keep a manual real-provider emulator session available long enough for user
   testing against non-`ccb_mobile` projects.
3. Run the physical Tailnet/relay lane as follow-up product hardening; it must
   use the same server gateway and must not change project identity semantics.

## Acceptance Gates

P0:

- `ccb install mobile` can run from outside any CCB project.
- Phone pairing creates a server profile, not a single-project-only profile.
- `/v1/projects` returns all mounted/reachable CCB projects on that server.
- App first page renders those projects.
- Opening a project loads that exact project's ProjectView.
- Messages and files route to the selected project only.
- Unknown/stale project ids fail closed.

P1:

- Project health updates without forcing app restart.
- Offline projects remain visible with degraded status and safe actions locked.
- Android app install/upgrade continuity is defined: the same release channel
  can install a new APK over the existing app without uninstalling, preserving
  pairing/app data, and signature mismatches are prevented or surfaced before
  users hit an install failure.
- Favorites/pins can be local or gateway-side, but must not change project
  identity.
- Tailnet route onboarding uses the same server gateway and does not change
  app project routing.

## Verification Plan

Source focused tests:

```bash
PYTHONPATH=lib python -m pytest \
  test/test_mobile_gateway_service.py \
  test/test_cli_parser.py \
  test/test_v2_cli_router.py
python -m py_compile lib/mobile_gateway/service.py lib/mobile_gateway/project_registry.py
git diff --check
```

App focused tests:

```bash
cd app
flutter test test/project_home_project_list_test.dart
flutter test test/gateway_mobile_ccb_repository_test.dart
flutter test test/http_gateway_transport_test.dart
flutter test test/project_home_runtime_activation_widget_test.dart
flutter test
git diff --check
```

Real AVD:

```bash
python tools/mobile_emulator_ui_smoke.py \
  --mode local-real-backend \
  --multi-project \
  --expect-project-count 2 \
  --measure-latency
```

The smoke artifact must record:

- source commit;
- app commit;
- gateway URL and route provider;
- adb reverse mappings;
- listed project ids and roots;
- selected project id for every message/file action;
- reply markers and file hashes;
- p50/p95 latency metrics.

## Open Risks

- Source currently has no durable host-level project registry service; scanning
  runtime roots must avoid stale/dead projects and path leaks.
- Pairing storage currently carries `project_id` in several paths; host profile
  semantics need a narrow migration to avoid confusing `host_id` and
  `project_id`.
- App state currently assumes one active `CcbProjectView`; multi-project list
  must be introduced without moving unrelated chat/focus/terminal logic.
- Existing local smoke tools are already rich but must grow a true
  multi-project lane instead of reusing a single current-project gateway.
