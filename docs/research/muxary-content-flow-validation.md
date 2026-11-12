# Muxary 长内容与终端流分层验证

- 日期：2026-11-11；采样约 18:38:53–18:40:37 +08:00，后验功能补充约 18:41:28–18:41:42。
- 状态：**已采集；包含失败及负面结果，不是“全负载性能通过”报告。** 本轮未修改生产源码。
- 对应边界：[工作目录与画布 SPEC](../specs/muxary-workspace-canvas.md#5-数据终端与长内容预算)。此前[只读对抗审查](muxary-expansion-adversarial-review.md)保持冻结，不倒填后来的 Command/mobile-focus 修复或本轮测量。

## 1. 可验证对象与隔离层

1. **长内容渲染层**：真实生产 Web build、App/MessageContent 和浏览器；仅拦截 GET `/api/projects/:id/jobs`，注入完整 1 MiB / 10 MiB reply。会话认证、项目、view 仍通过原 fixture 服务。此入口是明确标注的 UI renderer fixture，不是实际 Provider/大结果 API 的端到端容量证明。
2. **单因素 hydration 消融**：A 保留默认按需 `details`；B 在单独浏览器上下文中，用 fixture 的 MutationObserver 默认打开同一个 `details`。A/B 同运行 observer，只改变是否展开；生产代码、完整文本、响应 hash、60ms 路由延迟、纯文本展开形式、CSS、视口、原 polling 代码不变。不把 B 换成 Markdown 或另写一个 renderer。
3. **终端层**：保留真实 lazy Terminal、xterm 6.0.0、FitAddon 0.11.0；只替代 terminal create receipt 与该 terminal WebSocket 传输，不替换 xterm/write。未连接真实 PTY、未调用模型。
4. **既有单测层**：`Terminal.test.tsx` 的 fake-write/callback 控制能精确检查未消费预算与释放时机，但不因此声称真实 xterm 在所有负载下都不卡。

原始材料保留于本机私有目录 `~/.local/share/muxary-dev/expansion-review/content-flow/`（目录 0700、文件 0600）。沿用现有 `connection.json` 的 origin 与 `browser-state-private.json`，未再次 bootstrap、未打印 token；没有读取个人浏览器 profile。下文 hash 均为 SHA-256。

## 2. 前瞻协议、身份与控制

### 采样前冻结

| 材料 | Hash |
| --- | --- |
| `protocol.md` | `329a738488707398548e1630559757d7524fe4ff42b53bd52fb1432b776f45b7` |
| `run.cjs` | `c56d0797d4486ed36b786285774274c2b6e471dfd3c0b251b946d4a7e7b80e93` |
| `fixture-manifest.json` | `c33b6a4eedff95915293ea3340bbd608c8275d40945674f8496d85a3caf45b34` |
| `web/src/App.tsx` | `f3114d63167f1f43b1df199f1648b27fccb92c4e657b562e6950893b76afb006` |
| `web/src/MessageContent.tsx` | `fcc4416c6c3cefb966299c92d06d6326f73f735ae1216ca6356a864187faaf46` |
| `web/src/Terminal.tsx` | `d5c6b0468c5b46a0758920955f287e243fdbf530b842a90762ac87fa9498b001` |
| `web/package-lock.json` | `fecfa34dc4726c0c56fa8f39ce80e8e240f7b07505b0fd0ffeffd329c14b1035` |
| 主生产 JS `index-Csq1waKg.js` | `d22724183932d3c63c3fc09ea9266ced91948d9657f9e36a35207e67fdd9693e` |
| 生产 Terminal JS `Terminal-BJWEf2c2.js` | `d78655dc013ef271c7331acf74c2304dbb517e49911ca51e8899d1ebf998bdaa` |

完整生产 asset 身份见 `execution-identity.json`；采集后再次逐项核对仍一致。运行环境为 Node v22.23.1、全局 Playwright 所带 Chromium **151.0.7922.10** headless、Linux 6.6.119-49.20.tl4.x86_64、AMD EPYC 7K62、可见 32 CPU、约 62.3 GiB RAM、1440×1000。

**混淆保留**：这不是独占机器测量。父代理在窗口内另有轻量最终浏览器 E2E、前端 tests/build，后端 full suite 亦在共享机器；canvas 代理在本窗口没有重载。未锁 CPU 频率、电源模式或真实显示刷新率；不将此 headless 机器的时延泛化到用户桌面。生产资产 hash 未变化不消除 CPU/调度干扰。

### 预先确定的样本与量测

- 4 个保留 warmup：每个 size×variant 一次；20 个正式样本：1/10 MiB × A/B × 5 reps，A/B 顺序交替。全部保存，不删除失败或挑选有利样本。
- 每个样本新建 context，使用同一 Chromium 进程。首份完整 jobs 响应延迟 60ms；测量结束前后续 GET 若发出则保持 pending，不拒绝，结束后释放。生产 polling 未改。这样 timed window 的 A/B 均只交付同一完整响应一次，不拿早拒绝证明下游有效。
- 记录默认 DOM、全文字符数、preview、Markdown DOM、CDP heap、导航至 renderer-ready、10 次真实输入事件至下一 rAF 的时延、约 600ms 交互窗内 rAF 与全部 long tasks；不把输入至下一 rAF 说成已完成像素绘制。
- 时延建议门槛仍为每 rep 输入 p95 ≤100ms、交互窗口无 >200ms long task。冷启/首次展开另报，不能藏在交互窗口之外后称整条路径无卡顿。
- 计时后显式展开、在浏览器对完整 `pre.textContent` 编码并计算 SHA。A 再关闭、切 native source/返回、切 Agent/返回，检查不会自动挂载全文。原生 source 的短回复也是独立 fixture。

### 完整内容身份

| Reply | UTF-8 字节 | Reply SHA | 完整 jobs JSON 字节 / SHA |
| --- | ---: | --- | --- |
| 1 MiB | 1,048,576 | `11542a12fbdd9cabef70f474c067bc99b2a26426486dcea23f8b4254315421ad` | 1,063,780 / `a6f82e4d451df100829b77ff303c7df7407ba5850e80bc4e6bf76d28ebc56495` |
| 10 MiB | 10,485,760 | `205eb9faeda1c81bb4d89a2493a6f230c06b5b60e3bd49929cd7bd88188811b4` | 10,633,883 / `f5374dd543b58bc14874607c8c790563873ae9b009f4a526275f18f49daaa771` |

文本为可重复生成的 ASCII、多行 Markdown 标记字符串；字符数等于其 UTF-8 字节数，不代替 CJK、超长单行或复杂 Unicode 测试。

## 3. 长内容结果：完整数据相同，默认挂载不同

20 个正式样本在**默认表示、完整 SHA 和预设切换检查**阶段均达到各自断言；不要将此误读为每个完整脚本都 pass，后面的刷新断言有失败。

- A 默认每次仅一个 **2001 字符** preview，`message-full-text` 数为 0；B 默认有一个完整 `pre`，字符数分别为 1,048,576 / 10,485,760。
- 长回复区域的 Markdown DOM 数均为 0；冻结源码的 `>12000` 分支直接走 LongMessage，不调用 Markdown。任务请求那段短文本仍可以使用 Markdown，不能声称全页没有 Markdown。
- 所有正式样本显式访问到完整原文，浏览器 SHA/字节均匹配上表。所有 A 正式样本切 source/Agent 返回后仍无全文挂载，preview 保留。
- 默认 DOM elements 为 A **266**、B **272**。只差 6 个 element 却承载最多 10 MiB 额外文本，说明**节点数不能作为数据完整性、文本成本或虚拟化正确性的 oracle**。
- timed window 每个正式样本均完成 **1** 份 jobs 响应；10 MiB B 的每个样本另有一个尚未交付的 pending GET（其他 cell 请求数为 1），两组实际交付的完整字节相同。请求数差异仍记录，不能声称所有网络事件完全一致。

下表每格保留 reps 1→5 的值；heap 为计时窗末 CDP JSHeapUsedSize，不是 RSS、DOM/渲染器总内存或经 GC 的保留对象证明。

| 正式 cell | Renderer-ready ms | JS heap MiB | 每 rep 输入 p95 ms | 冷启最大 long task ms |
| --- | --- | --- | --- | --- |
| 1 MiB A | 369 / 356 / 351 / 388 / 349 | 6.65 / 6.68 / 6.65 / 6.59 / 7.27 | 14.2 / 13.0 / 14.0 / 15.5 / 15.2 | 65 / 64 / 64 / 63 / 62 |
| 1 MiB B | 468 / 467 / 465 / 467 / 452 | 11.38 / 11.37 / 11.37 / 11.38 / 11.38 | 15.3 / 17.2 / 14.1 / 16.3 / 15.1 | 137 / 138 / 136 / 138 / 135 |
| 10 MiB A | 691 / 629 / 622 / 637 / 625 | 15.68 / 15.69 / 15.50 / 15.69 / 15.67 | 16.4 / 15.5 / 16.5 / 14.4 / 15.4 | 74 / 65 / 63 / 65 / 64 |
| 10 MiB B | 2073 / 2058 / 2060 / 2072 / 2085 | 55.75 / 55.76 / 55.93 / 55.76 / 55.76 | 24.7 / 25.0 / 24.8 / 23.8 / 24.2 | **1398 / 1382 / 1384 / 1404 / 1398** |

正式交互窗口全部 rAF p95 为 16.7–16.8ms，long task 列表均空，输入建议门槛均满足。**10 MiB 默认全文的首次呈现却有约 1.4s long task**，不满足将 200ms 应用于整条初次呈现路径的要求。这个负面结果没有被稳定交互结果覆盖。

限于该 fixture/设备，数据支持“按需 hydration 避免默认展开的额外布局与内存成本”，不支持“JSON 不再驻留内存”“点击展开也不会卡”或所有大回复都达标。A 中完整字符串仍已从网络接收并存在状态里；显式展开 10 MiB 仍会产生大文本布局，此段未作预先冻结的独立时延采样。

## 4. 原始失败与后验补充：不改写 verdict

### 刷新完成等待假设

原脚本在末尾点击刷新后只等 180ms 就断言新增一份完成响应：

- 1 MiB：2 warmup + 10 正式完整脚本均 pass。
- 10 MiB：2 warmup + 10 正式完整脚本均 **fail** 于这一断言。此前的 DOM、完整 SHA、A 切换检查及计时材料均已记录。失败 JSON/截图/脚本保持原样，未改为 pass。
- 观察到 fixture 自身传输完整 10 MiB JSON 的完成时间超过 180ms，不能用固定 sleep 把异步正确性判断为实现已坏，也不能事后延长等待后倒填原 verdict。

另冻结 `supplemental-refresh-protocol.md`（`bc7e983265983ea2cf37b0a227a101872dd8f5151960b6f46d53da2bc3b4b539`）与脚本（`f455a3c017117b367a3b6ba1b34d98b5a343b36dce601f58e7afb1aa97625634`），只补一份 10 MiB A 和 B 的**功能**检查，等待真实路由完成（上限 30s，不是性能 gate）：A 在点击后 **346ms**、B **426ms** 完成；刷新前后完整 SHA 一致，A 仍默认不挂全文。补充结果均 pass，**不重采性能、不替代原失败、不把 30s 变成 UI 性能预算**。

## 5. 真实 xterm、传输 fixture 与负面结果

### 1000 lines/s：单次功能样本

- 每 100ms 一批 100 条唯一编号行，共 50 个 output frame、5000 行；记录窗口 **4.9997s**，目标 1000 lines/s。真实 xterm 保持正常已连接状态，页面保持一个 xterm，流窗口无被 observer 记录的 >50ms long task（冷启另有 65ms）。
- 截图 `terminal-1000-lines-per-second.png` 显示顺序编号输出。**可见区域最后为 `FLOW-LINE-004987`，没有显示第 5000 行**；固定 120×32 源栅格超出当前 pane 可见高度，未另开浏览器滚动核验。故这里只证明传输了 5000 行、真实 renderer 显示了部分连续编号且镜像未断，不声称逐行核验全部已消费、无丢失或已看到最后标记。
- 这是一次功能样本，不是 5 reps 终端性能验收；不将无一次明显卡顿泛化为所有 ANSI/字体/栅格/设备负载都不卡。

### 原前瞻 3×1 MiB burst：失败保留

原协议假设“同一 producer task 中，真实 xterm.write callback 必须等 task 结束才执行”，因此预计 3 帧会超过 2 MiB pending。实际三帧 burst 约 **360.6ms** 后 socket 仍 OPEN，等可见 backlog 诊断 30s 超时：**原样 fail**。

这推翻了原协议的 callback 时机假设，不能据此判断生产 byte budget 失效，也不能宣称已经制造出慢消费者。回调何时同步结算未被直接 instrument；“输入后首批可能同步消费”只是解释假设，不作已观测事实。

### 后验四帧边界探测：功能 pass，性能仍有失败

在保留原失败后，另冻结补充协议（`2ae39ff33a38ae16d7f9b157e2b07eb1386a4a595ad24bff04ccf67c891080fb`）与脚本（`496ba12841a1cb7224479d4765cea0570602700c132abeda5f7617311fc8c8b9`），只将 burst 数从三改为四，其余仍真实 xterm、同 receipt/WS fixture、一份先前输入：

- socket CLOSED，可见诊断为“终端输出积压；已关闭本页镜像。原 CLI 继续运行，可手动重连；不会重放输入。”截图实际可读。
- 没有自动重连；显式重连后两个 socket 的记录总计仍只有 **1 次 input、seq=1**，发送于第一个 socket；第二个只有 open，未重放输入。
- **该 burst 有 562ms long task，evaluate 约 559.7ms**。功能上的可见断开不等于没有冻结；此样本不满足 200ms 建议门槛。2 MiB pending budget 防止无界累积，不会消除大帧 base64/Uint8Array 转换、xterm 首次解析的同步成本。

后验四帧结果不让三帧前瞻假设“复活”，也不能替代所有慢消费者/真实 WS 背压测试。既有 callback 控制单测只在自己的层证明按 callback 释放预算；本轮未给真实 Provider/PTY 继续运行、重连历史、实际网络拥塞或服务端 handle 回收新增背书。

## 6. 可保留结论与下一步边界

- 保留按需纯文本 hydration：在相同完整字节输入下，默认不挂载巨型原文，完整 SHA 仍可访问；本次 10 MiB A/B 的首呈现/heap 代价有明显差异。
- **未宣称**全部脚本通过、所有内容性能达标、默认预览是消息虚拟化、显式展开无卡顿、DOM 少证明原文完整、终端极端 burst 无长任务。
- 如进一步优化大帧，应分别前瞻测量 base64 解码/解析与 pending budget；成熟 xterm flow-control seam 和服务端分帧/背压需独立决策与消融，不能只降低可见输出或静默丢数据来制造 pass。本轮未新增这些机制。
- 若要把“5000 行全部已渲染”列为门槛，需要真正可读取的 buffer/末标记 oracle，再单独冻结协议；当前截图不满足这个门槛。中文 IME、移动端长文本、10 MiB 单行、数十条大回复、持续多分钟/断网/真实 Provider 流仍未测。

## 7. 证据与清理

`summary.json` 保留原 26 个结果：4 warmup、20 正式、2 terminal，其中 **13 pass / 13 fail**；每个失败仍存在。`aggregate.json` 只是这些样本的无删选汇总。后验两份 refresh 样本及四帧 terminal 单独保存，不替换 summary。

脚本仅新建自己的独立 Chromium/context；所有路径均在 `finally` 精确关闭，初始记录到的 PID 已核对退出，未终止共享 fixture 或其他浏览器。18:41:55 已通知父代理与 canvas 代理释放窗口；之后只离线处理材料。保留可复验脚本、私有 JSON/日志/截图、既有依赖与生产交付资产，没有创建待删的一次性源码或下载工具，未改旧冻结证据。
