# Muxary：紧凑工作台 UI、交互与独立历史验证

- 日期：2026-11-12。
- 源码基线：`0cd8bfea2e9e28b8cf5f373809329bcb3e100473`；CCB 来源仍为 `df98e61e91b4be57873029b01667135e6265f371` / 8.7.22。
- 状态：**运行验证完成：112 项前端、269 项关联 Python、13 组浏览器及默认画布 15 次正式性能复验通过；独立历史交付另记于第 6 节**。通过只适用于下列固定范围，不是零缺陷或全平台声明。
- 私有证据：`~/.local/share/muxary-dev/ui-refinement-20261112/`。原基线、各失败 attempt、模型原始答复和旧扩展证据均保留，不覆盖重写。
- 关联：[SPEC](../specs/muxary-workbench.md)、[设计与两模型交叉评审](muxary-t3-multica-design-review.md)、[ADR-0003](../adr/0003-workspace-and-canvas-presentation-boundary.md)、[独立历史 ADR-0004](../adr/0004-independent-muxary-history-and-attribution.md)。

## 1. 实际改动与未改变的边界

紧凑顶栏集成专注/画布、高频变更、终端和上下文；次行保留目录身份与明确的来源切换。移除重复大标题。完整路径仍可展开核对，不只依赖 hover；不会写配置、热换 cwd 或重启 Agent。Composer 用已有 InputBar `leftActions` 显示实际 Agent/Provider 与“CCB 任务”，不虚构模型切换器；原生来源视图明确发送仍是 CCB Job。

右侧任务动态增加只读全部/进行中筛选；默认全部保留失败记录。搜索无结果可恢复而不改变执行目标。空态、首次连接与未选 Agent 文案分开。手机保留同一工作台、互斥抽屉与现有 Command/dialog，不增加导航层或依赖。

阅读跟随从原 App 分散状态/`scrollIntoView` 改为一个 hook，观察会话 viewport 与 content，尺寸增长合并到一帧；主动向上阅读取消待执行跟随。终端伸缩不再等到下一条消息才校正贴底。没有新队列、第二终端、消息虚拟化、worktree 管理器或轮询系统。

继续复用固定来源的 Agent Elements、shadcn Command/Resizable 和原 React Flow/xterm。T3/Multica 只作为官方图和源码研究，未 vendor 其代码、CSS、品牌或图片；尤其没有把 Multica 的额外许可条件当作普通 Apache2。两模型只收到文字事实与画面观察转述，不宣称模型已看图、操作产品或测过性能。

## 2. 当前冻结的运行身份

最终候选 `final-candidate-03` 来自 `frontend-build-04`；源码/运行资产相同关系由逐文件 manifest 核对。文档后续补记不改变运行资产。

| 文件 / 集合 | SHA-256 |
|---|---|
| `web/src/App.tsx` | `2b15fc5888e4ecce39966936bd141748b02cdebc0fbcd28b52045b01243151b8` |
| `web/src/style.css` | `7cd9b49158df0025bb2d2223377e9648e1476dc07de4ac2811f683d19dcdaddc` |
| `web/src/useConversationScroll.ts` | `86705b2853b873fffd46ec13799c6cc081617f8320403a1e124da10a5146aa64` |
| `web/src/App.test.tsx` | `fc2a06ac0aab3bebc6ceb69c2e1521e1f25b6032b6b0949afd66aafa32b03655` |
| `web/src/useConversationScroll.test.tsx` | `19f718d5bc6fa548f039cd80f21efcbc10e6dfe42ffe457fe8c11625e28d991e` |
| 14 个运行资产集合（按本轮性能 manifest 的集合算法） | `8d3bd54a1b8c5815daf1c576eb7bbcb70361891441e6fe9d0af4ecc800273ef9` |

## 3. 实际执行的分层验证

