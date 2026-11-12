# Muxary 方向纠偏与两模型文字评审

- 日期：2026-11-12。
- 基线：`fde3e6d63883b51a33476c88881fb2af19b40874`。
- 关联：[重梳理 SPEC](../specs/muxary-ui-realignment.md)、[既有运行边界](../adr/0001-muxary-product-and-runtime-boundary.md)。
- 状态：**本轮新增真实调用、静态审计与清理核查；不是前端实现、看图评审或浏览器验收。**

## 1. 决策依据

用户撤销独立 Multica 部署，要求删除其进程残留与代码，只参考 T3 Code / Multica 的 UI。两名只读审查代理分别核查 Muxary 内核/现有工作台与官方产品资料；主代理复核既有 ADR、SPEC、实现入口和官方仓库。结论是回归既有边界，不是另起架构：当前 Muxary 已复用 CCB，无须为了桌面式布局引入另一个后端。

既有三栏、项目/目录/Agent、摘要画布、xterm 与组件来源都应复用。下一增量的真实问题是目标、来源、目录及状态的可理解性，不是“再新增一套三栏和项目”。

## 2. 本轮真实 CodeBuddy 调用

两模型分别收到**字节相同**的文字事实与问题，要求寻找错误假设、提出最小实施顺序和验收。调用在私有空目录执行，不加载历史会话、不提供项目工具、不设置真实 Agent 任务；每次超时 180 秒、无重试。

```text
DISABLE_AUTOUPDATER=1 codebuddy-code -p --model <id> --tools '' \
  --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
  --max-turns 1 --no-session-persistence --output-format json
```

| 请求模型 | CLI/provider 报告身份 | wall 秒 | 观察结果 |
|---|---|---:|---|
| `deepseek-v4.1-flash` | `deepseek-v4.1-flash-ioa` | 24.921 | exit 0，success，stderr 为空 |
| `claude-opus-5.5` | `claude-opus-5.5` | 70.624 | exit 0，success，stderr 为空 |

这是 provider 自报身份，不是对权重或路由的独立认证。两次事件类型均为 `message / reasoning / message / result`，没有工具事件；两者自报 `num_turns=3`，虽然 argv 为 `--max-turns 1`，因此仅称**恰好两次 CLI 调用、每模型一次**，不称内部只运行一轮。没有传图、运行产品或性能测试，不把这些答复算作 UI 已验收。

本机私有证据：`~/.local/share/muxary-dev/product-realignment-20261112/model-review/`，包括共同请求、每次 argv/耗时/返回码、原始 JSON/stderr、公开最终答复与身份提取。目录 `0700`、文件 `0600`；原始 JSON 可能含内部 reasoning，不复制到公开仓库。

| 材料 | SHA-256 |
|---|---|
| 共同请求 | `f3e49377f5cdf476fd10648fced7493b3bf1ca8a74cedb46928a768930b928bc` |
| Flash 原始输出 | `6692a104c0f753a894dc8bdc911760e6718bdf311eea4bdfffd7ae06aba9e9a5` |
| Opus 原始输出 | `791bf46d0692ad9b634f684f5b28b6ab488c1b3a5c8b2b660487794a78422321` |
| Flash 公开最终答复 | `634b62a57879fbd2ba57e0da88f65763ce225a54e2a73711f3c00c9b405bd49f` |
| Opus 公开最终答复 | `518e8365a3eca8d98302aa61f81547e076d44c53027ee7c51c3aa6b15c946f3a` |

## 3. 主审综合与不采纳项

采纳的共同方向：

1. 不引入 thread/issue board、Runtime、组织账号或另一套任务状态机。发送仍创建真实 CCB Job，CCB/ccbd 是任务权威。
2. 默认专注、唯一 composer；并行画布次级，重内容与终端按需，最多一个 xterm。
3. 提交前持续可见当前目标；CLI 历史与任务分源；目录 diff 的 tracked/unstaged、共享与归因边界直白表达。
4. 先核既有真实闭环，再改信息层级，不用相似截图替代任务、身份、资源与性能核验。

保留异议，不制造三方全盘共识：

- Flash 的“选绑定目录”只能表示导航/分组，不得变成运行中切换 cwd 的控制器。
- Opus 的“原生历史不增条目”不能当 oracle：任务最终由 CLI 执行，原生日志可能合法增加。应断言 Web 只提交一条目标正确的 CCB 任务，未直接改写历史接口。
- Opus 建议使用 `ccb` 命令查询 Job，但本次未核实具体命令契约；验收应使用现有权威 API/ccbd 存储及明确身份，不编造 CLI 参数。
- 网络中断只证明连接状态，不自动改写已知任务状态为 `unknown`；未确认提交与已知任务进度是不同事实，均不得盲目重发。
- “发送后自动跳至 Job”是候选交互，不是已接受实现。须与阅读连续性、草稿和当前目标测试一起评估。
- 100 是现有摘要节点呈现上限，不是 100 个真实 CLI 的负载保证。`AgentCanvas.tsx` 已有超限提示并引导从项目栏选择其余 Agent，不重复开发另一套降级层，也不因模型提出就当成全新的缺口。

## 4. 清理与原工作区保护

本轮精确移除独立 `multica-local` 的 5 个容器、Compose 网络、4 个专用卷、4 个应用/定制构建镜像，以及 `~/Multica`、私有部署配置/旧部署材料、`multica` / `multica-web` 命令和研究缓存内的 Multica TSX 源码副本。仅将数据库与上传/Redis 数据保留为非运行备份；通用基础镜像和非可执行的 UI 研究记录/图片未当作应用源码删除。

清理后核查：7880 无监听，精确删除路径/旧容器/专用卷/网络均不存在，其他容器状态与原 Muxary 脏工作区清单不变；独立审查再核对一次。可读进程未见 Multica，不声称跨其他用户权限的穷尽取证。未启动已经停止的 Muxary 工作台，8789 仍无监听。

清理清单与结果留在本机 `~/.local/share/muxary-dev/cleanup-20261112T150450/`，数据库/上传数据和部署凭据不入 Git。旧研究中的来源哈希表示当时取得的材料；用户要求删除本机源码副本后，不回写旧记录来抹除历史。

本次需求在独立 docs worktree 处理，原 `feat/explicit-remote-web` 的未提交代码、测试和文档未合入、未回滚。仅新增本报告与 SPEC；做了相对链接/差异检查，没有运行构建、前端测试、真实 CCB 派活或浏览器验收。
