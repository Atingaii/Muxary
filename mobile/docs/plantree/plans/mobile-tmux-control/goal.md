# CCB Mobile Landing Goal

Date: 2026-06-18

## Purpose

This document is the reusable goal prompt for landing the full CCB Mobile
phone/iPad project.

Use it when starting or resuming a long-running implementation goal. The goal
is intentionally implementation-driving: it requires architecture first,
open-source reuse before greenfield work, regular plan-tree updates, and
regular coherent commits.

## Invocation

Use this file as the stable goal contract. When invoking a new long-running
agent run, give the agent the objective and call block below.

Direct copy/paste invocation:

```text
读取并执行 `/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal.md`
作为当前长期 goal。

你要端到端落地 CCB Mobile 手机/iPad 开发项目。默认产品体验必须是
Agent-first：顶部显示 agent 切换列表，主体只显示一个 selected agent
工作页，Markdown/content 以结构化阅读视图呈现，raw terminal/tmux stream
只作为显式 Open Terminal 控制/调试入口。不要先从零写代码；先
resume plan tree，读取 `docs/plantree/README.md`、本计划 README、
`implementation-status.md`、`roadmap.md`、active decisions/topics 和最新
commit 状态。确认当前 Current Phase、Next Target、Blocked By、Last
Verified 后，再进入工作。

执行纪律：
- Lead 只负责任务推进：拆分 coherent packages、派发 worker、组织
  reviewer 审查、维护 plan tree、汇总验收和决定下一包；除计划/状态文档
  或用户明确授权的紧急小修外，不直接落盘实现代码。
- 具体落盘和执行由 CCB workers 完成。每个 worker 包必须包含目标、范围、
  touched files、验证命令、风险和提交说明。
- 每个非文档实现包必须进入 reviewers 迭代。reviewer 以代码审查姿态先列
  bug、回归风险和缺失测试；worker 修复或 lead 明确记录接受/延期后，
  才能进入下一包。
- 先做或更新合理架构设计，再进入实现。
- 优先复用并二次修改成熟开源库和已有 CCB 源码能力；agent workspace、
  agent switcher、terminal、tmux、SSH/WebSocket、gateway、QR pairing、
  Markdown/math、notification、secure storage、reconnect 等核心能力
  不能默认从头写。
- 每个工作批次遵循：resume plan tree -> architecture/reuse check ->
  implement coherent package -> verify -> update plan tree -> commit。
- 每个批次开始和结束都要更新 plan tree；关键决策、阻塞、验证结果、
  scope 变化必须及时写入 plan tree。
- 长时间执行时，60-90 分钟内必须至少完成一次 coherent commit，或在
  `implementation-status.md` 写清当前状态、阻塞、验证和下一步。
- 修改 `/home/bfly/yunwei/ccb_source` 时，必须在 CCB 源码库独立检查、
  测试和提交；mobile 仓库和 source 仓库不要混合提交。
- 不提交 runtime state、secrets、build artifacts、`.ccb/agents`、
  `.ccb/ccbd`、日志、token 或本地 SDK 配置。
- 大包实现要拆分给 CCB worker/reviewer，并把结果回写为 plan-tree
  evidence。

不要把 goal 标记为 complete，直到 Android app、gateway route、
CCB project discovery/control、agent-first single-agent workspace、
top agent switcher、explicit raw-terminal fallback、Markdown/content reader、
notification path、remote access route、plan-tree evidence、verification
record 和 coherent commit history 都已落地，或已在 plan tree 中明确接受
延期/裁剪。
```

Recommended direct call:

```text
请读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal.md`
作为当前长期 goal。

目标是端到端落地整个 CCB Mobile 手机/iPad 开发项目。默认 UI 目标是
Agent-first：顶部 agent 切换，主体只显示一个 selected agent 工作页；
项目路径、gateway、pairing、runtime 诊断进入连接详情/设置，不常驻主
页面；raw terminal 是显式控制/调试 fallback，不是默认阅读界面。先恢复并更新
plan tree，检查 `implementation-status.md`、roadmap、decisions、
blocker 和最新 commit；在正式编码前，必须先确认或补齐合理架构设计和
开源库复用/二改方案。实现时优先复用成熟开源库和已有 CCB 源码能力，
不要从头手写 agent workspace、agent switcher、terminal、tmux、pairing、
gateway、Markdown、notification 等核心能力，除非 plan tree 已记录
license、平台、安全或边界原因。

