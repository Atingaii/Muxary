# Q9 增量实现：独立对抗审查

- 日期：2026-11-11，约 18:53–19:01（Asia/Beijing）。
- 范围：项目打开 dialog、Command 入口、项目 → 目录 → Agent 分组，以及项目打开后的 registry/gateway 接入边界。
- 关联：[Q9 真实模型复核](muxary-q9-product-review.md)、[当前 SPEC](../specs/muxary-workspace-canvas.md)、[ADR-0003](../adr/0003-workspace-and-canvas-presentation-boundary.md)。
- 结论：下列两个具体反例已复现、由实现者修复，并以独立相同脚本复核；**不是最终 release、浏览器视觉、性能或真实 Provider 联通验收**。此前[内容/终端验证](muxary-content-flow-validation.md)仍对应其原 build，不倒填到 Q9。

## 1. 审查方法与证据范围

独立审查者不修改生产源码或持久 tests。按实现边界和 SPEC 分别检查，而不是以代码风格意见替代可观察错误。

- 前端：真实 `App.tsx`、jsdom、Testing Library，通过 Vite `ssrLoadModule` 加载。仅 Terminal、Canvas、Markdown 替换为轻量组件；`fetch` 使用 deferred `Response`。这能验证状态和请求次数，不能证明原生浏览器 dialog 的布局、焦点或 xterm 行为。
- 服务端：真实 `WorkbenchService` 和 `MobileGatewayService`，只控制 registry discovery 与 CLI opener 两个外部边界；临时项目身份、真实服务对象与两线程制造明确乱序。不是声称真实 `/proc` 恰好发生过相同调度。
- 原始材料：`~/.local/share/muxary-dev/expansion-review/q9-adversarial/`（0700，文件0600）。保留初次 harness 未同时设置 `window.ResizeObserver` 的环境失败，以及修正 setup 后的产品 red/green，不把环境失败计为产品反例或删除。

## 2. SPEC 轴：反例、修复、复核

### A. 关闭慢 dialog 后，选择 ABA 被迟到结果覆盖

SPEC 要求迟到结果不得抢走后来主动切换的项目/Agent。修前 `openProject()` 只比较开始/结束时的两个字符串，忽略中间选择历史。

1. 在 `p/buddy` 提交打开 `/new`，响应保持 pending。
2. 关闭 dialog，选择 `coder`，再主动选择回 `buddy`。
3. 让旧请求成功返回 `new`。
4. 修前观察：响应前是 `Fixture project/buddy`，响应后变成 `new/buddy`。POST 始终只有一次；问题是过期选择意图，不是重复启动。

修复为轻量 `selectionRevision`，提交捕获 revision；只有没有后续选择变更才自动进入新项目。目录仍可加入列表，不丢弃已经真实成功的结果。修后相同脚本：响应前后均为 `Fixture project/buddy`，POST 仍一次。

| 阶段 | `App.tsx` SHA-256 | 结果 |
| --- | --- | --- |
| red | `ab68be41a383058e3ab6b279db2afbd22ffa90f8a43eedec596d6cd2e7d45279` | 迟到结果覆盖 ABA 后的选择 |
| 首次 green | `fa71b0138b1189cba7b29fc1c53b792a7505e1763dc2601f1e698673ea841e09` | 同一反例不覆盖 |
| 目录标签增量后的再次 green | `759b423c28dd6c08745f3285459e892e486bda9d8cc05a1d317797c14b4dda56` | 同一反例仍不覆盖 |

实现者的持久回归：`App.test.tsx` 的 `does not steal a later selection even when the user returns to the original Agent (ABA)`。原先只测最终停在 `coder`，不能覆盖 ABA。

### B. 旧 discovery 迟到，覆盖刚确认可用的新 registry

SPEC 要求 registry 更新覆盖工作台及原 gateway，列表或 startup exit 0 不能代替可用身份。修前 `_refresh_registry()` 在锁外 discovery、锁内无序赋值，旧结果可以后覆盖新结果。

1. 线程 A 先取得仅含 old 的 discovery snapshot，暂停结算。
2. 打开 new：CLI opener 一次，后续 discovery 得到 old+new，返回 `200 ready`。
3. 此时工作台和真实 gateway 均能 lookup new。
4. 释放 A，修前 new/view 立即得到 `404 project not found`。

