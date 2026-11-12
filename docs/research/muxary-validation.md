# Muxary 0.1.0 本机验收记录

日期：2026-11-11；Linux x86_64；源码里程碑，**不是已发布的跨平台 release**。
上游固定基线：`df98e61e91b4be57873029b01667135e6265f371`（CCB 8.7.22）。
工作区：`~/Muxary`，`feat/muxary-workbench`，未提交/推送。

## 证据原则

- receipt/HTTP 202 不是完成；实际 ccbd terminal decision、原生 JSONL 精确匹配才是相应完成证据。
- 合成事件、CLI stub、真实模型、浏览器和发布构建分层报告。测试数量不跨有重叠的集合相加。
- 历史失败日志保留；后续配置修正或修复另存日志，不覆盖、删除不利结果。
- 本机原始日志保存在 `~/.local/share/muxary-dev/review/`；截图在相邻 `visual/`。含一次性 token 或原生账号的私有材料不进入仓库。

## 1. 设计选型不是模拟协作

通过真实 `codebuddy-code -p --model ...` 分别调用 `deepseek-v4.1-flash` 与 `claude-opus-5.5`，共四轮、八次调用；禁用工具/MCP、限定轮数、不持久化会话。模型返回、耗时、session 和原始文件 SHA 见[模型讨论](muxary-model-design-review.md)。

候选全部来自 21st 官方 AgentChat 文档。第三轮提出 Empty centered + suggestions 与固定输入位置冲突，主审接受反例，最终选择 **AgentChat Basic**，第四轮两模型明确同意。不是事后把已有自绘 UI 挂上原型名称。模型没有看最终截图或替代执行测试。

固定 `21st-dev/agent-elements@b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37`；12 个去重源码/CSS 文件保留 MIT 声明，3 个必要修改、9 个字节不变。离线完整性 gate `test_muxary_ui_provenance.py`：**13 passed**，核本地文件/许可 SHA 与修改清单，不把本地清单当作独立上游真实性证明。[来源与实际单因素消融](muxary-ui-source.md)。

## 2. 前端与真实控制面

最终 `npm --prefix web test`：**25 passed，3 files**；`npm --prefix web run build` 成功，包含 TypeScript 检查。最后在 manifest/lock 删除可选 Shiki 依赖后执行干净 `npm ci --ignore-scripts` 再构建，未依赖残留 node_modules 制造通过。大 chunk 与第三方 `use client` 构建提示仍保留；没有运行时性能或首屏速度保证。

| 路径 | 实际证据 | 边界 |
| --- | --- | --- |
| 输入与提交 | React mount 覆盖 Enter/Shift+Enter/composition、拒绝保留草稿、accepted 后读取失败不变 unknown、存储故障释放发送锁 | 未做操作系统 IME 人工验收 |
| 幂等与失败 | 重复点击锁、稳定重试键、网络 unknown 不自动重发；BFF 持久化 request fingerprint/receipt，重启仍 unknown | 不保证网络中断后能够推断远端未提交 |
| Agent 切换 | 两个独立 stub Agent，经真实 ccbd/tmux/HTTP 完成；点击任务卡只切目标，POST 计数不增加；随后发送归属正确 | stub 不是模型联通证据 |
| 来源与顺序 | 任务按 created_at 升序，右栏倒序；原生会话独立 tab，不按文本猜去重；GET 携带 namespace_epoch | 原生来源不等于永久完整 CCB job 档案 |
| 原生读取失败 | 回归覆盖错误可见；浏览器发现漏 epoch 的 409，补参数后实际返回原生记录 | 不再吞掉错误伪装空历史 |
| 任务权威 | 独立真实控制面 exercise 包含 submit/cancel/retry 与完成竞态；完成由 ccbd 判定 | 没有第二调度器或统一审批 API |
| 终端接管 | 原 gateway handle → WebSocket → 原 pane；实际输入 seq 1—21，收到 open/output；手动重连取得新 handle/历史 | 此次未观察到 gateway ack，不能说已收 ack；固定源栅格不 resize 共享 pane |
| Git diff | 浏览器真实 tracked/unstaged README 变更；服务禁 extdiff/textconv，限输出/时间，显式 truncated | 不含 staged/untracked 文件，不是完整 IDE |

