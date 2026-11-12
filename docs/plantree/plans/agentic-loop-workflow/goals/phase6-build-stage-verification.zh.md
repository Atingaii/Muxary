# Phase 6 分阶段构建验证与验收

日期：2026-07-03
状态：Planning

## 目标

把 Phase 6 从“最终跑一组测试”拆成可执行的分阶段构建门禁。每个阶段都必须回答：

- 本阶段构建什么能力；
- 需要产出哪些文件、脚本、报告或 runtime 证据；
- 怎么验证；
- 什么条件算通过；
- 失败后如何分类和回流。

这份文档基于两类输入：

- Satinoös 介绍包验证结果：Markdown、SVG/PNG、PDF 已生成并经过基础视觉和文本抽查。
- [phase6-real-capability-assessment-goal.md](phase6-real-capability-assessment-goal.md)
  定义的真实能力评估目标：充分测试不同复杂度任务、异常状态和失败分类。

## 基本原则

- 先验证文档和测试设计，再验证程序链路，最后验证真实 provider 能力。
- 每个阶段都要有可复查证据，不能只靠口头判断。
- 每个阶段都允许发现失败；真正失败的是误判、丢证据、绕过脚本、残留 runtime 或隐藏降级。
- 构建级验收必须分开记录：`pass`、`valid_non_success`、`system_failure`、
  `role_failure`、`provider_failure`、`test_design_failure`。
- 进入下一阶段前，上一阶段的 blocker 必须关闭或转成明确的非阻塞风险。

## 阶段总览

| 阶段 | 名称 | 主要目标 | 通过含义 |
| :--- | :--- | :--- | :--- |
| B0 | 方案包验收 | 说明文档、示意图、PDF 可读可分发 | 思路表达清楚，但不证明 runtime 能力。 |
| B1 | 测试设计冻结 | 冻结 task matrix、复杂度阶梯、评分字段 | 后续实现不再临时改验收口径。 |
| B2 | 脚本/状态单元门禁 | `ccb plan`、artifact import、route/result enum、release guard 单测通过 | 状态机硬边界可被机器验证。 |
| B3 | Fake-provider 程序矩阵 | 用真实 CCB runtime + fake provider 跑完整矩阵 | 程序链路支持 Phase 6A。 |
| B4 | 真实 provider L0-L2 | 真实 provider 跑 sanity、文档任务、简单代码任务 | 基础真实单轮执行能力成立。 |
| B5 | 真实 provider L3-L4 | 跑 detail-needed、澄清、blocked、macro adjustment | 任务细化和非成功合法终态成立。 |
| B6 | 压力与异常注入 | 跑 reviewer rework、partial、busy retain、ask/provider 异常 | 能暴露并正确分类异常。 |
| B7 | 深度分析与准入裁决 | 形成分析报告，决定 Phase 6A/6B 是否可声明 | 下一阶段工作有明确证据输入。 |

## B0：方案包验收

构建对象：

- `topics/satinoos-workflow-introduction.zh.md`
- `assets/satinoos-workflow-layered-flow.svg`
- `assets/satinoos-workflow-layered-flow.png`
- `assets/satinoos-workflow-introduction.zh.pdf`

验证项：

- PDF 包含 Satinoös 项目名、分层结构、信息流和 Phase 6 单轮边界。
- 图中能区分 `ASK`、`SCRIPT`、`TOPOLOGY` 三类边界。
- PDF 可提取文本，关键术语可检索。
- 图文没有明显截断或错误排版。

通过标准：

- 文档、图片、PDF 文件存在；
- PDF 第一轮视觉抽查通过；
- 介绍性文档没有声称长期生产工作流已完成；
- coworker 审查的 blocker/major 建议已吸收或记录为风险。

不通过示例：

- 图把 topology 画成通信 DSL；
- PDF 声称 Phase 6 已证明多轮长期工作流；
- 角色边界把 planner 写成细节实现 owner。

## B1：测试设计冻结

构建对象：

- [phase6-single-round-task-matrix-goal.md](phase6-single-round-task-matrix-goal.md)
- [phase6-real-capability-assessment-goal.md](phase6-real-capability-assessment-goal.md)
- 本文件。

验证项：

- 五类 route 明确：`direct_execution`、`needs_detail`、
  `macro_adjustment_request`、`blocked`、`partial_completion`。
- 复杂度阶梯明确：L0 到 L5。
- `Phase 6A` 和 `Phase 6B` 的声明条件分开。
- 每个测试都要求记录 expected route、observed route、
  `route_decision_correct`、round result、final status、cleanup result。

通过标准：

- `git diff --check -- docs/plantree/plans/agentic-loop-workflow` 通过；
- README 能链接到 Phase 6 最小矩阵、真实能力评估和构建级验收；
- 没有一个文档把 `partial`、`blocked` 或 `macro_adjustment_request` 当作自动失败；
- 没有一个文档要求真实 provider 测试全部 pass 才能输出分析报告。

## B2：脚本/状态单元门禁

构建对象：

- task artifact schema；
- route/result enum；
- `ccb plan task-artifact`；
- `ccb plan task-status`；
- `round_summary` import；
- mount topology validator；
- dynamic release/retain guard。

验证项：

- 未导入 required artifact 时不能进入 `ready_for_orchestration`。
- 未引用 `execution_contract` 的 reviewer pass 不能被接受为合格证据。
- `orchestration_notes` 不能直接改变 task status。
- `round_summary` 的 `pass/partial/replan_required/blocked` 映射正确。
- mount topology 默认拒绝 `edges/gates/artifacts` 这类通信 DSL。
- busy agent release 必须进入 `retained_busy`，不能强杀。

通过标准：

