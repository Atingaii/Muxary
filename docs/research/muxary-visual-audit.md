# Muxary 工作台视觉源与改造依据

- 日期：2026-11-11；Q7 最终确认后使用独立无登录 Chrome（agent-browser/CDP）。
- 当前页面：独立诊断项目运行源码 `ccb config ui --no-open --port 0`；未修改用户配置、未启动用户 Agent。
- 参考：<https://agent-elements.21st.dev/docs/agent-chat>，选取其现成 InputBar/UserMessage/Markdown 交互，而非配套云端 Agent。
- 已捕获并实际打开检查 1440×1000 截图：`~/.local/share/muxary-dev/visual/01-existing-config.png`、`02-agent-elements.png`。

## 1. 原配置页（已捕获，主要设置功能正常）

首屏几乎全部为布局画布和配置项；高频“对话、派活、看进度、查看结果”没有入口。保存、校验、Reload、Activate 等不同阶段按钮同时出现；从截图不能判断激活成功或 Agent 是否接收任务。大块 pane 画布对于配置有意义，但不适合作为日常工作区。

这不是“换个配色”能解决的问题。保留配置页作为次级设置入口，不重写其配置权威及安全激活流程。

## 2. 21st Agent Elements（已捕获，选为聊天局部视觉目标）

现成预览提供克制的白底、细边框、圆角输入区、轻量消息层级和发送/停止区域。适合承载以 Agent 结果为中心的工作区；文档页面的导航、营销按钮和品牌资产不是 Muxary 的复用目标。

采用最小许可明确的源码子集，详见 [来源研究](muxary-ui-source.md)。项目导航与运行上下文在聊天区域外组合；不用 AgentChat 绑定云端或重写任务循环。

## 改造方向与验收

- 左侧为项目和现有 Agent，主区为当前 Agent 的消息与任务输入，右侧任务/上下文可折叠，终端按需展开；设置移到次级。
- 中性浅色、蓝色操作强调，避免满屏仪表盘卡片；字体、边界、间距和焦点统一。窄屏允许收拢导航/上下文。
- 清楚分开 gateway 在线、ccbd 健康、发送、运行中和终态；缺能力用文字说明，不给无作用的“审批”按钮。
- 截图仅证明外观，不证明键盘/IME、焦点、对比度合规、任务完成、重连或审批。上述必须由 DOM、交互与真实控制面联调单独验证。
- 前瞻单因素比较：保持项目/Agent/任务不变，只折叠右侧与终端，验证核心派活/看结果仍可完成；若不能，不保留依赖隐藏面板的关键操作。

以上第 1—2 节保留初次调查事实，不改写为后来的验收。当前实现与独立验证如下。

## 实施后的独立 Chrome 验证

最终选择 AgentChat Basic；两个真实模型与主审的四轮讨论（包含否定 Empty centered 的反例）见[模型评审](muxary-model-design-review.md)。深色/浅色使用中性底色与蓝色强调；有趣设计限于真实任务轨道、可编辑模板和安静的状态指示，而不是假进度或装饰动画。

最终截图位于本机 `~/.local/share/muxary-dev/visual/`：

- `14-muxary-final-desktop.png`：1440px，工作台任务、目标 Agent、固定输入、右栏。
- `15-muxary-native-source.png`：独立原生会话来源；明确标记的合成 Markdown 表格/代码/不安全链接探针。
- `16-muxary-final-mobile.png`：390px，折叠导航/上下文后的任务与输入。
- `08-muxary-dark-diff-confirmed.png`：深色模式与真实 unstaged tracked diff（加来源切换按钮之前的截图）。

390/768/1440px 的 DOM 测量均无横向溢出。Help dialog 实测焦点进入、Shift+Tab 循环、Escape 关闭并归还触发按钮；Ctrl+K 进入搜索。两个独立 stub Agent 经真实 ccbd/tmux 完成派活、刷新不重发、切任务卡不自动发；真实终端输入/输出与重连已观察。模型没有看这些截图、没有执行测试。

面板消融保持项目、Agent、配置不变，只关闭右栏（终端已关闭）：派活完成与结果阅读仍成立。Markdown 探针明确是合成原生记录，不是模型回答；script/onerror 没有执行、javascript 链接无可导航 href，但这不等于完整 XSS/WCAG 审计。

中文 IME 的 composition/Enter/Shift+Enter 有 React 回归测试，未做操作系统输入法人工验收；未做屏幕阅读器、完整 WCAG、首屏性能测试。细节见[验收报告](muxary-validation.md)。
