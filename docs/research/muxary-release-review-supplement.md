# 提交前独立审查补充

- 日期：2026-11-11（Asia/Beijing）。
- 范围：Q9 registry 并发补丁、分发许可、更新入口优先级，以及截图中的自动跟随疑点。
- 本文追加当前证据，不改写[前次 Q9 对抗审查](muxary-q9-adversarial-review.md)、[内容/终端实测](muxary-content-flow-validation.md)或既有失败记录。
- 审查期间没有再次调用模型、启动 Chrome 或执行前端构建。进入最终独占性能窗口后，仅做只读检查和本文记录。

## 1. 新反例：迟到的 preflight 候选导致多余启动

### 独立复现

修前 `service.py` SHA-256：`47dab3beb8e74de067f53ad5c22e229b35a843451a7f6172c7f30ff69137da8e`。

受控两线程仅替换 discovery 和 CLI opener 两个外部边界，使用真实 `WorkbenchService`、registry 和就绪检查：

1. 打开项目请求先取得仅含 old 的 discovery 候选，暂缓返回。
2. 另一读取发布 old + target；此时工作台可查到 target，真实就绪检查为真。
3. 释放旧 preflight 候选。
4. 修前打开请求最终返回 `200`，但仍调用了一次 cold starter。

因此反例是“已确认可用项目仍触发额外启动调用”，**不是证明底层 CCB 已强制重启或重复创建了进程**；底层 `--safe` 可能自行复用。不能用最终 `200` 掩盖多余副作用。

实现者只调整 preflight 选择：先检查当前已发布 registry；无匹配才检查本次候选。匹配但不可用仍 fail closed。原有 post-start 自有候选就绪确认、短锁 merge、generation fence 保持不变，没有增加调度器或等待慢读取。

### 同一脚本复核

修后 `service.py` SHA-256：`a6ae5de244df2099ad91cf7abd52d48aa884bb2485663b924e3f3f6195d43ebe`。

| 阶段 | 当前已发布 target 就绪 | 打开响应 | starter 调用次数 |
| --- | --- | --- | --- |
| 独立 red | 是 | 200 | 1，断言失败 |
| 相同脚本 green | 是 | 200 | 0 |

本机原始材料位于 `~/.local/share/muxary-dev/expansion-review/q9-adversarial/`；未入仓：

| 文件 | SHA-256 |
| --- | --- |
| `preflight-candidate-offline.py` | `3a8af515f2c8a01c3aa9cca68cb1ea86ee4de0fbae1d067f2f155eb31e2a9b89` |
| `preflight-candidate-offline-red.log` | `93d3974d12384916eaaea82ce0722a9cc6c12ad1bd9ed20e3adda1c4958cb27e` |
| `preflight-candidate-offline-green.log` | `14dbc6e9f33e5507f8e7059d685156dfdd10a92ef3e54e98a866bbb826770617` |

实现者的持久回归 `test_stale_preflight_candidate_cannot_start_project_already_published_live` 为 1 failed → 通过；与既有乱序案例一起运行得到 5 passed。审查者另以不变的独立脚本复核，不把实现者自测冒充第二次独立复现。

### 175 → 176 的准确边界

以下来自实现者保留的日志，审查者读取原文，未再次执行整套测试：

- fresh-candidate 初次 affected：**1 failed, 174 passed**。额外诊断确认启动器退出 127，`CCB_PYTHON` 未设置且找不到符合依赖的解释器；不是把失败删除或改 gate。
- 明确配置已有可用解释器后，同阶段：**175 passed in 53.08s**。
- 加入本节新反例并修复后，同范围：**176 passed in 52.53s**。

这些是测试环境下的指定 interleaving 和 affected 范围，不证明任意线程调度或真实 Provider 永远可用。后续只读检查未得到另一个已实证的并发阻断项；不将“未复现”表述为全局并发正确性证明。

## 2. 发布许可：已补齐分发路径，精确来源缺口仍公开

### 分发机制

使用 Vite 原生 `build.license.fileName = 'THIRD_PARTY_NOTICES.md'`，不自造依赖扫描器。现有 vendored Agent Elements / shadcn 许可证继续独立保留。

实际生成的 notices 为 **149,224 bytes**，SHA-256：`6d81b29338646d3d3812a9f7127f32a74a8551e6edaa25abefd97d06a99507e5`。只读比对其 135 个 bundled 包：134 个许可正文与本机对应包文件一致；唯一没有正文的条目为 `react-remove-scroll-bar@2.3.8`。在这 135 个包目录中未找到单独 NOTICE；开发依赖 TypeScript 的 NOTICE 不在实际 bundle 中。该结论只对应本 lockfile 和 bundle。

补充静态文件通过 Vite 标准 `public` 复制，实际 `assets/workbench/licenses/` 文件与源文件 SHA 逐项相同：

