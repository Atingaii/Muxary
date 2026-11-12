# Muxary UI 方向重梳理：CCB 内核，桌面式 Web 工作台

- 日期：2026-11-12。
- 状态：**产品边界经用户再次确认；布局优化为后续实施范围，不是新版本验收通过报告。**
- 基线：`fde3e6d63883b51a33476c88881fb2af19b40874`（`origin/main`）。
- 本文重申 [ADR-0001](../adr/0001-muxary-product-and-runtime-boundary.md) 和 [ADR-0003](../adr/0003-workspace-and-canvas-presentation-boundary.md)，不替换运行架构，不改写旧研究或测试结果。

## 1. 纠偏

用户要的是：**把原 CCB 的 Agent 工作现场变成易用的 Muxary Web 工作台，借鉴 T3 Code / Multica 的布局和交互，而非安装、改名或套壳独立 Multica。**

此前独立部署 Multica 是另一条产品路线，已由用户撤销。它不是 Muxary 的依赖，也不能用其部署或测试结果背书 Muxary。清理独立部署，不意味着删除 Muxary 里的设计研究、许可声明或引用。

必须保留的关系：

```text
Muxary Web（项目导航 / 对话派活 / 摘要画布 / 变更 / 终端）
       ↓ 同源 HTTP / WebSocket 薄适配
现有 WorkbenchService / mobile_gateway
       ↓
原 CCB / ccbd（项目、任务权威、Agent、会话、目录绑定）
       ↓
原有 Provider CLI，包括 CodeBuddy
```

不加入 Multica backend、Runtime/daemon、邮箱登录、组织账号、Postgres、Redis或第二套任务调度器。`lucentzhou` 如需展示，只是本机显示名称，不需要为此建立账号系统。无需邮箱登录不等于取消 Web 控制面的既有访问边界；远程访问是原独立需求，不借本轮布局修改重写它。

## 2. 现有实现，不从零重做

| 已有能力 | 可复用入口 | 本轮不能夸大的部分 |
|---|---|---|
| 项目 → 绑定目录 → Agent 导航、专注对话和唯一输入框 | `web/src/App.tsx`、`model.ts` | 不把界面换词等同新增了项目/线程模型 |
| 派活、查状态、取消、重试 | `lib/workbench/service.py`、原 `lib/ccbd` | HTTP 接收不等于完成，`unknown` 不猜成成功或失败 |
| 原生 CLI 历史与工作台任务分源呈现 | `App.tsx`、`lib/mobile_gateway/service.py` | 当前并非完整永久历史，也不是统一原生 token 流 |
| 目录身份、worktree 绑定与 diff | `lib/workspace/`、`lib/workbench/workspaces.py` | 目录不一定是 worktree，目录变更不是单个 Agent 产出 |
| 可切换并行画布 | `web/src/AgentCanvas.tsx` | 当前最多 100 个摘要节点，不是无限 CLI 或无限同屏内容 |
| 单个按需原生终端 | `web/src/Terminal.tsx` | 不在每个画布节点内实例化 xterm |
| 聊天、卡片、命令面板、可调面板 | `web/src/vendor/`、组件来源清单 | 不把整页宣称为某一个上游原型 |
| `muxary` 默认 Web、`muxary tui` / `ccb` 兼容 | `lib/workbench/cli.py` | 保留原协议、配置和会话语义，不全量替换内部 `CCB_*` |

基线 diff 仅覆盖 **tracked、unstaged**，不包括 staged/untracked；目前主要以轮询读取状态。当前 `feat/explicit-remote-web` 工作区另有未提交的远程适配，必须保留；其测试状态不能继承基线旧版本的通过记录。本独立 docs worktree 尚未集成该增量，后续实现须明确承接并回归，不能默认为基线已包含。

## 3. 信息架构与默认路径

```text
左：项目导航              中：当前 Agent 的工作区          右：按需详情
项目                      项目 / Agent 紧凑顶栏            项目任务
 └ 真实绑定目录            专注 ↔ 画布                     当前目录变更
    └ Agent               任务、结果、错误与未确认状态      目录/运行上下文
                          唯一输入框，发送目标持续可见
                          底部：一个按需打开的原生终端
```

高频路径固定为：**选择项目 → 选择 Agent → 输入任务 → 查看权威状态和结果 → 按需看变更或接管终端**。不要求先进入设置、不默认广播、不让新用户先整理画布。

- **T3 Code：参考层级。**让主要空间留给对话和输入，身份收敛到紧凑 breadcrumb，变更与终端按需展开；不照搬 thread/subagent/每线程 worktree 模型。
- **Multica：参考扫描和渐进详情。**状态、摘要、内容与属性分层清楚；不搬组织 rail、issue board 或 Review 状态机。
- **Muxary 自身识别度：并行现场。**画布卡片和真实运行状态组成可切换概览；不靠假桌面装饰、持续动画或第三种 board 增加复杂度。
- **worktree：真实目录。**展示根目录/共享目录/已核验 worktree 的区别；同名目录可查看完整路径。运行中不静默换 cwd，创建配置仍复用原 CCB 流程，暂不加入一键合并/删除。
- **设置：次级入口。**保留原 CCB 配置和重启规则；远程不可用能力应解释原因，不能显示成点击必定可用。

## 4. 下一轮必须解决的心智冲突

