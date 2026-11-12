# Muxary UI 来源、许可与最小复用记录

- 核查/取得日期：2026-11-11；状态：已完成来源核查、源码适配和构建；集成/浏览器验证分别见 [验收记录](muxary-validation.md)，不由来源核查代替。
- 官方来源：[Agent Elements docs](https://agent-elements.21st.dev/docs)、[安装契约](https://agent-elements.21st.dev/docs/installation)、[官方 GitHub](https://github.com/21st-dev/agent-elements)。仅核验这套官方项目，不把 21st marketplace 任意组件视为同许可。
- 固定源码 commit：[`b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37`](https://github.com/21st-dev/agent-elements/commit/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37)；`git ls-remote ... refs/heads/main` 于本次观察到此值。最初取得阶段仅从该 commit 读取 registry JSON 和 LICENSE；后续集成安装依赖、构建和独立浏览器验证另记。
- 最小范围：`UserMessage` + `Markdown` + `InputBar` + `Suggestions`；没有取得 `AgentChat`、`MessageList` 或其整套 tool renderers。目录：[`web/src/vendor/agent-elements`](../../web/src/vendor/agent-elements)；机器可读完整来源/上游与本地摘要：[`SOURCE.json`](../../web/src/vendor/agent-elements/SOURCE.json)。

## 1. 代码许可与网站条款是两个对象

该固定 commit 的根 [`LICENSE`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/LICENSE) 是 MIT，版权记录为 2026 21st.dev；本地完整保留于 [`vendor LICENSE`](../../web/src/vendor/agent-elements/LICENSE)。其 SHA-256 为 `8bc26817d6b5c323f8cb5e5da77182fe0db8a5ad0e0b563903f9382bba06dc9a`。复用这批代码时保留版权与许可文本；未把原仓库许可证替换为 MIT。

[21st 网站 Terms](https://21st.dev/terms)（页面标记 2026-07-20 更新）另行约束 Marketplace 与 Agents Platform，区分底层组件代码与其 demos/previews/media，且包含采集、再分发和素材使用限制。**本次依据固定 GitHub 源码的 MIT 复用代码，不复制网站布局、截图、品牌素材、预览媒体或 marketplace 元数据；MIT 不是整站素材的授权。** 没有据这些代码许可推断第三方依赖或任意其他 21st 组件的许可。

## 2. 为什么不直接安装 AgentChat

官方文档允许组件独立对接自己的 backend，而完整 Agent SDK 是另外的 runtime 选择。[官方独立使用说明](https://agent-elements.21st.dev/docs#agent-sdk)

固定 [`agent-chat registry`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/agent-chat.json) 声明 21 个 registry dependencies；[`message-list registry`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/message-list.json) 声明 17 个，包括多种工具卡。首期仅需文本消息与输入框，故不引入两者。这里的数字是直接 registry dependency 数，不是 npm 传递依赖数或 bundle 大小。

本次抓取的线上 `agent-chat.json` 与固定 commit 对应文件字节相同，SHA-256 为 `a304d1eccebb594995ec35c805ae54decad1b9615a35e89c6c33f80692dd689f`；`message-list.json` 同样字节相同，SHA-256 为 `d78ed06b069112a74077c636aeac93928a026bd652e60de18b8ec6440b055b4c`。这只证明当次 snapshot 一致，不保证未来 URL 不变；vendor 使用下面的 commit URL，非漂浮网站 registry。

### 所选 registry 闭包（7 items，12 个去重源码/CSS 文件）

| 固定 registry item | 声明 dependencies | 该 JSON 的 SHA-256 |
| --- | --- | --- |
| [`user-message`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/user-message.json) | `@tabler/icons-react`, `ai`, `clsx`, `tailwind-merge` | `d2b8276719846d00337c9a64ad08fda73960bb93263dcc2a4b43011a7220954d` |
| [`file-attachment`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/file-attachment.json) | `@tabler/icons-react`, `clsx`, `tailwind-merge` | `590d8053320b64397aa8370398cb0f9bb01f8ad69607a4148e21ef068e3247d3` |
| [`markdown`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/markdown.json) | `@streamdown/code`, `clsx`, `streamdown`, `tailwind-merge` | `ff64bec79145e0ee3c42bd6ff5bfbd9bb3c589b576b2b26dda586cb937877d3c` |
| [`input-bar`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/input-bar.json) | `@tabler/icons-react`, `ai`, `clsx`, `tailwind-merge` | `6a3df53d56b27ff67c2359006fd705afc7acf9cb8dc7411c62029dfceec7a74a` |
| [`attachment-button`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/attachment-button.json) | `@tabler/icons-react` | `e52b82647501c2a9f556b519e87eda785cd57d3fd37e96f3c6b462696087a33d` |
| [`send-button`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/send-button.json) | `@tabler/icons-react`, `clsx`, `tailwind-merge` | `5c52157639d3a2cc56f59cd351fd25566820babd9345c4a419aeb5874efaafc9` |
| [`suggestions`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/public/r/suggestions.json) | `clsx`, `tailwind-merge` | `67a9aa11a04a37a67bc7357cb2590442e205e4e45bae25e2fdd710a3bc4734aa` |

三项入口的真实源码为 [`user-message.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/user-message.tsx)、[`markdown.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/markdown.tsx)、[`input-bar.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input-bar.tsx)。`Suggestions` 已实际用于三个明确标注的任务模板；附件和问答仍未启用。`InputBar` 仍静态导入 question prompt/input typing，故“7 items/12 files”是**不裁剪上游结构**的最小所选闭包，不是理论最少行数。

[`build-registry.mts`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/scripts/build-registry.mts) 从 `lib/agent-ui` 跟踪本地 imports，改写搬迁后的相对路径并附带 theme CSS。本次保留 registry `target` 下的布局，去掉公共前缀 `components/agent-elements/` 后放在 vendor 目录；**没有再次 flatten `input/`、`question/` 或 `utils/`**。取得阶段三项主文件与固定源码经 `../utils/cn` → `./utils/cn` 变换后比对一致；后续三个本地修改文件见第 5 节。所有本地相对 import 均解析到这 12 个文件。

## 3. 实际依赖成本与 AgentCloud 边界

- 官方安装前提是 Node 18+、React 19+、Tailwind v4 和 shadcn 初始化项目；完整源码站点还用 Next 等，但复制所选源码不是复制整个文档站。[安装要求](https://agent-elements.21st.dev/docs/installation)、[固定 package manifest](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/package.json)
- 所选源码的外部 **runtime imports**：`react`、`react-dom`、`@tabler/icons-react`、`clsx`、`tailwind-merge`、`streamdown`（本地已去掉可选的 `@streamdown/code` 插件）。`ai` 仅以 `import type` 提供 `UIMessage` / `ChatStatus`；registry 仍声明它，不能把类型依赖误称为云调用。[UserMessage 源码](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/user-message.tsx)、[InputBar 源码](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input-bar.tsx)、[Markdown 源码](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/markdown.tsx)
- 上述依赖声明未固定版本。上游站点 manifest 的参考范围为 `ai ^5.0.0`、`@tabler/icons-react ^3.40.0`、`clsx ^2.1.0`、`tailwind-merge ^2.5.0`、`streamdown ^2.5.0`、`@streamdown/code ^1.1.0`；这不是本地 lockfile、兼容性保证或已安装结果。[固定 package manifest](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/package.json)
- 所选闭包没有 `@21st-sdk/*`、`@ai-sdk/react`、`next`、`@base-ui/react`、AgentCloud token/API client 或 backend fetch/WebSocket 调用。`InputBar` 只回调 `onSend`/`onStop`，消息由宿主传入；**不必须接入 AgentCloud，也不要求替换 CCB 调度器**。[所选文件清单](../../web/src/vendor/agent-elements/SOURCE.json)、[官方独立使用说明](https://agent-elements.21st.dev/docs#agent-sdk)
- 这不是“运行时绝不联网”的保证：图片组件可渲染传入 URL，宿主 backend 和 Markdown 的链接/资源策略仍需独立约束。所带 CSS 未发现 `@import` 或 `url(...)` 外链。[UserMessage 源码](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/user-message.tsx)、[theme CSS](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/agent-ui.css)
- 本地依赖已固定精确版本并提交 lockfile；`npm --prefix web ci --ignore-scripts` 干净重装成功。可选 Shiki 插件单因素结果见第 6 节；未测量真实网络首屏或模型响应速度，不宣称“轻量”或运行提速。

## 4. 每文件来源与摘要

下表“上游”指固定 registry `files[].content` 的 UTF-8 SHA-256（搬迁 import 已由上游 builder 改写），而非原始 `lib/agent-ui` 文件字节。来源链接对应原始源码位置；固定 registry JSON 与逐文件关联存于 `SOURCE.json`。`=` 表示本地与该上游内容字节相同。

| vendor 相对路径 / 原始源码 | 上游 registry content SHA-256 | 本地 SHA-256 |
| --- | --- | --- |
| [`agent-ui.css`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/agent-ui.css) | `20817c261c1ff7fca12a8ca93332a27bdcf5def6928fc7e19c2fed398b3ed5f5` | = |
| [`image-lightbox.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/image-lightbox.tsx) | `1534dfbfb40d90c4fc6fbfdee53f94f2cf268bb005e7cd21857546cf7ff4028d` | = |
| [`input-bar.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input-bar.tsx) | `4a85f7da95071a456baaa0be3fe64bcb89f27c1f440d0724341fff96bc8a4ad2` | `6863348a8c3950dc812b48626b95881c7a2334693d9fcb58236fb59487da0414` |
| [`input/attachment-button.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input/attachment-button.tsx) | `dd91d50da400e1881918be0b1a1382badf6e8a6853fa3d58245802a5bb7da47d` | = |
| [`input/file-attachment.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input/file-attachment.tsx) | `8619d5cd4b445d329e8ba706be317148bbae386788538832e610db763cd7a7bd` | = |
| [`input/input-typing.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input/input-typing.tsx) | `b80ebb92bed404d01e783c8a88d5b5dee5798dbe3a3b94bf6fad2793d28f9403` | = |
| [`input/send-button.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input/send-button.tsx) | `a3e59598834e3e854e5b96f1f665391b4a2c2eef4a0e77d5b2464ba1e87293cc` | `21491431cc254c6226ec58ee56e416f74969cba9ef24312c2601d20b39687e99` |
| [`input/suggestions.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/input/suggestions.tsx) | `7364fed98fe743c8b24c6b0a3d650ab08641d5b3e7e11d2b96e7c3fbd762a8eb` | = |
| [`markdown.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/markdown.tsx) | `5774a8ea60ff39ce635d0fff34ad47edf9655f6f6defa3f05942587f16db92ac` | `18bd670316c7a6f85c231c928d58c34a6b0e9635e8138f33619a69d3b2c79562` |
| [`question/question-prompt.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/question/question-prompt.tsx) | `0d5a337ff3f06c3ff2bfafea118f5d5d54b88bd51eeed605cac60b3525f46f37` | = |
| [`user-message.tsx`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/components/user-message.tsx) | `8d3a5fec29a7f6edbf3e6ed87adbcff22306ee8c6e930b8380e0c8b4e65ee471` | = |
| [`utils/cn.ts`](https://github.com/21st-dev/agent-elements/blob/b04b36cb6381a1dd1a0e86cc7c90564ddcd56d37/lib/agent-ui/utils/cn.ts) | `d1f1e0d62cb8d8d1e04c26e14de842d8a151f75812d81b046c65b5d1fe8e4b27` | = |

## 5. 明确的本地修改与验证边界

只修改三个文件，并在源码注释及 `SOURCE.json.local_modifications` 标记：

1. `input-bar.tsx`：中文默认 placeholder/textarea accessible label；使用 composition ref、native `isComposing` 和 Safari IME keyCode 229 阻止选词 Enter 误提交；发送/停止容器改为有中文 accessible name 和 disabled 语义的原生 button；controlled 模式交由宿主在接收回执后清空草稿，拒绝/未知不清空。
2. `input/send-button.tsx`：图形容器改为 `aria-hidden` 的 presentational spans，避免原生 button 内嵌 div。
3. `markdown.tsx`：移除可选全语言 Shiki 插件，保留 Streamdown 普通 Markdown/代码块；不提供语法高亮。

其余 9 个源码/CSS 文件与固定 registry content 字节相同。没有修改工具权限、backend、Job 状态或消息完成判断；UI 的 `ChatStatus` 不是 CCB Job 权威，映射由应用层负责。

已执行：逐 JSON hash 校验、去重文件内容一致性校验、本地相对 imports 存在性校验；从实际 vendored 源码抽出 keydown callback，用 Node 执行 6 个用例：普通 Enter、Shift+Enter、composition ref、native composition、Safari 229、普通字符；结果 6 passed。另断言 composition handlers、语义 button/aria 存在，且 `git diff --check` 通过。

这些是来源/静态检查和纯 callback 测试，**不是 React mount、真实 IME、浏览器或端到端验证**。后续必须由应用构建/typecheck 与浏览器核验中文选词、快捷键、focus、长消息、Markdown/代码、取消/失败重发及链接/图片策略。源码中的图片 lightbox、question prompt 等可选能力也没有因文本发送测试通过而取得验收。

取得阶段未安装依赖或运行浏览器；后续已做 React mount 与浏览器集成。没有复制网站媒体，未提交或推送。LICENSE、SOURCE.json 与上述源码是交付材料。

## 6. 最终原型选择与单因素消融

最终主原型是官方 [AgentChat Basic](https://agent-elements.21st.dev/docs/agent-chat)，不是 Empty centered。两模型第 3 轮指出“空态居中输入”与宿主“输入位置不跳动”冲突，主审接受反例改选 Basic，第 4 轮双方确认。Empty centered + suggestions 仅为空态组合参考；左项目/右任务壳是 CCB 产品适配，不冒称上游整页模板。完整四轮真实 CLI 调用见 [模型评审](muxary-model-design-review.md)。

保持其他源码、CSS、依赖版本、机器与调用不变，仅开/关 `Markdown` 的可选 `@streamdown/code` 插件，各做一次本机 warm-cache build：

| 因素 | 输出文件数 | 全量字节 | 入口 JS 字节 | 入口 JS gzip 字节 | 本机构建秒 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 开启可选 Shiki | 313 | 10,913,374 | 1,332,308 | 382,654 | 3.051 |
| 移除可选 Shiki | 5 | 1,190,973 | 1,138,636 | 321,242 | 1.912 |

仅证明这次构建产物差异，不是运行延迟、首屏、网络或渲染质量基准。插件开启分支临时使用先前已安装包；最终 manifest/lock 删除该依赖，随后干净 `npm ci` 和 build 成功，避免靠残留依赖制造通过。原始测量及固定源码摘要保存于本机 `~/.local/share/muxary-dev/review/bundle-ablation.json`；之后的 reduced-motion 修正不属于该冻结比较。Vite 仍报告大 chunk 和 client-only directive 提示，未调阈值隐藏。
