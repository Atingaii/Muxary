# Role Pack System Roadmap

Date: 2026-06-01

## Done

- Defined Role Pack as a reusable package of identity, responsibility, memory,
  skills, tools, permissions, and host adapters.
- Separated stable role ids from project-local agent names in
  [decisions/001-role-id-separate-from-agent-name.md](decisions/001-role-id-separate-from-agent-name.md).
- Chose a shared system role store with project locks and runtime projection in
  [decisions/002-system-role-store-project-locks.md](decisions/002-system-role-store-project-locks.md).
- Chose a host-neutral Role Pack core with host/provider adapters in
  [decisions/003-rolepacks-are-host-neutral-with-adapters.md](decisions/003-rolepacks-are-host-neutral-with-adapters.md).
- Accepted CCB role-id shorthand and role-id ask alias semantics in
  [decisions/004-role-id-shorthand-resolves-to-agent-name.md](decisions/004-role-id-shorthand-resolves-to-agent-name.md).
- Chose `agent-roles-spec` as the role catalog authority; CCB consumes the
  catalog but does not keep production role packages in its source tree. See
  [decisions/005-agent-roles-spec-is-catalog-authority.md](decisions/005-agent-roles-spec-is-catalog-authority.md).
- Captured the first `agentroles.archi` role slice in
  [topics/archi-role-first-slice.md](topics/archi-role-first-slice.md).
- Added the first source-tree `roles/ccb.archi` package, role manifest parsing,
  system-store install, `ccb roles list/show/install/add/doctor`, config
  `role` parsing, project role locks, role memory inclusion, and Codex/Claude
  role skill projection.
- Implemented CCB role-id shorthand in config loading and role-id ask alias
  routing with project-local agent names.
- Added `agent-roles-spec` catalog discovery with production `roles/`
  discovery by default, `reference_roles/` opt-in for development/testing,
  catalog digest status, and no production fallback to CCB source-tree role
  packages.
- Changed `ccb update` role handling so it updates already installed catalog
  roles when their version or digest changed, reports new catalog roles, and
  prompts interactively before installing newly available roles without binding
  them to a project or editing project locks.
- Added a lightweight `rolepacks.runtime_lookup` path for role memory and
  skill projection, so provider home materialization no longer imports role
  management services.
- Added runtime stale-lock protection: if an installed role's `current`
  version or digest no longer matches a project's `.ccb/role-lock.json`, CCB
  reports a `role_lock_mismatch` warning instead of silently projecting the
  drifted role memory or skills.
- Extended project role locks with `default_agent_name` so role-id shorthand
  keeps using the project-adopted visible agent name even when installed
  `current` has drifted.
- Rendered warning-only role memory sources so `role_lock_mismatch` is visible
  in generated provider memory, not only in projection event metadata.
- Changed installed role versions to content-addressed paths
  `versions/<version>/<digest>/` and made runtime/config lookup resolve project
  locks by version plus digest before consulting mutable `current`.
- Added duplicate catalog-source diagnostics so registered sources cannot
  silently shadow the default `agent-roles-spec` role id.
- Added a legacy compatibility alias from `ccb.archi` to `agentroles.archi`
  across roles CLI commands, config shorthand, ask routing, and installed
  store lookup. New writes use the canonical `agentroles.archi` id.
- Removed source-tree `roles/ccb.archi` content and excluded the source-tree
  `roles/` directory from release artifacts; production role content is now
  expected from `agent-roles-spec`.
- Added GitHub-backed `agent-roles-spec` catalog fallback through a CCB-owned
  user cache under `$XDG_CACHE_HOME/ccb/role-catalogs/agent-roles-spec`, with
  local env/path catalogs taking precedence. The cache is consumption-only;
  role content changes go to the upstream GitHub repository by PR.
- Added user-level system role sources at `~/.ccb/roles` and `~/.roles`.
  These local editable role sources take precedence over the remote catalog,
  are visible in `ccb roles list`, and can be snapshotted into the installed
  store when added to a project. Project-level `.roles` is deferred.
- Added explicit `ccb roles sync [path]` for local source edits. With no path,
  it defaults to the current working directory, updates only already installed
  same-id roles discovered under that path, and does not change project locks.
