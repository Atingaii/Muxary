# ADR-0002：同源本机 Web 边界，不建立第二任务权威

- 状态：accepted，2026-11-11。

Muxary 使用现有 MobileGateway/CcbdClient 与 ccbd 的项目、派活、取消、重试和原生终端能力，在 Python 本机服务中增加同源静态 SPA/HTTP/WS 边界。SQLite 仅保留幂等请求指纹和回执，不保存任务正文或重新调度任务；完成结果仍来自 ccbd terminal decision。由此避免 UI 刷新、网络超时或重新连接制造第二份任务事实。

## 为什么不是普通聊天 API 或另一套 Agent SDK

“请求已发出但回执丢失”时，自动重发可能产生两个真实任务；因此保留 pending，显示 unknown，由用户核对，不能以失败颜色替代不确定性。同一动作重放复用该动作自己的稳定幂等键并重新核查归属；重试创建新 job，不是继续旧的 in-flight 请求；完成先赢的竞态不得被取消覆盖。任务档案只展示现有 queue/view 能定位的记录，明确不是永久完整历史。

复用 UI 不等于复用运行内核。最终选择 [21st AgentChat Basic](https://agent-elements.21st.dev/docs/agent-chat) 的 InputBar/UserMessage/Markdown/Suggestions 子集；不引入 AgentCloud、整套工具渲染依赖或新调度器。三方真实讨论曾提出 Empty centered，但与固定输入位置冲突，已据反例改选 Basic。许可、固定 commit 与可选 Shiki 单因素消融见 [来源记录](../research/muxary-ui-source.md)。

## 身份边界与后果

工作台只监听 loopback；一次性 URL fragment token 换取按服务端口区分的 HttpOnly/SameSite cookie，所有 HTTP 检查精确 Host，mutation 与 WS 还要求同源 Origin；只读 GET 可不带 Origin。fragment 不进入服务器日志，幂等表不存 prompt。该边界不防同一 OS 用户的恶意进程，不提供团队权限或公网身份体系。安全远程方案仍沿用既有 CCB 能力，不能直接把这个本机监听开放到公网。

终端直连原 pane，尺寸以实际源栅格为准，不为适配浏览器强行 resize 共享 Agent。原生 trust/login/审批交互需要在终端完成；没有统一审批按钮，不假称每个 Provider 都有等价能力。Web 与 CLI 共用原配置和会话格式，保留 `ccb` 兼容入口。详见 [SPEC](../specs/muxary-workbench.md) 与 [独立验收](../research/muxary-validation.md)。
