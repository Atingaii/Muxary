# Muxary 工作目录、画布与交互：分层验收

日期：2026-11-11。范围来自用户已确认的 Q8/Q9；不是完整 IDE、第二套调度器或每任务工作树管理器。上游基线仍为 CCB 8.7.22 / `df98e61e91b4be57873029b01667135e6265f371`。初版历史见[原验收](muxary-validation.md)，本报告不反写其样本、测试数和失败。

## 1. 已实现与来源

- 默认专注视图，右侧上下文按需打开；可切换可平移/缩放/拖动的摘要画布，筛选、自动排列、适应视图及键盘/窄屏列表。导航、画布与 composer 共用唯一项目/Agent 选择；卡片不内嵌逐节点终端、会话或派活框。
- 项目 → CCB 实际报告的工作目录 → Agent；仅同 basename 碰撞时直接显示完整目录。共享路径明确无写入隔离，未知路径不猜项目根。真实 scoped diff 标注 tracked/unstaged、非 Agent 产出归因。
- 标准项目打开 dialog，只有明确提交本机路径才通过原 `ccb --safe` 启动；已运行项目不重启，managed worktree 映射回原项目。原配置页承载 worktree 配置/创建/激活，不另造生命周期或静默热换 cwd。
- 快速导航、移动抽屉互斥/焦点恢复、终端 Resizable 与来源分离。一个全局终端实例，显式接管；无自动输入重放。
- 保留 CCB 内部格式与脚本协议。`muxary` 默认 Web，`muxary tui`、兼容 `ccb` 及转发子命令保持原含义。后更新入口与安装器都优先 `MUXARY_BIN_DIR`、其次兼容 `CODEX_BIN_DIR`。