1. **历史与发送不是同一语义。**基线“原生会话”来源页仍显示 composer，但发送会创建 CCB Job。下一轮先明确“CCB 任务”和“CLI 历史（只读）”；只读仅限定历史展示，若仍展示 composer，必须常显“发送新的 CCB 任务 → 当前 Agent”，不要让人以为在直接续写历史记录。是否将历史改成抽屉，需单因素比较；不能先造一条拼接时间线。任务进入 CLI 后原生日志可能合法增加，不能用“历史永不增条目”作为验收 oracle。
2. **目录图标不能冒充 worktree。**当前目录组普遍使用分支图标；只有服务端确认是 Git/worktree 才表达对应身份，未知或普通目录如实显示。
3. **状态不虚构。**使用真实排队/执行/终态/unknown；不加假进度百分比、假审批按钮或未经 CLI 支持的模型热切换。
4. **变更范围清楚。**先把已有 diff 阅读和范围提示做好；增加暂存、未跟踪文件或 Git 写操作是另一个有测试的增量，不能仅改文案当已支持。

## 5. 组件与评审要求

沿用 [既有来源与许可记录](../research/muxary-ui-source.md)、[逐组件复用矩阵](../research/muxary-expansion-product-review.md) 和 [T3/Multica 研究](../research/muxary-t3-multica-design-review.md)。每个新增或重做的通用 UI 先检查已有依赖和 21st 可复用原型；许可与功能不匹配才说明不用的理由，不从零再造组件库，也不锁死在 AgentChat Basic 一个示例。

现有 React/Vite、已核验聊天组件、Card、Command、Resizable、React Flow 和 xterm 优先复用。T3/Multica 是参考实现，不引入其应用代码、品牌资源和运行服务。按用户清理要求，本机独立 Multica 源码和研究缓存中的 Multica TSX 副本已移除；旧研究记录表示当时实际取得的材料，远端固定来源与历史指纹仍可核查，不改写为从未取得过。

真实 CodeBuddy 两模型评审必须区分：请求模型名、provider 报告身份、文字评审与看图/操作验证。本轮已新增恰好两次真实 CLI 调用，请求 `deepseek-v4.1-flash` / `claude-opus-5.5`；均仅审同一份文字事实，未看图、未操作产品。身份、保留异议和原始证据指纹见[本轮评审](../research/muxary-ui-realignment-review.md)。旧轮次不充当新轮次，建议不充当浏览器通过结论。

## 6. 实施顺序与验收

1. **本轮：清理独立 Multica，固定方向与基线。**不启动已被用户叫停的 Muxary 工作台，不覆盖远程需求脏修改。
2. **下一实现增量：目标/历史语义与布局。**先围绕上述高频路径选取并评审组件组合，收敛导航、目录身份、主区和按需详情；不换后端、不同时新增 Git 工作流。
3. **闭环回归：真实 CCB 路径。**明确记录 CLI/Provider 覆盖与未测项，再验证冷项目、提交、终态、结果、正确目录 diff、终端和重连。
4. **最后：并行与负载。**先定位瓶颈，再对摘要画布、长内容和终端优化；不为“无限”预先引入第二数据层。

### 功能门槛

- 切项目/Agent/来源/画布和打开 diff 不产生派活；发送命中正确项目、Agent 与当前选择代际；旧响应不能覆盖新选择。
- 至少一个真实 CLI 完成提交 → 排队/执行 → 权威终态 → 结果；stub、截图与真实模型验证分别报告。刷新/超时不自动重发，unknown 保留。
- worktree 回映正确项目；错绑定明确失败，不 fallback 到别的目录。共享目录明确无独占写锁，不热换 cwd。
- 桌面 `1440×1000` 与窄屏 `390×844` 覆盖主路径、中文 IME、键盘、抽屉互斥、焦点恢复、上滚阅读与完整路径查看。

### 性能与单因素比较

- 平移缩放是画布视角，不是无限 DOM。沿用摘要节点、懒加载、单终端、可见来源读取和长内容按需展开；不自动渲染所有历史。
- 按[原 SPEC 第 6 节性能协议](muxary-workspace-canvas.md)的 `1/20/100` 摘要节点及普通视口/fit-all 分层取样，每个 cell **2 次热身、5 次正式**，全部保留且热身与正式分开；输入/选择延迟、rAF gap、long task 与最大在途读取数分别记录。
- 保留既有门槛：**每个正式 rep 分别**满足选择延迟 p95 ≤100 ms、rAF gap p95 ≤32 ms、交互窗口无 >200 ms long task，每个资源 `in-flight ≤1`；不能合并样本掩盖失败，不能通过换小 payload、隐藏失败或相关早拒绝制造通过。
- 前瞻比较：只改顶栏/导航密度时保持数据、网络、面板状态不变；比较历史 tab/只读抽屉时保持相同记录与发送语义；优化渲染时保持完整内容可访问并独立核对，不以 DOM 条数充当数据完整性证明。
- 旧长正文、突发终端和画布负结果继续保留。新布局未经实测，不称“全面不卡”或“桌面端完美复刻”。

## 7. 官方参考与证据边界

- [T3 Code 官方仓库](https://github.com/pingdotgg/t3code)、[官方产品画面](https://t3.codes/_astro/app-desktop.BHuzLVLF.webp)。
- [Multica 官方仓库](https://github.com/multica-ai/multica)、[既有固定版本 README](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/README.md)。

官方静态画面与源代码可以支持布局研究，不能证明本机交互、可及性和性能。本文是纠偏与实施约束，不是本轮 UI 已修改或全面测试通过的声明。
