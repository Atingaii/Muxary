# CCB Workflow Plan Tree Skill Overlay

Date: 2026-07-15
Status: Design accepted; implementation not started
Activation authority: Config V3 `agentic_loop_v1`
Permission prerequisite: Decision 030 Planner Scoped PlanTree Read Authority
Global control follow-up: [Decision 031](../decisions/031-global-plan-tree-authority-across-worktrees.md)

## Purpose

Define a CCB-owned Plan Tree skill for the agentic-loop workflow without
changing the public Plan Tree skill or making workflow behavior the default for
ordinary CCB agents. The CCB version may retain the useful public document
model while replacing incompatible behavior and adding workflow-only Roadmap,
task, proposal, revision, and controller semantics.

This is a specialized provider instruction surface, not the Plan Tree storage
engine. It cannot create runtime authority by itself.

## Product Decision

CCB ships one complete workflow-specific effective skill under the logical
skill name `plan-tree`. CCB projects that replacement only into the managed
provider home for the Config V3 Planner. The public skill in the user's source
home, global skill store, plugin, or repository remains untouched.

```text
public Plan Tree behavior                CCB workflow contracts
  entrypoint / baseline                    Config V3 identity
  roadmap / decisions / evidence           Decision 030 read boundary
  retrieval / resume                       proposal schemas and fences
                  \                       /
                   complete CCB effective skill
                             |
                    managed Planner home only
```

The first version is a complete replacement, not a textual suffix appended to
an arbitrary installed skill. Runtime concatenation would retain conflicting
instructions, make the effective digest depend on user-local files, and permit
an untrusted public/custom skill to expand Planner authority.

The specialized skill may be generated at build time from a pinned public base
or authored as a standalone artifact. In either case, the shipped result and
its exact digest are the authority. Runtime never merges it with the user's
installed `plan-tree` content.

## Exact Activation Gate

No new user-authored Boolean switch is needed. The first implementation uses
the existing strict Config V3 profile as the feature gate. The overlay is
eligible only when every predicate is true:

```text
project_config.version == 3
workflow.mode == "agentic-loop"
workflow.profile == "agentic_loop_v1"
agent slot == "planner"
role id == "agentroles.ccb_planner"
provider in the Decision 030 qualified provider set
Role, permission, command-surface, and projection digests are valid
inherited provider skills are mechanically excluded for this Planner
```

The gate is an exact tuple, not a fuzzy capability check. A future workflow
profile receives its own explicit overlay compatibility declaration. Config
V2, ordinary CCB agents, non-Planner Config V3 roles, and standalone provider
sessions retain their normal skill behavior and never receive this overlay.

A declared Config V3 workflow whose required overlay is missing, stale,
tampered, or incompatible fails Planner mount before provider submission. It
must not fall back to the public skill because that skill permits direct plan
editing and `execute-ready` implementation behavior that Decision 030 forbids.

## Projection Ownership

The CCB Planner RolePack adapter owns this projection. It should use a
workflow-gated adapter declaration rather than adding the skill to the generic
Role `contents.skills` list, because the latter currently also projects Role
skills for Config V2 agents.

Target adapter shape:

```toml
[adapters.ccb.skill_overlays.plan_tree]
logical_name = "plan-tree"
source = "skills/plan-tree"
activation = "config_v3_agentic_loop_planner"
mode = "managed_replace"
```

This is a target schema, not a claim that the current Role manifest parser
already accepts it.

Current implementation anchors that motivate the adapter gate are:

- `lib/agents/config_loader_runtime/parsing_runtime/workflow_v3.py` already
  validates the exact V3 mode/profile/entry-role tuple;
- `lib/rolepacks/projection.py` currently projects every declared Role skill
  without a Config V3 condition, so the specialized skill cannot use that
  generic list unchanged;
- `lib/provider_profiles/codex_home_config.py` and
  `lib/provider_backends/claude/launcher_runtime/home.py` materialize inherited
  assets before Role skills and therefore must apply the same exclusion and
  replacement contract;
- `lib/cli/services/role_command_policy.py` already identifies the restricted
  command surface that disables inherited assets for the Planner.

Projection order is deterministic:

1. Parse and validate the project config.
2. Resolve the exact Planner Role and command policy.
3. Exclude inherited provider skills for the restricted Planner surface.
4. Validate the specialized skill tree and its expected digest.
5. Project it as the sole effective `plan-tree` into the managed home.
6. Bind its digest into the provider projection and Planner activation.
7. Start the provider only after the capability gate accepts the exact surface.

