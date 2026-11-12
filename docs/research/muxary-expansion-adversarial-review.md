# Muxary 扩展：独立前端对抗评审

- 日期：2026-11-11，最终复核 18:26:54（Asia/Beijing）。
- 状态：**本文列出的已复现前端反例已修复并复核；不据此宣称浏览器、真实 CLI、后端权限或性能验收完成。**
- 关联：[扩展 SPEC](../specs/muxary-workspace-canvas.md)、[产品评审与来源](muxary-expansion-product-review.md)、[ADR-0003](../adr/0003-workspace-and-canvas-presentation-boundary.md)。
- 分工：独立子代理只读审查实现，主审修复源码及补测试；本次唯一仓库写入是本报告。没有修改旧模型输出、截图或冻结验收记录。

## 1. 范围与判定方法

本次审查 `web/src/App.tsx`、`polling.ts`、`MessageContent.tsx`、`Terminal.tsx` 及对应测试；画布内部行为/性能与服务端 workspace/diff 权限由其他评审负责，不能从本文继承通过。

分别检查：

1. **实现边界**：请求所有权、取消、异步回执、过期结果、终端生命周期；不以代码风格替代正确性反例。
2. **SPEC**：唯一 project/Agent 选择、unknown 不重发、默认专注/可切画布、来源按需读取、hidden 暂停、原文可访问、移动抽屉与 IME/浮层。

除源码阅读外，用 `node --input-type=module` 从 stdin 启动 Vite `ssrLoadModule`、jsdom 与 Testing Library，加载当时真实组件代码；网络由可控 deferred `Response` 替代，分别制造乱序、慢响应、错误、忽略 abort 的延迟结算以及遵守 AbortSignal 的取消。Terminal/Canvas 在 App 级反例中替代为轻量组件，Terminal 记录 effect 的 `{project, agent, epoch}`；**这不是实际 WebSocket、xterm 或 CLI 联通测试**。每个场景只改变需要隔离的因素。

stdin harness 未保存为新工具或页面副本，观察输出留在本次执行记录；可持久重跑的对应回归已由主审加入下述测试文件。没有因发现新反例而删样本、放宽 gate 或改写先前失败。

## 2. 修前来源指纹

评审发生在并行开发期间；SHA-256 区分当时的代码，不把后来的修复倒填到早期反例。

| 代号 | 文件 / 阶段 | SHA-256 |
| --- | --- | --- |
| A0 | `App.tsx`，初次 diff/IME 审查 | `4b99294cbd346cd633cfa458cc61994ce21245af5dfa04648acea010bb5d4761` |
| A1 | `App.tsx`，首次修复后的并发/终端反例 | `dbb8b65456f25f2551a1ffee82a6723a6f399d7b79a371206ac951e16d2547f1` |
| A2 | `App.tsx`，仅 project 级单 ref 去重及 explicit terminal identity | `d74dbe76f04331f50483e496268b5a56524ca3fa7839603d1a165dbfe94aca33` |
| M0 | `MessageContent.tsx`，展开状态仍在父组件 | `6f46c8d2eb22fa511427f30819fda69f0da55b76d75c1ce201ec3698a30ee615` |

## 3. 反例、修复与复核

下表的“复现”指内存组件/受控网络场景，不指真实浏览器截图或性能结果。

