# Q9：项目打开、目录分组与原 CCB 配置的真实模型复核

- 日期：2026-11-11；本条是追加记录，不改写[此前两轮产品评审](muxary-expansion-product-review.md)或其冻结原文。
- 用户已接受的问题原文：**“按项目→工作目录→Agent展示，可从Web打开项目、进入既有worktree配置与创建流程；明确共享目录/重启不热换，不删除/合并。”** 随后补充：**“可以参考主流这种设计，但是依托CCB。”** 这改变此前 Q9 pending 的产品范围，不改变 CCB 执行模型。
- 本记录完成真实双模型文本复核；**不是新实现、视觉、CLI 联通或性能验收**。追加实现/测试须有自己的身份，不能借此继承此前 build 的结果。

## 1. 实际调用与材料边界

两模型同一 prompt、独立答复，没有共享另一方本轮答案。CodeBuddy CLI **2.183.0**，`DISABLE_AUTOUPDATER=1`，使用：

```text
codebuddy-code -p --model <model> --tools '' --strict-mcp-config \
  --mcp-config '{"mcpServers":{}}' --max-turns 1 \
  --no-session-persistence --output-format json
```

请求提供：Q9 原文、CCB workspace/Job/registry 事实、既有 `ccb --safe` 启动及原 Config UI、主审 A–E 最小候选方案。没有传递凭据、个人配置内容或用户会话。模型未看截图、读源码、操作产品、测试性能或浏览 21st 来源；“主审代码阅读事实”不变成模型亲验。

私有材料：`~/.local/share/muxary-dev/expansion-review/q9-review/`（0700，文件0600），含同一 `prompt.txt`、runner、原始 raw、stderr、派生最终正文、metadata。无自动重试。数组 JSON 取末个 `type=result`，reported model 取 assistant `providerData.model`；身份是 CLI 的报告，不是对后端模型权重的独立验证。

- 请求 SHA-256：`cc04ad0e1ab7519c181eb59604e32ac048da0ecd64f6bd56709c6cc59d0e652b`。
- 两请求约于 18:46:41 +08:00 发出，exit 0、result success，stderr 均为空；没有公开 raw 中 reasoning/usage。

| 请求模型 | CLI reported | Session | CLI / 墙耗时 ms | Raw SHA-256 | 最终正文 SHA-256 |
| --- | --- | --- | ---: | --- | --- |
| `deepseek-v4.1-flash` | `deepseek-v4.1-flash-ioa` | `01a1ca37-9854-77fa-bc1d-33373a224ab6` | 38101 / 44188 | `30c29977b5fb7f0cab995bf0d0d07a42a59bbedc6587103181058355feb831d7` | `a4a131322928bcc7a873438d31aea805d4899b04d88172eb58e22340694ab1d3` |
| `claude-opus-5.5` | `claude-opus-5.5` | `01a1ca37-9874-7f47-8aa7-9dde20b42d21` | 128518 / 134570 | `803d932eb2bff4b6072316cec47a36a620a3349c9a99c4988eae8c7a1dbf18b4` | `8217e4be33402a5ea72be149234763d92d5168c83a2fa28ad67444b896fd4017` |

## 2. 两模型意见，不混同于主审决定

| 议题 | DeepSeek | Opus |
| --- | --- | --- |
| “打开本机目录”措辞 | 反对隐去启动副作用，偏“注册并启动” | 偏“在本机目录启动 CCB 项目”，说明读取/必要时创建配置和启动声明的 Agent |
| 目录组 | 条件接受；同 basename 要可区分，未知目录不可默认为根 | 倾向仅不同目录足够多时分组，也愿延后；绑定目录不能冒称实时 cwd |
| 已运行/alias | 服务端 canonical path 原子判重 | 特别指出 managed worktree 回映原项目；不能只比较输入 realpath 与 project_root |
| unknown | 只读核对运行状态，不“重试启动” | 保持 unknown；认为还需“已启动未接入”表达，并给受限显式再次启动提议 |
| Config UI | 要区分打开、保存、物化、live 绑定；提议四态 | 不读到原 restart_intent 就不显示“待重启”badge；不能声称已保存/创建/生效 |
| 对话前必须选 worktree？ | 不需要：AgentSpec/启动绑定决定目录 | 不需要：Job 仍只有 Agent+project 身份 |
| 组件 | 复用现有 dialog/input/Command，不加文件管理器 | 同意；worktree 徽标必须来自元数据，不凭路径猜 |
| 反例/测试 | Host/Origin、symlink/并发/断连、保存未重启、目录组单因素消融 | 加强 managed worktree alias、无 cookie/额外 argv 字段、unknown 跨刷新、配置/live scope 不变 |

**保留分歧**：Opus 倾向首版拒绝没有 CCB 配置的目录，DeepSeek 接受明确说明后的初始化；两者对目录组的价值均有怀疑。本记录不把这种偏好变成用户已确认范围的否决，也不伪写为三方无条件一致。

## 3. 主审保留的最低边界与对模型的反向审查

