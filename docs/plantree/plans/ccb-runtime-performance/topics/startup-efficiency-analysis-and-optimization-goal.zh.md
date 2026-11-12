# CCB 启动效率分析、优化与安全验证 Goal

日期：2026-07-16

状态：Executing — Phase 0 measurement foundation in progress

Role: execution and acceptance goal

Lifecycle: active execution goal; Phase 0 is in progress and no later phase is
accepted yet

Authority: subordinate to CCB startup, lifecycle, provider-session, and
diagnostics contracts

Domain: `ccb` CLI、keeper、`ccbd`、项目 tmux namespace、Agent runtime、
Provider launch、前台 attach

Read when: 分析启动耗时、设计启动并发、修改启动时序、建立冷/温启动
benchmark、决定启动优化是否可发布

Related:

- [CCBD Startup And Supervision Contract](../../../../ccbd-startup-supervision-contract.md)
- [CCBD Lifecycle Stability Plan](../../../../ccbd-lifecycle-stability-plan.md)
- [Startup Critical-Path Optimization](startup-critical-path-optimization-2026-07-15.md)
- [Runtime Performance Roadmap](../roadmap.md)
- [Source Runtime Test Gates](../../../baseline/test-and-release-gates.md)

## 1. Goal

建立一套可重复、可解释、可回退的 CCB 启动效率分析与优化程序，在不降低
生命周期、Provider session、Agent 通讯和持久化权威正确性的前提下：

1. 把 CLI、keeper、`ccbd`、tmux、Provider 和前台 UI 的启动耗时拆到可归因
   的阶段及 Agent 子阶段。
2. 优先识别并修复错误 relaunch、重复准备、重复扫描、无效落盘、同步等待范围
   过大等 bug 或不合理设计。
3. 在输入和 authority 边界冻结后，使用批处理、single-flight、有界并发、
   Provider-specific 限流等方式缩短真冷启动。
4. 将“控制面可用”“namespace 可 attach”“请求 Agent 可用”“全部 Agent 已预热”
   分开测量，必要时以显式、可观察、可回退的前台优先策略降低用户可感知耗时。
5. 用真实 Provider、故障注入、跨平台和慢文件系统测试证明加速没有引入
   session 串线、重复进程、丢任务、重复回复、authority 乱序或资源泄漏。

本 Goal 定义执行和验收边界，不授权立即修改实现、发布版本或在真实工作项目上
循环执行破坏性冷启动。

## 2. Authority And Reading Order

出现冲突时按以下顺序解释：

1. `docs/ccbd-startup-supervision-contract.md` 及 Provider session isolation
   contracts 定义不可破坏的运行时行为。
2. `topics/startup-critical-path-optimization-2026-07-15.md` 定义已接受的 P0-P5
   架构方向。
3. 本 Goal 定义后续分析、实现分期、测试矩阵和完成标准。
4. `roadmap.md` 与 `implementation-status.md` 只记录当前进度和交接。

性能改造若改变 mounted、readiness、foreground attach、configured-agent desired
set 或 Provider session 行为，必须在同一 patch 更新相应 contract；不能只更新
本 Goal。

## 3. Current Evidence Baseline

2026-07-16 在 Linux 本地文件系统、已安装 `v8.2.0`、五窗口、十五 Agent、
真实混合 Provider 项目上取得以下只读基线：

| 场景或阶段 | 当前证据 |
| :--- | ---: |
| 完整 kill 后单次冷启动 `supervisor_total` | `9.267 s` |
| 冷启动 `flow_total` | `8.580 s` |
| namespace 创建 | `0.686 s` |
| Agent 分类与 Provider 准备 | `0.884 s` |
| Agent runtime 总阶段 | `7.673 s` |
| 二十次健康 warm CLI wall p50 / p95 | `1.166 s / 1.301 s` |
| 二十次 warm daemon supervisor p50 / p95 | `0.550 s / 0.629 s` |
| 二十次 warm daemon flow p50 / p95 | `0.266 s / 0.305 s` |

冷启动中十五个 Agent 的单项 duration 相加为 `7.673 s`，与串行 runtime
阶段一致；两个最慢单项合计约占该阶段 `46%`。当前 `agent_runtime_commit`
指标实际包住 launch、tmux respawn、session write、binding resolve、authority
attach 和 restore，因此名称不足以支持下一步归因。

当前冷启动只有一个真实样本，不能作为 p50/p95 或并发度结论。warm 数据证明
P0-P3 的 reuse 修复有效，但不能证明真冷启动已经优化。

现有 `dev_tools/perf_runtime_lifecycle_profile.py` 是 CPU/RSS 时间窗采样器：
`startup_samples` 表示采样点而不是重复启动次数，且采样结束后会终止仍在运行的
前台进程。它可继续用于资源归因，但不能直接充当启动 wall-time benchmark。
Phase 0 隐私审计还发现它原先会持久化 `ps args`、自定义 load command 和 ask
message；working-tree 修复只保留脱敏 executable identity、message byte count
和明确的 `*_persisted=false`，不再把 prompt/argv 写入 profile。

2026-07-17 Phase 0 working-tree checkpoint 已把 source wrapper、Python eager
imports、CLI、daemon 和 Agent 子阶段放进可相关、互不重叠的归因链。最新两
Agent stub warm smoke measured command wall 为 `363.129 ms`，其中 process
bootstrap `243.986 ms`、CLI `99.766 ms`，external attribution 为 `94.664%`；
资源/cleanup gate 通过。T0-T6 no-attach 记录在三轮中均结构完整且同 generation，
当时冷启动 T1 仍只是与 T2 同时取得的 `observed_upper_bound`；后续 checkpoint
已补齐精确 keeper T1。T5 在 no-attach lane 明确为不适用。因此该早期结果仍是
`smoke_only`，完整证据和 digest 见
[Phase 0 readiness/attribution checkpoint](../history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md)。

同一 source、fixture、generation 与 warm reuse identity 的 instrumentation
控制/观测 A/B 先完成 `1 + 2` 烟测，随后两次完成冻结的正式 `3 + 20`。最新
exact-T1/active-resource-seed recheck 的 `20/20` measured pair 有效，paired
p50 额外开销为 `-0.283 ms`，95% CI 上界为 `7.868 ms`，均满足 `10 ms`
预算；`24/24` instrumented resource profile 均 verified、formal-eligible 且
process-I/O complete。readiness `24/24` 完整，其中冷 prime 有一个精确 keeper T1，
其余 23 个 warm 记录均为 `not_required_already_mounted`，没有用 upper bound 冒充。
instrumentation overhead、readiness 与 resource gate 均通过。整体
`formal_claim_allowed` 仍为 false：场景/Provider/故障/平台矩阵未完成。
证据见
[Phase 0 instrumentation A/B checkpoint](../history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md)。

