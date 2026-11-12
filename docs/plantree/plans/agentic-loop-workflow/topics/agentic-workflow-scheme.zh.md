# CCB 多 Agent 工作流方案

日期：2026-06-26

## 方案目标

这个方案的目标是把 CCB 从“多个 agent 同时在一个会话里协作”推进到
“由文档状态和脚本驱动的长期多 agent 工作流”。

基本出发点：

```text
程序内核要简洁、稳定、可恢复。
Agent 层要智能、灵活、能处理复杂语义。
二者通过 artifact、脚本准入和状态提交边界融合。
```

核心原则：

- `frontdesk` 只负责用户交流、宏观任务接收、确认、最终汇报和升级。
- Planner、orchestrator、worker、checker 等角色各自只持有当前阶段需要的上下文。
- 快速变化的执行细节进入 `.ccb/runtime/loops/`，不要污染长期对话和 plan tree。
- Agent 产出语义判断和报告，CCB 脚本负责硬约束、准入、索引和权威状态提交。
- Loop runner 读取状态并决定下一步激活哪个角色或脚本。

换句话说：脚本不追求智能，只追求稳定；agent 不直接拥有权威状态，只负责把复杂
问题想明白、写明白，并交给脚本提交或拒绝。

![CCB 多 Agent 工作流总览](../assets/agentic-workflow-overview.png)

## 重新梳理后的总体设计

新的工作流不应该被理解为“用脚本接管所有事情”，也不应该被理解为“让一群
agent 自由协作”。它应该分成三层：

```text
语义层：frontdesk / planner / task_detailer / broker / orchestrator / worker / checker / round_checker
  负责理解、规划、拆分、实现、审查、解释、判断。

提交层：ccb plan / ccb loop / ccb question / loop runner
  负责准入、状态边、锁、索引、artifact 提交、结果路由。

状态层：Plan Tree / Runtime State / Task Packet / Artifact Manifest
  负责保存长期事实、短期事实、证据和可恢复上下文。
```

这三层的关系是：

```text
Agent 生成语义 artifact
  -> 脚本做硬性校验和提交
  -> 状态文件成为唯一权威
  -> loop runner 只从已提交状态推进下一步
```

因此，系统的“智能”来自 agent，系统的“稳定”来自脚本，系统的“长期不漂移”来自
文档状态和 artifact 链路。

## 两层循环结构

系统分成两层循环。

外层是 `workflow loop`：

```text
用户
  -> frontdesk_group
  -> planner_group
  -> macro clarification_broker when needed
  -> task_detailer when detail refinement is needed
  -> task packet ready
  -> loop_runner
  -> execution_round
  -> script writeback
  -> done / partial / replan_required / blocked / needs_clarification
```

内层是 `execution round`：

```text
loop runner
  -> orchestrator
  -> worker + checker
  -> round_checker
  -> scripts writeback
  -> capacity release
```

关键边界：

- `frontdesk_group` 是用户边界，不是最强主 agent。
- `planner_group` 是宏观规划和 plan-tree 维护边界，可以包含 planner/reviewer/risk 节点。
- `task_detailer` 是短生命周期任务细化边界，负责源码/文档自研、detail packet 和任务局部澄清。
- Planner 在外层 workflow loop 内，但不在执行轮内。
- 执行轮结束后，不直接唤醒 planner；必须先由脚本写回状态。
- loop runner 只根据已提交的权威状态决定是否停止、回 planner、澄清或阻塞。

## 状态投影关系

长期 plan 和运行状态不是简单的上下级关系，而是动态投影关系：

```text
Runtime State = 高频事实
Task Packet = 任务桥梁
Plan Tree = 低频结论
```

`.ccb/runtime/loops/<loop-id>/` 保存高频事实：

- ask/job/callback 记录；
- node/branch/round 状态；
- 临时 artifact；
- provider/pane/lease/timeout 证据；
- retry、heartbeat、recovery 事件。

`docs/plantree/...` 只保存低频结论：

- 用户目标；
- 需求、非目标、验收标准；
- 稳定设计决策；
- blocker；
- partial/replan/done 的摘要；
- 可长期复用的证据链接。