最终 BFF service / lifecycle / Muxary CLI / 原 mobile gateway 定向集合：**202 passed，34.48s**，`final-workbench-regression.log`。此前集合有重叠，不另相加。

对抗复核还发现：仅依赖禁用按钮不足以保护回调，记忆的 Agent 在新项目 view 尚未返回时仍可被合成 Enter 触发提交。新增回归先 **1 RED /24 passed**，最小修复让 submit 和 UI 共用“当前 view 含目标 Agent 且已观察到 namespace epoch”条件，最终 **25 passed**；保持原 CCB 后端归属校验不变。

## 3. 独立无登录 Chrome

使用专用 `agent-browser --session muxary-audit`、独立 Chrome 148，不使用用户浏览器登录态。最终截图：

- `14-muxary-final-desktop.png`：1440px 浅色桌面，任务与原生来源可切换。
- `15-muxary-native-source.png`：原生来源合成 Markdown 探针，非模型/job 回答。
- `16-muxary-final-mobile.png`：390px 窄屏。
- `08-muxary-dark-diff-confirmed.png`：深色、真实 diff；拍摄于来源 tabs 改动之前，不冒充最后一版全部像素。

实际 DOM/交互：390/768/1440px 无横向溢出；Help 对话框焦点进入/循环/Escape/归还；Ctrl+K 搜索；reload 不产生新提交；真实终端双向输入/输出。关闭右侧上下文（终端保持关闭），其他因素不变，仍可派活完成并阅读结果，证明核心闭环不依赖隐藏面板。

Markdown 使用明确标记的**合成 Codex 原生日志**与最小线程索引，仅在专用 fixture 的私有 provider HOME 内；真实 jobs.jsonl SHA 不变。表格、代码 fence 正常显示；javascript 链接没有可导航 href，script/onerror 没有执行。该探针不等于全 XSS/WCAG 审计；未测屏幕阅读器、完整对比度或真实系统 IME。详细[视觉验收](muxary-visual-audit.md)。

## 4. CodeBuddy 真实 CLI / 模型

CodeBuddy **2.183.0** / `claude-opus-5.5`，两个独立临时项目，`ccb --safe` / native `permission-mode default`。ask、原生 clear、独立证据确认 compact、精确 UUID resume 后的新 ask 均得到 **EXACT completed**；四个成功 job 与原生匹配证据见[实测记录](codebuddy-live-validation.md)。

保留一次 trust 未完成时的 `incomplete/project_shutdown`，不算通过；五个继承 MCP 启动失败，不宣称插件/MCP 全兼容。账号只单向复制当前 Linux auth 文件/注销 marker 到私有 HOME，0600，不回写源。关闭 inherit_auth/config 停止外部继承，不撤销已经存在的私有副本，不等于 logout。macOS/Windows 原生账号存储、企业定制产品、并发刷新竞争未测。

对抗审查新增的真实反例：

1. user anchor 缺少/数字/空字符串 conversationRequestId 会被后续无关 generation 错误满足：先得到 reader/execution **6 RED**，修后与合法/错误 generation 正路对照通过；reader/execution/hooks 完整集合 **115 passed**。
2. 无效 hooks schema 在拒绝 relaunch 前写入新 launch generation，破坏旧绑定：单因素反例先红后绿，拒绝后旧 identity/sidecar/settings/prepared 字节不变。AgentSpec 在构造时已拒绝的错误模板未冒充 launcher 新缺陷证据。
3. settings.env 可被原生 EnvInterceptor 写回 process.env，覆盖私有 HOME/config：部署前增加受管隔离键冲突拒绝；按真实启用的 user/project/local/CLI 来源检查，普通 API/model/env 保留。已启用磁盘来源暂只支持严格 JSON，JSONC 注释/尾逗号明确拒绝且文件不变；不静默当空配置。启动后同用户编辑导致的动态 reload/TOCTOU 不在持续隔离保证内。最终 launcher 集合 **183 passed**，CodeBuddy 全部 / storage / catalog / mux backend 集合 **452 passed**；两集合有重叠，不相加。真实模型实测早于最后的 launcher 预检加固，未声称在相同冻结版本重新调用了真实模型。

