# CCB Mobile Emulator-Only Landing Goal

Date: 2026-06-21

## Purpose

This document is a reusable goal prompt for landing the remaining CCB Mobile
phone/iPad project using only local virtualized validation.

Use it when the next implementation run should avoid physical phones, public
domains, Cloudflare account setup, and live public relay infrastructure. The
run should still finish product-quality app and gateway slices, but every
acceptance gate must be reproducible on the local Android Emulator, isolated
CCB runtime, loopback gateway, and test harnesses.

This is an implementation-driving contract, not only a test checklist. It
requires architecture/reuse design before coding, regular plan-tree progress
records, regular coherent commits, and strict separation between local
emulator acceptance and deferred public-route work.

## Invocation

Use the following block as the primary copy/paste prompt when starting or
resuming the emulator-only landing goal.

Primary goal prompt:

```text
读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-emulator-only.md`
作为当前长期 goal。

目标：仅基于本机虚拟机/Android Emulator 端到端落地 CCB Mobile 后续全部
功能，并持续维护 plan tree、验证记录和阶段性 commit。

验收边界：
- 强制验收环境只允许使用本机 AVD `ccb_mobile_api35`、host loopback
  gateway `127.0.0.1:8787`、`adb reverse tcp:8787 tcp:8787`、isolated CCB
  test project/runtime、Flutter debug APK、fake/local route providers、
  Flutter/source tests、debug build 和自动/半自动 emulator smoke。
- 不得把真机、公网 IP、公网域名、Cloudflare 配置、生产 relay 服务器、
  外部公网可达环境、用户购买域名或真实远程服务器作为完成条件。
- Cloudflare、生产 relay、真实域名、物理手机和公网 smoke 全部是
  deferred/non-blocking；只保留 route-provider 边界、fake/local tests 和
  plan-tree 设计记录。

启动流程：
- 先 resume plan tree：读取 `docs/plantree/README.md`、本计划 README、
  `implementation-status.md`、`roadmap.md`、active decisions/topics、最新
  commit 和当前 git status。
- 确认 Current Phase、Next Target、Blocked By、Last Verified、允许写入
  范围和当前 dirty worktree 后再实现。
- 每个批次开始都要刷新 plan tree 的 target、阻塞、验证基线和写入范围。

产品方向：
- 默认产品体验继续遵守 Agent-first：顶部 agent switcher，主体只显示一个
  selected-agent workspace。
- Selected-agent workspace 必须落地结构化 Markdown/content reader 和
  可上下拖动的 readable terminal history。
- Raw terminal/tmux stream 只作为显式 Open Terminal 控制/调试入口。
- 项目路径、gateway URL、pairing code、runtime id、route diagnostics 和
  低层 terminal 状态放到连接详情/设置/终端模式，不常驻第一屏。

架构和复用纪律：
- 先做或更新合理架构设计和开源库复用/二次修改方案，再进入实现；不得默认
  从头手写 terminal、tmux、gateway、pairing、Markdown、notification、
  secure storage、reconnect、history renderer 等成熟能力。
- 优先复用并二次修改成熟开源库和已有 CCB 源码能力；如果必须写
  CCB-specific 实现，先在 plan tree 记录 license、平台、安全、维护或边界
  原因。
- 继续参考 ServerBox、MuxPod、tmux-mobile、Paseo、Flutter terminal/
  WebSocket/Markdown/notification/secure-storage 生态，但只引入 license
  和架构边界可接受的代码。
- 如果需要修改 `/home/bfly/yunwei/ccb_source`，必须在 CCB source repo
  单独检查、测试和提交，再回到 mobile repo 更新 plan-tree evidence。

工作循环：
resume plan tree -> architecture/reuse check -> implement coherent package ->
verify on emulator/local harness -> update plan tree -> commit。

计划和提交纪律：
- 每个批次结束时必须更新 plan tree 的进度、证据、下一步和风险。
- 长时间执行时，60-90 分钟内必须至少完成一次 coherent commit，或在
  `implementation-status.md` 记录状态、验证、阻塞和下一步。
