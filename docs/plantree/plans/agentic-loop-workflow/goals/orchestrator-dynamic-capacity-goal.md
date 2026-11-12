# Goal: Orchestrator Dynamic Capacity End-To-End

Date: 2026-06-24

## Supersession Note

This goal records the first landed dynamic-capacity substrate. The current
preferred workflow design is now topology-driven: `orchestrator` proposes a
runtime workflow graph, `ccb loop topology` commits desired state, and a
reconciler uses capacity/lifecycle/layout mechanisms to load, release, park,
or reflow agents. See
[../topics/runtime-workflow-graph-and-reconciler.md](../topics/runtime-workflow-graph-and-reconciler.md)
and
[../decisions/014-runtime-workflow-graph-reconciler.md](../decisions/014-runtime-workflow-graph-reconciler.md).

## Objective

Land the first working orchestrator dynamic-capacity loop:

1. `.ccb/ccb.config` can declare `loop.role_profiles`.
2. `agentroles.ccb_orchestrator` includes an `orchestrator-capacity` skill.
3. `orchestrator` can use the skill to load a temporary
   `worker + code_reviewer` execution pair.
4. `orchestrator` can assign work to the temporary pair, collect results, and
   release the pair after the loop round.
5. The whole path is proven in the external source-test project
   `/home/bfly/yunwei/test_ccb2` with `/home/bfly/yunwei/ccb_source/ccb_test`.

This is an implementation and test goal. It must not be marked complete until
the real source-test folder flow passes without using the globally installed
`ccb`.

## Current Progress

Implemented first slice in the current worktree:

- `loop.capacity` and `loop.role_profiles` are represented on
  `ProjectConfig.loop_capacity`.
- Config loading accepts, validates, records, and renders profile policy.
- Profile validation covers unknown fields, installed role lookup, provider
  model shortcut compatibility, thinking-level enum, workspace-group boundary,
  max-node bounds, and name-template validity.
- The authoritative config contract now documents `[loop.capacity]` and
  `[loop.role_profiles.*]`.

Implemented second slice in the current worktree:

- `ccb loop capacity ensure/status/release` is parsed as a normal phase2 CLI
  command.
- JSON mode is implemented for script and skill use.
- `ensure` resolves configured `loop.role_profiles`, validates counts against
  `max_nodes` and per-profile `max_instances`, produces deterministic planned
  agent names, and writes loop capacity state.
- `status` reads the stored loop capacity state without needing current config
  reparse.
- `release --idle-only` marks planned loop-owned agents released and writes an
  event record.
- State is stored under `PathLayout.runtime_state_root / runtime / loops`, so
  normal projects use `.ccb/runtime/loops/<loop-id>/...` while relocated WSL
  runtime roots remain inside the existing storage boundary.

Implemented third slice in the current worktree:

- Active `capacity.json` records are merged into `load_project_config` through
  a CCB-owned runtime overlay.
- User-authored `.ccb/ccb.config` is not rewritten.
- `config validate`, startup, and guarded reload see active loop agents while a
  loop state is `ensured`.
- `release --idle-only` marks generated agents released, after which config
  loading no longer includes them.
- If a daemon is mounted, `ensure` and `release` try to apply the overlay change
  through the existing guarded `ccb reload` path.
- If no daemon is mounted, `ensure` records `apply_status =
  deferred_until_start`, so the next start can materialize the dynamic agents.
- Reload failure rolls the loop capacity state back instead of leaving a broken
  active overlay.

Implemented fourth slice in the current worktree:

- Draft RolePack `agentroles.ccb_orchestrator` is materialized under
  `drafts/agentroles.ccb_orchestrator`.
- The draft includes CCB adapter memory and the private
  `orchestrator-capacity` skill.
- The skill allows only `ccb loop capacity ensure/status/release --json`,
  uses returned names as ask targets, and forbids raw reload, raw kill, tmux,
  provider process mutation, direct config edits, and direct runtime-file
  writes.
- Templates for capacity request, worker ask, and checker ask are included for
  loop-runner handoff.
- Focused RolePack tests prove manifest translation, skill command boundary,
  and projection into a managed Codex home.

Implemented fifth slice in the current worktree:

- `release --idle-only` now checks mounted runtime state before removing
  loop-owned agents.
- Busy, starting, stopping, or queued generated agents are retained and kept in
  the active overlay.
- Idle generated agents are released independently.
- A later release after the retained agent becomes idle releases the remaining
  agent and clears retained diagnostics.

Implemented sixth slice in the current worktree:

- `ccb loop run-once --loop-id <id> --task <text> [--json]` is implemented as
  the first deterministic loop-runner slice.
- The command requests one `worker` and one `code_reviewer` from
  `loop.role_profiles`, uses returned generated names as ask targets, watches
  worker/reviewer/orchestrator jobs to terminal state, then releases idle
  generated agents.
- It writes formal loop artifacts under
  `.ccb/runtime/loops/<loop-id>/`: `round.json`, `asks.jsonl`,
  `events.jsonl`, `breadcrumb.md`, and `artifacts/{worker,reviewer,aggregate}-reply.md`.
- The command is treated as a control-plane command requiring an existing CCB
  project anchor. It does not bootstrap a default `.ccb` when run in the wrong
  directory.
- After capacity is live, execution or release failures are surfaced in
  `round.json` as `failure` or `release_error`, `loop_run_status` becomes
  non-ok, and the loop runner still attempts `release --idle-only`.

Implemented repeat autonomous smoke hardening:

- `scripts/orchestrator_capacity_semantic_smoke.py` supports
  `--run-autonomous --repeat <n>`.
- Each repeat round submits a fresh ask to the real `orchestrator`, lets the
  orchestrator autonomously ensure `worker + code_reviewer`, dispatch callback
  asks, release idle capacity, and report final pass evidence.
- The watcher follows callback continuation chains and stops immediately when
  the terminal reply includes `AUTONOMOUS_LOOP_STATUS`, instead of waiting for
  a nonexistent next callback.
- Repeat rounds keep a stable loop id and verify the actual goal: repeated
  hot ensure, ask dispatch, callback resume, idle release, and return to the
  durable orchestrator-only graph.

Still not implemented:

- full workflow state-machine runner beyond the bounded `run-once` slice;
- fully daemon-side transient capacity ownership after the V1 runtime overlay;
- isolated `source-home` real-provider auth seeding. The guarded real-provider
  harness can run with `provider-home-mode = real-home`; using the isolated
  `source-home` without copied Codex auth correctly leaves Codex at the login
  screen.

Last verified:

```bash
python -m pytest test/test_v2_config_loader.py -q
python -m pytest test/test_agents_layout_runtime.py -q
python -m pytest test/test_loop_capacity_cli.py -q
python -m pytest test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py -q
python -m pytest test/test_ccbd_reload_dry_run.py test/test_ccbd_reload_drain.py -q
python -m pytest test/test_orchestrator_rolepack.py test/test_loop_capacity_cli.py test/test_v2_config_loader.py test/test_agents_layout_runtime.py test/test_ccbd_reload_dry_run.py test/test_ccbd_reload_drain.py test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py -q
python -m pytest test/test_orchestrator_capacity_semantic_smoke_script.py test/test_orchestrator_rolepack.py test/test_loop_capacity_cli.py test/test_v2_config_loader.py test/test_agents_layout_runtime.py test/test_ccbd_reload_dry_run.py test/test_ccbd_reload_drain.py test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py -q
git diff --check -- lib/agents test/test_v2_config_loader.py docs/ccb-config-layout-contract.md docs/plantree/plans/agentic-loop-workflow
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke/roles \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke config validate
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke/roles \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke loop capacity ensure --loop-id round1 --profile worker=1 --profile code_reviewer=1 --json
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke/roles \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke loop capacity status --loop-id round1 --json
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke/roles \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke loop capacity release --loop-id round1 --idle-only --json
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-runtime-smoke/roles \
CCB_NO_ATTACH=1 \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-runtime-smoke
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-runtime-smoke/roles \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-runtime-smoke loop run-once --loop-id s5 --task 'run once smoke: worker summarizes task, reviewer checks it, orchestrator aggregates result' --timeout 30 --json
python /home/bfly/yunwei/ccb_source/scripts/orchestrator_capacity_semantic_smoke.py --test-root /home/bfly/yunwei/test_ccb2 --project-name orchestrator-capacity-real-provider-smoke --provider codex --prepare-only --json
CCB_ORCH_SMOKE_RUN_REAL=1 \
python /home/bfly/yunwei/ccb_source/scripts/orchestrator_capacity_semantic_smoke.py --test-root /home/bfly/yunwei/test_ccb2 --project-name orchestrator-capacity-real-provider-smoke --provider codex --provider-home-mode source-home --loop-id rp1 --task 'For this CCB smoke, reply exactly with status: done and one short evidence line.' --timeout 180 --reset --run --json
CCB_ORCH_SMOKE_RUN_REAL=1 \
python /home/bfly/yunwei/ccb_source/scripts/orchestrator_capacity_semantic_smoke.py --test-root /home/bfly/yunwei/test_ccb2 --project-name orchestrator-capacity-realhome-smoke --provider codex --provider-home-mode real-home --loop-id rp1 --task 'For this CCB smoke, reply exactly with status: done and one short evidence line.' --timeout 180 --reset --run --json
CCB_ORCH_SMOKE_RUN_REAL=1 \
python /home/bfly/yunwei/ccb_source/scripts/orchestrator_capacity_semantic_smoke.py --test-root /home/bfly/yunwei/test_ccb2 --project-name orchestrator-capacity-autonomous-smoke --provider codex --provider-home-mode real-home --loop-id auto2 --task 'Autonomous smoke: dynamically request one worker and one code_reviewer, ask the worker for a status: done reply, ask the reviewer to verify it, release idle capacity, then report final pass evidence.' --timeout 420 --reset --run-autonomous --json
CCB_ORCH_SMOKE_RUN_REAL=1 \
python /home/bfly/yunwei/ccb_source/scripts/orchestrator_capacity_semantic_smoke.py --test-root /home/bfly/yunwei/test_ccb2 --project-name orchestrator-capacity-autonomous-repeat-smoke --provider codex --provider-home-mode real-home --loop-id rep --task 'Autonomous repeat smoke: for each round dynamically request one worker and one code_reviewer, ask the worker for status: done, ask the reviewer to verify it, release idle capacity, and report pass evidence.' --timeout 600 --repeat 3 --reset --run-autonomous --json
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
AGENT_ROLES_STORE=/home/bfly/yunwei/test_ccb2/orchestrator-capacity-real-provider-smoke/roles \
/home/bfly/yunwei/ccb_source/ccb_test --project /home/bfly/yunwei/test_ccb2/orchestrator-capacity-real-provider-smoke config validate
```

