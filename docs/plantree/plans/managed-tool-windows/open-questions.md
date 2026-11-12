# Managed Tool Windows Open Questions

Date: 2026-05-30

## Questions

- Should the first command contract be a single shell command string only, or
  should it also support an argv array before the feature ships?
- When a tool command exits, should CCB leave the pane open, restart it, or show
  an exited marker until explicit reload/restart?
- Should command changes be blocked until a future explicit `tool restart`
  policy exists, or should they be treated as remove-and-add when the old tool
  pane is idle/exited?
- Which clipboard lane should be the standard fallback inside tmux when the OS
  clipboard helper is missing: Neovim OSC52, tmux `set-clipboard`, or explicit
  platform helper installation?
- Should inline image rendering attempt automatically when terminal support is
  detected, or should it require an explicit command/keymap even when
  `snacks.image` reports support?
- On WSL, should external file/URL opening prefer `wslview`, Windows interop
  tools such as `explorer.exe`, or Linux desktop tools when more than one is
  present?
- What user-facing command or config flag should opt into browser-based
  Markdown preview once Node/browser/opener diagnostics are available?
- If parser readiness fails on a platform, should CCB enable Markview as an
  automatic fallback or only report Markdown rendering as degraded?
- Should the rich workbench opt-in be expressed as a global
  `[tools.workbench].profile = "rich"` setting, per-tool profile settings, or
  `tool_windows.<name>.profile = "rich"`?
- Should CCB offer WezTerm installation/provisioning directly, or should doctor
  recommend WezTerm while leaving installation to the user on each platform?
- In the rich workbench bundle, should WezTerm be a required component for
  `--profile rich`, or should the bundle support a degraded external-terminal
  mode when WezTerm is missing?
- Should `ccb-yazi-rich` show a visible degraded banner when it automatically
  falls back to the safe Yazi profile because terminal image checks fail?
- How should expensive PDF/video preview limits be configured so rich previews
  do not block large-project browsing?
- On partial bundle install failure, should CCB roll back generated profiles
  automatically or keep a disabled manifest for doctor/repair?
- How should GUI terminal close behavior be hardened beyond the first-slice
  recorded PID close path on Linux, macOS, and WSL?
- Should additional workbench aliases beyond `rich` be added, such as separate
  `files`, `edit`, or `monitor` aliases, or should `rich` remain the only
  reserved layout alias?