- 移动仓库和 CCB source 仓库必须分开提交；提交要小、可回滚。
- 不能提交 `.ccb/agents`、`.ccb/ccbd`、secrets、token、build artifacts、
  日志、本地 SDK 配置或 emulator/runtime 状态。

不要把 goal 标记为 complete，直到 emulator-only acceptance 全部满足：
App 能在 AVD 启动；本机 loopback gateway 能 pairing/claim；能看到 CCB
project/agent；agent switcher 能切换；selected-agent workspace 能显示
Markdown/content 和可滚动 readable terminal history；Open Terminal 能进入
raw tmux 控制；输入、paste、resize、reconnect、terminal token renewal、
route diagnostics、simulated notifications、safe lifecycle controls 都有
本机验证；plan-tree evidence 和 coherent commits 完整。
```

Short objective:

```text
仅基于本机虚拟机/Android Emulator 端到端落地 CCB Mobile 后续全部功能，并
持续维护 plan tree、验证记录和阶段性 commit。
```

Short call:

```text
请读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-emulator-only.md`
作为当前长期 goal。只用本机 Android Emulator/AVD、loopback gateway、
adb reverse、isolated CCB runtime、fake/local route-provider tests、
Flutter/source tests、debug APK build 和 emulator smoke 落地后续全部 CCB
Mobile 功能。不要依赖真机、公网、Cloudflare、域名、生产 relay、公网 IP
或外部服务器。实现前先恢复并更新 plan tree，补齐架构设计和开源库复用/
二改方案；实现后必须运行匹配验证并提交小而可回滚的 commit。所有长期进展
持续回写 plan tree。
```

English call block:

```text
Read `/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-emulator-only.md`
and execute it as the active project goal.

Deliver the remaining CCB Mobile project using only local virtualized
validation: Android Emulator/AVD, loopback gateway, adb reverse, isolated CCB
test runtime, fake/local route providers, Flutter tests, source focused tests,
and emulator smoke. Do not block on physical devices, Cloudflare, public DNS,
production relay, or external public connectivity. Preserve the agent-first UI:
top agent switcher, one selected-agent workspace, structured content reader,
readable terminal history with vertical scrolling, and raw terminal only as an
explicit Open Terminal fallback. Before implementation, update the
architecture/reuse design and prefer adapting mature open-source libraries or
existing CCB source capabilities over greenfield implementation. Keep plan tree
updated at the start and end of every work batch, record blockers/verification
promptly, and commit coherent packages regularly.
```

Current execution prompt:

```text
Read and execute
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-emulator-only.md`
as the active long-running goal.

Resume the plan tree first. Use only the local Android Emulator/AVD,
loopback gateway, adb reverse, isolated CCB runtime, fake/local route-provider
tests, Flutter tests, source focused tests, debug APK build, and emulator smoke
as required acceptance gates. Do not wait for Cloudflare, public DNS, public
IP, production relay, physical phones, or external servers.

Continue from the current Next Target unless a newer decision supersedes it:
land the agent-first selected-agent workspace, structured Markdown/content
reader, vertically scrollable readable terminal history, explicit raw terminal
fallback, terminal input/paste/resize/reconnect/token renewal, route
diagnostics, simulated notifications/deep links, and safe lifecycle controls.

