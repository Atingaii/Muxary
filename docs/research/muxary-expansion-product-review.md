# Muxary 扩展：两轮真实产品评审与复用证据

- 日期：2026-11-11。
- 状态：**产品/来源研究已记录；本轮双视图、交互与性能验收尚待执行/补录，不能据本文宣称实现或性能通过**。
- 关联：[扩展 SPEC](../specs/muxary-workspace-canvas.md)、[ADR-0003](../adr/0003-workspace-and-canvas-presentation-boundary.md)。本记录不修改[上一轮四轮模型评审](muxary-model-design-review.md)、[旧 UI 来源](muxary-ui-source.md)或旧验收。

> 后续状态：用户已在此两轮记录之后确认 Q9，新增本机项目打开及“项目 → 工作目录 → Agent”导航，原 worktree 创建/配置继续复用 CCB。下文 pending/未授权描述属于该轮历史，不代表当前范围；当前决定见 [ADR-0003](../adr/0003-workspace-and-canvas-presentation-boundary.md#q9-确认后的增量决定)。冻结模型原文不修改。

## 1. 需求与决策边界

用户希望严格评估整体布局，考虑项目/worktree、多 Agent 空间管理与大信息量性能；并再次明确每个功能都应查现有可复用 UI，不只复用 AgentChat Basic。需求是容易定位和操作真实 Agent，不预设“无限分屏必然等于无限画布”。

- **Q8 已确认**：默认专注，画布可切换。
- **Q9 待答复**：“首版 Agent 绑定 worktree、不做每任务 worktree”仍为提议，不能写为用户已接受。
- 本轮主审已授权实现：双视图、按需 hydration、无重叠轮询、现有 Agent 工作目录只读身份与服务端 scoped diff；不新增 Web project-open 或 worktree 生命周期。
- 模型曾建议“打开已有目录”，其安全条件保留为研究，不等于本轮获授权实现。未挂载项目启动、配置写入/重启、worktree 创建/删除/merge/prune/force 均不因模型建议进入本轮。
- 保留原 ccbd、任务与原生会话格式；Web 不引入另一套调度器、执行沙箱或统一跨 CLI 审批。

## 2. 改造前界面观察的来源

主审在独立、无登录 Chrome、CLI stubs、生产静态构建与真实 BFF 条件下保留了改造前截图。本小节记录**主审观察**，不是两个咨询模型看过图，也不是改造后验收。

本机证据目录：`~/.local/share/muxary-dev/expansion-review/`。

| 材料 | 条件与观察边界 |
| --- | --- |
| `baseline-desktop.png` | 1440×1000；专注交互可识别，但空任务右栏仍占 300px；“开始新任务”实际仅聚焦 |
| `baseline-mobile.png` | 从桌面 resize 到 390；主审观察到左右 overlay 同时保留、遮挡主内容 |
| `baseline-mobile-fresh.png` | 390×844 fresh-load，独立留样，不能把 resize 状态直接概括为所有移动首次进入状态 |
| `root-review-round1.md` | 主审冻结文字：项目/workspace 用语混淆、Agent 实际声明目录不显眼、无可发现的新项目入口；后者是观察，不代表本轮要新增该入口 |

既有“工作台任务 / 原生会话”分源有正确性意义，不因视觉统一删掉。截图只提供这些条件下的 UI 证据，不证明 CLI 真实联通、大规模负载或新的交互已经通过。

## 3. 真实 CodeBuddy 调用与来源指纹

两模型均通过本机 `codebuddy-code` 实际调用，不作角色模拟。两轮实际 CLI 均为 **2.183.0**；设置 `DISABLE_AUTOUPDATER=1`，使用：

```text
codebuddy-code -p --model <id> --tools '' --strict-mcp-config
  --mcp-config '{"mcpServers":{}}' --max-turns 1
  --no-session-persistence --output-format json
```

同轮提供相同文本。第 1 轮独立评审；第 2 轮共享双方第 1 轮完整最终正文、主审冻结评审和新增事实，要求互相反驳而非顺从主审。只提供用户需求与必要产品/代码事实，没有提供凭据、用户原生会话内容、截图或工具权限；它们没有执行产品、浏览器、性能或来源浏览验证。主审截图观察仅以注明归属的文字给第 2 轮。

| 轮 | 请求模型 | assistant 报告模型 | session | CLI / 墙耗时（ms） | 原始输出 SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| 1 | `deepseek-v4.1-flash` | `deepseek-v4.1-flash-ioa` | `01a1ca05-c4a8-7433-b9f4-f9a30e8ae5ac` | 28532 / 34731 | `875b11f3b5e9bb024ba4c611b865f7ecbe9391b0a477526b6620c32a45104f80` |
| 1 | `claude-opus-5.5` | `claude-opus-5.5` | `01a1ca05-c4b1-7752-b7e1-3c628eba3658` | 160553 / 166556 | `07a874fe30f676d4836c10ad448631b7450da37d77b59dbb8b21ea021a2add95` |
| 2 | `deepseek-v4.1-flash` | `deepseek-v4.1-flash-ioa` | `01a1ca0a-36fb-7bb5-9cc3-ac3df159764e` | 34702 / 40511 | `f92803f9e7dcf3d8ebd9f300c409d7463f6ad9c5b16b2cf86902239fc0f61ad4` |
| 2 | `claude-opus-5.5` | `claude-opus-5.5` | `01a1ca0a-371d-7ef7-9da8-ac1c23bc6b57` | 103304 / 109137 | `11cffed86cee713c73003038ff19a965ff83173ed84ad5b748cd4833f683ce46` |

四次均 `returncode=0`、最终 `subtype=success`。请求 SHA-256：

- 第 1 轮 `round1-prompt.txt`：`64a6586c934acd57138db8355339877765a3451c17123da1c6b19ece83daaa06`。
- 第 2 轮 `round2-prompt.txt`：`2386b74c97944248ca5d559fa0bc141068530707b2491a8791f475849b1b35ba`。

原始响应、请求、runner、派生 metadata 与完整最终正文均留在上述本机目录；目录 0700，模型原始文件与最终正文 0600，不把原始内部 reasoning 或凭据放进仓库。文件命名为 `round{1|2}-{requested-model}.{raw.json|answer.md|meta.json}`；索引为 `model-review-index.md`。SHA 只是来源指纹，不是独立证明模型权重或代码正确性。

CLI 的 JSON 实际为数组。第 1 轮 runner 初始按对象解析得到 `nonobject`，后从原数组提取最后的 `type=result`；模型身份取 assistant 的 `providerData.model`，未改原 raw。第一次 `python` 命令不存在，改为 `python3` 后才运行咨询；没有因此重复发模型请求。所有四组 raw/answer SHA 已重新核对。

## 4. 第 1 轮：独立意见与反例

下表是完整最终正文的摘要，不替代本机原文。此时尚未提供 CCB 具体 workspace 模型与 Q8 答案，不用后来事实反改首轮。

| 模型 | 独立建议 | 最强反例 / 首轮缺陷 |
| --- | --- | --- |
| DeepSeek | 项目 → Agent → 任务，worktree 作工作副本属性；默认专注；比较少量 Agent 用有限分屏，巡检大量 Agent 用 board；自由画布可选，只放摘要卡 | 长期发散探索有空间记忆价值。其“一个写入者，其余只读，只靠提示确认”不形成真实互斥；其 board/对比扩大了视图数量 |
| Opus | 项目 → 工作目录 → Agent → Job；默认上次项目/Agent专注；对比与 board 分工；先只列/选已有 worktree | 稳定管线的空间关系可能需要画布。其 `git worktree list` 真相源可能列出非 CCB 空组；“先选目录再派活”易被误实现为 live Agent 换 cwd；P1 新管理器可能重复 CCB |

两者都反对“分屏所以必然自由画布”的媒介推论，但没有否定用户有位置稳定/空间记忆诉求。两者都要求卡片摘要、连接与流数量有界，并把性能数字标为待测建议，未声称看图或测过产品。

## 5. 第 2 轮：新事实、撤回与主审取舍

第 2 轮新增的代码事实：

- CCB 已有 Planner → Materializer → BindingStore → Validator；managed worktree 回映原 project_id / `.ccb`，AgentSpec 决定 workspace。
- submit 只有 `to_agent` 与 `project_id` 等任务信息，不支持 Web 给 live Agent 静默热换 cwd。
- `project_view` 已有 Agent `workspace_path`；既有 diff 固定 project root，新增 scope 必须服务端验证。
- 共享目录无单写锁/只读强制；21st 当时条目只是来源候选，不是已 vendor。

**双方实际撤回**：DeepSeek 撤回“单写者靠确认”和新增独立 board/对比；Opus 撤回 `git worktree list` 为主真相源和 Web 创建管理器，承认双方“选 worktree → 派活”有热换 cwd 暗示。两者接受用户 Q8 与只保留专注/画布；自动排列、筛选吸收概览需求，不增加第三视图。

两者接受单一 selection、无连线、卡片不放 composer/xterm、工作目录只读身份、真实目录 diff 与逐组件来源核查；仍保留画布不适合少量 Agent 逐行比较的缺口，不宣称所有场景更优。

主审保留并明确取舍：

1. **scope 失败明确报错**。DeepSeek 允许降级 project_root，Opus 反对；采 Opus 的 fail-closed，避免用户以为看 Agent 目录实际看另一目录。共享目录标“目录差异，非该 Agent 独占产出”。
2. **撤回 80% gate**。两者均指出“80% 样本 p95 达标”会隐藏双峰/GC等不稳定；改为测前冻结、5 reps 全保留、失败不删除，逐 rep 和普通/fit-all 分报。具体建议协议见 SPEC，不伪造结果。
3. **不把进程 cwd 当永久保证**。两模型都把 workspace_path 与进程 cwd 相等作阻塞式前置检查，主审收窄为 CCB 声明/启动绑定身份验证。CLI 工具合法 chdir 不自动等于绑定失效，更不因此承诺文件隔离。
4. **数据完整性不是 DOM 总数**。不采 Opus 的“虚拟化后渲染条数必须等于 fixture 总数”的过强 oracle；核查数据、cursor、全部 Agent 可导航与原文可访问。裁剪本来不把所有 DOM 挂载。
5. **不把模型建议当授权**。两个模型提出打开已有目录和未初始化 `.ccb` 确认等条件；本轮先不实现该生命周期。Q9 仍 pending，不声称 Agent/task worktree 产品范围已获答复。
6. **不伪写原生无 force/prune**。源码 [`materializer.py`](../../lib/workspace/materializer.py) 自带 stale prune 和特定 force 重试；本轮没有新增 Web 入口，不改写成“原 CCB 全程不带 force”。

## 6. 逐功能复用矩阵

不是只保留一个 Basic 外观，也不是为“复用更多”堆不同设计系统。先检查当前代码/标准能力，再选 21st 原型与实际可取得的公开实现；共同 token、图标、选择态、滚动与焦点规则。

| 功能 | 现成来源 / 选择 | 本轮最小改造与边界 | 此记录时状态 |
| --- | --- | --- | --- |
| 聊天输入/消息 | [21st AgentChat Basic](https://agent-elements.21st.dev/docs/agent-chat)，既有固定 `b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37` | 保留 InputBar/UserMessage/Markdown/Suggestions 与已验证 IME 适配；不引云 SDK | 旧代码已有，新双视图集成待验 |
| Agent 画布卡/信息卡 | [21st @shadcn Card](https://21st.dev/@shadcn/components/card) → 固定公开 shadcn Card | 真实 Agent 摘要；只取所需 slots，共用 `cn`/token，不复制 demo 表单依赖 | 原型选定、公开源已取得；改造/验收待核 |
| 项目/Agent/页面快速导航 | [21st @shadcn Command](https://21st.dev/@shadcn/components/command) → 固定公开 shadcn cmdk 系列实现 | cmdk 拥有搜索/键盘行为；保留原生 modal shell，省未用 CommandDialog 依赖；仅已挂载项目与导航 | 公开源已取得；焦点/IME/集成待核 |
| 终端高度调整 | [21st @sean0205 Resizable](https://21st.dev/@sean0205/components/resizable) → ReUI公开说明 → 固定公开 shadcn Resizable | 只用于真实终端上下调整及键盘 separator，不重写 sidebar/frame、不 resize 源 pane | 公开源已取得；v4 API/交互待验 |
| 画布平移/缩放/定位 | 独立 [React Flow](https://reactflow.dev/learn/advanced-use/performance) / `@xyflow/react` | 成熟 MIT 行为引擎，不是 21st 原型；视觉来自所选卡片，非新 Agent runtime | 12.12.1 已固定依赖；产品/性能待验 |
| 左项目/Agent 导航、目录身份 | 现有列表/搜索与标准元素，Command补充 | 维持项目 → Agent；只读目录，Q9 未决前不加 worktree 选择/创建流程 | 目标交互已限定；新呈现待验 |
| 折叠上下文/长原文 | 已有 tabs、标准 `details` / `dialog` | 可按需保留，不为 Collapsible 候选加第二套 primitive；长内容按需纯文本，全文可访问 | 无新依赖要求；长内容/焦点待验 |
| 终端 | 原 xterm、原 pane WS | 保持单实例和源栅格；积压/慢消费不能靠 scrollback 上限冒称解决 | 原能力保留；新 resize/积压验证另列 |
| worktree选择/创建对话框 | 已评估 combobox/dialog 类复用需要 | Q9 未决且本轮不加生命周期，不造一个“假选择器”；已有标准 dialog 不必换库 | **提议/延后，不称已实现** |

### 公开源固定身份与许可

来源调查缓存：`~/.local/share/muxary-dev/expansion-review/source-research/source-manifest.json` 与 `source-findings.md`。该调查已取得公开固定 commit 文件，不是已取得 21st 账户门禁后的组件源，也不是完成集成。

- 公开上游：[`shadcn-ui/ui@dd41d19e2f80ff6891951f7ced74c2c9a650b065`](https://github.com/shadcn-ui/ui/tree/dd41d19e2f80ff6891951f7ced74c2c9a650b065)。本次观察 `git ls-remote refs/heads/main` 得到该 commit。
- [MIT LICENSE](https://github.com/shadcn-ui/ui/blob/dd41d19e2f80ff6891951f7ced74c2c9a650b065/LICENSE.md)，copyright 2023 shadcn；vendor 时保留完整许可和修改记录。
- 正确表述：**“从 21st 选择原型，适配固定公开 shadcn 上游”**。没有验证其与账户门禁文件字节相同，不声称取得 ReUI Pro blocks 或整站媒体授权。

| 已取得公开文件 | 原始 SHA-256 |
| --- | --- |
| [`LICENSE.md`](https://github.com/shadcn-ui/ui/blob/dd41d19e2f80ff6891951f7ced74c2c9a650b065/LICENSE.md) | `1564074e13439397221ffd522e2e504d56561994a23d371aa5e3ad43e4f5423f` |
| [`card.tsx`](https://github.com/shadcn-ui/ui/blob/dd41d19e2f80ff6891951f7ced74c2c9a650b065/apps/v4/registry/new-york-v4/ui/card.tsx) | `ef8305b12c3112dab42a4708b41b1ebcc042fa5ab4c20f039da8d45b09ed5059` |
| [`command.tsx`](https://github.com/shadcn-ui/ui/blob/dd41d19e2f80ff6891951f7ced74c2c9a650b065/apps/v4/registry/new-york-v4/ui/command.tsx) | `319e9264567dd46f04d705028bc345470663ca5919f31292c4ec43ea5ceb9336` |
| [`resizable.tsx`](https://github.com/shadcn-ui/ui/blob/dd41d19e2f80ff6891951f7ced74c2c9a650b065/apps/v4/registry/new-york-v4/ui/resizable.tsx) | `aaf3ea20e8060c75dd86e06fedfca053d49f81071123ba647b5699efcbc010ea` |

Resizable 固定源属于 v4 `Group/Panel/Separator` API；不能把旧 demo 的 v3 `direction` 当 v4 `orientation`，百分比大小明确使用字符串，不能误将数值当比例。参考[公开 ReUI 说明](https://reui.io/components/resizable)与[原库](https://github.com/bvaughn/react-resizable-panels)。

当前 package manifest 已固定 `@xyflow/react=12.12.1`、`cmdk=1.1.1`、`react-resizable-panels=4.21.0`；这证明依赖身份，不证明集成、包体收益或性能。React Flow 已安装包的 LICENSE 为独立 MIT（webkid GmbH），不能因此宣称其 21st 原型来源。实际 vendor 还须保留原始/本地 hash、许可、改动清单，未查这些就不写“已 vendor 完成”。

## 7. 前瞻验证，不是结果

[React Flow 官方性能说明](https://reactflow.dev/learn/advanced-use/performance)与 [xterm 流控说明](https://xtermjs.org/docs/guides/flowcontrol/)由主审本轮浏览核实。它们指导检查点，不证明本项目已经 memoize 正确、视口裁剪有收益或没有终端积压。

SPEC 冻结的建议：1/20/100 UI 节点、普通视口/fit-all、每 cell 5 reps 全留；frame gap p95 ≤32ms、选择响应 p95 ≤100ms、交互窗口无 >200ms long task。culling on/off 单因素；重内容 hydration、按需取数、visibility、无重叠轮询分别验证。上游限流、丢日志或拒绝大输入不能成为下游机制通过的证据；无收益机制不强留。

| 项目 | 本文记录时结果 |
| --- | --- |
| 两轮4次真实咨询、模型身份/请求/原始摘要核对 | 已完成 |
| Card/Command/Resizable 固定公开源/许可取得 | 已取得，集成与改造身份待核 |
| 新代码回归、独立 Chrome 端到端与 IME | **pending** |
| 1/20/100 ordinary/fit-all 性能5 reps | **pending** |
| culling、hydration、visibility 各自消融 | **pending** |
| 新功能真实 CLI 外部联通/平台矩阵 | **pending，不能从旧版继承** |

实际测量须另表补入命令、build/fixture、设备、每 rep、失败样本与限制；不把模型接受方案写成三方产品验收，也不修改冻结原文让首轮看起来已知道后续事实。

## 8. 清理与保留

本记录新增的三份文档、模型调用请求/回复/索引、公开源 manifest 与改造前截图仍用于复核，不是一轮即弃的缓存。文档任务未生成下载图片、构建产物或临时服务；不删除同目录主审/其他子任务的证据，不处理用户数据、配置或凭据。

## 9. Q9 后续产品资料核对（2026-11-11）

主审实际浏览当前 [Codex / ChatGPT worktree 文档](https://learn.chatgpt.com/docs/environments/git-worktrees)与 [Claude Code Desktop 文档](https://code.claude.com/docs/en/desktop#run-a-session-in-its-own-worktree)：前者把 worktree 与项目检出/对话关联，后者提供会话开始前的 worktree 选项。这些是对应产品的执行语义，不直接移植到 CCB。采纳“目录身份可见、并行工作易定位、创建前明确选择”的心智；不照搬每 chat 创建/迁移、归档删除或 handoff。CCB 的 Agent 绑定与原配置/Materializer 仍为基座。

逐功能增量复用：项目/目录导航继续复用现有列表和图标；项目打开用标准 `dialog` 与现有 token、Command 入口；worktree 设置直接复用原 CCB 配置页。没有引入新的 UI 原型来源或把浏览资料冒称已复制组件。新的真实双模型 Q9 评审及实现验证另列，不改第 1/2 轮判断。