| 文件 | 来源/适用边界 | SHA-256 |
| --- | --- | --- |
| `Apache-2.0.txt` | Apache 官方完整条款；适用 bundled streamdown 2.7.1 / remend 1.4.0；各自版权声明仍在生成 notices | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| `react-remove-scroll-bar-upstream-MIT.txt` | 同项目固定 upstream commit 的真实 MIT 补充，非 2.3.8 发布字节证明 | `a79aae0c0f21990d9d963bb3c5a79cdcea9a46f8523ba55c58d7fe776b6ebc84` |
| `README.md` | 来源、版本关联及未解决的精确发布身份边界 | `d87cc47073e1afeb28184fc2c95a6b02a809b973ba43e0f51f8e46211b5fe3a6` |

完整 URL 和字节长度见 [`web/public/licenses/README.md`](../../web/public/licenses/README.md)。npm 2.3.8 声明 MIT，但发布包缺 LICENSE，其声明的 gitHead 对应文件请求返回 404。补充文件来自同项目固定 commit，那个 commit 的 package.json 仍标 2.3.7；**没有获得 2.3.8 精确发布许可正文的验证，不能写成已获得**。该缺口未通过修改或覆盖生成 notices 来伪装解决。

### Gate 与单因素回归

release validator 必须拒绝 notices 和三个补充文件缺失、空内容或纯空白，并验证 tar 中保留正文：

- 生成 notices 缺失/空/空白：red 3 failed → 最初完整文件 15 passed。
- Apache 正文和来源 README：red 6 failed → 21 passed。
- upstream MIT 补充：red 3 failed → 最终 **24 passed in 0.33s**。

非空 gate 只检测分发遗漏，不证明所有未来依赖的法律状态或正文完整性。`q9-licenses-final-delta.json` 包含 Q9 混合构建的 JS/CSS/index 变化，不能用它证明“补充许可这一个因素不改变 bundle”；仅静态文件复制的逐字节匹配已在本轮独立核实。

## 3. 更新入口与 CodeBuddy 发布身份

`_installed_ccb_entrypoint()` 已与 `install.sh` 对齐：非空 `MUXARY_BIN_DIR` 优先于 `CODEX_BIN_DIR`，然后保留原 argv/home/install 候选规则。

- 预先加入新变量 only / 两变量不同 / 旧变量 only / default 四例：red **2 failed, 2 passed**，新变量两例失败。
- 最小实现后同四例：**4 passed**；原 update 文件完整运行：**69 passed in 1.04s**。
- 这些测试验证路径选择，不声称实际远端更新发布已完成。

本机已核 `@tencent-ai/codebuddy-code@2.183.0` 同时发布 `codebuddy-code`、`codebuddy`、`cbc` 三个 bin，指向同一 `./bin/codebuddy`。因此此版本的默认 `codebuddy` 与评估命令 `codebuddy-code` 并不矛盾。详见[真实联通记录的命令身份补充](codebuddy-live-validation.md)；不泛化到全部历史版本或平台。

## 4. 截图中的最新消息不可见：观察成立，成因尚未证实

只读检查已有 `q9-browser-acceptance-04/opened-project-working.png`：终端可见 acceptance 04，任务来源显示三条，但对话可见较早记录。没有当时 scrollTop / clientHeight / following 状态或用户滚动事件轨迹，单张截图不能证明是消息未接收、排序错乱，或用户主动阅读历史。

当前 `App.tsx` SHA-256：`759b423c28dd6c08745f3285459e892e486bda9d8cc05a1d317797c14b4dda56`。静态事实：

- 自动滚动 effect 依赖记录数量、最后文本、来源和 focus/canvas，不依赖 terminal 开关或容器高度。
- `onScroll` 用距底部 100px 阈值更新 `follow`；没有区分用户滚动和布局导致的 scroll。
- 没有 ResizeObserver 维护对话容器的贴底关系。终端展开/拖动、目录详情等导致视口变小时，现有 effect 不保证仍贴底；若没有 scroll 事件，`following` 也可能仍为真。

这是**有代码依据的已知交互限制与待验证原因**，不是本轮已复现的浏览器产品反例。未启动额外浏览器或 jsdom 来制造布局通过。后续最小真实布局回归应固定足够溢出的历史，分别测：贴底时展开/拖动终端后仍见最新；主动向上阅读时不被抢滚；返回最新后新回复再次跟随。需要记录真实几何值及事件顺序，jsdom 手设尺寸不能代替浏览器布局证明。

## 5. 交付范围与清理

提交范围审查未发现新增私钥、凭据、私有会话、浏览器 state、缓存或构建产物混入交付文件；模型 raw、令牌和本机 fixture 仍留本机、不入仓。这是检查当时范围的有界结论，不代替提交前最终 `git status`。

本轮只删除逐一核实属于本次 release-test 的四个私有 `supplementary-license-*-tmp` fixture 目录；保留 red/green 日志、复现脚本、源码、依赖、用户数据及仍用于发布验收的构建资产。没有清理其他 agent 的测试/浏览器目录。
