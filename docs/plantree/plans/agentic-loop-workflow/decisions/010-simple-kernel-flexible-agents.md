# Decision 010: Simple Kernel, Flexible Agents

Date: 2026-06-26

## Status

Accepted.

## Decision

Workflow design should start from the fusion of two constraints:

- Program code should stay simple, stable, deterministic, and easy to recover.
- Agents should provide semantic understanding, flexible writing, planning,
  review, diagnosis, and adaptation.

CCB workflow should not try to encode all intelligence into scripts. It should
also not let agents own hard state. The boundary is:

```text
scripts own hard constraints
agents own semantic work
scripts commit or reject agent outputs
```

## Rationale

Scripts are reliable when they enforce small, deterministic invariants:
identity allocation, state transitions, locks, leases, artifact manifests,
path safety, digest recording, indexes, and required evidence checks.

Scripts become fragile when they try to understand complex Markdown, product
requirements, risk tradeoffs, implementation strategy, or human-facing
explanations. Those surfaces should remain agent-authored semantic artifacts.

Agents are useful because they can reason across ambiguous goals, source
context, risk, plans, reviews, and non-convergence evidence. Agents become
unsafe when they directly mutate authority fields such as status, current
loop, locks, indexes, or terminal state.

The stable design is therefore a narrow workflow kernel plus flexible semantic
agents.

## Consequences

- `ccb plan`, `ccb loop`, and `ccb question` should stay small and stable.
- Script commands should be judged by determinism, idempotence, recoverability,
  and narrow validation, not by semantic completeness.
- Agents may write complex human-readable Markdown, but scripts import,
  validate, index, and record artifact metadata.
- Machine-owned authority should live in structured files or protected blocks.
- Mixed documents should separate script-managed fields from agent-authored
  narrative.
- If a behavior requires semantic judgment, prefer an agent artifact plus a
  deterministic commit/validation command instead of a growing script parser.

## Practical Test

When deciding whether a feature belongs in scripts or agents:

| Question | Owner |
| :--- | :--- |
| Is this a hard invariant, state edge, lock, identity, path, digest, or required evidence check? | script |
| Does this require interpreting intent, risk, code behavior, tradeoffs, or user-facing explanation? | agent |
| Does this need both? | agent drafts; script validates and commits |