Results on 2026-06-24:

- `test/test_v2_config_loader.py`: `100 passed`
- `test/test_agents_layout_runtime.py`: `11 passed`
- `test/test_loop_capacity_cli.py`: `3 passed`
- `test/test_orchestrator_capacity_semantic_smoke_script.py
  test/test_orchestrator_rolepack.py test/test_loop_capacity_cli.py`:
  `17 passed`
- `test/test_v2_cli_router.py test/test_v2_cli_context.py test/test_v2_cli_render.py`:
  `111 passed`
- `test/test_ccbd_reload_dry_run.py test/test_ccbd_reload_drain.py`:
  `35 passed`
- Broad relevant regression after `loop run-once` wiring:
  `265 passed`.
- `git diff --check`: passed
- External source-wrapper state smoke in
  `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-state-smoke`: config
  validate passed; `ensure/status/release` returned JSON; active `ensure`
  made `config validate` report `loop-round1-worker-1` and
  `loop-round1-code_reviewer-1`; `release` removed those dynamic agents from
  `config validate`; final state is `released`; event order includes
  `ensure, release`.
- RolePack and runtime verification after the fourth/fifth slices:
  `python -m pytest test/test_orchestrator_rolepack.py
  test/test_loop_capacity_cli.py test/test_v2_config_loader.py
  test/test_agents_layout_runtime.py test/test_ccbd_reload_dry_run.py
  test/test_ccbd_reload_drain.py test/test_v2_cli_router.py
  test/test_v2_cli_context.py test/test_v2_cli_render.py -q` passed with
  `253 passed`.
- `git diff --check` passed for the touched docs, config, CLI, agent, and test
  paths.
- External mounted-daemon smoke in
  `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-runtime-smoke` with
  isolated `HOME`, `CCB_SOURCE_HOME`, and `AGENT_ROLES_STORE`:
  - project started with only `orchestrator`;
  - `ensure --loop-id s1 --profile worker=1 --profile code_reviewer=1 --json`
    returned `apply_status = applied`, `plan_class = add_agent`;
  - `ps` showed generated `ls1-worker-1` and `ls1-code_reviewer-1`;
  - CCB `ask/watch` completed worker, reviewer, and orchestrator aggregation
    jobs on the generated targets;
  - `release --idle-only` returned `apply_status = applied`, `plan_class =
    remove_agent`, and removed generated agents;
  - restart after release mounted only `orchestrator`, proving generated agents
    did not become durable config.