允许从 runtime 投影到 plan tree 的边界事件：

| Runtime 事件 | Plan Tree 投影 |
| :--- | :--- |
| task ready | 记录 task packet 和 handoff |
| round pass | 记录 completion / evidence |
| round partial | 记录 partial report 和剩余分支 |
| replan_required | 记录 replan reason 和 planner 输入 |
| global_blocker | 记录 blocker 和下一 owner |
| clarification resolved | 记录 normalized answer 和新假设 |
| accepted decision | 记录 decision |

不投影：

- 每一次 ask；
- provider 临时输出；
- node 心跳；
- worker 重试过程；
- 原始 stdout/stderr；
- 未形成判断的中间讨论。

## 状态权威和文档边界

长期计划状态放在 plan tree：

```text
docs/plantree/plans/<plan-slug>/
  roadmap.md
  open-questions.md
  topics/
  decisions/
  history/
  tasks/<task-id>/
```

短期执行状态放在运行目录：

```text
.ccb/runtime/loops/<loop-id>/
  loop.json
  round.json
  breadcrumb.md
  asks.jsonl
  events.jsonl
  work-items/
  nodes/
  branches/
  artifacts/
  locks/
```

规则：

- Plan tree 记录稳定目标、决策、阻塞、验收标准和完成证据。
- Runtime state 记录 ask/job、节点状态、临时 artifact、心跳、重试和轮内证据。
- Agent 不直接改 `index.json`、`current_loop`、loop phase、owner、terminal status。
- 所有权威状态变更必须通过 `ccb plan`、`ccb loop` 或 `ccb question` 脚本。

文档分三类：

| 类型 | 主要维护者 | 例子 | 规则 |
| :--- | :--- | :--- | :--- |
| 机器权威文档 | 脚本 | `index.json`、`current_loop`、lock、lease、manifest、counter | Agent 不直接修改 |
| 语义文档 | Agent | plan brief、detail design、review、risk notes、partial/replan report | 脚本导入、记录 digest、索引和做硬性校验 |
| 混合文档 | 脚本 + Agent | task `README.md`、breadcrumb、plan status summary | 脚本管理 protected fields，Agent 管理正文叙事 |

这个边界的含义是：复杂 Markdown 不强迫脚本生成；但是 Markdown 里会影响状态机的
部分，必须由脚本保护或从结构化 manifest 生成。

## 角色清单

角色不是固定单点，而是 role group + 当前 owner。一个阶段可以由多个 agent 分工，但
对外必须有一个明确的当前 owner 和一个提交出口。