| 层级 | 最终结果 | 证据与边界 |
|---|---|---|
| 前端全部 Vitest | **112/112，通过，7 文件，9.88s** | `frontend-tests-03.log`；JSDOM/接口替代，不能证明浏览器绘制或真实 Provider |
| 类型检查与 Vite | **通过** | `frontend-build-04.log`；保留依赖的 `use client` 打包提示，不是跨平台产物发布 |
| 滚动 hook | **20/20 通过**，已包含于前端总数 | 原等价行为 3F/1P；新增内容/viewport 几何模型、合帧、用户输入、StrictMode cleanup；真实几何需浏览器另证 |
| 后端/命令/发行关联回归 | **269P / 2S，67.61s** | `backend-regression-02.log`；14 个指定文件，非全仓 8000+ 用例重跑 |
| 安装入口 | **通过** | `installed-entrypoints.log`；登录 shell 下 `muxary --version`、两命令 help 与 symlink 指向当前源码安装；未重启用户 Agent |
| 独立浏览器完整流程 | **13/13 组通过；0 pageerror、2 consoleerror 保留** | `final-candidate-03/acceptance-02/result.json`；真实 BFF/CCB 与私有 CLI stub，不等于真实模型负载或平台全兼容 |
| 新构建默认画布窄性能 | **15/15 正式通过，另有 6/6 warmup** | `canvas-default-regression/results/`；原门槛、普通视口、culling off，不覆盖 fit-all、极端长输出与真实百 CLI |

Python 范围为 `test_muxary_{cli,distribution,release_web,ui_provenance,canvas_ui_provenance}`、`test_workbench_{service,lifecycle,project_open,workspaces,yazi_open}`、`test_cli_tools_workbench`、`test_install_{source_dev_mode,release_entrypoints}`、`test_release_visible_versions`。两个 skip 都来自 `test_workbench_yazi_open.py:93` 的原生 Yazi/tmux 参数例（rich=False/True）；`backend-skip-audit.log` 为 10P/2S，Wayland XCursor 用例实际通过。没有把跳过记为通过。

## 4. 不利结果与修正留存

- 四项 UI 行为先红 4F，再绿 4P。首个全前端为 109P/1F：新 composer 曾丢失明确“发送给 coder”文字。恢复可见目标标签后 110P，没有删掉旧断言。两个连接/无 Agent 状态先红 2F、再绿 2P，最终总数 112P。
- 独立对抗审查发现 CSS 清理脚本遗留无 selector 规则、展开箭头 selector 与 JSX class 位置不匹配。源码修复后 PostCSS 327 个 rule / 0 空 selector；候选 01 的原资产仍保留，未执行浏览器认证，不冒充通过构建。
- 首次关联 Python 为 268P/2S/1F，真实 CCB 启动得到 unconfirmed。该轮没有给子进程显式导出 `CCB_PYTHON`/venv PATH；保留原失败。补齐运行环境后同一用例单独 1P、同范围全量 269P/2S。没有修改后端或放宽启动 gate；不据一次环境重跑断言已穷尽所有启动问题。
- 浏览器早期 attempt 保留：旧平移坐标命中缩放按钮而非画布空白、一次性 bootstrap token 的二次使用、teardown 期间读取旧 readiness receipt、任务 tab 名称空格不匹配。纠正命中点/生命周期/locator，不取消 transform、身份、mutation 或正文断言。
- 原 Codex 私有 stub 只写 JSONL，没有真实 reader 所需 `state_5.sqlite` 的 `threads` 索引。单因素 spike 保持 JSONL SHA 不变，仅补该真实索引，原生读取从 0 到 1 条并出现原回复。只修本轮私有 fixture，不改生产 reader、不切 Provider 绕过正文 gate；原失败与 spike 保留。

## 5. 审图与范围限制

主审已实际查看官方参考四图、冻结基线 desktop/mobile、候选 02 首屏及最终候选的变更、任务/原生正文、手机抽屉与画布列表、浅深色界面。浏览器审查代理看完全部 20 张最终图。静态图只能支持可见布局观察，不等于真实参考产品动态操作、完整无障碍或人类任务完成率对照。

相同初始空会话的真实 DOM 几何（不是估算截图坐标）：

| 视口 | 会话顶部：旧 → 新 | 会话高度：旧 → 新 |
|---|---|---|
| desktop 1440×1000 | 222 → 103 px | 538 → 695.5 px（+29.28%） |
| mobile 390×844 | 199 → 100 px | 411.5 → 555.109375 px（+34.90%） |

