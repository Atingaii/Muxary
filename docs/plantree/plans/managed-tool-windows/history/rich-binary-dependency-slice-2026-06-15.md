# Rich Binary Dependency Slice - 2026-06-15

## Scope

Harden `ccb update rich` so rich dependencies are binary-first where practical,
with package-manager fallback only when required.

## Changes

- Added CCB-owned Yazi/ya release download into
  `$XDG_DATA_HOME/ccb/tools/workbench/bin`.
- Preferred official Linux `unknown-linux-musl` Yazi assets before GNU assets
  to avoid glibc drift on older stable distributions.
- Added executable validation for downloaded `yazi --version` and
  `ya --version` before marking bundled binaries usable.
- Removed invalid CCB-owned Yazi/ya binaries when validation fails so normal
  dependency detection can fall back to system binaries or package managers.
- Added binary install status fields to rich doctor/update output.
- Made rich command detection prefer the CCB workbench `bin` directory before
  system `PATH`.
- Added WSL launch routing that prefers Windows-native `wezterm.exe` and starts
  rich commands through `wsl.exe --cd "$PWD" -- env ...`.

## Validation

Commands:

```bash
python -m py_compile lib/cli/tools_runtime/workbench.py
pytest -q test/test_cli_tools_workbench.py
/home/bfly/yunwei/ccb_source/ccb_test --diagnose
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test update rich
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/test_ccb2/source_home/.local/share/ccb/tools/workbench/bin/yazi --version
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/test_ccb2/source_home/.local/share/ccb/tools/workbench/bin/ya --version
```

Observed:

- Workbench unit tests passed.
- Source-wrapper diagnostics confirmed `/home/bfly/yunwei/test_ccb2` is the
  allowed external source validation project.
- Initial GNU Yazi validation failed on the host with a `GLIBC_2.39`
  requirement.
- After switching Linux preference to musl, `ccb_test update rich` installed
  `yazi-x86_64-unknown-linux-musl.zip`.
- `yazi --version` reported `Yazi 26.5.6`.
- `ya --version` reported `Ya 26.5.6`.

The remaining `workbench_status: degraded` in the live update output came from
the current outer `tmux` terminal image-passthrough warning, not from the rich
bundle dependency install.