| 角色/角色组 | 常驻性 | 主要职责 | 不负责 |
| :--- | :--- | :--- | :--- |
| `frontdesk_group` | 常驻或用户会话边界 | 与用户交流、接收宏观任务、转交 planner、展示宏观澄清问题、提示用户进入 `task_detailer` 做任务局部澄清、汇报最终结果和不可恢复阻塞 | 写代码、改状态、调度 worker、维护或解释执行细节 |
| `planner_group` | 按阶段激活或长期 steward | 理解宏观任务，维护 plan brief、roadmap、decisions、open questions、evidence index 和宏观 readiness 建议 | 用户直接沟通、维护详细设计正文、长期保存代码级细节、runtime agent 管理、最终代码正确性裁决 |
| `task_detailer` | 每个任务短生命周期，按 orchestrator 需要激活 | 读取 orchestrator refinement request、plan brief、宏观任务、detail refs、plan tree、源码和测试证据，维护任务相关细节设计正文/方案展开/局部技术调研/详细验收说明，生成 detail packet、source evidence、detail readiness、稳定摘要回填，并处理任务局部澄清 | 维护长期 roadmap、改权威状态、调度 worker/reviewer、长期用户会话 |
| `planner_coordinator` | Planner 组内 owner | 汇总 planner/reviewer/risk 节点输出，生成统一 macro task packet 或 macro clarification batch | 单独绕过 review 标记 ready，补全所有实现细节 |
| `plan_reviewer` | Planner/Detailer 后的 review gate，可合并 | 审查宏观 task packet 和 detail packet 的歧义、验收标准、风险、测试方案和是否 ready | 执行实现、改权威状态、替 detailer 重写细节包 |
| `clarification_broker` | 阶段性临时激活 | 合并 planner 的宏观候选问题，过滤非阻塞问题，默认可默认项，生成用户可读问题 artifact | 直接替用户决策、直接修改计划状态、接管 task-local 澄清 |
| planner stewardship mode / `ccb plan` | 脚本优先，planner 可作为工作模式审阅 | 维护 plan tree 一致性、证据链接、历史归档和同步摘要；权威写入仍由脚本完成 | 业务实现、provider 修复、绕过脚本写状态、作为独立主线 Role 调度 |
| `loop_runner` | 程序/脚本，不是对话 agent | 读取 task/loop 状态，绑定 current_loop，启动执行轮，判断 stop/pause/replan | 做语义产品决策、直接写自由文本计划 |
| `orchestrator` | ask 激活，可临时 | 分析任务复杂度，切 1-4 个工作节点，申请动态容量，分发任务，汇总节点结果 | reload/kill daemon、直接写 runtime 权威状态、把 partial 变成 done |
| `worker` | 动态节点 | 完成一个有边界的工作项，产出实现或分析结果和证据 | 降低验收标准、改 plan tree 权威状态、隐藏失败 |
| `checker` / `code_reviewer` | 动态节点，与 worker 配对 | 设计节点级测试，审查 worker 是否满足原设计，拒绝隐藏 fallback、降级、假成功 | 接管主实现、改变产品范围、把 partial 标记为 done |
| `round_checker` | 每轮执行后激活 | 基于 planner 的 verification contract 做整轮验收，给出 `pass`、`rework_node`、`partial`、`replan_required` 或 `global_blocker` | 改产品范围、直接修代码、直接写 task status |
| `inner_monitor` | 后续增强 | 观察 ask/callback、pane、provider、lease、timeout、节点心跳并生成健康报告 | 业务判断、随意恢复或破坏状态 |
| `recovery_node` | 异常时激活 | 分析通讯、provider、pane、锁、lease 等异常，判断 recoverable/blocked | 绕过状态机继续业务执行 |

## Agent 和脚本的接口

Agent 和脚本之间只通过 artifact 和命令交互。

推荐格式：

```text
agent output
  artifact_path
  artifact_kind
  semantic_result
  evidence_refs
  recommended_next_owner
  confidence / risk_flags

script commit
  validate path / kind / state edge / required evidence
  record digest / actor / job / timestamp
  update index / status / current_loop / counters
  return accepted or rejected
```

脚本拒绝时，不应该让 agent 猜测状态。脚本要返回明确原因：

- missing required artifact；
- illegal status edge；
- task already bound to another loop；
- stale lease；
- loop id mismatch；
- artifact kind not allowed；
- required evidence missing；
- terminal task cannot be modified。

Agent 收到拒绝后，应该产出修正 artifact 或 blocker，而不是直接改状态文件。

## 脚本功能清单

### `ccb plan`

`ccb plan` 负责长期任务包和 plan tree 权威状态。

| 命令 | 功能 |
| :--- | :--- |
| `ccb plan task-create --plan <slug> --title <title>` | 创建 durable task packet，分配 task id，写入 tasks index |
| `ccb plan task-artifact --task <id> --kind <kind> --file <path>` | 导入 planner、task_detailer、reviewer、round checker 等产出的 artifact，记录来源、大小、sha256、时间 |
| `ccb plan task-status --task <id> --status <status>` | 按合法状态边更新 task 状态，例如 `draft -> ready -> running -> done` |
| `ccb plan task-show --task <id>` | 展示任务包、状态、artifact 和 current_loop |
| `ccb plan task-list --plan <slug>` | 列出计划下任务，供 loop runner 查找 ready task |
| `ccb plan breadcrumb --task <id>` | 生成给 agent 或 UI 的短状态提示 |
| `ccb plan task-bind-loop --task <id> --loop <loop-id>` | 下一切片目标：把 ready task 原子绑定到 current_loop，并进入 running |
| `ccb plan task-import-round --task <id> --loop <loop-id> --result <result> --report <path>` | 下一切片目标：导入整轮结果，写 `round_pass/round_partial/round_replan/round_blocker`，清理 current_loop |
| `ccb plan evidence` / `ccb plan sync` | 后续：同步 commit、测试、发布、完成证据和 plan-tree 摘要 |

