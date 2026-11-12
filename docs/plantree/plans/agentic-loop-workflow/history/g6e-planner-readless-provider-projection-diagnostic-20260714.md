# G6E Planner Readless Provider Projection Diagnostic

Date: 2026-07-14
Status: normative contract frozen; P0 implementation and refreeze required
Observed code candidate: `62753d63791f8b644ee6f5f5433fe57070fb2c84`

## Admission Stop

The first visible C1/C3 lanes are rejected workflow evidence. Their Frontdesk
handoffs and Planner artifacts are useful, but neither Planner session honored
the required reply-only/readless boundary:

- Codex `gpt-5.4` exposed `exec_command`; Planner used it to read a projected
  file-backed skill.
- Claude Code `2.1.206` exposed `Read` and `Bash`; Planner used both.

The RolePack declares `permissions.read_files=false`, no writable or network
authority, and a required `deny_all_except` command surface with no allowed
commands. Prompt instructions and a read-only filesystem sandbox are not hard
enforcement. Fresh provider lanes stop until the provider launch surface proves
zero forbidden tools or fails mount.

## Projection Gaps

At the observed candidate:

- Codex maps required command policy to `--ask-for-approval never --sandbox
  read-only`. That blocks writes, not shell execution or file reads.
- Claude settings merge an empty allowlist with an empty denylist. Empty
  `allow` is not a deny-all declaration.
- Role skills are still projected as provider-readable files even when the
  RolePack says `read_files=false`.
- Existing tests assert manifest declarations and allowlist shape, but not the
  effective provider tool surface or real-session zero-tool behavior.

The repair must consume project-local RolePack policy, inline the complete
reply contract without provider file reads, suppress every built-in and MCP
tool when the provider supports that guarantee, and fail mount otherwise.

## Normative Contract

The Planner skill says verification entries are literal executable argv, while
one task-set example still allows `command or evidence review`. Non-execution
routes also encourage prose-like verification that a permissive argv parser can
accept. Section extraction accepts aliases and fuzzy headings despite the
RolePack requiring exact labels.

The Role-owner arbitration freezes this route matrix:

| Route | Readiness | Allowed paths | Verification |
| :--- | :--- | :--- | :--- |
| `direct_execution` | `ready` | non-empty | one or more direct argv commands |
| `partial_completion` | `ready` | non-empty accepted scope | one or more direct argv commands |
| `needs_detail` | normally `needs_clarification` | `[]` | `[]` |
| verified `detail_ready` stop | `ready` plus exact stop status | `[]` | `[]` |
| `macro_adjustment_request` | bounded assessment only | `[]` | `[]` |
| `blocked` | `blocked` | `[]` | `[]` |

Non-execution evidence belongs in blockers, acceptance/decomposition fields,
and controller-supplied refs. Every non-empty verification entry is one
single-line direct argv command with no shell operators, substitutions,
environment assignments, `cd`, `source`, or aliases.

Production output grammar is exact and has no fallback:

- single task: ordered `**task-packet.md**`/`markdown` then
  `**readiness.json**`/`json`;
- task set: only `**task-set.json**`/`json`;
- replan or closure: only `**planner-backfill.json**`/`json`;
- only whitespace may surround the selected sections.

Aliases, alternate case, wrong fence language, duplicate/mixed sections, fuzzy
headings, unfenced content, and extra authority prose fail closed. Candidate
questions remain inside the selected canonical artifact until a separately
versioned activation contract exists.

Planner skill files may remain separate authoring sources. For a readless Role,
the host must compile their complete effective contract into digest-bound turn
context, project no discoverable provider-side Planner skills, and expose an
empty effective tool list. Failure to guarantee that list must stop mount before
job submission; rejecting a tool call after provider execution is insufficient.

## Refreeze Requirements

- Change the Planner RolePack digest; re-resolve all seven RolePacks in one new
  lock snapshot without churning unaffected content hashes.
- Record Codex and Claude Planner projection digests over the inline contract,
  empty tool set, permission policy, templates, and exact parser grammar.
- Freeze source, Config, exact provider/profile/model, seven RolePack digests,
  and provider projection digests before the first ask.
- Tests must prove complete inline context, absent provider skill projection,
  empty effective tools, pre-submit fail-mount, exact grammar, every route's
  positive/negative verification cases, and zero tool side effects.
- Fresh frozen Codex and Claude-transport Planner sessions must show zero
  read/shell/search/task/skill-file calls; unit/fake tests cannot close the real
  regression by themselves.

## Model Qualification

- Codex CLI `0.144.3` exposes locally cached exact candidates including
  `gpt-5.4`; only `gpt-5.4` has old live session evidence, so it remains a
  candidate rather than an accepted strong-model profile.
- The current Claude transport resolves aliases to exact
  `deepseek-v4-pro`. This proves a third-party model over Claude transport, not
  a Claude-family secondary model. C3 strong-model qualification is
  `ENV_UNMET` until a fresh session proves a Claude-family exact ID.
- Weak-model claims require at least five independent fresh sessions per exact
  provider/model/profile/RolePack digest with no fallback and non-empty
  artifacts. Names such as `5.6` or Luna must not be invented.

## G7 Boundary

Read-only preflight confirms npm `@seemseam/ccb@8.1.4`, tag `v8.1.4`, and the
matching GitHub Release already exist. The current code cannot be packaged or
accepted under that identity. The smallest current patch-line candidate is
`8.1.5`, but the version change and final collision check wait for a terminal
code candidate. Publication and tagging remain separate authorization.

## Next Safe Order

1. Freeze the Planner reply-only Role and route verification grammar.
2. Implement provider hard enforcement or fail mount, and inline the contract.
3. Recompute all RolePack and provider projection digests.
4. Pass deterministic projection, launch, parser, and zero-tool stub tests.
5. Run fresh Planner-only provider smoke before full visible C1/C2/C3 lanes.
6. Run exact weak-model repetition, terminal full source, and G7 package gates.

## Claim Boundary

This diagnostic accepts the Phase2 wiring regression closure and rejects the
observed Planner provider projection. It does not accept a fresh provider lane,
any strong- or weak-model stability claim, production/default enablement,
installed-candidate behavior, publication, or tagging.
