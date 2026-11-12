# Windows WezTerm Native Open Questions

Date: 2026-06-15

## Product Questions

1. Should the first Windows-native WezTerm version target Windows-only provider
   CLIs, or allow WezTerm GUI on Windows with provider processes inside WSL?
2. Should WezTerm be a user-visible backend option in `.ccb/ccb.config`, or an
   installation/runtime auto-detection choice outside project config?
3. Is the goal full v7 parity, or a reduced Windows-native workbench first
   slice with fewer UI guarantees?

## Technical Questions

1. What is the stable namespace identity for one CCB project in WezTerm:
   `--class`, workspace, tab title, generated config, or a combination?
2. Can WezTerm expose enough pane metadata to replace tmux user options such as
   `@ccb_agent`, `@ccb_project`, and namespace epoch?
3. How should `ccb kill` terminate native Windows provider process trees when
   the pane process spawns children?
4. Does live WezTerm `get-text` provide enough scrollback and screen fidelity
   for `ccb_self` pane diagnostics compared with `tmux capture-pane`?
5. Which provider CLIs are actually stable under native Windows ConPTY when
   driven by `wezterm cli send-text` and `send-key`?
6. Can the sidebar be rendered as a normal WezTerm pane with current Rust
   helper output, or should the Windows native backend use a different UI
   projection?
