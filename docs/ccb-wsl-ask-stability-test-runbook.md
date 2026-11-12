# CCB WSL Ask Stability Test Runbook

## 1. Document Scope

This runbook is for field-testing CCB `ask` reliability on WSL, especially
issues that are hard to reproduce on normal Linux:

- a delegated job keeps running but never replies
- an empty reply is delivered
- a reply is delivered to the wrong caller
- an old active job blocks new work from entering the target agent
- `ccb clear <agent>` leaves the provider pane unable to answer later asks
- `ask` resolves to a different CCB project because of cwd, workspace binding,
  `--project`, or stale caller environment

This file is an evidence collection runbook. It does not replace:

- `docs/ccb-wsl-compatibility-plan.md`
- `docs/managed-provider-completion-reliability-plan.md`
- `docs/agent-message-timeout-retry-contract.md`
- `docs/ccbd-diagnostics-contract.md`

## 2. Cross-Project Ask Drift Analysis

Current `ask` project resolution is intentionally flexible, but that flexibility
can hide misrouting:

- the CLI can find the nearest ancestor `.ccb` from the current directory
- `.ccb-workspace.json` can bind an external worktree back to a project
- global `--project <path>` can point the command at another project from any
  current directory
- sender inference can consult environment variables such as
  `CCB_CALLER_ACTOR`, `CCB_CALLER_RUNTIME_DIR`, `CODEX_RUNTIME_DIR`, and
  `CCB_SESSION_ID`

This means a shell or provider pane with stale environment can submit to the
wrong project or infer the wrong caller, especially when two projects use the
same agent names.

The safer target rule is:

1. Default `ask` is project-local only.
2. The target daemon must belong to the current cwd's resolved `.ccb` project.
3. Workspace binding is allowed only when it resolves back to the same project
   authority.
4. `ccb --project OTHER ask ...` should be rejected when `OTHER` is not the
   current project, unless a dedicated dangerous cross-project option is used.
5. Cross-project ask should require an explicit absolute project path, for
   example a future option shaped like:

   ```bash
   ccb ask --cross-project /abs/path/to/other/project worker "message"
   ```

6. Cross-project ask should not infer an agent mailbox caller from the source
   project. Until a real cross-daemon bridge exists, it should default to a
   non-agent sender such as `user` or require a separate explicit sender rule.

The WSL tests below intentionally stress the current flexible behavior so that
misrouting evidence is captured before the rule is tightened.

## 3. Test Setup

Use the installed `ccb` release that the WSL user normally runs. Do not test
source changes from the source checkout unless that is the explicit target.

Prepare two CCB projects with the same configured agent names:

- `P1`: Linux filesystem project, for example `~/ccb-wsl-p1`
- `P2`: Windows mounted-drive project, for example `/mnt/c/tmp/ccb-wsl-p2`

Recommended agents:

- `main`
- `coworker`
- `worker`

Run tests from the relevant project root unless a step says otherwise.

Create a log directory:

```bash
export CCB_WSL_DIAG="ccb-wsl-diag-$(date +%Y%m%d-%H%M%S)"
mkdir -p "/tmp/$CCB_WSL_DIAG"
```

Collect the baseline from each project:

```bash
{
  date
  uname -a
  cat /proc/version || true
  pwd -P
  command -v ccb || true
  ccb version || true
  ccb doctor || true
  ccb ping ccbd || true
  ccb ps || true
  ccb queue --detail all || true
} 2>&1 | tee "/tmp/$CCB_WSL_DIAG/00-baseline-$(basename "$PWD").txt"
```

## 4. Baseline Ask

From `P1`:

```bash
command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/01-baseline-ask.txt"
请只回复：CCB_WSL_T1_OK
EOF
```

Expected:

- caller receives `CCB_WSL_T1_OK`
- no empty reply
- no wrong recipient

After the reply or after a visible failure:

```bash
ccb queue --detail all | tee "/tmp/$CCB_WSL_DIAG/01-queue.txt"
ccb ps | tee "/tmp/$CCB_WSL_DIAG/01-ps.txt"
```

## 5. Clear Then Ask

```bash
ccb clear coworker 2>&1 | tee "/tmp/$CCB_WSL_DIAG/02-clear.txt"

command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/02-after-clear-ask.txt"
请只回复：CCB_WSL_T2_AFTER_CLEAR_OK
EOF
```

Expected:

- clear does not break subsequent ask
- the reply still returns to the original caller

If it fails, collect:

```bash
{
  ccb queue --detail all || true
  ccb ps || true
  ccb doctor || true
  ls -la .ccb || true
  find .ccb -maxdepth 2 -name '*session*' -printf '%p %s %TY-%Tm-%Td %TH:%TM:%TS\n' 2>/dev/null || true
} 2>&1 | tee "/tmp/$CCB_WSL_DIAG/02-failure-snapshot.txt"
```

## 6. Clear Loop Pressure

```bash
for i in $(seq 1 10); do
  echo "==== clear-loop $i ===="
  ccb clear coworker || true
  command ask coworker <<EOF
请只回复：CCB_WSL_CLEAR_LOOP_$i
EOF
  sleep 3
done 2>&1 | tee "/tmp/$CCB_WSL_DIAG/03-clear-loop.txt"
```

Expected:

- every iteration eventually returns its matching token
- no agent stays permanently busy
- no reply appears in another agent's mailbox

## 7. Old Job Blocking New Work

Submit a long job:

```bash
command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/04-long-ask.txt"
请执行：bash -lc 'date +%s; sleep 120; date +%s'
完成后只回复：CCB_WSL_LONG_DONE
EOF
```

After five seconds, submit a second job:

```bash
sleep 5
command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/04-second-ask.txt"
请只回复：CCB_WSL_SECOND_AFTER_LONG
EOF
```