- Completed the production `agentroles.archi` PR in `agent-roles-spec` as
  GitHub PR #1, with production role content removed from `ccb_source`.
- Hardened installed role snapshots so Python tool hooks do not generate
  bytecode caches, polluted content-addressed targets are repaired on
  reinstall, and project locks write the installed metadata digest.
- Made duplicate catalog diagnostics visible in `ccb roles list`, including
  the `reference_roles` opt-in case where production `roles/` wins.
- Completed real `/home/bfly/yunwei/test_ccb2` validation for catalog list,
  install/update/tool doctor, project add/lock, digest pinning, `roles sync`
  path/default behavior, provider memory/skill projection, `ccb` startup,
  `ccb reload`, and runtime doctor. See
  [history/final-rolepack-validation-2026-06-03.md](history/final-rolepack-validation-2026-06-03.md).
- Accepted the long-term boundary that `agent-roles-spec` should own `.roles`
  package management while CCB wraps those operations for project/runtime
  integration. See
  [decisions/006-agent-roles-spec-owns-roles-store.md](decisions/006-agent-roles-spec-owns-roles-store.md)
  and [topics/spec-owned-roles-store.md](topics/spec-owned-roles-store.md).
- Accepted the single-current `.roles` store and restart-based role adoption
  model. Project role locks and content-addressed installed history are no
  longer target runtime semantics. See
  [decisions/007-single-current-store-and-restart-adoption.md](decisions/007-single-current-store-and-restart-adoption.md).
- Added the first executable `agent-roles` package-manager slice in
  `agent-roles-spec`: `.roles/installed` store, JSON package commands, and the
  `ccb.archi -> agentroles.archi` alias.
- Added the CCB compatibility bridge: `ccb roles install/update/sync` delegates
  role payload operations to `agent-roles`, and runtime/config lookup reads the
  spec-owned `AGENT_ROLES_STORE` or `~/.roles/installed` installed store.
- Added automatic legacy installed-role migration from
  `$XDG_DATA_HOME/ccb/roles` into `.roles/installed` at CCB role-management
  boundaries. The legacy store is migration input only; `.roles/installed` is
  the single runtime read path.
- Removed the CCB-private installed role writer and
  `CCB_AGENT_ROLES_MANAGER` rollback switch so role payload writes have one
  owner.
- Documented and tested multiple project-local agents bound to the same role
  id. The shorthand path remains a single-default-agent convenience, while
  `ccb roles add <role-id>:<provider> --agent <name>` creates explicit
  additional instances.

## In Progress

- Validate the single-store spec-owned package manager bridge and legacy store
  copy migration across old-version upgrade scenarios before release.
- Add provider-specific fresh-start support for role digest changes during
  guarded restart. The current landing fails explicitly instead of silently
  resuming an old provider conversation.

## Next

1. Add provider fresh-start implementation behind `ccb restart <agent>` for
   sessions whose launch role digest differs from installed current.
2. Add a doctor/cleanup command for legacy `.ccb/role-lock.json` residue.
3. Move legacy store migration ownership into `agent-roles` once the package
   manager exposes a stable migration command/API.
4. Decide whether CCB should keep calling `agent-roles` through subprocess JSON
   or also support a library API for management commands.
5. Add import-boundary smoke tests so config loading, provider hooks, and
   provider-home projection cannot accidentally import role management,
   package-manager subprocess, or network-capable source discovery paths.
6. Harden role install/update/sync resilience: tool-hook failure state or
   rollback, concurrent same-role operations, and project config mutation
   consistency.
7. Harden role projection cleanup when a role is removed or changed.
8. Add PR governance and compatibility tests from
   [topics/test-and-governance.md](topics/test-and-governance.md).

## Deferred

- Public role registry or marketplace.
- Signed remote role distribution.
- Automatic background update checks outside explicit `ccb update`.
- Role replacement for already-running agents without guarded restart.
- Multi-role composition on one agent.
- Role dependency solving across conflicting tool versions.
- UI browser for discovering community roles.
- Signed or otherwise authenticated catalog/cache updates.