- External busy-retain smoke:
  - `ensure --loop-id s4` mounted `ls4-worker-1` and
    `ls4-code_reviewer-1`;
  - a long fake-provider worker job made `ps` report
    `ls4-worker-1 state=busy queue=1`;
  - first `release --idle-only` retained `ls4-worker-1` and released the idle
    reviewer;
  - `config validate` showed only `ls4-worker-1` plus `orchestrator`;
  - after `watch` reached terminal, second release removed the retained
    worker; final `ps` and `config validate` showed only `orchestrator`;
  - final `kill -f` unmounted the smoke daemon.
- External deterministic run-once smoke on 2026-06-25 Asia/Shanghai:
  - `ccb_test --diagnose` confirmed the source wrapper and external test root;
  - project started with `CCB_NO_ATTACH=1` and only `orchestrator`;
  - `loop run-once --loop-id s5 --task ... --timeout 30 --json` returned
    `loop_run_status = ok`;
  - capacity ensure applied guarded reload `add_agent` and generated
    `ls5-worker-1` plus `ls5-code_reviewer-1`;
  - worker, reviewer, and orchestrator aggregation jobs all completed;
  - release applied guarded reload `remove_agent`, `released_count = 2`, and
    `retained_count = 0`;
  - post-run `ps` showed only `orchestrator state=idle`;
  - `.ccb/runtime/loops/s5/asks.jsonl` has three ask records;
  - `.ccb/runtime/loops/s5/events.jsonl` has loop start, capacity, ask
    terminal, and finish events;
  - `breadcrumb.md` reached `Phase: done`;
  - `artifacts/worker-reply.md`, `artifacts/reviewer-reply.md`, and
    `artifacts/aggregate-reply.md` were written;
  - final `kill -f` unmounted the smoke daemon.
- External deterministic run-once smoke after failure-evidence hardening:
  - project started with `CCB_NO_ATTACH=1` and only `orchestrator`;
  - `loop run-once --loop-id s6 --task 'run once smoke after
    failure-evidence hardening' --timeout 30 --json` returned
    `loop_run_status = ok`;
  - generated `ls6-worker-1` and `ls6-code_reviewer-1` completed worker and
    reviewer jobs, then orchestrator aggregation completed;
  - release returned `loop_capacity_status = released`, `released_count = 2`,
    and `retained_count = 0`;
  - post-run `ps` showed only `orchestrator state=idle`;
  - `asks.jsonl` has three records, `events.jsonl` has seven records, and
    `breadcrumb.md` reached `Phase: done`;
  - final `kill -f` unmounted the smoke daemon.
- Real-provider feasibility check:
  - `codex`, `claude`, and `gemini` binaries are present in the test
    environment;
  - `/home/bfly/yunwei/test_ccb2/source_home` contains provider home
    directories for Codex, Claude, and Gemini;
  - `scripts/orchestrator_capacity_semantic_smoke.py` now prepares and
    preflights the real-provider smoke project, refuses to run real providers
    unless `CCB_ORCH_SMOKE_RUN_REAL=1` is set, and records pre-kill
    `ps`, `config validate`, and per-agent `pend` snapshots after a failed
    `run-once`;
  - the preflight also reports whether the selected provider has auth material
    in the isolated `source_home` and in the real home. For Codex, the isolated
    `/home/bfly/yunwei/test_ccb2/source_home` currently has no
    `.codex/auth.json`, while `/home/bfly` does;
  - prepare/preflight for Codex passed in
    `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-real-provider-smoke`:
    `preflight_status = ok`, `provider_executable_found = true`,
    `source_home_exists = true`, `rolepack_source_exists = true`;
  - the generated real-provider smoke project passed `ccb_test config
    validate` with `layout: orchestrator:codex`;
  - real Codex smoke with `--reset --run --provider-home-mode source-home`
    reached dynamic capacity and job dispatch but did not complete because the
    isolated source home is not logged in. Manual pane capture showed the
    dynamic worker at the Codex sign-in screen; this is an auth precondition,
    not a dynamic capacity failure;
  - real Codex smoke with `--reset --run --provider-home-mode real-home`
    passed in `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-realhome-smoke`;
  - the real-home run dynamically created `lrp1-worker-1` and
    `lrp1-code_reviewer-1`, completed worker job `job_5f7edefa8189`, reviewer
    job `job_f4eb13503fdb`, and orchestrator aggregation job
    `job_449eda2557d3`;
  - the real-home run wrote worker/reviewer/aggregate artifacts, returned
    `loop_run_status = ok`, and release reported `loop_capacity_status =
    released`, `released_count = 2`, `retained_count = 0`;
  - the smoke harness then ran `kill -f`, which returned `state: unmounted`;
  - real autonomous Codex smoke with
    `--reset --run-autonomous --provider-home-mode real-home` passed in
    `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-autonomous-smoke`;
  - the autonomous run used only an initial external ask to `orchestrator`.
    The orchestrator itself called `orchestrator-capacity`, parsed returned
    names, submitted callback asks, and released loop capacity;
  - autonomous parent job `job_de9c6b8f4f2f` delegated to worker
    `lauto2-worker-1` job `job_ae81df8b66ef`, continued as orchestrator job
    `job_780345f6ca54`, delegated to reviewer
    `lauto2-code_reviewer-1` job `job_67d7f932429d`, continued as final
    orchestrator job `job_fd1844c9ccbb`;
  - final autonomous reply included `AUTONOMOUS_LOOP_STATUS: pass`, worker
    agent `lauto2-worker-1`, reviewer agent `lauto2-code_reviewer-1`,
    `release_status: released`, `released_count: 2`, and `retained_count: 0`;
  - final capacity status for `auto2` is `loop_capacity_status = released`,
    both dynamic agents have `state = released`, and post-run `ps` plus
    `config validate` showed only durable `orchestrator`;
  - the smoke harness then ran `kill -f`, which returned `state: unmounted`;
  - fake-provider smoke evidence must not be interpreted as proof of real model
    behavior; real-home autonomous smoke now proves real Codex model use of the
    `orchestrator-capacity` skill for the bounded two-node round.