执行过程中保持循环：lead resume plan tree -> lead design/reuse check ->
lead 拆包并派发 worker -> worker implement coherent package -> worker
self-verify -> reviewer review -> worker/reviewer 迭代到无阻断问题 -> lead
record progress -> coherent commit。每个工作批次开始和结束都要更新 plan
tree；每个关键决策、阻塞、验证结果、scope 变化都要及时记录。长时间
执行时，60-90 分钟内必须至少产生一个 coherent commit 或在
`implementation-status.md` 写清状态、阻塞、验证和下一步。提交要小、
可回滚，不提交 runtime state、secrets、build artifacts、`.ccb/agents`、
`.ccb/ccbd`。修改 `/home/bfly/yunwei/ccb_source` 时必须在 CCB 源码库中
独立检查、测试和提交。

不要把 goal 标记为 complete，直到 Android app、gateway route、
CCB project discovery/control、agent-first single-agent workspace、
top agent switcher、explicit raw-terminal fallback、Markdown/content reader、
notification path、remote access route、plan-tree evidence、verification
record 和 coherent commit history 都已落地，或已在 plan tree 中明确接受
延期/裁剪。
```

Objective:

```text
端到端落地以单 Agent 工作页为默认体验的 CCB Mobile 手机/iPad 开发项目，并持续维护 plan tree、进度记录和阶段性 commit。
```

Call block:

```text
Read `/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal.md`
and execute it as the active project goal.

