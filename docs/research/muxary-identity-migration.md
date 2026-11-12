# Muxary 身份迁移研究

- 日期：2026-11-11。
- 状态：**Research / not accepted ADR**。下文区分源码事实、建议与未决事项；底层身份迁移方案未接受，也没有实施迁移。
- 源码基线：`df98e61e91b4be57873029b01667135e6265f371`，版本 `8.7.22`（[`VERSION`](../../VERSION)、[`package.json:2-3`](../../package.json#L2-L3)）。调查工作区为 `feat/codebuddy-cli-compat`，包含未提交的 CodeBuddy 扩展；这些扩展不是上游已发布能力。
- 本次范围：本地只读源码核验及本文落盘；没有改代码、remote、提交、安装或发布，没有新增网络请求。相邻的 Web 能力研究见 [`muxary-existing-surfaces.md`](muxary-existing-surfaces.md)。
- 协调者转交的用户已确认约束：本地使用；基于 CCB 的 Codex/Claude 桌面式 Web 工作台；公众品牌 Muxary、主命令 `muxary` 并兼容 `ccb`。这些不是未决产品方向；兼容入口的安装与隔离方式尚未决定。

## 1. 仓库身份与远端观察的边界

本地 `git remote -v` 的 `origin` fetch/push 均为 `https://github.com/SeemSeam/claude_codex_bridge.git`，不是 Muxary。根包的 homepage、repository、bugs 也指向 SeemSeam 仓库；包声明许可证为 `AGPL-3.0-only`。这些来源和许可证记录不能被新品牌文案代替。[`package.json:5-13`](../../package.json#L5-L13)

任务协调者转交的已执行观察如下，本次没有重复联网：

```text
git ls-remote --symref https://github.com/Atingaii/Muxary.git
exit status: 0
advertised refs: none
```

这只证明在**当时环境、凭证与网络条件下**可以取得 Git ref advertisement，且没有广告分支或 tag。它不证明公开可见、拥有 push 权限、仓库元数据为空，也不证明与源项目具有 GitHub Fork 关系。匿名 GitHub API 请求遇到 rate limit，因而没有取得可用于确认 `private`、`size`、权限或 fork 关系的元数据。本文将该地址称为**拟用仓库**，不称“已 fork”。这一段来源是协调者记录的命令结果，不是从本地源码推导出的远端事实。

## 2. 首要问题：分发与更新不是同一个身份

**事实：当前基线已有不一致。** npm 名称是 `@seemseam/ccb`，包元数据指向 SeemSeam；npm 安装器默认从 SeemSeam 的 `releases/download/v${version}` 下载。但版本查询的 commit API、tags API、`REPO_URL` 三项仍指向 `bfly123/claude_code_bridge`。[`package.json:2-13`](../../package.json#L2-L13)、[`ccb-npm-install.js:266-269`](../../bin/ccb-npm-install.js#L266-L269)、[`versioning_runtime/constants.py:4-6`](../../lib/cli/management_runtime/versioning_runtime/constants.py#L4-L6)

**建议，P0：** 在 fork 首次交付前统一“包命名空间—下载 release—版本查询—更新目标—发布 workflow”的归属，先于纯品牌替换。只改 README 或 Git remote 不会改变这些硬编码行为；也不能把现有 SeemSeam 下载成功当成 Muxary release 已被验证。

更新归属有既存的严格约束，不应为了改名删掉它：

- npm runner 从自身 `package.json` 写入 `CCB_INSTALL_KIND`、包名、根目录和版本，再启动实际 release。[`ccb-npm-runner.js:7-26`](../../bin/ccb-npm-runner.js#L7-L26)
- Python 固定认可 `@seemseam/ccb`，要求包名/版本匹配 manifest，执行位置必须在该包的 `.ccb-release` 下；更新命令也使用此固定包名。改 npm 名称时需同步修改这些边界及其测试，而非放宽为任意环境变量声明。[`install.py:19-73`](../../lib/cli/management_runtime/install.py#L19-L73)
- 下载器要求 artifact 出现在 `SHA256SUMS` 中并核对摘要；解包后还要求 `ccb` executable 存在。改 artifact 或主命令时，安装器和发布产物必须一起验证。[`ccb-npm-install.js:274-291`](../../bin/ccb-npm-install.js#L274-L291)

## 3. 按外部契约分层，不做全局替换

| 层次 | 已核实的当前契约 | 建议边界（未接受） |
| --- | --- | --- |
| 公众品牌与入口 | npm 公开 `ccb`、`ask`、`autonew`、`ctx-transfer`；不是只有一个主命令。[`package.json:35-55`](../../package.json#L35-L55) | 按已确认的 Muxary/`muxary` 加 `ccb` 兼容目标，列清委派命令、help、文档、安装 URL 与兼容入口的外部契约，再改。 |
| 分发与更新 | npm 包、GitHub release、Python 更新器和 provenance 校验跨 JS/Python/workflow 关联，见上一节。 | 作为一个可验证迁移切片，使用新身份的真实产物验证，不混用源项目 release。 |
| 全局持久化与进程所有权 | 默认安装 `~/.local/share/codex-dual`；bin 为 `~/.local/bin`；roles/tools 在 XDG data home 的 `ccb` 下。[`install.sh:4-7`](../../install.sh#L4-L7)、[`install.sh:179-200`](../../install.sh#L179-L200) | 若允许与原 CCB 共存，fork 默认应有独立安装、state、data、socket 及清理所有权。仅改展示名字不足以隔离。 |
| 项目锚点 | 项目路径仍是 `.ccb/ccb.config`；运行 state 默认在 `$XDG_STATE_HOME/ccb/projects` 或 `~/.local/state/ccb/projects`，可显式设置 `CCB_RUNTIME_STATE_HOME`。[`paths_ccbd.py:15-30`](../../lib/storage/paths_ccbd.py#L15-L30)、[`path_helpers.py:93-124`](../../lib/storage/path_helpers.py#L93-L124) | 保留 `.ccb` 可降低导入成本，但必须明确一个项目只能由一个管理者维护；若需同项目并行管理，应决定新项目 namespace/所有权，不能默许共写。 |
| 内部兼容协议 | `CCB_REQ_ID`、`CCB_BEGIN`、`CCB_DONE` 是匹配协议；session payload 使用 `ccb_session_id`，调用者环境使用 `CCB_CALLER_*`/`CCB_SESSION_ID`。[`protocol constants:6-23`](../../lib/provider_core/protocol_runtime/constants.py#L6-L23)、[`session_files.py:68-75`](../../lib/cli/services/runtime_launch_runtime/session_files.py#L68-L75)、[`caller_env.py:73-88`](../../lib/provider_core/caller_env.py#L73-L88) | 公众品牌改变并不要求 wire marker 或保存字段改名。初期可保留，只有明确互操作边界要求时才设计版本化迁移。 |
| 内部模块与 helper | Python 包导出 `CcbdApp`/`CcbdClient`，Rust crate 名为 `ccb-runtime-accelerator`。[`ccbd/__init__.py:3-18`](../../lib/ccbd/__init__.py#L3-L18)、[`Cargo.toml:1-5`](../../rust/crates/ccb-runtime-accelerator/Cargo.toml#L1-L5) | 内部实现名称可保留；不能因字符串命中而要求整体重命名。 |

### 共存中的具体反例

1. **全局可执行文件冲突。** 安装器按脚本 basename 安装到 `BIN_DIR`，并对已安装入口做 `ccb`/`ask` smoke；其 executable 安装分支会清理目的路径，移除既有文件或链接。因此另发 `ccb`/`ask` 全局兼容别名存在覆盖原入口的风险，不能默认宣称无冲突共存。[`install.sh:1984-1992`](../../install.sh#L1984-L1992)、[`install.sh:2045-2058`](../../install.sh#L2045-L2058)、[`install.sh:2456-2492`](../../install.sh#L2456-L2492)
2. **清理目标也属于迁移边界。** 旧 Neovim 清理代码会处理 `$data_home/ccb/tools/neovim`、`$state_home/ccb/tools/neovim` 和 `ccb-nvim` 链接；fork 沿用路径可能触及原安装的材料。迁移应核查 install/update/uninstall/cleanup 全链路，而非只看新建目录。[`install.sh:3474-3493`](../../install.sh#L3474-L3493)
3. **tmux 不是 session 名换皮。** runtime socket root 含 `ccb-runtime`；tmux backend 接受 `CCB_TMUX_SOCKET_PATH` / `CCB_TMUX_SOCKET`，未指定 socket 时可以使用默认 tmux server。需要明确 server/socket 和 lifecycle 所有权，不能只把 `ccb-*` session 名改成 `muxary-*`。[`path_helpers.py:69-85`](../../lib/storage/path_helpers.py#L69-L85)、[`tmux_backend.py:49-62`](../../lib/terminal_runtime/tmux_backend.py#L49-L62)、[`tmux.py:29-34`](../../lib/terminal_runtime/tmux.py#L29-L34)

### Skills 是可执行契约

继承的 ask skill 明确执行裸 `command ask`；clear/compact skill 执行 `command ccb clear` / `command ccb compact`。所以“仅发布 `muxary` 主命令，其他不动”会留下指向旧入口的委派与控制指令。[`ask/SKILL.md:76-88`](../../inherit_skills/claude_skills/ask/SKILL.md#L76-L88)、[`ccb-clear/SKILL.md:14-25`](../../inherit_skills/claude_skills/ccb-clear/SKILL.md#L14-L25)、[`ccb-compact/SKILL.md:12-23`](../../inherit_skills/claude_skills/ccb-compact/SKILL.md#L12-L23)

**建议：** 把“重写技能中的明确命令”“新名字的委派入口”“受管理私有 PATH shim”“用户显式选择全局兼容别名”作为待比较方案。选择前验证调用究竟落到哪个安装及 generation；不要用占用原有全局 `ccb`/`ask` 名称来隐藏兼容问题。

## 4. 当前 release 绑定了移动端，不能假定是纯 CLI/Web fork

Android job 要求 keystore secret，并使用 store/key password 与 alias；缺少 keystore 会显式失败。发布 manifest 还含 `io.ccb.mobile.ccb_mobile`、`CCB Mobile`、SeemSeam 下载 URL 和 `ccb update mobile`。这些不是只修改桌面名称便会同步迁移的字段。[`release-artifacts.yml:115-157`](../../.github/workflows/release-artifacts.yml#L115-L157)、[`release-artifacts.yml:197-217`](../../.github/workflows/release-artifacts.yml#L197-L217)

release publish job 依赖 CLI build 与 mobile-android，检查 Linux/macOS tar、APK、版本 JSON、latest JSON，生成校验和并上传。npm workflow 也等待 CLI tar 与 mobile APK/JSON，smoke 使用固定包目录和 `ccb`，最后执行带 provenance 的 npm publish。[`release-artifacts.yml:233-286`](../../.github/workflows/release-artifacts.yml#L233-L286)、[`npm-publish.yml:55-89`](../../.github/workflows/npm-publish.yml#L55-L89)、[`npm-publish.yml:105-144`](../../.github/workflows/npm-publish.yml#L105-L144)

**建议：** 若新产品首期仅 CLI/Web，应明确建立独立 release 合同及资格范围，保留对应 artifact、checksum、版本、provenance 和运行 smoke。移动发布另作显式范围决定；不能删除缺 secret 的 gate 后声称原本完整 release 已通过，也不能把移动失败归因为 CLI 核心不工作。

## 5. 未决事项

1. 拟用 GitHub 仓库的实际权限、可见性、与上游的 fork/镜像关系，以及默认分支；当前远端观察不足以回答。
2. npm scope/包名是否可用且由谁拥有；`ask` 等委派入口如何分发；已确认的 `ccb` 兼容入口如何避免覆盖原版，是否承诺全局共存。
3. 是否支持原项目 `.ccb/ccb.config` 就地打开、一次性导入还是并行管理；旧数据如何只读识别，谁有迁移/清理权。
4. 是否接受独立全局 state/data/tmux socket；原有 `CCB_*` 环境变量作为兼容输入保留多久，优先级如何定义。
5. CLI/Web 和移动端是否同版本、同 release、同分发资格；移动包身份、签名和历史升级路径由谁维护。
6. 首次 fork 版本号、上游归属与差异记录如何呈现；内部 marker/module 名称没有必要随公众品牌一起改。

这些问题尚未拍板。本文不把新增配置层、兼容层或迁移框架视作已选方案。

## 6. 前瞻验证与消融（尚未执行）

以下用隔离 HOME、XDG 目录、安装前缀和临时 registry/release fixture 进行，保留原安装与用户数据不动。每个用例只改变一个因素，必须让样本到达要验证的 gate；不能以更早的拒绝证明下游机制有效。

| 决策/机制 | 单因素反例或消融 | 应观察的结果 |
| --- | --- | --- |
| 下载/更新同源 | 仅将版本查询、release URL 或 npm 包名之一改回源项目，其他 fixture 有效 | 独立断言最终下载、查询、更新目标；错误身份不能被 checksum 正确掩盖。 |
| 下载校验 | 同一正确 release fixture，仅改 artifact 内容或移除其 checksum 条目 | 对应 checksum gate 拒绝；再用有效校验和进入解包与 executable smoke，分别证明后续 gate。 |
| npm provenance | 保持有效 manifest/路径，只改包名、版本、执行根目录或继承环境中的一个 | 非所属安装不得取得更新权；正确新身份必须通过完整正例。不得放宽 gate 制造通过。 |
| 共存/清理 | 原 CCB 与 fork 各自有效安装；仅切换 PATH 顺序、项目管理者或 socket | 命令指向可观测，state/data/process 不串写；更新/卸载一方不修改另一方。 |
| skill 入口 | 仅移除 `ccb`/`ask` 兼容入口，保持未改写 skill | 应暴露缺入口或错误归属；然后分别验证所选新命令或私有 shim，不能只验证主命令 help。 |
| 内部协议保留 | 只改公众品牌，保留原 marker/session 字段 | 既存 request/completion/caller 测试保持含义；新增端到端断言，避免仅以字符串替换量衡量完成。 |
| CLI/移动范围 | 分别缺 CLI artifact、缺移动 secret、缺移动 artifact；其他输入有效 | 各资格结果独立归因。若正式拆分，验证新 CLI 合同而不宣称未运行的移动合同通过。 |

## 7. 本次核验记录与限制

本地执行 `git branch --show-current`、`git log -1`、`git remote -v`、读取 `VERSION`，并按文件逐项读取上述源码。针对**基线 HEAD 的 tracked 内容**执行：

```bash
for d in lib bin tools config inherit_skills test; do
  printf '%s ' "$d"
  git grep -i -l ccb HEAD -- "$d" | wc -l
done
```

结果为 `lib=736`、`bin=25`、`tools=16`、`config=11`、`inherit_skills=46`、`test=459`。这是 case-insensitive `ccb` 命中的文件数，仅说明影响面广；它既不是修改清单，也不说明每个命中都需要改名。本次没有执行改名测试、完整构建、发布验证或权限确认；上述验证表是前瞻计划，不是已通过结果。
