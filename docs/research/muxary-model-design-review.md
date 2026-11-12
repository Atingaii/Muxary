# Muxary 设计交叉评审记录

当前结论：四轮共八次真实 CodeBuddy CLI 模型调用，最终选择 21st **AgentChat Basic**；具体定案见[第 3—4 轮](#用户再次强调后的具体原型选型第-34-轮)及[验收报告](muxary-validation.md)。以下前两轮的状态、CLI 版本与待验证结论是当时研究快照，原样保留，不代表当前实现仍未选型。

## 第 1—2 轮当时研究快照

- 日期：2026-11-11。
- 状态：研究与提议；不等于用户已接受的需求或完成的 UI 验收。
- 实际参与：主审 Codex；经本机 CodeBuddy CLI 2.178.0 调用的两个模型。不是以子代理角色模拟模型身份。
- 调用方式：`codebuddy -p --model <id> --tools '' --strict-mcp-config --mcp-config '{"mcpServers":{}}' --max-turns 1 --no-session-persistence --output-format json <review-prompt>`。
- 两轮均为设计咨询，禁用工具；未让模型操作仓库或读取本机凭据。下文仅保存回复正文和必要来源信息，不保存原始 reasoning 或完整运行上下文。
- 第一轮共同事实输入：Python/tmux 内核、Web 仅配置页、Flutter 不能直接 Web、移动网关现有能力、可靠 Job 位于 ccbd RPC、普通消息不等于 Job、统一审批尚未验证。
- 第二轮向每个模型提供另一模型第一轮原文，以及主审三项质疑：主输入只走可靠 Job 而非两种易混淆发送；21st 只复用 UI、不换调度器或引入配套 Agent 云；右侧优先结果/变更、终端按需。

## 主审待验证的归纳

1. 日常主闭环应使用 ccbd 的可靠任务；原生输入是显式终端接管，不冒充可靠 Job。
2. 消息、任务、原生会话是不同对象；是否以会话聚合任务、何时新建上下文，仍需产品确认，不能只画一条聊天流掩盖状态差异。
3. 默认三栏是候选，不是已选视觉目标；先取得现有页面与 21st 候选截图，比较真实内容密度、窄屏、键盘/中文输入后再定案。
4. 工具审批不承诺跨 Provider 统一；原生终端降级也必须真实可达且表明权限语义。
5. 静态配置不能代表动态模型生效；`sent`、`running`、`completed` 各自需要自己的证据。
6. 候选复用源：[21st Agent Elements](https://agent-elements.21st.dev/docs)、[安装约束](https://agent-elements.21st.dev/docs/installation)、[AgentChat registry](https://agent-elements.21st.dev/r/agent-chat.json)。已查看文档与 registry，但许可、精确源码版本、视觉选型尚待核查，不宣布采用或已安装。

以下为实际回复正文。模型对性能阈值或功能的建议并非已执行测试结论。

## 主审对第二轮分歧的处理

- **不接受 Flash 的“自己新建 InputBar/MessageList、21st 仅作参照”路线**：这与用户明确要求选择现成原型/组件再改造不符。接受其对许可和适配成本的质疑，后续先核查许可、用单组件 Spike 测真实 Job 数据，再决定复用的最小范围，不能将“薄”当成未经测量的结论。
- **不凭空添加 `awaiting_input` 权威状态**：接受 Opus 对高频原生追问/审批可见性的质疑；先检查真实 Provider 能力和现有事件，再决定能否内联回复。无法可靠识别的审批仍以显式原生终端接管处理，不能假装统一支持。
- **不按模型建议修改冻结证据**：首轮、第二轮回复原样保留在下文；主审不同意的建议仍可见。范围和界面方案最终以用户确认及实际验证为准。

## 第 1 轮

### 请求 `deepseek-v4.1-flash`

- CLI 回复报告的模型：`deepseek-v4.1-flash-ioa`。
- 会话标识：`01a1c9a1-32bc-7e79-b193-cb1550abacdd`；结果：`success`；CLI 报告耗时：11958 ms。
- 原始输出 SHA-256：`3c2a144357a6fd64157934a7f159b144c7ad49f17ee593089ae2d42fcbb74aa2`（只作来源指纹，不代表源码或模型本身的独立验证）。

**已知事实**：运行层是 Python+tmux；Web 仅是配置页；gateway 已提供项目发现、消息、SSE、终端 WS；job 的可靠生命周期在本地 ccbd socket RPC；普通消息≠job；跨 provider 统一审批未验证。

**1. 主界面层级（建议）**
三栏桌面壳：左=项目/会话/Agent 名册；中=会话与 job 时间线，消息与 job 卡片视觉分离，卡片带 queued/running/failed/done 状态；右=上下文抽屉（终端、diff、产物、日志），可折叠。顶栏只放项目切换与双通道健康灯（gateway/ccbd）。设置降为二级路由。

**2. 三个真实闭环与失败态（建议）**
- Job 闭环：提交→watch→终态。失败必须显式区分：排队满、RPC 超时/断连、运行中取消、重试幂等冲突；禁止用转圈代替状态。
- 多 Agent 交接：@A 产出转交 B。失败：Agent 离线、provider 鉴权失败、部分输出。需可回退到原 Agent。
- 终端/文件闭环：WS 终端打开→断线→重连或会话丢失。失败须给“已断开、可恢复/不可恢复”而非静默。

**3. 应复用的 21st 组件类别（建议，不指具体条目）**
应用壳与侧边导航、消息线程+富输入框、带状态徽章的列表/表格、命令面板、可拖拽分栏、日志/终端视口容器、空态与错误态、Tabs。选型时自行核对许可，我不提供 URL。

**4. 我反对的复杂性（建议）**
反对现在做“跨 provider 统一审批与权限矩阵”。理由：事实层面尚未验证，它会同时污染 job 状态机与 UI 权限分支，拖慢主闭环；先用各 provider 原生审批透传，验证后再抽象。

**5. 反驳“美化设置页=桌面体验”（建议，可测试）**
桌面感来自操作密度与状态持续，不是皮肤。验收：①日常高频操作（选项目、发 job、看状态、取消）100% 不进入设置路由；②Cmd+K/发送快捷键可用；③切换 Agent/面板不整页刷新，刷新后布局与选中态恢复；④≥100 条 job 列表滚动不掉帧；⑤断线 2s 内提示并可重连，终态不丢；⑥job 失败必然出现可点重试与原因。设置页再美也过不了②③⑤。

> Recap
> 给出三栏主工作台层级、三条闭环及失败态、可复用的 21st 组件类别、反对跨 provider 统一审批，并用 6 条可测验收反驳“美化设置页即桌面体验”；已区分事实与建议。
> 本轮已应用：开发工作原则（vibe-coding.md）。

### 请求 `claude-opus-5.5`

- CLI 回复报告的模型：`claude-opus-5.5`。
- 会话标识：`01a1c9a1-32af-7c5c-b01e-05990557aadd`；结果：`success`；CLI 报告耗时：43457 ms。
- 原始输出 SHA-256：`94d675c19257159310537ecec776add1afee4aeb69b184f0ca6ffca6f01b293e`（只作来源指纹，不代表源码或模型本身的独立验证）。

**标注**：【事】为已核实事实，【议】为建议。

**1 主界面层级与布局**【议】
- **布局**：三栏，宽度可调。
  - 左栏：项目和会话列表。【事】gateway 已有项目发现。
  - 中栏：任务会话流。消息和 job 卡片用不同样式区分。【事】普通消息不等于 job。
  - 右栏：Agent 状态面板，终端作为下钻标签页。【事】已有终端 WebSocket。
- **顶栏与输入区**：顶栏显示 ccbd 和 gateway 连接状态；底部 composer 明确分为"发消息"和"提交任务"两个动作。
- **层级**：会话 > 任务 > Agent > 终端。设置降为次级入口。

**2 三个核心闭环**
- **提交 → 排队 → 执行 → 结果**
  - 【事】job RPC 在本地 ccbd socket。【议】Web 需经 gateway 桥接，需先确认现状。
  - 失败态：ccbd 不可达、排队卡死、provider 崩溃、SSE 断线后需用 get 补齐状态。
- **观察并接管 Agent**：状态 → 输出 → 接管终端 → 返回原任务。
  - 失败态：tmux pane 消失、WebSocket 断开、Agent 无响应。
- **取消 / 重试**
  - 失败态：点取消时任务已完成的竞态、重复提交、重试后结果归属错乱。

**3 应复用的 21st 组件类别**【议】
- App shell 和侧栏、可拖拽分栏、命令面板。
- AI 聊天流和 composer、状态徽章和时间线、Tabs。
- Toast / Alert、空状态和骨架屏。
- 终端渲染需另选专门的库。
- 每个组件的许可证上线前逐一核实。

**4 反对：首版做统一跨 provider 审批中心**
- 【事】统一跨 provider 审批尚未验证。
- 理由：各 CLI 的审批语义不同。强行统一可能让用户点了"批准"却没有生效，比没有这个功能更危险。
- 【议】首版只检测"待确认"状态，并一键跳转到对应终端处理。

**5 美化设置页 ≠ 桌面体验**
设置页处理静态配置；工作台处理持续变化的运行态。可测试验收项【议】：
- 不离开主界面即可完成 submit → watch → cancel → retry 全流程。
- 刷新页面或断网恢复后，job 状态与 ccbd get 结果一致。
- 同屏 3 个以上 Agent 的状态实时更新。
- Ctrl/Cmd+K 可触达全部主操作。
- 从终端下钻后，可一键回到原任务上下文。
- 普通消息不生成 job 记录。
- `muxary` 直接打开工作台；`ccb` 兼容性待用户确认后再验证。

> Recap
> 已给出 Muxary 主工作台布局、三个闭环及失败态、21st 组件类别、反对首版统一审批的理由和可测试验收项；本轮未调用工具。

## 第 2 轮

### 请求 `deepseek-v4.1-flash`

- CLI 回复报告的模型：`deepseek-v4.1-flash-ioa`。
- 会话标识：`01a1c9a3-ca74-7664-9cf0-ee1ee4eb306f`；结果：`success`；CLI 报告耗时：20462 ms。
- 原始输出 SHA-256：`ebd5f504c51109d63a94c8ec3b147ddbb0e889275b076bf51b66e36219ca45e1`（只作来源指纹，不代表源码或模型本身的独立验证）。

最弱一项：主审第2条“选21st独立源码、用最薄视图适配”。

用户只关心任务是否真在跑，组件出身不影响这一点；license未核验即选定，等于把法律风险前置，也与“尚未安装/定案”自相矛盾。工程上这是伪薄适配：21st类型参考Vercel UIMessage（流式parts、tool调用状态机），ccbd是job RPC+SSE+get补状态，对接需重写状态归并、错误态与取消语义，产出的是适配层债务，不是薄视图。另一模型的组件“类别清单”同样隐含此风险，但主审把它升级为选型结论，故最弱。

取舍：首版不把21st源码作为依赖，自建InputBar/MessageList/JobCard并锁定自有消息模型；21st仅作视觉参照，待license书面核验且单组件POC跑通一条完整job流后再评估。composer保持单输入框+显式模式切换，不做双主按钮。

断网/重试/取消测试：
1. 提交瞬间断网：UI只能显示“未确认”，不得乐观显示已排队；恢复后以get为准，ccbd无记录判失败，禁止静默重发。
2. 断网中刷新：状态全取get快照；SSE重连只补齐不重放，消息不重复、job卡不闪回。
3. 对已完成job点重试：禁用或提示已完成，禁止生成第二个job；重试带原job id幂等，新attempt归属清晰。
4. 运行→完成窗口点取消：须显示“已完成/取消失败”并展示真实结果，不得停在已取消；双标签并发取消须收敛一致。

以上为建议，不构成用户已批准决策。

> Recap
> 已反驳主审第2条，给出不引入21st源码的取舍及4组断网/重试/取消测试；本轮未调用工具。

### 请求 `claude-opus-5.5`

- CLI 回复报告的模型：`claude-opus-5.5`。
- 会话标识：`01a1c9a3-ca73-7a12-8c5f-6cf9ae71323b`；结果：`success`；CLI 报告耗时：44665 ms。
- 原始输出 SHA-256：`e4ac20fb98d7ad2ce79d832a2a990be728e19f5375a458141dff1b4de16c580e`（只作来源指纹，不代表源码或模型本身的独立验证）。

> 以下均为建议，不代表用户已批准的决策。

**反驳：主审第 1 条（最弱）**
这一条与“原生审批”以及第 3 条“终端不抢主屏”相互矛盾。原生审批和 Agent 追问都是高频操作。如果回复只能走终端模式，只有两种结果：终端常驻并抢占主屏，或者审批被漏看、job 卡在 running。“不让用户猜按钮”的目标是对的，但解法不应是把回复流放到终端。

**取舍**
只保留一个 composer，提交目标由 job 状态决定，而不是让用户选择：
- 默认提交新 job。
- 选中的 job 处于 awaiting_input 时，composer 明确标注“回复 job#N”，并按 job_id 回写。
- 代价：需要 ccbd 暴露 awaiting_input 状态和回写 RPC，这一点尚未验证。做不到时，卡片显示“需处理→打开终端”，不假装能内联审批。
- 放弃：没有 job 上下文的自由聊天不进入主 composer。

**揭穿伪完成 UI 的测试**
1. 提交后、收到 ack 前断网：显示“未确认”。恢复后用同一 request id 重试，ccbd 中只有一个 job。
2. running 期间停掉 gateway 30s：卡片转为“状态未知”，不继续转圈。恢复后从 ccbd 拉取真实终态，包括期间已完成的结果。
3. 取消请求本身断网：保持“取消中·未确认”，禁止乐观标记为 cancelled。
4. 临近完成时点取消：UI 终态必须与 ccbd 一致，不能显示“已取消”却有产物落盘。
5. 失败后双击重试：只生成一个新 job 并关联原 job，原 job 仍为 failed。
6. awaiting_input 时刷新页面：提示仍在，回复不丢失也不重发。
7. ccbd 断开而 gateway 正常：两盏健康灯分别显示，composer 禁用并说明原因。

> Recap
> 反驳主审第 1 条：它与原生审批、终端不抢屏相互矛盾。提出“单 composer、目标由 job 状态决定”的取舍及其代价，并给出 7 条断网/重试/取消测试；全部为建议，未经用户批准。

## 用户再次强调后的具体原型选型（第 3—4 轮）

用户再次明确：必须由三方共同选择 21st 现成原型，不是从零实现。为此追加两轮真实 CLI 讨论；模型只看到明确提供的来源、源码结构与设计事实，**没有看到截图，也没有执行浏览器测试**。取样时 CodeBuddy 原生自动升级后已为 2.183.0；后续设置 `DISABLE_AUTOUPDATER=1` 避免测试中再变更。先前 2.178.0 观察不改写成新版本证据。

实际对照三个官方展示：[AgentChat Basic、Empty centered、Empty centered + suggestions](https://agent-elements.21st.dev/docs/agent-chat)。两模型首轮都倾向第三个，但都反对主审“输入固定底部却仍叫 Empty centered”的不实命名。主审接受这一反例，**最终主原型改为 Basic**；Empty centered + suggestions 只作空态组合的次级参考。保留已选择的固定 commit/MIT 代码，不把整个云 SDK、工具卡或调度接入。

- 实际复用：vendor 的 InputBar、UserMessage、Markdown 和 Suggestions；不是自写一套再冠 21st 名称。左右 CCB 项目/Agent/任务壳是产品适配代码，不宣称也是上游已有整页模板。
- 输入固定底部，减少首条发送后的布局跳动；不照抄以营销动效为主的页面。浅/深色、低噪中性色和少量蓝强调维持主流开发者工具信息层级。
- 特色使用真实数据：持续可见“发送给 Agent”目标，点击任务卡明确切换但不发送；短 Job ID 可复制完整 ID；真实活跃任务信号点和文字状态并存，不编造 token/speed/工具审批。
- 3 条空态内容是明确标注的**快捷任务模板**，选择后可编辑且不自动发送；不是来自历史任务的“智能推荐”。模型关于“没有真实任务源就不能提供建议”的过强意见未采纳，但其反对伪造来源的要求已采纳。
- 右栏窄屏默认隐藏，桌面可折叠；动效遵循 reduced-motion。模型建议本身不是功能验收，行为另由测试记录证明。

### 第 3 轮

#### 请求 `deepseek-v4.1-flash`

- 返回：`success`；session `01a1c9c5-72c4-74eb-9ac0-6a0f13c9520f`；CLI reported duration `12214` ms。
- 消息报告模型：`未在该输出顶层给出`；原始输出 SHA-256：`3897ff90854e049f477f17d953a583630b88ba7fd783a142f77e543e61523e1b`。

仅基于你给的文本事实作答。

**1) 主原型**：Empty centered + suggestions，链接 https://agent-elements.21st.dev/docs/agent-chat ；有消息态回收为 Basic。

**2) 复用方式**：已 vendor 的 InputBar、Suggestions、UserMessage、Markdown 按原文件、原 props 直接接入，composition 保留 flex-col h-full 的 MessageList + InputBar 两段结构；空态在 MessageList 内传 3 条项目任务给 Suggestions，消息态切 Basic 列表渲染。左右栏是外部自包壳层，不改组件内部。

**3) 两项特色**：信号点仅绑 job.status，无 job 不渲染，reduced-motion 下只换色不脉冲；任务卡以 CCBD 源标记 + 短 job id 点击切换左栏选中 Agent，数据全部来自真实 job。

