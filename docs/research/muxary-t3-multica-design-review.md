# T3 Code / Multica 参考研究与 Muxary 布局交叉评审

- 日期：2026-11-12；研究基线 Muxary `0cd8bfea2e9e28b8cf5f373809329bcb3e100473`，需求分支由主代理管理。
- 状态：**参考证据与设计建议，不是本轮前端实现/测试通过报告**。主代理可同时实施获授权的有限改动；实现与浏览器验收另行记录，不回填成模型已看图或已测试。
- 主审 Codex 亲自查看下列 4 张官方公开工作台画面，读取固定版本源码及许可证。两名模型仅收到同一份文字事实及主审的画面观察转述，**没有收到图片、没有工具、没有测试产品**。
- 关联：[既有组件来源](muxary-ui-source.md)、[扩展评审与逐组件复用](muxary-expansion-product-review.md)、[workspace/canvas SPEC](../specs/muxary-workspace-canvas.md)。保留原研究、原验收与负结果，不覆盖冻结历史。

## 1. 来源、冻结身份与证据边界

只采用官方站及其相互链接的官方仓库，不采用搜索结果中相似域名的镜像/第三方 fork。公开 API 首次访问遇到 HTTP 403 rate limit，已保留事实；随后以不带凭据的公共 Git shallow/partial clone 读取固定源。没有因 API 失败改用二手说明。

