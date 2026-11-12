# Muxary 源码安装与回滚

状态：0.1.0 开发源码；不是已发布的 npm 包或 GitHub 二进制 release。
Muxary 基于 `SeemSeam/claude_codex_bridge` 8.7.22，保留原作者署名及 AGPL-3.0-only 许可证。内部 `ccb` 协议、项目状态与兼容入口没有全量改名。

## 首选：源码 / 独立 CLI 目录

需要 Bash 3.2+、Python 3.10+、tmux、Node/npm（构建 Web）、Rust/Cargo（构建原生 helper）。Python 3.10 还需要 `tomli`。各 Agent 的原生 CLI 与登录凭据分别准备；安装 Muxary 不会替用户开通模型服务。`install-cli` 自动构建 sidebar 与 rs-helper；可选 runtime accelerator 不由该路径自动构建。需要运行依赖 accelerator 的测试时，先执行 `bin/build-ccb-runtime-accelerator`，不要将本机复用官方 ELF 的记录当作干净 checkout 已自动具备此产物。

```bash
cd /path/to/Muxary
python3 -m venv .venv
.venv/bin/python -m pip install -r deploy/mobile-relay/requirements.txt
.venv/bin/python -m pip install 'tomli>=2; python_version < "3.11"'
npm --prefix web ci
npm --prefix web run build

# 独立目录，不覆盖原 npm ccb，也不修改全局 Agent、shell、tmux 配置。
MUXARY_INSTALL_PREFIX="$HOME/.local/share/muxary" \
MUXARY_BIN_DIR="$HOME/.local/share/muxary/bin" \
CCB_PYTHON_BIN="$PWD/.venv/bin/python" \
CCB_INSTALL_ROLES=0 \
bash ./install.sh install-cli

# 仅对本终端启用；先确认解析到自己的源码安装目录。
export PATH="$HOME/.local/share/muxary/bin:$PATH"
command -v muxary ccb
muxary --version
ccb --print-version
muxary --project /path/to/project
```

源码安装首先检查 `assets/workbench/index.html`；未构建时在安装副作用前失败，并提示上述 Web 构建命令。

`install-cli` 复用已有依赖检查、原生 helper 构建、运行时安装及入口自检，不投影全局 skills、commands、权限、shell profile 或 tmux 配置。入口自检可能初始化空的 `~/.ccb/logs/comm.log`（运行日志，不是配置投影）。源码安装入口固定到当前 checkout 的 Python/body，因此移动或删除 checkout / venv 后必须重新安装。安装入口显式允许源码运行，直接运行 checkout 的 `ccb` 仍保留其诊断目录限制。

也可不安装入口，直接运行：

```bash
CCB_PYTHON="$PWD/.venv/bin/python" ./muxary --project /path/to/project
```

`muxary` 默认打开本机 Web，绑定 `127.0.0.1` 随机端口；`--no-open` 只打印本机登录 URL。已有项目注册表可复用；冷项目仍通过原 `ccb --safe` 启动，不新增调度器，不默认绕过模型权限。`muxary tui [CCB_ARGS...]` 进入旧 TUI；`ccb` 默认行为不变。

## 完整投影安装

`bash ./install.sh install` 还会写入当前 HOME 的 CCB 兼容 skills/commands、Claude 权限、tmux 与 shell PATH，并清理旧 CCB 注入/MCP。它不是单纯复制二进制。已有安装并存时优先选上面的 `install-cli`。完整安装前应备份将被修改的 bin 入口、shell/tmux 文件和各 Agent 配置；备份中可能包含凭据，应保留原访问权限。

`MUXARY_INSTALL_PREFIX` / `MUXARY_BIN_DIR` 是新入口；旧 `CODEX_INSTALL_PREFIX` / `CODEX_BIN_DIR` 仅作为未设置新变量时的兼容回退。

## 更新身份

版本来源为本仓库 `VERSION` / package metadata。更新器只查询 `Atingaii/Muxary` 的发布信息和包身份；fork 无可用 release 时明确报告无可用发布并提示源码安装，不回退下载官方 CCB。源码更新先审查和拉取本 fork，再重建 Web 并重跑 `install-cli`；不要求 npm scope 已发布。