关键校验：

- `ready` 必须有 requirements、acceptance、verification、handoff、review。
- `done` 必须有 completion 或 `round_pass` 证据。
- `partial`、`replan_required`、`blocked` 必须有对应 round artifact。
- `task-bind-loop` 必须有 per-task lock，避免两个 runner 同时跑一个 task。

### `ccb loop`

`ccb loop` 负责短期执行轮和运行时状态。

| 命令 | 功能 |
| :--- | :--- |
| `ccb loop topology propose --loop-id <id> --from <file>` | 新方向：提交由 orchestrator 生成的运行时工作流图提案，包含 agent、信息流、调用顺序、artifact 和释放门槛 |
| `ccb loop topology commit --loop-id <id> --proposal <id> --apply` | 校验并提交 desired topology revision，然后显式触发 reconcile |
| `ccb loop topology reconcile --loop-id <id>` | 对比 desired/observed，自动加载、释放、park、移动或重排 agent |
| `ccb loop topology status --loop-id <id>` | 查询 topology desired/observed、drift、ready/busy、retained/released 状态 |
| `ccb loop capacity ensure/status/release` | 底层能力：由 topology reconciler 或诊断工具使用，不再作为 orchestrator 正常入口 |
| `ccb loop run-once --task <text>` | 已有能力：手动执行一轮 worker -> reviewer -> orchestrator -> round_checker |
| `ccb loop run-once --task-id <task-id>` | 下一切片目标：从 task packet 读取 handoff 和 verification，再执行一轮 |
| `ccb loop runner --once` | 下一切片目标：扫描一个 ready task，绑定 loop，运行一轮，导入结果后退出 |
| `ccb loop event --loop <id> --kind <kind> --file <json>` | 记录运行事件 |
| `ccb loop ask-record --loop <id> --target <agent> --job <job-id>` | 记录 ask/job 和节点关系 |
| `ccb loop node-status --loop <id> --node <id> --status <status>` | 记录节点运行、通过、重做、阻塞、非收敛 |
| `ccb loop branch-status --loop <id> --branch <id> --status <status>` | 记录分支 running/frozen/draining/drained |
| `ccb loop round-result --loop <id> --result <pass|partial|replan_required|blocked>` | 记录执行轮语义结果 |
| `ccb loop block` / `ccb loop finish` | 后续：写阻塞或完成状态 |

V1 不先做常驻 daemon。先做 `runner --once`，避免 PID 管理、并发任务、恢复策略一次性变复杂。

### `ccb question`

`ccb question` 负责宏观规划阶段性澄清链路。任务局部澄清由
`task_detailer` 在 per-task detailer artifact 下提出，并由 frontend 或
`frontdesk` 通知用户进入该 `task_detailer` 回答。

| 命令 | 功能 |
| :--- | :--- |
| `ccb question candidates --loop <id> --phase <phase> --file <path>` | Planner 提交候选澄清问题 |
| `ccb question broker-review --loop <id> --phase <phase>` | Broker 合并、过滤、默认、延期或废弃问题 |
| `ccb question publish --loop <id> --phase <phase>` | 生成给 frontdesk 展示的用户问题 artifact |
| `ccb question answer --loop <id> --question <id> --text <text>` | 记录用户原始回答 |
| `ccb question resolve --loop <id> --phase <phase>` | 生成 normalized answers 并唤醒 planner |

V1 可以延后 `ccb question`，先让宏观 `needs_clarification` 停在人工处理边界。
如果是任务局部细节阻塞，应记录到 detailer clarification artifact，而不是送回
broker。

## 整体生命周期

### 1. Intake