CCB must never replace, delete, or rewrite the source-home skill. The managed
home is rebuildable runtime state. Switching away from Config V3 or changing
the Planner Role removes the CCB-owned projection and rematerializes the normal
inherited skill set in the same lifecycle action; stale specialized content
must not survive until a second restart.

## Effective Skill Boundary

The specialized skill keeps these public Plan Tree concepts:

- one discoverable Plan Tree entrypoint and registered plan roots;
- baseline, roadmap, status, decisions, open questions, and evidence roles;
- minimal reading, stable links, retrieval, resume, and history hygiene;
- evidence-backed completion and explicit unresolved state;
- separation of durable meaning from noisy runtime observations.

It replaces these public behaviors for the workflow Planner:

- no `execute-ready` mode that edits implementation or Plan Tree files;
- no bootstrap, migration, archive, rename, or direct Markdown write;
- no generic shell, file search, file read, `update_plan`, ask, test, or build;
- no implicit authority from provider prose, a local Markdown checkout, or a
  skill instruction;
- no inference of task, lane, revision, completion, or release state.

The only positive read surface is the Decision 030 controller-issued,
digest-bound PlanTree read manifest and its dedicated literal list/read/find
operations. The skill cannot widen the manifest path set or convert a Markdown
link into read authority.

The only outputs are activation-selected proposals. Existing specialized
skills retain the parser-level output grammar:

- `planner-task-packet` owns initial single-task or task-set proposal shape;
- `planner-closure-backfill` owns Detailer replan and task-set closure shape;
- the workflow `plan-tree` skill owns document semantics, Roadmap reasoning,
  authority interpretation, and routing to the selected output contract;
- controller code validates and applies or rejects every proposal.

## Workflow Roadmap Properties

The specialized skill may reason about CCB workflow fields supplied by the
controller, but it never creates their authority. The first profile supports
only fields already backed by the current single-lane controller contracts:

- plan root and expected PlanTree projection revision;
- task or task-set id and revision;
- source Frontdesk request and Planner activation identity;
- goal, scope, non-goals, interface contracts, and acceptance criteria;
- dependency and ordering proposals;
- route and readiness recommendation;
- allowed change paths and executable verification for executable routes;
- Roadmap and TODO transition proposals;
- accepted, unresolved, blocker, decision, and evidence refs;
- aggregate result, closure evidence digest, and next milestone;
- compact Frontdesk status proposal when selected by the activation.

Roadmap Graph node ids, typed global authority closure, lanes, scope claims,
holder generations, integration ids, and publication stages remain dormant
unless a later controller-issued capability envelope explicitly enables their
implemented schema. Merely documenting Decision 031 or seeing lane-like files
does not activate those fields under `agentic_loop_v1`.

## Authority By Domain

There is no single blanket rule that all machine files outrank all Markdown.
Authority is divided by field ownership:

| Domain | Authority | Planner behavior |
| :--- | :--- | :--- |
| Goal, scope, rationale, accepted decision, acceptance meaning | Accepted semantic Plan Tree content | Read through the manifest and propose a revision |
| Task identity, revision, status, closure, indexes | Controller-owned records | Copy supplied authority and propose; never mutate |
| Runtime job, node, round, provider, release, cleanup | CCB runtime/controller state | Treat supplied facts as evidence only |
| Roadmap Graph, lane, fence, integration publication | Implemented controller schema when capability-enabled | Never infer from Markdown or prose |
| Human-readable generated status/index | Controller projection | Never use as stronger authority than its bound source |
| Provider response | Proposal evidence | Has no authority until validated and imported |

Markdown/record drift is a controller error. The Planner reports a blocker or
stale proposal; it does not choose one copy, repair the files, or use
last-writer-wins.

## Version And Digest Binding

Instruction versioning is separate from Plan Tree data schemas. A projection
record should bind at least:

```json
{
  "schema": "ccb.skill_projection.v1",
  "logical_skill": "plan-tree",
  "activation": "config_v3_agentic_loop_planner",
  "workflow_profile": "agentic_loop_v1",
  "effective_skill_version": "ccb-workflow-v1",
  "effective_skill_digest": "sha256:...",
  "public_compatibility_digest": "sha256:...",
  "role_id": "agentroles.ccb_planner",
  "role_version": "...",
  "role_digest": "sha256:...",
  "permission_digest": "sha256:...",
  "config_digest": "sha256:..."
}
```

