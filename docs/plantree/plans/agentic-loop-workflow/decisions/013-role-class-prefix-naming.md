# 013 Role Class Prefix Naming And Abstract Parent Roles

Date: 2026-06-30
Status: Historical; naming examples superseded by
[017-flat-roles-and-role-collections.md](017-flat-roles-and-role-collections.md)
and
[019-orchestrator-triage-before-task-detailer.md](019-orchestrator-triage-before-task-detailer.md)

## Decision

Workflow RolePacks should move from CCB-prefixed role ids such as
`agentroles.ccb_worker` to host-neutral class-prefixed concrete ids such as
`agentroles.worker_coder`, `agentroles.reviewer_code`,
`agentroles.planner_task`, and `agentroles.orchestrator_round`.

The examples above are historical. Current mainline naming keeps
`agentroles.planner` as the macro planner, treats `agentroles.planner_task` as
deprecated alias material, and uses Decision 019 for the orchestrator-before-
detailer runtime boundary.

The role name should describe the semantic class first, then the concrete
specialty:

```text
worker_coder
worker_doc
worker_research
worker_test
reviewer_code
reviewer_doc
reviewer_source
reviewer_plan
reviewer_round
planner
planner_replan
broker_clarification
orchestrator_round
frontdesk_user
```

Parent role classes are abstract contracts. They define shared purpose,
authority, boundaries, output contracts, validation rules, and common template
families. They are not installable runtime agents.

Concrete child roles are installable RolePacks and runtime mount targets. They
inherit or restate the parent contract, then add one narrow specialty and
host-adapter metadata. CCB-specific behavior belongs under an adapter section
such as `[adapters.ccb]`, not in the generic role id.

## Consequences

- The CCB workflow can dispatch multiple agents from the same semantic class
  without pretending each one is a separate architecture concept.
- `worker` becomes a role class, not one overloaded role. Concrete work is
  assigned to `worker_coder`, `worker_doc`, `worker_research`, `worker_test`,
  or future worker specialties.
- `reviewer` becomes a role class. Node checkers, plan reviewers, source
  reviewers, document reviewers, and round checkers can share reviewer
  authority rules while remaining distinct concrete roles.
- Old experimental `agentroles.ccb_*` workflow roles may be replaced rather
  than migrated. No alias or compatibility layer is required for this
  experimental line.
- CCB config and dynamic capacity profiles should reference concrete roles,
  while runtime UI may group them by class.

## Non-Goals

- Do not make parent classes provider sessions.
- Do not make inheritance implicit magic that hides actual role instructions.
- Do not encode CCB, tmux, or ask-specific behavior into host-neutral role ids.
- Do not preserve old `ccb_*` workflow role ids as permanent public aliases.

## External Spec Handoff

The Agent Roles spec should add a small, reviewable way to represent:

- abstract role classes;
- concrete child roles with `class` and `specialty`;
- non-installable parent contracts;
- host-specific adapter metadata for CCB and other hosts;
- validation that prevents abstract classes from being mounted as agents.
