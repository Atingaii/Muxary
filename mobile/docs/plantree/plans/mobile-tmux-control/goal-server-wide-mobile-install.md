# CCB Mobile Server-Wide Install Goal

Date: 2026-06-24

## Purpose

This document is the reusable long-running goal prompt for landing the
server-wide CCB Mobile install and multi-project gateway.

Use it when starting or resuming the work that changes CCB Mobile from a
current-project demo/gateway into a server-level capability:

```bash
ccb install mobile
```

The final result must let one paired phone connect to one server gateway, list
all mounted/reachable CCB projects on that server, open any project, send to
that project's agents, receive real backend replies, upload files, and download
backend-generated artifacts.

## Invocation

Primary copy/paste prompt:

```text
读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-server-wide-mobile-install.md`
作为当前长期 goal。

目标：先制定并校准方案，然后分包落地，最终打通 `ccb install mobile`
服务器级安装/激活能力。完成后，手机只需配对一次服务器 gateway，就能在
App 第一页看到该服务器所有 mounted/reachable 的 CCB 项目；点任意项目后
进入该项目的真实 ProjectView；发送问题能到达该项目真实 CCB 后端并显示
真实 agent 回复；图片/文档上传、后台生成文件下载、terminal、diagnostics、
lifecycle 都必须按当前选中的 project_id 路由，不能串项目。

启动前必须先 resume plan tree：读取
`docs/plantree/README.md`、本计划 README、`roadmap.md`、
`implementation-status.md`、
`topics/server-wide-mobile-install-and-project-registry.md`、
`topics/local-real-backend-comprehensive-test-plan.md`、相关 decisions、
当前 mobile/source git status 和最新 commits。确认 Current Phase、
Next Target、Blocked By、Last Verified、允许写入范围后再实现。

工作方式：
- Lead 负责方案校准、拆 coherent packages、派发 workers、组织 reviewers、
  维护 plan tree、收口验收；不要把同一份审查发给多个 reviewer，也不要让
  workers 交叉依赖同一个未收口 WIP。
- Workers 独立落地 coherent packages；每包必须有范围、文件、测试、提交、
  风险和复现说明。
- Reviewers 独立审查 exact commit/range；只给一个 reviewer 一份审查任务，
  除非用户明确要求多方 review。
- 不要继续切过碎 micro-helper；本 goal 的包要围绕完整能力边界：
  source registry、server install、app multi-project home、real AVD smoke。

必须先制定方案再落地：
1. 先确认 server-wide architecture：host_id 与 project_id 分离，
   server gateway 与 project gateway 分离，项目 registry 来源、红action、
   token/scopes、route-provider 边界、未知/离线项目 fail-closed。
2. 再落 source package：host-level project registry 和多项目 gateway route。
3. 再落 `ccb install mobile` package：服务器级安装/激活/配对入口，能在非
   CCB 项目目录执行。
4. 再落 app package：paired mode 首页先 `listProjects()`，展示服务器项目
   列表，点击项目后加载对应 ProjectView，fake demo 只作为显式 demo/fallback。
5. 最后落真实本地 AVD multi-project smoke：两个真实本地 CCB 项目、一个
   server gateway、一个 app profile、分别收发消息和文件，记录响应速度。

Source repo 规则：
- CCB source 在 `/home/bfly/yunwei/ccb_source`，但实现必须使用明确 worktree；
  不要在 source 主目录覆盖 unrelated dirty 文件。
- Source 和 mobile repo 分开提交、分开测试、分开汇报。
- 保持 gateway loopback-only；不使用 Funnel；不绑定 `0.0.0.0`；不保存
  Tailscale 密码、OAuth token 或 admin API token；不默认修改 ACL/grants。
- RouteProvider 是 reachability metadata，不进入 project ids、terminal ids、
  ProjectView 或 terminal frame schema。

App repo 规则：
- App 首页必须从 paired gateway 的 `listProjects()` 驱动，而不是启动时直接
  `getProjectView('proj-demo')`。
- `ProjectListScaffold` 必须支持多个 `CcbProject`，显示 health/root/activity。
- 选择项目时设置 active project id，清理 stale selected-agent/opened-project/
  terminal handle，再加载该项目 ProjectView。
- 所有 chat/file/terminal/lifecycle/diagnostics 操作必须携带当前 project_id。
- 错误态必须可恢复：retry、连接详情、回到 fake demo，但不能无限 spinner。

真实验收：
- 至少两个本地 CCB 项目通过同一个 server gateway 出现在 App 首页。
- 打开 project A 后发送消息，电脑端 project A 能看到对应输入，App 能看到
  project A 的真实 agent 回复。
- 打开 project B 后同样验证，并证明不会写入 project A。
- 对两个项目分别验证图片/文档上传、下载、backend-generated artifact 下载。
- 记录 p50/p95：project list、project view、message submit、reply visible、
  file upload、file download。
- 产出 machine-readable smoke artifact，写入 plan-tree history。

不要把 goal 标记为 complete，直到：
- `ccb install mobile` server-level path 已在 source worktree 落地并通过测试；
- source gateway 能列出所有 mounted/reachable CCB projects；
- app paired mode 首页能显示并打开多个真实项目；
- 多项目真实 AVD smoke 证明消息、回复、文件、artifact、diagnostics 路由都按
  project_id 正确隔离；