定位 exact T1 时确认 lifecycle durable atomic replace 不能串行化跨进程 stale
read-modify-write。CLI running intent、keeper lifecycle materialization 和
keeper startup transaction 现已在 working tree 使用 fresh-read 短锁与
`startup_id + generation` fence；确定性 POSIX process regression、扩展单测和
外部 source smoke 均通过。该修复不把 lock 跨越 spawn/ping，warm running intent
不再 durable rewrite。完整边界见
[Phase 0 lifecycle transaction checkpoint](../history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md)。

随后完成 keeper-to-child generation fence：child 精确认领 keeper generation，
progress/mounted/cleanup、stop/heartbeat/keeper/reload/namespace writers 与最新
daemon-boot report 均按 fresh authority 收口；readiness 同时核对 serving identity
与当前 lifecycle，超时 child process group 会被定向终止并 reap。聚焦矩阵与外部
formal A/B 均通过，完整证据见
[Phase 0 generation fence checkpoint](../history/startup-phase0-generation-fence-checkpoint-2026-07-17.md)。

精确 T1 不新增 authority 文件：keeper 在 durable `phase=starting` save 返回后
立即采样 host monotonic counter，随既有一次性 child fence 传入并在 child 入口
消费；start handler 仅在 startup id、generation、当前 lease identity 和单调顺序
全部一致时投影为相对毫秒。原始绝对 counter 不落盘，缺失/畸形只保留诚实的
upper bound。同期发现 benchmark 把历轮死亡 PID 永久累积进 active sampling seed，
导致 `vanished_process_count` 随轮数线性增长；现已把终态 active seed 与累计 cleanup
set 分离，并添加 baseline/terminal/never-valid/regression 互斥诊断。最终正式 A/B
的 warm active scan 只观察到 1-2 个 vanished PID，不再随 ordinal 增长。证据见
[Phase 0 exact T1 checkpoint](../history/startup-phase0-exact-t1-checkpoint-2026-07-17.md)。

严格 mounted/self-ping 边界也已在 working tree 收口：socket bind/listen 和路径
替换具备 attempt ownership，child self-ping 经过正常 request worker；随后 accept
loop 持续服务 ping，但 normal RPC 在 generation-fenced runtime bootstrap 完成前保持
关闭。最终 `phase=mounted/startup_stage=mounted` 只由当前 child 发布。外部烟测曾
确定性暴露 keeper 根据 interim lease 提前合成 mounted 的竞态；该失败 artifact 被
保留，keeper 现把 active child stage 当作 observation-only，并有独立回归。修复后
外部烟测零失败且正式 cleanup 无残留；同实现的冻结 `3 + 20` warm A/B recheck 满足
`10 ms` instrumentation 预算。随后深审又关闭 direct-start false mounted、worker
error 被后启动线程清空、foreign lease 存在时旧代 lifecycle-only unmount、stale child
stage 遮蔽 replacement generation，以及 shutdown unlink 未与 bind 共锁五条竞态。
post-closure smoke 零失败且 cleanup 干净；最终工作树正式 `3 + 20` A/B 也以
`20/20` valid pairs、paired p50 `+4.341 ms`、95% CI 上界 `+9.619 ms` 通过
`10 ms` budget。完整证据见
[Phase 0 strict mounted checkpoint](../history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md)。

随后完整套件真实暴露 final lifecycle 已落盘、runtime bootstrap gate 尚未打开的
窄窗口，首个非 ping RPC 会被误拒绝；进一步审查还发现 shutdown 清零 bootstrap
flag 可把 stopped 误编码成 ready，以及 post-replace directory-fsync 失败时 ping
可能误报 mounted。当前 working tree 已将 durable `mounted/mounted` 与 gate 开放
放在同一 request-dispatch 临界区，失败时在释放 gate 前置 stopping，并对 callback、
active/stop、sticky worker error、worker 存活做前后校验；同进程新 daemon instance
也固定校验已分配的下一 generation。确定性 focused/expanded/restart-provider 矩阵为
`80/263/87`；旧 formal 本身不覆盖这次最终改动，所以下一段使用独立的新 artifact
完成重新验证。

最终外部证据已补齐：atomic-ready smoke 的 warm p50 为 `379.489 ms`，零失败并
clean teardown；冻结 `3 + 20` A/B 完成 `20/20` 有效 pair，control/instrumented
p50 `389.326/387.804 ms`，paired p50 `-3.562 ms`，95% CI 上界 `+8.481 ms`
低于 `10 ms` 预算，readiness `24/24`、measured resource `20/20`、cleanup 均
通过。最新完整套件为 `5338 passed, 2 skipped, 4` 个已知 additive-reload baseline
失败，未新增 startup/readiness 失败；成功/失败发布竞态各重复 `100` 轮通过。
独立 dispatch A/B 测得 gate RLock 净中位开销约 `41.385 ns/RPC`。这些只允许
声明当前 correctness/overhead gate 通过；场景、Provider、故障和平台矩阵仍未
完成，`formal_claim_allowed` 继续为 false。

S4 full-cold 正式重复随后暴露 `/proc/<pid>/stat` 与 `io` 之间的 zombie 竞态：
fresh I/O open 在 zombie 状态返回 EACCES，下一次 foreground wait 又会 reap，六个
字段只能诚实标 partial。当前 sampler 已按 `(pid,start_ticks)` 在首次 stat 身份读取
时建立有上限、no-follow、CLOEXEC 的 profile-local I/O 句柄，并用同一 proc dirfd
复核身份；它读取真实终值，不补零、不沿用旧值。保留的第一轮 formal 又证明在
cmdline/exe/cwd 分类后才建句柄仍太晚，因此获取点已前移到分类之前。最终 S4
`3 + 20` 的启动、readiness 和 process-I/O 均为 `23/23`，wall p50/p95
`1193.533/1327.391 ms`，cleanup clean；随后 warm instrumentation A/B 的
control/instrumented p50 为 `410.619/413.173 ms`，paired p50 `+2.783 ms`，95% CI
上界 `+4.274 ms`，通过 `10 ms` 预算。无特权 TASKSTATS 查询实测需要
`CAP_NET_ADMIN`，因此未扩大权限边界。该证据只关闭 S4 resource-quality slice，
整体仍为 `smoke_only`。完整失败链、digest 与边界见
[Phase 0 stable process-I/O checkpoint](../history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md)。

