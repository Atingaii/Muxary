# ADR-0004：独立 Muxary 提交历史，保留 CCB 来源与许可

- 状态：**已接受；2026-11-12 用户明确确认备份后重建远端 main**。执行结果独立记录，不将决定当作已完成证明。
- 范围：Git 提交身份、默认分支历史、上游来源与备份；不改变产品运行时、会话或工作目录。

## 背景与选择

旧 Muxary `origin/main@0cd8bfea2e9e28b8cf5f373809329bcb3e100473` 有 2027 个可达提交（含 tip），包含 CCB 的历史；两个 Muxary 自身提交又继承本机全局 `lucentzhou` 身份。用户希望自己的仓库只呈现 Muxary 提交，作者为 `Atingaii`。GitHub 当前认证账号核对为 `Atingaii`（ID `227715769`）。

保留 fork 祖先便于普通 merge/rebase 上游，但不能满足独立提交链；仅 squash 最新两个提交也不会去掉 CCB 祖先。选择从已交付 Muxary 的完整源码树建立无父 root，再保留其文档交付与后续 UI 增量。不编辑旧 commit 对象，也不把原 CCB 源码的版权改成自己的。

## 执行约束

1. 先备份全部旧 refs/历史到本机 Git bundle，并验证 bundle 完整性；冻结远端 refs 以便 compare-and-swap。
2. 仅本仓库配置 `user.name=Atingaii`、`user.email=227715769+Atingaii@users.noreply.github.com`；不改全局配置，不公开使用个人邮箱。
3. 新 root 的完整树对应原 Muxary 功能提交；下一提交对应原验证文档树；本轮 UI 增量为后续提交。树身份、作者、父链和远端结果分别核验。
4. 保留 CCB 原许可证、版权、NOTICE、固定上游 SHA 和历史测试记录。新提交作者表示提交行为，不表示独自创作所有导入源码。
5. `upstream` 仍指向官方 CCB，旧历史留在本机备份。远端 `main` 及旧 Muxary 功能分支改指独立历史，不推送上游历史或本机上游 tags。
6. 只在本轮验证结束后使用精确旧 SHA 的 `--force-with-lease`；并发远端更新则停止重议，不能无条件 force 覆盖。新 UI 需求分支指向相同独立后继。

## 结果与代价

这是仓库身份整理，不是清除来源或修复 GitHub 贡献缓存的承诺。旧 URL、clone 与 PR 可能仍引用旧 SHA；本机 bundle 和真实历史文档保留这些身份。不会反写旧冻结证据，使它们看似基于新 SHA 运行。

以后核对 `git rev-list --count main`，不能用包含 `upstream`/备份 refs 的 `--all` 计数来判断独立历史是否成功。同步 CCB 时采用明确基线的差异移植并记录来源；不能再将整个上游历史 merge 进独立 main，否则会重新引入用户要求排除的祖先。恢复旧远端同样需要明确确认及 lease 检查，不作为静默 fallback。

执行身份、树映射、备份指纹及新提交数见[本轮交付验证](../research/muxary-ui-refinement-validation.md)。