| 项目 | 修前反例与可观察结果 | 最终修复 / 证据 |
| --- | --- | --- |
| diff 乱序（A0） | 连续两次手动刷新；第二个响应先回、第一响应后回，最终 `stale-diff` 覆盖 `newer-diff` | 统一 diff controller、递增序号和 project/Agent/epoch/workspace scope 校验；App 回归保留乱序，以及 workspace、epoch、Agent、关闭面板后的迟到响应 |
| 全局 IME（A0） | composer 的 `Ctrl+K` 带 `isComposing: true` 仍打开 Command；输入组件本身防 Enter 不能证明全局处理正确 | 全局键盘处理先检查 composition 与 legacy `keyCode=229`；回归覆盖 composing Ctrl+K/Esc 和 229 |
| 长内容按需挂载（M0） | 同一组件 long → 打开 details → short → long；新 details 已关闭但完整正文仍挂载 | 展开状态移入随长内容分支挂卸的 `LongMessage`；回归验证闭合时未挂全文，重新展开仍等于原文 |
| 移动抽屉与 Esc | 初始源码仅 CSS/scrim，没有背景 inert/焦点进入与恢复；全局 Esc 会同时关闭 Command 和底层抽屉。这部分先由源码发现，不伪称已做移动 Chrome 测量 | 增加互斥 drawer、inert、焦点进入/恢复和 Tab 环绕；Esc 优先关闭顶层；“给当前 Agent 派活”收起抽屉再聚焦。App 回归覆盖 inert、关闭入口、两次 Esc 层级；真实焦点/布局仍须浏览器验证 |
| 同资源并发（A1） | 手动 `/view` 慢请求在途时从专注切画布，旧 scope `p/true` 变 `p/false`；实测同时有两个 `/view`，旧手动请求无 signal | 呈现需求不再作为 `/view` 资源身份；同项目复用在途 round。最终 stdin 复核 manual → canvas，`/view` 计数保持 1 |
| 终端错身份（A1） | `p/buddy/1` 终端打开后切 q，q/view 延迟；effect 记录 `q/buddy/undefined`。父 effect 后续关闭不能撤回子 effect 已启动的创建请求 | 明确 terminal identity，仅在已验证当前 targetReady 且 project/Agent/epoch 完全匹配时挂载；稳定的 canvas 回调从最新可信候选读取。最终同反例只记录 `p/buddy/1`；App 记录 props，并覆盖普通 Agent 切换不自动接管 |
| 返回旧项目漏去重（A2） | 手动 p/view 延迟 → q → p；单 ref 被 q 覆盖，观察到旧 p 无 signal、新 p active 两个请求 | 使用按 project 保存的 request Map、每 round 自有 controller；切项目 abort 旧 round，返回时等旧 round settle 后重取。最终复核旧 p abort=true，结算前 p 只发 1 次，结算后只有 1 个 active p |
| hidden 回执旁路（A2） | visible 发 POST，隐藏页面后才回 202；mutation 没重发，但其后 `refreshView()` 在 hidden 新发 `/view`、`/jobs` 各 1 次 | 读取入口统一 hidden gate，不取消/重放 mutation。最终复核 hidden 新 GET=0、draft 清空、unknown=false；恢复 visible 后补真实 `/view` |

另外对新取消路径及 fan-out 做了反向检查：

- **取消错误泄漏**：真实 fetch 按 AbortSignal 拒绝，而非永远忽略 abort。最终复核切项目取消 p 后，q 没有旧 p 的错误提示；取消检查在读取结算后执行，界面 follow-up 也过滤过期/取消错误。不能靠忽略所有错误通过，真正失败仍保留。
- **兄弟请求早失败**：`/jobs` 立即 503，`/view` 长 pending。使用 `Promise.allSettled` 保留 round gate；最终复核等待 1.95 秒，慢 `/view` 仍只有 1 个；让它结算后，真实 `jobs failed` 明确出现。没有用 `Promise.all` 的早 reject 冒充所有底层请求已结束。
- **主动接管意图**：当前 Agent 经画布接管后手动关闭，再更新 epoch；最终实现不凭残留字符串意图重开终端。显式 identity 与普通选择分开，不把“改变选择”当成“接管终端”。

## 4. 修后快照与实际执行

最终 stdin 复核完成时的来源指纹：

