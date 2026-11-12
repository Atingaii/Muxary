# 028 Frontdesk-Owned Planner Silence Handoff

Date: 2026-07-12
Status: Accepted and real-provider verified

## Context

The prior automatic intake path made Controller code observe a completed
Frontdesk provider reply, decide whether it contained intake, construct a new
Planner prompt, submit that prompt, and start the loop runner. A second Codex
session observer duplicated the same semantic relay outside normal CCB job
delivery.

That design violated the small-kernel workflow principle. Frontdesk already
owns user-turn classification and intake wording; CCB already provides durable
submit-only `ask --silence`. Re-observing provider prose in Controller code
made two competing handoff paths, changed the message Planner actually saw,
and coupled automatic progress to provider-specific session files.

## Decision

Frontdesk owns the only semantic transition from user intake to Planner:

```text
user -> Frontdesk
          |
          +-- ask --silence --compact --inline-request
              --task-id act-frontdesk-<request-id>
              planner < complete Intake/Blocked Evidence
```

Frontdesk classifies every user turn. Direct questions are answered without a
handoff. Project work and blocked project prerequisites produce a complete
`Intake Evidence` or `Blocked Evidence` body with `CCB_REQ_ID`, then Frontdesk
submits exactly one silent ask to resident Planner and stops. It never asks for
a plan slug, waits, polls, chains, targets another role, or implements work.

Planner receives the exact Frontdesk-authored body. Planner infers single-task
versus task-set output from explicit independent deliverables, distinct
routes, or route-mix intent. Controller code does not prepend a semantic role
prompt, rewrite requirements, select task wording, or reconstruct the intake
from a completed Frontdesk reply.

## Sole Frontdesk Command Surface

The Frontdesk RolePack remains read-only and denies generic shell and generic
CCB access. Its one allowed effect is:

```text
argv prefix: ask --silence --compact --inline-request --task-id
required suffix: act-frontdesk-<request-id> planner
final inline argument: ccb.frontdesk.intake.v1
idempotency: request id plus intake digest
```

Codex receives one managed MCP capability,
`ccb_frontdesk_ask_planner(request_id, evidence)`, because its read-only sandbox
intentionally blocks direct Unix-socket access. The stdio MCP transport runs
outside that sandbox and invokes the same existing `submit_ask` service with
target, silence, compact, inline body, and task id fixed. Claude uses the shell
allowlist above. Neither transport waits for Planner.

Dispatcher validation is the hard backstop. A Frontdesk-originated request is
rejected unless it is a single-target, non-chain, inline, silent Planner ask;
the task id and `CCB_REQ_ID` must match, and required intake anchors must be
present. Therefore a provider cannot use the allowlist wildcard to target
another agent or invoke an authority surface.

## Minimal Controller Authority

The Controller retains only deterministic mechanics:

- validate the sole command shape and intake schema;
- resolve or bootstrap the active plan through project policy;
- fence the request id against the exact intake digest;
- persist one Frontdesk activation and one Planner job;
- return the existing job for an exact retry and reject conflicting reuse;
- wake or reuse the singleton loop runner;
- recover a persisted Planner job/activation after a submit-to-runner crash;
- import Planner output and advance script-owned task/runtime authority.

The Controller does not own the Frontdesk-to-Planner semantic message. The
legacy completed-job relay and provider-session observer are removed from
production finalization and heartbeat paths. The explicit legacy
`frontdesk forward-planner` CLI may remain temporarily for compatibility and
historical fixtures, but it is not exposed by the Frontdesk RolePack and is not
the production automatic path.

## Failure And Recovery Rules

- Same request id and same body: reuse the persisted Planner job; never submit
  a duplicate.
- Same request id and different body or plan: fail visibly.
- Planner job persisted but runner start failed: preserve the job and
  activation; exact retry or daemon startup recovery wakes the runner.
- Imported or terminally rejected Planner output: startup recovery does not
  restart historical work.
- Missing intake fields, non-silent ask, chain route, reply target, body
  artifact, arbitrary target, or mismatched id: reject before job creation.
- No elapsed business timeout converts a pending provider ask into success or
  failure.
- Managed provider callers validate the mounted lease/lifecycle identity and
  attempt the existing daemon RPC directly. They never clear shutdown intent,
  start a keeper, take over a daemon, or trust sandbox-restricted PID/socket
  probes as lifecycle authority.
- The evidence is one quoted inline request argument. Heredocs, pipes, and
  automatic request-artifact spill are prohibited because Frontdesk is
  intentionally read-only.
- Codex uses the role-owned stdio capability rather than direct socket access;
  this is transport only and does not parse, generate, or rewrite intake prose.

## Consequences

- Frontdesk-to-Planner communication uses the same durable CCB transport as
  other role collaboration.
- Planner sees what Frontdesk sent, so requirement loss is inspectable at the
  role boundary instead of hidden in Controller prompt generation.
- Controller code becomes smaller and provider-neutral while retaining
  exact-once, recovery, and authority guarantees.
- Frontdesk remains long-lived and conversational; Planner remains resident;
  all downstream immaculate roles keep their existing dynamic lifecycle.

## Acceptance

- RolePack tests prove one allowed command and no other effect.
- Dispatcher tests prove exact message preservation, strict target/silence/id
  validation, exact retry, crash-window recovery, and no completed-reply relay.
- Lifecycle tests prove no provider-session observer heartbeat and startup
  recovery of an unimported direct handoff.
- Full non-provider-blackbox source gate passes.
- One fresh visible real-provider project proves ordinary user prompt to
  Frontdesk, Frontdesk-owned silent Planner ask, Planner import, downstream
  execution/review/integration/round review, resident return, zero dynamic
  residue, and immediate project shutdown after evidence capture.

The acceptance run is recorded in
[../history/decision028-frontdesk-direct-handoff-real-provider-20260712.md](../history/decision028-frontdesk-direct-handoff-real-provider-20260712.md).

## Related

- [010-simple-kernel-flexible-agents.md](010-simple-kernel-flexible-agents.md)
- [022-semantic-orchestration-bundle-and-controller-execution.md](022-semantic-orchestration-bundle-and-controller-execution.md)
- [027-worker-owned-review-chain-and-minimal-controller.md](027-worker-owned-review-chain-and-minimal-controller.md)
- [../goals/single-lane-multi-workgroup-release-goal.md](../goals/single-lane-multi-workgroup-release-goal.md)