不是只参考一个 Basic：Card、Command、Resizable 在 21st 选择后，适配固定公开 shadcn 上游；聊天沿用固定 Agent Elements 源码。React Flow 是独立成熟画布引擎，不冒称 21st 源码；标准 dialog/details、原 xterm 能满足的部分不加第二套库。两套 vendor 都保留 MIT/SOURCE/hash，主项目保留 AGPL。[逐功能矩阵、许可和取舍](muxary-expansion-product-review.md#6-逐功能复用矩阵)。

已通过真实 CodeBuddy CLI 的两个模型做两轮交叉产品评审及 Q9 增量复核；每轮请求、报告模型身份、原始 SHA 和采纳/拒绝意见均分开记录。模型没有亲自看图或执行浏览器/性能测试。见[两轮评审](muxary-expansion-product-review.md)、[Q9 模型复核](muxary-q9-product-review.md)。CodeBuddy 原生 ask/clear/compact/resume 的既有真实单版本证据见[独立报告](codebuddy-live-validation.md)，不由 UI stubs 继承真实联通。

## 2. 自动化与构建

本机私有证据根为 `~/.local/share/muxary-dev/expansion-review/`，原始失败、runner、manifest 与 screenshots 保留，不提交令牌、凭据、原生完整对话、浏览器 storageState 或模型内部 reasoning。

| 层次 | 实际结果与来源 | 限定 |
| --- | --- | --- |
| 前端最终功能源码 | `npm --prefix web test`，**86 passed / 6 files**；`q9-frontend-final.log` | jsdom/边界替身，不替代真实浏览器或真实输入法 |
| 生产构建 | `npm --prefix web run build`，tsc + Vite 成功；`q9-build-final.log`、`q9-notices-build.log`、`q9-licenses-final-build.log` | vendor 的 use-client directive 警告保留；没有据此宣称其他打包器通过 |
| Python 完整快照 | **8579 passed / 82 skipped / 1 failed**，8662 collected，2317.99s，exit1 | 开始早于 Q9，不能当最终补丁完整全绿 |
| 旧 11 个失败定向复核 | **11 passed**，48.09s | 不抹除本次新增的那个失败 |
| Q9 最终 affected | **176 passed**，52.53s，`q9-adversarial/preflight-configured.log` | 包含原172、新fresh-candidate三例与preflight一例；不当成完整快照重跑 |
| release notices 与许可证附录门槛 | 原 notices 3F→15P；两附录6F→21P；第三附录3F→最终 **24 passed** | 缺失/空/空白及 tar 原文保留；真实Vite生成内容另核 |
| release/identity/provenance 最后复核 | **112 passed**，1.63s，`q9-release-identity-final.log` | 包含下面24与69项，不能重复相加当独立测试总数 |
| update 命令入口 | `test/test_cli_management_update.py` **69 passed**；新增4种目录优先级先2F再4P | 不代表真的发布/下载/安装一个新release |

完整回归的唯一失败为 `test_ccb_long_running_job_keeps_heartbeat_and_doctor_healthy`。未改源码、4秒stub时长、deadline或断言，隔离重跑仍失败；实际任务在后续 ping 返回前已 completed，原“连续多次 CLI 观测时始终 active=1”的时间假设不成立。这支持有界时序诊断，不证明 heartbeat core 故障，也不证明所有生命周期/性能性质都正常。完整失败与分阶段176项范围、SHA、真实时序见[后端报告](muxary-backend-expansion-validation.md)。

真实 Vite notices 修复使用已有 Vite8 原生 `build.license`，输出 `assets/workbench/THIRD_PARTY_NOTICES.md`，不是自造依赖收集器。第一次核实输出 **149224 bytes**；新增该文件前后的全部既有 JS/CSS/index 哈希相同。release 在删除 stage/node_modules 前必须校验非空 notices，tar 回归要求保留正文。它不替代源码 vendor 的独立 MIT 声明。

最终另外交付 `licenses/Apache-2.0.txt` 官方全文、`react-remove-scroll-bar-upstream-MIT.txt` 同项目固定上游许可和来源 README，Vite public 原生复制，release 校验三文件非空。最终实际生成14个文件；`q9-after-licenses-final-build.json` / `q9-licenses-final-delta.json` 留存 SHA。该次最终重建的 CSS/index 及引用 chunk hash 有变化，**不能把第一次 notices 单因素的字节不变结论扩展到最终构建**。`react-remove-scroll-bar@2.3.8` npm 声明MIT但没有内置LICENSE，声明gitHead不可公开读取；附录明确来自固定上游master、其package仍2.3.7，不冒充已核实2.3.8发布commit或源码等同性证明。

## 3. 浏览器与截图

### 完整工作流

`acceptance-attempt-07/browser-acceptance.json` 与最终静态资产的 `acceptance-attempt-08/browser-acceptance.json`：各 **8/8 场景通过，0 page errors**。Playwright 的独立非持久、无账号登录 context；真实本机 CCB/BFF + 独立 CodeBuddy/Codex CLI stubs，不调用模型。默认 Chrome **151.0.7922.10**，1440×1000 / 390×844。不要与性能试验显式选用的 Chrome156 混为同一环境。

覆盖默认专注/收起上下文、实际绑定目录/共享提示及 scoped diff、Command搜索/键盘/焦点、不发任务的画布导航/草稿保留/平移缩放排列、一个显式原生终端/键盘resize/换Agent关闭不自动接管、真实stub Job接收至completed、任务与原生会话分源、移动互斥抽屉/inert/Tab/Esc/焦点恢复/无横向溢出、桌面resize和深色。主审逐一查看了11张最终截图，不把自动截图存在当作已经审图。

### Q9 增量及保留的失败

- `q9-browser-acceptance-01`：前三步通过；后续实际打开/Job/终端已经发生，但 runner 找不存在的“关闭终端”按钮超时。保留失败；正确动作是“原生终端” toggle，不为此改产品。
- `q9-browser-acceptance-02`：前五步通过，包含真实新项目 `200 ready` → 新项目 Job completed → xterm；再次打开同一目录 namespace epoch **2 不变**。第六步误取了原配置页隐藏的第一个 workspace select 而超时；保留此失败，不能把整次运行叫全过。
- `q9-config-mobile-acceptance`：原配置页可见编辑器的真实 worktree option 验证通过；严格要求最后一个控件 Tab 后 document.activeElement 仍在 dialog 的假设失败。
- `q9-config-mobile-acceptance-02`：两步通过，0 page errors。实际记录 Tab 后 activeElement=BODY，下一次Tab回dialog；尝试聚焦背景搜索框不能移出modal，390px无溢出，Esc恢复原触发器且无启动POST。原生dialog允许浏览器chrome焦点，不冒称“永远锁在页面DOM内”；保留前次失败和修正后的独立协议。
- `q9-browser-acceptance-03`：显式停止仅测试新项目后再打开，返回503 unknown，随后只读GET发现项目mounted。这是一个真实未确认结果，**不是200**；没有重放POST来抹除失败。独立检查另证实一个 fresh-read-after-return registry 窗口，修复与后续验收另录；现有日志不足以把此次503精确归因给该窗口或原CCB短时view缓存。

- `q9-browser-acceptance-04`：重启BFF加载 fresh-candidate 修复（service `47dab3be…`）后，最终静态构建 **7/7 场景通过、0 page errors**，包含实际CCB打开→新Job完成→终端、重复打开epoch不变、原配置页和390pxmodal。它不抹除03的503。
- `q9-browser-acceptance-05`：再次重启BFF加载最终service `a6ae5de244df2099ad91cf7abd52d48aa884bb2485663b924e3f3f6195d43ebe`，同协议 **7/7通过、0 page errors**。未通过反复尝试覆盖03；04/05是代码版本变更后的独立记录。

上述 Q9 screenshots（dialog、无效路径保留、真实新项目、原配置页、窄屏dialog）已由主审查看。只进入原worktree设置，不在浏览器验收中保存/激活worktree，不宣称本次新建工作树的整套视觉操作已走通；服务端身份/managed worktree/外部合法目录/别名/伪造反例另有Python tests。

## 4. 独立对抗审查

独立反例先红后绿，不把正常 happy-path 或 correlated early rejection 当全机制有效：

1. 选择 ABA（关闭慢打开窗口→选择coder→选择回buddy）仍被迟到结果抢走：增加轻量 selectionRevision，保留成功项目但不抢后来选择。
2. 旧 discovery 迟到把已ready项目覆盖回404：短锁提交 generation，不把启动、discovery、RPC放进锁。
3. scope不明拒绝，不静默fallback项目根；完整目录同名仅在碰撞时显示全路径。

脚本/源码SHA、独立复核及未测性质见[首次独立审查](muxary-expansion-adversarial-review.md)、[Q9独立审查](muxary-q9-adversarial-review.md)。后续 fresh-read 窗口不能由第2项green推导已解决；它另有两分支red→green，且确认发布只合并目标以保留无关新项目。其后preflight又暴露“own old candidate不含目标、current已ready仍调用starter”反例，先红后修：pre-start优先current确认，再查own candidate，独立脚本由starter_calls=1变为0。post-start仍基于自己的完成candidate确认，二者不可混用。最终176项及独立复核见后端报告。

## 5. 性能与消融证据

### 画布

原先协议固定：1/20/100 UI Agents × ordinary/fit-all × culling off/on；每cell2次warmup、5次formal，全部保留。每rep p95 rAF gap≤32ms、选择≤100ms、交互无>200ms长任务；只对该固定headless VM/fixture/手势窗口判断。100摘要节点不是100个真实CLI、100条日志流或100个WS。1节点的20次选择是同目标no-op激活，不是20次目标切换；20/100节点按冻结顺序覆盖不同目标。

选择时延是click捕获→目标breadcrumb/sidebar及已挂载node状态正确→下一rAF绘制机会，不是CWV INP或物理屏幕像素延迟；rAF gap也不是GPU paint FPS。冷启耗时与longtask单列，不混入稳定交互通过数；中文草稿使用fill，不代替实际OS输入法。fit-all按全部模型bounds在视口内检查，不以全DOM挂载或culling-off作完整性oracle。

- release1 preflight：5个预检中1节点完成，4个100节点均在stable计时窗口前失败。真实侧栏布局把1440×1000视口内的`.react-flow`高度从642px撑到3773.5px，fit-all内容中心落在可见屏幕外；两种culling均复现。修grid minmax(0,1fr)/min-height:0后另建release2，不把这些预检算作正式性能样本、不删除失败。
- release2：84次完整记录（24warm+60formal），12个cell各5次正式rep均达预定交互与正确性门槛。普通100项culling使起始DOM3461→1221、挂载卡100→20，却使选择p95约28.1–28.5→44.6–45.1ms，未观察到可稳健外推的heap下降；fit-all两组在轨迹中均100卡全可见、起始DOM3461，没有裁剪收益。**因此保持生产默认关闭culling**，不是测后才首次设为false，也不因“减少DOM”就强启额外机制。该中间源码快照已被后续修复及Q9扩展替代，不能认证最终生产源码；5对rep仅作描述比较，不作显著性或无限规模承诺。
- release2同机活动：root独立Chrome、npm test/build、后端全量测试并行；另有本代理一次约10–15秒Python bundle比对CPU活动，约1节点fit-all的22–25号样本可能重叠。事件、所有热身/正式结果均保留，不据此删样本、调门槛或补跑。heap未强制GC，不宣称无泄漏。
- release3：用户Q9改变范围后外部中止。保留66条raw：6次完整（4warm+2formal）、60条中断/随后browser-closed失败记录；余18项未启动，冻结schedule仍保留。不与release2/4拼接，不当最终通过证据。中止后71项冻结输入hash均未变化，自有runner、Chrome与静态服务精确关闭。
- release4最终构建补测：结果待其独立冻结记录，不从旧版继承。

本机材料位于`~/.local/share/muxary-dev/expansion-review/canvas-performance/`：`protocol-1.md`的SHA256为`f136a22e20d1c63fea2df7cc6943a259b7b6b54a7138b39d1a55bb18bc29cc59`；`results-2/{report.md,index.json,summary.json}`含全部逐rep p50/p95/p99/max，`freeze-2.json`及`release-2/{source-manifest.json,build-manifest.json}`固定源码、lock、构建、fixture和脚本身份。`freeze-2.json`的`formalSamples:84`是保留未改的元数据标签错误，冻结schedule实际是84总/60正式/24热身。`preflight-1/FINDING.md`与`results-3/{ABORTED.md,abort-summary.json,external-closure-after-abort.json}`记录负面结果与中止；不覆盖旧冻结文件或已有结果。

### 重内容与终端

[内容/终端报告](muxary-content-flow-validation.md)对应其冻结旧build，不冒充Q9新build重跑。1/10MiB×按需/展开纯文本对照，4warm+20formal，原始26条结果13P/13F。10MiB固定180ms刷新oracle全部失败；后验等更久仅确认完整SHA，不补采性能掩盖失败。展开10MiB冷长任务约1382–1404ms、heap约55.75–55.93MiB；按需默认相应约63–74ms、15.50–15.69MiB，输入p95也更低；据此保留按需纯文本，而非提前挂巨大Markdown。没有实现消息列表虚拟化。

真实xterm 5000编号行流测中，截图末尾004987不证明5000行全消费；原3×1MiB突发未达假设积压，原样失败。后验4×1MiB验证可见断开、不自动重连/不重放输入，但有**562ms长任务**，不满足200ms目标。2MiB pending预算只防无界积压，不保证极端流无卡顿。

## 6. 仍保留的边界

- 摘要画布最多100个Agent，更多仍可左栏访问；浏览器布局最多20个项目，读取上限256×1024 UTF-16 code units（不是UTF-8字节）。不是无限CLI/无限内存保证。
- project-start unknown 防重为单服务实例canonical-root内存集合，不跨整个后端重启持久化；不能把Job SQLite receipt泛化到项目启动。
- stdout/stderr临时文件避免descendant持有PIPE拖死timeout，显示读有上限，但临时文件磁盘大小未设上限。
- 目录绑定不是文件访问沙箱或永久cwd；共享目录无写锁。Git禁用ext-diff/textconv仍可能触发仓库filter.clean（已复现）；未单测filter.process，不能称无插件副作用。
- synthetic composition不是实际各OS中文输入法验收；没有完整屏幕阅读器、全部浏览器、Windows/macOS、npm/二进制/签名移动端发布验收。源码安装复用既有官方helper ELF，不冒称全新Rust release构建。
- 不能宣称所有测试通过、10MiB显式展开/极端终端无长任务、100个真实CLI负载通过或跨平台“完美适配”。

## 7. 本机入口、提交与清理

原本已完成可逆入口切换，`~/.local/bin/{muxary,ccb,ask,autonew,ctx-transfer,codex-reconnect}` 指向源码安装；官方npm8.7.22、原HOME配置/Agent仍保留，未重启或派活。备份路径、回滚及source/venv依赖见[安装文档](../muxary-install.md)。最终fresh login shell复核 `muxary --no-open`：静态200、未认证API401、HttpOnly/SameSite Strict、bootstrap重用401；只读发现原HOME两Agent，没有派活，原配置SHA前后相同，SIGINT服务退出0（`installed-smoke-q9.json`）。最终远端提交结果按实际完成后补录，不预写成功。

清理只允许逐项识别的本任务浏览器、服务和临时项目；保留全部原始失败/成功日志、SHA清单、截图、源码、可复用依赖、当前运行所需Web资产、备份和用户数据。后端代理已清理18个专属测试运行时及7个basetemp，收据见其报告；不广泛删除/tmp或既有缓存。