For every package: refresh plan-tree status -> check architecture/reuse ->
implement -> verify locally/emulator-only -> update plan-tree evidence ->
commit. During long runs, produce a coherent commit or status/blocker record
within 60-90 minutes. Keep mobile repo and CCB source repo commits separate and
never commit runtime state, secrets, logs, build artifacts, `.ccb/agents`, or
`.ccb/ccbd`.
```

## Scope

### In Scope

- Flutter app work under `/home/bfly/yunwei/ccb_source/mobile/app`.
- Plan-tree updates under `docs/plantree`.
- Local Android Emulator validation through AVD `ccb_mobile_api35`.
- Local gateway validation through `127.0.0.1:8787` and
  `adb reverse tcp:8787 tcp:8787`.
- Isolated CCB test projects/runtimes only, not destructive operations against
  active user workspaces.
- CCB source changes under `/home/bfly/yunwei/ccb_source` only when a missing
  gateway/content/history/focus/lifecycle contract blocks emulator landing.
- Fake/local route-provider tests for relay compatibility.
- Simulated notifications and local deep-link behavior.

### Out Of Scope For This Goal

- Physical Android/iOS device validation.
- App Store/TestFlight/Play Store release.
- Public Cloudflare named-tunnel smoke.
- Public DNS/domain setup.
- Production CCB Relay deployment or public relay load testing.
- Real remote access from outside the LAN.
- Editing unrelated CCB source behavior outside mobile gateway, content,
  project-view, terminal-history, focus, diagnostics, route metadata,
  notification, or lifecycle contracts.

## Required Product Shape

The emulator-only landing must still produce the intended product experience:

1. Project opens to an agent-first workspace.
2. Top area is an agent switcher.
3. Main body shows exactly one selected agent.
4. Project path, pairing code, gateway URL, runtime id, and diagnostics stay
   behind connection/details views.
5. Structured CCB content is authoritative for Markdown/math.
6. Readable terminal history uses current tmux pane plus retained scrollback as
   best-effort history.
7. Raw terminal opens only through explicit Open Terminal.
8. Route diagnostics explain loopback/ADB/emulator state.
9. Notifications can be simulated from ProjectView/Comms deltas.
10. Lifecycle/admin actions are scoped, confirmed, and validated only against
    isolated runtime.

## Implementation Packages

Work in coherent packages. Each package should include tests, plan-tree notes,
and a commit when possible.

Before each package, run an explicit reuse check:

- identify the existing app/source module, library, or open-source project that
  should be adapted;
- record why it fits or why a small CCB-specific implementation is necessary;
- keep attribution/license obligations visible when code is imported or
  substantially copied;
- do not rewrite mature terminal, tmux, Markdown, notification, secure-storage,
  pairing, reconnect, or WebSocket behavior from scratch without a recorded
  reason.

Progress note 2026-06-21: app `be5f345` completed the script-level local
gateway smoke coverage for selected-agent `/terminal-history`; app `9a4a0c2`
added the first Android Emulator UI smoke that drives app screens, fake
selected-agent reading/history scrolling, local gateway claim, route
diagnostics, and selected-agent live terminal opening; app `5b72330` extends
that AVD smoke to drive live terminal send, paste, size sync, and reconnect
through the selected-agent terminal UI; app `6d2fab7` adds a local terminal
token-renewal smoke that injects an expired terminal frame and proves handle
renewal with resume cursor and preserved geometry; app `14e68a7` adds local
ProjectView/Comms notification synthesis and notification-center deep links
through model/widget tests; source `e1ace0b0` and app `b8d9507` add scoped
safe lifecycle routes and app controls for wake/open/close/stop without raw
tmux kill operations; app `f08754f` extends the source-backed Android Emulator
wrapper to prove real paired wake/open/close in the normal smoke and confirmed
stop in a separate throwaway runtime via `--include-lifecycle-stop`; app
`28dc384` adds the first relay route metadata guards and local relay pairing
coverage without a public relay dependency; app `f8c5a25` adds the first
fake/local `RelayGatewayTransport` envelope adapter coverage and proves relay
operation envelopes stay opaque at the JSON surface; app `3bd2ca1` adds the
app-side relay frame, handshake, and host-registration contract tests without
public relay infrastructure; source `1b438505` adds the source-side local
relay harness, fake outbound client, and `ccb mobile serve --route-provider
relay` local `relay_outbound` summary without public networking; source
`1112559d` and app `c10e4f1` add local relay health diagnostics for unknown
host, disconnected host, relay unreachable, stale device, and host-fingerprint
mismatch without public relay infrastructure. E9 now needs the remaining
emulator-only acceptance checklist consolidation and refreshed AVD smoke
evidence, not a public relay or Cloudflare gate.

1. **E1: Emulator Harness Baseline**
   - Verify Flutter SDK, Android SDK, AVD `ccb_mobile_api35`, adb, and debug
     build.
   - Start/stop emulator cleanly when needed.
   - Ensure `adb reverse tcp:8787 tcp:8787` is part of the smoke path.

2. **E2: Selected-Agent Workspace**
   - Keep top agent switcher and one selected-agent body.
   - Add selected-agent state, focus/refresh affordances, Comms/content slots,
     readable terminal history slot, and explicit Open Terminal action.

3. **E3: Structured Content Reader**
   - Add Markdown renderer with headings, lists, code, tables, links, copy,
     raw source, and safe link policy.
   - Add math rendering or a clear formula fallback.
   - Prefer CCB content ids, replies, Comms, and artifact refs over terminal
     scraping.

4. **E4: Readable Terminal History**
   - Add gateway/source route or local fixture for current pane plus retained
     tmux scrollback when needed.
   - Clean ANSI/control noise and group command/log/code/diff/error blocks.
   - Support vertical scrolling, refresh, copy block, and stale-evidence labels.
   - Preserve raw terminal for fidelity and input.

5. **E5: Local Pairing And Route Diagnostics**
   - Validate manual/QR claim with emulator using loopback/ADB reverse.
   - Show route health, origin-only URL rules, and server profile consistency.
   - Keep Cloudflare and relay live routes out of the emulator gate.

6. **E6: Raw Terminal Control Fallback**
   - Keep terminal WebSocket/open-token flow working from selected agent/window.
   - Verify input, paste, resize, background/resume, reconnect, cursor resume,
     and token renewal in emulator.

7. **E7: Notifications And Deep Links**
   - Simulate completion, failed, blocked, and callback-needed states from
     ProjectView/Comms deltas.
   - Deep-link back to project, selected agent, Comms/content, or terminal.
   - Validate emulator notification behavior when available; otherwise add
     widget/integration coverage and document emulator limitation.

8. **E8: Safe Lifecycle Controls**
   - Add wake/open/close/stop controls only through CCB authority.
   - Validate against isolated runtime.
   - Never call raw `tmux kill-server`.

9. **E9: Emulator End-to-End Smoke**
   - Produce a repeatable script or checklist that starts isolated runtime,
     serves loopback gateway, sets adb reverse, installs/runs debug APK, claims
     gateway, selects agents, reads content/history, opens terminal, sends input,
     verifies reconnect, and records evidence.

## Verification Gates

Run the smallest reliable set for each package, then broaden before final
completion.

App checks:

- `/home/bfly/.local/share/flutter-sdks/3.44.2/flutter/bin/flutter test`
- `/home/bfly/.local/share/flutter-sdks/3.44.2/flutter/bin/flutter build apk --debug`
- `flutter analyze` when available; if the Dart Analysis Server hits the known
  `Too many open files` failure while printing `No issues found!`, record the
  exact output and keep moving only after tests/build pass.

Source checks when `/home/bfly/yunwei/ccb_source` changes:

- focused source tests for the changed mobile gateway/content/history/focus
  contract;
- source `git diff --check`;
- separate source commit before mobile plan-tree evidence.

Emulator checks:

- AVD `ccb_mobile_api35` boots.
- APK installs and starts.
- `adb reverse tcp:8787 tcp:8787` is active.
- Gateway is loopback-bound at `127.0.0.1:8787`.
- App pairs/claims through local profile.
- Agent switching does not open terminal.
- Selected-agent workspace displays Markdown/content and readable history.
- Vertical history scrolling works for long retained tmux scrollback.
- Open Terminal can control the selected agent/window.
- Reconnect/token renewal is visible and recoverable.
- Route diagnostics explain local emulator state.

## Current Emulator-Only Evidence Map

The detailed checklist lives in
[topics/emulator-only-acceptance-checklist.md](topics/emulator-only-acceptance-checklist.md).
It records accepted local evidence, AVD smoke commands, accepted deferrals, and
the final audit surface before this long-running goal can be marked complete.

- App launch and AVD harness: app `9a4a0c2` adds the AVD UI smoke harness;
  app `5b72330` and `f08754f` extend it through terminal controls and live
  lifecycle wake/open/close with `adb reverse` against loopback gateway.
- Local pairing/claim and route diagnostics: app `28dc384` covers relay
  metadata guards; app `c10e4f1` adds relay host-state and fingerprint
  diagnostics; source `1112559d` adds matching local relay diagnostic states.
- Project/agent discovery and selected-agent switching: app `1c0023b` lands
  the top agent switcher plus one selected-agent workspace; later widget and
  AVD tests keep agent taps from opening raw terminal by default.
- Structured Markdown/content reader and readable terminal history: app
  `52ab628`, source `d8c8cc17`, app `26607d8`, and app `be5f345` cover
  structured content, readable tmux scrollback, gateway `/terminal-history`,
  and loopback smoke assertions for pane-scoped history.
- Explicit raw terminal fallback and controls: source `dfcb7af7`,
  `8ce445f1`, app `faa3039`, `f3e2d78`, `5b3c985`, `300691f`, `3bebca4`,
  `eef4d09`, `5b72330`, and `6d2fab7` cover terminal open, WebSocket/PTy
  frames, input, paste, resize, reconnect, resume cursor, and token renewal.
- Simulated notifications/deep links: app `14e68a7` covers ProjectView/Comms
  notification synthesis and in-app deep links through model/widget tests.
- Safe lifecycle controls: source `e1ace0b0`, app `b8d9507`, and app
  `f08754f` cover scoped wake/open/close/stop controls, confirmation, no raw
  tmux kill operations, and paired AVD lifecycle smoke.
- E9 checklist consolidation: `topics/emulator-only-acceptance-checklist.md`
  now records the completion gates, evidence sources, and next audit commands.
- Current AVD proof: 2026-06-21 normal smoke on `127.0.0.1:18877` and
  throwaway stop smoke on `127.0.0.1:18879` both returned `status: ok`.
- Completion audit: 2026-06-21 checklist audit accepted every emulator-only
  gate or explicit goal-level deferral.

## Completion Rule

Do not mark this goal complete until all emulator-only gates pass or have an
explicit accepted deferral in plan tree:

- Android emulator app launch;
- local pairing/claim;
- ProjectView/project/agent discovery;
- selected-agent switching;
- structured Markdown/content reader;
- readable terminal history with vertical scrolling;
- explicit raw terminal fallback;
- terminal input/paste/resize/reconnect/token renewal;
- route diagnostics for loopback/ADB;
- simulated notifications/deep links;
- safe lifecycle controls against isolated runtime;
- source/app tests and debug build;
- repeatable emulator smoke evidence;
- plan-tree status/evidence update;
- coherent mobile/source commit history.

Public remote access is not part of completion for this goal. Relay and
Cloudflare remain route-provider design constraints, fake/local test targets,
or deferred follow-up work.

## Commit And Plan Discipline

- Every batch starts by reading plan tree and current git status.
- Every batch ends with plan-tree status/evidence and a commit when possible.
- During long runs, do not go beyond 60-90 minutes without either a coherent
  commit or an explicit `implementation-status.md` progress/blocker record.
- `implementation-status.md` should keep Current Phase, Last Landed, Next
  Target, Active TODO, Blocked By, and Last Verified accurate for handoff.
- Larger evidence belongs in `history/evidence-index.md` or linked topic files,
  not as repeated logs inside active status.
- Keep commits small and reversible.
- Do not commit `.ccb/agents`, `.ccb/ccbd`, logs, build outputs, secrets,
  tokens, local SDK configs, or emulator runtime state.
- Mobile repo and CCB source repo commits stay separate.
- If blocked, update `implementation-status.md` with blocker, evidence, and
  next action before stopping.