原生日志 writer 的保证是 **append-only**。reader 能识别 inode 变化或观察到 size 小于 offset；不能检测两次 poll 间同 inode 截断后又增长到旧 offset 以上的任意重写。没有为未观察到的正常 native 行为增加全文件 hash 层。no_wrap/headless/运行中 job 自动恢复不支持；native resume 不等于 job 无重复续跑。

## 5. 全量回归与环境对照

首轮 `pytest test -q --maxfail=20`：**20 failed，6107 passed，52 skipped**。保留 `full-suite.log`。其中 provider count/installer fixtures 对新增入口的要求作窄修复，未删除断言或放宽 gate；另有当前系统无 `python` 与系统 `python3` 缺依赖导致的 subprocess 环境失败。

独立官方未改基线取同一 124 tests：原 PATH **11 failed /113 passed**，仅前置已有兼容 venv/bin 后 **124 passed**。没有改官方源码或测试阈值。故最终完整运行显式使用既有 venv 与 PATH，而不是排除这些测试：

```bash
PATH="$HOME/claude_codex_bridge/.venv/bin:$PATH" \
CCB_PYTHON="$HOME/claude_codex_bridge/.venv/bin/python" \
CCB_PYTHON_BIN="$HOME/claude_codex_bridge/.venv/bin/python" \
"$HOME/claude_codex_bridge/.venv/bin/python" -m pytest test -q
```

完整运行结果为 **11 failed，8374 passed，82 skipped，2050.32s**，保留 `full-suite-configured.log`，不是单次全绿。全部 11 个失败的归因、单因素对照和后续复跑如下：

| 失败数 | 原因 | 最小修复 / 前置补齐 | 独立复跑 |
| --- | --- | --- | --- |
| 2 | installer reuse 用例受全局 `CCB_PYTHON_BIN` 强制指定解释器影响 | 官方未改测试同条件也失败；仅这两例 unset 该变量，保持生产实现及断言 | 安装窄集 **50 passed**；变量 set/unset 两组各 2 passed |
| 4 | 可选 `ccb-runtime-accelerator` ELF 缺失，start matrix 等不到 owner | 官方基线无 ELF 同 4 failed；比对 workspace/lock/crate 共 5 个文件逐字一致，补齐官方 8.7.22 ELF，不改 gate | 原 start matrix **6 passed，33.71s** |
| 1 | defaults 顺序把新增 CodeBuddy 放在 Gemini 之前 | CodeBuddy 移至 Gemini 后，原 provider 相对顺序和值不变 | 包含下列 registry/runtime 的 **9 模块 591 passed** |
| 3 | execution 可选集合及两个 core registry 精确集合遗漏新增 provider | 增加精确 CodeBuddy 条目、session/mode 与 core-only 不含 CodeBuddy 的断言，不放宽集合判断 | 同上 **591 passed，25.82s** |
| 1 | Gemini stale actor 用例回退到真实 HOME，既有 `~/.cache` 是 symlink | 生产路径 gate 正确拒绝；仅该例注入临时真实 `XDG_CACHE_HOME`，原断言不变 | 单因素对照通过，包含于上述 591 passed |

最后统一受影响回归覆盖 48 个模块（全部改动/新增测试，加原 gateway、config loader、start matrix；清单 `final-affected-regression-files.json`）。首轮 **2 failed，1503 passed，252.85s**，原日志 `final-affected-regression.log` 保留。两个失败均为原 terminal 测试在创建 tmux 时使用 112/117 字节 UNIX socket 路径，受当前 login shell 的长 `TMPDIR=~/.local/tmp` 影响；真实 tmux stderr 为 `File name too long`。独立 AF_UNIX 单因素 probe：107 字节成功，108/112/117 字节拒绝。仅将 `TMPDIR=/tmp`、其他条件和断言不变，两例 **2 passed，13.65s**（`gateway-socket-path-ablation.log`）；不改生产路径 gate 或弱化测试。

相同 48 模块在该单变量配置下再次完整复跑：**1505 passed，257.08s**，见 `final-affected-regression-short-tmp.log`。并行审查后的 reader/launcher 新增回归也在此集合，不将较早收集的全套当作最后全部文件的冻结验证。

## 6. 安装、分发与当前本机状态