修复只为 discovery 提交增加 generation：短锁递增/提交，不把 discovery、启动或 RPC 放进共享锁。相同脚本修后得到 `view success`，启动次数仍一。没有以不执行旧请求、延长等待或修改 fixture 制造 green。

| 阶段 | `lib/workbench/service.py` SHA-256 | 结果 |
| --- | --- | --- |
| red | `fc10464abf7f7f6ed634bd1f5526f68f4f275ba91c1b8a1eedb4dd7d9e6a5150` | 200 后被旧 discovery 覆回，new/view 404 |
| green | `a57c84ba211e1b5fdbd75f6f57b57218ae997efdc98f2d2afb07a289eebc3309` | 旧 discovery 不再覆盖，new/view 成功 |

实现者的持久回归：`test_late_old_discovery_cannot_replace_registry_confirmed_by_open`。这只证明上述提交顺序边界，不泛化为所有 registry/生命周期并发已穷尽。

## 3. 其他只读检查与 Standards 轴

在上述最终前端快照及服务端 green 上，未另发现需单列的编码标准违规；该结论仅限本次增量，不是对全仓变更的标准审查。

- 目录按完整、实际报告的 path 分组，未知目录不猜项目根；仅已知 path 的多个 Agent 标共享。原先同 basename 只有 hover 区分，已改为**仅碰撞时显示完整路径**，触屏不再必须悬停才能区分。未增加目录派活目标或自行判断 worktree 类型。
- Command 的“打开本机项目目录”先打开确认 dialog，不直接发 startup/任务；全局 Ctrl+K 对项目 dialog/help 做阻止叠加，保留 composition/229 gate。真实焦点恢复仍需浏览器验证。
- 开始启动必须显式 submit；有实例内启动锁、固定原 CCB `--safe` argv、无客户端额外 argv、无 shell 拼接。打开原设置与保存配置不在前端热换 Agent cwd，也不造第二配置状态机。
- unknown 保留输入和可见诊断，当前相同输入禁止再次 submit；“查看已挂载项目”只关闭 dialog 展示原只读轮询列表，不新 spawn，也不旁路 poll gate 增加并发刷新。不同路径/别名最终仍须服务端身份与 unknown guard，不能只依靠前端字符串相等。
- 动态 registry 的原 gateway provider 指向工作台可信 snapshot，已检查新增项目不只是 UI 列表项。上文服务端脚本在迟到结算前实际验证了两者 lookup，未把 lookup 冒称真实 CLI/终端端到端通过。
- **明确限制**：`_uncertain_project_roots` 是当前服务实例内存保护，页面刷新仍由同实例保护；不是跨整个 Muxary 进程重启的持久 project-start receipt。既有 Job SQLite receipt 不能泛化为项目打开也具备此保证。整个后端重启后的显式再次打开仍应先核对原 CCB 状态。

## 4. 可复核材料与清理

| 私有材料 | SHA-256 |
| --- | --- |
| `aba.mjs` | `5c06293ebccaba7f1b55277a52dbbd24289fc020c52fedc3a551b5786aca9132` |
| `aba-red-fixedharness.log` | `6a8dcb724c8232a7e88f190990b02a713517f22b72b9a2fbb03f98a6f71a058e` |
| `aba-green.log` | `6361b0468a0d25aa0dee8c8b96b469921ad6adf35a9a1ce92581f6c21d8b411c` |
| `registry-race.py` | `b27874d6458fafa41ff36e6046eeb28d2aa75879e24d6b6159bb9f67d5fb13e9` |
| `registry-race-red.log` | `fa928daa18e212d121c200363ab97a4e0f6af4e6af1ef21086fa743b71fefbb7` |
| `registry-race-green.log` | `e9e0a3c3161e053dce113583b826ec6c76d3f55b36534020cf819fe8f7a1939c` |

本轮没有重跑全前端/后端 suite、真实 Provider 或浏览器验收，不把实现者另外执行的测试数记为独立执行。两次 ABA green 以及 registry green 是上述精确场景的独立证据；最终构建若再修改这些边界，应补自己的快照与回归。

所有自建 Vite server、jsdom 与服务对象均在 finally 关闭；Python 临时项目目录已自动清理。没有打开 Chrome，不占用画布代理的浏览器重载窗口。原始脚本/失败/成功日志是复核材料继续保留，既有缓存、依赖与用户数据不删除。
