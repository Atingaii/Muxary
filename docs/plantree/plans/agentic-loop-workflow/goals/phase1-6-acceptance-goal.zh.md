# Phase 1-6 分阶段与最终验收 Goal

日期：2026-07-03
状态：Planning

## 目标

把 Satinoös 工作流从 Phase 1 到 Phase 6 的建设过程整理成一个统一验收目标：

- 每个 Phase 有独立的阶段验收指标；
- Phase 1-6 全部完成后，有模块级验收指标；
- 最后通过深度测试和真实任务评估，判断是否可以声明 Phase 6A/6B 能力。

这个 goal 不负责分发 worker 任务。它定义“验收什么、怎么证明、什么条件可以声明
完成”。后续 worker/reviewer 只应按本 goal 拆分执行和审查。

## 验收分层

Satinoös 的验收分三层：

1. 阶段级验收：Phase 1 到 Phase 6 每个阶段分别通过。
2. 模块级验收：所有阶段完成后，按模块验证整体能力是否闭合。
3. 深度验收：用 fake-provider 程序矩阵和真实 provider 能力实验验证边界。

三层必须按顺序推进。阶段通过不等于模块通过，模块通过也不等于真实能力充分。

## Phase 1：Mount Topology Schema Split

目标：

- 把 topology 明确收窄为 agent/window/pane/provider/lifecycle 的 mount state；
- 拒绝把 topology 扩展成通信 DSL 或语义 DAG；
- 保留必要的 legacy read compatibility。

验收指标：

- `ccb.loop.agent_mount_topology.v1` schema 可写入和读取；
- 写入目标为 `agent_mount_topology.desired.json`、
  `agent_mount_topology.observed.json`、`agent_mount_topology.events.jsonl`；
- legacy `agent_topology.*` 可读但不作为新主线输出；
- mount schema 接受 windows、pane order、profiles、provider snapshot、
  lifecycle、release policy；
- 默认拒绝 `edges`、`gates`、`artifacts` 等通信/调度 DSL 字段；
- stale revision 和 base revision 冲突仍然拒绝；
- 现有 layout/topology 回归测试通过。

通过证据：

- focused pytest；
- `py_compile`；
- source-wrapper topology smoke；
- reviewer 确认 topology 只拥有 mount/lifecycle 权威。

## Phase 2：Document Anchors And Activation State

目标：

- 建立 workflow 最小文档锚点；
- 让 runner 从权威 task state 推进，而不是从 agent 对话记忆推断。

验收指标：

- 支持并校验 `task_packet.md`、`execution_contract.md`、
  `orchestration_notes.md`、`round_summary.md`；
- task status 至少覆盖 `draft`、`ready_for_orchestration`、`running`、
  `partial`、`replan_required`、`done`、`blocked`；
- `next_owner` 至少覆盖 `planner`、`orchestrator`、`frontdesk`、`terminal`；
- `execution_contract` 是进入 orchestration 的默认强制条件；
- `orchestration_notes` 可导入为 evidence，但不能改变 authority state；
- `round_summary` 可通过脚本导入并映射 round result；
- 重复导入同 digest 幂等，冲突 digest 拒绝或版本化。

通过证据：

- `ccb plan` 单元测试；
- artifact import 测试；
- status transition 测试；
- source-wrapper task-anchor smoke。

## Phase 3：Orchestrator Triage

目标：

- 让 `ccb_orchestrator` 成为 ready task 的语义路由者；
- 只在需要时激活 `ccb_task_detailer`；
- 宏观调整和阻塞必须回到正确 owner。

验收指标：

- route enum 覆盖 `direct_execution`、`needs_detail`、
  `macro_adjustment_request`、`blocked`；
- `direct_execution` 不激活 detailer；
- `needs_detail` 激活 detailer 并等待 detail packet/import；
- `macro_adjustment_request` 不挂载 worker/reviewer，返回 planner；
- `blocked` 记录 blocker evidence，不执行隐藏 fallback；
- 所有 route 的 task state 变化只通过脚本提交。

