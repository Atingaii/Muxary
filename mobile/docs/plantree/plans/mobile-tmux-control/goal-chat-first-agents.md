# CCB Mobile Chat-First Agents Goal

Date: 2026-06-21

## Purpose

This document is the reusable goal prompt for landing the next CCB Mobile
product phase: every configured CCB agent should appear as a standard
ChatGPT/DeepSeek-style conversation, with a pane-backed timeline and composer,
while raw terminal remains an explicit advanced fallback.

Use this goal when starting or resuming a focused implementation run after the
emulator-only baseline. The run should prioritize local Android Emulator and
loopback gateway validation before production relay, public routes, physical
devices, release packaging, or iOS validation.

## Invocation

Use the following block as the primary copy/paste prompt.

Primary goal prompt:

```text
读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-chat-first-agents.md`
作为当前长期 goal。

目标：把 CCB Mobile 的每个 configured agent 都落地成类似 ChatGPT/DeepSeek
的通用对话形态，但输入和读取必须直接绑定真实 selected tmux pane。App 默认
项目页必须是：顶部 agent/window 切换列表；主体只展示当前 selected agent
的对话时间线；底部固定/可折叠多行输入框和发送按钮。切换到任意 agent 后，
都看到同一种标准聊天界面，而不是 dashboard、裸 tmux stream 或只读状态页。

必须先 resume plan tree：读取 `docs/plantree/README.md`、本计划 README、
`implementation-status.md`、`roadmap.md`、
`decisions/014-chat-first-agent-workspace.md`、
`decisions/015-pane-backed-chat-input.md`、
`topics/chat-first-agent-workspace.md`、`topics/mobile-api-contract.md` 和当前
git status。确认 Current Phase、Next Target、Blocked By、Last Verified、
允许写入范围和 dirty worktree 后再实现。

产品要求：
- 每个 agent 都有一致的 conversation surface：timeline + composer。
- timeline 要能展示 user message、agent reply、callback、Comms、
  status/tool event、artifact/content card、best-effort terminal history block。
- composer 是默认输入方式：支持多行输入、发送、pending/sent/failed-or-echoed、
  每 agent draft 保留、软键盘不遮挡。
- 默认输入必须直接写入 selected agent 的 CCB-validated tmux pane，通过
  terminal session 的 paste/input frames 实现；不要再包一层 ask/message。
- timeline 的主读取来源必须是 selected pane 的 live output 和
  `/terminal-history`，再合并 Comms/artifacts/status 等结构化上下文。
- raw terminal/tmux stream 保留为明确的 Open Terminal 全控制/调试入口。
- project path、gateway URL、pairing code、runtime id、route diagnostics、
  lifecycle/admin 和 terminal state 必须放到详情/菜单/设置中，不占据第一屏。

架构要求：
- 先补齐或更新 chat-first architecture/reuse 设计，再编码。
- 优先复用已有 Flutter 组件、Markdown renderer、secure storage、
  WebSocket/gateway terminal 代码、terminal-history、ProjectView/Comms 能力；
  不从头手写已有成熟能力，除非 plan tree 记录 license、平台、安全或边界原因。
- 新增/改造 selected-agent pane-chat controller，复用
  `GatewayTerminalTransport` open/renew/reconnect、paste/input、output stream
  和 readable history。
- 在 `/home/bfly/yunwei/ccb_source` 中只在 terminal/history/pane validation
  缺契约时做小范围 mobile gateway/source 修改；source repo 与 mobile repo
  必须分开检查、测试和提交。
- composer send 默认需要 `terminal_input` scope；`ask`/`message_submit` 只作为
  兼容或未来显式 action，不是默认聊天权限。
- 终端输入重试必须保守：不能因为网络重试自动重复向 pane 发送同一段输入。

本阶段验收只要求本地虚拟机优先：
- 使用 Android Emulator/AVD、loopback gateway、`adb reverse`、isolated
  CCB runtime、Flutter tests、source focused tests、debug APK 和 emulator
  smoke。
- 不把 Cloudflare、域名、公网 IP、生产 relay、真机、iOS、应用商店发布
  作为完成条件。

执行循环：
resume plan tree -> architecture/reuse check -> implement coherent package ->
verify locally/emulator -> update plan tree evidence -> commit。

提交和记录纪律：
- 每个批次开始/结束都更新 plan tree 的状态、证据、阻塞和下一步。
- 长时间执行时，60-90 分钟内必须至少产生一个 coherent commit，或在
  `implementation-status.md` 写清状态、阻塞、验证和下一步。
- 不提交 `.ccb/agents`、`.ccb/ccbd`、secrets、token、日志、build artifacts、
  本地 SDK/emulator/runtime state。

不要把 goal 标记为 complete，直到：每个 configured agent 都能在手机 UI 中
以统一聊天形态打开；agent switcher 切换不会丢失每 agent draft/scroll；
composer 能本地输入、发送、显示 pending/sent/failed-or-echoed；paired gateway
能通过 terminal input/paste 写入 selected pane；timeline 能从 live output 或
terminal-history 读回 pane echo/output，并合并 Comms/content/status；Open
Terminal 仍是显式全控制入口；local AVD loopback smoke 覆盖 pane-backed
type-send-read；plan-tree evidence 和 coherent commits 完整。
```

Short objective:

```text
把 CCB Mobile 的每个 configured agent 都落地成统一的 pane-backed
ChatGPT/DeepSeek 式对话界面，并用本地 Android Emulator loopback 验证
composer 直写 tmux pane 的 type-send-read。
```

Short call:

```text
请读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-chat-first-agents.md`
作为当前长期 goal。目标是让每个 CCB agent 都成为一个统一聊天会话：
顶部 agent/window switcher，主体 selected-agent timeline，底部 composer。
普通输入必须直接写入 selected tmux pane，不走 ask/message 包装。先 resume
plan tree 和 Decision 015，再按 pane-chat controller、terminal input/paste、
terminal-history/live output timeline、paired-gateway wiring、AVD smoke 的
顺序落地，并持续更新 plan tree 和小步提交。
```