`frontdesk_group` 接收用户宏观目标，只保留必要的约束、非目标、风险偏好和目标
plan root。它不展开实现细节，也不直接调 worker。

输出：

```text
macro_task
user_goal
constraints
known_non_goals
risk_tolerance
target_plan_root
source_refs
```

### 2. Planning

`planner_group` 读取宏观任务和相关 plan tree/source context，生成语义 artifact：

- requirements；
- design notes；
- acceptance criteria；
- verification contract；
- risk notes；
- handoff；
- planner review；
- readiness recommendation。

如果需要用户澄清，planner 不直接问用户，而是输出 candidate questions。

### 3. Clarification

`clarification_broker` 对候选问题做阶段性处理：

- 合并重复问题；
- 丢弃已被 artifact 回答的问题；
- 默认可默认的问题，并记录 assumption；
- 延后非当前阶段必须的问题；
- 输出真正需要用户回答的问题。

`frontdesk_group` 只展示最终问题 artifact 或链接。

### 3.5 Task Detail Refinement

当 macro task packet 已经有明确目标但还不足以让 worker/reviewer 执行时，
`orchestrator` 或 `loop_runner` 可以激活 `task_detailer`。它读取宏观任务、
plan tree、accepted decisions、源码、测试和既有证据，输出：

- `detail-packet.manifest.json`；
- `source-evidence-map.md`；
- `execution-spec.md`；
- `acceptance-detail.md`；
- `verification-detail.md`；
- `worker-handoff.md`；
- `detail-readiness.json`。

如果细化过程中需要用户输入，`task_detailer` 生成 clarification-needed artifact，
frontend 或 `frontdesk` 只通知用户去对应 `task_detailer` 回答。用户回答后，
`task_detailer` 记录 clarification summary 并继续细化。V1 不额外拆
`task_clarifier`。

### 4. Ready Commit

当 planner 的宏观 task packet 和必要的 `task_detailer` detail
packet 通过 review gate 后，脚本导入 artifacts，再请求状态变更。
脚本只检查硬性条件：

- artifact 是否齐全；
- review 是否存在；
- 状态边是否合法；
- 路径是否安全；
- manifest/digest 是否记录成功。

脚本不判断“方案是否聪明”，只判断“是否允许提交到 ready”。

### 5. Loop Runner

`loop_runner` 读取 committed task 状态。V1 先做一次性入口：

```bash
ccb loop runner --once
```

它只做确定性动作：

- 找一个 ready task；
- 申请 per-task lock；
- 绑定 current_loop；
- 启动一轮 execution round；
- 导入 round 结果；
- 根据 committed result 路由下一步。

### 6. Execution Round

`orchestrator` 读取 task handoff、必要的 detail packet 和 verification
contract，决定 1-4 个工作节点。它可以判断需要 `task_detailer`，但不自己承担
源码级细化研究。

每个节点默认是：

```text
worker
  -> 实现或分析一个 bounded work item
checker
  -> 设计节点级测试，审查 worker，拒绝隐藏降级
```

orchestrator 汇总 node/checker 输出，并交给 `round_checker`。

### 7. Round Checking

`round_checker` 不修改代码，也不改状态。它基于 planner 的 verification contract 设计
整轮验证，并输出语义结果：

```text
pass
rework_node
partial
replan_required
global_blocker
```

### 8. Writeback

脚本导入 round checker 的报告并写入权威状态：

```text
round_pass -> done
round_partial -> partial
round_replan -> replan_required
round_blocker -> blocked / needs_clarification
```

如果导入失败，loop runner 停止自动推进，进入 script/state validation failure，而不是从
未提交报告继续推理。

### 9. Stop Or Next Cycle

loop runner 根据状态决定：

| 状态 | 下一步 |
| :--- | :--- |
| `done` | 通知 frontdesk，停止 |
| `partial` | planner_group 重新水合，保留完成分支，重规划剩余部分 |
| `replan_required` | planner_group 重新设计任务拆分、验收或风险模型 |
| `needs_clarification` | 宏观问题走 broker/frontdesk；任务局部问题回到 `task_detailer` 并由 frontend/frontdesk 通知入口 |
| `blocked` | recovery 或 frontdesk escalation |
| `rework_node` | 留在执行轮内，但必须受 rework limit 限制 |