- Real autonomous repeat Codex smoke with
  `--reset --run-autonomous --repeat 3 --provider-home-mode real-home` passed
  in
  `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-autonomous-repeat-smoke`:
  - external control submitted one ask to `orchestrator` per round; the
    orchestrator handled `ensure -> worker callback -> reviewer callback ->
    release` inside each round;
  - `repeat_count = 3`, `autonomous_status = ok`, and rounds 1, 2, and 3 each
    reported `round_status = ok`;
  - all three rounds used generated targets `lrep-worker-1` and
    `lrep-code_reviewer-1`, with fresh worker/reviewer job ids per round;
  - final capacity status for loop `rep` reported `loop_capacity_status =
    released`, `released_count = 2`, `retained_count = 0`, and
    `published_graph_version = 7`;
  - post-round `ps` and `config validate` reported only durable
    `orchestrator`;
  - final project `ps` after harness cleanup reported `ccbd_state =
    unmounted` and `orchestrator state=stopped`.
- Repeat smoke hardening tests:
  - `python -m pytest test/test_orchestrator_capacity_semantic_smoke_script.py
    test/test_orchestrator_rolepack.py -q` passed with `11 passed`;
  - the relevant regression suite passed with `265 passed`.
- Layout cleanup hardening:
  - `scripts/orchestrator_capacity_semantic_smoke.py` now collects
    `ccb layout status --json` after the autonomous parent callback chain;
  - autonomous success requires both `loop_capacity_status = released` with
    `retained_count = 0` and `layout_status = ok` with
    `loop_agent_count = 0`;
  - focused script tests now cover the success path and the failure case where
    capacity is released but layout still reports loop-agent residue;
  - source-wrapper prepare/config validation passed in
    `/home/bfly/yunwei/test_ccb2/orchestrator-capacity-layout-prepare-1782571`
    using the generated project-local role store.

External smoke limitation:

- The mounted smoke uses CCB's fake provider. It proves source wrapper,
  config parsing, JSON command contract, CCB-owned runtime overlay, guarded
  reload add/remove, dispatcher ask/watch, retained busy release, deterministic
  run-once artifact writing, and cleanup in the dedicated test folder.
- Real-home autonomous smoke separately proves that a real Codex orchestrator
  can decide to call the skill and manage the worker/reviewer round. It still
  relies on inherited real Codex auth.

Next real-provider test decision:

- Decide whether the source-test real-provider smoke should keep using
  `provider-home-mode = real-home` for intentional inherited auth, or whether
  a narrow auth-seeding step should populate the isolated `source_home`.
- Keep `provider-home-mode = source-home` as the stricter isolation mode, but
  treat missing provider auth there as an expected preflight/auth blocker, not
  as a loop-capacity failure.
- Next role-behavior work should broaden from one worker/reviewer pair to
  multi-node planning, round checker policy, and failure/retry cases.
- Keep the test in `/home/bfly/yunwei/test_ccb2`; do not validate from
  `/home/bfly/yunwei/ccb_source`.

## Chosen V1 Path

Use a CCB-owned runtime capacity overlay over the existing guarded reload path.

Rationale:

- Current CCB already supports explicit `ccb reload` for append-only
  `add_agent` / `add_window` and idle `remove_agent`.
- This lets the first loop capacity implementation reach real tmux/provider
  behavior without redesigning ccbd service-graph ownership first.
- User-authored `.ccb/ccb.config` should not be rewritten merely because an
  orchestrator requested short-lived execution capacity.
- Active loop capacity state is clearly CCB-owned and removable, so short-lived
  loop agents do not become user-authored durable intent.

Target later:

- Move overlay application fully into daemon-side transient capacity ownership
  after the loop runtime model is stable.

## Landing Targets

### 1. Config Grammar

Add rich TOML support for:

```toml
[loop.capacity]
enabled = true
max_nodes = 4
default_lifetime = "current_round"
name_template = "loop-{loop_id}-{profile}-{index}"
reuse = "prefer_idle"

[loop.role_profiles.worker]
role = "agentroles.coder"
provider = "codex"
model = "gpt-5.5"
thinking = "high"
workspace_mode = "git-worktree"
max_instances = 4
reuse = "prefer_idle"

[loop.role_profiles.code_reviewer]
role = "agentroles.code_reviewer"
provider = "codex"
model = "gpt-5.5"
thinking = "medium"
workspace_mode = "git-worktree"
max_instances = 4
reuse = "prefer_idle"
```

Required behavior:

- `ccb config validate` reports these fields and validates them.
- Unknown `loop.capacity` or `loop.role_profiles.*` fields fail visibly.
- Unknown role ids fail with role-store path diagnostics.
- Unknown providers fail with existing provider validation.
- `model` follows existing provider model shortcut rules.
- `thinking` is parsed as source policy and mapped by provider adapters, or
  fails visibly when unsupported.
- `max_nodes` and per-profile `max_instances` are bounded.
- `name_template` must generate valid, deterministic, collision-resistant
  agent names.

Files likely affected:

- config models and parser under `lib/agents/config_loader_runtime/`
- config serialization/rendering
- `docs/ccb-config-layout-contract.md`
- targeted config-loader tests

### 2. Capacity Command Surface

Add:

```bash
ccb loop capacity ensure --loop-id <id> --profile worker=1 --profile code_reviewer=1 --json
ccb loop capacity status --loop-id <id> --json
ccb loop capacity release --loop-id <id> --idle-only --json
```

Required behavior:

- Commands are JSON-capable and deterministic.
- `ensure` validates requested profiles against `loop.role_profiles`.
- `ensure` is idempotent for the same loop/profile/count/lifetime.
- `ensure` creates or reuses agents only within configured limits.
- `status` reports generated/reused agents, profile, role, provider, state,
  lifetime, ownership, and blockers.
- `release --idle-only` removes only loop-owned idle generated agents.
- Busy release returns `retained` with reasons, not false success.
- All authoritative writes go through CCB-owned script/service paths.
- Raw `reload` may be used internally, but not exposed to orchestrator.

Required runtime state:

```text
.ccb/runtime/loops/<loop-id>/capacity.json
.ccb/runtime/loops/<loop-id>/events.jsonl
```

The state must record:

- requested profile counts
- resolved agent names
- source: `created`, `reused`, or `pinned`
- lifetime
- generated config block id or transient overlay id
- release status
- blockers and retained agents

### 3. Runtime Capacity Overlay

For the V1 transitional path, generated agents are materialized through
CCB-owned runtime loop state merged into project config loading.

Rules:

- User-authored config must remain distinguishable from generated loop entries.
- Generated entries must be owned by one loop id.
- Re-running `ensure` must not duplicate entries.
- `release --idle-only` must remove only matching generated entries from the
  active overlay.
- If reload fails after overlay activation, rollback or diagnostics must leave a
  recoverable state.
- User-authored agents must not be removed by loop release.

The implementation must not silently convert generated loop agents into
user-authored durable project intent.

### 4. Orchestrator RolePack And Skill

Materialize or update `agentroles.ccb_orchestrator` with:

- `orchestrator-capacity` skill.
- Skill reference for `ccb loop capacity ensure/status/release`.
- Negative instructions forbidding raw `ccb reload`, raw `ccb kill`, direct
  config edits, direct runtime-file writes, arbitrary provider/model choices,
  and unbounded node creation.
- Positive examples for requesting `worker + code_reviewer`.

The skill must let `orchestrator`:

1. decide desired profile counts from a work graph;
2. call `ccb loop capacity ensure`;
3. use returned agent names as `ask` targets;
4. call `ccb loop capacity status` when progress is unclear;
5. call `ccb loop capacity release --idle-only` after round drain.