1. **先定义副作用，再选动词。** 原 CCB 启动可能读写配置、启动多个 Agent、触发原 workspace 物化/校验。入口和确认文本应明确未运行时会启动 CCB，不称只浏览目录；`--safe` 只说明不新增权限 bypass，不是无副作用保证。DeepSeek 文案“启动一个 Agent”不准确，不采。
2. **真实项目身份高于路径外观。** 先通过 CCB 现有身份规则处理已运行根目录、symlink 与 managed-worktree 回映；后者 canonical 目录不同仍可属原 project_id。不能任意把所有子目录认成父项目——须有可信 CCB 身份证据。普通 symlink 已由 realpath 消除，DeepSeek 关于它必然留下不同 canonical key 的泛化不采；特殊挂载别名需另界定。
3. **不要用前端禁用按钮冒充去重。** 服务端在真实启动边界判重，启动中/已发出的不明确结果不能自动再发。timeout/断连不等于子进程未启动；核对动作必须是只读，不能名为刷新实则再次 spawn。若长期 unknown 应明确限制/诊断，不凭一次空 registry 就断言可安全重启。
4. **接入的是执行权威，不是列表。** 新项目真实接入 registry 后，WorkbenchService 与 MobileGatewayService 的查找/授权必须一致。仅更新 UI 或 `GET /projects` 而 delegated view/jobs/native/terminal 仍用旧 registry，不能称项目可用。需要跨原适配器边界测试。
5. **不建第二个配置状态机。** 保持 live 绑定目录与原 Config UI 的 `restart_required` 语义；只打开配置页不能声称 worktree 已创建/保存/应用。未取得原状态时用静态准确说明，不造假的“待生效”badge或前端四态权威。当前声明/启动绑定不等于永久实际 cwd、文件沙箱或写入锁。
6. **不强引入第二调度器。** Opus 将请求线程启动一概说成“整个工作台卡住”过强：现有服务是 ThreadingHTTPServer，必须测具体阻塞/超时与去重边界，不能据一句话强加新后台队列。有限适配器可复用原启动；HTTP 回应、子进程生存期和服务重启仍需明确契约。
7. **尊重 Q9，仍消融复杂度。** 目录轻量分组可以承载已确认“项目→目录→Agent”，不因此加入目录派活目标、每消息 worktree 或新会话模型。可比较一目录时的轻量标签/组头，不机械保留折叠、计数、徽标等无决策增益装饰；不能未测试就删除用户明确需要的目录层。
8. **无新增 Web 强制生命周期入口。** 原 Config UI/下一次正常启动继续决定 worktree 创建与应用。没有新增删除、merge、prune、force、热换 cwd；但原 Materializer 自身既有行为不能被洗成“从不 force/prune”。

## 4. 最小流程与可证伪验收

### 最小流程

- **未运行**：输入本机有效目录 → 明确“将按原 CCB 以 `--safe` 启动，可能初始化配置并启动配置声明的 Agent” → 提交 → 区分启动过程/真实注册/可用状态。不新增服务器文件浏览器或上传功能。
- **已运行**：真实身份命中 registry → 选择原项目，不 spawn。目录/Agent 标签展示 live 绑定，目录组不是 composer 的另一个目标。
- **失败或 unknown**：已知失败展示有效原诊断；不明确结果保持“不自动重试”，提供只读核对。关闭 dialog、切换项目/Agent期间的迟到结果不能抢走新选择或悄悄再启动。
- **配置**：明确打开原 CCB 配置。保存若要求重启，按原规则下次正常启动生效；当前 Agent/composer/diff scope 不因打开该页面或仅保存而热迁移。

### 阻断级验证与单因素消融建议（此表不是通过结果）

| 验证 | 不变量 / 失败判定 |
| --- | --- |
| 服务端边界 | 无有效 cookie、错误 Host/Origin、文件/无效路径、客户端额外命令参数不得产生 spawn；固定 argv，无 shell 拼接 |
| 别名与并发 | symlink/realpath 并发只启动一次；managed worktree 命中原 project identity，无第二项目/重复启动；不能只验列表长度 |
| unknown 与迟到响应 | 断连/超时/重载不自动再 spawn；只读核对不启动；关闭慢 dialog 后用户选择不被迟到响应覆盖 |
| registry/gateway 一致 | 新项目可经同一真实适配器 view→jobs/native/terminal；不能以 list 可见推导执行授权已接入 |
| 保存但不重启 | live workspace、composer Agent、diff scope 保持原绑定；不能显示“新 worktree 已生效”，原配置诊断仍有出口 |
| 目录组单因素 | 同一 Agent/path 集合，仅分组/平铺改变；比较辨认共享目录与选择目标的误发/耗时，保留全部失败。不同 basename 冲突、未知路径、0/1/多 Agent、中文长路径另做正确性测试 |
| 模态可及性 | dialog/Command 顶层 Esc、Tab、焦点恢复与中文 composition；底层快捷键不能盖过项目打开 dialog或改变其输入 |

## 5. 清理

本轮两次真实调用均结束；工具/MCP禁用、会话不持久化，无自动重试。新增 prompt/raw/answer/meta/runner 是复核证据继续保留；未生成需删除的下载、构建产物或临时浏览器，未改此前两轮材料。实现代码和最终 E2E 的独立审阅另行记录，不借本表宣称通过。