**4) 反对（最严重）**：主审“输入固定底部”与该原型本体冲突——centered 的核心正是 suggestions 与输入同组居中。固定底部后实质是“底部输入 + 空态建议”，叫 Empty centered 名不副实，应明确标注为偏移改造，否则该选型论证不成立。其次右栏只读 diff 已超出最小改造，窄屏挤压主对话，建议右栏默认折叠而非可选。

**5) 验收**：空态与有消息态下 InputBar 的 `getBoundingClientRect().top` 相等；Suggestions 恰渲染 3 条且文案取自项目任务源；DOM 中不出现 token/speed 字段。

> Recap
> 已完成三方评审立场：选 Empty centered + suggestions 为主原型，给出源码复用路径、两项真实数据特色、对“固定底部输入”与原型定义冲突及右栏超范围两点明确反对，并给出一条可测验收。
> 未查看实际截图或执行测试，结论仅基于所给文本。

#### 请求 `claude-opus-5.5`

- 返回：`success`；session `01a1c9c5-7295-7e54-ba9e-c43c4ad3c01c`；CLI reported duration `42976` ms。
- 消息报告模型：`未在该输出顶层给出`；原始输出 SHA-256：`ef5968c899f105cf23528ba9f2ff84e6c90a89561cac9de763db4cac457f2dd3`。