场景构造证据随后完成了第一轮可信闭环。早期实现存在五类假通过窗口：S1 prime
先 kill 后取 before、S4 不拒绝 attachable namespace/active runtime、same-generation
daemon 可被标成 cold、summary 不回读 manifest/SHA、spawn 异常和重复 run-id 会让
attempt/run/manifest 状态分裂。当前 harness 在任何构造器 mutation 前先 durable
写入 immutable before，ready 与 final 形成 SHA predecessor chain；summary 按 exact
run 的 benchmark/ordinal/scenario/variant/arm 重新打开并校验三份文件，同时检查
orphan attempt。authority 使用 stable double-read，generation/project/config/record
type 必须一致；原始 Agent 名称、PID、prompt、runtime record 不持久化。确定性
startup/resource 矩阵为 `114/114`。外部 S4、S1 prime+measured、一次性 S5a 分别
证明四类 identity 为 `changed`、`changed+same`、`created`，scenario/readiness/
resource/process-I/O/cleanup gate 全部通过且最终 unmounted/stopped、无进程残留。
这只关闭 S1/S4/one-use-S5a 的 construction smoke；S0/S2/S3/S5b、自动逐轮新建
S5a、故障、Provider、平台和 interactive T5 当时仍未完成，因此所有 summary 仍为
`smoke_only`、`formal_claim_allowed=false`。证据见
[Phase 0 scenario-construction checkpoint](../history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md)。

随后 S3 串行 mixed-recovery 构造器在首次外部运行中真实暴露了“结构归属”和
“进程存活”混用的 product regression：一个精确归属但死亡的 Agent pane 被当作
拓扑变化，触发整个 namespace 重建并连带重启健康 peer。working tree 现把
project/session/window/epoch 的结构证明与 active/binding 的 live 要求分层；死亡
target 仍留在 authoritative topology 中，由普通 runtime 路径定向 relaunch，健康
peer 继续 attach。确定性 stub 通过官方单 Agent restart、indexed failure latch、
HMAC slot identity、supervision cursor 和受限 raw probe 证明补偿时序；后续审查又
将 protected active set 收紧为唯一、存活、精确预期的 slot，并拒绝 caller 注入的
`STUB_LAUNCH_*` 控制，degraded path 只做一次 bounded candidate listing。聚焦矩阵
`219/219`。外部最终 AQ 样本以 `665.070 ms` 完成，daemon/generation/namespace
保持 same，target 独立 relaunched、peer identity 保持 same、Provider prepare 为
`1/0`、并发最大值 1、无 supervision 抢跑且 cleanup clean。该结果只关闭 Linux
two-Agent stub 的 S3 serial smoke；S0、S2、S5b、自动逐轮 S5a、更多 fault、真实
Provider、平台和 interactive T5 仍未完成，且尚未开始 concurrency。证据见
[Phase 0 mixed-recovery checkpoint](../history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md)。

S0 CLI-only 切片随后完成。正式测量边界冻结为精确的
`ccb_test --print-version`：wrapper `exec` 后只覆盖 Python/import/早期 CLI
dispatch，不进入 project phase2、daemon ensure、RPC、namespace 或 Provider。
普通 cold prime 只用于创建一次健康 mounted baseline；23 个 CLI-only 轮次必须
无 startup id/trace、复用同一份不可变 report sentinel，并保持 daemon、generation、
namespace、全部 configured runtime identity 不变。首个外部 smoke 正确暴露 health
门禁误拒产品成功态 `restored`，现已与 supervision contract 对齐为
`healthy|restored`，仍拒绝 failed/degraded。clean HEAD 上最终 `3 + 20` 运行达到
20/20 measured、23/23 resource/report evidence、24/24 S0 manifests、零 failure/
timeout、cleanup clean；wall p50/p95 为 `286.132/298.046 ms`，低于
`750/1000 ms` 预算。该结论只关闭 Linux ext4 + two-Agent Codex stub 的 S0，不能
外推完整启动或 real Provider；Phase 0 仍保持 `smoke_only`。证据见
[Phase 0 CLI-only checkpoint](../history/startup-phase0-cli-only-checkpoint-2026-07-17.md)。

S0 的进程计数证据按采样下界解释：23/23 profile 都观察到且只观察到一个新建
command-process identity，但 procfs 周期快照本身不能排除在两个采样点之间完整
生灭的瞬时进程。无子进程边界由 `ccb_test` 的 `execvpe`、CLI version 分支在
phase 2 前立即返回的静态调用链，以及一次隔离 Linux `strace -f -e trace=process`
中零 `fork`/`vfork`/`clone`/`clone3` 的事件证据共同支持；该单次 Linux trace
不外推为跨平台保证。

## 4. Startup Scenario Definitions

所有报告必须明确场景，禁止把不同层次的“冷/热”数据混在同一统计中。

| ID | 场景 | 初始状态 |
| :--- | :--- | :--- |
| S0 | CLI-only hot path | backend、namespace、全部 Provider 健康，只启动一次 CLI 进程 |
| S1 | Warm attach | keeper、`ccbd`、namespace、全部 Agent runtime 健康且可复用 |
| S2 | Daemon restart reuse | 新 `ccbd` generation，现有 namespace/Provider 可安全复用 |
| S3 | Mixed recovery | 多数 Agent 可复用，指定一个或少量 pane/provider 失效 |
| S4 | Full cold | 通过正式控制面完整停止后重建 namespace 和全部 configured agents |
| S5a | Pristine cold | 新建 owner-marked project 和 source home，无历史 runtime/provider cache |
| S5b | First/update start | 新安装或更新后的第一次启动，包含允许发生的一次性 cache/projection 工作 |
| S6 | Slow-filesystem cold/warm | WSL mounted drive 或受控慢 metadata 文件系统上的对应场景 |

S4/S5 只能在一次性外部测试项目中执行。不得通过删除 `.ccb`、直接 kill tmux、
手工改 runtime authority、清 Provider conversation 或修改 worker commit 来制造
“冷启动”。

S4 是 lifecycle cold：保留配置、合法 Provider cache 和受管 session，不声称是
OS page-cache cold，不允许 `drop_caches`。S5a 每轮创建新的 disposable fixture，
不复制、清除或改写真实 auth；真实 Codex/Claude 继承环境只能在单独获准的
real-provider lane 使用。

## 5. Readiness Timeline

benchmark 必须记录以下单调时间点，而不是只记录一个总 wall time：

