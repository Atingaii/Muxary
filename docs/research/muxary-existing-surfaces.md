# Muxary Web 工作台：CCB 现有能力事实核查

- 调查日期：2026-11-11。
- 源码基线：`df98e61e91b4be57873029b01667135e6265f371`（8.7.22）。
- 调查位置：`feat/codebuddy-cli-compat` 工作区；存在未提交的 CodeBuddy 适配修改，不将其视作基线已发布能力。
- 范围：本地源码、现有测试和工具可用性；未启动网关、安装依赖或发送真实模型请求。
- 状态：**研究证据，可交付；不代表新产品范围、前端技术选型或实现方案已接受。**

## 入口与技术栈

| 入口 | 源码证据 | 能力边界 |
| --- | --- | --- |
| 配置 Web 页 | [`assets/config_ui/index.html`](../../assets/config_ui/index.html)、[`lib/cli/services/config_ui.py`](../../lib/cli/services/config_ui.py) 的 `prepare_config_ui` / `_handler_for` | 单文件 HTML/CSS/JavaScript，直接 `fetch`；Python `ThreadingHTTPServer`，loopback、query token、闲置退出。不是完整桌面工作台。 |
| 移动客户端 | [`mobile/app/pubspec.yaml`](../../mobile/app/pubspec.yaml)、[`mobile/README.md`](../../mobile/README.md) | Flutter/Dart、Riverpod、xterm、Markdown；有 Android/iOS 工程，没有 `mobile/app/web`。 |
| 移动传输层 | [`http_gateway_transport.dart`](../../mobile/app/lib/transport/http_gateway_transport.dart)、[`gateway_mobile_ccb_repository.dart`](../../mobile/app/lib/repository/gateway_mobile_ccb_repository.dart) | 直接依赖 `dart:io`；现有源码不能直接按浏览器客户端构建。 |
| 移动网关 | [`lib/mobile_gateway/service.py`](../../lib/mobile_gateway/service.py) 的 `build_mobile_gateway_server` | Python 标准库 HTTP JSON、SSE、WebSocket；Relay 使用 `aiohttp`。 |
| Agent 控制面 | [`lib/ccbd/app_runtime/handlers.py`](../../lib/ccbd/app_runtime/handlers.py)、[`control_plane_transport/unix.py`](../../lib/ccbd/control_plane_transport/unix.py) | 已有本地 socket RPC，不是现成浏览器 REST API。 |
| 存储与包装 | [`lib/jobs/store.py`](../../lib/jobs/store.py)、[`lib/storage/paths_agents.py`](../../lib/storage/paths_agents.py)、[`package.json`](../../package.json) | Job/Event 等使用 JSONL；npm 工程是 CLI 安装/启动包装，不是 React/Vite 前端工程。 |

## 可复用能力与缺口

以下 `/v1` 路由由 [`lib/mobile_gateway/service.py`](../../lib/mobile_gateway/service.py) 的 `dispatch_get` / `dispatch_post` 等实现。

| 领域 | 已有能力 | 不应泛化的部分 |
| --- | --- | --- |
| 项目与 Agent | `/v1/projects`、`/v1/projects/{id}/view`、`focus-agent`、`focus-window`；[`project_view/service.py`](../../lib/ccbd/project_view/service.py) 投影 namespace、windows、agents、active/queued jobs、通讯摘要。 | 项目发现不等于创建工作区、Git clone、worktree 管理。 |
| 任务 | RPC 已有 `submit/get/watch/queue/cancel/retry/resubmit/followup/trace`；见 [`handlers.py`](../../lib/ccbd/app_runtime/handlers.py) 及 [`lib/ccbd/handlers`](../../lib/ccbd/handlers)。 | 网关没有对应完整 Job HTTP API。不得绕过现有 dispatcher 另造任务状态权威。 |
| 消息 | `/v1/projects/{id}/agents/{agent}/messages`，`_submit_agent_message`。 | 普通 Agent 走 pane-native input，回执 `job_id=None`、`state=sent`；frontdesk 走 Job，OMP Collab 有专用 FIFO。`sent` 不证明模型接收，更不证明完成。 |
| 对话与历史 | `/conversation`、结构化内容、部分 Provider 的 native history 与分页。 | `_agent_native_conversation_items` 仅有 Codex、Claude、Pi、OMP 分支。工作区新增的 CodeBuddy reader 尚未接入该移动历史路径。没有统一任意历史会话浏览、切换、分支 API。 |
| 终端 | [`terminal.py`](../../lib/mobile_gateway/terminal.py)：pane terminal、独立 host shell；WS input/paste/resize、序号与恢复游标。 | Agent terminal 使用桌面源 geometry，不任意改变桌面布局；独立 host terminal 的 resize 语义不同。 |
| 附件 | `dispatch_file_upload` / `dispatch_file_download`，认证上传下载。 | 不是文件树、编辑器或 Git diff API；当前默认上传上限 25 MiB、下载 128 MiB。 |
| 模型设置 | `/provider-control`、`/provider-quota`；namespace、revision、idempotency fences。 | configured/pending/active native 值不同，能力受 Provider 约束。 |
| 交互与审批 | OMP `/ui-response`，`_respond_agent_ui`；[`ui_request_card.dart`](../../mobile/app/lib/features/agent_chat/ui_request_card.dart)。项目命令信任见 [`project_command_trust.py`](../../lib/project_command_trust.py)。 | OMP select/editor 问题不是全 Provider tool approval。配置自定义命令批准不是每次工具执行批准。 |
| 生命周期 | `/lifecycle`，`_project_lifecycle` 支持 `wake/open/close/stop`。 | `wake/open` 返回运行项目视图，不启动冷项目；`close` 只关闭移动视图；不能据动作名称推断暂停或冷启动能力。 |
| 实时通知 | `/v1/mobile/notifications` SSE、失效通知、恢复游标；[`notifications.py`](../../lib/mobile_gateway/notifications.py)、[`activity_watch.py`](../../lib/mobile_gateway/activity_watch.py)。 | 不等于完整 Job 事件流；事件应保留来源和完成权威。 |