桌面初始顶栏 54px、次行 49px；手机次行 46px。此值只适用于采集视口/字体/内容，不外推所有环境。`10-opened-project-completed.png` 实为重复 open 后 Agent 重读过渡帧，不能因文件名当作完成态 oracle；实际任务完成由 Job gate 与后续正文截图分别证明。

真实滚动屏障测试：跟随任务完成保持底部 gap=0；主动阅读时内容高度从 2763 增至 2795px，scrollTop 均为 1167px。无新消息时终端挂载/键盘/鼠标伸缩，会话高度 696 → 399 → 307 → 270px，各步 gap=0；手动阅读伸缩前后 scrollTop 均为 1825px。精确原值在浏览器结果中，JSDOM 几何不冒充浏览器证据。

默认画布复验预先固定 1/20/100 摘要节点、普通视口、culling off，每 cell 2 warmup + 5 正式，无剔除/补采。最坏正式 rAF p95 均为 16.8ms（门槛 32ms），选择 p95 分别 30.7/29.1/27.6ms（门槛 100ms），稳定阶段 longtask 为 0（门槛 200ms）。全部 21 次原始结果与 42 张图保留。共享宿主活动（包括可能重叠的 1.47s skip 审计）保留，不是隔离硬件 benchmark；不据此声称 CWV/INP、内存无泄漏、速度优于旧版或真实百 CLI 吞吐。

浏览器不是零 console：负测非法项目路径的 HTTP400 为预期一条；切 Agent 脱离终端另观测 `Data frame received after close`。唯一 terminal 句柄的 `closed_reason=client_closed` 落在该切换区间，关闭后无新增 output、无自动重连/新 attach，页面无未捕获异常。未采 WS 帧/console 时间戳，不能证明精确线上顺序或所有 worker 瞬停。原 `Terminal.tsx` 与 gateway websocket/core 均未改；静态存在关闭握手继续写 data 的边界，保留为后续单独修复项，不隐藏、不声称已解决。旧浏览器证据未采 console，也不能用旧日志无此字符串证明此前不存在。

最终 desktop 深色原图抓在 150ms CSS transition 中间，body 已变暗而部分按钮/气泡仍在插值；不能拿它当稳定颜色证据。另做只读补充 `stable-dark-supplement-02`：等待 500ms、fonts.ready 与双 rAF 后，按钮/气泡从浅色 `rgb(237,242,253)` / `rgb(241,244,248)` 变为预期深色 `rgb(37,47,69)` / `rgb(40,47,59)`；主审实看新增 desktop/mobile 两图。0 POST、0 pageerror、0 consoleerror 仅适用于该补充只读会话，不能覆盖完整流程中的两条 console 反例。补充首次 locator 误用旧 class 超时也保留，不改源码、不覆盖旧图、不冒充完成 WCAG 对比度审计。

既有 CCB 8.7.22 全仓负结果和实验 culling on 的失败仍属于各自原快照，未删除、未放宽、也未当作新构建实测。此次不承诺 canvas 重挂恢复阅读的精确 offset；只保留暂停跟随的意图。未做真实触屏硬件、OS 输入法候选窗口、屏幕阅读器或 Linux 以外平台验收；合成 composition 测试不能替代它们。

## 6. 独立历史与交付

用户明确确认后，已准备本机完整旧历史 bundle（验证完整），旧远端 `main` 的可达提交计数为 2027（含 tip）。仅本仓库 Git 身份已切换 `Atingaii` 与核验账号 ID 对应的 GitHub 隐私邮箱。重建/远端 lease 推送结果待最终 UI 验证完成后填写；不提前宣称远端历史已替换。

## 7. 清理

参考研究的两份一次性公开 clone 已按 remote/path 核对后删除；固定所选原图/源码证据、所有失败记录、运行资产、可复用依赖、旧历史 bundle 与已有安装备份保留。浏览器 fixture/本轮后台进程的最终清理结果待结束后填写，不触碰原用户项目与 Agent。