## Scope

### In Scope

- Flutter app chat-first selected-agent UI under `app/`.
- Per-agent timeline and composer model.
- Fake repository conversation fixtures and widget tests.
- Selected-agent pane-chat controller and terminal session reuse/renewal.
- Terminal-history/live output timeline ingestion and echo deduplication.
- Paired-gateway chat wiring and device scopes.
- Local AVD loopback type-send-read smoke.
- Plan-tree updates and coherent commits.

### Out Of Scope

- Production public relay deployment.
- Cloudflare or public DNS setup.
- Physical device acceptance.
- App Store/TestFlight/Play Store release.
- Full terminal journal.
- Rich file attachment workflow.
- Making the phone run CCB agents locally.
- Replacing CCB message authority with mobile-only state.

## Required Product Shape

1. Project opens into a chat-first agent workspace.
2. Top area is the agent switcher.
3. Exactly one selected agent is displayed at a time.
4. Every agent uses the same universal chat layout.
5. Main body is a scrollable timeline.
6. Bottom composer is always available when chat is allowed.
7. Timeline entries are typed and render appropriately.
8. Markdown replies and Comms are readable by default.
9. Terminal history is a labeled best-effort evidence block, not the reply
   source of truth.
10. Raw terminal is explicit Open Terminal full-control mode, while the compact
    composer still sends to the selected pane through terminal transport.

## Landing Packages

### C1: Fake Chat Shell

- Add typed conversation item models for fake data.
- Add selected-agent timeline UI.
- Add bottom multiline composer.
- Preserve draft and scroll state per agent.
- Keep current agent switcher behavior.
- Hide connection/runtime details from first viewport.
- Add widget tests for agent switching, draft preservation, composer layout,
  pending/sent/failed states, and explicit Open Terminal.

### C2: Pane Chat Boundary

- Add a selected-agent pane-chat controller above `GatewayTerminalTransport`.
- Reuse terminal open/renew/reconnect, paste/input, output stream, and
  terminal-history fetch paths.
- Add DTOs/state for conversation items, pane cursors, pending sends, echo
  matching, and conservative retry.
- Add fake implementation and transport tests.
- Use terminal input/paste as the default chat send path.

### C3: Pane-Backed Chat Transport

- Reuse the existing terminal-open, WebSocket frame, paste/input, renewal, and
  `/terminal-history` contracts whenever sufficient.
- Add source/gateway changes only if selected-agent pane validation, history,
  or live-output access is missing.
- Require `terminal_input` scope for default composer sends.
- Add echo-dedup and conservative retry rules that do not replay pane input
  automatically.
- Add focused app/source tests.

### C4: Paired Gateway App Wiring

- Request/store `terminal_input` and content/view scopes during pairing.
- Wire the composer to the selected agent terminal session.
- Render pending/sent/failed-or-echoed updates from terminal send/echo state.
- Poll history and/or stream terminal output after send.
- Render pane output plus supplemental reply/callback/Comms/content cards.
- Keep route diagnostics, lifecycle, and Open Terminal available.

### C5: Emulator Smoke

- Start isolated CCB runtime and loopback gateway.
- Install/run app on AVD.
- Pair through loopback.
- Select at least two agents.
- Type and send a message to one agent.
- Switch away/back and verify draft/scroll behavior.
- Observe pane echo/output/history or explicit fallback state.
- Verify Open Terminal remains explicit and still works.

## Acceptance Criteria

- Every configured agent opens as the same chat-style surface.
- Soft keyboard does not hide the composer.
- Agent switching preserves draft and scroll state per agent.
- Sending a message writes to the selected tmux pane through the gateway
  terminal transport, without calling the ask/message route.
- Chat send requires `terminal_input` scope because the compact chat surface is
  a pane input surface.
- Timeline displays user messages, agent replies/callbacks/Comms/status, and
  Markdown content.
- Failed sends can be retried only with explicit user intent and without
  automatic duplicate pane input.
- Connection details and terminal controls are secondary.
- Local AVD loopback smoke covers the complete pane-backed type-send-read path.

## Completion Rule

Do not mark this goal complete until the current pane-backed C1-C5 packages are
landed, verified locally, and recorded in plan tree with commits. Any deferred
part must have an explicit accepted deferral in `implementation-status.md` or a
linked decision/topic.

## Landing Evidence

Status: Completed for the old local Android Emulator ask/message acceptance
gate on 2026-06-21. Superseded as the default send path by
[Decision 015](decisions/015-pane-backed-chat-input.md); a replacement
pane-backed AVD gate is now required.

- C1 fake chat shell: app `6a1b64e`.
- C2 repository/gateway conversation boundary: app `b1a4227`.
- C3 CCB source selected-agent conversation/message routes: source
  `61109474`.
- C4 paired-gateway app chat wiring: app `b924d07`.
- C5 local AVD chat type-send-read smoke: app `aff2180`.

Final local gate:

```bash
tools/mobile_emulator_ui_smoke.py --gateway-listen 127.0.0.1:18887 \
  --start-timeout 60 --gateway-timeout 30 --flutter-timeout 260
```

Result: `status: ok`; disposable agents `mobile_probe, mobile_peer`; Flutter
integration `All tests passed!` for 2 tests; post-harness
`mobile_terminal_target_ok: true`.