### 5. Task Dispatch Loop

The first real task loop only needs one pair:

```text
orchestrator
  -> ensure worker=1, code_reviewer=1
  -> ask worker to perform a bounded file/task change
  -> ask code_reviewer to inspect worker result and tests
  -> aggregate result
  -> release idle generated agents
```

Acceptance rules:

- `worker` and `code_reviewer` are created dynamically from profile config.
- `orchestrator` does not target pre-existing hard-coded agent names.
- `code_reviewer` receives worker result refs or artifact refs.
- `orchestrator` reports pass, rework, blocked, or non-converged.
- Release happens only after the pair is idle.

### 6. Deterministic Run-Once Loop Runner

Add the first bounded loop-runner entrypoint:

```bash
ccb loop run-once --loop-id <id> --task <text> [--worker-profile worker] [--reviewer-profile code_reviewer] [--orchestrator orchestrator] [--timeout 30] [--json]
```

Required behavior:

- The command requires an existing CCB project anchor and must not bootstrap a
  default project when run from an unintended directory.
- It requests exactly one configured worker profile and one configured reviewer
  profile through the same `loop capacity ensure` authority.
- It must use generated names returned by capacity state, not static
  hard-coded worker/reviewer names.
- It must submit and watch three jobs in order: worker, reviewer, orchestrator
  aggregation.
- It must release generated agents through `loop capacity release --idle-only`
  after the ask/watch sequence finishes or fails.
- It must return nonzero when the round is incomplete, while still writing
  available evidence and attempting idle release.

Required loop artifacts:

```text
.ccb/runtime/loops/<loop-id>/round.json
.ccb/runtime/loops/<loop-id>/asks.jsonl
.ccb/runtime/loops/<loop-id>/events.jsonl
.ccb/runtime/loops/<loop-id>/breadcrumb.md
.ccb/runtime/loops/<loop-id>/artifacts/worker-reply.md
.ccb/runtime/loops/<loop-id>/artifacts/reviewer-reply.md
.ccb/runtime/loops/<loop-id>/artifacts/aggregate-reply.md
```

Artifact requirements:

- `round.json` records schema version, status, project id/root, task, selected
  profiles, generated agents, worker/reviewer/aggregation job ids, reply
  artifact paths, capacity ensure/release summaries, failure or release-error
  records when present, and artifact paths.
- `asks.jsonl` records one line per submitted ask with loop id, target,
  purpose, node id, job id, and submitted state.
- `events.jsonl` records loop start, capacity events, ask terminal events, and
  loop finish.
- `breadcrumb.md` is a compact current-state pointer for humans and future
  loop machinery; it must end at `Phase: done` for a successful round.
- Reply artifacts contain the terminal worker, reviewer, and aggregation
  replies exactly as captured by CCB watch.

## Test Targets

All source runtime validation must run from:

```bash
cd /home/bfly/yunwei/test_ccb2
HOME=/home/bfly/yunwei/test_ccb2/source_home \
CCB_SOURCE_HOME=/home/bfly/yunwei/test_ccb2/source_home \
/home/bfly/yunwei/ccb_source/ccb_test ...
```

Do not validate this feature from `/home/bfly/yunwei/ccb_source`, and do not use
the globally installed `ccb` for source-change validation.

### A. Unit And Parser Tests

Pass targeted tests for:

- config parsing of `[loop.capacity]`;
- config parsing of `[loop.role_profiles.<name>]`;
- unknown field rejection;
- role/provider/model/thinking validation;
- name-template validation;
- render/round-trip preservation;
- runtime overlay activation and removal;
- capacity state read/write.

### B. CLI Contract Tests

Pass targeted tests for:

```bash
/home/bfly/yunwei/ccb_source/ccb_test loop capacity ensure --help
/home/bfly/yunwei/ccb_source/ccb_test loop capacity status --help
/home/bfly/yunwei/ccb_source/ccb_test loop capacity release --help
/home/bfly/yunwei/ccb_source/ccb_test loop run-once --help
```

And JSON contract tests for:

- valid `ensure worker=1 code_reviewer=1`;
- repeated ensure idempotence;
- unknown profile rejection;
- max-node rejection;
- status after ensure;
- release after idle;
- busy release retained result;
- release idempotence after cleanup.
- `run-once` parser contract for loop id, task, profile override,
  orchestrator override, timeout, and JSON mode.
- `run-once` service contract for ensure -> worker ask/watch -> reviewer
  ask/watch -> orchestrator ask/watch -> release.
