# CCB Mobile Agent-Native Conversation Goal

Date: 2026-06-25

## Purpose

Reusable goal prompt for the correction phase: make CCB Mobile ordinary chat
input equivalent to selected-agent pane input, and make the timeline synchronize
with the selected desktop/server agent pane instead of only CCB ask/job history.

## Invocation

Use this prompt when assigning the next cohesive source/app implementation run:

```text
读取并执行
`/home/bfly/yunwei/ccb_source/mobile/docs/plantree/plans/mobile-tmux-control/goal-agent-native-conversation.md`
作为当前长期 goal。

目标：纠正 CCB Mobile 当前聊天路径。手机普通输入必须等同于在当前 selected
agent pane 里直接输入，不走 CCB ask/message 包装，不出现 CCB_REQ_ID，不追加
mobile 标识。手机 timeline 必须成为 selected agent pane 的等价渲染层：
当前电脑端 pane 里的用户输入、agent 回复、可见上下文和向上历史分页需要和手机端
一致。provider-native transcript 和 tmux scrollback 是实现来源；`.ccb/agents/<agent>/jobs.jsonl`
的 CCB ask/job 历史只能是兼容 fallback，不能作为默认聊天流。

必须先 resume plan tree：读取 `docs/plantree/README.md`、
`docs/plantree/plans/mobile-tmux-control/README.md`、
`implementation-status.md`、`roadmap.md`、
`decisions/015-pane-backed-chat-input.md`、
`decisions/016-pane-composer-send-primitive.md`、
`topics/agent-native-conversation-and-input-correction.md`、
`topics/local-real-backend-comprehensive-test-plan.md`，并检查 mobile/source
两个 worktree 的 dirty 状态。

实现边界：
- source 侧优先补 pane-equivalent conversation resolver：从 ProjectView
  解析 selected agent pane，再映射 Codex native transcript，必要时用同一 pane
  的 tmux scrollback/terminal-history fallback；
- source/app 侧把普通 composer send 改成 validated pane input/paste 或等价
  pane-input helper；
- `/agents/{agent}/messages` 只能保留为显式 ask/compat action，不能继续作为
  默认 composer send；
- app timeline 优先 pane-equivalent conversation pages；Comms/content/jobs/
  terminal-history 只做 supplement，且普通聊天 UI 不显示 `mobile_gateway`、
  `completion_snapshot`、job id、request id 等内部来源标签；
- backend agent 生成文件继续通过 authenticated opaque file/artifact ids 下载；
- server-wide project list 仍然作为入口，P0 不允许验证 fake demo。

验收：
- Android Emulator 通过 loopback gateway 打开真实本地 CCB 项目；
- 首页列出服务器上 mounted/reachable 的 CCB projects；
- 选中 test project 和两个 agents；
- 手机发送普通文本后，desktop pane 和 phone timeline 都看到同一条输入；
- provider 回复进入 phone timeline；
- pane/transcript/visible UI 都不出现 CCB_REQ_ID；
- 在电脑端 pane 直接输入的一轮对话，手机端无需重新打开项目即可刷新看到；
- 当 active pane 有更新内容时，旧 `.ccb/agents/<agent>/jobs.jsonl` ask 记录不能作为
  最新聊天覆盖或插入到普通 timeline 顶部；
- 向上滚动能加载旧的 native transcript；
- 图片/文档上传和 backend-generated file 下载仍可用；
- 记录 p50/p95：发送、首个本地可见、首个回复、旧历史加载、渲染、上传、下载；
- 提交 source/app commits，并更新 plan-tree evidence。
```

Short objective:

```text
让 CCB Mobile 普通聊天输入真正成为 selected-agent pane/native input，并在
手机 timeline 同步 selected desktop/server agent pane 的真实对话；用本地 AVD +
真实 CCB project 证明无 CCB_REQ_ID、能收真实回复、能刷新桌面端输入、能加载旧对话
和下载 agent 文件。
```

## Completion Rule

Do not mark this goal complete until a fresh real local AVD run proves the
ordinary mobile composer path no longer creates ask jobs and the selected-agent
timeline is pane-equivalent: current desktop pane turns and phone turns agree,
older pages load in the same conversation order, and `jobs.jsonl` records are
not the default source for ordinary chat.