通过证据：

- fake-provider route tests；
- route decision evidence；
- `route_decision_correct=true`；
- reviewer 确认 detailer 不是默认 planning chain 成员。

## Phase 4：Ask-First Execution Round

目标：

- 证明 worker/reviewer 通过普通 `ask` 完成单轮协作；
- topology 只负责挂载和可达性，不描述通信流程；
- 稳定结果通过 `round_summary` 导入。

验收指标：

- orchestrator 可提出执行所需 mount topology；
- CCB 可 apply topology 并证明 targets askable；
- worker 与 `code_reviewer` 通过 `ask` 协作；
- reviewer 输出必须引用 `execution_contract`；
- 不允许 hidden fallback、scope shrink、fake success；
- `round_summary` 导入后才允许进入 terminal 或 next owner 状态。

通过证据：

- source-wrapper ask-first round smoke；
- ask reachability evidence；
- worker/reviewer reply artifact；
- round summary import evidence；
- dynamic execution agent release evidence。

## Phase 5：Release, Retain, Park, Reflow

目标：

- 证明动态 agent 生命周期管理可安全运行；
- 不杀 busy provider session；
- surviving pane 不因 reflow 被重建。

验收指标：

- 动态 execution agent 在 evidence import 和 idle proof 后 release；
- active ask 或 busy provider 触发 `retained_busy`，不能强杀；
- resident 或长期角色默认 hide/park，不轻易 unload；
- reflow 保留 surviving pane identity；
- overflow window 可创建和移除；
- surviving agent ask reachability 不丢失；
- cleanup 后 `.ccb/ccb.config` 不残留已释放动态 agent。

通过证据：

- `1 -> 6 -> 1` grow/shrink 测试；
- overflow window 测试；
- busy retain 测试；
- park/resume 测试；
- source-wrapper topology/release smoke。

## Phase 6：Single-Round Task Matrix

目标：

- 证明不同任务类型下，Satinoös 能完成或正确终止一个 bounded round；
- Phase 6 不声明长期自动多轮工作流完成。

任务矩阵：

- `direct_execution`：明确任务直接执行并 pass；
- `needs_detail`：先 detailer 细化，再执行并 pass；
- `macro_adjustment_request`：返回 planner，不挂载 worker/reviewer；
- `blocked`：记录 blocker evidence，不假成功；
- `partial_completion`：明确完成与未完成 steps，状态不是 `done`。

验收指标：

- 每个任务都有 expected route 和 observed route；
- 每个任务记录 `route_decision_correct`；
- `direct_execution` 不激活 detailer；
- `needs_detail` 导入 detail packet 和 step files；
- `macro_adjustment_request` 恢复 `next_owner=planner`；
- `blocked` 保留 blocker evidence；
- `partial_completion` 保留 unfinished-step evidence；
- worker/reviewer ask 不依赖 topology communication edges；
- dynamic execution agents 清理干净。

通过证据：

- Phase 6 fake-provider source-wrapper matrix；
- optional real-provider smoke；
- failure taxonomy；
- cleanup/residue audit。

## 全部完成后的模块级验收

Phase 1-6 全部完成后，必须按模块做整体验收。模块通过不是简单累加阶段测试，而是
验证模块间契约闭合。

### Plan/Task Document Module

验收指标：

- task packet、execution contract、orchestration notes、round summary 能串成完整链路；
- markdown 正文和结构化 sidecar 不冲突；
- agent 不能直接修改 authority fields；
- digest、actor、job id、imported_at 可追溯。

### Orchestration Module

验收指标：

- ready task 能进入 orchestrator triage；
- route 与 task outcome 一致；
- detailer 只在 `needs_detail` 激活；
- macro/block route 不误挂 worker；
- route result 可被 planner/frontdesk 理解。

### Mount Topology Module

验收指标：