## 一轮执行的最小闭环

下一步最小可落地闭环：

```text
1. planner 创建 macro task；orchestrator triage 判断 direct execution、
   needs_detail、macro_adjustment_request 或 blocked；只有 needs_detail 时
   `task_detailer` 生成 detail packet 并回到 orchestrator
2. ccb loop runner --once 找到一个 ready task
3. ccb plan task-bind-loop 原子写 current_loop，并把 task 置为 running
4. ccb loop run-once --task-id 执行 orchestrator / worker / checker / round_checker
5. ccb plan task-import-round 导入 round 结果
6. loop runner 根据结果停止、回 planner、升级 frontdesk，或进入 blocked
```

结果路由：

| Round result | 写入 artifact | Task status | 下一步 |
| :--- | :--- | :--- | :--- |
| `pass` | `round_pass` | `done` | 停止并通知 frontdesk |
| `partial` | `round_partial` | `partial` | Planner 重新水合，保留完成分支，重规划剩余分支 |
| `replan_required` | `round_replan` | `replan_required` | Planner 重新设计计划、拆分、验收或风险模型 |
| `blocked` / `global_blocker` | `round_blocker` | `blocked` 或 `needs_clarification` | Recovery、macro broker/frontdesk，或 task-local `task_detailer` |

## 边界规则

### 不允许执行 loop 内降级

Worker 和 checker 不能为了完成任务而降低验收标准。以下情况必须拒绝：

- 吞掉错误并返回成功。
- 用户配置解析失败后静默使用默认配置。
- 跳过真实依赖行为但报告 ok。
- 改测试来适配错误行为。
- 把未完成或 partial 工作标记为 done。

### `rework_node` 只能用于有边界修复

只有在当前任务拆分、验收标准、风险模型都仍然有效时，才能返回
`rework_node`。如果需要重新拆分任务、修改验收标准、改变风险假设或询问用户，
必须升级为 `partial`、`replan_required` 或 `global_blocker`。

### Planner 也必须有停止条件

Planner 不是无限循环的思考 agent。以下情况需要停止或升级：

- 多次 replan 没有生成新的 artifact、决策或证据。
- 同一 failure signature 重复出现。
- readiness 建议多次被脚本校验拒绝。
- 用户 scope 在同一个 loop 内频繁变化。
- 宏观澄清问题反复被 broker 判定为重复、非阻塞或可默认。
- 任务局部澄清反复无法形成可执行 detail packet。

## V1 实施顺序

已经具备：

- `ccb plan task-create/task-artifact/task-status/task-show/task-list/breadcrumb`
- `ccb loop capacity ensure/status/release` 底层 capacity 能力
- `ccb loop run-once` 的 worker/reviewer/orchestrator/round_checker 轮次
- 基于 fake provider 的 `/home/bfly/yunwei/test_ccb2` 外部 smoke

下一切片：

1. 实现 `ccb loop topology propose/validate/commit/reconcile/status/release`
   的最小闭环，让 topology revision 触发 agent 加载、释放和状态回写。
2. 定义 `task_detailer` detail packet schema、manifest、readiness、clarification
   sidecar 和 import bridge。
3. 实现 `ccb plan task-bind-loop`
4. 实现 `ccb plan task-import-round`
5. 增加 `round_pass/round_partial/round_replan/round_blocker`
6. 增加 per-task lock 和最小 lease metadata
7. 增加 `ccb loop run-once --task-id`
8. 增加 `ccb loop runner --once`
9. 在 `/home/bfly/yunwei/test_ccb2` 做真实闭环 smoke：
   ready task -> runner once -> run-once -> import round -> done/partial

延后：

- 常驻 loop runner daemon
- 自动 planner 激活
- 完整 `ccb question` 澄清命令族
- 多任务并发 runner
- 多 orchestrator 仲裁
- 全自动 stale lease 恢复
- UI/rich panel 的工作流可视化