## 浏览器与身份边界

- 网关当前没有桌面静态页面服务，也未实现 CORS/`OPTIONS`；跨域 Bearer 请求不能直接照搬移动客户端。需验证 same-origin 边界，不以全局放开 CORS 替代契约。
- `handle_terminal_websocket` 使用第一条 `open` frame 中的 terminal token 认证，浏览器无需自定义 WS header；令牌撤销、输入序号与恢复游标应保留。相关源码：[`service.py`](../../lib/mobile_gateway/service.py)、[`pairing.py`](../../lib/mobile_gateway/pairing.py)。
- 配对和 scope 是设备控制模型，不是多用户、组织或租户 RBAC。配置页 query token 也不能原封不动扩展为公网管理身份。
- [`docs/mobile-cloudflare-alpha.zh.md`](../mobile-cloudflare-alpha.zh.md) 的 loopback-only 描述存在滞后；当前 `parse_listen_address(..., allow_lan=True)` 可接受明确私网地址。源码和对应测试应作为当前事实依据。
- 根 [`package.json`](../../package.json) 声明 `AGPL-3.0-only`；产品交付需保留明确的来源及许可证记录。

## 已验证与可运行命令

本次仅收集以下测试，结果 **393 tests collected**，不是 393 passed；未执行这些测试或真实外部联通验证：

```bash
cd ~/claude_codex_bridge
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  --collect-only -q -p no:cacheprovider \
  test/test_config_ui.py \
  test/test_mobile_gateway_service.py \
  test/test_mobile_gateway_terminal.py \
  test/test_mobile_gateway_omp_collab.py \
  test/test_v2_ccbd_dispatcher.py \
  test/test_v2_job_store.py \
  test/test_project_command_trust.py
```

移除 `--collect-only` 可运行对应回归。其他现成覆盖包括 `test/test_mobile_gateway_notifications.py`、`test/test_mobile_gateway_activity_watch.py`、`test/test_mobile_gateway_relay*.py`。调查时 `mobile/app/test` 有 118 个 `*_test.dart` 文件，`mobile/app/integration_test` 包含终端、重连、撤销和附件 smoke tests；文件数量不是通过数量。

以下是现有入口命令，**本次未执行**；服务命令应在已有 CCB 项目中使用：

```bash
ccb config ui --no-open --port 0
ccb mobile serve --listen 127.0.0.1:8787

# 已有 Flutter SDK 时
cd mobile/app
flutter test
flutter analyze
```

调查环境：`.venv` 可导入 pytest、aiohttp、cryptography，PATH 可找到 tmux/node/npm；**未找到 flutter/dart**。未安装大型依赖。

## 未来 Web contract 的验证重点（未实施）

1. **`sent ≠ completed`**：分别验证 pane 输入发送、native admission、Job 终态；user/tool/terminal echo、pre-tool commentary、其他 generation 均不得制造完成。只保留输入成功证据时，UI 必须保持未确认或处理中。
2. **冷项目**：在 ccbd 停止、项目未挂载、注册记录失效时分别验证 list/open/wake；不得将缓存视图或 HTTP 200 当作成功启动。若新增冷启动，需独立、可观测的契约和失败结果。
3. **cross-provider 能力**：覆盖 native history、队列、审批、模型切换分别支持与不支持的 Provider；缺能力应显式 unavailable，不得用 pane 文本或 OMP 专用协议静默伪装通用支持。
4. **same-origin**：实际浏览器验证静态页、API、SSE、WS 的 origin/认证组合；加入错误 origin、过期/撤销 token、断线恢复的反例。不能因移动端 HTTP 测试通过就声称浏览器契约通过。

上述验证按单因素隔离：保留其他条件，分别去除 native 完成证据、改变 generation、切换 Provider 能力、改变 origin，观察对应 gate 是否拒绝；不以更早的拒绝证明下游 gate 已生效。
