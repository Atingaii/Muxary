# ADR-0003：工作目录与画布是现有 Agent 的呈现，不是新执行边界

- 状态：**已接受；Q8、Q9 均经用户确认**。
- 日期：2026-11-11。
- 范围：Muxary Web 的 Agent 选择、画布、工作目录身份与差异查看。决定已接受不等于实现或性能验收已完成。

用户 Q8 已确认默认专注视图、画布可切换。CCB 已通过 `AgentSpec`、`WorkspacePlanner`、`WorkspaceMaterializer`、`WorkspaceBindingStore` 和 `WorkspaceValidator` 决定 Agent 的工作目录；Job 以 `project_id`、`to_agent` 派发。把画布节点、worktree 或每次派活再建成另一种执行实体，会使用户误以为拖动节点、切换目录或收到回执就改变了实际执行。

因此专注与画布只投影同一项目、同一 Agent 选择：画布使用摘要卡、自动排列、筛选和成熟平移缩放引擎，不增加第三个 board、连线编排、第二个 composer 或调度器。工作目录显示 CCB 声明/启动绑定的身份，不宣称进程永久 cwd、文件访问沙箱、只读或单写锁；多个 Agent 共享目录时明确无写入隔离。运行中的 Agent 不因前端下拉或卡片操作静默换 cwd。

差异查看由服务端根据项目与 Agent 的可信绑定确定 scope，客户端不提交任意路径。绑定或归属校验失败必须明确报错，不能静默返回项目根目录的另一份 diff；共享目录结果标注为**目录差异，不是该 Agent 独占产出**。原有 ccbd 任务权威、回执与完成的区分、原生审批和终端栅格保持不变。

UI 逐功能复用而不锁死在旧 Basic：保留已核验的聊天组件；Card、Command、Resizable 从 21st 选型，再适配固定公开 shadcn 上游；React Flow 只是独立 MIT 行为引擎，不冒称 21st 原型。标准 `dialog` / `details` 和原 xterm 能满足需求时保留，不为增加组件数量引入第二套 primitive。来源取得、代码集成和验收是三个独立状态。

认真比较过默认自由画布、独立 board/对比分屏，以及把 worktree 作为派活目标的方案。默认自由画布增加定位成本；第三视图重复概览能力；目录选择不能改变 CCB 现有 Agent 绑定，因此本轮选择双视图和只读身份呈现。画布不擅长 2—4 个 Agent 的逐行比较，是保留的限制，不宣称对所有任务最优。

## Q9 确认后的增量决定

用户随后确认“项目 → 工作目录 → Agent”，Web 可打开本机项目，worktree 配置和创建进入原 CCB 流程；不静默热换运行目录，不新增删除/合并。此前两轮评审的 pending 是当时事实，保留原始记录，并由本节更新当前范围。

导航按 CCB 报告的完整目录分组，通常显示短目录名，仅同名碰撞时直接显示完整路径，悬停与可访问名称保留完整路径；未知目录不猜测项目根目录，不误报共享。打开项目使用一个标准原生 `dialog`，复用已选 Command 的导航入口和既有样式 token，不再引入一套对话框库。用户明确提交本机绝对目录后，BFF 才通过原 CCB `--safe` 启动；已运行项目直接返回，不 force、不重启。managed worktree 映射回原项目身份，不能另造项目。

不新增 operation/queue 管理器：现有 ThreadingHTTPServer 请求线程足以承接一个有界启动，启动并发明确拒绝，不自动重试；动态 registry 必须同时用于项目列表和原 mobile gateway 的派活/终端授权。启动结果未知时先只读核对，不把超时解释成启动从未发生。配置保存、worktree 物化与 live Agent 绑定是不同事实，复用原配置页自己的激活/重启要求，不自造第二套配置状态机。原 Materializer 内部策略保持不变。空间定位或性能消融否定某机制时再重议，不反写冻结证据。

项目启动 unknown 的 canonical-root 防重保护只属于当前服务实例内存，不冒称跨后端重启持久化；原 Job SQLite receipt 不能替代项目启动回执。启动 stdout/stderr 用临时文件避免 descendant 持有 PIPE 阻塞超时，显示读取有上限，但不承诺临时文件磁盘大小有界。

关联：[扩展 SPEC](../specs/muxary-workspace-canvas.md)、[两轮真实产品评审与来源](../research/muxary-expansion-product-review.md)、[既有内核边界](0001-muxary-product-and-runtime-boundary.md)、[同源控制边界](0002-local-web-control-boundary.md)。