- `run-once` artifact contract for `round.json`, `asks.jsonl`, `events.jsonl`,
  `breadcrumb.md`, and reply artifacts.

### C. Real Test Folder Smoke

Use `/home/bfly/yunwei/test_ccb2` as the real project.

Initial project config:

- include an `orchestrator` agent;
- include `loop.capacity`;
- include `loop.role_profiles.worker`;
- include `loop.role_profiles.code_reviewer`;
- do not predefine the dynamic worker/reviewer agents as static mounted agents.

Smoke steps:

1. Run `/home/bfly/yunwei/ccb_source/ccb_test --diagnose`.
2. Run `/home/bfly/yunwei/ccb_source/ccb_test config validate` and confirm
   loop profiles are recognized.
3. Start the project with `/home/bfly/yunwei/ccb_source/ccb_test`.
4. Run `/home/bfly/yunwei/ccb_source/ccb_test loop capacity ensure --loop-id loop-smoke-001 --profile worker=1 --profile code_reviewer=1 --json`.
5. Confirm two generated agents enter the active project config and mount,
   appearing in project status/sidebar data.
6. Ask `orchestrator` to perform a bounded task using the generated
   `worker + code_reviewer` pair.
7. Confirm the worker produces the requested artifact.
8. Confirm the code reviewer reviews the worker result and either passes or
   returns a concrete rework result.
9. Confirm `orchestrator` aggregates the result.
10. Run `/home/bfly/yunwei/ccb_source/ccb_test loop capacity release --loop-id loop-smoke-001 --idle-only --json`.
11. Confirm generated agents are removed or detached, while user-authored
    agents remain mounted.
12. Restart the project and confirm released dynamic agents do not reappear as
    durable desired agents.
13. Run `/home/bfly/yunwei/ccb_source/ccb_test loop run-once --loop-id loop-smoke-002 --task "<bounded task>" --timeout 30 --json`.
14. Confirm the returned payload is `loop_run_status = ok`, includes generated
    worker/reviewer names, and includes worker/reviewer/aggregate job ids.
15. Confirm `.ccb/runtime/loops/loop-smoke-002/round.json`,
    `asks.jsonl`, `events.jsonl`, `breadcrumb.md`, and reply artifacts exist.
16. Confirm release after `run-once` leaves only user-authored agents mounted.

### D. Negative Real Tests

The real test folder must also prove:

- `orchestrator` cannot request a profile not declared in config.
- `orchestrator` cannot choose an undeclared provider/model/thinking value.
- requesting more than `max_nodes` fails.
- raw reload/kill/config-edit prompts are refused by the
  `orchestrator-capacity` skill.
- release refuses a busy generated agent and reports it as retained.
- failed capacity ensure does not leave duplicate generated config entries.
- failed capacity reload does not leave a broken active overlay.
- `loop run-once` from a directory without a CCB project anchor does not create
  a default `.ccb` project.
- `loop run-once` writes failure evidence and attempts idle release when a
  watched job is not terminal/completed.

## Completion Criteria

This goal is complete only when all are true:

- `loop.role_profiles` grammar lands with docs and tests.
- `ccb loop capacity ensure/status/release` lands with JSON contracts.
- `agentroles.ccb_orchestrator` includes the capacity skill.
- `/home/bfly/yunwei/test_ccb2` real smoke proves dynamic
  `worker + code_reviewer` creation, task dispatch, review, aggregation, and
  release.
- `loop run-once` writes the round, ask, event, breadcrumb, and reply artifacts
  described above.
- Negative tests prove no raw reload/kill/config-edit path is needed or used by
  orchestrator.
- Releasing a loop leaves no durable generated agents that remount on next
  start.
- User `.ccb/ccb.config` is not rewritten by capacity ensure/release.
- Verification evidence is recorded in this plan's roadmap or history.

## Non-Goals

- Arbitrary dynamic provider replacement.
- Busy force-unload.
- Moving existing user-authored agents between windows.
- Full daemon-side transient capacity overlay in the first slice.
- Unlimited parallel nodes.
- Publishing a release before real `test_ccb2` evidence exists.

## Handoff Notes

Implementation should proceed in this order:

1. Config grammar and validation.
2. Capacity state model and JSON CLI surface.
3. Runtime overlay over guarded reload.
4. RolePack skill materialization.
5. Unit/CLI tests.
6. Deterministic `loop run-once` runner and artifact contract.
7. Real `/home/bfly/yunwei/test_ccb2` smoke.
8. Plan-tree evidence update.