| 时间点 | 含义 |
| :--- | :--- |
| `T0_cli_entry` | `ccb.py` 入口；更早的 wrapper/Python bootstrap 单独计量 |
| `T1_lifecycle_intent` | keeper 接受本次 startup intent/startup id |
| `T2_control_plane_ready` | 当前 generation socket、lease、PID/instance/startup identity、自检 ping 与最终 `phase=mounted/startup_stage=mounted` 一致；`starting/runtime_bootstrap` 的 ping-only 服务不计 ready |
| `T3_namespace_attachable` | 当前 namespace/session/entry window 可 attach |
| `T4_requested_agents_ready` | 显式请求或前台必要 Agent 达到可投递状态 |
| `T5_foreground_attached` | tmux client 已 attach 且第一帧稳定 |
| `T6_fully_warm` | 全部 configured agents 达到可接受 mounted 状态 |

今天的 eager foreground 语义可能令 `T5` 等待 `T6`。任何让 `T5` 提前的改造
都属于可见行为变化，必须进入 Phase 4，不能伪装成内部微优化。

当前 cold 路径已把 keeper durable `phase=starting` 后的真实接受时刻带回同一
host monotonic origin。只有 startup/generation/lease identity 与
`T0 <= T1 <= T2 <= RPC` 全部成立时才计入精确 T1；否则仍报告
`observed_upper_bound`，不得进入正式 readiness gate。warm already-mounted 路径
使用 `not_required_already_mounted`，不能复用 daemon boot T1。no-attach benchmark 的 T5 是
`not_applicable_no_attach`，interactive attach/首帧必须由独立 lane 测量。

## 6. Non-Negotiable Safety Invariants

### 6.1 Lifecycle And Authority

- 一个 `.ccb` anchor 仍只能有一个 keeper、一个 authoritative `ccbd`
  generation 和一个项目 namespace。
- `.ccb/ccb.config` 仍定义完整 desired-agent set；`requested_agents` 只能决定
  优先级和 readiness，不能缩小 daemon 的长期 ownership。
- keeper 是启动 generation 的唯一 owner；并发 worker 不得创建第二条启动权威。
- `phase=mounted/startup_stage=mounted` 只由当前 child 在 bind/listen、正常 worker
  self-ping、mounted lease、runtime bootstrap 和最终 socket/lease/PID/daemon
  instance/startup/generation 复核全部完成后发布；keeper 不得根据 interim lease
  合成 mounted。
- runtime authority、helper ownership 和 mount-attempt token 必须属于同一 slot/
  generation；旧 attempt 完成后不得覆盖新 authority。
- topology mutation、lifecycle publish 和 runtime authority commit 必须保持
  确定性单写者语义。
- Agent reuse identity 继续由 project socket/session、namespace epoch、logical
  window、slot、role 和 Provider identity 共同证明；pane/window id 只是当前
  generation locator。
- 并发失败不得通过杀死已经成功 reuse 或成功 commit 的无关 Agent 来“回滚”。
- pane recovery 的升级顺序仍为 local respawn、slot replacement、workspace
  reflow，只有 namespace 严重失信时才允许 full remount；性能代码不得跳级。

### 6.2 Provider And Communication

- Codex、Claude 等 managed home/session root 继续按逻辑 Agent 隔离；禁止共享
  active session namespace 以换取启动速度。
- 启动前必须验证 effective Provider home/session/runtime 目标唯一；只有可重建、
  不含 auth/session/conversation 的 immutable asset 才允许进入 shared cache。
- 不得出现 cross-agent、cross-project、cross-provider 或 cross-generation
  session adoption。
- Provider 启动未达到 actionable binding 前，不得向 pane 注入 ask payload。
- foreground-first 若允许提前提交 ask，任务必须先进入 durable dispatcher
  authority 并等待目标 ready；若该保证不能成立，应返回稳定的
  `agent_warming` 类状态，不能静默丢失或注入错误 session。
- plain ask、queued ask、`ask --chain`、reply delivery、cancel、retry/resubmit
  在启动和 warming 边界都必须 exactly-once 收敛。
- 失败补偿只能清理当前 attempt 明确拥有的 pane/helper/launch residue；禁止
  project-wide Provider 扫描、`kill-server` 或杀死无关成功 Agent。

### 6.3 Test And Environment

- 源码验证只使用 `/home/bfly/yunwei/ccb_source/ccb_test`，并从
  `/home/bfly/yunwei/test_ccb2` 下的外部项目运行。
- 除非测试明确验证继承环境，否则设置隔离的 `HOME` 和 `CCB_SOURCE_HOME`。
- 不使用 installed `ccb` 验证当前源码，不把 `ccb_source` 当 source runtime
  project，不设置 `CCB_SOURCE_RUNTIME_OK=1` 绕过隔离。
- 真冷启动只使用正式 `ccb_test kill`/测试控制面路径；不直接删除 `.ccb` 或
  kill Provider/tmux 进程。
- benchmark 不读取、记录或输出 API key、token、完整 Provider prompt 或
  Provider conversation；进入仓库、公开 CI 或 release 的结果必须对 Agent 名称、
  窗口拓扑和本机路径做 alias/脱敏。
- 真实 Provider 验收只要求 Codex primary 和 Claude secondary；其他 adapter
  使用 fake/stub/source regression，不因缺少真实凭据阻塞本 Goal。
- diagnostics/report 写入失败不得覆盖原始 startup failure，也不得把失败 runtime
  标记 healthy。

## 7. Root-Cause Hypotheses To Prove Or Reject

优化前必须通过指标证明每个候选成本，不得根据函数大小或主观感觉选择改造。

1. 串行 `start_agent_runtime` 令 Provider launch 和 binding 等待线性累加。
2. `agent_runtime_commit` 指标混合了可并行 launch 与必须串行的 authority commit。
3. tmux 每 pane 多次 subprocess、identity 设置和 ready probe 仍有可批处理空间。
4. Provider profile/home/session projection 在冷启动存在重复扫描、hash 或写入。
5. CLI shell/Python bootstrap、解释器校验和 eager imports 占据稳定固定成本。
6. start RPC 成功后，sidebar/layout summary/maintenance 工作仍阻塞前台 attach。
7. configured-agent eager mount 与 foreground readiness 被绑定得过紧。
8. stale/foreign binding、window identity 或 generation 判断错误可能制造假 relaunch。
9. durable atomic write、目录 fsync 和全局扫描在慢 metadata 文件系统上放大。
10. Provider 进程在后台初始化造成 CPU/内存/I/O 竞争；提高并发度可能先变慢、
    OOM 或增加 session race，而不是自动加速。
11. 当前 lifecycle contract 要求 request handler 与 maintenance/reconcile tick
    共享一个串行 worker lane，而实现已经存在 request worker 和 maintenance
    thread 两条执行线；在增加 startup worker 前必须确认写入仲裁是否等价，或先
    收敛 contract/source 漂移。

