# Single-Lane Wave 1 Config And RolePack Closure

Date: 2026-07-11
Status: Accepted by direct `talk2` source audit

## Landed

- `615460ec`: adaptive one-to-four-workgroup RolePack contracts for the
  orchestrator, coder, code reviewer, task detailer, and round reviewer.
- `95d9a409`: aligned coder and reviewer template result fields with the
  runtime parser's authoritative `status:` contract.
- `6c2a15ad`: strict opt-in Config V3 loader, model, validator, effective
  capacity, sanitized diagnostics, and dry-run-only V2 migration preview.
- `fcf07b3a`: validate the complete installed RolePack manifest and reject a
  configured provider that the selected RolePack does not support.

Config V2 remains the static compatibility surface. Config V3 requires
explicit frontdesk/planner resident bindings, explicit immutable dynamic role
profiles, provider/model settings, one-to-four semantic workgroup limits,
physical dynamic-agent capacity, controller-owned integration, and installed
RolePacks. Provider replies still have no authority over config or runtime
state.

## Direct Verification

- Config V3 plus RolePack/projection/provider-hook gate: `176 passed`.
- V2 config/provider/doctor/parser/context compatibility: `270 passed`.
- Loop capacity, plan-task, topology, and bundle adjacency: `218 passed`.
- Repository gate excluding explicitly marked heavy provider blackboxes:
  `4033 passed, 2 skipped, 21 deselected`.
- Changed-file `py_compile` and `git diff --check`: passed.

The repository gate exposed a separate cleanup defect: several process-level
entrypoint tests left temporary pytest ccbd/tmux/provider processes after
pytest reported success. `talk2` released each temporary project with its own
source-test `ccb_test ... kill` command and verified the workflow source tree
remained clean. Automatic test-harness residue cleanup remains an E1/G5 gate;
the green assertion count does not waive it.

## Review Findings Fixed Before Acceptance

1. The coder and code-reviewer templates used `result:` / `check result:`,
   while the runtime parser consumes `status:`. This could miss a real
   `rework_required` result and was corrected with drift tests.
2. The initial Config V3 parser only checked that a role manifest path and id
   existed. It now parses the full RolePack schema and enforces its declared
   provider compatibility before startup. Real Agent Role preview manifests
   are covered through their CCB adapters.

## Remaining Boundary

Wave 1 does not enable multi-node execution. The controller still pauses a
multi-node bundle before bind. Git-reviewed node commits, deterministic
integration, ready-frontier scheduling, crash recovery, owner-scoped release,
fake/failure evidence, visible real-provider fanout, and packed-candidate
acceptance remain open.