`public_compatibility_digest` identifies the pinned public baseline used by
build/test compatibility checks. It does not authorize reading or merging the
user's installed skill. Changing effective instructions increments the
specialized skill and Planner Role versions and changes the canonical Role
tree/projection digests. Decision 030's exact ordered Role lock must therefore
be refrozen in the same accepted candidate.

## Reload And Recovery

- Materialization occurs before provider start or restart, never after a
  Planner activation has begun.
- Config or Role reload compares the effective projection digest. A changed
  gate or digest requires restart of the corresponding Planner pane.
- An in-flight activation keeps its original Role, permission, projection,
  read-manifest, and plan revision tuple; it is never silently upgraded.
- A stale reply is preserved as evidence and rejected at import.
- Projection cleanup is marker-owned and may remove only the managed-home
  target created by the matching CCB projection.
- Failed materialization leaves no half-written skill tree and does not start
  the provider.

## Acceptance Matrix

| Case | Required result |
| :--- | :--- |
| Config V2 with public `plan-tree` | Public source/managed behavior remains unchanged; no CCB workflow overlay marker |
| Config V3 Frontdesk or dynamic Role | No workflow `plan-tree` projection |
| Exact Config V3 Planner tuple | One specialized `plan-tree` with matching Role/permission/projection digests |
| Invalid mode/profile/Role binding | Config or mount fails before projection/provider submit |
| Missing or tampered specialized skill | Fail mount; never fall back to public instructions |
| Public skill contains `execute-ready` writes | Specialized effective skill contains no direct-write or implementation authority |
| User has a customized public skill | Source remains byte-identical; runtime does not merge it into Planner authority |
| Config V3 to V2 reload | Specialized target is removed and normal inherited skills are restored in one restart |
| Concurrent Codex/Claude Planner materialization | Provider homes receive semantically equivalent, digest-bound specialized skills |
| Activation/read-manifest drift | Reply/import fails closed with stale evidence retained |
| Planner output | Exactly one activation-selected proposal; no file write, ask, notification, or state mutation |
| Decision 030 gate | M1-M13, Role aggregate lock, provider projection, refusal cleanup, and zero residue remain mandatory |
| Real opened project | Visible Config V3 Codex-primary and qualified Claude-secondary runs prove the same frozen corpus |

Tests must inspect both positive presence and negative absence. A successful
Planner response alone does not prove that public skills were not inherited or
that stale workflow instructions were removed.

## Sequencing

1. Keep the public Plan Tree skill unchanged.
2. Land this design as a Config V3/Planner-only contract.
3. Complete and accept Decision 030 M1-M13 on the active workflow branch.
4. Add the workflow-gated Role adapter projection and complete specialized
   skill artifact in one candidate.
5. Refreeze the Planner Role, permission, projection, and ordered Role-set
   digests.
6. Pass source/fake projection, reload, tamper, stale, and zero-residue tests.
7. Re-run the frozen real-provider workflow gates before package publication.
8. Add Decision 031 fields only after their controller capability exists and
   its separate acceptance matrix passes.

## Non-Goals

- Do not redesign or replace the public Plan Tree skill.
- Do not expose the CCB workflow overlay to ordinary CCB agents.
- Do not add a second user-visible Config V3 enable flag.
- Do not dynamically merge arbitrary user skill content.
- Do not let a skill grant filesystem, tool, task, lane, or state authority.
- Do not enable Decision 031 multi-worktree or multi-lane behavior merely by
  shipping its vocabulary in the skill.
- Do not treat the projection marker, generated Markdown, or provider prose as
  workflow completion evidence.

## Related

- [config-v3-dynamic-workflow.md](config-v3-dynamic-workflow.md)
- [planner-role-design.md](planner-role-design.md)
- [planner-feedback-and-task-set-closure-plan.md](planner-feedback-and-task-set-closure-plan.md)
- [state-and-script-contract.md](state-and-script-contract.md)
- [../decisions/023-roadmap-graph-and-workflow-lanes.md](../decisions/023-roadmap-graph-and-workflow-lanes.md)
- [../decisions/024-project-topology-controller-and-single-lane-first.md](../decisions/024-project-topology-controller-and-single-lane-first.md)
- [../decisions/029-planner-feedback-and-task-set-closure.md](../decisions/029-planner-feedback-and-task-set-closure.md)
- [../decisions/031-global-plan-tree-authority-across-worktrees.md](../decisions/031-global-plan-tree-authority-across-worktrees.md)