Deliver the whole CCB Mobile phone/iPad project incrementally as an
agent-first remote controller: top agent switcher, one selected-agent
workspace, structured Markdown/content reading, and raw terminal only as an
explicit control/debug fallback. Before coding,
resume the plan tree, inspect current status/blockers, and keep the
architecture/reuse design current. Prefer adapting mature open-source mobile
agent workspace, terminal, tmux, pairing, gateway, Markdown, and notification
libraries over greenfield implementation. Update the plan tree at the start/end of each work
batch and after every decision, blocker, verification result, or scope change.
Lead owns orchestration only: split work into packages, dispatch CCB workers,
route implementation packages through reviewers, maintain plan-tree evidence,
and synthesize the next target. Workers own implementation and self-verification;
reviewers own bug/regression/test-gap review. Create small coherent commits for
each architecture package, source package, passing test point, or plan-only
checkpoint; during long runs, do not go more than 60-90 minutes without either
a commit or an explicit status/blocker record. Never commit runtime state,
secrets, build artifacts, `.ccb/agents`, or `.ccb/ccbd`.
```

Recommended first instruction to the agent:

```text
Read `/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal.md`
and execute it as the active project goal. Start by resuming the plan tree,
checking current blockers, and producing or updating the architecture/reuse
design before implementation.
```

Current direct call:

```text
Read `/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal.md`
and execute it as the active project goal. Resume from
`implementation-status.md`, keep `docs/plantree` current, commit coherent
packages regularly, and continue with the current Next Target unless a newer
decision or blocker supersedes it.
```

Completion rule:

```text
Do not mark this goal complete until the Android app, gateway route, CCB project
discovery/control, agent-first single-agent workspace, top agent switcher,
explicit raw-terminal fallback, Markdown/content reader, notification path,
remote access route, plan-tree evidence, verification record, and coherent
commit history have all landed or have explicit accepted deferrals in the plan
tree.
```

## Goal Prompt

目标：端到端落地以单 Agent 工作页为默认体验的 CCB Mobile 手机/iPad
开发项目，并持续维护
plan tree、进度记录和阶段性 commit。

项目目标：

在 `/home/bfly/yunwei/ccb_source/mobile` 中落地一个原生 Flutter
Android/iOS/iPadOS App，作为 server-side CCB 项目的移动远程控制器。
App 默认进入 CCB-aware 单 Agent 工作页：顶部显示 agent 切换列表，主体
只显示一个 selected agent 的状态、Comms、Markdown/content、可上下滚动的
可读化终端历史、操作和必要上下文。Raw terminal/tmux stream 是显式
Open Terminal 控制或调试入口，不是默认阅读界面。App 还负责项目发现、
agent/window focus、Markdown/math
阅读、通知、CCB Relay 默认远程访问、Cloudflare Tunnel 高级远程访问和
后续 lifecycle 控制。

核心原则：

- Lead/worker/reviewer 分工必须保持清晰：lead 只推进任务、拆包、派发、
  记录、验收和决定下一步；workers 负责具体实现、文件落盘、格式化、
  focused/full verification 和实现提交；reviewers 负责独立审查 bug、
  回归风险、架构漂移和测试缺口，并推动 worker 修复或记录可接受延期。
- 先做合理架构设计，再实现。架构未明确前不进入大规模编码。
- 优先复用并二次修改成熟开源项目/库，不从头手写核心能力。
- 对 terminal、tmux、SSH/WebSocket、QR pairing、gateway、Markdown/math、
  notification、secure storage、reconnect 等成熟能力，必须先找可复用
  开源库或可参考实现；只有 license、平台、架构边界或安全原因不适合时，
  才允许写 CCB 专用实现，并把原因写入 plan tree。
- 移动端首选复用方向：ServerBox、MuxPod、tmux-mobile、Paseo，以及
  相关 Flutter terminal、SSH、WebSocket、Markdown、notification 库。
- 复用前必须检查 license、维护状态、平台支持、改造成本、归属边界
  和 attribution 要求。
- 如果 AGPL 可接受，可 fork/改造 ServerBox/Paseo；如果不可接受，只能
  复用兼容 license 的代码或重新实现必要思想。
- App 必须是 CCB-aware remote controller，不是通用 SSH/tmux 客户端，
  也不在手机本地运行 provider/agent。
- 默认体验必须是 CCB-aware single-agent workspace，不是 tmux stream。
  顶部优先展示 agent 切换，主体只展示一个 selected agent；项目路径、
  gateway URL、pairing code、runtime id、诊断信息进入连接详情/设置，
  不常驻第一屏。
- 结构化 CCB content 是 Markdown/math 阅读的权威来源。不要从 tmux
  capture 推断权威 Markdown；pane snapshot/readable terminal history
  只能做可读化历史、预览或 fallback。
- Raw terminal/tmux stream 必须保留为明确可进入的控制/调试模式，但
  agent tap 的默认行为应是切换 selected agent，而不是直接打开终端。
- Selected-agent workspace 默认应优先展示可读化 agent 工作历史：结构化
  CCB content、Comms/replies/artifacts，以及来自 tmux scrollback 的
  best-effort readable terminal history。用户必须能上下拖动浏览历史，而
  不只是看到当前屏幕截图。
- 默认项目信息架构以
  [Decision 012](decisions/012-agent-first-project-workspace.md) 为准。

工程边界：

- 移动端代码放在 `/home/bfly/yunwei/ccb_source/mobile`，首选路径 `app/`。
- 不把本仓库当作 CCB 源码库。
- CCB 源码只在需要且经过 ready-check 后，才在
  `/home/bfly/yunwei/ccb_source` 中修改。
- CCB 权威来自现有 `project_view`、`project_focus_agent/window`、
  namespace epoch、tmux socket/session。
- `pane_id` 只能作为 evidence，不能单独授权输入、focus 或破坏性操作。
- CCB Relay 是普通用户默认非 LAN 远程路线；Cloudflare Tunnel 是
  advanced/self-hosted route provider。必须保留 relay-compatible
  `RouteProvider` 边界。

架构设计必须先完成：

1. 写清 App 模块划分：host/profile、pairing、repository、transport、
   agent workspace、agent switcher、terminal、project view、
   agent/window focus、content reader、readable terminal history、
   notification、lifecycle。
2. 写清默认 UI 信息架构：top agent switcher、single selected-agent
   workspace、connection details sheet、Markdown/content reader、
   scrollable readable terminal history、explicit Open Terminal action。
3. 写清 transport 边界：`GatewayTransport`、`SshTransport`、
   `RouteProvider`。
4. 写清 CCB 数据模型：Host、Project、Window、Agent、TerminalTarget、
   ContentItem、Notification、Scopes。
5. 写清开源库复用清单：库名、license、用途、改造点、风险、替代方案。
6. 写清测试策略：model tests、tmux command tests、fake transport tests、
   Android emulator smoke test、isolated CCB project terminal slice。
7. 架构文档必须落在 plan tree 或 `app/docs/`，并从 plan tree 可发现。

执行顺序：

1. 每次恢复时先读取 plan tree 当前状态、blocker、Next Target 和最新
   commit，不从过期记忆继续。
2. 解决当前阻塞：确认移动端 license 选择，安装或暴露
   Flutter/Dart/Android SDK/adb/emulator。
3. 完成 architecture/reuse design，并更新 plan tree。
4. 建立 `app/` Flutter 工程基线，优先 Android emulator 验证。
5. 实现 CCB-first fake transport、ProjectView fixture、数据模型、顶部
   agent switcher、single selected-agent workspace 和显式 Open Terminal
   action。
6. 实现 Markdown/content reader 和 readable terminal history：
   Comms、ask/callback、reply、artifact 优先走结构化内容；tmux
   capture/scrollback 只作为 best-effort 可读历史；raw source 和 raw
   terminal 是 fallback。
7. 加 socket-aware tmux command layer 测试，确保生成
   `tmux -S <project_socket> attach-session -t <session>`，并拒绝默认
   `tmux attach`。
8. 完成隔离 CCB 测试项目 raw terminal vertical slice：输入、paste、
   resize、background/resume、reconnect；该 slice 是显式控制模式，不是
   默认项目页。
9. 再推进 QR pairing、GatewayTransport、CCB Relay、Cloudflare Tunnel
   advanced route、live ProjectView、agent/window focus、notifications、
   lifecycle controls。

工作批次循环：

1. Resume：读 `docs/plantree/README.md`、本计划 README、
   `implementation-status.md`、roadmap、active decisions 和当前相关 topic。
2. Design：确认架构、复用库、license、接口边界和验收标准仍然成立。
3. Dispatch：lead 把当前 coherent package 拆成 worker 指令，写清目标、
   范围、文件、验收、验证命令、禁止事项和预期输出；需要结果闭环时使用
   CCB callback，不把实现细节留在 lead 侧临场补写。
4. Implement：worker 只做当前 coherent package，优先二改/复用成熟
   开源能力，并提交改动、验证结果、风险和剩余问题。
5. Review：至少一个 reviewer 对非文档实现包做代码审查；阻断问题交回
   worker 修复，非阻断问题由 lead 写入 plan tree 或下一包。
6. Verify：运行与改动匹配的最小可靠检查；移动端至少保持
   `flutter analyze`、`flutter test`、Android build/smoke 的节奏。
7. Record：lead 把 worker/reviewer 结果、决策、阻塞、验证证据、
   Next Target 回写 plan tree。
8. Commit：由 worker 或被授权执行者提交小而可回滚的 commit；不能提交
   时在状态文档写明原因。

Plan tree 维护要求：

- 每次开始工作先读 `docs/plantree/README.md`、目标计划 README、
  `implementation-status.md`、roadmap 和相关 decisions。
- 每完成一个阶段、一个关键包、一次架构决策或发现阻塞，都要更新
  plan tree。
- 至少在每个工作批次结束时更新：
  - `implementation-status.md` 的 Current Phase、Next Target、
    Active TODO、Blocked By、Last Verified、Last Landed；
  - `roadmap.md` 的 Done/In Progress/Next；
  - 必要时新增或更新 decisions/open-questions/topics。
- 不允许实现和计划树长期漂移。实现发现必须及时回写为 plan-tree
  evidence 或 decision。

定时进度要求：

- 每个工作批次开始时，先确认 `implementation-status.md` 的 Current Phase、
  Next Target、Active TODO 和 Blocked By 是否仍然准确。
- 每完成一个可验证 checkpoint，更新 `Last Verified`；如果 checkpoint
  会影响后续实现选择，新增或更新 decision。
- 长时间执行时，60-90 分钟内必须至少完成一次 plan-tree 状态更新或
  coherent commit；无法提交时，要在 `implementation-status.md` 写明原因、
  阻塞和下一步。
- 如果用户或上游 agent 中途给出新要求，先判断它是否改变 Current Phase、
  Next Target、架构边界、license 或验收标准；改变时先更新 plan tree，
  再继续实现。

Commit 要求：

- 做阶段性、可回滚的小 commit。
- 每完成一个 coherent package、架构文档、可运行 slice、测试通过点或
  plan-tree 状态更新，都应提交一次。
- 长时间开发时，最多每 60-90 分钟形成一次可解释 commit；如果代码
  未通过基本检查，则先整理为 WIP-safe 状态或只提交文档/计划更新。
- 每次 commit 前必须检查 `git status`，不要误提交 `.ccb/agents`、
  `.ccb/ccbd`、日志、build 产物、密钥、token、Android
  `local.properties` 等运行态文件。
- implementation commit 应包含对应 plan-tree 更新；纯计划更新也可以
  单独 commit。
- 修改 `/home/bfly/yunwei/ccb_source` 时必须在 CCB 源码库内独立检查、
  测试、提交，不要混到 mobile 仓库 commit。

验收标准：

- Android emulator 能启动 App。
- 首页展示 CCB 项目/agent fixture，而不是通用服务器面板。
- 项目页默认顶部是 agent switcher，主体只显示一个 selected agent
  工作页；项目/gateway/pairing/runtime 诊断不占用第一屏。
- Agent tap 默认切换 selected agent；raw terminal 只能通过显式
  Open Terminal 控制/调试入口进入。
- Markdown/content reader 以结构化 CCB 内容为权威来源，并保留 raw
  source/pane snapshot fallback。
- Selected-agent workspace 提供可上下滚动的 readable terminal history：
  MVP 至少覆盖当前 tmux pane scrollback；长期完整历史需要 recorder/journal
  方案，不误称为已覆盖所有历史。
- 模型测试证明 `pane_id` alone 不能构成 terminal input target。
- tmux 命令测试覆盖 socket path、session name、agent/window target、
  multiline paste。
- 第一条真实 raw terminal slice 连接的是 CCB project tmux socket/session。
- App 关闭或断线重连不会停止 server-side CCB。
- 架构设计、开源库复用方案、进度记录、验证证据和 commit 历史完整
  可追溯。