- desired/observed topology 可对账；
- windows/panes/agents/provider snapshot/lifecycle/release policy 完整；
- 默认拒绝通信 DSL；
- drift、stale revision、missing agent 能被检测；
- apply/reconcile/release 后无 runtime 残留。

### Ask Collaboration Module

验收指标：

- worker/reviewer/detailer/orchestrator 可通过 ask 协作；
- ask failure 可形成 blocker evidence；
- worker/reviewer 对话不进入 topology 权威；
- reviewer 能拒绝 hidden fallback 和 contract-free pass。

### Dynamic Lifecycle Module

验收指标：

- dynamic add/move/park/resume/release 可组合；
- busy retain 正确；
- surviving pane identity 保持；
- resident roles 不被 loop cleanup 误删；
- release 后 `ps`、config、observed topology 一致。

### Evidence And Reporting Module

验收指标：

- 每次 run 有 evidence row；
- pass、valid_non_success、system_failure、role_failure、provider_failure、
  test_design_failure 分类清晰；
- B7 报告能解释每个非 pass 结果；
- final claim 和证据一致。

## 最终深度测试与验收

最终深度测试分为两个声明层级。

### Phase 6A：Program Matrix Claim

可声明条件：

- Phase 1-6 阶段验收全部通过；
- 模块级验收中 program-side 模块通过；
- fake-provider source-wrapper matrix 覆盖所有 route 和关键异常；
- focused pytest/py_compile 通过；
- source-wrapper cleanup 全部成功；
- 没有 authority mutation、runtime residue、误标 `done`。

声明含义：

- CCB 程序链路具备支撑 Satinoös 单轮 workflow 的能力。

不代表：

- 真实 provider 语义能力已经充分；
- 长期多轮自动 workflow 已完成；
- 可以默认生产启用。

### Phase 6B：Real Capability Claim

可声明条件：

- Phase 6A 已成立；
- 真实 provider lab 完成 L0-L4；
- 至少 L0/L1/L2 基础任务可执行；
- 至少一条 L3 `needs_detail` 任务跑通；
- 至少一条 `blocked` 或 `macro_adjustment_request` 任务正确终止；
- 至少观察一次 reviewer rework 或 partial，并正确分类；
- B7 深度分析报告完成并通过 reviewer gate。

声明含义：

- Satinoös 具备初步真实 provider 单轮任务 workflow 能力。

不代表：

- L5 压力任务稳定通过；
- 多轮收敛完成；
- supervisor/recovery 生产可用；
- provider failure 已被完全消除。

## 最终报告要求

最终验收必须产出：

```text
docs/plantree/plans/agentic-loop-workflow/history/
  phase1-6-acceptance-report-<YYYYMMDD>.md
```

报告必须包含：

- Phase 1-6 阶段验收结果；
- 模块级验收结果；
- fake-provider matrix 结果；
- real-provider lab 结果；
- failure taxonomy 汇总；
- 首个稳定复杂度断点；
- 仍未解决的 blocker；
- Phase 6A 是否可声明；
- Phase 6B 是否可声明；
- 下一阶段修复和实现优先级。

## 停止条件

必须停止并修复：

- authority state 被 agent 直接修改；
- topology 接受 communication DSL 进入主线；
- runner 从 provider conversation memory 推断状态；
- dynamic release 留下不可解释 runtime residue；
- blocked/partial 被误标为 done；
- reviewer 明确拒绝后系统仍伪装 pass；
- source test 从 `ccb_source` live runtime 运行。

可以继续但必须记录：

- 真实 provider 输出格式漂移；
- 真实任务返回 `partial`；
- 任务要求 `macro_adjustment_request`；
- 用户输入不足导致 `blocked`；
- L5 压力任务失败但证据完整。

## 下一步

1. 以本 goal 为 Phase 1-6 验收总纲。
2. worker/reviewer 任务后续应从本 goal 拆分，而不是另建分散验收口径。
3. 当 Phase 1-6 全部有可执行实现后，按本 goal 生成最终验收报告。
