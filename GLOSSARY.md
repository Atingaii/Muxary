# Muxary 工作台

这里区分工作台中容易混淆的对象；沿用 CCB 的项目、Agent 与任务用语。

## Language

**Agent**：项目中有名字、使用特定 Provider CLI 的独立执行成员，不等同于模型名称。
_Avoid_：把 DeepSeek/Opus 模型当作两个已挂载的 Agent。

**任务（Job）**：派给一个 Agent、具有独立身份和执行结果的一次工作请求。
_Avoid_：把发送成功、消息或原生会话等同于任务完成。

**接收回执（Receipt）**：控制面已接收某次请求的确认，不是执行结果。
_Avoid_：完成通知。

**原生会话**：Provider CLI 自身的对话与交互上下文，可包含工作台之外的交互。
_Avoid_：把它当成完整的 CCB 任务档案。

**项目（Project）**：CCB 的稳定项目身份及原项目根目录。managed worktree 回映该身份，不因输入工作树路径创建第二个项目。

**Agent 工作目录（workspace）**：CCB 声明/启动绑定给 Agent 的目录。可以是共享主目录或 worktree；不是每条消息可选择的 cwd，不保证永久进程 cwd 或文件隔离。

**画布卡片**：现有 Agent 的摘要呈现；布局、选择与过滤不改变原 pane、任务或目录绑定。