| 文件 | SHA-256 |
| --- | --- |
| `web/src/App.tsx` | `f49ca71b62c879285058d706bc2ce9a6a73e2dc53c20519d290b42867663f743` |
| `web/src/Terminal.tsx` | `d5c6b0468c5b46a0758920955f287e243fdbf530b842a90762ac87fa9498b001` |
| `web/src/polling.ts` | `1fca0a03cf94f3e6e06d26a6ff852d1bdb6eeadc354df9dd8710c2512f19a7f8` |
| `web/src/MessageContent.tsx` | `fcc4416c6c3cefb966299c92d06d6326f73f735ae1216ca6356a864187faaf46` |
| `web/src/App.test.tsx` | `97f178a5dbb632c731a1a7dc3ec1788b49c00d474ecd780ba2ee292823fbcbd9` |
| `web/src/polling.test.tsx` | `8045452186182063cc2dbaf75099d48771c843b7661dfe3320447775d69e3747` |
| `web/src/MessageContent.test.tsx` | `711f1d5fbb69c9f9c2c80db05c26134b36b05176106afcaea14d8c9f31fc100d` |
| `web/src/Terminal.test.tsx` | `561a585399b1e3871002c43f698dd4a7e8a35663d9fef8310edbabea6e653605` |

独立执行（工作目录 `web/`）：

| 命令 / 验证 | 实际结果 | 边界 |
| --- | --- | --- |
| `npm test -- src/polling.test.tsx src/MessageContent.test.tsx src/Terminal.test.tsx`，18:20:26 | 3 文件，19/19 通过 | 中间快照；不能替代后来 App 修复的回归 |
| `npm test`，18:25:52 | 6 文件，73/73 通过，6.60 秒 | Vitest/jsdom/stubs；包含其他前端文件测试，不等于对其独立完整评审 |
| `npx tsc --noEmit`，同轮 | exit 0 | 类型检查，不是浏览器或性能证明 |
| 最终 stdin 场景，18:26:54 | 原两例、p→q→p、hidden 回执/恢复、兄弟早失败、取消错误隔离均得到上文结果 | 没有真实 CLI 或 WS，不计为浏览器性能样本 |

源码复核没有发现另需单列的编码标准违规；这不是对未审查文件、全部业务组合或后续改动的保证。

## 5. 结论与未测边界

在列明快照和反例范围内，已报告问题均有针对性修复，当前没有因此仍开放的前端阻断项。回归从只测 hook/单组件扩展到 App 入口，不能只拿 `useSerialPoll` 单测推导手动刷新、mutation follow-up 和项目切换全部正确。

仍须单独保留以下验收，不以 73P、类型检查或此报告替代：

- 独立无登录 Chrome 的真实布局、画布/Command、触摸、原生 dialog 的焦点恢复、抽屉 Tab、中文 IME 与移动视口；jsdom 不实现真实绘制和完整惯性/焦点行为。
- 真实 CCB/CLI、终端创建与源 pane WS 的生命周期、断连、服务端句柄回收和权限边界。App identity mock 只证明组件不会按错误身份挂载；Terminal mock 测试不能证明真实网关同时连接数。
- workspace allowlist、managed worktree 回映、symlink/路径替换、错误 scope 的服务端拒绝；前端传 Agent 而非任意 path 不是服务端权限证明。
- SPEC 的 1/20/100 UI 节点、ordinary/fit-all、全部 5 reps、frame/选择响应/long task，以及 culling、hydration、visibility 分离消融。长文本 1/10 MiB 单元测试只验证可访问原文与按需挂载，不证明输入延迟或内存达标。
- hidden 测试是应用 visibility gate 的受控功能证据，不是浏览器原生后台限速的性能证据；取消客户端读取也不意味着服务端工作已回滚。
- 本轮不新增 Web project-open、worktree 生命周期、第二调度器或永久写锁，不从这些测试推导未授权功能已实现。

验证结束后已关闭 stdin 创建的 Vite server、清理 jsdom/组件实例；没有下载图片或生成一次性源码副本。保留既有依赖/缓存、可重跑测试和本报告，不删除原始证据或用户数据。