Expected:

- the first job is active while it is running
- the second job is queued behind it, not lost
- after the first job completes, the second job runs and replies

Collect:

```bash
ccb queue --detail all | tee "/tmp/$CCB_WSL_DIAG/04-queue-after-second.txt"
ccb ps | tee "/tmp/$CCB_WSL_DIAG/04-ps-after-second.txt"
```

If job ids are visible in command output, save their traces:

```bash
for job in $(grep -ho 'job_[a-zA-Z0-9]*' "/tmp/$CCB_WSL_DIAG"/04-*.txt | sort -u); do
  ccb trace "$job" > "/tmp/$CCB_WSL_DIAG/trace-$job.txt" 2>&1 || true
done
```

## 8. Busy Clear

Submit a long job:

```bash
command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/05-busy-clear-long-ask.txt"
请执行：bash -lc 'date +%s; sleep 60; date +%s'
完成后只回复：CCB_WSL_BUSY_CLEAR_DONE
EOF
```

Clear during the run:

```bash
sleep 5
ccb clear coworker 2>&1 | tee "/tmp/$CCB_WSL_DIAG/05-clear-while-busy.txt"
```

Then verify the agent can still answer:

```bash
command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/05-after-busy-clear-ask.txt"
请只回复：CCB_WSL_AFTER_BUSY_CLEAR_OK
EOF
```

Expected:

- no permanent busy state
- no wrong caller
- no empty reply

## 9. Wrong Caller Detection

Run this from an agent pane, preferably `main`, not from an arbitrary shell:

```bash
command ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/06-from-main-to-coworker.txt"
请只回复：CCB_WSL_FROM_MAIN_TO_COWORKER
EOF
```

Expected:

- reply is delivered back to `main`
- no other agent receives the reply

If the reply goes elsewhere, capture:

```bash
ccb queue --detail all | tee "/tmp/$CCB_WSL_DIAG/06-wrong-caller-queue.txt"
ccb ps | tee "/tmp/$CCB_WSL_DIAG/06-wrong-caller-ps.txt"
```

## 10. Cross-Project Drift

From `P1`, intentionally target `P2` with current global `--project` behavior:

```bash
export P2=/abs/path/to/ccb-wsl-p2

{
  pwd -P
  ccb ping ccbd || true
  ccb --project "$P2" ask coworker <<'EOF'
请只回复：CCB_WSL_CROSS_PROJECT_CURRENT_BEHAVIOR
EOF
} 2>&1 | tee "/tmp/$CCB_WSL_DIAG/07-cross-project-project-flag.txt"
```

Current releases may accept this. If accepted, record it as evidence that ask
can communicate outside the current `.ccb` project.

Now test stale caller environment with same-name agents:

```bash
export P1=/abs/path/to/ccb-wsl-p1
export P2=/abs/path/to/ccb-wsl-p2

env CCB_CALLER_ACTOR=main \
  CODEX_RUNTIME_DIR="$P1/.ccb/agents/main/provider-runtime/codex" \
  ccb --project "$P2" ask coworker <<'EOF' 2>&1 | tee "/tmp/$CCB_WSL_DIAG/07-stale-env-cross-project.txt"
请只回复：CCB_WSL_STALE_ENV_CROSS_PROJECT
EOF
```

Failure signatures:

- reply appears in `P2`'s `main` when the operator expected `P1`
- reply never appears in the original caller
- trace shows a sender that does not match the visible caller
- target agent exists only in the other project

## 11. WSL Runtime And Socket Evidence

Run this inside the mounted-drive project `P2`:

```bash
{
  pwd -P
  ccb ping ccbd || true
  ccb doctor || true
  find .ccb -maxdepth 4 -type s -print || true
  find .ccb -maxdepth 4 -type f \( -name '*.sock' -o -name '*session*' -o -name '*.json' \) \
    -printf '%p %s %TY-%Tm-%Td %TH:%TM:%TS\n' 2>/dev/null || true
} 2>&1 | tee "/tmp/$CCB_WSL_DIAG/08-wsl-runtime-socket.txt"
```

Expected:

- socket/runtime diagnostics should make fallback or relocation visible
- a `/mnt/<drive>` project should not depend on unsupported mounted-drive Unix
  socket behavior

## 12. Failure Snapshot

Before running `ccb kill`, `ccb restart`, or manual tmux cleanup, collect:

```bash
{
  date
  pwd -P
  ccb version || true
  ccb doctor || true
  ccb ping ccbd || true
  ccb ps || true
  ccb queue --detail all || true
  find .ccb -maxdepth 4 -type f \( -name '*session*' -o -name '*.json' -o -name '*.log' \) \
    -printf '%p %s %TY-%Tm-%Td %TH:%TM:%TS\n' 2>/dev/null || true
} 2>&1 | tee "/tmp/$CCB_WSL_DIAG/failure-snapshot.txt"
```

If job ids are known:

```bash
for job in job_xxx job_yyy; do
  ccb trace "$job" > "/tmp/$CCB_WSL_DIAG/trace-$job.txt" 2>&1 || true
done
```

Replace `job_xxx` and `job_yyy` with the real job ids.

## 13. Result Bundle

```bash
tar -C /tmp -czf "/tmp/$CCB_WSL_DIAG.tar.gz" "$CCB_WSL_DIAG"
echo "/tmp/$CCB_WSL_DIAG.tar.gz"
```

Report these fields with the bundle:

- WSL distribution and Windows version
- CCB version
- provider types for `main`, `coworker`, and `worker`
- actual `P1` and `P2` paths
- failed job ids and reply ids
- observed failure category:
  - no reply
  - empty reply
  - wrong caller
  - old job blocked new job
  - clear broke later ask
  - cross-project drift
  - WSL socket/runtime relocation issue
