# Single Current Role Store And Restart Adoption

Date: 2026-06-17

## Context

The current Role Pack implementation keeps installed role snapshots under
`versions/<version>/<digest>/` and uses `.ccb/role-lock.json` to pin a project
to a specific digest. That gives reproducibility, but it makes ordinary role
updates hard to reason about: updating `agent-roles-spec` can leave projects on
old locks, diagnostics need stale-lock paths, and users must understand
project adoption separate from installed role updates.

The desired operating model is simpler: the user-level `.roles` library should
contain one installed copy of each role, projects should follow the installed
current role, and restarting an affected agent should be the clear adoption
boundary.

## Decision

Use a single-current installed role model.

`agent-roles-spec` owns one installed package per role id under
`.roles/installed/<role-id>/`. The installed package may be represented as a
`current/` directory or as a flat role directory, but `versions/<version>/<digest>/`
is no longer a runtime contract.

`install.json` remains useful and should keep:

- role id
- version
- current content digest
- source and provenance
- catalog level and timestamps when available

The digest is a current-content fingerprint for catalog comparison, update
diagnostics, and restart freshness. It is not a project lock target.

CCB should stop writing or using `.ccb/role-lock.json` for role resolution.
Existing lock files are legacy residue: CCB may report them in doctor/cleanup
diagnostics, but runtime lookup should resolve the configured role id to the
installed current role.

Running agents do not hot-apply role memory or skill changes. Role adoption for
a live agent happens through `ccb restart <agent>`:

1. `ccb roles update <role-id>` updates the installed current role.
2. New agent launches use the updated role.
3. Existing idle agents adopt the updated role through `ccb restart <agent>`.
4. Busy agents keep the existing busy gate and return blocked until active work
   is clear.
5. When the role digest changed since the agent started, restart must not
   silently resume the old provider conversation. The preferred final behavior
   is to launch a fresh provider conversation with the new role projection; a
   safe explicit failure is acceptable until each provider has that support.

No provider-native `clear` or resume packet is required for normal role updates.
Clear/resume remains a recovery tool for corrupted provider context or
interrupted work that must be reconstructed.

## Relationship To Earlier Decisions

This decision supersedes the project-lock and content-addressed historical
snapshot parts of
[002-system-role-store-project-locks.md](002-system-role-store-project-locks.md),
[005-agent-roles-spec-is-catalog-authority.md](005-agent-roles-spec-is-catalog-authority.md),
and [006-agent-roles-spec-owns-roles-store.md](006-agent-roles-spec-owns-roles-store.md).

Those decisions still stand for:

- stable role ids separate from project-local agent names
- production role content living in `agent-roles-spec`
- `agent-roles-spec` owning `.roles` package management
- CCB owning project config, provider projection, ask/sidebar/restart behavior,
  and CCB-specific diagnostics

## Consequences

- Role updates are easier to explain: update the role, then restart affected
  agents.
- `.roles` no longer needs installed history garbage collection as a core
  feature.
- Reproducibility shifts from per-project role locks to operational evidence:
  job/runtime records should capture the role id, version, and digest used when
  a provider was launched.
- Existing `.ccb/role-lock.json` files need a legacy handling path so they do
  not block startup or silently suppress role projection.
- Existing multi-version installed stores need migration or compatibility reads
  that resolve `current` once, then write the simplified store on the next
  install/update.
- Restart logic needs role-awareness: if the started role digest differs from
  installed current, restart must either fresh-start the provider conversation
  so the new role memory becomes initial context, or fail explicitly rather than
  pretending the old provider conversation adopted the new role.

## Acceptance Criteria

- `.roles/installed/<role-id>` contains one installed role package plus
  `install.json`; old `versions/` directories are not required for normal
  operation.
- CCB runtime/config lookup follows installed current and ignores project role
  locks for role resolution.
- `ccb roles add` updates `.ccb/ccb.config` only; it does not create or refresh
  `.ccb/role-lock.json`.
- `ccb roles update <role-id>` replaces installed current and updates
  `install.json.digest`.
- Agent startup records the role id, version, and digest used for that launch.
- `ccb restart <agent>` reloads current role assets. When the digest changed
  since launch, it must not resume the old provider conversation as if it
  adopted the new role; until provider fresh-start support lands, it may fail
  explicitly with a role-digest-changed reason.
- Existing `.ccb/role-lock.json` files do not suppress role memory or skills.
- Tests cover legacy lock residue, legacy multi-version stores, role update
  followed by restart, and busy restart blocking.