## 回滚

采用独立目录 `install-cli` 时：关闭本次 Web 服务、停止仅属于本次测试/项目的 Agent，然后在新终端移除上述 PATH 前置，或恢复安装前 PATH。原 npm `ccb` 包及原全局配置仍在。用 `command -v ccb` 和 `ccb --print-version` 确认回到了原入口。仅在确认独立目录没有用户数据且不再需要后，再移除它；源码 checkout 与项目 `.ccb` 数据不必删除。

入口/PATH 回滚不恢复共享项目 `.ccb`、registry 或会话状态；这些格式继续由 CCB 管理。两套版本不要同时管理同一个项目。已添加 CodeBuddy 的项目配置不保证能被上游 8.7.22 识别，恢复配置需使用相应项目的备份，不能靠换入口推断状态已回退。

不要把 `install.sh uninstall` 当作并存安装的自动回滚：现有卸载流程会删除所选 prefix 和兼容 bin，并清理全局 CCB skills/权限/tmux 内容，尚无逐文件归属恢复。完整投影安装应按预先备份逐项恢复，而不是假定卸载能够恢复旧版本。

## 验证证据边界

隔离 HOME、XDG、tmux socket 的本机完整源码安装及不依赖 ambient `CCB_PYTHON` 的 `muxary` / `ccb` / `ask` 入口已验证。当前机器没有 Rust 编译器，本机联调三个 helper（`ccb-rs-helper`、`ccb-agent-sidebar`、`ccb-runtime-accelerator`）复用既有官方 8.7.22 Linux 安装二进制，所对应 helper 源码未修改；这不是 Muxary 新发布构建证据。独立的可重现 release / npm / Windows / 移动端发布仍各自需要验收。


## 本机已执行的可逆切换（2026-11-11）

初版受影响回归 **1505 passed** 后，已创建以下六个受管 symlink（创建前均不存在）：

```text
~/.local/bin/{muxary,ccb,ask,autonew,ctx-transfer,codex-reconnect}
  -> ~/.local/share/muxary/bin/<same-name>
```

新 login shell 已验证解析；当前终端可先 `hash -r`。`muxary` 默认 Web，`muxary tui` / `ccb` 仍为原 TUI 行为。已运行的 daemon 保持原进程，不强制重启已有 Agent；后续正常重启项目时才加载新后端。官方 npm **8.7.22** 保留，完整包、原配置及入口清单备份位于 `~/.local/share/ccb-backups/20261111-muxary-cutover`（外层 0700，manifest 0600）。

此安装固定依赖 `~/Muxary` 和 `~/claude_codex_bridge/.venv/bin/python`，不要移动或删除；如需换到独立 venv，应先重跑安装再验证。当时尚未 commit/push；后续源码提交与扩展验收见[最终记录](research/muxary-expansion-validation.md)。未发布npm，也未替换原全局 Agent 配置。

Q9扩展后的再次只读复核：新login shell启动 `muxary --no-open` 成功；静态200、未认证API401、bootstrap只可用一次、会话cookie为HttpOnly/SameSite Strict，原HOME两Agent可读取，没有发Job，原配置SHA不变，关闭Web退出0。该复核不重启已有Agent，不当作新CodeBuddy模型调用或跨平台安装证据。

只回滚本次入口（先关闭本次 Web；若 symlink 已由你改动则跳过，不删其他文件）：

```bash
for name in muxary ccb ask autonew ctx-transfer codex-reconnect; do
  entry="$HOME/.local/bin/$name"
  expected="$HOME/.local/share/muxary/bin/$name"
  if [ -L "$entry" ] && [ "$(readlink "$entry")" = "$expected" ]; then
    rm -- "$entry"
  fi
done
hash -r
command -v ccb
ccb --print-version
```

这只恢复命令解析，不回滚共享项目状态；无需运行 `uninstall`，也不删除源码、依赖或备份。