官方 npm CCB 已更新至 **8.7.22**。Muxary 已在 `~/.local/share/muxary/bin` 独立源码安装；最终 1505 项 gate 通过后，已将 `~/.local/bin/{muxary,ccb,ask,autonew,ctx-transfer,codex-reconnect}` 六入口切换到该安装，官方 npm 安装完整保留。fresh login shell 的六入口解析、Muxary 0.1.0 / `ccb --print-version` / `muxary tui --print-version` / `ask --help` 均成功。已安装源码入口实际启动，静态页/认证项目接口 200、未认证/重用 bootstrap 401、按端口 HttpOnly/SameSite cookie；只读原 HOME 项目得到 2 个 idle Agent，配置 SHA 与备份一致，0 次派活。registry 中并行测试的不可用条目 503 如实保留，不声称所有条目在线（`installed-web-smoke.json`）。当前官方 npm 8.7.22 与原配置已额外备份到 `~/.local/share/ccb-backups/20261111-muxary-cutover`，0700 外层目录，未覆盖官方安装。切换后再次通过新 login shell（unset ambient Python overrides）启动默认 Web：静态/认证项目与原 HOME view 200、未认证和 bootstrap 重用 401，registry 仅原 HOME 1 个项目、2 个 Agent、0 次派活、原配置 SHA 不变；Ctrl+C 正常关闭 exit 0、stderr 为空（`final-default-web-smoke.json`）。原有 Agent 未重启，已在运行的 daemon 不会因入口切换热换代码；项目之后按原 CCB 正常重启才加载新增后端。

本机无 Rust；三个 helper（`ccb-rs-helper`、`ccb-agent-sidebar`、`ccb-runtime-accelerator`）复用官方 8.7.22 Linux 已安装 ELF，对应源码未修改，非新 Rust 构建。accelerator 的 SHA-256 为 `1d8b2973a8ea7f491fdd90a9ed65ecce5ec377f35b6eeb6b9771f736d3f01c63`；源码对应关系见本机 `controls-accelerator-provenance.json`。`install-cli` 只自动构建 sidebar/rs-helper，可选 accelerator 在干净 checkout 中需另外运行 `bin/build-ccb-runtime-accelerator`；本机复用 ELF 不是通用安装前置自动齐备的保证。release 导出测试验证固定 git-ref 内构建前端、缺资产 fail-closed、失败不继续 Cargo，但 npm/Cargo 是测试替身；**未运行真正 Muxary release 构建或发布**。npm scope、Windows binary、移动 APK 未发布/未验收；自动发布 workflow 已改为手动 opt-in，updater 只查 fork，不降回上游。

安装后 Web 默认复用现有 CCB registry；冷项目走原 `ccb --safe`。BFF 只 loopback、同源 cookie/Host/Origin，非团队或公网认证；同一 OS 用户的恶意进程不在该边界内。原生工具权限/审批仍归原 CLI，CCB 兼容 `auto` 模式保留，需原生确认时用 `--safe`。


## 7. 收尾与保留材料

仅停止本次 audit/source/installed-source Web 服务、独立 Chrome 和 browser fixture，撤销或删除其一次性 token。fixture 的 9 个专属进程、45901 监听均已消失；`ccb kill -f` 返回 unmounted。原 HOME 两个 Agent 前后均为 idle/restored，未强重启或派活。此前全量失败遗留的 pytest-79：19 个项目按精确 cwd 清理，进程和原 18 个 tmux socket 残留均为 0；不触碰其他正在运行的 pytest。

删除只含 3 个本任务配置/identity 文件的 `audit-project` 与已消费的 installed Web token 日志；保留最终截图、原失败日志、模型回复（本机 review 0700、原始回复 0600）、可复现 synthetic fixture、源码、node_modules、运行必需 Web 资产、官方 helper ELF 与切换备份。不将这些本机材料提交到仓库。详见 `final-browser-fixture-cleanup.json`、`root-service-cleanup.json`、`root-ephemeral-cleanup.json` 和 `controls-full-pytest79-cleanup-result.json`。

最后按逐项清单删除本任务 checkout 内的 **275 个** `__pycache__` / `.pytest_cache` / Vite 缓存目录，不删除 node_modules 依赖或运行资产。最终两次综合回归 basetemp 的专属进程残留为 **0**；本机清单与结果为 `workspace-cache-cleanup-{inventory,result}.json` / `final-cleanup-status.json`。118 个改动/新增交付文件的最终 SHA 保存在本机 `final-source-manifest.json`，源码仍未提交或推送。