严格 mounted 调查已证明并修复另一条 correctness 根因：keeper steady-state
reconcile 曾把 `starting/runtime_bootstrap` 的 interim lease 提前提升为
`mounted/runtime_bootstrap`。这项已从假设转为 retained failure、generation-fenced
修复和确定性回归，不再作为待验证的性能猜测。

每项结论必须链接代码路径、counter/timing 和可重复 artifact。发现 correctness
bug 时先以独立 patch 修复和回归，再继续性能实验。

## 8. Phase Plan

本节的 Phase 是本 Goal 的执行顺序。Goal Phase 3 对应现有架构计划的 P4
bounded launch concurrency；Goal Phase 4 对应其 P5 foreground-first
readiness，二者不重写原有 P0-P5 命名。

### Phase 0: Measurement Contract And Dedicated Harness

目标：先让每一毫秒、每次 relaunch 和每个副作用可解释。

Deliverables:

- 新增独立启动 benchmark harness，建议入口为
  `dev_tools/perf_ccb_startup.py`；不得把 lifecycle CPU sampler 的采样点误当
  成重复启动。
- 每一轮从外部测量 CLI wall time，并在下一轮覆盖前立即复制、解析和校验
  `.ccb/ccbd/startup-report.json`；报告的 trigger、generated time、config
  signature 和 daemon generation 必须与该轮一致。
- 定义 versioned JSON schema，至少记录 commit/version、source/install mode、
  平台、文件系统、CPU/RAM、Agent/window/provider 数、场景、restore policy、
  iteration、exit status、readiness 时间点、阶段/Agent 子阶段、资源计数和
  cleanup 结果。
- 同时记录 wall critical path 和 cumulative work；单独报告 CLI pre-RPC、daemon
  ensure、start RPC、CLI post-RPC、attach，以及 `external_wall -
  supervisor_total`，避免并发后用任务 duration 总和冒充用户等待时间。
- 将每个 Agent runtime duration 拆成：
  `prepare_launch_context`、`build_start_cmd`、`tmux_respawn`、
  `pane_identity`、`session_write`、`provider_post_launch`、
  `binding_resolve`、`authority_commit`、`restore_bookkeeping`。
- 增加 tmux command、subprocess spawn、process snapshot、projection file/byte、
  provider preparation、durable write/skip、helper spawn 和 orphan cleanup 计数。
- 保留现有 lifecycle profiler，用它同步采样 CPU、RSS、process count、I/O，
  通过共同 run id 与启动 artifact 关联。
- 扩展 deterministic Provider stub，支持 launch delay/barrier、active concurrency
  counter、按 Agent/阶段失败和 cancellation 注入；现有 request-delay stub 不能
  代替 startup concurrency 证明。

Harness safety contract:

- 默认 raw artifact 写入外部
  `/home/bfly/yunwei/test_ccb2/perf_artifacts/startup/<benchmark-id>/`，每轮保存
  `run.json`、启动报告快照、脱敏 identity 摘要和 cleanup verdict，最后生成
  `summary.json`。
- fixture 必须有 harness owner UUID marker 和独占 benchmark lock；缺 marker、
  lock 冲突或项目位于 source checkout 时 fail closed。
- 校验绝对 `ccb_test` 的 realpath/source sha、允许测试根、隔离 HOME；检测到
  `CCB_SOURCE_RUNTIME_OK` 时拒绝运行。
- 非交互 latency run 强制 `CCB_NO_ATTACH=1`。冷启动仅调用正式 `ccb_test kill`
  并等待 stopped/unmounted；kill 不收敛时先归档证据并停止，禁止删除状态、
  global `pkill` 或直接改 tmux。
- baseline/candidate source A/B 使用两个 clean source worktree/sha、独立
  project/HOME 和绝对 wrapper，不修改、reset 或复用当前 dirty main
  worktree。仅用于量化 harness instrumentation on/off 的 A/B 必须固定同一
  source SHA、同一 owner-marked fixture、同一 generation/reuse identity，并用
  显式 control/instrumented arm，不能把 worktree/cache 差异混进观测开销。

当前 harness CLI：

```bash
python /abs/source/dev_tools/perf_ccb_startup.py \
  --project-root /home/bfly/yunwei/test_ccb2/startup-perf-<uuid> \
  --ccb-test /abs/source/ccb_test \
  --scenario warm|full-cold|pristine|partial \
  --iterations 20 --warmup 3 \
  --launch-cap 1|2|3|4 \
  --instrumentation-mode profiled|instrumentation-ab \
  --resource-sample-interval-ms 50 \
  --result-root /home/bfly/yunwei/test_ccb2/perf_artifacts/startup
```

当前只接受已实现的 `warm`、`full-cold` 和单轮 `pristine` 语义；
`launch-cap > 1` 与无正式 constructor 的 partial recovery 会 fail closed，避免
生成标签正确但实际未执行的性能结果。默认启动命令由 harness 自己持有
`Popen`，预启动 full-discovery baseline 不计入 command wall，运行中仅追踪
foreground root、runtime authority、已观察 identity 和 descendant。资源采样
失败只降低 qualification；run-id/digest/coordinate 冲突属于 measurement
integrity failure。Linux process-I/O 对每个 `(pid,start_ticks)` 使用 profile-local、
有上限、CLOEXEC 且同一 proc-dirfd 复核身份的只读句柄；这允许在 zombie/reap
窗口读取真实终值而不是补零或沿用旧值。句柄读取失败仍保持 partial，整体 I/O
仍是 sampled lower bound。

Measurement rules:

- 每个正式结论至少 `3` 次不计入统计的 warm-up 和 `20` 次有效重复。
- baseline/candidate 使用相同机器、配置、Provider/model、restore policy 和
  cache 分类；按 ABBA 或交错顺序运行，避免温度、page cache 和系统负载漂移。
- 不删除 outlier；失败和 outlier 必须保留并分类。
- 同时报告 n、min、p50、p90、p95、max、mean/stddev、MAD/IQR、CV、failure/
  timeout count、CPU-seconds、peak RSS 和资源残留；A/B delta 应带 paired 或
  bootstrap confidence interval。
- instrumentation 在 S1 warm daemon path 的额外 p50 开销不得超过
  `max(10 ms, 2% of control p50)`，并应聚合后一次落盘，不能逐事件同步 fsync。

Exit gate:

- harness 自身有单元测试，能拒绝 source checkout、live work project 和不允许
  的测试根。
- 同一 run 的外部 wall、startup report 和资源 profile 可按 run id 对账。
- 至少 `90%` 的 warm/cold wall 可归因到已命名阶段，剩余部分有明确
  `unattributed` 数值而不是被吞掉。
- S0-S5 至少各有一个 fake/stub smoke artifact；正式性能声明仍须满足完整
  重复次数。