**1 主原型**：Empty centered + suggestions，https://agent-elements.21st.dev/docs/agent-chat

反对：把输入框固定在底部，会去掉这个原型的核心，也就是“建议和输入框居中组合”，实际上变成了 Basic 加 Suggestions。应保留上游从居中到底部的切换，只加一次 layout 过渡，reduced-motion 下直接切换。如果坚持固定底部，就应如实改选 Basic。

**2 实际复用**：直接沿用 AgentChat 的 `flex-col h-full` + MessageList + InputBar 组合。写一层 CCB 适配，把会话映射到 UserMessage 和 Markdown 的 props。InputBar 的 `onSubmit` 接原有 CCB 发送接口，Suggestions 的内容取自 CCB 的真实任务。已 vendor 的 12 个文件相对 b04b36c 只改 import 路径，三栏外壳另外写。

**3 两项特色**：
- ①信号点旁同时显示文字状态，不只靠颜色区分，并带 aria，只映射真实 job 状态。
- ②任务卡显示 CCBD 标记和短 job id，点击 id 即可复制，有轻动效反馈。

**4 最严重问题**：点击任务卡会隐式切换 Agent，用户容易把消息发给错误的 Agent。InputBar 必须常驻显示目标 Agent chip，切换时短暂高亮。另外，3 条建议如果没有真实 CCB 来源就属于捏造，没有数据时应不显示。