| 产品 | 官方入口与固定源 | 真实取得的材料 | 不据此声称 |
|---|---|---|---|
| T3 Code | [官网](https://t3.codes/)、[官方 repo](https://github.com/pingdotgg/t3code/blob/d63db064363e3ba9c12310ed5efb5c86c35d1caf/README.md)，固定 `d63db064363e3ba9c12310ed5efb5c86c35d1caf` | 官网嵌入的 [app-desktop.webp](https://t3.codes/_astro/app-desktop.BHuzLVLF.webp)；AppSidebarLayout、ChatHeader、PanelLayoutControls、SidebarThreadRow、Appearance/Project Settings 文档 | 不声称登录运行其产品；静态图未证明实际响应、键盘/触屏、负载或完整功能；图字节不因文件名带hash就获得源码许可 |
| Multica | [官网](https://multica.ai/)、[官方 repo](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/README.md)，固定 `191e84be118c280c158d3d18a9b46790fcdf6e10` | README 直接关联的 [workspace-overview](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/apps/docs/public/images/docs/workspace-overview.webp)、[issue](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/docs/assets/readme/issue.webp)、[run](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/docs/assets/readme/run.webp) 图；dashboard-layout、app-rail、animated-right-sidebar、breadcrumb-header、panel-resize-handle、LICENSE/NOTICE | 官网互动营销 demo 不算真实产品操作审计；仓库宣传画面亦仅证明官方呈现，不证明该流程已独立重现 |

选定源文件、原始图片、URL/字节数/SHA、commit metadata 和目录清单留在本机私有 `~/.local/share/muxary-dev/ui-refinement-20261112/reference/`。目录 `0700`、文件 `0600`；不把这些截图和参考项目源码加入 Muxary 的运行资产或 vendor。

### 画面与许可指纹

| 材料 | SHA-256 |
|---|---|
| pingdotgg/t3code `LICENSE` | `935d8f2af0c703f9c39517ee57cc4930b19d02d533be930b63f0e82f93614b43` |
| multica-ai/multica `LICENSE` | `ec78c4feacec52c7dad8ed5ffdd79033fc8c58e320a3c5ebe9a00286cab37f63` |
| multica-ai/multica `NOTICE` | `ae1d27215675c4305be1b51a31a913b936a56c2d2266c234ca140596b9a04eab` |
| multica-ai/multica `apps/docs/public/images/docs/workspace-overview.webp` | `51810b0bfa0abcd54e0a84e1d75218f33f8343e48485cc78e098e286272fc302` |
| multica-ai/multica `docs/assets/readme/issue.webp` | `08dd9bd617035ed1fc6e7f15772edeed4ae298ef4b3eafdf5190c50412f40af4` |
| multica-ai/multica `docs/assets/readme/run.webp` | `f609abf2b7393a2f8ff771cc89c5c7ee1a3257086728e3998f4aa081608bef14` |
| T3官网 `t3-desktop.webp` | `55e626c516dbec901e3d2980da75d9653285b861ab461f240f08ff20a56f7c2f` |

## 2. 主审实际观察与推断分开

### T3：借主次层级，不借线程/子代理领域

**图中可见**：左侧为会话条目、状态与时间；顶端是紧凑项目/任务 breadcrumb；主要空间留给会话和底部 composer；右侧卡把工作目录、分支/变更、subagent 状态收在上下文区。[官方画面](https://t3.codes/_astro/app-desktop.BHuzLVLF.webp)

**源码可核**：[ChatHeader](https://github.com/pingdotgg/t3code/blob/d63db064363e3ba9c12310ed5efb5c86c35d1caf/apps/web/src/components/chat/ChatHeader.tsx) 处理 breadcrumb 宽度和省略；[PanelLayoutControls](https://github.com/pingdotgg/t3code/blob/d63db064363e3ba9c12310ed5efb5c86c35d1caf/apps/web/src/components/chat/PanelLayoutControls.tsx) 对终端/右面板使用带名称和 pressed 状态的按钮，能力不可用时禁用；[AppSidebarLayout](https://github.com/pingdotgg/t3code/blob/d63db064363e3ba9c12310ed5efb5c86c35d1caf/apps/web/src/components/AppSidebarLayout.tsx) 区分编辑、终端、modal 等焦点情境。[Appearance](https://github.com/pingdotgg/t3code/blob/d63db064363e3ba9c12310ed5efb5c86c35d1caf/docs/user/appearance.md) 将面板动效设计为可控项，而非必须动画。

**对 Muxary 的推断**：去掉重复的大标题和目录条可以减少视觉 chrome；关键不是把字做小，而是让“我正在给哪个 Agent、哪个目录派活”始终清楚。Muxary 的 Agent 导航不替换为 T3 的 thread 主导航；CCB 未提供相应语义时不造 subagent 卡或实时模型切换器。

### Multica：借状态扫描与渐进详情，不借 board 状态机

**图中可见**：overview 是 rail+导航+多列 board；issue 画面是导航、中心内容/活动、右属性；run 画面先列出步骤摘要，再在侧面查看一个步骤的输入/结果。直接复制 board 会使 Muxary 的个人 Agent 工作台被误读成团队 issue 管理器。[overview](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/apps/docs/public/images/docs/workspace-overview.webp)、[issue](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/docs/assets/readme/issue.webp)、[run](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/docs/assets/readme/run.webp)

**源码可核**：[DashboardLayout](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/packages/views/layout/dashboard-layout.tsx) 组合 AppRail、SpacePanel 与主内容；[BreadcrumbHeader](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/packages/views/layout/breadcrumb-header.tsx) 要求可导航 crumb 对应真实容器，非导航未知态不混入；[AnimatedRightSidebar](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/packages/views/layout/animated-right-sidebar.tsx) 考虑 reduced motion、IME 和编辑目标的快捷键边界。没有因此假定该实现已在 Muxary 性能或可及性验收通过。

**对 Muxary 的推断**：现有任务状态+Agent+摘要可以更加整齐可扫描；长结果保留按需展开而不是塞入每个卡片。右栏原本按需打开，不再为“紧凑”增加二次隐藏层。不同布局密度和视觉主题各有用途，不能仅因 Multica 图为浅色就断言它对比度合格或整体优于现有暗色。

## 3. 复用与许可边界

- T3 固定根 [LICENSE](https://github.com/pingdotgg/t3code/blob/d63db064363e3ba9c12310ed5efb5c86c35d1caf/LICENSE) 为 MIT。若未来实际取用其代码需保留版权/完整许可；本轮仅研究，不 vendor T3 源码，不把代码许可推及官网图片、logo 或品牌。
- Multica [LICENSE](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/LICENSE) 由 Apache2 正文与额外条件共同组成，含 hosted/embedded 及界面品牌条件；[NOTICE](https://github.com/multica-ai/multica/blob/191e84be118c280c158d3d18a9b46790fcdf6e10/NOTICE) 同样明确该组合。**不是普通 Apache2 或 MIT，不把其源码/样式/资产搬入重新品牌的 Muxary**。本轮只采用常见交互原则，沿用已独立固定、保留许可的组件实现。
- 此决定是本轮的保守复用范围，不是对不同商业分发场景作授权保证。官方图仅保留本机研究证据并在文档链接，不再分发为 Muxary UI 资源。

| 要改的用户决策/界面 | 本轮最低复杂度方案 | 复用而非重建 | 明确不引入 |
|---|---|---|---|
| 选择目标 | 保留项目→目录→Agent；紧凑顶栏+次级身份/来源，完整路径可访问 | 当前导航、原生可聚焦 button/details；Command 继续导航 | 第二 rail、文件管理器、多 workspace 权限层 |
| 日常派活 | 会话主体+唯一 composer，目标 Agent/provider 为只读身份 | 现有 21st AgentElements InputBar/UserMessage/Markdown/Suggestions | 前端动态切 CLI/model、第二消息管线 |
| 查看变更 | 标注目录范围，单个入口打开现有变更面板 | 现有上下文面板与 diff API | 新 diff 引擎、把目录变更归因给单个 Agent |
| 扫描项目任务 | 状态/Agent/摘要对齐；只读“全部/进行中”过滤可恢复 | 已有状态映射、button group/Card；不另建任务模型 | board、issue/review 状态、后台重排任务 |
| 返回被过滤目标 | 无结果时提示清空过滤，不让导航看似消失 | 现有搜索、Command；标准按钮 | 新搜索服务 |
| 终端与阅读 | 唯一终端按需，保留已读位置/草稿，跟随时可到最新 | 原 xterm、现有 Resizable/following 机制 | 为参考图新建多终端/焦点状态系统 |
| 画布 | 默认 focus，画布仍为可选概览 | 既有 Card+独立 React Flow | 无限同时实时会话、第三个 board |
| 窄屏/可及性 | 一次一个 drawer；Esc/焦点归还、可点击目标、减少动效 | 现有 modal/scrim/native dialog 和CSS | 动画库、假桌面窗口 chrome |

这里的组件出处沿用[既有固定来源与许可记录](muxary-ui-source.md)及[逐组件来源矩阵](muxary-expansion-product-review.md#逐功能复用矩阵)。**参考 T3/Multica 是调整信息层级，不是推翻用户已经选定的 21st 原型复用路线。**

## 4. 保持的领域不变量与主审不采纳项

1. CCB/ccbd 仍为调度和状态权威；不新增本地 board/线程状态机。视觉按钮不能悄悄新增派活、config 写入、重启或 cwd 切换。
2. 工作目录为 CCB 声明/启动绑定，不是独占写锁；完整路径可展开/复制。仅 basename+hover title 不足以支持触屏/键盘及同名目录辨别；但本轮不为自动算最短差异路径另造命名子系统。
3. `unknown`/未确认请求不改成 failed/running，不自动重发。只读筛选不是执行操作；任务计数明确项目范围，不把当前 Agent 与整个项目混淆。
4. 模型建议的“待重启生效徽标”只有在服务端有权威中间态时才能显示。本轮若只有配置/正常重启的说明，保留说明，**不凭现有目录或 provider 猜测 pending 状态**。
5. Composer 内 Agent/provider 标识仅说明当前绑定，不能长得像可实时换模型的 selector。source tabs 是工作台可靠任务与原生会话来源，不等于两个发送模式。
6. 两模型把“布局改动必然重置滚动/焦点”当成结构性事实，**主审不接受这个绝对断言**。改布局可能触发回归，是否发生需前后实测；可先测现有 following，不先制造新锚点存储架构。
7. 两模型对“B 不做”“E 不做”“四态空状态”的互相转述存在误读，不作为已取得可靠共识的证据。多 tab 不必然破坏串行轮询，反对新增 tab 是此轮缺少收益/增加心智与状态成本，而非逻辑上不可能实现。
8. 模型建议用 DOM 条数确认渲染，只能检查可见组件规模，**不是完整数据 oracle**；全文仍通过内容/SHA、真实成功响应、目标身份和请求日志等独立证据核对。

## 5. 真实两模型独立评审与交叉轮

使用本机已核的 CodeBuddy CLI **2.183.0**，无角色模拟；每模型首轮收到字节相同共同事实。第二轮分别附上自己和另一模型的首轮最终公开答复，要求保留分歧。没有用其内部 reasoning 作为产品证据，没有发送凭据、用户数据或历史对话。

```text
DISABLE_AUTOUPDATER=1 codebuddy-code -p --model <id> --tools '' \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --max-turns 1 --no-session-persistence --output-format json
```

命令在该任务私有目录执行，不主动打开原 HOME 对话记录；未使用 resume/session 载入。输出为 JSON event 数组；原始字节保持不变，提取最后 result。原 runner 的顶层 model 提取为空，另存 `provider-identities.json` 从 `providerData.model` 提取实际报告身份，**不把请求名冒充返回身份**。四次 event 类型均为 message/reasoning/message/result，未出现 tool 事件。CLI 虽接收 `--max-turns 1`，最终 num_turns 自报 3，故只声称实际传入限制参数，不能据参数宣布其内部计数为 1。

模型身份是 CLI/provider 报告，不是对权重版本、路由或服务端实现的独立认证。所有答复是建议，不是界面看图/操作或性能结论。

| 轮次/请求 | provider 报告身份 | session | wall 秒 / CLI ms | 结果 |
|---|---|---|---|---|
| 1 / `deepseek-v4.1-flash` | `deepseek-v4.1-flash-ioa` | `01a1cd7e-f1b3-7f55-8d77-12ed26eddb18` | 37.814 / 31597 | exit 0，success |
| 1 / `claude-opus-5.5` | `claude-opus-5.5` | `01a1cd7e-f19b-7620-8a35-18a5091738fb` | 77.93 / 71788 | exit 0，success |
| 2 / `deepseek-v4.1-flash` | `deepseek-v4.1-flash-ioa` | `01a1cd80-219c-75a3-b09c-4cab95340d66` | 24.471 / 18462 | exit 0，success |
| 2 / `claude-opus-5.5` | `claude-opus-5.5` | `01a1cd80-21c4-78f6-9213-cd5f82540597` | 61.336 / 55291 | exit 0，success |

### 不制造共识的结果

- 首轮 Flash：D阅读连续性>A紧凑上下文>C空态>B紧凑右栏；Opus：A>D>C>B。两者均指出长路径/同名目录误认风险、反对本轮新增 rail/tab/board。
- 交叉轮 Opus 改为 D先A，Flash 接受不可点击热换cwd/状态说明补充。主审只采纳可测的阅读/身份边界，未把模型让步当成已测优先级。
- Opus 主张 B 收窄为 unknown 语义；Flash 倾向少改右栏。主代理选择可逆、只读的“全部/进行中”筛选与既有任务表现，不引第二次详情折叠。此为人工综合决策，不假称模型逐行审阅实现后共同批准。
- 模型提出按消息 id 锚定、差异路径段、pending 状态等是候选设计，需先核实际能力和反例。未将其全部直接加入生产范围。

### 请求及原始答复指纹

本机 `~/.local/share/muxary-dev/ui-refinement-20261112/model-review/` 留存共同事实、每次 prompt、raw JSON、stderr、最终答复、metadata、provider-identities 和 runner。raw 可能含内部 reasoning，因此只在权限受限本机留存，**不复制入此公开文档**。以下指纹对应原始字节而非内容真实性保证。

| 轮次/请求 | prompt SHA-256 | raw SHA-256 | final answer SHA-256 |
|---|---|---|---|
| 1 / `deepseek-v4.1-flash` | `513b792f88f74b9cdff99ecd348d130fd8a4800815bbc317455fff7a35694010` | `a56f8f6330e272efcf84121a518812a8b17f18ba9bf88aadd6584cf0047544a9` | `16523eff72a70aedabc68a1747078de8cb1bc215bf37d4dd85df3dd26481f763` |
| 1 / `claude-opus-5.5` | `513b792f88f74b9cdff99ecd348d130fd8a4800815bbc317455fff7a35694010` | `7a14998b878570d0b8d359d028e6f48659f5b34c93bc5c9c9ec9a7399a14ede2` | `6dc5c9385f6165d8496f3851da8dd828a8b72e59c517e61232cf24a91ca4c528` |
| 2 / `deepseek-v4.1-flash` | `5ecaef492fd87e76eb8120eb584745be477ff5795078d611de78e6405c96c917` | `26ee193cc734558b3a9e61048161782219ad5bddd2b0e71834c670841a7d4f6f` | `ecdbb34b647502a696ea102303f3ab6242eca9195b1912f2d9af6972d6fea446` |
| 2 / `claude-opus-5.5` | `223ee8a3170c9c1ebf016e0a59b58c618fa91c72222f121ad302486f78878e9c` | `65fe9963f5e58fa59f45e75baede53b44627a310f41c18a0790f0fb1b7ad8bd8` | `b4c4a43b1d33f6898ebb69d48be3b619acf1d38194d9df6d770913dc83451445` |

## 6. 实现前约定的有限验收/消融建议

本节是**前瞻协议建议，未在本报告执行**。不因模型意见和截图好看就写通过；最终以主代理固定的实现身份、浏览器证据和完整测试日志为准。

| 检查 | 固定条件与通过观察 | 不能替代的证据 |
|---|---|---|
| 目标辨别 | 同 basename、不同绝对路径的两个 Agent；桌面/最窄支持屏宽可查看完整路径；copy内容与CCB声明一致；路径UI只读 | tooltip存在不等于键盘/触屏可达；只读图标不等于无写请求 |
| 身份与发送 | 搜索/筛选/切source/打开变更只改变展示；实际一次send的project/Agent保持正确；中文IME Enter不派活 | 按钮外观/disabled态不足以证明没有网络执行 |
| 状态/过滤 | 同一非空job快照包含进行中/终态/unknown；切全部/进行中可恢复；计数范围诚实；unknown无自动重试 | 用空数组/4xx提前拒绝不能背书列表渲染 |
| 阅读连续性 | 默认following时新任务/回复可达；用户上滑时不强制跳底；终端开闭/resize、右栏切换不改变目标/草稿；加载更早不丢原文 | jsdom没有真实布局，不能证明滚动几何；固定sleep不证明response已到 |
| 窄屏与焦点 | sidebar/context互斥、scrim可关闭；Esc后回触发点；长路径不挤走主操作；键盘能到全路径；200%缩放/减少动效 | 截图不能独立证明焦点/读屏/对比度合格 |
| 领域边界 | 同scope切UI没有第二终端；隐藏或切走native后确实停读；无config写入/热换cwd/新调度器 | UI看似静止不能证明network停止 |
| 数据与性能 | 同一完整payload/请求成功，保留长内容SHA；首屏/按需路径分开测；记录longtask与输入/selection时延的全部样本 | DOM条数、API早拒绝和一种数据规模不能外推全负载 |

建议可逆的单因素比较：

1. **顶栏密度**：同一 Agent/完整成功数据/窗口/面板状态，只改变旧大标题与紧凑顶栏；比较首屏有效内容、目标可辨、操作可达及滚动漂移，不同时换 polling/渲染策略。
2. **任务筛选**：同一job快照，只切全部/进行中；检验选择态/目标/原始数据不变，不据减少DOM就宣布普遍性能提升。
3. **阅读跟随**：同一到达顺序/终端尺寸，只比较主动跟随与用户上滑两种状态，分别断言；不先建立自动滚动错误假设再按它修复。
4. **视觉/动效**：只改变颜色/spacing或动效开关，保留内容、请求和布局逻辑。没有人类任务对照时仅称可及性/回归检查，不宣称新手完成率提高。

保留旧边界：100抽象UI节点≠100真实CLI；默认culling off通过不抹去100ordinary on失败；10MiB默认全文冷加载约1.4秒、极端xterm burst约562ms不能被本轮紧凑样式改动改写成“全部不卡”。这些是旧固定版本的负结果，不在新版本未测时倒填为当前数值。[旧性能/功能总证据](muxary-expansion-validation.md)、[内容/flow分层验证](muxary-content-flow-validation.md)

## 7. 交付与清理边界

本项仅增加此研究文档，不修改生产代码、依赖、品牌资产或旧冻结记录；未启动产品浏览器、构建或测试。本机任务新建的两个临时 public partial Git clone 已确认 remote/path 后精确删除，固定所选源、原图、commit/目录清单与全部模型原始证据保留；不触碰主代理的 baseline、浏览器、用户 HOME 数据、既有缓存或安装。