### Phase 1: Correctness-First Startup Audit

目标：在并发前清除会放大耗时或破坏结果的 bug。

Audit scope:

- 对比当前实现、已知稳定 release 和近期 startup/lifecycle PR 的语义差异，
  重点看 reuse classification、namespace identity、restore、provider prepare、
  session binding、foreground wait 和 shutdown/recovery。
- 证明 healthy reuse 为零 Provider prepare、零 relaunch；真实 launch 每 Agent
  仅一次准备和一次 helper ownership 提交。
- 检查 no-op runtime/spec/workspace/profile 写入、tmux/global process snapshot、
  pane relabel 和 layout rebuild 是否仍重复。
- 使用 S3 mixed-recovery 和 fault injection 区分“正确恢复”与“错误全量重建”。
- 审计 socket request worker、maintenance thread、post-request tick 和
  `start_maintenance_lock` 的真实写入顺序；在 contract 与实现没有明确一致前，
  不增加第三条可写 startup lane。
- 将发现的问题按 correctness bug、measurement defect、performance-only cost
  分类，分别落独立 patch 和测试。

Exit gate:

- reuse、single-dead-pane、foreign binding、wrong window、generation change、
  restore fresh/resume 和 failed launch 均有确定性测试。
- 没有未解释的全量 relaunch、重复 Provider helper 或 authority generation 跳变。
- 修 bug 后 warm path 不回退，且 cold 样本改善不以缩小功能范围获得。

### Phase 2: Low-Risk Serial-Path Reduction

目标：先减少总工作量，再考虑并发隐藏 wall time。

Candidate work, subject to evidence:

- CLI/launcher lazy import、缓存解释器验证结果、将非启动命令模块移出热入口。
- tmux request-scoped snapshot、命令 batching 或长期 control client，减少每 pane
  subprocess 往返。
- Provider preparation single-flight、共享 immutable projection fingerprint，
  保持 per-agent active home/session 独立。
- 跳过 canonical content 未变化的 durable writes 和 identity writes。
- 将不影响 startup success 的 release advisory、诊断 summary、sidebar refresh、
  maintenance ensure 从前台关键路径移出；失败仍需可观察。
- 只在 profile 证明 Python 路径仍为热区时采用 Rust/native helper，不做宽泛重写。

当前 shared projected-tree bundle 和 Claude binary cache 使用可预测的固定临时
路径，部分 Claude hook migration/project-memory seed 也可能写项目级共享位置。
在这些写入具备 single-flight/lock、唯一临时路径或被证明为串行前，不得进入
并发 preparation pool。

Exit gate:

- 每个 patch 有单独 before/after；目标阶段至少改善 `5%` 或 `20 ms`，否则不以
  复杂度换取噪声级收益。
- 任一 cold-only 优化不得使 S1 warm p95 回退超过
  `max(50 ms, 5%)`。
- 语义、输出和状态文件兼容；关闭新优化无需数据迁移。

### Phase 3: Bounded Prepare And Launch Concurrency

目标：把可并行的 Provider-local 工作并发化，同时保持共享 authority 串行。

Required pipeline:

```text
load authority once
  -> ensure namespace
  -> capture immutable tmux/process snapshots
  -> classify all agents serially
  -> prepare launch set in a bounded pool
  -> sequence tmux respawn/identity mutations through one ordered lane
  -> wait for provider readiness under provider-specific caps
  -> resolve/validate candidate bindings in read-only workers
  -> commit runtime/helper authority serially in topology order
  -> publish requested/full readiness
```

Concurrency rules:

- classification 输入冻结后才允许创建 worker；worker 不读取变化中的 config 或
  lifecycle authority。
- 启动异步工作前先建立 slot-scoped mount-attempt ownership；没有 attempt fence
  的 future 结果不得进入 commit queue。
- 初始实验 global cap 为 `1/2/3/4`，不得加入 unlimited 选项；默认继续为 `1`
  直到 Phase 3 gate 完成。
- preparation pool 上限不超过 `min(4, cpu_count)`；Provider launch cap 由
  Codex/Claude 实测分别决定，不能从显示名称或 stub 速度推断。
- tmux namespace、pane respawn 和 identity mutation 通过一个确定性 command
  lane 发出；并发的是 respawn 后的 Provider 初始化/readiness 等待，不把整个
  `start_agent_runtime()` 直接提交线程池。
- shared immutable projection 使用 content-fingerprint single-flight；active
  Provider home、session file、completion artifacts 和 helper ownership 不共享。
- generation change、shutdown intent 或 startup cancellation 必须阻止尚未 commit
  的旧 worker 写 authority。
- 未知 Provider、未证明 home/cache 写入隔离的 Provider，launch cap 默认为 `1`。
- launch 失败按 Agent 聚合；成功 reuse/launch 的无关 Agent 保持有效，不执行
  project-wide rollback kill。
- 必须保留一个不改变持久化格式的 serial fallback，供运行时/发布回退。

Proposed experiment profiles（只是测试档位，不是默认配置）：

| Profile | Prep pool | Global readiness | Codex | Claude | Purpose |
| :--- | ---: | ---: | ---: | ---: | :--- |
| `S0` | 1 | 1 | 1 | 1 | 串行基线 |
| `P2` | 2 | 1 | 1 | 1 | 仅 preparation 并发 |
| `P4` | 4 | 1 | 1 | 1 | preparation 压力边界 |
| `L2` | 4 | 2 | 2 | 1 | 保守 readiness 并发 |
| `L4a` | 4 | 4 | 3 | 1 | 首选候选实验 |
| `L4b` | 4 | 4 | 4 | 1 | Codex 压力边界 |
| `X6` | 4 | 6 | 4 | 2 | 只探索，不得直接默认 |

Exit gate:

- fake/stub race/fault matrix 连续至少 `100` 轮，无 duplicate launch、stale
  authority write、session crossover、deadlock 或不可回收 helper。
- 完整真实 Codex primary 和 Claude secondary 冷启动各有至少 `20` 轮，结构性
  启动失败为 `0`。
- 对十五 Agent S4，candidate 相对 serial baseline 的 full-ready p95 至少改善
  `25%`，否则不默认启用并发。
- peak RSS 增幅不超过 `25%`，CPU-seconds 不增加超过 `15%`，结束后 process/
  fd/helper 数回到预期基线。
- 同配置 S1 warm p95 不发生超过既定回退门槛的退化。

### Phase 4: Optional Foreground-First Readiness

目标：在不伪装 fully-warm 的前提下缩短用户可见等待。

Required behavior:

- 默认关闭，使用明确实验开关；不能与 Phase 3 在同一首个 landing patch 中启用。
- background warming 必须由 daemon-owned、可恢复的 scheduler 管理，不能由
  即将退出的 CLI 局部线程或无 authority 的 detached helper 管理。
- `control_plane_ready`、`namespace_ready`、`requested_agents_ready`、
  `foreground_attached`、`fully_warm` 必须是可查询的不同状态。
- entry window 和显式 requested agents 优先；其余 configured agents 在受限
  CPU/内存预算下后台启动。
- 只有 `namespace_ready=true` 且 `requested_agents_ready=true` 才允许前台
  attach；`fully_warm=false` 必须保持可见。
- sidebar/doctor 清楚显示 warming、ready、degraded 和 failed；不得把 placeholder
  pane 报为 healthy Agent。
- ask 对 warming target 的行为必须遵循 6.2：durable queue 或稳定、可重试的
  warming 状态，不能丢失、乱序或写入旧 session。
- `ccb kill`、reload、generation replacement 必须能取消或接管 background
  warming，不留下旧 worker 或 orphan Provider。
- 每个 background attempt 必须同时校验 `mount_attempt_id`、daemon generation、
  startup id、config signature 和 namespace epoch；任一 fence 变化后旧 attempt
  只能写诊断，不能再提交 runtime authority。

Exit gate:

- 十五 Agent 项目 `namespace_attachable` p95 初始目标 `<= 2.0 s`。
- 前台 attach 后全部后台 Agent 最终进入 ready/degraded/failed 的有界终态；
  不允许永久 warming。
- Phase 4 fully-warm p95 不得比同一 candidate 的 eager Phase 3 模式恶化超过
  `10%`。
- foreground attach 期间执行 plain/queued/chain/cancel/reply-delivery 场景，
  无丢失、重复、错误 sender/target 或 delivery loop。
- 经过单独 contract review 和 opt-in real-provider qualification 后，才讨论默认
  策略；Phase 4 通过不等于可以默认发布。

### Phase 5: Platform, Scale, And Failure Qualification

目标：证明收益不是单机、单 Provider 或 cache 偶然结果。

Required matrix:

- Agent scale: `1 / 8 / 15 / 32`。
- Topology: legacy single-window、explicit one-window、explicit five-window。
- Provider: deterministic fake/stub；真实 Codex primary；真实 Claude secondary。
- Lifecycle: S0-S6、restore fresh/resume、single-pane death、mixed reuse/relaunch、
  daemon generation replacement、update-first-start。
- Platform/filesystem: Linux local、macOS、WSL ext4、支持的 mounted-drive path。
- Concurrency: serial baseline 与 candidate caps `2/3/4`，顺序交错。

Fault injection:

- tmux inspect/respawn/identity command failure。
- Provider executable missing、prepare failure、post-launch failure。
- session write、binding resolve、authority commit、restore write failure。
- startup-report write failure、shared cache publish 冲突和固定临时路径竞争。
- generation 在 prepare/launch/commit 三个边界分别变化。
- 启动中收到 reload、kill、restart、ask、cancel 和 reply delivery。
- 慢 Provider、挂起 Provider、资源不足、文件描述符/进程创建失败。

Exit gate:

- 所有 correctness assertions 跨平台一致；平台差异只能影响预算，不能放宽
  authority/session/communication 规则。
- 每个 non-pass 有稳定 failure taxonomy 和原始 artifact，不能隐藏重试或改用
  更强 Provider 伪造通过。
- 清理后项目 unmounted 或恢复到预期 mounted generation，零不可解释 residue。
- release/soak gate 至少包含 `100` 次 warm cycle、`30` 次 cold/partial cycle，
  以及启动中 ask receipt 到最终 exactly-once reply 的完整闭环。

### Phase 6: Rollout, Default Decision, And Release Gate

目标：以可回退方式把通过验证的优化交付给用户。

Rollout order:

1. measurement-only release or hidden diagnostics。
2. serial-path low-risk improvements。
3. bounded concurrency opt-in/canary。
4. foreground-first opt-in/canary。
5. 达成长期 SLO 和错误率门槛后，分别做 default-on decision。

Required rollback:

- 一次配置或实验开关即可回到 serial eager semantics。
- 回退不要求删除 `.ccb`、清 Provider history、重建 worktree 或降级 state schema。
- candidate 失败时保留 startup report、per-agent failure、helper ownership 和
  cleanup evidence。
- 只有在任何 pane/provider mutation 发生前，才允许自动切回 serial 重试；一旦
  部分启动已经发生，只能保留成功项并对失败 slot 做有界恢复，不能整批重跑。
- release smoke 证明安装包、installed/source 边界和 rollback 开关有效。

Release notes 只描述通用启动性能、可靠性与兼容性结果；不得包含私人 Agent
名称、窗口拓扑、工作流内容、prompt、session 路径或测试项目细节。

## 9. Initial Performance And Reliability Budgets

这些是 Phase 0 后可按证据修订的初始目标，不得通过减少 configured agents、
关闭 restore、替换更快 fake Provider 或放宽正确性来达成。

| 场景 | 初始目标 |
| :--- | :--- |
| S0/S1 完整 CLI wall | p50 `<= 0.75 s`, p95 `<= 1.0 s` |
| S1 daemon supervisor | p50 `<= 0.30 s`, p95 `<= 0.50 s` |
| S2 daemon restart with live namespace/providers | p95 `<= 2.0 s` |
| S4 十五 Agent fully warm | p50 `<= 5.0 s`, p95 `<= 6.0 s` |
| Phase 4 namespace attachable | p95 `<= 2.0 s` |
| 三十二 Agent scale | 不出现超线性失控；p95 不超过同机十五 Agent 的 `2x` |
| 支持的慢文件系统 | 无未解释的单次运行超过 `12 s` |

所有 accepted candidate 还必须满足：

- `20/20` 真实冷启动无 lifecycle/session/authority 结构性失败。
- session crossover、duplicate helper、lost/duplicate ask、reply-delivery loop、
  stale generation overwrite 和 orphan Provider 均为 `0`。
- warm p95 回退不超过 `max(50 ms, 5%)`。
- 启动期间 ask receipt p95 相对 serial baseline 回退不超过 `20%`，且最终回复
  不丢失、不重复、不循环。
- full-start CPU-seconds 增幅不超过 `15%`，peak RSS 增幅不超过 `25%`。
- 退出或回退后进程、fd、pane、helper 和 runtime authority 数量可对账。

## 10. Automated And Runtime Test Gates

### 10.1 Focused Source Tests

至少覆盖：