**5 验收**：E2E 测试中点击任务卡后，chip 立即更新为对应 Agent；发送后，CCB 记录的目标 Agent 与 chip 完全一致。

> Recap
> 选 Empty centered + suggestions；反对固定底部输入和隐式切换 Agent；给出复用路径、两项特色和一条验收。

### 第 4 轮（共享彼此上一轮原文与主审修订）

#### 请求 `deepseek-v4.1-flash`

- 返回：`success`；session `01a1c9c8-1c24-798c-88b0-04971a241f19`；CLI reported duration `12021` ms。
- 消息报告模型：`未在该输出顶层给出`；原始输出 SHA-256：`500233345c3cb59076c20b2a717ae9acc40ac546c622adef034a154def0f553c`。

接受。Basic 与“输入常驻底部”名实相符，因此上一轮“冒称 Empty centered”的反对可以撤回；Empty centered 只作为空态下建议的组合参考，不再改动输入框位置，这个边界成立。复用已 vendor 的四个文件、只改外壳、不装整个 tool/云运行时，与现状一致。把任务模板如实标注为可编辑模板，消除了“建议像历史推荐”的真实性隐患；常驻“发送给 Agent”、任务卡只标明目标而不发送、任务 ID 一键复制，解掉了隐式切换导致的误发。右栏在窄屏下默认关闭可以接受。