- plan-tree evidence、commits、测试结果和剩余风险都已记录。
```

Short objective:

```text
端到端落地 `ccb install mobile` 服务器级 mobile gateway：手机配对一次服务器，
首页列出所有 mounted/reachable CCB 项目，并能分别进入每个项目完成真实消息、
回复、文件上传下载和后台 artifact 下载。
```

Short call:

```text
请读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-server-wide-mobile-install.md`
作为当前长期 goal。先校准方案，再按 source registry、`ccb install mobile`、
App 多项目首页、真实 AVD 多项目 smoke 四个 coherent packages 落地。不要再
围绕单项目 demo 验收；完成条件是一个 server gateway、一个手机 profile、
多个真实 CCB 项目都能收发消息和文件且 project_id 不串。
```

## Scope

### In Scope

- CCB source worktree changes for server-level mobile install, project registry,
  host gateway routing, pairing metadata, and focused tests.
- CCB mobile app changes for paired gateway project list, project selection,
  state cleanup, and multi-project UI tests.
- Real local Android Emulator validation through loopback gateway and
  `adb reverse`.
- Plan-tree updates, smoke artifacts, focused/full tests, and coherent commits.

### Out Of Scope

- Physical device acceptance as a P0 gate.
- Public relay production deployment.
- Cloudflare named tunnel as the primary path.
- Tailscale ACL/grant automation.
- Listing arbitrary tmux sessions or filesystem directories.
- Making the mobile app run provider/agent processes locally.
- Replacing project ids with route-provider metadata.

## Required Architecture Decisions

Before implementation, confirm these decisions in the plan tree:

1. `host_id` identifies the server mobile gateway; `project_id` identifies one
   CCB project.
2. Pairing is server-wide, with optional last/default project metadata only.
3. `/v1/projects` is a host registry route, not a current-project wrapper.
4. Project actions route through a registry lookup by `project_id`.
5. Registry entries are redacted and never expose socket/runtime paths.
6. Unknown or stale project ids fail closed.
7. App fake demo is not the paired-gateway startup state.
8. Route providers change reachability only.

## Landing Packages

### A. Source Host Project Registry

Goal: make the gateway able to discover and route to multiple local CCB
projects.

Likely source files:

- `lib/mobile_gateway/project_registry.py`
- `lib/mobile_gateway/service.py`
- `test/test_mobile_gateway_service.py`
- focused parser/router tests only if API shape changes.

Acceptance:

- tests create at least two fake/discovered project records;
- `/v1/projects` returns both;
- `/v1/projects/{project_id}/view` calls the matching ccbd client;
- health/degraded state is represented without leaking socket/runtime paths;
- unknown project id returns typed 404/fail-closed response.

### B. Source `ccb install mobile`

Goal: expose product onboarding as server-level install/activate.

Likely source files:

- CLI parser/router for `ccb install mobile`;
- mobile install/update service;
- optional host gateway state under server/user mobile state;
- tests for command help, outside-project invocation, loopback-only binding,
  pairing payload, and Tailnet route safety.

Acceptance:

- command works outside any CCB project root;
- emits one server gateway pairing QR/payload;
- starts or refreshes loopback-only gateway;
- does not save credentials/tokens or modify Tailnet ACL/grants;
- existing `ccb update mobile` behavior is either delegated to or clearly
  aligned with this command.

### C. App Multi-Project Home

Goal: make paired mode first page a server project list.

Likely app files:

- `ProjectHomeScreen` state flow;
- project list widget/host;
- repository/project-list loading helper if needed;
- widget tests around paired startup, multi-project render, open project,
  project switch, and error/fallback.

Acceptance:

- paired startup calls `listProjects()` before opening a project view;
- list renders two or more server projects;
- tapping a project loads its exact ProjectView;
- stale selected agent/opened project/terminal handle does not cross projects;
- fake demo remains available only as explicit fake mode/fallback.

### D. Real Local Multi-Project AVD Smoke

Goal: prove the complete behavior outside mocks.

Likely app/source tooling:

- extend existing mobile emulator smoke harness;
- create two disposable real CCB project roots;
- run one server gateway;
- pair one app profile;
- drive messages/files/artifacts through both projects.

Acceptance:

- App screenshot/hierarchy shows both projects on first page;
- project A message/reply stays in A;
- project B message/reply stays in B;
- upload/download/artifact routes work in both;
- metrics include p50/p95 for list, open, send, reply-visible, upload,
  download;
- artifact is written to `docs/plantree/plans/mobile-tmux-control/history/`
  and linked from evidence index/status.

## Verification Matrix

Source:

```bash
PYTHONPATH=lib python -m pytest \
  test/test_mobile_gateway_service.py \
  test/test_cli_management_update.py \
  test/test_v2_cli_router.py \
  test/test_v2_cli_parser.py
python -m py_compile lib/mobile_gateway/service.py lib/mobile_gateway/project_registry.py
git diff --check
```

App:

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

## Completion Rule

This goal is complete only when all of the following are true:

- source has a committed server-level install/gateway/registry path;
- app has a committed paired-gateway multi-project home path;
- real AVD smoke proves two projects can be listed, opened, messaged, and used
  for file/artifact transfer through one paired server profile;
- project identity and route metadata are cleanly separated;
- plan-tree roadmap/status/evidence are updated;
- remaining risks are explicitly recorded and do not block P0 behavior.