- `test/test_v2_ccbd_start_flow.py`
- `test/test_v2_ccbd_start_matrix.py`
- `test/test_ccbd_start_preparation.py`
- `test/test_ccbd_start_agent_runtime.py`
- `test/test_ccbd_start_binding.py`
- `test/test_ccbd_startup_pane_snapshot.py`
- `test/test_v2_runtime_launch.py`
- `test/test_v2_runtime_launch_session_files.py`
- `test/test_cli_runtime_launch_tmux_panes.py`
- `test/test_ccbd_supervisor_lifecycle.py`
- `test/test_ccbd_supervisor_namespace.py`
- `test/test_ccbd_tmux_namespace.py`
- `test/test_v2_ccbd_keeper.py`
- `test/test_v2_daemon_startup_wait.py`
- `test/test_v2_start_service.py`
- `test/test_v2_start_foreground.py`
- `test/test_v2_cli_kill.py`
- `test/test_ccb_restart.py`
- `test/test_perf_ccb_startup.py`
- `test/test_perf_process_resources.py`

Phase 3/4 还必须加入：

- 并发顺序、generation fence、partial failure 和 cancellation 专项测试。
- `test/test_ask_cli.py`
- `test/test_v2_ask_service.py`
- `test/test_v2_ccbd_dispatcher.py`
- `test/test_reply_delivery_start_completion.py`
- `test/test_codex_reply_delivery.py`
- `test/test_v2_message_bureau_dispatcher_integration.py`

### 10.2 Source Runtime Validation

所有 stateful source smoke 从外部测试项目运行：

```bash
cd /home/bfly/yunwei/test_ccb2
env -u CCB_SOURCE_RUNTIME_OK \
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test --diagnose

env -u CCB_SOURCE_RUNTIME_OK \
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test config validate --json
```

启动 benchmark 统一使用 `dev_tools/perf_ccb_startup.py`。临时 shell 循环、旧
lifecycle profiler 的采样点、未绑定 native run id 的资源报告，以及未通过
owner marker/lock/source fingerprint/正式 cleanup gate 的结果都不是正式验收
证据。

### 10.3 Required Post-Run Audit

每组 runtime 测试结束后必须检查：

- lifecycle、lease、startup id、generation 和 socket holder 一致。
- configured runtime、pane、session、helper ownership 一一对应。
- 无旧 generation worker、bridge、Provider process、socket 或 pane 残留。
- queue、active job、pending reply、reply delivery 和 callback continuation 收敛。
- cleanup 使用正式控制面完成，测试项目回到预期 mounted 或 unmounted 状态。

## 11. Evidence And Handoff Contract

每个 Phase 的交付必须包含：

- 变更假设及对应 baseline artifact。
- 修改文件和 authority surface。
- exact test/benchmark commands、版本、commit、平台和 Provider/model id。
- before/after p50、p95、max、failure count、CPU-seconds、peak RSS。
- correctness/fault matrix 结果及所有 non-pass 分类。
- cleanup/residue audit。
- feature flag/default 状态和单步 rollback 方法。
- 已知风险、未覆盖平台和下一 Phase 的首个具体任务。

含原始 startup report 的 artifact 只保存在访问受限的外部测试项目；CI artifact
和进入仓库的 PlanTree evidence 必须脱敏，只保留可复核汇总、artifact digest/
位置和结论，不复制凭据、私人 prompt、Provider conversation、Agent 名称或私人
拓扑。

当前 Phase 0 checkpoint：
[history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md](../history/startup-phase0-readiness-attribution-checkpoint-2026-07-17.md)。

Instrumentation A/B checkpoint：
[history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md](../history/startup-phase0-instrumentation-ab-checkpoint-2026-07-17.md)。

Lifecycle transaction checkpoint：
[history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md](../history/startup-phase0-lifecycle-transaction-checkpoint-2026-07-17.md)。

Generation fence checkpoint：
[history/startup-phase0-generation-fence-checkpoint-2026-07-17.md](../history/startup-phase0-generation-fence-checkpoint-2026-07-17.md)。

Exact T1/resource checkpoint：
[history/startup-phase0-exact-t1-checkpoint-2026-07-17.md](../history/startup-phase0-exact-t1-checkpoint-2026-07-17.md)。

Strict mounted/self-ping checkpoint：
[history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md](../history/startup-phase0-strict-mounted-checkpoint-2026-07-17.md)。

Stable process-I/O/S4 checkpoint：
[history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md](../history/startup-phase0-stable-process-io-checkpoint-2026-07-17.md)。

Scenario-construction/S1-S4-S5a checkpoint：
[history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md](../history/startup-phase0-scenario-construction-checkpoint-2026-07-17.md)。

Mixed-recovery/S3 serial checkpoint：
[history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md](../history/startup-phase0-mixed-recovery-checkpoint-2026-07-17.md)。

CLI-only/S0 checkpoint：
[history/startup-phase0-cli-only-checkpoint-2026-07-17.md](../history/startup-phase0-cli-only-checkpoint-2026-07-17.md)。

## 12. Completion Criteria

只有同时满足以下条件，本 Goal 才能标记 Complete：

1. 独立启动 benchmark 和细粒度 startup-report contract 已落地并经过 harness
   自测。
2. 已发现的 correctness bug 均有独立修复、回归和 plan-to-landing evidence。
3. serial-path 与 bounded-concurrency 候选完成 before/after，达到预算或明确记录
   为 rejected experiment。
4. foreground-first 若未通过 contract/real-provider gate，保持 opt-in 或不落地，
   不影响前述 Goal 对 eager path 的完成判断。
5. Linux、macOS、WSL 和慢文件系统矩阵完成，或未支持平台被明确列为 blocker/
   qualified scope，而不是静默跳过。
6. 真实 Codex/Claude 验收、ask/reply 启动边界回归、故障注入和零残留审计通过。
7. 默认策略、回退路径、诊断输出和 release notes disclosure gate 均有明确证据。

## 13. Open Decisions Before Execute-Ready

以下问题必须在对应 Phase 开始前冻结，不阻止 Phase 0 measurement：

1. Phase 3 各 Provider 的最终并发 cap 和全局资源预算。
2. foreground-first 下，未 ready target 的 ask 是 durable queue 还是明确
   `agent_warming`；不能两者随机切换。
3. 性能实验开关使用环境变量、隐藏 CLI 选项还是 config 字段，以及何时成为
   稳定公开接口。
4. macOS/WSL runner 的标准硬件和慢文件系统基准环境。
5. raw benchmark artifact 的 CI retention 和脱敏汇总格式。
6. request worker、maintenance worker 和未来 startup scheduler 如何共享唯一
   authority-write/commit boundary，以及对应 contract 是回归单 lane 还是显式
   接受当前多线程模型。
