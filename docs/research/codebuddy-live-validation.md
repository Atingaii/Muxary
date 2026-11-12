# CodeBuddy 原生适配实测

状态：2026-11-11 本机 Linux 单版本联通证据，不是全部平台或权限模式保证。

## 条件与可观察结果

- Muxary `0.1.0` 开发源码；原生 CodeBuddy CLI `2.183.0`，模型为账户已有的 `claude-opus-5.5`。
- 两个专用临时项目、私有 HOME/XDG、独立项目 tmux socket；不在用户 HOME 项目中发送任务。使用 `ccb --safe`，启动参数为 `--permission-mode default`，没有跳过权限检查。
- 任务只要求回复测试标识，不调用工具、不修改业务文件。原生 JSONL 未观察到这些任务的模型工具调用；项目根没有创建 `.ccb` 以外的业务文件。
- 不以 `clear_status/compact_status: ok` 或终端空闲作为完成证据。每个成功 ask 同时检查 CCB trace 已持久化回复、精确原生 user anchor、原生 assistant `status=completed` 和匹配的 `CCB_DONE`。

| 验证 | 观察 |
| --- | --- |
| 首次 ask | `job_4f58b08a667d` 完成，返回 `LIVE_ASK_OK`，`codebuddy_done_marker` / `exact`。 |
| 原生 `/clear` | SessionStart sidecar 将 UUID 从 `967d627c-315a-49ec-a9fd-d234c46fb2aa` 更新为 `01a1c9cd-2c80-7179-9e6f-dc30c711a38c`。随后 `job_7ddbc669f122` 返回 `LIVE_AFTER_CLEAR_OK`，精确完成。 |
| 原生 `/compact` | 终端独立出现 `Conversation compacted` / `Compacted`；同一精确 JSONL 新增 `cmp_cc1707b3-66b2-4ce9-bc53-50de234cf8af` 用户消息，内容以 `<cb_summary>` 开头。随后新请求以该压缩节点为父节点；`job_4a5ee98e5943` 返回 `LIVE_AFTER_COMPACT_OK`，精确完成。不能仅凭 UUID 没变推断压缩成功。 |
| 原生 resume | 停止并重新启动项目，命令实际包含 `--resume 01a1c9cd-2c80-7179-9e6f-dc30c711a38c`，状态为 `exact_session_selected`；新的 launch UUID 为 `1716325a-588c-4325-8469-c9fbb2afcc7b`，sidecar generation 匹配。`job_1590886ff9c5` 返回 `LIVE_AFTER_RESUME_OK`，精确完成。 |

## 暴露的问题及修复

1. `.codebuddy/.credentials.json` 只是 MCP OAuth 来源，不足以恢复本机原生账号登录。实际默认产品账号位于 Linux HOME 的 `.local/share/CodeBuddyExtension/Data/Public/auth/Tencent-Cloud.coding-copilot.info`。适配器现在受 `inherit_auth` 控制，只单向复制当前账号文件或注销 marker，权限 `0600`，不复制备份、IDE 历史或整个共享数据树。源账号及三个源配置文件前后 SHA 检查未变；未将凭据正文写入报告或仓库。原生账号刷新只写私有副本。
2. 私有 HOME 不能阻止原生 CLI 更新共享 npm 二进制。验证期间版本从初查 `2.178.0` 变为 `2.183.0`；没有执行全局 npm 安装或更新，且另有原生 CLI 并发运行，无法归因到某一进程。managed launcher 现固定 `DISABLE_AUTOUPDATER=1`，真实进程环境已观察到该值；拒绝会重新启用更新的 `settings.env.DISABLE_AUTOUPDATER`，不静默绕过配置冲突。`NO_UPDATE_NOTIFIER` 不是该 CLI 的禁更新开关。
3. native trust/login 交互没有被自动接受。只手动选择当前临时项目的 `Trust folder only`。临时危险目录重启后再次要求 trust；一次过早提交的 `job_e05350eac6e0` 没进入 JSONL，停止项目后如实为 `incomplete/project_shutdown`，没有算成通过。确认 trust、原生恢复界面及新 generation sidecar 后的新 ask 才成功。SessionStart 绑定本身不代表所有原生 UI 交互已完成。

## 自动化反例与界限

上面的真实模型调用早于最终启动预检加固。后续仅用合成配置复跑启动边界，未再次调用模型冒称相同冻结版本的联通证据。

- launcher/storage 定向 `113 passed`：包括真实 shell 环境优先级、关闭 API 继承不泄漏 ambient/settings.env 凭据、冲突 hook policy 拒绝、继承账号开关对照、私有 inode/权限、注销 marker 和目录别名隔离、自更新配置反例。
- source/managed-venv installer 与 provider 注册表定向 `98 passed`，在没有 ambient `CCB_PYTHON` 的环境运行。源安装缺少已构建 Web 资产时，在安装副作用前明确失败；新主入口缺失继续 fail-closed。
- 插件缓存不复制，继承的插件/MCP 配置不等于已经验证其可用；这次原生启动有五个继承 MCP 服务失败。未据此宣称插件/MCP、全部 Agent 工具、Windows/macOS 或自定义产品账号储存完全兼容。
- 最终启动预检按原生 `--setting-sources` 选取 user/project/local 与 CLI 配置，拒绝会覆盖受管 HOME/XDG/config/caller identity 的 env。已启用磁盘来源目前只支持**严格 JSON**；原生支持的 JSONC 注释/尾逗号会明确拒绝，不吞成空配置、不修改文件。启动后由同 OS 用户改写并动态 reload 的配置仍有 TOCTOU，不是持续沙箱。
- 关闭 `inherit_auth/config` 只停止外部继承，不撤销已存在的私有副本，不等于 logout。日志按 append-only writer 假设读取；inode 变化或观察到 size<offset 可检测，不能检测两次 poll 间同 inode 截断并重长至旧 offset 以上的任意重写。
- `no_wrap` 仍明确不支持；没有原生 terminal hook 时不伪造精确完成。原生会话可 resume，不代表被中断的 CCB job 能无重复地续跑。

脱敏 trace、压缩界面与结构化证据留在本机 `~/.local/share/muxary-dev/review/codebuddy-*`；私有凭据和原生完整对话不纳入仓库。验证结束后只停止、清理此次临时项目，不清理用户会话或既有依赖。

## CLI 命令身份补充（提交前静态核实）

2026-11-11 只读检查本机安装包 `@tencent-ai/codebuddy-code` **2.183.0** 的 `package.json`：`bin.codebuddy-code` 和 `bin.codebuddy` 均声明为 `./bin/codebuddy`，本机两个可执行 symlink 也指向该同一文件。因此本适配器默认的 `codebuddy` 与设计评审使用的 `codebuddy-code` 在这份已核安装中不是不同 CLI，也不是为测试临时创建的别名。仍可用 `CODEBUDDY_START_CMD` 指定其他命令。此项仅核实当前包的命令声明及本机解析，不推断其他版本、分发渠道或平台具有相同别名，不新增一次模型联通验证。