残留条件：若空态 Suggestions 渲染在常驻 InputBar 之上，须确认它出现或消失不会改变 InputBar 位置，否则只是把“跳动”挪了地方。

必要测试：分别记录空态与首条消息后 InputBar 的 `getBoundingClientRect().top`，断言两者相等；同时断言 Suggestions 恰 3 条、文案含“任务模板”。

> Recap
> 第二轮已明确接受 Basic 为主原型及改造方案，指出空态建议与常驻输入框的残留布局风险，并给出一项可测验收：空态与有消息态下 InputBar 的 top 相等、Suggestions 恰 3 条且标任务模板。
> 未查看截图、未跑测试，结论基于文本。

#### 请求 `claude-opus-5.5`

- 返回：`success`；session `01a1c9c8-1c75-727e-82d0-4379f34ec25c`；CLI reported duration `20162` ms。
- 消息报告模型：`未在该输出顶层给出`；原始输出 SHA-256：`07b5cd54dd1546d30a0010f189bd8d5a1c8901289be84b791aa5a1214986219f`。

**结论：接受。** 选 Basic 为主原型，Empty centered + suggestions 只作空态参考，名称和实际做法一致，解决了第一轮的核心反对。在 Basic 下，输入框固定在底部是成立的。

**接受的改造**
- 沿用 vendor 源码，只适配外壳，不引入 tool 和云运行时。
- 快捷建议标为“任务模板”，避免被当成历史推荐，消除捏造风险。
- 常驻显示“发送给 Agent”；任务卡只切换目标、不发送；任务 ID 可复制。
- 信号点与文字状态并存，并支持 reduced-motion。
- 右栏在窄屏下默认关闭。

**附加条件（不是反对）**
- 点击模板只填入输入框，不自动发送。
- 信号点只映射真实 job 状态；没有 job 时不渲染。

**仍必要的 1 项测试（E2E）**
- 当前选中 Agent A 时，点击 Agent B 的任务卡：断言 chip 立即变为 B，且没有任何消息发出。
- 随后发送一条消息：断言 CCB 记录的目标 Agent 为 B。

> Recap
> 接受 Basic 主原型及各项改造，附两条约束和一项防误发 E2E 测试；结论只基于文本提议，未看图、未跑测试。