- focused pytest 覆盖状态边、artifact import、topology guard、release guard；
- `py_compile` 覆盖被改动的 CLI/runtime 服务；
- 所有失败都有明确错误消息，不能靠隐式 fallback。

## B3：Fake-provider 程序矩阵

构建对象：

- source-wrapper smoke 脚本；
- fake-provider deterministic replies；
- 外部测试根：
  `/home/bfly/yunwei/test_ccb2/phase6-fake-matrix-<stamp>`。

必须跑的 smoke：

- `smoke-direct-execution-pass`
- `smoke-needs-detail-pass`
- `smoke-macro-adjustment`
- `smoke-blocked`
- `smoke-partial-completion`
- `smoke-reviewer-reject-rework`
- `smoke-reviewer-cannot-accept`
- `smoke-busy-release`

验证项：

- 每条 smoke 使用真实 `ccb_test`、真实 `.ccb` runtime、真实 topology apply/reconcile。
- fake provider 只提供确定性语义输出，不替代状态机。
- 每条 smoke 都输出结构化 evidence row。
- 每条 smoke cleanup 后动态执行 agent 不残留。

通过标准：

- 所有 expected `pass` smoke 完成；
- expected non-success smoke 返回 `valid_non_success`；
- 无 `system_failure`；
- 无 authority-write violation；
- cleanup 全部 `kill_status: ok`。

通过后可声明：

- `Phase 6A: Program Matrix`。

## B4：真实 provider L0-L2

构建对象：

- 外部真实 provider lab：
  `/home/bfly/yunwei/test_ccb2/phase6-real-lab-<stamp>`；
- 真实 `frontdesk/planner/orchestrator/detailer/coder/code_reviewer` profiles；
- L0、L1、L2 任务包。

任务类型：

- L0：挂载、ask、status、release sanity。
- L1：简单 Markdown 或配置文档任务。
- L2：一个窄代码改动加 focused test。

验证项：

- route 判断正确；
- `direct_execution` 不激活 detailer；
- worker/reviewer 通过 ask 协作；
- reviewer 引用 `execution_contract`；
- 代码任务有真实测试或等价验证；
- dynamic release 干净。

通过标准：

- L0 全部 pass；
- L1 至少一条 pass；
- L2 至少一条 pass 或形成可解释的 `valid_non_success`；
- 没有 state corruption、runtime residue、hidden fallback。

## B5：真实 provider L3-L4

构建对象：

- detail-needed 任务；
- task-local clarification 任务；
- macro-adjustment 任务；
- blocked 任务。

任务类型：

- L3：需要 source inspection 和 step expansion 的任务。
- L3：需要 `ccb_task_detailer` 向用户澄清后继续。
- L4：故意包含宏观冲突或安全前提缺失。

验证项：

- `needs_detail` 必须激活 detailer；
- detailer 产出 `detail_packet/detail_summary/steps`；
- planner 不直接维护 detail body；
- `macro_adjustment_request` 不挂 worker；
- blocked 任务不执行隐藏 fallback。

通过标准：

- 至少一条 L3 `needs_detail` pass；
- 至少一条 `macro_adjustment_request` 正确返回 planner；
- 至少一条 `blocked` 正确保留 blocker evidence；
- 所有非成功结果都能被分类为 `valid_non_success` 或明确失败类型。

通过后可声明：

- `Phase 6B: initial real workflow capability for bounded single-round tasks`，
  但必须附带失败分类和适用范围。

## B6：压力与异常注入

构建对象：

- reviewer rework 压力任务；
- partial completion 任务；
- busy retain 任务；
- ask/provider interruption 任务；
- restart/resume 任务。

验证项：

- reviewer 拒绝一次后，worker 只获得一次 bounded rework。
- reviewer 二次不接受时不能继续隐藏重试。
- partial 任务记录完成与未完成 steps。
- busy release 进入 `retained_busy`。
- ask/provider interruption 形成 blocker evidence。
- route 和 execution 中间重启后不重复挂载 agent。

通过标准：

- 压力任务不要求全部 pass；
- 但每个异常必须被正确分类；
- 不允许出现误标 `done`、证据丢失、状态损坏或无法清理。

## B7：深度分析与准入裁决

构建对象：

```text
docs/plantree/plans/agentic-loop-workflow/history/
  phase6-real-capability-assessment-<YYYYMMDD>.md
```

报告必须包含：

- 测试环境、provider profiles、版本信息；
- 任务矩阵表；
- 每个任务的 score；
- failure taxonomy 汇总；
- 最强能力边界；
- 第一个稳定断点；
- role-boundary drift；
- script/runtime 缺陷；
- provider-specific 问题；
- 下一阶段工作建议；
- 是否可以声明 Phase 6A；
- 是否可以声明 Phase 6B。

通过标准：

- 报告能解释所有非 pass 结果；
- 每个 blocker 都有 owner 和下一步；
- 没有未解释的 runtime residue；
- 没有把 `valid_non_success` 粉饰为 pass；
- 没有把 provider 失败误归因到 workflow 设计成功。

## 构建级退出规则

可以进入下一构建阶段：

- 当前阶段没有 open blocker；
- 失败项已分类，并有明确 owner；
- cleanup 和 evidence 完整；
- 下一阶段测试输入不依赖未提交的临时状态。

必须停止：

- `.ccb` runtime 状态损坏；
- 权威状态被 agent 直接修改；
- dynamic agent 无法清理；
- `ccb_test --diagnose` 失败；
- 测试根或 provider home 隔离失效。

不需要停止：

- 真实任务返回 `partial`；
- 任务被正确 `blocked`；
- 任务要求 `macro_adjustment_request`；
- reviewer 拒绝并正确进入 replan。

这些属于能力观察，不是构建事故。
